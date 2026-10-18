"""World map render (Module E1): regions, climate belts, winds, currents, ice, scale. Concept view of the DATA, not game art.
    python tools/world/render_world_map.py [out.png]
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "data_tools"))
import ocean as O  # noqa: E402

CELL = 20.0
PX = 0.16   # px per km on the output (9000 km -> 1440 px)
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "art_bible" / "world_map_e1_v2.png"
ROUTE = ROOT / "game" / "data" / "world" / "slice_route.json"


def font(sz: int):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def main() -> None:
    oc = O.load()
    W, H = oc.W, oc.H
    nx, ny = int(W / CELL), int(H / CELL)
    img = Image.new("RGB", (nx, ny))
    px = img.load()
    acc = {r["id"]: [0.0, 0.0, 0] for r in oc.regions}
    for j in range(ny):
        for i in range(nx):
            x, y = (i + 0.5) * CELL, (j + 0.5) * CELL
            w = oc.region_weights(x, y)
            lk = [(wi, O.hex_rgb(r["water"]["deep"]), O.hex_rgb(r["water"]["shallow"])) for wi, r in zip(w, oc.regions)]
            k = max(range(len(w)), key=lambda q: w[q])
            a = acc[oc.regions[k]["id"]]
            a[0] += x
            a[1] += y
            a[2] += 1
            col = [sum(wi * (0.45 * d[k] + 0.55 * s[k]) for wi, d, s in lk) for k in range(3)]
            smp = oc.sample(x, y, 0.0)
            ice = smp["ice"]
            col = [c * (1 - 0.75 * ice) + 0.93 * 0.75 * ice for c in col]
            px[i, j] = tuple(int(255 * c) for c in col)
    big = img.resize((int(W * PX), int(H * PX)), Image.BICUBIC)
    d = ImageDraw.Draw(big)
    f, fs, fb = font(13), font(10), font(18)
    # climate belts
    for lat in (65, 55, 35, 20, 0, -20, -35, -55, -65):
        y = (oc.t["ocean.lat_extent_deg"] - lat) / (2 * oc.t["ocean.lat_extent_deg"]) * H * PX
        d.line([(0, y), (big.width, y)], fill=(255, 255, 255, 90) if lat else (255, 230, 150), width=1)
        d.text((4, y + 2), f"{lat:+d} deg", fill=(255, 255, 255), font=fs)
    # region borders (sampled boundaries) and labels
    for j in range(1, ny):
        for i in range(1, nx):
            if oc.region_index((i + 0.5) * CELL, (j + 0.5) * CELL) != oc.region_index((i - 0.5) * CELL, (j + 0.5) * CELL) or \
               oc.region_index((i + 0.5) * CELL, (j + 0.5) * CELL) != oc.region_index((i + 0.5) * CELL, (j - 0.5) * CELL):
                d.point((i * CELL * PX, j * CELL * PX), fill=(20, 20, 30))
    # wind arrows and currents
    for gy in range(300, int(H), 600):
        for gx in range(450, int(W), 900):
            smp = oc.sample(gx, gy, 10.5)
            ang = math.radians(smp["wind_from_deg"] + 180.0)
            L = max(6.0, smp["wind_kn"] * 1.1)
            x0, y0 = gx * PX, gy * PX
            x1, y1 = x0 + math.sin(ang) * L, y0 - math.cos(ang) * L
            d.line([(x0, y0), (x1, y1)], fill=(255, 255, 255), width=2)
            d.ellipse([x1 - 3, y1 - 3, x1 + 3, y1 + 3], fill=(255, 255, 255))
    # route
    if ROUTE.exists():
        import json
        rt = json.loads(ROUTE.read_text())
        pts = [(w["x_km"] * PX, w["y_km"] * PX) for w in rt["waypoints"]]
        d.line(pts, fill=(255, 90, 60), width=3)
        for k, (x, y) in enumerate(pts):
            d.ellipse([x - 6, y - 6, x + 6, y + 6], outline=(255, 90, 60), width=3, fill=(255, 255, 255))
            d.text((x + 10, y + 6), rt["waypoints"][k]["name"], fill=(255, 190, 160), font=fs)
    for r in oc.regions:
        a = acc[r["id"]]
        cx, cy = a[0] / a[2] * PX, a[1] / a[2] * PX
        label = r["name"].upper()
        tw = d.textlength(label, font=f)
        d.rectangle([cx - tw / 2 - 4, cy - 9, cx + tw / 2 + 4, cy + 22], fill=(10, 20, 35))
        d.text((cx - tw / 2, cy - 7), label, fill=(255, 245, 210), font=f)
        isl = r["islands"]
        d.text((cx - tw / 2, cy + 8), f"{isl['t1']}/{isl['t2']}/{isl['t3']} islands  {r['nav_rule']}", fill=(160, 210, 240), font=fs)
    # scale bar: 1000 km and the sailing time at 14.9 km/real minute
    sb = 1000 * PX
    d.rectangle([20, big.height - 54, 20 + sb, big.height - 48], fill=(255, 255, 255))
    d.text((20, big.height - 46), "1,000 km = 67 real minutes of sailing at the reference speed (14.9 km/min)", fill=(255, 255, 255), font=f)
    d.text((20, big.height - 28), f"world {int(W):,} x {int(H):,} km  |  white = sea ice (day 0)  |  arrows = prevailing wind at 10:30 day 0  |  provisional (E1)", fill=(220, 230, 240), font=fs)
    d.text((big.width - 520, 8), "CROWN OF THE SEAS  -  E1 WORLD (concept map)", fill=(255, 245, 210), font=fb)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    big.save(OUT)
    print("wrote", OUT, big.size)


if __name__ == "__main__":
    main()
