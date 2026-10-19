extends Node
## H2D-0: one playable HD-2D ocean scene. The simulation is the validated E1 one (Ocean, SeaState, world clock, weather
## smoothing); only the PICTURE changed, behind the single SeaView interface (3D Compatibility path or 2D fallback).
## H2D-0.2: weather, sea, rain, spray, sail shape and ship motion all come from ONE shared environment (env_model.gd).
## Keys: W weather lab (real / calm / breezy / drizzle / rain / fog / rough / gale / storm) | G gust |
##       M ship motion off / half / full | E effects budget (low / medium / high)
## H2D-1: Anvil Cay has a harbour. SPACE docks inside the dock zone (between the buoys) and casts off again;
##       N cycles the time of day (dawn / noon / sunset / night) to look at the lighting.
## H2D-1.2: F goes ashore from the moored ship (and back aboard at the pier); on foot WASD / arrows walk, Shift
## runs, T jumps to the
##       next stop (test); Tab cycles the weather lab anywhere (W does it only at sea, because W walks north ashore).
## Keys: A/D (or Left/Right) steer | Z/X turn sensitivity | 1-7 weather (1 squall 2 fair 4 fog 5 swell 6 gale 7 ice)
##       P pause | R reset ship | F1 quality (Dev-Lite / Standard / Ultra) | F2 path (3D / 2D) | F3 HUD | F4 flip colour
##       transfer | F12 screenshot | [ ] camera pitch | - = exposure | , . visual speed | B benchmark (about 80 s)
## Open the project in Godot and press F5 (main scene = this one). Sailing feel: helm.gd + data/tuning/tuning_helm.json.
## NOT YET RUN IN GODOT.
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
const Helm := preload("res://h2d/helm.gd")
const EnvModel := preload("res://h2d/env_model.gd")
const HelmHud := preload("res://h2d/helm_hud.gd")
const Harbor := preload("res://h2d/harbor.gd")
const LandWalker := preload("res://h2d/land_walker.gd")
const KeyUtil := preload("res://h2d/key_util.gd")
const PortGame := preload("res://h2d/port_game.gd")
const MAX_STEP_S := 0.25
const SMOOTH_S := 2.0
const START_POS := Vector2(-100.0, 140.0)  ## keep in step with START in tools/h2d/check_harbor.py
const START_HEADING := 58.0  ## points at the harbour mouth: the dock zone is about 120 m ahead
const SMOOTH_KEYS: Array[String] = ["wind_kn", "wave_m", "visibility_km", "cloud", "storm", "herald", "rain", "fog",
		"ice", "sst_c", "air_c", "light_peak", "light_floor"]
const COMPASS: Array[String] = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
const QUALITIES: Array[String] = ["dev_lite", "standard", "ultra"]
## Weather Lab: fixed sea states to test the whole system in seconds. The wind DIRECTION stays the real one.
const LAB_ORDER: Array[String] = ["real", "calm", "breezy", "drizzle", "rain", "fog", "rough", "gale", "storm"]
const LAB := {
	"calm": {"wind_kn": 4.0, "wave_m": 0.35, "rain": 0.0, "storm": 0.0, "fog": 0.05},
	"breezy": {"wind_kn": 14.0, "wave_m": 1.4, "rain": 0.0, "storm": 0.0, "fog": 0.05},
	"drizzle": {"wind_kn": 8.0, "wave_m": 0.8, "rain": 0.2, "storm": 0.0, "fog": 0.08},
	"rain": {"wind_kn": 14.0, "wave_m": 1.6, "rain": 0.6, "storm": 0.0, "fog": 0.10},
	"fog": {"wind_kn": 5.0, "wave_m": 0.5, "rain": 0.0, "storm": 0.0, "fog": 0.75},
	"rough": {"wind_kn": 24.0, "wave_m": 3.4, "rain": 0.35, "storm": 0.25, "fog": 0.10},
	"gale": {"wind_kn": 36.0, "wave_m": 6.0, "rain": 0.8, "storm": 0.7, "fog": 0.15},
	"storm": {"wind_kn": 48.0, "wave_m": 9.5, "rain": 1.0, "storm": 1.0, "fog": 0.2},
}
## Test hours for key N (the time of day moves on by itself too: 1 day = 15 real minutes).
const TOD_HOURS: Array[float] = [6.5, 12.0, 18.0, 22.5]
const TOD_NAMES: Array[String] = ["dawn 06:30", "noon 12:00", "sunset 18:00", "night 22:30"]
const MOTION_NAMES: Array[String] = ["off", "half", "full"]
const EFFECT_LEVELS: Array[String] = ["low", "medium", "high"]

