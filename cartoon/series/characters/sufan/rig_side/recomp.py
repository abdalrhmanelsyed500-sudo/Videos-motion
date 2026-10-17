import cv2,numpy as np,json,sys
BB=json.load(open(sys.argv[1] if len(sys.argv)>1 else 'parts/bbox.json')); d=sys.argv[2] if len(sys.argv)>2 else 'parts'
m=cv2.imread('master_side_2x.png'); H,W=m.shape[:2]
cv=np.zeros((H,W,3),np.float32)+np.array([255,0,255],np.float32)
order=['thighF','shinF','bootF','thighN','shinN','bootN','belly','torso','armUp','armLo','hand','head','ear','glasses','hat']
for n in order:
    im=cv2.imread(f'{d}/{n}.png',cv2.IMREAD_UNCHANGED).astype(np.float32); x0,y0,x1,y1=BB[n]; a=im[...,3:4]/255
    cv[y0:y1,x0:x1]=cv[y0:y1,x0:x1]*(1-a)+im[...,:3]*a
out=cv.astype(np.uint8); cv2.imwrite('recomp.png',out)
cv2.imwrite('/tmp/pv_srecomp.jpg',cv2.resize(out,(W//2,H//2),interpolation=cv2.INTER_AREA))
