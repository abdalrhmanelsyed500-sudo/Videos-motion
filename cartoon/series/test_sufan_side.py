import sys, os, math, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sufan_rig_side as S
from rigkit.rig import Rig
from rigkit.face import VISEMES
D=math.radians
rig=Rig(S.build())
def tile(pose,face=None,w=560,h=760,sc=1.0,ty=700,swap=None,zov=None):
    cv=np.ones((h,w,3),np.float32)*np.array([0.93,0.97,0.99],np.float32)
    rig.draw(cv,pose,cam=(sc,w/2,ty),dyn=S.face_dyn(face),zov=zov)
    return cv
P=[({},{}),
 ({'armR_up':{'rot':D(-40)},'armR_lo':{'rot':D(-20)},'armL_up':{'rot':D(30)},'legR_up':{'rot':D(-25)},'legL_up':{'rot':D(25)},'legR_lo':{'rot':D(20)}},{'mouth':VISEMES['grin']}),
 ({'armR_up':{'rot':D(-100)},'armR_lo':{'rot':D(-30)},'head':{'rot':D(-12)},'hat':{'rot':D(8)},'earR':{'rot':D(25)}},{'mouth':VISEMES['laugh'],'arc':1.0}),
 ({'spine':{'rot':D(-8)},'head':{'rot':D(10)},'armR_up':{'rot':D(60)}},{'mouth':VISEMES['O'],'blinkR':1}),
 ({'legR_up':{'rot':D(30)},'legR_lo':{'rot':D(40)},'footR':{'rot':D(-20)},'armL_up':{'rot':D(-80)}},{'mouth':VISEMES['sad'],'browR':(-.4,-.8),'look':(-.3,.5)}),
 ({'armR_up':{'rot':D(-150)},'armL_up':{'rot':D(-140)},'armR_lo':{'rot':D(-10)}},{'mouth':VISEMES['A'],'squint':.5,'browR':(.7,0),'look':(.8,-.3)})]
Z1={'armUpR':56,'armLoR':56,'handR':57}
Z2={'armUpR':56,'armLoR':56,'handR':57,'armUpL':56,'armLoL':56,'handL':57}
row=np.hstack([tile(p,f,zov=Z1 if i==2 else None) for i,(p,f) in enumerate(P[:3])]); row2=np.hstack([tile(p,f,zov=Z2 if i==2 else None) for i,(p,f) in enumerate(P[3:])])
cv2.imwrite(sys.argv[1],(np.clip(np.vstack([row,row2]),0,1)*255).astype(np.uint8)); print('ok')
