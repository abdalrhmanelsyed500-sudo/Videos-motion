import sys,subprocess,cv2,numpy as np
FF='/home/user/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
f,out=sys.argv[1],sys.argv[2]; ts=[float(x) for x in sys.argv[3].split(',')]
ims=[]
for t in ts:
    subprocess.run([FF,'-y','-loglevel','error','-ss',str(t),'-i',f,'-frames:v','1','-vf','scale=270:480','build/sh/_t.jpg'],check=True)
    im=cv2.imread('build/sh/_t.jpg'); cv2.putText(im,f'{t}',(8,22),0,0.6,(0,255,255),2); ims.append(im)
while len(ims)%6: ims.append(np.zeros_like(ims[0]))
cv2.imwrite(out,np.vstack([np.hstack(ims[i:i+6]) for i in range(0,len(ims),6)]))
