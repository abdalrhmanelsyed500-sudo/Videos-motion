"""CP-1 art for the Anvil Harbor "Fish Row" district: market stalls, fish goods, fishing boats, moored ships, markers and
the people of the port. Hand-drawn with numpy from the project palette (game/data/look/palette.json), prototype art.

DENSITY. Everything here except the moored ships is drawn at the pirate's density: 14.4 px per metre, so one sprite pixel is
one screen pixel at the on-foot zoom (4 x 3.6 px/m), exactly like the hero (24 x 32 px = 1.7 x 2.2 m). The moored ships are the
existing 22 m sloop hull sheet (3.6 px/m) recoloured, like the harbour buildings. docs/CP1_CAPITAL_PORT.md section 3 explains
why the buildings of H2D-1 stay at 3.6 px/m for now (open decision for the user).

Outputs (game/h2d/art/): port_stall_atlas.png (64 x 64 cells, 4 x 4), port_misc_atlas.png (64 x 64, 4 x 4), port_big_atlas.png
(192 x 112, 4 x 2), port_ships_atlas.png (112 x 112, 4 x 1), port_npc_atlas.png (24 x 32; one look = 4 facings x 4 frames).
All NPCs are men (project content rule 1 applies to the crew; no woman is drawn in this slice, see the doc's open question).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bake_harbor as BH  # noqa: E402
import bake_island as BI  # noqa: E402

ART = BH.ART
col = BH.col
CW, CH = 64, 64
PIVOT = (32, 60)
BW, BHT = 192, 112
BIG_PIVOT = (96, 100)
NPC_W, NPC_H = 24, 32
NPC_PIVOT = (12, 30)


# ---- tiny drawing kit ------------------------------------------------------------------------------------------------
def new(w=CW, h=CH):
    return np.zeros((h, w, 4), np.uint8)


def rect(c, x0, y0, x1, y1, colr):
    """Inclusive-exclusive rectangle."""
    c[max(y0, 0):max(y1, 0), max(x0, 0):max(x1, 0)] = colr


def px(c, x, y, colr):
    if 0 <= y < c.shape[0] and 0 <= x < c.shape[1]:
        c[y, x] = colr


def line(c, x0, y0, x1, y1, colr):
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        px(c, x0, y0, colr)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def disc(c, cx, cy, rx, ry, colr):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                px(c, x, y, colr)


def finish(c, outline="iron"):
    c[..., 3] = np.where(c[..., 3] > 127, 255, 0)
    BI._outline(c, outline)
    return c


def shaded(c, x0, y0, x1, y1, ramp, base=2):
    """A box face with a light left edge and a dark right edge: three ramp steps."""
    rect(c, x0, y0, x1, y1, col(ramp, base))
    rect(c, x0, y0, x0 + 1, y1, col(ramp, base + 1))
    rect(c, x1 - 1, y0, x1, y1, col(ramp, base - 1))


def fish(c, x, y, flip=False, body=("iron", 3), back=("iron", 2), belly=("iron", 4)):
    """A 9 x 4 px fish: back, body, belly, forked tail, one dark eye."""
    rows = [(2, 7, back), (1, 8, body), (1, 8, body), (2, 7, belly)]
    for dy, (a, b, cc) in enumerate(rows):
        for dx in range(a, b):
            px(c, x + (8 - dx if flip else dx), y + dy, col(*cc))
    for dy, (a, b) in enumerate([(7, 9), (8, 9), (8, 9), (7, 9)]):
        for dx in range(a, b):
            px(c, x + (8 - dx if flip else dx), y + dy, col(*back))
    px(c, x + (7 if flip else 1), y + 1, col("iron", 0))


def awning(c, x0, x1, y0, y1, r1, r2, stripe=6):
    """Striped awning with a scalloped lower edge."""
    for x in range(x0, x1):
        a, b = (r1, 3), (r2, 3)
        cc = a if ((x - x0) // stripe) % 2 == 0 else b
        for y in range(y0, y1):
            shade = 4 if y == y0 else (2 if y >= y1 - 2 else 3)
            colr = col(cc[0], shade) if cc[1] == 3 else col(*cc)
            px(c, x, y, colr)
        scallop = 2 if ((x - x0) % stripe) in (1, 2, 3, 4) else 0
        for y in range(y1, y1 + scallop):
            px(c, x, y, col(cc[0], 2))


# ---- stalls and goods (64 x 64, pivot (32, 60)) -----------------------------------------------------------------------
def stall(r1: str, r2: str, goods: str) -> np.ndarray:
    c = new()
    for x in (8, 54):                                   # posts
        shaded(c, x, 14, x + 2, 60, "wood")
    rect(c, 6, 40, 58, 44, col("wood", 4))              # table top
    rect(c, 6, 44, 58, 60, col("wood", 2))              # table front
    rect(c, 6, 44, 8, 60, col("wood", 3))
    rect(c, 56, 44, 58, 60, col("wood", 1))
    for x in range(10, 56, 8):                          # planks
        rect(c, x, 46, x + 1, 60, col("wood", 1))
    awning(c, 4, 60, 12, 25, r1, r2)
    rect(c, 6, 25, 58, 27, col("wood", 1))              # valance shadow under the awning
    if goods == "fish":                                  # silver fish on a cream tray
        rect(c, 10, 38, 54, 41, col("cloth_cream", 3))
        for i, x in enumerate(range(11, 52, 10)):
            fish(c, x, 34 + (i % 2), flip=bool(i % 2))
        for x, y in ((14, 29), (30, 30), (45, 29)):      # hanging fish
            line(c, x + 3, 27, x + 3, 29, col("iron", 1))
            rect(c, x + 1, y, x + 5, y + 7, col("iron", 3))
            rect(c, x + 1, y, x + 2, y + 7, col("iron", 4))
            rect(c, x + 2, y + 7, x + 4, y + 10, col("iron", 2))
    elif goods == "shell":                               # baskets of crabs and clams
        for x in (12, 28, 44):
            rect(c, x, 34, x + 11, 41, col("dirt", 3))
            rect(c, x, 34, x + 11, 35, col("dirt", 4))
            for k in range(4):
                disc(c, x + 2 + k * 2.4, 33, 1.6, 1.3, col("cloth_red", 3 if k % 2 else 4))
    elif goods == "tuna":                                # two big slabs and a hanging scale
        for x in (10, 34):
            rect(c, x, 35, x + 18, 41, col("cloth_red", 2))
            rect(c, x, 35, x + 18, 37, col("cloth_red", 3))
            rect(c, x + 3, 37, x + 15, 38, col("cloth_cream", 4))
        line(c, 31, 27, 31, 31, col("iron", 2))
        rect(c, 28, 31, 35, 33, col("gold", 3))
        rect(c, 27, 33, 36, 34, col("gold", 2))
    elif goods == "fruit":                               # crates of fruit
        for x, cc in ((10, ("fire", 3)), (26, ("grass", 3)), (42, ("fire", 2))):
            rect(c, x, 35, x + 12, 41, col("wood", 3))
            for k in range(5):
                disc(c, x + 2 + k * 2, 35, 1.4, 1.4, col(*cc))
    rect(c, 22, 49, 42, 57, col("iron", 1))             # price chalkboard on the front
    rect(c, 23, 50, 41, 56, col("iron", 2))
    for x in range(25, 39, 3):
        px(c, x, 52, col("cloth_cream", 4))
        px(c, x, 54, col("cloth_cream", 3))
    return finish(c, "wood")


def counter() -> np.ndarray:
    """The fishmonger's counter: the selling point. Broader, a painted FISH board, scales and a hanging catch."""
    c = new()
    for x in (4, 58):
        shaded(c, x, 8, x + 2, 60, "wood")
    rect(c, 3, 38, 61, 43, col("wood", 4))
    rect(c, 3, 43, 61, 60, col("wood", 2))
    rect(c, 3, 43, 5, 60, col("wood", 3))
    rect(c, 59, 43, 61, 60, col("wood", 1))
    for x in range(9, 59, 9):
        rect(c, x, 45, x + 1, 60, col("wood", 1))
    rect(c, 8, 2, 56, 15, col("gold", 2))               # the sign board
    rect(c, 8, 2, 56, 4, col("gold", 4))
    rect(c, 8, 13, 56, 15, col("gold", 1))
    letters = {"F": ["111", "100", "110", "100", "100"], "I": ["111", "010", "010", "010", "111"],
               "S": ["111", "100", "111", "001", "111"], "H": ["101", "101", "111", "101", "101"]}
    x = 11
    for ch in "FISH":
        for yy, row in enumerate(letters[ch]):
            for xx, v in enumerate(row):
                if v == "1":
                    rect(c, x + xx * 2, 5 + yy * 2, x + xx * 2 + 2, 7 + yy * 2, col("iron", 0))
        x += 9
    fish(c, 46, 6, flip=False, body=("iron", 4), back=("iron", 3), belly=("cloth_cream", 4))
    for x, y in ((14, 17), (28, 18), (46, 17)):          # hanging catch
        line(c, x + 2, 15, x + 2, y, col("iron", 1))
        rect(c, x, y, x + 5, y + 8, col("iron", 3))
        rect(c, x, y, x + 1, y + 8, col("iron", 4))
        rect(c, x + 1, y + 8, x + 4, y + 11, col("iron", 2))
    rect(c, 8, 36, 22, 38, col("iron", 2))               # scales
    rect(c, 14, 30, 16, 36, col("iron", 3))
    rect(c, 9, 30, 21, 31, col("gold", 3))
    rect(c, 7, 31, 11, 33, col("gold", 2))
    rect(c, 19, 31, 23, 33, col("gold", 2))
    for i, x in enumerate(range(28, 56, 9)):             # fish on the counter
        fish(c, x, 34 + (i % 2), flip=bool(i % 2))
    rect(c, 22, 48, 44, 57, col("iron", 1))              # chalkboard
    rect(c, 23, 49, 43, 56, col("iron", 2))
    for x in range(25, 41, 3):
        px(c, x, 51, col("cloth_cream", 4))
        px(c, x, 53, col("cloth_cream", 3))
    return finish(c, "wood")


