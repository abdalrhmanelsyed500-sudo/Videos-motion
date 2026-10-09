"""Part 5 (Arabic, 61.9 s): the new sound, the drill breaks through, the scream, the message tied to the bit, the note reaches the surface,
"we are fine in the refuge, the 33", the news, the celebration, and the truth: alive but trapped 700 m down.
Same STYLE LOCK as parts 1-4. No captions (the red-ink note is a prop), no music (SFX only)."""
import cv2, math, numpy as np
from PIL import Image, ImageDraw
import arabic_reshaper
from bidi.algorithm import get_display
import hook_scenes as HS
from hook_scenes import *
import part2_scenes as P2
import part3_scenes as P3
import part4_scenes as P4
from part4_scenes import ev, P, sit_row, CT, paper_bg, paper_pt, paper_center, stroke, pencil
from part2_scenes import draw_items, mk, head_pt, speak, kid
from part3_scenes import GRID, chamber_bg, finish, bpt, HOT
for _k in 'usgjyv': HS.RIG[_k] = HS.RIG['m']

D5 = 61.9
INK = (34.0, 30.0, 175.0)
rs_ = np.random.default_rng(5)


# ---------------------------------------------------------------- the drill bit (layers cut from p5_bit)
_bl = {}


def bit_layers():
    if not _bl:
        im = cv2.imread(os.path.join(LAY, 'h5_bit.png'), cv2.IMREAD_UNCHANGED).astype(np.float32); a = im[..., 3:] / 255.0
        pm = np.dstack([im[..., :3] * a, a]); _bl['bit'] = Layer.from_array(pm)
        strip = pm[20:120, 110:227]; strip = cv2.resize(strip, (117, 1600), interpolation=cv2.INTER_CUBIC); _bl['pipe'] = Layer.from_array(strip)
    return _bl['bit'], _bl['pipe']


def draw_bit(cv, tip, s, rot=0.0, gain=0.95, tint=None):
    b, p = bit_layers()
    place(cv, p, M3(tip[0], tip[1], s, s, rot, 168 - 110, 1600 + 723), gain=gain * 0.96, tint=tint)
    place(cv, b, M3(tip[0], tip[1], s, s, rot, 168, 723), gain=gain, tint=tint)


def bit_pt(tip, s, rot, dx, dy):
    """layer point of the bit layer (dx, dy relative to the tip, in bit px) -> screen"""
    a = math.radians(rot); c, sn = math.cos(a), math.sin(a)
    return tip[0] + s * (c * dx - sn * dy), tip[1] + s * (sn * dx + c * dy)


# ---------------------------------------------------------------- the ragged hole in the ceiling
_hole_pts = []


def ceiling_hole(cv, cam, e, T, cx=640, w=170, dmax=140, cracks=True, light=0.0):
    if e <= 0.01: return
    if not _hole_pts:
        r = np.random.default_rng(8); xs = np.linspace(-1, 1, 23); _hole_pts.append([(float(x), float(max(0.0, (1 - abs(x) ** 1.7)) * (0.72 + 0.28 * r.random()))) for x in xs])
        br = []
        for i in range(9):
            a = math.radians(70 + 40 * (i / 8) + r.normal(0, 8)); br.append((float(np.sign(math.cos(a)) * (0.1 + 0.9 * r.random())), float(a), float(0.5 + 0.9 * r.random())))
        _hole_pts.append(br)
    pts = _hole_pts[0]; poly = [cam.pt(cx - w * e, -30)] + [cam.pt(cx + x * w * e, -30 + (30 + dmax * d * e)) for x, d in pts] + [cam.pt(cx + w * e, -30)]
    m = np.zeros((H, W), np.float32); cv2.fillPoly(m, [np.array(poly, np.int32)], 1.0); m = cv2.GaussianBlur(m, (0, 0), 2.2)[..., None]
    rim = np.zeros((H, W), np.float32); cv2.polylines(rim, [np.array(poly[1:-1], np.int32)], False, 1.0, max(2, int(5 * cam.sc)), cv2.LINE_AA); rim = cv2.GaussianBlur(rim, (0, 0), 1.6)[..., None] * (1 - m) * 0.0 + cv2.GaussianBlur(rim, (0, 0), 1.6)[..., None] * 0.55
    if cracks:
        cr = np.zeros((H, W), np.float32)
        for (sx_, a, ln) in _hole_pts[1]:
            p0 = cam.pt(cx + sx_ * w * e, -30 + dmax * 0.6 * e); l = ln * 200 * e * cam.sc; p1 = (p0[0] + math.cos(a) * l * 0.5 * (1 if sx_ >= 0 else -1), p0[1] + math.sin(a) * l)
            pm = ((p0[0] + p1[0]) / 2 + 12 * math.sin(a * 7), (p0[1] + p1[1]) / 2); cv2.polylines(cr, [np.array([p0, pm, p1], np.int32)], False, 1.0, 2, cv2.LINE_AA)
        cr = cv2.GaussianBlur(cr, (0, 0), 0.9)[..., None]; cv *= (1 - 0.8 * cr)
    cv *= (1 - m); cv += np.array((8, 6, 10), np.float32) * m
    cv += rim * np.array((70, 140, 230), np.float32) * (1 - m)
    if light > 0:
        sh = np.zeros((H, W), np.float32); a_ = cam.pt(cx - w * e * 0.8, 40); b_ = cam.pt(cx + w * e * 0.8, 40); c_ = cam.pt(cx + w * e * 2.6, 760); d_ = cam.pt(cx - w * e * 2.6, 760)
        cv2.fillPoly(sh, [np.array([a_, b_, c_, d_], np.int32)], 1.0); sh = cv2.GaussianBlur(sh, (0, 0), 30)[..., None]; cv += sh * np.array((255, 235, 200), np.float32) * 0.22 * light


