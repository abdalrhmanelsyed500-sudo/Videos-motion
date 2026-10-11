"""Prosperi video PART 8 (Arabic, 63.8 s, final): the lesson (strength is not enough, courage is not lack of fear, admit the situation changed and find a new way), the storm that took him off route,
the closing question and the like / subscribe / comment call to action (procedural icons only, no text). Same oil layered-puppet system. NO face mark, NO captions, NO music."""
from pros7_scenes import *
import pros7_scenes as P7

DP8 = 63.79


def icon_thumb(cv, x, y, s, a=1.0):
    ov = cv.copy(); col = (245.0, 245.0, 245.0)
    cv2.rectangle(ov, (int(x - 30 * s), int(y - 6 * s)), (int(x - 14 * s), int(y + 28 * s)), col, -1)
    pts = np.array([(x - 10 * s, y - 4 * s), (x + 2 * s, y - 30 * s), (x + 12 * s, y - 28 * s), (x + 8 * s, y - 8 * s), (x + 32 * s, y - 8 * s), (x + 34 * s, y + 4 * s), (x + 28 * s, y + 28 * s), (x - 10 * s, y + 28 * s)], np.int32)
    cv2.fillConvexPoly(ov, pts, col, cv2.LINE_AA); cv[:] = cv * (1 - a) + ov * a


def icon_bell(cv, x, y, s, a=1.0):
    ov = cv.copy(); col = (245.0, 245.0, 245.0); sw = 6 * math.sin(a * 30) * (1 - a)
    cv2.ellipse(ov, (int(x), int(y - 4 * s)), (int(22 * s), int(24 * s)), 0, 180, 360, col, -1, cv2.LINE_AA)
    cv2.rectangle(ov, (int(x - 22 * s), int(y - 4 * s)), (int(x + 22 * s), int(y + 14 * s)), col, -1)
    cv2.rectangle(ov, (int(x - 30 * s), int(y + 12 * s)), (int(x + 30 * s), int(y + 20 * s)), col, -1)
    cv2.circle(ov, (int(x), int(y + 28 * s)), int(6 * s), col, -1, cv2.LINE_AA); cv[:] = cv * (1 - a) + ov * a


def icon_comment(cv, x, y, s, a=1.0):
    ov = cv.copy(); col = (245.0, 245.0, 245.0)
    cv2.ellipse(ov, (int(x), int(y - 4 * s)), (int(34 * s), int(24 * s)), 0, 0, 360, col, -1, cv2.LINE_AA)
    cv2.fillConvexPoly(ov, np.array([(x - 18 * s, y + 12 * s), (x - 24 * s, y + 32 * s), (x, y + 18 * s)], np.int32), col, cv2.LINE_AA)
    for dx in (-14, 0, 14): cv2.circle(ov, (int(x + dx * s), int(y - 4 * s)), int(4 * s), (60.0, 60.0, 60.0), -1, cv2.LINE_AA)
    cv[:] = cv * (1 - a) + ov * a


def badge(cv, x, y, r, a, col, fn):
    if a <= 0.02: return
    pop = 1.0 + 0.25 * math.sin(clamp(a) * math.pi) * (1 if a < 1 else 0)
    ov = cv.copy(); cv2.circle(ov, (int(x), int(y)), int(r * pop), col, -1, cv2.LINE_AA); cv2.circle(ov, (int(x), int(y)), int(r * pop), (255.0, 255.0, 255.0), 4, cv2.LINE_AA)
    cv[:] = cv * (1 - a) + ov * a; fn(cv, x, y + 4, r / 46.0 * pop, a)


# 1 a professional athlete: discipline and endurance
def shot_athlete(cv, T):
    wc = cam(T, 0, 3.8, (700, 336, 1.2), (900, 336, 1.2), 'pr_stadium', cv=cv)
    X = jog(450, 1000, 0.0, 3.8, T)
    draw_people(cv, [person(wc, 'p', X, 600, 1.2, 1, 0.3, walk=1.0, pose=RUN(T, 40, 30, 9.0, 8.0))], T); fin(cv, T, 1001, 0.35)


