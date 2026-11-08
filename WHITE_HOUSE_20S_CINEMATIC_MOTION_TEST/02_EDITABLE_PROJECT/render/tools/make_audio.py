#!/usr/bin/env python3
"""make_audio.py — original synthesized sound design for the 20s White House cutaway.
No copyrighted audio: all effects are procedurally synthesized (noise filters, sine
partials, envelopes). Output: mix.wav (float32) + sfx event wavs."""
import numpy as np
import scipy.signal as sps
import scipy.io.wavfile as wav
import os

SR = 48000
DUR = 20.0
N = int(SR * DUR)
rng = np.random.default_rng(20261108)

def t_axis():
    return np.arange(N) / SR

def place(buf, sig, t0, gain=1.0):
    i0 = int(t0 * SR)
    i1 = min(N, i0 + len(sig))
    if i1 <= i0:
        return
    buf[i0:i1] += sig[:i1 - i0] * gain

def white(n):
    return rng.standard_normal(n)

def pink(n):
    x = white(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    X /= np.sqrt(f + 1e-6)
    return np.fft.irfft(X, n)

def bandpass(x, lo, hi, order=4):
    sos = sps.butter(order, [lo, hi], btype='band', fs=SR, output='sos')
    return sps.sosfilt(sos, x)

def lowpass(x, fc, order=4):
    sos = sps.butter(order, fc, btype='low', fs=SR, output='sos')
    return sps.sosfilt(sos, x)

def env_ad(n, a, d, s=0.0, r=0.0, sus=0.7):
    e = np.ones(n)
    na, nd = int(a * SR), int(d * SR)
    if na > 0: e[:na] *= np.linspace(0, 1, na)
    if nd > 0: e[-nd:] *= np.linspace(1, 0, nd)
    if s > 0:
        ns = n - na - nd
        if ns > 0: e[na:na + ns] = sus
    return e

def whoosh(dur, f_start, f_end, peak=0.5, q=1.2):
    """time-varying bandpass whoosh via segmented filtering"""
    n = int(dur * SR)
    x = white(n) * env_ad(n, dur * 0.18, dur * 0.5)
    segs = 12
    out = np.zeros(n)
    seg_len = n // segs
    for i in range(segs):
        s0 = i * seg_len
        s1 = s0 + seg_len + int(0.004 * SR)
        if s1 > n: s1 = n
        f = f_start * (f_end / f_start) ** (i / (segs - 1))
        seg = bandpass(x[s0:s1], max(60, f * 0.55), min(SR / 2 - 500, f * 1.8), 4)
        seg *= np.hanning(len(seg)) ** 0.5
        L = min(len(out) - s0, len(seg))
        out[s0:s0 + L] += seg[:L]
    out /= np.max(np.abs(out)) + 1e-9
    return out * peak

def thunk(dur=0.22, f0=92, f1=52, peak=0.55):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 9)
    s += 0.25 * white(n) * np.exp(-t * 60)
    s /= np.max(np.abs(s)) + 1e-9
    return s * peak

def creak(dur, peak=0.3, f0=180, f1=420):
    n = int(dur * SR)
    x = pink(n) * env_ad(n, dur * 0.2, dur * 0.3)
    t = np.arange(n) / SR
    f = f0 + (f1 - f0) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * t))
    # time-varying bandpass via segmented filtering
    segs = 8
    out = np.zeros(n)
    sl = n // segs
    for i in range(segs):
        s0 = i * sl
        s1 = min(n, s0 + sl + int(0.003 * SR))
        fc = f[s0] if len(f) > s0 else f0
        seg = bandpass(x[s0:s1], fc * 0.6, fc * 1.6)
        L = min(len(out) - s0, len(seg))
        out[s0:s0 + L] += seg[:L] * np.hanning(len(seg)) ** 0.4
    out /= np.max(np.abs(out)) + 1e-9
    return out * peak

def crackle(t0, dur=0.05, peak=0.12, fc=2600):
    n = int(dur * SR)
    x = white(n) * np.exp(-np.arange(n) / SR * 40)
    x = bandpass(x, fc * 0.4, fc * 1.8)
    x /= np.max(np.abs(x)) + 1e-9
    return x * peak

def footstep(peak=0.22, hard=False):
    n = int(0.11 * SR)
    t = np.arange(n) / SR
    x = white(n) * np.exp(-t * 34)
    x = bandpass(x, 130, 900)
    s = np.sin(2 * np.pi * (78 if hard else 64) * t) * np.exp(-t * 26) * 0.5
    out = x + s
    out /= np.max(np.abs(out)) + 1e-9
    return out * peak

def chime(f0, dur=1.4, peak=0.16):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, amp, dec in [(1, 1.0, 3.2), (2.39, 0.45, 5.0), (3.92, 0.22, 7.0), (6.17, 0.10, 9.0)]:
        out += amp * np.sin(2 * np.pi * f0 * k * t + rng.uniform(0, 6.28)) * np.exp(-t * dec)
    out *= env_ad(n, 0.004, 0)
    out /= np.max(np.abs(out)) + 1e-9
    return out * peak

def ping(f0=1200, dur=0.25, peak=0.14):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.sin(2 * np.pi * f0 * t) * np.exp(-t * 9)
    out += 0.4 * np.sin(2 * np.pi * f0 * 2.01 * t) * np.exp(-t * 14)
    out /= np.max(np.abs(out)) + 1e-9
    return out * peak

