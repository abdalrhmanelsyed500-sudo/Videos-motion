"""Part 8 (Arabic, ~44.9 s): "the story did not end when they came out": trauma, anxiety, nightmares, depression, not being able to go back to the mine,
fame (cameras, interviews, money, disputes), and the difference between surviving and knowing how to live. Same STYLE LOCK as parts 1-7. No captions, no music."""
from part7_scenes import *
import part7_scenes as P7

D8 = 44.9
MOON = (0.86, 0.95, 1.14)
MAN = dict(shirt=SHIRTS[1])


def man8(x, gy, sc, flip=1, ph=0.3, **kw):
    kw.setdefault('gain', 0.95); return mk('m', x, gy, sc, flip, ph, **MAN, **kw)


def cam1(z=1.0, A=(640, 420), dx=0.0, dy=0.0, dz=None):
    return Cam(A=A, sb=z, sw=dz if dz else z, sc=z, d=(dx, dy), dw=(dx * 1.3, dy * 1.3))


def desat(cv, a):
    if a <= 0: return
    g = cv.mean(axis=2, keepdims=True); cv[:] = cv * (1 - a) + g * a


def smoke(cv, T, t0, t1, cx, cy, w=360, h=300, n=22, a=0.45, seed=10):
    puffs(cv, T, t0, t1, n, (cx - w / 2, cy - h / 2, w, h), (70, 62, 80), seed=seed, size=(50, 120), rise=(10, 50), life=2.0, alpha=a)


# ---------------------------------------------------------------- props
def mic(cv, x, y, ang, s=1.0):
    a = math.radians(ang); ex, ey = x - math.cos(a) * 260 * s, y - math.sin(a) * 260 * s
    cv2.line(cv, (int(ex + 3), int(ey + 4)), (int(x + 3), int(y + 4)), (8.0, 10.0, 14.0), max(3, int(14 * s)), cv2.LINE_AA)
    cv2.line(cv, (int(ex), int(ey)), (int(x), int(y)), (30.0, 34.0, 40.0), max(3, int(12 * s)), cv2.LINE_AA)
    cv2.circle(cv, (int(x), int(y)), max(5, int(26 * s)), (60.0, 64.0, 72.0), -1, cv2.LINE_AA); cv2.circle(cv, (int(x - 6 * s), int(y - 7 * s)), max(3, int(10 * s)), (140.0, 148.0, 160.0), -1, cv2.LINE_AA)
    cv2.circle(cv, (int(x), int(y)), max(5, int(26 * s)), (20.0, 22.0, 28.0), 2, cv2.LINE_AA)


def lens(cv, x, y, r, T, i=0, a=1.0):
    r = int(r)
    cv2.circle(cv, (int(x + 6), int(y + 8)), r + 6, (6.0, 8.0, 12.0), -1, cv2.LINE_AA); cv2.circle(cv, (int(x), int(y)), r, (22.0, 24.0, 30.0), -1, cv2.LINE_AA)
    for k, (f, col) in enumerate(((0.86, (50.0, 52.0, 60.0)), (0.7, (30.0, 28.0, 34.0)), (0.5, (90.0, 50.0, 40.0)), (0.32, (40.0, 30.0, 70.0)), (0.16, (12.0, 12.0, 16.0)))):
        cv2.circle(cv, (int(x), int(y)), max(2, int(r * f)), col, -1, cv2.LINE_AA)
    cv2.circle(cv, (int(x - r * 0.28), int(y - r * 0.3)), max(3, int(r * 0.13)), (255.0 * a, 250.0 * a, 245.0 * a), -1, cv2.LINE_AA)
    cv2.circle(cv, (int(x + r * 0.22), int(y + r * 0.26)), max(2, int(r * 0.07)), (200.0 * a, 190.0 * a, 160.0 * a), -1, cv2.LINE_AA)


def flashes(cv, T, rate=1.0, n=7, y=(0.36, 0.60), cam=None, amp=1.0):
    r = np.random.default_rng(int(T * 18 * rate) % 997); lb = LightBuf()
    for i in range(n):
        if r.random() > 0.45:
            px = 1376 * (0.05 + 0.9 * r.random()); py = 768 * (y[0] + (y[1] - y[0]) * r.random()); q = bpt(cam, px, py) if cam else (px, py)
            lb.glow(q[0], q[1], 30 + 26 * r.random(), (255, 255, 255), 0.65 * min(amp, 1.2))
    lb.apply(cv, blur=14); cv += 14 * amp * (r.random() > 0.55)


