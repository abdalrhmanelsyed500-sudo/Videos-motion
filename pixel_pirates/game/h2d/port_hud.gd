extends Control
# gdlint: disable=class-definitions-order
## CP-1 HUD built from standard nodes: purse + hold + crew + objective card (top right), the fishing panel under it, the tracking
## strip (top centre), the interaction prompt (bottom centre), toasts and the big banner. It only SHOWS what port_game.gd hands
## it in `set_data()`; it holds no rules.
## Printed in the corner of the screen so a tester can tell which build is running.
const BUILD_TAG := "CP-1 test build r3 (2026-10-19)   |   M map   E talk   F nets   F8 self-check"
const K := preload("res://h2d/ui_kit.gd")

var _card: PanelContainer
var _purse: Label
var _purse_shown := 0.0
var _purse_target := 0
var _purse_pulse := 0.0
var _hold_bar: ProgressBar
var _hold_lbl: Label
var _fresh_lbl: Label
var _crew_lbl: Label
var _obj_lbl: Label
var _fish: PanelContainer
var _fish_title: Label
var _fish_status: Label
var _fish_bar: ProgressBar
var _fish_list: Label
var _fish_hint: Label
var _track: PanelContainer
var _track_lbl: Label
var _track_arrow: Control
var _prompt: PanelContainer
var _prompt_key: Label
var _prompt_lbl: Label
var _toasts: VBoxContainer
var _banner: VBoxContainer
var _banner_t := 0.0
var _banner_big: Label
var _banner_sub: Label
var _t := 0.0
var _tag: Label
var shown_toasts := 0           # how many toasts were ever added (the self-play test reads it)


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_card()
	_build_fishing()
	_build_tracking()
	_build_prompt()
	_build_toasts()
	_build_banner()
	_tag = K.label(BUILD_TAG, 13, Color(1.0, 0.95, 0.82, 0.8), 3)
	_tag.name = "BuildTag"
	add_child(_tag)


func _build_card() -> void:
	var col := K.box(true, 8)
	col.anchor_left = 1.0
	col.anchor_right = 1.0
	col.offset_left = -318.0
	col.offset_right = -10.0
	col.offset_top = 8.0
	col.name = "RightColumn"
	add_child(col)
	_card = K.panel(K.INK, K.BORDER, 3, 6)
	_card.name = "StatusCard"
	col.add_child(_card)
	var v := K.box(true, 5)
	_card.add_child(v)
	var top := K.box(false, 8)
	v.add_child(top)
	var coin := K.rect(K.GOLD, Vector2(18, 18))
	coin.name = "Coin"
	top.add_child(coin)
	_purse = K.label("0 reales", 26, K.GOLD, 5, true)
	_purse.name = "Purse"
	top.add_child(_purse)
	_hold_lbl = K.label("Hold 0 / 40 kg", 15, K.CREAM, 3)
	v.add_child(_hold_lbl)
	_hold_bar = ProgressBar.new()
	_hold_bar.custom_minimum_size = Vector2(280, 12)
	_hold_bar.show_percentage = false
	_hold_bar.max_value = 1.0
	_hold_bar.add_theme_stylebox_override("background", K.style(Color(0.06, 0.05, 0.04), Color(0.3, 0.22, 0.12), 1, 2))
	_hold_bar.add_theme_stylebox_override("fill", K.style(Color(0.35, 0.72, 0.85), Color(0.35, 0.72, 0.85), 0, 2))
	_hold_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(_hold_bar)
	_fresh_lbl = K.label("", 13, K.DIM, 3)
	v.add_child(_fresh_lbl)
	_crew_lbl = K.label("Crew: none yet", 14, K.CREAM, 3)
	_crew_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_crew_lbl.custom_minimum_size = Vector2(280, 0)
	v.add_child(_crew_lbl)
	v.add_child(K.rect(Color(0.45, 0.32, 0.16), Vector2(280, 2)))
	var oh := K.label("OBJECTIVE", 12, K.GOLD, 3)
	v.add_child(oh)
	_obj_lbl = K.label("", 15, K.CREAM, 3)
	_obj_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_obj_lbl.custom_minimum_size = Vector2(280, 0)
	v.add_child(_obj_lbl)


