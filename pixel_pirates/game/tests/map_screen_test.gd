extends SceneTree
## The map scene ON ITS OWN (no game, no port controller): res://ui/map/map_screen.tscn with a mock provider.
##   godot --headless --fixed-fps 60 --path game --script res://tests/map_screen_test.gd      (prints MAPSCREEN n checks, m failed)
## Sends real key events through the viewport, real mouse clicks through the GUI, and measures the Control tree in SubViewports of
## several sizes (the headless main window is 0 x 0, a SubViewport has a real size). It proves logic + layout, NOT the look.
const SCENE := "res://ui/map/map_screen.tscn"
const Screen := preload("res://ui/map/map_screen.gd")
var checks := 0
var fails := 0
var opened_n := 0
var closed_n := 0
var toasts: Array = []
var tracks: Array = []
var mock := {"ashore": true, "docked": false, "player": Vector2(16, 4), "ship": Vector2(21.4, 21.0), "tracked": "", "heading": 0.5}
var places: Array = []


func chk(cond: bool, msg: String) -> void:
	checks += 1
	if not cond:
		fails += 1
		print("  FAIL: ", msg)


func frames(n: int) -> void:
	for i in n:
		await process_frame


func _initialize() -> void:
	_play()


func provider() -> Dictionary:
	var entries: Array = places.duplicate(true)
	entries.append({"id": "ship", "kind": "ship", "name": "Your sloop", "detail": "at the pier", "x": 21.4, "z": 21.0, "rank": 3, "views": ["city", "island", "sea"]})
	return {"entries": entries, "tracked": mock["tracked"], "player": mock["player"], "ship": mock["ship"], "ship_heading": mock["heading"],
			"ashore": mock["ashore"], "docked": mock["docked"],
			"rings": [{"x": -300.0, "z": 560.0, "r": 90.0, "open": true, "views": ["sea", "island"]}]}


func make(parent: Node) -> Node:
	var s: Node = (load(SCENE) as PackedScene).instantiate()
	s.set("provider", provider)
	s.set("notify", func(txt: String) -> void: toasts.append(txt))
	s.connect("opened", func(_t: int) -> void: opened_n += 1)
	s.connect("closed", func() -> void: closed_n += 1)
	s.connect("track_requested", func(id: String) -> void: tracks.append(id))
	parent.add_child(s)
	return s


## One key press delivered to `vp` the way the engine delivers it. `keycode` = what the layout produced, `physical` = the key place.
func key(vp: Viewport, keycode: int, physical: int = -1, shift: bool = false, echo: bool = false, wait: bool = true) -> void:
	var ev := InputEventKey.new()
	ev.keycode = keycode as Key
	ev.physical_keycode = (keycode if physical < 0 else physical) as Key
	ev.shift_pressed = shift
	ev.echo = echo
	ev.pressed = true
	vp.push_input(ev, false)
	if wait:
		await process_frame
	var up := InputEventKey.new()
	up.keycode = ev.keycode
	up.physical_keycode = ev.physical_keycode
	up.pressed = false
	vp.push_input(up, false)
	if wait:
		await process_frame


func click(vp: Viewport, pos: Vector2) -> void:
	for pressed in [true, false]:
		var ev := InputEventMouseButton.new()
		ev.button_index = MOUSE_BUTTON_LEFT
		ev.position = pos
		ev.global_position = pos
		ev.pressed = pressed
		ev.button_mask = MOUSE_BUTTON_MASK_LEFT if pressed else 0
		vp.push_input(ev, false)
		await process_frame


