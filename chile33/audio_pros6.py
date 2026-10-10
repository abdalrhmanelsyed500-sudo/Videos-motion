"""Prosperi Part 6 mix (NO MUSIC, SFX only - user request): Arabic voice (pros.wav) + procedural ambience/SFX synced to pros_scenes timeline. Output build/mix_pros.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import pros6_scenes as HS
SR = 44100; N = int(HS.DP6 * SR); t = np.arange(N) / SR
rg = np.random.default_rng(11)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/pros6.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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
D = HS.DP6
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
D = HS.DP6
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


# Part 6 SFX (no music): exhaustion heartbeat, wind, steps, icon pops, paper, tracks, camp, paw taps, water gulps, clinic room tone, IV drips, map ending
def gulp(t0, amp=0.07): burst(t0, 0.18, 120, 700, amp, 0.0, 14); burst(t0 + 0.05, 0.08, 800, 2200, amp * 0.4, 0.0, 30)
add(bp(noise(), 120, 900) * 0.08 * win(0, 14.8, .6, .8) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.17 * t)))
add(lp(noise(), 100) * 0.10 * win(0, D, .6, 1.0))
for tk in np.arange(3.6, 14.2, 1.15): thump(tk, 55, 0.10, 0.4); thump(tk + 0.3, 48, 0.06, 0.4)          # tired heartbeat
steps(0.6, 2.4, 0.6, 0.035); burst(3.1, 0.5, 80, 600, 0.06, 0.0, 6)                                     # staggers, drops to his knees
add(bp(noise(), 3000, 7000) * 0.015 * win(3.6, 14.0, .8, .8) * (0.6 + 0.4 * np.sin(2 * math.pi * 7 * t)))
burst(11.2, 0.4, 300, 1500, 0.02, 0.0, 8)
add(bp(noise(), 150, 700) * 0.08 * win(14.8, 23.5, 1.0, .8) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.2 * t)))   # dawn breeze
burst(17.2, 0.6, 200, 1200, 0.04, 0.0, 8); steps(19.6, 23.2, 0.5, 0.05)
add(bp(noise(), 150, 700) * 0.06 * win(23.5, 34.0, .8, .8))
for tk in (26.4, 27.8, 29.0): tink(tk, 900, 0.03, 0.0, 18); burst(tk, 0.12, 600, 2500, 0.03, 0.0, 30)   # icon pops
burst(30.4, 0.7, 2000, 7000, 0.03, 0.0, 5)                                                              # map paper
for k in range(7): burst(31.6 + k * 0.26, 0.06, 200, 1400, 0.04, 0.0 + 0.1 * k, 30)                    # paw taps
steps(35.2, 42.4, 0.55, 0.045)
for k in range(10): burst(34.6 + k * 0.5, 0.05, 250, 1500, 0.025, 0.2, 40)
add(bp(noise(), 150, 800) * 0.07 * win(42.8, 52.6, 1.0, .8)); steps(43.0, 48.4, 0.55, 0.045)
for tk in (45.0, 46.2, 47.0, 47.9): tink(tk, 1200 + 150 * (tk % 3), 0.008, 0.6, 30)                    # far goat bells (soft taps)
for i in range(10): tk = 48.8 + i * 0.36; tink(tk, 700 + 40 * i, 0.025, 0.0, 22)                         # day marks
steps(48.8, 52.6, 0.7, 0.03)
add(bp(noise(), 150, 800) * 0.06 * win(52.6, 66.0, .8, .8) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.22 * t)))
add(bp(noise(), 800, 2500) * 0.02 * win(54.4, 56.4, .3, .5) * (0.5 + 0.5 * np.sin(2 * math.pi * 3 * t)))     # cloth / hand wave
steps(62.4, 65.2, 0.32, 0.05)
add(lp(noise(), 160) * 0.07 * win(65.4, 75.0, .8, .8)); burst(67.0, 0.4, 600, 3000, 0.03, 0.0, 8); burst(72.0, 0.4, 600, 3000, 0.03, 0.0, 8)   # warm hush, cloth rustle
for tk in (75.3, 75.75, 76.2): gulp(tk)
add(lp(noise(), 130) * 0.09 * win(76.6, 89.8, 1.0, 1.0))
for tk in np.arange(77.2, 89.5, 1.35): tink(tk, 1500 + 80 * rnd(), 0.018, 0.5, 34)                       # IV drips
add(bp(noise(), 150, 600) * 0.05 * win(84.0, 89.8, .8, .8))                                               # air through the window
burst(89.9, 0.8, 2000, 7000, 0.03, 0.0, 4); thump(90.6, 46, 0.14, 0.9); thump(91.6, 40, 0.16, 1.2)      # map reveal
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.DP6 - 0.7, HS.DP6 - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_pros6.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
