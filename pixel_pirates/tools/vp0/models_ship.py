"""VP-0 voxel models: ship deck equipment (24 px/m: 1 voxel = 1 art pixel = 1/24 m). Dimensions follow ship_layout.gd."""
from __future__ import annotations

import numpy as np

from voxel import Vox, tone_noise, tone_planks, hash3

# material ids shared by the ship set
WOOD, IRON, PALE, ROPE, BRASS, TAR, GLASS, CLOTH, FISH, WATER, GLOW, RED = range(1, 13)


def _new(X, Y, Z) -> Vox:
    v = Vox(X, Y, Z)
    v.define(WOOD, "wood", 2)
    v.define(IRON, "iron", 2)
    v.define(PALE, "wood_pale", 2)
    v.define(ROPE, "rope_hemp", 2)
    v.define(BRASS, "brass", 2)
    v.define(TAR, "tar", 0)
    v.define(GLASS, "fire", 3, emissive=True)
    v.define(CLOTH, "cloth_cream", 2)
    v.define(FISH, "iron", 3)
    v.define(WATER, "sea_deep", 1, flat=True)
    v.define(GLOW, "fire", 4, emissive=True)
    v.define(RED, "cloth_red", 2)
    return v


def _staves(cx, cy, n=8):
    def f(x, y, z):
        a = np.arctan2(y - cy, x - cx)
        return np.where(np.floor((a + np.pi) / (2 * np.pi) * n * 2) % 2 == 0, 0, -1) + np.where(hash3(x, y, z, 5) < 0.08, 1, 0)
    return f


def barrel(open_top=False, fish=0) -> Vox:
    v = _new(24, 24, 26)
    cx = cy = 12.0
    for z in range(24):
        r = 6.6 + 1.7 * np.sin(np.pi * (z + 1.5) / 27.0)
        v.cyl(cx, cy, z, z + 1, r, WOOD, tone=_staves(cx, cy, 9))
    for z0 in (3, 8, 15, 20):
        r = 6.6 + 1.7 * np.sin(np.pi * (z0 + 1.5) / 27.0) + 0.7
        v.cyl(cx, cy, z0, z0 + 1, r, IRON)
    v.cyl(cx, cy, 22, 24, 7.1, WOOD, tone=_staves(cx, cy, 9))         # chime (rim)
    v.cyl(cx, cy, 24, 25, 7.0, PALE)                                  # rim
    v.cyl(cx, cy, 24, 25, 5.7, PALE, tone=tone_noise(3, 0.25))        # lid
    if open_top:
        v.carve(lambda x, y, z: (np.hypot(x - cx, y - cy) < 6.0) & (z > 19.5) & (z < 26))
        v.cyl(cx, cy, 19, 22, 6.0, WATER)
        rng = np.random.default_rng(4)
        for i in range(max(fish, 1) * 3):
            a = rng.uniform(0, 6.28)
            rr = rng.uniform(0, 4.0)
            fx, fy = cx + rr * np.cos(a), cy + rr * np.sin(a)
            v.ell(fx, fy, 22.0 + (i % 3) * 0.7, 3.0, 1.7, 1.3, FISH, tone=lambda x, y, z: np.where(hash3(x, y, z, 2) < 0.2, 1, 0))
            v.box(int(fx + 2), int(fy), 22, int(fx + 4), int(fy) + 1, 24, FISH)
        v.where(lambda x, y, z: (np.hypot(x - cx, y - cy) > 6.0) & (np.hypot(x - cx, y - cy) <= 7.0) & (z >= 24) & (z < 25), PALE)
    return v


