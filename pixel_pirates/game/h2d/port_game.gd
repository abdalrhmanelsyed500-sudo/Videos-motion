extends Node
## CP-1 starting loop as one controller: it owns the economy (port_state.gd), the nets (fishing.gd), the people (port_npcs.gd),
## the conversations (dialogue.gd + data/port/dialogue.json) and the interface (port_ui.gd, built from standard nodes). It reads
## what the scene tells it each frame (a context dictionary) and tells the scene back only two things: whether the nets are
## down (the ship must stop) and whether a panel is open (the world waits).
## Keys it owns: E talk / use (ashore) | F nets down / up (at sea) | M map (Shift+M stays the ship-motion toggle) |
##   in a conversation: W S / Up Down / 1-9 choose, Enter E Space confirm, Esc leave | at the fish counter: Enter / E sell all,
##   1-5 one species | on the map: Tab 1-3 view, +/- zoom, WASD pan, Up/Down pick, Enter track, C clear, Home centre |
##   F6 test +25 reales | F7 test +10 kg mackerel | F8 self-check (runs tests/test_port.gd in the game).
## Objectives, dialogue and markers come from real state: the purse, the hold, the crew, where the ship and the player are.
## NO SAVE TO DISK in this slice: the state lives until the game is closed (docs/CP1_CAPITAL_PORT.md).
const PortState := preload("res://h2d/port_state.gd")
const Fishing := preload("res://h2d/fishing.gd")
const PortNpcs := preload("res://h2d/port_npcs.gd")
const PortUi := preload("res://h2d/port_ui.gd")
const Dialogue := preload("res://h2d/dialogue.gd")
const KeyUtil := preload("res://h2d/key_util.gd")
const DataLoader := preload("res://core/data_loader.gd")
const WATERS_BOUNDS: Array = [-900.0, -420.0, 800.0, 1950.0]
const INTERACT_R := 2.8
const TALK_R := 2.4
const ARRIVE_M := 7.0
const DIRS: Array = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
const GROUP_PORTRAIT := {"fisher": "fisher", "merchant": "merchant", "docker": "docker", "sailor": "sailor", "shopkeeper": "shopkeeper",
		"townsman": "townsman", "guard": "guard", "noble": "noble", "tavernkeeper": "tavernkeeper", "clerk": "clerk"}
const GROUP_TITLE := {"fisher": "Fisher", "merchant": "Merchant", "docker": "Dock hand", "sailor": "Sailor", "shopkeeper": "Shopkeeper",
		"townsman": "Townsman", "guard": "Harbour guard", "noble": "Gentleman of the Hill", "tavernkeeper": "Tavern keeper", "clerk": "Customs clerk"}

var state: PortState = PortState.new()
var fishing: Fishing = Fishing.new()
var npcs: PortNpcs = PortNpcs.new()
var dlg: Dialogue = Dialogue.new()
var ui: PortUi
var enabled := false
var world: Object = null
var port: Dictionary = {}
var barks: Dictionary = {}
var _tuning: Dictionary = {}
var _pause_fn: Callable
var _mode := "none"                  # none | dialogue | market | map
var _spk: Dictionary = {}            # the person we are talking to
var _node := ""
var _spk_flags: Dictionary = {}      # speaker id -> {flag: true}
var _track := ""                     # the tracked target id ("" = none)
var _map_state_t := 0.0
var _market_result: Dictionary = {}
var _near := {"kind": "", "index": -1, "text": ""}
var _marker_sig := ""
var _hold_warned := false
var _last_ctx: Dictionary = {}
var _entries_cache: Array = []
var _cue_t := 0.0
var _extra: Dictionary = {}          # last dialogue variables that depend on an action (track name and distance)


## Collects the results of tests/test_port.gd and the live checks (F8).
class SelfCheck:
	extends RefCounted
	var checks := 0
	var fails: Array[String] = []

	func check(cond: bool, msg: String) -> void:
		checks += 1
		if not cond:
			fails.append(msg)


## `layer` = the CanvasLayer for the interface; `view_world` = the cay_world.gd of the 3D view; `pause_fn(on: bool)` pauses the
## game clock while a panel is open (T1: pause only in planning screens).
func setup(layer: CanvasLayer, view_world: Object, tuning: Dictionary, pause_fn: Callable) -> void:
	world = view_world
	_tuning = tuning
	_pause_fn = pause_fn
	var meta: Dictionary = (world.get("meta") as Dictionary)
	if not meta.has("port"):
		push_warning("CP-1: anvil_cay.json has no port section; run tools/h2d/bake_cay.py")
		return
	port = meta["port"]
	var fish_doc := DataLoader.load_dict("res://data/port/fish_market.json")
	var rec_doc := DataLoader.load_dict("res://data/port/recruits_port.json")
	var gr_doc := DataLoader.load_dict("res://data/port/fishing_grounds.json")
	barks = DataLoader.load_dict("res://data/port/barks.json")
	state.configure(tuning, fish_doc, rec_doc)
	fishing.configure(tuning, gr_doc, 20261019)
	npcs.setup(port["npcs"] as Array)
	dlg.load_file("res://data/port/dialogue.json")
	ui = PortUi.new()
	layer.add_child(ui)
	ui.dialogue.chosen.connect(_on_choice)
	ui.dialogue.closed.connect(_close)
	ui.dialogue.trade_action.connect(_on_trade_action)
	ui.map.closed.connect(_close)
	ui.map.track_requested.connect(_on_track_requested)
	ui.map.set_views((port["map"] as Dictionary)["views"] as Array)
	enabled = true
	_update_markers(true)
	var gl: Array = []
	for gid in fishing.ground_order:
		var gg: Dictionary = fishing.grounds[gid]
		gl.append({"id": gid, "x": gg["x"], "z": gg["z"], "r": gg["r"]})
	world.call("build_cues", gl)


func modal() -> bool:
	return _mode != "none"


