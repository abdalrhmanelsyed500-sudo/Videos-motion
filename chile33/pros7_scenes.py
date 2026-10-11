"""Prosperi video PART 7 (Arabic, 80.7 s): the surprise - he ended up in Algeria ~291 km from the race route; why the search failed; the hospital and the weight loss; the waiting family; the lesson.
Same oil layered-puppet system. NO face mark, NO captions, NO music. New character f = his wife (cut by prepare_pros7.py; same rig as m)."""
from pros6_scenes import *
import pros6_scenes as P6
import hook_scenes as HK
HK.RIG['f'] = HK.RIG['m']

DP7 = 80.72
START = ROUTE[0]; FAR = (1450, 462)
WHITE = (1.7, 1.7, 1.75)


def mapcam(cv, T, t0, t1, c0, c1, gain=1.0): return cam(T, t0, t1, c0, c1, 'pr_map', gain, cv=cv)


def dashed(cv, wc, a, b, k, col=(30.0, 45.0, 120.0), n=26, r=4):
    for j in range(n):
        if j / n > k: break
        x, y = wc.pt(lerp(a[0], b[0], j / n), lerp(a[1], b[1], j / n)); cv2.circle(cv, (int(x), int(y)), r, col, -1, cv2.LINE_AA)


def person_disc(cv, x, y, a, r=44):
    if a > 0.02: disc(cv, x, y, r, a * 0.92); icon_person(cv, x, y + 6, 1.3, a)


# 1 he was not near the race route as he imagined
def shot_near(cv, T):
    wc = mapcam(cv=cv, T=T, t0=0, t1=3.4, c0=(800, 336, 1.0), c1=(900, 380, 1.2))
    route_overlay(cv, wc, T, 0.2, 2.4)
    x, y = wc.pt(950, 556); a = ev(T, 1.0, 1.8); ring(cv, x, y, 90 * wc.z, a * (0.7 + 0.3 * math.sin(T * 4)), (200.0, 140.0, 40.0)); person_disc(cv, x, y - 80, a)
    fin(cv, T, 901, 0.4)


# 2 nor was he lost a few km from the right road: a short gap that is proven wrong
def shot_km(cv, T):
    wc = mapcam(cv=cv, T=T, t0=3.2, t1=7.2, c0=(950, 500, 1.4), c1=(950, 500, 1.4))
    route_overlay(cv, wc, T, 0, 0.01)
    p0 = (950, 556); p1 = (1020, 520); k = ev(T, 3.6, 4.6) * (1 - ev(T, 6.0, 6.8))
    dashed(cv, wc, p0, p1, k, (200.0, 140.0, 40.0), 8, 5)
    x0, y0 = wc.pt(*p0); x1, y1 = wc.pt(*p1); pin(cv, x0, y0, 1.3 * wc.z, ev(T, 3.5, 4.0) * (1 - ev(T, 6.2, 6.8))); pin(cv, x1, y1, 1.3 * wc.z, ev(T, 4.4, 4.9) * (1 - ev(T, 6.2, 6.8)))
    fin(cv, T, 902, 0.4)


# 3 after they re-determined his position: a pin falls on the true location
def shot_relocate(cv, T):
    wc = mapcam(cv=cv, T=T, t0=6.9, t1=9.2, c0=(1000, 420, 1.1), c1=(1100, 430, 1.2))
    route_overlay(cv, wc, T, 0, 0.01)
    x, y = wc.pt(*FAR); f = ev(T, 7.6, 8.3); yy = lerp(-60, y, f * f)
    pin(cv, x, yy, 1.6 * wc.z, 1.0); ring(cv, x, y, 160 * wc.z * ev(T, 8.3, 8.8), ev(T, 8.3, 8.8) * (0.7 + 0.3 * math.sin(T * 4)))
    fin(cv, T, 903, 0.4)


# 4 Algeria
def shot_algeria(cv, T):
    wc = mapcam(cv=cv, T=T, t0=8.7, t1=13.4, c0=(1100, 430, 1.2), c1=(1190, 440, 1.5))
    route_overlay(cv, wc, T, 0, 0.01)
    x, y = wc.pt(*FAR); pin(cv, x, y, 1.6 * wc.z, 1.0); ring(cv, x, y, 170 * wc.z, 0.7 + 0.3 * math.sin(T * 4))
    person_disc(cv, x + 150 * wc.z, y - 110 * wc.z, ev(T, 10.0, 10.8))
    fin(cv, T, 904, 0.4)


