"""UPGRADE TEST (Prosperi): richer cinematography + gap-free limbs.  Shots: wide crane with 3-layer parallax / low-angle approach with foreground DOF / close-up with background blur /
macro feet (knee-bend walk) / backlit silhouette.  Uses rig2 (skinned legs, elbow ball-joints), chroma-keyed foreground assets (up_fg_*), depth-of-field blur, light leaks."""
from pros8_scenes import *
import rig2
import cv2

DPU = 19.6
_bl = {}
def fgl(cv, name, x, y, sc, blur=0.0, gain=1.0, alpha=1.0, flip=1, tint=None):
    k = (name, round(blur, 1))
    if k not in _bl:
        Ly = get_layer(name)
        if blur > 0.2:
            im = cv2.GaussianBlur(Ly.img, (0, 0), blur); _bl[k] = Layer.from_array(im)
        else: _bl[k] = Ly
    Ly = _bl[k]; place(cv, Ly, M3(x, y, sc * flip, sc, 0, Ly.w / 2, Ly.h), gain=gain, alpha=alpha, tint=tint)


def hero(cv, T, x, gy, sc, flip=1, **kw):
    kw.setdefault('gain', 0.97); rig2.draw_char2(cv, 'p', T, x, gy, sc, flip=flip, ph0=0.3, **kw)


def hero_on(cv, T, wc, X, Y, base, flip=1, **kw):
    x, y = wc.pt(X, Y); hero(cv, T, x, y, wc.sc(Y, base), flip, **kw)


def blur_bg(cv, s): cv[:] = cv2.GaussianBlur(cv, (0, 0), s)


def leak(cv, x, y, r, T, amt=0.5, col=(120, 190, 255)):
    k = amt * (0.85 + 0.15 * math.sin(T * 2.1)); glowpt(cv, x, y, r, col, k)


# A: wide crane-in with three depth layers
def shot_a(cv, T):
    wc = cam(T, 0, 4.9, (880, 272, 1.25), (790, 338, 1.5), 'pr_empty', cv=cv)
    cv[:] = heat_haze(cv, T, 1.6, 0.05, 2.6, 250, 520)
    k = seg(T, 0, 4.9); hero_on(cv, T, wc, lerp(1010, 780, k), 500, 0.5, flip=-1, walk=1.0, pose={'aL': 10, 'aR': 10, 'head': 3})
    fgl(cv, 'up_fg_dune.png', 640 - (wc.px - 800) * 1.5, 1120, 1.25, blur=2.2, gain=0.92)
    fgl(cv, 'up_fg_rocks.png', 190 - (wc.px - 800) * 2.7, 900, 0.62, blur=3.5, gain=0.85)
    leak(cv, 1130, 60, 360, T, 0.35); fin(cv, T, 2001, 0.4)


# B: low-angle approach, rack-focus foreground
def shot_b(cv, T):
    wc = cam(T, 4.5, 9.8, (700, 212, 1.7), (740, 214, 1.55), 'pr_dawn', cv=cv)
    cv[:] = cv2.GaussianBlur(cv, (0, 0), 1.2)
    k = seg(T, 4.7, 9.6)
    hero(cv, T, lerp(700, 640, k), lerp(545, 650, k), lerp(0.30, 0.56, ease_out(k) * 0.4 + k * 0.6), walk=1.0, pose={'aL': 12, 'aR': 12, 'head': 2, 'lean': 2})
    fgl(cv, 'up_fg_dune.png', 640 - (wc.px - 720) * 2.2, 925, 1.25, blur=4 * (1 - 0.5 * k), gain=0.9)
    fgl(cv, 'up_fg_rocks.png', 110 - (wc.px - 720) * 3.0, 800, 1.15, blur=7.0, gain=0.8, alpha=0.95)
    leak(cv, *wc.pt(585, 262), 330, T, 0.38, (130, 200, 255)); fin(cv, T, 2002, 0.45)


# C: close-up with depth of field and a light leak
def shot_c(cv, T):
    wc = cam(T, 9.4, 14.0, (770, 300, 1.7), (800, 296, 1.85), 'pr_empty', cv=cv)
    blur_bg(cv, 6.5); cv[:] = heat_haze(cv, T, 2.0, 0.04, 2.4, 100, 720)
    k = seg(T, 9.4, 14.0); h = ev(T, 9.9, 10.9) * (1 - ev(T, 12.6, 13.4))
    hero(cv, T, 640 + 6 * math.sin(T * 0.7), lerp(1405, 1470, k), lerp(1.3, 1.42, k), pose={'aL': 8 + 108 * h, 'fL': 140 * h, 'aR': 8, 'fR': -10, 'head': 4 + 8 * math.sin((T - 10) * 1.6)})
    leak(cv, 1180, 40, 520, T, 0.55, (110, 185, 255)); leak(cv, 100, 700, 400, T, 0.12, (90, 150, 230)); fin(cv, T, 2003, 0.5, mo=40)


# D: macro of the feet - knee-bend steps with dust
def shot_d(cv, T):
    wc = cam(T, 13.8, 16.5, (780, 360, 2.2), (800, 380, 2.2), 'pr_empty', cv=cv); blur_bg(cv, 8.0)
    hero(cv, T, 640, 600, 1.0, walk=1.0, stride=1.2, pose={'aL': 8, 'aR': 8})
    puffs(cv, T, 13.8, 16.9, 22, (430, 585, 420, 24), (128, 178, 215), seed=7, size=(50, 110), rise=(8, 30), spread=(60, 140), grow=1.9, life=1.4, alpha=0.5)
    fgl(cv, 'up_fg_dune.png', 600 - (T - 14) * 60, 1090, 1.3, blur=9.0, gain=0.9, alpha=0.9)
    leak(cv, 1150, 80, 420, T, 0.3); fin(cv, T, 2004, 0.5)


# E: backlit silhouette crossing the low sun
def shot_e(cv, T):
    wc = cam(T, 16.2, 19.8, (585, 300, 1.1), (585, 288, 1.25), 'pr_dawn', cv=cv)
    sx, sy = wc.pt(585, 262); glowpt(cv, sx, sy, 520, (150, 205, 255), 0.30); glowpt(cv, sx, sy, 150, (200, 240, 255), 0.35)
    k = seg(T, 16.4, 19.6)
    hero_on(cv, T, wc, lerp(930, 300, k), 590, 1.15, flip=-1, walk=1.0, gain=0.04, pose={'aL': 12, 'aR': 12})
    fgl(cv, 'up_fg_rocks.png', 1130, 830, 0.95, blur=1.2, gain=0.18, flip=-1)
    fin(cv, T, 2005, 0.55)


SHOTSU = [('a', 0.0, 4.6, shot_a, 0.0), ('b', 4.6, 9.5, shot_b, 0.4), ('c', 9.5, 13.9, shot_c, 0.4), ('d', 13.9, 16.4, shot_d, 0.4), ('e', 16.4, DPU, shot_e, 0.4)]


class PartUP(P2.PartP2):
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTSU):
            hi = t1 + (SHOTSU[i + 1][4] / 2 if i + 1 < len(SHOTSU) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTSU) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
