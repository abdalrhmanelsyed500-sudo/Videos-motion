"""SIDE-PROFILE rig (v3): a real jointed skeleton drawn from AI-painted side-view parts (assets/layers/ps_*.png, see prepare_side.py).
Bones: pelvis > torso > head ; hip > thigh > knee > shin > ankle > shoe ; shoulder > upper arm > elbow > forearm.  Limbs are one painted image each (thigh+calf+gaiter, arm+forearm)
skinned per pixel so the KNEE and ELBOW bend like flesh with no gaps.  Walk cycle = real gait: hip swing, knee flexion in swing, ankle roll, pelvis bob/tilt, counter-swing arms,
planted foot is kept on the ground by forward kinematics.  Character faces RIGHT (flip=-1 mirrors)."""
import cv2, math, numpy as np
from engine import *
from rig2 import place_skin
import hook_scenes as HK

LEGK = 1.15
_c = {}


def _raw(n):
    im = cv2.imread(f'assets/layers/ps_{n}.png', cv2.IMREAD_UNCHANGED); return im


def _cx(im, y):
    row = np.where(im[int(y), :, 3] > 128)[0]; return float((row.min() + row.max()) / 2) if len(row) else im.shape[1] / 2.0


def _over(dst, src, x, y):
    """straight-alpha BGRA src over dst (canvas grows via preallocated dst)"""
    x, y = int(round(x)), int(round(y)); h, w = src.shape[:2]; roi = dst[y:y + h, x:x + w]
    a = src[..., 3:] / 255.0; ra = roi[..., 3:] / 255.0; oa = a + ra * (1 - a)
    rgb = (src[..., :3] * a + roi[..., :3] * ra * (1 - a)) / np.maximum(oa, 1e-4)
    roi[..., :3] = rgb; roi[..., 3:] = oa * 255


def _layer(im):
    f = im.astype(np.float32); a = f[..., 3:] / 255.0; f[..., :3] *= a; f[..., 3:] = a; return Layer.from_array(f)


