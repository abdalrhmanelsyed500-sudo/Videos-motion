import cv2, numpy as np
im=cv2.imread('master_side_2x.png'); H,W=im.shape[:2]
lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB).astype(np.float32)
bg=np.median(np.concatenate([im[:20].reshape(-1,3),im[-20:].reshape(-1,3),im[:,:20].reshape(-1,3),im[:,-20:].reshape(-1,3)]),axis=0)
bgl=cv2.cvtColor(bg.reshape(1,1,3).astype(np.uint8),cv2.COLOR_BGR2LAB).reshape(3).astype(np.float32); print('bg',bg,bgl)
d=np.sqrt(((lab-bgl)**2*np.array([0.5,1,1],np.float32)).sum(2))
a=np.clip((d-2.5)/(8.0-2.5),0,1)
bgmask=(d<4).astype(np.uint8); n,cc=cv2.connectedComponents(bgmask)
border=set(np.unique(np.concatenate([cc[0],cc[-1],cc[:,0],cc[:,-1]])))-{0}
a[np.isin(cc,list(border))&(d<4)]=0
for k in range(1,n):
    if k in border: continue
    m=cc==k
    if m.sum()>600: a[m]=0
alpha=a; bgf=bg.astype(np.float32); obs=im.astype(np.float32); aa=np.maximum(alpha[...,None],1e-3)
col=np.clip((obs-(1-alpha[...,None])*bgf)/aa,0,255); col[alpha>0.97]=obs[alpha>0.97]
cv2.imwrite('matte_full.png',np.dstack([col,alpha*255]).astype(np.uint8))
print('bbox',cv2.boundingRect((alpha>0.5).astype(np.uint8)))
pv=(col*alpha[...,None]+np.array([255,0,255],np.float32)*(1-alpha[...,None])).astype(np.uint8); cv2.imwrite('/tmp/pv_smatte.jpg',cv2.resize(pv,(W//2,H//2),interpolation=cv2.INTER_AREA))
