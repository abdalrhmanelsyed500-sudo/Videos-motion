"""VP-1A: the ship material atlas (game/art/vp1/ship_mats.png).
Four tiles of 128x128 px at 14.4 px/m (one tile = 8.9 m), packed 2x2:  [deck planks | hull strakes] / [timber | sail canvas].
Channels: R = value (0..1, 0.5 = the base tint), G = warm(1)/cool(0) shift, B = crevice / wet mask (dark seams hold water), A = 255.
Everything is hand-tuned procedural pixel art (numpy), seeded, so the atlas is reproducible:  python tools/vp1/make_ship_mats.py
Planks run along the texture's VERTICAL axis in the deck tile (fore-aft), hull strakes along the HORIZONTAL axis, canvas panels vertical."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

T = 128
OUT = Path(__file__).resolve().parents[2] / "game" / "art" / "vp1" / "ship_mats.png"


def split_widths(total: int, lo: int, hi: int, rng) -> list[int]:
    out = []
    while sum(out) < total:
        w = int(rng.integers(lo, hi + 1))
        if total - sum(out) - w < lo:
            w = total - sum(out)
        out.append(w)
    return out


def smooth_noise(shape, scale, rng, wrap=True):
    """Tileable value noise: a coarse random grid, bilinear-upsampled."""
    gh, gw = max(shape[0] // scale, 2), max(shape[1] // scale, 2)
    g = rng.random((gh, gw)).astype(np.float32)
    ys = np.linspace(0, gh, shape[0], endpoint=False)
    xs = np.linspace(0, gw, shape[1], endpoint=False)
    y0 = np.floor(ys).astype(int) % gh
    x0 = np.floor(xs).astype(int) % gw
    y1, x1 = (y0 + 1) % gh, (x0 + 1) % gw
    fy = (ys - np.floor(ys))[:, None]
    fx = (xs - np.floor(xs))[None, :]
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0] * (1 - fx) + g[y0][:, x1] * fx
    b = g[y1][:, x0] * (1 - fx) + g[y1][:, x1] * fx
    return a * (1 - fy) + b * fy


def blotches(rng, thresh, scale=14):
    n = smooth_noise((T, T), scale, rng) * 0.65 + smooth_noise((T, T), scale // 2, rng) * 0.35
    return np.clip((n - thresh) / (1 - thresh), 0, 1)


def planks(vertical: bool, lo: int, hi: int, seed: int, joint_lo: int, joint_hi: int, nails: bool, weather: float):
    """Returns value, warm, crevice arrays for a tile of boards. Boards run along axis 0 when vertical else axis 1."""
    rng = np.random.default_rng(seed)
    val = np.zeros((T, T), np.float32)
    warm = np.zeros((T, T), np.float32)
    crev = np.zeros((T, T), np.float32)
    widths = split_widths(T, lo, hi, rng)
    x0 = 0
    for w in widths:
        base = rng.uniform(0.80, 1.06)
        wm = rng.uniform(-0.25, 0.25)
        # grain: stretched noise along the board, plus fine streaks
        gl = smooth_noise((T, w * 4), 9, rng)[:, :w] if False else None
        grain = np.zeros((T, w), np.float32)
        for k in range(w):
            col = smooth_noise((T, 2), int(rng.integers(10, 26)), rng)[:, 0]
            grain[:, k] = col
        grain = (grain - 0.5) * 0.20
        streak = (rng.random(w) - 0.5) * 0.10
        board = base + grain + streak[None, :]
        # edge: dark caulk seam on the left, a light bevel on the right
        board[:, 0] = 0.55 + 0.08 * rng.random()
        if w > 3:
            board[:, w - 1] = np.minimum(board[:, w - 1] + 0.10, 1.2)
        # butt joints
        pos = int(rng.integers(0, T))
        joints = []
        while True:
            pos += int(rng.integers(joint_lo, joint_hi))
            if pos >= T + joint_hi:
                break
            joints.append(pos % T)
        joints = sorted(set(joints))
        for j in joints:
            board[j % T, :] = 0.52
            if nails and w >= 4:
                for ny in (j + 2,):
                    for nx in (1, w - 2):
                        board[ny % T, nx] = 0.14
                        board[(ny - 1) % T, nx] = 1.0 if (ny - j) > 0 else board[(ny - 1) % T, nx]
        # knots
        for _ in range(int(rng.integers(0, 3))):
            ky, kx = int(rng.integers(4, T - 4)), int(rng.integers(1, max(w - 1, 2)))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    xx = kx + dx
                    if 0 <= xx < w:
                        board[(ky + dy) % T, xx] -= 0.16 if (dx or dy) else 0.30
        val[:, x0:x0 + w] = board
        warm[:, x0:x0 + w] = wm
        crev[:, x0] = 1.0
        for j in joints:
            crev[j % T, x0:x0 + w] = 1.0
        x0 += w
    # weathering: low-frequency light/dark, bleached salt streaks along the boards, dark damp patches
    wl = blotches(rng, 0.52, 18)
    dm = blotches(rng, 0.60, 12)
    val *= 1.0 + weather * (wl * 0.24 - dm * 0.30)
    warm += weather * (-wl * 0.5 + dm * 0.2)
    crev = np.clip(crev + dm * 0.5, 0, 1)
    if not vertical:
        val, warm, crev = val.T, warm.T, crev.T
    return val, warm, crev


def timber(seed=31):
    rng = np.random.default_rng(seed)
    val = np.zeros((T, T), np.float32)
    for k in range(T):
        col = smooth_noise((T, 2), int(rng.integers(8, 30)), rng)[:, 0]
        val[:, k] = col
    val = 0.78 + (val - 0.5) * 0.45
    # vertical grain streaks and a few cracks
    val += ((rng.random(T) - 0.5) * 0.12)[None, :]
    for _ in range(9):
        x, y = int(rng.integers(0, T)), int(rng.integers(0, T))
        for i in range(int(rng.integers(6, 20))):
            val[(y + i) % T, (x + (i // 7)) % T] = 0.28
    wl = blotches(rng, 0.55, 16)
    val *= 1.0 + wl * 0.16
    crev = (val < 0.40).astype(np.float32)
    warm = (wl - 0.4) * -0.3
    return val, warm, crev


def canvas(seed=47):
    rng = np.random.default_rng(seed)
    val = np.full((T, T), 0.92, np.float32)
    # cloth: very fine irregular weave (2 px) kept subtle so it does not moire
    yy, xx = np.mgrid[0:T, 0:T]
    val += (((xx + yy) % 2) * 0.03 - 0.015)
    val += (rng.random((T, T)) - 0.5) * 0.05
    # soft broad mottling (dirt, age)
    wl = blotches(rng, 0.40, 22)
    val *= 1.0 - wl * 0.12
    warm = np.full((T, T), 0.2, np.float32) + wl * 0.15
    crev = np.zeros((T, T), np.float32)
    # panels: vertical seams every 16 px with a stitched double line; each panel has its own value
    px = 0
    while px < T:
        w = 16
        val[:, px:px + w] *= rng.uniform(0.95, 1.05)
        val[:, px] = 0.60
        val[:, (px + 2) % T] = np.where((np.arange(T) // 2) % 2 == 0, 0.70, 0.98)
        crev[:, px] = 0.6
        px += w
    # horizontal tabling (hem) rows at the tile edge look like reefing bands every 64 px
    for r in (0, 64):
        val[r:r + 1, :] = 0.62
        val[(r + 2) % T, :] = np.where((np.arange(T) // 2) % 2 == 0, 0.72, 0.98)
        crev[r, :] = 0.6
    # patches: rectangles, darker and warmer, with a stitched border
    for (x, y, w, h, v) in ((22, 30, 22, 18, 0.74), (76, 78, 26, 20, 0.70), (96, 14, 14, 16, 0.78)):
        val[y:y + h, x:x + w] = v + (rng.random((h, w)) - 0.5) * 0.05
        warm[y:y + h, x:x + w] += 0.35
        for i in range(w):
            val[y, x + i] = 0.55 if i % 2 else 0.92
            val[y + h - 1, x + i] = 0.55 if i % 2 else 0.92
        for j in range(h):
            val[y + j, x] = 0.55 if j % 2 else 0.92
            val[y + j, x + w - 1] = 0.55 if j % 2 else 0.92
    # mildew and tar streaks near the foot (the tile bottom, texture v = 1 repeats, so keep them soft)
    st = blotches(rng, 0.62, 10)
    val *= 1.0 - st * 0.22
    return val, warm, crev


def main() -> None:
    d = planks(True, 4, 6, 5, 46, 100, True, 1.0)
    h = planks(False, 5, 7, 9, 36, 80, False, 1.3)
    t = timber()
    c = canvas()
    atlas = np.zeros((2 * T, 2 * T, 4), np.uint8)
    for (r, cc), (val, warm, crev) in (((0, 0), d), ((0, 1), h), ((1, 0), t), ((1, 1), c)):
        im = np.stack([np.clip(val * 0.5 / 1.0 * 1.0, 0, 1), np.clip(warm * 0.5 + 0.5, 0, 1), np.clip(crev, 0, 1), np.ones_like(val)], -1)
        # store value so that the base tint (1.0) is mid-grey: shader multiplies by (2 * R)
        atlas[r * T:(r + 1) * T, cc * T:(cc + 1) * T] = (im * 255 + 0.5).astype(np.uint8)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(atlas, "RGBA").save(OUT, optimize=True)
    print("wrote", OUT, OUT.stat().st_size, "bytes")
    prev = Image.fromarray(atlas[..., [0, 0, 0]].copy()).resize((512, 512), Image.NEAREST)
    prev.save("/tmp/ship_mats_preview.png")


if __name__ == "__main__":
    main()
