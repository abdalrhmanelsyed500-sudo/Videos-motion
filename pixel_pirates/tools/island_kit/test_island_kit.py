"""Tests for the island kit (Module A6). Run: python tools/island_kit/test_island_kit.py"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bake as B  # noqa: E402
import island_checks as IC  # noqa: E402
import sameness as S  # noqa: E402
import shapes  # noqa: E402

FX = B.ROOT / "game" / "tests" / "fixtures" / "islands"
ctx = B.load_context()
isl = {r["id"]: r for r in B.read_island_file(FX / "islands.json")}
fails = 0


def expect(name: str, cond: bool, detail: str = "") -> None:
    global fails
    print(("ok   " if cond else "FAIL ") + name + ("" if cond else f"  {detail}"))
    fails += 0 if cond else 1


def rehash(m: dict) -> dict:
    m["grid_sha256"] = B.grid_hash(m["terrain"], m["elev"])
    m["content_sha256"] = B.content_hash(m)
    return m


m1 = B.bake(isl["isl_901"], ctx)
m2 = B.bake(isl["isl_901"], ctx)
expect("same seed gives byte-identical map", json.dumps(m1, sort_keys=True) == json.dumps(m2, sort_keys=True))
other = copy.deepcopy(isl["isl_901"])
other["seed"] = "12345"
expect("different seed gives a different island", B.bake(other, ctx)["terrain"] != m1["terrain"])

maps = {}
for iid, rec in isl.items():
    mp = B.bake(rec, ctx)
    maps[iid] = mp
    pr = IC.check_map(mp, rec, ctx)
    expect(f"{iid} ({rec['template']}) bakes and passes every map check", not pr, str(pr))
saved = {iid: IC.load_map(FX / "maps" / f"{iid}.map.json") for iid in isl}
expect("committed fixture maps equal a fresh bake", all(saved[i]["content_sha256"] == maps[i]["content_sha256"] for i in isl))
expect("committed fixture maps are not stale", not any(IC.is_stale(saved[i], isl[i], ctx) for i in isl))

# stale detection: any change to template, kit, seed or offers
c2 = copy.deepcopy(ctx)
c2["templates"]["tpl_blob_isle"]["relief"]["levels"] = 6
expect("changing the template makes the map stale", IC.is_stale(saved["isl_901"], isl["isl_901"], c2))
c3 = copy.deepcopy(ctx)
c3["kits"]["kit_tropical"]["props"][0]["density"] = 9
expect("changing the kit makes the map stale", IC.is_stale(saved["isl_901"], isl["isl_901"], c3))
r2 = copy.deepcopy(isl["isl_901"])
r2["seed"] = "1"
expect("changing the seed makes the map stale", IC.is_stale(saved["isl_901"], r2, ctx))

# tamper detection
t = copy.deepcopy(saved["isl_901"])
row = list(t["terrain"][5])
row[5] = "g"
t["terrain"][5] = "".join(row)
expect("hand-edited terrain is detected (hash)", any("hash" in p for p in IC.check_map(t, isl["isl_901"], ctx)))

# map-level rule violations (hashes recomputed so only the rule itself fires)
t = rehash(copy.deepcopy(saved["isl_901"]))
t["pois"] = [q for q in t["pois"] if q.get("offer") != "fruit"]
expect("missing survival offer is caught", any("offers without a POI" in p for p in IC.check_map(rehash(t), isl["isl_901"], ctx)))
t = copy.deepcopy(saved["isl_901"])
t["pois"][0]["x"], t["pois"][0]["y"] = 0, 0
expect("POI in the deep sea is caught", any("not on walkable dry land" in p for p in IC.check_map(rehash(t), isl["isl_901"], ctx)))
t = copy.deepcopy(saved["isl_901"])
t["landings"] = []
expect("island without landing is caught", any("landings" in p for p in IC.check_map(rehash(t), isl["isl_901"], ctx)))
c4 = copy.deepcopy(ctx)
c4["tuning"]["island.explore_budget_min_t2"] = 1.0
expect("explore-time budget is enforced", any("budget" in p for p in IC.check_map(saved["isl_901"], isl["isl_901"], c4)))
t = copy.deepcopy(saved["isl_901"])
t["prop_assets"] = ["prp_cannon"]
expect("prop outside the kit is caught", any("not in the island's kits" in p for p in IC.check_map(rehash(t), isl["isl_901"], ctx)))

# bake-time failures
bad = copy.deepcopy(isl["isl_909"])
bad["tier"] = 1
try:
    B.bake(bad, ctx)
    ok = False
except B.BakeError as e:
    ok = "not allowed for tier" in str(e)
expect("template used on a forbidden tier is refused", ok)
c5 = copy.deepcopy(ctx)
c5["templates"]["tpl_blob_isle"]["slots"][0]["where"] = {"terrain": ["rock"], "coast_tiles": [150, 160]}
try:
    B.bake(isl["isl_901"], c5)
    ok = False
except B.BakeError as e:
    ok = "no valid cell" in str(e)
expect("unsatisfiable slot raises a clear error", ok)
bad = copy.deepcopy(isl["isl_901"])
bad["template"] = "tpl_nope"
try:
    B.bake(bad, ctx)
    ok = False
except B.BakeError:
    ok = True
expect("unknown template raises", ok)

# data sanity
expect("every shape op in the schema has parameters", {t["shape"]["op"] for t in ctx["templates"].values()} <= set(shapes.PARAMS))
bad_params = [(t["id"], k) for t in ctx["templates"].values() for k in t["shape"].get("params", {}) if k not in shapes.allowed_params(t["shape"]["op"])]
expect("template shape parameters are all known", not bad_params, str(bad_params))
expect("every tier has at least 3 templates available", all(sum(1 for t in ctx["templates"].values() if tier in t["tiers"]) >= 3 for tier in (1, 2, 3)))
expect("each template has a hook slot where it matters", all(any(s["kind"] == "hook" for s in t["slots"]) for t in ctx["templates"].values()))
expect("the island grid sizes match the tier tuning", all(len(maps[i]["terrain"]) == B.grid_size(ctx, isl[i]["tier"]) for i in isl))

# sameness catalog
entries = [(isl[i], saved[i]) for i in isl]
pr, wr, pairs = S.check_catalog(entries, ctx)
expect("the 10 fixture islands pass the sameness catalog", not pr, str(pr))
dup = copy.deepcopy(isl["isl_901"])
dup["id"] = "isl_950"
dmap = copy.deepcopy(saved["isl_901"])
dmap["island"] = "isl_950"
pr, _, _ = S.check_catalog(entries + [(dup, dmap)], ctx)
expect("an identical silhouette is flagged as alike", any("look alike" in p and "isl_950" in p for p in pr))
# rotated copy must be flagged too (rotation invariance)
rot = copy.deepcopy(saved["isl_903"])
rot["island"] = "isl_951"
rot["terrain"] = ["".join(r) for r in zip(*rot["terrain"][::-1])]
rd = copy.deepcopy(isl["isl_903"])
rd["id"] = "isl_951"
pr, _, _ = S.check_catalog(entries + [(rd, rot)], ctx)
expect("a rotated copy is flagged as alike", any("isl_951" in p and "isl_903" in p for p in pr))
many = []
for k in range(5):
    r = copy.deepcopy(isl["isl_902"])
    r["id"] = f"isl_96{k}"
    r["hook_kind"] = "ruin"
    mm = copy.deepcopy(saved["isl_902"])
    mm["island"] = r["id"]
    many.append((r, mm))
pr, _, _ = S.check_catalog(many, ctx)
expect("hook-kind quota is enforced", any("hook kind 'ruin'" in p for p in pr))
a, b = copy.deepcopy(isl["isl_901"]), copy.deepcopy(isl["isl_903"])
a["neighbors"] = [{"id": "isl_903", "distance_km": 5, "sail_hours_sloop": 1}]
b["hook_kind"] = a["hook_kind"]
pr, _, _ = S.check_catalog([(a, saved["isl_901"]), (b, saved["isl_903"])], ctx)
expect("neighbours with the same hook kind are flagged", any("neighbours" in p for p in pr))

print("island kit tests:", "PASS" if not fails else f"{fails} FAILED")
sys.exit(1 if fails else 0)
