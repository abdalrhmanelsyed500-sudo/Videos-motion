"""cut the AI side-profile parts sheet (assets/raw/p_side_parts.jpg) into RGBA layers ps_*.png (connected components on a flat grey background)"""
import cv2, numpy as np
from scipy import ndimage as ndi
im = cv2.imread('assets/raw/p_side_parts.jpg'); im = cv2.resize(im, (1408, 768), interpolation=cv2.INTER_AREA) if im.shape[1] != 1408 else im
bg = np.median(np.vstack([im[:20].reshape(-1, 3), im[-20:].reshape(-1, 3)]), 0).astype(np.float32); print('bg', bg)
d = np.abs(im.astype(np.float32) - bg).max(2)
m = d > 22
m = ndi.binary_closing(m, iterations=2); m = ndi.binary_fill_holes(m)
lab, k = ndi.label(m); objs = ndi.find_objects(lab)
parts = []
for i, sl in enumerate(objs):
    a = (lab[sl] == i + 1).sum()
    if a < 3000: continue
    parts.append((sl[1].start, sl[0].start, sl[1].stop, sl[0].stop, i + 1, a))
for p in sorted(parts): print(p)
np.save('build/side_lab.npy', lab)
names = {1: 'head', 8: 'torso', 6: 'arm_a', 5: 'arm_b', 15: 'fore', 4: 'leg', 11: 'shin', 19: 'shoe'}
sheet = []
for lid, nm in names.items():
    mk = (lab == lid); mk = ndi.binary_erosion(mk, iterations=1)
    ys, xs = np.where(mk); y0, y1, x0, x1 = ys.min() - 3, ys.max() + 4, xs.min() - 3, xs.max() + 4
    a = cv2.GaussianBlur(mk[y0:y1, x0:x1].astype(np.float32), (0, 0), 0.9)
    rgb = im[y0:y1, x0:x1].astype(np.float32)
    # de-halo: pull edge colours toward interior colours
    inner = ndi.binary_erosion(mk[y0:y1, x0:x1], iterations=3)
    idx = ndi.distance_transform_edt(~inner, return_distances=False, return_indices=True)
    rgb = rgb[idx[0], idx[1]] * (1 - np.clip(ndi.distance_transform_edt(inner) / 3.0, 0, 1))[..., None] + rgb * np.clip(ndi.distance_transform_edt(inner) / 3.0, 0, 1)[..., None]
    out = np.dstack([rgb, a * 255]).astype(np.uint8); cv2.imwrite(f'assets/layers/ps_{nm}.png', out); print(nm, out.shape[1], out.shape[0])
    ck = np.indices(out.shape[:2]).sum(0) // 16 % 2 * 40 + 100
    prev = (rgb * a[..., None] + ck[..., None] * (1 - a[..., None])).astype(np.uint8)
    for gy in range(0, prev.shape[0], 50): cv2.putText(prev, str(gy), (0, gy + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
    for gx in range(0, prev.shape[1], 50): cv2.putText(prev, str(gx), (gx, 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1)
    sheet.append(prev)
Hh = max(s.shape[0] for s in sheet)
cv2.imwrite('build/side_cut.jpg', np.hstack([np.pad(s, ((0, Hh - s.shape[0]), (0, 8), (0, 0))) for s in sheet]))
