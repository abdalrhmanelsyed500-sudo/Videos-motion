"""LOOK LAB (Modules A3/A4): renders HD-2D stills of the intended final look WITHOUT a GPU.

    /home/user/.venv/bin/python tools/looklab/looklab.py [out_dir]

* Ground is ray-cast through a real pinhole camera (FOV 22 deg, pitch 39 deg land / 48 deg sea) so tiles foreshorten like in the game.
* Sprites are upright billboards scaled by depth, shaded by the same key-light model as the Art Bible.
* Post-process (tilt-shift, bloom, grade, vignette, fog, shafts) reads game/data/look/look_profiles.json: the SAME numbers the Godot shader will use.
* It APPROXIMATES the shader (Gaussian levels instead of the 12-tap golden-angle disc); it is a look target, not a pixel-exact emulation.
* Content is PLACEHOLDER art (mannequins etc.). It proves the lighting/atmosphere pipeline, not final art quality.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PH = ROOT / "game" / "art" / "placeholder"
MAN = json.loads((ROOT / "game" / "art" / "manifest" / "sprites.json").read_text())["assets"]
LOOK = json.loads((ROOT / "game" / "data" / "look" / "look_profiles.json").read_text())
PAL = json.loads((ROOT / "game" / "data" / "look" / "palette.json").read_text())
RAMPS = {k: np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in v], dtype=np.uint8) for k, v in PAL["ramps"].items()}
W, H = LOOK["art_grid"]
VFOV = math.radians(LOOK["camera"]["fov_deg"])
F = (H / 2) / math.tan(VFOV / 2)


def hexf(h: str) -> np.ndarray:
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=float) / 255.0


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ camera
class Cam:
    def __init__(self, pitch_deg: float, px_per_m: float, target=(0.0, 0.0)):
        th = math.radians(pitch_deg)
        self.D = F / px_per_m
        self.fwd = np.array([0, -math.sin(th), math.cos(th)])
        self.right = np.array([1.0, 0, 0])
        self.up = np.array([0, math.cos(th), math.sin(th)])
        self.pos = np.array([target[0], 0, target[1]]) - self.fwd * self.D
        self.ppm = px_per_m

    def ground(self):
        """world X,Z of every screen pixel (ray cast onto y=0)."""
        yy, xx = np.mgrid[0:H, 0:W]
        sx, sy = (xx + 0.5 - W / 2) / F, (yy + 0.5 - H / 2) / F
        d = self.fwd[None, None, :] + sx[..., None] * self.right - sy[..., None] * self.up
        t = -self.pos[1] / d[..., 1]
        return self.pos[0] + t * d[..., 0], self.pos[2] + t * d[..., 2], t

    def project(self, X, Y, Z):
        v = np.array([X, Y, Z]) - self.pos
        zc = v @ self.fwd
        return W / 2 + F * (v @ self.right) / zc, H / 2 - F * (v @ self.up) / zc, zc


# ------------------------------------------------------------------ assets
_cache: dict = {}


def img(aid: str) -> np.ndarray:
    if aid not in _cache:
        e = MAN[aid]
        _cache[aid] = np.asarray(Image.open(PH / e["category"] / f"{aid}.png").convert("RGBA"))
    return _cache[aid]


def frame(aid: str, col=0, row=0) -> np.ndarray:
    e = MAN[aid]
    a = img(aid)
    if e["kind"] == "character_sheet":
        cw, ch = e["cell"]
        return a[row * ch:(row + 1) * ch, col * cw:(col + 1) * cw]
    if e.get("frames", 1) > 1:
        w = e["size"][0]
        return a[:, col * w:(col + 1) * w]
    return a


def swap_ramp(tile: np.ndarray, src: str, dst: str) -> np.ndarray:
    out = tile.copy()
    for i in range(5):
        m = np.all(tile[..., :3] == RAMPS[src][i], axis=2)
        out[m, :3] = RAMPS[dst][i]
    return out


def sample_tile(tile: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
    n = tile.shape[0]
    iu = np.floor((u % 1.0) * n).astype(int) % n
    iv = np.floor((v % 1.0) * n).astype(int) % n
    return tile[iv, iu, :3]


# ------------------------------------------------------------------ scene
class Scene:
    def __init__(self, cam: Cam, ground_fn):
        self.cam = cam
        self.alb = np.zeros((H, W, 3), dtype=np.uint8)
        self.emis = np.zeros((H, W), dtype=bool)
        self.shadow = np.zeros((H, W), dtype=float)
        self.lights: list[tuple[float, float, float, np.ndarray, float]] = []  # sx, sy, radius_px, rgb, intensity
        self.sprites: list = []
        self.X, self.Z, self.T = cam.ground()
        self.alb[:] = ground_fn(self.X, self.Z)

    def add(self, aid: str, X: float, Z: float, col=0, row=0, scale=1.0, flip=False, Y=0.0):
        self.sprites.append((Z, aid, X, col, row, scale, flip, Y))

    def light(self, X: float, Z: float, Y: float, radius_m: float, rgb: str, intensity: float):
        sx, sy, zc = self.cam.project(X, Y, Z)
        self.lights.append((sx, sy, radius_m * F / zc * 0.75, hexf(rgb), intensity))

    def render_sprites(self):
        ppm_base = self.cam.ppm
        for Z, aid, X, col, row, scale, flip, Y in sorted(self.sprites, key=lambda s: -s[0]):
            e = MAN[aid]
            fr = frame(aid, col, row)
            if flip:
                fr = fr[:, ::-1]
            px, py, zc = self.cam.project(X, Y, Z)
            s = F / zc / MAN[aid]["px_per_m"] * scale if e["px_per_m"] else F / zc / 24 * scale
            h0, w0 = fr.shape[:2]
            nh, nw = max(1, int(round(h0 * s))), max(1, int(round(w0 * s)))
            ys = np.minimum((np.arange(nh) / s).astype(int), h0 - 1)
            xs = np.minimum((np.arange(nw) / s).astype(int), w0 - 1)
            sp = fr[np.ix_(ys, xs)]
            pv = e.get("pivot", [w0 // 2, h0 - 2])
            ox, oy = int(round(px - pv[0] * s)), int(round(py - pv[1] * s))
            # cast shadow (sheared alpha towards bottom-right, away from the top-left key light)
            a = sp[..., 3] > 0
            yy, xx = np.nonzero(a)
            hg = (pv[1] * s - yy).clip(0)
            sxs = (ox + xx + 0.55 * hg).round().astype(int)
            sys_ = (oy + pv[1] * s + 0.16 * hg + 0 * yy).round().astype(int)
            ok = (sxs >= 0) & (sxs < W) & (sys_ >= 0) & (sys_ < H)
            self.shadow[sys_[ok], sxs[ok]] = np.maximum(self.shadow[sys_[ok], sxs[ok]], 1.0)
            # blit
            y0, y1, x0, x1 = max(0, oy), min(H, oy + nh), max(0, ox), min(W, ox + nw)
            if y0 >= y1 or x0 >= x1:
                continue
            s2 = sp[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
            m = s2[..., 3] > 0
            self.alb[y0:y1, x0:x1][m] = s2[..., :3][m]
            fire = np.zeros(m.shape, bool)
            for k in (2, 3, 4):
                fire |= np.all(s2[..., :3] == RAMPS["fire"][k], axis=2)
            em = self.emis[y0:y1, x0:x1]
            em[m] = fire[m]


# ------------------------------------------------------------------ post pipeline
def render(scene: Scene, mood: str, profile: str, out_h: int, extras: dict | None = None) -> np.ndarray:
    P = LOOK["profiles"][profile]
    M = LOOK["moods"][mood]
    extras = extras or {}
    k = max(1, int(round(out_h / H))) if P["internal"] == "window" else 1
    key, amb = hexf(M["key"]), hexf(M["ambient"])
    lvl = M["ambient_level"]
    ys = np.arange(H)[:, None]
    # ---- lighting at art-grid resolution
    sh = scene.shadow
    if not P["shadows"]:
        sh = np.zeros_like(sh)
    else:
        sh = ndi.gaussian_filter(sh, 0.7)
    L = amb[None, None, :] * lvl * 1.5 + key[None, None, :] * (1 - lvl) * 1.4 * (1 - 0.85 * sh)[..., None]
    yy, xx = np.mgrid[0:H, 0:W]
    for sx, sy, r, rgb, inten in scene.lights:
        d = np.hypot(xx - sx, (yy - sy) * 1.6) / max(r, 1)
        L += rgb[None, None, :] * (inten * np.exp(-d * d * 1.8))[..., None]
    rgb = scene.alb.astype(float) / 255.0 * L * M["exposure"]
    em = scene.emis[..., None]
    rgb = np.where(em, np.maximum(rgb, scene.alb / 255.0 * 1.25), rgb)
    # ---- depth fog (more at the top = further)
    fog_col = key * 0.55 + amb * 0.45
    fog = P["fog"]["far_density"] * (1 - ys / H) ** 1.6 * (0.5 + 0.5 * (mood != "night_fire"))
    rgb = rgb * (1 - fog[..., None]) + (fog_col * L.mean() * 0.8)[None, None, :] * fog[..., None] if np.ndim(fog) else rgb
    # ---- up-res: albedo+light already combined at art grid; bilinear would blur the pixel art, so repeat nearest
    big = np.repeat(np.repeat(rgb, k, 0), k, 1) if k > 1 else rgb
    oh, ow = big.shape[:2]
    # light shafts (standard only): soft diagonal additive bands
    if P["shafts"]:
        gy, gx = np.mgrid[0:oh, 0:ow]
        u = (gx / ow) + 0.55 * (gy / oh)
        s = np.zeros((oh, ow))
        for u0, wd, a in ((0.25, 0.05, 0.9), (0.55, 0.035, 0.7), (0.9, 0.06, 1.0), (1.25, 0.04, 0.6)):
            s += a * np.exp(-((u - u0) / wd) ** 2)
        s *= np.clip(1 - gy / oh, 0, 1) ** 0.8 * (1 - 0.4 * np.clip(gy / oh, 0, 1))
        big = big + key[None, None, :] * (0.13 * extras.get("shaft_gain", 1.0) * s)[..., None]
    if extras.get("rain"):
        rng = np.random.default_rng(5)
        gy, gx = np.mgrid[0:oh, 0:ow]
        layer = np.zeros((oh, ow))
        for _ in range(int(900 * (oh / 1080))):
            x0, y0 = rng.integers(0, ow), rng.integers(0, oh)
            ln = int(rng.integers(10, 26) * oh / 1080)
            for t in range(ln):
                xx_, yy_ = x0 - t // 3, y0 + t
                if 0 <= xx_ < ow and 0 <= yy_ < oh:
                    layer[yy_, xx_] = 0.5 * (1 - t / ln)
        big = big + (np.array([0.6, 0.7, 0.8]) * layer[..., None]) * 0.5
    if extras.get("dust"):
        rng = np.random.default_rng(3)
        n = 70
        for _ in range(n):
            x0, y0 = int(rng.integers(0, ow)), int(rng.integers(int(oh * 0.15), int(oh * 0.85)))
            r = max(1, int(oh / 540))
            big[y0:y0 + r, x0:x0 + r] += key * 0.5
    # ---- tilt shift (rows get Gaussian levels; strength in px at 1080, scaled to this height)
    ts = P["tilt_shift"]
    strength = extras.get("tilt_strength", 1.0)
    maxb = ts["max_blur_px"] * oh / 1080.0 * strength
    if maxb > 0.3:
        fy = np.arange(oh) / oh
        r = maxb * smoothstep(0, 1, np.clip((np.abs(fy - ts["focus_y"]) - ts["focus_half_width"]) / ts["ramp_width"], 0, 1))
        sig = r * 0.5
        levels = np.linspace(0, sig.max(), ts["taps"] // 2 + 1)
        stack = [big] + [ndi.gaussian_filter(big, (s, s, 0), mode="nearest") for s in levels[1:]]
        out = np.empty_like(big)
        pos = np.interp(sig, levels, np.arange(len(levels)))
        for y in range(oh):
            i0 = int(math.floor(pos[y]))
            i1 = min(i0 + 1, len(levels) - 1)
            f = pos[y] - i0
            out[y] = stack[i0][y] * (1 - f) + stack[i1][y] * f
        big = out
    # ---- bloom (LDR glow, lowered threshold)
    bl = P["bloom"]
    if bl["intensity"] > 0:
        lum = big @ np.array([0.2126, 0.7152, 0.0722])
        bright = np.clip((lum - bl["threshold"]) / (1 - bl["threshold"] + 1e-6), 0, 1)[..., None] * big
        g = ndi.gaussian_filter(bright, (bl["radius_px"] * oh / 1080.0, bl["radius_px"] * oh / 1080.0, 0))
        g2 = ndi.gaussian_filter(bright, (bl["radius_px"] * 2.6 * oh / 1080.0, bl["radius_px"] * 2.6 * oh / 1080.0, 0))
        big = big + bl["intensity"] * (g + 0.6 * g2)
    # ---- grade
    gr = dict(P["grade"])
    sg = LOOK["state_grades"][extras.get("state", "well")]
    gr["saturation"] *= sg["sat_mul"]
    gr["contrast"] *= sg["contrast_mul"]
    big = np.clip(big, 0, 1.5)
    lum = (big @ np.array([0.2126, 0.7152, 0.0722]))[..., None]
    big = lum + (big - lum) * gr["saturation"]
    big = (big - 0.5) * gr["contrast"] + 0.5
    lift = hexf(gr["shadow_lift_colour"]) * 1.0 * gr["shadow_lift"] / 0.1
    big = big + lift * (1 - np.clip(lum, 0, 1)) ** 2
    big = np.clip(big, 0, 1) ** (1.0 / gr["gamma"])
    # ---- vignette
    gy, gx = np.mgrid[0:oh, 0:ow]
    d = np.hypot((gx / ow - 0.5) * 2, (gy / oh - 0.5) * 2) / math.sqrt(2) * 1.0
    vg = P["vignette"]
    vig = 1 - vg["strength"] * extras.get("vig_gain", 1.0) * smoothstep(vg["inner"], vg["outer"], d)
    vig = vig - sg["vig_add"] * smoothstep(0.35, 1.05, d)
    big = big * np.clip(vig, 0, 1)[..., None] * hexf(sg["tint"])[None, None, :]
    if P["internal"] != "window" and out_h > oh:  # Dev-Lite: nearest upscale to the window
        kk = out_h // oh
        big = np.repeat(np.repeat(big, kk, 0), kk, 1)
    return (np.clip(big, 0, 1) * 255 + 0.5).astype(np.uint8)


# ------------------------------------------------------------------ stats vs references
def stats(a: np.ndarray) -> dict:
    f = a.astype(float) / 255
    lum = f @ np.array([0.2126, 0.7152, 0.0722])
    mx, mn = f.max(2), f.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    h, w = lum.shape
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) / math.sqrt(2)
    # compare at a common ~560 px scale like the references
    s = 560.0 / w
    lm = ndi.zoom(lum, s, order=1)
    lap = ndi.laplace(ndi.gaussian_filter(lm, 0.6))
    hh = lap.shape[0]
    bands = [float(lap[int(hh * i / 10):int(hh * (i + 1) / 10)].var() * 1e4) for i in range(10)]
    ctr = max(bands)
    return {
        "mean_sat": round(float(sat.mean()), 3),
        "lum_p1": round(float(np.percentile(lum, 1)), 3),
        "lum_p50": round(float(np.percentile(lum, 50)), 3),
        "edge_over_centre_lum": round(float(lum[d > 0.9].mean() / lum[d < 0.3].mean()), 3),
        "sharp_edge_over_peak": round(float(np.mean([bands[0], bands[-1]]) / ctr), 3),
        "sharp_peak_band": int(np.argmax(bands)),
        "RB_shadow": round(float(f[lum < np.percentile(lum, 20)][:, 0].mean() / max(f[lum < np.percentile(lum, 20)][:, 2].mean(), 1e-3)), 2),
    }


# ------------------------------------------------------------------ scenes
def ground_island(kind: str):
    sand = img("til_sand_a")[..., :3]
    grass = img("til_grass_a")[..., :3]
    dirt = img("til_dirt_a")[..., :3]
    cob = img("til_cobble_a")[..., :3]
    plank = img("til_deck_planks_a")[..., :3]
    snow = img("til_snow_a")[..., :3]
    water = frame("til_water_deep_a", 0)[..., :3]
    lagoon = swap_ramp(np.dstack([water, np.full(water.shape[:2], 255, np.uint8)]), "sea_deep", "lagoon")[..., :3]
    rng = np.random.default_rng(11)
    wob = ndi.gaussian_filter(rng.random((64, 64)), 3)
    wob = (wob - wob.mean()) / wob.std()

    def fn(X, Z):
        n = ndi.map_coordinates(wob, [(Z * 1.3 + 32) % 64, (X * 1.3 + 32) % 64], order=1, mode="wrap")
        base = snow if kind == "frozen" else sand
        out = sample_tile(base, X / 2, Z / 2)
        if kind != "frozen":
            gm = (X < -2 + 2.2 * n - 0.15 * Z) & (Z > -1)
            out = np.where(gm[..., None], sample_tile(grass, X / 2, Z / 2), out)
        dm = np.hypot(X, (Z + 0.2) * 1.2) < 3.4 + 0.5 * n
        out = np.where(dm[..., None], sample_tile(dirt, X / 2, Z / 2), out)
        pm = (np.abs(X + 4.6 + 0.2 * n) < 0.9) & (Z > -0.5) & (Z < 4.5) | (np.abs(Z - 4.0) < 0.9) & (X < -3.5) & (X > -10)
        out = np.where(pm[..., None], sample_tile(cob, X / 2, Z / 2), out)
        shore = 8.4 + 1.1 * np.sin(X * 0.45) + 0.6 * n
        sea = Z > shore
        wat = sample_tile(water, X / 2, Z / 2)
        lag = sample_tile(lagoon, X / 2, Z / 2)
        shallow = (Z > shore) & (Z < shore + 1.6 + 0.4 * n)
        out = np.where(sea[..., None], np.where(shallow[..., None], lag, wat), out)
        foam = (np.abs(Z - shore) < 0.22) & (n > -0.4)
        out = np.where(foam[..., None], RAMPS["lagoon"][4][None, None, :], out)
        pier = (X > 7.0) & (X < 10.0) & (Z > 4.5) & (Z < 12.5)
        out = np.where(pier[..., None], sample_tile(plank, (X - 7) / 2, Z / 2 + 0.0), out)
        return out.astype(np.uint8)
    return fn


def ground_sea():
    water = frame("til_water_deep_a", 0)[..., :3]
    return lambda X, Z: sample_tile(water, X / 4, Z / 4).astype(np.uint8)


def build_camp(kind: str) -> Scene:
    cam = Cam(LOOK["camera"]["pitch_deg"], 24, (0, 1.0))
    sc = Scene(cam, ground_island(kind))
    if kind != "frozen":
        sc.add("prp_palm_b", 12.5, 6.0)
        sc.add("prp_palm_b", -13.0, 6.5)
        sc.add("prp_palm_a", 3.2, 5.6)
        sc.add("prp_palm_a", -2.5, 6.2, flip=True)
        sc.add("prp_palm_a", 10.0, -3.0, flip=True)
    sc.add("prp_hut_a", -9.5, 3.0, scale=1.0)
    sc.add("prp_campfire", 0.0, -0.4, col=0)
    idle = [("spr_crew_mannequin_captain", -2.6, -2.5, 0, 0), ("spr_crew_mannequin_sailor", 2.6, -1.9, 1, 3),
            ("spr_crew_mannequin_gunner", 0.2, 1.8, 2, 1), ("spr_npc_mannequin_villager", -4.4, -0.2, 0, 2),
            ("spr_crew_mannequin_sailor", 3.8, 1.6, 3, 2)]
    for aid, x, z, f, r in idle:
        sc.add(aid, x, z, col=f, row=r)
    sc.add("prp_barrel", -6.3, -1.6)
    sc.add("prp_barrel", -5.5, -2.4)
    sc.add("prp_crate", -7.6, -3.4)
    sc.add("prp_chest_closed", 5.6, -3.2)
    sc.add("prp_rock_a", 9.0, -4.6)
    sc.add("prp_rock_a", -12.0, -2.0, flip=True)
    sc.add("prp_lantern", -5.3, 1.3)
    sc.add("prp_cannon", 3.0, -5.6)
    if kind != "frozen":
        sc.add("shp_sloop_e", -3.0, 11.8, scale=0.5)
    sc.light(0.0, -0.4, 0.8, 9.0, "#ffa43a", 1.5 if kind == "night" else 0.55)
    sc.light(-5.3, 1.3, 0.8, 4.0, "#ffa43a", 0.9 if kind == "night" else 0.25)
    sc.light(-8.4, 2.0, 1.0, 3.0, "#ffa43a", 0.8 if kind == "night" else 0.0)
    sc.render_sprites()
    return sc


def build_sea() -> Scene:
    cam = Cam(LOOK["camera"]["pitch_sea_deg"], 12, (0, 0))
    sc = Scene(cam, ground_sea())
    sc.add("shp_sloop_e", 0.0, -3.0)
    sc.render_sprites()
    return sc


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "art_bible" / "looklab_stills"
    out.mkdir(parents=True, exist_ok=True)
    jobs = [
        ("still_beach_golden_standard", lambda: build_camp("beach"), "golden_hour", "standard", 1080, {"dust": True, "tilt_strength": 1.0, "shaft_gain": 2.4}),
        ("still_beach_golden_devlite", lambda: build_camp("beach"), "golden_hour", "dev_lite", 720, {}),
        ("still_beach_golden_starving", lambda: build_camp("beach"), "golden_hour", "standard", 1080, {"dust": True, "shaft_gain": 2.4, "state": "starving"}),
        ("still_camp_night_standard", lambda: build_camp("night"), "night_fire", "standard", 1080, {"dust": True, "shaft_gain": 0.0, "bloom_gain": 1.0, "tilt_strength": 1.0}),
        ("still_frozen_dawn_standard", lambda: build_camp("frozen"), "frozen_dawn", "standard", 1080, {"shaft_gain": 0.8, "tilt_strength": 0.8}),
        ("still_sea_storm_standard", build_sea, "storm", "standard", 1080, {"rain": True, "shaft_gain": 0.0, "vig_gain": 1.2}),
    ]
    rep = {}
    for name, mk, mood, prof, oh, ex in jobs:
        a = render(mk(), mood, prof, oh, ex)
        Image.fromarray(a).save(out / f"{name}.png", optimize=True)
        rep[name] = stats(a)
        print(name, a.shape, rep[name])
    (out / "stats.json").write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
