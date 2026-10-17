"""Tiny supersampled vector painter.  All coordinates are in character UNITS (y down);
the Art canvas has an origin (anchor) so every sprite knows where its joint is."""
import numpy as np, cv2

def hexc(h):
    h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

class Art:
    def __init__(self, x0, y0, x1, y1, ppu=2.0, ss=3):
        self.x0, self.y0, self.ppu, self.ss = x0, y0, ppu, ss
        self.w = int(round((x1 - x0) * ppu)); self.h = int(round((y1 - y0) * ppu))
        self.k = ppu * ss
        self.buf = np.zeros((self.h * ss, self.w * ss, 4), np.float32)   # premultiplied RGBA 0..1
        self._kern = {}

    # --- geometry helpers -------------------------------------------------
    def P(self, pts):
        p = np.asarray(pts, np.float64).reshape(-1, 2)
        q = np.empty_like(p); q[:, 0] = (p[:, 0] - self.x0) * self.k; q[:, 1] = (p[:, 1] - self.y0) * self.k
        return np.round(q * 16).astype(np.int32)       # 4 fractional bits

    def _mask(self):
        return np.zeros(self.buf.shape[:2], np.uint8)

    def _paint(self, mask, color, alpha=1.0, clip=False):
        m = mask.astype(np.float32) / 255.0
        if clip: m = m * (self.buf[..., 3] > 0.5)
        m = (m * alpha)[..., None]
        c = np.array([color[0] / 255, color[1] / 255, color[2] / 255, 1], np.float32)
        self.buf = self.buf * (1 - m) + c * m

    def _fill(self, draw, color, outline=None, ow=0.0, alpha=1.0, clip=False):
        m = self._mask(); draw(m, 255)
        if outline is not None and ow > 0:
            r = max(1, int(round(ow * self.k)))
            key = r
            if key not in self._kern: self._kern[key] = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
            self._paint(cv2.dilate(m, self._kern[key]), outline, alpha, clip)
        self._paint(m, color, alpha, clip)

    # --- primitives -------------------------------------------------------
    def poly(self, pts, color, outline=None, ow=0, alpha=1.0, clip=False):
        P = self.P(pts)
        self._fill(lambda m, v: cv2.fillPoly(m, [P], v, cv2.LINE_8, 4), color, outline, ow, alpha, clip)

    def ellipse(self, c, rx, ry, color, rot=0.0, outline=None, ow=0, alpha=1.0, clip=False, a0=0, a1=360):
        C = self.P([c])[0]; ax = (int(round(rx * self.k * 16)), int(round(ry * self.k * 16)))
        self._fill(lambda m, v: cv2.ellipse(m, (int(C[0]), int(C[1])), ax, float(np.degrees(rot)), a0, a1, v, -1, cv2.LINE_8, 4),
                   color, outline, ow, alpha, clip)

    def capsule(self, p0, p1, r0, r1, color, outline=None, ow=0, alpha=1.0, clip=False):
        p0 = np.array(p0, float); p1 = np.array(p1, float); d = p1 - p0; L = np.hypot(*d)
        pts = []
        if L < 1e-6:
            return self.ellipse(p0, r0, r0, color, outline=outline, ow=ow, alpha=alpha, clip=clip)
        ang = np.arctan2(d[1], d[0]); dr = np.arcsin(np.clip((r0 - r1) / L, -1, 1))
        for a in np.linspace(ang + np.pi / 2 + dr, ang + 3 * np.pi / 2 - dr, 24): pts.append(p0 + r0 * np.array([np.cos(a), np.sin(a)]))
        for a in np.linspace(ang - np.pi / 2 - dr, ang + np.pi / 2 + dr, 24): pts.append(p1 + r1 * np.array([np.cos(a), np.sin(a)]))
        self.poly(pts, color, outline, ow, alpha, clip)

    def rrect(self, x0, y0, x1, y1, r, color, outline=None, ow=0, alpha=1.0, clip=False):
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2); pts = []
        for (cx, cy, a0) in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            for a in np.linspace(a0, a0 + 90, 14): pts.append((cx + r * np.cos(np.radians(a)), cy + r * np.sin(np.radians(a))))
        self.poly(pts, color, outline, ow, alpha, clip)

    def curve(self, pts, color, w, alpha=1.0, clip=False, closed=False):
        """thick round-capped polyline; pts already smooth (dense)"""
        P = self.P(pts); t = max(1, int(round(w * self.k)))
        def d(m, v):
            cv2.polylines(m, [P], closed, v, t, cv2.LINE_8, 4)
            for q in (P[0], P[-1]): cv2.circle(m, (int(q[0] >> 4), int(q[1] >> 4)), t // 2, v, -1)
        self._fill(d, color, None, 0, alpha, clip)

    def result(self):
        a = cv2.resize(self.buf, (self.w, self.h), interpolation=cv2.INTER_AREA)
        return np.clip(a, 0, 1)

    def anchor_px(self, x=0.0, y=0.0):
        return ((x - self.x0) * self.ppu, (y - self.y0) * self.ppu)

def save_png(rgba_premult, path):
    a = rgba_premult[..., 3:4]
    rgb = np.where(a > 1e-4, rgba_premult[..., :3] / np.maximum(a, 1e-4), 0)
    out = np.concatenate([rgb[..., ::-1], a], -1)
    cv2.imwrite(str(path), (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))

def load_png(path):
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
    im[..., :3] *= im[..., 3:4]
    return im
