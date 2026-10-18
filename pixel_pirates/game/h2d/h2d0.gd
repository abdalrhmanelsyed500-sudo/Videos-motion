extends Node
## H2D-0: one playable HD-2D ocean scene. The simulation is the validated E1 one (Ocean, SeaState, world clock, weather
## smoothing); only the PICTURE changed, behind the single SeaView interface (3D Compatibility path or 2D fallback).
## Keys: A/D steer | 1-7 weather checkpoints (1 squall, 2 fair, 4 fog, 5 swell, 6 gale, 7 ice) | P pause | R reset ship
##       F1 quality (Dev-Lite / Standard / Ultra) | F2 path (3D / 2D) | F3 HUD | F4 flip colour transfer | F12 shot
##       [ ] camera pitch | - = exposure | , . visual speed | B benchmark (about 80 s)
## Start from the project folder with tools\run_h2d0.bat. NOT YET RUN IN GODOT.
const Ocean := preload("res://core/ocean.gd")
const SeaState := preload("res://core/sea_state.gd")
const VoyageClock := preload("res://core/voyage_clock.gd")
const GameState := preload("res://core/game_state.gd")
const DataLoader := preload("res://core/data_loader.gd")
const SeaView := preload("res://h2d/sea_view.gd")
const View3D := preload("res://h2d/sea_view_3d.gd")
const View2D := preload("res://h2d/sea_view_2d.gd")
const ShipSprite := preload("res://h2d/ship_sprite.gd")
const Bench := preload("res://h2d/bench.gd")
const TURN_DEG_PER_S := 14.0
const MAX_STEP_S := 0.25
const SMOOTH_S := 2.0
const START_POS := Vector2(-150.0, 190.0)
const START_HEADING := 39.0
const SMOOTH_KEYS: Array[String] = ["wind_kn", "wave_m", "visibility_km", "cloud", "storm", "herald", "rain", "fog",
		"ice", "sst_c", "air_c", "light_peak", "light_floor", "speed_kn"]
const COMPASS: Array[String] = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
const QUALITIES: Array[String] = ["dev_lite", "standard", "ultra"]

var _state: RefCounted
var _sea: RefCounted
var _oc: RefCounted
var _route: Array = []
var _starts: Array = []
var _d: Dictionary = {}
var _look: Dictionary = {}
var _look_target: Dictionary = {}
var _look_t := 0.0
var _heading_disp := 0.0
var _hour := 6.0
var _light := 1.0
var _real := 0.0
var _turn := 0.0
var _pos := START_POS
var _speed_mul := 1.0
var _grounded := false
var _fps := 0.0
var _hud: Label
var _hud_on := true
var _hud_t := 0.0
var _banner := ""
var _banner_until := 0.0
var _v3: SeaView
var _v2: SeaView
var _active: SeaView
var _region_id := ""
var _shot_n := 0
var _bench: RefCounted = null
var _bench_cli := false
var _vsync_saved := 0


func _ready() -> void:
	_state = GameState.new()
	_sea = SeaState.new(Ocean.load_default())
	_oc = _sea.ocean
	_route = DataLoader.load_dict("res://data/world/slice_route.json").get("checkpoints", [])
	for k in ["time.dawn_start_hour", "time.morning_start_hour", "time.day_start_hour", "time.sunset_start_hour",
			"time.evening_start_hour", "time.night_start_hour"]:
		_starts.append(_oc.tuning_value(k))
	_v3 = View3D.new()
	add_child(_v3)
	_v3.setup(self)
	_v2 = View2D.new()
	add_child(_v2)
	_v2.setup(self)
	var layer := CanvasLayer.new()
	layer.layer = 10
	add_child(layer)
	_hud = Label.new()
	_hud.position = Vector2(10.0, 8.0)
	_hud.add_theme_font_size_override("font_size", 15)
	_hud.add_theme_color_override("font_color", Color(1.0, 0.97, 0.88))
	_hud.add_theme_color_override("font_outline_color", Color(0.05, 0.08, 0.1))
	_hud.add_theme_constant_override("outline_size", 5)
	layer.add_child(_hud)
	_jump(2)
	_reset_ship()
	_set_path("3d")
	_bench_cli = OS.get_cmdline_user_args().has("--bench")
	await (_v3 as View3D).calibrate_gamma()
	_say((_v3 as View3D).calibration_note)
	if _bench_cli:
		_start_bench()


