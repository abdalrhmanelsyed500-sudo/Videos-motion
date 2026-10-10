"""Prosperi video PART 3 (Arabic, 86 s): April 14 1994, stage four - the sandstorm hits, hours hiding, calm, the course markers have vanished, he climbs a dune and sees only sand,
he thinks he can get back easily and keeps running - farther from where the rescuers will search. Same oil layered-puppet system. NO face mark, NO captions, NO music."""
from pros2_scenes import *
import pros2_scenes as P2

DP3 = 86.0
SANDC = np.array(SAND, np.float32)
_img = {}


def img(name):
    if name not in _img: _img[name] = cv2.imread(f'assets/layers/{name}.jpg').astype(np.float32)
    return _img[name]


def fog(cv, a, col=None):
    if a <= 0.01: return
    c = SANDC * 1.05 if col is None else np.array(col, np.float32); cv *= (1 - a); cv += c * a


def mound(cv, x, y, w, h, a=0.92):
    if w < 4 or h < 3: return
    x0, x1 = int(max(0, x - w - 20)), int(min(W, x + w + 20)); y0, y1 = int(max(0, y - h * 2 - 20)), H
    if x1 <= x0 or y1 <= y0: return
    roi = cv[y0:y1, x0:x1]; col = np.zeros_like(roi); m = np.zeros(roi.shape[:2], np.float32)
    c = (int(x - x0), int(y - y0)); cv2.ellipse(col, c, (int(w), int(h)), 0, 180, 360, (84.0, 140.0, 190.0), -1, cv2.LINE_AA); cv2.ellipse(m, c, (int(w), int(h)), 0, 180, 360, 1.0, -1, cv2.LINE_AA)
    cv2.rectangle(col, (c[0] - int(w), c[1]), (c[0] + int(w), y1 - y0), (84.0, 140.0, 190.0), -1); cv2.rectangle(m, (c[0] - int(w), c[1]), (c[0] + int(w), y1 - y0), 1.0, -1)
    cv2.ellipse(col, (c[0] + int(w * 0.15), c[1] - 2), (int(w * 0.8), int(h * 0.7)), 0, 180, 360, (104.0, 170.0, 225.0), -1, cv2.LINE_AA)
    cv2.ellipse(m, (c[0] + int(w * 0.15), c[1] - 2), (int(w * 0.8), int(h * 0.7)), 0, 180, 360, 1.0, -1, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 2.5)[..., None] * a; col = cv2.GaussianBlur(col, (0, 0), 2.0)
    roi[:] = roi * (1 - m) + col * m


def bubble(cv, cx, cy, r, plate, crop, a=1.0):
    """thought bubble: circular soft-edged window showing a crop (x0,y0,x1,y1) of a plate, with little trailing circles toward (cx-r*0.9, cy+r*1.4)."""
    if a <= 0.02: return
    r = int(r); x0, y0, x1, y1 = crop; im = cv2.resize(img(plate)[y0:y1, x0:x1], (2 * r, 2 * r), interpolation=cv2.INTER_AREA)
    m = np.zeros((2 * r, 2 * r), np.float32); cv2.circle(m, (r, r), r - 4, 1.0, -1, cv2.LINE_AA); m = cv2.GaussianBlur(m, (0, 0), 3)[..., None] * a
    xa, ya = int(cx - r), int(cy - r)
    if xa < 0 or ya < 0 or xa + 2 * r > W or ya + 2 * r > H: return
    roi = cv[ya:ya + 2 * r, xa:xa + 2 * r]; roi[:] = roi * (1 - m) + im * 0.95 * m
    cv2.circle(cv, (int(cx), int(cy)), int(r - 3), (210.0, 225.0, 235.0), 3, cv2.LINE_AA)
    for k, (dx, dy, rr) in enumerate(((-0.78, 1.25, 0.16), (-0.9, 1.6, 0.1), (-0.98, 1.88, 0.06))):
        cv2.circle(cv, (int(cx + dx * r), int(cy + dy * r)), max(2, int(rr * r)), (225.0, 235.0, 242.0), -1, cv2.LINE_AA)


