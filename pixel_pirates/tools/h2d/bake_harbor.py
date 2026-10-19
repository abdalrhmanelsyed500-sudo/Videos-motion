"""LEGACY (H2D-1, the 240 m harbour patch). Since H2D-1.2 this file is only a LIBRARY (palette helpers, structure and vegetation
artwork, STRUCTS) for bake_cay.py; running it as a script is refused because it would overwrite anvil_cay.json with the old
240 m island. Use tools/h2d/bake_cay.py.

Bakes Anvil Cay for H2D-1 (First Island and Harbor prototype): terrain, ground texture, height/shadow data, normal map,
vegetation atlas, structure atlas, and anvil_cay.json (trees, structures, lamps, pier, berth, dock zone).

  python tools/h2d/bake_harbor.py            # writes game/h2d/art/anvil_cay_*.png, anvil_veg_atlas.png, anvil_struct_atlas.png, anvil_cay.json
  python tools/h2d/bake_harbor.py --preview  # also art_bible/h2d1/*.png (a numpy composite: NOT a Godot render)
  python tools/h2d/check_harbor.py           # geometry checks on the baked files (berth, lane, pier, props, start)

The island is a 240 x 240 m patch at 3.6 px/m (864 x 864 px); heights run from -8 m (sea floor) to +40 m (encoded 0..255).
The game lights the ground per pixel from the height data and casts hill, tree and building shadows by ray-marching, so
the albedo is FLAT palette colour (no baked light). Deterministic (fixed seeds). Local coordinates: x east, z south, metres
from the island centre. The world places this island at the scene origin.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bake_island as BI  # noqa: E402  (H2D-0 sprites and palette helpers, reused so the vegetation matches)

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "game/h2d/art"
SIZE_M = 240.0
PPM = 3.6
PX = int(round(SIZE_M * PPM))
H_MIN, H_MAX = -8.0, 40.0
BAYER = BI.BAYER
ramp = BI.ramp

# ---- the layout (local metres) -------------------------------------------------------------------------------------
PIER_X0, PIER_X1 = 14.5, 17.5            # deck, 3 m wide, runs north-south
PIER_Z0, PIER_Z1 = 2.0, 36.0
HEAD_X0, HEAD_Z0 = 11.0, 32.0            # the pier head widens to the west only, so the berth lane to the east stays clear
PIER_H = 1.0
PLAZA_H = 1.95
BERTH = {"x": 21.4, "z": 21.0, "heading_deg": 0.0}   # ship centre, bow to the north, port side to the pier
APPROACH = {"x": 21.4, "z": 56.0}
ZONE = {"x0": 2.0, "z0": 42.0, "x1": 44.0, "z1": 100.0}   # open water: pressing the dock key works inside this rectangle
LANDING = {"x": 16.0, "z": 4.0}          # where the pier meets the beach
HARBOR_NAME = "Anvil Harbor"

Z_IDX, X_IDX = np.mgrid[0:PX, 0:PX]
X = (X_IDX + 0.5) / PPM - SIZE_M / 2     # metres east of the centre
Z = (Z_IDX + 0.5) / PPM - SIZE_M / 2     # metres south of the centre


def fbm(rs: np.random.RandomState, scale_px: float, octaves: int = 4) -> np.ndarray:
    out = np.zeros((PX, PX))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(1.0, scale_px / (2 ** o))
        n = ndimage.gaussian_filter(rs.randn(PX, PX), s, mode="wrap")
        n = n / (n.std() + 1e-9)
        out += amp * n
        tot += amp
        amp *= 0.5
    return out / tot


def ellipse(cx, cz, rx, rz, rot=0.0):
    x, z = X - cx, Z - cz
    c, s = math.cos(rot), math.sin(rot)
    return np.sqrt(((x * c + z * s) / rx) ** 2 + ((-x * s + z * c) / rz) ** 2)


def box_mask(x0, z0, x1, z1):
    return (X >= x0) & (X < x1) & (Z >= z0) & (Z < z1)


def soft(a, lo, hi):
    t = np.clip((a - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


# ---- terrain -------------------------------------------------------------------------------------------------------
def pier_mask() -> np.ndarray:
    return box_mask(PIER_X0, PIER_Z0, PIER_X1, PIER_Z1) | box_mask(HEAD_X0, HEAD_Z0, PIER_X1, PIER_Z1)


ROCKS = [  # offshore stacks and the two breakwaters at the cove mouth: x, z, radius m, height m
    (-3.0, 46.0, 3.2, 1.9), (-8.0, 37.0, 2.4, 1.3), (-12.0, 52.0, 2.0, 1.1),
    (37.0, 44.0, 3.4, 1.7), (42.0, 36.0, 2.4, 1.2), (47.0, 49.0, 2.0, 1.0),
    (-34.0, 56.0, 3.0, 1.6), (66.0, 38.0, 2.8, 1.3), (-78.0, 30.0, 3.6, 2.1), (86.0, 12.0, 4.0, 2.3),
    (-92.0, -26.0, 2.6, 1.4), (30.0, -62.0, 2.4, 1.2),
]
SHOALS = [(-22.0, 72.0, 9.0, -0.7), (54.0, 66.0, 7.0, -0.9), (-58.0, 48.0, 8.0, -0.8)]


def build_terrain():
    rs = np.random.RandomState(20261019)
    warp = fbm(rs, 26, 3)
    body = np.minimum.reduce([
        ellipse(-4, -8, 66, 30, -0.12), ellipse(54, -4, 27, 19, 0.30), ellipse(-54, -14, 27, 25, 0.0),
        ellipse(-20, 20, 24, 15, 0.20), ellipse(48, 22, 20, 13, -0.25),
    ])
    body = body + 0.13 * warp
    cove = ellipse(16, 30, 19, 26, 0.0) + 0.05 * warp
    lf = np.minimum(1.0 - body, cove - 1.0)
    lf = ndimage.gaussian_filter(lf, 1.6)
    mask = lf > 0.0
    # tiny specks are not islands
    lab, n = ndimage.label(mask)
    if n > 1:
        sizes = ndimage.sum(mask, lab, range(1, n + 1))
        keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 400])
        mask = keep
    d_in = ndimage.distance_transform_edt(mask) / PPM
    d_out = ndimage.distance_transform_edt(~mask) / PPM
    cove_k = np.exp(-(((X - 16) / 34.0) ** 2 + ((Z - 6) / 24.0) ** 2))
    beach_w = 7.0 + 6.0 * cove_k
    inland = d_in / beach_w
    h = 0.12 + 1.8 * soft(inland, 0.0, 1.0) + 0.07 * np.clip(d_in - beach_w, 0, 30)
    h = np.minimum(h, 4.2)
    # the hill (the Anvil), a knoll in the east, gentle swells in the jungle
    anvil = np.clip(1.0 - ellipse(-56, -16, 25, 21, 0.1), 0, 1)
    anvil = ndimage.gaussian_filter(np.where(anvil > 0, np.minimum(anvil * 2.4, 1.0), 0.0), 3.5)
    knoll = ndimage.gaussian_filter(np.clip(1.0 - ellipse(52, -6, 15, 11, 0.3), 0, 1), 3.0)
    ridge = fbm(rs, 9, 4)
    swell = fbm(rs, 30, 3)
    h = h + mask * (anvil * (26.0 + 4.0 * ridge) + knoll * (7.5 + 1.8 * ridge) + 0.9 * swell * soft(d_in, 6, 18)
                    + 0.5 * ridge * soft(d_in, 2, 8))
    # the harbour flat: building plots, street and plaza sit level
    flat = ndimage.gaussian_filter(box_mask(-12, -20, 44, 3.2).astype(float), 5.0)
    flat = np.clip(flat * 1.25, 0, 1) * mask * soft(d_in, 1.5, 6.5)
    h = h * (1 - flat) + PLAZA_H * flat
    h = np.where(mask, np.maximum(h, 0.15), h)
    # sea floor: a shelf that deepens with distance, gentler inside the cove
    cove_in = np.exp(-(((X - 18) / 26.0) ** 2 + ((Z - 30) / 30.0) ** 2))
    depth = np.clip(0.3 + (0.55 - 0.17 * cove_in) * d_out, 0.0, 8.0)
    depth = depth + 0.35 * np.clip(fbm(rs, 14, 2), -1, 1) * np.clip(d_out / 12.0, 0, 1)
    h = np.where(mask, h, -np.maximum(depth, 0.25))
    # rock stacks, shoals
    rock_mask = np.zeros((PX, PX), bool)
    for cx, cz, r, hh in ROCKS:
        dd = np.sqrt((X - cx) ** 2 + (Z - cz) ** 2) / r
        dd = dd + 0.25 * warp
        blob = np.clip(1.0 - dd, 0, 1)
        h = np.where(blob > 0, np.maximum(h, hh * np.minimum(blob * 2.2, 1.0) - 0.2 * (1 - np.minimum(blob * 2.2, 1.0)) + 0.1), h)
        rock_mask |= blob > 0.05
    for cx, cz, r, hh in SHOALS:
        dd = np.sqrt(((X - cx) / 1.5) ** 2 + (Z - cz) ** 2) / r + 0.45 * warp
        blob = np.clip(1.0 - dd, 0, 1)
        h = np.where((blob > 0) & (h < 0), np.maximum(h, hh - (1 - np.minimum(blob * 2.0, 1.0)) * 3.0), h)
    # the pier stands on piles over the water
    pm = pier_mask()
    h = np.where(pm, PIER_H, h)
    h = ndimage.gaussian_filter(h, 0.7)
    h = np.where(pm, np.maximum(h, PIER_H - 0.05), h)   # keep the deck crisp after the blur
    h = np.clip(h, H_MIN, H_MAX - 1.0)
    return h, mask, rock_mask, rs


def normals(h: np.ndarray) -> np.ndarray:
    m = 1.0 / PPM
    dz, dx = np.gradient(h, m)
    n = np.stack([-dx, np.ones_like(h), -dz], axis=-1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


# ---- keep-out areas for vegetation ---------------------------------------------------------------------------------
STREET = box_mask(14.2, -16.0, 17.8, 4.0)
PLAZA = box_mask(-2.0, -4.2, 34.0, 3.4)
HARBOR_CLEAR = box_mask(-30.0, -22.0, 48.0, 8.0)   # no jungle in the village (palms may line the beach edge)

# structures: name, atlas cell, x, z, scale, footprint (w m, d m, h m) for the shadow and the keep-out
STRUCTS = [
    ("warehouse", 1, -9.0, -6.0, 18.0, 8.0, 7.5),
    ("tavern", 2, 33.0, -6.5, 14.5, 7.0, 7.5),
    ("harbourmaster", 0, 16.0, -14.5, 10.5, 6.0, 6.0),
    ("fisher_hut", 3, -27.0, 3.0, 12.0, 6.0, 4.5),
    ("crates_a", 4, 23.0, 2.2, 3.8, 3.0, 2.4),
    ("crates_b", 4, 8.5, 2.6, 3.8, 3.0, 2.4),
    ("barrels_a", 5, 25.5, 1.4, 3.0, 2.0, 1.4),
    ("barrels_b", 5, 6.0, 1.0, 3.0, 2.0, 1.4),
    ("cannon", 10, 3.0, 3.0, 5.0, 2.0, 1.2),
    ("signal_mast", 11, 29.5, 1.5, 1.0, 1.0, 14.0),
    ("rowboat", 9, -2.0, 8.0, 9.0, 3.0, 1.0),
    ("pile_w1", 6, 14.8, 6.0, 1.2, 1.2, 3.2), ("pile_w2", 6, 14.8, 14.0, 1.2, 1.2, 3.2),
    ("pile_w3", 6, 14.8, 22.0, 1.2, 1.2, 3.2), ("pile_w4", 6, 14.8, 30.0, 1.2, 1.2, 3.2),
    ("pile_e1", 6, 17.2, 10.0, 1.2, 1.2, 3.2), ("pile_e2", 6, 17.2, 18.0, 1.2, 1.2, 3.2),
    ("pile_e3", 6, 17.2, 26.0, 1.2, 1.2, 3.2), ("pile_e4", 6, 17.2, 34.5, 1.2, 1.2, 3.2),
    ("bollard_1", 7, 17.0, 12.0, 1.0, 1.0, 1.0), ("bollard_2", 7, 17.0, 21.0, 1.0, 1.0, 1.0),
    ("bollard_3", 7, 17.0, 30.0, 1.0, 1.0, 1.0),
    ("lamp_head", 8, 12.2, 33.5, 1.0, 0.8, 4.4), ("lamp_pier", 8, 14.9, 11.0, 1.0, 0.8, 4.4),
    ("lamp_plaza_w", 8, 3.0, -2.5, 1.0, 0.8, 4.4), ("lamp_plaza_e", 8, 29.0, -2.0, 1.0, 0.8, 4.4),
    ("lamp_tavern", 8, 26.0, -3.0, 1.0, 0.8, 4.4), ("lamp_street", 8, 18.6, -9.0, 1.0, 0.8, 4.4),
    ("buoy_red", 12, 6.0, 58.0, 1.0, 1.0, 1.5), ("buoy_cream", 13, 36.0, 58.0, 1.0, 1.0, 1.5),
    ("buoy_red_in", 12, 5.5, 44.0, 1.0, 1.0, 1.5), ("buoy_cream_in", 13, 30.0, 48.0, 1.0, 1.0, 1.5),
]
LAMP_NAMES = ("lamp_head", "lamp_pier", "lamp_plaza_w", "lamp_plaza_e", "lamp_tavern", "lamp_street")


def struct_keepout() -> np.ndarray:
    m = np.zeros((PX, PX), bool)
    for name, _cell, x, z, w, d, _h in STRUCTS:
        if name.startswith(("pile", "bollard", "buoy", "lamp")):
            continue
        m |= box_mask(x - w / 2 - 2.5, z - d - 2.0, x + w / 2 + 2.5, z + 2.5)
    return m


# ---- ground texture ------------------------------------------------------------------------------------------------
def bake_ground(h, mask, rock_mask, n, rs):
    slope = np.sqrt(np.maximum(1.0 - n[..., 1] ** 2, 0)) / np.maximum(n[..., 1], 1e-3)
    detail = fbm(rs, 3.0, 2)
    patch = fbm(rs, 16.0, 3)
    bay = BAYER[Z_IDX % 4, X_IDX % 4]
    z = h + 0.5 * detail + 0.9 * patch
    layers = [(-99.0, ("sand", 1)), (0.55, ("sand", 2)), (1.25, ("sand", 3)), (2.35, ("grass", 2)), (3.5, ("grass", 1)),
              (6.5, ("foliage", 1)), (15.0, ("foliage", 0))]
    thr = np.array([t for t, _ in layers])
    idx = np.zeros((PX, PX), np.int32)
    for i in range(len(layers)):
        nxt = thr[i + 1] if i + 1 < len(layers) else 1e9
        band = nxt - thr[i] if nxt < 1e8 else 4.0
        up = (z >= nxt - 0.25 * band) & (z < nxt) & (bay < (z - (nxt - 0.25 * band)) / (0.25 * band))
        idx = np.where((z >= thr[i]) & (z < nxt), i, idx)
        idx = np.where(up, i + 1, idx)
    idx = np.where(z >= thr[-1], len(layers) - 1, idx)
    out = np.zeros((PX, PX, 3), np.uint8)
    for i, (_t, (name, st)) in enumerate(layers):
        out[idx == i] = ramp(name, st)
    # the village flat is trodden earth and grass, not jungle: a sandy-grass mix
    flat_zone = HARBOR_CLEAR & mask & (h > 1.4)
    tread = flat_zone & ((detail + 0.5 * patch) > -0.2)
    out[tread] = ramp("grass", 2)
    out[flat_zone & ~tread] = ramp("sand", 3)
    out[flat_zone & (bay < 0.35) & tread] = ramp("sand", 3)
    # cliffs and the Anvil's flanks: stone with a dithered skirt
    stone_score = slope + 0.12 * detail + np.clip(h - 16.0, 0, 20) * 0.03
    stone = ((stone_score > 0.95) | ((stone_score > 0.78) & (bay < 0.5))) & ~flat_zone
    smooth = ndimage.gaussian_filter(detail, 1.5) * 2.2
    shade_idx = np.clip(((smooth + 0.9 + 0.045 * (h - 14.0)) * 1.3).astype(int), 1, 3)
    for k in (1, 2, 3):
        out[stone & (shade_idx == k)] = ramp("stone_warm", k)
    out[stone & (detail < -1.9)] = ramp("stone_warm", 0)
    # reef stacks: stone, darker at the waterline
    rk = rock_mask & (h > 0.03)
    out[rk] = ramp("stone_warm", 2)
    out[rk & (bay < 0.45) & (h > 0.6)] = ramp("stone_warm", 3)
    out[rk & (h < 0.45)] = ramp("stone_warm", 1)
    # wet sand along the waterline, a dark seaweed line at the high-tide mark
    wet = (h < 0.45) & (h > 0.03) & ~rk
    out[wet] = ramp("sand", 0)
    wet2 = (h >= 0.45) & (h < 0.62) & ~rk & (bay < 0.5)
    out[wet2] = ramp("sand", 1)
    sp = rs.rand(PX, PX)
    weed = (h > 0.6) & (h < 0.95) & ~rk & (sp < 0.035) & mask
    out[weed] = ramp("foliage", 1)
    # sand ripples on the beach: short wind-aligned dashes
    rip = ndimage.gaussian_filter(rs.randn(PX, PX), (2.5, 0.8))
    sandz = (idx <= 2) & ~stone & ~wet & ~rk & mask & ~flat_zone
    out[sandz & (rip > 0.62)] = ramp("sand", 4)
    out[sandz & (rip < -0.66)] = ramp("sand", 1)
    grass_zone = (idx >= 3) & ~stone & ~flat_zone
    out[grass_zone & (sp > 0.985)] = ramp("grass", 4)
    out[grass_zone & (sp < 0.012)] = ramp("foliage", 0)
    out[sandz & (sp > 0.992)] = ramp("sand", 4)
    out[sandz & (sp < 0.006)] = ramp("sand", 0)
    # the street and plaza
    jit = 0.55 * detail
    st = (np.abs(X - 16.0 + jit) < 1.9) & (Z > -16.0) & (Z < 4.2) & mask
    out[st] = ramp("dirt", 2)
    out[st & (bay < 0.38)] = ramp("dirt", 3)
    out[st & (np.abs(X - 16.0 + jit) > 1.45)] = ramp("dirt", 1)
    plaza = (np.abs(X - 16.0) < 19.0 + jit) & (Z > -4.2 + jit) & (Z < 3.4 + jit) & mask
    cell = ((X_IDX // 4) + 31 * (Z_IDX // 4)) % 7
    cobble = np.where(cell < 2, 1, np.where(cell < 5, 2, 3))
    mortar = ((X_IDX % 4 == 0) | (Z_IDX % 4 == 0))
    for k in (1, 2, 3):
        out[plaza & (cobble == k) & ~mortar] = ramp("stone_warm", k)
    out[plaza & mortar] = ramp("stone_warm", 1)
    out[plaza & ~st & ((X_IDX + Z_IDX) % 11 == 0)] = ramp("sand", 3)
    # the pier deck: planks across the walkway, side beams, a darker underside
    pm = pier_mask()
    along = Z_IDX // 2
    pl_hash = ((along * 2654435761) >> 7) % 5
    deck = pm
    out[deck & (pl_hash <= 1)] = ramp("wood", 3)
    out[deck & (pl_hash == 2)] = ramp("wood", 2)
    out[deck & (pl_hash >= 3)] = ramp("wood", 3)
    out[deck & (Z_IDX % 2 == 1) & (pl_hash != 4)] = ramp("wood", 2)
    gap = deck & (Z_IDX % 6 == 0)
    out[gap] = ramp("wood", 1)
    edge_x = (np.abs(X - 16.0) > 1.1) | (X < PIER_X0 + 1.0)
    side = deck & ((X < PIER_X0 + 0.55) | (X > PIER_X1 - 0.55) | ((X < HEAD_X0 + 0.55) & (Z >= HEAD_Z0)) | ((Z > PIER_Z1 - 0.55)))
    out[side] = ramp("wood", 1)
    out[deck & (((X - PIER_X0) % 3.0 < 0.3) & (np.abs(X - 16.0) > 1.4)) & ~side & (Z_IDX % 2 == 0)] = ramp("wood", 4)
    del edge_x
    alpha = np.where(h > 0.02, 255, 0).astype(np.uint8)
    img = np.zeros((PX, PX, 4), np.uint8)
    img[..., :3] = out
    img[..., 3] = alpha
    return img


# ---- vegetation and structure placement ----------------------------------------------------------------------------
V_TYPES = ["palm_a", "palm_b", "jungle_a", "jungle_b", "bush", "rock_a", "rock_b", "palm_c", "fern", "grass", "flower_bush",
           "boulder", "reef_rock", "driftwood"]


def place_vegetation(h, mask, slope, rs, rock_mask):
    forest = fbm(rs, 14, 3)
    keep = struct_keepout() | STREET | PLAZA | pier_mask() | box_mask(10.0, 2.0, 25.0, 40.0) | ndimage.binary_dilation(rock_mask, iterations=3)
    clear = HARBOR_CLEAR
    trees: list[dict] = []
    taken: list[tuple[float, float, float]] = []

    def free(x, y, r):
        return all((x - a) ** 2 + (y - b) ** 2 >= (r + rr) ** 2 for a, b, rr in taken)

    def sample(count, tries, rad, cond, types, scale=(0.9, 1.15), allow_clear=False):
        got = 0
        for _ in range(tries):
            if got >= count:
                break
            px, py = rs.randint(4, PX - 4, 2)
            if keep[py, px] or (clear[py, px] and not allow_clear):
                continue
            hh, sl = h[py, px], slope[py, px]
            x, z = (px + 0.5) / PPM - SIZE_M / 2, (py + 0.5) / PPM - SIZE_M / 2
            if cond(hh, sl, forest[py, px]) and free(x, z, rad):
                taken.append((x, z, rad))
                trees.append({"x_m": round(float(x), 2), "z_m": round(float(z), 2), "y_m": round(float(hh), 2),
                              "type": int(rs.choice(types)), "scale": round(float(rs.uniform(*scale)), 2)})
                got += 1

    sample(135, 12000, 4.2, lambda hh, sl, f: 2.7 < hh < 20.0 and sl < 0.75 and f > -0.2, [2, 3], (0.85, 1.25))
    sample(70, 12000, 3.4, lambda hh, sl, f: 0.7 < hh < 3.2 and sl < 0.55, [0, 1, 7], (0.9, 1.2), allow_clear=False)
    # palms that frame the beach and the village edge (inside the clear area, outside the keep-out)
    sample(5, 6000, 5.0, lambda hh, sl, f: 0.8 < hh < 1.5 and sl < 0.5, [0, 1, 7], (0.95, 1.15), allow_clear=True)
    sample(75, 12000, 2.2, lambda hh, sl, f: 1.0 < hh < 22.0 and sl < 0.9, [4, 10], (0.9, 1.3))
    sample(70, 12000, 1.6, lambda hh, sl, f: 1.6 < hh < 12.0 and sl < 0.9, [8, 9], (0.9, 1.25))
    sample(10, 6000, 1.6, lambda hh, sl, f: 1.0 < hh < 1.6 and sl < 0.5, [8, 9, 10], (0.9, 1.1), allow_clear=True)
    sample(30, 12000, 3.0, lambda hh, sl, f: (hh > 14.0 and sl > 0.5) or (0.3 < hh < 1.2 and sl > 0.3), [5, 6, 11], (0.9, 1.4))
    sample(7, 4000, 1.5, lambda hh, sl, f: 0.5 < hh < 1.1 and sl < 0.5, [13], (0.9, 1.2), allow_clear=True)
    # the reef stacks get a boulder or reef rock on top
    for cx, cz, r, hh in ROCKS:
        trees.append({"x_m": round(cx, 2), "z_m": round(cz + 0.4, 2), "y_m": round(hh * 0.55, 2), "type": 12 if r < 3.0 else 11,
                      "scale": round(0.8 + 0.18 * r, 2)})
    return trees


def struct_list(h):
    out = []
    for name, cell, x, z, w, d, hh in STRUCTS:
        px = int((x + SIZE_M / 2) * PPM)
        py = int((z + SIZE_M / 2) * PPM)
        gy = float(h[min(max(py, 0), PX - 1), min(max(px, 0), PX - 1)])
        if name.startswith(("pile", "bollard", "lamp_head", "lamp_pier")) or (PIER_X0 - 0.2 <= x <= PIER_X1 + 0.2 and PIER_Z0 <= z <= PIER_Z1):
            gy = PIER_H
        if name.startswith("buoy"):
            gy = -0.1
        out.append({"name": name, "x_m": x, "z_m": z, "y_m": round(gy, 2), "type": cell, "scale": 1.0, "w_m": w, "d_m": d, "h_m": hh})
    return out


def data_image(h, trees, structs):
    occl = h.copy()
    for t in trees:
        ty = t["type"]
        if ty in (4, 10):
            top, rad = 2.0, 1.2
        elif ty in (8, 9, 13):
            top, rad = 0.8, 0.8
        elif ty in (5, 6, 11, 12):
            top, rad = 2.5, 1.6
        elif ty in (0, 1, 7):
            top, rad = 9.0 * t["scale"], 1.2
        else:
            top, rad = 11.0 * t["scale"], 3.0 * t["scale"]
        cx, cy = (t["x_m"] + SIZE_M / 2) * PPM, (t["z_m"] + SIZE_M / 2) * PPM
        r = int(rad * PPM) + 1
        y0, y1, x0, x1 = max(0, int(cy) - r), min(PX, int(cy) + r + 1), max(0, int(cx) - r), min(PX, int(cx) + r + 1)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        disc = (xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2 <= (rad * PPM) ** 2
        sub = occl[y0:y1, x0:x1]
        sub[disc] = np.maximum(sub[disc], t["y_m"] + top)
    for s in structs:
        if s["name"].startswith("buoy"):
            continue
        m = box_mask(s["x_m"] - s["w_m"] / 2, s["z_m"] - s["d_m"], s["x_m"] + s["w_m"] / 2, s["z_m"])
        occl = np.where(m, np.maximum(occl, s["y_m"] + s["h_m"]), occl)
    water_side = h <= 0.02
    dist = ndimage.distance_transform_edt(water_side) / PPM
    img = np.zeros((PX, PX, 4), np.uint8)
    img[..., 0] = np.clip((h - H_MIN) / (H_MAX - H_MIN) * 255.0 + 0.5, 0, 255)
    img[..., 1] = np.clip((occl - H_MIN) / (H_MAX - H_MIN) * 255.0 + 0.5, 0, 255)
    img[..., 2] = np.clip(dist / 40.0 * 255.0, 0, 255)
    img[..., 3] = 255
    return img


# ---- sprite helpers ------------------------------------------------------------------------------------------------
CELL_W, CELL_H, PIVOT = BI.CELL_W, BI.CELL_H, BI.PIVOT      # vegetation cells 48 x 56
SC_W, SC_H, SC_PIVOT = 80, 72, (40, 66)                       # structure cells
V_COLS, V_ROWS = 4, 4
S_COLS, S_ROWS = 4, 4


def col(name, i):
    return tuple(int(v) for v in ramp(name, i)) + (255,)


def new_img(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def hash2(a, b):
    return ((a * 73856093) ^ (b * 19349663)) % 1000 / 1000.0


def sprite_palm_c() -> np.ndarray:
    img = new_img(CELL_W, CELL_H)
    d = ImageDraw.Draw(img)
    pts = []
    for i in range(0, 31):
        t = i / 30.0
        pts.append((PIVOT[0] + (-1.2) * (t ** 1.5) * 3.2 + 1.6 * math.sin(t * 3.0) * t, PIVOT[1] - 36.0 * t))
    for i, (x, y) in enumerate(pts):
        wdt = 3 if i < 16 else 2
        d.rectangle([x - wdt / 2 - 0.5, y, x + wdt / 2 - 0.5, y + 1], fill=col("wood", 2))
        d.point((x - wdt / 2 - 0.5, y), fill=col("wood", 3))
        d.point((x + wdt / 2 - 0.5, y), fill=col("wood", 1))
        if i % 5 == 0 and i < 28:
            d.point((x + 0.5, y), fill=col("wood", 1))
    top = pts[-1]
    for f in range(9):
        ang = (f / 9.0) * 2 * math.pi + 0.5
        length = 14 + 2.0 * math.sin(f * 1.7)
        for s in range(0, 41):
            t = s / 40.0
            fx = top[0] + math.cos(ang) * length * t
            fy = top[1] - 3.0 + math.sin(ang) * length * t * 0.42 + 9.5 * t * t - 3.5 * math.sin(math.pi * t)
            lit = math.cos(ang) * -0.5 + math.sin(ang) * -0.7
            step = 3 if lit > 0.25 else (2 if lit > -0.35 else 1)
            if t < 0.35:
                step = min(4, step + 1)
            wdt = 3.4 * (1.0 - t) + 1.3
            d.ellipse([fx - wdt / 2, fy - wdt / 2 * 0.7, fx + wdt / 2, fy + wdt / 2 * 0.7], fill=col("palm_frond", step))
    for k in range(3):   # coconuts
        d.ellipse([top[0] - 3 + k * 3, top[1] + 1, top[0] - 1 + k * 3, top[1] + 4], fill=col("wood", 1 + (k % 2)))
    return _out(img, "palm_frond")


def _out(img, ramp_name):
    c = np.array(img)
    c[..., 3] = np.where(c[..., 3] > 127, 255, 0)
    BI._outline(c, ramp_name)
    return c


def sprite_fern() -> np.ndarray:
    img = new_img(CELL_W, CELL_H)
    d = ImageDraw.Draw(img)
    bx, by = 24, 50
    for b in range(11):
        ang = math.radians(-80 + b * 16)   # fan of blades
        length = 15 + 4 * math.sin(b * 1.9)
        for s in range(0, 31):
            t = s / 30.0
            x = bx + math.sin(ang) * length * t * 1.15
            y = by - math.cos(ang) * length * t * 0.9 + 6.0 * t * t * abs(math.sin(ang))
            step = 4 if (b % 3 == 0 and t > 0.4) else (3 if math.sin(ang) < 0.1 else 2)
            if t < 0.2:
                step = 1
            d.point((x, y), fill=col("palm_frond", step))
            d.point((x, y + 1), fill=col("palm_frond", max(1, step - 1)))
    return _out(img, "palm_frond")


def sprite_grass() -> np.ndarray:
    img = new_img(CELL_W, CELL_H)
    d = ImageDraw.Draw(img)
    for b in range(8):
        x0 = 15 + b * 2.4
        h = 11 + (b * 5) % 7
        lean = (b - 3.5) * 0.9
        for s in range(h):
            t = s / h
            c0 = col("grass", 4 if t > 0.55 else (3 if b % 2 else 2))
            d.point((x0 + lean * t, 50 - s), fill=c0)
            d.point((x0 + lean * t + 1, 50 - s), fill=col("grass", 2 if t < 0.55 else 3))
    return _out_grass(img)


def _out_grass(img):
    c = np.array(img)
    c[..., 3] = np.where(c[..., 3] > 127, 255, 0)
    BI._outline(c, "foliage")
    return c


def sprite_flower_bush() -> np.ndarray:
    c = BI.sprite_bush()
    rs = np.random.RandomState(404)
    leaf = c[..., 3] > 0
    ys, xs = np.nonzero(leaf)
    pick = rs.choice(len(xs), size=14, replace=False)
    for i, k in enumerate(pick):
        c[ys[k], xs[k]] = col("cloth_red", 3) if i % 3 else col("gold", 3)
    return c


def sprite_boulder() -> np.ndarray:
    img = new_img(CELL_W, CELL_H)
    d = ImageDraw.Draw(img)
    pts = [(6, 51), (8, 40), (15, 31), (26, 28), (35, 33), (42, 42), (41, 51)]
    d.polygon(pts, fill=col("stone_warm", 2))
    d.polygon([pts[1], pts[2], pts[3], (24, 38), (14, 45), (8, 48)], fill=col("stone_warm", 3))
    d.polygon([pts[3], pts[4], (32, 41), (26, 36)], fill=col("stone_warm", 4))
    d.polygon([pts[-2], pts[-1], (24, 51), (30, 44), pts[-3]], fill=col("stone_warm", 1))
    d.line([(15, 40), (20, 44), (21, 50)], fill=col("stone_warm", 1))
    d.line([(30, 36), (33, 44)], fill=col("stone_warm", 1))
    return _out(img, "stone_warm")


def sprite_reef_rock() -> np.ndarray:
    img = new_img(CELL_W, CELL_H)
    d = ImageDraw.Draw(img)
    pts = [(10, 51), (13, 43), (19, 38), (27, 40), (33, 46), (32, 51)]
    d.polygon(pts, fill=col("stone_warm", 1))
    d.polygon([pts[1], pts[2], pts[3], (24, 44), (16, 47)], fill=col("stone_warm", 2))
    d.line([pts[2], (23, 41)], fill=col("stone_warm", 3))
    d.polygon([(10, 51), (32, 51), (31, 49), (11, 49)], fill=col("stone_warm", 0))   # wet base
    return _out(img, "stone_warm")


def sprite_driftwood() -> np.ndarray:
    img = new_img(CELL_W, CELL_H)
    d = ImageDraw.Draw(img)
    d.polygon([(10, 49), (33, 46), (37, 48), (13, 52)], fill=col("wood", 3))
    d.line([(11, 49), (34, 46)], fill=col("wood", 4))
    d.line([(14, 52), (37, 48)], fill=col("wood", 2))
    d.line([(28, 46), (31, 42), (33, 41)], fill=col("wood", 3))
    return _out(img, "wood")


def build_veg_atlas() -> Image.Image:
    cells = [BI.sprite_palm(0), BI.sprite_palm(1), BI.sprite_jungle(0), BI.sprite_jungle(1), BI.sprite_bush(), BI.sprite_rock(0),
             BI.sprite_rock(1), sprite_palm_c(), sprite_fern(), sprite_grass(), sprite_flower_bush(), sprite_boulder(),
             sprite_reef_rock(), sprite_driftwood()]
    atlas = Image.new("RGBA", (CELL_W * V_COLS, CELL_H * V_ROWS), (0, 0, 0, 0))
    for i, cell in enumerate(cells):
        atlas.paste(Image.fromarray(cell, "RGBA"), ((i % V_COLS) * CELL_W, (i // V_COLS) * CELL_H))
    return atlas


# ---- structures ----------------------------------------------------------------------------------------------------
def draw_wall(c, x0, y0, x1, y1, seed, base=2):
    """Vertical planks: a seam every 4 px, a shade shift per plank, darker under the eave and at the ground."""
    for x in range(x0, x1):
        plank = (x - x0) // 4
        sh = base + (1 if hash2(plank, seed) > 0.62 else 0) - (1 if hash2(plank, seed + 9) < 0.22 else 0)
        for y in range(y0, y1):
            s = sh
            if (x - x0) % 4 == 0:
                s = max(1, base - 1)
            elif (x - x0) % 4 == 1 and x - x0 < 8:
                s = min(4, sh + 1)          # light catches the left edge of a plank
            if y < y0 + 3:
                s = 1
            elif y > y1 - 3:
                s = 1 if (x + y) % 2 == 0 else s
            if hash2(x * 7 + y, seed + 3) > 0.965:
                s = max(1, s - 1)
            c[y, x] = col("wood", int(np.clip(s, 1, 4)))


def draw_roof(c, x0, x1, y_eave, y_top, over, seed, ramp_name="roof_teal", steps=(1, 2, 3, 4)):
    """A front roof slope seen from the south camera: rows of shingles, lighter to the north-west."""
    h = y_eave - y_top
    for y in range(y_top, y_eave + 1):
        t = (y - y_top) / max(h, 1)
        inset = int(round((1.0 - t) * 4))
        xa, xb = x0 - over + inset, x1 + over - inset
        row = (y - y_top) // 3
        for x in range(xa, xb):
            u = (x - xa) / max(xb - xa, 1)
            base = steps[2] if u < 0.55 else steps[1]
            if hash2(x // 2 + row * 17, row) > 0.8:
                base = steps[2] if base == steps[1] else steps[1]
            if (y - y_top) % 3 == 2:
                base = steps[0] if (x + row) % 2 else steps[1]
            if (x + row * 3) % 6 == 0:
                base = steps[0]
            c[y, x] = col(ramp_name, base)
        if y == y_top:
            for x in range(xa, xb):
                c[y, x] = col(ramp_name, steps[3])
        if y == y_eave:
            for x in range(xa, xb):
                c[y, x] = col("wood", 1)


def draw_door(c, x, y_base, w=7, h=13, lit=False):
    for yy in range(y_base - h, y_base):
        for xx in range(x, x + w):
            edge = xx in (x, x + w - 1) or yy == y_base - h
            c[yy, xx] = col("wood", 3 if edge else (0 if (xx - x) % 3 else 1))
    c[y_base - h // 2, x + w - 2] = col("iron", 4)


def draw_window(c, x, y, w=8, h=7, shutters=True):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            frame = xx in (x, x + w - 1) or yy in (y, y + h - 1)
            mid = xx == x + w // 2 or yy == y + h // 2
            c[yy, xx] = col("wood", 4 if frame else 1) if (frame or mid) else col("fire", 3)    # fire[3] is the lit pixel
    if shutters:
        for yy in range(y, y + h):
            c[yy, x - 2] = col("wood", 2)
            c[yy, x - 1] = col("wood", 1)
            c[yy, x + w] = col("wood", 1)
            c[yy, x + w + 1] = col("wood", 2)


def building(w, hw, hr, over, seed, roof="roof_teal", roof_steps=(1, 2, 3, 4), doors=(), windows=(), extras=None):
    img = np.zeros((SC_H, SC_W, 4), np.uint8)
    px, by = SC_PIVOT
    x0 = px - w // 2
    x1 = x0 + w
    yw = by - hw
    draw_wall(img, x0, yw, x1, by, seed)
    draw_roof(img, x0, x1, yw + 1, yw - hr, over, seed, roof, roof_steps)
    for dx in doors:
        draw_door(img, x0 + dx, by)
    for dx, dy in windows:
        draw_window(img, x0 + dx, yw + dy)
    if extras:
        extras(img, x0, x1, yw, by)
    # stone footing
    for x in range(x0, x1):
        img[by - 1, x] = col("stone_warm", 2 if x % 3 else 1)
        img[by - 2, x] = col("stone_warm", 3 if (x + 1) % 4 == 0 else 2)
    img[..., 3] = np.where(img[..., 3] > 127, 255, 0)
    BI._outline(img, "wood")
    return img


def sprite_harbourmaster():
    def extras(c, x0, x1, yw, by):
        mx = (x0 + x1) // 2 + 14
        for y in range(yw - 24, yw - 4):          # flag pole on the roof
            c[y, mx] = col("wood", 3)
        for y in range(yw - 24, yw - 17):         # a red pennant
            for x in range(mx + 1, mx + 9 - (y - (yw - 24))):
                c[y, x] = col("cloth_red", 3 if (x + y) % 5 else 2)
        # chimney
        for y in range(yw - 22, yw - 6):
            for x in range(x0 + 4, x0 + 9):
                c[y, x] = col("stone_warm", 2 if x > x0 + 5 else 3)
    return building(40, 22, 14, 3, 11, "roof_teal", (1, 2, 3, 4), doors=(16,), windows=((5, 6), (28, 6)), extras=extras)


def sprite_warehouse():
    def extras(c, x0, x1, yw, by):
        for xx in range(x0 + 20, x0 + 44):        # big double doors with a cross brace
            for yy in range(by - 20, by - 1):
                edge = xx in (x0 + 20, x0 + 43, x0 + 31, x0 + 32) or yy == by - 20
                c[yy, xx] = col("wood", 3 if edge else (0 if (xx - x0) % 4 else 1))
        for k in range(24):
            yy = by - 3 - int(k * 0.7)
            if 0 <= yy < SC_H:
                c[yy, x0 + 20 + k] = col("wood", 4)
                c[yy, x0 + 43 - k] = col("wood", 4)
        c[by - 11, x0 + 29] = col("iron", 4)
        c[by - 11, x0 + 34] = col("iron", 4)
        for yy in range(yw - 8, yw - 3):          # a hoist beam over the doors
            c[yy, x0 + 32] = col("wood", 4)
        c[yw - 3, x0 + 32] = col("iron", 3)
    return building(64, 26, 18, 3, 23, "roof_teal", (1, 2, 3, 4), doors=(), windows=((6, 7), (52, 7)), extras=extras)


def sprite_tavern():
    def extras(c, x0, x1, yw, by):
        # upper floor band and a hanging anchor sign at the corner
        for x in range(x0, x1):
            c[yw + 12, x] = col("wood", 1)
            c[yw + 13, x] = col("wood", 4) if x % 2 else col("wood", 3)
        for yy in range(yw + 4, yw + 22):
            c[yy, x1 + 3] = col("iron", 3)
        for xx in range(x1 + 3, x1 + 12):
            c[yw + 4, xx] = col("iron", 3)
        for yy in range(yw + 6, yw + 16):
            for xx in range(x1 + 4, x1 + 12):
                c[yy, xx] = col("wood", 2 if xx > x1 + 4 else 3)
        anchor = ["...#...", ".#####.", "...#...", "...#...", "#..#..#", ".#.#.#.", "..###.."]
        for j, rowp in enumerate(anchor):
            for i, ch in enumerate(rowp):
                if ch == "#":
                    c[yw + 8 + j, x1 + 4 + i] = col("cloth_cream", 3)
        for xx in range(x0 + 20, x0 + 34):        # awning over the door
            for yy in range(by - 20, by - 17):
                c[yy, xx] = col("cloth_red", 3 if (xx // 3) % 2 else 2)
    return building(52, 34, 16, 3, 31, "cloth_red", (0, 1, 2, 3), doors=(22,), windows=((6, 3), (22, 3), (38, 3), (6, 19), (38, 19)), extras=extras)


def sprite_fisher_hut():
    def extras(c, x0, x1, yw, by):
        # net rack to the right: two poles, a drying net
        rx = x1 + 2
        for yy in range(by - 20, by):
            c[yy, rx] = col("wood", 3)
            c[yy, rx + 15] = col("wood", 3)
        for xx in range(rx, rx + 16):
            c[by - 20, xx] = col("wood", 4)
        for yy in range(by - 19, by - 6):
            for xx in range(rx + 1, rx + 15):
                if (xx + yy) % 3 == 0 or xx % 4 == 0 and yy % 2 == 0:
                    c[yy, xx] = col("cloth_cream", 3 if (xx + yy) % 2 else 2)
    return building(34, 18, 12, 3, 41, "dirt", (2, 3, 4, 4), doors=(13,), windows=((4, 5),), extras=extras)


def box_sprite(w, hfront, htop, seed, band=True):
    img = np.zeros((SC_H, SC_W, 4), np.uint8)
    px, by = SC_PIVOT
    x0 = px - w // 2
    for y in range(by - hfront, by):
        for x in range(x0, x0 + w):
            s = 2 if (x + y) % 7 else 1
            if x in (x0, x0 + w - 1) or y in (by - hfront, by - 1):
                s = 1
            if band and (x - x0 in (w // 3, 2 * w // 3)):
                s = 3
            img[y, x] = col("wood", s)
    for y in range(by - hfront - htop, by - hfront):
        t = (y - (by - hfront - htop)) / max(htop, 1)
        for x in range(x0 + int((1 - t) * 3), x0 + w + 3 - int((1 - t) * 0)):
            img[y, x] = col("wood", 4 if x < x0 + w // 2 else 3)
    return img


def sprite_crates():
    a = box_sprite(15, 11, 5, 1)
    b = box_sprite(13, 10, 5, 2)
    c = np.zeros_like(a)
    c[...] = a
    px, by = SC_PIVOT
    # a smaller crate stacked on the right, offset up
    shift = np.roll(np.roll(b, 10, axis=1), -11, axis=0)
    shift[-11:, :, 3] = 0
    m = shift[..., 3] > 0
    c[m] = shift[m]
    c[..., 3] = np.where(c[..., 3] > 127, 255, 0)
    BI._outline(c, "wood")
    return c


def sprite_barrels():
    img = np.zeros((SC_H, SC_W, 4), np.uint8)
    px, by = SC_PIVOT

    def barrel(cx, base, bw, bh):
        for y in range(base - bh, base):
            t = (y - (base - bh)) / bh
            half = bw / 2 * (0.82 + 0.28 * math.sin(math.pi * t))
            for x in range(int(cx - half), int(cx + half) + 1):
                u = (x - (cx - half)) / (2 * half)
                s = 4 if u < 0.2 else (3 if u < 0.5 else (2 if u < 0.8 else 1))
                if (x + y) % 5 == 0:
                    s = max(1, s - 1)
                img[y, x] = col("wood", s)
            if y in (base - bh + 3, base - 4):
                for x in range(int(cx - half), int(cx + half) + 1):
                    img[y, x] = col("iron", 3 if x % 3 else 2)
        for x in range(int(cx - bw / 2 + 1), int(cx + bw / 2)):
            img[base - bh, x] = col("wood", 4)

    barrel(px - 6, by, 11, 14)
    barrel(px + 6, by, 11, 14)
    barrel(px, by - 8, 11, 14)
    img[..., 3] = np.where(img[..., 3] > 127, 255, 0)
    BI._outline(img, "wood")
    return img


def sprite_pile():
    img = np.zeros((SC_H, SC_W, 4), np.uint8)
    px, by = SC_PIVOT
    for y in range(by - 14, by):
        for x in range(px - 2, px + 3):
            s = 3 if x == px - 2 else (2 if x < px + 2 else 1)
            if (y // 5) % 3 == 0 and x == px:
                s = 1
            img[y, x] = col("wood", s)
    for x in range(px - 2, px + 3):
        img[by - 14, x] = col("wood", 4)
    for y in range(by - 10, by - 8):                        # a turn of rope
        for x in range(px - 2, px + 3):
            img[y, x] = col("cloth_cream", 3 if (x + y) % 2 else 2)
    img[..., 3] = np.where(img[..., 3] > 127, 255, 0)
    BI._outline(img, "wood")
    return img


def sprite_bollard():
    img = np.zeros((SC_H, SC_W, 4), np.uint8)
    px, by = SC_PIVOT
    for y in range(by - 7, by):
        for x in range(px - 3, px + 4):
            img[y, x] = col("iron", 3 if x < px - 1 else (2 if x < px + 2 else 1))
    for x in range(px - 4, px + 5):
        img[by - 8, x] = col("iron", 4 if x < px + 1 else 3)
    img[..., 3] = np.where(img[..., 3] > 127, 255, 0)
    BI._outline(img, "wood")
    return img


def sprite_lantern():
    img = np.zeros((SC_H, SC_W, 4), np.uint8)
    px, by = SC_PIVOT
    for y in range(by - 30, by):
        for x in range(px - 1, px + 2):
            img[y, x] = col("wood", 3 if x == px - 1 else 2)
    for x in range(px, px + 8):                              # arm
        img[by - 30, x] = col("wood", 3)
        img[by - 29, x] = col("wood", 2)
    lx = px + 7
    for y in range(by - 27, by - 19):                        # the lantern: iron frame, a lit core
        for x in range(lx - 3, lx + 4):
            frame = x in (lx - 3, lx + 3) or y in (by - 27, by - 20)
            img[y, x] = col("iron", 3) if frame else col("fire", 4 if (x + y) % 2 else 3)
    img[by - 28, lx] = col("iron", 2)
    for x in range(lx - 2, lx + 3):
        img[by - 28, x] = col("iron", 2)
    img[..., 3] = np.where(img[..., 3] > 127, 255, 0)
    BI._outline(img, "wood")
    return img


def sprite_rowboat():
    img = new_img(SC_W, SC_H)
    d = ImageDraw.Draw(img)
    px, by = SC_PIVOT
    hull = [(px - 20, by - 12), (px + 20, by - 12), (px + 15, by - 2), (px - 14, by - 2)]
    d.polygon(hull, fill=col("wood", 3))
    d.polygon([(px - 20, by - 12), (px + 20, by - 12), (px + 19, by - 9), (px - 19, by - 9)], fill=col("wood", 4))   # gunwale
    for k in range(1, 4):
        d.line([(px - 18 + k * 2, by - 9 + k * 2), (px + 17 - k * 2, by - 9 + k * 2)], fill=col("wood", 2))
    d.polygon([(px - 14, by - 2), (px + 15, by - 2), (px + 14, by), (px - 12, by)], fill=col("wood", 1))
    d.line([(px - 8, by - 11), (px + 22, by - 20)], fill=col("wood", 4), width=1)       # an oar
    d.line([(px + 22, by - 20), (px + 25, by - 23)], fill=col("wood", 3), width=2)
    c = np.array(img)
    c[..., 3] = np.where(c[..., 3] > 127, 255, 0)
    BI._outline(c, "wood")
    return c


def sprite_cannon():
    img = new_img(SC_W, SC_H)
    d = ImageDraw.Draw(img)
    px, by = SC_PIVOT
    d.polygon([(px - 11, by - 6), (px + 11, by - 6), (px + 10, by - 2), (px - 10, by - 2)], fill=col("wood", 3))
    d.polygon([(px - 11, by - 6), (px + 11, by - 6), (px + 11, by - 5), (px - 11, by - 5)], fill=col("wood", 4))
    d.ellipse([px - 9, by - 5, px - 3, by + 1], fill=col("wood", 2))
    d.ellipse([px + 3, by - 5, px + 9, by + 1], fill=col("wood", 2))
    d.ellipse([px - 7, by - 3, px - 5, by - 1], fill=col("iron", 3))
    d.ellipse([px + 5, by - 3, px + 7, by - 1], fill=col("iron", 3))
    bar = [(px - 13, by - 14), (px + 12, by - 17), (px + 12, by - 9), (px - 13, by - 8)]
    d.polygon(bar, fill=col("iron", 2))
    d.polygon([(px - 13, by - 14), (px + 12, by - 17), (px + 12, by - 14), (px - 13, by - 11)], fill=col("iron", 3))
    d.line([(px - 12, by - 14), (px + 11, by - 17)], fill=col("iron", 4))
    d.ellipse([px + 10, by - 17, px + 14, by - 9], fill=col("iron", 1))
    c = np.array(img)
    c[..., 3] = np.where(c[..., 3] > 127, 255, 0)
    BI._outline(c, "wood")
    return c


def sprite_signal_mast():
    img = np.zeros((SC_H, SC_W, 4), np.uint8)
    px, by = SC_PIVOT
    for y in range(by - 56, by):
        for x in range(px - 1, px + 2):
            img[y, x] = col("wood", 3 if x == px - 1 else 2)
    for x in range(px - 9, px + 10):                         # yard arm
        img[by - 50, x] = col("wood", 3)
    for y in range(by - 49, by - 38):                        # signal flag, hoisted
        for x in range(px + 2, px + 16 - (y - (by - 49)) // 2):
            img[y, x] = col("cloth_red", 3 if (x // 3 + y // 3) % 2 else 2)
    for y in range(by - 38, by - 28):
        for x in range(px - 14, px - 2):
            img[y, x] = col("cloth_cream", 3 if (x // 3 + y // 3) % 2 else 2)
    for x in range(px - 4, px + 5):                          # base block
        for y in range(by - 4, by):
            img[y, x] = col("stone_warm", 2 if x > px - 2 else 3)
    img[..., 3] = np.where(img[..., 3] > 127, 255, 0)
    BI._outline(img, "wood")
    return img


def sprite_buoy(red: bool):
    img = new_img(SC_W, SC_H)
    d = ImageDraw.Draw(img)
    px, by = SC_PIVOT
    body = "cloth_red" if red else "cloth_cream"
    d.ellipse([px - 6, by - 14, px + 6, by - 1], fill=col(body, 3))
    d.pieslice([px - 6, by - 14, px + 6, by - 1], 30, 150, fill=col(body, 2))
    d.pieslice([px - 6, by - 14, px + 6, by - 1], 200, 330, fill=col(body, 4 if red else 3))
    d.rectangle([px - 6, by - 9, px + 6, by - 7], fill=col("cloth_cream", 3) if red else col("cloth_red", 3))
    d.line([(px, by - 14), (px, by - 22)], fill=col("iron", 3))
    d.polygon([(px, by - 24), (px + 5, by - 22), (px, by - 20)], fill=col("cloth_red", 3) if red else col("cloth_cream", 3))
    c = np.array(img)
    c[..., 3] = np.where(c[..., 3] > 127, 255, 0)
    BI._outline(c, "wood")
    return c


def build_struct_atlas() -> Image.Image:
    cells = [sprite_harbourmaster(), sprite_warehouse(), sprite_tavern(), sprite_fisher_hut(), sprite_crates(), sprite_barrels(),
             sprite_pile(), sprite_bollard(), sprite_lantern(), sprite_rowboat(), sprite_cannon(), sprite_signal_mast(),
             sprite_buoy(True), sprite_buoy(False)]
    atlas = Image.new("RGBA", (SC_W * S_COLS, SC_H * S_ROWS), (0, 0, 0, 0))
    for i, cell in enumerate(cells):
        atlas.paste(Image.fromarray(cell, "RGBA"), ((i % S_COLS) * SC_W, (i // S_COLS) * SC_H))
    return atlas


IMPORT_TEMPLATE = (Path(__file__).resolve().parent / "import_template.txt")


def write_import_files(names):
    """A .png.import next to each new PNG, same settings as the H2D-0.1 art (lossless, no mipmaps, no VRAM compression), so a
    first launch does not need an editor import to find them. Godot's destination name is md5('res://<path>')."""
    import hashlib
    tpl = IMPORT_TEMPLATE.read_text()
    for n in names:
        res = f"res://h2d/art/{n}"
        digest = hashlib.md5(res.encode()).hexdigest()
        (ART / (n + ".import")).write_text(tpl.replace("@NAME@", n).replace("@HASH@", digest))


