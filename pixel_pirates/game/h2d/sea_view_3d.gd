# gdlint: disable=max-public-methods
extends "res://h2d/sea_view.gd"
## HD-2D sailing view in the Compatibility renderer (decisions D1 to D3). A real 3D scene seen by a fixed north-up
## perspective camera (FOV 22 deg, pitch 48 deg), drawn into a SubViewport at the art grid and shown with nearest
## upscaling, then a post shader (tilt-shift, grade, rain, lightning). Pixel-art sprites (the ship, the trees) are
## camera-facing quads; the ocean and the island are shaded meshes. Lighting is ONE custom model shared by every shader
## through global uniforms (sun, ambient, fog), driven by the same clock and weather as the 2D path.
## NOT YET RUN IN GODOT: the first run on the user's PC is the first test (docs/H2D0_PROTOTYPE.md).
const ShipSprite := preload("res://h2d/ship_sprite.gd")
const WaveModel := preload("res://h2d/wave_model.gd")
const LightModel := preload("res://h2d/light_model.gd")
const ShipMotion := preload("res://h2d/ship_motion.gd")
const EnvModel := preload("res://h2d/env_model.gd")
const SailModel := preload("res://h2d/sail_model.gd")
const CayWorld := preload("res://h2d/cay_world.gd")
const DeckView := preload("res://h2d/ship_deck_view.gd")
const DeckLayout := preload("res://h2d/ship_layout.gd")
const WeatherLook := preload("res://h2d/weather_look.gd")
const DataLoader := preload("res://core/data_loader.gd")
const SHADER_DIR := "res://h2d/shaders/"
const ART_DIR := "res://h2d/art/"
const FOV_DEG := 22.0
const DEFAULT_PITCH_DEG := 48.0
const PX_PER_M := 3.6
const DECK_MOTION := 0.5   ## how much of the sea motion the walkable deck shows (the pirate must be able to walk and read prompts)
const ART_H := 360.0
const TARGET_LEAD_M := 9.0  ## the camera looks this far north of the ship, so the ship sits low in the picture
const OCEAN_SIZE_M := 420.0
const PROFILES := {
	"dev_lite": {"size": Vector2i(640, 360), "ocean_div": 64, "detail": 0.0, "shadow_steps": 6.0, "posterize": 12.0},
	"standard": {"size": Vector2i(1280, 720), "ocean_div": 128, "detail": 1.0, "shadow_steps": 10.0, "posterize": 16.0},
	"ultra": {"size": Vector2i(1920, 1080), "ocean_div": 192, "detail": 1.0, "shadow_steps": 12.0, "posterize": 24.0},
}
## Effects budget (key E): how many real raindrops, ring slots and spray droplets are simulated. The look is the same
## at every level, only the density and the cost change. Dev-Lite defaults to "medium"; measure before raising it.
const EFFECTS := {
	"low": {"grid": Vector2i(40, 32), "cell_m": 4.6, "k": 1, "spin": 120, "burst": 24, "dens": 0.9},
	"medium": {"grid": Vector2i(56, 44), "cell_m": 3.4, "k": 2, "spin": 250, "burst": 32, "dens": 0.5},
	"high": {"grid": Vector2i(64, 50), "cell_m": 3.0, "k": 3, "spin": 600, "burst": 48, "dens": 0.32},
}
const RAIN_DRIFT_MAX_MS := 12.0
## The rain grid sits a little south of the focus: drops that land just below the screen edge are seen high up.
const RAIN_CENTER_SOUTH_M := 14.0
const SPRAY_BOX := Vector2(150.0, 110.0)