def prints(cv, wc, pts, a=1.0, col=(40.0, 78.0, 128.0)):
    if a <= 0.02: return
    ov = cv.copy()
    for (X, Y, r_) in pts:
        x, y = wc.pt(X, Y); rr = max(1.2, r_ * wc.z); cv2.ellipse(ov, (int(x), int(y)), (int(rr * 1.4), int(max(1, rr * 0.6))), 0, 0, 360, col, -1, cv2.LINE_AA)
    cv[:] = cv * (1 - a) + ov * a


# ------------------------------------------------------------------ 1. "April 14 1994, the fourth stage" (0 - 5.7): the map, the first four stage dots, the fourth pulses
def shot_map4(cv, T):
    wc = cam(T, 0, 5.9, (700, 470, 1.1), (900, 470, 1.25), 'pr_map', cv=cv)
    route_overlay(cv, wc, min(T, 2.6), 0.3, 4.13)
    x, y = wc.pt(*ROUTE[3])
    for j in range(2):
        a = clamp((T - 3.9 - 0.5 * j) / 1.3)
        if 0 < a < 1: ring(cv, x, y, 16 + 90 * a * wc.z, (1 - a) * 0.9)
    tone(cv, 1.04, 0, (0.98, 1.0, 1.02), 1.0); fin(cv, T, 501, 0.45, True, 14)


# ------------------------------------------------------------------ 2. running in the dunes, the wind begins (5.7 - 10.0)
def shot_run3(cv, T):
    wc = cam(T, 5.5, 10.2, (700, 336, 1.1), (1000, 336, 1.1), 'pr_empty', cv=cv)
    items = []
    for i in range(4):
        X = jog(260 + 150 * i, 900 + 150 * i, 5.7, 10.0, T); Y = 600 + 26 * ((i * 5) % 3) - 8 * i
        items.append(person(wc, 'p' if i == 1 else 'r', X, Y, 1.1, 1, i * 1.7, walk=1.0, pose=RUN(T + i, 40, 28, 8.0, 8.0, 4 * math.sin(T * 2 + i) * ev(T, 8.4, 9.2)), shirt=RSH[i % 6] if i != 1 else None))
    draw_people(cv, items, T)
    w_ = ev(T, 7.8, 10.0); sand(cv, T, 0.22 * w_, 53, -1.0, 0.4)
    puffs(cv, T, 8.2, 10.2, 18, (200, 560, 1000, 90), SAND, seed=54, size=(40, 90), rise=(2, 14), life=1.6, alpha=0.22 * w_, wind=(-150, 0))
    tone(cv, 1.0, 0, (1.0 - 0.06 * w_, 1.0 - 0.05 * w_, 1.0), 1.0); fin(cv, T, 502, 0.35 + 0.1 * w_)


# ------------------------------------------------------------------ 3. the sand moves unnaturally around him (10.0 - 12.1)
def shot_ground(cv, T):
    wc = cam(T, 9.8, 12.3, (800, 430, 1.35), (760, 450, 1.55), 'pr_empty', 0.92, cv=cv)
    dn = ev(T, 10.0, 10.6) * (1 - ev(T, 11.2, 11.7))
    draw_people(cv, [person(wc, 'p', 790, 640, 1.2, 1, 0.3, pose={'aL': 8, 'aR': 8, 'lean': 8 * dn + 3, 'head': 24 * dn - 10 * (1 - dn) * ev(T, 11.3, 11.8), 'hs': 1.0})], T)
    puffs(cv, T, 9.9, 12.3, 34, (0, 600, 1280, 100), SAND, seed=55, size=(50, 120), rise=(0, 10), spread=(40, 100), life=1.2, alpha=0.3, wind=(-320, 0))
    sand(cv, T, 0.22, 56, -1.0, 0.4); tone(cv, 1.0, 0, (0.96, 0.98, 1.0), 1.0); fin(cv, T, 503, 0.45)


