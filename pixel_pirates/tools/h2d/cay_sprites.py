"""H2D-1.2 new sprites for Anvil Cay: lighthouse, two cottages, a route signpost, and the pirate who walks ashore.

Hand-drawn with numpy/PIL from the project palette (game/data/look/palette.json), like the H2D-1 sprites. Prototype art.
The pirate is male (project content rule), 24 x 32 px cells, 4 facings (south, north, west, east) x 4 frames (idle, 3 walk).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bake_harbor as BH  # noqa: E402
import bake_island as BI  # noqa: E402

col = BH.col
SC_W, SC_H = BH.SC_W, BH.SC_H
PX_, BY_ = BH.SC_PIVOT
HERO_W, HERO_H = 24, 32
HERO_PIVOT = (12, 30)


def sprite_lighthouse() -> np.ndarray:
    img = np.zeros((SC_H, SC_W, 4), np.uint8)
    px, by = PX_, BY_
    top = by - 46
    for y in range(by - 1, top, -1):
        t = (by - 1 - y) / float(by - 1 - top)
        hw = int(round(10.0 - 3.5 * t))
        band = ((by - 1 - y) // 7) % 2
        ramp = "cloth_cream" if band == 0 else "cloth_red"
        for x in range(px - hw, px + hw + 1):
            u = (x - (px - hw)) / max(2 * hw, 1)
            s = 4 if u < 0.25 else (3 if u < 0.6 else 2)
            if u > 0.9:
                s = 1
            img[y, x] = col(ramp, s)
    for x in range(px - 3, px + 4):                      # door
        for y in range(by - 9, by - 1):
            img[y, x] = col("wood", 2 if x > px - 3 else 3)
    for y in (by - 26, by - 27):                         # a slit window
        img[y, px] = col("fire", 3)
        img[y - 1, px] = col("fire", 3)
    for x in range(px - 12, px + 13):                    # gallery
        img[top, x] = col("iron", 3)
        img[top + 1, x] = col("iron", 2)
        img[top - 1, x] = col("iron", 4) if x % 3 else col("iron", 2)
    for y in range(top - 10, top - 1):                   # lamp room: glass lit from within (fire[3]/[4] glow at night)
        for x in range(px - 5, px + 6):
            frame = x in (px - 5, px + 5, px) or y == top - 10
            img[y, x] = col("iron", 3) if frame else col("fire", 4 if (x + y) % 2 else 3)
    for y in range(top - 18, top - 10):                  # roof cone
        k = (y - (top - 18)) / 8.0
        hw = int(round(1 + 6 * k))
        for x in range(px - hw, px + hw + 1):
            img[y, x] = col("roof_teal", 3 if x < px else 2)
    img[top - 20:top - 18, px] = col("iron", 4)
    img[..., 3] = np.where(img[..., 3] > 127, 255, 0)
    BI._outline(img, "iron")
    return img


def sprite_cottage(variant: int) -> np.ndarray:
    def extras(c, x0, x1, yw, by):
        if variant == 0:
            for y in range(yw - 14, yw - 3):             # chimney
                for x in range(x1 - 8, x1 - 4):
                    c[y, x] = col("stone_warm", 2 if x > x1 - 7 else 3)
        else:
            for xx in range(x0 + 9, x0 + 17):            # a little awning over the door
                for yy in range(by - 17, by - 14):
                    c[yy, xx] = col("cloth_cream", 3 if (xx // 2) % 2 else 2)
    if variant == 0:
        return BH.building(30, 14, 11, 2, 61, "cloth_red", (0, 1, 2, 3), doors=(11,), windows=((3, 3), (19, 3)), extras=extras)
    return BH.building(28, 13, 10, 2, 71, "roof_teal", (1, 2, 3, 4), doors=(10,), windows=((3, 3), (17, 3)), extras=extras)


def sprite_signpost() -> np.ndarray:
    """Route marker: a pole with a red pennant and a board. Not solid."""
    img = np.zeros((SC_H, SC_W, 4), np.uint8)
    px, by = PX_, BY_
    for y in range(by - 30, by):
        for x in range(px - 1, px + 1):
            img[y, x] = col("wood", 3 if x == px - 1 else 2)
    for y in range(by - 29, by - 23):                    # pennant
        for x in range(px + 1, px + 11 - (y - (by - 29))):
            img[y, x] = col("cloth_red", 3 if (x + y) % 5 else 2)
    for y in range(by - 21, by - 14):                    # board
        for x in range(px - 8, px + 8):
            edge = x in (px - 8, px + 7) or y in (by - 21, by - 15)
            img[y, x] = col("wood", 1) if edge else col("cloth_cream", 3 if (x + y) % 7 else 2)
    for x in range(px - 5, px + 5):                      # lines of writing
        img[by - 19, x] = col("wood", 1)
        img[by - 17, x] = col("wood", 1) if x % 5 else col("cloth_cream", 3)
    for x in range(px - 3, px + 4):
        for y in range(by - 2, by):
            img[y, x] = col("stone_warm", 2 if x > px - 1 else 3)
    img[..., 3] = np.where(img[..., 3] > 127, 255, 0)
    BI._outline(img, "wood")
    return img


def build_struct_atlas() -> Image.Image:
    cells = [BH.sprite_harbourmaster(), BH.sprite_warehouse(), BH.sprite_tavern(), BH.sprite_fisher_hut(), BH.sprite_crates(),
             BH.sprite_barrels(), BH.sprite_pile(), BH.sprite_bollard(), BH.sprite_lantern(), BH.sprite_rowboat(),
             BH.sprite_cannon(), BH.sprite_signal_mast(), BH.sprite_buoy(True), BH.sprite_buoy(False),
             sprite_lighthouse(), sprite_cottage(0), sprite_cottage(1), sprite_signpost()]
    cols, rows = 4, 5
    atlas = Image.new("RGBA", (SC_W * cols, SC_H * rows), (0, 0, 0, 0))
    for i, cell in enumerate(cells):
        atlas.paste(Image.fromarray(cell, "RGBA"), ((i % cols) * SC_W, (i // cols) * SC_H))
    return atlas


STRUCT_TYPES = ["harbourmaster", "warehouse", "tavern", "fisher_hut", "crates", "barrels", "pile", "bollard", "lantern_post",
                "rowboat", "cannon", "signal_mast", "buoy_red", "buoy_cream", "lighthouse", "cottage_a", "cottage_b",
                "signpost"]
STRUCT_COLS, STRUCT_ROWS = 4, 5


# ---- the pirate ----------------------------------------------------------------------------------------------------
def _rect(c, x0, y0, x1, y1, colr):
    """Inclusive-exclusive rectangle on a numpy RGBA canvas."""
    c[max(y0, 0):y1, max(x0, 0):x1] = colr


def _hero_frame(facing: str, frame: int) -> np.ndarray:
    c = np.zeros((HERO_H, HERO_W, 4), np.uint8)
    bob = -1 if frame in (1, 3) else 0
    swing = {0: 0, 1: 1, 2: 0, 3: -1}[frame]       # +1: left leg forward
    skin, skin_d = col("skin_tan", 3), col("skin_tan", 1)
    coat, coat_l, coat_d = col("cloth_red", 3), col("cloth_red", 4), col("cloth_red", 2)
    shirt = col("cloth_cream", 3)
    pants, pants_d = col("cloth_blue", 2), col("cloth_blue", 1)
    boot = col("wood", 1)
    hat, hat_l, trim = col("iron", 2), col("iron", 3), col("gold", 3)
    belt, buckle = col("wood", 2), col("gold", 4)
    hair = col("skin_dark", 0)
    if facing in ("S", "N"):
        lift_l = 1 if swing == 1 else 0
        lift_r = 1 if swing == -1 else 0
        # legs and boots
        _rect(c, 8, 22 + bob, 12, 27 - lift_l, pants)
        _rect(c, 12, 22 + bob, 16, 27 - lift_r, pants)
        _rect(c, 11, 22 + bob, 13, 26, pants_d)
        _rect(c, 7, 27 - lift_l, 12, 30 - lift_l, boot)
        _rect(c, 12, 27 - lift_r, 17, 30 - lift_r, boot)
        # coat
        _rect(c, 7, 12 + bob, 17, 23 + bob, coat)
        _rect(c, 7, 12 + bob, 9, 23 + bob, coat_l)
        _rect(c, 15, 12 + bob, 17, 23 + bob, coat_d)
        _rect(c, 7, 19 + bob, 17, 20 + bob, belt)
        # arms swing against the legs
        al, ar = -swing, swing
        _rect(c, 5, 13 + bob + al, 7, 20 + bob + al, coat_d if facing == "N" else coat)
        _rect(c, 17, 13 + bob + ar, 19, 20 + bob + ar, coat_d)
        _rect(c, 5, 20 + bob + al, 7, 22 + bob + al, skin)
        _rect(c, 17, 20 + bob + ar, 19, 22 + bob + ar, skin)
        # head
        _rect(c, 9, 5 + bob, 15, 12 + bob, skin if facing == "S" else hair)
        if facing == "S":
            _rect(c, 9, 10 + bob, 15, 12 + bob, skin_d)          # beard shadow
            c[8 + bob, 10] = col("iron", 0)
            c[8 + bob, 13] = col("iron", 0)
            _rect(c, 11, 12 + bob, 13, 14 + bob, shirt)             # open collar
            c[19 + bob, 11:13] = buckle
        else:
            _rect(c, 9, 5 + bob, 15, 9 + bob, hair)
            c[19 + bob, 11:13] = coat_d
        # tricorn hat
        _rect(c, 6, 4 + bob, 18, 6 + bob, hat)
        _rect(c, 8, 0 + bob, 16, 4 + bob, hat)
        _rect(c, 6, 4 + bob, 18, 5 + bob, trim)
        _rect(c, 8, 0 + bob, 12, 2 + bob, hat_l)
    else:
        # profile; drawn facing WEST, mirrored for EAST
        s = swing
        _rect(c, 10 - 2 * s, 22 + bob, 14 - 2 * s, 28, pants)       # front leg
        _rect(c, 10 + 2 * s, 22 + bob, 14 + 2 * s, 28, pants_d)      # back leg
        _rect(c, 8 - 2 * s, 28, 14 - 2 * s, 30, boot)
        _rect(c, 10 + 2 * s, 28, 16 + 2 * s, 30, boot)
        _rect(c, 8, 12 + bob, 16, 23 + bob, coat)
        _rect(c, 8, 12 + bob, 10, 23 + bob, coat_l)
        _rect(c, 14, 12 + bob, 16, 23 + bob, coat_d)
        _rect(c, 8, 19 + bob, 16, 20 + bob, belt)
        c[19 + bob, 9:11] = buckle
        _rect(c, 10 + s * 2, 13 + bob, 14 + s * 2, 20 + bob, coat_d)   # the near arm swings
        _rect(c, 10 + s * 2, 20 + bob, 14 + s * 2, 22 + bob, skin)
        _rect(c, 9, 5 + bob, 15, 12 + bob, skin)
        _rect(c, 12, 5 + bob, 15, 12 + bob, hair)                      # hair at the back of the head
        c[8 + bob, 10] = col("iron", 0)
        _rect(c, 8, 8 + bob, 9, 10 + bob, skin)                        # nose
        _rect(c, 9, 10 + bob, 12, 12 + bob, skin_d)
        _rect(c, 6, 4 + bob, 18, 6 + bob, hat)
        _rect(c, 8, 0 + bob, 16, 4 + bob, hat)
        _rect(c, 6, 4 + bob, 18, 5 + bob, trim)
        _rect(c, 8, 0 + bob, 11, 2 + bob, hat_l)
        if facing == "E":
            c = c[:, ::-1].copy()
    c[..., 3] = np.where(c[..., 3] > 127, 255, 0)
    BI._outline(c, "iron")
    return c


def build_hero_atlas() -> Image.Image:
    atlas = Image.new("RGBA", (HERO_W * 4, HERO_H * 4), (0, 0, 0, 0))
    for r, f in enumerate(("S", "N", "W", "E")):
        for k in range(4):
            atlas.paste(Image.fromarray(_hero_frame(f, k), "RGBA"), (k * HERO_W, r * HERO_H))
    return atlas


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "art_bible/h2d1_2"
    out.mkdir(parents=True, exist_ok=True)
    a = build_hero_atlas()
    a.resize((a.width * 5, a.height * 5), Image.NEAREST).save(out / "hero_sheet.png")
    s = build_struct_atlas()
    s.resize((s.width * 2, s.height * 2), Image.NEAREST).save(out / "struct_sheet.png")
    print("wrote previews to", out)
