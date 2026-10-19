extends SceneTree
## Plays the real scene headless: godot --headless --fixed-fps 60 --path game --script res://tests/selfplay.gd
## Sends real key events through the viewport, so the routing (_unhandled_input, modal panels, pause) is exercised.
## No rendering happens (dummy renderer): this proves the logic and that no script errors occur, not how it looks.
var checks := 0
var fails := 0
var scene: Node
var port: Node


func chk(cond: bool, msg: String) -> void:
	checks += 1
	if not cond:
		fails += 1
		print("  FAIL: ", msg)


func frames(n: int) -> void:
	for i in n:
		await process_frame


func key(code: int, shift: bool = false) -> void:
	var ev := InputEventKey.new()
	ev.keycode = code as Key
	ev.physical_keycode = code as Key
	ev.shift_pressed = shift
	ev.pressed = true
	root.push_input(ev, false)
	await process_frame
	var up := InputEventKey.new()
	up.keycode = code as Key
	up.pressed = false
	root.push_input(up, false)
	await process_frame


func _initialize() -> void:
	var ps := load("res://h2d/h2d0.tscn") as PackedScene
	scene = ps.instantiate()
	root.add_child(scene)
	_play()


func _paused() -> bool:
	return (scene.get("_state").clock.pause_reasons() as Array).has("port")


func _play() -> void:
	await frames(10)
	port = scene.get("_port")
	chk(port != null and bool(port.get("enabled")), "the port controller is enabled")
	var ui: Control = port.get("ui")
	chk(ui != null, "the interface exists")
	# ---- the map ------------------------------------------------------------------------------------------------
	await key(KEY_M)
	chk(bool(port.call("modal")), "M opens a modal panel")
	chk(str((ui.get("panel") as Dictionary).get("kind", "")) == "map", "the panel is the map")
	chk(_paused(), "the clock is paused while the map is open")
	await frames(3)
	chk(int(ui.get("draw_count")) > 0, "the interface _draw ran (%d times)" % int(ui.get("draw_count")))
	print("SIZE ", ui.size, " vis ", ui.is_visible_in_tree(), " font ", ui.get("_font"))
	await key(KEY_TAB)
	await key(KEY_M)
	chk(not bool(port.call("modal")), "M closes the map")
	chk(not _paused(), "the clock runs again after the map closes")
	# ---- fishing ------------------------------------------------------------------------------------------------
	var st: RefCounted = port.get("state")
	var fi: RefCounted = port.get("fishing")
	await key(KEY_F)
	chk(not bool(fi.get("active")), "F outside a ground does not start the nets")
	print("TOASTS after F outside: ", ui.get("toasts"))
	scene.set("_pos", Vector2(-300.0, 560.0))
	await frames(5)
	print("HUD prompt in ground: '", (ui.get("hud") as Dictionary).get("prompt", ""), "' speed ", scene.get("_helm").get("speed_kn"), " sea ", scene.get("_env").get("sea"))
	await key(KEY_F)
	chk(bool(fi.get("active")), "F inside Pilchard Shallows lowers the nets")
	print("TOASTS after F inside: ", ui.get("toasts"))
	await frames(60)
	print("status ", fi.get("status"), " speed ", scene.get("_helm").get("speed_kn"), " pos ", scene.get("_pos"))
	await frames(60 * 14)
	print("status ", fi.get("status"), " speed ", scene.get("_helm").get("speed_kn"), " hauls ", fi.get("hauls"), " hold ", st.call("hold_kg"), " pos ", scene.get("_pos"), " active ", fi.get("active"))
	print("SELFPLAY: %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0)
