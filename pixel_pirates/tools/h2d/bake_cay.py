"""H2D-1.2 bake: Anvil Cay (3-5 km across). Writes the data textures, the ground palette, the sprite atlases and anvil_cay.json.

    python tools/h2d/bake_cay.py [--preview]

Outputs in game/h2d/art/:
    anvil_cay_height.png  R height (encoding in cay_terrain.enc_h), G occluder height (canopy, houses, pier, stacks), B metres to shore / 64
    anvil_cay_biome.png   R class * 16, G variation noise, B forest density * 250 (255 = keep clear of vegetation)
    anvil_cay_palette.png 8 x 16: row = class, columns 0-4 ramp, 5 params (base/4, spread/4, pattern/8), 6-7 accent colours
    anvil_veg_atlas.png (unchanged H2D-1 sprites), anvil_struct_atlas.png (grown to 4 x 5), anvil_hero_atlas.png
    anvil_cay.json        every number the game needs: grid, POIs, paths, structures, blockers, scatter rules, harbour layout
The old 240 m albedo/data/normal textures of H2D-1 are removed: the ground is now drawn by a shader from these textures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bake_harbor as BH  # noqa: E402
import bake_island as BI  # noqa: E402
import cay_sprites as CS  # noqa: E402
import cay_terrain as CT  # noqa: E402
import city_export as CE  # noqa: E402
import city_layout as CY  # noqa: E402
import city_map as CM  # noqa: E402
import port_layout as PL  # noqa: E402
import port_sprites as PS  # noqa: E402

ART = BH.ART
ROOT = BH.ROOT
N, CELL, X0, Z0 = CT.N, CT.CELL, CT.X0, CT.Z0

# palette rows: class -> (ramp, base level, spread, pattern id, accent A (ramp, step), accent B (ramp, step))
PATTERNS = {"none": 0, "ripples": 1, "tufts": 2, "strata": 3, "pebbles": 4, "cobbles": 5}
CLASS_LOOK = {
    CT.SAND: ("sand", 2.7, 0.85, "ripples", ("sand", 4), ("sand", 1)),
    CT.DUNE: ("grass", 1.1, 1.2, "tufts", ("sand", 4), ("foliage", 1)),
    CT.MEADOW: ("grass", 2.1, 1.0, "tufts", ("grass", 4), ("foliage", 0)),
    CT.FOREST: ("foliage", 1.0, 1.1, "tufts", ("foliage", 0), ("grass", 1)),
    CT.ROCK: ("stone_warm", 2.0, 1.2, "pebbles", ("stone_warm", 4), ("stone_warm", 0)),
    CT.CLIFF: ("stone_warm", 1.6, 1.4, "strata", ("stone_warm", 0), ("stone_warm", 4)),
    CT.PATH: ("dirt", 2.4, 0.8, "pebbles", ("dirt", 4), ("dirt", 1)),
    CT.COBBLE: ("stone_warm", 2.2, 1.0, "cobbles", ("stone_warm", 1), ("stone_warm", 4)),
    CT.EARTH: ("dirt", 2.1, 1.1, "pebbles", ("grass", 2), ("dirt", 4)),
    CT.MARSH: ("foliage", 1.7, 1.0, "tufts", ("lagoon", 1), ("foliage", 0)),
    CT.HEATH: ("grass", 1.0, 1.4, "tufts", ("dirt", 3), ("grass", 4)),
    CY.SLABS: ("stone_warm", 2.9, 0.7, "cobbles", ("stone_warm", 4), ("stone_warm", 2)),
    CY.PAVER: ("cloth_red", 1.3, 0.8, "cobbles", ("dirt", 2), ("cloth_red", 3)),
    CY.STEPS: ("stone_warm", 3.0, 0.5, "strata", ("stone_warm", 4), ("stone_warm", 1)),
    CY.WALLC: ("stone_warm", 1.2, 0.9, "strata", ("stone_warm", 2), ("stone_warm", 0)),
}

# vegetation: veg atlas cell indices (BH.V_TYPES): palm_a 0, palm_b 1, jungle_a 2, jungle_b 3, bush 4, rock_a 5, rock_b 6,
# palm_c 7, fern 8, grass 9, flower_bush 10, boulder 11, reef_rock 12, driftwood 13
SCATTER_SPACING_M = 8.0
CHUNK_M = 200.0
SCATTER = {   # class id -> [veg type, probability per 8 m cell, scale min, scale max]; the sum is the cell's total probability
    CT.SAND: [[13, 0.012, 0.9, 1.2], [5, 0.006, 0.5, 0.8]],
    CT.DUNE: [[0, 0.07, 0.9, 1.2], [1, 0.05, 0.9, 1.2], [7, 0.05, 0.9, 1.2], [4, 0.14, 0.9, 1.3], [9, 0.20, 0.9, 1.2]],
    CT.MEADOW: [[4, 0.08, 0.9, 1.3], [9, 0.25, 0.9, 1.2], [10, 0.07, 0.9, 1.2], [0, 0.012, 1.0, 1.2], [7, 0.01, 1.0, 1.2]],
    CT.FOREST: [[2, 0.45, 0.9, 1.3], [3, 0.35, 0.9, 1.3], [8, 0.12, 0.9, 1.2], [4, 0.08, 0.9, 1.2]],
    CT.ROCK: [[11, 0.12, 0.8, 1.5], [5, 0.08, 0.8, 1.3], [6, 0.08, 0.8, 1.3], [4, 0.04, 0.9, 1.2]],
    CT.CLIFF: [[11, 0.10, 0.9, 1.6], [6, 0.06, 0.9, 1.3]],
    CT.MARSH: [[9, 0.30, 0.9, 1.2], [8, 0.15, 0.9, 1.2], [0, 0.05, 1.0, 1.2], [1, 0.04, 1.0, 1.2]],
    CT.HEATH: [[4, 0.08, 0.9, 1.3], [9, 0.14, 0.9, 1.2], [11, 0.05, 0.8, 1.3], [10, 0.04, 0.9, 1.2]],
}
FOREST_DENSITY_MIN, FOREST_DENSITY_GAIN = 0.30, 0.70
# trunk blockers (metres): veg type -> radius; the walker cannot enter these
TRUNK_R = {0: 0.55, 1: 0.55, 7: 0.55, 2: 0.9, 3: 0.9, 5: 1.1, 6: 1.1, 11: 1.4}
HERO_TYPES = ["S0", "S1", "S2", "S3", "N0", "N1", "N2", "N3", "W0", "W1", "W2", "W3", "E0", "E1", "E2", "E3"]

# structures added by H2D-1.2 on top of the H2D-1 harbour (BH.STRUCTS stays as it was): name, atlas cell, x, z, w, d, h
VILLAGE_STRUCTS = [
    ("cottage_w1", 15, 8.3, -34.0, 8.4, 6.0, 6.0), ("cottage_w2", 16, 8.3, -58.0, 7.8, 5.6, 5.6),
    ("cottage_w3", 15, 8.3, -84.0, 8.4, 6.0, 6.0), ("cottage_e1", 16, 23.7, -30.0, 7.8, 5.6, 5.6),
    ("cottage_e2", 15, 23.7, -52.0, 8.4, 6.0, 6.0), ("cottage_e3", 16, 23.7, -78.0, 7.8, 5.6, 5.6),
    ("fisher_hut_2", 3, 26.0, -104.0, 12.0, 6.0, 4.5), ("warehouse_2", 1, -22.0, -30.0, 18.0, 8.0, 7.5),
    ("hut_shipwright", 3, 48.0, -26.0, 12.0, 6.0, 4.5),
    ("crates_c", 4, -8.0, -24.0, 3.8, 3.0, 2.4), ("barrels_c", 5, -30.0, -23.0, 3.0, 2.0, 1.4),
    ("lantern_v1", 8, 13.2, -40.0, 1.0, 0.8, 4.4), ("lantern_v2", 8, 18.8, -70.0, 1.0, 0.8, 4.4),
    ("lantern_v3", 8, 13.2, -96.0, 1.0, 0.8, 4.4),
]
EXTRA_LAMPS = ("lantern_v1", "lantern_v2", "lantern_v3")   # not added to the six lamp uniforms: they glow as sprites only


# the roads out of the capital: from the two gates in the north wall
CITY_PATHS = {
    "lookout_road": [(120, -274), (104, -320), (128, -420), (146, -520), (150, -575)],
    "pearl_track": [(128, -276), (200, -262), (290, -235), (350, -232)],
    "wreck_track": [(-110, -274), (-170, -262), (-230, -240), (-262, -226)],
}


def cell_of(x, z):
    ix = int(min(max((x - X0) / CELL, 0), N - 1))
    iz = int(min(max((z - Z0) / CELL, 0), N - 1))
    return iz, ix


def build_world():
    T = CT.build()
    PL_MASKS = PL.carve(T)                       # CP-1: level Fish Row and dig the canal before anything reads the height
    rs = np.random.RandomState(31337)
    h = T.h.copy()
    # ---- find the POIs on the beaches (before the classes: they decide where paths end) -------------------------------
    slope0 = np.hypot(*np.gradient(h, CELL))
    pois = {}
    for key, name, (bx, bz, _r) in (("pearl", "Pearl Cove", CT.BAYS[0][1:]), ("wreck", "Wreck Beach", CT.BAYS[1][1:])):
        cand = (T.d_in > 6.0) & (T.d_in < 14.0) & (slope0 < 0.2) & (h > 0.5) & T.mask
        cand &= (CT.circle_d(bx, bz) < 170.0)
        iz, ix = np.nonzero(cand)
        d = (CT.XS[ix] - bx) ** 2 + (CT.ZS[iz] - bz) ** 2
        k = int(np.argmin(d))
        pois[key] = dict(name=name, x=float(CT.XS[ix[k]]), z=float(CT.ZS[iz[k]]))
    # Lookout Hill: the highest ground within 45 m of the design spot
    lx, lz = 150.0, -575.0
    win = (CT.circle_d(lx, lz) < 45.0) & T.mask
    iz, ix = np.nonzero(win)
    k = int(np.argmax(h[iz, ix]))
    pois["lookout"] = dict(name="Lookout Hill", x=float(CT.XS[ix[k]]), z=float(CT.ZS[iz[k]]))
    pois["plaza"] = dict(name="Anvil Harbor plaza", x=16.0, z=-2.0)
    pois["fish_market"] = dict(name="Fish market", x=PL.MARKET_POINT[0], z=PL.MARKET_POINT[1])
    # the lighthouse: the seaward end of the east arm
    cand = (T.d_in > 9.0) & (h > 0.7) & (slope0 < 0.2) & (CT.X > 40.0) & (CT.X < 95.0) & (CT.Z > -5.0) & (CT.Z < 45.0)
    iz, ix = np.nonzero(cand)
    d = (CT.XS[ix] - 70.0) ** 2 + (CT.ZS[iz] - 24.0) ** 2
    k = int(np.argmin(d))
    light = (float(CT.XS[ix[k]]), float(CT.ZS[iz[k]]))

    # ---- paths: wobbly polylines painted 3.2 m wide ---------------------------------------------------------------------
    paths = {k: [tuple(p) for p in v] for k, v in CITY_PATHS.items()}
    paths["pearl_track"][-1] = (pois["pearl"]["x"], pois["pearl"]["z"])
    paths["wreck_track"][-1] = (pois["wreck"]["x"], pois["wreck"]["z"])
    paths["lookout_road"][-1] = (pois["lookout"]["x"], pois["lookout"]["z"])
    img = Image.new("L", (N, N), 0)
    dr = ImageDraw.Draw(img)
    path_pts = {}
    for name, pts in paths.items():
        dense = []
        ph = rs.uniform(0, 6.28, 3)
        for (ax, az), (bx, bz) in zip(pts[:-1], pts[1:]):
            seg = math.hypot(bx - ax, bz - az)
            m = max(int(seg / 9.0), 1)
            nx, nz = -(bz - az) / seg, (bx - ax) / seg
            for i in range(m):
                t = i / m
                wob = 5.0 * math.sin(ph[0] + 0.05 * (len(dense) * 9.0)) + 2.5 * math.sin(ph[1] + 0.13 * (len(dense) * 9.0))
                edge = 1.0 if (i > 0 or len(dense) > 0) else 0.0
                dense.append((ax + (bx - ax) * t + nx * wob * edge, az + (bz - az) * t + nz * wob * edge))
        dense.append(pts[-1])
        path_pts[name] = [[round(x, 1), round(z, 1)] for x, z in dense]
        px = [((x - X0) / CELL, (z - Z0) / CELL) for x, z in dense]
        dr.line(px, fill=255, width=2, joint="curve")
    pathmask = np.array(img) > 0
    pathmask = ndimage.binary_dilation(pathmask, iterations=1) & (rs.rand(N, N) > 0.04)
    pathmask |= CT.box(*CT.STREET)

    # ---- pads under structures and a gently smoothed terrain along the paths -----------------------------------------
    # the old harbour houses are gone (the capital's buildings come from the city plan); piles, bollards, lamps, buoys, props stay
    structs = [s_ for s_ in BH.STRUCTS if not s_[0].startswith(("warehouse", "tavern", "harbourmaster", "fisher_hut"))]
    structs += [s_ for s_ in VILLAGE_STRUCTS if s_[0].startswith("lantern")]
    structs.append(("lighthouse", 14, light[0], light[1], 6.0, 6.0, 20.0))
    structs.append(("signpost_pearl", 17, pois["pearl"]["x"] + 3.0, pois["pearl"]["z"] + 3.0, 1.4, 1.0, 5.0))
    structs.append(("signpost_wreck", 17, pois["wreck"]["x"] + 3.0, pois["wreck"]["z"] + 3.0, 1.4, 1.0, 5.0))
    structs.append(("signpost_lookout", 17, pois["lookout"]["x"] + 3.0, pois["lookout"]["z"] + 3.0, 1.4, 1.0, 5.0))
    structs.append(("rowboat_pearl", 9, pois["pearl"]["x"] - 5.0, pois["pearl"]["z"] + 8.0, 9.0, 3.0, 1.0))
    structs.append(("rowboat_wreck", 9, pois["wreck"]["x"] + 6.0, pois["wreck"]["z"] + 10.0, 9.0, 3.0, 1.0))
    structs.append(("wreck_cannon", 10, pois["wreck"]["x"] - 4.0, pois["wreck"]["z"] - 6.0, 5.0, 2.0, 1.2))
    structs.append(("wreck_crates", 4, pois["wreck"]["x"] + 2.0, pois["wreck"]["z"] - 9.0, 3.8, 3.0, 2.4))
    structs.append(("wreck_barrels", 5, pois["wreck"]["x"] + 9.0, pois["wreck"]["z"] - 3.0, 3.0, 2.0, 1.4))
    structs.append(("pearl_barrels", 5, pois["pearl"]["x"] + 6.0, pois["pearl"]["z"] - 5.0, 3.0, 2.0, 1.4))
    # the POI props were placed by offset from the stop; if the offset lands in the surf, walk it inland (1 m steps)
    ex, ez = CT.EXPLORE["x"], CT.EXPLORE["z"]
    for k, (name, cell, x, z, w, d, hh) in enumerate(structs):
        if not name.startswith(("signpost_", "rowboat_", "wreck_", "pearl_")):
            continue
        for _ in range(120):
            iz, ix = cell_of(x, z - d * 0.5)
            if h[iz, ix] >= 0.7:
                break
            L = math.hypot(ex - x, ez - z)
            x, z = x + (ex - x) / L, z + (ez - z) / L
        structs[k] = (name, cell, x, z, w, d, hh)
    pad = np.zeros((N, N), np.float32)
    padh = np.zeros((N, N), np.float32)
    for name, _cell, x, z, w, d, _hh in structs:
        if name.startswith(("pile", "bollard", "buoy", "lamp_head", "lamp_pier")):
            continue
        if (CT.PIER["x0"] - 0.2 <= x <= CT.PIER["x1"] + 0.2 and CT.PIER["z0"] <= z <= CT.PIER["z1"]):
            continue
        iz, ix = cell_of(x, z - d * 0.5)
        y0 = float(h[iz, ix])
        if name.startswith(("cottage", "fisher", "hut", "warehouse", "lighthouse", "tavern", "harbour")):
            m = CT.box(x - w / 2 - 2.0, z - d - 2.0, x + w / 2 + 2.0, z + 3.0)
            pad = np.maximum(pad, m.astype(np.float32))
            padh = np.where(m, np.maximum(y0, 1.95 if z > -22.0 else 0.0), padh)
    padg = ndimage.gaussian_filter(pad, 2.0) * T.mask
    padg = np.clip(padg * 1.4, 0, 1)
    h = np.where(padg > 0.01, h * (1 - padg) + padh * padg, h)
    hs = ndimage.gaussian_filter(h, 2.2)
    pm2 = ndimage.binary_dilation(pathmask, iterations=3) & T.mask & (h > 1.0)
    pm2 = ndimage.gaussian_filter(pm2.astype(np.float32), 1.5)
    h = np.where(T.mask, h * (1 - 0.8 * pm2) + hs * 0.8 * pm2, h)
    h = np.where(T.mask & (T.h > 0), np.maximum(h, 0.15), h)
    CE.small_sizes()
    h = CY.shape(h, T)
    h = CY.shore_ramp(h, T)


    # ---- classes ------------------------------------------------------------------------------------------------------
    gz, gx = np.gradient(h, CELL)
    slope = np.hypot(gx, gz).astype(np.float32)
    land = T.mask & (h > 0.02)
    cls = np.full((N, N), CT.MEADOW, np.uint8)
    noise_a = CT.fbm(rs, 38.0, 2)
    noise_b = CT.fbm(rs, 120.0, 3)
    beach = T.d_in < T.beach_w * (0.85 + 0.25 * noise_a)
    dune = T.d_in < (T.beach_w + 20.0 * (1.0 - T.cliffk)) * (1.0 + 0.2 * noise_a)
    f = CT.soft(CT.fbm(rs, 300.0, 3), -0.25, 0.55)
    glade = CT.soft(CT.fbm(rs, 70.0, 2), 0.7, 1.3)
    f = f + 0.6 * np.exp(-((CT.X - 70.0) ** 2 + (CT.Z + 330.0) ** 2) / (2.0 * 210.0 ** 2)).astype(np.float32) * (0.5 + 0.5 * CT.soft(noise_b, -0.9, 0.7))
    f = f * (1.0 - 0.9 * glade) * CT.soft(T.d_in, T.beach_w + 16.0, T.beach_w + 70.0) * (1.0 - CT.soft(h, 38.0, 60.0))
    f = f * (1.0 - 0.85 * T.cliffk) * (1.0 - CT.soft(slope, 0.5, 0.8))
    f = np.clip(f * 1.15, 0.0, 1.0).astype(np.float32)
    forest = f > 0.30
    heath = (h > 22.0 + 6.0 * noise_a) & ~forest
    marsh = (h < 2.45) & (T.d_in > T.beach_w + 24.0) & (noise_b > 0.55)
    cls = np.where(heath, CT.HEATH, cls)
    cls = np.where(marsh, CT.MARSH, cls)
    cls = np.where(forest, CT.FOREST, cls)
    cls = np.where(dune, CT.DUNE, cls)
    cls = np.where(beach, CT.SAND, cls)
    rocky = (slope > 0.5) | (h > 52.0 + 4 * noise_a) | ((T.cliffk > 0.35) & (T.d_in < 26.0))
    cls = np.where(rocky, CT.ROCK, cls)
    cls = np.where((slope > 0.85) | ((T.cliffk > 0.45) & (T.d_in < 14.0) & (h > 3.0)), CT.CLIFF, cls)
    cls = np.where(T.rockmask & (h > 0.03), CT.ROCK, cls)
    # the village: trodden earth around the harbour, cobbles on the plaza, the street and every footpath
    x0, z0, x1, z1 = CT.VILLAGE
    sdf = np.maximum(np.maximum(x0 - CT.X, CT.X - x1), np.maximum(z0 - CT.Z, CT.Z - z1))
    vill = (sdf + 4.5 * noise_a < 0.0) & land & (h > 1.4)
    cls = np.where(vill, CT.EARTH, cls)
    plz = CT.box(*CT.PLAZA)
    ex = (np.abs(CT.X - 16.0) < 19.0 + 0.8 * noise_a) & (CT.Z > CT.PLAZA[1] + 0.8 * noise_a) & (CT.Z < CT.PLAZA[3] + 0.8 * noise_a)
    cls = np.where(ex & land, CT.COBBLE, cls)
    del plz
    # CP-1: Fish Row is cobbled (floors incl. the apron), the canal banks are quay walls, the lots behind the yard are earth
    pfloor = np.zeros((N, N), bool)
    for fx0, fz0, fx1, fz1 in PL.FLOORS:
        pfloor |= CT.box(fx0, fz0, fx1, fz1)
    cls = np.where((pfloor | PL_MASKS["apron"] | ndimage.binary_dilation(PL_MASKS["canal"], iterations=2)) & land, CT.COBBLE, cls)
    cls = np.where(CT.box(-122.0, -46.0, -34.0, -29.0) & land & (cls != CT.COBBLE), CT.EARTH, cls)
    cls = np.where(pathmask & land & (cls != CT.COBBLE), CT.PATH, cls)
    cls = np.where(T.rockmask & (h > 0.03), CT.ROCK, cls)
    cls = CY.paint(cls, land & (h > 0.02), h)
    city = CY.plan(h, cls, land & (h > 0.02), np.random.RandomState(7))
    # structure footprints: earth under every house, and no vegetation near anything (blue channel 255)
    clear = np.zeros((N, N), bool)
    blockers = []
    for name, _cell, x, z, w, d, hh in structs:
        if name.startswith(("pile", "bollard", "buoy", "lamp")):
            continue
        if name.startswith(("lantern",)):
            continue
        m = CT.box(x - w / 2 - 2.5, z - d - 2.0, x + w / 2 + 2.5, z + 3.0)
        clear |= m
        if name.startswith(("cottage", "fisher", "hut", "warehouse", "lighthouse", "tavern", "harbour")):
            cls = np.where(CT.box(x - w / 2 - 1.2, z - d - 1.2, x + w / 2 + 1.2, z + 1.5) & land & (cls != CT.COBBLE), CT.EARTH, cls)
        if name.startswith(("crates", "barrels", "cannon", "wreck", "pearl", "signal", "rowboat", "signpost")):
            pass
        solid = not name.startswith(("signpost", "rowboat")) or True
        if solid and not name.startswith("signpost"):
            blockers.append([round(x - w / 2 - 0.3, 2), round(z - d, 2), round(x + w / 2 + 0.3, 2), round(z + 0.4, 2)])
    blockers.extend(PL.solid_rects())
    blockers.extend(CE.blockers(city))
    clear |= CT.box(*CY.CLEAR_BOX)
    clear |= ndimage.binary_dilation(pathmask, iterations=2)
    clear |= CT.box(-34.0, -128.0, 62.0, 8.0)
    clear |= CT.box(-125.0, -46.0, -1.0, 40.0)
    lk = CT.circle_d(pois["lookout"]["x"], pois["lookout"]["z"]) < 12.0
    cls = np.where(lk & land, CT.HEATH, cls)
    clear |= lk
    cls = np.where(land, cls, 0).astype(np.uint8)

    # ---- the data textures ----------------------------------------------------------------------------------------
    var = np.clip(0.5 + 0.28 * CT.fbm(rs, 16.0, 2), 0, 1)
    forest_b = np.where(cls == CT.FOREST, f, 0.0)
    biome = np.zeros((N, N, 4), np.uint8)
    biome[..., 0] = cls * 16
    biome[..., 1] = (var * 255).astype(np.uint8)
    biome[..., 2] = np.where(clear, 255, np.clip(forest_b * 250.0, 0, 250)).astype(np.uint8)
    biome[..., 3] = 255
    # the occluder map: canopies, houses, stacks, the pier (the pier is stamped here ONLY, so the ground mesh stays flat)
    occ = h.copy()
    canopy = np.where(cls == CT.FOREST, 9.0 * np.clip(f * 1.6, 0.0, 1.0), 0.0)
    occ = occ + ndimage.gaussian_filter(canopy, 1.2)
    for name, _cell, x, z, w, d, hh in structs:
        if name.startswith(("pile", "bollard", "buoy", "lamp", "signpost", "rowboat", "crates", "barrels", "cannon", "wreck", "pearl")):
            continue
        m = CT.box(x - w / 2, z - d, x + w / 2, z)
        iz, ix = cell_of(x, z - d * 0.5)
        base = float(h[iz, ix]) if not (CT.PIER["x0"] - 0.2 <= x <= CT.PIER["x1"] + 0.2) else CT.PIER_H
        occ = np.where(m, np.maximum(occ, base + hh), occ)
    occ = CE.occluders(city, occ, h, cell_of)
    pm = CT.pier_mask()
    occ = np.where(pm, np.maximum(occ, CT.PIER_H), occ)
    heightpng = np.zeros((N, N, 4), np.uint8)
    heightpng[..., 0] = CT.enc_h(h)
    heightpng[..., 1] = CT.enc_h(occ)
    heightpng[..., 2] = np.clip(T.d_out / 64.0 * 255.0, 0, 255).astype(np.uint8)
    heightpng[..., 3] = 255
    return dict(T=T, h=h, cls=cls, f=f, slope=slope, pois=pois, paths=path_pts, structs=structs, blockers=blockers, light=light,
                biome=biome, heightpng=heightpng, rs=rs, city=city)


def palette_image() -> Image.Image:
    img = np.zeros((16, 8, 4), np.uint8)
    for c, (ramp, base, spread, pat, a, b) in CLASS_LOOK.items():
        for i in range(5):
            img[c, i, :3] = BI.ramp(ramp, i)
        img[c, 5] = (int(base / 4.0 * 255 + 0.5), int(spread / 4.0 * 255 + 0.5), PATTERNS[pat] * 32, 255)
        img[c, 6, :3] = BI.ramp(*a)
        img[c, 7, :3] = BI.ramp(*b)
        img[c, :5, 3] = 255
        img[c, 6:, 3] = 255
    return Image.fromarray(img, "RGBA")


def sample_h(w, x, z):
    iz, ix = cell_of(x, z)
    return float(w["h"][iz, ix])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    w = build_world()
    T, h, cls = w["T"], w["h"], w["cls"]
    ART.mkdir(parents=True, exist_ok=True)
    Image.fromarray(w["heightpng"], "RGBA").save(ART / "anvil_cay_height.png", optimize=True)
    Image.fromarray(w["biome"], "RGBA").save(ART / "anvil_cay_biome.png", optimize=True)
    palette_image().save(ART / "anvil_cay_palette.png")
    BH.build_veg_atlas().save(ART / "anvil_veg_atlas.png", optimize=True)
    PS.build_all(ART)
    catl = CE.build_atlases(ART)
    city = w["city"]
    CS.build_struct_atlas().save(ART / "anvil_struct_atlas.png", optimize=True)
    CS.build_hero_atlas().save(ART / "anvil_hero_atlas.png", optimize=True)
    # structures, with ground heights
    structs = []
    for name, cell, x, z, wd, dp, hh in w["structs"]:
        gy = sample_h(w, x, z - dp * 0.5)
        if name.startswith(("pile", "bollard", "lamp_head", "lamp_pier")) or (CT.PIER["x0"] - 0.2 <= x <= CT.PIER["x1"] + 0.2
                                                                              and CT.PIER["z0"] <= z <= CT.PIER["z1"]):
            gy = CT.PIER_H
        if name.startswith("buoy"):
            gy = -0.1
        structs.append({"name": name, "x_m": round(x, 2), "z_m": round(z, 2), "y_m": round(gy, 2), "type": cell, "scale": 1.0,
                        "w_m": wd, "d_m": dp, "h_m": hh})
    props = []
    for cx, cz, r, hh in T.stacks:
        if hh < 0.9:
            continue
        iz, ix = cell_of(cx, cz)
        top = float(h[iz, ix])
        if top < 0.3:
            continue     # drowned by the blur: no sprite without something to grind on
        props.append({"x_m": round(cx, 1), "z_m": round(cz, 1), "y_m": round(max(top, 0.0) - 0.1, 2), "type": 12,
                      "scale": round(min(max(r / 3.0, 0.7), 1.5), 2)})
    # land measures
    land = T.mask & (h > 0.02)
    ys, xs = np.nonzero(land)
    edge = land & ~ndimage.binary_erosion(land)
    pts = np.argwhere(edge)[::5] * CELL
    from scipy.spatial import ConvexHull
    hull = pts[ConvexHull(pts).vertices]
    diam = float(np.sqrt(((hull[:, None, :] - hull[None, :, :]) ** 2).sum(-1)).max())
    bbox = [float(CT.XS[xs.min()]), float(CT.ZS[ys.min()]), float(CT.XS[xs.max()]), float(CT.ZS[ys.max()])]
    per = float(edge.sum() * CELL * 1.2)
    lamp_names = BH.LAMP_NAMES
    lamps = [{"name": s["name"], "x_m": s["x_m"], "z_m": s["z_m"], "y_m": round(s["y_m"] + 3.4, 2)} for s in structs if s["name"] in lamp_names]
    pois = w["pois"]
    port = PL.port_json(h, lambda x, z: sample_h(w, x, z))
    lists = CE.sprite_lists(city, catl, lambda x, z: sample_h(w, x, z))
    port["atlases"].update(catl)
    port["props"] = list(port["props"]) + lists.pop("stall")
    port["city"] = {"lists": lists, "trees": CE.trees(city, lambda x, z: sample_h(w, x, z))}
    port["npcs"] = list(port["npcs"]) + CE.npc_records(city)
    port["places"] = city.places
    port["spots"] = {k: list(v) for k, v in city.spots.items()}
    port["name"] = "Anvil Harbor"
    w2 = dict(w)
    w2["port_map"] = port["map"]
    CM.city_map(w2, city, ART)
    CM.island_map(w2, ART)
    CM.sea_map(w2, ART)
    port["map"]["views"] = [CM.CITY_VIEW, CM.ISLAND_VIEW, CM.SEA_VIEW]
    # the map screen (game/ui/map) reads its three views from this small file, not from the big island json
    (ART / "map_views.json").write_text(json.dumps({"views": port["map"]["views"]}, indent=1) + "\n", encoding="utf-8")
    meta = {
        "id": "h2d1_2_anvil_cay", "name": "Anvil Cay (H2D-1.2 prototype, medium island, not a registry island)", "harbor": BH.HARBOR_NAME,
        "version": 3, "scale_note": "1 scene unit = 1 m = 1 geographic metre",
        "grid": {"origin_x": X0, "origin_z": Z0, "cells": N, "cell_m": CELL, "size_m": N * CELL},
        "height_enc": {"sea_min": -8.0, "knee": 0.1, "top": CT.H_TOP},
        "files": {"height": "anvil_cay_height.png", "biome": "anvil_cay_biome.png", "palette": "anvil_cay_palette.png"},
        "channels": "height: R ground, G occluder (canopy, houses, pier, stacks), B metres to shore / 64. biome: R class*16, G variation, B forest density*250 (255 = keep clear)",
        "extent": {"bbox_m": [round(v, 1) for v in bbox], "diameter_m": round(diam, 1), "area_km2": round(float(land.sum()) * CELL * CELL / 1e6, 3),
                   "peak_m": round(float(h.max()), 1), "coast_m": round(per, 0)},
        "classes": {str(k): v for k, v in CT.CLASS_NAMES.items()},
        "bays": [{"name": n, "x": x, "z": z, "r": r} for n, x, z, r in CT.BAYS],
        "hills": [{"name": n, "x": x, "z": z, "sigma": s, "h": hh} for n, x, z, s, hh in CT.HILLS],
        "veg_atlas": {"file": "anvil_veg_atlas.png", "cell_px": [BH.CELL_W, BH.CELL_H], "pivot_px": list(BH.PIVOT), "cols": BH.V_COLS,
                      "rows": BH.V_ROWS, "types": BH.V_TYPES},
        "struct_atlas": {"file": "anvil_struct_atlas.png", "cell_px": [BH.SC_W, BH.SC_H], "pivot_px": list(BH.SC_PIVOT),
                         "cols": CS.STRUCT_COLS, "rows": CS.STRUCT_ROWS, "types": CS.STRUCT_TYPES},
        "hero_atlas": {"file": "anvil_hero_atlas.png", "cell_px": [CS.HERO_W, CS.HERO_H], "pivot_px": list(CS.HERO_PIVOT), "cols": 4,
                       "rows": 4, "types": HERO_TYPES},
        "scatter": {"spacing_m": SCATTER_SPACING_M, "chunk_m": CHUNK_M, "forest_density_min": FOREST_DENSITY_MIN,
                    "forest_density_gain": FOREST_DENSITY_GAIN, "min_height_m": 0.45,
                    "classes": {str(k): v for k, v in SCATTER.items()}, "trunk_r": {str(k): v for k, v in TRUNK_R.items()}},
        "harbor_layout": {
            "pier": {"x0": CT.PIER["x0"], "x1": CT.PIER["x1"], "z0": CT.PIER["z0"], "z1": CT.PIER["z1"], "height_m": CT.PIER_H,
                     "head": {"x0": CT.HEAD["x0"], "z0": CT.HEAD["z0"]}},
            "berth": BH.BERTH, "approach": BH.APPROACH, "dock_zone": BH.ZONE, "landing": BH.LANDING,
            "ship_half_len_m": 11.0, "ship_half_beam_m": 3.1,
        },
        "land": {"explore": CT.EXPLORE, "disembark": {"x": 16.0, "z": 21.0}, "board": {"x": 16.0, "z": 21.0},
                 "pois": [{"id": k, **pois[k]} for k in ("plaza", "fish_market", "pearl", "lookout", "wreck")]},
        "paths": w["paths"],
        "lamps": lamps, "structures": structs, "props": props, "blockers": w["blockers"],
        "port": port,
    }
    (ART / "anvil_cay.json").write_text(json.dumps(meta, separators=(",", ":")) + "\n")
    names = ["anvil_cay_height.png", "anvil_cay_biome.png", "anvil_cay_palette.png", "anvil_veg_atlas.png", "anvil_struct_atlas.png",
             "anvil_hero_atlas.png", "port_stall_atlas.png", "port_misc_atlas.png", "port_big_atlas.png", "port_ships_atlas.png",
             "port_npc_atlas.png", "city_small_atlas.png", "city_grand_atlas.png", "city_civic_atlas.png",
             "city_props_atlas.png", "port_cue_atlas.png", "map_city.png", "map_island.png", "map_sea.png"]
    write_import_files(names)
    for old in ("anvil_cay_albedo.png", "anvil_cay_data.png", "anvil_cay_normal.png"):
        for ext in ("", ".import"):
            (ART / (old + ext)).unlink(missing_ok=True)
    print(f"Anvil Cay: diameter {diam / 1000:.2f} km, area {meta['extent']['area_km2']} km2, peak {meta['extent']['peak_m']} m, "
          f"structures {len(structs)}, props {len(props)}, blockers {len(w['blockers'])}")
    if args.preview:
        preview(w)
    return 0


def write_import_files(names):
    """.png.import beside each PNG: lossless, no mipmaps (the data textures MUST NOT be compressed or filtered by the importer)."""
    tpl = BH.IMPORT_TEMPLATE.read_text()
    for n in names:
        digest = hashlib.md5(f"res://h2d/art/{n}".encode()).hexdigest()
        (ART / (n + ".import")).write_text(tpl.replace("@NAME@", n).replace("@HASH@", digest))


def preview(w):
    out = ROOT / "art_bible/h2d1_2"
    out.mkdir(parents=True, exist_ok=True)
    cls = w["cls"]
    cols = {0: (20, 70, 100), 1: (230, 215, 160), 2: (170, 170, 90), 3: (120, 160, 70), 4: (40, 90, 50), 5: (140, 130, 115),
            6: (90, 80, 70), 7: (190, 140, 80), 8: (150, 110, 70), 9: (110, 130, 120), 10: (130, 140, 60), 11: (140, 150, 80)}
    rgb = np.zeros((N, N, 3), np.uint8)
    for k, c in cols.items():
        rgb[cls == k] = c
    gz, gx = np.gradient(w["h"], CELL)
    shade = np.clip(0.75 + (gx * -0.6 + gz * -0.6) * 0.8, 0.5, 1.3)
    rgb = np.clip(rgb * shade[..., None], 0, 255).astype(np.uint8)
    im = Image.fromarray(rgb).resize((1100, 1100), Image.LANCZOS)
    d = ImageDraw.Draw(im)

    def px(x, z):
        return (x - X0) / 4.0, (z - Z0) / 4.0
    for name, pts in w["paths"].items():
        d.line([px(*p) for p in pts], fill=(255, 255, 255), width=1)
    for k, p in w["pois"].items():
        a, b = px(p["x"], p["z"])
        d.ellipse((a - 5, b - 5, a + 5, b + 5), outline=(255, 0, 0), width=2)
        d.text((a + 8, b - 6), p["name"], fill=(255, 255, 0))
    cx, cz, r = CT.EXPLORE["x"], CT.EXPLORE["z"], CT.EXPLORE["r"]
    a, b = px(cx, cz)
    d.ellipse((a - r / 4, b - r / 4, a + r / 4, b + r / 4), outline=(255, 120, 0))
    im.save(out / "island_map.png")
    # a zoomed crop of the walkable area
    crop = Image.fromarray(rgb).crop((int((-560 - X0) / 2), int((-880 - Z0) / 2), int((620 - X0) / 2), int((100 - Z0) / 2)))
    crop.save(out / "walk_area.png")


if __name__ == "__main__":
    raise SystemExit(main())
