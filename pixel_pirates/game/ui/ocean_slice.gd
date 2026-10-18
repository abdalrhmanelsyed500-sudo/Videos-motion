extends Node2D
## E1 vertical slice "The Three Weathers": sail the ship across the living ocean (core/ocean.gd), watch the sky, sea,
## wildlife and the Herald Swell, and keep a journal. Plain 2D drawing at 640 x 360 logical pixels (scale 2), so it
## runs on the dev PC (Intel HD 3000). All numbers come from core/ocean.gd, core/wildlife.gd, core/sea_state.gd and
## the one world clock in core/game_state.gd; this scene only steers, draws and writes the HUD.
## Run: godot --path game res://ui/ocean_slice.tscn   (or tools/run_slice.bat)
## Keys: A/D steer, P pause, M chart (pauses the clock, as a planning screen does), 1-7 DEBUG jump to a checkpoint
## (never time acceleration), N chart reveal-all (debug), F1 or ` console (`route`, `ocean`, `time` commands work).
## NOT YET RUN IN GODOT: the first run on the dev PC is the first test (see docs/E1_WORLD_SPEC.md checklist).
const Ocean := preload("res://core/ocean.gd")
const SeaState := preload("res://core/sea_state.gd")
const Wildlife := preload("res://core/wildlife.gd")
const VoyageClock := preload("res://core/voyage_clock.gd")
const GameState := preload("res://core/game_state.gd")
const DataLoader := preload("res://core/data_loader.gd")
const Painter := preload("res://ui/sea_painter.gd")
const TURN_DEG_PER_S := 14.0
const MAX_STEP_S := 0.25
const SMOOTH_S := 2.0
const CHART_CELL_KM := 60.0
const REVEAL_RADIUS := 2
const REVEAL_PER_FRAME := 30
const REACH_KM := 40.0
const SIGHT_EVERY_S := 1.0
const BERG_EVERY_S := 1.5
const BERG_RADIUS_KM := 14.0
const CRITTER_LIFE_S := 40.0
const BANNER_S := 7.0
const SMOOTH_KEYS: Array[String] = ["wind_kn", "wave_m", "visibility_km", "cloud", "storm", "herald", "rain", "fog",
		"ice", "sst_c", "air_c", "light_peak", "light_floor", "speed_kn"]
const COMPASS: Array[String] = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

var _state: RefCounted
var _sea: RefCounted
var _oc: RefCounted
var _commands: RefCounted = null
var _species: Array = []
var _species_by_id: Dictionary = {}
var _route: Array = []
var _reached: Dictionary = {}
var _d: Dictionary = {}
var _look: Dictionary = {}
var _look_target: Dictionary = {}
var _heading_disp := 0.0
var _starts: Array = []
var _light := 1.0
var _hour := 6.0
var _real := 0.0
var _region_id := ""
var _banner := ""
var _banner_at := -100.0
var _critters: Array = []
var _bergs: Array = []
var _seen_keys: Dictionary = {}
var _journal: Dictionary = {}
var _journal_log: Array[String] = []
var _sight_t := 0.0
var _berg_t := 0.0
var _look_t := 0.0
var _show_chart := false
var _chart_img: Image
var _chart_tex: ImageTexture
var _chart_known := PackedByteArray()
var _chart_known_n := 0
var _chart_queue: Array[int] = []
var _chart_cols := 0
var _chart_rows := 0
var _chart_cell := Vector2i(-1, -1)
var _chart_dirty := false
var _labels: Array = []
var _fps := 0.0


func _ready() -> void:
	scale = Vector2(2.0, 2.0)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var dc: Node = get_node_or_null("/root/DebugConsole")
	if dc != null and dc.get("commands") != null:
		_commands = dc.get("commands")
		_state = dc.get("state")
		_sea = _commands.ensure_sea()
	else:
		_state = GameState.new()
		_sea = SeaState.new(Ocean.load_default())
	_oc = _sea.ocean
	_species = Wildlife.load_species()
	for sp in _species:
		_species_by_id[str(sp["id"])] = sp
	_route = DataLoader.load_dict("res://data/world/slice_route.json").get("checkpoints", [])
	for k in ["time.dawn_start_hour", "time.morning_start_hour", "time.day_start_hour", "time.sunset_start_hour",
			"time.evening_start_hour", "time.night_start_hour"]:
		_starts.append(_oc.tuning_value(k))
	for r in _oc.regions:
		var sd: Dictionary = r["seed"]
		_labels.append([str(r["name"]), float(sd["x_km"]), float(sd["y_km"]), false])
	_init_chart()
	_jump(1)


