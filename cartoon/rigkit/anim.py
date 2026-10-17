"""Animation toolkit: easing, keyframe poses, state blending, blink scheduler, spring secondary motion,
audio lip-sync (envelope + spectral centroid) and phoneme-timeline mode, procedural side walk with foot-lock IK."""
import math, wave
import numpy as np
from .face import VISEMES, DEFAULT_FACE, mix_vis

D2R = math.radians
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def lerp(a, b, t): return a + (b - a) * t
def smooth(x): x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10)
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in(x): x = clamp(x); return x ** 3
def ease_out_back(x, s=1.70158): x = clamp(x) - 1; return x * x * ((s + 1) * x + s) + 1
def env_window(t, t0, t1, fin=0.15, fout=0.2):
    """0..1 weight: fade in from t0, fade out to t1"""
    if t <= t0 or t >= t1: return 0.0
    return min(smooth((t - t0) / max(fin, 1e-6)), smooth((t1 - t) / max(fout, 1e-6)))

# ------------------------------------------------------------------ state blending (poses & faces are nested dicts of numbers)
POSE_DEF = dict(rot=0.0, sx=1.0, sy=1.0, tx=0.0, ty=0.0)

def lerp_pose(a, b, w):
    out = {}
    for k in set(a) | set(b):
        pa, pb = a.get(k, {}), b.get(k, {}); d = {}
        for f in set(pa) | set(pb):
            d[f] = lerp(pa.get(f, POSE_DEF[f]), pb.get(f, POSE_DEF[f]), w)
        out[k] = d
    return out

def add_pose(a, b, w=1.0):
    out = {k: dict(v) for k, v in a.items()}
    for k, pb in b.items():
        d = out.setdefault(k, {})
        for f, v in pb.items():
            if f in ('sx', 'sy'): d[f] = d.get(f, 1.0) * (1 + (v - 1) * w)
            else: d[f] = d.get(f, 0.0) + v * w
    return out

def lerp_tree(a, b, w):
    if isinstance(a, dict): return {k: lerp_tree(a[k], b[k], w) if k in b else a[k] for k in a} | {k: b[k] for k in b if k not in a}
    if isinstance(a, (tuple, list)): return tuple(lerp_tree(x, y, w) for x, y in zip(a, b))
    return lerp(a, b, w)

def face_merge(base, over, w):
    f = dict(base)
    for k, v in over.items():
        if k not in f: f[k] = v
        elif k == 'mouth': f[k] = lerp_tree(f[k], v, w)
        else: f[k] = lerp_tree(f[k], v, w)
    return f

class Keys:
    """Keyframed pose track: frames=[(t, pose, easing)] ; easing applies to the segment ENDING at that key."""
    def __init__(self, frames): self.f = frames
    def at(self, t):
        f = self.f
        if t <= f[0][0]: return f[0][1]
        if t >= f[-1][0]: return f[-1][1]
        for i in range(1, len(f)):
            if t <= f[i][0]:
                t0, p0, _ = f[i - 1]; t1, p1, e = f[i]
                return lerp_pose(p0, p1, e((t - t0) / (t1 - t0)))

# ------------------------------------------------------------------ blink
def blink_times(seed, t_end, lo=2.0, hi=4.6):
    r = np.random.RandomState(seed); t = r.uniform(.6, 1.6); out = []
    while t < t_end:
        out.append(t)
        if r.rand() < .18: out.append(t + .28)
        t += r.uniform(lo, hi)
    return out

def blink_value(t, times, close=.07, hold=.04, opn=.11):
    for b in times:
        d = t - b
        if -1e-9 <= d < close + hold + opn:
            if d < close: return smooth(d / close)
            if d < close + hold: return 1.0
            return 1 - smooth((d - close - hold) / opn)
    return 0.0

# ------------------------------------------------------------------ spring secondary motion
def spring_series(drive, fps=30, k=140.0, c=9.0, gain=0.014, lim=D2R(40), sub=8):
    """Damped spring angle for each frame; drive = per-frame (ax, ay, arot) accelerations of the parent.
    Deterministic, stable (semi-implicit Euler with sub-steps)."""
    n = len(drive); th = 0.0; om = 0.0; out = np.zeros(n); h = 1.0 / fps / sub
    for i in range(n):
        ax, ay, ar = drive[i]
        for _ in range(sub):
            acc = -k * th - c * om - gain * ax * math.cos(th) * 1.0 + 0.5 * ar
            om += acc * h; th += om * h
            th = max(-lim, min(lim, th))
        out[i] = th
    return out

