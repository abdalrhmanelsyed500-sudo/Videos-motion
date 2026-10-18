"""Python twin of game/h2d/sail_model.gd (H2D-0.3): how the drawn sail answers the wind.

The H2D-0.2 sail was a fixed formula of wind speed plus a constant 2 Hz sine: it moved the same way in every weather, it
shivered in light air (the opposite of real cloth) and it never settled. This model has STATE instead:
  fill   how full the sail is. A damped spring (period 2.8 s) towards a target that depends on the wind speed, the angle to
         the wind (luffing, close-hauled, reaching, running), a gale (taut and flat) and a gust (the sail fills, overshoots a
         little, settles). Heavy, slow cloth.
  flap   flutter amplitude. It exists only when the sail is luffing with some wind in it, or for a moment when a gust ARRIVES
         (wind rising fast). It builds in 0.6 s and fades over 1.4 s; its rate depends on the wind and wanders irregularly.
  breath a sub-pixel, never repeating, slow movement in light air.
The shader (ship.gdshader) turns belly and flap into whole-pixel steps per 3-pixel band of the sail, so the pixel-art
silhouette is kept and nothing shimmers.
This is a model of the GDScript, NOT a Godot run.

  python tools/h2d/sail_logic.py             # print the behaviour in each weather
  python tools/h2d/sail_logic.py --fixture   # rewrite game/tests/fixtures/sail_cases.json
  python tools/h2d/sail_logic.py --check     # fixture in sync
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import env_logic as E  # noqa: E402

ROOT = E.ROOT
PREFIX = "sail."


def ss(a: float, b: float, x: float) -> float:
    return E.smoothstep(a, b, x)


def spring(x: float, v: float, target: float, period: float, zeta: float, dt: float) -> tuple[float, float]:
    return E.spring(x, v, target, period, zeta, dt)


def wander(t: float) -> float:
    """Irregular 0..1 value that never repeats (three incommensurate sines)."""
    return 0.5 + 0.5 * (0.5 * math.sin(1.7 * t + 0.3) + 0.3 * math.sin(0.93 * t + 2.1) + 0.2 * math.sin(2.9 * t + 4.4))


class Sail:
    def __init__(self, P: dict[str, float] | None = None) -> None:
        self.P = P or E.load_params()
        self.fill = 0.0
        self.fill_v = 0.0
        self.flap = 0.0
        self.phase = 0.0
        self.rise = 0.0
        self.gust_prev = 0.0
        self.breath = 0.0
        self.luff = 0.0
        self.slack = 1.0
        self.first = True

    def p(self, k: str) -> float:
        return self.P[PREFIX + k]

    def targets(self, wind_kn: float, gust: float, off_deg: float, no_go_deg: float) -> tuple[float, float]:
        """(luff 0..1, fill target)."""
        luff = 1.0 - ss(no_go_deg - 4.0, no_go_deg + 14.0, off_deg)
        wind_k = ss(self.p("light_air_kn"), self.p("full_air_kn"), wind_kn)
        angle_k = 0.55 + 0.45 * math.sin(math.radians(E.clamp(off_deg, 0.0, 180.0)))
        flat = 1.0 - self.p("gale_flat") * ss(24.0, 42.0, wind_kn)
        tgt = (1.0 - luff) * wind_k * angle_k * flat * (1.0 + self.p("gust_fill") * gust)
        return luff, tgt

    def snap(self, wind_kn: float, gust: float, off_deg: float, no_go_deg: float) -> None:
        luff, tgt = self.targets(wind_kn, gust, off_deg, no_go_deg)
        self.fill, self.fill_v, self.luff = tgt, 0.0, luff
        self.gust_prev = gust
        self.rise = 0.0
        self.flap = 0.0
        self.first = False

    def step(self, dt: float, wind_kn: float, gust: float, off_deg: float, no_go_deg: float, t: float) -> None:
        if self.first:
            self.snap(wind_kn, gust, off_deg, no_go_deg)
        luff, tgt = self.targets(wind_kn, gust, off_deg, no_go_deg)
        self.luff = luff
        self.fill, self.fill_v = spring(self.fill, self.fill_v, tgt, self.p("fill_period_s"), self.p("fill_zeta"), dt)
        wind_k = ss(self.p("light_air_kn"), self.p("full_air_kn"), wind_kn)
        self.slack = 1.0 - wind_k
        if dt > 0.0:
            raw = E.clamp((gust - self.gust_prev) / dt, 0.0, 3.0)
            self.rise += (raw - self.rise) * (1.0 - math.exp(-dt / 0.6))
        self.gust_prev = gust
        ft = E.clamp(luff * ss(1.5, 9.0, wind_kn) + self.p("flap_gust_gain") * self.rise * wind_k * (1.0 - luff), 0.0, 1.0)
        tau = self.p("flap_rise_s") if ft > self.flap else self.p("flap_fall_s")
        self.flap = E.approach(self.flap, ft, tau, dt)
        hz = self.p("flap_hz_base") + self.p("flap_hz_per_kn") * wind_kn
        self.phase += math.tau * hz * dt * (0.75 + 0.5 * wander(t * 0.31))
        per = self.p("breath_period_s")
        self.breath = 0.5 * (math.sin(math.tau * t / per + 1.3) + math.sin(math.tau * t / (per * 1.73) + 0.4))

    def out(self) -> dict[str, float]:
        belly = self.p("max_belly_px") * E.clamp(self.fill, 0.0, 1.1) + self.p("breath_px") * self.slack * self.breath
        return {"belly_px": belly, "flap_px": self.p("flap_max_px") * self.flap, "flap_phase": self.phase,
                "luff": self.luff, "fill": self.fill, "slack": self.slack}


def run(sail: Sail, seconds: float, wind_kn: float, gust_fn, off_deg: float, no_go: float = 40.0, t0: float = 0.0, dt: float = 1.0 / 60.0):
    n = int(seconds / dt)
    rows = []
    for i in range(n):
        t = t0 + (i + 1) * dt
        g = gust_fn(t)
        sail.step(dt, wind_kn * (1.0 + 0.45 * g), g, off_deg, no_go, t)
        o = sail.out()
        rows.append((t, o["belly_px"], o["flap_px"] * math.sin(o["flap_phase"]), o["flap_px"]))
    return rows


# the weathers: mean wind, how gusty, angle to the wind
WEATHERS = {
    "calm": (4.0, 0.0),
    "breezy": (14.0, E.gustiness(14.0, 0.0)),
    "rough": (24.0, E.gustiness(24.0, 0.25)),
    "gale": (36.0, E.gustiness(36.0, 0.7)),
}


def gust_fn_for(kind: float):
    return lambda t: E.smoothstep(0.60, 0.92, E.gust_noise(t)) * kind


def report() -> None:
    P = E.load_params()
    print("sail response, 60 s per case (belly px, flutter px; 'steps' = how many whole-pixel changes the shader would show per second)")
    for name, (wk, gk) in WEATHERS.items():
        for off, label in ((90.0, "beam reach"), (50.0, "close-hauled"), (20.0, "in irons")):
            s = Sail(P)
            rows = run(s, 60.0, wk, gust_fn_for(gk), off, t0=30.0)
            bel = [r[1] for r in rows]
            disp = [round(r[1] + r[2]) for r in rows]
            steps = sum(1 for a, b in zip(disp, disp[1:]) if a != b) / 60.0
            print(f"  {name:7s} {label:13s}: belly {min(bel):4.2f}..{max(bel):4.2f}  flap amp max {max(r[3] for r in rows):4.2f}  displacement steps {steps:4.2f}/s")


def make_fixture() -> dict:
    P = E.load_params()
    out: dict = {"cases": []}
    scen = [("calm_reach", 4.0, 0.0, 90.0), ("breezy_reach", 14.0, E.gustiness(14.0, 0.0), 90.0),
            ("gale_irons", 36.0, E.gustiness(36.0, 0.7), 25.0), ("rough_closehauled", 24.0, E.gustiness(24.0, 0.25), 50.0)]
    for name, wk, gk, off in scen:
        s = Sail(P)
        rows = []
        dt = 1.0 / 60.0
        samples = []
        for i in range(1800):
            t = 20.0 + (i + 1) * dt
            g = E.smoothstep(0.60, 0.92, E.gust_noise(t)) * gk
            s.step(dt, wk * (1.0 + 0.45 * g), g, off, 40.0, t)
            if (i + 1) % 150 == 0:
                o = s.out()
                samples.append({"t": t, "belly": o["belly_px"], "flap": o["flap_px"], "phase": o["flap_phase"], "luff": o["luff"], "fill": o["fill"], "slack": o["slack"]})
        out["cases"].append({"name": name, "wind_kn": wk, "gustiness": gk, "off_deg": off, "t0": 20.0, "samples": samples})
    return out


if __name__ == "__main__":
    dst = ROOT / "game" / "tests" / "fixtures" / "sail_cases.json"
    if len(sys.argv) > 1 and sys.argv[1] == "--fixture":
        dst.write_text(json.dumps(make_fixture(), indent=1) + "\n")
        print("wrote", dst)
    elif len(sys.argv) > 1 and sys.argv[1] == "--check":
        ok = json.loads(dst.read_text()) == json.loads(json.dumps(make_fixture()))
        print("sail fixture in sync" if ok else "sail fixture OUT OF SYNC: run sail_logic.py --fixture")
        sys.exit(0 if ok else 1)
    else:
        report()
