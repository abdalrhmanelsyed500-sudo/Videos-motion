"""Part 3 (Arabic, 62.7 s): the emergency refuge, the food stock, Urzua's decision: food becomes time.
Same STYLE LOCK as parts 1-2. No captions, no music (SFX only)."""
import cv2, math, numpy as np
import hook_scenes as HS
from hook_scenes import *
import part2_scenes as P2
from part2_scenes import draw_items, mk, head_pt, speak, kid
for _k in 'usgj': HS.RIG[_k] = HS.RIG['m']

D3 = 62.7


def bpt(cam, px, py):
    """plate pixel -> screen on the BASE plate layer"""
    return cam.A[0] + cam.d[0] + cam.sb * (S0 * px - OX - cam.A[0]), cam.A[1] + cam.d[1] + cam.sb * (S0 * py - OY - cam.A[1])


def food_at(cv, cam, nm, x, y, sc, e=1.0, rot=0.0, gain=0.95, dark=1.0):
    if e <= 0: return
    sq = 1 + 0.25 * math.sin(clamp(e) * math.pi) * (1 - clamp(e)) * 2; drop = (1 - ease_out(clamp(e))) * -70
    Xc, Yc = cam.pt(x, y + drop); lyr = L(nm)
    shadow(cv, Xc, Yc + 4, sc * cam.sc * 0.35, a=0.5)
    place(cv, lyr, M3(Xc, Yc, sc * cam.sc * sq, sc * cam.sc / sq, rot, lyr.w / 2, lyr.h), gain=gain * dark, tint=(0.95, 1.0, 1.08))


def chamber_bg(cv, T, cam, dark=0.8, lamps=1.0, kill=None):
    plate(cv, 'h_p6', cam, 'b'); plate(cv, 'h_p6_wl', cam, 'w'); plate(cv, 'h_p6_wr', cam, 'w')
    cv *= dark
    lb = LightBuf(); fl = 0.85 + 0.15 * flick(T, 2.0)
    for i, (px, py, r_, a) in enumerate(((186, 312, 90, 1.0), (561, 328, 110, 1.0), (1079, 352, 90, 1.0))):
        k = lamps if kill is None or i != kill[0] else kill[1]
        q = cam.pt(S0 * px - OX, S0 * py - OY); lb.glow(q[0], q[1], r_ * cam.sw * 0.5, (90, 170, 255), 0.55 * fl * k); lb.glow(q[0], q[1], 330 * cam.sw, (40, 100, 200), 0.30 * fl * k)
    lb.apply(cv, blur=30)


def finish(cv, T, seed, vig=0.4, motes_n=30):
    motes(cv, T, seed, motes_n, 0.5, (210, 225, 245)); vignette(cv, vig, 2.0)


def grid33():
    out = []; k = 0
    for gy, sc, n, x0, dx in ((585, .15, 14, 70, 92), (640, .22, 11, 65, 118), (702, .31, 8, 120, 148)):
        for j in range(n):
            out.append(dict(ch='m', x=x0 + dx * j + (14 if k % 2 else -10), gy=gy + (k % 3) * 3, sc=sc * (1 + 0.05 * (((k * 5) % 4) - 1.5) / 1.5), flip=1 if k % 2 == 0 else -1, ph0=k * 0.97,
                            shirt=SHIRTS[(k * 3) % len(SHIRTS)], pants=PANTS[(k * 7 + 2) % len(PANTS)])); k += 1
    return out


GRID = grid33()
HOT = (0.88, 0.97, 1.12)


# ------------------------------------------------------------------ 1. the choice: the refuge door (0 - 3.35)
DOOR_CREW = [(300, 690, .40, 1), (520, 640, .30, -1), (760, 690, .38, 1), (980, 650, .31, -1), (430, 600, .22, 1), (900, 592, .20, -1), (660, 562, .15, 1), (1120, 706, .44, -1)]


def door_cam(k, k2=0.0):
    return Cam(A=(880, 420), sb=lerp(1.0, 1.32, k), sw=lerp(1.0, 1.55, k), sc=lerp(1.0, 1.28, k), d=(0, 0), dw=(0, 0))


def door_bg(cv, T, cam, glow=1.0):
    plate(cv, 'h3_door', cam, 'b'); plate(cv, 'h3_door_wl', cam, 'w'); plate(cv, 'h3_door_wr', cam, 'w')
    lb = LightBuf(); q = bpt(cam, 882, 395); fl = 0.85 + 0.15 * flick(T, 4.0)
    lb.glow(q[0], q[1], 48 * cam.sb, (110, 190, 255), 0.7 * fl * glow); lb.glow(q[0], q[1], 260 * cam.sb, (60, 130, 230), 0.35 * fl * glow)
    ql = bpt(cam, 340, 300); lb.glow(ql[0], ql[1], 160 * cam.sb, (70, 150, 255), 0.4 * fl); lb.apply(cv, blur=28)


