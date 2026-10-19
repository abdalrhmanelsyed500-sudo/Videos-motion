extends Node
## CP-1 "Fish Row" starting loop, as one controller: it owns the economy (port_state.gd), the nets (fishing.gd), the people
## (port_npcs.gd) and the interface (port_ui.gd), reads what the scene tells it each frame (a context dictionary) and tells
## the scene back only two things: whether the nets are down (the ship must stop) and whether a panel is open (the world waits).
## Keys it owns: E interact (ashore) | F nets down / up (at sea) | M map (Shift+M stays the ship-motion toggle) |
##   Y / N answer a recruit | Enter / Space / E continue or sell all | 1-5 sell one species | Tab switches the map |
##   Esc closes | F6 test +25 reales | F7 test +10 kg mackerel.
## Objectives and dialogue come from real state: the purse, the hold, the crew, where the ship is.
## NO SAVE TO DISK in this slice: the state lives until the game is closed (docs/CP1_CAPITAL_PORT.md). NOT YET RUN IN GODOT.
const PortState := preload("res://h2d/port_state.gd")
const Fishing := preload("res://h2d/fishing.gd")
const PortNpcs := preload("res://h2d/port_npcs.gd")
const PortUi := preload("res://h2d/port_ui.gd")
const DataLoader := preload("res://core/data_loader.gd")
const WATERS_BOUNDS: Array = [-900.0, -420.0, 800.0, 1950.0]
const INTERACT_R := 2.8
const TALK_R := 2.4

var state: PortState = PortState.new()
var fishing: Fishing = Fishing.new()
var npcs: PortNpcs = PortNpcs.new()
var ui: PortUi
var enabled := false
var world: Object = null
var port: Dictionary = {}
var barks: Dictionary = {}
var _tuning: Dictionary = {}
var _pause_fn: Callable
var _mode := "none"                  # none | dialogue | market | map
var _dlg: Dictionary = {}
var _met: Dictionary = {}            # crew id -> true once his pages were read
var _map_tab := 0
var _market_result: Dictionary = {}
var _near := {"kind": "", "index": -1, "text": ""}
var _marker_sig := ""
var _bark_n := 0
var _hold_warned := false
var _last_ctx: Dictionary = {}
var _fishing_hint := true


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
	ui = PortUi.new()
	layer.add_child(ui)
	enabled = true
	_update_markers(true)


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
	# the nets
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
	_update_hud(ctx)
	if _mode == "map":
		ui.panel = _map_data(ctx)
	elif _mode == "market" and _market_result.is_empty():
		ui.panel = _market_panel(float(ctx["now"]))


func _on_fishing_event(e: Dictionary) -> void:
	if str(e["type"]) == "haul":
		var nm := str((state.fish[str(e["species"])] as Dictionary)["name"])
		var stored := float(e["stored"])
		var lost := float(e["kg"]) - stored
		var txt := "+%.1f kg %s   (hold %.1f / %.0f kg)" % [stored, nm, state.hold_kg(), state.capacity_kg()]
		if lost > 0.05:
			txt += "   %.1f kg thrown back: hold full" % lost
		ui.toast(txt, PortUi.CREAM, 4.5)
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
		return {"kind": "recruit", "index": ri, "text": "E   Talk to %s, %s (%d reales)" % [str(rec["name"]), str(rec["role"]), int(rec["cost"])]}
	for it in port["interactions"]:
		var d := it as Dictionary
		var dx := x - float(d["x"])
		var dz := z - float(d["z"])
		if dx * dx + dz * dz <= float(d["r"]) * float(d["r"]):
			if str(d["kind"]) == "market":
				return {"kind": "market", "index": -1, "text": "E   Sell fish to the fishmonger (Fish Row market)"}
			return {"kind": "notice", "index": -1, "text": "E   Read the notice board / open the map"}
	var ni := npcs.nearest(x, z, TALK_R, false)
	if ni >= 0:
		return {"kind": "talk", "index": ni, "text": "E   Talk"}
	return none


