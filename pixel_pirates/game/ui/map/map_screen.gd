extends CanvasLayer
# gdlint: disable=class-definitions-order
## THE map. One self-contained scene (map_screen.tscn: a CanvasLayer holding plain Controls and containers) that replaces the old
## map_ui.gd + port_game routing. Design rules, each one a lesson from the old map that did not open on the player's PC:
##  * ONE way in: the Input Map action "open_map" (physical M, plus the key labelled M for AZERTY-like layouts) is read in
##    _input of this node only, so a focused control, a dialogue or the keyboard layout cannot swallow it, and nothing else in the
##    game opens or closes the map. The "MAP [M]" button in the corner calls the same request_open().
##  * No dependence on the port controller, the walker or any game rule: the map loads its own views (map_views.json) and asks an
##    optional `provider` Callable for live entries. If the provider or the data is missing the map still opens, with a red notice.
##  * Layout is containers (nothing is positioned in pixels except the picture and the markers INSIDE the clipped map frame), so the
##    picture can never cover the tabs or the Close button, at any window size.
##  * Opening never edits game state. The host listens to `opened` / `closed` (pause on open, resume on close, by reason) and every
##    path out (Esc, M, the Close button, the node leaving the tree) emits `closed` exactly once.
##  * A failure is shown, never swallowed: a notice in the window, a toast through `notify`, the line in diagnostics().
const Model := preload("res://ui/map/map_model.gd")
const KeyUtil := preload("res://h2d/key_util.gd")
const ACTION := &"open_map"
const TEX_DIR := "res://h2d/art/"
const DIAG_FILE := "user://map_diagnostics.txt"
const REFRESH_S := 0.25
const ZOOM_STEP := 1.25
const ZOOM_MAX := 6.0
const PAN_PX_PER_S := 650.0
const DOT := 26.0
const KIND_STYLE := {   # kind -> [letter, fill colour, ring colour]
	"recruit": ["R", Color(0.98, 0.80, 0.25), Color(0.20, 0.12, 0.02)], "market": ["F", Color(0.35, 0.78, 0.88), Color(0.04, 0.2, 0.28)],
	"ship": ["S", Color(0.40, 0.58, 1.0), Color(0.04, 0.08, 0.3)], "player": ["YOU", Color(1.0, 0.35, 0.30), Color(0.3, 0.02, 0.02)],
	"tavern": ["T", Color(0.92, 0.55, 0.28), Color(0.3, 0.12, 0.02)], "customs": ["C", Color(0.78, 0.70, 0.52), Color(0.2, 0.15, 0.05)],
	"palace": ["G", Color(0.80, 0.50, 0.92), Color(0.2, 0.05, 0.3)], "square": ["M", Color(0.70, 0.86, 0.50), Color(0.1, 0.2, 0.04)],
	"notice": ["N", Color(0.95, 0.92, 0.80), Color(0.25, 0.2, 0.1)], "light": ["L", Color(1.0, 0.95, 0.60), Color(0.3, 0.25, 0.02)],
	"ground": ["~", Color(0.5, 0.85, 1.0), Color(0.04, 0.2, 0.3)], "place": ["", Color(0.85, 0.80, 0.70), Color(0.2, 0.15, 0.1)],
	"pier": ["P", Color(0.60, 0.72, 0.95), Color(0.05, 0.1, 0.25)], "warehouse": ["W", Color(0.75, 0.62, 0.45), Color(0.2, 0.12, 0.05)],
}
const GOLD := Color(0.98, 0.80, 0.25)
const CREAM := Color(1.0, 0.97, 0.88)
const INK := Color(0.05, 0.08, 0.1)

signal opened(tab: int)
signal closed()
signal tab_changed(tab: int)
signal track_requested(id: String)

## Live data: Callable() -> Dictionary {entries, tracked, player, ship, ship_heading, ashore, docked, rings}. Optional.
var provider: Callable
## Callable() -> String: "" when the map may open now, otherwise the reason (a dialogue is open ...). Optional.
var can_open: Callable
## Callable(text: String): shows a message to the player (a toast). Optional.
var notify: Callable
var show_button := true         ## the corner "MAP [M]" button
var views: Array = []
var tab := -1
var init_error := ""            ## non-empty: the scene is damaged; open() then shows the emergency window instead
var last_error := ""
var open_count := 0
var fail_count := 0
var tracked := ""

var _open := false
var _opened_frame := -1
var _serial := 0
var _state: Dictionary = {"entries": [], "tracked": "", "player": Vector2.ZERO, "ship": Vector2.ZERO, "ship_heading": 0.0, "ashore": false, "docked": false, "rings": []}
var _notes: Dictionary = {}
var _tex_cache: Dictionary = {}
var _map_px := Vector2(1, 1)
var _zoom := 1.0
var _fit_z := 1.0
var _origin := Vector2.ZERO
var _need_init := false
var _dirty := true
var _drag := false
var _t := 0.0
var _refresh_t := 0.0
var _sel := ""
var _sig := ""
var _markers: Dictionary = {}
var _rows: Dictionary = {}
var _tab_btns: Array = []
var _vis_entries: Array = []
var _emergency: Control = null

