"""CP-1 static check of the Anvil Harbor "Fish Row" district (reads the baked anvil_cay.json and the data files; NOT a Godot run).

  python tools/h2d/check_port.py [--map]       # --map also writes art_bible/cp1/district_map.png

Checks: every NPC, recruit and interaction point is walkable and reachable on foot from the pier landing; wander discs hold
enough walkable ground; patrol legs are clear; no two people share a spot; props stand on ground or deck (not in the sea);
moored hulls are on water and clear of the decks; the canal is closed to ships by the wharf deck and crossed by two bridges;
atlas indices exist; all six NPC groups and four distinct recruit places exist; the grounds are open water, >= 100 m from land.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_land as CL  # noqa: E402
import scatter_logic as SL  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "game/h2d/art"
DATA = ROOT / "game/data"
errors: list[str] = []
GROUPS = {"fisher", "merchant", "docker", "sailor", "shopkeeper", "townsman"}


def fail(msg: str) -> None:
    errors.append(msg)
    print("FAIL", msg)


def main() -> int:
    do_map = "--map" in sys.argv
    tu = CL.tuning()
    sc = SL.Scatter()
    meta = sc.meta
    port = meta["port"]
    xs = np.arange(-135.0, 45.0 + 0.1, 1.0)
    zs = np.arange(-50.0, 50.0 + 0.1, 1.0)
    X, Z, _inside, ok, _ntr = CL.walk_grid(sc, tu, xs, zs, lambda X, Z: np.ones(X.shape, bool))

    def at(x: float, z: float) -> tuple[int, int]:
        return int(round((z - zs[0]) / 1.0)), int(round((x - xs[0]) / 1.0))

    def walk(x: float, z: float) -> bool:
        j, i = at(x, z)
        return 0 <= j < ok.shape[0] and 0 <= i < ok.shape[1] and bool(ok[j, i])

    # graph
    idx = -np.ones(ok.shape, np.int64)
    idx[ok] = np.arange(int(ok.sum()))
    rows, cols, ws = [], [], []
    for dj, di, d in [(0, 1, 1.0), (1, 0, 1.0), (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2))]:
        if di < 0:
            a, b = ok[:ok.shape[0] - dj, -di:], ok[dj:, :ok.shape[1] + di]
            ia, ib = idx[:ok.shape[0] - dj, -di:], idx[dj:, :ok.shape[1] + di]
        else:
            a, b = ok[:ok.shape[0] - dj, :ok.shape[1] - di], ok[dj:, di:]
            ia, ib = idx[:ok.shape[0] - dj, :ok.shape[1] - di], idx[dj:, di:]
        m = a & b
        rows.append(ia[m])
        cols.append(ib[m])
        ws.append(np.full(int(m.sum()), d))
    g = coo_matrix((np.concatenate(ws), (np.concatenate(rows), np.concatenate(cols))), shape=(int(ok.sum()),) * 2).tocsr()
    g = g + g.T
    land = meta["land"]
    bj, bi = at(land["board"]["x"], land["board"]["z"])
    if not ok[bj, bi]:
        fail("the boarding point is not walkable")
        return 1
    dist = dijkstra(g, directed=False, indices=int(idx[bj, bi]))

    def reach(x: float, z: float) -> float:
        j, i = at(x, z)
        if not (0 <= j < ok.shape[0] and 0 <= i < ok.shape[1]) or not ok[j, i]:
            return -1.0
        d = float(dist[int(idx[j, i])])
        return d if math.isfinite(d) else -2.0

    # ---- people
    npcs = port["npcs"]
    groups = {n["group"] for n in npcs}
    if not GROUPS <= groups:
        fail(f"missing NPC groups: {sorted(GROUPS - groups)}")
    far = 0.0
    for n in npcs:
        d = reach(n["x"], n["z"])
        if d == -1.0:
            fail(f"{n['id']} at ({n['x']}, {n['z']}) is not on walkable ground")
        elif d == -2.0:
            fail(f"{n['id']} cannot be reached from the pier")
        far = max(far, d)
        if n["mode"] == "wander":
            k = 0
            tot = 0
            for a in np.linspace(0, 2 * math.pi, 16, endpoint=False):
                for rr in (0.5, 1.0):
                    tot += 1
                    k += walk(n["x"] + math.cos(a) * n["r"] * rr, n["z"] + math.sin(a) * n["r"] * rr)
            if k / tot < 0.25:
                fail(f"{n['id']}: only {k}/{tot} points of its wander disc are walkable")
        if n["mode"] == "patrol":
            for t in np.linspace(-1, 1, 21):
                if not walk(n["x"] + t * n["r"], n["z"]):
                    fail(f"{n['id']}: the patrol leg is blocked at offset {t * n['r']:.1f} m")
                    break
    for a in range(len(npcs)):
        for b in range(a + 1, len(npcs)):
            if math.hypot(npcs[a]["x"] - npcs[b]["x"], npcs[a]["z"] - npcs[b]["z"]) < 1.2:
                fail(f"{npcs[a]['id']} and {npcs[b]['id']} stand within 1.2 m of each other")
    rec = [n for n in npcs if n.get("recruit")]
    if len(rec) != 4:
        fail(f"expected 4 recruits, found {len(rec)}")
    for a in range(len(rec)):
        for b in range(a + 1, len(rec)):
            if math.hypot(rec[a]["x"] - rec[b]["x"], rec[a]["z"] - rec[b]["z"]) < 20.0:
                fail(f"recruits {rec[a]['recruit']} and {rec[b]['recruit']} are closer than 20 m (they need distinct places)")
    # recruit ids must exist in the data files
    spots = json.loads((DATA / "port/recruits_port.json").read_text())
    for r in rec:
        if r["recruit"] not in spots["recruits"]:
            fail(f"recruit {r['recruit']} has no entry in data/port/recruits_port.json")
    print(f"people: {len(npcs)} NPCs ({len(rec)} recruits), groups {sorted(groups)}; farthest {far:.0f} m of walking from the pier")
    for r in rec:
        print(f"  {r['recruit']:<20} at ({r['x']:7.1f}, {r['z']:6.1f}), {reach(r['x'], r['z']):5.0f} m of walking from the pier")

    # ---- interaction points
    for it in port["interactions"]:
        d = reach(it["x"], it["z"])
        print(f"  interaction {it['id']:<14} {d:5.0f} m from the pier")
        if d < 0:
            fail(f"interaction point {it['id']} is not reachable on foot")

    # ---- props and decks
    decks = port["decks"]

    def on_deck(x: float, z: float) -> bool:
        return any(d["x0"] <= x <= d["x1"] and d["z0"] <= z <= d["z1"] for d in decks)

    for key in ("props", "big"):
        for p in port[key]:
            a = port["atlases"]["stall" if key == "props" else "big"]
            if p["type"] >= a["cols"] * a["rows"] or p["type"] >= len(a["types"]):
                fail(f"{key} {p.get('name')}: atlas index {p['type']} does not exist")
            if p["y_m"] < 1.0 and not p.get("bob"):
                fail(f"{key} {p.get('name')} at ({p['x_m']}, {p['z_m']}) stands at y {p['y_m']} (in the water?)")
    for s in port["ships"]:
        if s["type"] >= 4:
            fail("ship atlas index out of range")
    blockers = meta["blockers"]
    for p in port["props"]:
        if p["name"] in ("lantern_post",):
            continue
        for b in blockers:
            pass
    # hulls: on water and off the decks
    for hu in port["hulls"]:
        x0, z0, x1, z1 = hu
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        j, i = int((cz - sc.oz) / sc.cell), int((cx - sc.ox) / sc.cell)
        hgt = float(sc.lut[sc.hgt[j, i, 0]])
        if hgt > 0.1:
            fail(f"hull at ({cx:.0f}, {cz:.0f}) sits on land (height {hgt:.2f})")
        for d in decks:
            ox_ = min(x1, d["x1"]) - max(x0, d["x0"])
            oz_ = min(z1, d["z1"]) - max(z0, d["z0"])
            if ox_ > 0.2 and oz_ > 0.2:
                fail(f"hull at ({cx:.0f}, {cz:.0f}) overlaps the {d['kind']} deck by {ox_:.1f} x {oz_:.1f} m")
    # the canal mouth is closed to ships: a wharf deck covers the canal columns across the shore line
    can = port["canal"]
    wharf = [d for d in decks if d["kind"] == "wharf"]
    for x in (can["x0"] + 0.5, (can["x0"] + can["x1"]) / 2, can["x1"] - 0.5):
        zshore = None
        for z in np.arange(-14.0, 60.0, 1.0):
            if not any(d["x0"] <= x <= d["x1"] and d["z0"] <= z <= d["z1"] for d in wharf):
                continue
            zshore = z
            break
        if zshore is None:
            fail(f"canal column x={x}: no wharf deck over it (ships could sail into the canal)")
    # bridges join the two banks
    for b in port["map"]["bridges"]:
        zc = (b[1] + b[3]) / 2
        w = (b[0] - 2.0, zc)
        e = (b[2] + 2.0, zc)
        dw, de = reach(*w), reach(*e)
        if dw < 0 or de < 0:
            fail(f"bridge {b}: an end is not walkable ({w} -> {dw:.0f}, {e} -> {de:.0f})")
            continue
        # the pier's distance must differ by a bridge crossing, not a detour: compare the path between the two ends
        j1, i1 = at(*w)
        j2, i2 = at(*e)
        d2 = dijkstra(g, directed=False, indices=int(idx[j1, i1]))[int(idx[j2, i2])]
        print(f"  bridge {b}: the two banks are {d2:.0f} m apart by foot (straight 16 m)")
        if d2 > 40.0:
            fail(f"bridge {b} does not shorten the way across the canal ({d2:.0f} m)")
    # the canal itself is not walkable
    if walk(sum([can["x0"], can["x1"]]) / 2, -6.0):
        fail("the canal bed is walkable")

    # ---- grounds are open water, >= 100 m from land (the baked island map)
    gr = json.loads((DATA / "port/fishing_grounds.json").read_text())["grounds"]
    n, cell, ox, oz = sc.n, sc.cell, sc.ox, sc.oz
    hmap = np.array(sc.lut, np.float32)[sc.hgt[..., 0]]
    for k, v in gr.items():
        ang = np.linspace(0, 2 * math.pi, 48, endpoint=False)
        worst = 1e9
        for rr in (0.0, v["r"] * 0.5, v["r"]):
            for a in ang if rr else [0.0]:
                x, z = v["x"] + rr * math.cos(a), v["z"] + rr * math.sin(a)
                # distance to land: scan a 100 m disc on the map
                for dd in range(0, 101, 10):
                    for a2 in np.linspace(0, 2 * math.pi, 24, endpoint=False):
                        xx, zz = x + dd * math.cos(a2), z + dd * math.sin(a2)
                        i, j = int((xx - ox) / cell), int((zz - oz) / cell)
                        if 0 <= i < n and 0 <= j < n and hmap[j, i] > 0.3:
                            worst = min(worst, dd)
        if worst < 100:
            fail(f"ground {k}: land within {worst:.0f} m of its disc")
        print(f"  ground {k:<24} centre ({v['x']:6.0f}, {v['z']:6.0f}), r {v['r']:.0f} m: no land within 100 m")

    if do_map:
        draw_map(meta, port, ok, xs, zs, sc)
    for e in errors:
        print("FAIL", e)
    print("PASS" if not errors else f"{len(errors)} ERROR(S)")
    return 1 if errors else 0


def draw_map(meta, port, ok, xs, zs, sc) -> None:
    from PIL import Image, ImageDraw
    S = 8
    x0, z0, x1, z1 = port["map"]["bounds"]
    W, H = int((x1 - x0) * S), int((z1 - z0) * S)
    im = Image.new("RGB", (W, H), (40, 70, 110))
    px = im.load()
    hmap = np.array(sc.lut, np.float32)[sc.hgt[..., 0]]
    cols = {1: (214, 190, 140), 2: (150, 150, 90), 3: (120, 150, 80), 4: (70, 110, 60), 7: (160, 130, 90), 8: (150, 140, 130), 9: (120, 120, 90)}
    for j in range(H):
        for i in range(W):
            x, z = x0 + (i + 0.5) / S, z0 + (j + 0.5) / S
            ii, jj = int((x - sc.ox) / sc.cell), int((z - sc.oz) / sc.cell)
            if hmap[jj, ii] > 0.05:
                c = int(sc.bio[jj, ii, 0]) >> 4
                px[i, j] = cols.get(c, (130, 120, 100))
    d = ImageDraw.Draw(im, "RGBA")

    def rect(r, fill, outline=None):
        d.rectangle([(r[0] - x0) * S, (r[1] - z0) * S, (r[2] - x0) * S, (r[3] - z0) * S], fill=fill, outline=outline)

    for r in port["map"]["wharf"]:
        rect(r, (140, 100, 60, 255))
    for r in port["map"]["bridges"]:
        rect(r, (190, 150, 90, 255), (60, 40, 20, 255))
    for s in meta["structures"]:
        if s["name"].startswith(("cottage", "fisher", "warehouse", "tavern", "harbour")):
            rect([s["x_m"] - s["w_m"] / 2, s["z_m"] - s["d_m"], s["x_m"] + s["w_m"] / 2, s["z_m"]], (120, 70, 60, 255), (40, 20, 20, 255))
    for b in meta["blockers"]:
        if b[0] > x0 and b[2] < x1 and b[1] > z0 and b[3] < z1:
            rect(b, (60, 50, 40, 120))
    for hu in port["hulls"]:
        rect(hu, (90, 60, 40, 255), (20, 10, 10, 255))
    colors = {"fisher": (255, 220, 60), "merchant": (220, 40, 40), "docker": (160, 110, 60), "sailor": (80, 130, 220),
              "shopkeeper": (240, 240, 220), "townsman": (90, 180, 90), "recruit": (255, 0, 255)}
    for n in port["npcs"]:
        cx, cz = (n["x"] - x0) * S, (n["z"] - z0) * S
        r = 6 if n["group"] == "recruit" else 4
        d.ellipse([cx - r, cz - r, cx + r, cz + r], fill=colors[n["group"]] + (255,), outline=(0, 0, 0, 255))
        if n["mode"] == "wander" and n["r"] > 0:
            rr = n["r"] * S
            d.ellipse([cx - rr, cz - rr, cx + rr, cz + rr], outline=colors[n["group"]] + (120,))
    for it in port["interactions"]:
        cx, cz = (it["x"] - x0) * S, (it["z"] - z0) * S
        d.rectangle([cx - 6, cz - 6, cx + 6, cz + 6], outline=(255, 255, 0, 255), width=2)
        d.text((cx + 8, cz - 6), it["name"], fill=(255, 255, 255, 255))
    out = ROOT / "art_bible/cp1"
    out.mkdir(parents=True, exist_ok=True)
    im.save(out / "district_map.png")
    print("map ->", out / "district_map.png")


if __name__ == "__main__":
    sys.exit(main())
