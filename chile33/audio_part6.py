"""Part 6 mix (NO MUSIC, SFX only - user request): Arabic voice (part6.wav) + procedural ambience/SFX synced to part6_scenes timeline. Output build/mix_part3.wav (stereo 44.1k)."""
import numpy as np, math, wave
from scipy import signal
import part6_scenes as HS
SR = 44100; N = int(HS.D6 * SR); t = np.arange(N) / SR
rg = np.random.default_rng(7)

def rd(path):
    w = wave.open(path); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return x
voice = rd('audio/part6.wav'); v = np.zeros(N, np.float32); v[:min(N, len(voice))] = voice[:N]
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
D = HS.D6
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
# 0-1.9 surface: distant engines, wind
add(bp(noise(), 120, 900) * 0.10 * win(0, 2.5, .3, .6)); add(hp(noise(), 2500) * 0.03 * win(0, 2.5, .3, .6))
# 1.9-5: capsule slides down the pipe: metallic scrape, ticks
add(bp(noise(), 600, 3500) * 0.07 * win(1.9, 5.0, .2, .3) * (0.6 + 0.4 * np.sin(2 * math.pi * 7 * t)), 0.0)
for tk in np.arange(2.0, 4.9, 0.31): tink(tk, 1800 + 500 * rnd(), 0.025, rnd() * 0.5, 40)
add(lp(noise(), 120) * 0.10 * win(1.9, 5.2, .4, .4))
# 5-9.9: capsule arrives, items drop, hands catch: clanks, rustle, thumps
creak(4.8, 0.7, 240, 180, 0.06, 0.0); thump(5.4, 90, 0.18, 0.4); burst(5.4, 0.3, 500, 4000, 0.10, 0.0, 14)
for ti, pn in ((5.5, -0.5), (6.15, 0.5), (6.75, -0.2), (7.45, 0.4), (7.9, -0.5), (8.35, 0.2), (8.75, 0.6)):
    burst(ti, 0.25, 300, 3500, 0.10, pn, 14); thump(ti + 0.1, 100, 0.07, 0.25, pn); tink(ti + 0.05, 1100 + 300 * rnd(), 0.04, pn, 24)
