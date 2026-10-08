"""Part 5 shots: the note comes up, the country erupts, but 33 men are still 2,300 feet down."""
import cv2, math, numpy as np
from engine import *
from scenes_e import *
import scenes_e
HAND = 'assets/ReenieBeanie.ttf'
INK = (35.0, 35.0, 175.0)


def P5(n): return get_layer('p5_' + n)


_hc = {}
def hand_text(cv, M, s, x, y, size, prog, color=INK, alpha=0.92):
    """handwritten red ink, revealed left-to-right; (x, y) in plate space, drawn through plate matrix M (rotation baked in M)"""
    if prog <= 0.001: return
    key = (s, size)
    if key not in _hc:
        f = font(size, HAND); tw = int(f.getlength(s)) + 30; th = int(size * 1.6)
        im = Image.new('L', (tw, th), 0); ImageDraw.Draw(im).text((12, 4), s, font=f, fill=255)
        a = np.asarray(im, np.float32) / 255; a = cv2.GaussianBlur(a, (0, 0), 0.8) * 1.15
        out = np.zeros(a.shape + (4,), np.float32); out[..., :3] = np.array(color, np.float32) * np.clip(a, 0, 1)[..., None]; out[..., 3] = np.clip(a, 0, 1) * 0.95
        _hc[key] = out
    arr = _hc[key]; w = max(2, int(arr.shape[1] * clamp(prog)))
    lay = Layer.from_array(arr[:, :w])
    place(cv, lay, M @ M3(x, y, 1, 1, 0, 0, 0), alpha=alpha)


def flash(cv, a, col=(240, 245, 250)): fill_rect(cv, col, clamp(a))


def snow(cv, t, n=90, seed=3, speed=(40, 90), alpha=0.8):
    r = rng(seed)
    for i in range(n):
        x = (r.random() * W + 18 * math.sin(t * 0.8 + i)) % W; y = (r.random() * H + t * (speed[0] + (speed[1] - speed[0]) * r.random())) % H
        cv2.circle(cv, (int(x), int(y)), 1 + int(r.random() * 2), (235.0 * alpha, 240.0 * alpha, 245.0 * alpha), -1, cv2.LINE_AA)


