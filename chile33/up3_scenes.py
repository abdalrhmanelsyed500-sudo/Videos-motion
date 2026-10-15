"""UPGRADE TEST 3 (~26 s): directed mini-sequence 'Mauro realises he is lost'. Uses: side rig (jointed, gait, side expression heads), front rig (AI front parts, round-elbow arms, expression heads, blinks),
fx.hero_fx (cast shadow + rim light from the low sun), tracking/crane/push-in cameras, depth of field, handheld shake, ground-speed props.  Sun is LEFT (pr_dawn), so rim on the left edges, shadows fall right."""
from up2_scenes import *
import front_rig as FR, fx as FX

DP3 = 26.4
SUNX = -1.0


def shake(cv, T, amp=1.2, seed=0):
    r = np.random.default_rng(seed); n = lambda f, p: math.sin(T * f + p)
    dx = amp * (n(1.7, seed) + 0.6 * n(3.9, seed + 2)); dy = amp * (n(2.3, seed + 1) + 0.5 * n(4.7, seed + 3)); rot = 0.08 * amp * n(1.1, seed)
    M = cv2.getRotationMatrix2D((640, 360), rot, 1.0); M[0, 2] += dx; M[1, 2] += dy
    cv[:] = cv2.warpAffine(cv, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def side_face(t, script):
    """script: [(t0, name), ...] -> (A, B, mix) with 0.35 s cross-fade and a blink every ~3.4 s on neutral/determined"""
    xf = 0.35; cur = script[0][1]; prev = cur; t0 = 0.0
    for ts, nm in script:
        if t >= ts: prev, cur, t0 = cur, nm, ts
    A, B, m = (cur, cur, 0.0) if cur == prev else (prev, cur, sstep(clamp((t - t0) / xf)))
    if m >= 1.0: A, B, m = B, B, 0.0
    if A == B and m == 0.0 and (t % 3.4) < 0.13: return (A, 'blink', 0.95 * math.sin(math.pi * (t % 3.4) / 0.13))
    return (A, B, m)


def hero_side(cv, T, X, gy, k, walk=1.0, face=None, sun_h=0.2, head=0.0, rim=0.6, sl=1.0):
    FX.hero_fx(cv, lambda c: SR.draw_side(c, T, X, gy, k, 1, walk=walk, shadow=False, face=face, head=head), gy, sun=SUNX, sun_h=sun_h, rim=rim, shadow_len=sl)


def hero_front(cv, T, X, gy, k, face, pose, sun_h=0.2, rim=0.6, sl=1.0, t=None):
    FX.hero_fx(cv, lambda c: FR.draw_front(c, T if t is None else t, X, gy, k, face=face, pose=pose, shadow=False), gy, sun=SUNX, sun_h=sun_h, rim=rim, shadow_len=sl)


# 1. wide establishing crane (0 - 4.4)
def s1(cv, T):
    wc = cam(T, 0, 4.6, (930, 250, 1.12), (860, 292, 1.24), 'pr_dawn', cv=cv)
    cv[:] = heat_haze(cv, T, 1.2, 0.05, 2.4, 300, 470)
    k = 0.17; gy = 520 + 6 * seg(T, 0, 4.6)
    props(cv, T, gy, k * 1.6, 0.55, a=0.85, blur=1.0)
    hero_side(cv, T, 250 + 0.92 * V_GROUND * k * T * 0.95, gy, k, walk=1.0, face=('neutral', 'neutral', 0.0), rim=0.8, sl=1.4)
    fgl(cv, 'up_fg_dune.png', 640 - (wc.px - 880) * 1.4, 905, 1.3, blur=3, gain=0.8)
    fgl(cv, 'up_fg_rocks.png', 1050 + (wc.px - 880) * 2.4, 880, 0.55, blur=3.5, gain=0.7, flip=-1)
    leak(cv, *wc.pt(585, 262), 380, T, 0.35, (120, 195, 255)); fin(cv, T, 3001, 0.45); shake(cv, T, 0.7, 1)


# 2. medium side tracking shot, expression determined -> tired
def s2(cv, T):
    wc = cam(T, 4.2, 9.6, (700, 330, 1.35), (730, 326, 1.42), 'pr_dawn', cv=cv)
    cv[:] = heat_haze(cv, T, 1.4, 0.05, 2.4, 330, 520)
    k = 0.5; gy = 610
    props(cv, T, gy, k, 1.0, a=0.9)
    f = side_face(T - 4.2, [(0, 'determined'), (2.4, 'tired')])
    hero_side(cv, T, 470 + 8 * math.sin(T * 0.8), gy, k, walk=1.0, face=f, sun_h=0.18, head=-1.0)
    puffs(cv, T, 4.0, 10.0, 22, (300, gy - 12, 240, 14), (128, 178, 215), seed=5, size=(30, 70), rise=(6, 22), spread=(40, 110), grow=1.9, life=1.3, alpha=0.34, wind=(-330, 0))
    fgl(cv, 'up_fg_rocks.png', 120 - 160 * seg(T, 4.2, 9.6), 760, 1.0, blur=8, gain=0.7, alpha=0.9)
    leak(cv, *wc.pt(585, 262), 420, T, 0.4, (120, 195, 255)); fin(cv, T, 3002, 0.45); shake(cv, T, 1.0, 2)


# 3. profile close-up (slow walk), worried; background heavily blurred
def s3(cv, T):
    wc = cam(T, 9.2, 12.6, (700, 300, 1.6), (720, 296, 1.7), 'pr_dawn', cv=cv); blur_bg(cv, 7.0)
    f = side_face(T - 9.2, [(0, 'worried')])
    k = 1.45; gy = 1690 + 20 * seg(T, 9.2, 12.6)
    hero_side(cv, T, 560 - 20 * seg(T, 9.2, 12.6), gy, k, walk=0.0, face=f, sun_h=0.3, head=-2.0, rim=0.8, sl=0.0)
    leak(cv, *wc.pt(585, 262), 520, T, 0.55, (120, 195, 255)); fin(cv, T, 3003, 0.55, mo=40); shake(cv, T, 1.4, 3)


# 4. front medium shot: he stops, looks around, shades his eyes
def s4(cv, T):
    t = T - 12.2
    wc = cam(T, 12.2, 17.6, (760, 296, 1.5), (780, 296, 1.58), 'pr_dawn', cv=cv); blur_bg(cv, 3.5)
    hf = ev(t, 1.3, 2.1) * (1 - ev(t, 4.4, 5.1)); ha = ev(t, 1.8, 2.7) * (1 - ev(t, 3.9, 4.6)); hand = ha
    pose = {'aL': 4, 'fL': 6, 'aR': 6 + 94 * ha, 'fR': 6 - 122 * hf, 'fuR': 1 - 0.65 * ha, 'ffR': 1 - 0.2 * hf, 'head': 5 * math.sin(t * 0.9) + 4 * hand}
    f = [(0, 'worried'), (3.2, 'determined')]
    cur = f[0][1]
    fa = ('worried', 'determined', sstep(clamp((t - 3.2) / 0.5))) if t > 3.2 else ('worried', 'worried', 0.0)
    if fa[2] >= 1.0: fa = ('determined', 'determined', 0.0)
    if fa[2] == 0.0 and (t % 3.1) < 0.13: fa = (fa[0], 'blink', 0.95 * math.sin(math.pi * (t % 3.1) / 0.13))
    hero_front(cv, T, 520 + 6 * math.sin(t * 0.5), 690, 0.56, fa, pose, sun_h=0.2, rim=0.7, sl=0.0, t=t)
    leak(cv, 120, 240, 420, T, 0.45, (120, 195, 255)); fin(cv, T, 3004, 0.5, mo=30); shake(cv, T, 1.1, 4)


# 5. front close-up: worried -> shocked -> tired
def s5(cv, T):
    t = T - 17.2
    wc = cam(T, 17.2, 21.6, (760, 300, 1.8), (790, 296, 1.95), 'pr_dawn', cv=cv); blur_bg(cv, 8.0)
    k = lerp(1.4, 1.52, seg(T, 17.2, 21.6)); jolt = 1 + 0.035 * ev(t, 1.4, 1.65)
    if t < 1.3: fa = ('worried', 'worried', 0.0)
    elif t < 3.0: fa = ('worried', 'shocked', sstep(clamp((t - 1.3) / 0.22))); fa = ('shocked', 'shocked', 0.0) if fa[2] >= 1.0 else fa
    else: fa = ('shocked', 'tired', sstep(clamp((t - 3.0) / 0.6))); fa = ('tired', 'tired', 0.0) if fa[2] >= 1.0 else fa
    if fa[2] == 0.0 and fa[0] == 'worried' and (t % 3.1) < 0.13: fa = ('worried', 'blink', 0.95 * math.sin(math.pi * (t % 3.1) / 0.13))
    hero_front(cv, T, 640 + 5 * math.sin(t * 0.6), 52 + 1133 * k * jolt + 18 * seg(T, 17.2, 21.6), k * jolt, fa, {'aL': 6, 'aR': 6, 'fL': 6, 'fR': 6, 'head': 2 + 3 * ev(t, 3.0, 3.8)}, sun_h=0.3, rim=0.9, sl=0.0, t=t)
    leak(cv, 120, 200, 520, T, 0.55, (120, 195, 255)); fin(cv, T, 3005, 0.55, mo=40); shake(cv, T, 1.5, 5)


# 6. pull-back: tiny and alone, long shadow, fade out
def s6(cv, T):
    t = T - 21.0
    wc = cam(T, 21.0, 26.4, (800, 330, 1.55), (800, 300, 1.05), 'pr_dawn', cv=cv)
    cv[:] = heat_haze(cv, T, 1.2, 0.05, 2.0, 300, 480)
    X, Y = wc.pt(930, 520); k = 0.2 * wc.s / SC0
    sv = {'aL': 8, 'fL': 8, 'aR': 8, 'fR': 8, 'head': -4 * math.sin(t * 0.7)}
    hero_front(cv, T, X, Y, k * 0.95, ('tired', 'tired', 0.0), sv, sun_h=0.12, rim=1.0, sl=1.6, t=t)
    sand(cv, T, 0.06 + 0.1 * seg(T, 21, 26), 77, -1.0, 0.5)
    leak(cv, *wc.pt(585, 262), 380, T, 0.4, (120, 195, 255)); fin(cv, T, 3006, 0.5); shake(cv, T, 0.6, 6)


SHOTS3 = [('s1', 0.0, 4.4, s1, 0.0), ('s2', 4.4, 9.4, s2, 0.2), ('s3', 9.4, 12.4, s3, 0.2), ('s4', 12.4, 17.4, s4, 0.2), ('s5', 17.4, 21.2, s5, 0.2), ('s6', 21.2, DP3, s6, 0.25)]


class PartUP3(P2.PartP2):
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