var _overlay: Control
var _panel: PanelContainer
var _title: Label
var _tab_box: HBoxContainer
var _tab_hint: Label
var _zoom_info: Label
var _notice: Label
var _frame: Control
var _picture: TextureRect
var _rings: Control
var _marker_box: Control
var _scale_lbl: Label
var _row_box: VBoxContainer
var _detail: PanelContainer
var _detail_name: Label
var _detail_text: Label
var _track_btn: Button
var _open_btn: Button
var _close_btn: Button
var _footer: Label
var _zoom_in: Button
var _zoom_out: Button
var _fit_btn: Button


# ---- Input Map -------------------------------------------------------------------------------------------------------------
## Makes sure the action exists with its two keys (project.godot declares them too; this repairs a project file that lost them).
static func ensure_action() -> void:
	if not InputMap.has_action(ACTION):
		InputMap.add_action(ACTION)
	var has_phys := false
	var has_label := false
	for e in InputMap.action_get_events(ACTION):
		var ke := e as InputEventKey
		if ke == null or ke.shift_pressed or ke.ctrl_pressed or ke.alt_pressed or ke.meta_pressed:
			continue
		if ke.physical_keycode == KEY_M and ke.keycode == KEY_NONE:
			has_phys = true
		if ke.keycode == KEY_M:
			has_label = true
	if not has_phys:
		var p := InputEventKey.new()
		p.physical_keycode = KEY_M
		InputMap.action_add_event(ACTION, p)
	if not has_label:
		var l := InputEventKey.new()
		l.keycode = KEY_M
		InputMap.action_add_event(ACTION, l)


# ---- set-up ------------------------------------------------------------------------------------------------------------------
func _enter_tree() -> void:
	ensure_action()


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_process(false)
	_bind_nodes()
	var vr := Model.load_views()
	views = vr["views"] as Array
	if str(vr["error"]) != "":
		_notes["views"] = str(vr["error"])
		push_warning("MapScreen: " + str(vr["error"]))
	if init_error == "":
		_skin()
		_build_tabs()
		_wire()
		_overlay.visible = false
		get_viewport().size_changed.connect(_fit)
	else:
		push_error("MapScreen: " + init_error)
		_write_diag()
	if _open_btn != null:
		_open_btn.visible = show_button


func _find(path: String) -> Node:
	var n := get_node_or_null(path)
	if n == null and init_error == "":
		init_error = "map_screen.tscn lacks the node '%s'" % path
	return n


func _bind_nodes() -> void:
	_open_btn = _find("%OpenButton") as Button
	_overlay = _find("%Overlay") as Control
	_panel = _find("%Panel") as PanelContainer
	_title = _find("%Title") as Label
	_close_btn = _find("%CloseButton") as Button
	_tab_box = _find("%Tabs") as HBoxContainer
	_tab_hint = _find("%TabHint") as Label
	_zoom_info = _find("%ZoomInfo") as Label
	_notice = _find("%Notice") as Label
	_frame = _find("%MapFrame") as Control
	_picture = _find("%Picture") as TextureRect
	_rings = _find("%Rings") as Control
	_marker_box = _find("%Markers") as Control
	_scale_lbl = _find("%ScaleLabel") as Label
	_row_box = _find("%Rows") as VBoxContainer
	_detail = _find("%Detail") as PanelContainer
	_detail_name = _find("%DetailName") as Label
	_detail_text = _find("%DetailText") as Label
	_track_btn = _find("%TrackButton") as Button
	_footer = _find("%Footer") as Label
	_zoom_in = _find("%ZoomIn") as Button
	_zoom_out = _find("%ZoomOut") as Button
	_fit_btn = _find("%FitButton") as Button
	for b in [_open_btn, _close_btn, _track_btn]:
		if b != null:
			(b as Button).focus_mode = Control.FOCUS_NONE
	if init_error == "":
		for c in [_overlay, _panel, _title, _tab_box, _frame, _picture, _rings, _marker_box, _row_box, _track_btn, _close_btn, _open_btn, _tab_hint, _zoom_info, _notice, _scale_lbl, _detail, _detail_name, _detail_text, _zoom_in, _zoom_out, _fit_btn]:
			if c == null:
				init_error = "map_screen.tscn: a required node has the wrong type"


func _wire() -> void:
	_open_btn.pressed.connect(request_open.bind(-1))
	_close_btn.pressed.connect(close_map)
	_track_btn.pressed.connect(_on_track_pressed)
	_zoom_in.pressed.connect(zoom_by.bind(ZOOM_STEP))
	_zoom_out.pressed.connect(zoom_by.bind(1.0 / ZOOM_STEP))
	_fit_btn.pressed.connect(center_on_you)
	_frame.gui_input.connect(_on_frame_input)
	_frame.resized.connect(_on_frame_resized)
	_rings.draw.connect(_draw_overlay)


