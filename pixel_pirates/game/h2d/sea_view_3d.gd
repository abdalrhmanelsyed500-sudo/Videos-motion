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
const DataLoader := preload("res://core/data_loader.gd")
const SHADER_DIR := "res://h2d/shaders/"
const ART_DIR := "res://h2d/art/"
const FOV_DEG := 22.0
const DEFAULT_PITCH_DEG := 48.0
const PX_PER_M := 3.6
const ART_H := 360.0
const TARGET_LEAD_M := 9.0  ## the camera looks this far north of the ship, so the ship sits low in the picture
const OCEAN_SIZE_M := 420.0
const PROFILES := {
	"dev_lite": {"size": Vector2i(640, 360), "ocean_div": 64, "detail": 0.0, "shadow_steps": 6.0, "posterize": 12.0},
	"standard": {"size": Vector2i(1280, 720), "ocean_div": 128, "detail": 1.0, "shadow_steps": 10.0, "posterize": 16.0},
	"ultra": {"size": Vector2i(1920, 1080), "ocean_div": 192, "detail": 1.0, "shadow_steps": 12.0, "posterize": 24.0},
}

var quality := "dev_lite"
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
var _island: MeshInstance3D
var _island_mat: ShaderMaterial
var _trees: MultiMeshInstance3D
var _ship: MeshInstance3D
var _ship_mat: ShaderMaterial
var _post_mat: ShaderMaterial
var _look_profiles: Dictionary = {}
var _island_meta: Dictionary = {}
var _island_img: Image
var _wave_params: Array = []
var _time := 0.0


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


# ---- interface -------------------------------------------------------------------------------------------------
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
	_island_mat.set_shader_parameter("shadow_steps", float(p["shadow_steps"]))
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


func land_height_at(x: float, z: float) -> float:
	if _island_img == null:
		return -99.0
	var size: float = float(_island_meta["size_m"])
	var w := _island_img.get_width()
	var h := _island_img.get_height()
	var px := int(floorf((x - _island_origin().x) / size * float(w) + float(w) * 0.5))
	var py := int(floorf((z - _island_origin().y) / size * float(h) + float(h) * 0.5))
	if px < 0 or py < 0 or px >= w or py >= h:
		return -99.0
	return _island_img.get_pixel(px, py).r * 48.0 - 8.0


func update_view(v: Dictionary, ship: Dictionary, _dt: float) -> void:
	_time = float(v["time"])
	var lm := LightModel.compute(v)
	_set_globals(v, lm)
	_update_ocean(v, ship, lm)
	_update_ship(v, ship)
	_update_camera(ship)
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
	var px := img.get_pixel(img.get_width() / 2, img.get_height() / 2)
	set_gamma(2.2 if px.g > 0.38 else 1.0)
	calibration_note = "gamma probe read %.3f (0.5 wanted) -> h2d_gamma %.1f" % [px.g, gamma]
	q.queue_free()


# ---- construction ----------------------------------------------------------------------------------------------
func _register_globals() -> void:
	var existing: Array = RenderingServer.global_shader_parameter_get_list()
	var vec3 := RenderingServer.GLOBAL_VAR_TYPE_VEC3
	var vec2 := RenderingServer.GLOBAL_VAR_TYPE_VEC2
	var flt := RenderingServer.GLOBAL_VAR_TYPE_FLOAT
	var defs: Array = [
		["h2d_sun_dir", vec3, Vector3(0.3, 0.8, -0.5)], ["h2d_sun_col", vec3, Vector3(0.6, 0.55, 0.45)],
		["h2d_amb_col", vec3, Vector3(0.3, 0.35, 0.4)], ["h2d_fog_col", vec3, Vector3(0.55, 0.64, 0.64)],
		["h2d_fog_density", flt, 0.002], ["h2d_gamma", flt, 2.2], ["h2d_exposure", flt, 1.25], ["h2d_time", flt, 0.0],
		["h2d_wind_to", vec2, Vector2(0.0, 1.0)], ["h2d_cloud", flt, 0.2], ["h2d_storm", flt, 0.0],
		["h2d_rain", flt, 0.0],
	]
	for d in defs:
		if not existing.has(StringName(d[0])):
			RenderingServer.global_shader_parameter_add(d[0], d[1], d[2])
	RenderingServer.global_shader_parameter_set("h2d_gamma", gamma)
	RenderingServer.global_shader_parameter_set("h2d_exposure", exposure)


