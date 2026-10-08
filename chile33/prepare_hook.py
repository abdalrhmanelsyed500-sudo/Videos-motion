"""Hook project: cut parts sheets (m = miner, w = woman) into RGBA layers, sprites (rocks, food), and split plates into depth layers."""
import cv2, json, numpy as np
from scipy import ndimage as ndi
SEEDS = {'head': (515, 150), 'lid_l': (690, 115), 'lid_r': (775, 115), 'mouth': (703, 182), 'torso': (515, 450), 'arm_l': (220, 345), 'arm_r': (800, 355),
         'fore_l': (215, 600), 'fore_r': (810, 600), 'leg_l': (1000, 450), 'leg_r': (1210, 450)}


def bgcol(im):
    b = np.concatenate([im[:12].reshape(-1, 3), im[-12:].reshape(-1, 3), im[:, :12].reshape(-1, 3), im[:, -12:].reshape(-1, 3)])
    return np.median(b, axis=0).astype(np.float32)


def matte(im, bg, thr=22):
    d = np.linalg.norm(im.astype(np.float32) - bg, axis=2)
    d = cv2.GaussianBlur(d, (0, 0), 0.8)
    m = ndi.binary_fill_holes(ndi.binary_closing(d > thr, iterations=2)); m = ndi.binary_opening(m, iterations=1)
    return d, m


def cut(im, bg, d, mk, pad=2):
    inner = ndi.binary_erosion(mk, iterations=3)
    edge = np.clip((d - 12) / 24, 0, 1) * ndi.binary_dilation(mk, iterations=2)
    a = np.where(inner, 1.0, np.minimum(edge, cv2.GaussianBlur(ndi.binary_dilation(mk, iterations=1).astype(np.float32), (0, 0), 1.0)))
    a = a.astype(np.float32)
    col = np.clip((im.astype(np.float32) - (1 - a[..., None]) * bg) / np.maximum(a[..., None], 0.08), 0, 255)
    ys, xs = np.where(mk); y0, y1, x0, x1 = ys.min() - pad, ys.max() + pad + 1, xs.min() - pad, xs.max() + pad + 1
    out = np.dstack([col, a * 255]).astype(np.uint8)[y0:y1, x0:x1]
    return out, (int(x0), int(y0))


offs = {}
for ch in ('m', 'w', 'u', 's', 'g', 'j'):
    im = cv2.imread(f'assets/raw/{ch}_parts.jpg'); bg = bgcol(im); d, m = matte(im, bg); lab, n = ndi.label(m)
    offs[ch] = {}
    for k, (sx, sy) in SEEDS.items():
        win = lab[sy - 12:sy + 12, sx - 12:sx + 12]; ids = [i for i in np.unique(win) if i]
        if not ids: print('NO COMPONENT', ch, k); continue
        i = max(ids, key=lambda i: (win == i).sum()); out, off = cut(im, bg, d, lab == i)
        cv2.imwrite(f'assets/layers/{ch}_{k}.png', out); offs[ch][k] = off
    print(ch, offs[ch])
json.dump(offs, open('data/offs.json', 'w'))


def sprites(src, prefix, minarea=1500):
    im = cv2.imread(f'assets/raw/{src}.jpg'); bg = bgcol(im); d, m = matte(im, bg, 26); lab, n = ndi.label(m)
    items = [(i, np.argwhere(lab == i)) for i in range(1, n + 1) if (lab == i).sum() > minarea]
    items.sort(key=lambda t: (round(t[1][:, 0].mean() / 300), t[1][:, 1].mean()))
    for j, (i, _) in enumerate(items):
        out, _ = cut(im, bg, d, lab == i); cv2.imwrite(f'assets/layers/{prefix}_{j}.png', out)
    print(prefix, len(items))
sprites('m_rocks', 'rock'); sprites('m_food', 'food')

