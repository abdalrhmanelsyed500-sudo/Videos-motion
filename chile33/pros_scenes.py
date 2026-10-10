"""Prosperi video (Arabic, ~31.2 s): the Sahara sandstorm, Mauro Prosperi alone, walking away from the course, crossing a border without knowing.
Same oil-painting layered-puppet system. USER DECISION: NO black eye bar and NO B&W face circle in this video and the next ones (HK.FACE_MARK = False; HK.BARE_ARMS.update(('p', 'r'))).
No captions, no music."""
from part8_scenes import *
import hook_scenes as HK
HK.FACE_MARK = False; HK.BARE_ARMS.update(('p', 'r'))
for _k in 'pr': HK.RIG[_k] = HK.RIG['m']

DP = 31.2
PW, PH = 1584, 672
SC0 = 720.0 / 672.0      # plate scale at zoom 1
SAND = (96.0, 160.0, 214.0)   # BGR sand colour
RSH = [None, (1.3, 0.95, 0.8), (0.8, 1.0, 1.1), (1.6, 0.8, 0.7), (0.9, 0.9, 0.9), (1.2, 0.72, 0.65)]
RPT = [None, None, None, None, None, None]


class WC:
    """wide-plate camera: centre point of the plate (px,py) at screen centre, zoom z."""
    def __init__(self, px, py, z=1.0, gain=1.0):
        self.s = SC0 * z; self.z = z; self.gain = gain
        self.px = clamp(px, 640 / self.s, PW - 640 / self.s); self.py = clamp(py, 360 / self.s, PH - 360 / self.s)

    def pt(self, X, Y): return 640 + (X - self.px) * self.s, 360 + (Y - self.py) * self.s

    def draw(self, cv, name, gain=None):
        place(cv, L(name), M3(640, 360, self.s, self.s, 0, self.px, self.py), gain=self.gain if gain is None else gain)

    def sc(self, Y, base=1.0):   # character scale from plate depth (Y plate coords): horizon ~ 400
        return base * (0.06 + 0.0012 * (Y - 400)) * self.s / SC0


def person(wc, ch, X, Y, base=1.0, flip=1, ph0=0.0, **kw):
    x, y = wc.pt(X, Y); kw.setdefault('gain', 0.97)
    return mk(ch, x, y, wc.sc(Y, base), flip, ph0, **kw)


IDM = Cam(A=(0, 0), sb=1.0, sw=1.0, sc=1.0, d=(0, 0), dw=(0, 0))


def draw_people(cv, items, T): draw_items(cv, IDM, items, T)


def sand(cv, T, amt, seed=1, dirn=1.0, haze=1.0):
    if amt <= 0.01: return
    r = np.random.default_rng(seed); n = int(260 * amt)
    hz = np.array(SAND, np.float32) * 0.9
    cv[:] = cv * (1 - 0.6 * amt * haze) + hz * 0.6 * amt * haze
    for i in range(n):
        sp = 700 + 900 * r.random(); x = (r.random() * (W + 300) + T * sp * dirn) % (W + 300) - 150; y = r.random() * H
        ln = (14 + 60 * r.random()) * (0.5 + amt); c = 150 + 100 * r.random()
        cv2.line(cv, (int(x), int(y)), (int(x - ln * dirn), int(y + 3 * r.random())), (c * 0.55, c * 0.78, c), 1 + int(r.random() > 0.7), cv2.LINE_AA)


def dune_fx(cv, T, seed=5):
    motes(cv, T, seed, 26, 0.5, (150, 205, 240), 0.9)


def jog(X0, X1, t0, t1, T): return lerp(X0, X1, clamp((T - t0) / (t1 - t0)))


