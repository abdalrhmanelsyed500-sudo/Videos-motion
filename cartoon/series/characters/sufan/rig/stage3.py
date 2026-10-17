"""Cut Sufan's approved front master into rig parts (full-res px). Output: parts/*.png + meta.json"""
import cv2, numpy as np, json, os, math
rgba=cv2.imread('matte_full.png',cv2.IMREAD_UNCHANGED); H,W=rgba.shape[:2]
col=rgba[...,:3].copy(); alpha=rgba[...,3].astype(np.float32)/255
L=np.load('labels.npy')
names=['none','hat','head','torso','armL','armR','handL','handR','belly','legL','legR','bootL','bootR']; ID={n:i for i,n in enumerate(names)}
hsv=cv2.cvtColor(col,cv2.COLOR_BGR2HSV_FULL).astype(np.float32); hue=hsv[...,0]*360/256; sat=hsv[...,1]/255; val=hsv[...,2]/255
yy,xx=np.mgrid[0:H,0:W]
CX=912.0
# ---------------- 1) remove eyes + mouth from the head pixels (they become procedural layers)
head=(L==ID['head'])
eyes=np.zeros((H,W),np.uint8)
for cx,cy in ((798.5,609),(1035,609)):
    r=((xx-cx)**2+(yy-cy)**2)<(66**2); eyes[r&head&((val>0.9)&(sat<0.1)|(val<0.35))]=255   # sclera + pupil only (not the ring: ring is outside r66)
eyes=cv2.dilate(eyes,np.ones((9,9),np.uint8))
mouth=np.zeros((H,W),np.uint8)
mr=(xx>825)&(xx<1000)&(yy>795)&(yy<895)&head&(val<0.62)
mouth[mr]=255; mouth=cv2.dilate(mouth,np.ones((9,9),np.uint8))
feat=cv2.bitwise_or(eyes,mouth)
col_clean=cv2.inpaint(col,feat,9,cv2.INPAINT_TELEA)
col=col_clean
print('removed face px',int((feat>0).sum()))
# ---------------- 2) ear split polyline (left), mirrored for right
polyL=np.array([[572,760],[612,650],[640,560],[668,440]],np.float32)
def cut_x(y):  # x of the polyline for y (left ear): ear is to the LEFT of this
    return np.interp(y,polyL[:,1],polyL[:,0],left=polyL[0,0]-(polyL[0,1]-y)*0.0,right=polyL[-1,0])
ycoord=yy.astype(np.float32)
xcutL=np.interp(ycoord,polyL[::-1,1][::1],polyL[::-1,0][::1])
earzoneY=(yy>430)&(yy<830)
earL=head&earzoneY&(xx<xcutL)&(xx<640)
xcutR=2*CX-xcutL
earR=head&earzoneY&(xx>xcutR)&(xx>2*CX-640)
masks={n:(L==ID[n]) for n in names[1:]}
masks['head']=head&~earL&~earR
masks['earL']=earL; masks['earR']=earR
hall=cv2.dilate(((L==ID['head'])|(L==ID['hat'])).astype(np.uint8),np.ones((13,13),np.uint8))>0
# overlap band: head keeps cream (non-pink) pixels within 34px of the cut
pink=((hue<28)|(hue>335))&(sat>0.45)&(val>0.6)&(val<0.95)
bandL=earL&(xx>xcutL-34)&~pink; bandR=earR&(xx<xcutR+34)&~pink
masks['head']=masks['head']|bandL|bandR
# ---------------- helpers
def own_extend(mask,ring=2):
    """dilate mask by `ring` px, colouring the new ring from nearest own pixel"""
    m=mask.astype(np.uint8)
    dil=cv2.dilate(m,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*ring+1,2*ring+1)))
    dist,idx=cv2.distanceTransformWithLabels((1-m),cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
    flat=np.flatnonzero(m.ravel()); 
    lut=np.zeros(idx.max()+2,np.int64); lut[1:1+len(flat)]=flat
    src=lut[idx]
    c=col.reshape(-1,3)[src.ravel()].reshape(H,W,3); a=alpha.reshape(-1)[src.ravel()].reshape(H,W)
    out_c=np.where(m[...,None]>0,col,c); out_a=np.where(m>0,alpha,np.where(dil>0,np.maximum(a*0+0,0),0))
    # ring pixels keep the ORIGINAL silhouette alpha (so we never grow beyond the character) but own colour
    ring=(dil>0)&(m==0); out_a=np.where(m>0,alpha,np.where(ring,alpha,0))
    return out_c,out_a
def sweep(mask,center,direction,length,step=3,slice_px=14):
    """extrude the end-slice of `mask` along direction (unit) by `length` px -> returns (mask_add,color_img)"""
    ys,xs=np.where(mask); pts=np.stack([xs,ys],1).astype(np.float32)
    t=(pts-center)@direction
    tmax=t.max(); sl=(t>tmax-slice_px)
    add=np.zeros((H,W),np.uint8); cimg=np.zeros((H,W,3),np.uint8)
    p0=pts[sl]; c0=col[ys[sl],xs[sl]]
    for s in range(step,int(length)+1,step):
        q=np.round(p0+direction*s).astype(int)
        ok=(q[:,0]>=0)&(q[:,0]<W)&(q[:,1]>=0)&(q[:,1]<H)
        q=q[ok]; add[q[:,1],q[:,0]]=1; cimg[q[:,1],q[:,0]]=c0[ok]
    add=cv2.morphologyEx(add,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8)); 
    # fill gaps colours by dilating colour image
    cimg2=cv2.dilate(cimg,np.ones((5,5),np.uint8))
    return add>0,cimg2
