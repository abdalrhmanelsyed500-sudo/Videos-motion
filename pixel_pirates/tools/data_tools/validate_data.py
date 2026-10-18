"""Validate ALL game data (Module A5). Python twin of game/core/registry.gd (+ world rules; GDScript twin game/core/world_rules.gd since A7).

    python tools/data_tools/validate_data.py            # validates game/data
    python tools/data_tools/validate_data.py --ledger   # also writes docs/PROVISIONAL_LEDGER.md
Exit 0 = clean. Checks: file envelope {schema, kind, records}; every record against game/data/schemas/<kind>.schema.json;
unique keys; id prefix; cross references (ref / key_ref); tuning value inside [min, max]; WORLD RULES on islands.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import minischema as M  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "game" / "data"
SKIP_KINDS_AS_TABLE = {"save_state"}


def load_schemas(data_dir: Path) -> dict[str, dict]:
    return {p.name.split(".")[0]: json.loads(p.read_text()) for p in sorted((data_dir / "schemas").glob("*.schema.json"))}


def load_tables(data_dir: Path, schemas: dict, problems: list[str]) -> dict[str, dict[str, dict]]:
    """read every enveloped file under data_dir (not schemas/); returns kind -> key -> record (+ '_file')."""
    tables: dict[str, dict[str, dict]] = {}
    for f in sorted(data_dir.rglob("*.json")):
        if "schemas" in f.relative_to(data_dir).parts:
            continue
        try:
            doc = json.loads(f.read_text())
        except Exception as ex:  # noqa: BLE001
            problems.append(f"{f.name}: invalid JSON: {ex}")
            continue
        if not isinstance(doc, dict) or "records" not in doc:
            continue  # not an enveloped data file (palette, look profiles ...)
        rel = f.relative_to(ROOT) if f.is_relative_to(ROOT) else f
        kind = doc.get("kind")
        if doc.get("schema") != 1 or not isinstance(kind, str) or not isinstance(doc["records"], list):
            problems.append(f"{rel}: bad envelope (need schema=1, kind, records[])")
            continue
        sch = schemas.get(kind)
        if sch is None:
            problems.append(f"{rel}: no schema for kind '{kind}'")
            continue
        kf = sch["key_field"]
        for i, rec in enumerate(doc["records"]):
            errs = M.validate(rec, sch["record"], None)
            for p, m in errs:
                problems.append(f"{rel} record[{i}] {p}: {m}")
            key = rec.get(kf) if isinstance(rec, dict) else None
            if not isinstance(key, str):
                continue
            if sch["id_prefix"] and not key.startswith(sch["id_prefix"] + "_"):
                problems.append(f"{rel}: id '{key}' must start with '{sch['id_prefix']}_'")
            if key in tables.setdefault(kind, {}):
                problems.append(f"{rel}: duplicate {kind} '{key}' (also in {tables[kind][key]['_file']})")
            tables[kind][key] = {**rec, "_file": str(rel)}
    return tables


def make_lookup(tables: dict, schemas: dict, asset_ids: set[str]):
    mult = set(schemas.get("difficulty_mode", {}).get("record", {}).get("props", {}).get("multipliers", {}).get("required", []))

    def lookup(kind: str, key: str) -> bool:
        if kind == "asset":
            return key in asset_ids
        if kind == "multiplier":
            return key in mult
        return key in tables.get(kind, {})
    return lookup


def check_refs(tables: dict, schemas: dict, lookup, problems: list[str]) -> None:
    for kind, recs in tables.items():
        for key, rec in recs.items():
            clean = {k: v for k, v in rec.items() if k != "_file"}
            for p, m in M.validate(clean, schemas[kind]["record"], lookup):
                if m.startswith("unknown ") and "'" in m:  # only reference errors here; structural ones were reported by load_tables
                    problems.append(f"{rec['_file']} {kind} '{key}' {p}: {m}")
    for key, rec in tables.get("tuning", {}).items():
        if not (rec["min"] <= rec["value"] <= rec["max"]):
            problems.append(f"{rec['_file']} tuning '{key}': value {rec['value']} outside [{rec['min']}, {rec['max']}]")


def world_findings(islands: dict[str, dict]) -> list[tuple[str, str, str, str]]:
    """WORLD RULES (Canon), cross-record so a schema cannot express them. Returns (code, island_a, island_b, message).
    Codes: dist_short, not_mutual, asym, visible_no_landmark, visible_self. GDScript twin: game/core/world_rules.gd."""
    out: list[tuple[str, str, str, str]] = []
    for iid, isl in islands.items():
        px, py = isl["position"]["x_km"], isl["position"]["y_km"]
        for n in isl.get("neighbors", []):
            other = islands.get(n["id"])
            if other is None:
                continue  # unknown ref is reported by check_refs
            d_straight = math.hypot(px - other["position"]["x_km"], py - other["position"]["y_km"])
            if n["distance_km"] + 0.01 < d_straight:
                out.append(("dist_short", iid, n["id"], f"{iid}->{n['id']} sail distance {n['distance_km']} km is shorter than the straight line {d_straight:.2f} km"))
            back = next((m for m in other.get("neighbors", []) if m["id"] == iid), None)
            if back is None:
                out.append(("not_mutual", iid, n["id"], f"{iid} lists {n['id']} as neighbour but {n['id']} does not list {iid}"))
            elif abs(back["distance_km"] - n["distance_km"]) > 0.01 or abs(back["sail_hours_sloop"] - n["sail_hours_sloop"]) > 0.01:
                out.append(("asym", iid, n["id"], f"{iid}<->{n['id']} distance/time differs between the two directions"))
        if isl.get("visible_from") and not isl["landmark"]:
            out.append(("visible_no_landmark", iid, "", f"{iid} is visible from {isl['visible_from']} but is not flagged landmark (no island may be seen from another unless a deliberate landmark)"))
        for v in isl.get("visible_from", []):
            if v == iid:
                out.append(("visible_self", iid, "", f"{iid} lists itself in visible_from"))
    return out


def world_codes(islands: dict[str, dict]) -> list[str]:
    return sorted(f"{c}|{a}|{b}" for c, a, b, _ in world_findings(islands))


def world_rules(islands: dict[str, dict]) -> tuple[list[str], dict]:
    pr = [f"WORLD: {m}" for _, _, _, m in world_findings(islands)]
    tiers = {1: 0, 2: 0, 3: 0}
    for isl in islands.values():
        tiers[isl["tier"]] += 1
    clustered = sum(1 for i in islands.values() if any(n["distance_km"] < 25 for n in i.get("neighbors", [])))
    stats = {"islands": len(islands), "tier1": tiers[1], "tier2": tiers[2], "tier3": tiers[3], "in_clusters": clustered}
    return pr, stats


def run(data_dir: Path = DATA, asset_manifest: Path | None = None, with_world: bool = True) -> tuple[list[str], list[str], dict]:
    problems: list[str] = []
    schemas = load_schemas(data_dir)
    tables = load_tables(data_dir, schemas, problems)
    mf = asset_manifest or (ROOT / "game" / "art" / "manifest" / "sprites.json")
    assets = set(json.loads(mf.read_text())["assets"]) if mf.exists() else set()
    check_refs(tables, schemas, make_lookup(tables, schemas, assets), problems)
    info: list[str] = []
    if with_world and "island" in tables:
        wp, st = world_rules(tables["island"])
        problems += wp
        info.append(f"world: {st}")
        targets = (("tier1", 12, 15), ("tier2", 20, 25), ("tier3", 15, 25))
        for k, lo, hi in targets:
            if not lo <= st[k] <= hi:
                info.append(f"world target not yet met: {k} = {st[k]} (target {lo}-{hi}) - fills in with E3")
    counts = {k: len(v) for k, v in tables.items()}
    return problems, info, {"tables": tables, "counts": counts}


def write_ledger(tables: dict) -> Path:
    rows = []
    for kind, recs in tables.items():
        for key, r in recs.items():
            if r.get("provisional"):
                rows.append((r.get("owner", "?"), kind, key, r.get("source", "")))
    rows.sort()
    by_owner: dict[str, int] = {}
    for o, *_ in rows:
        by_owner[o] = by_owner.get(o, 0) + 1
    L = ["# PROVISIONAL LEDGER (generated by tools/data_tools/validate_data.py --ledger)", "",
         "Every balance number in `game/data/` carries `provisional`, `owner` and `source`. This table is the list of numbers that are NOT final,",
         "who is expected to finalise them, and where each came from. `owner` uses PROPOSED module numbers (N1..N14, B3); the N-module list is not",
         "fixed yet, so treat the tags as routing hints. Rule: B3 (survival overview) is finalised only when this ledger has no `N*` rows left.", "",
         f"**{len(rows)} provisional records** | " + ", ".join(f"{o}: {c}" for o, c in sorted(by_owner.items())), "",
         "| owner | kind | key | source |", "|---|---|---|---|"]
    L += [f"| {o} | {k} | `{key}` | {s} |" for o, k, key, s in rows]
    out = ROOT / "docs" / "PROVISIONAL_LEDGER.md"
    out.write_text("\n".join(L) + "\n")
    return out


def main() -> int:
    problems, info, res = run()
    for i in info:
        print("INFO ", i)
    for p in problems:
        print("FAIL ", p)
    print(f"validate_data: {res['counts']} -> {len(problems)} problems")
    if "--ledger" in sys.argv:
        print("wrote", write_ledger(res["tables"]))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
