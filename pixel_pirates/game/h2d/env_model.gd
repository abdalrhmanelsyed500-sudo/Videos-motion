extends RefCounted
## The ONE shared environmental state (H2D-0.2). The weather the world produces (Ocean.sample: wind, waves, rain, storm,
## fog) is only the TARGET; this model is what the scene actually experiences. Wind has gusts and veers in them, the sea
## builds up and dies away slowly, waves keep travelling the old way for a while after the wind turns, rain sets in and
## eases off, visibility follows rain and fog. Waves, rain, spray, sail shape and ship motion are all derived from these
## numbers, so they cannot disagree. Pure arithmetic (no nodes): testable without a window.
## Twin of tools/h2d/env_logic.py (fixture tests/fixtures/env_cases.json).
## All numbers: data/tuning/tuning_env.json (env.*).
## NOT YET RUN IN GODOT.
const PREFIX := "env."
const KN_TO_MS := 0.514444
const DEFAULTS := {
	"wind_tau_s": 5.0, "wind_dir_tau_s": 8.0, "sea_build_s": 14.0, "sea_decay_s": 24.0, "wave_dir_tau_s": 20.0,
	"rain_build_s": 5.0, "rain_decay_s": 9.0, "air_tau_s": 6.0, "gust_gain": 0.45, "gust_veer_deg": 12.0,
	"gust_manual_decay_s": 4.0, "gust_surge": 0.12, "wave_visual_gain": 1.3, "crest_p_calm": 1.0, "crest_p_gale": 2.6,
	"sea_wave_w": 0.5, "sea_wind_w": 0.35, "sea_storm_w": 0.2, "sea_wave_ref_m": 6.5, "sea_wind_ref_kn": 38.0,
	"sea_calm_max": 0.12, "sea_breezy_max": 0.35, "sea_rough_max": 0.65, "sea_storm_min": 0.96,
}

var wind_kn := 8.0  ## mean wind speed (no gust)
var wind_from := 0.0  ## mean direction the wind blows FROM, degrees
var wave_m := 1.0  ## wave height now (the sea builds and subsides gradually)
var wave_to := 180.0  ## direction the waves travel TO, degrees (lags the wind)
var rain := 0.0
var storm := 0.0
var fog := 0.0
var gust := 0.0  ## 0..1 gust strength now (deterministic in time, plus manual gusts)
var wind_inst_kn := 8.0  ## mean wind plus the gust
var wind_from_inst := 0.0  ## wind direction including the veer in a gust
var sea := 0.0  ## sea-state index 0..1: calm, breezy, rough, gale, storm
var rain_inst := 0.0
var visibility_km := 10.0
var adv := Vector2.ZERO  ## metres the wind has carried the air since the start (rain cells and gust patches drift)
var time := 0.0
var _p: Dictionary = DEFAULTS.duplicate()
var _clear_km := 10.0
var _fog_coeff := 3.2
var _rain_coeff := 1.0
var _manual_gust := 0.0


## `values` is the tuning dictionary {key: value} (Ocean.tuning()).
func configure(values: Dictionary) -> void:
	_p = DEFAULTS.duplicate()
	for k in DEFAULTS.keys():
		var full: String = PREFIX + str(k)
		if values.has(full):
			_p[k] = float(values[full])
	_clear_km = float(values.get("ocean.visibility_clear_km", 10.0))
	_fog_coeff = float(values.get("ocean.fog_vis_coeff", 3.2))
	_rain_coeff = float(values.get("ocean.rain_vis_coeff", 1.0))


func param(key: String) -> float:
	return float(_p[key])


## Jump straight to a target (start of the game, benchmark phases). A normal weather change uses step() and is gradual.
func snap(tgt: Dictionary) -> void:
	wind_kn = float(tgt["wind_kn"])
	wind_from = fposmod(float(tgt["wind_from_deg"]), 360.0)
	wave_m = float(tgt["wave_m"])
	wave_to = fposmod(wind_from + 180.0, 360.0)
	rain = float(tgt["rain"])
	storm = float(tgt["storm"])
	fog = float(tgt["fog"])
	_manual_gust = 0.0
	_derive(0.0, 0.0)


func trigger_gust() -> void:
	_manual_gust = 1.0


