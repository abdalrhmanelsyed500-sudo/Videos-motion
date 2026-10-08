"""Oil-painted puppet: cut the parts sheet into RGBA layers + split the alley plate into parallax layers."""
import cv2, numpy as np
from scipy import ndimage as ndi
im = cv2.imread('assets/raw/ar_parts.jpg'); bg = np.array([197., 197., 197.])
d = np.linalg.norm(im.astype(np.float32) - bg, axis=2)
m = ndi.binary_fill_holes(ndi.binary_closing(d > 22, iterations=2)); lab, n = ndi.label(m)
PARTS = {'head': (448, 37, 587, 255), 'lid_l': (663, 90, 725, 140), 'lid_r': (746, 90, 806, 139), 'mouth': (669, 154, 739, 207), 'torso': (362, 272, 664, 652),
         'arm_l': (168, 264, 274, 455), 'arm_r': (735, 272, 860, 460), 'fore_l': (177, 469, 276, 719), 'fore_r': (757, 465, 855, 724),
         'leg_l': (936, 211, 1112, 722), 'leg_r': (1152, 216, 1353, 720)}
for k, (x0, y0, x1, y1) in PARTS.items():
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    ids = [i for i in np.unique(lab[y0:y1, x0:x1]) if i and (lab == i).sum() > 300 and abs(np.argwhere(lab == i)[:, 1].mean() - cx) < 200]
    pick = max(ids, key=lambda i: (lab[y0:y1, x0:x1] == i).sum())
    mk = (lab == pick).astype(np.float32)
    a = np.clip((d - 14) / 26, 0, 1) * ndi.binary_dilation(mk > 0, iterations=3)
    a = np.minimum(a, cv2.GaussianBlur(ndi.binary_erosion(mk > 0, iterations=1).astype(np.float32), (0, 0), 1.0) * 1.0 + 0.0)
    af = np.clip(a, 0, 1); col = np.clip((im.astype(np.float32) - (1 - af[..., None]) * bg) / np.maximum(af[..., None], 0.05), 0, 255)
    out = np.dstack([col, af * 255]).astype(np.uint8)[y0 - 2:y1 + 2, x0 - 2:x1 + 2]
    cv2.imwrite(f'assets/layers/ar_{k}.png', out)
# ---- alley plate layers
bgp = cv2.imread('assets/raw/ar_bg.jpg'); H, W = bgp.shape[:2]
cv2.imwrite('assets/layers/ar_bg.jpg', bgp, [cv2.IMWRITE_JPEG_QUALITY, 95])
def poly_layer(name, pts, feather=3):
    m = np.zeros((H, W), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0); m = cv2.GaussianBlur(m, (0, 0), feather)
    cv2.imwrite(f'assets/layers/{name}.png', np.dstack([bgp, (m * 255).astype(np.uint8)]))
poly_layer('ar_wall_l', [(0, 0), (585, 0), (598, 330), (598, 612), (380, H), (0, H)])
poly_layer('ar_wall_r', [(852, 0), (W, 0), (W, H), (1000, H), (822, 600), (852, 300)])
x0, y0, x1, y1 = 572, 190, 662, 352
m = np.zeros((H, W), np.float32); cv2.ellipse(m, ((x0 + x1) // 2, (y0 + y1) // 2 + 8), ((x1 - x0) // 2, (y1 - y0) // 2), 0, 0, 360, 1.0, -1)
m = cv2.GaussianBlur(m, (0, 0), 4); cv2.imwrite('assets/layers/ar_lantern.png', np.dstack([bgp, (m * 255).astype(np.uint8)])[y0:y1, x0:x1])
print('ok')
