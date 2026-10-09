"""Part 8 prep: plates h8_home, h8_street, h8_gate, h8_press (1376x768, checked: no borders)."""
import cv2
for n in ('home', 'street', 'gate', 'press'):
    im = cv2.imread(f'assets/raw/p8_{n}.jpg'); assert im.shape[:2] == (768, 1376); cv2.imwrite(f'assets/layers/h8_{n}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 95])
