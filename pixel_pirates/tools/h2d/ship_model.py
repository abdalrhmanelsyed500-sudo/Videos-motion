"""Reference 3D model of the sloop (Module H2D-0). Pure geometry, no rendering.

Local axes (metres): +x = bow (forward), +y = up, +z = starboard. Waterline is y = 0.
The model is the BAKING REFERENCE for the layered pixel sprites (decision D2): it is never shipped in the game.

build(trim_deg) -> list of triangles; each triangle is a dict:
    v: three (x, y, z) tuples      part: name      layer: "hull" | "sail"     uv: three (a, b) tuples (part-local, for stripes)
trim_deg is the signed boom angle in degrees: + swings the boom to starboard, - to port. Only the sail layer depends on it.
"""
from __future__ import annotations

import math

LENGTH = 22.0
STERN_X = -10.0
BOW_X = 12.0
BEAM_HALF = 3.1
MAST_X = 2.2
MAST_TOP_Y = 19.0
STATIONS = 16


def _lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _scale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    n = math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)


def half_beam(u: float) -> float:
    """Half-beam at station u in [0, 1] (0 = transom, 1 = bow)."""
    if u < 0.38:
        t = (0.38 - u) / 0.38
        return BEAM_HALF * (1.0 - 0.39 * t * t)
    t = (u - 0.38) / 0.62
    return max(0.12, BEAM_HALF * max(0.0, 1.0 - t ** 1.7) ** 0.85)


def sheer(u: float) -> float:
    """Height of the gunwale line above the waterline."""
    return 1.5 + 0.8 * (1.0 - u) ** 3 + 2.1 * u ** 3


class Mesh:
    def __init__(self):
        self.tris: list[dict] = []

    def tri(self, a, b, c, part, layer="hull", uv=((0, 0), (1, 0), (0, 1))):
        self.tris.append({"v": (a, b, c), "part": part, "layer": layer, "uv": uv})

    def quad(self, a, b, c, d, part, layer="hull"):
        """a-b-c-d in order; uv spans 0..1 across the quad."""
        self.tri(a, b, c, part, layer, ((0, 0), (1, 0), (1, 1)))
        self.tri(a, c, d, part, layer, ((0, 0), (1, 1), (0, 1)))

    def box(self, x0, x1, y0, y1, z0, z1, part, layer="hull", top_part=None):
        p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        self.quad(p[4], p[5], p[6], p[7], part, layer)  # starboard face
        self.quad(p[1], p[0], p[3], p[2], part, layer)  # port face
        self.quad(p[5], p[1], p[2], p[6], part, layer)  # bow face
        self.quad(p[0], p[4], p[7], p[3], part, layer)  # stern face
        self.quad(p[3], p[7], p[6], p[2], top_part or part, layer)  # top

    def prism(self, a, b, radius, sides, part, layer="hull"):
        """Straight prism between two points."""
        axis = _norm(_sub(b, a))
        ref = (0.0, 1.0, 0.0) if abs(axis[1]) < 0.9 else (1.0, 0.0, 0.0)
        u = _norm(_cross(axis, ref))
        v = _cross(axis, u)
        ring_a, ring_b = [], []
        for i in range(sides):
            ang = 2 * math.pi * i / sides
            off = _add(_scale(u, math.cos(ang) * radius), _scale(v, math.sin(ang) * radius))
            ring_a.append(_add(a, off))
            ring_b.append(_add(b, off))
        for i in range(sides):
            j = (i + 1) % sides
            self.quad(ring_a[i], ring_a[j], ring_b[j], ring_b[i], part, layer)

    def strip(self, a, b, width, part, layer="hull", up=(0.0, 1.0, 0.0)):
        """A thin flat ribbon (rope) from a to b, width across `up`."""
        axis = _norm(_sub(b, a))
        side = _norm(_cross(axis, up))
        w = _scale(side, width / 2.0)
        self.quad(_sub(a, w), _add(a, w), _add(b, w), _sub(b, w), part, layer)