# ------------------------------------------------------------------ 4. the wind turns into a strong sandstorm (12.1 - 15.0)
def shot_arrive(cv, T):
    wc = cam(T, 12.0, 15.2, (900, 336, 1.1), (760, 336, 1.4), 'pr_storm', cv=cv)
    a = ev(T, 12.1, 14.8); items = []
    for i in range(4):
        X = 500 + 150 * i + 70 * (T - 12.1); Y = 600 + 20 * (i % 2)
        items.append(person(wc, 'p' if i == 2 else 'r', X, Y, 1.1, 1, i * 1.3, walk=1.0, pose=RUN(T + i, 30, 20, 8.0, 14 + 10 * a, 6 * a), shirt=RSH[i % 6] if i != 2 else None))
    draw_people(cv, items, T); sand(cv, T, 0.28 + 0.5 * a, 57, -1.0, 0.8); fin(cv, T, 504, 0.5, False)


# ------------------------------------------------------------------ 5. the air is full of sand, he cannot see the road (15.0 - 19.5)
def shot_noroad3(cv, T):
    wc = cam(T, 14.8, 19.7, (760, 360, 1.7), (740, 380, 2.0), 'pr_storm', 0.85, cv=cv)
    sh = ev(T, 15.2, 15.9); sc = math.sin((T - 16.5) * 2.2) * 20 * ev(T, 16.3, 16.8)
    draw_items(cv, IDM, [pc('p', 640, 710, 0.66, 1, 0.3, sway=1.6, pose={'aL': 8 + 110 * sh, 'fL': 140 * sh, 'aR': 8 + 20 * sh, 'head': -6 * sh + sc, 'lean': 6 * sh})], T)
    sand(cv, T, 0.62 + 0.25 * ev(T, 16.0, 18.5), 58, -1.0, 0.9); fin(cv, T, 505, 0.55, False)


# ------------------------------------------------------------------ 6. "everything vanished behind a thick yellow wall" (19.5 - 22.4)
def shot_wall3(cv, T):
    k = seg(T, 19.4, 22.5); wc = WC(760, 336, lerp(1.9, 1.15, ease_out(k))); wc.draw(cv, 'pr_storm', 0.8)
    fadeo = ev(T, 19.8, 22.2)
    items = [person(wc, 'p', 760, 640, 1.0, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 8 * math.sin(T * 3), 'lean': 10}, gain=0.97)]
    for i, X in enumerate((560, 960, 1100)):
        if T < 20.2 + 0.5 * i: items.append(person(wc, 'r', X, 610, 1.0, 1, i, pose={'aL': 14, 'aR': 14, 'lean': 10}, shirt=RSH[(i + 2) % 6], gain=0.9))
    draw_people(cv, items, T); sand(cv, T, 0.85, 59, -1.0, 1.0); fog(cv, 0.62 * fadeo); fin(cv, T, 506, 0.55, False)


# ------------------------------------------------------------------ 7. "even finding the direction became very hard" (22.4 - 24.7)
def shot_dir(cv, T):
    wc = cam(T, 22.2, 24.9, (760, 360, 1.8), (740, 360, 1.7), 'pr_storm', 0.7, cv=cv)
    sw = math.sin((T - 22.4) * 2.4)
    draw_items(cv, IDM, [pc('p', 640, 700, 0.6, 1 if sw > -0.2 else -1, 0.3, gain=0.8, sway=1.8, pose={'aL': 70 + 20 * math.sin(T * 3), 'aR': 60 + 20 * math.cos(T * 3), 'fL': 20, 'fR': 20, 'head': 28 * sw, 'lean': 6 * sw})], T)
    sand(cv, T, 0.8, 60, -1.0, 1.0); fog(cv, 0.5); fin(cv, T, 507, 0.55, False)


