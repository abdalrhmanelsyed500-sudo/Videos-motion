"""Part 4 assets: trim the white ink borders of generated plates, copy video frames used as portraits.  (earlier sessions' layers were lost; see git history for new lineage)"""
import cv2
CROP = {'camp': 40, 'refuge': 26, 'truck': 26, 'doctor': 26, 'map': 0, 'pov': 0, 'ceiling': 0, 'rig': 0, 'notebook': 0, 'drillbit': 0}
for k, c in CROP.items():
    im = cv2.imread(f'assets/raw/p4_{k}.jpg')
    if c: im = im[c:-c, c:-c]
    cv2.imwrite(f'assets/layers/p4_{k}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 94])
for k in ('urzua', 'sepulveda', 'gomez', 'tray'):
    cv2.imwrite(f'assets/layers/p4_{k}.jpg', cv2.imread(f'assets/frames/fr_{k}.jpg'), [cv2.IMWRITE_JPEG_QUALITY, 95])
# soften the (AI-garbled) note text: it is never read in the story, it is a cliffhanger
import numpy as np
im = cv2.imread('assets/layers/p4_drillbit.jpg'); H_, W_ = im.shape[:2]
m = np.zeros((H_, W_), np.float32); cv2.ellipse(m, (775, 215), (95, 110), -8, 0, 360, 1.0, -1); m = cv2.GaussianBlur(m, (0, 0), 6)[..., None]
bl = cv2.GaussianBlur(im, (0, 0), 7).astype(np.float32)
cv2.imwrite('assets/layers/p4_drillbit.jpg', (im * (1 - m) + bl * m).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 94])
# ---- Part 5 plates
for k, c in {'pull': 0, 'note': 0, 'pinera': 26, 'joy': 0, 'nation': 0, 'alive': 0, 'engineers': 0}.items():
    im = cv2.imread(f'assets/raw/p5_{k}.jpg')
    if c: im = im[c:-c, c:-c]
    cv2.imwrite(f'assets/layers/p5_{k}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 94])
