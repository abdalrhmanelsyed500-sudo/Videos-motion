extends RefCounted
## CP-2 Release A: COURSE HOLD (the autopilot). Pure logic (tests/test_ship_autopilot.gd steers the real helm model with it).
## It does not touch the ship's speed: the sails still decide that (helm.gd target speed). It only produces the same -1 .. +1
## steer axis the A and D keys produce, so the rudder, the turn rate and the heading all behave exactly as with the hands on
## the wheel, and a ship left alone keeps its heading and sails at the speed the wind allows on that heading.
##   steer = clamp(kp * error - kd * yaw_rate), error = wanted heading - heading (shortest way round)
## The wanted heading is the LATCHED heading, with one safety: if it points into the wind (inside the no-go wedge, plus a margin)
## the ship holds the nearest heading it can sail, so the ship never stalls in irons while nobody is steering.
## Pressing A or D while the hold is on steers by hand; when the keys are released the hold takes the new heading after the ship
## has stopped turning (settle_s), so a correction is a one-tap job and the hold never fights the player.
## Every number is in data/tuning/tuning_ship.json (keys autopilot.*); DEFAULTS only covers a missing key.
## NOT YET RUN ON THE USER'S PC.
const PREFIX := "autopilot."
const DEFAULTS := {"kp": 0.12, "kd": 0.04, "deadband_deg": 0.5, "settle_s": 0.6, "irons_margin_deg": 6.0, "relatch_yaw_deg_s": 2.0}

var engaged := false
var target_deg := 0.0           ## the latched heading
var adjusted := false           ## true while the hold is steering a different heading than the latched one (to keep the sails drawing)
var manual_override := false    ## true while the player steers by hand (the hold waits)
var _p: Dictionary = DEFAULTS.duplicate()
var _settle := 0.0


func configure(values: Dictionary) -> void:
	_p = DEFAULTS.duplicate()
	for k in DEFAULTS.keys():
		var full: String = PREFIX + str(k)
		if values.has(full):
			_p[k] = float(values[full])


func param(key: String) -> float:
	return float(_p[key])


static func wrap180(a: float) -> float:
	return fposmod(a + 180.0, 360.0) - 180.0


## Hold the heading the ship has now. Returns the heading that is really held (it may differ if the latch was inside the no-go wedge).
func engage(heading_deg: float, wind_from_deg: float, wind_kn: float, no_go_deg: float) -> float:
	engaged = true
	target_deg = fposmod(heading_deg, 360.0)
	manual_override = false
	_settle = 0.0
	var eff := effective_target(wind_from_deg, wind_kn, no_go_deg)
	adjusted = absf(wrap180(eff - target_deg)) > 0.5
	if adjusted:
		target_deg = eff
		adjusted = false
	return target_deg


func release() -> void:
	engaged = false
	adjusted = false
	manual_override = false
	_settle = 0.0


## Change the held course by hand (the helm menu, the compass keys): sets the latch directly.
func set_course(deg: float) -> void:
	target_deg = fposmod(deg, 360.0)


## The heading the ship will really steer: the latched one, or the nearest sailable heading when the latch is in the wedge.
func effective_target(wind_from_deg: float, wind_kn: float, no_go_deg: float) -> float:
	if wind_kn <= 3.0:
		return target_deg
	var lim := no_go_deg + float(_p["irons_margin_deg"])
	var rel := wrap180(target_deg - wind_from_deg)
	if absf(rel) >= lim:
		return target_deg
	var side := 1.0 if rel >= 0.0 else -1.0
	return fposmod(wind_from_deg + side * lim, 360.0)


## One frame. `manual` is the steer axis from the keys (-1 .. +1). Returns the steer axis to give the helm.
func steer(dt: float, manual: float, heading_deg: float, yaw_rate_deg_s: float, wind_from_deg: float, wind_kn: float,
		no_go_deg: float) -> float:
	if not engaged:
		return manual
	if absf(manual) > 0.05:
		manual_override = true
		_settle = float(_p["settle_s"])
		return manual
	if manual_override:
		_settle = maxf(_settle - dt, 0.0)
		if _settle > 0.0 or absf(yaw_rate_deg_s) > float(_p["relatch_yaw_deg_s"]):
			return 0.0
		manual_override = false
		target_deg = fposmod(heading_deg, 360.0)
	var eff := effective_target(wind_from_deg, wind_kn, no_go_deg)
	adjusted = absf(wrap180(eff - target_deg)) > 0.5
	var err := wrap180(eff - heading_deg)
	if absf(err) < float(_p["deadband_deg"]) and absf(yaw_rate_deg_s) < 1.0:
		return 0.0
	return clampf(float(_p["kp"]) * err - float(_p["kd"]) * yaw_rate_deg_s, -1.0, 1.0)
