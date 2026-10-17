"""Pose tables for every animation. Poses are plain dicts (see penguin.default_pose); keyframed animations are eased between keys."""
import copy, numpy as np
from sdf3d import *
import penguin as P
GS = P.GS

def new(**kw):
    p = P.default_pose()
    for k, v in kw.items(): p[k] = v
    return p
def gdict(pos, pitch=0., yaw=0., roll=0., parent='body'): return dict(pos=pos, pitch=pitch, yaw=yaw, roll=roll, parent=parent)
def gloc(g): return local(Ry(D(g['yaw'])) @ Rx(D(-g['pitch'])) @ Rz(D(g['roll'])), g['pos'])
def gpt(g, pt, mag_off=(0, 0, 0)): return gloc(g).ap(V(*pt) * GS + V(*mag_off) * GS)

READY = gdict((8.0, 14.5, 8.0), pitch=-6, yaw=11)
AIM = gdict((8.0, 15.4, 7.5), pitch=0, yaw=11)
RUNG = gdict((7.0, 15.0, 8.5), pitch=-7, yaw=9)

def sm(t): return t * t * (3 - 2 * t)
def lerp(a, b, t):
    if isinstance(a, dict) and isinstance(b, dict): return {k: lerp(a[k], b[k], t) for k in a}
    if isinstance(a, (int, float, np.floating)) and isinstance(b, (int, float, np.floating)) and not isinstance(a, bool): return a + (b - a) * t
    if isinstance(a, (tuple, list, np.ndarray)) and isinstance(b, (tuple, list, np.ndarray)) and len(a) == len(b) and len(a) and isinstance(a[0], (int, float, np.floating)):
        r = np.array(a, float) + (np.array(b, float) - np.array(a, float)) * t
        return tuple(r) if isinstance(a, tuple) else (list(r) if isinstance(a, list) else r)
    return a if t < 1 else b
def keyed(keys, n):
    out = []
    for f in range(n):
        ks = [k for k, _ in keys]
        if f in ks: out.append(copy.deepcopy(dict(keys)[f])); continue
        i = max(j for j, k in enumerate(ks) if k < f); a, b = keys[i], keys[i + 1]
        t = sm((f - a[0]) / (b[0] - a[0])); out.append(lerp(a[1], b[1], t))
    return out

def hands(p, lg=None, rg=None):
    g = p['gun']; p['lh'] = tuple(gpt(g, P.FORE / GS)) if lg is None else lg; p['rh'] = tuple(gpt(g, P.GRIP / GS)) if rg is None else rg
    return p

# ----------------------------------------------------------------------------------------------- idle
def idle(n=6):
    out = []
    for k in range(n):
        ph = 2 * np.pi * k / n; br = np.sin(ph)
        p = new(bob=.35 * br, squash=1 + .018 * br, head=(1.2 * np.sin(ph - .8), 3 * np.sin(ph - .4), 1.5 * np.sin(ph)), roll=1.0 * np.sin(ph),
                gun=gdict((5.5, 13.5 + .5 * br, 8.5), pitch=-6 + 1.2 * br), band=(ph, .5), eyes='closed' if k == 4 else 'open')
        out.append(hands(p))
    return out

