extends Node3D
## Pixel Pirates - Module A1 smoke test.
## Goal: prove on YOUR machine that (1) the engine/OS/GPU are what we expect and
## (2) the "HD-2D" look is possible in stock Godot: pixel sprites standing in a 3D
## diorama, pitched perspective camera, tilt-shift-style depth of field, bloom,
## warm directional light with real shadows, volumetric fog.
## Keys:  D = depth of field   G = glow/bloom   F = fog   S = shadows   Esc = quit

const PIXEL_SIZE := 0.07          # world units per sprite pixel (16x24 sprite = 1.12 x 1.68 units)

var _env: Environment
var _cam_attr: CameraAttributesPractical
var _sun: DirectionalLight3D
var _label: Label
var _info: Dictionary = {}

func _ready() -> void:
	_info = _report()
	_build_world()
	_build_hud()
	_print_report()

# ------------------------------------------------------------------ world
func _build_world() -> void:
	# Camera: narrow FOV + steep pitch = diorama look.  Pitch = atan(9 / 11) ~ 39 degrees.
	var cam := Camera3D.new()
	cam.fov = 22.0
	cam.position = Vector3(0, 9, 11)
	add_child(cam)
	cam.look_at(Vector3.ZERO, Vector3.UP)

	# Depth of field. Because the camera is pitched, distance grows from the bottom of
	# the screen to the top, so plain distance-based blur gives a horizontal in-focus
	# band = tilt-shift, with no custom shader.
	_cam_attr = CameraAttributesPractical.new()
	_cam_attr.dof_blur_far_enabled = true
	_cam_attr.dof_blur_far_distance = 16.0
	_cam_attr.dof_blur_far_transition = 7.0
	_cam_attr.dof_blur_near_enabled = true
	_cam_attr.dof_blur_near_distance = 10.5
	_cam_attr.dof_blur_near_transition = 3.5
	_cam_attr.dof_blur_amount = 0.12
	cam.attributes = _cam_attr

	# Environment: bloom, fog, filmic tonemap, slight colour grade.
	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.background_color = Color("14222b")
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color("5d6f7d")
	_env.ambient_light_energy = 0.7
	_env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	_env.glow_enabled = true
	_env.glow_intensity = 0.8
	_env.glow_bloom = 0.15
	_env.volumetric_fog_enabled = true
	_env.volumetric_fog_density = 0.015
	_env.volumetric_fog_albedo = Color("c9a46a")
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.15
	_env.adjustment_contrast = 1.08
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)

	# Warm sun with shadows (sprites cast shadows through alpha-cut).
	_sun = DirectionalLight3D.new()
	_sun.light_color = Color("ffd9a0")
	_sun.light_energy = 1.6
	_sun.shadow_enabled = true
	_sun.rotation_degrees = Vector3(-48, 32, 0)
	add_child(_sun)

	# Ground: nearest-filtered 16x16 pixel texture tiled over a plane.
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(60, 60)
	ground.mesh = plane
	var gm := StandardMaterial3D.new()
	gm.albedo_texture = _make_ground_texture()
	gm.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	gm.uv1_scale = Vector3(60, 60, 1)
	ground.material_override = gm
	add_child(ground)

	# Sprites: a row receding in depth so you can see sharp centre vs blurred ends.
	var tex := _make_sprite_texture()
	for i in range(9):
		var s := Sprite3D.new()
		s.texture = tex
		s.pixel_size = PIXEL_SIZE
		s.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
		s.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		s.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
		s.shaded = true
		s.double_sided = true
		s.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		s.centered = true
		s.offset = Vector2(0, 12)            # sprite feet at y=0 (24 px tall, centered -> shift up 12 px)
		s.position = Vector3(-4.0 + i * 1.0, 0.0, 6.0 - i * 1.6)
		add_child(s)

