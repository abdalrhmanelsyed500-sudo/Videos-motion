"""SFX + speech mixer (no music).  Deterministic synthesis with numpy."""
import numpy as np, wave, os
from . import anim

SR = 44100

def _res(x, sr):
    if sr == SR: return x
    n = int(len(x) * SR / sr); return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)

def _lp(x, a):
    y = np.zeros_like(x); s = 0.0
    for i, v in enumerate(x): s += a * (v - s); y[i] = s
    return y

def _env(n, att, dec):
    t = np.arange(n) / SR; return np.minimum(t / max(att, 1e-4), 1) * np.exp(-t / dec)

def step(rng, vol):
    n = int(.14 * SR); no = _lp(rng.randn(n).astype(np.float32), .12) * _env(n, .002, .03)
    t = np.arange(n) / SR; th = np.sin(2 * np.pi * (95 + 20 * rng.rand()) * t) * _env(n, .002, .045)
    return (no * 2.2 + th * .8) * vol

def pop(rng):
    n = int(.12 * SR); t = np.arange(n) / SR; f = 520 + 700 * (1 - np.exp(-t / .02))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, .002, .035) * .5

def boing(rng):
    n = int(.5 * SR); t = np.arange(n) / SR; f = 200 + 380 * np.exp(-t / .12) + 18 * np.sin(2 * np.pi * 14 * t)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, .004, .16) * .45

def thud(rng):
    n = int(.25 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 62 * t) * _env(n, .003, .07) * 1.0 + _lp(rng.randn(n).astype(np.float32), .1) * _env(n, .002, .04) * 1.6) * .8

def swish(rng):
    n = int(.32 * SR); no = rng.randn(n).astype(np.float32); t = np.arange(n) / SR
    bp = _lp(no, .35) - _lp(no, .04); return bp * np.sin(np.pi * np.clip(t / .32, 0, 1)) ** 2 * 1.8 * .35

def bird(rng):
    n = int(.22 * SR); t = np.arange(n) / SR; f = 3200 + 900 * np.sin(2 * np.pi * (7 + 5 * rng.rand()) * t) + 600 * rng.rand()
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * np.clip(t / .22, 0, 1)) ** 2 * .05

def mix(ep, audio_dir, out_wav, fps=30, sfx_gain=1.0):
    total = int((ep.n / fps + .5) * SR); L = np.zeros(total, np.float32); R = np.zeros(total, np.float32)
    rng = np.random.RandomState(5)
    def put(sig, t, pan=0.0, g=1.0):
        i = int(t * SR)
        if i < 0 or i >= total: return
        j = min(total, i + len(sig)); s = sig[:j - i] * g
        L[i:j] += s * np.sqrt((1 - pan) / 2) * 1.414 / 1.414; R[i:j] += s * np.sqrt((1 + pan) / 2)
    # ambience: gentle wind (low-passed noise, slow swell) + sparse birds
    wind = _lp(rng.randn(total).astype(np.float32), .02) * 0.9; sw = 0.6 + 0.4 * np.sin(2 * np.pi * np.arange(total) / SR / 7.0)
    amb = wind * sw * 0.55; L += amb; R += amb[::-1] * 0 + amb
    for tb in np.sort(rng.uniform(1, ep.n / fps - 1, 9)):
        for k in range(1 + rng.randint(3)): put(bird(rng), tb + k * .28, rng.uniform(-.8, .8))
    for e in ep.ev:
        cam = ep.cam[min(int(e['t'] * fps), ep.n - 1)]
        pan = float(np.clip((e.get('x', 0) - cam) * 1.15 / 960, -.9, .9)) if e['kind'] == 'step' else (-.25 if e['who'] == 'z' else .25)
        k = e['kind']
        if k == 'step': put(step(rng, e['vol']), e['t'], pan, .55 * sfx_gain)
        elif k == 'pop': put(pop(rng), e['t'], pan, .35 * sfx_gain)
        elif k == 'boing': put(boing(rng), e['t'], pan, .35 * sfx_gain)
        elif k == 'thud': put(thud(rng), e['t'], pan, .5 * sfx_gain)
        elif k == 'swish': put(swish(rng), e['t'] - .05, pan, .5 * sfx_gain)
    for key, sp in ep.speech.items():
        w = wave.open(os.path.join(audio_dir, key + '.wav')); sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        x = _res(x, sr); x = x / (np.percentile(np.abs(x), 99.5) + 1e-6) * 0.62
        put(x, sp['t0'], -.18 if sp['who'] == 'z' else .18, 1.0)
    m = max(np.abs(L).max(), np.abs(R).max()); g = 0.92 / m if m > 0.92 else 1.0
    st = np.stack([L, R], 1) * g; pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    w = wave.open(out_wav, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
    return st
