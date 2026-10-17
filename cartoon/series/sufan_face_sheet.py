import sys, os, math, numpy as np, cv2
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import sufan_rig as S
from rigkit.rig import Rig
from rigkit.face import VISEMES
D=math.radians; rig=Rig(S.build())
def mv(**k):
    m=dict(VISEMES['rest']); m.update(k); return m
EXPR={
 'neutral':{}, 'blink':dict(blinkL=1,blinkR=1), 'wink':dict(blinkL=1,mouth=VISEMES['smile']),
 'laugh ^_^':dict(mouth=VISEMES['laugh'],arc=1.0,browL=(.7,0),browR=(.7,0)),
 'happy':dict(mouth=VISEMES['grin'],browL=(.5,0),browR=(.5,0),squint=.25),
 'laugh':dict(mouth=VISEMES['laugh'],squint=.6,browL=(.7,0),browR=(.7,0)),
 'sad':dict(mouth=VISEMES['sad'],browL=(-.1,-.9),browR=(-.1,-.9),look=(0,.6),lidtilt=-.2),
 'worried':dict(mouth=mv(open=.15,wide=.4,smile=-.45),browL=(.3,-.9),browR=(.3,-.9),look=(.5,.2)),
 'angry/stubborn':dict(mouth=mv(open=0,wide=.5,smile=-.5),browL=(-.2,.9),browR=(-.2,.9),squint=.25,lidtilt=.35),
 'surprised':dict(mouth=VISEMES['gasp'],browL=(1,0),browR=(1,0),pupil=.8),
 'thinking':dict(mouth=mv(open=0,wide=.2,smile=-.1),browL=(.8,.3),browR=(-.1,.1),look=(-.8,-.8)),
 'touched':dict(mouth=mv(open=.08,wide=.35,smile=.55),browL=(.4,-.7),browR=(.4,-.7),look=(0,.2),squint=.2),
 'sleepy':dict(mouth=mv(open=.1,wide=.3,smile=0),squint=.65,browL=(-.2,0),browR=(-.2,0)),
}
tiles=[]
def tile(face,label):
    w,h=320,340; cv=np.ones((h,w,3),np.float32)*np.array([0.93,0.97,0.99],np.float32)
    rig.draw(cv,{},cam=(0.72,w/2,497),dyn=S.face_dyn(face),only=['head','earL','earR','hat','eyeL','eyeR','mouth','browL','browR','torso'])
    cv=(np.clip(cv,0,1)*255).astype(np.uint8); cv2.putText(cv,label,(8,h-10),cv2.FONT_HERSHEY_SIMPLEX,.6,(60,60,60),1,cv2.LINE_AA); return cv
for k,v in EXPR.items(): tiles.append(tile(v,k))
for k,v in VISEMES.items():
    if k in ('smile','grin','laugh','sad','gasp','rest'): continue
    tiles.append(tile(dict(mouth=v),'viseme '+k))
while len(tiles)%6: tiles.append(np.full_like(tiles[0],240))
rows=[np.hstack(tiles[i:i+6]) for i in range(0,len(tiles),6)]
out=sys.argv[1] if len(sys.argv)>1 else os.path.join(HERE,'sufan_face_sheet.png'); cv2.imwrite(out,np.vstack(rows)); print(out,len(tiles))
