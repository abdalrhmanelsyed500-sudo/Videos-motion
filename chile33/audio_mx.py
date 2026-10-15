"""V8 keyframe-method mix (footsteps are computed from the same phase function that drives the animation)
"""
"""Upgrade-test mix: NO MUSIC. Wind ambience (changes per shot), footsteps locked to the rig2 gait (1.1 cycles/s), sand shuffle, cut whooshes, cloth/breath for the close-up."""
import numpy as np, math, wave
from scipy import signal
SR = 44100; D = 15.8; N = int(D * SR); t = np.arange(N) / SR; rg = np.random.default_rng(5)
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

import mx2_scenes as M
from engine import ease_out, seg, lerp
gust = 0.6 + 0.4 * np.sin(2 * math.pi * 0.17 * t + 1) * np.sin(2 * math.pi * 0.07 * t + 2)
swell = 0.8 + 0.4 * sm(11, 15.5, t)
add(bp(nz(), 180, 900) * 0.10 * gust * swell * win(0, D, 0.6, 1.2)); add(bp(nz(), 900, 3200) * 0.025 * gust * swell * (0.4 + 0.6 * sm(1, 3, t)))
add(lp(nz(), 120) * 0.05 * (win(10.2, D, 0.6, 1.0)))
def breath(tk, dur, amp, lo=700, hi=2600):
    i0 = int(tk * SR); n = int(dur * SR); e = np.sin(np.linspace(0, math.pi, n)) ** 1.5
    x = bp(rg.normal(0, 1, n).astype(np.float32), lo, hi) * e * amp; s = np.zeros(N, np.float32); s[i0:i0 + n] = x; add(s)
def step(tk, amp):
    a = amp * (0.75 + 0.25 * rg.random()); burst(tk, 0.09, 150, 1800, a, 0.0); thump(tk, a * 0.9); burst(tk + 0.04, 0.18, 2500, 6500, a * 0.25, 0.0)
# step times = the moments the animation phase crosses a contact pose (A at k.0, B at k.5)
def phase(T):
    if T < 5.0: return T * M.RATE
    return M.phase2(T - 5.0)
prev = phase(0.0); T = 0.0
while T < 8.1:
    T += 1 / 600.0; p = phase(T)
    if math.floor(p * 2) != math.floor(prev * 2):
        step(T, 0.012 + 0.05 * seg(T, 0, 5.0)); 
    prev = p
burst(8.2, 0.3, 600, 2800, 0.012, 0.0)                 # settling / sigh, cloth
for tk in (6.3, 8.3): breath(tk, 0.8, 0.02, 500, 2200)                       # effort breathing
burst(9.3, 0.45, 500, 3000, 0.022, 0.0)                                      # cloth, raising the hand to the brow
breath(10.9, 1.1, 0.03); breath(12.0, 0.9, 0.03)                             # close-up, worried breaths
tg = 10.2 + 2.6
breath(tg - 0.02, 0.32, 0.09, 900, 3800); thump(tg + 0.03, 0.14); burst(tg + 0.05, 0.4, 300, 1500, 0.035, 0.0)   # gasp + jolt on the SHOCK frame
breath(14.0, 1.0, 0.04, 400, 1800)
for tk in (5.0, 10.2):
    i0 = int((tk - 0.35) * SR); n = int(0.7 * SR); e = np.sin(np.linspace(0, math.pi, n)) ** 2; x = bp(rg.normal(0, 1, n).astype(np.float32), 300, 3500) * e * 0.05
    s = np.zeros(N, np.float32); s[i0:i0 + n] = x; add(s)
fade = sm(0, 0.4, t) * (1 - sm(D - 1.3, D - 0.05, t))
out = np.tanh(np.stack([L, R], 1) * fade[:, None] * 2.2) * 0.9
w = wave.open('build/mix_mx2.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close(); print('peak', np.abs(out).max())