func _tex(file: String) -> ImageTexture:
	var img := Image.load_from_file(ART_DIR + file)
	if img == null:
		push_error("H2D: cannot load " + ART_DIR + file)
		return null
	img.convert(Image.FORMAT_RGBA8)
	return ImageTexture.create_from_image(img)


func _mat(shader_file: String) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(SHADER_DIR + shader_file)
	return m


func _island_origin() -> Vector2:
	return Vector2.ZERO


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
	_island_meta = DataLoader.load_dict(ART_DIR + "island_anvil.json")
	var files: Dictionary = _island_meta["files"]
	var size: float = float(_island_meta["size_m"])
	var data_img := Image.load_from_file(ART_DIR + str(files["data"]))
	data_img.convert(Image.FORMAT_RGBA8)
	_island_img = data_img
	var data_tex := ImageTexture.create_from_image(data_img)
	_ocean_mat.set_shader_parameter("island_data", data_tex)
	_ocean_mat.set_shader_parameter("island_origin", _island_origin())
	_ocean_mat.set_shader_parameter("island_size", size)
	_island_mat = _mat("island.gdshader")
	_island_mat.set_shader_parameter("albedo_tex", _tex(str(files["albedo"])))
	_island_mat.set_shader_parameter("data_tex", data_tex)
	_island_mat.set_shader_parameter("normal_tex", _tex(str(files["normal"])))
	_island_mat.set_shader_parameter("island_size", size)
	_island = MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(size, size)
	plane.subdivide_width = 95
	plane.subdivide_depth = 95
	_island.mesh = plane
	_island.material_override = _island_mat
	_island.position = Vector3(_island_origin().x, 0.0, _island_origin().y)
	_island.extra_cull_margin = 40.0
	_island.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_vp.add_child(_island)
	_build_trees()


func _build_trees() -> void:
	var atlas: Dictionary = _island_meta["atlas"]
	var list: Array = _island_meta["trees"]
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = QuadMesh.new()
	mm.instance_count = list.size()
	for i in list.size():
		var t: Dictionary = list[i]
		mm.set_instance_transform(i, Transform3D(Basis.IDENTITY, Vector3(float(t["x_m"]), float(t["y_m"]), float(t["z_m"]))))
		mm.set_instance_custom_data(i, Color(float(t["type"]), float(t["scale"]), 0.0, 0.0))
	mm.custom_aabb = AABB(Vector3(-90.0, -10.0, -90.0), Vector3(180.0, 80.0, 180.0))
	_trees = MultiMeshInstance3D.new()
	_trees.multimesh = mm
	var m := _mat("trees.gdshader")
	m.set_shader_parameter("atlas", _tex(str(atlas["file"])))
	var cell: Array = atlas["cell_px"]
	var piv: Array = atlas["pivot_px"]
	m.set_shader_parameter("cell_px", Vector2(float(cell[0]), float(cell[1])))
	m.set_shader_parameter("pivot_px", Vector2(float(piv[0]), float(piv[1])))
	m.set_shader_parameter("atlas_grid", Vector2(float(atlas["cols"]), float(atlas["rows"])))
	m.set_shader_parameter("m_per_px", 1.0 / PX_PER_M)
	_trees.material_override = m
	_trees.position = Vector3(_island_origin().x, 0.0, _island_origin().y)
	_trees.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_vp.add_child(_trees)


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
	_ship = MeshInstance3D.new()
	_ship.mesh = QuadMesh.new()
	_ship.material_override = _ship_mat
	_ship.custom_aabb = AABB(Vector3(-30.0, -10.0, -30.0), Vector3(60.0, 60.0, 60.0))
	_ship.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_vp.add_child(_ship)


# ---- per frame -------------------------------------------------------------------------------------------------
func _set_globals(v: Dictionary, lm: Dictionary) -> void:
	var g := RenderingServer
	g.global_shader_parameter_set("h2d_sun_dir", lm["sun_dir"])
	g.global_shader_parameter_set("h2d_sun_col", lm["sun_col"])
	g.global_shader_parameter_set("h2d_amb_col", lm["amb_col"])
	g.global_shader_parameter_set("h2d_fog_col", lm["fog_col"])
	g.global_shader_parameter_set("h2d_fog_density", float(lm["fog_density"]))
	g.global_shader_parameter_set("h2d_time", _time)
	g.global_shader_parameter_set("h2d_wind_to", lm["wind_to"])
	g.global_shader_parameter_set("h2d_cloud", float(v["cloud"]))
	g.global_shader_parameter_set("h2d_storm", float(v["storm"]))
	g.global_shader_parameter_set("h2d_rain", float(v["rain"]))


