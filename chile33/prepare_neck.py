"""Neck + upper-chest skin patch that sits BEHIND the front torso's V-neck (the AI torso has an empty hole there, so the head floated).
Colour is sampled from the neck of ph_neutral so it matches the face.  Output: assets/layers/pf_neck.png (227x110, layer y0 = torso y -30)."""
import cv2, numpy as np
h = cv2.imread('assets/layers/ph_neutral.png', -1)
H, W = h.shape[:2]
reg = h[int(H*0.50):int(H*0.58), int(W*0.26):int(W*0.36)]
m = reg[:, :, 3] > 250
skin = reg[:, :, :3][m].reshape(-1, 3).mean(0)
print('skin BGR', skin)
tw, OFF, HH = 227, 30, 110
poly = np.array([(76, -30), (152, -30), (156, 22), (113, 70), (72, 22)], np.float32)
poly[:, 1] += OFF
mask = np.zeros((HH, tw), np.uint8); cv2.fillPoly(mask, [poly.astype(np.int32)], 255)
mask = cv2.GaussianBlur(mask, (0, 0), 1.6)
yy, xx = np.mgrid[0:HH, 0:tw].astype(np.float32)
shade = np.clip(1.0 - (yy - OFF) / 80.0 * 0.40, 0.55, 1.0)           # darker towards the collar
side = 1.0 - 0.22 * np.clip(np.abs(xx - 113.5) / 40.0, 0, 1) ** 2        # round the neck: darker at the sides
under = 1.0 - 0.28 * np.exp(-((yy - (OFF - 6)) / 14.0) ** 2)           # chin shadow just under the head
rng = np.random.RandomState(4); n = cv2.GaussianBlur(rng.randn(HH, tw).astype(np.float32), (0, 0), 1.3) * 0.06
f = (shade * side * under + n)[:, :, None]
col = np.clip(skin[None, None, :] * f * 0.85, 0, 255)
out = np.dstack([col, mask]).astype(np.uint8)
cv2.imwrite('assets/layers/pf_neck.png', out)
bg = np.full((HH, tw, 3), 90, np.float32); a = out[:, :, 3:] / 255.
cv2.imwrite('build/neck_view1.png', cv2.resize((out[:, :, :3] * a + bg * (1 - a)).astype(np.uint8), None, fx=3, fy=3))
