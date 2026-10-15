"""V9 'RIGGED PAINTING' (~15.8 s).  Same painted, reference-locked character as v8, but now REALLY animated: the painted figure is skinned to a skeleton (skin_rig.py) -> frontal walk cycle
(bob, hip sway/roll, counter-rotating torso, lifted/foreshortened swing legs, swinging arms), breathing, tired sigh; the painted close-up is skinned too (breath, head recoil, shoulder shrug, neck-cloth follow-through).
Big pose changes that skinning cannot do (hand to the brow) use optical-flow in-betweens between two painted keyframes."""
from mx_scenes import *
import skin_rig as SK

RATE = 1 / 1.6
_sk = {}


def skin(nm, bones):
    if nm not in _sk: _sk[nm] = SK.Skin(nm, bones, s=11.0 if bones is SK.BODY else 26.0, hres=2 if bones is SK.BODY else 4)
    return _sk[nm]


def bump(x, a, b): return math.sin(math.pi * clamp((x - a) / (b - a))) ** 1.6


def spring(tau):
    """fast up, slow settle, slight undershoot"""
    if tau <= 0: return 0.0
    return (1 - math.exp(-tau / 0.045)) * math.exp(-tau / 0.8) * (1 + 0.25 * math.cos(tau * 9.0))


def add(p, b, k, v): p.setdefault(b, {}); p[b][k] = p[b].get(k, 0.0) + v if k != 'sa' else p[b].get(k, 1.0) * v


def m1(cv, T):
    t = T
    wc = cam(T, 0, 5.2, (930, 250, 1.12), (860, 285, 1.22), 'pr_dawn', cv=cv)
    cv[:] = heat_haze(cv, T, 1.2, 0.05, 2.4, 300, 470)
    s = seg(T, 0, 5.0); u = ease_out(s) * 0.3 + s * 0.7
    X = lerp(820, 520, u); gy0 = lerp(505, 640, u); hs = lerp(150, 400, u)
    arr = skin('idle', SK.BODY).render(SK.walk_pose(t * RATE))
    props(cv, T, 520, 0.2, 0.3, a=0.7, blur=1.2)
    hero_kf(cv, T, arr, X, gy0, hs / wc.s, wc, haze=lerp(0.24, 0.05, u), sl=1.4)
    puffs(cv, T, 0.4, 5.2, 14, (X - 70, gy0 - 8, 120, 10), (128, 178, 215), seed=11, size=(14, 36), rise=(4, 14), spread=(20, 60), grow=1.8, life=1.2, alpha=0.26, wind=(-200, 0))
    fgl(cv, 'up_fg_dune.png', 640 - (wc.px - 880) * 1.4, 905 + 160 * ease_out(seg(T, 0.8, 4.2)), 1.3, blur=3, gain=0.8)
    leak(cv, *wc.pt(585, 262), 380, T, 0.35, (120, 195, 255)); fin(cv, T, 3101, 0.45); shake(cv, T, 0.7, 1)


def phase2(t): return lerp(5.0 * RATE, 4.0, ease_out(seg(t, 0, 3.0)))


def m2(cv, T):
    t = T - 5.0
    wc = cam(T, 5.0, 10.4, (770, 330, 1.38), (790, 322, 1.56), 'pr_dawn', cv=cv); blur_bg(cv, 3.0)
    cv[:] = heat_haze(cv, T, 1.4, 0.05, 2.4, 330, 520)
    amp = 1.0 - sstep((t - 2.2) / 0.8) if t < 3.0 else 0.0
    pose = SK.walk_pose(phase2(t), amp=max(amp, 0.0)) if amp > 0 else {}
    sk = skin('idle', SK.BODY)
    if t < 4.25:
        if t > 2.9:                                     # breathing + a tired sigh, then everything returns EXACTLY to the rest pose for the keyframe hand-off
            ex = 1.0 - sstep((t - 4.0) / 0.25)
            br = 0.006 * math.sin((t - 2.9) * 2 * math.pi / 3.4) * ex
            sg = bump(t, 3.1, 4.1) * ex
            add(pose, 'torso', 'sa', 1 + br + 0.0); add(pose, 'pelvis', 'ty', 5.5 * sg); add(pose, 'torso', 'rot', 1.2 * sg)
            add(pose, 'head', 'rot', 4.5 * bump(t, 3.2, 4.15) * ex); add(pose, 'head', 'ty', 5 * sg)
            for sd, sgn in (('L', 1), ('R', -1)): add(pose, 'arm' + sd + '_up', 'ty', 6 * sg); add(pose, 'arm' + sd + '_up', 'rot', sgn * 2.0 * sg)
        arr = sk.render(pose)
    elif t < 5.1: arr = K.morph('idle', 'look', ev(t, 4.25, 5.05))
    else: arr = K.img('look')
    hs = 400 + 40 * seg(t, 0, 5.4); X = lerp(520, 650, ease_out(seg(t, 0, 3.0))); Y = 640 + 8 * seg(t, 0, 5.4)
    hero_kf(cv, T, arr, X, Y, hs / wc.s, wc, sun_h=0.18, haze=0.05)
    puffs(cv, T, 5.0, 8.0, 14, (X - 90, Y - 10, 160, 12), (128, 178, 215), seed=5, size=(20, 50), rise=(6, 22), spread=(30, 90), grow=1.9, life=1.3, alpha=0.30, wind=(-300, 0))
    leak(cv, *wc.pt(585, 262), 420, T, 0.4, (120, 195, 255)); fin(cv, T, 3102, 0.45); shake(cv, T, 0.9, 2)