var _env: EnvModel = EnvModel.new()
var _env_snap := true
var _lab := "real"
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
var _helm: Helm = Helm.new()
var _helm_snap := true
var _helm_hud: HelmHud
var _harbor: Harbor = Harbor.new()
var _moor := 0.0
var _walker: LandWalker = LandWalker.new()
var _port: Node = null  ## CP-1: the Fish Row loop (economy, nets, people, map, dialogue)
var _edge_said := -100.0
var _tp_next := 0
var _tod := 0
var _dock_label: Label
var _alert: Label
var _alert_sub: Label
var _advice := ""
var _renderer_line := ""
var _hour := 6.0
var _light := 1.0
var _real := 0.0
var _turn := 0.0
var _curve := 0.0
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
	_build_helm_widgets(layer)
	_helm.configure(_oc.tuning())
	_env.configure(_oc.tuning())
	(_v3 as View3D).configure_env(_oc.tuning())
	_harbor.configure((_v3 as View3D).harbor_layout(), _oc.tuning())
	_walker.configure((_v3 as View3D).land_world().meta["land"], _oc.tuning())
	(_v3 as View3D).land_world().walk_min_h = _walker.param("min_h")
	(_v3 as View3D).land_world().walk_max_slope = _walker.param("max_slope")
	_port = PortGame.new()
	add_child(_port)
	(_port as PortGame).setup(layer, (_v3 as View3D).land_world(), _oc.tuning(), _port_pause)
	_jump(2)
	_reset_ship()
	_set_path("3d")
	_bench_cli = OS.get_cmdline_user_args().has("--bench")
	_renderer_line = _renderer_summary()
	_write_diagnostics()
	await (_v3 as View3D).calibrate_gamma()
	_write_diagnostics()
	_say("A / D steer the ship. Z / X change how sharply it turns. Red wedge = where the sails cannot draw.")
	if _bench_cli:
		_start_bench()


# ---- world -------------------------------------------------------------------------------------------------------
func _jump(number: int) -> void:
	for c in _route:
		if int(c["id"]) == number:
			_sea.place(float(c["x_km"]), float(c["y_km"]), float(c["heading_deg"]))
			_sea.heading_deg = _helm.heading_deg
			_helm_snap = true
			_state.t_seconds = roundi(float(c["t_days"]) * 86400.0)
			_state.clock.set_location("sea")
			_region_id = ""
			_d.clear()


func _reset_ship() -> void:
	_pos = START_POS
	_sea.heading_deg = START_HEADING
	_helm.reset(START_HEADING, 0.0)
	_helm_snap = true
	_heading_disp = START_HEADING
	_turn = 0.0
	_curve = 0.0
	_grounded = false
	_harbor.reset()
	_moor = 0.0
	_walker.board()


func _set_path(which: String) -> void:
	if which == "2d" and _walker.is_ashore():
		_walker.board()     # the 2D fallback has no land: step back aboard instead of leaving the pirate nowhere
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
	var t0 := float(_state.clock.t) / 86400.0
	var gs: float = _state.tick(dt)
	if _sea.last_sample.is_empty():
		_sea.refresh(t0)
	# the helm: A/D -> rudder -> turn rate -> heading; the sails' speed at this heading -> actual speed (with momentum)
	_apply_lab()
	_step_env(dt)
	_land_step(dt, gs)
	var target_kn: float = _sea.speed_kn() * (1.0 + _env.gust_surge())
	if _port != null:
		(_port as PortGame).step(dt, _port_ctx())
		if (_port as PortGame).nets_down():
			target_kn = 0.0  # the nets drag: the sloop stops while they are down (CP-1)
	var speed_scene := 0.0
	if _harbor.state == Harbor.SAILING:
		speed_scene = _sail_step(dt, gs, t0, target_kn)
	else:
		speed_scene = _harbor_step(dt, gs)
	_smooth(dt)
	_apply_env_to_view()
	_d["speed_kn"] = _helm.speed_kn
	_curve = clampf(deg_to_rad(_helm.yaw_rate) / maxf(speed_scene, 3.0), -0.04, 0.04)
	_update_light(float(_state.clock.t) / 86400.0)
	_update_region()
	(_v3 as View3D).set_land(_land_view_state())
	_active.update_view(_view(), {"x": _pos.x, "z": _pos.y, "heading_deg": _heading_disp,
			"speed_kn": float(_d["speed_kn"]), "scene_speed": speed_scene, "curve": _curve, "moor": _moor}, delta)
	var advice := _helm_state(target_kn)
	_helm_hud.set_state(advice)
	_update_alert(advice)
	_hud_t -= delta
	if _hud_t <= 0.0:
		_hud_t = 0.2
		_draw_hud(speed_scene, advice)


