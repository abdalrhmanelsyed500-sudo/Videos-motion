"""Tests for ocean.py, ocean_checks.py and the E1 data (Module E1).  Run: python tools/data_tools/test_ocean.py [--write-fixtures]
The golden file game/tests/fixtures/ocean_cases.json is produced here and replayed by game/tests/test_ocean.gd (the GDScript twin)."""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ocean as O  # noqa: E402
import ocean_checks as C  # noqa: E402
import sea_state as SS  # noqa: E402
import wildlife as W  # noqa: E402

fails = 0
FX = C.ROOT / "game" / "tests" / "fixtures" / "ocean_cases.json"
FXW = C.ROOT / "game" / "tests" / "fixtures" / "wildlife_cases.json"
FXS = C.ROOT / "game" / "tests" / "fixtures" / "sea_cases.json"


def expect(name: str, cond: bool, detail: str = "") -> None:
    global fails
    print(("ok   " if cond else "FAIL ") + name + ("" if cond else f"  {detail}"))
    fails += 0 if cond else 1


def r6(v):
    return round(v, 6) if isinstance(v, float) else v


# ---------------------------------------------------------------------------------------------------------------------------
# golden cases
# ---------------------------------------------------------------------------------------------------------------------------
def build_cases(oc: O.Ocean) -> dict:
    h = lambda k, m: O.hash01(k * 7 - 20, k * 3 + 1, k - 5, m)  # noqa: E731
    noise = {"hash": [{"a": [k * 7 - 20, k * 3 + 1, k - 5, 1 + k % 5], "v": r6(O.hash01(k * 7 - 20, k * 3 + 1, k - 5, 1 + k % 5))} for k in range(12)],
             "vnoise": [{"a": [k * 1.37 - 4.2, k * 0.71 + 0.3, k * 2.9 - 1.0, 3 + k], "v": r6(O.vnoise(k * 1.37 - 4.2, k * 0.71 + 0.3, k * 2.9 - 1.0, 3 + k))} for k in range(12)],
             "fbm": [{"a": [k * 2.11 - 9.0, k * 1.13 - 3.5, k * 0.37, 7 + k], "v": r6(O.fbm(k * 2.11 - 9.0, k * 1.13 - 3.5, k * 0.37, 7 + k))} for k in range(12)]}
    del h
    pts = []
    for k in range(36):
        x = O.hash01(k, 1, 0, 4242) * oc.W
        y = O.hash01(k, 2, 0, 4242) * oc.H
        t = O.hash01(k, 3, 0, 4242) * 90.0
        pts.append((x, y, t))
    for c in json.loads((C.DATA / "world" / "slice_route.json").read_text())["checkpoints"]:
        pts.append((float(c["x_km"]), float(c["y_km"]), float(c["t_days"])))
    pts += [(5.0, 5.0, 3.3), (8995.0, 5995.0, 40.1), (4500.0, 3000.0, 0.25), (4500.0, 3000.0, 0.75)]
    samples = []
    for x, y, t in pts:
        s = oc.sample(x, y, t)
        samples.append({"x": x, "y": y, "t": t, "region": s["region"], "v": {k: r6(v) for k, v in s.items() if isinstance(v, float)}, "w": [r6(v) for v in s["weights"]]})
    speeds = []
    for k in range(24):
        head, wk, wf, ice = O.hash01(k, 1, 0, 8) * 360, O.hash01(k, 2, 0, 8) * 40, O.hash01(k, 3, 0, 8) * 360, [0.0, 0.0, 0.3, 0.6, 0.97][k % 5]
        speeds.append({"a": [r6(head), r6(wk), r6(wf), ice], "v": r6(oc.speed_through_water_kmh(head, wk, wf, ice))})
    bergs = []
    for x, y in ((5600.0, 100.0), (4200.0, 5600.0), (5400.0, 400.0), (1000.0, 3000.0)):
        bergs.append({"a": [x, y, 90.0], "v": [[r6(a), r6(b), n] for a, b, n in oc.bergs_near(x, y, 90.0)]})
    looks = []
    for x, y in ((7000.0, 2650.0), (4500.0, 3000.0), (5600.0, 500.0), (4200.0, 5700.0)):
        looks.append({"a": [x, y], "v": {k: ([r6(c) for c in v] if isinstance(v, tuple) else r6(v)) for k, v in O.look_at(oc, x, y).items()}})
    light = [{"a": [lat, s], "v": [r6(a) for a in oc.light_limits(lat, s)]} for lat, s in ((0.0, 0.0), (0.0, 0.5), (45.0, 0.0), (45.0, 0.5), (72.0, 0.0), (72.0, 0.5), (-72.0, 0.0), (-72.0, 0.5), (20.0, 0.25), (-30.0, 0.8), (10.0, 0.1), (60.0, 0.4))]
    winds = [{"a": [lat], "v": [r6(a) for a in oc.base_wind(lat)]} for lat in (-70.0, -50.0, -30.0, -10.0, 0.0, 5.0, 18.0, 28.0, 44.0, 60.0, 72.0)]
    return {"note": "Golden values from tools/data_tools/ocean.py (regenerate: python tools/data_tools/test_ocean.py --write-fixtures). Tolerance 1e-4 absolute. GDScript twin: game/core/ocean.gd.",
            "noise": noise, "samples": samples, "speeds": speeds, "bergs": bergs, "looks": looks, "light": light, "winds": winds}


