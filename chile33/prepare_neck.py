"""Neck + upper-chest skin patch that sits BEHIND the front torso's V-neck (the AI torso has an empty hole there, so the head floated).
Colour is sampled from the neck of ph_neutral so it matches the face.  Output: assets/layers/pf_neck.png (227x110, layer y0 = torso y -30)."""
import cv2, numpy as np
h = cv2.imread('assets/layers/ph_neutral.png', -1)
H, W = h.shape[:2]
reg = h[int(H*0.86):int(H*0.89), int(W*0.45):int(W*0.55)]
m = reg[:, :, 3] > 250
skin = reg[:, :, :3][m].reshape(-1, 3).mean(0)
print('skin BGR', skin)
tw, OFF, HH = 227, 80, 160
poly = np.array([(84, -24), (142, -24), (143, 6), (160, 26), (113, 70), (66, 26), (84, 6)], np.float32)
poly[:, 1] += OFF
mask = np.zeros((HH, tw), np.uint8); cv2.fillPoly(mask, [poly.astype(np.int32)], 255)
mask = cv2.GaussianBlur(mask, (0, 0), 1.6)
yy0 = np.arange(HH, dtype=np.float32)[:, None]
mask = (mask * np.clip((yy0 - (OFF - 24)) / 20.0, 0, 1)).astype(np.uint8)
yy, xx = np.mgrid[0:HH, 0:tw].astype(np.float32)
shade = np.clip(1.0 + (yy - OFF + 24) / 94.0 * 0.45, 1.0, 1.5)           # darker towards the collar
side = 1.0 - 0.22 * np.clip(np.abs(xx - 113.5) / 40.0, 0, 1) ** 2        # round the neck: darker at the sides
under = 1.0           # chin shadow just under the head
rng = np.random.RandomState(4)
def nz(sig): 
    g = cv2.GaussianBlur(rng.randn(HH, tw).astype(np.float32), (0, 0), sig); return g / (g.std() + 1e-6)
n = 0.035 * nz(0.8) + 0.05 * nz(2.5) + 0.07 * nz(7.0)
# collarbones / trapezius: soft darker diagonals from the neck base outwards, a lit sternum
cb = np.zeros((HH, tw), np.float32)
for sgn in (-1, 1):
    x0, y0 = 113 + sgn * 8, OFF + 6
    x1, y1 = 113 + sgn * 50, OFF + 24
    cv2.line(cb, (int(x0), int(y0)), (int(x1), int(y1)), 1.0, 5)
cb = cv2.GaussianBlur(cb, (0, 0), 3.5)
notch = np.exp(-(((xx - 113.5) / 7.0) ** 2 + ((yy - (OFF + 12)) / 8.0) ** 2))
chest_lit = 0.10 * np.exp(-(((xx - 100) / 26.0) ** 2 + ((yy - (OFF + 40)) / 18.0) ** 2))      # light from the left
f = (shade * side * under + n - 0.22 * cb - 0.25 * notch + chest_lit)[:, :, None]
col = np.clip(skin[None, None, :] * f, 0, 255)
# sand specks like the rest of the painted skin
sp = (rng.rand(HH, tw) > 0.995).astype(np.float32); sp = cv2.GaussianBlur(sp, (0, 0), 0.7) * 1.2
col = np.clip(col + sp[:, :, None] * np.array([40, 90, 140], np.float32), 0, 255)
out = np.dstack([col, mask]).astype(np.uint8)
cv2.imwrite('assets/layers/pf_neck.png', out)
bg = np.full((HH, tw, 3), 90, np.float32); a = out[:, :, 3:] / 255.
cv2.imwrite('build/neck_view1.png', cv2.resize((out[:, :, :3] * a + bg * (1 - a)).astype(np.uint8), None, fx=3, fy=3))
