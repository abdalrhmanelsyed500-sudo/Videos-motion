"""FRONT rig (v3): body from the AI-painted FRONT parts sheet (pf_*.png via prepare_front.py) + hi-res expression heads (ph_*.png).
Torso, arms (upper arm+forearm skinned as one image so the elbow bends like flesh), legs+shorts as one piece (standing / idle / gesturing / talking shots).
Walking is done with side_rig.py (profile).  draw_front(...) -> hand positions dict for props."""
import cv2, math, numpy as np
from engine import *
from rig2 import place_skin
import hook_scenes as HK
from side_rig import _raw, _cx, _over, _layer, mul_t

_c = {}
HEADK = 0.37
ARMK = 0.88
HEADUP = 26.0
LEGX, LEGY, TORX, TORY = 1.0, 1.05, 1.0, 1.38
UAX, UAY, FAX, FAY = 0.80, 1.05, 0.80, 1.08


def build():
    if _c: return _c
    arm, fl, fr = _raw('f_arm') if False else cv2.imread('assets/layers/pf_arm.png', -1), cv2.imread('assets/layers/pf_foreL.png', -1), cv2.imread('assets/layers/pf_foreR.png', -1)
    for side, fore, arm_i in (('L', fl, arm), ('R', fr, arm[:, ::-1].copy())):
        # rigid two-piece arm with a ROUND elbow: the forearm's top end sits hidden under the disc-shaped lower end of the upper arm and pivots about its centre -> no gap at any angle
        sh = (_cx(arm_i, 30), 30.0); el = (_cx(arm_i, 112), 112.0); fe = (_cx(fore, 26), 6.0)
        _c['arm' + side] = dict(A=_layer(arm_i), F=_layer(fore), sh=sh, el=el, fe=fe, hand=(_cx(fore, fore.shape[0] - 40), fore.shape[0] - 45.0))
    t = cv2.imread('assets/layers/pf_torso.png', -1); _c['torso'] = dict(L=_layer(t), neck=(_cx(t, 6), 40.0), w=t.shape[1], h=t.shape[0], shL=(28.0, 42.0), shR=(t.shape[1] - 28.0, 42.0), bot=(_cx(t, t.shape[0] - 8), t.shape[0] - 4.0))
    lg = cv2.imread('assets/layers/pf_legs.png', -1); _c['legs'] = dict(L=_layer(lg), w=lg.shape[1], h=lg.shape[0], top=(_cx(lg, 14), 26.0), foot=(_cx(lg, lg.shape[0] - 30), lg.shape[0] - 6.0))
    _c['neck'] = _layer(cv2.imread('assets/layers/pf_neck.png', -1))
    return _c


def head_neck(name):
    key = 'hn_' + name
    if key not in _c:
        Ly = HK.L('ph_' + name); im = Ly.img; row = np.where(im[int(Ly.h * 0.45), :, 3] > 0.5)[0]; _c[key] = ((row.min() + row.max()) / 2.0 if len(row) else Ly.w / 2.0, Ly.h * 0.86)
    return _c[key]


def draw_front(cv, t, X, gy, sc, face=('neutral', 'neutral', 0.0), flip=1, gain=1.0, tint=None, pose=None, ph0=0.0, shadow=True, hk=HEADK):
    """pose: aL,aR = arm abduction (deg, +ve = away from body), fL,fR = elbow flexion (+ve = hand towards chest/face), head, lean, sway"""
    C = build(); P = pose or {}; kw = dict(gain=gain, tint=tint)
    lg, tr = C['legs'], C['torso']
    br = 0.010 * math.sin(t * 2.1 + ph0); sw = P.get('sway', 0.0) + 0.55 * math.sin(t * 0.9 + ph0)
    if shadow: HK.shadow(cv, X, gy, sc * 1.05 * LEGY)
    fx = sc * flip
    # every limb segment is stretched in its OWN frame (no skew when rotated) so that the front figure has exactly the same height/proportions as the side rig
    Tl = M3(X, gy, fx * LEGX, sc * LEGY, sw * 0.5, lg['foot'][0], lg['foot'][1])
    place(cv, lg['L'], Tl, **kw)
    top = lg['top']; pt = Tl @ np.array([top[0], top[1], 1.0])
    rotT = sw * 0.5 + flip * (-sw * 0.9 + P.get('lean', 0.0))
    Tt = M3(pt[0], pt[1], fx * TORX, sc * TORY * (1 + br), rotT, tr['bot'][0], tr['bot'][1])
    fa, fb, fm = face; LA = HK.L('ph_' + fa); hn = head_neck(fa)
    hrot = P.get('head', 0.0) + 1.6 * math.sin(t * 1.1 + ph0) + 0.8 * math.sin(t * 2.3 + 1)
    pn = Tt @ np.array([tr['neck'][0], tr['neck'][1] - 12 - HEADUP, 1.0])
    Th = M3(pn[0], pn[1], fx * hk, sc * hk, rotT + flip * hrot, hn[0], hn[1])
    place(cv, LA, Th, **kw)
    if fm > 0.01 and fb != fa: place(cv, HK.L('ph_' + fb), Th, alpha=fm, **kw)
    place(cv, C['neck'], Tt @ M3(0, 0, 1, 1, 0, 0, 80), **kw)
    place(cv, tr['L'], Tt, **kw)
    hands = {}
    for side, sg in (('L', 1), ('R', -1)):
        a = C['arm' + side]; sh = tr['sh' + side]
        ang = sg * (P.get('a' + side, 5.0) + 1.5 * math.sin(t * 1.3 + ph0 + (0 if side == 'L' else 1.7)))
        fl_ = -sg * (P.get('f' + side, 8.0) + 3 * math.sin(t * 1.7 + ph0 + (1 if side == 'L' else 2)))
        ps = Tt @ np.array([sh[0], sh[1], 1.0]); r0 = rotT + flip * ang
        T0 = M3(ps[0], ps[1], fx * UAX, sc * UAY, r0, a['sh'][0], a['sh'][1]); ex, ey = a['el']
        pe = T0 @ np.array([ex, ey, 1.0])
        T1 = M3(pe[0], pe[1], fx * FAX, sc * FAY, r0 + flip * fl_, a['fe'][0], a['fe'][1])
        place(cv, a['F'], T1, **kw); place(cv, a['A'], T0, **kw)
        hx, hy = a['hand']; p = T1 @ np.array([hx, hy, 1.0]); hands[side] = (float(p[0]), float(p[1]))
    return hands
