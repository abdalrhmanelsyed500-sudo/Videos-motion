extends SceneTree
## Regression for the r4 blocker "M does not open the map": sends REAL key events through the viewport (like the engine does for the
## keyboard) and asserts that the toggle changes what is visible, in the City, Island and Sea views, at sea and ashore, with a Latin and
## an Arabic layout, and that the map's tab row and sidebar stay inside their panel.
##   godot --headless --fixed-fps 60 --path game --script res://tests/map_key.gd        (prints MAPKEY n checks, m failed)
## Headless has no renderer and a 0 x 0 window, so this proves the logic and the control tree, not the look; the real-renderer run of the
## same keys is tools/godot_browser/scenarios/map_*.mjs.
var checks := 0
var fails := 0
var scene: Node
var port: Node
var mp: Control


func chk(cond: bool, msg: String) -> void:
	checks += 1
	if not cond:
		fails += 1
		print("  FAIL: ", msg)


func frames(n: int) -> void:
	for i in n:
		await process_frame


## One key press through the viewport. `keycode` is what the layout produced, `physical` the key's place on the keyboard.
func key(keycode: int, physical: int = -1, shift: bool = false, echo: bool = false) -> void:
	var ev := InputEventKey.new()
	ev.keycode = keycode as Key
	ev.physical_keycode = (keycode if physical < 0 else physical) as Key
	ev.shift_pressed = shift
	ev.echo = echo
	ev.pressed = true
	root.push_input(ev, false)
	await process_frame
	var up := InputEventKey.new()
	up.keycode = ev.keycode
	up.physical_keycode = ev.physical_keycode
	up.pressed = false
	root.push_input(up, false)
	await process_frame


func shown() -> bool:
	return mp.is_visible_in_tree() and bool(mp.call("is_shown")) and bool(port.call("modal"))


func _initialize() -> void:
	scene = (load("res://h2d/h2d0.tscn") as PackedScene).instantiate()
	root.add_child(scene)
	_play()


func _play() -> void:
	await frames(10)
	port = scene.get("_port")
	chk(port != null and bool(port.get("enabled")), "the port controller exists and is enabled")
	if port == null:
		quit(1)
		return
	mp = (port.get("ui") as Node).get("map")
	chk(mp != null and not mp.visible, "the map starts hidden")
	var views: Array = mp.get("views")
	var ids: Array = []
	for v in views:
		ids.append(str((v as Dictionary)["id"]))
	chk(ids == ["city", "island", "sea"], "the three views are city, island, sea (%s)" % str(ids))
	# ---- at sea: M opens, M closes, Esc closes, the toggle really changes visibility, Arabic layout, Shift+M, key repeat ------------
	await key(KEY_M)
	chk(shown(), "AT SEA: M opens the map (visible + laid out + modal)")
	chk(int(mp.get("tab")) == 2, "AT SEA: it opens on the Sea view (tab %d)" % int(mp.get("tab")))
	await key(KEY_M)
	chk(not mp.visible and not bool(port.call("modal")), "AT SEA: M again closes it")
	await key(KEY_M)
	await key(KEY_ESCAPE)
	chk(not mp.visible and not bool(port.call("modal")), "AT SEA: Esc closes it")
	await key(0x0629, KEY_M)      # Arabic layout: the character is not Latin, the physical key is M
	chk(shown(), "ARABIC LAYOUT: the physical M key opens the map")
	await key(0x0629, KEY_M)
	chk(not mp.visible, "ARABIC LAYOUT: and closes it again")
	await key(KEY_M, KEY_M, false, true)
	chk(not mp.visible, "a key-repeat (echo) event does not open it")
	var mode_before: int = int((scene.get("_v3") as Object).get("motion_mode"))
	await key(KEY_M, KEY_M, true)
	chk(not mp.visible, "Shift+M does not open the map (it cycles the ship motion)")
	chk(int((scene.get("_v3") as Object).get("motion_mode")) != mode_before, "Shift+M still reaches the motion toggle")
	chk(String(port.get("last_key")).contains("keycode"), "the last-key diagnostic is filled: %s" % str(port.get("last_key")))
	# ---- every view opens, with its tab, markers and a size ------------------------------------------------------------------------
	await key(KEY_M)
	for i in 3:
		await key(KEY_1 + i)
		await frames(2)
		chk(shown() and int(mp.get("tab")) == i, "view %s: visible, laid out, selected" % ids[i])
		var p := mp.get_node("MapPanel") as Control
		chk(p.size.x > 1000.0 and p.size.y > 600.0, "view %s: the panel has a real size %s" % [ids[i], str(p.size)])
		chk((mp.get("_markers") as Dictionary).size() >= 2, "view %s: markers present (%d)" % [ids[i], (mp.get("_markers") as Dictionary).size()])
		chk((mp.get("_tex") as TextureRect).visible, "view %s: the map picture control is visible" % ids[i])
	_layout_checks()
	await key(KEY_M)
	chk(not mp.visible, "closed again after the view tour")
	# ---- ashore: M opens on the City view -------------------------------------------------------------------------------------------
	var land: Dictionary = (scene.get("_v3") as Object).call("land_world").meta["land"]
	(scene.get("_walker") as RefCounted).call("disembark", land)
	await frames(3)
	await key(KEY_M)
	chk(shown(), "ASHORE: M opens the map")
	chk(int(mp.get("tab")) == 0, "ASHORE: it opens on the City view (tab %d)" % int(mp.get("tab")))
	await key(KEY_M)
	chk(not mp.visible, "ASHORE: M closes it")
	await key(0x0629, KEY_M)
	chk(shown(), "ASHORE + ARABIC LAYOUT: the physical M key opens the map")
	await key(KEY_ESCAPE)
	chk(not mp.visible and not bool(port.call("modal")), "ASHORE: Esc closes it and the game is not left modal")
	# ---- a failed open must never leave the game paused in an invisible map -----------------------------------------------------------
	mp.set("views", [])
	await key(KEY_M)
	chk(not bool(port.call("modal")), "a map that cannot open leaves no modal state behind")
	chk(not (scene.get("_state").clock.pause_reasons() as Array).has("port"), "...and does not leave the clock paused")
	print("MAPKEY %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)


## Tab row and sidebar must fit inside the panel (the r4 screenshots showed the tab labels cut by the map picture and the sidebar
## wider than its column).
func _layout_checks() -> void:
	var tabs := mp.get_node("MapPanel/Holder/Tabs") as Control
	var vp := mp.get_node("MapPanel/Holder/MapViewport") as Control
	var tab_h := 0.0
	for b in (mp.get("_tab_btns") as Array):
		tab_h = maxf(tab_h, (b as Control).get_combined_minimum_size().y)
	chk(tabs.position.y + tab_h <= vp.position.y, "the tab row (y %.0f + %.0f high) ends above the map picture (y %.0f)" % [tabs.position.y, tab_h, vp.position.y])
	var panel := mp.get_node("MapPanel") as Control
	var side := mp.get_node("MapPanel/Holder/Sidebar") as Control
	var widest := 0.0
	for r in (mp.get("_row_btns") as Dictionary).values():
		widest = maxf(widest, (r as Control).get_combined_minimum_size().x)
	chk(widest <= 280.0, "no sidebar row asks for more than 280 px (widest %.0f)" % widest)
	chk(side.position.x + 290.0 + 18.0 <= panel.size.x, "the sidebar column (x %.0f + 290) fits inside the panel (%.0f wide)" % [side.position.x, panel.size.x])
	chk(vp.position.y + vp.size.y + 14.0 <= panel.size.y, "the map picture ends inside the panel")
