extends Control
## VP-0 stage: the shared base of the in-engine visual prototypes (NOT part of the game).
## It builds the render pipeline the Art Bible proposes:
##   SubViewport 640x360 (one art pixel = one viewport pixel)  ->  TextureRect (nearest, integer scale)  ->  grade shader (tilt-shift, bloom, vignette, grade)
## with an ORTHOGONAL camera (exact 1:1 sprite pixels, free depth bias, no shimmer) and the look presets day / golden / dusk / night.
## Scene scripts extend this file and override _build().   Keys: 1-4 look, G grade on/off, L lite grade, [ ] camera x, ; ' camera z, Esc quit.
## Command-line (after --):  look=golden  grade=0|1|2  cam=x,z  pitch=37

const U := preload("res://prototypes/vp0/vp0_util.gd")

const ART_W := 640
const ART_H := 360

const LOOKS := {
	"day": {
		"tint": Color(1.0, 0.99, 0.95), "sun": Vector3(0.55, -0.75, -0.40), "shadow": Color(0.16, 0.09, 0.20, 0.38),
		"fog": Color(0.62, 0.78, 0.80), "fog_amt": 0.25, "halo": 0.0,
		"grade_mul": Color(1.0, 1.0, 1.0), "sat": 1.12, "contrast": 1.06, "bloom": 0.25, "vignette": 0.55,
	},
	"golden": {
		"tint": Color(1.0, 0.85, 0.68), "sun": Vector3(0.85, -0.42, -0.40), "shadow": Color(0.24, 0.08, 0.26, 0.50),
		"fog": Color(0.92, 0.64, 0.50), "fog_amt": 0.35, "halo": 0.35,
		"grade_mul": Color(1.03, 0.99, 0.95), "sat": 1.15, "contrast": 1.08, "bloom": 0.45, "vignette": 0.68,
	},
	"dusk": {
		"tint": Color(0.72, 0.64, 0.88), "sun": Vector3(0.9, -0.28, -0.30), "shadow": Color(0.12, 0.07, 0.26, 0.46),
		"fog": Color(0.52, 0.44, 0.64), "fog_amt": 0.40, "halo": 0.80,
		"grade_mul": Color(0.97, 0.93, 1.06), "sat": 1.18, "contrast": 1.08, "bloom": 0.55, "vignette": 0.74,
	},
	"night": {
		"tint": Color(0.38, 0.46, 0.78), "sun": Vector3(-0.35, -0.65, -0.45), "shadow": Color(0.04, 0.05, 0.16, 0.34),
		"fog": Color(0.12, 0.17, 0.32), "fog_amt": 0.45, "halo": 1.0,
		"grade_mul": Color(0.92, 1.0, 1.14), "sat": 1.10, "contrast": 1.10, "bloom": 0.70, "vignette": 0.80,
	},
}
const LOOK_ORDER := ["day", "golden", "dusk", "night"]

const OCEAN_RAMP := ["#123a4f", "#1d5f73", "#238a8c", "#3d8c92", "#5cb8a5", "#9be0c0", "#dffbe0"]
const FOAM_RAMP := ["#7fc4bc", "#bfe8d8", "#e6faec", "#fffff0"]

var ppm := 24.0
var pitch_deg := 37.0
var cam_dist := 80.0
var look_name := "day"
var look: Dictionary = {}
var grade_level := 2
var sprite_mats: Array = []
var shadow_mats: Array = []
var halo_mats: Array = []
var cel_mats: Array = []
var terrain_mats: Array = []
var ocean_mats: Array = []
var line_mats: Array = []
var clip_mats: Array = []
var glass_mats: Array = []
var viewport: SubViewport
var world: Node3D
var cam: Camera3D
var grade_mat: ShaderMaterial
var out: TextureRect
var args := {}
var cam_target := Vector3.ZERO
var time_s := 0.0
var _hud: Label
var _noise: Texture2D


func _ready() -> void:
	_parse_args()
	var win := get_window()
	if String(args.get("int", "0")) == "1":
		win.set("content_scale_stretch", 1)      # integer scaling: one art pixel = a whole number of screen pixels
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	size = Vector2(1280, 720)
	_setup_viewport()
	_setup_output()
	_hud = Label.new()
	_hud.position = Vector2(10, 6)
	_hud.add_theme_color_override("font_color", Color(1, 1, 0.9, 0.85))
	_hud.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.8))
	add_child(_hud)
	_hud.visible = String(args.get("hud", "0")) == "1"
	_noise = U.tex(U.ART + "ground/noise_128.png")
	set_look(String(args.get("look", look_name)))
	_build()
	set_look(String(args.get("look", look_name)))
	grade_level = int(args.get("grade", grade_level))
	_apply_grade()
	_update_camera()
	if String(args.get("dbg", "0")) == "1":
		print("VP0DBG2 win=", get_window().size, " vis=", get_viewport().get_visible_rect().size, " self=", size, " out=", out.size, " tex=", out.texture.get_size(), " cs=", get_window().content_scale_size, " mode=", get_window().content_scale_mode)
		print("VP0DBG proj=", cam.projection, " size=", cam.size, " xf=", cam.global_transform, " vp=", viewport.size, " tgt=", cam_target)


