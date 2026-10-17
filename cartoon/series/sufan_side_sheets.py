"""Sheets for the Sufan SIDE rig: bones overlay, pose gallery, face sheet, random-pose stress test (limit violations)."""
import sys, os, math, numpy as np, cv2, random
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import sufan_rig_side as S
from rigkit.rig import Rig
from rigkit.face import VISEMES
D=math.radians; rig=Rig(S.build()); BG=np.array([0.93,0.97,0.99],np.float32)
HI={'armUpR':56,'armLoR':56,'handR':57}; HI2={**HI,'armUpL':56,'armLoL':56,'handL':57}; HI3={k:v+6 for k,v in HI2.items()}
def u8(c): return (np.clip(c,0,1)*255).astype(np.uint8)
def tile(pose,face=None,zov=None,w=560,h=760,sc=1.0,root=None):
    cv=np.ones((h,w,3),np.float32)*BG; rig.draw(cv,pose,cam=(sc,w/2,h-60),dyn=S.face_dyn(face),zov=zov,root=root); return cv
def label(img,t): cv2.putText(img,t,(12,28),cv2.FONT_HERSHEY_SIMPLEX,.7,(70,70,70),2,cv2.LINE_AA); return img
def bones_sheet(path):
    sc=1.2; w,h=900,800; img=u8(tile({},w=w,h=h,sc=sc)); W=rig.world({}); C=np.array([[sc,0,w/2],[0,sc,h-60],[0,0,1]])
    pt=lambda n: (C@np.array([*W[n][:2,2],1]))[:2]
    for b in rig.bones:
        if b['parent']: cv2.line(img,tuple(int(v) for v in pt(b['parent'])),tuple(int(v) for v in pt(b['name'])),(40,40,230),2,cv2.LINE_AA)
    for b in rig.bones:
        n=b['name']; p=pt(n); cv2.circle(img,(int(p[0]),int(p[1])),6,(30,30,200),-1,cv2.LINE_AA); cv2.circle(img,(int(p[0]),int(p[1])),7,(255,255,255),1,cv2.LINE_AA)
        side=-1 if n in('armL_up','armL_lo','handL','legL_up','legL_lo','footL','hips','spine','root') else 1
        cv2.putText(img,n,(int(p[0])+side*12-(0 if side>0 else 8*len(n)),int(p[1])+4),cv2.FONT_HERSHEY_SIMPLEX,.45,(20,20,140),1,cv2.LINE_AA)
    cv2.imwrite(path,label(img,'Sufan SIDE rig - 18 bones at rest (L = far limb, R = near limb, facing right)'))
def poses_sheet(path):
    A=lambda **k:{n:{'rot':D(v)} for n,v in k.items()}
    P=[('rest',{},{},None),
       ('wave (near arm)',A(armR_up=-65,armR_lo=-50,head=6),{'mouth':VISEMES['grin']},HI),
       ('head tilt + ear',A(head=-12,hat=8,earR=25),{'mouth':VISEMES['smile'],'look':(.8,-.3)},None),
       ('blink + lean back',A(spine=-8,head=10,armR_up=60),{'mouth':VISEMES['O'],'blinkR':1},None),
       ('step',A(legR_up=-25,legR_lo=30,footR=-10,legL_up=25,legL_lo=5,hips=3),{'mouth':VISEMES['smile']},None),
       ('cheer (both arms)',A(armR_up=-168,armL_up=-160,armR_lo=-5,armL_lo=-5),{'mouth':VISEMES['laugh'],'squint':.5,'arc':0},HI3),
       ('point forward',A(armR_up=-85,armR_lo=-5,head=-6),{'mouth':VISEMES['E'],'look':(1,0)},HI),
       ('laugh ^_^',A(spine=-6,head=8,earR=-15),{'mouth':VISEMES['laugh'],'arc':1.0},None)]
    T=[label(u8(tile(p,f,zov=z)),n) for n,p,f,z in P]
    cv2.imwrite(path,np.vstack([np.hstack(T[:4]),np.hstack(T[4:])]))
