extends CanvasLayer
## Debug console UI (A7). F1 or ` (backtick) toggles it. Debug builds only: it removes itself in an exported release.
## Up/Down = history, Tab = complete a command, Esc = close. Commands live in core/console_commands.gd.
## `state` is the GameState the commands edit; when the real game state exists (J1) call attach_state(real_state).
const Commands := preload("res://core/console_commands.gd")
const GameState := preload("res://core/game_state.gd")
const MAX_HISTORY := 100
const HUD_REFRESH_S := 0.25
const MAX_LIVE_STEP_S := 0.25  # a stalled frame never moves the debug clock by more than this

var commands: RefCounted
var state: RefCounted
var _panel: PanelContainer
var _out: RichTextLabel
var _line: LineEdit
var _history: PackedStringArray = PackedStringArray()
var _hist_pos := 0
var _hud: Label
var _hud_timer := 0.0


func _ready() -> void:
	if not OS.is_debug_build():
		queue_free()
		return
	layer = 100
	process_mode = Node.PROCESS_MODE_ALWAYS
	state = GameState.new()
	var data := get_node_or_null("/root/Data")
	if data == null:
		push_error("DebugConsole: autoload 'Data' is missing")
		queue_free()
		return
	commands = Commands.new(data, state, get_node_or_null("/root/Quality"), get_node_or_null("/root/Log"))
	_build_ui()
	_panel.visible = false
	set_process(true)
	_print("[color=#ffd9a0]Crown of the Seas debug console.[/color] Type 'help'. F1 or ` closes it.")


func attach_state(new_state: RefCounted) -> void:
	state = new_state
	commands.state = new_state


func _build_ui() -> void:
	_panel = PanelContainer.new()
	add_child(_panel)
	_panel.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_panel.offset_bottom = 300.0
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.05, 0.07, 0.1, 0.92)
	_panel.add_theme_stylebox_override("panel", style)
	var box := VBoxContainer.new()
	_panel.add_child(box)
	_out = RichTextLabel.new()
	_out.bbcode_enabled = true
	_out.scroll_following = true
	_out.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_child(_out)
	_hud = Label.new()
	_hud.visible = false
	_hud.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	_hud.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_hud.add_theme_color_override("font_color", Color(1.0, 0.85, 0.63))
	_hud.add_theme_color_override("font_outline_color", Color(0.05, 0.07, 0.1))
	_hud.add_theme_constant_override("outline_size", 4)
	add_child(_hud)
	_line = LineEdit.new()
	_line.placeholder_text = "command (try: help)"
	_line.text_submitted.connect(_on_submit)
	box.add_child(_line)


## Debug live clock (`time live on`): real frame time drives the ONE world clock; pauses are honoured by tick().
func _process(delta: float) -> void:
	if commands == null or _hud == null:
		return
	if commands.live:
		state.tick(minf(delta, MAX_LIVE_STEP_S))
	_hud.visible = commands.live
	_hud_timer += delta
	if commands.live and _hud_timer >= HUD_REFRESH_S:
		_hud_timer = 0.0
		_hud.text = commands.hud_text()


func _print(bbcode: String) -> void:
	_out.append_text(bbcode + "\n")


static func _escape(text: String) -> String:
	return text.replace("[", "[lb]")


func _toggle() -> void:
	_panel.visible = not _panel.visible
	if _panel.visible:
		_line.clear()
		_line.grab_focus()
	else:
		_line.release_focus()


func _input(event: InputEvent) -> void:
	if _panel == null or not (event is InputEventKey):
		return
	var k := event as InputEventKey
	if not k.pressed or k.echo:
		return
	if k.keycode == KEY_F1 or k.keycode == KEY_QUOTELEFT:
		_toggle()
		get_viewport().set_input_as_handled()
		return
	if not _panel.visible:
		return
	match k.keycode:
		KEY_ESCAPE:
			_toggle()
		KEY_UP:
			_history_step(-1)
		KEY_DOWN:
			_history_step(1)
		KEY_TAB:
			_complete()
		_:
			return
	get_viewport().set_input_as_handled()


func _history_step(delta: int) -> void:
	if _history.is_empty():
		return
	_hist_pos = clampi(_hist_pos + delta, 0, _history.size())
	_line.text = "" if _hist_pos >= _history.size() else _history[_hist_pos]
	_line.caret_column = _line.text.length()


func _complete() -> void:
	var text := _line.text
	if " " in text:
		return
	var matches: PackedStringArray = commands.complete(text)
	if matches.is_empty():
		return
	if matches.size() == 1:
		_line.text = matches[0] + " "
	else:
		_print(", ".join(matches))
		_line.text = _common_prefix(matches)
	_line.caret_column = _line.text.length()


static func _common_prefix(items: PackedStringArray) -> String:
	var prefix := items[0]
	for s in items:
		while not s.begins_with(prefix):
			prefix = prefix.left(prefix.length() - 1)
	return prefix


func _on_submit(text: String) -> void:
	_line.clear()
	if text.strip_edges() == "":
		return
	_history.append(text)
	if _history.size() > MAX_HISTORY:
		_history.remove_at(0)
	_hist_pos = _history.size()
	_print("[color=#9be0c0]> %s[/color]" % _escape(text))
	var r: Dictionary = commands.execute(text)
	if r.get("clear", false):
		_out.clear()
	elif str(r["text"]) != "":
		var col := "#e8e8e8" if r["ok"] else "#ff7a6b"
		_print("[color=%s]%s[/color]" % [col, _escape(str(r["text"]))])
	_line.grab_focus()
