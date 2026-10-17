"""side parts: cut the 2x side master into rig parts (all coords 2x px = native*2)"""
import cv2, numpy as np, json, os
rgba=cv2.imread('matte_full.png',cv2.IMREAD_UNCHANGED); H,W=rgba.shape[:2]; L=np.load('labels.npy')
bgr=rgba[...,:3].copy(); alpha=rgba[...,3].astype(np.float32)/255.
ID={n:i for i,n in enumerate(['none','hat','head','torso','arm','hand','belly','legN','legF','bootN','bootF'])}
hsv=cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV_FULL).astype(np.float32); hue=hsv[...,0]*360/256; sat=hsv[...,1]/255; val=hsv[...,2]/255
yy,xx=np.mgrid[0:H,0:W]; X=xx/2.0; Y=yy/2.0
EYE_ELL=(((X-614)/40.0)**2+((Y-311)/38.0)**2)<=1
alpha[EYE_ELL]=1.0; L[EYE_ELL]=ID['head']
# remove the white 'sticker' rim of the master (it would show around moved parts)
_fg=(alpha>0.5).astype(np.uint8); _d=cv2.distanceTransform(_fg,cv2.DIST_L2,5)
_rim=(_d<26)&(sat<0.09)&(val>0.86)&(_fg>0)
_rim=_rim&~EYE_ELL
_rim2=cv2.dilate(_rim.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))>0
_rim2=_rim2&(sat<0.16)&(val>0.82)&(_d<30)&~EYE_ELL
alpha[_rim2]=0
alpha=cv2.GaussianBlur(alpha,(0,0),0.8)*(alpha>0.02)
def E(d): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(d,d))
def lab(*n): return np.isin(L,[ID[k] for k in n])
os.makedirs('parts',exist_ok=True); BB={}
def save(name,mask,img=None,soft=None):
    img=bgr if img is None else img
    a=alpha*(mask.astype(np.float32) if soft is None else soft)
    op=cv2.morphologyEx((a>0.3).astype(np.uint8),cv2.MORPH_OPEN,E(5)); op=cv2.dilate(op,E(5))
    a=a*op
    nc_,cc_,st_,_=cv2.connectedComponentsWithStats((a>0.15).astype(np.uint8),connectivity=8)
    if nc_>2:
        keep=np.zeros(nc_,bool); mx=st_[1:,cv2.CC_STAT_AREA].max(); keep[1:]=st_[1:,cv2.CC_STAT_AREA]>=max(200,0.04*mx)
        a=a*keep[cc_]
    ys,xs=np.where(a>0.01); x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    out=np.dstack([img[y0:y1,x0:x1],(a[y0:y1,x0:x1]*255).astype(np.uint8)]); out[out[...,3]==0,:3]=0
    cv2.imwrite(f'parts/{name}.png',out); BB[name]=[int(x0),int(y0),int(x1),int(y1)]
# ---- measurements (native -> 2x)
# glasses: dark pixels in the glasses box, excluding the pupil
gbox=(X>=486)&(X<=662)&(Y>=250)&(Y<=362)
pup=((X-618)/12.0)**2+((Y-312)/18.0)**2<=1
dk=((val<0.5)&gbox&(alpha>0.5)).astype(np.uint8)
nc,cc,st,_=cv2.connectedComponentsWithStats(dk,connectivity=8)
big=1+np.argmax(st[1:,cv2.CC_STAT_AREA]); ringm=cv2.dilate((cc==big).astype(np.uint8),E(9))>0
pup=((cc>0)&(cc!=big)); pup=cv2.dilate(pup.astype(np.uint8),E(5))>0
glsoft=np.clip((0.66-val)/0.38,0,1)*(gbox&ringm&~pup)
gl=glsoft>0.5
# eye + pupil inside the lens -> removed from head
scl=(val>0.93)&(sat<0.14)&(X>=578)&(X<=644)&(Y>=278)&(Y<=342)
eyem=(scl|pup)&(alpha>0.5)
eye_rm=((((X-614)/46.0)**2+((Y-311)/44.0)**2)<=1)
glass_rm=cv2.dilate(((glsoft>0.05)&gbox).astype(np.uint8),E(17))>0
# mouth: dark red curve
mbox=(X>=652)&(X<=712)&(Y>=372)&(Y<=420)
mouth=(val<0.55)&(hue<40)&mbox
mouth_rm=cv2.dilate(mouth.astype(np.uint8),E(9))>0
# ear polygon (native) -> 2x
ear_poly=np.array([(420,252),(405,285),(385,320),(372,355),(375,385),(395,415),(420,424),(450,415),(478,390),(487,350),(488,300),(484,266),(460,255)],np.float32)*2
emask=np.zeros((H,W),np.uint8); cv2.fillPoly(emask,[ear_poly.astype(np.int32)],1)
ear_part=cv2.dilate(emask,E(15))>0; ear_core=cv2.erode(emask,E(11))>0
ring=ear_part&~ear_core
stroke=ring&(val<0.93)&(alpha>0.5); stroke=cv2.dilate(stroke.astype(np.uint8),E(5))>0
# ---- repair image under things that get cut away (inpaint with flat surroundings)
armm=lab('arm','hand')
under_arm=cv2.dilate(armm.astype(np.uint8),E(7))>0
zone=(cv2.dilate(lab('arm').astype(np.uint8),E(61))>0)&(yy<1610)&(lab('torso')|lab('arm'))
under_arm=under_arm|zone
rm_head=(eye_rm|glass_rm|mouth_rm|stroke)&lab('head')
work=bgr.copy(); work[alpha<0.5]=(233,233,233)
fix=(rm_head|under_arm).astype(np.uint8)*255
valid=((alpha>0.9)&~(fix>0)&~lab('hat')&(val>0.35)).astype(np.float32)
srcf=work.astype(np.float32); rep=np.zeros_like(srcf); done=np.zeros((H,W),bool)
for sg in (10,25,60,140):
    w=cv2.GaussianBlur(valid,(0,0),sg); num=cv2.GaussianBlur(srcf*valid[...,None],(0,0),sg)
    ok=(w>0.12)&~done
    rep[ok]=(num/np.maximum(w[...,None],1e-6))[ok]; done|=ok
