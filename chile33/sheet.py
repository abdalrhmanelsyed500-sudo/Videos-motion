import cv2,glob,sys,numpy as np
fs=sorted(glob.glob(sys.argv[1]+'*.jpg'))
ims=[cv2.resize(cv2.imread(f),(640,360)) for f in fs]
for i,f in enumerate(fs): cv2.putText(ims[i],f.split('_')[-1][:-4],(10,30),0,0.8,(0,255,0),2)
if len(ims)%2: ims.append(ims[0]*0)
cv2.imwrite(sys.argv[2],np.vstack([np.hstack(ims[i:i+2]) for i in range(0,len(ims),2)]))
