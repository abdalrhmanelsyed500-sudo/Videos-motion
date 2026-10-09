"""Part 6 (Arabic, 62.35 s): the supplies come down the narrow tube, the lifeline, the world sees them, NASA, the mind problem,
the routine, the rescue plans, time. Same STYLE LOCK as parts 1-5. No captions, no music."""
from part5_scenes import *
import part5_scenes as P5
from part3_scenes import food_at, table_bg, table_fg, table_cam, CLOCK, storage_bg, storage_cam

D6 = 62.35
BLUEW = (0.95, 1.04, 1.12)            # cold "camera light" tint


# ---------------------------------------------------------------- procedural props
_cap = {}


def capsule_layer():
    if not _cap:
        w, h = 80, 200; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); u = xx / (w - 1)
        sh = 0.40 + 0.75 * np.exp(-((u - 0.34) / 0.20) ** 2) + 0.2 * np.exp(-((u - 0.82) / 0.1) ** 2) - 0.25 * u
        rr = np.random.default_rng(3).normal(0, 1, (h, w)).astype(np.float32); rr = cv2.GaussianBlur(rr, (0, 0), 1.3)
        img = np.zeros((h, w, 3), np.float32); img[:] = np.array((165, 178, 188), np.float32)
        img *= (sh + 0.08 * rr)[..., None]
        for y0, y1 in ((22, 40), (h - 56, h - 38)): img[y0:y1] = img[y0:y1] * 0.3 + np.array((40, 52, 200), np.float32) * (sh[y0:y1, :, None] + 0.1) * 0.7
        m = np.zeros((h, w), np.float32); cv2.rectangle(m, (4, 40), (w - 5, h - 40), 1.0, -1); cv2.ellipse(m, (w // 2, 40), (w // 2 - 4, 36), 0, 180, 360, 1.0, -1); cv2.ellipse(m, (w // 2, h - 40), (w // 2 - 4, 30), 0, 0, 180, 1.0, -1)
        m = cv2.GaussianBlur(m, (0, 0), 1.0); edge = cv2.GaussianBlur(m, (0, 0), 3) < 0.9
        img[edge] *= 0.55
        img = np.clip(img, 0, 255); _cap['l'] = Layer.from_array(np.dstack([img * m[..., None], m]))
    return _cap['l']


def draw_capsule(cv, x, y, s, rot=0.0, gain=0.95, tint=None):
    """x,y = top-centre of the capsule (screen), s = scale (capsule is 80x200 at s=1)"""
    place(cv, capsule_layer(), M3(x, y, s, s, rot, 40, 0), gain=gain, tint=tint)


def shade_ell(cv, x, y, rx, ry, a=0.4):
    m = np.zeros((H, W), np.float32); cv2.ellipse(m, (int(x), int(y)), (max(1, int(rx)), max(1, int(ry))), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 3)[..., None]; cv *= (1 - a * m)


def rrect(cv, cx, cy, w, h, rot, col, edge=(20.0, 26.0, 36.0)):
    a = math.radians(rot); R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    pts = (np.array([[-w, -h], [w, -h], [w, h], [-w, h]], np.float32) / 2.0) @ R.T + np.array([cx, cy], np.float32)
    cv2.fillConvexPoly(cv, (pts + np.array([3, 4])).astype(np.int32), (8.0, 10.0, 16.0), cv2.LINE_AA)
    cv2.fillConvexPoly(cv, pts.astype(np.int32), tuple(float(c) for c in col), cv2.LINE_AA)
    cv2.polylines(cv, [pts.astype(np.int32)], True, edge, 1, cv2.LINE_AA); return pts


def item_draw(cv, kind, x, y, s, rot=0.0, cam=None):
    if kind == 'bottle':
        rrect(cv, x, y, 30 * s, 62 * s, rot, (215.0, 170.0, 95.0)); rrect(cv, x, y - 34 * s, 16 * s, 12 * s, rot, (235.0, 235.0, 240.0))
        cv2.line(cv, (int(x - 7 * s), int(y - 18 * s)), (int(x - 7 * s), int(y + 18 * s)), (250.0, 235.0, 200.0), max(1, int(2 * s)), cv2.LINE_AA)
    elif kind == 'med':
        rrect(cv, x, y, 58 * s, 40 * s, rot, (236.0, 236.0, 242.0)); cv2.rectangle(cv, (int(x - 4 * s), int(y - 14 * s)), (int(x + 4 * s), int(y + 14 * s)), (30.0, 30.0, 200.0), -1); cv2.rectangle(cv, (int(x - 14 * s), int(y - 4 * s)), (int(x + 14 * s), int(y + 4 * s)), (30.0, 30.0, 200.0), -1)
    elif kind == 'letter':
        pts = rrect(cv, x, y, 66 * s, 44 * s, rot, (172.0, 208.0, 228.0)); a = math.radians(rot)
        c, sn = math.cos(a), math.sin(a)
        for sx in (-1, 1): cv2.line(cv, (int(x + sx * 33 * s * c + 22 * s * sn), int(y + sx * 33 * s * sn - 22 * s * c)), (int(x), int(y + 4 * s)), (95.0, 135.0, 170.0), 1, cv2.LINE_AA)
    elif kind == 'ball': cv2.circle(cv, (int(x), int(y)), max(2, int(15 * s)), (60.0, 150.0, 225.0), -1, cv2.LINE_AA); cv2.circle(cv, (int(x - 4 * s), int(y - 5 * s)), max(1, int(5 * s)), (140.0, 210.0, 250.0), -1, cv2.LINE_AA)
    elif kind == 'cards': rrect(cv, x - 5 * s, y, 34 * s, 46 * s, rot - 10, (235.0, 235.0, 235.0)); rrect(cv, x + 7 * s, y, 34 * s, 46 * s, rot + 8, (225.0, 225.0, 232.0)); cv2.circle(cv, (int(x + 7 * s), int(y)), max(2, int(6 * s)), (30.0, 30.0, 190.0), -1, cv2.LINE_AA)
    elif kind == 'beads':
        for j in range(9):
            t = j / 8.0; cv2.circle(cv, (int(x + (t - 0.5) * 46 * s), int(y + math.sin(t * math.pi) * 18 * s)), max(2, int(4 * s)), (70.0, 90.0, 190.0), -1, cv2.LINE_AA)


def cable(cv, pts, w=3, col=(25.0, 30.0, 38.0), hi=(90.0, 100.0, 112.0)):
    p = np.array(pts, np.int32); cv2.polylines(cv, [p + np.array([2, 3])], False, (8.0, 10.0, 14.0), w + 1, cv2.LINE_AA); cv2.polylines(cv, [p], False, col, w, cv2.LINE_AA)
    cv2.polylines(cv, [p - np.array([1, 0])], False, hi, max(1, w // 3), cv2.LINE_AA)


def gen_men(T, xs, gy, sc, chs=None, **kw):
    return sit_row(xs, gy, sc, T, chs=chs, **kw)


def cold(cv, T, a=0.5):
    """camera-feed look: cool tint, scanlines, slight noise flicker"""
    tone(cv, 1.0, 0, (1.0, 1.0 - 0.0, 1.0), 1.0)
    cv[..., 0] *= 1 + 0.10 * a; cv[..., 2] *= 1 - 0.07 * a
    ln = (0.93 + 0.07 * np.sin(np.arange(H, dtype=np.float32) * 2.2 + T * 6))[:, None, None]; cv *= (1 - a * 0.5) + a * 0.5 * ln
    r = np.random.default_rng(int(T * 30) % 97); band = int(r.integers(0, H - 6)); cv[band:band + 2] *= 1.0 + 0.10 * a * (r.random() > 0.6)


# ---------------------------------------------------------------- 1. the rescuers know where they are (0 - 1.9)
def shot_know(cv, T): P4.shot_rig(cv, 29.4 + 0.8 * T)


# ---------------------------------------------------------------- 2. a very narrow tube: capsules slide down the pipe (1.9 - 5.0)
def depth_view(cv, T, cyp, zz=1.0, gain=0.95):
    sS = 2.0 * S0; sc = sS * zz; ox = 688 * S0 * zz * 2.0 - W / 2; oy = cyp * S0 * zz * 2.0 - H / 2
    place(cv, L('h5_depth'), M3(-ox, -oy, sc, sc, 0, 0, 0), gain=gain)
    return sc, ox, oy


def shot_tube(cv, T):
    k = ev(T, 1.8, 5.2); zz = 1.0 + 0.12 * k; cyp = min(lerp(230, 560, k), 768 - 192 / zz)
    sc, ox, oy = depth_view(cv, T, cyp, zz)
    lb = LightBuf(); q = (688 * sc - ox, 685 * sc - oy); fl = 0.85 + 0.15 * flick(T, 2.0)
    lb.glow(q[0], q[1], 70 * zz, (110, 190, 255), 0.5 * fl); lb.glow(q[0], q[1], 330 * zz, (60, 130, 230), 0.3 * fl)
    for j in range(3):
        u = ((T - 1.9) * 0.42 + j * 0.34) % 1.0
        if T < 1.9 + j * 0.8: continue
        yp = 160 + 500 * u; X = 688 * sc - ox; Y = yp * sc - oy
        draw_capsule(cv, X, Y - 35, 0.45 * zz, gain=1.0)
        lb.glow(X, Y, 40 * zz, (120, 200, 255), 0.45)
    lb.apply(cv, blur=26); motes(cv, T, 56, 24, 0.4, (210, 200, 180)); vignette(cv, 0.35, 2.0); finish(cv, T, 91, 0.45, 12)


# ---------------------------------------------------------------- 3. the supplies arrive in the chamber (5.0 - 9.9)
MEN3 = [(300, 696, .52, 1, 'm'), (455, 704, .54, 1, 'u'), (825, 704, .54, -1, 'g'), (980, 696, .52, -1, 'm'), (170, 652, .38, 1, 'm'), (1110, 652, .38, -1, 'j'), (560, 650, .30, 1, 'v'), (730, 650, .30, -1, 'y')]
ITEMS3 = [('tin', 5.0, 0), ('bottle', 5.6, 3), ('med', 6.2, 1), ('letter', 6.9, 2), ('ball', 7.4, 4), ('cards', 7.8, 5), ('beads', 8.2, 6), ('tin2', 8.6, 7)]


def shot_supply(cv, T):
    k = seg(T, 4.9, 10.0); cam = Cam(A=(640, 560), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.20, k), sc=lerp(1.0, 1.12, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.66, lamps=0.9)
    items = []
    for i, c in enumerate(GRID):
        if abs(c['x'] - 640) < 170 and c['gy'] > 600: continue
        items.append(dict(c, pose={'head': -6 * ev(T, 5.0, 5.6) + 2 * math.sin(T + i), 'aL': 4, 'aR': 4}, crouch=0.12, gain=0.74, tint=CT, sway=0.2))
    cap_e = ev(T, 4.9, 5.5); sw_ = 1 if T < 5 else 0
    for i, (x, gy, sc, fl_, ch) in enumerate(MEN3):
        t_i = [it for it in ITEMS3 if it[2] == i]; got = 0.0
        if t_i: got = ev(T, t_i[0][1] + 0.45, t_i[0][1] + 0.9) * (1 - ev(T, t_i[0][1] + 2.3, t_i[0][1] + 2.8))
        pose = {'aL': 8 + 40 * got, 'aR': 8 + 55 * got, 'fL': -40 * got, 'fR': -50 * got, 'head': (10 if x < 640 else -10) * got + 3 * math.sin(T * 1.3 + i), 'aL_': 0}
        pose.pop('aL_')
        items.append(mk(ch, x, gy, sc, fl_, i * 1.3, pose=pose, gain=0.9, tint=CT, shirt=SHIRTS[(i * 3 + 1) % 10] if ch == 'm' else None, pants=PANTS[(i * 7 + 2) % 10] if ch == 'm' else None, crouch=0.12 * (1 - got), mouth=speak(T, i, .5) * got * 0.6))
    draw_items(cv, cam, items, T)
    ceiling_hole(cv, cam, 0.6, T, 640, 80, 50, cracks=False, light=0.35)
    # the narrow tube and the capsule
    bob = 3 * math.sin(T * 2.0); cy_ = lerp(-80, 230, ev(T, 4.8, 5.5))
    top = cam.pt(640, -40); bot = cam.pt(640, cy_ + 8 + bob)
    cable(cv, [top, bot], w=max(3, int(8 * cam.sc)), col=(70.0, 82.0, 92.0), hi=(170.0, 185.0, 195.0))
    cs = 0.62 * cam.sc; cx_, cyy = cam.pt(640, cy_ + bob); draw_capsule(cv, cx_, cyy, cs, rot=1.5 * math.sin(T * 1.7), gain=0.98, tint=HOT)
    lb = LightBuf(); lb.glow(cx_, cyy + 100 * cs, 120 * cam.sc, (120, 200, 255), 0.25); lb.apply(cv, blur=26)
    # items drop out of the capsule into the men's hands
    for nm, t0, mi in ITEMS3:
        x, gy, sc, fl_, ch = MEN3[mi]; e = clamp((T - t0) / 0.55)
        if e <= 0: continue
        got = ev(T, t0 + 0.45, t0 + 0.9); gone = ev(T, t0 + 2.3, t0 + 2.8)
        if gone >= 1: continue
        hx = x + (24 if x < 640 else -24) * 1.0; hy = gy - 560 * sc
        sx = lerp(640, hx, ease_out(e)) + 14 * math.sin(e * 5); sy = lerp(cy_ + 190 * 0.62, hy, e * e * 0.6 + 0.4 * e) - 60 * math.sin(e * math.pi)
        if got > 0: sx = hx; sy = hy - 20 * got
        Xs, Ys = cam.pt(sx, sy); s = (1.0 - 0.3 * gone) * cam.sc * (0.62 if mi in (4, 5, 6) else 0.8)
        if nm.startswith('tin'): food_at(cv, cam, 'food_0' if nm == 'tin' else 'food_3', sx, sy + 20, .15 * (1 - 0.3 * gone), e=1.0, rot=12 * math.sin(e * 6) * (1 - got), dark=1.0)
        else: item_draw(cv, nm, Xs, Ys, s, rot=18 * math.sin(e * 5) * (1 - got))
    puffs(cv, T, 4.9, 10.0, 10, (500, 0, 280, 60), (150, 175, 200), seed=92, size=(30, 70), rise=(20, 50), life=2.0, alpha=0.12)
    tone(cv, 1.0, 0, (0.96, 1.0, 1.06), 1.0); veil(cv, T, 0.04); finish(cv, T, 92, 0.5, 20)


# ---------------------------------------------------------------- 4. the tube becomes a lifeline (9.9 - 13.1)
def shot_lifeline(cv, T):
    k = seg(T, 9.8, 13.2); zz = lerp(0.56, 0.74, k); cyp = lerp(384, 400, k)
    sc, ox, oy = depth_view(cv, T, cyp, zz, 0.9)
    # a warm pulse of light climbing... and running down the pipe
    lb = LightBuf(); X = 688 * sc - ox
    for j in range(5):
        u = ((T - 10.0) * 0.38 + j * 0.2) % 1.0; yp = lerp(150, 685, u if j % 2 == 0 else u); Y = yp * sc - oy
        a = 0.9 * math.sin(u * math.pi); lb.glow(X, Y, 44 * zz, (140, 215, 255), a); lb.glow(X, Y, 150 * zz, (70, 150, 240), 0.35 * a)
    q = (X, 685 * sc - oy); beat = 0.5 + 0.5 * math.sin(T * 5.0)
    lb.glow(q[0], q[1], 80 * zz, (110, 190, 255), 0.5 + 0.3 * beat); lb.glow(q[0], q[1], 360 * zz, (60, 130, 230), 0.3 + 0.12 * beat)
    lb.apply(cv, blur=24)
    cv2.line(cv, (int(X), 0), (int(X), H), (190.0, 225.0, 250.0), 1, cv2.LINE_AA) if False else None
    motes(cv, T, 57, 26, 0.4, (210, 200, 180)); vignette(cv, 0.4, 2.0); finish(cv, T, 93, 0.5, 12)


# ---------------------------------------------------------------- 5. suddenly the world could see them (13.1 - 16.05)
def shot_see(cv, T):
    k = seg(T, 13.0, 16.1); cam = Cam(A=(640, 560), sb=lerp(1.05, 1.18, k), sw=lerp(1.1, 1.30, k), sc=lerp(1.05, 1.20, k), d=(0, 0), dw=(0, 0))
    lit = ev(T, 13.15, 13.6)
    chamber_bg(cv, T, cam, 0.52, lamps=0.55)
    items = []
    for i, c in enumerate(GRID):
        if abs(c['x'] - 640) < 150 and c['gy'] > 640: continue
        up = ev(T, 13.4 + 0.02 * i, 14.0 + 0.02 * i); w_ = math.sin(T * 6 + i * 1.7) * ev(T, 14.6, 15.2) * (i % 3 == 0)
        items.append(dict(c, pose={'head': -14 * up + 2 * math.sin(T + i), 'aL': 4 + 110 * w_ * 0 + 60 * ev(T, 14.6, 15.2) * (i % 3 == 0) * (0.6 + 0.4 * w_), 'aR': 4}, crouch=0.08, gain=0.8, tint=BLUEW, sway=0.2))
    items.append(mk('u', 640, 724, .56, 1, 0.4, pose={'head': -16 * ev(T, 13.4, 14.0), 'aL': 8 + 60 * ev(T, 14.4, 15.0) * (0.7 + 0.3 * math.sin(T * 6)), 'aR': 8}, gain=0.8, tint=BLUEW, crouch=0.04))
    draw_items(cv, cam, items, T)
    ceiling_hole(cv, cam, 0.7, T, 640, 80, 70, cracks=False, light=1.6 * lit)
    # the cold camera light from the tube
    lb = LightBuf(); q = cam.pt(640, 40); lb.glow(q[0], q[1], 90 * cam.sc, (255, 240, 220), 0.7 * lit); lb.glow(q[0], q[1], 420 * cam.sc, (255, 230, 200), 0.3 * lit); lb.apply(cv, blur=28)
    cv += 60 * P(T, 13.15, 13.5)
    tone(cv, 1.0, 0, (0.96, 1.0, 1.08), 1.0); cold(cv, T, 0.5 * lit); finish(cv, T, 94, 0.5, 14)


# ---------------------------------------------------------------- 6-9. close-ups seen through the camera (16.05 - 21.06)
def cu_bg(cv, T, cam, dark=0.5):
    chamber_bg(cv, T, cam, dark, lamps=0.55); cv[:] = cv * 0.5 + cv2.GaussianBlur(cv, (0, 0), 10) * 0.5


def shot_thin(cv, T):
    k = seg(T, 16.0, 17.6); cam = Cam(A=(640, 620), sb=lerp(1.2, 1.3, k), sw=lerp(1.3, 1.5, k), sc=lerp(1.2, 1.32, k), d=(0, 0), dw=(0, 0)); cu_bg(cv, T, cam, 0.5)
    items = [mk('g', 400, 1040, .8, 1, 0.2, pose={'head': -4 + 3 * math.sin(T * 1.5), 'aL': 4, 'aR': 4}, gain=0.95, tint=BLUEW, crouch=0.0), mk('m', 880, 1030, .8, -1, 1.4, pose={'head': 5 + 3 * math.sin(T * 1.3), 'aL': 4, 'aR': 4}, shirt=SHIRTS[4], pants=PANTS[2], gain=0.95, tint=BLUEW, crouch=0.0)]
    draw_items(cv, cam, items, T); cold(cv, T, 0.6); finish(cv, T, 95, 0.55, 14)


def shot_tired(cv, T):
    k = seg(T, 17.4, 18.8); cam = Cam(A=(640, 620), sb=lerp(1.2, 1.3, k), sw=lerp(1.3, 1.5, k), sc=lerp(1.2, 1.32, k), d=(0, 0), dw=(0, 0)); cu_bg(cv, T, cam, 0.5)
    nod = ev(T, 17.6, 18.4)
    items = [mk('j', 640, 1110, .88, 1, 0.2, pose={'head': 14 * nod + 3 * math.sin(T * 1.4), 'aL': 4 + 20 * nod, 'fL': 0, 'aR': 4}, gain=0.95, tint=BLUEW, crouch=0.0)]
    draw_items(cv, cam, items, T); cold(cv, T, 0.6); finish(cv, T, 96, 0.55, 14)


def shot_beards(cv, T):
    k = seg(T, 18.6, 19.9); cam = Cam(A=(640, 620), sb=lerp(1.2, 1.3, k), sw=lerp(1.3, 1.5, k), sc=lerp(1.2, 1.32, k), d=(0, 0), dw=(0, 0)); cu_bg(cv, T, cam, 0.5)
    stroke_ = ev(T, 18.9, 19.5)
    items = [mk('s', 470, 1040, .8, 1, 0.2, pose={'head': 3 * math.sin(T * 1.4), 'aL': 4, 'aR': 4 + 118 * stroke_, 'fR': 140 * stroke_ * 0.8 + 10 * math.sin(T * 8) * stroke_}, gain=0.95, tint=BLUEW, crouch=0.0),
             mk('v', 880, 1030, .78, -1, 1.4, pose={'head': -4 + 3 * math.sin(T * 1.3), 'aL': 4, 'aR': 4}, gain=0.95, tint=BLUEW, crouch=0.0)]
    draw_items(cv, cam, items, T); cold(cv, T, 0.6); finish(cv, T, 97, 0.55, 14)


def shot_alive(cv, T):
    k = seg(T, 19.7, 21.1); cam = Cam(A=(640, 620), sb=lerp(1.1, 1.0, k), sw=lerp(1.2, 1.1, k), sc=lerp(1.12, 1.02, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.7, lamps=0.8); items = []
    row = [(240, 690, .50, 1, 'm'), (400, 700, .54, 1, 'j'), (560, 690, .50, 1, 'u'), (720, 700, .52, -1, 'g'), (880, 690, .50, -1, 's'), (1040, 700, .54, -1, 'm'), (130, 640, .36, 1, 'm'), (1160, 640, .36, -1, 'v')]
    for i, (x, gy, sc, fl_, ch) in enumerate(row):
        w_ = math.sin(2 * math.pi * 2.2 * T + i * 0.9); on = ev(T, 19.9 + 0.04 * i, 20.5 + 0.04 * i)
        items.append(mk(ch, x, gy, sc, fl_, i * 1.3, pose={'aL': 8 + (110 + 18 * w_) * on, 'fL': 20 * w_ * on, 'aR': 8 + (20 + 90 * (i % 2)) * on, 'head': -6 * on + 2 * math.sin(T * 3 + i)}, gain=0.92, tint=BLUEW, crouch=0.04, hop=abs(w_) * 8 * on * (i % 2),
                        shirt=SHIRTS[(i * 3 + 1) % 10] if ch == 'm' else None, pants=PANTS[(i * 7 + 2) % 10] if ch == 'm' else None, mouth=speak(T, i, .8) * on))
    draw_items(cv, cam, items, T); cold(cv, T, 0.4 * (1 - ev(T, 20.5, 21.0))); finish(cv, T, 98, 0.5, 18)


# ---------------------------------------------------------------- 10. specialised teams on the surface (21.06 - 23.65)
def shot_teams(cv, T):
    k = seg(T, 21.0, 23.7); z = lerp(1.7, 1.9, k); cam = Cam(A=(300, 470), sb=z, sw=z, sc=z); focus(cam, 400, 420, 600, 470)
    plate(cv, 'h_p5', cam, 'b'); plate(cv, 'h_p5_gr', cam, 'w'); items = []
    crew = [(330, 480, .13, 1, 0), (330, 540, .14, 1, 1), (480, 570, .15, -1, 2), (560, 500, .14, -1, 3), (640, 590, .16, -1, 4), (700, 520, .14, -1, 5)]
    for (px, py, sc, fl_, i) in crew:
        x, gy = world_of(px, py); x0 = x + (1 - ev(T, 21.1 + 0.15 * i, 22.2 + 0.15 * i)) * 340; mv = 1.0 if 0.02 < ev(T, 21.1 + 0.15 * i, 22.2 + 0.15 * i) < 0.98 else 0.0
        pt_ = ev(T, 22.3 + 0.1 * i, 22.9 + 0.1 * i)
        items.append(mk('m', x0, gy, sc, fl_, i * 1.3, pose={'aL': 8 + 70 * pt_ * (i % 2), 'aR': 8 + 90 * pt_ * ((i + 1) % 2), 'fL': 0, 'fR': 20 * pt_, 'head': -6 * pt_ + 2 * math.sin(T + i)}, walk=mv, gain=1.0,
                        shirt=SHIRTS[3] if i in (1, 3, 5) else SHIRTS[(i * 3 + 2) % 10], pants=PANTS[(i * 5 + 1) % 10], crouch=0.0, sway=0.6))
    draw_items(cv, cam, items, T)
    puffs(cv, T, 21.0, 23.7, 10, (160, 430, 300, 80), (150, 185, 215), seed=122, size=(50, 120), rise=(10, 40), life=2.4, alpha=0.2, wind=(30, 0))
    cv[:] = heat_haze(cv, T, 1.0, 0.05, 2.5, 380, 560); motes(cv, T, 7, 22, 1.4); vignette(cv, 0.3, 2.0)


# ---------------------------------------------------------------- 11. NASA (23.65 - 27.7)
def shot_nasa(cv, T):
    k = ev(T, 23.5, 27.8); sS = lerp(1.0, 1.55, k) * S0; cx_ = lerp(760, 560, k); cy_ = lerp(330, 540, k)
    ox = cx_ * sS - W / 2; oy = min(max(cy_ * sS - H / 2, 0), 768 * sS - H); ox = min(max(ox, 0), 1376 * sS - W)
    place(cv, L('h6_space'), M3(-ox, -oy, sS, sS, 0, 0, 0), gain=0.98)
    st = (774 * sS - ox, 170 * sS - oy); tw = np.random.default_rng(5)
    for i in range(40):
        x = tw.random() * W; y = tw.random() * H * 0.5; a = 0.5 + 0.5 * math.sin(T * (1.5 + 2 * tw.random()) + i)
        cv2.circle(cv, (int(x - (ox - 300) * 0.05), int(y)), 1, (230.0 * a, 235.0 * a, 250.0 * a), -1, cv2.LINE_AA)
    # guidance signal from the station down to Chile
    tgt = (450 * sS - ox, 430 * sS - oy); sg = ev(T, 24.0, 24.8) * (1 - ev(T, 27.2, 27.7))
    if sg > 0:
        mid = ((st[0] + tgt[0]) / 2 + 80, (st[1] + tgt[1]) / 2 - 30); lb = LightBuf()
        for j in range(8):
            u = ((T - 24.0) * 0.6 + j / 8.0) % 1.0; x = (1 - u) ** 2 * st[0] + 2 * u * (1 - u) * mid[0] + u * u * tgt[0]; y = (1 - u) ** 2 * st[1] + 2 * u * (1 - u) * mid[1] + u * u * tgt[1]
            lb.glow(x, y, 26, (255, 235, 200), 1.0 * sg * math.sin(u * math.pi)); cv2.circle(cv, (int(x), int(y)), 7, (210.0, 240.0, 255.0), -1, cv2.LINE_AA)
        lb.glow(tgt[0], tgt[1], 30, (110, 200, 255), 0.7 * sg * (0.6 + 0.4 * math.sin(T * 7))); lb.glow(tgt[0], tgt[1], 130, (60, 140, 240), 0.25 * sg); lb.glow(st[0], st[1], 40, (255, 240, 220), 0.3 * sg); lb.apply(cv, blur=18)
    vignette(cv, 0.4, 2.0); finish(cv, T, 99, 0.4, 0)


# ---------------------------------------------------------------- 12. "the problem was the mind" (27.7 - 31.6)
def shot_mind6(cv, T):
    k = seg(T, 27.6, 31.7); cam = Cam(A=(640, 640), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.24, k), sc=lerp(1.0, 1.18, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.48, lamps=0.4 + 0.1 * flick(T, 11.0))
    items = sit_row((180, 300, 1000, 1130), 640, .34, T, head=14, crouch=0.55, gain=0.62) + sit_row((120, 1230), 600, .22, T, head=14, crouch=0.5, gain=0.58, ph=2.0)
    hd = ev(T, 28.0, 29.0)
    items.append(mk('g', 640, 712, .62, 1, 0.1, crouch=0.62 * hd, pose={'head': 30 * hd + 2 * math.sin(T * 6) * hd, 'aL': 4 + 114 * hd, 'fL': 140 * hd, 'aR': 4 + 114 * hd, 'fR': 140 * hd}, gain=.88, tint=CT))
    draw_items(cv, cam, items, T)
    puffs(cv, T, 29.0, 31.7, 14, (500, 360, 280, 120), (30, 30, 36), seed=93, size=(40, 90), rise=(20, 60), life=1.8, alpha=0.30)
    cv[:] = heat_haze(cv, T, 1.2, 0.05, 2.2, 150, 700); veil(cv, T, 0.1 + 0.1 * ev(T, 29, 31)); tone(cv, 1.0, 0, (0.93, 0.98, 1.06), 1.0); finish(cv, T, 100, 0.6, 24)


# ---------------------------------------------------------------- 13-15. three questions (31.6 - 38.9)
def shot_sleep(cv, T):
    k = seg(T, 31.5, 34.1); cam = Cam(A=(640, 640), sb=lerp(1.0, 1.08, k), sw=lerp(1.0, 1.22, k), sc=lerp(1.0, 1.14, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.62, lamps=1.25)
    def lying(i, d):
        e = ev(T, 31.8, 32.6 + 0.1 * i); d['rot'] = (84 if i % 2 else -84) * e + 3 * math.sin(T * 0.9 + i * 2) * e * (1 + (i % 3 == 0) * 2.0); d['dy'] = 455 * e; d['crouch'] = 0.0; d['pose']['head'] = 0.0
    items = sit_row((250, 400, 560, 380, 150), 560, .36, T, head=0, crouch=0.0, gain=0.82, ph=0.3, extra=lying) + sit_row((820, 950, 1090, 900), 590, .38, T, head=0, crouch=0.0, gain=0.84, ph=1.3, extra=lying)
    draw_items(cv, cam, items, T)
    lb = LightBuf()
    for q in ((200, 300), (560, 330), (1080, 350)):
        p = cam.pt(*q); lb.glow(p[0], p[1], 200, (100, 180, 255), 0.35)
    lb.apply(cv, blur=36); finish(cv, T, 101, 0.5, 20)


def shot_wake(cv, T):
    k = seg(T, 33.9, 36.0); cam = Cam(A=(640, 640), sb=lerp(1.04, 1.12, k), sw=lerp(1.1, 1.26, k), sc=lerp(1.0, 1.18, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.40, lamps=0.4)
    up = ev(T, 34.5, 35.5)
    def lying(i, d): d['rot'] = (84 if i % 2 else -84); d['dy'] = 455; d['crouch'] = 0.0; d['pose']['head'] = 0.0
    items = sit_row((200, 360, 920, 1080), 585, .38, T, head=0, crouch=0.0, gain=0.6, ph=0.3, extra=lying)
    items.append(mk('u', 640, 716, .60, 1, 0.4, crouch=0.0, rot=-84 * (1 - up), dy=455 * (1 - up), pose={'head': -6 * up + 8 * (1 - up), 'aL': 8 + 110 * ev(T, 35.1, 35.5) * (1 - ev(T, 35.6, 35.95)), 'fL': 140 * ev(T, 35.1, 35.5), 'aR': 8}, gain=.95, tint=CT))
    draw_items(cv, cam, items, T)
    veil(cv, T, 0.1); finish(cv, T, 102, 0.6, 20)


def shot_dark(cv, T):
    k = seg(T, 35.9, 39.0); cam = Cam(A=(640, 560), sb=lerp(1.05, 1.15, k), sw=lerp(1.1, 1.25, k), sc=lerp(1.0, 1.12, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.34, lamps=0.35)
    sh = 0.6 * ev(T, 36.8, 37.6)
    items = sit_row((180, 300, 1000, 1130), 650, .34, T, head=18, crouch=0.6, gain=0.5, ph=0.9)
    items.append(mk('v', 640, 716, .52, 1, 0.4, crouch=0.2, pose={'head': 10 * ev(T, 36.2, 36.8) + 4 * math.sin(T * 7) * sh, 'aL': 4 + 110 * ev(T, 36.3, 37.0), 'fL': 130 * ev(T, 36.3, 37.0), 'aR': 8}, gain=.9, tint=CT))
    draw_items(cv, cam, items, T)
    hp = cam.pt(640, 716 - 880 * .52)
    e = ev(T, 36.5, 37.4)
    puffs(cv, T, 36.4, 39.0, 24, (hp[0] - 220, hp[1] - 160, 440, 260), (70, 62, 80), seed=94, size=(50, 130), rise=(10, 60), life=2.0, alpha=0.5 * e + 0.0)
    veil(cv, T, 0.15 * e); finish(cv, T, 103, 0.7, 20)


# ---------------------------------------------------------------- 16. a whole mountain above (38.9 - 42.2)
def shot_mount(cv, T):
    P4.rise(cv, T, 38.9, 42.1, glow=0.0)
    items = []
    e = ev(T, 39.3, 41.3)
    for i, x in enumerate((300, 430, 560, 720, 860, 990)):
        items.append(mk('m', x, 700 + 1000 * ev(T, 38.9, 42.2) + (i % 2) * 14, .22, 1 if i % 2 else -1, i * 1.3, pose={'head': 14, 'aL': 4, 'aR': 4}, crouch=0.5, gain=0.65, tint=CT, shirt=SHIRTS[(i * 3 + 1) % 10], pants=PANTS[(i * 7 + 2) % 10]))
    draw_items(cv, Cam(), items, T)
    dxy = shake_xy(T, 0.5 * P(T, 40.0, 42.0)); cv[:] = np.roll(cv, 0, axis=0)
    puffs(cv, T, 38.9, 42.2, 12, (100, 0, 1080, 100), (110, 150, 190), seed=95, size=(40, 90), rise=(60, 120), life=2.0, alpha=0.18)
    finish(cv, T, 104, 0.4, 0)


# ---------------------------------------------------------------- 17-21. the routine (42.2 - 46.4)
def chamber_men(T, spec, gain=0.88):
    return spec


def shot_exercise(cv, T):
    k = seg(T, 42.1, 43.3); cam = Cam(A=(640, 620), sb=lerp(1.0, 1.06, k), sw=lerp(1.0, 1.14, k), sc=lerp(1.0, 1.1, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.68, lamps=1.0); items = []
    row = [(240, 696, .48, 1, 'm'), (420, 704, .52, 1, 'j'), (600, 696, .48, 1, 'm'), (800, 704, .5, -1, 'g'), (980, 696, .48, -1, 'm'), (1140, 704, .5, -1, 'v')]
    for i, (x, gy, sc, fl_, ch) in enumerate(row):
        s = 0.5 + 0.5 * math.sin(2 * math.pi * 2.3 * T + 0.2 * (i % 2)); up = s
        items.append(mk(ch, x, gy, sc, fl_, i * 1.3, pose={'aL': 14 + 125 * up, 'aR': 14 + 125 * up, 'fL': 0, 'fR': 0, 'head': 0}, hop=26 * up, gain=0.9, tint=CT, crouch=0.15 * (1 - up), shirt=SHIRTS[(i * 3 + 1) % 10] if ch == 'm' else None, pants=PANTS[(i * 7 + 2) % 10] if ch == 'm' else None))
    draw_items(cv, cam, items, T); puffs(cv, T, 42.1, 43.3, 8, (200, 600, 880, 60), (95, 135, 178), seed=96, size=(30, 70), rise=(10, 40), life=1.2, alpha=0.18); finish(cv, T, 105, 0.45, 14)


def shot_pray(cv, T):
    k = seg(T, 43.1, 44.2); cam = Cam(A=(640, 640), sb=lerp(1.0, 1.05, k), sw=lerp(1.05, 1.14, k), sc=lerp(1.0, 1.1, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.56, lamps=0.7); items = []
    bow = 0.5 + 0.5 * math.sin(T * 2.2)
    for r, (gy, sc, xs) in enumerate(((620, .34, (200, 400, 600, 800, 1000, 1180)), (712, .46, (300, 500, 700, 900, 1090)))):
        for i, x in enumerate(xs):
            d = ev(T, 43.2, 43.6 + 0.05 * i)
            items.append(mk('m' if (i + r) % 4 else 'u', x, gy, sc, -1 if x > 640 else 1, i * 1.3 + r, crouch=0.9 * d, pose={'head': (28 + 10 * bow) * d, 'aL': 4 + 20 * d, 'aR': 4 + 20 * d, 'fL': -75 * d, 'fR': -75 * d}, gain=0.86, tint=CT, shirt=SHIRTS[(i * 3 + r) % 10], pants=PANTS[(i * 7 + r) % 10]))
    draw_items(cv, cam, items, T); finish(cv, T, 106, 0.55, 14)


def shot_games(cv, T):
    k = seg(T, 44.0, 44.9); cam = table_cam(k, 1.05, 1.15, (700, 440))
    table_bg(cv, T, cam, 0.95, hands=((0.1 + T * 0.01) % 1.0, (T * 0.05) % 1.0))
    items = [mk('u', 470, 522, .38, 1, 0.2, pose={'head': 6 * math.sin(T * 3), 'aR': 40 + 30 * P(T, 44.3, 44.6), 'fR': -20, 'aL': 12}, gain=.85, tint=CT), mk('m', 900, 520, .34, -1, 1.4, pose={'head': -6 + 3 * math.sin(T * 2), 'aL': 40 + 40 * P(T, 44.1, 44.5), 'fL': -20}, shirt=SHIRTS[4], pants=PANTS[2], gain=.85, tint=CT),
             mk('g', 640, 520, .30, 1, 2.1, pose={'head': 8, 'aR': 20}, gain=.8, tint=CT)]
    draw_items(cv, cam, items, T); table_fg(cv, cam, 0.95)
    for j in range(7):
        e = ev(T, 44.1 + 0.05 * j, 44.4 + 0.05 * j); x = 560 + 40 * j + (1 - e) * (-120 if j % 2 else 120); y = 500 + 6 * (j % 3) - 60 * (1 - e) * (1 - e)
        px, py = cam.pt(x, y); rrect(cv, px, py, 20 * cam.sc, 36 * cam.sc, 8 * (j % 3 - 1), (232.0, 236.0, 240.0)); cv2.line(cv, (int(px - 8 * cam.sc), int(py)), (int(px + 8 * cam.sc), int(py)), (30.0, 30.0, 40.0), 1)
        for dd in (-6, 6): cv2.circle(cv, (int(px), int(py + dd * cam.sc * 1.1 * (1 if j % 2 else 1))), max(1, int(2 * cam.sc)), (20.0, 20.0, 30.0), -1, cv2.LINE_AA)
    finish(cv, T, 107, 0.5, 14)


def shot_write6(cv, T): P5.shot_write(cv, 24.2 + 1.4 * (T - 44.8))


def shot_phone(cv, T):
    k = seg(T, 45.5, 46.5); cam = storage_cam(k, 1.0) if False else Cam(A=(640, 560), sb=lerp(1.0, 1.08, k), sw=lerp(1.05, 1.15, k), sc=lerp(1.0, 1.08, k), d=(0, 0), dw=(0, 0))
    plate(cv, 'h3_storage', cam, 'b'); cv *= 0.8
    lb = LightBuf(); q = bpt(cam, 1000, 100); lb.glow(q[0], q[1], 50 * cam.sb, (110, 190, 255), 0.5); lb.glow(q[0], q[1], 300 * cam.sb, (60, 130, 230), 0.25); lb.apply(cv, blur=28)
    on = ev(T, 45.6, 46.0)
    hx = 520; hand = cam.pt(hx + 70, 400)
    items = [mk('u', hx, 716, .5, 1, 0.4, pose={'head': -6 + 2 * math.sin(T * 3) * on, 'aL': 8, 'aR': 8 + 114 * on, 'fR': 140 * on}, mouth=speak(T, 1.0, 1.0) * on, gain=1.0, tint=HOT),
             mk('m', 860, 716, .5, -1, 0.9, pose={'head': 6 * on, 'aL': 8, 'aR': 8}, gain=.95, tint=HOT, shirt=SHIRTS[4], pants=PANTS[2], mouth=0.0)]
    draw_items(cv, cam, items, T)
    # the telephone cord rises through the ceiling
    top = cam.pt(hx + 60, -30); mid = cam.pt(hx + 130 + 12 * math.sin(T * 2), 150); lo = cam.pt(hx + 38, 300 + 10 * (1 - on))
    cable(cv, [top, mid, lo], w=max(2, int(3 * cam.sc)), col=(30.0, 36.0, 44.0)); finish(cv, T, 108, 0.5, 14)


# ---------------------------------------------------------------- 22. make the day look normal (46.4 - 51.5)
def shot_normal(cv, T):
    k = seg(T, 46.3, 51.6); cam = Cam(A=(640, 620), sb=lerp(1.12, 1.0, k), sw=lerp(1.28, 1.02, k), sc=lerp(1.28, 0.98, k), d=(0, 0), dw=(0, 0))
    dk = ev(T, 49.3, 51.2); chamber_bg(cv, T, cam, 0.78 - 0.34 * dk, lamps=1.0 - 0.55 * dk + 0.0 * flick(T, 3.0)); items = []
    for i, c in enumerate(GRID):
        if i % 4 == 0: pose = {'aL': 8 + 40 * P(T, 46.8 + 0.1 * i, 47.8 + 0.1 * i), 'head': 4 * math.sin(T * 2 + i), 'aR': 4}
        elif i % 4 == 1: pose = {'aL': 20 + 25 * math.sin(T * 4 + i), 'aR': 20 + 25 * math.sin(T * 4 + i + 2), 'head': 2 * math.sin(T * 3 + i)}
        else: pose = {'head': 3 * math.sin(T * 1.3 + i), 'aL': 4, 'aR': 4}
        items.append(dict(c, pose=pose, crouch=0.15 + 0.2 * dk, gain=0.86 - 0.2 * dk, tint=CT, sway=0.4, mouth=speak(T, i, .4) * (i % 4 == 0) * (1 - dk)))
    draw_items(cv, cam, items, T)
    puffs(cv, T, 46.4, 51.5, 12, (200, 0, 880, 60), (95, 135, 178), seed=97, size=(30, 80), rise=(20, 60), life=1.6, alpha=0.15)
    tone(cv, 1.0, 0, (0.95, 0.99, 1.04), 1.0); veil(cv, T, 0.04 + 0.1 * dk); finish(cv, T, 109, 0.45 + 0.3 * dk, 20)


# ---------------------------------------------------------------- 23. the rescue plan on paper: three drill lines (51.5 - 55.2)
PLANS = [([(0.22, 0.12), (0.34, 0.42), (0.46, 0.78)], (40.0, 40.0, 195.0), 53.9), ([(0.50, 0.12), (0.50, 0.45), (0.50, 0.80)], (190.0, 120.0, 40.0), 54.4), ([(0.78, 0.12), (0.66, 0.44), (0.54, 0.80)], (70.0, 150.0, 55.0), 54.9)]
GROUND = [(0.06, 0.12), (0.2, 0.10), (0.4, 0.13), (0.6, 0.10), (0.8, 0.13), (0.94, 0.11)]
BLOB = [(0.40 + 0.09 * math.cos(a / 8.0 * 2 * math.pi), 0.0) for a in range(0)]


def shot_plan(cv, T):
    k = seg(T, 51.4, 55.3); z = lerp(2.0, 2.3, k); cam = Cam(A=(680, 520), sb=z, sw=z, sc=z); cam.d = paper_center(z); cam.dw = cam.d
    paper_bg(cv, T, cam); tip = None; ink = (26.0, 34.0, 52.0)
    for pts, pr in ((GROUND, seg(T, 51.7, 52.7)), (SCRIB6, seg(T, 52.8, 53.6))):
        if pr > 0:
            t_ = stroke(cv, cam, pts, pr, w=2.2, col=ink)
            if pr < 1.0: tip = t_
    e = ev(T, 53.0, 53.6)
    if e > 0:   # the chamber, a small ellipse underground
        c = bpt(cam, *paper_pt(0.5, 0.82)); cv2.ellipse(cv, (int(c[0]), int(c[1])), (int(26 * cam.sb * 0.5 * e), int(13 * cam.sb * 0.5 * e)), 0, 0, 360, (30.0, 40.0, 190.0), -1, cv2.LINE_AA)
    for pts, col, t0 in PLANS:
        pr = seg(T, t0, t0 + 0.4)
        if pr > 0:
            t_ = stroke(cv, cam, pts, pr, w=3.4, col=col)
            if pr < 1.0: tip = t_
            else:
                q = bpt(cam, *paper_pt(*pts[0])); cv2.circle(cv, (int(q[0]), int(q[1])), int(7 * cam.sb * 0.5), col, -1, cv2.LINE_AA)
    if tip is None and T < 55.0: tip = bpt(cam, *paper_pt(0.5, 0.8))
    if T < 55.1: pencil(cv, tip, -32, 150, cam.sb / 2.0)
    veil(cv, T, 0.04); finish(cv, T, 110, 0.5, 14)


SCRIB6 = [(0.06 + 0.88 * t / 10.0, 0.80 + 0.02 * math.sin(t * 2.3)) for t in range(11)]


# ---------------------------------------------------------------- 24. giant drilling machines (55.2 - 57.6)
def shot_rigs(cv, T):
    k = seg(T, 55.1, 57.7); z = lerp(1.0, 1.28, ev(T, 55.1, 57.7)); cx_ = lerp(688, 760, k)
    sS = z * S0; ox = min(max(cx_ * sS - W / 2, 0), 1376 * sS - W); oy = min(max(500 * sS - H / 2, 0), 768 * sS - H)
    sh = shake_xy(T, 1.0 * ev(T, 55.5, 56.5)); ox -= sh[0]; oy -= sh[1]
    place(cv, L('h6_rigs'), M3(-ox, -oy, sS, sS, 0, 0, 0), gain=0.98)
    lb = LightBuf(); fl = 0.85 + 0.15 * flick(T, 4.0)
    for (px, py) in ((925, 150), (1005, 160), (1100, 225), (1055, 260), (810, 590)):
        lb.glow(px * sS - ox, py * sS - oy, 30 * z, (110, 190, 255), 0.45 * fl)
    lb.apply(cv, blur=22)
    puffs(cv, T, 55.2, 57.7, 28, (200, 360, 900, 200), (110, 150, 190), seed=98, size=(50, 130), rise=(-10, 40), life=2.0, alpha=0.28, wind=(15, 0))
    vignette(cv, 0.3, 2.0); finish(cv, T, 111, 0.4, 20)


# ---------------------------------------------------------------- 25. thousands of people waiting above (57.6 - 59.0)
def shot_wait(cv, T):
    k = seg(T, 57.5, 59.1); cam = Cam(A=(640, 620), sb=lerp(1.2, 1.0, k), sw=lerp(1.25, 1.05, k), sc=lerp(1.25, 1.02, k), d=(0, 0), dw=(0, 0))
    plate(cv, 'h4_night', cam, 'b'); plate(cv, 'h4_night_gr', cam, 'w'); items = []
    for r, (gy, sc, n) in enumerate(((600, .16, 17), (640, .21, 14), (690, .27, 11))):
        for i in range(n):
            x = 40 + (1200.0 / max(1, n - 1)) * i + 20 * ((i * 7 + r) % 3 - 1); ch = ('w', 'ar', 'm')[(i + r) % 3]; pr = 0.6 + 0.4 * math.sin(T * 1.2 + i)
            items.append(mk(ch, x, gy + (i % 2) * 6, sc, 1 if i % 2 else -1, i * 1.1 + r, pose={'head': 6 + 3 * math.sin(T * 0.9 + i), 'aL': 4, 'aR': 4 + 90 * (i % 5 == 0) * ev(T, 57.8, 58.3), 'fR': 100 * (i % 5 == 0)}, gain=0.9, tint=(0.95, 0.98, 1.04), crouch=0.0, sway=0.5))
    draw_items(cv, cam, items, T)
    lb = LightBuf(); fl = 0.9 + 0.1 * flick(T, 8.0)
    for (px, py, r_) in ((800, 530, 40), (1020, 548, 28), (560, 540, 26)):
        q = cam.pt(S0 * px - OX, S0 * py - OY); lb.glow(q[0], q[1], r_ * cam.sb, (110, 190, 255), 0.55 * fl); lb.glow(q[0], q[1], 7 * r_ * cam.sb, (50, 120, 230), 0.25 * fl)
    lb.apply(cv, blur=26); motes(cv, T, 58, 30, 0.6, (230, 225, 200)); vignette(cv, 0.4, 2.0)


# ---------------------------------------------------------------- 26. time: the clock spins (59.0 - 60.2)
def shot_time6(cv, T):
    k = seg(T, 58.9, 60.3); z = lerp(2.2, 2.6, k); cam = Cam(A=(640, 360), sb=z, sw=z, sc=z); focus(cam, CLOCK[0], CLOCK[1], 640, 360)
    sp = 0.2 + 3.0 * (T - 59.0); table_bg(cv, T, cam, 0.92, hands=(sp % 1.0, (sp * 8) % 1.0), glow=0.6)
    puffs(cv, T, 59.0, 60.3, 10, (300, 0, 700, 200), (110, 150, 190), seed=99, size=(30, 70), rise=(10, 40), life=1.4, alpha=0.12); finish(cv, T, 112, 0.5, 14)


# ---------------------------------------------------------------- 27. every extra day is more danger (60.2 - end)
CRACK = []
_rc = np.random.default_rng(66)
for _i in range(7):
    _x, _y = 200 + 880 * _rc.random(), 0.0; _p = [(_x, _y)]
    for _s in range(8): _x += _rc.normal(0, 36); _y += 50 + 40 * _rc.random(); _p.append((_x, _y))
    CRACK.append(_p)


def shot_danger(cv, T):
    k = seg(T, 60.1, D6); z = lerp(1.0, 1.1, k); sh = 0.3 + 1.5 * ev(T, 60.8, D6)
    cam = Cam(A=(640, 380), sb=z, sw=z, sc=z, d=shake_xy(T, sh), dw=shake_xy(T, sh))
    plate(cv, 'h5_wall', cam, 'b', gain=0.8 - 0.25 * ev(T, 60.8, D6))
    for i in range(17 + 8):
        e = ev(T, 60.2 + (0.08 * (i - 17) if i >= 17 else -1), 60.2 + (0.08 * (i - 17) + 0.16 if i >= 17 else -0.5))
        if e <= 0: continue
        (xa, ya), (xb, yb) = tally_pts(i); pa = bpt(cam, xa, ya); pb = bpt(cam, xa + (xb - xa) * e, ya + (yb - ya) * e); w_ = max(2, int(6 * cam.sb))
        cv2.line(cv, (int(pa[0] + 2), int(pa[1] + 3)), (int(pb[0] + 2), int(pb[1] + 3)), (10.0, 14.0, 22.0), w_ + 2, cv2.LINE_AA)
        cv2.line(cv, (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1])), (215.0, 232.0, 240.0) if i < 17 else (200.0, 215.0, 250.0), w_, cv2.LINE_AA)
    # cracks growing across the rock
    for j, p in enumerate(CRACK):
        g = ev(T, 60.9 + 0.12 * j, 61.9 + 0.12 * j)
        if g <= 0: continue
        n = max(2, int(1 + g * (len(p) - 1))); pts = np.array([bpt(cam, x, y) for (x, y) in p[:n]], np.int32); cv2.polylines(cv, [pts], False, (6.0, 8.0, 12.0), max(2, int(3 * cam.sb)), cv2.LINE_AA)
    chunk_fall(cv, T, 60.8, 62.3, 24, 67, 200, 1080, 700, cam.sc)
    puffs(cv, T, 60.4, D6, 26, (100, 0, 1080, 300), (110, 150, 190), seed=100, size=(50, 130), rise=(-20, 30), life=2.0, alpha=0.30, wind=(8, 0))
    lb = LightBuf(); q = bpt(cam, 160, 130); lb.glow(q[0], q[1], 260, (60, 130, 230), 0.18 * (0.8 + 0.2 * flick(T, 3.0))); lb.apply(cv, blur=30)
    vignette(cv, 0.4 + 0.3 * k, 2.0); finish(cv, T, 113, 0.6, 22)


SHOTS6 = [('know', 0.0, 1.9, shot_know, 0.0), ('tube', 1.9, 5.0, shot_tube, 0.3), ('supply', 5.0, 9.9, shot_supply, 0.4), ('lifeline', 9.9, 13.1, shot_lifeline, 0.4), ('see', 13.1, 16.05, shot_see, 0.3),
          ('thin', 16.05, 17.5, shot_thin, 0.2), ('tired', 17.5, 18.7, shot_tired, 0.2), ('beards', 18.7, 19.8, shot_beards, 0.2), ('alive', 19.8, 21.06, shot_alive, 0.3), ('teams', 21.06, 23.65, shot_teams, 0.4),
          ('nasa', 23.65, 27.7, shot_nasa, 0.5), ('mind', 27.7, 31.6, shot_mind6, 0.5), ('sleep', 31.6, 34.0, shot_sleep, 0.4), ('wake', 34.0, 35.97, shot_wake, 0.4), ('dark', 35.97, 38.9, shot_dark, 0.4),
          ('mount', 38.9, 42.2, shot_mount, 0.4), ('exercise', 42.2, 43.2, shot_exercise, 0.2), ('pray', 43.2, 44.1, shot_pray, 0.2), ('games', 44.1, 44.8, shot_games, 0.2), ('write', 44.8, 45.6, shot_write6, 0.2),
          ('phone', 45.6, 46.4, shot_phone, 0.2), ('normal', 46.4, 51.5, shot_normal, 0.4), ('plan', 51.5, 55.2, shot_plan, 0.4), ('rigs', 55.2, 57.6, shot_rigs, 0.4), ('wait', 57.6, 59.0, shot_wait, 0.3),
          ('time', 59.0, 60.2, shot_time6, 0.2), ('danger', 60.2, D6, shot_danger, 0.3)]


class Part6:
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTS6):
            hi = t1 + (SHOTS6[i + 1][4] / 2 if i + 1 < len(SHOTS6) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTS6) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
