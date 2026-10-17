"""Sufan 20 s TEST SCENE: walks in, talks (text-driven visemes, no voice yet), expressions per situation, walks on.
Placeholder background (NOT the series road design). SFX only: footsteps (from the walker's foot events), soft ambience. No music."""
import sys, os, math, wave, subprocess, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sufan_rig_side as S, sufan_walk as WK
from rigkit.rig import Rig
from rigkit.face import VISEMES, mix_vis
from rigkit.anim import viseme_track, smooth, clamp, lerp
from rigkit import audio as AU
D = math.radians
FF = '/home/user/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
W_, H_, FPS, DUR = 1920, 1080, 30, 20.0
SC = 1.3; GY = 935; SCREEN_X = 800

rig = Rig(S.build()); WK.BEND = 1
KW = dict(Ts=0.26, swing=0.20, a=13.0, stand=5.0, lift=6.0, arm_gain=1.3)
w1 = WK.make(rig, +1, 0.0, 150.0, 0.2, 3.6, **KW)
w2 = WK.make(rig, +1, 150.0, 235.0, 17.2, 20.3, **KW)

# ------------------------------------------------------------------ script (TEST LINES - not series dialogue)
LINES = [(3.9, 6.5, 'هيّا يا أولاد، الطريقُ طويلٌ وجميل!'),
         (7.0, 9.3, 'ما هذا؟ الطريقُ يتغيّرُ أمامنا!'),
         (9.9, 12.6, 'همم... ربّما هذا البابُ يأخذُنا إلى عالَمٍ آخر.'),
         (13.0, 15.0, 'لا بأس، سنمضي معًا ولن نتراجع!'),
         (15.4, 17.0, 'ها ها ها! مغامرةٌ جديدة!')]
VOW = {'ا': 'A', 'آ': 'A', 'أ': 'A', 'إ': 'I', 'و': 'O', 'ي': 'I', 'ى': 'A', 'ع': 'A', 'ح': 'A', 'ه': 'A', 'ة': 'A'}
CONS = {'م': 'M', 'ب': 'M', 'ف': 'FV', 'ل': 'L', 'ن': 'L', 'ر': 'L'}
def line_items(t0, t1, text):
    """approximate text-driven viseme track (letters -> visemes). Replace with audio envelope lip-sync when the real voice file arrives."""
    import re
    clean = re.sub('[\u064b-\u0652\u0640]', '', text)
    toks = []   # (kind,payload)
    for ch in clean:
        if ch == ' ': toks.append(('gap', .06))
        elif ch in '،,.؟?!…': toks.append(('gap', .16))
        else: toks.append(('v', VOW.get(ch) or CONS.get(ch) or ('E' if len(toks) % 2 else 'A'), 1.5 if ch in VOW else 0.7))
    wt = sum(t[2] if t[0] == 'v' else t[1] * 6 for t in toks); k = (t1 - t0) / wt; t = t0; items = []
    for tk in toks:
        if tk[0] == 'gap': t += tk[1] * 6 * k
        else:
            d = tk[2] * k; items.append((t, t + d, tk[1])); t += d
    return items
ITEMS = [it for l in LINES for it in line_items(*l)]
def speaking(t): return any(a - .05 <= t <= b + .05 for a, b, _ in LINES)

# ------------------------------------------------------------------ acting (blended over the walker's pose while standing)
def sm(x): return smooth(clamp(x))
def keys_interp(keys, t):
    if t <= keys[0][0]: return dict(keys[0][1])
    for (ta, A), (tb, B) in zip(keys, keys[1:]):
        if t <= tb:
            u = sm((t - ta) / max(tb - ta, 1e-6)); return {k: lerp(A[k], B[k], u) for k in A}
    return dict(keys[-1][1])
P = lambda spine=0, head=0, hat=0, ear=0, ru=0, rl=0, lu=0, ll=0: dict(spine=spine, head=head, hat=hat, ear=ear, ru=ru, rl=rl, lu=lu, ll=ll)
BODY = [(3.4, P()), (4.1, P(-2, -4, 0, 5, -55, -10, 6, -4)), (6.4, P(-2, -4, 0, 5, -55, -10, 6, -4)), (6.9, P(0, 0, 0, 0, -5, -5, 0, -3)),
        (7.25, P(-8, -10, 3, 22, -30, -20, 22, -10)), (9.1, P(-8, -10, 3, 22, -30, -20, 22, -10)),
        (9.8, P(0, -6, 5, -10, -58, -118, 0, -3)), (12.6, P(0, -6, 5, -10, -58, -118, 0, -3)),
        (13.0, P(3, -4, -2, 4, 6, -35, 6, -35)), (15.0, P(3, -4, -2, 4, 6, -35, 6, -35)),
        (15.4, P(-6, -9, 4, -18, -95, -45, 8, -6)), (17.0, P(-6, -9, 4, -18, -95, -45, 8, -6)), (17.5, P())]
