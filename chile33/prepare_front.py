"""cut the AI FRONT parts sheet (assets/raw/p_front_parts.jpg) into layers pf_*.png + print geometry"""
import cv2, numpy as np
from scipy import ndimage as ndi
im = cv2.imread('assets/raw/p_front_parts.jpg'); im = cv2.resize(im, (1408, 768), interpolation=cv2.INTER_AREA) if im.shape[1] != 1408 else im
bg = np.median(np.vstack([im[:20].reshape(-1, 3), im[-20:].reshape(-1, 3)]), 0).astype(np.float32); print('bg', bg)
d = np.abs(im.astype(np.float32) - bg).max(2); m = ndi.binary_fill_holes(ndi.binary_closing(d > 22, iterations=2))
lab, k = ndi.label(m); objs = ndi.find_objects(lab); parts = []
for i, sl in enumerate(objs):
    a = (lab[sl] == i + 1).sum()
    if a > 2500: parts.append((sl[1].start, sl[0].start, sl[1].stop, sl[0].stop, i + 1, int(a)))
parts.sort(); [print(p) for p in parts]; np.save('build/front_lab.npy', lab)
import json; json.dump(parts, open('build/front_parts.json', 'w'))
names = {5: 'torso', 2: 'arm', 11: 'foreL', 12: 'foreR', 3: 'legs', 17: 'shoeA', 18: 'shoeB'}
sheet = []
for lid, nm in names.items():
    mk = ndi.binary_erosion(lab == lid, iterations=1); ys, xs = np.where(mk); y0, y1, x0, x1 = ys.min() - 3, ys.max() + 4, xs.min() - 3, xs.max() + 4
    a = cv2.GaussianBlur(mk[y0:y1, x0:x1].astype(np.float32), (0, 0), 0.9); rgb = im[y0:y1, x0:x1].astype(np.float32)
    inner = ndi.binary_erosion(mk[y0:y1, x0:x1], iterations=3); idx = ndi.distance_transform_edt(~inner, return_distances=False, return_indices=True)
    wgt = np.clip(ndi.distance_transform_edt(inner) / 3.0, 0, 1)[..., None]; rgb = rgb[idx[0], idx[1]] * (1 - wgt) + rgb * wgt
    out = np.dstack([rgb, a * 255]).astype(np.uint8); cv2.imwrite(f'assets/layers/pf_{nm}.png', out); print(nm, out.shape[1], out.shape[0])
    ck = np.indices(out.shape[:2]).sum(0) // 16 % 2 * 40 + 100; prev = (rgb * a[..., None] + ck[..., None] * (1 - a[..., None])).astype(np.uint8)
    for gy in range(0, prev.shape[0], 50): cv2.putText(prev, str(gy), (0, gy + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
    for gx in range(0, prev.shape[1], 50): cv2.putText(prev, str(gx), (gx, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1)
    sheet.append(prev)
Hh = max(s.shape[0] for s in sheet)
cv2.imwrite('build/front_cut.jpg', np.hstack([np.pad(s, ((0, Hh - s.shape[0]), (0, 8), (0, 0))) for s in sheet]))