## Free sailing: the helm and the sails move the ship; the hull footprint is tested against the land; the scene speed is
## eased near the berth. Returns the scene speed in m/s (what the wake shows).
func _sail_step(dt: float, gs: float, t0: float, target_kn: float) -> float:
	if _helm_snap:
		_helm.speed_kn = target_kn
		_helm_snap = false
	if gs > 0.0:
		_helm.step(dt, _steer_axis(), target_kn)
		_sea.heading_deg = _helm.heading_deg
	_heading_disp = _helm.heading_deg
	_turn = _helm.yaw_rate * 0.5
	var speed_scene := ShipSprite.scene_speed_ms(_helm.speed_kn) * _speed_mul * _harbor.speed_scale(_pos.x, _pos.y)
	if gs > 0.0:
		var hd := deg_to_rad(_sea.heading_deg)
		var np := _pos + Vector2(sin(hd), -cos(hd)) * speed_scene * dt
		if _hull_aground(np):
			_grounded = true
			_helm.speed_kn = 0.0
		else:
			_grounded = false
			_pos = np
			_sea.advance(t0, gs)
	if _grounded:
		speed_scene = 0.0
	return speed_scene


## True if any probe of the hull (bow, stern, centre, both sides) is over land higher than harbor.ground_limit_m.
func _hull_aground(p: Vector2) -> bool:
	var limit := _harbor.param("ground_limit_m")
	for pt in _harbor.footprint(p.x, p.y, _sea.heading_deg):
		if _v3.land_height_at(float(pt[0]), float(pt[1])) > limit:
			return true
	return false


## Docking, moored, casting off: the harbour logic moves the ship and the helm only watches.
func _harbor_step(dt: float, gs: float) -> float:
	var before := _pos
	var pose: Dictionary = _harbor.step(dt if gs > 0.0 else 0.0)
	_pos = Vector2(float(pose["x"]), float(pose["z"]))
	_moor = float(pose["moor"])
	_sea.heading_deg = float(pose["heading"])
	_helm.reset(float(pose["heading"]), 0.0)
	_heading_disp = float(pose["heading"])
	_turn = 0.0
	_grounded = false
	_helm_snap = false
	if bool(pose["done"]):
		if int(pose["state"]) == Harbor.DOCKED:
			_say("Moored at %s. The sails hang slack. Press SPACE to cast off." % _harbor.port_name)
		else:
			_helm.reset(float(pose["heading"]), 0.8)
			_say("Clear of the berth: you have the helm. A / D steer.")
	if _harbor.state != Harbor.DOCKING or dt <= 0.0:
		return 0.0
	return minf((_pos - before).length() / dt, 25.0) * (1.0 - _moor)


## SPACE: dock inside the dock zone, cast off when moored.
func _dock_request() -> void:
	var r := _harbor.request(_pos.x, _pos.y, _sea.heading_deg)
	match r:
		"docking":
			_say("Docking at %s: the crew brings her alongside." % _harbor.port_name)
		"casting_off":
			_say("Casting off from %s." % _harbor.port_name)
		"not_in_zone":
			_say("Too far from the berth: sail into the harbour mouth (between the buoys) first.")


# ---- CP-1: the Fish Row loop -----------------------------------------------------------------------------------
func _port_pause(on: bool) -> void:
	if on:
		_state.clock.pause("port")
	else:
		_state.clock.resume("port")


## What the port controller needs to know about the world this frame.
func _port_ctx() -> Dictionary:
	return {"ashore": _walker.is_ashore(), "wx": _walker.x, "wz": _walker.z, "sx": _pos.x, "sz": _pos.y, "sheading": _heading_disp,
			"speed_kn": _helm.speed_kn, "hour": _hour, "now": float(_state.clock.t) / 86400.0, "sea": _env.sea,
			"docked": _harbor.state == Harbor.DOCKED, "sailing": _harbor.state == Harbor.SAILING}


