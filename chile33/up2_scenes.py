"""UPGRADE TEST 2: (1) real SIDE-PROFILE walk with a jointed skeleton (side_rig.py: knee/elbow/ankle) on a tracking camera with ground-speed parallax props;
(2) FRONT close-up with a script of consistent facial expressions (rig2 face=..., AI-repainted heads ph_*.png) + automatic blinking."""
from up_scenes import *
import side_rig as SR

DP2U = 15.2
V_GROUND = 930.0      # screen px/s of the planted foot per unit scale (see side_rig: sweep of 2*(Lt+Ls)*sin(27deg) per half cycle)


def props(cv, T, gy, k, speed_scale, depth0=0.0, a=1.0, blur=0.0, y_lo=None):
    """rocks passing at ground speed (further = smaller + slower) -> reads as a tracking shot"""
    v = V_GROUND * k
    for i, (u0, yy, s) in enumerate([(120, 14, 0.10), (560, 40, 0.15), (940, 8, 0.085), (1330, 62, 0.23), (1700, 22, 0.12), (2090, 50, 0.18), (2420, 12, 0.095)]):
        d = (gy + yy - 340.0) / (gy - 340.0); sp = v * d * speed_scale
        span = 2700.0; x = (u0 - sp * T) % span - 200
        fgl(cv, 'up_fg_rocks2.png', x, gy + yy, s * 1.7 * (0.7 + 0.5 * d) * (k / 0.6), blur=blur + (1.5 if yy > 40 else 0), gain=0.95 * (0.85 + 0.15 * d), alpha=a)


def shot_walk(cv, T):
    k = 0.47; gy = 640
    wc = cam(T, 0, 6.2, (700, 304, 1.30), (760, 300, 1.42), 'pr_empty', cv=cv)
    cv[:] = heat_haze(cv, T, 1.4, 0.05, 2.4, 300, 470)
    wk = sstep(clamp(T / 0.9))
    props(cv, T, gy, k, 1.0 if T > 0.9 else wk, a=0.9)
    SR.draw_side(cv, T, 560 + 30 * math.sin(T * 0.5), gy, k, 1, walk=wk, ph0=0.0, head=-1.0)
    puffs(cv, T, 0.3, 6.6, 22, (330, gy - 12, 260, 14), (128, 178, 215), seed=3, size=(30, 70), rise=(6, 22), spread=(40, 110), grow=1.9, life=1.3, alpha=0.38, wind=(-310 * wk, 0))
    fgl(cv, 'up_fg_dune.png', 640, 1060, 1.3, blur=6, gain=0.85, alpha=0.9)
    leak(cv, 1180, 60, 480, T, 0.42, (120, 195, 255)); fin(cv, T, 2101, 0.45)


SCRIPT = [(0.0, 'neutral'), (1.5, 'worried'), (3.0, 'shocked'), (4.3, 'tired'), (6.0, 'determined'), (7.4, 'smile')]


def face_at(t):
    """(A, B, mix): cross-fade 0.35 s between scripted expressions; neutral blinks every ~3 s"""
    xf = 0.35; cur = SCRIPT[0][1]; prev = cur; t0 = 0.0
    for (ts, nm) in SCRIPT:
        if t >= ts: prev, cur, t0 = cur, nm, ts
    if cur == prev: A, B, m = cur, cur, 0.0
    else: A, B, m = prev, cur, sstep(clamp((t - t0) / xf))
    if m >= 1.0: A, B, m = B, B, 0.0
    if A == B and A in ('neutral', 'smile') and m == 0.0:
        ph = t % 3.1
        if ph < 0.14: return (A, 'blink', 0.95 * math.sin(math.pi * ph / 0.14))
    return (A, B, m)


def shot_face(cv, T):
    t = T - 6.0
    wc = cam(T, 6.0, 15.2, (770, 300, 1.7), (800, 296, 1.85), 'pr_empty', cv=cv)
    blur_bg(cv, 6.5); cv[:] = heat_haze(cv, T, 2.0, 0.04, 2.4, 100, 720)
    k = seg(T, 6.0, 15.2)
    sh = 1.0 + 0.04 * ev(t, 2.9, 3.2)       # tiny shock jolt
    hero_k = lerp(1.30, 1.40, k)
    rig2.draw_char2(cv, 'p', t, 640 + 5 * math.sin(t * 0.7), lerp(1410, 1450, k), hero_k * sh, ph0=0.3, gain=0.97, face=face_at(t),
                    pose={'aL': 6, 'aR': 6, 'fL': -6, 'fR': -6, 'head': 3 * math.sin(t * 1.1) + (-6 if 1.5 < t < 3.0 else 0) + (5 * ev(t, 6.0, 6.6) if t > 5.9 else 0), 'lean': 1.5 * math.sin(t * 0.6)})
    leak(cv, 1180, 40, 520, T, 0.5, (110, 185, 255)); leak(cv, 100, 700, 400, T, 0.12, (90, 150, 230)); fin(cv, T, 2102, 0.5, mo=34)


SHOTSU2 = [('walk', 0.0, 6.0, shot_walk, 0.0), ('face', 6.0, DP2U, shot_face, 0.4)]


class PartUP2(P2.PartP2):
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTSU2):
            hi = t1 + (SHOTSU2[i + 1][4] / 2 if i + 1 < len(SHOTSU2) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTSU2) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
