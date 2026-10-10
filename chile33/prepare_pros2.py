"""Prosperi part 2 plates: crop AI borders, save wide plates 1584x672 to assets/layers/pr_*.jpg."""
import cv2, numpy as np
CROP = {'stadium': (38, 36, 44, 46), 'map': (62, 54, 76, 76)}   # top, bottom, left, right inset (px)
for n in ('rome', 'stadium', 'penta', 'map', 'rocks', 'camp'):
    im = cv2.imread(f'assets/raw/pr_{n}.jpg')
    if n in CROP:
        t, b, l, r = CROP[n]; im = im[t:im.shape[0] - b, l:im.shape[1] - r]
        im = cv2.resize(im, (1584, 672), interpolation=cv2.INTER_CUBIC)
    cv2.imwrite(f'assets/layers/pr_{n}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 95])
