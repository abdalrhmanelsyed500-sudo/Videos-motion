"""Python reference for game/h2d/ship_sprite.gd (heading frame, sail trim row, sea scale). Fixture: game/tests/fixtures/ship_sprite_cases.json.

Heading is compass degrees clockwise from north (0 = north = up the screen). The wind direction is the direction the wind
blows FROM, same convention as SeaState.
"""
from __future__ import annotations

import math

HEADINGS = 16
TRIMS_DEG = (-80, -45, 0, 45, 80)  # sail sheet rows; + = boom swung to starboard
WORLD_M_PER_SCENE_M = 10.0  # H2D-0 sea scale (provisional H2D0-3): 1 scene metre stands for 10 world metres
KN_TO_MS = 0.514444


def wrap180(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0


def heading_frame(heading_deg: float, n: int = HEADINGS) -> int:
    return int(math.floor((heading_deg % 360.0) / (360.0 / n) + 0.5)) % n


def trim_row(heading_deg: float, wind_from_deg: float) -> int:
    """Sheet row for the sail layer: the boom is eased to the lee side, further out the more the wind is behind."""
    rel = wrap180(wind_from_deg - heading_deg)  # +90 = wind on the starboard beam
    a = abs(rel)
    mag = 0 if a < 50.0 else (1 if a < 110.0 else 2)
    if mag == 0:
        return 2
    lee_is_port = rel > 0.0  # wind from starboard: boom goes to port (negative trim)
    if lee_is_port:
        return 1 if mag == 1 else 0
    return 3 if mag == 1 else 4


def scene_speed_ms(speed_kn: float) -> float:
    """Scene metres per second: the real speed in world metres per real second, divided by the sea scale.

    World time runs 96 game seconds per real second, so 5 kn (2.572 m/s) covers 246.9 world metres per real second.
    """
    return speed_kn * KN_TO_MS * 96.0 / WORLD_M_PER_SCENE_M


# ---- wave model (twin of game/h2d/wave_model.gd) ---------------------------------------------------------------
G = 9.81
DIR_OFFSETS_DEG = (0.0, 22.0, -38.0, 65.0)
LENGTHS_M = (46.0, 27.0, 15.0, 8.5)
SHARES = (0.55, 0.28, 0.12, 0.05)


def wave_params(wave_m: float, wind_from_deg: float, ice: float) -> list[list[float]]:
    to_deg = wind_from_deg + 180.0
    amp_total = 0.5 * wave_m * (1.0 - 0.85 * min(1.0, max(0.0, ice)))
    out = []
    for i in range(4):
        a = math.radians(to_deg + DIR_OFFSETS_DEG[i])
        wl = LENGTHS_M[i] * (0.8 + 0.06 * wave_m)
        out.append([math.sin(a), -math.cos(a), math.tau / wl, amp_total * SHARES[i]])
    return out


def wave_height(p: list[list[float]], x: float, z: float, t: float) -> float:
    return sum(w[3] * math.sin(w[2] * (w[0] * x + w[1] * z) - math.sqrt(G * w[2]) * t) for w in p)
