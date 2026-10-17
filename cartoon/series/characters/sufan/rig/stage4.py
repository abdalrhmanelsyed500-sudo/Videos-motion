"""stage4: clean the cut parts (remove hairline fragments / sleeve remnants, round the dome, shape the shoulders) -> parts_clean/"""
import cv2, numpy as np, json, os, shutil
bb = json.load(open('parts/bbox.json')); os.makedirs('parts_clean', exist_ok=True)
def ell(d): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (d, d))
def recon(seed, mask, n):
    k = ell(3); cur = seed.copy()
    for _ in range(n): cur = cv2.dilate(cur, k) & mask
    return cur
def clean(name, open_d, edit=None, grow=2):
    im = cv2.imread(f'parts/{name}.png', cv2.IMREAD_UNCHANGED); a = im[..., 3]
    B = (a > 128).astype(np.uint8)
    op = cv2.morphologyEx(B, cv2.MORPH_OPEN, ell(open_d)) if open_d else B
    # reconstruct back to the original outline (restores rounded features lost by the opening) but only near kept pixels
    op = recon(op, B, open_d // 2 + 2) if open_d else B
    if edit: op = edit(op, im, bb[name])
    if name.startswith('ear'):
        lum = im[..., :3].astype(np.int32).sum(2); op = op & (lum > 330).astype(np.uint8)
        op = cv2.morphologyEx(op, cv2.MORPH_OPEN, ell(5))
    n, lab, st, _ = cv2.connectedComponentsWithStats(op, connectivity=8)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < 1500: op[lab == i] = 0
    keep = cv2.dilate(op, ell(2 * grow + 1)).astype(np.float32)
    keep = cv2.GaussianBlur(keep, (0, 0), 0.8)
    im[..., 3] = np.clip(a.astype(np.float32) * keep, 0, 255).astype(np.uint8)
    # kill colour under zero alpha
    im[im[..., 3] == 0, :3] = 0
    cv2.imwrite(f'parts_clean/{name}.png', im); return im
def dome(op, im, b):
    H, W = op.shape; x0, y0 = b[0], b[1]
    yy, xx = np.mgrid[0:H, 0:W]; X = xx + x0; Y = yy + y0
    cy = 545; inside = ((X - 912) / 292.0) ** 2 + ((Y - cy) / 150.0) ** 2 <= 1
    out = op.copy(); out[(Y < cy) & ~inside] = 0; return out
def shoulder(op, im, b):
    H, W = op.shape; x0, y0 = b[0], b[1]
    yy, xx = np.mgrid[0:H, 0:W]; X = xx + x0; Y = yy + y0; dx = np.abs(X - 912.0)
    ytop = np.interp(dx, [0, 200, 330, 400, 460], [960, 960, 1022, 1062, 1090])
    out = op.copy(); out[Y < ytop] = 0; return out
def torso_edit(op, im, b):
    # remove sleeve remnants: only keep what survives a large opening (cuff rings / thin sleeve lines are thinner), then reconstruct
    big = cv2.morphologyEx(op, cv2.MORPH_OPEN, ell(45)); big = recon(big, op, 20)
    return shoulder(big, im, b)
def head_edit(op, im, b):
    op = dome(op, im, b); H, W = op.shape; x0, y0 = b[0], b[1]
    yy, xx = np.mgrid[0:H, 0:W]; X = xx + x0; Y = yy + y0
    Z = (np.abs(X - 912) > 255) & (Y > 640) & (Y < 1010)
    sm = (cv2.GaussianBlur(op.astype(np.float32), (0, 0), 12) > 0.5).astype(np.uint8)
    out = np.where(Z, sm, op).astype(np.uint8)
    Z2 = (np.abs(X - 912) > 270) & (Y > 700) & (Y < 870)
    sm2 = (cv2.GaussianBlur(out.astype(np.float32), (0, 0), 22) > 0.5).astype(np.uint8)
    out = np.where(Z2, sm2, out).astype(np.uint8)
    bgr = im[..., :3].astype(np.int32)
    pink = ((bgr[..., 2] - bgr[..., 1]) > 62) & (np.abs(X - 912) > 290)
    pink = cv2.dilate(pink.astype(np.uint8), ell(7)) > 0
    out[pink] = 0
    return out
def hat_edit(op, im, b):
    H, W = op.shape; x0, y0 = b[0], b[1]
    yy, xx = np.mgrid[0:H, 0:W]; Y = yy + y0
    cl = cv2.morphologyEx(op, cv2.MORPH_CLOSE, ell(101))
    add = (cl > 0) & (op == 0) & (Y > 420)
    rgb = im[..., :3].copy()
    fill = cv2.inpaint(rgb, add.astype(np.uint8) * 255, 7, cv2.INPAINT_TELEA)
    im[..., :3] = np.where(add[..., None], fill, rgb); im[..., 3] = np.where(add, 255, im[..., 3])
    return np.where(add, 1, op).astype(np.uint8)
def belly_edit(op, im, b):
    H, W = op.shape; x0, y0 = b[0], b[1]
    r0 = 1650 - y0; r1 = 1500 - y0
    for r in range(r1, r0):                      # extrude row 1650 upward (clean vertical sides, flat shading)
        im[r] = im[r0]; op[r] = op[r0]
    op[:r1] = 0
    return op
def arm_edit(op, im, b):
    H, W = op.shape; x0, y0 = b[0], b[1]
    yy, xx = np.mgrid[0:H, 0:W]; X = xx + x0; Y = yy + y0; dx = np.abs(X - 912.0)
    ytop = np.interp(dx, [0, 200, 330, 400, 460], [960, 960, 1022, 1062, 1090]) - 6
    out = op.copy(); out[Y < ytop] = 0; return out
clean('head', 31, head_edit)
clean('torso', 0, torso_edit)
clean('hat', 13); clean('belly', 13, belly_edit)
def ear_edit_factory(mirror):
    def f(op, im, b):
        o = op[:, ::-1].copy() if mirror else op.copy(); H, W = o.shape
        yy, xx = np.mgrid[0:H, 0:W]
        top = np.interp(xx, [0, 160, 300, 372, 460], [200, 128, 102, 92, 92]); o[yy < top] = 0
        o[(xx > 255) & (yy > 375 - (xx - 255) * 0.36)] = 0
        return (o[:, ::-1] if mirror else o).copy()
    return f
clean('earL', 71, ear_edit_factory(False)); clean('earR', 71, ear_edit_factory(True))
def arm_cap(P, E):
    P = np.array(P, float); u = np.array(E, float) - P; u /= np.linalg.norm(u)
    def f(op, im, b):
        op = arm_edit(op, im, b); H, W = op.shape; x0, y0 = b[0], b[1]
        yy, xx = np.mgrid[0:H, 0:W]; X = xx + x0 - P[0]; Y = yy + y0 - P[1]
        proj = X * u[0] + Y * u[1]; dist = np.hypot(X, Y)
        out = op.copy(); out[(proj < 0) & (dist > 85)] = 0; return out
    return f
clean('armUpL', 7, arm_cap((600, 1040), (425, 1217))); clean('armUpR', 7, arm_cap((1224, 1040), (1398, 1219)))
clean('armLoL', 7); clean('armLoR', 7); clean('handL', 0); clean('handR', 0)
for n in ('legL', 'legR', 'bootL', 'bootR'):
    shutil.copy(f'parts/{n}.png', f'parts_clean/{n}.png')
print('done')
