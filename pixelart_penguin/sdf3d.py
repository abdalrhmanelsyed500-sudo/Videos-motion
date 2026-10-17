"""Tiny orthographic SDF ray-marcher that renders a 3D-modelled character straight onto a 64x64 pixel grid,
then converts it into REAL pixel art: per-material 5-tone ramps, toon (banded) light from top-left, 1px selective outline,
internal separation lines, no anti-aliasing, no resampling.   World: x right, y up, z away from camera (north)."""
import numpy as np

def Rx(a): c, s = np.cos(a), np.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def Ry(a): c, s = np.cos(a), np.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def Rz(a): c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
def D(a): return np.deg2rad(a)
def V(*a): return np.array(a, float)

class Frame:
    def __init__(s, R=None, t=None): s.R = np.eye(3) if R is None else R; s.t = np.zeros(3) if t is None else np.array(t, float)
    def ap(s, p): return s.R @ np.asarray(p, float) + s.t
    def comp(s, o): return Frame(s.R @ o.R, s.R @ o.t + s.t)       # s o o
    def about(s, pivot):   # rotate about pivot given in parent coords
        pv = np.asarray(pivot, float); return Frame(s.R, s.t + pv - s.R @ pv)
def local(R=None, t=None, pivot=None):
    f = Frame(R, t)
    if pivot is not None: f = Frame(f.R, f.t + np.asarray(pivot, float) - f.R @ np.asarray(pivot, float))
    return f

def smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0) / k; return np.minimum(a, b) - h * h * k * .25

PART_ID = {}
class Prim:
    def __init__(s, kind, mat, part, **kw): s.kind, s.mat = kind, mat; s.part = PART_ID.setdefault(part, len(PART_ID)); s.__dict__.update(kw); s.group = kw.get('group'); s.mat_fn = kw.get('mat_fn')

class Scene:
    def __init__(s): s.prims = []
    def ell(s, fr, c, r, mat, part, rot=None, **kw):
        R = fr.R if rot is None else fr.R @ rot; s.prims.append(Prim('ell', mat, part, c=fr.ap(c), M=R, r=np.array(r, float), **kw))
    def cap(s, fr, a, b, ra, rb, mat, part, **kw): s.prims.append(Prim('cap', mat, part, a=fr.ap(a), b=fr.ap(b), ra=ra, rb=rb, **kw))
    def box(s, fr, c, h, mat, part, rot=None, rnd=.4, **kw):
        R = fr.R if rot is None else fr.R @ rot; s.prims.append(Prim('box', mat, part, c=fr.ap(c), M=R, h=np.array(h, float), rnd=rnd, **kw))
    def band(s, fr, c, r, y0, w, mat, part, rot=None, **kw):   # ellipsoid shell clipped to a horizontal slab (belts, bandanas, vests)
        R = fr.R if rot is None else fr.R @ rot; s.prims.append(Prim('band', mat, part, c=fr.ap(c), M=R, r=np.array(r, float), y0=y0, w=w, **kw))

    def _d(s, pr, P):
        if pr.kind in ('ell', 'band', 'box'):
            q = (P - pr.c) @ pr.M
            if pr.kind == 'box':
                qq = np.abs(q) - pr.h + pr.rnd; return np.linalg.norm(np.maximum(qq, 0), axis=1) + np.minimum(qq.max(1), 0) - pr.rnd
            k0 = np.linalg.norm(q / pr.r, axis=1); k1 = np.linalg.norm(q / (pr.r ** 2), axis=1)
            d = k0 * (k0 - 1) / np.maximum(k1, 1e-6)
            if pr.kind == 'band': d = np.maximum(d, np.abs(q[:, 1] - pr.y0) - pr.w)
            return d
        pa = P - pr.a; ba = pr.b - pr.a; h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
        return np.linalg.norm(pa - h[:, None] * ba, axis=1) - (pr.ra + (pr.rb - pr.ra) * h)

    def eval(s, P, ids=False):
        ds = np.stack([s._d(p, P) for p in s.prims]); d = ds.copy(); out = None
        groups = {}
        for i, p in enumerate(s.prims):
            if p.group: groups.setdefault(p.group, []).append(i)
        keep = np.ones(len(s.prims), bool)
        res = []
        for g, mem in groups.items():
            gd = ds[mem[0]]
            for j in mem[1:]: gd = smin(gd, ds[j], getattr(s.prims[j], 'k', 3.0))
            res.append(gd); keep[mem] = False
        base = ds[keep]; allp = np.concatenate([base] + [r[None] for r in res]) if res else base
        dist = allp.min(0)
        return (dist, ds.argmin(0)) if ids else dist