def banknote(cv, x, y, s, rot):
    rrect(cv, x, y, 96 * s, 46 * s, rot, (118.0, 176.0, 128.0), edge=(40.0, 80.0, 50.0)); a = math.radians(rot)
    cv2.circle(cv, (int(x), int(y)), max(2, int(11 * s)), (80.0, 130.0, 90.0), -1, cv2.LINE_AA)


def coin(cv, x, y, s, T, i):
    sq = abs(math.cos(T * 6 + i)); cv2.ellipse(cv, (int(x), int(y)), (max(1, int(14 * s * sq)), max(2, int(14 * s))), 0, 0, 360, (60.0, 190.0, 240.0), -1, cv2.LINE_AA)
    cv2.ellipse(cv, (int(x), int(y)), (max(1, int(14 * s * sq)), max(2, int(14 * s))), 0, 0, 360, (30.0, 110.0, 160.0), 2, cv2.LINE_AA)


def home_bg(cv, T, cam, dark=0.8, moon=1.0, warm=0.0):
    plate(cv, 'h8_home', cam, 'b', gain=dark)
    lb = LightBuf(); q = bpt(cam, 150, 150); fl = 0.95 + 0.05 * math.sin(T * 0.8)
    lb.glow(q[0], q[1], 120 * cam.sb, (255 - 110 * warm, 215, 150 + 70 * (1 - warm)), (0.34 * moon) * fl); lb.glow(q[0], q[1], 520 * cam.sb, (255 - 150 * warm, 190 + 10 * warm, 120 + 110 * (1 - warm)), 0.20 * moon * fl); lb.apply(cv, blur=36)


# ---------------------------------------------------------------- 1. "usually the story ends here" (0 - 1.75)
def shot_ends(cv, T):
    k = seg(T, 0, 1.9); cam = site_cam(lerp(1.5, 1.38, k), 688, 560, 640, 470); site_bg(cv, T, cam, 1.0)
    items = site_crowd(T, 0.8, 0.0, 28, 21, ((250, 1150), (520, 700)), hop=1.4); draw_items(cv, cam, items, T)
    fireworks(cv, T, 0.1, 9); vignette(cv, 0.4, 2.0); motes(cv, T, 62, 20, 0.5, (230, 225, 200))


# ---------------------------------------------------------------- 2. the heroes are back, the families celebrate (1.75 - 4.5)
def shot_back(cv, T):
    P7.shot_families(cv, 63.0 + 0.55 * (T - 1.75)); fireworks(cv, T, 2.5, 12)
    r = np.random.default_rng(91)
    for i in range(36):
        x = r.random() * W; sp = 60 + 120 * r.random(); y = (H - ((T - 2.0) * sp + r.random() * 200)) % H; c = 150 + 100 * r.random()
        cv2.circle(cv, (int(x + 10 * math.sin(T * 3 + i)), int(y)), 1 + int(r.random() > .6), (c * .45, c * .8, c), -1, cv2.LINE_AA)


# ---------------------------------------------------------------- 3. the whole world followed the moment (4.5 - 6.6)
def shot_world(cv, T):
    k = seg(T, 4.4, 6.7); z = lerp(1.0, 1.22, k); cam = cam1(z, (640, 420), -30 * k * 0)
    plate(cv, 'h8_press', cam, 'b', gain=0.95); flashes(cv, T, 1.0, 9, cam=cam)
    for i, x in enumerate((140, 1140)): camera_prop(cv, x * 1.0, 700, 2.0 * z, T, i)
    vignette(cv, 0.4, 2.0); finish(cv, T, 150, 0.4, 0)


# ---------------------------------------------------------------- 4. and then everything ended: the lights go quiet (6.6 - 7.7)
def shot_over(cv, T):
    k = seg(T, 6.5, 7.8); cam = site_cam(lerp(1.5, 1.45, k), 688, 560, 640, 470); dk = 1.0 - 0.5 * ev(T, 6.7, 7.7); site_bg(cv, T, cam, dk)
    cheer = 0.8 * (1 - ev(T, 6.6, 7.1)); items = site_crowd(T, cheer, 0.0, 28, 21, ((250, 1150), (520, 700)), hop=1.4); draw_items(cv, cam, items, T)
    desat(cv, 0.3 * ev(T, 6.8, 7.7)); vignette(cv, 0.45 + 0.2 * k, 2.0); finish(cv, T, 151, 0.45, 8)


