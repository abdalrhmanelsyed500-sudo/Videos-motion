"""FRONT rig v4: body cut from the AI model-sheet figure (prepare_mu.py -> mf_*.png), SAME proportions as the side rig; ph_* expression heads.
All pieces live in the 'cut' coordinate frame of assets/raw/mu_front_cut.png (feet midpoint = (155,825)); joints rotate about their pivots -> no skew, no stretching hacks.
Hierarchy: root(feet) -> hip(L/R) -> thigh -> knee -> shin ; root -> pelvis -> torso (waist 160,440) -> [head, shoulder -> upper arm -> elbow -> forearm].
draw_front(...) -> hands dict (screen px) for props."""
import cv2, json, math, numpy as np
from engine import *
import hook_scenes as HK
from side_rig import _layer

_c = {}
FEET = (155.0, 825.0)
S0 = 1.39                # cut px -> side-rig px at sc=1 (figure height 815 cut px == 1134 px of the side rig)
HK2 = 0.29              # ph head px -> cut px
HEAD_AT = (160.0, 152.0)  # ph head anchor (neck base) in cut coords
WAIST = (160.0, 440.0)
SH = {'L': (80.0, 198.0), 'R': (240.0, 198.0)}
EL = {'L': (58.0, 326.0), 'R': (261.0, 326.0)}
HIP = {'L': (118.0, 505.0), 'R': (195.0, 505.0)}
KN = {'L': (113.0, 612.0), 'R': (196.0, 612.0)}
HAND = {'L': (45.0, 480.0), 'R': (268.0, 480.0)}     # hand centre in cut coords (for props)
ORDER_LEG = ('shin', 'thigh')


def build():
    if _c: return _c
    meta = json.load(open('assets/layers/mf_pieces.json'))
    for k, off in meta.items():
        im = cv2.imread('assets/layers/mf_%s.png' % k, -1); _c[k] = (_layer(im), off)
    return _c


def head_layer(name):
    key = 'h_' + name
    if key not in _c:
        im = cv2.imread('assets/layers/ph_%s.png' % name, -1); H, W = im.shape[:2]
        row = np.where(im[int(H * 0.45), :, 3] > 128)[0]; cx = (row.min() + row.max()) / 2.0 if len(row) else W / 2.0
        f = im.copy(); y0 = int(H * 0.84); y1 = int(H * 0.91)       # feather the cut neck so it melts into the torso's neck
        ramp = np.clip((y1 - np.arange(H)) / float(y1 - y0), 0, 1)
        f[:, :, 3] = (f[:, :, 3] * ramp[:, None]).astype(np.uint8)
        _c[key] = (_layer(f), (cx, H * 0.86))
    return _c[key]


def J(T, pivot, rot):
    """rotate about pivot (cut coords) in the frame T"""
    return T @ M3(pivot[0], pivot[1], 1, 1, rot, pivot[0], pivot[1])


def piece(cv, name, T, **kw):
    L, (ox, oy) = _c[name]
    place(cv, L, T @ M3(ox, oy, 1, 1, 0, 0, 0), **kw)


def draw_front(cv, t, X, gy, sc, face=('neutral', 'neutral', 0.0), flip=1, gain=1.0, tint=None, pose=None, ph0=0.0, shadow=True, hk=None):
    """pose: aL,aR arm abduction (deg, +ve = away from body); fL,fR elbow flexion (+ve = hand towards chest; NEGATIVE = forearm up/out, used for the brow salute);
    hipL,hipR leg abduction; kneeL,kneeR; head; lean; sway; tilt (pelvis)"""
    build(); P = pose or {}; kw = dict(gain=gain, tint=tint); S = S0 * sc
    br = 0.008 * math.sin(t * 2.1 + ph0)
    sw = P.get('sway', 0.0) + 0.45 * math.sin(t * 0.9 + ph0)
    if shadow: HK.shadow(cv, X, gy, sc * 1.05)
    Tr = M3(X, gy, S * flip, S, 0, FEET[0], FEET[1])
    Tr = J(Tr, FEET, sw * 0.5)
    for s, sg in (('L', 1), ('R', -1)):
        Th = J(Tr, HIP[s], sg * (P.get('hip' + s, 0.0) + 0.0))
        piece(cv, 'thigh' + s, Th, **kw)
        Tk = J(Th, KN[s], sg * P.get('knee' + s, 0.0))
        piece(cv, 'shin' + s, Tk, **kw)
    # re-draw thigh over shin so that the knee disc covers the shin top
    for s, sg in (('L', 1), ('R', -1)):
        Th = J(Tr, HIP[s], sg * P.get('hip' + s, 0.0)); piece(cv, 'thigh' + s, Th, **kw)
    Tp = J(Tr, (157.0, 500.0), P.get('tilt', 0.0) + 0.5 * math.sin(t * 0.9 + ph0 + 1.0))
    piece(cv, 'pelvis', Tp, **kw)
    Tt = J(Tp, WAIST, P.get('lean', 0.0) - 0.4 * sw)
    Tt = Tt @ M3(WAIST[0], WAIST[1], 1, 1 + br, 0, WAIST[0], WAIST[1])
    piece(cv, 'torso', Tt, **kw)
    fa, fb, fm = face; hl, (hx, hy) = head_layer(fa)
    hrot = P.get('head', 0.0) + 1.5 * math.sin(t * 1.1 + ph0) + 0.7 * math.sin(t * 2.3 + 1)
    kk = HK2 * (hk / 0.37 if hk else 1.0)
    Thd = Tt @ M3(HEAD_AT[0], HEAD_AT[1], kk, kk, hrot, hx, hy)
    place(cv, hl, Thd, **kw)
    if fm > 0.01 and fb != fa:
        h2, _ = head_layer(fb); place(cv, h2, Thd, alpha=fm, **kw)
    hands = {}
    for s, sg in (('L', 1), ('R', -1)):
        ang = sg * (P.get('a' + s, 4.0) + 1.2 * math.sin(t * 1.3 + ph0 + (0 if s == 'L' else 1.7)))
        fl = -sg * (P.get('f' + s, 6.0) + 2.0 * math.sin(t * 1.7 + ph0 + (1 if s == 'L' else 2)))
        fu, ff = P.get('fu' + s, 1.0), P.get('ff' + s, 1.0)         # foreshortening (arm pointing towards the camera) of upper arm / forearm
        Tr0 = J(Tt, SH[s], ang)
        Ta = Tr0 @ M3(SH[s][0], SH[s][1], 1, fu, 0, SH[s][0], SH[s][1])
        pe = Ta @ np.array([EL[s][0], EL[s][1], 1.0]); pe0 = Tr0 @ np.array([EL[s][0], EL[s][1], 1.0])
        Tf = J(Tr0, EL[s], fl).copy(); Tf[0, 2] += pe[0] - pe0[0]; Tf[1, 2] += pe[1] - pe0[1]
        Tf = Tf @ M3(EL[s][0], EL[s][1], 1, ff, 0, EL[s][0], EL[s][1])
        piece(cv, 'arm%s_fo' % s, Tf, **kw); piece(cv, 'arm%s_up' % s, Ta, **kw)
        p = Tf @ np.array([HAND[s][0], HAND[s][1], 1.0]); hands[s] = (float(p[0]), float(p[1]))
    return hands
