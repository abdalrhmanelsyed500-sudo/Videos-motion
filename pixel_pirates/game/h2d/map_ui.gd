extends Control
# gdlint: disable=class-definitions-order
## The map overlay (M), built from standard nodes: a clipped viewport holding the baked map picture (a TextureRect that is
## scaled and moved to zoom and pan), one small Control per marker laid over it, Line2D rings for the fishing grounds and a
## dashed Line2D route to the tracked place, plus a sidebar (a ScrollContainer of buttons) that lists every place with its
## live distance. Markers and rows are clickable; keys: Tab or 1-3 switch view, +/- or the wheel zoom, W A S D or a drag
## pan, Up/Down pick a row, Enter / T track it, C clears, Home centres on you, Esc / M close.
## It owns no rules: port_game.gd gives it `set_views()` once and `set_entries()` / `set_state()` while it is open.
const K := preload("res://h2d/ui_kit.gd")
const KeyUtil := preload("res://h2d/key_util.gd")
const PANEL_POS := Vector2(24, 16)
const PANEL_SIZE := Vector2(1232, 688)
const VP_POS := Vector2(16, 76)          # inside the panel
const VP_SIZE := Vector2(884, 552)
const KIND_STYLE := {   # kind -> [letter, fill colour, ring colour]
	"recruit": ["R", Color(0.98, 0.80, 0.25), Color(0.20, 0.12, 0.02)], "market": ["F", Color(0.35, 0.78, 0.88), Color(0.04, 0.2, 0.28)],
	"ship": ["S", Color(0.40, 0.58, 1.0), Color(0.04, 0.08, 0.3)], "player": ["", Color(1.0, 0.35, 0.30), Color(0.3, 0.02, 0.02)],
	"tavern": ["T", Color(0.92, 0.55, 0.28), Color(0.3, 0.12, 0.02)], "customs": ["C", Color(0.78, 0.70, 0.52), Color(0.2, 0.15, 0.05)],
	"palace": ["G", Color(0.80, 0.50, 0.92), Color(0.2, 0.05, 0.3)], "square": ["M", Color(0.70, 0.86, 0.50), Color(0.1, 0.2, 0.04)],
	"notice": ["N", Color(0.95, 0.92, 0.80), Color(0.25, 0.2, 0.1)], "light": ["L", Color(1.0, 0.95, 0.60), Color(0.3, 0.25, 0.02)],
	"ground": ["", Color(0.5, 0.85, 1.0), Color(0.04, 0.2, 0.3)], "place": ["", Color(0.85, 0.80, 0.70), Color(0.2, 0.15, 0.1)],
	"pier": ["P", Color(0.60, 0.72, 0.95), Color(0.05, 0.1, 0.25)], "warehouse": ["W", Color(0.75, 0.62, 0.45), Color(0.2, 0.12, 0.05)],
}

signal track_requested(id: String)
signal closed()
signal tab_changed(index: int)

var views: Array = []
var tab := 0
var entries: Array = []                  # [{id, kind, name, detail, x, z, color?, rank, views:[ids], group}]
var tracked := ""
var player := Vector2.ZERO
var player_heading := 0.0
var ship := Vector2.ZERO
var ship_heading := 0.0
var ashore := true
var rings: Array = []

