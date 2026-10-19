extends RefCounted
## CP-1 the people of Fish Row: standing, wandering and patrolling NPCs (fishers, merchants, dockers, sailors, shopkeepers,
## townspeople and the four recruits). Pure logic: the world is anything with `walkable(x, z, r) -> bool`; the screen only
## reads `row_frame()`. A person only moves when the player is within `ACTIVE_M` metres (the rest of the harbour sleeps: the CPU
## budget of an Intel HD 3000 machine), and stops to face the player while he talks to him.
## Facing rows are the hero's: 0 south, 1 north, 2 west, 3 east; walk cycle [1, 2, 3, 2], standing frame 0.
## The walk uses its own tiny generator so tests are deterministic. NOT YET RUN IN GODOT.
const ACTIVE_M := 110.0
const WALK_MS := 1.15
const STRIDE_M := 0.8
const BODY_R := 0.4
const CYCLE: Array[int] = [1, 2, 3, 2]

var people: Array = []        # [{id, group, look, x, z, hx, hz, mode, r, facing, row, frame, hidden, recruit, ...}]
var _rng := 20261019


func setup(defs: Array, seed_value: int = 20261019) -> void:
	_rng = seed_value
	people.clear()
	for d in defs:
		var n: Dictionary = (d as Dictionary).duplicate(true)
		n["hx"] = float(n["x"])
		n["hz"] = float(n["z"])
		n["x"] = float(n["x"])
		n["z"] = float(n["z"])
		n["row"] = int(n.get("facing", 0))
		n["frame"] = 0
		n["hidden"] = false
		n["state"] = "idle"
		n["timer"] = _rand_range(1.0, 5.0)
		n["tx"] = float(n["x"])
		n["tz"] = float(n["z"])
		n["phase"] = 0.0
		n["leg"] = 1.0
		n["talking"] = false
		people.append(n)


func _rand() -> float:
	_rng = (1103515245 * _rng + 12345) % 2147483648
	return float(_rng) / 2147483648.0


func _rand_range(a: float, b: float) -> float:
	return a + (b - a) * _rand()


func index_of(id: String) -> int:
	for i in people.size():
		if str((people[i] as Dictionary)["id"]) == id:
			return i
	return -1


func index_of_recruit(crew_id: String) -> int:
	for i in people.size():
		if str((people[i] as Dictionary).get("recruit", "")) == crew_id:
			return i
	return -1


## Hire = the recruit leaves the quay for the ship: hide him.
func hide_recruit(crew_id: String) -> void:
	var i := index_of_recruit(crew_id)
	if i >= 0:
		(people[i] as Dictionary)["hidden"] = true


func nearest(px: float, pz: float, radius: float, recruits_only: bool = false) -> int:
	var best := -1
	var bd := radius * radius
	for i in people.size():
		var n := people[i] as Dictionary
		if bool(n["hidden"]) or (recruits_only and str(n.get("recruit", "")) == ""):
			continue
		var dx := float(n["x"]) - px
		var dz := float(n["z"]) - pz
		var d := dx * dx + dz * dz
		if d < bd:
			bd = d
			best = i
	return best


func face_towards(i: int, px: float, pz: float) -> void:
	var n := people[i] as Dictionary
	n["row"] = _row_of(px - float(n["x"]), pz - float(n["z"]), int(n["row"]))
	n["frame"] = 0


func set_talking(i: int, on: bool, px: float = 0.0, pz: float = 0.0) -> void:
	if i < 0:
		return
	(people[i] as Dictionary)["talking"] = on
	if on:
		face_towards(i, px, pz)


static func _row_of(dx: float, dz: float, fallback: int) -> int:
	if absf(dx) < 0.001 and absf(dz) < 0.001:
		return fallback
	if absf(dx) > absf(dz):
		return 3 if dx > 0.0 else 2
	return 0 if dz > 0.0 else 1


func row_frame(i: int) -> Vector2i:
	var n := people[i] as Dictionary
	return Vector2i(int(n["row"]), int(n["frame"]))


func step(dt: float, world: Object, player: Vector2) -> void:
	for i in people.size():
		var n := people[i] as Dictionary
		if bool(n["hidden"]) or bool(n["talking"]) or str(n["mode"]) == "stand":
			continue
		var dx := float(n["x"]) - player.x
		var dz := float(n["z"]) - player.y
		if dx * dx + dz * dz > ACTIVE_M * ACTIVE_M:
			continue
		_step_one(n, dt, world)


func _step_one(n: Dictionary, dt: float, world: Object) -> void:
	if str(n["state"]) == "idle":
		n["frame"] = 0
		n["timer"] = float(n["timer"]) - dt
		if float(n["timer"]) <= 0.0:
			_pick_target(n, world)
		return
	var tx := float(n["tx"])
	var tz := float(n["tz"])
	var dx := tx - float(n["x"])
	var dz := tz - float(n["z"])
	var d := sqrt(dx * dx + dz * dz)
	var stepm := WALK_MS * dt
	if d <= stepm:
		n["x"] = tx
		n["z"] = tz
		n["state"] = "idle"
		n["timer"] = _rand_range(2.0, 6.0)
		n["frame"] = 0
		return
	var nx := float(n["x"]) + dx / d * stepm
	var nz := float(n["z"]) + dz / d * stepm
	if not bool(world.call("walkable", nx, nz, BODY_R)):
		n["state"] = "idle"             # blocked (a person, a stall moved in the way of the plan): wait and choose again
		n["timer"] = _rand_range(0.5, 1.5)
		n["frame"] = 0
		return
	n["x"] = nx
	n["z"] = nz
	n["row"] = _row_of(dx, dz, int(n["row"]))
	n["phase"] = float(n["phase"]) + stepm / STRIDE_M
	n["frame"] = CYCLE[int(floorf(float(n["phase"]))) % CYCLE.size()]


func _pick_target(n: Dictionary, world: Object) -> void:
	var hx := float(n["hx"])
	var hz := float(n["hz"])
	var r := float(n["r"])
	if str(n["mode"]) == "patrol":
		n["leg"] = -float(n["leg"])
		var tx := hx + r * float(n["leg"])
		if _line_ok(float(n["x"]), float(n["z"]), tx, hz, world):
			n["tx"] = tx
			n["tz"] = hz
			n["state"] = "walk"
		else:
			n["timer"] = 2.0
		return
	for _try in 8:
		var a := _rand() * TAU
		var rr := r * sqrt(_rand())
		var tx2 := hx + cos(a) * rr
		var tz2 := hz + sin(a) * rr
		if _line_ok(float(n["x"]), float(n["z"]), tx2, tz2, world):
			n["tx"] = tx2
			n["tz"] = tz2
			n["state"] = "walk"
			return
	n["timer"] = 2.0


## The straight walk from (ax, az) to (bx, bz) is clear: 1.5 m samples all walkable.
func _line_ok(ax: float, az: float, bx: float, bz: float, world: Object) -> bool:
	var d := Vector2(bx - ax, bz - az).length()
	var steps := maxi(int(ceilf(d / 1.5)), 1)
	for k in range(1, steps + 1):
		var t := float(k) / float(steps)
		if not bool(world.call("walkable", lerpf(ax, bx, t), lerpf(az, bz, t), BODY_R)):
			return false
	return true