# ---- H2D-1.2: on foot -------------------------------------------------------------------------------------------
func _land_view_state() -> Dictionary:
	return {"ashore": _walker.is_ashore(), "x": _walker.x, "z": _walker.z, "row": _walker.row, "frame": _walker.frame,
			"zoom": _walker.param("zoom"), "zoom_s": _walker.param("zoom_s")}


func _walk_axis() -> Vector2:
	var a := Vector2.ZERO
	if _port != null and (_port as PortGame).modal():
		return a
	if KeyUtil.held(KEY_A) or KeyUtil.held(KEY_LEFT):
		a.x -= 1.0
	if KeyUtil.held(KEY_D) or KeyUtil.held(KEY_RIGHT):
		a.x += 1.0
	if KeyUtil.held(KEY_W) or KeyUtil.held(KEY_UP):
		a.y -= 1.0
	if KeyUtil.held(KEY_S) or KeyUtil.held(KEY_DOWN):
		a.y += 1.0
	return a


func _land_step(dt: float, gs: float) -> void:
	if not _walker.is_ashore():
		return
	_walker.step(dt if gs > 0.0 else 0.0, _walk_axis(), KeyUtil.held(KEY_SHIFT), (_v3 as View3D).land_world())
	if _walker.last_reached != "":
		_say("Reached %s (stop %d of %d)." % [_walker.last_reached, _walker.visited_count(), _walker.pois.size()])
		_walker.last_reached = ""
		if _walker.route_complete():
			_say("Route complete. Walk back to the pier and press F to board, then SPACE to cast off.")
	if _walker.blocked_by_edge and _real - _edge_said > 5.0:
		_edge_said = _real
		_say("That is the edge of the walkable area in this prototype. The rest of the island is not open yet.")


## F: go ashore from the moored ship, or board again at the pier.
func _land_toggle() -> void:
	if _active != _v3:
		_say("Walking ashore needs the 3D path (F2).")
		return
	if _walker.is_ashore():
		if _walker.can_board():
			_walker.board()
			_say("Back aboard. SPACE casts off.")
		else:
			_say("Too far from the ship to board: walk back to the pier. %s" % _walker.hint_text())
		return
	if _harbor.state != Harbor.DOCKED:
		_say("Dock first: sail into the harbour mouth and press SPACE. Then F goes ashore.")
		return
	_walker.disembark((_v3 as View3D).land_world().meta["land"])
	(_v3 as View3D).land_world().prime(Vector2(_walker.x, _walker.z))
	_say("Ashore. WASD or arrows walk, Shift runs. Follow the route: %s" % _walker.hint_text())


## T (test): jump to the next stop of the route.
func _land_teleport() -> void:
	if not _walker.is_ashore():
		_say("T jumps between the stops while you are ashore (F first).")
		return
	var d: Dictionary = _walker.pois[_tp_next % _walker.pois.size()]
	_tp_next += 1
	_walker.teleport_to(str(d["id"]))
	(_v3 as View3D).land_world().prime(Vector2(_walker.x, _walker.z))
	_say("Test jump: %s. (The stop only counts as reached when you walk into it.)" % str(d["name"]))


func _dock_prompt() -> String:
	if _walker.is_ashore():
		return "Press F to board the ship" if _walker.can_board() else ""
	var t := str(_harbor.prompt(_pos.x, _pos.y)["text"])
	if _harbor.state == Harbor.DOCKED:
		t += "   F: go ashore"
	return t


func _cycle_lab() -> void:
	_lab = LAB_ORDER[(LAB_ORDER.find(_lab) + 1) % LAB_ORDER.size()]
	_say("weather lab: %s (the sea builds up or dies away over about half a minute)" % _lab)


func _cycle_time_of_day() -> void:
	_tod = (_tod + 1) % TOD_HOURS.size()
	_state.set_clock(_state.day(), TOD_HOURS[_tod])
	_say("time of day: %s (test only; the real clock keeps running)" % TOD_NAMES[_tod])


func _steer_axis() -> float:
	if _bench != null and (_bench as Bench).active:
		return 0.55 * sin(_real * 0.9)
	var axis := 0.0
	if _port != null and (_port as PortGame).modal():
		return axis
	if KeyUtil.held(KEY_A) or KeyUtil.held(KEY_LEFT):
		axis -= 1.0
	if KeyUtil.held(KEY_D) or KeyUtil.held(KEY_RIGHT):
		axis += 1.0
	return axis


