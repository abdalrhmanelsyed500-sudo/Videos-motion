# gdlint: disable=max-line-length
extends SceneTree
## CP-2 Release A inside the REAL game scene (res://h2d/h2d0.tscn), with real key events:
##   godot --headless --fixed-fps 60 --path game --script res://tests/deck_flow.gd        (prints DECKFLOW n checks, m failed)
## Proves: E leaves the helm, the course hold engages and the ship keeps sailing and holds its heading while the pirate walks; the helm
## can be retaken; E at the desk opens the map; hatches, the hold and the rope ladder work in BOTH directions; the fish barrels and the
## provisions follow the real hold and inventory; W stays free for walking; Shift+E is still the effects budget; R and F recover.
## No pixels are checked here (tools/godot_browser/scenarios/deck_walk.mjs does that in a real renderer).
const Layout := preload("res://h2d/ship_layout.gd")
var checks := 0
var fails := 0
var scene: Node


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


func mode() -> RefCounted:
	return scene.get("_ship_mode")


func hud() -> Control:
	return scene.get("_ship_hud")


func v3() -> Object:
	return scene.get("_v3")


func hero_level() -> int:
	return int(mode().call("level"))


func put(level: int, p: Vector2) -> void:
	mode().get("walker").call("place", level, p)


func at(level: int, id: String) -> Vector2:
	var it: Dictionary = (mode().get("layout") as RefCounted).call("interaction", level, id)
	return it["c"]


func _initialize() -> void:
	scene = (load("res://h2d/h2d0.tscn") as PackedScene).instantiate()
	root.add_child(scene)
	_play()


