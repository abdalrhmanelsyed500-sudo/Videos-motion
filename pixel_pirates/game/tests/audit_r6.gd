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
	await _dialogue_audit()
	await _bad_map_data()
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
	var raw: int = int(scene.get("_key_raw"))
	var gm: int = int(scene.get("_key_game"))
	chk(raw > 0 and gm == raw, "every key so far reached the game: engine %d, game %d" % [raw, gm])
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


## Every person in the city, every node of the tree they speak, with the real variables and several purse/hold situations: no
## placeholder may stay unresolved ("{page1}" on screen), no option may be empty, every `next` must exist.
func _dialogue_audit() -> void:
	var state: RefCounted = port.get("state")
	var npcs: RefCounted = port.get("npcs")
	var dlg: RefCounted = port.get("dlg")
	chk((dlg.call("validate") as Array).is_empty(), "dialogue.json validates (%s)" % str(dlg.call("validate")))
	var people: Array = npcs.get("people")
	var trees_seen := {}
	var bad: Array = []
	var no_tree: Array = []
	var situations := [[5, false, 0.0], [5, false, 12.0], [200, false, 0.0], [200, true, 30.0]]
	for i in people.size():
		var spk: Dictionary = port.call("_speaker_for", i)
		var tree := str(spk["tree"])
		if not bool(dlg.call("has_tree", tree)):
			no_tree.append(str(spk["id"]))
			continue
		for sit in situations:
			state.set("reales", int(sit[0]))
			state.set("crew", [])
			state.set("lots", [])
			if bool(sit[1]):
				state.call("hire", str(state.call("cheapest_unhired")))
			if float(sit[2]) > 0.0:
				state.call("add_catch", str((state.get("fish") as Dictionary).keys()[0]), float(sit[2]), 0.0)
			if i % 9 != 0 and trees_seen.has(tree + str(spk.get("cid", ""))) and sit != situations[0]:
				continue     # one person per tree and recruit is enough for the heavy cases; the first situation is checked for everyone
			port.set("_spk", spk)
			port.set("_extra", {"track_name": "the fish market", "track_dist": "80 m west"})   # set by the "track" action before the "tracked" nodes
			var flags: Dictionary = port.call("_flags")
			var vars: Dictionary = port.call("_vars")
			var tr: Dictionary = (dlg.get("trees") as Dictionary)[tree]
			var nodes: Dictionary = tr["nodes"]
			for nid in nodes.keys():
				var v: Dictionary = dlg.call("view", tree, str(nid), flags, vars)
				for pg in v["pages"]:
					if str(pg).contains("{") or str(pg).strip_edges() == "":
						bad.append("%s/%s page '%s'" % [tree, nid, str(pg).substr(0, 40)])
				for o in v["options"]:
					var od := o as Dictionary
					if str(od["label"]).strip_edges() == "" and str(v["goto"]) == "":
						bad.append("%s/%s empty option label" % [tree, nid])
					if str(od["label"]).contains("{"):
						bad.append("%s/%s label '%s'" % [tree, nid, str(od["label"]).substr(0, 40)])
				if (v["options"] as Array).is_empty() and str(v["goto"]) == "":
					bad.append("%s/%s has no option and no goto (a dead end)" % [tree, nid])
		trees_seen[tree + str(spk.get("cid", ""))] = true
	chk(no_tree.is_empty(), "every one of the %d people has a dialogue tree (without: %s)" % [people.size(), str(no_tree.slice(0, 5))])
	var uniq := {}
	for b in bad:
		uniq[b] = true
	chk(uniq.is_empty(), "no unresolved placeholder, empty option or dead end in any node (%d: %s)" % [uniq.size(), str(uniq.keys().slice(0, 6))])
	chk(trees_seen.size() >= 12, "the audit covered %d tree/recruit combinations (>= 12)" % trees_seen.size())
	state.call("reset")


## Malformed or missing map data and invalid targets: the game must report, stay playable and never be left modal.
func _bad_map_data() -> void:
	var mp: Control = (port.get("ui") as Node).get("map")
	var good_views: Array = (mp.get("views") as Array).duplicate(true)
	# 1. an invalid tracking target is refused
	port.call("_set_track", "no_such_place_at_all")
	chk(str(port.get("_track")) == "", "tracking an unknown id is refused (track = '%s')" % str(port.get("_track")))
	chk(str(port.call("_resolve_target", "bogus_target")) == "", "an unknown dialogue target resolves to nothing")
	port.call("_on_track_requested", "pier")
	chk(str(port.get("_track")) == "pier", "tracking a real place works")
	port.call("_set_track", "")
	# 2. a view that lacks keys: reported by name, no exception, nothing left modal
	var broken: Array = good_views.duplicate(true)
	(broken[0] as Dictionary).erase("title")
	(broken[1] as Dictionary).erase("bounds")
	mp.call("set_views", broken)
	chk((mp.get("schema_errors") as Array).size() >= 2, "two missing view keys are reported (%s)" % str(mp.get("schema_errors")))
	await key(KEY_M)
	await frames(2)
	chk(bool(port.call("modal")) == bool(mp.call("is_shown")), "modal state always equals the map's real state with a broken view")
	if mp.visible:
		await key(KEY_ESCAPE)
	chk(not bool(port.call("modal")) and not mp.visible, "the broken map can be closed (Esc), the game is not left modal")
	# 3. a view whose picture is missing
	var nofile: Array = good_views.duplicate(true)
	for v in nofile:
		(v as Dictionary)["file"] = "does_not_exist.png"
	mp.call("set_views", nofile)
	await key(KEY_M)
	await frames(2)
	chk(bool(port.call("modal")) == bool(mp.call("is_shown")), "a missing map picture: modal state equals the real state")
	if mp.visible:
		await key(KEY_ESCAPE)
	chk(not bool(port.call("modal")), "...and the game is not left modal")
	# 4. an entry without coordinates
	mp.call("set_views", good_views)
	var errs: Array = mp.get_script().call("schema_problems", good_views, [{"id": "x", "kind": "place", "name": "n", "detail": "d"}])
	chk(errs.size() == 2, "an entry without x and z gives two named problems (%s)" % str(errs))
	# 5. all views empty
	mp.call("set_views", [])
	await key(KEY_M)
	chk(not bool(port.call("modal")), "no views at all: M opens nothing and leaves nothing modal")
	mp.call("set_views", good_views)
	await key(KEY_M)
	chk(mp.visible and bool(mp.call("is_shown")), "views restored: the map opens again")
	await key(KEY_ESCAPE)
