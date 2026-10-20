extends Control
## CP-2 Release A: everything the ship mode puts on the screen, in one place and built from the shared UiKit.
##   status chip  bottom centre: what steers the ship (STEERING: DIRECT / COURSE HOLD 058 ENE / STEERING BY HAND / MOORED) and where you are
##   prompt       a key chip and the thing E does here ("E  Take the helm")
##   toast        one short message that fades (the chest, the barrels, the berths, "course hold ON")
##   info panel   a small modal list (the provisions hold, the fish barrels) that E, Esc or Space close; the game never waits on it
##   fade         a black layer the hatch transitions use
## Layout at 1366x876 (bottom up): the existing dock label (-92..-52), prompt (-136..-98), status chip (-232..-144), toast (-292..-240).
## Nothing here reads keys: the host (h2d0.gd) decides, so there is ONE input path. NOT YET RUN ON THE USER'S PC.
const UiKit := preload("res://h2d/ui_kit.gd")
const KIND_COLOR := {
	"hold": Color(0.55, 0.92, 0.62), "hand": Color(1.0, 0.72, 0.25), "direct": Color(1.0, 0.95, 0.82),
	"moored": Color(0.70, 0.78, 0.86), "none": Color(1.0, 1.0, 1.0),
}
var _status: PanelContainer
var _place: Label
var _title: Label
var _sub: Label
var _prompt: PanelContainer
var _key: Label
var _what: Label
var _toast: Label
var _toast_left := 0.0
var _info: PanelContainer
var _info_title: Label
var _info_body: VBoxContainer
var _info_foot: Label
var _layer: CanvasLayer
var _fade: ColorRect
var _last_kind := ""


func _init() -> void:
	name = "ShipHud"
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()


func _build() -> void:
	# status chip
	_status = UiKit.panel(UiKit.INK, UiKit.BORDER, 3, 6)
	_status.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_status.anchor_left = 0.5
	_status.anchor_right = 0.5
	_status.anchor_top = 1.0
	_status.anchor_bottom = 1.0
	_status.offset_left = -330.0
	_status.offset_right = 330.0
	_status.offset_top = -232.0
	_status.offset_bottom = -144.0
	var col := UiKit.box(true, 0)
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	_status.add_child(col)
	_place = UiKit.label("", 13, UiKit.GOLD, 3)
	_place.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	col.add_child(_place)
	_title = UiKit.label("", 24, UiKit.CREAM, 5)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	col.add_child(_title)
	_sub = UiKit.label("", 14, UiKit.DIM, 3)
	_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	col.add_child(_sub)
	add_child(_status)
	# prompt
	_prompt = UiKit.panel(Color(0.08, 0.06, 0.04, 0.9), UiKit.GOLD, 2, 4)
	_prompt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_prompt.anchor_left = 0.5
	_prompt.anchor_right = 0.5
	_prompt.anchor_top = 1.0
	_prompt.anchor_bottom = 1.0
	_prompt.offset_left = -300.0
	_prompt.offset_right = 300.0
	_prompt.offset_top = -136.0
	_prompt.offset_bottom = -98.0
	var row := UiKit.box(false, 10)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	_prompt.add_child(row)
	_key = UiKit.label("E", 20, Color(0.1, 0.07, 0.04), 0)
	_key.add_theme_stylebox_override("normal", UiKit.style(UiKit.GOLD, UiKit.GOLD, 1, 4))
	_key.custom_minimum_size = Vector2(34.0, 0.0)
	_key.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	row.add_child(_key)
	_what = UiKit.label("", 20, UiKit.CREAM, 4)
	row.add_child(_what)
	add_child(_prompt)
	# toast
	_toast = UiKit.label("", 18, UiKit.CREAM, 6)
	_toast.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_toast.offset_top = -292.0
	_toast.offset_bottom = -240.0
	_toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_toast.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	_toast.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_toast.offset_left = 180.0
	_toast.offset_right = -180.0
	_toast.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_toast)
	# info panel
	_info = UiKit.panel(UiKit.INK2, UiKit.BORDER, 4, 12)
	_info.set_anchors_preset(Control.PRESET_CENTER)
	_info.custom_minimum_size = Vector2(560.0, 0.0)
	_info.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_info.grow_vertical = Control.GROW_DIRECTION_BOTH
	var ic := UiKit.box(true, 8)
	_info.add_child(ic)
	_info_title = UiKit.label("", 30, UiKit.GOLD, 6, true)
	_info_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ic.add_child(_info_title)
	_info_body = UiKit.box(true, 4) as VBoxContainer
	ic.add_child(_info_body)
	_info_foot = UiKit.label("", 14, UiKit.DIM, 3)
	_info_foot.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ic.add_child(_info_foot)
	_info.visible = false
	add_child(_info)
	_status.visible = false
	_prompt.visible = false
	_toast.visible = false


