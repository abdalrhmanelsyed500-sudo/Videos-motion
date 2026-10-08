"""Part 4 (Arabic, 109 s): day three underground, the sounds of digging, families above, Urzua's order, the routine,
Barrios the medic, Segovia the writer, Sepulveda's jokes, fights and despair, "how do we stay alive".
Same STYLE LOCK as parts 1-3. No captions, no music (SFX only)."""
import cv2, math, numpy as np
import hook_scenes as HS
from hook_scenes import *
import part2_scenes as P2
import part3_scenes as P3
from part2_scenes import draw_items, mk, head_pt, speak, kid
from part3_scenes import GRID, chamber_bg, finish, table_cam, table_bg, table_fg, storage_cam, storage_bg, food_at, bpt, HOT
for _k in 'usgjyv': HS.RIG[_k] = HS.RIG['m']

D4 = 109.0
CT = (0.85, 0.96, 1.1)


def P(T, a, b): return pulse(T, a, b)


def ev(T, a, b): return sstep(seg(T, a, b))


# ---------------------------------------------------------------- shared crowd helpers
def sit_row(xs, gy, sc, T, head=8, crouch=0.35, gain=0.8, ph=0.0, chs=None, extra=None):
    out = []
    for i, x in enumerate(xs):
        ch = (chs[i] if chs else 'm')
        pose = {'head': head + 3 * math.sin(T * 0.9 + i + ph), 'aL': 4, 'aR': 4}
        d = dict(ch=ch, x=x, gy=gy + (i % 2) * 6, sc=sc * (1 + 0.05 * ((i * 5) % 4 - 1.5) / 1.5), flip=1 if i % 2 else -1, ph0=ph + i * 1.3, pose=pose, crouch=crouch,
                 gain=gain, tint=CT, shirt=SHIRTS[(i * 3 + 1) % 10] if ch == 'm' else None, pants=PANTS[(i * 7 + 2) % 10] if ch == 'm' else None)
        if extra: extra(i, d)
        out.append(d)
    return out


def pcam(k, dx, z0=1.3, z1=1.42, A=(640, 620)):
    z = lerp(z0, z1, k); return Cam(A=A, sb=1.26 + 0.06 * k, sw=1.30 + 0.10 * k, sc=z, d=(dx * 0.45, 0), dw=(dx * 0.6, 0))


def rise(cv, T, t0, t1, glow=0.0, fadein=0.0):
    """camera climbs up the rock (h_p4) - 'no sun, no window'"""
    k = sstep(seg(T, t0, t1)); sS = 1.75 * S0
    oy = lerp(768 * sS - H, 0, k); ox = (1376 * sS - W) / 2 + 40 * math.sin(T * 0.4) + lerp(-60, 40, k)
    place(cv, L('h_p4'), M3(-ox, -oy, sS, sS, 0, 0, 0), gain=0.95)
    r = rng(33)
    for i in range(60):
        x = r.random() * W; sp = 10 + 20 * r.random(); y = ((r.random() * H) - T * sp) % H; c = 120 + 100 * r.random()
        cv2.circle(cv, (int(x), int(y)), 1, (c * .7, c * .85, c), -1, cv2.LINE_AA)
    vignette(cv, 0.35 + 0.35 * k, 2.0)
    if glow > 0:
        lb = LightBuf(); lb.glow(560, 690 + k * 300, 200, (60, 130, 255), 0.6 * glow * (1 - k)); lb.apply(cv, blur=40)


# ---------------------------------------------------------------- 1. hunger, heat, dust, dark (0 - 5.8)
def shot_hunger(cv, T):
    k = seg(T, 0, 6.0); cam = Cam(A=(680, 640), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.22, k), sc=lerp(1.0, 1.13, k), d=(0, 0), dw=(0, 0))
    dk = ev(T, 4.8, 5.8); chamber_bg(cv, T, cam, 0.78 - 0.30 * dk, lamps=1.0 - 0.88 * dk)
    items = []
    for i, c in enumerate(GRID):
        h_ = P(T, 2.3 + 0.02 * i, 3.2 + 0.02 * i) * (i % 3 == 0); w_ = P(T, 3.1 + 0.03 * i, 4.0 + 0.03 * i) * (i % 4 == 1); cg = P(T, 4.0 + 0.02 * i, 4.9 + 0.02 * i) * (i % 4 == 2)
        pose = {'head': 8 + 2 * math.sin(T * 0.9 + i) - 8 * cg - 12 * dk * (i % 2), 'aL': 4 + 114 * w_ + 20 * cg, 'fL': 140 * w_ + 128 * cg, 'aR': 4 + 26 * h_, 'fR': -95 * h_}
        items.append(dict(c, pose=pose, crouch=0.30 + 0.25 * h_ + 0.2 * cg, gain=0.80, tint=CT))
    draw_items(cv, cam, items, T)
    cv[:] = heat_haze(cv, T, 0.5 + 1.4 * ev(T, 3.0, 3.6), 0.05, 2.2, 150, 700)
    tone(cv, 1.0, 0, (0.90, 0.97, 1.10), 1.0)
    puffs(cv, T, 3.8, 5.8, 14, (200, 100, 880, 300), (95, 135, 178), seed=111, size=(100, 240), rise=(-4, 8), life=3.0, alpha=0.22)
    finish(cv, T, 51, 0.45 + 0.2 * dk, 20)


# ---------------------------------------------------------------- 2. no sun, no window (5.8 - 9.1)
def shot_nosun(cv, T): rise(cv, T, 5.7, 9.2, glow=0.8)


# ---------------------------------------------------------------- 3. no idea of the time (9.1 - 12.45)
def shot_notime(cv, T):
    k = seg(T, 8.9, 12.6); cam = table_cam(k, 1.15, 1.30, (700, 440))
    m_ = (T * 2.2 + 0.7 * math.sin(T * 3.3) + 0.4 * math.sin(T * 7.1)) % 1.0; h_ = (0.3 + T * 0.3 + 0.1 * math.sin(T * 2.7)) % 1.0
    table_bg(cv, T, cam, 0.78, hands=(h_, m_), glow=0.3 * flick(T, 7.0))
    items = [mk('m', 520, 524, .38, 1, 0.3, pose={'head': -8 + 4 * math.sin(T * 2.0), 'aL': 8, 'aR': 8}, shirt=SHIRTS[1], pants=PANTS[1], gain=.8, tint=CT, crouch=0.2),
             mk('g', 850, 524, .40, -1, 1.4, pose={'head': -10 + 5 * math.sin(T * 1.7 + 1), 'aL': 8, 'aR': 8}, gain=.8, tint=CT, crouch=0.15)]
    draw_items(cv, cam, items, T); table_fg(cv, cam, 0.78)
    veil(cv, T, 0.12 + 0.1 * P(T, 10.4, 11.8)); finish(cv, T, 52, 0.55, 22)