func _update_hud(ctx: Dictionary) -> void:
	var crew_names: Array = []
	for c in state.crew:
		var r: Dictionary = state.recruits[c]
		crew_names.append("%s (%s)" % [str(r["name"]), str(r["role"])])
	var f: Dictionary = {}
	if fishing.active:
		var g: Dictionary = fishing.grounds[fishing.ground_id]
		f = {"active": true, "ground": str(g["name"]), "status": fishing.status, "next_s": fishing.seconds_to_haul(),
				"interval": float(fishing.p["fish.haul_interval_s"]), "hauls": fishing.hauls, "session_kg": fishing.session_kg}
	var now := float(ctx["now"])
	var prompt := str(_near["text"])
	if prompt == "" and not bool(ctx["ashore"]) and bool(ctx["sailing"]) and _mode == "none":
		if fishing.active:
			prompt = ""
		elif fishing.ground_at(float(ctx["sx"]), float(ctx["sz"])) != "":
			prompt = "F   Lower the nets"
	ui.hud = {"show": true, "purse": state.reales, "hold_kg": state.hold_kg(), "cap_kg": state.capacity_kg(), "fresh": state.avg_freshness(now),
			"warn_frac": float(state.p["port.hold_warn_frac"]), "spoil_warn": float(state.p["fish.spoil_warn"]), "crew": crew_names,
			"objective": objective(ctx), "fishing": f, "prompt": prompt}


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
	var key := k.keycode
	if key == KEY_F6 or key == KEY_F7:
		_test_key(key, ctx)
		return true
	if _mode != "none":
		return _modal_key(k, ctx)
	var used := true
	if key == KEY_M and not k.shift_pressed:
		_open_map(0 if bool(ctx["ashore"]) else (1 if not bool(ctx["docked"]) else 0), ctx)
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


func _modal_key(k: InputEventKey, ctx: Dictionary) -> bool:
	var key := k.keycode
	if key == KEY_P or key == KEY_F1 or key == KEY_F2 or key == KEY_F3 or key == KEY_F4 or key == KEY_F12:
		return false
	match _mode:
		"dialogue":
			_dialogue_key(key)
		"market":
			_market_key(key, ctx)
		"map":
			if key == KEY_ESCAPE or key == KEY_M:
				_close()
			elif key == KEY_TAB:
				_map_tab = 1 - _map_tab
				ui.panel = _map_data(ctx)
	return true


func _close() -> void:
	if _mode == "dialogue" and int(_dlg.get("idx", -1)) >= 0:
		npcs.set_talking(int(_dlg["idx"]), false)
	_mode = "none"
	_dlg = {}
	_market_result = {}
	ui.panel = {}
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
		"recruit":
			_open_recruit(int(_near["index"]), ctx)
		"market":
			_open_market(ctx)
		"notice":
			_open_map(0, ctx)
		"talk":
			_bark(int(_near["index"]), ctx)
		_:
			ui.toast("Nothing to use here. Walk up to a person, a stall or the notice board.", PortUi.DIM, 3.5)


func _bark(i: int, ctx: Dictionary) -> void:
	var n := npcs.people[i] as Dictionary
	var g := str(n["group"])
	var pool: Dictionary = barks.get(g, {})
	var keys: Array = ["any"]
	if state.hold_kg() > 0.05 and pool.has("has_fish"):
		keys.append("has_fish")
	if state.hold_kg() <= 0.05 and state.kg_total <= 0.0 and pool.has("no_fish"):
		keys.append("no_fish")
	if state.reales < 18 and pool.has("poor"):
		keys.append("poor")
	if state.crew_count() > 0 and pool.has("crew"):
		keys.append("crew")
	var lines: Array = []
	for kk in keys:
		for l in pool.get(kk, []):
			lines.append(str(l))
	if lines.is_empty():
		lines = ["..."]
	_bark_n += 1
	var line := str(lines[_bark_n % lines.size()])
	npcs.set_talking(i, true, float(ctx["wx"]), float(ctx["wz"]))
	_dlg = {"idx": i, "stage": "bark", "cid": ""}
	ui.panel = {"kind": "dialogue", "speaker": _group_title(g), "sub": "", "text": line, "keys": "E / Esc: leave", "status": ""}
	_open("dialogue")


