extends Control
# gdlint: disable=class-definitions-order
## The conversation window and the fish counter, built from standard nodes in the style of Stardew Valley's dialogue box:
## a portrait frame on the left, the speaker's name plate, the text typed out letter by letter, and the player's options as
## numbered buttons above the box (keys 1-9, W/S or the arrow keys, Enter / E / Space, or the mouse). Enter on a half-typed
## line finishes it first. It owns no rules: it emits `chosen(index)` and `closed()`, and port_game.gd decides what happens.
const K := preload("res://h2d/ui_kit.gd")
const KeyUtil := preload("res://h2d/key_util.gd")
const PORTRAITS := "res://ui/portraits_atlas.png"
const PORTRAIT_ORDER: Array = ["pip", "tuck", "silas", "garrick", "fishmonger", "fisher", "merchant", "docker", "sailor", "shopkeeper",
		"townsman", "guard", "noble", "tavernkeeper", "clerk", "captain"]
const CELL := 48
const COLS := 4
const CHARS_PER_S := 70.0

signal chosen(index: int)
signal closed()
signal trade_action(action: String, arg: String)

var _dim: ColorRect
var _box: PanelContainer
var _portrait: TextureRect
var _name: Label
var _sub: Label
var _text: Label
var _page_lbl: Label
var _hint: Label
var _choices: VBoxContainer
var _choice_panel: PanelContainer
var _trade: PanelContainer
var _view: Dictionary = {}
var _pages: Array = []
var _page := 0
var _options: Array = []
var _sel := 0
var _typed := 0.0
var _buttons: Array = []
var _mode := ""                      # "" | dialogue | trade
var _atlas: Texture2D = null
var _status: Label
var typed_total := 0                 # characters ever typed (the self-play test checks the text really appears)


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visible = false
	_atlas = K.texture(PORTRAITS)
	_dim = ColorRect.new()
	_dim.color = Color(0.0, 0.0, 0.0, 0.28)
	_dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_dim.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_dim)
	_build_box()
	_build_choices()


func portrait(id: String) -> Texture2D:
	var i := PORTRAIT_ORDER.find(id)
	if i < 0:
		i = PORTRAIT_ORDER.size() - 1
	if _atlas == null:
		return null
	var at := AtlasTexture.new()
	at.atlas = _atlas
	at.region = Rect2((i % COLS) * CELL, (i / COLS) * CELL, CELL, CELL)
	return at


func _build_box() -> void:
	_box = K.panel(Color(0.95, 0.88, 0.70, 0.98), Color(0.45, 0.28, 0.10), 4, 10)
	_box.name = "DialogueBox"
	_box.add_theme_stylebox_override("panel", _parch_style())
	_box.anchor_left = 0.0
	_box.anchor_right = 1.0
	_box.anchor_top = 1.0
	_box.anchor_bottom = 1.0
	_box.offset_left = 40.0
	_box.offset_right = -40.0
	_box.offset_top = -232.0
	_box.offset_bottom = -22.0
	add_child(_box)
	var h := K.box(false, 16)
	_box.add_child(h)
	var frame := K.panel(Color(0.18, 0.12, 0.08), Color(0.45, 0.28, 0.10), 3, 0)
	frame.name = "PortraitFrame"
	frame.custom_minimum_size = Vector2(172, 172)
	h.add_child(frame)
	_portrait = TextureRect.new()
	_portrait.name = "Portrait"
	_portrait.custom_minimum_size = Vector2(160, 160)
	_portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_portrait.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_portrait.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.add_child(_portrait)
	var v := K.box(true, 4)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	var top := K.box(false, 12)
	v.add_child(top)
	_name = K.label("", 34, Color(0.40, 0.18, 0.06), 0, true)
	_name.name = "SpeakerName"
	top.add_child(_name)
	_sub = K.label("", 16, Color(0.40, 0.30, 0.18), 0)
	_sub.name = "SpeakerRole"
	_sub.size_flags_vertical = Control.SIZE_SHRINK_END
	top.add_child(_sub)
	v.add_child(K.rect(Color(0.55, 0.38, 0.18), Vector2(10, 2)))
	_text = K.label("", 21, Color(0.14, 0.09, 0.05), 0)
	_text.name = "SpeechText"
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_text.custom_minimum_size = Vector2(700, 100)
	v.add_child(_text)
	_status = K.label("", 15, Color(0.20, 0.38, 0.12), 0)
	v.add_child(_status)
	var foot := K.box(false, 10)
	v.add_child(foot)
	_hint = K.label("", 14, Color(0.40, 0.30, 0.18), 0)
	_hint.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	foot.add_child(_hint)
	_page_lbl = K.label("", 14, Color(0.40, 0.30, 0.18), 0)
	foot.add_child(_page_lbl)
	_box.gui_input.connect(_on_box_input)
	_box.mouse_filter = Control.MOUSE_FILTER_STOP


