"""Part 1 mix NO MUSIC (drones, pad, tinnitus ring and cricket tones removed): Arabic voice (hook.wav) + procedural ambience/SFX synced to hook_scenes timeline. Output build/mix_hook_nm.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import hook_scenes as HS
SR = 44100; N = int(HS.D * SR); t = np.arange(N) / SR
rg = np.random.default_rng(7)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/hook.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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
add(wind * 0.06 * (win(0, 5.6, 0.1, 1.0) + 1.3 * win(29.0, 41.9, 0.8, 1.2)))                # desert wind (exterior, surface)
add(lp(noise(), 110) * 0.12 * (0.25 + 0.75 * win(4.8, 54, 1, 0.5)))     # underground room tone (noise, no tone)
add(lp(noise(), 90, 3) * 0.20 * (sm(17.8, 20.6, t) * (1 - sm(20.8, 21.6, t))))   # 700 m of rock: pressure (noise)
add(lp(noise(), 120) * 0.25 * win(4.8, 8.0, 0.4, 0.2))                                          # tunnel room tone
add(lp(noise(), 160) * 0.2 * win(21.2, 29.4, 1.0, 0.8) + lp(noise(), 160) * 0.16 * win(43.9, 54.0, 1.0, 0.6))  # chamber air
# ---- footsteps
for c in HS.EXT:
    k0 = int(math.ceil((c['t0'] * 2 * math.pi * 1.1 + c['ph0']) / math.pi)); k = k0
    while True:
        ts = (k * math.pi - c['ph0']) / (2 * math.pi * 1.1)
        if ts > c['t0'] + c['dur'] + 0.2: break
        u = (ts - c['t0']) / c['dur']; g = 0.05 + 0.20 * min(1, max(0, u)); burst(ts, 0.22, 400, 2800, g, (c['xe'] - 640) / 700, 18); k += 1
for c in HS.TUN:
    k = int(math.ceil((c['t0'] * 2 * math.pi * 1.1 + c['ph0']) / math.pi))
    while True:
        ts = (k * math.pi - c['ph0']) / (2 * math.pi * 1.1)
        if ts > c['t0'] + c['dur'] + 0.2: break
        u = (ts - c['t0']) / c['dur']; g = 0.03 + 0.10 * min(1, max(0, u)); burst(ts, 0.2, 200, 1800, g, (c['xe'] - 640) / 700, 20); thump(ts, 90, 0.025 * min(1, max(0, u)), 0.15, (c['xe'] - 640) / 700); k += 1
# ---- the collapse
rum = lp(noise(), 90, 3) + 0.5 * lp(noise(), 220)
rum_env = sm(7.7, 8.7, t) * 0.35 + 0.9 * sm(8.70, 8.85, t) * np.exp(-np.clip(t - 8.85, 0, None) * 0.42) * (t > 8.7)
rum_env = rum_env * (1 - sm(12.5, 14.4, t) * 0.85)
add(rum * rum_env * 0.9)
thump(8.72, 62, 0.95, 1.8); thump(8.74, 38, 0.8, 2.2); burst(8.72, 1.2, 150, 4000, 0.5, 0.0, 3.0)
for e in HS.ROCKS:
    tl = e['t0'] + math.sqrt(2 * (e['yf'] + 120) / 1500.0); g = 0.15 + 0.7 * e['sc']; burst(tl, 0.35, 120 + 60 * (e['spr'] % 3), 3000, g * 0.5, (e['x'] - 640) / 640, 11); thump(tl, 70 + 10 * e['spr'], g * 0.28, 0.3, (e['x'] - 640) / 640)
add(hp(noise(), 3000, 2) * 0.05 * win(12.0, 14.2, 0.9, 0.9) + hp(noise(), 2000) * 0.06 * win(8.8, 10.5, 0.2, 1.6))   # dust hiss
ring = 0 * t
# ---- chamber: drips, heartbeat-like low pulse, tins
for td in (22.1, 23.4, 24.35, 25.2, 26.9, 27.8, 28.6, 44.5, 46.1, 47.0, 49.3, 51.0):
    i0 = int(td * SR); n = int(0.3 * SR); tt = np.arange(n) / SR; x = np.sin(2 * math.pi * (1700 + 500 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 28) * 0.07
    s_ = np.zeros(N, np.float32); s_[i0:i0 + n] = x; add(s_, (rg.random() - 0.5) * 1.4)
for tb in np.arange(21.8, 29.0, 1.05): thump(tb, 55, 0.22, 0.35); thump(tb + 0.28, 50, 0.14, 0.3)
for dl, tt0 in ((0, 26.0), (.12, 26.0), (.25, 26.0), (.35, 26.0), (.45, 26.0), (.55, 26.0)):
    i0 = int((tt0 + dl + 0.35) * SR); n = int(0.35 * SR); tt = np.arange(n) / SR
    x = (np.sin(2 * math.pi * 2600 * tt) + 0.6 * np.sin(2 * math.pi * 3900 * tt)) * np.exp(-tt * 22) * 0.06; s_ = np.zeros(N, np.float32); s_[i0:i0 + n] = x; add(s_, 0.0)
# ---- surface: time-lapse whooshes, night crickets, candle hush
def whoosh(a, b, amp):
    n = bp(noise(), 300, 3000, 2); f = np.exp(-((t - (a + b) / 2) ** 2) / (2 * ((b - a) / 4) ** 2)); return n * f * amp
for (a, b, k) in ((33.5, 34.3, 1), (34.4, 35.3, 2), (35.7, 36.7, 7)):
    for j in range(k): w_ = (b - a) / k; add(whoosh(a + j * w_, a + (j + 1) * w_, 0.10))
# ---- finale: warm swell
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.D - 0.5, HS.D - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_hook_nm.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
