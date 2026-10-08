"""Layer / camera / light / particle engine for the Chile-33 layered-puppet style.  (rebuilt in session 4)
canvas = float32 HxWx3 BGR 0..255.  Layers are premultiplied float32 BGRA."""
import cv2, math, os, numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1280, 720, 30
LAY = 'assets/layers'
FONT = 'assets/PirataOne-Regular.ttf'
DEJAVU = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def clamp(x, a=0.0, b=1.0): return a if x < a else (b if x > b else x)
def sstep(x): x = clamp(x); return x * x * (3 - 2 * x)
def seg(t, a, b): return clamp((t - a) / (b - a)) if b != a else (1.0 if t >= a else 0.0)
def ease_in(x): return clamp(x) ** 2.2
def ease_out(x): return 1 - (1 - clamp(x)) ** 2.2
def lerp(a, b, k): return a + (b - a) * k
def rng(seed): return np.random.default_rng(seed)


class Layer:
    def __init__(self, name, width=None, height=None, scale=None, fit=None):
        p = os.path.join(LAY, name)
        if not os.path.exists(p):
            for ext in ('.png', '.jpg'):
                if os.path.exists(p + ext): p += ext; break
        im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
        if im.shape[2] == 3: im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
        h0, w0 = im.shape[:2]
        if scale is None:
            if width: scale = width / w0
            elif height: scale = height / h0
            elif fit: scale = max(fit[0] / w0, fit[1] / h0)
            else: scale = 1.0
        if abs(scale - 1) > 1e-3:
            im = cv2.resize(im, (max(1, int(round(w0 * scale))), max(1, int(round(h0 * scale)))),
                            interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
        f = im.astype(np.float32); a = f[..., 3:] / 255.0
        f[..., :3] *= a; f[..., 3:] = a
        self.img = f; self.h, self.w = f.shape[:2]

    @staticmethod
    def from_array(bgra_premult):
        L = Layer.__new__(Layer); L.img = bgra_premult.astype(np.float32); L.h, L.w = L.img.shape[:2]; return L


_lc = {}
def get_layer(name, **kw):
    k = (name, tuple(sorted(kw.items())))
    if k not in _lc:
        if len(_lc) >= 7: _lc.pop(next(iter(_lc)))
        _lc[k] = Layer(name, **kw)
    return _lc[k]


def M3(tx=0, ty=0, sx=1.0, sy=None, rot=0.0, ax=0.0, ay=0.0):
    """anchor (ax, ay) of the layer lands at (tx, ty); scale+rotate about it"""
    sy = sx if sy is None else sy
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    R = np.array([[c * sx, -s * sy, 0], [s * sx, c * sy, 0], [0, 0, 1.0]])
    T0 = np.array([[1, 0, -ax], [0, 1, -ay], [0, 0, 1.0]]); T1 = np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1.0]])
    return T1 @ R @ T0


