#!/usr/bin/env python3
"""CP-2 Release B: the five fish of the first fishing grounds as 48x24 pixel-art icons (facing right, 1 px dark outline, three-tone
shading, species markings). Written to game/art/fish/ico_fish_<species>.png and used by the fish-storage panel, the catch card and
the fish flying into the barrels. Deterministic: same output every run. Needs numpy + Pillow.
    python tools/h2d/bake_fish.py            # writes the PNGs
    python tools/h2d/bake_fish.py --sheet X  # also a 6x preview sheet X.png
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[2] / "game" / "art" / "fish"
W, H = 48, 24
OUTLINE = (24, 26, 40, 255)


def hexc(s, a=255):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


class Fish:
    def __init__(self, x0, x1, half_h, cy=12.0, nose=0.75, tail=9, tail_fork=4, belly=0.55):
        self.x0, self.x1, self.half_h, self.cy, self.nose = x0, x1, half_h, cy, nose
        self.tail, self.tail_fork, self.belly = tail, tail_fork, belly

    def profile(self, x):
        t = (x - self.x0) / (self.x1 - self.x0)
        if t < 0 or t > 1:
            return None
        th = math.sin(math.pi * (t ** self.nose)) ** 0.8
        # tail end narrows to a thin peduncle
        th *= (1.0 - 0.45 * max(0.0, (t - 0.72) / 0.28))
        top = self.cy - self.half_h * th * (1.0 - self.belly * 0.0)
        bot = self.cy + self.half_h * th * self.belly + self.half_h * th * (1 - self.belly) * 0.0 + self.half_h * th * 0.0
        # back is rounder, belly a little flatter
        top = self.cy - self.half_h * th
        bot = self.cy + self.half_h * th * (0.55 + 0.45 * self.belly)
        return top, bot


def draw(spec):
    f = Fish(**spec["shape"])
    body = np.zeros((H, W), bool)
    tone = np.zeros((H, W), float)       # 0 back .. 1 belly
    xs = np.arange(W)
    for x in xs:
        pr = f.profile(x + 0.5)
        if pr is None:
            continue
        top, bot = pr
        for y in range(H):
            if top <= y + 0.5 <= bot:
                body[y, x] = True
                tone[y, x] = (y + 0.5 - top) / max(bot - top, 1e-3)
    # tail fin: a fork behind the body
    tail = np.zeros((H, W), bool)
    tx0 = int(f.x1 - 2)
    for x in range(tx0, min(W, tx0 + f.tail + 3)):
        k = (x - tx0) / max(f.tail + 2, 1)
        half = 1.5 + k * (spec["tail_h"])
        notch = f.tail_fork * (1.0 - k) if k > 0.35 else 0
        for y in range(H):
            d = abs(y + 0.5 - f.cy)
            if d <= half and not (d < notch * 0.0 + (spec["tail_cut"] * max(0.0, k - 0.35) / 0.65 * half if spec["tail_cut"] else 0.0)):
                tail[y, x] = True
    # fins: dorsal (above the back), pelvic/anal (below), pectoral (on the side)
    fins = np.zeros((H, W), bool)
    for (fx0, fx1, fh, up) in spec["fins"]:
        for x in range(fx0, fx1 + 1):
            pr = f.profile(x + 0.5)
            if pr is None:
                continue
            top, bot = pr
            t = (x - fx0) / max(fx1 - fx0, 1)
            h = fh * (1.0 - t) ** 0.8 * (0.35 + 0.65 * math.sin(math.pi * min(1.0, t * 0.9 + 0.1)))
            if up:
                for y in range(int(top - h), int(top) + 1):
                    if 0 <= y < H and y + 0.5 < top + 0.5:
                        fins[y, x] = True
            else:
                for y in range(int(bot), int(bot + h) + 1):
                    if 0 <= y < H and y + 0.5 > bot - 0.5:
                        fins[y, x] = True
    img = np.zeros((H, W, 4), np.uint8)
    pal = spec["pal"]
    for y in range(H):
        for x in range(W):
            if body[y, x]:
                t = tone[y, x]
                c = mix(pal["back"], pal["mid"], min(1.0, t / 0.45)) if t < 0.45 else mix(pal["mid"], pal["belly"], (t - 0.45) / 0.55)
                # three-tone banding for the pixel-art look
                if t < 0.28:
                    c = pal["back"]
                elif t < 0.62:
                    c = pal["mid"]
                else:
                    c = pal["belly"]
                if t < 0.12:
                    c = mix(pal["back"], (0, 0, 0, 255), 0.25)
                img[y, x] = c
            elif tail[y, x]:
                img[y, x] = pal["tail"]
            elif fins[y, x]:
                img[y, x] = pal["fin"]
    # markings (functions of body coordinates)
    spec["marks"](img, body, tone, f, pal)
    # eye
    ex, ey = int(f.x0 + (f.x1 - f.x0) * spec["eye_t"]), int(f.cy - f.half_h * spec["eye_dy"])
    img[ey, ex] = (250, 250, 245, 255)
    img[ey, min(ex + 1, W - 1)] = spec["eye_col"]
    # outline
    solid = (img[..., 3] > 0)
    out = img.copy()
    for y in range(H):
        for x in range(W):
            if solid[y, x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and solid[ny, nx]:
                    out[y, x] = OUTLINE
                    break
    # a pale gill line behind the eye
    gx = ex + 3
    for y in range(H):
        if 0 <= gx < W and body[y, gx] and abs(y - f.cy) < f.half_h * 0.85:
            c = out[y, gx]
            out[y, gx] = (int(c[0] * 0.72), int(c[1] * 0.72), int(c[2] * 0.72), 255)
    return Image.fromarray(out, "RGBA")


def marks_sardine(img, body, tone, f, pal):
    for i, x in enumerate((15, 19, 23)):
        y = int(f.cy - 1 + (i % 2))
        if body[y, x]:
            img[y, x] = hexc("#2b3d63")
    for x in range(10, 36):
        y = int(f.cy - f.half_h * 0.35)
        if body[y, x] and tone[y, x] > 0.25:
            img[y, x] = hexc("#bcd2e4")


def marks_mackerel(img, body, tone, f, pal):
    for x in range(9, 40):
        for y in range(H):
            if body[y, x] and tone[y, x] < 0.42:
                if (x + (2 if (x // 3) % 2 else 0) + int(2 * math.sin(x * 0.9))) % 4 == 0:
                    img[y, x] = hexc("#0f3a46")


def marks_parrot(img, body, tone, f, pal):
    for x in range(12, 34):
        for y in range(H):
            if body[y, x] and ((x // 4 + y // 3) % 3 == 0) and tone[y, x] > 0.15:
                img[y, x] = hexc("#e8688a")
    for y in range(H):
        for x in range(6, 12):
            if body[y, x] and tone[y, x] > 0.4:
                img[y, x] = hexc("#f4d37a")
    # the beak: two cream pixels at the nose
    for dy in (0, 1):
        x = int(f.x0 + 1)
        if body[int(f.cy) + dy, x]:
            img[int(f.cy) + dy, x] = hexc("#fff0c8")


def marks_snapper(img, body, tone, f, pal):
    for x in range(10, 36):
        for y in range(H):
            if body[y, x] and tone[y, x] > 0.45 and (x + y) % 5 == 0:
                img[y, x] = hexc("#f6b3a2")
    for x in range(12, 32):
        y = int(f.cy - f.half_h * 0.55)
        if body[y, x]:
            img[y, x] = hexc("#e25a46")


def marks_tuna(img, body, tone, f, pal):
    for x in range(8, 40):
        y = int(f.cy - f.half_h * 0.05)
        if body[y, x]:
            img[y, x] = hexc("#f2c230")
            if body[y + 1, x] and x % 2 == 0:
                img[y + 1, x] = hexc("#e0a916")
    # finlets
    for x in range(34, 41, 2):
        pr = f.profile(x + 0.5)
        if pr:
            top, bot = pr
            if 0 <= int(top) - 1 < H:
                img[int(top) - 1, x] = hexc("#f2c230")
            if int(bot) + 1 < H:
                img[int(bot), x] = hexc("#f2c230")


SPECIES = {
    "spc_sardine": dict(
        shape=dict(x0=3, x1=38, half_h=4.2, cy=12.0, nose=0.8, tail=8, tail_fork=3, belly=0.5), tail_h=6.0, tail_cut=0.6,
        pal=dict(back=hexc("#3b5c8a"), mid=hexc("#9fb8d0"), belly=hexc("#e8eef2"), tail=hexc("#5a7aa6"), fin=hexc("#6c88b0")),
        fins=[(18, 24, 3.5, True), (20, 24, 2.5, False)], marks=marks_sardine, eye_t=0.1, eye_dy=0.2, eye_col=(20, 20, 30, 255)),
    "spc_mackerel": dict(
        shape=dict(x0=2, x1=36, half_h=5.0, cy=12.0, nose=0.75, tail=9, tail_fork=4, belly=0.6), tail_h=7.0, tail_cut=0.7,
        pal=dict(back=hexc("#1f6f78"), mid=hexc("#7fb7b0"), belly=hexc("#e3ece8"), tail=hexc("#2c8089"), fin=hexc("#2a7078")),
        fins=[(13, 19, 4.0, True), (23, 27, 3.0, True), (22, 27, 3.0, False)], marks=marks_mackerel, eye_t=0.1, eye_dy=0.2, eye_col=(20, 20, 30, 255)),
    "spc_parrotfish": dict(
        shape=dict(x0=3, x1=33, half_h=7.2, cy=12.0, nose=0.55, tail=8, tail_fork=1, belly=0.85), tail_h=7.5, tail_cut=0.0,
        pal=dict(back=hexc("#1e8f87"), mid=hexc("#3cc3b0"), belly=hexc("#8fe0c9"), tail=hexc("#e8688a"), fin=hexc("#e8688a")),
        fins=[(10, 28, 4.2, True), (14, 22, 3.0, False)], marks=marks_parrot, eye_t=0.2, eye_dy=0.3, eye_col=(120, 40, 60, 255)),
    "spc_red_snapper": dict(
        shape=dict(x0=2, x1=35, half_h=6.6, cy=12.0, nose=0.7, tail=9, tail_fork=2, belly=0.8), tail_h=7.0, tail_cut=0.35,
        pal=dict(back=hexc("#a8281f"), mid=hexc("#d9503b"), belly=hexc("#f2a090"), tail=hexc("#c8402f"), fin=hexc("#b8321f")),
        fins=[(10, 28, 4.6, True), (18, 26, 3.4, False)], marks=marks_snapper, eye_t=0.14, eye_dy=0.25, eye_col=(160, 20, 20, 255)),
    "spc_yellowfin_tuna": dict(
        shape=dict(x0=1, x1=38, half_h=6.4, cy=12.0, nose=0.7, tail=8, tail_fork=4, belly=0.7), tail_h=8.5, tail_cut=0.8,
        pal=dict(back=hexc("#15264f"), mid=hexc("#4b6fa8"), belly=hexc("#d3dce5"), tail=hexc("#2a3f73"), fin=hexc("#f2c230")),
        fins=[(15, 21, 5.0, True), (26, 30, 3.0, True), (18, 24, 3.2, False)], marks=marks_tuna, eye_t=0.1, eye_dy=0.2, eye_col=(20, 20, 30, 255)),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    imgs = {}
    for sid, spec in SPECIES.items():
        im = draw(spec)
        name = "ico_fish_" + sid.replace("spc_", "")
        im.save(OUT / (name + ".png"))
        imgs[sid] = im
        print("wrote", name)
    if "--sheet" in sys.argv:
        path = sys.argv[sys.argv.index("--sheet") + 1]
        s = 6
        sheet = Image.new("RGBA", (W * s * 3, H * s * 2), (60, 90, 120, 255))
        for i, (sid, im) in enumerate(imgs.items()):
            big = im.resize((W * s, H * s), Image.NEAREST)
            sheet.alpha_composite(big, ((i % 3) * W * s, (i // 3) * H * s))
        sheet.save(path + ".png")


if __name__ == "__main__":
    main()