# ------------------------------------------------------------------ 8. "he tried to shelter" (24.7 - 29.3): he crouches, back to the wind, arms over his head; sand heaps up
def shot_shelter(cv, T):
    wc = cam(T, 24.5, 29.5, (740, 380, 1.9), (760, 400, 2.1), 'pr_storm', 0.7, cv=cv)
    c = ev(T, 24.9, 25.8); g = math.sin(T * 14) * 2
    draw_items(cv, IDM, [pc('p', 640, 730 + 190 * c, 0.66, -1, 0.3, gain=0.85, sway=2.0, pose={'aL': 8 + 110 * c, 'fL': 140 * c, 'aR': 8 + 110 * c, 'fR': 140 * c, 'head': 16 * c + g * c, 'lean': 26 * c})], T)
    mound(cv, 640, 700, 60 + 170 * ev(T, 25.5, 29.4), 8 + 50 * ev(T, 25.5, 29.4), 0.9)
    sand(cv, T, 0.82, 61, -1.0, 1.0); fog(cv, 0.35); fin(cv, T, 508, 0.55, False)


# ------------------------------------------------------------------ 9. "the storm kept on for hours; nothing clear to rely on" (29.3 - 34.3)
def shot_hours(cv, T):
    wc = cam(T, 29.1, 34.5, (760, 400, 2.1), (760, 400, 1.7), 'pr_storm', 0.7, cv=cv)
    lift = ev(T, 32.9, 33.6)
    draw_items(cv, IDM, [pc('p', 640, 920 - 120 * lift, 0.66, -1, 0.3, gain=0.85, sway=1.2, pose={'aL': 118 * (1 - lift) + 8, 'fL': 140 * (1 - lift), 'aR': 118 * (1 - lift) + 8, 'fR': 140 * (1 - lift), 'head': 16 - 26 * lift, 'lean': 26 - 14 * lift})], T)
    mound(cv, 640, 700 - 20 * lift, 220 + 40 * seg(T, 29.3, 34.3), 58 + 12 * seg(T, 29.3, 34.3), 0.92)
    sand(cv, T, 0.75, 62, -1.0, 1.0); fog(cv, 0.35 + 0.1 * math.sin(T * 1.1)); fin(cv, T, 509, 0.55, False)


# ------------------------------------------------------------------ 10. "after about seven or eight hours": time-lapse, the sun crosses the dusty sky (34.3 - 38.0)
def shot_sunarc(cv, T):
    k = seg(T, 34.3, 38.0); wc = WC(800, 330, lerp(1.0, 1.15, k)); wc.draw(cv, 'pr_storm', 0.8)
    draw_people(cv, [person(wc, 'p', 700, 690, 1.0, -1, 0.3, pose={'aL': 118, 'fL': 140, 'aR': 118, 'fR': 140, 'head': 16 * (1 - ev(T, 36.5, 37.4)), 'lean': 26}, gain=0.9)], T)
    x, y = wc.pt(700, 640); mound(cv, x, y - 4, 90, 24, 0.9)
    sand(cv, T, 0.55 * (1 - 0.7 * ev(T, 36.0, 38.0)), 63, -1.0, 0.8)
    lb = LightBuf(); sx = lerp(80, 1200, k); sy = 300 - 210 * math.sin(math.pi * k); lb.glow(sx, sy, 90, (200, 235, 255), 0.7); lb.glow(sx, sy, 260, (110, 190, 255), 0.35); lb.apply(cv, blur=36)
    tone(cv, 1.0, 0, (1.0 - 0.1 * k, 0.99 - 0.04 * k, 1.02 - 0.04 * k) if k > 0.6 else (1, 1, 1), 1.0); fin(cv, T, 510, 0.5, False)


