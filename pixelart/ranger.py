"""RANGER - sci-fi space ranger, top-down (3/4) pixel art, 32x32 frames, 4 directions: idle / walk / shoot.
Procedural pixel rig: parts are integer-grid masks; every pose is re-drawn (not tweened) so each frame is clean pixel art."""
import numpy as np
from pxlib import Mat, Canvas, hexrgb

# ---- palette (every colour is used through ramps: outline / shadow / base / light / highlight) ------------------
MATS = [
    Mat('armor',  ['#161d33', '#2b3d63', '#4668a0', '#7ba3d6', '#bfe0f7']),   # steel blue suit
    Mat('orange', ['#4a1d19', '#9c3a1c', '#e0701f', '#ffa43a', '#ffd78a']),   # accents
    Mat('visor',  ['#08303f', '#14707f', '#2fd2de', '#8ff3f0', '#f2ffff']),   # glass
    Mat('under',  ['#0e111c', '#1d2234', '#323a52', '#505b78', '#7c88a6']),   # undersuit / gloves / pack
    Mat('metal',  ['#10131c', '#2a303d', '#505a6c', '#8793a8', '#c9d3e2']),   # gun
    Mat('glow',   ['#0f4d5e', '#1fa7b8', '#5ff0f0', '#c8ffff', '#ffffff']),   # energy
]
ARM, ORG, VIS, UND, MET, GLW = range(6)
DIRS = ['down', 'up', 'right', 'left']

def pose_walk(i, n=6):
    """per-frame params (px). legs: lift of each foot, swing (side view), bob, arm swing"""
    ph = i / n
    s = np.sin(2 * np.pi * ph); c = np.cos(2 * np.pi * ph)
    bob = -1 if (i % 3 == 1) else 0                    # up on the passing frames
    return dict(bob=bob, lift_l=max(0, round(2 * s)) if s > 0.3 else 0, lift_r=max(0, round(-2 * s)) if s < -0.3 else 0,
                swing=int(round(3 * c)), armsw=int(round(2 * s)))
WALK = [dict(bob=0, lift_l=0, lift_r=2, swing=3, armsw=-1), dict(bob=-1, lift_l=0, lift_r=1, swing=1, armsw=0), dict(bob=0, lift_l=0, lift_r=0, swing=0, armsw=1),
        dict(bob=0, lift_l=2, lift_r=0, swing=-3, armsw=1), dict(bob=-1, lift_l=1, lift_r=0, swing=-1, armsw=0), dict(bob=0, lift_l=0, lift_r=0, swing=0, armsw=-1)]
IDLE = [dict(bob=0), dict(bob=0), dict(bob=1), dict(bob=1)]            # 4-frame breathing (slow loop)
SHOOT = [dict(bob=0, aim=1), dict(bob=0, aim=2), dict(bob=1, aim=3), dict(bob=0, aim=1)]

def draw(dirn, pose, shadow=True):
    flip = dirn == 'left'; cv = Canvas(MATS, flip=flip)
    b = pose.get('bob', 0)
    if shadow: cv.shadow_ell(15.5, 27, 8, 2)
    if dirn == 'down': front(cv, pose, b)
    elif dirn == 'up': back(cv, pose, b)
    else: side(cv, pose, b)
    cv.outline(); return cv

# ------------------------------------------------------------------------------------------------ shared parts
def legs_fb(cv, p, b):
    R = cv.rect; ll, lr = p.get('lift_l', 0), p.get('lift_r', 0)
    for x0, lift in ((12, ll), (16, lr)):
        cv.paint(R(x0, 21 - lift, x0 + 3, 24 - lift), ARM, lvl=1)                         # leg
        cv.paint(R(x0 + 1, 22 - lift, x0 + 2, 23 - lift), ARM, lvl=3, shade=False)        # knee plate
        cv.paint(R(x0, 25 - lift, x0 + 3, 27 - lift, cut=1), UND, lvl=2, edge=1)          # boot
        cv.paint(R(x0, 27 - lift, x0 + 3, 27 - lift), ORG, flat=2)                        # sole accent
        cv.dot(x0 + 1, 25 - lift, UND, 4)
def arms_fb(cv, p, b):
    R = cv.rect; a = p.get('armsw', 0)
    for x0, sw in ((8, a), (21, -a)):
        if x0 == 21 and p.get('aim'): continue
        cv.paint(R(x0, 16 + b + sw, x0 + 2, 21 + b + sw, cut=1), ARM, edge=1)
        cv.paint(R(x0, 21 + b + sw, x0 + 2, 23 + b + sw, cut=1), UND, edge=1)           # glove
