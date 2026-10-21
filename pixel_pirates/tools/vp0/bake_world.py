"""VP-0: bake the two prototype world maps (cell type map + signed shore-distance map) used by vp0_terrain / vp0_ocean shaders.

  cay: Anvil Cay harbour vignette, 60 x 34 m, 1 cell = 1 m.   sea: open-water test patch with a reef and a rock islet, 160 x 90 m.
Outputs game/art/vp0/world/<name>_cells.png (R = ground type = row in ground_atlas, 255 = water), <name>_depth.png (R: signed distance to
the shore, remapped), <name>_world.json (origin, sizes, distance range, sprite placements used by the prototype scenes).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "game" / "art" / "vp0" / "world"
SAND, WET, GRASS, DIRT, COBBLE, SLAB, SHALLOW, ROCKF, WATER = 0, 1, 2, 3, 4, 5, 6, 7, 255
DMIN, DMAX = -4.0, 20.0


def save_maps(name, cells, ox, oz, margin, ppm=4):
    H, W = cells.shape
    OUT.mkdir(parents=True, exist_ok=True)
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., 0] = cells
    rgba[..., 3] = 255
    Image.fromarray(rgba, "RGBA").save(OUT / f"{name}_cells.png")
    # depth map over (W + 2 margin) x (H + 2 margin) metres
    DW, DH = int((W + 2 * margin) * ppm), int((H + 2 * margin) * ppm)
    land = np.zeros((DH, DW), bool)
    big = np.kron((cells != WATER).astype(np.uint8), np.ones((ppm, ppm), np.uint8)).astype(bool)
    land[margin * ppm:margin * ppm + H * ppm, margin * ppm:margin * ppm + W * ppm] = big
    land = ndi.gaussian_filter(land.astype(np.float32), ppm * 0.5) > 0.5
    d_out = ndi.distance_transform_edt(~land) / ppm
    d_in = ndi.distance_transform_edt(land) / ppm
    sd = np.where(land, -d_in, d_out)
    # outside the baked rectangle the sea is deep: clamp handled by DMAX
    q = np.clip((sd - DMIN) / (DMAX - DMIN), 0, 1)
    g = (q * 255).astype(np.uint8)
    rgba2 = np.zeros((DH, DW, 4), np.uint8)
    rgba2[..., 0] = g
    rgba2[..., 3] = 255
    Image.fromarray(rgba2, "RGBA").save(OUT / f"{name}_depth.png")
    meta = {"cells": [W, H], "origin": [ox, oz], "depth_rect": [ox - margin, oz - margin, W + 2 * margin, H + 2 * margin],
            "depth_range": [DMIN, DMAX], "depth_px": [DW, DH]}
    return meta


def cay():
    W, H = 60, 34
    ox, oz = -30.0, -17.0
    rng = np.random.default_rng(11)
    c = np.full((H, W), GRASS, np.uint8)
    xs = np.arange(W)

    def shore(x):
        s = 21.0 + 2.0 * np.sin(x * 0.19 + 0.4) + 1.1 * np.sin(x * 0.07 + 2.0) + rng.uniform(-0.25, 0.25)
        return s
    sh = np.array([shore(x) for x in xs])
    quay = (xs >= 4) & (xs <= 22)
    sh[quay] = 18.0
    for x in xs:
        for r in range(H):
            if r > sh[x]:
                c[r, x] = WATER
            elif quay[x] and r >= sh[x] - 0.6:
                c[r, x] = SLAB
            elif sh[x] - r < 1.3:
                c[r, x] = WET
            elif sh[x] - r < 4.2:
                c[r, x] = SAND
    # beach mixes: sand patches in the grass
    n = rng.random((H // 3 + 2, W // 3 + 2))
    for r in range(H):
        for x in range(W):
            if c[r, x] == GRASS and n[r // 3, x // 3] > 0.82 and r > 9:
                c[r, x] = SAND
    # roads and plaza
    c[11:14, :] = np.where(c[11:14, :] == WATER, WATER, COBBLE)
    c[11:18, 3:18] = COBBLE
    c[11:18, 3:18] = np.where(np.arange(W)[None, 3:18] < 0, c[11:18, 3:18], c[11:18, 3:18])
    c[18, 4:23] = SLAB
    c[14:18, 9:12] = COBBLE                             # lane to the pier
    # dirt track down to the beach and around the west cottage
    for r in range(14, 21):
        for x in (31, 32):
            if c[r, x] in (GRASS, SAND):
                c[r, x] = DIRT
    c[8:11, 4:34] = np.where(c[8:11, 4:34] == GRASS, DIRT, c[8:11, 4:34])
    c[7:11, :4] = np.where(c[7:11, :4] == GRASS, DIRT, c[7:11, :4])
    # rocky west corner
    c[16:21, 0:5] = np.where(c[16:21, 0:5] == WATER, WATER, ROCKF)
    # rock islets in the shallows (foam rims come from the distance map)
    for (cx, cr, rad) in ((13, 25, 1.8), (16, 27, 1.2), (3, 24, 2.0), (44, 27, 2.2), (50, 25, 1.4)):
        for r in range(H):
            for x in range(W):
                if np.hypot(x - cx, r - cr) <= rad:
                    c[r, x] = ROCKF
    meta = save_maps("cay", c, ox, oz, 22)
    meta["terrace"] = {"x0": 8.0, "x1": 30.0, "z0": -17.0, "z1": -10.4, "h": 1.6}
    return c, meta


def sea():
    W, H = 160, 90
    ox, oz = -80.0, -45.0
    rng = np.random.default_rng(5)
    c = np.full((H, W), WATER, np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    # islet: sand with grass top, 22 x 14 m, at (+34, -12)
    def blob(cx, cz, rx, rz, seed):
        r = np.random.default_rng(seed)
        ph = r.uniform(0, 6, 3)
        ang = np.arctan2((yy - cz) / rz, (xx - cx) / rx)
        rad = np.hypot((xx - cx) / rx, (yy - cz) / rz)
        return rad < 1.0 + 0.16 * np.sin(ang * 3 + ph[0]) + 0.09 * np.sin(ang * 5 + ph[1])
    isl = blob(114, 33, 12, 7, 1)
    c[isl] = SAND
    core = blob(114, 33, 7, 3.6, 1)
    c[core] = GRASS
    ring = ndi.binary_dilation(isl, iterations=1) & ~isl
    c[ring] = WET
    # rocks and a reef
    for (cx, cz, rad) in ((52, 48, 2.6), (58, 52, 1.6), (92, 70, 2.2), (30, 66, 1.8), (24, 20, 3.0), (136, 66, 2.4)):
        m = (np.hypot(xx - cx, yy - cz) <= rad)
        c[m] = ROCKF
    # shallow sandbar cells are WATER cells, the ocean shader paints them from the distance map (<3 m reads as sand through water)
    meta = save_maps("sea", c, ox, oz, 40, 3)
    return c, meta


if __name__ == "__main__":
    for fn, nm in ((cay, "cay"), (sea, "sea")):
        c, meta = fn()
        (OUT / f"{nm}_world.json").write_text(json.dumps(meta, indent=1))
        print(nm, c.shape, meta["depth_px"])
    # preview
    pal = {SAND: (212, 196, 150), WET: (141, 122, 82), GRASS: (101, 128, 47), DIRT: (148, 105, 59), COBBLE: (134, 119, 92), SLAB: (179, 163, 126),
           ROCKF: (92, 89, 96), WATER: (29, 95, 115)}
    for nm in ("cay", "sea"):
        a = np.array(Image.open(OUT / f"{nm}_cells.png"))[..., 0]
        im = np.zeros(a.shape + (3,), np.uint8)
        for k, v in pal.items():
            im[a == k] = v
        Image.fromarray(im).resize((a.shape[1] * 6, a.shape[0] * 6), Image.NEAREST).save(f"/tmp/{nm}_cells_prev.png")
