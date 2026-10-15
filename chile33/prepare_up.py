"""chroma-key the generated foreground elements (green screen) into RGBA layers with despill"""
import cv2, numpy as np
from scipy import ndimage as ndi
for n in ('rocks', 'dune'):
    im = cv2.imread(f'assets/raw/up_fg_{n}.jpg').astype(np.float32); h, w = im.shape[:2]
    b, g, r = im[..., 0], im[..., 1], im[..., 2]
    gd = g - np.maximum(r, b)                     # greenness
    a = 1 - np.clip((gd - 25) / 50, 0, 1)
    a = ndi.binary_opening(a > 0.5, iterations=1).astype(np.float32) * 0 + a
    a = cv2.GaussianBlur(a, (0, 0), 0.8)
    # remove tiny islands
    m = a > 0.5; lab, k = ndi.label(m); sizes = ndi.sum(m, lab, range(1, k + 1)); keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 400])
    a = a * ndi.binary_dilation(keep, iterations=3)
    g2 = np.minimum(g, np.maximum(r, b)); im[..., 1] = g2        # despill
    out = np.dstack([np.clip(im, 0, 255), a * 255]).astype(np.uint8)
    ys, xs = np.where(a > 0.5); out = out[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    cv2.imwrite(f'assets/layers/up_fg_{n}.png', out); print(n, out.shape)
    prev = np.full((h, w, 3), 90, np.uint8); a3 = (a[..., None]); prev = (np.clip(im, 0, 255) * a3 + prev * (1 - a3)).astype(np.uint8); cv2.imwrite(f'build/up_prev_{n}.jpg', prev)
