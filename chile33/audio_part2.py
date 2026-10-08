"""Part 2 mix: Arabic voice (hook.wav) + procedural ambience/SFX synced to part2_scenes timeline. Output build/mix_part2.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import part2_scenes as HS
SR = 44100; N = int(HS.D2 * SR); t = np.arange(N) / SR
rg = np.random.default_rng(7)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/part2.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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

# ---- beds
wind = bp(noise(), 250, 1400, 2); wind *= 0.5 + 0.5 * np.sin(2 * math.pi * 0.13 * t + 1) * np.sin(2 * math.pi * 0.07 * t)
add(wind * 0.07 * (win(0, 5.9, 0.1, 0.9) + 0.9 * win(21.2, 24.6, 0.4, 0.5) + 1.2 * win(24.4, 28.2, 0.5, 0.5) + 1.2 * win(33.0, 44.0, 0.6, 0.6)))
drone = (np.sin(2 * math.pi * 55 * t) + 0.6 * np.sin(2 * math.pi * 82.4 * t + 1) + 0.3 * np.sin(2 * math.pi * 110.3 * t)) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.09 * t))
add(drone * 0.05 * (0.3 * win(5.7, 16.6, .6, .6) + 0.3 * win(28.0, 33.4, .6, .6) + 0.9 * win(43.8, 63.3, 1, 1.5) + 1.2 * win(16.4, 19.3, .4, .5)))
add(lp(noise(), 120) * 0.25 * win(5.7, 16.5, 0.6, 0.6) + lp(noise(), 130) * 0.22 * win(28.0, 33.4, .6, .6) + lp(noise(), 130) * 0.2 * win(43.8, 63.3, 1.0, 1.0))
# machinery far away at the mine, rhythmic pick/hammer taps in the tunnel
for th in np.arange(7.0, 9.0, 0.78): burst(th, 0.12, 900, 3500, 0.07, 0.3, 40); thump(th, 140, 0.03, 0.1, 0.3)
# footsteps of the opening walkers
for c in HS.W2:
    k = int(math.ceil((c['t0'] * 2 * math.pi * 1.1 + c['ph0']) / math.pi))
    while True:
        ts = (k * math.pi - c['ph0']) / (2 * math.pi * 1.1)
        if ts > c['t0'] + c['dur'] + 0.2: break
        u = (ts - c['t0']) / c['dur']; burst(ts, 0.22, 400, 2800, 0.05 + 0.16 * min(1, max(0, u)), (c['xe'] - 640) / 700, 18); k += 1
# coughs (rough breathy bursts)
for tc in (6.3, 6.55, 8.1, 8.35): burst(tc, 0.18, 300, 1800, 0.10, -0.3, 14)
# old collapse in the tunnel: pebbles then dust flash
for e in HS.PEB:
    tl = e['t0'] + math.sqrt(2 * (e['yf'] + 120) / 1500.0); burst(tl, 0.2, 800, 4000, 0.10, (e['x'] - 640) / 640, 22)
burst(11.12, 1.0, 150, 3500, 0.34, 0.0, 4.0); thump(11.12, 70, 0.5, 1.0)
add(hp(noise(), 2000) * 0.05 * win(10.8, 12.6, 0.2, 1.4))
# families: soft plucked Karplus-Strong guitar-ish phrase under the home/street beats
def pluck(t0, f, amp, dur=1.6):
    i0 = int(t0 * SR); n = int(dur * SR); p = int(SR / f); buf = rg.uniform(-1, 1, p).astype(np.float32); out = np.zeros(n, np.float32)
    for i in range(n):
        out[i] = buf[i % p]; buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
    seg_ = np.zeros(N, np.float32); seg_[i0:i0 + n] = out * amp * np.exp(-np.arange(n) / SR * 1.4); add(seg_, -0.2)
mel = [(16.5, 220.0), (17.1, 261.6), (17.8, 329.6), (19.2, 293.7), (19.75, 329.6), (20.3, 392.0), (20.9, 349.2), (21.45, 329.6), (22.0, 293.7), (22.55, 261.6), (23.1, 329.6), (23.7, 392.0), (24.2, 329.6)]
for tp, f in mel: pluck(tp, f, 0.16)
add(0.02 * (np.sin(2 * math.pi * 220 * t) + 0.5 * np.sin(2 * math.pi * 329.6 * t)) * win(19.0, 24.6, 0.8, 0.8))
# kids / town: distant voices murmur + laughs of the men with Mario
add(bp(noise(), 500, 2200) * 0.05 * (0.6 + 0.4 * np.sin(2 * math.pi * 3.1 * t)) * win(22.1, 24.8, .2, .5), 0.0)
for tl in (29.5, 29.95, 30.4, 31.2): burst(tl, 0.25, 400, 1800, 0.08, (rg.random() - 0.5) * 1.6, 9)
# birds / street ambience for Jimmy
cr = np.sin(2 * math.pi * 4400 * t) * (np.sin(2 * math.pi * 38 * t) > 0.6) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.7 * t)); add(cr * 0.012 * win(38.0, 43.8, 1.0, 0.8), 0.5)
# the collapse (47.0 thunder, 47.9 quake, 49.35 rocks, 51.25 dust blast)
rum = lp(noise(), 90, 3) + 0.5 * lp(noise(), 220)
rum_env = sm(45.9, 46.9, t) * 0.25 + (t >= 47.0) * (0.55 * np.exp(-np.clip(t - 47.0, 0, None) * 0.5)) + 0.35 * (t >= 47.9) * np.exp(-np.clip(t - 47.9, 0, None) * 0.35)
rum_env = rum_env * (1 - sm(51.5, 56.0, t) * 0.8)
add(rum * rum_env * 1.0)
for tt_, a_ in ((47.0, 1.0), (47.9, 0.9), (49.35, 0.6)): thump(tt_, 62, a_ * 0.95, 1.8); thump(tt_ + 0.02, 38, a_ * 0.8, 2.2); burst(tt_, 1.2, 150, 4000, 0.5 * a_, 0.0, 3.0)
burst(46.3, 1.4, 60, 400, 0.4, 0.0, 2.0)
for e in HS.ROCKS2:
    tl = e['t0'] + math.sqrt(2 * (e['yf'] + 120) / 1500.0); g = 0.15 + 0.7 * e['sc']; burst(tl, 0.35, 120 + 60 * (e['spr'] % 3), 3000, g * 0.5, (e['x'] - 640) / 640, 11); thump(tl, 70 + 10 * e['spr'], g * 0.28, 0.3, (e['x'] - 640) / 640)
burst(51.25, 1.8, 100, 3000, 0.45, 0.0, 1.6); thump(51.3, 45, 0.8, 1.6)
add(hp(noise(), 2000) * 0.07 * win(51.0, 56.0, 0.3, 2.0) + hp(noise(), 3000) * 0.04 * win(47.0, 53.0, 0.5, 1.0))
ring = np.sin(2 * math.pi * 5200 * t) * 0.02 * win(52.0, 58.5, 0.8, 2.5) * (0.7 + 0.3 * np.sin(2 * math.pi * 3 * t)); add(ring, 0.3)
for tb in np.arange(53.9, 61.5, 0.95): thump(tb, 55, 0.24, 0.35); thump(tb + 0.27, 50, 0.15, 0.3)
for td in (55.0, 56.3, 58.8, 61.9): 
    i0 = int(td * SR); n = int(0.3 * SR); tt = np.arange(n) / SR; x = np.sin(2 * math.pi * (1700 + 500 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 28) * 0.07
    s_ = np.zeros(N, np.float32); s_[i0:i0 + n] = x; add(s_, (rg.random() - 0.5) * 1.4)
# dreadful low swell as the mountain closes
pad = (np.sin(2 * math.pi * 55 * t) + 0.5 * np.sin(2 * math.pi * 58.3 * t) + 0.35 * np.sin(2 * math.pi * 82.4 * t)) * (0.8 + 0.2 * np.sin(2 * math.pi * 0.2 * t))
add(pad * 0.10 * sm(57.5, 62.0, t) * (1 - sm(62.6, 63.3, t)))
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.D2 - 0.7, HS.D2 - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_part2.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