def _hull(m: Mesh) -> None:
    n = STATIONS
    st = []
    for i in range(n + 1):
        u = i / n
        x = STERN_X + LENGTH * u
        b = half_beam(u)
        yd = sheer(u)
        st.append((x, b, yd))
    for i in range(n):
        x0, b0, y0 = st[i]
        x1, b1, y1 = st[i + 1]
        for s in (1.0, -1.0):
            wl0, wl1 = b0 * 0.80, b1 * 0.80
            top0, top1 = y0 + 1.15, y1 + 1.15
            # outer planking, waterline up to the wale
            a = (x0, 0.0, s * wl0)
            b = (x1, 0.0, s * wl1)
            c = (x1, y1 - 0.45, s * b1)
            d = (x0, y0 - 0.45, s * b0)
            (m.quad(a, b, c, d, "hull_side") if s > 0 else m.quad(b, a, d, c, "hull_side"))
            # wale (the lighter strake) and bulwark above it
            wa, wb = (x0, y0 - 0.45, s * b0), (x1, y1 - 0.45, s * b1)
            wc, wd = (x1, y1 + 0.05, s * b1), (x0, y0 + 0.05, s * b0)
            (m.quad(wa, wb, wc, wd, "wale") if s > 0 else m.quad(wb, wa, wd, wc, "wale"))
            ba, bb = (x0, y0 + 0.05, s * b0), (x1, y1 + 0.05, s * b1)
            bc, bd = (x1, top1, s * b1), (x0, top0, s * b0)
            (m.quad(ba, bb, bc, bd, "hull_side") if s > 0 else m.quad(bb, ba, bd, bc, "hull_side"))
            # rail cap and the inside face of the bulwark (visible on the far side)
            cap = 0.28
            ra, rb = (x0, top0, s * b0), (x1, top1, s * b1)
            rc, rd = (x1, top1, s * (b1 - cap)), (x0, top0, s * (b0 - cap))
            (m.quad(ra, rb, rc, rd, "rail") if s > 0 else m.quad(rb, ra, rd, rc, "rail"))
            ia, ib = (x0, top0, s * (b0 - cap)), (x1, top1, s * (b1 - cap))
            ic, idd = (x1, y1 - 0.5, s * (b1 - cap)), (x0, y0 - 0.5, s * (b0 - cap))
            (m.quad(ia, ib, ic, idd, "hull_inner") if s < 0 else m.quad(ib, ia, idd, ic, "hull_inner"))
        # deck between the inner faces
        da = (x0, y0 - 0.5, -(b0 - 0.28))
        db = (x1, y1 - 0.5, -(b1 - 0.28))
        dc = (x1, y1 - 0.5, (b1 - 0.28))
        dd = (x0, y0 - 0.5, (b0 - 0.28))
        m.quad(da, db, dc, dd, "deck")
    # transom
    x0, b0, y0 = st[0]
    m.quad((x0, 0.0, 0.8 * b0), (x0, 0.0, -0.8 * b0), (x0, y0 - 0.45, -b0), (x0, y0 - 0.45, b0), "hull_side")
    m.quad((x0, y0 - 0.45, b0), (x0, y0 - 0.45, -b0), (x0, y0 + 1.2, -b0), (x0, y0 + 1.2, b0), "hull_side")


def _deck_gear(m: Mesh) -> None:
    deck_y = lambda x: sheer((x - STERN_X) / LENGTH) - 0.5  # noqa: E731
    # stern cabin with a roof and two dark windows on its forward face
    cx0, cx1 = -9.0, -4.6
    y0 = deck_y(-7.0)
    m.box(cx0, cx1, y0, y0 + 2.2, -2.3, 2.3, "cabin")
    m.box(cx0 - 0.3, cx1 + 0.3, y0 + 2.2, y0 + 2.55, -2.6, 2.6, "roof")
    for zc in (-1.2, 1.2):
        m.quad((cx1 + 0.02, y0 + 0.9, zc + 0.5), (cx1 + 0.02, y0 + 0.9, zc - 0.5), (cx1 + 0.02, y0 + 1.7, zc - 0.5),
               (cx1 + 0.02, y0 + 1.7, zc + 0.5), "window")
    # main hatch and capstan
    hy = deck_y(-2.0)
    m.box(-3.0, -0.6, hy, hy + 0.7, -1.3, 1.3, "cabin", top_part="deck")
    m.box(8.4, 9.4, deck_y(8.9), deck_y(8.9) + 0.9, -0.5, 0.5, "mast")
    # six cannons, three a side, muzzles pointing out
    for x in (-3.8, 5.2, 7.2):
        for s in (1.0, -1.0):
            b = half_beam((x - STERN_X) / LENGTH)
            zc = s * (b - 0.95)
            y = deck_y(x)
            m.box(x - 0.55, x + 0.55, y, y + 0.55, min(zc, zc + s * 1.5), max(zc, zc + s * 1.5), "cannon")
    # stem post rising above the bow, and three barrels lashed beside the mast
    m.box(11.0, 11.9, sheer(0.95) - 0.5, sheer(0.95) + 2.3, -0.28, 0.28, "rail")
    for bx, bz in ((4.6, 1.4), (4.6, -1.4), (3.7, 1.9)):
        by = deck_y(bx)
        m.prism((bx, by, bz), (bx, by + 1.05, bz), 0.5, 8, "barrel")
    # bowsprit
    m.prism((9.4, deck_y(9.4) + 0.4, 0.0), (14.6, 2.1, 0.0), 0.26, 6, "mast")


