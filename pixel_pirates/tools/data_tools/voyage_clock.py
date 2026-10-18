"""Voyage clock (Module B2): watches, bells, the daily Morning Report, time scale and voyage bands.
Pure functions. The GDScript twin is game/core/voyage_clock.gd; both run game/tests/fixtures/clock_cases.json.

Ship's time: 24 h = 6 watches of crew.watch_length_hours (4). Bells strike every half hour; eight bells end a watch.
The Morning Report is due at eight bells of the Morning watch (08:00 ship time)."""
from __future__ import annotations

import math

WATCH_NAMES = ["Middle", "Morning", "Forenoon", "Afternoon", "Dog", "First"]  # 00-04, 04-08, 08-12, 12-16, 16-20, 20-24
REPORT_HOUR = 8.0


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


def ashore_game_hours(real_minutes: float, game_min_per_real_min: float) -> float:
    """Game hours that pass while the player spends this many real minutes ashore."""
    return real_minutes * game_min_per_real_min / 60.0


def days_to_real_minutes(days: float, minutes_per_day: float) -> float:
    return days * minutes_per_day


def reports_between(abs_hour_from: float, abs_hour_to: float) -> int:
    """Morning Reports due while the clock runs from one absolute hour to another (boundary: from < 08:00 <= to)."""
    return int(math.floor((abs_hour_to - REPORT_HOUR) / 24.0) - math.floor((abs_hour_from - REPORT_HOUR) / 24.0))


def band_of(minutes: float, hop_min: float, hop_max: float, passage_max: float, crossing_max: float, dead_max: float) -> str:
    if minutes < hop_min:
        return "below"
    for name, top in (("hop", hop_max), ("passage", passage_max), ("crossing", crossing_max), ("dead", dead_max)):
        if minutes <= top:
            return name
    return "beyond"


FUNCS = {"watch_index": watch_index, "watch_name": watch_name, "last_bell": last_bell, "hours_to_real_seconds": hours_to_real_seconds,
         "real_seconds_to_hours": real_seconds_to_hours, "days_to_real_minutes": days_to_real_minutes, "ashore_game_hours": ashore_game_hours, "reports_between": reports_between,
         "band_of": band_of}
