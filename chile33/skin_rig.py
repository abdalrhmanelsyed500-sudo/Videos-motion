"""REAL ANIMATION of a painted keyframe: linear-blend skinning (bones + smooth weights) on the high-res painted RGBA.  Every limb/torso/head really moves (rotation, foreshortening, translation) while
the painting stays one consistent image.  Rest pose = painted idle figure.  Skinning is evaluated on a half-res grid; the inverse map is found by fixed-point iteration; the painting is sampled once (no repeated resampling)."""
import cv2, numpy as np, math, os
from engine import LAY

PAD = 40


class Skin:
    def __init__(self, nm, bones, s=11.0, hres=2):
        im = cv2.imread(os.path.join(LAY, f'mx_{nm}.png'), cv2.IMREAD_UNCHANGED).astype(np.float32); a = im[..., 3:] / 255.0
        im[..., :3] *= a; im[..., 3:] = a; self.full = im; H, W = im.shape[:2]
        ys, xs = np.where(a[..., 0] > 0.02); self.x0 = max(0, xs.min() - PAD); self.x1 = min(W, xs.max() + PAD); self.y0 = max(0, ys.min() - PAD); self.y1 = min(H, ys.max() + PAD)
        self.img = im[self.y0:self.y1, self.x0:self.x1].copy(); self.h, self.w = self.img.shape[:2]; self.k = hres
        self.names = list(bones.keys()); self.bones = bones
        gh, gw = self.h // hres, self.w // hres
        gy, gx = np.mgrid[0:gh, 0:gw].astype(np.float32); self.gx = gx * hres + self.x0; self.gy = gy * hres + self.y0     # rest-pose coordinates of the grid (full-frame coords)
        d = []
        for nmb in self.names:
            b = bones[nmb]; p0 = np.array(b['j'], np.float32); p1 = np.array(b['t'], np.float32); v = p1 - p0; L2 = float(v @ v) + 1e-6
            u = np.clip(((self.gx - p0[0]) * v[0] + (self.gy - p0[1]) * v[1]) / L2, 0, 1)
            dd = np.hypot(self.gx - (p0[0] + u * v[0]), self.gy - (p0[1] + u * v[1])); d.append(np.maximum(dd - b['r'], 0))
        d = np.stack(d); w = np.exp(-(d / s) ** 2) + 1e-6; self.W = (w / w.sum(0, keepdims=True)).astype(np.float32)
        # soft mask: weights are only used where there is paint; smooth them a little to avoid steps
        self.W = np.stack([cv2.GaussianBlur(x, (0, 0), 1.5) for x in self.W]); self.W /= self.W.sum(0, keepdims=True)
        gx_, gy_ = np.meshgrid(np.arange(self.w, dtype=np.float32), np.arange(self.h, dtype=np.float32)); self.fx, self.fy = gx_, gy_

    @staticmethod
    def _m(j, rot=0.0, sa=1.0, sp=1.0, ax=(0.0, 1.0), tx=0.0, ty=0.0):
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot)); R = np.array([[c, -s], [s, c]])
        u = np.array(ax, float); u /= np.linalg.norm(u); v = np.array([-u[1], u[0]]); A = sa * np.outer(u, u) + sp * np.outer(v, v)
        L = R @ A; M = np.eye(3); M[:2, :2] = L; jj = np.array(j, float); M[:2, 2] = jj - L @ jj + np.array([tx, ty]); return M

    def world(self, pose):
        Wd = {}
        for nm in self.names:                                  # bones are listed parents-first
            b = self.bones[nm]; p = pose.get(nm, {}); ax = np.array(b['t'], float) - np.array(b['j'], float)
            Lm = self._m(b['j'], p.get('rot', 0.0), p.get('sa', 1.0), p.get('sp', 1.0), ax, p.get('tx', 0.0), p.get('ty', 0.0))
            Wd[nm] = (Wd[b['p']] @ Lm) if b.get('p') else Lm
        return Wd

    def render(self, pose, out=None):
        """returns the full-frame premultiplied RGBA of the deformed painting"""
        Wd = self.world(pose); gx, gy = self.gx, self.gy; px = np.zeros_like(gx); py = np.zeros_like(gy)
        for i, nm in enumerate(self.names):
            M = Wd[nm]; w = self.W[i]; px += w * (M[0, 0] * gx + M[0, 1] * gy + M[0, 2]); py += w * (M[1, 0] * gx + M[1, 1] * gy + M[1, 2])
        Dx, Dy = px - gx, py - gy                                  # forward displacement of rest pixels (half-res grid)
        gh, gw = Dx.shape
        D = np.dstack([Dx, Dy]).astype(np.float32); Dfull = cv2.resize(D, (self.w, self.h), interpolation=cv2.INTER_LINEAR)
        # inverse: output pixel y comes from rest pixel x with x + D(x) = y   (fixed-point)
        X = self.fx.copy(); Y = self.fy.copy()
        for _ in range(7):
            dx = cv2.remap(Dfull[..., 0], X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE); dy = cv2.remap(Dfull[..., 1], X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            X = self.fx - dx; Y = self.fy - dy
        res = cv2.remap(self.img, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        m = (res[..., 3] > 0.12).astype(np.uint8); n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)    # drop detached specks
        bad = [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] < 220]
        if bad: res = res * (~np.isin(lab, bad))[..., None]
        if out is None: out = np.zeros_like(self.full)
        out[self.y0:self.y1, self.x0:self.x1] = res; return out