def crate_fish() -> np.ndarray:
    c = new()
    for (x, y) in ((8, 36), (30, 36), (19, 20)):
        rect(c, x, y + 12, x + 22, y + 24, col("wood", 2))
        rect(c, x, y + 12, x + 2, y + 24, col("wood", 3))
        rect(c, x + 20, y + 12, x + 22, y + 24, col("wood", 1))
        rect(c, x, y + 16, x + 22, y + 17, col("wood", 1))
        rect(c, x + 1, y + 6, x + 21, y + 12, col("cloth_cream", 3))     # ice
        for k in range(2):
            fish(c, x + 3 + k * 9, y + 6 + k, flip=bool(k))
    return finish(c, "wood")


def barrels() -> np.ndarray:
    c = new()
    for cx in (18, 40):
        for y in range(30, 58):
            t = (y - 30) / 28.0
            hw = int(round(8 + 2.5 * np.sin(t * np.pi)))
            for x in range(cx - hw, cx + hw + 1):
                u = (x - (cx - hw)) / max(2 * hw, 1)
                s = 3 if u < 0.3 else (2 if u < 0.7 else 1)
                px(c, x, y, col("wood", s))
        for y in (36, 52):
            rect(c, cx - 10, y, cx + 11, y + 2, col("iron", 2))
        disc(c, cx, 30, 8, 3, col("wood", 3))
        disc(c, cx, 30, 6, 2, col("sea_deep", 2))                          # brine
        fish(c, cx - 4, 27, flip=bool(cx > 20))
    return finish(c, "wood")


