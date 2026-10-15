import cv2, numpy as np
from scipy import ndimage as ndi
# ---- side-profile expression heads -> pss_<expr>.png (512 px wide)
snames = ['neutral', 'blink', 'worried', 'tired', 'determined']
sims = {n: cv2.resize(cv2.imread(f'assets/raw/ps_head_{n}.jpg'), (512, 517), interpolation=cv2.INTER_AREA) for n in snames}
sref = cv2.cvtColor(sims['neutral'], cv2.COLOR_BGR2GRAY).astype(np.float32)
for n in snames:
    im = sims[n]; g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
    (dx, dy), r = cv2.phaseCorrelate(sref[:260], g[:260]); print('side', n, round(dx, 2), round(dy, 2), round(r, 2))
    if n != 'neutral': im = cv2.warpAffine(im, np.float32([[1, 0, -dx], [0, 1, -dy]]), (512, 517), borderMode=cv2.BORDER_REPLICATE)
    bg = np.median(np.vstack([im[:12].reshape(-1, 3), im[:, :8].reshape(-1, 3)]), 0).astype(np.float32)
    d = np.abs(im.astype(np.float32) - bg).max(2); m = ndi.binary_fill_holes(ndi.binary_closing(d > 24, iterations=2))
    lab, k = ndi.label(m); sz = ndi.sum(m, lab, range(1, k + 1)); m = ndi.binary_erosion(lab == (1 + int(np.argmax(sz))), iterations=1)
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.9)
    cv2.imwrite(f'assets/layers/pss_{n}.png', np.dstack([im, (a * 255)[..., None]]).astype(np.uint8))
