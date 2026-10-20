# gdlint: disable=class-definitions-order
extends RefCounted
## CP-2 Release A: the pirate walking aboard the moving ship. Pure logic (tests/test_ship_walker.gd runs it headless).
## The position is SHIP-LOCAL (u along the ship, v to starboard, see ship_layout.gd), so the ship's motion can never push the
## walker through a wall or off the deck: the walker is carried because it lives in the ship's own frame. The keys are read
## in SCREEN directions (up = north, like on land), turned into ship directions with the heading, and moved with the same
## walk / run feel and the same walk-cycle frames as the land walker (land_walker.gd). Collision, sliding and "unstick" are
## done against ShipLayout.walkable(). Level changes (hatch, ladder) are a short scripted transit with a fade at the midpoint;
## the rope ladder is a climb along a line that a key (or just E) drives up or down.
## Every number is in data/tuning/tuning_ship.json (keys deck.*); DEFAULTS only covers a missing key.
## NOT YET RUN ON THE USER'S PC.
const Layout := preload("res://h2d/ship_layout.gd")
const Land := preload("res://h2d/land_walker.gd")
enum Mode { WALK, CLIMB, TRANSIT }
const PREFIX := "deck."
const DEFAULTS := {
	"walk_ms": 3.4, "run_ms": 6.0, "speedup_s": 0.1, "body_r_m": 0.38, "stride_m": 0.8, "climb_s": 3.2, "transit_s": 0.8,
}

var layout: RefCounted = Layout.new()
var level := Layout.L_DECK
var u := Layout.HELM_LEAVE.x
var v := Layout.HELM_LEAVE.y
var row := Land.ROW_NORTH
var frame := 0
var speed_ms := 0.0
var distance_m := 0.0
var mode := Mode.WALK
var climb_t := 0.0
var climb_dir := 0
var transit_t := 0.0
var _p: Dictionary = DEFAULTS.duplicate()
var _phase := 0.0
var _t_from := Vector2.ZERO
var _t_via := Vector2.ZERO
var _t_dest := Vector2.ZERO
var _t_level := 0


func configure(values: Dictionary, p_layout: RefCounted = null) -> void:
	_p = DEFAULTS.duplicate()
	for k in DEFAULTS.keys():
		var full: String = PREFIX + str(k)
		if values.has(full):
			_p[k] = float(values[full])
	if p_layout != null:
		layout = p_layout


func param(key: String) -> float:
	return float(_p[key])


func pos() -> Vector2:
	return Vector2(u, v)


func place(p_level: int, p: Vector2) -> void:
	level = p_level
	u = p.x
	v = p.y
	speed_ms = 0.0
	frame = 0
	_phase = 0.0
	mode = Mode.WALK
	climb_t = 0.0
	climb_dir = 0
	transit_t = 0.0


## The pirate stands beside the wheel (used when leaving the helm, boarding and resets).
func place_at_helm() -> void:
	place(Layout.L_DECK, Layout.HELM_LEAVE)
	row = Land.ROW_NORTH


func is_busy() -> bool:
	return mode != Mode.WALK


## Height of the feet above the floor of the current level (climbing the rope ladder).
func height_above_floor() -> float:
	if mode == Mode.CLIMB:
		return Layout.ladder_point(climb_t).z
	return 0.0


## 0 .. 1: how dark the screen is during a hatch transit (peaks at the midpoint, when the level changes).
func fade_amount() -> float:
	if mode != Mode.TRANSIT:
		return 0.0
	var k := 1.0 - absf(transit_t * 2.0 - 1.0)
	return clampf(k * 1.6, 0.0, 1.0)


## The ship-local position of the feet while climbing; otherwise the walking position.
func feet_local() -> Vector2:
	if mode == Mode.CLIMB:
		var lp := Layout.ladder_point(climb_t)
		return Vector2(lp.x, lp.y)
	return Vector2(u, v)


## Turn a screen direction (x east, y south) into ship-local (u forward, v starboard).
static func to_local(dir: Vector2, heading_deg: float) -> Vector2:
	var a := deg_to_rad(heading_deg)
	var f := Vector2(sin(a), -cos(a))
	var sb := Vector2(cos(a), sin(a))
	return Vector2(dir.dot(f), dir.dot(sb))


## Turn a ship-local offset into a world offset (x east, z south).
static func to_world(local: Vector2, heading_deg: float) -> Vector2:
	var a := deg_to_rad(heading_deg)
	var f := Vector2(sin(a), -cos(a))
	var sb := Vector2(cos(a), sin(a))
	return f * local.x + sb * local.y


# ---- level changes --------------------------------------------------------------------------------------------------
## Go through a hatch: walk to `via`, fade, appear at `dest` on `to_level`.
func start_transit(to_level: int, via: Vector2, dest: Vector2) -> bool:
	if mode != Mode.WALK:
		return false
	mode = Mode.TRANSIT
	transit_t = 0.0
	_t_from = Vector2(u, v)
	_t_via = via
	_t_dest = dest
	_t_level = to_level
	speed_ms = 0.0
	frame = 0
	return true


## Start the rope ladder: dir +1 from the foot of the ladder (main deck), -1 from the crow's nest.
func start_climb(dir: int) -> bool:
	if mode != Mode.WALK:
		return false
	if dir > 0 and level == Layout.L_DECK:
		climb_t = 0.0
	elif dir < 0 and level == Layout.L_NEST:
		climb_t = 1.0
		level = Layout.L_DECK
	else:
		return false
	mode = Mode.CLIMB
	climb_dir = dir
	speed_ms = 0.0
	_phase = 0.0
	row = Land.ROW_NORTH
	return true


