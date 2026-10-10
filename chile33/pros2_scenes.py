"""Prosperi video PART 2 (Arabic, 80.3 s): who Mauro Prosperi is (Roman policeman, Olympic modern pentathlete), the Marathon des Sables 1994 in Morocco,
the race conditions (dunes, rocks, heat, no shops, water points), the first days go well ... one storm can change a life.
Same oil-painting layered-puppet system as Part 1 (pros_scenes.py). NO face mark, NO captions, NO music."""
from pros_scenes import *
import pros_scenes as PS

DP2 = 80.3
NAVY = (0.5, 0.38, 0.3)


def cam(T, t0, t1, c0, c1, plate, gain=1.0, cv=None):
    k = seg(T, t0, t1); wc = WC(lerp(c0[0], c1[0], k), lerp(c0[1], c1[1], k), lerp(c0[2], c1[2], k)); wc.draw(cv, plate, gain); return wc


def pc(ch, sx, sy, sc, flip=1, ph0=0.3, **kw):   # puppet placed directly in screen coords (close-ups)
    kw.setdefault('gain', 0.97); return mk(ch, sx, sy, sc, flip, ph0, **kw)


def fin(cv, T, seed, vig=0.35, fx=True, mo=26):
    if fx: motes(cv, T, seed, mo, 0.5, (150, 205, 240), 0.9)
    vignette(cv, vig, 2.0); finish(cv, T, seed, vig, 0)


def RUN(T, a=40, b=30, sp=9.0, lean=8.0, head=0.0):
    s = math.sin(T * sp); return {'aL': a + b * s, 'aR': a - b * s, 'fL': -55, 'fR': -55, 'lean': lean, 'head': head}


def drops(cv, T, x, y, seed, n=5, rate=1.3):
    r = np.random.default_rng(seed)
    for i in range(n):
        ph = (T * rate + r.random()) % 1.0; xx = x + (r.random() - 0.5) * 70 + 8 * ph; yy = y + ph * ph * 190
        cv2.ellipse(cv, (int(xx), int(yy)), (3, 6), 0, 0, 360, (235.0, 225.0, 205.0), -1, cv2.LINE_AA)


def pin(cv, x, y, s, a=1.0):
    if a <= 0.01 or s <= 0.02: return
    h = 46 * s; r = 14 * s
    cv2.fillConvexPoly(cv, np.array([(x - r * 0.9, y - h + r * 0.5), (x + r * 0.9, y - h + r * 0.5), (x, y)], np.int32), (45.0, 50.0, 200.0), cv2.LINE_AA)
    cv2.circle(cv, (int(x), int(y - h)), int(r), (45.0, 50.0, 205.0), -1, cv2.LINE_AA); cv2.circle(cv, (int(x), int(y - h)), int(r * 0.4), (225.0, 235.0, 245.0), -1, cv2.LINE_AA)
    cv2.circle(cv, (int(x), int(y - h)), int(r), (20.0, 25.0, 90.0), max(1, int(2 * s)), cv2.LINE_AA)


def ring(cv, x, y, r, a, col=(40.0, 60.0, 210.0)):
    if a <= 0.02: return
    ov = cv.copy(); cv2.ellipse(ov, (int(x), int(y)), (int(r), int(r * 0.45)), 0, 0, 360, col, max(2, int(4 * a)), cv2.LINE_AA); cv[:] = cv * (1 - a) + ov * a


ROUTE = [(632, 536), (790, 470), (950, 556), (1110, 468), (1290, 548), (1450, 462)]


