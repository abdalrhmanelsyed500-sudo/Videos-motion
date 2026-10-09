"""Part 5 prep: cut the drill bit + pipe (RGBA), plates h5_wall / h5_depth."""
import cv2, numpy as np
from scipy import ndimage as ndi
for n in ('wall', 'depth'):
    im = cv2.imread(f'assets/raw/p5_{n}.jpg'); assert im.shape[:2] == (768, 1376); cv2.imwrite(f'assets/layers/h5_{n}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 95])
im = cv2.imread('assets/raw/p5_bit.jpg'); bg = np.median(im.reshape(-1, 3)[::7], axis=0).astype(np.float32)
d = np.linalg.norm(im.astype(np.float32) - bg, axis=2); d = cv2.GaussianBlur(d, (0, 0), 1.0)
m = d > 38; m = ndi.binary_closing(m, iterations=3); m = ndi.binary_fill_holes(m); m = ndi.binary_opening(m, iterations=2)
lab, n = ndi.label(m); sizes = ndi.sum(m, lab, range(1, n + 1)); k = 1 + int(np.argmax(sizes)); mk = lab == k
inner = ndi.binary_erosion(mk, iterations=2); edge = np.clip((d - 20) / 30, 0, 1) * ndi.binary_dilation(mk, iterations=2)
a = np.where(inner, 1.0, np.minimum(edge, cv2.GaussianBlur(ndi.binary_dilation(mk, iterations=1).astype(np.float32), (0, 0), 1.0))).astype(np.float32)
col = np.clip((im.astype(np.float32) - (1 - a[..., None]) * bg) / np.maximum(a[..., None], 0.1), 0, 255)
ys, xs = np.where(mk); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min() - 2, xs.max() + 3
out = np.dstack([col, a * 255]).astype(np.uint8)[y0:y1, x0:x1]; cv2.imwrite('assets/layers/h5_bit.png', out)
print('bit', out.shape, 'offset', x0, y0, 'top row width cols', np.where(out[0, :, 3] > 128)[0][[0, -1]], 'bottom row', np.where(out[-1, :, 3] > 128)[0][[0, -1]] if (out[-1, :, 3] > 128).any() else None)
