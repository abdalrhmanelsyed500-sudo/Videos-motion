"""Frame renderer for the demo episode.  usage: python -m rigkit.render video OUT.mp4 [start end] | sheet OUT.jpg t1 t2 ..."""
import sys, os, subprocess, time
import numpy as np, cv2
from . import episode as E, face as F, bg
from .rig import Rig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = os.environ.get('FFMPEG', '/home/user/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2')

def draw_shadow(canvas, x, w, alpha, cam):
    sx = cam[1] + x * cam[0]; sy = cam[2]
    if not np.isfinite(sx) or sx < -400 or sx > canvas.shape[1] + 400: return
    m = np.zeros(canvas.shape[:2], np.float32)
    cv2.ellipse(m, (int(sx), int(sy + 4)), (int(w * cam[0]), int(13 * cam[0])), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 6) * alpha * 0.34
    canvas *= (1 - m[..., None] * np.array([1.0, 0.8, 0.9], np.float32)[None, None])

def make_episode():
    rig_root = os.path.join(ROOT, 'out', 'rigs')
    return E.Episode(rig_root, os.path.join(ROOT, 'audio'))

def frame(ep, park, i):
    cam_x = ep.cam[i]; t = i / E.FPS
    cv = park.back(cam_x, t); cam = (E.S, E.W / 2 - cam_x * E.S, E.GY)
    acts = [(ep.z, ep.z.states[i]), (ep.l, ep.l.states[i])]
    acts.sort(key=lambda a: a[1]['x'])
    for A, st in acts:
        draw_shadow(cv, st['x'], 78 if st['view'] == 'side' else 92, st['shadow'], cam)
    for A, st in acts:
        rig = A.rigs[st['view']]
        dyn = F.face_dyn(st['face'], A.spec, st['view'])
        rig.draw(cv, st['pose'], cam, swap=st['swap'], dyn=dyn, root=st['root'], zov=st['zov'])
    park.front(cv, cam_x)
    return cv

def main():
    mode = sys.argv[1]; ep = make_episode(); park = bg.Park()
    if mode == 'sheet':
        out = sys.argv[2]; ts = [float(x) for x in sys.argv[3:]]; tiles = []
        for t in ts:
            i = min(int(round(t * E.FPS)), ep.n - 1); tiles.append(cv2.resize((frame(ep, park, i) * 255).astype(np.uint8), (960, 540), interpolation=cv2.INTER_AREA))
        rows = [np.hstack(tiles[k:k + 2] + ([np.zeros_like(tiles[0])] if len(tiles[k:k + 2]) < 2 else [])) for k in range(0, len(tiles), 2)]
        cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 90]); return
    out = sys.argv[2]; a = int(sys.argv[3]) if len(sys.argv) > 3 else 0; b = int(sys.argv[4]) if len(sys.argv) > 4 else ep.n
    p = subprocess.Popen([FFMPEG, '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{E.W}x{E.H}', '-r', str(E.FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    t0 = time.time()
    for i in range(a, b):
        fr = (np.clip(frame(ep, park, i), 0, 1) * 255 + .5).astype(np.uint8)
        p.stdin.write(fr.tobytes())
        if i % 30 == 0: print(f'frame {i}/{b} {time.time() - t0:.0f}s', flush=True)
    p.stdin.close(); p.wait(); print('done', b - a, 'frames')

if __name__ == '__main__': main()
