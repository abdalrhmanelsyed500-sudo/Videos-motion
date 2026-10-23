extends RefCounted
## H2D-1 docking: the harbour's rules as pure logic (no nodes), so they can be tested without a screen.
##   SPACE inside the dock zone -> the ship is taken along a smooth assisted path (current position -> approach point ->
##   north along the berth lane) and moored port side to the pier. SPACE again casts off: it backs out stern-first to
##   the approach point, turns to face the sea (heading 180) and the player has the helm again.
##   Near the berth the whole scene speed is eased (speed_scale), because the scene runs ~5x faster than the real
##   knots (5 kn = 24.7 m/s on screen) and a harbour could not be entered at that pace.
## All the maths uses plain floats (not Vector2, which is single precision) so the Python twin tools/h2d/harbor_logic.py
## reproduces it to 1e-6. Every number is in data/tuning/tuning_harbor.json (keys harbor.*); DEFAULTS only covers a
## missing key and is checked against the JSON by tests/test_harbor.gd. NOT YET RUN IN GODOT.
enum { SAILING, DOCKING, DOCKED, UNDOCKING }
const PREFIX := "harbor."
const DEFAULTS := {
	"dock_speed_ms": 5.0, "dock_min_s": 6.0, "dock_max_s": 16.0, "undock_speed_ms": 3.5, "undock_min_s": 6.0,
	"turn_out_s": 3.0, "head_turn_frac": 0.12, "ease_min": 0.3, "ease_near_m": 40.0, "ease_far_m": 110.0,
	"hint_radius_m": 260.0, "half_len_m": 10.0, "side_m": 2.4, "ground_limit_m": 0.3,
}
const STATE_NAMES: Array[String] = ["sailing", "docking", "docked", "undocking"]
const COMPASS: Array[String] = ["north", "north-east", "east", "south-east", "south", "south-west", "west",
		"north-west"]

var state := SAILING
var port_name := "Port Marlin"   # FM-1: display name; Identity.home_port is the canonical source at runtime
var berth_x := 21.4
var berth_z := 21.0
var berth_heading := 0.0
var approach_x := 21.4
var approach_z := 56.0
var zone_x0 := 2.0
var zone_z0 := 42.0
var zone_x1 := 44.0
var zone_z1 := 100.0
var _p: Dictionary = DEFAULTS.duplicate()
var _t := 0.0
var _dur := 1.0
var _phase := 0  ## undocking: 0 reversing out, 1 turning to face the sea
var _x0 := 0.0
var _z0 := 0.0
var _h0 := 0.0


## `layout` is the "harbor_layout" dictionary of anvil_cay.json; `values` a tuning dictionary {key: value}.
func configure(layout: Dictionary, values: Dictionary, p_name: String = "Port Marlin") -> void:
	_p = DEFAULTS.duplicate()
	for k in DEFAULTS.keys():
		var full: String = PREFIX + str(k)
		if values.has(full):
			_p[k] = float(values[full])
	port_name = p_name
	var b: Dictionary = layout["berth"]
	berth_x = float(b["x"])
	berth_z = float(b["z"])
	berth_heading = float(b["heading_deg"])
	var a: Dictionary = layout["approach"]
	approach_x = float(a["x"])
	approach_z = float(a["z"])
	var z: Dictionary = layout["dock_zone"]
	zone_x0 = float(z["x0"])
	zone_z0 = float(z["z0"])
	zone_x1 = float(z["x1"])
	zone_z1 = float(z["z1"])


func param(key: String) -> float:
	return float(_p[key])


func reset() -> void:
	state = SAILING
	_t = 0.0
	_phase = 0


static func wrap180(a: float) -> float:
	return fposmod(a + 180.0, 360.0) - 180.0


static func bearing_deg(dx: float, dz: float) -> float:
	return fposmod(rad_to_deg(atan2(dx, -dz)), 360.0)


static func smootherstep(u: float) -> float:
	var c := clampf(u, 0.0, 1.0)
	return c * c * c * (c * (c * 6.0 - 15.0) + 10.0)


func in_zone(x: float, z: float) -> bool:
	return x >= zone_x0 and x <= zone_x1 and z >= zone_z0 and z <= zone_z1


func dist_to_berth(x: float, z: float) -> float:
	return sqrt((x - berth_x) * (x - berth_x) + (z - berth_z) * (z - berth_z))


## Scene-speed multiplier near the berth: ease_min right at the pier, 1.0 beyond ease_far_m. Only while sailing.
func speed_scale(x: float, z: float) -> float:
	if state != SAILING:
		return 1.0
	var s := smoothstep(param("ease_near_m"), param("ease_far_m"), dist_to_berth(x, z))
	return param("ease_min") + (1.0 - param("ease_min")) * s


## The points of the hull that must be over water: bow, stern, centre and four on the sides (+-side_m).
func footprint(x: float, z: float, heading_deg: float) -> Array:
	var a := deg_to_rad(heading_deg)
	var fx := sin(a)
	var fz := -cos(a)
	var sx := -fz
	var sz := fx
	var hl := param("half_len_m")
	var sd := param("side_m")
	var pts: Array = []
	for off in [[hl, 0.0], [-hl, 0.0], [0.0, 0.0], [hl * 0.4, sd], [hl * 0.4, -sd], [-hl * 0.4, sd], [-hl * 0.4, -sd]]:
		pts.append([x + fx * float(off[0]) + sx * float(off[1]), z + fz * float(off[0]) + sz * float(off[1])])
	return pts


