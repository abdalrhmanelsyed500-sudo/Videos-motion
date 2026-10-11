"""Prosperi Part 8 mix (NO MUSIC, SFX only - user request): Arabic voice (pros.wav) + procedural ambience/SFX synced to pros_scenes timeline. Output build/mix_pros.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import pros8_scenes as HS
SR = 44100; N = int(HS.DP8 * SR); t = np.arange(N) / SR
rg = np.random.default_rng(11)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/pros8.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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
D = HS.DP8
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
D = HS.DP8
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


# Part 8 SFX (no music): stadium crowd, heartbeat, wind, steps, loop dots, storm, night insects, call-to-action pops
def pinpop(t0, amp=0.04): burst(t0, 0.1, 500, 3000, amp, 0.0, 30); tink(t0, 820, amp * 0.5, 0.0, 26)
add(lp(noise(), 100) * 0.09 * win(0, D, .6, 1.0))
add(bp(noise(), 250, 1800) * 0.06 * win(0, 4.2, .4, .6) * (0.7 + 0.3 * np.sin(2 * math.pi * 1.3 * t))); steps(0.2, 3.7, 0.28, 0.04)
add(bp(noise(), 120, 800) * 0.08 * win(3.6, 15.8, .6, .6) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.17 * t)))
for tk in np.arange(5.6, 8.0, 1.0): thump(tk, 55, 0.10, 0.4); thump(tk + 0.3, 48, 0.06, 0.4)
add(bp(noise(), 3000, 7000) * 0.015 * win(7.8, 15.6, .8, .8) * (0.6 + 0.4 * np.sin(2 * math.pi * 7 * t)))
add(bp(noise(), 150, 700) * 0.07 * win(15.6, 30.0, .8, .8) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.2 * t)))
for tk in (16.2, 16.9, 17.6): burst(tk, 0.25, 500, 3000, 0.02, 0.0, 12)                                  # shaky breath
for tk in (19.0, 19.9, 20.8): burst(tk, 0.5, 300, 2500, 0.04, 0.0, 7)                                     # heavy breath
steps(21.5, 22.6, 0.5, 0.04)
for k in range(40): burst(24.7 + k * 0.038, 0.03, 200, 1500, 0.025, 0.0, 70)                             # loop dots
burst(26.3, 0.6, 800, 5000, 0.06, 0.0, 6)                                                                 # cross-out
for k in range(18): burst(27.5 + k * 0.083, 0.03, 600, 3000, 0.025, 0.0, 70)                             # green dots
steps(28.4, 29.9, 0.5, 0.05); steps(29.8, 32.9, 0.45, 0.045)
add(bp(noise(), 300, 3500) * 0.16 * win(33.0, 37.6, 1.0, 1.0) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.7 * t)))   # storm
add(lp(noise(), 200) * 0.12 * win(33.0, 37.6, 1.0, 1.0)); burst(34.0, 0.7, 800, 5000, 0.04, 0.0, 5)
add(lp(noise(), 130) * 0.08 * win(37.4, 41.8, .8, .8)); steps(40.0, 41.6, 0.7, 0.03)
add(bp(noise(), 100, 500) * 0.10 * win(41.8, 52.8, 1.2, 1.0) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.13 * t)))    # night wind
for k in range(30): tk = 42.5 + k * 0.33 + rnd() * 0.1; tink(tk, 4300 + 100 * (k % 3), 0.006, rnd() * 1.4, 70)
pinpop(44.0, 0.03)
for k in range(20): burst(50.6 + k * 0.05, 0.03, 600, 3000, 0.02, 0.0, 70)
add(bp(noise(), 150, 700) * 0.06 * win(52.6, D, .8, 1.0) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.2 * t)))
for tk in (55.3, 57.2, 59.2): pinpop(tk, 0.06); tink(tk + 0.05, 1500, 0.03, 0.0, 14)
steps(61.0, 63.4, 0.55, 0.04)
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.DP8 - 0.7, HS.DP8 - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_pros8.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
