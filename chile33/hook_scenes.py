"""Part 1 'hook' (Arabic narration, 53.9 s) - oil-painted layered puppets, STYLE LOCK (see STYLE_LOCK_AR.md).
Every character part is its own RGBA layer on a bone rig; every character carries the signature face mark; NO captions."""
import cv2, math, json, numpy as np
from engine import *

D = 53.9
S0 = 720 / 768.0                     # plate -> screen (cover)
OX, OY = (1376 * S0 - W) / 2, 0.0
HIPS = (513, 640)
OFF_AR = {'head': (446, 35), 'torso': (360, 270), 'arm_l': (166, 262), 'arm_r': (733, 270), 'fore_l': (175, 467), 'fore_r': (755, 463), 'leg_l': (934, 209), 'leg_r': (1150, 214), 'mouth': (667, 152)}
OFFS = json.load(open('data/offs.json')); OFFS['ar'] = OFF_AR
RIG = {'ar': dict(sock=(513, 302), piv=(517, 250), ring=(517, 147), bar=(458, 107, 578, 143), mouth=(519, 179)),
       'm': dict(sock=(513, 302), piv=(517, 250), ring=(517, 147), bar=(458, 107, 578, 143), mouth=(519, 179)),
       'w': dict(sock=(516, 312), piv=(520, 258), ring=(520, 152), bar=(458, 113, 582, 149), mouth=(522, 187))}

_c = {}
def L(name):
    if name not in _c: _c[name] = Layer(name)
    return _c[name]


def pt_(M, x, y):
    q = M @ np.array([x, y, 1.0]); return float(q[0]), float(q[1])


