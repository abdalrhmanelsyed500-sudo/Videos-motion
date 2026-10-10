"""Prosperi video PART 5 (Arabic, 104 s): days pass, thirst and exhaustion, emergency survival (lizard, bats in an old shelter), the marabout shrine for shade,
no safety, the search continues without result, nights, a crossroads, he keeps going toward a mirage. Same oil layered-puppet system. NO face mark, NO captions, NO music."""
from pros4_scenes import *
import pros4_scenes as P4

DP5 = 104.23


def bat(cv, x, y, s, T, ph=0.0, alpha=1.0, hang=False):
    col = (22.0, 18.0, 26.0)
    if alpha < 0.03: return
    ov = cv.copy()
    if hang:
        cv2.ellipse(ov, (int(x), int(y)), (max(2, int(7 * s)), max(3, int(15 * s))), 0, 0, 360, col, -1, cv2.LINE_AA)
    else:
        a = 0.9 * math.sin(T * 15 + ph)
        for sg in (-1, 1):
            pts = np.array([(x, y - 4 * s), (x + sg * 46 * s * math.cos(a), y - 34 * s * math.sin(a) - 10 * s), (x + sg * 30 * s, y + 6 * s), (x + sg * 14 * s, y + 10 * s)], np.int32)
            cv2.fillConvexPoly(ov, pts, col, cv2.LINE_AA)
        cv2.ellipse(ov, (int(x), int(y)), (max(2, int(7 * s)), max(3, int(12 * s))), 0, 0, 360, col, -1, cv2.LINE_AA)
    cv[:] = cv * (1 - alpha) + ov * alpha


def lizard(cv, x, y, s, T, d=1):
    n = 14; pts = []
    for i in range(n): pts.append((x - d * i * 9 * s, y + 3 * s * math.sin(T * 9 - i * 0.7) + 0.0 * i))
    rad = [5.5, 6.5, 6.0, 5.2, 5.6, 6.2, 6.0, 5.0, 4.0, 3.2, 2.6, 2.0, 1.5, 1.0]
    dk = (18.0, 30.0, 48.0); lt = (70.0, 130.0, 150.0); md = (45.0, 90.0, 110.0)
    # legs (two bent segments) with walking swing
    for i, ph in ((2, 0.0), (5, math.pi)):
        for sg in (-1, 1):
            sw = math.sin(T * 9 + ph + (0 if sg > 0 else math.pi)) * 5 * s
            p0 = (pts[i][0], pts[i][1]); k = (p0[0] + sw, p0[1] + sg * 9 * s); f = (k[0] + d * -4 * s + sw * 0.5, k[1] + sg * 7 * s)
            for c, w in ((dk, 5.5 * s + 3), (md, 5.5 * s)):
                cv2.line(cv, (int(p0[0]), int(p0[1])), (int(k[0]), int(k[1])), c, max(2, int(w * 0.6)), cv2.LINE_AA)
                cv2.line(cv, (int(k[0]), int(k[1])), (int(f[0]), int(f[1])), c, max(2, int(w * 0.5)), cv2.LINE_AA)
    for c, extra in ((dk, 3), (lt, 0)):
        for i in range(n - 1):
            r = int(rad[i] * s) + extra
            cv2.line(cv, (int(pts[i][0]), int(pts[i][1])), (int(pts[i + 1][0]), int(pts[i + 1][1])), c, max(2, 2 * r - (0 if extra else 0)), cv2.LINE_AA)
        cv2.ellipse(cv, (int(pts[0][0] + d * 5 * s), int(pts[0][1])), (int(9 * s) + extra, int(6 * s) + extra), 0, 0, 360, c, -1, cv2.LINE_AA)
    cv2.circle(cv, (int(pts[0][0] + d * 8 * s), int(pts[0][1] - 3 * s)), max(1, int(1.6 * s)), (10.0, 10.0, 10.0), -1, cv2.LINE_AA)
    for i in range(1, n - 3, 2):
        cv2.circle(cv, (int(pts[i][0]), int(pts[i][1] - 2 * s)), max(1, int(2 * s)), md, -1, cv2.LINE_AA)


