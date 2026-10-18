"""How long does the E1 slice take to SAIL (Module E1)? A crude VMG autopilot (best of 13 headings within 90 degrees of the
target bearing, re-chosen every 15 game minutes) sails each leg of slice_route.json starting at that checkpoint's own time.
It is an ESTIMATE of a competent player, not a measurement of one.
    python tools/world/slice_autopilot.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "data_tools"))
import ocean as O  # noqa: E402
import sea_state as SS  # noqa: E402

STEP_S, ARRIVE_KM, MAX_STEPS = 900.0, 40.0, 3000
REAL_S_PER_GAME_S = 1.0 / 96.0


def sail_leg(oc, a: dict, b: dict) -> tuple[float, float, bool]:
    st = SS.SeaState(oc)
    st.place(a["x_km"], a["y_km"], 0.0)
    t, steps = a["t_days"], 0
    while steps < MAX_STEPS:
        dx, dy = b["x_km"] - st.x_km, b["y_km"] - st.y_km
        d = math.hypot(dx, dy)
        if d < ARRIVE_KM:
            return st.distance_km, steps * STEP_S * REAL_S_PER_GAME_S / 60.0, True
        brg = math.degrees(math.atan2(dx, -dy))
        st.refresh(t)
        best = max(((oc.ground_velocity_kmh((brg + off) % 360.0, st.last_sample), (brg + off) % 360.0) for off in range(-90, 91, 15)),
                   key=lambda vh: (vh[0][0] * dx + vh[0][1] * dy) / d)
        st.heading_deg = best[1]
        st.advance(t, STEP_S)
        t += STEP_S / 86400.0
        steps += 1
    return st.distance_km, steps * STEP_S * REAL_S_PER_GAME_S / 60.0, False


def main() -> int:
    oc = O.load()
    cps = json.loads((ROOT / "game" / "data" / "world" / "slice_route.json").read_text())["checkpoints"]
    total = 0.0
    for a, b in zip(cps, cps[1:]):
        straight = math.hypot(b["x_km"] - a["x_km"], b["y_km"] - a["y_km"])
        dist, mins, ok = sail_leg(oc, a, b)
        total += mins
        note = "" if ok else "  (did not arrive)"
        print(f"{a['id']} -> {b['id']}: straight {straight:4.0f} km, sailed {dist:4.0f} km, {mins:4.0f} real min{note}")
    print(f"total about {total:.0f} real min ({total / 60:.1f} h); legs with the same place (5 -> 6) are a wait of one game day = 15 real min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