def shot_door1(cv, T):
    k = seg(T, 0, 3.5); cam = door_cam(ease_out(k) * 0.7 + k * 0.3); door_bg(cv, T, cam)
    items = []
    for i, (x, gy, sc, fl_) in enumerate(DOOR_CREW):
        look = sstep(seg(T, 1.5, 2.2)); lost = (1 - look) * 7 * math.sin(T * 1.3 + i * 1.9)
        side = 1 if x < 880 else -1
        P = {'head': lost + side * 9 * look, 'aL': 6 + 4 * math.sin(T + i), 'aR': 6 + 4 * math.sin(T * 1.1 + i)}
        if i == 2: ptq = sstep(seg(T, 1.9, 2.5)); P['aR'] = 8 + 70 * ptq; P['fR'] = -6 * ptq
        items.append(mk('m', x, gy, sc, fl_, i * 1.3, pose=P, crouch=0.12, gain=0.9, tint=HOT, shirt=SHIRTS[(i * 3) % 10], pants=PANTS[(i * 7 + 2) % 10]))
    draw_items(cv, cam, items, T); puffs(cv, T, 0, 3.5, 8, (200, 380, 800, 300), (95, 135, 178), seed=91, size=(100, 220), rise=(-4, 8), life=3.0, alpha=0.14)
    finish(cv, T, 33, 0.35)


# ------------------------------------------------------------------ 2. carved inside the mountain (3.35 - 5.4)
def shot_cross(cv, T):
    shot_depth(cv, T, 3.2, 5.3)


# ------------------------------------------------------------------ 3. 33 men enter (5.4 - 7.66)
ENTER = [dict(ch='m', t0=5.15 + 0.17 * i, dur=1.9 + 0.1 * (i % 3), flip=1 if i % 2 else -1, ph0=i * 1.1, i=i) for i in range(12)]


def shot_enter(cv, T):
    k = seg(T, 5.2, 7.9); cam = Cam(A=(880, 470), sb=lerp(1.10, 1.30, k), sw=lerp(1.2, 1.5, k), sc=lerp(1.0, 1.15, k), d=(0, 0), dw=(0, 0)); door_bg(cv, T, cam, 1.1)
    items = []
    for c in ENTER:
        s = clamp((T - c['t0']) / c['dur'])
        if s <= 0 or s >= 1: continue
        u = ease_in(s) * 0.25 + s * 0.75; X = lerp(100 + 40 * (c['i'] % 3), 880, u); gy = lerp(700 - 12 * (c['i'] % 3), 428, u ** 0.9)
        sc = max(0.03, 0.0013 * (gy - 388)); fade = 1 - sstep(seg(s, 0.86, 1.0))
        items.append(mk('m', X, gy, sc, 1, c['ph0'], walk=1.0, gain=0.9 * (0.5 + 0.5 * (1 - s * 0.6)) * fade, tint=HOT, crouch=0.08, shirt=SHIRTS[(c['i'] * 3) % 10], pants=PANTS[(c['i'] * 7 + 2) % 10], pose={'head': -4 + 3 * math.sin(T + c['i'])}))
    draw_items(cv, cam, items, T); finish(cv, T, 34, 0.35)


# ------------------------------------------------------------------ 4. narrow, suffocating heat, bad air (7.66 - 11.12)
def crowd_items(T, rows_scale=1.0, mode='cramped', t0=0.0):
    items = []
    for i, c in enumerate(GRID):
        P = {}; crouch = 0.08; mouth = 0.0
        if mode == 'cramped':
            if i % 4 == 0: f = sstep(seg(T, 8.0, 8.4)); P['aR'] = f * (100 + 40 * math.sin(2 * math.pi * 3.0 * T + i)); P['fR'] = f * (60 + 40 * math.sin(2 * math.pi * 3.0 * T + i + 1))
            elif i % 4 == 1: w_ = pulse(T, 8.4 + 0.05 * i, 9.3 + 0.05 * i); P['aL'] = 118 * w_; P['fL'] = 140 * w_
            elif i % 4 == 2: cg = pulse(T, 9.5, 10.2) * (i % 3 == 0); P['aL'] = 20 * cg; P['fL'] = 128 * cg; crouch += 0.2 * cg; P['head'] = -8 * cg
            P['head'] = P.get('head', 0) + 5 * sstep(seg(T, 7.7, 8.5)) + 2 * math.sin(T * 0.9 + i); crouch += 0.1 * sstep(seg(T, 7.7, 9.0))
        items.append(dict(c, pose=P, crouch=crouch, mouth=mouth, gain=0.80, tint=(0.85, 0.96, 1.1)))
    return items