# ------------------------------------------------------------------ 11. the storm finally calms, he stands and shakes off the sand (38.0 - 40.5)
def shot_calm3(cv, T):
    wc = cam(T, 37.8, 40.7, (800, 336, 1.3), (790, 336, 1.15), 'pr_empty', cv=cv)
    up = ev(T, 38.1, 39.0); shake = math.sin(T * 16) * P(T, 39.0, 40.0)
    draw_people(cv, [person(wc, 'p', 790, 640 + 120 * (1 - up), 1.25, 1, 0.3, sway=1.0, pose={'aL': 8 + 118 * (1 - up) + 30 * shake, 'fL': 140 * (1 - up), 'aR': 8 + 118 * (1 - up) - 30 * shake, 'fR': 140 * (1 - up), 'head': 16 * (1 - up) + 8 * shake, 'lean': 26 * (1 - up)})], T)
    xm, ym = wc.pt(790, 640); mound(cv, xm, ym - 6 + 20 * up, 110 * (1 - up) + 30, 30 * (1 - up) + 4, 0.9 * (1 - up) + 0.0)
    xx, yy = wc.pt(790, 500); puffs(cv, T, 38.4, 40.2, 22, (xx - 70, yy - 40, 140, 220), SAND, seed=64, size=(26, 56), rise=(-10, 26), life=1.0, alpha=0.35, wind=(-60, 40))
    sand(cv, T, 0.35 * (1 - ev(T, 38.0, 40.0)), 65, -1.0, 0.6); fin(cv, T, 511, 0.35)


# ------------------------------------------------------------------ 12. "and the scene appeared again... but here was the surprise" (40.5 - 42.6)
def shot_surprise(cv, T):
    wc = cam(T, 40.3, 42.8, (790, 336, 1.2), (790, 336, 1.45), 'pr_empty', cv=cv)
    look = math.sin((T - 40.6) * 2.6) * 26
    draw_people(cv, [person(wc, 'p', 790, 640, 1.3, 1, 0.3, pose={'aL': 8 + 40 * ev(T, 41.2, 41.8), 'aR': 8 + 40 * ev(T, 41.2, 41.8), 'fL': 40 * ev(T, 41.2, 41.8), 'fR': 40 * ev(T, 41.2, 41.8), 'head': look})], T)
    cv[:] = heat_haze(cv, T, 1.2, 0.045, 2.2, 300, 560); fin(cv, T, 512, 0.4)


# ------------------------------------------------------------------ 13. "the signs that marked the race route vanished" (42.6 - 48.5): the row of flags is buried and fades
def shot_flags3(cv, T):
    wc = cam(T, 42.4, 48.7, (560, 336, 1.15), (600, 336, 1.15), 'pr_empty', cv=cv)
    fa = 1.0 - ev(T, 45.6, 48.2); buried = ev(T, 43.0, 45.4)
    flags_far(cv, wc, T, 70, 12, fa * (1.0 - 0.2 * buried))
    point = ev(T, 44.0, 44.8) * (1 - ev(T, 47.0, 47.6))
    draw_people(cv, [person(wc, 'p', 900, 640, 1.25, 1, 0.3, pose={'aL': 8 + 70 * point, 'fL': 25 * point, 'aR': 8, 'head': -20 * point + 8 * math.sin((T - 47.6) * 2.5) * ev(T, 47.6, 48.0)})], T)
    puffs(cv, T, 43.2, 48.4, 22, (80, 460, 700, 90), SAND, seed=66, size=(40, 90), rise=(2, 18), life=1.6, alpha=0.28, wind=(-70, 0))
    cv[:] = heat_haze(cv, T, 1.2, 0.045, 2.2, 300, 560); fin(cv, T, 513, 0.38)


# ------------------------------------------------------------------ 14. "the racers' tracks were no longer clear" (48.5 - 51.2)
TRK = [(620 + 26 * i, 590 + 5 * math.sin(i * 1.3), 12.0) for i in range(22)]


def shot_tracks(cv, T):
    wc = cam(T, 48.3, 51.4, (840, 400, 1.4), (900, 400, 1.4), 'pr_empty', cv=cv)
    prints(cv, wc, TRK, 0.9 * (1 - ev(T, 49.3, 51.0)))
    draw_people(cv, [person(wc, 'p', 1180, 605, 1.2, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 22 * ev(T, 48.8, 49.4) * (1 - ev(T, 50.2, 50.8)), 'lean': 6 * ev(T, 48.8, 49.4)})], T)
    puffs(cv, T, 48.5, 51.3, 30, (200, 610, 900, 50), SAND, seed=67, size=(50, 110), rise=(0, 8), life=1.3, alpha=0.3, wind=(-210, 0))
    fin(cv, T, 514, 0.4)


