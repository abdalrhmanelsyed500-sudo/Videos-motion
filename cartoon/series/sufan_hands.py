"""Procedural hand-pose sprites for Sufan (same pink mitten style: 3 fingers + thumb, soft darker-pink outline).
Each sprite is drawn in the forearm axis frame (wrist at origin, +v toward the fingers) and rotated to the rest direction of the hand bone,
so it can be swapped for the drawn hand part:  rig.draw(..., swap={'handR': 'handR_fist'})"""
import os, math, numpy as np, cv2
from rigkit.vec import Art, save_png
SKIN = (249, 189, 166); OUT = (233, 166, 142); SHADE = (240, 172, 150)
VARIANTS = ('fist', 'point', 'thumb', 'flat')

def _shape(a, T, kind):
    """T(u,v)->xy. thumb side is u<0."""
    def E(c, ru, rv, rot=0.0):
        pts = [T(c[0] + ru * math.cos(t) * math.cos(rot) - rv * math.sin(t) * math.sin(rot), c[1] + ru * math.cos(t) * math.sin(rot) + rv * math.sin(t) * math.cos(rot)) for t in np.linspace(0, 2 * math.pi, 40, endpoint=False)]
        return pts
    def draw(pts, ow=5.0): a.poly(pts, SKIN, outline=OUT, ow=ow)
    def cap(p0, p1, r, ow=5.0): a.capsule(T(*p0), T(*p1), r, r, SKIN, outline=OUT, ow=ow)
    # forearm tube (hidden under the sleeve)
    a.poly([T(-37, -95), T(37, -95), T(37, 6), T(-37, 6)], SKIN)
    if kind == 'flat':      # relaxed flat hand, fingers together
        draw(E((0, 52), 46, 46)); 
        for u in (-24, 0, 24): cap((u, 70), (u * 1.05, 128 - abs(u) * .6), 15)
        cap((-48, 40), (-78, 78), 15)
    elif kind in ('fist', 'thumb'):
        draw(E((0, 52), 48, 44))
        for u in (-24, 0, 24): draw(E((u, 94 - abs(u) * .15), 20, 18))
        if kind == 'fist': draw(E((-44, 70), 17, 26, 0.35))
        else: cap((-38, 40), (-80, -2), 16)
        a.curve([T(-30, 80), T(-6, 74), T(20, 78)], SHADE, 4.5)
    elif kind == 'point':
        draw(E((0, 46), 46, 38))
        for u in (10, 30): draw(E((u, 84), 18, 17))
        cap((-16, 62), (-16, 150), 15)
        draw(E((-46, 58), 16, 22, 0.35))
        a.curve([T(0, 76), T(24, 72)], SHADE, 4.5)

def make(kind, dirvec, thumb_sign=1):
    """returns (premult RGBA float image, anchor px). dirvec = unit vector of the forearm axis in screen px (y down)."""
    d = np.array(dirvec, float); d /= np.linalg.norm(d); perp = np.array([d[1], -d[0]]) * (-1 if thumb_sign < 0 else 1)
    # perp points to the +u side; thumb is on -u
    def T(u, v): p = u * perp + v * d; return (float(p[0]), float(p[1]))
    a = Art(-190, -190, 190, 230, ppu=1.0, ss=4)
    _shape(a, T, kind)
    return a.result(), a.anchor_px(0, 0)

def add_variants(outdir, parts, spec):
    """spec: {'handL': (dirvec, thumb_sign), ...} -> writes PNGs, registers parts named '<hand>_<kind>'"""
    for hand, (dv, ts) in spec.items():
        for k in VARIANTS:
            im, an = make(k, dv, ts); name = f'{hand}_{k}'
            save_png(im, os.path.join(outdir, name + '.png'))
            parts[name] = dict(image=name + '.png', anchor=[float(an[0]), float(an[1])], size=[im.shape[1], im.shape[0]])
