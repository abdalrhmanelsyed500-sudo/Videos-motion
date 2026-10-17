"""2D skeletal rig runtime: FK, analytic 2-bone IK, slot/z-order sprite rendering with mirror/tint/swap/dynamic slots.
Convention (y down): rest bones hang DOWN.  Positive `rot` turns the bone's rest direction (0,1) toward -x on screen,
i.e. direction = (-sin r, cos r).  Pose per bone: dict(rot, sx, sy, tx, ty).  Root pose: dict(x, y, rot, sx, sy, flip)."""
import json, math, os
import numpy as np, cv2
from .vec import load_png

def T3(x, y): return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], np.float64)
def R3(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float64)
def S3(x, y): return np.array([[x, 0, 0], [0, y, 0], [0, 0, 1]], np.float64)

class Rig:
    def __init__(self, path):
        self.dir = os.path.dirname(path)
        d = json.load(open(path)); self.d = d; self.ppu = d['ppu']
        self.bones = d['bones']; self.idx = {b['name']: i for i, b in enumerate(self.bones)}
        self.head = {b['name']: np.array(b['head'], float) for b in self.bones}
        self.parent = {b['name']: b['parent'] for b in self.bones}
        self.limit = {b['name']: b.get('limit') for b in self.bones}
        self.slots = sorted(d['slots'], key=lambda s: s['z'])
        self.parts = d['parts']; self.ik = d.get('ik', {})
        self._img = {}; self._cache = {}
        self.order = [b['name'] for b in self.bones]   # parents always listed before children

    # ---------------------------------------------------------------- FK
    def root_matrix(self, root):
        r = root or {}
        M = T3(r.get('x', 0.0), r.get('y', 0.0)) @ R3(r.get('rot', 0.0)) @ S3(r.get('sx', 1.0) * (-1 if r.get('flip') else 1), r.get('sy', 1.0))
        return M

    def world(self, pose=None, root=None):
        pose = pose or {}; W = {}; Rm = self.root_matrix(root)
        for n in self.order:
            p = self.parent[n]; b = pose.get(n, {})
            base = Rm if p is None else W[p]
            off = self.head[n] - (self.head[p] if p else np.zeros(2))
            if p is None: off = self.head[n]
            W[n] = base @ T3(off[0] + b.get('tx', 0.0), off[1] + b.get('ty', 0.0)) @ R3(b.get('rot', 0.0)) @ S3(b.get('sx', 1.0), b.get('sy', 1.0))
        return W

    def pos(self, name, pose=None, root=None, W=None):
        W = W or self.world(pose, root); return W[name][:2, 2].copy()

    def tip(self, name, length, pose=None, root=None, W=None):
        W = W or self.world(pose, root); return (W[name] @ np.array([0, length, 1.0]))[:2]

    # ---------------------------------------------------------------- IK
    def ik2(self, pose, chain, target, bend=1, end_rot=None, root=None, stretch=True):
        """Analytic 2-bone IK. chain=(upper,lower,end) ; target = world position of the END bone head.
        Writes rot of upper/lower (and end if end_rot given: rotation relative to the root frame). Returns reach error (units)."""
        up, lo, en = chain
        pose = pose if pose is not None else {}
        for n in (up, lo): pose.setdefault(n, {})['rot'] = 0.0
        W = self.world(pose, root)
        par = self.parent[up]; Wp = self.root_matrix(root) if par is None else W[par]
        tl = (np.linalg.inv(Wp) @ np.array([target[0], target[1], 1.0]))[:2]
        o = self.head[up] - (self.head[par] if par else 0) + np.array([pose[up].get('tx', 0), pose[up].get('ty', 0)])
        L1 = float(np.linalg.norm(self.head[lo] - self.head[up])); L2 = float(np.linalg.norm(self.head[en] - self.head[lo]))
        d = tl - o; dist = float(np.hypot(*d)); phi = math.atan2(d[1], d[0])
        dc = min(max(dist, abs(L1 - L2) + 1e-3), L1 + L2 - 1e-3)
        A = math.acos(max(-1, min(1, (L1 * L1 + dc * dc - L2 * L2) / (2 * L1 * dc))))
        psi1 = phi - bend * A
        j = o + L1 * np.array([math.cos(psi1), math.sin(psi1)])
        e = o + dc * np.array([math.cos(phi), math.sin(phi)])
        psi2 = math.atan2(*(e - j)[::-1])
        t1 = psi1 - math.pi / 2; t2 = psi2 - math.pi / 2
        pose[up]['rot'] = _wrap(t1); pose[lo]['rot'] = _wrap(t2 - t1)
        if end_rot is not None: pose.setdefault(en, {})['rot'] = _wrap(end_rot - t2)
        return max(0.0, dist - (L1 + L2))

    # ---------------------------------------------------------------- limits
    def clamp(self, pose):
        out = {}
        for n, b in pose.items():
            b = dict(b); lim = self.limit.get(n)
            if lim and 'rot' in b: b['rot'] = float(np.clip(b['rot'], math.radians(lim[0]), math.radians(lim[1])))
            out[n] = b
        return out

    def violations(self, pose, tol=1e-6):
        v = []
        for n, b in pose.items():
            lim = self.limit.get(n)
            if lim and 'rot' in b and not (math.radians(lim[0]) - tol <= b['rot'] <= math.radians(lim[1]) + tol): v.append((n, math.degrees(b['rot']), lim))
        return v

    # ---------------------------------------------------------------- render
    def img(self, part):
        if part not in self._img:
            self._img[part] = load_png(os.path.join(self.dir, self.parts[part]['image']))
        return self._img[part]

    def _scaled(self, key, im, f):
        k = (key, round(f, 2))
        if k not in self._cache:
            self._cache[k] = cv2.resize(im, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
            if len(self._cache) > 600: self._cache.pop(next(iter(self._cache)))
        return self._cache[k]

    def draw(self, canvas, pose=None, cam=(1.0, 0.0, 0.0), hidden=(), swap=None, dyn=None, root=None, alpha=1.0, tint=None, only=None, zov=None):
        """canvas: float32 BGR (H,W,3) 0..1, drawn in place.  cam=(scale, tx, ty): screen = scale*world + t."""
        W = self.world(pose, root); swap = swap or {}; dyn = dyn or {}
        sc, cx, cy = cam; C = np.array([[sc, 0, cx], [0, sc, cy], [0, 0, 1]], np.float64)
        H, Wd = canvas.shape[:2]
        order = self.slots if not zov else sorted(self.slots, key=lambda q: zov.get(q['name'], q['z']))
        for s in order:
            nm = s['name']
            if nm in hidden or (only is not None and nm not in only): continue
            if s.get('dyn'):
                if s['dyn'] not in dyn or dyn[s['dyn']] is None: continue
                im, an, ppu = dyn[s['dyn']]; key = ('dyn', nm)
                anx, any_ = an
            else:
                part = swap.get(nm, s['part']); im = self.img(part); key = part
                anx, any_ = self.parts[part]['anchor']; ppu = self.ppu
            off = s.get('offset', [0, 0]); m = -1.0 if s.get('mirror') else 1.0
            Sp = np.array([[m / ppu, 0, -m * anx / ppu + off[0]], [0, 1 / ppu, -any_ / ppu + off[1]], [0, 0, 1]])
            A = C @ W[s['bone']] @ Sp                      # sprite px -> screen px
            f = math.sqrt(abs(np.linalg.det(A[:2, :2])))   # screen px per sprite px
            src = im
            if f < 0.7:
                src = self._scaled((key, id(im)) if s.get('dyn') else key, im, f) if not s.get('dyn') else cv2.resize(im, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
                A = A @ np.diag([1 / f, 1 / f, 1])
            h, w = src.shape[:2]
            corners = A @ np.array([[0, w, w, 0], [0, 0, h, h], [1, 1, 1, 1.0]])
            x0 = max(int(math.floor(corners[0].min())) - 1, 0); x1 = min(int(math.ceil(corners[0].max())) + 1, Wd)
            y0 = max(int(math.floor(corners[1].min())) - 1, 0); y1 = min(int(math.ceil(corners[1].max())) + 1, H)
            if x1 <= x0 or y1 <= y0: continue
            Aroi = (T3(-x0, -y0) @ A)[:2]
            roi = cv2.warpAffine(src, Aroi, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
            a = roi[..., 3:4] * alpha; rgb = roi[..., :3] * alpha
            t = s.get('tint')
            if t is not None: rgb = rgb * np.array(t[::-1], np.float32)
            if tint is not None: rgb = rgb * np.array(tint[::-1], np.float32)
            canvas[y0:y1, x0:x1] = canvas[y0:y1, x0:x1] * (1 - a) + rgb
        return canvas

def _wrap(a): return (a + math.pi) % (2 * math.pi) - math.pi
