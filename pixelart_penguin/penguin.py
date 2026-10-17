"""Penguin commando with AKM -- 3D model (SDF primitives) + pose system + pixel-art finishing."""
import numpy as np
from sdf3d import *
from sdf3d import PART_ID

import os
STYLE = os.environ.get('PENGUIN_STYLE', 'classic')      # 'classic', 'lackey' (palette/shading of the reference sheet) or 'pear' (cartoon pear-shaped penguin, flat lackey rendering)
FLAT = STYLE in ('lackey', 'pear'); PEAR = STYLE == 'pear'
def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
RAMPS_CLASSIC = {
 'body':  ['#090c16', '#182038', '#2b3858', '#455a85', '#7088b8'],
 'flip':  ['#0a0e1c', '#1c2844', '#31436a', '#4f6a9c', '#82a0cf'],
 'belly': ['#38425f', '#8794b6', '#cfd7ea', '#eef2fa', '#ffffff'],
 'orange':['#4a1a14', '#a8431a', '#f27a1d', '#ffae3b', '#ffe08a'],
 'red':   ['#32081a', '#781628', '#c4283a', '#ec5a52', '#ff9c8c'],
 'olive': ['#161d10', '#2b371c', '#475a2d', '#6c8243', '#9db468'],
 'metal': ['#0b0d12', '#242a35', '#485164', '#7a8599', '#c3cddb'],
 'wood':  ['#240d07', '#58270f', '#8c4520', '#bd6d33', '#eaa45c'],
 'brass': ['#46290a', '#8a5a14', '#d9a21e', '#f7d65a', '#fff3b0'],
 'pupil': ['#05060a', '#05060a', '#0c0f18', '#1a2033', '#2b3858'],
 'flash': ['#8a2a10', '#ff7a1a', '#ffc83a', '#fff0a0', '#ffffff'],
 'blood': ['#26050f', '#5a0e1c', '#8c1826', '#c2283a', '#e8505a'],
 'hurt':  ['#6a1428', '#d8484f', '#ff948c', '#ffd4cc', '#ffffff'],
 'eyew':  ['#38425f', '#8794b6', '#cfd7ea', '#eef2fa', '#ffffff'],
}
# palette sampled from the reference sheet (G.P. Lackey): indigo-black, plum, wine, rose, tan, cream, sage, teal
RAMPS_LACKEY = {
 'body':  ['#13022d', '#13022d', '#452547', '#62366a', '#62366a'],
 'flip':  ['#13022d', '#452547', '#62366a', '#886e9a', '#886e9a'],
 'belly': ['#925758', '#be9890', '#decfba', '#f7f7e8', '#f7f7e8'],
 'orange':['#823454', '#925758', '#be9890', '#decfba', '#f7f7e8'],
 'red':   ['#13022d', '#3e2b38', '#823454', '#925758', '#be9890'],
 'olive': ['#13022d', '#3d3a4e', '#6c7368', '#859580', '#859580'],
 'metal': ['#13022d', '#3d3a4e', '#554f61', '#886e9a', '#f7f7e8'],
 'wood':  ['#13022d', '#3e2b38', '#925758', '#be9890', '#decfba'],
 'brass': ['#925758', '#be9890', '#decfba', '#f7f7e8', '#f9f6f4'],
 'pupil': ['#13022d', '#13022d', '#13022d', '#13022d', '#13022d'],
 'flash': ['#823454', '#925758', '#decfba', '#f7f7e8', '#f9f6f4'],
 'blood': ['#3e2b38', '#823454', '#823454', '#925758', '#be9890'],
 'hurt':  ['#823454', '#be9890', '#decfba', '#f7f7e8', '#f9f6f4'],
 'eyew':  ['#f7f7e8', '#f7f7e8', '#f7f7e8', '#f7f7e8', '#f9f6f4'],
}
# cartoon black/white/orange pear penguin (shape reference: the 'Madagascar' penguins), flat 3-tone, no outlines
RAMPS_PEAR = dict(RAMPS_LACKEY)
RAMPS_PEAR.update({
 'body':  ['#0a0d15', '#0a0d15', '#1b2231', '#2d3649', '#2d3649'],
 'flip':  ['#0a0d15', '#1b2231', '#2d3649', '#4b5972', '#4b5972'],
 'belly': ['#76878a', '#a9b9b4', '#d9e3dc', '#f3f7f0', '#f3f7f0'],
 'orange':['#7a2c12', '#b8481a', '#e8731c', '#ff9f3a', '#ffc46a'],
 'metal': ['#0a0d15', '#2a303c', '#4b5262', '#7c8596', '#c3cad6'],
 'wood':  ['#1c0c06', '#4e2410', '#84451f', '#b36832', '#d9965a'],
 'eyew':  ['#ffffff'] * 5,
 'pupil': ['#05060a'] * 5,
 'socket':['#3a4458', '#3a4458', '#3a4458', '#3a4458', '#3a4458'],
 'flash': ['#8a2a10', '#ff7a1a', '#ffc83a', '#fff0a0', '#ffffff'],
 'blood': ['#26050f', '#5a0e1c', '#8c1826', '#c2283a', '#e8505a'],
 'hurt':  ['#6a1428', '#e0525a', '#ff9c94', '#ffd8d0', '#ffffff'],
})
TEAL = (0x75, 0xa0, 0x94)
RAMPS = RAMPS_PEAR if PEAR else RAMPS_LACKEY if STYLE == 'lackey' else RAMPS_CLASSIC
NAMES = list(RAMPS); IDX = {n: i for i, n in enumerate(NAMES)}
RAMP_RGB = [[hexrgb(h) for h in RAMPS[n]] for n in NAMES]
M = lambda n: IDX[n]
SHADOW_RGBA = (10, 12, 24, 84)

