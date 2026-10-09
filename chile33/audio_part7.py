"""Part 7 mix (NO MUSIC, SFX only - user request): Arabic voice (part7.wav) + procedural ambience/SFX synced to part7_scenes timeline. Output build/mix_part7.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import part7_scenes as HS
SR = 44100; N = int(HS.D7 * SR); t = np.arange(N) / SR
rg = np.random.default_rng(7)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/part7.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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
D = HS.D7
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

# ---------- Part 7 SFX timeline
add(lp(noise(), 130) * 0.14 * win(0, D, .6, 1.0))
# 0-2.3 rigs: engines, hydraulics, wind
add(lp(noise(), 160) * 0.26 * win(0, 2.4, .3, .5) * (0.7 + 0.3 * np.sign(np.sin(2 * math.pi * 5 * t)))); am_buzz(0.1, 2.3, 60, 500, 12, 0.45, 0.0, ramp=True); thump(0.2, 40, 0.3, 1.0)
# 2.3-8.1 drilling down: grind, bit hits, rock cracks
add(bp(noise(), 300, 3000) * 0.08 * win(2.3, 8.1, .4, .4) * (0.6 + 0.4 * np.sign(np.sin(2 * math.pi * 14 * t)))); add(lp(noise(), 100) * 0.18 * win(2.3, 8.2, .4, .4))
for tk in np.arange(2.6, 8.0, 0.55): thump(tk, 60, 0.10, 0.3); burst(tk, 0.12, 400, 3500, 0.05, rnd() * 0.5, 20)
for tk in (6.0, 6.8, 7.6): creak(tk, 0.6, 120, 80, 0.06, 0.2)
# 8.1-9.3 long, 9.3-12.4 danger in the dark: hush, drips, rock tension
add(lp(noise(), 80) * 0.22 * win(9.2, 14.0, .4, .5)); 
for tk in (10.0, 11.1, 12.0): drip(tk)
creak(10.4, 1.4, 90, 60, 0.07, -0.2); burst(11.6, 0.5, 600, 3000, 0.05, 0.3, 6)
# 12.4-14.0 drill reaches, 14.0-16.3 break: snap, falling
burst(13.7, 0.4, 300, 3000, 0.10, 0.0, 9); thump(13.9, 55, 0.25, 0.8); creak(14.1, 1.0, 140, 70, 0.10, 0.0)
for tk in np.arange(14.3, 16.0, 0.17): burst(tk, 0.12, 800, 5000, 0.04, rnd() * 1.4, 18)
# 16.3-24 searching for a way, narrow: scrape, taps
for tk in np.arange(16.4, 19.0, 0.3): tink(tk, 900 + 300 * rnd(), 0.035, rnd(), 28)
burst(19.6, 0.5, 500, 3500, 0.06, 0.3, 7); add(bp(noise(), 400, 2500) * 0.05 * win(20.8, 24.0, .3, .4) * (0.6 + 0.4 * np.sin(2 * math.pi * 5 * t)))
# 24-27.7 draft on the table: pencil, marker
for tk in np.arange(24.3, 26.0, 0.11): burst(tk, 0.1, 3000, 9000, 0.05, 0.0, 30)
for tk in (26.2, 26.8): burst(tk, 0.4, 2500, 8000, 0.07, 0.0, 9)
# 27.7-31.9 reveal: crowd, flashes, metal clang
add(bp(noise(), 200, 1500) * 0.07 * win(27.7, 31.9, .4, .5)); burst(28.0, 0.5, 300, 4000, 0.10, 0.0, 6); tink(28.1, 520, 0.08, 0.0, 6)
# 31.9-46: capsule walk, door, long dark shaft descent, night wait
for tk in np.arange(32.0, 33.4, 0.34): burst(tk, 0.1, 150, 900, 0.06, 0.1, 22)
creak(33.4, 0.9, 200, 150, 0.08, 0.0); thump(34.2, 70, 0.2, 0.5)
add(bp(noise(), 300, 2500) * 0.06 * win(36.0, 42.0, .5, .5) * (0.6 + 0.4 * np.sin(2 * math.pi * 9 * t)))
add(lp(noise(), 90) * 0.20 * win(36.0, 42.5, .5, .5))
for tk in np.arange(42.6, 45.8, 0.5): burst(tk, 0.5, 250, 1400, 0.03, rnd() * 1.4, 5)
add(bp(noise(), 200, 1200) * 0.06 * win(42.5, 46.0, .4, .4))
# 46-51.2 first man enters, door, rise
for tk in np.arange(46.5, 47.6, 0.34): burst(tk, 0.1, 150, 900, 0.06, 0.0, 22)
creak(48.0, 0.9, 220, 140, 0.09, 0.0); thump(48.9, 70, 0.25, 0.6); burst(48.9, 0.3, 400, 3000, 0.10, 0.0, 12)
am_buzz(49.5, 54.7, 80, 600, 9, 0.30, 0.0, ramp=True); add(lp(noise(), 120) * 0.22 * win(49.4, 54.8, .5, .5))
for tk in np.arange(49.8, 54.5, 0.31): tink(tk, 1800 + 500 * rnd(), 0.025, 0.0, 40)
for tk in (52.1, 52.96, 53.76): burst(tk, 0.4, 300, 3000, 0.12, 0.0, 8); thump(tk, 55, 0.25, 0.6)
# 54.5-60 arrival: steam hiss, door, cheering
burst(54.6, 1.5, 3000, 9000, 0.10, 0.0, 2.5); thump(56.3, 50, 0.3, 0.8); creak(56.73, 0.8, 200, 130, 0.08, 0.0); burst(57.0, 0.7, 4000, 10000, 0.07, 0.0, 4)
add(bp(noise(), 300, 2500) * 0.12 * win(58.0, 62.4, .3, .6) * (0.7 + 0.3 * np.sin(2 * math.pi * 3.1 * t)))
for tk in np.arange(58.2, 61.5, 0.2): burst(tk, 0.12, 200, 1800, 0.05, rnd() * 1.6, 20)
# 62.2-64.7 camera clicks and flashes, families
for tk in np.arange(62.2, 63.0, 0.07): burst(tk, 0.05, 2500, 9000, 0.09, rnd() * 1.6, 40)
add(bp(noise(), 300, 2500) * 0.08 * win(62.8, 64.8, .3, .4))
# 64.7-68.5 sun, wind
add(bp(noise(), 400, 2500) * 0.05 * win(64.7, 68.6, .6, .5) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.3 * t)))
# 68.5-83: more arrivals: every cycle has hiss, door, cheer
for ta in (68.0, 78.2, 80.4, 81.7):
    burst(ta, 0.9, 3000, 9000, 0.07, 0.0, 3); creak(ta + 0.7, 0.6, 220, 150, 0.06, 0.0)
    add(bp(noise(), 300, 2500) * 0.09 * win(ta + 0.5, ta + 2.0, .2, .5))
add(bp(noise(), 300, 2500) * 0.10 * win(68.5, 72.0, .3, .5))
add(bp(noise(), 300, 2500) * 0.10 * win(72.0, 75.4, .3, .5) * 0.5)
am_buzz(75.5, 78.0, 80, 600, 9, 0.28, 0.0, ramp=True)
# 83-95 fewer: crowd murmur fades; hush; a heartbeat
add(bp(noise(), 250, 1400) * 0.08 * win(83.0, 89.8, .4, 2.0) * (1 - 0.6 * sm(83.1, 89.5, t)))
for tk in (84.5, 86.5, 87.9, 89.0): thump(tk, 60, 0.14, 0.5)
add(lp(noise(), 90) * 0.20 * win(88.0, 95.2, 1.0, .5))
for tb in np.arange(90.0, 93.6, 1.0): thump(tb, 52, 0.16, 0.4)
drip(91.0); drip(92.8)
# 95.1-99.8 last man enters, door, rise; climbing
for tk in np.arange(95.1, 96.0, 0.34): burst(tk, 0.1, 150, 900, 0.05, 0.0, 22)
creak(96.9, 0.9, 220, 140, 0.09, 0.0); thump(97.8, 70, 0.25, 0.6); burst(97.8, 0.3, 400, 3000, 0.10, 0.0, 12)
am_buzz(98.5, 103.9, 80, 600, 9, 0.30, 0.0, ramp=True); add(lp(noise(), 120) * 0.2 * win(98.4, 104.0, .5, .5))
for tk in np.arange(99.0, 103.8, 0.31): tink(tk, 1800 + 500 * rnd(), 0.025, 0.0, 40)
# 103.9-105.8 Urzua emerges: hiss, door, roar of joy
burst(103.7, 1.3, 3000, 9000, 0.10, 0.0, 3); thump(104.3, 50, 0.3, 0.8); creak(104.4, 0.8, 200, 130, 0.08, 0.0)
add(bp(noise(), 300, 2800) * 0.18 * win(104.8, 108.9, .3, .8) * (0.7 + 0.3 * np.sin(2 * math.pi * 3.1 * t)))
for tk in np.arange(105.0, 108.5, 0.17): burst(tk, 0.12, 200, 1800, 0.05, rnd() * 1.6, 20)
# fireworks
for tk in (106.0, 106.35, 106.75, 107.2, 107.5, 107.9): burst(tk, 0.5, 300, 5000, 0.10, rnd() * 1.4, 6); thump(tk, 70, 0.18, 0.4, rnd()); burst(tk + 0.2, 0.6, 3000, 9000, 0.05, rnd() * 1.4, 5)
# 108.7-end 69 tally scratches, then quiet
for i in range(69): burst(108.7 + 0.033 * i, 0.05, 2500, 8000, 0.05, rnd() * 0.6, 40)
add(lp(noise(), 90) * 0.16 * win(108.6, D, .3, .8))
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.D7 - 0.7, HS.D7 - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_part7.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