func _skin() -> void:
	var ps := _box(Color(0.12, 0.08, 0.05, 0.98), GOLD.darkened(0.25), 3, 8, 12)
	_panel.add_theme_stylebox_override("panel", ps)
	_detail.add_theme_stylebox_override("panel", _box(Color(0.18, 0.12, 0.07, 1.0), GOLD.darkened(0.5), 2, 6, 8))
	_title.add_theme_color_override("font_color", GOLD)
	_title.add_theme_color_override("font_outline_color", INK)
	_title.add_theme_constant_override("outline_size", 4)
	_tab_hint.add_theme_color_override("font_color", Color(0.82, 0.76, 0.64))
	_zoom_info.add_theme_color_override("font_color", CREAM)
	_skin_button(_close_btn, Color(0.55, 0.12, 0.10), Color(1.0, 0.75, 0.6), CREAM)
	_skin_button(_track_btn, Color(0.40, 0.28, 0.08), GOLD, CREAM)
	for zb in [_zoom_in, _zoom_out, _fit_btn]:
		_skin_button(zb as Button, Color(0.26, 0.18, 0.10), GOLD.darkened(0.3), CREAM)
	_skin_button(_open_btn, Color(0.22, 0.15, 0.08, 0.95), GOLD, CREAM)
	_open_btn.add_theme_font_size_override("font_size", 16)


static func _box(fill: Color, border: Color, bw: int, radius: int, pad: int) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = fill
	sb.border_color = border
	sb.set_border_width_all(bw)
	sb.set_corner_radius_all(radius)
	sb.set_content_margin_all(float(pad))
	return sb


## Same look in every state, brighter on hover and when pressed; text colours set for every state.
static func _skin_button(b: Button, fill: Color, border: Color, text: Color) -> void:
	b.add_theme_stylebox_override("normal", _box(fill, border, 2, 6, 6))
	b.add_theme_stylebox_override("hover", _box(fill.lightened(0.18), border, 2, 6, 6))
	b.add_theme_stylebox_override("pressed", _box(fill.lightened(0.32), GOLD, 3, 6, 6))
	b.add_theme_stylebox_override("hover_pressed", _box(fill.lightened(0.40), GOLD, 3, 6, 6))
	b.add_theme_stylebox_override("disabled", _box(fill.darkened(0.45), border.darkened(0.5), 2, 6, 6))
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_hover_pressed_color", "font_focus_color"]:
		b.add_theme_color_override(c, text)
	b.add_theme_color_override("font_disabled_color", text.darkened(0.45))


func _build_tabs() -> void:
	for b in _tab_btns:
		(b as Node).queue_free()
	_tab_btns.clear()
	for i in views.size():
		var b := Button.new()
		b.name = "Tab_" + str((views[i] as Dictionary)["id"])
		b.text = "%d  %s" % [i + 1, str((views[i] as Dictionary)["tab"])]
		b.toggle_mode = true
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(100, 36)
		b.add_theme_font_size_override("font_size", 17)
		_skin_button(b, Color(0.26, 0.18, 0.10), GOLD.darkened(0.3), CREAM)
		b.pressed.connect(set_tab.bind(i))
		_tab_box.add_child(b)
		_tab_btns.append(b)


# ---- public API --------------------------------------------------------------------------------------------------------------
func is_open() -> bool:
	return _open


## The only entry point of the hotkey and the button. Returns true when the map is open afterwards; says why when it is not.
func request_open(first_tab: int = -1) -> bool:
	if _open:
		if first_tab >= 0:
			set_tab(first_tab)
		return true
	if can_open.is_valid():
		var why := str(can_open.call())
		if why != "":
			_say(why)
			return false
	return open_map(first_tab)


func open_map(first_tab: int = -1) -> bool:
	if _open:
		return true
	if init_error != "":
		return _open_emergency(init_error)
	_fit()
	_ensure_views()
	_fetch_state()
	if views.is_empty():
		return _fail("there are no map views")
	var t := first_tab if first_tab >= 0 else Model.default_tab(_state, views)
	_open = true
	_opened_frame = Engine.get_process_frames()
	_serial += 1
	_overlay.visible = true
	_open_btn.visible = false
	var vp := get_viewport()
	if vp != null:
		vp.gui_release_focus()
	tab = -1
	_sig = ""
	_sel = ""
	_refresh_t = REFRESH_S
	set_process(true)
	set_tab(clampi(t, 0, views.size() - 1))
	_update_notice()
	open_count += 1
	opened.emit(tab)
	_post_open_check(_serial)
	return true


## Views changed after loading (or were damaged): never open on bad data, fall back to the built-in three and say so.
func _ensure_views() -> void:
	var bad := Model.view_problems(views)
	if bad.is_empty():
		if str(_notes.get("views", "")).begins_with("Map views are damaged"):
			_notes.erase("views")
		return
	_notes["views"] = "Map views are damaged (%s): the built-in views are used." % str(bad[0])
	push_warning("MapScreen: " + str(_notes["views"]))
	views = Model.DEFAULT_VIEWS.duplicate(true)
	tab = -1
	_build_tabs()


func close_map() -> void:
	if not _open:
		return
	_open = false
	_drag = false
	set_process(false)
	if _overlay != null:
		_overlay.visible = false
	if _emergency != null:
		_emergency.queue_free()
		_emergency = null
	if _open_btn != null:
		_open_btn.visible = show_button
	var vp := get_viewport()
	if vp != null:
		vp.gui_release_focus()
	closed.emit()


func toggle() -> void:
	if _open:
		close_map()
	else:
		request_open()


