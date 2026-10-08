"""Part 5 mix: narration + drone + pulling rumble + paper rustle + heartbeat + flashes + crowd swell + hush + Christmas chime."""
import wave, numpy as np
from scipy.signal import butter, lfilter
SR = 24000; LEAD = 1.2; DUR = 54.7
w = wave.open('audio/voice5.wav'); v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
v = v / (np.abs(v).max() + 1e-6) * 0.9
n = int(DUR * SR); out = np.zeros(n, np.float32); out[int(LEAD * SR):int(LEAD * SR) + len(v)] += v
t = np.arange(n) / SR; r = np.random.default_rng(5)
def lp(x, fc, o=2): b, a = butter(o, fc / (SR / 2)); return lfilter(b, a, x)
def bp(x, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)
def env(a, b, fi=0.3, fo=0.3): return (np.clip((t - a) / max(fi, 1e-3), 0, 1) * np.clip((b - t) / max(fo, 1e-3), 0, 1)).astype(np.float32)
noise = r.normal(0, 1, n).astype(np.float32)
# drone: warm hope, then cold after reality (34.4), back to low unresolved tone
f0 = np.where(t < 34.4, 65.4, 55.0)
ph = 2 * np.pi * np.cumsum(f0) / SR
drone = (np.sin(ph) + 0.5 * np.sin(1.5 * ph) + 0.25 * np.sin(2 * ph)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t))
out += drone * 0.04 * np.clip(t / 3, 0, 1) * np.clip((DUR - t) / 3, 0, 1)
out += lp(noise, 160, 3) * 2.0 * env(0.3, 5.4, 0.5, 1.0) * 0.06   # drill rig hauling
out += bp(noise, 2500, 6000) * env(9.0, 9.7, 0.05, 0.4) * 0.02 * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 14 * t)))  # paper rustle
def hb(a, b, per, g):
    tt = a
    while tt < b:
        for off, amp in ((0, 1.0), (0.22, 0.6)):
            i = int((tt + off) * SR); k = np.arange(int(0.18 * SR)) / SR; s = np.sin(2 * np.pi * 52 * k) * np.exp(-k * 22) * amp * g
            if i + len(s) < n: out[i:i + len(s)] += s
        tt += per
hb(15.2, 19.0, 1.1, 0.3); hb(35.0, 39.4, 1.3, 0.28)
for k in range(15, 52):   # 33 dots: soft ticks
    pass
for tb in np.linspace(15.6, 17.9, 33):
    i = int(tb * SR); kk = np.arange(int(0.12 * SR)) / SR; s = np.sin(2 * np.pi * 1320 * kk) * np.exp(-kk * 35) * 0.035
    if i + len(s) < n: out[i:i + len(s)] += s
# camera flashes (clicks) in the press scene
rr = np.random.default_rng(7)
for tb in np.sort(rr.uniform(25.2, 28.0, 14)):
    i = int(tb * SR); kk = np.arange(int(0.05 * SR)) / SR; s = rr.normal(0, 1, len(kk)).astype(np.float32) * np.exp(-kk * 120) * 0.05
    if i + len(s) < n: out[i:i + len(s)] += s
# crowd eruption swell
crowd = bp(noise, 300, 3200) * (0.6 + 0.4 * np.sin(2 * np.pi * 3.1 * t))
out += crowd * env(28.4, 34.8, 0.9, 1.6) * 0.10
for tb in (28.8, 29.3, 29.9):  # cheers punches
    out += bp(noise, 400, 2500) * np.exp(-np.clip(t - tb, 0, None) * 5) * (t >= tb) * 0.05
# the question: low tension swell at "getting them out?"
out += np.sin(2 * np.pi * 73.4 * t) * env(44.0, 50, 1.5, 1.5) * 0.025
# Christmas chime (gentle)
for tb, f in ((52.2, 784), (52.55, 988), (52.9, 1175), (53.3, 1568)):
    i = int(tb * SR); kk = np.arange(int(1.6 * SR)) / SR; s = (np.sin(2 * np.pi * f * kk) + 0.3 * np.sin(2 * np.pi * 2 * f * kk)) * np.exp(-kk * 3.2) * 0.03
    if i + len(s) < n: out[i:i + len(s)] += s
out *= np.clip((DUR - t) / 1.6, 0, 1)
out = np.tanh(out * 1.1) * 0.95
w = wave.open('build/mix5.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes()); w.close(); print('ok', np.abs(out).max())
