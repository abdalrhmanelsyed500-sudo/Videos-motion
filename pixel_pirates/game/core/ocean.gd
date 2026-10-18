extends RefCounted
## The ocean model (Module E1): where you are, what the sea and sky are doing there, and what that does to a ship.
## Python twin: tools/data_tools/ocean.py. Both replay tests/fixtures/ocean_cases.json
## (golden values from the Python side).
## Everything here is a PURE function of (x_km, y_km, t_days) and the data files:
## no random-number state, no stored world.
## The same place at the same time is always the same sea, so a save needs only the clock
## and weather can never be re-rolled.
## Units: km, game days (fraction = time of day, 0.25 = 06:00), knots, metres, degrees C, compass degrees (0 = north).
## The map has y growing SOUTHWARD: y = 0 is the north edge.
## KEEP IN SYNC with the Python twin: if you change a formula there, change it here and regenerate the fixtures.
const DataLoader := preload("res://core/data_loader.gd")
const KN_KMH := 1.852
const SEED := 1
const GALE_LO := 0.66
const GALE_HI := 1.20
const T_STORM_GAIN := 0.34
const TUNING_DIR := "res://data/tuning"

var regions: Array = []
var bands: Array = []
var world_w: float = 0.0
var world_h: float = 0.0
var _t: Dictionary = {}
var _seed: int = SEED


## Build from plain dictionaries: tuning_map {key: value}, region records, climate band records.
func _init(tuning_map: Dictionary, region_records: Array, band_records: Array, seed_value: int = SEED) -> void:
	_t = tuning_map
	regions = region_records
	bands = band_records.duplicate()
	bands.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["lat_deg"]) < float(b["lat_deg"]))
	_seed = seed_value
	world_w = float(_t["ocean.world_width_km"])
	world_h = float(_t["ocean.world_height_km"])


## Load the shipped data files (no autoload needed, so headless tests can use it).
static func load_default() -> RefCounted:
	var script: GDScript = load("res://core/ocean.gd")
	var tuning_map := load_tuning()
	var rg: Dictionary = DataLoader.load_dict("res://data/world/regions.json")
	var bd: Dictionary = DataLoader.load_dict("res://data/world/climate_bands.json")
	return script.new(tuning_map, rg.get("records", []), bd.get("records", []))


static func load_tuning() -> Dictionary:
	var out: Dictionary = {}
	var d := DirAccess.open(TUNING_DIR)
	if d == null:
		return out
	for f in d.get_files():
		if f.begins_with("tuning_") and f.ends_with(".json"):
			var doc: Dictionary = DataLoader.load_dict(TUNING_DIR + "/" + f)
			for r in doc.get("records", []):
				out[str(r["key"])] = float(r["value"])
	return out


func tuning_value(key: String) -> float:
	return float(_t[key])


func tuning() -> Dictionary:
	return _t


# ---- noise ---------------------------------------------------------------------------------------
static func smoothstep_range(a: float, b: float, x: float) -> float:
	if a == b:
		return 1.0 if x >= b else 0.0
	var t := minf(1.0, maxf(0.0, (x - a) / (b - a)))
	return t * t * (3.0 - 2.0 * t)


## Integer hash to [0, 1]. Every product stays under 2^62, so 64-bit integers give the identical result to Python.
static func hash01(ix: int, iy: int, iz: int, seed_value: int) -> float:
	var h: int = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed_value * 668265263)
	h &= 0x7FFFFFFF
	h = ((h ^ (h >> 13)) * 1274126177) & 0x7FFFFFFF
	h ^= h >> 16
	return float(h) / 2147483647.0