static func _group_title(g: String) -> String:
	var titles := {"fisher": "A fisher", "merchant": "A merchant", "docker": "A dock hand", "sailor": "A sailor",
			"shopkeeper": "A shopkeeper", "townsman": "A townsman"}
	return str(titles.get(g, "Someone"))


# ---- recruits ----------------------------------------------------------------------------------------------------------------
func _open_recruit(i: int, ctx: Dictionary) -> void:
	var cid := str((npcs.people[i] as Dictionary)["recruit"])
	npcs.set_talking(i, true, float(ctx["wx"]), float(ctx["wz"]))
	_dlg = {"idx": i, "cid": cid, "stage": "offer" if _met.has(cid) else "pages", "page": 0}
	_open("dialogue")
	_refresh_dialogue()


func _refresh_dialogue() -> void:
	var cid := str(_dlg["cid"])
	var rec: Dictionary = state.recruits[cid]
	var fmt := {"cost": int(rec["cost"]), "have": state.reales, "missing": maxi(int(rec["cost"]) - state.reales, 0)}
	var stage := str(_dlg["stage"])
	var d := {"kind": "dialogue", "speaker": str(rec["name"]), "sub": "%s, %d   -   asks %d reales" % [str(rec["role"]).capitalize(), int(rec["age"]), int(rec["cost"])],
			"text": "", "keys": "", "status": "", "page": ""}
	match stage:
		"pages":
			var pages: Array = rec["pages"]
			var pg := int(_dlg["page"])
			d["text"] = str(pages[pg]).format(fmt)
			d["keys"] = "E / Enter: continue     Esc: leave"
			d["page"] = "%d / %d" % [pg + 1, pages.size()]
		"offer":
			var eff: Dictionary = rec["effect"]
			if state.can_afford(cid):
				d["text"] = str(rec["offer"]).format(fmt)
				d["status"] = "Cost %d reales.  Your purse: %d.  %s" % [int(rec["cost"]), state.reales, str(eff["text"])]
				d["status_color"] = PortUi.GREEN
				d["keys"] = "Y: hire him     N: not now     Esc: leave"
			else:
				d["text"] = str(rec["poor"]).format(fmt)
				d["status"] = "Cost %d reales.  Your purse: %d.  You are %d short.  %s" % [int(rec["cost"]), state.reales, int(fmt["missing"]), str(eff["text"])]
				d["status_color"] = PortUi.RED
				d["keys"] = "E / Esc: leave"
		"accepted":
			d["text"] = str(rec["accepted"]).format(fmt)
			d["status"] = "%s joins your crew.  Purse: %d reales." % [str(rec["name"]), state.reales]
			d["status_color"] = PortUi.GREEN
			d["keys"] = "E / Enter: close"
		"declined":
			d["text"] = str(rec["declined"]).format(fmt)
			d["keys"] = "E / Enter: close"
	ui.panel = d


func _dialogue_key(key: int) -> void:
	var stage := str(_dlg.get("stage", ""))
	if key == KEY_ESCAPE:
		_close()
		return
	var go := key == KEY_E or key == KEY_ENTER or key == KEY_KP_ENTER or key == KEY_SPACE
	match stage:
		"bark":
			if go:
				_close()
		"pages":
			if go:
				var rec: Dictionary = state.recruits[str(_dlg["cid"])]
				var n := (rec["pages"] as Array).size()
				_dlg["page"] = int(_dlg["page"]) + 1
				if int(_dlg["page"]) >= n:
					_dlg["stage"] = "offer"
					_met[str(_dlg["cid"])] = true
				_refresh_dialogue()
		"offer":
			var cid := str(_dlg["cid"])
			if state.can_afford(cid):
				if key == KEY_Y:
					_hire(cid)
				elif key == KEY_N:
					_dlg["stage"] = "declined"
					_refresh_dialogue()
			elif go:
				_close()
		"accepted", "declined":
			if go:
				_close()


