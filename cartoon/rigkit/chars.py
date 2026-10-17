"""Character art (flat vector style, no outlines -> limbs are round-capped capsules, so joints can never open gaps).
Every part sprite is drawn around its own joint at x=0 (world y in rest pose) and returns an anchor = joint position in px."""
import numpy as np
from .vec import Art

PPU = 2.0
SPECS = {
 'zaki': dict(kind='boy', skin=(244, 192, 150), skin_sh=(220, 158, 118), hair=(58, 38, 32), hair_hi=(104, 72, 56),
              shirt=(255, 140, 40), shirt_sh=(222, 100, 20), shirt_hi=(255, 180, 96), accent=(255, 255, 255),
              bottom=(46, 98, 190), bottom_sh=(30, 70, 150), shoe=(214, 52, 52), shoe_hi=(244, 110, 100), sock=(255, 255, 255),
              cheek=(255, 138, 128), iris=(86, 52, 30), brow=(52, 32, 28), tie=None),
 'lulu': dict(kind='girl', skin=(250, 206, 174), skin_sh=(226, 168, 134), hair=(44, 28, 38), hair_hi=(92, 60, 78),
              shirt=(255, 118, 170), shirt_sh=(224, 78, 134), shirt_hi=(255, 170, 204), accent=(255, 255, 255),
              bottom=(136, 86, 200), bottom_sh=(100, 60, 160), shoe=(30, 170, 160), shoe_hi=(110, 224, 214), sock=(255, 255, 255),
              cheek=(255, 132, 140), iris=(54, 92, 150), brow=(40, 26, 34), tie=(255, 208, 60)),
}
LIM = dict(upper=86, fore=80, thigh=96, shin=80)

def _mix(a, b, t): return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))

def _new(x0, y0, x1, y1): return Art(x0, y0, x1, y1, ppu=PPU, ss=3)

def _fin(a, ax, ay):
    return a.result(), a.anchor_px(ax, ay)

# ------------------------------------------------------------------ head
def head_part(s, view):
    a = _new(-150, -250, 150, 40)
    sk, sh = s['skin'], s['skin_sh']; boy = s['kind'] == 'boy'
    if view == 'front':
        a.ellipse((-103, -88), 15, 21, sk); a.ellipse((103, -88), 15, 21, sk)
        a.ellipse((-103, -88), 7, 12, sh, alpha=.7); a.ellipse((103, -88), 7, 12, sh, alpha=.7)
        a.ellipse((0, -96), 106, 100, sk)
        a.ellipse((12, -22), 70, 70, sh, clip=True, alpha=.0)
        a.ellipse((0, 4), 96, 34, sh, clip=True, alpha=.10); a.ellipse((0, 10), 80, 22, sh, clip=True, alpha=.10)   # soft chin shadow
        a.ellipse((-66, -76), 24, 15, s['cheek'], alpha=.40); a.ellipse((66, -76), 24, 15, s['cheek'], alpha=.40)
        # hair cap
        top = [(112 * np.cos(np.radians(t)), -98 + 110 * np.sin(np.radians(t))) for t in np.linspace(184, 356, 40)]
        if boy:
            fr = [(106, -108), (100, -140), (82, -164), (52, -176), (22, -168), (-8, -182), (-40, -170), (-66, -176), (-90, -156), (-102, -134), (-106, -108)]
        else:
            fr = [(110, -106), (104, -146), (84, -170), (50, -180), (14, -184), (-24, -182), (-58, -178), (-88, -160), (-104, -134), (-110, -106)]
        def _cl(p):
            x, y = p; lim = 112 * np.sqrt(max(0.0, 1 - ((y + 98) / 110) ** 2)) - 14
            return (float(np.sign(x)) * min(abs(x), max(lim, 0)), y)
        fr = [_cl(p) for p in fr]
        a.poly(top + fr, s['hair'])
        a.ellipse((-40, -192), 34, 9, s['hair_hi'], rot=-.2, clip=True, alpha=.9)
        if not boy:   # centre parting
            a.curve([(0, -200), (2, -190), (-2, -184)], _mix(s['hair'], (0, 0, 0), .35), 3, clip=True)
    else:  # side, facing +x
        a.ellipse((100, -82), 12, 12, sk)                                        # nose
        a.ellipse((0, -96), 99, 100, sk)
        a.ellipse((0, 6), 96, 30, sh, clip=True, alpha=.12)
        a.ellipse((50, -76), 22, 14, s['cheek'], alpha=.38)
        a.ellipse((-14, -90), 17, 22, sk); a.ellipse((-14, -90), 8, 13, sh, alpha=.75)
        top = [(108 * np.cos(np.radians(t)), -96 + 110 * np.sin(np.radians(t))) for t in np.linspace(130, 356, 60)]
        # back of head down to nape then inner boundary behind the ear back to the forehead
        inner = [(106, -112), (96, -140), (74, -166), (40, -172), (8, -156), (-8, -124), (-30, -112), (-56, -96), (-84, -70), (-92, -44)]
        # reorder: forehead -> over top -> back -> nape -> inner boundary
        poly = [(92, -130)] + top[::-1][:0]
        arc = [(106 * np.cos(np.radians(t)), -96 + 108 * np.sin(np.radians(t))) for t in np.linspace(355, 140, 60)]
        poly = [(92, -146), (62, -172)] + arc[3:] + [(-96, -60), (-80, -40), (-52, -52), (-34, -72), (-30, -112), (-18, -130), (22, -150), (60, -164), (92, -140)]
        a.poly(poly, s['hair'])
        a.ellipse((-40, -170), 30, 8, s['hair_hi'], rot=-.5, clip=True, alpha=.8)
    return _fin(a, 0, 0)