parts={}  # name -> (color, alpha, mask)
meta={}
def put(name,mask,color=None,al=None):
    c,a=own_extend(mask,2) if color is None else (color,al)
    parts[name]=(c,a)
# ------------- head, hat, ears
# dome under hat
hatm=masks['hat']
dome=((xx-CX)/310.0)**2+((yy-590)/235.0)**2<1
domefill=dome&hatm&~masks['head']
cream=np.median(col[400:470,880:940].reshape(-1,3),axis=0) if False else np.array([211,235,254],np.uint8)  # BGR of #FEEBD3
col_head=col.copy(); col_head[domefill]=cream
alpha_head=alpha.copy(); alpha_head[domefill]=1.0
hm=masks['head']|domefill
c,a=own_extend(hm,2); 
c=np.where(domefill[...,None],cream,c); a=np.where(domefill,1.0,a)
parts['head']=(c,a)
put('hat',hatm)
# ears: extend under head / hat: fill 70px inward (right for left ear) with cream, and up under the hat
for n,sgn,em in (('earL',1,masks['earL']),('earR',-1,masks['earR'])):
    m=em.copy()
    # inward extension: shift mask pixels inside ear area horizontally
    ext=np.zeros((H,W),bool)
    for s in range(4,90,4): ext|=np.roll(em,sgn*s,axis=1)
    ext&=(yy>470)&(yy<800)&~em&hall
    ext&=(xx<xcutL+60) if sgn>0 else (xx>xcutR-60)
    m2=em|ext
    # also up under hat brim
    ext2=np.zeros((H,W),bool)
    for s in range(4,50,4): ext2|=np.roll(em,-s,axis=0)
    ext2&=hatm&~m2
    m2|=ext2
    c,a=own_extend(m2,2)
    c=np.where((m2&~em)[...,None],cream,c); a=np.where(m2&~em,1.0,a)
    parts[n]=(c,a)
# ------------- torso: upward smear under beard, belly: upward smear
hall=cv2.dilate(((L==ID['head'])|(L==ID['hat'])).astype(np.uint8),np.ones((13,13),np.uint8))>0
tm=masks['torso']; c,a=own_extend(tm,2); a0=a.copy(); c0=c.copy()
ys,xs=np.where(tm); 
for x in range(xs.min(),xs.max()+1):
    col_y=np.where(tm[:,x])[0]
    if len(col_y)==0: continue
    y0=col_y.min()
    if y0>1100: continue
    ysrc=min(y0+10,col_y.max())
    c[y0-170:y0,x]=col[ysrc,x]; a[y0-170:y0,x]=1.0
bad=(a>a0+1e-6)&~hall
a[bad]=a0[bad]; c[bad]=c0[bad]
parts['torso']=(c,a)
bm=masks['belly']; c,a=own_extend(bm,2)
for x in range(0,W):
    col_y=np.where(bm[:,x])[0]
    if len(col_y)==0: continue
    y0=col_y.min(); ysrc=min(y0+8,col_y.max())
    c[y0-240:y0,x]=col[ysrc,x]; a[y0-240:y0,x]=1.0