func _build_fishing() -> void:
	var col := get_node("RightColumn") as Control
	_fish = K.panel(Color(0.06, 0.16, 0.22, 0.95), Color(0.30, 0.62, 0.78), 3, 6)
	_fish.name = "FishingPanel"
	_fish.visible = false
	col.add_child(_fish)
	var v := K.box(true, 5)
	_fish.add_child(v)
	_fish_title = K.label("NETS DOWN", 24, Color(0.62, 0.90, 1.0), 5, true)
	v.add_child(_fish_title)
	_fish_status = K.label("", 14, K.CREAM, 3)
	_fish_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_fish_status.custom_minimum_size = Vector2(280, 0)
	v.add_child(_fish_status)
	_fish_bar = ProgressBar.new()
	_fish_bar.custom_minimum_size = Vector2(280, 14)
	_fish_bar.show_percentage = false
	_fish_bar.max_value = 1.0
	_fish_bar.add_theme_stylebox_override("background", K.style(Color(0.03, 0.08, 0.12), Color(0.2, 0.4, 0.5), 1, 2))
	_fish_bar.add_theme_stylebox_override("fill", K.style(K.GOLD, K.GOLD, 0, 2))
	_fish_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(_fish_bar)
	_fish_list = K.label("", 14, K.CREAM, 3)
	v.add_child(_fish_list)
	_fish_hint = K.label("F: haul the nets in", 13, K.DIM, 3)
	v.add_child(_fish_hint)


func _build_tracking() -> void:
	_track = K.panel(Color(0.10, 0.07, 0.05, 0.9), K.GOLD, 2, 4)
	_track.name = "TrackingStrip"
	_track.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_track.offset_top = 8.0
	_track.visible = false
	_track.grow_horizontal = Control.GROW_DIRECTION_BOTH
	add_child(_track)
	var h := K.box(false, 10)
	_track.add_child(h)
	_track_arrow = Control.new()
	_track_arrow.custom_minimum_size = Vector2(26, 26)
	_track_arrow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var tri := Polygon2D.new()
	tri.polygon = PackedVector2Array([Vector2(0, -11), Vector2(9, 9), Vector2(0, 4), Vector2(-9, 9)])
	tri.color = K.GOLD
	tri.position = Vector2(13, 13)
	tri.name = "Tri"
	_track_arrow.add_child(tri)
	h.add_child(_track_arrow)
	_track_lbl = K.label("", 17, K.CREAM, 4)
	h.add_child(_track_lbl)


func _build_prompt() -> void:
	_prompt = K.panel(Color(0.10, 0.07, 0.05, 0.92), K.GOLD, 2, 4)
	_prompt.name = "Prompt"
	_prompt.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_prompt.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_prompt.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_prompt.offset_bottom = -150.0
	_prompt.visible = false
	add_child(_prompt)
	var h := K.box(false, 10)
	_prompt.add_child(h)
	var chip := K.panel(Color(0.96, 0.82, 0.40), Color(0.45, 0.30, 0.10), 2, 3)
	h.add_child(chip)
	_prompt_key = K.label("E", 20, Color(0.15, 0.09, 0.03), 0, true)
	chip.add_child(_prompt_key)
	_prompt_lbl = K.label("", 20, K.CREAM, 5)
	h.add_child(_prompt_lbl)


func _build_toasts() -> void:
	_toasts = K.box(true, 4)
	_toasts.name = "Toasts"
	_toasts.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_toasts.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_toasts.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_toasts.offset_bottom = -205.0
	_toasts.alignment = BoxContainer.ALIGNMENT_END
	add_child(_toasts)


func _build_banner() -> void:
	_banner = K.box(true, 0)
	_banner.name = "Banner"
	_banner.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_banner.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_banner.offset_top = 96.0
	_banner.visible = false
	add_child(_banner)
	_banner_big = K.label("", 54, K.GOLD, 10, true)
	_banner_big.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner.add_child(_banner_big)
	_banner_sub = K.label("", 18, K.CREAM, 6)
	_banner_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner.add_child(_banner_sub)


# ---- public ---------------------------------------------------------------------------------------------------------
func toast(text: String, color: Color = K.CREAM, seconds: float = 5.0) -> void:
	var p := K.panel(Color(0.08, 0.06, 0.04, 0.88), Color(color.r * 0.6, color.g * 0.6, color.b * 0.6), 2, 0)
	p.set_meta("t", seconds)
	var l := K.label(text, 17, color, 4)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(minf(float(text.length()) * 9.5 + 10.0, 760.0), 0)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	p.add_child(l)
	_toasts.add_child(p)
	shown_toasts += 1
	while _toasts.get_child_count() > 5:
		var first := _toasts.get_child(0)
		_toasts.remove_child(first)
		first.queue_free()


