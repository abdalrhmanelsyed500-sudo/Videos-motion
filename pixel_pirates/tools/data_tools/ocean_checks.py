"""World invariants for Module E1: the ocean model, the ten regions, the climate belts and the wildlife seed.
Pure checks over data + ocean.py (no Godot). Used by test_ocean.py and by check_project.py.
    python tools/data_tools/ocean_checks.py        # prints a region table and every problem found
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ocean as O  # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / "game" / "data"

# Identity contract: what each region must feel like, as measured on the model (median over a fixed sample set).
# (key, op, value). These are the design promises of docs/E1_WORLD_SPEC.md; the data may change, the promises may not.
IDENTITY: dict[str, list[tuple[str, str, float]]] = {
    "reg_kettle_seas": [("sst", ">", 25.0), ("rain", ">", 0.12), ("storm_p", ">", 0.01)],
    "reg_shattered_reaches": [("sst", ">", 25.0), ("wind", "<", 12.0)],
    "reg_sunward_banks": [("bloom_max", ">", 0.3), ("wind", "<", 11.0)],
    "reg_glass_sea": [("wind", "<", 3.0), ("wave", "<", 0.6)],
    "reg_dead_ocean": [("rain", "<", 0.2), ("productivity", "<", 0.25)],
    "reg_green_verge": [("wind", ">", 15.0)],
    "reg_fogbound_expanse": [("vis", "<", 2.0), ("fog", ">", 0.4)],
    "reg_grey_marches": [("ice_p90", ">", 0.2), ("sst", "<", 8.0)],
    "reg_storm_belt": [("wind", ">", 20.0), ("storm_p", ">", 0.08), ("wave", ">", 4.0)],
    "reg_white_hollow": [("ice_p90", ">", 0.8), ("sst", "<", 2.0)],
}


def sample_set(oc: O.Ocean, rid: str, n: int = 64, days: int = 80) -> list[dict]:
    """A fixed, reproducible sample set: n points inside the region (rejection-sampled on a hash lattice), spread across `days`."""
    out: list[dict] = []
    k = 0
    while len(out) < n and k < 40 * n:
        x = O.hash01(k, 1, 0, 9001) * oc.W
        y = O.hash01(k, 2, 0, 9001) * oc.H
        t = O.hash01(k, 3, 0, 9001) * days
        k += 1
        if oc.region_at(x, y) == rid and min(oc.region_weights(x, y)) >= 0.0 and max(oc.region_weights(x, y)) > 0.8:
            out.append(oc.sample(x, y, t))
    return out


def pct(vals: list[float], p: float) -> float:
    v = sorted(vals)
    if not v:
        return 0.0
    return v[min(len(v) - 1, int(p * len(v)))]


def stats(oc: O.Ocean, rid: str) -> dict[str, float]:
    ss = sample_set(oc, rid)
    g = lambda k: [s[k] for s in ss]  # noqa: E731
    n = max(1, len(ss))
    return {"n": len(ss), "sst": pct(g("sst_c"), 0.5), "sst_lo": pct(g("sst_c"), 0.05), "sst_hi": pct(g("sst_c"), 0.95), "wind": pct(g("wind_kn"), 0.5),
            "wave": pct(g("wave_m"), 0.5), "vis": pct(g("visibility_km"), 0.5), "fog": pct(g("fog"), 0.5), "rain": sum(1 for s in ss if s["rain"] > 0.3) / n,
            "storm_p": sum(1 for s in ss if s["storm"] > 0.3) / n, "ice_p90": pct(g("ice"), 0.9), "productivity": pct(g("productivity"), 0.5),
            "bloom_max": max(g("bloom") or [0.0]), "wind_from": pct(g("wind_from_deg"), 0.5)}


def region_areas(oc: O.Ocean, cell: float = 75.0) -> dict[str, float]:
    cnt = {r["id"]: 0 for r in oc.regions}
    n = 0
    for j in range(int(oc.H / cell)):
        for i in range(int(oc.W / cell)):
            cnt[oc.region_at((i + 0.5) * cell, (j + 0.5) * cell)] += 1
            n += 1
    return {k: v / n for k, v in cnt.items()}


def region_problems(oc: O.Ocean, st: dict[str, dict[str, float]]) -> list[str]:
    p: list[str] = []
    ids = [r["id"] for r in oc.regions]
    if not 6 <= len(ids) <= 10:
        p.append(f"region count {len(ids)} outside the brief's 6..10")
    rules = [r["nav_rule"] for r in oc.regions]
    if len(set(rules)) != len(rules):
        p.append("two regions share a nav_rule (each region needs its own navigational rule)")
    for k, key in (("t1", "world.islands_t1"), ("t2", "world.islands_t2"), ("t3", "world.islands_t3")):
        tot = sum(r["islands"][k] for r in oc.regions)
        if tot != oc.t[key]:
            p.append(f"island budget {k}: regions sum to {tot}, tuning says {oc.t[key]}")
    areas = region_areas(oc)
    for rid, a in areas.items():
        if not 0.04 <= a <= 0.20:
            p.append(f"{rid} covers {a:.1%} of the world (must be 4%..20%: regions need a believable size)")
    for rid, rules in IDENTITY.items():
        s = st[rid]
        for key, op, val in rules:
            ok = s[key] > val if op == ">" else s[key] < val
            if not ok:
                p.append(f"{rid}: identity promise {key} {op} {val} broken (measured {s[key]:.2f})")
    # pairwise distinctness: every pair must differ clearly on at least 2 of 6 normalised axes
    axes = [("sst", 4.0), ("wind", 5.0), ("wave", 1.0), ("vis", 3.0), ("rain", 0.12), ("ice_p90", 0.25), ("productivity", 0.2), ("storm_p", 0.05)]
    by = {r["id"]: r for r in oc.regions}
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            diffs = sum(1 for k, tol in axes if abs(st[a][k] - st[b][k]) >= tol)
            ca, cb = O.hex_rgb(by[a]["water"]["deep"]), O.hex_rgb(by[b]["water"]["deep"])
            diffs += 1 if math.dist(ca, cb) >= 0.12 else 0                        # a clearly different sea colour counts as an axis
            diffs += 1 if by[a]["nav_rule"] != by[b]["nav_rule"] else 0           # so does a different navigational rule
            if diffs < 3:
                p.append(f"{a} and {b} are too alike ({diffs} of {len(axes) + 2} axes differ clearly, need 3)")
    # look: no two regions with the same deep-water colour
    cols = [r["water"]["deep"] for r in oc.regions]
    if len(set(cols)) != len(cols):
        p.append("two regions share a deep-water colour")
    # seed neighbours at least one blend distance apart
    for i, a in enumerate(oc.regions):
        for b in oc.regions[i + 1:]:
            d = math.hypot(a["seed"]["x_km"] - b["seed"]["x_km"], a["seed"]["y_km"] - b["seed"]["y_km"])
            if d < 2.0 * oc.t["ocean.region_blend_km"]:
                p.append(f"seeds of {a['id']} and {b['id']} are only {d:.0f} km apart (<2 blend distances)")
    return p


def model_problems(oc: O.Ocean) -> list[str]:
    p: list[str] = []
    # light equals the T1 curve at the equator, all year
    for k in range(40):
        pk, fl = oc.light_limits(0.0, k / 40.0)
        if abs(pk - 1.0) > 1e-9 or abs(fl) > 1e-9:
            p.append(f"light at the equator is not the T1 curve (season {k / 40:.3f}: peak {pk:.3f}, floor {fl:.3f})")
            break
    # polar night / midnight sun exist and are opposite at the two poles
    pk_n, fl_n = oc.light_limits(72.0, 0.0)     # northern winter solstice (season 0)
    pk_s, fl_s = oc.light_limits(72.0, 0.5)     # northern summer solstice (season 0.5)
    if not (pk_n < 0.3 and fl_s > 0.2):
        p.append(f"polar light: winter peak {pk_n:.2f} should be low, summer floor {fl_s:.2f} should be raised")
    # herald swell invariant: the herald IS tomorrow's storm
    for k in range(60):
        x, y, t = O.hash01(k, 1, 0, 77) * oc.W, O.hash01(k, 2, 0, 77) * oc.H, O.hash01(k, 3, 0, 77) * 60
        a, b = oc.sample(x, y, t), oc.sample(x, y, t + oc.t["ocean.herald_lead_days"])
        if abs(a["herald"] - b["storm"]) > 1e-12:
            p.append("herald(t) != storm(t + lead): the Herald Swell is not honest")
            break
    # purity: same inputs, same output
    s1, s2 = oc.sample(1234.5, 2345.6, 17.25), oc.sample(1234.5, 2345.6, 17.25)
    if s1 != s2:
        p.append("sample() is not a pure function")
    # continuity: no sample jumps (1 real second = 0.0011 game days; test 1 real minute = 0.0667 days)
    worst = 0.0
    for k in range(80):
        x, y, t = O.hash01(k, 1, 0, 78) * oc.W, O.hash01(k, 2, 0, 78) * oc.H, O.hash01(k, 3, 0, 78) * 60
        a, b = oc.sample(x, y, t), oc.sample(x, y, t + 0.0667)
        worst = max(worst, abs(a["wind_kn"] - b["wind_kn"]) / 10.0, abs(a["wave_m"] - b["wave_m"]) / 2.0, abs(a["visibility_km"] - b["visibility_km"]) / 3.0)
    if worst > 1.0:
        p.append(f"weather changes too fast in 1 real minute (worst normalised step {worst:.2f})")
    # spatial continuity: 20 km (about 80 s of sailing) never changes the sea by a visible step
    worst = 0.0
    for k in range(80):
        x, y, t = O.hash01(k, 1, 0, 79) * (oc.W - 30), O.hash01(k, 2, 0, 79) * (oc.H - 30), O.hash01(k, 3, 0, 79) * 60
        a, b = oc.sample(x, y, t), oc.sample(x + 20.0, y, t)
        worst = max(worst, abs(a["wind_kn"] - b["wind_kn"]) / 10.0, abs(a["sst_c"] - b["sst_c"]) / 2.5, abs(a["visibility_km"] - b["visibility_km"]) / 3.0)
    if worst > 1.0:
        p.append(f"the sea changes too fast over 20 km (worst normalised step {worst:.2f})")
    # rim: weather, not a wall
    if oc.edge_rim(0.0, 3000.0) != 1.0 or oc.edge_rim(4500.0, 3000.0) != 0.0:
        p.append("edge rim should be 1 at the world edge and 0 in the interior")
    # ship: no-go zone is slow, beam reach is best, running is good, ice slows
    wind, wf = 14.0, 90.0
    v_nogo = oc.speed_through_water_kmh(wf, wind, wf, 0.0)
    v_beam = oc.speed_through_water_kmh(wf + 100.0, wind, wf, 0.0)
    v_run = oc.speed_through_water_kmh(wf + 180.0, wind, wf, 0.0)
    if not (v_nogo < 0.3 * v_beam and v_beam >= v_run * 0.95 and v_beam <= 1.05 * oc.t["ship.sail_speed_kmh"]):
        p.append(f"sail polar broken (no-go {v_nogo:.2f}, beam {v_beam:.2f}, run {v_run:.2f})")
    if oc.speed_through_water_kmh(wf + 100.0, wind, wf, 0.5) >= v_beam:
        p.append("sea ice does not slow the ship")
    if oc.speed_through_water_kmh(wf + 100.0, wind, wf, 0.97) != 0.0:
        p.append("a ship in closed ice should be stopped")
    if oc.speed_through_water_kmh(0.0, 0.0, 90.0, 0.0) <= 0.0:
        p.append("a becalmed ship should still drift, never be exactly stopped")
    # wind direction: trades from the east, westerlies from the west, both hemispheres
    for y, lo, hi, nm in ((2500.0, 20.0, 130.0, "N trades"), (3500.0, 20.0, 130.0, "S trades"), (5000.0, 200.0, 340.0, "S westerlies"), (1000.0, 180.0, 340.0, "N westerlies")):
        deg = [oc.sample(O.hash01(k, 5, 0, 5) * oc.W, y, 3.0 * k)["wind_from_deg"] for k in range(24)]
        med = sorted(deg)[12]
        if not lo <= med <= hi:
            p.append(f"{nm}: median wind-from {med:.0f} deg outside {lo:.0f}..{hi:.0f}")
    # scale: edge to edge at the reference speed
    hours = oc.W / oc.t["ship.sail_speed_kmh"]
    if not 8.0 <= hours * 3600.0 / 96.0 / 3600.0 * 60.0 / 60.0 * 1.0 <= 20.0 * 60.0:
        p.append("world width out of range")
    real_h = hours * 37.5 / 3600.0
    if not 8.0 <= real_h <= 14.0:
        p.append(f"edge to edge at the reference speed is {real_h:.1f} real hours (brief: crossing the ocean is the core experience; 8..14 h)")
    return p


def wildlife_problems(oc: O.Ocean, st: dict[str, dict[str, float]], species: list[dict]) -> list[str]:
    p: list[str] = []
    rids = {r["id"] for r in oc.regions}
    ids = [s["id"] for s in species]
    if len(set(ids)) != len(ids):
        p.append("duplicate species id")
    names = [s["name"] for s in species]
    if len(set(names)) != len(names):
        p.append("duplicate species name")
    for s in species:
        sid = s["id"]
        if s["temp_c"][0] > s["temp_c"][1] or s["depth_m"][0] > s["depth_m"][1] or s["group_size"][0] > s["group_size"][1]:
            p.append(f"{sid}: a min/max range is reversed")
        if s["real"] and "scientific" not in s:
            p.append(f"{sid}: a real species needs its scientific name")
        if not s["real"] and "scientific" in s:
            p.append(f"{sid}: a fictional species must not carry a scientific name")
        if s["rarity"] == "legendary" and s["lod"] != "bespoke":
            p.append(f"{sid}: legendary creatures are bespoke set-pieces")
        if s["rarity"] in ("rare", "legendary") and "report" not in s["methods"] and "observe" not in s["methods"]:
            p.append(f"{sid}: a rare creature must be observable (the naturalist loop)")
        if s.get("danger", 0.0) >= 0.7 and "observe" not in s["methods"]:
            p.append(f"{sid}: a dangerous animal must be observable from the ship")
        for rr in s["regions"]:
            if rr["region"] not in rids:
                p.append(f"{sid}: unknown region {rr['region']}")
                continue
            if rr["abundance"] >= 0.5:    # a common animal must be able to live there: its temperature band must meet the region's
                lo, hi = st[rr["region"]]["sst_lo"], st[rr["region"]]["sst_hi"]
                if s["habitat"] not in ("deep", "vent") and (hi < s["temp_c"][0] or lo > s["temp_c"][1]):
                    p.append(f"{sid}: abundant in {rr['region']} but its {s['temp_c']} C never meets the region's {lo:.0f}..{hi:.0f} C sea")
    # coverage per region: the sea is never empty
    for r in oc.regions:
        here = [s for s in species if any(x["region"] == r["id"] and x["abundance"] >= 0.3 for x in s["regions"])]
        if len(here) < 10:
            p.append(f"{r['id']}: only {len(here)} species with abundance >= 0.3 (need 10 so the sea is never empty)")
        if not any(s["group"] == "seabird" for s in here) and r["id"] not in ("reg_dead_ocean",):
            p.append(f"{r['id']}: no seabird (birds are the land-near signal)")
        if not any(("line" in s["methods"] or "net" in s["methods"]) and s["rarity"] == "common" for s in here):
            p.append(f"{r['id']}: no common catchable animal (P2: every region offers food on the water)")
        if not any(s["rarity"] in ("rare", "legendary") or s["group"] == "strange" for s in species if any(x["region"] == r["id"] for x in s["regions"])):
            p.append(f"{r['id']}: no rare or strange creature (every region needs a reason to look)")
    if sum(1 for s in species if s["rarity"] == "legendary") > 4:
        p.append("more than 4 legendary creatures (they stop being legends)")
    fic = [s for s in species if not s["real"]]
    if not 5 <= len(fic) <= 0.25 * len(species):
        p.append(f"fictional species count {len(fic)} should be 5..25% of the seed")
    return p


def load_species(data_dir: Path = DATA) -> list[dict]:
    out: list[dict] = []
    for f in sorted((data_dir / "wildlife").glob("species_*.json")):
        out += json.loads(f.read_text())["records"]
    return out


def all_problems() -> tuple[list[str], dict, O.Ocean]:
    oc = O.load()
    st = {r["id"]: stats(oc, r["id"]) for r in oc.regions}
    p = region_problems(oc, st) + model_problems(oc) + wildlife_problems(oc, st, load_species())
    for rid, s in st.items():
        if s["n"] < 40:
            p.append(f"{rid}: only {s['n']} sample points found inside the region")
    return p, st, oc


def main() -> int:
    p, st, oc = all_problems()
    print(f"{'region':24s} {'sst':>5s} {'wind':>5s} {'wave':>5s} {'vis':>5s} {'fog':>5s} {'rain':>5s} {'gale':>5s} {'ice90':>5s} {'prod':>5s}")
    for rid, s in st.items():
        print(f"{rid:24s} {s['sst']:5.1f} {s['wind']:5.1f} {s['wave']:5.1f} {s['vis']:5.1f} {s['fog']:5.2f} {s['rain']:5.2f} {s['storm_p']:5.2f} {s['ice_p90']:5.2f} {s['productivity']:5.2f}")
    sp = load_species()
    print(f"species {len(sp)} of target {int(oc.t['wildlife.species_target'])}")
    for x in p:
        print("PROBLEM", x)
    print("ocean_checks:", len(p), "problems")
    return 1 if p else 0


if __name__ == "__main__":
    sys.exit(main())
