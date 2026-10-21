extends SceneTree
## The map INSIDE the real game scene (res://h2d/h2d0.tscn), with real key events pushed through the window viewport:
##   godot --headless --fixed-fps 60 --path game --script res://tests/map_flow.gd        (prints MAPFLOW n checks, m failed)
## Proves: M works at sea, at the pier, ashore, with focus on a button, on other layouts; the clock pause belongs to the map and is
## released exactly; dialogue, fishing, recruiting and the ship controls are unharmed. The layout itself (a real window size) is
## proved by tests/map_screen_test.gd (SubViewports) and tools/godot_browser/scenarios/map_screen.mjs (a real renderer).
var checks := 0
var fails := 0
var scene: Node
var port: Node
var mp: Node


func chk(cond: bool, msg: String) -> void:
	checks += 1
	if not cond:
		fails += 1
		print("  FAIL: ", msg)


func frames(n: int) -> void:
	for i in n:
		await process_frame


func key(code: int, physical: int = -1, shift: bool = false) -> void:
	var ev := InputEventKey.new()
	ev.keycode = code as Key
	ev.physical_keycode = (code if physical < 0 else physical) as Key
	ev.shift_pressed = shift
	ev.pressed = true
	root.push_input(ev, false)
	await process_frame
	var up := InputEventKey.new()
	up.keycode = ev.keycode
	up.physical_keycode = ev.physical_keycode
	up.pressed = false
	root.push_input(up, false)
	await process_frame


func hold(code: int, on: bool) -> void:
	var e := InputEventKey.new()
	e.keycode = code as Key
	e.physical_keycode = code as Key
	e.pressed = on
	Input.parse_input_event(e)


func reasons() -> Array:
	return Array(scene.get("_state").clock.pause_reasons())


func _initialize() -> void:
	scene = (load("res://h2d/h2d0.tscn") as PackedScene).instantiate()
	root.add_child(scene)
	_play()