# 5 about 291 km from the original route
def shot_dist(cv, T):
    wc = mapcam(cv=cv, T=T, t0=13.2, t1=15.6, c0=(1040, 440, 1.0), c1=(1040, 440, 1.05))
    route_overlay(cv, wc, T, 0, 0.01)
    k = ev(T, 13.4, 14.8); dashed(cv, wc, START, FAR, k, (30.0, 45.0, 150.0), 36, 5)
    xs, ys = wc.pt(*START); xf, yf = wc.pt(*FAR); pin(cv, xs, ys, 1.1 * wc.z, 1.0); pin(cv, xf, yf, 1.6 * wc.z, 1.0)
    for j in range(0, 37, 6):
        if j / 36 <= k: tx, ty = wc.pt(lerp(START[0], FAR[0], j / 36), lerp(START[1], FAR[1], j / 36)); cv2.line(cv, (int(tx), int(ty) - 14), (int(tx), int(ty) + 14), (30.0, 45.0, 150.0), 3, cv2.LINE_AA)
    fin(cv, T, 905, 0.4)


# 6 the man who started his fourth day as a marathon runner
def shot_racer(cv, T):
    wc = cam(T, 15.3, 21.0, (780, 336, 1.15), (860, 336, 1.15), 'pr_race', cv=cv)
    items = [person(wc, 'p', 700, 620, 1.15, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 4 * math.sin(T * 1.2)})]
    for i in range(5):
        X = 500 + 40 * i + max(0, T - 17.4) * (60 + 15 * i) * ev(T, 17.4, 18.0)
        items.append(person(wc, 'r', X, 560 + 24 * (i % 3), 1.0, 1, i * 1.3, walk=ev(T, 17.4, 18.0), pose={'aL': 14, 'aR': 14}, shirt=RSH[i % 6]))
    draw_people(cv, items, T); fin(cv, T, 906, 0.35)


# 7 ... ended in another country (border)
def shot_border(cv, T):
    wc = cam(T, 20.5, 22.8, (700, 336, 1.2), (950, 336, 1.2), 'pr_border', cv=cv)
    X = jog(450, 1050, 20.7, 22.8, T)
    draw_people(cv, [person(wc, 'p', X, 600, 1.15, 1, 0.3, walk=1.0, pose={'aL': 14, 'aR': 14, 'lean': 8, 'head': 10})], T); fin(cv, T, 907, 0.4)


# 8 lost direction during the storm
def shot_storm7(cv, T):
    wc = cam(T, 22.3, 26.6, (800, 336, 1.2), (800, 336, 1.3), 'pr_storm', cv=cv)
    fl = 1 if (T < 23.4 or T > 24.8) else -1
    draw_people(cv, [person(wc, 'p', 800, 620, 1.2, fl, 0.3, walk=0.6, sway=2.0, pose={'aL': 20, 'aR': 20, 'lean': 14, 'head': 18 * math.sin(T * 2.4)})], T)
    sand(cv, T, 0.8, 99, 1.0, 0.8); qmark(cv, 820, 150, 120, 0.8 * ev(T, 23.0, 23.6)); fin(cv, T, 908, 0.4)


# 9 he kept moving huge distances without knowing where
def shot_huge(cv, T):
    k = seg(T, 26.2, 29.2); wc = WC(lerp(500, 1000, k), 336, 1.1); wc.draw(cv, 'pr_empty', 1.0)
    X = lerp(420, 920, k)
    pts = [(420 + 30 * i, 650 + 6 * math.sin(i), 9) for i in range(int((X - 420) / 30))]
    prints(cv, wc, pts, 0.85)
    draw_people(cv, [person(wc, 'p', X, 640, 1.2, 1, 0.3, walk=1.0, pose={'aL': 14, 'aR': 14, 'lean': 10, 'head': 10})], T)
    cv[:] = heat_haze(cv, T, 2.0, 0.05, 3.0, 300, 660); fin(cv, T, 909, 0.4)


# 10 why the search was so difficult: the search zone is the race area while he is far away
def shot_zone(cv, T):
    wc = mapcam(cv=cv, T=T, t0=28.9, t1=33.2, c0=(900, 440, 1.0), c1=(820, 470, 1.15))
    route_overlay(cv, wc, T, 0, 0.01)
    xs, ys = wc.pt(*START); a = ev(T, 29.4, 30.2)
    ring(cv, xs + 160 * wc.z, ys - 40 * wc.z, 330 * wc.z, a); ring(cv, xs + 160 * wc.z, ys - 40 * wc.z, 336 * wc.z, a)
    heli_icons(cv, wc, T, 30.0, 33.0)
    xf, yf = wc.pt(*FAR); pin(cv, xf, yf, 1.4 * wc.z, ev(T, 31.0, 31.8)); fin(cv, T, 910, 0.4)


