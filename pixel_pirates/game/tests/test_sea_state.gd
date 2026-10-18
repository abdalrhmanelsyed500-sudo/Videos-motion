extends RefCounted
## Ship movement for the E1 slice (core/sea_state.gd). Replays tests/fixtures/sea_cases.json (golden voyages from the
## Python twin) and checks the rules that matter: a paused clock never moves the ship, the world edge stops it,
## the ship cannot sail straight into the wind, and the same voyage in one call or many agrees.
## NOT YET RUN IN GODOT (see docs/E1_WORLD_SPEC.md).
const Ocean := preload("res://core/ocean.gd")
const SeaState := preload("res://core/sea_state.gd")
const DataLoader := preload("res://core/data_loader.gd")
const TOL_KM := 0.001


func run(t: Object) -> void:
	var oc: RefCounted = Ocean.load_default()
	var fx := DataLoader.load_dict("res://tests/fixtures/sea_cases.json")
	var cases: Array = fx.get("cases", [])
	t.check(cases.size() >= 8, "sea fixture has >= 8 voyages (has %d)" % cases.size())
	for c in cases:
		var st: RefCounted = SeaState.new(oc)
		var start: Array = c["start"]
		st.place(float(start[0]), float(start[1]), float(start[2]))
		var now := float(c["t0"])
		for gs in c["steps"]:
			st.advance(now, float(gs))
			now += float(gs) / 86400.0
		var e: Dictionary = c["expect"]
		var ok: bool = absf(st.x_km - float(e["x"])) < TOL_KM and absf(st.y_km - float(e["y"])) < TOL_KM
		ok = ok and absf(st.distance_km - float(e["distance"])) < TOL_KM
		ok = ok and absf(st.speed_kn() - float(e["speed_kn"])) < TOL_KM
		t.check(ok, "voyage '%s': got (%.3f, %.3f) %.3f km, expected (%s, %s) %s km" % [
				c["name"], st.x_km, st.y_km, st.distance_km, e["x"], e["y"], e["distance"]])
	_rules(t, oc)


func _rules(t: Object, oc: RefCounted) -> void:
	var st: RefCounted = SeaState.new(oc)
	st.place(7000.0, 2650.0, 270.0)
	st.advance(0.25, 0.0)
	t.check(st.last_sample.is_empty(), "a zero-length step takes no sample")
	st.refresh(0.25)
	t.check(not st.last_sample.is_empty() and st.speed_kn() > 0.0, "refresh() samples the sea at the ship")
	t.check(st.x_km == 7000.0 and st.distance_km == 0.0, "0 game seconds (a paused clock) moves nothing")
	st.advance(0.25, 5760.0)
	var minute_ok: bool = st.distance_km > 3.0 and st.distance_km < 25.0
	t.check(minute_ok, "one real minute of sailing covers 3..25 km (%.1f)" % st.distance_km)
	var west: float = st.x_km
	t.check(west < 7000.0 and absf(st.y_km - 2650.0) < 1.0, "heading 270 moves the ship west and not north or south")
	var edge: RefCounted = SeaState.new(oc)
	edge.place(50.0, 3000.0, 270.0)
	for k in 48:
		edge.advance(2.0 + float(k) / 24.0, 3600.0)
	t.check(edge.x_km == 0.0, "the world edge stops the ship (no wrap, no escape)")
	var calm: RefCounted = SeaState.new(oc)
	calm.place(4500.0, 3000.0, 90.0)
	calm.advance(0.25, 86400.0)
	t.check(calm.distance_km < 80.0, "the Glass Sea is slow: under 80 km in one game day (%.0f)" % calm.distance_km)