# ------------------------------------------------------------------ 15. "even the shape of the land itself changed" (51.2 - 54.5): two dune plates dissolve into each other
def shot_terrain(cv, T):
    k = seg(T, 51.0, 54.7); wc = WC(lerp(980, 900, k), 336, 1.0); wc.draw(cv, 'pr_empty')
    b = np.zeros_like(cv); wc.draw(b, 'pr_empty'); b[:] = cv2.flip(b, 1); a = ev(T, 51.8, 53.8); cv *= (1 - a); cv += b * a
    cv[:] = heat_haze(cv, T, 2.8 * math.sin(math.pi * clamp((T - 51.4) / 3.2)) + 0.6, 0.05, 3.0, 250, 620)
    draw_people(cv, [person(wc, 'p', 940, 620, 1.1, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 24 * math.sin((T - 51.4) * 1.5)})], T)
    fin(cv, T, 515, 0.4)


# ------------------------------------------------------------------ 16. he climbs a high dune (54.5 - 58.0)
def shot_climb(cv, T):
    wc = cam(T, 54.3, 58.2, (720, 380, 1.15), (560, 340, 1.25), 'pr_empty', cv=cv)
    X = jog(980, 520, 54.6, 57.9, T); Y = jog(650, 480, 54.6, 57.9, T)
    draw_people(cv, [person(wc, 'p', X, Y, 1.25, 1, 0.3, walk=1.0, pose={'aL': 20, 'aR': 20, 'lean': 16, 'head': 4})], T)
    xx, yy = wc.pt(X, Y + 6); puffs(cv, T, 54.6, 58.0, 18, (xx - 70, yy - 8, 70, 12), SAND, seed=68, size=(22, 46), rise=(8, 24), life=1.0, alpha=0.3, wind=(-60, 0))
    fin(cv, T, 516, 0.35)


# ------------------------------------------------------------------ 17. on the crest he searches with his eyes for any familiar sign (58.0 - 60.6)
def shot_scan(cv, T):
    wc = cam(T, 57.8, 60.8, (900, 380, 1.8), (700, 380, 1.8), 'pr_empty', cv=cv)
    sh = ev(T, 58.2, 58.8); sw = math.sin((T - 58.8) * 2.2) * 32 * sh
    draw_items(cv, IDM, [pc('p', 640, 700, 0.62, 1, 0.3, pose={'aL': 8 + 110 * sh, 'fL': 140 * sh, 'aR': 8, 'head': sw})], T)
    cv[:] = heat_haze(cv, T, 1.2, 0.045, 2.2, 300, 560); fin(cv, T, 517, 0.45)


# ------------------------------------------------------------------ 18. "he saw nothing but sand in every direction" (60.6 - 64.5): pull-back, he becomes tiny
def shot_sea(cv, T):
    k = seg(T, 60.4, 64.7); wc = WC(lerp(620, 940, k), 336, lerp(1.9, 1.0, ease_out(k))); wc.draw(cv, 'pr_empty')
    draw_people(cv, [person(wc, 'p', 940, 590, 0.8, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 36 * math.sin((T - 60.6) * 1.4)})], T)
    cv[:] = heat_haze(cv, T, 1.2, 0.045, 2.2, 300, 560); tone(cv, 1.0, 0, (0.96, 1.0, 1.04), 1.0); fin(cv, T, 518, 0.5)


# ------------------------------------------------------------------ 19. "he did not grasp the size of the problem at once" (64.5 - 68.0)
def shot_think(cv, T):
    wc = cam(T, 64.3, 68.2, (800, 400, 1.9), (820, 400, 1.75), 'pr_empty', cv=cv)
    sh = ev(T, 65.6, 66.4) * (1 - ev(T, 67.0, 67.6))
    draw_items(cv, IDM, [pc('p', 640, 700, 0.62, 1, 0.3, pose={'aL': 8 + 52 * sh, 'fL': 70 * sh, 'aR': 8 + 52 * sh, 'fR': 70 * sh, 'head': 14 * math.sin((T - 64.6) * 1.2) + 10 * sh})], T)
    fin(cv, T, 519, 0.45)