# ---- per frame -------------------------------------------------------------------------------------------------------
## ctx: {ashore, wx, wz, wheading, sx, sz, sheading, speed_kn, hour, now (game days), sea (0..1), docked, sailing, grounded}
func step(dt: float, ctx: Dictionary) -> void:
	if not enabled:
		return
	_last_ctx = ctx
	var px := float(ctx["wx"]) if bool(ctx["ashore"]) else float(ctx["sx"])
	var pz := float(ctx["wz"]) if bool(ctx["ashore"]) else float(ctx["sz"])
	npcs.step(dt, world, Vector2(px, pz))
	world.call("set_npcs", npcs.people)
	_cue_t += dt
	world.call("update_cues", dt, _cue_t, Vector2(float(ctx["sx"]), float(ctx["sz"])), float(ctx["sheading"]), fishing.active, float(ctx["speed_kn"]) * 0.514)
	if fishing.active:
		if not bool(ctx["sailing"]):
			fishing.stop("moored")
		else:
			var evs := fishing.step(dt, {"x": ctx["sx"], "z": ctx["sz"], "speed_kn": ctx["speed_kn"]}, float(ctx["hour"]), float(ctx["sea"]), state, float(ctx["now"]))
			for e in evs:
				_on_fishing_event(e as Dictionary)
	_check_warnings()
	_near = _find_near(ctx)
	_update_markers(false)
	_check_arrival(ctx)
	_update_hud(ctx)
	if _mode == "map":
		_map_state_t -= dt
		if _map_state_t <= 0.0:
			_map_state_t = 0.25
			ui.map.set_state(_map_state(ctx))
	elif _mode == "market" and _market_result.is_empty():
		ui.dialogue.show_trade(_spk, _market_panel(float(ctx["now"])))


func _on_fishing_event(e: Dictionary) -> void:
	if str(e["type"]) == "haul":
		var nm := str((state.fish[str(e["species"])] as Dictionary)["name"])
		var stored := float(e["stored"])
		var lost := float(e["kg"]) - stored
		var txt := "Haul: +%.1f kg %s   (hold %.1f / %.0f kg)" % [stored, nm, state.hold_kg(), state.capacity_kg()]
		if lost > 0.05:
			txt += "   %.1f kg thrown back: hold full" % lost
		ui.toast(txt, PortUi.GREEN, 5.5)
	else:
		ui.toast(str(e["text"]), PortUi.GOLD, 7.0)


func _check_warnings() -> void:
	var near_full := state.hold_frac() >= float(_tuning.get("port.hold_warn_frac", 0.85))
	if near_full and not _hold_warned:
		_hold_warned = true
		ui.toast("The hold is nearly full: sail home soon (the catch spoils with time).", Color(1.0, 0.72, 0.25), 6.0)
	if state.hold_kg() < 0.05:
		_hold_warned = false


func _find_near(ctx: Dictionary) -> Dictionary:
	var none := {"kind": "", "index": -1, "text": ""}
	if not bool(ctx["ashore"]) or _mode != "none":
		return none
	var x := float(ctx["wx"])
	var z := float(ctx["wz"])
	var ri := npcs.nearest(x, z, INTERACT_R, true)
	if ri >= 0:
		var cid := str((npcs.people[ri] as Dictionary)["recruit"])
		var rec: Dictionary = state.recruits[cid]
		return {"kind": "talk", "index": ri, "text": "Talk to %s, %s (%d reales)" % [str(rec["name"]), str(rec["role"]), int(rec["cost"])]}
	for it in port["interactions"]:
		var d := it as Dictionary
		var dx := x - float(d["x"])
		var dz := z - float(d["z"])
		if dx * dx + dz * dz <= float(d["r"]) * float(d["r"]):
			if str(d["kind"]) == "market":
				var mi := npcs.index_of("npc_fishmonger")
				return {"kind": "talk", "index": mi, "text": "Talk to Barnaby Gull, the fishmonger (sell your catch)"}
			return {"kind": "notice", "index": -1, "text": "Read the notice board and open the map"}
	var ni := npcs.nearest(x, z, TALK_R, false)
	if ni >= 0:
		return {"kind": "talk", "index": ni, "text": "Talk to %s" % str(_speaker_for(ni)["label"])}
	return none


func _update_hud(ctx: Dictionary) -> void:
	var crew_names: Array = []
	for c in state.crew:
		var r: Dictionary = state.recruits[c]
		crew_names.append("%s (%s)" % [str(r["name"]), str(r["role"])])
	var f: Dictionary = {}
	if fishing.active:
		var g: Dictionary = fishing.grounds[fishing.ground_id]
		var st := "Nets working: fish are coming aboard."
		if fishing.status == "drifting":
			st = "The ship is slowing down. The nets work under %.1f knots (now %.1f)." % [float(fishing.p["fish.max_speed_kn"]), float(ctx["speed_kn"])]
		var lines: Array = []
		for sp in fishing.session_by.keys():
			lines.append("%s  %.1f kg" % [str((state.fish[str(sp)] as Dictionary)["name"]), float(fishing.session_by[sp])])
		var lst := "This ground so far: %.1f kg in %d haul%s" % [fishing.session_kg, fishing.hauls, "" if fishing.hauls == 1 else "s"]
		if not lines.is_empty():
			lst += "\n" + "\n".join(PackedStringArray(lines))
		f = {"ground": str(g["name"]), "status": st, "next_s": fishing.seconds_to_haul(), "interval": float(fishing.p["fish.haul_interval_s"]), "list": lst}
	var now := float(ctx["now"])
	var prompt := str(_near["text"])
	var pkey := "E"
	if prompt == "" and not bool(ctx["ashore"]) and bool(ctx["sailing"]) and _mode == "none":
		pkey = "F"
		if fishing.active:
			prompt = ""
		elif fishing.ground_at(float(ctx["sx"]), float(ctx["sz"])) != "":
			prompt = "Lower the nets"
	ui.hud.set_data({"purse": state.reales, "hold_kg": state.hold_kg(), "cap_kg": state.capacity_kg(), "fresh": state.avg_freshness(now),
			"warn_frac": float(state.p["port.hold_warn_frac"]), "spoil_warn": float(state.p["fish.spoil_warn"]), "crew": crew_names,
			"objective": objective(ctx), "fishing": f, "prompt": prompt if _mode == "none" else "", "prompt_key": pkey, "track": _track_strip(ctx)})


