"""Builds rig.json + part PNGs for the front and side rigs of a character (data-driven, reproducible)."""
import json, os
from . import chars
from .vec import save_png

FACE_FRONT = dict(eyeL=(-46, -116), eyeR=(46, -116), browL=(-46, -163), browR=(46, -163), mouth=(0, -56))
FACE_SIDE = dict(eyeR=(60, -116), browR=(60, -161), mouth=(76, -54))
FAR_TINT = [0.80, 0.78, 0.86]

def skeleton(view):
    B = []
    def add(n, p, h, lim=None): B.append(dict(name=n, parent=p, head=list(h), limit=lim))
    add('root', None, (0, 0)); add('hips', 'root', (0, -215), [-25, 25]); add('spine', 'hips', (0, -215), [-30, 30])
    add('head', 'spine', (0, -392), [-40, 40]); add('tuft', 'head', (0, -597), [-70, 70])
    if view == 'front':
        add('pigtailL', 'head', (-112, -508), [-70, 70]); add('pigtailR', 'head', (112, -508), [-70, 70])
        for s, g in (('L', -1), ('R', 1)):
            add(f'arm{s}_up', 'spine', (g * 82, -372), [-45, 175] if g < 0 else [-175, 45])
            add(f'arm{s}_lo', f'arm{s}_up', (g * 82, -286), [-110, 150] if g < 0 else [-150, 110])
            add(f'hand{s}', f'arm{s}_lo', (g * 82, -206), [-70, 70])
            add(f'leg{s}_up', 'hips', (g * 36, -212), [-45, 60] if g < 0 else [-60, 45])
            add(f'leg{s}_lo', f'leg{s}_up', (g * 36, -116), [-130, 130])
            add(f'foot{s}', f'leg{s}_lo', (g * 36, -28), [-60, 60])
    else:
        add('pigtailR', 'head', (-98, -512), [-70, 70])
        for s, x in (('L', -3), ('R', 3)):
            add(f'arm{s}_up', 'spine', (x, -372), [-170, 60]); add(f'arm{s}_lo', f'arm{s}_up', (x, -286), [-150, 10])
            add(f'hand{s}', f'arm{s}_lo', (x, -206), [-70, 70])
            add(f'leg{s}_up', 'hips', (x, -212), [-90, 60]); add(f'leg{s}_lo', f'leg{s}_up', (x, -116), [-5, 150])
            add(f'foot{s}', f'leg{s}_lo', (x, -28), [-60, 60])
    return B

def slots(view, kind):
    S = []
    def add(name, part, bone, z, mirror=False, tint=None, dyn=None, offset=(0, 0)):
        S.append(dict(name=name, part=part, bone=bone, z=z, mirror=mirror, tint=tint, dyn=dyn, offset=list(offset)))
    S.append(dict(name='pelvis', part='pelvis', bone='hips', z=20, mirror=False, tint=None, dyn=None, offset=[0, 0]))
    S.append(dict(name='torso', part='torso', bone='spine', z=30, mirror=False, tint=None, dyn=None, offset=[0, 0]))
    S.append(dict(name='head', part='head', bone='head', z=50, mirror=False, tint=None, dyn=None, offset=[0, 0]))
    F = FACE_FRONT if view == 'front' else FACE_SIDE
    for k, off in F.items():
        add(k, None, 'head', 52 if k.startswith('eye') else 53 if k == 'mouth' else 54, dyn=k, offset=off)
    if kind == 'boy': add('tuft', 'tuft', 'tuft', 58)
    else:
        if view == 'front': add('pigtailL', 'pigtail', 'pigtailL', 46, mirror=True); add('pigtailR', 'pigtail', 'pigtailR', 46)
        else: add('pigtailR', 'pigtail', 'pigtailR', 46)
    for s in ('L', 'R'):
        far = view == 'side' and s == 'L'; t = FAR_TINT if far else None; dz = -100 if far else 0
        add(f'thigh{s}', 'thigh', f'leg{s}_up', 10 + dz, tint=t); add(f'shin{s}', 'shin', f'leg{s}_lo', 12 + dz, tint=t)
        add(f'shoe{s}', 'shoe', f'foot{s}', 14 + dz, tint=t, mirror=(view == 'front' and s == 'L'))
        add(f'upperarm{s}', 'upperarm', f'arm{s}_up', 40 + dz * 0 + (-60 if far else 0), tint=t)
        add(f'forearm{s}', 'forearm', f'arm{s}_lo', 42 + (-60 if far else 0), tint=t)
        add(f'hand{s}', 'hand_relaxed', f'hand{s}', 44 + (-60 if far else 0), tint=t, mirror=(view == 'side' or s == 'L'))
    return S

def write_rig(name, view, outdir):
    spec = chars.SPECS[name]; os.makedirs(outdir, exist_ok=True)
    P = chars.build_parts(name, view); parts = {}
    for k, (im, an) in P.items():
        save_png(im, os.path.join(outdir, f'{k}.png')); parts[k] = dict(image=f'{k}.png', anchor=[float(an[0]), float(an[1])], size=[im.shape[1], im.shape[0]])
    ik = {}
    if view == 'front':
        for s in 'LR':
            ik['leg' + s] = dict(chain=[f'leg{s}_up', f'leg{s}_lo', f'foot{s}'], bend=1); ik['arm' + s] = dict(chain=[f'arm{s}_up', f'arm{s}_lo', f'hand{s}'], bend=-1 if s == 'R' else 1)
    else:
        for s in 'LR':
            ik['leg' + s] = dict(chain=[f'leg{s}_up', f'leg{s}_lo', f'foot{s}'], bend=1); ik['arm' + s] = dict(chain=[f'arm{s}_up', f'arm{s}_lo', f'hand{s}'], bend=-1)
    rig = dict(name=f'{name}_{view}', character=name, view=view, ppu=chars.PPU, height_units=620, bones=skeleton(view), slots=slots(view, spec['kind']), parts=parts, ik=ik)
    json.dump(rig, open(os.path.join(outdir, 'rig.json'), 'w'), indent=1)
    return os.path.join(outdir, 'rig.json')

def build_all(outroot):
    paths = {}
    for n in chars.SPECS:
        for v in ('front', 'side'): paths[(n, v)] = write_rig(n, v, os.path.join(outroot, f'{n}_{v}'))
    return paths
