"""Part 2 (Arabic, 63.3 s): San Jose mine, the men and their families, Luis / Mario / Mario / Jimmy, the collapse.
Same STYLE LOCK as part 1: oil-painted layered puppets, face mark on every character, no captions."""
import cv2, math, numpy as np
import hook_scenes as HS
from hook_scenes import *
for _k in 'usgj': HS.RIG[_k] = HS.RIG['m']

D2 = 63.3


def speak(T, ph=0.0, amt=1.0):
    syl = abs(math.sin(2 * math.pi * 3.2 * T + ph + 0.8 * math.sin(T * 1.3))) ** 0.8
    return amt * clamp(0.2 + 0.9 * syl) * (0.7 + 0.3 * math.sin(T * 7.0 + ph))


def draw_items(cv, cam, items, T):
    heads = []
    for it in sorted(items, key=lambda a: a['gy']):
        Xc, Yc = cam.pt(it['x'], it['gy'] - it.get('hop', 0))
        HM = draw_char(cv, it['ch'], T, Xc, Yc, it['sc'] * cam.sc, walk=it.get('walk', 0.0), ph0=it.get('ph0', 0.0), pose=it.get('pose'), mouth=it.get('mouth', 0.0), flip=it.get('flip', 1),
                       gain=it.get('gain', 1.0), tint=it.get('tint'), crouch=it.get('crouch', 0.0), shirt=it.get('shirt'), pants=it.get('pants'), hs=it.get('hs', 1.0))
        heads.append((it, HM))
    return heads


def head_pt(it, HM):
    ch = it['ch']; ox, oy = OFFS[ch]['head']; rg_ = RIG[ch]['ring']; return pt_(HM, rg_[0] - ox, rg_[1] - oy)


def mk(ch, x, gy, sc, flip=1, ph0=0.0, **kw):
    d = dict(ch=ch, x=x, gy=gy, sc=sc, flip=flip, ph0=ph0); d.update(kw); return d


# ---------------------------------------------------------------- 1. the mine in the desert (0 - 5.7)
W2 = [dict(ch='m', xe=470, ge=650, t0=0.5, dur=3.8, flip=1, ph0=0.2, gain=1.0), dict(ch='m', xe=720, ge=690, t0=1.3, dur=3.8, flip=-1, ph0=1.7, gain=.96), dict(ch='m', xe=950, ge=640, t0=2.1, dur=3.6, flip=1, ph0=3.0, gain=1.04)]
PALE = (0.98, 1.0, 1.0)


def shot_mine(cv, T):
    k = seg(T, 0, 5.9); cam = Cam(A=(700, 520), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.26, k), sc=lerp(1.0, 1.15, k), d=(-6 * k, 0), dw=(-12 * k, 0))
    plate(cv, 'h2_mine', cam, 'b'); plate(cv, 'h2_mine_gr', cam, 'w')
    cv[:] = heat_haze(cv, T, 2.4, 0.045, 2.8, 250, 570)
    items = []
    for i, c in enumerate(W2):
        X, gy, sc, walk, on = walker(T, c, (820, 385), 370, 0.0016)
        if not on: continue
        wipe = pulse(T, 3.2 + 0.5 * i, 4.2 + 0.5 * i)
        items.append(mk('m', X, gy, sc, c['flip'], c['ph0'], walk=walk, gain=c['gain'], crouch=0.08 * sstep(seg(T, 1, 2)), pose={'aL': 112 * wipe, 'fL': 135 * wipe, 'head': 5 - 8 * wipe}, shirt=SHIRTS[(i * 3 + 1) % 10]))
    draw_items(cv, cam, items, T)
    puffs(cv, T, 0, 6.0, 22, (0, 330, 1280, 260), (190, 215, 235), seed=41, size=(140, 300), rise=(0, 12), spread=(80, 200), life=4.0, alpha=0.30, wind=(70, 0))
    lb = LightBuf(); lb.glow(130, 60, 420, (190, 225, 255), 0.55); lb.glow(130, 60, 140, (230, 245, 255), 0.35); lb.apply(cv, blur=44)
    motes(cv, T, 51, 40, 1.6, (215, 235, 255))
    vignette(cv, 0.22, 2.0)