func _hire(cid: String) -> void:
	var rec: Dictionary = state.recruits[cid]
	var before := state.reales
	if state.hire(cid) != "ok":
		return
	npcs.hide_recruit(cid)
	_dlg["stage"] = "accepted"
	_refresh_dialogue()
	ui.note_big("%s HIRED" % str(rec["name"]).to_upper(), "-%d reales (%d -> %d).  %s" % [int(rec["cost"]), before, state.reales, str((rec["effect"] as Dictionary)["text"])], 6.5)
	ui.toast("%s, the %s, is aboard. Crew: %d of %d." % [str(rec["name"]), str(rec["role"]), state.crew_count(), state.recruit_order.size()], PortUi.GREEN, 6.0)
	_update_markers(true)


# ---- the market --------------------------------------------------------------------------------------------------------------
func _open_market(ctx: Dictionary) -> void:
	var mi := npcs.index_of("npc_fishmonger")
	npcs.set_talking(mi, true, float(ctx["wx"]), float(ctx["wz"]))
	_dlg = {"idx": mi, "cid": "", "stage": "market"}
	_market_result = {}
	_open("market")
	ui.panel = _market_panel(float(ctx["now"]))
	if state.hold_kg() < 0.05:
		ui.toast("Barnaby: %s" % str((barks["fishmonger"] as Dictionary)["no_fish"]), PortUi.CREAM, 6.0)


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
				"price": state.quote(sp, now), "est": state.estimate_species(sp, now)})
	var prices: Array = []
	for sp in state.fish.keys():
		prices.append({"name": str((state.fish[sp] as Dictionary)["name"]), "price": state.quote(str(sp), now), "level": state.price_level(str(sp), now)})
	var keys := "Enter / E: sell everything"
	if rows.size() > 1:
		keys += "     1-%d: sell one species" % rows.size()
	keys += "     Esc: leave"
	if rows.is_empty():
		keys = "Esc: leave"
	return {"kind": "market", "monger": str((barks["fishmonger"] as Dictionary)["name"]), "rows": rows, "prices": prices, "total": state.estimate_all(now),
			"purse": state.reales, "keys": keys, "result": {}}


func _market_key(key: int, ctx: Dictionary) -> void:
	var now := float(ctx["now"])
	if key == KEY_ESCAPE:
		_close()
		return
	var go := key == KEY_E or key == KEY_ENTER or key == KEY_KP_ENTER or key == KEY_SPACE
	if not _market_result.is_empty():
		if go:
			_market_result = {}
			ui.panel = _market_panel(now)
		return
	var sp_list := state.species_in_hold()
	if sp_list.is_empty():
		if go:
			_close()
		return
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
	elif key >= KEY_1 and key <= KEY_9 and (key - KEY_1) < sp_list.size():
		var sp := str(sp_list[key - KEY_1])
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
	ui.panel = {"kind": "market", "monger": str((barks["fishmonger"] as Dictionary)["name"]), "rows": [], "prices": [], "total": 0, "purse": state.reales,
			"keys": "Enter / E: back to the counter     Esc: leave", "result": _market_result}
	ui.note_big("+%d reales" % total, "%.1f kg of fish sold.  Purse %d -> %d reales." % [kg, before, state.reales], 5.5)
	ui.toast("Sold %.1f kg for %d reales. Purse: %d." % [kg, total, state.reales], PortUi.GOLD, 6.0)
	_update_markers(false)


# ---- the map ---------------------------------------------------------------------------------------------------------------------
func _open_map(tab: int, ctx: Dictionary) -> void:
	_map_tab = tab
	if not ui.has_map_image("district"):
		var pb: Array = (port["map"] as Dictionary)["bounds"]
		ui.set_map_image("district", PortUi.build_map_image(world, pb, 1.0))
	if not ui.has_map_image("waters"):
		ui.set_map_image("waters", PortUi.build_map_image(world, WATERS_BOUNDS, 16.0))
	_open("map")
	ui.panel = _map_data(ctx)


