"""Prosperi video PART 6 (Arabic, 92.45 s): exhaustion, the decision to keep searching, reading the ground (tracks, herd traces, a depression), the Bedouins and the little girl,
water and care, the drained body, the biggest surprise (the map). Same oil layered-puppet system. NO face mark, NO captions, NO music.
New characters: b = Bedouin man, q = little girl (cut by prepare_pros6.py; same rig as m)."""
from pros5_scenes import *
import pros5_scenes as P5
import hook_scenes as HK
from PIL import Image, ImageDraw, ImageFont
from PIL import Image, ImageDraw, ImageFont
for _k in 'bq': HK.RIG[_k] = HK.RIG['m']

DP6 = 92.45
INK = (40.0, 62.0, 100.0)


def icon_drop(cv, x, y, s, a=1.0):
    ov = cv.copy(); cv2.circle(ov, (int(x), int(y + 6 * s)), int(13 * s), (200.0, 140.0, 60.0), -1, cv2.LINE_AA)
    cv2.fillConvexPoly(ov, np.array([(x - 12 * s, y + 2 * s), (x + 12 * s, y + 2 * s), (x, y - 24 * s)], np.int32), (200.0, 140.0, 60.0), cv2.LINE_AA); cv[:] = cv * (1 - a) + ov * a


def icon_paw(cv, x, y, s, a=1.0, col=INK):
    ov = cv.copy(); cv2.ellipse(ov, (int(x), int(y + 6 * s)), (int(13 * s), int(10 * s)), 0, 0, 360, col, -1, cv2.LINE_AA)
    for dx, dy in ((-15, -8), (-5, -17), (6, -17), (16, -8)): cv2.ellipse(ov, (int(x + dx * s), int(y + dy * s)), (int(5 * s), int(7 * s)), 0, 0, 360, col, -1, cv2.LINE_AA)
    cv[:] = cv * (1 - a) + ov * a


def icon_person(cv, x, y, s, a=1.0, col=INK):
    ov = cv.copy(); cv2.circle(ov, (int(x), int(y - 14 * s)), int(9 * s), col, -1, cv2.LINE_AA)
    cv2.fillConvexPoly(ov, np.array([(x - 7 * s, y - 4 * s), (x + 7 * s, y - 4 * s), (x + 14 * s, y + 24 * s), (x - 14 * s, y + 24 * s)], np.int32), col, cv2.LINE_AA); cv[:] = cv * (1 - a) + ov * a


def disc(cv, x, y, r, a, col=(245.0, 245.0, 240.0)):
    if a <= 0.02: return
    ov = cv.copy(); cv2.circle(ov, (int(x), int(y)), int(r), col, -1, cv2.LINE_AA); cv2.circle(ov, (int(x), int(y)), int(r), INK, 3, cv2.LINE_AA); cv[:] = cv * (1 - a) + ov * a


def sunicon(cv, x, y, r, a=1.0, half=False):
    if a <= 0.02: return
    ov = cv.copy(); col = (70.0, 190.0, 250.0)
    for i in range(12):
        an = i * math.pi / 6
        if half and not (-0.01 <= math.sin(an) <= 1.01 and math.cos(an) >= -0.01): continue
        cv2.line(ov, (int(x + r * 1.25 * math.cos(an)), int(y + r * 1.25 * math.sin(an))), (int(x + r * 1.7 * math.cos(an)), int(y + r * 1.7 * math.sin(an))), col, 4, cv2.LINE_AA)
    if half: cv2.ellipse(ov, (int(x), int(y)), (int(r), int(r)), 90, 0, 180, col, -1, cv2.LINE_AA)
    else: cv2.circle(ov, (int(x), int(y)), int(r), col, -1, cv2.LINE_AA)
    cv[:] = cv * (1 - a) + ov * a


