import cv2, numpy as np
rgba=cv2.imread('matte_full.png',cv2.IMREAD_UNCHANGED); H,W=rgba.shape[:2]
bgr=rgba[...,:3]; alpha=rgba[...,3]/255.
hsv=cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV_FULL).astype(np.float32); hue=hsv[...,0]*360/256; sat=hsv[...,1]/255; val=hsv[...,2]/255
yy,xx=np.mgrid[0:H,0:W]; X=xx/2.0; Y=yy/2.0; dx=np.abs(X-456)
fg=alpha>0.5
names=['none','hat','head','torso','armL','armR','handL','handR','belly','legL','legR','bootL','bootR']
L=np.zeros((H,W),np.uint8); ID={n:i for i,n in enumerate(names)}
def setl(mask,n): L[mask&fg&(L==0)]=ID[n]
brown=(hue>=10)&(hue<35)&(sat>0.25)&(val<0.78)
black=(val<0.25)
setl(brown&(Y<250),'hat')
setl(brown&(Y>985)&(X<456),'bootL'); setl(brown&(Y>985)&(X>=456),'bootR')
setl(black&(Y>985)&(X<456),'bootL'); setl(black&(Y>985)&(X>=456),'bootR')
mustard=(hue>=33)&(hue<=51)&(sat>0.40)&(val>0.76)
setl(mustard&(Y<745)&(dx>150)&(X<456),'armL'); setl(mustard&(Y<745)&(dx>150)&(X>=456),'armR')
pink=((hue<28)|(hue>335))&(sat>0.15)&(val>0.8)
setl(pink&(Y>640)&(Y<790)&(dx>280)&(X<456),'handL'); setl(pink&(Y>640)&(Y<790)&(dx>280)&(X>=456),'handR')
setl(pink&(Y>940)&(Y<1000)&(X<456),'legL'); setl(pink&(Y>940)&(Y<1000)&(X>=456),'legR')
vestcol=(hue>=36)&(hue<=75)&(sat>0.35)
wool=(sat<0.42)&(val>0.78)
setl((Y<600)&~vestcol&(Y>40),'head')
setl(wool&(Y>770)&(Y<980),'belly')
setl(vestcol&(Y>480)&(Y<870)&(dx<290),'torso')
# propagate to unlabeled fg pixels
lab0=(L>0)
dist,idx=cv2.distanceTransformWithLabels((~lab0).astype(np.uint8),cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
ys,xs=np.where(lab0); lut=np.zeros(idx.max()+1,np.uint8)
# label ids map to pixel position of zero pixels: build lookup
zy,zx=np.where(lab0==0)  # not used
pix=np.zeros((idx.max()+1,),np.int64)
flat=np.flatnonzero(lab0.ravel()); 
# distanceTransformWithLabels labels zero pixels in raster order starting at 1
lut=np.zeros(idx.max()+2,np.uint8); lut[1:1+len(flat)]=L.ravel()[flat]
Lp=lut[idx]
Lf=np.where(fg,np.where(L>0,L,Lp),0).astype(np.uint8)
np.save('labels.npy',Lf)
cols={'none':(0,0,0),'hat':(60,90,160),'head':(250,230,150),'torso':(80,170,90),'armL':(40,200,230),'armR':(40,140,255),'handL':(255,120,200),'handR':(200,60,255),'belly':(240,240,240),'legL':(255,200,100),'legR':(255,120,60),'bootL':(110,60,40),'bootR':(60,30,20)}
ov=np.zeros((H,W,3),np.uint8)+30
for n,i in ID.items(): ov[Lf==i]=cols[n][::-1] if False else cols[n]
mix=(0.55*ov+0.45*bgr).astype(np.uint8); mix[~fg]=(255,0,255)
cv2.imwrite('labels_prev1.jpg',cv2.resize(mix,(W//2,H//2),interpolation=cv2.INTER_AREA))
for n,i in ID.items(): print(n,(Lf==i).sum())
