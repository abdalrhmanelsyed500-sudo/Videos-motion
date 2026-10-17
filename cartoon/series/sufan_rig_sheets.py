"""Sheets for the Sufan front rig: bones overlay + pose gallery + random-pose stress sheet."""
import sys, os, math, numpy as np, cv2, random
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import sufan_rig as S
from rigkit.rig import Rig
from rigkit.face import VISEMES
D=math.radians; rig=Rig(S.build())
BG=np.array([0.93,0.97,0.99],np.float32)
HI={'armLoL':56,'handL':57,'armLoR':56,'handR':57}
def tile(pose,face=None,zov=None,w=640,h=760,sc=1.0,root=None):
    cv=np.ones((h,w,3),np.float32)*BG; rig.draw(cv,pose,cam=(sc,w/2,h-60),dyn=S.face_dyn(face),zov=zov,root=root); return cv
def u8(c): return (np.clip(c,0,1)*255).astype(np.uint8)
def label(img,t):
    cv2.putText(img,t,(12,28),cv2.FONT_HERSHEY_SIMPLEX,.7,(70,70,70),2,cv2.LINE_AA); return img
def bones_sheet(path):
    img=u8(tile({},w=900,h=800,sc=1.2)); W=rig.world({}); 
    C=np.array([[1.2,0,450],[0,1.2,800-72],[0,0,1]])
    for b in rig.bones:
        n=b['name']; p=(C@np.array([*W[n][:2,2],1]))[:2]
        if b['parent']:
            q=(C@np.array([*W[b['parent']][:2,2],1]))[:2]; cv2.line(img,tuple(int(v) for v in q),tuple(int(v) for v in p),(40,40,230),2,cv2.LINE_AA)
    for b in rig.bones:
        n=b['name']; p=(C@np.array([*W[n][:2,2],1]))[:2]
        cv2.circle(img,(int(p[0]),int(p[1])),6,(30,30,200),-1,cv2.LINE_AA); cv2.circle(img,(int(p[0]),int(p[1])),7,(255,255,255),1,cv2.LINE_AA)
        side=-1 if p[0]<450 else 1; 
        if n in('root','hips','spine'): side=1
        cv2.putText(img,n,(int(p[0])+side*12-(0 if side>0 else 8*len(n)),int(p[1])+4),cv2.FONT_HERSHEY_SIMPLEX,.45,(20,20,140),1,cv2.LINE_AA)
    cv2.imwrite(path,label(img,'Sufan front rig - 19 bones (red) at rest')); 
def arms(a,b,c,d): return {'armL_up':{'rot':D(a)},'armL_lo':{'rot':D(b)},'armR_up':{'rot':D(-c)},'armR_lo':{'rot':D(-d)}}
def poses_sheet(path):
    P=[('rest',{},{}),
       ('wave',{**arms(80,50,15,5),'head':{'rot':D(6)}},{'mouth':VISEMES['grin']}),
       ('head tilt + hat tip',{'head':{'rot':D(14)},'hat':{'rot':D(-8)},'earL':{'rot':D(18)},'earR':{'rot':D(-6)}},{'mouth':VISEMES['smile'],'look':(.8,-.3)}),
       ('blink + lean',{'spine':{'rot':D(8)},'head':{'rot':D(-8)},'armR_up':{'rot':D(-40)}},{'mouth':VISEMES['O'],'blinkL':1,'blinkR':1}),
       ('step (leg bend)',{'legL_up':{'rot':D(-25)},'legL_lo':{'rot':D(45)},'footL':{'rot':D(-20)},'legR_up':{'rot':D(25)},'legR_lo':{'rot':D(-25)},'hips':{'rot':D(5)}},{'mouth':VISEMES['smile']}),
       ('cheer',{**arms(80,40,80,40)},{'mouth':VISEMES['laugh'],'squint':.6}),
       ('arms out',{**arms(-5,70,-5,70)},{'mouth':VISEMES['rest'],'browL':(-.1,.5),'browR':(-.1,.5)}),
       ('point',{**arms(10,5,75,0),'head':{'rot':D(-8)}},{'mouth':VISEMES['E'],'look':(1,0)})]
    zs={'cheer':HI,'wave':HI}
    T=[label(u8(tile(p,f,zov=zs.get(n))),n) for n,p,f in P]
    cv2.imwrite(path,np.vstack([np.hstack(T[:4]),np.hstack(T[4:])]))
def random_sheet(path,n=12,seed=7):
    random.seed(seed); T=[]; viol=0
    for i in range(n):
        r=lambda a,b: D(random.uniform(a,b))
        pose={'spine':{'rot':r(-10,10)},'hips':{'rot':r(-6,6)},'head':{'rot':r(-20,20)},'hat':{'rot':r(-10,10)},'earL':{'rot':r(-20,30)},'earR':{'rot':r(-30,20)},
              'armL_up':{'rot':r(-20,120)},'armL_lo':{'rot':r(0,100)},'armR_up':{'rot':r(-120,20)},'armR_lo':{'rot':r(-100,0)},
              'handL':{'rot':r(-30,30)},'handR':{'rot':r(-30,30)},'legL_up':{'rot':r(-25,25)},'legL_lo':{'rot':r(-5,50)},'legR_up':{'rot':r(-25,25)},'legR_lo':{'rot':r(-50,5)},'footL':{'rot':r(-20,20)},'footR':{'rot':r(-20,20)}}
        viol+=len(rig.violations(pose)); 
        zov=HI if (pose['armL_up']['rot']>D(60) or pose['armR_up']['rot']<-D(60)) else None
        T.append(label(u8(tile(pose,{'mouth':random.choice(list(VISEMES.values())),'look':(random.uniform(-1,1),random.uniform(-1,1))},zov=zov,w=520,h=620,sc=.8)),f'random {i+1}'))
    cv2.imwrite(path,np.vstack([np.hstack(T[i:i+4]) for i in range(0,n,4)])); return viol
if __name__=='__main__':
    o=sys.argv[1]; os.makedirs(o,exist_ok=True)
    bones_sheet(o+'/sufan_rig_bones.png'); poses_sheet(o+'/sufan_rig_poses.png'); print('limit violations in random sheet:',random_sheet(o+'/sufan_rig_random.png'))
