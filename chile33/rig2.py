"""RIG v2 - gap-free limbs. Arms (upper arm + forearm) and legs (thigh / shin / foot) are drawn as ONE skinned image each: every output pixel is sampled from the rest-pose painting
through a smooth blend of the bone transforms (linear-blend skinning, done per pixel with cv2.remap), so elbows/knees/ankles bend like flesh instead of two rigid cut-outs that open a gap.
Everything else (head, torso, shadows, tint, camera) is the same layered system as hook_scenes.draw_char - the painted look is unchanged."""
import cv2, math, numpy as np
import hook_scenes as HK
from hook_scenes import *

KNEE = {'leg_l': (80, 238), 'leg_r': (82, 238)}      # layer coords of knee / ankle centres (leg layers are 176x517 / 194x511)
ANKLE = {'leg_l': (88, 402), 'leg_r': (88, 398)}


def smooth(x): x = np.clip(x, 0.0, 1.0); return x * x * (3 - 2 * x)


def place_skin(cv, layer, Ts, joints, axis, hw, gain=1.0, tint=None, alpha=1.0):
    """layer: premultiplied BGRA canvas; Ts: canvas->screen matrices per bone (root-most first); joints: canvas points between consecutive bones; axis: unit vector (canvas) pointing root->tip; hw: blend half width (canvas px)"""
    pts = np.array([[0, 0, 1], [layer.w, 0, 1], [layer.w, layer.h, 1], [0, layer.h, 1]], np.float64)
    allp = np.vstack([pts @ T.T for T in Ts]); pad = 4
    x0 = int(max(0, math.floor(allp[:, 0].min()) - pad)); x1 = int(min(W, math.ceil(allp[:, 0].max()) + pad))
    y0 = int(max(0, math.floor(allp[:, 1].min()) - pad)); y1 = int(min(H, math.ceil(allp[:, 1].max()) + pad))
    if x1 <= x0 or y1 <= y0: return
    gx, gy = np.meshgrid(np.arange(x0, x1, dtype=np.float32) + 0.5, np.arange(y0, y1, dtype=np.float32) + 0.5)
    R = []
    for T in Ts:
        Ti = np.linalg.inv(T)
        R.append((Ti[0, 0] * gx + Ti[0, 1] * gy + Ti[0, 2], Ti[1, 0] * gx + Ti[1, 1] * gy + Ti[1, 2]))
    n = len(Ts); sj = [j[0] * axis[0] + j[1] * axis[1] for j in joints]
    mid = R[min(1, n - 1)]; rx, ry = mid
    for _ in range(3):
        s = rx * axis[0] + ry * axis[1]
        c = [smooth((s - sj[k]) / (2 * hw) + 0.5) for k in range(n - 1)]
        Wt = [1 - c[0]] + [c[k] * (1 - c[k + 1]) for k in range(n - 2)] + [c[n - 2]]
        rx = sum(Wt[k] * R[k][0] for k in range(n)); ry = sum(Wt[k] * R[k][1] for k in range(n))
    wp = cv2.remap(layer.img, rx.astype(np.float32), ry.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    col = wp[..., :3] * gain
    if tint is not None: col = col * np.asarray(tint, np.float32)
    roi = cv[y0:y1, x0:x1]; a = wp[..., 3:] * alpha; roi *= (1 - a); roi += col * alpha


_arm = {}
def arm_canvas(ch, side):
    """upper arm + forearm joined at the elbow in rest pose -> one Layer, plus coords of shoulder/elbow in canvas space"""
    key = (ch, side)
    if key in _arm: return _arm[key]
    an, fn = f'arm_{side}', f'fore_{side}'; A, F = HK.L(f'{ch}_{an}'), HK.L(f'{ch}_{fn}')
    elb_s, fp_s, piv = ((222, 452), (226, 472), (221, 275)) if side == 'l' else ((800, 458), (806, 468), (797, 278))
    aoff, foff = HK.OFFS[ch][an], HK.OFFS[ch][fn]
    elb = (elb_s[0] - aoff[0], elb_s[1] - aoff[1]); fp = (fp_s[0] - foff[0], fp_s[1] - foff[1])
    fx, fy = elb[0] - fp[0], elb[1] - fp[1]                      # forearm layer origin in arm-layer coords
    ox, oy = min(0, fx) - 6, min(0, fy) - 6
    cw = int(max(A.w, fx + F.w) - ox + 6); chh = int(max(A.h, fy + F.h) - oy + 6)
    buf = np.zeros((chh, cw, 4), np.float32)
    def over(L, x, y):
        x = int(round(x - ox)); y = int(round(y - oy)); roi = buf[y:y + L.h, x:x + L.w]; roi[:] = L.img + roi * (1 - L.img[..., 3:])
    over(F, fx, fy); over(A, 0, 0)
    d = {'canvas': Layer.from_array(buf), 'org': (ox, oy), 'elb': (elb[0] - ox, elb[1] - oy), 'sh': (piv[0] - aoff[0] - ox, piv[1] - aoff[1] - oy), 'fp': (fp[0] + fx - ox, fp[1] + fy - oy), 'hand': (F.w * 0.5 + fx - ox, F.h * 0.92 + fy - oy)}
    _arm[key] = d; return d


def draw_char2(cv, ch, t, X, gy, sc, walk=0.0, ph0=0.0, pose=None, mouth=0.0, flip=1, gain=1.0, tint=None, crouch=0.0, legstyle='front', face=None, sway_amp=1.0, shirt=None, pants=None, hs=1.0, rot=0.0, dy=0.0, stride=1.0):
    P = pose or {}; R = HK.RIG[ch]
    Ls = {k: HK.L(f'{ch}_{k}') for k in ('head', 'torso', 'leg_l', 'leg_r', 'fore_l', 'fore_r')}; Ls_ = Ls
    ph = 2 * math.pi * 1.1 * t + ph0
    bob = abs(math.sin(ph)) * 7 * walk; sway = math.sin(ph) * 2.0 * walk * sway_amp
    breath = 0.012 * math.sin(t * 2.2 + ph0)
    sy = sc * (1 - 0.12 * crouch)
    root = M3(X, gy - 497 * sy + dy, sc * flip, sy, sway * 0.5 + P.get('lean', 0) * 0.4 + rot, HIPS[0], HIPS[1]) @ M3(0, -bob, 1, 1, 0, 0, 0)
    HK.shadow(cv, X, gy, sc)
    def mul(a, b): return a if b is None else (b if a is None else tuple(x * y for x, y in zip(a, b)))
    kw = dict(gain=gain, tint=tint); kws = dict(gain=gain, tint=mul(tint, shirt)); kwp = dict(gain=gain, tint=mul(tint, pants))
    # legs: hip swing + knee flex on the lifted leg + ankle counter-rotation so the shoe stays level
    for side, name, sock, piv in (('l', 'leg_l', (468, 640), (1025, 225)), ('r', 'leg_r', (558, 640), (1253, 230))):
        sg = 1 if side == 'l' else -1; s = math.sin(ph) * sg
        ox, oy = HK.OFFS[ch][name]; pv = (piv[0] - ox, piv[1] - oy); kx, ky = KNEE[name]; ax, ay = ANKLE[name]
        if legstyle == 'front' and walk > 0:
            # front-view walk (the art is a front drawing): legs never scissor sideways; the swing leg comes TOWARD the camera, so the thigh/shin FORESHORTEN
            # (knee rises, shin folds back, foot grows slightly) and the push-off leg lengthens its heel. Planted leg stays under the body.
            lf = max(0.0, -s) ** 0.9 * walk; pk = max(0.0, s - 0.45) / 0.55 * walk
            th = 3.0 * sg * lf * stride + P.get('legs', 0) * sg
            T0 = root @ M3(sock[0], sock[1], 1, 1 - 0.075 * lf * stride, th, pv[0], pv[1])
            T1 = T0 @ M3(kx, ky - 6 * lf * stride, 1, 1 - 0.40 * lf ** 1.15 * stride - 0.07 * pk, -3.5 * sg * lf, kx, ky)
            T2 = T1 @ M3(ax, ay, 1 + 0.07 * lf, 1 + 0.10 * lf - 0.22 * pk, 3.5 * sg * lf, ax, ay)
            place_skin(cv, Ls[name], [T0, T1, T2], [(kx, ky), (ax, ay)], (0.0, 1.0), 38, **kwp); continue
        th = (18 * stride * s) * walk + (2 if side == 'l' else -2) * (1 - walk) * math.sin(t * 0.8 + ph0) + P.get('legs', 0) * sg
        lift = max(0.0, -s) if walk > 0 else 0.0
        kn = (26 * lift ** 0.8) * walk * stride + P.get('knee', 0)
        an_ = -(th + kn) * 0.9
        T0 = root @ M3(sock[0], sock[1], 1, 1, th, pv[0], pv[1])
        T1 = T0 @ M3(kx, ky, 1, 1, -kn, kx, ky); T2 = T1 @ M3(ax, ay, 1, 1, an_, ax, ay)
        place_skin(cv, Ls[name], [T0, T1, T2], [(kx, ky), (ax, ay)], (0.0, 1.0), 38, **kwp)
    TF = root @ M3(HIPS[0], HIPS[1], 1, 1 + breath, sway * 0.6 + P.get('lean', 0), HIPS[0], HIPS[1])
    hn = 2.0 * math.sin(t * 1.7 + ph0) + 2.0 * math.sin(ph) * walk + P.get('head', 0.0)
    ox_, oy_ = HK.OFFS[ch]['head']; HM = TF @ M3(R['sock'][0], R['sock'][1], hs, hs, hn, R['piv'][0] - ox_, R['piv'][1] - oy_)
    if face is not None:
        # expression heads: hi-res AI repaints of the same head (ph_<name>.png), cross-faded; face=(nameA, nameB, mix)
        fa, fb, fm = face; LA = HK.L('ph_' + fa); kx_ = LA.w / float(Ls['head'].w); ky_ = LA.h / float(Ls['head'].h)
        HF = TF @ M3(R['sock'][0], R['sock'][1], hs / kx_, hs / ky_, hn, (R['piv'][0] - ox_) * kx_, (R['piv'][1] - oy_) * ky_)
        place(cv, LA, HF, **kw)
        if fm > 0.01 and fb != fa: place(cv, HK.L('ph_' + fb), HF, alpha=fm, **kw)
        mouth = 0.0
    else:
        place(cv, neck_patch(ch), TF @ M3(R['sock'][0], R['sock'][1] + 6, 1, 1, 0, 42, 50), **kws)
        place(cv, Ls['head'], HM, **kw)
    if mouth > 0.02:
        ml = HK.mouth_layer(ch); mo = 0.08 + 0.92 * mouth; ox, oy = HK.OFFS[ch]['head']
        place(cv, ml, HM @ M3(R['mouth'][0] - ox, R['mouth'][1] - oy, 0.64, 0.5 * mo, 0, ml.w / 2, ml.h * 0.42), **kw)
    tox, toy = HK.OFFS[ch]['torso']; place(cv, Ls['torso'], TF @ M3(tox, toy, 1, 1, 0, 0, 0), **kws)
    sw = 8 * walk * math.sin(ph)
    for side, an, fn, sock, piv, elb_s, fp_s in (('l', 'arm_l', 'fore_l', (388, 338), (221, 275), (222, 452), (226, 472)), ('r', 'arm_r', 'fore_r', (638, 338), (797, 278), (800, 458), (806, 468))):
        aoff, foff = HK.OFFS[ch][an], HK.OFFS[ch][fn]
        elb = (elb_s[0] - aoff[0], elb_s[1] - aoff[1]); fp = (fp_s[0] - foff[0], fp_s[1] - foff[1])
        if side == 'l':
            raise_a = 3 + 2 * math.sin(t * 1.1 + 1 + ph0) + P.get('aL', 0.0); raise_f = 4 + 4 * math.sin(t * 1.5 + ph0) + 14 * walk * max(0, math.sin(ph + 1.2)) + P.get('fL', 0.0)
            a_t = raise_a + sw; f_t = raise_f
        else:
            raise_a = 3 + 2 * math.sin(t * 1.3 + ph0) + P.get('aR', 0.0); raise_f = 6 * math.sin(t * 1.9 + ph0) + 8 * walk * max(0, math.sin(ph + 4.0)) + P.get('fR', 0.0)
            a_t = -raise_a + sw; f_t = -raise_f
        A = HK.pm(TF, ch, an, sock, piv, a_t)
        Fm = A @ M3(elb[0], elb[1] - 24, 1, 1, f_t, fp[0], fp[1])
        HK.LASTHAND[(ch, side)] = pt_(Fm, Ls_[fn].w * 0.5, Ls_[fn].h * 0.92)
        place(cv, Ls_[fn], Fm, **kw)
        ar = HK.L(f'{ch}_{an}'); capA = joint_cap(ch, an, elb, 'elbow')
        sh_l = (piv[0] - aoff[0], piv[1] - aoff[1])
        kwa = kw if (ch in HK.BARE_ARMS or shirt is None) else kws
        place(cv, ar, A, **kwa)
        # elbow cap follows the bisector of the bend -> no gap on the outer side of the elbow at any angle
        r = capA.w / 2.0
        ca = sstep((abs(f_t) - 8.0) / 28.0)
        if ca > 0.02: place(cv, capA, A @ M3(elb[0], elb[1] - 2, 1, 1, f_t * 0.5, r, r), alpha=ca, **kwa)
    HK.face_mark(cv, HM, ch, sc * hs)
    return HM


_cap = {}
def joint_cap(ch, name, pt, kind):
    """round patch of the limb's own painted skin (taken from just inside the limb) used as a ball joint; radius = half of the limb width there"""
    key = (ch, name, kind)
    if key in _cap: return _cap[key]
    Ly = HK.L(f'{ch}_{name}'); im = Ly.img; al = im[..., 3]
    y_ref = int(np.clip(pt[1] - (22 if kind == 'elbow' else -22), 4, Ly.h - 5)); row = np.where(al[y_ref] > 0.5)[0]
    wdt = (row.max() - row.min()) if len(row) > 3 else 60; cxr = (row.max() + row.min()) / 2.0 if len(row) > 3 else pt[0]
    Lf = HK.L(f'{ch}_' + name.replace('arm', 'fore')); rf = np.where(Lf.img[14, :, 3] > 0.5)[0]; wf = (rf.max() - rf.min()) if len(rf) > 3 else wdt
    r = int(max(12, min(wdt, wf) * 0.5 * 0.9))
    sy = int(np.clip(pt[1] + (-r * 0.7 if kind == 'elbow' else r * 0.7), r, Ly.h - r - 1)); sx = int(np.clip(cxr, r, Ly.w - r - 1))
    patch = im[sy - r:sy + r, sx - r:sx + r].copy()
    m = np.zeros(patch.shape[:2], np.float32); cv2.circle(m, (r, r), r - 2, 1.0, -1, cv2.LINE_AA); m = cv2.GaussianBlur(m, (0, 0), 1.6)
    amin = np.minimum(patch[..., 3], 1.0)
    patch = patch * m[..., None]; patch[..., 3] = np.maximum(patch[..., 3], 0) * 0 + m * (patch[..., 3] > 0.5)   # solid disc where the source had paint
    patch[..., 3] = m
    # fill colours of transparent source pixels with the mean skin so the disc is fully opaque
    mean = (im[..., :3] * (al[..., None] > 0.9)).reshape(-1, 3).sum(0) / max(1.0, (al > 0.9).sum())
    sol = (amin > 0.9)[..., None]
    patch[..., :3] = np.where(sol, patch[..., :3], mean * m[..., None]); 
    _cap[key] = Layer.from_array(patch); return _cap[key]


_neck = {}
def neck_patch(ch):
    """skin-coloured, vertically shaded ellipse behind the head: fills the open V of the collar under the chin (visible in close-ups)"""
    if ch in _neck: return _neck[ch]
    Ly = HK.L(f'{ch}_head'); im = Ly.img; al = im[..., 3]; h, w = al.shape
    ys, xs = np.where(al > 0.9); y0 = ys.max(); cx = int(np.median(xs))
    reg = im[int(y0 - 70):int(y0 - 25), cx - 25:cx + 25]; a = reg[..., 3:4]
    col = (reg[..., :3].reshape(-1, 3) * a.reshape(-1, 1)).sum(0) / max(1e-3, a.sum()) * 1.0
    ph, pw = 134, 84; yy, xx = np.mgrid[0:ph, 0:pw].astype(np.float32)
    e = 1 - np.clip((((xx - pw / 2) / (pw / 2)) ** 2 + ((yy - ph / 2) / (ph / 2)) ** 2 - 0.6) / 0.4, 0, 1)
    sh = (1.0 - 0.22 * (yy / ph))[..., None]
    out = np.dstack([col[None, None, :] * sh * e[..., None], e]).astype(np.float32)   # premultiplied
    _neck[ch] = Layer.from_array(out); return _neck[ch]