static func vnoise(x: float, y: float, z: float, seed_value: int) -> float:
	var x0 := floorf(x)
	var y0 := floorf(y)
	var z0 := floorf(z)
	var fx := x - x0
	var fy := y - y0
	var fz := z - z0
	fx = fx * fx * (3.0 - 2.0 * fx)
	fy = fy * fy * (3.0 - 2.0 * fy)
	fz = fz * fz * (3.0 - 2.0 * fz)
	var ix := int(x0)
	var iy := int(y0)
	var iz := int(z0)
	var c000 := hash01(ix, iy, iz, seed_value)
	var c001 := hash01(ix, iy, iz + 1, seed_value)
	var c010 := hash01(ix, iy + 1, iz, seed_value)
	var c011 := hash01(ix, iy + 1, iz + 1, seed_value)
	var c100 := hash01(ix + 1, iy, iz, seed_value)
	var c101 := hash01(ix + 1, iy, iz + 1, seed_value)
	var c110 := hash01(ix + 1, iy + 1, iz, seed_value)
	var c111 := hash01(ix + 1, iy + 1, iz + 1, seed_value)
	var a := lerpf(lerpf(c000, c001, fz), lerpf(c010, c011, fz), fy)
	var b := lerpf(lerpf(c100, c101, fz), lerpf(c110, c111, fz), fy)
	return lerpf(a, b, fx)


static func fbm(x: float, y: float, z: float, seed_value: int) -> float:
	return (vnoise(x, y, z, seed_value) + 0.5 * vnoise(2.0 * x, 2.0 * y, 2.0 * z, seed_value + 1) \
			+ 0.25 * vnoise(4.0 * x, 4.0 * y, 4.0 * z, seed_value + 2)) / 1.75


static func hex_rgb(h: String) -> Array:
	return [
			h.substr(1, 2).hex_to_int() / 255.0,
			h.substr(3, 2).hex_to_int() / 255.0,
			h.substr(5, 2).hex_to_int() / 255.0]


# ---- geography -----------------------------------------------------------------------------------
## Climate latitude, +north. Linear in y (compressed: 40 km per degree).
func lat(y_km: float) -> float:
	var ext := float(_t["ocean.lat_extent_deg"])
	return ext - 2.0 * ext * y_km / world_h


## Domain warp. Returns [x, y] as an Array of doubles (Vector2 would round to 32-bit floats and break parity).
func _warp(x: float, y: float) -> Array:
	var a := float(_t["ocean.region_warp_km"])
	var s := float(_t["ocean.region_warp_scale_km"])
	var dx := (fbm(x / s, y / s, 0.5, _seed + 11) - 0.5) * 2.0 * a
	var dy := (fbm(x / s, y / s, 7.5, _seed + 23) - 0.5) * 2.0 * a
	return [x + dx, y + dy]


func _lat_penalty(r: Dictionary, warped_y: float) -> float:
	var la := lat(warped_y)
	var rng: Dictionary = r["lat_range"]
	var outside := maxf(0.0, maxf(float(rng["lo"]) - la, la - float(rng["hi"])))
	return float(_t["ocean.region_lat_penalty"]) * outside * (world_h / (2.0 * float(_t["ocean.lat_extent_deg"])))


func _distances(x: float, y: float) -> PackedFloat64Array:
	var wp := _warp(x, y)
	var wx: float = wp[0]
	var wy: float = wp[1]
	var asp := float(_t["ocean.region_aspect"])
	var out := PackedFloat64Array()
	for r in regions:
		var seed_pos: Dictionary = r["seed"]
		var best := 1e18
		var pts: Array = [[float(seed_pos["x_km"]), float(seed_pos["y_km"])]]
		for e in r.get("extra_seeds", []):
			pts.append([float(e["x_km"]), float(e["y_km"])])
		for p in pts:
			var dx: float = wx - float(p[0])
			var dy: float = (wy - float(p[1])) * asp
			best = minf(best, sqrt(dx * dx + dy * dy))
		out.append(best / float(seed_pos["weight"]) + _lat_penalty(r, wy))
	return out


func region_index(x: float, y: float) -> int:
	var d := _distances(x, y)
	var best := 0
	for i in range(1, d.size()):
		if d[i] < d[best]:
			best = i
	return best


func region_at(x: float, y: float) -> String:
	return str(regions[region_index(x, y)]["id"])


## Soft membership (sums to 1). Environment parameters blend by this, so borders are gradients about 2 x blend km wide.
func region_weights(x: float, y: float) -> PackedFloat64Array:
	var d := _distances(x, y)
	var m := d[0]
	for v in d:
		m = minf(m, v)
	var tau := float(_t["ocean.region_blend_km"])
	var w := PackedFloat64Array()
	var total := 0.0
	for v in d:
		var e := exp(-(v - m) / tau)
		w.append(e)
		total += e
	for i in w.size():
		w[i] = w[i] / total
	return w


