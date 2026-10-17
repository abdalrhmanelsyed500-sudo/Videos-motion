"""Hand-pose sheet: original drawn hand + 4 procedural variants, front L/R and side (near)."""
import sys, os, math, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sufan_rig as S, sufan_rig_side as SS
from rigkit.rig import Rig
rf = Rig(S.build()); rs = Rig(SS.build())
def zoom(rig, mod, bone, swap, lab, sc=2.6, w=300, h=300):
    W = rig.world({}); x, y = W[bone][0, 2], W[bone][1, 2]
    cv = np.ones((h, w, 3), np.float32) * np.array([.93, .97, .99], np.float32)
    rig.draw(cv, {}, cam=(sc, w / 2 - x * sc, h / 2 - y * sc - 20), dyn=mod.face_dyn({}), swap=swap)
    im = (np.clip(cv, 0, 1) * 255).astype(np.uint8); cv2.putText(im, lab, (8, h - 10), cv2.FONT_HERSHEY_SIMPLEX, .6, (50, 50, 50), 2, cv2.LINE_AA); return im
K = ('flat', 'fist', 'point', 'thumb')
rows = [[zoom(rf, S, 'handR', {}, 'front R: drawn (relaxed)')] + [zoom(rf, S, 'handR', {'handR': 'handR_' + k}, 'front R: ' + k) for k in K],
        [zoom(rf, S, 'handL', {}, 'front L: drawn (relaxed)')] + [zoom(rf, S, 'handL', {'handL': 'handL_' + k}, 'front L: ' + k) for k in K],
        [zoom(rs, SS, 'handR', {}, 'side: drawn (relaxed)')] + [zoom(rs, SS, 'handR', {'handR': 'handR_' + k}, 'side: ' + k) for k in K]]
cv2.imwrite(sys.argv[1], np.vstack([np.hstack(r) for r in rows])); print('ok')