# 2 yet the desert cannot be beaten by physical strength alone: he flexes, the sun wins, he slumps
def shot_alone(cv, T):
    wc = cam(T, 3.5, 8.0, (800, 336, 1.3), (800, 336, 1.55), 'pr_empty', cv=cv)
    fx = ev(T, 3.8, 4.6) * (1 - ev(T, 5.4, 6.4)); sl = ev(T, 5.8, 7.4)
    draw_people(cv, [person(wc, 'p', 800, 640 + 40 * sl, 1.2, 1, 0.3, pose={'aL': 8 + 95 * fx, 'fL': 150 * fx, 'aR': 8 + 95 * fx, 'fR': 150 * fx, 'head': 20 * sl, 'lean': 22 * sl})], T)
    glowpt(cv, 1050, 70, 380, (200, 240, 255), 0.25 + 0.3 * ev(T, 5.0, 7.0)); cv[:] = heat_haze(cv, T, 2.2, 0.05, 3.0, 250, 660); vignette(cv, 0.3 + 0.4 * sl, 2.0); fin(cv, T, 1002, 0.4)


# 3 bigger than a race, bigger than a competition: the race bubble shrinks against the endless desert
def shot_bigger(cv, T):
    wc = cam(T, 7.8, 11.4, (800, 336, 1.7), (800, 336, 1.0), 'pr_empty', cv=cv)
    k = ev(T, 8.0, 10.6)
    draw_people(cv, [person(wc, 'p', 800, 620, 1.2 - 0.3 * k, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 8})], T)
    bubble(cv, 880, 170, 160 * (1 - 0.55 * k), 'pr_race', (40, 250, 640, 650), 1.0 - 0.3 * k); fin(cv, T, 1003, 0.35)


# 4 a harsh test of his ability to adapt: he shades his eyes at the huge dune
def shot_test(cv, T):
    wc = cam(T, 11.1, 15.8, (900, 336, 1.2), (780, 336, 1.45), 'pr_rocks', cv=cv)
    h = ev(T, 11.6, 12.4) * (1 - ev(T, 14.4, 15.2))
    draw_people(cv, [person(wc, 'p', 780, 640, 1.2, 1, 0.3, pose={'aL': 8 + 105 * h, 'fL': 140 * h, 'aR': 8, 'head': 4 * math.sin(T * 1.3), 'lean': 6})], T)
    cv[:] = heat_haze(cv, T, 1.8, 0.05, 3.0, 300, 660); glowpt(cv, 1050, 70, 380, (200, 240, 255), 0.4); fin(cv, T, 1004, 0.4)


# 5 courage is not the absence of fear, strength is not the absence of tiredness
def shot_courage(cv, T):
    wc = cam(T, 15.5, 21.7, (800, 340, 1.5), (800, 336, 1.3), 'pr_dawn', cv=cv)
    tr = math.sin(T * 24) * 1.2 * ev(T, 15.9, 16.6) * (1 - ev(T, 18.2, 18.8)); bend = ev(T, 18.6, 19.6) * (1 - ev(T, 20.0, 21.0))
    draw_people(cv, [person(wc, 'p', 800 + tr * 4, 640 + 25 * bend, 1.2, 1, 0.3, pose={'aL': 8 + 12 * tr, 'aR': 8 - 12 * tr, 'head': 4 + 8 * tr + 20 * bend, 'lean': 4 + 28 * bend})], T)
    glowpt(cv, *wc.pt(585, 262), 420 * wc.z, (150, 220, 255), 0.25); fin(cv, T, 1005, 0.4)


# 6 survival sometimes depends on admitting the situation has changed: he stops, lowers his arms
def shot_admit(cv, T):
    wc = cam(T, 21.4, 24.8, (800, 336, 1.25), (800, 336, 1.35), 'pr_dawn', cv=cv)
    st = ev(T, 21.8, 22.8)
    draw_people(cv, [person(wc, 'p', lerp(700, 800, st), 640, 1.2, 1, 0.3, walk=1.0 - st, pose={'aL': 14 * (1 - st) + 8, 'aR': 14 * (1 - st) + 8, 'head': 14 * st, 'lean': 8 + 6 * st})], T)
    fin(cv, T, 1006, 0.35)


