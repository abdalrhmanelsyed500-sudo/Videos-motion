import sys, os, math, numpy as np, cv2, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sufan_rig_side as S, sufan_walk as W
from rigkit.rig import Rig
from rigkit.face import VISEMES
rig = Rig(S.build()); w = W.make(rig, +1, 0.0, 250.0, 0.5, 7.5)
FF = '/home/user/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
out = sys.argv[1]; Wd, Hd = 960, 540; sc = 0.68; gy = 480
p = subprocess.Popen([FF, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{Wd}x{Hd}', '-r', '30', '-i', '-', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
nf = int((w.t_end + 0.6) * 30)
for i in range(nf):
    t = i / 30; rx, pose = w.state(t)
    cv = np.ones((Hd, Wd, 3), np.float32) * np.array([0.93, 0.97, 0.99], np.float32)
    cv[gy:] = np.array([0.74, 0.84, 0.70], np.float32)
    camx = Wd / 2 - rx * sc
    for k in range(-5, 12):  # ground ticks every 40 units (world fixed) -> planted feet must stay on them
        x = int(camx + k * 40 * sc * 1.0 * 1 + 0); x = int(camx + (k * 40) * sc)
    for gx in range(int(-80), int(400), 40):
        x = int(camx + gx * sc); cv2.line(cv, (x, gy), (x, gy + 40), (0.5, 0.65, 0.5), 2)
    face = {'mouth': VISEMES['smile']}
    ph = int(t * 30)
    if ph % 100 in (0, 3): face.update(blinkR=1.0 if ph % 100 == 0 else 0.5)
    rig.draw(cv, pose, cam=(sc, camx, gy), dyn=S.face_dyn(face), root={'x': rx})
    p.stdin.write((np.clip(cv, 0, 1) * 255).astype(np.uint8).tobytes())
p.stdin.close(); p.wait(); print('frames', nf)