rep=np.clip(rep,0,255).astype(np.uint8)
# row-wise interpolation across the removed arm (keeps the hem stripe / belly structure; no pale mush)
ua=(under_arm&~(eye_rm|glass_rm|mouth_rm|stroke)).astype(np.uint8)
rows=np.where(ua.any(1))[0]; rep2=rep.copy(); m2=np.zeros((H,W),np.float32)
for y in rows:
    xs_=np.where(ua[y])[0]
    # runs
    br=np.where(np.diff(xs_)>1)[0]; starts=np.r_[xs_[0],xs_[br+1]]; ends=np.r_[xs_[br],xs_[-1]]
    for x0,x1 in zip(starts,ends):
        if x1-x0<2: continue
        lc=work[y,max(x0-14,0):max(x0-5,1)].astype(np.float32).mean(0); rc=work[y,x1+6:x1+15].astype(np.float32).mean(0)
        t=((np.arange(x0,x1+1)-x0)/max(x1-x0,1))[:,None]
        rep2[y,x0:x1+1]=np.clip(lc*(1-t)+rc*t,0,255).astype(np.uint8); m2[y,x0:x1+1]=1
sm=cv2.GaussianBlur(rep2,(0,0),sigmaX=2.0,sigmaY=9.0)
rep=np.where(m2[...,None]>0,sm,rep).astype(np.uint8)
img_fix=np.where((fix>0)[...,None],rep,bgr)
# ---- hat
save('hat',lab('hat'))
# ---- head: head label + dome under the hat
head=lab('head').copy()
# dome fill: columns under hat
cx,cy,rx,ry=460*2,300*2,178*2,112*2
dome=((xx-cx)/rx)**2+((yy-cy)/ry)**2<=1
dome&=(yy<cy)
hat=lab('hat')
topy=np.full(W,-1)
for x in range(W):
    ys=np.where(head[:,x]&~hat[:,x])[0]
    if len(ys): topy[x]=ys.min()
img_h=img_fix.copy(); alpha_h=alpha.copy()
for x in range(W):
    t=topy[x]
    if t<0 or not dome[:,x].any(): continue
    ytop=np.where(dome[:,x])[0].min()
    if t>ytop:
        col=img_fix[min(t+10,H-1),x]; img_h[ytop:t,x]=col; alpha_h[ytop:t,x]=1; head[ytop:t,x]=True