func _jump(number: int) -> void:
	for c in _route:
		if int(c["id"]) == number:
			_sea.place(float(c["x_km"]), float(c["y_km"]), float(c["heading_deg"]))
			_state.t_seconds = roundi(float(c["t_days"]) * 86400.0)
			_state.clock.set_location("sea")
			_heading_disp = float(c["heading_deg"])
			_region_id = ""
			_critters.clear()
			_d.clear()


func _unhandled_input(event: InputEvent) -> void:
	var k := event as InputEventKey
	if k == null or not k.pressed or k.echo:
		return
	if k.keycode >= KEY_1 and k.keycode <= KEY_7:
		_jump(int(k.keycode) - int(KEY_1) + 1)
	elif k.keycode == KEY_P:
		_toggle_pause("menu")
	elif k.keycode == KEY_M:
		_show_chart = not _show_chart
		if _show_chart:
			_state.clock.pause("planning")
		else:
			_state.clock.resume("planning")
	elif k.keycode == KEY_N and _show_chart:
		for i in _chart_cols * _chart_rows:
			if _chart_known[i] == 0:
				_chart_queue.append(i)


func _toggle_pause(reason: String) -> void:
	if _state.clock.pause_reasons().has(reason):
		_state.clock.resume(reason)
	else:
		_state.clock.pause(reason)


# ---- per frame -----------------------------------------------------------------------------------
func _process(delta: float) -> void:
	_real += delta
	_fps = lerpf(_fps, 1.0 / maxf(delta, 0.0001), 0.05)
	var dt := minf(delta, MAX_STEP_S)
	if _commands != null:
		_commands.live = false  # this scene runs the clock; the console's own live clock would double the time
	if not _show_chart:
		var steer := 0.0
		if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
			steer -= 1.0
		if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
			steer += 1.0
		_sea.heading_deg = fposmod(_sea.heading_deg + steer * TURN_DEG_PER_S * dt, 360.0)
	var t0 := float(_state.clock.t) / 86400.0
	var gs: float = _state.tick(dt)
	if _sea.last_sample.is_empty():
		_sea.refresh(t0)
	if gs > 0.0:
		_sea.advance(t0, gs)
	var t_days := float(_state.clock.t) / 86400.0
	_smooth(dt)
	_update_light(t_days)
	_update_region()
	_update_checkpoints()
	_update_wildlife(delta, t_days)
	_update_chart()
	queue_redraw()


func _smooth(dt: float) -> void:
	var smp: Dictionary = _sea.last_sample
	var k := 1.0 - exp(-dt / SMOOTH_S)
	var first := _d.is_empty()
	for key in SMOOTH_KEYS:
		var target: float = _sea.speed_kn() if key == "speed_kn" else float(smp[key])
		_d[key] = target if first else lerpf(float(_d[key]), target, k)
	var wf := deg_to_rad(float(smp["wind_from_deg"]))
	_d["wind_from"] = rad_to_deg(wf) if first else rad_to_deg(lerp_angle(deg_to_rad(float(_d["wind_from"])), wf, k))
	_heading_disp = rad_to_deg(lerp_angle(deg_to_rad(_heading_disp), deg_to_rad(_sea.heading_deg), 1.0 - exp(-dt / 0.35)))
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
	if rid == _region_id:
		return
	_region_id = rid
	for r in _oc.regions:
		if str(r["id"]) == rid:
			var haz: Array = r["hazards"]
			_banner = "%s\n%s" % [r["name"], ", ".join(PackedStringArray(haz))]
			_banner_at = _real
			for lb in _labels:
				if lb[0] == str(r["name"]):
					lb[3] = true


func _update_checkpoints() -> void:
	for c in _route:
		var id := int(c["id"])
		if _reached.has(id):
			continue
		if _dist_to(float(c["x_km"]), float(c["y_km"])) <= REACH_KM:
			_reached[id] = true
			_banner = "Checkpoint %d reached\n%s" % [id, c["name"]]
			_banner_at = _real