def build():
    if _c: return _c
    leg, shin = _raw('leg'), _raw('shin'); gai = shin[178:]
    # leg canvas = leg + gaiter pasted around the ankle
    gx = _cx(leg, 350) - _cx(gai, 20); H0 = 335 + gai.shape[0] + 4
    cv_ = np.zeros((H0, leg.shape[1] + 40, 4), np.float32); cv_[..., :3] = 0
    off = 20
    _over(cv_, leg.astype(np.float32), off, 0); _over(cv_, gai.astype(np.float32), off + gx, 335)
    cv_ = cv_.astype(np.uint8)
    hip = (_cx(leg, 40) + off, 40.0); knee = (_cx(leg, 238) + off, 238.0); ank = (_cx(leg, 392) + off, 405.0)
    k = LEGK; cvk = cv2.resize(cv_, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
    _c['leg'] = dict(L=_layer(cvk), hip=(hip[0] * k, hip[1] * k), knee=(knee[0] * k, knee[1] * k), ank=(ank[0] * k, ank[1] * k))
    # arm canvas = forearm under upper arm
    for nm in ('arm_a', 'arm_b'):
        arm, fore = _raw(nm), _raw('fore')
        sh = (_cx(arm, 42), 40.0); el = (_cx(arm, 172), 172.0); fe = (_cx(fore, 24), 22.0)
        fx, fy = el[0] - fe[0], el[1] - fe[1]; ox = max(0, -fx) + 4
        cw = int(max(arm.shape[1], fx + fore.shape[1] + ox) + ox + 4); ch = int(max(arm.shape[0], fy + fore.shape[0]) + 4)
        buf = np.zeros((ch, cw, 4), np.float32)
        _over(buf, fore.astype(np.float32), fx + ox, fy); _over(buf, arm.astype(np.float32), ox, 0)
        _c[nm] = dict(L=_layer(buf.astype(np.uint8)), sh=(sh[0] + ox, sh[1]), el=(el[0] + ox, el[1]), hand=(fe[0] + fx + ox, fy + fore.shape[0] - 40))
    t = _raw('torso'); _c['torso'] = dict(L=_layer(t), neck=(_cx(t, 14), 14.0), sho=(_cx(t, 112), 112.0), hip=(_cx(t, 395), 410.0))
    h = _raw('head'); _c['head'] = dict(L=_layer(h), neck=(_cx(h, 248), 244.0))
    s = _raw('shoe'); _c['shoe'] = dict(L=_layer(s), ank=(50.0, 14.0), toe=(165.0, 70.0))
    return _c


def gait(ph, side, A=27.0, KM=62.0):
    """near leg phase ph; returns thigh angle, knee flexion, foot roll (deg, +ve = clockwise = backwards when facing right)"""
    p = ph + (math.pi if side == 'far' else 0.0)
    th = -A * math.sin(p) + 3.0
    sw = max(0.0, math.cos(p))                       # swing phase (leg moving forward)
    kn = 4.0 + KM * sw ** 1.5 + 9.0 * max(0.0, math.sin(p)) * max(0.0, 1 - 2 * abs(math.sin(p) - 0.45)) * 0
    kn += 8.0 * max(0.0, -math.sin(p)) ** 2 * (1 - sw)          # slight loading flex
    toe = 18.0 * max(0.0, -math.sin(p) - 0.2) * (1 - sw) / 0.8      # heel lifts at push-off
    return th, kn, toe


def mul_t(a, b):
    if b is None: return a
    if a is None: return b
    return tuple(x * y for x, y in zip(a, b))


def draw_side(cv, t, X, gy, sc, flip=1, walk=1.0, ph0=0.0, gain=1.0, tint=None, speed=1.1, head=0.0, lean=4.0, shadow=True, arms=(0.0, 0.0), far_tint=(0.74, 0.74, 0.8), elbow=0.0, face=None):
    """X, gy = screen position of the ground contact; sc = scale; arms=(extra shoulder angle, extra elbow flex) added to the walk swing"""
    C = build(); k = sc
    ph = 2 * math.pi * speed * t + ph0; leg = C['leg']; hp = leg['hip']; kx, ky = leg['knee']; ax, ay = leg['ank']
    Lt = ky - hp[1]; Ls = ay - ky; shoe = C['shoe']; SK = LEGK
    drop = (shoe['L'].h - shoe['ank'][1]) * SK * 0.86
    G = {}
    for side in ('near', 'far'):
        th, kn, toe = gait(ph, side)
        th = 3.0 + (th - 3.0) * walk; kn = 4.0 + (kn - 4.0) * walk; toe *= walk
        G[side] = (th, kn, toe, Lt * math.cos(math.radians(th)) + Ls * math.cos(math.radians(th + kn)))
    hipY = gy - (max(G['near'][3], G['far'][3]) + drop) * k
    root = M3(X, hipY, k * flip, k, 0, 0, 0)
    if shadow: HK.shadow(cv, X, gy, sc * 0.95)
    tor = C['torso']; ln = lean * walk + 1.0
    Tt = root @ M3(0, 0, 1, 1, ln + 1.6 * math.sin(2 * ph) * walk, tor['hip'][0], tor['hip'][1])
    hd = C['head']; hk_ = 1.0
    if face is not None:
        FL = HK.L('pss_' + face[0]); hk_ = FL.w / float(hd['L'].w); hdn = (hd['neck'][0] * hk_, hd['neck'][1] * hk_)
    else: hdn = hd['neck']
    Th = Tt @ M3(tor['neck'][0], tor['neck'][1], 1.0 / hk_, 1.0 / hk_, head + 2.0 * math.sin(2 * ph + 0.8) * walk - ln * 0.6 + 1.2 * math.sin(t * 1.3 + ph0), hdn[0], hdn[1])

    def leg_draw(side, tn):
        th, kn, toe, _ = G[side]; kk = dict(gain=gain, tint=mul_t(tint, tn))
        T0 = root @ M3(0, 0, 1, 1, th, hp[0], hp[1]); T1 = T0 @ M3(kx, ky, 1, 1, kn, kx, ky)
        place_skin(cv, leg['L'], [T0, T1], [(kx, ky)], (0.0, 1.0), 24, **kk)
        roll = -(th + kn) * 0.93 + toe
        place(cv, shoe['L'], T1 @ M3(ax, ay, SK, SK, roll, shoe['ank'][0], shoe['ank'][1]), **kk)

    def arm_draw(nm, side, tn):
        a = C[nm]; p = ph + (math.pi if side == 'far' else 0.0); sn = math.sin(p)
        ang_s = (22.0 * sn * walk + 4.0 + arms[0]); ang_e = -(14.0 + 24.0 * max(0.0, -sn) * walk + arms[1])
        T0 = Tt @ M3(tor['sho'][0], tor['sho'][1], 1, 1, ang_s, a['sh'][0], a['sh'][1]); ex, ey = a['el']; T1 = T0 @ M3(ex, ey, 1, 1, ang_e, ex, ey)
        place_skin(cv, a['L'], [T0, T1], [(ex, ey)], (0.0, 1.0), 20, gain=gain, tint=mul_t(tint, tn))

    arm_draw('arm_b', 'far', far_tint); leg_draw('far', far_tint); leg_draw('near', None)
    place(cv, tor['L'], Tt, gain=gain, tint=tint)
    if face is None: place(cv, hd['L'], Th, gain=gain, tint=tint)
    else:
        place(cv, FL, Th, gain=gain, tint=tint)
        if face[2] > 0.01 and face[1] != face[0]: place(cv, HK.L('pss_' + face[1]), Th, alpha=face[2], gain=gain, tint=tint)
    arm_draw('arm_a', 'near', None)
    return G