func set_tab(i: int) -> void:
	if i < 0 or i >= views.size() or init_error != "":
		return
	if i == tab and not _need_init:
		return
	tab = i
	var v := views[i] as Dictionary
	_title.text = "MAP:  %s" % str(v["title"])
	_picture.texture = null
	var tex := _load_texture(str(v["file"]))
	if tex == null:
		_notes["picture"] = "The map picture '%s' could not be loaded." % str(v["file"])
	else:
		_notes.erase("picture")
		_picture.texture = tex
	_map_px = Model.map_px(v)
	_need_init = true
	_sig = ""
	for j in _tab_btns.size():
		(_tab_btns[j] as Button).set_pressed_no_signal(j == tab)
	_sel = ""
	_sync(true)
	_init_view()
	_update_notice()
	tab_changed.emit(tab)


func set_state(d: Dictionary) -> void:
	var r := Model.normalize_state(d)
	_state = r["state"] as Dictionary
	tracked = str(_state["tracked"])
	if (r["problems"] as Array).is_empty():
		_notes.erase("state")
	else:
		_notes["state"] = "; ".join(PackedStringArray(r["problems"] as Array))
	if _open and tab >= 0:
		_sync(false)
		_update_notice()


func zoom_by(factor: float, pivot: Vector2 = Vector2(-1, -1)) -> void:
	if not _open or tab < 0 or _frame == null:
		return
	var fs := _frame.size
	var pv := pivot if pivot.x >= 0.0 else fs * 0.5
	var nz := clampf(_zoom * factor, _fit_z, ZOOM_MAX)
	_origin = Model.zoom_about(_origin, _zoom, nz, pv)
	_zoom = nz
	_dirty = true


func pan_by(delta_px: Vector2) -> void:
	_origin += delta_px
	_dirty = true


func center_on(world: Vector2) -> void:
	if tab < 0 or _frame == null:
		return
	_origin = Model.origin_centered_on(world, views[tab] as Dictionary, _zoom, _frame.size)
	_dirty = true


func center_on_you() -> void:
	if tab < 0:
		return
	var you := Model.you_at(_state)
	if Model.in_bounds(you, views[tab] as Dictionary):
		center_on(you)
	else:
		var b: Array = (views[tab] as Dictionary)["bounds"]
		center_on(Vector2((float(b[0]) + float(b[2])) * 0.5, (float(b[1]) + float(b[3])) * 0.5))


func select(id: String, centre: bool = false) -> void:
	_sel = id
	for rid in _rows.keys():
		(_rows[rid] as Button).set_pressed_no_signal(str(rid) == _sel)
	_update_detail()
	if centre and _marker_for(id) != null:
		var e := _entry(id)
		center_on(Vector2(float(e["x"]), float(e["z"])))
	_dirty = true


## True when the map is on screen and laid out (call it a frame or two after open). Lists what is wrong in `why`.
func verify_layout() -> Dictionary:
	var why: Array = []
	if not _open:
		why.append("the map is not open")
	elif init_error != "":
		why.append(init_error)
	else:
		var vr := get_viewport().get_visible_rect()
		if not _overlay.visible:
			why.append("overlay hidden")
		if _overlay.size.x < vr.size.x - 1.0 or _overlay.size.y < vr.size.y - 1.0:
			why.append("overlay %s smaller than the screen %s" % [str(_overlay.size), str(vr.size)])
		if _frame.size.x < 100.0 or _frame.size.y < 100.0:
			why.append("map frame is only %s" % str(_frame.size))
		var scr := Rect2(Vector2.ZERO, vr.size)
		for c in [_close_btn, _tab_box, _track_btn]:
			var r := (c as Control).get_global_rect()
			if not scr.encloses(r) or r.size.x < 5.0:
				why.append("%s is outside the screen: %s" % [(c as Control).name, str(r)])
		if tab < 0 or tab >= views.size():
			why.append("no tab selected")
		if _picture.get_global_rect().size.x < 2.0:
			why.append("picture has no size")
	return {"ok": why.is_empty(), "why": why}


func diagnostics() -> String:
	var out := "map: %s, tab %d of %d, opened %d times, failed %d" % ["OPEN" if _open else "closed", tab, views.size(), open_count, fail_count]
	if init_error != "":
		out += " | SCENE DAMAGED: " + init_error
	if last_error != "":
		out += " | last failure: " + last_error
	for k in _notes.keys():
		out += " | %s: %s" % [str(k), str(_notes[k])]
	return out


## Names the facts a bug report needs: sizes, counts, selected tab.
func snapshot() -> Dictionary:
	var shown := 0
	for m in _markers.values():
		if (m as Control).visible:
			shown += 1
	return {"open": _open, "tab": tab, "zoom": _zoom, "fit_zoom": _fit_z, "origin": _origin, "markers": _markers.size(), "markers_in_frame": shown,
			"rows": _rows.size(), "frame": _frame.size if _frame != null else Vector2.ZERO, "overlay": _overlay.size if _overlay != null else Vector2.ZERO,
			"names_shown": _names_shown(), "selected": _sel, "tracked": tracked, "picture": _picture.texture != null if _picture != null else false}


func marker_screen_pos(id: String) -> Vector2:
	var m := _marker_for(id)
	if m == null:
		return Vector2(-1, -1)
	return m.get_global_rect().get_center()


func rows_text() -> Array:
	var out: Array = []
	for b in _rows.values():
		out.append((b as Button).text)
	return out