# ---- objective ---------------------------------------------------------------------------------------------------------
# gdlint: disable=max-returns
func objective(ctx: Dictionary) -> String:
	var unh := state.unhired()
	if unh.is_empty():
		return "Crew complete: all four hands are aboard. The prologue loop ends here; the first voyage comes in a later module."
	var cheap := state.cheapest_unhired()
	var rec: Dictionary = state.recruits[cheap]
	var now := float(ctx["now"])
	var kg := state.hold_kg()
	if fishing.active:
		var g: Dictionary = fishing.grounds[fishing.ground_id]
		return "Nets down at %s: %.1f of %.0f kg. Press F to haul in and sail home when you have enough." % [str(g["name"]), kg, state.capacity_kg()]
	if kg > 0.05:
		if bool(ctx["ashore"]) or bool(ctx["docked"]):
			return "Sell your %.0f kg of fish at the Fish Market: west along Quay Street, under the red canopy. Press E at the counter (about %d reales)." % [kg, state.estimate_all(now)]
		return "Sail home with %.0f kg of fish (about %d reales): enter the dock zone and press SPACE to moor. Fish spoils with time." % [kg, state.estimate_all(now)]
	if state.can_afford(cheap):
		return "You can afford %s, the %s (%d reales). Find him at %s. Press M for the map." % [str(rec["name"]), str(rec["role"]), int(rec["cost"]), str(rec["place"])]
	var need := state.cost_of(cheap) - state.reales
	if state.kg_total <= 0.0:
		return "You have %d reales and need a crew. Sail to the Pilchard Shallows (0.6 km south-west; chart on M) and press F to lower the nets." % state.reales
	if bool(ctx["ashore"]):
		return "Earn %d more reales for %s (%d). Board the ship (F at the pier), sail to a fishing ground and cast the nets." % [need, str(rec["name"]), int(rec["cost"])]
	return "Earn %d more reales for %s, the %s (%d). Fish a ground (M for the chart), return and sell." % [need, str(rec["name"]), str(rec["role"]), int(rec["cost"])]
# gdlint: enable=max-returns


# ---- markers ---------------------------------------------------------------------------------------------------------
func _update_markers(force: bool) -> void:
	if world == null:
		return
	var sig := ""
	for c in state.recruit_order:
		sig += "%s%d%d;" % [str(c), 1 if state.is_hired(str(c)) else 0, 1 if state.can_afford(str(c)) else 0]
	if sig == _marker_sig and not force:
		return
	_marker_sig = sig
	var list: Array = []
	for m in port["markers"]:
		var d := m as Dictionary
		list.append({"x": d["x_m"], "y": d["y_m"], "z": d["z_m"], "type": d["type"], "bob": d.get("bob", 0.16)})
	for c in state.recruit_order:
		if state.is_hired(str(c)):
			continue
		var i := npcs.index_of_recruit(str(c))
		if i < 0:
			continue
		var n := npcs.people[i] as Dictionary
		var y := float(world.call("ground_y", float(n["x"]), float(n["z"]))) + 2.45
		list.append({"x": n["x"], "y": y, "z": n["z"], "type": 1 if state.can_afford(str(c)) else 0, "bob": 0.12})
	world.call("set_markers", list)


# ---- input -----------------------------------------------------------------------------------------------------------------
## Returns true when the key was used here.
func handle_key(k: InputEventKey, ctx: Dictionary) -> bool:
	if not enabled:
		return false
	var key := KeyUtil.code(k)
	if key == KEY_F6 or key == KEY_F7:
		_test_key(key, ctx)
		return true
	if key == KEY_F8 and _mode == "none":
		_self_check()
		return true
	if _mode != "none":
		return _modal_key(key, ctx)
	var used := true
	if key == KEY_M and not k.shift_pressed:
		_open_map(0 if bool(ctx["ashore"]) else (2 if not bool(ctx["docked"]) else 0), ctx)
	elif key == KEY_E and bool(ctx["ashore"]):
		_interact(ctx)
	elif key == KEY_F and bool(ctx["sailing"]) and not bool(ctx["ashore"]):
		_toggle_nets(ctx)
	else:
		used = false
	return used


## F6 / F7: test helpers so the selling and hiring can be tried without an hour of fishing.
func _test_key(key: int, ctx: Dictionary) -> void:
	if key == KEY_F6:
		state.reales += 25
		ui.toast("TEST: +25 reales (purse %d)" % state.reales, Color(1.0, 0.6, 1.0))
	else:
		var put := state.add_catch("spc_mackerel", 10.0, float(ctx["now"]))
		ui.toast("TEST: +%.1f kg mackerel in the hold" % put, Color(1.0, 0.6, 1.0))


