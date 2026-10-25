#!/usr/bin/env python3
"""EGYPTIAN TUKTUK MAYHEM - authored texture generator (PIL, seeded, deterministic).
Writes PNGs to game/assets/textures/. Detail-on-texture strategy per ART_BIBLE §1/§3: facades carry windows,
balcony doors, AC units, stains; asphalt carries lane paint; no photographic sources; no third-party art.
"""
import os, random
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(__file__), "..", "game", "assets", "textures")
os.makedirs(OUT, exist_ok=True)


def new(seed, size=256):
    r = random.Random(seed)
    im = Image.new("RGB", (size, size))
    return r, im, ImageDraw.Draw(im)


def noise(im, r, amt=10):
    px = im.load()
    for y in range(im.height):
        for x in range(0, im.width, 2):
            d = r.randint(-amt, amt)
            p = px[x, y]
            px[x, y] = (max(0, min(255, p[0] + d)), max(0, min(255, p[1] + d)), max(0, min(255, p[2] + d)))
            if x + 1 < im.width:
                px[x + 1, y] = px[x, y]


def save(im, name):
    im.save(os.path.join(OUT, name + ".png"))
    print("wrote", name)


def asphalt():
    r, im, d = new(11)
    d.rectangle([0, 0, 255, 255], fill=(74, 76, 82))
    noise(im, r, 8)
    d.rectangle([0, 0, 5, 255], fill=(210, 205, 190))            # edge line (u=0, runs along length)
    d.rectangle([250, 0, 255, 255], fill=(210, 205, 190))       # edge line (u=1)
    d.rectangle([124, 20, 132, 120], fill=(225, 220, 200))       # centre dash (v segment)
    for _ in range(26):                                          # patches & tyre polish
        x, y = r.randint(0, 240), r.randint(8, 240)
        d.ellipse([x, y, x + r.randint(6, 22), y + r.randint(4, 10)], fill=(66, 67, 72))
    im = im.filter(ImageFilter.GaussianBlur(0.4))
    save(im, "t_asphalt")


def sidewalk():
    r, im, d = new(12)
    d.rectangle([0, 0, 255, 255], fill=(168, 158, 140))
    for i in range(4):
        for j in range(4):
            t = r.randint(-10, 10)
            d.rectangle([i * 64 + 2, j * 64 + 2, i * 64 + 62, j * 64 + 62],
                        fill=(168 + t, 158 + t, 140 + t))
    noise(im, r, 6)
    save(im, "t_sidewalk")


def facade_a():
    r, im, d = new(21, 512)
    d.rectangle([0, 0, 511, 511], fill=(196, 168, 122))          # sandstone
    noise(im, r, 7)
    for y in range(0, 512, 16):                                  # course lines
        d.line([0, y, 512, y], fill=(180, 152, 108), width=1)
    for row in range(3):                                         # windows + balcony doors + AC
        for col in range(4):
            x, y = 30 + col * 122, 60 + row * 150
            d.rectangle([x, y, x + 62, y + 96], fill=(52, 62, 70))
            d.rectangle([x + 4, y + 4, x + 58, y + 92], fill=(88, 108, 118))
            d.line([x + 31, y, x + 31, y + 96], fill=(230, 226, 210), width=3)
            d.rectangle([x - 6, y - 8, x + 68, y], fill=(226, 220, 202))       # lintel
            if (row + col) % 3 == 0:
                d.rectangle([x + 70, y + 40, x + 96, y + 62], fill=(214, 212, 205))  # AC unit
                d.rectangle([x + 72, y + 44, x + 94, y + 58], fill=(120, 118, 112))
            if (row + col) % 4 == 1:                                             # shutter
                d.rectangle([x - 12, y, x - 2, y + 96], fill=(58, 122, 118))
    for x in (60, 300):                                          # water stains
        d.rectangle([x, 0, x + 10, 512], fill=(172, 146, 104))
    save(im, "t_facade_a")


def facade_b():
    r, im, d = new(22, 512)
    d.rectangle([0, 0, 511, 511], fill=(222, 214, 196))
    noise(im, r, 6)
    d.rectangle([0, 300, 511, 511], fill=(96, 88, 78))           # shopfront base tile
    for i in range(8):
        d.line([i * 64, 300, i * 64, 511], fill=(70, 64, 56), width=2)
    for col in range(3):                                         # big shop glazing + door
        x = 24 + col * 168
        d.rectangle([x, 320, x + 120, 470], fill=(70, 96, 104))
        d.rectangle([x + 6, 326, x + 114, 464], fill=(120, 152, 158))
        d.line([x + 60, 320, x + 60, 470], fill=(240, 236, 220), width=4)
    for col in range(4):                                         # upper windows
        x = 40 + col * 122
        d.rectangle([x, 90, x + 56, 190], fill=(60, 74, 82))
        d.rectangle([x - 6, 186, x + 62, 196], fill=(206, 198, 178))
    save(im, "t_facade_b")


