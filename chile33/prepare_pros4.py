"""Prosperi part 4 assets: dawn + kit plates (wide 1584x672) and the helicopter body cut out (RGBA, facing right and left) from the grey-background sheet."""
import cv2, numpy as np
from scipy import ndimage as ndi
for n in ('dawn', 'kit'):
    cv2.imwrite(f'assets/layers/pr_{n}.jpg', cv2.imread(f'assets/raw/pr_{n}.jpg'), [cv2.IMWRITE_JPEG_QUALITY, 95])
im = cv2.imread('assets/raw/heli_body.jpg'); f = im.astype(np.float32)
bg = np.median(np.concatenate([f[:20, :20].reshape(-1, 3), f[:20, -20:].reshape(-1, 3), f[-20:, :20].reshape(-1, 3), f[-20:, -20:].reshape(-1, 3)]), axis=0)
d = np.sqrt(((f - bg) ** 2).sum(axis=2)); m = d > 16
m = ndi.binary_closing(m, iterations=2); lab, n = ndi.label(ndi.binary_dilation(m, iterations=3)); sizes = ndi.sum(m, lab, range(1, n + 1)); keep = lab == (1 + int(np.argmax(sizes)))
m = m & keep; m = ndi.binary_fill_holes(m)
a = np.clip((d - 8) / 22, 0, 1) * ndi.binary_dilation(m, iterations=2); a = np.where(ndi.binary_erosion(m, iterations=2), 1.0, np.minimum(a, cv2.GaussianBlur(ndi.binary_dilation(m, iterations=1).astype(np.float32), (0, 0), 1.0)))
col = np.clip((f - (1 - a[..., None]) * bg) / np.maximum(a[..., None], 0.08), 0, 255)
ys, xs = np.where(m); y0, y1, x0, x1 = ys.min() - 2, ys.max() + 3, xs.min() - 2, xs.max() + 3
out = np.dstack([col, a * 255]).astype(np.uint8)[y0:y1, x0:x1]
cv2.imwrite('assets/layers/heli_r.png', out); cv2.imwrite('assets/layers/heli_l.png', out[:, ::-1].copy())
top = np.where(out[:, :, 3] > 128)
print(out.shape, 'mast top (x,y):', [(int(x), int(y)) for y, x in zip(*[t[np.argsort(t)[:1]] for t in top])] if False else '')
ys2, xs2 = top; i = np.argmin(ys2); print('topmost', xs2[i], ys2[i]); print('leftmost', xs2.min(), ys2[np.argmin(xs2)])