func button_node(which: String) -> Control:
	match which:
		"open":
			return _open_btn
		"close":
			return _close_btn
		"track":
			return _track_btn
		"tabs":
			return _tab_box
		"frame":
			return _frame
		"panel":
			return _panel
	return null


func tab_button(i: int) -> Button:
	return _tab_btns[i] as Button if i >= 0 and i < _tab_btns.size() else null


# ---- internals ---------------------------------------------------------------------------------------------------------------
func _say(text: String) -> void:
	if notify.is_valid():
		notify.call(text)
	else:
		print("MapScreen: ", text)


func _fail(why: String) -> bool:
	fail_count += 1
	last_error = why
	push_error("MapScreen: could not open: " + why)
	_write_diag()
	if _open:
		close_map()
	_say("The map could not open: %s. (details: user://map_diagnostics.txt)" % why)
	return false


func _write_diag() -> void:
	var f := FileAccess.open(DIAG_FILE, FileAccess.WRITE)
	if f != null:
		f.store_string("%s\nviewport: %s\n" % [diagnostics(), str(get_viewport().get_visible_rect().size) if get_viewport() != null else "?"])
		f.close()


func _fetch_state() -> bool:
	if not provider.is_valid():
		_notes["provider"] = "No live place list is connected, so only the pictures and your position are shown."
		set_state({})
		return false
	_notes.erase("provider")
	var r: Variant = provider.call()
	if r is Dictionary:
		set_state(r as Dictionary)
		return true
	_notes["provider"] = "The place list returned no data."
	set_state({})
	return false


func _fit() -> void:
	if _overlay == null:
		return
	var r := get_viewport().get_visible_rect()
	if r.size.x < 1.0 or r.size.y < 1.0:
		return
	# a hidden Control is not always resized when the window changes (seen with the old dialogue layer), so the size is set by hand
	if _overlay.position != r.position or _overlay.size != r.size:
		_overlay.set_anchors_preset(Control.PRESET_TOP_LEFT)
		_overlay.position = r.position
		_overlay.size = r.size
		var m := _overlay.get_node_or_null("Margin") as Control
		if m != null:
			m.set_anchors_preset(Control.PRESET_TOP_LEFT)
			m.position = Vector2.ZERO
			m.size = r.size
		var d := _overlay.get_node_or_null("Dim") as Control
		if d != null:
			d.set_anchors_preset(Control.PRESET_TOP_LEFT)
			d.position = Vector2.ZERO
			d.size = r.size


func _post_open_check(serial: int) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	if not _open or serial != _serial or init_error != "":
		return
	var v := verify_layout()
	if not bool(v["ok"]):
		_fit()
		await get_tree().process_frame
		v = verify_layout()
		if not bool(v["ok"]):
			_notes["layout"] = "Layout problem: " + "; ".join(PackedStringArray(v["why"] as Array))
			push_warning("MapScreen: " + str(_notes["layout"]))
			_write_diag()
			_update_notice()


func _load_texture(file: String) -> Texture2D:
	var path := TEX_DIR + file
	if _tex_cache.has(path):
		return _tex_cache[path] as Texture2D
	var t: Texture2D = null
	if ResourceLoader.exists(path):
		t = load(path) as Texture2D
	if t == null and FileAccess.file_exists(path):
		var img := Image.load_from_file(path)
		if img != null and not img.is_empty():
			t = ImageTexture.create_from_image(img)
	_tex_cache[path] = t
	return t


func _update_notice() -> void:
	if _notice == null:
		return
	var parts: Array = []
	for k in _notes.keys():
		parts.append(str(_notes[k]))
	_notice.text = "  |  ".join(PackedStringArray(parts))
	_notice.visible = not parts.is_empty()


func _entry(id: String) -> Dictionary:
	for e in _vis_entries:
		if str((e as Dictionary)["id"]) == id:
			return e as Dictionary
	for e in (_state["entries"] as Array):
		if str((e as Dictionary)["id"]) == id:
			return e as Dictionary
	return {}


func _marker_for(id: String) -> Control:
	return _markers.get(id) as Control


func _names_shown() -> int:
	var n := 0
	for m in _markers.values():
		var l := (m as Control).get_node_or_null("Name") as Control
		if l != null and l.visible and (m as Control).visible:
			n += 1
	return n


## Rebuilds the markers and the list when the set of places on this tab changed (or when forced), otherwise only refreshes texts.
func _sync(force: bool) -> void:
	if tab < 0 or tab >= views.size():
		return
	var vid := str((views[tab] as Dictionary)["id"])
	var want: Array = []
	var ids: Array = []
	var ashore := bool(_state.get("ashore", false))
	for e in Model.entries_for_view(_state["entries"] as Array, vid):
		var ed := e as Dictionary
		if str(ed["kind"]) == "player":
			continue          # the player is drawn from `player` / `ship` below, not from a list entry
		want.append(ed)
		ids.append(str(ed["id"]))
	var you_id := "__you"
	if ashore:
		want.append({"id": you_id, "kind": "player", "name": "You", "detail": "", "x": (_state["player"] as Vector2).x, "z": (_state["player"] as Vector2).y, "rank": 9, "views": []})
		ids.append(you_id)
	var sig := vid + "|" + ",".join(PackedStringArray(ids))
	_vis_entries = want
	if force or sig != _sig:
		_sig = sig
		_rebuild(want)
	else:
		_refresh_texts()
	_update_detail()
	_dirty = true


