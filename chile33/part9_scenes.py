"""Part 9 (Arabic, ~62.9 s) FINAL: the three numbers, the first decision (split the food, build a system, create roles, act as if the exit is possible),
survival began on day one, a story about people, then the like / subscribe / bell call to action. Reuses the locked scenes of parts 2-7 (time-remapped)
plus new shots. Same STYLE LOCK. No captions, no music."""
from part8_scenes import *
import part2_scenes as P2, part3_scenes as P3, part4_scenes as P4, part5_scenes as P5, part6_scenes as P6, part7_scenes as P7

D9 = 62.9


def SRC(mod, fn, s0, t0, rate=1.0):
    f = getattr(mod, fn)
    return lambda cv, T: f(cv, s0 + (T - t0) * rate)


# ---------------------------------------------------------------- icons (CTA)
def thumb(cv, cx, cy, s, a=1.0, fill=1.0, tilt=0.0):
    P_ = np.array([(28, 92), (28, 46), (44, 40), (56, 8), (68, 4), (76, 14), (70, 40), (96, 40), (101, 50), (96, 58), (100, 66), (95, 75), (96, 83), (88, 91), (80, 92)], np.float32) - (55, 50)
    c, sn = math.cos(math.radians(tilt)), math.sin(math.radians(tilt)); Rm = np.array([[c, -sn], [sn, c]], np.float32)
    pts = ((P_ @ Rm.T) * s + (cx, cy)).astype(np.int32)
    cuff = (np.array([(0, 46), (22, 46), (22, 94), (0, 94)], np.float32) - (55, 50)); cuff = ((cuff @ Rm.T) * s + (cx, cy)).astype(np.int32)
    sh = pts + np.array([int(6 * s / 3), int(8 * s / 3)])
    cv2.fillConvexPoly(cv, sh, (6.0, 8.0, 12.0), cv2.LINE_AA)
    col = (np.array((60.0, 190.0, 240.0)) * fill + np.array((70.0, 76.0, 90.0)) * (1 - fill)).tolist()
    cv2.fillPoly(cv, [pts], tuple(float(v) * a for v in col), cv2.LINE_AA); cv2.polylines(cv, [pts], True, (20.0, 40.0, 70.0), max(2, int(2.5 * s / 2)), cv2.LINE_AA)
    cv2.fillPoly(cv, [cuff], (150.0 * a, 90.0 * a, 40.0 * a), cv2.LINE_AA); cv2.polylines(cv, [cuff], True, (60.0, 30.0, 12.0), max(2, int(2.5 * s / 2)), cv2.LINE_AA)
    for yy in (50, 58, 66, 74, 82):
        p0 = (np.array((72, yy), np.float32) - (55, 50)) @ Rm.T * s + (cx, cy); p1 = (np.array((97, yy), np.float32) - (55, 50)) @ Rm.T * s + (cx, cy)
        cv2.line(cv, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), (30.0, 80.0, 130.0), max(1, int(s / 2.4)), cv2.LINE_AA)