## The fade layer lives in its own CanvasLayer under the HUD layer so hatch transitions darken the world but not the prompts.
func attach_fade(host: Node) -> void:
	_layer = CanvasLayer.new()
	_layer.layer = 5
	host.add_child(_layer)
	_fade = ColorRect.new()
	_fade.color = Color(0.0, 0.0, 0.0, 0.0)
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.visible = false
	_layer.add_child(_fade)


func set_fade(a: float) -> void:
	if _fade == null:
		return
	_fade.visible = a > 0.003
	_fade.color = Color(0.0, 0.0, 0.0, clampf(a, 0.0, 1.0))


func fade_alpha() -> float:
	return _fade.color.a if _fade != null and _fade.visible else 0.0


## st = ShipMode.status(); place = "MAIN DECK" etc ("" hides the line).
func set_status(st: Dictionary, place: String, show_it: bool) -> void:
	var kind := str(st.get("kind", "none"))
	var title := str(st.get("title", ""))
	_status.visible = show_it and title != ""
	if not _status.visible:
		return
	_place.text = place
	_place.visible = place != ""
	_title.text = title
	_sub.text = str(st.get("sub", ""))
	_title.add_theme_color_override("font_color", KIND_COLOR.get(kind, UiKit.CREAM))
	if kind != _last_kind:
		_last_kind = kind
		_status.add_theme_stylebox_override("panel", UiKit.style(UiKit.INK, KIND_COLOR.get(kind, UiKit.BORDER), 3, 6, 8))


## "E  Take the helm": the part before the first double space is the key (a chip), the rest is the action.
func set_prompt(text: String, show_it: bool) -> void:
	_prompt.visible = show_it and text != ""
	if not _prompt.visible:
		return
	var at := text.find("  ")
	if at <= 0:
		_key.visible = false
		_what.text = text
		return
	_key.visible = true
	_key.text = text.substr(0, at)
	_what.text = text.substr(at).strip_edges()


func prompt_text() -> String:
	return ("%s  %s" % [_key.text, _what.text]) if _prompt.visible and _key.visible else (_what.text if _prompt.visible else "")


func toast(text: String, seconds: float = 4.5) -> void:
	_toast.text = text
	_toast.visible = text != ""
	_toast.modulate.a = 1.0
	_toast_left = seconds


func toast_text() -> String:
	return _toast.text if _toast.visible else ""


func tick(dt: float) -> void:
	if _toast_left > 0.0:
		_toast_left -= dt
		if _toast_left <= 0.0:
			_toast.visible = false
		elif _toast_left < 0.8:
			_toast.modulate.a = _toast_left / 0.8


# ---- the info panel ----------------------------------------------------------------------------------------------------
## rows: Array of [name, quantity text, detail text] (an empty name draws a thin rule); foot: the close hint.
func open_info(title: String, rows: Array, foot: String) -> void:
	_info_title.text = title
	for c in _info_body.get_children():
		_info_body.remove_child(c)
		c.queue_free()
	for r in rows:
		var rr: Array = r
		if str(rr[0]) == "":
			_info_body.add_child(UiKit.rect(UiKit.BORDER, Vector2(0.0, 2.0)))
			continue
		var line := UiKit.box(false, 10)
		var n := UiKit.label(str(rr[0]), 18, UiKit.CREAM, 3)
		n.custom_minimum_size = Vector2(250.0, 0.0)
		n.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		line.add_child(n)
		var q := UiKit.label(str(rr[1]), 18, UiKit.GOLD, 3)
		q.custom_minimum_size = Vector2(90.0, 0.0)
		q.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		line.add_child(q)
		var d := UiKit.label(str(rr[2]), 15, UiKit.DIM, 3)
		d.custom_minimum_size = Vector2(150.0, 0.0)
		line.add_child(d)
		_info_body.add_child(line)
	_info_foot.text = foot
	_info.visible = true


func close_info() -> void:
	_info.visible = false


func is_info_open() -> bool:
	return _info.visible


func info_title() -> String:
	return _info_title.text if _info.visible else ""


func info_row_count() -> int:
	return _info_body.get_child_count() if _info.visible else 0
