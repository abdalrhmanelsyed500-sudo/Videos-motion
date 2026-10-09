import sys, subprocess, numpy as np, cv2, math
from engine import *
import part6_scenes as HS
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe(); S = HS.Part6(); DUR = HS.D6
_canvas = [None]
def post(cv, T):
    if _canvas[0] is None:
        r = np.random.default_rng(2); n = r.normal(0, 1, (H // 3, W // 3)).astype(np.float32)
        n = cv2.GaussianBlur(cv2.resize(n, (W, H), interpolation=cv2.INTER_CUBIC), (0, 0), 1.2)
        yy, xx = np.mgrid[0:H, 0:W]; weave = 0.5 + 0.5 * np.sin(xx * 1.9) * np.sin(yy * 1.9)
        _canvas[0] = (1 + 0.035 * n + 0.012 * (weave - 0.5))[..., None].astype(np.float32)
    cv *= _canvas[0]; tone(cv, 1.06, 0, (0.98, 1.0, 1.03), 1.0); vignette(cv, 0.3, 2.2); grain(cv, T, 3.5)
    cv *= sstep(seg(T, 0, 0.6)) * (1 - sstep(seg(T, DUR - 1.0, DUR - 0.1)))
    return np.clip(cv, 0, 255).astype(np.uint8)
def fr(T): return post(S.frame(max(0.0, min(T, DUR)), np.zeros((H, W, 3), np.float32)), T)
if __name__ == '__main__':
    if sys.argv[1] == '--preview':
        for T in [float(x) for x in sys.argv[2].split(',')]: cv2.imwrite(f'build/p6_{T:06.2f}.jpg', fr(T), [cv2.IMWRITE_JPEG_QUALITY, 90])
    else:   # --range f0 f1 out.mp4
        f0, f1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen([FF, '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '22', '-maxrate', '5M', '-bufsize', '10M', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for f in range(f0, f1): p.stdin.write(fr(f / FPS).tobytes())
        p.stdin.close(); p.wait()
