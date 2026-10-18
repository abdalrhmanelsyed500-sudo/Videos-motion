"""Ship position integrator for the E1 vertical slice (Python twin of game/core/sea_state.gd).
Pure arithmetic over ocean.py: heading and wind give a ground velocity, the clock gives elapsed game seconds, the position moves.
The full ocean sample is refreshed every SAMPLE_INTERVAL_S game seconds (15 game minutes = 9.4 real seconds): the weather
changes over hours and tens of kilometres, so this costs nothing visible and keeps the hot path cheap on the dev PC.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ocean as O  # noqa: E402

SAMPLE_INTERVAL_S = 900.0
SUBSTEP_S = 600.0


class SeaState:
    def __init__(self, ocean: O.Ocean):
        self.ocean = ocean
        self.x_km, self.y_km, self.heading_deg = 7000.0, 2650.0, 0.0
        self.distance_km = 0.0
        self.last_sample: dict = {}
        self.sample_t_days = -1.0e9

    def place(self, x_km: float, y_km: float, heading_deg: float) -> None:
        self.x_km, self.y_km, self.heading_deg = x_km, y_km, heading_deg
        self.last_sample = {}

    def refresh(self, t_days: float) -> None:
        self.last_sample = self.ocean.sample(self.x_km, self.y_km, t_days)
        self.sample_t_days = t_days

    def advance(self, t_start_days: float, game_seconds: float) -> None:
        left, t = game_seconds, t_start_days
        while left > 0.0:
            dt = min(left, SUBSTEP_S)
            if not self.last_sample or t - self.sample_t_days >= SAMPLE_INTERVAL_S / 86400.0:
                self.last_sample = self.ocean.sample(self.x_km, self.y_km, t)
                self.sample_t_days = t
            v = self.ocean.ground_velocity_kmh(self.heading_deg, self.last_sample)
            h = dt / 3600.0
            nx = O.clamp(self.x_km + v[0] * h, 0.0, self.ocean.W)
            ny = O.clamp(self.y_km + v[1] * h, 0.0, self.ocean.H)
            self.distance_km += math.sqrt((nx - self.x_km) ** 2 + (ny - self.y_km) ** 2)
            self.x_km, self.y_km = nx, ny
            t += dt / 86400.0
            left -= dt

    def speed_kn(self) -> float:
        if not self.last_sample:
            return 0.0
        s = self.last_sample
        return self.ocean.speed_through_water_kmh(self.heading_deg, s["wind_kn"], s["wind_from_deg"], s["ice"]) / O.KN_KMH
