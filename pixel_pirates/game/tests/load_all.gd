extends SceneTree
## Loads (compiles) every .gd file of the project and reports parse errors: godot --headless --script res://tests/load_all.gd
func _initialize() -> void:
	var bad := 0
	var n := 0
	for dir in ["res://core", "res://h2d", "res://ui", "res://tests"]:
		var d := DirAccess.open(dir)
		if d == null:
			continue
		for f in d.get_files():
			if f.ends_with(".gd"):
				n += 1
				var s := load(dir + "/" + f) as GDScript
				if s == null or not s.can_instantiate():
					bad += 1
					print("LOADFAIL ", dir, "/", f)
	print("LOADALL: %d scripts, %d failed" % [n, bad])
	quit(1 if bad > 0 else 0)