# 11 he had moved far from the expected place
def shot_far(cv, T):
    wc = mapcam(cv=cv, T=T, t0=32.8, t1=36.6, c0=(820, 470, 1.15), c1=(1100, 450, 1.1))
    route_overlay(cv, wc, T, 0, 0.01)
    xs, ys = wc.pt(*START); ring(cv, xs + 160 * wc.z, ys - 40 * wc.z, 330 * wc.z, 1.0); ring(cv, xs + 160 * wc.z, ys - 40 * wc.z, 336 * wc.z, 1.0)
    heli_icons(cv, wc, T, 33.0, 36.5)
    k = ev(T, 33.4, 35.6); dashed(cv, wc, (START[0] + 300, START[1] - 40), FAR, k, (30.0, 45.0, 220.0), 24, 7)
    xf, yf = wc.pt(*FAR); pin(cv, xf, yf, 1.5 * wc.z, 1.0); person_disc(cv, xf, yf - 120 * wc.z, ev(T, 35.0, 35.8)); fin(cv, T, 911, 0.4)


# 12 outside the usual search area: the plane passes, he is a tiny dot far away
def shot_scope(cv, T):
    wc = cam(T, 36.2, 40.8, (800, 336, 1.0), (900, 336, 1.15), 'pr_aerial', cv=cv)
    x, y = wc.pt(1300, 420); glowpt(cv, x, y, 80 * wc.z, (60, 60, 255), 0.35 * ev(T, 37.0, 38.0)); cv2.circle(cv, (int(x), int(y)), 11, (245.0, 245.0, 245.0), -1, cv2.LINE_AA); cv2.circle(cv, (int(x), int(y)), 8, (40.0, 40.0, 220.0), -1, cv2.LINE_AA); ring(cv, x, y, (40 + 25 * math.sin(T * 4)) * wc.z, ev(T, 37.0, 38.0))
    k = seg(T, 37.0, 40.4); hx = lerp(1300, 200, k); heli(cv, hx, 200 + 30 * math.sin(T), 0.28, T, -1, 0.0)
    fin(cv, T, 912, 0.4)


# 13 hospital: dehydration and injuries
def shot_hosp(cv, T):
    wc = cam(T, 40.4, 46.2, (800, 336, 1.0), (850, 336, 1.1), 'pr_hospital', cv=cv)
    s = math.sin(T * 1.1)
    draw_people(cv, [person(wc, 'p', 850, 620, 1.1, -1, 0.3, pose={'aL': 8, 'aR': 8, 'lean': 10 + 3 * s, 'head': 12 + 3 * s})], T)
    xx, yy = wc.pt(805, 190); drops(cv, T, xx, yy, 7, 3, 0.7); fin(cv, T, 913, 0.35)


# 14 he lost a lot of weight: bathroom scale needle drops
def shot_weight(cv, T):
    wc = cam(T, 45.9, 50.8, (850, 336, 1.1), (850, 336, 1.1), 'pr_hospital', cv=cv)
    cx, cy = 1000, 600; a = ev(T, 46.4, 47.2)
    draw_people(cv, [person(wc, 'p', 700, 620, 1.1, 1, 0.3, pose={'aL': 8, 'aR': 8, 'lean': 10, 'head': 8 + 2 * math.sin(T)})], T)
    ov = cv.copy(); cv2.ellipse(ov, (cx, cy + 40), (130, 34), 0, 0, 360, (200.0, 205.0, 210.0), -1, cv2.LINE_AA); cv2.ellipse(ov, (cx, cy + 40), (130, 34), 0, 0, 360, (60.0, 70.0, 90.0), 3, cv2.LINE_AA)
    cv2.circle(ov, (cx, cy + 40), 22, (240.0, 240.0, 235.0), -1, cv2.LINE_AA); ang = lerp(-0.2, -2.6, ev(T, 47.4, 49.6)) + 0.04 * math.sin(T * 9)
    cv2.line(ov, (cx, cy + 40), (int(cx + 18 * math.cos(ang)), int(cy + 40 + 18 * math.sin(ang))), (30.0, 40.0, 200.0), 3, cv2.LINE_AA); cv[:] = cv * (1 - a) + ov * a
    fin(cv, T, 914, 0.35)


