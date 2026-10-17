"""Sufan (front) rig: assembles the cut parts into a RigKit rig.json, procedural face (eyes/brows/mouth), pose helpers.
All geometry in the master's pixel space (1824x2272), converted to rig units with PPU=3.25, origin = (912, 2130) (ground between boots)."""
import os, sys, json, math, shutil
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
from rigkit.vec import Art
from rigkit.face import _pack, _get, _q, VISEMES, DEFAULT_FACE, mix_vis
RIGB = os.path.join(HERE, 'characters', 'sufan', 'rig')
PPU = 3.25; OX, OY = 912.0, 2130.0
def U(px, py): return [(px - OX) / PPU, (py - OY) / PPU]

BONES_PX = {  # name: (parent, head_px, limit deg)
 'root': (None, (912, 2130), None), 'hips': ('root', (912, 1800), [-20, 20]), 'spine': ('hips', (912, 1800), [-25, 25]),
 'head': ('spine', (912, 1110), [-40, 40]), 'hat': ('head', (912, 500), [-35, 35]),
 'earL': ('head', (636, 600), [-50, 50]), 'earR': ('head', (1188, 600), [-50, 50]),
 'armL_up': ('spine', (600, 1040), [-50, 170]), 'armL_lo': ('armL_up', (425, 1217), [-8, 140]), 'handL': ('armL_lo', (303, 1394), [-70, 70]),
 'armR_up': ('spine', (1224, 1040), [-170, 50]), 'armR_lo': ('armR_up', (1398, 1219), [-140, 8]), 'handR': ('armR_lo', (1521, 1397), [-70, 70]),
 'legL_up': ('hips', (726, 1840), [-45, 45]), 'legL_lo': ('legL_up', (726, 1925), [-100, 100]), 'footL': ('legL_lo', (726, 2020), [-50, 50]),
 'legR_up': ('hips', (1100, 1840), [-45, 45]), 'legR_lo': ('legR_up', (1100, 1925), [-100, 100]), 'footR': ('legR_lo', (1100, 2020), [-50, 50]),
}
# face placement (px): sclera centres, radius, neutral pupil centres, mouth anchor (centre of smile curve), brow centres
EYE_C = {'L': (792.0, 609.0), 'R': (1032.0, 609.0)}; EYE_R = 55.5; PUPIL_R = 31.0
PUPIL_N = {'L': (798.5, 616.5), 'R': (1025.0, 616.5)}
MOUTH_C = (912.0, 873.0); BROW_C = {'L': (792.0, 452.0), 'R': (1032.0, 452.0)}
INK = (86, 24, 31)

