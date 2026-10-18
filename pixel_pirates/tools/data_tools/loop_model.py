"""Core-loop arithmetic (Module B2). Takes the tuning numbers and answers: does the loop actually deliver the B1 pillar targets?

  python tools/data_tools/loop_model.py          # prints the cycle table and the resulting play-time split
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import design_checks as D  # noqa: E402
import voyage_clock as VC  # noqa: E402

# archetype -> (lower band key, upper band key, destination tier, mix key)
ARCH = {"hop": (None, "voyage.hop_max_minutes", 3, "loop.mix_hop_pct"),
        "passage": ("voyage.hop_max_minutes", "voyage.passage_max_minutes", 2, "loop.mix_passage_pct"),
        "crossing": ("voyage.passage_max_minutes", "voyage.crossing_max_minutes", 1, "loop.mix_crossing_pct"),
        "dead": ("voyage.crossing_max_minutes", "voyage.dead_max_minutes", 1, "loop.mix_dead_pct")}

NEED = ["time.real_minutes_per_game_day", "time.ashore_game_minutes_per_real_minute", "time.accel_fast_factor", "loop.report_max_seconds", "loop.max_quiet_minutes",
        "loop.choice_moments_per_10min", "loop.crisis_moments_per_10min_max", "loop.island_engagement", "loop.plan_minutes",
        "loop.provision_minutes", "loop.ship_fraction_of_voyage", "loop.combat_fraction_of_voyage", "crew.watch_length_hours",
        "island.explore_budget_min_t1", "island.explore_budget_min_t2", "island.explore_budget_min_t3"] + [v[3] for v in ARCH.values()]


def load_ranges(data_dir: Path = D.DATA) -> dict[str, tuple[float, float]]:
    out = {}
    for p in sorted((data_dir / "tuning").glob("*.json")):
        for r in json.loads(p.read_text())["records"]:
            out[r["key"]] = (r["min"], r["max"])
    return out


def cycle(t: dict, name: str) -> dict:
    """One average cycle of this archetype, in real minutes, split by the four pillar activities."""
    lo_k, hi_k, tier, _ = ARCH[name]
    lo = t["voyage.hop_min_minutes"] if lo_k is None else t[lo_k]
    hi = t[hi_k]
    voyage = (lo + hi) / 2.0
    ship_v, combat_v = voyage * t["loop.ship_fraction_of_voyage"], voyage * t["loop.combat_fraction_of_voyage"]
    island = t[f"island.explore_budget_min_t{tier}"] * t["loop.island_engagement"]
    c = {"name": name, "tier": tier, "voyage": voyage, "days": voyage / t["time.real_minutes_per_game_day"],
         "sea": voyage - ship_v - combat_v, "island": island, "ship": ship_v + t["loop.plan_minutes"] + t["loop.provision_minutes"], "combat": combat_v}
    c["total"] = c["sea"] + c["island"] + c["ship"] + c["combat"]
    c["reports"] = c["days"]
    return c


def shares(t: dict) -> dict:
    """Mix-weighted play-time split of the whole campaign, in percent."""
    tot = {"sea": 0.0, "island": 0.0, "ship": 0.0, "combat": 0.0, "total": 0.0, "voyage": 0.0, "days": 0.0}
    for name, (_, _, _, mk) in ARCH.items():
        w, c = t[mk] / 100.0, cycle(t, name)
        for k in tot:
            tot[k] += w * c[k]
    out = {k: 100.0 * tot[k] / tot["total"] for k in ("sea", "island", "ship", "combat")}
    out.update({"cycle_minutes": tot["total"], "voyage_minutes": tot["voyage"], "days_per_cycle": tot["days"]})
    return out


def loop_invariants(t: dict, ranges: dict) -> list[str]:
    miss = [k for k in NEED if k not in t]
    if miss:
        return [f"loop: missing tuning keys {miss}"]
    p: list[str] = []
    mix = sum(t[v[3]] for v in ARCH.values())
    if abs(mix - 100) > 0.01:
        p.append(f"loop: voyage mix must add to 100 percent (got {mix})")
    s = shares(t)
    for key, tk in (("sea", "share.sea_pct"), ("island", "share.island_pct"), ("ship", "share.ship_crew_pct")):
        lo, hi = ranges[tk]
        if not lo <= s[key] <= hi:
            p.append(f"loop: modelled {key} share {s[key]:.1f} percent is outside the pillar range {lo}-{hi} ({tk})")
    if s["combat"] > t["share.combat_pct_max"]:
        p.append(f"loop: modelled combat share {s['combat']:.1f} percent exceeds the cap {t['share.combat_pct_max']}")
    if s["sea"] < s["island"]:
        p.append("loop: the modelled sea share is below the island share (pillar P1)")
    rate = t["time.real_minutes_per_game_day"]
    if rate > t["loop.max_quiet_minutes"]:
        p.append("loop: a game day is longer than the maximum quiet stretch, so the daily Morning Report cannot keep the sea alive")
    if t["voyage.hop_min_minutes"] < rate:
        p.append("loop: the shortest voyage is shorter than one game day, so a voyage could have no Morning Report")
    if 24.0 % t["crew.watch_length_hours"] != 0:
        p.append("loop: the watch length must divide 24 hours")
    if t["loop.crisis_moments_per_10min_max"] > t["loop.choice_moments_per_10min"]:
        p.append("loop: more crises than choices per 10 minutes would turn the sea into a panic")
    if t["loop.report_max_seconds"] > 30:
        p.append("loop: the Morning Report must be readable in 30 seconds or less")
    k = t["time.ashore_game_minutes_per_real_minute"]
    worst_visit_days = VC.ashore_game_hours(t["island.explore_budget_min_t1"], k) / 24.0
    if worst_visit_days > 1.0:
        p.append(f"loop: a full Tier 1 visit would cost {worst_visit_days:.2f} game days; no island may cost more than one day of supplies")
    if k < 1440.0 / (t["island.explore_budget_min_t1"] * 4):
        p.append("loop: the ashore clock is too slow: a full Tier 1 visit would cost under a quarter of a game day, so islands would be free")
    band = VC.band_of(14 * rate, t["voyage.hop_min_minutes"], t["voyage.hop_max_minutes"], t["voyage.passage_max_minutes"],
                      t["voyage.crossing_max_minutes"], t["voyage.dead_max_minutes"])
    if band != "crossing":
        p.append(f"loop: the 14-day worked example from B1 must be a Crossing at this time scale (it is '{band}')")
    return p


def flags(t: dict) -> list[str]:
    """Design pressures that are intended, reported as information (not failures)."""
    rate = t["time.real_minutes_per_game_day"]
    out = []
    dead_days = t["voyage.dead_max_minutes"] / rate
    out.append(f"longest Dead Ocean crossing = {dead_days:.1f} game days; 12 men need {12 * t['water.need_l_per_man_day_min'] * dead_days:.0f} L at the minimum water ration")
    if "water.foul_after_days_warm" in t and dead_days > t["water.foul_after_days_warm"]:
        out.append(f"water goes foul after {t['water.foul_after_days_warm']:.0f} warm days = {t['water.foul_after_days_warm'] * rate:.0f} real min, "
                   f"before the longest Dead Ocean crossing ends ({t['voyage.dead_max_minutes']:.0f} min): rain catching, boiling or a spring is REQUIRED (intended)")
    visit_h = sum(t[v[3]] / 100.0 * VC.ashore_game_hours(t[f"island.explore_budget_min_t{v[2]}"] * t["loop.island_engagement"] + t["loop.provision_minutes"], t["time.ashore_game_minutes_per_real_minute"]) for v in ARCH.values())
    out.append(f"an average island visit (explore + provision) costs {visit_h:.1f} game hours; a full Tier 1 budget costs {VC.ashore_game_hours(t['island.explore_budget_min_t1'], t['time.ashore_game_minutes_per_real_minute']):.0f} h")
    out.append(f"scurvy clock {t['health.scurvy_onset_days_no_vitc']:.0f} days = {t['health.scurvy_onset_days_no_vitc'] * rate:.0f} real min of sailing without fruit")
    return out


def table(t: dict) -> str:
    L = ["| cycle | mix | to island tier | voyage min | game days | island min | ship+crew min | combat min | cycle min |", "|---|---|---|---|---|---|---|---|---|"]
    for name, (_, _, tier, mk) in ARCH.items():
        c = cycle(t, name)
        L.append(f"| {name} | {t[mk]:.0f}% | T{tier} | {c['voyage']:.1f} | {c['days']:.1f} | {c['island']:.1f} | {c['ship']:.1f} | {c['combat']:.1f} | {c['total']:.1f} |")
    s = shares(t)
    L.append(f"| **campaign average** | 100% | | {s['voyage_minutes']:.1f} | {s['days_per_cycle']:.1f} | | | | **{s['cycle_minutes']:.1f}** |")
    return "\n".join(L)


def main() -> int:
    t, rg = D.load_tuning(), load_ranges()
    print(table(t))
    s = shares(t)
    print(f"\nplay-time split: sea {s['sea']:.1f}%  islands {s['island']:.1f}%  ship+crew {s['ship']:.1f}%  combat {s['combat']:.1f}%")
    print("problems:", loop_invariants(t, rg) or "none")
    for f in flags(t):
        print("flag:", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