func _parch_style() -> StyleBoxFlat:
	var s := K.style(Color(0.95, 0.88, 0.70, 0.98), Color(0.45, 0.28, 0.10), 4, 6, 10)
	s.content_margin_left = 16.0
	s.content_margin_right = 20.0
	s.content_margin_top = 12.0
	s.content_margin_bottom = 10.0
	return s


func _build_choices() -> void:
	_choice_panel = K.panel(Color(0.10, 0.07, 0.05, 0.95), K.GOLD, 3, 8)
	_choice_panel.name = "ChoicePanel"
	_choice_panel.anchor_left = 1.0
	_choice_panel.anchor_right = 1.0
	_choice_panel.anchor_top = 1.0
	_choice_panel.anchor_bottom = 1.0
	_choice_panel.offset_left = -640.0
	_choice_panel.offset_right = -40.0
	_choice_panel.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_choice_panel.offset_bottom = -242.0
	_choice_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_choice_panel)
	_choices = K.box(true, 5)
	_choices.mouse_filter = Control.MOUSE_FILTER_PASS
	_choice_panel.add_child(_choices)


# ---- dialogue -------------------------------------------------------------------------------------------------------
## speaker: {name, sub, portrait}; view: Dialogue.view(...) plus optional `status` {text, color}
func show_view(speaker: Dictionary, view: Dictionary) -> void:
	_mode = "dialogue"
	visible = true
	if _trade != null:
		_trade.queue_free()
		_trade = null
	_box.visible = true
	_dim.visible = true
	_portrait.texture = portrait(str(speaker.get("portrait", "")))
	_name.text = str(speaker.get("name", ""))
	_sub.text = str(speaker.get("sub", ""))
	_view = view
	_pages = view["pages"] as Array
	_options = view["options"] as Array
	_page = 0
	_sel = 0
	for i in _options.size():
		if bool((_options[i] as Dictionary)["enabled"]):
			_sel = i
			break
	var st: Dictionary = view.get("status", {})
	_status.text = str(st.get("text", ""))
	_status.add_theme_color_override("font_color", st.get("color", Color(0.20, 0.38, 0.12)) as Color)
	_start_page()


func _start_page() -> void:
	_text.text = str(_pages[_page])
	_text.visible_characters = 0
	_typed = 0.0
	_refresh_choices()
	_refresh_hint()


func _refresh_hint() -> void:
	var typing := _is_typing()
	var last := _page >= _pages.size() - 1
	if typing:
		_hint.text = "Enter / E: show all the text"
	elif not last or _auto_only():
		_hint.text = "Enter / E: continue"
	else:
		_hint.text = "W / S or Up / Down: choose     Enter / E or 1-%d: confirm     Esc: leave" % maxi(_options.size(), 1)
	_page_lbl.text = "%d / %d" % [_page + 1, _pages.size()] if _pages.size() > 1 else ""


func _refresh_choices() -> void:
	for b in _buttons:
		(b as Node).queue_free()
	_buttons.clear()
	var show := _mode == "dialogue" and not _is_typing() and _page >= _pages.size() - 1 and not _options.is_empty() and not _auto_only()
	_choice_panel.visible = show
	if not show:
		return
	for i in _options.size():
		var o := _options[i] as Dictionary
		var b := K.button("%d.  %s" % [i + 1, str(o["label"])], 18)
		b.name = "Choice%d" % (i + 1)
		b.custom_minimum_size = Vector2(580, 34)
		b.disabled = false
		if not bool(o["enabled"]):
			b.add_theme_color_override("font_color", Color(0.62, 0.55, 0.46))
		b.pressed.connect(_pick.bind(i))
		b.mouse_entered.connect(_hover.bind(i))
		b.mouse_filter = Control.MOUSE_FILTER_STOP
		_choices.add_child(b)
		_buttons.append(b)
	_paint_selection()


