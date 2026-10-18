"""Wildlife sighting model (Module E1). Pure and stateless like ocean.py: the same place and time always shows the same animal.
GDScript twin: game/core/wildlife.gd, replayed against game/tests/fixtures/wildlife_cases.json.

A 'slot' is perf.sighting_min_gap_s of real time (90 s = 0.1 game days). In each slot at each 40 km cell the world rolls once:
nothing, or one sighting chosen from every species that could be here NOW, weighted by how well the place, season, hour and
water suit it. Fog and rain shorten how far you can see an animal, exactly as they shorten how far you can see a ship.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ocean as O  # noqa: E402

RARITY_W = {"common": 1.0, "uncommon": 0.4, "rare": 0.12, "legendary": 0.02}
SEED = 311
MIN_ABUNDANCE = 0.02
GAME_S_PER_REAL_S = 96.0


def slot_days(t: dict) -> float:
    return t["perf.sighting_min_gap_s"] * GAME_S_PER_REAL_S / 86400.0


def activity_factor(kind: str, hour: float) -> float:
    if kind == "always":
        return 1.0
    day = 6.0 <= hour < 18.0
    if kind == "diurnal":
        return 1.0 if day else 0.25
    if kind == "nocturnal":
        return 0.25 if day else 1.0
    near = min(abs(hour - 6.0), abs(hour - 18.0))   # crepuscular: dawn and dusk
    return 1.0 if near <= 2.0 else 0.4


def season_factor(window: list[float] | None, s: float) -> float:
    if not window:
        return 1.0
    a, b = window
    inside = (a <= s <= b) if a <= b else (s >= a or s <= b)
    return 1.0 if inside else 0.15


def suitability(t: dict, sp: dict, s: dict) -> float:
    """Relative weight of one species at one sampled place and time. 0 means it cannot be here."""
    w = s["weights"]
    ab = 0.0
    for wi, rid in zip(w, s["_region_ids"]):
        for rr in sp["regions"]:
            if rr["region"] == rid:
                ab += wi * rr["abundance"]
    if ab < MIN_ABUNDANCE:       # a trace from a far region's blend tail is not a population
        return 0.0
    tol = t["wildlife.temp_tolerance_c"]
    if sp["habitat"] in ("deep", "vent"):
        tf = 1.0
    else:
        out = max(0.0, sp["temp_c"][0] - s["sst_c"], s["sst_c"] - sp["temp_c"][1])
        tf = O.clamp(1.0 - out / tol, 0.0, 1.0)
    pf = 1.0
    need = sp.get("needs_productivity", 0.0)
    if need > 0.0:
        pf = O.clamp(s["productivity"] / need, 0.0, 1.0)
    icef = 1.0
    if sp["habitat"] == "ice_edge":
        icef = 0.4 + 0.6 * O.clamp(s["ice"] * 3.0, 0.0, 1.0)
    elif s["ice"] > 0.5:
        icef = 0.3
    return ab * tf * pf * icef * season_factor(sp.get("season"), s["season"]) * activity_factor(sp["activity"], s["hour"]) * RARITY_W[sp["rarity"]]


def table(oc: O.Ocean, species: list[dict], x: float, y: float, t_days: float) -> list[tuple[str, float]]:
    s = oc.sample(x, y, t_days)
    s["_region_ids"] = [r["id"] for r in oc.regions]
    out = [(sp["id"], suitability(oc.t, sp, s)) for sp in species]
    return [(i, w) for i, w in out if w > 0.0]


def sighting(oc: O.Ocean, species: list[dict], x: float, y: float, t_days: float) -> dict | None:
    """The sighting for the slot containing t_days at the 40 km cell containing (x, y), or None. Deterministic."""
    t = oc.t
    slot = int(math.floor(t_days / slot_days(t)))
    cell = t["perf.weather_grid_km"]
    cx, cy = int(math.floor(x / cell)), int(math.floor(y / cell))
    if O.hash01(slot, cx, cy, SEED) >= t["wildlife.sighting_chance"]:
        return None
    tb = table(oc, species, x, y, (slot + 0.5) * slot_days(t))
    total = sum(w for _, w in tb)
    if total <= 0.0:
        return None
    pick = O.hash01(slot, cx, cy, SEED + 1) * total
    acc, chosen = 0.0, tb[-1][0]
    for sid, w in tb:
        acc += w
        if pick <= acc:
            chosen = sid
            break
    sp = next(q for q in species if q["id"] == chosen)
    s = oc.sample(x, y, t_days)
    dmin, dmax = t["wildlife.sight_distance_min"], t["wildlife.sight_distance_max"]
    dist = s["visibility_km"] * (dmin + (dmax - dmin) * O.hash01(slot, cx, cy, SEED + 2))
    lo, hi = sp["group_size"]
    n = int(math.floor(lo * (hi / lo) ** O.hash01(slot, cx, cy, SEED + 3) + 0.5)) if hi > lo else lo
    return {"species": chosen, "bearing_deg": 360.0 * O.hash01(slot, cx, cy, SEED + 4), "distance_km": dist, "count": n, "slot": slot}