func _play() -> void:
	await frames(10)
	port = scene.get("_port")
	mp = scene.get("_map")
	chk(port != null and bool(port.get("enabled")), "the port controller is enabled")
	chk(mp != null and str(mp.get("init_error")) == "", "the map screen is in the game and intact")
	if mp == null or port == null:
		quit(1)
		return
	chk(not bool(mp.call("is_open")), "the map starts closed")
	chk((mp.call("button_node", "open") as Button).visible, "the MAP button is on screen from the start")
	await _at_sea()
	await _controls()
	await _ashore()
	await _dialogue()
	await _fishing_and_ship()
	await _recruiting()
	await _pause_exactness()
	print("MAPFLOW %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)


func _at_sea() -> void:
	var r0 := reasons()
	var pos0: Vector2 = scene.get("_pos")
	await key(KEY_M)
	chk(bool(mp.call("is_open")), "AT SEA: M opens the map")
	chk(int(mp.get("tab")) == 2, "AT SEA: it opens on the Sea tab (%d)" % int(mp.get("tab")))
	chk(reasons().has("map"), "AT SEA: the clock is paused by the reason 'map'")
	await frames(30)
	chk((scene.get("_pos") as Vector2).distance_to(pos0) < 0.01, "AT SEA: the ship does not move while the chart is open")
	await key(KEY_M)
	chk(not bool(mp.call("is_open")), "AT SEA: M closes it")
	chk(reasons() == r0, "AT SEA: the pause reasons are exactly as before (%s)" % str(reasons()))
	await frames(60)
	chk((scene.get("_pos") as Vector2).distance_to(pos0) > 0.5, "AT SEA: the ship sails again after closing (moved %.1f m)" % (scene.get("_pos") as Vector2).distance_to(pos0))
	# other layouts and the button
	await key(0x0629, KEY_M)
	chk(bool(mp.call("is_open")), "AT SEA: Arabic layout M opens it")
	await key(KEY_ESCAPE)
	chk(not bool(mp.call("is_open")) and not reasons().has("map"), "AT SEA: Esc closes it and releases the pause")
	(mp.call("button_node", "open") as Button).pressed.emit()
	await frames(2)
	chk(bool(mp.call("is_open")), "AT SEA: the MAP button opens it")
	(mp.call("button_node", "close") as Button).pressed.emit()
	await frames(2)
	chk(not bool(mp.call("is_open")) and not reasons().has("map"), "AT SEA: the Close button closes it and releases the pause")
	# 30 cycles: nothing leaks
	for i in 30:
		await key(KEY_M)
		await key(KEY_M)
	chk(not bool(mp.call("is_open")) and reasons() == r0 and int(mp.get("fail_count")) == 0, "30 open/close cycles: closed, same pause reasons, no failure")
	# Shift+M is still the ship-motion toggle and does not open the map
	var v3: Object = scene.get("_v3")
	var m0: int = int(v3.get("motion_mode"))
	await key(KEY_M, -1, true)
	chk(not bool(mp.call("is_open")) and int(v3.get("motion_mode")) == (m0 + 1) % 3, "Shift+M still toggles the ship motion and does not open the map")
	await key(KEY_M, -1, true)
	await key(KEY_M, -1, true)


func _controls() -> void:
	# held keys: while the map is open the ship and the walker ignore them; after closing they work
	hold(KEY_A, true)
	await frames(2)
	chk(float(scene.call("_steer_axis")) < -0.5, "the helm reads A (map closed)")
	await key(KEY_M)
	chk(bool(mp.call("is_open")) and float(scene.call("_steer_axis")) == 0.0, "with the map open the helm ignores A")
	await key(KEY_M)
	chk(float(scene.call("_steer_axis")) < -0.5, "after closing, the helm reads A again")
	hold(KEY_A, false)
	await frames(2)
	# SPACE (dock / cast off) is swallowed by the map and works after it
	var hs0: int = int(scene.get("_harbor").get("state"))
	await key(KEY_M)
	await key(KEY_SPACE)
	chk(int(scene.get("_harbor").get("state")) == hs0 and bool(mp.call("is_open")), "SPACE does nothing to the ship while the map is open")
	await key(KEY_ESCAPE)

	await key(KEY_SPACE)
	chk(str(scene.get("_banner")) != "" and not bool(mp.call("is_open")), "SPACE works again after closing (the helm answers: '%s')" % str(scene.get("_banner")).substr(0, 50))


func _ashore() -> void:
	var walker: RefCounted = scene.get("_walker")
	var land: Dictionary = (scene.get("_v3") as Object).call("land_world").meta["land"]
	walker.call("disembark", land)
	await frames(3)
	var wx: float = float(walker.get("x"))
	var wz: float = float(walker.get("z"))
	await key(KEY_M)
	chk(bool(mp.call("is_open")) and int(mp.get("tab")) == 0, "ASHORE: M opens the City tab")
	chk(Array(mp.call("rows_text")).size() >= 10, "ASHORE: the list shows %d places" % Array(mp.call("rows_text")).size())
	chk((mp.call("marker_screen_pos", "__you") as Vector2).x != -1.0, "ASHORE: a YOU marker exists")
	hold(KEY_D, true)
	hold(KEY_S, true)
	await frames(30)
	chk(is_equal_approx(float(walker.get("x")), wx) and is_equal_approx(float(walker.get("z")), wz), "ASHORE: W A S D move the chart, not the player, while the map is open")
	await key(KEY_M)
	await frames(30)
	chk(absf(float(walker.get("x")) - wx) + absf(float(walker.get("z")) - wz) > 0.5, "ASHORE: after closing, held D and S walk the player again")
	hold(KEY_D, false)
	hold(KEY_S, false)
	await frames(3)
	# the pier: docked, still ashore false -> City tab
	var land_ok := bool(walker.call("is_ashore"))
	chk(land_ok, "(player is ashore)")
	# the notice board opens the map through the port controller
	walker.set("x", 13.0)
	walker.set("z", 1.6)
	await frames(10)
	await key(KEY_E)
	chk(bool(mp.call("is_open")), "ASHORE: E at the notice board opens the map")
	await key(KEY_ESCAPE)
	chk(not bool(mp.call("is_open")) and not reasons().has("map"), "ASHORE: Esc closes it, pause released")
	# a focused button does not stop M
	var b := Button.new()
	root.add_child(b)
	b.grab_focus()
	await frames(2)
	await key(KEY_M)
	chk(bool(mp.call("is_open")), "ASHORE: M opens the map while a Button has the focus")
	await key(KEY_M)
	b.queue_free()
	await frames(2)


func _dialogue() -> void:
	var walker: RefCounted = scene.get("_walker")
	var np: RefCounted = port.get("npcs")
	var people: Array = np.get("people")
	var ip: int = int(np.call("index_of", "npc_pip_larkin"))
	var pip := people[ip] as Dictionary
	walker.set("x", float(pip["x"]) + 1.6)
	walker.set("z", float(pip["z"]) + 0.8)
	await frames(10)
	await key(KEY_E)
	var dui: Control = (port.get("ui") as Node).get("dialogue")
	chk(dui.call("is_open"), "DIALOGUE: E opens Pip's window")
	var toasts0: int = int(((port.get("ui") as Node).get("hud") as Control).get("shown_toasts"))
	await key(KEY_M)
	chk(not bool(mp.call("is_open")) and dui.call("is_open"), "DIALOGUE: M does not open the map over the conversation")
	chk(int(((port.get("ui") as Node).get("hud") as Control).get("shown_toasts")) > toasts0, "DIALOGUE: the player is told why")
	await frames(60)
	var guard := 0
	while bool(dui.call("is_open")) and guard < 12:
		await key(KEY_ESCAPE)
		guard += 1
	chk(not bool(dui.call("is_open")) and not reasons().has("port"), "DIALOGUE: Esc closes it and releases its pause")
	await key(KEY_M)
	chk(bool(mp.call("is_open")), "DIALOGUE: after the conversation M opens the map")
	await key(KEY_M)
	await frames(10)
	await key(KEY_E)
	chk(dui.call("is_open"), "DIALOGUE: after the map, E opens the conversation again")
	guard = 0
	while bool(dui.call("is_open")) and guard < 12:
		await key(KEY_ESCAPE)
		guard += 1
	chk(not bool(dui.call("is_open")), "DIALOGUE: closed again")


func _fishing_and_ship() -> void:
	var walker: RefCounted = scene.get("_walker")
	walker.call("board")
	await frames(5)
	var fi: RefCounted = port.get("fishing")
	scene.set("_pos", Vector2(-300.0, 560.0))
	await frames(5)
	await key(KEY_F)
	chk(not bool(fi.get("active")), "FISHING: F at the helm in the Pilchard Shallows does NOT lower a net (CP-2B.1: fishing is only at the winch)")
	await frames(120)
	await key(KEY_M)
	chk(bool(mp.call("is_open")), "FISHING: M opens the map on a ground")
	chk(int(mp.get("tab")) == 2, "FISHING: it opens on the Sea tab")
	await frames(120)
	await key(KEY_M)
	await frames(60)
	chk(float((port.get("state") as RefCounted).call("hold_kg")) == 0.0, "FISHING: nothing came aboard while the map was open or closed (hold %.2f kg)" % float((port.get("state") as RefCounted).call("hold_kg")))


func _recruiting() -> void:
	var st: RefCounted = port.get("state")
	var walker: RefCounted = scene.get("_walker")
	var land: Dictionary = (scene.get("_v3") as Object).call("land_world").meta["land"]
	walker.call("disembark", land)
	await frames(3)
	var crew0: int = int(st.call("crew_count"))
	st.set("reales", 200)
	port.call("_hire", "crew_pip_larkin")
	await frames(2)
	chk(int(st.call("crew_count")) == crew0 + 1, "RECRUIT: Pip is hired (crew %d -> %d)" % [crew0, int(st.call("crew_count"))])
	await key(KEY_M)
	await frames(2)
	var rows: String = str(mp.call("rows_text"))
	chk(rows.contains("aboard your ship"), "RECRUIT: the map shows Pip as aboard your ship")
	chk(rows.contains("reales"), "RECRUIT: the others show their price")
	await key(KEY_ESCAPE)
	chk(not bool(mp.call("is_open")), "RECRUIT: map closed")
	walker.call("board")
	await frames(3)


func _pause_exactness() -> void:
	# a pause the PLAYER set (P) must survive the map exactly
	var clock: RefCounted = scene.get("_state").clock
	await key(KEY_P)
	var before := reasons()
	chk(before.has("menu"), "P pauses (reason 'menu')")
	await key(KEY_M)
	chk(bool(mp.call("is_open")) and reasons().has("map") and reasons().has("menu"), "with P pause on, opening the map adds its own reason")
	await key(KEY_M)
	chk(reasons() == before, "closing the map leaves the P pause exactly as it was (%s)" % str(reasons()))
	await key(KEY_P)
	chk(not clock.call("is_paused"), "P resumes: nothing is left paused")
	# a stuck pause is released by the watchdog
	clock.call("pause", "map")
	await frames(3)
	chk(not reasons().has("map"), "the watchdog releases a 'map' pause when no map is open")
	chk(not clock.call("is_paused"), "the game is running")
