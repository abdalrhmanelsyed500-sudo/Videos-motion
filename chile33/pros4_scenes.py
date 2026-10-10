"""Prosperi video PART 4 (Arabic, 75 s): the next day, scant food and flares, the helicopter that never sees him, water and food running out, the search team looks along the course while he drifts away.
Same oil layered-puppet system. NO face mark, NO captions, NO music."""
from pros3_scenes import *
from hook_scenes import LASTHAND
import pros3_scenes as P3

DP4 = 75.2
HELI_W, HELI_H = 1091, 398


def heli(cv, x, y, s, T, face=1, tilt=0.0, alpha=1.0, gain=1.0, seed=0.0):
    """painted helicopter body (cut-out layer) + procedural spinning rotor discs. (x,y) = centre of the body."""
    lay = L('heli_r' if face > 0 else 'heli_l'); y = y + 3 * s * math.sin(T * 6.5 + seed)
    M = M3(x, y, s, s, tilt, 545, 200); place(cv, lay, M, alpha=alpha, gain=gain)
    mx = 716 if face > 0 else HELI_W - 716; tx = 70 if face > 0 else HELI_W - 70
    for (px, py, ax_, ay_, a_) in ((mx, 6, 540 * s, 34 * s, 0.30), (tx, 125, 14 * s, 62 * s, 0.30)):
        p = pt_(M, px, py)
        if alpha < 0.05: continue
        ov = cv.copy(); cv2.ellipse(ov, (int(p[0]), int(p[1])), (max(2, int(ax_)), max(1, int(ay_))), 0, 0, 360, (36.0, 40.0, 46.0), -1, cv2.LINE_AA); cv[:] = cv * (1 - a_ * alpha) + ov * (a_ * alpha)
    p = pt_(M, mx, 6)
    for k in range(3):
        ph = T * 47.0 + k * 2.1; ex = 540 * s * math.cos(ph); ey = 34 * s * math.sin(ph)
        cv2.line(cv, (int(p[0] - ex), int(p[1] - ey)), (int(p[0] + ex), int(p[1] + ey)), (30.0, 34.0, 40.0), max(1, int(2 * s)), cv2.LINE_AA)


def glowpt(cv, x, y, r, col, a):
    lb = LightBuf(); lb.glow(x, y, r, col, a); lb.apply(cv, blur=24)


def flare(cv, x, y, T, a=1.0, seed=1.0):
    """burning red signal flare: bright core + flicker + red sparks"""
    if a <= 0.02: return
    fl = 0.8 + 0.2 * math.sin(T * 31 + seed)
    glowpt(cv, x, y, 70, (70, 60, 255), 0.65 * a * fl)
    for r_, c, k in ((30, (90, 120, 255), 0.7), (14, (210, 235, 255), 0.9)):
        glowpt(cv, x, y, r_, c, k * a * fl)
    r = np.random.default_rng(int(seed * 7))
    for i in range(10):
        ph = (T * 1.6 + r.random()) % 1.0; xx = x + (r.random() - 0.5) * 60 * ph + 12 * math.sin(T * 5 + i); yy = y - ph * 110
        cv2.circle(cv, (int(xx), int(yy)), 2, (60.0, 150.0, 255.0), -1, cv2.LINE_AA)


def red_smoke(cv, T, t0, t1, x, y, seed=3):
    puffs(cv, T, t0, t1, 18, (x - 20, y - 10, 40, 20), (60, 60, 210), seed=seed, size=(40, 90), rise=(30, 70), spread=(20, 60), life=2.2, alpha=0.30, wind=(-50, 0))


