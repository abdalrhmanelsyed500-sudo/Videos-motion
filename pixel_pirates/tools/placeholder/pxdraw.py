"""pxdraw - tiny palette-locked pixel drawing kit for the placeholder pipeline (Module A4).

Every pixel comes from game/data/look/palette.json ramps. Shapes carry a fake 3D normal so the
result is shaded with the SAME key light as the Art Bible (top-left, 4-band cel steps).
Run with /home/user/.venv/bin/python (needs numpy + pillow).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
PAL = json.loads((ROOT / "game" / "data" / "look" / "palette.json").read_text())
RAMPS = {k: [tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in v] for k, v in PAL["ramps"].items()}
RAMP_NAMES = list(RAMPS)
RAMP_ID = {n: i for i, n in enumerate(RAMP_NAMES)}
PALETTE_SET = {c for r in RAMPS.values() for c in r}

_L = np.array([-0.5, -0.6, 0.62])
_L = _L / np.linalg.norm(_L)
_EDGES = (0.18, 0.38, 0.62, 0.80)


def step_from_lambert(lam: np.ndarray, bias: int = 0) -> np.ndarray:
    v = 0.55 * lam + 0.20
    s = np.zeros(v.shape, dtype=np.int16)
    for e in _EDGES:
        s += (v >= e)
    return np.clip(s + bias, 0, 4)


class Canvas:
    """RGBA canvas that remembers which ramp each pixel came from (for outlines + QA)."""

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.rgba = np.zeros((h, w, 4), dtype=np.uint8)
        self.ramp = np.full((h, w), -1, dtype=np.int16)
        yy, xx = np.mgrid[0:h, 0:w]
        self.xx = xx.astype(float) + 0.5
        self.yy = yy.astype(float) + 0.5

    # -- painting -----------------------------------------------------------------
    def paint(self, mask: np.ndarray, normal, ramp: str, bias: int = 0, flat_step: int | None = None):
        if not mask.any():
            return
        if flat_step is not None:
            step = np.full(mask.shape, flat_step, dtype=np.int16)
        else:
            nx, ny, nz = normal
            lam = nx * _L[0] + ny * _L[1] + nz * _L[2]
            step = step_from_lambert(lam, bias)
        cols = np.array(RAMPS[ramp], dtype=np.uint8)
        self.rgba[mask, :3] = cols[step[mask]]
        self.rgba[mask, 3] = 255
        self.ramp[mask] = RAMP_ID[ramp]

    def ellipsoid(self, cx, cy, rx, ry, ramp, bias=0, clip=None):
        dx = (self.xx - cx) / rx
        dy = (self.yy - cy) / ry
        r2 = dx * dx + dy * dy
        mask = r2 <= 1.0
        if clip is not None:
            mask &= clip
        nz = np.sqrt(np.clip(1 - r2, 0, 1))
        self.paint(mask, (dx, dy, nz), ramp, bias)
        return mask

    def capsule(self, p0, p1, r0, ramp, r1=None, bias=0):
        r1 = r0 if r1 is None else r1
        (x0, y0), (x1, y1) = p0, p1
        vx, vy = x1 - x0, y1 - y0
        ll = vx * vx + vy * vy
        t = np.clip(((self.xx - x0) * vx + (self.yy - y0) * vy) / ll, 0, 1) if ll > 0 else np.zeros_like(self.xx)
        px, py = x0 + t * vx, y0 + t * vy
        rr = r0 + (r1 - r0) * t
        dx, dy = (self.xx - px) / rr, (self.yy - py) / rr
        d2 = dx * dx + dy * dy
        mask = d2 <= 1.0
        nz = np.sqrt(np.clip(1 - d2, 0, 1))
        self.paint(mask, (dx, dy, nz), ramp, bias)
        return mask

    def cylinder_v(self, x0, x1, y0, y1, ramp, bias=0):
        """vertical cylinder body (barrels, masts): shaded across x."""
        cx, r = (x0 + x1) / 2.0, (x1 - x0) / 2.0
        mask = (self.xx >= x0) & (self.xx < x1) & (self.yy >= y0) & (self.yy < y1)
        dx = (self.xx - cx) / r
        self.paint(mask, (dx, np.zeros_like(dx), np.sqrt(np.clip(1 - dx * dx, 0, 1))), ramp, bias)
        return mask

    def rect(self, x0, y0, x1, y1, ramp, step=2):
        mask = (self.xx >= x0) & (self.xx < x1) & (self.yy >= y0) & (self.yy < y1)
        self.paint(mask, None, ramp, flat_step=step)
        return mask

    def poly(self, pts, ramp, step=2, normal=None, bias=0):
        im = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=255)
        mask = np.asarray(im) > 0
        if normal is None:
            self.paint(mask, None, ramp, flat_step=step)
        else:
            self.paint(mask, normal, ramp, bias)
        return mask

    def dots(self, pts, ramp, step):
        cols = RAMPS[ramp]
        for x, y in pts:
            x, y = int(x), int(y)
            if 0 <= x < self.w and 0 <= y < self.h:
                self.rgba[y, x, :3] = cols[step]
                self.rgba[y, x, 3] = 255
                self.ramp[y, x] = RAMP_ID[ramp]

    # -- finishing ----------------------------------------------------------------
    def outline(self, only_if_ramp_in: set[str] | None = None):
        """1 px selective outline: transparent pixel next to an opaque one takes step 0 of that neighbour's ramp."""
        a = self.rgba[..., 3] > 0
        pad = np.pad(a, 1)
        rp = np.pad(self.ramp, 1, constant_values=-1)
        nb = np.zeros_like(a)
        src = np.full(a.shape, -1, dtype=np.int16)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            sh = pad[1 + dy:1 + dy + self.h, 1 + dx:1 + dx + self.w]
            rs = rp[1 + dy:1 + dy + self.h, 1 + dx:1 + dx + self.w]
            take = sh & (src < 0)
            src[take] = rs[take]
            nb |= sh
        edge = (~a) & nb
        for rid in np.unique(src[edge]):
            if rid < 0:
                continue
            m = edge & (src == rid)
            self.rgba[m, :3] = RAMPS[RAMP_NAMES[rid]][0]
            self.rgba[m, 3] = 255
            self.ramp[m] = rid

    def to_image(self) -> Image.Image:
        return Image.fromarray(self.rgba, "RGBA")


def flip_h(c: Canvas) -> Canvas:
    out = Canvas(c.w, c.h)
    out.rgba = c.rgba[:, ::-1].copy()
    out.ramp = c.ramp[:, ::-1].copy()
    return out


def periodic_noise(size: int, cells: int, rng: np.random.Generator) -> np.ndarray:
    """seamless value noise in [0,1], size x size."""
    g = rng.random((cells, cells))
    u = np.arange(size) * cells / size
    i0 = np.floor(u).astype(int) % cells
    i1 = (i0 + 1) % cells
    f = u - np.floor(u)
    f = f * f * (3 - 2 * f)
    top = g[np.ix_(i0, i0)] * (1 - f)[None, :] + g[np.ix_(i0, i1)] * f[None, :]
    bot = g[np.ix_(i1, i0)] * (1 - f)[None, :] + g[np.ix_(i1, i1)] * f[None, :]
    return top * (1 - f)[:, None] + bot * f[:, None]


def used_colours(img: Image.Image) -> set[tuple[int, int, int]]:
    a = np.asarray(img.convert("RGBA"))
    m = a[..., 3] > 0
    return {tuple(int(v) for v in px) for px in np.unique(a[m][:, :3], axis=0)}
