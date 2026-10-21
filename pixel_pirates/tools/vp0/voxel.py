"""VP-0 voxel baker: one voxel model -> pixel-art sprites in the project palette.

WHY: every prop, tree, house and ship part is authored ONCE as a coarse voxel model (1 voxel = 1 art pixel = 1/24 m) and baked by
this tool with the SAME light, SAME camera, SAME palette ramps and SAME outline rules. That is what makes a few hundred assets
look like they were drawn by one team, and it lets us bake any number of facings (8 for props, 16 for ships) and any density
(24 px/m ashore and on deck, 12 px/m at sea) from one source.

Projection: vertical oblique ("military") projection. Heights are 1:1 (a 1.9 m pirate is 46 px tall), depth is shown by K px of
vertical shift per voxel of depth, so top faces are visible as in the references (camera looks down ~37 degrees). Axes of the model:
x to the right, y away from the viewer (north), z up.

Shading: smoothed-occupancy normals, one key light from the upper left, cast shadows (ray march), a little ambient occlusion,
then QUANTISED into 4 cel bands that move along the material's palette ramp (so shadows shift hue as the ramp does). Outline: a
1 px dark ramp-0 line round the silhouette, a depth-edge line where one object overlaps another, and a +1 light step on the top
and left rim.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
LOOK = ROOT / "game" / "data" / "look"

K = 0.75                                       # depth shear: tan(36.9 deg)
LIGHT = np.array([-0.55, -0.45, 0.70], np.float32)
LIGHT /= np.linalg.norm(LIGHT)


def _hex(h: str) -> tuple[int, int, int]:
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def load_ramps() -> dict[str, list[tuple[int, int, int]]]:
    r = json.loads((LOOK / "palette.json").read_text())["ramps"]
    r.update(json.loads((LOOK / "palette_vp0.json").read_text())["ramps"])
    return {k: [_hex(c) for c in v] for k, v in r.items()}


RAMPS = load_ramps()
RAMP_NAMES = list(RAMPS)


class Mat:
    """Material: a palette ramp, its base step, flags."""

    def __init__(self, ramp: str, base: int = 2, emissive: bool = False, flat: bool = False):
        self.ramp, self.base, self.emissive, self.flat = ramp, base, emissive, flat


class Vox:
    """A voxel grid. mat[x, y, z] = material id (0 empty); tone[x, y, z] = per-voxel step offset (-2..2)."""

    def __init__(self, X: int, Y: int, Z: int):
        self.X, self.Y, self.Z = X, Y, Z
        self.mat = np.zeros((X, Y, Z), np.uint8)
        self.tone = np.zeros((X, Y, Z), np.int8)
        self.mats: dict[int, Mat] = {}

    # ---- shapes (every shape only touches its own bounding box, so thousands of small parts stay fast) -----------------------
    def _reg(self, lo, hi):
        """Clip a float bounding box to the grid; returns (slices, x, y, z) with x/y/z the voxel-centre coordinates (broadcast)."""
        sl = []
        for a, b, n in zip(lo, hi, (self.X, self.Y, self.Z)):
            sl.append(slice(max(int(np.floor(a)), 0), min(int(np.ceil(b)) + 1, n)))
        if any(s.stop <= s.start for s in sl):
            return None
        ax = [np.arange(s.start, s.stop, dtype=np.float32) + 0.5 for s in sl]
        x, y, z = np.meshgrid(ax[0], ax[1], ax[2], indexing="ij")
        return tuple(sl), x, y, z

    def _put(self, reg, mask, mid, tone=None) -> None:
        sl, x, y, z = reg
        m = self.mat[sl]
        m[mask] = mid
        t = self.tone[sl]
        if tone is None:
            t[mask] = 0
        elif callable(tone):
            t[mask] = np.asarray(tone(x[mask], y[mask], z[mask]), np.int8)
        else:
            t[mask] = tone

    def define(self, mid: int, ramp: str, base: int = 2, **kw) -> int:
        assert ramp in RAMPS, ramp
        self.mats[mid] = Mat(ramp, base, **kw)
        return mid

    def box(self, x0, y0, z0, x1, y1, z1, mid, tone=None):
        """Axis-aligned box [x0,x1) x [y0,y1) x [z0,z1) in voxels."""
        r = self._reg((x0, y0, z0), (x1 - 1, y1 - 1, z1 - 1))
        if r:
            _, x, y, z = r
            self._put(r, (x >= x0) & (x < x1) & (y >= y0) & (y < y1) & (z >= z0) & (z < z1), mid, tone)

    def cyl(self, cx, cy, z0, z1, r, mid, axis="z", tone=None, r1=None):
        """Cylinder (cone/frustum if r1 given). axis z: vertical from z0 to z1 at (cx, cy); axis x: along x from cx to z1 at (y=cy, z=z0);
        axis y: along y from cy to z1 at (x=cx, z=z0)."""
        rm = max(r, r if r1 is None else r1) + 1
        if axis == "z":
            r_ = self._reg((cx - rm, cy - rm, z0), (cx + rm, cy + rm, z1))
        elif axis == "x":
            r_ = self._reg((min(cx, z1), cy - rm, z0 - rm), (max(cx, z1), cy + rm, z0 + rm))
        else:
            r_ = self._reg((cx - rm, min(cy, z1), z0 - rm), (cx + rm, max(cy, z1), z0 + rm))
        if not r_:
            return
        _, gx, gy, gz = r_
        if axis == "z":
            d = np.hypot(gx - cx, gy - cy)
            t = (gz - z0) / max(z1 - z0, 1e-6)
        elif axis == "x":
            d = np.hypot(gy - cy, gz - z0)
            t = (gx - cx) / (z1 - cx if z1 != cx else 1e-6)
        else:
            d = np.hypot(gx - cx, gz - z0)
            t = (gy - cy) / (z1 - cy if z1 != cy else 1e-6)
        rr = r if r1 is None else r + (r1 - r) * np.clip(t, 0, 1)
        self._put(r_, (d <= rr) & (t >= 0) & (t <= 1), mid, tone)

    def ell(self, cx, cy, cz, rx, ry, rz, mid, tone=None):
        r_ = self._reg((cx - rx, cy - ry, cz - rz), (cx + rx, cy + ry, cz + rz))
        if r_:
            _, gx, gy, gz = r_
            self._put(r_, (((gx - cx) / rx) ** 2 + ((gy - cy) / ry) ** 2 + ((gz - cz) / rz) ** 2) <= 1.0, mid, tone)

    def tube(self, p0, p1, r, mid, tone=None, r1=None):
        """Round tube between two points (x, y, z)."""
        p0, p1 = np.array(p0, np.float32), np.array(p1, np.float32)
        rm = max(r, r if r1 is None else r1) + 1
        r_ = self._reg(np.minimum(p0, p1) - rm, np.maximum(p0, p1) + rm)
        if not r_:
            return
        _, gx, gy, gz = r_
        d = p1 - p0
        L2 = float(d @ d)
        q0, q1, q2 = gx - p0[0], gy - p0[1], gz - p0[2]
        t = np.clip((q0 * d[0] + q1 * d[1] + q2 * d[2]) / max(L2, 1e-6), 0, 1)
        dist = np.sqrt((q0 - t * d[0]) ** 2 + (q1 - t * d[1]) ** 2 + (q2 - t * d[2]) ** 2)
        rr = r if r1 is None else r + (r1 - r) * t
        self._put(r_, dist <= rr, mid, tone)

    def where(self, fn, mid, tone=None, lo=None, hi=None):
        """Fill every voxel where fn(x, y, z) (voxel-centre coordinates) is True (optionally inside a bounding box)."""
        r_ = self._reg(lo or (0, 0, 0), hi or (self.X, self.Y, self.Z))
        if r_:
            _, gx, gy, gz = r_
            self._put(r_, fn(gx, gy, gz), mid, tone)

    def carve(self, fn, lo=None, hi=None):
        r_ = self._reg(lo or (0, 0, 0), hi or (self.X, self.Y, self.Z))
        if r_:
            sl, gx, gy, gz = r_
            m = fn(gx, gy, gz)
            self.mat[sl][m] = 0
            self.tone[sl][m] = 0

    def rotz(self, quarter_turns: int) -> "Vox":
        n = quarter_turns % 4
        v = Vox.__new__(Vox)
        v.mats = self.mats
        v.mat = np.ascontiguousarray(np.rot90(self.mat, n, axes=(0, 1)))
        v.tone = np.ascontiguousarray(np.rot90(self.tone, n, axes=(0, 1)))
        v.X, v.Y, v.Z = v.mat.shape
        return v

    def rotate(self, deg: float) -> "Vox":
        """Rotate about the vertical axis through the grid centre by any angle (nearest-neighbour, for the 8/16-facing bakes)."""
        cx, cy = self.X / 2.0, self.Y / 2.0
        n = int(np.ceil(np.hypot(self.X, self.Y)))
        a = np.radians(deg)
        c, s = np.cos(a), np.sin(a)
        gx, gy = np.meshgrid(np.arange(n) + 0.5 - n / 2.0, np.arange(n) + 0.5 - n / 2.0, indexing="ij")
        sx = (c * gx + s * gy + cx).astype(int)
        sy = (-s * gx + c * gy + cy).astype(int)
        ok = (sx >= 0) & (sx < self.X) & (sy >= 0) & (sy < self.Y)
        sx, sy = np.clip(sx, 0, self.X - 1), np.clip(sy, 0, self.Y - 1)
        v = Vox(n, n, self.Z)
        v.mats = self.mats
        m = self.mat[sx, sy, :]
        t = self.tone[sx, sy, :]
        m[~ok] = 0
        t[~ok] = 0
        v.mat, v.tone = m, t
        return v

    def merge(self, other: "Vox", ox: int, oy: int, oz: int) -> None:
        """Stamp `other` into self at an integer offset (non-empty voxels only)."""
        for k, v in other.mats.items():
            self.mats.setdefault(k, v)
        x0, y0, z0 = max(ox, 0), max(oy, 0), max(oz, 0)
        x1, y1, z1 = min(ox + other.X, self.X), min(oy + other.Y, self.Y), min(oz + other.Z, self.Z)
        if x1 <= x0 or y1 <= y0 or z1 <= z0:
            return
        sub = other.mat[x0 - ox:x1 - ox, y0 - oy:y1 - oy, z0 - oz:z1 - oz]
        st = other.tone[x0 - ox:x1 - ox, y0 - oy:y1 - oy, z0 - oz:z1 - oz]
        dst = self.mat[x0:x1, y0:y1, z0:z1]
        dt = self.tone[x0:x1, y0:y1, z0:z1]
        m = sub > 0
        dst[m] = sub[m]
        dt[m] = st[m]


# ---- tone helpers (deterministic texture on a material) --------------------------------------------------------------------
def hash3(x, y, z, seed=0):
    with np.errstate(over="ignore"):
        h = (np.floor(x).astype(np.uint64) * np.uint64(73856093)) ^ (np.floor(y).astype(np.uint64) * np.uint64(19349663)) ^ \
            (np.floor(z).astype(np.uint64) * np.uint64(83492791)) ^ np.uint64((seed * 2654435761) & 0xFFFFFFFFFFFF)
        h = (h ^ (h >> np.uint64(13))) * np.uint64(1274126177)
        h = h ^ (h >> np.uint64(16))
    return (h & np.uint64(0xFFFF)).astype(np.float32) / 65535.0


def tone_noise(seed=0, amt=0.18):
    def f(x, y, z):
        r = hash3(x, y, z, seed)
        return np.where(r < amt, -1, np.where(r > 1 - amt, 1, 0))
    return f


def tone_planks(axis="x", pitch=4, seed=1, grain=0.12):
    """Wooden planks: a dark seam every `pitch` voxels across `axis`, staggered butt joints, light grain."""
    def f(x, y, z):
        a = {"x": x, "y": y, "z": z}[axis]
        b = {"x": y, "y": x, "z": x}[axis]
        idx = np.floor(a / pitch)
        seam = (np.floor(a) % pitch) == 0
        off = hash3(idx, idx * 0, idx * 0, seed) * 24
        butt = (np.floor(b + off) % 22) == 0
        g = hash3(x, y, z, seed + 7)
        t = np.where(g < grain, -1, np.where(g > 1 - grain, 1, 0))
        shade = np.floor(hash3(idx, 3, 7, seed + 3) * 3).astype(int) - 1       # each plank a slightly different tone
        t = np.clip(t + shade * (np.abs(shade) > 0) * 0, -2, 2)
        t = np.where(seam | butt, -2, t + (shade == 1) * (~seam))
        return t
    return f


def tone_stones(size=5, seed=2, mortar=-2):
    """Cobble / ashlar: cells of ~size voxels with mortar lines and per-stone shade (2D on x/y)."""
    def f(x, y, z):
        row = np.floor(y / size)
        sh = (np.floor(x / size + (row % 2) * 0.5))
        cx = (x / size + (row % 2) * 0.5) % 1.0
        cy = (y / size) % 1.0
        edge = (cx < 1.0 / size) | (cy < 1.0 / size)
        s = np.floor(hash3(sh, row, 0, seed) * 3).astype(int) - 1
        return np.where(edge, mortar, s)
    return f


# ---- renderer ---------------------------------------------------------------------------------------------------------------
def _blur_grad(occ: np.ndarray, sigma: float):
    b = ndi.gaussian_filter(occ.astype(np.float32), sigma, mode="constant")
    g = np.stack(np.gradient(b))
    return b, g


def render(v: Vox, *, outline=True, rim=True, shadow=True, ao=True, bands=(0.40, 0.60, 0.82), pad=1,
           shear=K, ground_shadow=False) -> dict:
    """Bake the model. Returns {'img': RGBA uint8 (H, W, 4), 'pivot': (px, py) of the footprint centre bottom, 'depth': ...}."""
    X, Y, Z = v.X, v.Y, v.Z
    occ = v.mat > 0
    S = int(np.ceil(Z + shear * Y)) + 1               # number of screen rows
    s_idx = np.arange(S)
    hit_mat = np.zeros((X, S), np.uint8)
    hit_y = np.full((X, S), -1, np.int32)
    hit_z = np.zeros((X, S), np.int32)
    for yi in range(Y):
        zf = s_idx + 0.5 - shear * (yi + 0.5)
        zi = np.floor(zf).astype(np.int32)
        valid = (zi >= 0) & (zi < Z)
        zc = np.clip(zi, 0, Z - 1)
        m = v.mat[:, yi, :][:, zc]                   # (X, S)
        take = (m > 0) & valid[None, :] & (hit_y < 0)
        hit_mat[take] = m[take]
        hit_y[take] = yi
        hit_z[take] = np.broadcast_to(zc[None, :], (X, S))[take]
    hit = hit_y >= 0
    xs = np.broadcast_to(np.arange(X)[:, None], (X, S))
    hx, hy, hz = xs[hit], hit_y[hit], hit_z[hit]

    # normals from smoothed occupancy
    b1, g1 = _blur_grad(occ, 1.4)
    n = -np.stack([g1[0][hx, hy, hz], g1[1][hx, hy, hz], g1[2][hx, hy, hz]], axis=1)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = np.where(ln > 1e-4, n / np.maximum(ln, 1e-4), np.array([[0, -1.0, 0]], np.float32))
    lam = np.clip(n @ LIGHT, 0, 1)
    # cast shadows
    sh = np.ones(len(hx), np.float32)
    if shadow:
        p = np.stack([hx, hy, hz], axis=1).astype(np.float32) + 0.5 + n * 1.3
        alive = np.ones(len(hx), bool)
        for step in range(1, 90):
            q = p + LIGHT[None, :] * step
            qi = np.floor(q).astype(np.int32)
            inside = (qi[:, 0] >= 0) & (qi[:, 0] < X) & (qi[:, 1] >= 0) & (qi[:, 1] < Y) & (qi[:, 2] >= 0) & (qi[:, 2] < Z)
            if not inside.any():
                break
            idx = np.where(inside)[0]
            blocked = occ[qi[idx, 0], qi[idx, 1], qi[idx, 2]]
            sh[idx[blocked]] = 0.0
            alive &= inside
            if not alive.any():
                break
    aov = np.ones(len(hx), np.float32)
    if ao:
        b3 = ndi.gaussian_filter(occ.astype(np.float32), 3.0, mode="constant")
        p = np.stack([hx, hy, hz], axis=1).astype(np.float32) + 0.5 + n * 2.8
        pi = np.clip(np.floor(p).astype(np.int32), 0, [X - 1, Y - 1, Z - 1])
        aov = 1.0 - np.clip(b3[pi[:, 0], pi[:, 1], pi[:, 2]] * 1.5, 0, 0.55)
    amb = 0.42
    val = (amb + (1 - amb) * lam * (0.35 + 0.65 * sh) * (sh * 0.5 + 0.5)) * (0.55 + 0.45 * aov)
    val = np.where(sh < 0.5, np.minimum(val, 0.55), val)
    band = np.digitize(val, bands)                   # 0..3
    off = np.array([-2, -1, 0, 1])[band]

    # to palette
    H, W = S + 2 * pad, X + 2 * pad
    img = np.zeros((H, W, 4), np.uint8)
    ramp_id = np.full((H, W), -1, np.int32)
    step_img = np.zeros((H, W), np.int32)
    depth_img = np.full((H, W), 1e9, np.float32)
    mids = hit_mat[hit]
    tones = v.tone[hx, hy, hz].astype(np.int32)
    rows = (S - 1 - np.nonzero(hit)[1]) + pad         # flip: highest s at the top
    cols = np.nonzero(hit)[0] + pad
    for mid in np.unique(mids):
        mt = v.mats[int(mid)]
        sel = mids == mid
        if mt.emissive or mt.flat:
            st = np.full(sel.sum(), mt.base) + tones[sel]
        else:
            st = mt.base + off[sel] + tones[sel]
        st = np.clip(st, 0, 4)
        rid = RAMP_NAMES.index(mt.ramp)
        ramp_id[rows[sel], cols[sel]] = rid
        step_img[rows[sel], cols[sel]] = st
    depth_img[rows, cols] = hy.astype(np.float32)
    opaque = ramp_id >= 0

    flags = np.zeros((H, W), bool)                    # emissive pixels keep their step
    for mid, mt in v.mats.items():
        if mt.emissive or mt.flat:
            flags |= opaque & (hit_mat_img(hit_mat, hit, rows, cols, H, W) == mid)

    if rim:
        up = np.zeros_like(opaque)
        up[1:] = opaque[1:] & ~opaque[:-1]
        left = np.zeros_like(opaque)
        left[:, 1:] = opaque[:, 1:] & ~opaque[:, :-1]
        edge = (up | left) & ~flags
        step_img = np.where(edge, np.minimum(step_img + 1, 4), step_img)

    if outline:
        # depth edge: a pixel that lies clearly BEHIND its up/left neighbour gets a dark line (object overlap separation)
        dd = np.zeros((H, W), bool)
        for dy, dx in ((-1, 0), (0, -1), (0, 1), (1, 0)):
            nb = np.roll(depth_img, (dy, dx), axis=(0, 1))
            nbo = np.roll(opaque, (dy, dx), axis=(0, 1))
            dd |= opaque & nbo & ((depth_img - nb) > 5.0)
        step_img = np.where(dd & ~flags, 0, step_img)

    pal = np.array([RAMPS[n_] for n_ in RAMP_NAMES], np.uint8)       # (R, 5, 3)
    rid_c = np.clip(ramp_id, 0, None)
    img[..., :3] = pal[rid_c, step_img]
    img[..., 3] = np.where(opaque, 255, 0)

    if outline:
        grown = ndi.binary_dilation(opaque, structure=ndi.generate_binary_structure(2, 1)) & ~opaque
        # colour: ramp-0 of the darkest neighbouring ramp (prefers the pixel below/right = the object's own contact shadow)
        idx_near = ndi.distance_transform_edt(~opaque, return_distances=False, return_indices=True)
        near_r = ramp_id[idx_near[0], idx_near[1]]
        ol = pal[np.clip(near_r, 0, None), 0]
        img[grown, :3] = ol[grown]
        img[grown, 3] = 255
    pivot = (pad + X / 2.0, pad + (S - 1) - shear * (Y / 2.0))
    return {"img": img, "pivot": pivot, "px_h": Z, "shape": (H, W)}


def hit_mat_img(hit_mat, hit, rows, cols, H, W):
    out = np.zeros((H, W), np.uint8)
    out[rows, cols] = hit_mat[hit]
    return out


def crop(res: dict) -> dict:
    img = res["img"]
    a = img[..., 3] > 0
    ys, xs = np.where(a)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    px, py = res["pivot"]
    return {"img": img[y0:y1, x0:x1], "pivot": (px - x0, py - y0)}


def save(res: dict, path: Path, scale: int = 1) -> None:
    im = Image.fromarray(res["img"], "RGBA")
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


def count_colours(img: np.ndarray) -> int:
    a = img[..., 3] > 0
    return len({tuple(c) for c in img[a][:, :3]})
