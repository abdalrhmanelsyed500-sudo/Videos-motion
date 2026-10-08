"""Part 4 renderer.  python render4.py --preview 1,5,20 | --out part4.mp4 --procs 2"""
import sys, os, math, argparse, subprocess, numpy as np, cv2
from multiprocessing import Pool
from PIL import Image, ImageDraw
from engine import *
import scenes_e
from scenes_e import ScenesE, P
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
LEAD = 1.2; DUR = 117.2
S = ScenesE()
TL = [(0.0, 'e1'), (8.0, 'e2'), (13.4, 'e3'), (16.4, 'e4'), (20.6, 'e5'), (23.8, 'e6'), (26.0, 'e7'), (30.0, 'e8'), (37.4, 'e9'),
      (42.2, 'e10'), (47.4, 'e11'), (52.4, 'e12'), (57.4, 'e13'), (62.6, 'e14'), (72.4, 'e15'), (78.2, 'e16'), (83.2, 'e17'),
      (88.0, 'e18'), (96.4, 'e19'), (99.0, 'e20'), (103.9, 'e21'), (108.4, 'e22'), (111.4, 'e23')]
CUT = {'e22'}   # hard cut (after the puncture flash)
DIS = 0.45
SUBS = [("Imagine this.", .22, .88), ("It's day three.", 1.5, 2.28), ("Your stomach hurts.", 3.04, 3.96), ("The air smells like sweat and dust.", 4.48, 6.56),
 ("You hear drilling above you, rescue teams trying to reach you,", 7.38, 10.22), ("but the sound fades.", 10.64, 11.66), ("The drill misses.", 12.36, 13.22), ("Then misses again.", 13.92, 14.6),
 ("On the surface, families were camping outside the mine, holding vigils.", 15.46, 18.78),
 ("Rescuers drilled holes into the mountain, searching blindly, because the maps of the mine were outdated.", 19.32, 24.32),
 ("Inside, the men did something remarkable.", 25.04, 27.34), ("They organized.", 27.98, 28.82),
 ("Urzúa mapped the tunnels and kept the men on a schedule, creating a rhythm:", 29.38, 33.18), ("day and night, even though there was no sun.", 33.78, 35.76),
 ("He used a truck's headlights to simulate daylight, and turned them off to create night.", 36.42, 40.72),
 ("They divided the refuge.", 41.66, 42.78), ("Some areas for sleeping, some for waiting.", 43.16, 45.4),
 ("Some men were given jobs:", 45.94, 47.16), ("tracking the food, rationing the water, tending to the sick.", 47.52, 50.6),
 ("One man, Yonni Barrios,", 51.38, 52.98), ("had medical training and became the group's informal doctor.", 53.28, 55.82),
 ("Another, Víctor Segovia,", 56.5, 58.04), ("kept a written record of everything, tracking each day.", 58.44, 60.98),
 ("And Mario Sepúlveda?", 61.8, 62.72), ("He became the morale.", 63.5, 64.38), ("When the despair crept in, he'd crack jokes, stir the group,", 65.08, 68.16),
 ("remind them they were still men with futures.", 68.52, 70.56),
 ("But it wasn't all unity.", 71.44, 72.66), ("Later accounts said there were arguments. Fights.", 73.42, 75.76), ("Moments when the pressure nearly broke them.", 76.3, 77.92),
 ("One man later admitted he'd thought about whether he could go on.", 78.74, 81.34),
 ("And then there was the hunger.", 82.18, 83.22), ("Real hunger.", 84.04, 84.68), ("The kind that changes you.", 85.24, 86.04),
 ("Each man had to look at the others and trust that nobody would take more than their share.", 86.82, 90.46),
 ("In a place where cheating the system meant someone else might die,", 91.24, 93.78), ("that trust was everything.", 94.44, 95.3), ("Seventeen days.", 96.14, 96.94),
 ("On day seventeen, they heard something different.", 97.66, 99.64), ("A drill, closer than ever.", 100.38, 102.06),
 ("The sound grew louder, then the bit punctured through the rock into their chamber.", 102.78, 106.7),
 ("They rushed to it.", 107.6, 108.18), ("Banged on it.", 108.5, 108.94), ("Shouted.", 109.16, 109.6), ("And then, taped to the drill bit, they sent up a note.", 110.38, 113.46)]
SUBF = None