# 7 stop repeating the same attempt: a looping trail is crossed out
def shot_loop(cv, T):
    wc = cam(T, 24.5, 27.5, (800, 336, 1.2), (800, 336, 1.2), 'pr_empty', cv=cv)
    n = int(ev(T, 24.7, 26.2) * 40)
    for i in range(n):
        an = i / 40.0 * 6.28 * 1.6; x, y = wc.pt(800 + 220 * math.cos(an), 560 + 70 * math.sin(an)); cv2.circle(cv, (int(x), int(y)), 7, (40.0, 62.0, 100.0), -1, cv2.LINE_AA)
    xf = ev(T, 26.3, 26.9)
    if xf > 0.02:
        x0, y0 = wc.pt(640, 470); x1, y1 = wc.pt(960, 650)
        cv2.line(cv, (int(x0), int(y0)), (int(lerp(x0, x1, xf)), int(lerp(y0, y1, xf))), (30.0, 30.0, 210.0), 10, cv2.LINE_AA); cv2.line(cv, (int(x1), int(y0)), (int(lerp(x1, x0, xf)), int(lerp(y0, y1, xf))), (30.0, 30.0, 210.0), 10, cv2.LINE_AA)
    draw_people(cv, [person(wc, 'p', 800, 560, 1.0, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 10})], T); fin(cv, T, 1007, 0.35)


# 8 find a new way that fits the reality: a green path opens, he turns and walks along it
def shot_newway(cv, T):
    wc = cam(T, 27.2, 30.0, (800, 336, 1.25), (950, 336, 1.25), 'pr_dawn', cv=cv)
    f = ev(T, 27.5, 29.0)
    for i in range(int(f * 18)):
        u = (i + 1) / 18.0; x, y = wc.pt(800 + u * 520, lerp(620.0, 470.0, u ** 0.8)); cv2.circle(cv, (int(x), int(y)), max(3, int(14 * (1 - u * 0.6) * wc.z)), (80.0, 200.0, 90.0), -1, cv2.LINE_AA)
    X = jog(780, 900, 28.4, 29.9, T)
    draw_people(cv, [person(wc, 'p', X, 600, 1.2, 1, 0.3, walk=ev(T, 28.4, 28.8), pose={'aL': 12, 'aR': 12, 'head': 4, 'lean': 6})], T); fin(cv, T, 1008, 0.35)


# 9 he entered the desert to test his limits, then one storm took him off the route
def shot_enter(cv, T):
    wc = cam(T, 29.6, 33.2, (700, 336, 1.2), (900, 336, 1.2), 'pr_race', cv=cv)
    X = jog(450, 950, 29.8, 33.0, T)
    draw_people(cv, [person(wc, 'p', X, 600, 1.15, 1, 0.3, walk=1.0, pose=RUN(T, 14, 8, 5.0, 8.0))], T); fin(cv, T, 1009, 0.35)


def shot_storm8(cv, T):
    wc = cam(T, 32.7, 37.5, (800, 336, 1.2), (800, 336, 1.3), 'pr_storm', cv=cv)
    X = lerp(760, 960, ev(T, 33.5, 37.0)); ar = ev(T, 34.0, 36.0)
    draw_people(cv, [person(wc, 'p', X, 620, 1.2, 1, 0.3, walk=0.7, sway=2.0, pose={'aL': 20, 'aR': 20, 'lean': 16, 'head': 10})], T)
    sand(cv, T, 0.5 + 0.4 * ev(T, 33.0, 35.0), 98, 1.0, 0.8)
    if ar > 0.02:
        x0, y0 = 300, 560; x1, y1 = 1100, 330; cv2.arrowedLine(cv, (x0, y0), (int(lerp(x0, x1, ar)), int(lerp(y0, y1, ar))), (30.0, 30.0, 200.0), 9, cv2.LINE_AA, 0, 0.18)
    fin(cv, T, 1010, 0.4)


# 10 after days of thirst, loneliness and exhaustion the journey ended in a meeting with people who saved his life
def shot_saved(cv, T):
    nm = ev(T, 39.3, 40.0)
    wc = cam(T, 37.3, 42.2, (800, 336, 1.3), (800, 400, 1.5), 'pr_empty', cv=cv)
    buf = np.zeros_like(cv); w2 = cam(T, 37.3, 42.2, (760, 400, 1.7), (680, 400, 1.7), 'pr_nomad', cv=buf)
    draw_people(cv, [person(wc, 'p', 800, 640 + 40 * (1 - ev(T, 38.4, 39.2)), 1.2, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 24, 'lean': 22})], T)
    draw_people(buf, [person(w2, 'p', 600, 630, 1.2, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 10, 'lean': 10}), person(w2, 'b', 820, 620, 1.15, -1, 0.3, pose={'aL': 8, 'aR': 8 + 70 * ev(T, 40.2, 41.0), 'fR': 30, 'head': 2}),
                      person(w2, 'q', 930, 626, 1.0, -1, 0.5, pose={'aL': 8, 'aR': 8})], T)
    cv *= (1 - nm); cv += buf * nm; fin(cv, T, 1011, 0.4)


