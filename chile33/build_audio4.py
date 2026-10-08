"""Part 4 mix: narration (delayed by LEAD) + dark drone + drill rumble + heartbeat + puncture + bangs."""
import wave, numpy as np
from scipy.signal import butter, lfilter
SR = 24000; LEAD = 1.2; DUR = 117.2
def load(p):
    w = wave.open(p); d = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; return d
v = load('audio/voice4.wav'); n = int(DUR * SR); out = np.zeros(n, np.float32)
v = v / (np.abs(v).max() + 1e-6) * 0.9
out[int(LEAD * SR):int(LEAD * SR) + len(v)] += v
t = np.arange(n) / SR; r = np.random.default_rng(1)
def lp(x, fc, o=2): b, a = butter(o, fc / (SR / 2)); return lfilter(b, a, x)
def env(a, b, fi=0.3, fo=0.3):
    e = np.clip((t - a) / max(fi, 1e-3), 0, 1) * np.clip((b - t) / max(fo, 1e-3), 0, 1); return e.astype(np.float32)
# drone
drone = (np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 82.4 * t + 1) + 0.3 * np.sin(2 * np.pi * 110.3 * t)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.08 * t))
drone *= 0.045 * np.clip(t / 3, 0, 1) * np.clip((DUR - t) / 3, 0, 1)
swell = env(94, 97.5, 3, 0.5) * 0.04 * np.sin(2 * np.pi * 73.4 * t)
out += drone + swell
rumble = lp(r.normal(0, 1, n).astype(np.float32), 140, 3)
def drill(a, b, g, ramp=False):
    e = env(a, b, 0.4, 0.8)
    if ramp: e = e * (0.3 + 0.7 * np.clip((t - a) / (b - a), 0, 1))
    chat = lp(r.normal(0, 1, n).astype(np.float32), 900, 2) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 19 * t)))
    return (rumble * 2.2 + chat * 0.5 + np.sin(2 * np.pi * 47 * t) * 0.4) * e * g
out += drill(8.6, 12.8, 0.07)
out += drill(99.2, 106.7, 0.09, True)
# heartbeat (e1, e16, e17)
def hb(a, b, per, g):
    tt = a
    while tt < b:
        for off, amp in ((0, 1.0), (0.22, 0.6)):
            i = int((tt + off) * SR); k = np.arange(int(0.18 * SR)) / SR
            s = np.sin(2 * np.pi * 52 * k) * np.exp(-k * 22) * amp * g
            out[i:i + len(s)] += s[:max(0, n - i)][:len(s)] if i + len(s) <= n else 0
        tt += per
hb(1.0, 8.0, 1.1, 0.35); hb(79.0, 83.0, 1.4, 0.35); hb(84.0, 88.0, 1.2, 0.3)
# puncture crash + bangs
def hit(a, g, f=90, dec=6, noise=0.5, ln=1.5):
    i = int(a * SR); k = np.arange(int(ln * SR)) / SR
    s = (np.sin(2 * np.pi * f * k) + noise * lp(r.normal(0, 1, len(k)).astype(np.float32), 3000, 2) * 2) * np.exp(-k * dec) * g
    out[i:i + len(s)] += s[:n - i]
hit(106.7, 0.55, 70, 3.5, 0.8, 2.5)
for tb in (109.7, 110.0, 110.3):   # metal bangs
    i = int(tb * SR); k = np.arange(int(0.8 * SR)) / SR
    s = sum(np.sin(2 * np.pi * f * k + ph) * a for f, a, ph in ((410, 1, 0), (673, .6, 1), (1130, .35, 2))) * np.exp(-k * 9) * 0.22
    out[i:i + len(s)] += s[:n - i]
# fades + limiter
out *= np.clip((DUR - t) / 1.5, 0, 1)
out = np.tanh(out * 1.1) * 0.95
out16 = (out * 32767).astype(np.int16)
w = wave.open('build/mix4.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out16.tobytes()); w.close(); print('mix ok', np.abs(out).max())