var _panel: PanelContainer
var _vp: Control
var _tex: TextureRect
var _over: Control
var _zoom := 1.0
var _zoom_min := 0.2
var _origin := Vector2.ZERO               # content top-left in viewport coords
var _drag := false
var _markers: Dictionary = {}             # id -> Control
var _ring_lines: Array = []
var _route: Line2D
var _route_tex: ImageTexture
var _pulse: Control
var _rows: VBoxContainer
var _row_btns: Dictionary = {}
var _sel_id := ""
var _title: Label
var _tab_btns: Array = []
var _info: Label
var _zoom_lbl: Label
var _t := 0.0
var _map_px := Vector2(1, 1)
var _built_tab := -1
var layout_dumps := 0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	visible = false
	var dim := ColorRect.new()
	dim.color = Color(0.0, 0.0, 0.0, 0.55)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(dim)
	_panel = K.panel(Color(0.12, 0.08, 0.05, 0.98), K.BORDER, 4, 14)
	_panel.name = "MapPanel"
	_panel.position = PANEL_POS
	_panel.custom_minimum_size = PANEL_SIZE
	_panel.size = PANEL_SIZE
	_panel.add_theme_stylebox_override("panel", K.style(Color(0.12, 0.08, 0.05, 0.98), K.BORDER, 4, 6, 14))
	add_child(_panel)
	var holder := Control.new()
	holder.name = "Holder"
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.add_child(holder)
	_title = K.label("MAP OF ANVIL HARBOR", 36, K.GOLD, 5, true)
	_title.position = Vector2(4, -4)
	holder.add_child(_title)
	_info = K.label("", 14, K.DIM, 3)
	_info.position = Vector2(640, 6)
	_info.custom_minimum_size = Vector2(560, 0)
	_info.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	holder.add_child(_info)
	var tabs := K.box(false, 6)
	tabs.position = Vector2(4, 40)
	tabs.name = "Tabs"
	holder.add_child(tabs)
	_tab_btns = []
	_vp = Control.new()
	_vp.name = "MapViewport"
	_vp.position = VP_POS - Vector2(0, 0) - Vector2(12, 12)
	_vp.size = VP_SIZE
	_vp.custom_minimum_size = VP_SIZE
	_vp.clip_contents = true
	_vp.mouse_filter = Control.MOUSE_FILTER_STOP
	_vp.gui_input.connect(_on_vp_input)
	holder.add_child(_vp)
	var bg := ColorRect.new()
	bg.color = Color(0.10, 0.22, 0.30)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_vp.add_child(bg)
	_tex = TextureRect.new()
	_tex.name = "MapPicture"
	_tex.stretch_mode = TextureRect.STRETCH_SCALE
	_tex.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_tex.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_tex.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_vp.add_child(_tex)
	_over = Control.new()
	_over.name = "Overlay"
	_over.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_over.set_anchors_preset(Control.PRESET_FULL_RECT)
	_vp.add_child(_over)
	var img := Image.create(8, 2, false, Image.FORMAT_RGBA8)
	img.fill(Color(1, 1, 1, 0))
	for x in 4:
		for y in 2:
			img.set_pixel(x, y, Color(1, 1, 1, 1))
	_route_tex = ImageTexture.create_from_image(img)
	_route = Line2D.new()
	_route.name = "Route"
	_route.width = 4.0
	_route.default_color = K.GOLD
	_route.texture = _route_tex
	_route.texture_mode = Line2D.LINE_TEXTURE_TILE
	_route.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	_route.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_route.visible = false
	_over.add_child(_route)
	_pulse = Control.new()
	_pulse.name = "TrackPulse"
	_pulse.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var pl := Line2D.new()
	pl.width = 3.0
	pl.default_color = K.GOLD
	pl.closed = true
	for i in 32:
		pl.add_point(Vector2.from_angle(TAU * float(i) / 32.0) * 18.0)
	_pulse.add_child(pl)
	_pulse.visible = false
	_over.add_child(_pulse)
	_zoom_lbl = K.label("", 13, K.CREAM, 4)
	_zoom_lbl.position = Vector2(8, VP_SIZE.y - 24)
	_vp.add_child(_zoom_lbl)
	# sidebar
	var side := K.box(true, 6)
	side.name = "Sidebar"
	side.position = Vector2(VP_POS.x - 12 + VP_SIZE.x + 14, 40)
	side.custom_minimum_size = Vector2(290, 580)
	holder.add_child(side)
	side.add_child(K.label("PLACES AND PEOPLE", 13, K.GOLD, 3))
	var sc := ScrollContainer.new()
	sc.name = "RowScroll"
	sc.custom_minimum_size = Vector2(290, 440)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	side.add_child(sc)
	_rows = K.box(true, 4)
	_rows.custom_minimum_size = Vector2(272, 0)
	_rows.mouse_filter = Control.MOUSE_FILTER_PASS
	sc.add_child(_rows)
	var help := K.label("Click a place or press Enter to track it.\nTab: view   +/-: zoom   WASD: pan\nHome: centre on you   C: clear   Esc: close", 12, K.DIM, 3)
	help.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	help.custom_minimum_size = Vector2(285, 0)
	side.add_child(help)