def place(cv, layer, M, alpha=1.0, gain=1.0, additive=False, tint=None):
    if alpha <= 0.003: return
    pts = np.array([[0, 0, 1], [layer.w, 0, 1], [layer.w, layer.h, 1], [0, layer.h, 1]], np.float64) @ M.T
    x0 = int(max(0, math.floor(pts[:, 0].min()))); x1 = int(min(W, math.ceil(pts[:, 0].max())))
    y0 = int(max(0, math.floor(pts[:, 1].min()))); y1 = int(min(H, math.ceil(pts[:, 1].max())))
    if x1 <= x0 or y1 <= y0: return
    Ms = M.copy(); Ms[0, 2] -= x0; Ms[1, 2] -= y0
    wp = cv2.warpAffine(layer.img, Ms[:2], (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    col = wp[..., :3] * gain
    if tint is not None: col = col * np.asarray(tint, np.float32)
    roi = cv[y0:y1, x0:x1]
    if additive: roi += col * alpha
    else:
        a = wp[..., 3:] * alpha; roi *= (1 - a); roi += col * alpha


def fill_rect(cv, color, alpha):
    if alpha <= 0.003: return
    cv *= (1 - alpha); cv += np.array(color, np.float32) * alpha


def heat_haze(cv, t, amp=1.5, freq=0.045, speed=3.0, y0=0, y1=H, ampx=1.0):
    ys = np.arange(H, dtype=np.float32)
    dx = np.where((ys >= y0) & (ys < y1), amp * ampx * np.sin(ys * freq + t * speed) * np.sin(ys * freq * 0.37 + t * speed * 0.6), 0).astype(np.float32)
    mx = (np.arange(W, dtype=np.float32)[None, :] + dx[:, None]); my = np.repeat(ys[:, None], W, 1)
    return cv2.remap(cv, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


class LightBuf:
    S = 4

    def __init__(self): self.b = np.zeros((H // self.S, W // self.S, 3), np.float32)

    def glow(self, x, y, r, color, amount=1.0):
        s = self.S
        cv2.circle(self.b, (int(x / s), int(y / s)), max(1, int(r / s)), tuple(float(c * amount) for c in color), -1, cv2.LINE_AA)

    def beam(self, x, y, ang_deg, length, spread_deg, color, amount=1.0, steps=6):
        s = self.S; a = math.radians(ang_deg); sp = math.radians(spread_deg)
        for i in range(steps):
            L = length * (1 - i / steps * 0.85)
            pts = np.array([(x / s, y / s), ((x + L * math.cos(a - sp)) / s, (y + L * math.sin(a - sp)) / s), ((x + L * math.cos(a + sp)) / s, (y + L * math.sin(a + sp)) / s)], np.int32)
            cv2.fillConvexPoly(self.b, pts, tuple(float(c * amount / steps) for c in color), cv2.LINE_AA)

    def sample(self, x, y):
        s = self.S
        return self.b[int(clamp(y / s, 0, self.b.shape[0] - 1)), int(clamp(x / s, 0, self.b.shape[1] - 1))]

    def apply(self, cv, blur=7, gain=1.0):
        s = self.S
        up = cv2.resize(cv2.GaussianBlur(self.b, (0, 0), blur / s * 2), (W, H), interpolation=cv2.INTER_CUBIC)
        cv += np.clip(up, 0, None) * gain
        return up


_pt = []
def puff_tex():
    if not _pt:
        n = 96; y, x = np.mgrid[-1:1:n * 1j, -1:1:n * 1j]; r = np.sqrt(x * x + y * y)
        a = np.clip(1 - r, 0, 1) ** 1.6
        a *= 0.75 + 0.25 * np.random.default_rng(3).random((n, n)).astype(np.float32) * 0 + 0.0
        _pt.append(cv2.GaussianBlur(a.astype(np.float32), (0, 0), 3))
    return _pt[0]


def puffs(cv, t, t0, t1, n, emit, color, seed=1, size=(60, 140), rise=(10, 60), spread=(60, 160), grow=1.8, life=3.0, alpha=0.6, wind=(0, 0)):
    tex = puff_tex(); r = rng(seed); col = np.array(color, np.float32)
    for i in range(n):
        tb = t0 + (t1 - t0) * r.random(); ex = emit[0] + emit[2] * r.random(); ey = emit[1] + emit[3] * r.random()
        sz = lerp(size[0], size[1], r.random()); rs = lerp(rise[0], rise[1], r.random()); sp = (r.random() - .5) * spread[1]
        age = (t - tb) / life
        if age <= 0 or age >= 1: continue
        x = ex + sp * age + wind[0] * (t - tb); y = ey - rs * (t - tb) + wind[1] * (t - tb)
        s = int(sz * (1 + (grow - 1) * age))
        if s < 4: continue
        a = alpha * math.sin(math.pi * age) ** 0.8
        x0, y0 = int(x - s / 2), int(y - s / 2); x1, y1 = x0 + s, y0 + s
        cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
        if cx1 <= cx0 or cy1 <= cy0: continue
        pa = cv2.resize(tex, (s, s))[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0, None] * a
        roi = cv[cy0:cy1, cx0:cx1]; roi *= (1 - pa); roi += col * pa


_vig = {}
def vignette(cv, strength=0.55, power=2.2, cx=W / 2, cy=H / 2):
    k = (round(strength, 2), power, int(cx), int(cy))
    if k not in _vig:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((x - cx) / (W * 0.62)) ** 2 + ((y - cy) / (H * 0.70)) ** 2)
        if len(_vig) > 12: _vig.clear()
        _vig[k] = (1 - strength * np.clip(r, 0, 1.4) ** power)[..., None].astype(np.float32)
    cv *= _vig[k]


def grain(cv, t, amt=7.0):
    r = np.random.default_rng(int(t * FPS) + 1000)
    n = r.normal(0, amt, (H // 2, W // 2)).astype(np.float32)
    cv += cv2.resize(n, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]


def tone(cv, contrast=1.08, lift=0.0, warm=(1.0, 1.0, 1.0), sat=0.85):
    cv[:] = (cv - 110) * contrast + 110 + lift
    g = cv.mean(axis=2, keepdims=True); cv[:] = g + (cv - g) * sat
    cv *= np.asarray(warm, np.float32)


_fc = {}
def font(size, path=None):
    k = (size, path)
    if k not in _fc: _fc[k] = ImageFont.truetype(path or FONT, size)
    return _fc[k]


def text_layer(txt, size=40, color=(88, 170, 225), path=None, spacing=0, stroke=2, glow=True):
    f = font(size, path)
    if spacing:
        widths = [f.getlength(ch) + spacing for ch in txt]; tw = int(sum(widths)) + 8
    else: tw = int(f.getlength(txt)) + 8
    th = int(size * 1.5); pad = 14
    im = Image.new('L', (tw + 2 * pad, th + 2 * pad), 0); d = ImageDraw.Draw(im)
    if spacing:
        x = pad
        for ch, wd in zip(txt, widths): d.text((x, pad), ch, font=f, fill=255); x += wd
    else: d.text((pad, pad), txt, font=f, fill=255)
    a = np.asarray(im, np.float32) / 255
    out = np.zeros(a.shape + (4,), np.float32)
    if stroke:
        sh = np.clip(cv2.GaussianBlur(a, (0, 0), 3.0) * 1.17, 0, 1)
        out[..., 3] = np.clip(sh + a, 0, 1); out[..., :3] = np.array(color, np.float32) * a[..., None]
    else:
        out[..., :3] = np.array(color, np.float32) * a[..., None]; out[..., 3] = a
    return Layer.from_array(out)