def mirage(cv, y, x0, x1, a, T):
    if a <= 0.01: return
    ov = cv.copy(); cx = int((x0 + x1) / 2); cv2.ellipse(ov, (cx, int(y)), (int((x1 - x0) / 2), 14), 0, 0, 360, (235.0, 205.0, 150.0), -1, cv2.LINE_AA)
    cv2.ellipse(ov, (cx, int(y - 10)), (int((x1 - x0) / 2.6), 5), 0, 0, 360, (250.0, 240.0, 220.0), -1, cv2.LINE_AA)
    ov = cv2.GaussianBlur(ov, (0, 0), 3); cv[:] = cv * (1 - 0.55 * a) + ov * 0.55 * a
    for i in range(4):
        yy = y + 8 + i * 6; w = (x1 - x0) / 2 * (0.9 - 0.1 * i) * (1 + 0.04 * math.sin(T * 3 + i))
        cv2.line(cv, (int(cx - w), int(yy)), (int(cx + w), int(yy)), (245.0, 225.0, 190.0), 1, cv2.LINE_AA)


def sunarc(cv, T, k, a=1.0, col=(200, 235, 255)):
    sx = lerp(80, 1200, k); sy = 300 - 230 * math.sin(math.pi * k); glowpt(cv, sx, sy, 110, col, 0.55 * a); glowpt(cv, sx, sy, 300, (110, 190, 255), 0.25 * a)


# 1 days
def shot_days(cv, T):
    wc = cam(T, 0, 1.7, (800, 336, 1.1), (840, 336, 1.1), 'pr_empty', cv=cv)
    X = jog(620, 900, 0.0, 1.7, T)
    draw_people(cv, [person(wc, 'p', X, 640, 1.2, 1, 0.3, walk=1.0, pose=RUN(T, 14, 8, 5.0, 10.0))], T)
    k = (T / 0.85) % 1.0; sunarc(cv, T, k); tone(cv, 1.0, 0, (1.0, 1.0 - 0.1 * abs(k - 0.5), 1.0 - 0.18 * abs(k - 0.5) * 2), 1.0); fin(cv, T, 701, 0.35)


# 2 the bubble of the race start cracks away
def shot_bubble5(cv, T):
    wc = cam(T, 1.3, 4.5, (820, 336, 1.25), (800, 336, 1.15), 'pr_empty', cv=cv)
    a = 1.0 - ev(T, 3.0, 4.2); r = 170 * (0.55 + 0.45 * ev(T, 1.5, 2.2)) * (1 - 0.8 * ev(T, 3.0, 4.2)); up = ev(T, 3.0, 4.3)
    draw_people(cv, [person(wc, 'p', 640, 640, 1.3, -1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 8 * math.sin(T * 1.5) + 20 * ev(T, 3.2, 4.0), 'lean': 10 * ev(T, 3.2, 4.0)})], T)
    if r > 6: bubble(cv, lerp(840, 980, up), lerp(220, 120, up), r, 'pr_race', (40, 250, 640, 650), clamp(a * ev(T, 1.4, 2.0)))
    fin(cv, T, 702, 0.4)


# 3 battle for survival
def shot_battle(cv, T):
    wc = cam(T, 4.1, 7.6, (700, 336, 1.2), (900, 336, 1.2), 'pr_rocks', cv=cv)
    X = jog(560, 900, 4.3, 7.4, T)
    draw_people(cv, [person(wc, 'p', X, 640, 1.3, 1, 0.3, walk=0.8, sway=2.5, pose={'aL': 16, 'aR': 16, 'lean': 20, 'head': 22 + 4 * math.sin(T * 2)})], T)
    cv[:] = heat_haze(cv, T, 2.0, 0.05, 3.0, 300, 640); tone(cv, 1.0, 8, (0.96, 1.0, 1.05), 0.95); fin(cv, T, 703, 0.45)


