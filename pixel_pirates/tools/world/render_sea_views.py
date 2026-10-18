"""Sea-view concept stills (Module E1). A Python MIRROR of game/ui/sea_painter.gd's layering and colour logic, driven by
the real ocean model at the slice checkpoints. It shows what the DATA says each place looks like (palette, light, fog, swell,
ice); it is NOT a capture of the Godot scene, which has never been run. Differences from the GDScript: PIL line widths and
alpha compositing, no wildlife, no animation, simplified clouds.
    python tools/world/render_sea_views.py [outdir]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "data_tools"))
import ocean as O  # noqa: E402
import voyage_clock as VC  # noqa: E402

W, H, HOR = 640, 360, 140
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "art_bible" / "sea_views_e1"
EXTRA = [{"name": "Kettle Seas, night (22:00)", "x_km": 7000, "y_km": 2650, "t_days": 3.9167, "heading_deg": 300},
         {"name": "Glass Sea, noon (becalmed)", "x_km": 4500, "y_km": 3000, "t_days": 2.5, "heading_deg": 90}]


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def lerp(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def lit(c, light, fl):
    k = min(max((light - fl) / max(1.0 - fl, 0.001), 0.0), 1.0)
    k = k ** 0.55
    return lerp((c[0] * 0.22, c[1] * 0.30, c[2] * 0.55), c, k)


def px(c, a=1.0):
    return (int(min(max(c[0], 0), 1) * 255), int(min(max(c[1], 0), 1) * 255), int(min(max(c[2], 0), 1) * 255), int(a * 255))


def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def sky_colors(look, light, fl, cloud, storm, fog):
    twilight = min(max(4 * light * (1 - light), 0), 1)
    blend = min(max((light - fl) / 0.35, 0), 1)
    top = lerp(look["sky_night"], lerp(look["sky_day"], look["sky_dusk"], twilight), blend)
    g = (lum(top),) * 3
    top = lerp(top, g, 0.5 * cloud)
    top = tuple(c * (1 - 0.45 * storm) for c in top)
    fogc = lit(look["fog_color"], light, fl)
    hor = lerp(top, fogc, 0.3 + 0.55 * fog)
    hor = tuple(c + (1 - c) * 0.12 * (1 - twilight) for c in hor)
    return top, hor


def hash01(i, j=0, k=0, seed=0):
    return O.hash01(i, j, k, seed)


def render(oc, sc, label):
    t = sc["t_days"]
    x, y = sc["x_km"], sc["y_km"]
    s = oc.sample(x, y, t)
    look = O.look_at(oc, x, y)
    hour = s["hour"]
    st = [oc.t[k] for k in ("time.dawn_start_hour", "time.morning_start_hour", "time.day_start_hour", "time.sunset_start_hour", "time.evening_start_hour", "time.night_start_hour")]
    dl = VC.daylight(hour, st, oc.t["light.night_floor"], oc.t["light.dawn_end_level"], oc.t["light.sunset_end_level"])
    fl = s["light_floor"]
    light = max(fl, dl * s["light_peak"])
    cloud, storm, fog, rain, herald, ice = s["cloud"], s["storm"], s["fog"], s["rain"], s["herald"], s["ice"]
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    top, hor = sky_colors(look, light, fl, cloud, storm, fog)
    for yy in range(HOR):
        d.line([(0, yy), (W, yy)], fill=px(lerp(top, hor, (yy / (HOR - 1)) ** 1.6)))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    if light < 0.35:
        a = (0.35 - light) / 0.35 * (1 - 0.9 * cloud)
        for i in range(70):
            ld.point((hash01(i, 1, 0, 77) * W, hash01(i, 2, 0, 77) * (HOR - 12)), fill=px((1, 1, .92), a * 0.8))
    veil = 1 - 0.85 * cloud - 0.4 * fog
    if veil > 0.05:
        if 5 < hour < 19:
            f = (hour - 5) / 14
            p = (60 + f * 520, HOR - math.sin(f * math.pi) * 118 + 4)
            col = lerp((1, .82, .55), (1, .97, .85), min(max(4 * f * (1 - f), 0), 1))
            for r, a in ((26, 0.10), (17, 0.18), (9, 1.0)):
                ld.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=px(col, a * veil))
        else:
            f2 = ((hour - 19) % 24) / 10
            if f2 < 1:
                p = (60 + f2 * 520, HOR - math.sin(f2 * math.pi) * 100 + 4)
                for r, a in ((14, 0.10), (7, 1.0)):
                    ld.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=px((.92, .94, 1), a * veil))
    cb = tuple(c * (1 - 0.5 * storm) for c in lit((.95, .95, .97), light, fl))
    for i in range(int(3 + cloud * 11)):
        cx = hash01(i, 5, 0, 78) * (W + 160) - 80
        cy = 18 + hash01(i, 6, 0, 78) * (HOR - 56)
        r = 12 + 16 * hash01(i, 7, 0, 78) * (0.5 + cloud)
        for k in range(4):
            ox, oy = (k - 1.5) * r * 0.9, -abs(k - 1.5) * r * 0.25
            rr = r * (1 - 0.15 * abs(k - 1.5))
            ld.ellipse([cx + ox - rr, cy + oy - rr, cx + ox + rr, cy + oy + rr], fill=px(cb, 0.30 + 0.5 * cloud))
    img = Image.alpha_composite(img, layer)
    d = ImageDraw.Draw(img)
    deep, shallow = lit(look["deep"], light, fl), lit(look["shallow"], light, fl)
    n = 22
    sh = (H - HOR) / n
    for i in range(n):
        f = i / (n - 1)
        col = lerp(hor, lerp(shallow, deep, min(1, f * 1.6)), min(max(f * 3, 0), 1))
        d.rectangle([0, HOR + i * sh, W, HOR + (i + 1) * sh + 1], fill=px(col))
    amp_max = min(max(s["wave_m"] * 3.0 * look["wave_scale"], 0.6), 20)
    foam = lit((.95, .98, 1), light, fl)
    crest = 0.97 - 0.12 * min(max((s["wind_kn"] - 10) / 25, 0), 1) - 0.08 * storm
    rows = 17
    for r in range(rows):
        f = r / (rows - 1)
        yb = HOR + 4 + (H - HOR - 4) * f ** 1.8
        amp = amp_max * (0.12 + 0.88 * f)
        wl = (14 + 150 * f) * (1 + 1.3 * herald)
        ph = float(r) * 1.7
        col = lerp(deep, shallow, 0.35 * (1 - f))
        col = tuple(min(1, c + (1 - c) * (0.10 + 0.06 * f)) for c in col)
        pts = []
        xx = -16.0
        while xx <= W + 16:
            s1 = math.sin(xx / wl * math.tau + ph)
            s2 = math.sin(xx / (wl * 0.43) * math.tau - ph * 1.3 + r)
            yy = yb + amp * (0.7 * s1 + 0.3 * s2)
            pts.append((xx, yy))
            if s1 * 0.7 + s2 * 0.3 > crest * 0.7 and s["wave_m"] > 1.2:
                d.line([(xx - 2 - 3 * f, yy), (xx + 2 + 3 * f, yy)], fill=px(foam), width=int(1 + f))
            xx += 16
        d.line(pts, fill=px(col), width=int(1 + f))
    if ice > 0.04:
        icol = lit((.88, .95, 1), light, fl)
        for i in range(int(ice * 46)):
            f = hash01(i, 1, 0, 91) ** 0.8
            yy = HOR + 6 + (H - HOR - 6) * f
            xx = hash01(i, 2, 0, 91) * (W + 120) - 60
            rw = (5 + 26 * hash01(i, 3, 0, 91)) * (0.25 + f)
            rh = rw * 0.28
            d.polygon([(xx - rw, yy), (xx - rw * .5, yy - rh), (xx + rw * .6, yy - rh * .8), (xx + rw, yy), (xx + rw * .4, yy + rh * .6), (xx - rw * .6, yy + rh * .5)], fill=px(icol))
        if ice > 0.85:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(lay).rectangle([0, HOR + 2, W, H], fill=px(icol, (ice - .85) / .15 * .8))
            img = Image.alpha_composite(img, lay)
            d = ImageDraw.Draw(img)
    # icebergs
    heading = sc["heading_deg"]
    for bx, by, size in oc.bergs_near(x, y, 14.0):
        rel = (math.degrees(math.atan2(bx - x, -(by - y))) - heading + 180) % 360 - 180
        dist = math.hypot(bx - x, by - y)
        if abs(rel) > 61 or dist > s["visibility_km"]:
            continue
        tt = min(max(1 - dist / 14, 0), 1)
        ox, oy = W / 2 + rel / 55 * W / 2, HOR + 3 + 50 * tt * tt
        hg = (6 + 11 * size) * (0.35 + 1.6 * tt * tt)
        wd = hg * 1.4
        d.polygon([(ox - wd * .5, oy), (ox - wd * .3, oy - hg * .6), (ox - wd * .05, oy - hg), (ox + wd * .25, oy - hg * .7), (ox + wd * .5, oy)], fill=px(lit((.86, .93, 1), light, fl)))
        d.polygon([(ox - wd * .05, oy - hg), (ox + wd * .25, oy - hg * .7), (ox + wd * .5, oy), (ox + wd * .1, oy)], fill=px(lit((.55, .7, .86), light, fl)))
    # ship (static pose)
    rel_w = (s["wind_from_deg"] - heading + 180) % 360 - 180
    wf = min(max(s["wind_kn"] / 30, 0), 1)
    heel = (1 if rel_w > 0 else -1) * wf * 0.16 * math.sin(math.radians(abs(rel_w)))
    cx, cy = 320, 268

    def tp(px_, py_):
        c, s_ = math.cos(heel), math.sin(heel)
        return (cx + px_ * c - py_ * s_, cy + px_ * s_ + py_ * c)
    hull, hd = lit((.35, .235, .157), light, fl), lit((.227, .157, .11), light, fl)
    deck, sail, sailsh = lit((.54, .415, .27), light, fl), lit((.91, .86, .75), light, fl), lit((.75, .68, .55), light, fl)
    d.polygon([tp(*p) for p in ((-34, -6), (34, -6), (26, 16), (-26, 16))], fill=px(hull))
    d.polygon([tp(*p) for p in ((-34, -6), (34, -6), (31, -2), (-31, -2))], fill=px(deck))
    d.polygon([tp(*p) for p in ((-26, 9), (26, 9), (26, 12), (-26, 12))], fill=px(hd))
    d.polygon([tp(*p) for p in ((-1.5, -64), (1.5, -64), (1.5, -6), (-1.5, -6))], fill=px(hd))
    billow = min(max(math.sin(math.radians(abs(rel_w))), 0), 1) * wf * 9 + 2
    skew = min(max(rel_w / 90, -1), 1) * 6
    bel = -34 - billow * 0.2
    d.polygon([tp(*p) for p in ((-22, -60), (22, -60), (26 + skew, bel), (-26 + skew, bel))], fill=px(sail))
    d.polygon([tp(*p) for p in ((-26 + skew, bel), (26 + skew, bel), (30 + skew, -8), (-30 + skew, -8))], fill=px(sailsh))
    d.polygon([tp(*p) for p in ((1, -64), (8 + 6 * wf, -61), (1, -58))], fill=px(lit((.66, .125, .125), light, fl)))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ldr = ImageDraw.Draw(lay)
    if light < 0.45:
        g = (0.45 - light) / 0.45
        ldr.ellipse([cx + 30 - 9, cy - 4 - 9, cx + 30 + 9, cy - 4 + 9], fill=px((1, .75, .3), 0.12 * g))
        ldr.ellipse([cx + 28, cy - 6, cx + 32, cy - 2], fill=px((1, .85, .45), g))
    if fog >= 0.04:
        fc = lit(look["fog_color"], light, fl)
        ldr.rectangle([0, 0, W, H], fill=px(fc, min(max(fog * 0.55, 0), 0.6)))
        for i in range(8):
            yy = HOR - 30 + i * 12
            ldr.rectangle([0, yy, W, yy + 13], fill=px(fc, min(max(fog * .4, 0), .45) * (1 - abs(i - 3.5) / 5)))
    img = Image.alpha_composite(img, lay)
    rl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rl)  # ImageDraw replaces pixels instead of blending, so rain gets its own layer above the fog
    if rain > 0.05:
        for i in range(int(rain * 150)):
            rx, ry = hash01(i, 1, 0, 61) * W, hash01(i, 2, 0, 61) * H
            sl = min(max(s["wind_kn"] / 40, 0), 1) * 10
            rd.line([(rx, ry), (rx - sl * .6, ry + 7)], fill=px((.75, .82, .9), 0.35 + 0.25 * rain))
    img = Image.alpha_composite(img, rl)
    d = ImageDraw.Draw(img)
    f12, f10 = font(11), font(10)
    info = f"{label} | {s['region'][4:].replace('_', ' ')} | day {int(t) + 1} {int(hour):02d}:{int((hour % 1) * 60):02d}"
    d.text((7, 7), info, font=f12, fill=(255, 235, 170, 255), stroke_width=1, stroke_fill=(0, 0, 0, 255))
    d.text((7, 22), f"wind {s['wind_kn']:.0f} kn | waves {s['wave_m']:.1f} m | vis {s['visibility_km']:.1f} km | {s['air_c']:.0f} C | light {light:.2f} | storm {storm:.2f} herald {herald:.2f}", font=f10,
           fill=(235, 240, 245, 255), stroke_width=1, stroke_fill=(0, 0, 0, 255))
    return img.convert("RGB"), s, light


def main() -> None:
    oc = O.load()
    route = json.loads((ROOT / "game" / "data" / "world" / "slice_route.json").read_text())["checkpoints"]
    OUT.mkdir(parents=True, exist_ok=True)
    scenes = [(f"{c['id']}. {c['name']}", c) for c in route] + [(e["name"], e) for e in EXTRA]
    shots = []
    for i, (name, sc) in enumerate(scenes):
        im, s, light = render(oc, sc, name)
        im.resize((1280, 720), Image.NEAREST).save(OUT / f"sea_view_{i + 1:02d}.png")
        shots.append(im)
        print(f"{name}: wind {s['wind_kn']:.0f} kn, waves {s['wave_m']:.1f} m, vis {s['visibility_km']:.1f} km, light {light:.2f}")
    cols = 3
    rows = (len(shots) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * W, rows * H), (10, 10, 12))
    for i, im in enumerate(shots):
        sheet.paste(im, ((i % cols) * W, (i // cols) * H))
    sheet.save(OUT / "sea_views_sheet.png")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