# ---------------------------------------------------------------- 5. "but the truth?" - one face, close (7.7 - 8.9)
def shot_truth(cv, T):
    k = seg(T, 7.6, 9.0); cam = cam1(lerp(1.15, 1.3, k), (640, 620)); home_bg(cv, T, cam, 0.5, 0.5); cv[:] = cv * 0.45 + cv2.GaussianBlur(cv, (0, 0), 12) * 0.55
    draw_items(cv, cam, [man8(640, 1070, .8, 1, 0.2, pose={'head': 2 * math.sin(T * 1.4) - 4 * ev(T, 7.9, 8.6), 'aL': 4, 'aR': 4}, gain=0.95, tint=MOON, crouch=0.0)], T)
    vignette(cv, 0.6, 2.0); finish(cv, T, 152, 0.6, 12)


# ---------------------------------------------------------------- 6. the story did not end when they came out (8.9 - 11.3): he walks away from the party
def shot_notend(cv, T):
    k = seg(T, 8.8, 11.4); cam = site_cam(1.3, 688, 560, 640, 470); site_bg(cv, T, cam, lerp(1.0, 0.7, ev(T, 9.0, 11.0)))
    items = site_crowd(T, 0.7 * (1 - ev(T, 9.0, 10.4)), 0.0, 24, 21, ((250, 1150), (520, 640)), hop=1.0); draw_items(cv, cam, items, T)
    wk = ev(T, 8.9, 10.6); x = lerp(840, 520, wk); mv = 1.0 if 0.02 < wk < 0.98 else 0.0
    draw_items(cv, cam, [man8(x, 700, .3, -1, 0.3, walk=mv, pose={'head': 8 + 10 * ev(T, 10.0, 11.0), 'aL': 8, 'aR': 8}, gain=0.98)], T)
    desat(cv, 0.45 * ev(T, 9.4, 11.0)); vignette(cv, 0.4 + 0.3 * k, 2.0); finish(cv, T, 153, 0.5, 14)


# ---------------------------------------------------------------- 7. for some of the men a new, harder story began (11.3 - 15.1)
def shot_new(cv, T):
    k = seg(T, 11.2, 15.2); cam = cam1(lerp(1.0, 1.14, k), (640, 520), -20 * k); home_bg(cv, T, cam, lerp(0.82, 0.6, ev(T, 13.0, 15.0)), 1.0)
    sit = ev(T, 11.5, 12.5)
    draw_items(cv, cam, [man8(840, 690, .6, 1, 0.3, crouch=0.5 * sit, pose={'head': 16 * sit + 2 * math.sin(T * 1.2), 'aL': 8, 'aR': 8 + 20 * sit, 'fR': -40 * sit}, gain=0.9, tint=MOON)], T)
    vignette(cv, 0.45, 2.0); finish(cv, T, 154, 0.5, 12)


# ---------------------------------------------------------------- 8. the shock did not vanish when they saw the sun (15.1 - 18.1)
def shot_sunshock(cv, T):
    k = seg(T, 15.0, 18.2); z = lerp(1.0, 1.15, k); cam = cam1(z, (640, 420)); focus(cam, 755, 330, 640 + 120 * (1 - k), 330)
    sh = ev(T, 15.6, 16.6); plate(cv, 'h7_sun', cam, 'b', gain=lerp(1.0, 0.55, sh)); sp = bpt(cam, 755, 330)
    hd = ev(T, 15.5, 16.3)
    draw_items(cv, cam, [man8(400, 700, .42, 1, 0.3, crouch=0.2 * hd, pose={'head': 22 * hd + 3 * math.sin(T * 8) * hd, 'aL': 4 + 114 * hd, 'fL': 140 * hd, 'aR': 4 + 114 * hd, 'fR': 140 * hd}, gain=1.0 - 0.2 * sh)], T)
    lb = LightBuf(); lb.glow(sp[0], sp[1], 90 * z, (255, 245, 220), 0.4 * (1 - sh)); lb.glow(sp[0], sp[1], 420 * z, (255, 220, 150), 0.2 * (1 - sh)); lb.apply(cv, blur=34)
    smoke(cv, T, 15.8, 18.2, 400 * 1.0, 330, 340, 300, 18, 0.45 * sh, 11); desat(cv, 0.5 * sh); vignette(cv, 0.3 + 0.3 * sh, 2.0); finish(cv, T, 155, 0.35, 14)