func _blend(w: PackedFloat64Array, section: String, key: String, fallback: float = 0.0) -> float:
	var total := 0.0
	for i in regions.size():
		var r: Dictionary = regions[i]
		var v: float = fallback
		if section == "":
			v = float(r.get(key, fallback))
		else:
			v = float((r[section] as Dictionary).get(key, fallback))
		total += w[i] * v
	return total


## 0 inside, rising to 1 at the world edge over ocean.edge_storm_km (the Rim: weather, not a wall).
func edge_rim(x: float, y: float) -> float:
	var e := minf(minf(x, world_w - x), minf(y, world_h - y))
	return pow(clampf(1.0 - e / float(_t["ocean.edge_storm_km"]), 0.0, 1.0), 2.0)


# ---- seasons and light ---------------------------------------------------------------------------
func season_phase(t_days: float) -> float:
	return fmod(float(_t["ocean.start_season_phase"]) + t_days / float(_t["ocean.year_days"]), 1.0)


static func declination(s: float) -> float:
	return 23.44 * sin(2.0 * PI * (s - 0.25))


## [peak, floor]: regional ceiling and floor on the T1 daylight curve. At the equator [1, 0], so T1 is untouched there.
func light_limits(la: float, s: float) -> Array:
	var dec := declination(s)
	var noon := 90.0 - absf(la - dec)
	var midnight := absf(la + dec) - 90.0
	var lo := float(_t["ocean.light_twilight_deg"])
	var hi := float(_t["ocean.light_full_deg"])
	return [smoothstep_range(lo, hi, noon), 0.6 * smoothstep_range(lo, 12.0, midnight)]


# ---- temperature, wind, current ------------------------------------------------------------------
func sst_raw(la: float, s: float, offset_c: float) -> float:
	var amp := float(_t["ocean.seasonal_amp_per_lat"]) * absf(la)
	var sign_v := 1.0 if la >= 0.0 else -1.0
	var lat_term := float(_t["ocean.sst_lat_sq_c"]) * la * la
	return float(_t["ocean.sst_equator_c"]) - lat_term - amp * cos(2.0 * PI * s) * sign_v + offset_c


func _band_value(alat: float, key: String) -> float:
	var b := bands
	if alat <= float(b[0]["lat_deg"]):
		return float(b[0][key])
	for i in range(b.size() - 1):
		var lo: Dictionary = b[i]
		var hi: Dictionary = b[i + 1]
		if alat <= float(hi["lat_deg"]):
			var f := (alat - float(lo["lat_deg"])) / (float(hi["lat_deg"]) - float(lo["lat_deg"]))
			return float(lo[key]) + (float(hi[key]) - float(lo[key])) * f
	return float(b[b.size() - 1][key])


func _wind_vec(band: Dictionary, la: float) -> Array:
	var frm := float(band["wind_from_deg"])
	if la < 0.0:
		frm = fposmod(180.0 - frm, 360.0)
	var r := deg_to_rad(frm)
	var kn := float(band["wind_kn"])
	return [-sin(r) * kn, cos(r) * kn]   # blowing toward: east = -sin(from), south = +cos(from)


## [u_to_east_kn, v_to_south_kn, speed_kn]: prevailing wind at a latitude (vectors interpolated between band keyframes).
func base_wind(la: float) -> Array:
	var alat := absf(la)
	var b := bands
	var k := 0
	while k < b.size() - 2 and alat > float(b[k + 1]["lat_deg"]):
		k += 1
	var lo: Dictionary = b[k]
	var hi: Dictionary = b[k + 1]
	var f := clampf((alat - float(lo["lat_deg"])) / (float(hi["lat_deg"]) - float(lo["lat_deg"])), 0.0, 1.0)
	var v0 := _wind_vec(lo, la)
	var v1 := _wind_vec(hi, la)
	var u: float = float(v0[0]) + (float(v1[0]) - float(v0[0])) * f
	var v: float = float(v0[1]) + (float(v1[1]) - float(v0[1])) * f
	return [u, v, sqrt(u * u + v * v)]


