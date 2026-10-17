import sys, os, math, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sufan_rig_side as S, sufan_walk as W
from rigkit.rig import Rig
rig = Rig(S.build())
W.BEND = int(sys.argv[2]) if len(sys.argv) > 2 else 1
w = W.make(rig, +1, 0.0, 120.0, 0.3, 4.0)
print('steps', w.N, 't_end', round(w.t_end, 2), 'speed', round(w.v0, 1))
T = [0.9, 1.15, 1.4, 1.65, 1.9, 2.15, 2.4, 2.65]; tiles = []
for t in T:
    rx, pose = w.state(t); cv = np.ones((620, 420, 3), np.float32) * np.array([.93, .97, .99], np.float32)
    rig.draw(cv, pose, cam=(0.9, 210 - rx * 0.9, 570), dyn=S.face_dyn({'mouth': __import__('rigkit.face', fromlist=['x']).VISEMES['smile']}), root={'x': rx})
    tiles.append((np.clip(cv, 0, 1) * 255).astype(np.uint8))
cv2.imwrite(sys.argv[1], np.vstack([np.hstack(tiles[:4]), np.hstack(tiles[4:])]))
# foot slip: ankle world x while planted
mx = 0
for nm in 'LR':
    last = None
    for t in np.arange(0.3, w.t_end, 1 / 60):
        x, y, rot, st, _ = w.foot(nm, t); rx, pose = w.state(t)
        Wd = rig.world(pose, {'x': rx}); ax = Wd['foot' + nm][0, 2]
        if st == 'plant':
            if last is not None and abs(last - x) < 1e-6: mx = max(mx, abs(ax - x))
        last = x
print('max planted-foot ankle error (units):', round(mx, 3))