def tuft_part(s):
    a = _new(-60, -90, 60, 30)
    h = s['hair']
    a.poly([(-30, 12), (-34, -30), (-20, -62), (-8, -30), (4, -78), (14, -34), (30, -56), (30, 12)], h)
    a.ellipse((6, -4), 36, 14, h)
    a.poly([(-6, -26), (4, -64), (8, -30)], s['hair_hi'], alpha=.8)
    return _fin(a, 0, 0)

def pigtail_part(s):
    a = _new(-70, -30, 110, 190)
    h = s['hair']; lean = lambda y: 0.24 * max(y, 0)
    L = [(-17 + lean(y), y) for y in (0, 30, 70, 110, 140)]; Rr = [(17 + lean(y), y) for y in (140, 110, 70, 30, 0)]
    a.poly(L + [(0, 168)] + Rr, h)
    a.ellipse((lean(140), 140), 26, 30, h, rot=-.2)
    a.ellipse((lean(70) - 8, 64), 5, 34, s['hair_hi'], rot=-.2, clip=True, alpha=.8)
    t = s['tie'] or (255, 208, 60)
    a.rrect(-21, -8, 21, 14, 8, t); a.rrect(-21, 6, 21, 14, 4, tuple(int(v * .8) for v in t), clip=True)
    return _fin(a, 0, 0)

# ------------------------------------------------------------------ torso / pelvis
def _emblem(a, s, cx, cy):
    if s['kind'] == 'boy':
        pts = []
        for i in range(10):
            r = 26 if i % 2 == 0 else 11; t = np.radians(-90 + i * 36)
            pts.append((cx + r * np.cos(t), cy + r * np.sin(t)))
        a.poly(pts, s['accent'])
    else:
        a.ellipse((cx - 12, cy - 6), 14, 14, s['accent']); a.ellipse((cx + 12, cy - 6), 14, 14, s['accent'])
        a.poly([(cx - 25, cy - 1), (cx + 25, cy - 1), (cx, cy + 26)], s['accent'])