def shot_cramped(cv, T):
    k = seg(T, 7.5, 11.3); cam = Cam(A=(680, 640), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.22, k), sc=lerp(1.0, 1.13, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.75)
    draw_items(cv, cam, crowd_items(T), T)
    heat = 1.0 + 1.2 * sstep(seg(T, 8.4, 9.5)); cv[:] = heat_haze(cv, T, heat, 0.05, 2.2, 150, 700)
    tone(cv, 1.0, 0, (0.90, 0.97, 1.10), 1.0)
    puffs(cv, T, 9.0, 11.2, 14, (200, 100, 880, 300), (95, 135, 178), seed=92, size=(100, 240), rise=(-4, 8), life=3.0, alpha=0.20)
    finish(cv, T, 35, 0.45)


# ------------------------------------------------------------------ 5. searching (11.12 - 13.96)  /  6. found the stock (13.96 - 20.57)
def storage_cam(k, z=1.0):
    return Cam(A=(700, 520), sb=lerp(1.0, 1.10, k) * z, sw=lerp(1.0, 1.18, k) * z, sc=lerp(1.0, 1.10, k) * z, d=(0, 0), dw=(0, 0))


def storage_bg(cv, T, cam, dark=1.0):
    plate(cv, 'h3_storage', cam, 'b', gain=dark)
    lb = LightBuf(); q = bpt(cam, 1000, 100); fl = 0.88 + 0.12 * flick(T, 5.0)
    lb.glow(q[0], q[1], 50 * cam.sb, (110, 190, 255), 0.7 * fl); lb.glow(q[0], q[1], 300 * cam.sb, (60, 130, 230), 0.34 * fl); lb.apply(cv, blur=28)


def shot_search(cv, T):
    cam = storage_cam(seg(T, 10.9, 14.2)); storage_bg(cv, T, cam)
    lk = sstep(seg(T, 11.5, 12.1)); lk2 = pulse(T, 12.2, 13.4)
    items = [mk('m', 700, 690, .50, 1, 0.3, crouch=0.30 * lk, pose={'head': 16 * lk * (1 - lk2) - 4 + 3 * math.sin(T * 2), 'aL': 30 * lk + 20 * lk2, 'fL': -45 * lk, 'aR': 20 * lk, 'fR': -20 * lk}, shirt=SHIRTS[1], pants=PANTS[1], gain=.95, tint=HOT),
             mk('m', 980, 650, .38, -1, 1.7, crouch=0.2 * lk, pose={'head': -12 * lk + 6 * math.sin(T * 2.3), 'aR': 14 + 70 * pulse(T, 11.9, 12.8), 'fR': 20}, shirt=SHIRTS[4], pants=PANTS[5], gain=.95, tint=HOT),
             mk('m', 400, 700, .50, 1, 3.1, crouch=0.15, pose={'head': 12 * math.sin(T * 1.4) + 10 * lk, 'aL': 8, 'aR': 8 + 16 * lk2}, shirt=SHIRTS[6], pants=PANTS[2], gain=.95, tint=HOT)]
    draw_items(cv, cam, items, T); finish(cv, T, 36, 0.4)


FOUND = [('food_0', 700, 660, .28, 15.81), ('food_1', 790, 672, .27, 16.0), ('food_2', 880, 656, .27, 16.2), ('food_3', 975, 640, .30, 16.74), ('food_4', 1075, 668, .26, 17.82), ('food_6', 610, 672, .27, 18.6)]


def shot_found(cv, T):
    cam = storage_cam(seg(T, 13.8, 20.6), 1.0); storage_bg(cv, T, cam)
    # crate lowered off the shelf by a miner (14.0 - 15.4) then set down
    ce = clamp((T - 14.1) / 1.3); cy = lerp(540, 690, ease_out(ce)) if T >= 14.1 else 540
    reach = sstep(seg(T, 13.8, 14.2)) * (1 - sstep(seg(T, 15.2, 15.6)))
    items = [mk('m', 560, 690, .52, 1, 0.3, pose={'aL': 20 + 100 * reach, 'aR': 16 + 100 * reach, 'fL': 8, 'fR': 8, 'head': -10 * reach + 4 * math.sin(T * 1.5)}, shirt=SHIRTS[1], pants=PANTS[1], gain=.95, tint=HOT, crouch=0.2 * sstep(seg(T, 14.8, 15.4))),
             mk('m', 900, 700, .50, -1, 1.9, pose={'head': 6 * sstep(seg(T, 15.3, 16.0)) + 3 * math.sin(T * 1.2), 'aR': 10 + 70 * pulse(T, 16.5, 17.7)}, shirt=SHIRTS[3], pants=PANTS[3], gain=.95, tint=HOT),
             mk('m', 1130, 692, .46, 1, 3.2, pose={'head': -8 * sstep(seg(T, 15.8, 16.4)) + 3 * math.sin(T * 1.4), 'aL': 8 + 100 * pulse(T, 18.4, 19.5), 'fL': 20 * pulse(T, 18.4, 19.5)}, shirt=SHIRTS[6], pants=PANTS[5], gain=.95, tint=HOT)]
    draw_items(cv, cam, items, T)
    if T >= 14.1 and T < 15.8:
        food_at(cv, cam, 'food_5', 560, cy if T < 15.4 else 690, .38, e=1.0)
    elif T >= 15.8: food_at(cv, cam, 'food_5', 560, 690, .38, e=1.0)
    for nm, fx, fy, fs, tt in FOUND: food_at(cv, cam, nm, fx, fy, fs, e=clamp((T - tt) / 0.5))
    # 'وبس' - silence, all heads sink
    sink = sstep(seg(T, 19.8, 20.3))
    cv *= 1 - 0.18 * sink
    finish(cv, T, 37, 0.45)


