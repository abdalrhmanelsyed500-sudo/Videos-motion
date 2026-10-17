"""Presentation sheets: character parts sheet (like a Freepik animation kit) and bone/armature diagram (like Blender pose mode)."""
import os, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
from . import face as F, chars, anim
from .rig import Rig, T3
from .render import ROOT

FONT = os.path.join(ROOT, 'fonts', 'Amiri-Bold.ttf')
def ar(s): return get_display(arabic_reshaper.reshape(s))

def text(img, xy, s, size=34, color=(255, 255, 255), anchor='la', arabic=False):
    pil = Image.fromarray(img[..., ::-1]); d = ImageDraw.Draw(pil); f = ImageFont.truetype(FONT, size)
    d.text(xy, ar(s) if arabic else s, font=f, fill=tuple(color), anchor=anchor); img[:] = np.array(pil)[..., ::-1]

def rigs(name):
    return {v: Rig(os.path.join(ROOT, 'out', 'rigs', f'{name}_{v}', 'rig.json')) for v in ('front', 'side')}

def draw_on(img, rig, pose, cam, spec, view, **kw):
    cv = img.astype(np.float32) / 255
    rig.draw(cv, pose, cam, dyn=F.face_dyn(kw.pop('face', {}), spec, view), **kw)
    img[:] = (np.clip(cv, 0, 1) * 255 + .5).astype(np.uint8)

def blit_part(img, rig, part, dst, scale, mirror=False):
    im = rig.img(part); ax, ay = rig.parts[part]['anchor']; k = scale / rig.ppu
    a = cv2.resize(im, None, fx=k, fy=k, interpolation=cv2.INTER_AREA); ax *= k; ay *= k
    if mirror: a = a[:, ::-1]; ax = a.shape[1] - ax
    x0 = int(round(dst[0] - ax)); y0 = int(round(dst[1] - ay)); h, w = a.shape[:2]
    X0, Y0 = max(x0, 0), max(y0, 0); X1, Y1 = min(x0 + w, img.shape[1]), min(y0 + h, img.shape[0])
    if X1 <= X0 or Y1 <= Y0: return
    s = a[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]; al = s[..., 3:4]
    roi = img[Y0:Y1, X0:X1].astype(np.float32) / 255; img[Y0:Y1, X0:X1] = (np.clip(roi * (1 - al) + s[..., :3], 0, 1) * 255 + .5).astype(np.uint8)

EXPR = [('Neutral · عادي', {}), ('Happy · سعيد', dict(mouth=F.VISEMES['grin'], browL=(.5, .1), browR=(.5, .1), squint=.35)), ('Surprised · متفاجئ', dict(mouth=F.VISEMES['gasp'], browL=(1, -.2), browR=(1, -.2))),
        ('Sad · حزين', dict(mouth=F.VISEMES['sad'], browL=(0, -.8), browR=(0, -.8), look=(0, .5))), ('Angry · غاضب', dict(mouth=F.mix_vis(F.VISEMES['M'], F.VISEMES['sad'], .5), browL=(-.3, .9), browR=(-.3, .9), lidtilt=.5)),
        ('Wink · غمزة', dict(mouth=F.VISEMES['smile'], blinkL=1.0, browL=(.2, 0), browR=(.5, 0))), ('Laugh · ضحك', dict(mouth=F.VISEMES['laugh'], squint=.6, browL=(.7, 0), browR=(.7, 0))), ('Talk "A"', dict(mouth=F.VISEMES['A'], browL=(.3, 0), browR=(.3, 0)))]

