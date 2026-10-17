"""Build every sprite sheet / GIF / atlas for the penguin commando.   usage: python build_all.py [outdir]"""
import sys, os, json, time, numpy as np
from multiprocessing import Pool
from PIL import Image
import anims as A, frames as F, penguin as P
OUT = sys.argv[1] if len(sys.argv) > 1 else 'out'
BG = (0xbc, 0xc9, 0x93) if P.STYLE == 'lackey' else (70, 86, 66)
ORDER = ['idle', 'walk', 'run', 'shoot', 'reload', 'hit', 'death']; DIRS = ['down', 'up', 'right', 'left']
LABEL = {'idle': 'Idle (breathing)', 'walk': 'Walk', 'run': 'Run', 'shoot': 'Shoot (full-auto loop)', 'reload': 'Reload', 'hit': 'Get hit', 'death': 'Hit and die'}

def job(args):
    name, d, shadow = args; y = A.DIRS[d]; ps = A.ANIMS[name][0](y); cx = A.cx_for(name, y)
    return (name, d, shadow, [F.render_frame(p, y, shadow=shadow, cx=cx) for p in ps])

def noshadow_clean(im):    # drop semi-transparent shadow pixels completely
    im = im.copy(); im[im[..., 3] < 255] = 0; return im

def sheet(frames_by_dir):
    n = max(len(v) for v in frames_by_dir.values()); S = np.zeros((64 * 4, 64 * n, 4), np.uint8)
    for r, d in enumerate(DIRS):
        for c, im in enumerate(frames_by_dir[d]): S[r * 64:(r + 1) * 64, c * 64:(c + 1) * 64] = im
    return S

def gif(path, ims, dur, k=4, bg=None, loop=True):
    bg = bg or BG
    out = []
    for im in ims:
        a = Image.fromarray(im, 'RGBA'); a = a.resize((a.width * k, a.height * k), Image.NEAREST)
        b = Image.new('RGBA', a.size, bg + (255,)); b.alpha_composite(a); out.append(b.convert('RGB').quantize(colors=64, dither=Image.NONE))
    out[0].save(path, save_all=True, append_images=out[1:], duration=dur, loop=0 if loop else 1, disposal=2)