# ---------------------------------------------------------------- 4. the sounds of digging (12.45 - 22.15)
SND = [(14.46, 15.2), (15.36, 16.1), (16.44, 17.5), (19.8, 20.4), (20.71, 22.0)]


def hope(T):
    h = 0.0
    for a, b in SND: h = max(h, P(T, a - 0.2, b + 0.4))
    return h


def shot_listen(cv, T):
    k = seg(T, 12.3, 22.3); sh = 0.0
    for a, b in SND: sh = max(sh, 1.6 * P(T, a, b))
    dxy = shake_xy(T, sh); cam = Cam(A=(700, 520), sb=lerp(1.0, 1.08, k), sw=lerp(1.0, 1.16, k), sc=lerp(1.0, 1.08, k), d=dxy, dw=(dxy[0] * 1.5, dxy[1] * 1.5))
    plate(cv, 'h3_storage', cam, 'b')
    lb = LightBuf(); q = bpt(cam, 1000, 100); fl = 0.88 + 0.12 * flick(T, 5.0)
    lb.glow(q[0], q[1], 50 * cam.sb, (110, 190, 255), 0.7 * fl); lb.glow(q[0], q[1], 300 * cam.sb, (60, 130, 230), 0.34 * fl); lb.apply(cv, blur=28)
    hp = hope(T); turn = ev(T, 13.74, 14.3); items = []
    spec = [(250, 690, .50, 1, 'm'), (430, 700, .52, -1, 'u'), (600, 670, .42, 1, 'm'), (790, 700, .50, -1, 'g'), (960, 680, .46, 1, 'm'), (1130, 696, .50, -1, 'j')]
    for i, (x, gy, sc, fl_, ch) in enumerate(spec):
        up = hp
        pose = {'head': (-10 if x > 600 else 10) * turn * (1 - 0.6 * up) - 6 * up + 2 * math.sin(T * 1.5 + i), 'aL': 6 + 60 * up * (i % 2), 'aR': 6 + 80 * up * ((i + 1) % 2), 'fL': 0, 'fR': 0}
        crouch = 0.22 - 0.12 * up
        if i == 0: lis = ev(T, 13.6, 14.2) * (1 - ev(T, 21.9, 22.3)); pose.update({'head': 16 * lis - 4 * up, 'aL': 6 + 112 * lis * (1 - up), 'fL': 130 * lis * (1 - up)}); crouch = 0.28 * lis
        shirt = SHIRTS[(i * 3 + 1) % 10] if ch == 'm' else None; pants = PANTS[(i * 7 + 2) % 10] if ch == 'm' else None
        items.append(mk(ch, x, gy, sc, fl_, i * 1.3, pose=pose, crouch=crouch, gain=0.90 - 0.1 * (1 - up), tint=HOT, shirt=shirt, pants=pants))
    draw_items(cv, cam, items, T)
    for a, b in SND: puffs(cv, T, a, b, 5, (300, 0, 700, 80), (95, 135, 178), seed=int(a * 10), size=(40, 100), rise=(20, 70), life=1.4, alpha=0.2)
    cv *= 1 - 0.14 * (1 - hp) * ev(T, 17.6, 18.4) * (1 - ev(T, 19.6, 19.8))
    finish(cv, T, 53, 0.45, 22)


# ---------------------------------------------------------------- 5. families above ground at night (22.15 - 29.05)
def shot_vigil(cv, T):
    k = seg(T, 22.0, 29.2); pan = ev(T, 24.2, 25.0) * (-1) + ev(T, 26.8, 27.6) * (-1) + 1.0   # +1 left group, 0 centre, -1 right
    dx = 170 * pan; cam = Cam(A=(640, 620), sb=1.0 + 0.22 * ev(T, 22.2, 24.4), sw=1.0 + 0.26 * ev(T, 22.2, 24.4) + 0.06 * k, sc=lerp(1.0, 1.2, ev(T, 22.2, 24.4)),
                              d=(dx * 0.45 * ev(T, 22.2, 24.4), 0), dw=(dx * 0.6 * ev(T, 22.2, 24.4), 0))
    plate(cv, 'h4_night', cam, 'b'); plate(cv, 'h4_night_gr', cam, 'w')
    items = []
    pr = ev(T, 24.5, 25.2) * (1 - ev(T, 26.2, 26.6)); cr = ev(T, 26.5, 27.1) * (1 - ev(T, 27.7, 28.0)); cl = ev(T, 27.9, 28.4)
    # left group: praying; centre: crying; right: calling
    def pray(T, i): return {'head': 24 * pr + 2 * math.sin(T * 1.0 + i), 'aL': 18 * pr, 'fL': -105 * pr, 'aR': 18 * pr, 'fR': -105 * pr}
    for i, (ch, x, gy, sc, fl_) in enumerate((('w', 430, 650, .27, 1), ('ar', 520, 662, .29, -1), ('w', 340, 668, .30, 1))):
        items.append(mk(ch, x, gy, sc, fl_, i * 1.4, pose=pray(T, i), crouch=0.10 * pr, gain=0.95, tint=(0.95, 0.98, 1.04)))
    for i, (ch, x, gy, sc, fl_) in enumerate((('w', 640, 652, .28, -1), ('ar', 750, 660, .30, 1), ('w', 570, 672, .26, 1))):
        sob = 3 * math.sin(T * 9 + i)
        items.append(mk(ch, x, gy, sc, fl_, 2 + i * 1.1, pose={'aL': 4 + 114 * cr, 'fL': 140 * cr, 'aR': 4 + 114 * cr * (i % 2), 'fR': 140 * cr * (i % 2), 'head': 10 * cr + sob * cr}, crouch=0.12 * cr + 0.02 * sob * cr, gain=0.95, tint=(0.95, 0.98, 1.04)))
    for i, (ch, x, gy, sc, fl_) in enumerate((('ar', 880, 650, .28, 1), ('w', 990, 662, .30, -1), ('ar', 1090, 656, .27, 1))):
        sp = P(T, 28.0 + 0.1 * i, 29.0)
        items.append(mk(ch, x, gy, sc, fl_, 4 + i, pose={'aR': 4 + 128 * cl, 'fR': 118 * cl, 'aL': 4 + 20 * cl, 'fL': 124 * cl * (i % 2), 'head': -8 * cl}, mouth=speak(T, i, 0.9) * sp * cl, gain=0.95, tint=(0.95, 0.98, 1.04)))
    items += [kid('w', 470, 690, .19, 1, 7.1, pose={'head': 14 * pr}, tint=(0.95, 0.98, 1.04), gain=.95), kid('ar', 690, 694, .18, -1, 8.2, pose={'aL': 4 + 114 * cr, 'fL': 140 * cr}, tint=(0.95, 0.98, 1.04), gain=.95)]
    draw_items(cv, cam, items, T)
    lb = LightBuf(); fl = 0.9 + 0.1 * flick(T, 8.0)
    for (px, py, r_) in ((800, 530, 40), (1020, 548, 28), (560, 540, 26)):
        q = cam.pt(S0 * px - OX, S0 * py - OY); lb.glow(q[0], q[1], r_ * cam.sb, (110, 190, 255), 0.55 * fl); lb.glow(q[0], q[1], 7 * r_ * cam.sb, (50, 120, 230), 0.25 * fl)
    lb.apply(cv, blur=26); motes(cv, T, 54, 30, 0.6, (230, 225, 200)); vignette(cv, 0.4, 2.0)


