"""Part 4 prep: cut y (Yonni Barrios) + v (Victor Segovia) from parts sheets; plates -> h4_*. Does not touch other layers."""
import cv2, json, shutil, numpy as np
from scipy import ndimage as ndi
SEEDS = {'head': (515, 150), 'lid_l': (690, 115), 'lid_r': (775, 115), 'mouth': (703, 182), 'torso': (515, 450), 'arm_l': (220, 345), 'arm_r': (800, 355),
         'fore_l': (215, 600), 'fore_r': (810, 600), 'leg_l': (1000, 450), 'leg_r': (1210, 450)}
def bgcol(im):
    b = np.concatenate([im[:12].reshape(-1, 3), im[-12:].reshape(-1, 3), im[:, :12].reshape(-1, 3), im[:, -12:].reshape(-1, 3)]); return np.median(b, axis=0).astype(np.float32)
def matte(im, bg, thr=22):
    d = np.linalg.norm(im.astype(np.float32) - bg, axis=2); d = cv2.GaussianBlur(d, (0, 0), 0.8)
    m = ndi.binary_fill_holes(ndi.binary_closing(d > thr, iterations=2)); m = ndi.binary_opening(m, iterations=1); return d, m
def cut(im, bg, d, mk, pad=2):
    inner = ndi.binary_erosion(mk, iterations=3); edge = np.clip((d - 12) / 24, 0, 1) * ndi.binary_dilation(mk, iterations=2)
    a = np.where(inner, 1.0, np.minimum(edge, cv2.GaussianBlur(ndi.binary_dilation(mk, iterations=1).astype(np.float32), (0, 0), 1.0))).astype(np.float32)
    col = np.clip((im.astype(np.float32) - (1 - a[..., None]) * bg) / np.maximum(a[..., None], 0.08), 0, 255)
    ys, xs = np.where(mk); y0, y1, x0, x1 = ys.min() - pad, ys.max() + pad + 1, xs.min() - pad, xs.max() + pad + 1
    return np.dstack([col, a * 255]).astype(np.uint8)[y0:y1, x0:x1], (int(x0), int(y0))
offs = json.load(open('data/offs.json'))
for ch in ('y', 'v'):
    im = cv2.imread(f'assets/raw/{ch}_parts.jpg'); bg = bgcol(im); d, m = matte(im, bg); lab, n = ndi.label(m); offs[ch] = {}
    for k, (sx, sy) in SEEDS.items():
        win = lab[sy - 12:sy + 12, sx - 12:sx + 12]; ids = [i for i in np.unique(win) if i]
        if not ids: print('NO COMPONENT', ch, k); continue
        i = max(ids, key=lambda i: (win == i).sum()); out, off = cut(im, bg, d, lab == i); cv2.imwrite(f'assets/layers/{ch}_{k}.png', out); offs[ch][k] = off
    shutil.copy('assets/layers/m_mouth.png', f'assets/layers/{ch}_mouth.png'); offs[ch]['mouth'] = offs['m']['mouth']
    print(ch, offs[ch])
json.dump(offs, open('data/offs.json', 'w'))
def poly_layer(bgp, name, pts, feather=4):
    H, W = bgp.shape[:2]; m = np.zeros((H, W), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0); m = cv2.GaussianBlur(m, (0, 0), feather)
    cv2.imwrite(f'assets/layers/{name}.png', np.dstack([bgp, (m * 255).astype(np.uint8)]))
for n in ('p4_map', 'p4_night'):
    im = cv2.imread(f'assets/raw/{n}.jpg'); assert im.shape[:2] == (768, 1376); cv2.imwrite(f'assets/layers/h4_{n[3:]}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if n == 'p4_night': poly_layer(im, 'h4_night_gr', [(0, 700), (1376, 700), (1376, 768), (0, 768)], 14)