CAM_PITCH = D(44)
def render(scene, W=64, H=64, cx=32, cy=52, pitch=CAM_PITCH, want_shadow=True, light=(-.55, .75, -.38)):
    ph = pitch; d = V(0, -np.sin(ph), np.cos(ph)); up = V(0, np.cos(ph), np.sin(ph)); T = 160.0
    jj, ii = np.mgrid[0:H, 0:W]; u = (ii + .5 - cx).ravel(); v = (cy - (jj + .5)).ravel()
    O = u[:, None] * V(1, 0, 0) + v[:, None] * up - T * d
    N = len(u); t = np.full(N, T - 70.0); hit = np.zeros(N, bool); act = np.arange(N)
    for it in range(70):
        if not len(act): break
        P = O[act] + t[act, None] * d; dist = scene.eval(P)
        h = dist < .06; hit[act[h]] = True
        t[act] += np.maximum(dist, .02) * .92
        alive = ~h & (t[act] < T + 70); act = act[alive]
    P = O + t[:, None] * d; res = {}
    hp = np.where(hit)[0]; Ph = P[hp]
    _, idx = scene.eval(Ph, ids=True)
    e = .12; k = [V(1, -1, -1), V(-1, -1, 1), V(-1, 1, -1), V(1, 1, 1)]
    nrm = sum(kk[None] * scene.eval(Ph + kk[None] * e)[:, None] for kk in k)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    L = V(*light); L = L / np.linalg.norm(L)
    lam = nrm @ L
    mats = np.zeros(N, int) - 1; part = np.zeros(N, int) - 1; lamf = np.zeros(N); dep = np.full(N, 1e9)
    for j, pr in enumerate(scene.prims):
        sel = idx == j
        if not sel.any(): continue
        g = hp[sel]
        if pr.mat_fn is not None: mats[g] = pr.mat_fn((Ph[sel] - pr.c) @ pr.M, nrm[sel] @ pr.M)
        else: mats[g] = pr.mat
        part[g] = pr.part
    lamf[hp] = lam; dep[hp] = t[hp]
    rs = lambda a: a.reshape(H, W)
    # shadow on ground
    sh = np.zeros(N, bool)
    if want_shadow:
        gi = np.where(~hit)[0]
        # ground point under pixel: ray hits y=0
        tg = -O[gi, 1] / d[1]; G = O[gi] + tg[:, None] * d
        ok = (np.abs(G[:, 0]) < 40) & (G[:, 2] > -40) & (G[:, 2] < 40)
        gi = gi[ok]; G = G[ok]
        Ls = V(-.18, 1.0, -.12); Ls = Ls / np.linalg.norm(Ls); ts = np.full(len(gi), 1.0); occ = np.zeros(len(gi), bool); a2 = np.arange(len(gi))
        for it in range(26):
            if not len(a2): break
            dist = scene.eval(G[a2] + ts[a2, None] * Ls + V(0, .0, 0)); h = dist < .15; occ[a2[h]] = True
            ts[a2] += np.maximum(dist, .5); a2 = a2[~h & (ts[a2] < 70)]
        sh[gi[occ]] = True
    return dict(hit=rs(hit), mat=rs(mats), part=rs(part), lam=rs(lamf), depth=rs(dep), shadow=rs(sh), O=O, d=d, up=up)

def to_pixels(r, ramps, thresholds=(-.05, .35, .72, .93), edge_pairs=None, edge_thr=2.5, flash=None):
    H, W = r['hit'].shape; hit = r['hit']; mat = r['mat']; lam = r['lam']
    lvl = np.full((H, W), 2, int)
    lvl[lam < thresholds[0]] = 1 if False else 1
    lvl = np.where(lam < thresholds[1], 1, np.where(lam < thresholds[2], 2, np.where(lam < thresholds[3], 3, 4)))
    lvl = np.where(lam < thresholds[0] - .35, 1, lvl)
    rgb = np.zeros((H, W, 3), np.uint8); fill = hit.copy()
    for y in range(H):
        for x in range(W):
            if hit[y, x]: rgb[y, x] = ramps[mat[y, x]][lvl[y, x]]
    return rgb, fill, lvl