func _dist_to(x_km: float, y_km: float) -> float:
	return sqrt((x_km - _sea.x_km) * (x_km - _sea.x_km) + (y_km - _sea.y_km) * (y_km - _sea.y_km))


func _bearing_to(x_km: float, y_km: float) -> float:
	return fposmod(rad_to_deg(atan2(x_km - _sea.x_km, -(y_km - _sea.y_km))), 360.0)


func _update_wildlife(delta: float, t_days: float) -> void:
	_sight_t -= delta
	if _sight_t <= 0.0:
		_sight_t = SIGHT_EVERY_S
		var sg: Dictionary = Wildlife.sighting(_oc, _species, _sea.x_km, _sea.y_km, t_days)
		if not sg.is_empty():
			var key := "%d:%d:%d" % [int(sg["slot"]), int(floorf(_sea.x_km / 40.0)), int(floorf(_sea.y_km / 40.0))]
			if not _seen_keys.has(key):
				_seen_keys[key] = true
				_spawn_critter(sg)
	_berg_t -= delta
	if _berg_t <= 0.0:
		_berg_t = BERG_EVERY_S
		_bergs = _oc.bergs_near(_sea.x_km, _sea.y_km, BERG_RADIUS_KM)
	for i in range(_critters.size() - 1, -1, -1):
		if _real - float((_critters[i] as Dictionary)["born"]) > CRITTER_LIFE_S:
			_critters.remove_at(i)


func _spawn_critter(sg: Dictionary) -> void:
	var sp: Dictionary = _species_by_id[str(sg["species"])]
	var vis := maxf(float(_d["visibility_km"]), 0.1)
	var near := clampf(1.0 - float(sg["distance_km"]) / vis, 0.0, 1.0)
	_critters.append({"group": str(sp["group"]), "bearing": float(sg["bearing_deg"]), "near": near,
			"count": int(sg["count"]), "phase": randf() * TAU, "born": _real, "life": CRITTER_LIFE_S, "name": str(sp["name"])})
	if not _journal.has(str(sp["id"])):
		_journal[str(sp["id"])] = true
		_journal_log.append("%s x%d" % [sp["name"], int(sg["count"])])
		if _journal_log.size() > 6:
			_journal_log.remove_at(0)
		_banner = "New in the journal\n%s" % sp["name"]
		_banner_at = _real


# ---- chart (fog of war, revealed a few cells per frame) ---------------------------------
func _init_chart() -> void:
	_chart_cols = int(ceilf(_oc.world_w / CHART_CELL_KM))
	_chart_rows = int(ceilf(_oc.world_h / CHART_CELL_KM))
	_chart_img = Image.create_empty(_chart_cols, _chart_rows, false, Image.FORMAT_RGBA8)
	_chart_img.fill(Color(0.10, 0.09, 0.08))
	_chart_tex = ImageTexture.create_from_image(_chart_img)
	_chart_known.resize(_chart_cols * _chart_rows)
	_chart_known.fill(0)


func _update_chart() -> void:
	var cell := Vector2i(int(_sea.x_km / CHART_CELL_KM), int(_sea.y_km / CHART_CELL_KM))
	if cell != _chart_cell:
		_chart_cell = cell
		for dy in range(-REVEAL_RADIUS, REVEAL_RADIUS + 1):
			for dx in range(-REVEAL_RADIUS, REVEAL_RADIUS + 1):
				var cx := cell.x + dx
				var cy := cell.y + dy
				if dx * dx + dy * dy <= REVEAL_RADIUS * REVEAL_RADIUS + 1 and cx >= 0 and cy >= 0 \
						and cx < _chart_cols and cy < _chart_rows and _chart_known[cy * _chart_cols + cx] == 0:
					_chart_queue.append(cy * _chart_cols + cx)
	var n := mini(REVEAL_PER_FRAME, _chart_queue.size())
	for i in n:
		var idx: int = _chart_queue.pop_front()
		if _chart_known[idx] != 0:
			continue
		var cx2 := idx % _chart_cols
		var cy2 := idx / _chart_cols
		var lk: Dictionary = _oc.look_at((cx2 + 0.5) * CHART_CELL_KM, (cy2 + 0.5) * CHART_CELL_KM)
		_chart_img.set_pixel(cx2, cy2, Painter.rgb(lk["deep"]).lerp(Painter.rgb(lk["shallow"]), 0.3))
		_chart_known[idx] = 1
		_chart_known_n += 1
		_chart_dirty = true
	if _chart_dirty and _show_chart:
		_chart_tex.update(_chart_img)
		_chart_dirty = false