func _paint_selection() -> void:
	for i in _buttons.size():
		K.set_button_selected(_buttons[i] as Button, i == _sel)


func _hover(i: int) -> void:
	_sel = i
	_paint_selection()


func _auto_only() -> bool:
	return _options.size() == 1 and bool((_options[0] as Dictionary).get("auto", false))


func _is_typing() -> bool:
	return _mode == "dialogue" and _text.visible_characters >= 0 and _text.visible_characters < _text.text.length()


func _process(delta: float) -> void:
	if _mode != "dialogue" or not visible:
		return
	if _text.visible_characters < _text.text.length():
		_typed += delta * CHARS_PER_S
		var n := int(_typed)
		if n > _text.visible_characters:
			typed_total += n - maxi(_text.visible_characters, 0)
		_text.visible_characters = n
		if n >= _text.text.length():
			_text.visible_characters = -1
			_refresh_choices()
			_refresh_hint()


func finish_typing() -> void:
	if _is_typing():
		typed_total += _text.text.length() - maxi(_text.visible_characters, 0)
		_text.visible_characters = -1
		_refresh_choices()
		_refresh_hint()


## The text currently shown (for tests).
func shown_text() -> String:
	return _text.text if _mode == "dialogue" else ""


func is_open() -> bool:
	return visible


func option_count() -> int:
	return _options.size()


func _pick(i: int) -> void:
	if i < 0 or i >= _options.size():
		return
	var o := _options[i] as Dictionary
	if not bool(o["enabled"]):
		_status.text = str(o["hint"]) if str(o["hint"]) != "" else "That is not possible yet."
		_status.add_theme_color_override("font_color", Color(0.65, 0.18, 0.10))
		return
	chosen.emit(i)


func _on_box_input(ev: InputEvent) -> void:
	var mb := ev as InputEventMouseButton
	if mb != null and mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT:
		confirm()


## Enter / E / Space / click on the box.
func confirm() -> void:
	if _mode != "dialogue":
		return
	if _is_typing():
		finish_typing()
		return
	if _page < _pages.size() - 1:
		_page += 1
		_start_page()
		return
	if _options.is_empty():
		closed.emit()
		return
	_pick(_sel)


func move(delta: int) -> void:
	if _options.is_empty() or _is_typing():
		return
	_sel = (_sel + delta + _options.size()) % _options.size()
	_paint_selection()


## Returns true when the key was used.
# gdlint: disable=max-returns
func handle_key(key: int) -> bool:
	if _mode == "trade":
		return false
	if _mode != "dialogue":
		return false
	if key == KEY_ESCAPE:
		closed.emit()
		return true
	if KeyUtil.is_confirm(key):
		confirm()
		return true
	if key == KEY_W or key == KEY_UP:
		move(-1)
		return true
	if key == KEY_S or key == KEY_DOWN:
		move(1)
		return true
	var d := KeyUtil.digit(key)
	if d >= 0 and not _is_typing() and _page >= _pages.size() - 1 and not _auto_only():
		_sel = clampi(d, 0, maxi(_options.size() - 1, 0))
		_paint_selection()
		_pick(d)
		return true
	return true


func close() -> void:
	_mode = ""
	visible = false
	_choice_panel.visible = false
	if _trade != null:
		_trade.queue_free()
		_trade = null