def chunk_fall(cv, T, t0, t1, n, seed, x0=420, x1=860, ground=700, z=1.0):
    r = np.random.default_rng(seed)
    for i in range(n):
        ts = t0 + (t1 - t0) * r.random(); tt = T - ts
        if tt < 0 or tt > 1.4: continue
        x = x0 + (x1 - x0) * r.random(); sz = 5 + 14 * r.random(); y = -20 + 600 * tt * tt * 1.0 + 40 * tt; yy = min(y, ground - 20 * r.random())
        c = 70 + 60 * r.random(); col = (c * .55, c * .8, c)
        pp = np.array([(x - sz, yy), (x - sz * .2, yy - sz * .9), (x + sz, yy - sz * .2), (x + sz * .5, yy + sz * .7)], np.float32); pp = (pp - np.array([640, 360])) * z + np.array([640, 360])
        cv2.fillConvexPoly(cv, pp.astype(np.int32), col, cv2.LINE_AA)


def crew_pose(i, T, up=0.0, ears=0.0):
    return {'head': -10 * up + 2 * math.sin(T * 1.5 + i), 'aL': 6 + 70 * up * (i % 2), 'aR': 6 + 70 * up * ((i + 1) % 2), 'fL': 0, 'fR': 0}


SPEC6 = [(250, 690, .50, 1, 'm'), (430, 700, .52, -1, 'u'), (600, 670, .42, 1, 'm'), (790, 700, .50, -1, 'g'), (960, 680, .46, 1, 'm'), (1130, 696, .50, -1, 'j')]


# ---------------------------------------------------------------- 1. a new sound: closer, louder, clearer (0 - 5.4)
SND5 = [(0.9, 2.0, 0.6), (2.5, 3.8, 1.0), (4.1, 5.6, 1.7)]


def shot_heard(cv, T):
    k = seg(T, 0, 5.6); sh = 0.0
    for a, b, am in SND5: sh = max(sh, am * P(T, a, b))
    dxy = shake_xy(T, sh); cam = Cam(A=(700, 520), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.20, k), sc=lerp(1.0, 1.10, k), d=dxy, dw=(dxy[0] * 1.5, dxy[1] * 1.5))
    plate(cv, 'h3_storage', cam, 'b')
    lb = LightBuf(); q = bpt(cam, 1000, 100); fl = 0.88 + 0.12 * flick(T, 5.0)
    lb.glow(q[0], q[1], 50 * cam.sb, (110, 190, 255), 0.7 * fl); lb.glow(q[0], q[1], 300 * cam.sb, (60, 130, 230), 0.34 * fl); lb.apply(cv, blur=28)
    lk = ev(T, 0.7, 1.6); items = []
    for i, (x, gy, sc, fl_, ch) in enumerate(SPEC6):
        up = P(T, 4.0, 5.8) * 0.8
        pose = {'head': (-14 * lk + 2 * math.sin(T * 1.5 + i)) * (1 if i % 2 else 0.8), 'aL': 6 + 30 * up, 'aR': 6 + 30 * up, 'fL': -40 * up, 'fR': -40 * up}
        items.append(mk(ch, x, gy, sc, fl_, i * 1.3, pose=pose, crouch=0.2, gain=0.9, tint=HOT, shirt=SHIRTS[(i * 3 + 1) % 10] if ch == 'm' else None, pants=PANTS[(i * 7 + 2) % 10] if ch == 'm' else None, sway=1.0 - 0.7 * lk))
    draw_items(cv, cam, items, T)
    puffs(cv, T, 0.9, 5.6, 9, (300, 0, 700, 80), (95, 135, 178), seed=51, size=(40, 100), rise=(20, 70), life=1.4, alpha=0.2)
    finish(cv, T, 71, 0.45, 24)


# ---------------------------------------------------------------- 2. the men freeze; did they really reach us? (5.4 - 10.3)
def shot_freeze(cv, T):
    k = seg(T, 5.3, 10.4); sh = 0.0
    for a in (6.2, 7.5, 8.9): sh = max(sh, 1.2 * P(T, a, a + 0.7))
    dxy = shake_xy(T, sh); cam = Cam(A=(640, 640), sb=lerp(1.0, 1.12, k), sw=lerp(1.0, 1.30, k), sc=lerp(1.0, 1.22, k), d=dxy, dw=(dxy[0] * 1.5, dxy[1] * 1.5))
    chamber_bg(cv, T, cam, 0.66, lamps=0.9 - 0.15 * sh)
    items = []; fr = ev(T, 5.4, 6.0)
    for i, c in enumerate(GRID):
        if abs(c['x'] - 640) < 170 and c['gy'] > 630: continue
        items.append(dict(c, pose={'head': -12 * fr + (1 - fr) * 3 * math.sin(T + i), 'aL': 4, 'aR': 4}, crouch=0.12, gain=0.76, tint=CT, sway=0.12))
    q = ev(T, 8.6, 9.4)
    items.append(mk('u', 640, 722, .52, 1, 0.4, pose={'head': -14 * fr + 6 * q, 'aL': 8 + 100 * fr * (1 - q), 'fL': 130 * fr * (1 - q), 'aR': 8}, gain=1.0, tint=(0.95, 1.0, 1.06), sway=0.2, crouch=0.04))
    draw_items(cv, cam, items, T)
    puffs(cv, T, 5.4, 10.4, 14, (200, 0, 880, 60), (95, 135, 178), seed=52, size=(30, 80), rise=(20, 60), life=1.6, alpha=0.2)
    veil(cv, T, 0.05 + 0.08 * sh); finish(cv, T, 72, 0.5, 20)


