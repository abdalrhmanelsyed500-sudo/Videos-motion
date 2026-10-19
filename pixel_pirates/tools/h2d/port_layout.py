"""CP-1 layout of the Anvil Harbor "Fish Row" district: the single source of truth read by bake_cay.py (terrain carving, the
"port" section of anvil_cay.json) and by check_port.py (reachability and placement checks).

World frame as everywhere: x east, z SOUTH, metres. Quay Street runs west from the H2D-1 plaza along z -4..3.4; the market yard is
NORTH of it, the wharf apron SOUTH of it (down to the shore, which falls from z 9 at x -124 to z 37 at x -20); a canal ("The Cut")
runs from the shore up to z -14 and is crossed by two bridges; the wharf deck follows the coast and closes the canal mouth.
Everything in H2D-1 (pier, berth, dock zone, plaza) is untouched.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

import cay_terrain as CT

QUAY_H = CT.PLAZA_H            # 1.95: the district floor is level with the H2D-1 plaza
WHARF_H = 1.75                 # deck of the wharf: a 0.2 m step down from the quay, so the pirate does not hop
BRIDGE_H = 1.90
WHARF_X0, WHARF_X1, WHARF_STEP = -116.0, -28.0, 8.0
WHARF_DEPTH_IN, WHARF_DEPTH_OUT = 1.5, 3.5      # the deck reaches 1.5 m inland of the shoreline and 3.5 m out over the water
CANAL = dict(x0=-48.0, x1=-40.0, z0=-14.0)       # from z0 south to the sea
CANAL_BED = -1.4
BRIDGES = [dict(name="Quay Street Bridge", x0=-50.0, x1=-38.0, z0=-3.2, z1=3.2, h=BRIDGE_H),
           dict(name="Net Walk Footbridge", x0=-50.0, x1=-38.0, z0=9.6, z1=12.8, h=BRIDGE_H)]
INTERACT_R = 2.8               # metres from the point: E opens it

# district floors (cobbles, level with the plaza): x0, z0, x1, z1
FLOORS = [(-118.0, -4.4, -1.0, 3.5),            # Quay Street
          (-102.0, -29.0, -53.0, -4.0),          # the market yard (x order fixed below)
          (-36.0, -30.0, -19.0, -4.0),           # the warehouse yard (Garrick's boatyard)
          (-118.0, 3.4, -1.0, 8.0)]              # the first strip of the apron; the rest follows the shore (apron_mask)
FLOORS = [(min(a, c), b, max(a, c), d) for a, b, c, d in FLOORS]

# stalls, goods and furniture. atlas "stall": type index into port_sprites.STALL_TYPES. (x, z) is the sprite's ground point.
# solid: (width, depth) footprint in metres for the walk blockers (0 = none)
S = "stall"
PROPS = [
    # --- the fish market: a counter flanked by two stalls under the canopy, more stalls in the open yard
    (S, "fish_counter", -77.0, -12.6, 4.2, 1.4), (S, "stall_red", -83.6, -12.4, 4.2, 1.4), (S, "stall_blue", -70.4, -12.4, 4.2, 1.4),
    (S, "stall_green", -91.0, -20.0, 4.2, 1.4), (S, "stall_red", -64.0, -20.0, 4.2, 1.4), (S, "stall_fruit", -97.5, -9.5, 4.2, 1.4),
    (S, "fish_crates", -86.0, -8.2, 3.0, 1.4), (S, "barrels_fish", -68.0, -8.2, 3.0, 1.4), (S, "fish_crates", -57.5, -9.0, 3.0, 1.4),
    (S, "fish_rack", -79.0, -23.5, 4.2, 1.0), (S, "well", -57.5, -16.0, 2.4, 2.0),
    (S, "bench", -73.0, -5.6, 3.4, 1.0), (S, "bench", -90.0, -5.6, 3.4, 1.0),
    (S, "lantern_post", -100.5, -4.9, 0.5, 0.5), (S, "lantern_post", -64.0, -4.9, 0.5, 0.5), (S, "lantern_post", -81.0, -4.9, 0.5, 0.5),
    (S, "lantern_post", -52.0, -4.9, 0.5, 0.5), (S, "lantern_post", -30.0, -4.9, 0.5, 0.5), (S, "lantern_post", -10.0, -4.9, 0.5, 0.5),
    # --- the wharf apron: nets, racks, carts and cargo
    (S, "fish_rack", -88.0, 7.8, 4.2, 1.0), (S, "fish_rack", -82.0, 7.8, 4.2, 1.0), (S, "barrels_fish", -76.0, 8.0, 3.0, 1.4),
    (S, "handcart", -62.0, 8.2, 3.6, 1.4), (S, "fish_crates", -58.0, 9.4, 3.0, 1.4), (S, "net_rack", -52.8, 8.0, 4.2, 1.0),
    (S, "sacks", -33.0, 8.4, 3.0, 1.4), (S, "barrels_fish", -26.5, 9.0, 3.0, 1.4), (S, "sacks", -20.0, 8.0, 3.0, 1.4),
    (S, "anchor", -112.0, 5.4, 1.6, 1.0),
    # --- the warehouse yard (Garrick's boatyard)
    (S, "sacks", -33.0, -10.0, 3.0, 1.4), (S, "handcart", -23.0, -9.0, 3.6, 1.4),
    # --- by the pier landing: the notice board that opens the map
    (S, "notice_board", 13.0, -2.4, 3.6, 0.8), (S, "lantern_post", 9.5, -4.6, 0.5, 0.5),
]
BIG = [  # atlas "big" (192 x 112 px = 13.3 x 7.8 m): type, x, z, footprint w, d, solid
    ("market_canopy", -77.0, -10.0, 0.0, 0.0), ("net_frame", -101.0, 6.8, 11.0, 1.0), ("cargo_pile", -27.0, 15.5, 13.0, 4.0),
]
BIG_POSTS = [(-77.0 + dx, -10.0) for dx in (-5.97, -2.5, 2.2, 5.5)]     # canopy posts: little blockers

# structures from the H2D-1.2 atlas (80 x 72 px, 3.6 px/m): name, atlas cell, x, z (front), w, d, h
STRUCTS = [
    ("cottage_p1", 15, -106.0, -32.0, 8.4, 6.0, 6.0), ("cottage_p2", 16, -94.0, -34.0, 7.8, 5.6, 5.6),
    ("cottage_p3", 15, -82.0, -33.0, 8.4, 6.0, 6.0), ("cottage_p4", 16, -70.0, -34.0, 7.8, 5.6, 5.6),
    ("cottage_p5", 15, -58.0, -32.0, 8.4, 6.0, 6.0),
    ("fisher_hut_p1", 3, -110.0, -9.0, 12.0, 6.0, 4.5),
]
REMOVE_STRUCTS = ("fisher_hut",)     # the H2D-1 hut at (-27, 3) stood on Quay Street; it moves to Fish Row as fisher_hut_p1

# moored boats: atlas, type, x, z (pivot, on the water), hull footprint (w, d), y (waterline)
BOATS = [
    ("ships", 0, -105.0, "S", 22.0, 6.4), ("big", "smack_red", -86.0, "S", 9.4, 3.4), ("big", "smack_blue", -68.0, "S", 9.4, 3.4),
    ("big", "skiff", -44.0, -9.0, 4.6, 2.0), ("big", "skiff", -44.0, 6.2, 4.6, 2.0),
]

# the people: id, group (look name), x, z, mode, r (wander radius or patrol half length), facing 0 S 1 N 2 W 3 E
NPCS = [
    ("npc_fisher_1", "fisher", -98.0, 9.4, "stand", 0, 1), ("npc_fisher_2", "fisher", -86.0, 10.5, "wander", 4.0, 0),
    ("npc_fisher_3", "fisher", -70.0, 11.0, "wander", 5.0, 3), ("npc_fisher_4", "fisher", -60.0, 12.0, "stand", 0, 2),
    ("npc_fisher_5", "fisher", -72.0, -2.0, "wander", 6.0, 0),
    ("npc_fishmonger", "shopkeeper", -77.0, -15.2, "stand", 0, 0),
    ("npc_trader_1", "merchant", -83.6, -15.0, "stand", 0, 0), ("npc_trader_2", "shopkeeper", -70.4, -15.0, "stand", 0, 0),
    ("npc_trader_3", "shopkeeper", -91.0, -22.6, "stand", 0, 0), ("npc_trader_4", "merchant", -97.5, -12.0, "stand", 0, 0),
    ("npc_merchant_1", "merchant", -80.0, -6.5, "wander", 11.0, 0), ("npc_merchant_2", "merchant", -62.0, -24.0, "wander", 6.0, 0),
    ("npc_docker_1", "docker", -33.0, 4.5, "patrol", 5.0, 3), ("npc_docker_2", "docker", -17.0, 10.5, "wander", 3.0, 0),
    ("npc_docker_3", "docker", -104.0, 4.6, "patrol", 6.0, 3), ("npc_docker_4", "docker", -56.0, 11.5, "stand", 0, 2),
    ("npc_sailor_1", "sailor", 29.0, 0.2, "stand", 0, 2), ("npc_sailor_2", "sailor", 20.5, -5.5, "wander", 4.5, 0),
    ("npc_sailor_3", "sailor", 3.0, -6.0, "wander", 2.5, 3),
    ("npc_town_1", "townsman", -110.0, 0.0, "wander", 7.0, 3), ("npc_town_2", "townsman", -60.0, 0.4, "wander", 12.0, 3),
    ("npc_town_3", "townsman", -30.0, -1.0, "wander", 8.0, 2), ("npc_town_4", "townsman", -14.0, 0.0, "wander", 6.0, 0),
    ("npc_town_5", "townsman", -86.0, -26.5, "wander", 4.0, 0),
]
# the recruits: crew id -> look, position, facing. Their cost, role and words are in game/data/port/recruits_port.json.
RECRUIT_SPOTS = {
    "crew_pip_larkin": ("r_pip", 27.5, -2.4, 2),
    "crew_silas_reed": ("r_silas", -57.5, -13.8, 0),
    "crew_garrick_stave": ("r_garrick", -26.5, -22.0, 0),
    "crew_tuck_marrow": ("r_tuck", -100.5, 8.6, 3),
}
MARKET_POINT = (-77.0, -10.6)       # stand here to talk to the fishmonger (E): in front of the counter
NOTICE_POINT = (13.0, 0.2)       # in front of the board, 5 m from the pier landing

# ---- terrain -------------------------------------------------------------------------------------------------------------
def shore_z(h: np.ndarray, x: float) -> float:
    """First z south of -30 where the ground is below 0.1 m (the waterline), on the column of x."""
    if CANAL["x0"] - 1.0 <= x <= CANAL["x1"] + 1.0:      # the canal columns have no shore of their own: use the banks
        return 0.5 * (shore_z(h, CANAL["x0"] - 3.0) + shore_z(h, CANAL["x1"] + 3.0))
    ix = int((x - CT.X0) / CT.CELL)
    iz0 = int((-30.0 - CT.Z0) / CT.CELL)
    col = h[iz0:iz0 + 80, ix]
    k = np.nonzero(col < 0.1)[0]
    return float(CT.Z0 + (iz0 + int(k[0])) * CT.CELL + CT.CELL * 0.5) if len(k) else 40.0


def wharf_nodes(h: np.ndarray) -> list[tuple[float, float]]:
    xs = np.arange(WHARF_X0, WHARF_X1 + 0.1, WHARF_STEP)
    return [(float(x), shore_z(h, float(x))) for x in xs]


def decks(h: np.ndarray) -> list[dict]:
    out: list[dict] = []
    nodes = wharf_nodes(h)
    for (xa, za), (xb, zb) in zip(nodes[:-1], nodes[1:]):
        out.append({"x0": xa, "x1": xb, "z0": min(za, zb) - WHARF_DEPTH_IN, "z1": max(za, zb) + WHARF_DEPTH_OUT, "h": WHARF_H, "kind": "wharf"})
    for b in BRIDGES:
        out.append({"x0": b["x0"], "x1": b["x1"], "z0": b["z0"], "z1": b["z1"], "h": b["h"], "kind": "bridge", "name": b["name"]})
    return out


def carve(T: CT.Terrain) -> dict:
    """Level the district to the plaza height and dig the canal. Edits T.h and T.mask in place; returns masks for the bake."""
    h = T.h
    X, Z = CT.X, CT.Z
    nodes = wharf_nodes(h)
    apron = np.zeros(h.shape, bool)
    for (xa, za), (xb, zb) in zip(nodes[:-1], nodes[1:]):
        apron |= CT.box(xa, 3.4, xb, max(za, zb) - 0.8)
    floor = np.zeros(h.shape, bool)
    for x0, z0, x1, z1 in FLOORS:
        floor |= CT.box(x0, z0, x1, z1)
    floor |= apron
    floor &= T.mask & (h > 0.3)
    w = np.clip(ndimage.gaussian_filter(floor.astype(np.float32), 1.2) * 1.5, 0.0, 1.0) * floor.astype(np.float32)
    h[:] = np.where(floor, h * (1.0 - w) + QUAY_H * w, h)
    canal = CT.box(CANAL["x0"], CANAL["z0"], CANAL["x1"], 60.0) & (h > -0.5)
    h[canal] = CANAL_BED
    T.mask = T.mask & ~canal
    T.d_in = (ndimage.distance_transform_edt(T.mask) * CT.CELL).astype(np.float32)
    T.d_out = (ndimage.distance_transform_edt(~T.mask) * CT.CELL).astype(np.float32)
    return {"floor": floor, "canal": canal, "apron": apron}


def solid_rects() -> list[list[float]]:
    """Walk blockers [x0, z0, x1, z1] of every solid prop (the sprite's footprint: centred on x, ending 0.2 m behind z)."""
    out = []
    for _atlas, _t, x, z, w, d in PROPS:
        if w > 0:
            out.append([round(x - w / 2, 2), round(z - d, 2), round(x + w / 2, 2), round(z + 0.2, 2)])
    for _t, x, z, w, d in BIG:
        if w > 0:
            out.append([round(x - w / 2, 2), round(z - d, 2), round(x + w / 2, 2), round(z + 0.2, 2)])
    for x, z in BIG_POSTS:
        out.append([round(x - 0.35, 2), round(z - 0.35, 2), round(x + 0.35, 2), round(z + 0.35, 2)])
    return out


def boat_positions(h: np.ndarray) -> list[dict]:
    """Moored boats: on the water side of the wharf deck (clear of every deck segment under the hull), the skiffs inside the canal."""
    dk = [d for d in decks(h) if d["kind"] == "wharf"]
    out = []
    for atlas, t, x, z, w, d in BOATS:
        if z == "S":
            z1 = max(k["z1"] for k in dk if k["x1"] > x - w / 2 and k["x0"] < x + w / 2)
            zz = z1 + 0.6 + (d * 0.5 if atlas == "ships" else d)   # ships: pivot at the hull centre; big boats: pivot at the stern edge, the hull runs z-d..z
        else:
            zz = float(z)
        out.append({"atlas": atlas, "type": t, "x": x, "z": round(zz, 2), "w": w, "d": d})
    return out


# ---- the "port" section of anvil_cay.json --------------------------------------------------------------------------------------
PX_PER_M_PORT = 14.4


def atlases() -> dict:
    import port_sprites as PS
    return {
        "stall": {"file": "port_stall_atlas.png", "cell_px": [PS.CW, PS.CH], "pivot_px": list(PS.PIVOT), "cols": 4, "rows": 4,
                  "types": PS.STALL_TYPES, "px_per_m": PX_PER_M_PORT, "glow": True},
        "misc": {"file": "port_misc_atlas.png", "cell_px": [PS.CW, PS.CH], "pivot_px": list(PS.PIVOT), "cols": 4, "rows": 4,
                 "types": PS.MISC_TYPES, "px_per_m": PX_PER_M_PORT, "glow": True},
        "big": {"file": "port_big_atlas.png", "cell_px": [PS.BW, PS.BHT], "pivot_px": list(PS.BIG_PIVOT), "cols": 4, "rows": 2,
                "types": PS.BIG_TYPES, "px_per_m": PX_PER_M_PORT, "glow": True},
        "ships": {"file": "port_ships_atlas.png", "cell_px": [112, 112], "pivot_px": [56, 66], "cols": 4, "rows": 1,
                  "types": ["sloop_e", "sloop_w", "sloop_grey_e", "sloop_grey_w"], "px_per_m": 3.6, "glow": False},
        "npc": {"file": "port_npc_atlas.png", "cell_px": [PS.NPC_W, PS.NPC_H], "pivot_px": list(PS.NPC_PIVOT), "cols": 4,
                "rows": 4 * len(PS.LOOK_ORDER), "looks": PS.LOOK_ORDER, "px_per_m": PX_PER_M_PORT, "glow": False},
    }


def deck_at(decks_list: list[dict], x: float, z: float):
    for d in decks_list:
        if d["x0"] <= x <= d["x1"] and d["z0"] <= z <= d["z1"]:
            return d["h"]
    return None


def port_json(h: np.ndarray, sample_h) -> dict:
    """Everything the game needs of the district. `sample_h(x, z)` is the baked ground height."""
    import port_sprites as PS
    dk = decks(h)

    def ground(x: float, z: float) -> float:
        d = deck_at(dk, x, z)
        return float(d) if d is not None else float(sample_h(x, z))

    props = []
    for _atlas, name, x, z, _w, _d in PROPS:
        props.append({"name": name, "type": PS.STALL_TYPES.index(name), "x_m": x, "z_m": z, "y_m": round(ground(x, z - 0.4), 2), "scale": 1.0})
    big = []
    for name, x, z, _w, _d in BIG:
        big.append({"name": name, "type": PS.BIG_TYPES.index(name), "x_m": x, "z_m": z, "y_m": round(ground(x, z - 0.4), 2), "scale": 1.0})
    ships, hulls = [], []
    for b in boat_positions(h):
        rec = {"x_m": b["x"], "z_m": b["z"], "y_m": -0.12, "scale": 1.0, "bob": 0.08}
        if b["atlas"] == "ships":
            rec["type"] = int(b["type"])
            ships.append(rec)
            hulls.append([round(b["x"] - b["w"] / 2, 2), round(b["z"] - b["d"] / 2, 2), round(b["x"] + b["w"] / 2, 2), round(b["z"] + b["d"] / 2, 2)])
        else:
            rec["type"] = PS.BIG_TYPES.index(b["type"])
            rec["name"] = b["type"]
            big.append(rec)
            hulls.append([round(b["x"] - b["w"] / 2, 2), round(b["z"] - b["d"], 2), round(b["x"] + b["w"] / 2, 2), round(b["z"], 2)])
    npcs = []
    for nid, group, x, z, mode, r, face in NPCS:
        npcs.append({"id": nid, "group": group, "look": PS.LOOK_ORDER.index(group), "x": x, "z": z, "mode": mode, "r": r, "facing": face})
    for cid, (look, x, z, face) in RECRUIT_SPOTS.items():
        npcs.append({"id": "npc_" + cid[5:], "group": "recruit", "look": PS.LOOK_ORDER.index(look), "x": x, "z": z, "mode": "stand", "r": 0,
                     "facing": face, "recruit": cid})
    inter = [
        {"id": "fish_market", "kind": "market", "name": "Fish market", "x": MARKET_POINT[0], "z": MARKET_POINT[1], "r": 3.4},
        {"id": "notice_board", "kind": "notice", "name": "Harbour notice board", "x": NOTICE_POINT[0], "z": NOTICE_POINT[1], "r": INTERACT_R},
    ]
    markers = [
        {"id": "fish_market", "atlas": "misc", "type": PS.MISC_TYPES.index("marker_fish"), "x_m": MARKET_POINT[0], "z_m": MARKET_POINT[1] - 0.2,
         "y_m": round(QUAY_H + 7.6, 2), "scale": 1.0, "bob": 0.18},
        {"id": "notice_board", "atlas": "misc", "type": PS.MISC_TYPES.index("marker_notice"), "x_m": NOTICE_POINT[0], "z_m": -2.6,
         "y_m": round(QUAY_H + 3.3, 2), "scale": 1.0, "bob": 0.14},
    ]
    return {
        "name": "Fish Row", "district_of": "Anvil Harbor", "px_per_m": PX_PER_M_PORT, "atlases": atlases(),
        "wharf_h": WHARF_H, "decks": dk, "hulls": hulls, "canal": CANAL,
        "props": props, "big": big, "ships": ships, "npcs": npcs, "interactions": inter, "markers": markers,
        "map": {"floors": [list(f) for f in FLOORS], "canal": [CANAL["x0"], CANAL["z0"], CANAL["x1"], 60.0],
                "bridges": [[b["x0"], b["z0"], b["x1"], b["z1"]] for b in BRIDGES],
                "wharf": [[d["x0"], d["z0"], d["x1"], d["z1"]] for d in dk if d["kind"] == "wharf"],
                "bounds": [-125.0, -45.0, 40.0, 40.0]},
        "recruit_spots": {k: {"x": v[1], "z": v[2]} for k, v in RECRUIT_SPOTS.items()},
    }