## Weather Lab: replaces the sampled weather with a fixed sea state (every frame, because the ocean re-samples
## every 15 game minutes). The wind direction, the region and the light are untouched.
func _apply_lab() -> void:
	if _lab == "real" or _sea.last_sample.is_empty():
		return
	var p: Dictionary = LAB[_lab]
	var smp: Dictionary = _sea.last_sample
	for key in p.keys():
		smp[key] = float(p[key])


## The environment model eases towards the sampled weather: gusts, build-up and decay, slow wave direction.
func _step_env(dt: float) -> void:
	var smp: Dictionary = _sea.last_sample
	if _env_snap:
		_env.snap(smp)
		_env_snap = false
	_env.step(dt, smp, _real)


## The numbers the picture, the HUD and the 2D fallback read: from the environment, not from the raw sample.
func _apply_env_to_view() -> void:
	_d["wind_kn"] = _env.wind_kn
	_d["wind_from"] = _env.wind_from
	_d["wave_m"] = _env.wave_m
	_d["rain"] = _env.rain_inst
	_d["storm"] = _env.storm
	_d["fog"] = _env.fog
	_d["visibility_km"] = _env.visibility_km
	_d["cloud"] = maxf(float(_d["cloud"]), maxf(0.6 * _env.rain, 0.8 * _env.storm))


func _smooth(dt: float) -> void:
	var smp: Dictionary = _sea.last_sample
	var k := 1.0 - exp(-dt / SMOOTH_S)
	var first := _d.is_empty()
	for key in SMOOTH_KEYS:
		var target: float = _sea.speed_kn() if key == "speed_kn" else float(smp[key])
		_d[key] = target if first else lerpf(float(_d[key]), target, k)
	var wf := deg_to_rad(float(smp["wind_from_deg"]))
	_d["wind_from"] = rad_to_deg(wf) if first else rad_to_deg(lerp_angle(deg_to_rad(float(_d["wind_from"])), wf, k))
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
	v["env"] = _env.to_dict()
	v["no_go_deg"] = _oc.tuning_value("ship.no_go_deg")
	return v


# ---- input -------------------------------------------------------------------------------------------------------
func _unhandled_input(event: InputEvent) -> void:
	var k := event as InputEventKey
	if k == null or not k.pressed or k.echo:
		return
	var kc: int = KeyUtil.code(k)     # layout-proof key (an Arabic layout would otherwise break every letter key)
	var v3 := _v3 as View3D
	var ashore := _walker.is_ashore()
	if _port != null and (_port as PortGame).handle_key(k, _port_ctx()):
		return  # CP-1 keys: E interact, F nets (at sea), M map, Y/N, Enter, Tab and Esc inside a panel, F6/F7 test helpers
	if kc == KEY_F:
		_land_toggle()
	elif kc == KEY_T:
		_land_teleport()
	elif kc == KEY_TAB:
		_cycle_lab()
	elif ashore and (kc == KEY_R or kc == KEY_SPACE or (kc >= KEY_1 and kc <= KEY_7)):
		_say("You are ashore: board the ship first (F at the pier). %s" % _walker.hint_text())
	elif kc >= KEY_1 and kc <= KEY_7:
		_jump(int(kc) - int(KEY_1) + 1)
	elif kc == KEY_P:
		var reason := "menu"
		if _state.clock.pause_reasons().has(reason):
			_state.clock.resume(reason)
		else:
			_state.clock.pause(reason)
	elif kc == KEY_R:
		_reset_ship()
	elif kc == KEY_W:
		if not ashore:
			_cycle_lab()
	elif kc == KEY_SPACE:
		_dock_request()
	elif kc == KEY_N:
		_cycle_time_of_day()
	elif kc == KEY_G:
		_env.trigger_gust()
		_say("gust")
	elif kc == KEY_M:
		v3.motion_mode = (v3.motion_mode + 1) % 3
		_say("ship motion: " + MOTION_NAMES[v3.motion_mode])
	elif kc == KEY_E:
		var lv: String = EFFECT_LEVELS[(EFFECT_LEVELS.find(v3.effects) + 1) % EFFECT_LEVELS.size()]
		v3.set_effects(lv)
		_say("effects budget: " + lv)
	elif kc == KEY_F1:
		var q: String = QUALITIES[(QUALITIES.find(v3.quality) + 1) % QUALITIES.size()]
		v3.set_quality(q)
		_say("quality: " + q)
	elif kc == KEY_F2:
		_set_path("2d" if _active == _v3 else "3d")
		_say("path: " + _active.path_name())
	elif kc == KEY_F3:
		_hud_on = not _hud_on
	elif kc == KEY_F4:
		v3.set_gamma(1.0 if v3.gamma > 1.5 else 2.2)
		_say("colour transfer flipped: h2d_gamma %.1f (press F4 again if it looks washed out or too dark)" % v3.gamma)
	elif kc == KEY_F12:
		_shot_n += 1
		var img := get_viewport().get_texture().get_image()
		img.save_png("user://h2d0_shot_%03d.png" % _shot_n)
		_say("saved " + ProjectSettings.globalize_path("user://h2d0_shot_%03d.png" % _shot_n))
	elif kc == KEY_BRACKETLEFT:
		v3.adjust_pitch(-3.0)
	elif kc == KEY_BRACKETRIGHT:
		v3.adjust_pitch(3.0)
	elif kc == KEY_MINUS:
		v3.adjust_exposure(1.0 / 1.1)
	elif kc == KEY_EQUAL:
		v3.adjust_exposure(1.1)
	elif kc == KEY_Z:
		_helm.set_sensitivity(_helm.sensitivity - 0.2)
		_say("turn sensitivity x%.1f" % _helm.sensitivity)
	elif kc == KEY_X:
		_helm.set_sensitivity(_helm.sensitivity + 0.2)
		_say("turn sensitivity x%.1f" % _helm.sensitivity)
	elif kc == KEY_COMMA:
		_speed_mul = maxf(_speed_mul * 0.5, 0.125)
	elif kc == KEY_PERIOD:
		_speed_mul = minf(_speed_mul * 2.0, 8.0)
	elif kc == KEY_B and (_bench == null or not (_bench as Bench).active):
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
	_env_snap = true


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