def parts_sheet(name, out):
    R = rigs(name); spec = chars.SPECS[name]; rf, rs = R['front'], R['side']
    W, H = 2600, 1500; img = np.full((H, W, 3), (170, 168, 190), np.uint8)   # warm grey like the reference (BGR)
    img[:] = (176, 170, 192)
    cv2.rectangle(img, (0, 0), (W, 96), (60, 52, 70), -1)
    text(img, (40, 14), f'{name.upper()} — Character Animation Kit', 58, (255, 255, 255)); text(img, (W - 40, 18), 'مجموعة الشخصية — أجزاء منفصلة جاهزة للتحريك', 54, (255, 255, 255), 'ra', True)
    def panel(x0, y0, x1, y1, title=None):
        cv2.rectangle(img, (x0, y0), (x1, y1), (150, 145, 170), 3, cv2.LINE_AA)
        if title:
            en, _, arb = title.partition(' · ')
            text(img, (x0 + 16, y0 + 8), en, 30, (70, 60, 80))
            if arb: text(img, (x1 - 16, y0 + 8), arb, 32, (70, 60, 80), 'ra', True)
    # 1. assembled front + side
    panel(30, 120, 520, 1040, 'Assembled · مجمّع'); draw_on(img, rf, {}, (0.94, 275, 1010), spec, 'front', dyn=None) if False else None
    draw_on(img, rf, {}, (0.92, 195, 1010), spec, 'front', face=dict(mouth=F.VISEMES['smile'])); draw_on(img, rs, {}, (0.92, 420, 1010), spec, 'side', face=dict(mouth=F.VISEMES['smile']))
    # 2. exploded body
    panel(550, 120, 1130, 1040, 'Separated parts · الأجزاء')
    s = 0.74; ox = 840
    blit_part(img, rf, 'torso', (ox, 520), s); blit_part(img, rf, 'pelvis', (ox, 670), s)
    for i, g in enumerate((-1, 1)):
        x = ox + g * 195; blit_part(img, rf, 'upperarm', (x, 380), s, mirror=g < 0); blit_part(img, rf, 'forearm', (x, 470), s, mirror=g < 0)
        blit_part(img, rf, 'hand_relaxed', (x, 560), s, mirror=g < 0)
        x2 = ox + g * 75; blit_part(img, rf, 'thigh', (x2, 800), s); blit_part(img, rf, 'shin', (x2, 880), s); blit_part(img, rf, 'shoe', (x2, 965), s, mirror=g < 0)
    draw_on(img, rf, {}, (s, ox, 250 + 490 * s), spec, 'front', face=dict(mouth=F.VISEMES['smile']), only={'head', 'eyeL', 'eyeR', 'browL', 'browR', 'mouth'})
    hp = 'tuft' if spec['kind'] == 'boy' else 'pigtail'
    if hp == 'tuft': blit_part(img, rf, hp, (ox + 330 * 0 + 150, 330), s)
    else: blit_part(img, rf, hp, (ox - 190, 215), s); blit_part(img, rf, hp, (ox + 190, 215), s, mirror=True)
    # 3. expression heads (top row)
    panel(1160, 120, 2570, 470, 'Facial expressions (runtime-generated from parameters) · تعبيرات الوجه')
    for i, (nm, fc) in enumerate(EXPR):
        cx = 1160 + 85 + (i % 8) * 170; cy = 330
        draw_on(img, rf, {}, (0.42, cx, cy + 490 * 0.42 - 20 + 380 * 0), spec, 'front', face=fc, only={'head', 'eyeL', 'eyeR', 'browL', 'browR', 'mouth', 'tuft', 'pigtailL', 'pigtailR'}, root={'y': 0}) if False else None
    for i, (nm, fc) in enumerate(EXPR):
        cx = 1160 + 85 + i * 170; k = 0.40
        # place head: neck at world (0,-392) -> choose cam so that head centre (0,-490) lands at (cx, 285)
        cam = (k, cx, 285 + 490 * k)
        draw_on(img, rf, {}, cam, spec, 'front', face=fc, only={'head', 'eyeL', 'eyeR', 'browL', 'browR', 'mouth', 'tuft', 'pigtailL', 'pigtailR'})
        text(img, (cx, 440), nm.split('·')[0].strip() if '·' in nm else nm, 22, (70, 60, 80), 'ma')
    # 4. viseme row
    panel(1160, 490, 2570, 770, 'Mouth shapes (visemes) · أشكال الفم للنطق')
    vs = ['rest', 'M', 'A', 'E', 'I', 'O', 'U', 'FV', 'L', 'smile', 'grin', 'laugh', 'sad', 'gasp']
    for i, v in enumerate(vs):
        cx = 1160 + 52 + i * 100; k = 0.62
        draw_on(img, rf, {}, (k, cx, 630 + 448 * k), spec, 'front', face=dict(mouth=F.VISEMES[v], blinkL=0, blinkR=0), only={'mouth'}, root={'x': 0, 'y': 0})
        text(img, (cx, 722), v, 24, (70, 60, 80), 'ma')
    # 5. hands (swappable)
    panel(1160, 790, 1760, 1040, 'Hand poses · وضعيات اليد')
    for i, hk in enumerate(chars.HAND_KINDS):
        blit_part(img, rf, 'hand_' + hk, (1160 + 80 + i * 140, 880), 1.0); text(img, (1160 + 80 + i * 140, 1005), hk, 22, (70, 60, 80), 'ma')
    # 6. arm poses
    panel(1790, 790, 2570, 1040, 'Arm / gesture presets · أوضاع الذراع')
    D = math.radians
    pr = [('Wave', {'armR_up': {'rot': D(-112)}, 'armR_lo': {'rot': D(-68)}}, {'handR': 'hand_open'}), ('Point', {'armR_up': {'rot': D(-80)}, 'armR_lo': {'rot': D(-6)}}, {'handR': 'hand_point'}),
          ('Emphasis', {'armR_up': {'rot': D(-34)}, 'armR_lo': {'rot': D(-62)}}, {'handR': 'hand_open'}), ('Cheer', {'armR_up': {'rot': D(-150)}, 'armL_up': {'rot': D(150)}, 'armR_lo': {'rot': D(-18)}, 'armL_lo': {'rot': D(18)}}, {'handR': 'hand_open', 'handL': 'hand_open'})]
    for i, (nm, p, sw) in enumerate(pr):
        cx = 1790 + 100 + i * 190
        draw_on(img, rf, p, (0.29, cx, 1022), spec, 'front', swap=sw, only={'torso', 'pelvis', 'upperarmR', 'forearmR', 'handR', 'upperarmL', 'forearmL', 'handL', 'head', 'eyeL', 'eyeR', 'mouth', 'browL', 'browR', 'thighL', 'thighR', 'shinL', 'shinR', 'shoeL', 'shoeR', 'tuft', 'pigtailL', 'pigtailR'}, face=dict(mouth=F.VISEMES['smile']))
        text(img, (cx, 1010), nm, 22, (70, 60, 80), 'ma')
    # 7. walk cycle strip (side view, foot-locked IK)
    from .anim import Walker
    panel(30, 1060, 2570, 1480, 'Side walk cycle (procedural, foot-locked IK) · دورة المشي من الجانب')
    wk = Walker(rs, +1, 0, 700, 0.0, 3.0); t0 = wk.t_lift0 + 3 * wk.Ts; n = 10
    for i in range(n):
        t = t0 + i * (2 * wk.Ts) / n; rx, pose = wk.state(t)
        cx = 30 + 130 + i * 255
        cam = (0.52, cx - rx * 0.52, 1455)
        draw_on(img, rs, pose, cam, spec, 'side', root={'x': rx}, face=dict(mouth=F.VISEMES['smile']))
    cv2.imwrite(out, img)