func step(dt: float, tgt: Dictionary, t: float) -> void:
	wind_kn = approach(wind_kn, float(tgt["wind_kn"]), param("wind_tau_s"), dt)
	wind_from = approach_angle(wind_from, float(tgt["wind_from_deg"]), param("wind_dir_tau_s"), dt)
	var growing := float(tgt["wave_m"]) > wave_m
	wave_m = approach(wave_m, float(tgt["wave_m"]), param("sea_build_s") if growing else param("sea_decay_s"), dt)
	wave_to = approach_angle(wave_to, fposmod(wind_from + 180.0, 360.0), param("wave_dir_tau_s"), dt)
	var rising := float(tgt["rain"]) > rain
	rain = approach(rain, float(tgt["rain"]), param("rain_build_s") if rising else param("rain_decay_s"), dt)
	storm = approach(storm, float(tgt["storm"]), param("air_tau_s"), dt)
	fog = approach(fog, float(tgt["fog"]), param("air_tau_s"), dt)
	_manual_gust *= exp(-dt / param("gust_manual_decay_s"))
	_derive(t, dt)


func _derive(t: float, dt: float) -> void:
	time = t
	var g_det := smoothstep(0.60, 0.92, gust_noise(t)) * gustiness(wind_kn, storm)
	gust = maxf(g_det, _manual_gust)
	wind_inst_kn = wind_kn * (1.0 + param("gust_gain") * gust)
	wind_from_inst = fposmod(wind_from + param("gust_veer_deg") * gust * sin(0.37 * t), 360.0)
	var wt := vec_to(wind_from_inst + 180.0)
	adv += wt * (wind_inst_kn * KN_TO_MS * dt)
	sea = clampf(param("sea_wave_w") * wave_m / param("sea_wave_ref_m") + param("sea_wind_w") * wind_kn
			/ param("sea_wind_ref_kn") + param("sea_storm_w") * storm, 0.0, 1.0)
	rain_inst = clampf(rain * (1.0 + 0.25 * gust - 0.08), 0.0, 1.0)
	visibility_km = _clear_km * exp(-(_fog_coeff * fog + _rain_coeff * rain_inst))


## Wave height the renderer uses (presentation gain, a little pumping in a gust).
func wave_vis_m() -> float:
	return wave_m * param("wave_visual_gain") * (1.0 + 0.06 * gust)


func sea_name() -> String:
	return sea_class(sea, _p)


func wind_to() -> Vector2:
	return vec_to(wind_from_inst + 180.0)


func wind_ms() -> float:
	return wind_inst_kn * KN_TO_MS


## Extra boat speed from the sails drawing harder in a gust (a ratio, 0 .. gust_surge).
func gust_surge() -> float:
	return param("gust_surge") * gust


func to_dict() -> Dictionary:
	return {"wind_kn": wind_kn, "wind_inst_kn": wind_inst_kn, "wind_ms": wind_ms(), "wind_from": wind_from,
			"wind_from_inst": wind_from_inst, "wind_to": wind_to(), "wave_m": wave_m, "wave_vis_m": wave_vis_m(),
			"wave_to": wave_to, "gust": gust, "sea": sea, "sea_name": sea_name(), "rain": rain, "rain_inst": rain_inst,
			"storm": storm, "fog": fog, "visibility_km": visibility_km, "adv": adv, "crest_calm": param("crest_p_calm"),
			"crest_gale": param("crest_p_gale")}


# ---- pure helpers ------------------------------------------------------------------------------------------------
## Frame-rate independent exponential approach.
static func approach(current: float, target: float, tau: float, dt: float) -> float:
	if tau <= 0.0:
		return target
	return current + (target - current) * (1.0 - exp(-dt / tau))


static func wrap180(a: float) -> float:
	return fposmod(a + 540.0, 360.0) - 180.0


static func approach_angle(current: float, target: float, tau: float, dt: float) -> float:
	return fposmod(current + wrap180(target - current) * (1.0 - exp(-dt / maxf(tau, 0.000001))), 360.0)


## Unit vector (x east, y south) for a direction in compass degrees (clockwise from north).
static func vec_to(deg: float) -> Vector2:
	var a := deg_to_rad(deg)
	return Vector2(sin(a), -cos(a))


## Slowly varying 0..1 value whose peaks are the gusts (three incommensurate sines: no visible repeat, no randomness).
static func gust_noise(t: float) -> float:
	return 0.5 + 0.5 * (0.55 * sin(0.31 * t + 1.1) + 0.30 * sin(0.77 * t + 4.0) + 0.15 * sin(1.93 * t + 2.2))


## How gusty the wind is: none in light air, full from about 17 kn, a bit more in a storm.
static func gustiness(wind_kn_mean: float, storm_level: float) -> float:
	return clampf((wind_kn_mean - 3.0) / 14.0, 0.0, 1.0) * (0.75 + 0.25 * storm_level)


static func sea_class(sea_index: float, p: Dictionary) -> String:
	if sea_index < float(p["sea_calm_max"]):
		return "Calm"
	if sea_index < float(p["sea_breezy_max"]):
		return "Breezy"
	if sea_index < float(p["sea_rough_max"]):
		return "Rough"
	if sea_index < float(p["sea_storm_min"]):
		return "Gale"
	return "Storm"
