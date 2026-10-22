# VP-1A.4: the AUTHORED pixel-art atlas of the ship INTERIOR (game/art/vp1/interior_px.png).
# Second 1024 px sheet in the same 4x4-of-256 style as ship_px.png (tools/vp1/make_px_atlas.py): material ids 16..31 in
# ship_mesh.gd sample this sheet (shader uniform pxatlas2). Everything below decks is drawn: worn foot-traffic floors,
# inner hull planking with drawn frames and through-bolts, deck-head planks, cabin panelling with moulded raised panels,
# a woven rug, the chart on the desk with coastline and rhumb lines, hammock canvas, wool blankets, book spines,
# provisions (biscuit, salt fish, cheese), glass bottles, polished brass, tarred posts, rack boards with iron uprights,
# a coiled rope mat and ballast stones. Same techniques: periodic noise, quantised ramps, Bayer dither, wrapped seams.
# Run:  python tools/vp1/make_px_atlas2.py
import numpy as np

SIZE = 1024
TILE = 256


def pnoise(n, cells, seed):
    r = np.random.default_rng(seed)
    g = r.random((cells, cells))
    x = np.linspace(0, cells, n, endpoint=False)
    ix = x.astype(int)
    fx = x - ix
    fx = fx * fx * (3 - 2 * fx)
    i0 = ix % cells
    i1 = (ix + 1) % cells
    t = g[np.ix_(i0, i0)] * (1 - fx)[:, None] * (1 - fx)[None, :]
    t += g[np.ix_(i1, i0)] * fx[:, None] * (1 - fx)[None, :]
    t += g[np.ix_(i0, i1)] * (1 - fx)[:, None] * fx[None, :]
    t += g[np.ix_(i1, i1)] * fx[:, None] * fx[None, :]
    return t


def fbm(n, cells, seed, octaves=3):
    s = np.zeros((n, n))
    a = 0.5
    c = cells
    for k in range(octaves):
        s += a * pnoise(n, c, seed + k * 91)
        a *= 0.5
        c *= 2
    return s / (1.0 - a)