# ---------------------------------------------------------------- 2. inside the mine: cramped, dangerous, old collapse, injuries (5.7 - 16.4)
TA = [mk('m', 400, 650, .36, 1, 0.3, shirt=SHIRTS[1], pants=PANTS[1]), mk('m', 580, 570, .23, -1, 1.2, shirt=SHIRTS[3], pants=PANTS[2]),
      mk('m', 790, 612, .30, 1, 2.1, shirt=SHIRTS[6], pants=PANTS[5]), mk('m', 970, 690, .40, -1, 3.3, shirt=SHIRTS[4], pants=PANTS[7])]
_r = rng(77)
PEB = [dict(t0=9.9 + _r.random() * 1.2, x=240 + _r.random() * 800, yf=520 + _r.random() * 180, sc=0.045 + 0.05 * _r.random(), spr=int(_r.integers(0, 8)), rot=_r.random() * 360, spin=(_r.random() - .5) * 600) for _ in range(9)]


def draw_rock_list(cv, T, lst, front):
    for e in lst:
        dt = T - e['t0']
        if dt < 0: continue
        g = 1500.0; tf = math.sqrt(2 * (e['yf'] + 120) / g)
        if dt < tf: y = -120 + 0.5 * g * dt * dt; landed = False; rot = e['rot'] + e['spin'] * dt
        else: bt = dt - tf; y = e['yf'] - 10 * abs(math.sin(bt * 9)) * math.exp(-bt * 5); landed = True; rot = e['rot'] + e['spin'] * tf
        if landed == front: continue
        lyr = L(f"rock_{e['spr']}"); place(cv, lyr, M3(e['x'], y, e['sc'], e['sc'], rot, lyr.w / 2, lyr.h / 2), gain=0.82)


def tunnel_bg(cv, T, cam, after, bright=1.0, lamp_ang=0.0):
    base, wl, wr = ('h_p3', 'h_p3_wl', 'h_p3_wr') if after else ('h_p2', 'h_p2_wl', 'h_p2_wr')
    plate(cv, base, cam, 'b', gain=bright)
    if after: bq = draw_lamp(cv, cam, 'h_p3_lamp', (488, 66, 578, 266), (530, 74), (531, 210), lamp_ang, T)
    else: bq = draw_lamp(cv, cam, 'h_p2_lamp', (668, 120, 744, 214), (706, 125), (706, 172), lamp_ang, T)
    plate(cv, wl, cam, 'w', gain=bright); plate(cv, wr, cam, 'w', gain=bright)
    return bq


def lamp_light(cv, cam, bq, after, fl):
    lb = LightBuf(); lb.glow(bq[0], bq[1], 50, (110, 190, 255), 0.75 * fl); lb.glow(bq[0], bq[1], 300, (60, 130, 230), 0.38 * fl)
    if not after:
        for (px, py, r_) in ((706, 286, 22), (702, 322, 14)):
            q = cam.pt(S0 * px - OX, S0 * py - OY); lb.glow(q[0], q[1], r_, (110, 190, 255), 0.5)
    lb.apply(cv, blur=26)