# 4 the water is no longer enough
def shot_bottle5(cv, T):
    wc = cam(T, 7.2, 10.0, (800, 340, 1.3), (840, 340, 1.3), 'pr_rocks', cv=cv); cv[:] = cv2.GaussianBlur(cv, (0, 0), 5)
    lev = lerp(0.32, 0.03, ev(T, 7.8, 9.4)); bottle(cv, 800, 360, 430, lev, T)
    ph = (T - 9.0) / 0.9
    if 0 < ph < 1: cv2.ellipse(cv, (790, int(560 + ph * ph * 120)), (5, 9), 0, 0, 360, (240.0, 225.0, 190.0), -1, cv2.LINE_AA)
    draw_items(cv, IDM, [pc('p', 330, 720, 0.55, 1, 0.3, pose={'aL': 8 + 60 * ev(T, 8.0, 8.6), 'fL': 70 * ev(T, 8.0, 8.6), 'aR': 8, 'head': 14, 'lean': 4})], T)
    fin(cv, T, 704, 0.5)


# 5 the body weakens
def shot_weak(cv, T):
    k = seg(T, 9.6, 15.2); wc = WC(lerp(640, 920, k), 336, lerp(1.15, 1.4, k)); wc.draw(cv, 'pr_empty', 1.05)
    X = jog(480, 860, 9.8, 15.0, T); fall = ev(T, 13.2, 14.4)
    draw_people(cv, [person(wc, 'p', X, 640 + 40 * fall, 1.3, 1, 0.3, walk=0.7 * (1 - fall), sway=3.0, pose={'aL': 10, 'aR': 10, 'lean': 14 + 18 * fall, 'head': 16 + 14 * fall + 5 * math.sin(T * 2.2)})], T)
    cv[:] = heat_haze(cv, T, 2.6, 0.05, 3.2, 250, 660); glowpt(cv, 1050, 70, 380, (200, 240, 255), 0.5); xx, yy = wc.pt(X, 640); drops(cv, T, xx + 20, yy - 260 * wc.z, 9, 4, 1.0)
    vignette(cv, 0.3 + 0.35 * (0.5 + 0.5 * math.sin(T * 2.0)), 2.0); tone(cv, 1.0, 12 * k, (0.97, 1.0, 1.06), 0.85); fin(cv, T, 705, 0.5)


# 6 the body loses fluids in the heat
def shot_fluid(cv, T):
    k = seg(T, 14.8, 20.4); wc = WC(lerp(820, 780, k), 336, lerp(1.35, 1.7, k)); wc.draw(cv, 'pr_empty', 1.05)
    X = 800
    draw_people(cv, [person(wc, 'p', X, 640, 1.3, 1, 0.3, walk=0.4, sway=2.0, pose={'aL': 10, 'aR': 10, 'lean': 10, 'head': 12 + 3 * math.sin(T * 2)})], T)
    xx, yy = wc.pt(X, 640); h = 360 * wc.z
    puffs(cv, T, 15.2, 20.4, 26, (xx - 60, yy - h * 0.8, 120, h * 0.5), (235, 225, 205), seed=71, size=(30, 70), rise=(40, 90), spread=(20, 50), life=1.8, alpha=0.22, wind=(10, 0))
    cv[:] = heat_haze(cv, T, 3.2, 0.05, 3.6, 220, 680); glowpt(cv, 1050, 70, 460, (200, 240, 255), 0.5 + 0.3 * k); glowpt(cv, 1050, 70, 130, (235, 250, 255), 0.5)
    tone(cv, 1.0, 14 * k, (0.97, 1.0, 1.08), 0.8); fin(cv, T, 706, 0.5)


