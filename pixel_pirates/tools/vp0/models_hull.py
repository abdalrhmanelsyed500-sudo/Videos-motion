"""VP-0: the sloop as ONE metre-authored voxel model, baked at any density (8 px/m open sea, 12 px/m close-up, 24 px/m deck tier).

Dimensions are the real ones from ship_layout.gd (22 m long, 6.2 m beam on deck, mast at u = 1.0). Bow is +x, starboard is -y... (a ship
seen from above with the bow to the right has its starboard side toward the viewer, i.e. toward -y in model space).
The same module is the source for the sea sprite (16 headings), the future 24 px/m hull and the deck-tier collision-matched silhouette.
"""
from __future__ import annotations

import numpy as np

from voxel import Vox, hash3, tone_noise

(HULL, DECKM, TARM, CLOTH, ROPEM, IRONM, BRASSM, REDM, PALEM, GLASSM, DARKM, FLAGM) = range(1, 13)

HULL_HALF = [(-11.0, 1.9), (-10.0, 2.6), (-8.0, 3.0), (-3.0, 3.1), (2.0, 3.05), (5.0, 2.7), (7.5, 1.9), (9.5, 0.9), (11.0, 0.15)]


def half_w(u):
    us = [p[0] for p in HULL_HALF]
    ws = [p[1] for p in HULL_HALF]
    return np.interp(u, us, ws)