# ------------------------------------------------------------------ 20. "he thought he had only strayed a little and could easily return" (68.0 - 71.4): a thought bubble of the start line
def shot_bubble(cv, T):
    wc = cam(T, 67.8, 71.6, (800, 336, 1.25), (800, 336, 1.15), 'pr_empty', cv=cv)
    a = ev(T, 68.3, 69.0)
    draw_people(cv, [person(wc, 'p', 640, 640, 1.3, -1, 0.3, pose={'aL': 8, 'aR': 8 + 30 * a, 'head': 8 * math.sin(T * 1.5)})], T)
    bubble(cv, 840, 210, 170 * (0.6 + 0.4 * a), 'pr_race', (40, 250, 640, 650), a)
    fin(cv, T, 520, 0.4)


# ------------------------------------------------------------------ 21. "he decided to keep going: a long-distance athlete" (71.4 - 76.5)
def shot_run2(cv, T):
    wc = cam(T, 71.2, 76.7, (700, 336, 1.2), (1100, 336, 1.2), 'pr_empty', cv=cv)
    st = ev(T, 71.8, 72.6); X = 640 + 40 * st + jog(0, 640, 72.4, 76.4, T)
    draw_people(cv, [person(wc, 'p', X, 640, 1.25, 1, 0.3, walk=st, pose={'aL': 8 + (32 + 30 * math.sin(T * 9)) * st, 'aR': 8 + (32 - 30 * math.sin(T * 9)) * st, 'fL': -55 * st, 'fR': -55 * st, 'lean': 8 * st})], T)
    xx, yy = wc.pt(X, 650); puffs(cv, T, 72.4, 76.5, 22, (xx - 150, yy - 8, 130, 14), SAND, seed=69, size=(26, 56), rise=(8, 24), life=1.0, alpha=0.3, wind=(-110, 0))
    tone(cv, 1.0, 0, (1.0, 0.98, 0.95), 1.0); fin(cv, T, 521, 0.35)


# ------------------------------------------------------------------ 22. "each step took him farther from where the rescuers would search" (76.5 - 80.8): pull-back with a long trail of footprints
def shot_away(cv, T):
    k = seg(T, 76.4, 81.0); z = lerp(1.4, 1.0, ease_out(k)); wc = WC(lerp(1150, 800, k), 336, z); wc.draw(cv, 'pr_empty', 0.9)
    Xm = 1000.0; Ym = 590.0; pts = []
    for i in range(46):
        f = (i + 1) / 46.0
        if f > ev(T, 76.8, 80.0): break
        pts.append((lerp(Xm - 30, 120.0, f ** 0.9), lerp(Ym + 12, 455.0, f ** 0.9) + 4 * math.sin(i * 1.7), max(2.5, 12 * (1 - f))))
    prints(cv, wc, pts, 1.0, (28.0, 60.0, 105.0))
    draw_people(cv, [person(wc, 'p', Xm, Ym, 0.8, 1, 0.3, walk=1.0, pose=RUN(T, 36, 24, 8.0, 8.0))], T)
    tone(cv, 1.0, 0, (0.9, 0.95, 1.03), 1.0); fin(cv, T, 522, 0.5)


# ------------------------------------------------------------------ 23. the map again: the rescue search area vs. the path he keeps walking (80.8 - end)
PATHM = [(1110, 468), (1180, 430), (1260, 392), (1340, 350), (1420, 300), (1500, 250), (1560, 205)]