def shot_tun_a(cv, T):
    after = T >= 11.14
    k = seg(T, 5.7, 16.6); A = 0.0
    if 9.9 <= T < 11.3: A = 2.5 * math.sin(math.pi * seg(T, 9.9, 11.3))
    if T >= 11.14: A += 5.0 * math.exp(-3.0 * (T - 11.14))
    dxy = shake_xy(T, A)
    cam = Cam(A=(700, 390), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.28, k), sc=lerp(1.0, 1.15, k), d=dxy, dw=(dxy[0] * 1.5, dxy[1] * 1.5))
    bq = tunnel_bg(cv, T, cam, after, 1.0, 3.0 * math.sin(T * 1.6) + A * 1.2 * math.sin(T * 5.5))
    draw_rock_list(cv, T, PEB, False)
    items = []
    for i, c in enumerate(TA):
        P = {}; crouch = 0.0
        cough = pulse(T, 6.2, 7.0) + pulse(T, 8.0, 8.6)
        if i == 0: P['aL'] = 20 * cough; P['fL'] = 128 * cough; P['head'] = -8 * cough; crouch = 0.15 * cough
        if i == 1: e = pulse(T, 6.6, 7.9); P['aR'] = 115 * e; P['fR'] = 135 * e; P['head'] = 6 * e
        if i == 2: sw_ = math.sin(2 * math.pi * 1.3 * T); P['aL'] = 34 + 36 * sw_; P['fL'] = 22 + 28 * math.sin(2 * math.pi * 1.3 * T + 1) if T < 9.0 else 6; P['aR'] = 30 + 30 * math.sin(2 * math.pi * 1.3 * T + 2.0) if T < 9.0 else 6
        if i == 3: crouch = 0.12; P['head'] = 6
        lk = sstep(seg(T, 9.05, 9.6)) * (1 - sstep(seg(T, 11.2, 11.6)))
        P['head'] = P.get('head', 0) - 13 * lk + 2.5 * math.sin(T * 5 + i) * lk; P['aL'] = P.get('aL', 0) + 14 * lk; P['aR'] = P.get('aR', 0) + 14 * lk
        if T >= 11.4:
            lo = sstep(seg(T, 11.4, 12.0)); P['head'] = P.get('head', 0) + 6 * math.sin(T * 1.3 + i) * lo + (i % 2) * 8 * lo
            if i == 1: P['aR'] = P.get('aR', 0) + 78 * sstep(seg(T, 12.0, 12.6)) * (1 - sstep(seg(T, 13.3, 13.8))); P['fR'] = -12
        inj = sstep(seg(T, 13.44, 13.9)) * (1 - sstep(seg(T, 15.2, 15.8)))
        if i == 3: crouch += 0.30 * inj; P['head'] = P.get('head', 0) + 14 * inj; P['aL'] = P.get('aL', 0) + 18 * inj; P['fL'] = P.get('fL', 0) - 72 * inj; P['aR'] = P.get('aR', 0) + 8 * inj; P['fR'] = P.get('fR', 0) - 30 * inj
        if i == 0: P['aR'] = P.get('aR', 0) + 28 * inj; P['fR'] = P.get('fR', 0) - 55 * inj
        sh = sstep(seg(T, 14.9, 15.4)) * (1 - sstep(seg(T, 16.0, 16.6)))
        P['aL'] = P.get('aL', 0) + 30 * sh; P['aR'] = P.get('aR', 0) + 30 * sh; P['fL'] = P.get('fL', 0) + 24 * sh; P['fR'] = P.get('fR', 0) + 24 * sh; P['head'] = P.get('head', 0) + 7 * math.sin(T * 2 + i) * sh
        items.append(dict(c, pose=P, crouch=crouch, gain=0.9, tint=(0.92, 1.0, 1.08)))
    draw_items(cv, cam, items, T)
    draw_rock_list(cv, T, PEB, True)
    lamp_light(cv, cam, bq, after, 0.9 + 0.1 * math.sin(T * 9) * math.sin(T * 2.3))
    puffs(cv, T, 5.7, 9.0, 12, (150, 120, 980, 420), (95, 135, 178), seed=61, size=(120, 260), rise=(-6, 10), life=3.2, alpha=0.20)
    puffs(cv, T, 10.1, 12.2, 16, (200, 0, 880, 220), (100, 142, 184), seed=62, size=(100, 240), rise=(-30, -8), life=2.6, alpha=0.32)
    motes(cv, T, 9, 32)
    veil(cv, T, 0.18 + 0.10 * sstep(seg(T, 5.7, 8)) + 0.55 * pulse(T, 10.85, 11.6))


# ---------------------------------------------------------------- 4. families, home, kids, town (19.17 - 24.5)
def kid(ch, x, gy, sc, flip=1, ph0=0.0, T=0.0, hop=0.0, **kw): return mk(ch, x, gy, sc, flip, ph0, hs=1.4, hop=hop, **kw)


