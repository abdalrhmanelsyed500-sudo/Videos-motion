"""DIAGNOSTIC ONLY (H2D-0.3): a numpy re-implementation of rain.gdshader's drop placement and the real camera maths, to
check density, streak length and slant in screen pixels for each weather BEFORE the user runs Godot. It is not a render of
the game: no ocean, no light, no fog, no post-process, and the GPU's hash differs in the last bits. It proves the numbers,
not the look.
  python tools/h2d/rain_preview.py [out_dir]    # writes rain_preview.png and rain_preview.txt"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
T = {r["key"]: r["value"] for r in json.loads((ROOT / "game/data/tuning/tuning_env.json").read_text())["records"]}
W, H = 640, 360
FOV, PITCH, PX_PER_M = 22.0, 48.0, 3.6
FALL_FRAC, KN = 0.60, 0.514444
EFFECTS = {"low": (40, 32, 4.6, 1, 0.9), "medium": (56, 44, 3.4, 2, 0.5), "high": (64, 50, 3.0, 3, 0.32)}


def fract(x):
    return x - np.floor(x)


def hash2(px, py):
    px = fract(px * 123.34)
    py = fract(py * 456.21)
    d = px * (px + 45.32) + py * (py + 45.32)
    px = px + d
    py = py + d
    return fract(px * py)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def noise(px, py):
    ix, iy = np.floor(px), np.floor(py)
    fx, fy = px - ix, py - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = hash2(ix, iy), hash2(ix + 1, iy)
    c, d = hash2(ix, iy + 1), hash2(ix + 1, iy + 1)
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy


class Weather:
    def __init__(self, name, wind_kn, rain, gust, wind_from=270.0):
        self.name, self.wind_kn, self.rain, self.gust = name, wind_kn, rain, gust
        a = math.radians(wind_from + 180.0)
        self.wt = (math.sin(a), -math.cos(a))
        self.adv = (self.wt[0] * wind_kn * KN * 60.0, self.wt[1] * wind_kn * KN * 60.0)


def rain_local(w, x, z):
    n = noise(x * 0.011 - w.adv[0] * 0.011, z * 0.011 - w.adv[1] * 0.011)
    r = np.clip((w.rain - 0.55 * (1 - n) * (1 - 0.9 * w.rain)) * 1.25, 0, 1)
    sheet = 0.55 + 0.7 * noise(x * 0.028 - w.adv[0] * 0.028 + 71.0, z * 0.028 - w.adv[1] * 0.028 + 71.0)
    r = np.clip(r * (1 + (sheet - 1) * smooth(0.45, 0.85, w.rain)), 0, 1)
    return r ** 0.75


def gust_field(w, x, z, focus):
    if w.gust < 0.02:
        return np.zeros_like(x)
    d = np.hypot(x - focus[0], z - focus[1])
    thr = (0.80 + (0.45 - 0.80) * w.gust) - 0.25 * (1 - smooth(10, 70, d))
    return smooth(thr, thr + 0.22, noise(x * 0.02 - w.adv[0] * 0.02, z * 0.02 - w.adv[1] * 0.02)) * w.gust


def project(P, cam, f, r, u):
    d = P - cam
    z = d @ f
    x = d @ r
    y = d @ u
    th = math.tan(math.radians(FOV / 2))
    return np.stack([W / 2 + x / z / (th * W / H) * W / 2, H / 2 - y / z / th * H / 2, z], axis=-1)


def render(w: Weather, level: str, t: float = 37.3):
    gx, gz, cell_m, K, dens0 = EFFECTS[level]
    dens = dens0 * T["look.rain_density"]
    p = math.radians(PITCH)
    dist = H / (2 * math.tan(math.radians(FOV / 2)) * PX_PER_M)
    ship = np.array([0.0, 0.0])
    target = np.array([0.0, 0.0, -9.0])
    cam = target + np.array([0.0, dist * math.sin(p), dist * math.cos(p)])
    f = np.array([0.0, -math.sin(p), -math.cos(p)])
    r = np.array([1.0, 0.0, 0.0])
    u = np.array([0.0, math.cos(p), -math.sin(p)])
    k_i = min(max(w.rain, 0), 1)
    fall_ms = T["look.rain_fall_ms"] * (0.85 + 0.3 * k_i)
    streak_m = T["look.rain_streak_m"] * (0.5 + 0.5 * k_i)
    alpha = 0.55 + 0.35 * k_i
    drift = np.array(w.wt) * min(w.wind_kn * KN * T["look.rain_drift_factor"] * (0.5 + 0.5 * k_i), 12.0)
    focus = ship + np.array([0.0, -9.0])
    center = focus + np.array([0.0, 14.0]) + drift * 0.6
    base = np.array([math.floor(center[0] / cell_m) - gx * 0.5, math.floor(center[1] / cell_m) - gz * 0.5])
    ix, iz = np.meshgrid(np.arange(gx), np.arange(gz))
    img = Image.new("RGB", (W, H), (60, 78, 92))
    dr = ImageDraw.Draw(img)
    n_vis, lens, slants = 0, [], []
    for k in range(K):
        cx = base[0] + ix.astype(float)
        cz = base[1] + iz.astype(float)
        period = 1.25 + 0.65 * hash2(cx * 0.91 + k * 5.3 + 9.0, cz * 0.91 + k * 5.3 + 9.0)
        phase = hash2(cx * 0.37 + k * 3.7 + 3.0, cz * 0.37 + k * 3.7 + 3.0)
        tt = t / period + phase
        cyc = np.floor(tt)
        uu = tt - cyc
        seed = k + 3.0 * np.mod(cyc, 61.0)
        on_h = hash2(cx + seed * 9.1 + 29.0, cz + seed * 9.1 + 29.0)
        loc = rain_local(w, (cx + 0.5) * cell_m, (cz + 0.5) * cell_m) * dens
        on = on_h <= loc
        jx = hash2(cx + seed * 7.31, cz + seed * 7.31)
        jz = hash2(cz * 1.7 + seed * 5.17 + 11.0, cx * 1.7 + seed * 5.17 + 11.0)
        impx = (cx + 0.25 + 0.5 * jx) * cell_m
        impz = (cz + 0.25 + 0.5 * jz) * cell_m
        dv = hash2(cx * 1.31 + seed * 2.9 + 61.0, cz * 1.31 + seed * 2.9 + 61.0)
        falling = (uu <= FALL_FRAC) & on
        ft = np.clip(uu / FALL_FRAC, 0, 1)
        tau = (1 - ft) * period * FALL_FRAC
        fall = fall_ms * (0.88 + 0.24 * dv)
        gf = gust_field(w, impx, impz, focus)
        e0 = noise(impx * 0.03 - w.adv[0] * 0.03, impz * 0.03 - w.adv[1] * 0.03) - 0.5
        e1 = noise(impx * 0.03 + 37 - w.adv[0] * 0.03, impz * 0.03 + 37 - w.adv[1] * 0.03) - 0.5
        sp = np.hypot(*drift)
        dx = drift[0] * (1 + T["look.rain_gust_bend"] * gf) + e0 * sp * 0.6
        dz = drift[1] * (1 + T["look.rain_gust_bend"] * gf) + e1 * sp * 0.6
        spd = np.hypot(fall, np.hypot(dx, dz))
        tau2 = tau + streak_m * (0.7 + 0.6 * dv) / spd
        hd = np.stack([impx - dx * tau, fall * tau, impz - dz * tau], -1)
        tl = np.stack([impx - dx * tau2, fall * tau2, impz - dz * tau2], -1)
        ph, pt = project(hd, cam, f, r, u), project(tl, cam, f, r, u)
        for j in np.argwhere(falling):
            a, b = ph[j[0], j[1]], pt[j[0], j[1]]
            if not (-5 < a[0] < W + 5 and -5 < a[1] < H + 5):
                continue
            n_vis += 1
            lens.append(math.hypot(a[0] - b[0], a[1] - b[1]))
            slants.append(math.degrees(math.atan2(b[0] - a[0], abs(b[1] - a[1]) + 1e-6)))
            bright = 1.0 if dv[j[0], j[1]] > 0.7 else 0.62
            head = tuple(int(c) for c in (np.array([188, 214, 240]) * bright * alpha + np.array([60, 78, 92]) * (1 - bright * alpha)))
            tail = tuple(int(c) for c in (np.array([188, 214, 240]) * bright * alpha * 0.42 + np.array([60, 78, 92]) * (1 - bright * alpha * 0.42)))
            mid = (a[0] + (b[0] - a[0]) * 0.3, a[1] + (b[1] - a[1]) * 0.3)
            dr.line([a[0], a[1], mid[0], mid[1]], fill=head, width=1)
            dr.line([mid[0], mid[1], b[0], b[1]], fill=tail, width=1)
    area = gx * cell_m * gz * cell_m
    return img, {"drops_on_screen": n_vis, "mean_len_px": float(np.mean(lens)) if lens else 0.0,
                 "mean_slant_deg": float(np.mean(slants)) if slants else 0.0, "slant_spread_deg": float(np.std(slants)) if slants else 0.0,
                 "screen_coverage_pct": 100.0 * n_vis * (float(np.mean(lens)) if lens else 0.0) * 1.4 / (W * H), "grid_area_m2": area}


WEATHERS = [Weather("drizzle (rain 0.2, 8 kn)", 8.0, 0.2, 0.0), Weather("steady rain (0.5, 14 kn)", 14.0, 0.5, 0.2),
            Weather("downpour (0.8, 24 kn, gust 0.6)", 24.0, 0.8, 0.6), Weather("gale rain (0.8, 36 kn, gust 0.9)", 36.0, 0.8, 0.9)]


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "build"
    out.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (W * 2, H * 2))
    lines = ["DIAGNOSTIC ONLY: numpy emulation of the rain drop placement and camera, not a Godot render.",
             f"ship-to-camera {H / (2 * math.tan(math.radians(FOV / 2)) * PX_PER_M):.0f} scene m; art grid {W}x{H}", ""]
    for i, w in enumerate(WEATHERS):
        img, st = render(w, "medium")
        sheet.paste(img, ((i % 2) * W, (i // 2) * H))
        lines.append(f"{w.name:36s} drops on screen {st['drops_on_screen']:5d}  length {st['mean_len_px']:4.1f} px  slant {st['mean_slant_deg']:+5.1f} deg (spread {st['slant_spread_deg']:.1f})  coverage {st['screen_coverage_pct']:.1f}% of pixels")
    for lvl in ("low", "medium", "high"):
        _, st = render(WEATHERS[2], lvl)
        lines.append(f"downpour at effects {lvl:6s}: drops on screen {st['drops_on_screen']:5d} coverage {st['screen_coverage_pct']:.1f}%")
    sheet.save(out / "rain_preview.png")
    (out / "rain_preview.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