_ml = {}
def mouth_layer(ch):
    if ch not in _ml:
        Lm = L(f'{ch}_mouth' if ch != 'ar' else 'ar_mouth'); im = Lm.img.copy(); h, w = im.shape[:2]
        m = np.zeros((h, w), np.float32); cv2.ellipse(m, (w // 2, int(h * 0.42)), (int(w * 0.40), int(h * 0.30)), 0, 0, 360, 1.0, -1); m = cv2.GaussianBlur(m, (0, 0), 2.5)
        im *= m[..., None]; _ml[ch] = Layer.from_array(im)
    return _ml[ch]


def pm(frame, ch, name, socket, pivot, theta=0.0):
    ox, oy = OFFS[ch][name]; return frame @ M3(socket[0], socket[1], 1, 1, theta, pivot[0] - ox, pivot[1] - oy)


def shadow(cv, X, gy, sc, a=0.55):
    rx, ry = 190 * sc, 32 * sc
    x0 = int(max(0, X - rx - 14)); x1 = int(min(W, X + rx + 14)); y0 = int(max(0, gy - ry - 14)); y1 = int(min(H, gy + ry + 14))
    if x1 <= x0 or y1 <= y0: return
    m = np.zeros((y1 - y0, x1 - x0), np.float32); cv2.ellipse(m, (int(X - x0), int(gy - y0)), (max(1, int(rx)), max(1, int(ry))), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 6 * sc + 2)[..., None]; cv[y0:y1, x0:x1] *= (1 - a * m)


LASTHAND = {}   # (char, 'l'|'r') -> screen position of the hand (set by draw_char)
BARE_ARMS = set()   # characters whose upper arms are bare skin (no shirt tint)
FACE_MARK = True   # set False for projects without the signature (Prosperi video onwards: user decision)


def face_mark(cv, HM, ch, sc):
    if not FACE_MARK: return
    """SIGNATURE: B&W circular filter around the whole face (black + white rings) and a black bar over the eyes. On every character."""
    R = RIG[ch]; ox, oy = OFFS[ch]['head']
    c = pt_(HM, R['ring'][0] - ox, R['ring'][1] - oy); r = 128 * sc
    x0 = int(max(0, c[0] - r - 8)); x1 = int(min(W, c[0] + r + 8)); y0 = int(max(0, c[1] - r - 8)); y1 = int(min(H, c[1] + r + 8))
    if x1 <= x0 or y1 <= y0: return
    roi = cv[y0:y1, x0:x1]; cc = (int(c[0] - x0), int(c[1] - y0))
    mask = np.zeros(roi.shape[:2], np.float32); cv2.circle(mask, cc, int(r), 1.0, -1, cv2.LINE_AA); mask = cv2.GaussianBlur(mask, (0, 0), 0.8)[..., None]
    g = roi[..., :3].mean(axis=2, keepdims=True); g = np.clip((g - 118) * 1.35 + 118, 0, 255); gray = np.repeat(g, 3, axis=2)
    roi[:] = roi * (1 - mask) + gray * mask
    cv2.circle(roi, cc, int(r), (14.0, 14.0, 14.0), max(2, int(4.5 * sc * 2.2)), cv2.LINE_AA)
    cv2.circle(roi, cc, int(r - 3 * sc * 2.2), (245.0, 245.0, 245.0), max(1, int(2.5 * sc * 2.2)), cv2.LINE_AA)
    bx0, by0, bx1, by1 = R['bar']
    pts = np.array([pt_(HM, bx0 - ox, by0 - oy), pt_(HM, bx1 - ox, by0 - oy), pt_(HM, bx1 - ox, by1 - oy), pt_(HM, bx0 - ox, by1 - oy)], np.float64)
    pts = (pts - np.array([x0, y0])).astype(np.int32)
    cv2.fillConvexPoly(roi, pts, (6.0, 6.0, 6.0), cv2.LINE_AA)


def draw_char(cv, ch, t, X, gy, sc, walk=0.0, ph0=0.0, pose=None, mouth=0.0, flip=1, gain=1.0, tint=None, crouch=0.0, sway_amp=1.0, shirt=None, pants=None, hs=1.0, rot=0.0, dy=0.0):
    """layered puppet: legs, torso, head, arms+forearms - every part is a separate layer moved by its own joint"""
    P = pose or {}; R = RIG[ch]
    Ls = {k: L(f'{ch}_{k}') for k in ('head', 'torso', 'arm_l', 'arm_r', 'fore_l', 'fore_r', 'leg_l', 'leg_r')}
    ph = 2 * math.pi * 1.1 * t + ph0
    bob = abs(math.sin(ph)) * 7 * walk; sway = math.sin(ph) * 2.0 * walk * sway_amp
    breath = 0.012 * math.sin(t * 2.2 + ph0)
    sy = sc * (1 - 0.12 * crouch)
    root = M3(X, gy - 497 * sy + dy, sc * flip, sy, sway * 0.5 + P.get('lean', 0) * 0.4 + rot, HIPS[0], HIPS[1]) @ M3(0, -bob, 1, 1, 0, 0, 0)
    shadow(cv, X, gy, sc)
    def mul(a, b): return a if b is None else (b if a is None else tuple(x * y for x, y in zip(a, b)))
    kw = dict(gain=gain, tint=tint); kws = dict(gain=gain, tint=mul(tint, shirt)); kwp = dict(gain=gain, tint=mul(tint, pants))
    for side, name, sock, piv in (('l', 'leg_l', (468, 640), (1025, 225)), ('r', 'leg_r', (558, 640), (1253, 230))):
        th = (15 * math.sin(ph) * (1 if side == 'l' else -1)) * walk + (2 if side == 'l' else -2) * (1 - walk) * math.sin(t * 0.8 + ph0)
        place(cv, Ls[name], pm(root, ch, name, sock, piv, th), **kwp)
    TF = root @ M3(HIPS[0], HIPS[1], 1, 1 + breath, sway * 0.6 + P.get('lean', 0), HIPS[0], HIPS[1])
    hn = 2.0 * math.sin(t * 1.7 + ph0) + 2.0 * math.sin(ph) * walk + P.get('head', 0.0)
    ox_, oy_ = OFFS[ch]['head']; HM = TF @ M3(R['sock'][0], R['sock'][1], hs, hs, hn, R['piv'][0] - ox_, R['piv'][1] - oy_)
    place(cv, Ls['head'], HM, **kw)
    if mouth > 0.02:
        ml = mouth_layer(ch); mo = 0.08 + 0.92 * mouth; ox, oy = OFFS[ch]['head']
        place(cv, ml, HM @ M3(R['mouth'][0] - ox, R['mouth'][1] - oy, 0.64, 0.5 * mo, 0, ml.w / 2, ml.h * 0.42), **kw)
    tox, toy = OFFS[ch]['torso']; place(cv, Ls['torso'], TF @ M3(tox, toy, 1, 1, 0, 0, 0), **kws)
    sw = 8 * walk * math.sin(ph)
    for side, an, fn, sock, piv, elb_s, fp_s in (('l', 'arm_l', 'fore_l', (388, 338), (221, 275), (222, 452), (226, 472)), ('r', 'arm_r', 'fore_r', (638, 338), (797, 278), (800, 458), (806, 468))):
        aoff, foff = OFFS[ch][an], OFFS[ch][fn]
        elb = (elb_s[0] - aoff[0], elb_s[1] - aoff[1]); fp = (fp_s[0] - foff[0], fp_s[1] - foff[1])
        if side == 'l':
            raise_a = 3 + 2 * math.sin(t * 1.1 + 1 + ph0) + P.get('aL', 0.0); raise_f = 4 + 4 * math.sin(t * 1.5 + ph0) + 14 * walk * max(0, math.sin(ph + 1.2)) + P.get('fL', 0.0)
            a_t = raise_a + sw; f_t = raise_f
        else:
            raise_a = 3 + 2 * math.sin(t * 1.3 + ph0) + P.get('aR', 0.0); raise_f = 6 * math.sin(t * 1.9 + ph0) + 8 * walk * max(0, math.sin(ph + 4.0)) + P.get('fR', 0.0)
            a_t = -raise_a + sw; f_t = -raise_f
        A = pm(TF, ch, an, sock, piv, a_t)
        F = A @ M3(elb[0], elb[1], 1, 1, f_t, fp[0], fp[1])
        LASTHAND[(ch, side)] = pt_(F, Ls[fn].w * 0.5, Ls[fn].h * 0.92)
        place(cv, Ls[fn], F, **kw); place(cv, Ls[an], A, **(kw if ch in BARE_ARMS else kws))
    face_mark(cv, HM, ch, sc * hs)
    return HM


# ------------------------------------------------------------------ camera + plates
class Cam:
    def __init__(self, A=(640, 360), sb=1.0, sw=1.0, sc=1.0, d=(0.0, 0.0), dw=None):
        self.A, self.sb, self.sw, self.sc, self.d = A, sb, sw, sc, d; self.dw = dw if dw is not None else d

    def pt(self, x, y):
        return self.A[0] + (x - self.A[0]) * self.sc + self.d[0], self.A[1] + (y - self.A[1]) * self.sc + self.d[1]

    def Mp(self, s, d):
        pa = ((self.A[0] + OX) / S0, (self.A[1] + OY) / S0)
        return M3(self.A[0] + d[0], self.A[1] + d[1], S0 * s, S0 * s, 0, pa[0], pa[1])


def plate(cv, name, cam, kind='b', gain=1.0):
    s, d = (cam.sb, cam.d) if kind == 'b' else (cam.sw, cam.dw)
    place(cv, L(name), cam.Mp(s, d), gain=gain)


_noise = []
def noise_tex():
    if not _noise:
        r = rng(5); n = r.normal(0, 1, (36, 64)).astype(np.float32); n = cv2.resize(n, (2000, 1125), interpolation=cv2.INTER_CUBIC)
        n = cv2.GaussianBlur(n, (0, 0), 14); n = (n - n.min()) / (n.max() - n.min()); _noise.append(n)
    return _noise[0]


def veil(cv, T, alpha, color=(92, 135, 178), speed=30):
    if alpha <= 0.004: return
    n = noise_tex(); ox = int(300 + 160 * math.sin(T * 0.37) + T * speed % 200); oy = int(200 + 100 * math.cos(T * 0.29))
    crop = n[oy:oy + H, ox:ox + W]; a = np.clip(alpha * (0.82 + 0.36 * crop), 0, 0.93)[..., None]
    cv *= (1 - a); cv += np.array(color, np.float32) * a


def motes(cv, T, seed, n=40, amp=1.0, col=(195, 220, 245), y1=0.85):
    r = rng(seed)
    for i in range(n):
        x = (r.random() * W + T * (4 + 9 * r.random()) * amp) % W; y = (r.random() * H * y1 + 14 * math.sin(T * 0.7 + i)) % H
        c = 140 + 90 * r.random(); cv2.circle(cv, (int(x), int(y)), 1 + int(r.random() > 0.8), (c * col[0] / 255, c * col[1] / 255, c * col[2] / 255), -1, cv2.LINE_AA)


def shake_xy(T, A):
    return A * (math.sin(T * 41.0) + 0.7 * math.sin(T * 67.0 + 1.3) + 0.4 * math.sin(T * 23.0 + 0.4)) / 2.1, A * 0.8 * (math.sin(T * 53.0 + 2.0) + 0.6 * math.sin(T * 31.0 + 0.7)) / 1.6


def flick(T, seed=0):
    return 0.5 + 0.5 * (0.5 * math.sin(T * 9.1 + seed) + 0.3 * math.sin(T * 17.3 + seed * 2) + 0.2 * math.sin(T * 3.7))


# ------------------------------------------------------------------ crews
SHIRTS = [None, (0.72, 1.12, 1.0), (0.85, 0.88, 1.12), (0.9, 0.95, 0.98), (0.78, 1.0, 1.1), None, (0.7, 0.9, 1.0), (0.95, 1.1, 1.0), (0.82, 0.92, 1.05), (0.75, 1.05, 1.0)]
PANTS = [None, (1.25, 1.05, 0.85), (0.8, 0.85, 0.9), (1.4, 1.2, 1.0), None, (1.0, 1.15, 1.3), (0.85, 0.95, 1.1), (1.3, 1.1, 0.9), None, (0.9, 1.0, 1.1)]
def mkcrew(spec):
    out = []
    for i, s in enumerate(spec):
        d = dict(zip(('ch', 'x', 'gy', 'sc', 'flip', 'gain', 'ph0'), s)); d['shirt'] = SHIRTS[(i * 3) % len(SHIRTS)] if d['ch'] == 'm' else None
        d['pants'] = PANTS[(i * 7 + 2) % len(PANTS)] if d['ch'] == 'm' else None; d['sc'] *= 1 + 0.05 * (((i * 5) % 4) - 1.5) / 1.5; out.append(d)
    return out


CHAMBER = mkcrew([('m', 300, 600, .27, 1, .95, 0.3), ('m', 470, 598, .27, -1, 1.0, 1.1), ('m', 900, 600, .27, 1, 1.0, 2.0), ('m', 1070, 602, .27, -1, .92, 0.6),
                  ('m', 190, 652, .34, -1, 1.0, 2.7), ('m', 395, 650, .34, 1, .96, 3.3), ('m', 985, 652, .34, 1, .98, 1.7),
                  ('m', 130, 712, .43, 1, 1.0, 5.0), ('m', 1090, 712, .43, -1, .95, 2.4)])
GATHER = [(540, 610, .27), (620, 612, .27), (740, 610, .27), (820, 612, .27), (470, 655, .34), (680, 660, .34), (890, 655, .34), (570, 705, .42), (800, 706, .42)]
SURFACE = mkcrew([('w', 380, 610, .22, 1, 1.0, .2), ('ar', 520, 612, .22, 1, 1.0, 1.1), ('w', 660, 608, .22, -1, .96, 2.2), ('m', 800, 612, .22, 1, 1.0, 3.1), ('w', 940, 610, .22, -1, 1.0, 0.7),
                  ('w', 250, 722, .45, 1, 1.0, 1.4), ('ar', 500, 726, .45, -1, 1.0, 2.6), ('w', 800, 722, .45, 1, .97, 3.7), ('m', 1040, 726, .45, -1, 1.0, 0.4)])
EXT = [dict(ch='m', xe=380, ge=662, t0=0.5, dur=2.5, flip=1, gain=1.0, ph0=0.0), dict(ch='m', xe=610, ge=702, t0=1.2, dur=2.5, flip=-1, gain=.96, ph0=1.5),
       dict(ch='m', xe=850, ge=690, t0=1.9, dur=2.5, flip=1, gain=1.04, ph0=2.9), dict(ch='m', xe=1050, ge=655, t0=2.6, dur=2.4, flip=-1, gain=1.0, ph0=4.2)]
_ends = [(480, 548, 0), (570, 546, 1), (660, 548, 2), (750, 546, 3), (840, 548, 4), (360, 690, 5), (540, 694, 6), (720, 690, 7), (900, 694, 8)]
TUN = []
for i, (xe, ge, k) in enumerate(_ends):
    TUN.append(dict(ch='m', xe=xe, ge=ge, t0=4.85 + 0.2 * i, dur=1.9 + 0.1 * (i > 4), flip=1 if i % 2 == 0 else -1, gain=(.94, 1.0, 1.05, .97)[i % 4], ph0=i * 1.3, d=0.04 * ((i * 7) % 5)))


def walker(T, c, vp, hor, k):
    """character that walks from vp to (xe, ge); returns x, gy, sc, walk"""
    s = clamp((T - c['t0']) / c['dur']); u = 1 - (1 - s) ** 1.5
    X = lerp(vp[0], c['xe'], u); gy = lerp(vp[1], c['ge'], u); sc = k * (gy - hor)
    walk = 1.0 if T < c['t0'] else (1 - sstep(seg(T, c['t0'] + c['dur'], c['t0'] + c['dur'] + 0.4)))
    return X, gy, max(0.02, sc), walk, s > 0 or T >= c['t0']


# ------------------------------------------------------------------ shots
def shot_exterior(cv, T):
    k = ease_out(seg(T, 0, 5.0)) * 0.8 + seg(T, 0, 5.0) * 0.2
    cam = Cam(A=(560, 470), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.28, k), sc=lerp(1.0, 1.15, k), d=(-8 * k, 0), dw=(-14 * k, -6 * k))
    plate(cv, 'h_p1', cam, 'b'); plate(cv, 'h_p1_gr', cam, 'w')
    cv[:] = heat_haze(cv, T, 1.4, 0.05, 2.5, 380, 560)
    items = []
    for c in EXT:
        X, gy, sc, walk, on = walker(T, c, (610, 495), 410, 0.00145)
        if on: items.append((gy, c, X, gy, sc, walk))
    for _, c, X, gy, sc, walk in sorted(items, key=lambda a: a[0]):
        Xc, Yc = cam.pt(X, gy); breath_look = 6 * math.sin(T * 1.2 + c['ph0']) * (1 - walk)
        pose = {'head': breath_look, 'aL': 6 * (1 - walk) * max(0, math.sin(T * 1.4 + c['ph0'])) * 4}
        draw_char(cv, c['ch'], T, Xc, Yc, sc * cam.sc, walk=walk, ph0=c['ph0'], pose=pose, flip=c['flip'], gain=c['gain'] * 1.02, shirt=SHIRTS[(c['ph0'] > 1) * 3 + 1], pants=PANTS[int(c['ph0']) % 9 + 1])
    lb = LightBuf(); lb.glow(120, 90, 330, (90, 160, 255), 0.55); lb.glow(560, 300, 380, (60, 120, 220), 0.25); lb.apply(cv, blur=40)
    motes(cv, T, 7, 46, 1.4)


def draw_lamp(cv, cam, lampname, box, pivot, bulb, ang, T, glow=1.0):
    Mp = cam.Mp(0.5 * (cam.sb + cam.sw), (cam.d[0] * 0.5 + cam.dw[0] * 0.5, cam.d[1] * 0.5 + cam.dw[1] * 0.5))
    lm = Mp @ M3(pivot[0], pivot[1], 1, 1, ang, pivot[0] - box[0], pivot[1] - box[1])
    place(cv, L(lampname), lm)
    return pt_(lm, bulb[0] - box[0], bulb[1] - box[1])


def rock_events():
    r = rng(11); ev = []
    for i in range(54):
        t0 = 8.72 + (r.random() ** 1.3) * 3.4; x = 60 + r.random() * (W - 120); yf = 500 + r.random() * 230
        sc = (0.10 + 0.26 * (yf - 500) / 230) * (0.7 + 0.7 * r.random()); ev.append(dict(t0=t0, x=x, yf=yf, sc=sc, spr=int(r.integers(0, 8)), rot=r.random() * 360, spin=(r.random() - .5) * 700))
    return ev


ROCKS = rock_events()


def draw_rocks(cv, T, front):
    for e in ROCKS:
        dt = T - e['t0']
        if dt < 0: continue
        g = 1500.0; tf = math.sqrt(2 * (e['yf'] + 120) / g)
        if dt < tf: y = -120 + 0.5 * g * dt * dt; landed = False; rot = e['rot'] + e['spin'] * dt
        else: bt = dt - tf; y = e['yf'] - 14 * abs(math.sin(bt * 9)) * math.exp(-bt * 5); landed = True; rot = e['rot'] + e['spin'] * tf
        if landed == front: continue
        lyr = L(f"rock_{e['spr']}"); place(cv, lyr, M3(e['x'], y, e['sc'], e['sc'], rot, lyr.w / 2, lyr.h / 2), gain=0.82)


def shot_tunnel(cv, T):
    VP = (656, 412); k_ = 0.00126; hor = 407
    # ---------------- camera + quake
    A = 0.0
    if T >= 7.78: A = 1.6 * sstep(seg(T, 7.78, 8.5))
    if T >= 8.72: A = 17.0 * math.exp(-0.55 * (T - 8.72)) + 2.5
    if T >= 12.6: A *= 1 - sstep(seg(T, 12.6, 14.6)) * 0.9
    after = T >= 9.15
    dxy = shake_xy(T, A)
    kk = seg(T, 4.8, 18.5)
    push = 0.10 * sstep(seg(T, 4.8, 9)) + 0.04 * sstep(seg(T, 13.9, 18.4))
    p2 = sstep(seg(T, 14.6, 18.4))
    cam = Cam(A=(700, 330), sb=1.0 + push * 0.8 + p2 * 0.22, sw=1.0 + push * 2.0 + p2 * 0.5, sc=1.0 + push * 1.3 + p2 * 0.9, d=dxy, dw=(dxy[0] * 1.5, dxy[1] * 1.5))
    base, wl, wr = ('h_p3', 'h_p3_wl', 'h_p3_wr') if after else ('h_p2', 'h_p2_wl', 'h_p2_wr')
    bright = 1.0
    if 8.72 <= T < 12.4: bright = 0.82 + 0.18 * flick(T, 3.0)
    plate(cv, base, cam, 'b', gain=bright)
    lamp_ang = 3.0 * math.sin(T * 1.6) + (A * 1.6) * math.sin(T * 5.5)
    if after: bq = draw_lamp(cv, cam, 'h_p3_lamp', (488, 66, 578, 266), (530, 74), (531, 210), lamp_ang, T)
    else: bq = draw_lamp(cv, cam, 'h_p2_lamp', (668, 120, 744, 214), (706, 125), (706, 172), lamp_ang, T)
    plate(cv, wl, cam, 'w', gain=bright); plate(cv, wr, cam, 'w', gain=bright)
    # fallen rocks behind characters
    draw_rocks(cv, T, front=False)
    # ---------------- crew (world positions, pushed with the camera)
    items = []
    for i, c in enumerate(TUN):
        X, gy, sc, walk, on = walker(T, c, VP, hor, k_)
        if not on: continue
        d = c['d']; pose = {'head': 0.0}; crouch = 0.0
        if T >= 7.78:
            al = sstep(seg(T, 7.78 + d, 8.5 + d)); pose['head'] = 7 * math.sin((T - 7.78) * 6 + i) * al; pose['aL'] = pose['aR'] = 16 * al; crouch = 0.1 * al
        if T >= 8.80 + d:
            e = sstep(seg(T, 8.80 + d, 9.15 + d)) * (1 - sstep(seg(T, 13.9 + d * 2, 15.4 + d * 2)))
            pose['aL'] = pose['aR'] = 16 + 120 * e; pose['fL'] = pose['fR'] = 110 * e; crouch = 0.1 + 0.5 * e; pose['head'] = 14 * e * math.sin(T * 30 + i) * 0.0 + 10 * e; pose['lean'] = 0
        if T >= 14.6:
            r = sstep(seg(T, 14.6 + d, 15.4 + d)); pose['head'] = (-4 + 5 * ((i * 5) % 3 - 1)) * r + 3 * math.sin(T * 1.1 + i)
            if i % 3 == 0: pose['aL'] = 24 * r; pose['fL'] = 20 * r
            if i % 3 == 1: pose['aR'] = 35 * r * (0.5 + 0.5 * math.sin(T * 0.8 + i)); pose['fR'] = 60 * r
            if i in (1, 5) and T > 16.0: pose['aR' if i == 1 else 'aL'] = 70 * sstep(seg(T, 16.2, 16.9)); pose['fR' if i == 1 else 'fL'] = -10
        items.append((gy, i, c, X, gy, sc, walk, pose, crouch))
    for _, i, c, X, gy, sc, walk, pose, crouch in sorted(items, key=lambda a: a[0]):
        Xc, Yc = cam.pt(X, gy)
        draw_char(cv, 'm', T, Xc, Yc, sc * cam.sc, walk=walk, ph0=c['ph0'], pose=pose, flip=c['flip'], gain=c['gain'] * 0.9, tint=(0.92, 1.0, 1.08), crouch=crouch, shirt=SHIRTS[(i * 3) % len(SHIRTS)], pants=PANTS[(i * 7 + 2) % len(PANTS)])
    draw_rocks(cv, T, front=True)
    # ---------------- light
    lb = LightBuf(); fl = (0.9 + 0.1 * math.sin(T * 9) * math.sin(T * 2.3)) * (0.75 + 0.25 * flick(T, 1.0) if 8.72 < T < 12.4 else 1.0)
    lb.glow(bq[0], bq[1], 50, (110, 190, 255), 0.75 * fl); lb.glow(bq[0], bq[1], 300, (60, 130, 230), 0.38 * fl)
    if not after:
        for (px, py, r_) in ((706, 286, 22), (702, 322, 14)):
            q = cam.pt(S0 * px - OX, S0 * py - OY); lb.glow(q[0], q[1], r_, (110, 190, 255), 0.5)
    lb.apply(cv, blur=26)
    # ---------------- dust
    puffs(cv, T, 7.9, 9.0, 14, (200, 0, 880, 160), (95, 135, 178), seed=21, size=(80, 200), rise=(-40, -10), life=2.6, alpha=0.35)
    puffs(cv, T, 8.8, 12.4, 34, (150, 520, 980, 200), (100, 142, 184), seed=22, size=(120, 300), rise=(10, 70), life=3.0, alpha=0.5)
    motes(cv, T, 9, 30)
    vl = 0.0
    if T < 9.3: vl = 0.15 * sstep(seg(T, 8.0, 8.7)) + 0.85 * sstep(seg(T, 8.72, 9.12))
    elif T < 12.2: vl = 0.9 - 0.6 * sstep(seg(T, 9.3, 10.8)) + 0.0
    elif T < 13.86: vl = 0.3 + 0.62 * sstep(seg(T, 12.2, 13.4))
    else: vl = 0.92 * (1 - sstep(seg(T, 13.86, 16.0)))
    veil(cv, T, vl)
    if T > 16.0: veil(cv, T, 0.10 * (1 - sstep(seg(T, 17.8, 18.5))) * 1.0)


def shot_depth(cv, T, t0, t1, rev=False):
    k = sstep(seg(T, t0, t1)); sS = 1.75 * S0
    ph = k
    y_top = 0; y_bot = 768 * sS - H
    oy = lerp(y_top, y_bot, ph); ox = (1376 * sS - W) / 2 + 40 * math.sin(T * 0.4) + lerp(40, -60, k)
    zoom = 1.0 + 0.10 * sstep(seg(T, t1 - 1.2, t1))
    Mz = M3(W / 2, H / 2, zoom, zoom, 0, W / 2, H / 2) @ M3(-ox, -oy, sS, sS, 0, 0, 0)
    place(cv, L('h_p4'), Mz, gain=0.95)
    r = rng(31)
    for i in range(70):   # falling grit under pressure
        x = r.random() * W; sp = 14 + 30 * r.random(); y = ((r.random() * H) + T * sp) % H; c = 120 + 100 * r.random()
        cv2.circle(cv, (int(x), int(y)), 1, (c * .7, c * .85, c), -1, cv2.LINE_AA)
    vignette(cv, 0.35 + 0.35 * k, 2.0)
    lb = LightBuf(); gl = sstep(seg(T, t0 + (t1 - t0) * 0.55, t1)); lb.glow(560, 690, 200, (60, 130, 255), 0.6 * gl); lb.apply(cv, blur=40)


def pulse(T, a, b): return math.sin(math.pi * clamp((T - a) / (b - a))) ** 1.2 if a <= T <= b else 0.0


def shot_chamber(cv, T, G=False):
    if not G:
        k = seg(T, 21.43, 29.05); fz = sstep(seg(T, 25.8, 28.8))
        cam = Cam(A=(680, 640), sb=lerp(1.0, 1.08, k) + 0.28 * fz, sw=lerp(1.0, 1.2, k) + 0.4 * fz, sc=lerp(1.0, 1.12, k) + 0.5 * fz, d=(0, 0), dw=(0, 0))
        dark = lerp(0.22, 0.78, sstep(seg(T, 21.43, 23.6))) * (1 - 0.0)
    else:
        k = seg(T, 44.0, 53.9); cam = Cam(A=(680, 600), sb=lerp(1.0, 1.16, k), sw=lerp(1.0, 1.36, k), sc=lerp(1.0, 1.24, k), d=(-8 * k, 6 * k), dw=(-14 * k, 10 * k))
        dark = 0.8 + 0.2 * sstep(seg(T, 44.0, 47.0))
    plate(cv, 'h_p6', cam, 'b'); plate(cv, 'h_p6_wl', cam, 'w'); plate(cv, 'h_p6_wr', cam, 'w')
    cv *= dark
    # lamp glow (plate coords) -> screen
    lb = LightBuf(); fl = 0.85 + 0.15 * flick(T, 2.0)
    for (px, py, r_, a) in ((186, 312, 90, 1.0), (561, 328, 110, 1.0), (1079, 352, 90, 1.0)):
        q = cam.pt(S0 * px - OX, S0 * py - OY); lb.glow(q[0], q[1], r_ * cam.sw * 0.5, (90, 170, 255), 0.55 * fl * (1.2 if G else 1.0)); lb.glow(q[0], q[1], 330 * cam.sw, (40, 100, 200), 0.30 * fl * (1.35 if G else 1.0))
    lb.apply(cv, blur=30)
    # food (reveal at 'أما الأكل؟')
    food = [('food_0', 640, 656, .22, 0), ('food_1', 700, 664, .21, .12), ('food_5', 790, 650, .22, .25), ('food_3', 590, 662, .20, .35), ('food_4', 745, 683, .17, .45), ('food_6', 680, 640, .16, .55)]
    if 25.99 <= T < 44.0 or T < 29.05:
        pass
    crew = []
    for i, c in enumerate(CHAMBER):
        X, gy, sc = c['x'], c['gy'], c['sc']; walk = 0.0; pose = {}; crouch = 0.0; mouth = 0.0
        if not G:
            tired = sstep(seg(T, 21.43, 23.0)); crouch = 0.10 * tired; pose['head'] = 6 * tired + 2 * math.sin(T * 0.9 + i)
            wipe = pulse(T, 22.6 + 0.18 * i, 23.7 + 0.18 * i) if i % 2 == 0 else pulse(T, 23.0 + 0.1 * i, 24.0 + 0.1 * i)
            pose['aL'] = 118 * wipe + pose.get('aL', 0); pose['fL'] = 140 * wipe
            if T > 23.96:
                lk = sstep(seg(T, 23.96, 24.4)) * (1 - sstep(seg(T, 25.5, 26.0)))
                pose['head'] = pose['head'] * (1 - lk) + 12 * math.sin(2 * math.pi * 0.7 * (T - 24.0) + i) * lk; pose['aL'] = pose.get('aL', 0) + 14 * lk; pose['aR'] = 14 * lk; pose['fL'] = pose.get('fL', 0) + 6 * lk; pose['fR'] = 6 * lk
            if T > 26.0: pose['head'] = pose['head'] * 0.5 + 14 * sstep(seg(T, 26.0, 26.8))
        else:
            up = sstep(seg(T, 44.06, 45.4)); crouch = 0.10 * (1 - up); pose['head'] = -3 * up + 2 * math.sin(T * 1.3 + i)
            g = sstep(seg(T, 47.6, 51.0)); tx, tg, ts = GATHER[i]
            X = lerp(X, tx, g); gy = lerp(gy, tg, g); sc = lerp(sc, ts, g); walk = 1.0 if 47.6 < T < 51.0 else 0.0
            dn = sstep(seg(T, 51.7, 52.6)); pose['head'] += -9 * dn
            # taking turns to speak while they plan together (silent: voice-over carries the story)
            sp = 0.5 + 0.5 * math.sin(2 * math.pi * 0.28 * (T - 46) + i * 2.1)
            if T > 47.0 and sp > 0.8: mouth = 0.5 + 0.5 * abs(math.sin(T * 9 + i * 3)); pose['aR'] = 18 + 22 * math.sin(T * 3 + i); pose['fR'] = 40 * abs(math.sin(T * 2.2 + i))
            if T > 49.5 and i % 3 == 0: pose['head'] += 6 * math.sin(T * 3.2 + i)
        crew.append((gy, i, c, X, gy, sc, walk, pose, crouch, mouth))
    for _, i, c, X, gy, sc, walk, pose, crouch, mouth in sorted(crew, key=lambda a: a[0]):
        Xc, Yc = cam.pt(X, gy)
        draw_char(cv, 'm', T, Xc, Yc, sc * cam.sc, walk=walk, ph0=c['ph0'], pose=pose, mouth=mouth, flip=c['flip'], gain=c['gain'] * (0.78 if not G else 0.9) * (0.65 + 0.35 * dark), tint=(0.85, 0.96, 1.1), crouch=crouch, shirt=c['shirt'], pants=c['pants'])
        if G: pass
    # food on the floor
    if 25.99 <= T < 29.05:
        for nm, fx, fy, fs, dl in food:
            e = clamp((T - 26.0 - dl) / 0.5)
            if e <= 0: continue
            sq = 1 + 0.25 * math.sin(e * math.pi) * (1 - e) * 2; drop = (1 - ease_out(e)) * -70
            Xc, Yc = cam.pt(fx, fy + drop); lyr = L(nm)
            shadow(cv, Xc, Yc + 4, fs * cam.sc * 0.35, a=0.5)
            place(cv, lyr, M3(Xc, Yc, fs * cam.sc * sq, fs * cam.sc / sq, 0, lyr.w / 2, lyr.h), gain=0.95, tint=(0.95, 1.0, 1.08))
    # atmosphere
    if not G:
        heat = 1.2 * sstep(seg(T, 22.6, 24.0)); cv[:] = heat_haze(cv, T, heat, 0.05, 2.2, 150, 700)
        tone(cv, 1.0, 0, (0.93 + 0.0, 0.97, 1.06 + 0.04 * sstep(seg(T, 22.6, 24.5))), 1.0)
    motes(cv, T, 12, 34, 0.5, (210, 225, 245))
    vignette(cv, 0.4, 2.0)


def surface_n(T):
    """night amount: dusk -> three quick time-lapse day cycles ('a day, two days, a week') -> night vigil"""
    u = 1.0 * seg(T, 33.5, 34.3) + 2.0 * seg(T, 34.4, 35.3) + 7.0 * seg(T, 35.7, 36.7)
    if T < 33.5: return 0.29 * sstep(seg(T, 29.0, 33.4))
    n = 0.5 - 0.5 * math.cos(2 * math.pi * (u + 0.18))
    if T > 36.7: n = lerp(0.29, 0.93, sstep(seg(T, 37.0, 40.2)))
    return n


def shot_surface(cv, T):
    k = seg(T, 29.0, 41.8); cam = Cam(A=(700, 520), sb=lerp(1.0, 1.08, k), sw=lerp(1.0, 1.24, k), sc=lerp(1.0, 1.14, k), d=(-6 * k, 0), dw=(-10 * k, 0))
    plate(cv, 'h_p5', cam, 'b'); plate(cv, 'h_p5_gr', cam, 'w')
    cv[:] = heat_haze(cv, T, 1.0, 0.05, 2.0, 360, 560)
    n = surface_n(T)
    items = []
    for i, c in enumerate(SURFACE):
        pose = {}; crouch = 0.0; mouth = 0.0
        wr = 0.55 + 0.45 * math.sin(T * 2.3 + c['ph0'])
        pose['aL'] = 8 + 3 * wr; pose['aR'] = 8 + 3 * wr; pose['fL'] = -52 - 12 * wr; pose['fR'] = -54 - 10 * wr   # anxious hands at the belly
        pose['head'] = 3 * math.sin(T * 0.7 + c['ph0']) + 7 * sstep(seg(T, 38.64, 40.0)) + (6 * math.sin(2 * math.pi * 1.4 * T + c['ph0']) if 33.5 < T < 36.7 and i % 2 == 0 else 0.0)
        if i in (5, 7) and T > 39.0:
            hb = sstep(seg(T, 39.0, 39.8)); pose['aL'] = 11 + 32 * hb; pose['fL'] = (-52 - 12 * wr) * (1 - hb) + 128 * hb; pose['head'] += 6 * hb
        if i == 6 and T > 38.8: pose['head'] += 10 * sstep(seg(T, 38.8, 39.8))
        items.append((c['gy'], i, c, pose, mouth))
    for _, i, c, pose, mouth in sorted(items, key=lambda a: a[0]):
        Xc, Yc = cam.pt(c['x'], c['gy']); draw_char(cv, c['ch'], T, Xc, Yc, c['sc'] * cam.sc, pose=pose, flip=c['flip'], gain=c['gain'], ph0=c['ph0'], shirt=c['shirt'], pants=c['pants'])
    # time-of-day grade
    ev = np.array([0.80, 0.85, 1.0], np.float32); ni = np.array([0.95, 0.60, 0.40], np.float32) * 0.62
    mult = ev * (1 - n) + ni * n if n < 0.3 else None
    day = np.array([1.0, 1.0, 1.0], np.float32); dusk = np.array([0.85, 0.82, 1.0], np.float32); night = np.array([0.98, 0.62, 0.40], np.float32) * 0.62
    mult = day * (1 - min(1, n / 0.35)) + dusk * min(1, n / 0.35) if n < 0.35 else dusk * (1 - (n - 0.35) / 0.65) + night * ((n - 0.35) / 0.65)
    cv *= mult
    cv += np.array([14, 6, 0], np.float32) * clamp((n - 0.5) / 0.5) * 0.5
    # candle vigil
    cn = sstep(seg(T, 37.9, 39.6))
    if cn > 0.01:
        lb = LightBuf()
        for j in range(8):
            x = 150 + j * 140 + 10 * math.sin(j * 3.1); y = 690 + 8 * math.sin(j * 1.7); q = cam.pt(x, y); fl = 0.8 + 0.2 * math.sin(T * (7 + j) + j) * math.sin(T * 2.7 + j * .5)
            lb.glow(q[0], q[1] - 24, 70, (80, 170, 255), 0.55 * cn * fl); lb.glow(q[0], q[1] - 24, 260, (40, 100, 220), 0.30 * cn * fl)
            cv2.rectangle(cv, (int(q[0] - 8), int(q[1] - 14)), (int(q[0] + 8), int(q[1] + 30)), (205.0 * (0.7 + 0.3 * cn), 225.0 * (0.7 + 0.3 * cn), 240.0 * (0.7 + 0.3 * cn)), -1)
            cv2.ellipse(cv, (int(q[0]), int(q[1] - 24 + 2 * fl)), (6, int(13 * fl + 4)), 0, 0, 360, (40.0, 190.0, 255.0), -1, cv2.LINE_AA) if cn > 0.4 else None
        lb.apply(cv, blur=18)
    motes(cv, T, 17, 36, 1.2)
    vignette(cv, 0.28 + 0.25 * n, 2.1)


# (name, t0, t1, fn, crossfade seconds)
SHOTS = [('ext', 0.0, 4.82, shot_exterior, 0.0), ('tun', 4.82, 18.5, shot_tunnel, 0.5), ('dep1', 18.5, 21.43, lambda cv, T: shot_depth(cv, T, 18.45, 21.3), 0.5),
         ('cha1', 21.43, 29.05, lambda cv, T: shot_chamber(cv, T, False), 0.6), ('sur', 29.05, 41.69, shot_surface, 0.6), ('dep2', 41.69, 44.06, lambda cv, T: shot_depth(cv, T, 41.7, 43.9), 0.5),
         ('cha2', 44.06, D, lambda cv, T: shot_chamber(cv, T, True), 0.6)]


class Hook:
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTS):
            hi = t1 + (SHOTS[i + 1][4] / 2 if i + 1 < len(SHOTS) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTS) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
