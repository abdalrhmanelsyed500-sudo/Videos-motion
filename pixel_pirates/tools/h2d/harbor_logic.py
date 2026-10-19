"""Python twin of game/h2d/harbor.gd (H2D-1 docking: assisted path, undocking, harbour speed ease, hull footprint, prompt).
Same equations, same keys. Used to (1) own the tuning table, written to game/data/tuning/tuning_harbor.json, and (2) write the
fixture game/tests/fixtures/harbor_cases.json that tests/test_harbor.gd replays. This is a model of the GDScript, NOT a Godot run.

  python tools/h2d/harbor_logic.py --write   # rewrite tuning_harbor.json and the fixture
  python tools/h2d/harbor_logic.py --check   # fail if the JSON or the fixture differ from this file, or DEFAULTS in harbor.gd drift
  python tools/h2d/harbor_logic.py           # print a plain-language timing report
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TUNING = ROOT / "game/data/tuning/tuning_harbor.json"
FIXTURE = ROOT / "game/tests/fixtures/harbor_cases.json"
LAYOUT = ROOT / "game/h2d/art/anvil_cay.json"
GD = ROOT / "game/h2d/harbor.gd"
SRC = "H2D-1 first harbor; first values chosen by simulation, confirm by hand on the dev PC"
# key, value, unit, min, max, note
TABLE = [
    ("dock_speed_ms", 5.0, "scene metres per second", 1, 15, "Average speed of the assisted docking path. The time is path length / this, clamped to the two keys below."),
    ("dock_min_s", 6.0, "seconds", 2, 30, "The shortest docking manoeuvre (so a ship close to the berth does not snap into place)."),
    ("dock_max_s", 16.0, "seconds", 4, 60, "The longest docking manoeuvre (a ship at the far corner of the dock zone)."),
    ("undock_speed_ms", 3.5, "scene metres per second", 1, 15, "Average speed backing out of the berth to the approach point."),
    ("undock_min_s", 6.0, "seconds", 2, 30, "The shortest time backing out."),
    ("turn_out_s", 3.0, "seconds", 1, 10, "Time to swing the bow from north to south (heading 180) at the approach point before the helm is handed back."),
    ("head_turn_frac", 0.12, "fraction", 0.02, 0.5, "Share of the docking time over which the ship turns from its own heading onto the path."),
    ("ease_min", 0.3, "ratio", 0.1, 1.0, "Scene speed multiplier right at the berth (1 = no slowing near the harbour)."),
    ("ease_near_m", 40.0, "metres", 5, 200, "Distance to the berth at and below which the speed multiplier is ease_min."),
    ("ease_far_m", 110.0, "metres", 20, 400, "Distance to the berth at and beyond which the ship sails at full scene speed."),
    ("hint_radius_m", 260.0, "metres", 50, 1000, "Within this distance of the berth the HUD shows the distance, the bearing and how to dock."),
    ("half_len_m", 10.0, "metres", 4, 14, "Hull footprint: how far the bow and the stern probes are from the centre (the grounding test)."),
    ("side_m", 2.4, "metres", 0.5, 4, "Hull footprint: how far the side probes are from the centre line."),
    ("ground_limit_m", 0.3, "metres", 0, 2, "Land higher than this under any hull probe runs the ship aground."),
]
P = {k: v for k, v, *_ in TABLE}
COMPASS = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]
SAILING, DOCKING, DOCKED, UNDOCKING = 0, 1, 2, 3


def wrap180(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0


def bearing_deg(dx: float, dz: float) -> float:
    return math.degrees(math.atan2(dx, -dz)) % 360.0


def smoothstep(a: float, b: float, x: float) -> float:
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def smootherstep(u: float) -> float:
    c = min(max(u, 0.0), 1.0)
    return c * c * c * (c * (c * 6.0 - 15.0) + 10.0)


class Harbor:
    def __init__(self, layout: dict, params: dict | None = None):
        self.p = dict(P if params is None else params)
        self.state = SAILING
        b, a, z = layout["berth"], layout["approach"], layout["dock_zone"]
        self.bx, self.bz, self.bh = float(b["x"]), float(b["z"]), float(b["heading_deg"])
        self.ax, self.az = float(a["x"]), float(a["z"])
        self.zx0, self.zz0, self.zx1, self.zz1 = float(z["x0"]), float(z["z0"]), float(z["x1"]), float(z["z1"])
        self.port_name = "Anvil Harbor"
        self.t = 0.0
        self.dur = 1.0
        self.phase = 0
        self.x0 = self.z0 = self.h0 = 0.0

    def in_zone(self, x, z):
        return self.zx0 <= x <= self.zx1 and self.zz0 <= z <= self.zz1

    def dist_to_berth(self, x, z):
        return math.sqrt((x - self.bx) ** 2 + (z - self.bz) ** 2)

    def speed_scale(self, x, z):
        if self.state != SAILING:
            return 1.0
        s = smoothstep(self.p["ease_near_m"], self.p["ease_far_m"], self.dist_to_berth(x, z))
        return self.p["ease_min"] + (1.0 - self.p["ease_min"]) * s

    def footprint(self, x, z, heading):
        a = math.radians(heading)
        fx, fz = math.sin(a), -math.cos(a)
        sx, sz = -fz, fx
        hl, sd = self.p["half_len_m"], self.p["side_m"]
        offs = [(hl, 0.0), (-hl, 0.0), (0.0, 0.0), (hl * 0.4, sd), (hl * 0.4, -sd), (-hl * 0.4, sd), (-hl * 0.4, -sd)]
        return [[x + fx * o[0] + sx * o[1], z + fz * o[0] + sz * o[1]] for o in offs]

    def request(self, x, z, heading):
        if self.state == SAILING:
            if not self.in_zone(x, z):
                return "not_in_zone"
            self.state = DOCKING
            self.t = 0.0
            self.x0, self.z0, self.h0 = x, z, heading
            n = self.bez_len(x, z)
            self.dur = min(max(n / self.p["dock_speed_ms"], self.p["dock_min_s"]), self.p["dock_max_s"])
            return "docking"
        if self.state == DOCKED:
            self.state = UNDOCKING
            self.t = 0.0
            self.phase = 0
            ln = math.sqrt((self.ax - self.bx) ** 2 + (self.az - self.bz) ** 2)
            self.dur = max(ln / self.p["undock_speed_ms"], self.p["undock_min_s"])
            return "casting_off"
        return "busy"

    def bez_point(self, u):
        v = 1.0 - u
        return [v * v * self.x0 + 2.0 * v * u * self.ax + u * u * self.bx, v * v * self.z0 + 2.0 * v * u * self.az + u * u * self.bz]

    def bez_tangent(self, u):
        tx = 2.0 * (1.0 - u) * (self.ax - self.x0) + 2.0 * u * (self.bx - self.ax)
        tz = 2.0 * (1.0 - u) * (self.az - self.z0) + 2.0 * u * (self.bz - self.az)
        if tx * tx + tz * tz < 0.000001:
            tx, tz = self.bx - self.ax, self.bz - self.az
        return [tx, tz]

    def bez_len(self, x, z):
        self.x0, self.z0 = x, z
        total = 0.0
        prev = self.bez_point(0.0)
        for i in range(1, 17):
            q = self.bez_point(i / 16.0)
            total += math.sqrt((q[0] - prev[0]) ** 2 + (q[1] - prev[1]) ** 2)
            prev = q
        return total

    def step(self, dt):
        if self.state == DOCKING:
            self.t += dt
            ul = min(max(self.t / self.dur, 0.0), 1.0)
            u = smootherstep(ul)
            p = self.bez_point(u)
            tg = self.bez_tangent(u)
            tb = bearing_deg(tg[0], tg[1])
            w = smoothstep(0.0, self.p["head_turn_frac"], ul)
            hd = (self.h0 + wrap180(tb - self.h0) * w) % 360.0
            done = ul >= 1.0
            if done:
                self.state = DOCKED
                hd = self.bh
                p = [self.bx, self.bz]
            return {"x": p[0], "z": p[1], "heading": hd, "moor": smoothstep(0.7, 1.0, ul), "state": self.state, "done": done}
        if self.state == DOCKED:
            return {"x": self.bx, "z": self.bz, "heading": self.bh, "moor": 1.0, "state": self.state, "done": False}
        if self.state == UNDOCKING:
            self.t += dt
            if self.phase == 0:
                ul = min(max(self.t / self.dur, 0.0), 1.0)
                u = smootherstep(ul)
                out = {"x": self.bx + (self.ax - self.bx) * u, "z": self.bz + (self.az - self.bz) * u, "heading": self.bh,
                       "moor": 1.0 - smoothstep(0.0, 0.3, ul), "state": self.state, "done": False}
                if ul >= 1.0:
                    self.phase = 1
                    self.t = 0.0
                return out
            ul2 = min(max(self.t / self.p["turn_out_s"], 0.0), 1.0)
            hd2 = (self.bh + 180.0 * smootherstep(ul2)) % 360.0
            done2 = ul2 >= 1.0
            if done2:
                self.state = SAILING
                hd2 = (self.bh + 180.0) % 360.0
            return {"x": self.ax, "z": self.az, "heading": hd2, "moor": 0.0, "state": self.state, "done": done2}
        return {"x": 0.0, "z": 0.0, "heading": 0.0, "moor": 0.0, "state": self.state, "done": False}

    def prompt(self, x, z):
        dist = self.dist_to_berth(x, z)
        brg = bearing_deg(self.bx - x, self.bz - z)
        near = dist <= self.p["hint_radius_m"]
        return {"state": self.state, "dist": dist, "bearing": brg, "near": near, "can_dock": self.state == SAILING and self.in_zone(x, z)}


def load_layout() -> dict:
    return json.loads(LAYOUT.read_text())["harbor_layout"]


def tuning_doc() -> dict:
    recs = []
    for k, v, unit, lo, hi, note in TABLE:
        recs.append({"key": "harbor." + k, "value": v, "unit": unit, "min": lo, "max": hi, "provisional": True, "owner": "E1",
                     "source": SRC, "note": note})
    return {"schema": 1, "kind": "tuning", "records": recs}


def make_fixture() -> dict:
    lay = load_layout()
    out: dict = {"params": P, "scale": [], "footprint": [], "dock": [], "undock": [], "request": []}
    h = Harbor(lay)
    for x, z in [(21.4, 21.0), (21.4, 41.0), (21.4, 61.0), (21.4, 91.0), (21.4, 131.0), (60.0, 21.0), (-100.0, 140.0)]:
        out["scale"].append({"x": x, "z": z, "k": h.speed_scale(x, z)})
    for x, z, hd in [(21.4, 21.0, 0.0), (10.0, 60.0, 45.0), (0.0, 0.0, 270.0)]:
        out["footprint"].append({"x": x, "z": z, "heading": hd, "pts": h.footprint(x, z, hd)})
    dt = 1.0 / 30.0
    for name, x, z, hd in [("from_zone_corner", 4.0, 98.0, 200.0), ("from_mouth", 21.4, 60.0, 0.0), ("from_west", 8.0, 50.0, 90.0)]:
        h = Harbor(lay)
        assert h.request(x, z, hd) == "docking"
        marks = {}
        n = int(math.ceil(h.dur / dt)) + 5
        samples = []
        for i in range(n):
            r = h.step(dt)
            if (i + 1) % 15 == 0 or r["done"]:
                samples.append({"i": i + 1, **{k: r[k] for k in ("x", "z", "heading", "moor", "state", "done")}})
            if r["done"]:
                break
        out["dock"].append({"name": name, "x": x, "z": z, "heading": hd, "dur": h.dur, "dt": dt, "samples": samples})
        marks = None
        del marks
        # then undock
        assert h.state == DOCKED
        assert h.request(h.bx, h.bz, h.bh) == "casting_off"
        samples = []
        for i in range(2000):
            r = h.step(dt)
            if (i + 1) % 15 == 0 or r["done"]:
                samples.append({"i": i + 1, **{k: r[k] for k in ("x", "z", "heading", "moor", "state", "done")}})
            if r["done"]:
                break
        out["undock"].append({"name": name, "dt": dt, "samples": samples})
    h = Harbor(lay)
    seq = []
    seq.append(["not_in_zone", h.request(100.0, 200.0, 0.0)])
    seq.append(["docking", h.request(20.0, 70.0, 0.0)])
    seq.append(["busy", h.request(20.0, 70.0, 0.0)])
    out["request"] = [{"expect": a, "got": b} for a, b in seq]
    return out


def timing_report() -> list[str]:
    lay = load_layout()
    lines = []
    for name, x, z, hd in [("zone corner", 4.0, 98.0, 200.0), ("harbour mouth", 21.4, 60.0, 0.0), ("west of the mouth", 8.0, 50.0, 90.0)]:
        h = Harbor(lay)
        h.request(x, z, hd)
        lines.append(f"docking from the {name}: {h.dur:.1f} s")
    h = Harbor(lay)
    h.state = DOCKED
    h.request(h.bx, h.bz, h.bh)
    lines.append(f"casting off: {h.dur:.1f} s backing out + {h.p['turn_out_s']:.1f} s turning")
    h = Harbor(lay)
    lines.append("scene speed multiplier: " + ", ".join(f"{d} m: x{h.speed_scale(h.bx, h.bz + d):.2f}" for d in (20, 40, 60, 80, 110, 150)))
    return lines


def check() -> int:
    errs = []
    if not TUNING.exists() or json.loads(TUNING.read_text()) != tuning_doc():
        errs.append(f"{TUNING.relative_to(ROOT)} is out of date: run harbor_logic.py --write")
    if not FIXTURE.exists() or json.loads(FIXTURE.read_text()) != json.loads(json.dumps(make_fixture())):
        errs.append(f"{FIXTURE.relative_to(ROOT)} is out of date: run harbor_logic.py --write")
    src = GD.read_text()
    m = re.search(r"const DEFAULTS := \{(.*?)\n\}", src, re.S)
    gd = {k: float(v) for k, v in re.findall(r'"(\w+)":\s*(-?[0-9.]+)', m.group(1))} if m else {}
    if gd != {k: float(v) for k, v in P.items()}:
        errs.append("DEFAULTS in harbor.gd differ from the table in harbor_logic.py")
    for e in errs:
        print("FAIL", e)
    print("PASS harbor twin, tuning JSON, fixture and GDScript defaults are in sync" if not errs else f"{len(errs)} ERROR(S)")
    return 1 if errs else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        TUNING.write_text(json.dumps(tuning_doc(), indent=1).replace('\n  {', '\n  {') + "\n")
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(make_fixture(), indent=1) + "\n")
        print("wrote", TUNING.relative_to(ROOT), "and", FIXTURE.relative_to(ROOT))
        return 0
    if a.check:
        return check()
    print("\n".join(timing_report()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