def pads_fb(cv, p, b):
    for x0 in (8, 20): cv.paint(cv.rect(x0, 13 + b, x0 + 3, 16 + b, cut=1), ORG, edge=1)
    for x0 in (9, 21): cv.dot(x0, 14 + b, ORG, 4)


def flash(cv, cx, cy, size, vertical):
    """muzzle flash: size 2 = star, 1 = spark"""
    P = []
    if size >= 2:
        P = [(cx, cy), (cx + 1, cy), (cx - 1, cy + 1), (cx, cy + 1), (cx + 1, cy + 1), (cx + 2, cy + 1)] if vertical else \
            [(cx, cy), (cx, cy + 1), (cx + 1, cy - 1), (cx + 1, cy), (cx + 1, cy + 1), (cx + 1, cy + 2), (cx + 2, cy), (cx + 2, cy + 1)]
        for i, (x, y) in enumerate(P): cv.dotf(x, y, GLW, 4 if (x, y) in ((cx, cy + 1), (cx + 1, cy + 1)) else 3)
    elif size == 1:
        for (x, y) in ([(cx, cy), (cx + 1, cy)] if vertical else [(cx, cy), (cx, cy + 1)]): cv.dotf(x, y, GLW, 2)

def gun_front(cv, p, b):
    """aiming at the viewer: forearm crosses in front of the hip, gun points down-screen with a glowing muzzle"""
    R = cv.rect; aim = p.get('aim', 0)
    if not aim: return
    yo = -1 if aim == 3 else 0
    cv.paint(R(20, 16 + b, 23, 19 + b, cut=1), ARM, edge=1)                                # upper arm
    cv.paint(R(19, 20 + b + yo, 22, 22 + b + yo, cut=1), ARM, lvl=3, edge=1)               # forearm
    cv.paint(R(19, 22 + b + yo, 21, 23 + b + yo), UND, edge=1)                             # glove
    ln = 3 if aim == 1 else 4
    cv.paint(R(18, 23 + b + yo, 21, 23 + b + yo + ln - 1), MET, edge=1)                    # gun body, seen end-on
    cv.paint(R(19, 24 + b + yo, 20, 24 + b + yo), MET, lvl=1, shade=False)                 # barrel shadow
    my = 23 + b + yo + ln - 1
    cv.paint(R(19, my, 20, my), GLW, flat=3 if aim != 2 else 4)                            # muzzle
    if aim == 2:
        for (x, y) in ((17, my), (22, my), (18, my + 1), (21, my + 1)): cv.dotf(x, y, GLW, 3)
        cv.dotf(19, my + 1, GLW, 4); cv.dotf(20, my + 1, GLW, 4)

def gun_back(cv, p, b):
    R = cv.rect; aim = p.get('aim', 0)
    if not aim: return
    yo = 1 if aim == 3 else 0
    cv.paint(R(21, 11 + b + yo, 23, 16 + b + yo, cut=1), ARM, edge=1)
    cv.paint(R(21, 9 + b + yo, 24, 10 + b + yo), UND, edge=1)
    ln = 3 if aim == 1 else 5
    cv.paint(R(22, 9 + b + yo - ln, 24, 8 + b + yo), MET, edge=1)
    cv.paint(R(23, 9 + b + yo - ln, 23, 9 + b + yo - ln), GLW, flat=3)
    if aim == 2: flash(cv, 22, 1, 2, True)
    if aim == 3: flash(cv, 22, 2, 1, True)

def gun_side(cv, p, b):
    R = cv.rect; aim = p.get('aim', 0)
    if not aim: return
    xo = -1 if aim == 3 else 0
    cv.paint(R(13, 15 + b, 19 + xo, 17 + b, cut=1), ARM, lvl=3, edge=1)                    # arm stretched forward
    cv.paint(R(20 + xo, 15 + b, 21 + xo, 17 + b), UND, edge=1)
    ln = 4 if aim == 1 else 6
    cv.paint(R(22 + xo, 14 + b, 22 + xo + ln - 1, 17 + b), MET, edge=1)
    cv.paint(R(22 + xo + ln - 1, 15 + b, 22 + xo + ln - 1, 16 + b), GLW, flat=2)
    cv.paint(R(22 + xo, 18 + b, 23 + xo, 19 + b), MET, lvl=1, edge=1)                      # grip
    if aim == 2: flash(cv, 27 + xo, 14, 2, False)
    if aim == 3: flash(cv, 27 + xo, 15, 1, False)