# ------------------------------------------------------------------ table scenes
def table_cam(k, z0=1.0, z1=1.1, A=(640, 440)):
    z = lerp(z0, z1, k); return Cam(A=A, sb=z, sw=z, sc=z, d=(0, 0), dw=(0, 0))


CLOCK = (828, 280)


def table_bg(cv, T, cam, dark=1.0, hands=None, glow=0.0):
    plate(cv, 'h3_table', cam, 'b', gain=dark)
    cx, cy = bpt(cam, *CLOCK); r = 75 * S0 * cam.sb
    if hands is not None:
        hh, mm = hands   # angle in turns
        for ang, ln, wd, col in ((mm * 2 * math.pi, 0.80, 2.2, (22, 30, 40)), (hh * 2 * math.pi, 0.52, 3.6, (20, 28, 38))):
            x2 = cx + math.sin(ang) * r * ln; y2 = cy - math.cos(ang) * r * ln
            cv2.line(cv, (int(cx + 2), int(cy + 2)), (int(x2 + 2), int(y2 + 2)), (10.0, 14.0, 20.0), max(1, int(wd * cam.sb * 1.25)), cv2.LINE_AA)
            cv2.line(cv, (int(cx), int(cy)), (int(x2), int(y2)), tuple(float(c) for c in col), max(1, int(wd * cam.sb)), cv2.LINE_AA)
        cv2.circle(cv, (int(cx), int(cy)), max(2, int(4 * cam.sb)), (20.0, 28.0, 38.0), -1, cv2.LINE_AA)
    lb = LightBuf(); q = bpt(cam, 700, 130); fl = 0.88 + 0.12 * flick(T, 6.0)
    lb.glow(q[0], q[1], 46 * cam.sb, (110, 190, 255), 0.7 * fl); lb.glow(q[0], q[1], 340 * cam.sb, (60, 130, 230), 0.36 * fl)
    if glow > 0: lb.glow(cx, cy, r * 1.5, (90, 170, 255), 0.6 * glow); lb.glow(cx, cy, r * 3.0, (50, 120, 230), 0.3 * glow)
    lb.apply(cv, blur=28)


def table_fg(cv, cam, dark=1.0): plate(cv, 'h3_table_fg', cam, 'b', gain=dark)


# 7. enough for two days (20.57 - 23.7): fast clock
TFOOD = [('food_0', 545, 505, .17), ('food_1', 590, 520, .16), ('food_3', 668, 500, .17), ('food_4', 735, 515, .15), ('food_6', 625, 490, .15)]


def shot_twodays(cv, T):
    k = seg(T, 20.4, 23.9); cam = table_cam(k, 1.05, 1.22, (700, 440))
    prog = ease_in(clamp((T - 21.2) / 2.3)) * 0.4 + clamp((T - 21.2) / 2.3) * 0.6; hh = 0.1 + 2.0 * prog
    table_bg(cv, T, cam, 0.95, hands=(hh % 1.0, (hh * 6) % 1.0), glow=0.5 * sstep(seg(T, 20.9, 21.4)))
    items = [mk('u', 500, 522, .38, 1, 0.2, pose={'head': 4 * math.sin(T * 1.2), 'aR': 10, 'fR': -30, 'aL': 12}, gain=.85, tint=(.88, .98, 1.1)),
             mk('m', 880, 520, .32, -1, 1.4, pose={'head': -6 * sstep(seg(T, 21.0, 21.7)) + 3 * math.sin(T), 'aL': 12 + 60 * pulse(T, 22.0, 23.0)}, shirt=SHIRTS[4], pants=PANTS[2], gain=.85, tint=(.88, .98, 1.1))]
    draw_items(cv, cam, items, T); table_fg(cv, cam, 0.95)
    for nm, fx, fy, fs in TFOOD: food_at(cv, cam, nm, fx, fy, fs, e=1.0, dark=0.95)
    finish(cv, T, 38, 0.45, 18)


