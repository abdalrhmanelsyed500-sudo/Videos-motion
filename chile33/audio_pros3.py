"""Prosperi Part 3 mix (NO MUSIC, SFX only - user request): Arabic voice (pros.wav) + procedural ambience/SFX synced to pros_scenes timeline. Output build/mix_pros.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import pros3_scenes as HS
SR = 44100; N = int(HS.DP3 * SR); t = np.arange(N) / SR
rg = np.random.default_rng(11)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/pros3.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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
D = HS.DP3
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
D = HS.DP3
def steps(t0, t1, step, amp=0.05, pan=0.0):
    for tk in np.arange(t0, t1, step): burst(tk + rnd() * 0.02, 0.07, 120, 1200, amp, pan + rnd() * 0.5, 26)

# Part 3 SFX (no music): map pen, running, wind -> sandstorm roar (muffled while hiding), sudden calm, footsteps, final map scratch
def gust(t0, t1, amp, f0=90, f1=900, rate=0.8, ph=0.0): add(bp(noise(), f0, f1) * amp * win(t0, t1, 0.8, 0.8) * (0.55 + 0.45 * np.sin(2 * math.pi * rate * t + ph)))
for tk in (0.5, 1.5, 3.0): burst(tk, 0.3, 1500, 6000, 0.03, 0.0, 12)                         # map paper
for i in range(4): tk = 0.3 + 2.3 * i / 3; burst(tk, 0.5, 2000, 7000, 0.02, 0.0, 6); tink(tk + 0.4, 1500 + 90 * i, 0.03, 0.2, 18)
thump(3.9, 70, 0.18, 0.4)
steps(5.8, 10.0, 0.26, 0.05); add(bp(noise(), 150, 1100) * 0.06 * win(5.6, 8.4, .4, .6)); gust(7.8, 12.4, 0.16)
add(bp(noise(), 1500, 6500) * 0.06 * win(9.5, 12.2, 1.0, .5))
gust(12.0, 19.8, 0.50, 90, 1000, 1.1); add(bp(noise(), 1500, 7000) * 0.20 * win(12.2, 22.8, 1.0, .8) * (0.6 + 0.4 * np.sin(2 * math.pi * 2.3 * t)))
thump(12.2, 42, 0.22, 1.0); steps(12.4, 14.8, 0.24, 0.04)
gust(19.4, 38.4, 0.62, 80, 800, 0.6, 1.0); add(bp(noise(), 1500, 7000) * 0.16 * win(19.6, 38.4, .8, 1.2) * (0.6 + 0.4 * np.sin(2 * math.pi * 1.7 * t)))
for tk in np.arange(24.9, 29.0, 0.8): burst(tk, 0.4, 300, 2000, 0.03, 0.0, 6)                  # muffled breath
for tk in np.arange(30.0, 34.0, 1.2): burst(tk, 0.5, 400, 1800, 0.02, 0.0, 5)
add(lp(noise(), 90) * 0.20 * win(34.0, 38.2, 1.0, 1.2))
# 38-40.5 sudden calm: sand pour / shake off
add(lp(noise(), 130) * 0.07 * win(38.2, D, 0.8, 1.0)); burst(38.4, 1.2, 800, 5000, 0.07, 0.0, 3); burst(39.3, 0.6, 800, 5000, 0.05, 0.0, 6)
add(bp(noise(), 150, 900) * 0.05 * win(40.0, 55.0, .6, .6) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.25 * t)))
for tk in np.arange(41.0, 42.4, 0.7): burst(tk, 0.3, 500, 2000, 0.02, 0.0, 7)
add(bp(noise(), 800, 4000) * 0.03 * win(43.0, 48.2, .8, .8) * (0.6 + 0.4 * np.sin(2 * math.pi * 1.2 * t)))   # flags hiss
for tk in np.arange(54.8, 57.8, 0.6): burst(tk, 0.25, 120, 1200, 0.05, 0.0, 22)                   # slow steps up the dune
for tk in np.arange(48.9, 51.0, 1.0): burst(tk, 0.5, 600, 3500, 0.03, 0.0, 6)
add(bp(noise(), 120, 800) * 0.05 * win(57.0, 72.0, .6, .6))
burst(68.4, 0.2, 800, 4000, 0.04, 0.0, 20)
steps(72.4, 76.5, 0.27, 0.06); steps(76.6, 80.6, 0.27, 0.05); add(bp(noise(), 150, 1000) * 0.07 * win(72.0, 81.0, .5, .8))
for i in range(6): tk = 82.0 + 3.4 * i / 5; burst(tk, 0.45, 2000, 7000, 0.025, 0.0, 6)           # pen scratch of his path
add(lp(noise(), 110) * 0.10 * win(80.8, D, 1.0, 1.0)); thump(81.2, 38, 0.14, 1.2)
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.DP3 - 0.7, HS.DP3 - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_pros3.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
