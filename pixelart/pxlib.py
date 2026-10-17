"""Tiny pixel-art toolkit: masks -> auto-shaded parts (light from top-left) -> selective outline (sel-out) -> RGBA frames.
Everything is drawn on an integer pixel grid. No anti-aliasing, no resampling, limited palette."""
import numpy as np
from PIL import Image, ImageDraw

def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

class Mat:
    """material = ramp of 5 tones: 0 outline/darkest, 1 shadow, 2 base, 3 light, 4 highlight"""
    def __init__(self, name, hexes): self.name = name; self.ramp = [hexrgb(h) for h in hexes]

class Canvas:
    def __init__(self, mats, w=32, h=32, flip=False):
        self.w, self.h, self.mats, self.flip = w, h, mats, flip
        self.rgb = np.zeros((h, w, 3), np.uint8); self.fill = np.zeros((h, w), bool)
        self.mat = np.full((h, w), -1, int); self.shadow = np.zeros((h, w), bool)
    # ---- masks
    def M(self): return np.zeros((self.h, self.w), bool)
    def rect(self, x0, y0, x1, y1, cut=0):
        m = self.M(); m[max(y0, 0):y1 + 1, max(x0, 0):x1 + 1] = True
        if cut:   # chamfer corners
            for (cx, cy) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
                for k in range(cut):
                    for j in range(cut - k):
                        xx = cx + (j if cx == x0 else -j); yy = cy + (k if cy == y0 else -k)
                        if 0 <= xx < self.w and 0 <= yy < self.h: m[yy, xx] = False
        return m
    def ell(self, cx, cy, rx, ry):
        m = self.M(); ys, xs = np.mgrid[0:self.h, 0:self.w]
        m[((xs - cx) / (rx + .5)) ** 2 + ((ys - cy) / (ry + .5)) ** 2 <= 1.0] = True; return m
    def poly(self, pts):
        im = Image.new('L', (self.w, self.h), 0); ImageDraw.Draw(im).polygon(pts, fill=255, outline=255); return np.array(im) > 0
    def pts(self, *p):
        m = self.M()
        for x, y in p:
            if 0 <= x < self.w and 0 <= y < self.h: m[y, x] = True
        return m
    # ---- painting
    def _fx(self, m): return m[:, ::-1] if self.flip else m
    def paint(self, mask, mat, lvl=None, shade=True, edge=False, flat=None):
        """paint mask with material; shade: bevel (top/left edge lighter, bottom/right darker); edge: dark separation line on the part border where it overlaps earlier parts"""
        m = self._fx(mask) if not getattr(self, '_pre', False) else mask
        mi = self.mats.index(mat) if not isinstance(mat, int) else mat; R = self.mats[mi].ramp
        up = np.zeros_like(m); dn = np.zeros_like(m); lf = np.zeros_like(m); rt = np.zeros_like(m)
        up[1:] = ~m[:-1]; up[0] = True; dn[:-1] = ~m[1:]; dn[-1] = True; lf[:, 1:] = ~m[:, :-1]; lf[:, 0] = True; rt[:, :-1] = ~m[:, 1:]; rt[:, -1] = True
        L = np.full(m.shape, 2 if lvl is None else lvl, int)
        if shade: L = L + ((up | lf) & m).astype(int) - ((dn | rt) & m).astype(int) * 1
        if flat is not None: L[:] = flat
        L = np.clip(L, 0, 4)
        if edge:     # dark separation line on the border pixels that touch earlier parts
            fb = self.fill & ~m; touch = np.zeros_like(m)
            touch[1:] |= fb[:-1]; touch[:-1] |= fb[1:]; touch[:, 1:] |= fb[:, :-1]; touch[:, :-1] |= fb[:, 1:]
            L[m & touch] = 0 if edge is True else edge
        ys, xs = np.where(m)
        for y, x in zip(ys, xs): self.rgb[y, x] = R[L[y, x]]; self.fill[y, x] = True; self.mat[y, x] = mi
    def dot(self, x, y, mat, lvl):
        if self.flip: x = self.w - 1 - x
        if 0 <= x < self.w and 0 <= y < self.h and self.fill[y, x]: self.rgb[y, x] = self.mats[mat if isinstance(mat, int) else self.mats.index(mat)].ramp[lvl]
    def dotf(self, x, y, mat, lvl):     # dot that also creates the pixel
        if self.flip: x = self.w - 1 - x
        if 0 <= x < self.w and 0 <= y < self.h:
            mi = mat if isinstance(mat, int) else self.mats.index(mat); self.rgb[y, x] = self.mats[mi].ramp[lvl]; self.fill[y, x] = True; self.mat[y, x] = mi
    def shadow_ell(self, cx, cy, rx, ry): self.shadow |= self._fx(self.ell(cx, cy, rx, ry))
    def outline(self):
        f = self.fill; o = np.zeros_like(f); src = np.full(f.shape, -1, int)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.roll(np.roll(f, dy, 0), dx, 1); sm = np.roll(np.roll(self.mat, dy, 0), dx, 1)
            new = sh & ~f & ~o
            # roll wraps: kill wrapped edges
            if dy == 1: new[0] = False
            if dy == -1: new[-1] = False
            if dx == 1: new[:, 0] = False
            if dx == -1: new[:, -1] = False
            src[new] = sm[new]; o |= new
        ys, xs = np.where(o)
        for y, x in zip(ys, xs): self.rgb[y, x] = self.mats[src[y, x]].ramp[0]
        self.fill |= o
    def rgba(self, shadow_alpha=72):
        a = np.zeros((self.h, self.w, 4), np.uint8)
        a[self.shadow & ~self.fill] = (14, 16, 28, shadow_alpha)
        a[self.fill, :3] = self.rgb[self.fill]; a[self.fill, 3] = 255
        return np.roll(a, 1, axis=0)        # whole figure sits 1 px lower so the head/crest never touches the frame edge

def save_scaled(rgba, path, k=8, bg=(52, 58, 72)):
    im = Image.fromarray(rgba, 'RGBA'); big = im.resize((im.width * k, im.height * k), Image.NEAREST)
    base = Image.new('RGBA', big.size, bg + (255,)); base.alpha_composite(big); base.convert('RGB').save(path)
