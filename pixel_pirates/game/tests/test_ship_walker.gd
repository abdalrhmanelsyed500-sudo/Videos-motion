# gdlint: disable=max-line-length
extends RefCounted
## CP-2 Release A: the on-ship walker. It lives in ship-local coordinates, so the ship's heading and motion cannot push it
## through anything. Checks speeds, screen-relative input at several headings, collision and sliding, the hatch transit
## (level changes at the dark midpoint, lands standable), the rope ladder up and down (no sticking, both directions), settle()
## and unstick, and that DEFAULTS match data/tuning/tuning_ship.json. Pure logic. NOT YET RUN ON THE USER'S PC.
const Walker := preload("res://h2d/ship_walker.gd")
const Layout := preload("res://h2d/ship_layout.gd")
const Land := preload("res://h2d/land_walker.gd")


func _w() -> Object:
	var w := Walker.new()
	w.call("configure", {})
	w.call("place_at_helm")
	return w


func _run(w: Object, dir: Vector2, secs: float, heading := 0.0, run_key := false) -> void:
	for i in int(secs * 60.0):
		w.call("step", 1.0 / 60.0, dir, run_key, heading, 0.0)


func run(t: Object) -> void:
	# --- defaults equal the tuning JSON
	var f := FileAccess.open("res://data/tuning/tuning_ship.json", FileAccess.READ)
	var tuning: Dictionary = {}
	if f != null:
		for rec in (JSON.parse_string(f.get_as_text()) as Dictionary)["records"]:
			tuning[str((rec as Dictionary)["key"])] = float((rec as Dictionary)["value"])
	t.call("check", tuning.size() >= 15, "tuning_ship.json has records (%d)" % tuning.size())
	for k in Walker.DEFAULTS.keys():
		var full := "deck." + str(k)
		t.call("check", tuning.has(full) and absf(float(tuning[full]) - float(Walker.DEFAULTS[k])) < 0.000001, "DEFAULT matches json: " + full)
	# --- screen-relative input (north = up) at three headings
	var w := _w()
	_run(w, Vector2(0.0, -1.0), 1.0, 0.0)           # heading north: screen up = ship forward (+u)
	t.call("check", float(w.get("u")) > Layout.HELM_LEAVE.x + 2.0, "heading N: walking up moves forward (u=%.2f)" % float(w.get("u")))
	t.call("check", absf(float(w.get("v")) - Layout.HELM_LEAVE.y) < 0.05, "heading N: no sideways drift")
	t.call("check", int(w.get("row")) == Land.ROW_NORTH, "facing north row")
	w.call("place", 0, Vector2(0.0, 2.0))
	_run(w, Vector2(0.0, -1.0), 1.0, 90.0)          # heading east: screen up = port (-v)
	t.call("check", float(w.get("v")) < 2.0 - 2.0, "heading E: walking up moves to port (v=%.2f)" % float(w.get("v")))
	w.call("place_at_helm")
	_run(w, Vector2(0.0, -1.0), 1.0, 180.0)         # heading south: screen up = astern (-u)
	t.call("check", float(w.get("u")) < Layout.HELM_LEAVE.x + 0.01, "heading S: walking up moves aft or is blocked by the cabin wall (u=%.2f)" % float(w.get("u")))
	# --- speed and run
	w = _w()
	_run(w, Vector2(0.0, -1.0), 0.6, 0.0)
	var sp := float(w.get("speed_ms"))
	t.call("check", absf(sp - 3.4) < 0.05, "walking speed 3.4 m/s (%.2f)" % sp)
	w = _w()
	_run(w, Vector2(0.0, -1.0), 0.6, 0.0, true)
	t.call("check", absf(float(w.get("speed_ms")) - 6.0) < 0.05, "running speed 6 m/s")
	# --- diagonal is not faster
	w = _w()
	w.call("place", 0, Vector2(3.0, 1.0))
	_run(w, Vector2(1.0, -1.0), 0.5, 0.0)
	t.call("check", float(w.get("speed_ms")) < 3.45, "diagonal speed is normalised")
	# --- stopping
	w = _w()
	_run(w, Vector2(0.0, -1.0), 0.5, 0.0)
	_run(w, Vector2.ZERO, 0.4, 0.0)
	t.call("check", float(w.get("speed_ms")) == 0.0 and int(w.get("frame")) == 0, "stops cleanly with frame 0")
	# --- walk cycle advances
	w = _w()
	var frames := {}
	for i in 90:
		w.call("step", 1.0 / 60.0, Vector2(0.0, -1.0), false, 0.0, 0.0)
		frames[int(w.get("frame"))] = true
	t.call("check", frames.size() >= 3, "walk cycle uses several frames")
	# --- the hull stops you: run at the rail for 3 s in each direction, never leave the walkable area
	var lay := Layout.new()
	for hd in [0.0, 37.0, 90.0, 200.0, 315.0]:
		for dv in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1), Vector2(1, 1), Vector2(-1, 1)]:
			w = _w()
			_run(w, dv as Vector2, 6.0, float(hd), true)
			t.call("check", lay.walkable(0, float(w.get("u")), float(w.get("v")), 0.38 - 0.001), "stays on the deck: heading %d dir %s" % [int(hd), dv])
	# --- the heading changing while walking never puts the walker in a wall: sweep the heading at 30 deg/s
	w = _w()
	var ok := true
	for i in 600:
		var hd2 := fposmod(float(i) * 0.5, 360.0)
		w.call("step", 1.0 / 60.0, Vector2(0.7, -0.7), false, hd2, 0.0)
		if not lay.walkable(0, float(w.get("u")), float(w.get("v")), 0.37):
			ok = false
	t.call("check", ok, "turning ship: the walker never ends up inside a wall")
	# --- the helm station to the hatch by walking (bow-ward then to the hatch edge), not teleporting
	w = _w()
	w.call("place", 0, Vector2(-3.0, 0.0))
	_run(w, Vector2(0.0, -1.0), 0.0, 0.0)
	# --- hatch transit down and up
	w = _w()
	w.call("place", 0, Vector2(-2.9, 0.0))
	t.call("check", bool(w.call("start_transit", Layout.L_SLEEP, Layout.HATCH, Layout.ARRIVE_BELOW)), "transit starts")
	t.call("check", not bool(w.call("start_transit", Layout.L_HOLD, Layout.HATCH, Layout.ARRIVE_HOLD)), "no second transit while busy")
	var changed_at := -1.0
	var max_fade := 0.0
	for i in 120:
		if not bool(w.call("is_busy")):
			break
		w.call("step", 1.0 / 60.0, Vector2(1.0, 0.0), true, 0.0, 0.0)      # keys are ignored during a transit
		max_fade = maxf(max_fade, float(w.call("fade_amount")))
		if changed_at < 0.0 and int(w.get("level")) == Layout.L_SLEEP:
			changed_at = float(w.get("transit_t"))
	t.call("check", int(w.get("level")) == Layout.L_SLEEP and not bool(w.call("is_busy")), "transit ends on the sleeping deck")
	t.call("check", changed_at >= 0.5 and changed_at < 0.6, "the level changes at the dark midpoint (t=%.2f)" % changed_at)
	t.call("check", max_fade >= 0.99, "screen goes fully dark at the midpoint (%.2f)" % max_fade)
	t.call("check", w.call("pos").is_equal_approx(Layout.ARRIVE_BELOW), "lands at the arrival point %s" % str(w.call("pos")))
	t.call("check", lay.walkable(1, float(w.get("u")), float(w.get("v")), 0.38), "arrival standable")
	w.call("start_transit", Layout.L_DECK, Layout.HATCH, Layout.ARRIVE_ABOVE)
	_run(w, Vector2.ZERO, 1.2, 0.0)
	t.call("check", int(w.get("level")) == Layout.L_DECK and w.call("pos").is_equal_approx(Layout.ARRIVE_ABOVE), "and back up to the main deck")
	# --- settle() completes a running transit at once (scene change safety)
	w.call("start_transit", Layout.L_SLEEP, Layout.HATCH, Layout.ARRIVE_BELOW)
	_run(w, Vector2.ZERO, 0.1, 0.0)
	w.call("settle")
	t.call("check", int(w.get("level")) == Layout.L_SLEEP and not bool(w.call("is_busy")), "settle() finishes a transit")
	# --- rope ladder: up
	w = _w()
	w.call("place", 0, Layout.LADDER_LAND)
	t.call("check", not bool(w.call("start_climb", -1)), "cannot climb down from the deck")
	t.call("check", bool(w.call("start_climb", 1)), "climb starts")
	var h_prev := -1.0
	var mono := true
	for i in 1000:
		w.call("step", 1.0 / 60.0, Vector2.ZERO, false, 0.0, 0.0)
		if not bool(w.call("is_busy")):
			break
		var h := float(w.call("height_above_floor"))
		if h < h_prev - 0.0001:
			mono = false
		h_prev = h
	t.call("check", mono, "climbing up: height only rises")
	t.call("check", int(w.get("level")) == Layout.L_NEST and not bool(w.call("is_busy")), "arrives in the crow's nest")
	t.call("check", w.call("pos").is_equal_approx(Layout.NEST_ARRIVE) and lay.walkable(3, float(w.get("u")), float(w.get("v")), 0.38), "nest arrival standable")
	t.call("check", not bool(w.call("start_climb", 1)), "cannot climb up from the nest")
	# walk around the nest, it holds
	for hd in [0.0, 120.0]:
		_run(w, Vector2(1, 0), 2.0, float(hd), true)
		_run(w, Vector2(0, 1), 2.0, float(hd), true)
		t.call("check", lay.walkable(3, float(w.get("u")), float(w.get("v")), 0.37), "nest walking stays on the platform")
	w.call("place", 3, Layout.NEST_ARRIVE)
	# --- down
	t.call("check", bool(w.call("start_climb", -1)), "descent starts from the nest")
	var steps := 0
	while bool(w.call("is_busy")) and steps < 1000:
		w.call("step", 1.0 / 60.0, Vector2.ZERO, false, 0.0, 0.0)
		steps += 1
	t.call("check", int(w.get("level")) == Layout.L_DECK and w.call("pos").is_equal_approx(Layout.LADDER_LAND), "arrives at the foot of the ladder")
	t.call("check", steps > 150 and steps < 400, "climb takes about climb_s (%d frames)" % steps)
	# --- reverse mid-climb: up half way then S goes back down to the deck
	w.call("start_climb", 1)
	_run(w, Vector2.ZERO, 1.6, 0.0)
	t.call("check", float(w.get("climb_t")) > 0.4 and float(w.get("climb_t")) < 0.6, "half way up (%.2f)" % float(w.get("climb_t")))
	for i in 400:
		w.call("step", 1.0 / 60.0, Vector2.ZERO, false, 0.0, -1.0)
		if not bool(w.call("is_busy")):
			break
	t.call("check", int(w.get("level")) == Layout.L_DECK and not bool(w.call("is_busy")), "S on the ladder returns to the deck, not stuck")
	# --- settle() during a climb picks the nearer end, standable
	w.call("start_climb", 1)
	_run(w, Vector2.ZERO, 0.4, 0.0)
	w.call("settle")
	t.call("check", int(w.get("level")) == Layout.L_DECK and lay.walkable(0, float(w.get("u")), float(w.get("v")), 0.38), "settle() low on the ladder: deck")
	w.call("start_climb", 1)
	_run(w, Vector2.ZERO, 2.6, 0.0)
	w.call("settle")
	t.call("check", int(w.get("level")) == Layout.L_NEST and lay.walkable(3, float(w.get("u")), float(w.get("v")), 0.38), "settle() high on the ladder: nest")
	# --- unstick: forced into the hatch hole, one step moves to a free spot
	w = _w()
	w.call("place", 0, Layout.HATCH)
	w.call("step", 1.0 / 60.0, Vector2.ZERO, false, 0.0, 0.0)
	t.call("check", lay.walkable(0, float(w.get("u")), float(w.get("v")), 0.38), "unstick moves the walker out of a solid")
	# --- transform helpers are inverses
	for hd in [0.0, 45.0, 123.0, 270.0]:
		var d := Vector2(0.3, -0.8)
		var lo: Vector2 = Walker.to_local(d, float(hd))
		var back: Vector2 = Walker.to_world(lo, float(hd))
		t.call("check", back.is_equal_approx(d) or back.distance_to(d) < 0.0001, "to_local / to_world round trip at %d" % int(hd))
	t.call("check", Walker.to_local(Vector2(0, -1), 0.0).is_equal_approx(Vector2(1, 0)), "north on screen is forward at heading 0")
	t.call("check", Walker.to_local(Vector2(1, 0), 90.0).is_equal_approx(Vector2(1, 0)) or Walker.to_local(Vector2(1, 0), 90.0).distance_to(Vector2(1, 0)) < 0.0001, "east on screen is forward at heading 90")
