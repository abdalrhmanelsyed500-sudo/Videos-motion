extends SceneTree
## District data contract + live build checks on the real loop (--fixed-fps 60).
## Prints TESTS line like run_one.

var checks := 0
var fails := 0
var frame := 0
var dist: Node3D = null


func check(cond: bool, msg: String) -> void:
	checks += 1
	if not cond:
		fails += 1
		print("  FAIL: ", msg)


func _in_strip(p: Vector2, s: Dictionary, margin: float) -> bool:
	var cx: float = float(s.get("cx", 0))
	var cz: float = float(s.get("cz", 0))
	var w: float = float(s.get("w", 8)) / 2.0 + margin
	var d: float = float(s.get("d", 8)) / 2.0 + margin
	var ry: float = float(s.get("ry", 0))
	var dx: float = p.x - cx
	var dz: float = p.y - cz
	var c := cos(-ry)
	var s2 := sin(-ry)
	var lx := dx * c - dz * s2
	var lz := dx * s2 + dz * c
	return absf(lx) <= w and absf(lz) <= d


func _initialize() -> void:
	pass


func _process(_d: float) -> void:
	frame += 1
	if frame == 6:
		_data_checks()
		dist = (load("res://scenes/world/district_p1.tscn") as PackedScene).instantiate()
		root.add_child(dist)
	elif frame == 20:
		_scene_checks()
		_finish()


func _data_checks() -> void:
	var reg: Node = root.get_node("Reg")
	var probs: Array = reg.call("validate")
	check(probs.is_empty(), "registry validates: %s" % str(probs))
	var d: Dictionary = reg.call("district")
	var roads: Array = d.get("roads", [])
	check(roads.size() >= 6, "road network present (%d strips)" % roads.size())
	for key in ["pickup", "dest", "start"]:
		var pt: Dictionary = d[key]
		var p := Vector2(float(pt["x"]), float(pt["z"]))
		var on := false
		for r in roads:
			if _in_strip(p, r, 0.5):
				on = true
		check(on, "%s sits on a road" % key)
	for b in d.get("buildings", []):
		var bp := Vector2(float(b["x"]), float(b["z"]))
		var hit := false
		for r in roads:
			if _in_strip(bp, r, 11.5):
				hit = true
		check(not hit, "building %s clear of roads" % str(b.get("m")))
	var women := 0
	for c in reg.call("cast"):
		if bool(c.get("hijab", false)):
			women += 1
			check(String(c.get("hijab_col", "")) != "", "hijab cast has scarf colour")
	check(women >= 2, "cast includes hijab-wearing women (%d)" % women)


func _scene_checks() -> void:
	check(dist.get_node_or_null("Tuktuk") != null, "tuktuk in district")
	check(dist.get_node_or_null("ChaseCam") != null, "chase camera in district")
	check(dist.get_node_or_null("HUD") != null, "HUD in district")
	check(dist.get("passenger") != null, "passenger spawned at the stand")
	var meshes := 0
	for ch in dist.get_children():
		if ch is MeshInstance3D:
			meshes += 1
	check(meshes >= 20, "district surfaces/buildings/props built (%d mesh nodes)" % meshes)
	var arrow: Node3D = dist.get("_arrow")
	check(arrow != null and not arrow.visible, "destination arrow hidden before driving")


func _finish() -> void:
	print("TESTS: %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)
