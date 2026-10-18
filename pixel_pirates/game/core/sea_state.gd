extends RefCounted
## Ship position integrator for the E1 vertical slice. Python twin: tools/data_tools/sea_state.py
## (golden scenarios in tests/fixtures/sea_cases.json). Pure arithmetic over core/ocean.gd: heading and wind give a
## ground velocity, the world clock gives the elapsed game seconds, the position moves. It owns NO clock: whoever
## ticks the world clock passes the game seconds in, so pausing the clock stops the ship (T1 rule).
## The full ocean sample is refreshed every SAMPLE_INTERVAL_S game seconds (15 game minutes = 9.4 real seconds). Weather
## changes over hours and tens of kilometres, so this is invisible and keeps the per-frame cost near zero.
const KN_KMH := 1.852
const SAMPLE_INTERVAL_S := 900.0
const SUBSTEP_S := 600.0

var ocean: RefCounted
var x_km: float = 7000.0
var y_km: float = 2650.0
var heading_deg: float = 0.0
var distance_km: float = 0.0
var last_sample: Dictionary = {}
var sample_t_days: float = -1.0e9


func _init(p_ocean: RefCounted) -> void:
	ocean = p_ocean


func place(p_x_km: float, p_y_km: float, p_heading_deg: float) -> void:
	x_km = p_x_km
	y_km = p_y_km
	heading_deg = p_heading_deg
	last_sample = {}


## Sample the sea at the ship's position now (for the HUD before the first step, and after a debug jump).
func refresh(t_days: float) -> void:
	last_sample = ocean.sample(x_km, y_km, t_days)
	sample_t_days = t_days


## Move the ship for game_seconds, starting at world time t_start_days.
func advance(t_start_days: float, game_seconds: float) -> void:
	var left := game_seconds
	var t := t_start_days
	while left > 0.0:
		var dt := minf(left, SUBSTEP_S)
		if last_sample.is_empty() or t - sample_t_days >= SAMPLE_INTERVAL_S / 86400.0:
			last_sample = ocean.sample(x_km, y_km, t)
			sample_t_days = t
		var v: Array = ocean.ground_velocity_kmh(heading_deg, last_sample)
		var h := dt / 3600.0
		var nx := clampf(x_km + float(v[0]) * h, 0.0, ocean.world_w)
		var ny := clampf(y_km + float(v[1]) * h, 0.0, ocean.world_h)
		distance_km += sqrt((nx - x_km) * (nx - x_km) + (ny - y_km) * (ny - y_km))
		x_km = nx
		y_km = ny
		t += dt / 86400.0
		left -= dt


## Speed through the water in knots (0 before the first sample).
func speed_kn() -> float:
	if last_sample.is_empty():
		return 0.0
	var smp: Dictionary = last_sample
	var kmh: float = ocean.speed_through_water_kmh(
			heading_deg, float(smp["wind_kn"]), float(smp["wind_from_deg"]), float(smp["ice"]))
	return kmh / KN_KMH
