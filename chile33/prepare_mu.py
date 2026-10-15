"""NEW unified Mauro FRONT body (v4) cut from the AI model-sheet figure assets/raw/mu_front_apose.jpg (same proportions as the side rig).
Pieces (RGBA, cropped; offsets in mf_pieces.json, all in 'cut' pixel coordinates of assets/raw/mu_front_cut.png):
 torso (neck stub + vest + shoulder caps), arm{L,R}_up (deltoid..elbow disc), arm{L,R}_fo (forearm+hand, rounded top), pelvis (shorts top),
 thigh{L,R} (shorts leg opening .. knee disc), shin{L,R} (knee .. shoe).  The head is NOT included: ph_* expression heads are used."""
import cv2, json, numpy as np
src = cv2.imread('assets/raw/mu_front_cut.png', -1)
Hh, Ww = src.shape[:2]
A = src[:, :, 3].astype(np.float32) / 255.
B, G, R = [src[:, :, i].astype(np.float32) for i in range(3)]
blue = ((B > R + 14) & (B > 60)).astype(np.uint8)          # shorts / light-blue vest stripes (only used below the waist)
yy, xx = np.mgrid[0:Hh, 0:Ww]
def poly(pts):
    m = np.zeros((Hh, Ww), np.uint8); cv2.fillPoly(m, [np.array(pts, np.int32)], 1); return m
def disc(c, r):
    m = np.zeros((Hh, Ww), np.uint8); cv2.circle(m, (int(c[0]), int(c[1])), int(r), 1, -1); return m
def soft(m, s=0.9): return np.clip(cv2.GaussianBlur(m.astype(np.float32), (0, 0), s), 0, 1)
below = (yy > 428).astype(np.uint8)
skin = ((R - B) > 16).astype(np.uint8)
watch = np.zeros((Hh, Ww), np.uint8); cv2.rectangle(watch, (250, 388), (294, 428), 1, -1)       # the dark watch is not 'skin' coloured
notblue_low = np.clip(skin + watch, 0, 1)      # arm pieces = skin pixels only (no vest edge / shorts slivers that would stay behind when the arm moves)
def keep_main(m):
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n <= 1: return m
    k = 1 + np.argmax(st[1:, 4]); return (lab == k).astype(np.uint8)
pieces = {}; meta = {}
def put(name, m, fade_top=None, fade_bot=None):
    a = A * soft(m)
    if fade_top: a = a * np.clip((yy - fade_top[0]) / float(fade_top[1] - fade_top[0]), 0, 1)
    if fade_bot: a = a * np.clip((fade_bot[1] - yy) / float(fade_bot[1] - fade_bot[0]), 0, 1)
    ys, xs = np.where(a > 0.02); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    im = np.dstack([src[:, :, :3], (a * 255).astype(np.uint8)])[y0:y1, x0:x1]
    pieces[name] = im; meta[name] = (int(x0), int(y0))
# ---------------------------------------------------------------- torso
torso = poly([(128, 120), (192, 120), (194, 150), (222, 160), (252, 176), (260, 196), (256, 232), (242, 262), (229, 292), (229, 446), (92, 446), (92, 292), (79, 262), (64, 232), (60, 196), (68, 176), (98, 160), (126, 150)])
put('torso', torso, fade_bot=(436, 446))
# ---------------------------------------------------------------- arms (pivot = elbow)
EL = {'L': (58, 326, 22), 'R': (261, 326, 21)}
armreg = {'L': poly([(40, 160), (98, 158), (104, 200), (96, 250), (92, 300), (92, 560), (0, 560), (0, 160)]),
          'R': poly([(280, 160), (222, 158), (216, 200), (224, 250), (228, 300), (228, 560), (320, 560), (320, 160)])}
for s in 'LR':
    ex, ey, r = EL[s]
    reg = keep_main(armreg[s] * notblue_low)
    up = (reg * (yy < ey)) | disc((ex, ey), r)
    fo = (reg * (yy >= ey)) | (disc((ex, ey), r) * (yy < ey))
    put('arm%s_up' % s, up.astype(np.uint8) * armreg[s].clip(0, 1) | (disc((ex, ey), r)))
    put('arm%s_fo' % s, fo.astype(np.uint8))
# ---------------------------------------------------------------- pelvis + legs
pel = poly([(79, 420), (239, 420), (239, 506), (79, 506)])
put('pelvis', pel * keep_main(A > 0.3), fade_bot=(494, 506))
KN = {'L': (113, 612, 23), 'R': (196, 612, 26)}
legx = {'L': poly([(78, 495), (160, 495), (160, 850), (78, 850)]), 'R': poly([(154, 495), (240, 495), (240, 850), (154, 850)])}
for s in 'LR':
    kx, ky, r = KN[s]
    th = (legx[s] * (yy < ky) * (yy >= 495)) | (disc((kx, ky), r) * legx[s])
    sh = (legx[s] * (yy >= ky)) | (disc((kx, ky), r) * legx[s] * (yy < ky))
    put('thigh' + s, keep_main(th * (A > 0.3))); put('shin' + s, keep_main(sh * (A > 0.3)))
for k, im in pieces.items(): cv2.imwrite('assets/layers/mf_%s.png' % k, im)
json.dump(meta, open('assets/layers/mf_pieces.json', 'w'))
print({k: (v.shape, meta[k]) for k, v in pieces.items()})
# assembled check (rest pose) over a violet backdrop
canvas = np.zeros((Hh, Ww, 3), np.float32); canvas[:] = (200, 90, 140)
def over(name):
    im = pieces[name]; ox, oy = meta[name]; h, w = im.shape[:2]
    a = im[:, :, 3:] / 255.; canvas[oy:oy + h, ox:ox + w] = canvas[oy:oy + h, ox:ox + w] * (1 - a) + im[:, :, :3] * a
for n in ['shinL', 'shinR', 'thighL', 'thighR', 'pelvis', 'armL_fo', 'armR_fo', 'torso', 'armL_up', 'armR_up']: over(n)
cv2.imwrite('build/mf_assembled.png', canvas.astype(np.uint8))