func _build() -> void:
	pass


func _parse_args() -> void:
	for a in OS.get_cmdline_args() + OS.get_cmdline_user_args():
		var s := String(a)
		if "=" in s and not s.begins_with("--"):
			var kv := s.split("=", true, 1)
			args[kv[0]] = kv[1]
	if args.has("pitch"):
		pitch_deg = float(args["pitch"])


func _setup_viewport() -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(ART_W, ART_H)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.msaa_3d = Viewport.MSAA_DISABLED
	viewport.own_world_3d = true
	add_child(viewport)
	world = Node3D.new()
	viewport.add_child(world)
	cam = Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.near = 30.0
	cam.far = 150.0
	world.add_child(cam)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.07, 0.2, 0.27)
	var we := WorldEnvironment.new()
	we.environment = env
	world.add_child(we)


func _setup_output() -> void:
	out = TextureRect.new()
	out.texture = viewport.get_texture()
	out.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	out.stretch_mode = TextureRect.STRETCH_SCALE
	out.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	grade_mat = ShaderMaterial.new()
	grade_mat.shader = U.shader("vp0_grade")
	grade_mat.set_shader_parameter("src_near", viewport.get_texture())
	grade_mat.set_shader_parameter("src_lin", viewport.get_texture())
	out.material = grade_mat
	add_child(out)
	out.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	out.size = Vector2(1280, 720)


func set_cam(target: Vector3) -> void:
	cam_target = target
	_update_camera()


func _update_camera() -> void:
	if cam == null:
		return
	cam.size = float(ART_H) / ppm
	var p := deg_to_rad(pitch_deg)
	var dir := Vector3(0.0, sin(p), cos(p))
	var pos := cam_target + dir * cam_dist
	cam.global_transform = Transform3D(Basis.looking_at(-dir, Vector3.UP), pos)
	# snap the camera to the art-pixel grid in its own plane: world features move in whole pixels
	var inv := cam.global_transform.affine_inverse()
	var c := inv * cam_target
	var snapped_c := Vector3(roundf(c.x * ppm) / ppm, roundf(c.y * ppm) / ppm, c.z)
	cam.global_position += cam.global_transform.basis * (c - snapped_c)


func set_look(name: String) -> void:
	if not LOOKS.has(name):
		name = "day"
	look_name = name
	look = (LOOKS[name] as Dictionary).duplicate()
	var t: Color = look["tint"]
	look["tint_v"] = Vector3(t.r, t.g, t.b)
	var sun: Vector3 = look["sun"]
	var tv := Vector3(t.r, t.g, t.b)
	for m in sprite_mats:
		(m as ShaderMaterial).set_shader_parameter("light_tint", tv)
		(m as ShaderMaterial).set_shader_parameter("glow", clampf(float(look["halo"]) * 2.0, 0.0, 1.0))
	for m in shadow_mats:
		(m as ShaderMaterial).set_shader_parameter("sun_dir", sun)
		(m as ShaderMaterial).set_shader_parameter("shadow_colour", look["shadow"])
	for m in cel_mats:
		(m as ShaderMaterial).set_shader_parameter("sun_dir", sun)
		(m as ShaderMaterial).set_shader_parameter("light_tint", tv)
	for m in terrain_mats:
		(m as ShaderMaterial).set_shader_parameter("light_tint", tv)
	var fog: Color = look["fog"]
	for m in ocean_mats:
		(m as ShaderMaterial).set_shader_parameter("light_tint", Vector3(1, 1, 1).lerp(tv, 0.6))
		(m as ShaderMaterial).set_shader_parameter("fog_colour", Vector3(fog.r, fog.g, fog.b))
		(m as ShaderMaterial).set_shader_parameter("fog_amount", float(look["fog_amt"]))
	for m in halo_mats:
		(m as ShaderMaterial).set_shader_parameter("intensity", float(look["halo"]) * float((m as ShaderMaterial).get_meta("weight", 1.0)))
	for m in line_mats:
		var sm := m as StandardMaterial3D
		sm.albedo_color = (sm.get_meta("base") as Color) * t
	var hw := float(look["halo"])
	for m in glass_mats:
		(m as StandardMaterial3D).albedo_color = Color(0.45, 0.6, 0.62).lerp(Color(1.0, 0.72, 0.30), clampf(hw * 1.2, 0.0, 1.0))
	_apply_grade()
	_on_look()


func _on_look() -> void:
	pass