def sloop(ppm: float = 8.0, sail_trim_deg: float = 22.0, sails=True) -> Vox:
    m = ppm
    L = int(24 * m)
    Wd = int(10 * m)
    H = int(15.5 * m)
    v = Vox(L, Wd, H)
    v.define(HULL, "hull_oak", 2)
    v.define(DECKM, "wood_pale", 2)
    v.define(TARM, "tar", 1)
    v.define(CLOTH, "cloth_cream", 3)
    v.define(ROPEM, "rope_hemp", 2)
    v.define(IRONM, "iron", 2)
    v.define(BRASSM, "brass", 2)
    v.define(REDM, "cloth_red", 2)
    v.define(PALEM, "wood", 3)
    v.define(GLASSM, "fire", 3, emissive=True)
    v.define(DARKM, "wood", 1)
    v.define(FLAGM, "cloth_red", 3)
    cx = 12.0 * m                                                   # u = 0 at x = 12 m
    cy = Wd / 2.0

    def U(x):
        return (x / m) - 12.0                                     # voxel x -> ship u in metres

    wl = 0.6 * m                                                    # waterline: the sprite starts a little under the sheer
    deck_h = lambda u: (1.25 + 0.35 * np.clip((u - 5.0) / 6.0, 0, 1) ** 2 + 0.28 * np.clip((-u - 7.0) / 4.0, 0, 1)) * m  # noqa: E731
    stk = max(int(round(0.34 * m)), 1)

    def hull_fn(x, y, z):
        u = U(x)
        w = half_w(np.clip(u, -11.0, 11.0)) * m
        zd = deck_h(u)
        k = np.clip(z / np.maximum(zd, 1), 0, 1)
        wz = w * (0.66 + 0.34 * k ** 0.8)
        inside_u = (u >= -11.0) & (u <= 11.0)
        return inside_u & (np.abs(y - cy) <= wz) & (z <= zd)

    v.where(hull_fn, HULL, tone=lambda x, y, z: np.where(np.floor(z / stk) % 2 == 0, 0, -1) + np.where(hash3(x, y, z, 4) < 0.1, -1, 0), lo=(0, 0, 0), hi=(L, Wd, H))
    # tar band at the waterline
    v.where(lambda x, y, z: hull_fn(x, y, z) & (z < wl * 0.5), TARM, lo=(0, 0, 0), hi=(L, Wd, int(wl)))
    # deck: planks along the ship, the cabin and bulwarks added on top
    zd_c = lambda u: deck_h(u)  # noqa: E731

    def deck_fn(x, y, z):
        u = U(x)
        w = half_w(np.clip(u, -11.0, 11.0)) * m
        zd = zd_c(u)
        return (u >= -11.0) & (u <= 11.0) & (np.abs(y - cy) <= w - 0.12 * m) & (z <= zd) & (z > zd - 1.0)

    v.where(deck_fn, DECKM, tone=lambda x, y, z: np.where(np.floor((y - cy) / max(m * 0.22, 1.0)) % 2 == 0, 0, -1) + np.where(hash3(x, y, 0, 3) < 0.08, 1, 0), lo=(0, 0, 0), hi=(L, Wd, H))

    def rail_fn(x, y, z):
        u = U(x)
        w = half_w(np.clip(u, -11.0, 11.0)) * m
        zd = zd_c(u)
        t = max(0.14 * m, 1.0)
        return (u >= -11.0) & (u <= 11.0) & (np.abs(y - cy) <= w) & (np.abs(y - cy) >= w - t) & (z > zd - 1) & (z <= zd + 0.85 * m)

    v.where(rail_fn, HULL, tone=lambda x, y, z: np.where(np.floor(z / stk) % 2 == 0, 0, -1), lo=(0, 0, 0), hi=(L, Wd, H))
    # capping rail (pale) on top of the bulwark
    v.where(lambda x, y, z: rail_fn(x, y, z - 0.85 * m) & (z > 0.8 * m), PALEM, lo=(0, 0, 0), hi=(L, Wd, H))
    # bow stem and bowsprit
    v.tube((cx + 10.6 * m, cy, 1.5 * m), (cx + 12.6 * m, cy, 2.6 * m), max(0.22 * m, 0.8), HULL)
    v.tube((cx + 9.8 * m, cy, 2.1 * m), (cx + 13.6 * m, cy, 3.5 * m), max(0.16 * m, 0.7), PALEM)
    # captain's cabin: stern deckhouse, u -10 .. -5.4
    c0, c1 = cx + (-10.0) * m, cx + (-5.4) * m
    ch = (2.0 + 0.3) * m
    v.box(c0, cy - 2.2 * m, 1.25 * m, c1, cy + 2.2 * m, ch + 0.3 * m, DARKM, tone=lambda x, y, z: np.where(np.floor(x / stk) % 2 == 0, 0, -1))
    v.box(c0 - 0.2 * m, cy - 2.4 * m, ch + 0.3 * m, c1 + 0.2 * m, cy + 2.4 * m, ch + 0.5 * m, PALEM)             # roof
    for wy in (-1.4, 0.0, 1.4):                                                                                    # windows
        v.box(c0 - 0.05 * m, cy + wy * m - 0.4 * m, 1.7 * m, c0 + 0.1 * m, cy + wy * m + 0.4 * m, 2.2 * m, GLASSM)
    # helm
    v.cyl(cx - 3.6 * m, cy, 1.25 * m, 2.1 * m, max(0.3 * m, 1.0), DARKM)
    v.cyl(cx - 3.6 * m, cy, 2.0 * m, 2.1 * m, max(0.6 * m, 1.5), BRASSM)
    # hatch + winch + barrels (simple blocks at this density)
    v.box(cx - 2.3 * m, cy - 0.6 * m, 1.25 * m, cx - 0.9 * m, cy + 0.6 * m, 1.6 * m, DARKM)
    v.box(cx + 2.2 * m, cy + 1.7 * m, 1.25 * m, cx + 4.2 * m, cy + 2.8 * m, 2.6 * m, PALEM)                       # winch block (starboard? port side for fishing)
    for (bx, by) in ((5.2, -1.75), (6.1, -1.45), (5.2, -0.85), (6.1, -0.6)):
        v.cyl(cx + bx * m, cy - by * m, 1.25 * m, 2.2 * m, max(0.42 * m, 1.2), DARKM, tone=tone_noise(5, 0.1))
    # mast and boom
    mast_r = max(0.42 * m, 1.3)
    v.tube((cx + 1.0 * m, cy, 1.2 * m), (cx + 1.0 * m, cy, 13.4 * m), mast_r, PALEM, r1=max(mast_r * 0.6, 0.8),
           tone=lambda x, y, z: np.where(np.floor(np.arctan2(y - cy, x - (cx + 1.0 * m)) * 3) % 2 == 0, 0, -1))
    v.ell(cx + 1.0 * m, cy, 13.6 * m, max(0.4 * m, 1.2), max(0.4 * m, 1.2), max(0.35 * m, 1.0), BRASSM)
    th = np.radians(sail_trim_deg)
    bl = 6.6 * m
    bx1, by1 = cx + 1.0 * m - bl * np.cos(th), cy + bl * np.sin(th)
    v.tube((cx + 1.0 * m, cy, 3.6 * m), (bx1, by1, 3.6 * m), max(0.18 * m, 0.7), PALEM)
    if sails:
        # main sail: a billowed sheet between mast, boom and gaff (head at 11.4 m)
        nS, nT = int(bl * 4), int(8.6 * m * 4)
        for i in range(nS + 1):
            s = i / nS
            px = cx + 1.0 * m - s * bl * np.cos(th)
            py0 = cy + s * bl * np.sin(th)
            top = (11.6 - 2.2 * s) * m
            for j in range(nT + 1):
                t = j / nT
                zz = 3.7 * m + t * (top - 3.7 * m)
                bil = np.sin(np.pi * s) * np.sin(np.pi * (0.15 + 0.7 * t)) * 0.9 * m
                xi, yi, zi = int(px), int(py0 + bil), int(zz)
                if 0 <= xi < L and 0 <= yi < Wd and 0 <= zi < H:
                    v.mat[xi, yi, zi] = CLOTH
                    v.tone[xi, yi, zi] = -1 if i % max(nS // 6, 1) == 0 else 0
        # jib: triangle head -> bowsprit tip -> bow deck
        head = np.array([cx + 1.2 * m, cy, 12.8 * m])
        tip = np.array([cx + 13.3 * m, cy, 3.5 * m])
        tack = np.array([cx + 9.6 * m, cy, 2.0 * m])
        n = int(18 * m)
        for i in range(n + 1):
            for j in range(n + 1 - i):
                a, b = i / n, j / n
                p = head * (1 - a - b) + tip * a + tack * b
                bil = np.sin(np.pi * a) * 0.5 * m * (1 - b)
                xi, yi, zi = int(p[0]), int(p[1] - 0.6 * m + (bil * -1)), int(p[2])
                if 0 <= xi < L and 0 <= yi < Wd and 0 <= zi < H:
                    v.mat[xi, yi, zi] = CLOTH
                    v.tone[xi, yi, zi] = 0 if (i + j) % 9 else -1
        # a red pennant at the masthead
        v.box(cx + 1.0 * m - 2.0 * m, cy - 0.1 * m, 13.7 * m, cx + 1.0 * m, cy + 0.2 * m, 14.4 * m, FLAGM)
    # rigging: shrouds from the masthead to the rail, forestay, backstay
    r = max(0.28, 0.4)
    for (u_, sgn) in ((0.2, 1), (1.0, 1), (1.8, 1), (0.2, -1), (1.0, -1), (1.8, -1)):
        w = float(half_w(u_)) * m
        v.tube((cx + 1.0 * m, cy, 11.5 * m), (cx + u_ * m, cy + sgn * w, 2.1 * m), r, TARM)
    v.tube((cx + 1.0 * m, cy, 12.8 * m), (cx + 12.6 * m, cy, 3.0 * m), r, TARM)
    v.tube((cx + 1.0 * m, cy, 12.8 * m), (cx - 10.5 * m, cy, 2.2 * m), r, TARM)
    # a rudder / stern post and a stern lantern
    v.box(cx - 11.2 * m, cy - 0.15 * m, 0.6 * m, cx - 10.6 * m, cy + 0.15 * m, 2.4 * m, DARKM)
    v.ell(cx - 11.0 * m, cy, 3.4 * m, max(0.25 * m, 0.9), max(0.25 * m, 0.9), max(0.35 * m, 1.1), GLASSM)
    return v