## F8: runs tests/test_port.gd INSIDE the running game plus checks against the live world, and reports the result on screen and
## in the Output panel. It is the same test the headless runner executes, so you need no batch file to try it.
func _self_check() -> void:
	var sc := SelfCheck.new()
	var scr := load("res://tests/test_port.gd") as GDScript
	if scr == null:
		ui.toast("SELF-CHECK: cannot load tests/test_port.gd", PortUi.RED, 8.0)
		return
	(scr.new() as Object).call("run", sc)
	var unit_checks := sc.checks
	# live checks: the real world answers the same questions the baker answered offline
	if (world.get("_hd") as PackedByteArray).is_empty():
		print("SELF-CHECK: this runtime has no ground texture (headless), so live walkability is skipped here; it runs in the real game")
	else:
		for n in port["npcs"]:
			var d := n as Dictionary
			sc.check(bool(world.call("walkable", float(d["x"]), float(d["z"]), 0.4)), "live: %s stands on walkable ground" % str(d["id"]))
		for it in port["interactions"]:
			var q := it as Dictionary
			sc.check(bool(world.call("walkable", float(q["x"]), float(q["z"]), 0.4)), "live: interaction point %s is walkable" % str(q["id"]))
	sc.check(npcs.people.size() == (port["npcs"] as Array).size(), "live: every baked person is in the walker list")
	sc.check(_grounds_in_water(), "live: the four fishing grounds are in open water (>= 100 m from land)")
	if _mode == "none" and not _last_ctx.is_empty():
		await _ui_diag(sc)
	var line := "SELF-CHECK CP-1: %d checks (%d from the unit test, %d live), %d failed" % [sc.checks, unit_checks, sc.checks - unit_checks, sc.fails.size()]
	print(line)
	for f in sc.fails:
		print("  FAIL: ", f)
	ui.toast(line + (" -> PASS" if sc.fails.is_empty() else " -> FAIL (see the Output panel)"), PortUi.GREEN if sc.fails.is_empty() else PortUi.RED, 9.0)
	for i in mini(sc.fails.size(), 3):
		ui.toast(sc.fails[i], PortUi.RED, 9.0)


## F8, part 2: the interface itself. Opens the dialogue window and the map for two frames, then measures what the player would see:
## the window size, the font, the portrait, the text, the box and map rectangles (inside the screen? non-empty?), the map picture
## and the marker count. A failure here names the exact control, which is what a "nothing appears" report needs.
func _ui_diag(sc: SelfCheck) -> void:
	var vp := ui.get_viewport().get_visible_rect().size
	sc.check(vp.x >= 300.0 and vp.y >= 200.0, "UI: the game window is %d x %d px (needs >= 300 x 200)" % [int(vp.x), int(vp.y)])
	sc.check(PortUi.K.title_font() != null, "UI: the title font loaded")
	sc.check(ui.dialogue.portrait("pip") != null and ui.dialogue.portrait("guard") != null, "UI: the portrait atlas loaded (pip, guard)")
	var view := {"pages": ["Diagnostic line: if you can read this sentence, the dialogue window shows names, portraits and text."],
			"options": [{"label": "Continue", "enabled": true}], "status": {"text": "diagnostic", "color": Color(0.2, 0.38, 0.12)}}
	ui.dialogue.show_view({"portrait": "pip", "name": "Pip Larkin", "sub": "Deckhand, 14 - asks 18 reales"}, view)
	await ui.get_tree().process_frame
	await ui.get_tree().process_frame
	ui.dialogue.finish_typing()
	await ui.get_tree().process_frame
	var box := ui.dialogue.get("_box") as Control
	var br := box.get_global_rect()
	sc.check(box.is_visible_in_tree() and br.size.x > 200.0 and br.size.y > 80.0, "UI: the dialogue box is visible and %d x %d px" % [int(br.size.x), int(br.size.y)])
	sc.check(Rect2(Vector2.ZERO, vp).encloses(br), "UI: the dialogue box lies inside the screen (%s in %s)" % [str(br), str(vp)])
	var pt := ui.dialogue.get("_portrait") as TextureRect
	sc.check(pt.texture != null and pt.get_global_rect().size.x > 40.0, "UI: the portrait is drawn (%d px wide)" % int(pt.get_global_rect().size.x))
	sc.check(str((ui.dialogue.get("_name") as Label).text) == "Pip Larkin", "UI: the speaker name label holds 'Pip Larkin'")
	sc.check(str(ui.dialogue.call("shown_text")).length() > 40, "UI: the dialogue text label holds %d characters" % str(ui.dialogue.call("shown_text")).length())
	ui.dialogue.close()
	ui.map.open(0, _map_state(_last_ctx))
	await ui.get_tree().process_frame
	await ui.get_tree().process_frame
	var mr := (ui.map.get("_panel") as Control).get_global_rect()
	sc.check(mr.size.x > 300.0 and mr.size.y > 200.0, "UI: the map panel is %d x %d px" % [int(mr.size.x), int(mr.size.y)])
	var tr := ui.map.get("_tex") as TextureRect
	sc.check(tr.texture != null and tr.get_global_rect().size.x > 100.0, "UI: the map picture is loaded and %d px wide" % int(tr.get_global_rect().size.x))
	sc.check((ui.map.get("_markers") as Dictionary).size() >= 3, "UI: the map shows %d markers on this view" % (ui.map.get("_markers") as Dictionary).size())
	ui.map.close()
	_close()


func _grounds_in_water() -> bool:
	for id in fishing.ground_order:
		var g: Dictionary = fishing.grounds[id]
		for k in 8:
			var a := TAU * float(k) / 8.0
			var r := float(g["r"]) + 100.0
			if float(world.call("height_at", float(g["x"]) + cos(a) * r, float(g["z"]) + sin(a) * r)) > 0.0:
				return false
	return true


func _modal_key(key: int, ctx: Dictionary) -> bool:
	if key == KEY_P or key == KEY_F1 or key == KEY_F2 or key == KEY_F3 or key == KEY_F4 or key == KEY_F12:
		return false
	match _mode:
		"dialogue":
			ui.dialogue.handle_key(key)
		"market":
			_market_key(key, ctx)
		"map":
			ui.map.handle_key(key)
	return true


func _close() -> void:
	if _spk.has("idx") and int(_spk["idx"]) >= 0:
		npcs.set_talking(int(_spk["idx"]), false)
	_mode = "none"
	_spk = {}
	_market_result = {}
	ui.dialogue.close()
	ui.map.close()
	_pause_fn.call(false)