def shot_home(cv, T):
    k = seg(T, 19.1, 21.4); cam = Cam(A=(640, 600), sb=lerp(1.0, 1.12, k), sw=lerp(1.0, 1.12, k), sc=lerp(1.0, 1.12, k), d=(-6 * k, 0), dw=(-6 * k, 0))
    plate(cv, 'h2_home', cam, 'b')
    hug = sstep(seg(T, 19.5, 20.5))
    P_f = {'aL': 22 * hug, 'aR': 28 * hug, 'fL': 10 * hug, 'fR': -30 * hug, 'head': 4 * math.sin(T * 1.4)}
    P_m = {'aL': 30 * hug, 'aR': 20 * hug, 'fL': -28 * hug, 'fR': 12 * hug, 'head': -4 * math.sin(T * 1.2 + 1)}
    items = [mk('ar', 470, 705, .46, 1, 0.2, pose=P_f), mk('w', 830, 705, .44, -1, 1.6, pose=P_m),
             kid('w', 640, 712, .27, 1, 2.2, hop=10 * abs(math.sin(2 * math.pi * 1.7 * T)) * hug, pose={'aL': 40 * hug, 'aR': 40 * hug}),
             kid('ar', 330, 716, .25, -1, 3.1, hop=8 * abs(math.sin(2 * math.pi * 1.5 * T + 1)) * hug, pose={'aL': 35 * hug, 'aR': 45 * hug})]
    draw_items(cv, cam, items, T)
    lb = LightBuf(); fl = 0.9 + 0.1 * math.sin(T * 8) * math.sin(T * 2.1); q = cam.pt(S0 * 868 - OX, S0 * 170 - OY); c2 = cam.pt(S0 * 868 - OX, S0 * 540 - OY)
    lb.glow(q[0], q[1], 240, (70, 150, 255), 0.45); lb.glow(c2[0], c2[1], 40, (110, 190, 255), 0.5 * fl); lb.glow(c2[0], c2[1], 220, (50, 120, 230), 0.3 * fl); lb.apply(cv, blur=26)
    motes(cv, T, 71, 26, 0.5, (210, 230, 255)); vignette(cv, 0.3, 2.0)


def shot_house(cv, T):
    k = seg(T, 21.2, 22.4); cam = Cam(A=(640, 600), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.20, k), sc=lerp(1.0, 1.12, k), d=(0, 0), dw=(0, 0))
    plate(cv, 'h2_house', cam, 'b'); plate(cv, 'h2_house_gr', cam, 'w')
    wave = 70 + 28 * math.sin(2 * math.pi * 2.0 * T)
    items = [mk('w', 760, 700, .40, 1, 0.4, pose={'aR': wave, 'fR': 40 + 20 * math.sin(2 * math.pi * 2.0 * T + 1), 'head': 4 * math.sin(T * 2)}),
             kid('ar', 560, 712, .24, -1, 1.3, hop=9 * abs(math.sin(2 * math.pi * 1.8 * T)), pose={'aL': 60, 'aR': 60})]
    draw_items(cv, cam, items, T)
    lb = LightBuf(); lb.glow(300, 120, 380, (70, 150, 255), 0.4); lb.apply(cv, blur=30); motes(cv, T, 72, 24, 0.8); vignette(cv, 0.25, 2.0)


def shot_kids(cv, T):
    k = seg(T, 22.1, 23.2); cam = Cam(A=(400, 620), sb=lerp(1.12, 1.22, k), sw=lerp(1.3, 1.4, k), sc=lerp(1.2, 1.3, k), d=(0, 0), dw=(0, 0))
    plate(cv, 'h2_street', cam, 'b'); plate(cv, 'h2_street_gr', cam, 'w')
    items = []
    for i, (ch, x, gy, sc, fl_) in enumerate((('w', 430, 690, .30, 1), ('ar', 690, 700, .28, -1), ('w', 930, 690, .26, 1))):
        hp = 22 * abs(math.sin(2 * math.pi * 1.9 * T + i * 1.3))
        items.append(kid(ch, x, gy, sc, fl_, i * 1.7, hop=hp, pose={'aL': 125 + 25 * math.sin(T * 9 + i), 'aR': 125 + 25 * math.sin(T * 9 + i + 2), 'fL': 20, 'fR': 20}))
    draw_items(cv, cam, items, T); motes(cv, T, 73, 26, 1.0); vignette(cv, 0.25, 2.0)


TOWN = [('ar', 350, 600, .15), ('w', 470, 612, .17), ('ar', 600, 606, .15), ('w', 900, 610, .16), ('ar', 1010, 604, .15), ('w', 1130, 612, .17),
        ('ar', 250, 650, .22), ('w', 760, 655, .24), ('ar', 1060, 660, .23), ('w', 520, 668, .24), ('w', 150, 662, .22)]