BODY = {   # idle painting: nearly frontal, legs straight and apart, arms hanging (coords in the 1216x875 frame)
    'pelvis': dict(j=(610, 520), t=(610, 565), r=70),
    'torso': dict(j=(610, 505), t=(610, 215), r=66, p='pelvis'),
    'head': dict(j=(612, 212), t=(612, 60), r=64, p='torso'),
    'armL_up': dict(j=(535, 240), t=(518, 375), r=26, p='torso'), 'armL_lo': dict(j=(518, 375), t=(525, 500), r=30, p='armL_up'),
    'armR_up': dict(j=(690, 240), t=(708, 375), r=26, p='torso'), 'armR_lo': dict(j=(708, 375), t=(708, 505), r=30, p='armR_up'),
    'thighL': dict(j=(565, 555), t=(565, 645), r=38, p='pelvis'), 'shinL': dict(j=(565, 645), t=(562, 785), r=32, p='thighL'), 'footL': dict(j=(562, 785), t=(552, 850), r=46, p='shinL'),
    'thighR': dict(j=(665, 555), t=(665, 645), r=38, p='pelvis'), 'shinR': dict(j=(665, 645), t=(665, 785), r=32, p='thighR'), 'footR': dict(j=(665, 785), t=(675, 850), r=46, p='shinR'),
}


def sm(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def leg_state(u):
    """u = gait phase of this leg 0..1: stance 0..0.6 (foot planted, moving backward under the body), swing 0.6..1 (lifted, knee flexed, coming forward). returns lift 0..1, depth offset px (+ = towards camera)"""
    if u < 0.6: return 0.0, 12 - 20 * (u / 0.6)
    q = (u - 0.6) / 0.4; return math.sin(math.pi * q), -8 + 20 * sm(q)


def walk_pose(phi, amp=1.0, lean=0.0):
    """phi in cycles. frontal walk: bob, hip sway/roll, counter-rotating shoulders, swing legs with foot lift + foreshortening, arms swinging in depth"""
    pose = {}; a = 2 * math.pi
    uL, uR = phi % 1.0, (phi + 0.5) % 1.0
    lL, dL = leg_state(uL); lR, dR = leg_state(uR)
    bob = -6.5 * amp * abs(math.cos(a * phi * 1.0 + 0.0)) ** 1.2 + 3 * amp
    sway = 13 * amp * math.sin(a * phi)                                 # weight shifts over the stance leg
    pose['pelvis'] = dict(tx=sway, ty=bob, rot=2.4 * amp * math.sin(a * phi + 0.4))
    pose['torso'] = dict(rot=-2.6 * amp * math.sin(a * phi + 0.4) + lean, tx=-0.4 * sway)
    pose['head'] = dict(rot=0.9 * amp * math.sin(a * phi + 0.4) * -1 + 1.2 * amp * math.sin(a * phi * 2 + 1.2))
    for sd, l, dd, u in (('L', lL, dL, uL), ('R', lR, dR, uR)):
        pose['thigh' + sd] = dict(ty=dd * 0.55 - 3 * l, sa=1.0 - 0.05 * l, rot=(-1 if sd == 'L' else 1) * 3.5 * amp * l)
        pose['shin' + sd] = dict(ty=dd * 0.45 - 17 * l * amp, sa=1.0 - 0.22 * l * amp, rot=(1 if sd == 'L' else -1) * 4 * l)
        pose['foot' + sd] = dict(rot=-10 * l * (1 if sd == 'L' else -1) * 0 + 14 * l - 6 * (1 - l) * (1 if u < 0.2 else 0), sa=1.0 - 0.1 * l)
    # arms swing opposite to the same-side leg (depth: foreshortening + small in-plane swing)
    for sd, other in (('L', uR), ('R', uL)):
        s = math.sin(a * other); sg = 1 if sd == 'L' else -1
        pose['arm' + sd + '_up'] = dict(rot=sg * -5.0 * amp * (0.5 + 0.5 * s) + sg * 4.5 * s * amp, sa=1.0 - 0.07 * s)
        pose['arm' + sd + '_lo'] = dict(rot=sg * -(6 + 14 * max(s, 0)) * amp, sa=1.0 - 0.10 * max(s, 0))
    return pose


BUST = {   # painted close-up (worried / shock, registered): chest+shoulders, head (+cap), neck-cloth flap with follow-through
    'body': dict(j=(520, 870), t=(520, 700), r=330),
    'head': dict(j=(520, 670), t=(560, 300), r=205, p='body'),
    'flap': dict(j=(390, 330), t=(335, 610), r=70, p='head'),
}