def build(outdir=None):
    """writes out/rig.json and part pngs"""
    outdir = outdir or os.path.join(RIGB, 'out'); os.makedirs(outdir, exist_ok=True)
    bb = json.load(open(os.path.join(RIGB, 'parts', 'bbox.json')))
    parts = {}
    def save(name, img_bgra, x0, y0, bone):
        cv2.imwrite(os.path.join(outdir, name + '.png'), img_bgra)
        hx, hy = BONES_PX[bone][1]
        parts[name] = dict(image=name + '.png', anchor=[float(hx - x0), float(hy - y0)], size=[img_bgra.shape[1], img_bgra.shape[0]])
    # static parts: name -> bone
    simple = {'hat': 'hat', 'head': 'head', 'earL': 'earL', 'earR': 'earR', 'torso': 'spine', 'belly': 'hips',
              'armUpL': 'armL_up', 'armLoL': 'armL_lo', 'handL': 'handL', 'armUpR': 'armR_up', 'armLoR': 'armR_lo', 'handR': 'handR',
              'bootL': 'footL', 'bootR': 'footR'}
    for n, b in simple.items():
        im = cv2.imread(os.path.join(RIGB, 'parts_clean', n + '.png'), cv2.IMREAD_UNCHANGED); save(n, im, bb[n][0], bb[n][1], b)
    for s in 'LR':   # legs split at the knee (y=1925) with 12px overlap
        im = cv2.imread(os.path.join(RIGB, 'parts_clean', f'leg{s}.png'), cv2.IMREAD_UNCHANGED); x0, y0, x1, y1 = bb[f'leg{s}']
        cut_t = 1925 + 12 - y0; cut_s = 1925 - 12 - y0
        th = im[:cut_t].copy(); sh = im[cut_s:].copy()
        save(f'thigh{s}', th, x0, y0, f'leg{s}_up'); save(f'shin{s}', sh, x0, y0 + cut_s, f'leg{s}_lo')
    bones = [dict(name=n, parent=p, head=U(*h), limit=lim) for n, (p, h, lim) in BONES_PX.items()]
    Z = dict(thighL=1, thighR=1, shinL=2, shinR=2, bootL=3, bootR=3, belly=10, handL=18, handR=18, armLoL=19, armLoR=19, armUpL=20, armUpR=20,
             torso=30, earL=45, earR=45, head=50, hat=60)
    slots = []
    bone_of = {**simple, 'thighL': 'legL_up', 'thighR': 'legR_up', 'shinL': 'legL_lo', 'shinR': 'legR_lo'}
    for n, z in Z.items():
        slots.append(dict(name=n, part=n, bone=bone_of[n], z=z, mirror=False, tint=None, dyn=None, offset=[0, 0]))
    hx, hy = BONES_PX['head'][1]
    for k, c, z in (('eyeL', EYE_C['L'], 52), ('eyeR', EYE_C['R'], 52), ('mouth', MOUTH_C, 53), ('browL', BROW_C['L'], 54), ('browR', BROW_C['R'], 54)):
        slots.append(dict(name=k, part=None, bone='head', z=z, mirror=False, tint=None, dyn=k, offset=[(c[0] - hx) / PPU, (c[1] - hy) / PPU]))
    ik = {'legL': dict(chain=['legL_up', 'legL_lo', 'footL'], bend=1), 'legR': dict(chain=['legR_up', 'legR_lo', 'footR'], bend=1),
          'armL': dict(chain=['armL_up', 'armL_lo', 'handL'], bend=1), 'armR': dict(chain=['armR_up', 'armR_lo', 'handR'], bend=-1)}
    d = dict(name='sufan', character='sufan', view='front', ppu=PPU, height_units=(OY - 118) / PPU, bones=bones, slots=slots, parts=parts, ik=ik)
    json.dump(d, open(os.path.join(outdir, 'rig.json'), 'w'), indent=1)
    return os.path.join(outdir, 'rig.json')

# ----------------------------------------------------------------- procedural face (sprites in px units, ppu=1 canvas, then tagged PPU)
def _tag(sprite):
    im, an, _ = sprite
    return im, an, PPU
_LID = {}
def lid_color():
    if 'c' not in _LID:
        c = np.array([249, 224, 204], np.uint8)   # RGB sampled (cleaned) forehead/cheek cream beside the eyes; overridden if available
        p = os.path.join(RIGB, 'face_colors.json')
        if os.path.exists(p): c = np.array(json.load(open(p))['lid'], np.uint8)
        _LID['c'] = tuple(int(v) for v in c)
    return _LID['c']

def eye_sprite(side, look=(0, 0), blink=0.0, squint=0.0, lidtilt=0.0, pupil=1.0):
    key = ('sufeye', side, _q(look[0]), _q(look[1]), _q(blink), _q(squint), _q(lidtilt), _q(pupil))
    def mk():
        R = EYE_R; a = Art(-R - 8, -R - 8, R + 8, R + 8, ppu=1.0, ss=4)
        a.ellipse((0, 0), R, R, (253, 254, 253))
        nx, ny = PUPIL_N[side][0] - EYE_C[side][0], PUPIL_N[side][1] - EYE_C[side][1]
        lim = R - PUPIL_R * pupil - 3
        px = nx + look[0] * lim * 0.85; py = ny + look[1] * lim * 0.85
        n = math.hypot(px, py)
        if n > lim: px, py = px * lim / n, py * lim / n
        a.ellipse((px, py), PUPIL_R * pupil, PUPIL_R * pupil, (3, 2, 2), clip=True)
        lc = lid_color(); sgn = 1 if side == 'R' else -1
        xs = np.linspace(-R - 6, R + 6, 40)
        if blink > .02 or abs(lidtilt) > .02:
            yl = -R - 2 + blink * (2 * R + 4)
            top = [(x, -R - 14) for x in xs]; bot = [(x, yl + lidtilt * 30 * (x / R) * -sgn) for x in xs[::-1]]
            a.poly(top + bot, lc, clip=True)
            if blink > .06:
                a.curve([(x, yl + lidtilt * 30 * (x / R) * -sgn + 0.0 * x) for x in xs[4:-4]], INK, 6.0, clip=False)
        if squint > .02:
            ys = R + 3 - squint * 44
            a.poly([(x, ys - 10 * (1 - (x / R) ** 2)) for x in xs] + [(x, R + 14) for x in xs[::-1]], lc, clip=True)
        return _tag(_pack(a, 0, 0))
    return _get(key, mk)