# ---- material functions (get local coordinates inside the primitive's frame and the local normal)
def belly_fn(q, n):   # white belly on the front of the body, black on the sides/back
    z = q[:, 2] / 9.0; y = (q[:, 1]) / 12.0; x = q[:, 0] / 10.5
    white = (z > .20 + .55 * x ** 2) & (y < .72)
    return np.where(white, M('belly'), M('body'))
def pear_body_fn(q, n):
    x = q[:, 0] / 10.6; z = q[:, 2] / 9.6
    return np.where(z > .02 + .55 * x ** 2, M('belly'), M('body'))
def pear_head_fn(q, n):     # black cap down to the eyes, white face below, cap wraps down the sides/back
    x = q[:, 0] / 7.6; z = q[:, 2] / 7.6
    white = (z > .05 + .9 * x ** 2) & (q[:, 1] < 2.6 - 3.2 * x ** 2)
    return np.where(white, M('belly'), M('body'))
def flipper_fn(q, n): return np.full(len(q), M('body'))

# ---- geometry constants (penguin local, feet on y=0, forward +z)
SH = V(10.0, 16.5, 2.5); L1 = 11.0; L2 = 11.0
GRIP = V(0, -3.3, -4.2) * 0.82; FORE = V(0, -1.2, 7.4) * 0.82

def ik(S, T, pole, l1=L1, l2=L2):
    v = T - S; d = np.linalg.norm(v); dm = (l1 + l2) * .985
    if d > dm: T = S + v / d * dm; v = T - S; d = dm
    dirv = v / d; a = (l1 * l1 - l2 * l2 + d * d) / (2 * d); h = np.sqrt(max(l1 * l1 - a * a, 0))
    pp = pole - dirv * (pole @ dirv); pp = pp / (np.linalg.norm(pp) + 1e-9)
    return S + dirv * a + pp * h, T

def default_pose():
    return dict(bob=0., lean=0., roll=0., twist=0., off=(0., 0.), pivot=(0, 0, 0), head=(0., 0., 0.), hoff=(0., 0., 0.),
                fl=(-4.8, 0., 3.5), fr=(4.8, 0., 3.5), fl_pitch=0., fr_pitch=0., foot_yaw=(0., 0.),
                gun=dict(pos=(5.5, 13.5, 8.5), pitch=0., yaw=0., roll=0., parent='body'),
                lh=None, rh=None, lh_grip=FORE, rh_grip=GRIP,
                mag=dict(off=(0, 0, 0), pitch=0., vis=True, parent='gun', rootpos=(0, 0, 0)),
                mag2=None, bolt=0., band=(0., 0.), tail=0., flash=0., casing_ages=[], hurt=0., eyes='open', flip_pole=1.0,
                squash=1.0, blood=[], pool=0., shock=0.)

