"""Part 4 mix (NO MUSIC, SFX only - user request): Arabic voice (part4.wav) + procedural ambience/SFX synced to part4_scenes timeline. Output build/mix_part3.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import part4_scenes as HS
SR = 44100; N = int(HS.D4 * SR); t = np.arange(N) / SR
rg = np.random.default_rng(7)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/part4.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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
D = HS.D4
add(lp(noise(), 120) * 0.20 * win(0, D, .6, 1.2) * (0.8 + 0.2 * np.sin(2 * math.pi * 0.11 * t)))
add(hp(noise(), 3000) * 0.025 * win(0, 6.5, .4, .8))
rs = np.random.default_rng(11)
def tink(t0, f, amp, pan=0.0, dec=26):
    i0 = int(t0 * SR); n = int(0.5 * SR)
    if i0 + n > N: return
    tt = np.arange(n) / SR; x = (np.sin(2 * math.pi * f * tt) + 0.5 * np.sin(2 * math.pi * f * 2.76 * tt) + 0.3 * np.sin(2 * math.pi * f * 5.4 * tt)) * np.exp(-tt * dec) * amp
    s_ = np.zeros(N, np.float32); s_[i0:i0 + n] = x; add(s_, pan)
def creak(t0, dur, f0, f1, amp, pan=0.0):
    i0 = int(t0 * SR); n = int(dur * SR); tt = np.arange(n) / SR; fr = f0 + (f1 - f0) * tt / dur
    ph = 2 * math.pi * np.cumsum(fr) / SR; x = (np.sin(ph) * np.sign(np.sin(ph * 0.31 + 1)) * 0.5 + 0.5 * np.sin(ph * 2.01)) * np.sin(math.pi * tt / dur) ** 1.5 * (0.6 + 0.4 * np.sin(2 * math.pi * 31 * tt)) * amp
    s_ = np.zeros(N, np.float32); s_[i0:i0 + n] = x; add(s_, pan)

def rnd(): return rs.random() - .5
# 0-6 hunger / heat / dust: stomach growls, breaths, dust hiss
for t0_ in (1.0, 3.0, 4.6):
    i0 = int(t0_ * SR); n = int(1.1 * SR); tt = np.arange(n) / SR
    gr = lp(rg.normal(0, 1, n).astype(np.float32), 150) * (0.6 + 0.4 * np.sin(2 * math.pi * 7 * tt)) * np.sin(math.pi * tt / 1.1) * 0.45; s_ = np.zeros(N, np.float32); s_[i0:i0 + n] = gr; add(s_, 0.1)
for tb in np.arange(0.4, 6.0, 0.9): burst(tb, 0.4, 300, 1500, 0.045, rnd() * 1.4, 6)
creak(6.2, 1.6, 120, 90, 0.07, -0.2); burst(7.0, 0.6, 200, 1500, 0.06, 0.2, 5)
# 9-12 no sense of time: erratic ticks
for tt_ in (9.3, 9.6, 10.2, 10.35, 10.9, 11.0, 11.7, 12.1): tink(tt_, 2800 + 400 * rnd(), 0.06, 0.2, 60)
# 12-22 drilling sounds from far: rattling thuds, hope, then silence + dash thump
from_ = HS.SND
for a, b in from_:
    d_ = b - a; i0 = int(a * SR); n = int(d_ * SR); tt = np.arange(n) / SR
    buzz = bp(rg.normal(0, 1, n).astype(np.float32), 70, 380) * (0.5 + 0.5 * np.sign(np.sin(2 * math.pi * 11 * tt))) * np.sin(math.pi * tt / d_) ** 0.6 * 0.5
    s_ = np.zeros(N, np.float32); s_[i0:i0 + n] = buzz; add(s_, 0.3)
    for tk in np.arange(a, b, 0.18): burst(tk, 0.08, 300, 2500, 0.07, 0.3 + .1 * rnd(), 40)
    thump(b + 0.1, 45, 0.25, 0.9)   # hope dashed
add(hp(noise(), 2500) * 0.02 * win(12.4, 22.0, .6, .6))
# 22-29 vigil: crowd murmur, candle crackle, sobs
add(bp(noise(), 250, 1200) * 0.06 * win(22.1, 29.1, .8, .6) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.35 * t)), 0.0)
for tc in np.arange(22.4, 29.0, 0.23): burst(tc, 0.05, 2000, 8000, 0.04, rnd() * 1.6, 60)
for tsb in (24.6, 25.4, 26.6, 27.3): burst(tsb, 0.5, 500, 1800, 0.05, rnd() * 1.4, 5)
# 29-34 rig: heavy machinery rumble + clanks
mod = 0.5 + 0.5 * np.sign(np.sin(2 * math.pi * 6 * t))
add(bp(noise(), 60, 300) * 0.22 * mod * win(29.0, 34.1, .5, .6), -0.1)
for tk in np.arange(29.4, 34.0, 0.6): tink(tk, 900 + 200 * rnd(), 0.05, rnd(), 16)
# 34-38 Urzua decides: a footstep, a firm thump
thump(34.5, 60, 0.2, 0.5); burst(34.5, 0.2, 300, 2500, 0.1, 0, 20)
# 38.8-41.5 map: pencil scratches, taps for the coloured marks
for tk in np.arange(38.9, 40.4, 0.11): burst(tk, 0.1, 3000, 9000, 0.05, 0.1, 30)
for j in range(5): tink(40.55 + 0.18 * j, 1800 + 150 * j, 0.05, 0.1, 40)
# 41-46 rest/sleep times: tick-tock, then ticks speeding as time is lost
for tk in np.arange(41.7, 46.0, 0.5): tink(tk, 2800, 0.05, 0.2, 60)
# 46-50 mind: low heartbeat
for tb in np.arange(46.3, 50.2, 1.0): thump(tb, 55, 0.2, 0.35); thump(tb + 0.27, 50, 0.12, 0.3)
# 50-55 lights: lamp clicks, day/night
burst(50.5, 0.1, 800, 5000, 0.14, -0.4, 40); tink(50.55, 1500, 0.05, -0.4, 40); burst(51.1, 0.1, 800, 5000, 0.12, 0.4, 40)
burst(52.9, 0.1, 800, 5000, 0.12, -0.4, 40); burst(53.6, 0.1, 800, 5000, 0.12, 0.4, 40)
add(lp(noise(), 400) * 0.05 * win(53.5, 55.0, .6, .5) * (0.5 + 0.5 * np.sin(2 * math.pi * 0.28 * t)), 0.0)
# 55-60 routine: shuffles, men lying down (thump), sitting, gathering
for tk in np.arange(55.0, 60.0, 0.38): burst(tk, 0.15, 400, 2800, 0.05, rnd() * 1.4, 22)
for tl in (55.4, 55.8, 56.1): thump(tl, 70, 0.12, 0.2, -0.6); burst(tl, 0.15, 300, 2000, 0.08, -0.6, 20)
add(lp(noise(), 300) * 0.04 * win(56.0, 57.5, .4, .4) * (0.5 + 0.5 * np.sin(2 * math.pi * 0.3 * t)), -0.5)
# 60-64 tasks: cans, water pouring, crates
for tt_, f in ((60.8, 2100), (61.1, 1800), (61.5, 2300)): tink(tt_, f, 0.07, 0.1, 24); thump(tt_, 140, 0.07, 0.15, 0.1)
add(bp(noise(), 1500, 5000) * 0.05 * win(62.2, 63.4, .15, .25) * (0.6 + 0.4 * np.sin(2 * math.pi * 17 * t)), 0.3)
# 64-70 Yonni: cloth, a soft cough
for tk in np.arange(65.0, 68.8, 0.45): burst(tk, 0.2, 500, 3000, 0.04, 0.1, 14)
burst(66.5, 0.18, 300, 1800, 0.1, 0.4, 13)
# 70-79 writing: pencil scratches on notebook / paper
for tk in np.arange(70.0, 72.6, 0.12): burst(tk, 0.1, 3000, 9000, 0.05, 0.0, 30)
for tk in np.arange(72.8, 78.0, 0.14): burst(tk, 0.1, 3000, 9000, 0.05, 0.1, 30)
# 78.7-88 joke: laughter (noise bursts) , claps
for k_ in range(4):
    for tk in np.arange(84.0 + 0.35 * k_, 85.1 + 0.35 * k_, 0.16): burst(tk, 0.13, 500, 2200, 0.05, rnd() * 1.4, 14)
for tk in (86.0, 86.2, 86.5, 87.0): burst(tk, 0.06, 1200, 5000, 0.07, rnd() * 1.4, 40)
# 88-93 fight: shouts (rising noise), shoves, thumps
for tk, p_ in ((88.9, -0.5), (89.6, 0.5), (90.4, -0.3), (91.2, 0.4), (92.0, 0.0)):
    burst(tk, 0.45, 400, 2200, 0.09, p_, 6); thump(tk + 0.1, 70, 0.14, 0.25, p_); burst(tk + 0.1, 0.12, 300, 2000, 0.1, p_, 30)
# 93-99 despair: a lone drip, low breath, silence
for tk in (94.0, 96.0, 98.0): tink(tk, 1400, 0.035, 0.5, 30)
add(lp(noise(), 250) * 0.05 * win(93.5, 99.5, .8, .6) * (0.5 + 0.5 * np.sin(2 * math.pi * 0.22 * t)))
# 99-107: the real question - heartbeat
for tb in np.arange(100.0, 106.5, 1.05): thump(tb, 55, 0.16, 0.35); thump(tb + 0.27, 50, 0.1, 0.3)
# 107-109: something changes - dust falling, rumble rising
add(hp(noise(), 3500) * 0.05 * win(106.8, D, .4, .5)); add(lp(noise(), 150) * 0.18 * win(106.6, D, 1.0, .5), 0.0)
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.D4 - 0.7, HS.D4 - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_part4.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