# ---- drawing -------------------------------------------------------------------------------------
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
	return v


func _draw() -> void:
	if _d.is_empty():
		return
	var v := _view()
	Painter.sky(self, v)
	Painter.sea(self, v)
	Painter.ice(self, v)
	Painter.bergs(self, v, _berg_view())
	Painter.critters(self, v, _critter_view())
	Painter.ship(self, v)
	Painter.rain(self, v)
	Painter.fog(self, v)
	Painter.lightning(self, v)
	_hud(v)
	if _show_chart:
		Painter.chart(self, _chart_dict())


func _berg_view() -> Array:
	var out: Array = []
	for b in _bergs:
		var bx := float((b as Array)[0])
		var by := float((b as Array)[1])
		var rel := wrapf(_bearing_to(bx, by) - _heading_disp, -180.0, 180.0)
		out.append({"rel": rel, "dist": _dist_to(bx, by), "size": int(b[2])})
	return out


func _critter_view() -> Array:
	var out: Array = []
	for c in _critters:
		var cc: Dictionary = (c as Dictionary).duplicate()
		cc["rel"] = wrapf(float(c["bearing"]) - _heading_disp, -180.0, 180.0)
		out.append(cc)
	return out


func _chart_dict() -> Dictionary:
	return {"tex": _chart_tex, "world_w": _oc.world_w, "world_h": _oc.world_h, "ship": Vector2(_sea.x_km, _sea.y_km),
			"heading": _sea.heading_deg, "route": _route, "reached": _reached, "labels": _labels,
			"known_pct": 100.0 * float(_chart_known_n) / float(_chart_cols * _chart_rows)}


func _compass(deg: float) -> String:
	return COMPASS[int(floorf(fposmod(deg, 360.0) / 45.0 + 0.5)) % 8]


func _next_checkpoint() -> Dictionary:
	for c in _route:
		if not _reached.has(int(c["id"])):
			return c
	return {}


func _hud(v: Dictionary) -> void:
	var smp: Dictionary = _sea.last_sample
	var white := Color(0.96, 0.94, 0.86)
	var dim := Color(0.8, 0.82, 0.85)
	var band := VoyageClock.band_of_hour(_hour, _starts)
	var lat := float(smp["lat"])
	Painter.text(self, Vector2(8, 14), str(_region_name()), Color(1.0, 0.9, 0.6), 14)
	Painter.text(self, Vector2(8, 28), "%s  (%s)   lat %.1f%s   chart %.0f, %.0f km" % [
			_state.clock_text(), band, absf(lat), "N" if lat >= 0.0 else "S", _sea.x_km, _sea.y_km], white, 11)
	Painter.text(self, Vector2(8, 41), "wind %.0f kn from %s | waves %.1f m | vis %.1f km | %.0f C" % [
			float(_d["wind_kn"]), _compass(float(_d["wind_from"])), float(_d["wave_m"]), float(_d["visibility_km"]),
			float(_d["air_c"])], dim, 11)
	Painter.text(self, Vector2(8, 54), "heading %03.0f %s | speed %.1f kn | sailed %.0f km" % [
			_sea.heading_deg, _compass(_sea.heading_deg), float(_d["speed_kn"]), _sea.distance_km], dim, 11)
	var y := 72.0
	for warn in _warnings():
		Painter.text(self, Vector2(8, y), str(warn), Color(1.0, 0.6, 0.4), 12)
		y += 13.0
	_hud_journal(white, dim)
	_hud_route(dim)
	_hud_banner()
	_hud_wind_rose(v)
	var reasons: PackedStringArray = _state.clock.pause_reasons()
	if not reasons.is_empty():
		Painter.text(self, Vector2(280, 100), "TIME STOPPED (%s)" % ", ".join(reasons), Color(1.0, 0.9, 0.5), 14)
	var help := "A/D steer  P pause  M chart  1-7 debug jump  ` console   %.0f fps" % _fps
	Painter.text(self, Vector2(8, 352), help, Color(1, 1, 1, 0.55), 10)