func _open(kind: String) -> void:
	_mode = kind
	_pause_fn.call(true)


# ---- fishing ---------------------------------------------------------------------------------------------------------------
func _toggle_nets(ctx: Dictionary) -> void:
	if fishing.active:
		fishing.stop("player")
		ui.toast("Nets up. %.1f kg of fish in the hold." % state.hold_kg(), PortUi.CREAM)
		return
	if state.is_full():
		ui.toast("The hold is full (%.0f kg). Sail home and sell the catch first." % state.capacity_kg(), Color(1.0, 0.72, 0.25))
		return
	var r := fishing.start(float(ctx["sx"]), float(ctx["sz"]), state.crew_count(), float(ctx["sea"]))
	if bool(r["ok"]):
		var g: Dictionary = fishing.grounds[fishing.ground_id]
		ui.toast("Nets down at %s. The ship slows to a stop; a haul comes up every %d s." % [str(g["name"]), int(fishing.p["fish.haul_interval_s"])], PortUi.GOLD, 6.0)
	else:
		ui.toast(str(r["reason"]), Color(1.0, 0.72, 0.25), 6.5)


## True while the nets are down: the helm target speed is zero.
func nets_down() -> bool:
	return enabled and fishing.active


# ---- interaction -----------------------------------------------------------------------------------------------------------
func _interact(ctx: Dictionary) -> void:
	match str(_near["kind"]):
		"talk":
			_open_dialogue(int(_near["index"]), ctx)
		"notice":
			_open_map(0, ctx)
		_:
			ui.toast("Nothing to use here. Walk up to a person, a stall or the notice board.", PortUi.DIM, 3.5)


## The speaker record of person `i`: {id, idx, tree, name, sub, label, portrait, group, cid, greeting, line, wares}.
func _speaker_for(i: int) -> Dictionary:
	var n := npcs.people[i] as Dictionary
	var g := str(n["group"])
	var id := str(n["id"])
	var s := {"id": id, "idx": i, "group": g, "cid": str(n.get("recruit", ""))}
	if str(n.get("recruit", "")) != "":
		var rec: Dictionary = state.recruits[str(n["recruit"])]
		var look := str(rec.get("look", "r_pip"))
		s["tree"] = "recruit"
		s["name"] = str(rec["name"])
		s["sub"] = "%s, %d  -  asks %d reales" % [str(rec["role"]).capitalize(), int(rec["age"]), int(rec["cost"])]
		s["label"] = str(rec["name"])
		s["portrait"] = look.substr(2)
		return s
	if id == "npc_fishmonger":
		s["tree"] = "fishmonger"
		s["name"] = "Barnaby Gull"
		s["sub"] = "Fishmonger, Fish Row"
		s["label"] = "Barnaby Gull"
		s["portrait"] = "fishmonger"
		return s
	s["tree"] = g if dlg.has_tree(g) else "townsman"
	var title := str(GROUP_TITLE.get(g, "Local"))
	s["name"] = str(n.get("name", title))
	s["sub"] = str(n.get("title", title)) if n.has("name") else ""
	s["label"] = ("%s, %s" % [str(n["name"]), str(n.get("title", title))]) if n.has("name") else title
	s["portrait"] = str(n.get("portrait", GROUP_PORTRAIT.get(g, "townsman")))
	var pool: Dictionary = barks.get(g, {})
	var any: Array = pool.get("any", ["..."])
	var h := absi(id.hash())
	s["greeting"] = str(n.get("greeting", any[h % any.size()]))
	s["line"] = str(n.get("line", any[(h / 7 + 1) % any.size()]))
	s["wares"] = str(n.get("wares", "Odds and ends of the quay trade."))
	return s


func _open_dialogue(i: int, ctx: Dictionary) -> void:
	if i < 0:
		return
	_spk = _speaker_for(i)
	npcs.set_talking(i, true, float(ctx["wx"]), float(ctx["wz"]))
	_extra = {}
	_open("dialogue")
	_node = dlg.entry_node(str(_spk["tree"]), _flags())
	_show_node()


func _flags() -> Dictionary:
	var f := {"has_fish": state.hold_kg() > 0.05, "never_fished": state.kg_total <= 0.0, "poor": state.reales < 18, "crew": state.crew_count() >= 1,
			"rich": state.reales >= 100, "full_crew": state.unhired().is_empty()}
	var cid := str(_spk.get("cid", ""))
	if cid != "":
		f["afford"] = state.can_afford(cid)
		f["hired"] = state.is_hired(cid)
	var sf: Dictionary = _spk_flags.get(str(_spk.get("id", "")), {})
	for k in sf.keys():
		f[k] = true
	return f


func _vars() -> Dictionary:
	var now := float(_last_ctx.get("now", 0.0))
	var v := {"reales": state.reales, "hold_kg": "%.0f" % state.hold_kg(), "hold_value": state.estimate_all(now), "crew": state.crew_count()}
	var prices: Array = []
	for sp in state.fish.keys():
		var fd: Dictionary = state.fish[sp]
		prices.append("%s %.2f" % [str(fd["name"]).to_lower(), state.quote(str(sp), now)])
	v["price_list"] = ", ".join(PackedStringArray(prices)) + "."
	var px := float(_last_ctx.get("sx", 0.0))
	var pz := float(_last_ctx.get("sz", 0.0))
	var ng := fishing.nearest_ground(px, pz)
	v["nearest_ground"] = str((fishing.grounds[str(ng["id"])] as Dictionary)["name"]) if str(ng["id"]) != "" else "south-west of the cove"
	for sp in ["greeting", "line", "wares"]:
		if _spk.has(sp):
			v[sp] = str(_spk[sp])
	var cid := str(_spk.get("cid", ""))
	if cid != "":
		var rec: Dictionary = state.recruits[cid]
		var pages: Array = rec["pages"]
		var fmt := {"cost": int(rec["cost"]), "have": state.reales, "missing": maxi(int(rec["cost"]) - state.reales, 0)}
		v["rname"] = str(rec["name"]).replace("\"", "")
		v["cost"] = fmt["cost"]
		v["missing"] = fmt["missing"]
		v["role"] = str(rec["role"])
		for k in 3:
			v["page%d" % (k + 1)] = str(pages[mini(k, pages.size() - 1)]).format(fmt)
		for key in ["offer", "poor", "accepted", "declined"]:
			v[key] = str(rec[key]).format(fmt)
		v["backstory"] = str(rec["backstory"])
		v["effect"] = str((rec["effect"] as Dictionary)["text"])
	v["rumour"] = _rumour()
	for k in _extra.keys():
		v[k] = _extra[k]
	return v


