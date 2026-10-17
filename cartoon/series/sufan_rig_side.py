"""Sufan (SIDE view, facing +x) rig. Parts cut by characters/sufan/rig_side/s3_parts.py from master_side_2x.png (1850x2304).
Conventions: bone "L" = FAR limb, "R" = NEAR limb. Positive rot swings the rest direction (down) toward -x, so FORWARD (+x) = negative rot for arms/legs."""
import os, sys, json, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
from rigkit.vec import Art
from rigkit.face import _pack, _get, _q, VISEMES, DEFAULT_FACE
RIGB = os.path.join(HERE, 'characters', 'sufan', 'rig_side')
PPU = 3.336; OX, OY = 998.0, 2184.0
def U(px, py): return [(px - OX) / PPU, (py - OY) / PPU]
BONES_PX = {
 'root': (None, (998, 2184), None), 'hips': ('root', (960, 1880), [-20, 20]), 'spine': ('hips', (960, 1880), [-25, 25]),
 'head': ('spine', (900, 1060), [-40, 40]), 'hat': ('head', (880, 520), [-35, 35]), 'earR': ('head', (902, 520), [-50, 50]),
 'armL_up': ('spine', (880, 1090), [-170, 100]), 'armL_lo': ('armL_up', (880, 1280), [-140, 8]), 'handL': ('armL_lo', (890, 1550), [-70, 70]),
 'armR_up': ('spine', (880, 1090), [-170, 100]), 'armR_lo': ('armR_up', (880, 1280), [-140, 8]), 'handR': ('armR_lo', (890, 1550), [-70, 70]),
 'legL_up': ('hips', (1034, 1900), [-45, 45]), 'legL_lo': ('legL_up', (1034, 1970), [-5, 100]), 'footL': ('legL_lo', (1040, 2032), [-50, 50]),
 'legR_up': ('hips', (886, 1900), [-45, 45]), 'legR_lo': ('legR_up', (886, 1970), [-5, 100]), 'footR': ('legR_lo', (890, 2036), [-50, 50]),
}
EYE_C = (1224.0, 620.0); EYE_RX, EYE_RY = 50.0, 54.0; PUPIL_N = (1238.0, 626.0); PUPIL_R = (22.0, 30.0)
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
    for n, (src, b) in spec.items(): save(n, fix_holes(ld(src)) if src == 'armLo' else ld(src), src, b)
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
            ys = ry + 3 - squint * 46
            a.poly([(x, ys - 10 * (1 - (x / rx) ** 2)) for x in xs] + [(x, ry + 14) for x in xs[::-1]], lc, clip=True)
        if arc > .02:
            a.ellipse((0, 0), rx + 1, ry + 1, lc, clip=False)
            a.curve([(x, ry * .30 - arc * 50 * (1 - (x / 44.0) ** 2)) for x in np.linspace(-44, 44, 32)], INK, 10.0, clip=False)
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

def mouth_sprite(m):
    """profile mouth; origin = centre of the original smile curve. Back corner is free, the front end stays on the snout edge."""
    key = ('sufmouthS',) + tuple(_q(m[k]) for k in ('open', 'wide', 'smile', 'round', 'teeth', 'tongue', 'lip'))
    def mk():
        a = Art(-120, -110, 70, 200, ppu=1.0, ss=4)
        s = 0.67 + 0.7 * m['wide']; xb = -41 * s; yb = -20; xf, yf = 41.0, -46.0
        A = 30 + 60 * m['smile']; xs = np.linspace(0, 1, 40); w = 9.0
        line = lambda u: (xb + (xf - xb) * u, yb + (yf - yb) * u + A * math.sin(math.pi * u ** 0.8))
        up = [line(u) for u in xs]
        if m['open'] < .03:
            a.curve(up, INK, w); return _tag(_pack(a, 0, 0))
        H = 6 + 100 * m['open']
        if m['round'] > .5:
            cx, cy = 6, 14 + H * .25; rx = 20 + 12 * (1 - m['round']) + 8 * m['wide']; ry = max(H * .5, 18)
            a.ellipse((cx, cy), rx + 5, ry + 5, INK); a.ellipse((cx, cy), rx, ry, (122, 32, 46))
            if m['tongue'] > .1: a.ellipse((cx, cy + ry * .5), rx * .6, ry * .45, (238, 110, 120), clip=True)
            return _tag(_pack(a, 0, 0))
        lo = [(x - .22 * H * math.sin(math.pi * u), y + H * math.sin(math.pi * u) ** .8) for (x, y), u in zip(up, xs)][::-1]
        shape = up + lo
        a.poly(shape, INK, outline=INK, ow=5); a.poly(shape, (122, 32, 46))
        if m['tongue'] > .05:
            a.ellipse((xb * .1 + 4, line(.45)[1] + H * .8), 30, H * .34 * (.4 + m['tongue'] * .6), (238, 108, 120), clip=True)
        if m['teeth'] > .05:
            th = min(H * .5, 22 * m['teeth'] + 5)
            a.poly(up + [(x, y + th * math.sin(math.pi * u) ** .6) for (x, y), u in zip(up, xs)][::-1], (255, 250, 240), clip=True)
        a.curve(up, INK, w); return _tag(_pack(a, 0, 0))
    return _get(key, mk)

def face_dyn(face=None):
    f = {**DEFAULT_FACE, **(face or {})}
    h, t = f['browR']
    return {'mouth': mouth_sprite(f['mouth']), 'eyeR': eye_sprite(f['look'], f['blinkR'], f['squint'], f['lidtilt'], f['pupil'], f.get('arc', 0.0)), 'browR': brow_sprite(h, t)}