func _weather_index(x: float, y: float, t_days: float, la: float, storm_total: float) -> float:
	var bw := base_wind(la)
	var drift := 24.0 * KN_KMH * float(_t["ocean.weather_drift"])
	var lam := float(_t["ocean.weather_scale_km"])
	var ev := float(_t["ocean.weather_evolve_days"])
	var nx := (x - float(bw[0]) * drift * t_days) / lam
	var ny := (y - float(bw[1]) * drift * t_days) / lam
	var n := fbm(nx, ny, t_days / ev, _seed + 7)
	n = clampf((n - 0.5) * 1.7 + 0.5, 0.0, 1.0)
	return n + (storm_total - 0.5) * T_STORM_GAIN


# ---- the full sample -----------------------------------------------------------------------------
## Everything the sea and sky are doing at (x, y, t). Keys match the Python twin. "region" is a String, "weights" a
## PackedFloat64Array; the rest are floats.
func sample(x: float, y: float, t_days: float) -> Dictionary:
	var w := region_weights(x, y)
	var ri := region_index(x, y)
	var la := lat(y)
	var s := season_phase(t_days)
	var hour := 24.0 * (t_days - floorf(t_days))
	var bw := base_wind(la)
	var bu: float = bw[0]
	var bv: float = bw[1]
	var bspeed: float = bw[2]
	var rim := edge_rim(x, y)
	var storm_raw := _band_value(absf(la), "storminess") * _blend(w, "atmosphere", "storm_bias")
	var storm_total := clampf(storm_raw, 0.0, 1.5) + 0.8 * rim
	var wi := _weather_index(x, y, t_days, la, storm_total)
	var wi_next := _weather_index(x, y, t_days + float(_t["ocean.herald_lead_days"]), la, storm_total)
	var storm := smoothstep_range(GALE_LO, GALE_HI, wi)
	var herald := smoothstep_range(GALE_LO, GALE_HI, wi_next)
	var rain := clampf(smoothstep_range(0.58, 0.85, wi) * _blend(w, "atmosphere", "rain_bias"), 0.0, 1.0)
	var cloud := clampf(_blend(w, "atmosphere", "cloud_bias") + 1.1 * (wi - 0.5), 0.0, 1.0)
	var n_w := fbm(x / 400.0, y / 400.0, t_days / 2.0, _seed + 101)
	var mf := cos(2.0 * PI * (s - 0.5))
	var mon := 0.0
	for i in regions.size():
		var mz := float((regions[i] as Dictionary).get("monsoon", 0.0))
		mon += w[i] * (1.0 - mz + mz * mf)
	var wind_scale := _blend(w, "atmosphere", "wind_scale")
	var wind_kn := bspeed * absf(mon) * wind_scale * (0.85 + 0.30 * n_w) * (1.0 + 0.6 * storm)
	var calm := clampf(1.0 - bspeed * wind_scale / 12.0, 0.0, 1.0)
	var jitter := (25.0 + 40.0 * calm) * (fbm(x / 500.0, y / 500.0, t_days / 3.0, _seed + 131) - 0.5) * 2.0
	var from_deg := fposmod(rad_to_deg(atan2(-bu, bv)) + (180.0 if mon < 0.0 else 0.0) + 360.0 + jitter, 360.0)
	var n_f := fbm(x / 200.0, y / 200.0, t_days / 2.5, _seed + 31)
	var dawn := 0.5 + 0.5 * cos(2.0 * PI * (hour - 6.0) / 24.0)
	var fog_raw := _blend(w, "atmosphere", "fog_base") * (0.5 + 1.0 * n_f) * (1.0 - 0.8 * storm) * (0.8 + 0.4 * dawn)
	var fog := clampf(fog_raw, 0.0, 1.0)
	var vis_k := float(_t["ocean.fog_vis_coeff"]) * fog + float(_t["ocean.rain_vis_coeff"]) * rain
	var vis := float(_t["ocean.visibility_clear_km"]) * exp(-vis_k)
	var ms := wind_kn * 0.514444
	var swell_n := fbm(x / 600.0, y / 600.0, t_days / 4.0, _seed + 151)
	var swell := _blend(w, "sea", "swell_m") * (0.7 + 0.6 * swell_n) + 2.0 * herald
	var wc := float(_t["ocean.wave_coeff"]) * ms * ms
	var wave := minf(float(_t["ocean.wave_max_m"]), sqrt(wc * wc + swell * swell))
	var sst := sst_raw(la, s, _blend(w, "sea", "sst_offset_c"))
	var water_c := maxf(sst, float(_t["ocean.sst_freeze_c"]))
	var air_c := water_c + float(_t["ocean.air_minus_sst_c"]) + 1.5 * sin(2.0 * PI * (hour - 9.0) / 24.0)
	var m := clampf((-0.5 - sst) / 2.5, 0.0, 1.0)
	var base_ice := clampf(m * m * (3.0 - 2.0 * m) + 0.45 * _blend(w, "ice", "sea_ice_bias") + 0.5 * rim, 0.0, 1.0)
	var n_i := fbm(x / 150.0, y / 150.0, t_days / 6.0, _seed + 53)
	var ice := clampf(base_ice + 0.6 * (n_i - 0.5) * 4.0 * base_ice * (1.0 - base_ice), 0.0, 1.0)
	var ridge := 1.0 - absf(2.0 * fbm(x / 90.0, y / 90.0, t_days / 8.0, _seed + 71) - 1.0)
	var lead := smoothstep_range(0.90, 0.985, ridge) * clampf((sst + 5.5) / 3.0, 0.0, 1.0)
	ice = ice * (1.0 - 0.85 * lead)
	if base_ice < 0.02:
		ice = 0.0
	var n_d := fbm(x / 700.0, y / 700.0, 0.0, _seed + 91)
	var depth := maxf(15.0, _blend(w, "sea", "depth_m") * (0.35 + 1.3 * n_d))
	var bloom := 0.0
	for i in regions.size():
		var r: Dictionary = regions[i]
		if r.has("bloom"):
			var bl: Dictionary = r["bloom"]
			var d := absf(s - float(bl["center"]))
			d = minf(d, 1.0 - d)
			bloom += w[i] * float(bl["strength"]) * exp(-pow(d / float(bl["width"]), 2.0))
	var spring := 0.0
	if absf(la) >= 30.0:
		spring = 0.4 * cos(2.0 * PI * (s - (0.25 if la >= 0.0 else 0.75)))
	var prod_n := fbm(x / 400.0, y / 400.0, t_days / 10.0, _seed + 181)
	var prod := clampf(_blend(w, "sea", "productivity") * (0.6 + 0.8 * prod_n) * (1.0 + spring) + bloom, 0.0, 1.0)
	var lim := light_limits(la, s)
	var cu := _band_value(absf(la), "current_u_kn") + _blend(w, "sea", "current_u_kn")
	return {"region": str(regions[ri]["id"]), "lat": la, "season": s, "hour": hour, "rim": rim,
			"wind_kn": wind_kn, "wind_from_deg": from_deg, "storm": storm, "herald": herald, "rain": rain,
			"cloud": cloud, "fog": fog,
			"visibility_km": vis, "wave_m": wave, "lightning": storm * _blend(w, "atmosphere", "lightning"),
			"sst_c": water_c, "air_c": air_c, "ice": ice, "depth_m": depth, "productivity": prod, "bloom": bloom,
			"light_peak": float(lim[0]), "light_floor": float(lim[1]), "current_u_kn": cu,
			"current_v_kn": _blend(w, "sea", "current_v_kn"),
			"weights": w}


