extends RefCounted
## H2D-1.2 on-foot controller (land_walker.gd) with a stub world: a round island with one wall. Pure logic, no graphics.
## Checks speeds and acceleration, run, facing rows, walk-cycle frames, collision and wall sliding, the explore edge,
## stops (visit, teleport, hint), boarding range and that DEFAULTS match data/tuning/tuning_land.json.
## NOT YET RUN IN GODOT.
const Walker := preload("res://h2d/land_walker.gd")
const Ocean := preload("res://core/ocean.gd")


class StubWorld:
	extends RefCounted
	var wall_x := 30.0

	func walkable(x: float, z: float, r: float) -> bool:
		if absf(x - wall_x) < r and z < 10.0:
			return false
		return x * x + z * z < 90000.0

	func height_smooth(_x: float, _z: float) -> float:
		return 2.0


func _land() -> Dictionary:
	return {"board": {"x": 0.0, "z": 0.0}, "disembark": {"x": 0.0, "z": 0.0}, "explore": {"x": 0.0, "z": 0.0, "r": 200.0},
			"pois": [{"id": "a", "name": "Stop A", "x": 0.0, "z": -50.0}, {"id": "b", "name": "Stop B", "x": 100.0, "z": 50.0}]}


func _walker(values: Dictionary) -> Object:
	var w := Walker.new()
	w.configure(_land(), values)
	w.disembark(_land())
	return w


func _run(w: Object, world: Object, dir: Vector2, secs: float, run_key := false) -> void:
	var n := int(secs * 60.0)
	for i in n:
		w.step(1.0 / 60.0, dir, run_key, world)


func run(t: Object) -> void:
	var tuning := Ocean.load_tuning()
	for k in Walker.DEFAULTS.keys():
		var full: String = Walker.PREFIX + str(k)
		t.check(tuning.has(full), "tuning has %s" % full)
		if tuning.has(full):
			var same := absf(float(tuning[full]) - float(Walker.DEFAULTS[k])) < 0.000001
			t.check(same, "default of %s matches the JSON" % full)
	var world := StubWorld.new()
	var w := _walker({})
	t.check(w.is_ashore(), "disembark puts the pirate ashore")
	t.check(w.can_board(), "the pirate who just stepped off is within boarding range of the ship")
	# walking north (W = -z): speed ramps to walk_ms within about speedup_s and the row is NORTH
	_run(w, world, Vector2(0, -1), 0.05)
	t.check(w.speed_ms > 0.0 and w.speed_ms < 4.0, "speed is still ramping after 0.05 s (%.2f)" % w.speed_ms)
	_run(w, world, Vector2(0, -1), 0.5)
	t.check(absf(w.speed_ms - 4.0) < 0.01, "walking settles at land.walk_ms (%.2f)" % w.speed_ms)
	t.check(w.row == Walker.ROW_NORTH, "walking north faces the north row")
	t.check(w.z < -1.5, "the pirate moved north (z = %.2f)" % w.z)
	t.check(w.frame >= 1 and w.frame <= 3, "walk frame is 1..3 while moving (%d)" % w.frame)
	_run(w, world, Vector2(0, -1), 1.0, true)
	t.check(absf(w.speed_ms - 7.5) < 0.01, "Shift runs at land.run_ms (%.2f)" % w.speed_ms)
	# diagonal movement is not faster than straight movement
	var d := _walker({})
	_run(d, world, Vector2(1, -1), 1.0)
	t.check(absf(d.speed_ms - 4.0) < 0.01, "diagonal speed is not higher (%.2f)" % d.speed_ms)
	# stopping: the frame returns to 0 (standing)
	_run(d, world, Vector2.ZERO, 1.0)
	t.check(d.speed_ms == 0.0 and d.frame == 0, "released keys stop the walk cycle")
	# the four facing rows
	var f := _walker({})
	_run(f, world, Vector2(1, 0), 0.2)
	t.check(f.row == Walker.ROW_EAST, "east row")
	_run(f, world, Vector2(0, 1), 0.2)
	t.check(f.row == Walker.ROW_SOUTH, "south row")
	_run(f, world, Vector2(-1, 0), 0.2)
	t.check(f.row == Walker.ROW_WEST, "west row")
	# the wall at x = 30 (z < 10): walking east along z = 0 stops short of it (body radius 0.45)
	var c := _walker({})
	_run(c, world, Vector2(1, 0), 12.0)
	t.check(c.x < 30.0 - 0.45 + 0.001, "the wall stops the pirate (x = %.2f)" % c.x)
	t.check(c.x > 25.0, "the pirate got up to the wall (x = %.2f)" % c.x)
	# sliding: pressing into the wall diagonally keeps moving along it
	var z0: float = c.z
	_run(c, world, Vector2(1, -1), 1.0)
	t.check(c.z < z0 - 1.0, "the pirate slides along the wall (dz = %.2f)" % (c.z - z0))
	# the explore edge (radius 200): walking south reaches it and is held there
	var e := _walker({})
	_run(e, world, Vector2(0, 1), 60.0, true)
	var dist_c := sqrt(e.x * e.x + e.z * e.z)
	t.check(dist_c <= 200.0 + 0.01, "the explore circle holds (%.1f m from the centre)" % dist_c)
	t.check(e.blocked_by_edge, "the edge flag is raised at the border")
	# stops
	var p := _walker({})
	t.check(p.next_poi()["id"] == "a", "the first stop is A")
	t.check(p.hint_text().contains("Stop A"), "the hint names the next stop")
	p.teleport_to("a")
	_run(p, world, Vector2(0, -1), 0.1)
	t.check(p.visited_count() == 1 and p.last_reached == "Stop A", "walking onto stop A visits it")
	t.check(not p.route_complete(), "the route is not complete after one stop")
	p.teleport_to("b")
	_run(p, world, Vector2(1, 0), 0.1)
	t.check(p.route_complete(), "both stops visited: route complete")
	t.check(p.next_poi().is_empty(), "no next stop when complete")
	# boarding
	p.teleport_to("a")
	t.check(not p.can_board(), "50 m from the ship cannot board")
	p.x = 2.0
	p.z = 1.0
	t.check(p.can_board(), "2 m from the ship can board")
	p.board()
	t.check(not p.is_ashore(), "board() puts the pirate aboard")
	t.check(not p.step(0.1, Vector2(1, 0), false, world), "an aboard pirate does not walk")
	var names_ok := Walker.compass_name(0.0, -10.0) == "north" and Walker.compass_name(10.0, 0.0) == "east"
	t.check(names_ok, "compass names: north is -z")
	t.check(Walker.compass_name(10.0, 10.0) == "south-east", "south-east is +x +z")