## Finish whatever scripted movement is running at once and stand somewhere safe (a scene change, a reset).
func settle() -> void:
	if mode == Mode.TRANSIT:
		level = _t_level
		u = _t_dest.x
		v = _t_dest.y
	elif mode == Mode.CLIMB:
		if climb_t >= 0.5:
			level = Layout.L_NEST
			u = Layout.NEST_ARRIVE.x
			v = Layout.NEST_ARRIVE.y
		else:
			level = Layout.L_DECK
			u = Layout.LADDER_LAND.x
			v = Layout.LADDER_LAND.y
	mode = Mode.WALK
	transit_t = 0.0
	climb_dir = 0
	speed_ms = 0.0
	frame = 0


# ---- the step ------------------------------------------------------------------------------------------------------
## dir: screen direction from the keys (x east, y south). climb_in: +1 up (W), -1 down (S) while on the ladder, else 0.
## Returns true when the walker moved.
func step(dt: float, dir: Vector2, run: bool, heading_deg: float, climb_in: float = 0.0) -> bool:
	if mode == Mode.TRANSIT:
		_step_transit(dt)
		return false
	if mode == Mode.CLIMB:
		_step_climb(dt, climb_in)
		return false
	_unstick()
	var want := Vector2.ZERO
	if dir.length() > 0.01:
		want = dir.normalized()
	var top: float = float(_p["run_ms"]) if run else float(_p["walk_ms"])
	var target := top * minf(dir.length(), 1.0)
	var acc: float = maxf(float(_p["speedup_s"]), 0.01)
	speed_ms = move_toward(speed_ms, target, top / acc * dt)
	if speed_ms < 0.02 or want == Vector2.ZERO:
		if want == Vector2.ZERO and speed_ms < 0.05:
			speed_ms = 0.0
		frame = 0
		_phase = 0.0
		return false
	if absf(want.x) > absf(want.y) + 0.01:
		row = Land.ROW_EAST if want.x > 0.0 else Land.ROW_WEST
	else:
		row = Land.ROW_SOUTH if want.y > 0.0 else Land.ROW_NORTH
	var lw := to_local(want, heading_deg)
	var r: float = float(_p["body_r_m"])
	var d := speed_ms * dt
	var moved := false
	var cands: Array[Vector2] = [Vector2(u + lw.x * d, v + lw.y * d), Vector2(u + lw.x * d, v), Vector2(u, v + lw.y * d)]
	for c in cands:
		if c.is_equal_approx(Vector2(u, v)):
			continue
		if layout.call("walkable", level, c.x, c.y, r) as bool:
			distance_m += Vector2(u, v).distance_to(c)
			u = c.x
			v = c.y
			moved = true
			break
	if moved:
		_phase += d / maxf(float(_p["stride_m"]), 0.1)
		frame = Land.CYCLE[int(floorf(_phase)) % Land.CYCLE.size()]
	else:
		frame = 0
	return moved


func _step_transit(dt: float) -> void:
	transit_t += dt / maxf(float(_p["transit_s"]), 0.1)
	if transit_t < 0.5:
		var k := smoothstep(0.0, 1.0, transit_t / 0.5)
		var p := _t_from.lerp(_t_via, k)
		u = p.x
		v = p.y
		return
	if level != _t_level:
		level = _t_level
		u = _t_dest.x
		v = _t_dest.y
	if transit_t >= 1.0:
		mode = Mode.WALK
		transit_t = 0.0
		speed_ms = 0.0
		frame = 0


func _step_climb(dt: float, climb_in: float) -> void:
	if climb_in > 0.3:
		climb_dir = 1
	elif climb_in < -0.3:
		climb_dir = -1
	var before := climb_t
	climb_t += float(climb_dir) * dt / maxf(float(_p["climb_s"]), 0.2)
	_phase += absf(climb_t - before) * Layout.LADDER_RISE / 0.55
	frame = Land.CYCLE[int(floorf(_phase)) % Land.CYCLE.size()]
	row = Land.ROW_NORTH
	if climb_t >= 1.0:
		level = Layout.L_NEST
		u = Layout.NEST_ARRIVE.x
		v = Layout.NEST_ARRIVE.y
		_end_climb()
	elif climb_t <= 0.0:
		level = Layout.L_DECK
		u = Layout.LADDER_LAND.x
		v = Layout.LADDER_LAND.y
		_end_climb()


func _end_climb() -> void:
	mode = Mode.WALK
	climb_dir = 0
	climb_t = 0.0
	speed_ms = 0.0
	frame = 0


## If the walker ever stands on a spot that is not walkable (a layout change, a rounding edge), move to the nearest free spot.
func _unstick() -> void:
	var r: float = float(_p["body_r_m"])
	if layout.call("walkable", level, u, v, r) as bool:
		return
	for ring in range(1, 40):
		var rad := float(ring) * 0.1
		for k in 16:
			var a := TAU * float(k) / 16.0
			var c := Vector2(u + cos(a) * rad, v + sin(a) * rad)
			if layout.call("walkable", level, c.x, c.y, r) as bool:
				u = c.x
				v = c.y
				return