# ---------------------------------------------------------------- 6. the rescue teams drill, not sure where (29.05 - 34.1)
def shot_rig(cv, T):
    k = seg(T, 28.9, 34.3); cam = Cam(A=(500, 560), sb=lerp(1.0, 1.12, k), sw=lerp(1.0, 1.28, k), sc=lerp(1.0, 1.14, k), d=(0, 0), dw=(0, 0))
    vib = 0.9 * (0.5 + 0.5 * math.sin(T * 3.0)); cam.d = shake_xy(T, vib); cam.dw = (cam.d[0] * 1.4, cam.d[1] * 1.4)
    plate(cv, 'h_p5', cam, 'b'); plate(cv, 'h_p5_gr', cam, 'w')
    items = []
    for i, (x, gy, sc, fl_) in enumerate(((240, 630, .26, 1), (420, 668, .34, -1), (600, 640, .28, 1), (780, 676, .36, -1), (960, 636, .27, 1), (1120, 670, .32, -1))):
        w_ = math.sin(2 * math.pi * 1.4 * T + i * 1.3)
        pose = {'aL': 24 + 40 * w_ * (i % 2), 'aR': 26 + 44 * w_ * ((i + 1) % 2), 'fL': 20 + 30 * w_, 'fR': 20 - 30 * w_, 'head': 3 * math.sin(T + i)}
        if i == 2: sh = P(T, 31.0, 32.2); pose.update({'aL': 40 * sh, 'aR': 40 * sh, 'fL': 20 * sh, 'fR': 20 * sh, 'head': 10 * sh})
        if i == 3: lk = P(T, 32.6, 33.8); pose.update({'aR': 70 * lk, 'fR': 15 * lk, 'head': -10 * lk})
        items.append(mk('m', x, gy, sc, fl_, i * 1.7, pose=pose, shirt=SHIRTS[(i * 3 + 1) % 10], pants=PANTS[(i * 5 + 2) % 10], gain=1.0))
    draw_items(cv, cam, items, T)
    puffs(cv, T, 29.0, 34.3, 20, (120, 480, 300, 80), (150, 185, 215), seed=121, size=(60, 140), rise=(10, 50), life=2.6, alpha=0.3, wind=(30, 0))
    heat = heat_haze(cv, T, 1.2, 0.05, 2.5, 380, 560); cv[:] = heat
    lb = LightBuf(); lb.glow(130, 90, 330, (90, 160, 255), 0.45); lb.apply(cv, blur=40); motes(cv, T, 7, 30, 1.4); vignette(cv, 0.3, 2.0)


# ---------------------------------------------------------------- 7. Urzua decides: order (34.07 - 38.8)
def shot_decide(cv, T):
    k = seg(T, 34.0, 38.9); cam = Cam(A=(640, 640), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.24, k), sc=lerp(1.0, 1.16, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.62, lamps=0.9)
    items = []
    for i, c in enumerate(GRID[:24]):
        if abs(c['x'] - 640) < 170 and c['gy'] > 630: continue
        items.append(dict(c, pose={'head': 4 - 6 * ev(T, 35.0, 35.8) + 2 * math.sin(T + i)}, crouch=0.15, gain=0.74, tint=CT))
    g1 = P(T, 34.6, 36.2); g2 = P(T, 36.3, 37.8); g3 = P(T, 37.5, 38.7)
    pose = {'aR': 8 + 90 * g1 + 50 * g3, 'fR': 20 * g1, 'aL': 8 + 60 * g2, 'fL': -20 * g2 + 25 * g3, 'head': 3 * math.sin(T * 0.9) - 4 * g1}
    items.append(mk('u', 640, 714, .60, 1, 0.4, pose=pose, mouth=speak(T, 0.3, 0.45) * (1.0 if 34.2 < T < 38.7 else 0.0), gain=1.0, tint=(0.95, 1.0, 1.06)))
    draw_items(cv, cam, items, T)
    lb = LightBuf(); q = cam.pt(640, 420); lb.glow(q[0], q[1], 360 * cam.sc, (80, 150, 255), 0.35); lb.apply(cv, blur=40)
    finish(cv, T, 55, 0.5, 20)


# ---------------------------------------------------------------- 8. the map of the tunnels, tasks (38.84 - 41.55) / scribbles (72.6 - 78.5)
QUAD = [(535, 465), (790, 465), (920, 548), (442, 542)]   # paper corners (plate px): TL TR BR BL


def paper_pt(u, v):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = QUAD
    top = (x0 + (x1 - x0) * u, y0 + (y1 - y0) * u); bot = (x3 + (x2 - x3) * u, y3 + (y2 - y3) * u)
    return top[0] + (bot[0] - top[0]) * v, top[1] + (bot[1] - top[1]) * v


def paper_center(z, A=(680, 520)):
    cx, cy = paper_pt(0.5, 0.5); return (640 - A[0] - z * (S0 * cx - OX - A[0]), 360 - A[1] - z * (S0 * cy - OY - A[1]))


