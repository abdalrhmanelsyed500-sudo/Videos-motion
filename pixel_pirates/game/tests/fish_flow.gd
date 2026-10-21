# gdlint: disable=max-line-length
extends SceneTree
## CP-2 Release B inside the REAL game scene (res://h2d/h2d0.tscn), with real key events:
##   godot --headless --fixed-fps 60 --path game --script res://tests/fish_flow.gd        (prints FISHFLOW n checks, m failed)
## Proves the whole interaction: F at the winch enters the first-person view (refused with a reason elsewhere: no ground, full hold);
## while it is up no other key (M, digits, W, Tab) reaches the ship; the cast needle, the sink, the A/D haul, the raise, the catch card and
## the unload run in order; the catch lands in the REAL hold (lots, kg) at the unload; the 3D world is switched off for the view and
## comes back every time it ends (finish, Esc at every stage, a reset, losing the ground, a rough sea); walking works again afterwards;
## E at the barrels opens the storage panel with one row per species, the right totals and capacity, and it follows a sale.
## No pixels are checked here (tools/godot_browser/scenarios/fish_winch.mjs does that in a real renderer).
const Layout := preload("res://h2d/ship_layout.gd")
const Manual := preload("res://h2d/fish_manual.gd")
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


func mode() -> RefCounted:
	return scene.get("_ship_mode")


func hud() -> Control:
	return scene.get("_ship_hud")


func fs() -> Node:
	return scene.get("_fish")


func man() -> Manual:
	return fs().get("manual")


func port() -> Node:
	return scene.get("_port")


func ps() -> RefCounted:
	return port().get("state")


func world_on() -> bool:
	return bool((scene.get("_v3").get("_layer") as CanvasLayer).visible)


func put_winch() -> void:
	var it: Dictionary = (mode().get("layout") as RefCounted).call("interaction", Layout.L_DECK, "winch")
	mode().get("walker").call("place", Layout.L_DECK, it["c"])


func put_at(id: String) -> void:
	var it: Dictionary = (mode().get("layout") as RefCounted).call("interaction", Layout.L_DECK, id)
	mode().get("walker").call("place", Layout.L_DECK, it["c"])


func ground(id: String) -> Vector2:
	var g: Dictionary = (port().get("fishing").get("grounds") as Dictionary)[id]
	return Vector2(float(g["x"]), float(g["z"]))


func slow() -> void:
	scene.get("_helm").set("speed_kn", 0.4)


func on_ground(id: String = "gnd_pilchard_shallows") -> void:
	scene.set("_pos", ground(id))
	slow()


func _initialize() -> void:
	scene = (load("res://h2d/h2d0.tscn") as PackedScene).instantiate()
	root.add_child(scene)
	_play()


