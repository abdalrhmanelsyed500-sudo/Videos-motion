"""World clock (Module B2, revised by patch T1): ONE clock for sea and shore, day/night bands, daylight curve, pause rules.
Pure functions plus the WorldClock class. The GDScript twin is game/core/voyage_clock.gd + game/core/world_clock.gd; both are
run against game/tests/fixtures/clock_cases.json and clock_scenarios.json.

Decision T1: 1 game day = 15 real minutes (tuning time.real_minutes_per_game_day), identical at sea and ashore, fixed rate,
no player acceleration. Time stops only while a pause reason is held (planning screens, the Morning Report, menus).
Ship's time: 24 h = 6 watches of crew.watch_length_hours (4). Bells strike every half hour; eight bells end a watch."""
from __future__ import annotations

import math

WATCH_NAMES = ["Middle", "Morning", "Forenoon", "Afternoon", "Dog", "First"]  # 00-04, 04-08, 08-12, 12-16, 16-20, 20-24
BAND_NAMES = ["dawn", "morning", "day", "sunset", "evening", "night"]
DEFAULT_STARTS = [5.0, 7.0, 10.0, 17.0, 19.0, 20.0]  # band start hours, tuning time.*_start_hour
DEFAULT_REPORT_HOUR = 8.0


def watch_index(hour: float, watch_len: float = 4.0) -> int:
    return int(math.floor((hour % 24.0) / watch_len))


def watch_name(index: int) -> str:
    return WATCH_NAMES[index % len(WATCH_NAMES)]


def last_bell(hour: float, watch_len: float = 4.0) -> int:
    """Bells struck at the most recent half-hour mark: 1..7 inside a watch, 8 at the watch change."""
    k = int(math.floor((hour % watch_len) / 0.5))
    return k if k > 0 else 8


def hours_to_real_seconds(hours: float, minutes_per_day: float) -> float:
    return hours * minutes_per_day * 60.0 / 24.0


def real_seconds_to_hours(seconds: float, minutes_per_day: float) -> float:
    return seconds * 24.0 / (minutes_per_day * 60.0)


def days_to_real_minutes(days: float, minutes_per_day: float) -> float:
    return days * minutes_per_day


def reports_between(abs_hour_from: float, abs_hour_to: float, report_hour: float = DEFAULT_REPORT_HOUR) -> int:
    """Morning Reports due while the clock runs from one absolute hour to another (boundary: from < report hour <= to)."""
    return int(math.floor((abs_hour_to - report_hour) / 24.0) - math.floor((abs_hour_from - report_hour) / 24.0))


def band_of(minutes: float, hop_min: float, hop_max: float, passage_max: float, crossing_max: float, dead_max: float) -> str:
    """Voyage length band (real minutes)."""
    if minutes < hop_min:
        return "below"
    for name, top in (("hop", hop_max), ("passage", passage_max), ("crossing", crossing_max), ("dead", dead_max)):
        if minutes <= top:
            return name
    return "beyond"


# --- day / night ---------------------------------------------------------------------------------------------------------


def band_of_hour(hour: float, starts: list[float] | None = None) -> str:
    """Hard label for HUD text and band-triggered events: dawn, morning, day, sunset, evening, night (night wraps midnight)."""
    s = starts or DEFAULT_STARTS
    h = hour % 24.0
    if h < s[0] or h >= s[5]:
        return "night"
    for i in range(5):
        if h < s[i + 1]:
            return BAND_NAMES[i]
    return "night"


def _smooth(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3.0 - 2.0 * x)


def daylight(hour: float, starts: list[float] | None, night_floor: float, dawn_end: float, sunset_end: float) -> float:
    """Continuous daylight level 0..1 (the lighting driver). Smoothstep between keyframes at the band boundaries; wraps at midnight."""
    s = starts or DEFAULT_STARTS
    h = hour % 24.0
    keys = [(0.0, night_floor), (s[0], night_floor), (s[1], dawn_end), (s[2], 1.0), (s[3], 1.0), (s[4], sunset_end), (s[5], night_floor),
            (24.0, night_floor)]
    for (h0, v0), (h1, v1) in zip(keys, keys[1:]):
        if h0 <= h < h1:
            return v0 + (v1 - v0) * _smooth((h - h0) / (h1 - h0))
    return night_floor