def mv(**k): m=dict(VISEMES['rest']); m.update(k); return m
EXPR={'neutral':{},'blink':dict(blinkR=1),'happy':dict(mouth=VISEMES['grin'],browR=(.5,0),squint=.25),
 'laugh ^_^':dict(mouth=VISEMES['laugh'],arc=1.0,browR=(.7,0)),'sad':dict(mouth=VISEMES['sad'],browR=(-.1,-.9),look=(0,.6),lidtilt=-.2),
 'worried':dict(mouth=mv(open=.15,wide=.4,smile=-.45),browR=(.3,-.9),look=(.5,.2)),'angry/stubborn':dict(mouth=mv(open=0,wide=.5,smile=-.5),browR=(-.2,.9),squint=.25,lidtilt=.35),
 'surprised':dict(mouth=VISEMES['gasp'],browR=(1,0),pupil=.8),'thinking':dict(mouth=mv(open=0,wide=.2,smile=-.1),browR=(.8,.3),look=(-.8,-.8)),
 'touched':dict(mouth=mv(open=.08,wide=.35,smile=.55),browR=(.4,-.7),look=(0,.2),squint=.2),'sleepy':dict(mouth=mv(open=.1,wide=.3,smile=0),squint=.65,browR=(-.2,0))}
def face_sheet(path):
    T=[]
    def ft(face,lab):
        w,h=360,380; sc=1.15; cv=np.ones((h,w,3),np.float32)*BG
        rig.draw(cv,{},cam=(sc,w/2-8,200+445*sc),dyn=S.face_dyn(face),only=['head','earR','hat','eyeR','mouth','browR','glasses','torso'])
        cv=u8(cv); cv2.putText(cv,lab,(8,h-10),cv2.FONT_HERSHEY_SIMPLEX,.6,(60,60,60),1,cv2.LINE_AA); return cv
    for k,v in EXPR.items(): T.append(ft(v,k))
    for k,v in VISEMES.items():
        if k in('smile','grin','laugh','sad','gasp','rest'): continue
        T.append(ft(dict(mouth=v),'viseme '+k))
    while len(T)%5: T.append(np.full_like(T[0],240))
    cv2.imwrite(path,np.vstack([np.hstack(T[i:i+5]) for i in range(0,len(T),5)]))
def random_sheet(path,n=12,seed=11):
    random.seed(seed); T=[]; viol=0
    for i in range(n):
        r=lambda a,b: D(random.uniform(a,b))
        pose={'spine':{'rot':r(-10,10)},'hips':{'rot':r(-6,6)},'head':{'rot':r(-20,20)},'hat':{'rot':r(-10,10)},'earR':{'rot':r(-30,30)},
              'armR_up':{'rot':r(-120,40)},'armR_lo':{'rot':r(-100,0)},'armL_up':{'rot':r(-120,40)},'armL_lo':{'rot':r(-100,0)},'handR':{'rot':r(-30,30)},'handL':{'rot':r(-30,30)},
              'legR_up':{'rot':r(-25,25)},'legR_lo':{'rot':r(0,60)},'legL_up':{'rot':r(-25,25)},'legL_lo':{'rot':r(0,60)},'footR':{'rot':r(-20,20)},'footL':{'rot':r(-20,20)}}
        viol+=len(rig.violations(pose)); zov=HI2 if (pose['armR_up']['rot']<-D(60)) else None
        T.append(label(u8(tile(pose,{'mouth':random.choice(list(VISEMES.values())),'look':(random.uniform(-1,1),random.uniform(-1,1))},zov=zov,w=420,h=620,sc=.8)),f'random {i+1}'))
    cv2.imwrite(path,np.vstack([np.hstack(T[i:i+4]) for i in range(0,n,4)])); return viol
if __name__=='__main__':
    o=sys.argv[1]; os.makedirs(o,exist_ok=True)
    bones_sheet(o+'/sufan_side_bones.png'); poses_sheet(o+'/sufan_side_poses.png'); face_sheet(o+'/sufan_side_faces.png'); print('limit violations in random sheet:',random_sheet(o+'/sufan_side_random.png'))
