"""CP-1 revision: the capital's building sprites (Anvil Harbor). Small cell 192 x 208 px (13.3 x 14.4 m, pivot 96,202); grand cell
384 x 304 px (26.7 x 21.1 m, pivot 192,298). 14.4 px per metre. All fronts face south (the camera). Prototype art, from the palette."""
from __future__ import annotations

import numpy as np
from PIL import Image

from city_kit import (MATS, PPM, awning_striped, balcony, canvas, chimney, col, disc, dormer, finish, flag, hanging_sign, hsh, lantern,
                      line, px, rect, roof, shift, wall, window, door)

SW, SH, SPX, SPY = 224, 208, 112, 202
GW, GH, GPX, GPY = 384, 336, 192, 330
FLOOR = 44


def _cols(wpx, per=52):
    return max(1, int(round(wpx / per)))


def house(w_m, fl=2, mat="plaster", rf="red", shape="gable", rh=34, shutter=None, door_at=0.5, shop=None, sign=None, balc=False,
          chim=True, dorm=0, gable=False, seed=1, lit=0.75, arch_win=False, lantern_on=True, fh=FLOOR, planks=False, bays=None):
    """The general town building. `shop` = (awning a, awning b) gives it a shopfront."""
    c = canvas(SW, SH)
    W = int(w_m * PPM)
    x0 = SPX - W // 2
    x1 = x0 + W
    wall_h = fl * fh + 6
    ytop = SPY - wall_h
    wall(c, x0, ytop, x1, SPY, mat, seed)
    if mat in ("brick", "stone", "greystone", "half", "halfsand") or planks:
        rect(c, x0, SPY - 8, x1, SPY, col("stone_warm", 2))                       # plinth
        rect(c, x0, SPY - 8, x1, SPY - 7, col("stone_warm", 3))
    ncol = _cols(W)
    step = W / ncol
    dcol = min(ncol - 1, int(door_at * ncol))
    for f in range(fl):
        fy_base = SPY - f * fh
        for i in range(ncol):
            cx = int(x0 + step * (i + 0.5))
            if f == 0 and i == dcol:
                door(c, cx - 6, SPY, 12, 31, color=("wood", 2) if hsh(seed, 1) > 0.4 else ("cloth_blue", 2))
                if lantern_on:
                    lantern(c, cx + 9, SPY - 34)
                continue
            if f == 0 and shop is not None:
                window(c, cx - 11, SPY - 30, 22, 20, hsh(i, f, seed) < lit + 0.2, shutter=None, sill=True)
                continue
            lit_w = hsh(i, f, seed) < lit
            window(c, cx - 6, fy_base - 34, 12, 17, lit_w, shutter=shutter, arch=arch_win)
        if f > 0 and mat not in ("timber", "tar"):
            rect(c, x0, fy_base - 1 + 0, x1, fy_base + 1, col("stone_warm", 3))
            rect(c, x0, fy_base + 1, x1, fy_base + 3, col("stone_warm", 1))
    if shop is not None:
        awning_striped(c, x0 + 6, x1 - 6, SPY - 39, 8, shop[0], shop[1], 8)
        shift(c, x0 + 6, SPY - 31, x1 - 6, SPY - 29, -1)
    if balc:
        bx = x0 + int(step * (dcol + 0.5)) - 18
        balcony(c, max(bx, x0 + 2), min(bx + 36, x1 - 2), SPY - fh - 4)
    if gable:
        gh = 30
        steps = 5
        for i in range(steps):                                                       # crow-stepped gable in the wall material
            inset = (i + 1) * (W // 2 - 8) // steps
            rect(c, x0 + inset, ytop - (i + 1) * (gh // steps), x1 - inset, ytop - i * (gh // steps) + 1, col(*MATS[mat]))
            rect(c, x0 + inset, ytop - (i + 1) * (gh // steps) - 1, x1 - inset, ytop - (i + 1) * (gh // steps), col("stone_warm", 4))
        rect(c, x0 + W // 2 - 5, ytop - gh + 6, x0 + W // 2 + 5, ytop - gh + 20, col(*MATS[mat]))
        window(c, x0 + W // 2 - 4, ytop - gh + 9, 8, 10, hsh(seed, 7) < lit, sill=False)
        rect(c, x0 + W // 2, ytop - gh - 6, x0 + W // 2 + 1, ytop - gh - 1, col("iron", 2))
        rect(c, x0, ytop - 1, x1, ytop + 1, col("stone_warm", 4))
        top = ytop - gh
        if bays:
            hoist(c, x0 + W // 2, ytop - gh + 22)
    else:
        top = roof(c, x0, x1, ytop, rh, rf, shape, seed)
        if chim:
            chimney(c, x0 + int(W * (0.18 if hsh(seed, 2) < 0.5 else 0.68)), top + int(rh * 0.5), 15)
        for k in range(dorm):
            dx = x0 + int(W * (k + 1) / (dorm + 1)) - 9
            dormer(c, dx, ytop - 2, rf, lit=hsh(seed, 20 + k) < lit)
    if sign:
        hanging_sign(c, x1 + 2 if sign[1] == "r" else x0 - 1 + 14, SPY - fh - 16 if fl > 1 else SPY - 44, sign[0])
        if sign[1] == "r":
            pass
    shift(c, x0 - 4, ytop - 2, x1 + 5, ytop + 5, -1)
    return finish(c)


def hoist(c, cx, y):
    rect(c, cx - 14, y - 3, cx + 2, y, col("wood", 2))
    rect(c, cx - 12, y, cx - 11, y + 8, col("sand", 3))
    rect(c, cx - 14, y + 8, cx - 8, y + 12, col("wood", 3))


def warehouse(w_m=12.0, mat="timber", rf="slate", seed=5, doors=2, tall=2):
    c = canvas(SW, SH)
    W = int(w_m * PPM)
    x0, x1 = SPX - W // 2, SPX + W // 2
    wh = tall * FLOOR + 10
    ytop = SPY - wh
    wall(c, x0, ytop, x1, SPY, mat, seed)
    rect(c, x0, SPY - 8, x1, SPY, col("stone_warm", 2))
    rect(c, x0, SPY - 8, x1, SPY - 7, col("stone_warm", 3))
    dw = 28
    for i in range(doors):
        cx = int(x0 + W * (i + 0.5) / doors)
        rect(c, cx - dw // 2 - 2, SPY - 52, cx + dw // 2 + 2, SPY, col("wood", 1))
        rect(c, cx - dw // 2, SPY - 50, cx + dw // 2, SPY, col("wood", 2))
        for xx in range(cx - dw // 2, cx + dw // 2, 5):
            rect(c, xx, SPY - 50, xx + 1, SPY, col("wood", 1))
        line(c, cx - dw // 2, SPY - 50, cx + dw // 2 - 1, SPY - 1, col("wood", 1))
        line(c, cx + dw // 2 - 1, SPY - 50, cx - dw // 2, SPY - 1, col("wood", 1))
        rect(c, cx - 1, SPY - 50, cx + 1, SPY, col("iron", 1))
        window(c, cx - 5, ytop + 12, 10, 14, hsh(i, seed) < 0.6, sill=False, bars=True)
        rect(c, cx - 8, ytop + 28, cx + 8, ytop + 30, col("wood", 1)) if tall > 1 else None
    top = roof(c, x0, x1, ytop, 36, rf, "gable", seed, overhang=7, tile_w=10, tile_h=5)
    hoist(c, SPX, ytop + 4)
    rect(c, SPX - 1, ytop - 8, SPX + 1, ytop + 4, col("wood", 1))
    flag(c, x1 - 20, top - 8, 16, 10, ("cloth_blue", 3), ("cloth_cream", 4)) if mat == "brick" else None
    return finish(c)


def workshop(w_m=9.0, kind="smith", seed=2):
    """Open-fronted workshop: the dark bay, a glowing forge or a workbench, a deep roof on posts."""
    c = canvas(SW, SH)
    W = int(w_m * PPM)
    x0, x1 = SPX - W // 2, SPX + W // 2
    wh = 70
    ytop = SPY - wh
    wall(c, x0, ytop, x1, SPY, "timber", seed)
    rect(c, x0 + 10, ytop + 10, x1 - 10, SPY, col("hull_oak", 0))                      # open bay
    rect(c, x0 + 10, ytop + 10, x1 - 10, ytop + 14, col("hull_oak", 1))
    if kind == "smith":
        rect(c, x0 + 18, SPY - 34, x0 + 52, SPY, col("stone_warm", 2))                  # forge hearth
        rect(c, x0 + 18, SPY - 34, x0 + 52, SPY - 31, col("stone_warm", 4))
        rect(c, x0 + 24, SPY - 28, x0 + 46, SPY - 14, col("fire", 3))
        rect(c, x0 + 28, SPY - 24, x0 + 42, SPY - 16, col("fire", 4))
        rect(c, x0 + 26, SPY - 40, x0 + 44, SPY - 34, col("stone_warm", 1))
        rect(c, x1 - 50, SPY - 18, x1 - 30, SPY - 12, col("iron", 2))                   # anvil
        rect(c, x1 - 44, SPY - 12, x1 - 36, SPY, col("wood", 2))
        rect(c, x1 - 52, SPY - 22, x1 - 28, SPY - 18, col("iron", 3))
        for i in range(4):
            line(c, x0 + 60 + i * 5, ytop + 14, x0 + 60 + i * 5, ytop + 26 + (i % 2) * 5, col("iron", 3))   # hanging tools
    else:
        rect(c, x0 + 16, SPY - 22, x1 - 16, SPY - 16, col("wood", 3))                   # carpenter's bench
        rect(c, x0 + 20, SPY - 16, x0 + 24, SPY, col("wood", 2)); rect(c, x1 - 24, SPY - 16, x1 - 20, SPY, col("wood", 2))
        for i in range(5):
            rect(c, x0 + 22 + i * 6, SPY - 44, x0 + 26 + i * 6, SPY - 22 + (i % 2), col("wood", 4 if i % 2 else 3))     # planks
        rect(c, x1 - 40, SPY - 30, x1 - 18, SPY - 22, col("cloth_cream", 3))
    for x in (x0 + 2, x1 - 4):
        rect(c, x, ytop, x + 3, SPY, col("wood", 3)); rect(c, x, ytop, x + 1, SPY, col("wood", 4))
    top = roof(c, x0, x1, ytop, 34, "brown" if kind != "smith" else "dark", "gable", seed, overhang=8)
    if kind == "smith":
        chimney(c, x0 + 30, top + 18, 22, 12)
    hanging_sign(c, x1 + 4, ytop + 14, "hammer" if kind == "smith" else "rope")
    return finish(c)


def tavern(w_m=13.0, seed=9):
    c = house(w_m, fl=2, mat="half", rf="red", shape="gable", rh=40, shutter=("grass", 2), door_at=0.5, sign=("mug", "r"),
              balc=True, dorm=2, seed=seed, lit=1.0, lantern_on=True)
    return c


def mansion(w_m=14.0, mat="white", rf="teal", seed=4, columns=True, fl=2):
    c = canvas(SW, SH)
    W = int(w_m * PPM)
    x0, x1 = SPX - W // 2, SPX + W // 2
    wh = fl * (FLOOR + 4) + 8
    ytop = SPY - wh
    wall(c, x0, ytop, x1, SPY, mat, seed)
    rect(c, x0, SPY - 10, x1, SPY, col("stone_warm", 3))
    rect(c, x0, SPY - 10, x1, SPY - 9, col("stone_warm", 4))
    rect(c, x0, ytop, x1, ytop + 3, col("stone_warm", 4))
    rect(c, x0, ytop + 3, x1, ytop + 5, col("stone_warm", 2))
    ncol = 5
    step = W / ncol
    for f in range(fl):
        fy = SPY - f * (FLOOR + 4)
        for i in range(ncol):
            cx = int(x0 + step * (i + 0.5))
            if f == 0 and i == 2:
                continue
            window(c, cx - 6, fy - 40, 12, 22, hsh(i, f, seed) < 0.8, shutter=("cloth_blue", 2) if f == 0 else ("cloth_blue", 2), arch=True)
        if f > 0:
            rect(c, x0, fy - 1, x1, fy + 1, col("stone_warm", 4))
    door(c, SPX - 8, SPY - 10, 16, 34, color=("wood", 1), frame="stone_warm")
    if columns:
        for dx in (-18, 18):
            rect(c, SPX + dx - 3, SPY - 66, SPX + dx + 3, SPY - 10, col("cloth_cream", 4))
            rect(c, SPX + dx - 3, SPY - 66, SPX + dx - 1, SPY - 10, col("cloth_cream", 4))
            rect(c, SPX + dx + 1, SPY - 66, SPX + dx + 3, SPY - 10, col("cloth_cream", 2))
            rect(c, SPX + dx - 5, SPY - 70, SPX + dx + 5, SPY - 66, col("stone_warm", 4))
        rect(c, SPX - 26, SPY - 76, SPX + 26, SPY - 70, col("stone_warm", 3))
        for i in range(14):
            rect(c, SPX - 26 + i * 2, SPY - 90 + i, SPX + 26 - i * 2, SPY - 89 + i, col("stone_warm", 4 if i < 2 else 3))
        window(c, SPX - 5, SPY - 112 + 20, 10, 12, True, sill=False) if False else None
    top = roof(c, x0, x1, ytop, 38, rf, "hip", seed, overhang=6)
    chimney(c, x0 + 16, top + 20, 16)
    chimney(c, x1 - 26, top + 20, 16)
    flag(c, SPX, top - 22, 22, 14, ("cloth_blue", 3), ("gold", 3))
    for dx in (-W // 2 + 4, W // 2 - 10):
        rect(c, SPX + dx, SPY - 6, SPX + dx + 6, SPY, col("stone_warm", 3))
    return finish(c)


def wall_tower(seed=8):
    """Round-ish corner tower of the town wall: 6 m wide, 11 m tall, crenellated, one arrow slit."""
    c = canvas(SW, SH)
    W = int(6.4 * PPM)
    x0, x1 = SPX - W // 2, SPX + W // 2
    ytop = SPY - 128
    wall(c, x0, ytop, x1, SPY, "greystone", seed)
    shift(c, x0 + 2, ytop, x0 + 12, SPY, 1)
    shift(c, x1 - 14, ytop, x1, SPY, -1)
    for y in (SPY - 90, SPY - 50):
        rect(c, SPX - 1, y, SPX + 2, y + 12, col("hull_oak", 0))
    rect(c, x0 - 4, ytop - 4, x1 + 4, ytop + 4, col("stone_cool", 4))
    rect(c, x0 - 4, ytop + 4, x1 + 4, ytop + 7, col("stone_cool", 1))
    for x in range(x0 - 4, x1 + 4, 14):
        rect(c, x, ytop - 16, x + 8, ytop - 4, col("stone_cool", 3))
        rect(c, x, ytop - 16, x + 8, ytop - 14, col("stone_cool", 4))
    flag(c, SPX + 4, ytop - 40, 26, 14, ("cloth_red", 3), ("gold", 3))
    rect(c, x0, SPY - 8, x1, SPY, col("stone_cool", 2))
    return finish(c)


def wall_straight(seed=3, w_m=13.0):
    c = canvas(SW, SH)
    W = int(w_m * PPM)
    x0, x1 = SPX - W // 2, SPX + W // 2
    ytop = SPY - 78
    wall(c, x0, ytop, x1, SPY, "greystone", seed)
    shift(c, x0, ytop, x1, ytop + 3, 1)
    rect(c, x0, ytop - 4, x1, ytop + 3, col("stone_cool", 4))
    rect(c, x0, ytop + 3, x1, ytop + 5, col("stone_cool", 1))
    for x in range(x0 + 2, x1 - 10, 22):
        rect(c, x, ytop - 12, x + 12, ytop - 4, col("stone_cool", 3))
        rect(c, x, ytop - 12, x + 12, ytop - 10, col("stone_cool", 4))
    rect(c, x0, SPY - 8, x1, SPY, col("stone_cool", 2))
    return finish(c)


def wall_post(seed=3):
    """North-south wall segment seen end-on: a 2.4 m wide pillar with the walkway receding on its top."""
    c = canvas(SW, SH)
    W = int(2.6 * PPM)
    x0, x1 = SPX - W // 2, SPX + W // 2
    ytop = SPY - 60
    wall(c, x0, ytop, x1, SPY, "greystone", seed)
    rect(c, x0, ytop - 24, x1, ytop, col("stone_cool", 3))                              # the top walkway receding
    rect(c, x0, ytop - 24, x1, ytop - 22, col("stone_cool", 4))
    rect(c, x0, ytop - 24, x0 + 3, ytop, col("stone_cool", 2))
    rect(c, x1 - 3, ytop - 24, x1, ytop, col("stone_cool", 2))
    rect(c, x0, SPY - 8, x1, SPY, col("stone_cool", 2))
    return finish(c)


def gatehouse(seed=6):
    """The town gate: a 10 m arch between two squat towers; the passage is dark."""
    c = canvas(SW, SH)
    W = int(12.4 * PPM)
    x0, x1 = SPX - W // 2, SPX + W // 2
    ytop = SPY - 112
    wall(c, x0, ytop, x1, SPY, "greystone", seed)
    ax0, ax1 = SPX - 26, SPX + 26
    rect(c, ax0, SPY - 66, ax1, SPY, col("hull_oak", 0))
    for i in range(26):                                                                 # round arch
        h = int(np.sqrt(max(26 * 26 - i * i, 0)) * 0.9)
        rect(c, SPX - i, SPY - 66 - h, SPX - i + 1, SPY - 66, col("hull_oak", 0))
        rect(c, SPX + i, SPY - 66 - h, SPX + i + 1, SPY - 66, col("hull_oak", 0))
    for x in range(ax0 + 4, ax1 - 3, 8):                                                # raised portcullis
        rect(c, x, SPY - 100, x + 1, SPY - 66, col("iron", 2))
    rect(c, ax0, SPY - 90, ax1, SPY - 88, col("iron", 2))
    shift(c, x0, ytop, x0 + 12, SPY, 1)
    shift(c, x1 - 12, ytop, x1, SPY, -1)
    rect(c, x0 - 4, ytop - 4, x1 + 4, ytop + 4, col("stone_cool", 4))
    for x in range(x0 - 4, x1 + 4, 14):
        rect(c, x, ytop - 14, x + 8, ytop - 4, col("stone_cool", 3))
        rect(c, x, ytop - 14, x + 8, ytop - 12, col("stone_cool", 4))
    rect(c, SPX - 18, ytop + 14, SPX + 18, ytop + 40, col("cloth_blue", 2))              # arms of the island: a crest
    rect(c, SPX - 18, ytop + 14, SPX + 18, ytop + 16, col("gold", 3))
    rect(c, SPX - 8, ytop + 22, SPX + 8, ytop + 26, col("iron", 2)); rect(c, SPX - 4, ytop + 26, SPX + 4, ytop + 32, col("iron", 2))
    rect(c, SPX - 10, ytop + 32, SPX + 10, ytop + 35, col("iron", 3))
    window(c, x0 + 10, ytop + 40, 8, 14, True, sill=False, bars=True)
    window(c, x1 - 18, ytop + 40, 8, 14, True, sill=False, bars=True)
    flag(c, x0 + 12, ytop - 36, 22, 14, ("cloth_red", 3), ("gold", 3))
    flag(c, x1 - 14, ytop - 36, 22, 14, ("cloth_red", 3), ("gold", 3))
    rect(c, x0, SPY - 8, x1, SPY, col("stone_cool", 2))
    return finish(c)


def rowhouse(seed=11):
    """Three narrow terraced houses in different washes under one long roof."""
    c = canvas(SW, SH)
    W = int(12.6 * PPM)
    x0, x1 = SPX - W // 2, SPX + W // 2
    ytop = SPY - 96
    third = W // 3
    mats = ["rose", "sand", "blue"]
    for i in range(3):
        a, b = x0 + i * third, x0 + (i + 1) * third
        wall(c, a, ytop, b, SPY, mats[i], seed + i)
        rect(c, a, ytop + 44, b, ytop + 46, col("stone_warm", 3))
        window(c, (a + b) // 2 - 6, ytop + 14, 12, 17, hsh(i, seed) < 0.8, shutter=("cloth_red", 2) if i != 0 else ("cloth_blue", 2))
        window(c, (a + b) // 2 - 6 + (10 if i % 2 == 0 else -10), ytop + 56, 10, 17, True, sill=True) if False else None
        window(c, a + 8, ytop + 54, 9, 17, hsh(i, seed + 3) < 0.7, sill=True)
        door(c, b - 22, SPY, 12, 30, color=("wood", 2))
        rect(c, a, ytop, a + 1, SPY, col("stone_warm", 1))
        rect(c, a + 8, SPY - 8, a + 22, SPY, col("grass", 2)) if False else None
    top = roof(c, x0, x1, ytop, 34, "brown", "gable", seed, overhang=5)
    for i in range(3):
        chimney(c, x0 + i * third + 8, top + 18, 14)
    return finish(c)


def lighthouse_keeper():
    return house(6.5, fl=1, mat="white", rf="red", shape="hip", rh=30, shutter=("cloth_blue", 2), seed=21)


def tall_townhouse(w_m=5.8, mat="brick", seed=3, fl=3):
    return house(w_m, fl=fl, mat=mat, gable=True, shutter=("cloth_cream", 3) if mat == "brick" else ("cloth_red", 2), seed=seed, lit=0.8, bays=(seed % 2 == 0), door_at=0.5)



# ---- grand buildings (384 x 304 cell) ---------------------------------------------------------------------------------------
def _columns(c, xs, y_top, y_base, w=8):
    for x in xs:
        rect(c, x - w // 2, y_top, x + w // 2, y_base, col("cloth_cream", 3))
        rect(c, x - w // 2, y_top, x - w // 2 + 3, y_base, col("cloth_cream", 4))
        rect(c, x + w // 2 - 3, y_top, x + w // 2, y_base, col("cloth_cream", 1))
        rect(c, x - w // 2 - 2, y_top - 4, x + w // 2 + 2, y_top, col("stone_warm", 4))
        rect(c, x - w // 2 - 2, y_base - 4, x + w // 2 + 2, y_base, col("stone_warm", 3))


def _pediment(c, cx, half, y, h, mat_col=("stone_warm", 3)):
    for i in range(h):
        k = int(half * (1 - i / h))
        rect(c, cx - k, y - i, cx + k, y - i + 1, col(*mat_col))
    rect(c, cx - half, y, cx + half, y + 3, col("stone_warm", 4))
    rect(c, cx - half, y + 3, cx + half, y + 5, col("stone_warm", 1))
    disc(c, cx, y - h // 3, 6, 6, col("stone_warm", 2))
    disc(c, cx, y - h // 3, 4, 4, col("gold", 3))


def palace():
    """The Governor's Palace: two wings, a three-storey centre with a six-column portico, a copper dome and a grand double stair."""
    c = canvas(GW, GH)
    W = 368
    x0, x1 = GPX - W // 2, GPX + W // 2
    wing_h = 130
    y0 = GPY - wing_h
    wall(c, x0, y0, x1, GPY, "white", 14)
    rect(c, x0, GPY - 14, x1, GPY, col("stone_warm", 3))
    rect(c, x0, GPY - 14, x1, GPY - 13, col("stone_warm", 4))
    rect(c, x0, y0, x1, y0 + 4, col("stone_warm", 4))
    rect(c, x0, y0 + 4, x1, y0 + 7, col("stone_warm", 2))
    rect(c, x0, GPY - 14 - 48, x1, GPY - 14 - 46, col("stone_warm", 4))
    for i in range(11):
        cx = x0 + 18 + i * 33
        if abs(cx - GPX) < 70:
            continue
        for f, yb in enumerate((GPY - 14, GPY - 14 - 50)):
            window(c, cx - 7, yb - 36, 14, 26, hsh(i, f, 5) < 0.85, shutter=("cloth_blue", 2), arch=True)
    for xa, xb in ((x0, x0 + 128), (x1 - 128, x1)):                                    # wing roofs
        roof(c, xa, xb, y0, 40, "teal", "hip", 7, overhang=6, tile_w=10)
        chimney(c, xa + 20, y0 - 22, 16); chimney(c, xb - 30, y0 - 22, 16)
    my0 = GPY - 190
    mx0, mx1 = GPX - 82, GPX + 82
    wall(c, mx0, my0, mx1, GPY - 14, "white", 15)
    rect(c, mx0, my0, mx1, my0 + 4, col("stone_warm", 4))
    rect(c, mx0, my0 + 4, mx1, my0 + 7, col("stone_warm", 2))
    for f, yb in enumerate((GPY - 14, GPY - 14 - 50, GPY - 14 - 100)):
        if f == 2:
            for dx in (-60, -20, 20, 60):
                window(c, GPX + dx - 7, yb - 36, 14, 26, True, shutter=("cloth_blue", 2), arch=True)
        elif f == 1:
            for dx in (-60, 60):
                window(c, GPX + dx - 7, yb - 36, 14, 26, True, shutter=("cloth_blue", 2), arch=True)
            window(c, GPX - 11, yb - 38, 22, 30, True, shutter=None, arch=True)
            balcony(c, GPX - 30, GPX + 30, yb - 4)
    door(c, GPX - 12, GPY - 14, 24, 40, color=("wood", 1))
    _columns(c, [GPX + d for d in (-66, -40, -14, 14, 40, 66)], GPY - 14 - 120, GPY - 14, 9)
    rect(c, GPX - 80, GPY - 14 - 130, GPX + 80, GPY - 14 - 120, col("stone_warm", 3))
    rect(c, GPX - 80, GPY - 14 - 130, GPX + 80, GPY - 14 - 128, col("stone_warm", 4))
    _pediment(c, GPX, 86, GPY - 14 - 131, 24)
    for i in range(8):                                                                  # double stair
        rect(c, GPX - 64 - i * 3, GPY - 14 + i * 0, GPX + 64 + i * 3, GPY - 12 + 0, col("stone_warm", 3))
    shift(c, x0, y0, x0 + 3, GPY, 1)
    shift(c, mx0, my0, mx0 + 3, GPY, 1)
    # dome
    dcx, dr, dy = GPX, 52, my0 - 4
    rect(c, dcx - 44, dy - 22, dcx + 44, dy, col("cloth_cream", 3))
    rect(c, dcx - 44, dy - 22, dcx - 40, dy, col("cloth_cream", 4))
    for dx in (-30, -10, 10, 30):
        window(c, dcx + dx - 4, dy - 18, 8, 12, True, sill=False, arch=True)
    rect(c, dcx - 48, dy - 26, dcx + 48, dy - 22, col("stone_warm", 4))
    for yy in range(dr):
        k = int(np.sqrt(max(dr * dr - (yy) ** 2, 0)) * 0.86)
        yk = dy - 26 - yy
        for x in range(dcx - k, dcx + k):
            t = (x - (dcx - k)) / max(2 * k, 1)
            idx = 4 if t < 0.15 else (3 if t < 0.5 else (2 if t < 0.8 else 1))
            if (yy % 6) == 0 or ((x - dcx) % 14 == 0):
                idx = max(idx - 1, 0)
            px(c, x, yk, col("roof_teal", idx))
    rect(c, dcx - 6, dy - 26 - dr - 14, dcx + 6, dy - 26 - dr, col("cloth_cream", 3))
    rect(c, dcx - 3, dy - 26 - dr - 14, dcx + 3, dy - 26 - dr - 12, col("gold", 3))
    flag(c, dcx, dy - 26 - dr - 40, 30, 18, ("cloth_blue", 3), ("gold", 3))
    flag(c, x0 + 60, y0 - 70, 24, 14, ("cloth_blue", 3), ("gold", 3))
    flag(c, x1 - 60, y0 - 70, 24, 14, ("cloth_blue", 3), ("gold", 3))
    return finish(c)


def town_hall():
    """Town Hall: a stone hall with an arcaded front and a tall clock tower (the clock shows the game time of day in spirit only)."""
    c = canvas(GW, GH)
    W = 300
    x0, x1 = GPX - W // 2, GPX + W // 2
    h = 118
    y0 = GPY - h
    wall(c, x0, y0, x1, GPY, "stone", 22)
    rect(c, x0, GPY - 10, x1, GPY, col("stone_warm", 2))
    rect(c, x0, y0, x1, y0 + 4, col("stone_warm", 4))
    rect(c, x0, y0 + 4, x1, y0 + 7, col("stone_warm", 1))
    for i in range(7):                                                                  # ground arcade: arches
        cx = x0 + 22 + i * 42
        rect(c, cx - 14, GPY - 52, cx + 14, GPY, col("hull_oak", 0))
        for k in range(14):
            hh = int(np.sqrt(max(14 * 14 - k * k, 0)))
            rect(c, cx - k, GPY - 52 - hh, cx - k + 1, GPY - 52, col("hull_oak", 0))
            rect(c, cx + k, GPY - 52 - hh, cx + k + 1, GPY - 52, col("hull_oak", 0))
        rect(c, cx - 16, GPY - 52, cx - 14, GPY, col("stone_warm", 4))
        rect(c, cx + 14, GPY - 52, cx + 16, GPY, col("stone_warm", 1))
        if i in (1, 3, 5):
            rect(c, cx - 8, GPY - 30, cx + 8, GPY, col("wood", 2))
    for i in range(7):
        cx = x0 + 22 + i * 42
        window(c, cx - 7, y0 + 30, 14, 22, hsh(i, 2, 9) < 0.9, shutter=("cloth_red", 2), arch=True)
    roof(c, x0, x1, y0, 44, "red", "gable", 9, overhang=8, tile_w=10)
    chimney(c, x0 + 40, y0 - 20, 18)
    # clock tower
    tx0, tx1 = GPX + 60, GPX + 112
    ty = y0 - 6
    wall(c, tx0, ty - 110, tx1, ty, "stone", 23)
    shift(c, tx0, ty - 110, tx0 + 3, ty, 1)
    shift(c, tx1 - 4, ty - 110, tx1, ty, -1)
    rect(c, tx0 - 3, ty - 112, tx1 + 3, ty - 108, col("stone_warm", 4))
    disc(c, (tx0 + tx1) // 2, ty - 82, 17, 17, col("stone_warm", 4))
    disc(c, (tx0 + tx1) // 2, ty - 82, 14, 14, col("cloth_cream", 4))
    cx, cy = (tx0 + tx1) // 2, ty - 82
    for a in range(12):
        ang = a * np.pi / 6
        px(c, int(cx + 12 * np.sin(ang)), int(cy - 12 * np.cos(ang)), col("iron", 1))
    line(c, cx, cy, cx + 1, cy - 9, col("iron", 0)); line(c, cx, cy, cx + 7, cy + 3, col("iron", 0))
    window(c, cx - 5, ty - 54, 10, 14, True, sill=False, arch=True)
    rect(c, tx0 - 4, ty - 124, tx1 + 4, ty - 112, col("stone_warm", 3))
    for x in (tx0, tx1 - 6):
        rect(c, x, ty - 150, x + 6, ty - 124, col("stone_warm", 3))
    rect(c, tx0 + 6, ty - 150, tx1 - 6, ty - 124, col("hull_oak", 0))
    rect(c, cx - 5, ty - 144, cx + 5, ty - 130, col("gold", 3))
    for i in range(34):                                                                 # spire
        k = int((tx1 - tx0 + 8) * 0.5 * (1 - i / 34.0))
        rect(c, cx - k, ty - 150 - i, cx + k, ty - 149 - i, col("roof_teal", 2 if i % 4 else 3))
    flag(c, cx, ty - 150 - 34 - 18, 18, 12, ("cloth_red", 3), ("gold", 3))
    door(c, GPX - 14, GPY, 28, 38, color=("wood", 1), frame="stone_warm") if False else None
    return finish(c)


def customs_house():
    """Customs House: the harbour's tax office: three storeys, a colonnade, scales over the door, a flagpole."""
    c = canvas(GW, GH)
    W = 250
    x0, x1 = GPX - W // 2, GPX + W // 2
    h = 140
    y0 = GPY - h
    wall(c, x0, y0, x1, GPY, "plaster", 31)
    rect(c, x0, GPY - 12, x1, GPY, col("stone_warm", 3))
    rect(c, x0, y0, x1, y0 + 3, col("stone_warm", 4))
    for f in range(3):
        yb = GPY - 12 - f * 44
        for i in range(6):
            cx = x0 + 22 + i * 41
            if f == 0 and i in (2, 3):
                continue
            window(c, cx - 7, yb - 34, 14, 22, hsh(i, f, 4) < 0.85, shutter=("grass", 2), arch=True)
        if f:
            rect(c, x0, yb - 1, x1, yb + 1, col("stone_warm", 4))
    door(c, GPX - 14, GPY - 12, 28, 40, color=("wood", 1))
    _columns(c, [GPX - 40, GPX + 40], GPY - 12 - 70, GPY - 12, 8)
    rect(c, GPX - 46, GPY - 12 - 78, GPX + 46, GPY - 12 - 70, col("stone_warm", 3))
    hanging_sign(c, GPX + 66, GPY - 90, "scales", w=16, h=14)
    roof(c, x0, x1, y0, 40, "red", "hip", 12, overhang=8, tile_w=10)
    chimney(c, x0 + 34, y0 - 18, 18); chimney(c, x1 - 50, y0 - 18, 18)
    flag(c, x0 + 14, y0 - 54, 40, 16, ("cloth_red", 3), ("cloth_cream", 4))
    return finish(c)


def guild_hall():
    """The Merchants' Exchange: a hall on an open arcade, striped awnings, a bell cote."""
    c = canvas(GW, GH)
    W = 240
    x0, x1 = GPX - W // 2, GPX + W // 2
    h = 120
    y0 = GPY - h
    wall(c, x0, y0, x1, GPY, "brick", 41)
    rect(c, x0, GPY - 10, x1, GPY, col("stone_warm", 3))
    rect(c, x0, y0, x1, y0 + 3, col("stone_warm", 4))
    rect(c, x0 + 14, GPY - 62, x1 - 14, GPY - 10, col("hull_oak", 0))                  # open arcade
    for i in range(6):
        cx = x0 + 14 + i * (W - 28) // 5
        rect(c, cx - 4, GPY - 62, cx + 4, GPY - 10, col("stone_warm", 3))
        rect(c, cx - 4, GPY - 62, cx - 2, GPY - 10, col("stone_warm", 4))
    rect(c, x0 + 10, GPY - 68, x1 - 10, GPY - 62, col("stone_warm", 4))
    for i in range(5):
        cx = x0 + 14 + (i + 0.5) * (W - 28) // 5
        rect(c, int(cx) - 6, GPY - 30, int(cx) + 6, GPY - 10, col("wood", 2)) if i % 2 == 0 else rect(c, int(cx) - 8, GPY - 24, int(cx) + 8, GPY - 10, col("cloth_red", 3))
    for i in range(5):
        cx = x0 + 28 + i * 46
        window(c, cx - 7, y0 + 24, 14, 20, hsh(i, 4, 8) < 0.9, shutter=("cloth_cream", 3), arch=True)
    roof(c, x0, x1, y0, 40, "slate", "gable", 6, overhang=8, tile_w=10)
    rect(c, GPX - 9, y0 - 70, GPX + 9, y0 - 28, col("stone_warm", 3))
    rect(c, GPX - 9, y0 - 70, GPX - 6, y0 - 28, col("stone_warm", 4))
    rect(c, GPX - 5, y0 - 62, GPX + 5, y0 - 44, col("hull_oak", 0))
    rect(c, GPX - 3, y0 - 58, GPX + 3, y0 - 50, col("gold", 3))
    for i in range(14):
        k = 11 - int(11 * i / 14)
        rect(c, GPX - k, y0 - 70 - i, GPX + k, y0 - 69 - i, col("roof_teal", 2))
    hanging_sign(c, x1 + 2, y0 + 40, "scales")
    return finish(c)


def big_warehouse(mat="brick", rf="slate", seed=3):
    c = canvas(GW, GH)
    W = 330
    x0, x1 = GPX - W // 2, GPX + W // 2
    h = 120
    y0 = GPY - h
    wall(c, x0, y0, x1, GPY, mat, seed)
    rect(c, x0, GPY - 10, x1, GPY, col("stone_warm", 2))
    for i in range(3):
        cx = x0 + 55 + i * 110
        rect(c, cx - 28, GPY - 70, cx + 28, GPY, col("wood", 1))
        rect(c, cx - 26, GPY - 68, cx + 26, GPY, col("wood", 2))
        for xx in range(cx - 26, cx + 26, 5):
            rect(c, xx, GPY - 68, xx + 1, GPY, col("wood", 1))
        line(c, cx - 26, GPY - 68, cx + 25, GPY - 1, col("wood", 1)); line(c, cx + 25, GPY - 68, cx - 26, GPY - 1, col("wood", 1))
        rect(c, cx - 1, GPY - 68, cx + 1, GPY, col("iron", 1))
        window(c, cx - 5, y0 + 12, 10, 14, hsh(i, seed) < 0.6, sill=False, bars=True)
        rect(c, cx - 9, y0 + 34, cx + 9, y0 + 52, col("wood", 1))                       # loft door
        rect(c, cx - 7, y0 + 36, cx + 7, y0 + 52, col("wood", 2))
    roof(c, x0, x1, y0, 46, rf, "gable", seed, overhang=9, tile_w=10)
    for x in (x0 + 60, x1 - 60):
        hoist(c, x, y0 + 6)
    return finish(c)


def barracks():
    c = canvas(GW, GH)
    W = 280
    x0, x1 = GPX - W // 2, GPX + W // 2
    h = 112
    y0 = GPY - h
    wall(c, x0, y0, x1, GPY, "greystone", 52)
    rect(c, x0, GPY - 10, x1, GPY, col("stone_cool", 2))
    rect(c, x0, y0, x1, y0 + 4, col("stone_cool", 4))
    for i in range(7):
        cx = x0 + 22 + i * 40
        if i == 3:
            rect(c, cx - 16, GPY - 64, cx + 16, GPY, col("stone_cool", 1))
            rect(c, cx - 13, GPY - 61, cx + 13, GPY, col("wood", 1))
            for xx in range(cx - 13, cx + 13, 6):
                rect(c, xx, GPY - 61, xx + 1, GPY, col("iron", 1))
            continue
        for f, yb in enumerate((GPY - 10, GPY - 10 - 50)):
            window(c, cx - 5, yb - 34, 10, 20, hsh(i, f, 9) < 0.8, sill=True, bars=(f == 0))
    roof(c, x0, x1, y0, 42, "red", "hip", 14, overhang=7, tile_w=10)
    for xx in (x0 + 12, x1 - 12):
        rect(c, xx - 12, y0 - 36, xx + 12, y0 - 4, col("stone_cool", 3))
        rect(c, xx - 12, y0 - 44, xx + 12, y0 - 36, col("stone_cool", 4))
        for k in range(0, 24, 8):
            rect(c, xx - 12 + k, y0 - 52, xx - 12 + k + 5, y0 - 44, col("stone_cool", 3))
    flag(c, GPX, y0 - 70, 30, 16, ("cloth_red", 3), ("gold", 3))
    return finish(c)


def counting_house():
    c = canvas(GW, GH)
    W = 210
    x0, x1 = GPX - W // 2, GPX + W // 2
    h = 132
    y0 = GPY - h
    wall(c, x0, y0, x1, GPY, "stone", 61)
    rect(c, x0, GPY - 12, x1, GPY, col("stone_warm", 2))
    for f in range(3):
        yb = GPY - 12 - f * 40
        for i in range(5):
            cx = x0 + 22 + i * 41
            if f == 0 and i == 2:
                continue
            window(c, cx - 6, yb - 30, 12, 20, hsh(i, f, 6) < 0.85, shutter=("cloth_blue", 2), arch=(f == 0), bars=(f == 0))
        if f:
            rect(c, x0, yb - 1, x1, yb + 1, col("stone_warm", 4))
    door(c, GPX - 13, GPY - 12, 26, 38, color=("wood", 1))
    rect(c, GPX - 20, GPY - 12 - 56, GPX + 20, GPY - 12 - 52, col("stone_warm", 4))
    hanging_sign(c, x1 + 2, y0 + 56, "key")
    roof(c, x0, x1, y0, 42, "greenslate", "hip", 16, overhang=8, tile_w=10)
    chimney(c, x0 + 28, y0 - 20, 18)
    return finish(c)


def shipyard_shed():
    c = canvas(GW, GH)
    W = 320
    x0, x1 = GPX - W // 2, GPX + W // 2
    h = 108
    y0 = GPY - h
    wall(c, x0, y0, x1, GPY, "timber", 71)
    rect(c, x0 + 40, y0 + 18, x1 - 40, GPY, col("hull_oak", 0))                         # open slip
    rect(c, x0 + 40, y0 + 18, x1 - 40, y0 + 24, col("hull_oak", 1))
    # the rib of a hull under construction
    for i in range(7):
        xx = x0 + 70 + i * 28
        line(c, xx, GPY - 4, xx + 6, GPY - 60, col("wood", 3))
        line(c, xx + 1, GPY - 4, xx + 7, GPY - 60, col("wood", 2))
    rect(c, x0 + 60, GPY - 8, x1 - 60, GPY - 4, col("wood", 4))
    rect(c, x0 + 60, GPY - 8, x1 - 60, GPY - 6, col("wood", 3))
    for x in (x0 + 4, x0 + 36, x1 - 40, x1 - 7):
        rect(c, x, y0, x + 4, GPY, col("wood", 3)); rect(c, x, y0, x + 1, GPY, col("wood", 4))
    roof(c, x0, x1, y0, 52, "brown", "gable", 8, overhang=10, tile_w=12)
    hanging_sign(c, x1 + 10, y0 + 30, "hammer")
    flag(c, x0 + 20, y0 - 90, 26, 14, ("cloth_blue", 3), ("cloth_cream", 4))
    return finish(c)


def fort_bastion():
    """Anvil Battery: a stone bastion on the east shore with three embrasures and iron cannon muzzles."""
    c = canvas(GW, GH)
    W = 330
    x0, x1 = GPX - W // 2, GPX + W // 2
    h = 86
    y0 = GPY - h
    wall(c, x0, y0, x1, GPY, "greystone", 81)
    shift(c, x0, y0, x1, y0 + 3, 1)
    rect(c, x0, y0 - 6, x1, y0 + 3, col("stone_cool", 4))
    rect(c, x0, y0 + 3, x1, y0 + 6, col("stone_cool", 1))
    for i in range(5):
        cx = x0 + 40 + i * 62
        rect(c, cx - 10, y0 + 20, cx + 10, y0 + 46, col("hull_oak", 0))
        rect(c, cx - 14, y0 + 38, cx + 14, y0 + 46, col("iron", 3))
        rect(c, cx - 10, y0 + 38, cx + 10, y0 + 46, col("iron", 2))
        rect(c, cx - 3, y0 + 40, cx + 3, y0 + 44, col("iron", 0))
    for x in range(x0, x1 - 12, 36):
        rect(c, x + 4, y0 - 22, x + 22, y0 - 6, col("stone_cool", 3))
        rect(c, x + 4, y0 - 22, x + 22, y0 - 20, col("stone_cool", 4))
    rect(c, x0, GPY - 10, x1, GPY, col("stone_cool", 2))
    flag(c, GPX, y0 - 70, 50, 20, ("cloth_red", 3), ("gold", 3))
    return finish(c)


def sprite_dock_crane():
    c = canvas(128, 176)
    px0, py0 = 64, 170
    rect(c, 48, py0 - 90, 60, py0, col("wood", 2)); rect(c, 48, py0 - 90, 51, py0, col("wood", 3))
    rect(c, 60, py0 - 90, 72, py0, col("wood", 1))
    for k in range(5):
        line(c, 48, py0 - 10 - k * 18, 71, py0 - 28 - k * 18, col("wood", 1))
    rect(c, 8, py0 - 100, 118, py0 - 92, col("wood", 3)); rect(c, 8, py0 - 100, 118, py0 - 98, col("wood", 4))
    line(c, 56, py0 - 124, 14, py0 - 100, col("wood", 2)); line(c, 57, py0 - 124, 15, py0 - 100, col("wood", 1))
    rect(c, 52, py0 - 126, 62, py0 - 112, col("wood", 2))
    rect(c, 18, py0 - 92, 19, py0 - 62, col("sand", 3))
    rect(c, 12, py0 - 62, 26, py0 - 48, col("wood", 3)); rect(c, 12, py0 - 62, 26, py0 - 60, col("wood", 4))
    rect(c, 12, py0 - 50, 26, py0 - 48, col("iron", 2))
    rect(c, 44, py0 - 8, 76, py0, col("stone_warm", 2))
    return finish(c)


def sprite_fountain():
    c = canvas(128, 160)
    cx, by = 64, 150
    disc(c, cx, by - 8, 54, 20, col("stone_warm", 3))
    disc(c, cx, by - 12, 50, 17, col("stone_warm", 4))
    disc(c, cx, by - 12, 44, 14, col("sea_deep" if False else "lagoon", 2))
    disc(c, cx - 12, by - 14, 14, 3, col("lagoon", 3)); disc(c, cx + 14, by - 10, 10, 2, col("lagoon", 4))
    rect(c, cx - 6, by - 56, cx + 6, by - 14, col("stone_warm", 3)); rect(c, cx - 6, by - 56, cx - 3, by - 14, col("stone_warm", 4))
    disc(c, cx, by - 46, 22, 7, col("stone_warm", 3)); disc(c, cx, by - 48, 20, 5, col("lagoon", 3))
    rect(c, cx - 3, by - 86, cx + 3, by - 48, col("stone_warm", 4))
    disc(c, cx, by - 90, 9, 5, col("stone_warm", 4))
    for a in (-1, 1):                                                                    # water arcs
        for i in range(10):
            yy = by - 92 + int((i * 0.45) ** 2)
            px(c, cx + a * (i * 2 + 2), yy, col("lagoon", 4)); px(c, cx + a * (i * 2 + 2), yy + 1, col("ice", 3))
    rect(c, cx, by - 100, cx + 1, by - 88, col("ice", 4))
    return finish(c)


def sprite_anvil_monument():
    """The Anvil: a giant iron anvil on a stepped plinth in Customs Square, with a ship's bell."""
    c = canvas(128, 160)
    cx, by = 64, 152
    rect(c, cx - 40, by - 12, cx + 40, by, col("stone_warm", 3)); rect(c, cx - 40, by - 12, cx + 40, by - 10, col("stone_warm", 4))
    rect(c, cx - 32, by - 24, cx + 32, by - 12, col("stone_warm", 2)); rect(c, cx - 32, by - 24, cx + 32, by - 22, col("stone_warm", 4))
    rect(c, cx - 22, by - 60, cx + 22, by - 24, col("stone_warm", 3)); rect(c, cx - 22, by - 60, cx - 18, by - 24, col("stone_warm", 4))
    rect(c, cx + 18, by - 60, cx + 22, by - 24, col("stone_warm", 1))
    rect(c, cx - 10, by - 70, cx + 10, by - 60, col("iron", 2))                          # waist
    rect(c, cx - 30, by - 90, cx + 30, by - 70, col("iron", 3)); rect(c, cx - 30, by - 90, cx + 30, by - 87, col("iron", 4))
    for i in range(18):                                                                 # horn
        rect(c, cx + 30 + i, by - 90 + i // 3, cx + 31 + i, by - 76 + i // 2, col("iron", 3 if i < 9 else 2))
    rect(c, cx - 36, by - 86, cx - 30, by - 76, col("iron", 2))
    rect(c, cx - 8, by - 104, cx + 8, by - 90, col("gold", 3)); rect(c, cx - 8, by - 104, cx - 4, by - 90, col("gold", 4))  # ship's bell on it
    rect(c, cx - 2, by - 110, cx + 2, by - 104, col("iron", 2))
    return finish(c)


def sprite_statue():
    c = canvas(128, 160)
    cx, by = 64, 152
    rect(c, cx - 22, by - 10, cx + 22, by, col("stone_warm", 3)); rect(c, cx - 16, by - 44, cx + 16, by - 10, col("stone_warm", 4))
    rect(c, cx - 16, by - 44, cx - 12, by - 10, col("stone_warm", 4)); rect(c, cx + 12, by - 44, cx + 16, by - 10, col("stone_warm", 2))
    rect(c, cx - 8, by - 56, cx + 8, by - 44, col("iron", 3))                           # legs
    rect(c, cx - 10, by - 80, cx + 10, by - 56, col("iron", 3)); rect(c, cx - 10, by - 80, cx - 6, by - 56, col("iron", 4))
    disc(c, cx, by - 88, 6, 7, col("iron", 4))
    rect(c, cx - 10, by - 94, cx + 10, by - 90, col("iron", 2)); rect(c, cx - 7, by - 100, cx + 7, by - 94, col("iron", 2))
    rect(c, cx + 10, by - 78, cx + 20, by - 74, col("iron", 3)); rect(c, cx + 18, by - 100, cx + 20, by - 74, col("iron", 4))   # raised telescope arm
    return finish(c)


def smalls():
    S = []
    add = lambda name, w, d, h, arr: S.append((name, w, d, h, arr))
    add("cottage_thatch", 7.0, 5.5, 5.0, house(7.0, 1, "plaster", "thatch", "gable", 32, shutter=("cloth_blue", 2), seed=1, door_at=0.3, dorm=0))
    add("cottage_tile", 7.4, 5.5, 5.2, house(7.4, 1, "sand", "red", "gable", 32, shutter=("grass", 2), seed=2, door_at=0.7))
    add("fisher_cottage", 8.0, 5.5, 5.5, house(8.0, 1, "timber", "dark", "gable", 34, shutter=("cloth_cream", 3), seed=3, door_at=0.5, dorm=1, planks=True))
    add("fisher_cottage_tar", 7.6, 5.5, 5.5, house(7.6, 1, "tar", "brown", "gable", 32, shutter=("cloth_red", 2), seed=4, door_at=0.25, dorm=1, planks=True))
    add("house_plaster", 8.2, 6.5, 8.0, house(8.2, 2, "plaster", "red", "hip", 36, shutter=("cloth_blue", 2), seed=5, dorm=1))
    add("house_half", 8.6, 6.5, 8.4, house(8.6, 2, "half", "slate", "gable", 38, shutter=None, seed=6, dorm=2, balc=False))
    add("house_brick", 8.0, 6.5, 8.0, house(8.0, 2, "brick", "slate", "gable", 36, shutter=("cloth_cream", 3), seed=7, dorm=1))
    add("house_rose", 7.6, 6.5, 8.0, house(7.6, 2, "rose", "brown", "hip", 36, shutter=("cloth_cream", 3), seed=8))
    add("house_blue", 7.6, 6.5, 8.0, house(7.6, 2, "blue", "red", "hip", 36, shutter=("cloth_cream", 3), seed=9, dorm=1))
    add("house_green", 7.8, 6.5, 8.0, house(7.8, 2, "green", "slate", "gable", 36, shutter=("cloth_cream", 3), seed=10))
    add("house_ochre", 8.0, 6.5, 8.0, house(8.0, 2, "ochre", "red", "gable", 36, shutter=("cloth_blue", 2), seed=11, dorm=1))
    add("tall_brick", 5.8, 6.0, 12.0, tall_townhouse(5.8, "brick", 3))
    add("tall_white", 5.8, 6.0, 12.0, tall_townhouse(5.8, "white", 4))
    add("tall_sand", 6.2, 6.0, 12.0, tall_townhouse(6.2, "sand", 5))
    add("tall_rose", 5.6, 6.0, 12.0, tall_townhouse(5.6, "rose", 6))
    add("tall_blue", 6.0, 6.0, 12.0, tall_townhouse(6.0, "blue", 7))
    add("shop_baker", 8.4, 6.5, 8.0, house(8.4, 2, "plaster", "red", "gable", 34, shutter=("cloth_red", 2), seed=12, shop=(("cloth_red", 3), ("cloth_cream", 4)), sign=("loaf", "r"), door_at=0.82))
    add("shop_chandler", 8.4, 6.5, 8.0, house(8.4, 2, "sand", "slate", "gable", 34, shutter=("cloth_blue", 2), seed=13, shop=(("cloth_blue", 3), ("cloth_cream", 4)), sign=("rope", "r"), door_at=0.82))
    add("shop_cloth", 8.4, 6.5, 8.0, house(8.4, 2, "white", "brown", "hip", 34, shutter=("cloth_red", 2), seed=14, shop=(("gold", 3), ("cloth_cream", 4)), sign=("cloth", "r"), door_at=0.18))
    add("shop_cooper", 8.4, 6.5, 8.0, house(8.4, 2, "timber", "dark", "gable", 34, shutter=("cloth_cream", 3), seed=15, shop=(("grass", 3), ("cloth_cream", 4)), sign=("barrel", "r"), door_at=0.18, planks=True))
    add("shop_sailmaker", 8.4, 6.5, 8.0, house(8.4, 2, "plaster", "teal", "gable", 34, shutter=("cloth_blue", 2), seed=16, shop=(("cloth_blue", 3), ("cloth_red", 3)), sign=("sail", "r"), door_at=0.82))
    add("shop_fishmonger", 8.4, 6.5, 8.0, house(8.4, 2, "blue", "slate", "gable", 34, shutter=("cloth_cream", 3), seed=17, shop=(("cloth_blue", 3), ("cloth_cream", 4)), sign=("fish", "r"), door_at=0.5))
    add("shop_provisioner", 8.4, 6.5, 8.0, house(8.4, 2, "rose", "red", "gable", 34, shutter=("grass", 2), seed=18, shop=(("grass", 3), ("cloth_cream", 4)), sign=("barrel", "r"), door_at=0.82))
    add("smithy", 9.0, 6.5, 5.5, workshop(9.0, "smith", 2))
    add("carpenter", 9.0, 6.5, 5.5, workshop(9.0, "carpenter", 3))
    add("warehouse_timber", 12.0, 8.0, 9.5, warehouse(12.0, "timber", "slate", 5, 2, 2))
    add("warehouse_brick", 12.0, 8.0, 9.5, warehouse(12.0, "brick", "red", 6, 2, 2))
    add("warehouse_tar", 10.0, 8.0, 8.0, warehouse(10.0, "tar", "brown", 7, 1, 2))
    add("tavern_anchor", 13.0, 8.0, 11.0, tavern(13.0, 9))
    add("inn_gilded", 11.0, 7.5, 10.0, house(11.0, 2, "ochre", "red", "hip", 40, shutter=("cloth_red", 2), seed=19, sign=("mug", "r"), balc=True, dorm=2, door_at=0.5))
    add("rowhouse", 12.6, 7.0, 7.5, rowhouse())
    add("mansion_white", 14.0, 9.0, 10.5, mansion(14.0, "white", "teal", 4))
    add("mansion_rose", 14.0, 9.0, 10.5, mansion(14.0, "rose", "slate", 5))
    add("mansion_ochre", 13.0, 9.0, 10.0, mansion(13.0, "ochre", "red", 6, columns=False))
    add("mansion_stone", 14.0, 9.0, 10.5, mansion(14.0, "stone", "greenslate", 7, columns=True))
    add("wall_straight", 13.0, 2.4, 5.5, wall_straight())
    add("wall_tower", 6.4, 6.4, 9.5, wall_tower())
    add("wall_gate", 12.4, 6.0, 8.0, gatehouse())
    add("wall_post", 2.6, 2.4, 4.5, wall_post())
    add("keeper_house", 6.5, 5.0, 5.0, lighthouse_keeper())
    add("dock_crane", 6.0, 3.0, 11.0, None)
    return S


def grands():
    G = []
    add = lambda name, w, d, h, arr: G.append((name, w, d, h, arr))
    add("palace", 25.5, 14.0, 16.0, palace())
    add("town_hall", 20.8, 10.0, 11.0, town_hall())
    add("customs_house", 17.4, 10.0, 10.0, customs_house())
    add("guild_hall", 16.7, 9.0, 8.5, guild_hall())
    add("warehouse_big_brick", 22.9, 10.0, 9.0, big_warehouse("brick", "slate", 3))
    add("warehouse_big_timber", 22.9, 10.0, 9.0, big_warehouse("timber", "red", 4))
    add("barracks", 19.4, 9.0, 9.0, barracks())
    add("counting_house", 14.6, 8.0, 10.5, counting_house())
    add("shipyard_shed", 22.2, 10.0, 8.0, shipyard_shed())
    add("fort_bastion", 22.9, 6.0, 6.5, fort_bastion())
    return G


def civics():
    C = []
    add = lambda name, w, d, h, arr: C.append((name, w, d, h, arr))
    add("fountain", 7.0, 7.0, 6.0, sprite_fountain())
    add("anvil_monument", 5.5, 4.5, 7.5, sprite_anvil_monument())
    add("statue", 3.0, 3.0, 7.0, sprite_statue())
    add("dock_crane", 6.0, 3.0, 11.0, sprite_dock_crane())
    return C


def atlas(items, cw, ch, cols, pivot):
    rows = (len(items) + cols - 1) // cols
    im = Image.new("RGBA", (cw * cols, ch * rows), (0, 0, 0, 0))
    for i, (_n, _w, _d, _h, arr) in enumerate(items):
        if arr is None:
            continue
        cell = Image.fromarray(arr, "RGBA")
        # recentre the pivot: the arrays are authored with the pivot at (SPX, SPY) or (GPX, GPY) or (64, 150..170)
        im.paste(cell, ((i % cols) * cw, (i // cols) * ch))
    return im, rows


if __name__ == "__main__":
    import sys
    from pathlib import Path
    S, G, C = smalls(), grands(), civics()
    out = Path("/tmp/city_art")
    out.mkdir(exist_ok=True)
    for name, im in (("small", atlas(S, SW, SH, 6, 0)[0]), ("grand", atlas(G, GW, GH, 3, 0)[0]), ("civic", atlas(C, 128, 176, 4, 0)[0])):
        bg = Image.new("RGBA", im.size, (130, 118, 92, 255))
        bg.alpha_composite(im)
        bg.convert("RGB").save(out / f"{name}.png")
        print(name, im.size)