# ---- data -------------------------------------------------------------------------------------------------------------
func set_views(v: Array) -> void:
	views = v
	var tabs := _panel.get_node("Holder/Tabs") as BoxContainer
	for b in _tab_btns:
		(b as Node).queue_free()
	_tab_btns.clear()
	for i in views.size():
		var b := K.button("%d  %s" % [i + 1, str((views[i] as Dictionary)["name"])], 16)
		b.alignment = HORIZONTAL_ALIGNMENT_CENTER
		b.custom_minimum_size = Vector2(120, 30)
		b.mouse_filter = Control.MOUSE_FILTER_STOP
		b.pressed.connect(set_tab.bind(i))
		tabs.add_child(b)
		_tab_btns.append(b)


func open(first_tab: int, state: Dictionary) -> void:
	visible = true
	tab = -1
	set_state(state)
	set_tab(clampi(first_tab, 0, maxi(views.size() - 1, 0)))
	_sel_id = tracked
	_center_on(player if ashore else ship)


func close() -> void:
	visible = false


func set_state(d: Dictionary) -> void:
	entries = d["entries"] as Array
	tracked = str(d.get("tracked", ""))
	player = d["player"] as Vector2
	player_heading = float(d.get("player_heading", 0.0))
	ship = d["ship"] as Vector2
	ship_heading = float(d.get("ship_heading", 0.0))
	ashore = bool(d.get("ashore", true))
	rings = d.get("rings", []) as Array
	if visible:
		_sync()


func set_tab(i: int) -> void:
	if i == tab or i < 0 or i >= views.size():
		return
	tab = i
	var v := views[tab] as Dictionary
	var t := K.texture("res://h2d/art/" + str(v["file"]))
	_tex.texture = t
	var bounds: Array = v["bounds"]
	_map_px = Vector2((float(bounds[2]) - float(bounds[0])) * float(v["ppm"]), (float(bounds[3]) - float(bounds[1])) * float(v["ppm"]))
	_tex.size = _map_px
	_tex.scale = Vector2.ONE
	_zoom_min = minf(VP_SIZE.x / _map_px.x, VP_SIZE.y / _map_px.y) * 0.98
	_zoom = clampf(float(v.get("zoom", 1.0)), _zoom_min, 8.0)
	for i2 in _tab_btns.size():
		K.set_button_selected(_tab_btns[i2] as Button, i2 == tab)
	_title.text = "MAP: %s" % str(v["title"])
	_clear_markers()
	_sync()
	_center_on(player if ashore else ship)
	tab_changed.emit(tab)


func _clear_markers() -> void:
	for m in _markers.values():
		(m as Node).queue_free()
	_markers.clear()
	for l in _ring_lines:
		(l as Node).queue_free()
	_ring_lines.clear()
	for b in _row_btns.values():
		(b as Node).queue_free()
	_row_btns.clear()
	_built_tab = -1


func _in_view(e: Dictionary) -> bool:
	var vs := e.get("views", []) as Array
	return vs.is_empty() or vs.has(str((views[tab] as Dictionary)["id"]))


func _sync() -> void:
	if views.is_empty() or tab < 0:
		return
	var vid := str((views[tab] as Dictionary)["id"])
	var want: Array = []
	for e in entries:
		var d := e as Dictionary
		if _in_view(d):
			want.append(d)
	if _built_tab != tab or _markers.size() != want.size():
		_clear_markers()
		_built_tab = tab
		for d in want:
			_make_marker(d as Dictionary)
		_make_rows(want)
		_make_rings(vid)
	_update_texts(want)
	_layout()