parts['belly']=(c,a)
# ------------- arms (sleeve): PCA axis + extension towards shoulder; hand: extension towards cuff
armgeo={}
for s,sg in (('L',1),('R',-1)):
    am=masks['arm'+s]; hm_=masks['hand'+s]
    ys,xs=np.where(am); pts=np.stack([xs,ys],1).astype(np.float32); mu=pts.mean(0)
    u,sv,vt=np.linalg.svd(pts-mu,full_matrices=False); d=vt[0]
    # direction pointing towards the shoulder (towards the body centre / upward)
    toward=np.array([CX-mu[0],1100-mu[1]],np.float32)
    if d@toward<0: d=-d
    t=(pts-mu)@d; tmin,tmax=t.min(),t.max()
    ext_m,ext_c=sweep(am,mu,d,170)
    c,a=own_extend(am,2); ext_only=ext_m&~am
    c=np.where(ext_only[...,None],ext_c,c); a=np.where(ext_only,1.0,a)
    am2=am|ext_only
    # split into upper / lower at elbow fraction 0.52 along the visible sleeve (+ 30 px overlap)
    tt=((xx-mu[0])*d[0]+(yy-mu[1])*d[1])
    elbow_t=tmin+0.52*(tmax-tmin)
    upm=am2&(tt>=elbow_t-30); lom=am&(tt<=elbow_t+30)
    cu,au=own_extend(upm,1); cl,al=own_extend(lom,1)
    cu=np.where(ext_only[...,None],ext_c,cu); au=np.where(ext_only,1.0,au)
    parts['armUp'+s]=(cu,au); parts['armLo'+s]=(cl,al)
    # hand + extension towards the cuff (direction toward arm = d)
    ysh,xsh=np.where(hm_); ph=np.stack([xsh,ysh],1).astype(np.float32); muh=ph.mean(0)
    hext_m,hext_c=sweep(hm_,muh,d*1.0,80) if False else (None,None)
    # extend hand pixels along d (towards the sleeve)
    th=(ph-muh)@d; sl=th>th.max()-12; q0=ph[sl]; c0=col[ysh[sl],xsh[sl]]
    add=np.zeros((H,W),np.uint8); ci=np.zeros((H,W,3),np.uint8)
    for k in range(3,90,3):
        q=np.round(q0+d*k).astype(int); ok=(q[:,0]>=0)&(q[:,0]<W)&(q[:,1]>=0)&(q[:,1]<H); q=q[ok]; add[q[:,1],q[:,0]]=1; ci[q[:,1],q[:,0]]=c0[ok]
    add=cv2.morphologyEx(add,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))>0; ci=cv2.dilate(ci,np.ones((5,5),np.uint8))
    ch,ah=own_extend(hm_,2); eo=add&~hm_; ch=np.where(eo[...,None],ci,ch); ah=np.where(eo,1.0,ah)
    parts['hand'+s]=(ch,ah)
    # joint positions: shoulder = hidden end, elbow, wrist
    sh=mu+d*(tmax+120); el=mu+d*(elbow_t); wr=mu+d*(tmin+8)
    armgeo[s]=dict(dir=d.tolist(),shoulder=sh.tolist(),elbow=el.tolist(),wrist=wr.tolist(),hand_c=muh.tolist())
# ------------- legs: extend upward under belly, boots
for s in 'LR':
    lm=masks['leg'+s]; ys,xs=np.where(lm); mu=np.array([xs.mean(),ys.mean()],np.float32)
    ext_m,ext_c=sweep(lm,mu,np.array([0,-1.0],np.float32),110)
    c,a=own_extend(lm,2); eo=ext_m&~lm; c=np.where(eo[...,None],ext_c,c); a=np.where(eo,1.0,a)
    parts['leg'+s]=(c,a)
    put('boot'+s,masks['boot'+s])
json.dump(dict(arm=armgeo),open('geo.json','w'),indent=1)
# ------------- save as cropped PNGs + anchors file
os.makedirs('parts',exist_ok=True)
bb={}
for n,(c,a) in parts.items():
    m=a>0.004; ys,xs=np.where(m); x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    out=np.dstack([c[y0:y1,x0:x1],(a[y0:y1,x0:x1]*255+0.5).astype(np.uint8)])
    cv2.imwrite(f'parts/{n}.png',out); bb[n]=[int(x0),int(y0),int(x1),int(y1)]
json.dump(bb,open('parts/bbox.json','w'),indent=1)
print({n:b for n,b in bb.items()})
print(json.dumps(armgeo))