func note_big(text: String, sub: String, seconds: float = 5.5) -> void:
	_banner_big.text = text
	_banner_sub.text = sub
	_banner_t = seconds
	_banner.visible = true
	_purse_pulse = 1.0


func banner_text() -> String:
	return _banner_big.text if _banner.visible else ""


## d: {purse, hold_kg, cap_kg, fresh, warn_frac, spoil_warn, crew:[String], objective, fishing:{}, prompt, prompt_key, track:{name,text,angle}}
func set_data(d: Dictionary) -> void:
	if d.is_empty():
		return
	_purse_target = int(d["purse"])
	var frac := clampf(float(d["hold_kg"]) / maxf(float(d["cap_kg"]), 1.0), 0.0, 1.0)
	_hold_lbl.text = "Hold  %.1f / %.0f kg" % [float(d["hold_kg"]), float(d["cap_kg"])]
	_hold_bar.value = frac
	var warn := frac >= float(d["warn_frac"])
	(_hold_bar.get_theme_stylebox("fill") as StyleBoxFlat).bg_color = K.AMBER if warn else Color(0.35, 0.72, 0.85)
	if float(d["hold_kg"]) > 0.05:
		var fr := float(d["fresh"])
		_fresh_lbl.text = "Freshness %d%%%s" % [int(roundf(fr * 100.0)), "   (spoiling: sell soon)" if fr < float(d["spoil_warn"]) else ""]
		_fresh_lbl.add_theme_color_override("font_color", K.AMBER if fr < float(d["spoil_warn"]) else K.DIM)
	else:
		_fresh_lbl.text = "The hold is empty"
		_fresh_lbl.add_theme_color_override("font_color", K.DIM)
	var crew: Array = d["crew"]
	_crew_lbl.text = "Crew: none yet" if crew.is_empty() else "Crew (%d): %s" % [crew.size(), ", ".join(PackedStringArray(crew))]
	_obj_lbl.text = str(d["objective"])
	var f: Dictionary = d.get("fishing", {})
	_fish.visible = not f.is_empty()
	if not f.is_empty():
		_fish_title.text = "NETS DOWN"
		_fish_status.text = "%s\n%s" % [str(f["ground"]), str(f["status"])]
		_fish_bar.value = 1.0 - clampf(float(f["next_s"]) / maxf(float(f["interval"]), 1.0), 0.0, 1.0)
		_fish_list.text = str(f["list"])
		_fish_hint.text = "Next haul in %d s     F: haul the nets in" % int(ceilf(float(f["next_s"])))
	var tk: Dictionary = d.get("track", {})
	_track.visible = not tk.is_empty()
	if not tk.is_empty():
		_track_lbl.text = "%s   %s" % [str(tk["name"]), str(tk["text"])]
		(_track_arrow.get_node("Tri") as Polygon2D).rotation = float(tk["angle"])
	var pr := str(d.get("prompt", ""))
	_prompt.visible = pr != ""
	if pr != "":
		_prompt_key.text = str(d.get("prompt_key", "E"))
		_prompt_lbl.text = pr


func _process(delta: float) -> void:
	_t += delta
	if _tag != null:
		_tag.position = Vector2(10.0, size.y - 26.0)
	# the purse counts up or down instead of jumping
	var diff := float(_purse_target) - _purse_shown
	if absf(diff) < 0.5:
		_purse_shown = float(_purse_target)
	else:
		_purse_shown += diff * minf(delta * 5.0, 1.0) + signf(diff) * minf(absf(diff), delta * 4.0)
	_purse.text = "%d reales" % int(roundf(_purse_shown))
	_purse_pulse = maxf(_purse_pulse - delta * 1.2, 0.0)
	var pulse := _purse_pulse > 0.0
	_purse.add_theme_color_override("font_color", K.GREEN.lerp(K.GOLD, 1.0 - _purse_pulse) if pulse else K.GOLD)
	# toasts fade out
	for c in _toasts.get_children():
		var p := c as Control
		var tt := float(p.get_meta("t", 0.0)) - delta
		p.set_meta("t", tt)
		p.modulate.a = clampf(tt / 0.8, 0.0, 1.0)
		if tt <= 0.0:
			_toasts.remove_child(p)
			p.queue_free()
	if _banner.visible:
		_banner_t -= delta
		_banner.modulate.a = clampf(_banner_t / 0.8, 0.0, 1.0)
		_banner.offset_top = 96.0 - 6.0 * sin(_t * 2.0)
		if _banner_t <= 0.0:
			_banner.visible = false
	if _prompt.visible:
		_prompt.modulate.a = 0.82 + 0.18 * sin(_t * 4.0)