def stroke(cv, cam, pts, prog, w=3.2, col=(24.0, 36.0, 58.0), tip=None):
    """draw polyline pts (unit paper coords) up to fraction prog; returns the tip position (screen)"""
    if prog <= 0: return None
    n = len(pts) - 1; seglen = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(n)]; tot = sum(seglen); target = prog * tot; acc = 0.0; last = None
    sp = [paper_pt(*p) for p in pts]; sp = [bpt(cam, *p) for p in sp]
    for i in range(n):
        if acc >= target: break
        f = min(1.0, (target - acc) / max(1e-6, seglen[i])); a = sp[i]; b = (a[0] + (sp[i + 1][0] - a[0]) * f, a[1] + (sp[i + 1][1] - a[1]) * f)
        cv2.line(cv, (int(a[0] + 1), int(a[1] + 1)), (int(b[0] + 1), int(b[1] + 1)), (12.0, 18.0, 30.0), max(1, int(w * cam.sb * 0.9 + 1)), cv2.LINE_AA)
        cv2.line(cv, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), col, max(1, int(w * cam.sb * 0.7)), cv2.LINE_AA); last = b; acc += seglen[i]
    return last


def pencil(cv, tip, ang=-35, ln=170, sc=1.0):
    if tip is None: return
    a = math.radians(ang); x2 = tip[0] + math.cos(a) * ln * sc; y2 = tip[1] + math.sin(a) * ln * sc
    cv2.line(cv, (int(tip[0] + 2), int(tip[1] + 4)), (int(x2 + 2), int(y2 + 4)), (14.0, 20.0, 30.0), max(2, int(8 * sc)), cv2.LINE_AA)
    cv2.line(cv, (int(tip[0]), int(tip[1])), (int(x2), int(y2)), (70.0, 150.0, 220.0), max(2, int(10 * sc)), cv2.LINE_AA)
    cv2.line(cv, (int(tip[0]), int(tip[1])), (int(tip[0] + math.cos(a) * 22 * sc), int(tip[1] + math.sin(a) * 22 * sc)), (30.0, 40.0, 55.0), max(2, int(8 * sc)), cv2.LINE_AA)


MAPLINES = [[(0.08, 0.5), (0.18, 0.46), (0.28, 0.54), (0.38, 0.46), (0.48, 0.5), (0.60, 0.5)],
            [(0.18, 0.46), (0.18, 0.15), (0.30, 0.12)], [(0.38, 0.46), (0.40, 0.85), (0.52, 0.9)], [(0.60, 0.5), (0.72, 0.28), (0.9, 0.3)], [(0.60, 0.5), (0.74, 0.72), (0.88, 0.7)],
            [(0.28, 0.54), (0.26, 0.82), (0.16, 0.9)]]
_jr = rng(5)
SCRIB = []
for _r in range(7):
    v = 0.12 + _r * 0.12; pts = []; x = 0.06
    while x < (0.9 if _r % 3 else 0.62):
        pts.append((x, v + 0.025 * math.sin(x * 90 + _r) + 0.012 * (_jr.random() - .5))); x += 0.012
    SCRIB.append(pts)


def paper_bg(cv, T, cam, dark=0.95):
    plate(cv, 'h4_map', cam, 'b', gain=dark)
    lb = LightBuf(); q = bpt(cam, 872, 440); fl = 0.88 + 0.12 * flick(T, 9.0)
    lb.glow(q[0], q[1], 30 * cam.sb, (110, 190, 255), 0.7 * fl); lb.glow(q[0], q[1], 260 * cam.sb, (60, 130, 230), 0.34 * fl); lb.apply(cv, blur=24)


def shot_map(cv, T):
    k = seg(T, 38.7, 41.7); z = lerp(2.0, 2.35, k); cam = Cam(A=(680, 520), sb=z, sw=z, sc=z, d=(-40 * z / 2.0, 0), dw=(-40 * z / 2.0, 0))
    cam.d = paper_center(z); cam.dw = cam.d
    paper_bg(cv, T, cam)
    p = seg(T, 38.84, 40.35) * len(MAPLINES); tip = None
    for i, ln in enumerate(MAPLINES):
        pr = clamp(p - i)
        if pr > 0: t_ = stroke(cv, cam, ln, pr); tip = t_ if (pr < 1.0 or i == len(MAPLINES) - 1) else tip
    # task marks: coloured dots placed one by one
    for j, (u, v, col) in enumerate(((0.30, 0.50, (60.0, 120.0, 220.0)), (0.62, 0.50, (80.0, 200.0, 120.0)), (0.40, 0.88, (220.0, 140.0, 60.0)), (0.88, 0.30, (80.0, 80.0, 220.0)), (0.86, 0.70, (200.0, 200.0, 80.0)))):
        e = clamp((T - (40.48 + 0.18 * j)) / 0.25)
        if e > 0:
            q = bpt(cam, *paper_pt(u, v)); r_ = (10 + 6 * math.sin(e * math.pi)) * cam.sb * 0.5
            cv2.circle(cv, (int(q[0] + 1), int(q[1] + 2)), int(r_ + 1), (12.0, 16.0, 26.0), -1, cv2.LINE_AA); cv2.circle(cv, (int(q[0]), int(q[1])), int(r_), col, -1, cv2.LINE_AA)
    if T < 40.5: pencil(cv, tip, -32, 150, cam.sb / 2.0)
    elif tip is not None and T < 41.5: pencil(cv, tip, -32, 150, cam.sb / 2.0)
    veil(cv, T, 0.04); finish(cv, T, 56, 0.5, 14)


def shot_scrib(cv, T):
    k = seg(T, 72.5, 78.7); z = lerp(2.1, 2.5, k); cam = Cam(A=(680, 520), sb=z, sw=z, sc=z)
    cam.d = paper_center(z); cam.dw = cam.d
    paper_bg(cv, T, cam)
    p = seg(T, 72.7, 77.8) * len(SCRIB); tip = None
    for i, ln in enumerate(SCRIB):
        pr = clamp(p - i)
        if pr > 0:
            t_ = stroke(cv, cam, ln, pr, w=2.0, col=(26.0, 34.0, 52.0))
            if pr < 1.0: tip = t_
    if tip is None and p > 0:
        q = bpt(cam, *paper_pt(*SCRIB[-1][-1])); tip = q
    pencil(cv, tip, -32, 150, cam.sb / 2.0)
    veil(cv, T, 0.04); finish(cv, T, 57, 0.5, 14)