def bell(cv, cx, cy, s, ang=0.0, a=1.0, waves=0.0):
    dome = np.array([(-34, 30), (-30, -6), (-20, -26), (0, -34), (20, -26), (30, -6), (34, 30), (46, 40), (46, 46), (-46, 46), (-46, 40)], np.float32)
    c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang)); Rm = np.array([[c, -sn], [sn, c]], np.float32)
    pv = np.array([0, -38], np.float32); pts = ((((dome - pv) @ Rm.T) + pv) * s + (cx, cy)).astype(np.int32)
    cv2.fillPoly(cv, [pts + np.array([int(5 * s / 3), int(7 * s / 3)])], (6.0, 8.0, 12.0), cv2.LINE_AA)
    cv2.fillPoly(cv, [pts], (50.0 * a, 190.0 * a, 245.0 * a), cv2.LINE_AA); cv2.polylines(cv, [pts], True, (20.0, 60.0, 110.0), max(2, int(2.5 * s / 2)), cv2.LINE_AA)
    hl = ((((np.array([(-22, -4), (-16, -20), (-4, -28)], np.float32) - pv) @ Rm.T) + pv) * s + (cx, cy)).astype(np.int32)
    cv2.polylines(cv, [hl], False, (200.0 * a, 235.0 * a, 255.0 * a), max(2, int(3 * s / 2)), cv2.LINE_AA)
    cl = (((np.array([0, 54], np.float32) - pv) @ Rm.T + pv) * s + (cx, cy)); cv2.circle(cv, (int(cl[0]), int(cl[1])), max(3, int(8 * s)), (40.0 * a, 150.0 * a, 215.0 * a), -1, cv2.LINE_AA)
    tp = ((np.array([0, -38], np.float32)) * s + (cx, cy)); cv2.circle(cv, (int(tp[0]), int(tp[1])), max(3, int(6 * s)), (40.0 * a, 150.0 * a, 215.0 * a), -1, cv2.LINE_AA)
    if waves > 0:
        for sd in (-1, 1):
            for k, r in enumerate((62, 80)):
                cv2.ellipse(cv, (int(cx), int(cy)), (int(r * s), int(r * s)), 0, -35 + (0 if sd > 0 else 180) - 20, 35 + (0 if sd > 0 else 180) + 20 if False else (35 if sd > 0 else 215), (80.0 * waves, 200.0 * waves, 255.0 * waves), max(2, int(3 * s / 2)), cv2.LINE_AA)


def sub_btn(cv, cx, cy, s, state=0.0, a=1.0):
    w, h = 250 * s, 78 * s
    col = (np.array((38.0, 38.0, 225.0)) * (1 - state) + np.array((120.0, 120.0, 124.0)) * state).tolist()
    pts = rrect(cv, cx, cy, w, h, 0.0, tuple(float(v) * a for v in col), edge=(14.0, 14.0, 90.0)); r = int(h / 2)
    cv2.circle(cv, (int(cx - w / 2), int(cy)), r, tuple(float(v) * a for v in col), -1, cv2.LINE_AA); cv2.circle(cv, (int(cx + w / 2), int(cy)), r, tuple(float(v) * a for v in col), -1, cv2.LINE_AA)
    if state < 0.5:   # play triangle + two little bars like a media button
        tri = np.array([(cx - 28 * s, cy - 24 * s), (cx - 28 * s, cy + 24 * s), (cx + 24 * s, cy)], np.int32)
        cv2.fillConvexPoly(cv, tri, (250.0 * a, 250.0 * a, 252.0 * a), cv2.LINE_AA)
    else:             # check mark
        cv2.polylines(cv, [np.array([(cx - 30 * s, cy), (cx - 8 * s, cy + 22 * s), (cx + 32 * s, cy - 22 * s)], np.int32)], False, (250.0 * a, 250.0 * a, 252.0 * a), max(3, int(9 * s)), cv2.LINE_AA)


def cursor(cv, x, y, s, press=0.0):
    pts = np.array([(0, 0), (0, 70), (17, 54), (30, 84), (42, 78), (29, 49), (52, 49)], np.float32) * s * (1 - 0.1 * press) + (x, y)
    cv2.fillPoly(cv, [(pts + np.array([4, 5])).astype(np.int32)], (6.0, 8.0, 12.0), cv2.LINE_AA)
    cv2.fillPoly(cv, [pts.astype(np.int32)], (245.0, 245.0, 248.0), cv2.LINE_AA); cv2.polylines(cv, [pts.astype(np.int32)], True, (20.0, 20.0, 24.0), max(2, int(3 * s)), cv2.LINE_AA)
    if press > 0.05: cv2.circle(cv, (int(x), int(y)), int(40 * s * press + 10), (255.0, 255.0, 255.0), max(1, int(3 * s)), cv2.LINE_AA)


def pop(T, t0, d=0.4):   # overshoot pop-in 0..1..
    e = clamp((T - t0) / d); return 0.0 if e <= 0 else (1.0 + 0.22 * math.sin(e * math.pi) * (1 - e) * 3) * ease_out(e) if e < 1 else 1.0


