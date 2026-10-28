extends SceneTree
## Tactical scene test: builds an engagement, issues attack orders, runs the
## real fixed-fps loop, asserts units fight and the battle resolves.

var checks := 0
var failures: Array = []
var scene = null
var frames := 0
var GS = null
var _alive_at_start := 0
var _hp_at_start := 0.0


func ok(cond: bool, label: String) -> void:
	checks += 1
	if not cond:
		failures.append(label)


func _initialize() -> void:
	print("T0 init")
	GS = root.get_node("GameState")
	GS.new_campaign(4242)
	var st = GS.cs
	var pid: String = st.player_id()
	var region: String = st.formations_of(pid)[0]["region"]
	var eid: String = st.next_id("frm")
	st.formations[eid] = {"id": eid, "country": "cty_vardena", "name": "Test Garrison",
		"region": region, "units": [
			{"class": "infantry", "equip": "rif_surplus", "count": 3, "condition": 0.8}],
		"morale": 0.7, "cohesion": 0.7, "readiness": 0.8, "supplies": 0.9,
		"experience": 0, "commander": "T", "orders": [], "loyalty": 0.6}
	st.rel(pid, "cty_vardena")["threat"] = 0.9
	scene = load("res://scenes/tactical_map.tscn").instantiate()
	root.add_child(scene)


func _process(_delta: float) -> void:
	frames += 1
	if frames == 3:
		ok(scene.units.size() >= 2, "tactical units spawned")
		ok(scene.region_id != "", "engagement region picked")
		var enemy_idx := -1
		for i in scene.units.size():
			if scene.units[i]["side"] == 1:
				enemy_idx = i
				break
		ok(enemy_idx >= 0, "enemy present")
		for i in scene.units.size():
			if scene.units[i]["side"] == 0:
				scene.units[i]["target"] = enemy_idx
		scene.speed = 4
		_alive_at_start = _alive(1)
		_hp_at_start = scene.units[enemy_idx]["hp"]
	if frames == 240:
		var moved := false
		for u in scene.units:
			if u["side"] == 0 and u["x"] != 3:
				moved = true
		ok(moved or scene.finished, "units advanced toward target")
	if frames >= 600 or (scene.finished and frames > 30):
		ok(scene.finished or _alive(1) < _alive_at_start or scene.units.any(
			func(u): return float(u["hp"]) < _hp_at_start and int(u["side"]) == 1),
		"battle progressed/finished")
		print("TESTS: %s: %d checks" % [
			"PASS" if failures.is_empty() else "FAIL " + "; ".join(failures), checks])
		quit(0 if failures.is_empty() else 1)


func _alive(side: int) -> int:
	var n := 0
	for u in scene.units:
		if u["side"] == side and u["hp"] > 0:
			n += 1
	return n
