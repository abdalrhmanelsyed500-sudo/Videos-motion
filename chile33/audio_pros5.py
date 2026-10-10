"""Prosperi Part 5 mix (NO MUSIC, SFX only - user request): Arabic voice (pros.wav) + procedural ambience/SFX synced to pros_scenes timeline. Output build/mix_pros.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import pros5_scenes as HS
SR = 44100; N = int(HS.DP5 * SR); t = np.arange(N) / SR
rg = np.random.default_rng(11)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/pros5.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
sos = signal.butter(2, 70, 'hp', fs=SR, output='sos'); v = signal.sosfilt(sos, v); v *= 0.92 / max(1e-6, np.abs(v).max())
env = np.abs(v); env = signal.sosfilt(signal.butter(2, 6, 'lp', fs=SR, output='sos'), env); env = np.clip(env / (env.max() * 0.6), 0, 1)

def bp(x, lo, hi, o=2): return signal.sosfilt(signal.butter(o, [lo, hi], 'bp', fs=SR, output='sos'), x)
def lp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, 'lp', fs=SR, output='sos'), x)
def hp(x, f, o=2): return signal.sosfilt(signal.butter(o, f, 'hp', fs=SR, output='sos'), x)
def noise(): return rg.normal(0, 1, N).astype(np.float32)
def sm(a, b, x): return np.clip((x - a) / (b - a), 0, 1) ** 2 * (3 - 2 * np.clip((x - a) / (b - a), 0, 1))
def win(a, b, fi=0.5, fo=0.5): return sm(a, a + fi, t) * (1 - sm(b - fo, b, t))

L = np.zeros(N, np.float32); R = np.zeros(N, np.float32)
def add(x, pan=0.0, g=1.0):
    global L, R
    pl = math.cos((pan + 1) * math.pi / 4); pr = math.sin((pan + 1) * math.pi / 4)
    L += x * g * pl * 1.414; R += x * g * pr * 1.414
def burst(t0, dur, f_lo, f_hi, amp, pan=0.0, decay=6.0):
    i0 = int(t0 * SR); n = int(dur * SR)
    if i0 < 0 or i0 + n > N: return
    x = bp(rg.normal(0, 1, n).astype(np.float32), f_lo, f_hi) * np.exp(-np.arange(n) / SR * decay) * amp
    seg = np.zeros(N, np.float32); seg[i0:i0 + n] = x; add(seg, pan)
def thump(t0, f0, amp, dur=0.8, pan=0.0):
    i0 = int(t0 * SR); n = int(dur * SR)
    if i0 + n > N: n = N - i0
    tt = np.arange(n) / SR; x = np.sin(2 * math.pi * (f0 * np.exp(-tt * 2.0)) * tt + 0) * np.exp(-tt * 5) * amp
    seg = np.zeros(N, np.float32); seg[i0:i0 + n] = x; add(seg, pan)

# ---- beds (NO MUSIC: noise ambience and SFX only)
D = HS.DP5
rs = np.random.default_rng(21)
def rnd(): return rs.random() - .5
add(lp(noise(), 120) * 0.16 * win(0, D, .6, 1.0) * (0.8 + 0.2 * np.sin(2 * math.pi * 0.11 * t)))
def tink(t0, f, amp, pan=0.0, dec=26):
    i0 = int(t0 * SR); n = int(0.5 * SR)
    if i0 + n > N: return
    tt = np.arange(n) / SR; x = (np.sin(2 * math.pi * f * tt) + 0.5 * np.sin(2 * math.pi * f * 2.76 * tt) + 0.3 * np.sin(2 * math.pi * f * 5.4 * tt)) * np.exp(-tt * dec) * amp
    s_ = np.zeros(N, np.float32); s_[i0:i0 + n] = x; add(s_, pan)
def creak(t0, dur, f0, f1, amp, pan=0.0):
    i0 = int(t0 * SR); n = int(dur * SR); tt = np.arange(n) / SR; fr = f0 + (f1 - f0) * tt / dur
    ph = 2 * math.pi * np.cumsum(fr) / SR; x = (np.sin(ph) * np.sign(np.sin(ph * 0.31 + 1)) * 0.5 + 0.5 * np.sin(ph * 2.01)) * np.sin(math.pi * tt / dur) ** 1.5 * (0.6 + 0.4 * np.sin(2 * math.pi * 31 * tt)) * amp
    s_ = np.zeros(N, np.float32); s_[i0:i0 + n] = x; add(s_, pan)

def am_buzz(t0, t1, f_lo, f_hi, rate, amp, pan=0.0, ramp=False):
    i0 = int(t0 * SR); n = int((t1 - t0) * SR); tt = np.arange(n) / SR; d_ = t1 - t0
    env_ = (np.sin(math.pi * tt / d_) ** 0.6) * ((0.35 + 0.65 * tt / d_) if ramp else 1.0)
    x = bp(rg.normal(0, 1, n).astype(np.float32), f_lo, f_hi) * (0.5 + 0.5 * np.sign(np.sin(2 * math.pi * rate * tt))) * env_ * amp
    s_ = np.zeros(N, np.float32); s_[i0:i0 + n] = x; add(s_, pan)

def drip(tk, amp=0.04, pan=0.3): tink(tk, 1400 + 300 * rnd(), amp, pan, 30)

# ---------- Prosperi SFX timeline (no music)
D = HS.DP5
def steps(t0, t1, step, amp=0.05, pan=0.0):
    for tk in np.arange(t0, t1, step): burst(tk + rnd() * 0.02, 0.07, 120, 1200, amp, pan + rnd() * 0.5, 26)


def heli_snd(t0, t1, amp, pk=None, pan0=0.0, pan1=0.0, rate=11.0, shape=None):
    """rotor chop: band noise AM-gated at blade rate + low thump; envelope follows `shape(t)`"""
    pk = pk if pk is not None else (t0 + t1) / 2
    e = np.where(t < pk, sm(t0, pk, t), 1 - sm(pk, t1, t)) * ((t >= t0) & (t <= t1))
    e = e ** 1.2 if shape is None else shape
    gate = (0.55 + 0.45 * np.sin(2 * math.pi * rate * t)) ** 2
    x = bp(noise(), 70, 480) * gate * 1.4 + lp(noise(), 160) * gate * 0.9 + np.sin(2 * math.pi * 52 * t) * gate * 0.25
    x += bp(noise(), 2500, 5500) * 0.12 * gate        # turbine whine/air
    pan = np.clip(pan0 + (pan1 - pan0) * np.clip((t - t0) / (t1 - t0), 0, 1), -1, 1)
    pl = np.cos((pan + 1) * math.pi / 4); pr = np.sin((pan + 1) * math.pi / 4)
    global L, R
    L += x * e * amp * pl * 1.414; R += x * e * amp * pr * 1.414


# Part 5 SFX (no music): hot wind, steps, digging, lizard scurry, bat flutter/squeaks, shelter hush, night wind/crickets, crossroads, mirage shimmer
def flutter(t0, dur, amp, pan=0.0):
    for k in range(int(dur * 14)):
        burst(t0 + k / 14 + rnd() * 0.02, 0.06, 1500, 5000, amp * (0.6 + 0.8 * rs.random()), pan + rnd(), 30)
def squeak(t0, amp=0.02, pan=0.0): tink(t0, 5200 + 800 * rnd(), amp, pan, 40)
add(bp(noise(), 120, 900) * 0.08 * win(0, 38.0, .6, .8) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.17 * t)))      # hot wind
add(lp(noise(), 100) * 0.10 * win(0, D, .6, 1.0))
steps(0.6, 4.2, 0.45, 0.04); steps(9.8, 14.8, 0.55, 0.035)
for tk in (7.6, 8.4): burst(tk, 0.35, 700, 3500, 0.04, 0.0, 9)                                         # empty bottle shake
tink(8.9, 1500, 0.025, 0.0, 22)
add(bp(noise(), 3000, 7000) * 0.02 * win(15.0, 25.5, .8, .8) * (0.6 + 0.4 * np.sin(2 * math.pi * 7 * t)))   # heat shimmer
steps(20.4, 25.0, 0.7, 0.03)
for k in range(10): burst(29.6 + k * 0.18, 0.16, 300, 2200, 0.05 * (1 - 0.03 * k), -0.2 + 0.05 * k, 14)    # scraping/digging
for k in range(6): burst(30.8 + k * 0.2, 0.12, 200, 1500, 0.04, 0.0, 18)
for tk in np.arange(32.3, 33.7, 0.09): burst(tk, 0.04, 2500, 7500, 0.03, 0.4 - 0.7 * (tk - 32.3) / 1.4, 60)    # lizard scurry
steps(33.2, 34.3, 0.5, 0.025)
add(lp(noise(), 160) * 0.07 * win(34.3, 38.2, .5, .5))                                                   # hollow shelter hush
flutter(34.8, 1.6, 0.03, -0.4); flutter(36.4, 1.6, 0.03, 0.4)
for tk in (34.9, 35.2, 35.9, 36.5, 37.0, 37.4): squeak(tk, 0.018, rnd() * 1.6)
steps(38.4, 40.8, 0.55, 0.04)
add(bp(noise(), 150, 800) * 0.05 * win(41.0, 51.4, .8, .8)); burst(41.2, 0.6, 300, 1500, 0.03, 0.0, 5)    # shade, cooler hush
drip(46.0, 0.02); drip(49.0, 0.015)
add(lp(noise(), 130) * 0.09 * win(51.4, 64.3, .8, .8)); steps(51.6, 53.6, 0.7, 0.03)
for tk in (57.0, 60.5): burst(tk, 0.5, 400, 2500, 0.02, 0.2, 6)
add(bp(noise(), 150, 700) * 0.07 * win(64.3, 78.9, 1.0, .8) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.2 * t)))   # open desert wind
heli_snd(64.8, 71.0, 0.09, pk=67.5, pan0=0.6, pan1=-0.4, rate=11.0, shape=(sm(64.8, 67.0, t) * (1 - sm(68.5, 71.0, t))) * 0.55)  # faint search plane that passes
thump(72.0, 42, 0.08, 1.0)
add(bp(noise(), 100, 500) * 0.10 * win(78.9, 93.0, 1.2, 1.0) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.13 * t)))    # night wind
for k in range(40): tk = 79.5 + k * 0.33 + rnd() * 0.1; tink(tk, 4300 + 100 * (k % 3), 0.006, rnd() * 1.4, 70)  # insects (no melody)
steps(86.9, 93.0, 0.9, 0.03)
add(bp(noise(), 150, 800) * 0.07 * win(93.0, D, .8, 1.0) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.25 * t))); steps(93.4, 100.0, 0.5, 0.05)
add(bp(noise(), 4000, 9000) * 0.012 * win(98.7, D - 0.5, 1.0, 1.0) * (0.6 + 0.4 * np.sin(2 * math.pi * 5 * t)))      # mirage shimmer
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.DP5 - 0.7, HS.DP5 - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_pros5.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