def facade_c():
    r, im, d = new(23)
    d.rectangle([0, 0, 255, 255], fill=(158, 108, 84))           # rural brick
    for y in range(0, 256, 12):
        off = 0 if (y // 12) % 2 == 0 else 16
        for x in range(-16, 256, 32):
            d.rectangle([x + off + 1, y + 1, x + off + 30, y + 10],
                        fill=(158 + r.randint(-14, 14), 108 + r.randint(-10, 10), 84 + r.randint(-8, 8)))
    d.rectangle([90, 90, 150, 170], fill=(58, 66, 72))           # window
    d.rectangle([94, 94, 146, 166], fill=(96, 116, 124))
    d.rectangle([60, 40, 120, 90], fill=(206, 196, 176))         # plaster patch
    noise(im, r, 5)
    save(im, "t_facade_c")


def tuktuk_paint():
    r, im, d = new(31)
    d.rectangle([0, 0, 255, 255], fill=(24, 140, 148))           # jewel teal
    noise(im, r, 6)
    d.rectangle([0, 120, 255, 138], fill=(238, 226, 190))        # cream stripe
    d.rectangle([0, 142, 255, 150], fill=(178, 60, 46))         # red pinstripe
    for _ in range(40):                                          # wear: chips + rust flecks
        x, y = r.randint(0, 250), r.randint(0, 250)
        c = (140, 96, 60) if r.random() < 0.4 else (52, 58, 60)
        d.ellipse([x, y, x + r.randint(1, 4), y + r.randint(1, 3)], fill=c)
    save(im, "t_tuktuk_paint")


def stripes(name, c1, c2, w=32):
    r, im, d = new(41)
    for i in range(0, 256, w * 2):
        d.rectangle([i, 0, i + w - 1, 255], fill=c1)
        d.rectangle([i + w, 0, i + 2 * w - 1, 255], fill=c2)
    noise(im, r, 5)
    save(im, name)


def sign_band():
    r, im, d = new(42)
    d.rectangle([0, 0, 255, 255], fill=(46, 34, 26))
    d.rectangle([4, 4, 251, 251], outline=(196, 158, 74), width=4)   # brass frame
    for i in range(5):                                               # abstract shop emblems (no lettering)
        x = 30 + i * 46
        d.ellipse([x, 96, x + 34, 130], outline=(226, 196, 120), width=3)
        d.polygon([(x + 17, 100), (x + 30, 113), (x + 17, 126), (x + 4, 113)], fill=(178, 60, 46))
    noise(im, r, 4)
    save(im, "t_sign_band")


def wood():
    r, im, d = new(43)
    d.rectangle([0, 0, 255, 255], fill=(146, 106, 62))
    for y in range(0, 256, 42):
        d.line([0, y, 256, y], fill=(110, 78, 44), width=3)
        for x in range(0, 256, 8):
            d.line([x, y + 4, x + r.randint(-2, 2), y + 38], fill=(132, 94, 54), width=1)
    noise(im, r, 6)
    save(im, "t_wood")


def whitewash():
    r, im, d = new(44)
    d.rectangle([0, 0, 255, 255], fill=(228, 224, 212))
    noise(im, r, 7)
    for _ in range(14):
        x, y = r.randint(0, 240), r.randint(0, 240)
        d.ellipse([x, y, x + r.randint(4, 18), y + r.randint(4, 14)], fill=(206, 200, 186))
    save(im, "t_whitewash")


def plate():
    r, im, d = new(45)
    d.rectangle([0, 0, 255, 255], fill=(240, 238, 230))
    d.rectangle([6, 6, 249, 249], outline=(30, 30, 30), width=4)
    d.text((60, 100), "TKM 01", fill=(20, 20, 20))
    save(im, "t_plate")


if __name__ == "__main__":
    asphalt(); sidewalk(); facade_a(); facade_b(); facade_c(); tuktuk_paint()
    stripes("t_awning", (46, 122, 74), (232, 228, 214))
    stripes("t_bump", (226, 186, 40), (36, 34, 32), w=24)
    sign_band(); wood(); whitewash(); plate()
    print("textures:", sorted(os.listdir(OUT)))
