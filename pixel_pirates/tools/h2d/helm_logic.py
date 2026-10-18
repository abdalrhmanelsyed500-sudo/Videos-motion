"""Python twin of game/h2d/helm.gd (the helm: rudder, yaw rate, heading and speed inertia). Same equations, same keys.

Used to (1) tune the numbers by simulation, (2) write the fixture tests/fixtures/helm_cases.json that test_helm.gd
replays. This is a model of the GDScript, NOT a Godot run.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEYS = ["max_turn_deg_s", "min_steerage", "steerage_full_kn", "rudder_rise_s", "rudder_return_s", "yaw_build_s",
        "yaw_brake_s", "speed_gain_s", "speed_loss_s"]


def load_params() -> dict[str, float]:
    out: dict[str, float] = {}
    doc = json.loads((ROOT / "game" / "data" / "tuning" / "tuning_helm.json").read_text())
    for r in doc["records"]:
        if r["key"].startswith("helm."):
            out[r["key"][5:]] = float(r["value"])
    return out


def approach(cur: float, target: float, tau: float, dt: float) -> float:
    if tau <= 0.0:
        return target
    return cur + (target - cur) * (1.0 - math.exp(-dt / tau))


class Helm:
    def __init__(self, p: dict[str, float] | None = None) -> None:
        self.p = p or load_params()
        self.heading = 0.0
        self.yaw_rate = 0.0
        self.rudder = 0.0
        self.speed = 0.0
        self.sensitivity = 1.0

    def steerage(self, speed_kn: float) -> float:
        k = min(max(speed_kn / self.p["steerage_full_kn"], 0.0), 1.0)
        return self.p["min_steerage"] + (1.0 - self.p["min_steerage"]) * k

    def step(self, dt: float, steer: float, target_speed_kn: float) -> None:
        steer = min(max(steer, -1.0), 1.0)
        tau_r = self.p["rudder_rise_s"] if abs(steer) > abs(self.rudder) or steer * self.rudder < 0 else self.p["rudder_return_s"]
        if steer * self.rudder < 0:
            tau_r = self.p["rudder_return_s"]  # reversing: the rudder comes back first
        self.rudder = approach(self.rudder, steer, tau_r, dt)
        want = self.rudder * self.p["max_turn_deg_s"] * self.sensitivity * self.steerage(self.speed)
        tau_y = self.p["yaw_build_s"] if abs(want) > abs(self.yaw_rate) else self.p["yaw_brake_s"]
        self.yaw_rate = approach(self.yaw_rate, want, tau_y, dt)
        self.heading = (self.heading + self.yaw_rate * dt) % 360.0
        tau_s = self.p["speed_gain_s"] if target_speed_kn > self.speed else self.p["speed_loss_s"]
        self.speed = approach(self.speed, target_speed_kn, tau_s, dt)


def wrap180(a: float) -> float:
    return (a + 540.0) % 360.0 - 180.0


def simulate(h: Helm, seconds: float, steer_fn, target_fn, dt: float = 1.0 / 60.0):
    n = int(round(seconds / dt))
    for i in range(n):
        t = i * dt
        h.step(dt, steer_fn(t), target_fn(t, h))
    return h


if __name__ == "__main__":
    P = load_params()
    print("params", P)
    h = Helm(P)
    h.speed = 5.0
    # hold D until 90 deg turned
    t = 0.0
    dt = 1 / 60
    while wrap180(h.heading - 0.0) < 90.0 and t < 20:
        h.step(dt, 1.0, 5.0)
        t += dt
    print("90 deg to starboard at full helm: %.2f s" % t)
    # after release, overshoot
    hd = h.heading
    for _ in range(int(2 / dt)):
        h.step(dt, 0.0, 5.0)
    print("coasting after release: +%.1f deg, yaw now %.2f deg/s" % (wrap180(h.heading - hd), h.yaw_rate))
    for secs in (0.1, 0.2, 0.3):
        h = Helm(P)
        h.speed = 5.0
        for i in range(int(secs / dt)):
            h.step(dt, 1.0, 5.0)
        for i in range(int(2 / dt)):
            h.step(dt, 0.0, 5.0)
        print("tap %.1f s -> %.1f deg total" % (secs, wrap180(h.heading)))
    h = Helm(P)
    h.speed = 5.0
    t = 0.0
    while h.yaw_rate < 0.9 * P["max_turn_deg_s"] and t < 5:
        h.step(dt, 1.0, 5.0)
        t += dt
    print("time to 90%% of max yaw rate: %.2f s" % t)
    h = Helm(P)
    h.speed = 5.0
    for i in range(int(1 / dt)):
        h.step(dt, 1.0, 5.0)
    print("after 1 s of full helm: %.1f deg, yaw %.1f deg/s" % (wrap180(h.heading), h.yaw_rate))
    h = Helm(P)
    h.speed = 5.0
    for i in range(int(8 / dt)):
        h.step(dt, 0.0, 0.6)
    print("into the wind (target 0.6 kn) 8 s: speed %.2f kn" % h.speed)
    h = Helm(P)
    h.speed = 0.6
    for i in range(int(1 / dt)):
        h.step(dt, 1.0, 0.6)
    print("in irons, 1 s of helm: %.1f deg (steerage %.2f)" % (wrap180(h.heading), h.steerage(0.6)))


def point_of_sail(off: float, no_go: float) -> str:
    if off < no_go:
        return "In irons"
    for lim, name in ((55.0, "Close-hauled"), (80.0, "Close reach"), (110.0, "Beam reach"), (155.0, "Broad reach")):
        if off < lim:
            return name
    return "Running"


def escape_direction(heading: float, wind_from: float) -> int:
    return 1 if wrap180(heading - wind_from) >= 0.0 else -1


def make_fixture() -> dict:
    """Scenarios replayed by tests/test_helm.gd (dt = 1/60, the same Euler steps as the GDScript)."""
    P = load_params()
    out: dict = {"params": P, "scenarios": [], "sail": [], "escape": []}
    dt = 1.0 / 60.0
    scen = [
        ("hold_D_then_release", 0.0, 5.0, 1.0, lambda t: 1.0 if t < 3.0 else 0.0, lambda t, h: 5.0, 6.0),
        ("tap_A_200ms", 10.0, 5.0, 1.0, lambda t: -1.0 if t < 0.2 else 0.0, lambda t, h: 5.0, 3.0),
        ("D_across_north", 355.0, 5.0, 1.0, lambda t: 1.0, lambda t, h: 5.0, 2.0),
        ("reverse_D_then_A", 90.0, 4.0, 1.0, lambda t: 1.0 if t < 1.0 else -1.0, lambda t, h: 4.0, 3.0),
        ("head_to_wind_bleeds_speed", 0.0, 5.0, 1.0, lambda t: 0.0, lambda t, h: 0.6, 10.0),
        ("in_irons_still_steers", 0.0, 0.6, 1.0, lambda t: 1.0, lambda t, h: 0.6, 2.0),
        ("double_sensitivity", 0.0, 5.0, 2.0, lambda t: 1.0, lambda t, h: 5.0, 2.0),
        ("regain_speed_after_irons", 0.0, 0.6, 1.0, lambda t: 0.0, lambda t, h: 5.0, 8.0),
    ]
    for name, hd, sp, sens, steer_fn, tgt_fn, secs in scen:
        h = Helm(P)
        h.heading, h.speed, h.sensitivity = hd, sp, sens
        samples = []
        n = int(round(secs / dt))
        marks = {int(round(m / dt)) for m in [x * 0.5 for x in range(1, int(secs * 2) + 1)]}
        for i in range(n):
            h.step(dt, steer_fn(i * dt), tgt_fn(i * dt, h))
            if (i + 1) in marks:
                samples.append({"t": round((i + 1) * dt, 4), "heading": h.heading, "yaw": h.yaw_rate,
                                "rudder": h.rudder, "speed": h.speed})
        out["scenarios"].append({"name": name, "heading": hd, "speed": sp, "sensitivity": sens, "seconds": secs,
                                 "samples": samples})
    for off in (0, 20, 39.9, 40, 54.9, 55, 79.9, 80, 109.9, 110, 154.9, 155, 180):
        out["sail"].append({"off": off, "no_go": 40.0, "name": point_of_sail(off, 40.0)})
    for hd, wf in ((10, 0), (350, 0), (0, 0), (100, 90), (80, 90), (200, 180), (170, 180), (0, 350), (5, 350)):
        out["escape"].append({"heading": hd, "wind_from": wf, "dir": escape_direction(hd, wf)})
    return out


if __name__ == "__main__" and len(__import__("sys").argv) > 1 and __import__("sys").argv[1] == "--fixture":
    dst = ROOT / "game" / "tests" / "fixtures" / "helm_cases.json"
    dst.write_text(json.dumps(make_fixture(), indent=1) + "\n")
    print("wrote", dst)


if __name__ == "__main__" and len(__import__("sys").argv) > 1 and __import__("sys").argv[1] == "--check":
    import sys
    dst = ROOT / "game" / "tests" / "fixtures" / "helm_cases.json"
    ok = json.loads(dst.read_text()) == json.loads(json.dumps(make_fixture()))
    gd = (ROOT / "game" / "h2d" / "helm.gd").read_text()
    P = load_params()
    for key, val in P.items():
        if f'"{key}": {val}' not in gd and f'"{key}": {float(val)}' not in gd:
            print("helm.gd DEFAULTS differ from tuning_helm.json for", key)
            ok = False
    print("helm fixture + defaults in sync" if ok else "helm fixture/defaults OUT OF SYNC: run helm_logic.py --fixture")
    sys.exit(0 if ok else 1)