# ---------------------------------------------------------------- 9. some suffered (18.1 - 19.95): head in hands on the edge of the bed
def shot_suffer(cv, T):
    k = seg(T, 18.0, 20.0); cam = cam1(lerp(1.1, 1.22, k), (900, 560), -60 * k); home_bg(cv, T, cam, 0.6, 0.8)
    hd = ev(T, 18.3, 19.0)
    draw_items(cv, cam, [man8(900, 700, .62, -1, 0.3, crouch=0.6 * hd, pose={'head': 26 * hd, 'aL': 4 + 114 * hd, 'fL': 140 * hd, 'aR': 4 + 114 * hd, 'fR': 140 * hd}, gain=0.88, tint=MOON)], T)
    vignette(cv, 0.5, 2.0); finish(cv, T, 156, 0.55, 10)


# ---------------------------------------------------------------- 10. anxiety (19.95 - 20.6): trembling, fast breathing
def shot_anxiety(cv, T):
    k = seg(T, 19.9, 20.7); z = 1.12 + 0.015 * math.sin(T * 14); cam = cam1(z, (560, 420), 3 * math.sin(T * 31), 3 * math.cos(T * 27)); home_bg(cv, T, cam, 0.62, 0.8)
    tr = 1.0
    draw_items(cv, cam, [man8(560, 690, .55, 1, 0.3, pose={'head': 6 + 3 * math.sin(T * 17), 'aL': 118 + 4 * math.sin(T * 40), 'fL': 140 + 6 * math.sin(T * 38), 'aR': 4 + 20 * math.sin(T * 29), 'fR': 10 * math.sin(T * 33)}, gain=0.9, tint=MOON)], T)
    desat(cv, 0.2); vignette(cv, 0.55, 2.0); finish(cv, T, 157, 0.55, 14)


# ---------------------------------------------------------------- 11. nightmares (20.6 - 21.35): lying, jerks awake, dark smoke
def shot_nightmare(cv, T):
    k = seg(T, 20.5, 21.4); cam = cam1(lerp(1.1, 1.18, k), (960, 520)); home_bg(cv, T, cam, 0.5, 0.45)
    up = ev(T, 20.95, 21.15); tw = math.sin(T * 25) * (1 - up) * 3
    draw_items(cv, cam, [man8(lerp(1060, 940, up), lerp(525, 700, up), lerp(.5, .62, up), -1, 0.3, crouch=0.0, rot=-84 * (1 - up) + tw, dy=455 * (1 - up), pose={'head': 0 + 14 * up, 'aL': 4 + 114 * up, 'fL': 140 * up, 'aR': 8 + 30 * up}, gain=0.85, tint=MOON)], T)
    smoke(cv, T, 20.6, 21.4, 960, 480, 560, 300, 24, 0.5 * (1 - up * 0.3), 12); cv += 50 * P(T, 20.95, 21.1); vignette(cv, 0.6, 2.0); finish(cv, T, 158, 0.6, 10)


# ---------------------------------------------------------------- 12. depression (21.35 - 22.65): by the window, the colour drains
def shot_depress(cv, T):
    k = seg(T, 21.3, 22.8); cam = cam1(lerp(1.0, 1.18, k), (500, 540), 40 * k); home_bg(cv, T, cam, lerp(0.7, 0.45, k), 0.6)
    sg = ev(T, 21.4, 22.4)
    draw_items(cv, cam, [man8(340, 690, .56, -1, 0.3, crouch=0.5 * sg, pose={'head': 20 * sg, 'aL': 4, 'aR': 4}, gain=0.85, tint=MOON)], T)
    desat(cv, 0.75 * sg); vignette(cv, 0.6, 2.0); finish(cv, T, 159, 0.6, 8)


# ---------------------------------------------------------------- 13. problems returning to normal life (22.65 - 25.25): everyone walks by, he stands still
WALK = [(('w', 'ar', 'm')[i % 3], 1 if i % 2 == 0 else -1, 560 + 70 * (i % 4), 0.25 + 0.04 * (i % 3), 0.8 + 0.15 * i) for i in range(10)]


