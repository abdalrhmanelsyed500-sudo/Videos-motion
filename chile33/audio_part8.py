"""Part 7 mix (NO MUSIC, SFX only - user request): Arabic voice (part8.wav) + procedural ambience/SFX synced to part8_scenes timeline. Output build/mix_part8.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import part8_scenes as HS
SR = 44100; N = int(HS.D8 * SR); t = np.arange(N) / SR
rg = np.random.default_rng(8)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/part8.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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
D = HS.D8
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

# ---------- Part 8 SFX timeline
D = HS.D8
# 0-4.5 celebration: crowd cheer noise, fireworks pops, then fades
add(bp(noise(), 300, 2800) * 0.20 * win(0, 4.6, .2, 1.0) * (0.7 + 0.3 * np.sin(2 * math.pi * 3.1 * t)))
for tk in (0.2, 0.6, 1.1, 2.6, 3.0, 3.5): burst(tk, 0.5, 300, 5000, 0.09, rnd() * 1.4, 6); thump(tk, 70, 0.14, 0.4, rnd())
# 4.5-6.6 camera shutters and flashes
for tk in np.arange(4.7, 6.6, 0.07): burst(tk + rnd() * 0.03, 0.04, 2500, 9000, 0.06, rnd() * 1.6, 70)
add(bp(noise(), 400, 3000) * 0.10 * win(4.5, 6.8, .4, .5))
# 6.6-8.9 sudden quiet; low room tone
add(lp(noise(), 100) * 0.12 * win(6.8, D, .6, 1.0))
thump(7.0, 45, 0.20, 0.8)
# 11-15 room: slow heartbeat low
for tb in np.arange(11.6, 15.0, 1.1): thump(tb, 55, 0.14, 0.4); thump(tb + 0.22, 48, 0.10, 0.4)
# 15-18 sun: wind
add(bp(noise(), 200, 1400) * 0.10 * win(15.0, 18.3, .6, .6) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.3 * t)))
# 18-20.6 anxiety: heartbeat faster, breath
for tb in np.arange(18.3, 20.7, 0.45): thump(tb, 58, 0.15, 0.3); thump(tb + 0.12, 50, 0.10, 0.3)
am_buzz(19.9, 20.6, 1500, 5000, 30, 0.05, 0.0)
# 20.6-21.35 nightmare: rumble, then gasp / hit
add(lp(noise(), 160) * 0.30 * win(20.5, 21.2, .3, .15)); burst(20.95, 0.45, 800, 4000, 0.12, 0.0, 10); thump(21.0, 60, 0.30, 0.6)
# 21.35-22.65 depression: very low tone-less hush
add(lp(noise(), 70) * 0.18 * win(21.3, 22.8, .3, .5))
# 22.65-25.25 street: footsteps, traffic hum, passers
add(bp(noise(), 120, 900) * 0.08 * win(22.6, 25.3, .4, .4) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.7 * t)))
for tk in np.arange(22.7, 25.2, 0.31): burst(tk, 0.05, 200, 1100, 0.04, rnd() * 1.6, 40)
burst(23.4, 0.3, 500, 2500, 0.05, -0.7, 12); burst(24.2, 0.3, 500, 2500, 0.05, 0.8, 12)
# 25.25-28.7 mine gate: wind, rusty creak, slow steps
add(bp(noise(), 150, 1200) * 0.12 * win(25.2, 28.8, .5, .6) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.4 * t)))
creak(26.55, 0.8, 380, 250, 0.08, 0.3); creak(27.9, 0.7, 260, 400, 0.05, 0.3)
for tk in np.arange(25.4, 26.5, 0.4): burst(tk, 0.06, 150, 900, 0.05, 0.0, 30)
for tk in np.arange(27.2, 28.2, 0.4): burst(tk, 0.06, 150, 900, 0.05, 0.0, 30)
# 28.7-37.1 fame: shutter storm growing, mic bumps, coins, lens motor whirs
for tk in np.arange(28.8, 37.1, 0.09): 
    if rg.random() < 0.55: burst(tk, 0.04, 2500, 9000, 0.04 + 0.03 * min(1, (tk - 28.8) / 6), rnd() * 1.7, 70)
for tk in (32.6, 32.8, 33.0, 33.2): burst(tk, 0.12, 80, 500, 0.12, rnd() * 1.4, 25); thump(tk, 90, 0.10, 0.2)
for tk in np.arange(33.5, 34.6, 0.1): tink(tk + rnd() * 0.04, 3200 + 1200 * rnd(), 0.04, rnd() * 1.6, 28)
burst(33.9, 0.5, 300, 2500, 0.09, -0.5, 6); burst(34.1, 0.5, 300, 2500, 0.09, 0.5, 6)
for tk in np.arange(34.6, 36.6, 0.33): am_buzz(tk, tk + 0.25, 1200, 4500, 38, 0.05, rnd() * 1.6)
# 37.1-39.7 flashes die out, hush
add(lp(noise(), 90) * 0.14 * win(37.4, D, .8, 1.0))
# 39.7-end window: night room tone, first birds at dawn (noise chirps, not melodic)
add(bp(noise(), 120, 500) * 0.05 * win(39.6, D, .5, 1.0))
for tk in (43.0, 43.4, 43.7, 44.1): burst(tk, 0.07, 3500, 6500, 0.035, rnd() * 1.0, 40); burst(tk + 0.09, 0.06, 4200, 7000, 0.03, rnd() * 1.0, 45)
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.D8 - 0.7, HS.D8 - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_part8.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