def lamps_json(structs):
    return [{"name": s["name"], "x_m": s["x_m"], "z_m": s["z_m"], "y_m": round(s["y_m"] + 3.4, 2)} for s in structs if s["name"] in LAMP_NAMES]


def preview(ground, h, n, atlas_v, atlas_s, trees, structs, path_dir):
    lam = np.clip(n @ BI.LIGHT, 0, 1)
    sea = np.zeros((PX, PX, 3))
    depth = np.clip(-h / 5.0, 0, 1)[..., None]
    sea[:] = ramp("lagoon", 2) * (1 - depth) + ramp("sea_deep", 2) * depth
    shade = (0.5 + 0.7 * lam)[..., None]
    base = np.where((ground[..., 3] > 0)[..., None], ground[..., :3].astype(float) * shade, sea)
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    items = []
    for t in trees:
        items.append((t["z_m"], "v", t["type"], t["x_m"], t["z_m"], t["y_m"], t["scale"]))
    for s in structs:
        items.append((s["z_m"], "s", s["type"], s["x_m"], s["z_m"], s["y_m"], 1.0))
    for _z, kind, ty, x, zz, y, sc in sorted(items):
        if kind == "v":
            cell = atlas_v.crop(((ty % V_COLS) * CELL_W, (ty // V_COLS) * CELL_H, (ty % V_COLS + 1) * CELL_W, (ty // V_COLS + 1) * CELL_H))
            piv = PIVOT
        else:
            cell = atlas_s.crop(((ty % S_COLS) * SC_W, (ty // S_COLS) * SC_H, (ty % S_COLS + 1) * SC_W, (ty // S_COLS + 1) * SC_H))
            piv = SC_PIVOT
        if sc != 1.0:
            cell = cell.resize((int(cell.width * sc), int(cell.height * sc)), Image.NEAREST)
            piv = (int(piv[0] * sc), int(piv[1] * sc))
        px = (x + SIZE_M / 2) * PPM - piv[0]
        py = (zz + SIZE_M / 2) * PPM - piv[1] - y * PPM * math.cos(math.radians(48))
        if 0 <= px < PX - cell.width and 0 <= py < PX - cell.height:
            im.alpha_composite(cell, (int(px), int(py)))
    path_dir.mkdir(parents=True, exist_ok=True)
    im.save(path_dir / "harbor_preview.png")
    im.crop((170, 330, 700, 700)).resize((1060, 740), Image.NEAREST).save(path_dir / "harbor_preview_zoom.png")
    atlas_v.resize((atlas_v.width * 3, atlas_v.height * 3), Image.NEAREST).save(path_dir / "veg_sheet.png")
    atlas_s.resize((atlas_s.width * 2, atlas_s.height * 2), Image.NEAREST).save(path_dir / "struct_sheet.png")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--legacy", action="store_true", help="really rebuild the old 240 m island (breaks the H2D-1.2 files)")
    args = ap.parse_args()
    if not args.legacy:
        print("bake_harbor.py is a library since H2D-1.2. Run tools/h2d/bake_cay.py (or pass --legacy to rebuild the old island).")
        return 2
    h, mask, rock_mask, _rs = build_terrain()
    n = normals(h)
    slope = np.sqrt(np.maximum(1.0 - n[..., 1] ** 2, 0)) / np.maximum(n[..., 1], 1e-3)
    trees = place_vegetation(h, mask, slope, np.random.RandomState(77), rock_mask)
    structs = struct_list(h)
    ground = bake_ground(h, mask, rock_mask, n, np.random.RandomState(11))
    data = data_image(h, trees, structs)
    nrm = np.zeros((PX, PX, 4), dtype=np.uint8)
    nrm[..., :3] = np.clip((n * 0.5 + 0.5) * 255.0 + 0.5, 0, 255).astype(np.uint8)
    nrm[..., 3] = 255
    ART.mkdir(parents=True, exist_ok=True)
    Image.fromarray(ground, "RGBA").save(ART / "anvil_cay_albedo.png", optimize=True)
    Image.fromarray(data, "RGBA").save(ART / "anvil_cay_data.png", optimize=True)
    Image.fromarray(nrm, "RGBA").save(ART / "anvil_cay_normal.png", optimize=True)
    av, as_ = build_veg_atlas(), build_struct_atlas()
    av.save(ART / "anvil_veg_atlas.png", optimize=True)
    as_.save(ART / "anvil_struct_atlas.png", optimize=True)
    land = h > 0.02
    meta = {
        "id": "h2d1_anvil_cay", "name": "Anvil Cay (H2D-1 prototype harbor, not a registry island)", "harbor": HARBOR_NAME,
        "size_m": SIZE_M, "px": PX, "px_per_m": PPM, "height_min_m": H_MIN, "height_max_m": H_MAX, "sea_level_m": 0.0,
        "land_area_m2": round(float(land.sum() / PPM / PPM), 1), "peak_m": round(float(h.max()), 2),
        "files": {"albedo": "anvil_cay_albedo.png", "data": "anvil_cay_data.png", "normal": "anvil_cay_normal.png"},
        "data_channels": "R height (0..255 -> -8..40 m), G height with canopies and buildings (shadow caster), B metres from shore /40 (water side)",
        "veg_atlas": {"file": "anvil_veg_atlas.png", "cell_px": [CELL_W, CELL_H], "pivot_px": list(PIVOT), "cols": V_COLS, "rows": V_ROWS, "types": V_TYPES},
        "struct_atlas": {"file": "anvil_struct_atlas.png", "cell_px": [SC_W, SC_H], "pivot_px": list(SC_PIVOT), "cols": S_COLS, "rows": S_ROWS,
                         "types": [s[0] for s in STRUCTS if True][:0] or ["harbourmaster", "warehouse", "tavern", "fisher_hut", "crates", "barrels", "pile", "bollard",
                                                                          "lantern_post", "rowboat", "cannon", "signal_mast", "buoy_red", "buoy_cream"]},
        "harbor_layout": {
            "pier": {"x0": PIER_X0, "x1": PIER_X1, "z0": PIER_Z0, "z1": PIER_Z1, "height_m": PIER_H,
                     "head": {"x0": HEAD_X0, "z0": HEAD_Z0}},
            "berth": BERTH, "approach": APPROACH, "dock_zone": ZONE, "landing": LANDING,
            "ship_half_len_m": 11.0, "ship_half_beam_m": 3.1,
        },
        "lamps": lamps_json(structs),
        "trees": trees, "structures": structs,
    }
    (ART / "anvil_cay.json").write_text(json.dumps(meta, indent=1) + "\n")
    print(f"harbor island: land {meta['land_area_m2']} m2, peak {meta['peak_m']} m, vegetation {len(trees)}, structures {len(structs)}")
    write_import_files(["anvil_cay_albedo.png", "anvil_cay_data.png", "anvil_cay_normal.png", "anvil_veg_atlas.png",
                        "anvil_struct_atlas.png"])
    if args.preview:
        preview(ground, h, n, av, as_, trees, structs, ROOT / "art_bible/h2d1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
