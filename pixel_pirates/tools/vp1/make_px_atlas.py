# VP-1A.3: the AUTHORED pixel-art atlas of the playable ship (game/art/vp1/ship_px.png).
# Every surface of the ship mesh (ship_mesh.gd) carries real UVs into this sheet instead of shader maths: 16 seamless
# 256 px tiles in a 4x4 grid, each drawn like hand-made pixel art - a limited ramp per tile, plank-by-plank hue and value
# shifts, 2 px seams with a lit lip, grain strokes, nails, cracks, dithered wear - at the texel density of each material
# (px per metre in PX_DENS of ship_mesh.gd), so a deck plank is ~16 texture pixels wide and stays rich at gameplay scale.
# Tiles are PERIODIC (wrapped noise) because the mesh UVs wrap inside a tile. Run:  python tools/vp1/make_px_atlas.py
import numpy as np

SIZE = 1024
TILE = 256


def pnoise(n, cells, seed):
    """Periodic value noise: n x n, `cells` lattice wraps, so the tile is seamless."""
    r = np.random.default_rng(seed)
    g = r.random((cells, cells))
    x = np.linspace(0, cells, n, endpoint=False)
    ix = x.astype(int)
    fx = x - ix
    fx = fx * fx * (3 - 2 * fx)
    i0 = ix % cells
    i1 = (ix + 1) % cells
    top = g[np.ix_(i0, i0)] * (1 - fx)[:, None] * (1 - fx)[None, :]
    top += g[np.ix_(i1, i0)] * fx[:, None] * (1 - fx)[None, :]
    top += g[np.ix_(i0, i1)] * (1 - fx)[:, None] * fx[None, :]
    top += g[np.ix_(i1, i1)] * fx[:, None] * fx[None, :]
    return top


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
    """Quantise a 0..1 field to the nearest colour of a small ramp: crisp pixel-art clusters, no smooth gradients."""
    v = np.clip(v, 0.0, 0.9999)
    idx = (v * len(ramp)).astype(int)
    out = np.zeros(v.shape + (3,))
    for k, c in enumerate(ramp):
        out[idx == k] = c
    return out


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255.0


def grit(out, seed, lo=0.90, hi=0.08, up=1.10, dn=0.88):
    r = np.random.default_rng(seed)
    h = r.random(out.shape[:2])
    out[h > lo] = np.clip(out[h > lo] * up, 0, 1)
    out[h < hi] = out[h < hi] * dn
    return out


