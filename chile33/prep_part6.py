"""Part 6 prep: plates h6_space, h6_rigs (copied from the generated rasters)."""
import cv2
for n in ('space', 'rigs'):
    im = cv2.imread(f'assets/raw/p6_{n}.jpg'); assert im.shape[:2] == (768, 1376); cv2.imwrite(f'assets/layers/h6_{n}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 95])
