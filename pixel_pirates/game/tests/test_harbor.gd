extends RefCounted
## H2D-1 docking: replays tests/fixtures/harbor_cases.json made by tools/h2d/harbor_logic.py (the Python twin).
## Checks the docking invariants (exactly at the berth facing north; facing the sea after casting off) and that
## Harbor.DEFAULTS match data/tuning/tuning_harbor.json. NOT YET RUN IN GODOT.
const Harbor := preload("res://h2d/harbor.gd")
const Ocean := preload("res://core/ocean.gd")
const DataLoader := preload("res://core/data_loader.gd")
const TOL := 0.0001


func run(t: Object) -> void:
	var tuning := Ocean.load_tuning()
	for k in Harbor.DEFAULTS.keys():
		var full: String = Harbor.PREFIX + str(k)
		t.check(tuning.has(full), "tuning has %s" % full)
		if tuning.has(full):
			var same := absf(float(tuning[full]) - float(Harbor.DEFAULTS[k])) < 0.000001
			t.check(same, "default of %s matches the JSON" % full)
	var layout: Dictionary = DataLoader.load_dict("res://h2d/art/anvil_cay.json")["harbor_layout"]
	var fx := DataLoader.load_dict("res://tests/fixtures/harbor_cases.json")
	for c in fx["scale"]:
		var h := _make(layout, tuning)
		var got := h.speed_scale(float(c["x"]), float(c["z"]))
		var msg := "speed scale at (%s, %s) = %.4f (expected %.4f)" % [c["x"], c["z"], got, float(c["k"])]
		t.check(absf(got - float(c["k"])) < TOL, msg)
	for c in fx["footprint"]:
		var h := _make(layout, tuning)
		var pts: Array = h.footprint(float(c["x"]), float(c["z"]), float(c["heading"]))
		var want: Array = c["pts"]
		t.check(pts.size() == want.size(), "footprint has %d probes" % want.size())
		for i in mini(pts.size(), want.size()):
			var ok := absf(float(pts[i][0]) - float(want[i][0])) < TOL
			ok = ok and absf(float(pts[i][1]) - float(want[i][1])) < TOL
			t.check(ok, "footprint probe %d at heading %s" % [i, c["heading"]])
	for i in (fx["dock"] as Array).size():
		_replay_dock(t, layout, tuning, fx["dock"][i], fx["undock"][i])
	var h2 := _make(layout, tuning)
	t.check(h2.request(100.0, 200.0, 0.0) == "not_in_zone", "SPACE outside the dock zone does nothing")
	t.check(h2.state == Harbor.SAILING, "still sailing after a refused dock request")
	t.check(h2.request(20.0, 70.0, 0.0) == "docking", "SPACE inside the zone starts docking")
	t.check(h2.request(20.0, 70.0, 0.0) == "busy", "a second SPACE while docking is ignored")
	t.check(h2.speed_scale(21.4, 30.0) == 1.0, "no speed easing while the crew docks the ship")
	var pr := _make(layout, tuning).prompt(21.4, 70.0)
	var tells := bool(pr["can_dock"]) and str(pr["text"]).contains("SPACE")
	t.check(tells, "the prompt tells the player to press SPACE in the zone")
	var far := _make(layout, tuning).prompt(-100.0, 140.0)
	t.check(not bool(far["can_dock"]), "the start position is outside the dock zone")


func _make(layout: Dictionary, tuning: Dictionary) -> Harbor:
	var h := Harbor.new()
	h.configure(layout, tuning)
	return h


func _replay_dock(t: Object, layout: Dictionary, tuning: Dictionary, dk: Dictionary, ud: Dictionary) -> void:
	var nm := str(dk["name"])
	var h := _make(layout, tuning)
	t.check(h.request(float(dk["x"]), float(dk["z"]), float(dk["heading"])) == "docking", "%s: docking starts" % nm)
	var dt := float(dk["dt"])
	var marks: Dictionary = {}
	for s in dk["samples"]:
		marks[int(s["i"])] = s
	var i := 0
	var last: Dictionary = {}
	while i < 4000 and h.state == Harbor.DOCKING:
		i += 1
		last = h.step(dt)
		if marks.has(i):
			_same(t, "%s dock step %d" % [nm, i], last, marks[i])
	t.check(h.state == Harbor.DOCKED, "%s: ends docked" % nm)
	var at_berth := absf(float(last["x"]) - h.berth_x) < TOL and absf(float(last["z"]) - h.berth_z) < TOL
	t.check(at_berth, "%s: ends exactly at the berth" % nm)
	var north := absf(Harbor.wrap180(float(last["heading"]) - h.berth_heading)) < TOL
	t.check(north, "%s: ends facing north" % nm)
	t.check(float(last["moor"]) == 1.0, "%s: fully moored at the end" % nm)
	t.check(h.speed_scale(h.berth_x, h.berth_z) == 1.0, "%s: no speed easing while docked" % nm)
	var req := h.request(h.berth_x, h.berth_z, h.berth_heading)
	t.check(req == "casting_off", "%s: SPACE casts off" % nm)
	var umarks: Dictionary = {}
	for s in ud["samples"]:
		umarks[int(s["i"])] = s
	i = 0
	while i < 4000 and h.state == Harbor.UNDOCKING:
		i += 1
		last = h.step(dt)
		if umarks.has(i):
			_same(t, "%s undock step %d" % [nm, i], last, umarks[i])
	t.check(h.state == Harbor.SAILING, "%s: sailing again after casting off" % nm)
	var sea := absf(Harbor.wrap180(float(last["heading"]) - 180.0)) < TOL
	t.check(sea, "%s: facing the sea (heading 180) when the helm returns" % nm)
	var free := absf(float(last["x"]) - h.approach_x) < TOL and absf(float(last["z"]) - h.approach_z) < TOL
	t.check(free, "%s: free at the approach point" % nm)


func _same(t: Object, label: String, got: Dictionary, want: Dictionary) -> void:
	var ok := absf(float(got["x"]) - float(want["x"])) < TOL and absf(float(got["z"]) - float(want["z"])) < TOL
	ok = ok and absf(Harbor.wrap180(float(got["heading"]) - float(want["heading"]))) < TOL
	ok = ok and absf(float(got["moor"]) - float(want["moor"])) < TOL and int(got["state"]) == int(want["state"])
	t.check(ok, label)
