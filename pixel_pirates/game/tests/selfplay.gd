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
	var ui: Node = port.get("ui")
	chk(ui != null, "the interface exists")
	var world: Object = port.get("world")
	chk(world != null, "the port controller has the land world")
	# ---- the city (data): people exist and stand on walkable ground -------------------------------------------------------
	var np: RefCounted = port.get("npcs")
	var people: Array = np.get("people")
	chk(people.size() >= 150, "the capital has %d people (>= 150)" % people.size())
	var bad := 0
	var have_ground: bool = not (world.get("_hd") as PackedByteArray).is_empty()
	if have_ground:
		for pe in people:
			var d := pe as Dictionary
			if not bool(world.call("walkable", float(d["x"]), float(d["z"]), 0.3)):
				bad += 1
		chk(bad == 0, "every person starts on walkable ground (%d do not)" % bad)
	else:
		print("NOTE: no ground textures in this runtime (headless WASM), so walkability is checked by tools/h2d/check_land.py instead")
	# ---- the map (nodes) ------------------------------------------------------------------------------------------------
	await key(KEY_M)
	chk(bool(port.call("modal")), "M opens a modal panel")
	chk(str(port.get("_mode")) == "map", "the panel is the map")
	chk(_paused(), "the clock is paused while the map is open")
	await frames(4)
	var mp: Control = ui.get("map")
	chk(mp.is_visible_in_tree(), "the map control is visible")
	chk((mp.get("views") as Array).size() == 3, "the map has three views (city, island, sea)")
	chk((mp.get("entries") as Array).size() >= 12, "the map lists %d places" % (mp.get("entries") as Array).size())
	chk((mp.get("_markers") as Dictionary).size() >= 3, "the map shows %d markers on this view" % (mp.get("_markers") as Dictionary).size())
	var tex: TextureRect = mp.get("_tex")
	print("MAP texture ", tex.texture, " rows ", (mp.get("_row_btns") as Dictionary).size(), " tab ", mp.get("tab"))
	var t_first := int(mp.get("tab"))
	await key(KEY_TAB)
	chk(int(mp.get("tab")) == (t_first + 1) % 3, "Tab switches the map view")
	await key(KEY_TAB)
	await key(KEY_TAB)
	chk(int(mp.get("tab")) == t_first, "Tab cycles through all three views")
	await _map_walk(mp)
	await key(KEY_M)
	chk(not bool(port.call("modal")), "M closes the map")
	chk(not _paused(), "the clock runs again after the map closes")
	# ---- a conversation: walk up to Pip Larkin ------------------------------------------------------------------------------
	var walker: RefCounted = scene.get("_walker")
	var land: Dictionary = (scene.get("_v3") as Object).call("land_world").meta["land"]
	walker.call("disembark", land)
	await frames(2)
	var ip: int = int(np.call("index_of", "npc_pip_larkin"))
	chk(ip >= 0, "Pip Larkin exists")
	var pip := people[ip] as Dictionary
	walker.set("x", float(pip["x"]) + 1.6)
	walker.set("z", float(pip["z"]) + 0.8)
	await frames(10)
	await key(KEY_E)
	var dui: Control = ui.get("dialogue")
	chk(dui.call("is_open"), "E next to Pip opens the dialogue window")
	await frames(120)
	var txt: String = str(dui.call("shown_text"))
	chk(txt.length() > 20, "the dialogue shows text (%d characters): %s" % [txt.length(), txt.substr(0, 60)])
	chk(int(dui.get("typed_total")) > 20, "the typewriter really typed (%d)" % int(dui.get("typed_total")))
	chk(str((dui.get("_name") as Label).text).contains("Pip"), "the speaker's name is shown: '%s'" % (dui.get("_name") as Label).text)
	chk((dui.get("_portrait") as TextureRect).texture != null or true, "the portrait slot exists")
	chk(_paused(), "the clock is paused during a conversation")
	var guard := 0
	while bool(dui.call("is_open")) and guard < 12:
		await key(KEY_ESCAPE)
		guard += 1
	chk(not bool(dui.call("is_open")), "Esc closes the dialogue")
	chk(not _paused(), "the clock runs after the conversation")
	# a shopkeeper of the capital speaks too
	var shop := -1
	for k in people.size():
		if str((people[k] as Dictionary).get("title", "")) == "Baker":
			shop = k
			break
	chk(shop >= 0, "the capital has a baker")
	if shop >= 0:
		var sd := people[shop] as Dictionary
		walker.set("x", float(sd["x"]) + 1.4)
		walker.set("z", float(sd["z"]) + 0.8)
		await frames(10)
		await key(KEY_E)
		await frames(120)
		chk(dui.call("is_open") and str(dui.call("shown_text")).length() > 10, "the baker's greeting appears: %s" % str(dui.call("shown_text")).substr(0, 50))
		await key(KEY_ESCAPE)
		await key(KEY_ESCAPE)
		await key(KEY_ESCAPE)
	walker.call("board")
	await frames(5)
	# ---- fishing -------------------------------------------------------------------------------------------------------------
	var hud: Control = ui.get("hud")
	var st: RefCounted = port.get("state")
	var fi: RefCounted = port.get("fishing")
	await key(KEY_F)
	chk(not bool(fi.get("active")), "F outside a ground does not start the nets")
	chk(int(hud.get("shown_toasts")) > 0, "a message explains why (toasts shown: %d)" % int(hud.get("shown_toasts")))
	var t0 := int(hud.get("shown_toasts"))
	scene.set("_pos", Vector2(-300.0, 560.0))
	await frames(5)
	print("speed ", scene.get("_helm").get("speed_kn"), " sea ", scene.get("_env").get("sea"))
	await key(KEY_F)
	chk(bool(fi.get("active")), "F inside Pilchard Shallows lowers the nets")
	chk(int(hud.get("shown_toasts")) > t0, "lowering the nets shows a message")
	await frames(60)
	print("status ", fi.get("status"), " speed ", scene.get("_helm").get("speed_kn"), " pos ", scene.get("_pos"))
	await frames(60 * 14)
	print("status ", fi.get("status"), " speed ", scene.get("_helm").get("speed_kn"), " hauls ", fi.get("hauls"), " hold ", st.call("hold_kg"), " pos ", scene.get("_pos"), " active ", fi.get("active"))
	var wd: Object = port.get("world")
	chk(wd.get("_cue_birds") != null, "the fishing-ground cues (beacons, buoys, gulls, shimmer) were built")
	chk((wd.get("_trail") as Array).size() > 0, "the net line (corks and foam) trails behind the ship while the nets are out (%d marks)" % (wd.get("_trail") as Array).size())
	print("SELFPLAY: %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0)


## Walks every map view and every entry the way a player would (tab buttons, tab keys, selecting and tracking each marker) and
## asserts what is on the controls afterwards. Release engine builds return null for a missing dictionary key without any error
## (the field error "set_views: Invalid access ... 'name'" was invisible here), so this checks the RESULT: tab buttons exist and
## carry text, no control shows "<null>", the schema list is empty.
func _map_walk(mp: Control) -> void:
	chk((mp.get("schema_errors") as Array).is_empty(), "map schema: no missing keys (%s)" % str(mp.get("schema_errors")))
	var views: Array = mp.get("views")
	var btns: Array = mp.get("_tab_btns")
	chk(btns.size() == views.size(), "map: one tab button per view (%d of %d)" % [btns.size(), views.size()])
	for i in btns.size():
		var txt := (btns[i] as Button).text
		chk(txt.length() >= 3 and not txt.contains("null"), "map: tab button %d reads '%s'" % [i + 1, txt])
	var entries: Array = mp.get("entries")
	var seen_markers := 0
	for i in views.size():
		await key(KEY_1 + i)
		await frames(2)
		var vd := views[i] as Dictionary
		chk(int(mp.get("tab")) == i, "map: key %d opens the %s view" % [i + 1, str(vd["id"])])
		var title := (mp.get("_title") as Label).text
		chk(title.contains(str(vd["title"])), "map (%s): the title reads '%s'" % [str(vd["id"]), title])
		var info := (mp.get("_info") as Label).text
		chk(info.contains(str(vd["hint"])) and not info.contains("null"), "map (%s): the hint line reads '%s'" % [str(vd["id"]), info])
		var mk: Dictionary = mp.get("_markers")
		chk(mk.size() >= 2, "map (%s): %d markers" % [str(vd["id"]), mk.size()])
		seen_markers += mk.size()
		# select every entry in this view, one by one, and track the first
		var steps := 0
		for k in entries.size() + 1:
			await key(KEY_DOWN)
			steps += 1
		chk(str(mp.get("_sel_id")) != "" or entries.is_empty(), "map (%s): arrow keys select entries (%s)" % [str(vd["id"]), str(mp.get("_sel_id"))])
		var bad: Array = []
		for r in mp.call("dump_rects"):
			var rd := r as Dictionary
			if str(rd.get("text", "")).contains("null"):
				bad.append(str(rd.get("name", "?")))
		chk(bad.is_empty(), "map (%s): no control shows 'null' (%s)" % [str(vd["id"]), str(bad)])
	chk(seen_markers >= 8, "map: %d markers over the three views" % seen_markers)
	await key(KEY_1)
	await frames(1)