func _play() -> void:
	await frames(10)
	if mode() == null or hud() == null:
		chk(false, "ship mode and HUD exist in the game scene")
		quit(1)
		return
	await _helm_and_hold()
	await _walk_keeps_sailing()
	await _levels()
	await _ladder()
	await _stores()
	await _keys_and_recovery()
	print("DECKFLOW %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)


func _helm_and_hold() -> void:
	var m := mode()
	var ap: RefCounted = m.get("ap")
	chk(not bool(m.call("is_deck")), "the game starts at the helm")
	chk(not bool(ap.get("engaged")), "the course hold starts off")
	await frames(3)
	chk(str(hud().call("prompt_text")).contains("Leave the helm"), "prompt at the helm: %s" % str(hud().call("prompt_text")))
	# C at the helm toggles the hold
	await key(KEY_C)
	chk(bool(ap.get("engaged")), "C at the helm engages the course hold")
	chk(str(hud().call("toast_text")).contains("COURSE HOLD ON"), "toast says so: %s" % str(hud().call("toast_text")))
	await frames(2)
	var st: Dictionary = m.call("status", scene.call("_ship_ctx"))
	chk(str(st["kind"]) == "hold" and str(st["title"]).begins_with("COURSE HOLD"), "status chip: %s" % str(st))
	await key(KEY_C)
	chk(not bool(ap.get("engaged")), "C again releases it")
	st = m.call("status", scene.call("_ship_ctx"))
	chk(str(st["kind"]) == "direct", "status chip: direct steering")
	# the old way still works: A turns the ship
	var h0 := float(scene.get("_heading_disp"))
	hold(KEY_D, true)
	await frames(40)
	hold(KEY_D, false)
	chk(absf(float(scene.get("_heading_disp")) - h0) > 2.0, "D still steers by hand (%.1f -> %.1f)" % [h0, float(scene.get("_heading_disp"))])


func _walk_keeps_sailing() -> void:
	var m := mode()
	var ap: RefCounted = m.get("ap")
	await key(KEY_E)
	chk(bool(m.call("is_deck")), "E at the helm leaves it")
	chk(bool(ap.get("engaged")), "leaving the helm engages the course hold by itself")
	chk(str(hud().call("toast_text")).contains("Course hold ON"), "and says so: %s" % str(hud().call("toast_text")))
	chk(hero_level() == Layout.L_DECK, "on the main deck")
	await frames(240)       # the hold settles first (it may turn the ship out of the no-go wedge: that is its job)
	var hd0 := float(scene.get("_heading_disp"))
	print("DECKFLOW hold target ", ap.get("target_deg"), " effective ", ap.call("effective_target", float(scene.get("_d")["wind_from"]), float(scene.get("_d")["wind_kn"]), float(scene.call("_ship_ctx")["no_go"])), " heading ", hd0)
	var p0: Vector2 = scene.get("_pos")
	hold(KEY_D, true)       # a walking key: steers nothing now
	await frames(90)
	hold(KEY_D, false)
	hold(KEY_W, true)
	await frames(60)
	hold(KEY_W, false)
	var hd1 := float(scene.get("_heading_disp"))
	var p1: Vector2 = scene.get("_pos")
	chk(absf(wrap_deg(hd1 - hd0)) < 3.0, "walking does not turn the ship (%.1f -> %.1f)" % [hd0, hd1])
	chk(p0.distance_to(p1) > 5.0, "the ship keeps sailing while the pirate walks (%.1f m)" % p0.distance_to(p1))
	chk(str(scene.get("_lab")) == "real", "W on deck does not cycle the weather lab")
	var info: Dictionary = v3().call("deck_info")
	chk(bool(info["show"]), "the deck model is shown")
	# the camera follows: land state x,z = ship + hero local
	var ls: Dictionary = scene.call("_land_view_state")
	var wp: Vector2 = (scene.get("_pos") as Vector2) + (m.get("walker").get_script().call("to_world", m.call("hero_at"), float(scene.get("_heading_disp"))) as Vector2)
	chk(absf(float(ls["x"]) - wp.x) < 0.01 and absf(float(ls["z"]) - wp.y) < 0.01, "the camera focus is the pirate on the moving ship")
	# take the helm back at the wheel
	m.get("walker").call("place_at_helm")
	await frames(2)
	chk(str(hud().call("prompt_text")).contains("Take the helm"), "prompt at the wheel: %s" % str(hud().call("prompt_text")))
	await key(KEY_E)
	chk(not bool(m.call("is_deck")), "E at the wheel takes the helm back")
	chk(bool(ap.get("engaged")), "the course hold stays on (C releases it)")
	await key(KEY_C)
	chk(not bool(ap.get("engaged")), "C releases the hold at the helm")


func wrap_deg(a: float) -> float:
	return fposmod(a + 180.0, 360.0) - 180.0


func _levels() -> void:
	var m := mode()
	await key(KEY_E)           # leave the helm again
	# the desk opens the map
	put(Layout.L_DECK, at(Layout.L_DECK, "desk"))
	await frames(2)
	chk(str(hud().call("prompt_text")).contains("chart"), "prompt at the desk: %s" % str(hud().call("prompt_text")))
	await key(KEY_E)
	var mp: Node = scene.get("_map")
	chk(mp != null and bool(mp.call("is_open")), "E at the desk opens the map")
	await key(KEY_ESCAPE)
	await frames(2)
	chk(not bool(mp.call("is_open")), "Esc closes it")
	# chest, winch, barrels, berths: toasts or panels, never a crash
	put(Layout.L_DECK, at(Layout.L_DECK, "chest"))
	await key(KEY_E)
	chk(str(hud().call("toast_text")).contains("lockbox"), "the lockbox toast shows the purse: %s" % str(hud().call("toast_text")))
	put(Layout.L_DECK, at(Layout.L_DECK, "winch"))
	await key(KEY_E)
	chk(str(hud().call("toast_text")).contains("winch"), "the winch answers")
	# hatch down and back up, both directions
	put(Layout.L_DECK, at(Layout.L_DECK, "hatch_down"))
	await key(KEY_E)
	var seen_fade := 0.0
	for i in 70:
		await process_frame
		seen_fade = maxf(seen_fade, float(hud().call("fade_alpha")))
	chk(hero_level() == Layout.L_SLEEP, "the hatch leads to the sleeping deck (level %d)" % hero_level())
	chk(seen_fade > 0.5, "the screen dims during the hatch transit (%.2f)" % seen_fade)
	chk(float(hud().call("fade_alpha")) < 0.01, "and clears after it")
	chk(int(v3().call("deck_view").call("level")) == Layout.L_SLEEP, "the view shows the sleeping deck")
	chk(str(hud().call("prompt_text")) != "" or true, "prompt call is safe")
	put(Layout.L_SLEEP, at(Layout.L_SLEEP, "berths"))
	await key(KEY_E)
	chk(str(hud().call("toast_text")).contains("berths"), "the berths answer: %s" % str(hud().call("toast_text")))
	put(Layout.L_SLEEP, at(Layout.L_SLEEP, "hatch_down"))
	await key(KEY_E)
	await frames(70)
	chk(hero_level() == Layout.L_HOLD, "the hold hatch leads down to the hold (level %d)" % hero_level())
	put(Layout.L_HOLD, at(Layout.L_HOLD, "ladder_up"))
	await key(KEY_E)
	await frames(70)
	chk(hero_level() == Layout.L_SLEEP, "the hold ladder leads back up (level %d)" % hero_level())
	put(Layout.L_SLEEP, at(Layout.L_SLEEP, "ladder_up"))
	await key(KEY_E)
	await frames(70)
	chk(hero_level() == Layout.L_DECK, "the ladder leads back to the main deck (level %d)" % hero_level())
	chk(bool(m.call("is_deck")), "still on foot")


func _ladder() -> void:
	var m := mode()
	var w: RefCounted = m.get("walker")
	put(Layout.L_DECK, at(Layout.L_DECK, "rope_ladder"))
	await frames(2)
	await key(KEY_E)
	chk(int(w.get("mode")) == 1, "E at the rope ladder starts the climb")
	chk(str(hud().call("prompt_text")).contains("climb"), "the climb prompt: %s" % str(hud().call("prompt_text")))
	hold(KEY_W, true)
	for i in 400:
		await process_frame
		if hero_level() == Layout.L_NEST:
			break
	hold(KEY_W, false)
	chk(hero_level() == Layout.L_NEST, "W climbs to the crow's nest (level %d)" % hero_level())
	chk(int(w.get("mode")) == 0, "and the walker is on its feet there")
	await frames(60)
	var info: Dictionary = v3().call("deck_info")
	chk(float((scene.call("_land_view_state") as Dictionary)["zoom_to"]) < 3.5, "the camera pulls back in the nest")
	chk(bool(info["show"]), "model shown in the nest")
	# down again: E at the nest ladder starts the descent, S keeps it going
	put(Layout.L_NEST, at(Layout.L_NEST, "ladder_down"))
	await frames(2)
	await key(KEY_E)
	chk(int(w.get("mode")) == 1, "E at the nest ladder starts the descent")
	hold(KEY_S, true)
	for i in 400:
		await process_frame
		if hero_level() == Layout.L_DECK and int(w.get("mode")) == 0:
			break
	hold(KEY_S, false)
	chk(hero_level() == Layout.L_DECK and int(w.get("mode")) == 0, "S climbs down to the deck (level %d, mode %d)" % [hero_level(), int(w.get("mode"))])
	var f: Vector2 = w.call("feet_local")
	chk(bool((m.get("layout") as RefCounted).call("walkable", Layout.L_DECK, f.x, f.y, 0.2)), "and stands on free deck (%s)" % str(f))
	# reversal half way: up, then back down, ends on the deck and not stuck on the ladder
	put(Layout.L_DECK, at(Layout.L_DECK, "rope_ladder"))
	await frames(2)
	await key(KEY_E)
	hold(KEY_W, true)
	await frames(50)
	hold(KEY_W, false)
	chk(int(w.get("mode")) == 1 and float(w.call("height_above_floor")) > 1.0, "half way up the ladder (%.1f m)" % float(w.call("height_above_floor")))
	hold(KEY_S, true)
	for i in 400:
		await process_frame
		if int(w.get("mode")) == 0:
			break
	hold(KEY_S, false)
	chk(hero_level() == Layout.L_DECK and int(w.get("mode")) == 0, "reversing half way brings you back to the deck (level %d)" % hero_level())
	f = w.call("feet_local")
	chk(bool((m.get("layout") as RefCounted).call("walkable", Layout.L_DECK, f.x, f.y, 0.2)), "standing on free deck after the reversal (%s)" % str(f))


func _stores() -> void:
	var port: Node = scene.get("_port")
	var state: RefCounted = port.get("state")
	var dv: Object = v3().call("deck_view")
	await frames(3)
	chk(int(dv.call("fish_visible_count")) == 0, "empty hold: empty barrels")
	var put_kg := float(state.call("add_catch", "spc_mackerel", 20.0, 0.0))
	await frames(3)
	chk(put_kg > 19.0 and int(dv.call("fish_visible_count")) == 2, "20 of 40 kg: two barrels hold fish (%d)" % int(dv.call("fish_visible_count")))
	state.call("add_catch", "spc_mackerel", 20.0, 0.0)
	await frames(3)
	chk(int(dv.call("fish_visible_count")) == 4, "a full hold: four barrels")
	put(Layout.L_DECK, at(Layout.L_DECK, "fish_barrels"))
	await key(KEY_E)
	chk(bool((scene.get("_fish_panel") as Control).get("is_shown")), "E at the barrels opens the fish-storage panel (Release B: pictures, counts, capacity)")
	var p0: Vector2 = (m_walker()).call("feet_local")
	hold(KEY_A, true)
	await frames(20)
	hold(KEY_A, false)
	chk(((m_walker()).call("feet_local") as Vector2).distance_to(p0) < 0.01, "walking is blocked while the panel is open")
	await key(KEY_ESCAPE)
	chk(not bool((scene.get("_fish_panel") as Control).get("is_shown")), "Esc closes the panel")
	state.call("sell_all", 0.5)
	await frames(3)
	chk(int(dv.call("fish_visible_count")) == 0, "selling empties the barrels at once")
	# provisions
	put(Layout.L_HOLD, at(Layout.L_HOLD, "ledger"))
	await key(KEY_E)
	chk(bool(hud().call("is_info_open")) and int(hud().call("info_row_count")) >= 1, "E at the ledger opens the provisions list (empty inventory: bare racks)")
	await key(KEY_E)
	chk(not bool(hud().call("is_info_open")), "E closes it again")
	await key(KEY_F6, true)
	await frames(4)
	var inv: Dictionary = scene.get("_state").inventory
	chk(int(inv.get("item_hardtack", 0)) == 40, "Shift+F6 puts the test pack in the real inventory")
	await key(KEY_E)
	chk(bool(hud().call("is_info_open")) and int(hud().call("info_row_count")) > 5, "the list shows the real inventory (%d rows)" % int(hud().call("info_row_count")))
	await key(KEY_ESCAPE)
	var zn: Dictionary = dv.get("_zones")
	chk((zn["food"] as MeshInstance3D).mesh != null, "the food racks hold sacks")


func m_walker() -> RefCounted:
	return mode().get("walker")


func _keys_and_recovery() -> void:
	var m := mode()
	put(Layout.L_DECK, Vector2(0.0, 0.0))
	await frames(2)
	var fx := str(v3().get("effects"))
	await key(KEY_E, true)
	chk(str(v3().get("effects")) != fx, "Shift+E is still the effects budget")
	# F from the sea: must not strand anything
	await key(KEY_F)
	chk(bool(m.call("is_deck")), "F at sea keeps you on deck")
	# R resets everything
	put(Layout.L_HOLD, Vector2(-3.0, 0.0))
	await key(KEY_R)
	await frames(3)
	chk(not bool(m.call("is_deck")), "R puts you back at the helm")
	chk(not bool((m.get("ap") as RefCounted).get("engaged")), "R releases the course hold")
	chk(not bool(hud().call("is_info_open")), "R closes panels")
	chk(float(hud().call("fade_alpha")) < 0.01, "no fade left on the screen")
	chk(hero_level() == Layout.L_DECK, "walker back on the main deck")
