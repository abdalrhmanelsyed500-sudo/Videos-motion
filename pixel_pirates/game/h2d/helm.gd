extends RefCounted
## The helm: what A and D do to the ship. Pure logic (no nodes), so it can be tested without a screen.
##   keys -> rudder (the helm goes over smoothly) -> yaw rate (hull inertia) -> heading
##   sails -> speed the sails could give at this heading -> actual speed (momentum, so speed rises and falls gradually)
## Every number comes from data/tuning/tuning_helm.json (keys helm.*); DEFAULTS only covers a missing key and is
## checked against the JSON by tests/test_helm.gd. The wind, the polar (sails) and the world position stay in
## core/ocean.gd and core/sea_state.gd, unchanged: this only shapes how the ship answers the player.
## Twin of tools/h2d/helm_logic.py. NOT YET RUN IN GODOT.
const PREFIX := "helm."
const DEFAULTS := {
	"max_turn_deg_s": 36.0, "min_steerage": 0.45, "steerage_full_kn": 3.0, "rudder_rise_s": 0.12,
	"rudder_return_s": 0.1, "yaw_build_s": 0.18, "yaw_brake_s": 0.1, "speed_gain_s": 2.5, "speed_loss_s": 3.5,
}
const SENS_MIN := 0.4
const SENS_MAX := 2.0

var heading_deg := 0.0
var yaw_rate := 0.0  ## degrees per second, positive = turning to starboard (clockwise seen from above)
var rudder := 0.0  ## -1 hard to port .. +1 hard to starboard: what the helm indicator shows
var speed_kn := 0.0  ## speed through the water now (lags the target)
var sensitivity := 1.0  ## player setting, multiplies the turn rate
var _p: Dictionary = DEFAULTS.duplicate()


## `values` is a tuning dictionary {key: value}; keys without the helm. prefix are ignored.
func configure(values: Dictionary) -> void:
	_p = DEFAULTS.duplicate()
	for k in DEFAULTS.keys():
		var full: String = PREFIX + str(k)
		if values.has(full):
			_p[k] = float(values[full])


func param(key: String) -> float:
	return float(_p[key])


func reset(heading: float, speed: float) -> void:
	heading_deg = fposmod(heading, 360.0)
	yaw_rate = 0.0
	rudder = 0.0
	speed_kn = speed


func set_sensitivity(value: float) -> void:
	sensitivity = clampf(value, SENS_MIN, SENS_MAX)


## 1.0 when the rudder bites fully, min_steerage when the ship has lost all way.
func steerage(at_speed_kn: float) -> float:
	var k := clampf(at_speed_kn / maxf(param("steerage_full_kn"), 0.01), 0.0, 1.0)
	return param("min_steerage") + (1.0 - param("min_steerage")) * k


## `steer` is -1 (A, port) .. +1 (D, starboard); `target_speed_kn` is what the sails give at the current heading.
func step(dt: float, steer: float, target_speed_kn: float) -> void:
	var s := clampf(steer, -1.0, 1.0)
	var tau_r := param("rudder_rise_s")
	if s * rudder < 0.0 or absf(s) <= absf(rudder):
		tau_r = param("rudder_return_s")
	rudder = approach(rudder, s, tau_r, dt)
	var want := rudder * param("max_turn_deg_s") * sensitivity * steerage(speed_kn)
	var tau_y := param("yaw_build_s") if absf(want) > absf(yaw_rate) else param("yaw_brake_s")
	yaw_rate = approach(yaw_rate, want, tau_y, dt)
	heading_deg = fposmod(heading_deg + yaw_rate * dt, 360.0)
	var tau_s := param("speed_gain_s") if target_speed_kn > speed_kn else param("speed_loss_s")
	speed_kn = approach(speed_kn, target_speed_kn, tau_s, dt)


## Frame-rate independent exponential approach.
static func approach(current: float, target: float, tau: float, dt: float) -> float:
	if tau <= 0.0:
		return target
	return current + (target - current) * (1.0 - exp(-dt / tau))


static func wrap180(a: float) -> float:
	return fposmod(a + 180.0, 360.0) - 180.0


## Angle between the bow and the wind source, 0 = straight into the wind, 180 = running dead downwind.
static func off_wind_deg(heading: float, wind_from_deg: float) -> float:
	return absf(wrap180(heading - wind_from_deg))


## Name of the point of sail for an angle off the wind (see docs/H2D0_1_SAILING_AND_COMPAT.md).
static func point_of_sail(off_deg: float, no_go_deg: float) -> String:
	if off_deg < no_go_deg:
		return "In irons"
	if off_deg < 55.0:
		return "Close-hauled"
	if off_deg < 80.0:
		return "Close reach"
	if off_deg < 110.0:
		return "Beam reach"
	if off_deg < 155.0:
		return "Broad reach"
	return "Running"


## Which key gets the bow out of the no-go zone fastest: -1 = A (port), +1 = D (starboard). A bow already clockwise
## of the wind source keeps turning clockwise (D), one anticlockwise of it keeps turning anticlockwise (A).
static func escape_direction(heading: float, wind_from_deg: float) -> int:
	return 1 if wrap180(heading - wind_from_deg) >= 0.0 else -1