func _play() -> void:
	# ---- the Input Map action exists in the PROJECT FILE, with both keys -------------------------------------------------------
	chk(InputMap.has_action("open_map"), "project.godot declares the action open_map")
	var phys := false
	var label := false
	for e in InputMap.action_get_events("open_map"):
		var ke := e as InputEventKey
		if ke != null and ke.physical_keycode == KEY_M and ke.keycode == KEY_NONE:
			phys = true
		if ke != null and ke.keycode == KEY_M:
			label = true
	chk(phys and label, "open_map has the physical M and the key labelled M (physical %s, label %s)" % [str(phys), str(label)])
	# ---- repair: an action that lost its keys is re-created by the screen --------------------------------------------------------
	InputMap.erase_action("open_map")
	Screen.ensure_action()
	chk(InputMap.action_get_events("open_map").size() == 2, "ensure_action() re-creates a deleted action with its 2 keys")
	Screen.ensure_action()
	chk(InputMap.action_get_events("open_map").size() == 2, "ensure_action() twice does not duplicate the keys")
	# ---- places for the mock (real data) --------------------------------------------------------------------------------------
	var cay: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://h2d/art/anvil_cay.json"))
	for pl in (((cay as Dictionary)["port"] as Dictionary)["places"] as Array):
		var d: Dictionary = (pl as Dictionary).duplicate()
		d["detail"] = str(d.get("what", ""))
		places.append(d)
	var spots: Dictionary = (((cay as Dictionary)["port"] as Dictionary)["recruit_spots"] as Dictionary)
	for cid in spots.keys():
		var sp: Dictionary = spots[cid]
		places.append({"id": "recruit_" + str(cid), "kind": "recruit", "name": str(cid).replace("crew_", "").capitalize(), "detail": "recruit", "x": sp["x"], "z": sp["z"], "rank": 2, "views": ["city", "island"]})
	places.append({"id": "ground_pilchard", "kind": "ground", "name": "Pilchard Shallows", "detail": "fishing ground", "x": -300.0, "z": 560.0, "rank": 2, "views": ["sea", "island"]})
	await frames(2)
	await _scene_basics()
	await _keys_and_cycles()
	await _focus_and_layouts()
	await _tabs_zoom_pan()
	await _mouse()
	await _states()
	await _errors()
	await _layout_sizes()
	print("MAPSCREEN %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)


func _scene_basics() -> void:
	var s := make(root)
	await frames(3)
	chk(str(s.get("init_error")) == "", "the scene builds without an error (%s)" % str(s.get("init_error")))
	chk(not bool(s.call("is_open")), "the map starts closed")
	chk((s.get("views") as Array).size() == 3, "three views loaded")
	var tabs := s.call("button_node", "tabs") as Control
	chk(tabs.get_child_count() == 3, "three tab buttons: " + str(tabs.get_children().map(func(c: Node) -> String: return (c as Button).text)))
	chk(str((tabs.get_child(0) as Button).text).contains("City") and str((tabs.get_child(1) as Button).text).contains("Island") and str((tabs.get_child(2) as Button).text).contains("Sea"), "the tabs read City, Island, Sea")
	var ob := s.call("button_node", "open") as Button
	chk(ob.visible and ob.focus_mode == Control.FOCUS_NONE, "the corner MAP button is visible and cannot take keyboard focus")
	chk(ob.text.contains("MAP"), "the button reads: " + ob.text)
	var cb := s.call("button_node", "close") as Button
	chk(cb.text.to_lower().contains("close") and cb.focus_mode == Control.FOCUS_NONE, "the Close button reads: " + cb.text)
	s.queue_free()
	await frames(2)


func _keys_and_cycles() -> void:
	opened_n = 0
	closed_n = 0
	var s := make(root)
	await frames(3)
	# M (Latin layout) opens; M closes; 25 times
	for i in 25:
		await key(root, KEY_M)
		if not bool(s.call("is_open")):
			chk(false, "cycle %d: M did not open the map" % i)
			break
		await key(root, KEY_M)
		if bool(s.call("is_open")):
			chk(false, "cycle %d: M did not close the map" % i)
			break
	chk(opened_n == 25 and closed_n == 25, "25 open/close cycles by M: opened %d, closed %d" % [opened_n, closed_n])
	var ov := s.get_node("%Overlay") as Control
	chk(not ov.visible and not bool(s.call("is_open")), "after the cycles the map is closed and hidden")
	# Esc closes, the Close button closes, the corner button opens
	await key(root, KEY_M)
	await key(root, KEY_ESCAPE)
	chk(not bool(s.call("is_open")), "Esc closes the map")
	(s.call("button_node", "open") as Button).pressed.emit()
	await frames(1)
	chk(bool(s.call("is_open")), "the corner button opens the map")
	chk(not (s.call("button_node", "open") as Button).visible, "the corner button hides while the map is open")
	(s.call("button_node", "close") as Button).pressed.emit()
	await frames(1)
	chk(not bool(s.call("is_open")) and (s.call("button_node", "open") as Button).visible, "the Close button closes it and the corner button returns")
	chk(opened_n == closed_n, "every open was matched by one close (%d / %d)" % [opened_n, closed_n])
	# layouts: Arabic (keycode is the Arabic letter, physical = M), AZERTY (keycode M, physical = the key at QWERTY ';'), Russian
	await key(root, 0x0629, KEY_M)
	chk(bool(s.call("is_open")), "ARABIC layout (keycode U+0629, physical M) opens the map")
	await key(root, 0x0629, KEY_M)
	chk(not bool(s.call("is_open")), "ARABIC layout closes it again")
	await key(root, KEY_M, KEY_SEMICOLON)
	chk(bool(s.call("is_open")), "AZERTY-like layout (keycode M, physical elsewhere) opens the map")
	await key(root, KEY_M, KEY_SEMICOLON)
	await key(root, 0x043C, KEY_M)
	chk(bool(s.call("is_open")), "RUSSIAN layout (keycode U+043C, physical M) opens the map")
	await key(root, KEY_ESCAPE)
	# keys that must NOT open it
	await key(root, KEY_M, -1, true)
	chk(not bool(s.call("is_open")), "Shift+M does not open the map (it is the ship-motion key)")
	await key(root, KEY_M, -1, false, true)
	chk(not bool(s.call("is_open")), "a held-key repeat (echo) does not open it")
	var ev := InputEventKey.new()
	ev.keycode = KEY_M
	ev.physical_keycode = KEY_M
	ev.ctrl_pressed = true
	ev.pressed = true
	root.push_input(ev, false)
	await frames(1)
	chk(not bool(s.call("is_open")), "Ctrl+M does not open it")
	for other in [KEY_N, KEY_E, KEY_F, KEY_SPACE, KEY_W]:
		await key(root, other)
	chk(not bool(s.call("is_open")), "other keys do not open it")
	# the same frame twice: a duplicated delivery must not open-and-close
	await key(root, KEY_M, -1, false, false, false)
	await key(root, KEY_M, -1, false, false, false)
	await frames(2)
	chk(bool(s.call("is_open")), "two M events in the SAME frame leave the map open (no open-then-close flicker)")
	await key(root, KEY_M)
	chk(not bool(s.call("is_open")), "a later M closes it")
	# opening again repeatedly through the API too
	chk(bool(s.call("request_open", 1)) and int(s.get("tab")) == 1, "request_open(1) opens on the Island tab")
	chk(bool(s.call("request_open", 2)) and int(s.get("tab")) == 2, "request_open(2) while open switches to the Sea tab")
	s.call("close_map")
	s.call("close_map")
	chk(not bool(s.call("is_open")), "close_map() twice is harmless")
	chk(opened_n == closed_n, "opened == closed after everything (%d / %d)" % [opened_n, closed_n])
	# leaving the tree while open still reports `closed` (the host would otherwise stay paused)
	var c0 := closed_n
	s.call("open_map")
	s.queue_free()
	await frames(2)
	chk(closed_n == c0 + 1, "freeing the open map emits `closed` once (%d -> %d)" % [c0, closed_n])


func _focus_and_layouts() -> void:
	var s := make(root)
	var le := LineEdit.new()
	root.add_child(le)
	var btn := Button.new()
	btn.text = "focus thief"
	root.add_child(btn)
	await frames(3)
	btn.grab_focus()
	await frames(1)
	chk(root.gui_get_focus_owner() == btn, "a Button holds the keyboard focus")
	await key(root, KEY_M)
	chk(bool(s.call("is_open")), "M opens the map even while a Button has the focus")
	chk(root.gui_get_focus_owner() == null, "opening released the focus")
	await key(root, KEY_ESCAPE)
	le.grab_focus()
	await frames(1)
	await key(root, KEY_M)
	chk(not bool(s.call("is_open")), "typing M into a text field does not open the map")
	le.release_focus()
	btn.queue_free()
	le.queue_free()
	await frames(1)
	await key(root, KEY_M)
	chk(bool(s.call("is_open")), "after the text field lost focus M works again")
	await key(root, KEY_M)
	s.queue_free()
	await frames(2)


func _tabs_zoom_pan() -> void:
	var sub := _sub(1280, 720)
	var s := make(sub)
	await frames(3)
	mock["ashore"] = true
	mock["docked"] = false
	await key(sub, KEY_M)
	await frames(3)
	chk(int(s.get("tab")) == 0, "ashore: opens on the City tab (%d)" % int(s.get("tab")))
	var v := s.call("verify_layout") as Dictionary
	chk(bool(v["ok"]), "layout is valid at 1280x720: %s" % str(v["why"]))
	var views: Array = s.get("views")
	var pic := s.get_node("%Picture") as TextureRect
	for i in 3:
		await key(sub, KEY_1 + i)
		await frames(2)
		var vd := views[i] as Dictionary
		chk(int(s.get("tab")) == i, "key %d selects tab %d" % [i + 1, i])
		chk(pic.texture != null and absf(pic.texture.get_width() - Model_px(vd).x) <= 1.0, "tab %d shows its own picture (%s, %d px wide)" % [i, str(vd["file"]), pic.texture.get_width() if pic.texture != null else 0])
		chk(str((s.get_node("%Title") as Label).text).contains(str(vd["title"])), "tab %d title shows '%s'" % [i, str(vd["title"])])
		chk(((s.call("tab_button", i)) as Button).button_pressed, "tab %d button looks pressed" % i)
		var snap := s.call("snapshot") as Dictionary
		chk(int(snap["markers"]) >= 2, "tab %d has %d markers" % [i, int(snap["markers"])])
		chk(int(snap["markers_in_frame"]) >= 1 and int(snap["names_shown"]) >= 1, "tab %d: %d markers on screen, %d names readable" % [i, int(snap["markers_in_frame"]), int(snap["names_shown"])])
	chk(str(s.call("rows_text")).contains("Pilchard"), "the Sea/Island list shows the fishing ground")
	await key(sub, KEY_TAB)
	chk(int(s.get("tab")) == 0, "Tab wraps from Sea to City")
	# each tab button by real click (mouse)
	var tb := s.call("tab_button", 2) as Button
	await click(sub, tb.get_global_rect().get_center())
	chk(int(s.get("tab")) == 2, "a real mouse click on the Sea tab button selects it")
	# zoom + pan
	await click(sub, (s.call("tab_button", 0) as Button).get_global_rect().get_center())
	var z0 := float((s.call("snapshot") as Dictionary)["zoom"])
	await key(sub, KEY_EQUAL)
	var z1 := float((s.call("snapshot") as Dictionary)["zoom"])
	chk(z1 > z0 * 1.2, "'+' zooms in (%.2f -> %.2f)" % [z0, z1])
	await key(sub, KEY_MINUS)
	await key(sub, KEY_MINUS)
	await key(sub, KEY_MINUS)
	await key(sub, KEY_MINUS)
	var snap2 := s.call("snapshot") as Dictionary
	chk(float(snap2["zoom"]) >= float(snap2["fit_zoom"]) - 0.0001, "zoom out stops at the fit zoom (%.3f >= %.3f)" % [float(snap2["zoom"]), float(snap2["fit_zoom"])])
	for i in 12:
		s.call("zoom_by", 1.25)
	chk(float((s.call("snapshot") as Dictionary)["zoom"]) <= 6.0001, "zoom in stops at the maximum (6.0)")
	s.call("zoom_by", 0.5)
	var o0 := (s.call("snapshot") as Dictionary)["origin"] as Vector2
	s.call("pan_by", Vector2(-120, -80))
	await frames(2)
	var o1 := (s.call("snapshot") as Dictionary)["origin"] as Vector2
	chk(o1.distance_to(o0) > 20.0, "pan_by moves the map (%s -> %s)" % [str(o0), str(o1)])
	s.call("pan_by", Vector2(-99999, -99999))
	await frames(2)
	var o2 := (s.call("snapshot") as Dictionary)["origin"] as Vector2
	var fsz := (s.call("snapshot") as Dictionary)["frame"] as Vector2
	chk(o2.x >= -99999.0 and o2.x > fsz.x - 5000.0, "panning far away is clamped (origin %s)" % str(o2))
	# WASD held pans (the keys are polled)
	s.call("center_on_you")
	await frames(2)
	var o3 := (s.call("snapshot") as Dictionary)["origin"] as Vector2
	Input.parse_input_event(_key_ev(KEY_D, true))
	await frames(8)
	Input.parse_input_event(_key_ev(KEY_D, false))
	var o4 := (s.call("snapshot") as Dictionary)["origin"] as Vector2
	chk(o4 != o3, "holding D pans the map (%s -> %s)" % [str(o3), str(o4)])
	# mouse wheel + drag on the frame
	var frame := s.call("button_node", "frame") as Control
	var zw0 := float((s.call("snapshot") as Dictionary)["zoom"])
	var wheel := InputEventMouseButton.new()
	wheel.button_index = MOUSE_BUTTON_WHEEL_UP
	wheel.pressed = true
	wheel.position = frame.get_global_rect().get_center()
	wheel.global_position = wheel.position
	sub.push_input(wheel, false)
	await frames(2)
	chk(float((s.call("snapshot") as Dictionary)["zoom"]) > zw0 or zw0 >= 5.99, "mouse wheel up zooms in")
	var before := (s.call("snapshot") as Dictionary)["origin"] as Vector2
	var fc := frame.get_global_rect().get_center()
	for pressed in [true, false]:
		var d := InputEventMouseButton.new()
		d.button_index = MOUSE_BUTTON_LEFT
		d.pressed = pressed
		d.position = fc
		d.global_position = fc
		sub.push_input(d, false)
		if pressed:
			var mm := InputEventMouseMotion.new()
			mm.position = fc + Vector2(-60, -40)
			mm.global_position = mm.position
			mm.relative = Vector2(-60, -40)
			mm.button_mask = MOUSE_BUTTON_MASK_LEFT
			sub.push_input(mm, false)
		await frames(1)
	var after := (s.call("snapshot") as Dictionary)["origin"] as Vector2
	chk(after != before, "dragging with the mouse pans the map (%s -> %s)" % [str(before), str(after)])
	s.call("close_map")
	sub.queue_free()
	await frames(2)


func Model_px(vd: Dictionary) -> Vector2:
	return Vector2((float((vd["bounds"] as Array)[2]) - float((vd["bounds"] as Array)[0])) * float(vd["ppm"]), (float((vd["bounds"] as Array)[3]) - float((vd["bounds"] as Array)[1])) * float(vd["ppm"]))


func _key_ev(code: int, pressed: bool) -> InputEventKey:
	var e := InputEventKey.new()
	e.keycode = code as Key
	e.physical_keycode = code as Key
	e.pressed = pressed
	return e


func _sub(w: int, h: int) -> SubViewport:
	var sub := SubViewport.new()
	sub.size = Vector2i(w, h)
	sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(sub)
	return sub


func _mouse() -> void:
	var sub := _sub(1366, 876)
	var s := make(sub)
	await frames(3)
	# a real click on the corner button
	var ob := s.call("button_node", "open") as Button
	await click(sub, ob.get_global_rect().get_center())
	await frames(2)
	chk(bool(s.call("is_open")), "a real mouse click on the MAP button opens the map (button at %s)" % str(ob.get_global_rect()))
	await frames(2)
	# a real click on Close
	var cb := s.call("button_node", "close") as Button
	await click(sub, cb.get_global_rect().get_center())
	chk(not bool(s.call("is_open")), "a real mouse click on Close closes it (button at %s)" % str(cb.get_global_rect()))
	# markers and rows: select, track
	tracks.clear()
	await key(sub, KEY_M)
	await frames(3)
	await key(sub, KEY_1)
	await frames(2)
	var mpos := s.call("marker_screen_pos", "fish_market") as Vector2
	var frame_r := (s.call("button_node", "frame") as Control).get_global_rect()
	chk(frame_r.has_point(mpos), "the Fish Market marker is inside the map frame (%s in %s)" % [str(mpos), str(frame_r)])
	await click(sub, mpos)
	await frames(2)
	chk(str((s.call("snapshot") as Dictionary)["selected"]) == "fish_market", "clicking a marker selects it")
	chk(str((s.get_node("%DetailName") as Label).text).contains("Fish"), "the detail panel names it: " + (s.get_node("%DetailName") as Label).text)
	var tbtn := s.call("button_node", "track") as Button
	chk(not tbtn.disabled and tbtn.text.contains("Track"), "the Track button is enabled: " + tbtn.text)
	await click(sub, tbtn.get_global_rect().get_center())
	await frames(1)
	chk(tracks == ["fish_market"], "the Track button asks the game to track the selected place (%s)" % str(tracks))
	mock["tracked"] = "fish_market"
	await frames(20)
	chk(str((s.get_node("%TrackButton") as Button).text).contains("Stop"), "once tracked the button offers to stop: " + (s.get_node("%TrackButton") as Button).text)
	await key(sub, KEY_C)
	await frames(1)
	chk(tracks.back() == "", "C asks the game to clear tracking")
	mock["tracked"] = ""
	await key(sub, KEY_DOWN)
	await key(sub, KEY_DOWN)
	chk(str((s.call("snapshot") as Dictionary)["selected"]) != "fish_market", "Down moves the selection in the list")
	await key(sub, KEY_ENTER)
	chk(tracks.size() >= 3, "Enter asks to track the selected row")
	mock["tracked"] = ""
	s.call("close_map")
	sub.queue_free()
	await frames(2)


func _states() -> void:
	# at sea and docked: the right first tab, You are the ship; ashore: You are the walker; off-map hint
	var sub := _sub(1280, 720)
	var s := make(sub)
	await frames(3)
	mock["ashore"] = false
	mock["docked"] = false
	mock["ship"] = Vector2(-100.0, 140.0)
	await key(sub, KEY_M)
	await frames(3)
	chk(int(s.get("tab")) == 2, "AT SEA: opens on the Sea tab (%d)" % int(s.get("tab")))
	chk((s.get_node("%Picture") as TextureRect).texture != null, "AT SEA: the sea picture is shown")
	chk(not str(s.call("rows_text")).contains("You\n"), "the player is not a row in the list")
	await key(sub, KEY_1)
	await frames(3)
	chk(str((s.get_node("%TabHint") as Label).text).contains("not on this map"), "the City tab says you are not on it when you are at sea: " + (s.get_node("%TabHint") as Label).text)
	var snap := s.call("snapshot") as Dictionary
	chk(bool(snap["picture"]), "the City picture shows even when you are elsewhere")
	await key(sub, KEY_M)
	mock["docked"] = true
	mock["ship"] = Vector2(21.4, 21.0)
	await key(sub, KEY_M)
	await frames(3)
	chk(int(s.get("tab")) == 0, "AT THE PIER (docked): opens on the City tab (%d)" % int(s.get("tab")))
	await key(sub, KEY_M)
	mock["ashore"] = true
	mock["player"] = Vector2(16, -66)
	await key(sub, KEY_M)
	await frames(3)
	chk(int(s.get("tab")) == 0, "ASHORE: opens on the City tab")
	var m := s.call("marker_screen_pos", "__you") as Vector2
	chk(m.x > 0.0 and (s.call("button_node", "frame") as Control).get_global_rect().has_point(m), "ASHORE: the YOU marker is on the City map at %s" % str(m))
	var ship_m := s.call("marker_screen_pos", "ship") as Vector2
	chk(ship_m.x > 0.0, "ASHORE: the ship marker exists too")
	# the live state moves the marker without re-opening
	mock["player"] = Vector2(-60, -20)
	await frames(30)
	var m2 := s.call("marker_screen_pos", "__you") as Vector2
	chk(m2.distance_to(m) > 5.0, "the YOU marker follows the live position (%s -> %s)" % [str(m), str(m2)])
	await key(sub, KEY_M)
	sub.queue_free()
	await frames(2)


func _errors() -> void:
	var sub := _sub(1280, 720)
	# (a) no provider at all
	var s: Node = (load(SCENE) as PackedScene).instantiate()
	s.set("notify", func(txt: String) -> void: toasts.append(txt))
	sub.add_child(s)
	await frames(3)
	await key(sub, KEY_M)
	await frames(3)
	chk(bool(s.call("is_open")), "NO PROVIDER: the map still opens")
	chk((s.get_node("%Notice") as Label).visible and str((s.get_node("%Notice") as Label).text).contains("place list"), "NO PROVIDER: a visible notice says so: " + (s.get_node("%Notice") as Label).text)
	chk((s.get_node("%Picture") as TextureRect).texture != null, "NO PROVIDER: the picture is still shown")
	await key(sub, KEY_ESCAPE)
	chk(not bool(s.call("is_open")), "NO PROVIDER: Esc closes it")
	# (b) provider returns junk
	s.set("provider", func() -> Variant: return 42)
	await key(sub, KEY_M)
	await frames(2)
	chk(bool(s.call("is_open")) and (s.get_node("%Notice") as Label).visible, "BAD PROVIDER (returns 42): opens with a notice")
	await key(sub, KEY_M)
	s.set("provider", func() -> Dictionary: return {"entries": [{"id": "x"}, 5], "player": "no"})
	await key(sub, KEY_M)
	await frames(2)
	chk(bool(s.call("is_open")) and str((s.get_node("%Notice") as Label).text).contains("skipped"), "BAD ENTRIES: opens, drops them, says so: " + (s.get_node("%Notice") as Label).text)
	await key(sub, KEY_M)
	# (c) a missing picture
	var views: Array = s.get("views")
	(views[0] as Dictionary)["file"] = "no_such_picture.png"
	s.set("provider", provider)
	await key(sub, KEY_M)
	await frames(2)
	chk(bool(s.call("is_open")) and str((s.get_node("%Notice") as Label).text).contains("could not be loaded"), "MISSING PICTURE: opens, notice names it: " + (s.get_node("%Notice") as Label).text)
	chk(int((s.call("snapshot") as Dictionary)["markers"]) >= 2, "MISSING PICTURE: markers are still drawn")
	await key(sub, KEY_M)
	# (d) can_open refuses: no open, the reason reaches the player
	toasts.clear()
	s.set("can_open", func() -> String: return "Finish the conversation first.")
	await key(sub, KEY_M)
	chk(not bool(s.call("is_open")) and toasts == ["Finish the conversation first."], "BLOCKED (dialogue): the map stays closed and the reason is shown (%s)" % str(toasts))
	(s.call("button_node", "open") as Button).pressed.emit()
	chk(toasts.size() == 2, "BLOCKED: the button explains too")
	s.set("can_open", Callable())
	s.queue_free()
	await frames(2)
	# (e) the scene itself is damaged: a node is missing
	var d: Node = (load(SCENE) as PackedScene).instantiate()
	d.get_node("%MapFrame").free()
	d.set("notify", func(txt: String) -> void: toasts.append(txt))
	sub.add_child(d)
	await frames(3)
	chk(str(d.get("init_error")).contains("MapFrame"), "DAMAGED SCENE: init_error names the missing node (%s)" % str(d.get("init_error")))
	await key(sub, KEY_M)
	chk(bool(d.call("is_open")) and d.get_node_or_null("EmergencyMap") != null, "DAMAGED SCENE: M shows the emergency window instead of doing nothing")
	await key(sub, KEY_ESCAPE)
	chk(not bool(d.call("is_open")) and d.get_node_or_null("EmergencyMap") == null, "DAMAGED SCENE: Esc closes the emergency window")
	await key(sub, KEY_M)
	var eb := d.get_node("EmergencyMap").find_children("*", "Button", true, false)
	chk(eb.size() == 1, "DAMAGED SCENE: the emergency window has a Close button")
	(eb[0] as Button).pressed.emit()
	chk(not bool(d.call("is_open")), "DAMAGED SCENE: the Close button closes it")
	chk(str(d.call("diagnostics")).contains("SCENE DAMAGED"), "diagnostics() reports the damage")
	d.queue_free()
	sub.queue_free()
	await frames(2)


func _layout_sizes() -> void:
	# the whole window at several sizes: nothing outside the screen, the picture never reaches the tab row or the Close button
	for sz in [Vector2i(1366, 876), Vector2i(1280, 720), Vector2i(1024, 768), Vector2i(800, 600), Vector2i(1920, 1080), Vector2i(2560, 1440)]:
		var sub := _sub(sz.x, sz.y)
		var s := make(sub)
		mock["ashore"] = true
		await frames(3)
		await key(sub, KEY_M)
		await frames(4)
		for ti in 3:
			await key(sub, KEY_1 + ti)
			await frames(3)
			var v := s.call("verify_layout") as Dictionary
			chk(bool(v["ok"]), "%dx%d tab %d: layout valid %s" % [sz.x, sz.y, ti, str(v["why"])])
			var frame := (s.call("button_node", "frame") as Control).get_global_rect()
			var close_r := (s.call("button_node", "close") as Control).get_global_rect()
			var tabs_r := (s.call("button_node", "tabs") as Control).get_global_rect()
			var panel_r := (s.call("button_node", "panel") as Control).get_global_rect()
			chk(not frame.intersects(close_r) and not frame.intersects(tabs_r), "%dx%d tab %d: the map frame %s does not cover the tabs %s or Close %s" % [sz.x, sz.y, ti, str(frame), str(tabs_r), str(close_r)])
			chk(Rect2(Vector2.ZERO, Vector2(sz)).encloses(panel_r), "%dx%d: the panel %s is inside the screen" % [sz.x, sz.y, str(panel_r)])
			var pic := (s.get_node("%Picture") as Control).get_global_rect().intersection(frame)
			chk(pic.size.x > 50.0 and pic.size.y > 50.0, "%dx%d tab %d: the picture is visible inside the frame (%s)" % [sz.x, sz.y, ti, str(pic.size)])
			var snap := s.call("snapshot") as Dictionary
			chk(float(snap["frame"].x) > 300.0 and float(snap["frame"].y) > 150.0, "%dx%d: the map frame is %s" % [sz.x, sz.y, str(snap["frame"])])
		# resizing while open: the layout follows
		sub.size = Vector2i(sz.x - 100, sz.y - 60)
		await frames(4)
		var v2 := s.call("verify_layout") as Dictionary
		chk(bool(v2["ok"]), "%dx%d resized to %dx%d while open: layout valid %s" % [sz.x, sz.y, sz.x - 100, sz.y - 60, str(v2["why"])])
		s.call("close_map")
		sub.queue_free()
		await frames(2)