# ------------------------------------------------------------------------------------------------ FRONT
def front(cv, p, b):
    R = cv.rect; E = cv.ell
    legs_fb(cv, p, b); arms_fb(cv, p, b)
    cv.paint(R(11, 13 + b, 20, 20 + b, cut=1), ARM, edge=1)
    cv.paint(R(13, 14 + b, 18, 18 + b, cut=1), ARM, lvl=3, edge=False)                  # chest plate
    cv.paint(R(14, 15 + b, 17, 17 + b), ARM, lvl=1, shade=False)                         # recess
    cv.paint(cv.pts((15, 16 + b), (16, 16 + b)), GLW, flat=3)                             # core light
    cv.paint(cv.pts((15, 15 + b), (16, 15 + b)), GLW, flat=1)
    cv.paint(R(11, 19 + b, 20, 19 + b), ORG, flat=3); cv.paint(R(11, 20 + b, 20, 20 + b), ORG, flat=1)                              # belt
    cv.paint(R(15, 19 + b, 16, 20 + b), MET, flat=3)                                     # buckle
    pads_fb(cv, p, b); gun_front(cv, p, b)
    cv.paint(E(15.5, 7.5 + b, 6, 5), ARM, edge=1, lvl=2)                                  # helmet
    cv.paint(R(14, 2 + b, 17, 3 + b), ORG, shade=False, flat=3)                            # crest
    cv.paint(R(9, 7 + b, 10, 9 + b), UND, edge=1); cv.paint(R(21, 7 + b, 22, 9 + b), UND, edge=1)   # ear pieces
    cv.paint(E(15.5, 8 + b, 4, 2), VIS, edge=1)                                           # visor
    cv.dot(12, 7 + b, VIS, 4); cv.dot(13, 7 + b, VIS, 4); cv.dot(12, 8 + b, VIS, 3); cv.dot(19, 9 + b, VIS, 1); cv.dot(18, 10 + b, VIS, 1)
    cv.dot(11, 4 + b, ARM, 4); cv.dot(12, 3 + b, ARM, 4)                                 # helmet specular

# ------------------------------------------------------------------------------------------------ BACK
def back(cv, p, b):
    R = cv.rect; E = cv.ell
    legs_fb(cv, p, b); arms_fb(cv, p, b)
    cv.paint(R(11, 13 + b, 20, 20 + b, cut=1), UND, lvl=2, edge=1)                       # backpack body
    for x0 in (12, 17):
        cv.paint(R(x0, 14 + b, x0 + 2, 19 + b, cut=1), ARM, edge=1)                       # tanks
        cv.paint(R(x0, 14 + b, x0 + 2, 14 + b), ORG, flat=3)
    cv.paint(cv.pts((15, 18 + b), (16, 18 + b)), GLW, flat=2)                             # status light
    cv.paint(R(11, 19 + b, 20, 19 + b), ORG, flat=3); cv.paint(R(11, 20 + b, 20, 20 + b), ORG, flat=1)
    pads_fb(cv, p, b); gun_back(cv, p, b)
    cv.paint(E(15.5, 7.5 + b, 6, 5), ARM, edge=1, lvl=2)
    cv.paint(R(15, 2 + b, 16, 8 + b), ORG, shade=False, flat=2); cv.dot(15, 2 + b, ORG, 3); cv.dot(15, 3 + b, ORG, 3)   # crest stripe down the back
    for yy in (9, 10): cv.paint(R(12, yy + b, 19, yy + b), ARM, flat=1)                    # vents
    cv.paint(R(9, 7 + b, 10, 9 + b), UND, edge=1); cv.paint(R(21, 7 + b, 22, 9 + b), UND, edge=1)
    cv.dot(11, 4 + b, ARM, 4); cv.dot(12, 3 + b, ARM, 4)

