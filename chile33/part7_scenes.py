"""Part 7 (Arabic, 111.1 s): the drilling, the breakthrough, the narrow hole, the Phoenix capsule, the rescue, one by one, Urzua last, 33 alive after 69 days.
Same STYLE LOCK as parts 1-6. No captions, no music (SFX only)."""
from part6_scenes import *
import part6_scenes as P6

D7 = 111.1
HOLE = (688, 516)          # the borehole at the rescue site (plate px of h7_site)
WIN = (120, 190, 50, 60)   # capsule window (layer px): cx, cy, rx, ry
DOOR = (60, 130, 180, 540) # door rect in layer px: x0, y0, x1, y1
CAPH = 600


# ---------------------------------------------------------------- the Phoenix capsule (hi-res layer 240x600)
_c7 = {}


def cap7():
    if 'l' not in _c7:
        w, h = 240, CAPH; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); u = xx / (w - 1)
        sh = 0.42 + 0.80 * np.exp(-((u - 0.33) / 0.2) ** 2) + 0.20 * np.exp(-((u - 0.84) / 0.07) ** 2) - 0.28 * u
        rr = cv2.GaussianBlur(np.random.default_rng(4).normal(0, 1, (h, w)).astype(np.float32), (0, 0), 1.6)
        img = np.zeros((h, w, 3), np.float32); img[:] = np.array((168, 180, 190), np.float32); img *= (sh + 0.07 * rr)[..., None]
        for (y0, y1, col) in ((300, 322, (45, 52, 205)), (322, 344, (228, 232, 234)), (344, 366, (170, 85, 40))):
            img[y0:y1] = np.array(col, np.float32) * (sh[y0:y1, :, None] * 0.95 + 0.06 * rr[y0:y1, :, None])
        for ry_ in range(104, 560, 34): cv2.line(img, (20, ry_), (220, ry_), (110, 120, 130), 1, cv2.LINE_AA)   # panel seams
        x0, y0, x1, y1 = DOOR; cv2.rectangle(img, (x0, y0), (x1, y1), (36, 40, 46), 3, cv2.LINE_AA); cv2.rectangle(img, (x1 - 24, 330), (x1 - 12, 372), (60, 66, 74), -1, cv2.LINE_AA)
        cx, cy, rx, ry = WIN; cv2.ellipse(img, (cx, cy), (rx + 7, ry + 7), 0, 0, 360, (92, 102, 112), -1, cv2.LINE_AA); cv2.ellipse(img, (cx, cy), (rx, ry), 0, 0, 360, (26, 22, 20), -1, cv2.LINE_AA)
        cv2.ellipse(img, (cx - 14, cy - 18), (10, 28), 25, 0, 360, (90, 96, 100), -1, cv2.LINE_AA)
        for i in range(10): cv2.circle(img, (30 + 20 * i, 98), 2, (70, 78, 86), -1, cv2.LINE_AA); cv2.circle(img, (30 + 20 * i, 566), 2, (70, 78, 86), -1, cv2.LINE_AA)
        m = np.zeros((h, w), np.float32); cv2.rectangle(m, (14, 90), (226, 520), 1.0, -1); cv2.ellipse(m, (120, 90), (106, 88), 0, 180, 360, 1.0, -1, cv2.LINE_AA); cv2.ellipse(m, (120, 520), (106, 74), 0, 0, 180, 1.0, -1, cv2.LINE_AA)
        m = cv2.GaussianBlur(m, (0, 0), 1.2); edge = cv2.GaussianBlur(m, (0, 0), 4) < 0.92; img[edge] *= 0.5
        img = np.clip(img, 0, 255); _c7['l'] = Layer.from_array(np.dstack([img * m[..., None], m]))
    return _c7['l']


def cap_draw(cv, x, ytop, s, rot=0.0, gain=1.0, tint=None):
    place(cv, cap7(), M3(x, ytop, s, s, rot, 120, 0), gain=gain, tint=tint)


def lpt(x, ytop, s, lx, ly): return (x + (lx - 120) * s, ytop + ly * s)


