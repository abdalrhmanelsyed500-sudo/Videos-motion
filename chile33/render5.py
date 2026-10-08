"""Part 5 renderer: reuses render4's compositing, overrides timeline/subs.  python render5.py --preview 1,2 | --out x.mp4 --procs 2"""
import sys, argparse, math, os, subprocess
import render4 as R
from scenes_f import ScenesF
R.S = ScenesF(); R.LEAD = 1.2; R.DUR = 54.7
R.TL = [(0.0, 'f1'), (5.2, 'f2'), (8.9, 'f3'), (15.2, 'f4'), (18.7, 'f5'), (20.6, 'f6'), (25.0, 'f7'), (28.2, 'f8'), (34.4, 'f9'), (39.6, 'f10'), (48.8, 'f11'), (51.1, 'f12')]
R.SUBS = [("On the surface, the drill came back up.", .18, 2.02), ("The team pulled it out,", 2.64, 3.58), ("and there, tied to the bit, was a piece of paper.", 4.14, 7.10),
 ("Handwritten in red ink.", 7.96, 9.24), ("It said:", 10.04, 10.44), ('"Estamos bien en el refugio, los 33."', 10.98, 13.24),
 ("We are well in the refuge, the 33 of us.", 13.66, 17.06), ("Imagine reading those words.", 17.46, 18.44),
 ("After 17 days of silence, 17 days of the entire country holding its breath.", 19.4, 23.48), ("President Sebastián Piñera announced it to the world.", 23.92, 26.6),
 ("Families outside the mine erupted.", 27.64, 30.18), ("People cried, screamed, embraced.", 31.08, 32.62), ("But then reality set in.", 33.08, 35.2),
 ("The men were alive.", 36.06, 37.46), ("But they were trapped 2,300 feet below the surface.", 38.3, 43.18), ("And getting them out?", 43.86, 44.52),
 ("That was a different problem entirely.", 45.12, 46.8), ("Engineers estimated it could take months.", 47.66, 49.56), ("Possibly until Christmas.", 49.98, 51.22)]
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--preview'); ap.add_argument('--out'); ap.add_argument('--procs', type=int, default=2); ap.add_argument('--audio')
    a = ap.parse_args()
    if a.preview:
        import cv2
        for T in [float(x) for x in a.preview.split(',')]:
            cv2.imwrite(f'build/pv5_{T:06.2f}.jpg', R.frame_at(T), [cv2.IMWRITE_JPEG_QUALITY, 88])
        sys.exit()
    N = int(R.DUR * R.FPS); k = a.procs; ch = []; per = math.ceil(N / (k * 3)); i = 0
    while i < N: ch.append((i, min(N, i + per), f'build/c5_{len(ch):02d}.mp4')); i += per
    from multiprocessing import Pool
    with Pool(k) as pool:
        for r in pool.imap(R.render_chunk, ch): print('done', r, flush=True)
    with open('build/list5.txt', 'w') as f:
        for _, _, p in ch: f.write(f"file '{os.path.abspath(p)}'\n")
    subprocess.run([R.FF, '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', 'build/list5.txt', '-c', 'copy', a.out], check=True); print('OK', a.out)