## SPACE. Returns "docking", "casting_off", "not_in_zone" or "busy".
func request(x: float, z: float, heading_deg: float) -> String:
	if state == SAILING:
		if not in_zone(x, z):
			return "not_in_zone"
		state = DOCKING
		_t = 0.0
		_x0 = x
		_z0 = z
		_h0 = heading_deg
		var path_len := _bez_len(x, z)
		_dur = clampf(path_len / param("dock_speed_ms"), param("dock_min_s"), param("dock_max_s"))
		return "docking"
	if state == DOCKED:
		state = UNDOCKING
		_t = 0.0
		_phase = 0
		var out_len := sqrt((approach_x - berth_x) * (approach_x - berth_x) + (approach_z - berth_z) * (approach_z - berth_z))
		_dur = maxf(out_len / param("undock_speed_ms"), param("undock_min_s"))
		return "casting_off"
	return "busy"


## Quadratic Bezier from the start, through the approach point as control, to the berth. Its end tangent is the
## approach -> berth direction (north), so the ship slides in straight along the pier.
func bezier_point(u: float) -> Array:
	var v := 1.0 - u
	var px := v * v * _x0 + 2.0 * v * u * approach_x + u * u * berth_x
	var pz := v * v * _z0 + 2.0 * v * u * approach_z + u * u * berth_z
	return [px, pz]


func bezier_tangent(u: float) -> Array:
	var tx := 2.0 * (1.0 - u) * (approach_x - _x0) + 2.0 * u * (berth_x - approach_x)
	var tz := 2.0 * (1.0 - u) * (approach_z - _z0) + 2.0 * u * (berth_z - approach_z)
	if tx * tx + tz * tz < 0.000001:
		tx = berth_x - approach_x
		tz = berth_z - approach_z
	return [tx, tz]


func _bez_len(x: float, z: float) -> float:
	_x0 = x
	_z0 = z
	var total := 0.0
	var prev := bezier_point(0.0)
	for i in range(1, 17):
		var q := bezier_point(float(i) / 16.0)
		total += sqrt(((q[0] as float) - (prev[0] as float)) * ((q[0] as float) - (prev[0] as float))
				+ ((q[1] as float) - (prev[1] as float)) * ((q[1] as float) - (prev[1] as float)))
		prev = q
	return total


## Advances the manoeuvre. Returns {"x", "z", "heading", "moor", "state", "done"}; `moor` is 0 (under way) to 1
## (moored: sails slack, no wake). `done` is true on the frame a manoeuvre ends (docked, or free to sail again).
func step(dt: float) -> Dictionary:
	if state == DOCKING:
		_t += dt
		var ul := clampf(_t / _dur, 0.0, 1.0)
		var u := smootherstep(ul)
		var p := bezier_point(u)
		var tg := bezier_tangent(u)
		var tb := bearing_deg(float(tg[0]), float(tg[1]))
		var w := smoothstep(0.0, param("head_turn_frac"), ul)
		var hd := fposmod(_h0 + wrap180(tb - _h0) * w, 360.0)
		var done := ul >= 1.0
		if done:
			state = DOCKED
			hd = berth_heading
			p = [berth_x, berth_z]
		return {"x": float(p[0]), "z": float(p[1]), "heading": hd, "moor": smoothstep(0.7, 1.0, ul), "state": state,
				"done": done}
	if state == DOCKED:
		return {"x": berth_x, "z": berth_z, "heading": berth_heading, "moor": 1.0, "state": state, "done": false}
	if state == UNDOCKING:
		_t += dt
		if _phase == 0:
			var ul := clampf(_t / _dur, 0.0, 1.0)
			var u := smootherstep(ul)
			var out := {"x": berth_x + (approach_x - berth_x) * u, "z": berth_z + (approach_z - berth_z) * u,
					"heading": berth_heading, "moor": 1.0 - smoothstep(0.0, 0.3, ul), "state": state, "done": false}
			if ul >= 1.0:
				_phase = 1
				_t = 0.0
			return out
		var ul2 := clampf(_t / param("turn_out_s"), 0.0, 1.0)
		var hd2 := fposmod(berth_heading + 180.0 * smootherstep(ul2), 360.0)
		var done2 := ul2 >= 1.0
		if done2:
			state = SAILING
			hd2 = fposmod(berth_heading + 180.0, 360.0)
		return {"x": approach_x, "z": approach_z, "heading": hd2, "moor": 0.0, "state": state, "done": done2}
	return {"x": 0.0, "z": 0.0, "heading": 0.0, "moor": 0.0, "state": state, "done": false}


## What the HUD shows: distance, bearing and the plain-language prompt.
func prompt(x: float, z: float) -> Dictionary:
	var dist := dist_to_berth(x, z)
	var brg := bearing_deg(berth_x - x, berth_z - z)
	var text := ""
	var near := dist <= param("hint_radius_m")
	match state:
		DOCKED:
			text = "Moored at %s. Press SPACE to cast off." % port_name
		DOCKING:
			text = "Docking: the crew is bringing her alongside..."
		UNDOCKING:
			text = "Casting off: backing out of the berth..."
		_:
			if in_zone(x, z):
				text = "%s: press SPACE to dock." % port_name
			elif near:
				text = "%s berth: %d m %s. Steer into the harbour mouth (the dock zone, between the buoys), then press SPACE." % [
						port_name, int(roundf(dist)), COMPASS[int(floorf(brg / 45.0 + 0.5)) % 8]]
	return {"state": state, "text": text, "dist": dist, "bearing": brg, "near": near,
			"can_dock": state == SAILING and in_zone(x, z)}