def route_overlay(cv, wc, T, t0, t1, ink=(30.0, 45.0, 120.0)):
    """dashed route drawn progressively along ROUTE with a red dot (stage) at every point."""
    k = clamp((T - t0) / (t1 - t0)) * (len(ROUTE) - 1); n = int(k); last = len(ROUTE) - 1
    for i in range(last):
        if i > n: break
        a = ROUTE[i]; b = ROUTE[i + 1]; f = 1.0 if i < n else (k - n)
        for j in range(14):
            if j / 14.0 > f: break
            p0 = (lerp(a[0], b[0], j / 14.0), lerp(a[1], b[1], j / 14.0)); p1 = (lerp(a[0], b[0], (j + 0.55) / 14.0), lerp(a[1], b[1], (j + 0.55) / 14.0))
            x0, y0 = wc.pt(*p0); x1, y1 = wc.pt(*p1); cv2.line(cv, (int(x0), int(y0)), (int(x1), int(y1)), ink, max(3, int(5 * wc.z)), cv2.LINE_AA)
    for i, (X, Y) in enumerate(ROUTE):
        if i > k + 0.02: break
        x, y = wc.pt(X, Y); pop = (sstep(seg(k, i - 0.02, i + 0.2)) if i else 1.0) * (1 + 0.25 * math.sin(math.pi * clamp((k - i) / 0.35)))
        rr = max(3, int(11 * wc.z * pop)); cv2.circle(cv, (int(x), int(y)), rr, (40.0, 50.0, 205.0), -1, cv2.LINE_AA); cv2.circle(cv, (int(x), int(y)), rr, (15.0, 20.0, 80.0), 2, cv2.LINE_AA)


# ------------------------------------------------------------------ 1. "his name is Mauro Prosperi, an Italian policeman from Rome" (0 - 2.9)
def shot_rome(cv, T):
    wc = cam(T, 0, 3.2, (720, 336, 1.0), (800, 340, 1.12), 'pr_rome', cv=cv)
    wv = P(T, 0.9, 2.4)
    draw_people(cv, [person(wc, 'p', 810, 575, 1.5, 1, 0.3, shirt=NAVY, pose={'aL': 8, 'aR': 8 + 105 * ev(T, 0.5, 1.0) - 40 * ev(T, 2.0, 2.6), 'fR': 25 * math.sin(T * 7) * wv, 'head': 3 * math.sin(T * 1.6)})], T)
    lb = LightBuf(); lb.glow(*wc.pt(560, 230), 160 * wc.z, (110, 190, 255), 0.25); lb.apply(cv, blur=36)
    fin(cv, T, 401, 0.35)


# ------------------------------------------------------------------ 2. "a professional athlete who took part in the Olympic Games" (2.9 - 5.5)
def shot_stadium(cv, T):
    wc = cam(T, 2.7, 5.7, (640, 336, 1.0), (960, 330, 1.1), 'pr_stadium', cv=cv)
    X = jog(260, 980, 2.8, 5.6, T); hail = ev(T, 4.6, 5.2)
    draw_people(cv, [person(wc, 'p', X, 600, 1.2, 1, 0.3, walk=1.0 - 0.8 * hail, pose={'aL': 40 - 24 * hail, 'aR': 40 + 100 * hail, 'fL': -45 * (1 - hail), 'fR': -45 * (1 - hail), 'lean': 6 * (1 - hail)})], T)
    lb = LightBuf(); fx_, fy_ = wc.pt(1500, 220); lb.glow(fx_, fy_, 80 * wc.z, (60, 150, 255), 0.55 + 0.1 * math.sin(T * 9)); lb.glow(fx_, fy_, 200 * wc.z, (40, 110, 230), 0.2); lb.apply(cv, blur=26)
    puffs(cv, T, 2.8, 5.6, 14, (500, 560, 700, 40), (150, 120, 100), seed=41, size=(30, 60), rise=(6, 22), life=1.0, alpha=0.18, wind=(-70, 0))
    fin(cv, T, 402, 0.35)


# ------------------------------------------------------------------ 3. the five skills of the modern pentathlon (5.5 - 10.85): a pan across five painted zones
ZONES = [(190, 'fence'), (650, 'swim'), (810, 'shoot'), (1085, 'ride'), (1420, 'run')]


