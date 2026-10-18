"""The ocean model (Module E1): where you are, what the sea and sky are doing there, and what that does to a ship.
GDScript twin: game/core/ocean.gd. Both are run against game/tests/fixtures/ocean_cases.json.

EVERYTHING here is a pure function of (x_km, y_km, t_days) and the data files. There is no random-number state and no
stored world: the same place at the same time is always the same sea, so a saved game needs only the clock, a loaded game
cannot re-roll the weather, and the whole world costs no memory. Weather is smooth noise carried along by the wind, so
systems form, drift, mature and fade (they are not re-picked every few seconds), and the Herald Swell (a swell that
arrives one game day before the weather that made it) is simply the same function asked about tomorrow.

Units: km, game days (t_days, fraction = time of day, 0.25 = 06:00), knots, metres, degrees C, degrees (compass, 0 = north,
90 = east). The map has y growing SOUTHWARD: y = 0 is the north edge.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1] / "game" / "data"
KN_KMH = 1.852
SEED = 1
T_STORM_GAIN = 0.34      # how far a region's storminess shifts the weather index
GALE_LO, GALE_HI = 0.66, 1.20   # wide on purpose: a gale builds over >= 3 real minutes of sailing, never a wall


def smoothstep(a: float, b: float, x: float) -> float:
    if a == b:
        return 1.0 if x >= b else 0.0
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def hash01(ix: int, iy: int, iz: int, seed: int) -> float:
    """Integer hash to [0, 1]. Every product stays under 2^62 so GDScript's 64-bit integers give the identical result."""
    h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 668265263)
    h &= 0x7FFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0x7FFFFFFF
    h ^= h >> 16
    return h / 2147483647.0


def vnoise(x: float, y: float, z: float, seed: int) -> float:
    """Smooth value noise in [0, 1] (trilinear, smoothstep-eased)."""
    x0, y0, z0 = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - x0, y - y0, z - z0
    fx, fy, fz = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy), fz * fz * (3 - 2 * fz)
    ix, iy, iz = int(x0), int(y0), int(z0)

    def lerp(a: float, b: float, t: float) -> float:
        return a + (b - a) * t
    c = [[[hash01(ix + i, iy + j, iz + k, seed) for k in (0, 1)] for j in (0, 1)] for i in (0, 1)]
    return lerp(lerp(lerp(c[0][0][0], c[0][0][1], fz), lerp(c[0][1][0], c[0][1][1], fz), fy),
                lerp(lerp(c[1][0][0], c[1][0][1], fz), lerp(c[1][1][0], c[1][1][1], fz), fy), fx)


def fbm(x: float, y: float, z: float, seed: int) -> float:
    """Three octaves, normalised to [0, 1]."""
    return (vnoise(x, y, z, seed) + 0.5 * vnoise(2 * x, 2 * y, 2 * z, seed + 1) + 0.25 * vnoise(4 * x, 4 * y, 4 * z, seed + 2)) / 1.75


def hex_rgb(h: str) -> tuple[float, float, float]:
    return int(h[1:3], 16) / 255.0, int(h[3:5], 16) / 255.0, int(h[5:7], 16) / 255.0


def load_regions(data_dir: Path = DATA) -> list[dict]:
    return json.loads((data_dir / "world" / "regions.json").read_text())["records"]


def load_bands(data_dir: Path = DATA) -> list[dict]:
    return sorted(json.loads((data_dir / "world" / "climate_bands.json").read_text())["records"], key=lambda b: b["lat_deg"])