def shot_town(cv, T):
    k = seg(T, 22.9, 24.7); cam = Cam(A=(640, 520), sb=lerp(1.14, 1.0, k), sw=lerp(1.2, 1.0, k), sc=lerp(1.14, 1.0, k), d=(0, 0), dw=(0, 0))
    plate(cv, 'h2_street', cam, 'b'); plate(cv, 'h2_street_gr', cam, 'w')
    items = []
    for i, (ch, x, gy, sc) in enumerate(TOWN):
        items.append(mk(ch, x, gy, sc, 1 if i % 2 else -1, i * 0.9, pose={'aR': 60 + 30 * math.sin(2 * math.pi * 1.2 * T + i), 'fR': 30, 'head': 3 * math.sin(T + i)} if i % 3 == 0 else {'head': 3 * math.sin(T * 1.1 + i)}))
    for j, (x, gy, sc) in enumerate(((330, 700, .20), (880, 702, .19), (680, 690, .17))):
        items.append(kid('w' if j % 2 else 'ar', x, gy, sc, 1, j * 1.1 + 5, hop=14 * abs(math.sin(2 * math.pi * 1.8 * T + j)), pose={'aL': 112, 'aR': 112}))
    draw_items(cv, cam, items, T); motes(cv, T, 74, 30, 1.0); vignette(cv, 0.25, 2.0)


# ---------------------------------------------------------------- 5. the four men
def portrait(cv, T, t0, t1, plate_name, fg, cam_kw, main, bg, extra=None):
    k = seg(T, t0, t1); cam = Cam(**cam_kw(k))
    return cam, k


def shot_luis(cv, T):
    k = seg(T, 24.4, 28.1); cam = Cam(A=(640, 600), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.24, k), sc=lerp(1.0, 1.14, k), d=(-10 * k, 0), dw=(-18 * k, 0))
    plate(cv, 'h2_mine', cam, 'b'); plate(cv, 'h2_mine_gr', cam, 'w'); cv[:] = heat_haze(cv, T, 1.6, 0.05, 2.4, 250, 560)
    ptv = pulse(T, 25.2, 26.4)
    P = {'aR': 75 * ptv + 12 * math.sin(T * 1.6), 'fR': -10 * ptv, 'head': 3 * math.sin(T * 1.2) - 5 * ptv, 'aL': 10 + 22 * pulse(T, 26.6, 27.6), 'fL': -20 * pulse(T, 26.6, 27.6)}
    items = [mk('u', 560, 706, .62, 1, 0.4, pose=P, mouth=speak(T, 0.5, 0.35) if 24.6 < T < 27.4 else 0.0),
             mk('m', 800, 596, .19, -1, 1.1, shirt=SHIRTS[1], pants=PANTS[2], pose={'head': 4 * math.sin(T * 1.7)}), mk('m', 905, 602, .19, 1, 2.0, shirt=SHIRTS[4], pose={'head': 3 * math.sin(T * 1.3 + 1)}),
             mk('m', 1010, 598, .19, -1, 3.2, shirt=SHIRTS[3], pants=PANTS[1], pose={'head': 3 * math.sin(T * 1.5 + 2)}), mk('m', 1130, 612, .22, 1, 4.1, shirt=SHIRTS[6], pose={'head': 2 * math.sin(T)})]
    draw_items(cv, cam, items, T)
    lb = LightBuf(); lb.glow(130, 60, 420, (190, 225, 255), 0.45); lb.apply(cv, blur=44); motes(cv, T, 52, 30, 1.2, (215, 235, 255)); vignette(cv, 0.25, 2.0)


def shot_sep(cv, T):
    k = seg(T, 27.8, 33.3); A = 0.0
    cam = Cam(A=(700, 480), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.26, k), sc=lerp(1.0, 1.14, k), d=(0, 0), dw=(0, 0))
    bq = tunnel_bg(cv, T, cam, False, 1.0, 3.0 * math.sin(T * 1.6))
    lau = 0.5 + 0.5 * math.sin(2 * math.pi * 2.4 * T)
    big = 0.5 + 0.5 * math.sin(2 * math.pi * 0.8 * T)
    P = {'aL': 30 + 55 * big, 'aR': 30 + 55 * (1 - big), 'fL': 10 + 40 * (1 - big), 'fR': 10 + 40 * big, 'head': 5 * math.sin(2 * math.pi * 1.5 * T)}
    items = [mk('s', 640, 712, .62, 1, 0.3, pose=P, mouth=speak(T, 0.2, 0.9) if 28.0 < T < 32.9 else 0.0)]
    lt = sstep(seg(T, 29.4, 30.0))
    for i, (x, gy, sc, fl_) in enumerate(((330, 650, .32, 1), (980, 646, .32, -1), (1120, 700, .38, 1))):
        items.append(mk('m', x, gy, sc, fl_, 1.0 + i * 1.7, shirt=SHIRTS[(i * 3 + 1) % 10], pants=PANTS[(i * 2 + 1) % 10], crouch=0.12 * lt * lau, gain=0.92, tint=(0.92, 1.0, 1.08),
                        pose={'head': -10 * lt * lau + 3 * math.sin(T + i), 'aL': 10 * lt, 'aR': 10 * lt}))
    for it in items: it.setdefault('gain', 0.92); it.setdefault('tint', (0.92, 1.0, 1.08))
    draw_items(cv, cam, items, T); lamp_light(cv, cam, bq, False, 0.9 + 0.1 * math.sin(T * 9)); motes(cv, T, 9, 26); veil(cv, T, 0.10)