func _update_ocean(v: Dictionary, ship: Dictionary, lm: Dictionary) -> void:
	_wave_params = WaveModel.params(float(v["wave_m"]), float(v["wind_from_deg"]), float(v["ice"]))
	for i in 4:
		var w: Array = _wave_params[i]
		_ocean_mat.set_shader_parameter("w%d" % i, Vector4(float(w[0]), float(w[1]), float(w[2]), float(w[3])))
	var amp := 0.5 * float(v["wave_m"]) * (1.0 - 0.85 * clampf(float(v["ice"]), 0.0, 1.0))
	_ocean_mat.set_shader_parameter("wave_norm", amp)
	var foam := 0.12 + float(v["wind_kn"]) / 40.0 + 0.9 * float(v["storm"])
	_ocean_mat.set_shader_parameter("foam_amount", clampf(foam, 0.0, 1.0))
	_ocean_mat.set_shader_parameter("ice_cover", float(v["ice"]))
	_ocean_mat.set_shader_parameter("deep_col", lm["deep"])
	_ocean_mat.set_shader_parameter("shallow_col", lm["shallow"])
	_ocean_mat.set_shader_parameter("foam_col", lm["foam"])
	_ocean_mat.set_shader_parameter("sun_k", clampf((lm["sun_col"] as Vector3).length() / 0.6, 0.0, 1.0))
	var h := deg_to_rad(float(ship["heading_deg"]))
	_ocean_mat.set_shader_parameter("ship_pos", Vector2(float(ship["x"]), float(ship["z"])))
	_ocean_mat.set_shader_parameter("ship_dir", Vector2(sin(h), -cos(h)))
	_ocean_mat.set_shader_parameter("ship_speed", float(ship["scene_speed"]))
	var cell := OCEAN_SIZE_M / float(PROFILES[quality]["ocean_div"])
	_ocean.position = Vector3(roundf(float(ship["x"]) / cell) * cell, 0.0, roundf(float(ship["z"]) / cell) * cell)


func _update_ship(v: Dictionary, ship: Dictionary) -> void:
	var hd := float(ship["heading_deg"])
	var frame := ShipSprite.heading_frame(hd)
	var row := ShipSprite.trim_row(hd, float(v["wind_from_deg"]))
	_ship_mat.set_shader_parameter("hull_cell", Vector2(float(frame), 0.0))
	_ship_mat.set_shader_parameter("sail_cell", Vector2(float(frame), float(row)))
	var x := float(ship["x"])
	var z := float(ship["z"])
	var bob := WaveModel.height(_wave_params, x, z, _time) * 0.8
	_ship_mat.set_shader_parameter("bob_m", roundf(bob * PX_PER_M) / PX_PER_M)  # whole art pixels only
	_ship_mat.set_shader_parameter("sprite_light", 0.7)
	_ship.position = Vector3(x, 0.0, z)


func _update_camera(ship: Dictionary) -> void:
	var dist := ART_H / (2.0 * tan(deg_to_rad(FOV_DEG) * 0.5) * PX_PER_M)
	var p := deg_to_rad(pitch_deg)
	var target := Vector3(float(ship["x"]), 0.0, float(ship["z"]) - TARGET_LEAD_M)
	_cam.position = target + Vector3(0.0, dist * sin(p), dist * cos(p))
	_cam.rotation_degrees = Vector3(-pitch_deg, 0.0, 0.0)


func _update_post(v: Dictionary, lm: Dictionary) -> void:
	var storm := float(v["storm"])
	_post_mat.set_shader_parameter("rain", float(v["rain"]))
	_post_mat.set_shader_parameter("rain_slant", (lm["wind_to"] as Vector2).x * 0.35)
	_post_mat.set_shader_parameter("flash", LightModel.flash(_time, storm))
	_post_mat.set_shader_parameter("haze", clampf(0.35 * float(v["fog"]) + 0.15 * storm, 0.0, 0.6))
	_post_mat.set_shader_parameter("haze_col", lm["fog_col"])
	_post_mat.set_shader_parameter("sat", float(lm["sat"]))
	_post_mat.set_shader_parameter("con", float(lm["con"]))
	_post_mat.set_shader_parameter("tint", lm["tint"])
	_post_mat.set_shader_parameter("time", _time)
