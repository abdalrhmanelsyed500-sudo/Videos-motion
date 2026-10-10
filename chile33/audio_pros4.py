"""Prosperi Part 4 mix (NO MUSIC, SFX only - user request): Arabic voice (pros.wav) + procedural ambience/SFX synced to pros_scenes timeline. Output build/mix_pros.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import pros4_scenes as HS
SR = 44100; N = int(HS.DP4 * SR); t = np.arange(N) / SR
rg = np.random.default_rng(11)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/pros4.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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
D = HS.DP4
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
D = HS.DP4
def steps(t0, t1, step, amp=0.05, pan=0.0):
    for tk in np.arange(t0, t1, step): burst(tk + rnd() * 0.02, 0.07, 120, 1200, amp, pan + rnd() * 0.5, 26)


# Part 4 SFX (no music): dawn wind, steps, helicopter rotor (distant -> overhead -> gone), flare hiss, water/sun ambience, searching helis on map
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

add(bp(noise(), 120, 900) * 0.07 * win(0, 10, .6, .8) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.2 * t)))   # morning wind
add(lp(noise(), 100) * 0.10 * win(0, D, .6, 1.0))
steps(0.6, 5.6, 0.30, 0.04); steps(9.6, 13.0, 0.30, 0.03)
for tk in (6.8, 7.7, 8.5): burst(tk, 0.25, 600, 3500, 0.04, 0.0, 12)                                   # rummaging bag
tink(7.4, 1700, 0.03, 0.0, 22); burst(8.2, 0.5, 1800, 6000, 0.03, 0.0, 8)                               # bottle / wrapper
add(bp(noise(), 150, 800) * 0.05 * win(13.0, 15.5, .5, .5))
burst(16.0, 0.6, 400, 1800, 0.015, 0.0, 6)
heli_snd(15.4, 20.8, 0.05, pk=20.0, pan0=0.8, pan1=0.2, shape=sm(15.4, 20.0, t) * (1 - sm(20.0, 20.8, t)) * 0.5)       # first faint rotor
heli_snd(18.0, 30.8, 0.55, pk=24.5, pan0=0.7, pan1=-0.8, rate=11.5, shape=np.where(t < 24.5, sm(18.0, 24.5, t), 1 - sm(24.5, 31.5, t)) ** 1.3 * ((t > 18) & (t < 33.5)))
add(bp(noise(), 400, 3500) * 0.05 * win(24.3, 29.2, .3, .8) * (0.7 + 0.3 * np.sin(2 * math.pi * 24 * t)))   # flare hiss
burst(24.3, 0.5, 600, 5000, 0.07, 0.0, 9)                                                                  # flare strike
add(bp(noise(), 150, 900) * 0.04 * win(31.5, 41.2, .6, .6))
for tk in np.arange(31.8, 33.5, 0.9): burst(tk, 0.5, 400, 1800, 0.015, 0.0, 6)
heli_snd(34.0, 41.4, 0.40, pk=36.0, pan0=0.0, pan1=0.0, rate=11.5, shape=(sm(34.0, 34.8, t) * (1 - sm(37.2, 41.4, t))) ** 1.2 * 0.8)   # memory replay of the heli
burst(34.0, 0.5, 300, 2000, 0.05, 0.0, 6)
add(bp(noise(), 150, 900) * 0.06 * win(41.2, 47.0, .6, .6)); steps(43.6, 47.2, 0.30, 0.05)
for tk in (47.6, 48.4): burst(tk, 0.35, 700, 4000, 0.03, 0.0, 8)
steps(47.2, 49.4, 0.31, 0.04)
for tk in (50.4, 51.2): burst(tk, 0.4, 600, 3000, 0.04, 0.0, 9)                                         # water bottle shake / slosh
tink(51.8, 900, 0.02, 0.0, 14)
add(bp(noise(), 300, 1500) * 0.05 * win(50.0, 52.6, .3, .5) * (0.5 + 0.5 * np.sin(2 * math.pi * 3.2 * t)))   # slosh
for tk in (52.9, 53.5): burst(tk, 0.3, 1500, 6000, 0.04, 0.0, 12)                                       # wrapper
add(lp(noise(), 140) * 0.10 * win(54.0, 57.8, .6, .6)); add(bp(noise(), 3000, 7000) * 0.02 * win(54.0, 57.8, .6, .6) * (0.6 + 0.4 * np.sin(2 * math.pi * 7 * t)))   # sun heat shimmer hiss
steps(54.4, 57.6, 0.42, 0.045)
add(bp(noise(), 150, 800) * 0.05 * win(57.8, 59.8, .4, .5) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.4 * t)))
for i in range(6): tk = 59.9 + 2.0 * i / 5; burst(tk, 0.45, 2000, 7000, 0.02, 0.0, 6)                # map scratch
heli_snd(59.8, 68.4, 0.10, pk=64.0, pan0=-0.6, pan1=0.6, rate=10.5, shape=(sm(59.8, 61.5, t) * (1 - sm(66.0, 68.4, t))) * 0.7)
heli_snd(60.5, 68.4, 0.08, pk=64.0, pan0=0.7, pan1=-0.5, rate=12.5, shape=(sm(60.5, 62.5, t) * (1 - sm(66.0, 68.4, t))) * 0.6)
add(lp(noise(), 90) * 0.09 * win(64.0, 71.9, 1.0, 1.0)); thump(68.2, 40, 0.12, 1.0)
add(bp(noise(), 150, 900) * 0.07 * win(68.0, D, .8, 1.0) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.3 * t)))
heli_snd(71.9, D, 0.05, pk=73.0, pan0=-0.7, pan1=-0.9, rate=10.5, shape=sm(71.9, 73.5, t) * 0.4)
steps(72.0, 74.8, 0.55, 0.03)
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.DP4 - 0.7, HS.DP4 - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_pros4.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
