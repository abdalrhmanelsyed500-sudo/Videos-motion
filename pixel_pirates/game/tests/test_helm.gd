extends RefCounted
## The helm (H2D-0.1): replays tests/fixtures/helm_cases.json made by tools/h2d/helm_logic.py (the Python twin), checks
## the feel invariants and that Helm.DEFAULTS match data/tuning/tuning_helm.json. NOT YET RUN IN GODOT.
const Helm := preload("res://h2d/helm.gd")
const Ocean := preload("res://core/ocean.gd")
const DataLoader := preload("res://core/data_loader.gd")
const DT := 1.0 / 60.0
const TOL := 0.001


func run(t: Object) -> void:
	var tuning := Ocean.load_tuning()
	var probe := Helm.new()
	for k in Helm.DEFAULTS.keys():
		var full: String = Helm.PREFIX + str(k)
		t.check(tuning.has(full), "tuning has %s" % full)
		if tuning.has(full):
			var same := absf(float(tuning[full]) - float(Helm.DEFAULTS[k])) < 0.000001
			t.check(same, "default of %s matches the JSON" % full)
	var fx := DataLoader.load_dict("res://tests/fixtures/helm_cases.json")
	for sc in fx["scenarios"]:
		_replay(t, sc, tuning)
	for c in fx["sail"]:
		var got := Helm.point_of_sail(float(c["off"]), float(c["no_go"]))
		t.check(got == str(c["name"]), "point of sail at %s deg = %s (expected %s)" % [c["off"], got, c["name"]])
	for c in fx["escape"]:
		var got := Helm.escape_direction(float(c["heading"]), float(c["wind_from"]))
		t.check(got == int(c["dir"]), "escape from irons at heading %s wind %s -> %d" % [c["heading"], c["wind_from"], got])
	_feel(t, tuning)
	t.check(probe.steerage(0.0) > 0.0, "steerage never reaches zero")


func _replay(t: Object, sc: Dictionary, tuning: Dictionary) -> void:
	var h := Helm.new()
	h.configure(tuning)
	h.heading_deg = float(sc["heading"])
	h.speed_kn = float(sc["speed"])
	h.set_sensitivity(float(sc["sensitivity"]))
	var scn := str(sc["name"])
	var n := int(roundf(float(sc["seconds"]) / DT))
	var marks: Dictionary = {}
	for s in sc["samples"]:
		marks[int(roundf(float(s["t"]) / DT))] = s
	for i in n:
		h.step(DT, _steer(scn, float(i) * DT), _target(scn, h))
		if marks.has(i + 1):
			var s: Dictionary = marks[i + 1]
			var dh := absf(Helm.wrap180(h.heading_deg - float(s["heading"])))
			t.check(dh < TOL, "%s t=%.1f heading %.4f vs %.4f" % [scn, float(s["t"]), h.heading_deg, float(s["heading"])])
			t.check(absf(h.yaw_rate - float(s["yaw"])) < TOL, "%s t=%.1f yaw rate" % [scn, float(s["t"])])
			t.check(absf(h.rudder - float(s["rudder"])) < TOL, "%s t=%.1f rudder" % [scn, float(s["t"])])
			t.check(absf(h.speed_kn - float(s["speed"])) < TOL, "%s t=%.1f speed" % [scn, float(s["t"])])


## The scripted inputs of each scenario (the same lambdas as in helm_logic.make_fixture).
func _steer(scn: String, time: float) -> float:
	match scn:
		"hold_D_then_release":
			return 1.0 if time < 3.0 else 0.0
		"tap_A_200ms":
			return -1.0 if time < 0.2 else 0.0
		"reverse_D_then_A":
			return 1.0 if time < 1.0 else -1.0
		"D_across_north", "in_irons_still_steers", "double_sensitivity":
			return 1.0
	return 0.0


func _target(scn: String, _h: RefCounted) -> float:
	match scn:
		"head_to_wind_bleeds_speed", "in_irons_still_steers":
			return 0.6
		"reverse_D_then_A":
			return 4.0
	return 5.0


## The properties a player feels, independent of the fixture.
func _feel(t: Object, tuning: Dictionary) -> void:
	var h := Helm.new()
	h.configure(tuning)
	h.reset(0.0, 5.0)
	var secs := 0.0
	while Helm.wrap180(h.heading_deg) < 90.0 and secs < 20.0:
		h.step(DT, 1.0, 5.0)
		secs += DT
	t.check(secs > 1.5 and secs < 4.0, "90 degrees at full helm takes %.2f s (wanted 1.5 to 4)" % secs)
	var at_release := h.heading_deg
	for i in 120:
		h.step(DT, 0.0, 5.0)
	var coast := Helm.wrap180(h.heading_deg - at_release)
	t.check(coast >= 0.0 and coast < 9.0, "the ship coasts %.1f deg after the key is released (wanted under 9)" % coast)
	t.check(absf(h.yaw_rate) < 0.5, "turning has stopped 2 s after release")
	h.reset(0.0, 5.0)
	for i in 12:
		h.step(DT, -1.0, 5.0)
	for i in 120:
		h.step(DT, 0.0, 5.0)
	var tap := Helm.wrap180(h.heading_deg)
	t.check(tap < -2.0 and tap > -10.0, "a 0.2 s tap on A turns %.1f deg to port (wanted 2 to 10)" % tap)
	h.reset(0.0, 5.0)
	for i in 480:
		h.step(DT, 0.0, 0.6)
	var bled := h.speed_kn
	t.check(bled > 0.6 and bled < 2.0, "8 s head to wind: speed %.2f kn, bled but not stopped dead" % bled)
	h.reset(0.0, 0.6)
	var first := h.speed_kn
	for i in 60:
		h.step(DT, 0.0, 5.0)
	t.check(h.speed_kn > first and h.speed_kn < 3.0, "speed builds up gradually after bearing away")