if __name__ == '__main__':
    t0 = time.time()
    for sub in ('sheets', 'sheets_noshadow', 'gifs', 'gifs_by_direction', 'frames_png'): os.makedirs(f'{OUT}/{sub}', exist_ok=True)
    jobs = [(n, d, s) for s in (True, False) for n in ORDER for d in DIRS]
    with Pool(2) as pool: res = pool.map(job, jobs, chunksize=2)
    R = {}; RN = {}
    for name, d, sh, fr in res: (R if sh else RN).setdefault(name, {})[d] = fr
    atlas = dict(canvas=[64, 64], camera='top-down 3/4 (44 deg), light from top-left', directions=DIRS, direction_row={d: i for i, d in enumerate(DIRS)}, pivot_note='feet-contact origin is at (32 + pivot_dx, 47) in each frame', animations={})
    qa = []; allrows = []; total = 0; clipped = 0; offpal = 0; fxorph = {}
    pal = {tuple(c) for r in P.RAMP_RGB for c in r} | {P.TEAL if hasattr(P, 'TEAL') else (0, 0, 0)}
    for name in ORDER:
        fn, dur, loop = A.ANIMS[name]; byd = R[name]; nfr = len(byd['down']); total += nfr * 4
        S = sheet(byd); Image.fromarray(S, 'RGBA').save(f'{OUT}/sheets/penguin_{name}_sheet.png')
        Sn = sheet(RN[name])
        Image.fromarray(Sn, 'RGBA').save(f'{OUT}/sheets_noshadow/penguin_{name}_sheet_noshadow.png')
        gif(f'{OUT}/gifs/penguin_{name}.gif', [np.concatenate([byd[d][i] for d in DIRS], 1) for i in range(nfr)], dur, loop=loop if name not in ('reload', 'hit', 'death') else True)
        for d in DIRS:
            gif(f'{OUT}/gifs_by_direction/penguin_{name}_{d}.gif', byd[d], dur, k=6)
            for i, im in enumerate(byd[d]): Image.fromarray(im, 'RGBA').save(f'{OUT}/frames_png/{name}_{d}_{i:02d}.png')
            row = np.zeros((64, 64 * 16, 4), np.uint8)
            for i, im in enumerate(byd[d]): row[:, i * 64:(i + 1) * 64] = im
            allrows.append(row)
            for i, im in enumerate(byd[d]):
                op = im[..., 3] == 255
                if P.STYLE == 'lackey': op = op & ~np.all(im[..., :3] == np.array(P.TEAL), axis=2)     # ground disc may touch the frame edge
                if op[0].any() or op[-1].any() or op[:, 0].any() or op[:, -1].any(): clipped += 1; qa.append(f'  CLIPPED at frame edge: {name}/{d}/{i}')
                rgb = im[..., :3][op]; 
                for c in {tuple(x) for x in rgb}:
                    if c not in pal and c != (0, 0, 0): pass
                bad = sum(1 for c in {tuple(x) for x in rgb} if c not in pal)
                if bad: offpal += bad
                # orphans (opaque pixel with no opaque 4-neighbour)
                nb = np.zeros_like(op); nb[1:] |= op[:-1]; nb[:-1] |= op[1:]; nb[:, 1:] |= op[:, :-1]; nb[:, :-1] |= op[:, 1:]
                o = int((op & ~nb).sum()); fxorph[name] = fxorph.get(name, 0) + o
        atlas['animations'][name] = dict(label=LABEL[name], frames=nfr, frame_ms=dur, loop=loop, rows={d: DIRS.index(d) for d in DIRS},
                                         sheet=f'sheets/penguin_{name}_sheet.png', pivot_dx={d: A.cx_for(name, A.DIRS[d]) - 32 for d in DIRS})
    master = np.concatenate(allrows, 0); Image.fromarray(master, 'RGBA').save(f'{OUT}/penguin_ALL_sheet.png')
    atlas['master_sheet'] = dict(file='penguin_ALL_sheet.png', rows=[f'{n}_{d}' for n in ORDER for d in DIRS], cols=16, cell=[64, 64])
    json.dump(atlas, open(f'{OUT}/penguin_atlas.json', 'w'), indent=1, ensure_ascii=False)
    big = Image.fromarray(master, 'RGBA').resize((master.shape[1] * 2, master.shape[0] * 2), Image.NEAREST); bg = Image.new('RGBA', big.size, BG + (255,)); bg.alpha_composite(big); bg.convert('RGB').save(f'{OUT}/penguin_ALL_preview_x2.png')
    # palette files
    uniq = []
    for r in P.RAMP_RGB:
        for col in r:
            if col not in uniq: uniq.append(col)
    if P.STYLE == 'lackey': uniq.append(P.TEAL)
    sw = Image.new('RGB', (8 * 24, ((len(uniq) + 7) // 8) * 24), (40, 40, 40))
    with open(f'{OUT}/penguin_palette.hex', 'w') as fh, open(f'{OUT}/penguin_palette.gpl', 'w') as fg:
        fg.write('GIMP Palette\nName: Penguin Commando (%s)\nColumns: 8\n#\n' % P.STYLE)
        for i, col in enumerate(uniq):
            sw.paste(col, ((i % 8) * 24, (i // 8) * 24, (i % 8) * 24 + 24, (i // 8) * 24 + 24)); fh.write('%02x%02x%02x\n' % col); fg.write('%3d %3d %3d\tc%02d\n' % (*col, i))
    sw.save(f'{OUT}/penguin_palette.png'); print('unique colours:', len(uniq))
    rep = ['PENGUIN COMMANDO - QA REPORT (automated)', '', f'frames rendered: {total}  (7 animations x 4 directions)  style: ' + P.STYLE + f'  unique colours: {len(uniq)}',
           f'frames touching the 64x64 border with opaque pixels: {clipped}', f'off-palette colours (opaque pixels): {offpal}', 'isolated single pixels per animation (blood drops, casings, muzzle sparks are intentional): ' + str(fxorph)] + qa
    rep += ['', 'not covered by automation: how good the poses look. That was reviewed by eye in zoomed contact sheets (see README, known weaknesses).']
    open(f'{OUT}/QA_REPORT.txt', 'w').write('\n'.join(rep)); print('\n'.join(rep)); print('time %.0fs' % (time.time() - t0))