func _play() -> void:
	await frames(10)
	if mode() == null or fs() == null:
		chk(false, "the game scene has the winch session")
		quit(1)
		return
	await _no_auto_fish()
	await _enter_and_refuse()
	await _full_haul()
	await _barrels_panel()
	await _cancel_everywhere()
	await _interruptions()
	print("FISHFLOW %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)


## CP-2B.1: the old automatic catch is gone. Sitting on a ground, pressing F at the helm (several times, at different moments) and
## waiting for minutes of game time must never put one gram in the hold, start a net, or open the winch view.
func _no_auto_fish() -> void:
	on_ground()
	await frames(10)
	chk(not bool(mode().call("is_deck")), "set-up: the pirate is still at the helm")
	chk(float(ps().call("hold_kg")) == 0.0 and (ps().get("lots") as Array).is_empty(), "set-up: the hold is empty")
	var fishing: RefCounted = port().get("fishing")
	chk(str(fishing.call("ground_at", scene.get("_pos").x, scene.get("_pos").y)) == "gnd_pilchard_shallows", "set-up: the ship is inside the Pilchard Shallows")
	var phud: Control = port().get("ui").get("hud")
	await frames(60 * 20)                    # 20 s on the ground, no key at all
	on_ground()
	chk(float(ps().call("hold_kg")) == 0.0, "20 s waiting on a fishing ground bring no fish (hold %.2f kg)" % float(ps().call("hold_kg")))
	chk(not bool(fishing.get("active")), "waiting does not start a net")
	for i in 3:
		var t0 := int(phud.get("shown_toasts"))
		await key(KEY_F)
		chk(int(phud.get("shown_toasts")) > t0, "F at the helm explains where the winch is (a message, no catch)")
		chk(not bool(fishing.get("active")), "F at the helm on a ground does not start a net (press %d)" % (i + 1))
		chk(not bool(fs().get("active")), "F at the helm does not open the winch view")
		chk(world_on(), "F at the helm leaves the 3D world on")
		await frames(60 * 6)
		on_ground()
	chk(float(ps().call("hold_kg")) == 0.0 and (ps().get("lots") as Array).is_empty(), "F at the helm plus 18 s more: still no fish (hold %.2f kg)" % float(ps().call("hold_kg")))
	chk(not bool(fishing.get("active")) and str(fishing.get("status")) == "idle", "the legacy net never became active (status %s)" % str(fishing.get("status")))
	var prompt_on: bool = bool((phud.get("_prompt") as Control).visible)
	var prompt := str((phud.get("_prompt_lbl") as Label).text) if prompt_on else ""
	chk(not prompt.to_lower().contains("lower the nets"), "no 'Lower the nets' prompt is offered (%s)" % prompt)
	# a rough sea and a slow ship change nothing either
	slow()
	await frames(60 * 5)
	chk(float(ps().call("hold_kg")) == 0.0, "still nothing after more waiting")


func _enter_and_refuse() -> void:
	await key(KEY_E)                       # leave the helm
	chk(bool(mode().call("is_deck")), "E leaves the helm")
	put_winch()
	await frames(3)
	chk(str(hud().call("prompt_text")).contains("F  Work the fishing winch") or str(hud().call("prompt_text")).contains("Work the fishing winch"), "prompt at the winch: %s" % str(hud().call("prompt_text")))
	chk(bool(mode().call("winch_ready")), "the pirate is at the winch")
	scene.set("_pos", Vector2(-100.0, 140.0))        # the harbour mouth: no fishing ground here
	await key(KEY_F)
	chk(not bool(fs().get("active")), "F outside a fishing ground does not enter the view")
	chk(str(hud().call("toast_text")).contains("No fish here"), "and says why: %s" % str(hud().call("toast_text")))
	chk(world_on(), "the world keeps rendering")
	# a full hold
	on_ground()
	var held := float(ps().call("hold_kg"))
	ps().call("add_catch", "spc_mackerel", 100.0, 0.0)
	await key(KEY_F)
	chk(not bool(fs().get("active")), "F with a full hold does not enter the view")
	chk(str(hud().call("toast_text")).contains("hold is full"), "and says why: %s" % str(hud().call("toast_text")))
	ps().set("lots", [])
	chk(held == 0.0 and float(ps().call("hold_kg")) == 0.0, "the test hold is empty again")


func _wait_stage(stage: int, max_frames: int) -> bool:
	for i in max_frames:
		if man().stage == stage:
			return true
		await process_frame
	return man().stage == stage


func _cast_now() -> void:
	for i in 400:
		if absf(man().aim - 0.5) < 0.02 or man().stage != Manual.Stage.AIM:
			break
		await process_frame
	await key(KEY_SPACE)


func _full_haul() -> void:
	on_ground("gnd_gannet_bank")
	put_winch()
	await frames(2)
	var pos0: Vector2 = scene.get("_pos")
	await key(KEY_F)
	chk(bool(fs().get("active")), "F at the winch on a ground enters the first-person view")
	chk(bool(fs().get("view").get("visible")), "the view is visible")
	chk(not world_on(), "the 3D world is switched off while the view is up")
	chk(bool(scene.call("_ship_ui_blocked")), "walking and steering are blocked")
	await frames(3)
	chk(man().stage == Manual.Stage.AIM, "the ship is slow enough: the needle starts (%s)" % man().stage_name())
	# nothing else may react to keys now
	await key(KEY_M)
	chk(not bool(scene.call("_map_is_open")), "M does not open the chart behind the view")
	chk(not bool((scene.get("_map") as Node).call("request_open", -1)), "the chart refuses to open while the winch view is up")
	await key(KEY_3)
	await key(KEY_TAB)
	await key(KEY_W)
	chk((scene.get("_pos") as Vector2).distance_to(pos0) < 3.0, "digits and other keys do not move the ship (%.1f m)" % (scene.get("_pos") as Vector2).distance_to(pos0))
	chk(man().stage == Manual.Stage.AIM and bool(fs().get("active")), "still at the winch after stray keys")
	# stage 1: cast with the needle
	await _cast_now()
	chk(man().stage == Manual.Stage.SINK, "Space casts the net (%s)" % man().stage_name())
	chk(man().cast_q >= 1.0, "a centred needle is a good cast (%.2f, %s)" % [man().cast_q, man().cast_grade])
	chk(await _wait_stage(Manual.Stage.SOAK, 300), "the net sinks")
	chk(await _wait_stage(Manual.Stage.HAUL, 300), "the shoal gathers, then the haul starts")
	# stage 2: haul, alternating A and D, easing off during a run
	var t := 0.0
	var side := true
	var n := 0
	while man().stage == Manual.Stage.HAUL and t < 40.0:
		if man().surge_phase == 2:
			await frames(6)
			t += 0.1
			continue
		await key(KEY_A if side else KEY_D)
		side = not side
		n += 1
		await frames(21)
		t += 0.42
	chk(man().stage == Manual.Stage.RAISE or man().stage == Manual.Stage.SUMMARY, "the haul is won with A and D (%s after %d pulls, %.1f s)" % [man().stage_name(), n, man().haul_t])
	chk(man().haul_t > 6.5 and man().haul_t < 14.0, "the haul takes about 8 to 12 s (%.1f)" % man().haul_t)
	var kg0 := float(ps().call("hold_kg"))
	chk(kg0 == 0.0, "nothing is in the hold before the unload (%.2f)" % kg0)
	chk(await _wait_stage(Manual.Stage.SUMMARY, 400), "the net is raised and the catch card shows")
	var res: Dictionary = man().result
	chk(not bool(res.get("failed", true)) and int(res["count"]) > 0 and float(res["kg"]) > 0.5, "the catch has real fish: %d, %.1f kg" % [int(res["count"]), float(res["kg"])])
	chk(float(ps().call("hold_kg")) == 0.0, "still nothing stored on the card")
	# stage 3: unload
	await key(KEY_E)
	chk(man().stage == Manual.Stage.UNLOAD, "E on the card unloads (%s)" % man().stage_name())
	await frames(2)
	var kg1 := float(ps().call("hold_kg"))
	chk(absf(kg1 - float(res["kg"])) < 0.2, "the catch is in the real hold at once (%.2f of %.2f kg)" % [kg1, float(res["kg"])])
	var by_species := 0
	for lot in (ps().get("lots") as Array):
		by_species += 1
	chk(by_species >= 1, "the hold has lots for what was caught")
	var shown := fs().get("view").get("env") as Dictionary
	chk(absf(float(shown["hold_kg"]) - kg1) < 0.2, "the view's hold line follows the real hold")
	for i in 400:
		if not bool(fs().get("active")):
			break
		await process_frame
	chk(not bool(fs().get("active")), "the unload ends the session")
	chk(not bool(fs().get("view").get("visible")), "the view is hidden again")
	chk(world_on(), "the 3D world is back")
	chk(not bool(scene.call("_ship_ui_blocked")), "walking works again")
	chk(str(hud().call("toast_text")).contains("Stored"), "the report says what was stored: %s" % str(hud().call("toast_text")))
	chk(not bool(port().get("fishing").get("active")), "the nets are up (the ship is free to sail)")
	# exactly once: the hold equals the catch card, and waiting on the ground afterwards adds nothing (no legacy system on top)
	var lot_sum := 0.0
	for lot in (ps().get("lots") as Array):
		lot_sum += float((lot as Array)[1])
	chk(absf(lot_sum - float(ps().call("hold_kg"))) < 0.005, "the lots add up to the hold (%.2f)" % lot_sum)
	chk(absf(float(ps().call("hold_kg")) - float(res["kg"])) < 0.2, "the hold holds the catch ONCE (hold %.2f, card %.2f kg)" % [float(ps().call("hold_kg")), float(res["kg"])])
	var kept := float(ps().call("hold_kg"))
	var lots_n := (ps().get("lots") as Array).size()
	on_ground("gnd_gannet_bank")
	await frames(60 * 15)
	on_ground("gnd_gannet_bank")
	await key(KEY_F)                 # the pirate stands at the winch: this opens a NEW session, which we leave at once
	await key(KEY_ESCAPE)
	await frames(30)
	chk(absf(float(ps().call("hold_kg")) - kept) < 0.0001 and (ps().get("lots") as Array).size() == lots_n, "15 s later and after opening and closing the winch the hold is unchanged (%.2f kg, %d lots)" % [float(ps().call("hold_kg")), (ps().get("lots") as Array).size()])


func _barrels_panel() -> void:
	put_at("fish_barrels")
	await frames(2)
	await key(KEY_E)
	var panel: Control = scene.get("_fish_panel")
	chk(bool(panel.get("is_shown")), "E at the barrels opens the fish-storage panel")
	var m: Dictionary = panel.get("model")
	var rows: Array = m["rows"]
	chk(rows.size() >= 1 and not bool(m["empty"]), "one row per species in the hold (%d)" % rows.size())
	var kg := 0.0
	var n := 0
	for r in rows:
		kg += float((r as Dictionary)["kg"])
		n += int((r as Dictionary)["count"])
		chk(str((r as Dictionary)["icon"]) != "" and int((r as Dictionary)["count"]) >= 1, "row %s has an icon id and a count" % str((r as Dictionary)["name"]))
	chk(absf(kg - float(ps().call("hold_kg"))) < 0.01 and absf(float(m["total_kg"]) - kg) < 0.01, "total kg equals the real hold (%.2f)" % kg)
	chk(int(m["total_n"]) == n and n >= 1, "total quantity is the sum of the rows (%d)" % n)
	chk(absf(float(m["capacity"]) - float(ps().call("capacity_kg"))) < 0.01 and absf(float(m["remaining"]) - (float(m["capacity"]) - kg)) < 0.01, "capacity and the space left are right")
	var dv: Dictionary = scene.call("_deck_view_state")
	chk(bool(dv.get("on", false)) and absf(float(dv["fish_frac"]) - float(ps().call("hold_frac"))) < 0.001 and float(dv["fish_frac"]) > 0.0, "the barrels on deck are filled to the real hold fraction (%.2f)" % float(dv.get("fish_frac", -1.0)))
	# a sale empties the barrels: the open panel follows
	var purse0 := int(ps().get("reales"))
	var worth := int(ps().call("estimate_all", float(scene.get("_state").get("clock").get("t")) / 86400.0))
	var sale: Dictionary = ps().call("sell_all", float(scene.get("_state").get("clock").get("t")) / 86400.0)
	chk(int(sale["reales"]) > 0 and int(ps().get("reales")) == purse0 + int(sale["reales"]), "SELLING still works: the market paid %d reales (estimate %d)" % [int(sale["reales"]), worth])
	chk(float(ps().call("hold_kg")) == 0.0 and (ps().get("lots") as Array).is_empty(), "the sale emptied the hold")
	var again: Dictionary = ps().call("sell_all", float(scene.get("_state").get("clock").get("t")) / 86400.0)
	chk(int(again["reales"]) == 0 and int(ps().get("reales")) == purse0 + int(sale["reales"]), "selling twice pays once")
	await frames(3)
	chk(float((scene.call("_deck_view_state") as Dictionary)["fish_frac"]) == 0.0, "and the barrels on deck are empty")
	chk(bool((panel.get("model") as Dictionary)["empty"]) and ((panel.get("model") as Dictionary)["rows"] as Array).is_empty(), "after a sale the panel lists nothing (no zero rows)")
	await key(KEY_ESCAPE)
	chk(not bool(panel.get("is_shown")), "Esc closes the panel")
	await key(KEY_E)
	chk(bool(panel.get("is_shown")), "E opens it again")
	await key(KEY_E)
	chk(not bool(panel.get("is_shown")), "E closes it")


func _cancel_everywhere() -> void:
	put_winch()
	# Esc while the needle runs: nothing was lost, nothing stored
	on_ground()
	await key(KEY_F)
	chk(bool(fs().get("active")), "enter again")
	await frames(3)
	await key(KEY_ESCAPE)
	chk(not bool(fs().get("active")) and world_on(), "Esc at the needle leaves cleanly and the world is back")
	chk(str(hud().call("toast_text")).contains("let go") or str(hud().call("toast_text")) != "", "with a message")
	# Esc while the net is down: it comes back empty
	on_ground("gnd_kelp_reef")
	await key(KEY_F)
	await frames(3)
	await _cast_now()
	chk(await _wait_stage(Manual.Stage.SOAK, 300), "cast again, the net is down")
	await key(KEY_ESCAPE)
	chk(man().stage == Manual.Stage.CANCEL, "Esc with the net down hauls it back (%s)" % man().stage_name())
	for i in 300:
		if not bool(fs().get("active")):
			break
		await process_frame
	chk(not bool(fs().get("active")) and world_on(), "the session ended by itself after the net came back")
	chk(float(ps().call("hold_kg")) == 0.0, "an abandoned haul stores nothing")
	# a hand that does nothing: the haul fails with an explanation, E returns to the deck
	on_ground()
	await key(KEY_F)
	await frames(3)
	await _cast_now()
	chk(await _wait_stage(Manual.Stage.HAUL, 600), "idle player reaches the haul")
	chk(await _wait_stage(Manual.Stage.FAIL, 3600), "doing nothing loses the haul")
	chk(str(man().fail_text).length() > 30, "the failure is explained: %s" % str(man().fail_text).left(70))
	await key(KEY_E)
	chk(not bool(fs().get("active")) and world_on(), "E leaves the failure card cleanly")
	chk(float(ps().call("hold_kg")) == 0.0, "a lost haul stores nothing")


func _interruptions() -> void:
	put_winch()
	on_ground()
	await key(KEY_F)
	await frames(3)
	chk(bool(fs().get("active")), "enter for the interruption tests")
	scene.set("_pos", Vector2(-100.0, 140.0))          # the ship drifts off the ground
	await frames(5)
	chk(not bool(fs().get("active")) and world_on() and not bool(scene.call("_ship_ui_blocked")), "losing the fishing ground ends the view and restores the world")
	chk(str(hud().call("toast_text")).contains("ground"), "and says why: %s" % str(hud().call("toast_text")))
	on_ground()
	await key(KEY_F)
	await frames(3)
	scene.call("_reset_ship")
	await frames(3)
	chk(not bool(fs().get("active")) and world_on(), "a ship reset during the view ends it and restores the world")
	chk(not bool(port().get("fishing").get("active")), "and the nets are up")
	# the sea turns rough: the passive rules stop the nets and the view ends
	await key(KEY_E)
	put_winch()
	on_ground()
	await key(KEY_F)
	await frames(3)
	chk(bool(fs().get("active")), "enter once more")
	(port().get("fishing") as RefCounted).call("stop", "rough")
	await frames(3)
	chk(not bool(fs().get("active")) and world_on(), "the nets stopping from outside ends the view")
	await key(KEY_F)                       # the pirate still stands at the winch: the view opens again after an interruption
	await frames(3)
	chk(bool(fs().get("active")), "the winch can be used again after the interruptions")
	await key(KEY_ESCAPE)
	chk(not bool(fs().get("active")) and world_on(), "final state: no view, world on")
