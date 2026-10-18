"""Tests for design_checks.py, loop_model.py and voyage_clock.py (B1, B2, patch T1). Run: python tools/data_tools/test_design_checks.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import design_checks as D  # noqa: E402
import loop_model as LM  # noqa: E402
import voyage_clock as VC  # noqa: E402

fails = 0
FX = D.ROOT / "game" / "tests" / "fixtures"


def expect(name: str, cond: bool, detail: str = "") -> None:
    global fails
    print(("ok   " if cond else "FAIL ") + name + ("" if cond else f"  {detail}"))
    fails += 0 if cond else 1


T = D.load_tuning()
RG = LM.load_ranges()
expect("real tuning satisfies every pillar invariant", D.invariants(T) == [], str(D.invariants(T)))


def broken(**kw):
    t = dict(T)
    t.update(kw)
    return D.invariants(t)


# ---- B1 pillar invariants -------------------------------------------------------------------------------------------------
expect("ladder order is enforced", any("ladder" in p for p in broken(**{"warn.warning_hours": 60})))
expect("ladder must stay above zero", any("ladder" in p for p in broken(**{"warn.critical_hours": 0})))
expect("critical rung leaves 2 real minutes to act", any("2 real minutes" in p for p in broken(**{"warn.critical_hours": 3})))
expect("3 warning steps minimum", any("3 warning" in p for p in broken(**{"warn.min_steps_before_loss": 2})))
expect("2 recovery options minimum", any("recovery" in p for p in broken(**{"recovery.min_options": 1})))
expect("dead ocean band wider than sea band", any("forecast band" in p for p in broken(**{"plan.forecast_spread_dead": 0.2})))
expect("narrowest band is above zero and below the sea band", any("narrowest" in p for p in broken(**{"plan.forecast_spread_min": 0})) and
       any("narrowest" in p for p in broken(**{"plan.forecast_spread_min": 0.3})))
expect("voyage bands must increase", any("strictly" in p for p in broken(**{"voyage.passage_max_minutes": 8})))
expect("dead ocean about 2x longest crossing", any("twice" in p for p in broken(**{"voyage.dead_max_minutes": 80})))
expect("shares must add to 100", any("add to 100" in p for p in broken(**{"share.sea_pct": 45})))
expect("sea share not below island share", any("at least as much" in p for p in broken(**{"share.sea_pct": 30, "share.island_pct": 45})))
expect("combat capped at 12 percent", any("combat" in p for p in broken(**{"share.combat_pct_max": 20, "share.sea_pct": 28})))
expect("missing keys are reported", any("missing" in p for p in D.invariants({"warn.advisory_hours": 48})))

hit = D.content_findings({"x.json": {"records": [{"name": "Temple of the Gods", "note": "x"}]}})
expect("lint: religion word", any("rule 3" in h for h in hit))
expect("lint: sexual word", any("rule 2" in h for h in D.content_findings({"x.json": {"name": "The Naked Cove"}})))
expect("lint: female word in a name", any("rule 1" in h for h in D.content_findings({"x.json": {"name": "The Queen's Rest"}})))
expect("lint: word boundary (no false hit on 'shelf' or 'goddard')", D.content_findings({"x.json": {"name": "Shelf of Goddard"}}) == [])
expect("lint: free-text note may mention the rule", D.content_findings({"x.json": {"note": "no female crew"}}) == [])
expect("lint: id and gender fields skipped", D.content_findings({"x.json": {"id": "crew_she", "gender": "male"}}) == [])
expect("real data has no banned words", D.scan_data() == [], str(D.scan_data()[:3]))

r = D.reckoning(T, 12, 3, 0.25, {"hardtack_kg": 21, "water_l": 100})
expect("reckoning band 2.25 / 3 / 3.75 days", r["band_days"] == (2.25, 3, 3.75), str(r["band_days"]))
expect("reckoning daily need 5.4 kg and 30 L", r["per_day"] == {"hardtack_kg": 5.4, "water_l": 30.0})
rows = {x["stock"]: x for x in r["rows"]}
expect("reckoning: hardtack fine, water short in the worst case", rows["hardtack_kg"]["margin_days_worst"] > 0 > rows["water_l"]["margin_days_worst"], str(rows))
expect("reckoning expected need fits both stocks", all(row["need_expected"] < row["have"] for row in r["rows"]))
expect("ladder rungs (game hours)", [D.rung(x, T) for x in (100, 48, 20, 16, 7, 6, 2)] ==
       ["ok", "advisory", "advisory", "warning", "warning", "critical", "critical"])

# ---- loop model + time-dependent systems (B2, T1) ---------------------------------------------------------------------------
expect("real tuning satisfies every loop and time invariant", LM.loop_invariants(T, RG) == [], str(LM.loop_invariants(T, RG)))


def loop_broken(**kw):
    t = dict(T)
    t.update(kw)
    return LM.loop_invariants(t, RG)


def has(word, **kw):
    return any(word in p for p in loop_broken(**kw))


expect("time: the day is locked at 15 minutes", has("exactly 15", **{"time.real_minutes_per_game_day": 12}))
expect("time: the removed acceleration key is rejected", has("two-clock", **{"time.accel_fast_factor": 4}))
expect("time: the removed ashore-clock key is rejected", has("two-clock", **{"time.ashore_game_minutes_per_real_minute": 24}))
expect("time: band starts must increase", has("strictly increase", **{"time.day_start_hour": 6}))
expect("time: every band must last 30 s", has("at least 30 s", **{"time.evening_start_hour": 19.9, "time.night_start_hour": 20.0}))
expect("time: report hour inside the Morning band", has("inside the Morning band", **{"time.report_hour": 12}))
expect("time: light levels ordered", has("light levels", **{"light.sunset_end_level": 0.6}))
expect("time: watch must divide 24", has("divide 24", **{"crew.watch_length_hours": 5}))
expect("loop: mix must add to 100", has("add to 100", **{"loop.mix_hop_pct": 40}))
expect("loop: too little sea is caught", has("sea share", **{"loop.ship_fraction_of_voyage": 0.4, "loop.combat_fraction_of_voyage": 0.2}))
expect("loop: too much island time is caught", has("island share", **{"loop.island_engagement": 1.0}))
expect("loop: too much ship work is caught", has("ship share", **{"loop.plan_minutes": 5, "loop.provision_minutes": 5}))
expect("loop: combat cap is caught", has("combat", **{"loop.combat_fraction_of_voyage": 0.2}))
expect("loop: crises cannot outnumber choices", has("crises", **{"loop.crisis_moments_per_10min_max": 3}))
expect("loop: report must be readable", has("30 seconds", **{"loop.report_max_seconds": 45}))
expect("loop: the report may not eat 3 percent of a day (28 s fails, 27 s passes)", has("3 percent", **{"loop.report_max_seconds": 28}) and
       not has("3 percent", **{"loop.report_max_seconds": 27}))
expect("loop: the 3-day example must be a Crossing", has("3-day", **{"voyage.crossing_max_minutes": 40, "voyage.dead_max_minutes": 80}))
expect("visits: the full Tier 1 visit cap", has("cap is", **{"island.explore_budget_min_t1": 60}))
expect("visits: islands may not be free", has("islands are free", **{"island.explore_budget_min_t1": 10}))
expect("stores: start hold must cover a worst-case Crossing", has("worst-case Crossing", **{"ship.stores_hold_days_start": 4}))
expect("stores: Dead Ocean must need preparation", has("needs no preparation", **{"ship.stores_hold_days_start": 12, "ship.stores_hold_days_mid": 14}))
expect("stores: mid hold must cover Dead Ocean", has("mid-game stores hold", **{"ship.stores_hold_days_mid": 10, "ship.stores_hold_days_late": 24}))
expect("stores: holds must increase", has("must increase", **{"ship.stores_hold_days_mid": 6}))
expect("water: foul-after not before a worst-case Crossing", has("foul-after", **{"water.foul_after_days_warm": 4}))
expect("water: foul-after not after a worst-case Dead Ocean", has("foul-after", **{"water.foul_after_days_warm": 20}))
expect("health: scurvy slower than one crossing", has("longest single voyage", **{"health.scurvy_onset_days_no_vitc": 7}))
expect("health: scurvy must matter within 6 cycles", has("never matter", **{"health.scurvy_onset_days_no_vitc": 40}))
expect("ship: Dead Ocean hull wear cap", has("10 percent of the hull", **{"ship.hull_wear_pct_per_day_at_sea": 2.0}))
expect("activity: too short is caught", has("activities must take", **{"activity.fish_cast_hours": 0.2}))
expect("activity: too long is caught", has("activities must take", **{"activity.careen_hours": 30}))
expect("weather: season must last 4 cycles", has("season", **{"weather.season_length_days": 8}))
expect("loop: missing keys are reported", any("missing" in p for p in LM.loop_invariants({"loop.plan_minutes": 2}, RG)))

sh = LM.shares(T)
expect("modelled split is about 41 / 34 / 20 / 5", abs(sh["sea"] - 41.3) < 0.2 and abs(sh["island"] - 34.4) < 0.2 and abs(sh["ship"] - 19.8) < 0.2 and
       abs(sh["combat"] - 4.6) < 0.2, str(sh))
expect("average cycle is 48 minutes = 3.2 game days", abs(sh["cycle_minutes"] - 48.2) < 0.1 and abs(sh["days_per_cycle"] - 3.21) < 0.02)
expect("water-foul pressure on Dead Ocean is flagged (intended)", any("REQUIRED" in f for f in LM.flags(T)))
expect("starting hold is reported next to the Dead Ocean need", any("starting ship's hold covers 8 days" in f for f in LM.flags(T)))

# ---- clock: fixture (hand-written expectations) --------------------------------------------------------------------------
cases = json.loads((FX / "clock_cases.json").read_text())["cases"]
bad = []
for c in cases:
    got, want = VC.FUNCS[c["fn"]](*c["args"]), c["expect"]
    if isinstance(want, dict):
        ok = all(abs(got[k] - want.get(k, 0.0)) < 1e-6 for k in got) and abs(sum(got.values()) - 1.0) < 1e-9
    elif isinstance(want, float):
        ok = abs(got - want) < 1e-6
    else:
        ok = got == want
    if not ok:
        bad.append((c["fn"], c["args"], got, want))
expect(f"clock fixture: {len(cases)} hand-written cases match", not bad, str(bad[:3]))
scs = json.loads((FX / "clock_scenarios.json").read_text())["scenarios"]
mism = [m for sc in scs for m in VC.run_scenario(sc)]
expect(f"clock scenarios: {len(scs)} hand-calculated scenarios match (pause, resume, sea/island)", not mism, str(mism[:3]))

# ---- day / night boundaries and smoothness ------------------------------------------------------------------------------------
S = LM.starts_of(T)
args = (S, T["light.night_floor"], T["light.dawn_end_level"], T["light.sunset_end_level"])
steps = [i / 100.0 for i in range(0, 2401)]
dl = [VC.daylight(h, *args) for h in steps]
expect("daylight is never abrupt (max step 0.01 h < 0.01)", max(abs(a - b) for a, b in zip(dl, dl[1:])) < 0.01, str(max(abs(a - b) for a, b in zip(dl, dl[1:]))))
expect("daylight wraps cleanly at midnight", abs(VC.daylight(0.0, *args) - VC.daylight(23.9999, *args)) < 0.001)
expect("daylight stays in [night floor, 1]", min(dl) >= T["light.night_floor"] - 1e-9 and max(dl) <= 1.0 + 1e-9)
expect("daylight is full at noon and at the floor at 03:00", VC.daylight(12.0, *args) == 1.0 and abs(VC.daylight(3.0, *args) - T["light.night_floor"]) < 1e-9)
expect("daylight rises through dawn and morning, falls through sunset and evening",
       all(VC.daylight(a + 0.01, *args) > VC.daylight(a, *args) for a in (5.2, 6.0, 8.0, 9.5)) and
       all(VC.daylight(a + 0.01, *args) < VC.daylight(a, *args) for a in (17.2, 18.0, 19.0, 19.7)))
w = [VC.band_weights(h, S) for h in steps]
expect("band weights always sum to 1", all(abs(sum(x.values()) - 1.0) < 1e-9 for x in w))
expect("band weights never jump (max step 0.01 h < 0.01)", max(abs(a[k] - b[k]) for a, b in zip(w, w[1:]) for k in a) < 0.01)
expect("band weights wrap cleanly at midnight", all(abs(VC.band_weights(0.0, S)[k] - VC.band_weights(23.9999, S)[k]) < 0.001 for k in VC.BAND_NAMES))
expect("every hour of the day has exactly one hard band label", {VC.band_of_hour(h / 4.0, S) for h in range(96)} == set(VC.BAND_NAMES))
lengths = {b: sum(1 for h in range(2400) if VC.band_of_hour(h / 100.0, S) == b) / 100.0 for b in VC.BAND_NAMES}
expect("band lengths in game hours: 2 / 3 / 7 / 2 / 1 / 9", [lengths[b] for b in VC.BAND_NAMES] == [2.0, 3.0, 7.0, 2.0, 1.0, 9.0], str(lengths))
expect("band lengths add to 24", abs(sum(lengths.values()) - 24.0) < 1e-9)

# ---- pause behaviour: nothing that depends on time may advance while paused ---------------------------------------------------
HUNGER_KG_PER_DAY = 5.4


class Consumer:
    """A stand-in for any time-dependent system: it may only use the game seconds that WorldClock.tick() returns."""

    def __init__(self):
        self.used = 0.0

    def step(self, game_dt: float) -> None:
        self.used += HUNGER_KG_PER_DAY * game_dt / 86400.0


clk, cons = VC.WorldClock(T["time.real_minutes_per_game_day"]), Consumer()
for _ in range(900):          # 900 real seconds at 1 s = one game day
    cons.step(clk.tick(1.0))
expect("one real quarter-hour consumes exactly one day of rations", abs(cons.used - 5.4) < 1e-9 and abs(clk.t - 86400) < 1e-6, f"{cons.used} {clk.t}")
used_before, t_before = cons.used, clk.t
clk.pause("report")
for _ in range(600):
    cons.step(clk.tick(1.0))
expect("ten paused real minutes consume nothing and move no clock", cons.used == used_before and clk.t == t_before)
clk.pause("planning")
clk.resume("report")
cons.step(clk.tick(30.0))
expect("a second pause reason keeps time stopped after the first is released", cons.used == used_before and clk.is_paused())
clk.resume("planning")
cons.step(clk.tick(30.0))
expect("resuming restarts consumption at the same rate", abs(cons.used - used_before - 5.4 * 30 / 900) < 1e-9)
expect("tick with a negative or zero delta does nothing", clk.tick(-3.0) == 0.0 and clk.tick(0.0) == 0.0)

# ---- continuity between sea and island ------------------------------------------------------------------------------------------
clk = VC.WorldClock(15.0)
trace = []
for i in range(300):
    clk.set_location("sea" if (i // 50) % 2 == 0 else "island")   # switch every 50 real seconds
    before = clk.t
    clk.tick(1.0)
    trace.append(clk.t - before)
expect("clock speed is identical at sea and ashore (every tick = 96 game s)", all(abs(d - 96.0) < 1e-9 for d in trace))
c1, c2 = VC.WorldClock(15.0), VC.WorldClock(15.0)
c2.set_location("island")
for _ in range(100):
    c1.tick(0.37)
    c2.tick(0.37)
expect("the same real time gives the same game time on either side", abs(c1.t - c2.t) < 1e-9)
c3 = VC.WorldClock(15.0, 5000.0)
c3.set_location("island")
expect("changing location does not move the clock", c3.t == 5000.0)
expect("1 game hour = 37.5 s, 4 h watch = 150 s, 1 day = 900 s", VC.hours_to_real_seconds(1, 15) == 37.5 and VC.hours_to_real_seconds(4, 15) == 150.0 and
       VC.hours_to_real_seconds(24, 15) == 900.0)

print("design checks tests:", "PASS" if not fails else f"{fails} FAILED")
sys.exit(1 if fails else 0)
