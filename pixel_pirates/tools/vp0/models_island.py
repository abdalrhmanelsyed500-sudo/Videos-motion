"""VP-0 voxel models: island and harbour set (24 px/m). Palms, rocks, scrub, three period buildings, pier, lamp post, signpost."""
from __future__ import annotations

import numpy as np

from voxel import Vox, hash3, tone_noise, tone_planks, tone_stones

(TRUNK, FROND, FROND2, ROCK, MOSS, SAND, WALL, TIMBER, ROOF, STONE, DOOR, GLASS, THATCH, IRON, BRASS, GRASS, FLOWER, WOOD, TAR, ROPE,
 GLOW, TEAL, CLOTH_R, CLOTH_C) = range(1, 25)


def _new(X, Y, Z) -> Vox:
    v = Vox(X, Y, Z)
    v.define(TRUNK, "dirt", 3)
    v.define(FROND, "palm_frond", 2)
    v.define(FROND2, "palm_frond", 3)
    v.define(ROCK, "rock_basalt", 3)
    v.define(MOSS, "grass", 2)
    v.define(SAND, "sand", 2)
    v.define(WALL, "plaster", 2)
    v.define(TIMBER, "wood", 1)
    v.define(ROOF, "terracotta", 2)
    v.define(STONE, "stone_warm", 2)
    v.define(DOOR, "wood", 2)
    v.define(GLASS, "cloth_blue", 1, flat=True)
    v.define(THATCH, "thatch", 2)
    v.define(IRON, "iron", 2)
    v.define(BRASS, "brass", 2)
    v.define(GRASS, "foliage", 2)
    v.define(FLOWER, "cloth_red", 3)
    v.define(WOOD, "wood_pale", 2)
    v.define(TAR, "tar", 1)
    v.define(ROPE, "rope_hemp", 2)
    v.define(GLOW, "fire", 4, emissive=True)
    v.define(TEAL, "roof_teal", 2)
    v.define(CLOTH_R, "cloth_red", 2)
    v.define(CLOTH_C, "cloth_cream", 2)
    return v


# ---- palms ---------------------------------------------------------------------------------------------------------------------
def palm(seed=0, height=150, lean=18.0, fronds=10) -> Vox:
    rng = np.random.default_rng(seed)
    S = 150
    v = _new(S, S, height + 40)
    cx, cy = S / 2 - lean * 0.4, S / 2
    pts = []
    n = 26
    for i in range(n + 1):
        t = i / n
        pts.append((cx + lean * t ** 1.7, cy + 3 * np.sin(t * 2.2 + seed), t * height))
    for i in range(n):
        r0 = 4.6 - 1.6 * i / n
        r1 = 4.6 - 1.6 * (i + 1) / n
        v.tube(pts[i], pts[i + 1], r0, TRUNK, r1=r1,
               tone=lambda x, y, z: np.where(np.floor(z / 3.2) % 2 == 0, -1, 0) + np.where(hash3(x, y, z, 6) < 0.1, 1, 0))
    v.cyl(pts[0][0], pts[0][1], 0, 5, 6.6, TRUNK, r1=4.8, tone=tone_noise(2, 0.25))
    topx, topy, topz = pts[-1]
    v.ell(topx, topy, topz + 2, 5, 5, 4, TRUNK)
    for i in range(3):                                                                    # coconuts
        a = i * 2.1 + seed
        v.ell(topx + 4 * np.cos(a), topy + 4 * np.sin(a), topz - 1.5, 2.6, 2.6, 2.6, WOOD, tone=-1)
    for k in range(fronds):
        a = k * 2 * np.pi / fronds + rng.uniform(-0.2, 0.2)
        reach = rng.uniform(54, 66)
        rise = rng.uniform(14, 26)
        droop = rng.uniform(26, 40)
        prev = None
        steps = 18
        for j in range(steps + 1):
            s = j / steps
            hx = reach * s
            hz = rise * np.sin(np.pi * 0.85 * s) - droop * s ** 2.2
            p = (topx + hx * np.cos(a), topy + hx * np.sin(a) * 0.9, topz + 3 + hz)
            if prev is not None:
                v.tube(prev, p, 1.5 - 0.7 * s, FROND, tone=-1)
                # leaflets: two rows angled outwards and drooping, longer in the middle
                L = (5.5 + 8.0 * np.sin(np.pi * s)) * (1.0 - 0.2 * s)
                for sgn in (-1, 1):
                    nx, ny = -np.sin(a) * sgn, np.cos(a) * sgn
                    q = (p[0] + nx * L * 0.85 + np.cos(a) * 2.5, p[1] + ny * L * 0.85 + np.sin(a) * 2.5, p[2] - L * 0.42)
                    v.tube(p, q, 1.25, FROND2 if (j + (sgn > 0)) % 2 == 0 else FROND, r1=0.7,
                           tone=lambda x, y, z: np.where(hash3(x, y, z, 9) < 0.3, 1, 0))
            prev = p
    return v