# ----------------------------------------------------------------------------------------------- walk / run
def gait(n, stride, lift, bob, lean, roll, twist, gun, bandamp, headtilt=1.0, toe=30):
    out = []
    for k in range(n):
        ph = 2 * np.pi * k / n; c, s = np.cos(ph), np.sin(ph)
        zl, zr = stride * s, -stride * s
        ll, lr = lift * max(0, c), lift * max(0, -c)
        pl, pr = -toe * max(0, c) * (1 if s > 0 else 0.4) + 10 * max(0, -c) * 0, -toe * max(0, -c)
        g = dict(gun); g['pos'] = (g['pos'][0], g['pos'][1] + .55 * bob * abs(c) * 0 + .4 * s * 0, g['pos'][2])
        g['pitch'] = g['pitch'] + 2.0 * np.cos(2 * ph + 1.0) ; g['yaw'] = 2.0 * s
        p = new(bob=bob * abs(c), lean=lean, roll=-roll * c, twist=twist * s, head=(-lean * .6 + .8 * np.cos(2 * ph), -twist * s * .8, roll * c * .55 * headtilt),
                fl=(-4.8, ll, 3.5 + zl), fr=(4.8, lr, 3.5 + zr), fl_pitch=pl, fr_pitch=pr, gun=g, band=(ph * 1.0 + 1.0, bandamp), tail=s)
        out.append(hands(p))
    return out
def walk(n=8): return gait(n, 5.0, 2.8, 1.5, 3, 6.5, 3.0, READY, 1.0)
def run(n=8): return gait(n, 8.0, 4.4, 2.6, 15, 4.5, 5.0, RUNG, 2.4, toe=45)

# ----------------------------------------------------------------------------------------------- shoot (loop of 4 shots-frames)
def shoot(n=4):
    spec = [dict(rz=-3.4, rp=4.0, fl=1.0, lean=-4.0, bolt=2.8, cs=[0.0]), dict(rz=-1.5, rp=1.8, fl=.55, lean=-2.2, bolt=1.2, cs=[1.0]),
            dict(rz=-.4, rp=.5, fl=0, lean=-.8, bolt=0, cs=[2.0]), dict(rz=0, rp=0, fl=0, lean=0, bolt=0, cs=[3.0])]
    out = []
    for k, sp in enumerate(spec[:n]):
        g = gdict((8.0, 15.4 + .2 * sp['rp'], 7.5 + sp['rz']), pitch=sp["rp"], yaw=11)
        ages = [a for a in sp['cs'] if a > 0]
        p = new(lean=sp['lean'], bob=-.3 * sp['fl'], head=(1.5 * sp['fl'], 0, 0), gun=g, flash=sp['fl'], bolt=sp['bolt'], casing_ages=ages,
                twist=-1.0, band=(k * .8, 1.2), foot_yaw=(0, 0), fl=(-5.5, 0, 0), fr=(5.5, 0, 2.5), eyes='open')
        out.append(hands(p))
    return out