# 7 dehydration noticed too late: the gauge empties, he sways
def shot_notice(cv, T):
    wc = cam(T, 20.0, 25.7, (780, 336, 1.3), (840, 336, 1.3), 'pr_empty', cv=cv)
    lev = lerp(0.5, 0.05, ev(T, 20.4, 24.6)); bottle(cv, 250, 380, 400, lev, T)
    red = ev(T, 23.0, 24.6) * 0.25
    sw = ev(T, 23.4, 24.2); X = jog(700, 860, 20.2, 23.6, T)
    draw_people(cv, [person(wc, 'p', X, 640, 1.3, 1, 0.3, walk=1.0 - sw, sway=1.0 + 3 * sw, pose={'aL': 8 + 110 * sw, 'fL': 140 * sw, 'aR': 8, 'lean': 8 + 10 * sw, 'head': 6 + 14 * sw})], T)
    cv *= (1 - red); cv += np.array((40, 40, 200), np.float32) * red; cv[:] = heat_haze(cv, T, 1.8, 0.05, 3.0, 300, 660); vignette(cv, 0.2 + 0.4 * sw, 2.0); fin(cv, T, 707, 0.45)


# 8 he relies on any chance
def shot_chance5(cv, T):
    wc = cam(T, 25.3, 29.4, (700, 336, 1.25), (860, 336, 1.25), 'pr_rocks', cv=cv)
    sc = ev(T, 25.7, 26.2); look = 26 * math.sin((T - 26.2) * 2.4) * (1 - ev(T, 27.4, 27.8)); dn = ev(T, 27.8, 28.5)
    draw_people(cv, [person(wc, 'p', 780, 640, 1.3, 1, 0.3, pose={'aL': 8 + 110 * sc * (1 - dn), 'fL': 140 * sc * (1 - dn), 'aR': 8 + 50 * dn, 'fR': 30 * dn, 'head': look + 24 * dn, 'lean': 22 * dn})], T)
    cv[:] = heat_haze(cv, T, 1.8, 0.05, 3.0, 300, 640); fin(cv, T, 708, 0.4)


# 9 desperate measures: he kneels and digs
def shot_dig(cv, T):
    wc = cam(T, 29.0, 32.0, (840, 360, 1.5), (860, 380, 1.7), 'pr_rocks', cv=cv)
    dg = ev(T, 29.4, 30.0); s = math.sin(T * 7)
    draw_people(cv, [person(wc, 'p', 820, 640 + 70 * dg, 1.05, 1, 0.3, pose={'aL': 8 + (40 + 30 * s) * dg, 'aR': 8 + (40 - 30 * s) * dg, 'fL': 30 * dg, 'fR': 30 * dg, 'lean': 20 * dg, 'head': 18 * dg})], T)
    xx, yy = wc.pt(820, 640); puffs(cv, T, 29.8, 31.8, 22, (xx - 40, yy + 60, 100, 20), SAND, seed=72, size=(24, 50), rise=(10, 34), life=0.9, alpha=0.32, wind=(60, 0)); fin(cv, T, 709, 0.45)


# 10 a small creature
def shot_creature(cv, T):
    wc = cam(T, 31.6, 34.7, (900, 400, 1.5), (880, 410, 1.6), 'pr_rocks', cv=cv)
    lx = lerp(700, 300, ev(T, 32.2, 33.6))
    lizard(cv, lx, 590, 3.0, T, -1)
    k = ev(T, 33.2, 34.0)
    draw_people(cv, [person(wc, 'p', 1080, 600, 1.05, -1, 0.3, pose={'aL': 8, 'aR': 8 + 60 * k, 'fR': 40 * k, 'head': 24, 'lean': 14})], T)
    fin(cv, T, 710, 0.5)


# 11 bats in an old shelter
BATS = [(640, 150, 1.3), (720, 130, 1.1), (800, 160, 1.4), (900, 140, 1.2), (980, 165, 1.3), (860, 120, 1.0)]


