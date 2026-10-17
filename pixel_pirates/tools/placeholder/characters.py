"""Mannequin crew placeholders (Module A4).

Cell 48x64, feet baseline y=60, body about 42 px = 1.75 m at 24 px/m. 4 directions (s, n, e, w), 7 animations.
Deliberately plain "mannequin" look (shaded blobs, no faces to speak of) so nobody mistakes it for final art.
All figures are male (hard content rule 1): broad shoulders, short hair/beard/hat.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

from pxdraw import Canvas, flip_h

CELL_W, CELL_H = 48, 64
PIVOT = (24, 60)
DIRS = ["s", "n", "e", "w"]
ANIMS = {  # name: (frames, ms per frame, loop)
    "idle": (4, 180, True),
    "walk": (6, 100, True),
    "run": (6, 70, True),
    "work": (6, 120, True),
    "attack": (5, 70, False),
    "hit": (3, 80, False),
    "death": (8, 110, False),
}
VARIANTS = {  # name: (shirt ramp, hat style, skin ramp, hair ramp)
    "captain": ("cloth_red", "tricorn", "skin_light", "hull_oak"),
    "sailor": ("cloth_cream", "bandana", "skin_tan", "dirt"),
    "gunner": ("cloth_blue", "cap", "skin_dark", "hull_oak"),
    "villager": ("stone_cool", "none", "skin_tan", "dirt"),
}


def _pose(anim: str, i: int, n: int, d: str) -> dict:
    """returns joint offsets for frame i of n."""
    ph = i / n * 2 * math.pi
    p = dict(ph=ph, bob=0, lean=0, swing=0.0, lift=0, arm_l=0.0, arm_r=0.0, sword=None, head_dy=0, fold=0.0)
    if anim == "idle":
        p["bob"] = [0, 0, -1, -1][i % 4]
        p["arm_l"] = p["arm_r"] = [0, 0.5, 1, 0.5][i % 4]
    elif anim in ("walk", "run"):
        run = anim == "run"
        amp = 8 if run else 5.5
        p["swing"] = amp * math.sin(ph)
        p["lift"] = (3.5 if run else 2.5)
        p["bob"] = -round((2 if run else 1) * abs(math.sin(ph)))
        p["lean"] = 1 if run else 0
        sw = 6.0 if run else 4.0
        p["arm_l"], p["arm_r"] = sw * math.sin(ph), -sw * math.sin(ph)
    elif anim == "work":
        p["bob"] = -round(abs(math.sin(ph)))
        p["arm_l"] = 5 * math.sin(ph)
        p["arm_r"] = -5 * math.sin(ph)
        p["lean"] = 1
    elif anim == "attack":
        th = [-100, -150, -20, 45, 20][i % 5]  # sword angle, degrees from hanging straight down
        p["sword"] = th
        p["lean"] = [0, -1, 1, 2, 1][i % 5]
    elif anim == "hit":
        p["lean"] = [-1, -2, -1][i % 3]
        p["head_dy"] = [0, 1, 0][i % 3]
        p["arm_l"], p["arm_r"] = 3, 3
    elif anim == "death":
        p["fold"] = min(1.0, i / (n - 3))
    return p


def _draw(d: str, anim: str, i: int, n: int, variant: str, no_hat: bool = False) -> Canvas:
    shirt, hat, skin, hair = VARIANTS[variant]
    if no_hat and hat in ("tricorn", "cap"):
        hat = "none"
    p = _pose(anim, i, n, d)
    c = Canvas(CELL_W, CELL_H)
    cx = 24 + p["lean"] * (0.6 if d in ("e", "w") else 0)
    cx_body = 24 + (p["lean"] if d == "e" else 0)
    bob = p["bob"]
    hip_y, sh_y, head_cy = 44 + bob, 31 + bob, 24 + bob + p["head_dy"]
    side = d in ("e", "w")
    front = d == "s"
    sw = p["swing"]

    # ---- legs
    ph = p["ph"]
    moving = anim in ("walk", "run")
    for k, sgn in enumerate((1, -1)):
        lift = p["lift"] * max(0.0, sgn * math.cos(ph)) if moving else 0.0
        if side:
            fx = 24 + sgn * sw + p["lean"] * 0.5
            foot = (fx, 59 - lift)
            c.capsule((24 + p["lean"] * 0.4, hip_y), foot, 3.0, "dirt", r1=2.6, bias=-1 if k == 1 else 0)
            c.ellipsoid(foot[0] + 1.5, foot[1] - 0.5, 3.6, 2.4, "hull_oak")
        else:
            sx = -3.2 if k == 0 else 3.2
            foot = (24 + sx, 59 - lift)
            c.capsule((24 + sx * 0.8, hip_y), foot, 3.0, "dirt", r1=2.6)
            c.ellipsoid(foot[0], foot[1] - 0.5, 3.0, 2.4, "hull_oak")

    # ---- far arm (side view) drawn before the torso
    def arm(sx: float, swing_x: float, swing_y: float, near: bool):
        s = (cx_body + sx, sh_y + 1)
        h = (s[0] + swing_x * (1 if side else 0.2), s[1] + 10 + swing_y * (0.2 if side else 1))
        c.capsule(s, h, 2.4, shirt, r1=2.1, bias=0 if near else -1)
        c.ellipsoid(h[0], h[1] + 0.5, 2.0, 2.0, skin)

    if side:
        arm(0, -p["arm_r"], 0, False)
    # ---- torso
    trx = 5.2 if side else 7.2
    c.ellipsoid(cx_body, (sh_y + hip_y) / 2 + 0.5, trx, (hip_y - sh_y) / 2 + 3.0, shirt)
    belt_y = hip_y - 1
    belt = (c.xx > cx_body - trx) & (c.xx < cx_body + trx) & (c.yy >= belt_y) & (c.yy < belt_y + 2) & (c.rgba[..., 3] > 0)
    c.paint(belt, None, "wood", flat_step=1)
    # ---- arms
    if not side:
        sword = p["sword"]
        arm(-8.2, 0, p["arm_l"], True)
        if sword is None:
            arm(8.2, 0, p["arm_r"], True)
    else:
        if p["sword"] is None:
            arm(0, p["arm_l"], 0, True)
    if p["sword"] is not None:
        th = math.radians(p["sword"])
        s0 = (cx_body + (3.5 if side else 8.2), sh_y + 1.5)
        dirx = 1 if d != "w" else 1  # drawn as 'e'/'s' then flipped for w
        hand = (s0[0] + 7 * math.sin(th) * dirx, s0[1] + 7 * math.cos(th))
        c.capsule(s0, hand, 2.4, shirt, r1=2.1)
        c.ellipsoid(hand[0], hand[1], 2.0, 2.0, skin)
        tip = (hand[0] + 10 * math.sin(th), hand[1] + 10 * math.cos(th))
        c.capsule(hand, tip, 1.0, "iron", r1=0.8, bias=1)
        c.capsule((hand[0] - 1.2 * math.sin(th) - 1.6 * math.cos(th), hand[1] - 1.2 * math.cos(th) + 1.6 * math.sin(th)),
                  (hand[0] - 1.2 * math.sin(th) + 1.6 * math.cos(th), hand[1] - 1.2 * math.cos(th) - 1.6 * math.sin(th)), 0.8, "gold")
        if not side:
            arm(-8.2, 0, 0, True)
    # ---- head
    hx = cx_body + (1.0 if d == "e" else 0)
    head = c.ellipsoid(hx, head_cy, 6.0, 6.2, hair if d == "n" else skin)
    if d == "s":
        low = head & (c.yy > head_cy + 2.8)
        c.paint(low, None, hair, flat_step=2)  # beard
        c.dots([(hx - 2.5, head_cy - 0.5), (hx + 1.5, head_cy - 0.5)], "iron", 0)
    elif d in ("e", "w"):
        back = head & (c.xx < hx - 1.5)
        c.paint(back, None, hair, flat_step=2)
        low = head & (c.yy > head_cy + 3.0) & (c.xx > hx - 1)
        c.paint(low, None, hair, flat_step=2)
        c.dots([(hx + 2.5, head_cy - 0.5)], "iron", 0)
    # ---- hat
    if hat == "tricorn":
        c.poly([(hx - 9, head_cy - 4), (hx, head_cy - 11.5), (hx + 9, head_cy - 4), (hx + 6, head_cy - 3), (hx - 6, head_cy - 3)], "hull_oak", step=2)
        c.rect(hx - 9, head_cy - 4.5, hx + 9, head_cy - 3, "gold", step=2)
    elif hat == "bandana":
        c.paint(head & (c.yy < head_cy - 2.2), None, "cloth_red", flat_step=2)
        if d in ("n", "e", "w"):
            c.dots([(hx - 6.5, head_cy - 1), (hx - 7.5, head_cy)], "cloth_red", 1)
    elif hat == "cap":
        c.ellipsoid(hx, head_cy - 3.5, 6.5, 3.8, "cloth_blue", bias=1)
    return c


def _death(base: Canvas, d: str, k: float) -> Canvas:
    """rotate an idle figure about the waist, lay it on the ground, keep it inside the cell. k in [0,1]."""
    img = base.to_image()
    ang = 90 * k * (-1 if d in ("n", "w") else 1)
    img = img.rotate(-ang, resample=Image.NEAREST, center=(24, 40))
    a = np.asarray(img)[..., 3] > 0
    ys, xs = np.nonzero(a)
    dy = int(round((60 - (ys.max() + 1)) * k))  # settle towards the ground line
    dx = 0
    if xs.min() < 1:
        dx = 1 - xs.min()
    elif xs.max() > 46:
        dx = 46 - xs.max()
    shifted = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shifted.paste(img, (dx, dy), img)
    out = Canvas(CELL_W, CELL_H)
    arr = np.asarray(shifted)
    out.rgba = arr.copy()
    out.ramp = np.where(arr[..., 3] > 0, 0, -1).astype(np.int16)
    return out


def make_sheet(variant: str) -> tuple[Image.Image, dict]:
    """sheet: columns = all frames of all anims in ANIMS order, rows = DIRS (s, n, e, w)."""
    total = sum(v[0] for v in ANIMS.values())
    sheet = Image.new("RGBA", (total * CELL_W, len(DIRS) * CELL_H), (0, 0, 0, 0))
    meta = {}
    col = 0
    for anim, (n, ms, loop) in ANIMS.items():
        meta[anim] = {"start": col, "frames": n, "ms": ms, "loop": loop}
        for r, d in enumerate(DIRS):
            dd = "e" if d == "w" else d
            for i in range(n):
                if anim == "death":
                    base = _draw(dd, "idle", 0, 4, variant, no_hat=True)
                    base.outline()
                    c = _death(base, d, min(1.0, i / (n - 3)))
                else:
                    c = _draw(dd, anim, i, n, variant)
                    c.outline()
                if d == "w":
                    c = flip_h(c)
                sheet.paste(c.to_image(), ((col + i) * CELL_W, r * CELL_H))
        col += n
    return sheet, meta