# ----------------------------------------------------------------------------------------------- reload
def reload(n=16):
    R0 = hands(new(gun=READY, fl=(-5.5, 0, 0.5), fr=(5.5, 0, 2.0), eyes='open'))
    g1 = gdict((4.5, 14.2, 7.0), pitch=26, roll=-8); g2 = gdict((4.2, 14.4, 6.6), pitch=30, roll=-10)
    magc = (0, -7.4, 4.4)
    # key poses
    k0 = copy.deepcopy(R0)
    k1 = hands(new(gun=g1, lean=-1.5, head=(14, 0, 0), fl=(-5.5, 0, 0.5), fr=(5.5, 0, 2.0)))                      # raise & look down at the mag
    k2 = hands(new(gun=g2, lean=-1.5, head=(16, 0, 0), fl=(-5.5, 0, .5), fr=(5.5, 0, 2.0)), lg=tuple(gpt(g2, magc) + V(-1.5, .4, 0)))  # left flipper to mag
    k3 = hands(new(gun=g2, lean=-1.5, head=(16, 0, 0), fl=(-5.5, 0, .5), fr=(5.5, 0, 2.0), mag=dict(off=(0, -.8, 1.2), pitch=14, vis=True, parent='gun', rootpos=(0, 0, 0))),
               lg=tuple(gpt(g2, magc, (0, -.8, 1.2)) + V(-1.5, .4, 0)))                                                  # mag released (rocks forward)
    k4 = hands(new(gun=g2, lean=-1.5, head=(14, 0, 0), fl=(-5.5, 0, .5), fr=(5.5, 0, 2.0), mag=dict(off=(0, -9.0, 3.0), pitch=22, vis=True, parent='gun', rootpos=(0, 0, 0))),
               lg=tuple(gpt(g2, magc, (0, -9.0, 3.0)) + V(-1.5, .4, 0)))                                                 # pulled out
    pouchL = (-4.8, 11.0, 11.3)
    out = []
    keys = [(0, k0), (1, k1), (3, k2), (4, k3), (6, k4)]
    base = keyed(keys, 7)
    out += base                                            # frames 0..6
    # mag world position when it leaves the gun (root frame)
    # frame 7: mag falls (root frame), left flipper goes to the pouch
    from sdf3d import Frame
    def dropped(y, pitch, off=(0, 0, 0)):
        return dict(off=(0, 0, 0), pitch=pitch, vis=True, parent='root', rootpos=(9.0 + off[0], y, 4.0 + off[2]))
    f7 = hands(new(gun=g2, lean=-1.0, head=(14, 0, 0), fl=(-5.5, 0, .5), fr=(5.5, 0, 2.0), mag=dropped(9.5, 30)), lg=tuple(V(-6, 13, 11.5)))
    f8 = hands(new(gun=gdict((4.4, 14.3, 7.2), pitch=24, roll=-8), lean=-1.0, head=(12, 0, 0), fl=(-5.5, 0, .5), fr=(5.5, 0, 2.0), mag=dropped(1.9, 85, (.8, 0, 1.5))), lg=tuple(V(*pouchL)))
    f9 = hands(new(gun=gdict((4.4, 14.3, 7.2), pitch=24, roll=-8), lean=-1.0, head=(10, 0, 0), fl=(-5.5, 0, .5), fr=(5.5, 0, 2.0), mag=dict(off=(0, 0, 0), pitch=0, vis=False, parent='gun', rootpos=(0, 0, 0)),
                    mag2=dict(parent='body', pos=tuple(V(*pouchL) + V(-.5, .8, -.5)), pitch=8)), lg=tuple(V(*pouchL)))
    # frame 10: new mag carried toward magwell; 11: aligned below; 12: inserted + slap; 13: left flipper to charging handle & pull; 14: release; 15: ready
    gI = gdict((4.3, 16.8, 7.0), pitch=26, roll=-8)
    def carry(t):
        a = V(*pouchL) + V(-.5, .8, -.5); b = gloc(gI).ap(V(0, -6.5, 1.6) * GS)
        return tuple(a + (b - a) * t)
    f10 = hands(new(gun=gI, lean=-1.0, head=(12, 0, 0), fl=(-5.5, 0, .5), fr=(5.5, 0, 2.0), mag=dict(off=(0, 0, 0), pitch=0, vis=False, parent='gun', rootpos=(0, 0, 0)),
                    mag2=dict(parent='body', pos=carry(.6), pitch=14)), lg=tuple(np.array(carry(.6)) + V(-1.4, 1.2, 0)))
    gp = tuple(gpt(gI, (0, 0, 0)) * 0)
    mg11 = tuple(gloc(gI).ap(V(0, -3.2, 0) * GS))
    f11 = hands(new(gun=gI, lean=-1.0, head=(12, 0, 0), fl=(-5.5, 0, .5), fr=(5.5, 0, 2.0), mag=dict(off=(0, -3.0, 0.8), pitch=10, vis=True, parent='gun', rootpos=(0, 0, 0))),
                lg=tuple(gpt(gI, magc, (0, -3.0, 0.8)) + V(-1.5, .4, 0)))
    f12 = hands(new(gun=gdict((4.5, 15.8, 7.4), pitch=22, roll=-6), lean=-1.0, head=(10, 0, 0), fl=(-5.5, 0, .5), fr=(5.5, 0, 2.0), mag=dict(off=(0, 0, 0), pitch=0, vis=True, parent='gun', rootpos=(0, 0, 0))),
                lg=tuple(gpt(gdict((4.5, 15.8, 7.4), pitch=22, roll=-6), magc) + V(-1.5, .4, 0)))
    gC = gdict((4.8, 14.0, 7.6), pitch=12, roll=-4)
    chp = lambda g, pull: tuple(gpt(g, (2.4, 3.6, .5 - pull)))
    f13 = hands(new(gun=gC, lean=-.5, head=(6, 0, 0), fl=(-5.5, 0, .5), fr=(5.5, 0, 2.0), bolt=5.0), lg=chp(gC, 5.0))
    gR = gdict((5.2, 13.8, 8.2), pitch=-2)
    f14 = hands(new(gun=gR, lean=0, head=(2, 0, 0), fl=(-5.5, 0, .5), fr=(5.5, 0, 2.0), bolt=0.0), lg=tuple(gpt(gR, (2.4, 3.6, .5))))
    f15 = copy.deepcopy(R0)
    out += [f7, f8, f9, f10, f11, f12, f13, f14, f15]
    for i, p in enumerate(out): p['band'] = (i * .5, .8)
    return out