# ------------------------------------------------------------------------------------------------ SIDE (right-facing; left = flipped geometry, light stays top-left)
def side(cv, p, b):
    R = cv.rect; E = cv.ell
    sw = p.get('swing', 0) * 4 // 3; ll, lr = p.get('lift_l', 0), p.get('lift_r', 0); a = p.get('armsw', 0) * 3 // 2
    # far leg + far arm (mid-tone, no bevel) -----------------------------------------------------------------------
    xf = 13 - sw
    cv.paint(R(xf, 21 - ll, xf + 3, 24 - ll), ARM, lvl=0, shade=False)
    cv.paint(R(xf, 25 - ll, xf + 4, 27 - ll, cut=1), UND, lvl=1, shade=False, edge=1)
    cv.paint(R(xf, 27 - ll, xf + 4, 27 - ll), ORG, flat=1)
    if abs(a) >= 2:
        cv.paint(R(12 - a, 16 + b, 14 - a, 20 + b, cut=1), ARM, lvl=0, shade=False, edge=1)
        cv.paint(R(12 - a, 21 + b, 14 - a, 22 + b), UND, lvl=0, shade=False)
    # backpack -----------------------------------------------------------------------------------------------------
    cv.paint(R(8, 13 + b, 11, 21 + b, cut=1), UND, lvl=2, edge=1)
    cv.paint(R(8, 14 + b, 9, 19 + b), ARM, lvl=2, edge=False)                              # tank
    cv.paint(R(8, 13 + b, 11, 13 + b), ORG, flat=3); cv.paint(R(8, 20 + b, 11, 20 + b), ORG, flat=1)
    # near leg -----------------------------------------------------------------------------------------------------
    xn = 13 + sw
    cv.paint(R(xn, 21 - lr, xn + 3, 24 - lr), ARM, lvl=1)
    cv.paint(R(xn + 1, 22 - lr, xn + 3, 23 - lr), ARM, lvl=3, shade=False)                 # knee plate (front)
    cv.paint(R(xn, 25 - lr, xn + 4, 27 - lr, cut=1), UND, lvl=2, edge=1); cv.dot(xn + 1, 25 - lr, UND, 4)
    cv.paint(R(xn, 27 - lr, xn + 4, 27 - lr), ORG, flat=2)
    # torso --------------------------------------------------------------------------------------------------------
    cv.paint(R(11, 13 + b, 19, 20 + b, cut=1), ARM, edge=1)
    cv.paint(R(16, 14 + b, 18, 17 + b), ARM, lvl=3, shade=False); cv.paint(cv.pts((17, 15 + b)), GLW, flat=3)   # chest plate + light
    cv.paint(R(11, 19 + b, 19, 19 + b), ORG, flat=3); cv.paint(R(11, 20 + b, 19, 20 + b), ORG, flat=1)
    # near arm + pad -----------------------------------------------------------------------------------------------
    if p.get('aim'): gun_side(cv, p, b)
    else:
        cv.paint(R(12 + a, 16 + b, 14 + a, 20 + b, cut=1), ARM, lvl=3, edge=1)
        cv.paint(R(12 + a, 21 + b, 14 + a, 23 + b, cut=1), UND, lvl=3, edge=1)
    cv.paint(R(11, 13 + b, 15, 15 + b, cut=1), ORG, edge=1); cv.dot(12, 13 + b, ORG, 4); cv.dot(13, 13 + b, ORG, 4)
    # head ---------------------------------------------------------------------------------------------------------
    head = E(15.5, 7.5 + b, 6, 5)
    cv.paint(head, ARM, edge=1, lvl=2)
    cv.paint(R(12, 2 + b, 16, 3 + b) & head, ORG, shade=False, flat=3)
    cv.paint(R(12, 7 + b, 13, 8 + b), ORG, flat=2); cv.dot(12, 7 + b, ORG, 4)                 # ear cap
    cv.paint(R(15, 5 + b, 21, 9 + b, cut=1) & head, VIS, edge=1)                              # visor wraps the front
    cv.dot(16, 6 + b, VIS, 4); cv.dot(17, 6 + b, VIS, 4); cv.dot(16, 7 + b, VIS, 3); cv.dot(20, 9 + b, VIS, 1); cv.dot(19, 9 + b, VIS, 1)
    cv.dot(10, 5 + b, ARM, 4); cv.dot(11, 4 + b, ARM, 4)

def preview(path, k=6):
    from PIL import Image
    import numpy as np
    rows = []
    for d in DIRS:
        fr = [draw(d, IDLE[0]).rgba()] + [draw(d, w).rgba() for w in WALK]
        rows.append(np.hstack(fr))
    im = np.vstack(rows); from pxlib import save_scaled; save_scaled(im, path, k)

if __name__ == '__main__':
    preview('/tmp/rg_prev.png', 6)
