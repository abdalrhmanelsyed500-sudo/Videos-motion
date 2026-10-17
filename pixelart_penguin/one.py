import sys, numpy as np
from PIL import Image
import anims as A, frames as F
name=sys.argv[1]; idxs=[int(i) for i in sys.argv[2].split(',')]; dirs=sys.argv[3].split(','); k=int(sys.argv[4]); out=sys.argv[5]
rows=[]
for d in dirs:
    y=A.DIRS[d]; ps=A.ANIMS[name][0](y); rows.append(np.concatenate([F.render_frame(ps[i],y,cx=A.cx_for(name,y)) for i in idxs],1))
im=np.concatenate(rows,0); big=Image.fromarray(im,'RGBA').resize((im.shape[1]*k,im.shape[0]*k),Image.NEAREST); bg=Image.new('RGBA',big.size,(92,108,80,255)); bg.alpha_composite(big); bg.convert('RGB').save(out)