def brow_sprite(side, h=0.0, tilt=0.0):
    key = ('sufbrow', side, _q(h), _q(tilt))
    def mk():
        a = Art(-70, -60, 70, 60, ppu=1.0, ss=4); sgn = 1 if side == 'R' else -1   # sgn>0 : inner end towards -x
        pts = []
        for x in np.linspace(-46, 46, 30):
            y = -9 * (1 - (x / 46) ** 2) - h * 17 + tilt * (-sgn * x) * 0.55
            pts.append((x, y))
        col = (118, 80, 56)
        for i in range(len(pts) - 1):
            t = i / (len(pts) - 1); r = 4.8 + 4.4 * math.sin(math.pi * t)
            a.capsule(pts[i], pts[i + 1], r, r, col)
        return _tag(_pack(a, 0, 0))
    return _get(key, mk)

def mouth_sprite(m):
    key = ('sufmouth',) + tuple(_q(m[k]) for k in ('open', 'wide', 'smile', 'round', 'teeth', 'tongue', 'lip'))
    def mk():
        a = Art(-130, -90, 130, 190, ppu=1.0, ss=4)
        hw = max(24, (36 + 71 * m['wide']) * (1 - .38 * m['round']))
        c = m['smile'] * 69 * (1 - m['round'] * .8)
        H = 8 + 118 * m['open'] * (1 - .22 * m['wide'] * (1 - m['round']))
        xs = np.linspace(-1, 1, 48); w = 12.0
        # philtrum: nose -> upper lip centre
        a.curve([(0, -63), (0, 3)], INK, w)
        if m['open'] < .03:
            a.curve([(u * hw, -c * u * u) for u in xs], INK, w)
            if m['lip']: a.ellipse((0, 16), hw * .5, 10, (230, 120, 120))
            return _tag(_pack(a, 0, 0))
        if m['round'] > .5:
            rx = hw; ry = max(H * .5, 16)
            a.ellipse((0, ry * .8), rx + 6, ry + 6, INK); a.ellipse((0, ry * .8), rx, ry, (122, 32, 46))
            if m['tongue'] > .1: a.ellipse((0, ry * 1.35), rx * .6, ry * .5, (238, 110, 120), clip=True)
            return _tag(_pack(a, 0, 0))
        up = [(u * hw, -c * u * u) for u in xs]; lo = [(u * hw, -c * u * u + H * (1 - u * u) ** .85) for u in xs[::-1]]
        shape = up + lo
        a.poly(shape, INK, outline=INK, ow=5.5); a.poly(shape, (122, 32, 46))
        if m['tongue'] > .05:
            a.ellipse((0, H * .88), hw * .58, H * .40 * (.4 + m['tongue'] * .6), (238, 108, 120), clip=True)
        if m['teeth'] > .05:
            th = min(H * .5, 26 * m['teeth'] + 6)
            a.poly([(u * hw * .92, -c * u * u + 2) for u in xs] + [(u * hw * .92, -c * u * u + th * (1 - u * u) ** .4 + 2) for u in xs[::-1]], (255, 250, 240), clip=True)
        a.curve([(u * hw, -c * u * u) for u in xs], INK, w)
        return _tag(_pack(a, 0, 0))
    return _get(key, mk)

def face_dyn(face=None):
    f = {**DEFAULT_FACE, **(face or {})}
    d = {'mouth': mouth_sprite(f['mouth'])}
    for s in 'LR':
        d['eye' + s] = eye_sprite(s, f['look'], f['blinkL'] if s == 'L' else f['blinkR'], f['squint'], f['lidtilt'], f['pupil'])
        h, t = f['brow' + s]; d['brow' + s] = brow_sprite(s, h, t)
    return d
