"""Validation of baked island maps (Module A6). Used by bake.py, check_project.py and the tests."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import ndimage

import bake as B

HEX = set("0123456789abcdef")


def load_map(path: Path) -> dict:
    return json.loads(path.read_text())


def is_stale(m: dict, island: dict, ctx: dict) -> bool:
    return m.get("source_hash") != B.source_hash(island, ctx)


def check_map(m: dict, island: dict, ctx: dict) -> list[str]:
    p: list[str] = []
    tpl = ctx["templates"][island["template"]]
    tier = island["tier"]
    n = B.grid_size(ctx, tier)
    if m.get("map_schema") != 1:
        return ["map_schema must be 1"]
    if m["size"] != [n, n]:
        p.append(f"size {m['size']} != [{n}, {n}] for tier {tier}")
    t, e = m["terrain"], m["elev"]
    if len(t) != n or len(e) != n or any(len(r) != n for r in t + e):
        return p + ["terrain/elev grids are not n x n"]
    if any(c not in B.LEGEND for r in t for c in r):
        p.append("terrain contains a code outside the legend")
    if any(c not in HEX for r in e for c in r):
        p.append("elev contains a non-hex digit")
    if m["grid_sha256"] != B.grid_hash(t, e):
        p.append("grid hash mismatch (map was hand-edited; edit the template/seed and re-bake)")
    if m.get("content_sha256") != B.content_hash(m):
        p.append("content hash mismatch (map was hand-edited; edit the template/seed and re-bake)")
    if m["island"] != island["id"] or m["template"] != island["template"]:
        p.append("map belongs to another island/template")
    codes = np.array([list(r) for r in t])
    elev = np.array([[int(c, 16) for c in r] for r in e])
    land_only = np.isin(codes, list(".gur#"))
    frac = float(land_only.sum()) / (n * n)
    lf = tpl["land_fraction"]
    if not lf["min"] <= frac <= lf["max"]:
        p.append(f"land fraction {frac:.3f} outside template range {lf['min']}..{lf['max']}")
    lab, cnt = ndimage.label(land_only)
    if cnt:
        share = float(max(ndimage.sum(land_only, lab, range(1, cnt + 1)))) / max(float(land_only.sum()), 1)
        need = 0.3 if tpl.get("multi_island") else 0.8
        if share < need:
            p.append(f"main landmass is only {share:.2f} of the land (need >= {need})")
    walk = np.isin(codes, list(B.WALK_MULT))
    wl, _ = ndimage.label(walk)
    lo, hi = tpl["landings"]
    if not lo <= len(m["landings"]) <= hi:
        p.append(f"{len(m['landings'])} landings, template allows {lo}..{hi}")
    comps = set()
    for L in m["landings"]:
        x, y, sx, sy = L["x"], L["y"], L["sea_x"], L["sea_y"]
        if codes[y, x] != ".":
            p.append(f"landing at {x},{y} is not on a beach")
        if codes[sy, sx] != "-" or abs(sx - x) + abs(sy - y) != 1:
            p.append(f"landing at {x},{y} has no adjacent shallow-water cell")
        comps.add(int(wl[y, x]))
    if len(comps) > 1:
        p.append("landings are on different walkable components")
    seen = set()
    offers_found = set()
    for q in m["pois"]:
        x, y = q["x"], q["y"]
        if not (0 <= x < n and 0 <= y < n) or codes[y, x] not in ".gur":
            p.append(f"poi {q['slot']} is not on walkable dry land")
            continue
        if (x, y) in seen:
            p.append(f"poi {q['slot']} shares a cell")
        seen.add((x, y))
        if int(wl[y, x]) not in comps:
            p.append(f"poi {q['slot']} is not reachable from the landing")
        if "offer" in q:
            offers_found.add(q["offer"])
    declared = set(island["survival_offers"])
    if declared - offers_found:
        p.append(f"survival offers without a POI: {sorted(declared - offers_found)}")
    if offers_found - declared:
        p.append(f"POI offers not declared on the island: {sorted(offers_found - declared)}")
    if any(s["kind"] == "hook" for s in tpl["slots"]) and not any(q["kind"] == "hook" for q in m["pois"]):
        p.append("no hook POI")
    for poly in m["trails"]:
        for x, y in poly:
            if codes[y, x] not in B.WALK_MULT:
                p.append(f"trail passes through unwalkable cell {x},{y}")
                break
    budget = B.explore_budget(ctx, tier)
    mins = m["stats"]["explore_minutes"]
    if mins > budget:
        p.append(f"explore time {mins} min exceeds the tier-{tier} budget {budget} min")
    kit_assets = {a["asset"] for k in island["kits"] for a in ctx["kits"][k]["props"]}
    for a in m["prop_assets"]:
        if a not in kit_assets:
            p.append(f"prop asset {a} is not in the island's kits")
    for x, y, i in m["props"]:
        if not (0 <= x < n and 0 <= y < n) or codes[y, x] in "~#" or not (0 <= i < len(m["prop_assets"])):
            p.append(f"bad prop at {x},{y}")
            break
    return p
