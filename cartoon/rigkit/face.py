"""Procedural face: eyes (look, blink, squint, lid tilt), brows (height, tilt), mouth (visemes + emotions).
Sprites are generated at runtime from numeric parameters (cached) so any in-between value is valid - no popping, no missing frames."""
import numpy as np
from .vec import Art

VISEMES = {
 'rest': dict(open=0.0, wide=.45, smile=.35, round=0, teeth=0, tongue=0, lip=0),
 'M':    dict(open=0.0, wide=.40, smile=.0,  round=0, teeth=0, tongue=0, lip=0),
 'A':    dict(open=.90, wide=.65, smile=.1,  round=0, teeth=.35, tongue=.5, lip=0),
 'E':    dict(open=.38, wide=1.0, smile=.25, round=0, teeth=.95, tongue=.1, lip=0),
 'I':    dict(open=.22, wide=.95, smile=.30, round=0, teeth=1.0, tongue=0, lip=0),
 'O':    dict(open=.70, wide=.15, smile=0,   round=1, teeth=0, tongue=.3, lip=0),
 'U':    dict(open=.38, wide=.0,  smile=0,   round=1, teeth=0, tongue=0, lip=0),
 'FV':   dict(open=.16, wide=.65, smile=.1,  round=0, teeth=1.0, tongue=0, lip=1),
 'L':    dict(open=.45, wide=.65, smile=.15, round=0, teeth=.8, tongue=1.0, lip=0),
 'smile':dict(open=0.0, wide=.85, smile=.95, round=0, teeth=0, tongue=0, lip=0),
 'grin': dict(open=.32, wide=1.0, smile=.85, round=0, teeth=1.0, tongue=.1, lip=0),
 'laugh':dict(open=.95, wide=1.0, smile=.95, round=0, teeth=.55, tongue=.7, lip=0),
 'sad':  dict(open=0.0, wide=.40, smile=-.75, round=0, teeth=0, tongue=0, lip=0),
 'gasp': dict(open=.85, wide=.2, smile=0, round=.85, teeth=0, tongue=.2, lip=0),
}
DEFAULT_FACE = dict(look=(0.0, 0.0), blinkL=0.0, blinkR=0.0, squint=0.0, lidtilt=0.0, browL=(0.0, 0.0), browR=(0.0, 0.0), mouth=VISEMES['rest'], pupil=1.0)

def mix_vis(a, b, t):
    return {k: a[k] * (1 - t) + b[k] * t for k in a}

def _q(x, n=24): return round(float(x) * n) / n
_CACHE = {}

def _get(key, fn):
    if key not in _CACHE:
        if len(_CACHE) > 1500: _CACHE.clear()
        _CACHE[key] = fn()
    return _CACHE[key]

def _pack(a, ox, oy):
    im = a.result()
    bgra = np.concatenate([im[..., 2::-1], im[..., 3:4]], -1) if False else np.dstack([im[..., 2], im[..., 1], im[..., 0], im[..., 3]])
    return bgra.astype(np.float32), a.anchor_px(ox, oy), a.ppu

def eye_sprite(spec, view, side, look, blink, squint, lidtilt, pupil):
    key = ('eye', spec['kind'], view, side, _q(look[0]), _q(look[1]), _q(blink), _q(squint), _q(lidtilt), _q(pupil))
    def mk():
        a = Art(-40, -44, 40, 44, ppu=2.0, ss=3)
        nw = 0.72 if view == 'side' else 1.0
        rx, ry = 25 * nw, 31
        a.ellipse((0, 0), rx, ry, (255, 255, 255))
        a.ellipse((0, 8), rx, ry * .55, (225, 232, 245), clip=True, alpha=.55)
        lx = look[0] * 9 * nw + (4 if view == 'side' else 0); ly = look[1] * 9
        ir = 15.5 * (1 if view == 'front' else .9)
        a.ellipse((lx, ly + 2), ir * nw if view == 'side' else ir, ir, spec['iris'], clip=True)
        a.ellipse((lx, ly + 3), ir * .55 * pupil * (nw if view == 'side' else 1), ir * .55 * pupil, (18, 14, 20), clip=True)
        a.ellipse((lx - 5 * nw, ly - 5), 4.5 * nw, 4.5, (255, 255, 255), clip=True)
        a.ellipse((lx + 5 * nw, ly + 7), 2.4 * nw, 2.4, (255, 255, 255), clip=True, alpha=.8)
        # lids (skin coloured) - top lid closes by `blink`, bottom lid rises by `squint`
        sk = spec['skin']
        yl = -ry - 3 + blink * (2 * ry + 6)
        if blink > .02 or abs(lidtilt) > .02:
            sgn = 1 if side == 'R' else -1
            xs = np.linspace(-rx - 4, rx + 4, 30)
            top = [(x, -ry - 12) for x in xs]
            bot = [(x, yl + lidtilt * 16 * (x / rx) * -sgn + 4 * (1 - (x / (rx + 4)) ** 2) * min(1, blink * 3) * 0) for x in xs[::-1]]
            a.poly(top + bot, sk, clip=True)
            if blink > .02:
                a.curve([(x, yl + lidtilt * 16 * (x / rx) * -sgn) for x in xs], (60, 36, 34), 3.6 if blink < .98 else 4.2, clip=False)
        if squint > .02:
            ys = ry + 3 - squint * 20
            xs = np.linspace(-rx - 4, rx + 4, 30)
            a.poly([(x, ys - 6 * (1 - (x / rx) ** 2)) for x in xs] + [(x, ry + 12) for x in xs[::-1]], sk, clip=True)
        if blink < .98:   # upper lash line
            t = np.radians(np.linspace(200, 340, 30))
            a.curve([(rx * 1.02 * np.cos(q), ry * 1.02 * np.sin(q)) for q in t if (ry * np.sin(q)) > yl - 1.0 or blink < .02], (58, 34, 34), 4.0)
        return _pack(a, 0, 0)
    return _get(key, mk)