func _rebuild(want: Array) -> void:
	for m in _markers.values():
		(m as Node).queue_free()
	_markers.clear()
	for r in _rows.values():
		(r as Node).queue_free()
	_rows.clear()
	for e in want:
		_make_marker(e as Dictionary)
		if str((e as Dictionary)["kind"]) != "player":
			_make_row(e as Dictionary)
	if _sel != "" and not _markers.has(_sel):
		_sel = ""
	_refresh_texts()


func _make_marker(e: Dictionary) -> void:
	var id := str(e["id"])
	var kind := str(e["kind"])
	var st: Array = KIND_STYLE.get(kind, KIND_STYLE["place"])
	var fill: Color = e.get("color", st[1]) as Color
	var b := Button.new()
	b.name = "M_" + id
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(DOT, DOT)
	b.size = Vector2(DOT, DOT)
	b.text = str(e.get("letter", st[0]))
	b.add_theme_font_size_override("font_size", 12 if b.text.length() > 1 else 14)
	b.add_theme_constant_override("outline_size", 0)
	var sb := _box(fill, st[2] as Color, 3, int(DOT / 2.0), 0)
	b.add_theme_stylebox_override("normal", sb)
	b.add_theme_stylebox_override("hover", _box(fill.lightened(0.25), GOLD, 3, int(DOT / 2.0), 0))
	b.add_theme_stylebox_override("pressed", _box(fill.lightened(0.25), GOLD, 3, int(DOT / 2.0), 0))
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		b.add_theme_color_override(c, st[2] as Color)
	b.tooltip_text = "%s\n%s" % [str(e["name"]), str(e.get("detail", ""))]
	if id != "__you":
		b.pressed.connect(select.bind(id, false))
	else:
		b.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if kind == "ship":
		var tri := Polygon2D.new()
		tri.name = "Heading"
		tri.polygon = PackedVector2Array([Vector2(0, -DOT * 0.85), Vector2(7, -DOT * 0.45), Vector2(-7, -DOT * 0.45)])
		tri.position = Vector2(DOT * 0.5, DOT * 0.5)
		tri.color = st[1] as Color
		b.add_child(tri)
	var lab := Label.new()
	lab.name = "Name"
	lab.text = str(e["name"])
	lab.mouse_filter = Control.MOUSE_FILTER_IGNORE
	lab.add_theme_font_size_override("font_size", 14)
	lab.add_theme_color_override("font_color", CREAM)
	lab.add_theme_color_override("font_outline_color", INK)
	lab.add_theme_constant_override("outline_size", 5)
	b.add_child(lab)
	_marker_box.add_child(b)
	_markers[id] = b


func _make_row(e: Dictionary) -> void:
	var id := str(e["id"])
	var b := Button.new()
	b.name = "Row_" + id
	b.toggle_mode = true
	b.focus_mode = Control.FOCUS_NONE
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.custom_minimum_size = Vector2(0, 46)
	b.clip_text = true
	b.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	b.add_theme_font_size_override("font_size", 14)
	_skin_button(b, Color(0.20, 0.14, 0.08), GOLD.darkened(0.55), CREAM)
	b.pressed.connect(_on_row_pressed.bind(id))
	_row_box.add_child(b)
	_rows[id] = b


func _refresh_texts() -> void:
	for e in _vis_entries:
		var ed := e as Dictionary
		var id := str(ed["id"])
		var mk := _marker_for(id)
		if mk != null:
			var nm := str(ed["name"])
			if str(ed["kind"]) == "ship" and not bool(_state.get("ashore", false)):
				nm = "%s (you are aboard)" % nm
			(mk.get_node("Name") as Label).text = nm
			mk.tooltip_text = "%s\n%s" % [nm, str(ed.get("detail", ""))]
		if _rows.has(id):
			var tag := "     << TRACKED" if id == tracked else ""
			var b := _rows[id] as Button
			b.text = "%s%s\n%s" % [str(ed["name"]), tag, str(ed.get("detail", ""))]
			b.add_theme_color_override("font_color", GOLD if id == tracked else CREAM)
			b.set_pressed_no_signal(id == _sel)


func _update_detail() -> void:
	if _detail_name == null:
		return
	var e := _entry(_sel) if _sel != "" else {}
	if e.is_empty():
		_detail_name.text = "Nothing selected"
		_detail_text.text = "Click a marker or a name in the list."
		_track_btn.disabled = true
		_track_btn.text = "Track this place"
		return
	_detail_name.text = str(e["name"])
	_detail_text.text = str(e.get("detail", ""))
	_track_btn.disabled = false
	_track_btn.text = "Stop tracking this place" if _sel == tracked else "Track this place"


func _on_row_pressed(id: String) -> void:
	select(id, true)


func _on_track_pressed() -> void:
	if _sel != "":
		track_requested.emit(_sel)
		call_deferred("_after_track")


func _after_track() -> void:
	if provider.is_valid() and _open:
		_fetch_state()
		_refresh_texts()
		_update_detail()


