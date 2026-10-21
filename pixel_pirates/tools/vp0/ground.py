"""VP-0 seamless top-down ground / deck / hull / sail textures at 24 px per metre (a 48 px tile = 2 m).

Same rules as the voxel sprites: palette ramps only (palette.json + palette_vp0.json), light from the upper left, 4 cel bands,
no #000000 / #ffffff. Every tile is periodic (tiles on a torus) so the terrain shader can repeat it without seams.
Output: game/art/vp0/ground/ground_atlas.png (4 variants per row, one row per material) + ground_manifest.json; plus deck_planks.png,
hull_strakes.png, sail_canvas.png.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voxel as V  # noqa: E402

T = 48
OUT = V.ROOT / "game" / "art" / "vp0" / "ground"


def vnoise(n: int, cells: int, rng) -> np.ndarray:
    """Periodic value noise on an n x n torus with `cells` lattice cells, smoothstep interpolation, range 0..1."""
    lat = rng.random((cells, cells))
    t = np.arange(n) * cells / n
    i0 = np.floor(t).astype(int) % cells
    i1 = (i0 + 1) % cells
    f = t - np.floor(t)
    f = f * f * (3 - 2 * f)
    a = lat[i0][:, i0]
    b = lat[i0][:, i1]
    c = lat[i1][:, i0]
    d = lat[i1][:, i1]
    fx = f[:, None]
    fy = f[None, :]
    return (a * (1 - fy) + b * fy) * (1 - fx) + (c * (1 - fy) + d * fy) * fx


def fbm(n, rng, octs=((3, 1.0), (6, 0.5), (12, 0.25))):
    out = np.zeros((n, n))
    tot = 0
    for c, w in octs:
        out += vnoise(n, c, rng) * w
        tot += w
    return out / tot


def voronoi(n: int, cells: int, rng, jitter=0.85):
    """Periodic voronoi. Returns (cell id grid, distance to nearest site, distance to 2nd nearest) in pixels."""
    pts = (np.stack(np.meshgrid(np.arange(cells), np.arange(cells), indexing="ij"), -1) + 0.5 + (rng.random((cells, cells, 2)) - 0.5) * jitter) * (n / cells)
    pts = pts.reshape(-1, 2)
    yy, xx = np.meshgrid(np.arange(n) + 0.5, np.arange(n) + 0.5, indexing="ij")
    best = np.full((n, n), 1e9)
    second = np.full((n, n), 1e9)
    bid = np.zeros((n, n), int)
    for k, (py, px) in enumerate(pts):
        dy = np.abs(yy - py)
        dy = np.minimum(dy, n - dy)
        dx = np.abs(xx - px)
        dx = np.minimum(dx, n - dx)
        d = np.hypot(dx, dy)
        m = d < best
        second = np.where(m, best, np.minimum(second, d))
        bid = np.where(m, k, bid)
        best = np.where(m, d, best)
    return bid, best, second


def light(h: np.ndarray, strength=2.2) -> np.ndarray:
    """Lambert from the upper left on a periodic height field; returns 0..1."""
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    nx, ny, nz = -gx * strength, -gy * strength, np.ones_like(h)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    L = np.array([-0.5, -0.6, 0.62])
    L /= np.linalg.norm(L)
    return np.clip((nx * L[0] + ny * L[1] + nz * L[2]) / ln, 0, 1)


def bands(v: np.ndarray, lo=0.55, hi=0.97):
    """4 cel bands from a lighting value (relative to flat = 0.62/|L|); returns -2..+1."""
    flat = 0.62
    d = (v - flat)
    return np.digitize(d, [-0.12, -0.03, 0.06]) - 2


def to_rgb(step: np.ndarray, ramp: str) -> np.ndarray:
    pal = np.array(V.RAMPS[ramp], np.uint8)
    return pal[np.clip(step, 0, 4)]


def tile_sand(rng, wet=False):
    n = T
    ripple = np.sin((np.arange(n)[None, :] * 2 * np.pi / n * 2 + fbm(n, rng) * 5.0) + np.arange(n)[:, None] * 2 * np.pi / n * 1) * 0.5 + 0.5
    h = ripple * 0.22 + fbm(n, rng, ((6, 1.0), (12, 0.6), (24, 0.4))) * 0.8
    st = 2 + bands(light(h, 1.7))
    gr = rng.random((n, n))
    st = np.where(gr < 0.018, st - 1, np.where(gr > 0.985, st + 1, st))
    peb = rng.random((n, n)) < 0.012                                  # pebbles: 2 px, dark underside
    pk = np.argwhere(peb)
    for (y, x) in pk:
        st[y % n, x % n] = 3
        st[(y + 1) % n, (x + 1) % n] = 0
    return st + (-1 if wet else 0), ("sand")


def tile_grass(rng):
    n = T
    base = fbm(n, rng, ((4, 1.0), (8, 0.6)))
    st = np.where(base > 0.6, 3, np.where(base < 0.38, 1, 2))
    st = st.copy()
    ys, xs = np.nonzero(rng.random((n, n)) < 0.075)                   # blades: 3 px tall, light tip, shadow base
    for y, x in zip(ys, xs):
        st[(y + 1) % n, x % n] = 1
        st[y % n, x % n] = 3
        st[(y - 1) % n, x % n] = 4 if base[y, x] > 0.45 else 3
    ys, xs = np.nonzero(rng.random((n, n)) < 0.02)
    for y, x in zip(ys, xs):
        st[y, x] = 0
    return st, "grass"


def tile_dirt(rng):
    n = T
    h = fbm(n, rng, ((5, 1.0), (10, 0.7), (20, 0.4)))
    st = 2 + bands(light(h, 3.4))
    r = rng.random((n, n))
    st = np.where(r < 0.03, st - 1, np.where(r > 0.975, st + 1, st))
    return st, "dirt"


def tile_cobble(rng, cells=6, ramp="stone_warm"):
    n = T
    bid, d1, d2 = voronoi(n, cells, rng, 0.7)
    edge = d2 - d1
    dome = np.clip(edge / 4.0, 0, 1) ** 0.6
    h = dome * 1.0 + fbm(n, rng, ((12, 1.0),)) * 0.12
    shade = bands(light(h, 3.2))
    tone = (np.random.default_rng(bid.max() + 5).random(cells * cells))[bid]
    base = np.where(tone < 0.3, 1, np.where(tone > 0.7, 3, 2))
    st = base + shade
    mortar = edge < 1.15
    st = np.where(mortar, 0, st)
    r = rng.random((n, n))
    st = np.where((r < 0.05) & ~mortar, st - 1, st)
    # moss in some joints
    return st, ramp


def tile_slab(rng):
    return tile_cobble(rng, 3, "stone_warm")


def tile_shallow(rng):
    st, _ = tile_sand(rng)
    return st + 1, "sand"


def tile_rockfloor(rng):
    n = T
    bid, d1, d2 = voronoi(n, 4, rng, 0.9)
    h = np.clip((d2 - d1) / 6.0, 0, 1) * 0.7 + fbm(n, rng, ((8, 1.0), (16, 0.6))) * 0.5
    st = 2 + bands(light(h, 3.6))
    st = np.where(d2 - d1 < 1.0, 0, st)
    return st, "rock_basalt"


GROUND = [("sand_dry", tile_sand), ("sand_wet", lambda r: tile_sand(r, True)), ("grass", tile_grass), ("dirt", tile_dirt),
          ("cobble", tile_cobble), ("slab", tile_slab), ("shallow_bed", tile_shallow), ("rock_floor", tile_rockfloor)]


def make_ground():
    OUT.mkdir(parents=True, exist_ok=True)
    atlas = np.zeros((T * len(GROUND), T * 4, 4), np.uint8)
    atlas[..., 3] = 255
    man = {}
    for r, (name, fn) in enumerate(GROUND):
        for c in range(4):
            rng = np.random.default_rng(100 * r + c + 7)
            st, ramp = fn(rng)
            rgb = to_rgb(st, ramp)
            if name == "sand_wet":
                rgb = to_rgb(np.clip(st, 0, 4), "sand")
            atlas[r * T:(r + 1) * T, c * T:(c + 1) * T, :3] = rgb
        man[name] = {"row": r, "variants": 4, "tile": T, "ramp": GROUND[r][0]}
    Image.fromarray(atlas, "RGBA").save(OUT / "ground_atlas.png")
    (OUT / "ground_manifest.json").write_text(json.dumps({"tile_px": T, "px_per_m": 24, "rows": [g[0] for g in GROUND], "variants": 4}, indent=1))
    print("ground atlas", atlas.shape)


# ---- deck planks, hull strakes, sail -----------------------------------------------------------------------------------------
def make_deck():
    n = T
    rng = np.random.default_rng(31)
    out = np.zeros((n, n, 4), np.uint8)
    out[..., 3] = 255
    st = np.zeros((n, n), int)
    pw = 6
    for p in range(n // pw):
        y0 = p * pw
        tone = [2, 3, 2, 1, 3, 2, 2, 3][p % 8]
        off = int(rng.integers(0, n))
        for y in range(y0, y0 + pw):
            for x in range(n):
                s = tone
                if y == y0:
                    s = 0                                                   # seam (caulked, dark)
                elif y == y0 + 1:
                    s = min(tone + 1, 4)                                    # lit edge of the plank
                elif y == y0 + pw - 1:
                    s = max(tone - 1, 0)
                if (x + off) % n in (0, 1) and y > y0:
                    s = 0 if (x + off) % n == 0 else max(tone - 1, 0)       # butt joint
                if (x + off) % n in (4, n // 2 + 4) and y in (y0 + 2, y0 + 3) and (x + off) % n != 0:
                    s = 0 if y == y0 + 3 else min(tone + 1, 4)             # nail head + glint
                st[y, x] = s
        g = rng.random((n, n))
        for y in range(y0 + 2, y0 + pw - 1):
            for x in range(n):
                if g[y, x] < 0.07 and st[y, x] == tone:
                    st[y, x] = max(tone - 1, 0)
                elif g[y, x] > 0.95 and st[y, x] == tone:
                    st[y, x] = min(tone + 1, 4)
    out[..., :3] = to_rgb(st, "wood_pale")
    Image.fromarray(out, "RGBA").save(OUT / "deck_planks.png")
    # worn variant (washed grey, for the foc'sle)
    out2 = out.copy()
    out2[..., :3] = to_rgb(np.clip(st - 1, 0, 4), "wood_pale")
    Image.fromarray(out2, "RGBA").save(OUT / "deck_planks_dark.png")


def make_hull():
    """Clinker strakes: horizontal boards 8 px tall, lit top edge, dark overlap shadow, a tarred waterline band. 48 x 48 px (2 m)."""
    n = T
    rng = np.random.default_rng(32)
    st = np.zeros((n, n), int)
    for b in range(n // 8):
        y0 = b * 8
        tone = [2, 3, 2, 2, 3, 2][b % 6]
        off = int(rng.integers(0, n))
        for y in range(y0, y0 + 8):
            for x in range(n):
                s = tone
                k = y - y0
                s = {0: tone + 1, 1: tone + 1, 6: tone - 1, 7: 0}.get(k, tone)
                if (x + off) % n == 0:
                    s = 0
                st[y, x] = s
    g = rng.random((n, n))
    st = np.where(g < 0.06, st - 1, np.where(g > 0.96, st + 1, st))
    out = np.zeros((n, n, 4), np.uint8)
    out[..., 3] = 255
    out[..., :3] = to_rgb(st, "hull_oak")
    Image.fromarray(out, "RGBA").save(OUT / "hull_strakes.png")


def make_sail(w=96, h=120):
    """Patched cream canvas with seam lines and a rope-bolt edge. Billow shading is done by the sail shader (3 bands from the normal)."""
    rng = np.random.default_rng(33)
    st = np.full((h, w), 2)
    for x in range(0, w, 12):                                               # cloths
        st[:, x] = 1
        st[:, x + 1:x + 2] = 3
    for y in range(0, h, 40):
        pass
    for (px, py, pw_, ph) in ((18, 30, 20, 16), (60, 78, 24, 18)):           # patches
        st[py:py + ph, px:px + pw_] = 1
        st[py, px:px + pw_] = 3
        st[py:py + ph, px] = 3
        st[py + ph - 1, px:px + pw_] = 0
        st[py:py + ph, px + pw_ - 1] = 0
        for x in range(px + 2, px + pw_ - 2, 3):
            st[py + 2, x] = 0
    g = rng.random((h, w))
    st = np.where(g < 0.05, st - 1, np.where(g > 0.97, st + 1, st))
    for x in range(w):
        st[0:2, x] = 3
        st[h - 2:h, x] = 1
    st[:, 0:2] = 3
    st[:, w - 2:w] = 1
    out = np.zeros((h, w, 4), np.uint8)
    out[..., 3] = 255
    out[..., :3] = to_rgb(np.clip(st, 0, 4), "cloth_cream")
    for x in range(w):                                                      # rope bolt
        out[0, x, :3] = V.RAMPS["rope_hemp"][2]
        out[h - 1, x, :3] = V.RAMPS["rope_hemp"][1]
    out[:, 0, :3] = V.RAMPS["rope_hemp"][2]
    out[:, w - 1, :3] = V.RAMPS["rope_hemp"][1]
    Image.fromarray(out, "RGBA").save(OUT / "sail_canvas.png")


def make_noise(n=128):
    """Tileable fbm noise, 3 independent channels, for the water / terrain shaders (linear filter, repeat)."""
    out = np.zeros((n, n, 4), np.uint8)
    out[..., 3] = 255
    for ch in range(3):
        rng = np.random.default_rng(900 + ch)
        f = fbm(n, rng, ((4, 1.0), (8, 0.55), (16, 0.3), (32, 0.15)))
        f = (f - f.min()) / (f.max() - f.min())
        out[..., ch] = (f * 255).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(OUT / "noise_128.png")


if __name__ == "__main__":
    make_noise()
    make_ground()
    make_deck()
    make_hull()
    make_sail()
    # preview at 3x
    names = ["ground_atlas", "deck_planks", "hull_strakes", "sail_canvas"]
    ims = [Image.open(OUT / f"{n}.png") for n in names]
    W = sum(i.width for i in ims) + 10 * len(ims)
    H = max(i.height for i in ims)
    c = Image.new("RGBA", (W, H), (60, 60, 70, 255))
    x = 0
    for i in ims:
        c.alpha_composite(i, (x, 0))
        x += i.width + 10
    c = c.resize((c.width * 2, c.height * 2), Image.NEAREST)
    c.save("/tmp/ground_preview.png")
