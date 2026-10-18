extends RefCounted
## How the drawn sail answers the wind (H2D-0.3). Twin of tools/h2d/sail_logic.py (tests/fixtures/sail_cases.json).
## H2D-0.2 had no state: a fixed belly from the wind speed plus a constant 2 Hz sine, so a sail shivered in light
## air, looked the same in every breeze and never settled. This model has state:
##   fill   how full the sail is: a damped spring (period 2.8 s) towards a target from wind speed, angle to the wind
##          (luffing, close-hauled, reaching, running), a gale (taut and flat) and a gust (fills, overshoots, settles).
##   flap   flutter amplitude: only while luffing with wind in the sail, or briefly when a gust ARRIVES. It builds in
##          0.6 s, fades over 1.4 s, and its rate follows the wind and wanders irregularly.
##   breath sub-pixel, never repeating, slow drift in light air.
## The shader (ship.gdshader) turns belly and flap into whole-pixel steps per 3-pixel band so the pixel art stays crisp.
## All numbers: data/tuning/tuning_env.json (sail.*). NOT YET RUN IN GODOT.
const PREFIX := "sail."
const DEFAULTS := {
	"fill_period_s": 2.8, "fill_zeta": 0.55, "max_belly_px": 2.2, "light_air_kn": 2.0, "full_air_kn": 14.0,
	"gust_fill": 0.35, "gale_flat": 0.35, "flap_max_px": 1.0, "flap_rise_s": 0.6, "flap_fall_s": 1.4,
	"flap_hz_base": 0.4, "flap_hz_per_kn": 0.025, "flap_gust_gain": 0.6, "breath_px": 0.45, "breath_period_s": 6.0,
}

var fill := 0.0
var fill_v := 0.0
var flap := 0.0
var phase := 0.0
var rise := 0.0
var luff := 0.0
var slack := 1.0
var breath := 0.0
var _gust_prev := 0.0
var _first := true
var _p: Dictionary = DEFAULTS.duplicate()


func configure(values: Dictionary) -> void:
	_p = DEFAULTS.duplicate()
	for k in DEFAULTS.keys():
		var full: String = PREFIX + str(k)
		if values.has(full):
			_p[k] = float(values[full])


func param(key: String) -> float:
	return float(_p[key])


## Returns [luff 0..1, fill target].
func targets(wind_kn: float, gust: float, off_deg: float, no_go_deg: float) -> Array:
	var lf := 1.0 - smoothstep(no_go_deg - 4.0, no_go_deg + 14.0, off_deg)
	var wind_k := smoothstep(param("light_air_kn"), param("full_air_kn"), wind_kn)
	var angle_k := 0.55 + 0.45 * sin(deg_to_rad(clampf(off_deg, 0.0, 180.0)))
	var flat := 1.0 - param("gale_flat") * smoothstep(24.0, 42.0, wind_kn)
	return [lf, (1.0 - lf) * wind_k * angle_k * flat * (1.0 + param("gust_fill") * gust)]


func reset() -> void:
	_first = true
	flap = 0.0
	rise = 0.0
	fill_v = 0.0


## `wind_kn` is the wind in the sail now (gust included), `gust` 0..1, `off_deg` the bow's angle to the wind.
func step(dt: float, wind_kn: float, gust: float, off_deg: float, no_go_deg: float, t: float) -> void:
	if _first:
		var s0 := targets(wind_kn, gust, off_deg, no_go_deg)
		fill = s0[1]
		fill_v = 0.0
		luff = s0[0]
		_gust_prev = gust
		rise = 0.0
		flap = 0.0
		_first = false
	var tg := targets(wind_kn, gust, off_deg, no_go_deg)
	luff = tg[0]
	var wn := param("fill_period_s")
	var r := _spring(fill, fill_v, tg[1], wn, param("fill_zeta"), dt)
	fill = r[0]
	fill_v = r[1]
	var wind_k := smoothstep(param("light_air_kn"), param("full_air_kn"), wind_kn)
	slack = 1.0 - wind_k
	if dt > 0.0:
		var raw := clampf((gust - _gust_prev) / dt, 0.0, 3.0)
		rise += (raw - rise) * (1.0 - exp(-dt / 0.6))
	_gust_prev = gust
	var gust_shiver := param("flap_gust_gain") * rise * wind_k * (1.0 - luff)
	var ft := clampf(luff * smoothstep(1.5, 9.0, wind_kn) + gust_shiver, 0.0, 1.0)
	var tau := param("flap_rise_s") if ft > flap else param("flap_fall_s")
	flap = _approach(flap, ft, tau, dt)
	var hz := param("flap_hz_base") + param("flap_hz_per_kn") * wind_kn
	phase += TAU * hz * dt * (0.75 + 0.5 * wander(t * 0.31))
	var per := param("breath_period_s")
	breath = 0.5 * (sin(TAU * t / per + 1.3) + sin(TAU * t / (per * 1.73) + 0.4))


## belly_px (signed, + = towards the lee), flap_px (amplitude), flap_phase, luff, fill, slack.
func out() -> Dictionary:
	var belly := param("max_belly_px") * clampf(fill, 0.0, 1.1) + param("breath_px") * slack * breath
	return {"belly_px": belly, "flap_px": param("flap_max_px") * flap, "flap_phase": phase, "luff": luff,
			"fill": fill, "slack": slack}


## Irregular 0..1 value that never repeats (three incommensurate sines).
static func wander(t: float) -> float:
	return 0.5 + 0.5 * (0.5 * sin(1.7 * t + 0.3) + 0.3 * sin(0.93 * t + 2.1) + 0.2 * sin(2.9 * t + 4.4))


static func _approach(current: float, target: float, tau: float, dt: float) -> float:
	if tau <= 0.0:
		return target
	return current + (target - current) * (1.0 - exp(-dt / tau))


## Damped spring towards `target`, advanced in steps of at most 1/90 s. Returns [position, velocity].
static func _spring(x: float, v: float, target: float, period: float, zeta: float, dt: float) -> Array:
	var w := TAU / period
	var n := maxi(1, ceili(dt / (1.0 / 90.0)))
	var h := dt / float(n)
	for i in n:
		v += (w * w * (target - x) - 2.0 * zeta * w * v) * h
		x += v * h
	return [x, v]
