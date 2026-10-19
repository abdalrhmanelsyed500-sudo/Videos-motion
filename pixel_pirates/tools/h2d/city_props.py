"""CP-1 revision: street furniture for the capital, 64 x 64 px cells (4.4 m), pivot (32, 60), 14.4 px per metre."""
from __future__ import annotations

import numpy as np

from city_kit import col, disc, finish, line, px, rect, shift, hsh, canvas

CW, CH, PIV = 64, 64, (32, 60)


def lamp_iron():
    c = canvas(CW, CH)
    rect(c, 30, 20, 34, 60, col("iron", 2)); rect(c, 30, 20, 31, 60, col("iron", 3))
    rect(c, 27, 54, 37, 60, col("iron", 1))
    rect(c, 26, 8, 38, 12, col("iron", 1))
    rect(c, 27, 12, 37, 22, col("iron", 2))
    rect(c, 29, 13, 35, 21, col("fire", 3)); rect(c, 30, 14, 34, 18, col("fire", 4))
    for i in range(6):
        rect(c, 29 - i + 3, 7 - i, 35 + i - 3, 8 - i, col("iron", 1))
    rect(c, 31, 2, 33, 4, col("iron", 1))
    return finish(c)


def tub_bush():
    c = canvas(CW, CH)
    rect(c, 18, 44, 46, 60, col("wood", 2)); rect(c, 18, 44, 22, 60, col("wood", 3)); rect(c, 42, 44, 46, 60, col("wood", 1))
    rect(c, 18, 48, 46, 50, col("iron", 2)); rect(c, 18, 55, 46, 57, col("iron", 2))
    for cx, cy, r, k in ((32, 30, 14, 2), (24, 36, 9, 3), (40, 36, 9, 2), (32, 22, 8, 3), (30, 30, 6, 3)):
        disc(c, cx, cy, r, int(r * 0.9), col("palm_frond" if False else "foliage", k + 1))
    for i in range(7):
        px(c, 22 + int(hsh(i, 1) * 20), 22 + int(hsh(i, 2) * 18), col("grass", 3))
    return finish(c)