# ---------------------------------------------------------------- 9. rest and sleep times: the clock (41.55 - 46.0)
def shot_sched(cv, T):
    k = seg(T, 41.4, 46.2); cam = table_cam(k, 1.05, 1.2, (700, 440))
    cl = ev(T, 41.8, 42.4); hh = 0.12 + 0.02 * (T - 41.5) * 4; table_bg(cv, T, cam, 0.9, hands=(hh % 1.0, (hh * 12) % 1.0), glow=cl * 0.8)
    nd = P(T, 42.4, 43.3) + P(T, 44.0, 44.9)
    items = [mk('u', 640, 524, .40, 1, 0.3, pose={'aR': 8 + 80 * P(T, 41.8, 43.0), 'fR': 20, 'aL': 8 + 40 * P(T, 43.0, 45.0), 'head': 3 * math.sin(T * 1.3)}, mouth=speak(T, 0.3, 0.4) * (1.0 if T < 45.8 else 0.0), gain=.92, tint=(.94, 1.0, 1.06))]
    for i, (x, gy, sc, fl_) in enumerate(P3.SIT_L + P3.SIT_R):
        sl = ev(T, 43.4, 44.2) * (i % 2)
        items.append(mk('m', x, gy, sc, fl_, i * 1.2, crouch=0.18 + 0.5 * sl, pose={'head': 4 * math.sin(T * 1.1 + i) + (4 if x < 640 else -4) * ev(T, 42.0, 43.0) + 16 * sl, 'aL': 4, 'aR': 4},
                        shirt=SHIRTS[(i * 3 + 1) % 10], pants=PANTS[(i * 7 + 2) % 10], gain=.8, tint=CT))
    draw_items(cv, cam, items, T); table_fg(cv, cam, 0.9); finish(cv, T, 58, 0.45, 16)


# ---------------------------------------------------------------- 10. the mind collapses (46.0 - 50.4)
def shot_mind(cv, T):
    k = seg(T, 45.9, 50.6); cam = Cam(A=(640, 640), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.24, k), sc=lerp(1.0, 1.18, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.50, lamps=0.35 + 0.1 * flick(T, 11.0))
    items = sit_row((180, 300, 1000, 1130), 640, .34, T, head=14, crouch=0.55, gain=0.62)
    items += sit_row((120, 1230), 600, .22, T, head=14, crouch=0.5, gain=0.58, ph=2.0)
    hd = ev(T, 46.3, 47.3)
    items.append(mk('g', 640, 712, .58, 1, 0.1, crouch=0.62 * hd, pose={'head': 30 * hd + 2 * math.sin(T * 6) * hd, 'aL': 4 + 114 * hd, 'fL': 140 * hd, 'aR': 4 + 114 * hd, 'fR': 140 * hd}, gain=.85, tint=CT))
    draw_items(cv, cam, items, T)
    cv[:] = heat_haze(cv, T, 1.2, 0.05, 2.2, 150, 700); veil(cv, T, 0.1 + 0.1 * ev(T, 47, 49)); tone(cv, 1.0, 0, (0.93, 0.98, 1.06), 1.0)
    finish(cv, T, 59, 0.6, 24)


# ---------------------------------------------------------------- 11. day and night in the mountain: the lights (50.4 - 54.85)
def shot_lights(cv, T):
    k = seg(T, 50.3, 55.0); cam = Cam(A=(680, 640), sb=lerp(1.0, 1.08, k), sw=lerp(1.0, 1.18, k), sc=lerp(1.0, 1.10, k), d=(0, 0), dw=(0, 0))
    day = ev(T, 50.45, 51.1) * (1 - ev(T, 53.74, 54.0)); click = P(T, 53.70, 53.85) + P(T, 50.40, 50.55) * 0.6
    chamber_bg(cv, T, cam, 0.34 + 0.66 * day, lamps=0.10 + 1.35 * day)
    items = []
    for i, c in enumerate(GRID):
        slp = ev(T, 54.0, 54.6); st = P(T, 51.2 + 0.03 * i, 52.4 + 0.03 * i) * (i % 3 == 0)
        pose = {'head': 8 - 6 * day + 12 * slp + 3 * math.sin(T * 0.9 + i), 'aL': 4 + 118 * st * 0.5, 'aR': 4 + 118 * st, 'fL': 0, 'fR': 20 * st}
        d_ = dict(c, pose=pose, crouch=0.30 - 0.20 * day * (1 - slp), gain=0.8, tint=CT)
        if i % 3 != 0: d_['rot'] = (84 if i % 2 else -84) * slp; d_['dy'] = 455 * slp; d_['pose'] = dict(pose, head=pose['head'] * (1 - slp))
        items.append(d_)
    # one man at the left lamp reaches to the switch
    sw_ = P(T, 50.2, 50.9) + P(T, 53.2, 53.9)
    items.append(mk('u', 140, 700, .46, 1, 0.5, pose={'aR': 8 + 130 * sw_, 'fR': 10, 'head': -10 * sw_}, gain=.9, tint=CT))
    draw_items(cv, cam, items, T)
    tone(cv, 1.0, 0, (0.90 + 0.10 * day, 0.97, 1.10 - 0.08 * day), 1.0)
    if click > 0.01: cv += 22 * click
    finish(cv, T, 60, 0.45 + 0.2 * (1 - day), 20)


# ---------------------------------------------------------------- 12. routine: sleep / sit / gather (54.85 - 60.0)
def shot_routine(cv, T):
    pan = 1.0 - ev(T, 56.8, 57.5) * 1.0 - ev(T, 58.1, 58.9) * 1.0; k = seg(T, 54.8, 60.2)
    cam = pcam(k, 250 * pan, 1.3, 1.36)
    chamber_bg(cv, T, cam, 0.7, lamps=0.9)
    items = []
    # left: sleeping corner
    def lying(i, d): d['rot'] = (84 if i % 2 else -84) * ev(T, 55.0, 56.0 + 0.1 * i); d['dy'] = 455 * ev(T, 55.0, 56.0 + 0.1 * i); d['crouch'] = 0.0; d['pose']['head'] = 0.0
    items += sit_row((300, 430, 560, 380), 640, .36, T, head=0, crouch=0.0, gain=0.78, ph=0.3, extra=lying)
    # centre: sitting by the table, chatting
    def chat(i, d):
        g = P(T, 57.3 + 0.2 * i, 58.0 + 0.2 * i); d['pose'].update({'aR': 4 + 50 * g, 'head': 4 + 5 * math.sin(T * 2 + i)}); d['mouth'] = speak(T, i, 0.4) * g
    items += sit_row((560, 650, 740, 700), 668, .38, T, head=4, crouch=0.40, gain=0.82, ph=1.5, extra=chat)
    # right: gathered, listening to Urzua
    items += sit_row((860, 950, 1040, 905), 664, .38, T, head=-6, crouch=0.18, gain=0.86, ph=2.5)
    items.append(mk('u', 970, 700, .44, -1, 0.4, pose={'aR': 8 + 70 * P(T, 58.6, 59.8), 'fR': 20, 'head': 3 * math.sin(T)}, mouth=0.0, gain=.95, tint=CT))
    draw_items(cv, cam, items, T)
    tone(cv, 1.0, 0, (0.92, 0.98, 1.06), 1.0); finish(cv, T, 61, 0.45, 18)