# 15 a long time to recover: days and nights cycle
def shot_recover(cv, T):
    wc = cam(T, 50.4, 53.4, (800, 336, 1.1), (780, 336, 1.15), 'pr_hospital', cv=cv)
    ph = (T - 50.6) / 1.4 * math.pi; night = 0.5 - 0.5 * math.cos(ph)
    draw_people(cv, [person(wc, 'p', 850, 620, 1.1, -1, 0.3, pose={'aL': 8, 'aR': 8, 'lean': 14, 'head': 14 + 2 * math.sin(T)})], T)
    tone(cv, 1.0, -18 * night, (1.0 - 0.18 * night, 1.0 - 0.1 * night, 1.0 + 0.1 * night), 1.0 - 0.2 * night); fin(cv, T, 915, 0.4)


# 16 the family: his wife waits and paces near the phone, days pass
def shot_family(cv, T):
    wc = cam(T, 52.9, 60.6, (800, 336, 1.0), (640, 336, 1.2), 'pr_home', cv=cv)
    X = 640 + 140 * math.sin((T - 53.0) * 0.55); fl = 1 if math.cos((T - 53.0) * 0.55) > 0 else -1
    draw_people(cv, [person(wc, 'f', X, 600, 1.35, fl, 0.3, walk=0.7, pose={'aL': 14, 'aR': 14, 'lean': 4, 'head': 8})], T)
    dk = 0.5 - 0.5 * math.cos(seg(T, 53.0, 60.6) * 6.28 * 1.5); tone(cv, 1.0, -10 * dk, (1.0 - 0.14 * dk, 1.0 - 0.08 * dk, 1.0 + 0.05 * dk), 1.0); fin(cv, T, 916, 0.4)


# 17 imagine waiting for a call from someone at a race
def shot_call(cv, T):
    wc = cam(T, 60.3, 64.2, (340, 400, 1.7), (320, 400, 2.0), 'pr_home', cv=cv)
    xx, yy = wc.pt(165, 430)
    for i in range(3):
        ph = ((T * 1.6 + i / 3.0) % 1.0); cv2.ellipse(cv, (int(xx + 20), int(yy - 30)), (int(30 + 70 * ph), int(20 + 50 * ph)), 0, 200, 340, (60.0, 160.0, 230.0), 3, cv2.LINE_AA)
    draw_items(cv, IDM, [pc('f', 1000, 800, 0.62, -1, 0.4, pose={'aL': 8, 'aR': 8 + 55 * ev(T, 61.0, 62.0), 'fR': 50 * ev(T, 61.0, 62.0), 'head': 10})], T)
    bubble(cv, 760, 190, 150, 'pr_race', (40, 250, 640, 650), ev(T, 61.2, 62.0)); fin(cv, T, 917, 0.4)


# 18 the sports trip turns into a search for a missing person in one of the hardest places on earth
def shot_missing(cv, T):
    wc = cam(T, 63.9, 69.5, (320, 400, 2.0), (500, 400, 1.7), 'pr_home', cv=cv)
    h = ev(T, 64.5, 65.5)
    draw_items(cv, IDM, [pc('f', 1000, 800, 0.62, -1, 0.4, pose={'aL': 8 + 110 * h, 'fL': 140 * h, 'aR': 8 + 110 * h, 'fR': 140 * h, 'head': 22 * h, 'lean': 8 * h})], T)
    a = ev(T, 64.6, 65.4) * (1 - ev(T, 68.6, 69.4)); bubble(cv, 700, 190, 150, 'pr_aerial', (300, 100, 900, 650), a)
    if a > 0.02: heli(cv, lerp(620, 780, seg(T, 65.5, 68.8)), 190, 0.17, T, 1, 0.0, alpha=a)
    fin(cv, T, 918, 0.45)


# 19 not just a story of a runner who lost the road
def shot_notjust(cv, T):
    wc = cam(T, 69.0, 73.8, (800, 336, 1.2), (800, 336, 1.0), 'pr_dawn', cv=cv)
    k = seg(T, 69.3, 73.6); X = lerp(700, 980, k); Y = lerp(640, 560, k)
    draw_people(cv, [person(wc, 'p', X, Y, 1.2 - 0.5 * k, 1, 0.3, walk=1.0, pose={'aL': 12, 'aR': 12, 'lean': 8, 'head': 6})], T)
    glowpt(cv, *wc.pt(585, 262), 420 * wc.z, (150, 220, 255), 0.25); fin(cv, T, 919, 0.35)