func _make_marker(d: Dictionary) -> void:
	var kind := str(d["kind"])
	var st: Array = KIND_STYLE.get(kind, KIND_STYLE["place"])
	var m := Control.new()
	m.name = "M_" + str(d["id"])
	m.mouse_filter = Control.MOUSE_FILTER_IGNORE
	m.set_meta("id", str(d["id"]))
	var ring := Panel.new()
	ring.name = "Dot"
	var sb := K.style(d.get("color", st[1]) as Color, st[2] as Color, 3, 13)
	ring.add_theme_stylebox_override("panel", sb)
	ring.size = Vector2(24, 24)
	ring.position = Vector2(-12, -12)
	ring.mouse_filter = Control.MOUSE_FILTER_STOP
	ring.gui_input.connect(_on_marker_input.bind(str(d["id"])))
	ring.mouse_entered.connect(func() -> void: _hover_id(str(d["id"])))
	m.add_child(ring)
	var letter := K.label(str(d.get("letter", st[0])), 15, st[2] as Color, 0, true)
	letter.name = "Letter"
	letter.position = Vector2(-12, -14)
	letter.size = Vector2(24, 24)
	letter.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	letter.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	m.add_child(letter)
	if kind == "player" or kind == "ship":
		var tri := Polygon2D.new()
		tri.name = "Heading"
		tri.polygon = PackedVector2Array([Vector2(0, -22), Vector2(7, -10), Vector2(-7, -10)])
		tri.color = st[1] as Color
		m.add_child(tri)
	var lab := K.label(str(d["name"]), 14, K.CREAM, 5)
	lab.name = "Name"
	lab.position = Vector2(15, -11)
	m.add_child(lab)
	_over.add_child(m)
	_markers[str(d["id"])] = m


func _make_rings(vid: String) -> void:
	for r in rings:
		var rd := r as Dictionary
		if not (rd.get("views", []) as Array).has(vid):
			continue
		var l := Line2D.new()
		l.width = 3.0
		l.closed = true
		l.default_color = (K.GREEN if bool(rd["open"]) else K.AMBER)
		l.set_meta("x", float(rd["x"]))
		l.set_meta("z", float(rd["z"]))
		l.set_meta("r", float(rd["r"]))
		for i in 40:
			l.add_point(Vector2.ZERO)
		l.default_color.a = 0.9
		_over.add_child(l)
		_over.move_child(l, 0)
		_ring_lines.append(l)


func _make_rows(want: Array) -> void:
	for d in want:
		var e := d as Dictionary
		var kind := str(e["kind"])
		if kind == "player" or int(e.get("row", 1)) == 0:
			continue
		var b := K.button("", 15)
		b.name = "Row_" + str(e["id"])
		b.custom_minimum_size = Vector2(268, 48)
		b.mouse_filter = Control.MOUSE_FILTER_STOP
		b.pressed.connect(_on_row.bind(str(e["id"])))
		b.mouse_entered.connect(func() -> void: _hover_id(str(e["id"])))
		_rows.add_child(b)
		_row_btns[str(e["id"])] = b


func _update_texts(want: Array) -> void:
	for d in want:
		var e := d as Dictionary
		var id := str(e["id"])
		if _row_btns.has(id):
			var b := _row_btns[id] as Button
			var tag := "   << TRACKING" if id == tracked else ""
			b.text = "%s%s\n%s" % [str(e["name"]), tag, str(e["detail"])]
			K.set_button_selected(b, id == _sel_id)
			if id == tracked:
				b.add_theme_color_override("font_color", K.GOLD)
	var v := views[tab] as Dictionary
	_info.text = "%s    zoom %d%%" % [str(v["hint"]), int(roundf(_zoom / maxf(_zoom_min, 0.001) * 100.0))]