def bottle(cv, cx, cy, h, lev, T):
    """procedural water bottle: translucent body, blue cap, water level lev (0..1)."""
    w = h * 0.34; top = cy - h / 2; bot = cy + h / 2; r = int(w * 0.35)
    body = np.array([(cx - w * 0.5, top + h * 0.22), (cx - w * 0.28, top + h * 0.1), (cx + w * 0.28, top + h * 0.1), (cx + w * 0.5, top + h * 0.22), (cx + w * 0.5, bot - r), (cx + w * 0.4, bot), (cx - w * 0.4, bot), (cx - w * 0.5, bot - r)], np.int32)
    ov = cv.copy(); cv2.fillConvexPoly(ov, body, (235.0, 225.0, 205.0), cv2.LINE_AA); cv[:] = cv * 0.72 + ov * 0.28
    wl = bot - (bot - (top + h * 0.2)) * lev; wv = 3 * math.sin(T * 3)
    sub = np.array([(cx - w * 0.5, wl + wv), (cx + w * 0.5, wl - wv), (cx + w * 0.5, bot - r), (cx + w * 0.4, bot), (cx - w * 0.4, bot), (cx - w * 0.5, bot - r)], np.int32)
    ov = cv.copy(); cv2.fillConvexPoly(ov, sub, (225.0, 150.0, 70.0), cv2.LINE_AA); cv[:] = cv * 0.45 + ov * 0.55
    cv2.polylines(cv, [body], True, (90.0, 85.0, 80.0), 3, cv2.LINE_AA)
    cv2.rectangle(cv, (int(cx - w * 0.2), int(top)), (int(cx + w * 0.2), int(top + h * 0.1)), (170.0, 90.0, 30.0), -1, cv2.LINE_AA); cv2.rectangle(cv, (int(cx - w * 0.2), int(top)), (int(cx + w * 0.2), int(top + h * 0.1)), (60.0, 40.0, 20.0), 2, cv2.LINE_AA)
    for k in range(4): cv2.line(cv, (int(cx - w * 0.5), int(top + h * (0.4 + 0.12 * k))), (int(cx - w * 0.3), int(top + h * (0.4 + 0.12 * k))), (110.0, 100.0, 95.0), 2, cv2.LINE_AA)


# ------------------------------------------------------------------ 1. "the next day, he kept moving hoping to find the course" (0 - 6.0)
def shot_dawn(cv, T):
    wc = cam(T, 0, 6.2, (900, 336, 1.1), (760, 336, 1.0), 'pr_dawn', cv=cv)
    up = ev(T, 0.3, 1.5); wk = ev(T, 1.6, 2.2); sh = ev(T, 4.0, 4.6) * (1 - ev(T, 5.4, 5.9))
    X = 620 + jog(0, 520, 1.6, 6.0, T)
    draw_people(cv, [person(wc, 'p', X, 640 + 120 * (1 - up), 1.25, 1, 0.3, walk=wk, sway=1.0, pose={'aL': 8 + 110 * sh + (1 - up) * 110, 'fL': 140 * sh + 140 * (1 - up), 'aR': 8 + (1 - up) * 110, 'fR': 140 * (1 - up), 'head': 16 * (1 - up) + 26 * math.sin((T - 4.4) * 2.5) * sh, 'lean': 26 * (1 - up) + 8 * wk})], T)
    xm, ym = wc.pt(620, 640); mound(cv, xm, ym - 6 + 24 * up, 110 * (1 - up) + 30, 30 * (1 - up) + 4, 0.9 * (1 - up))
    glowpt(cv, *wc.pt(600, 258), 220 * wc.z, (110, 190, 255), 0.35); cv[:] = heat_haze(cv, T, 1.0, 0.045, 2.0, 300, 560); fin(cv, T, 601, 0.4)


# ------------------------------------------------------------------ 2. "some food, simple gear and distress flares" (6.0 - 9.4)
def shot_kit(cv, T):
    wc = cam(T, 5.8, 9.6, (440, 380, 1.3), (1080, 380, 1.3), 'pr_kit', cv=cv)
    for (X, Y, t0, t1) in ((420, 500, 6.1, 7.4), (700, 330, 7.2, 8.0), (880, 420, 7.8, 8.6), (1380, 540, 8.4, 9.3)):
        a = P(T, t0, t1); glowpt(cv, *wc.pt(X, Y), 110 * wc.z, (180, 230, 255), 0.38 * a)
    tone(cv, 1.04, 0, (1.0, 1.0, 1.02), 1.0); fin(cv, T, 602, 0.45, True, 14)


# ------------------------------------------------------------------ 3. "but he was not prepared for a long trip alone" (9.4 - 13.0)
def shot_alone(cv, T):
    k = seg(T, 9.2, 13.2); wc = WC(lerp(620, 900, k), 336, lerp(1.5, 1.0, ease_out(k))); wc.draw(cv, 'pr_empty', 1.04)
    X = jog(480, 1000, 9.4, 13.0, T)
    draw_people(cv, [person(wc, 'p', X, 600, 0.85, 1, 0.3, walk=1.0, pose={'aL': 14, 'aR': 14, 'lean': 8, 'head': -6})], T)
    cv[:] = heat_haze(cv, T, 1.6, 0.045, 2.6, 300, 560); glowpt(cv, 1000, 80, 300, (190, 235, 255), 0.25); fin(cv, T, 603, 0.4)