# 11 the question: lost in the desert at night with no idea how far the nearest person is
def shot_question(cv, T):
    wc = cam(T, 41.6, 52.9, (800, 336, 1.15), (800, 336, 1.45), 'pr_night', cv=cv)
    fl = 1 if int((T - 42.0) / 2.2) % 2 == 0 else -1
    draw_people(cv, [person(wc, 'p', 800, 620, 1.1, fl, 0.3, pose={'aL': 8, 'aR': 8, 'head': 12 * math.sin(T * 1.3)})], T)
    a = ev(T, 44.0, 45.2); glowpt(cv, 800, 150, 140, (220, 160, 80), 0.4 * a); qmark(cv, 800, 150, 170, a * (0.85 + 0.15 * math.sin(T * 3)), (255, 215, 110))
    two = ev(T, 50.6, 51.6)
    if two > 0.02:
        for sg, col in ((-1, (80.0, 200.0, 90.0)), (1, (40.0, 40.0, 215.0))):
            for i in range(int(two * 10)):
                u = (i + 1) / 10.0; x, y = wc.pt(800 + sg * u * 380, lerp(545.0, 490.0, u)); cv2.circle(cv, (int(x), int(y)), max(3, int(12 * (1 - u * 0.5) * wc.z)), col, -1, cv2.LINE_AA)
    fin(cv, T, 1012, 0.45)


# 12 like, subscribe, comment (procedural icons only)
def shot_cta(cv, T):
    wc = cam(T, 52.4, DP8, (800, 336, 1.2), (900, 336, 1.1), 'pr_dawn', cv=cv)
    w = ev(T, 54.6, 55.2) * (1 - ev(T, 56.0, 56.6)); X = lerp(700, 960, ev(T, 61.0, 63.4))
    draw_people(cv, [person(wc, 'p', X, 620, 1.2 - 0.25 * ev(T, 61.0, 63.4), 1, 0.3, walk=ev(T, 61.0, 61.4), pose={'aL': 8 + 105 * w + 14 * math.sin(T * 7) * w, 'fL': 70 * w, 'aR': 8, 'head': 4})], T)
    badge(cv, 360, 190, 56, ev(T, 55.3, 55.8), (60.0, 60.0, 200.0), icon_thumb)
    badge(cv, 640, 190, 56, ev(T, 57.2, 57.7), (40.0, 40.0, 210.0), icon_bell)
    badge(cv, 920, 190, 56, ev(T, 59.2, 59.7), (190.0, 120.0, 40.0), icon_comment)
    glowpt(cv, *wc.pt(585, 262), 420 * wc.z, (150, 220, 255), 0.25); fin(cv, T, 1013, 0.35)


SHOTS8 = [('athlete', 0.0, 3.6, shot_athlete, 0.0), ('alone', 3.6, 7.8, shot_alone, 0.3), ('bigger', 7.8, 11.3, shot_bigger, 0.3), ('test', 11.3, 15.6, shot_test, 0.3), ('courage', 15.6, 21.5, shot_courage, 0.4),
          ('admit', 21.5, 24.6, shot_admit, 0.3), ('loop', 24.6, 27.3, shot_loop, 0.3), ('newway', 27.3, 29.8, shot_newway, 0.3), ('enter', 29.8, 32.9, shot_enter, 0.3), ('storm8', 32.9, 37.4, shot_storm8, 0.4),
          ('saved', 37.4, 41.8, shot_saved, 0.4), ('question', 41.8, 52.6, shot_question, 0.5), ('cta', 52.6, DP8, shot_cta, 0.5)]


class PartP8(P2.PartP2):
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTS8):
            hi = t1 + (SHOTS8[i + 1][4] / 2 if i + 1 < len(SHOTS8) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTS8) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