# ---- plates
def inpaint_box(img, box, pad=6):
    x0, y0, x1, y1 = box; m = np.zeros(img.shape[:2], np.uint8); cv2.ellipse(m, ((x0 + x1) // 2, (y0 + y1) // 2), ((x1 - x0) // 2 + pad, (y1 - y0) // 2 + pad), 0, 0, 360, 255, -1)
    return cv2.inpaint(img, m, 9, cv2.INPAINT_TELEA)


def poly_layer(bgp, name, pts, feather=4):
    H, W = bgp.shape[:2]; m = np.zeros((H, W), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0); m = cv2.GaussianBlur(m, (0, 0), feather)
    cv2.imwrite(f'assets/layers/{name}.png', np.dstack([bgp, (m * 255).astype(np.uint8)]))


def lamp_layer(bgp, name, box):
    x0, y0, x1, y1 = box; H, W = bgp.shape[:2]; m = np.zeros((H, W), np.float32)
    cv2.ellipse(m, ((x0 + x1) // 2, (y0 + y1) // 2), ((x1 - x0) // 2, (y1 - y0) // 2), 0, 0, 360, 1.0, -1); m = cv2.GaussianBlur(m, (0, 0), 3)
    cv2.imwrite(f'assets/layers/{name}.png', np.dstack([bgp, (m * 255).astype(np.uint8)])[y0:y1, x0:x1])


for p in ('p1', 'p2', 'p3', 'p4', 'p5', 'p6'):
    im = cv2.imread(f'assets/raw/m_{p}.jpg'); assert im.shape[:2] == (768, 1376), im.shape
    if p == 'p2':
        lamp_layer(im, 'h_p2_lamp', (668, 120, 744, 214)); base = inpaint_box(im, (706, 167, 76, 94)[:0] or (668, 120, 744, 214), 8)
        cv2.imwrite('assets/layers/h_p2.jpg', base, [cv2.IMWRITE_JPEG_QUALITY, 95])
        poly_layer(base, 'h_p2_wl', [(0, 0), (430, 0), (440, 200), (450, 520), (320, 768), (0, 768)])
        poly_layer(base, 'h_p2_wr', [(985, 0), (1376, 0), (1376, 768), (1010, 768), (990, 520)])
    elif p == 'p3':
        lamp_layer(im, 'h_p3_lamp', (488, 66, 578, 266)); base = inpaint_box(im, (488, 66, 578, 266), 8)
        cv2.imwrite('assets/layers/h_p3.jpg', base, [cv2.IMWRITE_JPEG_QUALITY, 95])
        poly_layer(base, 'h_p3_wl', [(0, 0), (275, 0), (285, 300), (290, 640), (200, 768), (0, 768)])
        poly_layer(base, 'h_p3_wr', [(1095, 0), (1376, 0), (1376, 768), (1180, 768), (1150, 650), (1100, 150)])
    elif p == 'p1':
        cv2.imwrite('assets/layers/h_p1.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 95]); poly_layer(im, 'h_p1_gr', [(0, 650), (1376, 650), (1376, 768), (0, 768)], 22)
    elif p == 'p5':
        cv2.imwrite('assets/layers/h_p5.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 95]); poly_layer(im, 'h_p5_gr', [(0, 640), (1376, 640), (1376, 768), (0, 768)], 22)
    elif p == 'p6':
        cv2.imwrite('assets/layers/h_p6.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 95])
        poly_layer(im, 'h_p6_wl', [(0, 0), (150, 0), (170, 300), (200, 700), (190, 768), (0, 768)], 8); poly_layer(im, 'h_p6_wr', [(1230, 0), (1376, 0), (1376, 768), (1250, 768), (1260, 500)], 8)
    else: cv2.imwrite('assets/layers/h_p4.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 95])
# ---- part 2 plates
for nm in ('mine', 'home', 'house', 'street'):
    im = cv2.imread(f'assets/raw/p2_{nm}.jpg'); assert im.shape[:2] == (768, 1376)
    cv2.imwrite(f'assets/layers/h2_{nm}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if nm in ('mine', 'house', 'street'): poly_layer(im, f'h2_{nm}_gr', [(0, 650), (1376, 650), (1376, 768), (0, 768)], 22)
print('ok')