# ------------------------------------------------------------------ 4. "while trying to work out where he was" (13.0 - 15.2)
def shot_where(cv, T):
    wc = cam(T, 12.8, 15.4, (800, 336, 1.2), (760, 336, 1.35), 'pr_rocks', cv=cv)
    sh = ev(T, 13.2, 13.8); turn = math.sin((T - 13.8) * 3.0) * 30 * sh
    draw_people(cv, [person(wc, 'p', 780, 640, 1.3, 1, 0.3, pose={'aL': 8 + 110 * sh, 'fL': 140 * sh, 'aR': 8, 'head': turn})], T)
    cv[:] = heat_haze(cv, T, 1.8, 0.05, 2.8, 300, 600); fin(cv, T, 604, 0.4)


# ------------------------------------------------------------------ 5. "he heard a helicopter fairly near" (15.2 - 18.5)
def shot_hear(cv, T):
    wc = cam(T, 15.0, 18.7, (800, 336, 1.15), (800, 330, 1.25), 'pr_empty', cv=cv)
    ear = ev(T, 15.5, 16.0)
    hx = lerp(1250, 900, ev(T, 16.0, 18.6)); hy = lerp(190, 170, ev(T, 16.0, 18.6)); hs = lerp(0.10, 0.18, ev(T, 16.0, 18.6))
    if T > 15.9: heli(cv, hx, hy, hs, T, -1, alpha=ev(T, 15.9, 16.6))
    draw_people(cv, [person(wc, 'p', 760, 640, 1.3, 1, 0.3, pose={'aL': 8 + 110 * ear, 'fL': 140 * ear, 'aR': 8, 'head': -14 * ear + 8 * math.sin((T - 16.5) * 2.4) * ear})], T)
    fin(cv, T, 605, 0.4)


# ------------------------------------------------------------------ 6. "the most important news he could hear" (18.5 - 20.8)
def shot_hope(cv, T):
    wc = cam(T, 18.3, 21.0, (800, 400, 1.9), (800, 400, 1.75), 'pr_empty', cv=cv)
    heli(cv, lerp(1080, 960, ev(T, 18.5, 20.8)), 150, 0.20, T, -1, 0.0)
    up = ev(T, 18.8, 19.4)
    draw_items(cv, IDM, [pc('p', 560, 700, 0.62, 1, 0.3, mouth=0.35 * up, pose={'aL': 8 + 60 * up, 'fL': 60 * up, 'aR': 8 + 60 * up, 'fR': 60 * up, 'head': -12 * up})], T)
    fin(cv, T, 606, 0.45)


# ------------------------------------------------------------------ 7. "he thought the rescue teams had finally come" (20.8 - 24.1)
def shot_arrives(cv, T):
    wc = cam(T, 20.6, 24.3, (800, 336, 1.1), (800, 336, 1.2), 'pr_empty', cv=cv)
    k = ev(T, 20.8, 24.0); heli(cv, lerp(1350, 560, k), lerp(150, 190, k), lerp(0.22, 0.42, k), T, -1, -4 * k)
    ch = ev(T, 21.2, 21.8)
    draw_people(cv, [person(wc, 'p', 780, 640, 1.3, 1, 0.3, hop=18 * abs(math.sin(T * 6)) * ch, pose={'aL': 8 + 128 * ch, 'aR': 8 + 128 * ch, 'fL': 10 * ch, 'fR': 10 * ch, 'head': -8 * ch})], T)
    puffs(cv, T, 22.0, 24.2, 16, (300, 560, 700, 40), SAND, seed=71, size=(40, 90), rise=(8, 26), life=1.4, alpha=0.2, wind=(-80, 0)); fin(cv, T, 607, 0.35)


