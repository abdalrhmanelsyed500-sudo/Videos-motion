"""KEYFRAME METHOD (v8): the AI model paints each pose of the SAME character (reference-locked) on flat grey; this keys the grey out into clean RGBA layers (assets/layers/mx_*.png).
bg = plane fit per channel on the border band; bg-like pixels connected to the border are removed (inner highlights stay); edge colours de-contaminated from the grey."""
import cv2, numpy as np, sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
NAMES = {'walk_A': 'mx_walk34', 'walk_B': 'mx_walk_B', 'walk_P': 'mx_walk_P', 'walk_P2': 'mx_walk_P2', 'look': 'mx_look34', 'idle': 'mx_idle34', 'bust_worried': 'mx_bust_worried', 'bust_shock': 'mx_bust_shock'}


def key(img, thr=17.0, enc=(140, 8.0, 5.0, 17.0)):
    h, w = img.shape[:2]; f = img.astype(np.float32)
    ys, xs = np.mgrid[0:h, 0:w]; band = np.zeros((h, w), bool); band[:12] = 1; band[:, -12:] = 1
    band[:, :12] = 1; band[-12:] = 1
    A = np.stack([xs[band], ys[band], np.ones(band.sum())], 1).astype(np.float32)
    bg = np.zeros_like(f)
    for c in range(3):
        v = f[..., c][band]; keep = np.abs(v - np.median(v)) < 14      # ignore the body where it touches the border
        co, *_ = np.linalg.lstsq(A[keep], v[keep], rcond=None); bg[..., c] = co[0] * xs + co[1] * ys + co[2]
    d = np.sqrt(((f - bg) ** 2).sum(2))
    d = cv2.GaussianBlur(d, (0, 0), 0.8)
    bgl = (d < thr).astype(np.uint8)
    n, lab = cv2.connectedComponents(bgl, connectivity=4)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    areas = np.bincount(lab.ravel()); g = f.mean(2); big_bg = []
    for i in range(1, n):
        if areas[i] > enc[0] and i not in border:
            m = lab == i
            if bgl[m][0] and d[m].mean() < enc[1] and g[m].std() < enc[2] and d[m].max() < enc[3]: big_bg.append(i)
    isbg = (np.isin(lab, list(border)) | np.isin(lab, big_bg)) & (bgl > 0)
    fg = (~isbg).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg, connectivity=8)
    big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); fg = (lab == big).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    # fill holes
    inv = 1 - fg; n, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    small = [i for i in range(1, n) if st2[i, cv2.CC_STAT_AREA] < 140]; fg = np.where(np.isin(lab2, small), 1, fg).astype(np.uint8)
    a = cv2.erode(fg, np.ones((3, 3), np.uint8)).astype(np.float32)
    a = cv2.GaussianBlur(a, (0, 0), 1.0)
    a = np.clip((a - 0.25) / 0.6, 0, 1)
    ac = np.maximum(a, 0.04)[..., None]
    col = np.clip((f - (1 - a)[..., None] * bg) / ac, 0, 255)
    edge = (a > 0) & (a < 0.98)
    # replace edge colours by nearest inner colours (kills the grey halo)
    inner = (a >= 0.98).astype(np.uint8); dist, idx = cv2.distanceTransformWithLabels(1 - inner, cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
    return np.dstack([col, a * 255]).astype(np.uint8), inner, dist


if __name__ == '__main__':
    for nm, src in NAMES.items():
        img = cv2.imread(f'assets/raw/{src}.jpg'); rgba, inner, dist = key(img, enc=(60, 11.0, 6.0, 20.0) if nm == 'walk_P2' else (140, 8.0, 5.0, 17.0))
        # inpaint halo: edge pixels take colour from the blurred inner colours
        a = rgba[..., 3:4].astype(np.float32) / 255; c = rgba[..., :3].astype(np.float32)
        m = (inner > 0)[..., None].astype(np.float32)
        num = cv2.GaussianBlur(c * m, (0, 0), 3); den = cv2.GaussianBlur(m[..., 0], (0, 0), 3)[..., None] + 1e-4
        fill = num / den; edge = ((a > 0) & (a < 0.98)).astype(np.float32)
        c = c * (1 - 0.7 * edge) + fill * 0.7 * edge
        rgba[..., :3] = np.clip(c, 0, 255).astype(np.uint8)
        ys, xs = np.where(rgba[..., 3] > 10); print(nm, img.shape, 'bbox', xs.min(), ys.min(), xs.max(), ys.max())
        cv2.imwrite(f'assets/layers/mx_{nm}.png', rgba)
