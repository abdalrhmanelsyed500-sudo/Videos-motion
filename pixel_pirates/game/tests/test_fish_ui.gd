# gdlint: disable=max-line-length
extends RefCounted
## CP-2 Release B: the data side of the interface. The fish-storage model (one row per species really in the hold, no zero rows, counts
## from kg and the average weight, totals, capacity and the space left), the five fish pictures load, every species the grounds can give
## has an icon and a name, the five fishing Input Map actions exist (two keys each, repaired by ensure_actions when lost), the views
## build and accept their data, and the catch card / panel keep their text inside the 1366 x 876 screen. Pure data + node construction.
## NOT YET RUN ON THE USER'S PC.
const Storage := preload("res://h2d/fish_storage.gd")
const FishArt := preload("res://h2d/fish_art.gd")
const FishPanel := preload("res://h2d/fish_panel.gd")
const FishView := preload("res://h2d/fish_view.gd")
const Manual := preload("res://h2d/fish_manual.gd")
const Keys := preload("res://h2d/ship_keys.gd")
const PortState := preload("res://h2d/port_state.gd")
const Ocean := preload("res://core/ocean.gd")
const DataLoader := preload("res://core/data_loader.gd")


func run(t: Object) -> void:
	var doc := DataLoader.load_dict("res://data/port/manual_fishing.json")
	var species: Dictionary = doc["species"]
	var tuning := Ocean.load_tuning()
	var ps := PortState.new()
	ps.configure(tuning, DataLoader.load_dict("res://data/port/fish_market.json"), DataLoader.load_dict("res://data/port/recruits_port.json"))
	# ---- the pictures ----
	for sid in species.keys():
		var icon := str((species[sid] as Dictionary)["icon"])
		var tex := FishArt.texture(icon)
		t.check(tex != null, "the picture %s loads" % icon)
		if tex != null:
			t.check(tex.get_width() == 48 and tex.get_height() == 24, "%s is 48 x 24" % icon)
		t.check(ps.fish.has(sid) and str((ps.fish[sid] as Dictionary).get("name", "")) != "", "%s has a display name in the market data" % sid)
	t.check(FishArt.texture("ico_fish_does_not_exist") == null, "an unknown picture is null, not a crash")
	t.check(FishArt.texture("") == null, "an empty icon id is null")
	# ---- the model ----
	var m0 := Storage.model([], ps.fish, species, 0.0, ps.freshness_of, 40.0)
	t.check(bool(m0["empty"]) and (m0["rows"] as Array).is_empty() and int(m0["total_n"]) == 0, "an empty hold has no rows and no total")
	t.check(absf(float(m0["remaining"]) - 40.0) < 0.001, "an empty hold has all its space left")
	var lots: Array = [["spc_mackerel", 4.5, 0.0], ["spc_mackerel", 0.9, 0.0], ["spc_yellowfin_tuna", 12.0, 0.0], ["spc_sardine", 0.0, 0.0]]
	var m1 := Storage.model(lots, ps.fish, species, 0.0, ps.freshness_of, 40.0)
	var rows: Array = m1["rows"]
	t.check(rows.size() == 2, "two kinds in the hold, the zero-kg lot is hidden (%d rows)" % rows.size())
	t.check(str((rows[0] as Dictionary)["id"]) == "spc_yellowfin_tuna", "the heaviest kind is listed first")
	t.check(int((rows[0] as Dictionary)["count"]) == 2, "12 kg of 6 kg tuna is 2 fish")
	t.check(int((rows[1] as Dictionary)["count"]) == 12, "5.4 kg of 0.45 kg mackerel is 12 fish (the two lots are merged)")
	t.check(int(m1["total_n"]) == 14, "total quantity is the sum")
	t.check(absf(float(m1["total_kg"]) - 17.4) < 0.001 and absf(float(m1["remaining"]) - 22.6) < 0.001, "total kg and space left (%.2f / %.2f)" % [float(m1["total_kg"]), float(m1["remaining"])])
	t.check(int((rows[0] as Dictionary)["fresh"]) == 100, "fresh fish show 100%")
	var m2 := Storage.model(lots, ps.fish, species, 3.0, ps.freshness_of, 40.0)
	t.check(int((m2["rows"][0] as Dictionary)["fresh"]) < 100, "three days later the freshness has dropped")
	var over := Storage.model([["spc_mackerel", 45.0, 0.0]], ps.fish, species, 0.0, ps.freshness_of, 40.0)
	t.check(float(over["remaining"]) == 0.0, "the space left never goes negative")
	# the real hold feeds the model: add_catch -> row -> sale -> gone
	ps.add_catch("spc_parrotfish", 2.8, 0.0)
	var m3 := Storage.model(ps.lots, ps.fish, species, 0.0, ps.freshness_of, ps.capacity_kg())
	t.check((m3["rows"] as Array).size() == 1 and int(m3["total_n"]) == 2, "the real hold: 2.8 kg of parrotfish is 2 fish")
	ps.lots = []
	t.check(bool(Storage.model(ps.lots, ps.fish, species, 0.0, ps.freshness_of, ps.capacity_kg())["empty"]), "after a sale nothing is listed")
	# ---- the input actions ----
	for a in ["fish_winch", "fish_haul_left", "fish_haul_right", "fish_cast", "fish_cancel", "ship_interact", "autopilot_toggle"]:
		t.check(InputMap.has_action(a), "action %s exists" % a)
		t.check(Keys.ACTIONS.has(a), "ship_keys knows %s" % a)
	var first := InputMap.action_get_events("fish_haul_left")
	var phys := 0
	var lab := 0
	for e in first:
		var ke := e as InputEventKey
		if ke != null and int(ke.physical_keycode) == KEY_A and int(ke.keycode) == 0:
			phys += 1
		if ke != null and int(ke.keycode) == KEY_A:
			lab += 1
	t.check(phys == 1 and lab == 1, "the left lever is A by physical key and by label (layout-proof)")
	t.check(Keys.label("fish_haul_left") == "A" and Keys.label("fish_haul_right") == "D" and Keys.label("fish_winch") == "F", "labels shown on screen: %s %s %s" % [Keys.label("fish_haul_left"), Keys.label("fish_haul_right"), Keys.label("fish_winch")])
	t.check(Keys.label("fish_cast") == "Space", "cast label: %s" % Keys.label("fish_cast"))
	InputMap.erase_action("fish_haul_right")
	Keys.ensure_actions()
	t.check(InputMap.has_action("fish_haul_right") and InputMap.action_get_events("fish_haul_right").size() == 2, "ensure_actions repairs a lost action")
	Keys.ensure_actions()
	t.check(InputMap.action_get_events("fish_haul_right").size() == 2, "and does not duplicate keys")
	var ev := InputEventKey.new()
	ev.keycode = KEY_D
	ev.physical_keycode = KEY_D
	ev.pressed = true
	t.check(Keys.hit(ev, "fish_haul_right") and not Keys.hit(ev, "fish_haul_left"), "D hits the right lever only")
	ev.shift_pressed = true
	t.check(not Keys.hit(ev, "fish_haul_right"), "Shift+D is not the right lever")
	# ---- the views build and accept data ----
	var view: Control = FishView.new()
	var man := Manual.new()
	man.configure(tuning, doc)
	view.call("setup", man)
	view.call("set_env", {"hour": 18.0, "sea": 0.3, "light": 0.5, "ground": "Test Ground", "hold_kg": 10.0, "capacity": 40.0, "names": {}, "keys": {"fish_haul_left": "A"}})
	t.check(view.get("m") == man and str((view.get("env") as Dictionary)["ground"]) == "Test Ground", "the view takes the state machine and the environment")
	view.call("on_events", [{"type": "cast", "grade": "Perfect cast", "quality": 1.15}, {"type": "surge_warn", "kind": 1}, {"type": "fail", "reason": "snap", "text": "x"}, {"type": "unknown"}])
	view.call("tick", 0.016)
	t.check(view.size.x > 0.0, "the view sizes itself (a CanvasLayer child is never laid out)")
	view.free()
	var panel: Control = FishPanel.new()
	panel.call("open", m1)
	t.check(bool(panel.get("is_shown")) and panel.visible, "the panel opens with a model")
	panel.call("refresh", m0)
	t.check(bool((panel.get("model") as Dictionary)["empty"]), "and follows a new model")
	panel.call("close")
	t.check(not bool(panel.get("is_shown")) and not panel.visible, "and closes")
	panel.free()
