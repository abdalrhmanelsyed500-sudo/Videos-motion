import cv2, numpy as np
im=cv2.imread('../work/master_front.png'); H,W=im.shape[:2]
lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB).astype(np.float32)
bgl=np.array([236.5,128.0,128.0],np.float32)
d=np.sqrt(((lab-bgl)**2*np.array([0.5,1,1],np.float32)).sum(2))
# alpha ramp
a=np.clip((d-2.5)/(8.0-2.5),0,1)
# background connected to border = bg; keep interior holes only if strongly different
bgmask=(d<4).astype(np.uint8)
n,cc=cv2.connectedComponents(bgmask)
border=set(np.unique(np.concatenate([cc[0],cc[-1],cc[:,0],cc[:,-1]])))-{0}
bgc=np.isin(cc,list(border))
a[bgc&(d<4)]=0
# interior enclosed grey regions (e.g. between arm and body) are also bg: label components not touching border but small d
for k in range(1,n):
    if k in border: continue
    m=cc==k
    if m.sum()>200: a[m]=0
alpha=a
# decontaminate: c = (obs-(1-a)*bg)/a
bg=np.array([235,234,234],np.float32)
obs=im.astype(np.float32); aa=np.maximum(alpha[...,None],1e-3)
col=np.clip((obs-(1-alpha[...,None])*bg)/aa,0,255)
col[alpha>0.97]=obs[alpha>0.97]
rgba=np.dstack([col,alpha*255]).astype(np.uint8)
cv2.imwrite('matte_full.png',rgba)
print('fg px',(alpha>0.5).sum(), 'bbox',cv2.boundingRect((alpha>0.5).astype(np.uint8)))
# preview on magenta
pv=(col*alpha[...,None]+np.array([255,0,255],np.float32)*(1-alpha[...,None])).astype(np.uint8)
cv2.imwrite('matte_prev.jpg',cv2.resize(pv,(W//2,H//2),interpolation=cv2.INTER_AREA))