# ------------------------------------------------------------------ 8. "he took out the distress flare" (24.1 - 26.7)
def shot_flare(cv, T):
    wc = cam(T, 23.9, 26.9, (800, 400, 1.9), (800, 380, 1.8), 'pr_empty', cv=cv)
    heli(cv, lerp(560, 300, ev(T, 24.0, 26.7)), 150, 0.34, T, -1, -4)
    r = ev(T, 24.2, 25.1)
    draw_items(cv, IDM, [pc('p', 580, 700, 0.62, 1, 0.3, mouth=0.3, pose={'aL': 8, 'aR': 8 + 105 * r, 'fR': 20 * r, 'head': -10 * r})], T)
    hx, hy = LASTHAND[('p', 'r')]; flare(cv, hx, hy, T, ev(T, 24.8, 25.2), 2.0); red_smoke(cv, T, 25.0, 27.0, 800, 200)
    fin(cv, T, 608, 0.45)


# ------------------------------------------------------------------ 9. "tried to draw the pilot's attention, waving everything he had" (26.7 - 28.5)
def shot_wave(cv, T):
    wc = cam(T, 26.5, 28.7, (760, 336, 1.15), (760, 336, 1.15), 'pr_empty', cv=cv)
    k = ev(T, 26.6, 30.8); heli(cv, lerp(300, -150, k), lerp(180, 140, k), lerp(0.40, 0.55, 0.0) * (1 - 0.35 * k), T, -1, -3)
    w = math.sin(T * 9)
    draw_people(cv, [person(wc, 'p', 780, 640, 1.3, 1, 0.3, mouth=0.6, pose={'aL': 8 + 120 + 20 * w, 'aR': 8 + 120 - 20 * w, 'fL': 20 * w, 'fR': -20 * w, 'head': 5 * w})], T)
    hx, hy = LASTHAND[('p', 'r')]; flare(cv, hx, hy, T, 1.0, 2.0); red_smoke(cv, T, 26.0, 28.5, hx, hy, 4); fin(cv, T, 609, 0.35)


# ------------------------------------------------------------------ 10. "but the helicopter did not notice him and flew on" (28.5 - 30.7)
def shot_unnoticed(cv, T):
    wc = cam(T, 28.3, 30.9, (760, 336, 1.15), (700, 336, 1.15), 'pr_empty', cv=cv)
    k = ev(T, 26.6, 30.8); heli(cv, lerp(300, -150, k), lerp(180, 140, k), 0.40 * (1 - 0.35 * k), T, -1, -3)
    w = math.sin(T * 6) * (1 - ev(T, 29.4, 30.6)); dn = ev(T, 29.4, 30.6)
    draw_people(cv, [person(wc, 'p', 780, 640, 1.3, 1, 0.3, mouth=0.5 * (1 - dn), pose={'aL': 8 + (120 - 80 * dn) + 15 * w, 'aR': 8 + (120 - 100 * dn) - 15 * w, 'head': 5 * w})], T)
    hx, hy = LASTHAND[('p', 'r')]; flare(cv, hx, hy, T, 1.0 - ev(T, 29.4, 30.4), 2.0); fin(cv, T, 610, 0.4)


# ------------------------------------------------------------------ 11. "until its sound faded away" (30.7 - 33.0)
def shot_fades(cv, T):
    wc = cam(T, 30.5, 33.2, (700, 336, 1.1), (760, 336, 1.0), 'pr_empty', cv=cv)
    k = ev(T, 30.7, 32.8); heli(cv, lerp(430, 110, k), lerp(220, 250, k), lerp(0.18, 0.03, k), T, -1, alpha=1 - ev(T, 31.8, 32.9))
    draw_people(cv, [person(wc, 'p', 790, 640, 1.2, 1, 0.3, pose={'aL': 8 + 60 * (1 - ev(T, 30.8, 31.6)), 'aR': 8 + 40 * (1 - ev(T, 30.8, 31.6)), 'head': -12 * (1 - ev(T, 31.8, 32.6)), 'lean': 4 * ev(T, 32.0, 32.8)})], T)
    tone(cv, 1.0, 0, (0.94, 0.98, 1.04), 1.0); fin(cv, T, 611, 0.45)


# ------------------------------------------------------------------ 12. "imagine how hard that moment is" (33.0 - 34.2)
def shot_imagine(cv, T):
    wc = cam(T, 32.8, 34.4, (800, 410, 1.8), (800, 410, 1.9), 'pr_empty', 0.92, cv=cv)
    draw_items(cv, IDM, [pc('p', 640, 700, 0.62, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 22, 'lean': 10})], T)
    tone(cv, 1.0, 0, (0.94, 0.98, 1.04), 1.0); fin(cv, T, 612, 0.5)


