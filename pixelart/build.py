"""Build RANGER sprite sheets, atlas JSON, GIF previews, palette and QA report.  python3 build.py [outdir]"""
import sys, os, json, numpy as np
from PIL import Image, ImageDraw, ImageFont
import ranger as RG
from pxlib import save_scaled

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
os.makedirs(OUT, exist_ok=True)
ANIMS = [('idle', RG.IDLE, 420), ('walk', RG.WALK, 110), ('shoot', RG.SHOOT, 90)]
COLS = 6; FS = 32

def frames(anim, d, shadow=True): return [RG.draw(d, p, shadow=shadow).rgba(72 if shadow else 0) for p in anim]

def build_sheet(shadow):
    rows = [(a[0], d) for a in ANIMS for d in RG.DIRS]
    sheet = np.zeros((len(rows) * FS, COLS * FS, 4), np.uint8); atlas = {}
    for r, (name, d) in enumerate(rows):
        anim = next(a for a in ANIMS if a[0] == name)
        for c, fr in enumerate(frames(anim[1], d, shadow)):
            sheet[r * FS:(r + 1) * FS, c * FS:(c + 1) * FS] = fr
    return sheet, rows

def main():
    sheet, rows = build_sheet(True); Image.fromarray(sheet, 'RGBA').save(os.path.join(OUT, 'ranger_sheet_32.png'))
    sheet2, _ = build_sheet(False); Image.fromarray(sheet2, 'RGBA').save(os.path.join(OUT, 'ranger_sheet_32_noshadow.png'))
    # atlas (Aseprite-like: frames + frameTags)
    fr = {}; tags = []; n = 0
    for r, (name, d) in enumerate(rows):
        a = next(x for x in ANIMS if x[0] == name); k = len(a[1])
        for c in range(k):
            fr[f'ranger_{name}_{d}_{c}'] = dict(frame=dict(x=c * FS, y=r * FS, w=FS, h=FS), duration=a[2], pivot=dict(x=0.5, y=27 / 32))
        tags.append(dict(name=f'{name}_{d}', from_=sum(1 for _ in fr) - k, to=len(fr) - 1, loop=name != 'shoot'))
    meta = dict(app='ranger build.py', image='ranger_sheet_32.png', size=dict(w=COLS * FS, h=len(rows) * FS), frameSize=FS, ground_pivot_y=27,
                directions=RG.DIRS, note='left = separately drawn (light stays top-left); 6 columns, unused cells are transparent', frameTags=[{('from' if k == 'from_' else k): v for k, v in t.items()} for t in tags])
    json.dump(dict(frames=fr, meta=meta), open(os.path.join(OUT, 'ranger_atlas.json'), 'w'), indent=1)
    # palette
    cols = []
    for m in RG.MATS:
        cols += [(m.name, i, '#%02x%02x%02x' % c) for i, c in enumerate(m.ramp)]
    sw = Image.new('RGB', (len(cols) * 24, 24 * 1), (0, 0, 0))
    for i, (_, _, h) in enumerate(cols): ImageDraw.Draw(sw).rectangle([i * 24, 0, i * 24 + 23, 23], fill=h)
    sw = sw.resize((sw.width, 24)); sw.save(os.path.join(OUT, 'ranger_palette.png'))
    open(os.path.join(OUT, 'ranger_palette.hex'), 'w').write('\n'.join(h[1:] for _, _, h in cols) + '\n')
    open(os.path.join(OUT, 'ranger_palette.gpl'), 'w').write('GIMP Palette\nName: Ranger\nColumns: 5\n#\n' + '\n'.join('%3d %3d %3d  %s_%d' % (*[int(h[j:j + 2], 16) for j in (1, 3, 5)], n, i) for n, i, h in cols) + '\n')
    # preview sheet x8 with labels
    bg = (44, 50, 64); K = 6
    rowsimgs = []
    for name, d in rows:
        a = next(x for x in ANIMS if x[0] == name)
        rowsimgs.append(np.hstack([RG.draw(d, p).rgba() for p in a[1]] + [np.zeros((FS, FS, 4), np.uint8)] * (COLS - len(a[1]))))
    big = np.vstack(rowsimgs); im = Image.fromarray(big, 'RGBA').resize((big.shape[1] * K, big.shape[0] * K), Image.NEAREST)
    base = Image.new('RGBA', (im.width + 150, im.height), bg + (255,)); base.alpha_composite(im, (150, 0)); dr = ImageDraw.Draw(base)
    for r, (name, d) in enumerate(rows): dr.text((8, r * FS * K + 8), f'{name} {d}', fill=(190, 200, 220))
    base.convert('RGB').save(os.path.join(OUT, 'ranger_preview_x6.png'))
    # GIFs (4 directions side by side, solid bg, x8)
    for name, seq, dur in ANIMS:
        imgs = []
        for i in range(len(seq)):
            row = np.hstack([RG.draw(d, seq[i]).rgba() for d in RG.DIRS]); im = Image.fromarray(row, 'RGBA').resize((row.shape[1] * 8, row.shape[0] * 8), Image.NEAREST)
            b = Image.new('RGBA', im.size, bg + (255,)); b.alpha_composite(im); imgs.append(b.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=64))
        imgs[0].save(os.path.join(OUT, f'ranger_{name}.gif'), save_all=True, append_images=imgs[1:], duration=dur, loop=0, disposal=1)
    # QA
    qa = qa_report(); open(os.path.join(OUT, 'QA_REPORT.txt'), 'w').write(qa); print(qa)

def qa_report():
    pal = {tuple(c) for m in RG.MATS for c in m.ramp}; L = []; bad = 0; orphan = 0; feet = {}
    for name, seq, dur in ANIMS:
        for d in RG.DIRS:
            for i, p in enumerate(seq):
                cv = RG.draw(d, p); a = cv.rgba(); op = a[..., 3] == 255
                cols = {tuple(x) for x in a[op][:, :3]}; extra = cols - pal
                if extra: bad += 1; L.append(f'  off-palette colours in {name}/{d}/{i}: {extra}')
                ys, xs = np.where(op)
                if xs.min() < 0 or xs.max() > 31 or ys.min() < 0 or ys.max() > 31: L.append(f'  out of frame {name}/{d}/{i}')
                if xs.min() == 0 or xs.max() == 31 or ys.min() == 0 or ys.max() == 31: L.append(f'  touches frame border {name}/{d}/{i}')
                # orphan pixels (no 8-neighbour) - ignore glow/flash colours
                for y, x in zip(ys, xs):
                    nb = op[max(y - 1, 0):y + 2, max(x - 1, 0):x + 2].sum() - 1
                    if nb == 0: orphan += 1; L.append(f'  orphan pixel {name}/{d}/{i} at {x},{y}')
                body = op & ~(np.isin(a[..., 0], [c[0] for c in RG.MATS[RG.GLW].ramp]) & np.isin(a[..., 1], [c[1] for c in RG.MATS[RG.GLW].ramp]))
                feet.setdefault((name, d), []).append(int(np.where(op.any(axis=1))[0].max()))
    L.insert(0, f'frames checked: {sum(len(s) for _, s, _ in ANIMS) * 4}; off-palette frames: {bad}; orphan pixels: {orphan}')
    for k, v in feet.items(): L.append(f'  lowest opaque row {k[0]}/{k[1]}: {v}')
    return 'QA\n' + '\n'.join(L) + '\n'
if __name__ == '__main__': main()
