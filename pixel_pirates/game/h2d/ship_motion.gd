extends RefCounted
## The ship's answer to the sea (H2D-0.2): heave, pitch and roll from the water under the hull, plus the steady heel of
## the wind in the sails. The hull samples the SAME wave field the ocean shader draws (WaveModel.height_b) at five
## points (bow, stern, both rails, middle), so wave direction, height and the ship's own course decide the motion:
## head seas pitch it, beam seas roll it, following seas lift it gently. Damped springs give it weight. Spray events
## come from the water meeting the bow or a rail fast, never from a random timer. Only the DRAWN ship moves; the helm
## and the course do not. Twin of tools/h2d/env_logic.py (class Motion).
## All numbers: data/tuning/tuning_env.json (motion.*). NOT YET RUN IN GODOT.
const WaveModel := preload("res://h2d/wave_model.gd")
const PREFIX := "motion."
const SHIP_LEN := 22.0
const SHIP_BEAM := 6.2
const DEFAULTS := {
	"gain": 1.0, "roll_max_deg": 10.0, "pitch_max_deg": 6.0, "heave_max_m": 1.8, "roll_period_s": 3.4,
	"pitch_period_s": 2.6, "heave_period_s": 2.2, "damping": 0.6, "wave_follow": 0.8, "heel_deg_per_ms2": 0.04,
	"slam_bow_ms": 11.0, "slam_side_ms": 12.0, "slam_cooldown_calm_s": 4.0, "slam_cooldown_gale_s": 1.6,
	"slam_min_sea": 0.3,
}
const BOW := 0
const STARBOARD := 1
const PORT := 2

var heave := 0.0
var heave_v := 0.0
var pitch := 0.0  ## radians, + = bow up
var pitch_v := 0.0
var roll := 0.0  ## radians, + = starboard side down
var roll_v := 0.0
var slam := 0.0  ## 0..1 pulse that decays after a bow slam (drives the foam around the bow)
var events: Array = []  ## this step's spray events: [kind (BOW/STARBOARD/PORT), power 0..1]
var gain_override := -1.0  ## >= 0: the player's motion setting (key M) replaces motion.gain
var _p: Dictionary = DEFAULTS.duplicate()
var _prev: Array = []
var _cool: Array = [0.0, 0.0, 0.0]


func configure(values: Dictionary) -> void:
	_p = DEFAULTS.duplicate()
	for k in DEFAULTS.keys():
		var full: String = PREFIX + str(k)
		if values.has(full):
			_p[k] = float(values[full])


func param(key: String) -> float:
	return float(_p[key])


func reset() -> void:
	heave = 0.0
	heave_v = 0.0
	pitch = 0.0
	pitch_v = 0.0
	roll = 0.0
	roll_v = 0.0
	slam = 0.0
	events = []
	_prev = []
	_cool = [0.0, 0.0, 0.0]


## `b` = WaveModel.build(...). `c` = {x, z (ship position, scene metres), heading_deg, t (real seconds), wind_to (unit
## vector the wind blows towards), wind_ms, off_deg (angle between the bow and the wind source), no_go_deg, sea}.
func step(dt: float, b: Dictionary, c: Dictionary) -> void:
	var t: float = c["t"]
	var wind_to: Vector2 = c["wind_to"]
	var wind_ms: float = c["wind_ms"]
	var sea: float = c["sea"]
	var hd := deg_to_rad(float(c["heading_deg"]))
	var f := Vector2(sin(hd), -cos(hd))
	var s := Vector2(-f.y, f.x)  # starboard
	var pos := Vector2(float(c["x"]), float(c["z"]))
	var pts: Array[Vector2] = [
		pos + f * (SHIP_LEN * 0.38),
		pos + f * (SHIP_LEN * 0.10) + s * (SHIP_BEAM * 0.5),
		pos + f * (SHIP_LEN * 0.10) - s * (SHIP_BEAM * 0.5),
		pos - f * (SHIP_LEN * 0.38),
		pos,
	]
	var hs: Array[float] = []
	for p in pts:
		hs.append(WaveModel.height_b(b, p.x, p.y, t))
	var follow := param("wave_follow")
	var pitch_t := atan((hs[0] - hs[3]) / (SHIP_LEN * 0.76)) * follow
	var roll_t := atan((hs[2] - hs[1]) / SHIP_BEAM) * follow
	var heave_t := (hs[0] + hs[1] + hs[2] + hs[3] + hs[4]) / 5.0 * follow
	var side := wind_to.dot(s)
	var drive := clampf((float(c["off_deg"]) - float(c["no_go_deg"]) * 0.9) / 20.0, 0.0, 1.0)
	var heel := deg_to_rad(param("heel_deg_per_ms2") * wind_ms * wind_ms * side * drive)
	var r := _spring(roll, roll_v, roll_t + heel, param("roll_period_s"), dt)
	roll = r.x
	roll_v = r.y
	r = _spring(pitch, pitch_v, pitch_t, param("pitch_period_s"), dt)
	pitch = r.x
	pitch_v = r.y
	r = _spring(heave, heave_v, heave_t, param("heave_period_s"), dt)
	heave = r.x
	heave_v = r.y
	events = []
	slam *= exp(-dt / 0.7)
	for i in 3:
		_cool[i] = maxf(float(_cool[i]) - dt, 0.0)
	if not _prev.is_empty() and dt > 0.0 and sea >= param("slam_min_sea"):
		var cd := param("slam_cooldown_calm_s") + (param("slam_cooldown_gale_s") - param("slam_cooldown_calm_s")) * sea
		var thr: Array[float] = [param("slam_bow_ms"), param("slam_side_ms"), param("slam_side_ms")]
		for i in 3:
			var vrel := (hs[i] - float(_prev[i])) / dt
			if vrel > thr[i] and float(_cool[i]) <= 0.0:
				var power := clampf((vrel - thr[i]) / 9.0, 0.25, 1.0) * (0.5 + 0.5 * sea)
				events.append([i, power])
				_cool[i] = cd
				slam = maxf(slam, power if i == BOW else 0.5 * power)
	_prev = [hs[0], hs[1], hs[2]]


## What the sprite shows: soft-limited so a freak wave bends the ship but never flips it, times the player's setting.
func out() -> Dictionary:
	var g := gain_override if gain_override >= 0.0 else param("gain")
	return {"roll_deg": _soft(rad_to_deg(roll), param("roll_max_deg")) * g,
			"pitch_deg": _soft(rad_to_deg(pitch), param("pitch_max_deg")) * g,
			"heave_m": _soft(heave, param("heave_max_m")) * g}


static func _soft(x: float, m: float) -> float:
	return m * tanh(x / m)


## Damped spring towards `target`, advanced in steps of at most 1/90 s. Returns Vector2(position, velocity).
static func _spring(x: float, v: float, target: float, period: float, zeta: float, dt: float) -> Vector2:
	var w := TAU / period
	var n := maxi(1, ceili(dt / (1.0 / 90.0)))
	var h := dt / float(n)
	for i in n:
		v += (w * w * (target - x) - 2.0 * zeta * w * v) * h
		x += v * h
	return Vector2(x, v)