func _rumour() -> String:
	var unh := state.unhired()
	if unh.is_empty():
		return "Quiet on the quay tonight: every hand worth hiring is already aboard your sloop, Captain. They say that is a first."
	var cid := str(state.cheapest_unhired())
	var rec: Dictionary = state.recruits[cid]
	return "They say %s, a %s, is looking for a berth: %s. He asks %d reales. And a shoal of mackerel was seen off Gannet Bank at first light." % [
			str(rec["name"]).replace("\"", ""), str(rec["role"]), str(rec["place"]), int(rec["cost"])]


func _show_node() -> void:
	var tree := str(_spk["tree"])
	var v := dlg.view(tree, _node, _flags(), _vars())
	var sf: Dictionary = _spk_flags.get(str(_spk["id"]), {})
	for fl in v["set"]:
		sf[str(fl)] = true
	_spk_flags[str(_spk["id"])] = sf
	if str(v["goto"]) != "":
		v["options"] = [{"label": "", "enabled": true, "hint": "", "action": "", "arg": "", "next": str(v["goto"]), "fail": "", "auto": true}]
	var cid := str(_spk.get("cid", ""))
	if cid != "" and _node == "hub":
		var rec: Dictionary = state.recruits[cid]
		if state.can_afford(cid):
			v["status"] = {"text": "Cost %d reales.  Your purse: %d.  %s" % [int(rec["cost"]), state.reales, str((rec["effect"] as Dictionary)["text"])], "color": Color(0.18, 0.42, 0.10)}
		else:
			v["status"] = {"text": "Cost %d reales.  Your purse: %d.  You are %d short." % [int(rec["cost"]), state.reales, int(rec["cost"]) - state.reales], "color": Color(0.70, 0.18, 0.10)}
	ui.dialogue.show_view(_spk, v)


func _on_choice(i: int) -> void:
	var v := ui.dialogue._view as Dictionary
	var o := (v["options"] as Array)[i] as Dictionary
	var act := str(o["action"])
	var next := str(o["next"])
	match act:
		"leave":
			_close()
			return
		"trade":
			_open_market(_last_ctx)
			return
		"map":
			_close()
			_open_map(0, _last_ctx)
			return
		"hire":
			var cid := str(_spk.get("cid", ""))
			if cid != "" and state.can_afford(cid):
				_hire(cid)
				next = "hired"
			else:
				return
		"track":
			var id := _resolve_target(str(o["arg"]))
			if id != "":
				_set_track(id, false)
				var e := _entry(id)
				_extra["track_name"] = str(e.get("name", id))
				_extra["track_dist"] = _dist_text(_origin_point(_last_ctx), Vector2(float(e.get("x", 0.0)), float(e.get("z", 0.0))))
			else:
				_extra["track_name"] = "That place"
				_extra["track_dist"] = "I do not know the way"
		"pay":
			var cost := int(o["arg"])
			if state.reales >= cost:
				state.reales -= cost
				ui.toast("-%d reales  (purse %d)" % [cost, state.reales], PortUi.AMBER, 4.0)
			else:
				next = str(o["fail"])
	if next == "":
		return
	_node = next
	_show_node()


func _on_trade_action(action: String, arg: String) -> void:
	if _mode != "market":
		return
	var now := float(_last_ctx.get("now", 0.0))
	match action:
		"leave":
			_close()
		"back":
			_market_result = {}
			ui.dialogue.show_trade(_spk, _market_panel(now))
		"sell_all":
			_sell(KEY_ENTER, _last_ctx)
		"sell_one":
			_sell(KEY_1 + int(arg.trim_suffix(".")) - 1, _last_ctx)


# ---- recruits --------------------------------------------------------------------------------------------------------------
func _hire(cid: String) -> void:
	var rec: Dictionary = state.recruits[cid]
	var before := state.reales
	if state.hire(cid) != "ok":
		return
	npcs.hide_recruit(cid)
	ui.note_big("%s HIRED" % str(rec["name"]).replace("\"", "").to_upper(), "-%d reales (%d -> %d).  %s" % [int(rec["cost"]), before, state.reales, str((rec["effect"] as Dictionary)["text"])], 6.5)
	ui.toast("%s, the %s, is aboard. Crew: %d of %d." % [str(rec["name"]).replace("\"", ""), str(rec["role"]), state.crew_count(), state.recruit_order.size()], PortUi.GREEN, 6.0)
	if _track == "recruit_" + cid:
		_track = ""
	_update_markers(true)


# ---- the market --------------------------------------------------------------------------------------------------------------
func _open_market(ctx: Dictionary) -> void:
	_market_result = {}
	_mode = "market"
	if not _spk.has("id") or str(_spk["id"]) != "npc_fishmonger":
		var mi := npcs.index_of("npc_fishmonger")
		_spk = _speaker_for(mi)
		npcs.set_talking(mi, true, float(ctx["wx"]), float(ctx["wz"]))
	ui.dialogue.show_trade(_spk, _market_panel(float(ctx["now"])))


