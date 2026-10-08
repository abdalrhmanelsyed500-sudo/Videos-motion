"""Part 4 assets: trim the white ink borders of generated plates, copy video frames used as portraits.  (earlier sessions' layers were lost; see git history for new lineage)"""
import cv2
CROP = {'camp': 40, 'refuge': 26, 'truck': 26, 'doctor': 26, 'map': 0, 'pov': 0, 'ceiling': 0, 'rig': 0, 'notebook': 0, 'drillbit': 0}
for k, c in CROP.items():
    im = cv2.imread(f'assets/raw/p4_{k}.jpg')
    if c: im = im[c:-c, c:-c]
    cv2.imwrite(f'assets/layers/p4_{k}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 94])
for k in ('urzua', 'sepulveda', 'gomez', 'tray'):
    cv2.imwrite(f'assets/layers/p4_{k}.jpg', cv2.imread(f'assets/frames/fr_{k}.jpg'), [cv2.IMWRITE_JPEG_QUALITY, 95])