def planter():
    c = canvas(CW, CH)
    rect(c, 8, 46, 56, 60, col("stone_warm", 3)); rect(c, 8, 46, 56, 48, col("stone_warm", 4)); rect(c, 8, 58, 56, 60, col("stone_warm", 1))
    rect(c, 10, 40, 54, 46, col("dirt", 1))
    for x in range(10, 54, 4):
        rect(c, x, 34 + int(hsh(x, 3) * 5), x + 3, 42, col("grass", 2 + (x // 4) % 2))
        if hsh(x, 5) > 0.5:
            rect(c, x + 1, 31 + int(hsh(x, 3) * 4), x + 3, 34, col(("cloth_red", "gold", "cloth_cream", "cloth_blue")[(x // 4) % 4], 3))
    return finish(c)


def bench_stone():
    c = canvas(CW, CH)
    rect(c, 8, 44, 56, 50, col("stone_warm", 3)); rect(c, 8, 44, 56, 46, col("stone_warm", 4))
    rect(c, 10, 50, 18, 60, col("stone_warm", 2)); rect(c, 46, 50, 54, 60, col("stone_warm", 2))
    rect(c, 8, 34, 56, 38, col("wood", 3)); rect(c, 8, 34, 56, 35, col("wood", 4)); rect(c, 12, 38, 14, 44, col("wood", 2)); rect(c, 50, 38, 52, 44, col("wood", 2))
    return finish(c)


def crates(kind=0):
    c = canvas(CW, CH)
    def crate(x, y, w, h):
        rect(c, x, y, x + w, y + h, col("wood", 3)); rect(c, x, y, x + w, y + 2, col("wood", 4)); rect(c, x + w - 2, y, x + w, y + h, col("wood", 1))
        rect(c, x + 2, y + 2, x + 4, y + h, col("wood", 2)); rect(c, x + w - 6, y + 2, x + w - 4, y + h, col("wood", 2))
        line(c, x + 2, y + 2, x + w - 3, y + h - 1, col("wood", 2))
    if kind == 0:
        crate(10, 42, 22, 18); crate(32, 46, 20, 14); crate(18, 26, 20, 16)
    else:
        crate(8, 44, 18, 16); crate(26, 44, 18, 16); crate(44, 48, 14, 12); crate(14, 28, 18, 16); crate(32, 30, 16, 14)
    return finish(c)


def barrels(kind=0):
    c = canvas(CW, CH)
    def barrel(cx, by, r=9, h=18):
        rect(c, cx - r, by - h, cx + r, by, col("wood", 3)); rect(c, cx - r - 1, by - h + 4, cx + r + 1, by - 4, col("wood", 3))
        rect(c, cx - r, by - h, cx - r + 3, by, col("wood", 4)); rect(c, cx + r - 3, by - h, cx + r, by, col("wood", 1))
        rect(c, cx - r - 1, by - h + 5, cx + r + 1, by - h + 7, col("iron", 2)); rect(c, cx - r - 1, by - 7, cx + r + 1, by - 5, col("iron", 2))
        disc(c, cx, by - h, r, 3, col("wood", 4)); disc(c, cx, by - h, r - 2, 2, col("wood", 3))
    if kind == 0:
        barrel(22, 60); barrel(42, 60); barrel(32, 46)
    else:
        barrel(20, 60); barrel(40, 60, 8, 16); rect(c, 46, 50, 58, 60, col("wood", 2)); rect(c, 46, 50, 58, 52, col("wood", 4))
    return finish(c)


def sacks():
    c = canvas(CW, CH)
    for cx, by, w in ((20, 60, 12), (38, 60, 12), (30, 46, 11), (50, 60, 9)):
        disc(c, cx, by - 8, w, 9, col("cloth_cream", 3)); disc(c, cx - 3, by - 11, w - 5, 5, col("cloth_cream", 4))
        rect(c, cx - 3, by - 19, cx + 3, by - 15, col("cloth_cream", 2)); rect(c, cx - 3, by - 16, cx + 3, by - 15, col("dirt", 2))
    return finish(c)


def hay_cart():
    c = canvas(CW, CH)
    rect(c, 8, 38, 54, 48, col("wood", 3)); rect(c, 8, 38, 54, 40, col("wood", 4)); rect(c, 8, 46, 54, 48, col("wood", 1))
    for x in range(10, 52, 3):
        rect(c, x, 28 + int(hsh(x, 1) * 6), x + 3, 38, col("sand", 3 if x % 2 else 4))
    disc(c, 22, 52, 8, 8, col("wood", 2)); disc(c, 22, 52, 5, 5, col("wood", 3)); disc(c, 22, 52, 1, 1, col("iron", 2))
    disc(c, 44, 52, 8, 8, col("wood", 2)); disc(c, 44, 52, 5, 5, col("wood", 3)); disc(c, 44, 52, 1, 1, col("iron", 2))
    rect(c, 54, 42, 62, 44, col("wood", 2))
    return finish(c)


def cannon_s():
    c = canvas(CW, CH)
    rect(c, 14, 40, 52, 50, col("iron", 2)); rect(c, 14, 40, 52, 42, col("iron", 3)); rect(c, 48, 38, 56, 52, col("iron", 1))
    rect(c, 8, 42, 16, 48, col("iron", 1))
    rect(c, 18, 48, 48, 54, col("wood", 2)); rect(c, 18, 48, 48, 49, col("wood", 3))
    disc(c, 22, 54, 6, 6, col("wood", 2)); disc(c, 22, 54, 3, 3, col("wood", 3)); disc(c, 42, 54, 6, 6, col("wood", 2)); disc(c, 42, 54, 3, 3, col("wood", 3))
    return finish(c)


def balls():
    c = canvas(CW, CH)
    for i, (x, y) in enumerate(((20, 56), (32, 56), (44, 56), (26, 47), (38, 47), (32, 38))):
        disc(c, x, y, 6, 6, col("iron", 2)); disc(c, x - 2, y - 2, 2, 2, col("iron", 4))
    return finish(c)


def hitching():
    c = canvas(CW, CH)
    rect(c, 10, 30, 14, 60, col("wood", 2)); rect(c, 50, 30, 54, 60, col("wood", 2)); rect(c, 10, 34, 54, 38, col("wood", 3)); rect(c, 10, 34, 54, 35, col("wood", 4))
    rect(c, 26, 38, 28, 46, col("sand", 3)); disc(c, 27, 47, 2, 2, col("iron", 2))
    return finish(c)


def signpost():
    c = canvas(CW, CH)
    rect(c, 30, 14, 34, 60, col("wood", 2)); rect(c, 30, 14, 31, 60, col("wood", 3))
    rect(c, 10, 18, 31, 28, col("wood", 3)); rect(c, 10, 18, 31, 19, col("wood", 4)); rect(c, 33, 32, 56, 42, col("wood", 3)); rect(c, 33, 32, 56, 33, col("wood", 4))
    for x in range(14, 28, 3):
        rect(c, x, 22, x + 2, 24, col("wood", 1))
    for x in range(37, 52, 3):
        rect(c, x, 36, x + 2, 38, col("wood", 1))
    return finish(c)


def clothes():
    c = canvas(CW, CH)
    rect(c, 4, 20, 8, 60, col("wood", 2)); rect(c, 56, 20, 60, 60, col("wood", 2))
    line(c, 8, 24, 56, 28, col("sand", 3))
    for i, (x, k) in enumerate(((14, "cloth_cream"), (24, "cloth_blue"), (34, "cloth_red"), (44, "cloth_cream"))):
        rect(c, x, 26 + i // 2, x + 7, 40 + (i % 2) * 3, col(k, 3)); rect(c, x, 26 + i // 2, x + 7, 28 + i // 2, col(k, 4))
    return finish(c)


def rain_barrel():
    c = canvas(CW, CH)
    rect(c, 20, 36, 44, 60, col("wood", 3)); rect(c, 20, 36, 24, 60, col("wood", 4)); rect(c, 40, 36, 44, 60, col("wood", 1))
    rect(c, 20, 40, 44, 42, col("iron", 2)); rect(c, 20, 54, 44, 56, col("iron", 2))
    disc(c, 32, 36, 12, 4, col("wood", 4)); disc(c, 32, 36, 10, 3, col("lagoon", 2))
    rect(c, 30, 14, 34, 36, col("stone_cool", 2)) if False else None
    return finish(c)


def tree_palm_street():
    c = canvas(CW, CH)
    rect(c, 29, 24, 34, 60, col("wood", 2)); rect(c, 29, 24, 31, 60, col("wood", 3)); rect(c, 32, 24, 34, 60, col("wood", 1))
    for k in range(5):
        rect(c, 28, 60 - 10 * k - 1, 35, 60 - 10 * k, col("wood", 1))
    for a in (-1, 1):
        for i, (dx, dy) in enumerate(((6, -2), (12, 0), (18, 4), (22, 9))):
            rect(c, 31 + a * dx - (1 if a < 0 else 0), 20 + dy, 33 + a * dx, 22 + dy + 1, col("palm_frond", 3 if i < 2 else 2))
        line(c, 31, 22, 31 + a * 26, 36, col("palm_frond", 2)); line(c, 31, 21, 31 + a * 20, 12, col("palm_frond", 3))
        line(c, 31, 21, 31 + a * 10, 8, col("palm_frond", 4))
    line(c, 31, 22, 31, 6, col("palm_frond", 3)); line(c, 32, 22, 32, 8, col("palm_frond", 2))
    disc(c, 32, 24, 3, 3, col("wood", 1))
    return finish(c)


PROP_TYPES = ["lamp_iron", "tub_bush", "planter", "bench_stone", "crates_a", "crates_b", "barrels_a", "barrels_b", "sacks", "hay_cart",
              "cannon_s", "cannon_balls", "hitching_post", "signpost", "clothes_line", "rain_barrel"]


def props():
    return [lamp_iron(), tub_bush(), planter(), bench_stone(), crates(0), crates(1), barrels(0), barrels(1), sacks(), hay_cart(), cannon_s(), balls(),
            hitching(), signpost(), clothes(), rain_barrel()]