# ---------------------------------------------------------------- 13. everyone has a task: food, water, the sick (60.0 - 64.15)
def shot_tasks(cv, T):
    pan = 1.0 - ev(T, 61.2, 61.8) - ev(T, 62.5, 63.1); k = seg(T, 59.8, 64.3)
    dx = 250 * pan; cam = Cam(A=(640, 620), sb=1.26 + 0.05 * k, sw=1.30 + 0.08 * k, sc=lerp(1.32, 1.4, k), d=(dx * 0.45, 0), dw=(dx * 0.6, 0))
    plate(cv, 'h3_storage', cam, 'b')
    lb = LightBuf(); q = bpt(cam, 1000, 100); fl = 0.88 + 0.12 * flick(T, 5.0)
    lb.glow(q[0], q[1], 50 * cam.sb, (110, 190, 255), 0.7 * fl); lb.glow(q[0], q[1], 300 * cam.sb, (60, 130, 230), 0.34 * fl); lb.apply(cv, blur=28)
    cnt = math.sin(2 * math.pi * 0.9 * T)
    items = [mk('m', 450, 664, .42, 1, 0.3, pose={'aL': 20 + 50 * (0.5 + 0.5 * cnt), 'fL': -20 + 30 * cnt, 'aR': 14, 'head': 10 * cnt + 6}, shirt=SHIRTS[1], pants=PANTS[1], gain=.92, tint=HOT, crouch=0.15),
             mk('m', 640, 660, .40, -1, 1.7, pose={'aL': 14, 'aR': 28 + 30 * (0.5 + 0.5 * math.sin(T * 1.8)), 'head': -8}, shirt=SHIRTS[4], pants=PANTS[5], gain=.92, tint=HOT, crouch=0.3),
             mk('y', 830, 664, .44, 1, 0.9, pose={'aR': 20 + 60 * P(T, 62.4, 63.9), 'fR': 18, 'head': 8}, gain=.95, tint=HOT, crouch=0.12),
             mk('m', 950, 672, .40, -1, 2.3, pose={'head': 22, 'aL': 4, 'aR': 4}, shirt=SHIRTS[6], pants=PANTS[2], gain=.85, tint=HOT, crouch=0.62),
             mk('g', 1060, 668, .42, -1, 3.3, pose={'head': 10, 'aL': 4, 'aR': 10 + 30 * P(T, 62.8, 63.8)}, gain=.9, tint=HOT, crouch=0.2)]
    draw_items(cv, cam, items, T)
    for j, (nm, fx, fy, fs) in enumerate((('food_0', 470, 692, .15), ('food_3', 520, 700, .14), ('food_4', 415, 700, .13))): food_at(cv, cam, nm, fx, fy, fs, e=1.0)
    finish(cv, T, 62, 0.45, 20)


# ---------------------------------------------------------------- 14. Yonni Barrios, the unofficial doctor (64.15 - 69.5)
def shot_yonni(cv, T):
    k = seg(T, 64.0, 69.7); cam = Cam(A=(640, 640), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.24, k), sc=lerp(1.0, 1.18, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.66, lamps=0.95)
    items = sit_row((150, 270, 1030, 1150), 640, .32, T, head=10, crouch=0.35, gain=0.72, ph=0.7) + sit_row((90, 1230), 596, .20, T, head=8, crouch=0.3, gain=0.66)
    pulse_ = 8 + 16 * ev(T, 64.6, 65.4) - 10 * ev(T, 67.4, 68.2)
    items.append(mk('m', 840, 668, .44, -1, 1.2, rot=-84, dy=455, pose={'head': 4 * math.sin(T * 1.2), 'aL': 4, 'aR': 4}, shirt=SHIRTS[6], pants=PANTS[2], gain=.95, tint=CT))
    items.append(mk('y', 560, 712, .60, 1, 0.5, pose={'aR': 8 + 36 * ev(T, 64.5, 65.3) * (1 - ev(T, 68.0, 68.8)) + 3 * math.sin(T * 5), 'fR': 30 * ev(T, 64.5, 65.3), 'aL': 8 + 20 * ev(T, 66.9, 67.6), 'head': 14 * ev(T, 64.6, 65.3) - 6 * ev(T, 67.4, 68.2)}, mouth=0.0, gain=1.0, tint=(0.96, 1.0, 1.06)))
    draw_items(cv, cam, items, T)
    lb = LightBuf(); q = cam.pt(700, 430); lb.glow(q[0], q[1], 300 * cam.sc, (80, 150, 255), 0.3); lb.apply(cv, blur=40); finish(cv, T, 63, 0.5, 18)