def build(pose, yaw_deg):
    p = pose; sc = Scene()
    Ry0 = Ry(D(yaw_deg)); root = local(Ry0, Ry0 @ V(p['off'][0], 0, p['off'][1]))
    Rb = Rz(D(p['roll'])) @ Rx(D(p['lean'])) @ Ry(D(p['twist']))
    body = root.comp(local(Rb, (0, p['bob'], 0), pivot=p['pivot']))
    # ---- feet (root frame, they stay on the ground)
    for side, key, pk, yk in ((-1, 'fl', 'fl_pitch', 0), (1, 'fr', 'fr_pitch', 1)):
        fx, fy, fz = p[key]; f = root.comp(local(Ry(D(p['foot_yaw'][yk])) @ Rx(D(p[pk])), (0, 0, 0)))
        fr_ = root.comp(local(Ry(D(p['foot_yaw'][yk])) @ Rx(D(p[pk])), (fx, fy + 1.4, fz), pivot=(0, 0, 0)))
        sc.ell(fr_, (0, 0, 2.6), (3.7, 1.6, 5.8), M('orange'), 'foot')
        sc.ell(fr_, (-1.8, 0, 5.5), (1.4, 1.1, 1.8), M('orange'), 'foot', group=None)
        sc.ell(fr_, (1.8, 0, 5.5), (1.4, 1.1, 1.8), M('orange'), 'foot', group=None)
    sq = p['squash']
    # ---- torso
    if PEAR:
        sc.ell(body, (0, 12.4, 0), (10.6, 12.4 * sq, 9.6), M('body'), 'body', group='torso', mat_fn=pear_body_fn)
        sc.ell(body, (0, 3.0, -9.0), (3.4, 1.8, 3.6), M('body'), 'tail', rot=Rx(D(18)))
        hp, hy, hr = p['head']; hoff = np.array(p['hoff'])
        head = body.comp(local(Rx(D(hp)) @ Ry(D(hy)) @ Rz(D(hr)), hoff, pivot=(0, 22.5, 0)))
        sc.ell(head, (0, 25.2, .6), (7.6, 9.0, 7.6), M('body'), 'head', group='torso', k=9.0, mat_fn=pear_head_fn)
        # big flat orange beak (upper + lower mandible)
        if not (Ry0 @ V(0, 0, 1))[2] > .7 or abs(p['lean']) >= 30:
            sc.ell(head, (0, 23.8, 8.6), (3.3, 1.1, 4.4), M('orange'), 'beak', rot=Rx(D(-12)))
            sc.ell(head, (0, 22.5, 7.9), (2.5, .8, 3.0), M('orange'), 'beak', rot=Rx(D(-4)))
        ex = 3.3
        fz = (Ry0 @ V(0, 0, 1))[2]
        away = fz > .7 and abs(p['lean']) < 30      # seen from behind: face is occluded by the head, skip it (avoids stray pixels over the silhouette)
        for sx in (-1, 1):
            if away: break
            sc.ell(head, (sx * ex, 27.7, 6.0), (3.0, 3.2, 2.0), M('socket'), 'socket', rot=Ry(D(sx * 18)))
            sc.ell(head, (sx * ex, 27.8, 6.4), (2.6, 2.9, 1.9), M('eyew'), 'eye', rot=Ry(D(sx * 18)))
            if p['eyes'] == 'open':     sc.ell(head, (sx * (ex - .5), 27.4, 8.0), (1.1, 1.4, 1.0), M('pupil'), 'pupil')
            elif p['eyes'] == 'closed': sc.ell(head, (sx * (ex - .2), 27.4, 7.8), (1.9, .6, .9), M('pupil'), 'pupil')
            elif p['eyes'] == 'wide':   sc.ell(head, (sx * (ex - .2), 27.8, 8.1), (1.0, 1.1, .8), M('pupil'), 'pupil')
    else:
        sc.ell(body, (0, 13.2, 0), (10.6, 12.2 * sq, 9.2), M('body'), 'body', group='torso', mat_fn=belly_fn)
        sc.ell(body, (0, 3.2, -9.0 + 0), (3.4, 1.8, 3.6), M('body'), 'tail', rot=Rx(D(18)))
        # vest
        sc.band(body, (0, 13.2, 0), (11.35, 12.8, 9.95), 11.2 - 13.2 + 1.0, 3.6, M('olive'), 'vest')
        sc.box(body, (-4.3, 10.9, 9.3), (2.4, 2.2, 1.3), M('olive'), 'pouch', rnd=.8)
        sc.box(body, (4.3, 10.9, 9.3), (2.4, 2.2, 1.3), M('olive'), 'pouch', rnd=.8)
        # ---- head
        hp, hy, hr = p['head']; hoff = np.array(p['hoff'])
        head = body.comp(local(Rx(D(hp)) @ Ry(D(hy)) @ Rz(D(hr)), hoff, pivot=(0, 22.5, 0)))
        sc.ell(head, (0, 26.5, 1.2), (9.6, 8.0, 9.2), M('body'), 'head', group='torso', k=4.5)
        # headband
        sc.band(head, (0, 26.5, 1.2), (10.25, 8.7, 9.8), 3.2, 1.15, M('red'), 'band')
        wv, am = p['band']
        for i, (sx) in enumerate((-1, 1)):
            a0 = V(sx * 1.0, 29.2, -8.0)
            b1 = a0 + V(sx * (2.2 + am * np.sin(wv)), -3.0 + am * .5 * np.sin(wv + 1), -3.2)
            b2 = b1 + V(sx * (1.2 + am * 1.2 * np.sin(wv + 1.4)), -3.6 + am * np.sin(wv + 2.2), -2.4)
            sc.cap(head, a0, b1, 1.15, 1.05, M('red'), 'bandtail'); sc.cap(head, b1, b2, 1.05, .7, M('red'), 'bandtail')
        # beak
        sc.cap(head, (0, 25.6, 8.4), (0, 24.6, 13.8), 2.5, .9, M('orange'), 'beak')
        sc.ell(head, (0, 24.1, 9.3), (1.9, .9, 3.4), M('orange'), 'beak')
        # eyes
        ex = 4.5
        for sx in (-1, 1):
            sc.ell(head, (sx * ex, 27.4, 9.0), (2.8, 3.0, 2.0), M('eyew'), 'eye', rot=Ry(D(sx * 22)))
            if p['eyes'] == 'open':
                sc.ell(head, (sx * (ex - .5), 27.0, 10.8), (1.15, 1.45, 1.0), M('pupil'), 'pupil')
            elif p['eyes'] == 'closed':
                sc.ell(head, (sx * (ex - .2), 27.0, 10.6), (1.9, .6, .9), M('pupil'), 'pupil')
            elif p['eyes'] == 'wide':
                sc.ell(head, (sx * (ex - .2), 27.4, 10.9), (1.0, 1.1, .8), M('pupil'), 'pupil')
    # ---- gun
    g = p['gun']
    gf_local = local(Ry(D(g['yaw'])) @ Rx(D(-g['pitch'])) @ Rz(D(g['roll'])), g['pos'])
    gfr = (body if g['parent'] == 'body' else root).comp(gf_local)
    build_gun(sc, gfr, p, body, root)
    # ---- flippers (IK to grips)
    for sx, key, grip in ((-1, 'lh', p['lh_grip']), (1, 'rh', p['rh_grip'])):
        S = V(sx * SH[0], SH[1], SH[2])
        tgt = p[key]
        if tgt is None: tgt = (gf_local.ap(grip) if g['parent'] == 'body' else body_inv_gun(body, gfr, grip))
        tgt = V(*tgt); pole = V(sx * .9, -.9, -.45 * p['flip_pole'])
        E, T = ik(S, tgt, pole)
        sc.cap(body, S, E, 3.1, 2.6, M('flip'), 'flipper')
        sc.cap(body, E, T, 2.6, 1.7, M('flip'), 'flipper')
        sc.ell(body, S, (3.5, 3.5, 3.5), M('flip'), 'flipper')
    return sc, root, body, gfr