def torso_part(s, view):
    a = _new(-130, -440, 130, -150)
    sk = s['skin']; hw = 66 if view == 'front' else 52; cx = 0 if view == 'front' else 3
    a.capsule((cx + 2, -372), (cx + 2, -418), 21, 20, sk)                       # neck
    a.ellipse((cx + 2, -384), 30, 12, s['skin_sh'], alpha=.55)
    a.rrect(cx - hw, -392, cx + hw, -188, 38, s['shirt'])
    a.rrect(cx - hw, -214, cx + hw, -188, 12, s['shirt_sh'], clip=True, alpha=.5)   # hem
    a.ellipse((cx + hw + 28, -290), 40, 130, s['shirt_sh'], clip=True, alpha=.45)    # shade
    a.ellipse((cx - hw + 12, -338), 8, 44, s['shirt_hi'], clip=True, alpha=.55)
    a.ellipse((cx + 2, -391), 36 if view == 'front' else 26, 14, sk)             # neckline
    a.ellipse((cx + 2, -384), 34 if view == 'front' else 24, 10, s['skin_sh'], clip=True, alpha=.6)
    a.curve([(cx - 36, -392), (cx - 20, -382), (cx + 2, -378), (cx + 24, -382), (cx + 40, -392)], s['shirt_sh'], 5, clip=False) if view == 'front' else None
    if view == 'front':
        a.rrect(-hw, -310, hw, -296, 0, s['accent'], clip=True, alpha=.0)
        _emblem(a, s, 0, -290)
    else:
        _emblem(a, s, cx + 6, -290)
    return _fin(a, 0, -215)

def pelvis_part(s, view):
    a = _new(-130, -260, 130, -120)
    hw = 58 if view == 'front' else 46; cx = 0 if view == 'front' else 3
    if s['kind'] == 'boy':
        a.rrect(cx - hw, -246, cx + hw, -176, 24, s['bottom'])
        a.rrect(cx - hw, -246, cx + hw, -226, 8, s['bottom_sh'], clip=True, alpha=.6)
        a.rrect(cx - 10, -246, cx + 10, -236, 3, (240, 220, 80), clip=True, alpha=.0)
    else:
        sw = 98 if view == 'front' else 80
        pts = [(cx - hw + 6, -244), (cx + hw - 6, -244)]
        n = 9
        for i in range(n + 1):
            x = cx + sw - (2 * sw) * i / n
            pts.append((x, -140 + (8 if i % 2 else 0) * (1 if True else 0) - 2 * np.sin(np.pi * i / n)))
        a.poly(pts, s['bottom'])
        for k in range(-3, 4):
            a.curve([(cx + k * 20, -236), (cx + k * 28, -150)], s['bottom_sh'], 3, clip=True, alpha=1)
        a.rrect(cx - hw, -250, cx + hw, -232, 8, s['bottom_sh'])
    return _fin(a, 0, -215)

# ------------------------------------------------------------------ limbs (drawn straight down from the joint at origin)
def upperarm_part(s):
    a = _new(-50, -30, 50, 130)
    a.capsule((0, 0), (0, LIM['upper']), 20, 19, s['skin'])
    a.capsule((0, -2), (0, 50), 26, 25, s['shirt'])
    a.rrect(-25, 40, 25, 54, 6, s['shirt_sh'])
    a.ellipse((14, 20), 8, 30, s['shirt_sh'], clip=True, alpha=.5)
    a.ellipse((10, 78), 6, 16, s['skin_sh'], clip=True, alpha=.45)
    return _fin(a, 0, 0)

def forearm_part(s):
    a = _new(-40, -30, 40, 120)
    a.capsule((0, 0), (0, LIM['fore']), 18, 15, s['skin'])
    a.ellipse((10, 40), 6, 28, s['skin_sh'], clip=True, alpha=.4)
    return _fin(a, 0, 0)