# ---- icebergs (a hash on a grid, no stored state) ------------------------------------------------
## Icebergs within radius_km of (x, y): an Array of [x_km, y_km, size 1..4].
func bergs_near(x: float, y: float, radius_km: float) -> Array:
	var cell := float(_t["ocean.iceberg_cell_km"])
	var out: Array = []
	for cx in range(int(floorf((x - radius_km) / cell)), int(floorf((x + radius_km) / cell)) + 1):
		for cy in range(int(floorf((y - radius_km) / cell)), int(floorf((y + radius_km) / cell)) + 1):
			var px := (cx + 0.5) * cell
			var py := (cy + 0.5) * cell
			if px < 0.0 or py < 0.0 or px > world_w or py > world_h:
				continue
			var dens := _blend(region_weights(px, py), "ice", "iceberg_per_10k_km2") * cell * cell / 10000.0
			var n := int(dens)
			if hash01(cx, cy, 0, _seed + 5) < dens - float(int(dens)):
				n += 1
			for k in n:
				var bx := (cx + hash01(cx, cy, 2 * k + 1, _seed + 6)) * cell
				var by := (cy + hash01(cx, cy, 2 * k + 2, _seed + 7)) * cell
				if sqrt((bx - x) * (bx - x) + (by - y) * (by - y)) <= radius_km:
					var size := 1 + int(4.0 * pow(hash01(cx, cy, 2 * k + 9, _seed + 8), 2.0))
					out.append([bx, by, mini(size, 4)])
	return out


