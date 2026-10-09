"""Part 7 prep: plates h7_site, h7_sun, h7_shaft cropped/scaled to 1376x768 (cover)."""
import cv2
for n, off in (('site', None), ('sun', 240), ('shaft', None)):
    im = cv2.imread(f'assets/raw/p7_{n}.jpg'); h, w = im.shape[:2]; s = max(1376 / w, 768 / h)
    im = cv2.resize(im, (int(round(w * s)), int(round(h * s))), interpolation=cv2.INTER_AREA); h, w = im.shape[:2]
    x0 = (w - 1376) // 2 if off is None else off; y0 = (h - 768) // 2
    cv2.imwrite(f'assets/layers/h7_{n}.jpg', im[y0:y0 + 768, x0:x0 + 1376], [cv2.IMWRITE_JPEG_QUALITY, 95])
