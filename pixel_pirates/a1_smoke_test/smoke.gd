extends Node3D
## Pixel Pirates - Module A1 (revision R1): GPU probe + HD-2D smoke test, COMPATIBILITY renderer only.
##
## Purpose
##  1. PROBE: report which renderer/driver/GPU Godot really uses on this PC and how fast it runs.
##  2. PROVE the "authored HD-2D" look works without Forward+ features:
##     pixel sprites in a 3D diorama, pitched camera, tilt-shift via our own screen shader
##     (the Compatibility renderer has no built-in depth of field), bloom, depth fog,
##     warm light with shadows, authored light shafts.
##  3. Show the QUALITY LADDER:  1 = Dev-Lite (for weak PCs), 2 = Standard.
##
## Keys:  1 Dev-Lite   2 Standard   T tilt-shift   G glow   F fog   S shadows   H shafts
##        R write report file   Esc quit

const PIXEL_SIZE := 0.07              # world units per sprite pixel (16x24 sprite = 1.12 x 1.68 units)
const DEV_LITE_SIZE := Vector2i(683, 438)   # exactly half of a 1366x876 screen: 1 art pixel = 2 screen pixels

const TILT_SHADER := """
shader_type canvas_item;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear, repeat_disable;
uniform float focus_y = 0.58;       // screen y (0 top .. 1 bottom) of the sharp band centre
uniform float band = 0.16;          // half height of the sharp band
uniform float falloff = 0.30;       // distance over which blur ramps up to its maximum
uniform float max_blur_px = 5.0;    // blur radius at the screen edges, in screen pixels
uniform float vignette = 0.35;
uniform float strength = 1.0;       // 0 = off
void fragment() {
	vec2 px = SCREEN_PIXEL_SIZE;
	float d = clamp((abs(SCREEN_UV.y - focus_y) - band) / falloff, 0.0, 1.0);
	float r = d * d * max_blur_px * strength;
	vec3 col = texture(screen_tex, SCREEN_UV).rgb;
	if (r > 0.5) {
		vec3 acc = col;
		float wsum = 1.0;
		for (int i = 0; i < 12; i++) {
			float a = float(i) * 2.399963;                    // golden angle
			float rad = sqrt((float(i) + 0.5) / 12.0) * r;
			vec2 o = vec2(cos(a), sin(a)) * rad * px;
			acc += texture(screen_tex, SCREEN_UV + o).rgb;
			wsum += 1.0;
		}
		col = acc / wsum;
	}
	float vig = 1.0 - vignette * smoothstep(0.35, 0.85, distance(SCREEN_UV, vec2(0.5)));
	COLOR = vec4(col * vig, 1.0);
}
"""

var _env: Environment
var _sun: DirectionalLight3D
var _label: Label
var _tilt_rect: ColorRect
var _tilt_mat: ShaderMaterial
var _shafts: Array[MeshInstance3D] = []
var _info: Dictionary = {}
var _quality: String = "Standard"
var _t: float = 0.0
var _fps_acc: float = 0.0
var _fps_n: int = 0
var _fps_min: float = 9999.0
var _fps_avg: float = 0.0

func _ready() -> void:
	_info = _report()
	_build_world()
	_build_hud()
	_apply_quality("Standard")
	print("=== PIXEL PIRATES A1 PROBE ===")
	for k in _info:
		print("%s: %s" % [k, _info[k]])