def qmark(cv, x, y, h, a, col=(40, 62, 150)):
    if a <= 0.02: return
    im = Image.new('RGBA', (int(h * 1.2), int(h * 1.6)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype('assets/Amiri-Bold.ttf', int(h)); d.text((im.width / 2, im.height / 2), '?', font=f, fill=(col[0], col[1], col[2], 255), anchor='mm')
    arr = np.array(im).astype(np.float32); al = arr[..., 3:4] / 255.0 * a; x0, y0 = int(x - im.width / 2), int(y - im.height / 2)
    if x0 < 0 or y0 < 0 or x0 + im.width > W or y0 + im.height > H: return
    roi = cv[y0:y0 + im.height, x0:x0 + im.width]; roi[:] = roi * (1 - al) + arr[..., [2, 1, 0]] * al


def B_(T): return 0.5 + 0.5 * math.sin(T * 2.0)


# 1 exhausted: staggers, sinks to his knees
def shot_collapse(cv, T):
    wc = cam(T, 0, 3.8, (760, 336, 1.15), (800, 340, 1.4), 'pr_empty', cv=cv)
    k = ev(T, 1.6, 3.4)
    draw_people(cv, [person(wc, 'p', 760, 640 + 90 * k, 1.3, 1, 0.3, walk=0.5 * (1 - k), sway=3.0, pose={'aL': 10, 'aR': 10, 'lean': 16 + 14 * k, 'head': 18 + 14 * k + 3 * math.sin(T * 2.2)})], T)
    cv[:] = heat_haze(cv, T, 2.6, 0.05, 3.2, 250, 660); glowpt(cv, 1050, 70, 380, (200, 240, 255), 0.5); vignette(cv, 0.3 + 0.35 * B_(T), 2.0); tone(cv, 1.0, 12, (0.97, 1.0, 1.06), 0.85); fin(cv, T, 801, 0.45)


# 2 the strength runs out: he sits on the ground and stops moving, the dunes alone
def shot_sink(cv, T):
    wc = cam(T, 3.4, 8.9, (860, 340, 1.25), (880, 345, 1.4), 'pr_rocks', cv=cv)
    s = math.sin(T * 1.3)
    draw_people(cv, [person(wc, 'p', 860, 670, 1.15, -1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 34 + 3 * s, 'lean': 30 + 2 * s})], T)
    xx, yy = wc.pt(860, 670); mound(cv, xx, yy + 30 * wc.z, 150 * wc.z, 36 * wc.z, 0.92)
    cv[:] = heat_haze(cv, T, 2.0, 0.05, 3.0, 250, 650); vignette(cv, 0.45 + 0.3 * B_(T), 2.0); tone(cv, 0.98, 8, (0.95, 1.0, 1.08), 0.7); fin(cv, T, 802, 0.5)


# 3 even the strongest person can reach the moment he cannot bear more: tiny figure, huge sky at dusk
def shot_cant(cv, T):
    wc = cam(T, 8.6, 15.0, (800, 336, 1.0), (800, 336, 1.0), 'pr_empty', cv=cv)
    k = seg(T, 8.6, 15.0)
    draw_people(cv, [person(wc, 'p', 800, 600, 0.85, 1, 0.3, pose={'aL': 8 + 100 * ev(T, 11.0, 11.8) * (1 - ev(T, 13.0, 13.8)), 'fL': 140 * ev(T, 11.0, 11.8) * (1 - ev(T, 13.0, 13.8)), 'aR': 8, 'head': 28 + 3 * math.sin(T * 1.2), 'lean': 22})], T)
    tone(cv, 1.0, -6 * k, (1.0 - 0.1 * k, 1.0 - 0.18 * k, 1.0 - 0.3 * k), 0.9); vignette(cv, 0.4 + 0.4 * k, 2.0); fin(cv, T, 803, 0.5)


# 4 but the story did not end there: dawn, he lifts his head
def shot_notend(cv, T):
    wc = cam(T, 14.6, 17.0, (800, 340, 1.3), (800, 336, 1.2), 'pr_dawn', cv=cv)
    up = ev(T, 15.2, 16.4)
    draw_people(cv, [person(wc, 'p', 800, 640 + 60 * (1 - up), 1.3, 1, 0.3, pose={'aL': 8, 'aR': 8, 'head': 28 * (1 - up) - 6 * up, 'lean': 24 * (1 - up)})], T)
    glowpt(cv, *wc.pt(585, 262), 420 * wc.z, (150, 220, 255), 0.1 + 0.25 * ev(T, 14.8, 16.8)); fin(cv, T, 804, 0.35)


# 5 instead of waiting for a rescue that may never come, he decides to continue: the waiting bubble fades, he walks
def shot_decide(cv, T):
    wc = cam(T, 16.6, 23.6, (700, 336, 1.25), (1000, 336, 1.25), 'pr_dawn', cv=cv)
    X = jog(620, 1060, 19.4, 23.2, T); up = ev(T, 16.8, 17.8)
    a = ev(T, 17.0, 17.8) * (1 - ev(T, 19.0, 19.9))
    if a > 0.02:
        bubble(cv, 700, 190, 150, 'pr_aerial', (300, 100, 900, 650), clamp(a))
        qmark(cv, 700, 190, 130, 0.9 * a)
    draw_people(cv, [person(wc, 'p', 620 if T < 19.4 else X, 640 + 40 * (1 - up), 1.3, 1, 0.3, walk=1.0 if T > 19.4 else 0.0, pose={'aL': 10, 'aR': 10, 'lean': 8 + 10 * (1 - up), 'head': 14 * (1 - up)})], T)
    if T > 19.4: xx, yy = wc.pt(X, 650); puffs(cv, T, 19.4, 23.2, 12, (xx - 140, yy - 8, 120, 14), SAND, seed=76, size=(24, 50), rise=(8, 24), life=1.0, alpha=0.28, wind=(-100, 0))
    fin(cv, T, 805, 0.35)


# 6 he reads the ground: signs of water, animals or people
def shot_read(cv, T):
    wc = cam(T, 23.4, 30.6, (700, 380, 1.5), (760, 400, 1.7), 'pr_rocks', cv=cv)
    d = ev(T, 24.0, 25.0)
    draw_people(cv, [person(wc, 'p', 700, 640 + 40 * d, 1.3, 1, 0.3, pose={'aL': 8 + 100 * ev(T, 25.2, 26.0) * (1 - ev(T, 29.0, 29.8)), 'fL': 140 * ev(T, 25.2, 26.0) * (1 - ev(T, 29.0, 29.8)), 'aR': 8, 'head': 24 * d + 5 * math.sin(T * 1.4), 'lean': 14 * d})], T)
    for i, (fn, t0) in enumerate(((icon_drop, 26.4), (icon_paw, 27.8), (icon_person, 29.0))):
        a = ev(T, t0, t0 + 0.5); x = 930 + i * 130; y = 190 + 8 * math.sin(T * 2 + i)
        if a > 0.02: disc(cv, x, y, 52, a * 0.9); fn(cv, x, y + 4, 1.4, a)
    cv[:] = heat_haze(cv, T, 1.6, 0.05, 3.0, 300, 640); fin(cv, T, 806, 0.4)


# 7 sometimes the small sign is more important than any map: the map fades, big prints take over
def shot_small(cv, T):
    m = 1.0 - ev(T, 31.0, 32.2)
    wc = cam(T, 30.0, 34.3, (800, 336, 1.2), (900, 336, 1.5), 'pr_rocks', cv=cv)
    if m > 0.02:
        buf = np.zeros_like(cv); w2 = WC(800, 336, 1.0); w2.draw(buf, 'pr_map', 1.0); sc = 0.95 + 0.1 * (1 - m); cv[:] = cv * (1 - m * 0.95) + buf * m * 0.95
    pts = [(760 + 55 * i, 510 - 10 * (i % 2) - 6 * i, 15) for i in range(7)]
    prints(cv, wc, pts[:int(ev(T, 31.4, 33.2) * 7) + 1], ev(T, 31.2, 31.8), (40.0, 62.0, 100.0))
    for i in range(min(7, int(ev(T, 31.4, 33.2) * 7) + 1)): icon_paw(cv, *wc.pt(pts[i][0], pts[i][1] - 6), 1.5 * wc.z, ev(T, 31.4, 32.2) * 0.8)
    cv[:] = heat_haze(cv, T, 1.2, 0.05, 3.0, 300, 640); fin(cv, T, 807, 0.4)


# 8 an animal's tracks, signs of a passing herd
def shot_tracks(cv, T):
    wc = cam(T, 33.9, 42.9, (700, 336, 1.3), (1100, 336, 1.3), 'pr_rocks', cv=cv)
    n = int(ev(T, 34.4, 41.5) * 22)
    pts = [(600 + 24 * i + 6 * math.sin(i), 520 + 12 * math.sin(i * 0.9), 11) for i in range(n)] + [(600 + 22 * i, 480 + 10 * math.sin(i * 1.3), 9) for i in range(max(0, n - 4))]
    prints(cv, wc, pts, 0.9, (40.0, 62.0, 100.0))
    X = jog(480, 1040, 35.2, 42.4, T); crouch = ev(T, 34.6, 35.4) * (1 - ev(T, 36.0, 36.6))
    draw_people(cv, [person(wc, 'p', 480 if T < 35.2 else X, 600 + 40 * crouch, 1.3, 1, 0.3, walk=1.0 if T > 35.2 else 0.0, pose={'aL': 8 + 40 * crouch, 'aR': 8, 'lean': 12 + 14 * crouch, 'head': 14 + 14 * crouch})], T)
    cv[:] = heat_haze(cv, T, 1.4, 0.05, 3.0, 300, 640); fin(cv, T, 808, 0.4)


# 9 the shape of the land near a depression: he looks down to a hollow, a ring marks it
def shot_depression(cv, T):
    wc = cam(T, 38.4, 43.0, (640, 380, 1.1), (800, 400, 1.3), 'pr_empty', cv=cv)
    a = ev(T, 39.4, 40.4)
    hx, hy = wc.pt(1100, 560); ring(cv, hx, hy, 260 * wc.z, a * (0.7 + 0.3 * math.sin(T * 3)))
    X = jog(380, 700, 38.6, 42.8, T)
    draw_people(cv, [person(wc, 'p', X, 600, 1.2, 1, 0.3, walk=1.0, pose={'aL': 14, 'aR': 14, 'lean': 8, 'head': 10})], T)
    cv[:] = heat_haze(cv, T, 1.6, 0.05, 3.0, 300, 640); fin(cv, T, 809, 0.4)


# 10 closer to traces of human life: far camp and smoke
def shot_approach(cv, T):
    k = seg(T, 42.6, 48.6); wc = WC(lerp(560, 900, k), lerp(420, 380, k), lerp(1.0, 1.5, k)); wc.draw(cv, 'pr_nomad', 1.0)
    X = jog(260, 700, 42.8, 48.4, T)
    draw_people(cv, [person(wc, 'p', X, 600, 1.1, 1, 0.3, walk=1.0, pose={'aL': 14, 'aR': 14, 'lean': 10, 'head': 8})], T)
    cv[:] = heat_haze(cv, T, 1.2, 0.05, 3.0, 300, 640); glowpt(cv, *wc.pt(380, 310), 300 * wc.z, (110, 200, 255), 0.25); fin(cv, T, 810, 0.4)


# 11 about nine and a half days: nine suns and half a sun
def shot_days9(cv, T):
    wc = cam(T, 48.4, 52.8, (800, 336, 1.2), (850, 336, 1.2), 'pr_dawn', cv=cv)
    ov = np.zeros_like(cv); cv[:] = cv * 0.78
    for i in range(10):
        t0 = 48.8 + i * 0.36; a = ev(T, t0, t0 + 0.3)
        x = 190 + (i % 5) * 225; y = 190 if i < 5 else 330
        sunicon(cv, x, y, 36, a, half=(i == 9))
    X = jog(300, 760, 48.5, 52.8, T)
    draw_people(cv, [person(wc, 'p', X, 650, 0.8, 1, 0.3, walk=0.8, pose={'aL': 14, 'aR': 14, 'lean': 16, 'head': 14})], T)
    fin(cv, T, 811, 0.45)


# 12 he sees the Bedouin: the family at the tents
def shot_sees(cv, T):
    k = seg(T, 52.5, 59.5); wc = WC(lerp(760, 960, k), 400, lerp(1.2, 1.5, k)); wc.draw(cv, 'pr_nomad', 1.0)
    wv = ev(T, 54.6, 55.4) * (1 - ev(T, 58.4, 59.2)); sw = math.sin(T * 6)
    items = [person(wc, 'p', 520, 600, 1.1, 1, 0.3, pose={'aL': 8 + 105 * wv + 14 * sw * wv, 'fL': 80 * wv, 'aR': 8, 'lean': 8, 'head': 8})]
    bx = lerp(1040, 960, ev(T, 53.2, 56.0))
    items += [person(wc, 'b', bx, 470, 0.8, -1, 0.3, pose={'aL': 8, 'aR': 8 + 80 * ev(T, 55.8, 56.6), 'fR': 30 * ev(T, 55.8, 56.6), 'head': 3}),
              person(wc, 'q', bx + 90, 480, 0.8, -1, 0.6, pose={'aL': 8, 'aR': 8, 'head': 3})]
    draw_people(cv, items, T); cv[:] = heat_haze(cv, T, 1.0, 0.05, 3.0, 300, 640); fin(cv, T, 812, 0.4)


# 13 a little girl notices him (close-up) and calls her family
def shot_girl(cv, T):
    cv[:] = 0; w2 = cam(T, 59.2, 62.4, (1020, 400, 1.7), (1020, 400, 1.9), 'pr_nomad', cv=cv); cv[:] = cv2.GaussianBlur(cv, (0, 0), 4)
    p = ev(T, 60.0, 60.8)
    draw_items(cv, IDM, [pc('q', 640, 770, 0.7, 1, 0.5, pose={'aL': 8, 'aR': 8 + 110 * p, 'fR': 60 * p, 'head': 3 * math.sin(T * 2) - 6 * p})], T)
    fin(cv, T, 813, 0.45)


# 14 help from her family and community: the Bedouin man and the girl hurry to him
def shot_help(cv, T):
    k = seg(T, 62.0, 66.0); wc = WC(lerp(760, 640, k), 400, 1.35); wc.draw(cv, 'pr_nomad', 1.0)
    bx = lerp(1000, 720, ev(T, 62.2, 65.2)); mw = 1.0 - ev(T, 64.4, 65.0)
    items = [person(wc, 'p', 600, 620 + 40 * ev(T, 62.2, 63.0), 1.15, 1, 0.3, pose={'aL': 8, 'aR': 8, 'lean': 18, 'head': 18}),
             person(wc, 'b', bx, 560, 0.95, -1, 0.3, walk=mw, pose={'aL': 14, 'aR': 14, 'head': 4}),
             person(wc, 'q', bx + 120, 566, 0.95, -1, 0.7, walk=mw, pose={'aL': 14, 'aR': 14})]
    draw_people(cv, items, T); fin(cv, T, 814, 0.4)


# 15 not just a meeting: the first real proof that the way out exists (warm light on the two men)
def shot_meaning(cv, T):
    wc = cam(T, 65.4, 75.2, (700, 400, 1.7), (680, 410, 2.0), 'pr_nomad', cv=cv)
    up = ev(T, 67.0, 69.6)
    items = [person(wc, 'p', 640, 640 + 60 * (1 - up), 1.2, 1, 0.3, pose={'aL': 8, 'aR': 8, 'lean': 20 * (1 - up), 'head': 18 * (1 - up) - 4 * up}),
             person(wc, 'b', 800, 630, 1.15, -1, 0.3, pose={'aL': 8, 'aR': 8 + 70 * ev(T, 66.4, 67.4) * (1 - ev(T, 72.0, 73.0)), 'fR': 30, 'head': 2})]
    draw_people(cv, items, T); glowpt(cv, *wc.pt(380, 310), 520 * wc.z, (140, 215, 255), 0.1 + 0.12 * ev(T, 69.0, 74.0)); fin(cv, T, 815, 0.35)


# 16 water and food, then a place for care
def shot_water(cv, T):
    wc = cam(T, 74.6, 77.4, (680, 410, 2.0), (700, 410, 2.1), 'pr_nomad', cv=cv)
    sip = ev(T, 75.4, 76.2)
    items = [person(wc, 'p', 640, 640, 1.2, 1, 0.3, pose={'aL': 8 + 110 * sip, 'fL': 140 * sip, 'aR': 8, 'head': -10 * sip, 'lean': 4}),
             person(wc, 'b', 800, 630, 1.15, -1, 0.3, pose={'aL': 8, 'aR': 8 + 80 * ev(T, 74.8, 75.4), 'fR': 40, 'head': 2})]
    draw_people(cv, items, T); fin(cv, T, 816, 0.35)


def shot_care(cv, T):
    wc = cam(T, 76.6, 81.3, (800, 336, 1.0), (760, 336, 1.15), 'pr_hospital', cv=cv)
    s = math.sin(T * 1.1)
    draw_people(cv, [person(wc, 'p', 850, 620, 1.1, -1, 0.3, pose={'aL': 8, 'aR': 8, 'lean': 10 + 3 * s, 'head': 14 + 3 * s})], T)
    glowpt(cv, *wc.pt(1250, 120), 360 * wc.z, (220, 240, 255), 0.35); fin(cv, T, 817, 0.35)


# 17 the body was badly drained: he sways, hand on forehead
def shot_drained(cv, T):
    wc = cam(T, 81.0, 83.6, (800, 336, 1.3), (820, 336, 1.5), 'pr_hospital', cv=cv)
    s = math.sin(T * 1.4); h = ev(T, 81.6, 82.4)
    draw_people(cv, [person(wc, 'p', 820, 620, 1.15, -1, 0.3, pose={'aL': 8 + 110 * h, 'fL': 140 * h, 'aR': 8, 'lean': 16 + 4 * s, 'head': 22 + 3 * s})], T)
    vignette(cv, 0.35 + 0.35 * B_(T), 2.0); tone(cv, 1.0, 4, (0.97, 1.0, 1.05), 0.8); fin(cv, T, 818, 0.4)


# 18 he cannot recover just by eating and drinking: the cup and the dates, he looks at the window
def shot_notnormal(cv, T):
    wc = cam(T, 83.4, 89.8, (1000, 336, 1.2), (1240, 250, 1.8), 'pr_hospital', cv=cv)
    draw_people(cv, [person(wc, 'p', 1050, 620, 1.15, 1, 0.3, pose={'aL': 8, 'aR': 8, 'lean': 8, 'head': 8 * math.sin(T * 0.9) + 6})], T)
    glowpt(cv, *wc.pt(1250, 110), 360 * wc.z, (220, 240, 255), 0.4); fin(cv, T, 819, 0.35)


# 19 when the details of his location became clear, the biggest surprise
def shot_surprise(cv, T):
    k = seg(T, 89.6, DP6); wc = WC(lerp(1000, 960, k), 336, lerp(1.0, 1.15, k)); wc.draw(cv, 'pr_map', 1.0)
    route_overlay(cv, wc, T, 89.8, 90.8)
    hx, hy = wc.pt(1450, 462); ring(cv, hx, hy, 120 * wc.z, ev(T, 90.6, 91.2) * (0.7 + 0.3 * math.sin(T * 4)))
    qmark(cv, min(hx - 20, 1150), hy - 160, 150, ev(T, 91.0, 91.8)); fin(cv, T, 820, 0.4)


SHOTS6 = [('collapse', 0.0, 3.6, shot_collapse, 0.0), ('sink', 3.6, 8.7, shot_sink, 0.4), ('cant', 8.7, 14.8, shot_cant, 0.4), ('notend', 14.8, 16.8, shot_notend, 0.4), ('decide', 16.8, 23.5, shot_decide, 0.4),
          ('read', 23.5, 30.3, shot_read, 0.4), ('small', 30.3, 34.0, shot_small, 0.4), ('tracks', 34.0, 38.5, shot_tracks, 0.3), ('depression', 38.5, 42.8, shot_depression, 0.3), ('approach', 42.8, 48.5, shot_approach, 0.4),
          ('days9', 48.5, 52.6, shot_days9, 0.4), ('sees', 52.6, 59.4, shot_sees, 0.4), ('girl', 59.4, 62.2, shot_girl, 0.3), ('help', 62.2, 65.6, shot_help, 0.3), ('meaning', 65.6, 74.8, shot_meaning, 0.4),
          ('water', 74.8, 76.8, shot_water, 0.3), ('care', 76.8, 81.1, shot_care, 0.5), ('drained', 81.1, 83.6, shot_drained, 0.3), ('notnormal', 83.6, 89.8, shot_notnormal, 0.3), ('surprise', 89.8, DP6, shot_surprise, 0.4)]


class PartP6(P2.PartP2):
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
