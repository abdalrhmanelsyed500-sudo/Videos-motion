"""CP-1 revision (P3): sprites that tell the player where the fish are and that the nets are out. 64 x 96 px cells, pivot (32, 92), 14.4 px/m.
0 beacon (tall pole, red-and-cream pennant, fish badge: marks a fishing ground from afar), 1 buoy_red, 2 buoy_white, 3 gull_up, 4 gull_down,
5 sparkle (the shimmer of a shoal), 6 cork (a net float), 7 foam (wake puff)."""
from __future__ import annotations

import numpy as np
from PIL import Image

from port_sprites import col, disc, finish, line, new, px, rect

CUE_W, CUE_H = 64, 96
PIVOT = (32, 92)
CUE_TYPES = ["beacon", "buoy_red", "buoy_white", "gull_up", "gull_down", "sparkle", "cork", "foam"]


def beacon():
    c = new(CUE_W, CUE_H)
    rect(c, 30, 14, 34, 86, col("wood", 2)); rect(c, 30, 14, 31, 86, col("wood", 3)); rect(c, 33, 14, 34, 86, col("wood", 1))
    disc(c, 32, 86, 15, 5, col("cloth_red", 2)); disc(c, 31, 85, 11, 3, col("cloth_red", 3))
    rect(c, 18, 86, 46, 88, col("cloth_red", 1))
    for y in range(18, 46):                                  # pennant, streaming to the right
        w = int(26 * (1.0 - (y - 18) / 28.0)) + 2
        for x in range(34, 34 + w):
            px(c, x, y, col("cloth_red", 3) if ((x - 34) // 5 + (y - 18) // 6) % 2 == 0 else col("cloth_cream", 4))
    disc(c, 42, 30, 5, 3, col("sea_deep", 2)); px(c, 47, 30, col("sea_deep", 2)); px(c, 48, 28, col("sea_deep", 2)); px(c, 48, 32, col("sea_deep", 2))   # fish badge
    disc(c, 32, 12, 3, 3, col("gold", 4))
    return finish(c)


def buoy(a, b):
    c = new(CUE_W, CUE_H)
    cx, by = 32, 90
    disc(c, cx, by - 3, 9, 3, col("sea_deep", 1))
    for y in range(by - 22, by - 3):
        w = 4 + (y - (by - 22)) * 5 // 19
        for x in range(cx - w, cx + w + 1):
            px(c, x, y, col(*a) if (y // 5) % 2 == 0 else col(*b))
    rect(c, cx - 1, by - 30, cx + 1, by - 22, col("iron", 2)); disc(c, cx, by - 31, 2, 2, col("gold", 4))
    rect(c, cx - 5, by - 21, cx - 3, by - 6, col("cloth_cream", 4))
    return finish(c)


def gull(up):
    c = new(CUE_W, CUE_H)
    cx, cy = 32, 48
    disc(c, cx, cy, 6, 3, col("cloth_cream", 4)); disc(c, cx + 6, cy - 1, 2, 2, col("cloth_cream", 4)); px(c, cx + 9, cy - 1, col("gold", 3))
    for s in (-1, 1):
        for i in range(0, 18):
            yy = cy - (i * 7 // 18 if up else -(i * 3 // 18)) - (1 if i > 10 and up else 0)
            xx = cx + s * (4 + i)
            px(c, xx, yy, col("cloth_cream", 3 if i < 12 else 1)); px(c, xx, yy + 1, col("cloth_cream", 4 if i < 12 else 0)); px(c, xx, yy - 1, col("cloth_cream", 3))
    return finish(c, "stone_warm")


def sparkle():
    c = new(CUE_W, CUE_H)
    cx, cy = 32, 80
    for i in range(-7, 8):
        px(c, cx + i, cy, (255, 255, 235, 255 if abs(i) < 5 else 150)); px(c, cx, cy + i // 1, (255, 255, 235, 255 if abs(i) < 5 else 150))
    for i in range(-3, 4):
        px(c, cx + i, cy + i, (200, 245, 255, 220)); px(c, cx + i, cy - i, (200, 245, 255, 220))
    px(c, cx, cy, (255, 255, 255, 255))
    return c


def cork():
    c = new(CUE_W, CUE_H)
    cx, by = 32, 88
    disc(c, cx, by - 2, 5, 3, col("cloth_red", 2)); disc(c, cx - 1, by - 4, 3, 1, col("cloth_red", 4))
    disc(c, cx - 14, by, 2, 1, col("cloth_cream", 3)); disc(c, cx + 14, by, 2, 1, col("cloth_cream", 3))
    line(c, cx - 12, by, cx - 5, by - 1, col("cloth_cream", 2)); line(c, cx + 5, by - 1, cx + 12, by, col("cloth_cream", 2))
    return finish(c)


def foam():
    c = new(CUE_W, CUE_H)
    for dx, dy, r in ((-8, 0, 4), (0, -2, 5), (8, 0, 4), (-3, 2, 3), (5, 2, 3)):
        disc(c, 32 + dx, 88 + dy, r, max(r - 2, 1), (255, 255, 250, 235))
    for dx, dy in ((-10, -3), (2, -6), (10, -3)):
        px(c, 32 + dx, 88 + dy, (255, 255, 255, 200))
    return c


def atlas():
    cells = [beacon(), buoy(("cloth_red", 3), ("cloth_cream", 4)), buoy(("cloth_cream", 4), ("sea_deep", 2)), gull(True), gull(False), sparkle(), cork(), foam()]
    im = Image.new("RGBA", (CUE_W * 4, CUE_H * 2), (0, 0, 0, 0))
    for i, a in enumerate(cells):
        im.alpha_composite(Image.fromarray(a, "RGBA"), ((i % 4) * CUE_W, (i // 4) * CUE_H))
    return im


if __name__ == "__main__":
    im = atlas()
    bg = Image.new("RGBA", im.size, (60, 120, 150, 255))
    bg.alpha_composite(im)
    bg = bg.resize((im.size[0] * 3, im.size[1] * 3), Image.NEAREST)
    bg.convert("RGB").save("/tmp/cue_preview.png")