def shot_penta(cv, T):
    wc = cam(T, 5.4, 11.0, (330, 340, 1.5), (1260, 340, 1.5), 'pr_penta', cv=cv)
    items = []
    for i, (X, kind) in enumerate(ZONES):
        t_in = 5.7 + 1.0 * i; sc = ev(T, t_in, t_in + 0.35)
        if sc <= 0.01: continue
        pose = {'aL': 14, 'aR': 14}; kw = {}; Y = 610
        if kind == 'fence': pose = {'aL': 20 + 8 * math.sin(T * 7), 'aR': 80 + 12 * math.sin(T * 9), 'fR': 0, 'lean': 10 + 4 * math.sin(T * 9)}
        elif kind == 'swim': pose = {'aL': 20 + 100 * abs(math.sin(T * 4)), 'aR': 20 + 100 * abs(math.cos(T * 4)), 'lean': 22}
        elif kind == 'shoot': pose = {'aL': 20, 'aR': 98, 'fR': 55, 'head': 8, 'lean': 2}
        elif kind == 'ride': pose = {'aL': 44, 'aR': 44, 'fL': -30, 'fR': -30}; kw = dict(crouch=0.45)
        else: pose = RUN(T, 40, 30, 8.0); kw = dict(walk=1.0)
        items.append(person(wc, 'p', X, Y, 1.0 * (0.4 + 0.6 * sc), 1, 0.3 + i, pose=pose, gain=0.97, **kw))
    draw_people(cv, items, T); fin(cv, T, 403, 0.4)


# ------------------------------------------------------------------ 4. "focus and a great ability to endure" (10.85 - 13.45)
def shot_focus(cv, T):
    wc = cam(T, 10.7, 13.6, (800, 420, 1.9), (860, 400, 1.7), 'pr_stadium', cv=cv)
    draw_items(cv, IDM, [pc('p', 640, 700, 0.64, 1, 0.3, walk=1.0, pose=RUN(T, 36, 22, 7.0, 6.0, 3 * math.sin(T * 1.3)))], T)
    lb = LightBuf(); lb.glow(1000, 120, 280, (100, 190, 255), 0.2); lb.apply(cv, blur=40)
    fin(cv, T, 404, 0.45)


# ------------------------------------------------------------------ 5. "not someone who decided to stroll through the desert and got lost" (13.45 - 18.0)
def shot_wander(cv, T):
    wc = cam(T, 13.3, 18.2, (520, 336, 1.15), (900, 336, 1.15), 'pr_empty', cv=cv)
    st = ev(T, 16.0, 16.4)
    X = jog(420, 880, 13.5, 16.2, T); look = 22 * math.sin((T - 13.5) * 1.5) * (1 - st)
    draw_people(cv, [person(wc, 'r', X, 640, 1.2, 1, 0.5, walk=1.0 - st, shirt=RSH[2], pose={'aL': 14 + 104 * st, 'fL': 140 * st, 'aR': 14, 'head': look + 14 * st * math.sin((T - 16.4) * 4)})], T)
    cv[:] = heat_haze(cv, T, 1.6, 0.045, 2.6, 300, 560); fin(cv, T, 405, 0.35)


# ------------------------------------------------------------------ 6. "but an athlete used to hard training" (18.0 - 22.4)
def shot_train(cv, T):
    X = jog(260, 1180, 18.0, 22.2, T); wc = cam(T, 17.9, 22.5, (480, 340, 1.12), (1020, 340, 1.12), 'pr_stadium', cv=cv)
    draw_people(cv, [person(wc, 'p', X, 600, 1.3, 1, 0.3, walk=1.0, pose=RUN(T, 40, 34, 10.0, 12.0, 0.0))], T)
    xx, yy = wc.pt(X, 610); puffs(cv, T, 18.0, 22.4, 26, (xx - 150, yy - 8, 130, 14), (110, 110, 135), seed=42, size=(26, 56), rise=(8, 24), life=1.0, alpha=0.3, wind=(-120, 0))
    fin(cv, T, 406, 0.4)