def bayer(n):
    m = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], float) / 16.0
    return np.tile(m, (n // 4, n // 4))


def ramp_map(v, ramp):
    v = np.clip(v, 0.0, 0.9999)
    idx = (v * len(ramp)).astype(int)
    out = np.zeros(v.shape + (3,))
    for k, c in enumerate(ramp):
        out[idx == k] = c
    return out


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255.0


def coat(out, mask, col, coef):
    out[mask] = (col[None, None, :] * coef[:, :, None])[mask]
    return out


def grit(out, seed, lo=0.90, hi=0.08, up=1.10, dn=0.88):
    r = np.random.default_rng(seed)
    h = r.random(out.shape[:2])
    out[h > lo] = np.clip(out[h > lo] * up, 0, 1)
    out[h < hi] = out[h < hi] * dn
    return out


def ifloor():
    n = TILE
    pw = 12
    x = np.arange(n)
    px = x // pw
    ph = np.random.default_rng(211).random(pw * 8)
    base = 0.34 + 0.26 * ph[px % (pw * 8)]
    grain = 0.6 * fbm(n, 8, 212, 3) + 0.4 * pnoise(n, 64, 213)
    v = base + 0.18 * (grain - 0.5)
    ramp = [hexc(c) for c in ("33230f", "402c14", "4d3619", "5a401e", "674a24", "74542a", "815e30")]
    out = ramp_map(v, ramp)
    xs = x % pw
    out[(xs == 0) | (xs == 1)] = out[(xs == 0) | (xs == 1)] * 0.26
    out[xs == 2] = out[xs == 2] * 1.28
    y = np.arange(n)
    off = (ph[px % (pw * 8)] * 89).astype(int)
    jy = (y[:, None] + off[None, :]) % 88
    out[((jy == 0) | (jy == 1)) & (xs[None, :] > 1)] *= 0.3
    out[(jy == 2) & (xs[None, :] > 1)] *= 1.2
    # foot traffic: a worn pale path down the middle, dithered edges
    wear = np.exp(-((x[None, :] - n * 0.5) ** 2) / (2 * (n * 0.16) ** 2)) * (0.7 + 0.3 * fbm(n, 6, 216, 2))
    bd = bayer(n)
    m = (wear > 0.55) & (bd < (wear - 0.55) * 2.0)
    out[m] = out[m] * 0.7 + hexc("b8a888") * 0.3
    # replaced pale plank and a dark spill
    out[:, (px == 5)] = out[:, (px == 5)] * 1.35
    spill = (fbm(n, 4, 218, 2) > 0.72) & (bd < 0.6)
    out[spill] = out[spill] * 0.55
    for k in range(0, n, pw):
        for yy in (20, 140):
            out[yy, (k + 4) % n] = hexc("140d05")
            out[yy, (k + 5) % n] = hexc("140d05")
            out[(yy - 1) % n, (k + 4) % n] = hexc("d8c090")
    return np.ascontiguousarray(out.transpose(1, 0, 2))


def ihull():
    n = TILE
    sh = 10
    y = np.arange(n)
    sid = y // sh
    ph = np.random.default_rng(221).random(n)
    base = 0.32 + 0.22 * ph[sid]
    grain = 0.6 * fbm(n, 6, 222, 3) + 0.4 * pnoise(n, 48, 223)
    v = base + 0.16 * (grain - 0.5)
    ramp = [hexc(c) for c in ("2a1a0d", "34210f", "3e2812", "482f16", "52361a", "5c3d1e")]
    out = ramp_map(v, ramp)
    ys = y % sh
    out[(ys == 0) | (ys == 1)] = out[(ys == 0) | (ys == 1)] * 0.28
    out[ys == 2] = out[ys == 2] * 1.26
    # drawn frames (futtocks): a dark vertical band every 24 px with lit edges and two through-bolts
    x = np.arange(n)
    fx = x % 24
    frame = (fx == 0) | (fx == 1) | (fx == 2) | (fx == 3)
    out[frame] = out[frame] * 0.42
    out[fx == 4] = out[fx == 4] * 1.35
    out[fx == 23] = out[fx == 23] * 0.6
    bd = bayer(n)
    grain2 = fbm(n, 10, 226, 2)
    out[frame & (grain2 > 0.5) & (bd > 0.5)] *= 1.25
    for cx in range(2, n, 24):
        for cy in range(15, n, 40):
            out[cy, cx + 1] = hexc("0e0a06")
            out[cy, cx + 2] = hexc("7a6a50")
    # bilge stain at the bottom of the tile wrap
    stain = (y[None, :] > 232) & (bd > 0.4)
    out[stain] = out[stain] * 0.6
    return out


def ceilp():
    n = TILE
    pw = 14
    x = np.arange(n)
    px = x // pw
    ph = np.random.default_rng(231).random(n)
    base = 0.42 + 0.2 * ph[px]
    grain = fbm(n, 8, 232, 3)
    v = base + 0.14 * (grain - 0.5)
    ramp = [hexc(c) for c in ("3c2a14", "48331a", "543c20", "604526", "6c4e2c", "785732")]
    out = ramp_map(v, ramp)
    xs = x % pw
    out[(xs == 0) | (xs == 1)] = out[(xs == 0) | (xs == 1)] * 0.3
    out[xs == 2] = out[xs == 2] * 1.22
    y = np.arange(n)
    # nail rows along each caulking line and soot near the lantern spots
    for k in range(0, n, pw):
        for yy in range(8, n, 32):
            out[yy, k + 1] = hexc("120c06")
    soot = (fbm(n, 5, 235, 2) > 0.74) & (bayer(n) < 0.6)
    out[soot] = out[soot] * 0.55
    return np.ascontiguousarray(out.transpose(1, 0, 2))


def cwall():
    n = TILE
    v = 0.5 + 0.14 * (fbm(n, 6, 241, 3) - 0.5)
    ramp = [hexc(c) for c in ("4a2f16", "57381b", "644120", "714a25", "7e532a", "8b5c2f")]
    out = ramp_map(v, ramp)
    x = np.arange(n)
    y = np.arange(n)
    # raised panels: 128 px grid, moulding = lit top/left, dark bottom/right, field slightly darker with vertical grain
    pu = x[None, :] % 128
    pv = y[:, None] % 128
    band = 10
    inb = (pu > band) & (pu < 128 - band) & (pv > band) & (pv < 128 - band)
    field = (pu > band + 8) & (pu < 128 - band - 8) & (pv > band + 8) & (pv < 128 - band - 8)
    out[inb & ~field] = out[inb & ~field] * 0.78
    out[(pu == band) | (pv == band)] = out[(pu == band) | (pv == band)] * 1.4
    out[(pu == 127) | (pv == 127)] = out[(pu == 127) | (pv == 127)] * 0.5
    vg = 0.92 + 0.10 * (0.5 + 0.5 * np.sin(x[None, :] * 0.9))
    out = out * np.where(field[:, :, None], vg[:, :, None], 1.0)
    grain = fbm(n, 24, 244, 2)
    out[field & (grain > 0.62)] *= 1.12
    out[field & (grain < 0.34)] *= 0.86
    # a brass screw in each panel corner
    for cx in (24, 104, 152, 232):
        for cy in (24, 104, 152, 232):
            out[cy, cx] = hexc("c8a040")
            out[cy, cx + 1] = hexc("705018")
    return out


def rug():
    n = TILE
    y = np.arange(n)
    band_id = (y // 16) % 4
    cols = [hexc("5a1c18"), hexc("2a2440"), hexc("7a4a20"), hexc("3a3048")]
    out = np.zeros((n, n, 3))
    for k in range(4):
        out[band_id == k] = cols[k]
    x = np.arange(n)
    weave = ((x[None, :] // 2) % 2) == ((y[:, None] // 2) % 2)
    out[weave] = out[weave] * 0.84
    # diamond motifs down the centre
    d = (np.abs((x[None, :] - 128) % 64 - 32) + np.abs((y[:, None] - 64) % 128 - 64))
    mot = (np.abs(d - 20) < 3)
    out[mot] = hexc("c8a860")
    mot2 = (np.abs(d - 12) < 2)
    out[mot2] = hexc("8a2018")
    # fringe at both wrap ends and worn pale patches
    out[y < 6] = out[y < 6] * 0.6 + hexc("b8a878") * 0.4
    out[y > 249] = out[y > 249] * 0.6 + hexc("b8a878") * 0.4
    bd = bayer(n)
    wear = (fbm(n, 5, 254, 2) > 0.68) & (bd < 0.5)
    out[wear] = out[wear] * 0.75 + hexc("a89878") * 0.25
    return out


def chart():
    n = TILE
    v = 0.78 + 0.08 * (fbm(n, 6, 261, 2) - 0.5)
    ramp = [hexc(c) for c in ("b09868", "bc a474".replace(" ", ""), "c8b080", "d4bc8c", "e0c898", "ecd4a4")]
    out = ramp_map(v, ramp)
    x = np.arange(n)
    y = np.arange(n)
    # a coastline: land mass in the corner with a shaded shoal ring
    land = ((x[None, :] - 40) ** 2 / 90.0 ** 2 + (y[:, None] - 210) ** 2 / 70.0 ** 2) < 1.0 + 0.25 * (fbm(n, 8, 263, 2) - 0.5)
    out[land] = hexc("a89058")
    ring = ((x[None, :] - 40) ** 2 / 100.0 ** 2 + (y[:, None] - 210) ** 2 / 80.0 ** 2) < 1.0
    out[ring & ~land & (bayer(n) > 0.5)] = hexc("98b0a0")
    out[ring & ~land & (bayer(n) <= 0.5)] = out[ring & ~land & (bayer(n) <= 0.5)] * 0.9
    # rhumb lines from a compass rose
    cx, cy = 180, 70
    ang = np.arctan2(y[:, None] - cy, x[None, :] - cx)
    rh = (np.abs(np.sin(ang * 4.0)) < 0.012)
    out[rh] = hexc("705838")
    for k in range(8):
        a = k * np.pi / 4.0
        for r in range(6, 26):
            xx = int(cx + np.cos(a) * r) % n
            yy = int(cy + np.sin(a) * r) % n
            out[yy, xx] = hexc("8a2018") if k % 2 == 0 else hexc("403020")
    out[cy, cx] = hexc("403020")
    # script dashes and a coffee stain
    for yy in range(120, 240, 14):
        xx = 120
        while xx < 240:
            ln = int(4 + 6 * abs(np.sin(xx * 0.7 + yy)))
            out[yy, xx:xx + ln] = hexc("48382a")
            xx += ln + 4
    st = ((x[None, :] - 90) ** 2 + (y[:, None] - 60) ** 2)
    out[(st < 26 ** 2) & (st > 22 ** 2)] = out[(st < 26 ** 2) & (st > 22 ** 2)] * 0.82 + hexc("7a5830") * 0.18
    return out


def ham():
    n = TILE
    v = 0.66 + 0.08 * (fbm(n, 8, 271, 2) - 0.5)
    ramp = [hexc(c) for c in ("9c9278", "aca288", "bcb298", "ccc2a8", "dcd2b8", "e8e0c8")]
    out = ramp_map(v, ramp)
    x = np.arange(n)
    y = np.arange(n)
    weave = ((x[None, :] // 2) % 2) == ((y[:, None] // 2) % 2)
    out[weave] = out[weave] * 0.88
    # stitched seams and gathered end stripes
    out[(y % 64) < 2] = out[(y % 64) < 2] * 0.7
    out[(y % 64 == 3) & (x % 4 < 2)] = hexc("6a6250")
    out[x < 10] = out[x < 10] * 0.8
    out[x > 245] = out[x > 245] * 0.8
    for xx in range(0, 10, 3):
        out[:, xx] = out[:, xx] * 0.75
        out[:, 255 - xx] = out[:, 255 - xx] * 0.75
    # a sewn patch
    out[100:130, 150:190] = out[100:130, 150:190] * 0.85 + hexc("b0a888") * 0.15
    out[100, 150:190] = hexc("6a6250")
    out[129, 150:190] = hexc("6a6250")
    out[100:130, 150] = hexc("6a6250")
    out[100:130, 189] = hexc("6a6250")
    return out


def blank():
    n = TILE
    y = np.arange(n)
    sid = (y // 24) % 3
    cols = [hexc("6a2018"), hexc("585048"), hexc("7a5a28")]
    out = np.zeros((n, n, 3))
    for k in range(3):
        out[sid == k] = cols[k]
    x = np.arange(n)
    weave = ((x[None, :] // 2) % 2) == ((y[:, None] // 2) % 2)
    out[weave] = out[weave] * 0.86
    out[(y % 24) < 2] = out[(y % 24) < 2] * 0.6
    bd = bayer(n)
    fuzz = (fbm(n, 12, 284, 2) > 0.7) & (bd > 0.6)
    out[fuzz] = out[fuzz] * 1.2
    return out


def books():
    n = TILE
    out = np.zeros((n, n, 3))
    r = np.random.default_rng(291)
    cols = ["6a1c14", "1e3040", "4a3a14", "24402a", "50284a", "704018"]
    x = 0
    while x < n:
        w = int(r.integers(10, 20))
        h0 = int(r.integers(0, 24))
        c = hexc(cols[int(r.integers(0, 6))])
        out[h0:, x:x + w - 2] = c * (0.85 + 0.3 * r.random())
        out[h0:h0 + 2, x:x + w - 2] = c * 1.5
        out[h0:, x + w - 2:x + w] = c * 0.4
        gy = h0 + int(r.integers(8, 20))
        out[gy:gy + 2, x:x + w - 2] = hexc("c8a040")
        gy2 = gy + int(r.integers(14, 30))
        if gy2 < n - 4:
            out[gy2:gy2 + 2, x:x + w - 2] = hexc("c8a040")
        for yy in range(h0 + 30, n - 10, 6):
            out[yy, x + 2:x + w - 4] = c * 0.7
        x += w
    return out


def food():
    n = TILE
    out = np.zeros((n, n, 3)) + hexc("8a6a38")
    x = np.arange(n)
    y = np.arange(n)
    bd = bayer(n)
    # biscuit heap top-left: pale rounds with docker holes
    for cy in range(20, 110, 34):
        for cx in range(20, 120, 36):
            d = (x[None, :] - cx) ** 2 + (y[:, None] - cy) ** 2
            m = d < 14 ** 2
            coat(out, m, hexc("c8a868"), 0.9 + 0.2 * (bd > 0.5))
            e = (d < 15 ** 2) & (d >= 13 ** 2)
            out[e] = hexc("8a6a30")
            for k in range(4):
                out[cy - 4 + k * 3, cx - 4 + (k % 2) * 6] = hexc("7a5828")
    # salt fish rows right: silver bodies, dark backs, tails
    for cy in range(30, 240, 46):
        for cx in range(150, 250, 52):
            body = (np.abs(y[:, None] - cy) < 7) & (x[None, :] > cx) & (x[None, :] < cx + 40)
            coat(out, body, hexc("b8c0c8"), 0.85 + 0.3 * (bd > 0.4))
            out[body & (np.abs(y[:, None] - cy + 5) < 2)] = hexc("485868")
            tl = (x[None, :] >= cx + 40) & (x[None, :] < cx + 48) & (np.abs(y[:, None] - cy) < np.abs(x[None, :] - cx - 40) * 0.8 + 2)
            out[tl] = hexc("98a0a8")
            out[cy, cx + 4] = hexc("20242a")
    # cheese wheel bottom-left
    d = (x[None, :] - 60) ** 2 + (y[:, None] - 190) ** 2
    coat(out, d < 34 ** 2, hexc("c8a030"), 0.9 + 0.15 * (bd > 0.5))
    out[(d < 35 ** 2) & (d >= 32 ** 2)] = hexc("8a6818")
    wedge = (d < 30 ** 2) & (np.arctan2(y[:, None] - 190, x[None, :] - 60) > 0.4) & (np.arctan2(y[:, None] - 190, x[None, :] - 60) < 1.2)
    out[wedge] = hexc("e8d090")
    return out


def bottle():
    n = TILE
    out = np.zeros((n, n, 3)) + hexc("182018")
    r = np.random.default_rng(301)
    for cx in range(16, 256, 48):
        for cy in range(24, 256, 64):
            w = int(r.integers(14, 20))
            h = int(r.integers(40, 56))
            g = hexc(["2a4028", "3a2818", "203038"][int(r.integers(0, 3))])
            out[cy:cy + h, cx:cx + w] = g * (0.8 + 0.4 * r.random())
            out[cy:cy + h, cx:cx + 2] = g * 1.6
            out[cy:cy + h, cx + w - 2:cx + w] = g * 0.5
            nw = w // 3
            out[cy - 12:cy, cx + w // 2 - nw // 2:cx + w // 2 + nw // 2] = g * 1.1
            out[cy - 14:cy - 12, cx + w // 2 - nw // 2:cx + w // 2 + nw // 2] = hexc("8a6a40")
            out[cy + 4:cy + h - 6, cx + 3:cx + 5] = hexc("c8d8c0") * 0.7
            out[cy + h // 2:cy + h // 2 + 10, cx + 2:cx + w - 2] = hexc("d8c8a0") * 0.8
    return out


def brass():
    n = TILE
    v = 0.55 + 0.25 * (fbm(n, 8, 311, 3) - 0.5) + 0.12 * (pnoise(n, 32, 312) - 0.5)
    ramp = [hexc(c) for c in ("5a3c10", "6e4a14", "825818", "96661c", "aa7420", "be8224")]
    out = ramp_map(v, ramp)
    bd = bayer(n)
    streak = (np.abs(fbm(n, 16, 314, 2) - 0.5) < 0.035)
    out[streak] = hexc("e8c060")
    tarn = (fbm(n, 5, 316, 2) > 0.66) & (bd < (fbm(n, 5, 316, 2) - 0.66) * 2.5)
    out[tarn] = out[tarn] * 0.55 + hexc("3a4030") * 0.45
    x = np.arange(n)
    out[(x % 64) < 2] = out[(x % 64) < 2] * 0.6
    return out


def tar():
    n = TILE
    v = 0.3 + 0.1 * (fbm(n, 6, 321, 3) - 0.5)
    ramp = [hexc(c) for c in ("141008", "1a150c", "201a10", "261f14", "2c2418", "32291c")]
    out = ramp_map(v, ramp)
    bd = bayer(n)
    gloss = (fbm(n, 10, 324, 2) > 0.72) & (bd > 0.55)
    out[gloss] = out[gloss] * 1.8 + hexc("485060") * 0.25
    y = np.arange(n)
    out[(y % 32) < 2] = out[(y % 32) < 2] * 0.5
    drip = (fbm(n, 24, 326, 2) > 0.8)
    out[drip] = out[drip] * 0.6
    return out


def rack():
    n = TILE
    pw = 16
    x = np.arange(n)
    px = x // pw
    ph = np.random.default_rng(331).random(n)
    base = 0.4 + 0.2 * ph[px]
    grain = fbm(n, 8, 332, 3)
    v = base + 0.16 * (grain - 0.5)
    ramp = [hexc(c) for c in ("3a2812", "463116", "523a1a", "5e431e", "6a4c22", "765526")]
    out = ramp_map(v, ramp)
    xs = x % pw
    out[(xs == 0) | (xs == 1)] = out[(xs == 0) | (xs == 1)] * 0.3
    out[xs == 2] = out[xs == 2] * 1.24
    # iron upright with brackets every 128 px
    ux = x % 128
    upr = (ux < 6)
    coat(out, upr, hexc("24262a"), 0.8 + 0.5 * (fbm(n, 12, 335, 2) > 0.5))
    out[ux == 6] = hexc("5a5e66")
    y = np.arange(n)
    br = (ux > 5) & (ux < 22) & ((y % 64) < 5)
    out[br] = hexc("24262a")
    out[(ux == 22) & ((y % 64) < 5)] = hexc("5a5e66")
    for cy in range(10, n, 64):
        out[cy, 2] = hexc("8a94a2")
        out[cy, 3] = hexc("101216")
    return np.ascontiguousarray(out.transpose(1, 0, 2))


def ropemat():
    n = TILE
    x = np.arange(n)
    y = np.arange(n)
    dxx = np.minimum(np.abs(x - 128), n - np.abs(x - 128))[None, :]
    dyy = np.minimum(np.abs(y - 128), n - np.abs(y - 128))[:, None]
    d = np.sqrt(dxx ** 2 + dyy ** 2)
    ring = np.sin(d * 2 * np.pi / 14.0) * 0.5 + 0.5
    twist = np.sin((np.arctan2(dyy, dxx) * 128.0 / 3.14159 + d) * 2 * np.pi / 9.0) * 0.5 + 0.5
    v = 0.42 + 0.22 * ring + 0.14 * twist
    ramp = [hexc(c) for c in ("5a4828", "6a5630", "7a6438", "8a7240", "9a8048", "aa8e50")]
    out = ramp_map(v, ramp)
    bd = bayer(n)
    fray = (fbm(n, 12, 344, 2) > 0.74) & (bd > 0.5)
    out[fray] = out[fray] * 0.7
    return out


def ballast():
    n = TILE
    cell = 40
    g = np.random.default_rng(351)
    pts = g.random((n // cell, n // cell, 2)) * 0.6 + 0.2
    col_id = np.zeros((n, n), int)
    dist = np.full((n, n), 1e9)
    ys = np.arange(n)[:, None]
    xs = np.arange(n)[None, :]
    for iy in range(n // cell):
        for ix in range(n // cell):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    py = ((iy + dy) % (n // cell)) * cell + pts[iy, ix, 1] * cell
                    px = ((ix + dx) % (n // cell)) * cell + pts[iy, ix, 0] * cell
                    dyy = np.minimum(np.abs(ys - py), n - np.abs(ys - py))
                    dxx = np.minimum(np.abs(xs - px), n - np.abs(xs - px))
                    d = np.sqrt(dyy ** 2 + dxx ** 2)
                    m = d < dist
                    dist = np.where(m, d, dist)
                    col_id = np.where(m, (iy * 31 + ix * 13 + dy * 3 + dx) % 89, col_id)
    r = np.random.default_rng(352)
    sv = 0.35 + 0.3 * r.random(90)
    v = sv[col_id] + 0.06 * (fbm(n, 16, 353, 2) - 0.5)
    ramp = [hexc(c) for c in ("3a3834", "464440", "52504c", "5e5c58", "6a6864", "767470")]
    out = ramp_map(v, ramp)
    # rounded tops: lit crown and dark crevice per stone
    crown = dist < cell * 0.16
    out[crown] = out[crown] * 1.3
    edge = dist > cell * 0.36
    out[edge] = out[edge] * 0.4
    moss = (fbm(n, 6, 356, 2) > 0.7) & edge
    out[moss] = hexc("34402c")
    return out


BUILD = [ifloor, ihull, ceilp, cwall, rug, chart, ham, blank, books, food, bottle, brass, tar, rack, ropemat, ballast]


def main():
    atlas = np.zeros((SIZE, SIZE, 3))
    for k, fn in enumerate(BUILD):
        t = grit(fn(), 400 + k)
        iy, ix = divmod(k, 4)
        atlas[iy * TILE:(iy + 1) * TILE, ix * TILE:(ix + 1) * TILE] = t
    img = (np.clip(atlas, 0, 1) * 255.0 + 0.5).astype(np.uint8)
    import os
    out = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "game", "art", "vp1", "interior_px.png"))
    from PIL import Image
    Image.fromarray(img, "RGB").save(out)
    print("wrote", out, img.shape)


if __name__ == "__main__":
    main()