## Everything the helm display and the plain-language advice need, from the helm and the wind.
func _helm_state(target_kn: float) -> Dictionary:
	var wind_from := float(_d["wind_from"])
	var wind_kn := float(_d["wind_kn"])
	var no_go: float = _oc.tuning_value("ship.no_go_deg")
	var off := Helm.off_wind_deg(_helm.heading_deg, wind_from)
	var best_kmh: float = _oc.speed_through_water_kmh(fposmod(wind_from + 100.0, 360.0), wind_kn, wind_from,
			float(_d["ice"]))
	var best_kn := best_kmh / SeaState.KN_KMH
	var irons := off < no_go and wind_kn > 3.0
	var sail := "In irons" if irons else Helm.point_of_sail(maxf(off, no_go), no_go)
	var esc := Helm.escape_direction(_helm.heading_deg, wind_from)
	return {"heading": _helm.heading_deg, "wind_from": wind_from, "no_go": no_go, "in_irons": irons,
			"rudder": _helm.rudder, "speed_kn": _helm.speed_kn, "target_kn": target_kn, "best_kn": best_kn,
			"sail_name": sail, "off": off, "escape_key": "A" if esc < 0 else "D", "wind_kn": wind_kn}


## One or two plain sentences that say what the ship is doing and why its speed is what it is.
func _advice_for(st: Dictionary) -> String:
	var eff := float(st["target_kn"]) / maxf(float(st["best_kn"]), 0.1)
	if _walker.is_ashore() or _harbor.state != Harbor.SAILING:
		return _walker.hint_text() if _walker.is_ashore() else _dock_prompt()
	if _grounded:
		return "AGROUND on Anvil Cay. Turn away from the island with A or D (or press R to start again)."
	if bool(st["in_irons"]):
		var msg := "IN IRONS: the bow is within %d deg of the wind, so the sails cannot draw and the ship is losing speed."
		msg += " Turn away from the red wedge: press %s."
		return msg % [int(st["no_go"]), str(st["escape_key"])]
	if float(st["speed_kn"]) < float(st["target_kn"]) - 0.4:
		return "%s: picking up speed (%.1f kn now, the sails can give %.1f kn at this heading)." % [
				str(st["sail_name"]), float(st["speed_kn"]), float(st["target_kn"])]
	if eff < 0.75:
		return "%s: the sails give %d%% of the best speed. Turn towards the green zone to go faster." % [
				str(st["sail_name"]), int(eff * 100.0)]
	return "%s: good speed (%d%% of the best the wind allows)." % [str(st["sail_name"]), int(minf(eff, 1.0) * 100.0)]


