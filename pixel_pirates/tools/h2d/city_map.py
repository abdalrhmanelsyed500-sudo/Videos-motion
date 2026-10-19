"""CP-1 revision: the parchment maps shown by the M overlay: a city map (2.5 px/m), an island map and a sea chart (0.25 px/m).
Everything is drawn from the baked ground (classes, heights) and the plan, so the map can never disagree with the world."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import cay_terrain as CT
import city_layout as CY

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
PIRATA = Path(__file__).resolve().parents[2] / "game/ui/fonts/pirata_one_regular.ttf"
PARCH = (226, 208, 160)
INK = (62, 40, 20)
SEA = (140, 178, 178)
SEA_D = (112, 154, 160)

CITY_VIEW = dict(id="city", title="Anvil Harbor", file="map_city.png", bounds=[-212.0, -282.0, 212.0, 42.0], ppm=2.5, zoom=0.9)
ISLAND_VIEW = dict(id="island", title="Anvil Cay", file="map_island.png", bounds=[-1300.0, -3500.0, 1500.0, 140.0], ppm=0.25, zoom=1.0)
SEA_VIEW = dict(id="sea", title="Fishing waters", file="map_sea.png", bounds=[-900.0, -420.0, 800.0, 1950.0], ppm=0.2, zoom=1.0)

CLS_COL = {1: (232, 218, 172), 2: (206, 200, 140), 3: (190, 196, 130), 4: (150, 172, 110), 5: (186, 174, 150), 6: (150, 138, 118), 7: (214, 190, 140),
           8: (240, 230, 206), 9: (196, 168, 120), 10: (176, 190, 130), 11: (196, 198, 140), 12: (236, 224, 196), 13: (214, 170, 120),
           14: (210, 196, 170), 15: (120, 110, 100)}


def font(sz, bold=True, pirata=False):
    if pirata:
        return ImageFont.truetype(str(PIRATA), sz)
    return ImageFont.truetype(str(FONT_DIR / ("DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf")), sz)


def crop_world(arr, bounds, ppm):
    x0, z0, x1, z1 = bounds
    W, H = int((x1 - x0) * ppm), int((z1 - z0) * ppm)
    xs = x0 + (np.arange(W) + 0.5) / ppm
    zs = z0 + (np.arange(H) + 0.5) / ppm
    ix = np.clip(((xs - CT.X0) / CT.CELL).astype(int), 0, CT.N - 1)
    iz = np.clip(((zs - CT.Z0) / CT.CELL).astype(int), 0, CT.N - 1)
    inside_x = (xs >= CT.X0) & (xs < CT.X0 + CT.N * CT.CELL)
    inside_z = (zs >= CT.Z0) & (zs < CT.Z0 + CT.N * CT.CELL)
    out = arr[np.ix_(iz, ix)]
    return out, inside_z[:, None] & inside_x[None, :]


def land_colors(cls, h, land):
    rgb = np.zeros(cls.shape + (3,), np.float32)
    rgb[:] = SEA
    for k, c in CLS_COL.items():
        rgb[(cls == k) & land] = c
    rgb[land & (cls == 0)] = CLS_COL[9]
    gz, gx = np.gradient(h, 1.0)
    shade = np.clip(1.0 + (gx * -0.9 + gz * -0.9) * 1.2, 0.8, 1.15)
    rgb = np.where(land[..., None], rgb * shade[..., None], rgb)
    return rgb


def parchment_noise(size, seed=3):
    rs = np.random.RandomState(seed)
    n = rs.rand(size[1] // 8 + 2, size[0] // 8 + 2).astype(np.float32)
    n = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((size[0], size[1]), Image.BICUBIC), np.float32) / 255.0
    return n


def frame(im, margin=10, title=None, sub=None):
    d = ImageDraw.Draw(im)
    w, h = im.size
    d.rectangle((2, 2, w - 3, h - 3), outline=INK, width=3)
    d.rectangle((9, 9, w - 10, h - 10), outline=INK, width=1)
    return im


def compass(d, cx, cy, r=34):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=INK, width=2)
    for a in range(8):
        ang = a * math.pi / 4
        L = r if a % 2 == 0 else r * 0.62
        d.line((cx, cy, cx + L * math.sin(ang), cy - L * math.cos(ang)), fill=INK, width=2 if a % 2 == 0 else 1)
    d.polygon([(cx, cy - r - 12), (cx - 6, cy - r + 4), (cx + 6, cy - r + 4)], fill=(150, 40, 30), outline=INK)
    d.text((cx - 5, cy - r - 30), "N", fill=INK, font=font(18))


def text_halo(d, xy, text, f, fill=INK, halo=(240, 228, 190), anchor="mm"):
    x, y = xy
    for ox in (-2, -1, 0, 1, 2):
        for oy in (-2, -1, 0, 1, 2):
            if ox or oy:
                d.text((x + ox, y + oy), text, font=f, fill=halo, anchor=anchor)
    d.text(xy, text, font=f, fill=fill, anchor=anchor)


def city_map(w, city, out: Path):
    v = CITY_VIEW
    ppm = v["ppm"]
    b = v["bounds"]
    cls, ok = crop_world(w["cls"], b, ppm)
    h, _ = crop_world(w["h"], b, ppm)
    land = ok & (h > 0.15)
    rgb = land_colors(cls, h, land)
    # sea hatching
    H, W = cls.shape
    yy, xx = np.mgrid[0:H, 0:W]
    sea = ~land
    hatch = ((xx + yy * 2) % 9 == 0) & sea
    rgb[hatch] = SEA_D
    nz = parchment_noise((W, H))
    rgb = np.clip(rgb * (0.94 + 0.12 * nz[..., None]), 0, 255)
    im = Image.fromarray(rgb.astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")

    def P(x, z):
        return ((x - b[0]) * ppm, (z - b[1]) * ppm)
    # coast line: dark edge
    edge = land & ~np.pad(land, 1, constant_values=True)[:-2, 1:-1] | land & ~np.pad(land, 1, constant_values=True)[2:, 1:-1] | \
        land & ~np.pad(land, 1, constant_values=True)[1:-1, :-2] | land & ~np.pad(land, 1, constant_values=True)[1:-1, 2:]
    arr = np.array(im)
    arr[edge] = (84, 60, 36)
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im, "RGBA")
    # terrace walls as dark bars
    for zw in CY.WALLS_Z:
        x0, y0 = P(CY.BOX["x0"], zw - 1.0)
        x1, y1 = P(CY.BOX["x1"], zw + 0.2)
        d.rectangle((x0, y0, x1, y1), fill=(96, 84, 76, 255))
    # buildings
    kinds = {"wall": (86, 80, 76), "grand": (170, 150, 120), "tavern": (190, 100, 60), "warehouse": (150, 120, 90), "mansion": (200, 170, 150),
             "shop": (206, 130, 80), "house": (190, 120, 90), "cottage": (170, 130, 90), "fisher": (150, 120, 90), "tall": (180, 110, 80)}
    for p in city.placed:
        x0, y0 = P(p.x - p.w / 2, p.z - p.d)
        x1, y1 = P(p.x + p.w / 2, p.z)
        n = p.name
        col = kinds["wall"] if n.startswith("wall") else (kinds["grand"] if p.atlas == "grand" else
              next((c for k, c in kinds.items() if k in n), (190, 120, 90)))
        d.rectangle((x0, y0, x1, y1), fill=col + (255,), outline=(70, 44, 26, 255))
        if p.atlas == "grand" and not n.startswith("fort"):
            d.line((x0, y0 + 1, x1, y0 + 1), fill=(240, 226, 190, 255), width=1)
    for t, x, z, s, r in city.trees:
        cx, cy = P(x, z)
        d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(92, 134, 84, 255), outline=(52, 84, 48, 255))
    for atlas, name, x, z, w2, d2, solid in city.props:
        if name == "fountain":
            cx, cy = P(x, z)
            d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=(140, 190, 200, 255), outline=INK)
        elif name == "anvil_monument":
            cx, cy = P(x, z)
            d.rectangle((cx - 4, cy - 4, cx + 4, cy + 4), fill=(80, 84, 96, 255), outline=INK)
    # canal and wharf from the port data
    from_port = w.get("port_map")
    if from_port:
        for r in from_port.get("wharf", []):
            x0, y0 = P(r[0], r[1]); x1, y1 = P(r[2], r[3])
            d.rectangle((x0, y0, x1, y1), fill=(170, 130, 86, 255), outline=(84, 56, 30, 255))
        for r in from_port.get("bridges", []):
            x0, y0 = P(r[0], r[1]); x1, y1 = P(r[2], r[3])
            d.rectangle((x0, y0, x1, y1), fill=(190, 150, 100, 255), outline=(84, 56, 30, 255))
    pier = (14.5, 2.0, 17.5, 36.0)
    x0, y0 = P(pier[0], pier[1]); x1, y1 = P(pier[2], pier[3])
    d.rectangle((x0, y0, x1, y1), fill=(170, 130, 86, 255), outline=(84, 56, 30, 255))
    x0, y0 = P(11.0, 32.0); x1, y1 = P(17.5, 36.0)
    d.rectangle((x0, y0, x1, y1), fill=(170, 130, 86, 255), outline=(84, 56, 30, 255))
    # labels: districts (blackletter), streets (small caps look)
    big = font(30, pirata=True)
    mid = font(14)
    small = font(11, bold=False)
    for name, x, z in (("Governor's Hill", 16.0, -250.0), ("Terrace Walk", -100.0, -160.0), ("Hill Road", 100.0, -113.0), ("Merchants' Row", -100.0, -86.0),
                       ("Chandlers' Street", 100.0, -44.0), ("Quay Street", 150.0, 0.0)):
        pass
    for name, x, z, f in (("Governor's Hill", 16.0, -252.0, big), ("The Mansions", -105.0, -182.0, big), ("Anchor Avenue", 16.0, -120.0, mid), ("Market Quarter", 105.0, -60.0, big),
                          ("Netmakers' Quarter", -160.0, -75.0, big), ("Fish Row", -88.0, -37.0, big), ("The Quay", 82.0, -14.0, big),
                          ("Lower Town", -100.0, -62.0, mid), ("Eastside", 160.0, -70.0, big), ("Hill Road Terrace", 100.0, -137.0, mid)):
        text_halo(d, P(x, z), name, f)
    for name, zc, xs in (("QUAY STREET", 0.0, (-160.0, 120.0)), ("CHANDLERS' STREET", -44.0, (-160.0, 150.0)), ("MERCHANTS' ROW", -86.0, (-160.0, 150.0)),
                         ("HILL ROAD", -113.0, (-160.0, 150.0)), ("TERRACE WALK", -158.0, (-160.0, 150.0))):
        for x in xs:
            text_halo(d, P(x, zc), name, small, halo=(222, 204, 170))
    # gates, compass, title
    for name, gx in CY.GATES:
        cx, cy = P(gx, CY.BOX["z0"] + 1.5)
        text_halo(d, (cx, cy - 18), name.upper(), small)
    compass(d, 60, im.size[1] - 70, 34)
    text_halo(d, (im.size[0] // 2, 26), "ANVIL HARBOR", font(34, pirata=True))
    im = frame(im)
    im.save(out / v["file"], optimize=True)
    return im


def island_map(w, out: Path):
    v = ISLAND_VIEW
    ppm = v["ppm"]
    b = v["bounds"]
    cls, ok = crop_world(w["cls"], b, ppm)
    h, _ = crop_world(w["h"], b, ppm)
    land = ok & (h > 0.15)
    rgb = land_colors(cls, h, land)
    H, W = cls.shape
    yy, xx = np.mgrid[0:H, 0:W]
    rgb[((xx + yy * 2) % 7 == 0) & ~land] = SEA_D
    nz = parchment_noise((W, H), 5)
    rgb = np.clip(rgb * (0.94 + 0.12 * nz[..., None]), 0, 255)
    im = Image.fromarray(rgb.astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")

    def P(x, z):
        return ((x - b[0]) * ppm, (z - b[1]) * ppm)
    arr = np.array(im)
    pad = np.pad(land, 1, constant_values=True)
    edge = land & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    arr[edge] = (84, 60, 36)
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im, "RGBA")
    x0, y0 = P(CY.BOX["x0"], CY.BOX["z0"]); x1, y1 = P(CY.BOX["x1"], 20.0)
    d.rectangle((x0, y0, x1, y1), outline=(140, 40, 30, 255), width=2)
    text_halo(d, P(0.0, -150.0), "ANVIL HARBOR", font(26, pirata=True))
    for name, x, z in (("Mount Anvil", -330.0, -3000.0), ("Lookout Hill", 150.0, -575.0), ("Beacon Hill", -420.0, -1500.0), ("Horn Ridge", 1100.0, -3100.0)):
        cx, cy = P(x, z)
        d.polygon([(cx, cy - 8), (cx - 7, cy + 5), (cx + 7, cy + 5)], fill=(120, 100, 84, 255), outline=INK)
        text_halo(d, (cx, cy + 16), name, font(12))
    compass(d, 70, im.size[1] - 80, 34)
    text_halo(d, (im.size[0] // 2, 30), "ANVIL CAY", font(34, pirata=True))
    im = frame(im)
    im.save(out / v["file"], optimize=True)


def sea_map(w, out: Path):
    v = SEA_VIEW
    ppm = v["ppm"]
    b = v["bounds"]
    W, H = int((b[2] - b[0]) * ppm), int((b[3] - b[1]) * ppm)
    yy, xx = np.mgrid[0:H, 0:W]
    rgb = np.zeros((H, W, 3), np.float32)
    rgb[:] = SEA
    rgb[((xx * 2 + yy) % 11 == 0)] = SEA_D
    cls, ok = crop_world(w["cls"], b, ppm)
    h, _ = crop_world(w["h"], b, ppm)
    land = ok & (h > 0.15)
    cl = land_colors(cls, h, land)
    rgb = np.where(land[..., None], cl, rgb)
    nz = parchment_noise((W, H), 9)
    rgb = np.clip(rgb * (0.94 + 0.12 * nz[..., None]), 0, 255)
    im = Image.fromarray(rgb.astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")

    def P(x, z):
        return ((x - b[0]) * ppm, (z - b[1]) * ppm)
    # a dotted route home
    pts = [P(16, 40), P(16, 120), P(-100, 260), P(-300, 500)]
    # compass and title
    compass(d, W - 70, H - 80, 34)
    text_halo(d, (W // 2, 30), "FISHING WATERS", font(32, pirata=True))
    text_halo(d, P(16, 24), "Anvil Harbor", font(13))
    im = frame(im)
    im.save(out / v["file"], optimize=True)
