"""Negative + positive tests for validate_data.py (A5). Builds throw-away data dirs in a temp folder."""
import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import validate_data as V  # noqa: E402

ROOT = V.ROOT
MF = ROOT / "game" / "art" / "manifest" / "sprites.json"

REGION = {"id": "reg_sunset_shoals", "name": "Sunset Shoals", "climate": "tropical", "mood": "golden_hour"}


def isl(n, x, y, tier=2, offers=("fresh_water",), neighbors=(), landmark=False, visible_from=()):
    return {"id": f"isl_{n:03d}", "name": f"Test Isle {n}", "tier": tier, "biome": "palm_atoll", "region": "reg_sunset_shoals",
            "position": {"x_km": x, "y_km": y}, "survival_offers": list(offers), "status": "planned", "landmark": landmark,
            "neighbors": list(neighbors), "visible_from": list(visible_from)}


def nb(i, d, h):
    return {"id": f"isl_{i:03d}", "distance_km": d, "sail_hours_sloop": h}


def world_ok():
    return [isl(1, 0, 0, neighbors=[nb(2, 13.5, 2.7)]), isl(2, 12, 0, neighbors=[nb(1, 13.5, 2.7)]),
            isl(3, 500, 300), isl(4, 40, 900, landmark=True, visible_from=["isl_003"])]


CREW = {"id": "crew_test_sailor", "name": "Test Sailor", "age": 30, "gender": "male", "role": "sailor", "sprite": "spr_crew_mannequin_sailor",
        "stats": {"strength": 5, "endurance": 5, "seamanship": 5, "fighting": 5, "craft": 5}, "loyalty_start": 50}


def build(tmp: Path, islands, crew=None, tuning_patch=None):
    d = tmp / "data"
    if d.exists():
        shutil.rmtree(d)
    shutil.copytree(ROOT / "game" / "data", d)
    (d / "regions").mkdir()
    (d / "regions" / "r.json").write_text(json.dumps({"schema": 1, "kind": "region", "records": [REGION]}))
    (d / "islands").mkdir()
    (d / "islands" / "i.json").write_text(json.dumps({"schema": 1, "kind": "island", "records": islands}))
    if crew is not None:
        (d / "crew").mkdir()
        (d / "crew" / "c.json").write_text(json.dumps({"schema": 1, "kind": "crew_member", "records": crew}))
    if tuning_patch:
        f = d / "tuning" / "tuning_core.json"
        doc = json.loads(f.read_text())
        tuning_patch(doc["records"])
        f.write_text(json.dumps(doc))
    return d


fails = 0


def expect(name, problems, needle=None):
    global fails
    if needle is None:
        ok = not problems
    else:
        ok = any(needle in p for p in problems)
    if not ok:
        fails += 1
        print("FAIL", name, "->", problems[:3])
    else:
        print("ok  ", name)