# ------------------------------------------------------------------ 7. "how to deal with fatigue and physical pressure" (22.4 - 25.5)
def shot_tired(cv, T):
    wc = cam(T, 22.2, 25.7, (900, 420, 1.8), (820, 400, 1.95), 'pr_stadium', 0.92, cv=cv)
    b = math.sin(T * 5.5) * 0.5 + 0.5; lean = 30 + 6 * b
    draw_items(cv, IDM, [pc('p', 640, 720, 0.66, 1, 0.3, crouch=0.15, sway=2.5, pose={'aL': 6, 'aR': 6, 'fL': -10, 'fR': -10, 'lean': lean, 'head': 22 + 4 * b})], T)
    drops(cv, T, 700, 255, 7, 6, 1.1)
    tone(cv, 1.0, 0, (0.92, 0.97, 1.06), 1.0); fin(cv, T, 407, 0.5)


# ------------------------------------------------------------------ 8. "experience and fitness alone are not enough" (25.5 - 28.9): the open-palm shrug in a vast desert
def shot_shrug(cv, T):
    wc = cam(T, 25.3, 29.1, (800, 336, 1.3), (790, 336, 1.0), 'pr_empty', cv=cv)
    a = ev(T, 25.8, 26.6); sh = math.sin((T - 26.8) * 3.0) * ev(T, 26.8, 27.2) * (1 - ev(T, 28.3, 28.8))
    draw_people(cv, [person(wc, 'p', 790, 640, 1.25, 1, 0.3, pose={'aL': 8 + 52 * a, 'fL': 70 * a, 'aR': 8 + 52 * a, 'fR': 70 * a, 'head': 14 * sh})], T)
    cv[:] = heat_haze(cv, T, 1.4, 0.045, 2.4, 300, 560); fin(cv, T, 408, 0.4)


# ------------------------------------------------------------------ 9. "when nature is stronger than all your calculations" (28.9 - 31.25)
def shot_nature(cv, T):
    k = seg(T, 28.8, 31.4); wc = WC(lerp(780, 800, k), lerp(340, 336, k), lerp(1.45, 1.0, ease_out(k)), 0.9); wc.draw(cv, 'pr_storm')
    draw_people(cv, [person(wc, 'p', 780, 640, 0.95, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 6 * math.sin(T * 1.2)})], T)
    sand(cv, T, 0.12 + 0.18 * k, 51, -1.0, 0.5); tone(cv, 1.0, 0, (0.95, 0.97, 1.0), 1.0); fin(cv, T, 409, 0.55)


# ------------------------------------------------------------------ 10. "in 1994 he decided to enter the Marathon des Sables in Morocco" (31.25 - 35.6): old map, a pin drops on the desert
def shot_map1(cv, T):
    wc = cam(T, 31.1, 35.8, (760, 380, 1.0), (700, 440, 1.45), 'pr_map', cv=cv)
    x, y = wc.pt(*ROUTE[0]); drop = ev(T, 33.2, 33.5); sj = 1.0 - 0.25 * math.sin(math.pi * clamp((T - 33.5) / 0.3))
    pin(cv, x, y - 300 * (1 - drop ** 2) * (drop < 1.0), 1.0 * wc.z * (sj if T > 33.5 else 1.0), drop)
    for j in range(3):
        a = clamp((T - 33.5 - 0.35 * j) / 1.2)
        if 0 < a < 1: ring(cv, x, y, 20 + 140 * a * wc.z, (1 - a) * 0.9)
    tone(cv, 1.04, 0, (0.98, 1.0, 1.02), 1.0); fin(cv, T, 410, 0.45, True, 14)


