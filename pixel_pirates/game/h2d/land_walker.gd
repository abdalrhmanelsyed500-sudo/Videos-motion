extends RefCounted
## H2D-1.2 the pirate on foot: state (aboard or ashore), smooth walk and run, collision against a world object, the
## facing and
## walk-cycle frame, and the little on-foot route (4 stops). Pure logic: the world is anything with `walkable(x, z,
## r) -> bool`
## and `height_smooth(x, z)`; the screen never enters here, so tests/test_land.gd runs it with a stub.
## Every number is in data/tuning/tuning_land.json (keys land.*); DEFAULTS only covers a missing key.
## Axes: x east, z SOUTH (scene metres), like the rest of the sailing view. "North" on the keyboard (W / Up) is -z.
## NOT YET RUN IN GODOT.
enum { ABOARD, ASHORE }
const PREFIX := "land."
const DEFAULTS := {
	"walk_ms": 4.0, "run_ms": 7.5, "speedup_s": 0.12, "body_r_m": 0.45, "board_radius_m": 5.0, "poi_radius_m": 12.0,
	"stride_m": 0.8, "zoom": 4.0, "zoom_s": 1.1, "min_h": 0.45, "max_slope": 0.55, "edge_margin_m": 0.0,
}
const COMPASS: Array[String] = ["north", "north-east", "east", "south-east", "south", "south-west", "west",
		"north-west"]
const CYCLE: Array[int] = [1, 2, 3, 2]
const ROW_SOUTH := 0
const ROW_NORTH := 1
const ROW_WEST := 2
const ROW_EAST := 3

var state := ABOARD
var x := 0.0
var z := 0.0
var row := ROW_NORTH
var frame := 0
var speed_ms := 0.0
var distance_m := 0.0
var blocked_by_edge := false
var last_reached := ""     ## the name of the stop just reached; the controller says it and clears it
var board_x := 16.0
var board_z := 21.0
var explore_x := 40.0
var explore_z := -260.0
var explore_r := 520.0
var pois: Array = []          # [{id, name, x, z, visited}]
var _p: Dictionary = DEFAULTS.duplicate()
var _phase := 0.0


## `land` is the "land" dictionary of anvil_cay.json; `values` a tuning dictionary {key: value}.
func configure(land: Dictionary, values: Dictionary) -> void:
	_p = DEFAULTS.duplicate()
	for k in DEFAULTS.keys():
		var full: String = PREFIX + str(k)
		if values.has(full):
			_p[k] = float(values[full])
	var b: Dictionary = land["board"]
	board_x = float(b["x"])
	board_z = float(b["z"])
	var e: Dictionary = land["explore"]
	explore_x = float(e["x"])
	explore_z = float(e["z"])
	explore_r = float(e["r"]) + float(_p["edge_margin_m"])
	pois.clear()
	for q in land["pois"]:
		var d: Dictionary = q
		pois.append({"id": str(d["id"]), "name": str(d["name"]), "x": float(d["x"]), "z": float(d["z"]), "visited": false})


func param(key: String) -> float:
	return float(_p[key])


func is_ashore() -> bool:
	return state == ASHORE


## Step onto the pier from the moored ship.
func disembark(land: Dictionary) -> void:
	var d: Dictionary = land["disembark"]
	state = ASHORE
	x = float(d["x"])
	z = float(d["z"])
	row = ROW_NORTH
	frame = 0
	speed_ms = 0.0
	_phase = 0.0


func distance_to_board() -> float:
	return sqrt((x - board_x) * (x - board_x) + (z - board_z) * (z - board_z))


func can_board() -> bool:
	return state == ASHORE and distance_to_board() <= float(_p["board_radius_m"])


func board() -> void:
	state = ABOARD
	speed_ms = 0.0
	frame = 0


