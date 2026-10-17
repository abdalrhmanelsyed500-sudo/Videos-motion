import sys, numpy as np
from PIL import Image
import anims as A, frames as F
name = sys.argv[1]; dirs = sys.argv[2].split(',') if len(sys.argv) > 2 else ['down']; step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
rows = []
for d in dirs:
    y = A.DIRS[d]; ps = A.ANIMS[name][0](y); rows.append(np.concatenate([F.render_frame(p, y, cx=A.cx_for(name, y)) for p in ps[::step]], 1))
W = max(r.shape[1] for r in rows); rows = [np.pad(r, ((0, 0), (0, W - r.shape[1]), (0, 0))) for r in rows]
im = np.concatenate(rows, 0); k = 4
big = Image.fromarray(im, 'RGBA').resize((im.shape[1] * k, im.shape[0] * k), Image.NEAREST); bg = Image.new('RGBA', big.size, (92, 108, 80, 255)); bg.alpha_composite(big)
bg.convert('RGB').save(sys.argv[4] if len(sys.argv) > 4 else '/tmp/prev.png'); print(big.size)