# ---------------------------------------------------------------- 15. Victor Segovia writes (69.75 - 72.6)
def shot_victor(cv, T):
    k = seg(T, 69.6, 72.8); cam = table_cam(k, 1.0, 1.1, (700, 440))
    table_bg(cv, T, cam, 0.92, hands=(0.45, 0.82), glow=0.0)
    wr = math.sin(2 * math.pi * 3.2 * T)
    pose = {'aR': 30 + 3 * wr, 'fR': -95 + 5 * wr, 'aL': 24, 'fL': -100, 'head': 14 + 3 * math.sin(T * 0.9)}
    sc0 = .42; items = [mk('v', 640, 545, sc0, 1, 0.3, pose=pose, gain=.95, tint=(.94, 1.0, 1.06), crouch=0.05)]
    draw_items(cv, cam, items, T)
    # the notebook he writes in (procedural, in front of his chest)
    Xc, Yc = cam.pt(640, 545); s_ = sc0 * cam.sc; cx, cy = Xc + 8 * s_, Yc - 520 * s_
    a = math.radians(-8); R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    pts = np.array([[-110, -78], [110, -78], [110, 78], [-110, 78]], np.float32) * s_ @ R.T + np.array([cx, cy])
    cv2.fillConvexPoly(cv, (pts + np.array([4, 6])).astype(np.int32), (10.0, 14.0, 22.0), cv2.LINE_AA); cv2.fillConvexPoly(cv, pts.astype(np.int32), (150.0, 190.0, 215.0), cv2.LINE_AA)
    nl = int(clamp((T - 69.9) / 2.6) * 6) + 1
    for j in range(nl):
        y0 = -56 + j * 20; xe = 80 if j < nl - 1 else -80 + 160 * (clamp((T - 69.9) / 2.6) * 6 % 1.0)
        a0 = (np.array([-80, y0], np.float32) * s_) @ R.T + np.array([cx, cy]); a1 = (np.array([xe, y0 + 3 * math.sin(T * 9)], np.float32) * s_) @ R.T + np.array([cx, cy])
        cv2.line(cv, (int(a0[0]), int(a0[1])), (int(a1[0]), int(a1[1])), (40.0, 52.0, 78.0), max(1, int(2 * s_)), cv2.LINE_AA)
    table_fg(cv, cam, 0.92)
    finish(cv, T, 64, 0.5, 14)


# ---------------------------------------------------------------- 16. Mario Sepulveda: morale (78.7 - 88.3)
def shot_joke(cv, T):
    k = seg(T, 78.6, 88.4); cam = Cam(A=(640, 640), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.24, k), sc=lerp(1.0, 1.16, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.72 + 0.12 * ev(T, 79.5, 81.0), lamps=1.0)
    big = 0.5 + 0.5 * math.sin(2 * math.pi * 0.8 * T); spk = 1.0 if 78.8 < T < 88.1 else 0.0
    items = []
    for i, (x, gy, sc, fl_) in enumerate(((160, 690, .38, 1), (300, 650, .30, -1), (440, 700, .40, 1), (860, 700, .40, -1), (1000, 650, .30, 1), (1150, 690, .38, -1), (60, 600, .20, 1), (1240, 600, .20, -1))):
        lt = ev(T, 81.8 + 0.1 * i, 82.4 + 0.1 * i) * (1 - 0.0 * ev(T, 87, 88)); lau = 0.5 + 0.5 * math.sin(2 * math.pi * 2.4 * T + i)
        items.append(mk('m', x, gy, sc, fl_, i * 1.3, crouch=0.15 + 0.15 * lt * lau, pose={'head': -8 * lt * lau + 3 * math.sin(T + i), 'aL': 8 + 10 * lt, 'aR': 8 + 10 * lt}, shirt=SHIRTS[(i * 3 + 1) % 10], pants=PANTS[(i * 7 + 2) % 10], gain=.84, tint=CT))
    P_ = {'aL': 30 + 55 * big, 'aR': 30 + 55 * (1 - big), 'fL': 10 + 40 * (1 - big), 'fR': 10 + 40 * big, 'head': 5 * math.sin(2 * math.pi * 1.5 * T)}
    items.append(mk('s', 640, 716, .62, 1, 0.3, pose=P_, mouth=speak(T, 0.2, 0.9) * spk, gain=1.0, tint=(0.96, 1.0, 1.06)))
    draw_items(cv, cam, items, T)
    for nm, fx, fy, fs, tt in (('food_0', 470, 704, .17, 85.5),):
        food_at(cv, cam, nm, fx, fy, fs, e=clamp((T - tt) / 0.5))
    finish(cv, T, 65, 0.4, 20)


# ---------------------------------------------------------------- 17. fights (88.3 - 93.5)
def shot_fight(cv, T):
    k = seg(T, 88.2, 93.6); sh = 0.8 * P(T, 90.0, 93.0); dxy = shake_xy(T, sh); cam = Cam(A=(640, 640), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.24, k), sc=lerp(1.0, 1.16, k), d=dxy, dw=(dxy[0] * 1.5, dxy[1] * 1.5))
    chamber_bg(cv, T, cam, 0.62, lamps=0.8 * (0.85 + 0.15 * flick(T, 13.0)))
    ang = ev(T, 89.2, 90.0); sp = P(T, 89.6, 93.3)
    items = sit_row((150, 280, 1000, 1130), 650, .34, T, head=0, crouch=0.2, gain=0.72, ph=0.2)
    items.append(mk('m', 470, 712, .56, 1, 0.4, pose={'aR': 8 + 100 * ang * abs(math.sin(T * 3.0)), 'fR': 10, 'aL': 8 + 60 * ang, 'head': -6 * ang}, shirt=SHIRTS[1], pants=PANTS[1], mouth=speak(T, 0.0, 1.0) * ang * (1 - ev(T, 93.0, 93.4)), gain=.95, tint=CT))
    items.append(mk('j', 810, 712, .54, -1, 1.1, pose={'aR': 8 + 100 * ang * abs(math.sin(T * 3.3 + 1)), 'fR': 10, 'aL': 8 + 60 * ang, 'head': 6 * ang}, mouth=speak(T, 1.5, 1.0) * ang * (1 - ev(T, 93.0, 93.4)), gain=.95, tint=CT))
    hold = ev(T, 91.0, 91.8)
    items.append(mk('u', 640, 700, .46, 1, 0.9, pose={'aL': 8 + 70 * hold, 'aR': 8 + 70 * hold, 'fL': 10, 'fR': 10, 'head': 4 * math.sin(T * 5) * hold}, mouth=speak(T, 0.7, 0.5) * hold, gain=.95, tint=CT))
    items.append(mk('g', 330, 690, .40, 1, 2.1, pose={'aL': 8 + 40 * hold, 'head': 6 * math.sin(T * 4)}, gain=.85, tint=CT, crouch=0.1))
    draw_items(cv, cam, items, T)
    puffs(cv, T, 90.0, 93.3, 8, (350, 560, 560, 120), (95, 135, 178), seed=131, size=(60, 120), rise=(-6, 10), life=2.0, alpha=0.14)
    finish(cv, T, 66, 0.55, 22)


