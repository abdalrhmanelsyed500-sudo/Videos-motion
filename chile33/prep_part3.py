"""Part 3 plates -> depth layers (does NOT touch the other layers)."""
import cv2, numpy as np
def poly_layer(bgp, name, pts, feather=4):
    H, W = bgp.shape[:2]; m = np.zeros((H, W), np.float32); cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0); m = cv2.GaussianBlur(m, (0, 0), feather)
    cv2.imwrite(f'assets/layers/{name}.png', np.dstack([bgp, (m * 255).astype(np.uint8)]))
for n in ('p3_door', 'p3_storage', 'p3_table'):
    im = cv2.imread(f'assets/raw/{n}.jpg'); assert im.shape[:2] == (768, 1376)
    cv2.imwrite(f'assets/layers/h3_{n[3:]}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if n == 'p3_door':
        poly_layer(im, 'h3_door_wl', [(0, 0), (380, 0), (345, 400), (300, 768), (0, 768)], 8); poly_layer(im, 'h3_door_wr', [(1180, 0), (1376, 0), (1376, 768), (1090, 768), (1150, 400)], 8)
    if n == 'p3_table':
        k = 1.4333; pts = [(240, 412), (330, 318), (555, 316), (705, 388), (712, 425), (640, 432), (640, 540), (318, 540), (318, 432)]
        poly_layer(im, 'h3_table_fg', [(int(x * k), int(y * k)) for x, y in pts], 5)
