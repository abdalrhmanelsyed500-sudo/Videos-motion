import sys, os, math, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sufan_rig as S
from rigkit.rig import Rig
from rigkit.face import VISEMES
D=math.radians
rig=Rig(S.build())
def tile(pose,face=None,root=None,w=640,h=760,sc=1.0,ty=700,swap=None):
    cv=np.ones((h,w,3),np.float32)*np.array([0.93,0.97,0.99],np.float32)
    rig.draw(cv,pose,cam=(sc,w/2,ty),dyn=S.face_dyn(face),root=root)
    return cv
P=[]
P.append(({},{}))
P.append(({'armL_up':{'rot':D(135)},'armL_lo':{'rot':D(25)},'armR_up':{'rot':D(-40)},'armR_lo':{'rot':D(-10)}},{'mouth':VISEMES['grin']}))
P.append(({'head':{'rot':D(15)},'hat':{'rot':D(-8)},'earL':{'rot':D(22)},'earR':{'rot':D(-8)}},{'mouth':VISEMES['smile'],'look':(.8,-.3)}))
P.append(({'spine':{'rot':D(10)},'head':{'rot':D(-8)},'armR_up':{'rot':D(-70)}},{'mouth':VISEMES['O'],'blinkL':1,'blinkR':1}))
P.append(({'legL_up':{'rot':D(30)},'legL_lo':{'rot':D(-40)},'footL':{'rot':D(25)}},{'mouth':VISEMES['sad'],'browL':(-.4,-.8),'browR':(-.4,-.8),'look':(-.3,.5)}))
P.append(({'armL_up':{'rot':D(150)},'armR_up':{'rot':D(-150)},'armL_lo':{'rot':D(-20)},'armR_lo':{'rot':D(20)}},{'mouth':VISEMES['laugh'],'squint':.7,'browL':(.7,0),'browR':(.7,0)}))
row=np.hstack([tile(p,f) for p,f in P[:3]]); row2=np.hstack([tile(p,f) for p,f in P[3:]])
img=np.vstack([row,row2]); cv2.imwrite(sys.argv[1],(np.clip(img,0,1)*255).astype(np.uint8))
print('ok',[v for v in rig.violations(P[5][0])] if hasattr(rig,'violations') else '')