# ------------------------------------------------------------------ 1. imagining a race in the desert (0 - 3.1)
def shot_start(cv, T):
    k = seg(T, 0, 2.3); wc = WC(lerp(640, 740, k), 336, lerp(1.0, 1.08, k)); wc.draw(cv, 'pr_race')
    items = []
    for i in range(13):
        X = 300 + 78 * i + 70 * T * (0.9 + 0.02 * (i % 4)); Y = 560 + 38 * ((i * 7) % 3) - 8 * (i % 2)
        if i == 6: items.append(person(wc, 'p', X - 30, 600, 1.12, 1, 0.3, walk=1.0, pose={'aL': 14, 'aR': 14}, gain=1.0)); continue
        items.append(person(wc, 'r', X, Y, 1.0, 1, i * 1.3, walk=1.0, pose={'aL': 14, 'aR': 14}, shirt=RSH[i % 6], pants=RPT[(i * 2) % 6]))
    draw_people(cv, items, T); sand(cv, T, 0.0); dune_fx(cv, T, 11); vignette(cv, 0.3, 2.0); finish(cv, T, 301, 0.3, 0)


# ------------------------------------------------------------------ 2. the sandstorm rolls in (3.1 - 5.5)
def shot_storm(cv, T):
    k = seg(T, 2.0, 3.9); wc = WC(lerp(900, 760, k), 336, lerp(1.0, 1.18, k)); wc.draw(cv, 'pr_storm')
    items = []
    for i in range(9):
        X = 420 + 95 * i + 40 * (T - 2.0); Y = 560 + 34 * ((i * 5) % 3)
        lean = 8 + 10 * ev(T, 2.6, 3.6)
        items.append(person(wc, 'r' if i != 4 else 'p', X, Y, 1.0, 1, i * 1.1, walk=1.0, pose={'aL': 14, 'aR': 14, 'lean': lean, 'head': lean}, shirt=RSH[i % 6] if i != 4 else None, pants=RPT[(i * 2) % 6] if i != 4 else None))
    draw_people(cv, items, T); sand(cv, T, 0.15 + 0.5 * ev(T, 2.2, 3.8), 21, -1.0, 0.6); vignette(cv, 0.5, 2.0); finish(cv, T, 302, 0.4, 0)


# ------------------------------------------------------------------ 3. everything disappears (5.5 - 6.9)
def shot_hide(cv, T):
    k = seg(T, 3.6, 5.1); wc = WC(760, 336, lerp(1.2, 1.5, k)); wc.draw(cv, 'pr_storm', 0.8)
    sh = 1.0
    draw_people(cv, [person(wc, 'p', 790, 650, 1.0, 1, 0.3, crouch=0.35, pose={'aL': 118, 'fL': 140, 'aR': 30, 'fR': -30, 'head': 12 + 3 * math.sin(T * 14), 'lean': 10 + 3 * math.sin(T * 9)})], T)
    sand(cv, T, 0.95, 22, -1.0, 1.0); cv += 0; vignette(cv, 0.6, 2.0); finish(cv, T, 303, 0.5, 0)


# ------------------------------------------------------------------ 4. the storm calms: he is alone (6.9 - 9.5)
def shot_calm(cv, T):
    k = seg(T, 4.9, 7.5); wc = WC(790, 336, lerp(1.12, 1.0, k)); wc.draw(cv, 'pr_empty')
    lk = ev(T, 5.1, 6.6); look = 0.0
    if T > 6.2: look = math.sin((T - 6.2) * 3.2) * 22 * ev(T, 6.2, 6.6)
    draw_people(cv, [person(wc, 'p', 790, 640, 1.1, 1, 0.3, crouch=0.3 * (1 - lk), pose={'aL': 118 * (1 - lk), 'fL': 140 * (1 - lk), 'aR': 8, 'head': 10 * (1 - lk) + look, 'lean': 4 * (1 - lk)})], T)
    sand(cv, T, 0.9 * (1 - lk) ** 1.5 + 0.0, 23, -1.0, 1.0 - 0.5 * lk); dune_fx(cv, T, 12); vignette(cv, 0.35, 2.0); finish(cv, T, 304, 0.35, 0)


# ------------------------------------------------------------------ 5. no road (9.5 - 10.6)
def shot_noroad(cv, T):
    k = seg(T, 7.3, 8.9); wc = WC(790, 336, lerp(1.0, 1.0, k)); wc.draw(cv, 'pr_empty')
    sp = ev(T, 7.6, 8.2)
    draw_people(cv, [person(wc, 'p', 790, 640, 1.1, 1, 0.3, pose={'aL': 8 + 38 * sp, 'aR': 8 + 38 * sp, 'fL': 10 * sp, 'fR': 10 * sp, 'head': 18 * math.sin(T * 2.4) * sp})], T)
    dune_fx(cv, T, 13); vignette(cv, 0.35, 2.0); finish(cv, T, 305, 0.35, 0)