def shot_gom(cv, T):
    k = seg(T, 33.0, 38.2); cam = Cam(A=(560, 470), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.28, k), sc=lerp(1.0, 1.14, k), d=(-8 * k, 0), dw=(-14 * k, -6 * k))
    plate(cv, 'h_p1', cam, 'b'); plate(cv, 'h_p1_gr', cam, 'w'); cv[:] = heat_haze(cv, T, 1.2, 0.05, 2.5, 380, 560)
    cough = pulse(T, 34.0, 34.9) + pulse(T, 36.6, 37.4)
    P = {'aR': 8 + 6 * math.sin(T * 0.8), 'fR': -40, 'aL': 18 * cough, 'fL': 120 * cough, 'head': 4 * math.sin(T * 0.9) + 8 * cough, 'lean': 1.6 * math.sin(T * 0.7)}
    items = [mk('g', 700, 706, .60, 1, 0.1, pose=P, crouch=0.10 + 0.08 * cough, mouth=speak(T, 0.0, 0.0)),
             mk('m', 400, 650, .30, 1, 1.4, shirt=SHIRTS[1], pants=PANTS[1], pose={'head': 4 * math.sin(T * 1.1)}),
             mk('m', 1000, 640, .30, -1, 2.4, shirt=SHIRTS[4], pants=PANTS[5], pose={'head': 4 * math.sin(T * 1.2 + 2), 'aL': 20 * pulse(T, 34.3, 35.3)})]
    draw_items(cv, cam, items, T)
    lb = LightBuf(); lb.glow(120, 90, 330, (90, 160, 255), 0.5); lb.glow(560, 300, 380, (60, 120, 220), 0.25); lb.apply(cv, blur=40); motes(cv, T, 7, 40, 1.4); vignette(cv, 0.22, 2.0)


def shot_jim(cv, T):
    k = seg(T, 38.0, 44.0); cam = Cam(A=(840, 620), sb=lerp(1.15, 1.24, k), sw=lerp(1.2, 1.32, k), sc=lerp(1.1, 1.18, k), d=(0, 0), dw=(0, 0))
    plate(cv, 'h2_street', cam, 'b'); plate(cv, 'h2_street_gr', cam, 'w')
    up = sstep(seg(T, 41.8, 42.8))
    P = {'aL': 8 + 3 * math.sin(T * 1.4) + 14 * up, 'aR': 8 + 3 * math.sin(T * 1.3) + 14 * up, 'fL': -50 * (1 - up), 'fR': -52 * (1 - up), 'head': (4 * math.sin(T * 1.6) + 6 * math.sin(T * 0.7)) * (1 - up) - 9 * up, 'lean': 1.2 * math.sin(T * 1.1)}
    items = [mk('j', 760, 706, .46, 1, 0.5, pose=P, mouth=0.0)]
    for j, (x, gy, sc) in enumerate(((330, 640, .20), (470, 650, .21), (1100, 640, .20))):
        items.append(kid('w' if j % 2 else 'ar', x, gy, sc, 1, j * 1.3 + 2, hop=10 * abs(math.sin(2 * math.pi * 1.7 * T + j)), pose={'aL': 112, 'aR': 112}))
    draw_items(cv, cam, items, T)
    lb = LightBuf(); lb.glow(700, 120, 420, (100, 180, 255), 0.35 + 0.35 * up); lb.apply(cv, blur=44); motes(cv, T, 75, 34, 1.0); vignette(cv, 0.25, 2.0)