# ---------------------------------------------------------------- 3. the drill breaks through the rock (10.3 - 13.95)
def wall_cam(T, k, z0=1.0, z1=1.12, sh=0.0, A=(640, 300)):
    dxy = shake_xy(T, sh); return Cam(A=A, sb=lerp(z0, z1, k), sw=lerp(z0, z1, k), sc=lerp(z0, z1, k), d=dxy, dw=dxy)


def wall_bg(cv, T, cam, dark=0.9, glow=1.0):
    plate(cv, 'h5_wall', cam, 'b', gain=dark)
    lb = LightBuf(); q = bpt(cam, 170, 190); fl = 0.88 + 0.12 * flick(T, 3.0)
    lb.glow(q[0], q[1], 40 * cam.sb, (110, 190, 255), 0.5 * fl * glow); lb.glow(q[0], q[1], 300 * cam.sb, (60, 130, 230), 0.30 * fl * glow); lb.apply(cv, blur=28)


def shot_break(cv, T):
    k = seg(T, 10.2, 14.0); e = ev(T, 11.0, 12.5)
    sh = 0.3 * ev(T, 10.3, 11.0) + 1.4 * P(T, 11.4, 12.8) + 0.7 * P(T, 12.8, 14.0); cam = wall_cam(T, k, 1.0, 1.12, sh)
    wall_bg(cv, T, cam, 0.86); ceiling_hole(cv, cam, e, T, 640, 170, 150)
    chunk_fall(cv, T, 11.2, 13.4, 22, 61, 470, 820, 640, cam.sc)
    ex = ev(T, 12.05, 13.15); tip = cam.pt(640 + 3 * math.sin(T * 45), lerp(-640, 430, ex) + 3 * math.sin(T * 60)); s = 0.60 * cam.sc
    if ex > 0: draw_bit(cv, tip, s, rot=1.2 * math.sin(T * 38), gain=0.95, tint=(0.92, 1.0, 1.08))
    puffs(cv, T, 11.0, 14.0, 26, (440, 0, 400, 300), (110, 150, 190), seed=62, size=(50, 130), rise=(-20, 40), life=2.0, alpha=0.30, wind=(8, 0))
    fl_ = P(T, 12.0, 12.6) * 0.3; cv += fl_ * 120
    lb = LightBuf(); lb.glow(tip[0], tip[1], 160 * cam.sc, (120, 200, 255), 0.22 * ex * P(T, 12.0, 14.0)); lb.apply(cv, blur=26)
    finish(cv, T, 73, 0.5, 26)