# ------------------------------------------------------------------ 6. no racers: tiny and alone (10.6 - 11.5)
def shot_norunners(cv, T):
    k = seg(T, 8.7, 9.8); wc = WC(790, 336, lerp(1.0, 1.0, k)); wc.draw(cv, 'pr_empty')
    draw_people(cv, [person(wc, 'p', 900, 560, 0.7, 1, 0.3, pose={'head': 25 * math.sin(T * 2.0), 'aL': 14, 'aR': 14})], T)
    dune_fx(cv, T, 14); vignette(cv, 0.45, 2.0); finish(cv, T, 306, 0.4, 0)


# ------------------------------------------------------------------ 7. not even one sign (11.5 - 12.1): he shades his eyes and scans the horizon
def shot_nosign(cv, T):
    k = seg(T, 9.6, 12.2); wc = WC(lerp(700, 860, k), 336, 1.2); wc.draw(cv, 'pr_empty')
    draw_people(cv, [person(wc, 'p', 790, 640, 1.2, 1, 0.3, pose={'aL': 118, 'fL': 140, 'aR': 8, 'head': 20 * math.sin((T - 9.7) * 3.6)})], T)
    dune_fx(cv, T, 15); vignette(cv, 0.4, 2.0); finish(cv, T, 307, 0.4, 0)


# ------------------------------------------------------------------ 8. "this really happened to an Italian runner" (12.1 - 14.6)
def flag_it(cv, x, y, s, T, ph=0.0):
    ht = 300 * s
    cv2.line(cv, (int(x + 3), int(y + 4)), (int(x + 3), int(y - ht + 4)), (8.0, 10.0, 14.0), max(3, int(7 * s)), cv2.LINE_AA)
    cv2.line(cv, (int(x), int(y)), (int(x), int(y - ht)), (175.0, 190.0, 205.0), max(3, int(6 * s)), cv2.LINE_AA)
    cols = ((70.0, 140.0, 0.0), (240.0, 245.0, 245.0), (50.0, 40.0, 205.0)); sw = 56 * s; h = 110 * s; seg_n = 5
    for i in range(3):
        for j in range(seg_n):
            xa = x + (i * seg_n + j) * sw / seg_n; xb = xa + sw / seg_n
            wv = lambda xx: 7 * s * math.sin((xx - x) / (22 * s) - T * 5 + ph) * min(1.0, (xx - x) / (sw * 1.5) + 0.15)
            ya, yb = y - ht + wv(xa), y - ht + wv(xb)
            cv2.fillConvexPoly(cv, np.array([(xa, ya), (xb + 1, yb), (xb + 1, yb + h), (xa, ya + h)], np.int32), cols[i], cv2.LINE_AA)
    cv2.rectangle(cv, (int(x), int(y - ht)), (int(x + 3 * sw), int(y - ht + h)), (30.0, 30.0, 34.0), 1, cv2.LINE_AA)


def shot_italian(cv, T):
    k = seg(T, 12.0, 14.7); wc = WC(790, 336, lerp(1.1, 1.22, k)); wc.draw(cv, 'pr_race', 0.95)
    fl = ev(T, 12.2, 12.8)
    draw_people(cv, [person(wc, 'p', 790, 650, 1.25, 1, 0.3, mouth=0.0, pose={'aL': 8, 'aR': 8 + 120 * P(T, 13.2, 14.4), 'fR': 0, 'head': 3 * math.sin(T * 1.4)})], T)
    xs, ys = wc.pt(540, 630); flag_it(cv, xs, ys, 0.8 * fl + 0.01, T)
    dune_fx(cv, T, 16); vignette(cv, 0.35, 2.0); finish(cv, T, 308, 0.3, 0)


