"""H2D-1.2 terrain of Anvil Cay (3-5 km across) as numpy fields at 2 m per cell. Deterministic (fixed seeds).

World frame (scene metres, the SAME frame the ship sails in): x east, z south, the harbour berth at (21.4, 21). The harbour
district keeps the exact geometry of H2D-1 (pier, berth, cove, dock zone) so the docking logic and its tuning are untouched.
Everything else grows around it: a big irregular island shaped like an anvil (the name): a wide face to the north with a horn
pointing east, a narrower waist, and a broad base in the south where the harbour is.

Used by bake_cay.py (writes the PNGs and the JSON), check_cay.py and check_land.py (read the PNGs back).
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage

CELL = 2.0
N = 2200
X0, Z0 = -2100.0, -3900.0          # world position of the grid's north-west corner (metres)
H_TOP = 100.0                      # highest encodable land height
PLAZA_H = 1.95
PIER_H = 1.0
PIER = dict(x0=14.5, x1=17.5, z0=2.0, z1=36.0)
HEAD = dict(x0=11.0, z0=32.0)

XS = (X0 + (np.arange(N) + 0.5) * CELL).astype(np.float32)
ZS = (Z0 + (np.arange(N) + 0.5) * CELL).astype(np.float32)
X = XS[None, :]
Z = ZS[:, None]

# class ids (biome map red channel = id * 16)
SAND, DUNE, MEADOW, FOREST, ROCK, CLIFF, PATH, COBBLE, EARTH, MARSH, HEATH = range(1, 12)
CLASS_NAMES = {1: "sand", 2: "dune scrub", 3: "meadow", 4: "forest floor", 5: "rock", 6: "cliff", 7: "path", 8: "cobbles",
               9: "village earth", 10: "marsh", 11: "heath"}


def soft(a, lo, hi):
    t = np.clip((a - lo) / (hi - lo), 0.0, 1.0)
    return (t * t * (3.0 - 2.0 * t)).astype(np.float32)


def fbm(rs: np.random.RandomState, scale_m: float, octaves: int = 3) -> np.ndarray:
    """Smooth noise of unit variance, features about scale_m wide. Coarse random grid + cubic zoom: fast at any scale."""
    out = np.zeros((N, N), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(scale_m / (2 ** o), 2.0 * CELL)
        g = int(math.ceil(N * CELL / s)) + 4
        base = rs.randn(g, g)
        base = ndimage.gaussian_filter(base, 0.9, mode="wrap")
        z = ndimage.zoom(base, N / g, order=3, mode="grid-wrap", grid_mode=True)[:N, :N]
        z = z / (z.std() + 1e-9)
        out += amp * z.astype(np.float32)
        tot += amp
        amp *= 0.5
    return out / tot


def ellipse(cx, cz, rx, rz, rot=0.0, xx=None, zz=None):
    x = (X if xx is None else xx) - cx
    z = (Z if zz is None else zz) - cz
    c, s = math.cos(rot), math.sin(rot)
    return np.sqrt(((x * c + z * s) / rx) ** 2 + ((-x * s + z * c) / rz) ** 2).astype(np.float32)


def box(x0, z0, x1, z1):
    return (X >= x0) & (X < x1) & (Z >= z0) & (Z < z1)


def circle_d(cx, cz):
    return np.sqrt((X - cx) ** 2 + (Z - cz) ** 2).astype(np.float32)


# ---- the design ---------------------------------------------------------------------------------------------------
# (name, x, z, radius m): bays carved out of the coast; each gets a wide beach (rocky coasts get none)
BAYS = [
    ("Pearl Cove", 548.0, -290.0, 90.0),
    ("Wreck Bay", -497.0, -300.0, 85.0),
    ("Gull Beach", -1230.0, -900.0, 170.0),
    ("Smuggler's Inlet", -250.0, -3500.0, 150.0),
    ("Cold Cove", 1180.0, -1000.0, 190.0),
    ("Reef Bay", -820.0, -2600.0, 220.0),
]
HARBOR_BODY = [(-4, -8, 66, 30, -0.12), (54, -4, 27, 19, 0.30), (-54, -14, 27, 25, 0.0), (-20, 20, 24, 15, 0.20),
               (48, 22, 20, 13, -0.25)]   # the five ellipses of the H2D-1 island: the south coast around the cove
BODY = [  # the anvil: face (north), horn (east), waist, base, bridge to the harbour point
    (-150, -3050, 1250, 480, 0.04), (1180, -3130, 520, 190, -0.15), (1620, -3220, 260, 80, -0.2),
    (-120, -1950, 520, 780, 0.08), (-250, -950, 880, 430, -0.05), (560, -760, 470, 360, 0.2),
    (60, -300, 520, 330, 0.0), (-720, -1500, 380, 300, 0.3),
]
HILLS = [  # name, x, z, sigma m, height m (added to the base)
    ("Mount Anvil", -330.0, -3000.0, 330.0, 66.0), ("Beacon Hill", -420.0, -1500.0, 150.0, 34.0),
    ("Lookout Hill", 150.0, -575.0, 80.0, 30.0), ("Horn Ridge", 1100.0, -3100.0, 260.0, 30.0),
    ("Saddle Ridge", -120.0, -2150.0, 200.0, 30.0), ("East Knoll", 640.0, -780.0, 120.0, 22.0),
    ("West Down", -900.0, -1300.0, 170.0, 20.0), ("Face Ridge", 500.0, -3200.0, 240.0, 26.0),
    ("Harbor Brow", -60.0, -120.0, 55.0, 7.0),
]
ROCKS = [  # offshore stacks and the two breakwaters at the cove mouth: x, z, radius m, height m (the H2D-1 set)
    (-3.0, 46.0, 3.2, 1.9), (-8.0, 37.0, 2.4, 1.3), (-12.0, 52.0, 2.0, 1.1),
    (37.0, 44.0, 3.4, 1.7), (42.0, 36.0, 2.4, 1.2), (47.0, 49.0, 2.0, 1.0),
    (-34.0, 56.0, 3.0, 1.6), (66.0, 38.0, 2.8, 1.3), (-78.0, 30.0, 3.6, 2.1), (86.0, 12.0, 4.0, 2.3),
]
VILLAGE = (-34.0, -128.0, 62.0, 6.0)     # x0, z0, x1, z1 of the trodden earth around the harbour
PLAZA = (-2.0, -4.2, 34.0, 3.4)
STREET = (14.2, -16.0, 17.8, 4.0)
# footpaths (world metres), painted 3.2 m wide: the village street, the forest road to the lookout, the shore track to
# Pearl Cove, the track west to Wreck Bay
PATHS = {
    "street": [(16, 4), (16, -16), (16, -60), (20, -112)],
    "lookout_road": [(20, -112), (44, -190), (92, -300), (128, -420), (146, -520), (150, -575)],
    "pearl_track": [(30, -118), (96, -150), (190, -190), (290, -222), (350, -232)],
    "wreck_track": [(2, -112), (-90, -150), (-190, -200), (-262, -226)],
}
EXPLORE = dict(x=60.0, z=-270.0, r=560.0)    # the on-foot area of this prototype (the rest of the island is not opened yet)


def enc_h(h: np.ndarray) -> np.ndarray:
    """Height (m) -> byte. Below 0 (sea floor, 8 m deep at most): 26 levels. Above 0: sqrt curve, so the beach is exact."""
    v = np.where(h < 0.0, (np.clip(h, -8.0, 0.0) + 8.0) / 8.0 * 0.1, 0.1 + 0.9 * np.sqrt(np.clip(h, 0.0, H_TOP) / H_TOP))
    return np.clip(v * 255.0 + 0.5, 0, 255).astype(np.uint8)


def dec_h(b: np.ndarray) -> np.ndarray:
    v = b.astype(np.float32) / 255.0
    return np.where(v < 0.1, v / 0.1 * 8.0 - 8.0, ((v - 0.1) / 0.9) ** 2 * H_TOP).astype(np.float32)


class Terrain:
    pass


def build() -> Terrain:
    rs = np.random.RandomState(20261019)
    T = Terrain()
    # --- coastline: ellipses with a domain warp that fades out near the harbour so its geometry stays exact
    dh = np.sqrt((X - 20.0) ** 2 + (Z + 10.0) ** 2)
    w = soft(dh, 160.0, 420.0)
    wx = (fbm(rs, 900.0, 3) * 150.0 + fbm(rs, 200.0, 2) * 34.0) * w
    wz = (fbm(rs, 900.0, 3) * 150.0 + fbm(rs, 200.0, 2) * 34.0) * w
    Xw, Zw = X + wx, Z + wz
    big = np.minimum.reduce([ellipse(*e, xx=Xw, zz=Zw) for e in BODY])
    big = big + 0.05 * fbm(rs, 110.0, 3) * w
    harb = np.minimum.reduce([ellipse(*e) for e in HARBOR_BODY])
    harb = harb + 0.13 * fbm(rs, 52.0, 3)
    inside = (big < 1.0) | (harb < 1.0)
    # bays
    T.bay_near = np.zeros((N, N), np.float32)
    bay_noise = fbm(rs, 70.0, 2)
    for _name, cx, cz, r in BAYS:
        d = circle_d(cx, cz) / r
        inside &= ~(d < 1.0 + 0.20 * bay_noise)
        T.bay_near = np.maximum(T.bay_near, np.exp(-(d / 2.0) ** 2))
    # the harbour cove (H2D-1 geometry)
    cove = ellipse(16, 30, 19, 26) + 0.05 * fbm(rs, 26.0, 3)
    inside &= ~(cove < 1.0)
    inside = ndimage.gaussian_filter(inside.astype(np.float32), 1.3) > 0.5
    lab, n = ndimage.label(inside)
    sizes = ndimage.sum(inside, lab, range(1, n + 1))
    inside = lab == (int(np.argmax(sizes)) + 1)
    T.mask = inside
    T.d_in = (ndimage.distance_transform_edt(inside) * CELL).astype(np.float32)
    T.d_out = (ndimage.distance_transform_edt(~inside) * CELL).astype(np.float32)
    # --- coast character: rocky stretches (cliffs, no beach) away from the harbour and the bays
    near_h = np.exp(-((X - 20.0) ** 2 + (Z - 20.0) ** 2) / (2.0 * 260.0 ** 2)).astype(np.float32)
    cliffk = soft(fbm(rs, 650.0, 2), 0.1, 0.9) * (1.0 - np.clip(T.bay_near * 1.4, 0, 1)) * (1.0 - np.clip(near_h * 2.0, 0, 1))
    T.cliffk = cliffk
    harbor_beach = np.exp(-(((X - 16.0) / 34.0) ** 2 + ((Z - 6.0) / 24.0) ** 2)).astype(np.float32)
    beach_w = (6.0 + 6.0 * harbor_beach + 16.0 * T.bay_near) * (1.0 - 0.85 * cliffk)
    T.beach_w = beach_w.astype(np.float32)
    # --- height
    inland = T.d_in / beach_w
    h = 0.12 + 1.8 * soft(inland, 0.0, 1.0) + 0.012 * np.clip(T.d_in - beach_w, 0.0, 400.0)
    h = np.minimum(h, 4.4 + 0.012 * np.clip(T.d_in - 420.0, 0.0, 600.0))
    low = 5.5 * fbm(rs, 420.0, 3) * soft(T.d_in, 30.0, 220.0) + 2.0 * fbm(rs, 70.0, 3) * soft(T.d_in, 10.0, 70.0)
    hills = np.zeros((N, N), np.float32)
    for _n, cx, cz, sg, ht in HILLS:
        r2 = ((X - cx) ** 2 + (Z - cz) ** 2) / (2.0 * sg * sg)
        hills += (ht * np.exp(-r2)).astype(np.float32)
    ridge = fbm(rs, 60.0, 3)
    hills *= (1.0 + 0.18 * ridge) * soft(T.d_in, 20.0, 160.0)
    cliff_add = cliffk * (14.0 + 6.0 * fbm(rs, 80.0, 2)) * soft(T.d_in, 2.0, 22.0)
    beach_profile = 0.12 + 1.8 * soft(inland, 0.0, 1.0)
    h = h + inside * (low + hills + cliff_add + 0.5 * ridge * soft(T.d_in, 2.0, 8.0))
    h = np.where(inside, np.maximum(h, beach_profile + 0.25 * soft(T.d_in, 10.0, 60.0)), h)   # no inland depressions at sea level
    # the harbour flat (H2D-1): plots, street and plaza sit level; the brow behind it rises gently
    flat = ndimage.gaussian_filter(box(-12.0, -20.0, 44.0, 3.2).astype(np.float32), 2.5)
    flat = np.clip(flat * 1.25, 0.0, 1.0) * inside * soft(T.d_in, 1.5, 6.5)
    h = h * (1.0 - flat) + PLAZA_H * flat
    h = np.where(inside, np.maximum(h, 0.15), h)
    # sea floor: a shelf that deepens with distance from the shore, gentler inside the cove and the bays
    cove_in = np.exp(-(((X - 18.0) / 26.0) ** 2 + ((Z - 30.0) / 30.0) ** 2)).astype(np.float32)
    shelf = np.clip(0.3 + (0.55 - 0.17 * np.maximum(cove_in, 0.8 * T.bay_near)) * T.d_out, 0.0, 8.0)
    shelf = shelf + 0.35 * np.clip(fbm(rs, 28.0, 2), -1, 1) * np.clip(T.d_out / 12.0, 0, 1)
    h = np.where(inside, h, -np.maximum(shelf, 0.25))
    # stacks and reefs: the H2D-1 stacks at the cove mouth plus random reef stacks off the rocky coasts
    T.stacks = [list(r) for r in ROCKS]
    near_coast = (T.d_out > 14.0) & (T.d_out < 80.0)
    excl = box(-30.0, 20.0, 80.0, 140.0)
    cand = np.argwhere(near_coast & ~excl & (cliffk > 0.35))
    pick = rs.choice(len(cand), size=min(70, len(cand)), replace=False)
    for iz, ix in cand[pick]:
        T.stacks.append([float(XS[ix]), float(ZS[iz]), float(rs.uniform(2.0, 4.6)), float(rs.uniform(1.0, 2.6))])
    warp_small = fbm(rs, 14.0, 2)
    T.rockmask = np.zeros((N, N), bool)
    for cx, cz, r, hh in T.stacks:
        x0, x1 = int((cx - r * 2 - X0) / CELL), int((cx + r * 2 - X0) / CELL) + 1
        z0, z1 = int((cz - r * 2 - Z0) / CELL), int((cz + r * 2 - Z0) / CELL) + 1
        x0, z0, x1, z1 = max(x0, 0), max(z0, 0), min(x1, N), min(z1, N)
        dd = np.sqrt((X[:, x0:x1] - cx) ** 2 + (Z[z0:z1, :] - cz) ** 2) / r + 0.25 * warp_small[z0:z1, x0:x1]
        blob = np.clip(1.0 - dd, 0.0, 1.0)
        sub = h[z0:z1, x0:x1]
        top = hh * np.minimum(blob * 2.2, 1.0) - 0.2 * (1 - np.minimum(blob * 2.2, 1.0)) + 0.1
        h[z0:z1, x0:x1] = np.where(blob > 0, np.maximum(sub, top), sub)
        T.rockmask[z0:z1, x0:x1] |= blob > 0.05
    h = ndimage.gaussian_filter(h, 0.6)
    T.h = np.clip(h, -8.0, H_TOP - 1.0).astype(np.float32)
    T.rs = rs
    return T


def pier_mask():
    return box(PIER["x0"], PIER["z0"], PIER["x1"], PIER["z1"]) | box(HEAD["x0"], HEAD["z0"], PIER["x1"], PIER["z1"])