# ---- world -------------------------------------------------------------------------------------------------------
func _jump(number: int) -> void:
	for c in _route:
		if int(c["id"]) == number:
			var keep: float = _sea.heading_deg
			_sea.place(float(c["x_km"]), float(c["y_km"]), float(c["heading_deg"]))
			_sea.heading_deg = keep
			_state.t_seconds = roundi(float(c["t_days"]) * 86400.0)
			_state.clock.set_location("sea")
			_region_id = ""
			_d.clear()


func _reset_ship() -> void:
	_pos = START_POS
	_sea.heading_deg = START_HEADING
	_heading_disp = START_HEADING
	_turn = 0.0
	_grounded = false


func _set_path(which: String) -> void:
	_active = _v3 if which == "3d" else _v2
	_v3.set_active(which == "3d")
	_v2.set_active(which == "2d")


func _say(text: String) -> void:
	_banner = text
	_banner_until = _real + 6.0
	print("H2D0 ", text)


# ---- frame -------------------------------------------------------------------------------------------------------
func _process(delta: float) -> void:
	_real += delta
	_fps = lerpf(_fps, 1.0 / maxf(delta, 0.0001), 0.05)
	if _bench != null and (_bench as Bench).active:
		(_bench as Bench).step(delta, self)
		if not (_bench as Bench).active:
			_finish_bench()
	var dt := minf(delta, MAX_STEP_S)
	var steer := _steer_axis()
	_sea.heading_deg = fposmod(_sea.heading_deg + steer * TURN_DEG_PER_S * dt, 360.0)
	_turn = lerpf(_turn, steer * TURN_DEG_PER_S, 1.0 - exp(-dt / 0.25))
	var t0 := float(_state.clock.t) / 86400.0
	var gs: float = _state.tick(dt)
	if _sea.last_sample.is_empty():
		_sea.refresh(t0)
	_smooth(dt)
	var speed_scene := ShipSprite.scene_speed_ms(float(_d["speed_kn"])) * _speed_mul
	if gs > 0.0:
		var hd := deg_to_rad(_sea.heading_deg)
		var np := _pos + Vector2(sin(hd), -cos(hd)) * speed_scene * dt
		if _v3.land_height_at(np.x, np.y) > 0.3:
			_grounded = true
		else:
			_grounded = false
			_pos = np
			_sea.advance(t0, gs)
	if _grounded:
		speed_scene = 0.0
	_update_light(float(_state.clock.t) / 86400.0)
	_update_region()
	_active.update_view(_view(), {"x": _pos.x, "z": _pos.y, "heading_deg": _heading_disp,
			"speed_kn": float(_d["speed_kn"]), "scene_speed": speed_scene}, delta)
	_hud_t -= delta
	if _hud_t <= 0.0:
		_hud_t = 0.2
		_draw_hud(speed_scene)


func _steer_axis() -> float:
	if _bench != null and (_bench as Bench).active:
		return 0.55 * sin(_real * 0.9)
	var axis := 0.0
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
		axis -= 1.0
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
		axis += 1.0
	return axis


func _smooth(dt: float) -> void:
	var smp: Dictionary = _sea.last_sample
	var k := 1.0 - exp(-dt / SMOOTH_S)
	var first := _d.is_empty()
	for key in SMOOTH_KEYS:
		var target: float = _sea.speed_kn() if key == "speed_kn" else float(smp[key])
		_d[key] = target if first else lerpf(float(_d[key]), target, k)
	var wf := deg_to_rad(float(smp["wind_from_deg"]))
	_d["wind_from"] = rad_to_deg(wf) if first else rad_to_deg(lerp_angle(deg_to_rad(float(_d["wind_from"])), wf, k))
	var hk := 1.0 - exp(-dt / 0.35)
	_heading_disp = rad_to_deg(lerp_angle(deg_to_rad(_heading_disp), deg_to_rad(_sea.heading_deg), hk))
	_look_t -= dt
	if _look_t <= 0.0 or _look.is_empty():
		_look_t = 2.0
		_look_target = _oc.look_at(_sea.x_km, _sea.y_km)
		if _look.is_empty():
			_look = _look_target.duplicate(true)
	_look = _lerp_look(_look, _look_target, k)


