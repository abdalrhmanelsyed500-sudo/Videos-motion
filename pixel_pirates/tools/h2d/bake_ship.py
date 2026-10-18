"""Bakes the layered pixel-art sloop sprites from the 3D reference model (Module H2D-0, decision D2).

  python tools/h2d/bake_ship.py            # writes game/h2d/art/ship_sloop_hull.png, ship_sloop_sails.png, ship_sloop.json
  python tools/h2d/bake_ship.py --preview  # also writes art_bible/h2d0/ship_*.png (contact sheets, trim study, turn strip)

Method: orthographic camera at the sea pitch (48 deg, A3), north-up and fixed; the model is yawed to each of 16 headings;
flat shading with a FIXED north-west key light and the master palette's ramps (the game re-tints with the sun at run time);
4x supersampling, majority-vote downsample (no blended colours), 1 px inside outline. Layers: hull (everything that does not
move) and sails (boom, gaff, sails, jib, pennant) at 5 trim angles, so the sails can be eased without re-baking the ship.
Deterministic: same input, same bytes.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ship_model  # noqa: E402
from ship_sprite_logic import HEADINGS, TRIMS_DEG, heading_frame, trim_row  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PITCH_DEG = 48.0
PPM = 3.6  # pixels per metre at the art grid
SS = 4
FW, FH = 112, 112
PIVOT = (56, 66)  # the pixel that sits on the water line at the ship's position
LIGHT = np.array([-0.5, 0.95, -0.6])
LIGHT = LIGHT / np.linalg.norm(LIGHT)

PALETTE = json.loads((ROOT / "game/data/look/palette.json").read_text())["ramps"]
# part -> (ramp, step shift, fixed step or None, outline colour or None)
PARTS = {
    "hull_side": ("hull_oak", 0, None, "#1c0f0a"),
    "wale": ("cloth_red", 0, None, "#3d0f14"),
    "rail": ("wood", 1, None, "#2b160d"),
    "hull_inner": ("hull_oak", -1, None, "#1c0f0a"),
    "deck": ("wood", 0, None, "#2b160d"),
    "cabin": ("wood", -1, None, "#2b160d"),
    "roof": ("hull_oak", 1, None, "#1c0f0a"),
    "window": ("iron", 0, 0, None),
    "cannon": ("iron", 0, None, "#1a1c24"),
    "barrel": ("dirt", 0, None, "#2e1d12"),
    "mast": ("wood", 0, None, "#2b160d"),
    "rope": ("wood", 0, 1, None),
    "sail": ("cloth_cream", 1, None, "#5a4d3f"),
    "sail_band": ("cloth_red", 1, None, "#3d0f14"),
    "flag": ("cloth_red", 1, None, "#3d0f14"),
}
PART_NAMES = list(PARTS)


def hex_rgb(h: str) -> tuple[int, int, int]:
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def project(pts: np.ndarray, heading_deg: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Local (x, y, z) points -> (sx, sy, depth) in metres. sy is up the screen, depth larger = closer to the camera."""
    h = math.radians(heading_deg)
    f = np.array([math.sin(h), 0.0, -math.cos(h)])
    r = np.array([math.cos(h), 0.0, math.sin(h)])
    w = pts[:, 0:1] * f + pts[:, 1:2] * np.array([0.0, 1.0, 0.0]) + pts[:, 2:3] * r
    p = math.radians(PITCH_DEG)
    sx = w[:, 0]
    sy = w[:, 1] * math.cos(p) - w[:, 2] * math.sin(p)
    depth = w[:, 1] * math.sin(p) + w[:, 2] * math.cos(p)
    return sx, sy, depth