# ------------------------------------------------------------------ 13. "seeing the means of survival right in front of you" (34.2 - 36.4)
def shot_survival(cv, T):
    wc = cam(T, 34.0, 36.6, (800, 336, 1.2), (800, 336, 1.2), 'pr_empty', cv=cv)
    k = ev(T, 34.2, 36.4); heli(cv, lerp(1250, 640, k), lerp(160, 190, k), lerp(0.30, 0.52, k), T, -1, -3)
    w = math.sin(T * 7)
    draw_people(cv, [person(wc, 'p', 700, 640, 1.3, 1, 0.3, mouth=0.4, pose={'aL': 8 + 120 + 15 * w, 'aR': 8 + 120 - 15 * w, 'head': -10})], T)
    fin(cv, T, 613, 0.35)


# ------------------------------------------------------------------ 14. "and giving everything so they notice you" (36.4 - 38.6)
def shot_allout(cv, T):
    wc = cam(T, 36.2, 38.8, (800, 400, 1.9), (800, 395, 1.75), 'pr_empty', cv=cv)
    w = math.sin(T * 11)
    draw_items(cv, IDM, [pc('p', 640, 700, 0.62, 1, 0.3, mouth=0.9 * abs(w), pose={'aL': 8 + 125 + 25 * w, 'aR': 8 + 125 - 25 * w, 'fL': 30 * w, 'fR': -30 * w, 'head': 6 * w})], T)
    hx, hy = LASTHAND[('p', 'r')]; flare(cv, hx, hy, T, 1.0, 3.0); red_smoke(cv, T, 36.2, 38.6, hx, hy, 5); fin(cv, T, 614, 0.45)


# ------------------------------------------------------------------ 15. "and in the end you watch it move off, leaving you alone again" (38.6 - 41.2)
def shot_leaves(cv, T):
    wc = cam(T, 38.4, 41.4, (800, 336, 1.0), (800, 336, 1.0), 'pr_empty', cv=cv)
    k = ev(T, 38.6, 41.0); heli(cv, lerp(640, 1180, k), lerp(190, 250, k), lerp(0.40, 0.04, k), T, 1, 3, alpha=1 - 0.9 * ev(T, 40.2, 41.2))
    dn = ev(T, 38.8, 39.8)
    draw_people(cv, [person(wc, 'p', 700, 640, 1.2, 1, 0.3, pose={'aL': 8 + 120 * (1 - dn), 'aR': 8 + 120 * (1 - dn), 'head': -10 * (1 - dn) + 14 * dn, 'lean': 8 * dn})], T)
    tone(cv, 1.0, 0, (0.92, 0.97, 1.05), 1.0); fin(cv, T, 615, 0.5)


# ------------------------------------------------------------------ 16. "as time passed... " (41.2 - 43.4): time-lapse, he sits waiting; the sun crosses the sky
def shot_wait(cv, T):
    k = seg(T, 41.0, 43.6); wc = WC(800, 336, 1.1); wc.draw(cv, 'pr_empty')
    draw_people(cv, [person(wc, 'p', 790, 700, 1.25, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 24, 'lean': 22}, gain=0.95)], T)
    xs = lerp(120, 1180, k); ys = 240 - 150 * math.sin(math.pi * k); glowpt(cv, xs, ys, 260, (110, 190, 255), 0.35); glowpt(cv, xs, ys, 80, (200, 235, 255), 0.6)
    tone(cv, 1.0, 0, (1.0 - 0.08 * k, 0.99 - 0.05 * k, 1.0 + 0.0 * k), 1.0); fin(cv, T, 616, 0.45)


