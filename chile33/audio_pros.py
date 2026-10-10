"""Part 7 mix (NO MUSIC, SFX only - user request): Arabic voice (pros.wav) + procedural ambience/SFX synced to pros_scenes timeline. Output build/mix_pros.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import pros_scenes as HS
SR = 44100; N = int(HS.DP * SR); t = np.arange(N) / SR
rg = np.random.default_rng(11)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/pros.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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
D = HS.DP
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
D = HS.DP
def steps(t0, t1, step, amp=0.05, pan=0.0):
    for tk in np.arange(t0, t1, step): burst(tk + rnd() * 0.02, 0.07, 120, 1200, amp, pan + rnd() * 0.5, 26)
# 0-2.1 start: light desert breeze, many soft running footsteps, murmur of the field
add(bp(noise(), 150, 1100) * 0.07 * win(0, 2.3, .3, .3)); steps(0.1, 2.1, 0.11, 0.035, 0.0); add(bp(noise(), 250, 1800) * 0.05 * win(0, 2.3, .2, .3))
# 2.1-5.0 the storm: wind roar swells, sand hiss, gusts
roar = bp(noise(), 90, 900) * win(2.0, 5.2, 1.2, 0.5) * (0.5 + 0.5 * np.sin(2 * math.pi * 0.9 * t + 1)); add(roar * 0.55)
add(bp(noise(), 1500, 7000) * 0.20 * win(2.2, 5.1, 1.0, 0.5) * (0.6 + 0.4 * np.sin(2 * math.pi * 2.3 * t)))
thump(2.1, 42, 0.18, 0.9)
# 5.0-7.4 sudden quiet: low breeze, a few settling grains, his breathing
add(lp(noise(), 120) * 0.10 * win(4.9, D, .6, 1.0)); add(bp(noise(), 600, 3000) * 0.04 * win(5.0, 6.0, .3, .8))
for tk in np.arange(5.6, 9.6, 1.0): burst(tk, 0.45, 300, 1500, 0.025, 0.0, 5)
# 7.4-12.1 emptiness: faint wind and one distant flap
add(bp(noise(), 120, 800) * 0.06 * win(7.0, 12.4, .6, .6) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.3 * t)))
# 12.1-14.6 flag flapping
for tk in np.arange(12.3, 14.5, 0.09): burst(tk, 0.05, 400, 3000, 0.04, -0.4, 40)
# 14.6-18.1 racers murmur, a distant starter horn-like noise burst (no tone), cheers
add(bp(noise(), 250, 1800) * 0.07 * win(14.6, 18.1, .4, .5) * (0.7 + 0.3 * np.sin(2 * math.pi * 2.9 * t)))
burst(15.2, 0.35, 500, 3500, 0.07, 0.0, 6)
# 18.1-28.3 lone walking/running: steady footsteps in sand, breath, wind
steps(18.4, 21.4, 0.55, 0.045); steps(21.7, 25.6, 0.33, 0.055); steps(25.7, 28.3, 0.33, 0.05)
add(bp(noise(), 120, 900) * 0.07 * win(18.1, 31.0, .5, .8) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.35 * t)))
add(bp(noise(), 500, 2500) * 0.035 * win(21.5, 25.8, .5, .6))
# 28.3-end border: wire hum, wooden post creak, sunset wind, slower steps
for tk in (28.9, 30.0): tink(tk, 1900 + 400 * rnd(), 0.025, 0.4, 14)
creak(29.4, 0.8, 330, 210, 0.05, -0.4); steps(28.5, 30.9, 0.5, 0.05)
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.DP - 0.7, HS.DP - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_pros.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
