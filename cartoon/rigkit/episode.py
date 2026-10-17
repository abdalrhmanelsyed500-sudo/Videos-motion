"""Demo episode director: builds per-frame states (pose/face/root) for Zaki and Lulu, camera, and audio schedule."""
import math, os, json
import numpy as np
from . import anim, chars, face as F, build
from .anim import D2R, smooth, ease_io, ease_out, clamp, lerp, lerp_pose, env_window, Walker
from .rig import Rig

FPS = 30; W, H = 1920, 1080; S = 1.15; GY = 940
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCRIPT = dict(
    zaki_walk=(0.4, 5.0), x_zaki0=-1150.0, x_zaki=0.0,
    z1=6.3, l_walk=(12.9, 16.5), x_lulu0=1130.0, x_lulu=330.0,
    l1=17.5, z2=25.4, l2=27.7, jump=29.7, bye=31.2, end=33.4)

def kf(u, keys):
    """piecewise keyframe value: keys=[(u, v, ease)] easing for the segment ENDING at that key"""
    if u <= keys[0][0]: return keys[0][1]
    for i in range(1, len(keys)):
        if u <= keys[i][0]:
            u0, v0, _ = keys[i - 1]; u1, v1, e = keys[i]; return lerp(v0, v1, e((u - u0) / (u1 - u0)))
    return keys[-1][1]

def jump_profile(u, H_=105.0):
    """crouch -> push -> flight -> landing squash -> recover.  returns dict"""
    lin = lambda x: x
    dy = kf(u, [(0, 0, lin), (0.30, 52, ease_io), (0.40, -4, ease_out), (0.44, 0, ease_io), (0.95, 0, lin), (1.04, 44, ease_out), (1.40, 0, ease_out)])
    s = (u - 0.42) / 0.53
    h = H_ * 4 * s * (1 - s) if 0 < s < 1 else 0.0
    sy = kf(u, [(0, 1, lin), (0.30, 0.90, ease_io), (0.42, 1.10, ease_out), (0.60, 1.03, ease_io), (0.95, 1.04, lin), (1.04, 0.88, ease_out), (1.40, 1.0, ease_out)])
    sx = 1 / math.sqrt(sy)
    arms = kf(u, [(0, 0, lin), (0.26, 0.0, lin), (0.46, 1.0, ease_out), (0.95, 1.0, lin), (1.4, 0.0, ease_io)])
    tuck = math.sin(math.pi * clamp(s)) * 14 if 0 < s < 1 else 0.0
    return dict(dy=dy, h=h, sx=sx, sy=sy, arms=arms, tuck=tuck, air=0 < s < 1)

class Actor:
    def __init__(self, name, seed, root_dir):
        self.name = name; self.spec = chars.SPECS[name]
        self.rigs = {v: Rig(os.path.join(root_dir, f'{name}_{v}', 'rig.json')) for v in ('front', 'side')}
        self.blinks = anim.blink_times(seed, 40)
        self.states = []

