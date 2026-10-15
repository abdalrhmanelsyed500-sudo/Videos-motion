"""Upgrade-test mix: NO MUSIC. Wind ambience (changes per shot), footsteps locked to the rig2 gait (1.1 cycles/s), sand shuffle, cut whooshes, cloth/breath for the close-up."""
import numpy as np, math, wave
from scipy import signal
SR = 44100; D = 26.4; N = int(D * SR); t = np.arange(N) / SR; rg = np.random.default_rng(5)
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
swell = 0.7 + 0.5 * sm(21, 26, t)
add(bp(nz(), 180, 900) * 0.10 * gust * swell * win(0, D, 0.6, 1.2)); add(bp(nz(), 900, 3200) * 0.025 * gust * swell * (0.4 + 0.6 * sm(4, 6, t)))
add(lp(nz(), 120) * 0.05 * (win(9.4, 12.4, 0.6, 0.6) + win(17.2, 21.2, 0.6, 0.6)))
def breath(tk, dur, amp, lo=700, hi=2600):
    i0 = int(tk * SR); n = int(dur * SR); e = np.sin(np.linspace(0, math.pi, n)) ** 1.5
    x = bp(rg.normal(0, 1, n).astype(np.float32), lo, hi) * e * amp; s = np.zeros(N, np.float32); s[i0:i0 + n] = x; add(s)
def steps(t0, t1, amp, big=1.0):
    n = 0
    while True:
        tk = 0.227 + 0.4545 * n; n += 1
        if tk > t1: break
        if tk < t0: continue
        a = amp * (0.75 + 0.25 * rg.random()); burst(tk, 0.09, 150, 1800, a * big, 0.0); thump(tk, a * 0.9 * big); burst(tk + 0.04, 0.18, 2500, 6500, a * 0.25 * big, 0.0)
steps(0.2, 4.4, 0.02, 0.8); steps(4.4, 9.4, 0.06, 1.0)
for tk in (6.5, 8.0): breath(tk, 0.8, 0.02, 500, 2200)           # effort breathing in the medium shot
breath(10.0, 1.0, 0.03); breath(11.4, 0.9, 0.03)                   # profile close-up, worried breaths
burst(13.8, 0.35, 500, 3000, 0.02, 0.0); burst(15.9, 0.5, 500, 3000, 0.02, 0.0); breath(14.6, 0.7, 0.025)      # cloth + breath, raising the hand
breath(18.5, 0.30, 0.08, 900, 3800); thump(18.55, 0.12); burst(18.6, 0.4, 300, 1500, 0.03, 0.0)          # gasp + jolt at the realisation
breath(19.9, 1.0, 0.04, 400, 1800); breath(21.0, 0.9, 0.035, 400, 1800)
for tk in (4.4, 9.4, 12.4, 17.4):
    i0 = int((tk - 0.35) * SR); n = int(0.7 * SR); e = np.sin(np.linspace(0, math.pi, n)) ** 2; x = bp(rg.normal(0, 1, n).astype(np.float32), 300, 3500) * e * 0.05
    s = np.zeros(N, np.float32); s[i0:i0 + n] = x; add(s)
for k in range(30): burst(22.0 + rg.random() * 4.0, 0.03, 3000, 7000, 0.006, rg.random() * 2 - 1)      # sand ticks in the last wide shot
fade = sm(0, 0.4, t) * (1 - sm(D - 1.4, D - 0.05, t))
out = np.tanh(np.stack([L, R], 1) * fade[:, None] * 2.2) * 0.9
w = wave.open('build/mix_up3.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close(); print('peak', np.abs(out).max())