# ---- the fish counter -----------------------------------------------------------------------------------------------
## d: {speaker, purse, rows:[{key,name,kg,fresh,price,est,level}], board:[{name,price,level}], total, result:{}, keys}
func show_trade(speaker: Dictionary, d: Dictionary) -> void:
	_mode = "trade"
	visible = true
	_box.visible = false
	_choice_panel.visible = false
	if _trade != null:
		_trade.queue_free()
	_trade = K.panel(Color(0.12, 0.08, 0.05, 0.98), K.BORDER, 4, 12)
	_trade.name = "TradePanel"
	_trade.anchor_left = 0.5
	_trade.anchor_right = 0.5
	_trade.anchor_top = 0.5
	_trade.anchor_bottom = 0.5
	_trade.offset_left = -520.0
	_trade.offset_right = 520.0
	_trade.offset_top = -300.0
	_trade.offset_bottom = 300.0
	_trade.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_trade)
	var root := K.box(true, 10)
	_trade.add_child(root)
	var head := K.box(false, 14)
	root.add_child(head)
	var pf := K.panel(Color(0.18, 0.12, 0.08), K.BORDER, 2, 0)
	head.add_child(pf)
	var pt := TextureRect.new()
	pt.custom_minimum_size = Vector2(96, 96)
	pt.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	pt.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	pt.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	pt.texture = portrait(str(speaker.get("portrait", "fishmonger")))
	pt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pf.add_child(pt)
	var hv := K.box(true, 2)
	hv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(hv)
	hv.add_child(K.label("%s  -  the Fish Row counter" % str(speaker.get("name", "")), 34, K.GOLD, 5, true))
	var line := str(d.get("line", ""))
	var ll := K.label(line if line != "" else "Put it on the scale, Captain. I weigh honest.", 17, K.CREAM, 3)
	ll.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ll.custom_minimum_size = Vector2(620, 0)
	hv.add_child(ll)
	var pur := K.panel(Color(0.20, 0.14, 0.06), K.GOLD, 2, 0)
	head.add_child(pur)
	var pv := K.box(true, 0)
	pur.add_child(pv)
	pv.add_child(K.label("YOUR PURSE", 12, K.DIM, 3))
	pv.add_child(K.label("%d reales" % int(d["purse"]), 28, K.GOLD, 5, true))
	root.add_child(K.rect(K.BORDER, Vector2(10, 2)))
	var body := K.box(false, 18)
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(body)
	var res: Dictionary = d.get("result", {})
	if res.is_empty():
		_fill_counter(body, d)
	else:
		_fill_receipt(body, res)
	root.add_child(K.rect(K.BORDER, Vector2(10, 2)))
	var foot := K.box(false, 10)
	root.add_child(foot)
	var back := K.button("Leave the counter   (Esc)", 18)
	back.pressed.connect(func() -> void: trade_action.emit("leave", ""))
	back.mouse_filter = Control.MOUSE_FILTER_STOP
	foot.add_child(back)
	if not res.is_empty():
		var again := K.button("Back to the counter   (Enter)", 18)
		again.pressed.connect(func() -> void: trade_action.emit("back", ""))
		again.mouse_filter = Control.MOUSE_FILTER_STOP
		foot.add_child(again)
	var hint := K.label(str(d.get("keys", "")), 14, K.DIM, 3)
	hint.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	foot.add_child(hint)


