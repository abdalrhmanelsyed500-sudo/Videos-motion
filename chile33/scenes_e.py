"""Part 4 shots: day three, the surface vigil, the men organize, hunger, the drill breaks through."""
import cv2, math, numpy as np
from engine import *

GOLD = (70, 165, 225); LAMP = (120, 190, 255); RED = (45.0, 70.0, 225.0); ICE = (225, 175, 110)
CROP = {'camp': 40, 'refuge': 26, 'truck': 26, 'doctor': 26}
_tc = {}


def P(name): return get_layer('p4_' + name)


def txt(cv, s, x, y, size=40, color=GOLD, alpha=1.0, path=None, spacing=0, center=False, rot=0.0, scale=1.0):
    if alpha <= 0.01: return
    key = (s, size, tuple(color), path, spacing)
    if key not in _tc: _tc[key] = text_layer(s, size, color, path, spacing, stroke=1)
    lay = _tc[key]
    place(cv, lay, M3(x, y, scale, scale, rot, lay.w / 2 if center else 0, lay.h / 2 if center else 0), alpha=alpha)


def typed(cv, s, t, t0, t1, x, y, size=26, color=GOLD, path=DEJAVU, spacing=4, alpha=1.0, center=False):
    n = int(len(s) * seg(t, t0, t1))
    if n <= 0 or alpha <= 0.01: return
    key = (s[:n] + ('_' if n < len(s) else ''), size, tuple(color), path, spacing, 'T')
    if key not in _tc: _tc[key] = text_layer(key[0], size, color, path, spacing, stroke=1)
    lay = _tc[key]
    if center:
        wfull = (font(size, path).getlength(s) + spacing * len(s)) if True else lay.w
        x = x - wfull / 2
    place(cv, lay, M3(x, y, 1, 1, 0, 0, 0), alpha=alpha)


def pcam(layer, fx, fy, z, sh=(0.0, 0.0), over=1.0, cx=W / 2, cy=H / 2):
    s = max(W / layer.w, H / layer.h) * over * z
    tx = clamp(cx, W - (layer.w - fx) * s, fx * s); ty = clamp(cy, H - (layer.h - fy) * s, fy * s)
    return M3(tx + sh[0], ty + sh[1], s, s, 0, fx, fy)


def pt(M, x, y):
    q = M @ np.array([x, y, 1.0]); return float(q[0]), float(q[1])


def kf(t, keys):
    if t <= keys[0][0]: return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            u = sstep((t - t0) / (t1 - t0)); return tuple(lerp(p, q, u) for p, q in zip(a, b))
    return keys[-1][1]


def shk(t, amp, seed=0):
    return (amp * math.sin(t * 37 + seed) * math.sin(t * 11.3 + seed * 2), amp * math.cos(t * 29 + seed) * math.sin(t * 13 + seed * 1.7))


def flick(t, ph=0.0): return 0.88 + 0.12 * math.sin(t * 9 + ph) * math.sin(t * 2.3 + ph)


def beat(t, per=1.1):
    ph = (t % per) / per
    return max(math.exp(-ph * 10) * (ph < 0.5), 0.6 * math.exp(-((ph - 0.27) * 12) ** 2))


def shade_bottom(cv, h, a, power=1.5, k=0.7):
    if a <= 0.01: return
    s = np.linspace(0, 1, h, dtype=np.float32)[:, None, None] ** power * k * a
    cv[H - h:] *= (1 - s)


def dust_motes(cv, lb, t, n=60, seed=77, speed=(6, 16), up=0.0, bright=1.0):
    r = rng(seed)
    for i in range(n):
        x = (r.random() * W + t * (speed[0] + (speed[1] - speed[0]) * r.random())) % W
        y = (r.random() * H + 20 * math.sin(t * 0.6 + i) - up * t * (4 + 8 * r.random())) % H
        li = float(lb.sample(x, y).mean()); a = clamp(li * 1.5) * (0.30 + 0.4 * r.random()) * bright
        if a > 0.03:
            c = float(190 * a + 20); cv2.circle(cv, (int(x), int(y)), 1 + int(r.random() * 1.6), (c * 0.95, c, c * 1.05), -1, cv2.LINE_AA)


def sift(cv, t, amt, seed=5, lb=None, chunks=True):
    """dust and pebbles falling from the ceiling; amt 0..1"""
    r = rng(seed); n = int(110 * amt)
    for i in range(n):
        x = r.random() * W; sp = 60 + 140 * r.random(); y = (r.random() * H + t * sp) % H
        a = 0.35 + 0.5 * r.random(); c = 150 + 90 * a
        cv2.circle(cv, (int(x + 6 * math.sin(t * 2 + i)), int(y)), 1 + int(r.random() * 1.8), (c * 0.85, c * 0.95, c), -1, cv2.LINE_AA)
    if chunks:
        for i in range(int(10 * amt)):
            x = r.random() * W; sp = 260 + 260 * r.random(); y = (r.random() * H * 1.6 + t * sp) % (H * 1.3) - 40
            cv2.circle(cv, (int(x), int(y)), 3 + int(r.random() * 4), (24.0, 34.0, 44.0), -1, cv2.LINE_AA)


def wave(cv, t, amp, y0, alpha=1.0, color=GOLD, x0=150, x1=W - 150, seed=0, freq=1.0):
    if alpha <= 0.01: return
    xs = np.arange(x0, x1, 4)
    env = np.sin(np.pi * (xs - x0) / (x1 - x0)) ** 0.7
    ys = y0 + amp * env * (np.sin(xs * 0.19 * freq + t * 31 + seed) * 0.6 + np.sin(xs * 0.07 + t * 17) * 0.3 + np.sin(xs * 0.41 - t * 53) * 0.25)
    ov = cv.copy()
    cv2.polylines(ov, [np.stack([xs, ys], 1).astype(np.int32)], False, tuple(float(c) for c in color), 2, cv2.LINE_AA)
    cv[:] = cv * (1 - alpha * 0.9) + ov * alpha * 0.9


def ring(cv, cx, cy, R, frac, color=GOLD, th=4, alpha=1.0):
    if alpha <= 0.01: return
    ov = cv.copy(); cv2.circle(ov, (int(cx), int(cy)), R, tuple(float(c * 0.35) for c in color), 2, cv2.LINE_AA)
    n = int(clamp(frac) * 120)
    if n > 1:
        pts = np.array([[cx + R * math.sin(2 * math.pi * i / 120), cy - R * math.cos(2 * math.pi * i / 120)] for i in range(n + 1)], np.int32)
        cv2.polylines(ov, [pts], False, tuple(float(c) for c in color), th, cv2.LINE_AA)
    cv[:] = cv * (1 - alpha) + ov * alpha