var quality := "dev_lite"
var effects := "medium"
var motion_mode := 2  ## 0 off, 1 half, 2 full (key M)
var gamma := 2.2
var exposure := 1.25
var calibration_note := "not calibrated"
var pitch_deg := DEFAULT_PITCH_DEG
var _layer: CanvasLayer
var _vp: SubViewport
var _rect: TextureRect
var _cam: Camera3D
var _ocean: MeshInstance3D
var _ocean_mat: ShaderMaterial
var _cay: CayWorld = CayWorld.new()
var _harbor_layout: Dictionary = {}
var _ship: MeshInstance3D
var _ship_mat: ShaderMaterial
var _post_mat: ShaderMaterial
var _look_profiles: Dictionary = {}
var _wave_b: Dictionary = {}
var _time := 0.0
var _rain: MultiMeshInstance3D
var _rain_mat: ShaderMaterial
var _spray: MultiMeshInstance3D
var _spray_mat: ShaderMaterial
var _motion: ShipMotion = ShipMotion.new()
var _sail: SailModel = SailModel.new()
var _look: WeatherLook = WeatherLook.new()
var _sail_boxes: Array = []
var _trim_row := 2
var _bursts: Array = [[0.0, 0.0, -100.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, -100.0, 0.0, 0.0, 0.0, 0.0, 0.0],
		[0.0, 0.0, -100.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
var _burst_next := 0
var _slam_count := 0
var _last_out: Dictionary = {"roll_deg": 0.0, "pitch_deg": 0.0, "heave_m": 0.0}
var _focus := Vector2.ZERO
## 1 at sea; the land view eases it to land.zoom (about 4): the pirate keeps one sprite pixel per screen pixel
var _zoom := 1.0
var _land: Dictionary = {"ashore": false}
## CP-2: the walkable ship model (ship_deck_view.gd), drawn instead of the sprite while the pirate is on foot aboard.
var _deck: DeckView
var _deck_state: Dictionary = {}
var _deck_s := 0.0           ## camera blend 0 (sailing view) .. 1 (deck view), from the zoom
var _deck_show := false
var _deck_trim := 0.0
var _deck_alpha := 0.0
var _deck_hero := Vector3.ZERO


func setup(host: Node) -> void:
	_register_globals()
	_look_profiles = DataLoader.load_dict("res://data/look/look_profiles.json")
	_layer = CanvasLayer.new()
	_layer.layer = 0
	host.add_child(_layer)
	_vp = SubViewport.new()
	_vp.own_world_3d = true
	_vp.msaa_3d = Viewport.MSAA_DISABLED
	_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_vp.size = PROFILES[quality]["size"]
	_layer.add_child(_vp)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.10, 0.22, 0.28)
	var we := WorldEnvironment.new()
	we.environment = env
	_vp.add_child(we)
	_cam = Camera3D.new()
	_cam.fov = FOV_DEG
	_cam.near = 40.0
	_cam.far = 1800.0
	_vp.add_child(_cam)
	_build_ocean()
	_build_island()
	_build_ship()
	_deck = DeckView.new()
	_vp.add_child(_deck)
	_deck.build(1.0 / (PX_PER_M * 4.0))
	_build_weather_fx()
	_post_mat = ShaderMaterial.new()
	_post_mat.shader = load(SHADER_DIR + "post.gdshader")
	_rect = TextureRect.new()
	_rect.texture = _vp.get_texture()
	_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_rect.stretch_mode = TextureRect.STRETCH_SCALE
	_rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	_rect.material = _post_mat
	_layer.add_child(_rect)
	set_quality(quality)
	set_effects(effects)


# ---- interface -------------------------------------------------------------------------------------------------
## Hands the tuning table to the parts of this view that have tuning keys (motion.*, sail.*, look.*).
## H2D-0.2 never did this for the ship motion, so edits to motion.* in the JSON were ignored until now.
func configure_env(values: Dictionary) -> void:
	_motion.configure(values)
	_sail.configure(values)
	_look.configure(values)


func path_name() -> String:
	return "3D"


func describe() -> String:
	var s: Vector2i = PROFILES[quality]["size"]
	return "3D HD-2D, %s, %dx%d internal" % [quality, s.x, s.y]


func set_active(on: bool) -> void:
	_layer.visible = on
	_vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS if on else SubViewport.UPDATE_DISABLED


func set_quality(q: String) -> void:
	if not PROFILES.has(q):
		return
	quality = q
	var p: Dictionary = PROFILES[q]
	_vp.size = p["size"]
	var plane := _ocean.mesh as PlaneMesh
	plane.subdivide_width = int(p["ocean_div"])
	plane.subdivide_depth = int(p["ocean_div"])
	_ocean_mat.set_shader_parameter("detail", float(p["detail"]))
	_ocean_mat.set_shader_parameter("posterize", float(p["posterize"]))
	_cay.set_quality(float(p["shadow_steps"]), 1.0 if q != "dev_lite" else 0.0)
	var prof: Dictionary = (_look_profiles["profiles"] as Dictionary)["dev_lite" if q == "dev_lite" else "standard"]
	var ts: Dictionary = prof["tilt_shift"]
	var vg: Dictionary = prof["vignette"]
	var bl: Dictionary = prof["bloom"]
	_post_mat.set_shader_parameter("focus_y", float(ts["focus_y"]))
	_post_mat.set_shader_parameter("focus_half", float(ts["focus_half_width"]))
	_post_mat.set_shader_parameter("ramp_w", float(ts["ramp_width"]))
	_post_mat.set_shader_parameter("max_blur", float(ts["max_blur_px"]))
	_post_mat.set_shader_parameter("taps", int(ts["taps"]))
	_post_mat.set_shader_parameter("vign_in", float(vg["inner"]))
	_post_mat.set_shader_parameter("vign_out", float(vg["outer"]))
	_post_mat.set_shader_parameter("vign_str", float(vg["strength"]))
	_post_mat.set_shader_parameter("bloom_i", float(bl["intensity"]))
	_post_mat.set_shader_parameter("bloom_thr", float(bl["threshold"]))


func set_effects(level: String) -> void:
	if not EFFECTS.has(level):
		return
	effects = level
	var e: Dictionary = EFFECTS[level]
	var g: Vector2i = e["grid"]
	var n_rain: int = g.x * g.y * int(e["k"])
	var n_spray: int = int(e["spin"]) + 3 * int(e["burst"])
	_fill_identity(_rain.multimesh as MultiMesh, n_rain)
	_fill_identity(_spray.multimesh as MultiMesh, n_spray)
	_rain_mat.set_shader_parameter("grid", Vector2(float(g.x), float(g.y)))
	_rain_mat.set_shader_parameter("cell_m", float(e["cell_m"]))
	_spray_mat.set_shader_parameter("n_spin", float(e["spin"]))
	_spray_mat.set_shader_parameter("n_burst", float(e["burst"]))
	_ocean_mat.set_shader_parameter("rain_cell_m", float(e["cell_m"]))
	_ocean_mat.set_shader_parameter("ring_k", float(e["k"]))


func motion_summary() -> String:
	var o: Dictionary = _last_out
	return "roll %+.1f deg  pitch %+.1f deg  heave %+.2f m  slams %d" % [float(o["roll_deg"]), float(o["pitch_deg"]),
			float(o["heave_m"]), _slam_count]


func land_height_at(x: float, z: float) -> float:
	return _cay.height_at(x, z)


## The land (anvil_cay.json + the baked maps) for the on-foot controller: walkable(), height_smooth(), ...
func land_world() -> CayWorld:
	return _cay


## The pirate on foot, set by the controller every frame: {ashore, x, z, row, frame, zoom, zoom_s}. `ashore` false
## = at sea.
func set_land(state: Dictionary) -> void:
	_land = state


## Where the camera looks now (scene metres): the ship at sea, the pirate ashore, blended while the zoom eases.
func camera_focus() -> Vector2:
	return _focus


## CP-2 ship mode, set every frame by the controller: {on, level, u, v, height, row, frame, cabin_open, rudder, fish_frac, stores}.
## `on` false = the sailing view. The model shows while `on` and while the camera is still easing back out.
func set_deck(state: Dictionary) -> void:
	_deck_state = state


func deck_view() -> DeckView:
	return _deck


## What the deck view is doing now (tests and the HUD): {show, alpha, blend, hero_world}.
func deck_info() -> Dictionary:
	return {"show": _deck_show, "alpha": _deck_alpha, "blend": _deck_s, "hero_world": _deck_hero, "sprite_visible": _ship.visible}


func update_view(v: Dictionary, ship: Dictionary, dt: float) -> void:
	_time = float(v["time"])
	var env: Dictionary = v["env"]
	var lm := LightModel.compute(v, _look.param("haze_density_cap"), _look.param("fog_density_cap"))
	_wave_b = WaveModel.build(float(env["wave_vis_m"]), float(env["wave_to"]), float(env["sea"]), float(v["ice"]),
			float(env["crest_calm"]), float(env["crest_gale"]))
	_set_globals(v, lm)
	_step_motion(dt, v, ship)
	_update_ocean(v, ship, lm)
	_update_weather_fx(v, ship)
	_update_ship(v, ship, dt)
	_update_camera(ship, dt)
	_update_deck(v, ship, dt)
	_update_post(v, lm)


func adjust_pitch(delta_deg: float) -> void:
	pitch_deg = clampf(pitch_deg + delta_deg, 30.0, 62.0)


func adjust_exposure(factor: float) -> void:
	exposure = clampf(exposure * factor, 0.5, 2.5)
	RenderingServer.global_shader_parameter_set("h2d_exposure", exposure)


func set_gamma(g: float) -> void:
	gamma = g
	RenderingServer.global_shader_parameter_set("h2d_gamma", gamma)


## Reads one pixel of a known grey back from the 3D viewport and picks the output transfer that shows it correctly.
func calibrate_gamma() -> void:
	var m := ShaderMaterial.new()
	m.shader = load(SHADER_DIR + "calib.gdshader")
	var q := MeshInstance3D.new()
	var qm := QuadMesh.new()
	qm.size = Vector2(900.0, 900.0)
	q.mesh = qm
	q.material_override = m
	q.custom_aabb = AABB(Vector3(-600, -600, -10), Vector3(1200, 1200, 20))
	_cam.add_child(q)
	q.position = Vector3(0.0, 0.0, -150.0)
	set_gamma(2.2)
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img := _vp.get_texture().get_image()
	var px := img.get_pixel(int(img.get_width() * 0.5), int(img.get_height() * 0.5))
	set_gamma(2.2 if px.g > 0.38 else 1.0)
	calibration_note = "gamma probe read %.3f (0.5 wanted) -> h2d_gamma %.1f" % [px.g, gamma]
	q.queue_free()


# ---- construction ----------------------------------------------------------------------------------------------
func _global_defaults() -> Array:
	var vec3 := RenderingServer.GLOBAL_VAR_TYPE_VEC3
	var vec2 := RenderingServer.GLOBAL_VAR_TYPE_VEC2
	var flt := RenderingServer.GLOBAL_VAR_TYPE_FLOAT
	return [
		["h2d_sun_dir", vec3, Vector3(0.3, 0.8, -0.5)], ["h2d_sun_col", vec3, Vector3(0.6, 0.55, 0.45)],
		["h2d_amb_col", vec3, Vector3(0.3, 0.35, 0.4)], ["h2d_fog_col", vec3, Vector3(0.55, 0.64, 0.64)],
		["h2d_fog_density", flt, 0.002], ["h2d_gamma", flt, 2.2], ["h2d_exposure", flt, 1.25], ["h2d_time", flt, 0.0],
		["h2d_wind_to", vec2, Vector2(0.0, 1.0)], ["h2d_cloud", flt, 0.2], ["h2d_storm", flt, 0.0],
		["h2d_rain", flt, 0.0], ["h2d_adv", vec2, Vector2.ZERO], ["h2d_wind_ms", flt, 0.0], ["h2d_gust", flt, 0.0],
		["h2d_sea", flt, 0.0], ["h2d_overcast", flt, 0.0], ["h2d_fog_start", flt, 190.0],
		["h2d_focus", vec2, Vector2.ZERO], ["h2d_rain_dens", flt, 0.5], ["h2d_night", flt, 0.0],
	]


## The h2d_* global shader uniforms are DECLARED in project.godot ([shader_globals]); a declared global must exist
## before any shader that uses it compiles, which only a project setting guarantees. Here we only SET values.
## (RenderingServer.global_shader_parameter_get_list() is editor-only: outside the editor the engine rejects the call
## with "This function should never be used outside the editor", which was the error at the old line 193.)
func _register_globals() -> void:
	for d in _global_defaults():
		var gname := str(d[0])
		if not ProjectSettings.has_setting("shader_globals/" + gname):
			# Only reachable if project.godot lost its [shader_globals] section. Adding at run time works, but a shader
			# compiled earlier would already have failed, so say so loudly.
			push_error("H2D: global shader uniform '%s' is not declared in project.godot [shader_globals]" % gname)
			RenderingServer.global_shader_parameter_add(gname, d[1], d[2])
		else:
			RenderingServer.global_shader_parameter_set(gname, d[2])
	RenderingServer.global_shader_parameter_set("h2d_gamma", gamma)
	RenderingServer.global_shader_parameter_set("h2d_exposure", exposure)


## Imported resource, loaded the normal way (ResourceLoader). The import settings live in the .import file next to
## each PNG (lossless, no VRAM compression, no mipmaps), so pixel art is never altered by the importer.
func _tex(file: String) -> Texture2D:
	var path := ART_DIR + file
	if not ResourceLoader.exists(path):
		push_error("H2D: %s is not imported. Open the project in the Godot editor once (it imports it), then run." % path)
		return null
	return load(path) as Texture2D


func _mat(shader_file: String) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(SHADER_DIR + shader_file)
	return m


func _build_ocean() -> void:
	_ocean = MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(OCEAN_SIZE_M, OCEAN_SIZE_M)
	_ocean.mesh = plane
	_ocean_mat = _mat("ocean.gdshader")
	_ocean.material_override = _ocean_mat
	_ocean.extra_cull_margin = 40.0
	_ocean.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_vp.add_child(_ocean)


func _build_island() -> void:
	_cay.build(_vp, _ocean_mat, Callable(self, "_tex"), Callable(self, "_mat"))
	_harbor_layout = _cay.harbor_layout()
	var b: Dictionary = _harbor_layout["berth"]
	var hl: float = float(_harbor_layout["ship_half_len_m"]) + 0.8
	var hb: float = float(_harbor_layout["ship_half_beam_m"]) + 0.4
	_ocean_mat.set_shader_parameter("berth_rect", Vector4(float(b["x"]) - hb, float(b["z"]) - hl, float(b["x"]) + hb,
			float(b["z"]) + hl))
	_set_lamps()


## The six harbour lamps (anvil_cay.json \"lamps\") go to every material that lights things at night.
func _set_lamps() -> void:
	var lamps: Array = _cay.lamps()
	var mats: Array = [_ocean_mat]
	mats.append_array(_cay.lamp_materials())
	for i in 6:
		var v := Vector4(0.0, 0.0, 1.0, 0.0)
		if i < lamps.size():
			var l: Dictionary = lamps[i]
			v = Vector4(float(l["x_m"]), float(l["z_m"]), 15.0, 0.9)
		for m in mats:
			(m as ShaderMaterial).set_shader_parameter("lamp%d" % i, v)


## Harbour data for the controller (the layout of anvil_cay.json: berth, approach, dock zone, pier).
func harbor_layout() -> Dictionary:
	return _harbor_layout


func _build_ship() -> void:
	var meta := DataLoader.load_dict(ART_DIR + "ship_sloop.json")
	_ship_mat = _mat("ship.gdshader")
	_ship_mat.set_shader_parameter("hull_tex", _tex(str(meta["hull_sheet"])))
	_ship_mat.set_shader_parameter("sail_tex", _tex(str(meta["sail_sheet"])))
	var fr: Array = meta["frame_px"]
	var pv: Array = meta["pivot_px"]
	var n_trims: int = (meta["trims_deg"] as Array).size()
	_ship_mat.set_shader_parameter("frame_px", Vector2(float(fr[0]), float(fr[1])))
	_ship_mat.set_shader_parameter("pivot_px", Vector2(float(pv[0]), float(pv[1])))
	_ship_mat.set_shader_parameter("hull_grid", Vector2(float(meta["headings"]), 1.0))
	_ship_mat.set_shader_parameter("sail_grid", Vector2(float(meta["headings"]), float(n_trims)))
	_ship_mat.set_shader_parameter("m_per_px", 1.0 / float(meta["px_per_m"]))
	_sail_boxes = DataLoader.load_dict(ART_DIR + "ship_sloop_sailbox.json").get("boxes", [])
	_ship = MeshInstance3D.new()
	_ship.mesh = QuadMesh.new()
	_ship.material_override = _ship_mat
	_ship.custom_aabb = AABB(Vector3(-30.0, -10.0, -30.0), Vector3(60.0, 60.0, 60.0))
	_ship.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_vp.add_child(_ship)


func _fill_identity(mm: MultiMesh, count: int) -> void:
	mm.instance_count = count
	var buf := PackedFloat32Array()
	buf.resize(count * 12)
	for i in count:
		buf[i * 12] = 1.0
		buf[i * 12 + 5] = 1.0
		buf[i * 12 + 10] = 1.0
	mm.buffer = buf


## Rain and spray: MultiMesh quads whose positions the vertex shader computes from the instance id (no per-frame
## CPU work except a handful of uniforms). The MultiMeshInstance3D only sets the culling box; it sits at the focus.
func _build_weather_fx() -> void:
	_rain_mat = _mat("rain.gdshader")
	_rain = _fx_instance(_rain_mat, 260.0)
	_spray_mat = _mat("spray.gdshader")
	_spray = _fx_instance(_spray_mat, 160.0)
	_spray.sorting_offset = 2.0


func _fx_instance(m: ShaderMaterial, half_extent: float) -> MultiMeshInstance3D:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = QuadMesh.new()
	mm.custom_aabb = AABB(Vector3(-half_extent, -20.0, -half_extent), Vector3(half_extent * 2.0, 80.0, half_extent * 2.0))
	var mi := MultiMeshInstance3D.new()
	mi.multimesh = mm
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_vp.add_child(mi)
	return mi


# ---- per frame -------------------------------------------------------------------------------------------------
func _set_globals(v: Dictionary, lm: Dictionary) -> void:
	var g := RenderingServer
	g.global_shader_parameter_set("h2d_sun_dir", lm["sun_dir"])
	g.global_shader_parameter_set("h2d_sun_col", lm["sun_col"])
	g.global_shader_parameter_set("h2d_amb_col", lm["amb_col"])
	g.global_shader_parameter_set("h2d_fog_col", lm["fog_col"])
	g.global_shader_parameter_set("h2d_fog_density", float(lm["fog_density"]))
	g.global_shader_parameter_set("h2d_time", _time)
	g.global_shader_parameter_set("h2d_night", night_level(float(v["hour"]), float(v["storm"]), float(lm["overcast"])))
	g.global_shader_parameter_set("h2d_wind_to", lm["wind_to"])
	g.global_shader_parameter_set("h2d_cloud", float(v["cloud"]))
	g.global_shader_parameter_set("h2d_storm", float(v["storm"]))
	var env: Dictionary = v["env"]
	g.global_shader_parameter_set("h2d_rain", float(env["rain_inst"]))
	g.global_shader_parameter_set("h2d_adv", env["adv"])
	g.global_shader_parameter_set("h2d_wind_ms", float(env["wind_ms"]))
	g.global_shader_parameter_set("h2d_gust", float(env["gust"]))
	g.global_shader_parameter_set("h2d_sea", float(env["sea"]))
	g.global_shader_parameter_set("h2d_overcast", float(lm["overcast"]))
	g.global_shader_parameter_set("h2d_fog_start", _look.fog_start_m(float(v["fog"])))
	var dens: float = (EFFECTS[effects] as Dictionary)["dens"]
	g.global_shader_parameter_set("h2d_rain_dens", dens * _look.param("rain_density"))


## 0 (day) .. 1 (night): the lamps come on through the evening, go out through the dawn, and glow a little in a storm.
static func night_level(hour: float, storm: float, overcast: float) -> float:
	var n := (1.0 - smoothstep(4.5, 6.5, hour)) if hour < 12.0 else smoothstep(17.0, 19.5, hour)
	return clampf(maxf(n, 0.35 * storm + 0.15 * overcast), 0.0, 1.0)


func _set_waves(m: ShaderMaterial) -> void:
	var ws: Array = _wave_b["waves"]
	for i in 4:
		var w: Array = ws[i]
		m.set_shader_parameter("w%d" % i, Vector4(float(w[0]), float(w[1]), float(w[2]), float(w[3])))
	m.set_shader_parameter("crest_pb", Vector2(float(_wave_b["p"]), float(_wave_b["bias"])))


func _wave_amp(v: Dictionary) -> float:
	var env: Dictionary = v["env"]
	return 0.5 * float(env["wave_vis_m"]) * (1.0 - 0.85 * clampf(float(v["ice"]), 0.0, 1.0))


func _update_ocean(v: Dictionary, ship: Dictionary, lm: Dictionary) -> void:
	var env: Dictionary = v["env"]
	var sea := float(env["sea"])
	_set_waves(_ocean_mat)
	_ocean_mat.set_shader_parameter("wave_norm", _wave_amp(v))
	_ocean_mat.set_shader_parameter("foam_amount", clampf(0.04 + 1.0 * smoothstep(0.08, 0.9, sea), 0.0, 1.0))
	_ocean_mat.set_shader_parameter("normal_gain", 1.0 + 0.6 * sea)
	_ocean_mat.set_shader_parameter("ice_cover", float(v["ice"]))
	_ocean_mat.set_shader_parameter("deep_col", lm["deep"])
	_ocean_mat.set_shader_parameter("shallow_col", lm["shallow"])
	_ocean_mat.set_shader_parameter("foam_col", lm["foam"])
	_ocean_mat.set_shader_parameter("sun_k", clampf((lm["sun_col"] as Vector3).length() / 0.6, 0.0, 1.0))
	var h := deg_to_rad(float(ship["heading_deg"]))
	var berth: Dictionary = _harbor_layout.get("berth", {"x": 0.0, "z": 0.0})
	var bd := Vector2(float(ship["x"]) - float(berth["x"]), float(ship["z"]) - float(berth["z"])).length()
	var moor := float(ship.get("moor", 0.0))
	var show := (1.0 - smoothstep(110.0, 170.0, bd)) * (1.0 - smoothstep(0.3, 0.9, moor))
	_ocean_mat.set_shader_parameter("berth_show", show)
	_ocean_mat.set_shader_parameter("ship_pos", Vector2(float(ship["x"]), float(ship["z"])))
	_ocean_mat.set_shader_parameter("ship_dir", Vector2(sin(h), -cos(h)))
	_ocean_mat.set_shader_parameter("ship_speed", float(ship["scene_speed"]))
	_ocean_mat.set_shader_parameter("ship_curve", float(ship.get("curve", 0.0)))
	var speed_frac := clampf(float(ship["scene_speed"]) / 25.0, 0.0, 1.0)
	_ocean_mat.set_shader_parameter("ship_roll", float(_last_out["roll_deg"]) / 10.0)
	_ocean_mat.set_shader_parameter("wash", clampf(0.15 * speed_frac + 0.55 * sea + 0.5 * _motion.slam, 0.0, 1.0))
	_ocean_mat.set_shader_parameter("slam", _motion.slam)
	var cell := OCEAN_SIZE_M * _ocean.scale.x / float(PROFILES[quality]["ocean_div"])
	_ocean.position = Vector3(roundf(_focus.x / cell) * cell, 0.0, roundf(_focus.y / cell) * cell)


## The hull feels the same waves the ocean draws. Spray events (bow or a rail meeting the water fast) become bursts.
func _step_motion(dt: float, v: Dictionary, ship: Dictionary) -> void:
	var env: Dictionary = v["env"]
	var m := _motion
	m.gain_override = [0.0, 0.5, -1.0][motion_mode]
	var no_go := float(v["no_go_deg"])
	var hd := float(ship["heading_deg"])
	var off := absf(EnvModel.wrap180(hd - float(v["wind_from_deg"])))
	m.step(minf(dt, 0.1), _wave_b, {"x": float(ship["x"]), "z": float(ship["z"]), "heading_deg": hd, "t": _time,
			"wind_to": env["wind_to"], "wind_ms": float(env["wind_ms"]), "off_deg": off, "no_go_deg": no_go,
			"sea": float(env["sea"])})
	_last_out = m.out()
	var hr := deg_to_rad(hd)
	var f := Vector2(sin(hr), -cos(hr))
	var sb := Vector2(-f.y, f.x)
	var pos := Vector2(float(ship["x"]), float(ship["z"]))
	var vel := f * float(ship["scene_speed"])
	for e in m.events:
		var kind: int = e[0]
		var power: float = e[1]
		var origin := pos + f * (ShipMotion.SHIP_LEN * 0.42)
		var dir := f
		if kind == ShipMotion.STARBOARD:
			origin = pos + f * (ShipMotion.SHIP_LEN * 0.10) + sb * (ShipMotion.SHIP_BEAM * 0.5)
			dir = (sb + f * 0.3).normalized()
		elif kind == ShipMotion.PORT:
			origin = pos + f * (ShipMotion.SHIP_LEN * 0.10) - sb * (ShipMotion.SHIP_BEAM * 0.5)
			dir = (-sb + f * 0.3).normalized()
		_bursts[_burst_next] = [origin.x, origin.y, _time, power, dir.x, dir.y, vel.x, vel.y]
		_burst_next = (_burst_next + 1) % 3
		_slam_count += 1


## Visible state of the drawn ship from the sea and the wind: lean, belly, flutter, lift.
func _update_ship(v: Dictionary, ship: Dictionary, dt: float) -> void:
	var env: Dictionary = v["env"]
	var hd := float(ship["heading_deg"])
	var frame := ShipSprite.heading_frame(hd)
	_trim_row = ShipSprite.trim_row_sticky(hd, float(v["wind_from_deg"]), _trim_row)
	var row := _trim_row
	_ship_mat.set_shader_parameter("hull_cell", Vector2(float(frame), 0.0))
	_ship_mat.set_shader_parameter("sail_cell", Vector2(float(frame), float(row)))
	var x := float(ship["x"])
	var z := float(ship["z"])
	_ship_mat.set_shader_parameter("bob_m", roundf(float(_last_out["heave_m"]) * PX_PER_M) / PX_PER_M)  # whole art pixels
	_ship_mat.set_shader_parameter("sprite_light", 0.7)
	var hr := deg_to_rad(hd)
	var f := Vector2(sin(hr), -cos(hr))
	var sb := Vector2(-f.y, f.x)
	var lean := sb * tan(deg_to_rad(float(_last_out["roll_deg"]))) - f * tan(deg_to_rad(float(_last_out["pitch_deg"])))
	_ship_mat.set_shader_parameter("lean", lean)
	var wind := float(env["wind_inst_kn"])
	var no_go := float(v["no_go_deg"])
	var off := absf(EnvModel.wrap180(hd - float(v["wind_from_deg"])))
	var slack_k := 1.0 - clampf(float(ship.get("moor", 0.0)), 0.0, 1.0)   # moored: no wind in the sails, they hang slack
	_sail.step(minf(dt, 0.1), wind * slack_k, float(env["gust"]) * slack_k, off, no_go, _time)
	var so := _sail.out()
	var loose := maxf(float(so["slack"]), float(so["luff"]))
	var folds := clampf(loose * (1.0 - 0.5 * clampf(float(so["fill"]), 0.0, 1.0)), 0.0, 1.0)
	_ship_mat.set_shader_parameter("sail_belly", float(so["belly_px"]))
	_ship_mat.set_shader_parameter("sail_flap", Vector2(float(so["flap_px"]), float(so["flap_phase"])))
	_ship_mat.set_shader_parameter("sail_folds", folds)
	if row < _sail_boxes.size() and frame < (_sail_boxes[row] as Array).size():
		var bx: Array = _sail_boxes[row][frame]
		_ship_mat.set_shader_parameter("sail_box", Vector4(float(bx[0]), float(bx[1]), float(bx[2]), float(bx[3])))
	var wt: Vector2 = env["wind_to"]
	_ship_mat.set_shader_parameter("lee", Vector2(wt.x, wt.y * 0.74))
	_ship.position = Vector3(x, 0.0, z)


## The rain and spray follow the camera focus; every number they use comes from the shared environment (env_model.gd).
func _update_weather_fx(v: Dictionary, ship: Dictionary) -> void:
	var env: Dictionary = v["env"]
	var sea := float(env["sea"])
	var wt: Vector2 = env["wind_to"]
	var wms := float(env["wind_ms"])
	var e: Dictionary = EFFECTS[effects]
	var g: Vector2i = e["grid"]
	var cell: float = e["cell_m"]
	# the rain leans with the MEAN wind everywhere (gusts add lean inside the gust patch, in rain.gdshader), and light rain
	# stays nearly upright while a downpour is driven
	var rain_i := float(env["rain_inst"])
	var mean_ms := float(env["wind_kn"]) * EnvModel.KN_TO_MS
	var drift := wt * minf(mean_ms * _look.param("rain_drift_factor") * lerpf(0.5, 1.0, rain_i), RAIN_DRIFT_MAX_MS)
	var rc := _look.rain_character(rain_i)
	RenderingServer.global_shader_parameter_set("h2d_focus", Vector2(float(ship["x"]), float(ship["z"])))
	_rain_mat.set_shader_parameter("fall_ms", float(rc["fall_ms"]))
	_rain_mat.set_shader_parameter("streak_m", float(rc["streak_m"]))
	_rain_mat.set_shader_parameter("alpha_k", float(rc["alpha"]))
	_rain_mat.set_shader_parameter("splash_k", float(rc["splash"]))
	_rain_mat.set_shader_parameter("gust_bend", _look.param("rain_gust_bend"))
	_ocean_mat.set_shader_parameter("ring_size", lerpf(0.6, 1.0, rain_i))
	var center := _focus + Vector2(0.0, RAIN_CENTER_SOUTH_M) + drift * 0.6
	var base := Vector2(floorf(center.x / cell) - float(g.x) * 0.5, floorf(center.y / cell) - float(g.y) * 0.5)
	_rain_mat.set_shader_parameter("base_cell", Vector2(roundf(base.x), roundf(base.y)))
	_rain_mat.set_shader_parameter("drift", drift)
	_rain.position = Vector3(center.x, 0.0, center.y)
	_set_waves(_rain_mat)
	_set_waves(_spray_mat)
	_spray_mat.set_shader_parameter("focus", _focus + Vector2(0.0, 10.0))
	_spray.position = Vector3(_focus.x, 0.0, _focus.y + 10.0)
	_spray_mat.set_shader_parameter("wind_vel", wt * wms)
	_spray_mat.set_shader_parameter("spray_level", smoothstep(0.30, 0.90, sea))
	_spray_mat.set_shader_parameter("crest_min", lerpf(0.80, 0.55, sea))
	_spray_mat.set_shader_parameter("wave_norm", _wave_amp(v))
	for i in 3:
		var b: Array = _bursts[i]
		_spray_mat.set_shader_parameter("burst_a%d" % i, Vector4(float(b[0]), float(b[1]), float(b[2]), float(b[3])))
		_spray_mat.set_shader_parameter("burst_b%d" % i, Vector4(float(b[4]), float(b[5]), float(b[6]), float(b[7])))


## The camera looks at the ship at sea and at the pirate ashore. The zoom eases between 1 (sea: 3.6 px per metre)
## and the land
## zoom (about 4: 14.4 px per metre, so a 28 px pirate is 1.9 m tall and one sprite pixel is one screen pixel).
func _update_camera(ship: Dictionary, dt: float) -> void:
	var ashore: bool = bool(_land.get("ashore", false))
	var zt := float(_land.get("zoom_to", _land.get("zoom", 4.0))) if ashore else 1.0
	var tau := maxf(float(_land.get("zoom_s", 1.1)), 0.05) / 3.0
	_zoom = zt if absf(_zoom - zt) < 0.002 else lerpf(_zoom, zt, 1.0 - exp(-minf(dt, 0.1) / tau))
	var zmax := maxf(float(_land.get("zoom", 4.0)), 1.01)
	var zref := maxf(float(_land.get("zoom_ref", zmax)), 1.01)     # CP-2: the deck view reaches full follow at its own, lower zoom (the nest)
	var s := clampf((_zoom - 1.0) / (zref - 1.0), 0.0, 1.0)
	_deck_s = s
	var ship_t := Vector2(float(ship["x"]), float(ship["z"]) - TARGET_LEAD_M)
	var hero_t := Vector2(float(_land.get("x", ship_t.x)), float(_land.get("z", ship_t.y)) - 1.6)
	_focus = ship_t.lerp(hero_t, s)
	var gy := 0.0
	if s > 0.001:
		gy = _cay.height_smooth(_focus.x, _focus.y)
		if _land.has("focus_y"):
			gy = float(_land["focus_y"])       # CP-2: on a ship the camera looks at the deck, not the sea floor
		gy = lerpf(0.0, maxf(gy, 0.0), s)
	var dist := ART_H / (2.0 * tan(deg_to_rad(FOV_DEG) * 0.5) * PX_PER_M * _zoom)
	var p := deg_to_rad(pitch_deg)
	var target := Vector3(_focus.x, gy, _focus.y)
	_cam.near = clampf(dist * 0.18, 8.0, 40.0)
	_cam.position = target + Vector3(0.0, dist * sin(p), dist * cos(p))
	_cam.rotation_degrees = Vector3(-pitch_deg, 0.0, 0.0)
	_ship_mat.set_shader_parameter("cam_cos", cos(p))
	_ship_mat.set_shader_parameter("cam_tan", tan(p))
	_cay.update(_focus, _zoom)
	if not bool(_deck_state.get("on", false)):    # on a ship deck the pirate is placed by _update_deck at his rolled position
		_cay.set_hero(ashore, float(_land.get("x", 0.0)), float(_land.get("z", 0.0)), int(_land.get("row", 0)),
				int(_land.get("frame", 0)), zmax)     # CP-1: the on-foot sprites keep ONE world scale (see cay_world.set_sprite_zoom)
	var os := clampf(1.6 / _zoom, 0.4, 1.0)
	_ocean.scale = Vector3(os, 1.0, os)


## CP-2: the walkable ship. Pose from the same ship motion as the sprite, boom and wheel follow the sails and the helm, the pirate is
## drawn at his place ON the rolling deck, and the shader gets his screen position for the see-through hole.
func _update_deck(v: Dictionary, ship: Dictionary, dt: float) -> void:
	var st := _deck_state
	var on := bool(st.get("on", false))
	_deck_show = on or (_deck_show and _deck_s > 0.02)
	var target_a := smoothstep(0.35, 0.8, _deck_s) if _deck_show else 0.0
	_deck_alpha = target_a
	_ship.visible = _deck_alpha < 0.55
	_deck.set_alpha(_deck_alpha)
	if not _deck_show:
		return
	var hd := float(ship["heading_deg"])
	_deck.set_pose(Vector2(float(ship["x"]), float(ship["z"])), hd, float(_last_out["roll_deg"]), float(_last_out["pitch_deg"]),
			float(_last_out["heave_m"]), DECK_MOTION)
	_deck.set_level(int(st.get("level", 0)))
	var trims: Array = [-80.0, -45.0, 0.0, 45.0, 80.0]
	_deck_trim = move_toward(_deck_trim, float(trims[clampi(_trim_row, 0, 4)]), 140.0 * minf(dt, 0.1))
	_deck.set_trim(_deck_trim)
	_deck.set_rudder(float(st.get("rudder", 0.0)))
	_deck.set_fish_fill(float(st.get("fish_frac", 0.0)))
	_deck.set_cabin_open(bool(st.get("cabin_open", false)), minf(dt, 0.1))
	_deck.set_aspect(float(_vp.size.x) / float(_vp.size.y))
	_deck.set_wet(clampf(float(v.get("rain", 0.0)), 0.0, 1.0))
	if st.has("stores"):
		_deck.set_stores(st["stores"])
		_deck_state.erase("stores")
	if not on:
		return
	var level := int(st.get("level", 0))
	var feet := DeckView.ShipMesh.p(float(st.get("u", 0.0)), float(st.get("v", 0.0)), DeckLayout.floor_y(level) + float(st.get("height", 0.0)))
	var w := _deck.to_world(feet)
	_deck_hero = w
	_cay.set_hero(true, w.x, w.z, int(st.get("row", 0)), int(st.get("frame", 0)), float(_land.get("zoom", 4.0)), w.y)
	var chest := w + Vector3(0.0, 1.0, 0.0)
	var px := _cam.unproject_position(chest)
	var in_nest := level == DeckLayout.L_NEST or (float(st.get("height", 0.0)) > 4.0)
	_deck.set_hero_screen(Vector2(px.x / float(_vp.size.x), px.y / float(_vp.size.y)), (chest - _cam.global_position).length(), in_nest)


## Colour grade only. H2D-0.3 removed the screen-space haze and lightning flash that H2D-0.2 laid over the picture:
## fog is real distance fog in every 3D shader and lightning is a boost of the scene's own light (light_model.gd).
func _update_post(_v: Dictionary, lm: Dictionary) -> void:
	_post_mat.set_shader_parameter("sat", float(lm["sat"]))
	_post_mat.set_shader_parameter("con", float(lm["con"]))
	_post_mat.set_shader_parameter("tint", lm["tint"])