def band_weights(hour: float, starts: list[float] | None = None) -> dict[str, float]:
    """Continuous mix of the six bands (sums to 1) for grading and ambience: smoothstep between band MIDPOINTS, so the look never
    switches abruptly at a boundary. Hard labels stay in band_of_hour."""
    s = starts or DEFAULT_STARTS
    mids = [(s[0] + s[1]) / 2, (s[1] + s[2]) / 2, (s[2] + s[3]) / 2, (s[3] + s[4]) / 2, (s[4] + s[5]) / 2, (s[5] + s[0] + 24.0) / 2]
    pts = [mids[5] - 24.0] + mids + [mids[0] + 24.0]
    names = ["night", "dawn", "morning", "day", "sunset", "evening", "night", "dawn"]
    h = hour % 24.0
    if h < pts[0]:
        h += 24.0
    out = {n: 0.0 for n in BAND_NAMES}
    for i in range(len(pts) - 1):
        if pts[i] <= h < pts[i + 1]:
            w = _smooth((h - pts[i]) / (pts[i + 1] - pts[i]))
            out[names[i]] += 1.0 - w
            out[names[i + 1]] += w
            return out
    out["night"] = 1.0
    return out


# --- the one clock ------------------------------------------------------------------------------------------------------


class WorldClock:
    """The only time source. Every time-dependent system (supplies, crew needs, weather, events, repairs) must consume the game
    seconds returned by tick(); a paused clock returns 0, so nothing can advance while time is stopped. Location never touches it."""

    def __init__(self, minutes_per_day: float = 15.0, t: float = 0.0):
        self.minutes_per_day = minutes_per_day
        self.t = float(t)  # game seconds since the start of day 1, 00:00
        self.pauses: set[str] = set()
        self.where = "sea"

    def pause(self, reason: str) -> None:
        self.pauses.add(reason)

    def resume(self, reason: str) -> None:
        self.pauses.discard(reason)

    def is_paused(self) -> bool:
        return bool(self.pauses)

    def set_location(self, where: str) -> None:
        self.where = where  # deliberately does nothing else: the clock never changes speed or jumps between sea and shore

    def tick(self, real_dt: float) -> float:
        if self.pauses or real_dt <= 0.0:
            return 0.0
        dt = real_dt * 86400.0 / (self.minutes_per_day * 60.0)
        self.t += dt
        return dt

    def hour(self) -> float:
        return (self.t / 3600.0) % 24.0

    def day(self) -> int:
        return int(math.floor(self.t / 86400.0)) + 1


FUNCS = {"watch_index": watch_index, "watch_name": watch_name, "last_bell": last_bell, "hours_to_real_seconds": hours_to_real_seconds,
         "real_seconds_to_hours": real_seconds_to_hours, "days_to_real_minutes": days_to_real_minutes, "reports_between": reports_between,
         "band_of": band_of, "band_of_hour": band_of_hour, "daylight": daylight, "band_weights": band_weights}


def run_scenario(sc: dict) -> list[str]:
    """Plays a fixture scenario against WorldClock; returns mismatch descriptions."""
    clk, bad = WorldClock(sc.get("minutes_per_day", 15.0), sc.get("start_t", 0.0)), []
    for n, st in enumerate(sc["steps"]):
        op, dt = st["op"], None
        if op == "tick":
            dt = clk.tick(st["dt"])
        elif op == "pause":
            clk.pause(st["reason"])
        elif op == "resume":
            clk.resume(st["reason"])
        elif op == "where":
            clk.set_location(st["place"])
        for key, got in (("expect_dt", dt), ("expect_t", clk.t), ("expect_paused", clk.is_paused()), ("expect_hour", clk.hour()), ("expect_day", clk.day())):
            if key in st:
                want = st[key]
                ok = got == want if isinstance(want, bool) else got is not None and abs(got - want) < 1e-6
                if not ok:
                    bad.append(f"{sc['name']} step {n} ({op}): {key} expected {want}, got {got}")
    return bad
