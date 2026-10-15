"""Upgrade-test mix: NO MUSIC. Wind ambience (changes per shot), footsteps locked to the rig2 gait (1.1 cycles/s), sand shuffle, cut whooshes, cloth/breath for the close-up."""
import numpy as np, math, wave
from scipy import signal
SR = 44100; D = 19.6; N = int(D * SR); t = np.arange(N) / SR; rg = np.random.default_rng(5)
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
# wind: slow gusts, brighter in the low-sun shots
gust = 0.6 + 0.4 * np.sin(2 * math.pi * 0.17 * t + 1) * np.sin(2 * math.pi * 0.07 * t + 2)
add(bp(nz(), 180, 900) * 0.10 * gust * win(0, D, 0.6, 1.0)); add(bp(nz(), 900, 3000) * 0.025 * gust * (0.3 + sm(4, 6, t)))
add(lp(nz(), 120) * 0.05 * win(9.4, 14, 0.8, 0.8))          # close-up: low pressure rumble
# steps (rig gait: foot plants every half cycle)
def steps(t0, t1, amp, pan=0.0, big=1.0):
    k = math.ceil((2 * math.pi * 1.1 * t0 + 0.3) / math.pi)
    while True:
        tk = (k * math.pi - 0.3) / (2 * math.pi * 1.1); k += 1
        if tk > t1: break
        a = amp * (0.7 + 0.3 * rg.random()); burst(tk, 0.09, 150, 1800, a * big, pan + (rg.random() - .5) * 0.2); thump(tk, a * 0.9 * big); burst(tk + 0.04, 0.18, 2500, 6500, a * 0.25 * big, pan)
steps(0.4, 4.4, 0.020, 0.1, 0.6); steps(4.9, 9.4, 0.05, 0.0, 1.0); steps(14.0, 16.3, 0.11, 0.0, 1.5); steps(16.6, 19.3, 0.035, -0.1, 0.8)
# cloth + breath for the close-up
for tk in (10.3, 12.7): burst(tk, 0.4, 500, 3000, 0.018, 0.0)
add(bp(nz(), 400, 1800) * 0.012 * (0.5 + 0.5 * np.sin(2 * math.pi * 0.28 * t)) * win(9.6, 13.6, 0.5, 0.5))
# cut whooshes
for tk in (4.6, 9.5, 13.9, 16.4):
    i0 = int((tk - 0.35) * SR); n = int(0.7 * SR); e = np.sin(np.linspace(0, math.pi, n)) ** 2; x = bp(rg.normal(0, 1, n).astype(np.float32), 300, 3500) * e * 0.05
    s = np.zeros(N, np.float32); s[i0:i0 + n] = x; add(s)
# low sun drone-free shimmer: tiny sand ticks in the silhouette
for k in range(40): burst(16.8 + rg.random() * 2.8, 0.03, 3000, 7000, 0.008, rg.random() * 2 - 1)
fade = sm(0, 0.4, t) * (1 - sm(D - 0.9, D - 0.05, t))
out = np.tanh(np.stack([L, R], 1) * fade[:, None] * 2.2) * 0.9
w = wave.open('build/mix_up.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close(); print('peak', np.abs(out).max())
