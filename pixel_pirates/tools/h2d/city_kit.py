"""CP-1 revision: the drawing kit for the capital's buildings (14.4 px per metre, like the pirate).

Everything is drawn with numpy from the project palette (game/data/look/palette.json). `shift` moves pixels along their own
colour ramp (so shading never leaves the palette); `wall`, `roof`, `window`, `door` ... are the parts the building recipes in
city_art.py are made of. Light comes from the upper left: left edges are lifted, right edges and eave shadows are lowered.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bake_harbor as BH  # noqa: E402
import bake_island as BI  # noqa: E402
import port_sprites as PS  # noqa: E402

col = BH.col
rect, px, line, disc = PS.rect, PS.px, PS.line, PS.disc
PPM = 14.4

# colour -> (ramp name, index), to shade inside the palette
_IDX: dict[tuple, tuple] = {}
for _name in ("sand", "dirt", "stone_warm", "stone_cool", "wood", "hull_oak", "grass", "foliage", "roof_teal", "cloth_red", "cloth_blue",
              "cloth_cream", "iron", "gold", "fire", "skin_light", "skin_tan", "palm_frond", "lagoon", "ice"):
    for _i in range(5):
        _IDX.setdefault(col(_name, _i), (_name, _i))


def shift(c, x0, y0, x1, y1, d):
    """Move every opaque pixel of the region `d` steps along its ramp."""
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, c.shape[1]), min(y1, c.shape[0])
    for y in range(y0, y1):
        for x in range(x0, x1):
            if c[y, x, 3] == 0:
                continue
            k = _IDX.get(tuple(int(v) for v in c[y, x]))
            if k is None:
                continue
            c[y, x] = col(k[0], min(max(k[1] + d, 0), 4))


def hsh(a, b=0, c=0):
    v = (a * 73856093) ^ (b * 19349663) ^ (c * 83492791)
    v = (v ^ (v >> 13)) * 1274126177
    return ((v ^ (v >> 16)) & 0xFFFF) / 65535.0


def canvas(w, h):
    return np.zeros((h, w, 4), np.uint8)


# ---- materials -------------------------------------------------------------------------------------------------------------
MATS = {
    "plaster": ("cloth_cream", 3), "white": ("cloth_cream", 4), "sand": ("sand", 3), "ochre": ("gold", 2), "blue": ("cloth_blue", 2),
    "rose": ("cloth_red", 3), "green": ("grass", 2), "stone": ("stone_warm", 3), "greystone": ("stone_cool", 3),
    "timber": ("wood", 2), "brick": ("cloth_red", 2), "tar": ("hull_oak", 2), "half": ("cloth_cream", 3), "halfsand": ("sand", 3),
}


def wall(c, x0, y0, x1, y1, mat, seed=1):
    """Fill a wall face with a material."""
    ramp, base = MATS[mat]
    rect(c, x0, y0, x1, y1, col(ramp, base))
    w, h = x1 - x0, y1 - y0
    if mat in ("plaster", "white", "sand", "ochre", "blue", "rose", "green", "half", "halfsand"):
        for y in range(y0, y1):
            for x in range(x0, x1):
                r = hsh(x, y, seed)
                if r < 0.035:
                    px(c, x, y, col(ramp, max(base - 1, 0)))
                elif r > 0.985:
                    px(c, x, y, col(ramp, min(base + 1, 4)))
        for k in range(0, h // 22):                       # a few stains and cracks
            sx, sy = x0 + int(hsh(seed, k, 3) * (w - 6)), y0 + int(hsh(seed, k, 4) * (h - 14))
            rect(c, sx, sy, sx + 1, sy + 3 + int(hsh(seed, k, 5) * 4), col(ramp, max(base - 1, 0)))
    elif mat == "brick":
        for r in range((h + 4) // 5):
            y = y0 + r * 5
            rect(c, x0, y + 4, x1, min(y + 5, y1), col("stone_warm", 2))
            off = 6 if r % 2 else 0
            for x in range(x0 - off, x1, 12):
                if x >= x0:
                    rect(c, x, y, x + 1, min(y + 5, y1), col("stone_warm", 2))
                v = hsh(x, r, seed)
                if v < 0.2:
                    rect(c, max(x + 1, x0), y, min(x + 11, x1), min(y + 4, y1), col("cloth_red", 1))
                elif v > 0.85:
                    rect(c, max(x + 1, x0), y, min(x + 11, x1), min(y + 1, y1), col("cloth_red", 3))
    elif mat in ("stone", "greystone"):
        r1, light, dark = ramp, base + 1, base - 1
        for r in range((h + 7) // 8):
            y = y0 + r * 8
            rect(c, x0, y + 7, x1, min(y + 8, y1), col(r1, 1))
            off = 8 if r % 2 else 0
            for x in range(x0 - off, x1, 16):
                if x >= x0:
                    rect(c, x, y, x + 1, min(y + 8, y1), col(r1, 1))
                v = hsh(x, r, seed)
                if v < 0.3:
                    rect(c, max(x + 1, x0), y, min(x + 15, x1), min(y + 7, y1), col(r1, dark))
                elif v > 0.7:
                    rect(c, max(x + 1, x0), y, min(x + 15, x1), min(y + 1, y1), col(r1, min(light, 4)))
    elif mat in ("timber", "tar"):
        r1 = ramp
        for x in range(x0, x1, 5):
            rect(c, x, y0, x + 1, y1, col(r1, 1))
            v = hsh(x, 0, seed)
            rect(c, x + 1, y0, x + 4, y1, col(r1, base + (1 if v > 0.7 else (-1 if v < 0.2 else 0))) if base < 4 else col(r1, base))
        for k in range(h // 30):
            px(c, x0 + int(hsh(seed, k, 8) * (w - 2)), y0 + int(hsh(seed, k, 9) * (h - 2)), col(r1, 0))
    if mat in ("half", "halfsand"):                       # timber framing
        beam = col("wood", 1)
        bw = max(24, w // max(w // 26, 1))
        for x in range(x0, x1 + 1, bw):
            rect(c, x - 1 if x > x0 else x, y0, (x + 1) if x < x1 else x1, y1, beam)
        rect(c, x0, y0, x1, y0 + 2, beam)
        rect(c, x0, (y0 + y1) // 2, x1, (y0 + y1) // 2 + 2, beam)
        for x in range(x0, x1 - bw + 1, bw):
            line(c, x + 1, (y0 + y1) // 2 + 2, x + bw - 1, y0 + 2, beam)
    # lighting: the left edge lifts, the right edge falls, the foot darkens
    shift(c, x0, y0, x0 + 2, y1, 1)
    shift(c, x1 - 3, y0, x1, y1, -1)
    shift(c, x0, y1 - 5, x1, y1, -1)


def window(c, x, y, w, h, lit=True, shutter=None, arch=False, frame=("wood", 1), sill=True, bars=False):
    """A window with frame, mullions, optional shutters and a glowing pane (the exact fire colours glow at night)."""
    rect(c, x - 1, y - 1, x + w + 1, y + h + 1, col(*frame))
    glass = col("fire", 3) if lit else col("stone_cool", 1)
    rect(c, x, y, x + w, y + h, glass)
    if lit:
        rect(c, x, y, x + w, y + 2, col("fire", 4))
        rect(c, x, y + h - 2, x + w, y + h, col("fire", 3))
    else:
        rect(c, x, y, x + 2, y + h, col("stone_cool", 2))
    rect(c, x + w // 2, y, x + w // 2 + 1, y + h, col(*frame))
    if h >= 12:
        rect(c, x, y + h // 2, x + w, y + h // 2 + 1, col(*frame))
    if arch:
        rect(c, x - 1, y - 3, x + w + 1, y - 1, col("stone_warm", 3))
        rect(c, x - 1, y - 3, x, y - 1, col("stone_warm", 2))
    if shutter:
        sw = max(w // 3, 3)
        for sx in (x - sw - 1, x + w + 1):
            rect(c, sx, y - 1, sx + sw, y + h + 1, col(shutter[0], shutter[1]))
            for yy in range(y + 1, y + h, 3):
                rect(c, sx, yy, sx + sw, yy + 1, col(shutter[0], max(shutter[1] - 1, 0)))
    if sill:
        rect(c, x - 2, y + h + 1, x + w + 2, y + h + 3, col("stone_warm", 3))
        rect(c, x - 2, y + h + 3, x + w + 2, y + h + 4, col("stone_warm", 1))
    if bars:
        for xx in range(x + 2, x + w, 3):
            rect(c, xx, y, xx + 1, y + h, col("iron", 1))


def door(c, x, base, w, h, color=("wood", 2), arch=True, frame="stone_warm"):
    rect(c, x - 2, base - h - 2, x + w + 2, base, col(frame, 3))
    rect(c, x - 2, base - h - 2, x - 1, base, col(frame, 4))
    rect(c, x, base - h, x + w, base, col(*color))
    for xx in range(x + 2, x + w - 1, 4):
        rect(c, xx, base - h, xx + 1, base, col(color[0], max(color[1] - 1, 0)))
    rect(c, x + w - 4, base - h // 2, x + w - 2, base - h // 2 + 2, col("gold", 3))      # handle
    if arch:
        rect(c, x, base - h, x + 2, base - h + 2, col(frame, 3))
        rect(c, x + w - 2, base - h, x + w, base - h + 2, col(frame, 3))
    rect(c, x - 3, base - 2, x + w + 3, base, col("stone_warm", 2))                       # step
    rect(c, x - 3, base - 2, x + w + 3, base - 1, col("stone_warm", 3))


# ---- roofs -----------------------------------------------------------------------------------------------------------------
ROOFS = {"red": ("cloth_red", 2), "slate": ("stone_cool", 2), "teal": ("roof_teal", 2), "brown": ("wood", 2), "dark": ("hull_oak", 3),
         "thatch": ("sand", 2), "terracotta": ("fire", 1), "greenslate": ("roof_teal", 3)}


def roof(c, x0, x1, y_eave, rh, kind="red", shape="gable", seed=3, overhang=5, tile_w=8, tile_h=5):
    """A sloped roof band above y_eave (ridge parallel to the wall). Returns the ridge y."""
    ramp, base = ROOFS[kind]
    top = y_eave - rh
    inset_max = int((x1 - x0) * 0.16) if shape == "hip" else 0
    for y in range(top, y_eave + 2):
        t = (y - top) / max(rh, 1)
        inset = int(inset_max * (1.0 - t))
        xa, xb = x0 - overhang + inset, x1 + overhang - inset
        r = (y - top) // tile_h
        if kind == "thatch":
            rect(c, xa, y, xb, y + 1, col(ramp, base + (1 if (y - top) % 4 == 0 else 0)))
            continue
        row_off = (tile_w // 2) if r % 2 else 0
        for x in range(xa, xb):
            lx = (x - xa + row_off) % tile_w
            ly = (y - top) % tile_h
            v = hsh((x - xa + row_off) // tile_w, r, seed)
            b = base + (1 if v > 0.84 else (-1 if v < 0.16 else 0))
            if lx == 0:
                cc = col(ramp, max(b - 1, 0))
            elif ly == tile_h - 1:
                cc = col(ramp, max(b - 1, 0))
            elif ly == 0:
                cc = col(ramp, min(b + 1, 4))
            else:
                cc = col(ramp, b)
            px(c, x, y, cc)
    if kind == "thatch":                                  # ragged thatch edge
        for x in range(x0 - overhang, x1 + overhang):
            n = int(hsh(x, 1, seed) * 4)
            rect(c, x, y_eave + 1, x + 1, y_eave + 2 + n, col("sand", 2 if n > 1 else 1))
        for k in range(0, (x1 - x0) // 9):
            sx = x0 + int(hsh(k, 2, seed) * (x1 - x0))
            rect(c, sx, top + 2, sx + 1, y_eave - 2, col("sand", 3))
    shift(c, x0 - overhang, top, x1 + overhang, top + 2, 1)                              # ridge catches the light
    rect(c, x0 - overhang + (inset_max if shape == "hip" else 0), y_eave + 1, x1 + overhang - (0), y_eave + 3, col("hull_oak", 1))   # eave shadow line
    shift(c, x0 - overhang, y_eave - 4, x1 + overhang, y_eave, -1)
    shift(c, x1 + overhang - 5, top, x1 + overhang, y_eave, -1)
    return top


def chimney(c, x, y_roof, h=14, w=9):
    rect(c, x, y_roof - h, x + w, y_roof + 2, col("stone_warm", 2))
    rect(c, x, y_roof - h, x + 2, y_roof + 2, col("stone_warm", 3))
    rect(c, x + w - 2, y_roof - h, x + w, y_roof + 2, col("stone_warm", 1))
    rect(c, x - 1, y_roof - h - 2, x + w + 1, y_roof - h, col("stone_warm", 4))
    rect(c, x + 2, y_roof - h - 1, x + w - 2, y_roof - h, col("iron", 1))


def dormer(c, x, y_roof_base, kind="red", lit=True):
    """A small dormer standing on the roof: wall, window, little roof."""
    rect(c, x, y_roof_base - 16, x + 18, y_roof_base, col("cloth_cream", 3))
    shift(c, x, y_roof_base - 16, x + 2, y_roof_base, 1)
    shift(c, x + 16, y_roof_base - 16, x + 18, y_roof_base, -1)
    window(c, x + 5, y_roof_base - 13, 8, 9, lit, sill=False)
    for i in range(7):
        rect(c, x - 2 + i, y_roof_base - 22 + i, x + 20 - i, y_roof_base - 21 + i, col(ROOFS[kind][0], ROOFS[kind][1] + (1 if i == 0 else 0)))


def awning_striped(c, x0, x1, y0, h, a, b, stripe=8):
    """Shop awning sloping towards the viewer, with a scalloped edge."""
    for x in range(x0, x1):
        cc = a if ((x - x0) // stripe) % 2 == 0 else b
        for y in range(y0, y0 + h):
            sh = 4 if y == y0 else (2 if y >= y0 + h - 2 else 3)
            px(c, x, y, col(cc[0], sh))
        sc = 3 if ((x - x0) % stripe) in (1, 2, 3, 4, 5, 6) else 1
        for y in range(y0 + h, y0 + h + sc):
            px(c, x, y, col(cc[0], 2))
    shift(c, x0, y0, x0 + 1, y0 + h, 1)
    rect(c, x0, y0 + h + 3, x1, y0 + h + 6, col("wood", 0)) if False else None


def hanging_sign(c, x, y, kind="anchor", w=14, h=12):
    """A board on an iron bracket: `kind` picks a tiny emblem."""
    rect(c, x - 12, y - 3, x + 1, y - 1, col("iron", 2))
    rect(c, x - 10, y - 1, x - 9, y + 2, col("iron", 1))
    rect(c, x - 1, y - 1, x, y + 2, col("iron", 1))
    rect(c, x - 12, y + 1, x + 2, y + h, col("wood", 3))
    rect(c, x - 11, y + 2, x + 1, y + h - 1, col("cloth_cream", 3))
    cx, cy = x - 5, y + h // 2 + 1
    if kind == "anchor":
        rect(c, cx, cy - 4, cx + 1, cy + 3, col("iron", 1)); rect(c, cx - 2, cy - 3, cx + 3, cy - 2, col("iron", 1))
        line(c, cx - 3, cy, cx, cy + 3, col("iron", 1)); line(c, cx + 3, cy, cx, cy + 3, col("iron", 1))
    elif kind == "fish":
        rect(c, cx - 3, cy - 1, cx + 3, cy + 2, col("cloth_blue", 3)); rect(c, cx + 3, cy - 2, cx + 5, cy + 3, col("cloth_blue", 2))
    elif kind == "loaf":
        disc(c, cx, cy, 4, 3, col("dirt", 3)); rect(c, cx - 2, cy - 1, cx + 1, cy, col("dirt", 4))
    elif kind == "barrel":
        rect(c, cx - 3, cy - 3, cx + 4, cy + 4, col("wood", 2)); rect(c, cx - 3, cy - 1, cx + 4, cy, col("iron", 2)); rect(c, cx - 3, cy + 2, cx + 4, cy + 3, col("iron", 2))
    elif kind == "cloth":
        rect(c, cx - 3, cy - 3, cx + 4, cy + 4, col("cloth_red", 3)); rect(c, cx - 3, cy, cx + 4, cy + 1, col("gold", 3))
    elif kind == "mug":
        rect(c, cx - 2, cy - 3, cx + 3, cy + 3, col("gold", 3)); rect(c, cx - 2, cy - 3, cx + 3, cy - 1, col("cloth_cream", 4)); rect(c, cx + 3, cy - 1, cx + 5, cy + 2, col("gold", 2))
    elif kind == "key":
        disc(c, cx - 1, cy - 2, 2, 2, col("gold", 3)); rect(c, cx - 1, cy, cx, cy + 4, col("gold", 3)); rect(c, cx, cy + 2, cx + 2, cy + 3, col("gold", 3))
    elif kind == "scales":
        rect(c, cx, cy - 4, cx + 1, cy + 3, col("iron", 1)); rect(c, cx - 4, cy - 3, cx + 5, cy - 2, col("iron", 1))
        rect(c, cx - 4, cy, cx - 1, cy + 1, col("gold", 3)); rect(c, cx + 2, cy, cx + 5, cy + 1, col("gold", 3))
    elif kind == "hammer":
        rect(c, cx, cy - 3, cx + 1, cy + 4, col("wood", 2)); rect(c, cx - 3, cy - 4, cx + 4, cy - 1, col("iron", 2))
    elif kind == "rope":
        for i in range(6):
            rect(c, cx - 3 + i, cy - 3 + (i % 2), cx - 2 + i, cy + 1 + (i % 2), col("sand", 3))
    elif kind == "sail":
        for i in range(7):
            rect(c, cx - 3, cy - 3 + i, cx - 3 + max(7 - i, 1), cy - 2 + i, col("cloth_cream", 4))
        rect(c, cx - 3, cy - 4, cx - 2, cy + 4, col("wood", 2))


def balcony(c, x0, x1, y, depth=6):
    rect(c, x0, y, x1, y + 3, col("wood", 3))
    rect(c, x0, y + 3, x1, y + 4, col("wood", 1))
    for x in range(x0 + 1, x1, 5):
        rect(c, x, y - 8, x + 1, y, col("wood", 2))
    rect(c, x0, y - 9, x1, y - 7, col("wood", 3))


def lantern(c, x, y):
    rect(c, x, y - 4, x + 1, y, col("iron", 1))
    rect(c, x - 1, y, x + 3, y + 5, col("iron", 1))
    rect(c, x, y + 1, x + 2, y + 4, col("fire", 3))


def flag(c, x, y, h=22, w=14, a=("cloth_red", 3), b=None):
    rect(c, x, y, x + 1, y + h, col("wood", 2))
    for i in range(w):
        yy = y + 1 + int(1.5 * np.sin(i * 0.5))
        rect(c, x + 1 + i, yy, x + 2 + i, yy + 8, col(a[0], a[1] if i < w - 1 else a[1] - 1))
        if b:
            rect(c, x + 1 + i, yy + 3, x + 2 + i, yy + 5, col(b[0], b[1]))
    rect(c, x - 1, y - 2, x + 2, y, col("gold", 3))


def finish(c):
    c[..., 3] = np.where(c[..., 3] > 127, 255, 0)
    BI._outline(c, "iron")
    return c