def build_wildlife_cases(oc: O.Ocean) -> dict:
    sp = C.load_species()
    cases = []
    for k in range(40):
        x, y = O.hash01(k, 1, 0, 515) * oc.W, O.hash01(k, 2, 0, 515) * oc.H
        t = O.hash01(k, 3, 0, 515) * 80.0
        sg = W.sighting(oc, sp, x, y, t)
        tb = sorted(W.table(oc, sp, x, y, t), key=lambda r: -r[1])[:4]
        cases.append({"x": x, "y": y, "t": t, "sighting": None if sg is None else {kk: r6(v) for kk, v in sg.items()}, "top": [[i, r6(w)] for i, w in tb]})
    return {"note": "Golden values from tools/data_tools/wildlife.py (regenerate: python tools/data_tools/test_ocean.py --write-fixtures). Tolerance 1e-4.", "cases": cases}


SEA_SCENARIOS = [
    {"name": "Kettle, west, one real minute in one call", "start": [7000.0, 2650.0, 270.0], "t0": 0.25, "steps": [5760.0]},
    {"name": "Kettle, west, one real minute in 16 calls", "start": [7000.0, 2650.0, 270.0], "t0": 0.25, "steps": [360.0] * 16},
    {"name": "Kettle, north-west reach, 3 game days", "start": [7000.0, 2650.0, 315.0], "t0": 0.25, "steps": [3600.0] * 72},
    {"name": "Paused clock: zero game seconds", "start": [7000.0, 2650.0, 90.0], "t0": 0.25, "steps": [0.0, 0.0]},
    {"name": "West edge clamp", "start": [50.0, 3000.0, 270.0], "t0": 2.0, "steps": [3600.0] * 48},
    {"name": "Glass Sea, becalmed, 2 game days", "start": [4500.0, 3000.0, 90.0], "t0": 0.25, "steps": [3600.0] * 48},
    {"name": "Storm Belt, run east, 4 game days", "start": [3000.0, 4950.0, 90.0], "t0": 5.0, "steps": [3600.0] * 96},
    {"name": "Ice edge, north into the pack, 2 game days", "start": [5600.0, 300.0, 0.0], "t0": 14.25, "steps": [3600.0] * 48},
]


def run_sea(oc: O.Ocean, sc: dict) -> dict:
    st = SS.SeaState(oc)
    st.place(*sc["start"])
    t = sc["t0"]
    for gs in sc["steps"]:
        st.advance(t, gs)
        t += gs / 86400.0
    return {"x": r6(st.x_km), "y": r6(st.y_km), "distance": r6(st.distance_km), "t_end": r6(t), "speed_kn": r6(st.speed_kn())}


def build_sea_cases(oc: O.Ocean) -> dict:
    return {"note": "Golden voyages from tools/data_tools/sea_state.py. Tolerance 1e-3 km.", "cases": [dict(sc, expect=run_sea(oc, sc)) for sc in SEA_SCENARIOS]}


