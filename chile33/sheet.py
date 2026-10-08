import sys, glob, cv2, numpy as np
fs = sorted(glob.glob(sys.argv[1] + '*.jpg')); cols = int(sys.argv[3]) if len(sys.argv) > 3 else 3
ims = []
for f in fs:
    im = cv2.resize(cv2.imread(f), (640, 360)); cv2.putText(im, f.split('_')[-1][:-4], (8, 24), 0, 0.8, (0, 255, 255), 2); ims.append(im)
while len(ims) % cols: ims.append(np.zeros_like(ims[0]))
cv2.imwrite(sys.argv[2], np.vstack([np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]))
