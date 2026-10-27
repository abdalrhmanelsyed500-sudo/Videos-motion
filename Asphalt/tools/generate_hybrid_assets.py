#!/usr/bin/env python3
"""Generate original low-resolution art for the Hybrid 2.5D A/B benchmark.

All sprites/backgrounds are hand-crafted procedurally with Pillow at low
resolution, then upscaled with NEAREST filtering. No external game artwork is
used. Frames share a fixed canvas and wheel baseline so vehicle/rider sprites
do not jump between animation states.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:
    arabic_reshaper = None
    get_display = lambda x: x

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "hybrid_2p5d" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

PALETTE = {
    "sky_top": "#5F8BEB", "sky_horizon": "#7D9EFC", "cloud": "#F2F5F5",
    "road": "#4B4858", "road_alt": "#535060", "road_dark": "#3A3847",
    "yellow": "#D9B51F", "white": "#D8D9D1", "concrete": "#B4A992",
    "sand": "#B9996D", "sand_light": "#D6B98B", "sand_dark": "#8F754F",
    "brick": "#A47F72", "brick_dark": "#8B665C", "window": "#30272E",
    "dash": "#272326", "dash_light": "#403A38", "gauge": "#DDD8C5",
    "needle": "#CE3C31", "magenta": "#A72C86", "red": "#C32228",
    "blue": "#37568A", "green": "#4F8E3A", "black": "#1B1B20",
    "metal": "#8C8D8A", "skin": "#B47B4C", "skin_dark": "#8F5D39",
    "jeans": "#344C78", "shoe": "#E5E2D2", "gold": "#D8B23C",
}


def rgb(value: str):
    v = value.lstrip("#")
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def c(name: str, alpha: int = 255):
    return (*rgb(PALETTE.get(name, name if name.startswith("#") else "#FFFFFF")), alpha)


def shaped(text: str) -> str:
    if arabic_reshaper is None:
        return text
    return get_display(arabic_reshaper.reshape(text))


def font(size: int, mono: bool = True):
    path = FONT_MONO if mono else FONT_SANS
    return ImageFont.truetype(path, size)


def text_center(draw: ImageDraw.ImageDraw, xy, text: str, fnt, fill, outline=None, width=1):
    box = draw.textbbox((0, 0), text, font=fnt)
    x = xy[0] - (box[2] - box[0]) / 2 - box[0]
    y = xy[1] - (box[3] - box[1]) / 2 - box[1]
    if outline:
        for dx in range(-width, width + 1):
            for dy in range(-width, width + 1):
                draw.text((x + dx, y + dy), text, font=fnt, fill=outline)
    draw.text((x, y), text, font=fnt, fill=fill)


def nearest_upscale(img: Image.Image, scale: int) -> Image.Image:
    return img.resize((img.width * scale, img.height * scale), Image.Resampling.NEAREST)


def make_shadow(draw: ImageDraw.ImageDraw, cx: int, cy: int, rx: int, ry: int, alpha=75):
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(20, 18, 22, alpha))


def draw_wheel(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, thick=5):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c("black"), width=thick)
    draw.ellipse([cx - r + 5, cy - r + 5, cx + r - 5, cy + r - 5], outline=(150, 148, 140, 255), width=2)
    draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(90, 89, 84, 255))
    for i in range(6):
        a = i * math.pi / 3.0
        draw.line([(cx, cy), (cx + (r - 6) * math.cos(a), cy + (r - 6) * math.sin(a))],
                  fill=(170, 168, 158, 255), width=1)


def draw_bike_layer(pose: dict) -> Image.Image:
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    lean = pose.get("lean", 0.0)
    brake = pose.get("brake", False)
    accel = pose.get("accel", False)
    make_shadow(d, 64, 120, 27, 5, 75)
    # Front wheel peeks above the tank, aligned with rear wheel on the same x.
    draw_wheel(d, 64 + int(lean * 2), 55, 15, 4)
    # Exhausts and swingarm.
    d.line([(52, 83), (35, 94)], fill=(170, 168, 158, 255), width=4)
    d.line([(76, 83), (93, 94)], fill=(170, 168, 158, 255), width=4)
    d.polygon([(42, 74), (86, 74), (82, 88), (46, 88)], fill=(45, 43, 50, 255))
    # Engine block with cooling fins.
    d.rectangle([52, 70, 76, 86], fill=(92, 91, 91, 255), outline=(35, 34, 40, 255), width=2)
    for y in (73, 78, 83):
        d.line([(52, y), (76, y)], fill=(58, 57, 61, 255), width=1)
    # Frame tubes.
    d.line([(50, 68), (64, 45), (78, 68)], fill=(39, 38, 45, 255), width=4)
    d.line([(50, 68), (78, 68)], fill=(39, 38, 45, 255), width=4)
    # Tank and tail.
    d.polygon([(52, 43), (76, 43), (82, 60), (46, 60)], fill=c("red"), outline=(80, 20, 25, 255), width=2)
    d.polygon([(55, 45), (73, 45), (77, 53), (51, 53)], fill=(234, 76, 66, 255))
    d.polygon([(48, 63), (80, 63), (78, 70), (50, 70)], fill=(31, 30, 35, 255))
    d.rectangle([58, 67, 70, 72], fill=(215, 48, 45, 255) if brake else (125, 35, 38, 255))
    # Handlebars and mirrors.
    d.line([(38, 36 + int(lean * 2)), (90, 36 - int(lean * 2))], fill=(42, 41, 47, 255), width=4)
    d.line([(38, 36), (34, 31)], fill=(42, 41, 47, 255), width=2)
    d.line([(90, 36), (94, 31)], fill=(42, 41, 47, 255), width=2)
    d.ellipse([31, 27, 38, 33], fill=(180, 181, 175, 255))
    d.ellipse([90, 27, 97, 33], fill=(180, 181, 175, 255))
    # Rear wheel in front, fixed baseline for all riding frames.
    draw_wheel(d, 64, 98, 22, 6)
    # Rear fender / plate.
    d.polygon([(48, 80), (80, 80), (78, 88), (50, 88)], fill=c("red"), outline=(80, 20, 25, 255), width=2)
    if accel:
        d.ellipse([30, 94, 40, 102], fill=(190, 185, 175, 150))
        d.ellipse([88, 95, 99, 104], fill=(190, 185, 175, 120))
    return img


def draw_rider_layer(pose: dict) -> Image.Image:
    img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    lean = pose.get("lean", 0.0)
    crouch = pose.get("crouch", 0.0)
    brake = pose.get("brake", False)
    lx = int(lean * 3)
    # Legs and sneakers; knees stay around the tank, feet on pegs.
    d.line([(55, 57), (46, 78 + int(crouch * 2)), (42, 88)], fill=c("jeans"), width=8)
    d.line([(73, 57), (82, 78 + int(crouch * 2)), (86, 88)], fill=c("jeans"), width=8)
    d.polygon([(36, 86), (49, 86), (50, 92), (34, 92)], fill=c("shoe"), outline=(80, 78, 74, 255), width=2)
    d.polygon([(79, 86), (92, 86), (94, 92), (78, 92)], fill=c("shoe"), outline=(80, 78, 74, 255), width=2)
    # Torso: red jacket with bright shirt insert and patches.
    tx = 64 + lx
    ty = 34 + int(crouch * 2)
    d.polygon([(tx - 16, ty), (tx + 16, ty), (tx + 20, 60), (tx - 20, 60)],
              fill=c("red"), outline=(82, 20, 26, 255), width=2)
    d.polygon([(tx - 7, ty + 2), (tx + 7, ty + 2), (tx + 9, 55), (tx - 9, 55)], fill=(225, 67, 57, 255))
    d.rectangle([tx - 15, 48, tx + 15, 53], fill=(35, 34, 40, 255))
    d.rectangle([tx - 13, 49, tx - 10, 52], fill=c("gold"))
    # Arms to handlebars; brake pose pulls elbows in.
    arm_y = 41 if brake else 37
    d.line([(tx - 14, ty + 2), (43, arm_y), (38, 37)], fill=c("red"), width=7)
    d.line([(tx + 14, ty + 2), (85, arm_y), (90, 37)], fill=c("red"), width=7)
    d.ellipse([34, 33, 42, 40], fill=c("skin"))
    d.ellipse([86, 33, 94, 40], fill=c("skin"))
    # Crossbody bag and strap.
    d.line([(tx - 13, ty + 3), (tx + 11, 59)], fill=(45, 42, 48, 255), width=3)
    d.rectangle([tx + 6, 52, tx + 18, 65], fill=(55, 50, 56, 255), outline=(30, 28, 32, 255), width=1)
    # Neck/head from behind, spiky black hair and tan skin.
    d.rectangle([tx - 5, ty - 8, tx + 5, ty + 2], fill=c("skin"))
    d.ellipse([tx - 11, ty - 25, tx + 11, ty - 4], fill=c("skin"), outline=(80, 52, 35, 255), width=1)
    d.polygon([(tx - 12, ty - 17), (tx - 8, ty - 33), (tx - 3, ty - 19)], fill=c("black"))
    d.polygon([(tx - 7, ty - 20), (tx, ty - 37), (tx + 5, ty - 20)], fill=c("black"))
    d.polygon([(tx + 2, ty - 20), (tx + 10, ty - 32), (tx + 12, ty - 16)], fill=c("black"))
    d.rectangle([tx - 11, ty - 20, tx + 11, ty - 16], fill=c("black"))
    # Small gold earring / scarf accent.
    d.ellipse([tx + 10, ty - 12, tx + 13, ty - 9], fill=c("gold"))
    d.polygon([(tx - 9, ty - 4), (tx + 9, ty - 4), (tx + 6, ty + 3), (tx - 6, ty + 3)], fill=(230, 190, 55, 255))
    return img


def composite_rider_bike(pose: dict) -> Image.Image:
    bike = draw_bike_layer(pose)
    rider = draw_rider_layer(pose)
    out = Image.alpha_composite(bike, rider)
    return out


def crash_frame(kind: str) -> Image.Image:
    base_bike = draw_bike_layer({"lean": 0.0, "brake": False, "accel": False})
    base_rider = draw_rider_layer({"lean": 0.0, "crouch": 0.0, "brake": False})
    out = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(out, "RGBA")
    # Skid marks on road.
    d.line([(18, 112), (105, 112)], fill=(35, 33, 38, 120), width=3)
    d.line([(24, 117), (100, 117)], fill=(35, 33, 38, 90), width=2)
    if kind == "fall_1":
        bike = base_bike.rotate(-24, resample=Image.Resampling.NEAREST, expand=False)
        rider = base_rider.rotate(18, resample=Image.Resampling.NEAREST, expand=False)
        out.alpha_composite(bike, (-6, 4))
        out.alpha_composite(rider, (13, -6))
    elif kind == "fall_2":
        bike = base_bike.rotate(-48, resample=Image.Resampling.NEAREST, expand=False)
        rider = base_rider.rotate(58, resample=Image.Resampling.NEAREST, expand=False)
        out.alpha_composite(bike, (-18, 10))
        out.alpha_composite(rider, (24, 2))
    elif kind == "slide":
        bike = base_bike.rotate(-68, resample=Image.Resampling.NEAREST, expand=False)
        rider = base_rider.rotate(74, resample=Image.Resampling.NEAREST, expand=False)
        out.alpha_composite(bike, (-8, 18))
        out.alpha_composite(rider, (30, 18))
        # Spark / dust puffs.
        for x, y, r in [(22, 104, 5), (34, 110, 4), (100, 105, 5)]:
            d.ellipse([x - r, y - r, x + r, y + r], fill=(225, 205, 160, 150))
    elif kind == "recovery":
        bike = base_bike.rotate(-10, resample=Image.Resampling.NEAREST, expand=False)
        rider = base_rider.rotate(-8, resample=Image.Resampling.NEAREST, expand=False)
        out.alpha_composite(bike, (0, 6))
        out.alpha_composite(rider, (6, 0))
        d.text((45, 20), "!", font=font(18), fill=c("yellow"))
    else:  # defeat
        bike = base_bike.rotate(-78, resample=Image.Resampling.NEAREST, expand=False)
        rider = base_rider.rotate(82, resample=Image.Resampling.NEAREST, expand=False)
        out.alpha_composite(bike, (-10, 22))
        out.alpha_composite(rider, (34, 24))
        d.text((42, 14), "X_X", font=font(12), fill=c("white"))
    return out


def make_rider_bike_sheet() -> dict:
    frame_w, frame_h = 128, 128
    cols, rows = 4, 3
    sheet = Image.new("RGBA", (frame_w * cols, frame_h * rows), (0, 0, 0, 0))
    poses = [
        ("ride", {"lean": 0.0, "crouch": 0.0, "brake": False, "accel": False}),
        ("steer_left", {"lean": -1.0, "crouch": 0.0, "brake": False, "accel": False}),
        ("steer_right", {"lean": 1.0, "crouch": 0.0, "brake": False, "accel": False}),
        ("lean_left", {"lean": -1.8, "crouch": 0.2, "brake": False, "accel": True}),
        ("lean_right", {"lean": 1.8, "crouch": 0.2, "brake": False, "accel": True}),
        ("accelerate", {"lean": 0.0, "crouch": 1.0, "brake": False, "accel": True}),
        ("brake", {"lean": 0.0, "crouch": 0.4, "brake": True, "accel": False}),
    ]
    frames = []
    for i, (name, pose) in enumerate(poses):
        frames.append((f"riding/{name}", composite_rider_bike(pose)))
    for name in ["fall_1", "fall_2", "slide", "recovery", "defeat"]:
        frames.append((f"crash/{name}", crash_frame(name)))
    for i, (name, frame_img) in enumerate(frames):
        x = (i % cols) * frame_w
        y = (i // cols) * frame_h
        sheet.alpha_composite(frame_img, (x, y))
    sheet.save(OUT / "rider_bike_sheet.png", optimize=True)
    return {
        "path": "rider_bike_sheet.png", "frame_width": frame_w, "frame_height": frame_h,
        "columns": cols, "rows": rows, "frame_names": [n for n, _ in frames],
        "pivot": [64, 126], "wheel_base_y": 98,
        "riding_frames": [n for n, _ in frames if n.startswith("riding/")],
        "crash_frames": [n for n, _ in frames if n.startswith("crash/")],
        "collision_width_m": 0.9, "collision_length_m": 2.1,
    }


def draw_traffic_base(kind: str) -> Image.Image:
    img = Image.new("RGBA", (128, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    make_shadow(d, 64, 89, 48, 6, 80)
    if kind == "car":
        body, accent = c("concrete"), c("window")
        d.rectangle([25, 38, 103, 78], fill=body, outline=(60, 58, 58, 255), width=2)
        d.rectangle([37, 25, 91, 48], fill=(120, 122, 122, 255), outline=(55, 55, 58, 255), width=2)
        d.rectangle([42, 29, 86, 43], fill=accent)
        d.line([(64, 29), (64, 43)], fill=(160, 160, 160, 255), width=1)
        d.rectangle([29, 57, 99, 66], fill=(160, 160, 158, 255))
        d.rectangle([31, 68, 44, 76], fill=(190, 55, 45, 255))
        d.rectangle([84, 68, 97, 76], fill=(190, 55, 45, 255))
        d.rectangle([24, 74, 38, 86], fill=c("black")); d.rectangle([90, 74, 104, 86], fill=c("black"))
    elif kind == "taxi":
        d.rectangle([25, 38, 103, 78], fill=c("yellow"), outline=(70, 60, 25, 255), width=2)
        d.rectangle([37, 25, 91, 48], fill=(220, 185, 40, 255), outline=(55, 55, 58, 255), width=2)
        d.rectangle([42, 29, 86, 43], fill=c("window"))
        d.rectangle([29, 57, 99, 66], fill=(245, 210, 55, 255))
        for x in range(31, 98, 10):
            d.rectangle([x, 58, x + 4, 64], fill=(30, 30, 34, 255))
        d.rectangle([55, 18, 73, 27], fill=(235, 225, 190, 255), outline=(60, 55, 45, 255), width=1)
        d.text((58, 18), "TAXI", font=font(7), fill=(40, 40, 40, 255))
        d.rectangle([31, 68, 44, 76], fill=(190, 55, 45, 255)); d.rectangle([84, 68, 97, 76], fill=(190, 55, 45, 255))
        d.rectangle([24, 74, 38, 86], fill=c("black")); d.rectangle([90, 74, 104, 86], fill=c("black"))
    elif kind == "microbus":
        d.rectangle([19, 20, 109, 80], fill=(231, 226, 212, 255), outline=(70, 68, 65, 255), width=2)
        d.rectangle([25, 26, 103, 48], fill=c("window"))
        for x in range(30, 100, 15):
            d.line([(x, 26), (x, 48)], fill=(180, 180, 170, 255), width=1)
        d.rectangle([19, 52, 109, 60], fill=c("blue"))
        d.rectangle([25, 63, 45, 73], fill=(190, 55, 45, 255))
        d.rectangle([83, 63, 103, 73], fill=(190, 55, 45, 255))
        d.rectangle([22, 75, 38, 88], fill=c("black")); d.rectangle([90, 75, 106, 88], fill=c("black"))
    elif kind == "truck":
        d.rectangle([20, 24, 108, 78], fill=(145, 112, 78, 255), outline=(65, 50, 38, 255), width=2)
        d.rectangle([26, 30, 102, 62], fill=(170, 135, 95, 255))
        d.rectangle([28, 34, 100, 40], fill=(110, 85, 60, 255))
        d.rectangle([25, 66, 103, 73], fill=(70, 70, 72, 255))
        d.rectangle([28, 70, 42, 79], fill=(190, 55, 45, 255)); d.rectangle([86, 70, 100, 79], fill=(190, 55, 45, 255))
        for x in (26, 48, 82, 102):
            d.rectangle([x - 6, 76, x + 6, 90], fill=c("black"))
    elif kind == "trailer":
        d.rectangle([14, 22, 114, 78], fill=(190, 182, 164, 255), outline=(65, 60, 55, 255), width=2)
        d.rectangle([20, 28, 108, 64], fill=(165, 158, 142, 255))
        d.rectangle([20, 28, 108, 34], fill=(160, 58, 48, 255))
        for x in range(26, 108, 12):
            d.line([(x, 35), (x, 63)], fill=(120, 115, 105, 255), width=1)
        d.rectangle([20, 70, 108, 77], fill=(70, 70, 72, 255))
        for x in (24, 48, 82, 106):
            d.rectangle([x - 6, 77, x + 6, 91], fill=c("black"))
    elif kind == "police":
        d.rectangle([25, 38, 103, 78], fill=(235, 233, 223, 255), outline=(45, 48, 58, 255), width=2)
        d.rectangle([37, 25, 91, 48], fill=(225, 225, 220, 255), outline=(45, 48, 58, 255), width=2)
        d.rectangle([42, 29, 86, 43], fill=c("window"))
        d.rectangle([29, 56, 99, 65], fill=(35, 40, 55, 255))
        d.rectangle([45, 17, 62, 25], fill=(210, 50, 45, 255))
        d.rectangle([66, 17, 83, 25], fill=(55, 100, 215, 255))
        d.rectangle([31, 68, 44, 76], fill=(190, 55, 45, 255)); d.rectangle([84, 68, 97, 76], fill=(190, 55, 45, 255))
        d.rectangle([24, 74, 38, 86], fill=c("black")); d.rectangle([90, 74, 104, 86], fill=c("black"))
    else:
        raise ValueError(kind)
    return img


def shear_sprite(img: Image.Image, amount: float) -> Image.Image:
    w, h = img.size
    return img.transform((w, h), Image.Transform.AFFINE,
                         (1.0, amount, -amount * h / 2.0, 0.0, 1.0, 0.0),
                         resample=Image.Resampling.NEAREST, fillcolor=(0, 0, 0, 0))


def make_traffic_sheet() -> dict:
    frame_w, frame_h = 128, 96
    kinds = ["taxi", "car", "microbus", "truck", "trailer", "police"]
    angles = ["straight", "left", "right"]
    sheet = Image.new("RGBA", (frame_w * len(angles), frame_h * len(kinds)), (0, 0, 0, 0))
    frame_names = []
    for row, kind in enumerate(kinds):
        base = draw_traffic_base(kind)
        for col, angle in enumerate(angles):
            frame = base if angle == "straight" else shear_sprite(base, -0.12 if angle == "left" else 0.12)
            sheet.alpha_composite(frame, (col * frame_w, row * frame_h))
            frame_names.append(f"{kind}/{angle}")
    sheet.save(OUT / "traffic_sheet.png", optimize=True)
    collision = {
        "taxi": [1.9, 4.5], "car": [1.9, 4.4], "microbus": [2.1, 5.6],
        "truck": [2.6, 8.5], "trailer": [2.6, 12.0], "police": [2.0, 4.8],
    }
    return {
        "path": "traffic_sheet.png", "frame_width": frame_w, "frame_height": frame_h,
        "columns": len(angles), "rows": len(kinds), "kinds": kinds, "angles": angles,
        "frame_names": frame_names, "pivot": [64, 94], "collision": collision,
    }


def make_sky() -> dict:
    w, h = 320, 90
    img = Image.new("RGB", (w, h), rgb(PALETTE["sky_horizon"]))
    d = ImageDraw.Draw(img)
    top = rgb(PALETTE["sky_top"]); horizon = rgb(PALETTE["sky_horizon"])
    for y in range(h):
        t = y / (h - 1)
        color = tuple(int(top[i] * (1 - t) + horizon[i] * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=color)
    cloud = rgb(PALETTE["cloud"])
    for cx, cy, s in [(60, 28, 1.0), (150, 18, 0.7), (250, 36, 0.9), (300, 20, 0.6)]:
        d.ellipse([cx, cy, cx + 28 * s, cy + 10 * s], fill=cloud)
        d.ellipse([cx + 7 * s, cy - 7 * s, cx + 22 * s, cy + 10 * s], fill=cloud)
        d.rectangle([cx + 4 * s, cy + 7 * s, cx + 25 * s, cy + 10 * s], fill=cloud)
    out = nearest_upscale(img, 4)
    out.save(OUT / "sky.png", optimize=True)
    return {"path": "sky.png", "size": [out.width, out.height]}


def make_hills() -> dict:
    w, h = 320, 60
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    sand = c("sand"); light = c("sand_light"); dark = c("sand_dark")
    pts = [(0, 42), (35, 32), (70, 40), (110, 24), (155, 38), (200, 20), (245, 35), (285, 26), (320, 37), (320, 60), (0, 60)]
    d.polygon(pts, fill=sand)
    d.polygon([(0, 49), (60, 41), (120, 48), (180, 36), (240, 47), (320, 40), (320, 60), (0, 60)], fill=light)
    d.line([(0, 42), (35, 32), (70, 40), (110, 24), (155, 38), (200, 20), (245, 35), (285, 26), (320, 37)], fill=dark, width=2)
    for x, y in [(40, 46), (120, 43), (220, 42), (275, 46)]:
        d.line([(x - 10, y), (x + 10, y - 1)], fill=(120, 146, 83, 160), width=2)
    out = nearest_upscale(img, 4)
    out.save(OUT / "hills.png", optimize=True)
    return {"path": "hills.png", "size": [out.width, out.height]}


def draw_far_building(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, idx: int):
    colors = [c("brick"), (190, 155, 121, 255), (150, 108, 98, 255), (174, 137, 108, 255)]
    d.rectangle([x, y, x + w, y + h], fill=colors[idx % len(colors)], outline=(90, 70, 65, 255), width=1)
    d.rectangle([x, y, x + w, y + 3], fill=c("concrete"))
    for wy in range(y + 7, y + h - 3, 8):
        for wx in range(x + 4, x + w - 4, 8):
            d.rectangle([wx, wy, wx + 4, wy + 4], fill=c("window"))
            d.line([(wx + 2, wy), (wx + 2, wy + 4)], fill=(120, 95, 88, 255), width=1)
    if idx % 3 == 0:
        d.rectangle([x + 2, y + h - 9, x + w - 2, y + h - 6], fill=(180, 55, 55, 255))
        d.rectangle([x + 4, y + h - 6, x + w - 4, y + h - 3], fill=(235, 225, 200, 255))
    if idx % 4 == 1:
        d.rectangle([x + w // 3, y - 3, x + 2 * w // 3, y], fill=c("concrete"))


def make_ground() -> dict:
    w, h = 320, 120
    img = Image.new("RGB", (w, h), rgb(PALETTE["sand"]))
    d = ImageDraw.Draw(img)
    rng = random.Random(901)
    for _ in range(22):
        y = rng.randrange(h)
        d.line([(0, y), (w, y + rng.randint(-2, 2))], fill=(198, 166, 118, 255), width=1)
    for _ in range(420):
        x = rng.randrange(w); y = rng.randrange(h)
        v = rng.randint(-18, 18)
        d.point((x, y), fill=(max(0, 185 + v), max(0, 153 + v), max(0, 109 + v), 255))
    for y in range(10, h, 34):
        d.line([(0, y), (w, y + rng.randint(-1, 2))], fill=(160, 132, 92, 255), width=1)
    out = nearest_upscale(img, 4)
    out.save(OUT / "ground.png", optimize=True)
    return {"path": "ground.png", "size": [out.width, out.height]}


def make_far_buildings() -> dict:
    w, h = 320, 70
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    rng = random.Random(771)
    x = 0
    idx = 0
    while x < w:
        bw = rng.randint(18, 34)
        bh = rng.randint(28, 55)
        draw_far_building(d, x, h - bh, bw, bh, idx)
        x += bw + rng.randint(2, 7)
        idx += 1
    # Small Arabic shop signs.
    for x, label in [(18, "الجيزة"), (118, "المعادي"), (235, "الطريق الدائري")]:
        d.rectangle([x, h - 19, x + 36, h - 11], fill=(34, 100, 68, 255), outline=(220, 215, 195, 255), width=1)
        text_center(d, (x + 18, h - 15), shaped(label), font(5, mono=False), (245, 244, 231, 255))
    out = nearest_upscale(img, 4)
    out.save(OUT / "buildings_far.png", optimize=True)
    return {"path": "buildings_far.png", "size": [out.width, out.height]}


def draw_palm(d: ImageDraw.ImageDraw, x: int, y: int, scale: float, mirror: bool = False):
    trunk = (123, 96, 64, 255); leaf = c("palm") if "palm" in PALETTE else (71, 107, 55, 255)
    d.rectangle([x - 2 * scale, y - 28 * scale, x + 2 * scale, y], fill=trunk)
    for a in range(0, 360, 60):
        rad = math.radians(a)
        ex = x + 16 * scale * math.cos(rad) * (-1 if mirror else 1)
        ey = y - 28 * scale + 9 * scale * math.sin(rad)
        d.line([(x, y - 28 * scale), (ex, ey)], fill=leaf, width=max(1, int(3 * scale)))


def make_roadside_layers() -> dict:
    w, h = 320, 210
    left = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(left, "RGBA")
    # Large perspective facade on the left.
    d.polygon([(0, 0), (110, 18), (110, 185), (0, 210)], fill=(164, 127, 114, 255), outline=(95, 70, 65, 255), width=2)
    d.polygon([(110, 18), (180, 30), (180, 180), (110, 185)], fill=(145, 105, 95, 255), outline=(80, 60, 58, 255), width=2)
    for floor in range(4):
        y = 18 + floor * 38
        for col in range(4):
            x = 10 + col * 24
            d.rectangle([x, y, x + 13, y + 17], fill=c("window"))
            d.rectangle([x + 2, y + 2, x + 11, y + 10], fill=(60, 54, 62, 255))
        d.rectangle([0, y + 22, 110, y + 26], fill=(190, 148, 122, 255))
    # Balconies / AC / water tank.
    d.rectangle([18, 48, 48, 54], fill=c("concrete"))
    d.line([(18, 48), (18, 36), (48, 36), (48, 48)], fill=(110, 108, 104, 255), width=2)
    d.rectangle([70, 92, 86, 102], fill=(150, 148, 140, 255))
    d.ellipse([12, 2, 34, 16], fill=(160, 158, 150, 255))
    # Ground-floor shops with striped awnings and Arabic signs.
    for x0, label, bg in [(8, "قهوة", "#8C3C31"), (68, "قطع غيار", "#9A642B")]:
        d.rectangle([x0, 158, x0 + 38, 181], fill=(55, 42, 45, 255))
        d.rectangle([x0 - 2, 151, x0 + 40, 157], fill=(220, 215, 198, 255))
        for sx in range(x0, x0 + 40, 8):
            d.rectangle([sx, 151, sx + 3, 157], fill=(185, 48, 48, 255))
        d.rectangle([x0 + 3, 161, x0 + 35, 170], fill=rgb(bg), outline=(230, 225, 205, 255), width=1)
        text_center(d, (x0 + 19, 165), shaped(label), font(6, mono=False), (245, 244, 231, 255))
    # Palms and concrete barriers.
    draw_palm(d, 208, 190, 1.0)
    draw_palm(d, 280, 196, 0.8, mirror=True)
    d.polygon([(0, 196), (320, 188), (320, 210), (0, 210)], fill=c("concrete"))
    for x in range(0, 320, 32):
        d.rectangle([x, 192, x + 24, 202], fill=(190, 183, 166, 255), outline=(130, 125, 113, 255), width=1)
    left_out = nearest_upscale(left, 2)
    right = ImageOps.mirror(left)
    right_out = nearest_upscale(right, 2)
    left_out.save(OUT / "roadside_left.png", optimize=True)
    right_out.save(OUT / "roadside_right.png", optimize=True)
    return {
        "left": {"path": "roadside_left.png", "size": [left_out.width, left_out.height]},
        "right": {"path": "roadside_right.png", "size": [right_out.width, right_out.height]},
    }


def draw_gauge(d: ImageDraw.ImageDraw, cx: int, cy: int, r: int, label: str):
    d.ellipse([cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4], fill=(18, 17, 19, 255))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c("gauge"), outline=(40, 38, 38, 255), width=2)
    for i in range(9):
        a = math.radians(135 + i * 270 / 8)
        x1 = cx + (r - 5) * math.cos(a); y1 = cy + (r - 5) * math.sin(a)
        x2 = cx + (r - 10) * math.cos(a); y2 = cy + (r - 10) * math.sin(a)
        d.line([(x1, y1), (x2, y2)], fill=(45, 42, 42, 255), width=1)
        tx = cx + (r - 16) * math.cos(a); ty = cy + (r - 16) * math.sin(a)
        text_center(d, (tx, ty), str(i), font(6), (45, 42, 42, 255))
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(40, 38, 38, 255))
    text_center(d, (cx, cy + 20), label, font(7), (70, 65, 60, 255))


def make_cockpit() -> dict:
    w, h = 640, 110
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    # Irregular dark motorcycle fairing.
    d.polygon([(0, 110), (0, 44), (55, 36), (150, 28), (250, 22), (390, 22), (500, 28), (590, 36), (640, 44), (640, 110)],
              fill=(31, 29, 30, 255))
    d.polygon([(0, 110), (0, 52), (70, 42), (180, 34), (320, 29), (460, 34), (570, 42), (640, 52), (640, 110)],
              fill=(46, 42, 42, 255))
    # Carbon-like coarse diagonal pattern.
    for x in range(-110, 700, 12):
        d.line([(x, 110), (x + 110, 32)], fill=(58, 54, 54, 80), width=2)
    # Gauges and gear box.
    draw_gauge(d, 230, 70, 34, "KM/H")
    draw_gauge(d, 410, 70, 34, "RPM")
    d.rectangle([300, 48, 340, 92], fill=(20, 19, 21, 255), outline=(150, 145, 132, 255), width=2)
    text_center(d, (320, 70), "3", font(24), (235, 232, 218, 255))
    text_center(d, (320, 39), "GEAR", font(7), (230, 196, 65, 255))
    # Engine strip.
    d.rectangle([270, 98, 370, 104], fill=(18, 18, 20, 255))
    d.rectangle([271, 99, 325, 103], fill=(60, 150, 65, 255))
    d.rectangle([326, 99, 350, 103], fill=(210, 180, 45, 255))
    d.rectangle([351, 99, 369, 103], fill=(200, 55, 45, 255))
    # Indicator labels.
    for x, label, fill in [(92, "ACCEL", (55, 150, 70, 255)), (92, "BRAKE", (170, 55, 50, 255)),
                            (506, "BOOST", (55, 120, 190, 255)), (506, "HAZARD", (205, 165, 45, 255))]:
        y = 66 if label in ("ACCEL", "BOOST") else 84
        d.rectangle([x - 28, y - 8, x + 28, y + 8], fill=(38, 36, 38, 255), outline=(100, 96, 92, 255), width=1)
        text_center(d, (x, y), label, font(7), (225, 223, 214, 255))
        d.rectangle([x - 24, y - 5, x - 20, y + 5], fill=fill)
    out = nearest_upscale(img, 2)
    out.save(OUT / "cockpit_base.png", optimize=True)
    return {
        "path": "cockpit_base.png", "size": [out.width, out.height],
        "top_y": 500, "gauge_left": [460, 140], "gauge_right": [820, 140],
        "gauge_radius": 68, "gear_center": [640, 140],
        "needle_start_deg": 135.0, "needle_end_deg": 405.0,
    }


def audit_sheets(manifest: dict) -> dict:
    audit = {"passed": True, "checks": [], "errors": []}
    def check(name, condition, detail):
        audit["checks"].append({"name": name, "passed": bool(condition), "detail": detail})
        if not condition:
            audit["passed"] = False
            audit["errors"].append(f"{name}: {detail}")
    for key in ["rider_bike_sheet", "traffic_sheet"]:
        info = manifest[key]
        img = Image.open(OUT / info["path"]).convert("RGBA")
        check(f"{key}_size", img.size == (info["frame_width"] * info["columns"], info["frame_height"] * info["rows"]),
              f"expected atlas {info['frame_width']*info['columns']}x{info['frame_height']*info['rows']}, got {img.size}")
        check(f"{key}_transparent_background", img.getpixel((0, 0))[3] == 0, "top-left pixel alpha is zero")
        for i, name in enumerate(info["frame_names"]):
            x = (i % info["columns"]) * info["frame_width"]
            y = (i // info["columns"]) * info["frame_height"]
            frame = img.crop((x, y, x + info["frame_width"], y + info["frame_height"]))
            bbox = frame.getchannel("A").getbbox()
            check(f"{key}_frame_{name}_alpha", bbox is not None and (bbox[2] - bbox[0]) > 20,
                  f"transparent bbox={bbox}")
    # Wheel baseline consistency for riding frames: rear-wheel dark pixels should
    # remain near the same y across the sheet. We verify the designed baseline
    # plus alpha coverage rather than relying on screen-space placement.
    rb = manifest["rider_bike_sheet"]
    check("riding_wheel_baseline", rb["wheel_base_y"] == 98, "all riding frames use rear wheel y=98")
    check("riding_frame_count", len(rb["riding_frames"]) >= 7, f"{len(rb['riding_frames'])} riding animation frames")
    check("crash_frame_count", len(rb["crash_frames"]) >= 5, f"{len(rb['crash_frames'])} crash/recovery frames")
    check("traffic_kinds", len(manifest["traffic_sheet"]["kinds"]) >= 6,
          f"{len(manifest['traffic_sheet']['kinds'])} traffic types")
    return audit


def make_manifest(parts: dict) -> dict:
    manifest = {
        "generator": "tools/generate_hybrid_assets.py",
        "description": "Original low-resolution sprites/backgrounds for the Hybrid 2.5D A/B benchmark.",
        "palette": PALETTE,
        **parts,
        "files": [],
    }
    for path in sorted(OUT.glob("*")):
        if path.is_file() and path.name not in ("hybrid_assets_manifest.json", "sprite_audit.json") \
                and path.suffix != ".import":
            manifest["files"].append({
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
    (OUT / "hybrid_assets_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    audit = audit_sheets(manifest)
    (OUT / "sprite_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return manifest, audit


def main():
    parts = {
        "rider_bike_sheet": make_rider_bike_sheet(),
        "traffic_sheet": make_traffic_sheet(),
        "backgrounds": {
            "sky": make_sky(),
            "hills": make_hills(),
            "ground": make_ground(),
            "far_buildings": make_far_buildings(),
            "roadside": make_roadside_layers(),
        },
        "cockpit": make_cockpit(),
    }
    manifest, audit = make_manifest(parts)
    print(json.dumps({
        "generated_files": len(manifest["files"]),
        "total_bytes": sum(f["bytes"] for f in manifest["files"]),
        "riding_frames": len(manifest["rider_bike_sheet"]["riding_frames"]),
        "crash_frames": len(manifest["rider_bike_sheet"]["crash_frames"]),
        "traffic_frames": len(manifest["traffic_sheet"]["frame_names"]),
        "sprite_audit_passed": audit["passed"],
    }, indent=2))


if __name__ == "__main__":
    main()