# ---- ship ----------------------------------------------------------------------------------------
## Speed through the water (km per game hour) for a heading, given wind and ice.
func speed_through_water_kmh(heading_deg: float, wind_kn: float, wind_from_deg: float, ice: float) -> float:
	var off := absf(fposmod(heading_deg - wind_from_deg + 540.0, 360.0) - 180.0)   # 0 = straight into the wind
	var no_go := float(_t["ship.no_go_deg"])
	var f := 0.0
	if off < no_go:
		f = 0.12
	elif off < 100.0:
		f = 0.55 + 0.45 * (off - no_go) / (100.0 - no_go)
	elif off < 135.0:
		f = 1.0 - 0.05 * (off - 100.0) / 35.0
	else:
		f = 0.95 - 0.15 * (off - 135.0) / 45.0
	var ref_kn := float(_t["ship.ref_wind_kn"])
	var reef := float(_t["ship.reef_wind_kn"])
	var hull := float(_t["ship.hull_speed_factor"])
	var g := 0.0
	if wind_kn <= reef:
		g = minf(hull, pow(wind_kn / ref_kn, 0.6))
	else:
		g = maxf(0.5, hull * (1.0 - 0.02 * (wind_kn - reef)))
	var v := float(_t["ship.sail_speed_kmh"]) * f * g * (1.0 - float(_t["ship.ice_speed_loss"]) * ice)
	if ice > 0.95:
		return 0.0
	return maxf(0.4 if ice < 0.5 else 0.0, v)   # a becalmed ship still drifts; stopped only when frozen in


## [east, south] km per game hour: sailing plus the current.
func ground_velocity_kmh(heading_deg: float, smp: Dictionary) -> Array:
	var v := speed_through_water_kmh(heading_deg, float(smp["wind_kn"]), float(smp["wind_from_deg"]), float(smp["ice"]))
	var r := deg_to_rad(heading_deg)
	return [v * sin(r) + float(smp["current_u_kn"]) * KN_KMH, -v * cos(r) + float(smp["current_v_kn"]) * KN_KMH]


## Blended presentation parameters (colours as [r, g, b] 0..1). The renderer never needs to know which region it is in.
func look_at(x: float, y: float) -> Dictionary:
	var w := region_weights(x, y)
	return {"deep": _col(w, "water", "deep"), "shallow": _col(w, "water", "shallow"),
			"clarity": _blend(w, "water", "clarity"),
			"wave_scale": _blend(w, "water", "wave_scale"), "foam": _blend(w, "water", "foam"),
			"sky_day": _col(w, "sky", "day"), "sky_dusk": _col(w, "sky", "dusk"), "sky_night": _col(w, "sky", "night"),
			"fog_color": _col(w, "atmosphere", "fog_color")}


func _col(w: PackedFloat64Array, section: String, key: String) -> Array:
	var out: Array = [0.0, 0.0, 0.0]
	for i in regions.size():
		var c := hex_rgb(str((regions[i][section] as Dictionary)[key]))
		for k in 3:
			out[k] = float(out[k]) + w[i] * float(c[k])
	return out