def world_normal(tri_v: np.ndarray, heading_deg: float) -> np.ndarray:
    h = math.radians(heading_deg)
    f = np.array([math.sin(h), 0.0, -math.cos(h)])
    r = np.array([math.cos(h), 0.0, math.sin(h)])
    n = np.cross(tri_v[1] - tri_v[0], tri_v[2] - tri_v[0])
    n = n / (np.linalg.norm(n) or 1.0)
    w = n[0] * f + n[1] * np.array([0.0, 1.0, 0.0]) + n[2] * r
    p = math.radians(PITCH_DEG)
    to_cam = np.array([0.0, math.sin(p), math.cos(p)])
    return w if np.dot(w, to_cam) >= 0 else -w


def lambert_step(n_world: np.ndarray) -> int:
    v = 0.3 + 0.7 * max(0.0, float(np.dot(n_world, LIGHT)))
    return 1 + int(v > 0.45) + int(v > 0.62) + int(v > 0.80)


def raster(tris: list[dict], heading_deg: float, out_layer: str | None) -> np.ndarray:
    """Return int16 key buffer (H*SS, W*SS): part_index*8 + step, or -1 where no pixel of `out_layer` is the front-most."""
    gw, gh = FW * SS, FH * SS
    zbuf = np.full((gh, gw), -1e9, dtype=np.float32)
    owner = np.full((gh, gw), -1, dtype=np.int32)
    attr = np.zeros((gh, gw, 5), dtype=np.float32)  # local x, y, z, u, v of the front-most surface point
    info = []
    for ti, t in enumerate(tris):
        v = np.array(t["v"], dtype=np.float64)
        sx, sy, dp = project(v, heading_deg)
        px = PIVOT[0] * SS + sx * PPM * SS
        py = PIVOT[1] * SS - sy * PPM * SS
        n = world_normal(v, heading_deg)
        info.append((t["part"], lambert_step(n), t["layer"]))
        x0, x1 = int(max(0, math.floor(px.min()))), int(min(gw - 1, math.ceil(px.max())))
        y0, y1 = int(max(0, math.floor(py.min()))), int(min(gh - 1, math.ceil(py.max())))
        if x1 < x0 or y1 < y0:
            continue
        den = (py[1] - py[2]) * (px[0] - px[2]) + (px[2] - px[1]) * (py[0] - py[2])
        if abs(den) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((py[1] - py[2]) * (gx - px[2]) + (px[2] - px[1]) * (gy - py[2])) / den
        w1 = ((py[2] - py[0]) * (gx - px[2]) + (px[0] - px[2]) * (gy - py[2])) / den
        w2 = 1.0 - w0 - w1
        eps = -1e-4
        inside = (w0 >= eps) & (w1 >= eps) & (w2 >= eps)
        if not inside.any():
            continue
        z = w0 * dp[0] + w1 * dp[1] + w2 * dp[2]
        sl_z = zbuf[y0:y1 + 1, x0:x1 + 1]
        win = inside & (z > sl_z + 1e-5)
        if not win.any():
            continue
        sl_z[win] = z[win]
        owner[y0:y1 + 1, x0:x1 + 1][win] = ti
        for k in range(3):
            a = w0 * v[0][k] + w1 * v[1][k] + w2 * v[2][k]
            attr[y0:y1 + 1, x0:x1 + 1, k][win] = a[win]
        uv = t["uv"]
        attr[y0:y1 + 1, x0:x1 + 1, 3][win] = (w0 * uv[0][0] + w1 * uv[1][0] + w2 * uv[2][0])[win]
        attr[y0:y1 + 1, x0:x1 + 1, 4][win] = (w0 * uv[0][1] + w1 * uv[1][1] + w2 * uv[2][1])[win]
    keys = np.full((gh, gw), -1, dtype=np.int16)
    tri_part = np.array([PART_NAMES.index(i[0]) for i in info], dtype=np.int16)
    tri_step = np.array([i[1] for i in info], dtype=np.int16)
    tri_layer = np.array([1 if i[2] == "sail" else 0 for i in info], dtype=np.int16)
    have = owner >= 0
    own = np.where(have, owner, 0)
    part = tri_part[own]
    step = tri_step[own].copy()
    lx, ly, lz, u, vv = (attr[..., k] for k in range(5))
    # surface patterns (all derived from the 3D position, so they turn with the hull)
    hs = part == PART_NAMES.index("hull_side")
    step = np.where(hs & (np.floor(ly / 0.8).astype(np.int32) % 2 == 1), step - 1, step)
    dk = part == PART_NAMES.index("deck")
    step = np.where(dk & ((lz / 1.1) % 1.0 < 0.14), step - 1, step)
    sl = part == PART_NAMES.index("sail")
    step = np.where(sl & ((u * 6.0) % 1.0 < 0.07), step - 1, step)
    step = np.clip(step, 0, 4)
    for name, (ramp, shift, fixed, _o) in PARTS.items():
        m = part == PART_NAMES.index(name)
        if fixed is not None:
            step = np.where(m, fixed, step)
        elif shift:
            step = np.where(m, np.clip(step + shift, 0, 4), step)
    keys = np.where(have, part * 8 + step, -1).astype(np.int16)
    if out_layer == "hull":
        keys = np.where(have & (tri_layer[own] == 0), keys, -1).astype(np.int16)
    elif out_layer == "sail":
        keys = np.where(have & (tri_layer[own] == 1), keys, -1).astype(np.int16)
    return keys