func _map_data(ctx: Dictionary) -> Dictionary:
	var m: Dictionary = port["map"]
	var buildings: Array = []
	var labels: Array = [{"x": -82.0, "z": -19.0, "text": "FISH MARKET"}, {"x": -47.0, "z": -17.0, "text": "the Cut"}, {"x": 4.0, "z": 5.5, "text": "plaza"},
			{"x": -114.0, "z": 1.0, "text": "Quay Street"}, {"x": -118.0, "z": 12.0, "text": "west wharf"}]
	var named := {"warehouse": "warehouse", "tavern": "tavern", "harbourmaster": "harbourmaster", "hut_shipwright": "boatyard"}
	for s in (world.get("meta") as Dictionary)["structures"]:
		var d := s as Dictionary
		var nm := str(d["name"])
		var is_house := nm.begins_with("cottage") or nm.begins_with("fisher_hut") or named.has(nm) or nm.begins_with("warehouse")
		if not is_house or not d.has("w_m"):
			continue
		var hw := float(d["w_m"]) * 0.5
		var z1 := float(d["z_m"])
		var z0 := z1 - float(d.get("d_m", 6.0))
		buildings.append([float(d["x_m"]) - hw, z0, float(d["x_m"]) + hw, z1])
		if named.has(nm):
			labels.append({"x": float(d["x_m"]) - hw + 1.0, "z": (z0 + z1) * 0.5, "text": str(named[nm])})
	var recs: Array = []
	for c in state.recruit_order:
		var cid := str(c)
		var r: Dictionary = state.recruits[cid]
		var spot: Dictionary = (port["recruit_spots"] as Dictionary)[cid]
		var st := "hired" if state.is_hired(cid) else ("afford" if state.can_afford(cid) else "poor")
		recs.append({"x": spot["x"], "z": spot["z"], "name": str(r["name"]).replace("\"", ""), "role": str(r["role"]), "cost": int(r["cost"]), "state": st,
				"short": maxi(int(r["cost"]) - state.reales, 0), "place": str(r["place"])})
	var pts: Array = []
	for it in port["interactions"]:
		var d2 := it as Dictionary
		pts.append({"x": d2["x"], "z": d2["z"], "kind": str(d2["kind"]), "name": str(d2["name"])})
	var grounds: Array = []
	var sx := float(ctx["sx"])
	var sz := float(ctx["sz"])
	for id in fishing.ground_order:
		var g: Dictionary = fishing.grounds[id]
		var dist := maxf(Vector2(float(g["x"]) - sx, float(g["z"]) - sz).length() - float(g["r"]), 0.0)
		var names: Array = []
		for sw in g["species"]:
			names.append(str((state.fish[str((sw as Array)[0])] as Dictionary)["name"]))
		var open := int(g["min_crew"]) <= state.crew_count()
		var line := "%s%s" % ["%d m away" % int(roundf(dist)) if dist > 0.0 else "you are here", "" if open else "  (needs %d hand)" % int(g["min_crew"])]
		grounds.append({"x": g["x"], "z": g["z"], "r": g["r"], "name": str(g["name"]), "open": open, "line": line})
	var harbor: Dictionary = (world.get("meta") as Dictionary)["harbor_layout"]
	var berth: Dictionary = harbor["berth"]
	return {"kind": "map", "tab": _map_tab, "bounds": (m["bounds"] as Array) if _map_tab == 0 else WATERS_BOUNDS, "wharf": m["wharf"], "bridges": m["bridges"],
			"buildings": buildings, "recruits": recs, "points": pts, "grounds": grounds, "labels": labels, "berth": [berth["x"], berth["z"]],
			"ship": Vector2(sx, sz), "ship_heading": float(ctx.get("sheading", 0.0)), "player": Vector2(float(ctx["wx"]), float(ctx["wz"])),
			"player_heading": 0.0, "ashore": bool(ctx["ashore"]), "docked": bool(ctx["docked"])}