def shot_normal8(cv, T):
    k = seg(T, 22.6, 25.3); cam = cam1(lerp(1.0, 1.12, k), (640, 560)); plate(cv, 'h8_street', cam, 'b', gain=0.95); items = []
    for i, (ch, d, gy, sc, sp) in enumerate(WALK):
        ph = (T * 0.075 * sp + i * 0.31) % 1.0; x = (ph * 1500 - 110) if d > 0 else (1390 - ph * 1500)
        items.append(mk(ch, x, gy, sc, d, i * 1.7, walk=1.0, pose={'aL': 12, 'aR': 12, 'head': 0}, gain=0.95, tint=(1.02, 1.02, 1.0), shirt=SHIRTS[(i * 3 + 2) % 10] if ch == 'm' else None, pants=PANTS[(i * 5 + 1) % 10] if ch == 'm' else None))
    fz = ev(T, 22.9, 23.6)
    items.append(man8(640, 700, .42, 1, 0.3, pose={'head': 14 * fz + 2 * math.sin(T * 1.5), 'aL': 6 + 40 * fz, 'aR': 6, 'fL': -20 * fz}, gain=0.98, tint=(1.0 - 0.1 * fz, 1.0 - 0.05 * fz, 1.0)))
    items.sort(key=lambda d_: d_['gy']); draw_items(cv, cam, items, T)
    desat(cv, 0.3 * fz); vignette(cv, 0.3, 2.0); finish(cv, T, 160, 0.3, 14)


# ---------------------------------------------------------------- 14. some could not work in the mines again (25.25 - 28.7)
def shot_gate(cv, T):
    k = seg(T, 25.2, 28.8); cam = cam1(lerp(1.0, 1.2, k), (640, 600), -40 * k); plate(cv, 'h8_gate', cam, 'b', gain=lerp(1.0, 0.7, ev(T, 26.5, 28.5)))
    wk = ev(T, 25.3, 26.5); rt = ev(T, 27.0, 28.2); x = lerp(300, 520, wk) - 160 * rt; mv = 1.0 if (0.02 < wk < 0.98 or 0.02 < rt < 0.98) else 0.0
    fl = 1 if rt < 0.5 else -1
    ex = ev(T, 26.5, 26.95) * (1 - ev(T, 27.0, 27.3))
    draw_items(cv, cam, [man8(x, 700, .56, fl, 0.3, walk=mv, pose={'head': 4 + 16 * ev(T, 27.2, 28.2), 'aL': 8 + 100 * ex, 'aR': 8, 'fL': 10 * ex}, gain=0.96, tint=(1.0, 0.98, 0.95))], T)
    puffs(cv, T, 25.2, 28.8, 16, (0, 520, 1280, 160), (120, 130, 150), seed=161, size=(50, 130), rise=(-10, 20), life=2.0, alpha=0.18, wind=(30, 0))
    desat(cv, 0.4 * ev(T, 27.0, 28.5)); vignette(cv, 0.35 + 0.25 * k, 2.0); finish(cv, T, 161, 0.4, 14)


# ---------------------------------------------------------------- 15. sudden fame was not always easy (28.7 - 32.45)
def press_man(cv, T, cam, hands, cx=640, gy=720, sc=.5, ph=0.3):
    draw_items(cv, cam, [man8(cx, gy, sc, 1, ph, pose={'head': -6 * (1 - hands) + 10 * hands, 'aL': 8 + 110 * hands, 'fL': 80 * hands, 'aR': 8 + 90 * hands, 'fR': 70 * hands}, gain=0.98, tint=(1.04, 1.04, 1.04))], T)


def shot_fame(cv, T):
    k = seg(T, 28.7, 32.5); cam = cam1(lerp(1.0, 1.18, k), (640, 600)); plate(cv, 'h8_press', cam, 'b', gain=0.95)
    hands = ev(T, 29.6, 30.2) * (1 - 0.3 * ev(T, 31.0, 32.0)); press_man(cv, T, cam, hands)
    flashes(cv, T, 1.1, 10, cam=cam, amp=1.0 + 0.5 * k); vignette(cv, 0.4, 2.0); finish(cv, T, 162, 0.3, 0)