func _build_helm_widgets(layer: CanvasLayer) -> void:
	_helm_hud = HelmHud.new()
	_helm_hud.anchor_top = 1.0
	_helm_hud.anchor_bottom = 1.0
	_helm_hud.offset_left = 10.0
	_helm_hud.offset_right = 10.0 + HelmHud.WIDTH
	_helm_hud.offset_top = -HelmHud.HEIGHT - 8.0
	_helm_hud.offset_bottom = -8.0
	layer.add_child(_helm_hud)
	_alert = Label.new()
	_alert.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_alert.offset_top = 40.0
	_alert.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_alert.add_theme_font_size_override("font_size", 38)
	_alert.add_theme_color_override("font_color", Color(1.0, 0.32, 0.26))
	_alert.add_theme_color_override("font_outline_color", Color(0.05, 0.05, 0.08))
	_alert.add_theme_constant_override("outline_size", 8)
	_alert.visible = false
	layer.add_child(_alert)
	_alert_sub = Label.new()
	_alert_sub.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_alert_sub.offset_top = 88.0
	_alert_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_alert_sub.add_theme_font_size_override("font_size", 17)
	_alert_sub.add_theme_color_override("font_color", Color(1.0, 0.95, 0.85))
	_alert_sub.add_theme_color_override("font_outline_color", Color(0.05, 0.05, 0.08))
	_alert_sub.add_theme_constant_override("outline_size", 5)
	_alert_sub.visible = false
	layer.add_child(_alert_sub)
	_dock_label = Label.new()
	_dock_label.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_dock_label.offset_top = -92.0
	_dock_label.offset_bottom = -52.0
	_dock_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_dock_label.add_theme_font_size_override("font_size", 22)
	_dock_label.add_theme_color_override("font_color", Color(1.0, 0.93, 0.7))
	_dock_label.add_theme_color_override("font_outline_color", Color(0.05, 0.05, 0.08))
	_dock_label.add_theme_constant_override("outline_size", 7)
	_dock_label.visible = false
	layer.add_child(_dock_label)


## The big IN IRONS / AGROUND banner. Pulses so it cannot be missed, and says which key to press.
func _update_alert(st: Dictionary) -> void:
	var ptxt := _dock_prompt()
	_dock_label.visible = _hud_on and ptxt != ""
	_dock_label.text = ptxt
	var sailing := _harbor.state == Harbor.SAILING and not _walker.is_ashore()
	var alarm := _hud_on and sailing and (bool(st["in_irons"]) or _grounded)
	_alert.visible = alarm
	_alert_sub.visible = alarm
	_helm_hud.visible = _hud_on and not _walker.is_ashore()
	if not alarm:
		return
	_alert.text = "AGROUND" if _grounded else "IN IRONS"
	_alert_sub.text = _advice_for(st)
	var pulse := 0.65 + 0.35 * sin(_real * 6.0)
	_alert.modulate = Color(1.0, 1.0, 1.0, pulse)