func _fill_counter(body: BoxContainer, d: Dictionary) -> void:
	var left := K.box(true, 8)
	left.custom_minimum_size = Vector2(600, 0)
	body.add_child(left)
	left.add_child(K.label("IN YOUR HOLD", 14, K.GOLD, 3))
	var rows: Array = d["rows"]
	if rows.is_empty():
		left.add_child(K.label("The hold is empty. Sail to a fishing ground, lower the nets (F), and come back.", 18, K.DIM, 3))
	else:
		var grid := GridContainer.new()
		grid.columns = 5
		grid.add_theme_constant_override("h_separation", 18)
		grid.add_theme_constant_override("v_separation", 6)
		grid.mouse_filter = Control.MOUSE_FILTER_IGNORE
		left.add_child(grid)
		for t in ["Fish", "kg", "Fresh", "Offer / kg", "Worth"]:
			grid.add_child(K.label(t, 13, K.DIM, 3))
		for r in rows:
			var rd := r as Dictionary
			grid.add_child(K.label("%s %s" % [str(rd["key"]) + ".", str(rd["name"])], 18, K.CREAM, 3))
			grid.add_child(K.label("%.1f" % float(rd["kg"]), 18, K.CREAM, 3))
			var fr := float(rd["fresh"])
			grid.add_child(K.label("%d%%" % int(roundf(fr * 100.0)), 18, K.GREEN if fr >= 0.8 else K.AMBER, 3))
			var lv := float(rd["level"])
			grid.add_child(K.label("%.2f  %s" % [float(rd["price"]), "(low)" if lv < 0.8 else ""], 18, K.AMBER if lv < 0.8 else K.CREAM, 3))
			grid.add_child(K.label("%d" % int(rd["est"]), 18, K.GOLD, 3))
		left.add_child(K.rect(K.BORDER, Vector2(10, 1)))
		var tot := K.label("Everything: about %d reales" % int(d["total"]), 24, K.GOLD, 5, true)
		left.add_child(tot)
		var sell := K.button("SELL EVERYTHING   (Enter / E)", 22)
		sell.custom_minimum_size = Vector2(0, 46)
		sell.mouse_filter = Control.MOUSE_FILTER_STOP
		sell.pressed.connect(func() -> void: trade_action.emit("sell_all", ""))
		left.add_child(sell)
		if rows.size() > 1:
			var rb := K.box(false, 8)
			left.add_child(rb)
			for r in rows:
				var rd2 := r as Dictionary
				var b := K.button("%s: sell %s" % [str(rd2["key"]), str(rd2["name"])], 15)
				b.mouse_filter = Control.MOUSE_FILTER_STOP
				var sp_key := str(rd2["key"])
				b.pressed.connect(func() -> void: trade_action.emit("sell_one", sp_key))
				rb.add_child(b)
	var right := K.box(true, 6)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_child(right)
	right.add_child(K.label("TODAY'S PRICE BOARD  (reales per kg)", 14, K.GOLD, 3))
	for bd in d["board"]:
		var b2 := bd as Dictionary
		var lv2 := float(b2["level"])
		var rowc := K.box(false, 10)
		right.add_child(rowc)
		var nm := K.label(str(b2["name"]), 17, K.CREAM, 3)
		nm.custom_minimum_size = Vector2(130, 0)
		rowc.add_child(nm)
		var pr := K.label("%.2f" % float(b2["price"]), 17, K.GOLD, 3)
		pr.custom_minimum_size = Vector2(52, 0)
		rowc.add_child(pr)
		var bar := ProgressBar.new()
		bar.custom_minimum_size = Vector2(110, 10)
		bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		bar.show_percentage = false
		bar.max_value = 1.0
		bar.value = clampf(lv2, 0.0, 1.0)
		var col := K.GREEN if lv2 >= 0.95 else (K.AMBER if lv2 >= 0.7 else K.RED)
		bar.add_theme_stylebox_override("background", K.style(Color(0.05, 0.04, 0.03), Color(0.3, 0.22, 0.12), 1, 2))
		bar.add_theme_stylebox_override("fill", K.style(col, col, 0, 2))
		bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
		rowc.add_child(bar)
	var note := K.label("A full bar is a fresh market. Sell a lot of one fish and its bar drops; it heals in about six days.", 13, K.DIM, 3)
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	note.custom_minimum_size = Vector2(380, 0)
	right.add_child(note)


func _fill_receipt(body: BoxContainer, res: Dictionary) -> void:
	var v := K.box(true, 8)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_child(v)
	v.add_child(K.label("SOLD", 16, K.GOLD, 3))
	var total := K.label("+%d reales" % int(res["reales"]), 64, K.GREEN, 10, true)
	total.name = "ReceiptTotal"
	v.add_child(total)
	v.add_child(K.label("Purse  %d  ->  %d reales" % [int(res["purse_before"]), int(res["purse_after"])], 24, K.GOLD, 5))
	for r in res["rows"]:
		var rd := r as Dictionary
		v.add_child(K.label("%s   %.1f kg   at %d%% fresh   =   %d reales" % [str(rd["name"]), float(rd["kg"]), int(roundf(float(rd["fresh"]) * 100.0)), int(rd["reales"])], 19, K.CREAM, 3))
	var ln := K.label(str(res["line"]), 18, K.DIM, 3)
	ln.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ln.custom_minimum_size = Vector2(900, 0)
	v.add_child(ln)