# ---------------------------------------------------------------- 16. interviews, ads (32.45 - 33.5): microphones, a billboard "$"
def shot_interview(cv, T):
    k = seg(T, 32.4, 33.6); cam = cam1(lerp(1.05, 1.15, k), (640, 600)); plate(cv, 'h8_press', cam, 'b', gain=0.9)
    sp = ev(T, 32.5, 33.3); press_man(cv, T, cam, 0.0)
    for i, (x0, y0, ang) in enumerate(((60, 520, 12), (1220, 480, 168), (240, 280, 40), (1060, 260, 140))):
        e = ev(T, 32.5 + 0.1 * i, 32.9 + 0.1 * i); tx, ty = 640 + (x0 - 640) * (1 - 0.65 * e), 380 + (y0 - 380) * (1 - 0.6 * e); mic(cv, tx, ty, ang, 1.2)
    ad = ev(T, 33.0, 33.4); tmp = np.zeros((H, W, 3), np.uint8)
    if ad > 0:
        rrect(cv, 1080, 130, 300 * ad, 170 * ad, -4, (60.0, 190.0, 240.0)); cv2.putText(tmp, '$', (1010, 195), cv2.FONT_HERSHEY_DUPLEX, 4.0 * ad, (30, 20, 140), 8, cv2.LINE_AA); cv += tmp.astype(np.float32)
    flashes(cv, T, 1.2, 8, cam=cam); vignette(cv, 0.4, 2.0); finish(cv, T, 163, 0.3, 0)


# ---------------------------------------------------------------- 17. money, disputes (33.5 - 34.6)
def shot_money(cv, T):
    k = seg(T, 33.4, 34.7); cam = cam1(lerp(1.0, 1.1, k), (640, 600)); plate(cv, 'h8_street', cam, 'b', gain=0.62)
    arg = ev(T, 33.9, 34.3); items = []
    items.append(mk('m', 400, 700, .58, 1, 0.5, pose={'aL': 8 + 70 * arg * (0.6 + 0.4 * math.sin(T * 9)), 'fL': 10, 'aR': 8, 'head': -4 * arg}, shirt=SHIRTS[2], pants=PANTS[1], gain=0.95, mouth=speak(T, 1.0, 1.0) * arg))
    items.append(mk('m', 880, 700, .58, -1, 1.5, pose={'aL': 8, 'aR': 8 + 80 * arg * (0.6 + 0.4 * math.cos(T * 8)), 'fR': 10, 'head': 4 * arg}, shirt=SHIRTS[6], pants=PANTS[3], gain=0.95, mouth=speak(T, 2.0, 1.0) * arg))
    draw_items(cv, cam, items, T)
    r = np.random.default_rng(171)
    for i in range(26):
        t0 = 33.5 + 0.8 * r.random(); tt = T - t0
        if tt < 0: continue
        x = 80 + 1120 * r.random() + 30 * math.sin(tt * 4 + i); y = -40 + 520 * tt * (0.8 + 0.5 * r.random())
        if y > 760: continue
        if i % 3: banknote(cv, x, y, 0.6 + 0.3 * r.random(), 40 * math.sin(tt * 5 + i) + 20 * i % 90)
        else: coin(cv, x, y, 1.2, T, i)
    vignette(cv, 0.4, 2.0); finish(cv, T, 164, 0.3, 0)


# ---------------------------------------------------------------- 18. and camera lenses (34.6 - 35.5) everywhere (35.5 - 37.1)
def shot_lenses(cv, T):
    k = seg(T, 34.5, 37.2); cam = cam1(lerp(1.0, 1.05, k), (640, 600)); plate(cv, 'h8_press', cam, 'b', gain=0.8); press_man(cv, T, cam, 0.8)
    r = np.random.default_rng(181)
    for i in range(10):
        t0 = 34.6 + 0.2 * i; e = ev(T, t0, t0 + 0.5)
        if e <= 0: continue
        ang = (i / 10.0) * 2 * math.pi + 0.3; d = 520 * (1 - 0.35 * e) + 40 * (i % 3); rx = 640 + math.cos(ang) * d * 1.3; ry = 380 + math.sin(ang) * d * 0.75
        lens(cv, rx, ry, (60 + 45 * (i % 3)) * (0.4 + 0.6 * e), T, i)
    flashes(cv, T, 1.5, 12, cam=cam, amp=1.0); vignette(cv, 0.5, 2.0); finish(cv, T, 165, 0.3, 0)


