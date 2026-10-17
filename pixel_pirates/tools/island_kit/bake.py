"""Island baker (Module A6): island record + template + kit + seed  ->  baked map (game/data/islands/maps/<id>.map.json).

The game NEVER generates islands at run time: it loads the baked map. Same seed + same sources = same map; the map stores a
source_hash so a changed template/kit/seed is detected as 'stale' (check_project.py), and a grid hash so hand-edits are detected.
Usage:  python bake.py --islands FILE --out DIR [--only isl_901] [--find-seed isl_901]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, str(Path(__file__).parent))
import prng  # noqa: E402
import shapes  # noqa: E402

GENERATOR_VERSION = 1
ROOT = Path(__file__).resolve().parents[2]
GAME_DATA = ROOT / "game" / "data"
LEGEND = {"~": "deep", "-": "shallow", ".": "beach", "g": "ground", "u": "upland", "r": "rock", "#": "cliff"}
CODE_OF = {v: k for k, v in LEGEND.items()}
WALK_MULT = {"-": 1.6, ".": 1.0, "g": 1.0, "u": 1.15, "r": 1.25}
DIRS = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, 1.4142), (-1, 1, 1.4142), (1, -1, 1.4142), (-1, -1, 1.4142)]
TIER_KEYS = {1: "t1", 2: "t2", 3: "t3"}


class BakeError(Exception):
    pass


# ------------------------------------------------------------------ context
def _records(path: Path) -> list[dict]:
    return json.loads(path.read_text())["records"]


def load_context(data_dir: Path = GAME_DATA) -> dict:
    tuning = {r["key"]: r["value"] for p in sorted((data_dir / "tuning").glob("*.json")) for r in _records(p)}
    return {"kits": {r["id"]: r for r in _records(data_dir / "kits" / "kits.json")},
            "templates": {r["id"]: r for r in _records(data_dir / "templates" / "island_templates.json")}, "tuning": tuning}


def grid_size(ctx: dict, tier: int) -> int:
    return int(ctx["tuning"][f"island.size_tiles_{TIER_KEYS[tier]}"])


def explore_budget(ctx: dict, tier: int) -> float:
    return float(ctx["tuning"][f"island.explore_budget_min_{TIER_KEYS[tier]}"])


def source_hash(island: dict, ctx: dict) -> str:
    tpl = ctx["templates"][island["template"]]
    src = {"v": GENERATOR_VERSION, "n": grid_size(ctx, island["tier"]), "speed": ctx["tuning"]["move.walk_speed_mps"],
           "island": {k: island.get(k) for k in ("id", "tier", "template", "kits", "seed", "survival_offers", "hook_kind")},
           "template": tpl, "kits": [ctx["kits"][k] for k in island["kits"]]}
    return hashlib.sha256(json.dumps(src, sort_keys=True).encode()).hexdigest()


def grid_hash(terrain: list[str], elev: list[str]) -> str:
    return hashlib.sha256(("\n".join(terrain) + "|" + "\n".join(elev)).encode()).hexdigest()


def content_hash(m: dict) -> str:
    d = {k: v for k, v in m.items() if k != "content_sha256"}
    return hashlib.sha256(json.dumps(d, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# ------------------------------------------------------------------ terrain
def _dilate(mask: np.ndarray, r: int) -> np.ndarray:
    return ndimage.binary_dilation(mask, structure=np.ones((3, 3), bool), iterations=r) if r > 0 else mask


def make_terrain(tpl: dict, n: int, rng: prng.SplitMix64, base: int):
    op, params = tpl["shape"]["op"], tpl["shape"].get("params", {})
    P, aux = shapes.potential(op, params, rng.fork("shape"), n, base)
    p = aux["p"]
    Pn = P + p["rough"] * (prng.fbm(n, n / 6, 4, base + 101) - 0.5) * 2
    lin = (np.arange(n) + 0.5) / n * 2 - 1
    U, V = np.meshgrid(lin, lin)
    land = (Pn > 0) & (np.abs(U) < 0.9) & (np.abs(V) < 0.9)
    lab, cnt = ndimage.label(land)
    if cnt:
        sizes = ndimage.sum(land, lab, range(1, cnt + 1))
        for i, sz in enumerate(sizes, 1):
            if sz < 5:
                land[lab == i] = False
    rel = tpl["relief"]
    levels = int(rel["levels"])
    Pc = np.clip(Pn, 0, 1)
    ne = prng.fbm(n, n / 8, 3, base + 202)
    if op == "cone":
        ef = Pc ** 0.55 * (0.92 + 0.16 * ne)
        cr = aux["crater"]
        inside = aux["r"] < cr
        ef = np.where(inside, ef * (0.62 + 0.38 * (aux["r"] / cr) ** 2), ef)
    elif op == "mesa":
        plateau = Pc > 0.28
        step = np.where(plateau, 0.85 + 0.15 * ne, 0.04 + Pc / 0.28 * 0.2)
        ramp = np.clip(Pc / 0.45, 0, 1) * 0.9
        dth = np.abs((aux["th"] - aux["ramp_th"] + math.pi) % (2 * math.pi) - math.pi)
        w = np.clip(1 - dth / (aux["ramp_w"] / 2), 0, 1)
        w = w * w * (3 - 2 * w)
        ef = step * (1 - w) + np.maximum(ramp, step * 0.6) * w
    else:
        ef = Pc ** 0.8 * (0.9 + 0.2 * ne)
    elev = np.where(land, np.clip(np.rint(ef * levels), 0, 15), 0).astype(int)
    d_in = ndimage.distance_transform_edt(land)
    d_sea = ndimage.distance_transform_edt(~land)
    pad = np.pad(elev, 1, mode="constant", constant_values=0)  # outside the grid and the sea count as height 0
    drop = np.maximum.reduce([elev - pad[1:-1, :-2], elev - pad[1:-1, 2:], elev - pad[:-2, 1:-1], elev - pad[2:, 1:-1]])
    cliff = land & (drop >= int(rel["cliff_step"])) & (elev >= 2)
    beach_w = tpl["coast"]["beach_tiles"] * (0.6 + 0.8 * prng.fbm(n, n / 5, 2, base + 303))
    beach = land & (d_in <= beach_w) & (elev <= 2) & ~cliff
    rn = prng.fbm(n, n / 7, 3, base + 404)
    ra = float(rel["rock_amount"])
    rock = land & ~beach & ~cliff & ((rn > 1 - ra * 0.55) | ((elev >= round(0.85 * levels)) & (ra >= 0.4) & (levels >= 4) & (op != "mesa")))
    upland = land & ~beach & ~cliff & ~rock & (elev >= round(0.55 * levels)) & (levels >= 3)
    sw = tpl["coast"]["shallow_tiles"] * (0.7 + 0.6 * prng.fbm(n, n / 6, 3, base + 505))
    sea = ~land
    slab, scnt = ndimage.label(sea)
    enclosed = np.zeros_like(sea)
    border = set(np.unique(np.concatenate([slab[0], slab[-1], slab[:, 0], slab[:, -1]])).tolist())
    for i in range(1, scnt + 1):
        if i not in border:
            enclosed |= slab == i
    shallow = sea & ((d_sea <= sw) | enclosed)
    codes = np.full((n, n), "~", dtype="<U1")
    codes[shallow] = "-"
    codes[land] = "g"
    codes[upland] = "u"
    codes[rock] = "r"
    codes[beach] = "."
    codes[cliff] = "#"
    return codes, elev, d_in


def _rows(codes: np.ndarray) -> list[str]:
    return ["".join(r) for r in codes]


def _elev_rows(elev: np.ndarray) -> list[str]:
    return ["".join("0123456789abcdef"[v] for v in r) for r in elev]


# ------------------------------------------------------------------ walking graph
def build_graph(codes: np.ndarray, elev: np.ndarray):
    n = codes.shape[0]
    walk = np.isin(codes, list(WALK_MULT))
    mult = np.zeros((n, n))
    for ch, m in WALK_MULT.items():
        mult[codes == ch] = m
    idx = np.arange(n * n).reshape(n, n)
    rows, cols, wts = [], [], []
    for dx, dy, ln in DIRS:
        ys, xs = np.mgrid[0:n, 0:n]
        y2, x2 = ys + dy, xs + dx
        ok = (y2 >= 0) & (y2 < n) & (x2 >= 0) & (x2 < n)
        y2c, x2c = np.clip(y2, 0, n - 1), np.clip(x2, 0, n - 1)
        ok &= walk & walk[y2c, x2c]
        if dx != 0 and dy != 0:  # no corner cutting
            ok &= walk[ys, x2c] & walk[y2c, xs]
        w = ln * mult[y2c, x2c] + 0.8 * np.maximum(0, elev[y2c, x2c] - elev)
        rows.append(idx[ok])
        cols.append(idx[y2c, x2c][ok])
        wts.append(w[ok])
    r, c, w = np.concatenate(rows), np.concatenate(cols), np.concatenate(wts)
    return coo_matrix((w, (r, c)), shape=(n * n, n * n)).tocsr(), walk


def _walk_label(walk: np.ndarray):
    return ndimage.label(walk)  # 4-connectivity: conservative vs. the 8-move graph


# ------------------------------------------------------------------ placement
def _sample(rng: prng.SplitMix64, cells: np.ndarray, k: int) -> np.ndarray:
    return cells[[int(rng.random() * len(cells)) for _ in range(min(k, 4 * len(cells)))]]


def _best_candidate(rng, mask, existing, min_d, k=48):
    cells = np.argwhere(mask)
    if len(cells) == 0:
        return None
    pts = _sample(rng, cells, k)
    best, best_s = None, -1.0
    for y, x in pts:
        d = min((math.hypot(x - ex, y - ey) for ex, ey in existing), default=1e9)
        if d >= min_d and d > best_s:
            best, best_s = (int(x), int(y)), d
    return best


def bake(island: dict, ctx: dict) -> dict:
    tpl = ctx["templates"].get(island.get("template", ""))
    if tpl is None:
        raise BakeError(f"unknown template {island.get('template')}")
    tier = int(island["tier"])
    if tier not in tpl["tiers"]:
        raise BakeError(f"template {tpl['id']} is not allowed for tier {tier} (allowed {tpl['tiers']})")
    n = grid_size(ctx, tier)
    seed = int(island["seed"])
    rng = prng.SplitMix64(seed)
    base = seed & 0xFFFFFFFF
    codes, elev, d_in = make_terrain(tpl, n, rng, base)
    graph, walk = build_graph(codes, elev)
    lab, cnt = _walk_label(walk)
    land_cells = np.isin(codes, list("."+"gur"))
    if cnt == 0 or not land_cells.any():
        raise BakeError("no land generated")
    per = ndimage.sum(land_cells, lab, range(1, cnt + 1))
    main = int(np.argmax(per)) + 1
    reach = (lab == main)
    reach_land = reach & land_cells
    prs = rng.fork("slots")
    # landings: beach cells next to shallows, in the main walkable component
    sh = codes == "-"
    nb = np.zeros_like(sh)
    nb[1:, :] |= sh[:-1, :]
    nb[:-1, :] |= sh[1:, :]
    nb[:, 1:] |= sh[:, :-1]
    nb[:, :-1] |= sh[:, 1:]
    cand = reach & (codes == ".") & nb
    if not cand.any():
        raise BakeError("no landing beach in the main landmass")
    lo, hi = tpl["landings"]
    k_land = prs.randint(lo, hi)
    landings: list[tuple[int, int]] = []
    for i in range(k_land):
        pt = _best_candidate(prs, cand, landings, (n / 4 if i else 0), k=64)
        if pt is None:
            break
        landings.append(pt)
    land_out = []
    for x, y in landings:
        sx, sy = next((x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= x + dx < n and 0 <= y + dy < n and codes[y + dy, x + dx] == "-")
        land_out.append({"x": x, "y": y, "sea_x": sx, "sea_y": sy})
    # points of interest
    ok_cell = ndimage.binary_erosion(np.isin(codes, list("."+"gur")), structure=np.ones((3, 3), bool))
    offers = list(island["survival_offers"])
    pois: list[dict] = []
    taken = list(landings)
    for slot in tpl["slots"]:
        lo, hi = slot["count"][str(tier)]
        k = prs.randint(lo, hi)
        if slot["kind"] == "survival":
            k = max(k, len(offers))
        w = slot.get("where", {})
        terr = w.get("terrain", ["beach", "ground", "upland", "rock"])
        tmask = np.isin(codes, [CODE_OF[t] for t in terr])
        cmask = np.ones_like(tmask)
        if "coast_tiles" in w:
            cmask = (d_in >= w["coast_tiles"][0]) & (d_in <= w["coast_tiles"][1])
        for i in range(k):
            mask = reach_land & ok_cell & tmask & cmask
            if "near_slot" in w:
                refs = [(p["x"], p["y"]) for p in pois if p["slot"].rsplit("_", 1)[0] == w["near_slot"]]
                if refs:
                    yy, xx = np.mgrid[0:n, 0:n]
                    dmin = np.min([np.hypot(xx - rx, yy - ry) for rx, ry in refs], axis=0)
                    mask = mask & (dmin >= w["near_tiles"][0]) & (dmin <= w["near_tiles"][1])
            spacing = float(slot.get("spacing_tiles", 8))
            pt = None
            for f in (1.0, 0.6, 0.35):
                pt = _best_candidate(prs, mask, taken, spacing * f)
                if pt:
                    break
            if pt is None:
                raise BakeError(f"slot '{slot['id']}' #{i + 1}: no valid cell (template too tight for this seed)")
            taken.append(pt)
            poi = {"slot": f"{slot['id']}_{i + 1}", "kind": slot["kind"], "x": pt[0], "y": pt[1]}
            if slot["kind"] == "survival":
                poi["offer"] = offers[i % len(offers)]
            if slot["kind"] == "hook" and island.get("hook_kind"):
                poi["hook_kind"] = island["hook_kind"]
            pois.append(poi)
    # trails = shortest-path tree from the landings (so paths merge into trunks, like real trails)
    li = [y * n + x for x, y in landings]
    dist, pred, srcs = dijkstra(graph, directed=True, indices=li, min_only=True, return_predecessors=True)
    trail_cells: set[tuple[int, int]] = set()
    trails: list[list[list[int]]] = []
    for p in pois:
        cur = p["y"] * n + p["x"]
        if not np.isfinite(dist[cur]):
            raise BakeError(f"poi {p['slot']} is unreachable")
        path = [cur]
        while pred[cur] >= 0 and srcs[cur] != cur:
            cur = int(pred[cur])
            path.append(cur)
        path.reverse()
        pts = [(c % n, c // n) for c in path]
        trail_cells.update(pts)
        turn = [pts[0]]
        for a in range(1, len(pts) - 1):
            d1 = (pts[a][0] - pts[a - 1][0], pts[a][1] - pts[a - 1][1])
            d2 = (pts[a + 1][0] - pts[a][0], pts[a + 1][1] - pts[a][1])
            if d1 != d2:
                turn.append(pts[a])
        turn.append(pts[-1])
        trails.append([[int(x), int(y)] for x, y in turn])
    # explore time: nearest-neighbour tour of all POIs from the first landing
    nodes = [li[0]] + [p["y"] * n + p["x"] for p in pois]
    dm = dijkstra(graph, directed=True, indices=nodes)
    D = dm[:, nodes]
    left, cur, total = set(range(1, len(nodes))), 0, 0.0
    while left:
        nxt = min(left, key=lambda j: D[cur, j])
        total += float(D[cur, nxt])
        left.discard(nxt)
        cur = nxt
    tile_m = 2.0
    metres = total * tile_m
    minutes = metres / ctx["tuning"]["move.walk_speed_mps"] / 60.0
    # props
    props_out, assets = place_props(island, ctx, codes, trail_cells, landings, pois, rng.fork("props"))
    land_mask = codes != "~"
    land_only = np.isin(codes, list("."+"gur#"))
    ll, lc = ndimage.label(land_only)
    lsz = ndimage.sum(land_only, ll, range(1, lc + 1)) if lc else [0]
    terrain, elev_rows = _rows(codes), _elev_rows(elev)
    m = {"map_schema": 1, "island": island["id"], "template": tpl["id"], "kits": list(island["kits"]), "seed": str(island["seed"]),
         "generator": GENERATOR_VERSION, "source_hash": source_hash(island, ctx), "grid_sha256": grid_hash(terrain, elev_rows),
         "size": [n, n], "tile_m": tile_m, "legend": LEGEND, "terrain": terrain, "elev": elev_rows,
         "landings": land_out, "pois": pois, "trails": trails, "prop_assets": assets, "props": props_out,
         "stats": {"land_tiles": int(land_only.sum()), "land_fraction": round(float(land_only.sum()) / (n * n), 4),
                   "land_components": int(lc), "main_land_share": round(float(max(lsz)) / max(float(land_only.sum()), 1), 4),
                   "max_elev": int(elev.max()), "pois": len(pois), "landings": len(landings), "trail_tiles": len(trail_cells),
                   "props": len(props_out), "explore_metres": round(metres, 1), "explore_minutes": round(minutes, 2),
                   "counts": {LEGEND[c]: int((codes == c).sum()) for c in LEGEND}}}
    m["content_sha256"] = content_hash(m)
    return m


def place_props(island, ctx, codes, trail_cells, landings, pois, rng):
    n = codes.shape[0]
    block = np.zeros((n, n), bool)
    for x, y in trail_cells:
        block[y, x] = True
    pts = np.zeros((n, n), bool)
    for x, y in landings:
        pts[y, x] = True
    for p in pois:
        pts[p["y"], p["x"]] = True
    block |= _dilate(pts, 2)
    occ = np.zeros((n, n), bool)
    rules, assets, out = [], [], []
    for kid in island["kits"]:
        rules += ctx["kits"][kid]["props"]
    zone_code = {"beach": ".", "ground": "g", "upland": "u", "rock": "r", "shallows": "-"}
    for r in rules:
        mask = (codes == zone_code[r["zone"]]) & ~block
        cells = np.argwhere(mask)
        if len(cells) == 0:
            continue
        target = int(round(r["density"] * len(cells) / 100.0))
        sp = int(r["spacing"])
        cl = r.get("cluster", [1, 1])
        if r["asset"] not in assets:
            assets.append(r["asset"])
        ai = assets.index(r["asset"])
        placed, tries = 0, 0
        while placed < target and tries < target * 8 and len(out) < 8000:
            tries += 1
            y, x = cells[int(rng.random() * len(cells))]
            members = rng.randint(cl[0], cl[1])
            for mi in range(members):
                px, py = int(x), int(y)
                if mi:
                    px += rng.randint(-2, 2)
                    py += rng.randint(-2, 2)
                if not (0 <= px < n and 0 <= py < n) or not mask[py, px]:
                    continue
                y0, y1, x0, x1 = max(py - sp + 1, 0), min(py + sp, n), max(px - sp + 1, 0), min(px + sp, n)
                if occ[y0:y1, x0:x1].any():
                    continue
                occ[py, px] = True
                out.append([px, py, ai])
                placed += 1
    return out, assets


def write_map(m: dict, path: Path) -> None:
    keys = list(m.keys())
    lines = []
    for k in keys:
        v = m[k]
        if k in ("terrain", "elev"):
            lines.append(f'"{k}": [\n  ' + ",\n  ".join(json.dumps(r) for r in v) + "\n ]")
        elif k in ("pois", "landings", "trails"):
            lines.append(f'"{k}": [\n  ' + ",\n  ".join(json.dumps(r, separators=(",", ":")) for r in v) + "\n ]")
        elif k == "props":
            lines.append('"props": [\n  ' + ",\n  ".join(json.dumps(v[i:i + 12], separators=(",", ":"))[1:-1] for i in range(0, len(v), 12)) + "\n ]")
        else:
            lines.append(f'"{k}": ' + json.dumps(v, separators=(",", ":")))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{\n" + ",\n".join(lines) + "\n}\n")


def read_island_file(path: Path) -> list[dict]:
    return json.loads(path.read_text())["records"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--islands", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only")
    ap.add_argument("--find-seed")
    a = ap.parse_args()
    ctx = load_context()
    import island_checks as IC  # noqa: PLC0415
    isl = read_island_file(Path(a.islands))
    if a.find_seed:
        rec = next(r for r in isl if r["id"] == a.find_seed)
        s0 = int(rec["seed"])
        for i in range(500):
            rec["seed"] = str(s0 + i)
            try:
                m = bake(rec, ctx)
            except BakeError as e:
                continue
            probs = IC.check_map(m, rec, ctx)
            if not probs:
                print(f"{rec['id']}: seed {rec['seed']} works (explore {m['stats']['explore_minutes']} min, land {m['stats']['land_fraction']})")
                return 0
        print("no seed found in 500 tries")
        return 1
    bad = 0
    for rec in isl:
        if a.only and rec["id"] != a.only:
            continue
        try:
            m = bake(rec, ctx)
        except BakeError as e:
            print(f"FAIL {rec['id']}: {e}")
            bad += 1
            continue
        probs = IC.check_map(m, rec, ctx)
        for p in probs:
            print(f"FAIL {rec['id']}: {p}")
        bad += bool(probs)
        write_map(m, Path(a.out) / f"{rec['id']}.map.json")
        s = m["stats"]
        print(f"{rec['id']} {rec['template']} T{rec['tier']}: land {s['land_fraction']:.2f}, pois {s['pois']}, explore {s['explore_minutes']} min, props {s['props']}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
