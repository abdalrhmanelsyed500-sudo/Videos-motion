#!/usr/bin/env python3
"""IRON ATLAS deterministic pixel-art generator (Stage 1 asset family).
Style rules from the supplied references (CHAR D1/R35 sprites + Rogue North):
limited palettes, 3-tone body shading, 1px darker rim (no thick outlines),
light from top-left, clean readable texture, consistent 24px units / 32px tiles.
Run:  python3 iron_atlas/tools/make_sprites.py   (needs Pillow)
"""
import os, random
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(__file__), "..", "game", "assets", "sprites")
U = os.path.join(OUT, "units"); T = os.path.join(OUT, "terrain")
os.makedirs(U, exist_ok=True); os.makedirs(T, exist_ok=True)

CAMO = [(126, 140, 88), (152, 166, 104), (98, 112, 72)]
RIM = (52, 60, 42)
STEEL = (110, 114, 104)
STEEL_D = (74, 78, 70)
GLASS = (170, 190, 180)


def px(d, x, y, c):
    d.point((x, y), fill=c + (255,))


def rect(d, x0, y0, x1, y1, c):
    d.rectangle([x0, y0, x1, y1], fill=c + (255,))


def rim_rect(d, x0, y0, x1, y1, c):
    rect(d, x0, y0, x1, y1, c)
    d.rectangle([x0, y0, x1, y1], outline=RIM + (255,))


def unit_tracked(name, body, barrel=True, long_gun=False, turret=True):
    im = Image.new("RGBA", (24, 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rect(d, 4, 4, 6, 19, STEEL_D)          # left track
    rect(d, 17, 4, 19, 19, STEEL_D)        # right track
    for y in range(4, 20, 2):              # track links
        px(d, 5, y, STEEL); px(d, 18, y, STEEL)
    rim_rect(d, 7, 3, 16, 20, body[2])     # hull base (shadow tone)
    rect(d, 7, 3, 16, 12, body[0])         # hull mid
    rect(d, 7, 3, 16, 6, body[1])          # top-light
    px(d, 7, 3, body[1]); px(d, 8, 3, body[1])
    if turret:
        rim_rect(d, 9, 8, 14, 14, body[0])
        rect(d, 9, 8, 14, 10, body[1])
        px(d, 10, 9, GLASS)
    if barrel:
        gy = 2 if long_gun else 4
        rect(d, 11, gy, 12, 8, STEEL_D)
        px(d, 11, gy, STEEL)
    im.save(os.path.join(U, name + ".png"))


def unit_wheeled(name, body, cab=True, bed=False):
    im = Image.new("RGBA", (24, 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rect(d, 6, 5, 7, 18, (40, 38, 36)); rect(d, 16, 5, 17, 18, (40, 38, 36))
    rim_rect(d, 8, 4, 15, 19, body[2])
    rect(d, 8, 4, 15, 10, body[0]); rect(d, 8, 4, 15, 6, body[1])
    if cab:
        rim_rect(d, 9, 5, 14, 9, body[1]); rect(d, 10, 5, 13, 6, GLASS)
    if bed:
        rect(d, 9, 11, 14, 18, body[2]); rect(d, 10, 12, 13, 17, body[0])
    im.save(os.path.join(U, name + ".png"))


def unit_infantry(name):
    im = Image.new("RGBA", (24, 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, (ox, oy) in enumerate([(8, 8), (13, 9), (10, 13), (14, 14)]):
        c = CAMO[i % 3]
        rect(d, ox, oy, ox + 2, oy + 3, c)
        px(d, ox, oy, CAMO[1]); px(d, ox + 2, oy + 3, RIM)
        px(d, ox + 1, oy + 1, (60, 55, 45))   # helmet shadow
    rect(d, 9, 7, 15, 7, STEEL_D)             # rifles line
    im.save(os.path.join(U, name + ".png"))


def unit_artillery(name):
    im = Image.new("RGBA", (24, 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rect(d, 7, 12, 16, 17, STEEL_D)
    rim_rect(d, 8, 10, 15, 16, CAMO[2])
    rect(d, 11, 3, 12, 11, STEEL_D); px(d, 11, 3, STEEL)
    rect(d, 9, 13, 14, 14, CAMO[0])
    im.save(os.path.join(U, name + ".png"))


unit_tracked("tank_light", CAMO, True, False)
unit_tracked("tank_main", [(108, 120, 76), (134, 148, 92), (82, 94, 60)], True, True)
unit_tracked("apc", [(116, 126, 96), (142, 152, 112), (88, 98, 74)], False)
unit_wheeled("pickup", [(140, 132, 100), (166, 158, 122), (108, 100, 76)])
unit_wheeled("truck", [(96, 108, 78), (122, 134, 96), (72, 82, 58)], True, True)
unit_infantry("infantry")
unit_artillery("artillery")

# ------------------------------------------------------------------- terrain
def terrain(name, base, fn):
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rect(d, 0, 0, 31, 31, base)
    rnd = random.Random(hash(name) & 0xFFFF)
    fn(d, rnd)
    im.save(os.path.join(T, name + ".png"))


def speckle(d, rnd, cols, n=60):
    for _ in range(n):
        px(d, rnd.randrange(32), rnd.randrange(32), rnd.choice(cols))


terrain("t_grass", (104, 128, 78), lambda d, r: speckle(d, r, [(92, 116, 68), (116, 140, 88), (84, 106, 62)]))
terrain("t_forest", (72, 100, 58), lambda d, r: [
    (d.ellipse([x, y, x + 7, y + 7], fill=(44, 74, 40), outline=(30, 52, 28)),
     d.point((x + 2, y + 2), fill=(64, 96, 56)))
    for x, y in [(3, 3), (14, 8), (6, 16), (20, 18), (12, 24), (24, 4)]])
terrain("t_snow", (226, 230, 236), lambda d, r: speckle(d, r, [(210, 214, 222), (238, 242, 246), (196, 200, 210)], 80))
terrain("t_desert", (196, 172, 122), lambda d, r: speckle(d, r, [(182, 158, 110), (210, 186, 134), (170, 148, 102)], 70))
terrain("t_urban", (128, 124, 118), lambda d, r: [
    (d.rectangle([x, y, x + 8, y + 7], fill=(150, 146, 138), outline=(84, 80, 76)),
     d.rectangle([x + 2, y + 2, x + 4, y + 3], fill=(96, 92, 88)))
    for x, y in [(2, 2), (16, 6), (6, 16), (20, 20)]])
terrain("t_water", (58, 92, 128), lambda d, r: [
    d.line([(2, y), (29, y)], fill=(74, 108, 144), width=1) for y in (6, 14, 22, 28)])
terrain("t_mountain", (128, 124, 118), lambda d, r: [
    (d.polygon([(x, y + 9), (x + 6, y), (x + 12, y + 9)], fill=(150, 146, 140),
       outline=(84, 80, 76)), d.point((x + 5, y + 2), fill=(210, 208, 204)))
    for x, y in [(2, 6), (15, 2), (8, 18), (20, 16)]])
terrain("t_hills", (116, 132, 84), lambda d, r: [
    d.ellipse([x, y, x + 12, y + 8], fill=(128, 144, 94), outline=(88, 102, 64))
    for x, y in [(2, 4), (14, 12), (4, 20), (18, 22)]])
terrain("t_marsh", (88, 104, 74), lambda d, r: [
    d.ellipse([x, y, x + 7, y + 4], fill=(70, 96, 100)) for x, y in [(4, 6), (18, 12), (8, 22)]])

print("sprites written:", len(os.listdir(U)), "units,", len(os.listdir(T)), "terrain")