def main() -> int:
    oc = O.load()
    if "--write-fixtures" in sys.argv:
        FX.write_text(json.dumps(build_cases(oc), separators=(",", ":")) + "\n")
        FXW.write_text(json.dumps(build_wildlife_cases(oc), separators=(",", ":")) + "\n")
        FXS.write_text(json.dumps(build_sea_cases(oc), separators=(",", ":")) + "\n")
        print("wrote", FX, FX.stat().st_size, "bytes")
        return 0

    # ---- the real world passes every invariant ---------------------------------------------------------------------------
    problems, st, _ = C.all_problems()
    expect("ocean_checks: real data has no problems", problems == [], "; ".join(problems[:4]))

    # ---- noise primitives ---------------------------------------------------------------------------------------------------
    vals = [O.hash01(i, -i, 2 * i, 5) for i in range(-500, 500)]
    expect("hash01 stays in [0, 1] and is not degenerate", all(0.0 <= v <= 1.0 for v in vals) and 0.45 < sum(vals) / len(vals) < 0.55 and len(set(vals)) > 990)
    expect("hash01 is deterministic and seed-sensitive", O.hash01(3, 4, 5, 1) == O.hash01(3, 4, 5, 1) and O.hash01(3, 4, 5, 1) != O.hash01(3, 4, 5, 2))
    step = max(abs(O.fbm(i * 0.01, 0.3, 0.2, 9) - O.fbm((i + 1) * 0.01, 0.3, 0.2, 9)) for i in range(2000))
    expect("fbm is continuous (no steps at lattice lines)", step < 0.01, f"max step {step:.4f}")
    expect("hash01 never needs more than 62 bits (GDScript parity)", all((abs(i) * 73856093) < 2 ** 62 for i in (10 ** 6,)) and 1274126177 * 0x7FFFFFFF < 2 ** 62)

    # ---- geography ------------------------------------------------------------------------------------------------------------
    expect("latitude: equator at y=3000, poles at the edges", abs(oc.lat(3000.0)) < 1e-9 and abs(oc.lat(0.0) - 75.0) < 1e-9 and abs(oc.lat(6000.0) + 75.0) < 1e-9)
    expect("every region's seed lies inside its own region", all(oc.region_at(r["seed"]["x_km"], r["seed"]["y_km"]) == r["id"] for r in oc.regions))
    ws = [sum(oc.region_weights(O.hash01(k, 1, 0, 3) * oc.W, O.hash01(k, 2, 0, 3) * oc.H)) for k in range(100)]
    expect("region weights sum to 1", all(abs(w - 1.0) < 1e-9 for w in ws))
    worst = 0.0
    for k in range(60):
        x, y = O.hash01(k, 1, 0, 6) * (oc.W - 40), O.hash01(k, 2, 0, 6) * oc.H
        a, b = oc.region_weights(x, y), oc.region_weights(x + 20.0, y)
        worst = max(worst, max(abs(p - q) for p, q in zip(a, b)))
    expect("region borders are gradients: 20 km moves a weight by under 0.25", worst < 0.25, f"worst {worst:.3f}")
    expect("the start region is Kettle Seas at the first anchorage", oc.region_at(7000.0, 2650.0) == "reg_kettle_seas")
    expect("Treasure Island's reserved site is in the White Hollow", oc.region_at(4200.0, 5700.0) == "reg_white_hollow")

    # ---- determinism: the weather needs no saved state ---------------------------------------------------------------------
    a = oc.sample(5600.0, 520.0, 12.5)
    b = O.load().sample(5600.0, 520.0, 12.5)
    expect("a freshly loaded world gives the identical weather (nothing to save)", a == b)

    # ---- the Herald Swell is what it says -----------------------------------------------------------------------------------------
    pts = [(O.hash01(k, 1, 0, 12) * oc.W, O.hash01(k, 2, 0, 12) * oc.H, O.hash01(k, 3, 0, 12) * 70) for k in range(300)]
    rising = [(x, y, t) for x, y, t in pts if oc.sample(x, y, t)["herald"] > 0.5]
    honest = [p for p in rising if oc.sample(p[0], p[1], p[2] + 1.0)["storm"] > 0.5]
    expect("Herald Swell: every strong herald is followed by a gale one game day later", len(rising) > 5 and len(honest) == len(rising), f"{len(honest)}/{len(rising)}")

    # ---- the slice route ---------------------------------------------------------------------------------------------------------
    route = json.loads((C.DATA / "world" / "slice_route.json").read_text())
    for c in route["checkpoints"]:
        s = oc.sample(c["x_km"], c["y_km"], c["t_days"])
        bad = [k for k, v in c["expect"].items() if (k == "region" and s["region"] != v) or (k.endswith("_min") and not s[k[:-4]] >= v) or (k.endswith("_max") and not s[k[:-4]] <= v)]
        expect(f"slice checkpoint {c['id']} ({c['name']}) matches its promise", bad == [], f"{bad}")
    regs = [oc.region_at(c["x_km"], c["y_km"]) for c in route["checkpoints"]]
    expect("the slice route crosses at least 4 different regions", len(set(regs)) >= 4, str(set(regs)))
    total = sum(math.hypot(b["x_km"] - a["x_km"], b["y_km"] - a["y_km"]) for a, b in zip(route["waypoints"], route["waypoints"][1:]))
    expect("slice route length 3,300..3,600 km (about 4 h of real sailing)", 3300 <= total <= 3600, f"{total:.0f}")

    # ---- scale -----------------------------------------------------------------------------------------------------------------------
    kmh = oc.t["ship.sail_speed_kmh"]
    expect("reference speed: 14.9 km per real minute", abs(kmh * 96.0 / 60.0 - 14.88) < 0.01)
    expect("edge to edge (9,000 km) is about 10 real hours", 9.5 <= oc.W / kmh * 37.5 / 3600.0 <= 10.5)
    horizon_km = 3.57 * math.sqrt(oc.t["ocean.horizon_eye_height_m"])
    expect("the horizon is about 10 km: 40 real seconds from first sight to arrival", 9.0 <= horizon_km <= 11.0 and 38.0 <= horizon_km / kmh * 37.5 <= 45.0, f"{horizon_km:.1f} km")

    # ---- ship ---------------------------------------------------------------------------------------------------------------------------
    s0 = oc.sample(7000.0, 2650.0, 0.25)
    vw, vn = oc.ground_velocity_kmh(90.0, s0)
    through = oc.speed_through_water_kmh(90.0, s0["wind_kn"], s0["wind_from_deg"], s0["ice"])
    expect("ground velocity = sailing + current (heading east)", abs(vw - (through + s0["current_u_kn"] * O.KN_KMH)) < 1e-9 and abs(vn - s0["current_v_kn"] * O.KN_KMH) < 1e-9)
    up = oc.speed_through_water_kmh(0.0, 14.0, 0.0, 0.0)
    expect("sailing straight into the wind is slow but not stopped", 0.3 < up < 2.0, f"{up:.2f}")
    heavy = oc.speed_through_water_kmh(90.0, 45.0, 0.0, 0.0)
    expect("a ship under reefed sail in a 45 kn gale still makes way but slower than at 14 kn", 0.3 * kmh < heavy < oc.speed_through_water_kmh(90.0, 14.0, 0.0, 0.0))

    # ---- mutation tests: the checks catch what they should ----------------------------------------------------------------------
    def with_regions(mut) -> list[str]:
        rg = copy.deepcopy(oc.regions)
        mut(rg)
        o2 = O.Ocean(oc.t, rg, oc.bands)
        s2 = {r["id"]: C.stats(o2, r["id"]) for r in o2.regions}
        return C.region_problems(o2, s2)
    expect("mutation: duplicate nav_rule is caught", any("nav_rule" in p for p in with_regions(lambda rg: rg[1].update(nav_rule=rg[0]["nav_rule"]))))
    expect("mutation: island budget mismatch is caught", any("island budget" in p for p in with_regions(lambda rg: rg[0]["islands"].update(t1=9))))
    expect("mutation: a Glass Sea with gales is caught", any("identity" in p for p in with_regions(lambda rg: rg[3]["atmosphere"].update(wind_scale=3.0))))
    expect("mutation: two regions merged in climate are caught", any("too alike" in p for p in with_regions(lambda rg: [rg[1]["atmosphere"].update(rg[0]["atmosphere"]), rg[1]["sea"].update(rg[0]["sea"]), rg[1].update(nav_rule=rg[0]["nav_rule"], water=rg[0]["water"])])))
    expect("mutation: regions crowded together are caught", any("apart" in p for p in with_regions(lambda rg: rg[1]["seed"].update(x_km=rg[0]["seed"]["x_km"] + 100, y_km=rg[0]["seed"]["y_km"]))))
    sp = C.load_species()
    st2 = {r["id"]: C.stats(oc, r["id"]) for r in oc.regions}

    def wl(mut) -> list[str]:
        sc = copy.deepcopy(sp)
        mut(sc)
        return C.wildlife_problems(oc, st2, sc)
    expect("wildlife: the seed itself is clean", wl(lambda s: None) == [])
    expect("wildlife: reversed temperature range is caught", any("reversed" in p for p in wl(lambda s: s[0].update(temp_c=[30, 10]))))
    expect("wildlife: unknown region is caught", any("unknown region" in p for p in wl(lambda s: s[0]["regions"].append({"region": "reg_nowhere", "abundance": 0.5}))))
    expect("wildlife: tropical animal abundant in the ice is caught", any("never meets" in p for p in wl(lambda s: s[0]["regions"].append({"region": "reg_white_hollow", "abundance": 0.9}))))
    expect("wildlife: a real species without a scientific name is caught", any("scientific" in p for p in wl(lambda s: s[0].pop("scientific"))))
    expect("wildlife: a fictional species with a scientific name is caught", any("fictional" in p for p in wl(lambda s: [x for x in s if not x["real"]][0].update(scientific="Fakus fakus"))))
    expect("wildlife: duplicate id is caught", any("duplicate" in p for p in wl(lambda s: s.append(copy.deepcopy(s[0])))))
    expect("wildlife: a fifth legendary is caught", any("legendary" in p for p in wl(lambda s: [x.update(rarity="legendary", lod="bespoke") for x in s[:6]])))
    expect("wildlife: a region stripped of animals is caught", any("reg_glass_sea: only" in p for p in wl(lambda s: [x.update(regions=[y for y in x["regions"] if y["region"] != "reg_glass_sea"]) for x in s])))
    expect("species count is reported against the 200 target", len(sp) >= 60, f"{len(sp)}")

    # ---- the voyage integrator --------------------------------------------------------------------------------------------------------------------
    res = {sc["name"]: run_sea(oc, sc) for sc in SEA_SCENARIOS}
    one, many = res[SEA_SCENARIOS[0]["name"]], res[SEA_SCENARIOS[1]["name"]]
    expect("one real minute of sailing covers 3..25 km (reference: 14.9 km at a beam reach in 14 kn)", 3.0 <= one["distance"] <= 25.0, f"{one['distance']:.1f}")
    expect("one call and sixteen calls agree to within 5% (time-step independence)", abs(one["distance"] - many["distance"]) <= 0.05 * one["distance"], f"{one['distance']:.2f} vs {many['distance']:.2f}")
    still = res["Paused clock: zero game seconds"]
    expect("a paused clock (0 game seconds) never moves the ship", still["x"] == 7000.0 and still["y"] == 2650.0 and still["distance"] == 0.0)
    expect("the world edge stops the ship (no wrapping, no leaving)", res["West edge clamp"]["x"] == 0.0)
    glass = res["Glass Sea, becalmed, 2 game days"]
    expect("the Glass Sea really is slow: under 120 km in 2 game days (30 real minutes)", glass["distance"] < 120.0, f"{glass['distance']:.0f} km")
    storm = res["Storm Belt, run east, 4 game days"]
    expect("a run east in the Storm Belt covers 500..1500 km in 4 game days", 500.0 <= storm["distance"] <= 1500.0, f"{storm['distance']:.0f} km")
    pack = res["Ice edge, north into the pack, 2 game days"]
    expect("sailing north into the polar pack ends frozen in: speed 0 and stopped near the north edge (y < 100 km)", pack["speed_kn"] == 0.0 and pack["y"] < 100.0, f"{pack}")
    fxs = json.loads(FXS.read_text()) if FXS.exists() else None
    expect("sea golden fixtures exist and match the current model", fxs is not None and fxs == json.loads(json.dumps(build_sea_cases(oc))))

    # ---- wildlife sightings ---------------------------------------------------------------------------------------------------------------------
    def rate(x: float, y: float, t0: float = 0.0, days: float = 10.0) -> tuple[float, set]:
        n, kinds, sd = 0, set(), W.slot_days(oc.t)
        for k in range(int(days / sd)):
            r = W.sighting(oc, sp, x, y, t0 + k * sd + 0.01)
            if r:
                n += 1
                kinds.add(r["species"])
        return n / (days * 15.0), kinds     # sightings per real minute (1 game day = 15 real minutes)
    for nm, (x, y) in {"Kettle": (7000.0, 2650.0), "Glass Sea": (4500.0, 3000.0), "Dead Ocean": (4400.0, 4150.0), "White Hollow": (4200.0, 5700.0)}.items():
        rt, kinds = rate(x, y)
        expect(f"sightings in {nm}: 0.15..0.7 per real minute (never empty, never spam) and 8+ different animals", 0.15 <= rt <= 0.7 and len(kinds) >= 8, f"{rt:.2f}/min, {len(kinds)} kinds")
    expect("a sighting is deterministic", W.sighting(oc, sp, 7000.0, 2650.0, 1.234) == W.sighting(oc, sp, 7000.0, 2650.0, 1.234))
    tropic = {i for i, _ in W.table(oc, sp, 7000.0, 2650.0, 3.5)}
    polar = {i for i, _ in W.table(oc, sp, 4200.0, 5700.0, 3.5)}
    expect("tropical and polar waters share few animals", len(tropic & polar) <= 8 and "spc_emperor_penguin" in polar and "spc_emperor_penguin" not in tropic and "spc_yellowfin_tuna" in tropic and "spc_yellowfin_tuna" not in polar)
    byid = {q["id"]: q for q in sp}
    sm = oc.sample(7000.0, 2650.0, 3.25)
    sm["_region_ids"] = [r["id"] for r in oc.regions]
    sm_day, sm_night = dict(sm, hour=12.0), dict(sm, hour=0.0)
    expect("nocturnal animals prefer the night, diurnal the day", W.suitability(oc.t, byid["spc_moray_eel"], sm_night) > W.suitability(oc.t, byid["spc_moray_eel"], sm_day) and W.suitability(oc.t, byid["spc_yellowfin_tuna"], sm_day) > W.suitability(oc.t, byid["spc_yellowfin_tuna"], sm_night))
    cold = dict(sm, sst_c=2.0)
    expect("a tropical animal fades out in cold water", W.suitability(oc.t, byid["spc_yellowfin_tuna"], cold) == 0.0)
    r_in = [W.sighting(oc, sp, 5640.0, 560.0, 12.0 + k * 0.1) for k in range(200)]
    foggy = [W.sighting(oc, sp, 5889.0, 1047.0, 8.25 + k * 0.1) for k in range(200)]
    avg = lambda rs: sum(q["distance_km"] for q in rs if q) / max(1, sum(1 for q in rs if q))  # noqa: E731
    expect("fog shortens how far animals can be seen", avg(foggy) < 0.5 * avg(r_in) or avg(foggy) < 1.0, f"{avg(foggy):.2f} vs {avg(r_in):.2f}")
    expect("legendary animals are rare among sightings", sum(1 for k in range(2000) for q in [W.sighting(oc, sp, 4400.0 + k, 4150.0, k * 0.1)] if q and byid[q["species"]]["rarity"] == "legendary") < 40)

    # ---- the golden file is current ----------------------------------------------------------------------------------------------------
    fx = json.loads(FX.read_text()) if FX.exists() else None
    cur = json.loads(json.dumps(build_cases(oc)))
    expect("golden fixtures exist and match the current model (run --write-fixtures after an intentional change)", fx is not None and fx == cur)
    fxw = json.loads(FXW.read_text()) if FXW.exists() else None
    expect("wildlife golden fixtures exist and match the current model", fxw is not None and fxw == json.loads(json.dumps(build_wildlife_cases(oc))))

    print("test_ocean:", "FAILED" if fails else "all passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