# ---------------------------------------------------------------- 6. that day: the collapse (43.8 - 63.3)
CR2 = [mk('m', 480, 548, .17, 1, 0.5, shirt=SHIRTS[1], pants=PANTS[1]), mk('m', 570, 546, .17, -1, 1.5, shirt=SHIRTS[3], pants=PANTS[2]), mk('m', 660, 548, .17, 1, 2.5, shirt=SHIRTS[6], pants=PANTS[5]),
       mk('m', 750, 546, .17, -1, 3.5, shirt=SHIRTS[4], pants=PANTS[3]), mk('m', 840, 548, .17, 1, 4.5, shirt=SHIRTS[7], pants=PANTS[7]),
       mk('u', 360, 690, .36, 1, 0.2), mk('s', 540, 694, .36, -1, 1.1), mk('g', 720, 690, .36, 1, 2.0), mk('j', 900, 694, .36, -1, 3.0)]


def rock_events2():
    r = rng(23); ev = []
    for i in range(64):
        t0 = 47.1 + (r.random() ** 1.15) * 4.7; x = 60 + r.random() * (W - 120); yf = 500 + r.random() * 230
        sc = (0.10 + 0.26 * (yf - 500) / 230) * (0.7 + 0.7 * r.random()); ev.append(dict(t0=t0, x=x, yf=yf, sc=sc, spr=int(r.integers(0, 8)), rot=r.random() * 360, spin=(r.random() - .5) * 700))
    return ev


ROCKS2 = rock_events2()


def quake2(T):
    A = 0.0
    if T < 47.0: A = 1.4 * sstep(seg(T, 45.9, 46.8))
    for t0, a, kk in ((47.0, 13.0, 0.9), (47.9, 18.0, 0.42), (49.35, 8.0, 0.9)):
        if T >= t0: A += a * math.exp(-kk * (T - t0))
    if T >= 47.0: A += 2.2 * (1 - sstep(seg(T, 53.5, 58.0)))
    return A