def body_w(t): return sm((t - 3.4) / 0.4) * (1 - sm((t - 17.0) / 0.5))
def hand_swap(t):
    if 4.0 <= t <= 6.6: return {'handR': 'handR_point'}
    if 9.9 <= t <= 12.7: return {'handR': 'handR_flat'}
    if 13.0 <= t <= 15.1: return {'handR': 'handR_fist', 'handL': 'handL_fist'}
    if 15.4 <= t <= 17.1: return {'handR': 'handR_flat'}
    return {}
# face: (t, dict)
F = lambda h=.2, tl=0, lx=.3, ly=0, sq=0, lt=0, arc=0, pu=1, sm_=.35, wd=.5, op=0: dict(h=h, tl=tl, lx=lx, ly=ly, sq=sq, lt=lt, arc=arc, pu=pu, sm=sm_, wd=wd, op=op)
FACE = [(0, F()), (3.4, F(.2)), (3.9, F(.45, 0, .5, 0, .15, 0, 0, 1, .55, .7)), (6.5, F(.45, 0, .5, 0, .15, 0, 0, 1, .55, .7)),
        (6.9, F(1, 0, .45, -.15, 0, 0, 0, .8, 0, .2, .3)), (9.2, F(1, 0, .45, -.15, 0, 0, 0, .8, 0, .2, .2)),
        (9.7, F(.8, .3, -.8, -.8, 0, 0, 0, 1, -.1, .2)), (12.6, F(.8, .3, -.8, -.8, 0, 0, 0, 1, -.1, .2)),
        (12.9, F(-.2, .9, .3, 0, .25, .35, 0, 1, -.5, .5)), (15.0, F(-.2, .9, .3, 0, .25, .35, 0, 1, -.5, .5)),
        (15.3, F(.7, 0, 0, 0, .5, 0, 1.0, 1, .95, 1.0, .5)), (17.0, F(.7, 0, 0, 0, .5, 0, 1.0, 1, .95, 1.0, .5)),
        (17.5, F(.25, 0, .4, 0, 0, 0, 0, 1, .5, .5)), (20, F(.25, 0, .4, 0, 0, 0, 0, 1, .5, .5))]
BLINKS = [2.1, 5.6, 8.5, 11.4, 14.0, 17.9, 19.3]
def face_at(t):
    f = keys_interp(FACE, t)
    bl = 0.0
    for b in BLINKS:
        if b <= t <= b + .2: bl = 1 - abs((t - b) / .1 - 1)
    if speaking(t):
        m = dict(viseme_track(ITEMS, t)); m['smile'] = clamp(m['smile'] * .5 + f['sm'] * .6, -1, 1); m['open'] = clamp(m['open'] * (1 + f['op']), 0, 1)
        if f['arc'] > .5: m = mix_vis(m, VISEMES['laugh'], .55)
    else:
        m = dict(VISEMES['rest']); m['smile'] = f['sm']; m['wide'] = f['wd']; m['open'] = f['op'] * .3 if f['arc'] < .5 else .8
        if f['arc'] > .5: m = dict(VISEMES['laugh'])
    return {'mouth': m, 'look': (f['lx'], f['ly']), 'blinkR': bl, 'squint': f['sq'], 'lidtilt': f['lt'], 'browR': (f['h'], f['tl']), 'pupil': f['pu'], 'arc': f['arc']}

def pose_at(t):
    wk = w1 if t < 17.0 else w2
    rx, pose = wk.state(t); pose = {k: dict(v) for k, v in pose.items()}
    wgt = body_w(t)
    if wgt > 0:
        b = keys_interp(BODY, t); talk = math.sin(t * 9.0) * D(1.2) * (1 if speaking(t) else 0)
        def mix(name, val):
            base = pose.get(name, {}).get('rot', 0.0); pose.setdefault(name, {})['rot'] = lerp(base, val, wgt)
        mix('spine', D(b['spine'])); mix('head', D(b['head']) + talk); mix('hat', D(b['hat'])); mix('earR', D(b['ear']))
        mix('armR_up', D(b['ru'])); mix('armR_lo', D(b['rl'])); mix('armL_up', D(b['lu'])); mix('armL_lo', D(b['ll']))
    return rx, pose