func _init_view() -> void:
	if tab < 0 or _frame == null:
		return
	var fs := _frame.size
	if fs.x < 50.0 or fs.y < 50.0:
		return        # not laid out yet: _process / the resized signal call this again
	_need_init = false
	var v := views[tab] as Dictionary
	_fit_z = Model.fit_zoom(fs, _map_px)
	_zoom = clampf(float(v["zoom"]), _fit_z, ZOOM_MAX)
	_origin = Vector2.ZERO
	center_on_you()
	_dirty = true


func _on_frame_resized() -> void:
	if _need_init:
		_init_view()
	_dirty = true


func _apply_layout() -> void:
	_dirty = false
	if tab < 0 or _frame == null:
		return
	var fs := _frame.size
	if fs.x < 50.0 or fs.y < 50.0:
		return
	var v := views[tab] as Dictionary
	_fit_z = Model.fit_zoom(fs, _map_px)
	_zoom = clampf(_zoom, _fit_z, ZOOM_MAX)
	_origin = Model.clamp_origin(_origin, fs, _map_px * _zoom)
	_picture.position = _origin
	_picture.size = _map_px * _zoom
	var items: Array = []
	var frame_rect := Rect2(Vector2(-30, -30), fs + Vector2(60, 60))
	var ship_pos: Vector2 = _state["ship"]
	for e in _vis_entries:
		var ed := e as Dictionary
		var id := str(ed["id"])
		var m := _marker_for(id)
		if m == null:
			continue
		var p := Vector2(float(ed["x"]), float(ed["z"]))
		if str(ed["kind"]) == "ship":
			p = ship_pos
		var sp := Model.world_to_frame(p, v, _origin, _zoom)
		m.position = sp - Vector2(DOT, DOT) * 0.5
		m.visible = frame_rect.has_point(sp)
		var hd := m.get_node_or_null("Heading") as Polygon2D
		if hd != null:
			hd.rotation = float(_state["ship_heading"])
		var lab := m.get_node("Name") as Label
		lab.visible = false
		if m.visible:
			var rk := int(ed.get("rank", 1))
			items.append({"id": id, "dot": Rect2(m.position, Vector2(DOT, DOT)), "label": lab.get_minimum_size(), "priority": rk * 10 + (5 if _zoom > _fit_z * 1.8 else 0),
					"force": id == _sel or id == tracked or str(ed["kind"]) == "player"})
	var shown := Model.place_labels(items)
	for id in shown.keys():
		var m2 := _marker_for(str(id))
		var lr: Rect2 = shown[id]
		var lab2 := m2.get_node("Name") as Label
		lab2.visible = true
		lab2.position = lr.position - m2.position
	var you := Model.you_at(_state)
	var here := Model.in_bounds(you, v)
	var hint := str(v["hint"])
	if not here:
		hint = "You are not on this map (%s)" % _where_you_are()
	_tab_hint.text = hint
	_zoom_info.text = "%d%%" % int(roundf(_zoom / maxf(_fit_z, 0.0001) * 100.0))
	_scale_lbl.text = "about %d m across" % int(fs.x / _zoom / float(v["ppm"]))
	_rings.queue_redraw()


func _where_you_are() -> String:
	var you := Model.you_at(_state)
	for i in views.size():
		if Model.in_bounds(you, views[i] as Dictionary):
			return "you are on the %s tab" % str((views[i] as Dictionary)["tab"])
	return "you are outside every map"


func _draw_overlay() -> void:
	if tab < 0 or tab >= views.size():
		return
	var v := views[tab] as Dictionary
	var vid := str(v["id"])
	var ppm := float(v["ppm"])
	for r in (_state["rings"] as Array):
		var rd := r as Dictionary
		var vs: Array = rd.get("views", []) as Array
		if not vs.is_empty() and not vs.has(vid):
			continue
		var c := Model.world_to_frame(Vector2(float(rd["x"]), float(rd["z"])), v, _origin, _zoom)
		var col := Color(0.35, 0.95, 0.45, 0.9) if bool(rd.get("open", true)) else Color(1.0, 0.7, 0.25, 0.9)
		_rings.draw_arc(c, float(rd["r"]) * ppm * _zoom, 0.0, TAU, 48, col, 3.0)
	var you := Model.you_at(_state)
	if Model.in_bounds(you, v):
		var yp := Model.world_to_frame(you, v, _origin, _zoom)
		_rings.draw_arc(yp, 20.0 + 3.0 * sin(_t * 4.0), 0.0, TAU, 32, Color(1.0, 0.35, 0.30, 0.95), 3.0)
	var te := _entry(tracked) if tracked != "" else {}
	if not te.is_empty():
		var to := Model.world_to_frame(Vector2(float(te["x"]), float(te["z"])), v, _origin, _zoom)
		if Model.in_bounds(you, v):
			_rings.draw_dashed_line(Model.world_to_frame(you, v, _origin, _zoom), to, GOLD, 3.0, 10.0)
		_rings.draw_arc(to, 20.0 + 4.0 * sin(_t * 5.0), 0.0, TAU, 32, GOLD, 3.0)