def _rig(m: Mesh, trim_deg: float) -> None:
    deck_y = lambda x: sheer((x - STERN_X) / LENGTH) - 0.5  # noqa: E731
    mast_foot = (MAST_X, deck_y(MAST_X), 0.0)
    mast_top = (MAST_X, MAST_TOP_Y, 0.0)
    m.prism(mast_foot, mast_top, 0.42, 8, "mast")
    # fixed rigging (hull layer): shrouds, forestay, backstay
    for s in (1.0, -1.0):
        for dx in (-0.6, 0.9):
            x = MAST_X + dx
            b = half_beam((x - STERN_X) / LENGTH)
            m.strip((MAST_X, 14.0, 0.0), (x, sheer((x - STERN_X) / LENGTH) + 1.15, s * (b - 0.14)), 0.30, "rope", up=(1, 0, 0))
    m.strip(mast_top, (14.6, 2.1, 0.0), 0.30, "rope", up=(0, 0, 1))
    m.strip((MAST_X, 18.4, 0.0), (STERN_X + 0.4, sheer(0.0) + 1.15, 0.0), 0.30, "rope", up=(0, 0, 1))

    # ---- sail layer: boom, gaff, main sail, jib, pennant ------------------------------------------------------
    psi = math.radians(trim_deg)
    side = 1.0 if trim_deg >= 0 else -1.0
    aft = (-math.cos(psi), 0.0, math.sin(psi))
    boom_len = 11.2
    tack = (MAST_X, 3.9, 0.0)
    clew = _add(tack, _add(_scale(aft, boom_len), (0.0, 0.25, 0.0)))
    m.prism(tack, clew, 0.26, 6, "mast", "sail")
    gaff_len = 7.0
    throat = (MAST_X, 12.0, 0.0)
    peak = _add(throat, _add(_scale(aft, gaff_len * math.cos(math.radians(32))), (0.0, gaff_len * math.sin(math.radians(32)), 0.0)))
    m.prism(throat, peak, 0.22, 6, "mast", "sail")
    bulge = 1.2 * side if abs(trim_deg) > 1.0 else 0.4
    nu, nv = 6, 5
    perp = (math.sin(psi), 0.0, math.cos(psi))  # horizontal, perpendicular to the boom: the way the sail bellies

    def sail_pt(u, v):
        base = _lerp(_lerp(tack, clew, u), _lerp(throat, peak, u), v)
        k = bulge * math.sin(math.pi * u) * math.sin(math.pi * min(v * 1.0, 1.0) * 0.9 + 0.15)
        return _add(base, _scale(perp, k * side if abs(trim_deg) > 1.0 else k))

    for i in range(nu):
        for j in range(nv):
            u0, u1, v0, v1 = i / nu, (i + 1) / nu, j / nv, (j + 1) / nv
            a, b, c, d = sail_pt(u0, v0), sail_pt(u1, v0), sail_pt(u1, v1), sail_pt(u0, v1)
            part = "sail_band" if v1 <= 0.13 else "sail"
            m.tri(a, b, c, part, "sail", ((u0, v0), (u1, v0), (u1, v1)))
            m.tri(a, c, d, part, "sail", ((u0, v0), (u1, v1), (u0, v1)))
    # jib: tack on the bowsprit tip, head on the mast, clew swung by the jib sheet
    jt = (14.4, 2.2, 0.0)
    jh = (MAST_X + 0.5, 16.6, 0.0)
    jphi = psi * 0.8
    jc = (jt[0] - 6.8 * math.cos(jphi), 2.9, 6.8 * math.sin(jphi))
    jb = 0.9 * side if abs(trim_deg) > 1.0 else 0.3
    for i in range(4):
        for j in range(4):
            def pj(u, v):
                base = _lerp(_lerp(jt, jh, v), _lerp(jc, jh, v), u)
                k = jb * math.sin(math.pi * u) * math.sin(math.pi * v)
                return _add(base, _scale((math.sin(jphi), 0.0, math.cos(jphi)), k))
            u0, u1, v0, v1 = i / 4, (i + 1) / 4, j / 4, (j + 1) / 4
            m.tri(pj(u0, v0), pj(u1, v0), pj(u1, v1), "sail", "sail", ((u0, v0), (u1, v0), (u1, v1)))
            m.tri(pj(u0, v0), pj(u1, v1), pj(u0, v1), "sail", "sail", ((u0, v0), (u1, v1), (u0, v1)))
    # pennant at the masthead streams downwind (towards the side the sail is eased to)
    pang = math.radians(max(25.0, min(80.0, abs(trim_deg) if trim_deg else 25.0)))
    tip = (MAST_X - 3.4 * math.cos(pang), MAST_TOP_Y + 0.15, side * 3.4 * math.sin(pang))
    m.tri((MAST_X, MAST_TOP_Y + 0.5, 0.0), (MAST_X, MAST_TOP_Y - 0.5, 0.0), tip, "flag", "sail")
    m.tri((MAST_X, MAST_TOP_Y - 0.5, 0.0), (MAST_X, MAST_TOP_Y + 0.5, 0.0), tip, "flag", "sail")


def build(trim_deg: float = 0.0) -> list[dict]:
    m = Mesh()
    _hull(m)
    _deck_gear(m)
    _rig(m, trim_deg)
    return m.tris