def cta_bg(cv, T, k, dark=0.78, warm=1.0):
    cam = cam1(lerp(1.0, 1.08, k), (640, 420)); plate(cv, 'h7_sun', cam, 'b', gain=dark)
    lb = LightBuf(); lb.glow(640, 330, 520, (255, 220, 150), 0.18 * warm); lb.apply(cv, blur=40); motes(cv, T, 91, 40, 0.8, (255, 235, 190), 0.9)


# ---------------------------------------------------------------- new shots
def shot_press_like(cv, T):   # 50.4 - 53.0: "if you got here, like and subscribe" - thumb floats up, men below
    k = seg(T, 50.3, 53.1); cta_bg(cv, T, k)
    e = pop(T, 50.7, 0.5); thumb(cv, 640, 330 - 8 * math.sin(T * 2.0), 2.6 * e, 1.0, 1.0, -10 + 4 * math.sin(T * 2.0))
    for j in range(6):
        ph = (T * 0.3 + j * 0.37) % 1.0
        if e > 0.5: cv2.circle(cv, (int(300 + 680 * ((j * 0.37) % 1.0)), int(560 - ph * 380)), 3, (90.0, 200.0, 255.0), -1, cv2.LINE_AA)
    vignette(cv, 0.4, 2.0); finish(cv, T, 191, 0.4, 0)