def roomtone(dur, level=0.05):
    n = int(dur * SR)
    x = pink(n)
    x = lowpass(x, 420)
    t = np.arange(n) / SR
    x *= 1 + 0.08 * np.sin(2 * np.pi * 0.07 * t)
    x /= np.max(np.abs(x)) + 1e-9
    return x * level

def air_soft(dur, peak=0.08):
    n = int(dur * SR)
    x = pink(n) * env_ad(n, dur * 0.3, dur * 0.5)
    x = lowpass(x, 700)
    x /= np.max(np.abs(x)) + 1e-9
    return x * peak

# ---------------- build mix ----------------
mix = np.zeros(N)

# Shot 1: paper drawing ambience + title thump
for t0 in [0.25, 0.6, 1.05, 1.5, 1.9]:
    place(mix, crackle(0, peak=0.10, fc=3200), t0)
place(mix, air_soft(0.9, peak=0.05), 0.2)
place(mix, thunk(0.3, f0=110, f1=70, peak=0.3), 1.35)

# Shot 2: roof lift + dust + approach whoosh
place(mix, creak(1.3, peak=0.26, f0=170, f1=380), 3.0)
place(mix, thunk(0.4, f0=85, f1=48, peak=0.4), 3.08)
for t0 in [3.5, 3.85, 4.15]:
    place(mix, crackle(0, peak=0.07, fc=1800), t0)
place(mix, whoosh(1.1, 260, 1100, peak=0.3), 3.55)
place(mix, whoosh(0.85, 900, 400, peak=0.22), 4.25)

# Shot 3: expansion + oval
place(mix, whoosh(0.95, 300, 1500, peak=0.32), 5.05)
place(mix, thunk(0.3, f0=95, f1=60, peak=0.28), 5.85)
place(mix, air_soft(0.6, peak=0.04), 6.0)
place(mix, ping(900, peak=0.07), 6.55)

# Shot 4: arch transition + cabinet
place(mix, whoosh(0.6, 400, 1600, peak=0.3), 8.05)
place(mix, creak(0.5, peak=0.16, f0=220, f1=340), 9.72)
place(mix, ping(1100, peak=0.07), 9.85)

# Shot 5: dive + match cut + dining
place(mix, whoosh(0.65, 350, 1400, peak=0.28), 11.02)
place(mix, thunk(0.35, f0=100, f1=55, peak=0.34), 11.62)
place(mix, whoosh(0.5, 1300, 500, peak=0.24), 11.68)
place(mix, chime(660, peak=0.13), 13.55)
place(mix, ping(820, peak=0.06), 13.15)

# Shot 6: corridor footsteps + east room
steps = [14.15, 14.32, 14.49, 14.66]
for i, t0 in enumerate(steps):
    place(mix, footstep(peak=0.19, hard=(i % 2 == 0)), t0)
place(mix, whoosh(0.5, 500, 1500, peak=0.22), 14.35)
place(mix, air_soft(0.7, peak=0.05), 15.9)
place(mix, chime(523, peak=0.11), 16.6)

# Shot 7: reverse + markers + resolve
place(mix, whoosh(0.9, 1400, 300, peak=0.26), 17.05)
for i, t0 in enumerate([18.45, 18.95, 19.35, 19.72]):
    place(mix, ping(700 + i * 120, peak=0.1), t0)
# final resolve chord (G3 B3 D4 G4)
n = int(2.4 * SR)
t = np.arange(n) / SR
chord = np.zeros(n)
for f, a in [(196, 0.5), (246.9, 0.38), (293.7, 0.32), (392, 0.24)]:
    chord += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28))
chord *= env_ad(n, 0.5, 1.2) * 0.5
place(mix, chord, 19.35)

# room tone bed (subtle, whole piece with fade in/out)
tone = roomtone(DUR, level=0.045)
tt = t_axis()
tone *= np.clip((tt - 0.4) / 1.2, 0, 1) * np.clip((DUR - tt) / 1.5, 0, 1)
mix += tone

# stereo width: slight decorrelation
mix_r = mix.copy()
mix_r = lowpass(mix_r, 1200) * 0.94 + pink(N) * 0.012

# normalize
peak = max(np.max(np.abs(mix)), np.max(np.abs(mix_r)))
target = 0.89  # -1 dBTP
mix *= target / peak
mix_r *= target / peak

out_dir = os.path.join(os.path.dirname(__file__), '..', '04_audio_out')
os.makedirs(out_dir, exist_ok=True)
wav.write(os.path.join(out_dir, 'mix.wav'), SR, np.stack([mix, mix_r], axis=1).astype(np.float32))
wav.write(os.path.join(out_dir, 'mix_16.wav'), SR, (np.stack([mix, mix_r], axis=1) * 32767).astype(np.int16))

# RMS report per 0.5s
rms = []
for i in range(40):
    seg = mix[int(i * 0.5 * SR):int((i + 1) * 0.5 * SR)]
    rms.append(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9))
print('RMS dBFS per 0.5s:')
print(' '.join(f'{v:.0f}' for v in rms))
print('peak dBTP:', 20 * np.log10(peak))
print('written:', out_dir)