# ----------------------------------------------------------------------------------------------- hit
def hit(n=7):
    spec = [dict(lean=-5, h=-14, hurt=1, ba=0.0, gp=3, e='wide'), dict(lean=-11, h=-24, hurt=1, ba=1.0, gp=8, e='wide'), dict(lean=-13, h=-22, hurt=0, ba=2.0, gp=9, e='closed'),
            dict(lean=-9, h=-14, hurt=0, ba=3.0, gp=6, e='closed'), dict(lean=-4, h=-6, hurt=0, ba=4.0, gp=3, e='open'), dict(lean=-1, h=-2, hurt=0, ba=None, gp=0, e='open'), dict(lean=0, h=0, hurt=0, ba=None, gp=-3, e='open')]
    out = []
    for k, sp in enumerate(spec[:n]):
        g = gdict((5.5, 13.5 + .35 * sp['gp'], 8.5 - .25 * sp['gp']), pitch=-6 + sp['gp'] * 1.3, roll=-sp['gp'] * .8)
        p = new(lean=sp['lean'], bob=.7 if k in (1, 2) else 0, head=(sp['h'], 0, -sp['gp'] * .6), roll=-1.2 * sp['gp'] * (1 if k % 2 else -1) * .3, gun=g, hurt=sp['hurt'], eyes=sp['e'],
                blood=(sp['ba'], 11, 1.0) if sp['ba'] is not None else None, fl=(-5.5, 0, .5 - .35 * abs(sp['lean']) * .2), fr=(5.5, 0, 2.0 - .25 * abs(sp['lean']) * .2), band=(k * .9, 2.0 if k < 4 else 1.0), twist=-sp['gp'] * .4)
        out.append(hands(p))
    return out

