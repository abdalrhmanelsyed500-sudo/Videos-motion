"""Python twin of the CP-1 starting economy: game/h2d/port_state.gd (purse, hold, freshness, selling, hiring) and game/h2d/fishing.gd
(the haul rule and the deterministic random stream). Same equations, same keys. Used to
  (1) own the tuning table written to game/data/tuning/tuning_port.json,
  (2) write the fixture game/tests/fixtures/economy_cases.json that tests/test_port.gd replays,
  (3) PROVE the balance: a simulated first hour of the prologue (time to the first and the last hire, income per minute per ground).
This is a model of the GDScript, NOT a Godot run.

  python tools/h2d/economy_logic.py --write    # rewrite tuning_port.json and the fixture
  python tools/h2d/economy_logic.py --check    # fail if either differs from this file, if the GDScript DEFAULTS drift, or the balance breaks
  python tools/h2d/economy_logic.py            # print the balance report (every price and the time to afford each recruit)

The market is core/market.gd (twin tools/data_tools/market.py): price = base x factor x exp(x) x (1 - spread/2); selling V (in base
value) moves x by V/depth; x forgets with a half-life. Fish lots lose freshness linearly with age (a cook slows it).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data_tools"))
import market as MK  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TUNING = ROOT / "game/data/tuning/tuning_port.json"
FIXTURE = ROOT / "game/tests/fixtures/economy_cases.json"
DATA = ROOT / "game/data/port"
GD_STATE = ROOT / "game/h2d/port_state.gd"
GD_FISH = ROOT / "game/h2d/fishing.gd"
SRC = "CP-1 Fish Row slice; first values chosen by simulation (economy_logic.py), confirm by hand on the dev PC"
ECON = json.loads((ROOT / "game/data/tuning/tuning_economy.json").read_text())["records"]
SPREAD_PCT = next(r["value"] for r in ECON if r["key"] == "market.spread_pct")
HALF_LIFE = next(r["value"] for r in ECON if r["key"] == "market.recovery_half_life_days")

# key, value, unit, min, max, owner, note (keys are fish.* / port.*; market.* comes from B4's tuning_economy.json)
TABLE = [
    ("port.start_reales", 5, "reales", 0, 600, "B4", "Prologue purse: five reales, the price of a loaf and a bed. B4's 600 is the campaign purse after the first prize; the prologue is meant to be poor."),
    ("port.hold_kg", 40, "kg", 10, 200, "B4", "Fish hold of the bare sloop. One haul is about 1.2 kg, so a full hold is about 33 hauls = 6.7 minutes of nets."),
    ("port.hold_warn_frac", 0.85, "fraction", 0.5, 1, "B4", "The HUD turns the hold amber at this fill."),
    ("fish.haul_interval_s", 12, "seconds", 4, 60, "B4", "INCOME MODEL ONLY (CP-2B.1: the game has no timed hauls; fishing is manual at the winch). Real seconds between hauls while the nets are down and the ship is slow enough."),
    ("fish.haul_kg", 1.2, "kg", 0.2, 10, "B4", "INCOME MODEL ONLY (CP-2B.1: the game has no timed hauls; fishing is manual at the winch). Average kg of one haul on a ground of richness 1.0 at midday, before crew bonuses."),
    ("fish.haul_spread", 0.4, "fraction", 0, 0.9, "B4", "INCOME MODEL ONLY (CP-2B.1: the game has no timed hauls; fishing is manual at the winch). A haul varies by plus or minus this fraction (uniform) around its average."),
    ("fish.max_speed_kn", 1.5, "knots", 0.2, 5, "B4", "The nets only work while the ship is slower than this; the ship drifts to a stop once the nets are down."),
    ("fish.max_sea", 0.6, "sea index 0..1", 0.2, 1, "B4", "In a rougher sea the nets are hauled in and fishing stops."),
    ("fish.mult_dawn", 1.3, "factor", 0.5, 3, "B4", "INCOME MODEL ONLY (CP-2B.1: the game has no timed hauls; fishing is manual at the winch). Fish bite better in the thin light of dawn (05:00-07:00) and dusk (17:00-19:00), the T1 bands."),
    ("fish.mult_day", 1.0, "factor", 0.5, 3, "B4", "INCOME MODEL ONLY (CP-2B.1: the game has no timed hauls; fishing is manual at the winch). Bite rate in daylight and in the evening."),
    ("fish.mult_night", 0.7, "factor", 0.2, 3, "B4", "INCOME MODEL ONLY (CP-2B.1: the game has no timed hauls; fishing is manual at the winch). Bite rate at night (20:00-05:00): fishing is possible but slower."),
    ("fish.spoil_per_day", 0.35, "freshness per game day", 0.05, 2, "B4", "Fresh fish loses this fraction of its value per game day (15 real minutes); a catch is worth about 95% after a 4-minute trip."),
    ("fish.spoil_floor", 0.25, "fraction", 0, 1, "B4", "Spoiled fish still sells for this fraction (fish meal and bait): it is never worthless, but it hurts."),
    ("fish.spoil_warn", 0.7, "fraction", 0.2, 1, "B4", "The HUD warns when the average freshness of the hold falls below this."),
    ("market.fish_depth_reales", 150, "reales", 20, 5000, "B4", "Depth of the Fish Row market PER SPECIES: selling 150 reales of one species in one go drops its price by 1/e (37%). T1 ports are 4500 across all goods; a fish stall is a small market."),
]
P = {k: float(v) for k, v, *_ in TABLE}
DEPTH_KEY, SPREAD, HALF = "market.fish_depth_reales", float(SPREAD_PCT) / 100.0, float(HALF_LIFE)
FISH = json.loads((DATA / "fish_market.json").read_text())["species"]
GROUNDS = json.loads((DATA / "fishing_grounds.json").read_text())["grounds"]
RECRUITS = json.loads((DATA / "recruits_port.json").read_text())
ORDER = RECRUITS["order"]
REC = RECRUITS["recruits"]

LCG_A, LCG_C, LCG_M = 1103515245, 12345, 2147483648


# ---- the deterministic random stream (shared with fishing.gd) -------------------------------------------------------------------
def lcg(state: int) -> tuple[int, float]:
    s = (LCG_A * state + LCG_C) % LCG_M
    return s, s / LCG_M


def round_half_up(v: float) -> int:
    return int(math.floor(v + 0.5))


def time_mult(hour: float) -> float:
    if 5.0 <= hour < 7.0 or 17.0 <= hour < 19.0:
        return P["fish.mult_dawn"]
    if hour >= 20.0 or hour < 5.0:
        return P["fish.mult_night"]
    return P["fish.mult_day"]


def haul(state: int, ground: dict, mult: float, bonus: float) -> tuple[int, str, float]:
    """One haul: species by weight, kg = haul_kg x richness x mult x (1 + bonus) x (1 +/- spread); kg rounded to 0.01."""
    state, r1 = lcg(state)
    state, r2 = lcg(state)
    acc, species = 0.0, ground["species"][-1][0]
    total = sum(w for _s, w in ground["species"])
    for sp, w in ground["species"]:
        acc += w / total
        if r1 < acc:
            species = sp
            break
    kg = P["fish.haul_kg"] * ground["richness"] * mult * (1.0 + bonus) * (1.0 + P["fish.haul_spread"] * (2.0 * r2 - 1.0))
    kg = math.floor(kg * 100.0 + 0.5) / 100.0
    return state, species, kg


class Port:
    """Purse, hold, market memory and crew (mirror of port_state.gd)."""

    def __init__(self) -> None:
        self.reales = int(P["port.start_reales"])
        self.lots: list[list] = []        # [species, kg, caught_day]
        self.crew: list[str] = []
        self.x: dict[str, float] = {}
        self.t_mkt = 0.0
        self.sold_total = 0
        self.kg_total = 0.0

    def eff(self, typ: str) -> float:
        vals = [REC[c]["effect"]["value"] for c in self.crew if REC[c]["effect"]["type"] == typ]
        if typ == "spoil_mult":
            out = 1.0
            for v in vals:
                out *= v
            return out
        return sum(vals)

    def capacity(self) -> float:
        return P["port.hold_kg"] + self.eff("hold_kg")

    def hold_kg(self) -> float:
        return sum(lot[1] for lot in self.lots)

    def add_catch(self, species: str, kg: float, day: float) -> float:
        room = max(self.capacity() - self.hold_kg(), 0.0)
        put = min(kg, room)
        put = math.floor(put * 100.0 + 0.5) / 100.0
        if put > 0.0:
            self.lots.append([species, put, day])
            self.kg_total += put
        return put

    def freshness(self, caught: float, now: float) -> float:
        return max(P["fish.spoil_floor"], 1.0 - P["fish.spoil_per_day"] * self.eff("spoil_mult") * max(now - caught, 0.0))

    def avg_freshness(self, now: float) -> float:
        kg = self.hold_kg()
        if kg <= 0:
            return 1.0
        return sum(lot[1] * self.freshness(lot[2], now) for lot in self.lots) / kg

    def _decay(self, now: float) -> None:
        dt = max(now - self.t_mkt, 0.0)
        if dt > 0:
            for k in list(self.x):
                self.x[k] = MK.decay(self.x[k], dt, HALF)
        self.t_mkt = max(now, self.t_mkt)

    def quote(self, species: str, now: float) -> float:
        """Reales per kg of fresh fish for a small sale right now (the spread and the market's memory included)."""
        self._decay(now)
        f = FISH[species]
        return f["base_reales_per_kg"] * f["factor"] * (1.0 - SPREAD / 2.0) * math.exp(self.x.get(species, 0.0))

    def sell_species(self, species: str, now: float) -> dict:
        self._decay(now)
        kg, v = 0.0, 0.0
        keep = []
        for lot in self.lots:
            if lot[0] == species:
                kg += lot[1]
                v += lot[1] * FISH[species]["base_reales_per_kg"] * self.freshness(lot[2], now)
            else:
                keep.append(lot)
        if kg <= 0:
            return {"kg": 0.0, "reales": 0, "value_base": 0.0}
        rev, nx = MK.sell(v, self.x.get(species, 0.0), FISH[species]["factor"], SPREAD, P[DEPTH_KEY])
        pay = round_half_up(rev)
        self.x[species] = nx
        self.lots = keep
        self.reales += pay
        self.sold_total += pay
        return {"kg": kg, "reales": pay, "value_base": v}

    def sell_all(self, now: float) -> dict:
        total, kg, per = 0, 0.0, {}
        for sp in sorted({lot[0] for lot in self.lots}):
            r = self.sell_species(sp, now)
            total += r["reales"]
            kg += r["kg"]
            per[sp] = r["reales"]
        return {"kg": kg, "reales": total, "per": per}

    def hire(self, cid: str) -> str:
        if cid in self.crew:
            return "already"
        if self.reales < REC[cid]["cost"]:
            return "poor"
        self.reales -= REC[cid]["cost"]
        self.crew.append(cid)
        return "ok"


# ---- fixture ----------------------------------------------------------------------------------------------------------------------
def make_fixture() -> dict:
    fx: dict = {"lcg": [], "haul": [], "session": []}
    for seed in (1, 12345, 2147483647, 987654321):
        s, out = seed, []
        for _ in range(4):
            s, v = lcg(s)
            out.append(round(v, 9))
        fx["lcg"].append({"seed": seed, "values": out})
    for seed, g, hour, bonus in ((7, "gnd_pilchard_shallows", 12.0, 0.0), (7, "gnd_kelp_reef", 6.0, 0.25), (99, "gnd_blue_drop", 22.0, 0.35),
                                 (31337, "gnd_gannet_bank", 18.0, 0.10)):
        s, seq = seed, []
        for _ in range(5):
            s, sp, kg = haul(s, GROUNDS[g], time_mult(hour), bonus)
            seq.append({"species": sp, "kg": kg})
        fx["haul"].append({"seed": seed, "ground": g, "hour": hour, "bonus": bonus, "hauls": seq, "state_after": s})
    # scripted sessions: ops on a Port; the expected values are recorded after every op
    scripts = [
        [{"op": "catch", "sp": "spc_sardine", "kg": 20.0, "day": 0.0}, {"op": "catch", "sp": "spc_mackerel", "kg": 10.0, "day": 0.1},
         {"op": "sell_all", "day": 0.3}, {"op": "hire", "id": "crew_pip_larkin"}, {"op": "catch", "sp": "spc_sardine", "kg": 30.0, "day": 0.4},
         {"op": "sell", "sp": "spc_sardine", "day": 0.4}, {"op": "sell", "sp": "spc_sardine", "day": 6.4}],
        [{"op": "hire", "id": "crew_garrick_stave"}, {"op": "catch", "sp": "spc_red_snapper", "kg": 45.0, "day": 1.0},
         {"op": "catch", "sp": "spc_red_snapper", "kg": 30.0, "day": 1.0}, {"op": "sell_all", "day": 4.0},
         {"op": "hire", "id": "crew_garrick_stave"}, {"op": "hire", "id": "crew_silas_reed"}],
        [{"op": "catch", "sp": "spc_yellowfin_tuna", "kg": 12.0, "day": 0.0}, {"op": "sell_all", "day": 0.0},
         {"op": "hire", "id": "crew_tuck_marrow"}, {"op": "hire", "id": "crew_silas_reed"}, {"op": "catch", "sp": "spc_parrotfish", "kg": 8.0, "day": 0.0},
         {"op": "sell_all", "day": 5.0}],
    ]
    for ops in scripts:
        p = Port()
        steps = []
        for op in ops:
            res: dict = {}
            if op["op"] == "catch":
                res["stored"] = p.add_catch(op["sp"], op["kg"], op["day"])
            elif op["op"] == "sell_all":
                r = p.sell_all(op["day"])
                res = {"reales": r["reales"], "kg": r["kg"]}
            elif op["op"] == "sell":
                r = p.sell_species(op["sp"], op["day"])
                res = {"reales": r["reales"], "kg": r["kg"]}
            elif op["op"] == "hire":
                res["result"] = p.hire(op["id"])
            steps.append({**op, "expect": {**res, "purse": p.reales, "hold_kg": round(p.hold_kg(), 4),
                                           "x": {k: round(v, 9) for k, v in sorted(p.x.items())}, "capacity": p.capacity()}})
        fx["session"].append({"start_purse": int(P["port.start_reales"]), "steps": steps})
    fx["freshness"] = [{"age_days": a, "spoil_mult": m, "value": max(P["fish.spoil_floor"], 1.0 - P["fish.spoil_per_day"] * m * a)}
                       for a in (0.0, 0.5, 1.0, 3.0) for m in (1.0, 0.7)]
    fx["time_mult"] = [{"hour": h, "mult": time_mult(h)} for h in (0.0, 4.9, 5.0, 6.9, 7.0, 12.0, 17.0, 18.9, 19.0, 19.9, 20.0, 23.0)]
    return fx


# ---- balance simulation -------------------------------------------------------------------------------------------------------------
PATH_KN = 4.0                    # average speed over a voyage with the wind as it is
SCENE_MS_PER_KN = 24.7 / 5.0     # H2D-1.2: 5 kn = 24.7 scene m/s
TRIP_OVERHEAD_S = 100.0          # dock 12 + walk to the market 20 + sell 10 + walk back 20 + board 8 + cast off 13 + turn 15 + slack
BERTH = (21.4, 21.0)


def ground_dist(g: dict) -> float:
    return math.hypot(g["x"] - BERTH[0], g["z"] - BERTH[1])


def fish_trip(p: Port, gid: str, fish_s: float, day: float, seed: int, hour: float = 12.0) -> tuple[float, int, float]:
    """Sail out, fish `fish_s` seconds (stop early when full), sail back, sell. Returns (real seconds used, new seed, reales gained)."""
    g = GROUNDS[gid]
    sail_s = (ground_dist(g) - g["r"] * 0.6) / (PATH_KN * SCENE_MS_PER_KN)
    t = sail_s + 0.0
    n = int(fish_s // P["fish.haul_interval_s"])
    bonus = p.eff("catch_bonus")
    day0 = day + t / 900.0
    state = seed
    for k in range(n):
        state, sp, kg = haul(state, g, time_mult(hour), bonus)
        stored = p.add_catch(sp, kg, day0 + (k + 1) * P["fish.haul_interval_s"] / 900.0)
        t += P["fish.haul_interval_s"]
        if stored < kg - 1e-9:
            break
    t += sail_s + TRIP_OVERHEAD_S
    before = p.reales
    p.sell_all(day + t / 900.0)
    return t, state, p.reales - before


def simulate(policy: str, horizon_min: float = 90.0, fish_s: float = 150.0) -> dict:
    """policy: 'near' (always the Pilchard Shallows), 'best' (the ground with the best reales per real second for the crew now),
    'cautious' (nearest ground, 100 s nets). Hires the cheapest affordable recruit whenever the purse allows (that is the optimum:
    cheap hands first). Returns the times (real minutes) of each hire and the totals."""
    p = Port()
    clock, day, seed = 0.0, 0.0, 1
    hires: dict[str, float] = {}
    trips = []
    while clock < horizon_min * 60 and len(p.crew) < len(ORDER):
        # hire what we can afford (at the harbour, between trips); walking to the recruit is part of the overhead
        for cid in sorted((c for c in ORDER if c not in p.crew), key=lambda c: REC[c]["cost"]):
            if p.reales >= REC[cid]["cost"]:
                p.hire(cid)
                hires[cid] = clock / 60.0
                clock += 25.0
        open_g = [k for k, g in GROUNDS.items() if g["min_crew"] <= len(p.crew)]
        if policy == "best":
            def rate(k: str) -> float:
                q = Port()
                q.crew = list(p.crew)
                q.x = dict(p.x)
                q.t_mkt = p.t_mkt
                t_, _s, gain = fish_trip(q, k, fish_s, day, seed)
                return gain / t_
            gid = max(open_g, key=rate)
        else:
            gid = "gnd_pilchard_shallows"
        fs = 100.0 if policy == "cautious" else fish_s
        t, seed, gain = fish_trip(p, gid, fs, day, seed)
        clock += t
        day += t / 900.0
        trips.append((round(clock / 60.0, 1), gid, gain))
        if clock > horizon_min * 60:
            break
    return {"hires": hires, "trips": trips, "purse": p.reales, "sold_total": p.sold_total, "crew": list(p.crew)}


def ground_rates() -> list[dict]:
    """Expected reales per real minute of one trip to each ground with a fresh market and no crew (the deterministic mean haul)."""
    rows = []
    for gid, g in GROUNDS.items():
        tot = sum(w for _s, w in g["species"])
        avg_price = sum(w / tot * FISH[s]["base_reales_per_kg"] for s, w in g["species"])
        kg_haul = P["fish.haul_kg"] * g["richness"]
        sail = (ground_dist(g) - g["r"] * 0.6) / (PATH_KN * SCENE_MS_PER_KN)
        rows.append({"ground": gid, "name": g["name"], "dist_m": round(ground_dist(g)), "sail_s": round(sail), "avg_price": round(avg_price, 2),
                     "kg_haul": round(kg_haul, 2), "reales_haul": round(kg_haul * avg_price, 2),
                     "reales_per_min_nets": round(kg_haul * avg_price * 60.0 / P["fish.haul_interval_s"], 1)})
    return rows


def balance_errors() -> list[str]:
    errs = []
    near = simulate("near")
    best = simulate("best")
    cautious = simulate("cautious", horizon_min=120.0)
    first = {k: min(v["hires"].values()) if v["hires"] else 999.0 for k, v in (("near", near), ("best", best), ("cautious", cautious))}
    last = {k: max(v["hires"].values()) if len(v["hires"]) == len(ORDER) else 999.0 for k, v in (("near", near), ("best", best), ("cautious", cautious))}
    for k in first:
        if not 3.0 <= first[k] <= 9.0:
            errs.append(f"policy {k}: the first hire comes at {first[k]:.1f} min (target 3 to 9)")
    if not 12.0 <= last["best"] <= 40.0:
        errs.append(f"policy best: the whole crew is hired at {last['best']:.1f} min (target 12 to 40)")
    if last["near"] > 75.0:
        errs.append(f"policy near: the whole crew takes {last['near']:.1f} min (target at most 75: staying at the first ground must not trap the player)")
    if last["cautious"] > 90.0:
        errs.append(f"policy cautious: {last['cautious']:.1f} min (target at most 90)")
    rows = ground_rates()
    top, low = max(r["reales_per_min_nets"] for r in rows), min(r["reales_per_min_nets"] for r in rows)
    if top / low > 3.5:
        errs.append(f"the best ground pays {top / low:.1f}x the worst (target at most 3.5x)")
    for cid in ORDER:
        c = REC[cid]["cost"]
        if c > 0 and c % 1 != 0:
            errs.append(f"{cid}: the cost must be a whole number of reales")
    if min(REC[c]["cost"] for c in ORDER) <= P["port.start_reales"]:
        errs.append("the cheapest recruit is affordable from the start: the loop would have nothing to teach")
    for sp in {s for g in GROUNDS.values() for s, _w in g["species"]}:
        if sp not in FISH:
            errs.append(f"species {sp} has no price")
    return errs


def report() -> list[str]:
    out = ["CP-1 starting economy (reales). Every number here is read from game/data/tuning/tuning_port.json and game/data/port/*.json", ""]
    out.append(f"purse at the start: {int(P['port.start_reales'])}; hold {int(P['port.hold_kg'])} kg; haul every {P['fish.haul_interval_s']:.0f} s of {P['fish.haul_kg']} kg x richness; market spread {SPREAD * 100:.0f}%, "
               f"depth {P[DEPTH_KEY]:.0f} reales per species, memory half-life {HALF:.0f} game days ({HALF * 15:.0f} real minutes)")
    out.append("")
    out.append("fish: " + "; ".join(f"{v['name']} {v['base_reales_per_kg']:.1f}/kg" for v in FISH.values()))
    out.append("")
    out.append(f"{'ground':<22}{'dist':>7}{'sail':>7}{'avg/kg':>8}{'kg/haul':>9}{'r/haul':>8}{'r/min nets':>12}")
    for r in ground_rates():
        out.append(f"{r['name']:<22}{r['dist_m']:>6}m{r['sail_s']:>6}s{r['avg_price']:>8}{r['kg_haul']:>9}{r['reales_haul']:>8}{r['reales_per_min_nets']:>12}")
    out.append("")
    out.append("recruits (cost, effect): " + "; ".join(f"{REC[c]['name']} {REC[c]['cost']} ({REC[c]['effect']['type']} {REC[c]['effect']['value']})" for c in ORDER))
    out.append(f"whole crew costs {sum(REC[c]['cost'] for c in ORDER)} reales")
    out.append("")
    for pol in ("cautious", "near", "best"):
        s = simulate(pol, 120.0 if pol == "cautious" else 90.0)
        hires = ", ".join(f"{REC[c]['name'].split()[0]} at {t:.1f} min" for c, t in sorted(s["hires"].items(), key=lambda kv: kv[1]))
        out.append(f"policy {pol:<9}: {hires or 'nobody'}; {len(s['trips'])} trips, sold {s['sold_total']} reales")
    errs = balance_errors()
    out.append("")
    out.append("balance: " + ("OK" if not errs else "; ".join(errs)))
    return out


# ---- tuning JSON -------------------------------------------------------------------------------------------------------------------
def tuning_doc() -> dict:
    recs = [{"key": k, "value": v, "unit": u, "min": lo, "max": hi, "provisional": True, "owner": o, "source": SRC, "note": n}
            for k, v, u, lo, hi, o, n in TABLE]
    return {"schema": 1, "kind": "tuning", "records": recs}


def check() -> int:
    errs = []
    if not TUNING.exists() or json.loads(TUNING.read_text()) != tuning_doc():
        errs.append(f"{TUNING.relative_to(ROOT)} is out of date: run economy_logic.py --write")
    if not FIXTURE.exists() or json.loads(FIXTURE.read_text()) != json.loads(json.dumps(make_fixture())):
        errs.append(f"{FIXTURE.relative_to(ROOT)} is out of date: run economy_logic.py --write")
    for gd, name in ((GD_STATE, "port_state.gd"), (GD_FISH, "fishing.gd")):
        if not gd.exists():
            errs.append(f"{name} is missing")
            continue
        src = gd.read_text()
        m = re.search(r"const DEFAULTS := \{(.*?)\n\}", src, re.S)
        got = {k: float(v) for k, v in re.findall(r'"([\w.]+)":\s*(-?[0-9.]+)', m.group(1))} if m else {}
        want = {k: float(v) for k, v in P.items() if k.startswith("fish.") == (gd is GD_FISH) and k.startswith(("fish.", "port.", "market."))}
        if gd is GD_STATE:
            want = {k: float(v) for k, v in P.items() if k.startswith(("port.", "market.", "fish.spoil"))}
        else:
            want = {k: float(v) for k, v in P.items() if k in ("fish.max_speed_kn", "fish.max_sea")}   # CP-2B.1: the only fishing.gd defaults
        if got != want:
            errs.append(f"DEFAULTS in {name} differ from the table in economy_logic.py: {sorted(set(got.items()) ^ set(want.items()))[:4]}")
        if "LCG" in src or gd is GD_FISH:
            for const in (str(LCG_A), str(LCG_C), str(LCG_M)):
                if gd is GD_FISH and const not in src:
                    errs.append(f"fishing.gd lacks the LCG constant {const}")
    errs += balance_errors()
    for e in errs:
        print("FAIL", e)
    print("PASS economy twin, tuning JSON, fixture, GDScript defaults and balance targets are in sync" if not errs else f"{len(errs)} ERROR(S)")
    return 1 if errs else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        TUNING.write_text(json.dumps(tuning_doc(), indent=1) + "\n")
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(make_fixture(), indent=1) + "\n")
        print("wrote", TUNING.relative_to(ROOT), "and", FIXTURE.relative_to(ROOT))
        return 0
    if a.check:
        return check()
    print("\n".join(report()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