def interior_mask(x, ytop, s, e, win=True):
    m = np.zeros((H, W), np.float32)
    if e > 0.02:
        x0, y0, x1, y1 = DOOR; xa = x1 - e * (x1 - x0 - 6); a = lpt(x, ytop, s, xa, y0 + 4); b = lpt(x, ytop, s, x1 - 3, y1 - 3); cv2.rectangle(m, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 1.0, -1)
    if win and e < 0.98:
        cx, cy, rx, ry = WIN; c = lpt(x, ytop, s, cx, cy); cv2.ellipse(m, (int(c[0]), int(c[1])), (int(rx * s), int(ry * s)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    return cv2.GaussianBlur(m, (0, 0), 1.0)[..., None]


def cap_with_man(cv, x, ytop, s, T, e_door, man, glow=0.0, straps=0.0):
    """capsule + a man inside (visible through the open door, or the window when closed); man: dict for mk() without position"""
    cap_draw(cv, x, ytop, s, gain=1.0, tint=(0.97, 1.0, 1.04))
    if man is not None:
        x0, y0, x1, y1 = DOOR; gb = lpt(x, ytop, s, 120, y1 - 6)[1]; buf = np.zeros_like(cv); buf[:] = (22.0, 17.0, 14.0)
        # soft interior light from the lamp inside
        lb = LightBuf(); lb.glow(x, gb - 380 * s, 220 * s, (110, 190, 255), 0.55 + 0.3 * glow); lb.apply(buf, blur=24)
        it = dict(man); it.update(x=x, gy=gb, sc=0.375 * s, flip=man.get('flip', 1)); draw_items(buf, Cam(), [it], T)
        if straps > 0:
            for sx_ in (-1, 1):
                a = (x - sx_ * 70 * s * 0.5, gb - 700 * s * 0.5 * 1.0 + 0); b = (x + sx_ * 70 * s * 0.5, gb - 470 * s * 0.5 + 0)
                cv2.line(buf, (int(x - sx_ * 60 * s), int(gb - 330 * s * 1.0)), (int(x + sx_ * 60 * s), int(gb - 250 * s)), (14.0, 16.0, 20.0), max(2, int(9 * s)), cv2.LINE_AA)
        m = interior_mask(x, ytop, s, e_door); cv[:] = cv * (1 - m) + buf * m
        if e_door < 0.98:   # glass reflection over the window
            c = lpt(x, ytop, s, WIN[0] - 18, WIN[1] - 20); gl = np.zeros((H, W), np.float32); cv2.ellipse(gl, (int(c[0]), int(c[1])), (max(2, int(7 * s)), max(3, int(30 * s))), 25, 0, 360, 1.0, -1, cv2.LINE_AA)
            cv += cv2.GaussianBlur(gl, (0, 0), 2.5)[..., None] * 38 * (1 - e_door)


def phoenix(cv, cx, cy, sz, glow=1.0, T=0.0):
    """a stylised fire bird (procedural), wings flapping slowly"""
    fl = 0.9 + 0.1 * math.sin(T * 9)
    for k, (col, sc_) in enumerate((((30, 90, 230), 1.0), ((40, 160, 250), 0.78), ((120, 225, 255), 0.5))):
        s = sz * sc_; wing = 0.12 * math.sin(T * 3.0)
        pts = []
        for sgn in (-1, 1):
            p = [(0, -0.1), (sgn * 0.35, -0.35 - wing), (sgn * 0.8, -0.55 - 1.4 * wing), (sgn * 1.0, -0.2 - wing), (sgn * 0.7, -0.15), (sgn * 0.5, 0.05), (sgn * 0.25, 0.1)]
            pts.append(p)
        poly = [(cx + x * s, cy + y * s) for x, y in pts[0]] + [(cx + x * s, cy + y * s) for x, y in reversed(pts[1])]
        cv2.fillPoly(cv, [np.array(poly, np.int32)], tuple(float(c * glow * fl) for c in col), cv2.LINE_AA)
        body = [(cx, cy - 0.5 * s), (cx + 0.14 * s, cy - 0.2 * s), (cx + 0.08 * s, cy + 0.5 * s), (cx, cy + 1.1 * s), (cx - 0.08 * s, cy + 0.5 * s), (cx - 0.14 * s, cy - 0.2 * s)]
        cv2.fillPoly(cv, [np.array(body, np.int32)], tuple(float(c * glow * fl) for c in col), cv2.LINE_AA)
        for j in (-1, 0, 1):
            tail = [(cx + j * 0.1 * s, cy + 0.5 * s), (cx + j * 0.35 * s, cy + 1.3 * s * (1 + 0.1 * math.sin(T * 7 + j))), (cx + j * 0.05 * s, cy + 0.45 * s + 0.2 * s)]
            cv2.fillPoly(cv, [np.array(tail, np.int32)], tuple(float(c * glow * fl) for c in col), cv2.LINE_AA)


def glasses(cv, heads, T):
    for it, HM in heads:
        if not it.get('glasses'): continue
        p = head_pt(it, HM); s = it['sc'] * it.get('_zc', 1.0)
        if s <= 0: continue
        for sx_ in (-1, 1):
            c = (int(p[0] + sx_ * 33 * s), int(p[1] - 4 * s)); cv2.ellipse(cv, c, (max(2, int(27 * s)), max(2, int(19 * s))), 0, 0, 360, (10.0, 10.0, 14.0), -1, cv2.LINE_AA)
            cv2.ellipse(cv, c, (max(2, int(27 * s)), max(2, int(19 * s))), 0, 0, 360, (120.0, 130.0, 140.0), max(1, int(2 * s)), cv2.LINE_AA)
            cv2.line(cv, (c[0] - int(12 * s), c[1] - int(8 * s)), (c[0] - int(2 * s), c[1] - int(12 * s)), (235.0, 240.0, 250.0), max(1, int(3 * s)), cv2.LINE_AA)
        cv2.line(cv, (int(p[0] - 8 * s), int(p[1] - 6 * s)), (int(p[0] + 8 * s), int(p[1] - 6 * s)), (10.0, 10.0, 14.0), max(1, int(3 * s)), cv2.LINE_AA)


def draw_g(cv, cam, items, T):
    for it in items: it['_zc'] = cam.sc
    hs = draw_items(cv, cam, items, T); glasses(cv, hs, T); return hs


# ---------------------------------------------------------------- the rescue site (night plate)
def site_cam(z=1.0, fx=688, fy=470, sx=640, sy=420, shk=0.0, T=0.0):
    cam = Cam(A=(640, 420), sb=z, sw=z, sc=z); focus(cam, fx, fy, sx, sy)
    if shk > 0: dxy = shake_xy(T, shk); cam.d = (cam.d[0] + dxy[0], cam.d[1] + dxy[1]); cam.dw = cam.d
    return cam


def site_bg(cv, T, cam, dark=1.0, flash=0.0):
    plate(cv, 'h7_site', cam, 'b', gain=dark)
    lb = LightBuf(); fl = 0.9 + 0.1 * flick(T, 3.0)
    for (px, py, r_, a) in ((688, 270, 70, 0.55), (565, 322, 30, 0.35), (810, 310, 30, 0.35), (655, 215, 40, 0.3)):
        q = bpt(cam, px, py); lb.glow(q[0], q[1], r_ * cam.sb, (110, 190, 255), a * fl); lb.glow(q[0], q[1], 4 * r_ * cam.sb, (60, 130, 230), 0.18 * fl)
    lb.apply(cv, blur=26)


def site_sc(py): return 0.055 + 0.00068 * (py - 480)


def site_person(ch, px, py, flip=1, k=1.0, **kw):
    x, gy = world_of(px, py); return mk(ch, x, gy, site_sc(py) * k, flip, px * 0.013, **kw)


def site_crowd(T, cheer=0.0, wave=0.0, n=16, seed=3, zone=((420, 960), (520, 600)), tint=(0.95, 0.98, 1.04), hop=1.0):
    r = np.random.default_rng(seed); items = []
    for i in range(n):
        px = zone[0][0] + (zone[0][1] - zone[0][0]) * r.random(); py = zone[1][0] + (zone[1][1] - zone[1][0]) * r.random(); ch = ('w', 'ar', 'm')[i % 3]
        w_ = math.sin(2 * math.pi * 2.4 * T + i * 1.3)
        pose = {'aL': 4 + 134 * cheer * (0.6 + 0.4 * w_), 'aR': 4 + 134 * cheer * (0.6 - 0.4 * w_) + 100 * wave * (i % 2), 'head': -6 * cheer + 3 * math.sin(T * 2 + i)}
        items.append(site_person(ch, px, py, 1 if r.random() > .5 else -1, 1.0, pose=pose, hop=abs(w_) * 20 * cheer * hop * site_sc(py) * 12, gain=0.92, tint=tint, mouth=speak(T, i, 1.0) * cheer))
    return items


def surface_shot(cv, T, P):
    """capsule standing over the borehole, door, men stepping out.  P: dict(z, fx, fy, rise=(a,b)|None, door=t, outs=[(t, ch, shirt, pants, glasses)], cheer=(a,b), hug=bool, flash=bool, shk)"""
    z = P.get('z', 2.0); z = z(T) if callable(z) else z; shk = P.get('shk', 0.0); shk = shk(T) if callable(shk) else shk
    cam = site_cam(z, P.get('fx', 688), P.get('fy', 470), P.get('sx', 640), P.get('sy', 430), shk=shk, T=T)
    site_bg(cv, T, cam, P.get('dark', 1.0))
    hx, hy = world_of(*HOLE); cx, cy = cam.pt(hx, hy)
    s = 1000 * site_sc(HOLE[1]) * 1.2 / CAPH * cam.sc * P.get('cs', 1.6)
    rise = P.get('rise'); re_ = ev(T, rise[0], rise[1]) if rise else 1.0
    ytop = cy - 585 * s + (1 - re_) * 640 * s
    cheer = ev(T, *P['cheer']) if 'cheer' in P else 0.0
    crowd = site_crowd(T, cheer * 0.8 if P.get('crowd', True) else 0.0, 0.0, 12, P.get('seed', 3), tint=(0.95, 0.98, 1.04))
    crowd = [c for c in crowd if abs(cam.pt(c['x'], c['gy'])[0] - cx) > 500 * s]
    draw_items(cv, cam, [c for c in crowd if c['gy'] < hy + 4], T)
    back = cv.copy()
    outs = P.get('outs', []); first = outs[0] if outs else None
    e_door = ev(T, P['door'], P['door'] + 0.7) if 'door' in P else 0.0
    inside = None
    if first and T < first[0] + 0.3:
        inside = dict(ch=first[1], shirt=first[2], pants=first[3], pose={'aL': 6, 'aR': 6, 'head': 0}, tint=(1.0, 1.0, 1.0), gain=0.95)
    cap_with_man(cv, cx, ytop, s, T, e_door, inside, glow=re_)
    cv2.line(cv, (int(cx), 0), (int(cx), int(ytop)), (30.0, 34.0, 40.0), max(2, int(4 * s * 4)), cv2.LINE_AA)
    if rise and re_ < 1.0: m_ = np.zeros((H, W), bool); m_[int(hy):] = True; cv[m_] = back[m_]
    # men stepping out of the capsule: the door is at the capsule centre, they walk out to the side
    items = []
    gb = ytop + (DOOR[3] - 6) * s
    for k, (to, ch, sh_, pa_, gl) in enumerate(outs):
        a = ev(T, to, to + 0.25); wlk = ev(T, to + 0.15, to + 1.5); direction = P.get('dir', 1)
        if a <= 0: continue
        dest = 230 * s / 0.6 * (1.0 + 0.55 * k) * direction
        x = cx + wlk * dest; g_ = min(gb + 8 * s, cy + 20 * s + 40 * k) + 0.0
        up = ev(T, to + 0.6, to + 1.2) * (1 - 0.3 * (k > 0))
        w_ = math.sin(2 * math.pi * 2.0 * T + k * 1.9)
        pose = {'aL': 6 + (130 + 8 * w_) * up, 'aR': 6 + (128 - 8 * w_) * up, 'head': -8 * up + 2 * math.sin(T * 3 + k), 'fL': 0, 'fR': 0}
        if P.get('shade') and k >= 0: pose.update({'aL': 6 + 118 * up, 'fL': 140 * up})
        items.append(mk(ch, x, g_, 0.24 * s, -1 if direction > 0 else 1, k * 1.3, pose=pose, walk=1.0 if 0.03 < wlk < 0.97 else 0.0, gain=0.95 * a, shirt=sh_, pants=pa_, mouth=speak(T, k, 1.0) * up, glasses=gl, hop=abs(w_) * 16 * s * up * (k % 2 == 0)))
    if P.get('hug'):
        h_ = P['hug']; run = ev(T, h_[0], h_[0] + 1.2); fm = [('ar', -1.0, .22), ('w', -1.5, .19)]
        for j, (ch, offs, k_) in enumerate(fm):
            xx = cx + (offs * 280 * s / 0.6 * (1 - 0.85 * run)) * (1 if P.get('dir', 1) > 0 else -1) + (1 if P.get('dir', 1) > 0 else -1) * 150 * s / 0.6 * 0.5
            items.append(mk(ch, xx, cy + 22 * s + 14 * j, k_ * s, 1 if P.get('dir', 1) > 0 else -1, 3 + j, pose={'aL': 6 + 90 * run, 'aR': 6 + 100 * run, 'head': 4}, walk=1.0 if 0.03 < run < 0.97 else 0.0, gain=0.95))
    draw_g(cv, Cam(), items, T)
    draw_items(cv, cam, [c for c in crowd if c['gy'] >= hy + 4], T)
    puffs(cv, T, 54.0, 61.0, 8, (cx - 200, cy - 160, 400, 200), (210, 215, 225), seed=33, size=(30, 70), rise=(-30, 20), life=1.6, alpha=0.18) if P.get('steam') else None
    if P.get('flash'):
        r = np.random.default_rng(int(T * 14) % 50)
        for i in range(3):
            if r.random() > 0.45: fx_ = r.random() * W; fy_ = 300 + r.random() * 330; lb = LightBuf(); lb.glow(fx_, fy_, 60, (255, 255, 255), 0.9); lb.apply(cv, blur=18)
    vignette(cv, 0.35, 2.0); motes(cv, T, 60, 24, 0.6, (230, 225, 200))


# ---------------------------------------------------------------- 1-4. digging
def shot_rigs7(cv, T): P6.shot_rigs(cv, 55.3 + T)


def shot_meters(cv, T):
    k = ev(T, 2.2, 5.3); zz = 1.0; cyp = lerp(235, 330, k)
    sc, ox, oy = depth_view(cv, T, cyp, zz, 0.95); X = 688 * sc - ox
    steps = [ev(T, 1.5, 2.1), ev(T, 2.9, 3.5), ev(T, 4.2, 4.8)]; tipy = 172 + 30 * steps[0] + 30 * steps[1] + 30 * steps[2]
    lb = LightBuf(); Y0 = 160 * sc - oy; Y1 = tipy * sc - oy
    for yy in np.linspace(Y0, Y1, 8): lb.glow(X, yy, 22 * zz, (110, 190, 255), 0.22)
    lb.glow(X, Y1, 60 * zz, (140, 215, 255), 0.7 + 0.2 * math.sin(T * 14)); lb.glow(X, Y1, 190 * zz, (70, 150, 240), 0.3); lb.apply(cv, blur=22)
    for j, (t0, yy) in enumerate(((2.1, 202), (3.5, 232), (4.8, 262))):
        e = ev(T, t0 - 0.5, t0 + 0.2) * 1.0; yq = yy * sc - oy
        if e > 0: cv2.line(cv, (int(X - 70 * e), int(yq)), (int(X - 14), int(yq)), (225.0, 240.0, 250.0), 3, cv2.LINE_AA)
    dxy = shake_xy(T, 0.4); cv[:] = np.roll(np.roll(cv, int(dxy[0] * 0.5), 1), int(dxy[1] * 0.5), 0) if False else cv
    motes(cv, T, 56, 24, 0.4, (210, 200, 180)); vignette(cv, 0.35, 2.0); finish(cv, T, 120, 0.45, 10)


def shot_hard(cv, T):
    k = seg(T, 5.1, 8.2); cam = wall_cam(T, k, 1.0, 1.12, 0.9 + 0.5 * math.sin(T * 2.0) ** 2)
    wall_bg(cv, T, cam, 0.8)
    adv = ev(T, 5.2, 8.1); tip = cam.pt(640 + 2 * math.sin(T * 45), lerp(250, 345, adv) + 3 * math.sin(T * 60)); s = 0.60 * cam.sc
    draw_bit(cv, tip, s, rot=1.4 * math.sin(T * 38), gain=0.95, tint=(0.92, 1.0, 1.08))
    r = np.random.default_rng(7); lb = LightBuf()
    for i in range(34):
        ph = (T * 3.2 + r.random()) % 1.0; ang = math.radians(-90 + 150 * (r.random() - 0.5) + (60 if i % 2 else -60)); sp = 120 + 260 * r.random()
        x = tip[0] + math.cos(ang) * sp * ph; y = tip[1] + math.sin(ang) * sp * ph + 380 * ph * ph
        a = (1 - ph); cv2.circle(cv, (int(x), int(y)), 2, (60.0 * a, 160.0 * a + 40, 255.0 * a), -1, cv2.LINE_AA)
    lb.glow(tip[0], tip[1], 70 * cam.sc, (60, 150, 255), 0.5); lb.apply(cv, blur=20)
    puffs(cv, T, 5.2, 8.2, 20, (440, 150, 400, 300), (110, 150, 190), seed=121, size=(50, 130), rise=(-20, 40), life=2.0, alpha=0.26, wind=(8, 0))
    chunk_fall(cv, T, 5.5, 8.0, 10, 71, 470, 820, 640, cam.sc); finish(cv, T, 121, 0.5, 24)


def shot_long(cv, T): P6.shot_lifeline(cv, 10.0 + (T - 8.0))


def shot_danger7(cv, T):
    k = seg(T, 9.2, 12.5); sh = 0.3 + 1.0 * P(T, 10.0, 12.3); dxy = shake_xy(T, sh)
    cam = Cam(A=(640, 600), sb=lerp(1.0, 1.10, k), sw=lerp(1.0, 1.22, k), sc=lerp(1.0, 1.14, k), d=dxy, dw=(dxy[0] * 1.5, dxy[1] * 1.5))
    chamber_bg(cv, T, cam, 0.5, lamps=0.7 - 0.2 * flick(T, 9.0)); items = []
    for i, c in enumerate(GRID):
        if abs(c['x'] - 640) < 150 and c['gy'] > 640: continue
        cov = ev(T, 10.2 + 0.02 * (i % 9), 10.8 + 0.02 * (i % 9)); items.append(dict(c, pose={'head': -12 * ev(T, 9.4, 9.9) + 8 * cov + 2 * math.sin(T * 8 + i) * cov, 'aL': 4 + 114 * cov, 'fL': 140 * cov, 'aR': 4 + 114 * cov * (i % 2), 'fR': 140 * cov * (i % 2)}, crouch=0.15 + 0.2 * cov, gain=0.76, tint=CT, sway=0.2))
    items.append(mk('u', 640, 722, .54, 1, 0.4, pose={'head': -14 * ev(T, 9.4, 9.9), 'aL': 8, 'aR': 8}, gain=1.0, tint=(0.95, 1.0, 1.06), crouch=0.04))
    draw_items(cv, cam, items, T)
    r = np.random.default_rng(12)
    for j in range(6):   # cracks growing in the ceiling
        g = ev(T, 9.5 + 0.3 * j, 10.5 + 0.3 * j); x = 140 + 1000 * r.random(); pts = [(x, 0.0)]
        for q in range(7): x += r.normal(0, 28); pts.append((x, (q + 1) * 34.0))
        n = max(2, int(1 + g * 7)); cv2.polylines(cv, [np.array(pts[:n], np.int32)], False, (6.0, 8.0, 12.0), max(2, int(3 * cam.sc)), cv2.LINE_AA)
    chunk_fall(cv, T, 9.8, 12.2, 26, 72, 160, 1120, 700, cam.sc)
    puffs(cv, T, 9.5, 12.5, 24, (100, 0, 1080, 200), (110, 150, 190), seed=122, size=(40, 100), rise=(-30, 20), life=1.8, alpha=0.30)
    veil(cv, T, 0.1 + 0.12 * ev(T, 10.5, 12.3)); tone(cv, 1.0, 0, (0.93, 0.98, 1.06), 1.0); finish(cv, T, 122, 0.6, 26)


def shot_reach(cv, T):
    k = ev(T, 12.4, 14.1); zz = lerp(0.8, 1.2, k); cyp = min(lerp(430, 590, k), 768 - 192 / zz)
    sc, ox, oy = depth_view(cv, T, cyp, zz, 0.95); X = 688 * sc - ox; ar = ev(T, 12.6, 13.5); tipy = lerp(250, 685, ar)
    lb = LightBuf(); Y1 = tipy * sc - oy
    for yy in np.linspace(160 * sc - oy, Y1, 10): lb.glow(X, yy, 22 * zz, (110, 190, 255), 0.2)
    lb.glow(X, Y1, 60 * zz, (140, 215, 255), 0.7 + 0.2 * math.sin(T * 14)); lb.glow(X, Y1, 200 * zz, (70, 150, 240), 0.3)
    q = (X, 685 * sc - oy); fl = ev(T, 13.4, 13.8) * (1 - ev(T, 13.8, 14.2)); lb.glow(q[0], q[1], 200 * zz, (255, 235, 200), 0.9 * fl); lb.glow(q[0], q[1], 600 * zz, (255, 200, 120), 0.4 * fl); lb.apply(cv, blur=26)
    cv += 40 * fl; motes(cv, T, 56, 24, 0.4, (210, 200, 180)); vignette(cv, 0.35, 2.0); finish(cv, T, 123, 0.45, 10)


def chamber_men(T, up=0.0, hope=0.0, cold_=False, skip_centre=True, gain=0.8, look=0.0):
    items = []
    for i, c in enumerate(GRID):
        if skip_centre and abs(c['x'] - 640) < 150 and c['gy'] > 640: continue
        w_ = math.sin(2 * math.pi * 1.6 * T + i * 0.8)
        items.append(dict(c, pose={'head': -14 * look + 2 * math.sin(T + i), 'aL': 4 + 130 * hope * (0.5 + 0.5 * w_) * (i % 2 == 0) + 110 * hope * (i % 2), 'aR': 4 + 120 * hope * (0.5 - 0.5 * w_)}, crouch=0.08, gain=gain, tint=CT, sway=0.3, hop=abs(w_) * 10 * hope))
    return items


def shot_break7(cv, T):
    k = seg(T, 14.0, 16.3); sh = 0.3 * ev(T, 14.0, 14.5) + 1.4 * P(T, 14.6, 15.8); cam = wall_cam(T, k, 1.0, 1.08, sh, A=(640, 400))
    chamber_bg(cv, T, cam, 0.5, lamps=0.55); items = chamber_men(T, look=ev(T, 14.1, 14.6), gain=0.78)
    items.append(mk('u', 640, 722, .54, 1, 0.4, pose={'head': -16 * ev(T, 14.1, 14.6), 'aL': 8, 'aR': 8}, gain=1.0, tint=(0.95, 1.0, 1.06), crouch=0.04)); draw_items(cv, cam, items, T)
    e = ev(T, 14.5, 15.3); ceiling_hole(cv, cam, e, T, 640, 90, 80, cracks=True, light=1.5 * ev(T, 15.3, 16.0))
    ex = ev(T, 14.9, 15.4) * (1 - ev(T, 15.6, 16.2)); tip = cam.pt(640 + 3 * math.sin(T * 45), lerp(-640, 300, ex) + 3 * math.sin(T * 60))
    if ex > 0: draw_bit(cv, tip, 0.5 * cam.sc, rot=1.2 * math.sin(T * 38), gain=0.95, tint=(0.92, 1.0, 1.08))
    chunk_fall(cv, T, 14.8, 16.0, 16, 73, 520, 760, 700, cam.sc)
    puffs(cv, T, 14.8, 16.3, 18, (440, 0, 400, 300), (110, 150, 190), seed=124, size=(50, 130), rise=(-20, 40), life=2.0, alpha=0.28)
    cv += 40 * P(T, 15.2, 15.6); finish(cv, T, 124, 0.5, 20)


def hole_chamber(cv, T, k, light, dark=0.55, men=None, z=(1.0, 1.1), lamps=0.6):
    cam = Cam(A=(640, 560), sb=lerp(z[0], z[1], k), sw=lerp(z[0], z[1] * 1.1, k), sc=lerp(z[0], z[1] * 1.05, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, dark, lamps=lamps)
    if men: draw_items(cv, cam, men(cam), T)
    ceiling_hole(cv, cam, 1.0, T, 640, 90, 80, cracks=True, light=light)
    return cam


def shot_way(cv, T):
    k = seg(T, 16.2, 19.2); hp = ev(T, 16.6, 18.6)
    def men(cam):
        it = chamber_men(T, hope=hp * 0.8, look=ev(T, 16.3, 16.8) * (1 - hp), gain=0.82)
        it.append(mk('u', 640, 722, .54, 1, 0.4, pose={'head': -14 + 8 * hp, 'aL': 8 + 120 * hp, 'aR': 8 + 110 * hp}, gain=1.0, tint=(0.95, 1.0, 1.06), crouch=0.04)); return it
    cam = hole_chamber(cv, T, k, 1.4, 0.6, men, (1.0, 1.1), 0.7)
    lb = LightBuf(); q = cam.pt(640, 60); lb.glow(q[0], q[1], 120 * cam.sc, (255, 235, 205), 0.6); lb.apply(cv, blur=30)
    puffs(cv, T, 16.3, 19.2, 14, (560, 0, 160, 400), (255, 240, 210), seed=125, size=(20, 50), rise=(30, 60), life=2.0, alpha=0.12)
    tone(cv, 1.0, 0, (0.98, 1.0, 1.03), 1.0); finish(cv, T, 125, 0.5, 22)


def shot_problem(cv, T):
    k = seg(T, 19.0, 20.9); dim = ev(T, 19.2, 20.2)
    def men(cam):
        it = []
        for i, c in enumerate(GRID):
            if abs(c['x'] - 640) < 150 and c['gy'] > 640: continue
            it.append(dict(c, pose={'head': -6 + 10 * math.sin(T * 1.8 + i) * dim, 'aL': 4, 'aR': 4}, crouch=0.1 + 0.1 * dim, gain=0.8 - 0.2 * dim, tint=CT, sway=0.3))
        it.append(mk('u', 640, 722, .54, 1, 0.4, pose={'head': 12 * math.sin(T * 3.0) * dim, 'aL': 8, 'aR': 8 + 30 * dim}, gain=1.0 - 0.2 * dim, tint=(0.95, 1.0, 1.06), crouch=0.04)); return it
    cam = hole_chamber(cv, T, k, 1.4 * (1 - 0.7 * dim), 0.6 - 0.2 * dim, men, (1.1, 1.3), 0.7 - 0.3 * dim)
    veil(cv, T, 0.1 * dim); finish(cv, T, 126, 0.55, 18)


def shot_narrow(cv, T):
    k = seg(T, 20.7, 24.1); cam = Cam(A=(640, 560), sb=lerp(1.05, 1.15, k), sw=lerp(1.1, 1.25, k), sc=lerp(1.05, 1.15, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.55, lamps=0.7)
    items = []
    for i, c in enumerate(GRID):
        if c['gy'] > 640: continue
        items.append(dict(c, pose={'head': -8 + 2 * math.sin(T + i), 'aL': 4, 'aR': 4}, crouch=0.1, gain=0.6, tint=CT, sway=0.3))
    ar = ev(T, 21.3, 22.2) * (1 - 0.2 * ev(T, 23.0, 24.0))
    items.append(mk('u', 470, 722, .62, 1, 0.4, pose={'head': -10 + 10 * math.sin(T * 2.2) * ev(T, 22.8, 23.6), 'aL': 8 + 76 * ar, 'aR': 8 + 76 * ar, 'fL': 0, 'fR': 0}, gain=1.0, tint=(0.95, 1.0, 1.06), crouch=0.04, mouth=0.0))
    draw_items(cv, cam, items, T)
    ceiling_hole(cv, cam, 0.5, T, 790, 60, 40, cracks=False, light=0.8)
    top = cam.pt(790, -40); bot = cam.pt(790, 260); cable(cv, [top, bot], w=max(3, int(10 * cam.sc)), col=(70.0, 82.0, 92.0), hi=(170.0, 185.0, 195.0))
    lb = LightBuf(); q = cam.pt(790, 20); lb.glow(q[0], q[1], 80 * cam.sc, (255, 235, 205), 0.4); lb.apply(cv, blur=26)
    veil(cv, T, 0.06); finish(cv, T, 127, 0.55, 18)


CAPS = [(0.42, 0.82), (0.42, 0.24), (0.44, 0.15), (0.50, 0.11), (0.56, 0.15), (0.58, 0.24), (0.58, 0.82), (0.56, 0.88), (0.50, 0.9), (0.44, 0.88), (0.42, 0.82)]
CWIN = [(0.5 + 0.045 * math.cos(a / 12.0 * 2 * math.pi), 0.30 + 0.06 * math.sin(a / 12.0 * 2 * math.pi)) for a in range(13)]
STICK = [[(0.5 + 0.03 * math.cos(a / 10.0 * 2 * math.pi), 0.46 + 0.045 * math.sin(a / 10.0 * 2 * math.pi)) for a in range(11)], [(0.5, 0.505), (0.5, 0.68)], [(0.43, 0.58), (0.5, 0.54), (0.57, 0.58)], [(0.5, 0.68), (0.46, 0.8)], [(0.5, 0.68), (0.54, 0.8)]]
ARROWS = [[(0.72, 0.8), (0.72, 0.2), (0.70, 0.27), (0.72, 0.2), (0.74, 0.27)], [(0.28, 0.8), (0.28, 0.2), (0.26, 0.27), (0.28, 0.2), (0.30, 0.27)]]


def shot_draft(cv, T):
    k = seg(T, 23.9, 27.8); z = lerp(2.0, 2.3, k); cam = Cam(A=(680, 520), sb=z, sw=z, sc=z); cam.d = paper_center(z); cam.dw = cam.d
    paper_bg(cv, T, cam); tip = None; ink = (26.0, 34.0, 52.0)
    seq = [(CAPS, seg(T, 24.2, 25.2), ink, 2.4), (CWIN, seg(T, 25.2, 25.6), ink, 2.0), (STICK[0], seg(T, 26.0, 26.3), (40.0, 40.0, 195.0), 2.4), (STICK[1], seg(T, 26.3, 26.55), (40.0, 40.0, 195.0), 2.4), (STICK[2], seg(T, 26.55, 26.8), (40.0, 40.0, 195.0), 2.4),
           (STICK[3], seg(T, 26.8, 27.0), (40.0, 40.0, 195.0), 2.4), (STICK[4], seg(T, 27.0, 27.2), (40.0, 40.0, 195.0), 2.4), (ARROWS[0], seg(T, 25.6, 25.9), (70.0, 150.0, 55.0), 2.4), (ARROWS[1], seg(T, 25.8, 26.0), (70.0, 150.0, 55.0), 2.4)]
    for pts, pr, col, w_ in seq:
        if pr > 0:
            t_ = stroke(cv, cam, pts, pr, w=w_, col=col)
            if pr < 1.0: tip = t_
    if tip is None and T < 27.5: tip = bpt(cam, *paper_pt(0.5, 0.8))
    if T < 27.6: pencil(cv, tip, -32, 150, cam.sb / 2.0)
    veil(cv, T, 0.04); finish(cv, T, 128, 0.5, 14)


def shot_reveal(cv, T):
    k = seg(T, 27.6, 32.0); z = lerp(1.0, 1.14, k); cam = site_cam(z, 688, 560, 640, 520)
    site_bg(cv, T, cam, 0.42)
    s = 1000 * 0.52 * 1.1 / CAPH * cam.sc; cx, cy = 640, 700; ytop = cy - 585 * s
    lb = LightBuf(); lb.glow(cx, ytop - 80, 360, (255, 235, 200), 0.35 * ev(T, 27.8, 28.8)); lb.glow(cx, cy - 300 * s, 520, (255, 220, 160), 0.25 * ev(T, 27.8, 28.8)); lb.apply(cv, blur=36)
    shade_ell(cv, cx, cy + 6, 120 * s, 20 * s, 0.6)
    cap_draw(cv, cx, ytop, s, gain=1.0, tint=(1.02, 1.0, 0.98))
    ph = ev(T, 29.1, 29.9) * (1 - 0.2 * ev(T, 31.0, 31.9)); pc = lpt(cx, ytop, s, 120, 440)
    if ph > 0:
        lb = LightBuf(); lb.glow(pc[0], pc[1], 130 * s * 2, (60, 150, 255), 0.35 * ph); lb.apply(cv, blur=24); phoenix(cv, pc[0], pc[1], 60 * s * ph, 0.95, T)
    items = [mk('m', 330, 704, .36, 1, 0.3, pose={'head': -12 + 2 * math.sin(T), 'aL': 8 + 60 * P(T, 28.4, 29.6), 'aR': 8}, gain=0.85, tint=HOT, shirt=SHIRTS[2], pants=PANTS[2]), mk('m', 950, 706, .36, -1, 1.1, pose={'head': -12, 'aL': 8, 'aR': 8 + 50 * P(T, 30.0, 31.2)}, gain=0.85, tint=HOT, shirt=SHIRTS[7], pants=PANTS[5])]
    draw_items(cv, cam, items, T)
    r = np.random.default_rng(14)
    for i in range(20):   # welding sparks
        ph_ = (T * 1.7 + r.random()) % 1.0; x = cx + (r.random() - 0.5) * 200; y = ytop + 300 * s + 300 * ph_ * ph_ - 200 * ph_; a = 1 - ph_
        cv2.circle(cv, (int(x), int(y)), 2, (60.0 * a, 180.0 * a + 30, 255.0 * a), -1, cv2.LINE_AA)
    vignette(cv, 0.4, 2.0); finish(cv, T, 129, 0.5, 20)


def chamber_floor(cv, T, cam, dark=0.5, lamps=0.55): chamber_bg(cv, T, cam, dark, lamps=lamps)


def enter_shot(cv, T, t0, t_in, t_door, t_rise, t1, ch, glow_end=1.0, seed=130, crowd=True):
    """a capsule standing in the chamber under the hole: the man walks in, the door closes, the capsule rises through the ceiling"""
    k = seg(T, t0 - 0.1, t1 + 0.1); up = ev(T, t_rise, t1 + 0.4)
    cam = Cam(A=(640, 380 + 0 * k), sb=lerp(1.0, 1.04, k), sw=lerp(1.0, 1.1, k), sc=lerp(1.0, 1.06, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.55, lamps=0.65)
    items = []
    for i, c in enumerate(GRID if crowd else []):
        if abs(c['x'] - 640) < 190 and c['gy'] > 600: continue
        w_ = math.sin(2 * math.pi * 1.8 * T + i * 0.7)
        items.append(dict(c, pose={'head': -10 * ev(T, t_door - 0.5, t_door + 0.5) + 2 * math.sin(T + i), 'aL': 4 + 120 * up * (i % 2) * (0.6 + 0.4 * w_), 'aR': 4 + 40 * up}, crouch=0.08, gain=0.74, tint=CT, sway=0.3))
    draw_items(cv, cam, items, T)
    s = 1.12 * cam.sc * 1.0; cx = 640; floor = 700; ytop0 = floor - 585 * s; ytop = ytop0 - up * 1100
    cable(cv, [(cx, 0), (cx, ytop + 4)], w=max(3, int(5 * cam.sc)), col=(40.0, 46.0, 54.0), hi=(110.0, 120.0, 130.0))
    e_door = ev(T, t_in - 0.3, t_in + 0.4) * (1 - ev(T, t_door, t_door + 0.9))
    gb = ytop + (DOOR[3] - 6) * s
    walk = ev(T, t_in - 1.6, t_in); xw = lerp(950, cx, walk)
    inside = dict(ch=ch, pose={'aL': 6, 'aR': 6, 'head': 0}, tint=(1.0, 1.0, 1.0), gain=0.95, shirt=SHIRTS[1] if ch == 'm' else None)
    show_in = ev(T, t_in, t_in + 0.3)
    shade_ell(cv, cx, floor - 6, 110 * s, 18 * s, 0.55 * (1 - up))
    if T < t_in + 0.3:
        # outside man walking to the door (same size as the one inside)
        out = mk(ch, xw, gb, 0.375 * s, -1, 0.7, pose={'aL': 8, 'aR': 8, 'head': -6}, walk=1.0 if 0.02 < walk < 0.98 else 0.0, gain=0.95 * (1 - show_in), shirt=SHIRTS[1] if ch == 'm' else None)
        cap_with_man(cv, cx, ytop, s, T, e_door, None); draw_items(cv, cam, [out], T)
        if show_in > 0: cap_with_man(cv, cx, ytop, s, T, e_door, dict(inside, gain=0.95 * show_in))
    else:
        cap_with_man(cv, cx, ytop, s, T, e_door, inside, glow=up, straps=0.0)
    ceiling_hole(cv, cam, 1.0, T, 640, 90, 80, cracks=True, light=1.0)
    lb = LightBuf(); lb.glow(cx, ytop + 150 * s, 110 * s * 2, (110, 190, 255), 0.18 * up); lb.apply(cv, blur=26)
    chunk_fall(cv, T, t_rise, t1, 10, seed, 560, 720, 700, cam.sc)
    puffs(cv, T, t_rise, t1 + 0.5, 12, (500, 0, 280, 400), (150, 175, 200), seed=seed + 1, size=(30, 80), rise=(30, 70), life=1.6, alpha=0.15)
    tone(cv, 1.0, 0, (0.96, 1.0, 1.06), 1.0); finish(cv, T, seed + 2, 0.5, 20)


def shot_enter(cv, T):   # 32.0 - 34.3 : the man inside, strapped; the capsule closes and starts
    k = seg(T, 31.9, 34.4); z = lerp(1.0, 1.25, k); cam = Cam(A=(640, 380), sb=z, sw=1.1 * z, sc=z, d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.5, lamps=0.6)
    s = 1.15 * cam.sc; cx = 640; ytop = 420 - 585 * s * 0.55 * 0 + 20 - 40; ytop = lerp(40, 20, k) - 40 * ev(T, 33.4, 34.4)
    e = ev(T, 31.9, 32.4) * (1 - ev(T, 32.8, 33.4)); st = ev(T, 32.3, 32.7)
    cable(cv, [(cx, 0), (cx, ytop + 4)], w=max(3, int(5 * cam.sc)), col=(40.0, 46.0, 54.0), hi=(110.0, 120.0, 130.0))
    inside = dict(ch='m', pose={'aL': 6, 'aR': 6, 'head': 3 * math.sin(T * 1.6)}, tint=(1.0, 1.0, 1.0), gain=0.95, shirt=SHIRTS[1])
    cap_with_man(cv, cx, ytop, s, T, e, inside, glow=ev(T, 33.4, 34.0), straps=st * (1 - ev(T, 32.9, 33.1)))
    lb = LightBuf(); lb.glow(cx, ytop + 330 * s, 160 * s * 2, (110, 190, 255), 0.2); lb.apply(cv, blur=26)
    puffs(cv, T, 33.3, 34.4, 10, (500, 400, 280, 300), (150, 175, 200), seed=131, size=(30, 80), rise=(30, 70), life=1.6, alpha=0.15)
    veil(cv, T, 0.06); finish(cv, T, 131, 0.55, 20)


def shot_far(cv, T):   # 34.3 - 36.0 : 700 metres, ticks light up one by one
    k = ev(T, 34.2, 36.1); zz = 0.58; cyp = 384
    sc, ox, oy = depth_view(cv, T, cyp, zz, 0.92); X = 688 * sc - ox; lb = LightBuf()
    for j in range(8):
        t_ = 34.4 + 0.2 * j; e = ev(T, t_, t_ + 0.2); yy = (685 - j * 75) * sc - oy
        if e > 0: cv2.line(cv, (int(X - 16 * e), int(yy)), (int(X - 4), int(yy)), (225.0, 240.0, 250.0), 2, cv2.LINE_AA); lb.glow(X - 12, yy, 14, (140, 215, 255), 0.5 * e)
    yp = lerp(685, 160, ev(T, 34.3, 36.0) ** 1.2); Y = yp * sc - oy
    cap_draw(cv, X, Y - 45, 0.18, gain=1.0); lb.glow(X, Y, 26, (120, 200, 255), 0.7); lb.glow(X, Y, 90, (70, 150, 240), 0.25)
    q = (X, 685 * sc - oy); lb.glow(q[0], q[1], 60, (110, 190, 255), 0.5); lb.apply(cv, blur=22)
    vignette(cv, 0.4, 2.0); finish(cv, T, 132, 0.5, 8)


def shaft_view(cv, T, zoom, flip=False, glow_top=0.0, glow_bot=0.0, dark=1.0, ox=0.0, oy=0.0):
    im = L('h7_shaft'); s = S0 * zoom; cx, cy = 688, 384
    if flip:
        place(cv, im, M3(640 - cx * s + ox, 360 + (768 - cy) * s * 0 + oy + (cy * s), s, -s, 0, 0, 768 * 0.0 + 0.0), gain=dark) if False else None
    place(cv, im, M3(640 - cx * s + ox, 360 - cy * s + oy, s, s, 0, 0, 0), gain=dark)


def shot_alone(cv, T):   # 36.0 - 38.7: the man alone in the capsule, rock walls sliding past
    k = seg(T, 35.9, 38.8); shaft_view(cv, T, lerp(1.0, 1.5, k), dark=0.8)
    # strata streaks sliding down = ascent
    r = np.random.default_rng(9)
    for i in range(26):
        x = r.random() * W; y = ((r.random() * H) + T * (160 + 120 * r.random())) % H; ln = 40 + 90 * r.random(); a = 0.25 * r.random()
        cv2.line(cv, (int(x), int(y)), (int(x), int(y + ln)), (60.0 * a * 3, 90.0 * a * 3, 130.0 * a * 3), 2, cv2.LINE_AA)
    s = 1.05; cx = 640; ytop = 120 + 6 * math.sin(T * 7.0)
    cap_with_man(cv, cx, ytop, s, T, 0.0, dict(ch='m', pose={'aL': 6, 'aR': 6, 'head': 4 * math.sin(T * 1.3) + 6}, tint=(0.9, 0.95, 1.0), gain=0.9, shirt=SHIRTS[1]), glow=0.0)
    cv *= 1 - 0.0; vignette(cv, 0.65, 2.0); finish(cv, T, 133, 0.7, 24)


def shot_below(cv, T):   # 38.7 - 40.6: looking down into the dark void, a faint warm glow far below
    k = seg(T, 38.6, 40.7); z = lerp(1.6, 1.0, k)
    im = L('h7_shaft'); s = S0 * z
    m = M3(640 + 688 * s, 360 + 384 * s, -s, -s, 0, 0, 0)   # rotated 180 deg
    place(cv, im, m, gain=0.55)
    lb = LightBuf(); lb.glow(640, 360, 60, (60, 140, 240), 0.35 + 0.1 * math.sin(T * 3.0)); lb.glow(640, 360, 220, (40, 110, 220), 0.18); lb.apply(cv, blur=24)
    r = np.random.default_rng(10)
    for i in range(30):
        x = 640 + (r.random() - 0.5) * 700; y = ((r.random() * H) - T * 60 * (0.5 + r.random())) % H; cv2.circle(cv, (int(x), int(y)), 1, (150.0, 170.0, 190.0), -1, cv2.LINE_AA)
    vignette(cv, 0.8, 2.0); finish(cv, T, 134, 0.8, 0)


def shot_above(cv, T):   # 40.6 - 42.6: the light above grows, the whole world waits
    k = ev(T, 40.5, 42.7); shaft_view(cv, T, lerp(1.0, 2.6, k), dark=0.9)
    lb = LightBuf(); lb.glow(640, 360, 80 * (1 + 2 * k), (255, 235, 200), 0.5 + 0.5 * k); lb.glow(640, 360, 300 * (1 + k), (255, 210, 140), 0.25 + 0.3 * k); lb.apply(cv, blur=30)
    vignette(cv, 0.6 - 0.2 * k, 2.0); finish(cv, T, 135, 0.6, 20)


def shot_night(cv, T):   # 42.6 - 46.0
    k = seg(T, 42.5, 46.1); cam = site_cam(lerp(1.0, 1.28, k), 688, 440, 640, 400)
    site_bg(cv, T, cam, 1.0)
    items = site_crowd(T, 0.0, 0.0, 22, 5, ((120, 1250), (540, 720)), tint=(0.9, 0.95, 1.05)) + site_crowd(T, 0.0, 0.0, 12, 8, ((450, 930), (505, 540)))
    for it in items: it['pose']['head'] = -8 + 2 * math.sin(T + it['ph0'])
    draw_items(cv, cam, items, T)
    lb = LightBuf(); r = np.random.default_rng(12)
    for i in range(14):
        x = 130 + 1020 * r.random(); y = 560 + 120 * r.random(); lb.glow(*cam.pt(S0 * x - OX, S0 * y - OY), 14 * cam.sc, (90, 170, 255), 0.5 * (0.7 + 0.3 * math.sin(T * 3 + i)))
    lb.apply(cv, blur=18); motes(cv, T, 61, 26, 0.5, (230, 225, 200)); vignette(cv, 0.4, 2.0)


# ---------------------------------------------------------------- the rescue begins
def shot_enter1(cv, T): enter_shot(cv, T, 46.0, 47.6, 48.0, 49.5, 51.2, 'm', seed=130)


def shot_rise(cv, T):   # 51.2 - 54.6 slowly... higher... higher... higher
    zz = 0.8; p = 0.7 * ev(T, 51.2, 54.7) + 0.1 * (ev(T, 52.0, 52.5) + ev(T, 52.9, 53.4) + ev(T, 53.7, 54.2)); yp = lerp(670, 175, clamp(p)); cyp = min(max(yp, 240), 768 - 192 / zz)
    sc, ox, oy = depth_view(cv, T, cyp, zz, 0.92); X = 688 * sc - ox; Y = yp * sc - oy; lb = LightBuf()
    for j in range(1, 7): lb.glow(X, Y + 26 * j * zz, 16 * zz * (1 + 0.1 * j), (110, 190, 255), 0.35 * (1 - j / 7.0))
    sur = 0.6 * (P(T, 52.0, 52.5) + P(T, 52.9, 53.4) + P(T, 53.7, 54.2)); cap_draw(cv, X, Y - 80, 0.27, gain=1.0)
    lb.glow(X, Y, 50, (120, 200, 255), 0.7 + sur); lb.glow(X, Y, 130, (70, 150, 240), 0.25 + 0.2 * sur)
    q = (X, 685 * sc - oy); lb.glow(q[0], q[1], 80 * zz, (110, 190, 255), 0.45); lb.apply(cv, blur=22)
    vignette(cv, 0.4, 2.0); finish(cv, T, 136, 0.5, 8)


def shake_ar(T): return 0.9 * P(T, 54.6, 56.4) + 0.2


SURF1 = dict(z=lambda T: lerp(2.0, 2.35, seg(T, 54.5, 60.0)), fx=688, fy=470, rise=(54.6, 56.4), door=56.73, outs=[(58.16, 'm', SHIRTS[1], None, False)], cheer=(58.4, 59.2), shk=shake_ar, steam=True, hug=None)


def shot_surface1(cv, T): surface_shot(cv, T, SURF1)


def shot_crowd(cv, T):   # 60.0 - 62.2 people screaming with joy
    k = seg(T, 59.9, 62.3); cam = site_cam(lerp(1.5, 1.7, k), 688, 560, 640, 470); site_bg(cv, T, cam, 1.0)
    ch = ev(T, 60.0, 60.5); items = site_crowd(T, ch, 0.0, 30, 21, ((250, 1150), (520, 700)), hop=1.6)
    draw_items(cv, cam, items, T)
    r = np.random.default_rng(15)
    if ch > 0.5:
        for i in range(60):
            x = r.random() * W; sp = 60 + 140 * r.random(); y = (H - ((T - 60.0) * sp + r.random() * 200)) % H; c = 150 + 100 * r.random(); cv2.circle(cv, (int(x), int(y)), 1 + int(r.random() > .6), (c * .45, c * .8, c), -1, cv2.LINE_AA)
    vignette(cv, 0.4, 2.0); motes(cv, T, 62, 20, 0.5, (230, 225, 200))


def camera_prop(cv, x, y, s, T, i):
    for dx in (-26, 0, 26): cv2.line(cv, (int(x), int(y - 30 * s)), (int(x + dx * s), int(y + 70 * s)), (14.0, 16.0, 20.0), max(2, int(5 * s)), cv2.LINE_AA)
    rrect(cv, x, y - 52 * s, 80 * s, 46 * s, 0, (36.0, 40.0, 46.0)); cv2.circle(cv, (int(x + 46 * s), int(y - 52 * s)), max(3, int(18 * s)), (18.0, 18.0, 22.0), -1, cv2.LINE_AA); cv2.circle(cv, (int(x + 46 * s), int(y - 52 * s)), max(2, int(10 * s)), (110.0, 90.0, 60.0), -1, cv2.LINE_AA)
    cv2.circle(cv, (int(x - 30 * s), int(y - 66 * s)), max(2, int(4 * s)), (40.0, 40.0, 230.0), -1, cv2.LINE_AA)


def shot_cams(cv, T):   # 62.2 - 62.9 flashes
    k = seg(T, 62.1, 63.0); cam = site_cam(lerp(1.5, 1.6, k), 688, 560, 640, 470); site_bg(cv, T, cam, 0.9)
    items = site_crowd(T, 0.7, 0.0, 26, 21, ((250, 1150), (520, 700)), hop=1.0) + site_crowd(T, 0.0, 1.0, 8, 24, ((300, 1100), (600, 700)))
    draw_items(cv, cam, items, T)
    for i, x in enumerate((180, 420, 860, 1100)): camera_prop(cv, x, 640 + 20 * (i % 2), 1.7 - 0.2 * (i % 2), T, i)
    r = np.random.default_rng(int(T * 22) % 60); lb = LightBuf()
    for i in range(5):
        if r.random() > 0.35: lb.glow(120 + r.random() * 1040, 230 + r.random() * 420, 44 + 40 * r.random(), (255, 255, 255), 1.0)
    lb.apply(cv, blur=16); cv += 18 * (r.random() > 0.5); vignette(cv, 0.4, 2.0)


def shot_families(cv, T):   # 62.9 - 64.7 reunions, journalists
    k = seg(T, 62.8, 64.8); cam = site_cam(lerp(2.1, 2.4, k), 600, 560, 640, 500); site_bg(cv, T, cam, 1.0)
    hug = ev(T, 63.1, 63.9); items = []
    pairs = [(470, 'm', 'ar', 1, 0), (640, 'm', 'w', -1, 1), (800, 'm', 'ar', 1, 2)]
    for px, a, b, fl, i in pairs:
        py = 585 + 6 * i; x, gy = world_of(px, py); sc = site_sc(py) * 1.2
        items.append(mk(a, x, gy, sc, fl, i * 1.3, pose={'aL': 20 + 100 * hug, 'aR': 24 + 110 * hug, 'fL': -28 * hug, 'fR': 12 * hug, 'head': 4 * math.sin(T * 1.4 + i)}, gain=0.95, shirt=SHIRTS[(i * 3 + 1) % 10], pants=PANTS[(i * 5 + 2) % 10]))
        items.append(mk(b, x + fl * 70 * sc / 0.35 * (1 - 0.6 * hug) * 0.5, gy + 4, sc * 0.9, -fl, i * 1.1 + 2, pose={'aL': 22 + 100 * hug, 'aR': 28 + 100 * hug, 'fR': -30 * hug, 'head': -4 * math.sin(T * 1.2 + 1)}, gain=0.95))
    jr = [(300, 'm', 1), (990, 'm', -1)]
    for i, (px, ch, fl) in enumerate(jr):
        x, gy = world_of(px, 575); items.append(mk(ch, x, gy, site_sc(575) * 1.1, fl, 5 + i, pose={'aL': 8, 'aR': 8 + 90 * ev(T, 63.0, 63.6), 'fR': 30, 'head': 3 * math.sin(T * 2)}, gain=0.95, shirt=SHIRTS[6 + i], pants=PANTS[3], mouth=speak(T, i, 0.7) * ev(T, 63.0, 63.6)))
    draw_items(cv, cam, items, T)
    r = np.random.default_rng(int(T * 12) % 50); lb = LightBuf()
    if r.random() > 0.5: lb.glow(100 + r.random() * 1000, 250 + r.random() * 250, 40, (255, 255, 255), 0.8)
    lb.apply(cv, blur=16); vignette(cv, 0.4, 2.0)


def shot_sun(cv, T):   # 64.7 - 68.5 the sun, for the first time in more than two months
    k = seg(T, 64.6, 68.6); z = lerp(1.0, 1.18, k); cam = Cam(A=(640, 420), sb=z, sw=z, sc=z, d=(0, 0), dw=(0, 0)); focus(cam, 755, 330, 640 + 120 * (1 - k), 330)
    plate(cv, 'h7_sun', cam, 'b'); bl = ev(T, 65.0, 67.0); sp = bpt(cam, 755, 330)
    shade = ev(T, 65.6, 66.2) * (1 - ev(T, 67.4, 68.0))
    man = mk('m', 400, 730, .5, 1, 0.3, pose={'head': -16 * (1 - shade), 'aL': 8 + 110 * ev(T, 65.2, 65.9) * (1 - shade) + 118 * shade, 'fL': 140 * shade, 'aR': 8 + 110 * ev(T, 65.2, 65.9) * (1 - shade), 'fR': 0}, gain=1.05, shirt=SHIRTS[1], tint=(1.05, 1.0, 0.95), crouch=0.0)
    draw_items(cv, cam, [man], T)
    lb = LightBuf(); lb.glow(sp[0], sp[1], 90 * z, (255, 245, 220), 0.45 + 0.25 * bl); lb.glow(sp[0], sp[1], 420 * z, (255, 220, 150), 0.2 + 0.2 * bl); lb.apply(cv, blur=34)
    cv += 18 * bl * (0.6 + 0.4 * math.sin(T * 1.5)); vignette(cv, 0.25, 2.0); finish(cv, T, 137, 0.2, 18)


SG = [(68.65, 'm', SHIRTS[1], None, True), (69.4, 'j', SHIRTS[2], None, True), (70.15, 'g', SHIRTS[4], None, True), (70.9, 'm', SHIRTS[6], PANTS[3], True), (71.55, 's', None, None, True)]
SURF2 = dict(z=2.4, fx=720, fy=480, rise=None, door=68.2, outs=SG, cheer=(68.8, 69.6), dir=1, flash=True, shk=0.0)


def shot_glasses(cv, T): surface_shot(cv, T, SURF2)


def shot_squint(cv, T):   # 72.0 - 75.5 sunglasses, the eyes can't take the light
    k = seg(T, 71.9, 75.6); z = lerp(1.1, 1.2, k); cam = Cam(A=(640, 620), sb=z, sw=z, sc=z, d=(0, 0), dw=(0, 0)); focus(cam, 755, 330, 640, 300)
    plate(cv, 'h7_sun', cam, 'b'); cv[:] = cv * 0.45 + cv2.GaussianBlur(cv, (0, 0), 12) * 0.55
    lb = LightBuf(); sp = bpt(cam, 755, 330); lb.glow(sp[0], sp[1], 260, (255, 235, 190), 0.5); lb.apply(cv, blur=34)
    items = []
    for i, (x, ch, sh_, pa_) in enumerate(((330, 'j', SHIRTS[2], None), (640, 'm', SHIRTS[1], None), (950, 'g', SHIRTS[4], None))):
        sd = ev(T, 72.4 + 0.25 * i, 73.0 + 0.25 * i) * (1 - ev(T, 74.4 + 0.2 * i, 75.0 + 0.2 * i)) * (1 if i != 1 else 0.6)
        items.append(mk(ch, x, 1010, .66, 1 if i != 2 else -1, i * 1.3, pose={'head': -6 - 6 * sd + 3 * math.sin(T * 1.2 + i), 'aL': 4 + 114 * sd, 'fL': 140 * sd, 'aR': 4}, gain=1.0, shirt=sh_, pants=pa_, glasses=True, tint=(1.05, 1.0, 0.95), crouch=0.0))
    draw_g(cv, cam, items, T); cv += 20 * ev(T, 72.0, 73.0); vignette(cv, 0.3, 2.0); finish(cv, T, 138, 0.2, 14)


def shot_cycle(cv, T):   # 75.5 - 78.2 down and up again
    zz = 0.58; sc, ox, oy = depth_view(cv, T, 384, zz, 0.92); X = 688 * sc - ox; lb = LightBuf()
    yp = 160 + 525 * ev(T, 75.5, 76.5) if T < 76.7 else 685 - 525 * ev(T, 76.8, 78.0)
    Y = yp * sc - oy; cap_draw(cv, X, Y - 45, 0.18, gain=1.0)
    lb.glow(X, Y, 28, (120, 200, 255), 0.75); lb.glow(X, Y, 100, (70, 150, 240), 0.28)
    q = (X, 685 * sc - oy); lb.glow(q[0], q[1], 60, (110, 190, 255), 0.5); lb.glow(X, 160 * sc - oy, 50, (255, 235, 200), 0.3 * ev(T, 77.8, 78.2)); lb.apply(cv, blur=22)
    vignette(cv, 0.4, 2.0); finish(cv, T, 139, 0.5, 8)


ONCE = [dict(z=2.0, fx=688, fy=470, rise=(78.2, 78.8), door=78.9, outs=[(79.4, 'j', SHIRTS[2], None, True)], cheer=(79.5, 80.2), dir=1, hug=(79.5,), seed=4),
        dict(z=2.35, fx=640, fy=475, rise=(80.4, 80.9), door=81.0, outs=[(81.2, 'g', SHIRTS[4], None, True)], cheer=(81.3, 81.7), dir=-1, hug=(81.2,), seed=6),
        dict(z=2.7, fx=740, fy=480, rise=(81.7, 82.2), door=82.3, outs=[(82.6, 's', None, None, True)], cheer=(82.7, 83.1), dir=1, hug=(82.6,), seed=8)]


def shot_once1(cv, T): surface_shot(cv, T, ONCE[0])
def shot_once2(cv, T): surface_shot(cv, T, ONCE[1])
def shot_once3(cv, T): surface_shot(cv, T, ONCE[2])


_vt = []


def van_times():
    if not _vt:
        r = np.random.default_rng(23); n = len(GRID); order = list(r.permutation(n)); sched = [(83.3, 85.6, 11), (86.1, 86.7, 8), (87.6, 88.2, 7), (88.65, 89.4, n - 26)]; ts = {}; i = 0
        for a, b, c in sched:
            for j in range(c):
                if i < n: ts[order[i]] = a + (b - a) * j / max(1, c - 1); i += 1
        _vt.append(ts)
    return _vt[0]


def shot_fewer(cv, T):
    k = seg(T, 83.0, 89.7); ts = van_times(); cam = Cam(A=(640, 600), sb=lerp(1.0, 1.1, k), sw=lerp(1.0, 1.2, k), sc=lerp(1.0, 1.1, k), d=(0, 0), dw=(0, 0))
    dm = ev(T, 83.2, 89.0); chamber_bg(cv, T, cam, 0.58 - 0.12 * dm, lamps=0.65 - 0.25 * dm); items = []
    for i, c in enumerate(GRID):
        t_ = ts.get(i, 999.0); g = 1.0 - ev(T, t_, t_ + 0.5)
        if g <= 0.01 or (abs(c['x'] - 640) < 150 and c['gy'] > 640): continue
        items.append(dict(c, pose={'head': 4 * math.sin(T * 1.1 + i) - 4 * dm, 'aL': 4, 'aR': 4}, crouch=0.1, gain=0.8 * g, tint=CT, sway=0.3, hop=0))
    items.append(mk('u', 640, 722, .56, 1, 0.4, pose={'head': -6 + 3 * math.sin(T * 0.8), 'aL': 8, 'aR': 8}, gain=1.0, tint=(0.95, 1.0, 1.06), crouch=0.04))
    draw_items(cv, cam, items, T); ceiling_hole(cv, cam, 1.0, T, 640, 90, 80, cracks=True, light=0.8 * (1 - 0.4 * dm))
    puffs(cv, T, 83.0, 89.7, 8, (100, 0, 1080, 100), (110, 150, 190), seed=140, size=(30, 80), rise=(10, 40), life=2.0, alpha=0.1)
    veil(cv, T, 0.04 + 0.1 * dm); tone(cv, 1.0, 0, (0.95, 0.99, 1.05), 1.0); finish(cv, T, 140, 0.5 + 0.2 * dm, 14)


def shot_one(cv, T):   # 89.6 - 93.8 one man left, the one who led them from the start
    k = seg(T, 89.5, 93.9); cam = Cam(A=(640, 620), sb=lerp(1.0, 1.12, k), sw=lerp(1.0, 1.2, k), sc=lerp(1.0, 1.18, k), d=(0, 0), dw=(0, 0))
    chamber_bg(cv, T, cam, 0.5, lamps=0.45); pr = ev(T, 91.4, 92.6)
    man = mk('u', 640, 722, .6, 1, 0.4, pose={'head': 14 * math.sin(T * 0.9) * (1 - pr) - 8 * pr, 'aL': 8 + 8 * pr, 'aR': 8 + 8 * pr}, gain=1.0, tint=(0.95, 1.0, 1.06), crouch=0.04 * (1 - pr))
    draw_items(cv, cam, [man], T); ceiling_hole(cv, cam, 1.0, T, 640, 90, 80, cracks=True, light=0.9)
    puffs(cv, T, 89.5, 93.9, 8, (560, 0, 160, 400), (255, 240, 210), seed=141, size=(20, 50), rise=(30, 60), life=2.0, alpha=0.1)
    veil(cv, T, 0.08); finish(cv, T, 141, 0.65, 16)


def shot_name(cv, T):   # 93.8 - 95.2 close-up Luis Urzua
    k = seg(T, 93.7, 95.2); cam = Cam(A=(640, 620), sb=lerp(1.2, 1.3, k), sw=lerp(1.3, 1.5, k), sc=lerp(1.2, 1.3, k), d=(0, 0), dw=(0, 0)); cu_bg(cv, T, cam, 0.55)
    lb = LightBuf(); lb.glow(640, 120, 300, (255, 235, 205), 0.35 * ev(T, 93.8, 94.5)); lb.apply(cv, blur=36)
    draw_items(cv, cam, [mk('u', 640, 1090, .86, 1, 0.2, pose={'head': -6 + 3 * math.sin(T * 1.4), 'aL': 4, 'aR': 4}, gain=1.0, tint=(0.98, 1.0, 1.04), crouch=0.0)], T)
    vignette(cv, 0.5, 2.0); finish(cv, T, 142, 0.55, 14)


def shot_enter2(cv, T): enter_shot(cv, T, 95.1, 96.0, 96.9, 98.5, 99.8, 'u', seed=143, crowd=False)


def shot_last(cv, T):   # 99.8 - 104.0 the capsule climbs, the depths go dark
    zz = 0.8; p = ev(T, 99.9, 103.9); yp = lerp(670, 175, p); cyp = min(max(yp, 240), 768 - 192 / zz)
    sc, ox, oy = depth_view(cv, T, cyp, zz, 0.9); X = 688 * sc - ox; Y = yp * sc - oy; lb = LightBuf()
    q = (X, 685 * sc - oy); dk = ev(T, 100.4, 102.4); shade_ell(cv, q[0], q[1] - 6, 190 * zz * 1.6, 120 * zz * 1.6, 0.0 + 0.85 * dk)
    for j in range(1, 7): lb.glow(X, Y + 26 * j * zz, 16 * zz * (1 + 0.1 * j), (110, 190, 255), 0.35 * (1 - j / 7.0))
    cap_draw(cv, X, Y - 80, 0.27, gain=1.0); lb.glow(X, Y, 50, (120, 200, 255), 0.8); lb.glow(X, Y, 130, (70, 150, 240), 0.3)
    lb.glow(q[0], q[1], 80 * zz, (110, 190, 255), 0.45 * (1 - dk)); lb.apply(cv, blur=22)
    vignette(cv, 0.45 + 0.2 * dk, 2.0); finish(cv, T, 144, 0.55, 8)


SURF3 = dict(z=lambda T: lerp(2.0, 2.2, seg(T, 103.7, 105.9)), fx=688, fy=470, rise=(103.7, 104.3), door=104.4, outs=[(105.0, 'u', None, None, False)], cheer=(105.0, 105.6), dir=1, flash=True, shk=lambda T: 0.7 * P(T, 103.7, 104.3), steam=True, seed=11)


def shot_emerge(cv, T): surface_shot(cv, T, SURF3)


def fireworks(cv, T, t0, seed=5):
    r = np.random.default_rng(seed); lb = LightBuf()
    for b in range(9):
        tb = t0 + 0.35 * b + r.random() * 0.3; tt = T - tb
        if tt < 0 or tt > 1.6: continue
        cx = 120 + 1040 * r.random(); cy = 90 + 180 * r.random(); col = ((60, 60, 235), (240, 240, 240), (235, 120, 40), (60, 200, 255))[b % 4]
        for i in range(34):
            a = i / 34.0 * 2 * math.pi; sp = 90 + 70 * r.random(); x = cx + math.cos(a) * sp * tt; y = cy + math.sin(a) * sp * tt + 80 * tt * tt; f = max(0.0, 1 - tt / 1.6)
            cv2.circle(cv, (int(x), int(y)), 2, tuple(float(c * f) for c in col), -1, cv2.LINE_AA)
        lb.glow(cx, cy, 90 * (1 + tt), tuple(int(c) for c in col), 0.3 * max(0.0, 1 - tt / 0.6))
    lb.apply(cv, blur=26)


def shot_wide33(cv, T):   # 105.8 - 108.7 thirty-three men, all alive
    k = seg(T, 105.7, 108.8); cam = site_cam(lerp(1.5, 1.0, ev(T, 105.7, 108.8)), 688, 640, 640, 480 + 100 * (1 - k)); site_bg(cv, T, cam, 1.0)
    items = []; r = np.random.default_rng(30)
    for row, (py, n, x0, x1) in enumerate(((655, 16, 120, 1260), (705, 17, 70, 1300))):
        for i in range(n):
            px = x0 + (x1 - x0) * i / (n - 1); idx = len(items); up = ev(T, 105.9 + 0.012 * idx, 106.4 + 0.012 * idx); w_ = math.sin(2 * math.pi * 2.0 * T + idx * 0.9)
            x, gy = world_of(px, py); ch = 'u' if idx == 16 else ('j' if idx == 3 else ('g' if idx == 20 else ('s' if idx == 9 else 'm')))
            items.append(mk(ch, x, gy, site_sc(py) * 1.0, 1 if idx % 2 else -1, idx * 1.3, pose={'aL': 6 + (132 + 6 * w_) * up, 'aR': 6 + (128 - 6 * w_) * up, 'head': -8 * up + 2 * math.sin(T * 2 + idx)}, gain=0.96, shirt=SHIRTS[(idx * 3 + 1) % 10] if ch == 'm' else None, pants=PANTS[(idx * 7 + 2) % 10] if ch == 'm' else None, hop=abs(w_) * 14 * up, mouth=speak(T, idx, .9) * up))
    draw_items(cv, cam, items, T); fireworks(cv, T, 106.0, 7); vignette(cv, 0.35, 2.0); motes(cv, T, 63, 26, 0.5, (230, 225, 200))


def tally7(i):
    g, j = divmod(i, 5); row, c = divmod(g, 7); x0 = 130 + 180 * c; y0 = 190 + 280 * row; r = np.random.default_rng(500 + i)
    if j < 4: x = x0 + j * 30; return [(x + r.normal(0, 2), y0 + r.normal(0, 3)), (x + 3 + r.normal(0, 2), y0 + 150 + r.normal(0, 3))]
    return [(x0 - 14, y0 + 118 + r.normal(0, 3)), (x0 + 3 * 30 + 12, y0 + 28 + r.normal(0, 3))]


def shot_days69(cv, T):   # 108.7 - end : 69 days, the marks on the rock
    k = seg(T, 108.6, D7); z = lerp(1.0, 1.06, k); cam = Cam(A=(640, 380), sb=z, sw=z, sc=z, d=(0, 0), dw=(0, 0))
    plate(cv, 'h5_wall', cam, 'b', gain=0.75)
    lb = LightBuf(); q = bpt(cam, 160, 130); lb.glow(q[0], q[1], 300, (60, 130, 230), 0.12); lb.apply(cv, blur=30)
    for i in range(69):
        t0 = 108.7 + 0.033 * i; e = ev(T, t0, t0 + 0.12)
        if e <= 0: continue
        (xa, ya), (xb, yb) = tally7(i); pa = bpt(cam, xa, ya); pb = bpt(cam, xa + (xb - xa) * e, ya + (yb - ya) * e); w_ = max(2, int(5 * cam.sb))
        cv2.line(cv, (int(pa[0] + 2), int(pa[1] + 3)), (int(pb[0] + 2), int(pb[1] + 3)), (10.0, 14.0, 22.0), w_ + 2, cv2.LINE_AA)
        cv2.line(cv, (int(pa[0]), int(pa[1])), (int(pb[0]), int(pb[1])), (215.0, 232.0, 240.0), w_, cv2.LINE_AA)
    al = ev(T, 109.6, 111.0); lb = LightBuf(); lb.glow(640, 380, 560, (80, 170, 255), 0.65 * al); lb.glow(640, 380, 200, (200, 235, 255), 0.4 * al); lb.apply(cv, blur=44)
    puffs(cv, T, 108.6, D7, 8, (100, 0, 1080, 500), (110, 150, 190), seed=145, size=(40, 90), rise=(10, 30), life=2.4, alpha=0.10); finish(cv, T, 145, 0.55, 22)


SHOTS7 = [('rigs', 0.0, 2.3, shot_rigs7, 0.0), ('meters', 2.3, 5.2, shot_meters, 0.3), ('hard', 5.2, 8.1, shot_hard, 0.3), ('long', 8.1, 9.3, shot_long, 0.3), ('danger', 9.3, 12.4, shot_danger7, 0.4),
          ('reach', 12.4, 14.0, shot_reach, 0.3), ('break', 14.0, 16.3, shot_break7, 0.3), ('way', 16.3, 19.1, shot_way, 0.4), ('problem', 19.1, 20.8, shot_problem, 0.3), ('narrow', 20.8, 24.0, shot_narrow, 0.4),
          ('draft', 24.0, 27.7, shot_draft, 0.4), ('reveal', 27.7, 31.95, shot_reveal, 0.5), ('enter', 31.95, 34.3, shot_enter, 0.3), ('far', 34.3, 36.0, shot_far, 0.3), ('alone', 36.0, 38.7, shot_alone, 0.4),
          ('below', 38.7, 40.6, shot_below, 0.4), ('above', 40.6, 42.6, shot_above, 0.3), ('night', 42.6, 46.0, shot_night, 0.5), ('enter1', 46.0, 51.2, shot_enter1, 0.4), ('rise', 51.2, 54.6, shot_rise, 0.4),
          ('surface1', 54.6, 60.0, shot_surface1, 0.4), ('crowd', 60.0, 62.2, shot_crowd, 0.3), ('cams', 62.2, 62.9, shot_cams, 0.1), ('families', 62.9, 64.7, shot_families, 0.2), ('sun', 64.7, 68.5, shot_sun, 0.4),
          ('glasses', 68.5, 72.0, shot_glasses, 0.4), ('squint', 72.0, 75.5, shot_squint, 0.3), ('cycle', 75.5, 78.2, shot_cycle, 0.3), ('once1', 78.2, 80.4, shot_once1, 0.1), ('once2', 80.4, 81.7, shot_once2, 0.1),
          ('once3', 81.7, 83.1, shot_once3, 0.1), ('fewer', 83.1, 89.6, shot_fewer, 0.4), ('one', 89.6, 93.8, shot_one, 0.4), ('name', 93.8, 95.1, shot_name, 0.2), ('enter2', 95.1, 99.8, shot_enter2, 0.3),
          ('last', 99.8, 103.9, shot_last, 0.3), ('emerge', 103.9, 105.8, shot_emerge, 0.3), ('wide33', 105.8, 108.7, shot_wide33, 0.4), ('days69', 108.7, D7, shot_days69, 0.4)]


class Part7:
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTS7):
            hi = t1 + (SHOTS7[i + 1][4] / 2 if i + 1 < len(SHOTS7) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTS7) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