# ------------------------------------------------------------------ 11. "Marathon des Sables": the start line and crowd (35.6 - 39.0)
def shot_start2(cv, T):
    k = seg(T, 35.4, 39.2); wc = WC(lerp(760, 700, k), 336, lerp(1.0, 1.32, k)); wc.draw(cv, 'pr_race')
    items = []
    for i in range(14):
        X = 250 + 74 * i + 8 * math.sin(i * 2.0); Y = 570 + 36 * ((i * 7) % 3) - 7 * (i % 2)
        if i == 7: continue
        items.append(person(wc, 'r', X, Y, 1.0, 1 if i % 3 else -1, i * 1.3, pose={'aL': 8 + 8 * math.sin(T * 1.3 + i), 'aR': 8 + 20 * max(0, math.sin(T * 2 + i)) * (i % 2), 'head': 5 * math.sin(T * 1.2 + i)}, shirt=RSH[i % 6], pants=RPT[(i * 2) % 6]))
    items.append(person(wc, 'p', 250 + 74 * 7, 610, 1.18, 1, 0.3, pose={'aL': 8, 'aR': 8 + 115 * P(T, 36.8, 38.4), 'fR': 55 * P(T, 36.8, 38.4), 'head': 4 * math.sin(T * 1.3)}))
    draw_people(cv, items, T); px_, py_ = wc.pt(250 + 74 * 7, 450)
    lb = LightBuf(); lb.glow(px_, py_, 130 * wc.z, (210, 235, 255), 0.22); lb.apply(cv, blur=30); fin(cv, T, 411, 0.35)


# ------------------------------------------------------------------ 12. "about 250 km, split into several stages" (39.0 - 43.0): the route is drawn across the map, stage after stage
def shot_map2(cv, T):
    wc = cam(T, 38.8, 43.2, (700, 470, 1.35), (1180, 470, 1.35), 'pr_map', cv=cv)
    route_overlay(cv, wc, T, 39.2, 42.6); tone(cv, 1.04, 0, (0.98, 1.0, 1.02), 1.0); fin(cv, T, 412, 0.45, True, 14)


# ------------------------------------------------------------------ 13. "not running on a paved road" (43.0 - 47.6): a line of racers floundering through soft dunes
def shot_noroad2(cv, T):
    k = seg(T, 42.8, 47.8); wc = WC(lerp(560, 1060, k), 336, lerp(1.12, 1.0, k)); wc.draw(cv, 'pr_empty')
    items = []
    for i in range(7):
        ch = 'p' if i == 3 else 'r'; Y = 600 + 22 * ((i * 5) % 3) - 6 * i
        X = 420 + 120 * i + 90 * (T - 43.0) * (0.7 + 0.04 * i)
        items.append(person(wc, ch, X, Y, 1.05, 1, i * 1.7, walk=1.0, pose=RUN(T + i, 24, 16, 6.0, 14.0, 6 * math.sin(T * 2 + i)), shirt=RSH[i % 6] if ch == 'r' else None, pants=RPT[i % 6] if ch == 'r' else None))
    draw_people(cv, items, T)
    puffs(cv, T, 43.0, 47.6, 24, (300, 600, 900, 40), SAND, seed=43, size=(34, 70), rise=(8, 26), life=1.2, alpha=0.28, wind=(-90, 0))
    cv[:] = heat_haze(cv, T, 1.3, 0.045, 2.4, 300, 560); fin(cv, T, 413, 0.35)


# ------------------------------------------------------------------ 14. "nor shops to stop at and buy water when thirsty" (47.6 - 50.0)
def shot_noshop(cv, T):
    wc = cam(T, 47.4, 50.2, (700, 330, 1.15), (760, 330, 1.35), 'pr_rocks', cv=cv)
    a = ev(T, 47.8, 48.5); turn = math.sin((T - 48.5) * 2.8) * 24 * ev(T, 48.5, 48.9)
    draw_people(cv, [person(wc, 'p', 760, 640, 1.3, 1, 0.3, crouch=0.06, pose={'aL': 14 + 104 * a * (1 - ev(T, 49.3, 49.7)), 'fL': 140 * a * (1 - ev(T, 49.3, 49.7)), 'aR': 14, 'head': turn, 'lean': 4})], T)
    cv[:] = heat_haze(cv, T, 2.0, 0.05, 3.0, 300, 600); lb = LightBuf(); lb.glow(*wc.pt(800, 90), 260 * wc.z, (190, 235, 255), 0.18); lb.apply(cv, blur=40); fin(cv, T, 414, 0.4)


