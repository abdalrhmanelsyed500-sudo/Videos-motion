"""V8 'KEYFRAME METHOD' test (~15.8 s): same story beat ('Mauro realises he is lost'), but every pose is a high-res painted keyframe of the SAME reference-locked character
(kf_rig.py: optical-flow in-betweens), keyed into the plate with fx.hero_fx (cast shadow, rim light, colour match, haze).  Shots: wide approach walk -> medium stop/idle/shade eyes -> painted close-up worried -> SHOCK."""
from up3_scenes import *
import kf_rig as K

DPX = 15.8
HSRC = 818.0                  # painted figure height in source px
ZERO = np.zeros(3)


def ev(t, a, b): return sstep((t - a) / (b - a))


def hero_kf(cv, T, arr, X, gy, hpl, wc, flip=1, sy=1.0, rot=0.0, sun_h=0.18, rim=0.8, sl=1.2, haze=0.0, grade=1.0, shadow_a=0.9):
    k = hpl * wc.s / HSRC
    FX.hero_fx(cv, lambda c: K.draw_kf(c, arr, X, gy, k, flip, rot, sy), gy, sun=SUNX, sun_h=sun_h, rim=rim, shadow_len=sl, haze=haze, grade=grade, shadow_a=shadow_a)


def walk_ph(t, rate=1 / 1.9): return t * rate


# 1. wide approach (0 - 5.0): he walks towards camera-left along the dune, growing in frame
def m1(cv, T):
    t = T
    wc = cam(T, 0, 5.2, (930, 250, 1.12), (860, 285, 1.22), 'pr_dawn', cv=cv)
    cv[:] = heat_haze(cv, T, 1.2, 0.05, 2.4, 300, 470)
    s = seg(T, 0, 5.0); u = ease_out(s) * 0.3 + s * 0.7
    X = lerp(820, 520, u); gy0 = lerp(505, 640, u); hs = lerp(150, 400, u)
    ph = walk_ph(t); bob = abs(math.sin(math.pi * ph * 2)) ** 1.5
    props(cv, T, 520, 0.2, 0.3, a=0.7, blur=1.2)
    hero_kf(cv, T, K.walk_pose(ph), X, gy0 - 0.012 * hs * bob, hs / wc.s, wc, haze=lerp(0.24, 0.05, u), sl=1.4)
    puffs(cv, T, 0.4, 5.2, 14, (X - 70, gy0 - 8, 120, 10), (128, 178, 215), seed=11, size=(14, 36), rise=(4, 14), spread=(20, 60), grow=1.8, life=1.2, alpha=0.26, wind=(-200, 0))
    fgl(cv, 'up_fg_dune.png', 640 - (wc.px - 880) * 1.4, 905 + 160 * ease_out(seg(T, 0.8, 4.2)), 1.3, blur=3, gain=0.8)
    leak(cv, *wc.pt(585, 262), 380, T, 0.35, (120, 195, 255)); fin(cv, T, 3101, 0.45); shake(cv, T, 0.7, 1)


# 2. medium (5.0 - 10.2): last steps, stops, tired idle, raises the hand to shade his eyes
def m2(cv, T):
    t = T - 5.0
    wc = cam(T, 5.0, 10.4, (770, 330, 1.38), (790, 322, 1.56), 'pr_dawn', cv=cv); blur_bg(cv, 3.0)
    cv[:] = heat_haze(cv, T, 1.4, 0.05, 2.4, 330, 520)
    p0 = walk_ph(5.0); pe = 3.25                  # continue the cycle from the end of shot 1, stop on a passing pose
    ph = lerp(p0, pe, ease_out(seg(t, 0, 2.3)))
    if t < 2.3: arr = K.walk_pose(ph)
    elif t < 2.9: arr = K.morph('walk_P', 'idle', ev(t, 2.3, 2.9))
    elif t < 4.1: arr = K.img('idle')
    elif t < 5.0: arr = K.morph('idle', 'look', ev(t, 4.1, 4.9))
    else: arr = K.img('look')
    breath = 1.0 + 0.0035 * math.sin(t * 2.0 * math.pi / 3.2) if t > 2.6 else 1.0
    bob = abs(math.sin(math.pi * ph * 2)) ** 1.5 if t < 2.3 else 0.0
    hs = 400 + 40 * seg(t, 0, 5.4); X = lerp(520, 650, ease_out(seg(t, 0, 2.3))); Y = 640 + 8 * seg(t, 0, 5.4) - 0.012 * hs * bob
    hero_kf(cv, T, arr, X, Y, hs / wc.s, wc, sy=breath, sun_h=0.18, haze=0.05)
    puffs(cv, T, 5.0, 7.4, 14, (X - 90, Y - 10, 160, 12), (128, 178, 215), seed=5, size=(20, 50), rise=(6, 22), spread=(30, 90), grow=1.9, life=1.3, alpha=0.30, wind=(-300, 0))
    leak(cv, *wc.pt(585, 262), 420, T, 0.4, (120, 195, 255)); fin(cv, T, 3102, 0.45); shake(cv, T, 0.9, 2)


# 3. painted close-up (10.2 - 15.8): worried -> SHOCK
def m3(cv, T):
    t = T - 10.2; ts = 2.6                      # shock moment
    punch = ease_out(seg(t, ts, ts + 0.22)) * 0.10 + 0.05 * seg(t, ts + 0.22, 5.6) if t > ts else 0.0
    wc = cam(T, 10.2, 15.8, (700, 300, 1.6), (716, 298, 1.72), 'pr_dawn', cv=cv); blur_bg(cv, 8.0)
    arr = K.img('bust_worried') if t < ts else (K.morph('bust_worried', 'bust_shock_reg', ev(t, ts, ts + 0.16)) if t < ts + 0.16 else K.img('bust_shock_reg'))
    # alias the two busts into one register: they share the frame, so no re-alignment needed
    sc = 0.9 * (1 + 0.012 * seg(t, 0, ts) + punch + 0.006 * math.sin(t * 1.9)) ; rot = 0.5 * math.sin(t * 0.9) - (1.2 * math.exp(-(t - ts) * 9) if t > ts else 0)
    ox = -14 * seg(t, 0, ts) + (6 * math.exp(-(t - ts) * 7) * math.sin((t - ts) * 40) if t > ts else 0)
    X, Y = 690 + ox, 262 + (2 * math.sin(t * 2.0 * math.pi / 3.4))
    FX.hero_fx(cv, lambda c: K.draw_kf(c, arr, X, Y, sc, 1, rot, 1.0, ax=601.0, ay=270.0), 9999, sun=SUNX, sun_h=0.3, rim=0.55, shadow_a=0.0, grade=0.35, haze=0.0)
    if t > ts: cv += 38 * math.exp(-(t - ts) * 14)
    leak(cv, *wc.pt(585, 262), 520, T, 0.5, (120, 195, 255)); fin(cv, T, 3103, 0.6, mo=40); shake(cv, T, 1.0 + (3.0 * math.exp(-(t - ts) * 5) if t > ts else 0), 3)


SHOTSX = [('m1', 0.0, 5.0, m1, 0.0), ('m2', 5.0, 10.2, m2, 0.25), ('m3', 10.2, DPX, m3, 0.25)]


class PartMX(P2.PartP2):
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTSX):
            hi = t1 + (SHOTSX[i + 1][4] / 2 if i + 1 < len(SHOTSX) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTSX) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