# ------------------------------------------------------------------ 17. "waiting alone for rescue is not enough; he had to move carefully" (43.4 - 47.0)
def shot_move(cv, T):
    wc = cam(T, 43.2, 47.2, (800, 336, 1.2), (900, 336, 1.2), 'pr_empty', cv=cv)
    up = ev(T, 43.6, 44.4); sh = ev(T, 44.6, 45.2) * (1 - ev(T, 45.8, 46.2)); wk = ev(T, 46.0, 46.6)
    X = 780 + jog(0, 260, 46.0, 47.1, T)
    draw_people(cv, [person(wc, 'p', X, 640 + 90 * (1 - up), 1.3, 1, 0.3, walk=wk, pose={'aL': 8 + 110 * sh + 40 * wk, 'fL': 140 * sh, 'aR': 8 + 20 * wk, 'head': 18 * (1 - up) + 20 * math.sin((T - 45.0) * 2.5) * sh, 'lean': 22 * (1 - up) + 6 * wk})], T)
    fin(cv, T, 617, 0.4)


# ------------------------------------------------------------------ 18. "making use of any opportunity" (47.0 - 49.4)
def shot_chance(cv, T):
    wc = cam(T, 46.8, 49.6, (700, 340, 1.15), (900, 340, 1.15), 'pr_rocks', cv=cv)
    X = jog(520, 980, 47.0, 49.5, T)
    draw_people(cv, [person(wc, 'p', X, 630, 1.25, 1, 0.3, walk=1.0, pose={'aL': 14, 'aR': 14, 'lean': 8, 'head': 20 + 4 * math.sin(T * 3)})], T)
    cv[:] = heat_haze(cv, T, 1.8, 0.05, 2.8, 300, 600); fin(cv, T, 618, 0.4)


# ------------------------------------------------------------------ 19. "the water is running low" (49.4 - 52.6)
def shot_water4(cv, T):
    wc = cam(T, 49.2, 52.8, (800, 340, 1.3), (840, 340, 1.3), 'pr_rocks', cv=cv); cv[:] = cv2.GaussianBlur(cv, (0, 0), 5)
    lev = lerp(0.72, 0.16, ev(T, 49.8, 52.4))
    bottle(cv, 800, 360, 430, lev, T)
    for i in range(4):
        ph = (T * 0.8 + i * 0.27) % 1.0; cv2.circle(cv, (int(740 + 60 * i), int(150 - ph * 90)), 4, (240.0, 235.0, 215.0), -1, cv2.LINE_AA)
    draw_items(cv, IDM, [pc('p', 330, 720, 0.55, 1, 0.3, pose={'aL': 8 + 50 * ev(T, 50.0, 50.6), 'fL': 60 * ev(T, 50.0, 50.6), 'aR': 8, 'head': 14, 'lean': 4})], T)
    fin(cv, T, 619, 0.5)


# ------------------------------------------------------------------ 20. "and the food is limited" (52.6 - 54.0)
def shot_food(cv, T):
    wc = cam(T, 52.4, 54.2, (420, 450, 2.0), (560, 450, 2.0), 'pr_kit', cv=cv)
    glowpt(cv, *wc.pt(420, 520), 120 * wc.z, (180, 230, 255), 0.4 * P(T, 52.5, 54.0)); glowpt(cv, *wc.pt(600, 540), 90 * wc.z, (180, 230, 255), 0.35 * P(T, 52.9, 54.0)); fin(cv, T, 620, 0.5, True, 10)


# ------------------------------------------------------------------ 21. "and the sun drains his body with every hour" (54.0 - 57.8)
def shot_sun(cv, T):
    k = seg(T, 53.8, 58.0); wc = WC(lerp(700, 900, k), 336, lerp(1.15, 1.3, k)); wc.draw(cv, 'pr_empty', 1.05)
    X = jog(520, 1000, 54.0, 57.8, T)
    draw_people(cv, [person(wc, 'p', X, 640, 1.3, 1, 0.3, walk=0.9, sway=2.0, pose={'aL': 8, 'aR': 8, 'lean': 10 + 8 * k, 'head': 14 + 10 * k + 4 * math.sin(T * 2)})], T)
    cv[:] = heat_haze(cv, T, 2.8, 0.05, 3.4, 250, 650); glowpt(cv, 1050, 70, 420, (200, 240, 255), 0.45 + 0.25 * k); glowpt(cv, 1050, 70, 120, (230, 250, 255), 0.5)
    xx, yy = wc.pt(X, 640); drops(cv, T, xx + 18, yy - 330 * 1.3 * wc.z * 0.6, 8, 4, 1.0)
    tone(cv, 1.0, 14 * k, (0.97, 1.0, 1.06), 0.9 - 0.15 * k); fin(cv, T, 621, 0.5)