func _region_name() -> String:
	for r in _oc.regions:
		if str(r["id"]) == _region_id:
			return str(r["name"])
	return ""


func _warnings() -> Array[String]:
	var out: Array[String] = []
	if float(_d["storm"]) > 0.6:
		out.append("GALE: shorten sail, keep her head to the sea")
	elif float(_d["herald"]) > 0.35:
		out.append("A long swell is running from the %s: weather is coming" % _compass(float(_d["wind_from"])))
	if float(_d["fog"]) > 0.5:
		out.append("Fog: you can see %.1f km" % float(_d["visibility_km"]))
	if float(_d["ice"]) > 0.35:
		out.append("Ice on the water: %.0f%% covered" % (100.0 * float(_d["ice"])))
	if float(_d["speed_kn"]) < 1.0 and float(_d["wind_kn"]) < 4.0:
		out.append("Becalmed")
	return out


func _hud_journal(white: Color, dim: Color) -> void:
	Painter.text(self, Vector2(480, 14), "JOURNAL  %d / %d species" % [_journal.size(), _species.size()], white, 11)
	var y := 28.0
	for i in range(_journal_log.size() - 1, -1, -1):
		Painter.text(self, Vector2(480, y), _journal_log[i], dim, 10)
		y += 12.0


func _hud_route(dim: Color) -> void:
	var nxt := _next_checkpoint()
	if nxt.is_empty():
		Painter.text(self, Vector2(8, 340), "Route complete: the Three Weathers are behind you", Color(0.6, 1.0, 0.7), 12)
		return
	var d := _dist_to(float(nxt["x_km"]), float(nxt["y_km"]))
	var brg := _bearing_to(float(nxt["x_km"]), float(nxt["y_km"]))
	Painter.text(self, Vector2(8, 326), "Next %d: %s" % [int(nxt["id"]), nxt["name"]], Color(1.0, 0.9, 0.5), 11)
	var eta := ""
	if float(_d["speed_kn"]) > 0.3:
		var km_per_real_min: float = float(_d["speed_kn"]) * 1.852 * 24.0 / _oc.tuning_value("time.real_minutes_per_game_day")
		eta = "  about %.0f real min at this speed" % (d / km_per_real_min)
	Painter.text(self, Vector2(8, 339), "%.0f km, bearing %03.0f %s%s" % [d, brg, _compass(brg), eta], dim, 10)


func _hud_banner() -> void:
	var age := _real - _banner_at
	if age < 0.0 or age > BANNER_S or _banner == "":
		return
	var a := clampf(minf(age / 0.6, (BANNER_S - age) / 1.2), 0.0, 1.0)
	var lines := _banner.split("\n")
	var y := 190.0
	for i in lines.size():
		var s := str(lines[i])
		Painter.text(self, Vector2(320.0 - float(s.length()) * (3.6 if i == 0 else 2.7), y + 18.0 * float(i)),
				s, Color(1.0, 0.95, 0.75, a) if i == 0 else Color(0.85, 0.88, 0.9, a), 16 if i == 0 else 12)


func _hud_wind_rose(v: Dictionary) -> void:
	var c := Vector2(600.0, 320.0)
	draw_circle(c, 22.0, Color(0, 0, 0, 0.35))
	draw_arc(c, 22.0, 0.0, TAU, 28, Color(1, 1, 1, 0.5), 1.0)
	var rel := deg_to_rad(float(v["wind_from_deg"]) - float(v["heading_deg"]))
	var from_dir := Vector2(sin(rel), -cos(rel))
	draw_line(c + from_dir * 20.0, c - from_dir * 14.0, Color(0.6, 0.9, 1.0), 2.0)
	var side := Vector2(-from_dir.y, from_dir.x) * 4.0
	draw_colored_polygon(PackedVector2Array([c - from_dir * 14.0, c - from_dir * 7.0 + side, c - from_dir * 7.0 - side]),
			Color(0.6, 0.9, 1.0))
	var bow := PackedVector2Array([c + Vector2(0, -8), c + Vector2(4, 6), c + Vector2(-4, 6)])
	draw_colored_polygon(bow, Color(1, 1, 1, 0.9))
	Painter.text(self, Vector2(572, 354), "wind (bow up)", Color(1, 1, 1, 0.55), 9)