# ----------------------------------------------------------------------------------------------- death
DEATH_SHIFT = {180: -2, 0: 25, 90: 15, 270: 15}      # per facing: keeps the lying body inside the 64 px frame
def death(yaw, n=16):
    out = []
    shift = DEATH_SHIFT[yaw]
    leans = [-6, -12, -22, -36, -54, -73, -91, -100, -93, -90, -90, -90, -90, -90, -90, -90]
    bobs = [.3, .5, 1.0, 1.4, 1.7, 2.2, 3.1, 3.9, 3.3, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2, 3.2]
    heads = [-14, -22, -28, -22, -14, -8, 6, 14, 4, 0, 0, 0, 0, 0, 0, 0]
    gun_root = {  # frame: (pos in root frame (right, up, forward), pitch, roll)
        3: ((5.5, 16, 6), 18, 40), 4: ((8.5, 17, 2), 14, 120), 5: ((11.5, 16, -4), 4, 230), 6: ((13.5, 14, -12), 5, 330), 7: ((15, 5.0, -17), 0, 410), 8: ((15.5, 3.3, -18), 0, 440)}
    for f in range(n):
        s = sm(min(f / 7.0, 1.0)); fe = f - 6
        fw = DEATH_SHIFT[yaw] * s
        ground = min(1.0, max(0.0, (f - 5) / 2.0))
        # feet flail while falling then flop
        fl_y = 3.0 * np.sin(np.pi * np.clip((f - 1) / 6.0, 0, 1)) + (0.8 if f >= 8 else 0); fr_y = 3.4 * np.sin(np.pi * np.clip((f - 1.5) / 6.0, 0, 1)) + (0.5 if f >= 8 else 0)
        zf = -5 * s
        eyes = 'wide' if f < 3 else ('open' if f < 5 else 'closed')
        if f <= 2: g = gdict((5.5, 13.5 + .35 * (3 + 3 * f), 8.5 - .6 * f), pitch=-6 + 12 * f, roll=-3 * f); gpar = 'body'
        else:
            pos, gp_, gr_ = gun_root[min(f, 8)]; g = gdict(pos, pitch=gp_, roll=gr_, parent='root'); gpar = 'root'
        p = new(lean=leans[f], bob=bobs[f], head=(heads[f], 0, 0), pivot=(0, 0, -6), off=(0, fw), hurt=1 if f < 2 else 0, eyes=eyes, gun=g,
                fl=(-5.0 - 1.0 * s, fl_y, 1 + zf), fr=(5.0 + 1.0 * s, fr_y, 1 + zf + 1), fl_pitch=-30 * s, fr_pitch=-34 * s, band=(f * .7, 1.6 * (1 - ground) + .3),
                blood=(f * 1.0, 5) if f < 6 else None, squash=1.0)
        if f <= 2: hands(p)
        else:
            # flippers fly up, then drop to the sides
            up = {3: 0, 4: 0, 5: 0}
            w = 1 - ground
            lh = V(-12, 24, 3) * w + V(-19, 11.5, -2) * (1 - w); rh = V(12, 24, 3) * w + V(19, 11.5, -2) * (1 - w)
            if f >= 9: lh = V(-19.5, 11, -3.5); rh = V(19.5, 11, -3.5)
            if f in (10, 12): lh = lh + V(0, .8, 0)
            p['lh'] = tuple(lh); p['rh'] = tuple(rh)
        mag_drop = {3: (7, 17, 3), 4: (10, 20, 0), 5: (-9, 12, -5)}
        p['mag'] = dict(off=(0, 0, 0), pitch=0, vis=(f <= 2), parent='gun', rootpos=(0, 0, 0))
        if f >= 3:
            mp = {3: ((-6, 17, 6), 40), 4: ((-9, 20, 3), 80), 5: ((-12, 12, -2), 120), 6: ((-14, 4.5, -6), 160), 7: ((-14, 2.2, -8), 180)}
            if f >= 3:
                pos, pit = mp[min(f, 7)]
                p['mag'] = dict(off=(0, 0, 0), pitch=pit, vis=True, parent='root', rootpos=pos)
        if f >= 6: p['pool'] = min(1.0, (f - 5) / 7.0) * 1.0; p['pool_c'] = (0, fw - 17)
        out.append(p)
    return out

ANIMS = {   # name: (frames-fn, duration ms/frame, loop)
    'idle': (lambda y: idle(), 140, True), 'walk': (lambda y: walk(), 90, True), 'run': (lambda y: run(), 65, True),
    'shoot': (lambda y: shoot(), 60, True), 'reload': (lambda y: reload(), 95, False), 'hit': (lambda y: hit(), 70, False), 'death': (lambda y: death(y), 100, False)}
DIRS = {'down': 180, 'up': 0, 'right': 90, 'left': 270}

def cx_for(name, yaw):
    if name == 'death': return 32
    return {90: 29, 270: 35}.get(yaw, 32)