def shot_shrug(cv, T):   # 53.0 - 56.6 : "can we follow 33 men ... and leave without a like?!"
    k = seg(T, 52.9, 56.7); cam = Cam(A=(680, 640), sb=lerp(1.02, 1.1, k), sw=lerp(1.0, 1.2, k), sc=lerp(1.0, 1.12, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.9, lamps=1.2); items = []
    for i, c in enumerate(P3.GRID):
        sh = ev(T, 54.0 + 0.012 * i, 54.5 + 0.012 * i)
        pose = {'head': 4 * math.sin(T * 1.1 + i) + 8 * sh * (1 if c['x'] > 640 else -1), 'aL': 4 + 60 * sh, 'aR': 4 + 60 * sh, 'fL': 40 * sh, 'fR': 40 * sh}
        items.append(dict(c, pose=pose, crouch=0.05, gain=0.9, tint=(0.95, 1.0, 1.06), hop=5 * sh * math.sin(T * 6 + i)))
    draw_items(cv, cam, items, T); tone(cv, 1.0, 0, (0.98, 1.0, 1.04), 1.0); finish(cv, T, 192, 0.4, 14)


def shot_icons(cv, T):   # 56.6 - end: empty thumb ... LIKE ... SUBSCRIBE ... BELL
    k = seg(T, 56.5, D9); cta_bg(cv, T, k, 0.7, 1.0 + 0.4 * ev(T, 59.6, 60.5))
    # phase 1 (56.6 - 59.5): empty grey thumb, sad sway
    f1 = ev(T, 59.65, 59.95); sad = 1.0 - ev(T, 59.5, 59.7)
    e0 = pop(T, 56.7, 0.5)
    if T >= 56.7:
        sc_ = 2.3 * e0 * (1.0 + 0.25 * P(T, 59.7, 60.1)) * (1 - 0.6 * ev(T, 60.35, 60.9))
        cxp = lerp(640, 250, ev(T, 60.35, 60.9)); cyp = lerp(360, 335, ev(T, 60.35, 60.9))
        thumb(cv, cxp, cyp + 6 * math.sin(T * 2.5) * sad, max(0.01, sc_), 1.0, f1, -10 * sad + 8 * f1)
        if f1 > 0.5 and T < 60.6:
            r = np.random.default_rng(int(T * 24)); [cv2.circle(cv, (int(cxp + (r.random() - .5) * 420), int(cyp + (r.random() - .5) * 360)), 3, (90.0, 210.0, 255.0), -1, cv2.LINE_AA) for _ in range(10)]
    # phase 2: subscribe button click (60.66 - 61.3)
    if T >= 60.6:
        e = pop(T, 60.6, 0.35); st = ev(T, 61.2, 61.35)
        sub_btn(cv, 640, 335, 1.4 * e * (1 + 0.08 * P(T, 61.2, 61.45)), st)
        if T < 61.9: cursor(cv, lerp(900, 700, ev(T, 60.5, 61.15)), lerp(520, 345, ev(T, 60.5, 61.15)), 1.4, P(T, 61.1, 61.35) * 1.2)
    # phase 3: bell rings (61.6 - end)
    if T >= 61.5:
        e = pop(T, 61.5, 0.35); ring = math.sin((T - 61.6) * 22) * 24 * math.exp(-(T - 61.6) * 0.6) if T > 61.6 else 0.0
        bell(cv, 1030, 335, 1.7 * e, ring, 1.0, waves=0.6 if T > 61.6 else 0.0)
    vignette(cv, 0.4, 2.0); finish(cv, T, 193, 0.35, 0)


def shot_day1(cv, T):    # 35.2 - 37.4 : survival began on day one - they take the refuge together
    P3.shot_enter(cv, 5.4 + (T - 35.2) * 0.95)


# ---------------------------------------------------------------- the part
SHOTS9 = [
    ('mine0', 0.0, 2.5, SRC(P2, 'shot_mine', 0.5, 0.0, 0.8), 0.0),
    ('n33', 2.5, 3.95, SRC(P3, 'shot_count', 23.65, 2.5), 0.25),
    ('n69', 3.95, 5.05, SRC(P5, 'shot_days', 41.5, 3.95), 0.2),
    ('n700', 5.05, 6.6, SRC(P7, 'shot_meters', 2.5, 5.05), 0.2),
    ('which', 6.6, 9.5, SRC(P3, 'shot_luis1', 32.4, 6.6), 0.4),
    ('first', 9.5, 11.75, SRC(P3, 'shot_door1', 0.2, 9.5), 0.3),
    ('twodays', 11.75, 14.3, SRC(P3, 'shot_twodays', 20.6, 11.75), 0.3),
    ('ration', 14.3, 16.55, SRC(P3, 'shot_ration', 41.0, 14.3), 0.3),
    ('lights', 16.55, 19.2, SRC(P4, 'shot_lights', 50.45, 16.55, 1.25), 0.3),
    ('sched', 19.2, 20.4, SRC(P4, 'shot_sched', 42.3, 19.2), 0.2),
    ('fear', 20.4, 22.8, SRC(P4, 'shot_despair', 94.4, 20.4), 0.3),
    ('roles', 22.8, 24.1, SRC(P4, 'shot_tasks', 60.6, 22.8), 0.2),
    ('noguar', 24.1, 26.9, SRC(P4, 'shot_vigil', 22.6, 24.1), 0.3),
    ('map', 26.9, 29.2, SRC(P4, 'shot_map', 38.9, 26.9), 0.3),
    ('amaz', 29.2, 32.25, SRC(P4, 'shot_routine', 55.4, 29.2, 0.9), 0.4),
    ('capsule', 32.25, 35.2, SRC(P7, 'shot_rise', 51.6, 32.25), 0.4),
    ('day1', 35.2, 37.4, shot_day1, 0.4),
    ('chaos', 37.4, 38.4, SRC(P3, 'shot_cramped', 8.4, 37.4), 0.2),
    ('enter33', 38.4, 40.0, SRC(P2, 'shot_tun_a', 8.0, 38.4), 0.3),
    ('rescue33', 40.0, 43.6, SRC(P7, 'shot_wide33', 105.8, 40.0, 0.85), 0.4),
    ('human', 43.6, 48.2, SRC(P4, 'shot_listen', 14.0, 43.6), 0.4),
    ('time', 48.2, 50.4, SRC(P3, 'shot_time', 36.0, 48.2), 0.3),
    ('like', 50.4, 53.0, shot_press_like, 0.4),
    ('shrug', 53.0, 56.6, shot_shrug, 0.4),
    ('icons', 56.6, D9, shot_icons, 0.5),
]


class Part9:
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTS9):
            hi = t1 + (SHOTS9[i + 1][4] / 2 if i + 1 < len(SHOTS9) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTS9) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