class Ocean:
    def __init__(self, tuning: dict, regions: list[dict], bands: list[dict], seed: int = SEED):
        self.t, self.regions, self.bands, self.seed = tuning, regions, bands, seed
        self.W, self.H = tuning["ocean.world_width_km"], tuning["ocean.world_height_km"]

    # ---- geography ---------------------------------------------------------------------------------------------------------
    def lat(self, y_km: float) -> float:
        """Climate latitude, +north. Linear in y (compressed: 40 km per degree)."""
        ext = self.t["ocean.lat_extent_deg"]
        return ext - 2.0 * ext * y_km / self.H

    def _warp(self, x: float, y: float) -> tuple[float, float]:
        a, s = self.t["ocean.region_warp_km"], self.t["ocean.region_warp_scale_km"]
        return (x + (fbm(x / s, y / s, 0.5, self.seed + 11) - 0.5) * 2.0 * a, y + (fbm(x / s, y / s, 7.5, self.seed + 23) - 0.5) * 2.0 * a)

    def _distances(self, x: float, y: float) -> list[float]:
        wx, wy = self._warp(x, y)
        asp = self.t["ocean.region_aspect"]
        out = []
        for r in self.regions:
            best = 1e18
            for sx, sy in [(r["seed"]["x_km"], r["seed"]["y_km"])] + [(e["x_km"], e["y_km"]) for e in r.get("extra_seeds", [])]:
                dx, dy = wx - sx, (wy - sy) * asp
                best = min(best, math.sqrt(dx * dx + dy * dy))
            out.append(best / r["seed"]["weight"] + self._lat_penalty(r, wy))
        return out

    def _lat_penalty(self, r: dict, warped_y: float) -> float:
        lat = self.lat(warped_y)
        outside = max(0.0, r["lat_range"]["lo"] - lat, lat - r["lat_range"]["hi"])
        return self.t["ocean.region_lat_penalty"] * outside * (self.H / (2.0 * self.t["ocean.lat_extent_deg"]))

    def region_index(self, x: float, y: float) -> int:
        d = self._distances(x, y)
        return d.index(min(d))

    def region_at(self, x: float, y: float) -> str:
        return self.regions[self.region_index(x, y)]["id"]

    def region_weights(self, x: float, y: float) -> list[float]:
        """Soft region membership (sums to 1): environment parameters blend by this, so borders are gradients over ~2 x blend km."""
        d = self._distances(x, y)
        m, tau = min(d), self.t["ocean.region_blend_km"]
        w = [math.exp(-(v - m) / tau) for v in d]
        s = sum(w)
        return [v / s for v in w]

    def _blend(self, w: list[float], getter) -> float:
        return sum(wi * getter(r) for wi, r in zip(w, self.regions))

    def edge_rim(self, x: float, y: float) -> float:
        """0 inside, rising to 1 at the world edge over ocean.edge_storm_km (the Rim: weather, not a wall)."""
        e = min(x, self.W - x, y, self.H - y)
        return clamp(1.0 - e / self.t["ocean.edge_storm_km"], 0.0, 1.0) ** 2

    # ---- seasons and light -------------------------------------------------------------------------------------------------
    def season_phase(self, t_days: float) -> float:
        return math.fmod(self.t["ocean.start_season_phase"] + t_days / self.t["ocean.year_days"], 1.0)

    @staticmethod
    def declination(s: float) -> float:
        return 23.44 * math.sin(2.0 * math.pi * (s - 0.25))

    def light_limits(self, lat: float, s: float) -> tuple[float, float]:
        """(peak, floor): regional ceiling and floor on the T1 daylight curve. At the equator (1.0, 0.0), so T1 is untouched there.
        Polar winter: the noon sun stays low, the peak falls. Polar summer: the midnight sun lifts the floor."""
        dec = self.declination(s)
        noon = 90.0 - abs(lat - dec)
        midnight = abs(lat + dec) - 90.0
        lo, hi = self.t["ocean.light_twilight_deg"], self.t["ocean.light_full_deg"]
        return smoothstep(lo, hi, noon), 0.6 * smoothstep(lo, 12.0, midnight)

    # ---- temperature, wind, current ----------------------------------------------------------------------------------------
    def sst_raw(self, lat: float, s: float, offset_c: float) -> float:
        amp = self.t["ocean.seasonal_amp_per_lat"] * abs(lat)
        sign = 1.0 if lat >= 0 else -1.0
        return self.t["ocean.sst_equator_c"] - self.t["ocean.sst_lat_sq_c"] * lat * lat - amp * math.cos(2.0 * math.pi * s) * sign + offset_c

    def _band_value(self, alat: float, key: str) -> float:
        b = self.bands
        if alat <= b[0]["lat_deg"]:
            return b[0][key]
        for lo, hi in zip(b, b[1:]):
            if alat <= hi["lat_deg"]:
                f = (alat - lo["lat_deg"]) / (hi["lat_deg"] - lo["lat_deg"])
                return lo[key] + (hi[key] - lo[key]) * f
        return b[-1][key]

    def base_wind(self, lat: float) -> tuple[float, float, float]:
        """Prevailing wind at a latitude: (u_to_east_kn, v_to_south_kn, speed_kn). Vectors are interpolated between the band keyframes."""
        alat = abs(lat)
        b = self.bands
        k = 0
        while k < len(b) - 2 and alat > b[k + 1]["lat_deg"]:
            k += 1
        lo, hi = b[k], b[k + 1]
        f = clamp((alat - lo["lat_deg"]) / (hi["lat_deg"] - lo["lat_deg"]), 0.0, 1.0)

        def vec(band: dict) -> tuple[float, float]:
            frm = band["wind_from_deg"] if lat >= 0 else (180.0 - band["wind_from_deg"]) % 360.0
            r = math.radians(frm)
            return -math.sin(r) * band["wind_kn"], math.cos(r) * band["wind_kn"]   # blowing toward: east = -sin(from), south = +cos(from)
        (u0, v0), (u1, v1) = vec(lo), vec(hi)
        u, v = u0 + (u1 - u0) * f, v0 + (v1 - v0) * f
        return u, v, math.hypot(u, v)

    # ---- the full sample ---------------------------------------------------------------------------------------------------
    def _weather_index(self, x: float, y: float, t_days: float, lat: float, storm_total: float) -> float:
        u, v, _ = self.base_wind(lat)
        drift = 24.0 * KN_KMH * self.t["ocean.weather_drift"]
        lam, ev = self.t["ocean.weather_scale_km"], self.t["ocean.weather_evolve_days"]
        n = fbm((x - u * drift * t_days) / lam, (y - v * drift * t_days) / lam, t_days / ev, self.seed + 7)
        n = clamp((n - 0.5) * 1.7 + 0.5, 0.0, 1.0)     # value noise is bunched around 0.5; stretch it so weather has real extremes
        return n + (storm_total - 0.5) * T_STORM_GAIN

    def sample(self, x: float, y: float, t_days: float) -> dict:
        T = self.t
        w = self.region_weights(x, y)
        ri = self.region_index(x, y)
        lat = self.lat(y)
        s = self.season_phase(t_days)
        hour = 24.0 * (t_days - math.floor(t_days))
        bu, bv, bspeed = self.base_wind(lat)
        rim = self.edge_rim(x, y)
        atm = lambda k: self._blend(w, lambda r: r["atmosphere"][k])  # noqa: E731
        sea = lambda k: self._blend(w, lambda r: r["sea"][k])  # noqa: E731
        storm_total = clamp(self._band_value(abs(lat), "storminess") * atm("storm_bias"), 0.0, 1.5) + 0.8 * rim
        wi = self._weather_index(x, y, t_days, lat, storm_total)
        wi_next = self._weather_index(x, y, t_days + T["ocean.herald_lead_days"], lat, storm_total)
        storm = smoothstep(GALE_LO, GALE_HI, wi)
        herald = smoothstep(GALE_LO, GALE_HI, wi_next)
        rain = clamp(smoothstep(0.58, 0.85, wi) * atm("rain_bias"), 0.0, 1.0)
        cloud = clamp(atm("cloud_bias") + 1.1 * (wi - 0.5), 0.0, 1.0)
        n_w = fbm(x / 400.0, y / 400.0, t_days / 2.0, self.seed + 101)
        mf = math.cos(2.0 * math.pi * (s - 0.5))
        mon = self._blend(w, lambda r: 1.0 - r.get("monsoon", 0.0) + r.get("monsoon", 0.0) * mf)   # 1 for no monsoon; +1 summer, -0.8 winter
        wind_kn = bspeed * abs(mon) * atm("wind_scale") * (0.85 + 0.30 * n_w) * (1.0 + 0.6 * storm)
        calm = clamp(1.0 - bspeed * atm("wind_scale") / 12.0, 0.0, 1.0)
        jitter = (25.0 + 40.0 * calm) * (fbm(x / 500.0, y / 500.0, t_days / 3.0, self.seed + 131) - 0.5) * 2.0
        from_deg = (math.degrees(math.atan2(-bu, bv)) + (180.0 if mon < 0 else 0.0) + 360.0 + jitter) % 360.0   # direction the wind comes FROM
        # fog is thickest near dawn
        n_f = fbm(x / 200.0, y / 200.0, t_days / 2.5, self.seed + 31)
        dawn = 0.5 + 0.5 * math.cos(2.0 * math.pi * (hour - 6.0) / 24.0)
        fog = clamp(atm("fog_base") * (0.5 + 1.0 * n_f) * (1.0 - 0.8 * storm) * (0.8 + 0.4 * dawn), 0.0, 1.0)
        vis = T["ocean.visibility_clear_km"] * math.exp(-T["ocean.fog_vis_coeff"] * fog - T["ocean.rain_vis_coeff"] * rain)
        ms = wind_kn * 0.514444
        swell = sea("swell_m") * (0.7 + 0.6 * fbm(x / 600.0, y / 600.0, t_days / 4.0, self.seed + 151)) + 2.0 * herald
        wave = min(T["ocean.wave_max_m"], math.sqrt((T["ocean.wave_coeff"] * ms * ms) ** 2 + swell * swell))
        # temperature and ice
        sst = self.sst_raw(lat, s, sea("sst_offset_c"))
        water_c = max(sst, T["ocean.sst_freeze_c"])
        air_c = water_c + T["ocean.air_minus_sst_c"] + 1.5 * math.sin(2.0 * math.pi * (hour - 9.0) / 24.0)
        m = clamp((-0.5 - sst) / 2.5, 0.0, 1.0)
        base_ice = clamp(m * m * (3 - 2 * m) + 0.45 * self._blend(w, lambda r: r["ice"]["sea_ice_bias"]) + 0.5 * rim, 0.0, 1.0)
        n_i = fbm(x / 150.0, y / 150.0, t_days / 6.0, self.seed + 53)
        ice = clamp(base_ice + 0.6 * (n_i - 0.5) * 4.0 * base_ice * (1.0 - base_ice), 0.0, 1.0)
        ridge = 1.0 - abs(2.0 * fbm(x / 90.0, y / 90.0, t_days / 8.0, self.seed + 71) - 1.0)
        lead = smoothstep(0.90, 0.985, ridge) * clamp((sst + 5.5) / 3.0, 0.0, 1.0)
        ice = ice * (1.0 - 0.85 * lead)
        if base_ice < 0.02:
            ice = 0.0
        # water, life, light
        n_d = fbm(x / 700.0, y / 700.0, 0.0, self.seed + 91)
        depth = max(15.0, sea("depth_m") * (0.35 + 1.3 * n_d))
        bloom = 0.0
        for wi_, r in zip(w, self.regions):
            if "bloom" in r:
                b = r["bloom"]
                d = abs(s - b["center"])
                d = min(d, 1.0 - d)
                bloom += wi_ * b["strength"] * math.exp(-(d / b["width"]) ** 2)
        spring = 0.0 if abs(lat) < 30.0 else 0.4 * math.cos(2.0 * math.pi * (s - (0.25 if lat >= 0 else 0.75)))
        prod = clamp(sea("productivity") * (0.6 + 0.8 * fbm(x / 400.0, y / 400.0, t_days / 10.0, self.seed + 181)) * (1.0 + spring) + bloom, 0.0, 1.0)
        peak, floor_ = self.light_limits(lat, s)
        cu = self._band_value(abs(lat), "current_u_kn") + sea("current_u_kn")
        return {"region": self.regions[ri]["id"], "lat": lat, "season": s, "hour": hour, "rim": rim,
                "wind_kn": wind_kn, "wind_from_deg": from_deg, "storm": storm, "herald": herald, "rain": rain, "cloud": cloud, "fog": fog,
                "visibility_km": vis, "wave_m": wave, "lightning": storm * atm("lightning"),
                "sst_c": water_c, "air_c": air_c, "ice": ice, "depth_m": depth, "productivity": prod, "bloom": bloom,
                "light_peak": peak, "light_floor": floor_, "current_u_kn": cu, "current_v_kn": sea("current_v_kn"),
                "weights": w}

    # ---- icebergs (a hash on a grid, no state) ----------------------------------------------------------------------------
    def bergs_near(self, x: float, y: float, radius_km: float) -> list[tuple[float, float, int]]:
        cell = self.t["ocean.iceberg_cell_km"]
        out = []
        for cx in range(int(math.floor((x - radius_km) / cell)), int(math.floor((x + radius_km) / cell)) + 1):
            for cy in range(int(math.floor((y - radius_km) / cell)), int(math.floor((y + radius_km) / cell)) + 1):
                px, py = (cx + 0.5) * cell, (cy + 0.5) * cell
                if px < 0 or py < 0 or px > self.W or py > self.H:
                    continue
                dens = self._blend(self.region_weights(px, py), lambda r: r["ice"]["iceberg_per_10k_km2"]) * cell * cell / 10000.0
                n = int(dens) + (1 if hash01(cx, cy, 0, self.seed + 5) < dens - int(dens) else 0)
                for k in range(n):
                    bx = (cx + hash01(cx, cy, 2 * k + 1, self.seed + 6)) * cell
                    by = (cy + hash01(cx, cy, 2 * k + 2, self.seed + 7)) * cell
                    if math.hypot(bx - x, by - y) <= radius_km:
                        size = 1 + int(4.0 * hash01(cx, cy, 2 * k + 9, self.seed + 8) ** 2)
                        out.append((bx, by, min(size, 4)))
        return out

    # ---- ship ----------------------------------------------------------------------------------------------------------------
    def speed_through_water_kmh(self, heading_deg: float, wind_kn: float, wind_from_deg: float, ice: float) -> float:
        T = self.t
        off = abs((heading_deg - wind_from_deg + 540.0) % 360.0 - 180.0)   # 0 = straight into the wind
        no_go = T["ship.no_go_deg"]
        if off < no_go:
            f = 0.12
        elif off < 100.0:
            f = 0.55 + 0.45 * (off - no_go) / (100.0 - no_go)
        elif off < 135.0:
            f = 1.0 - 0.05 * (off - 100.0) / 35.0
        else:
            f = 0.95 - 0.15 * (off - 135.0) / 45.0
        ref, reef = T["ship.ref_wind_kn"], T["ship.reef_wind_kn"]
        hull = T["ship.hull_speed_factor"]    # a sloop cannot outrun its hull however hard it blows
        if wind_kn <= reef:
            g = min(hull, (wind_kn / ref) ** 0.6)
        else:
            g = max(0.5, hull * (1.0 - 0.02 * (wind_kn - reef)))     # reefed down: slower again
        v = T["ship.sail_speed_kmh"] * f * g * (1.0 - T["ship.ice_speed_loss"] * ice)
        if ice > 0.95:
            return 0.0
        return max(0.4 if ice < 0.5 else 0.0, v)   # a becalmed ship still drifts; never exactly stopped unless frozen in

    def ground_velocity_kmh(self, heading_deg: float, sample: dict) -> tuple[float, float]:
        """(east, south) km per game hour: sailing plus the current."""
        v = self.speed_through_water_kmh(heading_deg, sample["wind_kn"], sample["wind_from_deg"], sample["ice"])
        r = math.radians(heading_deg)
        return (v * math.sin(r) + sample["current_u_kn"] * KN_KMH, -v * math.cos(r) + sample["current_v_kn"] * KN_KMH)