a_bak=alpha; alpha=alpha_h
head_nogl=head&~(ear_part&~stroke&False)
# ear part = pixels in dilated polygon (original pixels incl. stroke), head = everything else incl. repaired area under ear
ear_img=bgr
save('ear',ear_part&lab('head'),img=ear_img,soft=cv2.GaussianBlur(ear_part.astype(np.float32),(0,0),1.2))
save('head',head,img=img_h)
alpha=a_bak
# glasses (separate part on top of eye)
gimg=np.zeros_like(bgr); gimg[:]=(3,2,2)
save('glasses',gbox&ringm,img=gimg,soft=glsoft)
# ---- torso (+ extension up under the beard), sleeve area repaired
tor=lab('torso')|(armm&(Y<845))
tor_ext=tor.copy(); img_t=img_fix.copy(); alpha_t=alpha.copy()
for x in range(int(300*2),int(650*2)):
    ys=np.where(tor[:,x]&(Y[:,x]>440))[0]
    if len(ys)==0: continue
    t=ys.min(); y0=max(int(430*2),t-110)
    if t>y0:
        img_t[y0:t,x]=img_fix[min(t+14,H-1),x]; alpha_t[y0:t,x]=1; tor_ext[y0:t,x]=True
a_bak=alpha; alpha=alpha_t; save('torso',tor_ext,img=img_t); alpha=a_bak
# ---- belly (+ upward extension under the vest), tail included
bel=lab('belly')|(armm&(Y>=845))
bel_ext=bel.copy(); img_b=img_fix.copy(); alpha_b=alpha.copy()
for x in range(int(246*2),int(690*2)):
    ys=np.where(bel[:,x])[0]
    if len(ys)==0: continue
    t=ys.min(); y0=int(790*2)
    if t>y0:
        img_b[y0:t,x]=img_fix[min(t+16,H-1),x]; alpha_b[y0:t,x]=1; bel_ext[y0:t,x]=True
a_bak=alpha; alpha=alpha_b; save('belly',bel_ext,img=img_b); alpha=a_bak
# ---- arm: upper / lower (split at y=640 native, 8px overlap), hand
sl=lab('arm'); sp=int(640*2)
row=np.where(sl[sp])[0]; ecx=(row.min()+row.max())/2; er=(row.max()-row.min())/2-3
disc=((xx-ecx)**2+(yy-1280)**2)<=er**2   # round elbow: both parts carry the same disc so the joint stays closed when it bends
save('armUp',sl&((yy<sp+8)|disc)); save('armLo',sl&((yy>=sp-8)|disc)); save('hand',lab('hand'))
print('elbow disc',ecx,er)
# ---- legs: extend up (hidden under belly) and down (hidden under boot); thigh / shin split at y=985 native
for s in ('N','F'):
    lg=lab('leg'+s)&(((X>=410)&(X<=476)) if s=='N' else ((X>=484)&(X<=552)))&(Y>=955)&(Y<=1016)
    nc2,cc2,st2,_=cv2.connectedComponentsWithStats(lg.astype(np.uint8),connectivity=8)
    if nc2>2: lg=cc2==(1+np.argmax(st2[1:,cv2.CC_STAT_AREA]))
    xs_=np.where(lg.any(0))[0]; 
    img_l=bgr.copy(); alpha_l=alpha.copy(); m=lg.copy()
    for x in range(xs_.min(),xs_.max()+1):
        ys=np.where(lg[:,x])[0]
        if len(ys)==0: continue
        t,b=ys.min(),ys.max()
        img_l[int(940*2):t,x]=bgr[t+8,x]; alpha_l[int(940*2):t,x]=1; m[int(940*2):t,x]=True
        img_l[b:b+60,x]=bgr[b-8,x]; alpha_l[b:b+60,x]=1; m[b:b+60,x]=True
    a_bak=alpha; alpha=alpha_l
    ks=int(985*2)
    save('thigh'+s,m&(yy<ks+8),img=img_l); save('shin'+s,m&(yy>=ks-8),img=img_l); alpha=a_bak
    bm=lab('boot'+s); bimg=bgr.copy(); ba=alpha.copy()
    if s=='F':
        hole=(X>=481)&(X<=520)&(Y>=1040)&(Y<=1078)&~bm&lab('bootN')
        hole=cv2.dilate(hole.astype(np.uint8),E(5))>0
        br=np.median(bgr[bm&(val>0.2)&(val<0.45)],axis=0)
        bimg[hole&~bm]=br; ba[hole&~bm]=1; bm=bm|(hole&lab('bootN'))
    a_bak=alpha; alpha=ba; save('boot'+s,bm,img=bimg); alpha=a_bak
json.dump(BB,open('parts/bbox.json','w'))
# procedural-face colours
skin=np.median(img_fix[int(330*2):int(350*2),int(600*2):int(640*2)].reshape(-1,3),axis=0)[::-1]
lid=np.median(img_fix[int(300*2):int(330*2),int(572*2):int(582*2)].reshape(-1,3),axis=0)[::-1]
json.dump({'skin':[int(v) for v in skin],'lid':[int(v) for v in lid]},open('face_colors.json','w')); print(BB, skin, lid)
