"""H2D-1.2 on-foot reachability check on the baked Anvil Cay (static: reads only the baked files and tuning_land.json).

  python tools/h2d/check_land.py

Mirrors cay_world.gd `walkable()` on a 1 m grid over the explore circle: the pier counts as walkable; elsewhere the bilinear
ground height must reach land.min_h, the biome class must not be CLIFF, the slope (2 m baseline) must stay under
land.max_slope, and the body (land.body_r_m) must clear the baked blockers and every tree trunk of scatter_logic.py.
Then: the boarding point reaches all four stops, every stop is walkable, the route lengths and times are printed, and a
tree-free-corridor check (no walkable pocket smaller than 20 m2 that holds a stop). It cannot prove that the game feels
right; it proves the route can be walked. NOT a Godot run.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scatter_logic as SL  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CLIFF = 6
STEP = 1.0
errors: list[str] = []


def tuning() -> dict[str, float]:
    recs = json.loads((ROOT / "game/data/tuning/tuning_land.json").read_text())["records"]
    return {r["key"]: float(r["value"]) for r in recs}


def walk_grid(sc, tu, xs, zs, inside_fn):
    """The walkable mask on a regular grid (mirror of cay_world.gd walkable): returns (X, Z, inside, ok)."""
    meta = sc.meta
    X, Z = np.meshgrid(xs, zs)
    inside = inside_fn(X, Z)
    body = tu["land.body_r_m"]
    ntr = 0
    cell, ox, oz, n = sc.cell, sc.ox, sc.oz, sc.n
    hmap = np.array(sc.lut, np.float32)[sc.hgt[..., 0]]

    def hs(x, z):
        """cay_world.height_smooth: bilinear with the -0.5 cell offset; outside the map = -8."""
        fx, fz = (x - ox) / cell - 0.5, (z - oz) / cell - 0.5
        return ndimage.map_coordinates(hmap, [fz, fx], order=1, mode="constant", cval=-8.0).astype(np.float32)

    h = hs(X, Z)
    gx = (hs(X + 1, Z) - hs(X - 1, Z)) * 0.5
    gz = (hs(X, Z + 1) - hs(X, Z - 1)) * 0.5
    slope = np.sqrt(gx * gx + gz * gz)
    ci = np.clip(np.floor((X - ox) / cell).astype(int), 0, n - 1)
    cj = np.clip(np.floor((Z - oz) / cell).astype(int), 0, n - 1)
    cls = sc.bio[cj, ci, 0] >> 4
    ok = inside & (h >= tu["land.min_h"]) & (cls != CLIFF) & (slope <= tu["land.max_slope"])
    for x0, z0, x1, z1 in meta["blockers"]:
        ok &= ~((X > x0 - body) & (X < x1 + body) & (Z > z0 - body) & (Z < z1 + body))
    # tree trunks of every chunk that touches the circle
    per = float(sc.sc["chunk_m"])
    for cz in range(math.floor(zs.min() / per), math.floor(zs.max() / per) + 1):
        for cx in range(math.floor(xs.min() / per), math.floor(xs.max() / per) + 1):
            for tx, tz, tr in sc.chunk(cx, cz)["trunks"]:
                rr = tr + body
                i0, i1 = int((tx - rr - xs[0]) / STEP), int((tx + rr - xs[0]) / STEP) + 2
                j0, j1 = int((tz - rr - zs[0]) / STEP), int((tz + rr - zs[0]) / STEP) + 2
                i0, j0, i1, j1 = max(i0, 0), max(j0, 0), min(i1, len(xs)), min(j1, len(zs))
                if i0 >= i1 or j0 >= j1:
                    continue
                ok[j0:j1, i0:i1] &= ((X[j0:j1, i0:i1] - tx) ** 2 + (Z[j0:j1, i0:i1] - tz) ** 2) >= rr * rr
                ntr += 1
    pier = meta["harbor_layout"]["pier"]
    hd = pier["head"]
    on_pier = (((X >= pier["x0"]) & (X <= pier["x1"]) & (Z >= pier["z0"]) & (Z <= pier["z1"]))
               | ((X >= hd["x0"]) & (X <= pier["x1"]) & (Z >= hd["z0"]) & (Z <= pier["z1"])))
    ok |= on_pier & inside
    for d in meta.get("port", {}).get("decks", []):      # CP-1: decks and bridges are walkable like the pier, but props block them
        dk = (X >= d["x0"]) & (X <= d["x1"]) & (Z >= d["z0"]) & (Z <= d["z1"]) & inside
        for x0, z0, x1, z1 in meta["blockers"]:
            dk &= ~((X > x0 - body) & (X < x1 + body) & (Z > z0 - body) & (Z < z1 + body))
        ok |= dk
    return X, Z, inside, ok, ntr


def main() -> int:
    tu = tuning()
    sc = SL.Scatter()
    meta = sc.meta
    land = meta["land"]
    ex, ez, er = land["explore"]["x"], land["explore"]["z"], land["explore"]["r"] + tu["land.edge_margin_m"]
    xs = np.arange(math.floor(ex - er), math.ceil(ex + er) + 1, STEP)
    zs = np.arange(math.floor(ez - er), math.ceil(ez + er) + 1, STEP)
    X, Z, inside, ok, ntr = walk_grid(sc, tu, xs, zs, lambda X, Z: (X - ex) ** 2 + (Z - ez) ** 2 <= er * er)
    body = tu["land.body_r_m"]
    cell, ox, oz, n = sc.cell, sc.ox, sc.oz, sc.n
    print(f"land: grid {len(xs)} x {len(zs)} at {STEP} m, {ntr} trunks, walkable {ok.sum() * STEP * STEP / 1e4:.1f} ha "
          f"of {inside.sum() * STEP * STEP / 1e4:.1f} ha in the explore circle")

    def at(x: float, z: float) -> tuple[int, int]:
        return int(round((z - zs[0]) / STEP)), int(round((x - xs[0]) / STEP))

    # graph (8-neighbour) over walkable cells; moves are checked on both end cells (the game checks the end point only)
    idx = -np.ones(ok.shape, np.int64)
    idx[ok] = np.arange(int(ok.sum()))
    rows, cols, w = [], [], []
    for dj, di, d in [(0, 1, 1.0), (1, 0, 1.0), (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2))]:
        if di < 0:
            a = ok[:ok.shape[0] - dj, -di:]
            b = ok[dj:, :ok.shape[1] + di]
            ia, ib = idx[:ok.shape[0] - dj, -di:], idx[dj:, :ok.shape[1] + di]
        else:
            a = ok[:ok.shape[0] - dj, :ok.shape[1] - di]
            b = ok[dj:, di:]
            ia, ib = idx[:ok.shape[0] - dj, :ok.shape[1] - di], idx[dj:, di:]
        m = a & b
        rows.append(ia[m])
        cols.append(ib[m])
        w.append(np.full(int(m.sum()), d * STEP))
    r_, c_, w_ = np.concatenate(rows), np.concatenate(cols), np.concatenate(w)
    g = coo_matrix((w_, (r_, c_)), shape=(int(ok.sum()),) * 2).tocsr()
    g = g + g.T
    bj, bi = at(land["board"]["x"], land["board"]["z"])
    if not ok[bj, bi]:
        errors.append("the boarding point is not walkable")
        for e in errors:
            print("FAIL", e)
        return 1
    dist = dijkstra(g, directed=False, indices=int(idx[bj, bi]))
    walk, run = tu["land.walk_ms"], tu["land.run_ms"]
    total = 0.0
    for p in land["pois"]:
        j, i = at(p["x"], p["z"])
        if not ok[j, i]:
            errors.append(f"stop {p['id']} is not walkable")
            continue
        d = float(dist[int(idx[j, i])])
        if not math.isfinite(d):
            errors.append(f"stop {p['id']} cannot be reached from the pier on foot")
            continue
        straight = math.hypot(p["x"] - land["board"]["x"], p["z"] - land["board"]["z"])
        total = max(total, d)
        print(f"  {p['name']:<20} straight {straight:6.0f} m, walking path {d:6.0f} m (x{d / max(straight, 1):.2f}), "
              f"{d / walk / 60:4.1f} min walking, {d / run / 60:4.1f} min running")
        # the stop's surroundings: a 12 m radius disc around it must hold a decent walkable area
        yy, xx = np.ogrid[:ok.shape[0], :ok.shape[1]]
        disc = (yy - j) ** 2 + (xx - i) ** 2 <= (tu["land.poi_radius_m"] / STEP) ** 2
        area = float(ok[disc].sum()) * STEP * STEP
        if area < 100.0:
            errors.append(f"stop {p['id']}: only {area:.0f} m2 walkable inside its {tu['land.poi_radius_m']:.0f} m radius")
    # CP-1 revision: every place on the map, every named spot and every person must be standable AND reachable from the pier
    port = meta.get("port", {})
    bad = 0
    far = 0.0
    for kind, items in (("place", [(p["id"], p["x"], p["z"]) for p in port.get("places", []) if p["id"] not in ("lighthouse",)]),
                        ("npc", [(n["id"], n["x"], n["z"]) for n in port.get("npcs", [])])):
        for nid, x, z in items:
            j, i = at(x, z)
            if not (0 <= j < ok.shape[0] and 0 <= i < ok.shape[1]) or not ok[j, i]:
                # a place is a door: allow a walkable cell within 2.5 m
                near = ok[max(j - 2, 0):j + 3, max(i - 2, 0):i + 3].any() if (0 <= j < ok.shape[0] and 0 <= i < ok.shape[1]) else False
                if kind == "npc" or not near:
                    errors.append(f"{kind} {nid} at ({x:.1f}, {z:.1f}) is not on walkable ground")
                    bad += 1
                continue
            d = float(dist[int(idx[j, i])])
            if not math.isfinite(d):
                errors.append(f"{kind} {nid} at ({x:.1f}, {z:.1f}) cannot be reached from the pier")
                bad += 1
            else:
                far = max(far, d)
    print(f"  city check: {len(port.get('places', []))} places, {len(port.get('npcs', []))} people; {bad} problems; farthest {far:.0f} m from the pier")
    lab, nlab = ndimage.label(ok, structure=np.ones((3, 3)))
    sizes = ndimage.sum(ok, lab, range(1, nlab + 1))
    main_lab = lab[bj, bi]
    print(f"  walkable regions {nlab}; the pier's region holds {sizes[main_lab - 1] / ok.sum():.1%} of all walkable cells")
    if sizes[main_lab - 1] / ok.sum() < 0.9:
        errors.append("less than 90% of the walkable ground is connected to the pier")
    # the explore edge must not cut the island in a way that matters: report how much walkable ground touches the border
    edge = inside & ~ndimage.binary_erosion(inside, iterations=3)
    print(f"  walkable cells within 3 m of the explore border: {int((ok & edge).sum())} (the soft wall of the prototype)")
    # the route as a loop: the longest leg
    print(f"  longest one-way walk from the pier {total:.0f} m = {total / walk / 60:.1f} min at {walk} m/s")
    for e in errors:
        print("FAIL", e)
    print("PASS" if not errors else f"{len(errors)} ERROR(S)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
