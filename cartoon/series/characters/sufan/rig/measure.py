import cv2, numpy as np
rgba=cv2.imread('matte_full.png',cv2.IMREAD_UNCHANGED); H,W=rgba.shape[:2]
bgr=rgba[...,:3]; hsv=cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV_FULL).astype(np.float32)
val=hsv[...,2]/255; sat=hsv[...,1]/255
black=((val<0.30)).astype(np.uint8); black[:420]=0; black[760:]=0   # full-res y 420..760 (half 210..380)
n,cc,st,cen=cv2.connectedComponentsWithStats(black,connectivity=8)
for k in range(1,n):
    if st[k,4]>150: print(k,st[k],cen[k])
white=((val>0.965)&(sat<0.06)).astype(np.uint8); white[:420]=0; white[760:]=0
n2,cc2,st2,cen2=cv2.connectedComponentsWithStats(white)
for k in range(1,n2):
    if st2[k,4]>800: print('white',k,st2[k],cen2[k])