def downsample(keys: np.ndarray) -> np.ndarray:
    """Majority vote per output pixel; -1 (empty) wins only when at least 10 of the 16 samples are empty."""
    blk = keys.reshape(FH, SS, FW, SS).transpose(0, 2, 1, 3).reshape(FH, FW, SS * SS)
    empty = (blk < 0).sum(-1)
    out = np.full((FH, FW), -1, dtype=np.int16)
    best = np.zeros((FH, FW), dtype=np.int32)
    for k in np.unique(blk[blk >= 0]):
        cnt = (blk == k).sum(-1)
        better = cnt > best
        out = np.where(better, k, out)
        best = np.where(better, cnt, best)
    return np.where(empty >= 10, -1, out).astype(np.int16)


def colourise(keys: np.ndarray) -> np.ndarray:
    img = np.zeros((FH, FW, 4), dtype=np.uint8)
    solid = keys >= 0
    for k in np.unique(keys[solid]):
        name = PART_NAMES[int(k) // 8]
        step = int(k) % 8
        ramp = PALETTE[PARTS[name][0]]
        r, g, b = hex_rgb(ramp[step])
        img[keys == k] = (r, g, b, 255)
    # inside outline: opaque pixels with a transparent 4-neighbour take the part's outline colour
    pad = np.pad(solid, 1, constant_values=False)
    edge = solid & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    for name, (_r, _s, _f, outline) in PARTS.items():
        if outline is None:
            continue
        m = edge & ((keys // 8) == PART_NAMES.index(name))
        if m.any():
            r, g, b = hex_rgb(outline)
            img[m] = (r, g, b, 255)
    return img


def render_frame(trim_deg: float, heading_deg: float, layer: str) -> np.ndarray:
    tris = ship_model.build(trim_deg)
    return colourise(downsample(raster(tris, heading_deg, layer)))


def bake() -> tuple[Image.Image, Image.Image, dict]:
    hull = Image.new("RGBA", (FW * HEADINGS, FH), (0, 0, 0, 0))
    sails = Image.new("RGBA", (FW * HEADINGS, FH * len(TRIMS_DEG)), (0, 0, 0, 0))
    hull_tris = ship_model.build(0.0)
    for k in range(HEADINGS):
        h = k * 360.0 / HEADINGS
        keys = downsample(raster(hull_tris, h, "hull"))
        hull.paste(Image.fromarray(colourise(keys), "RGBA"), (k * FW, 0))
        for row, trim in enumerate(TRIMS_DEG):
            tris = ship_model.build(float(trim))
            keys = downsample(raster(tris, h, "sail"))
            sails.paste(Image.fromarray(colourise(keys), "RGBA"), (k * FW, row * FH))
    cols = set()
    for im in (hull, sails):
        a = np.array(im)
        cols |= {tuple(c) for c in a[a[..., 3] > 0][:, :3]}
    meta = {
        "id": "shp_sloop_h2d", "frame_px": [FW, FH], "pivot_px": list(PIVOT), "px_per_m": PPM, "pitch_deg": PITCH_DEG,
        "headings": HEADINGS, "heading_step_deg": 360.0 / HEADINGS, "trims_deg": list(TRIMS_DEG),
        "hull_sheet": "ship_sloop_hull.png", "sail_sheet": "ship_sloop_sails.png",
        "key_light_world": [float(x) for x in LIGHT], "colour_count": len(cols),
        "ramps_used": sorted({v[0] for v in PARTS.values()}),
        "_doc": "Frame k = heading k*22.5 deg clockwise from north. Sheets are 16 columns; the sail sheet has 5 rows (trims_deg). "
                "Composite: sail pixel if opaque, else hull pixel. Baked light comes from the north-west.",
    }
    return hull, sails, meta


def composite(hull: Image.Image, sails: Image.Image, heading_k: int, row: int) -> Image.Image:
    h = hull.crop((heading_k * FW, 0, (heading_k + 1) * FW, FH))
    s = sails.crop((heading_k * FW, row * FH, (heading_k + 1) * FW, (row + 1) * FH))
    out = h.copy()
    out.alpha_composite(s)
    return out


def sea_bg(w: int, h: int) -> Image.Image:
    img = Image.new("RGBA", (w, h))
    px = img.load()
    base = [hex_rgb(c) for c in PALETTE["sea_deep"]]
    for y in range(h):
        for x in range(w):
            wv = (math.sin(x * 0.21 + y * 0.9) + math.sin(x * 0.07 - y * 0.5)) * 0.5
            i = 2 if wv < 0.55 else 3
            px[x, y] = base[i] + (255,)
    return img


def previews(hull: Image.Image, sails: Image.Image, wind_from: float, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    zoom = 3
    cols = 8
    rows = 2
    sheet = sea_bg(cols * FW, rows * FH)
    for k in range(HEADINGS):
        row = trim_row(k * 22.5, wind_from)
        frame = composite(hull, sails, k, row)
        sheet.alpha_composite(frame, ((k % cols) * FW, (k // cols) * FH))
    sheet.resize((sheet.width * zoom // 2, sheet.height * zoom // 2), Image.NEAREST).save(out_dir / "ship_headings_sheet.png")
    # trim study: heading east, all five trims
    study = sea_bg(5 * FW, FH)
    for r in range(5):
        study.alpha_composite(composite(hull, sails, 4, r), (r * FW, 0))
    study.resize((study.width * zoom, study.height * zoom), Image.NEAREST).save(out_dir / "ship_trim_study.png")
    # turn strip: what steering looks like frame by frame (every heading, bow sweeping north -> east -> south -> west)
    strip = sea_bg(HEADINGS * 56, 48)
    for k in range(HEADINGS):
        small = composite(hull, sails, k, trim_row(k * 22.5, wind_from)).crop((14, 6, 98, 84))
        small = small.resize((56, 52), Image.NEAREST)
        strip.alpha_composite(small, (k * 56, -2))
    strip.resize((strip.width * 2, strip.height * 2), Image.NEAREST).save(out_dir / "ship_turn_strip.png")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--wind-from", type=float, default=270.0, help="preview wind direction (from), degrees")
    args = ap.parse_args()
    hull, sails, meta = bake()
    out = ROOT / "game/h2d/art"
    out.mkdir(parents=True, exist_ok=True)
    hull.save(out / "ship_sloop_hull.png", optimize=True)
    sails.save(out / "ship_sloop_sails.png", optimize=True)
    (out / "ship_sloop.json").write_text(json.dumps(meta, indent=1) + "\n")
    print(f"baked: {meta['colour_count']} colours, hull {hull.size}, sails {sails.size}")
    if args.preview:
        previews(hull, sails, args.wind_from, ROOT / "art_bible/h2d0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