# ------------------------------------------------------------------ 9. Mauro Prosperi in the toughest endurance race (14.6 - 18.1): back at the start line, light on him
def shot_mauro(cv, T):
    k = seg(T, 14.5, 18.2); wc = WC(lerp(760, 700, k), 336, lerp(1.0, 1.25, k)); wc.draw(cv, 'pr_race')
    items = []
    for i in range(14):
        X = 260 + 74 * i + 8 * math.sin(i * 2.0); Y = 570 + 36 * ((i * 7) % 3) - 7 * (i % 2)
        if i == 7: continue
        items.append(person(wc, 'r', X, Y, 1.0, 1 if i % 3 else -1, i * 1.3, pose={'aL': 8 + 8 * math.sin(T + i), 'aR': 8, 'head': 5 * math.sin(T * 1.2 + i)}, shirt=RSH[i % 6], pants=RPT[(i * 2) % 6], crouch=0.0))
    items.append(person(wc, 'p', 260 + 74 * 7, 610, 1.15, 1, 0.3, pose={'aL': 8, 'aR': 8 + 30 * P(T, 16.0, 17.0), 'head': 4 * math.sin(T * 1.3)}))
    draw_people(cv, items, T); px_, py_ = wc.pt(260 + 74 * 7, 450)
    lb = LightBuf(); lb.glow(px_, py_, 130 * wc.z, (210, 235, 255), 0.25 * ev(T, 15.0, 15.8)); lb.apply(cv, blur=30)
    dune_fx(cv, T, 17); vignette(cv, 0.35 + 0.15 * ev(T, 15.0, 16.0), 2.0); finish(cv, T, 309, 0.3, 0)


# ------------------------------------------------------------------ 10. "the problem was not only that he lost the way" (18.1 - 21.5)
def shot_problem(cv, T):
    k = seg(T, 18.0, 21.6); wc = WC(lerp(650, 900, k), 336, 1.05); wc.draw(cv, 'pr_empty')
    X = lerp(640, 900, ev(T, 18.2, 21.4)); wk = 1.0
    draw_people(cv, [person(wc, 'p', X, 640, 1.1, 1, 0.3, walk=wk, pose={'aL': 10, 'aR': 10, 'head': 16 * math.sin((T - 18.0) * 1.9) + 6})], T)
    puffs(cv, T, 18.0, 21.8, 12, (400, 660, 500, 40), SAND, seed=31, size=(40, 90), rise=(8, 28), life=1.6, alpha=0.25, wind=(-30, 0))
    dune_fx(cv, T, 18); vignette(cv, 0.35, 2.0); finish(cv, T, 310, 0.3, 0)


# ------------------------------------------------------------------ 11. he keeps running, sure he is going back (21.5 - 25.6): the real course (flags) fades far behind him
def flags_far(cv, wc, T, X0, n=14, fade=1.0):
    for i in range(n):
        X = X0 + 55 * i; Y = 450 + 4 * i; x, y = wc.pt(X, Y); s = (0.55 - 0.02 * i) * wc.z
        if s < 0.12: continue
        cv2.line(cv, (int(x), int(y)), (int(x), int(y - 90 * s)), (30.0 * fade, 40.0 * fade, 60.0 * fade), max(1, int(2 * s)), cv2.LINE_AA)
        wv = 6 * s * math.sin(T * 5 + i)
        pts = np.array([(x, y - 90 * s), (x + 34 * s + wv, y - 80 * s), (x, y - 62 * s)], np.int32)
        cv2.fillConvexPoly(cv, pts, (60.0 * fade, 60.0 * fade, 215.0 * fade), cv2.LINE_AA)


def shot_walking(cv, T):
    k = seg(T, 21.4, 25.7); evn = ev(T, 21.6, 25.5); wc = WC(lerp(420, 1160, evn), 336, lerp(1.12, 1.0, k)); wc.draw(cv, 'pr_empty', lerp(1.0, 0.82, k))
    flags_far(cv, wc, T, 90, 12, 1.0 - 0.7 * k)
    Xm = wc.px + 40 + 50 * math.sin(T * 0.5); ls = 0.4 * ev(T, 23.0, 25.0)
    draw_people(cv, [person(wc, 'p', Xm, 640, 1.05, 1, 0.3, walk=1.0, pose={'aL': 14, 'aR': 14, 'lean': 6, 'head': -4 + 3 * math.sin(T * 5)})], T)
    xx, yy = wc.pt(Xm, 650); puffs(cv, T, 21.4, 25.7, 22, (xx - 150, yy - 8, 140, 18), SAND, seed=32, size=(30, 70), rise=(8, 30), life=1.1, alpha=0.3, wind=(-110, 0))
    tone(cv, 1.0, 0, (1.0 - 0.15 * k, 0.98 - 0.05 * k, 1.0 + 0.08 * k), 1.0); dune_fx(cv, T, 19); vignette(cv, 0.35 + 0.2 * k, 2.0); finish(cv, T, 311, 0.3, 0)