def bust_pose(t, ts):
    p = {}; tau = t - ts; br = math.sin(t * 2 * math.pi / 3.4)
    add(p, 'body', 'ty', 2.6 * br); add(p, 'body', 'sa', 1 + 0.005 * br)
    add(p, 'head', 'rot', 1.3 * math.sin(t * 0.9)); add(p, 'head', 'tx', 3 * math.sin(t * 0.7)); add(p, 'flap', 'rot', 1.8 * math.sin(t * 1.3 + 1))
    if tau > 0:
        s0 = spring(tau); s1 = spring(tau - 0.05); s2 = spring(tau - 0.13)
        add(p, 'body', 'ty', -34 * s0); add(p, 'body', 'sa', 1 + 0.03 * s0)
        add(p, 'head', 'rot', -7.5 * s1); add(p, 'head', 'sa', 1 + 0.05 * s1); add(p, 'head', 'ty', -10 * s1)
        add(p, 'flap', 'rot', 11 * s2)
    return p


def m3(cv, T):
    t = T - 10.2; ts = 2.6
    punch = ease_out(seg(t, ts, ts + 0.22)) * 0.10 + 0.05 * seg(t, ts + 0.22, 5.6) if t > ts else 0.0
    wc = cam(T, 10.2, 15.8, (700, 300, 1.6), (716, 298, 1.72), 'pr_dawn', cv=cv); blur_bg(cv, 8.0)
    pose = bust_pose(t, ts); sw = skin('bust_worried', SK.BUST)
    if t < ts: arr = sw.render(pose)
    else:
        ss = skin('bust_shock_reg', SK.BUST)
        if t < ts + 0.16: arr = K.morph_arr(sw.render(pose), ss.render(pose), ev(t, ts, ts + 0.16))
        else: arr = ss.render(pose)
    sc = 0.9 * (1 + 0.012 * seg(t, 0, ts) + punch + 0.006 * math.sin(t * 1.9)); rot = 0.5 * math.sin(t * 0.9) - (1.2 * math.exp(-(t - ts) * 9) if t > ts else 0)
    ox = -14 * seg(t, 0, ts) + (6 * math.exp(-(t - ts) * 7) * math.sin((t - ts) * 40) if t > ts else 0)
    X, Y = 690 + ox, 262 + 2 * math.sin(t * 2.0 * math.pi / 3.4)
    FX.hero_fx(cv, lambda c: K.draw_kf(c, arr, X, Y, sc, 1, rot, 1.0, ax=601.0, ay=270.0), 9999, sun=SUNX, sun_h=0.3, rim=0.55, shadow_a=0.0, grade=0.35, haze=0.0)
    if t > ts: cv += 38 * math.exp(-(t - ts) * 14)
    leak(cv, *wc.pt(585, 262), 520, T, 0.5, (120, 195, 255)); fin(cv, T, 3103, 0.6, mo=40); shake(cv, T, 1.0 + (3.0 * math.exp(-(t - ts) * 5) if t > ts else 0), 3)


SHOTSX2 = [('m1', 0.0, 5.0, m1, 0.0), ('m2', 5.0, 10.2, m2, 0.25), ('m3', 10.2, DPX, m3, 0.25)]


class PartMX2(PartMX):
    def frame(self, T, cv):
        global SHOTSX
        old = __import__('mx_scenes').SHOTSX
        try:
            __import__('mx_scenes').SHOTSX = SHOTSX2; return PartMX.frame(self, T, cv)
        finally: __import__('mx_scenes').SHOTSX = old
