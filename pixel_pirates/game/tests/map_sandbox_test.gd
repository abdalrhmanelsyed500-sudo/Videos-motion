extends SceneTree
## Loads the sandbox scene, presses M, checks the map opens on its own: godot --headless --script res://tests/map_sandbox_test.gd
func _initialize() -> void:
	var s := (load("res://ui/map/map_sandbox.tscn") as PackedScene).instantiate()
	root.add_child(s)
	_go(s)


func _go(s: Node) -> void:
	for i in 5:
		await process_frame
	var mp: Node = s.get("_map")
	var ok1: bool = mp != null and not bool(mp.call("is_open"))
	var ev := InputEventKey.new()
	ev.keycode = KEY_M
	ev.physical_keycode = KEY_M
	ev.pressed = true
	root.push_input(ev, false)
	await process_frame
	await process_frame
	var ok2: bool = bool(mp.call("is_open"))
	var tabs: int = (mp.get("views") as Array).size()
	mp.call("close_map")
	var ok3: bool = not bool(mp.call("is_open"))
	var good: bool = ok1 and ok2 and ok3 and tabs == 3
	print("MAPSANDBOX closed-at-start %s, M opens %s, tabs %d, closes %s -> %s" % [ok1, ok2, tabs, ok3, "PASS" if good else "FAIL"])
	quit(0 if good else 1)