func _process(delta: float) -> void:
	if not _open:
		return
	_t += delta
	if _need_init:
		_init_view()
	var dir := Vector2.ZERO
	if KeyUtil.held(KEY_A) or KeyUtil.held(KEY_LEFT):
		dir.x += 1.0
	if KeyUtil.held(KEY_D) or KeyUtil.held(KEY_RIGHT):
		dir.x -= 1.0
	if KeyUtil.held(KEY_W):
		dir.y += 1.0
	if KeyUtil.held(KEY_S):
		dir.y -= 1.0
	if dir != Vector2.ZERO:
		pan_by(dir * PAN_PX_PER_S * delta)
	_refresh_t -= delta
	if _refresh_t <= 0.0:
		_refresh_t = REFRESH_S
		if provider.is_valid():
			_fetch_state()
	if _dirty or tracked != "":
		_apply_layout()
	_rings.queue_redraw()


# ---- input -------------------------------------------------------------------------------------------------------------------
func _typing() -> bool:
	var vp := get_viewport()
	if vp == null:
		return false
	var f := vp.gui_get_focus_owner()
	return f is LineEdit or f is TextEdit


func _input(event: InputEvent) -> void:
	var k := event as InputEventKey
	if k == null or not k.pressed or k.echo:
		return
	if _typing():
		return
	if _open:
		if _on_open_key(k):
			get_viewport().set_input_as_handled()
		return
	if k.is_action_pressed(ACTION, false, true):
		get_viewport().set_input_as_handled()
		request_open()


## Keys while the map is open. Returns true when swallowed: everything except the function keys is, so the game never reacts
## to a key meant for the map (W/A/S/D must not walk the player while the chart is being moved).
func _on_open_key(k: InputEventKey) -> bool:
	var code := KeyUtil.code(k)
	if code >= KEY_F1 and code <= KEY_F12:
		return false
	if k.ctrl_pressed or k.alt_pressed or k.meta_pressed:
		return false
	if k.is_action_pressed(ACTION, false, true):
		if Engine.get_process_frames() != _opened_frame:     # never close in the very frame that opened (a duplicated event)
			close_map()
		return true
	if code == KEY_ESCAPE:
		close_map()
		return true
	if init_error != "" or _overlay == null:
		return true
	var d := KeyUtil.digit(code)
	if d >= 0 and d < views.size():
		set_tab(d)
	elif code == KEY_TAB:
		set_tab((tab + 1) % maxi(views.size(), 1))
	elif code == KEY_EQUAL or code == KEY_PLUS or code == KEY_KP_ADD:
		zoom_by(ZOOM_STEP)
	elif code == KEY_MINUS or code == KEY_KP_SUBTRACT:
		zoom_by(1.0 / ZOOM_STEP)
	elif code == KEY_HOME:
		center_on_you()
	elif code == KEY_C:
		track_requested.emit("")
		call_deferred("_after_track")
	elif code == KEY_ENTER or code == KEY_KP_ENTER or code == KEY_T:
		_on_track_pressed()
	elif code == KEY_UP or code == KEY_DOWN:
		_step_selection(-1 if code == KEY_UP else 1)
	return true


func _step_selection(dir: int) -> void:
	var ids: Array = []
	for e in _vis_entries:
		if _rows.has(str((e as Dictionary)["id"])):
			ids.append(str((e as Dictionary)["id"]))
	if ids.is_empty():
		return
	var i := ids.find(_sel)
	i = 0 if i < 0 else clampi(i + dir, 0, ids.size() - 1)
	select(str(ids[i]), true)
	var row := _rows[str(ids[i])] as Control
	var sc := _row_box.get_parent() as ScrollContainer
	if sc != null:
		sc.ensure_control_visible(row)


func _on_frame_input(ev: InputEvent) -> void:
	var mb := ev as InputEventMouseButton
	if mb != null:
		if mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_UP:
			zoom_by(ZOOM_STEP, mb.position)
		elif mb.pressed and mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			zoom_by(1.0 / ZOOM_STEP, mb.position)
		elif mb.button_index == MOUSE_BUTTON_LEFT or mb.button_index == MOUSE_BUTTON_MIDDLE:
			_drag = mb.pressed
		return
	var mm := ev as InputEventMouseMotion
	if mm != null and _drag:
		pan_by(mm.relative)


# ---- emergency window --------------------------------------------------------------------------------------------------------
## The scene itself is damaged (a node is missing): build a plain window from code so the player still gets a visible answer
## and a way out, instead of a key that silently does nothing.
func _open_emergency(why: String) -> bool:
	_open = true
	_opened_frame = Engine.get_process_frames()
	fail_count += 1
	last_error = why
	var root := Control.new()
	root.name = "EmergencyMap"
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_STOP
	var bg := ColorRect.new()
	bg.color = Color(0.0, 0.0, 0.0, 0.85)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)
	var cc := CenterContainer.new()
	cc.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(cc)
	var vb := VBoxContainer.new()
	vb.custom_minimum_size = Vector2(520, 0)
	cc.add_child(vb)
	var l := Label.new()
	l.text = "THE MAP CANNOT BE SHOWN\n\n%s\n\nThe game itself is not affected. Press Esc or the button to close this message." % why
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_size_override("font_size", 18)
	vb.add_child(l)
	var b := Button.new()
	b.text = "CLOSE"
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(0, 44)
	b.pressed.connect(close_map)
	vb.add_child(b)
	add_child(root)
	_emergency = root
	set_process(false)
	_write_diag()
	opened.emit(-1)
	return true


func _exit_tree() -> void:
	if _open:
		_open = false
		closed.emit()