def shot_tun_b(cv, T):
    after = T >= 52.4
    A = quake2(T); dxy = shake_xy(T, A)
    push = 0.10 * sstep(seg(T, 43.8, 47)) + 0.04 * sstep(seg(T, 52.5, 58)); p2 = sstep(seg(T, 58.6, 63.0))
    cam = Cam(A=(700, 330), sb=1.0 + push * 0.8 + p2 * 0.10, sw=1.0 + push * 2.0 + p2 * 0.22, sc=1.0 + push * 1.3 + p2 * 0.38, d=dxy, dw=(dxy[0] * 1.5, dxy[1] * 1.5))
    bright = 0.82 + 0.18 * flick(T, 3.0) if 47.0 <= T < 53.0 else 1.0
    bq = tunnel_bg(cv, T, cam, after, bright, 3.0 * math.sin(T * 1.6) + A * 1.6 * math.sin(T * 5.5))
    draw_rock_list(cv, T, ROCKS2, False)
    items = []
    for i, c in enumerate(CR2):
        d = 0.04 * ((i * 7) % 5); P = {}; crouch = 0.0; X = c['x']
        work = (1 - sstep(seg(T, 45.2, 45.8))) * sstep(seg(T, 44.0, 44.6))
        if work > 0 and i % 2 == 0: P['aL'] = work * (30 + 34 * math.sin(2 * math.pi * 1.2 * T + i)); P['fL'] = work * (22 + 22 * math.sin(2 * math.pi * 1.2 * T + i + 1))
        if work > 0 and i % 2 == 1: P['aR'] = work * (25 + 28 * math.sin(2 * math.pi * 1.0 * T + i)); P['fR'] = work * (10 + 18 * math.sin(2 * math.pi * 1.0 * T + i))
        al = sstep(seg(T, 45.4, 46.3 + d)) * (1 - sstep(seg(T, 47.0 + d, 47.3 + d)))
        P['head'] = P.get('head', 0) - 10 * al + 2 * math.sin(T * 4 + i) * al; P['aL'] = P.get('aL', 0) + 12 * al; P['aR'] = P.get('aR', 0) + 12 * al
        ec = sstep(seg(T, 47.0 + d, 47.35 + d)) * (1 - sstep(seg(T, 53.0 + d, 53.8 + d)))
        P['aL'] = P.get('aL', 0) + 120 * ec; P['aR'] = P.get('aR', 0) + 120 * ec; P['fL'] = P.get('fL', 0) + 110 * ec; P['fR'] = P.get('fR', 0) + 110 * ec; crouch += 0.55 * ec; P['head'] = P.get('head', 0) + 10 * ec
        eg = sstep(seg(T, 53.4, 54.2)) * (1 - sstep(seg(T, 56.8, 57.4)))
        P['aL'] = P.get('aL', 0) + 36 * eg; P['aR'] = P.get('aR', 0) + 36 * eg; P['fL'] = P.get('fL', 0) + 30 * eg; P['fR'] = P.get('fR', 0) + 30 * eg
        P['head'] = P.get('head', 0) + 14 * math.sin(2 * math.pi * 0.9 * T + i * 1.7) * eg; crouch += 0.18 * eg
        X += 28 * math.sin(0.7 * T + i * 2.1) * eg
        fz = sstep(seg(T, 57.4, 58.4)); P['head'] = P.get('head', 0) - 4 * fz + 3 * math.sin(T * 1.1 + i) * fz
        if T > 61.4: dn = sstep(seg(T, 61.4, 62.3)); P['head'] = P.get('head', 0) - 10 * dn; crouch += 0.06 * dn
        items.append(dict(c, x=X, pose=P, crouch=crouch, gain=0.9, tint=(0.92, 1.0, 1.08)))
    heads = draw_items(cv, cam, items, T)
    draw_rock_list(cv, T, ROCKS2, True)
    lamp_light(cv, cam, bq, after, (0.9 + 0.1 * math.sin(T * 9) * math.sin(T * 2.3)) * (0.75 + 0.25 * flick(T, 1.0) if 47.0 < T < 53.0 else 1.0))
    puffs(cv, T, 46.3, 47.6, 12, (200, 0, 880, 160), (95, 135, 178), seed=81, size=(80, 200), rise=(-40, -10), life=2.6, alpha=0.35)
    puffs(cv, T, 47.9, 52.4, 40, (150, 520, 980, 200), (100, 142, 184), seed=82, size=(120, 300), rise=(10, 70), life=3.0, alpha=0.5)
    motes(cv, T, 9, 30)
    vl = float(np.interp(T, [43.8, 45.9, 46.3, 47.0, 47.4, 49.3, 51.2, 52.3, 53.4, 57.3, 59.0, 61.0], [0.0, 0.04, 0.10, 0.28, 0.20, 0.28, 0.50, 0.93, 0.55, 0.50, 0.12, 0.04]))
    veil(cv, T, vl)
    cv *= float(np.interp(T, [52.6, 54.2, 56.8, 58.8], [1.0, 0.30, 0.30, 1.0]))
    bm = sstep(seg(T, 53.3, 54.0)) * (1 - sstep(seg(T, 57.0, 57.8)))
    if bm > 0.01:   # headlamp beams groping through the dust
        lb = LightBuf()
        for i, (it, HM) in enumerate(heads):
            hx, hy = head_pt(it, HM); ang = (0 if i % 2 else 180) + 38 * math.sin(1.3 * T + i * 1.9) + (12 if i % 3 == 0 else -6)
            lb.glow(hx, hy - 6, 14, (170, 225, 255), 0.6 * bm)
            lb.beam(hx, hy, ang, 120 + 700 * it['sc'] * cam.sc, 6, (190, 235, 255), 1.5 * bm)
        lb.apply(cv, blur=8, gain=1.0)


# (name, t0, t1, fn, crossfade seconds)
SHOTS2 = [('mine', 0.0, 5.72, shot_mine, 0.0), ('tun_a', 5.72, 16.40, shot_tun_a, 0.5), ('dep', 16.40, 19.17, lambda cv, T: shot_depth(cv, T, 16.35, 19.0), 0.5),
          ('home', 19.17, 21.30, shot_home, 0.4), ('house', 21.30, 22.20, shot_house, 0.25), ('kids', 22.20, 23.00, shot_kids, 0.25), ('town', 23.00, 24.50, shot_town, 0.3),
          ('luis', 24.50, 27.95, shot_luis, 0.5), ('sep', 27.95, 33.10, shot_sep, 0.5), ('gom', 33.10, 38.10, shot_gom, 0.5), ('jim', 38.10, 43.85, shot_jim, 0.5), ('tun_b', 43.85, D2, shot_tun_b, 0.6)]


class Part2:
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
