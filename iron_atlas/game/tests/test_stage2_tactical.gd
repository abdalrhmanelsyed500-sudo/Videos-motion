extends SceneTree
## UI-level retreat and tactical battle consequences, staged after _ready.
var checks := 0
var failures: Array = []
var frame := 0
var GS = null
var scene = null
var first_enemy := ""
var first_enemy_count := 0
var first_player := ""


func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures.append(label)


func _initialize() -> void:
	GS = root.get_node("GameState")
	setup_battle(400)


func setup_battle(seed_int: int) -> void:
	GS.new_campaign(seed_int)
	var st = GS.cs
	var a: Dictionary = st.formations_of(st.player_id())[0]
	var b: Dictionary = st.formations_of("cty_vardena")[0]
	b["region"] = a["region"]
	first_player = a["id"]
	first_enemy = b["id"]
	first_enemy_count = int(b["units"][0]["count"])
	GS.tactical_region = a["region"]
	scene = load("res://scenes/tactical_map.tscn").instantiate()
	root.add_child(scene)


func _process(_delta: float) -> void:
	frame += 1
	if frame == 3:
		check(scene.region_id == GS.tactical_region and scene.units.size() > 1, "requested hostile contact opens")
		check(scene.unit_textures.size() == 7 and scene.tile_textures.size() == 8, "committed pixel sprites decode for tactical view")
		var reports_before: int = GS.cs.reports.size()
		scene._on_hud("end")
		check(scene.finished and scene.result_text.begins_with("RETREAT"), "retreat button does not manufacture victory")
		check(int(GS.cs.formations[first_enemy]["units"][0]["count"]) == first_enemy_count, "retreat does not fabricate enemy casualties")
		check(GS.cs.reports.size() > reports_before and GS.cs.finalized_battles.size() == 1, "retreat creates one real battle report")
		check(scene.hud["back"].visible, "result remains readable until player returns")
		scene.queue_free()
	if frame == 5:
		setup_battle(401)
	if frame == 8:
		var player_index := -1
		var enemy_index := -1
		for i in scene.units.size():
			if scene.units[i]["side"] == 0 and player_index < 0:
				player_index = i
			if scene.units[i]["side"] == 1 and enemy_index < 0:
				enemy_index = i
		check(player_index >= 0 and enemy_index >= 0, "tactical sides are present")
		GS.cs.formations[first_player]["ammo_reserve"] = 0.8
		scene._fire(scene.units[player_index], scene.units[enemy_index])
		check(float(GS.cs.formations[first_player]["ammo_reserve"]) < 0.8, "tactical fire consumes strategic ammunition")
		var saved_rng: int = GS.cs.rng_state
		scene.units[enemy_index]["hp"] = 10.0
		GS.cs.formations[first_player]["ammo_reserve"] = 1.0
		scene._fire(scene.units[player_index], scene.units[enemy_index])
		var full_damage := 10.0 - float(scene.units[enemy_index]["hp"])
		GS.cs.rng_state = saved_rng
		GS.cs.reseed()
		scene.units[enemy_index]["hp"] = 10.0
		GS.cs.formations[first_player]["ammo_reserve"] = 0.0
		scene._fire(scene.units[player_index], scene.units[enemy_index])
		check(10.0 - float(scene.units[enemy_index]["hp"]) < full_damage * 0.2, "empty ammunition severely reduces tactical fire")
		scene._on_hud("pause")
		var acc: float = scene.tick_acc
		scene._process(10.0)
		check(scene.paused and scene.tick_acc == acc, "tactical pause stops time")
		for u in scene.units:
			if u["side"] == 1:
				u["hp"] = 0.0
		scene.units[player_index]["hp"] = 0.0
		var enemy_before := first_enemy_count
		scene._finish(true)
		check(scene.finished and scene.result_text.begins_with("VICTORY"), "wiped opponent produces victory")
		check(int(GS.cs.formations[first_enemy]["units"][0]["count"]) < enemy_before, "enemy tactical losses persist")
		check(int(GS.cs.formations[first_player]["wounded"]) > 0, "friendly tactical wounds persist")
		check(not GS.cs.regions[scene.region_id]["salvage"].is_empty(), "tactical equipment salvage persists")
		var battles: int = GS.cs.finalized_battles.size()
		scene._finish(true)
		check(GS.cs.finalized_battles.size() == battles, "tactical finish cannot apply twice")
		print("TESTS: %s: %d checks" % ["PASS" if failures.is_empty() else "FAIL " + "; ".join(failures), checks])
		quit(0 if failures.is_empty() else 1)