# 16x24 placeholder pirate drawn in code (no external art needed for the test).
func _make_sprite_texture() -> ImageTexture:
	var img := Image.create_empty(16, 24, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	img.fill_rect(Rect2i(4, 0, 8, 3), Color("2b1d2e"))      # hat top
	img.fill_rect(Rect2i(2, 3, 12, 2), Color("2b1d2e"))     # hat brim
	img.fill_rect(Rect2i(5, 5, 6, 5), Color("e0b48a"))      # face
	img.set_pixel(6, 7, Color("1a1020")); img.set_pixel(9, 7, Color("1a1020"))   # eyes
	img.fill_rect(Rect2i(3, 10, 10, 8), Color("a8322e"))    # coat
	img.fill_rect(Rect2i(1, 11, 2, 6), Color("a8322e"))     # left arm
	img.fill_rect(Rect2i(13, 11, 2, 6), Color("a8322e"))    # right arm
	img.fill_rect(Rect2i(7, 10, 2, 8), Color("e8d9b5"))     # shirt
	img.fill_rect(Rect2i(4, 18, 3, 5), Color("2f3a4a"))     # left leg
	img.fill_rect(Rect2i(9, 18, 3, 5), Color("2f3a4a"))     # right leg
	img.fill_rect(Rect2i(3, 23, 4, 1), Color("1a1020"))     # boots
	img.fill_rect(Rect2i(9, 23, 4, 1), Color("1a1020"))
	return ImageTexture.create_from_image(img)

func _make_ground_texture() -> ImageTexture:
	var img := Image.create_empty(16, 16, false, Image.FORMAT_RGBA8)
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var cols := [Color("6f7d3c"), Color("7d8a45"), Color("5f6c34"), Color("8a7a48")]
	for y in 16:
		for x in 16:
			img.set_pixel(x, y, cols[rng.randi_range(0, cols.size() - 1)])
	return ImageTexture.create_from_image(img)

# ------------------------------------------------------------------ HUD / report
func _build_hud() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	_label = Label.new()
	_label.position = Vector2(12, 8)
	_label.add_theme_color_override("font_color", Color.WHITE)
	_label.add_theme_color_override("font_outline_color", Color.BLACK)
	_label.add_theme_constant_override("outline_size", 6)
	layer.add_child(_label)

func _report() -> Dictionary:
	var mem := OS.get_memory_info()
	return {
		"engine": Engine.get_version_info()["string"],
		"os": OS.get_name(),
		"64-bit build": OS.has_feature("64"),
		"double-precision build": OS.has_feature("double"),
		"gpu": RenderingServer.get_video_adapter_name(),
		"graphics api": RenderingServer.get_video_adapter_api_version(),
		"renderer": str(ProjectSettings.get_setting("rendering/renderer/rendering_method")),
		"cpu": OS.get_processor_name(),
		"cpu threads": OS.get_processor_count(),
		"ram MB": floori(float(mem.get("physical", -1)) / 1048576.0),
		# Float precision demo: a single-precision Vector3 cannot hold 100000.001 -> prints 100000 (why we need a floating origin).
		"Vector3.x for 100000.001": Vector3(100000.001, 0, 0).x,
	}

func _print_report() -> void:
	print("=== PIXEL PIRATES A1 SMOKE TEST ===")
	for k in _info:
		print("%s: %s" % [k, _info[k]])

func _process(_dt: float) -> void:
	var t := "FPS %d   |   D dof:%s  G glow:%s  F fog:%s  S shadows:%s   |   Esc quit\n" % [
		Engine.get_frames_per_second(), _on(_cam_attr.dof_blur_far_enabled), _on(_env.glow_enabled),
		_on(_env.volumetric_fog_enabled), _on(_sun.shadow_enabled)]
	var r := _info
	for k in ["engine", "gpu", "graphics api", "renderer", "double-precision build"]:
		t += "%s: %s\n" % [k, r[k]]
	_label.text = t

func _on(b: bool) -> String:
	return "on" if b else "off"

func _unhandled_key_input(event: InputEvent) -> void:
	var e := event as InputEventKey
	if e == null or not e.pressed or e.echo:
		return
	match e.keycode:
		KEY_D:
			var v := not _cam_attr.dof_blur_far_enabled
			_cam_attr.dof_blur_far_enabled = v
			_cam_attr.dof_blur_near_enabled = v
		KEY_G: _env.glow_enabled = not _env.glow_enabled
		KEY_F: _env.volumetric_fog_enabled = not _env.volumetric_fog_enabled
		KEY_S: _sun.shadow_enabled = not _sun.shadow_enabled
		KEY_ESCAPE: get_tree().quit()