## dir: x = east (+1), y = south (+1), already read from the keys. Returns true when the pirate moved.
func step(dt: float, dir: Vector2, run: bool, world: Object) -> bool:
	if state != ASHORE:
		return false
	var want := Vector2.ZERO
	if dir.length() > 0.01:
		want = dir.normalized()
	var top: float = float(_p["run_ms"]) if run else float(_p["walk_ms"])
	var target := top * minf(dir.length(), 1.0)
	var acc: float = maxf(float(_p["speedup_s"]), 0.01)
	speed_ms = move_toward(speed_ms, target, top / acc * dt)
	blocked_by_edge = false
	if speed_ms < 0.02 or want == Vector2.ZERO:
		if want == Vector2.ZERO and speed_ms < 0.05:
			speed_ms = 0.0
		frame = 0
		_phase = 0.0
		return false
	if absf(want.x) > absf(want.y) + 0.01:
		row = ROW_EAST if want.x > 0.0 else ROW_WEST
	else:
		row = ROW_SOUTH if want.y > 0.0 else ROW_NORTH
	var r: float = float(_p["body_r_m"])
	var moved := false
	var d := speed_ms * dt
	var cands: Array[Vector2] = [Vector2(x + want.x * d, z + want.y * d), Vector2(x + want.x * d, z),
			Vector2(x, z + want.y * d)]
	for c in cands:
		if c.is_equal_approx(Vector2(x, z)):
			continue
		if _outside(c.x, c.y):
			blocked_by_edge = true
			continue
		if world.call("walkable", c.x, c.y, r) as bool:
			distance_m += Vector2(x, z).distance_to(c)
			x = c.x
			z = c.y
			moved = true
			break
	if moved:
		_phase += d / maxf(float(_p["stride_m"]), 0.1)
		frame = CYCLE[int(floorf(_phase)) % CYCLE.size()]
		_visit()
	else:
		frame = 0
	return moved


func _outside(px: float, pz: float) -> bool:
	var dx := px - explore_x
	var dz := pz - explore_z
	return dx * dx + dz * dz > explore_r * explore_r


func _visit() -> void:
	var rr: float = float(_p["poi_radius_m"])
	for q in pois:
		var d: Dictionary = q
		if bool(d["visited"]):
			continue
		var dx: float = x - float(d["x"])
		var dz: float = z - float(d["z"])
		if dx * dx + dz * dz <= rr * rr:
			d["visited"] = true
			last_reached = str(d["name"])


func visited_count() -> int:
	var c := 0
	for q in pois:
		if bool((q as Dictionary)["visited"]):
			c += 1
	return c


func route_complete() -> bool:
	return not pois.is_empty() and visited_count() == pois.size()


## The next stop not yet visited, or {} when all are done.
func next_poi() -> Dictionary:
	for q in pois:
		if not bool((q as Dictionary)["visited"]):
			return q as Dictionary
	return {}


static func compass_name(dx: float, dz: float) -> String:
	## dx east, dz south
	var ang := rad_to_deg(atan2(dx, -dz))
	var i := int(roundf(fposmod(ang, 360.0) / 45.0)) % 8
	return COMPASS[i]


func hint_text() -> String:
	var dx := board_x - x
	var dz := board_z - z
	var s := "Ship: %d m %s" % [int(roundf(sqrt(dx * dx + dz * dz))), compass_name(dx, dz)]
	var np := next_poi()
	s += "   Route %d/%d" % [visited_count(), pois.size()]
	if np.is_empty():
		s += "  complete: walk back to the pier"
	else:
		var ex: float = float(np["x"]) - x
		var ez: float = float(np["z"]) - z
		s += "  next: %s, %d m %s" % [str(np["name"]), int(roundf(sqrt(ex * ex + ez * ez))), compass_name(ex, ez)]
	return s


## Teleport for testing (key T): onto a stop (the position is the stop's own, already on walkable ground).
func teleport_to(poi_id: String) -> bool:
	for q in pois:
		var d: Dictionary = q
		if str(d["id"]) == poi_id:
			x = float(d["x"])
			z = float(d["z"])
			speed_ms = 0.0
			return true
	return false