# ------------------------------------------------------------------ 12. hundreds of kilometres away (25.7 - 28.3): the camera pulls back, a long trail of footprints
def shot_far(cv, T):
    k = seg(T, 25.6, 28.4); z = lerp(1.35, 1.0, ease_out(k)); wc = WC(lerp(1100, 800, k), 336, z); wc.draw(cv, 'pr_empty', 0.85)
    flags_far(cv, wc, T, 90, 10, 0.3 * (1 - k))
    Xm = 1000.0; Ym = 590.0
    n = 38
    for i in range(n):          # footprints trail coming from the far left horizon
        f = (i + 1) / n; X = lerp(Xm, 120.0, f ** 0.9); Y = lerp(Ym, 455.0, f ** 0.9) + 4 * math.sin(i * 1.7)
        if f > ev(T, 25.8, 27.6) + 0.0: continue
        x, y = wc.pt(X, Y); r_ = max(1.2, 6 * (1 - f) * wc.z); cv2.ellipse(cv, (int(x), int(y)), (int(r_ * 1.4), int(max(1, r_ * 0.6))), 0, 0, 360, (40.0, 80.0, 130.0), -1, cv2.LINE_AA)
    draw_people(cv, [person(wc, 'p', Xm, Ym, 0.75, 1, 0.3, walk=1.0, pose={'aL': 14, 'aR': 14, 'lean': 6, 'head': -3})], T)
    tone(cv, 1.0, 0, (0.88, 0.95, 1.04), 1.0); dune_fx(cv, T, 20); vignette(cv, 0.5, 2.0); finish(cv, T, 312, 0.45, 0)


# ------------------------------------------------------------------ 13. he crosses a border without noticing (28.3 - end)
def shot_border(cv, T):
    k = seg(T, 28.2, DP); evn = ev(T, 28.3, 30.9); wc = WC(lerp(760, 880, k), 336, lerp(1.0, 1.12, k)); wc.draw(cv, 'pr_border')
    X = lerp(330, 1260, evn)
    wk = 1.0 if evn < 0.98 else 0.0
    draw_people(cv, [person(wc, 'p', X, 600, 0.95, 1, 0.3, walk=wk, pose={'aL': 10, 'aR': 10, 'head': 18 - 3 * math.sin(T * 4), 'lean': 4})], T)
    xx, yy = wc.pt(X, 610); puffs(cv, T, 28.3, DP, 16, (xx - 130, yy - 8, 120, 16), SAND, seed=33, size=(26, 60), rise=(8, 26), life=1.0, alpha=0.3, wind=(-100, 0))
    dune_fx(cv, T, 21); vignette(cv, 0.4, 2.0); finish(cv, T, 313, 0.35, 0)


SHOTSP = [('start', 0.0, 2.1, shot_start, 0.0), ('storm', 2.1, 3.7, shot_storm, 0.4), ('hide', 3.7, 5.0, shot_hide, 0.3), ('calm', 5.0, 7.4, shot_calm, 0.5), ('noroad', 7.4, 8.8, shot_noroad, 0.2),
          ('norunners', 8.8, 9.7, shot_norunners, 0.2), ('nosign', 9.7, 12.1, shot_nosign, 0.2), ('italian', 12.1, 14.6, shot_italian, 0.3), ('mauro', 14.6, 18.1, shot_mauro, 0.4),
          ('problem', 18.1, 21.5, shot_problem, 0.4), ('walking', 21.5, 25.6, shot_walking, 0.4), ('far', 25.6, 28.3, shot_far, 0.4), ('border', 28.3, DP, shot_border, 0.4)]


class PartP:
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTSP):
            hi = t1 + (SHOTSP[i + 1][4] / 2 if i + 1 < len(SHOTSP) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTSP) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