class ScenesF:
    # ------------------------------------------------------------------ f1 : the drill comes back up
    def f1(self, t, cv):
        D = 5.6; L = P5('pull')
        z = lerp(1.0, 1.4, sstep(seg(t, 0, D))); fx = lerp(688, 731, sstep(seg(t, 0, D))); fy = lerp(384, 480, sstep(seg(t, 0, D)))
        sh = shk(t, 1.0 + 1.6 * sstep(seg(t, 0.8, 2.2)) * (1 - sstep(seg(t, 3.8, 5.0))), 4)
        M = pcam(L, fx, fy, z, sh)
        place(cv, L, M, gain=0.95)
        lb = LightBuf()
        for (x, y, ph) in ((129, 96, 0), (1268, 85, 2), (677, 181, 4)):
            q = pt(M, x, y); lb.glow(q[0], q[1], 40, (200, 230, 255), 0.7 * (0.85 + 0.15 * math.sin(t * 8 + ph))); lb.glow(q[0], q[1], 170, (110, 160, 200), 0.3)
        q = pt(M, 204, 128); lb.glow(q[0], q[1], 200, (80, 150, 230), 0.55); lb.apply(cv, blur=26)
        bs = pt(M, 731, 640)
        puffs(cv, t, 0, D, 36, (bs[0] - 120, bs[1] - 60, 240, 80), (95, 135, 170), seed=51, size=(120, 280), alpha=0.45, life=2.8, rise=(10, 60), spread=(200, 360), grow=2.4)
        dust_motes(cv, lb, t, 60, 31, (20, 50), up=0.5)
        typed(cv, 'DAY 17', t, 0.1, 0.8, 56, 54, 34, GOLD, spacing=8, alpha=1 - seg(t, 4.8, 5.4))
        typed(cv, 'ON THE SURFACE', t, 0.6, 1.8, 56, 100, 26, (150, 205, 235), spacing=6, alpha=1 - seg(t, 4.8, 5.4))
        return cv

    # ------------------------------------------------------------------ f2 : something is tied to the bit
    def f2(self, t, cv):
        D = 4.4; L = P('drillbit')
        z = lerp(1.0, 1.8, sstep(seg(t, 0.2, D))); fx = lerp(700, 775, sstep(seg(t, 0.2, D))); fy = lerp(380, 215, sstep(seg(t, 0.2, D)))
        M = pcam(L, fx, fy, z, (0.8 * math.sin(t * 1.2), 0.8 * math.sin(t * 1.5)))
        place(cv, L, M, gain=0.95)
        q = pt(M, 502, 172); lb = LightBuf(); lb.glow(q[0], q[1], 70, LAMP, 0.7 * flick(t)); lb.glow(q[0], q[1], 400, (70, 130, 190), 0.4)
        nq = pt(M, 775, 215); pu = 0.5 + 0.5 * math.sin(t * 3.2); lb.glow(nq[0], nq[1], 90 * z * 0.6, (170, 215, 250), 0.18 + 0.12 * pu * sstep(seg(t, 2.0, 3.0))); lb.apply(cv, blur=30)
        puffs(cv, t, 0, 3.0, 14, (0, 560, W, 120), (90, 125, 150), seed=60, size=(120, 260), alpha=0.25, life=3.0, rise=(0, 14), spread=(100, 260))
        dust_motes(cv, lb, t, 40, 24, (3, 9), up=0.5)
        typed(cv, 'TIED TO THE BIT', t, 0.9, 2.2, 56, 54, 28, GOLD, spacing=8, alpha=1 - seg(t, 3.7, 4.2))
        return cv

    # ------------------------------------------------------------------ f3 : the note, red ink
    NOTE_C = (690, 385); NOTE_ROT = 2.0

    def _note(self, cv, t, z, fx, fy, tmain=0.0, sh=(0, 0)):
        L = P5('note'); M = pcam(L, fx, fy, z, sh)
        place(cv, L, M, gain=0.95)
        lb = LightBuf(); q = pt(M, 1230, 40); lb.glow(q[0], q[1], 60, LAMP, 0.9 * flick(t)); lb.glow(q[0], q[1], 420, (70, 130, 190), 0.5)
        nq = pt(M, *self.NOTE_C); lb.glow(nq[0], nq[1], 260 * z, (150, 190, 230), 0.12); lb.apply(cv, blur=36)
        return M

    def f3(self, t, cv):
        D = 6.6
        M = self._note(cv, t, lerp(1.0, 1.3, sstep(seg(t, 0, D))), 690, 385, sh=(0.8 * math.sin(t * 0.9), 0.8 * math.sin(t * 1.3)))
        R = M @ M3(self.NOTE_C[0], self.NOTE_C[1], 1, 1, self.NOTE_ROT, self.NOTE_C[0], self.NOTE_C[1])
        hand_text(cv, R, 'Estamos bien', 575, 262, 54, ease_out(seg(t, 3.25, 3.85)))
        hand_text(cv, R, 'en el refugio,', 560, 322, 54, ease_out(seg(t, 3.75, 4.35)))
        hand_text(cv, R, 'los 33.', 620, 385, 74, ease_out(seg(t, 4.9, 5.5)))
        dust_motes(cv, LightBuf(), t, 0, 1)
        typed(cv, 'HANDWRITTEN IN RED INK', t, 0.2, 1.8, 56, 54, 26, (80.0, 80.0, 235.0), spacing=6, alpha=1 - seg(t, 2.2, 2.6))
        typed(cv, 'IT SAID:', t, 2.2, 2.9, 56, 54, 34, GOLD, spacing=10, alpha=1 - seg(t, 6.0, 6.5))
        return cv

    # ------------------------------------------------------------------ f4 : the 33, counted
    def f4(self, t, cv):
        D = 3.8; L = P5('alive')
        place(cv, L, pcam(L, 688, 384, lerp(1.0, 1.1, seg(t, 0, D))), gain=0.5)
        n = int(33 * ease_out(seg(t, 0.4, 3.2))); lb = LightBuf()
        cols = 11; x0 = W / 2 - 5 * 52; y0 = 300
        for i in range(n):
            u = seg(t, 0.4 + 2.8 * (1 - (1 - i / 33) ** (1 / 2.2)) if False else 0.4, 3.4)
            cx_ = x0 + (i % cols) * 52; cy_ = y0 + (i // cols) * 52
            lb.glow(cx_, cy_, 10, (150, 215, 255), 0.9)
        lb.apply(cv, blur=10)
        for i in range(n):
            cx_ = x0 + (i % cols) * 52; cy_ = y0 + (i // cols) * 52
            cv2.circle(cv, (int(cx_), int(cy_)), 8, (200.0, 235.0, 255.0), -1, cv2.LINE_AA)
        txt(cv, str(n) if n < 33 else '33', W / 2, 110, 150, GOLD, sstep(seg(t, 0.3, 0.8)), path=None, center=True, spacing=6)
        typed(cv, 'ALL ALIVE. ALL WELL.', t, 2.2, 3.3, W / 2, 470, 28, (150, 205, 235), spacing=8, center=True, alpha=1 - seg(t, 3.5, 3.9))
        return cv

    # ------------------------------------------------------------------ f5 : imagine reading those words
    def f5(self, t, cv):
        D = 2.4
        M = self._note(cv, t, lerp(1.3, 1.55, sstep(seg(t, 0, D))), 690, 385, sh=(0.6 * math.sin(t * 0.9), 0.6 * math.sin(t * 1.3)))
        R = M @ M3(self.NOTE_C[0], self.NOTE_C[1], 1, 1, self.NOTE_ROT, self.NOTE_C[0], self.NOTE_C[1])
        for (s, x, y, sz) in (('Estamos bien', 575, 262, 54), ('en el refugio,', 560, 322, 54), ('los 33.', 620, 385, 74)): hand_text(cv, R, s, x, y, sz, 1.0)
        vignette(cv, 0.35 + 0.1 * math.sin(t * 2), 1.8)
        return cv

    # ------------------------------------------------------------------ f6 : seventeen days of silence
    def f6(self, t, cv):
        D = 4.8; L = P5('nation')
        M = pcam(L, 700, 500, lerp(1.0, 1.25, sstep(seg(t, 0, D))) + 0.006 * math.sin(t * 1.0), (0.8 * math.sin(t * 0.9), 0.6 * math.sin(t * 1.3)))
        place(cv, L, M, gain=0.9)
        lb = LightBuf(); q = pt(M, 839, 587); fl = 0.8 + 0.2 * math.sin(t * 13) * math.sin(t * 3)
        lb.glow(q[0], q[1], 70, (210, 225, 240), 0.8 * fl); lb.glow(q[0], q[1], 330, (150, 175, 200), 0.4 * fl); lb.apply(cv, blur=36)
        dust_motes(cv, lb, t, 30, 33, (2, 6), up=0.2)
        vignette(cv, 0.25 + 0.3 * sstep(seg(t, 0, D)), 1.8)
        # flat-line of silence
        xs = np.arange(150, W - 150, 4); ys = (H - 190 + 1.2 * np.sin(xs * 0.3 + t * 5)).astype(np.int32)
        ov = cv.copy(); cv2.polylines(ov, [np.stack([xs, ys], 1)], False, (70.0, 165.0, 225.0), 2, cv2.LINE_AA)
        a = sstep(seg(t, 0.3, 0.8)) * (1 - sstep(seg(t, 4.2, 4.7))); cv[:] = cv * (1 - 0.8 * a) + ov * 0.8 * a
        n = int(clamp((t - 0.9) / 1.5) * 17) if t > 0.9 else 0
        typed(cv, 'DAYS OF SILENCE', t, 0.4, 1.8, 56, 54, 28, GOLD, spacing=8, alpha=1 - seg(t, 4.2, 4.7))
        if n > 0:
            txt(cv, f'{n}', W - 190, 40, 130, GOLD, 1 - seg(t, 4.2, 4.7), path=None, center=False, spacing=4)
        return cv

    # ------------------------------------------------------------------ f7 : Pinera tells the world
    def f7(self, t, cv):
        D = 3.6; L = P5('pinera')
        M = pcam(L, 740, 380, lerp(1.0, 1.22, sstep(seg(t, 0, D))), (0.8 * math.sin(t * 0.9), 0.6 * math.sin(t * 1.3)))
        place(cv, L, M, gain=0.95)
        lb = LightBuf(); r = rng(70)
        fls = [(183, 309), (441, 448), (1172, 416), (1247, 341), (300, 260), (1100, 520)]
        for k, (x, y) in enumerate(fls):
            ph = (t * (2.2 + 0.7 * k) + k * 0.37) % 1.0; a = math.exp(-ph * 9)
            q = pt(M, x - 26, y - 26); lb.glow(q[0], q[1], 34, (255, 255, 255), 1.1 * a); lb.glow(q[0], q[1], 120, (200, 220, 240), 0.5 * a)
        lb.apply(cv, blur=22)
        mq = pt(M, 731 - 26, 352 - 26)
        for k in range(4):
            u = ((t - 1.0) / 1.9 + k * 0.25) % 1.0
            if t > 1.0: cv2.circle(cv, (int(mq[0]), int(mq[1])), int(30 + 700 * u), (tuple(float(c * (1 - u) * sstep(seg(t, 1.0, 1.4))) for c in GOLD)), 3, cv2.LINE_AA)
        a = 1 - seg(t, 3.0, 3.5); shade_bottom(cv, 250, sstep(seg(t, 0.4, 0.9)) * a)
        txt(cv, 'SEBASTIAN PINERA', 70, H - 335, 66, GOLD, sstep(seg(t, 0.5, 1.0)) * a, spacing=3)
        typed(cv, 'PRESIDENT OF CHILE', t, 1.1, 2.1, 76, H - 250, 22, (150, 205, 235), spacing=5, alpha=a)
        la = sstep(seg(t, 1.0, 1.3)) * a; blink = 0.4 + 0.6 * (math.sin(t * 6) > 0)
        cv2.circle(cv, (W - 150, 62), 10, (50.0 * la * blink, 60.0 * la * blink, 235.0 * la * blink), -1, cv2.LINE_AA)
        typed(cv, 'LIVE', t, 1.0, 1.4, W - 125, 48, 28, (80.0, 90.0, 240.0), spacing=5, alpha=la)
        return cv

    # ------------------------------------------------------------------ f8 : the camp erupts
    def f8(self, t, cv):
        D = 6.6; L = P5('joy')
        bumps = [0.6, 1.1, 1.7, 2.3]; amp = 1.0 + sum(7 * math.exp(-(t - b) * 5) for b in bumps if t >= b)
        z = lerp(1.0, 1.28, sstep(seg(t, 0, D))) + 0.02 * sum(math.exp(-(t - b) * 6) for b in bumps if t >= b)
        M = pcam(L, lerp(700, 900, sstep(seg(t, 0, D))), 400, z, shk(t, amp, 5))
        place(cv, L, M, gain=0.95)
        lb = LightBuf(); r = rng(81)
        for i in range(16):
            x = 100 + 80 * i; y = 560 + 40 * math.sin(i * 1.7); q = pt(M, x, y)
            lb.glow(q[0], q[1], 24, (100, 175, 255), 0.35 * (0.7 + 0.3 * math.sin(t * (7 + i) + i))); 
        lb.glow(W * 0.5, H * 0.55, 400, (60, 120, 200), 0.2 + 0.15 * sstep(seg(t, 0.4, 1.2)))
        lb.apply(cv, blur=28)
        for i in range(60):   # sparks / confetti rising
            x0 = r.random() * W; sp = 40 + 110 * r.random(); ph = r.random() * 8
            y = H + 20 - ((t - 0.4) * sp + ph * 60) % (H + 40) if t > 0.4 else -50
            a = 0.5 + 0.5 * math.sin(t * 5 + i); c = (60 + 190 * r.random(), 170 + 70 * r.random(), 255.0)
            cv2.circle(cv, (int(x0 + 25 * math.sin(t * 1.3 + ph)), int(y)), 2, tuple(float(k * a) for k in c), -1, cv2.LINE_AA)
        a = 1 - seg(t, 5.6, 6.2)
        sh_ = np.linspace(1, 0, 260, dtype=np.float32)[:, None, None] ** 1.4 * 0.65 * (sstep(seg(t, 0.4, 0.8)) * (1 - sstep(seg(t, 2.6, 3.0))) + sstep(seg(t, 3.8, 4.1)) * a)
        cv[:260] *= (1 - sh_)
        typed(cv, 'ABOVE GROUND', t, 0.1, 1.0, 56, 54, 26, (150, 205, 235), spacing=8, alpha=1 - seg(t, 1.0, 1.4))
        u = seg(t, 0.55, 0.8); txt(cv, 'ERUPTED', W / 2, 150, 130, GOLD, sstep(u) * (1 - sstep(seg(t, 2.5, 3.0))), spacing=14, center=True, scale=1.5 - 0.5 * ease_out(u))
        for (t0, w_, x, y, rot) in ((4.0, 'CRIED', 330, 190, -5), (4.6, 'SCREAMED', 700, 150, 3), (5.05, 'EMBRACED', 960, 240, -3)):
            u = seg(t, t0, t0 + 0.25)
            txt(cv, w_, x, y, 72, GOLD, sstep(u) * a, spacing=5, center=True, rot=rot, scale=1.4 - 0.4 * ease_out(u))
        return cv

    # ------------------------------------------------------------------ f9 : reality sets in
    def f9(self, t, cv):
        D = 5.4; L = P5('alive')
        cold = sstep(seg(t, 0.2, 1.4)) * (1 - 0.8 * sstep(seg(t, 3.0, 3.6)))
        M = pcam(L, 688, 400, lerp(1.0, 1.25, sstep(seg(t, 0, D))), (0.8 * math.sin(t * 0.9), 0.6 * math.sin(t * 1.3)))
        place(cv, L, M, gain=lerp(1.0, 0.7, cold))
        g = cv.mean(axis=2, keepdims=True); cv[:] = cv * (1 - 0.55 * cold) + g * 0.55 * cold * np.array([1.12, 1.0, 0.85], np.float32)
        lb = LightBuf(); q = pt(M, 688, 40); lb.glow(q[0], q[1], 50, (200, 225, 245), 0.8); lb.beam(q[0], q[1], 90, 560, 11, (190, 215, 240), 0.35 + 0.1 * math.sin(t * 2))
        warm = sstep(seg(t, 2.9, 3.4)); lb.glow(W / 2, 430, 380, (70, 140, 210), 0.4 * warm); lb.apply(cv, blur=26)
        dust_motes(cv, lb, t, 60, 41, (2, 6), up=0.4, bright=1.4)
        vignette(cv, 0.2 + 0.35 * cold * (1 - warm * 0.6) + 0.1 * beat(t, 1.3), 1.9)
        typed(cv, 'BUT THEN REALITY SET IN', t, 0.3, 1.9, 56, 54, 28, (150, 195, 235), spacing=8, alpha=1 - seg(t, 2.6, 3.0))
        txt(cv, 'ALIVE', W / 2, 90, 130, GOLD, sstep(seg(t, 3.0, 3.5)) * (1 - seg(t, 4.8, 5.3)), spacing=18, center=True)
        return cv

    # ------------------------------------------------------------------ f10 : 2,300 feet down, and how to get them out?
    def f10(self, t, cv):
        D = 9.8; WORLD_H = 1560; CH_Y = 1500
        desc = ease_out(seg(t, 1.3, 5.3)) if False else sstep(seg(t, 1.3, 5.4))
        camY = lerp(-170, CH_Y - 420, desc)
        # background rock (scrolling) + sky
        tex = ScenesE()._rock_tex(); off = int(camY) % (2 * H)
        cv[:] = np.vstack([tex, tex[::-1], tex])[off:off + H] * 0.8
        sy = int(0 - camY)   # screen y of the surface
        if sy > 0:
            sky = np.linspace(46, 14, max(1, sy), dtype=np.float32)[:, None, None] * np.array([1.25, 1.0, 0.8], np.float32); cv[:min(sy, H)] = sky[:min(sy, H)] + 10
        xs = np.arange(0, W + 20, 20); ys = sy + 6 * np.sin(xs * 0.03) + 4 * np.sin(xs * 0.11)
        if sy > -40:
            poly = np.concatenate([np.stack([xs, ys], 1), [[W + 20, -400], [0, -400]]]).astype(np.int32)
            cv2.fillPoly(cv, [poly], (34.0, 30.0, 28.0), cv2.LINE_AA); cv2.polylines(cv, [np.stack([xs, ys], 1).astype(np.int32)], False, (90.0, 150.0, 200.0), 2, cv2.LINE_AA)
            # rig
            rx = W / 2 + 250; cv2.line(cv, (int(rx - 28), sy), (int(rx), sy - 120), (140.0, 150.0, 160.0), 3, cv2.LINE_AA); cv2.line(cv, (int(rx + 28), sy), (int(rx), sy - 120), (140.0, 150.0, 160.0), 3, cv2.LINE_AA)
            cv2.line(cv, (int(rx - 18), sy - 60), (int(rx + 18), sy - 60), (140.0, 150.0, 160.0), 2, cv2.LINE_AA)
        cx = W / 2 - 40
        # shaft
        y0 = max(0, sy); y1 = int(CH_Y - camY)
        cv2.line(cv, (int(cx), y0), (int(cx), min(H, y1)), (60.0, 110.0, 150.0), 4, cv2.LINE_AA)
        # chamber
        cy = CH_Y - camY
        if cy < H + 120:
            lb = LightBuf(); pul = 0.8 + 0.2 * math.sin(t * 3); lb.glow(cx, cy, 120, LAMP, 0.7 * pul); lb.glow(cx, cy, 320, (60, 110, 170), 0.35); lb.apply(cv, blur=30)
            cv2.rectangle(cv, (int(cx - 90), int(cy - 32)), (int(cx + 90), int(cy + 32)), (20.0, 40.0, 70.0), -1)
            cv2.rectangle(cv, (int(cx - 90), int(cy - 32)), (int(cx + 90), int(cy + 32)), (110.0, 190.0, 255.0), 2, cv2.LINE_AA)
            for i in range(33): cv2.circle(cv, (int(cx - 80 + (i % 11) * 16), int(cy - 16 + (i // 11) * 16)), 3, (180.0, 230.0, 255.0), -1, cv2.LINE_AA)
        # ruler
        rx0 = 190
        cv2.line(cv, (rx0, max(0, sy)), (rx0, H), (150.0, 190.0, 220.0), 2, cv2.LINE_AA)
        for ft in range(0, 2400, 100):
            yy = int(ft * CH_Y / 2300 - camY)
            if 0 <= yy < H:
                big = ft % 500 == 0; cv2.line(cv, (rx0 - (18 if big else 9), yy), (rx0, yy), (150.0, 190.0, 220.0), 2, cv2.LINE_AA)
                if big: txt(cv, f'{ft}', rx0 - 78, yy - 13, 18, (160, 200, 230), 1.0, path=DEJAVU)
        # counter
        ft_now = int(2300 * clamp((camY + 170) / (CH_Y - 420 + 170)) ** 1.0)
        cur = int(clamp((t - 1.5) / 3.7) ** 0.9 * 2300) if t > 1.5 else 0
        a = sstep(seg(t, 1.2, 1.7)) * (1 - sstep(seg(t, 8.8, 9.4)))
        if a > 0.01:
            panel(cv, W - 400, 80, W - 40, 250, 0.6 * a, GOLD, 0.8 * a)
            txt(cv, f'{cur:,}', W - 360, 92, 96, GOLD, a, path=None)
            typed(cv, 'FEET  (700 M)', t, 1.3, 2.3, W - 355, 205, 22, (150, 205, 235), spacing=6, alpha=a)
        typed(cv, 'TRAPPED BELOW', t, 0.4, 1.5, 56, 54, 26, GOLD, spacing=8, alpha=1 - seg(t, 3.6, 4.2))
        # the problem
        qa = sstep(seg(t, 5.6, 6.0)) * (1 - sstep(seg(t, 9.0, 9.6)))
        if qa > 0.01:
            pr = seg(t, 6.4, 8.2); cx2 = int(cx + 4)
            top = int(lerp(cy - 36, max(60, -camY + 40), ease_in(pr) if False else sstep(pr)))
            for k in range(int(cy - 40), top, -22):
                if k > 0: cv2.line(cv, (cx2 + 24, k), (cx2 + 24, max(top, k - 11)), (tuple(float(c * qa) for c in (90, 215, 255))), 4, cv2.LINE_AA)
            if pr > 0.97: cv2.fillConvexPoly(cv, np.array([[cx2 + 8, top + 2], [cx2 + 40, top + 2], [cx2 + 24, top - 24]], np.int32), (tuple(float(c * qa) for c in (90, 215, 255))), cv2.LINE_AA)
            sc = 1 + 0.08 * math.sin(t * 5)
            txt(cv, '?', cx + 210, cy - 110, 200, (55, 85, 240), qa, path=DEJAVU, center=True, scale=sc)
            typed(cv, 'A DIFFERENT PROBLEM', t, 6.8, 8.4, W - 520, 440, 26, (80.0, 100.0, 240.0), spacing=6, alpha=qa)
        return cv

    # ------------------------------------------------------------------ f11 : engineers, months
    def f11(self, t, cv):
        D = 3.0; L = P5('engineers')
        M = pcam(L, 688, 440, lerp(1.0, 1.2, sstep(seg(t, 0, D))), (0.8 * math.sin(t * 0.9), 0.6 * math.sin(t * 1.3)))
        place(cv, L, M, gain=0.95)
        q = pt(M, 660, 40); lb = LightBuf(); sw = 0.9 + 0.1 * math.sin(t * 2.0)
        lb.glow(q[0], q[1], 60, LAMP, 0.9 * sw); lb.glow(q[0], q[1], 420, (70, 130, 190), 0.55 * sw); lb.apply(cv, blur=40)
        dust_motes(cv, lb, t, 40, 51, (2, 6), up=0.3)
        vignette(cv, 0.3 * sstep(seg(t, 0.5, D)), 1.8)
        typed(cv, 'ENGINEERS ESTIMATED', t, 0.1, 1.1, 56, 54, 26, GOLD, spacing=8, alpha=1 - seg(t, 2.5, 3.0))
        txt(cv, 'MONTHS?', W / 2, 120, 130, GOLD, sstep(seg(t, 1.5, 2.0)), spacing=14, center=True)
        return cv

    # ------------------------------------------------------------------ f12 : the calendar, Christmas
    def f12(self, t, cv):
        D = 3.9
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        cv[:] = np.array([22, 28, 36], np.float32) * (0.6 + 0.6 * yy) + 0
        lb = LightBuf(); lb.glow(W / 2 - 150, 330, 380, (70, 130, 190), 0.35 + 0.05 * math.sin(t * 2)); lb.apply(cv, blur=60)
        cx, cy, w_, h_ = W // 2 - 150, 300, 420, 470
        months = ['OCTOBER', 'NOVEMBER', 'DECEMBER']; day = ['DAY 18', '', '']
        idx = 0 if t < 0.5 else (1 if t < 1.05 else 2)
        # flip squash around change times
        flip = max(math.exp(-abs(t - 0.5) * 9), math.exp(-abs(t - 1.05) * 9))
        sy_ = 1 - 0.7 * flip
        top = int(cy - h_ / 2 * sy_); bot = int(cy + h_ / 2 * sy_)
        ov = cv.copy(); cv2.rectangle(ov, (cx - w_ // 2, top), (cx + w_ // 2, bot), (230.0, 235.0, 240.0), -1)
        cv[:] = cv * (1 - 0.95 * sstep(seg(t, 0, 0.3))) + ov * 0.95 * sstep(seg(t, 0, 0.3))
        a = sstep(seg(t, 0, 0.3))
        hdr = (60.0, 60.0, 200.0) if idx == 2 else (70.0, 70.0, 150.0)
        cv2.rectangle(cv, (cx - w_ // 2, top), (cx + w_ // 2, top + int(80 * sy_)), tuple(c * a + 20 * (1 - a) for c in hdr), -1)
        txt(cv, months[idx], cx, top + 40 * sy_, 54, (235, 240, 245), a, spacing=6, center=True, scale=sy_)
        # day grid
        for d in range(1, 32):
            gx = cx - w_ // 2 + 30 + ((d - 1) % 7) * 54; gy = top + int((120 + ((d - 1) // 7) * 66) * sy_)
            txt(cv, str(d), gx - 4, gy - 24 * sy_, 22, (70, 70, 80), a, path=DEJAVU, scale=0.3 + 0.7 * sy_)
        if idx == 2:
            gx = cx - w_ // 2 + 30 + 24 * 54 // 7 * 0; d = 25; gx = cx - w_ // 2 + 30 + ((d - 1) % 7) * 54 + 12; gy = top + int((120 + ((d - 1) // 7) * 66) * sy_) - 9
            r_ = int(30 * ease_out(seg(t, 1.5, 1.9)))
            if r_ > 2: cv2.circle(cv, (gx, gy), r_, (40.0, 50.0, 220.0), 4, cv2.LINE_AA)
            typed(cv, 'CHRISTMAS?', t, 1.8, 2.8, cx - 100, cy + h_ / 2 + 24, 30, (110.0, 215.0, 250.0), spacing=8, alpha=1 - seg(t, 3.4, 3.8))
        # tree
        ta = sstep(seg(t, 1.7, 2.3)); tx, ty = W // 2 + 330, 380
        if ta > 0.02:
            ov = cv.copy()
            for k, (wd, y_) in enumerate(((110, 0), (150, 55), (190, 115))):
                pts = np.array([[tx, ty - 120 + y_], [tx - wd / 2, ty - 50 + y_], [tx + wd / 2, ty - 50 + y_]], np.int32)
                cv2.fillConvexPoly(ov, pts, (60.0, 130.0, 50.0), cv2.LINE_AA)
            cv2.rectangle(ov, (tx - 12, ty + 70), (tx + 12, ty + 100), (30.0, 60.0, 90.0), -1)
            r = rng(9)
            for i in range(9): cv2.circle(ov, (int(tx + (r.random() - .5) * 120), int(ty - 60 + r.random() * 160)), 4, (80.0 + 0 * i, 180.0, 255.0 * (0.6 + 0.4 * math.sin(t * 5 + i))), -1, cv2.LINE_AA)
            cv[:] = cv * (1 - ta) + ov * ta
            sun_icon(cv, tx, ty - 134, 10, (90, 220, 255), ta)
        snow(cv, t, 80, 5, alpha=sstep(seg(t, 1.5, 2.5)))
        return cv
