import cv2, numpy as np
rgba=cv2.imread('matte_full.png',cv2.IMREAD_UNCHANGED); H,W=rgba.shape[:2]
rgba[:6]=0; rgba[-6:]=0; rgba[:,:6]=0; rgba[:,-6:]=0     # kill border junk
cv2.imwrite('matte_full.png',rgba)
bgr=rgba[...,:3]; alpha=rgba[...,3]/255.; fg=alpha>0.5
hsv=cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV_FULL).astype(np.float32); hue=hsv[...,0]*360/256; sat=hsv[...,1]/255; val=hsv[...,2]/255
yy,xx=np.mgrid[0:H,0:W]; X=xx/2.0; Y=yy/2.0
names=['none','hat','head','torso','arm','hand','belly','legN','legF','bootN','bootF']; ID={n:i for i,n in enumerate(names)}
L=np.zeros((H,W),np.uint8)
def setl(m,n): L[m&fg&(L==0)]=ID[n]
brown=(hue>=10)&(hue<35)&(sat>0.25)&(val<0.78)
setl(brown&(Y<315),'hat')
dark=(val<0.5)
bt=(brown|dark)&(Y>985)
_pm=np.zeros((H,W),np.uint8); cv2.fillPoly(_pm,[(np.array([(400,1005),(473,1005),(473,1040),(481,1042),(495,1046),(505,1054),(512,1066),(515,1080),(511,1092),(400,1096)],np.float32)*2).astype(np.int32)],1)
nearb=_pm>0; setl(bt&nearb,'bootN'); setl(bt&~nearb,'bootF')
mustard=(hue>=33)&(hue<=52)&(sat>0.40)&(val>0.74)
setl(mustard&(X>372)&(X<512)&(Y>495)&(Y<782),'arm')
pink=((hue<28)|(hue>335))&(sat>0.15)&(val>0.8)
setl(pink&(Y>768)&(Y<870)&(X>405)&(X<500),'hand')
setl(pink&(Y>955)&(Y<1012)&(X<478),'legN'); setl(pink&(Y>955)&(Y<1012)&(X>=478),'legF')
vestcol=(hue>=36)&(hue<=75)&(sat>0.35)
wool=(sat<0.42)&(val>0.78)
setl(wool&(Y<585),'head'); setl(~vestcol&(Y<470),'head')
setl(wool&(Y>835),'belly')
setl(vestcol&(Y>455)&(Y<870),'torso')
lab0=(L>0); flat=np.flatnonzero(lab0.ravel())
dist,idx=cv2.distanceTransformWithLabels((~lab0).astype(np.uint8),cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
lut=np.zeros(idx.max()+2,np.uint8); lut[1:1+len(flat)]=L.ravel()[flat]
Lf=np.where(fg,np.where(L>0,L,lut[idx]),0).astype(np.uint8); np.save('labels.npy',Lf)
cols={'none':(0,0,0),'hat':(60,90,160),'head':(250,230,150),'torso':(80,170,90),'arm':(40,200,230),'hand':(255,120,200),'belly':(240,240,240),'legN':(255,200,100),'legF':(255,120,60),'bootN':(110,60,40),'bootF':(200,150,250)}
ov=np.zeros((H,W,3),np.uint8)+30
for n,i in ID.items(): ov[Lf==i]=cols[n]
mix=(0.6*ov+0.4*bgr).astype(np.uint8); mix[~fg]=(255,0,255)
cv2.imwrite('/tmp/pv_slab.jpg',cv2.resize(mix,(W//2,H//2),interpolation=cv2.INTER_AREA))
for n,i in ID.items(): print(n,(Lf==i).sum())