func _market_panel(now: float) -> Dictionary:
	var rows: Array = []
	var sp_list := state.species_in_hold()
	for k in sp_list.size():
		var sp := str(sp_list[k])
		var kg := state.kg_of(sp)
		var fr := 0.0
		for lot in state.lots:
			var l := lot as Array
			if str(l[0]) == sp:
				fr += float(l[1]) * state.freshness_of(float(l[2]), now)
		rows.append({"key": str(k + 1), "name": str((state.fish[sp] as Dictionary)["name"]), "kg": kg, "fresh": fr / maxf(kg, 0.001),
				"price": state.quote(sp, now), "est": state.estimate_species(sp, now), "level": state.price_level(sp, now)})
	var board: Array = []
	for sp in state.fish.keys():
		board.append({"name": str((state.fish[sp] as Dictionary)["name"]), "price": state.quote(str(sp), now), "level": state.price_level(str(sp), now)})
	var keys := "Enter / E: sell everything"
	if rows.size() > 1:
		keys += "     1-%d: sell one species" % rows.size()
	keys += "     Esc: leave"
	if rows.is_empty():
		keys = "Esc: leave"
	return {"rows": rows, "board": board, "total": state.estimate_all(now), "purse": state.reales, "keys": keys, "result": {},
			"line": str((barks["fishmonger"] as Dictionary)["greet"])}


func _market_key(key: int, ctx: Dictionary) -> void:
	var now := float(ctx["now"])
	if key == KEY_ESCAPE:
		_close()
		return
	var go := KeyUtil.is_confirm(key)
	if not _market_result.is_empty():
		if go:
			_market_result = {}
			ui.dialogue.show_trade(_spk, _market_panel(now))
		return
	_sell(key, ctx)


func _sell(key: int, ctx: Dictionary) -> void:
	var now := float(ctx["now"])
	var sp_list := state.species_in_hold()
	if sp_list.is_empty():
		return
	var go := KeyUtil.is_confirm(key)
	var before := state.reales
	var rows: Array = []
	var total := 0
	var kg := 0.0
	if go:
		var r := state.sell_all(now)
		for q in r["rows"]:
			var d := q as Dictionary
			rows.append({"name": str((state.fish[str(d["species"])] as Dictionary)["name"]), "kg": d["kg"], "fresh": d["fresh"], "level": d["level"], "reales": d["reales"],
					"level_after": state.price_level(str(d["species"]), now)})
		total = int(r["reales"])
		kg = float(r["kg"])
	elif KeyUtil.digit(key) >= 0 and KeyUtil.digit(key) < sp_list.size():
		var sp := str(sp_list[KeyUtil.digit(key)])
		var level := state.price_level(sp, now)
		var r2 := state.sell_species(sp, now)
		rows.append({"name": str((state.fish[sp] as Dictionary)["name"]), "kg": r2["kg"], "fresh": r2["fresh"], "level": level, "reales": r2["reales"],
				"level_after": state.price_level(sp, now)})
		total = int(r2["reales"])
		kg = float(r2["kg"])
	else:
		return
	var flooded := false
	for rr in rows:
		if float((rr as Dictionary)["level_after"]) < 0.7:
			flooded = true
	var line := str((barks["fishmonger"] as Dictionary)["flooded" if flooded else "sold"])
	_market_result = {"rows": rows, "reales": total, "purse_before": before, "purse_after": state.reales, "line": "Barnaby: " + line}
	var d2 := _market_panel(now)
	d2["result"] = _market_result
	d2["keys"] = "Enter / E: back to the counter     Esc: leave"
	ui.dialogue.show_trade(_spk, d2)
	ui.note_big("+%d reales" % total, "%.1f kg of fish sold.  Purse %d -> %d reales." % [kg, before, state.reales], 5.5)
	ui.toast("Sold %.1f kg for %d reales. Purse: %d." % [kg, total, state.reales], PortUi.GOLD, 6.0)
	_update_markers(false)


# ---- the map and tracking ----------------------------------------------------------------------------------------------------
func _open_map(tab: int, ctx: Dictionary) -> void:
	_open("map")
	_map_state_t = 0.25
	ui.map.open(tab, _map_state(ctx))


func _origin_point(ctx: Dictionary) -> Vector2:
	if bool(ctx.get("ashore", true)):
		return Vector2(float(ctx["wx"]), float(ctx["wz"]))
	return Vector2(float(ctx["sx"]), float(ctx["sz"]))


static func dir_name(from: Vector2, to: Vector2) -> String:
	var ang := fposmod(rad_to_deg(atan2(to.x - from.x, -(to.y - from.y))), 360.0)
	return DIRS[int(roundf(ang / 45.0)) % 8]


static func _dist_text(from: Vector2, to: Vector2) -> String:
	var d := from.distance_to(to)
	if d < 1.0:
		return "right here"
	if d >= 1500.0:
		return "%.1f km %s" % [d / 1000.0, dir_name(from, to)]
	return "%d m %s" % [int(roundf(d)), dir_name(from, to)]


