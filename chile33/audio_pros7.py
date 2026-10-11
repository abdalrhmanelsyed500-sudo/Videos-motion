"""Prosperi Part 7 mix (NO MUSIC, SFX only - user request): Arabic voice (pros.wav) + procedural ambience/SFX synced to pros_scenes timeline. Output build/mix_pros.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import pros7_scenes as HS
SR = 44100; N = int(HS.DP7 * SR); t = np.arange(N) / SR
rg = np.random.default_rng(11)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/pros7.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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
D = HS.DP7
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
D = HS.DP7
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


# Part 7 SFX (no music): map paper/pins, race crowd, border wind, storm, steps, search planes, clinic room tone + IV drips, scale ticks, home clock + phone ring, ending pins
def pinpop(t0, amp=0.04): burst(t0, 0.1, 500, 3000, amp, 0.0, 30); tink(t0, 820, amp * 0.5, 0.0, 26)
add(lp(noise(), 100) * 0.09 * win(0, D, .6, 1.0))
add(bp(noise(), 2000, 7000) * 0.012 * win(0, 15.6, .5, .5))
for tk in (0.2, 2.0, 6.9, 8.7, 13.2): burst(tk, 0.5, 2000, 7000, 0.03, 0.0, 5)                           # map paper moves
pinpop(1.0); pinpop(3.5); pinpop(4.4); pinpop(10.0)
thump(8.3, 60, 0.12, 0.7); burst(8.3, 0.2, 200, 1500, 0.06, 0.0, 14)                                      # the pin lands
for tk in (8.5, 9.3, 10.1): thump(tk, 48, 0.06, 0.8)
for k in range(40): burst(13.4 + k * 0.035, 0.03, 1500, 5000, 0.02, 0.0, 70)                             # dashed line drawing ticks
add(bp(noise(), 250, 1800) * 0.05 * win(15.4, 20.8, .6, .6) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.9 * t)))   # race start crowd murmur
steps(17.4, 20.6, 0.28, 0.03); burst(17.4, 0.5, 600, 3500, 0.04, 0.0, 6)
add(bp(noise(), 120, 800) * 0.09 * win(20.6, 29.2, .5, .6) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.2 * t)))   # border wind
steps(20.7, 22.4, 0.5, 0.045)
add(bp(noise(), 300, 3500) * 0.16 * win(22.3, 26.6, .5, .8) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.7 * t)))   # storm
add(lp(noise(), 200) * 0.12 * win(22.3, 26.6, .5, .8))
steps(26.6, 29.0, 0.5, 0.045)
add(bp(noise(), 150, 800) * 0.05 * win(29.0, 40.5, 1.0, .8))
pinpop(31.0)
heli_snd(30.0, 36.4, 0.10, pk=33.0, pan0=-0.6, pan1=0.6, rate=11.0, shape=(sm(30.0, 32.0, t) * (1 - sm(34.5, 36.4, t))) * 0.5)
heli_snd(37.0, 40.5, 0.38, pk=38.4, pan0=0.8, pan1=-0.8, rate=11.5, shape=(sm(37.0, 38.4, t) * (1 - sm(38.4, 40.5, t))) ** 1.2)
add(lp(noise(), 140) * 0.09 * win(40.4, 53.0, .8, .8))
for tk in np.arange(41.0, 52.5, 1.25): tink(tk, 1500 + 90 * rnd(), 0.018, 0.5, 34)                       # IV drips
steps(41.4, 43.2, 0.7, 0.025)
for i in range(28): burst(47.4 + i * (0.08 + 0.004 * i), 0.03, 800, 3500, 0.03, 0.4, 60)                 # scale needle ticks
burst(47.2, 0.3, 200, 1200, 0.05, 0.4, 12)
add(bp(noise(), 150, 500) * 0.05 * win(50.6, 53.0, .4, .5))
add(lp(noise(), 130) * 0.08 * win(52.9, 60.6, .8, .8))
for tk in np.arange(53.4, 60.2, 1.0): tink(tk, 3100, 0.012, -0.6, 90)                                    # wall clock
steps(54.0, 59.5, 0.65, 0.03)
for r0 in (60.5, 62.0): am_buzz(r0, r0 + 0.8, 1100, 2400, 22, 0.07, -0.5); am_buzz(r0 + 0.9, r0 + 1.3, 1100, 2400, 22, 0.05, -0.5)   # phone ring
add(lp(noise(), 130) * 0.08 * win(60.5, 69.5, .6, 1.0))
for tk in np.arange(64.6, 69.0, 1.1): thump(tk, 52, 0.09, 0.4); thump(tk + 0.28, 46, 0.05, 0.4)
heli_snd(65.5, 69.3, 0.08, pk=67.0, pan0=-0.5, pan1=0.5, rate=11.0, shape=(sm(65.5, 67.0, t) * (1 - sm(67.5, 69.3, t))) * 0.5)
add(bp(noise(), 150, 700) * 0.08 * win(69.3, 78.0, 1.0, .8) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.2 * t)))    # desert dawn wind
steps(69.6, 73.4, 0.55, 0.04); steps(76.0, 77.9, 0.5, 0.045)
for tk in np.arange(74.2, 76.0, 0.13): burst(tk, 0.05, 300, 1500, 0.02, 0.0, 40)                        # dots appearing
burst(76.0, 0.7, 800, 5000, 0.05, 0.3, 5)                                                                 # arrow whoosh
for i in range(6): pinpop(78.0 + i * 0.35, 0.035)
thump(80.0, 44, 0.15, 0.9)
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.DP7 - 0.7, HS.DP7 - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_pros7.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