def body_inv_gun(body, gfr, grip):    # grip point in world -> body frame
    w = gfr.ap(grip); return body.R.T @ (w - body.t)

GS = 0.82      # gun scale (keeps a 33 px long rifle inside a 64 px frame)
MAG_PTS = [V(0, -2.0, 2.2), V(0, -6.0, 2.8), V(0, -9.8, 4.6), V(0, -12.2, 7.0)]
PORT = V(2.0, 1.4, 1.0)

def build_gun(sc, f, p, body, root):
    W_, B_ = M('wood'), M('metal'); g = GS
    S = lambda *v: V(*v) * g
    box = lambda c, h, mat, part, rot=None, rnd=.4: sc.box(f, S(*c), tuple(np.array(h) * g), mat, part, rot=rot, rnd=rnd * g)
    cap = lambda a, b_, ra, rb, mat, part: sc.cap(f, S(*a), S(*b_), ra * g, rb * g, mat, part)
    box((0, 0, 0), (1.9, 2.2, 6.2), B_, 'gun', rnd=.7)                          # receiver
    box((0, 2.5, -.3), (1.6, .8, 5.8), B_, 'gun', rnd=.6)                       # dust cover
    box((0, 0.3, -12.0), (1.5, 2.3, 5.8), W_, 'stock', rot=Rx(D(7)), rnd=.8)    # stock
    box((0, 1.5, -17.3), (1.6, 3.1, .8), W_, 'stock', rot=Rx(D(7)), rnd=.5)     # butt plate
    cap((0, -1.8, -3.4), (0, -6.4, -4.8), 1.5, 1.3, W_, 'stock')                # pistol grip
    box((0, -.2, 9.4), (1.7, 1.7, 3.5), W_, 'gun', rnd=.7)                      # lower handguard
    box((0, 2.0, 9.6), (1.4, .85, 3.3), W_, 'gun', rnd=.4)                      # upper handguard
    cap((0, 3.0, 6.8), (0, 3.0, 14.5), .85, .85, B_, 'gun')                     # gas tube
    cap((0, .9, 6.5), (0, .9, 20.5), .85, .85, B_, 'gun')                       # barrel
    box((0, .9, 21.2), (1.25, 1.25, 1.2), B_, 'gun', rnd=.5)                    # muzzle brake
    box((0, 2.6, 19.0), (.35, 1.2, .4), B_, 'gun', rnd=.2)                      # front sight
    box((0, 3.5, -3.0), (.9, .5, .9), B_, 'gun', rnd=.2)                        # rear sight
    sc.ell(f, S(2.0, 1.1, 0.5 - p['bolt']), (.95 * g,) * 3, B_, 'gun')           # charging handle
    def mag(mf):
        for a_, b_, ra, rb in zip(MAG_PTS, MAG_PTS[1:], (1.9, 1.9, 1.8), (1.9, 1.8, 1.7)):
            sc.cap(mf, a_ * g, b_ * g, ra * g, rb * g, B_, 'mag')
    m = p['mag']
    if m['vis']:
        if m['parent'] == 'gun': mf = f.comp(local(Rx(D(-m['pitch'])), np.array(m['off']) * g))
        else: mf = root.comp(local(Rx(D(-m['pitch'])), m['rootpos']))
        mag(mf)
    if p.get('mag2'):
        m2 = p['mag2']; mag((body if m2['parent'] == 'body' else root).comp(local(Rx(D(-m2['pitch'])), m2['pos'])))
    for age in p['casing_ages']:
        v = f.R @ V(3.0, 2.6, -1.4); pos = f.ap(PORT * g) + v * age + V(0, -.55 * age * age, 0)
        pos[1] = max(pos[1], 0.9)
        sc.ell(Frame(), pos, (.65, .65, 1.15), M('brass'), 'casing', rot=Ry(D(70 * age)))