for tk in (5.7, 6.3, 7.0): burst(tk, 0.5, 2000, 8000, 0.03, 0.0, 6)
add(bp(noise(), 250, 1800) * 0.06 * win(5.6, 9.9, .6, .5) * (0.6 + 0.4 * np.sin(2 * math.pi * 1.1 * t)))
add(lp(noise(), 110) * 0.12 * win(5.0, 10.0, .5, .5))
# 9.9-13.1 lifeline: soft pulses travelling down, a low heartbeat
for tb in np.arange(10.0, 13.0, 0.62): thump(tb, 62, 0.14, 0.35); burst(tb, 0.35, 500, 1600, 0.025, 0.0, 9)
add(lp(noise(), 100) * 0.16 * win(9.9, 13.2, .5, .4))
# 13.1-21.06: the world sees them: a digital blip, camera hum, static
burst(13.15, 0.12, 1500, 9000, 0.12, 0.0, 30); thump(13.15, 70, 0.14, 0.5)
add(bp(noise(), 3000, 9000) * 0.035 * win(13.2, 21.0, .2, .6) * (0.5 + 0.5 * np.sign(np.sin(2 * math.pi * 3.5 * t))))
add(bp(noise(), 90, 140) * 0.10 * win(13.2, 21.0, .2, .6))
for tk in (16.05, 17.5, 18.7, 19.8): burst(tk, 0.1, 2000, 9000, 0.10, 0.0, 32)
for tc in (20.0, 20.25, 20.5, 20.8): burst(tc, 0.25, 500, 2500, 0.07, rnd() * 1.6, 8)
# 21.06-23.65: surface teams: voices, steps, equipment
add(bp(noise(), 250, 1500) * 0.05 * win(21.0, 23.7, .4, .4))
for tk in np.arange(21.2, 23.2, 0.30): burst(tk, 0.1, 150, 900, 0.06, rnd() * 1.4, 22)
for tk in (22.0, 22.7, 23.2): tink(tk, 700 + 200 * rnd(), 0.04, rnd(), 18)
# 23.65-27.7 NASA: airy quiet, soft radio pings and static (no tones sustained)
add(hp(noise(), 4000) * 0.03 * win(23.6, 27.8, .6, .6)); add(lp(noise(), 200) * 0.08 * win(23.6, 27.8, .6, .6))
for tk in (24.1, 24.8, 25.5, 26.2, 26.9): burst(tk, 0.15, 1800, 5000, 0.07, 0.4 * rnd(), 18); tink(tk, 2200, 0.025, 0.2, 40)
# 27.7-31.6 the mind: heavy hush, slow heartbeat, a breath
add(lp(noise(), 120) * 0.16 * win(27.6, 31.7, .6, .6))
for tb in np.arange(28.0, 31.6, 0.95): thump(tb, 52, 0.20, 0.4); thump(tb + 0.24, 48, 0.12, 0.3)
burst(29.0, 0.7, 400, 1800, 0.05, 0.0, 4)
# 31.6-38.9 sleep/wake/dark thoughts: breathing, shifting, drips, distant rumble
for tk in (32.3, 33.2, 34.4): burst(tk, 0.6, 300, 1500, 0.04, rnd() * 1.2, 5)
for tk in np.arange(31.8, 34.0, 0.9): burst(tk, 0.4, 1500, 6000, 0.04, rnd() * 1.4, 7)
for tk in (32.0, 33.5, 35.2, 36.4, 37.9): drip(tk)
burst(35.1, 0.6, 600, 3000, 0.07, 0.0, 6)
add(lp(noise(), 90) * 0.18 * win(35.9, 38.9, .6, .5) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.4 * t)))
for tb in np.arange(36.0, 38.8, 0.7): thump(tb, 50, 0.16, 0.35)
# 38.9-42.2 the mountain above: deep rumble, rock creaks, falling dust
add(lp(noise(), 70) * 0.30 * win(38.8, 42.3, .5, .4)); creak(39.5, 2.0, 70, 50, 0.10, 0.0); creak(41.0, 1.2, 90, 60, 0.07, 0.3)
for tk in np.arange(39.6, 42.0, 0.25): burst(tk, 0.15, 1500, 6000, 0.04, rnd() * 1.6, 20)
# 42.2-46.4 routine: jumping thumps, murmur, domino clicks, pen, phone
for tk in np.arange(42.25, 43.2, 0.43): thump(tk, 80, 0.14, 0.2, rnd()); burst(tk, 0.08, 200, 1200, 0.05, rnd(), 30)
add(bp(noise(), 250, 1300) * 0.05 * win(43.2, 44.1, .2, .2) * (0.5 + 0.5 * np.sin(2 * math.pi * 0.8 * t)))
for tk in np.arange(44.12, 44.75, 0.1): tink(tk, 2600 + 600 * rnd(), 0.05, rnd() * 0.8, 70)
for tk in np.arange(44.85, 45.55, 0.1): burst(tk, 0.1, 3000, 9000, 0.05, 0.0, 30)
add(bp(noise(), 300, 1800) * 0.06 * win(45.6, 46.4, .15, .15) * (0.5 + 0.5 * np.sin(2 * math.pi * 3.0 * t)))
# 46.4-51.5 pretending normal: low chatter, steps, then it fades into hush
add(bp(noise(), 250, 1600) * 0.10 * win(46.4, 51.5, .4, 1.4) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.9 * t) * np.sin(2 * math.pi * 0.31 * t)))
for tk in np.arange(46.6, 49.5, 0.35): burst(tk, 0.1, 150, 900, 0.04, rnd() * 1.5, 22)
for k_ in range(10): burst(46.8 + 2.4 * rs.random(), 0.4, 400, 1800, 0.05, rnd() * 1.6, 6)
add(lp(noise(), 110) * 0.14 * win(49.3, 51.6, .8, .5))
# 51.5-55.2 plan: pencil on paper, three marker strokes
for tk in np.arange(51.7, 53.6, 0.11): burst(tk, 0.1, 3000, 9000, 0.05, 0.0, 30)
for tk in (53.9, 54.4, 54.9): burst(tk, 0.4, 2500, 8000, 0.08, 0.0, 9); thump(tk, 80, 0.10, 0.25)
add(lp(noise(), 150) * 0.10 * win(51.5, 55.3, .5, .4))
# 55.2-57.6 giant drilling machines: engines, grinding, big rumble
add(lp(noise(), 160) * 0.30 * win(55.1, 57.7, .3, .5) * (0.7 + 0.3 * np.sign(np.sin(2 * math.pi * 5 * t))))
am_buzz(55.3, 57.6, 60, 500, 12, 0.55, 0.0, ramp=True); thump(55.4, 40, 0.4, 1.2); thump(56.4, 38, 0.35, 1.2)
add(bp(noise(), 800, 5000) * 0.05 * win(55.5, 57.6, .3, .4) * (0.5 + 0.5 * np.sign(np.sin(2 * math.pi * 17 * t))))
# 57.6-59 waiting crowd: murmur, wind, a few chimes of candles
add(bp(noise(), 200, 1200) * 0.08 * win(57.5, 59.1, .3, .4)); add(lp(noise(), 300) * 0.07 * win(57.5, 59.2, .3, .4))
# 59-60.2 time: fast ticking
for tk in np.arange(59.0, 60.2, 0.08): tink(tk, 3200, 0.04, 0.2, 90)
# 60.2-end: tally scratches, cracks, falling stones, rumble that grows
for i in range(8): burst(60.25 + 0.08 * i * 1.0, 0.1, 2500, 8000, 0.07, rnd() * 0.5, 28)
add(lp(noise(), 90) * (0.14 + 0.30 * sm(60.5, D, t)) * win(60.1, D, .3, .3))
for tk in np.arange(60.8, 62.2, 0.12): burst(tk, 0.14, 300, 3000, 0.06 + 0.04 * (tk - 60.8), rnd() * 1.4, 18)
creak(60.9, 1.3, 80, 55, 0.12, 0.0); thump(61.5, 40, 0.30, 1.0)
# ---- duck ambience under the voice, then mix
amb_L, amb_R = L * (1 - 0.30 * env), R * (1 - 0.30 * env)
oL = amb_L + v; oR = amb_R + v
fade = sm(0, 0.35, t) * (1 - sm(HS.D6 - 0.7, HS.D6 - 0.05, t))
out = np.tanh(np.stack([oL, oR], 1) * fade[:, None] * 1.0) * 0.95
pk = np.abs(out).max(); print('peak', pk)
pcm = (out * 32767).astype(np.int16)
w = wave.open('build/mix_part6.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok', N / SR)