def brow_sprite(spec, view, side, h, tilt):
    key = ('brow', spec['kind'], view, side, _q(h), _q(tilt))
    def mk():
        a = Art(-40, -50, 40, 30, ppu=2.0, ss=3)
        nw = .72 if view == 'side' else 1.0
        L = 24 * nw; pts = []
        sgn = -1 if side == 'R' else 1       # inner end of the R eye is at -x
        for u in np.linspace(-1, 1, 24):
            inner = (-u if side == 'R' else u)    # -1 at inner? make inner=+1 for R's u=-1 ... compute explicit
            iu = (1 - u) / 2 if side == 'R' else (1 + u) / 2    # 0 outer .. 1 inner
            y = -h * 14 + tilt * 16 * (iu - .5) * 2 - 5 * (1 - u * u)
            pts.append((u * L, y))
        a.curve(pts, spec['brow'], 8.5)
        return _pack(a, 0, 0)
    return _get(key, mk)

def mouth_sprite(spec, view, m):
    key = ('mouth', view) + tuple(_q(m[k]) for k in ('open', 'wide', 'smile', 'round', 'teeth', 'tongue', 'lip'))
    def mk():
        a = Art(-50, -40, 50, 70, ppu=2.0, ss=3)
        nw = .55 if view == 'side' else 1.0
        hw = (14 + 22 * m['wide']) * (1 - .35 * m['round']) * nw
        hw = max(hw, 9)
        c = m['smile'] * 15 * (1 - m['round'] * .8)
        h = 3 + 46 * m['open'] * (1 - .25 * m['wide'] * (1 - m['round']))
        ink = (84, 26, 34); xs = np.linspace(-1, 1, 40)
        top = [(u * hw, -c * u * u + c * .1 - 0.0) for u in xs]
        if m['open'] < .03:
            line = [(u * hw, c * (u * u) * -1 + (c if c > 0 else 0) * 0) for u in xs]
            pts = [(u * hw, -c * (u * u - .0) + (0 if c < 0 else 0)) for u in xs]
            a.curve([(u * hw, (-c * u * u) if c >= 0 else (-c * u * u)) for u in xs], ink, 4.4)
            if m['lip']: a.ellipse((0, 4), hw * .5, 4, (230, 120, 120))
            return _pack(a, 0, 0)
        if m['round'] > .5:
            rx = hw; ry = max(h * .5, 6)
            a.ellipse((0, ry * .6), rx + 3, ry + 3, ink)
            a.ellipse((0, ry * .6), rx, ry, (120, 30, 44))
            if m['tongue'] > .1: a.ellipse((0, ry * 1.05), rx * .6, ry * .45, (238, 110, 120), clip=True)
            return _pack(a, 0, 0)
        upper = [(u * hw, -c * u * u) for u in xs]
        lower = [(u * hw, -c * u * u + h * (1 - u * u) ** .85) for u in xs[::-1]]
        shape = upper + lower
        a.poly(shape, ink, outline=ink, ow=2.2)
        a.poly(shape, (122, 32, 46))
        if m['tongue'] > .05:
            a.ellipse((0, h * .85), hw * .55, h * .38 * (.4 + m['tongue'] * .6), (238, 108, 120), clip=True)
        if m['teeth'] > .05:
            th = min(h * .5, 11 * m['teeth'] + 3)
            a.poly([(u * hw * .9, -c * u * u + 1) for u in xs] + [(u * hw * .9, -c * u * u + th * (1 - u * u) ** .4 + 1) for u in xs[::-1]], (255, 255, 255), clip=True)
        if m['lip']:
            a.ellipse((0, h * 1.0), hw * .7, 7, (232, 126, 126), clip=False)
        a.curve([(u * hw, -c * u * u) for u in xs], ink, 4.0)
        return _pack(a, 0, 0)
    return _get(key, mk)

def face_dyn(face, spec, view='front'):
    f = {**DEFAULT_FACE, **face}
    d = {'mouth': mouth_sprite(spec, view, f['mouth'])}
    sides = ('L', 'R') if view == 'front' else ('R',)
    for s in sides:
        bl = f['blinkL'] if s == 'L' else f['blinkR']
        d['eye' + s] = eye_sprite(spec, view, s, f['look'], bl, f['squint'], f['lidtilt'], f['pupil'])
        h, t = f['brow' + s]
        d['brow' + s] = brow_sprite(spec, view, s, h, t)
    return d
