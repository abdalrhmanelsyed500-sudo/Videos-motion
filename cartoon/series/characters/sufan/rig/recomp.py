import cv2,numpy as np,json
bb=json.load(open('parts/bbox.json'))
orig=cv2.imread('../work/master_front.png'); H,W=orig.shape[:2]
Z=['legL','legR','bootL','bootR','belly','handL','handR','armLoL','armLoR','armUpL','armUpR','torso','earL','earR','head','hat']
import sys
only=sys.argv[1].split(',') if len(sys.argv)>1 else Z
cv=np.zeros((H,W,3),np.float32)+np.array([235,234,234],np.float32)
for n in Z:
    if n not in only: continue
    im=cv2.imread(f'parts/{n}.png',cv2.IMREAD_UNCHANGED).astype(np.float32); x0,y0,x1,y1=bb[n]
    a=im[...,3:4]/255; reg=cv[y0:y1,x0:x1]; cv[y0:y1,x0:x1]=reg*(1-a)+im[...,:3]*a
out=np.clip(cv,0,255).astype(np.uint8)
cv2.imwrite('recomp.png',out)
d=np.abs(out.astype(int)-orig.astype(int)).sum(2)
print('mean diff',d.mean(),'px>60:',(d>60).sum())
dm=np.clip(d*3,0,255).astype(np.uint8); cv2.imwrite('recomp_diff.jpg',cv2.resize(dm,(W//2,H//2)))
cv2.imwrite('recomp_prev.jpg',cv2.resize(out,(W//2,H//2),interpolation=cv2.INTER_AREA))