# 20 a simple decision: continue in the wrong direction
def shot_wrong(cv, T):
    wc = cam(T, 73.4, 78.1, (800, 336, 1.25), (800, 336, 1.25), 'pr_dawn', cv=cv)
    for sg, col in ((-1, (80.0, 200.0, 90.0)), (1, (40.0, 40.0, 215.0))):
        f = ev(T, 74.2, 76.0)
        for i in range(int(f * 14)):
            u = (i + 1) / 14.0; x, y = wc.pt(800 + sg * u * 420, lerp(560.0, 440.0, u ** 0.8)); cv2.circle(cv, (int(x), int(y)), max(3, int(14 * (1 - u * 0.6) * wc.z)), col, -1, cv2.LINE_AA)
    ar = ev(T, 76.0, 76.8); x0, y0 = wc.pt(930, 520); x1, y1 = wc.pt(1200, 470)
    if ar > 0.02: cv2.arrowedLine(cv, (int(x0), int(y0)), (int(lerp(x0, x1, ar)), int(lerp(y0, y1, ar))), (30.0, 30.0, 200.0), 8, cv2.LINE_AA, 0, 0.3)
    X = jog(800, 940, 76.0, 78.0, T)
    draw_people(cv, [person(wc, 'p', X, 570, 1.2, 1, 0.3, walk=ev(T, 76.0, 76.4), pose={'aL': 12, 'aR': 12, 'lean': 8, 'head': 10 * (1 - ev(T, 75.0, 76.0))})], T); fin(cv, T, 920, 0.35)


# 21 a chain of events that is hard to stop: pins appear one after another along the route to the far point
def shot_chain(cv, T):
    wc = mapcam(cv=cv, T=T, t0=77.8, t1=DP7, c0=(1040, 440, 1.05), c1=(1040, 440, 0.98))
    route_overlay(cv, wc, T, 0, 0.01)
    pts = [START, (790, 470), (950, 556), (1110, 468), (1290, 548), FAR]
    for i, p in enumerate(pts):
        a = ev(T, 78.0 + i * 0.35, 78.4 + i * 0.35); x, y = wc.pt(*p); pin(cv, x, y, 1.2 * wc.z, a)
        if i < len(pts) - 1 and a > 0.5:
            dashed(cv, wc, p, pts[i + 1], ev(T, 78.4 + i * 0.35, 78.9 + i * 0.35), (30.0, 45.0, 150.0), 12, 4)
    x, y = wc.pt(*FAR); ring(cv, x, y, 150 * wc.z, ev(T, 80.0, 80.4) * (0.7 + 0.3 * math.sin(T * 4))); fin(cv, T, 921, 0.4)


SHOTS7 = [('near', 0.0, 3.3, shot_near, 0.0), ('km', 3.3, 7.0, shot_km, 0.3), ('relocate', 7.0, 8.8, shot_relocate, 0.3), ('algeria', 8.8, 13.3, shot_algeria, 0.3), ('dist', 13.3, 15.4, shot_dist, 0.3),
          ('racer', 15.4, 20.7, shot_racer, 0.4), ('border', 20.7, 22.4, shot_border, 0.3), ('storm7', 22.4, 26.3, shot_storm7, 0.4), ('huge', 26.3, 29.0, shot_huge, 0.4), ('zone', 29.0, 33.0, shot_zone, 0.5),
          ('far', 33.0, 36.4, shot_far, 0.3), ('scope', 36.4, 40.5, shot_scope, 0.4), ('hosp', 40.5, 46.1, shot_hosp, 0.5), ('weight', 46.1, 50.6, shot_weight, 0.3), ('recover', 50.6, 53.0, shot_recover, 0.3),
          ('family', 53.0, 60.5, shot_family, 0.5), ('call', 60.5, 64.0, shot_call, 0.3), ('missing', 64.0, 69.3, shot_missing, 0.3), ('notjust', 69.3, 73.6, shot_notjust, 0.4), ('wrong', 73.6, 77.9, shot_wrong, 0.4),
          ('chain', 77.9, DP7, shot_chain, 0.4)]


class PartP7(P2.PartP2):
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTS7):
            hi = t1 + (SHOTS7[i + 1][4] / 2 if i + 1 < len(SHOTS7) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTS7) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