# ---------------------------------------------------------------- 18. despair (93.5 - 99.5)
def shot_despair(cv, T):
    k = seg(T, 93.4, 99.7); cam = Cam(A=(640, 640), sb=lerp(1.0, 1.08, k), sw=lerp(1.0, 1.2, k), sc=lerp(1.0, 1.14, k), d=(0, 0), dw=(0, 0))
    dk = ev(T, 93.6, 96.0); chamber_bg(cv, T, cam, 0.66 - 0.30 * dk, lamps=0.95 - 0.55 * dk)
    items = []
    for i, c in enumerate(GRID):
        w_ = ev(T, 93.8 + 0.02 * i, 94.8 + 0.02 * i); up = 0.0
        pose = {'head': 8 + 22 * w_ + 2 * math.sin(T * 0.7 + i), 'aL': 4, 'aR': 4}
        if i % 6 == 0: pose.update({'aL': 4 + 114 * w_, 'fL': 140 * w_, 'aR': 4 + 114 * w_, 'fR': 140 * w_})
        d_ = dict(c, pose=pose, crouch=0.3 * w_, gain=0.80, tint=CT)
        if i % 4 == 0: d_['rot'] = (84 if i % 8 else -84) * ev(T, 95.0 + 0.04 * i, 96.2 + 0.04 * i); d_['dy'] = 455 * ev(T, 95.0 + 0.04 * i, 96.2 + 0.04 * i)
        items.append(d_)
    draw_items(cv, cam, items, T)
    tone(cv, 1.0, 0, (0.94, 0.98, 1.05), 1.0); veil(cv, T, 0.10 + 0.08 * dk); finish(cv, T, 67, 0.55 + 0.1 * dk, 24)


# ---------------------------------------------------------------- 19. "how will we stay alive" (99.5 - 103.0 Luis looks up; 103.0 - 106.9 huddle)
def shot_q1(cv, T):
    k = seg(T, 99.4, 103.2); cam = Cam(A=(640, 640), sb=lerp(1.0, 1.12, k), sw=lerp(1.0, 1.30, k), sc=lerp(1.0, 1.22, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.42, lamps=0.55)
    items = sit_row((160, 280, 1000, 1120), 650, .34, T, head=18, crouch=0.6, gain=0.55, ph=0.9)
    up = ev(T, 99.9, 101.0) * (1 - ev(T, 102.2, 103.0))
    items.append(mk('u', 640, 716, .62, 1, 0.4, pose={'head': -14 * up + 3 * math.sin(T * 0.8), 'aL': 8, 'aR': 8 + 20 * up, 'fR': 10}, mouth=0.0, gain=1.0, tint=(0.95, 1.0, 1.06)))
    draw_items(cv, cam, items, T)
    lb = LightBuf(); q = cam.pt(640, 380); lb.glow(q[0], q[1], 300 * cam.sc, (80, 150, 255), 0.25 + 0.15 * up); lb.apply(cv, blur=40)
    veil(cv, T, 0.08); finish(cv, T, 68, 0.6, 24)


def shot_q2(cv, T):
    k = seg(T, 102.8, 107.1); cam = Cam(A=(640, 640), sb=lerp(1.04, 1.14, k), sw=lerp(1.1, 1.3, k), sc=lerp(1.0, 1.2, k), d=(0, 0), dw=(0, 0))
    wm = ev(T, 103.2, 105.5); chamber_bg(cv, T, cam, 0.5 + 0.2 * wm, lamps=0.6 + 0.4 * wm)
    items = []
    row = [(300, 690, .46, 1, 'm'), (440, 700, .50, 1, 'g'), (840, 700, .50, -1, 'j'), (980, 690, .46, -1, 'm'), (200, 640, .34, 1, 'm'), (1080, 640, .34, -1, 'm'), (560, 640, .30, 1, 'v'), (730, 640, .30, -1, 'y')]
    for i, (x, gy, sc, fl_, ch) in enumerate(row):
        hold = ev(T, 104.0 + 0.15 * i, 104.8 + 0.15 * i)
        items.append(mk(ch, x, gy, sc, fl_, i * 1.2, crouch=0.15 + 0.1 * (1 - hold), pose={'aL': 8 + 52 * hold, 'aR': 8 + 52 * hold, 'fL': -12 * hold, 'fR': -12 * hold, 'head': (8 if x < 640 else -8) * hold + 2 * math.sin(T + i)},
                        shirt=SHIRTS[(i * 3 + 1) % 10] if ch == 'm' else None, pants=PANTS[(i * 7 + 2) % 10] if ch == 'm' else None, gain=.86, tint=CT))
    items.append(mk('u', 640, 716, .58, 1, 0.4, pose={'aR': 8 + 20 * P(T, 104.5, 106.5), 'head': -4 * ev(T, 105.0, 106.0)}, mouth=speak(T, 0.3, 0.35) * (1.0 if 103.1 < T < 106.8 else 0.0), gain=1.0, tint=(0.96, 1.0, 1.06)))
    draw_items(cv, cam, items, T); finish(cv, T, 69, 0.5, 20)


# ---------------------------------------------------------------- 20. "after seventeen days, something changed" (106.9 - 109)
def shot_change(cv, T): P3.shot_depth(cv, T, 106.8, 109.0) if hasattr(P3, 'shot_depth') else shot_depth(cv, T, 106.8, 109.0)


SHOTS4 = [('hunger', 0.0, 5.8, shot_hunger, 0.0), ('nosun', 5.8, 9.1, shot_nosun, 0.5), ('notime', 9.1, 12.45, shot_notime, 0.4), ('listen', 12.45, 22.15, shot_listen, 0.5),
          ('vigil', 22.15, 29.05, shot_vigil, 0.6), ('rig', 29.05, 34.07, shot_rig, 0.5), ('decide', 34.07, 38.8, shot_decide, 0.5), ('map', 38.8, 41.55, shot_map, 0.35),
          ('sched', 41.55, 46.0, shot_sched, 0.35), ('mind', 46.0, 50.4, shot_mind, 0.4), ('lights', 50.4, 54.85, shot_lights, 0.2), ('routine', 54.85, 60.0, shot_routine, 0.3),
          ('tasks', 60.0, 64.15, shot_tasks, 0.3), ('yonni', 64.15, 69.5, shot_yonni, 0.4), ('victor', 69.5, 72.6, shot_victor, 0.4), ('scrib', 72.6, 78.7, shot_scrib, 0.3),
          ('joke', 78.7, 88.3, shot_joke, 0.5), ('fight', 88.3, 93.5, shot_fight, 0.3), ('despair', 93.5, 99.5, shot_despair, 0.4), ('q1', 99.5, 103.0, shot_q1, 0.4),
          ('q2', 103.0, 106.85, shot_q2, 0.4), ('change', 106.85, D4, shot_change, 0.5)]


class Part4:
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