## Every place the map and the tracker know: [{id, kind, name, detail, x, z, rank, views, color?, row?}]
func _entries(ctx: Dictionary) -> Array:
	var org := _origin_point(ctx)
	var out: Array = []
	out.append({"id": "player", "kind": "player", "name": "You", "detail": "", "x": float(ctx["wx"]), "z": float(ctx["wz"]), "rank": 3, "views": ["city", "island"], "row": 0})
	var berth: Dictionary = (world.get("meta") as Dictionary)["harbor_layout"]["berth"]
	var sx := float(ctx["sx"])
	var sz := float(ctx["sz"])
	out.append({"id": "ship", "kind": "ship", "name": "Your sloop", "detail": "at the pier" if bool(ctx["docked"]) else _dist_text(org, Vector2(sx, sz)),
			"x": sx if not bool(ctx["docked"]) else float(berth["x"]), "z": sz if not bool(ctx["docked"]) else float(berth["z"]), "rank": 3, "views": ["city", "island", "sea"]})
	for pl in port.get("places", []):
		var d := (pl as Dictionary).duplicate()
		d["detail"] = "%s  -  %s" % [str(d.get("what", "")), _dist_text(org, Vector2(float(d["x"]), float(d["z"])))]
		if not d.has("views"):
			d["views"] = ["city", "island"]
		out.append(d)
	for c in state.recruit_order:
		var cid := str(c)
		var r: Dictionary = state.recruits[cid]
		var spot: Dictionary = (port["recruit_spots"] as Dictionary)[cid]
		var hired := state.is_hired(cid)
		var afford := state.can_afford(cid)
		var detail := ""
		var col := Color(0.98, 0.80, 0.25)
		if hired:
			detail = "%s  -  aboard your ship" % str(r["role"])
			col = Color(0.5, 0.5, 0.5)
		else:
			detail = "%s  -  %d reales%s  -  %s" % [str(r["role"]), int(r["cost"]), "" if afford else " (short %d)" % (int(r["cost"]) - state.reales), _dist_text(org, Vector2(float(spot["x"]), float(spot["z"])))]
			col = Color(0.55, 0.92, 0.38) if afford else Color(0.98, 0.72, 0.25)
		out.append({"id": "recruit_" + cid, "kind": "recruit", "name": str(r["name"]).replace("\"", ""), "detail": detail, "x": float(spot["x"]), "z": float(spot["z"]),
				"rank": 2, "views": ["city", "island"], "color": col})
	for gid in fishing.ground_order:
		var g: Dictionary = fishing.grounds[gid]
		var open := int(g["min_crew"]) <= state.crew_count()
		var dist := maxf(org.distance_to(Vector2(float(g["x"]), float(g["z"]))) - float(g["r"]), 0.0)
		var line := "you are inside" if dist <= 0.0 else _dist_text(org, Vector2(float(g["x"]), float(g["z"])))
		out.append({"id": "ground_" + str(gid).substr(4), "kind": "ground", "name": str(g["name"]), "detail": "fishing ground  -  %s%s" % [line, "" if open else "  (needs %d hand)" % int(g["min_crew"])],
				"x": float(g["x"]), "z": float(g["z"]), "rank": 2, "views": ["sea", "island"], "color": Color(0.5, 0.85, 1.0) if open else Color(0.7, 0.6, 0.5), "letter": "~"})
	_entries_cache = out
	return out


func _entry(id: String) -> Dictionary:
	if id == "":
		return {}
	var list := _entries_cache if not _entries_cache.is_empty() else _entries(_last_ctx)
	for e in list:
		if str((e as Dictionary)["id"]) == id:
			return e as Dictionary
	return {}


func _map_state(ctx: Dictionary) -> Dictionary:
	var rings: Array = []
	for gid in fishing.ground_order:
		var g: Dictionary = fishing.grounds[gid]
		rings.append({"x": g["x"], "z": g["z"], "r": g["r"], "open": int(g["min_crew"]) <= state.crew_count(), "views": ["sea", "island"]})
	return {"entries": _entries(ctx), "tracked": _track, "player": Vector2(float(ctx["wx"]), float(ctx["wz"])), "player_heading": 0.0,
			"ship": Vector2(float(ctx["sx"]), float(ctx["sz"])), "ship_heading": deg_to_rad(float(ctx.get("sheading", 0.0))), "ashore": bool(ctx["ashore"]), "rings": rings}


func _resolve_target(arg: String) -> String:
	if arg == "recruit_cheapest":
		var c := state.cheapest_unhired()
		return "recruit_" + str(c) if str(c) != "" else ""
	if arg == "ground_nearest":
		var org := _origin_point(_last_ctx)
		var n := fishing.nearest_ground(org.x, org.y, state.crew_count())
		return "ground_" + str(n["id"]).substr(4) if str(n["id"]) != "" else ""
	var e := _entry(arg)
	return arg if not e.is_empty() else ""


func _set_track(id: String, announce: bool = true) -> void:
	_track = id
	if id == "":
		if announce:
			ui.toast("Tracking cleared.", PortUi.DIM, 2.5)
		return
	var e := _entry(id)
	if announce and not e.is_empty():
		ui.toast("Tracking: %s (%s). Follow the gold arrow at the top of the screen." % [str(e["name"]), _dist_text(_origin_point(_last_ctx), Vector2(float(e["x"]), float(e["z"])))], PortUi.GOLD, 5.0)


func _on_track_requested(id: String) -> void:
	if id == "" or id == _track:
		_set_track("")
	else:
		_set_track(id)
	if _mode == "map":
		ui.map.set_state(_map_state(_last_ctx))


func _track_strip(ctx: Dictionary) -> Dictionary:
	if _track == "":
		return {}
	var e := _entry(_track)
	if e.is_empty():
		return {}
	var org := _origin_point(ctx)
	var to := Vector2(float(e["x"]), float(e["z"]))
	return {"name": "Tracking: %s" % str(e["name"]), "text": _dist_text(org, to), "angle": atan2(to.x - org.x, -(to.y - org.y))}


func _check_arrival(ctx: Dictionary) -> void:
	if _track == "" or _mode != "none":
		return
	var e := _entry(_track)
	if e.is_empty():
		return
	var org := _origin_point(ctx)
	var to := Vector2(float(e["x"]), float(e["z"]))
	var arrived := false
	if str(e["kind"]) == "ground":
		var gid := "gnd_" + _track.substr(7)
		arrived = fishing.ground_at(float(ctx["sx"]), float(ctx["sz"])) == gid
	else:
		arrived = org.distance_to(to) <= ARRIVE_M and (bool(ctx["ashore"]) or bool(ctx["docked"]))
	if arrived:
		ui.toast("You have arrived: %s." % str(e["name"]), PortUi.GREEN, 4.0)
		_track = ""