def net_rack() -> np.ndarray:
    c = new()
    for x in (6, 56):
        shaded(c, x, 8, x + 3, 60, "wood")
    rect(c, 6, 8, 59, 12, col("wood", 3))
    for y in range(12, 46, 2):                          # net: a lattice with sag
        for x in range(9, 56):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                px(c, x, y + int(2 * np.sin((x - 9) / 46.0 * np.pi)), col("cloth_blue", 3 if (x + y) % 8 else 4))
    for x in range(10, 56, 9):                          # cork floats
        rect(c, x, 10, x + 3, 14, col("dirt", 4))
    rect(c, 6, 56, 59, 60, col("wood", 1))
    return finish(c, "wood")


def fish_rack() -> np.ndarray:
    c = new()
    for x in (6, 56):
        shaded(c, x, 14, x + 3, 60, "wood")
    for y in (18, 36):
        rect(c, 6, y, 59, y + 2, col("wood", 3))
        for x in range(10, 54, 7):
            rect(c, x, y + 2, x + 4, y + 14, col("dirt", 3))
            rect(c, x, y + 2, x + 1, y + 14, col("dirt", 4))
            rect(c, x + 1, y + 13, x + 3, y + 16, col("dirt", 2))
    return finish(c, "wood")


def lantern_post() -> np.ndarray:
    c = new()
    shaded(c, 31, 10, 34, 60, "wood")
    rect(c, 26, 8, 40, 11, col("iron", 2))              # arm
    rect(c, 26, 11, 29, 24, col("iron", 2))
    rect(c, 27, 12, 29, 23, col("fire", 4))              # glass: glows at night
    rect(c, 27, 12, 29, 14, col("fire", 3))
    rect(c, 25, 24, 30, 26, col("iron", 2))
    rect(c, 28, 4, 31, 8, col("iron", 3))
    return finish(c, "wood")


def bench() -> np.ndarray:
    c = new()
    rect(c, 8, 38, 56, 44, col("wood", 3))
    rect(c, 8, 38, 56, 40, col("wood", 4))
    rect(c, 8, 44, 56, 47, col("wood", 1))
    rect(c, 8, 28, 56, 33, col("wood", 2))
    for x in (10, 52):
        rect(c, x, 33, x + 3, 38, col("wood", 1))
        rect(c, x, 47, x + 3, 58, col("wood", 1))
    return finish(c, "wood")