def muzzle_world(gfr): return gfr.ap(V(0, .9, 23.0) * GS)

# ---------------------------------------------------------------------------------------------- pixel finishing
def finish(r, p=None, flash=None, outline=True, sep=True, hurt=0.0):
    H, W = r['hit'].shape; hit = r['hit']; mat = r['mat'].copy(); lam = r['lam']; part = r['part']; dep = r['depth']
    th = (-.08, .28, .80, 9.0) if FLAT else (-.08, .34, .70, .92)
    if FLAT: outline = False; sep = False
    lvl = np.where(lam < th[1], 1, np.where(lam < th[2], 2, np.where(lam < th[3], 3, 4)))
    if hurt > 0: mat[hit] = M('hurt')
    rgb = np.zeros((H, W, 3), np.uint8)
    for y, x in zip(*np.where(hit)): rgb[y, x] = RAMP_RGB[mat[y, x]][lvl[y, x]]
    fill = hit.copy(); alpha = np.zeros((H, W), np.uint8); alpha[hit] = 255
    if sep:    # internal separation: far pixel next to a clearly nearer pixel of another part -> darkest tone of its own ramp
        dark = np.zeros((H, W), bool)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            sh = lambda a, fill_=0: np.roll(np.roll(a, dy, 0), dx, 1)
            nh = sh(hit); npart = sh(part); ndep = sh(dep)
            m = hit & nh & (npart != part) & (dep - ndep > 2.6)
            if dy == 1: m[0] = False
            if dy == -1: m[-1] = False
            if dx == 1: m[:, 0] = False
            if dx == -1: m[:, -1] = False
            dark |= m
        keepmask = ~np.isin(part, [PART_ID.get('tail', -9)])
        for y, x in zip(*np.where(dark & keepmask)):
            rgb[y, x] = RAMP_RGB[mat[y, x]][0] if hurt == 0 else RAMP_RGB[mat[y, x]][0]
    if outline:
        f = fill; o = np.zeros_like(f); src = np.zeros((H, W), int) - 1
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(np.roll(f, dy, 0), dx, 1); sm = np.roll(np.roll(mat, dy, 0), dx, 1)
            new = sh & ~f & ~o
            if dy == 1: new[0] = False
            if dy == -1: new[-1] = False
            if dx == 1: new[:, 0] = False
            if dx == -1: new[:, -1] = False
            src[new] = sm[new]; o |= new
        for y, x in zip(*np.where(o)): rgb[y, x] = RAMP_RGB[src[y, x]][0]; alpha[y, x] = 255
    return rgb, alpha

