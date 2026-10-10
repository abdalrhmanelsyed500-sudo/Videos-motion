"""Prosperi Part 2 mix (NO MUSIC, SFX only - user request): Arabic voice (pros.wav) + procedural ambience/SFX synced to pros_scenes timeline. Output build/mix_pros.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import pros2_scenes as HS
SR = 44100; N = int(HS.DP2 * SR); t = np.arange(N) / SR
rg = np.random.default_rng(11)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/pros2.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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
D = HS.DP2
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
D = HS.DP2
def steps(t0, t1, step, amp=0.05, pan=0.0):
    for tk in np.arange(t0, t1, step): burst(tk + rnd() * 0.02, 0.07, 120, 1200, amp, pan + rnd() * 0.5, 26)

# Part 2 SFX timeline (no music): Rome city murmur, stadium crowd, five sports, desert wind, footsteps, storm brewing at the end
def crowd(t0, t1, amp): add(bp(noise(), 250, 1800) * amp * win(t0, t1, .4, .5) * (0.7 + 0.3 * np.sin(2 * math.pi * 2.7 * t)))
add(bp(noise(), 300, 2200) * 0.04 * win(0, 3.0, .3, .5)); 
for tk in (0.6, 1.4, 2.3): burst(tk, 0.5, 2500, 6000, 0.012, 0.5 * rnd() * 2, 8)          # birds
crowd(2.8, 5.8, 0.09); steps(3.0, 5.0, 0.2, 0.04)                                          # stadium + jog
for tk in (4.9,): burst(tk, 0.9, 400, 3000, 0.05, 0.0, 3)                                  # cheer swell
# five disciplines 5.5-10.85: fencing swish/clash, water splash, shot, hoofbeats, running steps
for i, tk in enumerate(np.arange(5.8, 6.6, 0.14)): burst(tk, 0.07, 2000, 7000, 0.05, -0.6, 30)
tink(6.2, 2100, 0.03, -0.5, 18); tink(6.5, 2600, 0.03, -0.5, 18)
for tk in np.arange(6.9, 8.0, 0.2): burst(tk + 0.05 * rnd(), 0.16, 400, 3500, 0.05, -0.1, 9)
thump(8.6, 90, 0.2, 0.3); burst(8.6, 0.12, 1500, 9000, 0.14, 0.2, 40); burst(9.4, 0.12, 1500, 9000, 0.12, 0.2, 40)
for tk in np.arange(9.6, 10.6, 0.17): thump(tk, 120, 0.05, 0.08); burst(tk, 0.06, 150, 900, 0.05, 0.3, 40)
steps(10.4, 13.3, 0.30, 0.05); crowd(10.9, 13.6, 0.05)
# 13.45-18 stroll in the desert: soft wind, slow steps; 18-22 hard run: fast steps and breathing
add(lp(noise(), 160) * 0.12 * win(13.4, 31.5, .6, .8) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.2 * t)))
add(bp(noise(), 400, 1800) * 0.04 * win(13.4, 18.0, .5, .5) * (0.5 + 0.5 * np.sin(2 * math.pi * 0.4 * t)))
steps(13.6, 16.1, 0.56, 0.04)
steps(18.1, 22.3, 0.28, 0.06); crowd(18.1, 22.4, 0.04)
for tk in np.arange(18.6, 22.3, 0.55): burst(tk, 0.25, 500, 2500, 0.025, 0.0, 7)
# 22.4-25.5 exhaustion: heavy panting
for tk in np.arange(22.7, 25.4, 0.6): burst(tk, 0.35, 400, 2800, 0.07, 0.0, 6); burst(tk + 0.3, 0.3, 500, 3000, 0.05, 0.0, 7)
# 25.5-31.25 desert open, wind gradually darker: storm rumble from 28.9
add(lp(noise(), 100) * 0.30 * win(28.8, 31.4, 1.0, 0.8) * (0.5 + 0.5 * np.sin(2 * math.pi * 0.7 * t))); add(bp(noise(), 1500, 6000) * 0.05 * win(29.5, 31.4, 1.0, 0.6))
thump(28.95, 45, 0.15, 0.9)
# 31.25-35.6 old map: paper rustle, pin thud + ring of tink
for tk in (31.6, 32.4, 33.0): burst(tk, 0.25, 1200, 6000, 0.035, 0.0, 14)
thump(33.5, 70, 0.22, 0.4); burst(33.5, 0.1, 800, 4000, 0.08, 0.0, 30); tink(33.55, 1300, 0.02, 0.0, 10)
# 35.6-39 start line crowd with whistles-free murmur
crowd(35.5, 39.0, 0.08); burst(37.0, 0.25, 600, 4000, 0.07, 0.0, 6)
# 39-43 route drawn: pen scratches and a pop at each stage dot
for i in range(6): tk = 39.2 + 3.4 * i / 5; burst(tk, 0.5, 2000, 7000, 0.02, 0.0, 6); tink(tk + 0.45, 1500 + 90 * i, 0.03, 0.2, 18)
# 43-47.6 running in soft dunes: heavy sand steps; 47.6-50 thirst: wind and breath; 50-53.8: dunes, rocks, heat shimmer
steps(43.0, 47.6, 0.3, 0.06); crowd(43.0, 47.6, 0.03)
add(bp(noise(), 150, 1000) * 0.06 * win(47.4, 54.0, .5, .6)); steps(50.0, 51.2, 0.32, 0.055); steps(51.2, 53.7, 0.34, 0.05)
add(bp(noise(), 3000, 8000) * 0.015 * win(51.0, 54.0, .6, .5) * (0.6 + 0.4 * np.sin(2 * math.pi * 5.5 * t)))   # heat shimmer hiss
for tk in np.arange(48.2, 49.9, 0.7): burst(tk, 0.3, 500, 2500, 0.04, 0.0, 7)
# 53.75-56.8 carrying: sand steps + canteen slosh; 56.8-60.2 water point: pour + gulps
steps(53.8, 56.7, 0.4, 0.05)
for tk in np.arange(54.5, 56.6, 0.45): burst(tk, 0.15, 300, 1800, 0.025, 0.4, 14)
add(bp(noise(), 1200, 7000) * 0.07 * win(57.3, 58.6, .2, .3) * (0.6 + 0.4 * np.sin(2 * math.pi * 17 * t)))
for tk in (58.2, 58.6, 59.0): thump(tk, 160, 0.06, 0.12); burst(tk, 0.12, 300, 1500, 0.05, 0.0, 22)
# 60.2-66.9 starting gun-like crowd burst, steady running with the pack
crowd(60.2, 62.8, 0.06); burst(62.7, 0.3, 500, 4000, 0.10, 0.0, 6); steps(62.9, 67.0, 0.22, 0.06); crowd(63.0, 67.0, 0.06)
# 67-70.9 three quick days: steps, wind of each day; 70.9-72.75 calm camp
steps(67.0, 70.9, 0.3, 0.05); steps(71.0, 72.7, 0.6, 0.02)
# 72.75-80.3 sky darkens: wind rises into a low roar, sand hiss, distant thunder-like rumble
add(bp(noise(), 90, 700) * 0.28 * win(73.0, 80.3, 2.5, 1.0) * (0.4 + 0.6 * np.sin(2 * math.pi * 0.6 * t + 1) ** 2)); add(bp(noise(), 1500, 7000) * 0.14 * win(75.0, 80.3, 2.0, 1.0) * (0.6 + 0.4 * np.sin(2 * math.pi * 2.1 * t)))
thump(76.6, 40, 0.2, 1.2)
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.DP2 - 0.7, HS.DP2 - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_pros2.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