# ------------------------------------------------------------------ 22. "he did not know exactly where he had got to" (57.8 - 59.8)
def shot_lost4(cv, T):
    wc = cam(T, 57.6, 60.0, (700, 336, 1.3), (780, 336, 1.15), 'pr_empty', cv=cv)
    sw = math.sin((T - 58.0) * 2.4) * 30; sh = ev(T, 58.6, 59.2)
    draw_people(cv, [person(wc, 'p', 780, 640, 1.3, 1, 0.3, pose={'aL': 8 + 52 * sh, 'fL': 70 * sh, 'aR': 8 + 52 * sh, 'fR': 70 * sh, 'head': sw})], T)
    fin(cv, T, 622, 0.45)


# ------------------------------------------------------------------ 23-24. the search teams along the race route; Mauro's path leaves it (59.8 - 68.2)
def heli_icons(cv, wc, T, t0, t1):
    for i in range(2):
        f = (math.sin((T - t0) * 0.8 + i * math.pi) + 1) * 0.5 * (len(ROUTE) - 1); n = min(int(f), len(ROUTE) - 2); a = ROUTE[n]; b = ROUTE[n + 1]; u = f - n
        X = lerp(a[0], b[0], u); Y = lerp(a[1], b[1], u) - 30; x, y = wc.pt(X, Y); heli(cv, x, y, 0.12 * wc.z, T, 1 if b[0] > a[0] else -1, 0.0, seed=i)


def shot_search(cv, T):
    wc = cam(T, 59.6, 64.7, (760, 440, 1.15), (1000, 440, 1.15), 'pr_map', cv=cv)
    route_overlay(cv, wc, 99.0, 0, 1)
    sx, sy = wc.pt(*ROUTE[3]); rr = 190 * wc.s * (1 + 0.04 * math.sin(T * 3)); ov = cv.copy(); cv2.ellipse(ov, (int(sx), int(sy)), (int(rr), int(rr * 0.62)), 0, 0, 360, (45.0, 55.0, 200.0), -1, cv2.LINE_AA); cv[:] = cv * 0.82 + ov * 0.18 * ev(T, 60.0, 61.0)
    cv2.ellipse(cv, (int(sx), int(sy)), (int(rr), int(rr * 0.62)), 0, 0, 360, (35.0, 40.0, 190.0), 3, cv2.LINE_AA)
    heli_icons(cv, wc, T, 60.0, 64.7); tone(cv, 1.04, 0, (0.98, 1.0, 1.02), 1.0); fin(cv, T, 623, 0.5, True, 10)


def shot_drift(cv, T):
    k = seg(T, 64.4, 68.4); wc = WC(lerp(1000, 940, k), lerp(440, 380, k), lerp(1.15, 1.0, k)); wc.draw(cv, 'pr_map')
    route_overlay(cv, wc, 99.0, 0, 1)
    sx, sy = wc.pt(*ROUTE[3]); rr = 190 * wc.s * (1 + 0.04 * math.sin(T * 3)); ov = cv.copy(); cv2.ellipse(ov, (int(sx), int(sy)), (int(rr), int(rr * 0.62)), 0, 0, 360, (45.0, 55.0, 200.0), -1, cv2.LINE_AA); cv[:] = cv * 0.82 + ov * 0.18
    cv2.ellipse(cv, (int(sx), int(sy)), (int(rr), int(rr * 0.62)), 0, 0, 360, (35.0, 40.0, 190.0), 3, cv2.LINE_AA)
    f = ev(T, 64.7, 67.8) * (len(PATHM) - 1); n = int(f); head = None
    for i in range(len(PATHM) - 1):
        if i > n: break
        a = PATHM[i]; b = PATHM[i + 1]; fr = 1.0 if i < n else f - n
        for j in range(8):
            if j / 8.0 > fr: break
            p0 = (lerp(a[0], b[0], j / 8.0), lerp(a[1], b[1], j / 8.0)); p1 = (lerp(a[0], b[0], (j + .55) / 8.0), lerp(a[1], b[1], (j + .55) / 8.0))
            x0, y0 = wc.pt(*p0); x1, y1 = wc.pt(*p1); cv2.line(cv, (int(x0), int(y0)), (int(x1), int(y1)), (20.0, 20.0, 150.0), max(4, int(6 * wc.z)), cv2.LINE_AA); head = (x1, y1)
    if head is not None: pin(cv, head[0], head[1], 0.9 * wc.z, 1.0)
    heli_icons(cv, wc, T, 60.0, 68.4); tone(cv, 1.04, 0, (0.98, 1.0, 1.02), 1.0); fin(cv, T, 624, 0.5, True, 10)


