"""KEYFRAME RIG (v8). Each pose is a high-res painted RGBA keyframe of the SAME character (reference-locked AI paintings, keyed by prepare_mx.py, all in one 1216x875 frame so poses register).
In-betweens: DIS optical flow (premultiplied RGBA, forward/backward warp + blend) -> real inbetweens instead of dissolves.  Walk cycle A -> P -> B -> P2 -> A.  Pose graph = any pair can be morphed."""
import cv2, numpy as np, os
from engine import *
AX, AY = 620.0, 862.0           # ground anchor of the full-body frames (between the feet)
_img, _flow = {}, {}
_dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM); _dis.setFinestScale(0); _dis.setPatchSize(12); _dis.setPatchStride(4); _dis.setVariationalRefinementIterations(8)


def img(nm):
    if nm.endswith('_reg'): return reg(nm[:-4])
    if nm not in _img:
        im = cv2.imread(os.path.join(LAY, f'mx_{nm}.png'), cv2.IMREAD_UNCHANGED).astype(np.float32); a = im[..., 3:] / 255.0
        im[..., :3] *= a; im[..., 3:] = a; _img[nm] = im
    return _img[nm]


REG = {'bust_shock': ((623.0, 238.0), (601.0, 270.0), 1.25)}     # painted at a slightly different framing: eyes+scale registered onto the worried bust


def reg(nm):
    k = nm + '_reg'
    if k not in _img:
        (ex, ey), (tx, ty), s = REG[nm]; im = img(nm)
        M = np.float32([[s, 0, tx - s * ex], [0, s, ty - s * ey]])
        _img[k] = cv2.warpAffine(im, M, (im.shape[1], im.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
    return _img[k]


def _gray(im): return cv2.cvtColor(np.clip(im[..., :3] + (1 - im[..., 3:]) * 128, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)


def flow(a, b):
    k = (a, b)
    if k not in _flow:
        ga, gb = _gray(img(a)), _gray(img(b)); _flow[k] = _dis.calc(ga, gb, None)
    return _flow[k]


_mc = {}
def morph(a, b, t):
    """in-between of pose a -> b at t in 0..1 (cached on a 1/24 grid)"""
    t = round(clamp(t) * 24) / 24.0
    if t <= 0: return img(a)
    if t >= 1: return img(b)
    k = (a, b, t)
    if k in _mc: return _mc[k]
    if len(_mc) > 28: _mc.pop(next(iter(_mc)))
    Ia, Ib = img(a), img(b); Fab, Fba = flow(a, b), flow(b, a)
    h, w = Ia.shape[:2]; gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    # backward warping with the opposite flow field (flow fields are smooth, so this is a good approximation)
    wa = cv2.remap(Ia, gx - t * (-Fba[..., 0]), gy - t * (-Fba[..., 1]), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    wb = cv2.remap(Ib, gx - (1 - t) * (-Fab[..., 0]), gy - (1 - t) * (-Fab[..., 1]), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    out = wa * (1 - t) + wb * t
    # no half-transparent ghosts: where one side has no body and the other does, show the nearer pose
    aa, ab = wa[..., 3:], wb[..., 3:]; mis = (np.abs(aa - ab) > 0.45).astype(np.float32); mis = cv2.GaussianBlur(mis, (0, 0), 1.2)[..., None]
    near = wa if t < 0.5 else wb
    out = out * (1 - mis) + near * mis
    _mc[k] = out; return out


def layer_of(arr): return Layer.from_array(arr)


WALK = ['walk_A', 'walk_P', 'walk_B', 'walk_P2']


def walk_pose(phase):
    """phase in cycles (0..1 = A,P,B,P2,A): returns the morphed RGBA"""
    p = (phase % 1.0) * 4; i = int(p) % 4; u = p - int(p)
    return morph(WALK[i], WALK[(i + 1) % 4], sstep(u) * 0.35 + u * 0.65)


def draw_kf(cv, arr, X, gy, k, flip=1, rot=0.0, sy=1.0, alpha=1.0, ax=AX, ay=AY):
    """arr anchor (ax,ay) lands at (X,gy); k = screen px per source px"""
    place(cv, layer_of(arr), M3(X, gy, k * flip, k * sy, rot, ax, ay), alpha=alpha)
