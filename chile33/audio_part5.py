"""Part 5 mix (NO MUSIC, SFX only - user request): Arabic voice (part5.wav) + procedural ambience/SFX synced to part5_scenes timeline. Output build/mix_part3.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import part5_scenes as HS
SR = 44100; N = int(HS.D5 * SR); t = np.arange(N) / SR
rg = np.random.default_rng(7)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/part5.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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
D = HS.D5
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
# 0-5.5: the new sound - closer, louder, clearer (three approaches)
for (a, b, am), pn in zip(HS.SND5, (0.4, 0.2, 0.0)):
    am_buzz(a, b, 70, 420, 11, 0.45 * am, pn, ramp=True)
    for tk in np.arange(a, b, 0.17): burst(tk, 0.08, 300, 3000, 0.06 * am, pn + 0.1 * rnd(), 40)
    tink(a + 0.3, 900, 0.03 * am, pn, 18)
add(hp(noise(), 3000) * 0.02 * win(0.8, 5.6, .6, .6))
# 5.4-10.3: frozen men - near silence, distant thuds, held breath, a heartbeat
for tb in np.arange(6.0, 10.2, 1.05): thump(tb, 55, 0.16, 0.35); thump(tb + 0.27, 50, 0.10, 0.3)
for a in (6.2, 7.5, 8.9): thump(a, 48, 0.22, 0.7, 0.3); burst(a, 0.4, 150, 900, 0.06, 0.3, 6)
add(hp(noise(), 3500) * 0.03 * win(5.6, 10.3, .4, .4))
# 10.3-13.95: the rock cracks, breaks through, the drill grinds in
creak(10.4, 1.4, 160, 110, 0.10, 0.0); creak(11.4, 1.2, 130, 90, 0.10, 0.1)
for tk in np.arange(10.5, 12.0, 0.23): burst(tk, 0.12, 400, 3000, 0.07, rnd() * 1.2, 24)
am_buzz(11.0, 14.0, 60, 500, 13, 0.6, 0.0, ramp=True)
thump(12.05, 42, 0.5, 1.2); burst(12.05, 0.8, 150, 5000, 0.28, 0.0, 6)
for tk in np.arange(12.2, 13.6, 0.09): burst(tk + 0.05 * rnd(), 0.09, 600, 5500, 0.08, rnd() * 1.4, 30)
tink(12.5, 700, 0.07, 0.0, 14); tink(13.1, 900, 0.06, 0.1, 14)
add(hp(noise(), 3000) * 0.05 * win(11.2, 14.5, .4, .6))
# 13.95-23.7: the scream - shouting crowd, running feet, knocking and hitting
add(bp(noise(), 300, 2200) * 0.20 * win(13.9, 23.6, .3, 1.0) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.9 * t) * np.sin(2 * math.pi * 0.37 * t)), 0.0)
for k_ in range(40):
    tv = 14.0 + 9.4 * rs.random(); burst(tv, 0.35 + 0.3 * rs.random(), 350, 2000, 0.07 + 0.05 * rs.random(), rnd() * 1.8, 5)
for tk in np.arange(14.0, 16.4, 0.14): burst(tk, 0.1, 300, 2600, 0.07, rnd() * 1.6, 24)
for tk in np.arange(16.7, 22.0, 0.16):
    thump(tk + 0.04 * rnd(), 75, 0.10, 0.2, rnd() * 1.6); burst(tk, 0.1, 400, 2500, 0.08, rnd() * 1.6, 28)
for tk in np.arange(17.0, 22.0, 0.55): tink(tk + 0.1 * rnd(), 520 + 120 * rnd(), 0.09, rnd() * 0.6, 8)
for tk in np.arange(21.8, 23.6, 0.11): burst(tk, 0.08, 1200, 5000, 0.06, rnd() * 1.6, 30)   # applause-like
# 23.7-26: writing (pen on paper)
for tk in np.arange(23.9, 25.9, 0.12): burst(tk, 0.1, 3000, 9000, 0.05, 0.0, 30)
# 26-29: string rustle, the bit hoisted away: winch hum, chain, creak
burst(26.9, 0.5, 500, 3500, 0.06, 0.0, 6)
add(lp(noise(), 400) * 0.12 * win(27.6, 29.2, .5, .5) * (0.5 + 0.5 * np.sign(np.sin(2 * math.pi * 9 * t))), 0.0)
creak(27.7, 1.4, 200, 320, 0.08, 0.0)
# 29-32.5: surface - winch, chain clatter, crowd rising, gasps
add(bp(noise(), 80, 400) * 0.16 * win(28.9, 31.0, .4, .8) * (0.5 + 0.5 * np.sign(np.sin(2 * math.pi * 7 * t))), 0.2)
for tk in np.arange(29.2, 30.7, 0.13): tink(tk, 1200 + 400 * rnd(), 0.04, 0.2 + 0.2 * rnd(), 24)
add(bp(noise(), 250, 1500) * 0.07 * win(29.9, 32.6, .6, .5))
for tg in (30.8, 31.1, 31.5): burst(tg, 0.3, 500, 2500, 0.07, rnd() * 1.4, 7)
# 32.5-39.8: the paper - rustle, quiet wind, a held breath
burst(32.6, 0.9, 1200, 7000, 0.06, 0.0, 4); burst(33.6, 0.5, 1200, 7000, 0.04, 0.0, 6)
add(lp(noise(), 300) * 0.07 * win(32.6, 39.9, .8, .8) * (0.5 + 0.5 * np.sin(2 * math.pi * 0.2 * t)))
for tc in (36.9, 39.4): burst(tc, 0.3, 1500, 8000, 0.04, 0.0, 10)
# 39.8-45.6: chalk marks (17), then the warm swell
for i in range(17): burst(40.0 + 0.11 * i, 0.12, 2500, 8000, 0.07, rnd() * 0.5, 28)
add(hp(noise(), 1500) * 0.04 * win(44.6, 45.7, .5, .3)); add(lp(noise(), 200) * 0.14 * win(44.4, 45.7, .6, .3))
# 45.6-53.45: news - gasp, sobbing, cheers, claps; then the air goes still
burst(45.8, 0.4, 500, 2500, 0.10, 0.0, 6)
for k_ in range(14): burst(47.0 + 2.0 * rs.random(), 0.6, 450, 1600, 0.07, rnd() * 1.6, 4)
add(bp(noise(), 300, 1500) * 0.07 * win(46.8, 49.4, .5, .5) * (0.6 + 0.4 * np.sin(2 * math.pi * 1.4 * t)))
add(bp(noise(), 400, 3200) * 0.24 * win(49.3, 51.0, .2, 0.9) * (0.7 + 0.3 * np.sin(2 * math.pi * 3.1 * t)), 0.0)
for tk in np.arange(49.5, 51.0, 0.06): burst(tk, 0.05, 1000, 6000, 0.07, rnd() * 1.8, 40)
for k_ in range(12): burst(49.4 + 1.4 * rs.random(), 0.4, 500, 2400, 0.10, rnd() * 1.8, 5)
add(lp(noise(), 600) * 0.10 * win(50.8, 53.5, .8, .6) * (0.5 + 0.5 * np.sin(2 * math.pi * 0.25 * t)), 0.0)
# 53.45-57.9: down the pipe - deep rumble, creaks, heartbeat
add(lp(noise(), 90) * 0.22 * win(53.4, 58.0, .8, .6)); creak(54.0, 2.4, 70, 55, 0.08, 0.0)
for tb in np.arange(54.2, 57.9, 1.0): thump(tb, 52, 0.18, 0.35); thump(tb + 0.27, 48, 0.1, 0.3)
tink(56.4, 1300, 0.03, 0.2, 30)
# 57.9-61.9: the chamber - low wind, drips, trickling dust from the new hole, a last low thump
for tk in (58.5, 59.6, 60.8): tink(tk, 1500, 0.035, 0.4, 30)
add(hp(noise(), 3500) * 0.03 * win(57.9, D, .6, .8)); add(lp(noise(), 220) * 0.08 * win(58.0, D, .8, .8))
thump(60.0, 45, 0.2, 0.9)
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.D5 - 0.7, HS.D5 - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_part5.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
