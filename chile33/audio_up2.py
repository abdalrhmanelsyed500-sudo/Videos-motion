"""Upgrade-test mix: NO MUSIC. Wind ambience (changes per shot), footsteps locked to the rig2 gait (1.1 cycles/s), sand shuffle, cut whooshes, cloth/breath for the close-up."""
import numpy as np, math, wave
from scipy import signal
SR = 44100; D = 15.2; N = int(D * SR); t = np.arange(N) / SR; rg = np.random.default_rng(5)
def bp(x, lo, hi, o=2): return signal.sosfilt(signal.butter(o, [lo, hi], 'bp', fs=SR, output='sos'), x)
def lp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, 'lp', fs=SR, output='sos'), x)
def sm(a, b, x): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
def win(a, b, fi=.5, fo=.5): return sm(a, a + fi, t) * (1 - sm(b - fo, b, t))
nz = lambda: rg.normal(0, 1, N).astype(np.float32)
L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)
def add(x, pan=0.0):
    global L, R; L += x * math.cos((pan + 1) * math.pi / 4) * 1.414; R += x * math.sin((pan + 1) * math.pi / 4) * 1.414
def burst(tk, dur, lo, hi, amp, pan=0.0):
    i0 = int(tk * SR); n = int(dur * SR)
    if i0 + n >= N: return
    x = bp(rg.normal(0, 1, n).astype(np.float32), lo, hi) * np.exp(-np.arange(n) / (n * 0.28)) * amp; s = np.zeros(N, np.float32); s[i0:i0 + n] = x; add(s, pan)
def thump(tk, amp):
    i0 = int(tk * SR); n = int(0.12 * SR)
    if i0 + n >= N: return
    tt = np.arange(n) / SR; x = np.sin(2 * math.pi * (70 - 200 * tt) * tt) * np.exp(-tt * 30) * amp; s = np.zeros(N, np.float32); s[i0:i0 + n] = x; add(s)
gust = 0.6 + 0.4 * np.sin(2 * math.pi * 0.17 * t + 1) * np.sin(2 * math.pi * 0.07 * t + 2)
add(bp(nz(), 180, 900) * 0.10 * gust * win(0, D, 0.6, 1.0)); add(bp(nz(), 900, 3000) * 0.025 * gust * (0.3 + 0.7 * sm(0, 3, t)))
add(lp(nz(), 120) * 0.05 * win(5.6, 14, 0.8, 0.8))
def steps(t0, t1, amp, big=1.0):
    n = 0
    while True:
        tk = 0.227 + 0.4545 * n; n += 1
        if tk > t1: break
        if tk < t0: continue
        a = amp * (0.7 + 0.3 * rg.random()) * min(1.0, (tk - 0.2) / 1.0 + 0.3)
        burst(tk, 0.09, 150, 1800, a * big, 0.0); thump(tk, a * 0.9 * big); burst(tk + 0.04, 0.18, 2500, 6500, a * 0.25 * big, 0.0)
steps(0.2, 6.0, 0.06)
def breath(tk, dur, amp, lo=700, hi=2600):
    i0 = int(tk * SR); n = int(dur * SR); e = np.sin(np.linspace(0, math.pi, n)) ** 1.5
    x = bp(rg.normal(0, 1, n).astype(np.float32), lo, hi) * e * amp; s = np.zeros(N, np.float32); s[i0:i0 + n] = x; add(s)
breath(7.3, 0.7, 0.03); breath(8.95, 0.28, 0.07, 900, 3600); thump(9.0, 0.10)       # worried breath, sharp gasp + jolt
for tk in (10.6, 12.0): breath(tk, 0.9, 0.04, 400, 1800)                              # tired heavy breathing
breath(13.3, 0.6, 0.02); breath(14.2, 0.6, 0.02, 500, 2000)
for tk in (6.9, 10.3, 12.7): burst(tk, 0.4, 500, 3000, 0.016, 0.0)
for tk in (6.0,):
    i0 = int((tk - 0.35) * SR); n = int(0.7 * SR); e = np.sin(np.linspace(0, math.pi, n)) ** 2; x = bp(rg.normal(0, 1, n).astype(np.float32), 300, 3500) * e * 0.05
    s = np.zeros(N, np.float32); s[i0:i0 + n] = x; add(s)
fade = sm(0, 0.4, t) * (1 - sm(D - 0.9, D - 0.05, t))
out = np.tanh(np.stack([L, R], 1) * fade[:, None] * 2.2) * 0.9
w = wave.open('build/mix_up2.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close(); print('peak', np.abs(out).max())