# ------------------------------------------------------------------ placeholder background (parallax strips)
rng = np.random.RandomState(4)
def smooth_noise(n, k=8):
    v = rng.randn(n // k + 3); x = np.linspace(0, len(v) - 3, n); i = x.astype(int); f = x - i; f = f * f * (3 - 2 * f)
    return v[i] * (1 - f) + v[i + 1] * f
def periodic(m, SW, L):
    w = np.linspace(0, 1, L); n = m[:SW].copy(); n[:L] = w * m[:L] + (1 - w) * m[SW:SW + L]; return n
def make_layers():
    SW = 3600
    # far strip: sky gradient is separate; hills + clouds
    sky = np.zeros((H_, W_, 3), np.float32)
    top = np.array([232, 214, 176], np.float32); bot = np.array([214, 236, 248], np.float32)   # BGR
    for y in range(H_): sky[y] = bot * (1 - y / 700) + top * (y / 700) if y < 700 else top
    sky = np.clip(sky, 0, 255)
    cv2.circle(sky, (1450, 250), 150, (225, 245, 252), -1); sky = cv2.GaussianBlur(sky, (0, 0), 38) * .6 + np.clip(sky, 0, 255) * .4
    def strip(col, base, amp, fq, trees=0, tcol=None):
        im = np.zeros((H_, SW, 4), np.float32); n = periodic(smooth_noise(SW + 400, int(fq)), SW, 400) * amp
        pts = [(x, base - n[min(x, SW - 1)]) for x in range(0, SW + 8, 8)] + [(SW + 8, H_), (0, H_)]
        cv2.fillPoly(im, [np.array(pts, np.int32)], (*col, 255))
        for _ in range(trees):
            x = rng.randint(150, SW - 150); y = int(base - n[min(x, SW - 1)]) + 6; r = rng.randint(34, 70)
            cv2.rectangle(im, (x - 5, y - r // 2), (x + 5, y + 4), (60, 90, 110, 255), -1)
            cv2.circle(im, (x, y - r), r, (*tcol, 255), -1); cv2.circle(im, (x - r // 3, y - r - r // 4), r // 2, (*[min(255, c + 18) for c in tcol], 255), -1)
        im = cv2.GaussianBlur(np.pad(im, ((0, 0), (30, 30), (0, 0)), mode='wrap'), (0, 0), 3.0)[:, 30:-30]; return im
    far = strip((196, 214, 168), 640, 70, 220); mid = strip((170, 205, 150), 760, 60, 150, 14, (130, 178, 108)); near = strip((160, 200, 140), 840, 28, 110, 7, (112, 168, 98))
    clouds = np.zeros((H_, SW, 4), np.float32)
    for _ in range(9):
        x = rng.randint(250, SW - 250); y = rng.randint(80, 330); 
        for _ in range(5): cv2.ellipse(clouds, (x + rng.randint(-90, 90), y + rng.randint(-18, 18)), (rng.randint(70, 130), rng.randint(24, 40)), 0, 0, 360, (255, 252, 250, 235), -1)
    clouds = cv2.GaussianBlur(clouds, (0, 0), 9)
    # ground (foreground, parallax 1.0): grass + path + tufts
    G = np.zeros((H_, SW, 4), np.float32)
    G[860:] = (140, 200, 160, 255)                       # grass (BGR)
    path = np.array([[0, 905], [SW, 905], [SW, H_], [0, H_]], np.int32); cv2.fillPoly(G, [path], (176, 212, 232, 255))
    cv2.line(G, (0, 905), (SW, 905), (150, 190, 214, 255), 6)
    for _ in range(260):
        x = rng.randint(0, SW); y = rng.randint(915, 1075); r = rng.randint(2, 6); c = int(rng.randint(170, 205)); cv2.circle(G, (x, y), r, (c - 24, c, c + 18, 255), -1)
    for _ in range(90):   # grass tufts + flowers on both borders
        x = rng.randint(0, SW); y = rng.choice([rng.randint(865, 900), rng.randint(1040, 1075)])
        for dx in (-7, 0, 7): cv2.line(G, (x, y), (x + dx * 2 // 1, y - rng.randint(18, 32)), (96, 160, 96, 255), 3, cv2.LINE_AA)
        if rng.rand() < .35: cv2.circle(G, (x, y - 34), 6, [(120, 140, 240, 255), (120, 220, 250, 255), (250, 200, 160, 255)][rng.randint(3)], -1)
    G = cv2.GaussianBlur(G, (0, 0), 1.2)
    grain = (rng.randn(H_, W_, 1) * 2.2).astype(np.float32)
    return sky, [(far, .10), (mid, .22), (near, .40)], clouds, G, grain
SKY, STRIPS, CLOUDS, GROUND, GRAIN = make_layers()
def slice_strip(im, off):
    SW = im.shape[1]; off = int(off) % SW; idx = (np.arange(W_) + off) % SW; return im[:, idx]
def over(cv, rgba):
    a = rgba[..., 3:4] / 255.0; cv[:] = cv * (1 - a) + rgba[..., :3] * a
def bg_frame(camx):
    cv = SKY.copy()
    over(cv, slice_strip(CLOUDS, camx * .04)); 
    for im, p in STRIPS: over(cv, slice_strip(im, camx * p))
    over(cv, slice_strip(GROUND, camx)); return cv

def shadow(cv, sx, wk_scale=1.0):
    ov = np.zeros((H_, W_), np.float32); cv2.ellipse(ov, (int(sx), GY + 6), (int(190 * SC / 1.3 * wk_scale), 20), 0, 0, 360, 1.0, -1); ov = cv2.GaussianBlur(ov, (0, 0), 14) * .30
    cv[:] = cv * (1 - ov[..., None]) + np.array([60, 90, 70], np.float32) * ov[..., None]

# ------------------------------------------------------------------ audio (SFX + ambience only)
def build_audio(path):
    SR = AU.SR; n = int(DUR * SR); out = np.zeros(n, np.float32); r = np.random.RandomState(9)
    def add(x, t, g=1.0):
        i = int(t * SR); x = x[:max(0, n - i)]; out[i:i + len(x)] += x * g
    for wk in (w1, w2):
        for ev in wk.events():
            if ev['t'] < DUR: add(AU.step(r, 1.0), ev['t'], .55 if ev['foot'] == 'R' else .4)
    for tb in (1.0, 4.6, 8.2, 12.4, 18.0): add(AU.bird(r), tb, .22)
    wind = AU._lp(r.randn(n).astype(np.float32), .004) * 3.5; out += wind * .22 * (0.6 + 0.4 * np.sin(np.arange(n) / SR * 0.7))
    fade = np.minimum(1, np.minimum(np.arange(n) / (0.3 * SR), (n - np.arange(n)) / (1.0 * SR)))
    out = np.clip(out * fade * 0.9, -1, 1)
    wv = wave.open(path, 'wb'); wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((out * 32767).astype(np.int16).tobytes()); wv.close()

def main(out_mp4, stills=None, nframes=None):
    tmp = out_mp4 + '.v.mp4'; wav = out_mp4 + '.wav'; build_audio(wav)
    p = subprocess.Popen([FF, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W_}x{H_}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    nf = nframes or int(DUR * FPS); viol = 0; saved = {}
    for i in range(nf):
        t = i / FPS; rx, pose = pose_at(t)
        viol += len(rig.violations(pose))
        camx = rx * SC - SCREEN_X; cv = bg_frame(camx); shadow(cv, SCREEN_X)
        zov = {'armUpR': 56, 'armLoR': 56, 'handR': 57} if pose['armR_up']['rot'] < -D(45) else None
        cv /= 255.0
        rig.draw(cv, pose, cam=(SC, SCREEN_X - rx * SC, GY), dyn=S.face_dyn(face_at(t)), swap=hand_swap(t), root={'x': rx}, zov=zov)
        cv *= 255.0
        cv += GRAIN; fo = 1 - sm((t - 19.0) / 1.0); cv = cv * fo + np.array([214, 236, 248], np.float32) * (1 - fo)
        fr = np.clip(cv, 0, 255).astype(np.uint8); p.stdin.write(fr.tobytes())
        if stills and i in stills: cv2.imwrite(stills[i], fr)
    p.stdin.close(); p.wait()
    subprocess.run([FF, '-y', '-loglevel', 'error', '-i', tmp, '-i', wav, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out_mp4], check=True)
    os.remove(tmp); os.remove(wav); print('frames', nf, 'limit violations', viol)
if __name__ == '__main__':
    main(sys.argv[1])