# ---------------------------------------------------------------- 19. "because there is a big difference between surviving..." the flashes die, he stands alone (37.1 - 39.7)
def shot_alone8(cv, T):
    k = seg(T, 37.0, 39.8); cam = cam1(lerp(1.0, 1.35, ev(T, 37.0, 39.8)), (640, 640)); fd = 1 - ev(T, 37.3, 39.2)
    plate(cv, 'h8_press', cam, 'b', gain=lerp(0.9, 0.4, 1 - fd)); press_man(cv, T, cam, 0.8 * (1 - ev(T, 37.6, 38.4)) + 0.0)
    flashes(cv, T, 1.2, 10, cam=cam, amp=1.2 * fd); desat(cv, 0.5 * (1 - fd)); vignette(cv, 0.4 + 0.4 * (1 - fd), 2.0); finish(cv, T, 166, 0.5, 12)


# ---------------------------------------------------------------- 20. surviving death (39.7 - 42.3): at the window in the moonlight
def shot_window(cv, T):
    k = seg(T, 39.6, 42.4); cam = cam1(lerp(1.0, 1.12, k), (400, 520), 20 * k); home_bg(cv, T, cam, 0.7, 1.0)
    draw_items(cv, cam, [man8(300, 690, .55, -1, 0.3, pose={'head': 2 * math.sin(T * 1.0) - 6 * ev(T, 40.0, 41.5), 'aL': 8, 'aR': 8}, gain=0.9, tint=MOON)], T)
    vignette(cv, 0.5, 2.0); finish(cv, T, 167, 0.5, 12)


# ---------------------------------------------------------------- 21. ... and knowing how to live after it (42.3 - end): the first light of dawn
def shot_dawn(cv, T):
    k = seg(T, 42.2, D8); wm = ev(T, 42.4, 44.4); cam = cam1(lerp(1.12, 1.25, k), (400, 520), 20 + 20 * k); home_bg(cv, T, cam, lerp(0.7, 1.05, wm), 1.0 + 1.0 * wm, warm=wm)
    tn = ev(T, 42.6, 43.8)
    draw_items(cv, cam, [man8(lerp(300, 330, tn), 690, .55, -1, 0.3, pose={'head': -8 * tn, 'aL': 8 + 30 * tn, 'fL': -20 * tn, 'aR': 8}, gain=0.95, tint=(lerp(0.86, 1.08, wm), lerp(0.95, 1.0, wm), lerp(1.14, 0.9, wm)))], T)
    lb = LightBuf(); q = bpt(cam, 150, 150); lb.glow(q[0], q[1], 260 * cam.sb, (120, 200, 255), 0.35 * wm); lb.apply(cv, blur=40)
    tone(cv, 1.0, 0, (1.0 + 0.06 * wm, 1.0, 1.0 - 0.04 * wm), 1.0); vignette(cv, 0.4, 2.0); finish(cv, T, 168, 0.3 + 0.2 * (1 - wm), 14)


SHOTS8 = [('ends', 0.0, 1.75, shot_ends, 0.0), ('back', 1.75, 4.5, shot_back, 0.3), ('world', 4.5, 6.6, shot_world, 0.3), ('over', 6.6, 7.7, shot_over, 0.3), ('truth', 7.7, 8.9, shot_truth, 0.3),
          ('notend', 8.9, 11.3, shot_notend, 0.4), ('new', 11.3, 15.1, shot_new, 0.4), ('sunshock', 15.1, 18.1, shot_sunshock, 0.4), ('suffer', 18.1, 19.95, shot_suffer, 0.3), ('anxiety', 19.95, 20.6, shot_anxiety, 0.1),
          ('nightmare', 20.6, 21.35, shot_nightmare, 0.1), ('depress', 21.35, 22.65, shot_depress, 0.2), ('normal', 22.65, 25.25, shot_normal8, 0.3), ('gate', 25.25, 28.7, shot_gate, 0.4), ('fame', 28.7, 32.45, shot_fame, 0.4),
          ('interview', 32.45, 33.5, shot_interview, 0.1), ('money', 33.5, 34.6, shot_money, 0.1), ('lenses', 34.6, 37.1, shot_lenses, 0.2), ('alone', 37.1, 39.7, shot_alone8, 0.4), ('window', 39.7, 42.3, shot_window, 0.4),
          ('dawn', 42.3, D8, shot_dawn, 0.5)]


class Part8:
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTS8):
            hi = t1 + (SHOTS8[i + 1][4] / 2 if i + 1 < len(SHOTS8) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTS8) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