# ------------------------------------------------------------------ 15. "dunes" (50.0 - 51.2)
def shot_dunes2(cv, T):
    wc = cam(T, 49.9, 51.4, (840, 336, 1.25), (760, 336, 1.1), 'pr_empty', 1.0, cv=cv)
    items = []
    for i in range(5):
        X = 420 + 130 * i + 70 * (T - 50.0); Y = 640 - 34 * i
        items.append(person(wc, 'p' if i == 2 else 'r', X, Y, 1.0, 1, i * 1.2, walk=1.0, pose=RUN(T + i, 24, 16, 6.0, 20.0), shirt=RSH[i % 6] if i != 2 else None, crouch=0.1))
    draw_people(cv, items, T); fin(cv, T, 415, 0.35)


# ------------------------------------------------------------------ 16. "rocky ground and dangerous heat" (51.2 - 53.75)
def shot_heat(cv, T):
    wc = cam(T, 51.0, 53.9, (560, 340, 1.0), (900, 330, 1.0), 'pr_rocks', cv=cv)
    items = []
    for i in range(4):
        X = 300 + 140 * i + 55 * (T - 51.2); items.append(person(wc, 'p' if i == 1 else 'r', X, 620 + 10 * (i % 2), 0.95, 1, i * 1.4, walk=1.0, pose=RUN(T + i, 14, 8, 5.0, 18.0, 8), shirt=RSH[i % 6] if i != 1 else None))
    draw_people(cv, items, T); cv[:] = heat_haze(cv, T, 2.6, 0.05, 3.2, 280, 640)
    lb = LightBuf(); sx_, sy_ = wc.pt(800, 90); lb.glow(sx_, sy_, 420, (190, 235, 255), 0.5 + 0.1 * math.sin(T * 3)); lb.apply(cv, blur=44)
    tone(cv, 1.0, 12, (0.96, 1.0, 1.06), 0.95); fin(cv, T, 416, 0.4)


# ------------------------------------------------------------------ 17. "each one must carry his own food and equipment" (53.75 - 56.8)
def shot_carry(cv, T):
    wc = cam(T, 53.6, 57.0, (620, 360, 1.2), (900, 360, 1.2), 'pr_camp', cv=cv)
    X = jog(1100, 700, 53.8, 56.8, T)
    draw_people(cv, [person(wc, 'p', X, 620, 1.35, -1, 0.3, walk=1.0, pose={'aL': 6, 'aR': 6, 'lean': 10, 'head': -3 + 2 * math.sin(T * 3)})], T)
    puffs(cv, T, 53.8, 56.8, 14, (700, 610, 440, 14), SAND, seed=44, size=(24, 50), rise=(8, 22), life=1.0, alpha=0.26, wind=(110, 0))
    fin(cv, T, 417, 0.35)


# ------------------------------------------------------------------ 18. "water at specific points along the route" (56.8 - 60.2)
def shot_water(cv, T):
    wc = cam(T, 56.6, 60.4, (330, 400, 1.7), (360, 400, 1.55), 'pr_camp', cv=cv)
    d = ev(T, 57.6, 58.3) * (1 - ev(T, 59.2, 59.8))
    draw_items(cv, IDM, [pc('p', 520, 700, 0.62, 1, 0.3, mouth=0.5 * d, pose={'aL': 8 + 110 * d, 'fL': 140 * d, 'aR': 8, 'head': -14 * d, 'lean': -2 * d})], T)
    fin(cv, T, 418, 0.35)


# ------------------------------------------------------------------ 19. "Mauro was ready for the challenge" (60.2 - 62.8)
def shot_ready(cv, T):
    wc = cam(T, 60.0, 63.0, (720, 400, 1.9), (700, 390, 1.7), 'pr_race', cv=cv)
    f = P(T, 60.8, 62.4)
    draw_items(cv, IDM, [pc('p', 640, 700, 0.64, 1, 0.3, pose={'aL': 8, 'aR': 8 + 110 * f, 'fR': 100 * f, 'head': -5 * f + 3 * math.sin(T * 1.4)})], T)
    lb = LightBuf(); lb.glow(640, 200, 260, (210, 235, 255), 0.18 * ev(T, 60.3, 61.2)); lb.apply(cv, blur=40); fin(cv, T, 419, 0.45)