def well() -> np.ndarray:
    c = new()
    for y in range(40, 58):
        for x in range(14, 50):
            u = (x - 14) / 36.0
            s = 4 if u < 0.2 else (3 if u < 0.6 else 2)
            if (x // 5 + y // 4) % 2 == 0:
                s = max(s - 1, 1)
            px(c, x, y, col("stone_warm", s))
    disc(c, 32, 40, 18, 5, col("stone_warm", 4))
    disc(c, 32, 40, 14, 3, col("sea_deep", 1))
    for x in (16, 46):
        shaded(c, x, 10, x + 2, 42, "wood")
    rect(c, 14, 8, 50, 12, col("wood", 3))
    rect(c, 31, 12, 32, 30, col("dirt", 3))
    rect(c, 28, 30, 36, 36, col("wood", 2))
    return finish(c, "wood")


def sacks() -> np.ndarray:
    c = new()
    for (cx, cy) in ((24, 52), (44, 52), (34, 38), (14, 54)):
        for y in range(cy - 14, cy + 4):
            t = (y - (cy - 14)) / 18.0
            hw = int(round(4 + 6 * np.sin(min(t * 1.5, 1.0) * np.pi / 2)))
            for x in range(cx - hw, cx + hw + 1):
                u = (x - (cx - hw)) / max(2 * hw, 1)
                px(c, x, y, col("cloth_cream", 4 if u < 0.25 else (3 if u < 0.7 else 2)))
        rect(c, cx - 3, cy - 15, cx + 4, cy - 12, col("cloth_cream", 2))
        rect(c, cx - 3, cy - 13, cx + 4, cy - 12, col("dirt", 2))
    return finish(c, "wood")


def anchor_prop() -> np.ndarray:
    c = new()
    rect(c, 30, 14, 34, 54, col("iron", 2))
    rect(c, 30, 14, 31, 54, col("iron", 3))
    rect(c, 24, 20, 40, 23, col("iron", 2))
    disc(c, 32, 12, 4, 4, col("iron", 2))
    disc(c, 32, 12, 2, 2, col(("iron"), 0))
    for t in np.linspace(0, np.pi, 40):
        x, y = int(32 + 17 * np.cos(t)), int(52 - 12 * np.sin(t))
        rect(c, x - 1, y, x + 2, y + 3, col("iron", 3))
    rect(c, 12, 49, 18, 53, col("iron", 2))
    rect(c, 46, 49, 52, 53, col("iron", 2))
    return finish(c, "iron")


def handcart() -> np.ndarray:
    c = new()
    rect(c, 10, 34, 54, 50, col("wood", 2))
    rect(c, 10, 34, 54, 37, col("wood", 3))
    rect(c, 10, 47, 54, 50, col("wood", 1))
    for x in range(14, 52, 9):
        rect(c, x, 37, x + 1, 47, col("wood", 1))
    disc(c, 22, 52, 7, 7, col("wood", 1))
    disc(c, 22, 52, 5, 5, col("wood", 3))
    disc(c, 22, 52, 1.5, 1.5, col("iron", 2))
    rect(c, 54, 44, 62, 46, col("wood", 3))              # handles
    for x, y in ((14, 26), (28, 28)):                    # crates on top
        rect(c, x, y, x + 12, y + 9, col("wood", 3))
        rect(c, x, y, x + 12, y + 2, col("wood", 4))
        rect(c, x, y + 5, x + 12, y + 6, col("wood", 1))
    return finish(c, "wood")


def notice_board() -> np.ndarray:
    c = new()
    for x in (14, 47):
        shaded(c, x, 22, x + 3, 60, "wood")
    rect(c, 8, 8, 58, 40, col("wood", 2))
    rect(c, 8, 8, 58, 10, col("wood", 4))
    rect(c, 8, 38, 58, 40, col("wood", 1))
    for (x, y, w, h) in ((12, 13, 12, 14), (28, 12, 11, 12), (42, 14, 12, 15), (14, 29, 14, 7), (32, 27, 18, 9)):
        rect(c, x, y, x + w, y + h, col("cloth_cream", 3))
        rect(c, x, y, x + w, y + 1, col("cloth_cream", 4))
        for k in range(y + 3, y + h - 1, 3):
            rect(c, x + 2, k, x + w - 2, k + 1, col("wood", 1))
        px(c, x + w // 2, y, col("cloth_red", 3))
    return finish(c, "wood")


# ---- markers (billboards above people and places) ----------------------------------------------------------------------
def marker_diamond(body: str, ring: str) -> np.ndarray:
    c = new(24, 24)
    for y in range(24):
        w = 11 - abs(y - 11)
        for x in range(12 - w, 12 + w + 1):
            u = (x - (12 - w)) / max(2 * w, 1)
            px(c, x, y, col(ring, 4 if u < 0.3 else (3 if u < 0.7 else 2)))
    for y in range(4, 20):
        w = 7 - abs(y - 11) * 7 // 8
        for x in range(12 - max(w, 0), 12 + max(w, 0) + 1):
            px(c, x, y, col(body, 3))
    rect(c, 11, 6, 13, 14, col("iron", 0))              # the exclamation mark
    rect(c, 11, 16, 13, 18, col("iron", 0))
    return finish(c, "iron")


def marker_fish() -> np.ndarray:
    c = new(24, 24)
    for y in range(24):
        w = 11 - abs(y - 11)
        for x in range(12 - w, 12 + w + 1):
            px(c, x, y, col("cloth_blue", 3 if x > 12 - w + 2 else 4))
    fish(c, 7, 10, body=("iron", 4), back=("iron", 3), belly=("cloth_cream", 4))
    return finish(c, "iron")


def marker_scroll() -> np.ndarray:
    c = new(24, 24)
    for y in range(24):
        w = 11 - abs(y - 11)
        for x in range(12 - w, 12 + w + 1):
            px(c, x, y, col("gold", 3 if x > 12 - w + 2 else 4))
    rect(c, 7, 7, 17, 17, col("cloth_cream", 3))
    for k in (9, 12, 15):
        rect(c, 9, k, 15, k + 1, col("wood", 1))
    return finish(c, "iron")


# ---- big pieces (192 x 112, pivot (96, 100)) ----------------------------------------------------------------------------
def canopy() -> np.ndarray:
    """An open market hall: posts, a striped roof, a cloth valance. The middle is open so the stalls under it show."""
    c = new(BW, BHT)
    for x in (10, 60, 128, 176):                         # posts
        shaded(c, x, 22, x + 4, 100, "wood")
    rect(c, 8, 20, 184, 26, col("wood", 1))              # beam
    for y in range(2, 22):                               # roof: a shallow gable seen from the front
        t = (y - 2) / 20.0
        inset = int(round((1.0 - t) * 22))
        for x in range(2 + inset, 190 - inset):
            stripe = ((x - 2) // 12) % 2
            cc = "cloth_red" if stripe == 0 else "cloth_cream"
            shade = 4 if y < 5 else (3 if y < 15 else 2)
            px(c, x, y, col(cc, shade))
    for x in range(2, 190):                              # scalloped valance
        stripe = ((x - 2) // 12) % 2
        cc = "cloth_red" if stripe == 0 else "cloth_cream"
        for y in range(22, 27 + (2 if ((x - 2) % 12) in (2, 3, 4, 5, 6, 7, 8, 9) else 0)):
            px(c, x, y, col(cc, 2))
    for x in (30, 100, 150):                             # lanterns
        line(c, x, 27, x, 31, col("iron", 1))
        rect(c, x - 2, 31, x + 3, 38, col("fire", 4))
        rect(c, x - 2, 31, x + 3, 33, col("iron", 2))
    rect(c, 70, 92, 124, 100, col("dirt", 2))            # worn ground strip under the hall
    return finish(c, "wood")


def smack(hull_ramp: str, sail_ramp: str, stripe: str) -> np.ndarray:
    """A fishing smack, broadside, bow to the east: a 9 m hull (130 px), a mast with a furled sail, nets and a catch."""
    c = new(BW, BHT)
    cy = 92
    hx0, hx1 = 30, 164
    for x in range(hx0, hx1):                            # hull: sheer line and round bilge
        t = (x - hx0) / float(hx1 - hx0)
        top = cy - 18 - int(round(9 * (abs(t - 0.5) * 2) ** 2))
        bottom = cy + 6 - int(round(8 * (abs(t - 0.5) * 2) ** 3.0))
        for y in range(top, bottom):
            k = (y - top) / max(bottom - top, 1)
            s = 4 if k < 0.12 else (3 if k < 0.35 else (2 if k < 0.75 else 1))
            px(c, x, y, col(hull_ramp, s))
        if int(cy - 6) <= int(top + 12):
            pass
    for x in range(hx0 + 6, hx1 - 8):                    # stripe along the hull
        t = (x - hx0) / float(hx1 - hx0)
        top = cy - 18 - int(round(9 * (abs(t - 0.5) * 2) ** 2))
        rect(c, x, top + 7, x + 1, top + 10, col(stripe, 3))
    for x in range(hx0 + 4, hx1 - 4):                    # inside of the far gunwale and the deck
        t = (x - hx0) / float(hx1 - hx0)
        top = cy - 18 - int(round(9 * (abs(t - 0.5) * 2) ** 2))
        rect(c, x, top - 3, x + 1, top, col("wood", 3))
    rect(c, 76, cy - 62, 80, cy - 14, col("wood", 2))     # mast
    rect(c, 76, cy - 62, 77, cy - 14, col("wood", 3))
    rect(c, 54, cy - 40, 118, cy - 36, col("wood", 2))    # boom and furled sail
    for x in range(56, 116):
        for y in range(cy - 37, cy - 28):
            px(c, x, y, col(sail_ramp, 3 if (x // 7) % 2 else 2))
    line(c, 78, cy - 62, 150, cy - 20, col("iron", 2))    # forestay
    line(c, 78, cy - 62, 36, cy - 20, col("iron", 2))
    rect(c, 128, cy - 26, 150, cy - 18, col("cloth_blue", 3))     # a heap of net
    rect(c, 128, cy - 26, 150, cy - 24, col("cloth_blue", 4))
    for i, x in enumerate(range(104, 124, 7)):            # fish on the deck
        fish(c, x, cy - 22 + (i % 2), flip=bool(i % 2))
    for x in (46, 60):                                    # fenders
        disc(c, x, cy - 10, 3, 4, col("dirt", 3))
    return finish(c, "wood")


def skiff() -> np.ndarray:
    c = new(BW, BHT)
    cy = 92
    hx0, hx1 = 62, 134
    for x in range(hx0, hx1):
        t = (x - hx0) / float(hx1 - hx0)
        top = cy - 12 - int(round(6 * (abs(t - 0.5) * 2) ** 2))
        bottom = cy + 4 - int(round(6 * (abs(t - 0.5) * 2) ** 3))
        for y in range(top, bottom):
            k = (y - top) / max(bottom - top, 1)
            px(c, x, y, col("wood", 4 if k < 0.15 else (3 if k < 0.5 else (2 if k < 0.8 else 1))))
    for x in range(hx0 + 4, hx1 - 4):
        t = (x - hx0) / float(hx1 - hx0)
        top = cy - 12 - int(round(6 * (abs(t - 0.5) * 2) ** 2))
        rect(c, x, top - 2, x + 1, top, col("wood", 1))
    for x in (84, 100, 114):                              # thwarts
        rect(c, x, cy - 12, x + 3, cy - 9, col("wood", 4))
    line(c, 80, cy - 11, 40, cy - 30, col("wood", 2))     # an oar leaning out
    line(c, 81, cy - 11, 41, cy - 30, col("wood", 3))
    return finish(c, "wood")


def net_frame() -> np.ndarray:
    """A big drying frame hung with nets and floats (cargo and fishing area)."""
    c = new(BW, BHT)
    for x in (24, 166):
        shaded(c, x, 20, x + 5, 100, "wood")
    rect(c, 22, 18, 174, 24, col("wood", 3))
    rect(c, 22, 18, 174, 20, col("wood", 4))
    for y in range(24, 78, 3):
        for x in range(28, 166):
            if (x + y) % 5 == 0 or (x - y) % 5 == 0:
                sag = int(4 * np.sin((x - 28) / 138.0 * np.pi))
                px(c, x, y + sag, col("cloth_blue", 3 if (x + y) % 10 else 4))
    for x in range(30, 164, 12):
        rect(c, x, 22, x + 4, 28, col("dirt", 4))
    return finish(c, "wood")


def cargo_pile() -> np.ndarray:
    """Tarp-covered cargo with rope and a stack of crates: the warehouse yard."""
    c = new(BW, BHT)
    rect(c, 20, 56, 112, 100, col("cloth_cream", 2))
    rect(c, 20, 56, 112, 62, col("cloth_cream", 3))
    for x in range(20, 112, 10):
        rect(c, x, 62, x + 1, 100, col("cloth_cream", 1))
    for y in (70, 86):
        rect(c, 20, y, 112, y + 2, col("dirt", 2))
    for (x, y) in ((118, 66), (146, 66), (118, 40), (132, 84)):
        w = 26
        rect(c, x, y, x + w, y + 30 if y < 80 else y + 16, col("wood", 2))
        rect(c, x, y, x + w, y + 4, col("wood", 4))
        rect(c, x, y, x + 3, y + 30 if y < 80 else y + 16, col("wood", 3))
        rect(c, x + w - 3, y, x + w, y + 30 if y < 80 else y + 16, col("wood", 1))
        rect(c, x, y + 14, x + w, y + 15, col("wood", 1))
    return finish(c, "wood")


# ---- ships: the existing sloop hull, recoloured ---------------------------------------------------------------------------
def ships_atlas() -> Image.Image:
    sheet = np.array(Image.open(ART / "ship_sloop_hull.png").convert("RGBA"))
    frames = {"E": sheet[:, 4 * 112:5 * 112].copy(), "W": sheet[:, 12 * 112:13 * 112].copy()}
    recolour = {tuple(BI.ramp("hull_oak", i)): tuple(BI.ramp("stone_cool", i)) for i in range(5)}
    out = Image.new("RGBA", (112 * 4, 112), (0, 0, 0, 0))
    for k, key in enumerate(("E", "W", "E", "W")):
        f = frames[key].copy()
        if k >= 2:
            for src, dst in recolour.items():
                m = (f[..., 0] == src[0]) & (f[..., 1] == src[1]) & (f[..., 2] == src[2]) & (f[..., 3] > 0)
                f[m, :3] = dst
        out.paste(Image.fromarray(f, "RGBA"), (k * 112, 0))
    return out


# ---- the people of the port ------------------------------------------------------------------------------------------------
# One look = a dictionary; the figure is the hero's 24 x 32 body (bake: cay_sprites._hero_frame) with its own clothes.
LOOKS = {
    "fisher": dict(skin="skin_tan", hair=("dirt", 2), coat=("gold", 3, 4, 2), shirt=("cloth_cream", 3), pants=("cloth_blue", 2, 1),
                   boots=("wood", 1), hat="sou", hatc=("gold", 3, 4, 2), beard=True, belt=("wood", 2)),
    "merchant": dict(skin="skin_light", hair=("iron", 1), coat=("cloth_red", 2, 3, 1), shirt=("cloth_cream", 4), pants=("iron", 1, 0),
                     boots=("wood", 1), hat="bicorne", hatc=("iron", 1, 2, 0), beard=False, belt=("gold", 3), trim=("gold", 4)),
    "docker": dict(skin="skin_tan", hair=("dirt", 1), coat=("dirt", 3, 4, 2), shirt=("cloth_cream", 3), pants=("stone_cool", 2, 1),
                   boots=("wood", 1), hat="cap", hatc=("stone_cool", 2, 3, 1), beard=False, belt=("wood", 2), bare_arms=True),
    "sailor": dict(skin="skin_dark", hair=("iron", 1), coat=("cloth_cream", 3, 4, 2), shirt=("cloth_blue", 3), pants=("cloth_cream", 3, 2),
                   boots=("wood", 1), hat="bandana", hatc=("cloth_red", 3, 4, 2), beard=True, belt=("wood", 2), stripes=("cloth_blue", 3)),
    "shopkeeper": dict(skin="skin_light", hair=("cloth_cream", 3), coat=("cloth_cream", 4, 4, 3), shirt=("grass", 2), pants=("dirt", 2, 1),
                       boots=("wood", 1), hat="none", hatc=("cloth_cream", 3, 4, 2), beard=False, belt=("wood", 2), apron=True),
    "townsman": dict(skin="skin_tan", hair=("dirt", 1), coat=("grass", 2, 3, 1), shirt=("cloth_cream", 3), pants=("dirt", 2, 1),
                     boots=("wood", 1), hat="brim", hatc=("dirt", 3, 4, 2), beard=False, belt=("wood", 2)),
    # recruits: each reads differently from every group above at 24 px
    "r_tuck": dict(skin="skin_tan", hair=("fire", 1), coat=("cloth_blue", 3, 4, 2), shirt=("cloth_cream", 3), pants=("cloth_cream", 3, 2),
                   boots=("wood", 1), hat="bandana", hatc=("cloth_red", 3, 4, 2), beard=False, belt=("wood", 2), stripes=("cloth_cream", 4),
                   carry="net"),
    "r_silas": dict(skin="skin_light", hair=("cloth_cream", 3), coat=("cloth_cream", 4, 4, 3), shirt=("cloth_cream", 3), pants=("cloth_blue", 2, 1),
                    boots=("wood", 1), hat="cook", hatc=("cloth_cream", 4, 4, 3), beard=True, belt=("wood", 2), apron=True, wide=True,
                    carry="ladle"),
    "r_garrick": dict(skin="skin_tan", hair=("cloth_cream", 2), coat=("dirt", 2, 3, 1), shirt=("cloth_cream", 2), pants=("dirt", 2, 1),
                      boots=("wood", 1), hat="none", hatc=("dirt", 3, 4, 2), beard=True, belt=("wood", 1), apron=True, apron_c=("dirt", 3, 2),
                      bare_arms=True, carry="hammer"),
    "r_pip": dict(skin="skin_light", hair=("fire", 2), coat=("cloth_red", 2, 3, 1), shirt=("cloth_cream", 4), pants=("cloth_blue", 2, 1),
                  boots=("wood", 1), hat="floppy", hatc=("cloth_blue", 2, 3, 1), beard=False, belt=("wood", 2), carry="glass", slim=True),
}
LOOK_ORDER = list(LOOKS.keys())


def _look_frame(look: dict, facing: str, frame: int) -> np.ndarray:
    c = np.zeros((NPC_H, NPC_W, 4), np.uint8)
    bob = -1 if frame in (1, 3) else 0
    swing = {0: 0, 1: 1, 2: 0, 3: -1}[frame]
    skin, skin_d = col(look["skin"], 3), col(look["skin"], 1)
    cr, cs, cd = look["coat"][0], look["coat"][1], look["coat"][3]
    coat, coat_l, coat_d = col(cr, look["coat"][1]), col(cr, look["coat"][2]), col(cr, look["coat"][3])
    shirt = col(*look["shirt"])
    pants, pants_d = col(look["pants"][0], look["pants"][1]), col(look["pants"][0], look["pants"][2])
    boot = col(*look["boots"])
    hair = col(*look["hair"])
    belt = col(*look["belt"])
    hat = look["hat"]
    hc, hc_l, hc_d = col(look["hatc"][0], look["hatc"][1]), col(look["hatc"][0], look["hatc"][2]), col(look["hatc"][0], look["hatc"][3])
    ex = 1 if look.get("wide") else 0
    sl = 1 if look.get("slim") else 0
    arm_c = skin if look.get("bare_arms") else coat_d
    if facing in ("S", "N"):
        lift_l = 1 if swing == 1 else 0
        lift_r = 1 if swing == -1 else 0
        rect(c, 8, 22 + bob, 12, 27 - lift_l, pants)
        rect(c, 12, 22 + bob, 16, 27 - lift_r, pants)
        rect(c, 11, 22 + bob, 13, 26, pants_d)
        rect(c, 7, 27 - lift_l, 12, 30 - lift_l, boot)
        rect(c, 12, 27 - lift_r, 17, 30 - lift_r, boot)
        tx0, tx1 = 7 - ex + sl, 17 + ex - sl
        rect(c, tx0, 12 + bob, tx1, 23 + bob, coat)
        rect(c, tx0, 12 + bob, tx0 + 2, 23 + bob, coat_l)
        rect(c, tx1 - 2, 12 + bob, tx1, 23 + bob, coat_d)
        if "stripes" in look:
            for y in range(13 + bob, 22 + bob, 3):
                rect(c, tx0 + 2, y, tx1 - 2, y + 1, col(*look["stripes"]))
        if look.get("apron"):
            ac = look.get("apron_c", ("cloth_cream", 4, 3))
            rect(c, 8, 15 + bob, 16, 26 + bob, col(ac[0], ac[1]))
            rect(c, 8, 15 + bob, 9, 26 + bob, col(ac[0], ac[2]))
        rect(c, tx0, 19 + bob, tx1, 20 + bob, belt)
        al, ar = -swing, swing
        rect(c, tx0 - 2, 13 + bob + al, tx0, 20 + bob + al, arm_c if facing == "S" else coat_d)
        rect(c, tx1, 13 + bob + ar, tx1 + 2, 20 + bob + ar, arm_c)
        rect(c, tx0 - 2, 20 + bob + al, tx0, 22 + bob + al, skin)
        rect(c, tx1, 20 + bob + ar, tx1 + 2, 22 + bob + ar, skin)
        rect(c, 9, 5 + bob, 15, 12 + bob, skin if facing == "S" else hair)
        if facing == "S":
            if look["beard"]:
                rect(c, 9, 10 + bob, 15, 12 + bob, hair)
            else:
                rect(c, 9, 10 + bob, 15, 12 + bob, skin_d)
            c[8 + bob, 10] = col("iron", 0)
            c[8 + bob, 13] = col("iron", 0)
            rect(c, 11, 12 + bob, 13, 14 + bob, shirt)
        else:
            rect(c, 9, 5 + bob, 15, 9 + bob, hair)
        _hat(c, hat, bob, hc, hc_l, hc_d, hair, facing, look)
        if look.get("carry") == "net" and facing == "S":
            rect(c, 15, 11 + bob, 20, 19 + bob, col("cloth_blue", 3))
            rect(c, 15, 11 + bob, 20, 12 + bob, col("cloth_blue", 4))
        elif look.get("carry") == "net":
            rect(c, 4, 11 + bob, 9, 19 + bob, col("cloth_blue", 3))
        if look.get("carry") == "ladle" and facing == "S":
            rect(c, tx1 + 1, 16 + bob + ar, tx1 + 2, 22 + bob + ar, col("iron", 3))
            rect(c, tx1, 14 + bob + ar, tx1 + 3, 16 + bob + ar, col("iron", 2))
        if look.get("carry") == "hammer" and facing == "S":
            rect(c, tx1 + 1, 17 + bob + ar, tx1 + 2, 22 + bob + ar, col("wood", 3))
            rect(c, tx1 - 1, 15 + bob + ar, tx1 + 3, 18 + bob + ar, col("iron", 3))
        if look.get("carry") == "glass" and facing == "S":
            rect(c, tx1, 15 + bob + ar, tx1 + 5, 17 + bob + ar, col("gold", 3))
            rect(c, tx1 + 4, 14 + bob + ar, tx1 + 6, 18 + bob + ar, col("gold", 2))
    else:
        s = swing
        rect(c, 10 - 2 * s, 22 + bob, 14 - 2 * s, 28, pants)
        rect(c, 10 + 2 * s, 22 + bob, 14 + 2 * s, 28, pants_d)
        rect(c, 8 - 2 * s, 28, 14 - 2 * s, 30, boot)
        rect(c, 10 + 2 * s, 28, 16 + 2 * s, 30, boot)
        tx0, tx1 = 8 - ex, 16 + ex
        rect(c, tx0, 12 + bob, tx1, 23 + bob, coat)
        rect(c, tx0, 12 + bob, tx0 + 2, 23 + bob, coat_l)
        rect(c, tx1 - 2, 12 + bob, tx1, 23 + bob, coat_d)
        if "stripes" in look:
            for y in range(13 + bob, 22 + bob, 3):
                rect(c, tx0 + 1, y, tx1 - 1, y + 1, col(*look["stripes"]))
        if look.get("apron"):
            ac = look.get("apron_c", ("cloth_cream", 4, 3))
            rect(c, tx0, 15 + bob, tx0 + 4, 26 + bob, col(ac[0], ac[1]))
        rect(c, tx0, 19 + bob, tx1, 20 + bob, belt)
        rect(c, 10 + s * 2, 13 + bob, 14 + s * 2, 20 + bob, arm_c)
        rect(c, 10 + s * 2, 20 + bob, 14 + s * 2, 22 + bob, skin)
        rect(c, 9, 5 + bob, 15, 12 + bob, skin)
        rect(c, 12, 5 + bob, 15, 12 + bob, hair)
        if look["beard"]:
            rect(c, 9, 10 + bob, 12, 12 + bob, hair)
        else:
            rect(c, 9, 10 + bob, 12, 12 + bob, skin_d)
        c[8 + bob, 10] = col("iron", 0)
        rect(c, 8, 8 + bob, 9, 10 + bob, skin)
        _hat(c, hat, bob, hc, hc_l, hc_d, hair, "W", look)
        if look.get("carry") == "net":
            rect(c, 13, 11 + bob, 18, 19 + bob, col("cloth_blue", 3))
        if look.get("carry") == "glass":
            rect(c, 5, 15 + bob + s, 11, 17 + bob + s, col("gold", 3))
        if look.get("carry") == "hammer":
            rect(c, 7, 17 + bob + s, 8, 22 + bob + s, col("wood", 3))
            rect(c, 5, 15 + bob + s, 10, 18 + bob + s, col("iron", 3))
        if look.get("carry") == "ladle":
            rect(c, 7, 16 + bob + s, 8, 22 + bob + s, col("iron", 3))
        if facing == "E":
            c = c[:, ::-1].copy()
    return finish(c, "iron")


def _hat(c, hat, bob, hc, hc_l, hc_d, hair, facing, look):
    if hat == "sou":                                      # fisher's sou'wester: dome, wide brim, a tail down the back
        rect(c, 8, 1 + bob, 16, 5 + bob, hc)
        rect(c, 8, 1 + bob, 11, 3 + bob, hc_l)
        rect(c, 6, 5 + bob, 18, 7 + bob, hc_d)
        if facing == "N":
            rect(c, 8, 7 + bob, 16, 10 + bob, hc_d)
    elif hat == "bicorne":                                # merchant: wide black bicorne with a gold edge and a red plume
        rect(c, 5, 4 + bob, 19, 6 + bob, hc)
        rect(c, 7, 1 + bob, 17, 4 + bob, hc)
        rect(c, 5, 4 + bob, 19, 5 + bob, col("gold", 4))
        rect(c, 15, 0 + bob, 18, 3 + bob, col("cloth_red", 3))
    elif hat == "cap":                                    # docker's flat cap with a short peak
        rect(c, 8, 3 + bob, 16, 6 + bob, hc)
        rect(c, 8, 3 + bob, 12, 4 + bob, hc_l)
        if facing != "N":
            rect(c, 8, 6 + bob, 17, 7 + bob, hc_d)
    elif hat == "bandana":                                # sailor's red bandana, knot at the side
        rect(c, 9, 3 + bob, 15, 7 + bob, hc)
        rect(c, 9, 3 + bob, 12, 4 + bob, hc_l)
        rect(c, 15, 5 + bob, 18, 7 + bob, hc_d)
        rect(c, 16, 7 + bob, 18, 9 + bob, hc)
    elif hat == "brim":                                   # townsman's soft brimmed hat
        rect(c, 6, 5 + bob, 18, 6 + bob, hc_d)
        rect(c, 8, 1 + bob, 16, 5 + bob, hc)
        rect(c, 8, 4 + bob, 16, 5 + bob, hc_d)
    elif hat == "cook":                                   # a tall, flat-topped linen cap
        rect(c, 8, 0 + bob, 16, 6 + bob, hc)
        rect(c, 8, 0 + bob, 10, 6 + bob, hc_l)
        rect(c, 8, 5 + bob, 16, 6 + bob, hc_d)
    elif hat == "floppy":                                 # lookout's floppy cap, bent over to one side
        rect(c, 8, 2 + bob, 16, 6 + bob, hc)
        rect(c, 14, 4 + bob, 19, 8 + bob, hc_d)
        rect(c, 8, 2 + bob, 11, 3 + bob, hc_l)
    else:                                                 # bare head: hair on top
        rect(c, 9, 3 + bob, 15, 6 + bob, hair)
        rect(c, 8, 5 + bob, 9, 9 + bob, hair)
        rect(c, 15, 5 + bob, 16, 9 + bob, hair)


def npc_atlas() -> Image.Image:
    atlas = Image.new("RGBA", (NPC_W * 4, NPC_H * 4 * len(LOOK_ORDER)), (0, 0, 0, 0))
    for li, name in enumerate(LOOK_ORDER):
        for r, f in enumerate(("S", "N", "W", "E")):
            for k in range(4):
                atlas.paste(Image.fromarray(_look_frame(LOOKS[name], f, k), "RGBA"), (k * NPC_W, (li * 4 + r) * NPC_H))
    return atlas


# ---- atlases --------------------------------------------------------------------------------------------------------------------
STALL_TYPES = ["stall_red", "stall_blue", "stall_green", "stall_fruit", "fish_counter", "fish_crates", "barrels_fish", "net_rack",
               "fish_rack", "lantern_post", "bench", "well", "sacks", "anchor", "handcart", "notice_board"]
MISC_TYPES = ["marker_recruit", "marker_recruit_ok", "marker_fish", "marker_notice"]
BIG_TYPES = ["market_canopy", "smack_red", "smack_blue", "skiff", "net_frame", "cargo_pile"]


def grid_atlas(cells, cw, ch, cols, rows) -> Image.Image:
    atlas = Image.new("RGBA", (cw * cols, ch * rows), (0, 0, 0, 0))
    for i, cell in enumerate(cells):
        im = Image.fromarray(cell, "RGBA")
        atlas.paste(im, ((i % cols) * cw, (i // cols) * ch))
    return atlas


def stall_atlas() -> Image.Image:
    cells = [stall("cloth_red", "cloth_cream", "fish"), stall("cloth_blue", "cloth_cream", "shell"),
             stall("grass", "cloth_cream", "tuna"), stall("gold", "cloth_cream", "fruit"), counter(), crate_fish(), barrels(), net_rack(),
             fish_rack(), lantern_post(), bench(), well(), sacks(), anchor_prop(), handcart(), notice_board()]
    return grid_atlas(cells, CW, CH, 4, 4)


def misc_atlas() -> Image.Image:
    cells = [marker_diamond("gold", "gold"), marker_diamond("grass", "gold"), marker_fish(), marker_scroll()]
    cells = [np.pad(x, ((60 - x.shape[0], CH - 60), ((CW - x.shape[1]) // 2, CW - x.shape[1] - (CW - x.shape[1]) // 2), (0, 0))) for x in cells]
    return grid_atlas(cells, CW, CH, 4, 4)


def big_atlas() -> Image.Image:
    cells = [canopy(), smack("hull_oak", "cloth_cream", "cloth_red"), smack("stone_cool", "cloth_cream", "gold"), skiff(), net_frame(),
             cargo_pile()]
    return grid_atlas(cells, BW, BHT, 4, 2)


def reduce_colours(im: Image.Image, cap: int) -> Image.Image:
    """Merge the least-used opaque colours into their nearest neighbour until the atlas has at most `cap` (palette.json limit)."""
    a = np.array(im.convert("RGBA"))
    op = a[..., 3] >= 128
    while True:
        cols, counts = np.unique(a[op][:, :3], axis=0, return_counts=True)
        if len(cols) <= cap:
            break
        i = int(np.argmin(counts))
        d = np.abs(cols.astype(int) - cols[i].astype(int)).sum(axis=1)
        d[i] = 10 ** 6
        j = int(np.argmin(d))
        m = op & (a[..., :3] == cols[i]).all(axis=-1)
        a[m, :3] = cols[j]
    return Image.fromarray(a, "RGBA")


def build_all(out_dir: Path = ART) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    sheets = {"port_stall_atlas.png": reduce_colours(stall_atlas(), 32), "port_misc_atlas.png": misc_atlas(), "port_big_atlas.png": big_atlas(),
              "port_ships_atlas.png": ships_atlas(), "port_npc_atlas.png": npc_atlas()}
    for name, im in sheets.items():
        im.save(out_dir / name, optimize=True)
    return sheets


def preview(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    s = build_all(Path("/tmp/port_art"))
    bg = (130, 118, 92, 255)
    for name, im in s.items():
        z = 3 if name in ("port_stall_atlas.png", "port_misc_atlas.png") else (2 if name != "port_npc_atlas.png" else 4)
        big = im.resize((im.width * z, im.height * z), Image.NEAREST)
        canvas = Image.new("RGBA", big.size, bg)
        canvas.alpha_composite(big)
        canvas.convert("RGB").save(out / ("preview_" + name))
    print("previews in", out)


if __name__ == "__main__":
    build_all()          # writes the five atlases into game/h2d/art
    preview(Path(__file__).resolve().parents[2] / "art_bible/cp1")