def shot_map5(cv, T):
    k = seg(T, 80.6, DP3); wc = WC(lerp(980, 900, k), 336, lerp(1.05, 1.0, k)); wc.draw(cv, 'pr_map')
    route_overlay(cv, wc, 99.0, 0, 1)
    sx, sy = wc.pt(*ROUTE[3]); rr = 190 * wc.s * (1 + 0.04 * math.sin(T * 3))
    ov = cv.copy(); cv2.ellipse(ov, (int(sx), int(sy)), (int(rr), int(rr * 0.62)), 0, 0, 360, (45.0, 55.0, 200.0), -1, cv2.LINE_AA); cv[:] = cv * 0.82 + ov * 0.18 * ev(T, 81.0, 82.0)
    cv2.ellipse(cv, (int(sx), int(sy)), (int(rr), int(rr * 0.62)), 0, 0, 360, (35.0, 40.0, 190.0), 3, cv2.LINE_AA)
    f = ev(T, 82.0, 85.4) * (len(PATHM) - 1); n = int(f); head = None
    for i in range(len(PATHM) - 1):
        if i > n: break
        a = PATHM[i]; b = PATHM[i + 1]; fr = 1.0 if i < n else f - n
        for j in range(8):
            if j / 8.0 > fr: break
            p0 = (lerp(a[0], b[0], j / 8.0), lerp(a[1], b[1], j / 8.0)); p1 = (lerp(a[0], b[0], (j + .55) / 8.0), lerp(a[1], b[1], (j + .55) / 8.0))
            x0, y0 = wc.pt(*p0); x1, y1 = wc.pt(*p1); cv2.line(cv, (int(x0), int(y0)), (int(x1), int(y1)), (20.0, 20.0, 150.0), max(4, int(6 * wc.z)), cv2.LINE_AA); head = (x1, y1)
    if head is not None and T > 82.0: pin(cv, head[0], head[1], 0.9 * wc.z, 1.0)
    tone(cv, 1.04, 0, (0.98, 1.0, 1.02), 1.0); fin(cv, T, 523, 0.5, True, 12)


SHOTS3 = [('map4', 0.0, 5.7, shot_map4, 0.0), ('run3', 5.7, 10.0, shot_run3, 0.3), ('ground', 10.0, 12.1, shot_ground, 0.3), ('arrive', 12.1, 15.0, shot_arrive, 0.3), ('noroad3', 15.0, 19.5, shot_noroad3, 0.4),
          ('wall3', 19.5, 22.4, shot_wall3, 0.4), ('dir', 22.4, 24.7, shot_dir, 0.3), ('shelter', 24.7, 29.3, shot_shelter, 0.4), ('hours', 29.3, 34.3, shot_hours, 0.3), ('sunarc', 34.3, 38.0, shot_sunarc, 0.4),
          ('calm3', 38.0, 40.5, shot_calm3, 0.5), ('surprise', 40.5, 42.6, shot_surprise, 0.3), ('flags3', 42.6, 48.5, shot_flags3, 0.3), ('tracks', 48.5, 51.2, shot_tracks, 0.3), ('terrain', 51.2, 54.5, shot_terrain, 0.3),
          ('climb', 54.5, 58.0, shot_climb, 0.3), ('scan', 58.0, 60.6, shot_scan, 0.3), ('sea', 60.6, 64.5, shot_sea, 0.3), ('think', 64.5, 68.0, shot_think, 0.3), ('bubble', 68.0, 71.4, shot_bubble, 0.3),
          ('run2', 71.4, 76.5, shot_run2, 0.3), ('away', 76.5, 80.8, shot_away, 0.4), ('map5', 80.8, DP3, shot_map5, 0.5)]


class PartP3(P2.PartP2):
    def frame(self, T, cv):
        act = []
        for i, (nm, t0, t1, fn, xf) in enumerate(SHOTS3):
            hi = t1 + (SHOTS3[i + 1][4] / 2 if i + 1 < len(SHOTS3) else 0); lo = t0 - xf / 2
            if lo <= T < hi or (i == len(SHOTS3) - 1 and T >= lo): act.append((i, fn, xf, t0))
        if len(act) == 1:
            act[0][1](cv, T); return cv
        (ia, fa, _, _), (ib, fb, xfb, t0b) = act[-2], act[-1]
        fa(cv, T); buf = np.zeros_like(cv); fb(buf, T)
        a = sstep(clamp((T - (t0b - xfb / 2)) / xfb)); cv *= (1 - a); cv += buf * a
        return cv