def accel_from_positions(P, fps=30):
    P = np.asarray(P, float); v = np.gradient(P, axis=0) * fps; a = np.gradient(v, axis=0) * fps
    return a

# ------------------------------------------------------------------ audio lip-sync
def read_wav(path):
    w = wave.open(path); sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if w.getnchannels() > 1: x = x.reshape(-1, w.getnchannels()).mean(1)
    return x, sr

def audio_features(x, sr, fps=30):
    n = int(len(x) / sr * fps) + 1; win = int(sr * 0.046); rms = np.zeros(n); cen = np.zeros(n)
    fr = np.fft.rfftfreq(win, 1 / sr); hann = np.hanning(win)
    for i in range(n):
        c = int((i + .5) / fps * sr); s = x[max(0, c - win // 2): c + win // 2]
        if len(s) < win: s = np.pad(s, (0, win - len(s)))
        rms[i] = np.sqrt(np.mean(s ** 2) + 1e-12)
        sp = np.abs(np.fft.rfft(s * hann)); cen[i] = (sp * fr).sum() / (sp.sum() + 1e-9)
    return rms, cen

def lipsync(path, fps=30, smile_bias=.22):
    """Returns (list of mouth-param dicts per frame, envelope 0..1 per frame)."""
    x, sr = read_wav(path); rms, cen = audio_features(x, sr, fps)
    db = 20 * np.log10(rms + 1e-9); ref = np.percentile(db, 96)
    e = np.clip((db - (ref - 34)) / 30, 0, 1)
    # attack / release smoothing
    s = np.zeros_like(e); prev = 0.0
    for i, v in enumerate(e):
        prev = prev + (v - prev) * (0.75 if v > prev else 0.45); s[i] = prev
    # closure: strong local dips between syllables -> lips meet (M) for >=1 frame
    out = []
    for i in range(len(e)):
        o = float(s[i]) ** 0.85
        c = cen[i]
        rnd = clamp((1300 - c) / 700) * (o > .25)
        wide = clamp((c - 1500) / 1800)
        open_ = o * (1.0 - .35 * wide) * (1 + .15 * rnd)
        closed = o < .10
        if closed: p = dict(VISEMES['M'])
        else:
            base = mix_vis(VISEMES['A'], VISEMES['E'], wide)
            base = mix_vis(base, VISEMES['O'], rnd * .85)
            p = dict(base); p['open'] = clamp(open_ * 1.05, .08, 1)
            p['teeth'] = base['teeth'] * (1 if p['open'] > .2 else .5)
        p['smile'] = clamp(p['smile'] + smile_bias * (1 - rnd), -1, 1)
        out.append(p)
    return out, s

def viseme_track(items, t, co=0.06):
    """Phoneme-timeline mode: items=[(t0,t1,name)] ; smooth co-articulation cross-fade of `co` seconds."""
    cur = VISEMES['rest']
    for i, (a, b, n) in enumerate(items):
        if a - co <= t <= b + co:
            v = VISEMES[n]
            w = smooth((t - (a - co)) / (2 * co)) if t < a + co else 1.0
            if t > b - co and i + 1 < len(items): w = 1 - smooth((t - (b - co)) / (2 * co)); v = mix_vis(VISEMES[items[i + 1][2]], VISEMES[n], w); w = 1
            return mix_vis(cur, v, w)
    return VISEMES['rest']

def peaks(env, fps=30, thr=.55, gap=.9):
    out = []; last = -9
    for i in range(1, len(env) - 1):
        if env[i] > thr and env[i] >= env[i - 1] and env[i] > env[i + 1] and i / fps - last > gap:
            out.append(i / fps); last = i / fps
    return out

# ------------------------------------------------------------------ procedural side walk (foot-lock IK)
LEG_UP, LEG_LO = 96.0, 80.0
LMAX = 0.985 * (LEG_UP + LEG_LO)
HIP_Y = -212.0; ANKLE_REST = -36.0

def ankle_height(th):
    """ankle height above ground for a foot rotated th (toe-down positive); sole bottom touches ground"""
    return 36 * math.cos(th) + (72 * math.sin(th) if th > 0 else 36 * math.sin(-th))

class Walker:
    """Side-view walk with exact foot locking. Direction d=+1 (right) or -1 (left).
    Steps alternate L(far) R(near) ...; every planted foot stays at the SAME world x until its next lift."""
    def __init__(self, rig, d, x0, x1, t0, t_end, Ts=0.40, swing=0.33, a=58.0, stand=22.0, lift=34.0, hz=240, geo=None, bend=1, arm_gain=1.15, arm_bend=14.0):
        self.rig, self.d, self.x0, self.t0 = rig, d, x0, t0
        self.geo = geo or dict(hip_y=HIP_Y, lmax=LMAX, ankle=ankle_height); self.bend = bend; self.arm_gain = arm_gain; self.arm_bend = arm_bend
        self.Ts, self.swing, self.a, self.stand, self.lift = Ts, swing, a, stand, lift
        self.t_lift0 = t0 + 0.14
        N = int(round((t_end - self.t_lift0 - swing) / Ts)) + 2
        if N % 2 == 0: N += 1
        self.N = N
        self.t_stop = self.t_lift0 + (N - 2) * Ts + swing            # right foot lands -> root stops
        self.t_close = self.t_lift0 + (N - 1) * Ts                  # left close-step lift
        self.t_end = self.t_close + swing
        self.x1 = x1
        # root path from speed profile (smooth ramps) integrated numerically
        ramp = 0.9 * Ts + 0.25; tU, tD = t0, self.t_stop
        T = tD - tU; v0 = (x1 - x0) / (T - ramp)             # avg ramp contributes half of each ramp
        self.hz = hz; ts = np.arange(t0 - 0.5, self.t_end + 1.0, 1.0 / hz); v = np.zeros_like(ts)
        for i, t in enumerate(ts):
            v[i] = v0 * smooth((t - tU) / ramp) * smooth((tD - t) / ramp) if tU <= t <= tD else 0.0
        # make sure distance matches exactly
        X = np.cumsum(v) / hz; tot = float(X[-1]); fac = (x1 - x0) / tot; X = X * fac; self.ts, self.X = ts, x0 + X
        self.v = v * fac
        self.v0 = abs(v0)
        self._plan(); self._hips_table()

    def root_x(self, t): return float(np.interp(t, self.ts, self.X))
    def speed(self, t): return float(np.interp(t, self.ts, self.v))

    def _plan(self):
        d = self.d; self.steps = []        # each: dict(foot,t_lift,t_land,x_from,x_to,k)
        pos = {'R': self.x0 + d * self.stand, 'L': self.x0 - d * self.stand}
        for k in range(self.N):
            foot = 'L' if k % 2 == 0 else 'R'; tl = self.t_lift0 + k * self.Ts; tn = tl + self.swing
            if k == self.N - 1: xt = self.x1 - d * self.stand
            elif k == self.N - 2: xt = self.x1 + d * self.stand
            else:
                ratio = clamp(abs(self.speed(tn)) / self.v0, .45, 1.0); xt = self.root_x(tn) + d * self.a * ratio
            # keep stride sane
            self.steps.append(dict(foot=foot, t_lift=tl, t_land=tn, x_from=pos[foot], x_to=xt, k=k, h=self.lift * (0.55 if k >= self.N - 2 or k == 0 else 1.0)))
            pos[foot] = xt
        self.final = pos

    def foot(self, name, t):
        """returns (x, ankle_y, rot, state) for foot at time t. ankle_y is negative (up)"""
        st = [s for s in self.steps if s['foot'] == name]
        x = self.x0 + self.d * (self.stand if name == 'R' else -self.stand); prev_land = -1e9; nxt = None
        for s in st:
            if t < s['t_lift']: nxt = s; break
            if t < s['t_land']:
                u = (t - s['t_lift']) / self.swing
                e = 0.75 * ease_io(u) + 0.25 * u
                xx = lerp(s['x_from'], s['x_to'], e)
                lift = s['h'] * math.sin(math.pi * clamp(u)) ** 0.85
                rot = lerp(D2R(24), D2R(-10), smooth(u * 1.25)) if u < .8 else D2R(-10 - 4 * (u - .8) / .2)
                rot = D2R(24) * (1 - smooth(u / .55)) + D2R(-6) * smooth(u / .55) if u < .55 else lerp(D2R(-6), D2R(-12), (u - .55) / .45)
                return xx, -(self.geo['ankle'](rot) + lift), rot, 'swing', s
            x = s['x_to']; prev_land = s['t_land']
        # planted
        if nxt is None:
            rot = D2R(-12) * (1 - smooth((t - prev_land) / 0.18)) if prev_land > -1e8 else 0.0
            return x, -self.geo['ankle'](rot), rot, 'plant', None
        t_in = t - prev_land if prev_land > -1e8 else 1e9
        t_to = nxt['t_lift'] - t
        rot = D2R(-12) * (1 - smooth(t_in / 0.16)) if prev_land > -1e8 else 0.0
        rot += D2R(20) * smooth(1 - t_to / 0.16)
        return x, -self.geo['ankle'](rot), rot, 'plant', nxt

    def _hips_table(self):
        n = len(self.ts); dys = np.zeros(n); d = self.d
        for i in range(0, n, 1):
            t = self.ts[i]; rx = self.X[i]; need = -1e9
            for nm in 'LR':
                x, y, _, _, _ = self.foot(nm, t); dx = x - (rx + self.geo.get('hip_dx', {'R': 3, 'L': -3})[nm] * d)
                need = max(need, y - self.geo['hip_y'] - math.sqrt(max(self.geo['lmax'] ** 2 - dx * dx, 1.0)))
            dys[i] = need
        k = int(0.14 * self.hz); ker = np.ones(2 * k + 1) / (2 * k + 1)
        pad = np.pad(dys, k, mode='edge'); ma = np.convolve(pad, ker, 'valid')
        shift = max(0.0, float(np.max(dys - ma))); self.dy = ma + shift + 3.0 * 0
        self.dy = self.dy + 0.5

    def state(self, t):
        """returns (root_x, pose dict, events) ; world feet are locked via IK"""
        rig, d = self.rig, self.d; rx = self.root_x(t); dy = float(np.interp(t, self.ts, self.dy)); sp = abs(self.speed(t)) / max(self.v0, 1e-9)
        pose = {'hips': {'ty': dy}}
        lean = D2R(4.5) * smooth(sp * 1.6)
        # step phase for body bobbing
        ph = 0.0
        if self.t_lift0 - .2 < t < self.t_stop + .2: ph = math.sin(2 * math.pi * (t - self.t_lift0) / (2 * self.Ts))
        pose['spine'] = {'rot': lean + D2R(1.4) * ph * sp}
        pose['head'] = {'rot': -lean * 0.7 - D2R(1.0) * ph * sp + D2R(2)}
        rot_leg = {}
        for nm in 'LR':
            x, y, rot, stt, _ = self.foot(nm, t)
            tgt = (x, y)
            ch = (f'leg{nm}_up', f'leg{nm}_lo', f'foot{nm}')
            rig.ik2(pose, ch, tgt, bend=self.bend, end_rot=rot, root={'x': rx, 'flip': d < 0})
            rot_leg[nm] = pose[f'leg{nm}_up']['rot']
        for nm, other in (('L', 'R'), ('R', 'L')):
            ar = -self.arm_gain * rot_leg[other] * sp - D2R(2)
            pose[f'arm{nm}_up'] = {'rot': ar}
            pose[f'arm{nm}_lo'] = {'rot': -(D2R(self.arm_bend) + 0.7 * max(0.0, -ar) + 0.25 * max(0.0, ar))}
            pose[f'hand{nm}'] = {'rot': D2R(6)}
        return rx, pose

    def events(self):
        return [dict(t=s['t_land'], x=s['x_to'], foot=s['foot']) for s in self.steps]

    def standing_state(self, x):   # not used by Walker timeline
        return x
