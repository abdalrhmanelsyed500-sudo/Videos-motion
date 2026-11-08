#!/usr/bin/env python3
"""qc.py — quality control for the final MP4:
   - ffmpeg container/stream checks
   - per-frame luminance/detail stats at sampled timestamps (no black frames)
   - frame-to-frame diff analysis (frozen frames / jump cuts)
   - audio RMS window check
   - Arabic text presence check on key frames (ink coverage in title/label regions)
Writes QC_REPORT.md"""
import subprocess, os, sys, re
import numpy as np
import scipy.io.wavfile as wav

FFMPEG = '/home/user/.venv-wh20s/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v9.0.2'

mp4 = sys.argv[1] if len(sys.argv) > 1 else '/home/user/Videos-motion/WHITE_HOUSE_20S_CINEMATIC_MOTION_TEST/01_FINAL_VIDEO/white_house_20s_final.mp4'
root = '/home/user/Videos-motion/WHITE_HOUSE_20S_CINEMATIC_MOTION_TEST'
qc_dir = os.path.join(root, '05_PREVIEWS_AND_QC')
os.makedirs(qc_dir, exist_ok=True)

def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout + r.stderr

def read_frame(mp4, ts):
    r = subprocess.run([FFMPEG, '-v', 'error', '-ss', str(ts), '-i', mp4,
                        '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                       capture_output=True)
    buf = r.stdout
    n = len(buf) // 3
    return np.frombuffer(buf[:n * 3], dtype=np.uint8).reshape(1080, 1920, 3).astype(np.float32)

report = []
def log(s=''):
    print(s)
    report.append(s)

# ---- 1. container probe ----
info = sh([FFMPEG, '-i', mp4])
def grab(pat):
    m = re.search(pat, info)
    return m.group(1) if m else '?'
dm = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', info)
dur = int(dm.group(1)) * 3600 + int(dm.group(2)) * 60 + float(dm.group(3))
vres = grab(r'(\d{3,4}x\d{3,4})')
vr = grab(r'(\d+(?:\.\d+)?) fps')
vcodec = grab(r'Video: (\w+)')
acodec = grab(r'Audio: (\w+)')
asr = grab(r'Audio: \w+.*?(\d+) Hz')

log('=== CONTAINER ===')
log(f"duration: {dur:.3f}s (target 20.0)  {'PASS' if abs(dur-20) < 0.15 else 'FAIL'}")
log(f"video: {vres} {vr}fps {vcodec}  {'PASS' if vres.startswith('1920x1080') and abs(float(vr)-30) < 0.5 else 'FAIL'}")
log(f"audio: {acodec} {asr}Hz stereo")

# ---- 2. sampled frame stats ----
log('\n=== FRAME STATS (sampled) ===')
sample_ts = [0.5, 2.0, 3.6, 5.0, 5.9, 6.8, 8.3, 9.5, 10.8, 11.7, 12.6, 13.5, 14.35, 15.2, 16.0, 17.4, 18.5, 19.5]
for ts in sample_ts:
    im = read_frame(mp4, ts)
    lum = 0.299 * im[:, :, 0] + 0.587 * im[:, :, 1] + 0.114 * im[:, :, 2]
    mean = lum.mean(); std = lum.std()
    dark_pct = (lum < 12).mean() * 100
    ok = 'PASS' if (25 < mean < 225 and std > 18 and dark_pct < 5) else 'CHECK'
    log(f"t={ts:5.2f}s  mean={mean:6.1f}  std={std:5.1f}  black%={dark_pct:4.1f}  {ok}")

# ---- 3. frame diff analysis ----
log('\n=== MOTION CONTINUITY (frame diff) ===')
diffs = []
prev = None
for i in range(0, 600, 15):
    im = read_frame(mp4, i / 30)
    if prev is not None:
        diffs.append(np.abs(im - prev).mean())
    prev = im
log(f"mean|delta| over {len(diffs)} samples: min={min(diffs):.2f} max={max(diffs):.2f} mean={np.mean(diffs):.2f}")
log('(frozen frames would show ~0; abrupt cuts would spike)')

# ---- 4. audio windows ----
log('\n=== AUDIO ===')
mix_path = os.path.join(root, '02_EDITABLE_PROJECT/render/04_audio_out/mix.wav')
sr, audio = wav.read(mix_path)
if audio.ndim == 1:
    audio = np.stack([audio, audio], axis=1)
rms = [20 * np.log10(np.sqrt(np.mean(audio[int(i * 0.5 * sr):int((i + 1) * 0.5 * sr)] ** 2)) + 1e-9) for i in range(40)]
log('RMS dBFS/0.5s: ' + ' '.join(f'{v:.0f}' for v in rms))
peak = 20 * np.log10(np.max(np.abs(audio)) + 1e-9)
log(f'peak: {peak:.2f} dBTP  {"PASS" if peak <= -0.5 else "FAIL"}')

# ---- 5. Arabic text ink check ----
log('\n=== ARABIC TEXT PRESENCE ===')
for ts, region, name in [
    (1.6, (640, 140, 1320, 235), 'main title'),
    (19.7, (640, 140, 1320, 230), 'closing title'),
    (6.8, (30, 125, 270, 200), 'Oval Office label'),
    (9.9, (1380, 125, 1690, 200), 'Cabinet Room label'),
    (13.7, (1380, 115, 1690, 190), 'State Dining label'),
    (16.5, (40, 105, 310, 180), 'East Room label'),
]:
    im = read_frame(mp4, ts)
    x0, y0, x1, y1 = region
    lum = 0.299 * im[:, :, 0] + 0.587 * im[:, :, 1] + 0.114 * im[:, :, 2]
    ink = (lum[y0:y1, x0:x1] < 100).sum()
    log(f"t={ts}s {name}: ink px={ink}  {'PASS (text present)' if ink > 800 else 'CHECK'}")

with open(os.path.join(qc_dir, 'QC_REPORT.md'), 'w') as f:
    f.write('# QUALITY CONTROL REPORT\n\n' + '\n'.join(report) + '\n')
log('\nreport -> ' + os.path.join(qc_dir, 'QC_REPORT.md'))
