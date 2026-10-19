extends SceneTree
## r6 audit regressions. Each block names the failure it guards:
##  1. F1 used to open the debug console, whose text field then swallowed M/A/D ("dead keys"). F1 must go to the game, the console
##     opens on the backtick only (also on an Arabic layout), and the HUD diagnostic must say where a key dies.
##  2. The nets and the people used to keep working under the map / dialogue / pause (a catch farm that never spoiled).
##  3. A controller that fails to start must say so (stage + reason) and M must not silently toggle the motion mode.
##  4. A negative "pay" must not pay the player; an impossible hire must not change the purse or the crew.
##   godot --headless --fixed-fps 60 --path game --script res://tests/audit_r6.gd     (prints AUDIT6 n checks, m failed)
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


func key(keycode: int, physical: int = -1, shift: bool = false, unicode: int = 0) -> void:
	var ev := InputEventKey.new()
	ev.unicode = unicode      # a real keyboard event carries the typed character; a text field only swallows the key when it has one
	ev.keycode = keycode as Key
	ev.physical_keycode = (keycode if physical < 0 else physical) as Key
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


func _initialize() -> void:
	scene = (load("res://h2d/h2d0.tscn") as PackedScene).instantiate()
	root.add_child(scene)
	_play()


func _play() -> void:
	await frames(10)
	port = scene.get("_port")
	chk(port != null and bool(port.get("enabled")), "the port controller starts")
	chk(str(port.get("setup_stage")) == "done" and str(port.get("setup_error")) == "", "setup reports 'done' with no error (stage '%s')" % str(port.get("setup_stage")))
	await _console_and_keys()
	await _pause_rules()
	await _setup_failures()
	await _money_rules()
	print("AUDIT6 %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)


func _console_and_keys() -> void:
	# a real console (the autoload removes itself in a release template, so the test builds one that stays)
	var con: Node = (load("res://ui/debug_console.gd") as GDScript).new()
	con.set("force_enabled", true)
	con.set("force_enabled", true)
	con.name = "DebugConsole"
	root.add_child(con)
	await frames(2)
	chk(con.has_method("is_open") and not bool(con.call("is_open")), "the console starts closed")
	await key(KEY_F1)
	chk(not bool(con.call("is_open")), "F1 does NOT open the debug console (that was the dead-keys trap)")
	chk(int(scene.get("_key_raw")) > 0 and int(scene.get("_key_game")) == int(scene.get("_key_raw")), "every key so far reached the game: engine %d, game %d" % [int(scene.get("_key_raw")), int(scene.get("_key_game"))])
	var mp: Control = (port.get("ui") as Node).get("map")
	await key(KEY_M)
	chk(mp.visible and bool(mp.call("is_shown")), "after F1, M opens the map")
	await key(KEY_M)
	chk(not mp.visible, "M closes it again")
	# the backtick opens the console, on a Latin and on an Arabic layout (physical key)
	await key(KEY_QUOTELEFT)
	chk(bool(con.call("is_open")), "the backtick opens the console")
	var diag: String = scene.call("_key_diag_line")
	chk(diag.contains("DEBUG CONSOLE IS OPEN"), "the HUD says the console is open: %s" % diag.substr(0, 120))
	await key(KEY_QUOTELEFT)
	chk(not bool(con.call("is_open")), "the backtick closes it")
	await key(0x0630, KEY_QUOTELEFT)
	chk(bool(con.call("is_open")), "ARABIC LAYOUT: the physical backtick key opens it")
	await key(KEY_ESCAPE)
	chk(not bool(con.call("is_open")), "Esc closes it")
	# with the console closed, the map works again
	await key(KEY_M)
	chk(mp.visible, "console closed: M opens the map")
	chk(int(port.get("map_opens")) >= 2, "map_opens counts every successful open (%d)" % int(port.get("map_opens")))
	await key(KEY_ESCAPE)
	chk(not mp.visible, "Esc closes the map")
	con.queue_free()
	await frames(2)
	# a key that something swallows is counted by the engine tap but not by the game: that is how the stage is located
	var le := LineEdit.new()
	scene.add_child(le)
	le.grab_focus()
	await frames(2)
	var raw1: int = int(scene.get("_key_raw"))
	var game1: int = int(scene.get("_key_game"))
	await key(KEY_M, -1, false, 109)
	chk(int(scene.get("_key_raw")) == raw1 + 1, "a key typed into a focused text field is still seen by the engine tap")
	chk(int(scene.get("_key_game")) == game1, "...but never reaches the game (so the diagnostic points at the focus owner)")
	chk(not mp.visible, "...and the map stays closed while a text field holds the focus")
	chk((scene.call("_key_diag_line") as String).contains("FOCUSED CONTROL"), "the HUD names the focused control")
	le.release_focus()
	le.queue_free()
	await frames(2)
	await key(KEY_M, -1, false, 109)
	chk(mp.visible, "focus released: M works again")
	await key(KEY_ESCAPE)


func _pause_rules() -> void:
	var fishing: RefCounted = port.get("fishing")
	var npcs: RefCounted = port.get("npcs")
	var gid: String = str((fishing.get("ground_order") as Array)[0])
	var g: Dictionary = (fishing.get("grounds") as Dictionary)[gid]
	var ctx: Dictionary = scene.call("_port_ctx")
	ctx["sx"] = float(g["x"])
	ctx["sz"] = float(g["z"])
	ctx["speed_kn"] = 0.0
	ctx["sailing"] = true
	ctx["ashore"] = false
	ctx["sea"] = 0.0
	var r: Dictionary = fishing.call("start", float(g["x"]), float(g["z"]), 4, 0.0)
	chk(bool(r["ok"]), "test set-up: the nets go down on %s" % gid)
	# paused clock: nothing is hauled however long we wait
	ctx["paused"] = true
	var t0: float = float(fishing.get("timer"))
	for i in 40:
		port.call("step", 1.0, ctx)
	chk(is_equal_approx(float(fishing.get("timer")), t0) and int(fishing.get("hauls")) == 0, "PAUSED: 40 s under a paused clock bring no haul (timer %.1f)" % float(fishing.get("timer")))
	ctx["paused"] = false
	for i in 14:
		port.call("step", 1.0, ctx)
	chk(int(fishing.get("hauls")) >= 1, "RUNNING: the same 14 s do bring a haul (hauls %d)" % int(fishing.get("hauls")))
	# an open map is modal: the nets wait, the people stand still (the nets are started AFTER the map opens and with no frame in
	# between, because a live frame would stop them: the real ship is not on the ground)
	fishing.call("stop", "test")
	await key(KEY_M)
	chk(bool(port.call("modal")), "test set-up: the map is open")
	fishing.call("start", float(g["x"]), float(g["z"]), 4, 0.0)
	var hauls0: int = int(fishing.get("hauls"))
	for i in 40:
		port.call("step", 1.0, ctx)
	chk(int(fishing.get("hauls")) == hauls0 and int(fishing.get("hauls")) == 0, "MAP OPEN: 40 s bring no haul (hauls %d)" % int(fishing.get("hauls")))
	fishing.call("stop", "test")
	await key(KEY_ESCAPE)
	# people: stand the player among them, once with the clock paused and once running
	var people: Array = npcs.get("people")
	var centre := Vector2(-77.0, -10.6)   # the fish market: the busiest corner
	var ids: Array = []
	for i in people.size():
		var n := people[i] as Dictionary
		if str(n["mode"]) != "stand" and not bool(n["hidden"]) and Vector2(float(n["x"]), float(n["z"])).distance_to(centre) < 60.0:
			ids.append(i)
	chk(ids.size() >= 5, "test set-up: %d walking people near the fish market" % ids.size())
	var ctx2: Dictionary = ctx.duplicate()
	ctx2["ashore"] = true
	ctx2["wx"] = centre.x
	ctx2["wz"] = centre.y
	# (the headless harness has no terrain textures, so nobody finds a walkable target: the idle timers are the observable clock)
	var before := {}
	for i in ids:
		before[i] = [float((people[i] as Dictionary)["timer"]), float((people[i] as Dictionary)["x"]), float((people[i] as Dictionary)["z"])]
	ctx2["paused"] = true
	for i in 30:
		port.call("step", 1.0, ctx2)
	var moved := 0
	for i in ids:
		var n2 := people[i] as Dictionary
		if absf(float(n2["timer"]) - float(before[i][0])) > 0.0001 or absf(float(n2["x"]) - float(before[i][1])) > 0.0001 or absf(float(n2["z"]) - float(before[i][2])) > 0.0001:
			moved += 1
	chk(moved == 0, "PAUSED: no person's clock or position advances while the game clock is paused (%d of %d did)" % [moved, ids.size()])
	ctx2["paused"] = false
	for i in 30:
		port.call("step", 1.0, ctx2)
	moved = 0
	for i in ids:
		var n3 := people[i] as Dictionary
		if absf(float(n3["timer"]) - float(before[i][0])) > 0.0001 or absf(float(n3["x"]) - float(before[i][1])) > 0.0001:
			moved += 1
	chk(moved >= 1, "RUNNING: the same people do advance (%d of %d)" % [moved, ids.size()])


func _setup_failures() -> void:
	var pg_script := load("res://h2d/port_game.gd") as GDScript
	# a world without the port section
	var holder := Object.new()
	holder.set_script(load("res://tests/audit_fake_world.gd"))
	var layer := CanvasLayer.new()
	root.add_child(layer)
	var pg: Node = pg_script.new()
	root.add_child(pg)
	pg.call("setup", layer, holder, {}, func(_on: bool) -> void: pass)
	chk(not bool(pg.get("enabled")), "a world with no port section leaves the controller OFF")
	chk(str(pg.get("setup_error")).contains("no port section"), "...and says why: '%s'" % str(pg.get("setup_error")))
	chk(str(pg.get("setup_stage")) == "start", "...and names the stage it stopped at ('%s')" % str(pg.get("setup_stage")))
	var ev := InputEventKey.new()
	ev.keycode = KEY_M
	ev.physical_keycode = KEY_M
	ev.pressed = true
	chk(not bool(pg.call("handle_key", ev, {})), "a disabled controller does not swallow keys")
	# malformed documents are named, not crashed on
	var probs: Array = pg_script.call("_doc_problems", {}, {}, {})
	chk(probs.size() == 3, "three empty documents give three problems (%d)" % probs.size())
	probs = pg_script.call("_doc_problems", {"species": {"a": 1}}, {"recruits": {"x": {}}, "order": ["x", "ghost"]}, {"grounds": {"g": {}}})
	chk(probs.size() == 1 and str(probs[0]).contains("ghost"), "a recruit order naming an undefined recruit is reported (%s)" % str(probs))
	probs = pg_script.call("_doc_problems", {"species": {"a": 1}}, {"recruits": {"x": {}}, "order": ["x"]}, {"grounds": {"g": {}}})
	chk(probs.is_empty(), "good documents give no problem")
	layer.queue_free()
	pg.queue_free()
	# on the live scene: a disabled controller must make M say so instead of cycling the ship motion
	var v3: Object = scene.get("_v3")
	var mm: int = int(v3.get("motion_mode"))
	port.set("enabled", false)
	await key(KEY_M)
	chk(int(v3.get("motion_mode")) == mm, "controller OFF: plain M does not toggle the ship motion")
	port.set("enabled", true)


func _money_rules() -> void:
	var state: RefCounted = port.get("state")
	var ui: Node = port.get("ui")
	var reales0: int = int(state.get("reales"))
	# a "pay" option with a negative argument
	var dlg: Control = ui.get("dialogue")
	dlg.set("_view", {"options": [{"label": "x", "enabled": true, "hint": "", "action": "pay", "arg": "-50", "next": "", "fail": ""}]})
	port.set("_spk", {"id": "npc_test", "tree": "fishmonger", "cid": ""})
	port.call("_on_choice", 0)
	chk(int(state.get("reales")) <= reales0, "a negative 'pay' never adds money (%d -> %d)" % [reales0, int(state.get("reales"))])
	# hiring without the money, and hiring twice
	var cid: String = str(state.call("cheapest_unhired"))
	state.set("reales", int(state.call("cost_of", cid)) - 1)
	chk(str(state.call("hire", cid)) == "poor", "hire: too poor is refused")
	chk(int(state.get("reales")) == int(state.call("cost_of", cid)) - 1 and not bool(state.call("is_hired", cid)), "...and changes nothing")
	state.set("reales", 1000)
	chk(str(state.call("hire", cid)) == "ok" and int(state.get("reales")) == 1000 - int(state.call("cost_of", cid)), "hire: the price is paid once")
	chk(str(state.call("hire", cid)) == "already" and int(state.get("reales")) == 1000 - int(state.call("cost_of", cid)), "hire: a second hire is refused and costs nothing")
	# selling twice pays once
	state.call("add_catch", "fish_mackerel" if (state.get("fish") as Dictionary).has("fish_mackerel") else str((state.get("fish") as Dictionary).keys()[0]), 5.0, 0.0)
	var r1: Dictionary = state.call("sell_all", 0.0)
	var money1: int = int(state.get("reales"))
	var r2: Dictionary = state.call("sell_all", 0.0)
	chk(int(r1["reales"]) > 0 and int(r2["reales"]) == 0 and int(state.get("reales")) == money1, "selling the same hold twice pays only once")
	# the dialogue for a missing person is explained, not silent
	port.call("_open_dialogue", -1, {"wx": 0.0, "wz": 0.0})
	chk(not bool(port.call("modal")), "a missing speaker leaves no dialogue open")
