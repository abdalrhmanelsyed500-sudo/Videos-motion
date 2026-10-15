import sys; sys.path.insert(0,'.')
import numpy as np, cv2
import pros_scenes as PS, front_rig as FR, side_rig as SR, fx
from engine import *
from up_scenes import cam
cv=np.zeros((H,W,3),np.float32)
wc=PS.WC(800,300,1.5); wc.draw(cv,'pr_dawn')
fx.hero_fx(cv, lambda c: SR.draw_side(c, 0.5, 520, 640, 0.5, 1, walk=1.0, shadow=False), 640, sun=-1.0, sun_h=0.18)
fx.hero_fx(cv, lambda c: FR.draw_front(c, 1.0, 960, 640, 0.5, face=('worried','worried',0), shadow=False), 640, sun=-1.0, sun_h=0.18)
cv2.imwrite('build/fx_b.jpg', np.clip(cv,0,255).astype(np.uint8))