with tempfile.TemporaryDirectory() as t:
    tmp = Path(t)
    pr, _, _ = V.run()
    expect("real data is clean", pr)
    pr, info, _ = V.run(build(tmp, world_ok(), [CREW]), MF)
    expect("synthetic world + crew is clean", pr)

    w = world_ok(); w[1]["neighbors"] = []
    expect("asymmetric neighbour", V.run(build(tmp, w), MF)[0], "does not list")
    w = world_ok(); w[0]["neighbors"][0]["distance_km"] = 5.0; w[1]["neighbors"][0]["distance_km"] = 5.0
    expect("sail distance shorter than straight line", V.run(build(tmp, w), MF)[0], "shorter than the straight line")
    w = world_ok(); w[1]["neighbors"][0]["sail_hours_sloop"] = 9.0
    expect("different time per direction", V.run(build(tmp, w), MF)[0], "differs between the two directions")
    w = world_ok(); w[3]["landmark"] = False
    expect("visible without landmark flag", V.run(build(tmp, w), MF)[0], "not flagged landmark")
    w = world_ok(); w[2]["survival_offers"] = []
    expect("island with no survival offer", V.run(build(tmp, w), MF)[0], "survival_offers")
    w = world_ok(); w[2]["region"] = "reg_nowhere"
    expect("unknown region reference", V.run(build(tmp, w), MF)[0], "unknown region")
    w = world_ok(); w[2]["id"] = "isl_3"
    expect("bad island id", V.run(build(tmp, w), MF)[0], "$.id")
    w = world_ok(); w[2]["neighbours_typo"] = []
    expect("typo key rejected", V.run(build(tmp, w), MF)[0], "unknown key")
    w = world_ok() + [isl(1, 9, 9)]
    expect("duplicate island id", V.run(build(tmp, w), MF)[0], "duplicate")
    c = copy.deepcopy(CREW); c["gender"] = "female"
    expect("CONTENT RULE 1 at schema level (female crew)", V.run(build(tmp, world_ok(), [c]), MF)[0], "$.gender")
    c = copy.deepcopy(CREW); c["sprite"] = "spr_crew_nonexistent"
    expect("crew sprite must exist in the manifest", V.run(build(tmp, world_ok(), [c]), MF)[0], "unknown asset")

    def patch(rows):
        rows[0]["value"] = 999999
    expect("tuning value outside its allowed range", V.run(build(tmp, world_ok(), None, patch), MF)[0], "outside")


    # save_state schema (shared with game/tests/test_save.gd)
    schemas = V.load_schemas(ROOT / "game" / "data")
    pr, _, res = V.run()
    lk = V.make_lookup(res["tables"], schemas, set(json.loads(MF.read_text())["assets"]))
    st = {"meta": {"profile": "Test", "difficulty": "mode_normal", "playtime_s": 3600}, "clock": {"t_seconds": 123456},
          "rng": {"world_seed": "18446744073709551615", "weather_seed": "42"}, "player": {"x_m": 1234567.891, "y_m": -987654.321, "at_island": ""},
          "inventory": {"item_hardtack": 40, "item_rope": 3}}
    sch = schemas["save_state"]["record"]
    expect("sample save state validates", [str(e) for e in V.M.validate(st, sch, lk)])
    br = copy.deepcopy(st); br["inventory"]["item_unknown_thing"] = 1; br["rng"]["world_seed"] = "not a number"
    n = len(V.M.validate(br, sch, lk))
    expect("broken save state flags exactly 2 errors", [] if n == 2 else [f"got {n}"])
    # difficulty ordering story <= normal <= hardcore, normal == 1.0
    modes = res["tables"]["difficulty_mode"]
    bad = [k for k in modes["mode_normal"]["multipliers"] if not (modes["mode_story"]["multipliers"][k] <= modes["mode_normal"]["multipliers"][k] <= modes["mode_hardcore"]["multipliers"][k] and modes["mode_normal"]["multipliers"][k] == 1.0)]
    expect("difficulty ordering and normal == 1.0", [f"bad keys {bad}"] if bad else [])
    # tuning scaling arithmetic (mirror of game/tests/test_tuning.gd)
    tun = res["tables"]["tuning"]

    def eff(key, mode):
        r = tun[key]
        if "scale" not in r:
            return r["value"]
        m = modes[mode]["multipliers"][r["scale"]]
        return r["value"] / max(m, 0.0001) if r.get("scale_mode", "mul") == "div" else r["value"] * m
    checks = [(eff("food.need_kcal_per_man_day", "mode_normal"), 3200), (eff("food.need_kcal_per_man_day", "mode_story"), 1600), (eff("food.need_kcal_per_man_day", "mode_hardcore"), 4000),
              (eff("health.scurvy_onset_days_no_vitc", "mode_hardcore"), 50), (eff("health.scurvy_onset_days_no_vitc", "mode_story"), 140), (eff("crew.watch_length_hours", "mode_hardcore"), 4),
              (eff("water.need_l_per_man_day_min", "mode_hardcore"), 3.125), (round(eff("crew.awake_limit_hours", "mode_hardcore")), 13)]
    expect("tuning scaling matches the GDScript test expectations", [str(c) for c in checks if abs(c[0] - c[1]) > 1e-9])

print("data tool tests:", "FAIL" if fails else "PASS")
sys.exit(1 if fails else 0)