def deck():
    n = TILE
    pw = 16                      # plank width in px (0.34 m at 48 px/m)
    x = np.arange(n)
    px = (x // pw)
    ph = np.random.default_rng(11).random(pw * 8)
    plank_id = px % (pw * 8)
    base = 0.44 + 0.30 * ph[plank_id]
    grain = fbm(n, 8, 21, 3)
    grain = 0.5 * grain + 0.5 * pnoise(n, 64, 22)
    stretch = fbm(n, 4, 23, 2)
    v = base + 0.20 * (grain - 0.5) + 0.10 * (stretch - 0.5)
    ramp = [hexc(c) for c in ("4a3418", "5f4522", "75562c", "8b6736", "a17840", "b7894a", "cd9a56")]
    out = ramp_map(v, ramp)
    xs = x % pw
    seam = (xs == 0) | (xs == 1)
    lip = (xs == 2)
    out[seam] = out[seam] * 0.28
    out[lip] = out[lip] * 1.3
    dith = (xs[None, :] % 4 == 0) & (bayer(n)[:, :] > 0.5)
    out[dith] = out[dith] * 0.90
    y = np.arange(n)
    off = (ph[plank_id] * 97).astype(int)
    jy = (y[:, None] + off[None, :]) % 96
    joint = ((jy == 0) | (jy == 1)) & (xs[None, :] > 1)
    jl = (jy == 2) & (xs[None, :] > 1)
    out[joint] = out[joint] * 0.3
    out[jl] = out[jl] * 1.25
    for k in range(pw * 8):
        if k % pw != 0:
            continue
        oy = int(ph[k] * 96)
        for yy in (oy + 3, oy + 93):
            for xx in (k + 3, k + pw - 4):
                if xx < n and yy < n:
                    out[yy, xx] = hexc("1c1206")
                    out[yy, (xx + 1) % n] = hexc("1c1206")
                    out[(yy + 1) % n, xx] = hexc("1c1206")
                    out[(yy - 1) % n, xx] = hexc("f0d898")
    wear = fbm(n, 5, 31, 2)
    bd = bayer(n)
    mask = (wear > 0.70) & (bd < (wear - 0.70) * 2.2)
    out[mask] = out[mask] * 0.75 + hexc("cfc0a0") * 0.25
    stain = (fbm(n, 3, 37, 2) < 0.34) & (bd > 0.5)
    out[stain] = out[stain] * 0.8
    r = np.random.default_rng(41)
    for c0 in (30, 150):
        xx = c0
        for yy in range(n):
            xx = (xx + r.integers(-1, 2)) % n
            out[yy, xx] = out[yy, xx] * 0.5
            if r.random() < 0.4:
                out[yy, (xx + 1) % n] = out[yy, (xx + 1) % n] * 0.7
    return np.ascontiguousarray(out.transpose(1, 0, 2))   # planks run fore-aft in ship space


def hull():
    n = TILE
    sh = 12
    y = np.arange(n)
    sid = (y // sh)
    r = np.random.default_rng(51)
    ph = r.random(n)
    base = 0.40 + 0.26 * ph[sid]
    grain = 0.6 * fbm(n, 6, 52, 3) + 0.4 * pnoise(n, 48, 53)
    v = base + 0.18 * (grain - 0.5)
    ramp = [hexc(c) for c in ("3a2513", "472e18", "55381d", "634224", "714c2a", "7f5631")]
    out = ramp_map(v, ramp)
    ys = y % sh
    lap = (ys == 0) | (ys == 1)
    lip = (ys == 2)
    out[lap] = out[lap] * 0.26
    out[lip] = out[lip] * 1.3
    hd = ((y[None, :] % 3) == 0) & (bayer(n) > 0.6)
    out[hd] = out[hd] * 0.88
    bd = bayer(n)
    streak = fbm(n, 16, 57, 2)
    m = (streak > 0.66) & (bd < (streak - 0.66) * 2.5)
    out[m] = out[m] * 0.62
    for row in range(n // sh):
        for xx in range(8, n, 32):
            yy = row * sh + sh // 2
            out[yy, xx] = hexc("20160c")
            out[yy, (xx + 1) % n] = hexc("8a7048")
    return out


def timber():
    n = TILE
    v = 0.55 + 0.22 * (fbm(n, 6, 61, 3) - 0.5) + 0.10 * (pnoise(n, 32, 62) - 0.5)
    ramp = [hexc(c) for c in ("4a3018", "5a3b1e", "6b4726", "7c532e", "8d6036", "9e6d3e")]
    out = ramp_map(v, ramp)
    bd = bayer(n)
    gr = fbm(n, 4, 63, 2)
    m = (np.abs(gr - 0.5) < 0.03)
    out[m] = out[m] * 0.72
    x = np.arange(n)
    out[:, x < 4] = out[:, x < 4] * 1.25
    out[:, x > n - 5] = out[:, x > n - 5] * 0.5
    knots = ((pnoise(n, 6, 66) > 0.86) & (bd > 0.5))
    out[knots] = out[knots] * 0.5 + hexc("2a1a0c") * 0.5
    gl = (np.abs(fbm(n, 12, 68, 2) - 0.5) < 0.04)
    out[gl] = out[gl] * 0.78
    return out


def canvas():
    n = TILE
    v = 0.62 + 0.10 * (fbm(n, 8, 71, 2) - 0.5)
    ramp = [hexc(c) for c in ("9a9078", "aaa086", "bab094", "cac0a2", "d8ceb0", "e4dcc0")]
    out = ramp_map(v, ramp)
    x = np.arange(n)
    weave = ((x[None, :] // 2) % 2) == ((x[:, None] // 2) % 2)
    out[weave] = out[weave] * 0.86
    y = np.arange(n)
    seam = (y % 96) < 3
    out[seam] = out[seam] * 0.68
    st = ((y[:, None] % 96) == 4) & ((x[None, :] % 4) < 2)
    out[st] = hexc("7c7460")
    for yy in range(32, n, 64):
        for xx in range(16, n, 64):
            out[yy, xx] = hexc("6a6250")
            out[yy, xx + 1] = hexc("6a6250")
    p = slice(150, 190)
    out[p, p] = out[p, p] * 0.88 + hexc("b0a888") * 0.12
    e = 150
    out[e, p] = hexc("7c7460")
    out[189, p] = hexc("7c7460")
    out[p, e] = hexc("7c7460")
    out[p, 189] = hexc("7c7460")
    return out


def rope():
    n = TILE
    x = np.arange(n)
    u = (x[None, :] + x[:, None]) * 0.25
    twist = np.sin(u * 2 * np.pi / 8.0) * 0.5 + 0.5
    fibre = pnoise(n, 64, 81)
    v = 0.45 + 0.30 * twist + 0.12 * (fibre - 0.5)
    ramp = [hexc(c) for c in ("6b5636", "7d6640", "8f764a", "a18654", "b39660", "c5a66c")]
    out = ramp_map(v, ramp)
    bd = bayer(n)
    fray = (fbm(n, 12, 82, 2) > 0.72) & (bd > 0.5)
    out[fray] = out[fray] * 0.7
    return out


def iron():
    n = TILE
    v = 0.42 + 0.16 * (fbm(n, 8, 91, 3) - 0.5) + 0.10 * (pnoise(n, 32, 92) - 0.5)
    ramp = [hexc(c) for c in ("1d2024", "26292e", "30343a", "3b3f46", "474c54", "545a63")]
    out = ramp_map(v, ramp)
    bd = bayer(n)
    r = np.random.default_rng(95)
    for k in range(14):
        xx, yy = r.integers(0, n, 2)
        for s in range(r.integers(8, 26)):
            xx = (xx + r.integers(-1, 2)) % n
            yy = (yy + r.integers(0, 2)) % n
            out[yy, xx] = out[yy, xx] * 0.6 + hexc("8d97a4") * 0.4
    rust = fbm(n, 5, 96, 2)
    m = (rust > 0.64) & (bd < (rust - 0.64) * 2.4)
    out[m] = out[m] * 0.5 + hexc("5a3a22") * 0.5
    for yy in range(16, n, 64):
        for xx in range(16, n, 64):
            out[yy, xx] = hexc("8a94a2")
            out[(yy + 1) % n, xx] = hexc("101216")
            out[yy, (xx + 1) % n] = hexc("5a626e")
    return out


def staves():
    n = TILE
    sw = 18
    x = np.arange(n)
    sid = x // sw
    r = np.random.default_rng(101)
    ph = r.random(n)
    base = 0.52 + 0.15 * ph[sid]
    grain = 0.65 * fbm(n, 6, 102, 3) + 0.35 * pnoise(n, 48, 103)
    grain = 0.5 * grain + 0.5 * pnoise(n, 96, 104)
    v = base + 0.18 * (grain - 0.5)
    ramp = [hexc(c) for c in ("4e3418", "5d3f1d", "6c4a23", "7b5529", "8a602f", "996b36")]
    out = ramp_map(v, ramp)
    xs = x % sw
    gap = (xs == 0)
    crown = (xs == sw // 2)
    out[(xs == 0) | (xs == 1)] = out[(xs == 0) | (xs == 1)] * 0.3
    out[xs == 2] = out[xs == 2] * 1.24
    out[crown] = out[crown] * 1.10
    y = np.arange(n)
    out[150, :] = out[150, :] * 0.75
    out[151, :] = out[151, :] * 0.85
    return out


def crate():
    n = TILE
    bw = 20
    x = np.arange(n)
    bid = x // bw
    r = np.random.default_rng(111)
    ph = r.random(n)
    base = 0.50 + 0.16 * ph[bid]
    grain = fbm(n, 6, 112, 3)
    v = base + 0.20 * (grain - 0.5)
    ramp = [hexc(c) for c in ("54401f", "634c26", "72582d", "816434", "90703b", "9f7c42")]
    out = ramp_map(v, ramp)
    xs = x % bw
    out[(xs == 0) | (xs == 1)] = out[(xs == 0) | (xs == 1)] * 0.3
    out[xs == 2] = out[xs == 2] * 1.28
    y = np.arange(n)
    for yy in (10, 118, 246 % n):
        for xx in range(6, n, bw):
            out[yy % n, xx] = hexc("241a10")
            out[(yy + 1) % n, xx] = hexc("a89060")
    bd = bayer(n)
    scuff = (fbm(n, 7, 115, 2) > 0.68) & (bd < 0.4)
    out[scuff] = out[scuff] * 0.8 + hexc("c8b890") * 0.2
    return out


def painted():
    n = TILE
    v = 0.55 + 0.08 * (fbm(n, 6, 121, 2) - 0.5)
    ramp = [hexc(c) for c in ("5e2420", "6d2b26", "7c322c", "8b3932", "9a4038", "a9473e")]
    out = ramp_map(v, ramp)
    x = np.arange(n)
    brush = np.tile(((x // 3) % 2) == 0, (n, 1))
    out[brush & (bayer(n) > 0.4)] = out[brush & (bayer(n) > 0.4)] * 0.90
    bd = bayer(n)
    chip = (fbm(n, 9, 124, 2) > 0.70) & (bd < (fbm(n, 9, 124, 2) - 0.70) * 3.0)
    out[chip] = hexc("6b4d28")
    return out


def net():
    n = TILE
    out = np.zeros((n, n, 3)) + hexc("20180e")
    x = np.arange(n)
    u = (x[None, :] + x[:, None]) % 32
    w = (x[None, :] - x[:, None]) % 32
    tw = 6
    on = (np.minimum(u, 32 - u) < tw) | (np.minimum(w, 32 - w) < tw)
    fibre = pnoise(n, 64, 131)
    v = 0.5 + 0.3 * (fibre - 0.5)
    ramp = [hexc(c) for c in ("6a5636", "7b6540", "8c744a", "9d8354", "ae925e")]
    col = ramp_map(v, ramp)
    edge = (np.minimum(u, 32 - u) == tw - 1) | (np.minimum(w, 32 - w) == tw - 1)
    col[edge] = col[edge] * 0.6
    out[on] = col[on]
    for yy in range(0, n, 16):
        for xx in range(0, n, 16):
            out[yy % n, xx % n] = hexc("54432a")
    return out


def lamp():
    n = TILE
    y = np.arange(n)
    g = 0.75 + 0.25 * np.sin(np.pi * np.clip(y / n, 0, 1))[:, None]
    v = g * (0.9 + 0.1 * pnoise(n, 8, 141))
    ramp = [hexc(c) for c in ("b06a20", "c88028", "e09630", "f0ac3c", "ffc24c", "ffd868")]
    out = ramp_map(np.clip(v * 0.72, 0, 0.999), ramp)
    bd = bayer(n)
    bub = (pnoise(n, 12, 142) > 0.8) & (bd > 0.6)
    out[bub] = out[bub] * 1.12
    soot = (y < 24) & (bd < 0.5)
    out[soot] = out[soot] * 0.55
    return out


def flag():
    n = TILE
    v = 0.4 + 0.12 * (fbm(n, 8, 151, 2) - 0.5)
    ramp = [hexc(c) for c in ("141418", "1a1a20", "202028", "26262e", "2c2c34", "32323a")]
    out = ramp_map(v, ramp)
    x = np.arange(n)
    weave = ((x[None, :] // 2) % 2) == ((x[:, None] // 2) % 2)
    out[weave] = out[weave] * 0.9
    bd = bayer(n)
    fray = (fbm(n, 10, 154, 2) > 0.74) & (bd > 0.55)
    out[fray] = out[fray] * 0.5
    return out


def sand():
    n = TILE
    v = 0.55 + 0.18 * (fbm(n, 10, 161, 3) - 0.5) + 0.08 * (pnoise(n, 64, 162) - 0.5)
    ramp = [hexc(c) for c in ("9a8a62", "aa9a70", "baaa7e", "caba8c", "dac99a", "ead9a8")]
    out = ramp_map(v, ramp)
    bd = bayer(n)
    r = np.random.default_rng(165)
    for k in range(26):
        xx, yy = r.integers(0, n, 2)
        out[yy, xx] = hexc("7c6c4c")
        out[yy, (xx + 1) % n] = hexc("e8e0c8")
    spk = np.random.default_rng(167).random((n, n))
    out[spk > 0.93] = out[spk > 0.93] * 1.15
    out[spk < 0.10] = out[spk < 0.10] * 0.85
    ripple = (np.abs(np.sin((np.arange(n)[:, None] * 0.22) + fbm(n, 4, 166, 2) * 4.0)) < 0.08) & (bd > 0.4)
    out[ripple] = out[ripple] * 0.86
    return out


def grass():
    n = TILE
    v = 0.5 + 0.2 * (fbm(n, 8, 171, 3) - 0.5)
    ramp = [hexc(c) for c in ("2c4a20", "365826", "40662c", "4a7432", "548238", "5e903e")]
    out = ramp_map(v, ramp)
    bd = bayer(n)
    x = np.arange(n)
    blade = ((x[None, :] * 1 + (x[:, None] // 2)) % 4) == 0
    tip = (blade) & (bd < 0.7)
    out[tip] = out[tip] * 1.25
    dark = (blade) & (bd > 0.85)
    out[dark] = out[dark] * 0.6
    r = np.random.default_rng(175)
    for k in range(8):
        xx, yy = r.integers(4, n - 4, 2)
        out[yy, xx] = hexc("e8e0a0") if k % 2 else hexc("d8a0b0")
    return out


def cobble():
    n = TILE
    cell = 48
    g = np.random.default_rng(181)
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
                    col_id = np.where(m, (iy * 37 + ix * 17 + dy * 5 + dx) % 97, col_id)
    r = np.random.default_rng(182)
    sv = 0.45 + 0.25 * r.random(98)
    v = sv[col_id] + 0.05 * (fbm(n, 16, 183, 2) - 0.5)
    ramp = [hexc(c) for c in ("4a4640", "565248", "625e54", "6e6a60", "7a766c", "86827a")]
    out = ramp_map(v, ramp)
    edge = dist > (cell * 0.40)
    out[edge] = out[edge] * 0.45
    moss = (fbm(n, 6, 186, 2) > 0.68) & (edge)
    out[moss] = hexc("3c5030")
    return out


def rock():
    n = TILE
    v = 0.45 + 0.25 * (fbm(n, 6, 191, 4) - 0.5)
    strata = 0.08 * np.sin(np.arange(n)[:, None] * 0.15 + fbm(n, 4, 192, 2) * 5)
    v = v + strata
    ramp = [hexc(c) for c in ("3a3630", "46423a", "524e46", "5e5a52", "6a665e", "76726a")]
    out = ramp_map(v, ramp)
    bd = bayer(n)
    lit = (fbm(n, 8, 195, 2) > 0.66) & (bd < 0.5)
    out[lit] = out[lit] * 1.2
    strl = (np.abs(np.sin(np.arange(n)[:, None] * 0.11 + fbm(n, 3, 197, 2) * 3.0)) < 0.06)
    out[strl] = out[strl] * 0.7
    return out


BUILD = [deck, hull, timber, canvas, rope, iron, staves, crate, painted, net, lamp, flag, sand, grass, cobble, rock]


def main():
    atlas = np.zeros((SIZE, SIZE, 3))
    for k, fn in enumerate(BUILD):
        t = grit(fn(), 300 + k)
        iy, ix = divmod(k, 4)
        atlas[iy * TILE:(iy + 1) * TILE, ix * TILE:(ix + 1) * TILE] = t
    img = (np.clip(atlas, 0, 1) * 255.0 + 0.5).astype(np.uint8)
    import os
    out = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "game", "art", "vp1", "ship_px.png"))
    from PIL import Image
    Image.fromarray(img, "RGB").save(out)
    print("wrote", out, img.shape)


if __name__ == "__main__":
    main()
