"""Oil-painted layered puppet test: alley parallax + rigged character with the signature face mark."""
import cv2, math, numpy as np
from engine import *
import arabic_reshaper
from bidi.algorithm import get_display

AFONT = 'assets/Amiri-Bold.ttf'
OFF = {'head': (446, 35), 'torso': (360, 270), 'arm_l': (166, 262), 'arm_r': (733, 270), 'fore_l': (175, 467), 'fore_r': (755, 463), 'leg_l': (934, 209), 'leg_r': (1150, 214), 'mouth': (667, 152)}
HIPS = (513, 640); BGF = 1280 / 1376; VP = (700, 420)


def ar_text_layer(s, size=52, color=(70, 170, 232)):
    shaped = get_display(arabic_reshaper.reshape(s)); f = font(size, AFONT)
    bb = f.getbbox(shaped); tw = bb[2] - bb[0] + 40; th = int(size * 1.9)
    im = Image.new('L', (tw, th), 0); ImageDraw.Draw(im).text((20 - bb[0], 10), shaped, font=f, fill=255, stroke_width=4, stroke_fill=110)
    a = np.asarray(im, np.float32) / 255
    return a


def mouth_layer():
    L = get_layer('ar_mouth'); im = L.img.copy(); h, w = im.shape[:2]
    m = np.zeros((h, w), np.float32); cv2.ellipse(m, (w // 2, int(h * 0.42)), (int(w * 0.40), int(h * 0.30)), 0, 0, 360, 1.0, -1); m = cv2.GaussianBlur(m, (0, 0), 2.5)
    im *= m[..., None]; return Layer.from_array(im)


_ml = []
def pm(frame, name, socket, pivot, theta=0.0, sx=1.0, sy=1.0):
    ox, oy = OFF[name]; return frame @ M3(socket[0], socket[1], sx, sy, theta, pivot[0] - ox, pivot[1] - oy)


CAPTIONS = False  # STYLE LOCK: user does NOT want on-screen subtitles


class ScenesAR:
    D = 12.5

    def character(self, cv, t, X, gy, sc, walk, talk, mouth_open, gest):
        Ls = {k: get_layer('ar_' + k) for k in ('head', 'torso', 'arm_l', 'arm_r', 'fore_l', 'fore_r', 'leg_l', 'leg_r')}
        ph = 2 * math.pi * 1.1 * t
        bob = abs(math.sin(ph)) * 7 * walk; sway = math.sin(ph) * 2.0 * walk
        breath = 0.012 * math.sin(t * 2.2)
        root = M3(X, gy - 497 * sc - bob * sc * 0.0, sc, sc, sway * 0.5, HIPS[0], HIPS[1]) @ M3(0, -bob, 1, 1, 0, 0, 0)
        shadow = np.zeros((H, W), np.float32); cv2.ellipse(shadow, (int(X), int(gy)), (int(190 * sc), int(32 * sc)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
        shadow = cv2.GaussianBlur(shadow, (0, 0), 6 * sc + 2)[..., None]; cv[:] = cv * (1 - 0.55 * shadow)
        # legs (behind)
        for side, name, sock, piv in (('l', 'leg_l', (468, 640), (1025, 225)), ('r', 'leg_r', (558, 640), (1253, 230))):
            th = (15 * math.sin(ph) * (1 if side == 'l' else -1)) * walk + (2 if side == 'l' else -2) * (1 - walk) * math.sin(t * 0.8)
            place(cv, Ls[name], pm(root, name, sock, piv, th))
        TF = root @ M3(HIPS[0], HIPS[1], 1, 1 + breath, sway * 0.6, HIPS[0], HIPS[1])
        # head
        hn = 2.0 * math.sin(t * 1.7) + talk * 2.6 * math.sin(2 * math.pi * 1.6 * t) + 2.0 * math.sin(ph) * walk
        HM = pm(TF, 'head', (513, 302), (517, 250), hn)
        place(cv, Ls['head'], HM)
        ml = mouth_layer() if not _ml else _ml[0]
        if not _ml: _ml.append(ml)
        mo = 0.08 + 0.92 * mouth_open
        if mouth_open > 0.02:
            place(cv, ml, HM @ M3(72 + 1, 148 - 4, 0.64, 0.5 * mo, 0, ml.w / 2, ml.h * 0.42))
        place(cv, Ls['torso'], TF @ M3(360, 270, 1, 1, 0, 0, 0))
        # arms
        aw = math.sin(ph) * 12 * walk
        for side, an, fn, sock, piv, elb, fpiv, sgn in (('l', 'arm_l', 'fore_l', (388, 338), (221, 275), (56, 190), (51, 5), 1), ('r', 'arm_r', 'fore_r', (638, 338), (797, 278), (67, 188), (51, 5), -1)):
            if side == 'r': a_t = -aw * 1.0 - (22 + 18 * gest) * (1 - walk) * talk - 3 * math.sin(t * 1.3) * (1 - talk); f_t = -(95 * gest + 10) * talk + 6 * math.sin(t * 1.9) * (1 - talk) - 8 * walk
            else: a_t = aw + 3 + 2 * math.sin(t * 1.1 + 1) + talk * 6 * math.sin(t * 2.0); f_t = 4 + 4 * math.sin(t * 1.5) + 14 * walk * max(0, math.sin(ph + 1.2)) + talk * 10 * (0.5 + 0.5 * math.sin(t * 2.3))
            A = pm(TF, an, sock, piv, a_t)
            F = A @ M3(elb[0], elb[1], 1, 1, f_t, fpiv[0], fpiv[1])
            place(cv, Ls[fn], F); place(cv, Ls[an], A)
        return HM

    def face_mark(self, cv, HM, sc):
        """signature: B&W circular filter around the face + black bar over the eyes"""
        c = pt_(HM, 71, 112); R = 128 * sc
        mask = np.zeros((H, W), np.float32); cv2.circle(mask, (int(c[0]), int(c[1])), int(R), 1.0, -1, cv2.LINE_AA)
        mask = cv2.GaussianBlur(mask, (0, 0), 0.8)[..., None]
        g = cv[..., :3].mean(axis=2, keepdims=True); g = np.clip((g - 118) * 1.35 + 118, 0, 255); gray = np.repeat(g, 3, axis=2)
        cv[:] = cv * (1 - mask) + gray * mask
        cv2.circle(cv, (int(c[0]), int(c[1])), int(R), (14.0, 14.0, 14.0), max(2, int(4.5 * sc * 2.2)), cv2.LINE_AA)
        cv2.circle(cv, (int(c[0]), int(c[1])), int(R - 3 * sc * 2.2), (245.0, 245.0, 245.0), max(1, int(2.5 * sc * 2.2)), cv2.LINE_AA)
        pts = np.array([pt_(HM, 12, 72), pt_(HM, 132, 72), pt_(HM, 132, 108), pt_(HM, 12, 108)], np.int32)
        cv2.fillConvexPoly(cv, pts, (6.0, 6.0, 6.0), cv2.LINE_AA)

    def frame(self, t, cv):
        # ---- alley plate in depth layers: base / foreground walls / swinging lantern
        k = sstep(seg(t, 0, self.D))
        sb, sw_ = lerp(1.0, 1.08, k), lerp(1.0, 1.22, k)
        vs = (VP[0] * BGF + 6 * math.sin(t * 0.3), VP[1] * BGF)
        Mb = M3(vs[0], vs[1], BGF * sb, BGF * sb, 0, VP[0], VP[1])
        place(cv, get_layer('ar_bg'), Mb, gain=0.97)
        walk = 1 - sstep(seg(t, 3.9, 4.6)); talk = sstep(seg(t, 4.2, 4.8))
        e = ease_out(seg(t, 0.4, 4.4)); sc = lerp(0.17, 0.50, e); gy = lerp(520, 705, e); X = lerp(700, 640, e)
        # speech rhythm for the mouth (placeholder until the Arabic narration arrives)
        spk = 1.0 if (4.4 < t < 7.2 or 7.8 < t < 11.4) else 0.0
        syl = abs(math.sin(2 * math.pi * 3.4 * t + 0.8 * math.sin(t * 1.3))) ** 0.8
        mo = spk * clamp(0.25 + 0.9 * syl) * (0.7 + 0.3 * math.sin(t * 7.0))
        gest = 0.5 + 0.5 * math.sin(2 * math.pi * 0.55 * t)
        HM = self.character(cv, t, X, gy, sc, walk, talk * (1 if spk or True else 0), mo, gest)
        place(cv, get_layer('ar_wall_l'), M3(vs[0], vs[1], BGF * sw_, BGF * sw_, 0, VP[0], VP[1]), gain=0.97)
        place(cv, get_layer('ar_wall_r'), M3(vs[0], vs[1], BGF * sw_, BGF * sw_, 0, VP[0], VP[1]), gain=0.97)
        Ml = M3(vs[0], vs[1], BGF * (sw_ + sb) / 2, BGF * (sw_ + sb) / 2, 0, VP[0], VP[1])
        lant = Ml @ M3(615, 200, 1, 1, 3.0 * math.sin(t * 1.6), 615 - 572, 200 - 190)
        place(cv, get_layer('ar_lantern'), lant @ M3(0, 0, 1, 1, 0, 0, 0) if False else lant)
        lb = LightBuf(); q = pt_(lant, 43, 70); fl = 0.9 + 0.1 * math.sin(t * 9) * math.sin(t * 2.3)
        lb.glow(q[0], q[1], 40, (110, 190, 255), 0.7 * fl); lb.glow(q[0], q[1], 240, (60, 130, 220), 0.35 * fl); lb.apply(cv, blur=26)
        self.face_mark(cv, HM, sc)
        # dust in the light
        r = rng(4)
        for i in range(36):
            x = (r.random() * W + t * (4 + 8 * r.random())) % W; y = (r.random() * H * 0.8 + 12 * math.sin(t * 0.7 + i)) % H
            c = 150 + 80 * r.random(); cv2.circle(cv, (int(x), int(y)), 1, (c * 0.8, c * 0.95, c), -1, cv2.LINE_AA)
        if not CAPTIONS: return cv
        sh_ = np.linspace(0, 1, 210, dtype=np.float32)[:, None, None] ** 1.6 * 0.72 * sstep(seg(t, 4.2, 4.8)); cv[H - 210:] *= (1 - sh_)
        # Arabic captions, gold, wiped in right -> left
        for (s, t0, t1, t2) in (('هذا اختبار لأسلوب الرسم الزيتي', 4.4, 6.6, 7.6), ('كل جزء من الشخصية يتحرك بنظام الطبقات', 7.9, 10.8, 12.0)):
            if t0 <= t < t2 + 0.2:
                a = ar_text_layer(s); h_, w_ = a.shape; reveal = seg(t, t0, t1); x0 = (W - w_) // 2; y0 = H - 135
                cut = int(w_ * (1 - reveal)); m = a.copy(); m[:, :cut] = 0
                fade = 1 - seg(t, t2, t2 + 0.2)
                roi = cv[y0:y0 + h_, x0:x0 + w_]
                dk = np.clip(m * 2, 0, 1)[..., None] * 0.85 * fade; gd = np.clip((m - 0.5) * 2, 0, 1)[..., None] * fade
                roi *= (1 - dk); roi += (np.array((75, 170, 232), np.float32) - roi) * gd
        return cv


def pt_(M, x, y):
    q = M @ np.array([x, y, 1.0]); return float(q[0]), float(q[1])