def crate(w=24, d=24, h=22) -> Vox:
    v = _new(w + 2, d + 2, h + 2)
    v.box(1, 1, 0, 1 + w, 1 + d, h, PALE, tone=tone_planks("z", 5, 4))
    for (x0, x1) in ((1, 4), (w - 2, w + 1)):                      # corner posts
        for (y0, y1) in ((1, 4), (d - 2, d + 1)):
            v.box(x0, y0, 0, x1, y1, h, WOOD, tone=tone_noise(7, 0.2))
    v.box(1, 1, h - 3, 1 + w, 1 + d, h, WOOD, tone=tone_noise(8, 0.15))                       # top frame
    v.box(1, 1, 0, 1 + w, 1 + d, 3, WOOD, tone=tone_noise(9, 0.15))
    v.box(3, 3, h - 3, w - 1, d - 1, h, PALE, tone=tone_planks("x", 6, 3))                    # lid inset
    # diagonal brace on the front face
    v.tube((3, 0.5, 4), (w - 3, 0.5, h - 4), 1.2, WOOD)
    v.box(w // 2 - 2, 0, h // 2 - 2, w // 2 + 3, 1, h // 2 + 3, IRON)                         # nail plate
    return v


def cannon() -> Vox:
    """Light 6-pounder on a truck carriage. Barrel points to +x. About 2.4 m x 1.1 m."""
    v = _new(66, 30, 34)
    cy = 15
    v.box(10, 8, 6, 46, 11, 16, WOOD, tone=tone_planks("z", 5, 2))                              # cheeks
    v.box(10, 19, 6, 46, 22, 16, WOOD, tone=tone_planks("z", 5, 2))
    for i, x in enumerate((14, 24, 34)):                                                          # steps / transoms
        v.box(x, 11, 6, x + 3, 19, 10 + (2 - i), WOOD)
    v.box(8, 11, 4, 20, 19, 8, WOOD)
    for cx in (16, 40):                                                                           # truck wheels (solid)
        for (ya, yb) in ((6, 9), (21, 24)):
            v.cyl(cx, ya, 5, yb, 5.0, WOOD, axis="y", tone=tone_noise(cx, 0.08))
            v.cyl(cx, ya, 5, yb, 1.4, IRON, axis="y")
    v.tube((16, 8, 5), (16, 22, 5), 1.6, IRON)
    v.tube((40, 8, 5), (40, 22, 5), 1.6, IRON)
    v.tube((12, cy, 19), (56, cy, 21), 5.0, IRON, r1=3.6)                                         # barrel
    v.tube((10, cy, 19), (13, cy, 19), 2.0, IRON)                                                 # breech
    v.ell(8, cy, 19, 2.6, 2.6, 2.6, IRON)                                                         # cascabel ball
    for x in (20, 36, 52):                                                                         # reinforcing rings
        v.tube((x, cy, 19.2 + (x - 12) * 2.0 / 44), (x + 1, cy, 19.2 + (x - 12) * 2.0 / 44), 5.4 - (x - 12) * 1.4 / 44, IRON)
    v.tube((55, cy, 20.8), (58, cy, 20.9), 3.9, IRON)                                              # muzzle swell
    v.carve(lambda x, y, z: (np.hypot(y - cy, z - 20.9) < 1.9) & (x > 57))
    v.box(24, 14, 22, 26, 17, 24, BRASS)                                                           # touch-hole pan
    v.tube((41, 6, 24), (41, 24, 24), 0.9, ROPE)                                                    # breeching rope
    v.tube((41, 24, 24), (46, 22, 14), 0.9, ROPE)
    v.tube((41, 6, 24), (46, 8, 14), 0.9, ROPE)
    v.cyl(30, 15, 12, 17, 2.2, WOOD)                                                                # elevating quoin
    return v


def rope_coil() -> Vox:
    v = _new(22, 22, 9)
    cx = cy = 11.0
    for i in range(5):
        R = 7.2 - i * 0.55
        zc = 1.6 + i * 1.3
        v.where(lambda x, y, z, R=R, zc=zc: (np.hypot(x - cx, y - cy) - R) ** 2 + (z - zc) ** 2 <= 1.9 ** 2, ROPE,
                tone=lambda x, y, z: np.where(np.floor((np.arctan2(y - cy, x - cx) + 3.15) * 3.0) % 2 == 0, 0, -1))
    v.where(lambda x, y, z: (np.hypot(x - cx, y - cy) < 2.2) & (z < 7), ROPE, tone=-1)
    v.tube((cx + 3, cy, 6), (cx + 10, cy + 3, 1), 1.1, ROPE)
    return v


def winch() -> Vox:
    """Fishing winch (ship_layout WINCH 1.9 m x 1.1 m footprint, 1.4 m high). Drum axis along x; crank on the right."""
    v = _new(50, 28, 38)
    v.box(2, 3, 0, 48, 25, 3, WOOD, tone=tone_planks("y", 5, 6))                                  # bed
    for x in (7, 37):                                                                              # A-frame cheeks
        v.box(x, 4, 3, x + 4, 7, 30, WOOD, tone=tone_planks("z", 4, 8))
        v.box(x, 21, 3, x + 4, 24, 30, WOOD, tone=tone_planks("z", 4, 8))
        v.box(x, 4, 18, x + 4, 24, 21, WOOD)
        v.box(x, 3, 29, x + 4, 25, 32, IRON)                                                      # bearing cap
    v.cyl(9, 14, 24, 40, 7.0, WOOD, axis="x", tone=lambda x, y, z: np.where(np.floor(x) % 4 == 0, -1, 0))   # drum
    v.cyl(9, 14, 24, 40, 7.4, ROPE, axis="x",
          tone=lambda x, y, z: np.where(np.floor(x * 0.6 + np.arctan2(z - 24, y - 14) * 0.3) % 2 == 0, 0, -1))
    v.cyl(9, 14, 24, 11, 9.4, WOOD, axis="x")                                                      # left flange
    v.cyl(37, 14, 24, 39, 9.4, WOOD, axis="x")                                                     # right flange
    v.cyl(41, 14, 24, 44, 8.0, IRON, axis="x")                                                     # ratchet wheel
    for a in np.linspace(0, 2 * np.pi, 9)[:-1]:
        v.tube((41, 14 + 8 * np.cos(a), 24 + 8 * np.sin(a)), (44, 14 + 9.4 * np.cos(a), 24 + 9.4 * np.sin(a)), 1.1, IRON)
    v.tube((44, 14, 24), (47, 14, 24), 1.5, IRON)
    v.tube((47, 14, 24), (47, 22, 31), 1.7, WOOD)                                                  # crank arm
    v.tube((47, 22, 31), (50, 22, 31), 2.1, PALE)                                                  # grip
    v.tube((41, 9, 31), (44, 9, 32), 2.0, IRON)                                                    # pawl
    v.tube((10, 14, 31), (2, 24, 3), 0.9, ROPE)                                                    # rope trailing to the deck
    v.tube((2, 24, 3), (5, 26, 2), 0.9, ROPE)
    return v


def helm() -> Vox:
    """Ship's wheel on its pedestal. The wheel faces +x/-x (looks along the ship's axis)."""
    v = _new(36, 36, 56)
    cx, cy = 18.0, 18.0
    v.box(11, 11, 0, 25, 25, 4, WOOD)
    v.box(13, 13, 4, 23, 23, 22, WOOD, tone=tone_planks("z", 4, 11))
    v.box(12, 12, 20, 24, 24, 24, WOOD)
    v.box(14, 14, 24, 22, 22, 26, BRASS)
    zc, R = 34.0, 13.0
    v.where(lambda x, y, z: ((np.hypot(y - cy, z - zc) - R) ** 2 + (x - cx) ** 2) <= 2.2 ** 2, WOOD,
            tone=lambda x, y, z: np.where(np.floor(np.arctan2(z - zc, y - cy) * 5) % 2 == 0, 0, -1), lo=(cx - 3, cy - R - 3, zc - R - 3), hi=(cx + 3, cy + R + 3, zc + R + 3))
    v.where(lambda x, y, z: ((np.hypot(y - cy, z - zc) - 9.0) ** 2 + (x - cx) ** 2) <= 1.0, BRASS, lo=(cx - 3, cy - 12, zc - 12), hi=(cx + 3, cy + 12, zc + 12))
    for a in np.linspace(0, 2 * np.pi, 9)[:-1]:
        c, s = np.cos(a), np.sin(a)
        v.tube((cx, cy + 3 * c, zc + 3 * s), (cx, cy + R * c, zc + R * s), 1.2, WOOD)
        v.tube((cx, cy + R * c, zc + R * s), (cx, cy + (R + 6) * c, zc + (R + 6) * s), 1.5, WOOD, r1=1.9)    # handles
        v.ell(cx, cy + (R + 6.5) * c, zc + (R + 6.5) * s, 2.0, 2.0, 2.0, BRASS)
    v.cyl(cx, cy, zc - 3, zc + 3, 3.4, BRASS, axis="z")
    v.tube((cx - 3, cy, zc), (cx + 3, cy, zc), 3.2, BRASS)
    return v


def lantern() -> Vox:
    v = _new(14, 14, 24)
    c = 7.0
    v.cyl(c, c, 0, 2, 4.5, IRON)
    v.cyl(c, c, 2, 14, 4.0, GLASS)
    v.carve(lambda x, y, z: (z > 2) & (z < 14) & ((np.abs(x - c) < 1.0) | (np.abs(y - c) < 1.0)) & (np.hypot(x - c, y - c) > 3.2))
    for a in (0.78, 2.35, 3.93, 5.5):
        v.tube((c + 4.0 * np.cos(a), c + 4.0 * np.sin(a), 2), (c + 4.0 * np.cos(a), c + 4.0 * np.sin(a), 14), 0.9, IRON)
    v.cyl(c, c, 14, 16, 5.0, IRON, r1=4.0)
    v.cyl(c, c, 16, 18, 3.0, IRON, r1=1.6)
    v.where(lambda x, y, z: (np.hypot(x - c, y - c) - 2.6) ** 2 + (z - 21) ** 2 <= 1.0, IRON)
    v.ell(c, c, 8, 1.8, 1.8, 3.0, GLOW)
    return v


def hatch() -> Vox:
    """Main hatch (HATCH_HALF 0.7 x 0.6 m -> 34 x 29 voxels), coaming 8 voxels high, open grating."""
    v = _new(36, 32, 12)
    v.box(1, 1, 0, 35, 30, 8, WOOD, tone=tone_planks("y", 4, 14))
    v.carve(lambda x, y, z: (x > 5) & (x < 31) & (y > 5) & (y < 26) & (z > 3))
    v.box(5, 5, 0, 31, 26, 3, TAR)
    for x in range(7, 30, 4):                                                                       # grating bars
        v.box(x, 5, 5, x + 2, 26, 7, PALE, tone=tone_noise(x, 0.2))
    for y in (11, 19):
        v.box(5, y, 4, 31, y + 2, 6, WOOD)
    v.box(0, 0, 7, 36, 2, 9, PALE)
    v.box(0, 29, 7, 36, 31, 9, PALE)
    v.box(0, 0, 7, 2, 31, 9, PALE)
    v.box(34, 0, 7, 36, 31, 9, PALE)
    v.box(16, 29, 8, 20, 30, 10, IRON)
    return v


def fishing_net() -> Vox:
    """A hauled net heaped on the deck: dark body, rope strands on the shell (the gaps read as mesh), cork floats."""
    v = _new(44, 32, 14)
    cx, cy = 22.0, 16.0
    v.ell(cx, cy, 3, 19, 13, 7, TAR)
    v.where(lambda x, y, z: (((x - cx) / 19.5) ** 2 + ((y - cy) / 13.5) ** 2 + ((z - 3) / 7.5) ** 2 <= 1.0) &
            (((x - cx) / 18.0) ** 2 + ((y - cy) / 12.0) ** 2 + ((z - 3) / 6.0) ** 2 >= 1.0) &
            ((((x + y) % 6) < 1.7) | (((x - y) % 6) < 1.7)), ROPE,
            tone=lambda x, y, z: np.where(hash3(x, y, z, 3) < 0.25, -1, np.where(hash3(x, y, z, 4) > 0.8, 1, 0)))
    v.carve(lambda x, y, z: z < 0.5)
    for (x, y) in ((8, 9), (31, 8), (24, 23), (14, 20), (35, 19), (19, 12)):
        v.ell(x, y, 8, 2.4, 1.7, 1.7, PALE)
    v.tube((4, 16, 2), (-1, 17, 0), 0.9, ROPE)
    return v


def chest() -> Vox:
    v = _new(32, 22, 22)
    v.box(2, 2, 0, 30, 20, 12, WOOD, tone=tone_planks("z", 4, 21))
    for z in range(12, 20):
        h = np.sqrt(max(0.0, 1 - ((z - 12) / 8.0) ** 2))
        inset = int(round(9 * (1 - h)))
        v.box(2, 2 + inset, z, 30, 20 - inset, z + 1, WOOD, tone=tone_planks("x", 4, 22))
    for x in (5, 25):
        v.box(x, 1, 0, x + 3, 21, 12, IRON)
        v.where(lambda xx, y, z, x=x: (xx >= x) & (xx < x + 3) & (z >= 12) & (z < 20) & (np.abs((y - 11) / 9.0) < np.sqrt(np.maximum(1 - ((z - 12) / 8.0) ** 2, 0)) + 0.02), IRON)
    v.box(13, 1, 8, 19, 2, 14, BRASS)
    v.box(15, 0, 9, 17, 1, 11, TAR)
    for x in (3, 29):
        for z in (2, 10):
            v.box(x, 1, z, x + 1, 2, z + 1, BRASS)
    return v


def bollard() -> Vox:
    v = _new(20, 20, 20)
    v.cyl(10, 10, 0, 12, 5.0, IRON, tone=tone_noise(2, 0.2))
    v.cyl(10, 10, 12, 15, 6.4, IRON, tone=tone_noise(3, 0.2))
    v.box(2, 6, 0, 18, 14, 2, WOOD)
    v.where(lambda x, y, z: (np.hypot(x - 10, y - 10) - 7.0) ** 2 + (z - 7) ** 2 <= 1.5 ** 2, ROPE,
            tone=lambda x, y, z: np.where(np.floor(np.arctan2(y - 10, x - 10) * 4) % 2 == 0, 0, -1))
    return v


def mast() -> Vox:
    """Mast with its crow's nest (11.25 m; rotation-symmetric so it is one billboard frame). The nest platform is 2.8 m square at 8.4 m above the
    deck (ship_layout NEST_HALF 1.4, NEST_Y - FLOOR_Y)."""
    H = 270
    C = 36
    v = _new(72, 72, H + 8)
    for z in range(H):
        r = 11.0 - 3.6 * (z / H)
        v.cyl(C, C, z, z + 1, r, WOOD, tone=lambda x, y, zz: np.where(np.floor(np.arctan2(y - C, x - C) * 4 + zz * 0.0) % 2 == 0, 0, -1) + np.where(hash3(x, 0, zz // 7, 4) < 0.1, 1, 0))
    for z0 in (6, 70, 140, 235):
        r = 11.0 - 3.6 * (z0 / H) + 0.9
        v.cyl(C, C, z0, z0 + 3, r, IRON)
    v.cyl(C, C, H, H + 3, 5.0, BRASS)
    v.cyl(C, C, 0, 8, 11.8, WOOD)
    # crow's nest
    z0 = 202
    v.box(2, 2, z0, 70, 70, z0 + 4, PALE, tone=tone_planks(3, 0.1) if False else tone_noise(2, 0.1))
    v.box(2, 2, z0 - 3, 70, 70, z0, WOOD)
    for (x0, y0, x1, y1) in ((2, 2, 70, 5), (2, 67, 70, 70), (2, 2, 5, 70), (67, 2, 70, 70)):
        v.box(x0, y0, z0 + 4, x1, y1, z0 + 15, WOOD, tone=tone_noise(5, 0.12))        # planked wall
        v.box(x0 - (1 if x0 < 3 else 0), y0 - (1 if y0 < 3 else 0), z0 + 15, x1 + (1 if x1 > 69 else 0), y1 + (1 if y1 > 69 else 0), z0 + 18, PALE)   # rail cap
    for (px, py) in ((2, 2), (67, 2), (2, 67), (67, 67), (34, 2), (34, 67), (2, 34), (67, 34)):
        v.box(px, py, z0 + 4, px + 3, py + 3, z0 + 26, WOOD)                             # posts
    for (x0, y0, x1, y1) in ((2, 2, 70, 4), (2, 68, 70, 70), (2, 2, 4, 70), (68, 2, 70, 70)):
        v.box(x0, y0, z0 + 24, x1, y1, z0 + 26, ROPE)                                    # top line
    return v


def pirate() -> Vox:
    """Scale-reference mannequin (1.8 m = 43 voxels). NOT the final character art: production characters are hand-painted frames at the
    same 24 px/m (see VP0_ART_BIBLE). Shares the voxel light so it sits in the scene while the prototype is judged."""
    v = _new(30, 20, 52)
    v.define(13, "skin_tan", 2)
    v.define(14, "cloth_blue", 2)
    v.define(15, "cloth_red", 2)
    c = 15
    for sx in (-1, 1):
        v.box(c + sx * 3 - 2, 7, 0, c + sx * 3 + 2, 12, 5, TAR)                         # boots
        v.box(c + sx * 3 - 2, 7, 5, c + sx * 3 + 2, 12, 19, 14, tone=tone_noise(3, 0.1))   # trousers
    v.box(c - 7, 6, 19, c + 7, 13, 32, 15, tone=tone_noise(2, 0.08))                    # red coat
    v.box(c - 7, 6, 18, c + 7, 13, 21, TAR)                                              # belt
    v.box(c - 1, 5, 20, c + 1, 6, 21, BRASS)
    v.box(c - 7, 6, 28, c + 7, 13, 32, 15)
    for sx in (-1, 1):
        v.box(c + sx * 8 - 2 + (1 if sx > 0 else 0), 7, 16, c + sx * 8 + 2 + (1 if sx > 0 else 0), 12, 31, 15)    # arms
        v.box(c + sx * 8 - 2 + (1 if sx > 0 else 0), 7, 14, c + sx * 8 + 2 + (1 if sx > 0 else 0), 12, 17, 13)     # hands
    v.ell(c, 9.5, 36, 5.2, 5, 5.5, 13)                                                    # head
    v.box(c - 1, 4, 34, c + 2, 6, 36, 13)                                                 # nose
    v.cyl(c, 9.5, 39, 41, 8.5, TAR)                                                       # hat brim
    v.cyl(c, 9.5, 41, 47, 5.6, TAR, r1=4.6)                                               # crown
    v.box(c - 8, 8, 40, c - 5, 11, 43, TAR)
    v.box(c + 5, 8, 40, c + 8, 11, 43, TAR)
    v.box(c - 6, 5, 31, c + 6, 7, 33, CLOTH)                                              # neckerchief
    v.box(c - 4, 5, 33, c, 6, 35, 13)
    return v


MODELS = {
    "pirate": (pirate, 8),
    "barrel": (lambda: barrel(False), 1),
    "barrel_fish": (lambda: barrel(True, 3), 1),
    "crate": (crate, 8),
    "cannon": (cannon, 8),
    "rope_coil": (rope_coil, 1),
    "winch": (winch, 8),
    "helm": (helm, 8),
    "lantern": (lantern, 1),
    "hatch": (hatch, 8),
    "fishing_net": (fishing_net, 8),
    "chest": (chest, 8),
    "bollard": (bollard, 1),
    "mast": (mast, 1),
}