# 8. 33 men + two days of food (23.7 - 26.49)
def shot_count(cv, T):
    k = seg(T, 23.5, 26.7); cam = Cam(A=(680, 640), sb=lerp(1.02, 1.10, k), sw=lerp(1.0, 1.2, k), sc=lerp(1.0, 1.12, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.82)
    items = []
    for i, c in enumerate(GRID):
        e = clamp((T - (23.75 + 0.034 * i)) / 0.18)
        if e <= 0: continue
        hop = 12 * math.sin(e * math.pi)
        P = {'head': 4 * math.sin(T * 1.1 + i)}
        if T > 25.0: P['head'] = (-10 if c['x'] > 640 else 10) * sstep(seg(T, 25.0, 25.8)) * 0.8 + 2 * math.sin(T + i)
        items.append(dict(c, pose=P, crouch=0.08, hop=hop, gain=0.84 * (0.4 + 0.6 * e), tint=(0.85, 0.96, 1.1)))
    draw_items(cv, cam, items, T)
    for nm, fx, fy, fs in (('food_0', 640, 666, .17), ('food_3', 676, 672, .15), ('food_4', 612, 674, .14)): food_at(cv, cam, nm, fx, fy, fs, e=clamp((T - 25.2) / 0.5))
    tone(cv, 1.0, 0, (0.93, 0.98, 1.08), 1.0); finish(cv, T, 39, 0.45)


# 9. eating normally: everything is gone (26.49 - 29.39)
EAT = [(1, 'food_0', 26.9), (2, 'food_1', 27.15), (0, 'food_2', 27.4), (3, 'food_3', 27.7), (4, 'food_4', 28.0), (1, 'food_6', 28.3)]


def shot_eat(cv, T):
    k = seg(T, 26.3, 29.5); cam = table_cam(k, 1.08, 1.02, (700, 440))
    table_bg(cv, T, cam, 0.95, hands=(0.25 + 0.05 * (T - 26), 0.6 + 0.35 * (T - 26)))
    items = []
    for i, x in enumerate((420, 520, 600, 780, 860, 960)):
        gy = 520 + (i % 2) * 6; c = dict(ch='m', x=x, gy=gy, sc=.32 + .02 * (i % 3), flip=1 if i % 2 else -1, ph0=i * 1.3)
        e = pulse(T, 26.8 + 0.28 * i, 27.5 + 0.28 * i) + pulse(T, 27.9 + 0.2 * i, 28.5 + 0.2 * i)
        side = 'aL' if i % 2 else 'aR'; f = 'fL' if i % 2 else 'fR'
        items.append(dict(c, pose={side: 118 * e, f: 140 * e, 'head': -4 * e + 3 * math.sin(T * 1.4 + i), 'lean': 0.0}, shirt=SHIRTS[(i * 3 + 1) % 10], pants=PANTS[(i * 7 + 2) % 10], gain=.85, tint=(.88, .98, 1.1), crouch=0.04 * e))
    draw_items(cv, cam, items, T); table_fg(cv, cam, 0.95)
    for j, (nm, fx, fy, fs) in enumerate(TFOOD):
        gone = EAT[j][2] if j < len(EAT) else 27.5
        e = 1.0 - clamp((T - gone) / 0.3)
        if e > 0: food_at(cv, cam, nm, fx, fy, fs * (0.4 + 0.6 * e), e=1.0, dark=0.95 * e)
    finish(cv, T, 40, 0.45, 16)


# 10. if they ate it all they'd die waiting: weak men (29.39 - 32.23)
def shot_weak(cv, T):
    k = seg(T, 29.2, 32.4); cam = Cam(A=(680, 640), sb=lerp(1.0, 1.12, k), sw=lerp(1.0, 1.26, k), sc=lerp(1.0, 1.15, k), d=(0, 0), dw=(0, 0))
    dark = lerp(0.8, 0.5, sstep(seg(T, 29.4, 30.8))); chamber_bg(cv, T, cam, dark, lamps=lerp(1.0, 0.7, sstep(seg(T, 29.4, 31.5))))
    items = []
    for i, c in enumerate(GRID):
        w_ = sstep(seg(T, 29.4 + 0.015 * i, 30.2 + 0.015 * i)); up = sstep(seg(T, 31.0, 31.7))
        P = {'head': 18 * w_ * (1 - up) - 14 * up + 2 * math.sin(T * 0.8 + i), 'aL': 4, 'aR': 4}
        items.append(dict(c, pose=P, crouch=0.72 * w_ * (1 - 0.3 * up), gain=0.80, tint=(0.85, 0.96, 1.1)))
    draw_items(cv, cam, items, T)
    tone(cv, 1.0, 0, (0.95, 0.99, 1.06), 1.0); veil(cv, T, 0.10 * sstep(seg(T, 29.4, 31)))
    finish(cv, T, 41, 0.55, 24)


# 11. Urzua's decision (32.23 - 35.11)
def shot_luis1(cv, T):
    k = seg(T, 32.1, 35.3); cam = Cam(A=(640, 640), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.24, k), sc=lerp(1.0, 1.16, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.5, lamps=0.8)
    items = []
    for i, c in enumerate(GRID[:22]):
        if abs(c['x'] - 640) < 150 and c['gy'] > 640: continue
        items.append(dict(c, pose={'head': 6 + 2 * math.sin(T + i)}, crouch=0.2, gain=0.72, tint=(0.85, 0.96, 1.1)))
    th = sstep(seg(T, 32.6, 33.3)) * (1 - sstep(seg(T, 34.6, 35.2)))
    items.append(mk('u', 640, 712, .56, 1, 0.4, pose={'aR': 8 + 117 * th, 'fR': 8 + 132 * th, 'aL': 8, 'fL': -20 * th, 'head': 4 * math.sin(T * 0.9) - 4 * th}, gain=1.0, tint=(0.95, 1.0, 1.06)))
    draw_items(cv, cam, items, T)
    lb = LightBuf(); q = cam.pt(640, 420); lb.glow(q[0], q[1], 360 * cam.sc, (80, 150, 255), 0.35 * sstep(seg(T, 32.3, 33.3))); lb.apply(cv, blur=40)
    finish(cv, T, 42, 0.5, 20)


# 12. food became time (35.11 - 40.34)
SIT_L = [(150, 690, .42, 1), (270, 700, .44, -1), (140, 600, .30, 1)]
SIT_R = [(1130, 690, .42, -1), (1020, 700, .44, 1), (1150, 600, .30, -1)]


def shot_time(cv, T):
    k = seg(T, 35.0, 40.5); cam = table_cam(k, 1.0, 1.12, (680, 420))
    cl = sstep(seg(T, 37.7, 38.1)) * (1 - sstep(seg(T, 39.0, 39.8)))
    table_bg(cv, T, cam, 0.92, hands=(0.12 + 0.002 * (T - 35), 0.3 + 0.03 * (T - 35)), glow=cl)
    spk = 1.0 if 35.2 < T < 40.2 else 0.0; g1 = pulse(T, 35.6, 37.0); g2 = pulse(T, 37.2, 38.6); g3 = pulse(T, 38.6, 40.1)
    P = {'aL': 12 + 50 * g1 + 40 * g3, 'aR': 12 + 38 * g2 + 70 * g3 * abs(math.sin(T * 6.0)), 'fL': 20 * g1, 'fR': 30 * g2, 'head': 3 * math.sin(T * 1.3) - 3 * g3}
    items = [mk('u', 640, 524, .40, 1, 0.3, pose=P, mouth=speak(T, 0.3, 0.45) * spk, gain=.95, tint=(.94, 1.0, 1.06))]
    for i, (x, gy, sc, fl_) in enumerate(SIT_L + SIT_R):
        items.append(mk('m', x, gy, sc, fl_, i * 1.2, crouch=0.18, pose={'head': 4 * math.sin(T * 1.1 + i) + (4 if x < 640 else -4) * sstep(seg(T, 36.0, 37.0)), 'aL': 4, 'aR': 4}, shirt=SHIRTS[(i * 3 + 1) % 10], pants=PANTS[(i * 7 + 2) % 10], gain=.8, tint=(.85, .96, 1.1)))
    draw_items(cv, cam, items, T); table_fg(cv, cam, 0.92)
    for nm, fx, fy, fs in (('food_0', 600, 500, .15), ('food_3', 690, 497, .15), ('food_4', 745, 510, .13)): food_at(cv, cam, nm, fx, fy, fs, e=1.0, dark=0.92)
    finish(cv, T, 43, 0.45, 16)


# 13. tiny rations (40.34 - 46.11)
def shot_ration(cv, T):
    k = seg(T, 40.2, 46.3); cam = table_cam(k, 1.28, 1.42, (680, 470))
    table_bg(cv, T, cam, 0.95, hands=(0.14, 0.9 + 0.03 * (T - 40)))
    sw_ = math.sin(2 * math.pi * 0.7 * T)
    P = {'aL': 36 + 24 * sw_, 'aR': 36 - 24 * sw_, 'fL': -30 + 18 * sw_, 'fR': -30 - 18 * sw_, 'head': 6 + 3 * math.sin(T * 1.2)}
    items = [mk('u', 640, 526, .42, 1, 0.3, pose=P, gain=.95, tint=(.94, 1.0, 1.06))]
    for i, x in enumerate((330, 420, 880, 970)):
        items.append(mk('m', x, 522 + (i % 2) * 6, .34, 1 if i < 2 else -1, i * 1.3, pose={'head': 5 * math.sin(T * 1.2 + i) + 4 * sstep(seg(T, 41.0, 41.8)), 'aL': 4, 'aR': 4}, shirt=SHIRTS[(i * 3 + 1) % 10], pants=PANTS[(i * 7 + 2) % 10], gain=.85, tint=(.88, .98, 1.1)))
    draw_items(cv, cam, items, T); table_fg(cv, cam, 0.95)
    # rations on the table: small and exact
    for j in range(3): food_at(cv, cam, ('food_0', 'food_1', 'food_2')[j], 560 + 52 * j, 508 + 3 * j, .10, e=clamp((T - (41.5 + 0.12 * j)) / 0.4), dark=0.95)
    for j in range(3): food_at(cv, cam, 'food_3', 660 + 48 * j, 502 + 3 * j, .10, e=clamp((T - (43.7 + 0.12 * j)) / 0.4), dark=0.95)
    for j in range(3): food_at(cv, cam, 'food_4', 575 + 62 * j + 130, 528 + 2 * j, .09, e=clamp((T - (44.7 + 0.12 * j)) / 0.4), dark=0.95)
    finish(cv, T, 44, 0.45, 14)


# 14. eating by plan, not by hunger (46.11 - 49.36)
def shot_plan(cv, T):
    k = seg(T, 46.0, 49.5); cam = Cam(A=(680, 640), sb=lerp(1.0, 1.08, k), sw=lerp(1.0, 1.18, k), sc=lerp(1.0, 1.10, k), d=(0, 0), dw=(0, 0))
    night = 0.5 + 0.5 * math.cos(2 * math.pi * (T - 46.0) / 2.6); chamber_bg(cv, T, cam, 0.62 + 0.18 * night)
    items = []
    for i, c in enumerate(GRID):
        g = 0.0
        if i == 14: g = pulse(T, 46.6, 47.3) * (1 - sstep(seg(T, 47.0, 47.6)))
        P = {'head': 6 * math.sin(T * 0.9 + i) + 6, 'aL': 6, 'aR': 6 + 100 * g, 'fR': -15 * g}
        if i % 5 == 0: P['aL'] = 4 + 18 * pulse(T, 47.8 + 0.03 * i, 48.8 + 0.03 * i)
        items.append(dict(c, pose=P, crouch=0.3, gain=0.78, tint=(0.85, 0.96, 1.1)))
    draw_items(cv, cam, items, T)
    for nm, fx, fy, fs in (('food_0', 640, 666, .13), ('food_3', 672, 672, .12), ('food_4', 610, 674, .11)): food_at(cv, cam, nm, fx, fy, fs, e=1.0)
    tone(cv, 1.0, 0, (0.92 + 0.04 * night, 0.98, 1.08 - 0.04 * night), 1.0); finish(cv, T, 45, 0.5, 20)


# 15. trust (49.36 - 53.22)
def shot_trust(cv, T):
    k = seg(T, 49.3, 53.3); cam = Cam(A=(680, 640), sb=lerp(1.0, 1.06, k), sw=lerp(1.0, 1.16, k), sc=lerp(1.0, 1.22, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.85)
    items = []
    row = [(150, 640, .36), (300, 645, .36), (450, 650, .38), (610, 650, .40), (770, 650, .40), (930, 645, .38), (1090, 640, .36), (1240, 638, .34)]
    for i, (x, gy, sc) in enumerate(row):
        hold = sstep(seg(T, 49.8 + 0.12 * i, 50.6 + 0.12 * i)); nod = pulse(T, 50.6 + 0.2 * i, 51.4 + 0.2 * i)
        items.append(mk('m', x, gy, sc, 1 if i % 2 else -1, i * 1.1, pose={'aL': 60 * hold, 'aR': 60 * hold, 'fL': -12 * hold, 'fR': -12 * hold, 'head': 10 * nod + 2 * math.sin(T + i)}, shirt=SHIRTS[(i * 3 + 1) % 10], pants=PANTS[(i * 7 + 2) % 10], gain=.88, tint=(.9, .98, 1.08)))
    for i, c in enumerate(GRID[:11]): items.append(dict(c, pose={'head': 4 * math.sin(T + i)}, crouch=0.1, gain=0.70, tint=(0.85, 0.96, 1.1)))
    draw_items(cv, cam, items, T); finish(cv, T, 46, 0.45, 20)


# 16. one man takes extra, the price is someone else's life (53.22 - 57.75)
def shot_cost(cv, T):
    k = seg(T, 53.0, 57.9); cam = table_cam(k, 1.15, 1.32, (lerp(700, 560, sstep(seg(T, 55.8, 57.8))), 470))
    table_bg(cv, T, cam, 0.62, hands=(0.14, 0.2 + 0.02 * (T - 53)))
    rch = sstep(seg(T, 53.8, 54.5)) * (1 - sstep(seg(T, 55.2, 55.9)))
    items = [mk('s', 620, 522, .40, 1, 0.3, pose={'aR': 15 + 38 * rch, 'fR': -22 * rch + 6 * math.sin(T * 14) * rch, 'head': 10 * rch - 5 * sstep(seg(T, 55.3, 56.0)), 'aL': 6}, gain=.80, tint=(.85, .96, 1.1), crouch=0.15 + 0.12 * rch),
             mk('g', 360, 700, .52, 1, 1.5, pose={'head': 12 + 2 * math.sin(T * 0.8), 'aL': 4, 'aR': 4}, crouch=0.55, gain=.78, tint=(.85, .96, 1.1)),
             mk('m', 1000, 690, .50, -1, 2.5, pose={'head': 12 + 2 * math.sin(T * 0.9 + 1), 'aL': 4, 'aR': 4}, crouch=0.5, shirt=SHIRTS[4], pants=PANTS[2], gain=.75, tint=(.85, .96, 1.1))]
    draw_items(cv, cam, items, T); table_fg(cv, cam, 0.62)
    for nm, fx, fy, fs in (('food_0', 780, 452, .08), ('food_3', 830, 450, .075), ('food_4', 805, 462, .07)): food_at(cv, cam, nm, fx, fy, fs, e=1.0, dark=0.7)
    tone(cv, 1.0, 0, (0.95, 0.99, 1.06), 1.0); finish(cv, T, 47, 0.55, 16)


# 17. a bigger problem (57.75 - 60.24)
def shot_big(cv, T):
    k = seg(T, 57.6, 60.4); A = 1.2 * sstep(seg(T, 58.6, 59.2)) * (1 - sstep(seg(T, 60.0, 60.4))); dxy = shake_xy(T, A)
    cam = Cam(A=(680, 600), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.24, k), sc=lerp(1.0, 1.16, k), d=dxy, dw=(dxy[0] * 1.5, dxy[1] * 1.5))
    chamber_bg(cv, T, cam, 0.6, kill=(1, 1.0 - 0.8 * sstep(seg(T, 59.0, 59.6))))
    items = []
    for i, c in enumerate(GRID):
        lk = sstep(seg(T, 58.0 + 0.01 * i, 58.7 + 0.01 * i))
        items.append(dict(c, pose={'head': 10 * (1 - lk) - 16 * lk + 2 * math.sin(T * 5 + i) * lk, 'aL': 4, 'aR': 4}, crouch=0.3 * (1 - 0.6 * lk), gain=0.76, tint=(0.85, 0.96, 1.1)))
    draw_items(cv, cam, items, T)
    puffs(cv, T, 58.6, 60.2, 12, (100, 0, 1080, 120), (95, 135, 178), seed=93, size=(70, 160), rise=(30, 90), life=1.8, alpha=0.30)
    veil(cv, T, 0.10 * sstep(seg(T, 58.5, 60.0))); finish(cv, T, 48, 0.6, 24)


# 18. nobody above ground knows (60.24 - 62.7): up through the rock to the empty surface
def shot_above(cv, T):
    k = sstep(seg(T, 60.2, 62.3)); sS = 1.75 * S0
    oy = lerp(768 * sS - H, 0, k); ox = (1376 * sS - W) / 2 + 40 * math.sin(T * 0.4) + lerp(-60, 40, k)
    Mz = M3(-ox, -oy, sS, sS, 0, 0, 0)
    place(cv, L('h_p4'), Mz, gain=0.95)
    r = rng(33)
    for i in range(60):
        x = r.random() * W; sp = 10 + 20 * r.random(); y = ((r.random() * H) - T * sp) % H; c = 120 + 100 * r.random()
        cv2.circle(cv, (int(x), int(y)), 1, (c * .7, c * .85, c), -1, cv2.LINE_AA)
    vignette(cv, 0.35 + 0.35 * k, 2.0)
    lb = LightBuf(); gl = 1 - k; lb.glow(560, 690 + k * 300, 200, (60, 130, 255), 0.6 * gl); lb.apply(cv, blur=40)


# (name, t0, t1, fn, crossfade seconds)
SHOTS3 = [('door1', 0.0, 3.35, shot_door1, 0.0), ('cross', 3.35, 5.40, shot_cross, 0.3), ('enter', 5.40, 7.66, shot_enter, 0.3), ('cramped', 7.66, 11.12, shot_cramped, 0.3),
          ('search', 11.12, 13.96, shot_search, 0.3), ('found', 13.96, 20.57, shot_found, 0.35), ('twodays', 20.57, 23.70, shot_twodays, 0.35), ('count', 23.70, 26.49, shot_count, 0.25),
          ('eat', 26.49, 29.39, shot_eat, 0.3), ('weak', 29.39, 32.23, shot_weak, 0.3), ('luis1', 32.23, 35.11, shot_luis1, 0.3), ('time', 35.11, 40.34, shot_time, 0.3),
          ('ration', 40.34, 46.11, shot_ration, 0.3), ('plan', 46.11, 49.36, shot_plan, 0.3), ('trust', 49.36, 53.22, shot_trust, 0.3), ('cost', 53.22, 57.75, shot_cost, 0.4),
          ('big', 57.75, 60.24, shot_big, 0.4), ('above', 60.24, D3, shot_above, 0.5)]


class Part3:
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTS3):
            hi = t1 + (SHOTS3[i + 1][4] / 2 if i + 1 < len(SHOTS3) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTS3) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
