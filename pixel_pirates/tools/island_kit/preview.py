"""Preview renderer for baked island maps (Module A6): one PNG per island, and a size-true contact sheet."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
PAL = json.loads((ROOT / "game" / "data" / "look" / "palette.json").read_text())["ramps"]


def _c(ramp: str, i: int) -> np.ndarray:
    h = PAL[ramp][i].lstrip("#")
    return np.array([int(h[k:k + 2], 16) for k in (0, 2, 4)], dtype=float)


BASE = {"~": _c("sea_deep", 1), "-": _c("lagoon", 2), ".": _c("sand", 3), "g": _c("grass", 3), "u": _c("foliage", 2),
        "r": _c("stone_cool", 2), "#": _c("stone_warm", 1)}
POI_COL = {"survival": (80, 220, 120), "hook": (255, 90, 90), "secret": (200, 120, 255), "story": (255, 220, 60), "camp": (255, 150, 60)}


def render(m: dict, px: int = 3, overlays: bool = True) -> Image.Image:
    n = m["size"][0]
    t = m["terrain"]
    img = np.zeros((n, n, 3))
    for y, row in enumerate(t):
        for x, ch in enumerate(row):
            img[y, x] = BASE[ch]
    el = np.array([[int(c, 16) for c in r] for r in m["elev"]], dtype=float)
    land = np.array([[c not in "~-" for c in r] for r in t])
    img = np.where(land[..., None], np.clip(img * (0.78 + 0.035 * el[..., None]), 0, 255), img)
    im = Image.fromarray(img.astype(np.uint8)).resize((n * px, n * px), Image.NEAREST)
    if not overlays:
        return im
    d = ImageDraw.Draw(im)
    for poly in m["trails"]:
        pts = [(x * px + px // 2, y * px + px // 2) for x, y in poly]
        d.line(pts, fill=(150, 105, 60), width=max(1, px // 2))
    for x, y, i in m["props"]:
        d.point((x * px + px // 2, y * px + px // 2), fill=(20, 60, 30))
    for L in m["landings"]:
        x, y = L["x"] * px + px // 2, L["y"] * px + px // 2
        d.polygon([(x, y - px * 2), (x - px * 2, y + px * 2), (x + px * 2, y + px * 2)], fill=(255, 255, 255), outline=(0, 0, 0))
    for q in m["pois"]:
        x, y = q["x"] * px + px // 2, q["y"] * px + px // 2
        d.ellipse([x - px * 2, y - px * 2, x + px * 2, y + px * 2], fill=POI_COL[q["kind"]], outline=(0, 0, 0))
    return im


def contact_sheet(maps: list[dict], cols: int = 5, cell: int = 250, px: float = 1.25) -> Image.Image:
    rows = (len(maps) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + 16)), (24, 30, 38))
    d = ImageDraw.Draw(sheet)
    for i, m in enumerate(maps):
        im = render(m, 1, overlays=False)
        s = int(m["size"][0] * px)
        im = im.resize((s, s), Image.NEAREST)
        cx, cy = (i % cols) * cell, (i // cols) * (cell + 16)
        sheet.paste(im, (cx + (cell - s) // 2, cy + (cell - s) // 2))
        d.text((cx + 4, cy + cell), f"{m['island']} {m['template'].replace('tpl_', '')}", fill=(230, 230, 230))
    return sheet


if __name__ == "__main__":
    import sys
    for f in sys.argv[2:]:
        render(json.loads(Path(f).read_text()), int(sys.argv[1])).save(Path(f).with_suffix(".png"))