# ---- rocks ---------------------------------------------------------------------------------------------------------------------
def rock(seed=0, w=72, d=56, h=44, moss=0.5) -> Vox:
    rng = np.random.default_rng(seed)
    v = _new(w + 8, d + 8, h + 6)
    blobs = []
    nb = 5
    for i in range(nb):
        blobs.append((rng.uniform(0.25, 0.75) * w + 4, rng.uniform(0.3, 0.7) * d + 4, rng.uniform(0.15, 0.45) * h,
                      rng.uniform(0.22, 0.34) * w, rng.uniform(0.25, 0.38) * d, rng.uniform(0.45, 0.8) * h))
    nz = rng.uniform(0, 100)

    def field(x, y, z):
        f = np.full_like(x, -1.0)
        for (bx, by, bz, rx, ry, rz) in blobs:
            f = np.maximum(f, 1.0 - np.sqrt(((x - bx) / rx) ** 2 + ((y - by) / ry) ** 2 + ((z - bz) / rz) ** 2))
        f += (hash3(x // 3, y // 3, z // 3, int(nz)) - 0.5) * 0.18
        # strata: ledge every 9 voxels cuts the profile in terraces
        f += 0.06 * np.sin(z / 4.5)
        return f > 0.0

    v.where(lambda x, y, z: field(x, y, z) & (z > 0.5), ROCK,
            tone=lambda x, y, z: np.where(np.floor(z / 7.0) % 2 == 0, 0, -1) + np.where(hash3(x, y, z, 3) < 0.14, -1, 0) + np.where(hash3(x, y, z, 5) > 0.9, 1, 0))
    # moss / scrub on the upward-facing surface
    top = np.zeros((v.X, v.Y), np.int32) - 1
    solid = v.mat > 0
    zi = np.arange(v.Z)[None, None, :]
    top = np.where(solid.any(axis=2), (solid * (zi + 1)).max(axis=2) - 1, -1)
    for x in range(v.X):
        for y in range(v.Y):
            z = top[x, y]
            if z > 4 and hash3(x // 2, y // 2, 0, 11) < moss * (0.4 + 0.6 * z / h):
                v.mat[x, y, z] = MOSS
                v.tone[x, y, z] = -1 if hash3(x, y, 1, 3) < 0.3 else 0
                if z > 1 and hash3(x, y, 3, 8) < 0.5:
                    v.mat[x, y, z - 1] = MOSS
    return v


def bush(seed=0, r=26) -> Vox:
    rng = np.random.default_rng(seed)
    v = _new(2 * r + 10, 2 * r + 10, r + 12)
    c = r + 5
    for i in range(7):
        a = rng.uniform(0, 6.28)
        rr = rng.uniform(0, r * 0.55)
        v.ell(c + rr * np.cos(a), c + rr * np.sin(a) * 0.7, rng.uniform(5, 11), rng.uniform(10, 15), rng.uniform(8, 12), rng.uniform(7, 12), GRASS,
              tone=lambda x, y, z: np.where(hash3(x, y, z, 5) < 0.28, -1, np.where(hash3(x, y, z, 6) > 0.72, 1, 0)) + (z > 12) * 1)
    for i in range(5):
        a = rng.uniform(0, 6.28)
        rr = rng.uniform(r * 0.2, r * 0.7)
        v.ell(c + rr * np.cos(a), c + rr * np.sin(a) * 0.7, rng.uniform(10, 17), 1.6, 1.6, 1.6, FLOWER)
    v.carve(lambda x, y, z: z < 0.6)
    return v


# ---- buildings -----------------------------------------------------------------------------------------------------------------
def _gable_roof(v, x0, x1, y0, y1, zb, rise, mat, thick=3, tone=None, ridge_axis="x", overhang=3):
    yc = (y0 + y1) / 2.0
    half = (y1 - y0) / 2.0 + overhang
    xc = (x0 + x1) / 2.0
    if ridge_axis == "x":
        def roof(x, y, z):
            h = rise * (1 - np.abs(y - yc) / half)
            return (x >= x0 - overhang) & (x < x1 + overhang) & (h > 0) & (z >= zb + (rise - h) * 0 + 0) & (z < zb + h) & (z >= zb + h - thick)
        v.where(roof, mat, tone=tone, lo=(x0 - overhang, y0 - overhang, zb), hi=(x1 + overhang, y1 + overhang, zb + rise + 1))
    else:
        halfx = (x1 - x0) / 2.0 + overhang

        def roof(x, y, z):
            h = rise * (1 - np.abs(x - xc) / halfx)
            return (y >= y0 - overhang) & (y < y1 + overhang) & (h > 0) & (z < zb + h) & (z >= zb + h - thick)
        v.where(roof, mat, tone=tone, lo=(x0 - overhang, y0 - overhang, zb), hi=(x1 + overhang, y1 + overhang, zb + rise + 1))


def house_a() -> Vox:
    """Plaster cottage with timber frame, terracotta roof (ridge along x), chimney, door and two shuttered windows. 6.0 x 4.2 m."""
    W, D, WH, RISE = 144, 100, 78, 38
    v = _new(W + 16, D + 20, WH + RISE + 36)
    x0, y0 = 8, 8
    v.box(x0, y0, 0, x0 + W, y0 + D, 6, STONE, tone=tone_stones(6, 2))                                        # plinth
    v.box(x0 + 1, y0 + 1, 6, x0 + W - 1, y0 + D - 1, WH, WALL, tone=tone_noise(4, 0.06))
    # timber frame on the front and the visible gable ends
    for xx in (x0, x0 + W - 4, x0 + W // 2 - 2):
        v.box(xx, y0 - 1, 6, xx + 4, y0 + 1, WH, TIMBER, tone=tone_planks("z", 4, 3, 0.2))
    v.box(x0, y0 - 1, 42, x0 + W, y0 + 1, 46, TIMBER, tone=tone_planks("x", 4, 3, 0.2))
    v.box(x0, y0 - 1, WH - 4, x0 + W, y0 + 1, WH, TIMBER)
    for (a, b) in ((x0 + 6, x0 + 28), (x0 + W // 2 + 6, x0 + 44), (x0 + W - 24, x0 + W - 4)):
        pass
    # braces
    v.tube((x0 + 4, y0, 46), (x0 + 30, y0, WH - 5), 1.7, TIMBER)
    v.tube((x0 + W - 4, y0, 46), (x0 + W - 30, y0, WH - 5), 1.7, TIMBER)
    # door
    dx = x0 + W // 2 - 26
    v.carve(lambda x, y, z: (x >= dx) & (x < dx + 18) & (z >= 6) & (z < 52) & (y < y0 + 4), lo=(dx, y0 - 2, 6), hi=(dx + 18, y0 + 5, 52))
    v.box(dx, y0 + 3, 6, dx + 18, y0 + 5, 52, DOOR, tone=tone_planks("z", 3, 5))
    v.box(dx - 2, y0 - 1, 52, dx + 20, y0 + 1, 55, TIMBER)
    v.box(dx + 13, y0 + 2, 28, dx + 15, y0 + 4, 31, BRASS)
    v.box(dx - 3, y0 - 3, 0, dx + 21, y0 + 3, 4, STONE, tone=tone_stones(5, 5))                            # step
    v.box(dx - 1, y0 - 6, 0, dx + 19, y0 - 3, 2, STONE, tone=tone_stones(5, 6))
    # windows with shutters
    for wx in (x0 + 22, x0 + W - 46):
        v.carve(lambda x, y, z, wx=wx: (x >= wx) & (x < wx + 22) & (z >= 32) & (z < 56) & (y < y0 + 4), lo=(wx, y0 - 2, 32), hi=(wx + 22, y0 + 5, 56))
        v.box(wx, y0 + 3, 32, wx + 22, y0 + 5, 56, GLASS, tone=lambda x, y, z: np.where((np.floor(x) % 11 == 0) | (np.floor(z) % 12 == 0), -1, np.where(z > 48, 1, 0)))
        v.box(wx - 2, y0 - 1, 30, wx + 24, y0 + 2, 33, TIMBER)
        v.box(wx - 2, y0 - 1, 56, wx + 24, y0 + 1, 59, TIMBER)
        v.box(wx - 9, y0 - 1, 32, wx - 1, y0 + 1, 56, CLOTH_R, tone=tone_planks("z", 3, 8, 0.1))
        v.box(wx + 23, y0 - 1, 32, wx + 31, y0 + 1, 56, CLOTH_R, tone=tone_planks("z", 3, 9, 0.1))
        v.box(wx - 1, y0 - 3, 26, wx + 23, y0, 31, WOOD)                                                     # flower box
        for i in range(6):
            v.ell(wx + 3 + i * 3.6, y0 - 2, 33, 2.0, 1.6, 2.4, GRASS if i % 2 else FLOWER)
    # gable infill + roof
    cx = x0 + W / 2.0
    yc = y0 + D / 2.0
    v.where(lambda x, y, z: (x >= x0 + 1) & (x < x0 + W - 1) & (np.abs(y - yc) < (D / 2.0 - 1) * (1 - (z - WH) / RISE)) & (z >= WH) & (z < WH + RISE), WALL,
            lo=(x0, y0, WH), hi=(x0 + W, y0 + D, WH + RISE))
    _gable_roof(v, x0, x0 + W, y0, y0 + D, WH, RISE, ROOF, thick=3, ridge_axis="x", overhang=5,
                tone=lambda x, y, z: np.where(np.floor((y + z) / 3.5) % 2 == 0, 0, -1) + np.where(hash3(np.floor(x / 4.0), np.floor((y + z) / 3.5), 0, 3) < 0.2, 1, 0))
    v.box(x0 - 7, y0 - 7, WH - 1, x0 + W + 7, y0 - 3, WH + 3, TIMBER) if False else None
    # chimney
    v.box(x0 + W - 36, y0 + D // 2 - 8, WH, x0 + W - 22, y0 + D // 2 + 8, WH + RISE + 14, STONE, tone=tone_stones(5, 7))
    v.box(x0 + W - 38, y0 + D // 2 - 10, WH + RISE + 14, x0 + W - 20, y0 + D // 2 + 10, WH + RISE + 18, STONE)
    return v


def house_b() -> Vox:
    """Harbour master's house: stone ground floor, plaster upper floor with a hoist beam, teal roof, ridge toward the viewer. 5.0 x 4.6 m."""
    W, D, WH1, WH2, RISE = 120, 110, 56, 108, 40
    v = _new(W + 24, D + 24, WH2 + RISE + 40)
    x0, y0 = 12, 10
    v.box(x0, y0, 0, x0 + W, y0 + D, WH1, STONE, tone=tone_stones(6, 3))
    v.box(x0 - 3, y0 - 3, WH1, x0 + W + 3, y0 + D + 3, WH1 + 4, STONE, tone=tone_stones(5, 4))
    v.box(x0, y0, WH1 + 4, x0 + W, y0 + D, WH2, WALL, tone=tone_noise(8, 0.05))
    for xx in (x0, x0 + W - 4):
        v.box(xx, y0 - 1, WH1 + 4, xx + 4, y0 + 1, WH2, TIMBER, tone=tone_planks("z", 4, 3, 0.2))
    v.box(x0, y0 - 1, WH2 - 4, x0 + W, y0 + 1, WH2, TIMBER)
    # arched door (ground floor)
    dx = x0 + 18
    v.carve(lambda x, y, z: (x >= dx) & (x < dx + 24) & (y < y0 + 5) & ((z < 40) | (np.hypot(x - dx - 12, z - 40) < 12)) & (z >= 0), lo=(dx, y0 - 2, 0), hi=(dx + 24, y0 + 6, 54))
    v.box(dx + 1, y0 + 4, 0, dx + 23, y0 + 6, 38, DOOR, tone=tone_planks("z", 3, 5))
    v.where(lambda x, y, z: (np.hypot(x - dx - 12, z - 40) < 11.5) & (y >= y0 + 4) & (y < y0 + 6) & (z >= 38), DOOR, tone=tone_planks("z", 3, 5), lo=(dx, y0 + 3, 38), hi=(dx + 24, y0 + 7, 54))
    v.box(dx + 18, y0 + 3, 20, dx + 20, y0 + 5, 23, BRASS)
    # big arched window below and two windows above
    wx = x0 + W - 52
    v.carve(lambda x, y, z: (x >= wx) & (x < wx + 28) & (y < y0 + 4) & (z >= 20) & (z < 46), lo=(wx, y0 - 2, 20), hi=(wx + 28, y0 + 5, 46))
    v.box(wx, y0 + 3, 20, wx + 28, y0 + 5, 46, GLASS, tone=lambda x, y, z: np.where((np.floor(x) % 14 == 0) | (np.floor(z) % 13 == 0), -1, 0))
    v.box(wx - 3, y0 - 1, 18, wx + 31, y0 + 2, 21, STONE)
    v.box(wx - 3, y0 - 1, 46, wx + 31, y0 + 2, 49, STONE)
    for wx2 in (x0 + 18, x0 + W - 50):
        v.carve(lambda x, y, z, wx2=wx2: (x >= wx2) & (x < wx2 + 26) & (y < y0 + 4) & (z >= 70) & (z < 98), lo=(wx2, y0 - 2, 70), hi=(wx2 + 26, y0 + 5, 98))
        v.box(wx2, y0 + 3, 70, wx2 + 26, y0 + 5, 98, GLASS, tone=lambda x, y, z: np.where((np.floor(x) % 13 == 0) | (np.floor(z) % 14 == 0), -1, np.where(z > 90, 1, 0)))
        v.box(wx2 - 2, y0 - 1, 67, wx2 + 28, y0 + 2, 70, TIMBER)
        v.box(wx2 - 8, y0 - 1, 70, wx2 - 1, y0 + 1, 98, CLOTH_R, tone=tone_planks("z", 3, 8, 0.1))
        v.box(wx2 + 27, y0 - 1, 70, wx2 + 34, y0 + 1, 98, CLOTH_R, tone=tone_planks("z", 3, 9, 0.1))
    # hoist beam with block and rope
    v.box(x0 + W // 2 - 3, y0 - 20, WH2 + 8, x0 + W // 2 + 3, y0 + 4, WH2 + 14, TIMBER)
    v.tube((x0 + W // 2, y0 - 18, WH2 + 8), (x0 + W // 2, y0 - 18, WH2 - 30), 0.9, ROPE)
    v.ell(x0 + W // 2, y0 - 18, WH2 - 33, 3, 3, 4, IRON)
    # teal gable roof, ridge toward the viewer (along y)
    xc = x0 + W / 2.0
    v.where(lambda x, y, z: (y >= y0 + 1) & (y < y0 + D - 1) & (np.abs(x - xc) < (W / 2.0 - 1) * (1 - (z - WH2) / RISE)) & (z >= WH2) & (z < WH2 + RISE), WALL,
            lo=(x0, y0, WH2), hi=(x0 + W, y0 + D, WH2 + RISE))
    _gable_roof(v, x0, x0 + W, y0, y0 + D, WH2, RISE, TEAL, thick=3, ridge_axis="y", overhang=5,
                tone=lambda x, y, z: np.where(np.floor((x + z) / 4.5) % 2 == 0, 0, -1) + np.where(hash3(np.floor(y / 5.0), np.floor((x + z) / 4.5), 0, 4) < 0.25, 1, 0))
    v.box(x0 + 6, y0 + D - 30, WH2 + 4, x0 + 20, y0 + D - 14, WH2 + RISE + 12, STONE, tone=tone_stones(5, 8))
    return v


def warehouse() -> Vox:
    """Long fish warehouse: board-and-batten walls, big double door, thatch roof. 8.0 x 4.5 m."""
    W, D, WH, RISE = 192, 108, 60, 40
    v = _new(W + 20, D + 20, WH + RISE + 20)
    x0, y0 = 10, 8
    v.box(x0, y0, 0, x0 + W, y0 + D, 5, STONE, tone=tone_stones(6, 9))
    v.box(x0 + 1, y0 + 1, 5, x0 + W - 1, y0 + D - 1, WH, WOOD, tone=tone_planks("x", 4, 2, 0.14))
    v.where(lambda x, y, z: (np.floor((x - x0) / 4) % 4 == 0) & (y < y0 + 2) & (y >= y0 - 1) & (z >= 5) & (z < WH), TIMBER, lo=(x0, y0 - 1, 5), hi=(x0 + W, y0 + 2, WH))
    v.box(x0, y0 - 1, WH - 4, x0 + W, y0 + 1, WH, TIMBER)
    for xx in (x0, x0 + W - 5, x0 + W // 2 - 2):
        v.box(xx, y0 - 2, 5, xx + 5, y0 + 1, WH, TIMBER, tone=tone_planks("z", 5, 3, 0.2))
    dx = x0 + 40
    v.carve(lambda x, y, z: (x >= dx) & (x < dx + 52) & (z >= 5) & (z < 50) & (y < y0 + 5), lo=(dx, y0 - 2, 5), hi=(dx + 52, y0 + 6, 50))
    v.box(dx, y0 + 3, 5, dx + 52, y0 + 5, 50, DOOR, tone=tone_planks("z", 3, 7))
    v.box(dx + 25, y0 + 2, 5, dx + 27, y0 + 5, 50, TIMBER)
    v.box(dx - 3, y0 - 2, 50, dx + 55, y0 + 1, 54, TIMBER)
    v.tube((dx + 3, y0 + 2, 8), (dx + 24, y0 + 2, 47), 1.3, TIMBER)
    v.tube((dx + 49, y0 + 2, 8), (dx + 28, y0 + 2, 47), 1.3, TIMBER)
    v.box(dx + 20, y0 + 1, 24, dx + 24, y0 + 4, 27, IRON)
    v.box(dx + 28, y0 + 1, 24, dx + 32, y0 + 4, 27, IRON)
    yc = y0 + D / 2.0
    v.where(lambda x, y, z: (x >= x0 + 1) & (x < x0 + W - 1) & (np.abs(y - yc) < (D / 2.0 - 1) * (1 - (z - WH) / RISE)) & (z >= WH) & (z < WH + RISE), WOOD,
            tone=tone_planks("z", 4, 4, 0.1), lo=(x0, y0, WH), hi=(x0 + W, y0 + D, WH + RISE))
    _gable_roof(v, x0, x0 + W, y0, y0 + D, WH, RISE, THATCH, thick=4, ridge_axis="x", overhang=6,
                tone=lambda x, y, z: np.where(hash3(np.floor(x / 2.0), np.floor((y + z) / 3.0), 0, 5) < 0.3, -1, np.where(hash3(x, y, z, 6) > 0.8, 1, 0)))
    # crates of fish against the wall, a barrel, a drying net on the wall
    v.box(x0 + W - 60, y0 - 12, 0, x0 + W - 36, y0 - 1, 20, WOOD, tone=tone_planks("z", 5, 3))
    v.box(x0 + W - 34, y0 - 10, 0, x0 + W - 12, y0 - 1, 18, WOOD, tone=tone_planks("z", 5, 4))
    v.box(x0 + W - 56, y0 - 10, 20, x0 + W - 38, y0 - 1, 36, WOOD, tone=tone_planks("z", 5, 5))
    return v


def pier(sections=4) -> Vox:
    """A pier piece: plank deck on posts (2.4 m wide, sections x 1.5 m), seen end-on to the viewer. 1 voxel = 1/24 m."""
    L = sections * 36
    v = _new(L + 8, 66, 52)
    x0 = 4
    for i in range(sections + 1):
        xx = x0 + i * 36
        for yy in (4, 52):
            v.cyl(xx + 2, yy + 3, 0, 34, 3.6, TAR, tone=tone_noise(3 + i, 0.2))
            v.cyl(xx + 2, yy + 3, 34, 36, 4.0, IRON)
    v.box(x0, 1, 26, x0 + L + 4, 8, 31, WOOD, tone=tone_planks("x", 4, 3, 0.1))
    v.box(x0, 49, 26, x0 + L + 4, 56, 31, WOOD, tone=tone_planks("x", 4, 3, 0.1))
    v.box(x0, 1, 31, x0 + L + 4, 57, 34, WOOD, tone=tone_planks("y", 5, 4, 0.12))
    for i in range(sections):                                                                  # rope rail between posts
        for yy in (4, 52):
            v.tube((x0 + i * 36 + 2, yy + 3, 44), (x0 + i * 36 + 38, yy + 3, 41), 0.9, ROPE)
    for i in range(sections + 1):
        for yy in (4, 52):
            v.cyl(x0 + i * 36 + 2, yy + 3, 36, 46, 2.6, TAR, tone=tone_noise(i + yy, 0.2))
    return v


def lamp_post() -> Vox:
    v = _new(26, 26, 118)
    c = 13
    v.cyl(c, c, 0, 6, 5.5, IRON)
    v.cyl(c, c, 6, 92, 2.2, IRON, r1=1.7)
    v.cyl(c, c, 6, 10, 3.6, IRON)
    v.tube((c, c, 88), (c + 8, c, 96), 1.2, IRON)
    # lantern
    lx, lz = c + 8, 90
    v.cyl(lx, c, lz - 1, lz + 2, 3.6, IRON)
    v.cyl(lx, c, lz + 2, lz + 14, 3.4, GLOW)
    v.cyl(lx, c, lz + 14, lz + 17, 4.6, IRON, r1=3.0)
    v.cyl(lx, c, lz + 17, lz + 20, 2.0, IRON, r1=0.8)
    for a in (0.78, 2.35, 3.93, 5.5):
        v.tube((lx + 3.4 * np.cos(a), c + 3.4 * np.sin(a), lz + 2), (lx + 3.4 * np.cos(a), c + 3.4 * np.sin(a), lz + 14), 0.7, IRON)
    return v


def signpost() -> Vox:
    v = _new(60, 20, 90)
    v.box(26, 8, 0, 31, 13, 84, WOOD, tone=tone_planks("z", 3, 3, 0.15))
    v.box(8, 8, 56, 50, 12, 70, WOOD, tone=tone_planks("x", 4, 4, 0.1))
    v.box(24, 8, 40, 56, 12, 52, WOOD, tone=tone_planks("x", 4, 5, 0.1))
    v.box(12, 7, 60, 18, 8, 66, IRON)
    v.box(30, 7, 44, 38, 8, 48, IRON)
    return v


MODELS = {
    "palm_a": (lambda: palm(1, 150, 20.0, 10), 1),
    "palm_b": (lambda: palm(2, 124, -14.0, 9), 1),
    "palm_c": (lambda: palm(3, 92, 10.0, 8), 1),
    "rock_a": (lambda: rock(1, 80, 60, 50, 0.35), 1),
    "rock_b": (lambda: rock(2, 52, 40, 30, 0.2), 1),
    "rock_c": (lambda: rock(3, 120, 84, 78, 0.5), 1),
    "bush_a": (lambda: bush(1, 26), 1),
    "bush_b": (lambda: bush(2, 18), 1),
    "house_a": (house_a, 1),
    "house_b": (house_b, 1),
    "warehouse": (warehouse, 1),
    "pier_4": (lambda: pier(4), 1),
    "pier_y_6": (lambda: pier(6).rotz(1), 1),
    "lamp_post": (lamp_post, 1),
    "signpost": (signpost, 1),
}