def squeeze(cv, amt, cy=H * 0.62):
    if amt <= 0.01: return cv
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    w = np.exp(-((y - cy) / 190) ** 2)
    mx = x - (x - W / 2) * amt * 0.10 * w; my = y - (y - cy) * amt * 0.12 * w
    return cv2.remap(cv, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def pencil(cv, p0, p1, f, col=(28.0, 36.0, 46.0), th=3, seed=0):
    f = clamp(f)
    if f <= 0: return
    r = rng(seed); j = lambda: (r.random() - .5) * 2.0
    q1 = (p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f)
    cv2.line(cv, (int(p0[0] + j()), int(p0[1] + j())), (int(q1[0]), int(q1[1])), col, th, cv2.LINE_AA)


def tallies(cv, M, n, ox, oy, prog=1.0, gpr=3, gw=96, gh=100, col=(26.0, 34.0, 44.0), th=3):
    """pencil tally marks laid out in plate space; prog = fractional progress of the latest mark"""
    for i in range(int(math.ceil(n))):
        f = 1.0 if i < int(n) else clamp(n - int(n))
        if f <= 0: continue
        g, k = divmod(i, 5); x0 = ox + (g % gpr) * gw; y0 = oy + (g // gpr) * gh
        if k < 4: a, b = (x0 + k * 16, y0), (x0 + k * 16 + 2, y0 + 60)
        else: a, b = (x0 - 8, y0 + 50), (x0 + 70, y0 + 6)
        pencil(cv, pt(M, *a), pt(M, *b), f, col, th, seed=i)


def scribbles(cv, M, x0, y0, x1, nlines, prog, col=(40.0, 48.0, 58.0), lh=34, seed=3):
    r = rng(seed); total = nlines
    for ln in range(nlines):
        lp = clamp(prog * total - ln)
        if lp <= 0: continue
        pts = []; x = x0; words = 0
        while x < x1 - 40 * r.random() and x - x0 < (x1 - x0) * lp:
            if r.random() < 0.12: x += 12
            pts.append(pt(M, x, y0 + ln * lh + 6 * math.sin(x * 0.55 + ln) + (r.random() - .5) * 4)); x += 5
        if len(pts) > 1: cv2.polylines(cv, [np.array(pts, np.int32)], False, col, 2, cv2.LINE_AA)


def sun_icon(cv, x, y, r, col=GOLD, a=1.0):
    ov = cv.copy(); cv2.circle(ov, (int(x), int(y)), r, tuple(float(c) for c in col), -1, cv2.LINE_AA)
    for k in range(8):
        an = k * math.pi / 4; cv2.line(ov, (int(x + math.cos(an) * (r + 6)), int(y + math.sin(an) * (r + 6))), (int(x + math.cos(an) * (r + 18)), int(y + math.sin(an) * (r + 18))), tuple(float(c) for c in col), 3, cv2.LINE_AA)
    cv[:] = cv * (1 - a) + ov * a


def moon_icon(cv, x, y, r, col=ICE, a=1.0):
    ov = cv.copy(); cv2.circle(ov, (int(x), int(y)), r, tuple(float(c) for c in col), -1, cv2.LINE_AA)
    sub = cv.copy(); cv2.circle(ov, (int(x + r * 0.5), int(y - r * 0.25)), int(r * 0.85), (0.0, 0.0, 0.0), -1, cv2.LINE_AA)
    m = np.zeros((H, W), np.uint8); cv2.circle(m, (int(x), int(y)), r, 255, -1)
    k = (m > 0)[..., None]
    out = np.where(k, ov, cv)
    # restore crescent hole to the original plate
    hole = np.zeros((H, W), np.uint8); cv2.circle(hole, (int(x + r * 0.5), int(y - r * 0.25)), int(r * 0.85), 255, -1)
    out = np.where((hole > 0)[..., None] & k, cv, out)
    cv[:] = cv * (1 - a) + out * a


def panel(cv, x0, y0, x1, y1, a=0.6, border=GOLD, ba=0.8):
    ov = cv.copy(); cv2.rectangle(ov, (int(x0), int(y0)), (int(x1), int(y1)), (12.0, 10.0, 8.0), -1)
    cv[:] = cv * (1 - a) + ov * a
    ov2 = cv.copy(); cv2.rectangle(ov2, (int(x0), int(y0)), (int(x1), int(y1)), tuple(float(c) for c in border), 2, cv2.LINE_AA)
    cv[:] = cv * (1 - ba) + ov2 * ba


class ScenesE:
    # ------------------------------------------------------------------ e1 : day three (POV)
    def e1(self, t, cv):
        D = 8.0; L = P('pov'); br = math.sin(t * 1.25)
        z = lerp(1.0, 1.16, sstep(seg(t, 0, D))) + 0.008 * br
        M = pcam(L, 688, 430, z, (0, 3 * br))
        place(cv, L, M, gain=0.95)
        q = pt(M, 691, 133); lb = LightBuf(); fl = flick(t)
        lb.glow(q[0], q[1], 60, LAMP, 0.9 * fl); lb.glow(q[0], q[1], 330, (70, 130, 190), 0.55 * fl); lb.apply(cv, blur=40)
        dust_motes(cv, lb, t, 70, 12, (3, 9), up=0.3)
        puffs(cv, t, 4.8, 8.0, 18, (0, 100, W, 500), (70, 105, 135), seed=3, size=(160, 380), alpha=0.28 * sstep(seg(t, 5.2, 6.2)), life=3.4, rise=(-10, 14), spread=(30, 120), grow=2.0)
        pain = math.sin(math.pi * seg(t, 4.0, 5.3)) ** 2
        cv[:] = squeeze(cv, pain * (0.7 + 0.3 * math.sin(t * 14)))
        fill_rect(cv, (30, 40, 150), 0.22 * pain)
        vignette(cv, 0.15 + 0.4 * beat(t) + 0.25 * pain, 2.0)
        a = sstep(seg(t, 2.6, 3.0)) * (1 - sstep(seg(t, 4.4, 4.9)))
        txt(cv, 'DAY 3', W / 2, 150, 140, GOLD, a, spacing=10, center=True)
        typed(cv, 'SWEAT AND DUST', t, 5.8, 7.0, 56, 54, 28, GOLD, spacing=6, alpha=1 - seg(t, 7.5, 8.0))
        return cv

    # ------------------------------------------------------------------ e2 : drilling above, the sound fades
    def e2(self, t, cv):
        D = 5.4; L = P('ceiling')
        A = (0.22 + 0.78 * sstep(seg(t, 0.4, 1.6))) * (1 - 0.95 * sstep(seg(t, 3.7, 5.1)))
        M = pcam(L, 880, 330, lerp(1.05, 1.22, seg(t, 0, D)), shk(t, A * 7, 2))
        place(cv, L, M, gain=0.95)
        q = pt(M, 997, 158); lb = LightBuf(); fl = 1 - 0.35 * A * abs(math.sin(t * 38))
        lb.glow(q[0], q[1], 60, LAMP, 0.9 * fl); lb.glow(q[0], q[1], 360, (70, 130, 190), 0.55 * fl); lb.apply(cv, blur=40)
        dust_motes(cv, lb, t, 40, 13, (3, 9), up=-0.5)
        sift(cv, t, A, 7)
        wa = sstep(seg(t, 0.4, 0.9)) * (1 - sstep(seg(t, 4.8, 5.4)))
        wave(cv, t, 34 * A, H - 190, wa)
        typed(cv, 'DRILLING ABOVE', t, 0.5, 1.7, 56, 54, 28, GOLD, spacing=6, alpha=1 - seg(t, 4.4, 5.0))
        return cv

    # ------------------------------------------------------------------ e3 : the drill misses (cross-section)
    _rock = None

    def _rock_tex(self):
        if ScenesE._rock is None:
            r = np.random.default_rng(9); base = np.zeros((H, W), np.float32)
            for s_, w_ in ((60, 0.5), (22, 0.3), (7, 0.2)):
                n = r.normal(0, 1, (H // s_ + 2, W // s_ + 2)).astype(np.float32)
                base += cv2.resize(n, (W, H), interpolation=cv2.INTER_CUBIC) * w_
            yy = np.arange(H, dtype=np.float32)[:, None]; strata = 0.35 * np.sin(yy * 0.09 + base * 4)
            v = np.clip(0.45 + 0.22 * base + 0.12 * strata, 0, 1)
            tex = np.stack([v * 70, v * 98, v * 128], -1).astype(np.float32)
            ScenesE._rock = tex
        return ScenesE._rock

    def e3(self, t, cv):
        cv[:] = self._rock_tex() * 0.85
        gy = 120; sky = np.linspace(40, 10, gy, dtype=np.float32)[:, None, None] * np.array([1.2, 1.0, 0.8], np.float32)
        cv[:gy] = sky + 12
        # ragged surface
        xs = np.arange(0, W + 20, 20); ys = gy + 6 * np.sin(xs * 0.03) + 4 * np.sin(xs * 0.11)
        poly = np.concatenate([np.stack([xs, ys], 1), [[W + 20, 0], [0, 0]]]).astype(np.int32); cv2.fillPoly(cv, [poly], (30.0, 28.0, 26.0), cv2.LINE_AA)
        cv2.polylines(cv, [np.stack([xs, ys], 1).astype(np.int32)], False, (90.0, 150.0, 200.0), 2, cv2.LINE_AA)
        cx, cy = W / 2, 560
        # old tunnel / ramp down to the refuge
        path = [(150, gy + 8), (170, 230), (260, 280), (240, 360), (330, 420), (420, 470), (500, 510), (cx - 80, cy)]
        for a, b in zip(path, path[1:]): cv2.line(cv, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), (60.0, 100.0, 140.0), 3, cv2.LINE_AA)
        # refuge chamber
        pul = 0.8 + 0.2 * math.sin(t * 3)
        lb = LightBuf(); lb.glow(cx, cy, 110, LAMP, 0.7 * pul); lb.glow(cx, cy, 300, (60, 110, 170), 0.35); lb.apply(cv, blur=30)
        cv2.rectangle(cv, (int(cx - 80), int(cy - 30)), (int(cx + 80), int(cy + 30)), (20.0, 40.0, 70.0), -1)
        cv2.rectangle(cv, (int(cx - 80), int(cy - 30)), (int(cx + 80), int(cy + 30)), (110.0, 190.0, 255.0), 2, cv2.LINE_AA)
        r = rng(4)
        for i in range(33): cv2.circle(cv, (int(cx - 70 + (i % 11) * 14), int(cy - 14 + (i // 11) * 14)), 3, (180.0, 230.0, 255.0), -1, cv2.LINE_AA)
        typed(cv, 'THE REFUGE', t, 0.3, 1.3, cx - 55, cy + 44, 20, (150, 205, 235), spacing=5, alpha=1 - seg(t, 2.7, 3.0))
        # the two drills
        for (xd, t0, t1, ytop, lab, t_lab) in ((cx - 190, 0.05, 0.85, 500, 'MISS', 0.9), (cx + 215, 1.55, 2.35, 470, 'MISS', 2.4)):
            u = ease_out(seg(t, t0, t1)); yb = lerp(gy + 10, ytop, u)
            for k in range(3):
                cv2.line(cv, (int(xd - 3 + k * 3), gy - 40), (int(xd - 3 + k * 3), int(yb)), (150.0 - 25 * k, 160.0 - 25 * k, 172.0 - 25 * k), 2, cv2.LINE_AA)
            cv2.line(cv, (int(xd - 18), gy - 40), (int(xd + 18), gy - 40), (170.0, 180.0, 190.0), 5, cv2.LINE_AA)
            cv2.fillConvexPoly(cv, np.array([[xd - 9, yb], [xd + 9, yb], [xd + 1.5 * math.sin(t * 40), yb + 22]], np.int32), (190.0, 200.0, 210.0), cv2.LINE_AA)
            if u > 0 and u < 1:
                for s in range(5): cv2.circle(cv, (int(xd + (s - 2) * 7 * math.sin(t * 30 + s)), int(yb + 10 + s * 3)), 2, (120.0, 210.0, 255.0), -1, cv2.LINE_AA)
            if t > t_lab:
                a = sstep(seg(t, t_lab, t_lab + 0.2)); sc = 1 + 0.6 * (1 - sstep(seg(t, t_lab, t_lab + 0.25)))
                txt(cv, 'MISS', xd, ytop + 40, 54, (60, 90, 240), a, path=DEJAVU, center=True, scale=sc)
                cv2.line(cv, (int(xd - 38), int(ytop - 60)), (int(xd + 38), int(ytop + 14)), (50.0, 70.0, 235.0), 6, cv2.LINE_AA)
                cv2.line(cv, (int(xd + 38), int(ytop - 60)), (int(xd - 38), int(ytop + 14)), (50.0, 70.0, 235.0), 6, cv2.LINE_AA)
        cv[:] = squeeze(cv, 0)
        cv *= (1 + 0.0)
        return cv

    # ------------------------------------------------------------------ e4 : the vigil
    def e4(self, t, cv):
        D = 4.2; L = P('camp'); c = CROP['camp']
        M = pcam(L, 560, 380, lerp(1.02, 1.22, sstep(seg(t, 0, D))), (1.0 * math.sin(t * 0.9), 0.8 * math.sin(t * 1.3)))
        place(cv, L, M, gain=0.95)
        lb = LightBuf(); r = rng(21)
        for i in range(12):
            x = 260 + 60 * i + 25 * math.sin(i * 2.1); y = 500 + 30 * math.sin(i * 1.3); q = pt(M, x - c, y - c)
            fl = 0.7 + 0.3 * math.sin(t * (7 + i * 0.9) + i) * math.sin(t * 2.7 + i * 3)
            lb.glow(q[0], q[1], 26, (100, 175, 255), 0.5 * fl); lb.glow(q[0], q[1], 70, (60, 120, 200), 0.25 * fl)
        lb.apply(cv, blur=30)
        for i in range(70):
            x = r.random() * W; y = r.random() * H * 0.28; tw = 0.5 + 0.5 * math.sin(t * (1 + 3 * r.random()) + i)
            cv2.circle(cv, (int(x), int(y)), 1, (200.0 * tw, 215.0 * tw, 235.0 * tw), -1, cv2.LINE_AA)
        for i in range(26):  # embers rising from the candles
            x0 = 200 + r.random() * 880; sp = 14 + 24 * r.random(); ph = r.random() * 6
            y = (H * 0.78 - ((t * sp + ph * 40) % 220)); a = math.sin(math.pi * ((t * sp + ph * 40) % 220) / 220)
            cv2.circle(cv, (int(x + 10 * math.sin(t + ph)), int(y)), 1, (80.0 * a, 170.0 * a, 255.0 * a), -1, cv2.LINE_AA)
        puffs(cv, t, 0, D, 8, (0, 520, W, 120), (120, 90, 70), seed=8, size=(120, 260), alpha=0.1, life=3.6, rise=(0, 6), spread=(40, 80), wind=(30, 0))
        typed(cv, 'ABOVE GROUND', t, 0.4, 1.6, 56, 54, 28, GOLD, spacing=6, alpha=1 - seg(t, 3.7, 4.2))
        typed(cv, 'THE VIGIL', t, 1.4, 2.4, 56, 98, 38, (110, 205, 250), spacing=8, alpha=1 - seg(t, 3.7, 4.2))
        return cv

    # ------------------------------------------------------------------ e5 : rescuers drill blindly
    def e5(self, t, cv):
        D = 3.2; L = P('rig')
        sh = shk(t, 1.6, 3)
        M = pcam(L, 700, 300, lerp(1.0, 1.28, sstep(seg(t, 0, D))), sh)
        place(cv, L, M, gain=0.95)
        lb = LightBuf()
        for (x, y, s) in ((1032, 351, 0), (300, 400, 2), (1285, 110, 4)):
            q = pt(M, x, y); fl = 0.85 + 0.15 * math.sin(t * 8 + s)
            lb.glow(q[0], q[1], 40, (200, 230, 255), 0.7 * fl); lb.glow(q[0], q[1], 200, (110, 160, 200), 0.3 * fl)
            lb.beam(q[0], q[1], 200 + 40 * math.sin(t * 0.9 + s), 520, 10, (150, 190, 220), 0.35)
        lb.apply(cv, blur=24)
        puffs(cv, t, 0, D, 40, (0, 420, W, 220), (100, 140, 175), seed=11, size=(120, 300), alpha=0.22, life=3.0, rise=(0, 14), spread=(60, 160), wind=(120, 0))
        dust_motes(cv, lb, t, 50, 14, (30, 60))
        typed(cv, 'SEARCHING BLINDLY', t, 0.7, 2.4, 56, 54, 30, GOLD, spacing=6, alpha=1 - seg(t, 2.7, 3.2))
        return cv

    # ------------------------------------------------------------------ e6 : the maps were outdated
    def e6(self, t, cv):
        D = 2.2; L = P('map')
        M = pcam(L, 640, 384, lerp(1.0, 1.15, sstep(seg(t, 0, D))), (0.8 * math.sin(t * 1.1), 0.6 * math.sin(t * 1.5)))
        place(cv, L, M, gain=0.95)
        lb = LightBuf(); q = pt(M, 120, 90); lb.glow(q[0], q[1], 90, LAMP, 0.8); lb.glow(q[0], q[1], 400, (70, 120, 180), 0.45 * flick(t)); lb.apply(cv, blur=40)
        for i, (x, y) in enumerate(((400, 300), (820, 250), (760, 560))):
            a = sstep(seg(t, 0.3 + 0.2 * i, 0.6 + 0.2 * i)) * (0.7 + 0.3 * math.sin(t * 5 + i))
            sx, sy = pt(M, x, y); txt(cv, '?', sx, sy, 96, (60, 90, 235), a, path=DEJAVU, center=True)
        if t > 0.9:
            k = seg(t, 0.9, 1.15); sc = 2.4 - 1.4 * ease_out(k); a = sstep(seg(t, 0.9, 1.0))
            sx, sy = pt(M, 700, 390)
            txt(cv, 'OUTDATED', sx + shk(t, 5 * math.exp(-(t - 1.15) * 5) * (t > 1.15), 1)[0], sy, 120, (50, 70, 225), a, spacing=6, center=True, rot=-10, scale=sc)
            if t < 1.25: fill_rect(cv, (210, 220, 235), 0.4 * (1 - seg(t, 0.95, 1.25)))
        return cv

    # ------------------------------------------------------------------ e7 : inside, they organized
    def e7(self, t, cv):
        D = 4.0; L = P('refuge'); c = CROP['refuge']
        M = pcam(L, 688, 380, lerp(1.0, 1.15, sstep(seg(t, 0, D))), (1.0 * math.sin(t * 0.9), 0.8 * math.sin(t * 1.3)))
        place(cv, L, M, gain=0.55 + 0.4 * sstep(seg(t, 1.5, 3.2)))
        q = pt(M, 688 - c, 70 - c); lb = LightBuf(); fl = flick(t)
        lb.glow(q[0], q[1], 60, LAMP, 0.9 * fl); lb.glow(q[0], q[1], 380, (70, 130, 190), 0.6 * fl); lb.apply(cv, blur=40)
        dust_motes(cv, lb, t, 50, 15, (3, 9), up=0.3)
        typed(cv, 'INSIDE', t, 0.2, 0.9, 56, 54, 30, GOLD, spacing=8, alpha=1 - seg(t, 2.5, 3.0))
        a = sstep(seg(t, 3.0, 3.5)); txt(cv, 'THEY ORGANIZED', W / 2, 90, 96, GOLD, a, spacing=6, center=True)
        return cv

    # ------------------------------------------------------------------ e8 : Urzua maps the tunnels, sets the day / night rhythm
    def e8(self, t, cv):
        D = 7.4; L = P('map')
        M = pcam(L, 660, 384, lerp(1.02, 1.12, sstep(seg(t, 0, D))), (0.8 * math.sin(t * 1.1), 0.6 * math.sin(t * 1.5)))
        place(cv, L, M, gain=0.9)
        lb = LightBuf(); q = pt(M, 120, 90); lb.glow(q[0], q[1], 90, LAMP, 0.8); lb.glow(q[0], q[1], 400, (70, 120, 180), 0.45 * flick(t)); lb.apply(cv, blur=40)
        # pencil path: spiral ramp redrawn by hand
        cx0, cy0 = 667, 386; n = 160; f = ease_out(seg(t, 0.6, 3.4))
        pts = []
        for i in range(int(n * f) + 1):
            s = i / n; an = 2 * math.pi * 2.3 * s + 0.4; rr = 40 + 250 * s
            pts.append(pt(M, cx0 + rr * math.cos(an) * 1.18, cy0 + rr * math.sin(an) * 0.82))
        if len(pts) > 1:
            cv2.polylines(cv, [np.array(pts, np.int32)], False, (40.0, 120.0, 215.0), 4, cv2.LINE_AA)
            tip = pts[-1]; l2 = LightBuf(); l2.glow(tip[0], tip[1], 18, (150, 215, 255), 0.9); l2.apply(cv, blur=10)
        # Urzua inset
        fr = P('urzua'); ia = sstep(seg(t, 0.3, 0.8))
        crop = fr.img[110:410, 395:695, :3] / np.maximum(fr.img[110:410, 395:695, 3:], 1e-3)
        crop = cv2.resize(crop, (150, 150), interpolation=cv2.INTER_AREA)
        ic = (120, 150); m = np.zeros((H, W), np.float32); cv2.circle(m, ic, 75, 1.0, -1, cv2.LINE_AA)
        canvas = np.zeros_like(cv); canvas[ic[1] - 75:ic[1] + 75, ic[0] - 75:ic[0] + 75] = crop
        mm = (m * ia)[..., None]; cv[:] = cv * (1 - mm) + canvas * mm
        cv2.circle(cv, ic, 77, tuple(float(c * ia) for c in GOLD), 3, cv2.LINE_AA)
        panel(cv, 200, 106, 590, 200, 0.55 * ia * (1 - seg(t, 6.6, 7.2)), GOLD, 0.5 * ia * (1 - seg(t, 6.6, 7.2)))
        typed(cv, 'LUIS URZUA', t, 0.5, 1.5, 214, 128, 30, GOLD, spacing=5, alpha=1 - seg(t, 6.6, 7.2))
        typed(cv, 'MAPPED THE TUNNELS', t, 1.0, 2.6, 214, 168, 18, (150, 205, 235), spacing=4, alpha=1 - seg(t, 6.6, 7.2))
        # day / night dial
        ca = sstep(seg(t, 3.6, 4.2)) * (1 - sstep(seg(t, 6.9, 7.4)))
        if ca > 0.01:
            cx_, cy_, R_ = W - 190, 250, 100
            panel(cv, cx_ - 150, cy_ - 150, cx_ + 150, cy_ + 205, 0.55 * ca, GOLD, 0.7 * ca)
            ov = cv.copy()
            cv2.ellipse(ov, (cx_, cy_), (R_, R_), 0, -90, 90, (70.0, 165.0, 225.0), 12, cv2.LINE_AA)
            cv2.ellipse(ov, (cx_, cy_), (R_, R_), 0, 90, 270, (225.0, 150.0, 80.0), 12, cv2.LINE_AA)
            ang = (t - 3.6) * 0.9
            cv2.line(ov, (cx_, cy_), (int(cx_ + math.sin(ang) * (R_ - 20)), int(cy_ - math.cos(ang) * (R_ - 20))), (240.0, 240.0, 240.0), 5, cv2.LINE_AA)
            cv2.circle(ov, (cx_, cy_), 7, (240.0, 240.0, 240.0), -1, cv2.LINE_AA)
            cv[:] = cv * (1 - ca) + ov * ca
            sun_icon(cv, cx_ + 50, cy_ - 10, 14, GOLD, ca); moon_icon(cv, cx_ - 52, cy_ - 8, 20, ICE, ca)
            typed(cv, 'DAY', t, 5.0, 5.4, cx_ + 22, cy_ + 120, 22, GOLD, spacing=5, alpha=ca)
            typed(cv, 'NIGHT', t, 5.3, 5.8, cx_ - 108, cy_ + 120, 22, ICE, spacing=5, alpha=ca)
            if t > 6.0:
                cv2.line(cv, (int(cx_ + 26), int(cy_ - 36)), (int(cx_ + 74), int(cy_ + 16)), (50.0 * ca, 70.0 * ca, 235.0 * ca), 5, cv2.LINE_AA)
                typed(cv, 'NO SUN', t, 6.0, 6.5, cx_ - 40, cy_ + 160, 22, RED, spacing=5, alpha=ca)
        return cv

    # ------------------------------------------------------------------ e9 : truck headlights = daylight
    def e9(self, t, cv):
        D = 4.8; L = P('truck'); c = CROP['truck']
        off = sstep(seg(t, 3.0, 3.25)); flk = 1.0 if t < 2.9 else (0.5 + 0.5 * (math.sin(t * 60) > 0)) * (1 - off)
        M = pcam(L, 640, 380, lerp(1.0, 1.14, sstep(seg(t, 0, D))), (0.8 * math.sin(t * 0.9), 0.6 * math.sin(t * 1.3)))
        on = (1 - off) * (0.6 + 0.4 * flk)
        place(cv, L, M, gain=lerp(0.27, 1.0, on), tint=tuple(np.array([1, 1, 1.0]) * (1 - off) + np.array([1.25, 1.0, 0.7]) * off))
        lb = LightBuf()
        for x in (548 - c, 793 - c):
            q = pt(M, x, 386 - c)
            lb.glow(q[0], q[1], 50, (200, 240, 255), 1.0 * on); lb.glow(q[0], q[1], 260, (110, 190, 255), 0.6 * on)
        lb.apply(cv, blur=26)
        dust_motes(cv, lb, t, 60, 16, (3, 9), up=0.2, bright=1.4 * on + 0.2)
        # day / night labels
        sun_icon(cv, 90, 98, 18, GOLD, (1 - off) * sstep(seg(t, 0.2, 0.6))); moon_icon(cv, 90, 98, 24, ICE, off)
        typed(cv, 'DAYLIGHT', t, 0.4, 1.6, 140, 82, 30, GOLD, spacing=8, alpha=1 - off)
        typed(cv, 'NIGHT', t, 3.3, 4.2, 140, 82, 30, ICE, spacing=8, alpha=off)
        return cv

    # ------------------------------------------------------------------ e10 : dividing the refuge
    def e10(self, t, cv):
        D = 5.2; L = P('refuge'); c = CROP['refuge']
        M = pcam(L, 688, 400, lerp(1.0, 1.1, sstep(seg(t, 0, D))), (0.8 * math.sin(t * 0.9), 0.6 * math.sin(t * 1.3)))
        place(cv, L, M, gain=0.85)
        q = pt(M, 688 - c, 70 - c); lb = LightBuf(); fl = flick(t)
        lb.glow(q[0], q[1], 60, LAMP, 0.9 * fl); lb.glow(q[0], q[1], 380, (70, 130, 190), 0.55 * fl); lb.apply(cv, blur=40)
        dust_motes(cv, lb, t, 40, 17, (3, 9), up=0.3)
        def zone(x0, y0, x1, y1, t0, col, label, icon):
            a = sstep(seg(t, t0, t0 + 0.5)) * (1 - sstep(seg(t, D - 0.5, D)))
            if a <= 0.01: return
            p0 = pt(M, x0, y0); p1 = pt(M, x1, y1)
            ov = cv.copy(); cv2.rectangle(ov, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), tuple(float(k) for k in col), -1)
            cv[:] = cv * (1 - 0.22 * a) + ov * 0.22 * a
            for k in range(int(p0[0]), int(p1[0]), 24):  # dashed outline
                cv2.line(cv, (k, int(p0[1])), (min(k + 12, int(p1[0])), int(p0[1])), tuple(float(k_ * a) for k_ in col), 3, cv2.LINE_AA)
                cv2.line(cv, (k, int(p1[1])), (min(k + 12, int(p1[0])), int(p1[1])), tuple(float(k_ * a) for k_ in col), 3, cv2.LINE_AA)
            for k in range(int(p0[1]), int(p1[1]), 24):
                cv2.line(cv, (int(p0[0]), k), (int(p0[0]), min(k + 12, int(p1[1]))), tuple(float(k_ * a) for k_ in col), 3, cv2.LINE_AA)
                cv2.line(cv, (int(p1[0]), k), (int(p1[0]), min(k + 12, int(p1[1]))), tuple(float(k_ * a) for k_ in col), 3, cv2.LINE_AA)
            typed(cv, label, t, t0 + 0.1, t0 + 1.1, p0[0] + 14, p0[1] - 42, 28, col, spacing=7, alpha=a)
            if icon == 'moon': moon_icon(cv, p1[0] - 40, p0[1] + 40, 22, col, a)
            else:
                cx_, cy_ = p1[0] - 40, p0[1] + 40; ring(cv, cx_, cy_, 22, 0.78, col, 4, a)
                cv2.line(cv, (int(cx_), int(cy_)), (int(cx_), int(cy_ - 14)), tuple(float(k_ * a) for k_ in col), 3, cv2.LINE_AA)
        # central dashed divider draws first
        dv = seg(t, 0.7, 1.7)
        if dv > 0:
            a_, b_ = pt(M, 540, 120), pt(M, 540, 720)
            for k in range(int(a_[1]), int(lerp(a_[1], b_[1], dv)), 26):
                cv2.line(cv, (int(a_[0]), k), (int(a_[0]), k + 13), (70.0, 165.0, 225.0), 3, cv2.LINE_AA)
        zone(20, 330, 520, 700, 2.2, (110.0, 170.0, 235.0), 'SLEEPING', 'moon')
        zone(560, 250, 1320, 700, 3.2, (120.0, 215.0, 170.0), 'WAITING', 'clock')
        return cv

    # ------------------------------------------------------------------ e11 : jobs for everyone
    def e11(self, t, cv):
        D = 5.0; L = P('refuge')
        M = pcam(L, 688, 400, 1.05, (0.5 * math.sin(t * 0.9), 0.4 * math.sin(t * 1.3)))
        place(cv, L, M, gain=0.30)
        txt(cv, 'JOBS', W / 2, 70, 100, GOLD, sstep(seg(t, 0.1, 0.5)) * (1 - seg(t, 4.5, 5.0)), spacing=14, center=True)
        cards = [(1.35, 'TRACKING THE FOOD', 'ledger'), (2.6, 'RATIONING THE WATER', 'drop'), (3.6, 'TENDING TO THE SICK', 'cross')]
        for i, (t0, label, icon) in enumerate(cards):
            a = sstep(seg(t, t0, t0 + 0.5)) * (1 - seg(t, 4.5, 5.0)); cx_ = 230 + i * 410; cy_ = 330
            if a <= 0.01: continue
            dy = 30 * (1 - sstep(seg(t, t0, t0 + 0.5)))
            panel(cv, cx_ - 170, cy_ - 150 + dy, cx_ + 170, cy_ + 150 + dy, 0.65 * a, GOLD, 0.9 * a)
            ov = cv.copy(); col = (70.0, 165.0, 225.0); y0 = cy_ + dy - 20
            if icon == 'ledger':
                cv2.rectangle(ov, (cx_ - 60, int(y0 - 80)), (cx_ + 60, int(y0 + 70)), col, 4, cv2.LINE_AA)
                for k in range(4):
                    cv2.line(ov, (cx_ - 40, int(y0 - 45 + k * 30)), (cx_ + 30, int(y0 - 45 + k * 30)), col, 3, cv2.LINE_AA)
                    if seg(t, t0 + 0.4 + 0.2 * k, t0 + 0.6 + 0.2 * k) > 0: cv2.line(ov, (cx_ + 36, int(y0 - 45 + k * 30)), (cx_ + 44, int(y0 - 38 + k * 30)), (120.0, 215.0, 170.0), 4, cv2.LINE_AA)
            elif icon == 'drop':
                pts = [(cx_ + 60 * math.sin(a_) * (1 if a_ < math.pi else 1), y0 + 20 + 60 * -math.cos(a_)) for a_ in np.linspace(0.0, 2 * math.pi, 60)]
                pts = np.array([(cx_ + 56 * math.sin(a_), y0 + 25 - 56 * math.cos(a_)) for a_ in np.linspace(0.65, 2 * math.pi - 0.65, 50)] + [(cx_, y0 - 85)], np.int32)
                cv2.polylines(ov, [pts], True, (225.0, 175.0, 110.0), 4, cv2.LINE_AA)
                lvl = lerp(0.9, 0.3, seg(t, t0 + 0.3, t0 + 1.8)); cv2.rectangle(ov, (cx_ - 36, int(y0 + 80 - lvl * 80)), (cx_ + 36, int(y0 + 70)), (225.0, 175.0, 110.0), -1)
            else:
                cv2.rectangle(ov, (cx_ - 18, int(y0 - 70)), (cx_ + 18, int(y0 + 70)), (110.0, 120.0, 235.0), -1, cv2.LINE_AA)
                cv2.rectangle(ov, (cx_ - 70, int(y0 - 18)), (cx_ + 70, int(y0 + 18)), (110.0, 120.0, 235.0), -1, cv2.LINE_AA)
            cv[:] = cv * (1 - a) + ov * a
            txt(cv, label, cx_, cy_ + 92 + dy, 22, GOLD, a, path=DEJAVU, spacing=1, center=True)
        return cv

    # ------------------------------------------------------------------ e12 : Yonni Barrios, informal doctor
    def e12(self, t, cv):
        D = 5.0; L = P('doctor'); c = CROP['doctor']
        M = pcam(L, 640 - c, 360, lerp(1.0, 1.28, sstep(seg(t, 0, D))), (1.0 * math.sin(t * 0.9), 0.8 * math.sin(t * 1.3)), cx=W * 0.45)
        place(cv, L, M, gain=0.95)
        q = pt(M, 576 - c, 98 - c); lb = LightBuf(); fl = flick(t)
        lb.glow(q[0], q[1], 60, LAMP, 0.9 * fl); lb.glow(q[0], q[1], 360, (70, 130, 190), 0.55 * fl); lb.apply(cv, blur=40)
        dust_motes(cv, lb, t, 40, 18, (3, 9), up=0.3)
        a = 1 - seg(t, 4.4, 4.9); shade_bottom(cv, 250, sstep(seg(t, 0.6, 1.2)) * a)
        txt(cv, 'YONNI BARRIOS', 70, H - 330, 70, GOLD, sstep(seg(t, 0.8, 1.3)) * a, spacing=3)
        typed(cv, "THE GROUP'S INFORMAL DOCTOR", t, 3.0, 4.4, 76, H - 245, 22, (150, 205, 235), spacing=4, alpha=a)
        typed(cv, 'MEDICAL TRAINING', t, 2.0, 3.0, 76, H - 205, 18, GOLD, spacing=4, alpha=a)
        return cv

    # ------------------------------------------------------------------ e13 : Victor Segovia keeps the record
    def e13(self, t, cv):
        D = 5.2; L = P('notebook')
        M = pcam(L, 760, 330, lerp(1.0, 1.4, sstep(seg(t, 0, D))), (0.8 * math.sin(t * 0.9), 0.6 * math.sin(t * 1.3)))
        place(cv, L, M, gain=0.95)
        q = pt(M, 280, 20); lb = LightBuf(); lb.glow(q[0], q[1], 80, LAMP, 0.8 * flick(t)); lb.glow(q[0], q[1], 420, (70, 130, 190), 0.5); lb.apply(cv, blur=40)
        scribbles(cv, M, 700, 150, 990, 9, ease_out(seg(t, 2.1, 3.8)))
        tallies(cv, M, 5 * ease_out(seg(t, 3.9, 4.9)), 700, 470, gpr=3, gw=96)
        a = 1 - seg(t, 4.6, 5.1); shade_bottom(cv, 230, sstep(seg(t, 0.7, 1.2)) * a)
        txt(cv, 'VICTOR SEGOVIA', 70, H - 310, 66, GOLD, sstep(seg(t, 0.9, 1.4)) * a, spacing=3)
        typed(cv, 'KEPT A WRITTEN RECORD', t, 2.3, 3.7, 76, H - 230, 22, (150, 205, 235), spacing=4, alpha=a)
        return cv

    # ------------------------------------------------------------------ e14 : Mario Sepulveda, the morale
    def e14(self, t, cv):
        D = 9.8; L = P('sepulveda')
        z = lerp(1.0, 1.16, sstep(seg(t, 0, D))); M = pcam(L, 560, 330, z, (1.2 * math.sin(t * 0.9), 0.9 * math.sin(t * 1.3)), cx=W * 0.40)
        mood = 1.0 - 0.75 * sstep(seg(t, 3.5, 4.4)) + 0.75 * sstep(seg(t, 5.0, 6.6))   # despair then jokes
        place(cv, L, M, gain=0.30 + 0.75 * mood)
        g = cv.mean(axis=2, keepdims=True); k = 1 - mood
        cv[:] = cv * (1 - 0.7 * k) + g * 0.7 * k * np.array([1.0, 0.95, 0.9], np.float32)
        fill_rect(cv, (90, 60, 30), 0.25 * k)
        lb = LightBuf(); q = pt(M, 900, 90); lb.glow(q[0], q[1], 120, LAMP, 0.35 * mood * flick(t)); lb.apply(cv, blur=50)
        dust_motes(cv, lb, t, 40, 19, (3, 9), up=0.4)
        a = 1 - seg(t, 9.2, 9.8)
        shade_bottom(cv, 250, sstep(seg(t, 0.5, 1.0)) * a)
        txt(cv, 'MARIO SEPULVEDA', 70, H - 330, 70, GOLD, sstep(seg(t, 0.5, 1.0)) * a, spacing=3)
        typed(cv, 'THE MORALE', t, 2.0, 3.0, 76, H - 245, 24, (150, 205, 235), spacing=6, alpha=a)
        # morale meter
        ma = sstep(seg(t, 2.2, 2.7)) * a
        if ma > 0.01:
            fv = 0.15 + 0.55 * sstep(seg(t, 2.4, 3.4)) - 0.5 * sstep(seg(t, 3.7, 4.5)) + 0.85 * sstep(seg(t, 5.2, 7.0))
            bx, by, bw, bh = 76, H - 195, 360, 18
            cv2.rectangle(cv, (bx, by), (bx + bw, by + bh), (60.0 * ma, 60.0 * ma, 60.0 * ma), 2, cv2.LINE_AA)
            col = tuple(float(c) for c in np.array([60, 80, 230]) * (1 - fv) + np.array([120, 215, 170]) * fv)
            cv2.rectangle(cv, (bx + 3, by + 3), (bx + 3 + int((bw - 6) * clamp(fv)), by + bh - 3), col, -1)
            typed(cv, 'DESPAIR' if (3.8 < t < 5.2) else 'MORALE', t, 3.7 if 3.8 < t < 5.2 else 2.2, 4.6 if 3.8 < t < 5.2 else 3.0, bx, by + 30, 16, col, spacing=4, alpha=ma)
        for i, (t0, x, y, rot) in enumerate(((5.3, 880, 250, -8), (5.9, 990, 340, 7), (6.5, 800, 380, -4))):
            u = seg(t, t0, t0 + 0.25); al = sstep(u) * (1 - sstep(seg(t, t0 + 1.0, t0 + 1.5)))
            txt(cv, 'HA!', x, y - 20 * sstep(seg(t, t0, t0 + 1.4)), 80, GOLD, al, center=True, rot=rot, scale=0.6 + 0.5 * ease_out(u))
        typed(cv, 'MEN WITH FUTURES', t, 7.0, 8.8, W - 520, 90, 34, GOLD, spacing=8, alpha=a)
        return cv

    # ------------------------------------------------------------------ e15 : arguments, fights
    def e15(self, t, cv):
        D = 5.8; L = P('refuge'); c = CROP['refuge']
        crack = seg(t, 1.2, 1.5)
        bursts = [(2.4, 6), (3.0, 9), (3.7, 7), (4.2, 12), (4.5, 14)]
        sh_amp = 0.6 + sum(a * math.exp(-(t - tb) * 6) for tb, a in bursts if t >= tb)
        M = pcam(L, lerp(688, 1000, sstep(seg(t, 0.5, 3.0))), 420, lerp(1.0, 1.45, sstep(seg(t, 0, D))), shk(t, sh_amp, 4))
        place(cv, L, M, gain=0.85 - 0.25 * crack)
        q = pt(M, 688 - c, 70 - c); lb = LightBuf()
        fl = flick(t) if t < 1.3 else 0.45 + 0.55 * (0.5 + 0.5 * math.sin(t * 23))
        lb.glow(q[0], q[1], 60, LAMP, 0.9 * fl); lb.glow(q[0], q[1], 380, (70, 130, 190), 0.55 * fl); lb.apply(cv, blur=40)
        red = (0.28 + 0.18 * math.sin(t * 9)) * sstep(seg(t, 1.8, 2.4)) * (1 - sstep(seg(t, 5.0, 5.8)))
        fill_rect(cv, (30, 40, 190), max(0, red))
        if 1.2 < t < 1.45:  # glitch tear
            h0 = int(H * 0.4); cv[h0:h0 + 60] = np.roll(cv[h0:h0 + 60], 40, axis=1)
        txt(cv, "NOT ALL UNITY", W / 2, 80, 64, GOLD, sstep(seg(t, 0.3, 0.8)) * (1 - sstep(seg(t, 1.6, 2.0))), spacing=6, center=True)
        for (t0, lab, y, sc) in ((2.5, 'ARGUMENTS', 150, 1.0), (4.15, 'FIGHTS', 260, 1.3)):
            u = seg(t, t0, t0 + 0.2); al = sstep(u) * (1 - sstep(seg(t, t0 + 1.4, t0 + 1.8)))
            txt(cv, lab, W / 2, y, 100, (60, 85, 240), al, spacing=8, center=True, scale=sc * (1.6 - 0.6 * ease_out(u)), rot=-3 if lab == 'FIGHTS' else 2)
        return cv

    # ------------------------------------------------------------------ e16 : could he go on?
    def e16(self, t, cv):
        D = 5.0; L = P('gomez')
        z = lerp(1.0, 1.26, sstep(seg(t, 0, D))); M = pcam(L, 640, 330, z, (1.0 * math.sin(t * 0.9), 0.8 * math.sin(t * 1.3)))
        place(cv, L, M, gain=0.85 - 0.30 * seg(t, 0, D))
        g = cv.mean(axis=2, keepdims=True); cv[:] = cv * (1 - 0.5 * seg(t, 0, D)) + g * 0.5 * seg(t, 0, D)
        lb = LightBuf(); q = pt(M, 70, 300); lb.glow(q[0], q[1], 70, LAMP, 0.7 * flick(t)); lb.apply(cv, blur=40)
        dust_motes(cv, lb, t, 30, 20, (3, 9), up=0.4)
        vignette(cv, 0.25 + 0.55 * sstep(seg(t, 0, D)) + 0.2 * beat(t, 1.4), 1.8)
        typed(cv, 'THE PRESSURE', t, 0.2, 1.3, 56, 54, 28, GOLD, spacing=8, alpha=1 - seg(t, 1.6, 2.0))
        typed(cv, 'COULD HE GO ON?', t, 2.5, 4.0, 56, 54, 34, (150, 205, 235), spacing=8, alpha=1 - seg(t, 4.5, 5.0))
        return cv

    # ------------------------------------------------------------------ e17 : hunger
    def e17(self, t, cv):
        D = 4.8; L = P('tray')
        z = lerp(1.0, 1.35, sstep(seg(t, 0, D)))
        M = pcam(L, 640, 360, z, (1.0 * math.sin(t * 0.9), 0.8 * math.sin(t * 1.3)))
        place(cv, L, M, gain=0.75 - 0.25 * seg(t, 1.5, D))
        g = cv.mean(axis=2, keepdims=True); k = 0.5 + 0.4 * seg(t, 0, D); cv[:] = cv * (1 - k) + g * k
        gr = max(math.exp(-((t - 0.7) % 1.7) * 3) * (0.0 + 1.0), 0) if t > 0.4 else 0
        cv[:] = squeeze(cv, 0.35 * gr, cy=H * 0.5)
        vignette(cv, 0.4 + 0.45 * sstep(seg(t, 0, D)), 1.7)
        txt(cv, 'HUNGER', W / 2, 90, 120, GOLD, sstep(seg(t, 0.3, 0.9)) * (1 - sstep(seg(t, 1.8, 2.3))), spacing=14, center=True)
        typed(cv, 'THE KIND THAT CHANGES YOU', t, 3.1, 4.2, W / 2, 110, 30, (150, 205, 235), spacing=6, alpha=1 - seg(t, 4.4, 4.8), center=True)
        return cv

    # ------------------------------------------------------------------ e18 : trust
    def e18(self, t, cv):
        D = 8.4; L = P('refuge'); c = CROP['refuge']
        M = pcam(L, lerp(680, 760, sstep(seg(t, 0, D))), 440, lerp(1.0, 1.25, sstep(seg(t, 0, D))), (0.8 * math.sin(t * 0.9), 0.6 * math.sin(t * 1.3)))
        place(cv, L, M, gain=0.8)
        q = pt(M, 688 - c, 70 - c); lb = LightBuf(); fl = flick(t)
        lb.glow(q[0], q[1], 60, LAMP, 0.9 * fl); lb.glow(q[0], q[1], 380, (70, 130, 190), 0.55 * fl); lb.apply(cv, blur=40)
        dust_motes(cv, lb, t, 40, 22, (3, 9), up=0.3)
        nodes = [(200, 560), (330, 610), (150, 650), (800, 540), (900, 420), (1010, 450), (1130, 440), (1200, 520), (640, 560)]
        pts = [pt(M, x - c, y - c) for x, y in nodes]
        ea = sstep(seg(t, 3.0, 4.6)) * (0.35 + 0.65 * sstep(seg(t, 7.0, 8.0)))
        if ea > 0.01:
            ov = cv.copy(); n = len(pts)
            for i in range(n):
                for j in range(i + 1, n):
                    if (i * 7 + j * 3) % 4 == 0 or j == n - 1:
                        cv2.line(ov, (int(pts[i][0]), int(pts[i][1])), (int(pts[j][0]), int(pts[j][1])), (70.0, 165.0, 225.0), 2, cv2.LINE_AA)
            cv[:] = cv * (1 - 0.7 * ea) + ov * 0.7 * ea
            for (x, y) in pts: cv2.circle(cv, (int(x), int(y)), 7, tuple(float(k_ * ea) for k_ in (150, 215, 255)), -1, cv2.LINE_AA)
        typed(cv, 'NOBODY TAKES MORE THAN THEIR SHARE', t, 1.0, 3.2, W / 2, 54, 28, GOLD, spacing=6, alpha=1 - seg(t, 3.6, 4.0), center=True)
        txt(cv, 'TRUST', W / 2, 90, 130, GOLD, sstep(seg(t, 7.3, 7.9)), spacing=16, center=True)
        return cv

    # ------------------------------------------------------------------ e19 / helper : seventeen days of tallies
    def _tally_page(self, cv, t, n, D, label_t):
        L = P('notebook')
        M = pcam(L, 760, 330, lerp(1.0, 1.25, sstep(seg(t, 0, D))), (0.8 * math.sin(t * 0.9), 0.6 * math.sin(t * 1.3)))
        place(cv, L, M, gain=0.95)
        q = pt(M, 280, 20); lb = LightBuf(); lb.glow(q[0], q[1], 80, LAMP, 0.8 * flick(t)); lb.glow(q[0], q[1], 420, (70, 130, 190), 0.5); lb.apply(cv, blur=40)
        tallies(cv, M, n, 700, 170, gpr=3, gw=96, gh=100)
        return M

    def e19(self, t, cv):
        D = 2.6; n = 17 * ease_out(seg(t, 0.2, 1.8))
        self._tally_page(cv, t, n, D, 0)
        fill_rect(cv, (0, 0, 0), 0.35 * sstep(seg(t, 1.3, 1.9)))
        a = sstep(seg(t, 1.3, 1.8)) * (1 - sstep(seg(t, 2.3, 2.6)))
        txt(cv, str(int(n)), W / 2, 150, 220, GOLD, a, path=DEJAVU, center=True)
        txt(cv, 'DAYS', W / 2, 400, 70, GOLD, a, spacing=18, center=True)
        return cv

    # ------------------------------------------------------------------ e20 : day seventeen, something different
    def e20(self, t, cv):
        D = 4.9; L = P('ceiling')
        A = 0.08 + 0.92 * sstep(seg(t, 1.0, 4.3))
        M = pcam(L, 880, 330, lerp(1.1, 1.3, seg(t, 0, D)), shk(t, A * 8, 6))
        place(cv, L, M, gain=0.9)
        q = pt(M, 997, 158); lb = LightBuf(); fl = 1 - 0.4 * A * abs(math.sin(t * 40))
        lb.glow(q[0], q[1], 60, LAMP, 0.9 * fl); lb.glow(q[0], q[1], 360, (70, 130, 190), 0.55 * fl); lb.apply(cv, blur=40)
        dust_motes(cv, lb, t, 40, 23, (3, 9), up=-0.5)
        sift(cv, t, A, 9)
        wave(cv, t, 12 + 55 * A, H - 190, sstep(seg(t, 0.5, 1.0)), freq=1.0 + 1.3 * A)
        txt(cv, 'DAY 17', W / 2, 90, 120, GOLD, sstep(seg(t, 0.0, 0.5)) * (1 - sstep(seg(t, 2.0, 2.6))), spacing=12, center=True)
        return cv

    # ------------------------------------------------------------------ e21 : the bit punctures the rock
    def e21(self, t, cv):
        D = 4.5; T_P = 2.8
        if t < T_P:
            L = P('ceiling'); A = 0.7 + 0.5 * sstep(seg(t, 0, T_P))
            M = pcam(L, 880, 330, lerp(1.3, 1.5, seg(t, 0, T_P)), shk(t, A * 11, 7))
            place(cv, L, M, gain=0.9)
            q = pt(M, 997, 158); lb = LightBuf(); fl = 1 - 0.5 * abs(math.sin(t * 40))
            lb.glow(q[0], q[1], 60, LAMP, 0.9 * fl); lb.glow(q[0], q[1], 360, (70, 130, 190), 0.55 * fl); lb.apply(cv, blur=40)
            sift(cv, t, 1.0, 11)
            wave(cv, t, 70, H - 190, 1.0, freq=2.3)
            fill_rect(cv, (200, 215, 230), 0.12 * sstep(seg(t, 2.2, T_P)))
        else:
            u = t - T_P; L = P('drillbit')
            z = lerp(1.7, 1.0, ease_out(u / 0.7))
            M = pcam(L, 700, 380, z, shk(t, 14 * math.exp(-u * 3.5), 8))
            place(cv, L, M, gain=0.95)
            tip = pt(M, 677, 523); lb = LightBuf(); lb.glow(tip[0], tip[1], 40, (200, 240, 255), 0.9); lb.beam(tip[0], tip[1] - 280, 90, 380, 14, (200, 225, 245), 0.35)
            q = pt(M, 502, 172); lb.glow(q[0], q[1], 70, LAMP, 0.8 * flick(t)); lb.apply(cv, blur=24)
            puffs(cv, t, T_P, T_P + 1.2, 26, (tip[0] - 160, tip[1] - 120, 320, 120), (90, 125, 150), seed=30, size=(120, 280), alpha=0.55, life=2.6, rise=(-40, 20), spread=(200, 400), grow=2.6)
            sift(cv, t, max(0.0, 1 - u * 0.3), 12)
            fill_rect(cv, (235, 240, 245), 0.9 * max(0, 1 - u / 0.22))
        return cv

    # ------------------------------------------------------------------ e22 : they rush to it, bang, shout
    def e22(self, t, cv):
        D = 3.0; L = P('drillbit')
        bangs = [(1.3, 9), (1.6, 9), (1.9, 9)]
        sh_amp = 1.2 + sum(a * math.exp(-(t - tb) * 7) for tb, a in bangs if t >= tb)
        M = pcam(L, 700, 380, lerp(1.0, 1.18, sstep(seg(t, 0, D))), shk(t, sh_amp, 9))
        place(cv, L, M, gain=0.95)
        tip = pt(M, 677, 523); lb = LightBuf(); lb.glow(tip[0], tip[1], 40, (200, 240, 255), 0.9); lb.beam(tip[0], tip[1] - 280, 90, 380, 14, (200, 225, 245), 0.35)
        q = pt(M, 502, 172); lb.glow(q[0], q[1], 70, LAMP, 0.8 * flick(t)); lb.apply(cv, blur=24)
        for tb, a in bangs:
            if tb <= t < tb + 0.12: fill_rect(cv, (225, 235, 245), 0.18)
        for tb, _ in bangs:   # shock rings from the bit
            u = (t - tb) / 0.5
            if 0 <= u < 1:
                cv2.circle(cv, (int(tip[0]), int(tip[1] - 40)), int(40 + 380 * ease_out(u)), (200.0 * (1 - u), 225.0 * (1 - u), 245.0 * (1 - u)), 3, cv2.LINE_AA)
        sift(cv, t, 0.5, 13)
        return cv

    # ------------------------------------------------------------------ e23 : the note goes up
    def e23(self, t, cv):
        D = 6.1; L = P('drillbit')
        z = lerp(1.0, 1.5, sstep(seg(t, 0, 2.2))); fy = lerp(300, 190, sstep(seg(t, 0, 2.2)))
        fy = lerp(fy, 20, ease_in(seg(t, 3.4, 6.0))); fx = lerp(700, 755, sstep(seg(t, 0, 2.2)))
        M = pcam(L, fx, fy, z, (0.8 * math.sin(t * 1.2), 0.8 * math.sin(t * 1.5)))
        place(cv, L, M, gain=0.95)
        q = pt(M, 502, 172); lb = LightBuf(); lb.glow(q[0], q[1], 70, LAMP, 0.7 * flick(t)); lb.glow(q[0], q[1], 400, (70, 130, 190), 0.4)
        nq = pt(M, 755, 190); lb.glow(nq[0], nq[1], 120 * z * 0.5, (160, 210, 250), 0.25); lb.apply(cv, blur=30)
        dust_motes(cv, lb, t, 40, 24, (3, 9), up=0.5)
        sift(cv, t, 0.15, 14, chunks=False)
        return cv