func _draw_hud(speed_scene: float, st: Dictionary) -> void:
	_hud.visible = _hud_on
	if not _hud_on:
		return
	var wind_from := float(_d["wind_from"])
	var lines: Array[String] = []
	lines.append("CROWN OF THE SEAS - H2D-1.2 Anvil Cay (scale + land)   [%s]   %.0f fps" % [_active.describe(), _fps])
	lines.append(_renderer_line)
	lines.append("%s   %02d:%02d   wind %.0f kn (gusting %.0f) from %s   waves %.1f m   visibility %.1f km" % [
			_region_name(), int(_hour), int((_hour - floorf(_hour)) * 60.0), float(_d["wind_kn"]), _env.wind_inst_kn,
			_compass(wind_from), float(_d["wave_m"]), float(_d["visibility_km"])])
	lines.append("sea state: %s (%.2f)   gust %.2f   weather: %s   effects: %s" % [_env.sea_name(), _env.sea, _env.gust,
			"real" if _lab == "real" else "LAB " + _lab, (_v3 as View3D).effects])
	if _walker.is_ashore():
		var w3 := (_v3 as View3D).land_world()
		lines.append("ON FOOT  x %.0f  z %.0f  ground %.1f m  speed %.1f m/s  walked %d m   %s" % [_walker.x, _walker.z,
				w3.height_smooth(_walker.x, _walker.z), _walker.speed_ms, int(_walker.distance_m), w3.chunk_stats()])
	else:
		lines.append("ship motion [%s]: %s" % [MOTION_NAMES[(_v3 as View3D).motion_mode], (_v3 as View3D).motion_summary()])
		lines.append("turn rate %.0f deg/s (sensitivity x%.1f, Z/X)   scene speed %.1f m/s (x%.2f)   sprite frame %d/16" % [
			absf(_helm.yaw_rate), _helm.sensitivity, speed_scene, _speed_mul, ShipSprite.heading_frame(_heading_disp)])
	lines.append("rain %.2f  storm %.2f  fog %.2f  ice %.2f  swell warning %.2f" % [
			float(_d["rain"]), float(_d["storm"]), float(_d["fog"]), float(_d["ice"]), float(_d["herald"])])
	lines.append(_advice_for(st))
	if _port != null:
		lines.append("last key: %s" % (_port as PortGame).last_key)
	var pr := _harbor.prompt(_pos.x, _pos.y)
	if bool(pr["near"]) and _harbor.state == Harbor.SAILING:
		var zone_txt := "IN THE DOCK ZONE" if bool(pr["can_dock"]) else "outside the dock zone"
		lines.append("%s berth: %d m, bearing %03d deg   harbour speed x%.2f   %s" % [_harbor.port_name,
				int(roundf(float(pr["dist"]))), int(roundf(float(pr["bearing"]))) % 360,
				_harbor.speed_scale(_pos.x, _pos.y), zone_txt])
	if _state.clock.is_paused():
		lines.append("PAUSED")
	if _bench != null and (_bench as Bench).active:
		lines.append("BENCHMARK " + (_bench as Bench).current_label())
	if _real < _banner_until:
		lines.append(_banner)
	if _walker.is_ashore():
		lines.append("WASD walk  Shift run  E talk / sell / read  M map  F board (at pier)  T next stop  N time  P pause   F6/F7 test money/fish")
	else:
		lines.append("A/D steer  F nets (on a fishing ground)  M map  SPACE dock/cast off  F ashore (moored)  Z/X turn  Shift+M motion  W/Tab weather  R reset")
	_hud.text = "\n".join(PackedStringArray(lines))


# ---- renderer diagnostics ------------------------------------------------------------------------------------------
## Which OpenGL path is really running. The Windows build tries native OpenGL 3.3 first and, if the driver reports less
## (an Intel HD 3000 reports 3.1), switches to ANGLE = OpenGL ES 3.0 on top of Direct3D 11 and prints the warning
## "Your video card drivers seem not to support the required OpenGL 3.3 version, switching to ANGLE". That fallback is
## by design (project setting rendering/gl_compatibility/fallback_to_angle), not a fault of this project.
func _renderer_summary() -> String:
	var drv := RenderingServer.get_current_rendering_driver_name()
	var path := drv
	if drv == "opengl3":
		path = "native OpenGL 3.3"
	elif drv == "opengl3_angle":
		path = "OpenGL ES 3.0 via ANGLE (Direct3D 11)"
	elif drv == "opengl3_es":
		path = "native OpenGL ES 3.0"
	return "renderer: %s [%s]  GPU: %s" % [path, drv, RenderingServer.get_video_adapter_name()]


func _write_diagnostics() -> void:
	var lines: Array[String] = []
	lines.append("H2D-0.1 renderer diagnostics")
	lines.append("godot: %s" % Engine.get_version_info()["string"])
	lines.append("os: %s" % OS.get_name())
	lines.append("rendering method: %s" % RenderingServer.get_current_rendering_method())
	lines.append("rendering driver: %s" % RenderingServer.get_current_rendering_driver_name())
	lines.append(_renderer_summary())
	lines.append("adapter vendor: %s" % RenderingServer.get_video_adapter_vendor())
	lines.append("adapter api version: %s" % RenderingServer.get_video_adapter_api_version())
	lines.append("driver info: %s" % str(OS.get_video_adapter_driver_info()))
	lines.append("window size: %s" % str(DisplayServer.window_get_size()))
	lines.append("colour transfer: %s" % (_v3 as View3D).calibration_note)
	var declared := ProjectSettings.has_setting("shader_globals/h2d_gamma")
	lines.append("shader globals declared in project.godot: %s" % str(declared))
	var f := FileAccess.open("user://h2d0_diagnostics.txt", FileAccess.WRITE)
	for line in lines:
		print("H2D0 ", line)
		if f != null:
			f.store_line(line)
