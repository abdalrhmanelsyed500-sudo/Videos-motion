"""Prosperi part 5 plates: shrine, inside, night, aerial (wide 1584x672)."""
import cv2
for n in ('shrine', 'inside', 'night', 'aerial'):
    cv2.imwrite(f'assets/layers/pr_{n}.jpg', cv2.imread(f'assets/raw/pr_{n}.jpg'), [cv2.IMWRITE_JPEG_QUALITY, 95])