# ---------------------------------------------------------------- bone diagram
BONE_COL = (205, 190, 150); BONE_EDGE = (255, 255, 255)

def bone_diagram(out):
    W, H = 2600, 1500; img = np.full((H, W, 3), (62, 62, 62), np.uint8)
    for x in range(0, W, 50): cv2.line(img, (x, 0), (x, H), (70, 70, 70), 1)
    for y in range(0, H, 50): cv2.line(img, (0, y), (W, y), (70, 70, 70), 1)
    cv2.line(img, (0, 1370), (W, 1370), (60, 60, 200), 2)          # ground / x axis like Blender's red line
    cv2.rectangle(img, (0, 0), (W, 90), (40, 40, 40), -1)
    text(img, (40, 12), 'RigKit — Armature (Pose view)', 56, (255, 255, 255)); text(img, (W - 40, 16), 'هيكل العظام (الـ Rig) للشخصيتين', 52, (255, 255, 255), 'ra', True)
    cells = [('zaki', 'front', 330), ('zaki', 'side', 930), ('lulu', 'front', 1530), ('lulu', 'side', 2150)]
    for (nm, v, cx) in cells:
        R = rigs(nm)[v]; spec = chars.SPECS[nm]; k = 1.72; cam = (k, cx, 1370)
        cv = img.astype(np.float32) / 255; ghost = np.zeros_like(cv)
        R.draw(ghost, {}, cam, dyn=F.face_dyn(dict(mouth=F.VISEMES['smile']), spec, v))
        # ghost: draw character translucent over background
        mask = np.zeros(cv.shape[:2], np.float32); tmp1 = np.zeros_like(cv); tmp2 = np.ones_like(cv)
        R.draw(tmp1, {}, cam, dyn=F.face_dyn(dict(mouth=F.VISEMES['smile']), spec, v)); R.draw(tmp2, {}, cam, dyn=F.face_dyn(dict(mouth=F.VISEMES['smile']), spec, v))
        al = np.clip(1 - (tmp2 - tmp1).mean(2), 0, 1)[..., None]
        cv = cv * (1 - al * .55) + tmp1 * .55
        img = (np.clip(cv, 0, 1) * 255 + .5).astype(np.uint8)
        W_ = R.world({}, {}); kids = {}
        for b in R.bones:
            if b['parent']: kids.setdefault(b['parent'], []).append(b['name'])
        def P(n): p = W_[n][:2, 2]; return np.array([cx + p[0] * k, 1370 + p[1] * k])
        for b in R.bones:
            n = b['name']
            if n == 'root': continue
            p0 = P(n)
            if n in kids and n != 'hips':
                ch = [c for c in kids[n] if c not in ('tuft', 'pigtailL', 'pigtailR')] or kids[n]
                p1 = P(ch[0])
            else:
                dirs = {'tuft': (0, -60), 'pigtailL': (0, 120), 'pigtailR': (0, 120)}
                d = dirs.get(n, (0, 50 if n.startswith('hand') else 60 if n.startswith('foot') else 30)); p1 = p0 + np.array(d, float) * (k / 1.8)
                if n.startswith('foot'): p1 = p0 + np.array([(26 if v == 'front' else 70) * k, 28 * k]) * (1 if not n.endswith('L') or v == 'side' else -1)
            if np.linalg.norm(p1 - p0) < 4: continue
            d = (p1 - p0) / np.linalg.norm(p1 - p0); nrm = np.array([-d[1], d[0]]); w = min(14, 0.12 * np.linalg.norm(p1 - p0) + 5); mid = p0 + (p1 - p0) * .18
            poly = np.array([p0, mid + nrm * w, p1, mid - nrm * w], np.int32)
            col = (200, 170, 120) if 'L' in n[-3:] or n.endswith('L') else (170, 200, 140) if n.endswith('R') or n[-3:].startswith('R') else (190, 190, 200)
            cv2.fillPoly(img, [poly], col, cv2.LINE_AA); cv2.polylines(img, [poly], True, (255, 255, 255), 1, cv2.LINE_AA)
        for b in R.bones:                              # joints
            n = b['name']; p = P(n); cv2.circle(img, (int(p[0]), int(p[1])), 7, (255, 255, 255), -1, cv2.LINE_AA); cv2.circle(img, (int(p[0]), int(p[1])), 7, (30, 30, 30), 1, cv2.LINE_AA)
        # IK controllers (orange) and root (big ring) and face controls (yellow)
        for ik, d in R.ik.items():
            e = P(d['chain'][2]); cv2.circle(img, (int(e[0]), int(e[1])), 17, (40, 150, 255), 3, cv2.LINE_AA)
        r0 = np.array([cx, 1370.0]); cv2.circle(img, (int(r0[0]), int(r0[1])), 36, (40, 190, 255), 4, cv2.LINE_AA); cv2.line(img, (int(r0[0] - 50), 1370), (int(r0[0] + 50), 1370), (40, 190, 255), 4)
        from .build import FACE_FRONT, FACE_SIDE
        for kf, off in (FACE_FRONT if v == 'front' else FACE_SIDE).items():
            hp = P('head') + np.array(off) * k; cv2.circle(img, (int(hp[0]), int(hp[1])), 9, (0, 230, 255), 2, cv2.LINE_AA)
        text(img, (cx, 110), f'{nm.capitalize()} · {v}', 44, (255, 255, 255), 'ma')
        if v == 'front':
            def labels(items, side):
                items = sorted(items, key=lambda it: P(it[1])[1]); y_prev = -1e9
                for lbl, bn in items:
                    p = P(bn); y = max(p[1], y_prev + 46); y_prev = y
                    x = cx + side * 215
                    cv2.line(img, (int(p[0]), int(p[1])), (int(x), int(y)), (200, 200, 200), 1, cv2.LINE_AA)
                    text(img, (x + side * 8, y - 16), lbl, 26, (235, 235, 235), 'la' if side > 0 else 'ra')
            labels([('shoulder / upper arm', 'armR_up'), ('elbow / forearm', 'armR_lo'), ('wrist / hand  (IK)', 'handR'), ('hip / thigh', 'legR_up'), ('knee / shin', 'legR_lo'), ('ankle / foot  (IK)', 'footR')], +1)
            labels([('head (neck pivot)', 'head'), ('spine / hips (body lean, breathing)', 'spine'), ('tuft / pigtails (spring)', 'tuft' if nm == 'zaki' else 'pigtailL')], -1)
    text(img, (60, 1420), 'orange rings = IK controllers · big ring = root (move/squash/flip) · yellow rings = face controls (eyes, brows, mouth) · blue/green bones = left/right', 28, (210, 210, 210))
    cv2.imwrite(out, img)

if __name__ == '__main__':
    import sys
    od = os.path.join(ROOT, 'out', 'demo'); os.makedirs(od, exist_ok=True)
    for n in chars.SPECS: parts_sheet(n, os.path.join(od, f'parts_sheet_{n}.png'))
    bone_diagram(os.path.join(od, 'bones_diagram.png'))