def shot_bats(cv, T):
    wc = cam(T, 34.3, 38.2, (760, 336, 1.2), (840, 336, 1.35), 'pr_inside', cv=cv)
    up = ev(T, 34.8, 35.5)
    draw_people(cv, [person(wc, 'p', 760, 620, 1.2, 1, 0.3, pose={'aL': 8 + 70 * up, 'fL': 30 * up, 'aR': 8, 'head': -18 * up, 'lean': -2 * up})], T)
    for i, (bx, by, bs) in enumerate(BATS):
        t0 = 36.0 + 0.2 * i; x, y = wc.pt(bx, by)
        if T < t0: bat(cv, x, y, bs * wc.z, T, hang=True)
        else:
            f = T - t0; bat(cv, x + 90 * f * (1 + 0.1 * i) + 40 * math.sin(f * 5), y + 20 * f - 40 * f * f + 30 * math.sin(f * 7 + i), 1.1 * wc.z, T, i, alpha=clamp(1 - f / 1.8))
    fin(cv, T, 711, 0.55, True, 18)


# 12 the marabout shrine
def shot_shrine(cv, T):
    wc = cam(T, 37.8, 41.4, (800, 336, 1.0), (980, 360, 1.3), 'pr_shrine', cv=cv)
    X = jog(300, 820, 38.0, 41.2, T)
    draw_people(cv, [person(wc, 'p', X, 540, 1.1, 1, 0.3, walk=1.0, pose={'aL': 12, 'aR': 12, 'lean': 8, 'head': 8})], T)
    cv[:] = heat_haze(cv, T, 1.2, 0.05, 2.4, 380, 560); fin(cv, T, 712, 0.4)


# 13 the shade
def shot_shade(cv, T):
    wc = cam(T, 41.0, 45.7, (860, 380, 1.5), (880, 390, 1.7), 'pr_shrine', cv=cv)
    sit = ev(T, 41.6, 42.6)
    draw_people(cv, [person(wc, 'p', 760, 535 + 18 * sit, 1.2, 1, 0.3, pose={'aL': 8 + 10 * sit, 'aR': 8, 'lean': 16 * sit, 'head': -8 * sit})], T)
    glowpt(cv, 1150, 50, 420, (200, 240, 255), 0.35); cv[:] = heat_haze(cv, T, 1.4, 0.05, 2.4, 100, 330); fin(cv, T, 713, 0.5)