# ------------------------------------------------------------------ 20. "and began the race, competing hard; the first days passed without problems" (62.8 - 66.9)
def shot_racing(cv, T):
    k = seg(T, 62.6, 67.1); wc = WC(lerp(540, 1120, k), 336, lerp(1.0, 1.12, k)); wc.draw(cv, 'pr_race')
    items = []
    for i in range(11):
        X = jog(250 + 70 * i, 950 + 70 * i + 40 * math.sin(i * 3.0), 62.8, 67.0, T); Y = 560 + 34 * ((i * 7) % 3) - 7 * (i % 2)
        if i == 5: continue
        items.append(person(wc, 'r', X, Y, 1.0, 1, i * 1.3, walk=1.0, pose=RUN(T + i, 40, 28, 8.5, 6.0), shirt=RSH[i % 6], pants=RPT[(i * 2) % 6]))
    Xm = jog(250 + 70 * 5, 950 + 70 * 5 + 60, 62.8, 67.0, T)
    items.append(person(wc, 'p', Xm, 620, 1.15, 1, 0.3, walk=1.0, pose=RUN(T, 42, 32, 9.0, 8.0)))
    draw_people(cv, items, T)
    xx, yy = wc.pt(Xm, 630); puffs(cv, T, 62.8, 67.0, 26, (xx - 200, yy - 8, 180, 14), SAND, seed=45, size=(30, 66), rise=(8, 24), life=1.1, alpha=0.3, wind=(-100, 0))
    fin(cv, T, 420, 0.3)


# ------------------------------------------------------------------ 21-23. "he kept covering the required distances" (67.0 - 70.9): three quick days, three moods of light
def day_shot(cv, T, t0, t1, plate, c0, c1, Y, xs, warm, seed, gainv=1.0):
    k = seg(T, t0 - 0.2, t1 + 0.2); wc = WC(lerp(c0[0], c1[0], k), lerp(c0[1], c1[1], k), lerp(c0[2], c1[2], k)); wc.draw(cv, plate, gainv)
    X = jog(xs[0], xs[1], t0 - 0.2, t1 + 0.2, T)
    draw_people(cv, [person(wc, 'p', X, Y, 1.2, 1, 0.3, walk=1.0, pose=RUN(T, 40, 30, 8.5, 8.0))], T)
    xx, yy = wc.pt(X, Y + 8); puffs(cv, T, t0 - 0.2, t1 + 0.2, 12, (xx - 130, yy - 8, 120, 14), SAND, seed=seed, size=(24, 56), rise=(8, 24), life=1.0, alpha=0.3, wind=(-100, 0))
    tone(cv, 1.0, 0, warm, 1.0); fin(cv, T, seed, 0.35)


def shot_day1(cv, T): day_shot(cv, T, 67.0, 68.3, 'pr_rocks', (560, 340, 1.1), (760, 340, 1.1), 620, (300, 900), (1.0, 1.0, 1.04), 421)
def shot_day2(cv, T): day_shot(cv, T, 68.3, 69.6, 'pr_empty', (1000, 336, 1.1), (800, 336, 1.1), 640, (1180, 560), (0.97, 1.0, 1.0), 422)
def shot_day3(cv, T): day_shot(cv, T, 69.6, 70.95, 'pr_race', (900, 336, 1.1), (1100, 336, 1.1), 640, (500, 1200), (0.9, 0.96, 1.1), 423)


# ------------------------------------------------------------------ 24. "everything was going according to plan" (70.9 - 72.75)
def shot_plan(cv, T):
    wc = cam(T, 70.7, 72.95, (860, 380, 1.4), (900, 380, 1.3), 'pr_camp', 1.0, cv=cv)
    th = ev(T, 71.3, 71.8)
    draw_people(cv, [person(wc, 'p', 880, 640, 1.3, 1, 0.3, pose={'aL': 8, 'aR': 8 + 120 * th, 'fR': 70 * th, 'head': -4 * th})], T)
    tone(cv, 1.0, 0, (0.96, 1.0, 1.08), 1.0); fin(cv, T, 424, 0.35)


