"""CP-1 revision: the plan of Anvil Harbor, the capital (docs/CP1_CITY_PLAN.md is the written district plan this file implements).

World axes: x east, z south (the sea is at +z); the camera looks north, so every front faces south. Heights in metres.
The city rises in four terraces from the quay (1.95 m) to Governor's Hill (12.5 m):
  A  the Lower Town       z   +8 .. -104   gentle slope 1.95 -> 5.0 m: Quay, Chandlers' Street, Market Square, Merchants' Row
  B  Hill Road terrace    z -107 .. -150   7.4 m
  C  Terrace Walk         z -152 .. -196   9.9 m: the mansions
  D  Governor's Hill      z -198 .. -266   12.5 m: forecourt, palace, town hall, barracks, treasury, gardens
Retaining walls at z -106, -151, -197; stairs at the five N-S ways. The north wall (z -270) closes the town with two gates.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy import ndimage

import cay_terrain as CT

SLABS, PAVER, STEPS, WALLC = 12, 13, 14, 15
EARTH, COBBLE, MEADOW, SAND = CT.EARTH, CT.COBBLE, CT.MEADOW, CT.SAND

BOX = dict(x0=-198.0, x1=198.0, z0=-270.0, z1=30.0)
CLEAR_BOX = (-206.0, -282.0, 206.0, 14.0)
WALLS_Z = (-106.0, -151.0, -197.0)
# terrace heights, north -> south (z ascending); stairs ramp over 12 m, walls step over 2 m
Z_WALL = [-270.0, -198.0, -196.0, -152.0, -150.0, -107.0, -105.0, -26.0, 40.0]
H_WALL = [12.5, 12.5, 9.9, 9.9, 7.4, 7.4, 5.0, 1.95, 1.95]
Z_STAIR = [-270.0, -203.0, -191.0, -157.0, -145.0, -112.0, -100.0, -26.0, 40.0]
STAIRS = [(16.0, 16.0), (-28.0, 6.0), (62.0, 6.0), (-150.0, 6.0), (140.0, 6.0)]     # x centre, width

# E-W streets: name, z centre, width, x0, x1
STREETS = [("Quay Street", 0.0, 8.0, -198.0, 198.0), ("Chandlers' Street", -44.0, 6.0, -198.0, 198.0),
           ("Merchants' Row", -86.0, 6.0, -198.0, 198.0), ("Hill Road", -113.0, 6.0, -198.0, 198.0),
           ("Terrace Walk", -158.0, 6.0, -198.0, 198.0)]
# N-S lanes: x centre, width, z0 (north end), z1 (south end)
LANES = [("West Lane", -28.0, 6.0, -266.0, -44.0), ("East Lane", 62.0, 6.0, -266.0, -44.0),
         ("Far West Lane", -150.0, 6.0, -266.0, -44.0), ("Far East Lane", 140.0, 6.0, -266.0, -44.0),
         ("Net Lane", -112.0, 5.0, -44.0, 10.0), ("Shore Lane", 112.0, 5.0, -44.0, 10.0)]
AVENUE = dict(x0=8.0, x1=24.0, z0=-199.0, z1=-4.0, walk=4.0)
PLAZAS = {"customs_square": (-2.0, -4.2, 34.0, 3.4), "market_square": (-14.0, -84.0, 46.0, -56.0), "forecourt": (-34.0, -214.0, 66.0, -199.0)}
FORBID_X_COLUMNS = [(-31.0, -25.0), (59.0, 65.0), (-153.0, -147.0), (137.0, 143.0), (4.0, 28.0)]
FISH_ROW = (-127.0, -52.0, -43.0, 14.0)
CANAL_BOX = (-52.0, -16.0, -38.0, 80.0)


def interp_col(z, zs, hs):
    return np.interp(z, zs, hs).astype(np.float32)


def window_idx(x0, z0, x1, z1):
    ix0 = int(max((x0 - CT.X0) / CT.CELL, 0)); ix1 = int(min((x1 - CT.X0) / CT.CELL, CT.N))
    iz0 = int(max((z0 - CT.Z0) / CT.CELL, 0)); iz1 = int(min((z1 - CT.Z0) / CT.CELL, CT.N))
    return ix0, ix1, iz0, iz1


def shape(h: np.ndarray, T) -> np.ndarray:
    """Terrace the land under the city; the beach and the sea are left alone."""
    ix0, ix1, iz0, iz1 = window_idx(BOX["x0"] - 40, BOX["z0"] - 40, BOX["x1"] + 40, BOX["z1"] + 20)
    xs = CT.XS[ix0:ix1][None, :]
    zs = CT.ZS[iz0:iz1]
    zc = zs[:, None]
    hn = interp_col(zs, Z_WALL, H_WALL)[:, None] * np.ones_like(xs)
    hs_ = interp_col(zs, Z_STAIR, H_WALL)[:, None] * np.ones_like(xs)
    stair = np.zeros(hn.shape, bool)
    for sx, sw in STAIRS:
        stair |= np.abs(xs - sx) <= sw * 0.5
    ht = np.where(stair, hs_, hn)
    d = np.maximum(np.maximum(BOX["x0"] - xs, xs - BOX["x1"]), np.maximum(BOX["z0"] - zc, zc - BOX["z1"]))
    wc = np.clip(1.0 - d / 16.0, 0.0, 1.0)
    wc = wc * wc * (3 - 2 * wc)
    sub = h[iz0:iz1, ix0:ix1]
    wl = np.clip((sub - 0.25) / 1.05, 0.0, 1.0)
    out = h.copy()
    out[iz0:iz1, ix0:ix1] = sub + (ht - sub) * wc * wl
    return out


def box_mask(x0, z0, x1, z1):
    return CT.box(x0, z0, x1, z1)


def paint(cls: np.ndarray, land: np.ndarray, h: np.ndarray) -> np.ndarray:
    """City ground classes (called after the island classes and the old paths)."""
    cls = cls.copy()
    inside = CT.box(BOX["x0"], BOX["z0"], BOX["x1"], BOX["z1"]) & land & (h > 1.6)
    fish = CT.box(*FISH_ROW)
    cls = np.where(inside & (cls != COBBLE) & ~fish, EARTH, cls)
    # lawns of the mansion terrace and the palace gardens
    for x0, z0, x1, z1 in ((-196.0, -196.0, 196.0, -172.0), (-196.0, -266.0, 196.0, -236.0)):
        cls = np.where(CT.box(x0, z0, x1, z1) & inside, MEADOW, cls)
    ix0, ix1, iz0, iz1 = window_idx(BOX["x0"] - 5, BOX["z0"] - 5, BOX["x1"] + 5, BOX["z1"] + 5)
    for _n, zc, w, x0, x1 in STREETS:
        cls = np.where(CT.box(x0, zc - w / 2, x1, zc + w / 2) & land & ~fish & (h > 1.0), COBBLE, cls)
    for _n, xc, w, z0, z1 in LANES:
        cls = np.where(CT.box(xc - w / 2, z0, xc + w / 2, z1) & land & ~fish & (h > 1.0), COBBLE, cls)
    # Anchor Avenue: slabs between brick pavements
    cls = np.where(CT.box(AVENUE["x0"] - AVENUE["walk"], AVENUE["z0"], AVENUE["x1"] + AVENUE["walk"], AVENUE["z1"]) & land, PAVER, cls)
    cls = np.where(CT.box(AVENUE["x0"], AVENUE["z0"], AVENUE["x1"], AVENUE["z1"]) & land, SLABS, cls)
    for name, (x0, z0, x1, z1) in PLAZAS.items():
        cls = np.where(CT.box(x0, z0, x1, z1) & land, SLABS, cls)
    # a brick waterfront promenade east of the plaza
    cls = np.where(CT.box(34.0, -4.0, 130.0, 3.0) & land & (h > 1.2), PAVER, cls)
    cls = np.where(CT.box(CT.PLAZA[0] - 1.0, CT.PLAZA[1] + 0.0, CT.PLAZA[2] + 1.0, CT.PLAZA[3]) & land, SLABS, cls)
    # retaining walls and stairs (stairs win)
    for zw in WALLS_Z:
        wall_band = CT.box(BOX["x0"], zw - 2.6, BOX["x1"], zw + 1.0) & land
        cls = np.where(wall_band, WALLC, cls)
        for sx, sw in STAIRS:
            cls = np.where(CT.box(sx - sw / 2, zw - 6.0, sx + sw / 2, zw + 6.0) & land, STEPS, cls)
    # the north wall's footing
    cls = np.where(CT.box(BOX["x0"], BOX["z0"] - 2.0, BOX["x1"], BOX["z0"] + 2.0) & land, WALLC, cls)
    return cls


# ---- placement ---------------------------------------------------------------------------------------------------------------
@dataclass
class Placed:
    atlas: str
    name: str
    x: float
    z: float          # front base
    w: float
    d: float
    h: float
    solid: bool = True


@dataclass
class City:
    h: np.ndarray
    cls: np.ndarray
    land: np.ndarray
    rs: np.random.RandomState
    placed: list = field(default_factory=list)
    props: list = field(default_factory=list)          # (atlas, name, x, z, w, d, solid)
    trees: list = field(default_factory=list)          # (veg type, x, z, scale, trunk_r)
    places: list = field(default_factory=list)         # map entries
    spots: dict = field(default_factory=dict)          # named positions for NPCs: id -> (x, z, facing)
    rects: list = field(default_factory=list)          # forbidden / placed footprints (x0, z0, x1, z1)

    # -- tools --
    def ground(self, x, z):
        iz = int(min(max((z - CT.Z0) / CT.CELL, 0), CT.N - 1)); ix = int(min(max((x - CT.X0) / CT.CELL, 0), CT.N - 1))
        return float(self.h[iz, ix])

    def is_land(self, x, z, hmin=1.5):
        return self.ground(x, z) >= hmin

    def free(self, r, margin=0.5, need_land=True):
        x0, z0, x1, z1 = r
        if x0 < BOX["x0"] + 3 or x1 > BOX["x1"] - 3 or z0 < BOX["z0"] + 4 or z1 > BOX["z1"]:
            return False
        for fx0, fz0, fx1, fz1 in self.rects:
            if x0 < fx1 + margin and x1 > fx0 - margin and z0 < fz1 + margin and z1 > fz0 - margin:
                return False
        if need_land:
            for px in (x0, (x0 + x1) / 2, x1):
                for pz in (z0, z1, z1 + 2.0):
                    if not self.is_land(px, pz, 1.7):
                        return False
        return True

    def put(self, atlas, name, x, z, w, d, h, solid=True, force=False):
        r = (x - w / 2, z - d, x + w / 2, z)
        if not force and not self.free(r):
            return None
        self.rects.append(r)
        p = Placed(atlas, name, x, z, w, d, h, solid)
        self.placed.append(p)
        return p

    def prop(self, atlas, name, x, z, w=1.0, d=0.6, solid=True):
        self.props.append((atlas, name, x, z, w, d, solid))

    def forbid(self, r):
        self.rects.append(r)


def pools():
    import city_art as CA
    from city_art import smalls
    return None


SMALL_W = {}


def register_sizes(smalls_list, grands_list):
    for n, w, d, h, _a in smalls_list:
        SMALL_W[n] = ("bld", w, d, h)
    for n, w, d, h, _a in grands_list:
        SMALL_W[n] = ("grand", w, d, h)


POOLS = {
    "fisher": [("cottage_thatch", 3), ("cottage_tile", 3), ("fisher_cottage", 4), ("fisher_cottage_tar", 3), ("house_plaster", 1), ("rowhouse", 1)],
    "home": [("house_plaster", 3), ("house_half", 3), ("house_brick", 3), ("house_rose", 2), ("house_blue", 2), ("house_green", 2), ("house_ochre", 2),
             ("tall_brick", 2), ("tall_white", 2), ("tall_sand", 2), ("tall_rose", 1), ("tall_blue", 1), ("rowhouse", 1)],
    "shops": [("shop_baker", 2), ("shop_chandler", 2), ("shop_cloth", 2), ("shop_cooper", 2), ("shop_sailmaker", 2), ("shop_fishmonger", 1),
              ("shop_provisioner", 2), ("smithy", 1), ("carpenter", 1), ("house_plaster", 1), ("house_half", 1), ("tall_sand", 1), ("tall_white", 1)],
    "merchant": [("tall_brick", 3), ("tall_white", 3), ("tall_sand", 3), ("tall_rose", 2), ("tall_blue", 2), ("house_brick", 2), ("house_half", 1),
                 ("shop_cloth", 1), ("house_ochre", 1)],
    "docks": [("warehouse_timber", 3), ("warehouse_brick", 3), ("warehouse_tar", 2), ("shop_cooper", 1), ("shop_chandler", 1), ("house_brick", 1)],
    "mansion": [("mansion_white", 3), ("mansion_rose", 3), ("mansion_ochre", 2), ("mansion_stone", 3)],
}


def pick(rs, pool):
    names = [n for n, _w in POOLS[pool]]
    w = np.array([w for _n, w in POOLS[pool]], float)
    return names[int(rs.choice(len(names), p=w / w.sum()))]


def row(city: City, z_front, x0, x1, pool, gap=(0.7, 2.2), skip=(), tag=""):
    """Fill the line z = z_front from x0 to x1 with buildings of `pool`. Anything that does not fit (water, lane, plaza) is skipped."""
    rs = city.rs
    x = x0
    out = []
    while x < x1:
        name = pick(rs, pool)
        atlas, w, d, h = SMALL_W[name]
        xc = x + w / 2
        if any(a - w / 2 - 0.2 < xc < b + w / 2 + 0.2 for a, b in FORBID_X_COLUMNS) or any(a - w / 2 < xc < b + w / 2 for a, b in skip):
            x += 2.0
            continue
        p = city.put(atlas, name, xc, z_front, w, d, h)
        if p is not None:
            out.append(p)
            x += w + float(rs.uniform(*gap))
        else:
            x += 2.5
    return out


# ---- the plan ----------------------------------------------------------------------------------------------------------------
GATES = [("West Gate", -110.0), ("East Gate", 120.0)]


def plan(h, cls, land, rs) -> City:
    import city_people as PP
    city = City(h=h, cls=cls, land=land, rs=rs)
    # ---- no-build zones --------------------------------------------------------------------------------------------------
    for (x0, x1) in FORBID_X_COLUMNS + [(-114.5, -109.5), (109.5, 114.5)]:
        city.forbid((x0, -272.0, x1, 12.0))
    for x0, z0, x1, z1 in PLAZAS.values():
        city.forbid((x0, z0, x1, z1))
    city.forbid(FISH_ROW)
    city.forbid(CANAL_BOX)
    city.forbid((-36.0, -30.0, -19.0, -4.0))                    # Garrick's boatyard
    city.forbid((-10.0, 4.0, 40.0, 60.0))                       # the pier and the cove mouth
    for zw in WALLS_Z:
        city.forbid((-200.0, zw - 3.2, 200.0, zw + 1.6))
    for _n, zc, w, x0, x1 in STREETS:
        city.forbid((x0, zc - w / 2 - 0.2, x1, zc + w / 2 + 0.2))
    city.forbid((-34.0, -230.0, 66.0, -199.0))                  # palace forecourt and the palace itself (placed by hand below)
    spots = city.spots

    def key(atlas, name, x, z, label=None, tries=None, **kw):
        w = SMALL_W[name]
        cands = tries or [(x, z)]
        for cx, cz in cands:
            p = city.put(w[0], name, cx, cz, w[1], w[2], w[3], force=kw.get("force", False))
            if p is not None:
                return p
        print("  WARNING: could not place", name, cands[:2])
        return None

    # ---- the key buildings ----------------------------------------------------------------------------------------------
    # palace first (it overlaps its own forbid box)
    pal = city.put("grand", "palace", 16.0, -216.0, 25.5, 14.0, 16.0, force=True)
    city.put("grand", "town_hall", -62.0, -216.0, 20.8, 10.0, 11.0, force=True)
    city.put("grand", "barracks", 94.0, -216.0, 19.4, 9.0, 9.0, force=True)
    city.put("grand", "counting_house", 122.0, -216.0, 14.6, 8.0, 10.5, force=True)
    city.put("grand", "customs_house", -10.0, -6.5, 17.4, 10.0, 10.0, force=True)
    city.put("grand", "guild_hall", -13.0, -90.4, 16.7, 9.0, 8.5, force=True)
    city.put("grand", "counting_house", 46.0, -90.4, 14.6, 8.0, 10.5, force=True)
    harbourm = city.put("bld", "house_brick", 33.0, -6.2, 8.0, 6.5, 8.0, force=True)
    tav = city.put("bld", "tavern_anchor", 50.0, -6.2, 13.0, 8.0, 11.0, force=True)
    inn = city.put("bld", "inn_gilded", 76.0, -6.2, 11.0, 7.5, 10.0, force=True)
    yard = None
    for zz in (14.0, 12.0, 10.0, 8.0, 6.0, 4.0, 0.0, -4.0):
        for xx in (132.0, 128.0, 124.0, 136.0):
            yard = city.put("grand", "shipyard_shed", xx, zz, 22.2, 10.0, 8.0)
            if yard:
                break
        if yard:
            break
    fort = None
    for zz in (10.0, 8.0, 12.0, 6.0, 14.0, 4.0):
        for xx in (170.0, 166.0, 174.0, 176.0, 162.0):
            fort = city.put("grand", "fort_bastion", xx, zz, 22.9, 6.0, 6.5)
            if fort:
                break
        if fort:
            break
    # walls: the north wall with two gates, the east and west walls of end-on posts
    wz = BOX["z0"] + 1.5
    for name, gx in GATES:
        city.put("bld", "wall_gate", gx, wz, 12.4, 5.0, 8.0, solid=False, force=True)
        city.put("bld", "wall_tower", gx - 9.5, wz, 6.4, 6.4, 9.5, force=True)
        city.put("bld", "wall_tower", gx + 9.5, wz, 6.4, 6.4, 9.5, force=True)
    city.put("bld", "wall_tower", BOX["x0"] + 3.0, wz, 6.4, 6.4, 9.5, force=True)
    city.put("bld", "wall_tower", BOX["x1"] - 3.0, wz, 6.4, 6.4, 9.5, force=True)
    x = BOX["x0"] + 8.0
    while x < BOX["x1"] - 8.0:
        if all(abs(x - gx) > 16.5 for _n, gx in GATES):
            city.put("bld", "wall_straight", x + 6.3, wz, 12.6, 2.4, 5.5, force=True)
            x += 12.6
        else:
            x += 1.0
    for side, wx in (("west", BOX["x0"] + 1.0), ("east", BOX["x1"] - 1.0)):
        z = BOX["z0"] + 6.0
        while z < BOX["z1"]:
            if city.ground(wx, z) < 0.45:
                break
            city.put("bld", "wall_post", wx, z, 2.6, 2.4, 4.5, force=True)
            z += 2.1
    # ---- the rows ------------------------------------------------------------------------------------------------------
    sq = [(-17.0, 49.0)]
    row(city, -5.8, BOX["x0"] + 4, -128.0, "fisher", tag="quay_w")
    row(city, -26.0, BOX["x0"] + 4, -128.0, "fisher", tag="quay_w2")
    row(city, -31.0, -126.0, -44.0, "fisher", tag="fishrow_back")
    row(city, -7.0, 88.0, BOX["x1"] - 4, "docks", tag="quay_e")
    row(city, -28.0, 38.0, 108.0, "docks", tag="east_docks")
    row(city, -28.0, 116.0, BOX["x1"] - 4, "home", tag="east_homes")
    row(city, -48.4, BOX["x0"] + 4, -131.0, "fisher", skip=sq, tag="b1w")
    row(city, -48.4, -131.0, 100.0, "shops", skip=sq, tag="b1c")
    row(city, -48.4, 100.0, BOX["x1"] - 4, "home", skip=sq, tag="b1e")
    row(city, -66.0, BOX["x0"] + 4, BOX["x1"] - 4, "home", skip=sq, tag="b2")
    row(city, -90.4, BOX["x0"] + 4, BOX["x1"] - 4, "merchant", tag="c1")
    row(city, -117.4, BOX["x0"] + 4, BOX["x1"] - 4, "home", tag="hill1")
    row(city, -136.0, BOX["x0"] + 4, BOX["x1"] - 4, "home", tag="hill2")
    row(city, -162.8, BOX["x0"] + 4, BOX["x1"] - 4, "mansion", gap=(3.0, 6.0), tag="mansions")
    row(city, -216.0, BOX["x0"] + 4, -76.0, "mansion", gap=(4.0, 8.0), tag="hill_w")
    row(city, -216.0, 134.0, BOX["x1"] - 4, "mansion", gap=(4.0, 8.0), tag="hill_e")
    row(city, -238.0, BOX["x0"] + 4, -40.0, "home", gap=(6.0, 14.0), tag="hill_back_w")
    row(city, -238.0, 40.0, BOX["x1"] - 4, "home", gap=(6.0, 14.0), tag="hill_back_e")
    # ---- trees, hedges and clutter -------------------------------------------------------------------------------------
    def tree(t, x, z, s=1.0, r=0.0):
        if city.ground(x, z) < 1.7:
            return
        rr = (x - 0.9, z - 0.9, x + 0.9, z + 0.9)
        if not city.free(rr, margin=0.6, need_land=False):
            return
        city.rects.append(rr)
        city.trees.append((t, x, z, s, r))
    # palms down the avenue, lamps between them
    for z in np.arange(-14.0, -196.0, -9.0):
        if any(abs(z - zw) < 7.5 for zw in WALLS_Z):
            continue
        for x in (9.4, 22.6):
            tree(int(rs.choice([0, 1, 7])), x, float(z) + (0.0 if x < 16 else 1.5), 0.95, 0.5)
    for z in np.arange(-22.0, -196.0, -18.0):
        if any(abs(z - zw) < 7.5 for zw in WALLS_Z):
            continue
        for x in (9.4, 22.6):
            city.prop("street", "lamp_iron", x, float(z) + 4.0, 0.7, 0.7, True)
    # lamps along the E-W streets (south edge)
    for _n, zc, w, x0, x1 in STREETS:
        for x in np.arange(x0 + 10.0, x1 - 6.0, 24.0):
            z = zc + w / 2 + 0.4
            if any(a < x < b for a, b in FORBID_X_COLUMNS) or city.ground(float(x), z) < 1.7:
                continue
            if FISH_ROW[0] < x < FISH_ROW[2] and FISH_ROW[1] < z < FISH_ROW[3]:
                continue
            city.prop("street", "lamp_iron", float(x), z, 0.7, 0.7, True)
    # gardens: palms, bushes and flower bushes on the two lawns
    for x0, z0, x1, z1, n in ((-194, -194, 194, -176, 110), (-194, -264, 194, -240, 90)):
        for _ in range(n):
            x, z = float(rs.uniform(x0, x1)), float(rs.uniform(z0, z1))
            if CT.box(-34, -230, 66, -199)[int((z - CT.Z0) / 2), int((x - CT.X0) / 2)]:
                continue
            tree(int(rs.choice([0, 1, 7, 4, 4, 10, 10])), x, z, float(rs.uniform(0.85, 1.15)), 0.5)
    # market square: stalls around a fountain, benches, tubs
    msq = PLAZAS["market_square"]
    city.prop("civic", "fountain", 16.0, -65.0, 6.0, 4.0, True)
    stall_types = ["stall_red", "stall_blue", "stall_green", "stall_fruit"]
    k = 0
    for z in (-53.0, -78.0):
        for x in (-6.0, 4.0, 28.0, 38.0):
            city.prop("stall", stall_types[k % 4], x, z, 4.2, 1.4, True)
            spots["stall_%d" % k] = (x, z + 2.4, 0)
            k += 1
    for x in (-9.0, 41.0):
        city.prop("stall", "bench", x, -65.0, 3.4, 1.0, True)
        city.prop("street", "tub_bush", x + (3 if x < 0 else -3), -60.0, 1.4, 1.0, True)
        city.prop("street", "tub_bush", x + (3 if x < 0 else -3), -70.0, 1.4, 1.0, True)
    city.prop("stall", "bench", 16.0, -75.0, 3.4, 1.0, True)
    city.prop("stall", "bench", 16.0, -55.0, 3.4, 1.0, True)
    # customs square: the Anvil, a notice and lamps (the old ones keep the light sources)
    city.prop("civic", "anvil_monument", 6.5, -0.8, 3.4, 2.4, True)
    for (x, z) in ((3.0, -2.5), (29.0, -2.0), (26.0, -3.0), (18.6, -9.0)):
        city.prop("street", "lamp_iron", x, z, 0.6, 0.6, True)
    city.prop("civic", "dock_crane", -13.0, 6.8, 5.0, 2.0, True)
    city.prop("civic", "dock_crane", 96.0, 7.0, 5.0, 2.0, True)
    # the palace forecourt
    city.prop("civic", "statue", 16.0, -203.0, 3.0, 2.0, True)
    for dx in (-26.0, -14.0, 14.0, 26.0):
        city.prop("street", "lamp_iron", 16.0 + dx, -207.0, 0.6, 0.6, True)
    for dx in (-30.0, 30.0):
        city.prop("street", "tub_bush", 16.0 + dx, -212.0, 1.4, 1.0, True)
    city.prop("civic", "fountain", 16.0, -250.0, 6.0, 4.0, True)
    for dx in (-10.0, 10.0):
        city.prop("stall", "bench", 16.0 + dx, -245.0, 3.4, 1.0, True)
    city.prop("civic", "statue", -110.0, -184.0, 3.0, 2.0, True)
    city.prop("civic", "statue", 140.0, -184.0, 3.0, 2.0, True)
    city.prop("civic", "fountain", 16.0, -183.0, 6.0, 4.0, True) if False else None
    # the battery
    if fort is not None:
        for dx in (-9.0, -4.5, 0.0, 4.5, 9.0):
            city.prop("street", "cannon_s", fort.x + dx, fort.z + 3.0, 3.0, 1.2, True)
        city.prop("street", "cannon_balls", fort.x - 12.0, fort.z + 2.5, 1.6, 1.2, True)
        city.prop("street", "cannon_balls", fort.x + 12.0, fort.z + 2.5, 1.6, 1.2, True)
    # doorstep tubs and planters on some fronts, crates and barrels beside warehouses
    for p in list(city.placed):
        if p.atlas != "bld" or p.name.startswith("wall"):
            continue
        r = rs.rand()
        if p.name.startswith("warehouse"):
            side = 1 if rs.rand() < 0.5 else -1
            city.prop("street", ("crates_a", "crates_b", "barrels_a", "barrels_b", "sacks")[int(rs.randint(5))], p.x + side * (p.w / 2 + 1.8), p.z + 0.4, 2.4, 1.2, True)
        elif r < 0.30:
            city.prop("street", "tub_bush" if rs.rand() < 0.6 else "planter", p.x + (p.w / 2 - 0.6) * (1 if rs.rand() < 0.5 else -1), p.z + 1.1,
                      1.4, 0.8, True)
    # backyard clutter
    small = ["clothes_line", "rain_barrel", "crates_b", "barrels_a", "hay_cart", "sacks", "barrels_b", "crates_a"]
    tries = 0
    n = 0
    while n < 160 and tries < 1500:
        tries += 1
        x, z = float(rs.uniform(BOX["x0"] + 6, BOX["x1"] - 6)), float(rs.uniform(-262, 6))
        if city.ground(x, z) < 1.8:
            continue
        ci = city.cls[int((z - CT.Z0) / 2), int((x - CT.X0) / 2)]
        if ci not in (EARTH,):
            continue
        rr = (x - 1.6, z - 1.0, x + 1.6, z + 0.4)
        if not city.free(rr, margin=1.0, need_land=False):
            continue
        city.rects.append(rr)
        city.prop("street", small[int(rs.randint(len(small)))], x, z, 2.6, 0.8, True)
        n += 1
    # signposts at the gates and the crossroads
    city.prop("street", "signpost", 14.0, -9.0, 0.8, 0.6, True)
    # ---- the map's places ----------------------------------------------------------------------------------------------
    pl = city.places
    def place(id_, kind, name, what, x, z, rank=2, views=("city", "island"), letter=None):
        d = {"id": id_, "kind": kind, "name": name, "what": what, "x": round(x, 1), "z": round(z, 1), "rank": rank, "views": list(views)}
        if letter:
            d["letter"] = letter
        pl.append(d)
    place("pier", "pier", "Anvil Harbor pier", "your berth", 16.0, 12.0, 3, ("city", "island", "sea"))
    place("fish_market", "market", "Fish Market (Fish Row)", "sell your catch here", -77.0, -10.6, 3)
    place("notice_board", "notice", "Harbour notice board", "jobs and news", 13.0, 0.2, 2)
    place("customs", "customs", "Customs House", "duties, permits", -10.0, -3.8, 2)
    place("tavern", "tavern", "The Anchor and Crown", "tavern: soup, ale, rumours", 50.0, -3.8, 3)
    place("inn", "inn", "The Gilded Gull", "inn", 76.0, -3.8, 1)
    place("market_square", "square", "Grand Market Square", "shops and stalls", 16.0, -66.0, 2)
    place("exchange", "exchange", "Merchants' Exchange", "cargo brokers", -13.0, -87.0, 2)
    place("counting_house", "place", "Counting House", "coin and assay", 46.0, -87.0, 1, letter="$")
    place("palace", "palace", "Governor's Palace", "seat of government", 16.0, -212.0, 3)
    place("town_hall", "hall", "Town Hall", "clock tower", -62.0, -213.0, 1)
    place("barracks", "place", "Barracks", "town guard", 94.0, -213.0, 1, letter="B")
    place("treasury", "place", "Treasury", "harbour accounts", 122.0, -213.0, 1, letter="$")
    place("west_gate", "gate", "West Gate", "North Road to Wreck Bay", -110.0, -264.0, 2)
    place("east_gate", "gate", "East Gate", "North Road to Lookout Hill, Pearl Cove", 120.0, -264.0, 2)
    place("garrick_yard", "place", "Garrick's boatyard", "carpenter wanted", -27.0, -14.0, 1, letter="Y")
    if yard:
        place("shipyard", "warehouse", "Shipyard", "hulls and repairs", yard.x, yard.z + 2.0, 1)
    if fort:
        place("battery", "fort", "Anvil Battery", "harbour guns", fort.x, fort.z + 3.0, 1)
    place("lighthouse", "light", "Anvil Light", "lighthouse", 70.0, 22.0, 1, ("city", "island", "sea"))
    # spots for the people of the main buildings
    spots["tavern_door"] = (50.0, -4.4, 0)
    spots["inn_door"] = (76.0, -4.4, 0)
    spots["customs_door"] = (-10.0, -4.6, 0)
    spots["harbourmaster_door"] = (33.0, -4.4, 0)
    spots["exchange_door"] = (-13.0, -88.0, 0)
    spots["counting_door"] = (46.0, -88.0, 0)
    spots["palace_door"] = (16.0, -214.0, 0)
    spots["hall_door"] = (-62.0, -214.5, 0)
    spots["barracks_door"] = (94.0, -214.0, 0)
    spots["treasury_door"] = (122.0, -214.0, 0)
    for name, gx in GATES:
        spots["gate_%s" % name.split()[0].lower()] = (gx, -265.0, 0)
    if yard:
        spots["yard_door"] = (yard.x, yard.z + 1.4, 0)
    city.yard, city.fort, city.tav = yard, fort, tav
    return city


# ---- the people ---------------------------------------------------------------------------------------------------------------
LOOKS = {"fisher": ["fisher", "fisher_b"], "merchant": ["merchant", "merchant_b"], "docker": ["docker", "docker_b"], "sailor": ["sailor", "sailor_b"],
         "shopkeeper": ["shopkeeper", "shopkeeper_b"], "townsman": ["townsman", "townsman_b", "townsman_c"], "guard": ["guard"], "noble": ["noble"],
         "tavernkeeper": ["tavernkeeper"], "clerk": ["clerk"]}


def people(city: City) -> list[dict]:
    import city_people as PP
    rs = np.random.RandomState(4242)
    out: list[dict] = []
    taken = {v[1].replace('Clerk ', '').replace('Broker ', '').replace('Master ', '').replace('Steward ', '') for v in PP.KEY.values()}
    names = iter([n for n in PP.NAMES if n not in taken] * 3)
    count = {"n": 0}
    sp = city.spots

    def blocked(x, z, m=1.0):
        if city.ground(x, z) < 1.7:
            return True
        for p in city.placed:
            if p.solid and p.x - p.w / 2 - m < x < p.x + p.w / 2 + m and p.z - p.d - m < z < p.z + m:
                return True
        for _a, _n, px, pz, w, d, solid in city.props:
            if solid and px - w / 2 - m < x < px + w / 2 + m and pz - d - m < z < pz + 0.6 + m:
                return True
        return False

    def add(group, x, z, mode="stand", r=0.0, face=0, look=None, name=None, title=None, greeting=None, line=None, wares=None, ident=None):
        if blocked(x, z, 0.5):
            return False
        count["n"] += 1
        lk = look or LOOKS[group][count["n"] % len(LOOKS[group])]
        rec = {"id": ident or "npc_c%03d" % count["n"], "group": group, "look_name": lk, "x": round(x, 2), "z": round(z, 2), "mode": mode, "r": r, "facing": face}
        if name:
            rec["name"] = name
        if title:
            rec["title"] = title
        if greeting:
            rec["greeting"] = greeting
        if line:
            rec["line"] = line
        if wares:
            rec["wares"] = wares
        out.append(rec)
        return True

    def spot(key, dx=0.0, dz=0.0):
        x, z, f = sp[key]
        return x + dx, z + dz, f
    # shopkeepers at their doors: the shops nearest to the avenue
    shops = [p for p in city.placed if p.name in PP.SHOPS]
    shops.sort(key=lambda p: abs(p.x - 16.0) + abs(p.z + 60.0) * 0.3)
    for p in shops[:30]:
        t, g, l, w = PP.SHOPS[p.name]
        add("shopkeeper", p.x + p.w * 0.12, p.z + 1.9, name=next(names), title=t, greeting=g, line=l, wares=w, look=("shopkeeper_b" if rs.rand() < 0.5 else "shopkeeper"))
    # the tavern, the inn and the offices
    t, nm, g, l, w = PP.KEY["tavern"]
    add("tavernkeeper", *spot("tavern_door", 3.6, 0.2)[:2], name=nm, title=t, greeting=g, line=l, wares=w, ident="npc_tavernkeeper", look="tavernkeeper")
    t, nm, g, l, w = PP.KEY["inn"]
    add("tavernkeeper", *spot("inn_door", 3.0, 0.2)[:2], name=nm, title=t, greeting=g, line=l, wares=w, look="shopkeeper_b")
    for k, (dx, dz) in enumerate(((-4.0, 1.0), (6.0, 0.5), (0.0, 2.0))):
        add("sailor", 50.0 + dx, -2.0 + dz, "wander", 3.5, 0)
    for key, tk in (("customs_door", "customs"), ("exchange_door", "exchange"), ("counting_door", "counting"), ("palace_door", "palace")):
        t, nm, g, l, w = PP.KEY[tk]
        x, z, f = sp[key]
        add("clerk", x + 3.0, z + 1.2, name=nm, title=t, greeting=g, line=l, wares=w, look="clerk")
    add("clerk", *spot("harbourmaster_door", 0.0, 1.5)[:2], name="Harbourmaster Jeremiah Slade", title="Harbourmaster", look="captain",
        greeting="Jeremiah Slade, harbourmaster. Berths, tides and troubles: I keep the book.",
        line="Anchor where you like inside the buoys, and leave the channel clear. That is the whole law of the water.", wares="Berths, tide tables, harbour dues.",
        ident="npc_harbourmaster")
    add("sailor", 2.0, -3.4, "stand", 0, 3, look="captain", name="Captain Rufus Vane", title="Retired captain",
        greeting="Rufus Vane. Thirty years under canvas, and now I count other men's ships in.",
        line="A sloop and a hold of fish is a fine beginning. I began with less, and a worse temper.", wares="Stories, mostly.")
    for dx in (-3.2, 3.2):
        add("guard", 16.0 + dx * 2.4, -213.5, "stand", 0, 0, name="Palace guard")
    add("guard", 16.0, -205.0, "patrol", 14.0, 3)
    add("guard", -12.0, -208.0, "patrol", 12.0, 3)
    for dx in (-10.0, 18.0, 44.0):
        add("noble", 16.0 + dx, -207.0, "wander", 7.0, 0)
    add("clerk", *spot("hall_door", 2.5, 1.2)[:2], look="clerk", name="Registrar Octavian Pell", title="Town registrar",
        greeting="Town Hall. Births, deeds and bell-times are all written in my books.", line="The clock is never wrong. The sun, on occasion, is.",
        wares="Deeds, registers, the town clock.")
    for x in (-8.0 + 94.0, 104.0):
        add("guard", x, -213.0, "stand", 0, 0, name="Barracks guard")
    add("guard", 94.0, -203.0, "patrol", 10.0, 3)
    add("clerk", *spot("treasury_door", 2.5, 1.0)[:2], look="clerk", name="Clerk Matthias Orne", title="Treasury clerk",
        greeting="The Harbour Treasury. We count everything twice.", line="Count it twice, spend it once.", wares="Accounts.")
    for name, gx in GATES:
        for dx in (-4.2, 4.2):
            add("guard", gx + dx, -264.5, "stand", 0, 0, name="Gate guard", title="Town watch", greeting=PP.KEY["gate"][2], line=PP.KEY["gate"][3])
    if city.yard:
        t, nm, g, l, w = PP.KEY["yard"]
        add("docker", city.yard.x - 4.0, city.yard.z + 1.8, name=nm, title=t, greeting=g, line=l, wares=w, look="docker_b")
        for dx in (-6.0, 7.0):
            add("docker", city.yard.x + dx, city.yard.z + 3.0, "wander", 3.0, 0)
    if city.fort:
        for dx in (-9.0, 0.0, 9.0):
            add("guard", city.fort.x + dx, city.fort.z + 5.0, "stand", 0, 0, name="Battery gunner", title="Harbour guns")
    # market square: stallholders and shoppers
    ware = ["Greens and onions", "Oranges and limes", "Cheese and butter", "Salted pork and peas", "Rope and twine", "Pots and pans", "Tallow candles", "Dried fruit"]
    for k in range(8):
        key = "stall_%d" % k
        if key in sp:
            x, z, f = sp[key]
            for dz in (-3.4, -4.2, -5.0, 1.6):
                if add("shopkeeper", x, z + dz, name=next(names), title="Stallholder", wares=ware[k], look="shopkeeper_b" if k % 2 else "shopkeeper",
                       greeting="Come closer, Captain: %s, fresh today." % ware[k].lower(), line="Everything on this stall came off a cart this morning."):
                    break
    # walkers on the streets
    def street_walkers(group, n, zc, x0, x1, r=6.0, mode="wander"):
        got = 0
        tries = 0
        while got < n and tries < 60:
            tries += 1
            x = float(rs.uniform(x0, x1))
            z = zc + float(rs.uniform(-1.2, 1.2))
            if any(a - 1 < x < b + 1 for a, b in ((-53.0, -39.0),)) and zc > -20:
                continue
            if add(group, x, z, mode, r, int(rs.randint(4))):
                got += 1
    street_walkers("townsman", 8, 0.0, 36.0, 190.0, 8.0)
    street_walkers("townsman", 6, 0.0, -190.0, -130.0, 8.0)
    street_walkers("docker", 6, 1.0, 84.0, 190.0, 7.0, "patrol")
    street_walkers("sailor", 4, 1.0, 36.0, 120.0, 6.0)
    street_walkers("fisher", 8, -9.0, -195.0, -130.0, 7.0)
    street_walkers("fisher", 4, -28.0, -190.0, -130.0, 6.0)
    street_walkers("townsman", 10, -44.0, -190.0, 190.0, 7.0)
    street_walkers("merchant", 5, -44.0, -100.0, 190.0, 7.0)
    street_walkers("townsman", 10, -86.0, -190.0, 190.0, 7.0)
    street_walkers("merchant", 6, -86.0, -190.0, 190.0, 7.0)
    street_walkers("townsman", 8, -113.0, -190.0, 190.0, 7.0)
    street_walkers("noble", 5, -158.0, -190.0, 190.0, 7.0)
    street_walkers("guard", 3, -158.0, -190.0, 190.0, 14.0, "patrol")
    street_walkers("guard", 3, -113.0, -190.0, 190.0, 14.0, "patrol")
    street_walkers("noble", 4, -181.0, -190.0, 190.0, 8.0)
    street_walkers("townsman", 4, -56.0, -12.0, 46.0, 9.0)
    street_walkers("merchant", 3, -66.0, -12.0, 46.0, 9.0)
    for z in (-30.0, -70.0, -105.0, -140.0, -185.0):                                    # the avenue
        for k in range(2):
            add(("townsman", "merchant", "noble")[int(rs.randint(3))] if z > -150 else "noble", float(rs.uniform(10.5, 21.5)), z + float(rs.uniform(-4, 4)), "wander", 5.0, int(rs.randint(4)))
    return out