def look_at(ocean: Ocean, x: float, y: float) -> dict:
    """Blended presentation parameters (colours as 0..1 RGB). The renderer never needs to know which region it is in."""
    w = ocean.region_weights(x, y)

    def col(getter) -> tuple[float, float, float]:
        cs = [hex_rgb(getter(r)) for r in ocean.regions]
        return tuple(sum(wi * c[i] for wi, c in zip(w, cs)) for i in range(3))
    num = lambda getter: sum(wi * getter(r) for wi, r in zip(w, ocean.regions))  # noqa: E731
    return {"deep": col(lambda r: r["water"]["deep"]), "shallow": col(lambda r: r["water"]["shallow"]), "clarity": num(lambda r: r["water"]["clarity"]),
            "wave_scale": num(lambda r: r["water"]["wave_scale"]), "foam": num(lambda r: r["water"]["foam"]),
            "sky_day": col(lambda r: r["sky"]["day"]), "sky_dusk": col(lambda r: r["sky"]["dusk"]), "sky_night": col(lambda r: r["sky"]["night"]),
            "fog_color": col(lambda r: r["atmosphere"]["fog_color"])}


def load(data_dir: Path = DATA) -> Ocean:
    import design_checks as D  # noqa: PLC0415
    return Ocean(D.load_tuning(), load_regions(data_dir), load_bands(data_dir))


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(HERE))
    oc = load()
    for rid, (px, py) in {r["id"]: (r["seed"]["x_km"], r["seed"]["y_km"]) for r in oc.regions}.items():
        smp = oc.sample(px, py, 10.5)
        print(f"{rid:24s} wind {smp['wind_kn']:5.1f}kn wave {smp['wave_m']:4.1f}m vis {smp['visibility_km']:5.2f}km sst {smp['sst_c']:5.1f} ice {smp['ice']:.2f} region {smp['region']}")