func _lerp_look(a: Dictionary, b: Dictionary, k: float) -> Dictionary:
	var out: Dictionary = {}
	for key in b.keys():
		if b[key] is Array:
			var arr: Array = []
			for i in (b[key] as Array).size():
				arr.append(lerpf(float((a[key] as Array)[i]), float((b[key] as Array)[i]), k))
			out[key] = arr
		else:
			out[key] = lerpf(float(a[key]), float(b[key]), k)
	return out


func _update_light(t_days: float) -> void:
	_hour = 24.0 * (t_days - floorf(t_days))
	var dl := VoyageClock.daylight(_hour, _starts, _oc.tuning_value("light.night_floor"),
			_oc.tuning_value("light.dawn_end_level"), _oc.tuning_value("light.sunset_end_level"))
	_light = maxf(float(_d["light_floor"]), dl * float(_d["light_peak"]))


func _update_region() -> void:
	var rid := str(_sea.last_sample["region"])
	if rid != _region_id:
		_region_id = rid


func _view() -> Dictionary:
	var v: Dictionary = _d.duplicate()
	v["light"] = _light
	v["floor"] = float(_d["light_floor"])
	v["hour"] = _hour
	v["time"] = _real
	v["look"] = _look
	v["wind_from_deg"] = float(_d["wind_from"])
	v["heading_deg"] = _heading_disp
	v["speed_kn"] = float(_d["speed_kn"])
	v["turn"] = _turn
	v["lat"] = float(_sea.last_sample["lat"])
	return v


# ---- input -------------------------------------------------------------------------------------------------------
func _unhandled_input(event: InputEvent) -> void:
	var k := event as InputEventKey
	if k == null or not k.pressed or k.echo:
		return
	var v3 := _v3 as View3D
	if k.keycode >= KEY_1 and k.keycode <= KEY_7:
		_jump(int(k.keycode) - int(KEY_1) + 1)
	elif k.keycode == KEY_P:
		var reason := "menu"
		if _state.clock.pause_reasons().has(reason):
			_state.clock.resume(reason)
		else:
			_state.clock.pause(reason)
	elif k.keycode == KEY_R:
		_reset_ship()
	elif k.keycode == KEY_F1:
		var q: String = QUALITIES[(QUALITIES.find(v3.quality) + 1) % QUALITIES.size()]
		v3.set_quality(q)
		_say("quality: " + q)
	elif k.keycode == KEY_F2:
		_set_path("2d" if _active == _v3 else "3d")
		_say("path: " + _active.path_name())
	elif k.keycode == KEY_F3:
		_hud_on = not _hud_on
	elif k.keycode == KEY_F4:
		v3.set_gamma(1.0 if v3.gamma > 1.5 else 2.2)
		_say("colour transfer flipped: h2d_gamma %.1f (press F4 again if it looks washed out or too dark)" % v3.gamma)
	elif k.keycode == KEY_F12:
		_shot_n += 1
		var img := get_viewport().get_texture().get_image()
		img.save_png("user://h2d0_shot_%03d.png" % _shot_n)
		_say("saved " + ProjectSettings.globalize_path("user://h2d0_shot_%03d.png" % _shot_n))
	elif k.keycode == KEY_BRACKETLEFT:
		v3.adjust_pitch(-3.0)
	elif k.keycode == KEY_BRACKETRIGHT:
		v3.adjust_pitch(3.0)
	elif k.keycode == KEY_MINUS:
		v3.adjust_exposure(1.0 / 1.1)
	elif k.keycode == KEY_EQUAL:
		v3.adjust_exposure(1.1)
	elif k.keycode == KEY_COMMA:
		_speed_mul = maxf(_speed_mul * 0.5, 0.125)
	elif k.keycode == KEY_PERIOD:
		_speed_mul = minf(_speed_mul * 2.0, 8.0)
	elif k.keycode == KEY_B and (_bench == null or not (_bench as Bench).active):
		_start_bench()


# ---- benchmark ---------------------------------------------------------------------------------------------------
func _start_bench() -> void:
	_vsync_saved = DisplayServer.window_get_vsync_mode()
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	_bench = Bench.new()
	(_bench as Bench).start(self)
	_say("benchmark started: about 80 s, do not touch the keyboard or mouse")


