"""Tiles, props, ship and icon placeholders (Module A4). All palette-locked, 24 px/m (ship: 12 px/m 'sea scale')."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from pxdraw import RAMPS, Canvas, periodic_noise

TILE = 48  # 2 m x 2 m at 24 px/m


# ------------------------------------------------------------------ tiles (seamless)
def _quant(v: np.ndarray, thr: list[float]) -> np.ndarray:
    s = np.zeros(v.shape, dtype=int)
    for t in thr:
        s += v >= t
    return s


def _tile_from_steps(steps: np.ndarray, ramp: str) -> Image.Image:
    cols = np.array(RAMPS[ramp], dtype=np.uint8)
    rgb = cols[np.clip(steps, 0, 4)]
    a = np.dstack([rgb, np.full(steps.shape, 255, np.uint8)])
    return Image.fromarray(a, "RGBA")


def tile_sand(seed=1) -> Image.Image:
    rng = np.random.default_rng(seed)
    n = 0.35 * periodic_noise(TILE, 3, rng) + 0.3 * periodic_noise(TILE, 8, rng) + 0.35 * periodic_noise(TILE, 24, rng)
    s = _quant(n, [0.27, 0.40, 0.62, 0.76])
    s = np.where(s == 0, 1, s)
    s = np.where(s == 4, 3, s)
    sp = rng.random((TILE, TILE))
    s = np.where(sp > 0.985, 1, s)
    s = np.where(sp < 0.006, 4, s)
    return _tile_from_steps(s, "sand")


def tile_grass(seed=2) -> Image.Image:
    rng = np.random.default_rng(seed)
    n = 0.5 * periodic_noise(TILE, 4, rng) + 0.5 * periodic_noise(TILE, 12, rng)
    s = _quant(n, [0.34, 0.47, 0.60, 0.74])
    s = np.where(s == 0, 1, s)
    tufts = rng.random((TILE, TILE)) > 0.965
    up = np.roll(tufts, -1, 0)
    s = np.where(tufts, 4, s)
    s = np.where(up & ~tufts, 3, s)
    return _tile_from_steps(s, "grass")


def tile_dirt(seed=3) -> Image.Image:
    rng = np.random.default_rng(seed)
    n = 0.6 * periodic_noise(TILE, 5, rng) + 0.4 * periodic_noise(TILE, 14, rng)
    s = _quant(n, [0.30, 0.45, 0.62, 0.78])
    s = np.where(rng.random((TILE, TILE)) > 0.98, 0, s)
    return _tile_from_steps(np.maximum(s, 0), "dirt")


def tile_cobble(seed=4) -> Image.Image:
    rng = np.random.default_rng(seed)
    pts = []
    k = 4
    for gy in range(k):
        for gx in range(k):
            pts.append(((gx + 0.5 + (rng.random() - 0.5) * 0.6) * TILE / k, (gy + 0.5 + (rng.random() - 0.5) * 0.6) * TILE / k))
    yy, xx = np.mgrid[0:TILE, 0:TILE]
    best = np.full((TILE, TILE), 1e9)
    second = np.full((TILE, TILE), 1e9)
    idx = np.zeros((TILE, TILE), int)
    for i, (px, py) in enumerate(pts):
        d = np.full((TILE, TILE), 1e9)
        for ox in (-TILE, 0, TILE):
            for oy in (-TILE, 0, TILE):
                d = np.minimum(d, np.hypot(xx + 0.5 - px - ox, yy + 0.5 - py - oy))
        upd = d < best
        second = np.where(upd, best, np.minimum(second, d))
        idx = np.where(upd, i, idx)
        best = np.minimum(best, d)
    edge = (second - best) < 1.6
    base = 2 + (np.array([rng.integers(-1, 2) for _ in pts])[idx])
    hl = ((xx % TILE) < 0) | (best < 4)
    s = np.where(edge, 0, np.clip(base + (best < 3.5), 1, 3))
    s = np.where(~edge & (best > 7.5), np.maximum(s - 1, 1), s)
    return _tile_from_steps(s, "stone_warm")


def tile_planks(seed=5) -> Image.Image:
    rng = np.random.default_rng(seed)
    s = np.full((TILE, TILE), 2)
    ph = 8
    for r in range(TILE // ph):
        y0 = r * ph
        shade = rng.integers(1, 4)
        s[y0:y0 + ph - 1, :] = shade
        s[y0 + ph - 1, :] = 0
        off = int(rng.integers(0, TILE))
        s[y0:y0 + ph, off % TILE] = 0
        grain = periodic_noise(TILE, 16, rng)[y0:y0 + ph - 1]
        s[y0:y0 + ph - 1, :] = np.where(grain > 0.72, np.minimum(s[y0:y0 + ph - 1, :] + 1, 4), s[y0:y0 + ph - 1, :])
        for nx in ((off + 2) % TILE, (off - 3) % TILE):
            s[y0 + 3, nx] = 0
    return _tile_from_steps(s, "wood")


def tile_snow(seed=6) -> Image.Image:
    rng = np.random.default_rng(seed)
    n = 0.5 * periodic_noise(TILE, 3, rng) + 0.5 * periodic_noise(TILE, 10, rng)
    s = _quant(n, [0.32, 0.45, 0.58, 0.70]) + 1
    s = np.clip(s, 1, 4)
    s = np.where(rng.random((TILE, TILE)) > 0.992, 4, s)
    return _tile_from_steps(s, "ice")


def tile_rock(seed=8) -> Image.Image:
    """bare rock: cool stone, large flat facets with cracks."""
    rng = np.random.default_rng(seed)
    n = 0.55 * periodic_noise(TILE, 4, rng) + 0.45 * periodic_noise(TILE, 12, rng)
    s = _quant(n, [0.33, 0.47, 0.61, 0.76])
    crack = periodic_noise(TILE, 9, rng)
    s = np.where((crack > 0.50) & (crack < 0.535), 0, s)
    return _tile_from_steps(s, "stone_cool")


def tile_ice(seed=9) -> Image.Image:
    """sea ice / glacier: darker and bluer than snow, with fracture lines."""
    rng = np.random.default_rng(seed)
    n = 0.6 * periodic_noise(TILE, 3, rng) + 0.4 * periodic_noise(TILE, 8, rng)
    s = _quant(n, [0.30, 0.46, 0.62, 0.78])
    fr = periodic_noise(TILE, 7, rng)
    s = np.where((fr > 0.48) & (fr < 0.515), 0, s)
    return _tile_from_steps(s, "ice")


def tile_water_frames(n_frames=4, seed=7, ramp="sea_deep") -> list[Image.Image]:
    """seamless in space AND time: noise is shifted by TILE/n px per frame."""
    rng = np.random.default_rng(seed)
    big = 0.6 * periodic_noise(TILE, 4, rng) + 0.4 * periodic_noise(TILE, 8, rng)
    frames = []
    for f in range(n_frames):
        sh = np.roll(big, (f * TILE // n_frames), axis=1)
        s = _quant(sh, [0.30, 0.44, 0.58, 0.74])
        crest = (sh > 0.70) & (np.roll(sh, 1, 0) <= 0.70)
        s = np.where(crest, 4, s)
        frames.append(_tile_from_steps(s, ramp))
    return frames


# ------------------------------------------------------------------ props
def prop_barrel() -> Canvas:
    c = Canvas(16, 24)
    c.cylinder_v(2, 14, 4, 22, "wood")
    c.ellipsoid(8, 5, 6, 2.6, "wood", bias=1)
    c.ellipsoid(8, 21, 6, 2.0, "wood", bias=-1, clip=c.yy > 21)
    for y in (8, 17):
        m = (c.xx >= 2) & (c.xx < 14) & (c.yy >= y) & (c.yy < y + 2)
        c.paint(m, None, "iron", flat_step=2)
    c.outline()
    return c


def prop_crate() -> Canvas:
    c = Canvas(28, 28)
    c.poly([(3, 9), (11, 3), (25, 3), (17, 9)], "wood", step=3)  # top
    c.poly([(3, 9), (17, 9), (17, 25), (3, 25)], "wood", step=2)  # front
    c.poly([(17, 9), (25, 3), (25, 19), (17, 25)], "wood", step=1)  # side
    for y in (13, 17, 21):
        c.rect(3, y, 17, y + 1, "wood", step=1)
    c.rect(3, 9, 5, 25, "wood", step=1)
    c.rect(15, 9, 17, 25, "wood", step=1)
    c.outline()
    return c


def prop_chest() -> Canvas:
    c = Canvas(28, 24)
    c.poly([(3, 9), (17, 9), (17, 21), (3, 21)], "wood", step=2)
    c.poly([(17, 9), (25, 5), (25, 17), (17, 21)], "wood", step=1)
    c.ellipsoid(10, 9, 7.5, 6, "wood", bias=1, clip=c.yy < 9)
    c.poly([(17, 9), (25, 5), (25, 8), (17, 9)], "wood", step=1)
    c.rect(3, 12, 17, 13, "gold", step=2)
    c.rect(8, 11, 12, 16, "gold", step=3)
    c.dots([(10, 13)], "iron", 0)
    c.outline()
    return c


def prop_rock() -> Canvas:
    c = Canvas(36, 24)
    c.ellipsoid(14, 15, 11, 7.5, "stone_cool")
    c.ellipsoid(24, 17, 9, 6, "stone_cool", bias=-1)
    c.ellipsoid(12, 12, 4, 2.6, "stone_cool", bias=2)
    c.outline()
    return c


def prop_palm(s: float = 1.0) -> Canvas:
    """s = size factor. 1.0 is a 4 m young palm; 1.8 is a 7 m grown palm."""
    c = Canvas(int(72 * s), int(104 * s))
    pts = [(34 * s, 100 * s), (36 * s, 80 * s), (40 * s, 62 * s), (46 * s, 46 * s), (54 * s, 34 * s)]
    for a, b, r0, r1 in zip(pts, pts[1:], (4.2, 3.6, 3.2, 2.8), (3.6, 3.2, 2.8, 2.4)):
        c.capsule(a, b, r0 * (0.6 + 0.4 * s), "wood", r1=r1 * (0.6 + 0.4 * s))
    top = pts[-1]
    for ring in range(int(6 * s)):  # trunk rings
        y = (94 - ring * 10) * s
        m = (c.rgba[..., 3] > 0) & (abs(c.yy - y) < 0.8)
        c.paint(m & (c.ramp == 3), None, "wood", flat_step=1)
    fronds = [(-150, 26), (-120, 28), (-85, 22), (-55, 28), (-25, 26), (-190, 20), (15, 20), (-100, 14)]
    for k, (deg, ln) in enumerate(fronds):
        th = math.radians(deg)
        x, y = top
        prev = (x, y)
        steps = 6
        ln *= s
        for j in range(1, steps + 1):
            t = j / steps
            px = x + math.cos(th) * ln * t
            py = y + math.sin(th) * ln * t + 22 * s * t * t  # droop
            w = 0.6 + 0.4 * s
            c.capsule(prev, (px, py), (3.0 - 2.4 * t + 0.4) * w, "palm_frond", r1=(2.6 - 2.2 * t + 0.4) * w, bias=1 if math.sin(th) < -0.5 else 0)
            prev = (px, py)
    c.ellipsoid(top[0], top[1] + 1, 3.2 * s ** 0.5, 3.0 * s ** 0.5, "wood", bias=-1)
    c.outline()
    return c


def prop_campfire_frames(n=4) -> list[Canvas]:
    out = []
    for f in range(n):
        c = Canvas(28, 28)
        c.capsule((5, 24), (20, 21), 2.4, "wood", bias=-1)
        c.capsule((22, 24), (7, 21), 2.4, "wood")
        ph = f / n * 2 * math.pi
        for k, (h, w, ramp_step) in enumerate(((13, 5.5, 0), (10, 4.0, 1), (6.5, 2.4, 2))):
            hh = h + 1.6 * math.sin(ph + k) + (1 if k == 0 else 0)
            cxf = 14 + 1.0 * math.sin(ph * 2 + k)
            dx = (c.xx - cxf) / w
            dy = (c.yy - 20) / hh
            m = (dx * dx * (1 + np.clip(-dy, 0, 2) * 1.6) + (np.clip(dy, -9, 0) ** 2) <= 1) & (c.yy < 22) & (c.yy > 20 - hh)
            c.paint(m, None, "fire", flat_step=[2, 3, 4][k])
        c.outline()
        out.append(c)
    return out


def prop_hut() -> Canvas:
    c = Canvas(104, 104)
    c.rect(14, 52, 90, 94, "wood", step=2)  # front wall
    for y in range(56, 94, 6):
        c.rect(14, y, 90, y + 1, "wood", step=1)
    c.poly([(90, 52), (100, 46), (100, 88), (90, 94)], "wood", step=1)  # side wall
    c.rect(44, 66, 62, 94, "hull_oak", step=1)  # door
    c.rect(44, 66, 62, 67, "hull_oak", step=0)
    c.rect(20, 62, 34, 74, "fire", step=3)  # lit window
    c.rect(20, 62, 34, 63, "wood", step=0)
    c.rect(26, 62, 28, 74, "wood", step=0)
    c.rect(20, 74, 34, 76, "wood", step=3)
    roof_front = [(6, 54), (52, 14), (98, 54)]
    c.poly(roof_front, "roof_teal", step=2)
    c.poly([(98, 54), (52, 14), (62, 10), (108, 46)], "roof_teal", step=1)
    for k, y in enumerate(range(22, 54, 5)):  # shingle rows
        span = (y - 14) * 1.15
        c.rect(52 - span, y, 52 + span, y + 1, "roof_teal", step=1)
        for x in np.arange(52 - span + (k % 2) * 3, 52 + span, 6):
            c.dots([(x, y + 2), (x, y + 3)], "roof_teal", 1)
    c.rect(6, 53, 98, 56, "roof_teal", step=0)  # eave shadow line
    c.outline()
    return c


def prop_lantern() -> Canvas:
    c = Canvas(14, 22)
    c.rect(4, 2, 10, 4, "iron", step=2)
    c.rect(5, 0, 9, 2, "iron", step=1)
    c.ellipsoid(7, 11, 4.5, 6, "fire", bias=1)
    c.rect(3, 17, 11, 20, "iron", step=2)
    c.rect(6, 4, 7, 17, "iron", step=0)
    c.outline()
    return c


def prop_cannon() -> Canvas:
    c = Canvas(40, 28)
    c.poly([(8, 18), (30, 18), (32, 24), (6, 24)], "wood", step=2)
    c.capsule((6, 14), (34, 11), 4.6, "iron", r1=3.8)
    c.ellipsoid(34.5, 11, 1.8, 3.6, "iron", bias=-1)
    c.ellipsoid(8, 24, 4.5, 4.5, "wood", bias=-1)
    c.ellipsoid(28, 24, 4.5, 4.5, "wood", bias=-1)
    c.dots([(8, 24), (28, 24)], "iron", 2)
    c.outline()
    return c


def ship_sloop() -> Canvas:
    """3/4 view heading east, 'sea scale' 12 px/m -> about 22 m long. Placeholder: the real ship is a 3D model (Art Bible)."""
    c = Canvas(272, 200)
    hull = [(14, 120), (60, 150), (200, 150), (254, 112), (236, 112), (200, 126), (70, 126), (36, 112)]
    c.poly(hull, "hull_oak", step=2)
    c.poly([(36, 112), (70, 126), (200, 126), (236, 112), (254, 112), (236, 104), (40, 104)], "wood", step=3)  # deck rim
    for k in range(4):
        y = 132 + k * 5
        c.rect(40 + k * 6, y, 214 - k * 4, y + 1, "hull_oak", step=1)
    c.rect(60, 150, 200, 153, "hull_oak", step=0)
    # masts
    c.cylinder_v(86, 92, 22, 114, "wood")
    c.cylinder_v(156, 162, 34, 114, "wood")
    # sails: bulging towards the viewer
    for (x0, x1, y0, y1) in ((92, 150, 30, 94), (162, 218, 42, 96)):
        dxs = (c.xx - (x0 + x1) / 2) / ((x1 - x0) / 2)
        dys = (c.yy - (y0 + y1) / 2) / ((y1 - y0) / 2)
        m = (c.xx >= x0) & (c.xx < x1) & (c.yy >= y0) & (c.yy < y1 + 6 * (1 - dxs * dxs) * 0)
        nz = np.sqrt(np.clip(1 - 0.55 * dxs * dxs, 0, 1))
        c.paint(m, (dxs * 0.8, dys * 0.4, nz), "cloth_cream")
        c.rect(x0, y0, x1, y0 + 2, "wood", step=2)
    # flag + bowsprit
    c.poly([(86, 22), (86, 14), (104, 16)], "cloth_red", step=2)
    c.capsule((236, 108), (268, 92), 1.6, "wood")
    c.poly([(150, 94), (150, 110), (92, 110), (92, 94)], "cloth_cream", step=1) if False else None
    c.outline()
    return c


# ------------------------------------------------------------------ icons
ICON_BG = {"food": "wood", "water": "sea_deep", "medicine": "cloth_red", "ship": "hull_oak", "ammo": "iron", "tool": "stone_cool", "money": "gold", "misc": "cloth_cream"}


def make_icon(code: str, category: str) -> Image.Image:
    size = 24
    bg = RAMPS[ICON_BG.get(category, "misc")]
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=4, fill=bg[0] + (255,))
    d.rounded_rectangle((1, 1, size - 2, size - 2), radius=3, fill=bg[2] + (255,))
    d.line((2, 2, size - 3, 2), fill=bg[3] + (255,))
    d.line((2, size - 3, size - 3, size - 3), fill=bg[1] + (255,))
    font = ImageFont.load_default()
    tw = d.textlength(code, font=font)
    d.text(((size - tw) / 2 + 1, 6), code, fill=bg[0] + (255,), font=font)
    d.text(((size - tw) / 2, 5), code, fill=bg[4] + (255,), font=font)
    a = np.asarray(im).copy()
    # snap anti-aliased text pixels to palette steps of the ramp (default font is bitmap, but be safe)
    cols = np.array(bg)
    m = a[..., 3] > 0
    flat = a[m][:, :3].astype(int)
    dist = ((flat[:, None, :] - cols[None, :, :]) ** 2).sum(2)
    a[m, :3] = cols[dist.argmin(1)]
    a[..., 3] = np.where(m, 255, 0)
    return Image.fromarray(a, "RGBA")
