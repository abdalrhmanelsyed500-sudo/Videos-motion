"""Procedural kids-style park background with parallax layers (all drawn in code, deterministic)."""
import numpy as np, cv2, math

W_TILE = 3840

def _aa_circle(img, c, r, col):
    cv2.circle(img, (int(round(c[0] * 16)), int(round(c[1] * 16))), int(round(r * 16)), col, -1, cv2.LINE_AA, 4)

def _poly(img, pts, col):
    cv2.fillPoly(img, [np.round(np.array(pts) * 16).astype(np.int32)], col, cv2.LINE_AA, 4)

def _wrapx(f):
    """call f(dx) for dx in (-W,0,W) so features wrap seamlessly"""
    for dx in (-W_TILE, 0, W_TILE): f(dx)

def bgr(c): return (c[2], c[1], c[0])

class Park:
    def __init__(self, H=1080, W=1920, ground_y=940, scale=1.15, horizon=700):
        self.H, self.W, self.gy, self.S, self.hz = H, W, ground_y, scale, horizon
        self.rng = np.random.RandomState(7)
        self.sky = self._sky(); self.clouds = self._clouds(); self.hills1 = self._hills((172, 214, 196), 0.0, 520, 70, 3, 1.0)
        self.hills2 = self._hills((120, 196, 128), 1.7, 600, 55, 4, 2.0); self.trees = self._trees(); self.ground = self._ground(); self.fg = self._fg()

    def _rgba(self): return np.zeros((self.H, W_TILE, 4), np.uint8)

    def _sky(self):
        H, W = self.H, self.W
        top = np.array([255, 190, 120], np.float32); bot = np.array([255, 245, 225], np.float32)   # BGR: light blue -> pale
        t = np.linspace(0, 1, H)[:, None, None] ** 0.8; img = (top * (1 - t) + bot * t) * np.ones((1, W, 1), np.float32)
        yy, xx = np.mgrid[0:H, 0:W]; d = np.hypot(xx - 1540, yy - 190)
        glow = np.exp(-(d / 330) ** 2)[..., None] * np.array([120, 235, 255], np.float32) * 0.9
        img = np.clip(img + glow * 0.5, 0, 255).astype(np.uint8)
        # sun
        for r, a in ((110, .0), ):
            pass
        cv2.circle(img, (1540, 190), 78, (140, 235, 255), -1, cv2.LINE_AA); cv2.circle(img, (1540, 190), 62, (170, 245, 255), -1, cv2.LINE_AA)
        for i in range(16):
            a = i * math.pi / 8; p0 = (1540 + 100 * math.cos(a), 190 + 100 * math.sin(a)); p1 = (1540 + 140 * math.cos(a), 190 + 140 * math.sin(a))
            cv2.line(img, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), (140, 235, 255), 6, cv2.LINE_AA)
        return img

    def _clouds(self):
        L = self._rgba(); r = self.rng
        for i in range(7):
            cx = (i + .5) * W_TILE / 7 + r.uniform(-120, 120); cy = r.uniform(70, 190); sc = r.uniform(.7, 1.15)
            def draw(dx, cx=cx, cy=cy, sc=sc):
                tmp = np.zeros((self.H, W_TILE, 3), np.uint8); m = np.zeros((self.H, W_TILE), np.uint8)
                parts = [(-80, 12, 52), (-30, -14, 66), (30, -4, 74), (88, 10, 56), (0, 22, 62)]
                for (ox, oy, rr) in parts: cv2.circle(m, (int(cx + dx + ox * sc), int(cy + oy * sc)), int(rr * sc), 255, -1, cv2.LINE_AA)
                m = cv2.GaussianBlur(m, (0, 0), 1.2)
                L[..., :3][m > 0] = (255, 255, 255); sh = np.zeros_like(m)
                for (ox, oy, rr) in parts: cv2.circle(sh, (int(cx + dx + ox * sc), int(cy + oy * sc + 16 * sc)), int(rr * sc), 255, -1, cv2.LINE_AA)
                shade = (m > 0) & ~(cv2.erode(sh, np.ones((1, 1), np.uint8)) > 0)
                L[..., 3] = np.maximum(L[..., 3], m)
            _wrapx(draw)
        return L

    def _hills(self, col, ph, base, amp, n, f):
        L = self._rgba(); xs = np.arange(W_TILE)
        y = base + amp * (np.sin(2 * np.pi * (xs / W_TILE) * n + ph) * .6 + np.sin(2 * np.pi * (xs / W_TILE) * (2 * n + 1) + ph * 2) * .4)
        for x in xs:
            y0 = int(y[x]); L[y0:, x, :3] = bgr(col); L[y0:, x, 3] = 255
        L[..., 3] = cv2.GaussianBlur(L[..., 3], (0, 0), 1.0)
        return L

    def _tree(self, img, x, base, h, w, dark, light, trunk):
        _poly(img, [(x - w * .09, base), (x - w * .06, base - h * .45), (x + w * .06, base - h * .45), (x + w * .09, base)], bgr(trunk))
        for (ox, oy, rr, c) in ((-.28, -.62, .30, dark), (.28, -.62, .30, dark), (0, -.82, .36, dark), (-.1, -.7, .32, light), (.14, -.9, .26, light)):
            _aa_circle(img, (x + ox * w, base + oy * h), rr * w, bgr(c))
        _aa_circle(img, (x - .12 * w, base - .95 * h), .08 * w, bgr((190, 235, 150)))

    def _trees(self):
        L = self._rgba(); r = self.rng; img = L[..., :3].copy(); a = np.zeros((self.H, W_TILE), np.uint8)
        pal = [((52, 150, 70), (92, 190, 90)), ((40, 130, 90), (80, 176, 110)), ((70, 160, 60), (130, 205, 80))]
        for i in range(14):
            x0 = (i + r.uniform(.2, .8)) * W_TILE / 14; base = self.hz + 40 + r.uniform(-10, 20); h = r.uniform(190, 280); w = h * r.uniform(.9, 1.1)
            d, l = pal[i % 3]
            for dx in (-W_TILE, 0, W_TILE): self._tree(img, x0 + dx, base, h, w, d, l, (96, 66, 44))
        # mask = pixels changed from zero
        m = (img.sum(2) > 0).astype(np.uint8) * 255; m = cv2.GaussianBlur(m, (0, 0), .8)
        L[..., :3] = img; L[..., 3] = m
        return L

    def _ground(self):
        H = self.H; L = self._rgba(); hz = self.hz
        g0 = np.array([88, 200, 120], np.float32); g1 = np.array([60, 168, 70], np.float32)
        t = np.clip((np.arange(H) - hz) / (H - hz), 0, 1)[:, None, None]
        grad = g0 * (1 - t) + g1 * t
        L[hz:, :, :3] = grad[hz:].astype(np.uint8); L[hz:, :, 3] = 255
        # mowed stripes
        for i in range(0, W_TILE, 240):
            st = L[hz:, i:i + 120, :3].astype(np.float32); L[hz:, i:i + 120, :3] = np.clip(st * 1.05 + 4, 0, 255).astype(np.uint8)
        # sandy path
        y0, y1 = self.gy - 28, self.gy + 70
        path = np.zeros((self.H, W_TILE), np.uint8)
        pts = [(0, y0 + 4)] + [(x, y0 + 6 * math.sin(x / 520)) for x in range(0, W_TILE + 1, 80)] + [(W_TILE, y1)] + [(x, y1 + 8 * math.sin(x / 400 + 1)) for x in range(W_TILE, -1, -80)]
        cv2.fillPoly(path, [np.array(pts, np.int32)], 255, cv2.LINE_AA)
        pc = np.array([150, 205, 238], np.float32); m = (path / 255.0)[..., None]
        L[..., :3] = (L[..., :3] * (1 - m) + pc * m).astype(np.uint8)
        for k in range(120):
            x = self.rng.randint(0, W_TILE); y = self.rng.randint(y0 + 8, y1 - 4)
            cv2.ellipse(L, (x, y), (self.rng.randint(4, 9), 2), 0, 0, 360, (130, 185, 222, 255), -1, cv2.LINE_AA)
        # grass tufts and flowers on the meadow (behind & in front of the path)
        cols = [(80, 80, 240), (60, 220, 255), (255, 255, 255), (200, 120, 255), (60, 160, 255)]
        for k in range(150):
            x = self.rng.randint(0, W_TILE); y = self.rng.randint(hz + 20, H - 10)
            if y0 - 6 < y < y1 + 6: continue
            sc = 0.5 + 0.9 * (y - hz) / (H - hz)
            if k % 3 == 0:
                for j in (-1, 0, 1): cv2.line(L, (x + j * 5, y), (x + j * 8, y - int(18 * sc)), (50, 140, 60, 255), 3, cv2.LINE_AA)
            else:
                c = cols[k % len(cols)]; cv2.line(L, (x, y), (x, y - int(26 * sc)), (50, 140, 60, 255), 3, cv2.LINE_AA)
                for j in range(5):
                    a = j * 2 * math.pi / 5
                    cv2.circle(L, (x + int(7 * sc * math.cos(a)), y - int(26 * sc) + int(7 * sc * math.sin(a))), max(2, int(5 * sc)), (*c, 255), -1, cv2.LINE_AA)
                cv2.circle(L, (x, y - int(26 * sc)), max(2, int(4 * sc)), (60, 200, 255, 255), -1, cv2.LINE_AA)
        # picket fence along the horizon
        for x in range(0, W_TILE, 70):
            cv2.rectangle(L, (x, hz - 8), (x + 34, hz + 56), (245, 250, 255, 255), -1, cv2.LINE_AA)
            _poly(L, [(x, hz - 8), (x + 17, hz - 28), (x + 34, hz - 8)], (245, 250, 255, 255))
        cv2.rectangle(L, (0, hz + 6), (W_TILE, hz + 20), (230, 238, 250, 255), -1)
        cv2.rectangle(L, (0, hz + 34), (W_TILE, hz + 46), (230, 238, 250, 255), -1)
        return L

    def _fg(self):
        L = self._rgba(); r = self.rng
        for i in range(70):
            x = int(r.uniform(0, W_TILE)); h = r.uniform(30, 70)
            for j in range(-2, 3):
                _poly(L, [(x + j * 9, self.H), (x + j * 9 + 8, self.H), (x + j * 9 + 4 + j * 5, self.H - h * (1 - abs(j) * .15))], (40, 130, 56, 255))
        return L

    # ---------------------------------------------------------------- composition
    @staticmethod
    def _layer(canvas, L, off, y0=0):
        """alpha-composite tile L (BGRA uint8) at horizontal offset `off` (tile px), wrapping"""
        Wd = canvas.shape[1]; off = int(off) % W_TILE
        seg = np.concatenate([L[:, off:], L[:, :off]], 1)[:, :Wd] if off + Wd <= W_TILE else np.concatenate([L[:, off:], L[:, :Wd - (W_TILE - off)]], 1)
        a = seg[..., 3:4].astype(np.float32) / 255
        canvas[:] = canvas * (1 - a) + seg[..., :3].astype(np.float32) / 255 * a

    def back(self, cam_x, t):
        c = (self.sky.astype(np.float32) / 255).copy(); S = self.S
        self._layer(c, self.clouds, cam_x * 0.05 * S + t * 14)
        self._layer(c, self.hills1, cam_x * 0.10 * S)
        self._layer(c, self.hills2, cam_x * 0.20 * S)
        self._layer(c, self.trees, cam_x * 0.45 * S)
        self._layer(c, self.ground, cam_x * 1.0 * S)
        return c

    def front(self, canvas, cam_x):
        self._layer(canvas, self.fg, cam_x * 1.5 * self.S)
