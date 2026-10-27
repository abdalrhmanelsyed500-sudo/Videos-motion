#!/usr/bin/env python3
"""Deterministic asset generator for THE ASPHALT GROOMS.

All textures, data, portraits and audio are original and generated from this
script. The coarse pixel look is intentional: images are authored at low
resolution and nearest-neighbour upscaled, matching the supplied PS1/PS2-era
references.

Usage (from the Asphalt project folder):
    python3 tools/generate_assets.py
Dependencies: Pillow, numpy, arabic-reshaper, python-bidi.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import struct
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:  # pragma: no cover - generation still works without Arabic shaping
    arabic_reshaper = None
    get_display = lambda text: text


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
TEXTURES = ASSETS / "textures"
UI = ASSETS / "ui"
PORTRAITS = UI / "portraits"
SIGNS = TEXTURES / "signs"
AUDIO = ASSETS / "audio"
DATA = ASSETS / "data"

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

PALETTE = {
    "sky_top": "#5F8BEB",
    "sky_horizon": "#7D9EFC",
    "cloud": "#F2F5F5",
    "road": "#585260",
    "road_dark": "#454250",
    "yellow": "#D9B51F",
    "white": "#D8D9D1",
    "concrete": "#B4A992",
    "sand": "#B9996D",
    "sand_light": "#D6B98B",
    "brick": "#A47F72",
    "brick_dark": "#8B665C",
    "window": "#30272E",
    "skin_light": "#C99768",
    "skin_mid": "#A9764B",
    "skin_dark": "#805234",
    "dash": "#272326",
    "dash_light": "#403A38",
    "gauge": "#DDD8C5",
    "needle": "#CE3C31",
    "magenta": "#A72C86",
    "red": "#C32228",
    "blue": "#37568A",
    "green": "#4F8E3A",
    "black": "#1B1B20",
}

RIDERS = [
    {
        "id": "kareem", "name": "Kareem Ibn El-Dawaran", "arabic_name": "كريم ابن الدوران",
        "epithet": "The Ring Road Native", "gender": "masculine",
        "description": "Spiky-haired street racer in a red track jacket, tight jeans and a worn crossbody bag.",
        "skin": "#B47B4C", "shirt": "#C72C32", "jacket": "#A81F27", "pants": "#344C78",
        "shoes": "#E5E2D2", "hair": "#171318", "accent": "#F1CF4B",
        "hair_style": "spikes", "accessory": "crossbody_bag", "build": 1.00,
        "height": 1.78, "aggression": 0.68, "skill": 0.82, "bike_id": "cairo_125",
    },
    {
        "id": "sayed", "name": "Sayed El-Nar", "arabic_name": "سيد النار",
        "epithet": "The Aggressive Rival", "gender": "masculine",
        "description": "Flat-top hair, black racing jacket, red sleeves and a permanent glare in the mirror.",
        "skin": "#9E6740", "shirt": "#1F2027", "jacket": "#25232A", "pants": "#2B3248",
        "shoes": "#C9C4B4", "hair": "#101014", "accent": "#D32B2B",
        "hair_style": "flattop", "accessory": "sunglasses", "build": 1.08,
        "height": 1.82, "aggression": 0.95, "skill": 0.78, "bike_id": "fury_250",
    },
    {
        "id": "tarek", "name": "Tarek El-Behangy", "arabic_name": "طارق البهنجي",
        "epithet": "The Sidewalk Stuntman", "gender": "masculine",
        "description": "Mohawk, yellow windbreaker, blue patched jeans and bright high-tops. Loves wheelies.",
        "skin": "#C08B5E", "shirt": "#E4BD28", "jacket": "#E0A91D", "pants": "#315487",
        "shoes": "#F0D64A", "hair": "#1B1312", "accent": "#3A79C5",
        "hair_style": "mohawk", "accessory": "knee_pads", "build": 0.94,
        "height": 1.74, "aggression": 0.73, "skill": 0.88, "bike_id": "delta_150",
    },
    {
        "id": "mona", "name": "Mona El-Saree'a", "arabic_name": "منى السريعة",
        "epithet": "The Velocity Tuner", "gender": "feminine",
        "description": "Purple cropped jacket, high ponytail, narrow sunglasses and a precise full-throttle style.",
        "skin": "#D09A6A", "shirt": "#A52D8C", "jacket": "#7D2474", "pants": "#263B63",
        "shoes": "#EDE5D6", "hair": "#181218", "accent": "#E6D046",
        "hair_style": "ponytail", "accessory": "helmet_half", "build": 0.88,
        "height": 1.68, "aggression": 0.56, "skill": 0.94, "bike_id": "sprint_200",
    },
    {
        "id": "hassan", "name": "Hassan Custom", "arabic_name": "حسن كاستم",
        "epithet": "The Chrome Mechanic", "gender": "masculine",
        "description": "Denim vest, red bandana, tool bag and a heavily modified low-slung street bike.",
        "skin": "#8F5D39", "shirt": "#B7442F", "jacket": "#315A84", "pants": "#2F3D55",
        "shoes": "#B9B09F", "hair": "#151018", "accent": "#CBC7B6",
        "hair_style": "undercut", "accessory": "bandana", "build": 1.05,
        "height": 1.79, "aggression": 0.66, "skill": 0.86, "bike_id": "khan_custom",
    },
    {
        "id": "fofo", "name": "Fofo El-Alwany", "arabic_name": "فوفو الألواني",
        "epithet": "The Colour Clash", "gender": "masculine",
        "description": "Curly hair, green and yellow colour-blocking, patterned shirt and oversized sneakers.",
        "skin": "#AE7448", "shirt": "#52A13A", "jacket": "#F0C52A", "pants": "#263A6A",
        "shoes": "#E9E4D2", "hair": "#1A1116", "accent": "#F05B2D",
        "hair_style": "curly", "accessory": "chain", "build": 0.97,
        "height": 1.75, "aggression": 0.61, "skill": 0.75, "bike_id": "neon_125",
    },
    {
        "id": "ashraf", "name": "Ashraf El-Leil", "arabic_name": "أشرف الليل",
        "epithet": "The Night Commuter", "gender": "masculine",
        "description": "Black hoodie, dark jeans, cap and an understated bike that is faster than it looks.",
        "skin": "#96613D", "shirt": "#26262D", "jacket": "#191A21", "pants": "#222737",
        "shoes": "#9C9A91", "hair": "#100F14", "accent": "#5B728C",
        "hair_style": "cap", "accessory": "backpack", "build": 1.02,
        "height": 1.80, "aggression": 0.48, "skill": 0.91, "bike_id": "shadow_250",
    },
    {
        "id": "zizo", "name": "Zizo El-Shaboura", "arabic_name": "زيزو الشبورة",
        "epithet": "The Unpredictable One", "gender": "masculine",
        "description": "Tall uneven spikes, orange scarf, longline streetwear and a taste for dangerous gaps.",
        "skin": "#C28B5D", "shirt": "#E8752B", "jacket": "#B94A24", "pants": "#354A70",
        "shoes": "#D9D5C5", "hair": "#191116", "accent": "#31A69B",
        "hair_style": "wild_spikes", "accessory": "scarf", "build": 1.10,
        "height": 1.84, "aggression": 0.88, "skill": 0.72, "bike_id": "desert_350",
    },
]

BIKES = [
    {
        "id": "cairo_125", "name": "Cairo 125", "arabic_name": "قايرو ١٢٥", "type": "commuter",
        "description": "Cheap, reliable everyday motorcycle with upright bars and a narrow frame.",
        "body_color": "#B5252C", "accent_color": "#E1C84B", "dark_color": "#2B2930",
        "top_speed": 56.0, "acceleration": 13.5, "handling": 0.84, "braking": 24.0,
        "mass": 118.0, "wheel_radius": 0.34, "fairing": False, "high_bars": True,
        "exhausts": 1, "custom": False, "unlocked": True,
    },
    {
        "id": "delta_150", "name": "Delta 150", "arabic_name": "دلتا ١٥٠", "type": "lightweight",
        "description": "Small lightweight street bike with quick steering and bright blue bodywork.",
        "body_color": "#2C65A8", "accent_color": "#E9D44A", "dark_color": "#242832",
        "top_speed": 63.0, "acceleration": 16.0, "handling": 0.96, "braking": 26.0,
        "mass": 108.0, "wheel_radius": 0.33, "fairing": False, "high_bars": False,
        "exhausts": 1, "custom": False, "unlocked": True,
    },
    {
        "id": "sprint_200", "name": "Sprint 200", "arabic_name": "سبرنت ٢٠٠", "type": "sport",
        "description": "Low sport fairing, twin headlights and a high-revving engine.",
        "body_color": "#D9D8CE", "accent_color": "#CE3030", "dark_color": "#252730",
        "top_speed": 72.0, "acceleration": 18.0, "handling": 0.90, "braking": 30.0,
        "mass": 132.0, "wheel_radius": 0.35, "fairing": True, "high_bars": False,
        "exhausts": 1, "custom": False, "unlocked": True,
    },
    {
        "id": "khan_custom", "name": "Khan El-Khalili Custom", "arabic_name": "خان الخليلي كاستم", "type": "custom",
        "description": "Purple tank, gold trim, high handlebars, twin exhausts and a stretched rear fender.",
        "body_color": "#7E2B92", "accent_color": "#D8B23C", "dark_color": "#2C2530",
        "top_speed": 68.0, "acceleration": 17.0, "handling": 0.78, "braking": 27.0,
        "mass": 145.0, "wheel_radius": 0.36, "fairing": False, "high_bars": True,
        "exhausts": 2, "custom": True, "unlocked": True,
    },
    {
        "id": "shadow_250", "name": "Shadow 250", "arabic_name": "شادو ٢٥٠", "type": "standard",
        "description": "Dark standard bike with a broad seat and strong mid-range acceleration.",
        "body_color": "#313846", "accent_color": "#6B7B8E", "dark_color": "#1B1E26",
        "top_speed": 66.0, "acceleration": 15.0, "handling": 0.82, "braking": 28.0,
        "mass": 154.0, "wheel_radius": 0.35, "fairing": False, "high_bars": False,
        "exhausts": 1, "custom": False, "unlocked": True,
    },
    {
        "id": "golden_falcon", "name": "Golden Falcon", "arabic_name": "الصقر الذهبي", "type": "rival",
        "description": "The rival's gold and black machine. Unlock it by winning a race.",
        "body_color": "#C59B28", "accent_color": "#20202A", "dark_color": "#191920",
        "top_speed": 80.0, "acceleration": 20.5, "handling": 0.88, "braking": 32.0,
        "mass": 150.0, "wheel_radius": 0.35, "fairing": True, "high_bars": False,
        "exhausts": 2, "custom": True, "unlocked": False,
    },
]

TRAFFIC_TYPES = [
    {"id": "car", "name": "Passenger Car", "mass": 1.0, "speed_min": 19.0, "speed_max": 31.0,
     "length": 4.4, "width": 1.9, "height": 1.4, "color": "#9AA0A1", "accent": "#D4D2C7", "lane_change": 0.55},
    {"id": "taxi", "name": "Cairo Taxi", "mass": 1.0, "speed_min": 18.0, "speed_max": 29.0,
     "length": 4.5, "width": 1.9, "height": 1.5, "color": "#E5BC28", "accent": "#24242A", "lane_change": 0.70},
    {"id": "microbus", "name": "Microbus", "mass": 1.5, "speed_min": 16.0, "speed_max": 25.0,
     "length": 5.6, "width": 2.1, "height": 2.2, "color": "#E7E2D4", "accent": "#2862A4", "lane_change": 0.45},
    {"id": "minibus", "name": "Minibus", "mass": 1.8, "speed_min": 15.0, "speed_max": 23.0,
     "length": 7.2, "width": 2.3, "height": 2.5, "color": "#D7D9CF", "accent": "#3D7C55", "lane_change": 0.30},
    {"id": "truck", "name": "Heavy Truck", "mass": 3.0, "speed_min": 12.0, "speed_max": 19.0,
     "length": 8.5, "width": 2.6, "height": 3.0, "color": "#8B6B4D", "accent": "#3F454A", "lane_change": 0.18},
    {"id": "trailer", "name": "Trailer", "mass": 4.5, "speed_min": 11.0, "speed_max": 17.0,
     "length": 12.0, "width": 2.6, "height": 3.1, "color": "#B9B1A0", "accent": "#A33A32", "lane_change": 0.10},
    {"id": "police", "name": "Egyptian Police Car", "mass": 1.2, "speed_min": 26.0, "speed_max": 45.0,
     "length": 4.8, "width": 2.0, "height": 1.5, "color": "#ECE9DF", "accent": "#202735", "lane_change": 0.85},
]

SETTINGS = {
    "quality": "medium", "resolution_scale": 1.0, "shadows": True,
    "traffic_density": 1.0, "difficulty": 1, "master_volume": 0.75,
    "default_camera": "cockpit", "show_fps": False,
}


def ensure_dirs() -> None:
    for p in [TEXTURES, UI, PORTRAITS, SIGNS, AUDIO, DATA]:
        p.mkdir(parents=True, exist_ok=True)


def rgb(value: str):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int,
             min_size: int = 10, font_path: str | None = None):
    path = font_path or next((p for p in FONT_CANDIDATES if Path(p).exists()), FONT_CANDIDATES[0])
    size = start_size
    while size > min_size:
        font = ImageFont.truetype(path, size)
        box = draw.textbbox((0, 0), text, font=font)
        if box[2] - box[0] <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(path, min_size)


def shaped(text: str) -> str:
    if arabic_reshaper is None:
        return text
    return get_display(arabic_reshaper.reshape(text))


def text_center(draw, xy, text, font, fill, outline=None, outline_width=2, shape=False):
    value = shaped(text) if shape else text
    box = draw.textbbox((0, 0), value, font=font)
    x = xy[0] - (box[2] - box[0]) / 2 - box[0]
    y = xy[1] - (box[3] - box[1]) / 2 - box[1]
    if outline:
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx * dx + dy * dy <= outline_width * outline_width:
                    draw.text((x + dx, y + dy), value, font=font, fill=outline)
    draw.text((x, y), value, font=font, fill=fill)


def noise_image(size, base, spread, seed, channels=3):
    rng = np.random.default_rng(seed)
    h, w = size[1], size[0]
    base_arr = np.array(rgb(base), dtype=np.float32)
    noise = rng.normal(0, spread, (h, w, 1))
    arr = base_arr[None, None, :] + noise
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    if channels == 1:
        gray = arr.mean(axis=2).astype(np.uint8)
        return Image.fromarray(gray, "L")
    return Image.fromarray(arr, "RGB")


def save_lowres(img: Image.Image, path: Path, scale: int = 2, mode="RGB"):
    if img.mode != mode:
        img = img.convert(mode)
    out = img.resize((img.width * scale, img.height * scale), Image.Resampling.NEAREST)
    out.save(path, optimize=True)
    return out


def make_noise_textures():
    road = noise_image((128, 128), PALETTE["road"], 9, 11)
    d = ImageDraw.Draw(road)
    for _ in range(38):
        x, y = np.random.default_rng(100 + _).integers(0, 128, 2)
        d.line([(int(x), int(y)), (int(x) + 8, int(y) + 3)], fill=(58, 56, 68), width=1)
    save_lowres(road, TEXTURES / "asphalt.png", 2)

    sand = noise_image((128, 128), PALETTE["sand"], 14, 23)
    d = ImageDraw.Draw(sand)
    for y in range(4, 128, 18):
        d.line([(0, y), (128, y + 3)], fill=(190, 160, 114), width=1)
    save_lowres(sand, TEXTURES / "sand.png", 2)

    concrete = noise_image((128, 128), PALETTE["concrete"], 10, 31)
    d = ImageDraw.Draw(concrete)
    for x in range(0, 128, 32):
        d.line([(x, 0), (x, 128)], fill=(142, 133, 117), width=1)
    for y in range(0, 128, 42):
        d.line([(0, y), (128, y + 2)], fill=(152, 143, 126), width=1)
    save_lowres(concrete, TEXTURES / "concrete.png", 2)

    carbon = noise_image((64, 64), PALETTE["dash"], 5, 41)
    d = ImageDraw.Draw(carbon)
    for i in range(-64, 128, 8):
        d.line([(i, 0), (i + 64, 64)], fill=(54, 49, 49), width=2)
    save_lowres(carbon, TEXTURES / "carbon.png", 4)

    tile = Image.new("RGB", (64, 64), (173, 193, 174))
    d = ImageDraw.Draw(tile)
    for y in range(0, 64, 16):
        for x in range(0, 64, 16):
            d.rectangle([x, y, x + 15, y + 15], outline=(122, 145, 132), width=1)
    save_lowres(tile, TEXTURES / "hospital_tile.png", 4)

    checker = Image.new("RGB", (32, 32), (235, 233, 220))
    d = ImageDraw.Draw(checker)
    for y in range(0, 32, 8):
        for x in range(0, 32, 8):
            if (x // 8 + y // 8) % 2 == 0:
                d.rectangle([x, y, x + 7, y + 7], fill=(30, 30, 34))
    save_lowres(checker, TEXTURES / "checker.png", 4)

    awning = Image.new("RGB", (128, 32))
    d = ImageDraw.Draw(awning)
    for x in range(0, 128, 16):
        d.rectangle([x, 0, x + 7, 31], fill=(185, 48, 48))
        d.rectangle([x + 8, 0, x + 15, 31], fill=(228, 219, 198))
    save_lowres(awning, TEXTURES / "awning_stripe.png", 2)

    stripe = Image.new("RGB", (128, 32), (232, 229, 216))
    d = ImageDraw.Draw(stripe)
    for x in range(-32, 160, 32):
        d.polygon([(x, 0), (x + 14, 0), (x + 46, 32), (x + 32, 32)], fill=(28, 34, 48))
    save_lowres(stripe, TEXTURES / "police_stripe.png", 2)

    for idx, base in enumerate([PALETTE["brick"], "#B9957F", "#9A6F63"]):
        img = noise_image((128, 128), base, 8, 50 + idx)
        d = ImageDraw.Draw(img)
        for y in range(0, 128, 16):
            d.line([(0, y), (128, y)], fill=rgb(PALETTE["brick_dark"]), width=1)
            offset = 0 if (y // 16) % 2 == 0 else 16
            for x in range(offset, 128, 32):
                d.line([(x, y), (x, y + 15)], fill=rgb(PALETTE["brick_dark"]), width=1)
        # dark recessed windows, 3 across and 3 down
        for wy in [10, 52, 94]:
            for wx in [8, 52, 96]:
                d.rectangle([wx, wy, wx + 24, wy + 25], fill=(38, 31, 36))
                d.rectangle([wx + 2, wy + 2, wx + 22, wy + 19], fill=(50, 43, 50))
                d.line([(wx + 12, wy + 2), (wx + 12, wy + 19)], fill=(112, 93, 84), width=1)
        save_lowres(img, TEXTURES / f"brick_{idx + 1}.png", 2)

    window = Image.new("RGB", (32, 32), (120, 100, 87))
    d = ImageDraw.Draw(window)
    d.rectangle([2, 2, 29, 29], fill=(38, 31, 36))
    d.rectangle([4, 4, 27, 21], fill=(58, 58, 76))
    d.line([(16, 4), (16, 21)], fill=(125, 105, 91), width=1)
    d.line([(4, 13), (27, 13)], fill=(125, 105, 91), width=1)
    save_lowres(window, TEXTURES / "window.png", 4)

    cloud = Image.new("RGBA", (128, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(cloud)
    white = (242, 245, 245, 235)
    d.ellipse([8, 27, 54, 54], fill=white)
    d.ellipse([29, 15, 77, 51], fill=white)
    d.ellipse([58, 22, 111, 53], fill=white)
    d.rectangle([18, 36, 104, 52], fill=white)
    # deliberately coarse stepped top edges
    for x, y in [(18, 30), (35, 18), (55, 14), (75, 18), (94, 28)]:
        d.rectangle([x, y, x + 7, y + 5], fill=white)
    cloud.save(TEXTURES / "cloud.png", optimize=True)


def make_signs():
    signs = [
        ("sign_giza.png", "الجيزة", "GIZA 12 KM", "#246B45"),
        ("sign_ring_road.png", "الطريق الدائري", "CAIRO RING ROAD", "#1D5C86"),
        ("sign_maadi.png", "المعادي", "EL-MAADI 4 KM", "#246B45"),
        ("sign_nasr_city.png", "مدينة نصر", "NASR CITY 18 KM", "#1D5C86"),
        ("shop_cafe.png", "قهوة ومشروبات", "CAFE / JUICE", "#8C3C31"),
        ("shop_spares.png", "قطع غيار موتوسيكلات", "MOTORCYCLE PARTS", "#9A642B"),
    ]
    for filename, arabic, english, background in signs:
        # Opaque signs avoid large translucent quads in the 3D cockpit view.
        img = Image.new("RGB", (256, 96), rgb(background))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([2, 2, 253, 93], radius=4,
                            fill=rgb(background), outline=(231, 226, 207), width=3)
        d.rectangle([8, 8, 247, 87], outline=(170, 183, 169), width=1)
        ar = shaped(arabic)
        font_ar = fit_font(d, ar, 230, 30, 16)
        font_en = fit_font(d, english, 220, 18, 10, FONT_MONO)
        text_center(d, (128, 34), ar, font_ar, (245, 244, 231), (18, 25, 22), 2, shape=False)
        text_center(d, (128, 70), english, font_en, (235, 226, 177), (18, 25, 22), 1)
        save_lowres(img, SIGNS / filename, 1, "RGB")


def make_title_and_backgrounds():
    # Low-resolution menu background, deliberately upscaled with no smoothing.
    w, h = 640, 360
    img = Image.new("RGB", (w, h), rgb(PALETTE["sky_horizon"]))
    d = ImageDraw.Draw(img)
    for y in range(0, 110):
        t = y / 109.0
        c = tuple(int(rgb(PALETTE["sky_top"])[i] * (1 - t) + rgb(PALETTE["sky_horizon"])[i] * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)
    # Dusty ground plane below the horizon; without this the sky color bleeds
    # down the sides of the road and breaks the reference composition.
    d.rectangle([0, 105, w, h], fill=rgb(PALETTE["sand_light"]))
    d.rectangle([0, 176, w, 205], fill=rgb(PALETTE["concrete"]))
    for cx, cy, s in [(90, 42, 1.0), (420, 28, 0.8), (520, 60, 0.6)]:
        d.ellipse([cx, cy, cx + 70 * s, cy + 20 * s], fill=(239, 244, 244))
        d.ellipse([cx + 20 * s, cy - 12 * s, cx + 58 * s, cy + 20 * s], fill=(239, 244, 244))
    # Sandy hills
    d.polygon([(0, 130), (70, 105), (150, 128), (240, 92), (330, 125), (430, 95), (540, 126), (640, 105), (640, 175), (0, 175)], fill=rgb(PALETTE["sand"]))
    d.polygon([(0, 152), (90, 135), (190, 150), (300, 126), (410, 155), (520, 132), (640, 150), (640, 182), (0, 182)], fill=rgb(PALETTE["sand_light"]))
    # Buildings flanking the road
    for side in [-1, 1]:
        for i in range(7):
            x = 20 + i * 32 if side < 0 else 410 + i * 34
            top = 90 + (i % 3) * 22
            bw = 52 - i * 3
            color = [(164, 127, 114), (181, 151, 121), (146, 111, 100)][i % 3]
            d.rectangle([x, top, x + bw, 188], fill=color)
            for wy in range(top + 8, 180, 18):
                for wx in range(x + 6, x + bw - 8, 14):
                    d.rectangle([wx, wy, wx + 7, wy + 8], fill=(43, 34, 39))
            if i % 2 == 0:
                d.rectangle([x - 3, 152, x + bw + 3, 160], fill=(190, 68, 61))
    # Road with strong perspective
    d.polygon([(210, 180), (430, 180), (640, 360), (0, 360)], fill=rgb(PALETTE["road"]))
    d.polygon([(316, 180), (324, 180), (340, 360), (300, 360)], fill=rgb(PALETTE["yellow"]))
    for y in range(190, 360, 30):
        t = (y - 180) / 180.0
        length = 8 + 38 * t
        for side in [-1, 1]:
            x = 320 + side * (35 + 150 * t)
            d.polygon([(x, y), (x + 3 + int(4 * t), y), (x + 8 + int(18 * t), y + length), (x + 1 + int(12 * t), y + length)], fill=rgb(PALETTE["white"]))
    # Barriers
    d.polygon([(0, 245), (85, 192), (100, 194), (0, 266)], fill=(178, 168, 148))
    d.polygon([(640, 245), (555, 192), (540, 194), (640, 266)], fill=(178, 168, 148))
    # Two rival motorcycles from behind
    for cx, cy, col in [(260, 288, (170, 43, 132)), (385, 300, (196, 38, 42))]:
        d.ellipse([cx - 9, cy + 32, cx + 9, cy + 63], fill=(24, 23, 27))
        d.rectangle([cx - 7, cy + 26, cx + 7, cy + 49], fill=col)
        d.ellipse([cx - 9, cy + 7, cx + 9, cy + 25], fill=(42, 32, 34))
        d.polygon([(cx - 10, cy + 20), (cx + 10, cy + 20), (cx + 16, cy + 43), (cx - 16, cy + 43)], fill=col)
        d.rectangle([cx - 14, cy + 42, cx + 14, cy + 48], fill=(165, 35, 40))
    # Retro dashboard cowl
    d.polygon([(0, 360), (0, 322), (110, 309), (250, 301), (390, 301), (530, 309), (640, 322), (640, 360)], fill=(37, 34, 35))
    for cx in [225, 415]:
        d.ellipse([cx - 48, 310, cx + 48, 390], fill=(67, 61, 58), outline=(12, 12, 13), width=4)
        d.ellipse([cx - 37, 318, cx + 37, 382], fill=(218, 213, 194))
        d.line([(cx, 350), (cx + 22, 327)], fill=(200, 55, 45), width=4)
    d.rectangle([296, 316, 344, 355], fill=(25, 23, 25), outline=(110, 103, 95), width=2)
    text_center(d, (320, 335), "3", ImageFont.truetype(FONT_MONO, 28), (238, 235, 220))
    save_lowres(img, UI / "menu_background.png", 2)

    title = Image.new("RGBA", (960, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(title)
    ar = shaped("عرسان الأسفلت")
    ar_font = fit_font(d, ar, 900, 92, 40)
    en_font = fit_font(d, "THE ASPHALT GROOMS", 900, 58, 24, FONT_MONO)
    tag_font = fit_font(d, "THE RING ROAD WAITS FOR NO ONE", 880, 26, 14, FONT_MONO)
    text_center(d, (480, 76), ar, ar_font, (238, 199, 58), (35, 24, 30), 5, shape=False)
    text_center(d, (480, 151), "THE ASPHALT GROOMS", en_font, (233, 231, 217), (36, 28, 33), 4)
    text_center(d, (480, 199), "THE RING ROAD WAITS FOR NO ONE", tag_font, (208, 78, 54), (35, 28, 33), 2)
    title.save(UI / "title.png", optimize=True)

    hospital = Image.new("RGB", (640, 360), (164, 184, 165))
    d = ImageDraw.Draw(hospital)
    for x in range(0, 640, 32):
        d.line([(x, 0), (x, 360)], fill=(139, 162, 143), width=1)
    for y in range(0, 360, 32):
        d.line([(0, y), (640, y)], fill=(139, 162, 143), width=1)
    d.rectangle([20, 25, 240, 165], fill=(104, 151, 190), outline=(54, 65, 70), width=6)
    d.line([(130, 25), (130, 165)], fill=(54, 65, 70), width=4)
    d.line([(20, 95), (240, 95)], fill=(54, 65, 70), width=4)
    d.rectangle([70, 205, 440, 292], fill=(222, 220, 205), outline=(70, 78, 75), width=5)
    d.rectangle([80, 190, 230, 224], fill=(236, 235, 222), outline=(80, 88, 84), width=3)
    d.ellipse([94, 174, 142, 214], fill=(188, 124, 75))
    d.ellipse([102, 178, 126, 192], fill=(242, 239, 226))
    d.rectangle([100, 176, 137, 185], fill=(242, 239, 226))
    d.line([(505, 55), (505, 235)], fill=(85, 88, 86), width=5)
    d.rectangle([486, 48, 524, 72], fill=(215, 224, 215), outline=(85, 88, 86), width=3)
    d.line([(505, 72), (505, 130)], fill=(210, 211, 202), width=2)
    d.rectangle([292, 20, 348, 76], fill=(242, 239, 226), outline=(70, 78, 75), width=3)
    d.rectangle([316, 28, 324, 68], fill=(196, 51, 46))
    d.rectangle([300, 44, 340, 52], fill=(196, 51, 46))
    for x, y, r in [(550, 90, 24), (580, 120, 18), (545, 145, 14)]:
        d.ellipse([x - r, y - r, x + r, y + r], outline=(218, 202, 89), width=3)
    save_lowres(hospital, UI / "hospital_bg.png", 2)

    victory = Image.new("RGB", (640, 360), rgb(PALETTE["sky_top"]))
    d = ImageDraw.Draw(victory)
    d.polygon([(0, 230), (100, 170), (230, 225), (360, 150), (500, 225), (640, 170), (640, 360), (0, 360)], fill=rgb(PALETTE["sand"]))
    d.polygon([(220, 225), (420, 225), (640, 360), (0, 360)], fill=rgb(PALETTE["road"]))
    d.polygon([(316, 225), (324, 225), (340, 360), (300, 360)], fill=rgb(PALETTE["yellow"]))
    save_lowres(victory, UI / "results_bg.png", 2)


def make_portraits():
    for i, rider in enumerate(RIDERS):
        w, h = 160, 200
        img = Image.new("RGB", (w, h), (43, 52, 72))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 150, w, h], fill=(75, 72, 88))
        d.rectangle([10, 12, 150, 188], outline=(211, 181, 75), width=2)
        skin = rgb(rider["skin"])
        shirt = rgb(rider["shirt"])
        jacket = rgb(rider["jacket"])
        hair = rgb(rider["hair"])
        # Torso and jacket silhouette
        d.polygon([(52, 83), (108, 83), (124, 112), (116, 181), (44, 181), (36, 112)], fill=shirt)
        d.polygon([(36, 112), (52, 83), (57, 181), (44, 181)], fill=jacket)
        d.polygon([(108, 83), (124, 112), (116, 181), (103, 181)], fill=jacket)
        # Neck/head
        d.rectangle([70, 68, 90, 88], fill=skin)
        d.ellipse([60, 28, 100, 78], fill=skin)
        # Eyes and eyebrows
        d.rectangle([68, 50, 75, 53], fill=(38, 32, 34))
        d.rectangle([85, 50, 92, 53], fill=(38, 32, 34))
        d.line([(67, 46), (76, 45)], fill=(30, 25, 28), width=2)
        d.line([(84, 45), (93, 46)], fill=(30, 25, 28), width=2)
        d.line([(76, 66), (85, 66)], fill=(90, 48, 43), width=2)
        style = rider["hair_style"]
        if style == "spikes":
            for x, top in [(62, 16), (70, 8), (80, 5), (90, 9), (98, 17)]:
                d.polygon([(x - 5, 34), (x, top), (x + 5, 34)], fill=hair)
        elif style == "flattop":
            d.rectangle([58, 18, 102, 37], fill=hair)
            d.rectangle([62, 12, 98, 20], fill=hair)
        elif style == "mohawk":
            d.rectangle([75, 4, 85, 36], fill=hair)
            d.polygon([(70, 36), (75, 4), (85, 4), (90, 36)], fill=hair)
        elif style == "ponytail":
            d.ellipse([58, 18, 102, 48], fill=hair)
            d.polygon([(98, 34), (125, 48), (118, 66), (95, 46)], fill=hair)
        elif style == "undercut":
            d.rectangle([58, 22, 102, 40], fill=hair)
            d.rectangle([54, 18, 106, 25], fill=rgb(rider["accent"]))
        elif style == "curly":
            for x, y in [(62, 22), (76, 14), (90, 16), (100, 26), (58, 34), (74, 28), (88, 28)]:
                d.ellipse([x - 8, y - 8, x + 8, y + 8], fill=hair)
        elif style == "cap":
            d.polygon([(54, 30), (106, 30), (114, 40), (46, 40)], fill=(28, 31, 41))
            d.rectangle([58, 18, 100, 31], fill=(34, 38, 52))
        else:  # wild_spikes
            for x, top in [(60, 18), (69, 4), (79, 12), (89, 0), (99, 15), (105, 8)]:
                d.polygon([(x - 4, 36), (x, top), (x + 4, 36)], fill=hair)
        accessory = rider["accessory"]
        if accessory == "crossbody_bag":
            d.line([(50, 90), (110, 155)], fill=(45, 42, 48), width=5)
            d.rectangle([84, 137, 112, 162], fill=(55, 50, 56))
        elif accessory == "sunglasses":
            d.rectangle([64, 47, 77, 55], fill=(24, 25, 32))
            d.rectangle([83, 47, 96, 55], fill=(24, 25, 32))
            d.line([(77, 50), (83, 50)], fill=(24, 25, 32), width=2)
        elif accessory == "knee_pads":
            d.rectangle([52, 170, 70, 184], fill=rgb(rider["accent"]))
            d.rectangle([90, 170, 108, 184], fill=rgb(rider["accent"]))
        elif accessory == "helmet_half":
            d.pieslice([55, 14, 105, 64], start=180, end=360, fill=rgb(rider["accent"]))
            d.rectangle([55, 36, 105, 41], fill=(230, 226, 211))
        elif accessory == "bandana":
            d.rectangle([57, 23, 103, 34], fill=rgb(rider["accent"]))
            d.polygon([(100, 30), (118, 26), (105, 39)], fill=rgb(rider["accent"]))
        elif accessory == "chain":
            for x in range(68, 95, 7):
                d.ellipse([x, 84, x + 5, 89], outline=(223, 199, 84), width=1)
        elif accessory == "backpack":
            d.rectangle([36, 103, 52, 155], fill=(35, 36, 44))
        elif accessory == "scarf":
            d.polygon([(65, 78), (97, 78), (92, 96), (70, 96)], fill=rgb(rider["accent"]))
            d.polygon([(90, 88), (112, 105), (101, 112), (86, 98)], fill=rgb(rider["accent"]))
        # Name plate
        d.rectangle([12, 164, 148, 187], fill=(25, 25, 31))
        name_font = fit_font(d, rider["name"].split()[0].upper(), 130, 18, 10, FONT_MONO)
        text_center(d, (80, 176), rider["name"].split()[0].upper(), name_font, (231, 199, 66))
        save_lowres(img, PORTRAITS / f"rider_{i:02d}_{rider['id']}.png", 2)

    for i, bike in enumerate(BIKES):
        w, h = 240, 120
        img = Image.new("RGB", (w, h), (42, 48, 66))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 96, w, h], fill=(75, 72, 88))
        d.rectangle([6, 6, 233, 113], outline=(211, 181, 75), width=2)
        body = rgb(bike["body_color"])
        accent = rgb(bike["accent_color"])
        dark = rgb(bike["dark_color"])
        # Wheels
        for cx in [65, 178]:
            d.ellipse([cx - 25, 68, cx + 25, 118], fill=(23, 23, 27))
            d.ellipse([cx - 16, 77, cx + 16, 109], fill=(100, 99, 101))
            d.ellipse([cx - 8, 85, cx + 8, 101], fill=(58, 58, 62))
            for a in range(0, 360, 60):
                rad = math.radians(a)
                d.line([(cx, 93), (cx + 14 * math.cos(rad), 93 + 14 * math.sin(rad))], fill=(178, 175, 162), width=2)
        # Frame, engine, tank, seat
        d.polygon([(65, 82), (91, 62), (151, 62), (178, 82), (148, 90), (91, 90)], fill=dark)
        d.rectangle([100, 76, 141, 94], fill=(78, 78, 82))
        for x in range(104, 140, 8):
            d.line([(x, 78), (x, 91)], fill=(54, 54, 58), width=1)
        d.polygon([(92, 49), (146, 49), (159, 65), (84, 65)], fill=body)
        d.polygon([(96, 51), (141, 51), (148, 59), (91, 59)], fill=accent)
        d.polygon([(73, 46), (113, 44), (108, 54), (69, 56)], fill=(31, 30, 35))
        # Fork and bars
        d.line([(178, 82), (187, 48)], fill=(164, 163, 155), width=4)
        d.line([(176, 47), (199, 44)], fill=(45, 45, 49), width=4)
        if bike["high_bars"]:
            d.line([(178, 48), (184, 34), (196, 34)], fill=(45, 45, 49), width=3)
        # Exhausts
        for n in range(bike["exhausts"]):
            y = 91 + n * 5
            d.line([(107, y), (171, y + 3)], fill=(174, 169, 151), width=3)
        if bike["fairing"]:
            d.polygon([(178, 42), (213, 55), (211, 79), (182, 75)], fill=body)
            d.ellipse([201, 52, 215, 62], fill=(238, 224, 154))
        if bike["custom"]:
            d.line([(65, 82), (95, 96), (150, 96), (178, 82)], fill=accent, width=3)
        # Label
        d.rectangle([10, 12, 230, 35], fill=(25, 25, 31))
        label_font = fit_font(d, bike["name"].upper(), 210, 17, 10, FONT_MONO)
        text_center(d, (120, 24), bike["name"].upper(), label_font, (231, 199, 66))
        save_lowres(img, PORTRAITS / f"bike_{i:02d}_{bike['id']}.png", 2)


def write_wav(path: Path, samples: np.ndarray, rate: int = 22050):
    samples = np.clip(samples, -1.0, 1.0)
    pcm = (samples * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm.tobytes())


def make_audio():
    rate = 22050
    t = np.linspace(0, 2.0, int(rate * 2.0), endpoint=False)
    # Engine: layered saw-like harmonics with a small rpm wobble; loops cleanly.
    base = 55.0
    env = 0.72 + 0.18 * np.sin(2 * np.pi * 1.0 * t)
    engine = np.zeros_like(t)
    for k in range(1, 10):
        engine += np.sin(2 * np.pi * base * k * t + k * 0.4) / k
    engine *= env * 0.32
    # Fade first/last 10 ms to remove loop clicks.
    fade = min(220, len(engine) // 20)
    engine[:fade] *= np.linspace(0, 1, fade)
    engine[-fade:] *= np.linspace(1, 0, fade)
    write_wav(AUDIO / "engine_loop.wav", engine, rate)

    rng = np.random.default_rng(77)
    amb = rng.normal(0, 0.055, len(t))
    amb += 0.08 * np.sin(2 * np.pi * 42 * t)
    amb *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.5 * t)
    write_wav(AUDIO / "traffic_ambience.wav", amb, rate)

    siren = np.zeros_like(t)
    for i, sample in enumerate(t):
        f = 720.0 if math.floor(sample / 0.32) % 2 == 0 else 980.0
        siren[i] = 0.24 * math.sin(2 * np.pi * f * sample)
    write_wav(AUDIO / "siren_loop.wav", siren, rate)

    def tone(freq, duration, volume=0.3, kind="sine", end_freq=None):
        ts = np.linspace(0, duration, int(rate * duration), endpoint=False)
        f = np.full_like(ts, float(freq)) if end_freq is None else np.linspace(freq, end_freq, len(ts))
        phase = 2 * np.pi * np.cumsum(f) / rate
        if kind == "square":
            sig = np.sign(np.sin(phase))
        elif kind == "saw":
            sig = 2.0 * ((phase / (2 * np.pi)) % 1.0) - 1.0
        else:
            sig = np.sin(phase)
        sig *= volume * np.minimum(1.0, np.minimum(ts / 0.008, (duration - ts) / 0.025))
        return sig

    write_wav(AUDIO / "countdown_beep.wav", tone(660, 0.18, 0.32, "square"), rate)
    write_wav(AUDIO / "race_go.wav", tone(880, 0.42, 0.35, "saw", 1320), rate)
    write_wav(AUDIO / "menu_click.wav", tone(520, 0.07, 0.25, "square"), rate)
    write_wav(AUDIO / "police_alert.wav", np.concatenate([tone(740, 0.18, 0.3), tone(980, 0.18, 0.3)]), rate)
    write_wav(AUDIO / "boost.wav", tone(180, 0.34, 0.22, "saw", 760), rate)

    for name, duration, volume in [("collision_minor.wav", 0.22, 0.36), ("collision_major.wav", 0.62, 0.58)]:
        n = int(rate * duration)
        ts = np.linspace(0, duration, n, endpoint=False)
        noise = rng.normal(0, 1, n) * np.exp(-ts * (9 if duration < 0.3 else 4))
        thump = np.sin(2 * np.pi * (80 - 40 * ts) * ts) * np.exp(-ts * 12)
        write_wav(AUDIO / name, noise * volume * 0.55 + thump * volume * 0.45, rate)

    hospital = np.concatenate([
        tone(440, 0.16, 0.26, "square"), tone(370, 0.16, 0.26, "square"),
        tone(294, 0.20, 0.26, "square"), tone(220, 0.42, 0.30, "saw"),
    ])
    write_wav(AUDIO / "hospital_sting.wav", hospital, rate)

    victory = np.concatenate([
        tone(392, 0.18, 0.26, "square"), tone(494, 0.18, 0.26, "square"),
        tone(587, 0.18, 0.26, "square"), tone(784, 0.48, 0.32, "saw"),
    ])
    write_wav(AUDIO / "victory_sting.wav", victory, rate)


def make_data():
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "riders.json").write_text(json.dumps({
        "version": 1, "palette": PALETTE, "riders": RIDERS,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DATA / "bikes.json").write_text(json.dumps({
        "version": 1, "bikes": BIKES,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DATA / "traffic.json").write_text(json.dumps({
        "version": 1, "types": TRAFFIC_TYPES,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DATA / "settings_defaults.json").write_text(json.dumps(SETTINGS, indent=2) + "\n", encoding="utf-8")
    (ASSETS / "LICENSE-ASSETS.txt").write_text(
        "All generated textures, portraits, UI art, data and WAV audio in this project are original works "
        "created by tools/generate_assets.py for THE ASPHALT GROOMS. Arabic and Latin title/signage text is "
        "rasterized with DejaVu Sans (Bitstream Vera / DejaVu license); no third-party game assets, music, "
        "photographs, or commercial model libraries are included. Audio files are procedural placeholders. "
        "The three images in docs/reference are user-provided visual references and are not used as game textures.\n",
        encoding="utf-8",
    )


def make_manifest():
    files = []
    for path in sorted(ASSETS.rglob("*")):
        # Godot creates sibling .import metadata files after the first editor
        # run; those are engine state, not deterministic generator output.
        if path.is_file() and path.name != "ASSET_MANIFEST.json" and path.suffix != ".import":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            files.append({"path": str(path.relative_to(ROOT)).replace(os.sep, "/"),
                          "bytes": path.stat().st_size, "sha256": digest})
    manifest = {
        "generator": "tools/generate_assets.py",
        "version": 1,
        "file_count": len(files),
        "total_bytes": sum(f["bytes"] for f in files),
        "files": files,
    }
    (ASSETS / "ASSET_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    ensure_dirs()
    make_noise_textures()
    make_signs()
    make_title_and_backgrounds()
    make_portraits()
    make_audio()
    make_data()
    manifest = make_manifest()
    print(f"Generated {manifest['file_count']} asset files, {manifest['total_bytes'] / 1024 / 1024:.2f} MiB")
    print(f"Riders: {len(RIDERS)}, bikes: {len(BIKES)}, traffic types: {len(TRAFFIC_TYPES)}")


if __name__ == "__main__":
    main()
