"""Python twin of game/h2d/env_model.gd, the shaped-wave functions of game/h2d/wave_model.gd and game/h2d/ship_motion.gd (H2D-0.2).

One environmental state (wind with gusts, sea state, rain, visibility) from which the waves, the rain, the spray and the ship's
motion are all derived. Used to tune the numbers by simulation and to write tests/fixtures/env_cases.json for tests/test_env.gd.
This is a model of the GDScript, NOT a Godot run.

  python tools/h2d/env_logic.py            # print the behaviour of each sea state and of a transition
  python tools/h2d/env_logic.py --fixture  # rewrite game/tests/fixtures/env_cases.json
  python tools/h2d/env_logic.py --check    # fixture and tuning JSON in sync
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KN_TO_MS = 0.514444
G = 9.81
DIR_OFFSETS_DEG = [0.0, 22.0, -38.0, 65.0]
LENGTHS_M = [46.0, 27.0, 15.0, 8.5]
SHARES = [0.55, 0.28, 0.12, 0.05]
SHIP_LEN = 22.0
SHIP_BEAM = 6.2
CAM_PITCH_DEG = 48.0


def load_params() -> dict[str, float]:
    out: dict[str, float] = {}
    doc = json.loads((ROOT / "game" / "data" / "tuning" / "tuning_env.json").read_text())
    for r in doc["records"]:
        out[r["key"]] = float(r["value"])
    oc = json.loads((ROOT / "game" / "data" / "tuning" / "tuning_ocean.json").read_text())
    for r in oc["records"]:
        if r["key"] in ("ocean.visibility_clear_km", "ocean.fog_vis_coeff", "ocean.rain_vis_coeff"):
            out[r["key"]] = float(r["value"])
    return out


def clamp(x: float, a: float, b: float) -> float:
    return min(max(x, a), b)


def smoothstep(a: float, b: float, x: float) -> float:
    t = clamp((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def approach(cur: float, target: float, tau: float, dt: float) -> float:
    if tau <= 0.0:
        return target
    return cur + (target - cur) * (1.0 - math.exp(-dt / tau))


def wrap180(a: float) -> float:
    return (a + 540.0) % 360.0 - 180.0


def approach_angle(cur: float, target: float, tau: float, dt: float) -> float:
    return (cur + wrap180(target - cur) * (1.0 - math.exp(-dt / max(tau, 1e-6)))) % 360.0


def vec_to(deg_to: float) -> tuple[float, float]:
    a = math.radians(deg_to)
    return (math.sin(a), -math.cos(a))


def gust_noise(t: float) -> float:
    return 0.5 + 0.5 * (0.55 * math.sin(0.31 * t + 1.1) + 0.30 * math.sin(0.77 * t + 4.0) + 0.15 * math.sin(1.93 * t + 2.2))


def gustiness(wind_kn: float, storm: float) -> float:
    return clamp((wind_kn - 3.0) / 14.0, 0.0, 1.0) * (0.75 + 0.25 * storm)


def sea_class(sea: float, P: dict[str, float]) -> str:
    if sea < P["env.sea_calm_max"]:
        return "Calm"
    if sea < P["env.sea_breezy_max"]:
        return "Breezy"
    if sea < P["env.sea_rough_max"]:
        return "Rough"
    if sea < P["env.sea_storm_min"]:
        return "Gale"
    return "Storm"


class Env:
    def __init__(self, P: dict[str, float] | None = None) -> None:
        self.P = P or load_params()
        self.clear_km = self.P["ocean.visibility_clear_km"]
        self.fog_coeff = self.P["ocean.fog_vis_coeff"]
        self.rain_coeff = self.P["ocean.rain_vis_coeff"]
        self.wind_kn = 8.0
        self.wind_from = 0.0
        self.wave_m = 1.0
        self.wave_to = 180.0
        self.rain = 0.0
        self.storm = 0.0
        self.fog = 0.0
        self.manual_gust = 0.0
        self.gust = 0.0
        self.wind_inst_kn = 8.0
        self.wind_from_inst = 0.0
        self.sea = 0.0
        self.adv = [0.0, 0.0]
        self.rain_inst = 0.0
        self.visibility_km = 20.0
        self.time = 0.0

    def snap(self, tgt: dict[str, float]) -> None:
        self.wind_kn = tgt["wind_kn"]
        self.wind_from = tgt["wind_from_deg"] % 360.0
        self.wave_m = tgt["wave_m"]
        self.wave_to = (self.wind_from + 180.0) % 360.0
        self.rain = tgt["rain"]
        self.storm = tgt["storm"]
        self.fog = tgt["fog"]
        self.manual_gust = 0.0
        self._derive(0.0, 0.0)

    def trigger_gust(self) -> None:
        self.manual_gust = 1.0

    def step(self, dt: float, tgt: dict[str, float], t: float) -> None:
        P = self.P
        self.wind_kn = approach(self.wind_kn, tgt["wind_kn"], P["env.wind_tau_s"], dt)
        self.wind_from = approach_angle(self.wind_from, tgt["wind_from_deg"], P["env.wind_dir_tau_s"], dt)
        growing = tgt["wave_m"] > self.wave_m
        self.wave_m = approach(self.wave_m, tgt["wave_m"], P["env.sea_build_s"] if growing else P["env.sea_decay_s"], dt)
        self.wave_to = approach_angle(self.wave_to, (self.wind_from + 180.0) % 360.0, P["env.wave_dir_tau_s"], dt)
        up = tgt["rain"] > self.rain
        self.rain = approach(self.rain, tgt["rain"], P["env.rain_build_s"] if up else P["env.rain_decay_s"], dt)
        self.storm = approach(self.storm, tgt["storm"], P["env.air_tau_s"], dt)
        self.fog = approach(self.fog, tgt["fog"], P["env.air_tau_s"], dt)
        self.manual_gust *= math.exp(-dt / P["env.gust_manual_decay_s"])
        self._derive(t, dt)

    def _derive(self, t: float, dt: float) -> None:
        P = self.P
        self.time = t
        g_det = smoothstep(0.60, 0.92, gust_noise(t)) * gustiness(self.wind_kn, self.storm)
        self.gust = max(g_det, self.manual_gust)
        self.wind_inst_kn = self.wind_kn * (1.0 + P["env.gust_gain"] * self.gust)
        self.wind_from_inst = (self.wind_from + P["env.gust_veer_deg"] * self.gust * math.sin(0.37 * t)) % 360.0
        wt = vec_to(self.wind_from_inst + 180.0)
        ms = self.wind_inst_kn * KN_TO_MS
        self.adv[0] += wt[0] * ms * dt
        self.adv[1] += wt[1] * ms * dt
        self.sea = clamp(P["env.sea_wave_w"] * self.wave_m / P["env.sea_wave_ref_m"]
                         + P["env.sea_wind_w"] * self.wind_kn / P["env.sea_wind_ref_kn"]
                         + P["env.sea_storm_w"] * self.storm, 0.0, 1.0)
        self.rain_inst = clamp(self.rain * (1.0 + 0.25 * self.gust - 0.08), 0.0, 1.0)
        self.visibility_km = self.clear_km * math.exp(-(self.fog_coeff * self.fog + self.rain_coeff * self.rain_inst))

    @property
    def wave_vis_m(self) -> float:
        return self.wave_m * self.P["env.wave_visual_gain"] * (1.0 + 0.06 * self.gust)

    def sea_name(self) -> str:
        return sea_class(self.sea, self.P)


def crest_bias(p: float) -> float:
    n = 64
    s = 0.0
    for i in range(n):
        s += (0.5 + 0.5 * math.cos(math.tau * i / n)) ** p
    return 2.0 * (s / n) - 1.0


def wave_build(wave_vis_m: float, wave_to_deg: float, sea: float, ice: float, P: dict[str, float]) -> dict:
    p = P["env.crest_p_calm"] + (P["env.crest_p_gale"] - P["env.crest_p_calm"]) * sea
    spread = 1.0 - 0.3 * sea
    amp_total = 0.5 * wave_vis_m * (1.0 - 0.85 * clamp(ice, 0.0, 1.0))
    waves = []
    for i in range(4):
        a = math.radians(wave_to_deg + DIR_OFFSETS_DEG[i] * spread)
        wl = LENGTHS_M[i] * (0.8 + 0.06 * wave_vis_m)
        waves.append([math.sin(a), -math.cos(a), math.tau / wl, amp_total * SHARES[i]])
    return {"waves": waves, "p": p, "bias": crest_bias(p)}


def wave_height(b: dict, x: float, z: float, t: float) -> float:
    h = 0.0
    p = b["p"]
    for w in b["waves"]:
        k = w[2]
        ph = k * (w[0] * x + w[1] * z) - math.sqrt(G * k) * t
        q = 0.5 + 0.5 * math.cos(ph)
        h += w[3] * (2.0 * (max(q, 0.0001) ** p) - 1.0 - b["bias"])
    return h


def soft_limit(x: float, m: float) -> float:
    return m * math.tanh(x / m)


def spring(x: float, v: float, target: float, period: float, zeta: float, dt: float) -> tuple[float, float]:
    w = math.tau / period
    n = max(1, int(math.ceil(dt / (1.0 / 90.0))))
    h = dt / n
    for _ in range(n):
        v += (w * w * (target - x) - 2.0 * zeta * w * v) * h
        x += v * h
    return x, v


class Motion:
    def __init__(self, P: dict[str, float] | None = None) -> None:
        self.P = P or load_params()
        self.heave = self.heave_v = 0.0
        self.pitch = self.pitch_v = 0.0
        self.roll = self.roll_v = 0.0
        self.prev: list[float] | None = None
        self.cool = [0.0, 0.0, 0.0]
        self.slam = 0.0
        self.events: list[tuple[int, float]] = []

    def step(self, dt: float, b: dict, x: float, z: float, heading_deg: float, t: float,
             wind_to: tuple[float, float], wind_ms: float, off_deg: float, no_go_deg: float, sea: float) -> None:
        P = self.P
        hd = math.radians(heading_deg)
        f = (math.sin(hd), -math.cos(hd))
        s = (-f[1], f[0])  # starboard
        pts = [
            (x + f[0] * SHIP_LEN * 0.38, z + f[1] * SHIP_LEN * 0.38),
            (x + f[0] * SHIP_LEN * 0.10 + s[0] * SHIP_BEAM * 0.5, z + f[1] * SHIP_LEN * 0.10 + s[1] * SHIP_BEAM * 0.5),
            (x + f[0] * SHIP_LEN * 0.10 - s[0] * SHIP_BEAM * 0.5, z + f[1] * SHIP_LEN * 0.10 - s[1] * SHIP_BEAM * 0.5),
            (x - f[0] * SHIP_LEN * 0.38, z - f[1] * SHIP_LEN * 0.38),
            (x, z),
        ]
        hs = [wave_height(b, p[0], p[1], t) for p in pts]
        hb, hst, hpt, hsn, hc = hs
        follow = P["motion.wave_follow"]
        pitch_t = math.atan((hb - hsn) / (SHIP_LEN * 0.76)) * follow
        roll_t = math.atan((hpt - hst) / SHIP_BEAM) * follow
        heave_t = (hb + hst + hpt + hsn + hc) / 5.0 * follow
        side = wind_to[0] * s[0] + wind_to[1] * s[1]
        drive = clamp((off_deg - no_go_deg * 0.9) / 20.0, 0.0, 1.0)
        heel = math.radians(P["motion.heel_deg_per_ms2"] * wind_ms * wind_ms * side * drive)
        self.roll, self.roll_v = spring(self.roll, self.roll_v, roll_t + heel, P["motion.roll_period_s"], P["motion.damping"], dt)
        self.pitch, self.pitch_v = spring(self.pitch, self.pitch_v, pitch_t, P["motion.pitch_period_s"], P["motion.damping"], dt)
        self.heave, self.heave_v = spring(self.heave, self.heave_v, heave_t, P["motion.heave_period_s"], P["motion.damping"], dt)
        self.events = []
        self.slam *= math.exp(-dt / 0.7)
        for i in range(3):
            self.cool[i] = max(self.cool[i] - dt, 0.0)
        if self.prev is not None and dt > 0.0 and sea >= P["motion.slam_min_sea"]:
            cd = P["motion.slam_cooldown_calm_s"] + (P["motion.slam_cooldown_gale_s"] - P["motion.slam_cooldown_calm_s"]) * sea
            thr = [P["motion.slam_bow_ms"], P["motion.slam_side_ms"], P["motion.slam_side_ms"]]
            for i in range(3):
                vrel = (hs[i] - self.prev[i]) / dt
                if vrel > thr[i] and self.cool[i] <= 0.0:
                    power = clamp((vrel - thr[i]) / 9.0, 0.25, 1.0) * (0.5 + 0.5 * sea)
                    self.events.append((i, power))
                    self.cool[i] = cd
                    self.slam = max(self.slam, power if i == 0 else 0.5 * power)
        self.prev = hs[:3]

    def out(self) -> dict[str, float]:
        P = self.P
        g = P["motion.gain"]
        return {"roll_deg": soft_limit(math.degrees(self.roll), P["motion.roll_max_deg"]) * g,
                "pitch_deg": soft_limit(math.degrees(self.pitch), P["motion.pitch_max_deg"]) * g,
                "heave_m": soft_limit(self.heave, P["motion.heave_max_m"]) * g}


PRESETS = {
    "calm": dict(wind_kn=4.0, wave_m=0.35, rain=0.0, storm=0.0, fog=0.05),
    "breezy": dict(wind_kn=14.0, wave_m=1.4, rain=0.0, storm=0.0, fog=0.05),
    "rough": dict(wind_kn=24.0, wave_m=3.4, rain=0.35, storm=0.25, fog=0.10),
    "gale": dict(wind_kn=36.0, wave_m=6.0, rain=0.8, storm=0.7, fog=0.15),
    "storm": dict(wind_kn=48.0, wave_m=9.5, rain=1.0, storm=1.0, fog=0.2),
}


def target(name: str, wind_from: float = 225.0) -> dict[str, float]:
    d = dict(PRESETS[name])
    d["wind_from_deg"] = wind_from
    return d


def simulate_ship(env: Env, mot: Motion, seconds: float, heading: float, speed_ms: float, off_deg: float, t0: float = 0.0):
    P = env.P
    dt = 1.0 / 60.0
    x, z = 0.0, 0.0
    hd = math.radians(heading)
    f = (math.sin(hd), -math.cos(hd))
    rolls, pitches, heaves, slams = [], [], [], 0
    t = t0
    for i in range(int(seconds / dt)):
        t += dt
        env.step(dt, env_target[0], t)
        b = wave_build(env.wave_vis_m, env.wave_to, env.sea, 0.0, P)
        x += f[0] * speed_ms * dt
        z += f[1] * speed_ms * dt
        wt = vec_to(env.wind_from_inst + 180.0)
        mot.step(dt, b, x, z, heading, t, wt, env.wind_inst_kn * KN_TO_MS, off_deg, 40.0, env.sea)
        o = mot.out()
        rolls.append(o["roll_deg"]); pitches.append(o["pitch_deg"]); heaves.append(o["heave_m"])
        slams += len(mot.events)
    return rolls, pitches, heaves, slams


env_target = [None]


def report() -> None:
    P = load_params()
    print("sea states at steady state (ship 5 kn = 24.7 scene m/s; wind from 225, waves travel to 45):")
    for name in PRESETS:
        for hdg, label in ((0.0, "heading N (waves from the stern-quarter... wind 225 = SW)"), (90.0, "heading E"), (225.0, "into the wind/waves")):
            e = Env(P)
            e.snap(target(name))
            env_target[0] = target(name)
            m = Motion(P)
            off = abs(wrap180(hdg - 225.0))
            r, p, h, sl = simulate_ship(e, m, 40.0, hdg, 24.7, off, 100.0)
            r, p, h = r[600:], p[600:], h[600:]
            print(f"  {name:7s} sea {e.sea:.2f} {e.sea_name():6s} hdg {hdg:5.0f} off {off:5.0f}: roll {min(r):+5.1f}..{max(r):+5.1f} pitch {min(p):+5.1f}..{max(p):+5.1f} heave {min(h):+4.1f}..{max(h):+4.1f} slams/40s {sl}")
    print("transition calm -> gale (waves 0.35 m -> 6 m), seconds after the change:")
    e = Env(P)
    e.snap(target("calm"))
    env_target[0] = target("gale")
    t = 0.0
    for sec in (0, 5, 10, 20, 30, 45, 60, 90):
        while t < sec:
            t += 1 / 60
            e.step(1 / 60, env_target[0], t)
        print(f"  t={sec:3d}s wind {e.wind_kn:4.1f} kn wave {e.wave_m:4.2f} m sea {e.sea:.2f} {e.sea_name():6s} rain {e.rain:.2f} vis {e.visibility_km:5.2f} km")
    print("gusts: fraction of time with gust > 0.3 and peak, mean wind 14 kn / 26 kn / 40 kn:")
    for wk in (14.0, 26.0, 40.0):
        gs = [smoothstep(0.60, 0.92, gust_noise(t * 0.05)) * gustiness(wk, 0.3) for t in range(int(600 / 0.05))]
        print(f"  {wk:4.0f} kn: gust>0.3 {sum(1 for g in gs if g > 0.3) / len(gs) * 100:4.1f}% of the time, peak {max(gs):.2f}")


def make_fixture() -> dict:
    P = load_params()
    out: dict = {"params": P, "gust": [], "wave": [], "env": [], "motion": [], "classes": []}
    for t in (0.0, 1.0, 3.7, 8.2, 12.5, 20.0, 33.3, 61.0):
        out["gust"].append({"t": t, "noise": gust_noise(t), "raw": smoothstep(0.60, 0.92, gust_noise(t))})
    for sea in (0.0, 0.1, 0.34, 0.5, 0.64, 0.7, 0.84, 0.9, 1.0):
        out["classes"].append({"sea": sea, "name": sea_class(sea, P)})
    for p in (1.0, 1.8, 2.6):
        out["wave"].append({"p": p, "bias": crest_bias(p)})
    b = wave_build(3.0, 45.0, 0.5, 0.0, P)
    pts = [(0.0, 0.0, 0.0), (13.0, -7.0, 2.5), (-40.0, 22.0, 9.1), (250.0, 80.0, 31.7)]
    out["wave_build"] = {"wave_m": 3.0, "to_deg": 45.0, "sea": 0.5, "ice": 0.0, "p": b["p"], "bias": b["bias"], "waves": b["waves"],
                         "heights": [{"x": x, "z": z, "t": t, "h": wave_height(b, x, z, t)} for x, z, t in pts]}
    # an environment transition replayed at dt = 1/60, sampled every 5 s
    for name_from, name_to, secs in (("calm", "gale", 60), ("storm", "calm", 90)):
        e = Env(P)
        e.snap(target(name_from))
        tg = target(name_to, 200.0)
        samples = []
        t = 0.0
        n = int(secs * 60)
        for i in range(n):
            t += 1.0 / 60.0
            e.step(1.0 / 60.0, tg, t)
            if (i + 1) % 300 == 0:
                samples.append({"t": t, "wind_kn": e.wind_kn, "wave_m": e.wave_m, "wave_to": e.wave_to, "wind_from": e.wind_from,
                                "rain": e.rain, "sea": e.sea, "gust": e.gust, "wind_inst_kn": e.wind_inst_kn,
                                "visibility_km": e.visibility_km, "adv_x": e.adv[0], "adv_z": e.adv[1]})
        out["env"].append({"from": name_from, "to": name_to, "from_target": target(name_from), "to_target": tg, "samples": samples})
    # a ship in a rough sea, 20 s, sampled every 2 s
    e = Env(P)
    e.snap(target("rough"))
    tg = target("rough")
    m = Motion(P)
    t = 50.0
    x = z = 0.0
    hd = 30.0
    f = (math.sin(math.radians(hd)), -math.cos(math.radians(hd)))
    samples = []
    ev = 0
    for i in range(1200):
        t += 1.0 / 60.0
        e.step(1.0 / 60.0, tg, t)
        b2 = wave_build(e.wave_vis_m, e.wave_to, e.sea, 0.0, P)
        x += f[0] * 12.0 / 60.0
        z += f[1] * 12.0 / 60.0
        wt = vec_to(e.wind_from_inst + 180.0)
        m.step(1.0 / 60.0, b2, x, z, hd, t, wt, e.wind_inst_kn * KN_TO_MS, 100.0, 40.0, e.sea)
        ev += len(m.events)
        if (i + 1) % 120 == 0:
            o = m.out()
            samples.append({"t": t, "x": x, "z": z, "roll": o["roll_deg"], "pitch": o["pitch_deg"], "heave": o["heave_m"], "events": ev, "slam": m.slam})
    out["motion"].append({"heading": hd, "speed_ms": 12.0, "off_deg": 100.0, "t0": 50.0, "target": tg, "samples": samples})
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fixture":
        dst = ROOT / "game" / "tests" / "fixtures" / "env_cases.json"
        dst.write_text(json.dumps(make_fixture(), indent=1) + "\n")
        print("wrote", dst)
    elif len(sys.argv) > 1 and sys.argv[1] == "--check":
        dst = ROOT / "game" / "tests" / "fixtures" / "env_cases.json"
        ok = json.loads(dst.read_text()) == json.loads(json.dumps(make_fixture()))
        gd_env = (ROOT / "game" / "h2d" / "env_model.gd").read_text() + (ROOT / "game" / "h2d" / "ship_motion.gd").read_text()
        for key, val in load_params().items():
            if not key.startswith(("env.", "motion.")):
                continue
            short = key.split(".", 1)[1]
            if f'"{short}": {val}' not in gd_env and f'"{short}": {float(val)}' not in gd_env:
                print("GDScript DEFAULTS differ from tuning_env.json for", key)
                ok = False
        print("env fixture + defaults in sync" if ok else "env fixture/defaults OUT OF SYNC: run env_logic.py --fixture")
        sys.exit(0 if ok else 1)
    else:
        report()
