"""CP-1 revision: turns the planned capital (city_layout.City) into game data: atlas PNGs, sprite lists, blockers, occluders, people, map
entries. Called from bake_cay.py."""
from __future__ import annotations

import numpy as np
from PIL import Image

import city_art as CA
import city_layout as CY
import city_props as CP
import cay_terrain as CT
import port_sprites as PS

PPM = 14.4


def civic_atlas():
    items = CA.civics()
    im = Image.new("RGBA", (128 * 4, 176 * ((len(items) + 3) // 4)), (0, 0, 0, 0))
    for i, (_n, _w, _d, _h, arr) in enumerate(items):
        cell = Image.fromarray(arr, "RGBA")
        py = {"fountain": 150, "anvil_monument": 152, "statue": 152, "dock_crane": 170}[_n]
        im.alpha_composite(cell.crop((0, 0, 128, min(cell.size[1], 176 - (170 - py)))), ((i % 4) * 128, (i // 4) * 176 + (170 - py)))
    return im, items


def build_atlases(art):
    """Writes the four city atlases; returns the atlas dictionaries for the JSON."""
    S, G = CA.smalls(), CA.grands()
    out = {}
    im, rows = CA.atlas(S, CA.SW, CA.SH, 6, 0)
    im.save(art / "city_small_atlas.png", optimize=True)
    out["bld"] = {"file": "city_small_atlas.png", "cell_px": [CA.SW, CA.SH], "pivot_px": [CA.SPX, CA.SPY], "cols": 6, "rows": rows,
                  "types": [s[0] for s in S], "px_per_m": PPM, "glow": True}
    im, rows = CA.atlas(G, CA.GW, CA.GH, 3, 0)
    im.save(art / "city_grand_atlas.png", optimize=True)
    out["grand"] = {"file": "city_grand_atlas.png", "cell_px": [CA.GW, CA.GH], "pivot_px": [CA.GPX, CA.GPY], "cols": 3, "rows": rows,
                    "types": [g[0] for g in G], "px_per_m": PPM, "glow": True}
    im, items = civic_atlas()
    im.save(art / "city_civic_atlas.png", optimize=True)
    out["civic"] = {"file": "city_civic_atlas.png", "cell_px": [128, 176], "pivot_px": [64, 170], "cols": 4, "rows": (len(items) + 3) // 4,
                    "types": [c[0] for c in items], "px_per_m": PPM, "glow": True}
    arrs = CP.props()
    cols = 4
    rows = (len(arrs) + cols - 1) // cols
    pim = Image.new("RGBA", (64 * cols, 64 * rows), (0, 0, 0, 0))
    for i, a in enumerate(arrs):
        pim.alpha_composite(Image.fromarray(a, "RGBA"), ((i % cols) * 64, (i // cols) * 64))
    pim.save(art / "city_props_atlas.png", optimize=True)
    out["street"] = {"file": "city_props_atlas.png", "cell_px": [64, 64], "pivot_px": [32, 60], "cols": cols, "rows": rows,
                     "types": CP.PROP_TYPES, "px_per_m": PPM, "glow": True}
    return out


def small_sizes():
    CY.register_sizes(CA.smalls(), CA.grands())


def sprite_lists(city, atlases, ground):
    """-> dict atlas name -> list of sprite dicts {type, x_m, z_m, y_m, scale}. `ground(x, z)` = baked height."""
    lists = {"bld": [], "grand": [], "civic": [], "street": [], "stall": []}
    for p in city.placed:
        if p.atlas == "bld" and p.name == "dock_crane":
            continue
        a = atlases[p.atlas]
        lists[p.atlas].append({"type": a["types"].index(p.name), "x_m": round(p.x, 2), "z_m": round(p.z, 2), "y_m": round(ground(p.x, p.z - p.d * 0.5), 2),
                               "scale": 1.0, "name": p.name})
    stall_types = PS.STALL_TYPES
    for atlas, name, x, z, w, d, solid in city.props:
        if atlas == "stall":
            t = stall_types.index("bench" if name == "bench" else name)
            lists["stall"].append({"type": t, "x_m": round(x, 2), "z_m": round(z, 2), "y_m": round(ground(x, z - 0.3), 2), "scale": 1.0, "name": name})
        else:
            a = atlases[atlas]
            lists[atlas].append({"type": a["types"].index(name), "x_m": round(x, 2), "z_m": round(z, 2), "y_m": round(ground(x, z - 0.3), 2), "scale": 1.0, "name": name})
    return lists


def trees(city, ground):
    out = []
    for t, x, z, s, r in city.trees:
        out.append({"type": int(t), "x_m": round(x, 2), "z_m": round(z, 2), "y_m": round(ground(x, z), 2), "scale": round(float(s), 2)})
    return out


def blockers(city):
    out = []
    for p in city.placed:
        if p.solid:
            out.append([round(p.x - p.w / 2 + 0.15, 2), round(p.z - p.d, 2), round(p.x + p.w / 2 - 0.15, 2), round(p.z + 0.35, 2)])
    for atlas, name, x, z, w, d, solid in city.props:
        if solid and not name in ("signpost",):
            out.append([round(x - w / 2, 2), round(z - d, 2), round(x + w / 2, 2), round(z + 0.2, 2)])
    for t, x, z, s, r in city.trees:
        if r > 0.0:
            out.append([round(x - r, 2), round(z - r, 2), round(x + r, 2), round(z + r, 2)])
    return out


def occluders(city, occ, h, cell_of):
    """Raises the occluder height map under every building."""
    for p in city.placed:
        m = CT.box(p.x - p.w / 2, p.z - p.d, p.x + p.w / 2, p.z)
        iz, ix = cell_of(p.x, p.z - p.d * 0.5)
        occ = np.where(m, np.maximum(occ, float(h[iz, ix]) + p.h), occ)
    return occ


def npc_records(city):
    out = []
    for r in city.people:
        d = dict(r)
        d["look"] = PS.LOOK_ORDER.index(d.pop("look_name"))
        out.append(d)
    return out