# ---- layout -----------------------------------------------------------------------------------------------------------
func w2s(p: Vector2) -> Vector2:
	var v := views[tab] as Dictionary
	var b: Array = v["bounds"]
	var ppm := float(v["ppm"])
	return _origin + Vector2((p.x - float(b[0])) * ppm, (p.y - float(b[1])) * ppm) * _zoom


func s2w(s: Vector2) -> Vector2:
	var v := views[tab] as Dictionary
	var b: Array = v["bounds"]
	var ppm := float(v["ppm"])
	var c := (s - _origin) / _zoom / ppm
	return Vector2(c.x + float(b[0]), c.y + float(b[1]))


func _center_on(p: Vector2) -> void:
	if views.is_empty() or tab < 0:
		return
	_origin = Vector2.ZERO
	var sp := w2s(p)
	_origin = VP_SIZE * 0.5 - sp
	_clamp_origin()
	_layout()


func _clamp_origin() -> void:
	var sz := _map_px * _zoom
	var lo := Vector2(minf(VP_SIZE.x - sz.x, 0.0), minf(VP_SIZE.y - sz.y, 0.0)) - Vector2(80, 80)
	var hi := Vector2(maxf(0.0, VP_SIZE.x - sz.x), maxf(0.0, VP_SIZE.y - sz.y)) + Vector2(80, 80)
	if sz.x < VP_SIZE.x:
		lo.x = (VP_SIZE.x - sz.x) * 0.5
		hi.x = lo.x
	if sz.y < VP_SIZE.y:
		lo.y = (VP_SIZE.y - sz.y) * 0.5
		hi.y = lo.y
	_origin = Vector2(clampf(_origin.x, lo.x, hi.x), clampf(_origin.y, lo.y, hi.y))


func _layout() -> void:
	if views.is_empty() or tab < 0 or not visible:
		return
	_tex.position = _origin
	_tex.size = _map_px * _zoom
	var show_all := _zoom >= _zoom_min * 2.2
	for id in _markers.keys():
		var m := _markers[id] as Control
		var e := _entry(str(id))
		var p := Vector2(float(e["x"]), float(e["z"]))
		var kind := str(e["kind"])
		if kind == "player":
			p = player
			m.visible = ashore
		elif kind == "ship":
			p = ship
		m.position = w2s(p)
		var important := int(e.get("rank", 1)) >= 2 or str(id) == tracked or str(id) == _sel_id
		(m.get_node("Name") as Control).visible = important or show_all
		var hd := m.get_node_or_null("Heading") as Polygon2D
		if hd != null:
			hd.rotation = (player_heading if kind == "player" else ship_heading)
	for l in _ring_lines:
		var ln := l as Line2D
		var c := w2s(Vector2(float(ln.get_meta("x")), float(ln.get_meta("z"))))
		var v := views[tab] as Dictionary
		var rr := float(ln.get_meta("r")) * float(v["ppm"]) * _zoom
		for i in 40:
			ln.set_point_position(i, c + Vector2.from_angle(TAU * float(i) / 40.0) * rr)
	var te := _entry(tracked)
	if tracked != "" and not te.is_empty() and _markers.has(tracked):
		var from := w2s(player if ashore else ship)
		var to := w2s(Vector2(float(te["x"]), float(te["z"])))
		_route.visible = true
		_route.clear_points()
		_route.add_point(from)
		_route.add_point(to)
		_pulse.visible = true
		_pulse.position = to
		_pulse.scale = Vector2.ONE * (1.0 + 0.25 * sin(_t * 5.0))
	else:
		_route.visible = false
		_pulse.visible = false
	_zoom_lbl.text = "%d m per screen width" % int(VP_SIZE.x / _zoom / float((views[tab] as Dictionary)["ppm"]))


func _entry(id: String) -> Dictionary:
	for e in entries:
		if str((e as Dictionary)["id"]) == id:
			return e as Dictionary
	return {}


func _process(delta: float) -> void:
	_t += delta
	if visible:
		_layout()


# ---- input ------------------------------------------------------------------------------------------------------------
func _hover_id(id: String) -> void:
	_sel_id = id
	for rid in _row_btns.keys():
		K.set_button_selected(_row_btns[rid] as Button, rid == _sel_id)