def hand_part(s, kind):
    a = _new(-50, -20, 50, 90)
    sk, sh = s['skin'], s['skin_sh']
    a.ellipse((0, 2), 15, 14, sk)                                              # wrist cuff overlap
    if kind == 'relaxed':
        a.ellipse((0, 22), 16, 22, sk); a.capsule((-11, 12), (-15, 38), 7, 6, sk)   # palm + thumb (toward body = -x)
        a.curve([(4, 30), (4, 42)], sh, 2.5, clip=True)
    elif kind == 'open':
        a.ellipse((0, 20), 19, 17, sk)
        for ang in (-26, -9, 9, 26):
            t = np.radians(ang); p0 = (np.sin(t) * 6, 24); p1 = (np.sin(t) * 6 + np.sin(t) * 36, 24 + np.cos(t) * 36)
            a.capsule(p0, p1, 6.5, 5.5, sk)
        a.capsule((-14, 18), (-34, 36), 7.5, 6, sk)
    elif kind == 'fist':
        a.ellipse((0, 24), 19, 19, sk)
        for i in range(4): a.ellipse((-12 + i * 8, 40), 6.5, 7, sk)
        for i in range(3): a.curve([(-8 + i * 8, 36), (-8 + i * 8, 44)], sh, 2, clip=True)
        a.capsule((-12, 18), (-4, 38), 7, 6.5, sk)
    elif kind == 'point':
        a.ellipse((0, 22), 18, 17, sk)
        for i in range(3): a.ellipse((-4 + i * 8, 40), 6.5, 7, sk)
        a.capsule((8, 22), (14, 66), 6.5, 5.5, sk)
        a.capsule((-12, 16), (-4, 34), 7, 6.5, sk)
    return _fin(a, 0, 0)

def thigh_part(s):
    a = _new(-50, -40, 50, 130)
    a.capsule((0, 0), (0, LIM['thigh']), 22, 20, s['skin'])
    if s['kind'] == 'boy':
        a.rrect(-31, -10, 31, 66, 12, s['bottom'])
        a.rrect(-31, 52, 31, 66, 6, s['bottom_sh'])
        a.ellipse((18, 20), 12, 44, s['bottom_sh'], clip=True, alpha=.4)
    else:
        a.ellipse((12, 70), 6, 20, s['skin_sh'], clip=True, alpha=.4)
    return _fin(a, 0, 0)

def shin_part(s):
    a = _new(-40, -30, 40, 120)
    a.capsule((0, 0), (0, LIM['shin']), 20, 16, s['skin'])
    a.rrect(-19, 32, 19, 86, 10, s['sock'])
    a.rrect(-19, 32, 19, 44, 5, s['shoe'], clip=True, alpha=.9)
    a.ellipse((9, 66), 6, 22, (0, 0, 0), clip=True, alpha=.06)
    return _fin(a, 0, 0)

def shoe_part(s, view):
    a = _new(-60, -30, 110, 50)
    if view == 'front':   # right foot, toe slightly outward (+x)
        a.rrect(-26, -4, 34, 32, 15, s['shoe'])
        a.rrect(-27, 25, 35, 36, 6, (250, 250, 250))
        a.ellipse((12, 8), 15, 9, s['shoe_hi'], clip=True, alpha=.8)
        a.rrect(-18, -6, 18, 6, 4, s['shoe_hi'], clip=True, alpha=.0)
        a.curve([(-14, 2), (10, 2)], (255, 255, 255), 3, clip=True, alpha=.9)
    else:
        a.poly([(-26, -6), (14, -8), (22, 6), (58, 12), (74, 24), (70, 36), (-30, 36), (-34, 12)], s['shoe'])
        a.ellipse((52, 24), 22, 11, s['shoe_hi'], clip=True, alpha=.7)
        a.rrect(-34, 27, 76, 36, 5, (250, 250, 250))
        a.rrect(-22, -8, 16, 4, 3, (255, 255, 255), clip=True, alpha=.9)
    return _fin(a, 0, 0)

HAND_KINDS = ['relaxed', 'open', 'fist', 'point']

def build_parts(spec_name, view):
    s = SPECS[spec_name]; P = {}
    P['head'] = head_part(s, view)
    P['torso'] = torso_part(s, view); P['pelvis'] = pelvis_part(s, view)
    P['upperarm'] = upperarm_part(s); P['forearm'] = forearm_part(s)
    for k in HAND_KINDS: P['hand_' + k] = hand_part(s, k)
    P['thigh'] = thigh_part(s); P['shin'] = shin_part(s); P['shoe'] = shoe_part(s, view)
    if s['kind'] == 'boy': P['tuft'] = tuft_part(s)
    else: P['pigtail'] = pigtail_part(s)
    return P