# ---------------------------------------------------------------- 4. the scream: they run, knock, call, hit with all their strength (13.95 - 23.7)
RUNNERS = []
for _i in range(16):
    _side = -1 if _i % 2 == 0 else 1; _r = np.random.default_rng(100 + _i)
    RUNNERS.append(dict(ch='m' if _i not in (3, 8, 11) else ('u', 's', 'g')[(_i // 4) % 3], x0=640 + _side * (760 + 80 * _r.random()), x1=640 + _side * (140 + 65 * (_i // 2) + 20 * _r.random()), gy=640 + 70 * ((_i * 5) % 4) / 3, sc=.46 + .05 * ((_i * 3) % 3), t0=13.9 + 0.12 * _i, ph=_r.random() * 6))
RUNNERS[3]['ch'] = 'u'; RUNNERS[8]['ch'] = 's'; RUNNERS[11]['ch'] = 'g'


def shot_scream(cv, T):
    k = seg(T, 13.8, 23.8); sh = 0.5 * ev(T, 14.0, 15.0) * (1 - ev(T, 22.0, 23.5)) + 0.5 * P(T, 17.4, 21.5)
    cam = wall_cam(T, k, 1.0, 1.0, sh, A=(640, 450)); wall_bg(cv, T, cam, 0.88, 1.0)
    ceiling_hole(cv, cam, 1.0, T, 640, 170, 150)
    tip = cam.pt(640 + 2 * math.sin(T * 30) * (1 if T < 24 else 0), 380 + 3 * math.sin(T * 50)); draw_bit(cv, tip, 0.60 * cam.sc, rot=0.8 * math.sin(T * 33), gain=0.95, tint=(0.92, 1.0, 1.08))
    items = []
    for i, c in enumerate(RUNNERS):
        u = ev(T, c['t0'], c['t0'] + 2.0); x = lerp(c['x0'], c['x1'], u); moving = 1.0 if 0.02 < u < 0.98 else 0.0
        hit = ev(T, 16.6 + 0.07 * i, 17.4 + 0.07 * i); w_ = math.sin(2 * math.pi * 3.2 * T + i * 1.7); w2 = math.sin(2 * math.pi * 3.2 * T + i * 1.7 + math.pi)
        pose = {'aL': 20 + 95 * hit * (0.5 + 0.5 * w_) + 40 * (1 - hit) * moving, 'aR': 20 + 95 * hit * (0.5 + 0.5 * w2) + 40 * (1 - hit) * moving, 'fL': 30 * hit * w_, 'fR': 30 * hit * w2, 'head': -10 * hit + 4 * math.sin(T * 6 + i)}
        if T > 21.5: pose['aL'] = 20 + 110 * ev(T, 21.5 + 0.05 * i, 22.3 + 0.05 * i); pose['aR'] = pose['aL'] * 0.8
        face_c = -1 if x < 640 else 1
        items.append(mk(c['ch'], x, c['gy'], c['sc'], face_c, c['ph'], pose=pose, walk=1.0 * moving, mouth=speak(T, i, 1.0) * (1.0 if T > c['t0'] + 0.3 and T < 23.6 else 0.0), hop=abs(math.sin(T * 6.5 + i)) * 14 * hit * (i % 3 == 0),
                        gain=0.9, tint=HOT, shirt=SHIRTS[(i * 3 + 1) % 10] if c['ch'] == 'm' else None, pants=PANTS[(i * 7 + 2) % 10] if c['ch'] == 'm' else None, crouch=0.0))
    draw_items(cv, cam, items, T)
    chunk_fall(cv, T, 14.0, 20.0, 14, 63, 420, 860, 700, cam.sc)
    puffs(cv, T, 13.9, 23.8, 30, (200, 380, 880, 300), (110, 150, 190), seed=64, size=(50, 130), rise=(-10, 40), life=2.2, alpha=0.22, wind=(10, 0))
    finish(cv, T, 74, 0.5, 30)


# ---------------------------------------------------------------- 5. they write a message (23.7 - 26.0), tie it to the drill, let it go back (26.0 - 29.0)
SCRIB5 = []
_r5 = np.random.default_rng(15)
for _j in range(5):
    _y = 0.26 + 0.11 * _j; _x = 0.86; _pts = [(_x, _y)]
    while _x > 0.16 + 0.2 * (_j == 4): _x -= 0.025 + 0.02 * _r5.random(); _pts.append((_x, _y + 0.035 * math.sin(_x * 60 + _j) + 0.012 * _r5.normal()))
    SCRIB5.append(_pts)


def shot_write(cv, T):
    k = seg(T, 23.6, 26.2); z = lerp(2.0, 2.3, k); cam = Cam(A=(680, 520), sb=z, sw=z, sc=z); cam.d = paper_center(z); cam.dw = cam.d
    paper_bg(cv, T, cam)
    p = seg(T, 23.9, 25.8) * len(SCRIB5); tip = None
    for i, ln in enumerate(SCRIB5):
        pr = clamp(p - i)
        if pr > 0:
            t_ = stroke(cv, cam, ln, pr, w=2.6, col=INK)
            if pr < 1.0: tip = t_
    if tip is None and p > 0: tip = bpt(cam, *paper_pt(*SCRIB5[-1][-1]))
    pencil(cv, tip, -32, 150, cam.sb / 2.0)
    veil(cv, T, 0.04); finish(cv, T, 75, 0.5, 14)


def note_poly(cx, cy, w, h, rot, bend=0.0):
    a = math.radians(rot); R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    return (np.array([[-w, -h], [w, -h * (1 - bend)], [w * (1 - bend), h], [-w * 0.95, h * 1.02]], np.float32) / 2.0) @ R.T + np.array([cx, cy], np.float32)


def draw_note(cv, cx, cy, w, h, rot, tint=1.0):
    pts = note_poly(cx, cy, w, h, rot)
    cv2.fillConvexPoly(cv, (pts + np.array([4, 5])).astype(np.int32), (10.0, 14.0, 22.0), cv2.LINE_AA)
    cv2.fillConvexPoly(cv, pts.astype(np.int32), (150.0 * tint, 195.0 * tint, 220.0 * tint), cv2.LINE_AA)
    cv2.polylines(cv, [pts.astype(np.int32)], True, (90.0 * tint, 130.0 * tint, 165.0 * tint), 1, cv2.LINE_AA)
    return pts


def shot_tie(cv, T):
    k = seg(T, 26.0, 29.1); up = ev(T, 27.7, 29.0); sh = 0.35 * P(T, 27.6, 29.0) + 0.1
    cam = wall_cam(T, k, 1.05, 1.0, sh, A=(640, 450)); wall_bg(cv, T, cam, 0.86); ceiling_hole(cv, cam, 1.0, T, 640, 170, 150)
    tipy = lerp(380, -520, up ** 1.3); tip = cam.pt(640 + 2 * math.sin(T * 36) * up, tipy); s = 0.60 * cam.sc; draw_bit(cv, tip, s, rot=0.8 * math.sin(T * 33) * up, gain=0.95, tint=(0.92, 1.0, 1.08))
    # the note, tied with a string round the pipe above the bit
    ne = ev(T, 26.9, 27.5)
    if ne > 0:
        nx, ny = bit_pt(tip, s, 0, 26, -380)
        nx += (1 - ne) * 40; ny += (1 - ne) * 60 - 8 * math.sin(T * 5) * (1 - up)
        cv2.line(cv, (int(nx - 24 * s * 1.0), int(ny)), (int(nx - 60 * s), int(ny - 20 * s)), (60.0, 110.0, 150.0), 2, cv2.LINE_AA)
        draw_note(cv, nx, ny, 150 * cam.sc * 0.7, 105 * cam.sc * 0.7, -8 + 8 * math.sin(T * 3.0))
    items = []
    urz = ev(T, 26.2, 26.9) * (1 - ev(T, 27.5, 28.2))
    for i, (x, gy, sc, fl_, ch) in enumerate(((200, 690, .50, 1, 'm'), (340, 700, .52, 1, 'j'), (480, 696, .52, 1, 'u'), (800, 700, .50, -1, 'g'), (940, 690, .52, -1, 's'), (1080, 700, .50, -1, 'm'), (80, 650, .38, 1, 'm'), (1200, 650, .38, -1, 'm'))):
        po = {'head': -12 + 4 * math.sin(T * 2 + i) - 6 * up, 'aL': 8 + 20 * up * (i % 2), 'aR': 8 + 20 * up * ((i + 1) % 2), 'fL': 0, 'fR': 0}
        if ch == 'u': po.update({'aR': 8 + 105 * urz + 30 * up, 'fR': 20 * urz, 'head': -14, 'aL': 8 + 20 * urz})
        items.append(mk(ch, x, gy, sc, fl_, i * 1.2, pose=po, mouth=0.0, gain=0.9, tint=HOT, shirt=SHIRTS[(i * 3 + 1) % 10] if ch == 'm' else None, pants=PANTS[(i * 7 + 2) % 10] if ch == 'm' else None, crouch=0.0))
    draw_items(cv, cam, items, T)
    puffs(cv, T, 26.0, 29.0, 12, (440, 0, 400, 300), (110, 150, 190), seed=65, size=(50, 130), rise=(-10, 40), life=2.0, alpha=0.2, wind=(8, 0))
    finish(cv, T, 76, 0.5, 24)


# ---------------------------------------------------------------- 6. the bit reaches the surface, people see the paper (28.97 - 32.5)
def focus(cam, px, py, sx, sy):
    cam.d = (0, 0); cam.dw = (0, 0); b = bpt(cam, px, py); cam.d = (sx - b[0], sy - b[1]); cam.dw = cam.d


def world_of(px, py): return S0 * px - OX, S0 * py - OY


def shot_surface(cv, T):
    k = seg(T, 28.9, 32.6); z = lerp(1.85, 2.05, k); cam = Cam(A=(300, 470), sb=z, sw=z, sc=z); focus(cam, 400, 420, 560, 470)
    sh = 0.5 * P(T, 29.1, 30.4); dxy = shake_xy(T, sh); cam.d = (cam.d[0] + dxy[0], cam.d[1] + dxy[1]); cam.dw = cam.d
    plate(cv, 'h_p5', cam, 'b'); plate(cv, 'h_p5_gr', cam, 'w')
    base = bpt(cam, 262, 400); rise = ev(T, 29.2, 30.5); s = 0.14 * cam.sc
    tip = (base[0], base[1] - 20 - rise * 200 * cam.sc)
    held = ev(T, 30.6, 31.2)
    if held < 1: draw_bit(cv, tip, s, rot=0.0, gain=0.98)
    if held < 1:
        nx, ny = bit_pt(tip, s, 0, 26, -300); draw_note(cv, nx, ny, 150 * s * 1.0 * 1.2, 105 * s * 1.2, -8 + 6 * math.sin(T * 6), 1.05)
    items = []
    crew = [(330, 470, .13, 1, 'm', 0), (330, 530, .14, 1, 'm', 1), (480, 560, .15, -1, 'm', 2), (560, 500, .14, -1, 'm', 3), (640, 590, .16, -1, 'm', 4)]
    for (px, py, sc, fl_, ch, i) in crew:
        x, gy = world_of(px, py); pt_ = ev(T, 29.4 + 0.1 * i, 30.3)
        po = {'head': -10 * (1 - held) + 8 * held, 'aL': 8 + 60 * pt_ * (i % 2) + 100 * held * (i == 4), 'aR': 8 + 40 * pt_ + 110 * held * ((i == 4) or (i == 2)), 'fL': 0, 'fR': 0}
        items.append(mk(ch, x, gy, sc * 1.0 * 1.0, fl_, i * 1.3, pose=po, mouth=speak(T, i) * held * 0.8, gain=1.0, shirt=SHIRTS[(i * 3 + 2) % 10], pants=PANTS[(i * 5 + 1) % 10], crouch=0.0, sway=0.6))
    fam = [(790, 520, .15, -1, 'w'), (880, 570, .16, -1, 'ar'), (930, 500, .14, 1, 'w'), (740, 620, .17, -1, 'ar')]
    for j, (px, py, sc, fl_, ch) in enumerate(fam):
        x, gy = world_of(px, py); run = ev(T, 30.0 + 0.15 * j, 31.6); xs = x + (1 - run) * 260
        items.append(mk(ch, xs, gy, sc, fl_, 4 + j * 1.1, pose={'aL': 8 + 40 * held, 'aR': 8 + 114 * held * (j % 2), 'fR': 100 * held * (j % 2), 'head': -6 * held}, walk=1.0 if 0.03 < run < 0.97 else 0.0, gain=1.0, crouch=0.0, sway=0.6))
    draw_items(cv, cam, items, T)
    if held > 0:
        x, gy = world_of(640, 590); hx, hy = cam.pt(x, gy); ny = hy - 1000 * 0.16 * cam.sc * lerp(0.6, 1.38, held)
        draw_note(cv, hx - 12, ny, 100 * cam.sc * 0.75, 70 * cam.sc * 0.75, -6 + 5 * math.sin(T * 5.0), 1.1)
    puffs(cv, T, 29.0, 32.6, 14, (160, 430, 300, 80), (150, 185, 215), seed=121, size=(50, 120), rise=(10, 40), life=2.4, alpha=0.25, wind=(30, 0))
    heat = heat_haze(cv, T, 1.0, 0.05, 2.5, 380, 560); cv[:] = heat; motes(cv, T, 7, 22, 1.4); vignette(cv, 0.3, 2.0)


# ---------------------------------------------------------------- 7. the note, in red ink (32.5 - 39.8)
_note = {}


def note_text():
    if 'img' not in _note:
        W_, H_ = 900, 620; base = np.zeros((H_, W_), np.float32); lines = []
        for j, tx in enumerate(('نحن بخير في الملجأ…', 'نحن الثلاثة والثلاثون')):
            im = Image.new('L', (W_, 200), 0); d = ImageDraw.Draw(im); f = font(78, 'assets/Amiri-Bold.ttf')
            s = get_display(arabic_reshaper.reshape(tx)); tw = d.textlength(s, font=f); d.text(((W_ - tw) / 2 + 6 * (j == 1), 40), s, font=f, fill=255, stroke_width=2, stroke_fill=255)
            a = np.asarray(im, np.float32) / 255.0; M = cv2.getRotationMatrix2D((W_ / 2, 100), 2.0 - 3.5 * j, 1.0); a = cv2.warpAffine(a, M, (W_, 200)); lines.append(a)
        base[130:330] += lines[0]; base[330:530] += lines[1]; _note['l'] = [(130, 330), (330, 530)]; _note['img'] = np.clip(base, 0, 1)
        n = cv2.GaussianBlur(np.random.default_rng(3).normal(0, 1, (H_, W_)).astype(np.float32), (0, 0), 6); _note['grain'] = n
    return _note['img']


def shot_note(cv, T):
    ink = note_text(); k = seg(T, 32.4, 39.9)
    # dim blurred background of the surface
    z = lerp(1.0, 1.08, k); cam = Cam(A=(640, 360), sb=2.4, sw=2.4, sc=2.4); focus(cam, 430, 330, 640, 360)
    plate(cv, 'h_p5', cam, 'b'); cv[:] = cv2.GaussianBlur(cv, (0, 0), 14) * 0.38
    grow = ev(T, 32.5, 33.9); ps = lerp(0.62, 1.0, grow) * z
    cx, cy = 640 + 6 * math.sin(T * 0.8), 372 + 5 * math.sin(T * 0.6 + 1); rot = -2.0 + 1.6 * math.sin(T * 0.7); pw, ph = 900 * 0.92 * ps, 620 * 0.95 * ps
    # paper (warm, creased) with soft shadow
    paper = np.zeros((620, 900, 3), np.float32); paper[:] = (175, 210, 232); paper += _note['grain'][..., None] * 5.0
    yy, xx = np.mgrid[0:620, 0:900]; paper *= (0.80 + 0.2 * (1 - ((xx - 450) / 560.0) ** 2) * (1 - ((yy - 310) / 420.0) ** 2))[..., None]
    paper = np.minimum(paper, 255)
    for fx in (300, 600): paper[:, fx - 2:fx + 2] *= 0.88
    paper[300:304] *= 0.9
    # red ink reveal: line 1 (right to left) 35.55-37.0, line 2 37.6-39.5
    mask = np.zeros_like(ink); (a0, a1), (b0, b1) = _note['l']
    r1 = ev(T, 35.55, 37.0); r2 = ev(T, 37.6, 39.5)
    c1 = int(900 - 900 * r1); c2 = int(900 - 900 * r2)
    mask[a0:a1, c1:] = ink[a0:a1, c1:]; mask[b0:b1, c2:] = ink[b0:b1, c2:]
    mask = cv2.GaussianBlur(mask, (0, 0), 0.7)
    ink_a = np.clip(mask * 1.0, 0, 1)[..., None]; col = np.array(INK, np.float32) * (0.85 + 0.25 * _note['grain'][..., None] / 3.0)
    layer = paper * (1 - ink_a * 0.93) + col * ink_a * 0.93
    rgba = np.dstack([layer, np.full((620, 900), 255, np.float32)]); a_ = rgba[..., 3:] / 255.0; pm = np.dstack([rgba[..., :3] * a_, a_])
    lay = Layer.from_array(pm)
    # shadow
    place(cv, lay, M3(cx + 14, cy + 20, ps * 0.92, ps * 0.95, rot, 450, 310), gain=0.0)
    sh_ = np.zeros((H, W), np.float32); poly = note_poly(cx + 14, cy + 22, pw, ph, rot); cv2.fillConvexPoly(sh_, poly.astype(np.int32), 1.0); sh_ = cv2.GaussianBlur(sh_, (0, 0), 14)[..., None]; cv *= (1 - 0.55 * sh_)
    place(cv, lay, M3(cx, cy, ps * 0.92, ps * 0.95, rot, 450, 310), gain=1.0)
    lb = LightBuf(); lb.glow(cx - 40, cy - 80, 520, (90, 170, 255), 0.18 + 0.05 * math.sin(T * 1.3)); lb.apply(cv, blur=40)
    finish(cv, T, 77, 0.55, 18)


# ---------------------------------------------------------------- 8. seventeen days (39.8 - 45.6): chalk marks on the rock, then the light
def tally_pts(i):
    g, j = divmod(i, 5); x0 = 300 + g * 215; r = np.random.default_rng(300 + i)
    if j < 4: x = x0 + j * 36; return [(x + r.normal(0, 3), 420 + r.normal(0, 4)), (x + 4 + r.normal(0, 3), 560 + r.normal(0, 4))]
    return [(x0 - 20, 540 + r.normal(0, 4)), (x0 + 4 * 36 + 10, 450 + r.normal(0, 4))]


def shot_days(cv, T):
    k = seg(T, 39.7, 45.7); z = lerp(1.0, 1.14, k); cam = Cam(A=(640, 380), sb=z, sw=z, sc=z, d=(0, 0), dw=(0, 0))
    plate(cv, 'h_p4', cam, 'b', gain=0.78)
    lb = LightBuf(); q = bpt(cam, 160, 130); lb.glow(q[0], q[1], 300, (60, 130, 230), 0.12); lb.apply(cv, blur=30)
    for i in range(17):
        e = ev(T, 40.0 + 0.11 * i, 40.0 + 0.11 * i + 0.22)
        if e <= 0: continue
        (xa, ya), (xb, yb) = tally_pts(i)
        pa = bpt(cam, xa, ya); pb = bpt(cam, xa + (xb - xa) * e, ya + (yb - ya) * e); w_ = max(2, int(6 * cam.sb))
        cv2.line(cv, (int(pa[0] + 2), int(pa[1] + 3)), (int(pb[0] + 2), int(pb[1] + 3)), (10.0, 14.0, 22.0), w_ + 2, cv2.LINE_AA)
        cv2.line(cv, (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1])), (215.0, 232.0, 240.0), w_, cv2.LINE_AA)
    al = ev(T, 44.7, 45.6); wob = 0.9 + 0.1 * math.sin(T * 7)
    lb = LightBuf(); lb.glow(640, 380, 520, (80, 170, 255), 0.75 * al * wob); lb.glow(640, 380, 180, (200, 235, 255), 0.55 * al); lb.apply(cv, blur=44)
    puffs(cv, T, 39.8, 45.7, 8, (100, 0, 1080, 500), (110, 150, 190), seed=81, size=(40, 90), rise=(10, 30), life=2.4, alpha=0.10)
    finish(cv, T, 78, 0.55, 22)


# ---------------------------------------------------------------- 9. the news, the tears, the party; then "something changed" (45.6 - 53.45)
CAST = [('w', 340, 668, .30, 1), ('ar', 430, 650, .27, 1), ('ar', 520, 662, .29, -1), ('w', 640, 652, .28, -1), ('ar', 750, 660, .30, 1), ('w', 570, 672, .26, 1), ('ar', 880, 650, .28, 1), ('w', 990, 662, .30, -1), ('ar', 1090, 656, .27, 1),
        ('m', 260, 676, .30, 1), ('m', 1180, 668, .29, -1), ('m', 700, 690, .31, 1)]


def shot_camp(cv, T):
    k = seg(T, 45.5, 53.6); cam = Cam(A=(640, 620), sb=lerp(1.0, 1.06, k), sw=lerp(1.0, 1.12, k), sc=lerp(1.05, 1.10, k), d=(0, 0), dw=(0, 0))
    plate(cv, 'h4_night', cam, 'b'); plate(cv, 'h4_night_gr', cam, 'w')
    stun = ev(T, 45.6, 46.3); cry = ev(T, 47.0, 47.8) * (1 - ev(T, 49.2, 49.8)); party = ev(T, 49.4, 50.2) * (1 - ev(T, 50.7, 51.5)); drop = ev(T, 50.7, 52.2)
    items = []
    for i, (ch, x, gy, sc, fl_) in enumerate(CAST):
        jmp = abs(math.sin(T * 5.5 + i * 0.9)) * 26 * party; sob = 3 * math.sin(T * 9 + i)
        pose = {'aL': 4 + 114 * cry + 138 * party, 'fL': 140 * cry + 8 * party, 'aR': 4 + 114 * cry * (i % 2) + 138 * party, 'fR': 140 * cry * (i % 2) + 8 * party, 'head': 8 * cry * (1 + 0.3 * math.sin(T * 9)) - 4 * party + 3 * drop + sob * cry}
        if stun > 0 and cry < 0.1 and party < 0.1: pose.update({'aL': 4 + 20 * stun * (i % 2), 'aR': 4 + 20 * stun * ((i + 1) % 2), 'head': -6 * stun * (1 - drop)})
        mo = speak(T, i, 1.0) * party * (1 - drop)
        if ch == 'm': items.append(mk(ch, x, gy, sc, fl_, i * 1.3, pose=pose, mouth=mo, hop=jmp, gain=0.95, tint=(0.95, 0.98, 1.04), shirt=SHIRTS[(i * 3 + 1) % 10], pants=PANTS[(i * 7 + 2) % 10], crouch=0.1 * cry + 0.1 * drop))
        else: items.append(mk(ch, x, gy, sc, fl_, i * 1.3, pose=pose, mouth=mo, hop=jmp, gain=0.95, tint=(0.95, 0.98, 1.04), crouch=0.12 * cry + 0.1 * drop))
    items += [kid('w', 470, 690, .19, 1, 7.1, pose={'aL': 4 + 114 * party, 'aR': 4 + 114 * party, 'head': 0}, hop=abs(math.sin(T * 6.5)) * 22 * party, tint=(0.95, 0.98, 1.04), gain=.95), kid('ar', 690, 694, .18, -1, 8.2, pose={'aL': 4 + 114 * cry, 'fL': 140 * cry, 'aR': 4 + 114 * party}, hop=abs(math.sin(T * 7.0)) * 22 * party, tint=(0.95, 0.98, 1.04), gain=.95)]
    draw_items(cv, cam, items, T)
    lb = LightBuf(); fl = 0.9 + 0.1 * flick(T, 8.0)
    for (px, py, r_) in ((800, 530, 40), (1020, 548, 28), (560, 540, 26)):
        q = cam.pt(S0 * px - OX, S0 * py - OY); lb.glow(q[0], q[1], r_ * cam.sb, (110, 190, 255), (0.55 + 0.45 * party) * fl); lb.glow(q[0], q[1], 7 * r_ * cam.sb, (50, 120, 230), 0.25 * fl)
    lb.apply(cv, blur=26)
    # celebration sparks
    r = np.random.default_rng(91)
    if party > 0.02:
        for i in range(70):
            x = r.random() * W; sp = 60 + 140 * r.random(); y = (H * 0.9 - ((T - 49.4) * sp + r.random() * 200)) % H; c = (150 + 100 * r.random())
            cv2.circle(cv, (int(x + 12 * math.sin(T * 3 + i)), int(y)), 1 + int(r.random() > .6), (c * .45, c * .8, c), -1, cv2.LINE_AA)
    motes(cv, T, 54, 30, 0.6, (230, 225, 200)); vignette(cv, 0.4, 2.0)
    # "but...": the colour drains, the air goes still
    g = cv.mean(axis=2, keepdims=True); cv[:] = cv * (1 - 0.65 * drop) + g * 0.65 * drop; cv *= (1 - 0.30 * drop)


# ---------------------------------------------------------------- 10. alive but trapped, ~700 m down (53.45 - 57.9)
def shot_depth5(cv, T):
    k = ev(T, 53.5, 57.2); sS = 2.0 * S0; cx_ = 688
    zz = 1.0 + 0.9 * ev(T, 56.2, 58.0); cyp = min(lerp(250, 570, k), 768 - 192 / zz) if k < 1 else 768 - 192 / zz; cyp = min(cyp + 100 * ev(T, 56.2, 58.0), 768 - 192 / zz)
    sc = sS * zz; ox = cx_ * S0 * zz * 2.0 - W / 2; oy = cyp * S0 * zz * 2.0 - H / 2
    place(cv, L('h5_depth'), M3(-ox, -oy, sc, sc, 0, 0, 0), gain=0.95)
    q = (cx_ * sc - ox, 685 * sc - oy); fl = 0.85 + 0.15 * flick(T, 2.0) + 0.1 * math.sin(T * 2.4)
    lb = LightBuf(); lb.glow(q[0], q[1], 70 * zz, (110, 190, 255), 0.55 * fl); lb.glow(q[0], q[1], 330 * zz, (60, 130, 230), 0.32 * fl); lb.apply(cv, blur=26)
    # a slow descending mote of dust along the pipe
    motes(cv, T, 56, 24, 0.4, (210, 200, 180)); vignette(cv, 0.35 + 0.25 * ev(T, 56.5, 58.0), 2.0)


# ---------------------------------------------------------------- 11. the chamber: a shaft of surface light from the new hole - they are only at the beginning (57.9 - 61.9)
def shot_begin(cv, T):
    k = seg(T, 57.8, 61.9); cam = Cam(A=(640, 600), sb=lerp(1.12, 1.0, k), sw=lerp(1.2, 1.02, k), sc=lerp(1.12, 0.98, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.5, lamps=0.55)
    items = []
    for i, c in enumerate(GRID):
        if abs(c['x'] - 640) < 190 and c['gy'] > 600: continue
        items.append(dict(c, pose={'head': -10 + 2 * math.sin(T * 0.7 + i), 'aL': 4, 'aR': 4}, crouch=0.2, gain=0.68, tint=CT, sway=0.4))
    items.append(mk('u', 470, 716, .46, 1, 0.4, pose={'head': -9 + 2 * math.sin(T * 0.6), 'aL': 8, 'aR': 8}, gain=1.0, tint=(0.95, 1.0, 1.06), sway=0.3, crouch=0.04))
    draw_items(cv, cam, items, T)
    ceiling_hole(cv, cam, 0.85, T, 640, 170, 170, cracks=True, light=1.0)
    puffs(cv, T, 57.8, 61.9, 10, (500, 0, 280, 60), (150, 175, 200), seed=111, size=(30, 70), rise=(20, 50), life=2.0, alpha=0.12)
    veil(cv, T, 0.06); finish(cv, T, 79, 0.55 + 0.1 * k, 18)


SHOTS5 = [('heard', 0.0, 5.4, shot_heard, 0.0), ('freeze', 5.4, 10.3, shot_freeze, 0.5), ('break', 10.3, 13.95, shot_break, 0.4), ('scream', 13.95, 23.7, shot_scream, 0.3),
          ('write', 23.7, 26.0, shot_write, 0.4), ('tie', 26.0, 28.95, shot_tie, 0.4), ('surface', 28.95, 32.5, shot_surface, 0.4), ('note', 32.5, 39.8, shot_note, 0.5),
          ('days', 39.8, 45.6, shot_days, 0.4), ('camp', 45.6, 53.45, shot_camp, 0.5), ('depth', 53.45, 57.9, shot_depth5, 0.5), ('begin', 57.9, D5, shot_begin, 0.6)]


class Part5:
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTS5):
            hi = t1 + (SHOTS5[i + 1][4] / 2 if i + 1 < len(SHOTS5) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTS5) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