# ------------------------------------------------------------------ 25. "but in the desert you don't need a big mistake to lose everything" (72.75 - 76.5): the sky starts to darken
def shot_doubt(cv, T):
    k = seg(T, 72.6, 76.7); wc = WC(lerp(780, 820, k), 336, lerp(1.35, 1.0, ease_out(k))); wc.draw(cv, 'pr_empty', 1.0 - 0.28 * k)
    look = ev(T, 73.3, 74.2); sh = math.sin((T - 74.4) * 2.6) * 12 * ev(T, 74.4, 74.8)
    draw_people(cv, [person(wc, 'p', 790, 640, 1.25, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 22 * look + sh, 'lean': 2 * look})], T)
    puffs(cv, T, 73.5, 76.7, 12, (200, 500, 1000, 120), SAND, seed=46, size=(50, 110), rise=(4, 20), life=2.0, alpha=0.2, wind=(-120 * k - 20, 0))
    tone(cv, 1.0, 0, (1.0 - 0.1 * k, 0.99 - 0.07 * k, 0.98), 1.0); fin(cv, T, 425, 0.35 + 0.25 * k)


# ------------------------------------------------------------------ 26. "one storm is enough to change your life completely" (76.5 - 80.3): the storm wall, Mauro tiny
def shot_wall(cv, T):
    k = seg(T, 76.3, DP2); wc = WC(lerp(1000, 900, k), 336, lerp(1.0, 1.35, k * k * 0.5 + 0.5 * k), 1.0); wc.draw(cv, 'pr_storm')
    draw_people(cv, [person(wc, 'p', 600, 640, 0.95, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 4 * math.sin(T * 1.2) + 8 * ev(T, 77.0, 77.8)})], T)
    sand(cv, T, 0.10 + 0.3 * k, 52, -1.0, 0.6); fin(cv, T, 426, 0.42 + 0.12 * k)


SHOTS2 = [('rome', 0.0, 2.9, shot_rome, 0.0), ('stadium', 2.9, 5.5, shot_stadium, 0.3), ('penta', 5.5, 10.85, shot_penta, 0.3), ('focus', 10.85, 13.45, shot_focus, 0.3), ('wander', 13.45, 18.0, shot_wander, 0.4),
          ('train', 18.0, 22.4, shot_train, 0.3), ('tired', 22.4, 25.5, shot_tired, 0.3), ('shrug', 25.5, 28.9, shot_shrug, 0.4), ('nature', 28.9, 31.25, shot_nature, 0.4), ('map1', 31.25, 35.6, shot_map1, 0.4),
          ('start2', 35.6, 39.0, shot_start2, 0.4), ('map2', 39.0, 43.0, shot_map2, 0.4), ('noroad2', 43.0, 47.6, shot_noroad2, 0.4), ('noshop', 47.6, 50.0, shot_noshop, 0.3), ('dunes2', 50.0, 51.2, shot_dunes2, 0.2),
          ('heat', 51.2, 53.75, shot_heat, 0.3), ('carry', 53.75, 56.8, shot_carry, 0.3), ('water', 56.8, 60.2, shot_water, 0.3), ('ready', 60.2, 62.8, shot_ready, 0.3), ('racing', 62.8, 67.0, shot_racing, 0.3),
          ('day1', 67.0, 68.3, shot_day1, 0.2), ('day2', 68.3, 69.6, shot_day2, 0.2), ('day3', 69.6, 70.9, shot_day3, 0.2), ('plan', 70.9, 72.75, shot_plan, 0.3), ('doubt', 72.75, 76.5, shot_doubt, 0.4), ('wall', 76.5, DP2, shot_wall, 0.4)]


class PartP2:
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTS2):
            hi = t1 + (SHOTS2[i + 1][4] / 2 if i + 1 < len(SHOTS2) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTS2) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
