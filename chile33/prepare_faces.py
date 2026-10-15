"""expression heads (AI edits of the Mauro head, same framing) -> aligned RGBA layers ph_<expr>.png (440 px wide)"""
import cv2, numpy as np
from scipy import ndimage as ndi
names = ['neutral', 'blink', 'worried', 'tired', 'determined', 'shocked', 'smile']
ims = {n: cv2.resize(cv2.imread(f'assets/raw/p_face_{n}.jpg'), (440, 599), interpolation=cv2.INTER_AREA) for n in names}
ref = cv2.cvtColor(ims['neutral'], cv2.COLOR_BGR2GRAY).astype(np.float32)[:200]
for n in names:
    im = ims[n]; g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)[:200]
    (dx, dy), r = cv2.phaseCorrelate(ref, g); print(n, round(dx, 2), round(dy, 2), round(r, 2))
    if n != 'neutral': im = cv2.warpAffine(im, np.float32([[1, 0, -dx], [0, 1, -dy]]), (440, 599), borderMode=cv2.BORDER_REPLICATE)
    bg = np.median(np.vstack([im[:12].reshape(-1, 3), im[:, :8].reshape(-1, 3)]), 0).astype(np.float32)
    d = np.abs(im.astype(np.float32) - bg).max(2); m = d > 24; m = ndi.binary_closing(m, iterations=2); m = ndi.binary_fill_holes(m)
    lab, k = ndi.label(m); sz = ndi.sum(m, lab, range(1, k + 1)); m = lab == (1 + int(np.argmax(sz))); m = ndi.binary_erosion(m, iterations=1)
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.9)
    out = np.dstack([im, (a * 255)[..., None]]).astype(np.uint8); cv2.imwrite(f'assets/layers/ph_{n}.png', out)
    ck = np.indices(m.shape).sum(0) // 16 % 2 * 40 + 100; ims[n] = (im * a[..., None] + ck[..., None] * (1 - a[..., None])).astype(np.uint8)
cv2.imwrite('build/faces_b.jpg', np.hstack([cv2.resize(ims[n], (293, 399)) for n in names]))

