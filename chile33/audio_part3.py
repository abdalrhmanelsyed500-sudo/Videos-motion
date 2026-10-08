"""Part 3 mix (NO MUSIC, SFX only - user request): Arabic voice (hook.wav) + procedural ambience/SFX synced to part3_scenes timeline. Output build/mix_part3.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import part3_scenes as HS
SR = 44100; N = int(HS.D3 * SR); t = np.arange(N) / SR
rg = np.random.default_rng(7)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/part3.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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

# ---- beds (NO MUSIC: noise-based ambience and SFX only)
add(lp(noise(), 120) * 0.22 * win(0, 5.5, .3, .6) + lp(noise(), 130) * 0.26 * win(5.0, 62.0, .6, 1.0))
add(bp(noise(), 250, 1400) * 0.035 * win(0, 3.6, .1, .8) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.2 * t)), -0.3)
add(bp(noise(), 300, 1500) * 0.05 * win(60.0, 62.7, .4, .6) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.3 * t)))
def tink(t0, f, amp, pan=0.0, dec=26):
    i0 = int(t0 * SR); n = int(0.5 * SR)
    if i0 + n > N: return
    tt = np.arange(n) / SR; x = (np.sin(2 * math.pi * f * tt) + 0.5 * np.sin(2 * math.pi * f * 2.76 * tt) + 0.3 * np.sin(2 * math.pi * f * 5.4 * tt)) * np.exp(-tt * dec) * amp
    s_ = np.zeros(N, np.float32); s_[i0:i0 + n] = x; add(s_, pan)
def creak(t0, dur, f0, f1, amp, pan=0.0):
    i0 = int(t0 * SR); n = int(dur * SR); tt = np.arange(n) / SR; fr = f0 + (f1 - f0) * tt / dur
    ph = 2 * math.pi * np.cumsum(fr) / SR; x = (np.sin(ph) * np.sign(np.sin(ph * 0.31 + 1)) * 0.5 + 0.5 * np.sin(ph * 2.01)) * np.sin(math.pi * tt / dur) ** 1.5 * (0.6 + 0.4 * np.sin(2 * math.pi * 31 * tt)) * amp
    s_ = np.zeros(N, np.float32); s_[i0:i0 + n] = x; add(s_, pan)
# door: faint distant drips and shuffles
for td in (0.8, 2.3): tink(td, 1800, 0.035, 0.5, 40)
for ts in np.arange(1.9, 3.3, 0.55): burst(ts, 0.2, 300, 2500, 0.05, (np.random.rand() - .5), 18)
# the file of men entering (12 walkers), footsteps while on screen
for c in HS.ENTER:
    ts = c['t0'] + 0.15
    while ts < c['t0'] + c['dur'] - 0.2:
        u = (ts - c['t0']) / c['dur']; burst(ts, 0.2, 350, 2600, 0.12 * (1 - 0.7 * u), -0.6 + 1.2 * u, 20); ts += 0.46
# heat, bad air: heavy breathing + hiss, coughs, fanning swishes
add(hp(noise(), 2500) * 0.035 * win(7.6, 11.2, .6, .6))
for tb in np.arange(7.9, 11.0, 0.75): burst(tb, 0.35, 300, 1500, 0.05, (np.random.rand() - .5) * 1.4, 6)
for tc in (9.55, 9.8, 10.3): burst(tc, 0.18, 300, 1800, 0.12, -0.2, 13)
for tf in np.arange(8.2, 9.4, 0.33): burst(tf, 0.2, 1200, 4500, 0.05, 0.4, 14)
# searching: shuffle, locker creak, crate scrape and thud
for ts in np.arange(11.2, 13.9, 0.42): burst(ts, 0.15, 400, 2800, 0.05, (np.random.rand() - .5) * 1.2, 22)
creak(11.9, 0.9, 380, 300, 0.07, -0.4); tink(12.9, 900, 0.04, -0.4, 14)
burst(14.1, 1.2, 300, 2200, 0.09, -0.2, 2.5); thump(15.38, 80, 0.4, 0.4, -0.2); burst(15.38, 0.3, 200, 2500, 0.2, -0.2, 14)
# the stock: tuna cans, milk, biscuits, peaches
for tt_, f, p in ((15.81, 2100, 0.0), (16.0, 1850, 0.1), (16.2, 2350, 0.2), (18.6, 1600, -0.3)): tink(tt_ + 0.05, f, 0.12, p, 22); thump(tt_ + 0.05, 140, 0.1, 0.15, p)
thump(16.8, 120, 0.2, 0.25, 0.3); burst(16.8, 0.2, 200, 1500, 0.1, 0.3, 18)
for k_ in range(6): burst(17.86 + 0.07 * k_, 0.07, 3000, 9000, 0.06, 0.5, 40)
# 'وبس' beat: quiet, one low thud
thump(19.9, 50, 0.18, 0.5)
# fast clock (two days): rapid ticks, then settle
for tt_ in np.arange(21.2, 23.5, 0.1): tink(tt_, 3300, 0.045, 0.2, 90)
# counting 33: soft pops
for i in range(0, 33, 2): burst(23.75 + 0.034 * i, 0.06, 500, 2500, 0.07, -0.8 + 1.6 * (i % 11) / 11, 60)
# eating normally: chewing crunches, quick
r_ = np.random.default_rng(3)
for tt_ in np.arange(26.8, 28.8, 0.13): burst(tt_ + r_.random() * 0.05, 0.08, 800, 5000, 0.07 + 0.04 * r_.random(), (r_.random() - .5) * 1.4, 40)
tink(27.1, 2000, 0.06, 0.0); tink(27.9, 1700, 0.06, 0.2)
# the weak wait: heartbeat (a body sound) and slow breaths
for tb in np.arange(29.5, 32.1, 0.95): thump(tb, 55, 0.22, 0.35); thump(tb + 0.27, 50, 0.14, 0.3)
for tb in (29.8, 31.3): burst(tb, 0.9, 200, 1200, 0.04, 0.0, 3)
# Urzua: footstep + low thud as he decides
thump(32.8, 60, 0.15, 0.4)
# food as time: a slow, loud clock (tick - tock) under his speech
for k_, tt_ in enumerate(np.arange(35.3, 40.3, 1.0)): tink(tt_, 2800, 0.07, 0.2, 60); tink(tt_ + 0.5, 2200, 0.05, 0.2, 60)
tink(37.95, 3000, 0.12, 0.2, 18); burst(37.95, 0.4, 300, 3000, 0.08, 0.2, 8)
burst(39.3, 0.12, 400, 2000, 0.1, 0.0, 30); burst(39.7, 0.12, 400, 2000, 0.1, 0.0, 30)   # finger taps on the table
# tiny rations: cans, milk, biscuit
for tt_, f in ((41.5, 2100), (41.62, 1900), (41.74, 2300)): tink(tt_ + 0.1, f, 0.07, -0.2, 26)
for tt_ in (43.7, 43.82, 43.94): thump(tt_ + 0.1, 130, 0.07, 0.15, 0.2); burst(tt_ + 0.1, 0.15, 200, 1200, 0.05, 0.2, 18)
for k_ in range(3): burst(44.7 + 0.12 * k_, 0.06, 3000, 9000, 0.05, 0.3, 40)
# plan, not hunger: stomach growl, a hand reaches then withdraws
i0 = int(46.4 * SR); n = int(1.3 * SR); tt = np.arange(n) / SR
gr = lp(rg.normal(0, 1, n).astype(np.float32), 160) * (0.6 + 0.4 * np.sin(2 * math.pi * 7 * tt)) * np.sin(math.pi * tt / 1.3) * 0.5; s_ = np.zeros(N, np.float32); s_[i0:i0 + n] = gr; add(s_, 0.1)
burst(46.7, 0.2, 800, 4000, 0.04, 0.0, 12); burst(47.3, 0.2, 800, 4000, 0.04, 0.0, 12)
# trust: cloth rustles as arms link, soft pats
for i in range(8): burst(49.8 + 0.12 * i, 0.22, 500, 3500, 0.07, -0.8 + 0.23 * i, 16)
for i in range(8): thump(50.8 + 0.2 * i, 90, 0.07, 0.15, -0.8 + 0.23 * i)
# one man reaches toward the pile: hesitant rustle, tin touch, withdraw
burst(53.8, 0.7, 500, 3000, 0.06, 0.1, 5); tink(54.6, 2100, 0.05, 0.1, 30); burst(55.3, 0.5, 500, 3000, 0.05, 0.1, 6)
for tt_ in np.arange(53.5, 57.7, 1.0): tink(tt_, 2800, 0.04, 0.2, 60)
for tb in np.arange(56.0, 58.0, 0.95): thump(tb, 55, 0.14, 0.35)
# a bigger problem: dust trickling from the ceiling, creaks, a lamp fizzles out
add(hp(noise(), 3500) * 0.05 * win(58.5, 60.3, .5, .4))
creak(58.0, 1.4, 90, 70, 0.10, 0.0); thump(58.8, 45, 0.3, 1.2)
burst(59.3, 0.25, 1500, 7000, 0.18, -0.2, 20); tink(59.5, 1200, 0.05, 0.4, 20)
for tt_ in (58.7, 59.0, 59.6, 59.9, 60.1): burst(tt_, 0.1, 1500, 6000, 0.05, (r_.random() - .5) * 1.4, 40)
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.D3 - 0.7, HS.D3 - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_part3.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
