"""Sufan (SIDE view, facing +x) rig. Parts cut by characters/sufan/rig_side/s3_parts.py from master_side_2x.png (1850x2304).
Conventions: bone "L" = FAR limb, "R" = NEAR limb. Positive rot swings the rest direction (down) toward -x, so FORWARD (+x) = negative rot for arms/legs."""
import os, sys, json, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
from rigkit.vec import Art
from rigkit.face import _pack, _get, _q, VISEMES, DEFAULT_FACE
RIGB = os.path.join(HERE, 'characters', 'sufan', 'rig_side')
PPU = 3.336; OX, OY = 960.0, 2184.0
LEG_RAISE = 130   # px: hip joint raised INTO the belly (hidden behind it) so the legs can take real strides; visible leg/boots unchanged at rest
def U(px, py): return [(px - OX) / PPU, (py - OY) / PPU]
BONES_PX = {
 'root': (None, (960, 2184), None), 'hips': ('root', (960, 1880), [-20, 20]), 'spine': ('hips', (960, 1880), [-25, 25]),
 'head': ('spine', (900, 1060), [-40, 40]), 'hat': ('head', (880, 520), [-35, 35]), 'earR': ('head', (902, 520), [-50, 50]),
 'armL_up': ('spine', (880, 1090), [-170, 100]), 'armL_lo': ('armL_up', (880, 1280), [-140, 8]), 'handL': ('armL_lo', (890, 1550), [-70, 70]),
 'armR_up': ('spine', (880, 1090), [-170, 100]), 'armR_lo': ('armR_up', (880, 1280), [-140, 8]), 'handR': ('armR_lo', (890, 1550), [-70, 70]),
 'legL_up': ('hips', (960, 1900 - LEG_RAISE), [-60, 60]), 'legL_lo': ('legL_up', (960, 1970), [-5, 120]), 'footL': ('legL_lo', (960, 2032), [-85, 85]),
 'legR_up': ('hips', (960, 1900 - LEG_RAISE), [-60, 60]), 'legR_lo': ('legR_up', (960, 1970), [-5, 120]), 'footR': ('legR_lo', (960, 2036), [-85, 85]),
}
EYE_C = (1236.5, 606.2); EYE_RX, EYE_RY = 30.0, 87.0; PUPIL_N = (1238.0, 626.0); PUPIL_R = (22.0, 30.0)   # eye = narrow profile lens hole of glasses.png (measured centre 1236.5/606.2, 62x181 px); old 100x108 ellipse overflowed the ring
MOUTH_C = (1365.0, 810.0); BROW_C = (1226.0, 486.0)
INK = (86, 24, 31)
def fix_holes(im):
    """fill interior alpha holes (matte removed the near-white interior of the cuff strap ring) with the surrounding colour"""
    a = im[..., 3] > 127
    inv = (~a).astype(np.uint8); n, cc = cv2.connectedComponents(inv, connectivity=4)
    border = set(np.unique(np.concatenate([cc[0], cc[-1], cc[:, 0], cc[:, -1]])))
    hole = np.isin(cc, [i for i in range(1, n) if i not in border]) & ~a
    if not hole.any(): return im
    hole = cv2.dilate(hole.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    rgb = cv2.inpaint(np.ascontiguousarray(im[..., :3]), (hole & ~a).astype(np.uint8) * 255, 5, cv2.INPAINT_TELEA)
    out = im.copy(); out[..., :3] = np.where((hole & ~a)[..., None], rgb, im[..., :3]); out[..., 3] = np.where(hole, 255, im[..., 3]); return out

def build(outdir=None):
    outdir = outdir or os.path.join(RIGB, 'out'); os.makedirs(outdir, exist_ok=True)
    bb = json.load(open(os.path.join(RIGB, 'parts', 'bbox.json'))); parts = {}
    def save(name, img, src, bone):
        cv2.imwrite(os.path.join(outdir, name + '.png'), img); x0, y0 = bb[src][:2]; hx, hy = BONES_PX[bone][1]
        parts[name] = dict(image=name + '.png', anchor=[float(hx - x0), float(hy - y0)], size=[img.shape[1], img.shape[0]])
    ld = lambda n: cv2.imread(os.path.join(RIGB, 'parts', n + '.png'), cv2.IMREAD_UNCHANGED)
    spec = {'hat': ('hat', 'hat'), 'head': ('head', 'head'), 'earR': ('ear', 'earR'), 'glasses': ('glasses', 'head'), 'torso': ('torso', 'spine'), 'belly': ('belly', 'hips'),
            'armUpR': ('armUp', 'armR_up'), 'armLoR': ('armLo', 'armR_lo'), 'handR': ('hand', 'handR'),
            'armUpL': ('armUp', 'armL_up'), 'armLoL': ('armLo', 'armL_lo'), 'handL': ('hand', 'handL'),
            'thighR': ('thighN', 'legR_up'), 'shinR': ('shinN', 'legR_lo'), 'bootR': ('bootN', 'footR'),
            'thighL': ('thighF', 'legL_up'), 'shinL': ('shinF', 'legL_lo'), 'bootL': ('bootF', 'footL')}
    for n, (src, b) in spec.items():
        img = fix_holes(ld(src)) if src == 'armLo' else ld(src)
        if src == 'glasses':    # temple tail poked out behind the ear as a stray dot when the ear/head moved -> end the temple under the ear
            img = img.copy(); img[:, :44] = 0
        if src == 'ear':        # remove the baked-in stray dark dot (old glasses-temple end) at the ear's front edge
            img = img.copy(); dk = ((img[..., :3].max(axis=2) < 80) & (img[..., 3] > 100)).astype(np.uint8); dk[:, :200] = 0
            dk = cv2.dilate(dk, np.ones((7, 7), np.uint8)); rgb = cv2.inpaint(np.ascontiguousarray(img[..., :3]), dk * 255, 6, cv2.INPAINT_TELEA)
            img[..., :3] = np.where(dk[..., None] > 0, rgb, img[..., :3])
        if src in ('thighN', 'thighF'):    # extend the (mostly hidden) thigh upward to the raised hip joint
            pad = LEG_RAISE + 24; img = np.vstack([np.repeat(img[:1], pad, axis=0), img]); bb = dict(bb); bb[src] = [bb[src][0], bb[src][1] - pad] + list(bb[src][2:])
        save(n, img, src, b)
    import sufan_hands as _H
    _H.add_variants(outdir, parts, {'handL': ((0.0, 1.0), -1), 'handR': ((0.0, 1.0), -1)})
    bones = [dict(name=n, parent=p, head=U(*h), limit=lim) for n, (p, h, lim) in BONES_PX.items()]
    Z = dict(thighL=1, shinL=2, bootL=3, armUpL=4, armLoL=4, handL=4, thighR=5, shinR=6, bootR=7, belly=10, torso=30,
             handR=40, armLoR=41, armUpR=42, head=50, glasses=53, earR=55, hat=60)
    TINT = {'thighL': .86, 'shinL': .86, 'bootL': .86, 'armUpL': .8, 'armLoL': .8, 'handL': .8}
    slots = []
    for n, z in Z.items():
        t = TINT.get(n); slots.append(dict(name=n, part=n, bone=spec[n][1], z=z, mirror=False, tint=[t, t, t] if t else None, dyn=None, offset=[0, 0]))
    hx, hy = BONES_PX['head'][1]
    for k, c, z in (('eyeR', EYE_C, 52), ('mouth', MOUTH_C, 52.5), ('browR', BROW_C, 54)):
        slots.append(dict(name=k, part=None, bone='head', z=z, mirror=False, tint=None, dyn=k, offset=[(c[0] - hx) / PPU, (c[1] - hy) / PPU]))
    ik = {'legL': dict(chain=['legL_up', 'legL_lo', 'footL'], bend=-1), 'legR': dict(chain=['legR_up', 'legR_lo', 'footR'], bend=-1),
          'armL': dict(chain=['armL_up', 'armL_lo', 'handL'], bend=-1), 'armR': dict(chain=['armR_up', 'armR_lo', 'handR'], bend=-1)}
    d = dict(name='sufan_side', character='sufan', view='side', ppu=PPU, height_units=(OY - 119) / PPU, bones=bones, slots=slots, parts=parts, ik=ik)
    json.dump(d, open(os.path.join(outdir, 'rig.json'), 'w'), indent=1); return os.path.join(outdir, 'rig.json')

def _tag(s): im, an, _ = s; return im, an, PPU
_LID = {}
def lid_color():
    if 'c' not in _LID:
        c = json.load(open(os.path.join(RIGB, 'face_colors.json')))['lid']; _LID['c'] = tuple(int(v) for v in c)
    return _LID['c']

def eye_sprite(look=(0, 0), blink=0.0, squint=0.0, lidtilt=0.0, pupil=1.0, arc=0.0):
    key = ('sufeyeS', _q(look[0]), _q(look[1]), _q(blink), _q(squint), _q(lidtilt), _q(pupil), _q(arc))
    def mk():
        rx, ry = EYE_RX, EYE_RY; a = Art(-rx - 10, -ry - 10, rx + 10, ry + 10, ppu=1.0, ss=4)
        a.ellipse((0, 0), rx, ry, (253, 254, 253))
        nx, ny = PUPIL_N[0] - EYE_C[0], PUPIL_N[1] - EYE_C[1]
        pr = (PUPIL_R[0] * pupil, PUPIL_R[1] * pupil)
        px = nx + look[0] * (rx - pr[0] - 4) * 0.85; py = ny + look[1] * (ry - pr[1] - 4) * 0.85
        e = (px / max(rx - pr[0] - 2, 1)) ** 2 + (py / max(ry - pr[1] - 2, 1)) ** 2
        if e > 1: px, py = px / math.sqrt(e), py / math.sqrt(e)
        a.ellipse((px, py), pr[0], pr[1], (3, 2, 2), clip=True)
        lc = lid_color(); xs = np.linspace(-rx - 8, rx + 8, 40)
        if blink > .02 or abs(lidtilt) > .02:
            yl = -ry - 2 + blink * (2 * ry + 4)
            a.poly([(x, -ry - 16) for x in xs] + [(x, yl + lidtilt * 28 * (x / rx) * -1) for x in xs[::-1]], lc, clip=True)
            if blink > .06: a.curve([(x, yl + lidtilt * 28 * (x / rx) * -1) for x in xs[4:-4]], INK, 6.0, clip=False)
        if squint > .02:
            ys = ry + 3 - squint * 70
            a.poly([(x, ys - 10 * (1 - (x / rx) ** 2)) for x in xs] + [(x, ry + 14) for x in xs[::-1]], lc, clip=True)
        if arc > .02:
            a.ellipse((0, 0), rx + 1, ry + 1, lc, clip=False)
            a.curve([(x, 10 - arc * 46 * (1 - (x / 26.0) ** 2)) for x in np.linspace(-26, 26, 32)], INK, 8.0, clip=False)   # arc kept INSIDE the narrow profile lens (inner hole 62 px wide, centre +12/-14 from EYE_C)
        return _tag(_pack(a, 0, 0))
    return _get(key, mk)

def brow_sprite(h=0.0, tilt=0.0):
    key = ('sufbrowS', _q(h), _q(tilt))
    def mk():
        a = Art(-70, -60, 70, 60, ppu=1.0, ss=4); pts = []
        for x in np.linspace(-40, 40, 28): pts.append((x, -8 * (1 - (x / 40) ** 2) - h * 17 + tilt * (-x) * 0.55))   # tilt>0: inner(front,+x) end down
        for i in range(len(pts) - 1):
            t = i / (len(pts) - 1); r = 4.6 + 4.2 * math.sin(math.pi * t); a.capsule(pts[i], pts[i + 1], r, r, (118, 80, 56))
        return _tag(_pack(a, 0, 0))
    return _get(key, mk)

_XE = [(-110, 50), (-95, 58), (-65, 58), (-50, 54), (-35, 50), (-20, 46), (-5, 39), (10, 31), (25, 22), (40, 7), (55, -17), (70, -43)]
def _xe(y):   # head silhouette x (relative to the mouth origin) at height y, measured from head.png
    ys = [p[0] for p in _XE]; xs = [p[1] for p in _XE]; return float(np.interp(y, ys, xs))
def mouth_sprite(m):
    """PROFILE mouth (v2). Origin = centre of the original smile curve. Closed: the smile curve. Open: a wedge whose apex is the mouth corner (inside the cheek)
    and whose front end opens onto the snout/chin silhouette (upper lip stays, lower lip drops) - not a frontal 'V' pasted on the cheek."""
    key = ('sufmouthS2',) + tuple(_q(m[k]) for k in ('open', 'wide', 'smile', 'round', 'teeth', 'tongue', 'lip'))
    def mk():
        a = Art(-120, -110, 70, 200, ppu=1.0, ss=4)
        s = 0.67 + 0.7 * m['wide']; xb = -41 * s; yb = -20; xf, yf = 41.0, -46.0
        A = 30 + 60 * m['smile']; N = 44; us = np.linspace(0, 1, N); w = 9.0
        line = lambda u: (xb + (xf - xb) * u, yb + (yf - yb) * u + A * math.sin(math.pi * u ** 0.8))
        if m['open'] < .03:
            a.curve([line(u) for u in us], INK, w); return _tag(_pack(a, 0, 0))
        op = min(1.0, m['open']); H = 10 + 60 * op ** .8; rd = m['round']
        xfo = _xe(yf) - 3.0                                  # upper lip front end sits on the silhouette
        k = min(1.0, op * 6.0); xF = xf + (xfo - xf) * k
        if rd > .3:                                           # pursed / round: ring-shaped opening just inside the snout/chin front
            ry = max(11.0, H * .5); rx = 15 + 9 * (1 - rd) + 8 * m['wide']; cy = yf + ry + 2
            cx = min(_xe(cy + ry * .7) - rx * .72 - 3.0, _xe(cy) - rx - 1.5)
            th = np.linspace(0, 2 * math.pi, 48, endpoint=False)
            ring = [(cx + rx * math.cos(t), cy + ry * math.sin(t)) for t in th]
            a.poly(ring, INK); a.poly([(cx + (rx - 5) * math.cos(t), cy + (ry - 5) * math.sin(t)) for t in th], (122, 32, 46))
            if m['tongue'] > .1: a.ellipse((cx - 1, cy + ry * .45), rx * .6, ry * .38, (238, 110, 120), clip=True)
            return _tag(_pack(a, 0, 0))
        if True:
            Ao = A * (1 - .55 * op)
            ul = lambda u: (xb + (xF - xb) * u, yb + (yf - yb) * u + Ao * math.sin(math.pi * u ** 0.8))
            up = [ul(u) for u in us]
            yl = yf + H; xl = _xe(yl) - 3.0
            lo = [(x + (xl - xF) * u, y + H * u ** 0.9 + .12 * H * math.sin(math.pi * u)) for (x, y), u in zip(up, us)]
        shape = up + lo[::-1]
        a.poly(shape, (122, 32, 46))
        if m['tongue'] > .05:
            cx = lo[int(N * .42)][0]; cy = lo[int(N * .42)][1] - .14 * H
            a.ellipse((cx, cy), 22 + 8 * m['tongue'], max(5, H * .26 * (.5 + m['tongue'] * .5)), (238, 108, 120), clip=True)
        if m['teeth'] > .05:
            th = min(.42 * H, 20 * m['teeth'] + 3)
            a.poly(up + [(x, y + th * min(1.0, u * 1.6) ** .8) for (x, y), u in zip(up, us)][::-1], (255, 250, 240), clip=True)
        if m['lip'] > .5:      # F/V: upper teeth rest on the lower lip
            a.curve(lo[int(N * .35):], (214, 150, 150), 7.0, clip=True)
        a.curve(up, INK, w); a.curve(lo, INK, w * .9)
        return _tag(_pack(a, 0, 0))
    return _get(key, mk)

def face_dyn(face=None):
    f = {**DEFAULT_FACE, **(face or {})}
    h, t = f['browR']
    return {'mouth': mouth_sprite(f['mouth']), 'eyeR': eye_sprite(f['look'], f['blinkR'], f['squint'], f['lidtilt'], f['pupil'], f.get('arc', 0.0)), 'browR': brow_sprite(h, t)}