func bench_apply(phase: Dictionary) -> void:
	_set_path(str(phase["path"]))
	if str(phase["path"]) == "3d":
		(_v3 as View3D).set_quality(str(phase["quality"]))
	_jump(int(phase["cp"]))
	_reset_ship()


func bench_capture() -> Image:
	return get_viewport().get_texture().get_image()


func _info() -> Dictionary:
	var mem: Dictionary = OS.get_memory_info()
	return {
		"godot": Engine.get_version_info()["string"], "os": OS.get_name(),
		"gpu": RenderingServer.get_video_adapter_name(), "gpu_vendor": RenderingServer.get_video_adapter_vendor(),
		"gpu_api": RenderingServer.get_video_adapter_api_version(),
		"renderer": "%s / %s" % [RenderingServer.get_current_rendering_method(),
				RenderingServer.get_current_rendering_driver_name()],
		"cpu": OS.get_processor_name(), "cpu_threads": OS.get_processor_count(),
		"ram_mb": int(float(mem.get("physical", 0)) / 1048576.0),
		"window": str(DisplayServer.window_get_size()), "colour_transfer": (_v3 as View3D).calibration_note,
	}


func _finish_bench() -> void:
	DisplayServer.window_set_vsync_mode(_vsync_saved as DisplayServer.VSyncMode)
	var lines: Array[String] = (_bench as Bench).report(_info())
	var f := FileAccess.open(Bench.REPORT_PATH, FileAccess.WRITE)
	for line in lines:
		print("H2D0BENCH ", line)
		if f != null:
			f.store_line(line)
	print("H2D0BENCH report file: ", ProjectSettings.globalize_path(Bench.REPORT_PATH))
	_set_path("3d")
	_say("benchmark finished: " + ProjectSettings.globalize_path(Bench.REPORT_PATH))
	if _bench_cli:
		get_tree().quit(0)


# ---- HUD ---------------------------------------------------------------------------------------------------------
func _compass(deg: float) -> String:
	return COMPASS[int(floorf(fposmod(deg, 360.0) / 45.0 + 0.5)) % 8]


func _region_name() -> String:
	for r in _oc.regions:
		if str(r["id"]) == _region_id:
			return str(r["name"])
	return ""


func _draw_hud(speed_scene: float) -> void:
	_hud.visible = _hud_on
	if not _hud_on:
		return
	var hd := fposmod(_sea.heading_deg, 360.0)
	var wind_from := float(_d["wind_from"])
	var off := absf(fposmod(_sea.heading_deg - wind_from + 540.0, 360.0) - 180.0)
	var lines: Array[String] = []
	lines.append("CROWN OF THE SEAS - H2D-0   [%s]   %.0f fps" % [_active.describe(), _fps])
	lines.append("%s   %02d:%02d   wind %.0f kn from %s   waves %.1f m   visibility %.1f km" % [
			_region_name(), int(_hour), int((_hour - floorf(_hour)) * 60.0), float(_d["wind_kn"]),
			_compass(wind_from), float(_d["wave_m"]), float(_d["visibility_km"])])
	lines.append("heading %03d %s   %.1f kn   scene %.1f m/s (x%.2f)   sail row %d   frame %d/16" % [
			int(hd), _compass(hd), float(_d["speed_kn"]), speed_scene, _speed_mul,
			ShipSprite.trim_row(_heading_disp, wind_from), ShipSprite.heading_frame(_heading_disp)])
	lines.append("rain %.2f  storm %.2f  fog %.2f  ice %.2f  swell warning %.2f" % [
			float(_d["rain"]), float(_d["storm"]), float(_d["fog"]), float(_d["ice"]), float(_d["herald"])])
	if off < _oc.tuning_value("ship.no_go_deg") and float(_d["wind_kn"]) > 3.0:
		lines.append("IN IRONS: head to wind (%.0f deg off it). Bear away with A or D" % off)
	if _grounded:
		lines.append("AGROUND on Anvil Cay: turn away with A or D, or press R")
	if _state.clock.is_paused():
		lines.append("PAUSED")
	if _bench != null and (_bench as Bench).active:
		lines.append("BENCHMARK " + (_bench as Bench).current_label())
	if _real < _banner_until:
		lines.append(_banner)
	lines.append("A/D steer  1-7 weather  P pause  R reset  F1 quality  F2 3D/2D  F3 HUD  F4 colour  F12 shot  B bench")
	_hud.text = "\n".join(PackedStringArray(lines))