# 14 any space away from the sun matters
def shot_relief(cv, T):
    wc = cam(T, 45.3, 51.6, (980, 420, 2.2), (900, 430, 2.4), 'pr_shrine', 0.8, cv=cv); cv[:] = cv2.GaussianBlur(cv, (0, 0), 3)
    draw_items(cv, IDM, [pc('p', 640, 730, 0.62, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': -8 + 5 * math.sin(T * 0.8), 'lean': 10})], T)
    glowpt(cv, 1100, 40, 360, (200, 240, 255), 0.45); motes(cv, T, 714, 24, 0.4, (200, 235, 255), 0.9); fin(cv, T, 714, 0.55, False)


# 15 inside: not comfortable, not safe
def shot_inside(cv, T):
    wc = cam(T, 51.2, 54.6, (800, 360, 1.2), (900, 360, 1.3), 'pr_inside', cv=cv)
    draw_people(cv, [person(wc, 'p', 1000, 620, 1.2, -1, 0.3, pose={'aL': 8, 'aR': 8, 'lean': 14, 'head': 14 + 3 * math.sin(T * 1.2)})], T)
    motes(cv, T, 715, 40, 0.3, (170, 215, 255), 0.7); fin(cv, T, 715, 0.6, False)


# 16 in the doorway: no guaranteed water or food
def shot_door(cv, T):
    wc = cam(T, 54.2, 59.7, (1100, 400, 1.3), (1230, 420, 1.75), 'pr_inside', cv=cv)
    draw_people(cv, [person(wc, 'p', 1180, 600, 1.2, 1, 0.3, gain=0.55, pose={'aL': 8, 'aR': 8, 'lean': 8, 'head': 12 + 6 * math.sin(T * 0.9)})], T)
    glowpt(cv, *wc.pt(1250, 340), 200 * wc.z, (210, 240, 255), 0.25); fin(cv, T, 716, 0.6, False)


# 17 close-up: he is not sure anyone will find him before his body collapses
def shot_face(cv, T):
    wc = cam(T, 59.3, 64.5, (1000, 400, 2.4), (1020, 400, 2.6), 'pr_inside', 0.7, cv=cv); cv[:] = cv2.GaussianBlur(cv, (0, 0), 4)
    draw_items(cv, IDM, [pc('p', 640, 735, 0.66, 1, 0.3, sway=2.0, pose={'aL': 8 + 110 * ev(T, 61.0, 61.8), 'fL': 140 * ev(T, 61.0, 61.8), 'aR': 8, 'head': 10 + 8 * math.sin(T * 1.6), 'lean': 8})], T)
    vignette(cv, 0.25 + 0.4 * (0.5 + 0.5 * math.sin(T * 1.6)), 2.0); fin(cv, T, 717, 0.6, False)


# 18 the search continues: aerial view, a helicopter sweeps the dunes
def shot_aerial(cv, T):
    k = seg(T, 64.0, 69.8); wc = WC(lerp(700, 900, k), 336, 1.0); wc.draw(cv, 'pr_aerial', 0.95)
    hx = lerp(-100, 1380, ev(T, 64.6, 69.4)); hy = 250 + 30 * math.sin(T * 0.8)
    ov = cv.copy(); cv2.ellipse(ov, (int(hx - 30), int(hy + 320)), (110, 28), 0, 0, 360, (30.0, 40.0, 60.0), -1, cv2.LINE_AA); cv[:] = cv * 0.78 + ov * 0.22
    heli(cv, hx, hy, 0.30, T, 1, 2); fin(cv, T, 718, 0.4)


# 19 his traces on the ground are erased
def shot_traces(cv, T):
    wc = cam(T, 69.3, 72.2, (840, 420, 1.5), (900, 420, 1.5), 'pr_empty', cv=cv)
    prints(cv, wc, TRK, 1.0 - 0.9 * ev(T, 69.8, 71.8), (28.0, 60.0, 105.0))
    puffs(cv, T, 69.5, 72.2, 30, (200, 580, 900, 50), SAND, seed=73, size=(50, 110), rise=(0, 8), life=1.3, alpha=0.3, wind=(-230, 0)); fin(cv, T, 719, 0.45)


# 20 not enough to lead the rescuers to him
def shot_notenough(cv, T):
    wc = WC(900, 336, 1.0); wc.draw(cv, 'pr_aerial', 0.95)
    pts = [(1180 - 11 * i + 10 * math.sin(i * 0.8), 520 + 6.5 * i + 4 * math.sin(i * 1.1)) for i in range(30)]
    n = int(ev(T, 72.3, 74.2) * len(pts))
    for (X, Y) in pts[:n]: cv2.circle(cv, (int(X), int(Y)), 4, (28.0, 55.0, 95.0), -1, cv2.LINE_AA)
    hx = lerp(1300, -100, ev(T, 72.2, 75.1)); heli(cv, hx, 160, 0.14, T, -1, 0)
    fin(cv, T, 720, 0.45)


# 21 the vast desert
def shot_vast(cv, T):
    k = seg(T, 74.8, 79.1); wc = WC(900, lerp(250, 336, k), lerp(2.0, 1.0, ease_out(k))); wc.draw(cv, 'pr_aerial', 0.92)
    x, y = wc.pt(780, 500); b = 0.5 + 0.5 * math.sin(T * 5)
    cv2.circle(cv, (int(x), int(y)), 7, (40.0, 40.0, 220.0), -1, cv2.LINE_AA); glowpt(cv, x, y, 50, (60, 60, 255), 0.55 * b); tone(cv, 1.0, 0, (0.95, 0.98, 1.04), 1.0); fin(cv, T, 721, 0.55)


# 22 every extra day: the sky turns (time-lapse of the night)
def shot_nightfall(cv, T):
    wc = cam(T, 78.7, 80.6, (800, 336, 1.1), (800, 336, 1.1), 'pr_night', cv=cv)
    draw_people(cv, [person(wc, 'p', 800, 640, 1.2, 1, 0.3, pose={'aL': 8, 'aR': 8, 'lean': 10, 'head': 10}, tint=(1.0, 0.9, 0.82))], T)
    fin(cv, T, 722, 0.5)


# 23 the body and the mind deteriorate
def shot_decline(cv, T):
    wc = cam(T, 80.2, 85.5, (800, 400, 1.9), (800, 400, 2.1), 'pr_night', cv=cv)
    sh = math.sin(T * 17) * 1.2
    draw_items(cv, IDM, [pc('p', 640 + sh, 730, 0.64, 1, 0.3, sway=1.5, tint=(0.82, 0.92, 1.1), pose={'aL': 8, 'aR': 8, 'lean': 22, 'head': 26 + 4 * math.sin(T * 1.4)})], T)
    xx = 640; puffs(cv, T, 80.6, 85.4, 14, (xx - 10, 160, 40, 20), (225, 225, 235), seed=74, size=(30, 60), rise=(14, 40), life=1.4, alpha=0.18, wind=(-20, 0)); fin(cv, T, 723, 0.6, False)


# 24 nobody near
def shot_nobody(cv, T):
    k = seg(T, 85.1, 87.2); wc = WC(800, 336, lerp(1.6, 1.0, ease_out(k))); wc.draw(cv, 'pr_night')
    draw_people(cv, [person(wc, 'p', 800, 590, 0.8, 1, 0.3, tint=(0.82, 0.92, 1.1), pose={'aL': 8, 'aR': 8, 'lean': 16, 'head': 20})], T); fin(cv, T, 724, 0.6)


# 25 the crossroads of decisions
def shot_fork(cv, T):
    wc = cam(T, 86.7, 93.2, (800, 336, 1.15), (800, 336, 1.3), 'pr_dawn', cv=cv)
    lk = math.sin((T - 87.5) * 1.6) * 24 * ev(T, 87.4, 88.0) * (1 - ev(T, 91.0, 91.6))
    draw_people(cv, [person(wc, 'p', 800, 640, 1.3, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': lk, 'lean': 4})], T)
    for sg, col, hi in ((-1, (80.0, 200.0, 255.0), 0.0), (1, (80.0, 200.0, 255.0), 1.0)):
        f = ev(T, 88.2, 91.0); n = int(f * 16)
        for i in range(n):
            u = (i + 1) / 16.0; X = 800 + sg * u * 520; Y = lerp(620.0, 470.0, u ** 0.8)
            x, y = wc.pt(X, Y); r_ = max(3, int(16 * (1 - u * 0.7) * wc.z)); cv2.circle(cv, (int(x), int(y)), r_, col, -1, cv2.LINE_AA); cv2.circle(cv, (int(x), int(y)), r_, (30.0, 90.0, 160.0), 2, cv2.LINE_AA)
    glowpt(cv, *wc.pt(1280, 470), 80 * wc.z, (120, 220, 255), 0.4 * ev(T, 91.0, 92.0)); fin(cv, T, 725, 0.4)


# 26 he rises
def shot_rise(cv, T):
    wc = cam(T, 92.8, 95.4, (800, 380, 1.5), (800, 360, 1.4), 'pr_dawn', cv=cv)
    up = ev(T, 93.1, 94.3)
    draw_people(cv, [person(wc, 'p', 800, 640 + 130 * (1 - up), 1.3, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 20 * (1 - up), 'lean': 28 * (1 - up)})], T); fin(cv, T, 726, 0.4)


# 27 he walks on with no perfect plan
def shot_go(cv, T):
    wc = cam(T, 94.9, 99.0, (700, 336, 1.2), (1000, 336, 1.2), 'pr_dawn', cv=cv)
    X = jog(620, 1000, 95.1, 98.8, T)
    draw_people(cv, [person(wc, 'p', X, 640, 1.3, 1, 0.3, walk=1.0, pose={'aL': 12, 'aR': 12, 'lean': 10, 'head': 6})], T)
    xx, yy = wc.pt(X, 650); puffs(cv, T, 95.1, 98.8, 14, (xx - 140, yy - 8, 120, 14), SAND, seed=75, size=(24, 50), rise=(8, 24), life=1.0, alpha=0.28, wind=(-100, 0)); fin(cv, T, 727, 0.35)


# 28 searching the horizon for any sign: a mirage shimmers
def shot_mirage(cv, T):
    k = seg(T, 98.5, DP5); wc = WC(lerp(780, 860, k), 336, lerp(1.2, 1.5, k)); wc.draw(cv, 'pr_empty', 1.0)
    hx, hy = wc.pt(1080, 300); mirage(cv, hy, hx - 230 * wc.z, hx + 230 * wc.z, ev(T, 100.0, 102.5), T)
    sh = ev(T, 99.0, 99.8)
    draw_people(cv, [person(wc, 'p', 640, 640, 1.3, 1, 0.3, pose={'aL': 8 + 110 * sh, 'fL': 140 * sh, 'aR': 8, 'head': 8 * math.sin((T - 99.8) * 1.4) * sh + 6, 'lean': 8})], T)
    cv[:] = heat_haze(cv, T, 2.2, 0.05, 3.0, 300, 640); glowpt(cv, 1050, 70, 360, (200, 240, 255), 0.35); fin(cv, T, 728, 0.5)


SHOTS5 = [('days', 0.0, 1.5, shot_days, 0.0), ('bubble5', 1.5, 4.3, shot_bubble5, 0.2), ('battle', 4.3, 7.4, shot_battle, 0.3), ('bottle5', 7.4, 9.8, shot_bottle5, 0.3), ('weak', 9.8, 15.0, shot_weak, 0.3),
          ('fluid', 15.0, 20.2, shot_fluid, 0.4), ('notice', 20.2, 25.5, shot_notice, 0.4), ('chance5', 25.5, 29.2, shot_chance5, 0.3), ('dig', 29.2, 31.8, shot_dig, 0.3), ('creature', 31.8, 34.5, shot_creature, 0.3),
          ('bats', 34.5, 38.0, shot_bats, 0.3), ('shrine', 38.0, 41.2, shot_shrine, 0.3), ('shade', 41.2, 45.5, shot_shade, 0.3), ('relief', 45.5, 51.4, shot_relief, 0.3), ('inside', 51.4, 54.4, shot_inside, 0.3),
          ('door', 54.4, 59.5, shot_door, 0.4), ('face', 59.5, 64.3, shot_face, 0.4), ('aerial', 64.3, 69.5, shot_aerial, 0.4), ('traces', 69.5, 72.0, shot_traces, 0.3), ('notenough', 72.0, 75.0, shot_notenough, 0.3),
          ('vast', 75.0, 78.9, shot_vast, 0.3), ('nightfall', 78.9, 80.4, shot_nightfall, 0.5), ('decline', 80.4, 85.3, shot_decline, 0.4), ('nobody', 85.3, 86.9, shot_nobody, 0.3), ('fork', 86.9, 93.0, shot_fork, 0.5),
          ('rise', 93.0, 95.1, shot_rise, 0.2), ('go', 95.1, 98.7, shot_go, 0.3), ('mirage', 98.7, DP5, shot_mirage, 0.4)]


class PartP5(P2.PartP2):
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTS5):
            hi = t1 + (SHOTS5[i + 1][4] / 2 if i + 1 < len(SHOTS5) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTS5) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