# ------------------------------------------------------------------ world
func _build_world() -> void:
	var cam := Camera3D.new()
	cam.fov = 22.0                                  # narrow FOV keeps pixel size almost constant
	cam.position = Vector3(0, 9, 11)                # pitch = atan(9/11) ~ 39 degrees
	add_child(cam)
	cam.look_at(Vector3.ZERO, Vector3.UP)

	_env = Environment.new()
	_env.background_mode = Environment.BG_COLOR
	_env.background_color = Color("14222b")
	_env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	_env.ambient_light_color = Color("6a7d8c")
	_env.ambient_light_energy = 0.8
	_env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	_env.glow_enabled = true                        # supported in Compatibility
	_env.glow_hdr_threshold = 0.65                  # Compatibility is LDR (RGBA8): lower threshold so bloom shows
	_env.glow_intensity = 0.9
	_env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SCREEN
	_env.fog_enabled = true                         # depth fog (volumetric fog does NOT exist in Compatibility)
	_env.fog_light_color = Color("c9a46a")
	_env.fog_density = 0.012
	_env.adjustment_enabled = true
	_env.adjustment_saturation = 1.15
	_env.adjustment_contrast = 1.08
	var we := WorldEnvironment.new()
	we.environment = _env
	add_child(we)

	_sun = DirectionalLight3D.new()
	_sun.light_color = Color("ffd9a0")
	_sun.light_energy = 1.5
	_sun.shadow_enabled = true
	_sun.rotation_degrees = Vector3(-48, 32, 0)
	add_child(_sun)

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
		s.offset = Vector2(0, 12)                   # feet on y=0 (24 px tall, centered)
		s.position = Vector3(-4.0 + i * 1.0, 0.0, 6.0 - i * 1.6)
		add_child(s)

	_build_shafts()

	# Full-screen tilt-shift + vignette: a ColorRect that reads the already rendered 3D picture.
	var layer := CanvasLayer.new()
	layer.layer = 1
	add_child(layer)
	var shader := Shader.new()
	shader.code = TILT_SHADER
	_tilt_mat = ShaderMaterial.new()
	_tilt_mat.shader = shader
	_tilt_rect = ColorRect.new()
	_tilt_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	_tilt_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_tilt_rect.material = _tilt_mat
	layer.add_child(_tilt_rect)

# Authored light shafts: additive gradient quads (replaces volumetric fog, which Compatibility lacks).
func _build_shafts() -> void:
	var grad := Gradient.new()
	grad.colors = PackedColorArray([Color(1.0, 0.86, 0.55, 0.42), Color(1.0, 0.86, 0.55, 0.0)])
	grad.offsets = PackedFloat32Array([0.0, 1.0])
	var gt := GradientTexture2D.new()
	gt.gradient = grad
	gt.fill = GradientTexture2D.FILL_LINEAR
	gt.fill_from = Vector2(0.5, 0.0)
	gt.fill_to = Vector2(0.5, 1.0)
	gt.width = 64
	gt.height = 128
	for i in range(3):
		var m := MeshInstance3D.new()
		var q := QuadMesh.new()
		q.size = Vector2(1.8 - i * 0.3, 9.0)
		m.mesh = q
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		mat.albedo_texture = gt
		m.material_override = mat
		m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		m.position = Vector3(-3.0 + i * 3.2, 4.5, -4.0 - i)
		m.rotation_degrees = Vector3(0, 0, -25)
		add_child(m)
		_shafts.append(m)

func _make_sprite_texture() -> ImageTexture:
	var img := Image.create_empty(16, 24, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	img.fill_rect(Rect2i(4, 0, 8, 3), Color("2b1d2e"))
	img.fill_rect(Rect2i(2, 3, 12, 2), Color("2b1d2e"))
	img.fill_rect(Rect2i(5, 5, 6, 5), Color("e0b48a"))
	img.set_pixel(6, 7, Color("1a1020"))
	img.set_pixel(9, 7, Color("1a1020"))
	img.fill_rect(Rect2i(3, 10, 10, 8), Color("a8322e"))
	img.fill_rect(Rect2i(1, 11, 2, 6), Color("a8322e"))
	img.fill_rect(Rect2i(13, 11, 2, 6), Color("a8322e"))
	img.fill_rect(Rect2i(7, 10, 2, 8), Color("e8d9b5"))
	img.fill_rect(Rect2i(4, 18, 3, 5), Color("2f3a4a"))
	img.fill_rect(Rect2i(9, 18, 3, 5), Color("2f3a4a"))
	img.fill_rect(Rect2i(3, 23, 4, 1), Color("1a1020"))
	img.fill_rect(Rect2i(9, 23, 4, 1), Color("1a1020"))
	return ImageTexture.create_from_image(img)

func _make_ground_texture() -> ImageTexture:
	var img := Image.create_empty(16, 16, false, Image.FORMAT_RGBA8)
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var cols: Array[Color] = [Color("6f7d3c"), Color("7d8a45"), Color("5f6c34"), Color("8a7a48")]
	for y in 16:
		for x in 16:
			img.set_pixel(x, y, cols[rng.randi_range(0, cols.size() - 1)])
	return ImageTexture.create_from_image(img)

# ------------------------------------------------------------------ quality ladder
func _apply_quality(q: String) -> void:
	_quality = q
	var win := get_window()
	if q == "Dev-Lite":
		# Render at half resolution (683x438) and upscale with nearest filtering: pixel art stays crisp,
		# GPU work drops by 4x. Shadows and bloom off, blur kept but cheaper.
		win.content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT
		win.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_KEEP
		win.content_scale_size = DEV_LITE_SIZE
		_sun.shadow_enabled = false
		_env.glow_enabled = false
		_tilt_mat.set_shader_parameter("max_blur_px", 2.0)
	else:
		win.content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
		_sun.shadow_enabled = true
		_env.glow_enabled = true
		_tilt_mat.set_shader_parameter("max_blur_px", 5.0)
	_fps_acc = 0.0
	_fps_n = 0
	_fps_min = 9999.0

# ------------------------------------------------------------------ HUD / report
func _build_hud() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 2
	add_child(layer)
	_label = Label.new()
	_label.position = Vector2(10, 6)
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
		"rendering method": RenderingServer.get_current_rendering_method(),
		"rendering driver": RenderingServer.get_current_rendering_driver_name(),
		"cpu": OS.get_processor_name(),
		"cpu threads": OS.get_processor_count(),
		"ram MB": floori(float(mem.get("physical", -1)) / 1048576.0),
		"Vector3.x for 100000.001": Vector3(100000.001, 0, 0).x,
	}