func _on_marker_input(ev: InputEvent, id: String) -> void:
	var mb := ev as InputEventMouseButton
	if mb != null and mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT:
		if id != "player":
			track_requested.emit(id)
		accept_event()


func _on_row(id: String) -> void:
	track_requested.emit(id)


func _on_vp_input(ev: InputEvent) -> void:
	var mb := ev as InputEventMouseButton
	if mb != null:
		if mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			zoom_at(1.25, mb.position)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			zoom_at(0.8, mb.position)
		elif mb.button_index == MOUSE_BUTTON_LEFT:
			_drag = mb.pressed
		return
	var mm := ev as InputEventMouseMotion
	if mm != null and _drag:
		_origin += mm.relative
		_clamp_origin()
		_layout()


func zoom_at(f: float, at: Vector2) -> void:
	var before := s2w(at)
	_zoom = clampf(_zoom * f, _zoom_min, 8.0)
	_origin = Vector2.ZERO
	_origin = at - w2s(before)
	_clamp_origin()
	_layout()


func pan(d: Vector2) -> void:
	_origin += d
	_clamp_origin()
	_layout()


func select_step(delta: int) -> void:
	var ids: Array = []
	for c in _rows.get_children():
		ids.append(str(c.name).substr(4))
	if ids.is_empty():
		return
	var i := ids.find(_sel_id)
	i = (i + delta + ids.size()) % ids.size() if i >= 0 else 0
	_sel_id = str(ids[i])
	for rid in _row_btns.keys():
		K.set_button_selected(_row_btns[rid] as Button, rid == _sel_id)
	var btn := _row_btns[_sel_id] as Control
	var sc := _rows.get_parent() as ScrollContainer
	sc.ensure_control_visible(btn)


func handle_key(key: int) -> bool:
	if not visible:
		return false
	if key == KEY_ESCAPE or key == KEY_M:
		closed.emit()
	elif key == KEY_TAB:
		set_tab((tab + 1) % maxi(views.size(), 1))
	elif KeyUtil.digit(key) >= 0 and KeyUtil.digit(key) < views.size():
		set_tab(KeyUtil.digit(key))
	elif key == KEY_EQUAL or key == KEY_KP_ADD or key == KEY_PLUS:
		zoom_at(1.3, VP_SIZE * 0.5)
	elif key == KEY_MINUS or key == KEY_KP_SUBTRACT:
		zoom_at(0.77, VP_SIZE * 0.5)
	elif key == KEY_W:
		pan(Vector2(0, 90))
	elif key == KEY_S:
		pan(Vector2(0, -90))
	elif key == KEY_A:
		pan(Vector2(90, 0))
	elif key == KEY_D:
		pan(Vector2(-90, 0))
	elif key == KEY_UP:
		select_step(-1)
	elif key == KEY_DOWN:
		select_step(1)
	elif key == KEY_ENTER or key == KEY_KP_ENTER or key == KEY_T or key == KEY_E or key == KEY_SPACE:
		if _sel_id != "":
			track_requested.emit(_sel_id)
	elif key == KEY_C:
		track_requested.emit("")
	elif key == KEY_HOME:
		_center_on(player if ashore else ship)
	return true


## Every control's rectangle, for the layout dump of the headless test (what is where, and is it inside the screen).
func dump_rects() -> Array:
	var out: Array = []
	_collect(_panel, out)
	return out


func _collect(n: Node, out: Array) -> void:
	var c := n as Control
	if c != null and c.is_visible_in_tree():
		var r := c.get_global_rect()
		var txt := ""
		if c is Label:
			txt = (c as Label).text
		elif c is Button:
			txt = (c as Button).text
		out.append({"name": str(c.name), "cls": c.get_class(), "x": r.position.x, "y": r.position.y, "w": r.size.x, "h": r.size.y, "text": txt})
	for ch in n.get_children():
		_collect(ch, out)