# ------------------------------------------------------------------ 25. "the farther from the right place, the harder to find him" (68.2 - 71.9): he walks toward the horizon, shrinking
def shot_farther(cv, T):
    wc = cam(T, 68.0, 72.1, (800, 336, 1.0), (800, 336, 1.0), 'pr_empty', cv=cv)
    k = ev(T, 68.4, 71.8); X = lerp(760, 980, k); Y = lerp(640, 468, k)
    draw_people(cv, [person(wc, 'p', X, Y, 1.25, 1, 0.3, walk=1.0, pose={'aL': 14, 'aR': 14, 'lean': 6, 'head': -3})], T)
    xx, yy = wc.pt(X, Y + 4); puffs(cv, T, 68.4, 71.8, 14, (xx - 60, yy - 6, 60, 10), SAND, seed=72, size=(18, 40), rise=(6, 20), life=1.0, alpha=0.25, wind=(-60, 0))
    cv[:] = heat_haze(cv, T, 1.4, 0.045, 2.4, 300, 560); tone(cv, 1.0, 0, (0.94, 0.98, 1.04), 1.0); fin(cv, T, 625, 0.5)


# ------------------------------------------------------------------ 26. "even if they were searching with all their strength" (71.9 - 75.2): a far helicopter searches the wrong place
def shot_wrong(cv, T):
    k = seg(T, 71.7, DP4); wc = WC(lerp(900, 760, k), 336, 1.0); wc.draw(cv, 'pr_empty', 0.95)
    heli(cv, lerp(120, 560, ev(T, 71.9, 75.2)), lerp(190, 160, k), 0.07, T, 1, 0.0)
    draw_people(cv, [person(wc, 'p', 1010, 466, 1.2, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 24 * math.sin((T - 72.0) * 1.3)})], T)
    tone(cv, 1.0, 0, (0.9 - 0.04 * k, 0.94 - 0.03 * k, 1.04), 1.0); fin(cv, T, 626, 0.5 + 0.1 * k)


SHOTS4 = [('dawn', 0.0, 6.0, shot_dawn, 0.0), ('kit', 6.0, 9.4, shot_kit, 0.4), ('alone', 9.4, 13.0, shot_alone, 0.4), ('where', 13.0, 15.2, shot_where, 0.3), ('hear', 15.2, 18.5, shot_hear, 0.3),
          ('hope', 18.5, 20.8, shot_hope, 0.3), ('arrives', 20.8, 24.1, shot_arrives, 0.3), ('flare', 24.1, 26.7, shot_flare, 0.3), ('wave', 26.7, 28.5, shot_wave, 0.2), ('unnoticed', 28.5, 30.7, shot_unnoticed, 0.2),
          ('fades', 30.7, 33.0, shot_fades, 0.4), ('imagine', 33.0, 34.2, shot_imagine, 0.3), ('survival', 34.2, 36.4, shot_survival, 0.3), ('allout', 36.4, 38.6, shot_allout, 0.3), ('leaves', 38.6, 41.2, shot_leaves, 0.4),
          ('wait', 41.2, 43.4, shot_wait, 0.4), ('move', 43.4, 47.0, shot_move, 0.3), ('chance', 47.0, 49.4, shot_chance, 0.3), ('water4', 49.4, 52.6, shot_water4, 0.3), ('food', 52.6, 54.0, shot_food, 0.3),
          ('sun', 54.0, 57.8, shot_sun, 0.3), ('lost4', 57.8, 59.8, shot_lost4, 0.3), ('search', 59.8, 64.5, shot_search, 0.4), ('drift', 64.5, 68.2, shot_drift, 0.2), ('farther', 68.2, 71.9, shot_farther, 0.4), ('wrong', 71.9, DP4, shot_wrong, 0.4)]


class PartP4(P2.PartP2):
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTS4):
            hi = t1 + (SHOTS4[i + 1][4] / 2 if i + 1 < len(SHOTS4) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTS4) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
