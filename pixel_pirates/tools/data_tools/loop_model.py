"""Core-loop arithmetic (Module B2, revised by patch T1: one 15-minute day everywhere).
Takes the tuning numbers and answers: does the loop still deliver the B1 pillar targets, and are the time-dependent systems consistent?

  python tools/data_tools/loop_model.py          # prints the cycle table, the resulting play-time split and the design flags
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import design_checks as D  # noqa: E402
import voyage_clock as VC  # noqa: E402

DECIDED_MINUTES_PER_DAY = 15.0  # decision T1; changing it needs a new decision, not just a new number
FORBIDDEN_TIME_KEYS = ("time.accel_fast_factor", "time.ashore_game_minutes_per_real_minute")

# archetype -> (lower band key, upper band key, destination tier, mix key)
ARCH = {"hop": (None, "voyage.hop_max_minutes", 3, "loop.mix_hop_pct"),
        "passage": ("voyage.hop_max_minutes", "voyage.passage_max_minutes", 2, "loop.mix_passage_pct"),
        "crossing": ("voyage.passage_max_minutes", "voyage.crossing_max_minutes", 1, "loop.mix_crossing_pct"),
        "dead": ("voyage.crossing_max_minutes", "voyage.dead_max_minutes", 1, "loop.mix_dead_pct")}
STARTS = ["time.dawn_start_hour", "time.morning_start_hour", "time.day_start_hour", "time.sunset_start_hour", "time.evening_start_hour",
          "time.night_start_hour"]
ACTIVITIES = ["activity.fish_cast_hours", "activity.cook_meal_hours", "activity.patch_leak_hours", "activity.replace_plank_hours",
              "activity.careen_hours", "crew.sleep_need_hours"]
NEED = ["time.real_minutes_per_game_day", "time.report_hour", "light.night_floor", "light.dawn_end_level", "light.sunset_end_level",
        "loop.report_max_seconds", "loop.max_quiet_minutes", "loop.choice_moments_per_10min", "loop.crisis_moments_per_10min_max",
        "loop.island_engagement", "loop.plan_minutes", "loop.provision_minutes", "loop.ship_fraction_of_voyage",
        "loop.combat_fraction_of_voyage", "loop.visit_cost_days_max", "crew.watch_length_hours", "island.explore_budget_min_t1",
        "island.explore_budget_min_t2", "island.explore_budget_min_t3", "ship.stores_hold_days_start", "ship.stores_hold_days_mid",
        "ship.stores_hold_days_late", "water.foul_after_days_warm", "health.scurvy_onset_days_no_vitc", "ship.hull_wear_pct_per_day_at_sea",
        "weather.season_length_days", "plan.forecast_spread_sea", "plan.forecast_spread_dead", "voyage.hop_min_minutes",
        "voyage.hop_max_minutes", "voyage.passage_max_minutes", "voyage.crossing_max_minutes", "voyage.dead_max_minutes"
        ] + STARTS + ACTIVITIES + [v[3] for v in ARCH.values()]


def load_ranges(data_dir: Path = D.DATA) -> dict[str, tuple[float, float]]:
    out = {}
    for p in sorted((data_dir / "tuning").glob("*.json")):
        for r in json.loads(p.read_text())["records"]:
            out[r["key"]] = (r["min"], r["max"])
    return out


def starts_of(t: dict) -> list[float]:
    return [t[k] for k in STARTS]


def cycle(t: dict, name: str) -> dict:
    """One average cycle of this archetype, in real minutes, split by the four pillar activities."""
    lo_k, hi_k, tier, _ = ARCH[name]
    lo = t["voyage.hop_min_minutes"] if lo_k is None else t[lo_k]
    hi = t[hi_k]
    rate = t["time.real_minutes_per_game_day"]
    voyage = (lo + hi) / 2.0
    ship_v, combat_v = voyage * t["loop.ship_fraction_of_voyage"], voyage * t["loop.combat_fraction_of_voyage"]
    island = t[f"island.explore_budget_min_t{tier}"] * t["loop.island_engagement"]
    c = {"name": name, "tier": tier, "voyage": voyage, "days": voyage / rate, "island_days": island / rate,
         "sea": voyage - ship_v - combat_v, "island": island, "ship": ship_v + t["loop.plan_minutes"] + t["loop.provision_minutes"], "combat": combat_v}
    c["total"] = c["sea"] + c["island"] + c["ship"] + c["combat"]
    c["total_days"] = c["total"] / rate
    return c


def shares(t: dict) -> dict:
    """Mix-weighted play-time split of the whole campaign, in percent."""
    tot = {"sea": 0.0, "island": 0.0, "ship": 0.0, "combat": 0.0, "total": 0.0, "voyage": 0.0, "days": 0.0}
    for name, (_, _, _, mk) in ARCH.items():
        w, c = t[mk] / 100.0, cycle(t, name)
        for k in tot:
            tot[k] += w * c[k]
    out = {k: 100.0 * tot[k] / tot["total"] for k in ("sea", "island", "ship", "combat")}
    out.update({"cycle_minutes": tot["total"], "voyage_minutes": tot["voyage"], "days_per_cycle": tot["total"] / t["time.real_minutes_per_game_day"]})
    return out


def worst_days(t: dict, band_key: str, spread_key: str) -> float:
    """Game days of the longest voyage of a band at the HIGH end of the forecast band."""
    return t[band_key] / t["time.real_minutes_per_game_day"] * (1.0 + t[spread_key])


def clock_invariants(t: dict) -> list[str]:
    p: list[str] = []
    rate = t["time.real_minutes_per_game_day"]
    if rate != DECIDED_MINUTES_PER_DAY:
        p.append(f"time: one game day must be exactly {DECIDED_MINUTES_PER_DAY:.0f} real minutes (decision T1); got {rate}")
    for k in t:
        if k in FORBIDDEN_TIME_KEYS or k.startswith("time.ashore") or "accel" in k:
            p.append(f"time: key '{k}' belongs to the removed two-clock / acceleration model (patch T1)")
    s = starts_of(t)
    if not all(0 <= a < b <= 24 for a, b in zip(s, s[1:])) or not 0 <= s[0] or s[5] > 24:
        p.append(f"time: day-band start hours must strictly increase inside 0-24 (got {s})")
        return p
    for i, name in enumerate(VC.BAND_NAMES):
        length = (s[i + 1] - s[i]) if i < 5 else (24.0 - s[5] + s[0])
        secs = VC.hours_to_real_seconds(length, rate)
        if secs < 30.0:
            p.append(f"time: the {name} band lasts only {secs:.0f} real seconds; each band must last at least 30 s to be seen")
    if not s[1] <= t["time.report_hour"] < s[2]:
        p.append("time: the Morning Report hour must fall inside the Morning band")
    if not 0 <= t["light.night_floor"] < t["light.sunset_end_level"] < t["light.dawn_end_level"] < 1.0:
        p.append("time: light levels must satisfy night floor < sunset end < dawn end < 1")
    if 24.0 % t["crew.watch_length_hours"] != 0:
        p.append("time: the watch length must divide 24 hours")
    if VC.band_of_hour(t["time.report_hour"], s) != "morning":
        p.append("time: the Morning Report must be labelled a Morning-band event")
    return p


def loop_invariants(t: dict, ranges: dict) -> list[str]:
    miss = [k for k in NEED if k not in t]
    if miss:
        return [f"loop: missing tuning keys {miss}"]
    p = clock_invariants(t)
    rate = t["time.real_minutes_per_game_day"]
    mix = sum(t[v[3]] for v in ARCH.values())
    if abs(mix - 100) > 0.01:
        p.append(f"loop: voyage mix must add to 100 percent (got {mix})")
    s = shares(t)
    for key, tk in (("sea", "share.sea_pct"), ("island", "share.island_pct"), ("ship", "share.ship_crew_pct")):
        lo, hi = ranges[tk]
        if not lo <= s[key] <= hi:
            p.append(f"loop: modelled {key} share {s[key]:.1f} percent is outside the pillar range {lo}-{hi} ({tk})")
    if s["combat"] > t["share.combat_pct_max"]:
        p.append(f"loop: modelled combat share {s['combat']:.1f} percent exceeds the cap {t['share.combat_pct_max']}")
    if s["sea"] < s["island"]:
        p.append("loop: the modelled sea share is below the island share (pillar P1)")
    if t["loop.crisis_moments_per_10min_max"] > t["loop.choice_moments_per_10min"]:
        p.append("loop: more crises than choices per 10 minutes would turn the sea into a panic")
    if t["loop.report_max_seconds"] > 30:
        p.append("loop: the Morning Report must be readable in 30 seconds or less")
    if t["loop.report_max_seconds"] / (rate * 60.0) > 0.03:
        p.append("loop: the daily Morning Report may not take more than 3 percent of a game day")
    band = VC.band_of(3 * rate, t["voyage.hop_min_minutes"], t["voyage.hop_max_minutes"], t["voyage.passage_max_minutes"],
                      t["voyage.crossing_max_minutes"], t["voyage.dead_max_minutes"])
    if band != "crossing":
        p.append(f"loop: the 3-day worked example from B1 must be a Crossing at this time scale (it is '{band}')")
    # island visits: one clock, so a full visit costs real game time and the cost must be bounded and visible
    full_t1 = t["island.explore_budget_min_t1"] / rate
    if full_t1 > t["loop.visit_cost_days_max"]:
        p.append(f"loop: a full Tier 1 visit costs {full_t1:.1f} game days; the cap is {t['loop.visit_cost_days_max']}")
    if full_t1 < 1.0:
        p.append("loop: a full Tier 1 visit must cost at least one game day or islands are free")
    # stores hold vs voyage length: crossings are survivable on the starting ship, Dead Ocean needs preparation or a better ship
    cross_worst = worst_days(t, "voyage.crossing_max_minutes", "plan.forecast_spread_sea")
    dead_worst = worst_days(t, "voyage.dead_max_minutes", "plan.forecast_spread_dead")
    start, mid, late = t["ship.stores_hold_days_start"], t["ship.stores_hold_days_mid"], t["ship.stores_hold_days_late"]
    if not start < mid < late:
        p.append("ship: stores holds must increase start < mid < late")
    if cross_worst > start:
        p.append(f"ship: the starting stores hold ({start} d) cannot cover a worst-case Crossing ({cross_worst:.1f} d)")
    if dead_worst <= start:
        p.append(f"ship: a worst-case Dead Ocean ({dead_worst:.1f} d) must exceed the starting stores hold ({start} d), or it needs no preparation")
    if dead_worst > mid:
        p.append(f"ship: the mid-game stores hold ({mid} d) must cover a worst-case Dead Ocean ({dead_worst:.1f} d)")
    foul = t["water.foul_after_days_warm"]
    if not cross_worst < foul <= dead_worst:
        p.append(f"water: foul-after ({foul} d) must lie between a worst-case Crossing ({cross_worst:.1f} d) and a worst-case Dead Ocean ({dead_worst:.1f} d)")
    scurvy_min = t["health.scurvy_onset_days_no_vitc"] * rate
    if scurvy_min <= t["voyage.dead_max_minutes"]:
        p.append("health: scurvy must take longer than the longest single voyage, so a prepared crew is never sick on one crossing")
    if scurvy_min > 6 * s["cycle_minutes"]:
        p.append("health: scurvy would take more than 6 average cycles, so it would never matter")
    if t["ship.hull_wear_pct_per_day_at_sea"] * dead_worst > 10.0:
        p.append("ship: a worst-case Dead Ocean voyage may not wear more than 10 percent of the hull")
    for k in ACTIVITIES:
        secs = VC.hours_to_real_seconds(t[k], rate)
        if not 20.0 <= secs <= 900.0:
            p.append(f"activity: {k} lasts {secs:.0f} real seconds; activities must take between 20 s and 15 min")
    if t["weather.season_length_days"] * rate < 4 * s["cycle_minutes"]:
        p.append("weather: a season must last at least 4 average cycles to be felt as a phase")
    return p


def flags(t: dict) -> list[str]:
    """Design pressures that are intended, reported as information (not failures)."""
    rate = t["time.real_minutes_per_game_day"]
    cw, dw = worst_days(t, "voyage.crossing_max_minutes", "plan.forecast_spread_sea"), worst_days(t, "voyage.dead_max_minutes", "plan.forecast_spread_dead")
    out = [f"voyage lengths in game days: Hop {t['voyage.hop_min_minutes'] / rate:.2f}-{t['voyage.hop_max_minutes'] / rate:.2f}, "
           f"Passage to {t['voyage.passage_max_minutes'] / rate:.2f}, Crossing to {t['voyage.crossing_max_minutes'] / rate:.1f}, "
           f"Dead Ocean to {t['voyage.dead_max_minutes'] / rate:.1f} (worst case {dw:.1f})",
           f"longest Dead Ocean worst case = {dw:.1f} game days; 12 men need {12 * t['water.need_l_per_man_day_min'] * dw:.0f} L at the minimum water ration "
           f"and {12 * t['food.hardtack_kg_per_man_day'] * dw:.0f} kg of hardtack; the starting ship's hold covers {t['ship.stores_hold_days_start']:.0f} days",
           f"water goes foul after {t['water.foul_after_days_warm']:.0f} warm days = {t['water.foul_after_days_warm'] * rate:.0f} real min: past a worst-case Crossing "
           f"({cw:.1f} d), inside a worst-case Dead Ocean ({dw:.1f} d): rain catching, boiling or a spring is REQUIRED there (intended)",
           f"scurvy clock {t['health.scurvy_onset_days_no_vitc']:.0f} days = {t['health.scurvy_onset_days_no_vitc'] * rate:.0f} real min of play without fruit"]
    for tier in (1, 2, 3):
        b = t[f"island.explore_budget_min_t{tier}"]
        out.append(f"Tier {tier} visit: full {b / rate:.2f} game days ({b:.0f} min), typical {b * t['loop.island_engagement'] / rate:.2f} d")
    return out


def table(t: dict) -> str:
    L = ["| cycle | mix | to island tier | voyage min | voyage days | island min | island days | ship+crew min | combat min | cycle min | cycle days |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, (_, _, tier, mk) in ARCH.items():
        c = cycle(t, name)
        L.append(f"| {name} | {t[mk]:.0f}% | T{tier} | {c['voyage']:.1f} | {c['days']:.2f} | {c['island']:.1f} | {c['island_days']:.2f} | {c['ship']:.1f} | "
                 f"{c['combat']:.1f} | {c['total']:.1f} | {c['total_days']:.2f} |")
    s = shares(t)
    L.append(f"| **campaign average** | 100% | | {s['voyage_minutes']:.1f} | | | | | | **{s['cycle_minutes']:.1f}** | **{s['days_per_cycle']:.2f}** |")
    return "\n".join(L)


def main() -> int:
    t, rg = D.load_tuning(), load_ranges()
    print(table(t))
    s = shares(t)
    print(f"\nplay-time split: sea {s['sea']:.1f}%  islands {s['island']:.1f}%  ship+crew {s['ship']:.1f}%  combat {s['combat']:.1f}%")
    print(f"50 islands = {50 * s['cycle_minutes'] / 60:.0f} h of play and {50 * s['days_per_cycle']:.0f} game days; 30 islands = {30 * s['cycle_minutes'] / 60:.0f} h")
    print("problems:", loop_invariants(t, rg) or "none")
    for f in flags(t):
        print("flag:", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
