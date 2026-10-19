"""CP-1 revision: dialogue portraits. 16 busts of 48 x 48 px (shown at x4 with nearest filtering), drawn procedurally from a face
description: skin, hair, beard, hat, coat, marks. Output: game/ui/portraits_atlas.png (4 x 4 cells) and art_bible/cp1/portraits.png.
Every portrait is a man (Canon rule 1) and nothing religious is drawn (rule 3).

    python tools/h2d/port_portraits.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
CELL = 48
COLS = 4

ORDER = ["pip", "tuck", "silas", "garrick", "fishmonger", "fisher", "merchant", "docker", "sailor", "shopkeeper", "townsman", "guard",
         "noble", "tavernkeeper", "clerk", "captain"]

SKIN = {"fair": (236, 196, 158), "tan": (214, 160, 112), "brown": (160, 108, 72), "dark": (112, 72, 50), "ruddy": (222, 152, 120), "olive": (200, 156, 112)}


def sh(c, f):
    return tuple(int(max(0, min(255, v * f))) for v in c)


# description: bg, skin, hair, hairstyle, beard, beard color, hat, hat color, coat, coat2 (trim), brow thickness, mark list, mouth, age, eye color
P = {
    "pip": dict(bg=(52, 84, 110), skin="fair", hair=(184, 108, 54), style="messy", beard=None, hat="cap", hatc=(118, 82, 56), coat=(70, 96, 128), trim=(210, 190, 140),
                marks=["freckles"], mouth="grin", age=0, eyes=(60, 110, 60), wide=0, extra="spyglass"),
    "tuck": dict(bg=(60, 78, 70), skin="tan", hair=(54, 40, 32), style="short", beard="stubble", beardc=(60, 46, 38), hat="bandana", hatc=(150, 52, 44), coat=(118, 100, 70), trim=(86, 70, 48),
                 marks=["scar_cheek"], mouth="flat", age=1, eyes=(60, 50, 40), wide=1, extra=None),
    "silas": dict(bg=(88, 64, 44), skin="brown", hair=(220, 220, 214), style="bald_sides", beard="mustache", beardc=(224, 224, 218), hat="cook", hatc=(236, 232, 220), coat=(236, 232, 220), trim=(180, 60, 50),
                  marks=["wrinkles"], mouth="smile", age=2, eyes=(50, 40, 30), wide=2, extra=None),
    "garrick": dict(bg=(70, 60, 58), skin="ruddy", hair=(112, 72, 40), style="short", beard="full", beardc=(120, 76, 42), hat=None, hatc=(0, 0, 0), coat=(112, 82, 52), trim=(60, 44, 32),
                    marks=["sawdust"], mouth="flat", age=1, eyes=(70, 90, 110), wide=2, extra="pencil"),
    "fishmonger": dict(bg=(150, 70, 58), skin="ruddy", hair=(90, 60, 40), style="balding", beard="mustache", beardc=(90, 60, 40), hat="straw", hatc=(214, 184, 112), coat=(236, 232, 216), trim=(70, 100, 150),
                       marks=["apron"], mouth="grin", age=1, eyes=(70, 60, 50), wide=3, extra=None),
    "fisher": dict(bg=(56, 90, 106), skin="tan", hair=(140, 138, 134), style="short", beard="full", beardc=(160, 158, 152), hat="knit", hatc=(70, 86, 120), coat=(60, 82, 104), trim=(40, 56, 74),
                   marks=["wrinkles"], mouth="flat", age=2, eyes=(60, 80, 100), wide=1, extra=None),
    "merchant": dict(bg=(104, 70, 40), skin="olive", hair=(36, 28, 26), style="slick", beard="goatee", beardc=(36, 28, 26), hat="tall", hatc=(48, 40, 52), coat=(120, 40, 56), trim=(230, 190, 80),
                     marks=["ring"], mouth="smile", age=1, eyes=(50, 36, 28), wide=0, extra="collar"),
    "docker": dict(bg=(80, 80, 84), skin="brown", hair=(30, 24, 22), style="buzz", beard="stubble", beardc=(40, 32, 28), hat="cap", hatc=(90, 88, 96), coat=(128, 110, 82), trim=(88, 72, 52),
                   marks=["scar_brow"], mouth="flat", age=1, eyes=(40, 30, 24), wide=3, extra=None),
    "sailor": dict(bg=(48, 100, 120), skin="tan", hair=(210, 170, 90), style="long", beard="stubble", beardc=(190, 150, 80), hat="bandana", hatc=(220, 220, 214), coat=(224, 224, 216), trim=(50, 76, 140),
                   marks=["earring"], mouth="grin", age=0, eyes=(50, 120, 150), wide=1, extra="stripes"),
    "shopkeeper": dict(bg=(124, 96, 60), skin="fair", hair=(80, 54, 40), style="parted", beard=None, hat=None, hatc=(0, 0, 0), coat=(96, 120, 84), trim=(214, 190, 130),
                       marks=["spectacles"], mouth="smile", age=1, eyes=(80, 70, 60), wide=0, extra="apron"),
    "townsman": dict(bg=(94, 104, 88), skin="olive", hair=(70, 54, 44), style="short", beard="sideburns", beardc=(70, 54, 44), hat="flat", hatc=(88, 72, 56), coat=(136, 96, 64), trim=(190, 160, 110),
                     marks=[], mouth="flat", age=1, eyes=(64, 50, 40), wide=1, extra=None),
    "guard": dict(bg=(56, 66, 100), skin="tan", hair=(50, 40, 34), style="short", beard="mustache", beardc=(50, 40, 34), hat="helmet", hatc=(150, 156, 164), coat=(48, 70, 130), trim=(220, 200, 90),
                  marks=["strap"], mouth="stern", age=1, eyes=(40, 40, 40), wide=2, extra="buttons"),
    "noble": dict(bg=(96, 54, 92), skin="fair", hair=(236, 232, 224), style="wig", beard="none", hat=None, hatc=(0, 0, 0), coat=(112, 50, 120), trim=(236, 200, 90),
                  marks=["beauty"], mouth="smirk", age=1, eyes=(60, 90, 140), wide=0, extra="cravat"),
    "tavernkeeper": dict(bg=(120, 70, 36), skin="ruddy", hair=(168, 104, 48), style="curly", beard="full", beardc=(176, 108, 50), hat=None, hatc=(0, 0, 0), coat=(236, 232, 214), trim=(130, 90, 56),
                         marks=["rosy"], mouth="grin", age=1, eyes=(60, 100, 60), wide=3, extra="towel"),
    "clerk": dict(bg=(74, 86, 76), skin="fair", hair=(60, 52, 48), style="parted", beard=None, hat="visor", hatc=(60, 100, 70), coat=(60, 56, 70), trim=(236, 232, 214),
                  marks=["spectacles", "ink"], mouth="flat", age=0, eyes=(60, 70, 80), wide=0, extra="quill"),
    "captain": dict(bg=(40, 60, 88), skin="tan", hair=(40, 30, 26), style="long", beard="goatee", beardc=(40, 30, 26), hat="tricorn", hatc=(36, 34, 42), coat=(120, 36, 44), trim=(236, 196, 80),
                    marks=["scar_eye"], mouth="smirk", age=1, eyes=(40, 40, 50), wide=1, extra="feather"),
}


class Cv:
    """A 48 x 48 canvas with helpers that draw shaded, outlined pixel shapes."""

    def __init__(self, bg):
        self.im = Image.new("RGBA", (CELL, CELL), bg + (255,))
        self.d = ImageDraw.Draw(self.im)
        self.fig = np.zeros((CELL, CELL), bool)
        self.paint_bg = True

    def px(self, x, y, c):
        if 0 <= x < CELL and 0 <= y < CELL:
            self.im.putpixel((int(x), int(y)), c + (255,))
            if not self.paint_bg:
                self.fig[int(y), int(x)] = True

    def shaded_ellipse(self, cx, cy, rx, ry, base, light=(-0.6, -0.6)):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                r2 = u * u + v * v
                if r2 <= 1.0:
                    dot = u * light[0] + v * light[1]
                    f = 1.0 - 0.28 * max(0.0, -dot + 0.15) + 0.12 * max(0.0, dot - 0.2)
                    f *= 1.0 - 0.10 * max(0.0, r2 - 0.55)
                    self.px(x, y, sh(base, f))

    def shaded_poly(self, pts, base, light_x=-1.0):
        m = Image.new("L", (CELL, CELL), 0)
        ImageDraw.Draw(m).polygon(pts, fill=255)
        a = np.array(m) > 0
        ys, xs = np.nonzero(a)
        if len(xs) == 0:
            return
        x0, x1 = xs.min(), xs.max() + 1
        for y, x in zip(ys, xs):
            t = (x - x0) / max(x1 - x0, 1)
            f = 1.08 - 0.30 * t * (1 if light_x < 0 else -1) if light_x < 0 else 0.78 + 0.30 * t
            self.px(x, y, sh(base, f))

    def rect(self, x0, y0, x1, y1, c):
        self.d.rectangle((x0, y0, x1, y1), fill=c + (255,))
        self.fig[max(int(y0), 0):int(y1) + 1, max(int(x0), 0):int(x1) + 1] = True

    def finish(self):
        """1 px dark rim around everything that differs from the flat background."""
        arr = np.array(self.im)
        solid = self.fig
        edge = solid & ~(np.roll(solid, 1, 0) & np.roll(solid, -1, 0) & np.roll(solid, 1, 1) & np.roll(solid, -1, 1))
        edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = False
        for y, x in zip(*np.nonzero(edge)):
            r, g, b = arr[y, x, :3]
            arr[y, x, :3] = (int(r * 0.45), int(g * 0.4), int(b * 0.38))
        return Image.fromarray(arr, "RGBA")


def draw(name: str, p: dict) -> Image.Image:
    skin = SKIN[p["skin"]]
    cv = Cv(p["bg"])
    # backdrop: a darker band at the bottom and a soft window glow top-left
    for y in range(CELL):
        for x in range(CELL):
            g = 1.0 + 0.18 * (1.0 - y / CELL) - 0.22 * (y / CELL) ** 2 - 0.10 * (x / CELL)
            if (x - 8) ** 2 + (y - 8) ** 2 < 120:
                g += 0.10
            cv.px(x, y, sh(p["bg"], g))
    cv.paint_bg = False
    wide = p["wide"]
    cx = 24
    # shoulders and coat
    top = 34
    sw = 17 + wide
    cv.shaded_poly([(cx - sw - 6, 48), (cx - sw, top + 3), (cx - 9, top - 1), (cx + 9, top - 1), (cx + sw, top + 3), (cx + sw + 6, 48)], p["coat"])
    # neck
    cv.shaded_poly([(cx - 5, 30), (cx + 5, 30), (cx + 6, top + 2), (cx - 6, top + 2)], sh(skin, 0.86))
    ex = p.get("extra")
    # collar / trim
    trim = p["trim"]
    cv.shaded_poly([(cx - 8, top - 1), (cx - 2, top + 8), (cx - 6, top + 11), (cx - 12, top + 2)], trim)
    cv.shaded_poly([(cx + 8, top - 1), (cx + 2, top + 8), (cx + 6, top + 11), (cx + 12, top + 2)], sh(trim, 0.85), light_x=1)
    cv.rect(cx - 1, top + 5, cx, 47, sh(p["coat"], 0.7))
    if ex == "stripes":
        for yy in range(top + 9, 48, 4):
            cv.rect(cx - sw - 4, yy, cx + sw + 4, yy, sh(trim, 1.0))
    if ex == "buttons" or p["marks"] and "strap" in p["marks"]:
        for yy in (top + 9, top + 14, top + 19):
            cv.px(cx - 2, yy, (240, 214, 90)); cv.px(cx + 2, yy, (240, 214, 90))
    if ex == "apron":
        cv.shaded_poly([(cx - 10, top + 8), (cx + 10, top + 8), (cx + 12, 48), (cx - 12, 48)], (214, 196, 150))
    if "apron" in p["marks"]:
        cv.shaded_poly([(cx - 11, top + 7), (cx + 11, top + 7), (cx + 13, 48), (cx - 13, 48)], (186, 214, 224))
    if ex == "cravat" or ex == "collar":
        cv.shaded_poly([(cx - 4, top), (cx + 4, top), (cx + 3, top + 7), (cx - 3, top + 7)], (240, 236, 224))
    if ex == "towel":
        cv.shaded_poly([(cx - 14, top + 1), (cx - 9, top - 1), (cx - 6, 47), (cx - 12, 47)], (190, 70, 60))
    # head
    hw, hh = 10.5 + (1 if p["age"] == 2 else 0), 13
    hy = 20
    # ears
    cv.shaded_ellipse(cx - hw + 0.5, hy + 1, 2.4, 3.2, sh(skin, 0.95))
    cv.shaded_ellipse(cx + hw - 0.5, hy + 1, 2.4, 3.2, sh(skin, 0.82))
    cv.shaded_ellipse(cx, hy, hw, hh, skin)
    if p["age"] == 0:
        pass
    # hair behind (long styles)
    hair = p["hair"]
    st = p["style"]
    if st == "long":
        cv.shaded_poly([(cx - hw - 2, hy - 6), (cx - hw - 3, hy + 16), (cx - hw + 3, hy + 14), (cx - hw + 3, hy - 4)], hair)
        cv.shaded_poly([(cx + hw + 2, hy - 6), (cx + hw + 3, hy + 16), (cx + hw - 3, hy + 14), (cx + hw - 3, hy - 4)], sh(hair, 0.8), light_x=1)
    if st == "wig":
        cv.shaded_ellipse(cx - hw - 1, hy + 6, 4.5, 9, hair)
        cv.shaded_ellipse(cx + hw + 1, hy + 6, 4.5, 9, sh(hair, 0.85))
    # hair on top
    def cap_hair(h=1.0, low=0):
        for y in range(hy - hh - 3, hy + 3):
            for x in range(cx - 14, cx + 15):
                u, v = (x + 0.5 - cx) / (hw + 1.6), (y + 0.5 - hy) / (hh + 2.0)
                if u * u + v * v <= 1.0 and (y + 0.5) < hy - 6 + (h - 1.0) * 6 + low + 8 * u * u:
                    f = 1.08 - 0.3 * max(0, (x - cx) / 14) + 0.12 * (1 - abs(v))
                    cv.px(x, y, sh(hair, f))
    if st in ("short", "messy", "parted", "slick", "buzz", "long", "curly", "wig"):
        cap_hair(1.0 if st != "buzz" else 0.5, low=(2 if st in ("short", "parted", "slick") else 0))
    if st == "messy":
        for (dx, dy) in ((-9, -12), (-5, -15), (0, -16), (5, -15), (9, -12), (11, -8)):
            cv.shaded_ellipse(cx + dx, hy + dy + 2, 3, 2.4, hair)
    if st == "curly":
        for k in range(-5, 6):
            cv.shaded_ellipse(cx + k * 2.1, hy - hh + 1.5 - abs(k) * 0.35, 3.0, 2.6, hair)
    if st == "balding":
        cap_hair(0.2, low=-6)
        for dx in (-hw - 0.5, hw - 1):
            cv.shaded_ellipse(cx + dx, hy - 1, 2.3, 5, hair)
    if st == "bald_sides":
        for dx in (-hw + 0.5, hw - 0.5):
            cv.shaded_ellipse(cx + dx, hy - 2, 2.2, 5.5, hair)
    if st == "wig":
        for k in range(-5, 6):
            cv.shaded_ellipse(cx + k * 2.0, hy - hh + 2 - abs(k) * 0.2, 3.1, 3.0, hair)
    # face: brow, eyes, nose, mouth
    ey = hy - 1
    for sx in (-1, 1):
        ecx = cx + sx * 5
        # eye white + iris
        cv.rect(ecx - 2, ey, ecx + 1, ey + 1, (240, 236, 226))
        ix = ecx + (0 if sx < 0 else -1) + (1 if sx < 0 else 0)
        cv.px(ecx - (1 if sx > 0 else 0) + (1 if sx < 0 else 0), ey, p["eyes"])
        cv.px(ecx - (1 if sx > 0 else 0) + (1 if sx < 0 else 0), ey + 1, sh(p["eyes"], 0.55))
        # brows
        bc = sh(hair if p["age"] < 2 else (200, 198, 192), 0.8)
        cv.rect(ecx - 2, ey - 3, ecx + 1, ey - 3 + (1 if wide < 2 else 1), bc)
        if p["mouth"] in ("stern",):
            cv.px(ecx - sx * 2 + (1 if sx < 0 else 0), ey - 4, bc)
        if p["age"] == 2:
            cv.px(ecx + sx * 3, ey + 2, sh(skin, 0.8))
    # nose
    cv.rect(cx - 1, ey + 3, cx, ey + 6, sh(skin, 0.86))
    cv.rect(cx - 2, ey + 6, cx + 1, ey + 6, sh(skin, 0.74))
    cv.px(cx - 1, ey + 3, sh(skin, 1.1))
    # mouth
    my = ey + 10
    mc = sh(skin, 0.52)
    m = p["mouth"]
    beard = p.get("beard")
    if m in ("smile", "grin"):
        cv.rect(cx - 3, my, cx + 2, my, mc)
        cv.px(cx - 4, my - 1, mc); cv.px(cx + 3, my - 1, mc)
        if m == "grin":
            cv.rect(cx - 2, my + 1, cx + 1, my + 1, (244, 240, 230))
    elif m == "smirk":
        cv.rect(cx - 2, my, cx + 1, my, mc); cv.px(cx + 2, my - 1, mc); cv.px(cx + 3, my - 2, mc)
    elif m == "stern":
        cv.rect(cx - 3, my, cx + 2, my, mc); cv.rect(cx - 3, my + 1, cx - 2, my + 1, sh(mc, 1.1))
    else:
        cv.rect(cx - 3, my, cx + 2, my, mc)
    # beard
    bc = p.get("beardc", hair)
    if beard == "full":
        for y in range(hy + 3, hy + hh + 3):
            for x in range(cx - 11, cx + 12):
                u, v = (x + 0.5 - cx) / (hw + 0.4), (y + 0.5 - hy) / (hh + 0.3)
                if u * u + v * v <= 1.0 and y > hy + 4 + 3 * abs(u) ** 3 * 4 and not (abs(x + 0.5 - cx) < 3.5 and hy + 8 <= y <= hy + 11):
                    cv.px(x, y, sh(bc, 1.08 - 0.3 * max(0, (x - cx) / 12)))
        cv.rect(cx - 3, my, cx + 2, my, mc)
    elif beard == "stubble":
        rs = np.random.RandomState(7 + len(name))
        for y in range(hy + 4, hy + hh + 2):
            for x in range(cx - 10, cx + 11):
                u, v = (x + 0.5 - cx) / (hw - 0.4), (y + 0.5 - hy) / (hh - 0.3)
                if u * u + v * v <= 1.0 and y > hy + 6 + 2 * abs(u) * 3 and rs.rand() < 0.5:
                    cv.px(x, y, sh(skin, 0.62))
    elif beard in ("mustache",):
        cv.shaded_ellipse(cx - 3.2, my - 2, 3.4, 1.7, bc); cv.shaded_ellipse(cx + 3.2, my - 2, 3.4, 1.7, sh(bc, 0.85))
    elif beard == "goatee":
        cv.shaded_ellipse(cx, my + 4, 3.6, 3.4, bc)
        cv.shaded_ellipse(cx - 3, my - 2, 2.6, 1.3, bc); cv.shaded_ellipse(cx + 3, my - 2, 2.6, 1.3, sh(bc, 0.85))
    elif beard == "sideburns":
        cv.rect(cx - hw + 1, hy - 3, cx - hw + 2, hy + 7, bc); cv.rect(cx + hw - 2, hy - 3, cx + hw - 1, hy + 7, sh(bc, 0.8))
    # marks
    for mk in p["marks"]:
        if mk == "freckles":
            for (dx, dy) in ((-7, 3), (-5, 4), (-8, 4), (5, 3), (7, 4), (4, 4), (-6, 2), (6, 2)):
                cv.px(cx + dx, ey + dy, sh(skin, 0.7))
        elif mk == "scar_cheek":
            for k in range(6):
                cv.px(cx + 5 + k // 2, ey + 3 + k, (232, 190, 170))
        elif mk == "scar_brow":
            for k in range(4):
                cv.px(cx - 7 + k, ey - 5 + k // 2 + 1, (232, 190, 170))
        elif mk == "scar_eye":
            for k in range(8):
                cv.px(cx - 6 + k // 3, ey - 4 + k, (236, 196, 176))
        elif mk == "wrinkles":
            for dx in (-6, -5, 5, 6):
                cv.px(cx + dx, ey - 5, sh(skin, 0.74))
            cv.px(cx - 4, ey + 6, sh(skin, 0.8)); cv.px(cx + 3, ey + 6, sh(skin, 0.8))
        elif mk == "earring":
            cv.px(cx - hw - 1, hy + 4, (250, 214, 90)); cv.px(cx - hw - 1, hy + 5, (250, 214, 90))
        elif mk == "spectacles":
            for sx in (-1, 1):
                ecx = cx + sx * 5
                cv.d.rectangle((ecx - 3, ey - 1, ecx + 2, ey + 3), outline=(40, 36, 30, 255))
                cv.px(ecx - 2, ey, (200, 224, 236))
            cv.rect(cx - 1, ey, cx, ey, (40, 36, 30))
        elif mk == "rosy":
            for sx in (-1, 1):
                cv.shaded_ellipse(cx + sx * 7.5, ey + 5, 2.5, 1.8, (232, 120, 108))
        elif mk == "beauty":
            cv.px(cx + 6, ey + 7, (60, 40, 40))
        elif mk == "sawdust":
            for (dx, dy) in ((-4, -10), (2, -12), (7, -9), (-8, -6)):
                cv.px(cx + dx, hy + dy, (236, 216, 170))
        elif mk == "ink":
            cv.px(cx + 8, ey + 6, (40, 50, 90)); cv.px(cx + 9, ey + 6, (40, 50, 90))
    # hats
    hat = p["hat"]
    hc = p["hatc"]
    if hat == "tricorn":
        cv.shaded_poly([(cx - 20, hy - 6), (cx - 8, hy - 18), (cx + 8, hy - 18), (cx + 20, hy - 6), (cx + 12, hy - 7), (cx, hy - 10), (cx - 12, hy - 7)], hc)
        cv.rect(cx - 20, hy - 7, cx + 20, hy - 6, trim_c := (236, 196, 80))
        cv.shaded_ellipse(cx + 12, hy - 14, 3, 6, (230, 230, 220))
    elif hat == "bandana":
        cv.shaded_poly([(cx - hw - 1, hy - 4), (cx, hy - 14), (cx + hw + 1, hy - 4), (cx + hw + 2, hy - 1), (cx - hw - 2, hy - 1)], hc)
        cv.shaded_poly([(cx + hw, hy - 3), (cx + hw + 5, hy + 5), (cx + hw + 1, hy + 3)], sh(hc, 0.75), light_x=1)
    elif hat == "cap":
        cv.shaded_poly([(cx - hw - 1, hy - 5), (cx - 6, hy - 15), (cx + 6, hy - 15), (cx + hw + 1, hy - 5)], hc)
        cv.shaded_poly([(cx - hw - 3, hy - 4), (cx + hw + 3, hy - 4), (cx + hw + 1, hy - 2), (cx - hw - 1, hy - 2)], sh(hc, 0.8))
    elif hat == "cook":
        cv.shaded_ellipse(cx, hy - 14, 9, 6, hc); cv.shaded_poly([(cx - hw, hy - 6), (cx + hw, hy - 6), (cx + hw - 1, hy - 3), (cx - hw + 1, hy - 3)], sh(hc, 0.92))
    elif hat == "straw":
        cv.shaded_ellipse(cx, hy - 5, 17, 4.5, hc); cv.shaded_ellipse(cx, hy - 11, 9, 6.5, sh(hc, 1.06)); cv.rect(cx - 9, hy - 8, cx + 8, hy - 7, (140, 70, 50))
    elif hat == "knit":
        cv.shaded_ellipse(cx, hy - 9, hw + 1, 8, hc)
        for xx in range(int(cx - hw), int(cx + hw), 3):
            cv.rect(xx, hy - 14, xx, hy - 6, sh(hc, 0.82))
        cv.shaded_ellipse(cx, hy - 16, 2.4, 2.4, (230, 230, 220))
    elif hat == "tall":
        cv.shaded_ellipse(cx, hy - 5, 14, 3.4, hc)
        cv.shaded_poly([(cx - 8, hy - 5), (cx - 7, hy - 20), (cx + 7, hy - 20), (cx + 8, hy - 5)], hc)
        cv.rect(cx - 8, hy - 8, cx + 8, hy - 7, (230, 190, 80))
    elif hat == "flat":
        cv.shaded_ellipse(cx, hy - 8, hw + 3, 4.2, hc); cv.shaded_ellipse(cx, hy - 11, hw - 1, 3.2, sh(hc, 1.06))
    elif hat == "helmet":
        cv.shaded_ellipse(cx, hy - 8, hw + 1.5, 9, hc)
        cv.shaded_poly([(cx - hw - 3, hy - 4), (cx + hw + 3, hy - 4), (cx + hw + 1, hy - 2), (cx - hw - 1, hy - 2)], sh(hc, 0.8))
        cv.rect(cx - 1, hy - 16, cx, hy - 5, sh(hc, 0.7))
    elif hat == "visor":
        cv.shaded_poly([(cx - hw - 1, hy - 5), (cx + hw + 1, hy - 5), (cx + hw + 5, hy - 2), (cx - hw - 5, hy - 2)], hc)
    # props
    if ex == "pencil":
        cv.rect(cx + hw - 1, hy - 4, cx + hw + 3, hy - 3, (230, 200, 90))
    if ex == "quill":
        cv.d.line((cx + 14, 30, cx + 18, 18), fill=(236, 232, 220, 255)); cv.d.line((cx + 13, 31, cx + 14, 30), fill=(60, 50, 40, 255))
    if ex == "spyglass":
        cv.d.line((cx - 18, 46, cx - 9, 36), fill=(170, 120, 50, 255), width=3); cv.d.line((cx - 10, 37, cx - 8, 35), fill=(240, 220, 150, 255), width=3)
    if ex == "feather":
        cv.d.line((cx + 12, hy - 13, cx + 20, hy - 22), fill=(236, 90, 70, 255), width=2)
    return cv.finish()


def build() -> Image.Image:
    rows = (len(ORDER) + COLS - 1) // COLS
    img = Image.new("RGBA", (COLS * CELL, rows * CELL), (0, 0, 0, 0))
    for i, name in enumerate(ORDER):
        img.paste(draw(name, P[name]), ((i % COLS) * CELL, (i // COLS) * CELL))
    return img


def main() -> int:
    img = build()
    out = ROOT / "game/ui/portraits_atlas.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, optimize=True)
    prev = ROOT / "art_bible/cp1"
    prev.mkdir(parents=True, exist_ok=True)
    img.resize((img.width * 4, img.height * 4), Image.NEAREST).save(prev / "portraits.png")
    cols = len({img.getpixel((x, y)) for x in range(img.width) for y in range(img.height)})
    print(f"portraits: {len(ORDER)} busts, {cols} colours -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