func _apply_grade() -> void:
	if grade_mat == null or look.is_empty():
		return
	var g := grade_mat
	g.set_shader_parameter("grade_mul", Vector3((look["grade_mul"] as Color).r, (look["grade_mul"] as Color).g, (look["grade_mul"] as Color).b))
	g.set_shader_parameter("saturation", float(look["sat"]) if grade_level > 0 else 1.0)
	g.set_shader_parameter("contrast", float(look["contrast"]) if grade_level > 0 else 1.0)
	g.set_shader_parameter("vignette", float(look["vignette"]) if grade_level > 0 else 0.0)
	g.set_shader_parameter("bloom", float(look["bloom"]) if grade_level >= 2 else 0.0)
	g.set_shader_parameter("taps", 8 if grade_level >= 2 else 0)
	g.set_shader_parameter("shadow_lift", 0.035 if grade_level > 0 else 0.0)


## ---------- builders shared by the scenes ----------

func make_ocean(depth_png: String, rect: Array, range_m: Array, tile_m: float, bed_atlas: Texture2D) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = U.shader("vp0_ocean")
	m.set_shader_parameter("depth_tex", U.tex(depth_png))
	m.set_shader_parameter("noise_tex", _noise)
	m.set_shader_parameter("bed_atlas", bed_atlas)
	m.set_shader_parameter("depth_rect", Vector4(rect[0], rect[1], rect[2], rect[3]))
	m.set_shader_parameter("depth_range", Vector2(range_m[0], range_m[1]))
	m.set_shader_parameter("ppm", ppm)
	m.set_shader_parameter("tile_m", tile_m)
	var rp := PackedVector3Array()
	for h in OCEAN_RAMP:
		var c := Color(h)
		rp.append(Vector3(c.r, c.g, c.b))
	m.set_shader_parameter("ramp", rp)
	var fp := PackedVector3Array()
	for h in FOAM_RAMP:
		var c2 := Color(h)
		fp.append(Vector3(c2.r, c2.g, c2.b))
	m.set_shader_parameter("foam", fp)
	ocean_mats.append(m)
	return m


func make_terrain(cells_png: String, origin: Vector2, count: Vector2i, tile_m: float) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = U.shader("vp0_terrain")
	m.set_shader_parameter("cells", U.tex(cells_png))
	m.set_shader_parameter("atlas", U.tex(U.ART + "ground/ground_atlas.png"))
	m.set_shader_parameter("noise_tex", _noise)
	m.set_shader_parameter("origin", origin)
	m.set_shader_parameter("cell_count", count)
	m.set_shader_parameter("ppm", ppm)
	m.set_shader_parameter("tile_m", tile_m)
	terrain_mats.append(m)
	return m


func atlas_tile(row: int, variant := 0) -> Texture2D:
	var at := U.tex(U.ART + "ground/ground_atlas.png")
	var img := at.get_image()
	var r := img.get_region(Rect2i(variant * 48, row * 48, 48, 48))
	return ImageTexture.create_from_image(r)


func make_cel(tex: Texture2D, tint := Color(1, 1, 1), back_glow := 0.0) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = U.shader("vp0_cel")
	m.set_shader_parameter("albedo_tex", tex)
	m.set_shader_parameter("tint", tint)
	m.set_shader_parameter("back_glow", back_glow)
	cel_mats.append(m)
	return m


func make_lines(points: PackedVector3Array, colour: Color) -> MeshInstance3D:
	var im := ImmediateMesh.new()
	im.surface_begin(Mesh.PRIMITIVE_LINES)
	for p in points:
		im.surface_add_vertex(p)
	im.surface_end()
	var mi := MeshInstance3D.new()
	mi.mesh = im
	mi.extra_cull_margin = 40.0
	var sm := StandardMaterial3D.new()
	sm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	sm.albedo_color = colour
	sm.set_meta("base", colour)
	mi.material_override = sm
	line_mats.append(sm)
	return mi


func _process(delta: float) -> void:
	time_s += delta
	for m in ocean_mats:
		(m as ShaderMaterial).set_shader_parameter("time_s", time_s)
	for m in halo_mats:
		(m as ShaderMaterial).set_shader_parameter("time_s", time_s)
	_tick(delta)
	if _hud != null and _hud.visible:
		_hud.text = "VP-0  look %s  grade %d  %d fps" % [look_name, grade_level, Engine.get_frames_per_second()]


func _tick(_delta: float) -> void:
	pass


func _unhandled_input(ev: InputEvent) -> void:
	var k := ev as InputEventKey
	if k == null or not k.pressed or k.echo:
		return
	match k.keycode:
		KEY_1: set_look("day")
		KEY_2: set_look("golden")
		KEY_3: set_look("dusk")
		KEY_4: set_look("night")
		KEY_G:
			grade_level = (grade_level + 1) % 3
			_apply_grade()
		KEY_H:
			_hud.visible = not _hud.visible
		KEY_BRACKETLEFT: set_cam(cam_target + Vector3(-1, 0, 0))
		KEY_BRACKETRIGHT: set_cam(cam_target + Vector3(1, 0, 0))
		KEY_SEMICOLON: set_cam(cam_target + Vector3(0, 0, -1))
		KEY_APOSTROPHE: set_cam(cam_target + Vector3(0, 0, 1))
		KEY_ESCAPE: get_tree().quit()
