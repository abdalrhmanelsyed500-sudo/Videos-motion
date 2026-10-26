extends CanvasLayer
## Arcade HUD (ART_BIBLE §4): oversized italic timer, LED fare panel, speed, destination line,
## toasts, offer card, result card, on-screen direction triangle. Reads signals only - no logic.

var world = null
var _timer: Label
var _fare: Label
var _speed: Label
var _dest: Label
var _toast: Label
var _offer: PanelContainer
var _offer_text: Label
var _result: PanelContainer
var _result_text: Label
var _needle: Polygon2D
var _last_result: Dictionary = {}


func _ready() -> void:
	layer = 10
	_timer = _label("Timer", Vector2(24, 8), 44, Color("ffe14d"))
	_fare = _label("Fare", Vector2(980, 12), 26, Color("ff5533"))
	_speed = _label("Speed", Vector2(980, 48), 22, Color.WHITE)
	_dest = _label("Dest", Vector2(24, 64), 20, Color("8ef0a0"))
	_toast = _label("Toast", Vector2(340, 640), 22, Color("ffe14d"))
	_offer = _card(Vector2(330, 240), 620, 180)
	_offer_text = _offer.get_node("Text") as Label
	_result = _card(Vector2(330, 200), 620, 260)
	_result_text = _result.get_node("Text") as Label
	_offer.visible = false
	_result.visible = false
	_needle = Polygon2D.new()
	_needle.polygon = PackedVector2Array([
		Vector2(0, -18), Vector2(12, 10), Vector2(0, 4), Vector2(-12, 10)])
	_needle.position = Vector2(640, 620)
	_needle.color = Color("3ddc55")
	add_child(_needle)
	MissionMgr.offer_shown.connect(_on_offer)
	MissionMgr.driving_started.connect(_on_driving)
	MissionMgr.mission_result.connect(_on_result)
	MissionMgr.toast.connect(show_toast)
	Tk.balance_changed.connect(_on_balance)
	_fare.text = "%s %d" % [str(Reg.tuning().get("symbol_en", "E£")), int(Tk.balance)]


func _label(name: String, pos: Vector2, size: int, col: Color) -> Label:
	var l := Label.new()
	l.name = name
	l.position = pos
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", col)
	l.add_theme_color_override("font_outline_color", Color.BLACK)
	l.add_theme_constant_override("outline_size", 6)
	add_child(l)
	return l


func _card(pos: Vector2, w: float, h: float) -> PanelContainer:
	var p := PanelContainer.new()
	p.position = pos
	p.custom_minimum_size = Vector2(w, h)
	var st := StyleBoxFlat.new()
	st.bg_color = Color("2e2218ee")
	st.border_color = Color("c49e4a")
	st.set_border_width_all(3)
	st.set_content_margin_all(14)
	p.add_theme_stylebox_override("panel", st)
	var t := Label.new()
	t.name = "Text"
	t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	t.add_theme_font_size_override("font_size", 20)
	p.add_child(t)
	add_child(p)
	return p


func bind_world(w: Node3D) -> void:
	world = w


func show_toast(text: String) -> void:
	_toast.text = text
	var tw := create_tween()
	tw.tween_interval(2.2)
	tw.tween_callback(func() -> void: _toast.text = "")


func _on_offer(info: Dictionary) -> void:
	_offer.visible = true
	_offer_text.text = "%s\n\"%s\"\nTo: %s  (%d m)\nTime: %d s   [E] accept" % [
		str(info.get("name", "")), str(info.get("line", "")), str(info.get("dest", "")),
		int(info.get("dist_m", 0)), int(info.get("time_s", 0))]


func _on_driving(info: Dictionary) -> void:
	_offer.visible = false
	_dest.text = "To: %s  (%d m)" % [str(info.get("dest", "")), int(info.get("dist_m", 0))]


func _on_result(result: Dictionary) -> void:
	_last_result = result
	_result.visible = true
	var b: Dictionary = result.get("breakdown", {})
	var sym: String = str(Reg.tuning().get("symbol_en", "E£"))
	if bool(result.get("success", false)):
		var fmt := "DELIVERED!\nFare %s%d = base %s%d + dist %s%d + time %s%d"
		fmt += " + clean %s%d + drift %s%d + shortcut %s%d - hits %s%d\nBalance %s%d  [E] next"
		_result_text.text = fmt % [
			sym, int(result.get("reward", 0)), sym, int(b.get("base", 0)),
			sym, int(b.get("distance", 0)), sym, int(b.get("time_left", 0)),
			sym, int(b.get("clean", 0)), sym, int(b.get("drift", 0)),
			sym, int(b.get("shortcut", 0)),
			sym, int(b.get("penalty", 0)), sym, int(Tk.balance)]
	else:
		var fmt2 := "TOO SLOW - passenger walked off.\nReputation took a hit.\n"
		fmt2 += "Balance %s%d   [E] next passenger"
		_result_text.text = fmt2 % [sym, int(Tk.balance)]
	_dest.text = ""


func _on_balance(v: float) -> void:
	_fare.text = "%s %d" % [str(Reg.tuning().get("symbol_en", "E£")), int(v)]


func _process(_delta: float) -> void:
	if world == null:
		return
	var st: int = MissionMgr.state
	if st == MissionMgr.State.DRIVING:
		_timer.text = "%02d:%02d" % [int(MissionMgr.time_left_s) / 60, int(MissionMgr.time_left_s) % 60]
		var tuktuk: Node3D = world.get("tuktuk")
		if tuktuk != null:
			_speed.text = "%d km/h" % int(absf(float(tuktuk.get("speed"))) * 3.6)
			var dest: Vector3 = world.get("_dest_marker")
			var rel := Vector2(tuktuk.global_position.x - dest.x,
				tuktuk.global_position.z - dest.z)
			var d2: float = rel.length()
			_dest.text = "To: %s  (%d m)" % [MissionMgr.dest_name, int(d2)]
			_needle.rotation = _heading_to(tuktuk, dest)
			_needle.visible = true
	else:
		_timer.text = ""
		_needle.visible = false
	if st != MissionMgr.State.RESULT:
		_result.visible = false
	if st != MissionMgr.State.OFFER:
		_offer.visible = false


func _heading_to(tuktuk: Node3D, dest: Vector3) -> float:
	var to_dest := Vector2(dest.x - tuktuk.global_position.x, dest.z - tuktuk.global_position.z)
	var fwd := Vector2(-sin(float(tuktuk.get("yaw"))), -cos(float(tuktuk.get("yaw"))))
	return atan2(to_dest.x, -to_dest.y) - atan2(fwd.x, -fwd.y)