func _process(dt: float) -> void:
	_t += dt
	for i in range(_shafts.size()):
		_shafts[i].rotation_degrees.z = -25.0 + sin(_t * 0.4 + i) * 3.0
		var mat := _shafts[i].material_override as StandardMaterial3D
		mat.albedo_color.a = 0.7 + 0.3 * sin(_t * 0.7 + i * 1.7)
	if _t > 2.0 and dt > 0.0:                      # ignore start-up hitches
		var f := 1.0 / dt
		_fps_acc += f
		_fps_n += 1
		_fps_min = minf(_fps_min, f)
		_fps_avg = _fps_acc / float(_fps_n)
	var txt := "Quality: %s   FPS now %d   avg %d   min %d   engine mem %d MB\n" % [
		_quality, Engine.get_frames_per_second(), int(_fps_avg), int(_fps_min),
		OS.get_static_memory_usage() / 1048576]
	txt += "1 Dev-Lite  2 Standard  |  T tilt:%s  G glow:%s  F fog:%s  S shadows:%s  H shafts:%s  |  R report  Esc quit\n" % [
		_on(_tilt_mat.get_shader_parameter("strength") > 0.0), _on(_env.glow_enabled), _on(_env.fog_enabled),
		_on(_sun.shadow_enabled), _on(_shafts[0].visible)]
	for k in ["gpu", "graphics api", "rendering method", "rendering driver"]:
		txt += "%s: %s\n" % [k, _info[k]]
	_label.text = txt

func _on(b: bool) -> String:
	return "on" if b else "off"

func _write_report() -> void:
	var lines: PackedStringArray = []
	for k in _info:
		lines.append("%s: %s" % [k, _info[k]])
	lines.append("quality: %s" % _quality)
	lines.append("window: %s" % str(get_window().size))
	lines.append("fps avg: %d  min: %d  (measured after 2 s warm-up)" % [int(_fps_avg), int(_fps_min)])
	var f := FileAccess.open("user://probe_result.txt", FileAccess.WRITE)
	if f == null:
		push_error("could not write report")
		return
	f.store_string("\n".join(lines) + "\n")
	f.close()
	print("REPORT WRITTEN TO: ", ProjectSettings.globalize_path("user://probe_result.txt"))
	print("\n".join(lines))

func _unhandled_key_input(event: InputEvent) -> void:
	var e := event as InputEventKey
	if e == null or not e.pressed or e.echo:
		return
	match e.keycode:
		KEY_1: _apply_quality("Dev-Lite")
		KEY_2: _apply_quality("Standard")
		KEY_T: _tilt_mat.set_shader_parameter("strength", 0.0 if _tilt_mat.get_shader_parameter("strength") > 0.0 else 1.0)
		KEY_G: _env.glow_enabled = not _env.glow_enabled
		KEY_F: _env.fog_enabled = not _env.fog_enabled
		KEY_S: _sun.shadow_enabled = not _sun.shadow_enabled
		KEY_H:
			for m in _shafts:
				m.visible = not m.visible
		KEY_R: _write_report()
		KEY_ESCAPE: get_tree().quit()
