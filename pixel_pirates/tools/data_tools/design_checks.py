"""Design-pillar checks (Module B1): machine-checked invariants, content-word lint, and the Reckoning calculation.

  python tools/data_tools/design_checks.py            # prints the worked Reckoning example used in docs/B1_PILLARS.md
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / "game" / "data"

# --- 1. pillar invariants over the tuning numbers -------------------------------------------------------------------


def load_tuning(data_dir: Path = DATA) -> dict[str, float]:
    out: dict[str, float] = {}
    for p in sorted((data_dir / "tuning").glob("*.json")):
        for r in json.loads(p.read_text())["records"]:
            out[r["key"]] = r["value"]
    return out


def invariants(t: dict[str, float]) -> list[str]:
    """Rules the pillars promise. Returns problem strings; missing keys are problems too."""
    need = ["warn.advisory_days", "warn.warning_days", "warn.critical_days", "warn.min_steps_before_loss", "recovery.min_options",
            "plan.forecast_spread_sea", "plan.forecast_spread_dead", "plan.forecast_spread_min", "voyage.hop_min_minutes", "voyage.hop_max_minutes",
            "voyage.passage_max_minutes", "voyage.crossing_max_minutes", "voyage.dead_max_minutes", "share.sea_pct", "share.island_pct",
            "share.ship_crew_pct", "share.combat_pct_max"]
    miss = [k for k in need if k not in t]
    if miss:
        return [f"pillar: missing tuning keys {miss}"]
    p: list[str] = []
    if not t["warn.advisory_days"] > t["warn.warning_days"] > t["warn.critical_days"] > 0:
        p.append("pillar P3: warning ladder must satisfy advisory > warning > critical > 0 days")
    if t["warn.min_steps_before_loss"] < 3:
        p.append("pillar P3: at least 3 warning steps before any loss")
    if t["recovery.min_options"] < 2:
        p.append("pillar P3: at least 2 recovery options at every critical state")
    if not 0 < t["plan.forecast_spread_sea"] < t["plan.forecast_spread_dead"] < 1:
        p.append("pillar P2: forecast band must be wider on dead ocean than on ordinary sea, and below 100 percent")
    if not 0 < t["plan.forecast_spread_min"] < t["plan.forecast_spread_sea"]:
        p.append("pillar P2: the narrowest forecast band must be above 0 (the sea keeps secrets) and below the ordinary band")
    bands = [t["voyage.hop_min_minutes"], t["voyage.hop_max_minutes"], t["voyage.passage_max_minutes"], t["voyage.crossing_max_minutes"],
             t["voyage.dead_max_minutes"]]
    if any(b2 <= b1 for b1, b2 in zip(bands, bands[1:])):
        p.append(f"pillar P1: voyage bands must strictly increase (got {bands})")
    if t["voyage.dead_max_minutes"] < 2 * t["voyage.crossing_max_minutes"] * 0.9:
        p.append("pillar P1: a dead-ocean crossing should be about twice the longest ordinary crossing")
    total = t["share.sea_pct"] + t["share.island_pct"] + t["share.ship_crew_pct"] + t["share.combat_pct_max"]
    if abs(total - 100) > 0.01:
        p.append(f"pillar P1: play-time shares must add to 100 at their central values (got {total})")
    if t["share.sea_pct"] < t["share.island_pct"]:
        p.append("pillar P1: the sea must take at least as much play time as the islands")
    if t["share.combat_pct_max"] > 12:
        p.append("anti-pillar: combat may not exceed 12 percent of play time")
    return p


# --- 2. content-word lint (HARD CONTENT RULES 2 and 3, plus crew rule 1 as a backstop) ---------------------------------

BANNED = {
    "rule 3 (religion)": ["god", "gods", "goddess", "pray", "prayer", "prays", "church", "chapel", "heaven", "amen", "blessed", "holy",
                          "sinner", "devil", "satan", "angel", "bible", "priest", "atheist", "atheism", "religion", "religious"],
    "rule 2 (sexual)": ["sex", "sexy", "nude", "naked", "brothel", "harlot", "strumpet", "wench", "seduce", "erotic", "lust", "whore"],
    "rule 1 (female crew)": ["she", "her", "hers", "woman", "women", "girl", "lady", "mistress", "mermaid", "queen", "female", "daughter",
                             "wife", "mother", "sister"],
}
ALLOW_FEMALE_RULE_KEYS = {"note", "source", "description"}  # free-text fields about the rule itself are checked by humans


def strings(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from strings(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from strings(v, f"{path}[{i}]")
    elif isinstance(o, str):
        yield path, o


def content_findings(docs: dict[str, object]) -> list[str]:
    """docs: {relative path: parsed json}. Only player-facing text kinds are scanned for rule 1 words (crew, npc, dialogue, names)."""
    out: list[str] = []
    for rel, doc in docs.items():
        for path, text in strings(doc):
            leaf = path.rsplit(".", 1)[-1]
            for rule, words in BANNED.items():
                if rule.startswith("rule 1") and (leaf in ALLOW_FEMALE_RULE_KEYS or leaf in ("id", "gender", "ref")):
                    continue
                for w in words:
                    if re.search(rf"\b{re.escape(w)}\b", text, re.I):
                        out.append(f"content {rule}: '{w}' in {rel}{path}: {text[:60]!r}")
    return out


def scan_data(data_dir: Path = DATA) -> list[str]:
    docs = {}
    for p in sorted(data_dir.rglob("*.json")):
        rel = p.relative_to(data_dir).as_posix()
        if rel.startswith(("schemas/", "islands/maps/")) or p.name.endswith(".map.json"):
            continue
        docs[rel] = json.loads(p.read_text())
    return content_findings(docs)


# --- 3. the Reckoning (voyage planner arithmetic), used for the worked example in B1_PILLARS.md ---------------------------


def reckoning(t: dict[str, float], crew: int, expected_days: float, spread: float, stock: dict[str, float], water_l_per_man: float | None = None) -> dict:
    """Honest arithmetic: needs at the low / expected / high end of the forecast band and the margin of each stock, in days."""
    water_pm = water_l_per_man if water_l_per_man is not None else t["water.need_l_per_man_day_min"]
    lo, hi = expected_days * (1 - spread), expected_days * (1 + spread)
    per_day = {"hardtack_kg": crew * t["food.hardtack_kg_per_man_day"], "water_l": crew * water_pm}
    out = {"band_days": (round(lo, 1), round(expected_days, 1), round(hi, 1)), "per_day": per_day, "rows": []}
    for k, per in per_day.items():
        have = stock[k]
        out["rows"].append({"stock": k, "have": have, "need_expected": round(per * expected_days, 1), "need_worst": round(per * hi, 1),
                            "days_of_stock": round(have / per, 1), "margin_days_worst": round(have / per - hi, 1)})
    return out


def rung(days_left: float, t: dict[str, float]) -> str:
    """Warning ladder rung for a stock with this many days left at current consumption."""
    if days_left <= t["warn.critical_days"]:
        return "critical"
    if days_left <= t["warn.warning_days"]:
        return "warning"
    if days_left <= t["warn.advisory_days"]:
        return "advisory"
    return "ok"


def main() -> int:
    t = load_tuning()
    r = reckoning(t, 12, 14, t["plan.forecast_spread_sea"], {"hardtack_kg": 90, "water_l": 480})
    print(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