class Episode:
    def __init__(self, rig_root, audio_dir, nframes=None):
        self.sc = SCRIPT
        self.n = int(self.sc['end'] * FPS) if nframes is None else nframes
        self.z = Actor('zaki', 3, rig_root); self.l = Actor('lulu', 11, rig_root)
        sc = self.sc
        self.zw = Walker(self.z.rigs['side'], +1, sc['x_zaki0'], sc['x_zaki'], sc['zaki_walk'][0], sc['zaki_walk'][1])
        self.lw = Walker(self.l.rigs['side'], -1, sc['x_lulu0'], sc['x_lulu'], sc['l_walk'][0], sc['l_walk'][1], Ts=0.36, swing=0.30, a=54.0)
        self.turn_z = self.zw.t_end + 0.25; self.turn_l = self.lw.t_end + 0.25
        # speech
        self.speech = {}
        for key, who, t0 in (('z1', 'z', sc['z1']), ('l1', 'l', sc['l1']), ('z2', 'z', sc['z2']), ('l2', 'l', sc['l2'])):
            mouth, env = anim.lipsync(os.path.join(audio_dir, key + '.wav'), FPS)
            self.speech[key] = dict(who=who, t0=t0, t1=t0 + len(mouth) / FPS - 0.05, mouth=mouth, env=env, pk=anim.peaks(env, FPS))
        self.events = []   # sound events
        self._build()

    # ------------------------------------------------------------ helpers
    def speaking(self, who, t):
        for k, sp in self.speech.items():
            if sp['who'] == who and sp['t0'] <= t < sp['t1']:
                i = min(int((t - sp['t0']) * FPS), len(sp['mouth']) - 1); return sp, i
        return None, 0

    def other_speaking(self, who, t):
        o = 'l' if who == 'z' else 'z'; sp, _ = self.speaking(o, t); return sp is not None

    def gestures(self, who):
        sc = self.sc; G = []
        if who == 'z':
            G.append(('wave', sc['z1'] + 0.15, sc['z1'] + 2.5, 'R'))
            G.append(('point', sc['z1'] + 6.35, sc['z1'] + 7.7, 'R'))
            G.append(('emph', sc['z2'] + 0.1, sc['z2'] + 1.5, 'L'))
            G.append(('wave', sc['bye'], sc['end'] - 0.2, 'L'))
        else:
            G.append(('wave', sc['l1'] + 0.1, sc['l1'] + 2.4, 'R'))
            G.append(('emph', sc['l2'] + 0.05, sc['l2'] + 1.4, 'R'))
            G.append(('wave', sc['bye'] + 0.15, sc['end'] - 0.2, 'R'))
        # emphasis gestures on speech peaks (skip when a scripted gesture is active)
        side = 0
        for k, sp in self.speech.items():
            if sp['who'] != who: continue
            for pk in sp['pk']:
                t = sp['t0'] + pk
                if pk < 2.4 and k in ('z1', 'l1'): continue
                if any(g[1] - .2 < t < g[2] for g in G): continue
                if k in ('z2', 'l2'): continue
                G.append(('emph', t - 0.25, t + 0.65, 'R' if side % 2 == 0 else 'L')); side += 1
        return G

    def arm_pose(self, kind, side, t, t0, t1):
        """pose dict for an arm gesture on `side` (R/L) at time t (before weight)"""
        g = -1.0 if side == 'R' else 1.0          # outward = negative rot on R, positive on L
        u = t - t0
        if kind == 'wave':
            osc = math.sin(2 * math.pi * 2.4 * u)
            up, lo, hr = D2R(112), D2R(68 + 24 * osc), D2R(10 * osc)
            return {f'arm{side}_up': {'rot': g * up}, f'arm{side}_lo': {'rot': g * lo}, f'hand{side}': {'rot': g * hr}}, {f'hand{side}': 'hand_open'}
        if kind == 'point':
            return {f'arm{side}_up': {'rot': g * D2R(80)}, f'arm{side}_lo': {'rot': g * D2R(6)}, f'hand{side}': {'rot': g * D2R(-8)}}, {f'hand{side}': 'hand_point'}
        osc = math.sin(2 * math.pi * 1.6 * u)       # emphasis
        return {f'arm{side}_up': {'rot': g * D2R(34 + 4 * osc)}, f'arm{side}_lo': {'rot': g * D2R(62 + 8 * osc)}, f'hand{side}': {'rot': g * D2R(6 * osc)}}, {f'hand{side}': 'hand_open'}

    # ------------------------------------------------------------ front-view state
    def front_state(self, A, who, t, x0):
        rig = A.rigs['front']; ph = 0.0 if who == 'z' else 1.7
        br = 0.012 * math.sin(2 * math.pi * t / 3.2 + ph)
        pose = {'spine': {'sy': 1 + br, 'rot': D2R(0.8) * math.sin(2 * math.pi * t / 5.3 + ph)},
                'head': {'rot': D2R(1.4) * math.sin(2 * math.pi * t / 4.1 + ph), 'ty': -2.0 * br * 100},
                'armR_up': {'rot': D2R(-4.0) + D2R(-1.0) * math.sin(2 * math.pi * t / 3.2 + ph)}, 'armL_up': {'rot': D2R(4.0) + D2R(1.0) * math.sin(2 * math.pi * t / 3.2 + ph + .5)},
                'armR_lo': {'rot': D2R(-7)}, 'armL_lo': {'rot': D2R(7)}, 'hips': {'rot': D2R(1.2) * math.sin(2 * math.pi * t / 6.0 + ph), 'ty': 0.0, 'tx': 3 * math.sin(2 * math.pi * t / 6.0 + ph)}}
        swap = {}; zov = {}
        face = dict(blinkL=anim.blink_value(t, A.blinks), blinkR=anim.blink_value(t, A.blinks), look=(0.0, 0.0), browL=(.15, 0), browR=(.15, 0), mouth=F.mix_vis(F.VISEMES['rest'], F.VISEMES['smile'], .5))
        # listening
        if self.other_speaking(who, t) and not self.speaking(who, t)[0]:
            w = 1.0; pose = anim.add_pose(pose, {'head': {'rot': D2R(3.5 * (1 if who == 'z' else -1))}}, w)
            face['look'] = (0.85 if who == 'z' else -0.85, 0.0); face['browL'] = face['browR'] = (.4, 0)
            sp, _ = self.speaking('l' if who == 'z' else 'z', t); 
            for pk in sp['pk']:
                tt = sp['t0'] + pk
                if tt - .1 < t < tt + .45: pose = anim.add_pose(pose, {'head': {'rot': 0, 'ty': 6 * math.sin(math.pi * (t - tt + .1) / .55)}})
        # watching the other character walk in
        if who == 'z' and self.sc['l_walk'][0] + 0.5 < t < self.turn_l + 0.3 and not self.speaking(who, t)[0]:
            ww = smooth((t - self.sc['l_walk'][0] - 0.5) / 0.4) * (1 - smooth((t - self.turn_l) / 0.3))
            face['look'] = (0.9 * ww, 0.0); face['browL'] = face['browR'] = (.15 + .3 * ww, 0)
            pose = anim.add_pose(pose, {'head': {'rot': D2R(3.0) * ww}})
        # speech
        sp, i = self.speaking(who, t)
        env = 0.0
        if sp:
            face['mouth'] = sp['mouth'][i]; env = float(sp['env'][i])
            pose = anim.add_pose(pose, {'head': {'rot': 0, 'ty': 5 * env, 'tx': 0}})
            b = face['browL'][0] + .35 * env; face['browL'] = face['browR'] = (b, 0.0)
            if (i % 71) < 3: pass
        # gestures
        gl = self.gestures(who)
        for (kind, t0, t1, side) in gl:
            w = env_window(t, t0, t1, .28, .30) if kind != 'wave' else env_window(t, t0, t1, .30, .35)
            if w <= 0: continue
            p, sw = self.arm_pose(kind, side, t, t0, t1)
            pose = lerp_pose(pose, {**pose, **p}, w)
            if w > .5: swap.update(sw)
            pose = anim.add_pose(pose, {'head': {'rot': D2R(4) * (1 if side == 'R' else -1) * w}})
            if kind == 'wave' and not sp: face['mouth'] = F.VISEMES['grin']
            if kind in ('wave', 'emph'): face['browL'] = face['browR'] = (max(face['browL'][0], .5 * w), .1)
            if kind == 'point': face['look'] = (0.9 if who == 'z' else -0.9, 0.0)
        # jump
        root = {'x': x0}; feet_h = 0.0; air = False; shadow = 1.0; tuck = 0.0
        sc = self.sc; tj = sc['jump'] + (0.0 if who == 'z' else 0.12); u = t - tj
        if u > -0.05 and u < 1.45:
            jp = jump_profile(u)
            pose['hips'] = {**pose.get('hips', {}), 'ty': pose['hips'].get('ty', 0) + jp['dy'], 'tx': 0.0}
            root.update(y=-jp['h'], sx=jp['sx'], sy=jp['sy']); feet_h = jp['h']; air = jp['air']; tuck = jp['tuck']
            a = jp['arms']
            pose = lerp_pose(pose, {**pose, 'armR_up': {'rot': D2R(-150)}, 'armL_up': {'rot': D2R(150)}, 'armR_lo': {'rot': D2R(-18)}, 'armL_lo': {'rot': D2R(18)}, 'handR': {'rot': 0}, 'handL': {'rot': 0}}, a)
            if a > .5: swap.update({'handR': 'hand_open', 'handL': 'hand_open'})
            face['mouth'] = F.VISEMES['laugh'] if 0.3 < u < 1.2 else face['mouth']
            face['squint'] = .5 * smooth((u - .3) / .2) * (1 - smooth((u - 1.0) / .3)); face['browL'] = face['browR'] = (.7, .0)
            shadow = 1.0 - clamp(jp['h'] / 160) * 0.6
        # legs: IK planted feet (front view), world targets
        for nm, g in (('L', -1), ('R', 1)):
            fx = x0 + g * 36; fy = -36 - (feet_h - tuck if air else 0.0)
            rig.ik2(pose, (f'leg{nm}_up', f'leg{nm}_lo', f'foot{nm}'), (fx, fy), bend=1, end_rot=0.0 if not air else D2R(g * -8), root=root)
        return dict(view='front', root=root, pose=pose, face=face, swap=swap, zov=({'upperarmR': 60, 'forearmR': 61, 'handR': 62, 'upperarmL': 60, 'forearmL': 61, 'handL': 62}), shadow=shadow, x=x0)

    def side_state(self, A, who, t, walker, d):
        rig = A.rigs['side']; rx, pose = walker.state(t)
        br = 0.012 * math.sin(2 * math.pi * t / 3.2)
        pose['spine']['sy'] = 1 + br
        face = dict(blinkL=anim.blink_value(t, A.blinks), blinkR=anim.blink_value(t, A.blinks), mouth=F.mix_vis(F.VISEMES['rest'], F.VISEMES['smile'], .6))
        if walker.t_lift0 - .3 < t < walker.t_stop: face['mouth'] = F.VISEMES['smile']; face['browR'] = (.25, 0)
        return dict(view='side', root={'x': rx, 'flip': d < 0}, pose=pose, face=face, swap={}, zov=None, shadow=1.0, x=rx)

    def turn_state(self, A, who, t, tt, walker, d, x0):
        """squash-swap turn side -> front over 0.30 s"""
        u = (t - tt) / 0.30
        if u < 0.5:
            st = self.side_state(A, who, t, walker, d); k = ease_io(u / 0.5)
            st['root']['sx'] = lerp(1.0, 0.10, k); st['root']['sy'] = 1 + 0.04 * k
            return st
        st = self.front_state(A, who, t, x0); k = ease_io((u - 0.5) / 0.5)
        st['root']['sx'] = lerp(0.10, 1.0, anim.ease_out_back(k, 1.2)) if 'sx' not in st['root'] else st['root']['sx']
        st['root']['sy'] = st['root'].get('sy', 1.0) * (1 + 0.04 * (1 - k))
        return st

    # ------------------------------------------------------------ build
    def _build(self):
        sc = self.sc; n = self.n
        for A, who in ((self.z, 'z'), (self.l, 'l')):
            A.states = []
            for i in range(n):
                t = i / FPS
                if who == 'z':
                    if t < self.turn_z: st = self.side_state(A, who, t, self.zw, +1)
                    elif t < self.turn_z + .30: st = self.turn_state(A, who, t, self.turn_z, self.zw, +1, sc['x_zaki'])
                    else: st = self.front_state(A, who, t, sc['x_zaki'])
                else:
                    if t < self.turn_l: st = self.side_state(A, who, t, self.lw, -1)
                    elif t < self.turn_l + .30: st = self.turn_state(A, who, t, self.turn_l, self.lw, -1, sc['x_lulu'])
                    else: st = self.front_state(A, who, t, sc['x_lulu'])
                st['t'] = t; A.states.append(st)
            self._secondary(A, who)
        self._camera()
        self._events()

    def _secondary(self, A, who):
        """spring secondary motion for tuft / pigtails driven by head acceleration (deterministic)"""
        P = []
        for st in A.states:
            rig = A.rigs[st['view']]; W = rig.world(st['pose'], st['root']); P.append(W['head'][:2, 2] + np.array([0, -300 * 0]))
        P = np.array(P); acc = anim.accel_from_positions(P, FPS)
        # light low-pass of acceleration to avoid single-frame spikes
        k = np.ones(3) / 3
        acc = np.stack([np.convolve(np.pad(acc[:, j], 1, mode='edge'), k, 'valid') for j in range(2)], 1)
        drive = [(a[0], a[1], 0.0) for a in acc]
        th_t = anim.spring_series(drive, FPS, k=150.0, c=8.5, gain=0.011)
        th_p = anim.spring_series(drive, FPS, k=95.0, c=6.0, gain=0.016, lim=D2R(55))
        for i, st in enumerate(A.states):
            flip = st['root'].get('flip', False); sg = -1 if flip else 1
            pose = st['pose']
            if A.spec['kind'] == 'boy': pose['tuft'] = {'rot': sg * th_t[i]}
            else:
                for nm in ('pigtailL', 'pigtailR'):
                    if st['view'] == 'side' and nm == 'pigtailL': continue
                    pose[nm] = {'rot': -sg * th_p[i] * (1 if nm == 'pigtailR' else 1)}
            # follow-through also when a bone is mirrored (front L slot is mirrored: rotation is applied in bone space, ok)

    def _camera(self):
        sc = self.sc; cam = []; x = sc['x_zaki0'] + 250; v = 0.0; w = 2.6
        for i in range(self.n):
            t = i / FPS
            if t < self.turn_z - .2: tgt = self.zw.root_x(t) + 250
            else: tgt = (sc['x_zaki'] + sc['x_lulu']) / 2 - 10
            a = -2 * w * v - w * w * (x - tgt); v += a / FPS; x += v / FPS; cam.append(x)
        self.cam = cam

    def _events(self):
        ev = []
        for who, wk in (('z', self.zw), ('l', self.lw)):
            for e in wk.events(): ev.append(dict(kind='step', t=e['t'], who=who, x=e['x'], vol=.8 if e['foot'] == 'R' else .65))
        for who, tt in (('z', self.turn_z), ('l', self.turn_l)): ev.append(dict(kind='pop', t=tt + .15, who=who, x=0))
        sc = self.sc
        for who, d in (('z', 0), ('l', .12)):
            tj = sc['jump'] + d
            ev.append(dict(kind='boing', t=tj + .42, who=who, x=0)); ev.append(dict(kind='thud', t=tj + .95, who=who, x=0))
        for who, tt in (('z', sc['z1'] + .15), ('l', sc['l1'] + .1), ('z', sc['bye']), ('l', sc['bye'] + .15)): ev.append(dict(kind='swish', t=tt, who=who, x=0))
        ev.append(dict(kind='chime', t=sc['l_walk'][0] - 0.2, who='l', x=0))
        self.ev = ev
