"""Bakes the H2D-0 demo island "Anvil Cay" (Module H2D-0): ground texture, height/shadow data, normal map, tree atlas, tree list.

  python tools/h2d/bake_island.py            # writes game/h2d/art/island_anvil_*.png, trees_atlas.png, island_anvil.json
  python tools/h2d/bake_island.py --preview  # also art_bible/h2d0/island_preview.png and trees_sheet.png

The island is a 160 x 160 m patch at 3.6 px/m (576 x 576 px). Heights run from -8 m (sea floor) to +40 m (encoded 0..255).
The game lights the ground per pixel from the height data and casts hill and tree shadows by ray-marching, so the albedo here
is FLAT colour (no baked light). Deterministic (fixed seeds).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
PALETTE = json.loads((ROOT / "game/data/look/palette.json").read_text())["ramps"]
SIZE_M = 160.0
PX = 576
PPM = PX / SIZE_M
H_MIN, H_MAX = -8.0, 40.0
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
LIGHT = np.array([-0.5, 0.95, -0.6])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def rgb(h: str) -> np.ndarray:
    return np.array([int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)], dtype=np.uint8)


def ramp(name: str, i: int) -> np.ndarray:
    return rgb(PALETTE[name][i])


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


def ellipse_field(cx, cy, rx, ry, rot=0.0):
    """Normalised distance (1 at the rim) in metres-from-centre coordinates."""
    ys, xs = np.mgrid[0:PX, 0:PX]
    x = (xs + 0.5) / PPM - SIZE_M / 2 - cx
    y = (ys + 0.5) / PPM - SIZE_M / 2 - cy
    c, s = math.cos(rot), math.sin(rot)
    xr, yr = x * c + y * s, -x * s + y * c
    return np.sqrt((xr / rx) ** 2 + (yr / ry) ** 2)


def build_terrain() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rs = np.random.RandomState(20261018)
    warp = fbm(rs, 28, 3)
    body = np.minimum.reduce([
        ellipse_field(-6, 4, 52, 27, -0.18),
        ellipse_field(34, 10, 24, 17, 0.35),
        ellipse_field(-38, -4, 20, 24, 0.0),
    ])
    body = body + 0.16 * warp
    bay = ellipse_field(18, 33, 17, 13, 0.0)  # a bite out of the south shore
    land_field = np.minimum(1.0 - body, bay - 1.0 + 0.0) if False else (1.0 - body)
    land_field = np.minimum(land_field, (bay - 1.0) * 1.0 + 0.0)
    land_field = ndimage.gaussian_filter(land_field, 2.0)
    # shore profile: gentle beach, shelf falling away offshore
    h = np.where(land_field > 0, np.minimum(land_field * 9.0, 3.0) + 0.0, land_field * 22.0)
    h = np.clip(h, -8.0, 3.0)
    # the Anvil: a steep rocky hill on the western lobe, plus a lower knoll to the east
    anvil = np.clip(1.0 - ellipse_field(-34, -6, 20, 15, 0.1), 0, 1)
    anvil = ndimage.gaussian_filter(np.where(anvil > 0.0, np.minimum(anvil * 2.6, 1.0), 0.0), 4.0)
    knoll = np.clip(1.0 - ellipse_field(30, 8, 14, 10, 0.3), 0, 1)
    knoll = ndimage.gaussian_filter(knoll, 3.0)
    ridge = fbm(rs, 10, 4)
    on_land = (land_field > 0.02).astype(float)
    h = h + on_land * (anvil * (27.0 + 4.5 * ridge) + knoll * (8.0 + 2.0 * ridge) + 0.8 * ridge * np.clip(land_field * 3, 0, 1))
    h = np.where(land_field > 0.02, np.maximum(h, 0.15), h)
    h = np.clip(h, H_MIN, H_MAX - 1.0)
    return ndimage.gaussian_filter(h, 0.8), land_field, rs.randn(PX, PX)


def normals(h: np.ndarray) -> np.ndarray:
    m = 1.0 / PPM
    dz, dx = np.gradient(h, m)  # rows go south (+z), columns go east (+x)
    n = np.stack([-dx, np.ones_like(h), -dz], axis=-1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def place_trees(h: np.ndarray, slope: np.ndarray, rs: np.random.RandomState) -> list[dict]:
    """type: 0,1 palm; 2,3 jungle tree; 4 bush; 5,6 rock."""
    forest = fbm(rs, 14, 3)
    trees: list[dict] = []
    taken: list[tuple[float, float, float]] = []

    def free(x, y, r):
        return all((x - a) ** 2 + (y - b) ** 2 >= (r + rr) ** 2 for a, b, rr in taken)

    def sample(kind: str, count: int, tries: int, rad: float, cond, types, scale=(0.9, 1.15)):
        got = 0
        for _ in range(tries):
            if got >= count:
                break
            px, py = rs.randint(4, PX - 4, 2)
            hh, sl = h[py, px], slope[py, px]
            x, z = (px + 0.5) / PPM - SIZE_M / 2, (py + 0.5) / PPM - SIZE_M / 2
            if cond(hh, sl, forest[py, px]) and free(x, z, rad):
                taken.append((x, z, rad))
                trees.append({"x_m": round(float(x), 2), "z_m": round(float(z), 2), "y_m": round(float(hh), 2), "type": int(rs.choice(types)),
                              "scale": round(float(rs.uniform(*scale)), 2)})
                got += 1

    sample("jungle", 110, 9000, 4.2, lambda hh, sl, f: 2.6 < hh < 20.0 and sl < 0.75 and f > -0.15, [2, 3], (0.85, 1.25))
    sample("palm", 46, 9000, 3.4, lambda hh, sl, f: 0.7 < hh < 3.0 and sl < 0.5, [0, 1], (0.9, 1.2))
    sample("bush", 60, 9000, 2.0, lambda hh, sl, f: 1.0 < hh < 22.0 and sl < 0.9, [4], (0.9, 1.3))
    sample("rock", 26, 9000, 3.0, lambda hh, sl, f: (hh > 14.0 and sl > 0.5) or (0.3 < hh < 1.2 and sl > 0.3), [5, 6], (0.9, 1.4))
    return trees


def bake_ground(h: np.ndarray, land_field: np.ndarray, n: np.ndarray, rs: np.random.RandomState) -> np.ndarray:
    slope = np.sqrt(np.maximum(1.0 - n[..., 1] ** 2, 0)) / np.maximum(n[..., 1], 1e-3)
    detail = fbm(rs, 3.0, 2)
    patch = fbm(rs, 16.0, 3)
    ys, xs = np.mgrid[0:PX, 0:PX]
    bay = BAYER[ys % 4, xs % 4]
    img = np.zeros((PX, PX, 4), dtype=np.uint8)
    # a continuous "elevation score" with dithered band edges gives the painted pixel-art transitions
    z = h + 0.5 * detail + 0.9 * patch
    layers = [
        (-99.0, ("sand", 1)), (0.55, ("sand", 2)), (1.25, ("sand", 3)), (2.2, ("grass", 2)), (3.4, ("grass", 1)),
        (6.5, ("foliage", 1)), (15.0, ("foliage", 0)),
    ]
    out = np.zeros((PX, PX, 3), dtype=np.uint8)
    idx = np.zeros((PX, PX), dtype=np.int32)
    thr = np.array([t for t, _ in layers])
    for i in range(len(layers)):
        nxt = thr[i + 1] if i + 1 < len(layers) else 1e9
        band = nxt - thr[i] if nxt < 1e8 else 4.0
        # dither across the top 25% of each band
        edge = thr[i] + 0.75 * band
        up = (z >= nxt - 0.25 * band) & (z < nxt) & (bay < (z - (nxt - 0.25 * band)) / (0.25 * band))
        idx = np.where((z >= thr[i]) & (z < nxt), i, idx)
        idx = np.where(up, i + 1, idx)
    idx = np.where(z >= thr[-1], len(layers) - 1, idx)
    for i, (_t, (name, st)) in enumerate(layers):
        out[idx == i] = ramp(name, st)
    # cliffs and the Anvil's flanks: stone, with a dithered skirt
    stone_score = slope + 0.12 * detail + (np.clip(h - 16.0, 0, 20) * 0.03)
    stone = (stone_score > 0.95) | ((stone_score > 0.78) & (bay < 0.5))
    smooth = ndimage.gaussian_filter(detail, 1.5) * 2.2
    shade_idx = np.clip(((smooth + 0.9 + 0.045 * (h - 14.0)) * 1.3).astype(int), 1, 3)
    for k in (1, 2, 3):
        out[stone & (shade_idx == k)] = ramp("stone_warm", k)
    out[stone & (detail < -1.35)] = ramp("stone_warm", 0)
    # wet sand along the waterline
    wet = (h < 0.45) & (h > 0.0)
    out[wet] = ramp("sand", 0)
    # speckle: 1 px tufts and pebbles
    sp = rs.rand(PX, PX)
    grass_zone = (idx >= 3) & ~stone
    out[grass_zone & (sp > 0.985)] = ramp("grass", 4)
    out[grass_zone & (sp < 0.012)] = ramp("foliage", 0)
    sand_zone = (idx <= 2) & ~stone & ~wet
    out[sand_zone & (sp > 0.992)] = ramp("sand", 4)
    out[sand_zone & (sp < 0.006)] = ramp("sand", 0)
    alpha = np.where(h > 0.02, 255, 0).astype(np.uint8)
    img[..., :3] = out
    img[..., 3] = alpha
    return img


def data_image(h: np.ndarray, trees: list[dict], land_field: np.ndarray) -> np.ndarray:
    occl = h.copy()
    for t in trees:
        if t["type"] in (4,):
            top, rad = 2.0, 1.2
        elif t["type"] in (5, 6):
            top, rad = 2.5, 1.6
        elif t["type"] in (0, 1):
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
    dist = ndimage.distance_transform_edt(h <= 0.02) / PPM  # metres from the shore, on the water side
    img = np.zeros((PX, PX, 4), dtype=np.uint8)
    img[..., 0] = np.clip((h - H_MIN) / (H_MAX - H_MIN) * 255.0 + 0.5, 0, 255)
    img[..., 1] = np.clip((occl - H_MIN) / (H_MAX - H_MIN) * 255.0 + 0.5, 0, 255)
    img[..., 2] = np.clip(dist / 40.0 * 255.0, 0, 255)
    img[..., 3] = 255
    return img


# ---- tree sprites -----------------------------------------------------------------------------------------------
CELL_W, CELL_H = 48, 56
PIVOT = (24, 52)
ATLAS_COLS, ATLAS_ROWS = 4, 2


def _blob(canvas, shade, cx, cy, rx, ry, rs, ramp_name, light=(-0.55, -0.7)):
    """Fill an ellipse with ramp shading from the north-west, dithered; writes colour and a mask."""
    h, w = canvas.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w]
    dx, dy = (xs + 0.5 - cx) / rx, (ys + 0.5 - cy) / ry
    inside = dx * dx + dy * dy <= 1.0
    d = (dx * light[0] + dy * light[1]) * -1.0  # +1 where it faces the light
    v = 0.52 - 0.5 * d
    v = v + (BAYER[ys % 4, xs % 4] - 0.5) * 0.28
    step = np.clip(np.floor((1.0 - v) * 4.2).astype(int), 0, 4)
    step = np.clip(step, 0, 4)
    for s in range(5):
        m = inside & (step == s)
        canvas[m] = np.append(ramp(ramp_name, s), 255)
    shade[inside] = True


def _outline(canvas, name):
    solid = canvas[..., 3] > 0
    pad = np.pad(solid, 1, constant_values=False)
    edge = solid & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    canvas[edge] = np.append(ramp(name, 0), 255)


def sprite_palm(variant: int) -> np.ndarray:
    c = np.zeros((CELL_H, CELL_W, 4), dtype=np.uint8)
    rs = np.random.RandomState(100 + variant)
    lean = [-2.0, 1.4][variant]
    pts = []
    for i in range(0, 25):
        t = i / 24.0
        pts.append((PIVOT[0] + lean * (t ** 1.6) * 3.0, PIVOT[1] - 30.0 * t))
    d = ImageDraw.Draw(Image.fromarray(c, "RGBA"))
    img = Image.fromarray(c, "RGBA")
    d = ImageDraw.Draw(img)
    for i, (x, y) in enumerate(pts):
        wdt = 3 if i < 14 else 2
        col = tuple(int(v) for v in ramp("wood", 2)) + (255,)
        d.rectangle([x - wdt / 2 - 0.5, y, x + wdt / 2 - 0.5, y + 1], fill=col)
        d.point((x - wdt / 2 - 0.5, y), fill=tuple(int(v) for v in ramp("wood", 3)) + (255,))
        d.point((x + wdt / 2 - 0.5, y), fill=tuple(int(v) for v in ramp("wood", 1)) + (255,))
    top = pts[-1]
    # fronds: drooping arcs from the crown, lit from the north-west
    n_f = 11
    for f in range(n_f):
        ang = (f / n_f) * 2 * math.pi + 0.3 * variant
        length = 13 + 2.5 * math.sin(f * 2.1)
        for s in range(0, 41):
            t = s / 40.0
            fx = top[0] + math.cos(ang) * length * t
            fy = top[1] - 4.0 + math.sin(ang) * length * t * 0.40 + 8.0 * t * t - 3.0 * math.sin(math.pi * t)
            lit = (math.cos(ang) * -0.5 + math.sin(ang) * -0.7)
            step = 3 if lit > 0.25 else (2 if lit > -0.35 else 1)
            if t < 0.35:
                step = min(4, step + 1)
            wdt = 3.6 * (1.0 - t) + 1.4
            col = tuple(int(v) for v in ramp("palm_frond", step)) + (255,)
            d.ellipse([fx - wdt / 2, fy - wdt / 2 * 0.7, fx + wdt / 2, fy + wdt / 2 * 0.7], fill=col)
    for k in range(3):
        d.rectangle([top[0] - 2 + k * 2, top[1] + 1, top[0] - 1 + k * 2, top[1] + 2], fill=tuple(int(v) for v in ramp("dirt", 1)) + (255,))
    c = np.array(img)
    c[..., 3] = np.where(c[..., 3] > 127, 255, 0)
    _outline(c, "palm_frond")
    return c


def sprite_jungle(variant: int) -> np.ndarray:
    c = np.zeros((CELL_H, CELL_W, 4), dtype=np.uint8)
    rs = np.random.RandomState(200 + variant)
    shade = np.zeros((CELL_H, CELL_W), dtype=bool)
    img = Image.fromarray(c, "RGBA")
    d = ImageDraw.Draw(img)
    trunk = tuple(int(v) for v in ramp("wood", 1)) + (255,)
    d.rectangle([PIVOT[0] - 2, PIVOT[1] - 8, PIVOT[0] + 1, PIVOT[1]], fill=trunk)
    d.line([PIVOT[0] - 2, PIVOT[1] - 8, PIVOT[0] - 2, PIVOT[1]], fill=tuple(int(v) for v in ramp("wood", 2)) + (255,))
    c = np.array(img)
    blobs = [(24, 29, 15, 14), (14, 35, 10, 9), (34, 35, 10, 9), (22, 19, 10, 9), (31, 22, 8, 8)] if variant == 0 else \
            [(24, 31, 14, 15), (13, 37, 9, 8), (35, 38, 9, 8), (26, 18, 9, 9), (16, 24, 8, 8)]
    layer = np.zeros_like(c)
    for cx, cy, rx, ry in blobs:
        _blob(layer, shade, cx, cy, rx, ry, rs, "foliage")
    # the global light: re-shade by the whole crown so the sprite reads as ONE mass
    ys, xs = np.mgrid[0:CELL_H, 0:CELL_W]
    dx, dy = (xs - 22.0) / 18.0, (ys - 29.0) / 18.0
    v = 0.5 + 0.55 * (dx * 0.55 + dy * 0.75) + (BAYER[ys % 4, xs % 4] - 0.5) * 0.30
    step = np.clip(np.floor((1.0 - v) * 4.6 + 0.2).astype(int), 0, 4)
    cols = np.stack([np.append(ramp("foliage", s), 255) for s in range(5)])
    shaded = cols[np.clip(4 - step, 0, 4)]
    leaf = layer[..., 3] > 0
    c[leaf] = shaded[leaf]
    # a few lighter leaf clusters on the lit side
    sp = rs.rand(CELL_H, CELL_W)
    c[leaf & (sp > 0.93) & (xs < 26) & (ys < 24)] = np.append(ramp("foliage", 4), 255)
    _outline(c, "foliage")
    return c


def sprite_bush() -> np.ndarray:
    c = np.zeros((CELL_H, CELL_W, 4), dtype=np.uint8)
    rs = np.random.RandomState(300)
    shade = np.zeros((CELL_H, CELL_W), dtype=bool)
    for cx, cy, rx, ry in ((20, 46, 8, 5), (28, 47, 8, 5), (24, 43, 7, 5)):
        _blob(c, shade, cx, cy, rx, ry, rs, "grass")
    _outline(c, "foliage")
    return c


def sprite_rock(variant: int) -> np.ndarray:
    c = np.zeros((CELL_H, CELL_W, 4), dtype=np.uint8)
    img = Image.fromarray(c, "RGBA")
    d = ImageDraw.Draw(img)
    pts = [(12, 51), (14, 42), (21, 36), (31, 37), (37, 45), (36, 52)] if variant == 0 else [(14, 51), (17, 44), (24, 40), (33, 43), (35, 51)]
    d.polygon(pts, fill=tuple(int(v) for v in ramp("stone_warm", 2)) + (255,))
    # lit facet (north-west) and shadow facet (south-east)
    d.polygon([pts[1], pts[2], pts[3], (26, 46), (18, 48)], fill=tuple(int(v) for v in ramp("stone_warm", 3)) + (255,))
    d.polygon([pts[-2], pts[-1], (26, 52), (30, 47), pts[-3]], fill=tuple(int(v) for v in ramp("stone_warm", 1)) + (255,))
    d.line([pts[2], (22, 41), (27, 40)], fill=tuple(int(v) for v in ramp("stone_warm", 4)) + (255,))
    c = np.array(img)
    c[..., 3] = np.where(c[..., 3] > 127, 255, 0)
    _outline(c, "stone_warm")
    return c


def build_atlas() -> Image.Image:
    cells = [sprite_palm(0), sprite_palm(1), sprite_jungle(0), sprite_jungle(1), sprite_bush(), sprite_rock(0), sprite_rock(1)]
    atlas = Image.new("RGBA", (CELL_W * ATLAS_COLS, CELL_H * ATLAS_ROWS), (0, 0, 0, 0))
    for i, cell in enumerate(cells):
        atlas.paste(Image.fromarray(cell, "RGBA"), ((i % ATLAS_COLS) * CELL_W, (i // ATLAS_COLS) * CELL_H))
    return atlas


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    h, land_field, _ = build_terrain()
    n = normals(h)
    slope = np.sqrt(np.maximum(1.0 - n[..., 1] ** 2, 0)) / np.maximum(n[..., 1], 1e-3)
    rs = np.random.RandomState(7)
    trees = place_trees(h, slope, rs)
    ground = bake_ground(h, land_field, n, np.random.RandomState(11))
    data = data_image(h, trees, land_field)
    nrm = np.zeros((PX, PX, 4), dtype=np.uint8)
    nrm[..., :3] = np.clip((n * 0.5 + 0.5) * 255.0 + 0.5, 0, 255).astype(np.uint8)
    nrm[..., 3] = 255
    out = ROOT / "game/h2d/art"
    out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(ground, "RGBA").save(out / "island_anvil_albedo.png", optimize=True)
    Image.fromarray(data, "RGBA").save(out / "island_anvil_data.png", optimize=True)
    Image.fromarray(nrm, "RGBA").save(out / "island_anvil_normal.png", optimize=True)
    atlas = build_atlas()
    atlas.save(out / "trees_atlas.png", optimize=True)
    land = h > 0.02
    meta = {
        "id": "isl_h2d0_anvil_cay", "name": "Anvil Cay (H2D-0 demo island, not a registry island)", "size_m": SIZE_M, "px": PX, "px_per_m": PPM,
        "height_min_m": H_MIN, "height_max_m": H_MAX, "sea_level_m": 0.0,
        "land_area_m2": round(float(land.sum() / PPM / PPM), 1), "peak_m": round(float(h.max()), 2),
        "atlas": {"file": "trees_atlas.png", "cell_px": [CELL_W, CELL_H], "pivot_px": list(PIVOT), "cols": ATLAS_COLS, "rows": ATLAS_ROWS,
                  "types": ["palm_a", "palm_b", "jungle_a", "jungle_b", "bush", "rock_a", "rock_b"]},
        "files": {"albedo": "island_anvil_albedo.png", "data": "island_anvil_data.png", "normal": "island_anvil_normal.png"},
        "data_channels": "R height (0..255 -> -8..40 m), G height with tree canopies (shadow caster), B metres from shore /40 (water side)",
        "trees": trees,
    }
    (out / "island_anvil.json").write_text(json.dumps(meta, indent=1) + "\n")
    print(f"island: land {meta['land_area_m2']} m2, peak {meta['peak_m']} m, trees {len(trees)}")
    if args.preview:
        pv = ROOT / "art_bible/h2d0"
        pv.mkdir(parents=True, exist_ok=True)
        lam = np.clip(n @ LIGHT, 0, 1)
        sea = np.zeros((PX, PX, 3))
        depth = np.clip(-h / 6.0, 0, 1)[..., None]
        sea[:] = ramp("sea_deep", 3) * (1 - depth) * 0.0 + (ramp("lagoon", 2) * (1 - depth) + ramp("sea_deep", 2) * depth)
        shade = (0.45 + 0.75 * lam)[..., None]
        land_rgb = ground[..., :3].astype(float) * shade
        base = np.where((ground[..., 3] > 0)[..., None], land_rgb, sea)
        im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
        for t in sorted(trees, key=lambda q: q["z_m"]):
            cell = atlas.crop(((t["type"] % ATLAS_COLS) * CELL_W, (t["type"] // ATLAS_COLS) * CELL_H, (t["type"] % ATLAS_COLS + 1) * CELL_W, (t["type"] // ATLAS_COLS + 1) * CELL_H))
            x = (t["x_m"] + SIZE_M / 2) * PPM - PIVOT[0]
            y = (t["z_m"] + SIZE_M / 2) * PPM - PIVOT[1] - t["y_m"] * PPM * math.cos(math.radians(48))
            im.alpha_composite(cell, (int(x), int(y))) if 0 <= x < PX - CELL_W and 0 <= y < PX - CELL_H else None
        im.save(pv / "island_preview.png")
        atlas.resize((atlas.width * 4, atlas.height * 4), Image.NEAREST).save(pv / "trees_sheet.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