def sub_layer(i, t):
    global SUBF
    txtf, a0, a1 = SUBS[i]
    s0 = a0 + LEAD; dur = max(0.35, (a1 - a0) * 0.8); n = int(len(txtf) * clamp((t - s0 + 0.04) / dur))
    if n <= 0: return None
    f = font(46)
    words = txtf.split(' '); lines = ['']
    for w in words:
        if f.getlength((lines[-1] + ' ' + w).strip()) > 1080 and lines[-1]: lines.append(w)
        else: lines[-1] = (lines[-1] + ' ' + w).strip()
    if len(lines) > 2:   # balance
        lines = [' '.join(words[:len(words) // 2]), ' '.join(words[len(words) // 2:])]
    im = Image.new("L", (W, 135), 0); d = ImageDraw.Draw(im); used = 0
    for k, ln in enumerate(lines):
        part = ln[:max(0, n - used)]; used += len(ln) + 1
        x = (W - f.getlength(ln)) / 2
        if part: d.text((x, 12 + k * 56), part, font=f, fill=255, stroke_width=4, stroke_fill=128)
    return np.asarray(im, np.float32) / 255


def draw_sub(cv, T):
    idx = None
    for i, (tx, a0, a1) in enumerate(SUBS):
        nxt = SUBS[i + 1][1] + LEAD - 0.03 if i + 1 < len(SUBS) else 1e9
        if a0 + LEAD - 0.05 <= T <= min(a1 + LEAD + 0.35, nxt): idx = i
    if idx is None: return
    m = sub_layer(idx, T)
    if m is None: return
    y0 = H - 135; roi = cv[y0:y0 + 135]
    dk = np.clip(m * 2, 0, 1)[..., None] * 0.85; gd = np.clip((m - 0.5) * 2, 0, 1)[..., None]
    roi *= (1 - dk); gold = np.array((75, 170, 232), np.float32); roi += (gold - roi) * gd


def frame_at(T):
    cur = max(i for i, (s, _) in enumerate(TL) if s <= T)
    def sc(i, TT):
        s, n = TL[i]; return getattr(S, n)(max(0.0, TT - s), np.zeros((H, W, 3), np.float32))
    cv = sc(cur, T)
    if cur + 1 < len(TL) and TL[cur + 1][1] not in CUT and T > TL[cur + 1][0] - DIS / 2:
        k = sstep((T - (TL[cur + 1][0] - DIS / 2)) / DIS); nxt = sc(cur + 1, T)
        cv = cv * (1 - k) + nxt * k
    elif cur > 0 and TL[cur][1] not in CUT and T < TL[cur][0] + DIS / 2:
        pass
    tone(cv, 1.07, 0, (0.98, 1.0, 1.03), 0.95)
    vignette(cv, 0.28, 2.2)
    grain(cv, T, 4.5)
    draw_sub(cv, T)
    fade = sstep(seg(T, 0, 0.7)) * (1 - sstep(seg(T, DUR - 2.0, DUR - 0.4)))
    cv *= fade
    return np.clip(cv, 0, 255).astype(np.uint8)


def render_chunk(args):
    a, b, path = args
    p = subprocess.Popen([FF, '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-maxrate', '5M', '-bufsize', '10M', '-pix_fmt', 'yuv420p', '-g', '60', path], stdin=subprocess.PIPE)
    for f in range(a, b):
        p.stdin.write(frame_at(f / FPS).tobytes())
    p.stdin.close(); p.wait(); return path


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--preview'); ap.add_argument('--out'); ap.add_argument('--procs', type=int, default=2); ap.add_argument('--audio')
    a = ap.parse_args()
    if a.preview:
        ts = [float(x) for x in a.preview.split(',')]
        for T in ts:
            cv2.imwrite(f'build/pv_{T:06.2f}.jpg', frame_at(T), [cv2.IMWRITE_JPEG_QUALITY, 88])
        sys.exit()
    N = int(DUR * FPS); k = a.procs; ch = []
    per = math.ceil(N / (k * 3)); i = 0
    while i < N: ch.append((i, min(N, i + per), f'build/chunk_{len(ch):02d}.mp4')); i += per
    with Pool(k) as pool:
        for r in pool.imap(render_chunk, ch): print('done', r, flush=True)
    with open('build/list.txt', 'w') as f:
        for _, _, p in ch: f.write(f"file '{os.path.abspath(p)}'\n")
    cmd = [FF, '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', 'build/list.txt']
    if a.audio: cmd += ['-i', a.audio, '-c:a', 'aac', '-b:a', '160k', '-shortest']
    cmd += ['-c:v', 'copy', '-movflags', '+faststart', a.out]
    subprocess.run(cmd, check=True); print('OK', a.out)
