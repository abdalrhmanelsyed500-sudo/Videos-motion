"""Part 7 mix (NO MUSIC, SFX only - user request): Arabic voice (part9.wav) + procedural ambience/SFX synced to part9_scenes timeline. Output build/mix_part9.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import part9_scenes as HS
SR = 44100; N = int(HS.D9 * SR); t = np.arange(N) / SR
rg = np.random.default_rng(9)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/part9.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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
D = HS.D9
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

# ---------- Part 9 SFX timeline
D = HS.D9
def tickrow(t0, t1, step, amp=0.05, f=2200): 
    for tk in np.arange(t0, t1, step): tink(tk, f, amp, 0.2, 60)
def steps(t0, t1, step, amp=0.05, pan=0.0):
    for tk in np.arange(t0, t1, step): burst(tk + rnd() * 0.04, 0.06, 150, 900, amp, pan + rnd() * 0.6, 30)
def murmur(t0, t1, amp=0.08): add(bp(noise(), 200, 1800) * amp * win(t0, t1, .4, .4) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.9 * t)))
# 0-2.5 desert wind + far machinery
add(bp(noise(), 150, 1100) * 0.10 * win(0, 2.7, .3, .5) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.5 * t))); add(lp(noise(), 90) * 0.10 * win(0, 2.7, .3, .5))
# 2.5-3.95 33 men appear: soft steps; 3.95-5.05 tally scratches; 5.05-6.6 deep rock rumble
steps(2.55, 3.95, 0.045, 0.045)
for i in range(19): burst(4.0 + 0.055 * i, 0.05, 2500, 8000, 0.05, rnd() * 0.6, 40)
add(lp(noise(), 110) * 0.28 * win(5.0, 6.8, .3, .5)); thump(5.1, 45, 0.25, 0.9)
# 6.6-9.5 hush, low room tone; 9.5-11.75 door creak
add(lp(noise(), 90) * 0.12 * win(6.5, 11.8, .5, .5)); creak(9.7, 1.3, 230, 150, 0.08, 0.0); thump(10.9, 60, 0.16, 0.5)
# 11.75-14.3 clock ticking; 14.3-16.55 cans clink
tickrow(11.8, 14.3, 0.25, 0.05); 
for tk in (14.8, 15.2, 15.55, 15.9, 16.2): tink(tk, 1700 + 500 * rnd(), 0.05, rnd(), 24); burst(tk, 0.06, 500, 3000, 0.04, rnd(), 25)
# 16.55-20.4 lamp switch clicks, murmur
burst(16.7, 0.05, 1000, 5000, 0.10, -0.6, 40); burst(18.6, 0.05, 1000, 5000, 0.10, -0.6, 40); burst(19.1, 0.06, 1000, 5000, 0.12, -0.6, 40); murmur(19.3, 20.6, 0.06)
# 20.4-22.8 fear: heartbeat + hush; 22.8-24.1 chores
for tb in np.arange(20.5, 22.8, 0.8): thump(tb, 55, 0.14, 0.4); thump(tb + 0.2, 48, 0.10, 0.4)
add(lp(noise(), 100) * 0.12 * win(20.4, 22.9, .3, .3)); murmur(22.8, 24.2, 0.07); steps(22.9, 24.0, 0.3, 0.04)
# 24.1-26.9 waiting: drips, far drilling; 26.9-29.2 pencil lines
for tk in (24.5, 25.4, 26.3): tink(tk, 1500 + 300 * rnd(), 0.04, 0.3, 30)
am_buzz(24.1, 26.9, 60, 300, 8, 0.08, 0.0)
for tk in np.arange(27.0, 28.4, 0.12): burst(tk, 0.09, 1500, 6000, 0.035, 0.2, 18)
# 29.2-32.25 murmur; 32.25-35.2 capsule: cable hum and thump; 35.2-38.4 steps
murmur(29.2, 32.3, 0.07)
add(bp(noise(), 120, 700) * 0.14 * win(32.2, 35.3, .4, .4) * (0.7 + 0.3 * np.sin(2 * math.pi * 3 * t))); thump(32.4, 50, 0.20, 0.8)
steps(35.4, 37.3, 0.38, 0.05); murmur(37.4, 38.5, 0.08); steps(38.5, 39.9, 0.4, 0.05)
# 40-43.6 soft cheer and fireworks; 43.6-48.2 hush with drips; 48.2-50.4 clock
add(bp(noise(), 300, 2800) * 0.13 * win(40.0, 43.8, .3, .8) * (0.7 + 0.3 * np.sin(2 * math.pi * 3.1 * t)))
for tk in (40.4, 41.1, 42.0): burst(tk, 0.5, 300, 5000, 0.07, rnd() * 1.4, 6); thump(tk, 70, 0.12, 0.4, rnd())
add(lp(noise(), 90) * 0.11 * win(43.6, 48.4, .5, .4)); tink(44.8, 1400, 0.035, 0.3, 30); tink(46.7, 1500, 0.035, -0.3, 30)
tickrow(48.2, 50.4, 0.25, 0.05)
# 50.4-53 sparkle pops; 53-56.6 murmurs, surprised gasps; 56.6-59.6 hush; UI sounds
for tk in np.arange(50.8, 52.8, 0.17): burst(tk, 0.03, 3500, 9000, 0.03, rnd() * 1.4, 80)
murmur(53.0, 56.6, 0.09); burst(53.5, 0.35, 500, 2500, 0.07, 0.0, 8)
add(lp(noise(), 80) * 0.09 * win(56.5, 59.7, .4, .3))
burst(59.68, 0.15, 800, 6000, 0.13, 0.0, 28); tink(59.7, 1800, 0.07, 0.0, 22)       # like pop
burst(60.95, 0.06, 1000, 5000, 0.10, 0.2, 60); burst(61.2, 0.07, 1500, 6000, 0.16, 0.2, 55)   # subscribe click
for k_, tk in enumerate(np.arange(61.6, 62.4, 0.11)): tink(tk, 2300 + (k_ % 2) * 40, 0.06 * math.exp(-k_ * 0.2), 0.5, 18)    # bell rings (metal, no melody)
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.D9 - 0.7, HS.D9 - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_part9.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
