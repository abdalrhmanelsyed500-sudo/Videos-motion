extends RefCounted
## VP-0 helpers (static): texture loading with the project's raw-PNG fallback, sprite and shadow placement, mesh builders.
## Everything here is prototype code: it does not touch the game scenes.

const ART := "res://art/vp0/"
const SHADER_DIR := "res://prototypes/vp0/shaders/"

static var _tex: Dictionary = {}
static var _man: Dictionary = {}
static var _shaders: Dictionary = {}


static func tex(path: String) -> Texture2D:
	if _tex.has(path):
		return _tex[path] as Texture2D
	var t: Texture2D = null
	if ResourceLoader.exists(path):
		t = load(path) as Texture2D
	if t == null and FileAccess.file_exists(path):
		var img := Image.load_from_file(path)
		if img != null and not img.is_empty():
			t = ImageTexture.create_from_image(img)
	if t == null:
		push_warning("VP0: cannot load %s" % path)
	_tex[path] = t
	return t


static func shader(name: String) -> Shader:
	if not _shaders.has(name):
		_shaders[name] = load(SHADER_DIR + name + ".gdshader")
	return _shaders[name] as Shader


static func manifest(group: String) -> Dictionary:
	if _man.has(group):
		return _man[group] as Dictionary
	var p := ART + group + "/" + group + "_manifest.json"
	var d: Dictionary = {}
	if FileAccess.file_exists(p):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(p))
		if parsed is Dictionary:
			d = parsed as Dictionary
	_man[group] = d
	return d


static func frame_for(nf: int, phi_deg: float) -> int:
	## Facing frames are the model rotated COUNTER-CLOCKWISE (seen from above, north up) by k * 360/nf degrees.
	## phi_deg = the counter-clockwise angle (east -> north) of the model's +x axis in the world.
	var step := 360.0 / float(nf)
	return int(roundf(fposmod(phi_deg, 360.0) / step)) % nf


## Adds one sprite (and optionally its flattened shadow) standing on `pos` (the pivot = centre of the footprint on the ground).
## Returns the MeshInstance3D; stage.sprite_mats / stage.shadow_mats get the materials so the look can retint them.
static func add_sprite(stage: Node, parent: Node3D, group: String, sname: String, pos: Vector3, phi_deg := 0.0, shadow := true, ppm_override := 0.0, extra_bias := 0.0) -> MeshInstance3D:
	var man: Dictionary = manifest(group)
	if not man.has(sname):
		push_warning("VP0: no sprite %s/%s" % [group, sname])
		return null
	var e: Dictionary = man[sname]
	var frames: Array = e["frames"]
	var k := frame_for(int(e["facings"]), phi_deg) if int(e["facings"]) > 1 else 0
	var f: Dictionary = frames[k]
	var t := tex(ART + group + "/" + String(f["file"]))
	var ppm: float = ppm_override if ppm_override > 0.0 else float(stage.get("ppm"))
	var w := float(f["w"])
	var h := float(f["h"])
	var pv: Array = f["pivot"]
	var piv := Vector2(roundf(float(pv[0])), roundf(float(pv[1])))
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(1, 1)
	mi.mesh = q
	mi.extra_cull_margin = 24.0
	var m := ShaderMaterial.new()
	m.shader = shader("vp0_sprite")
	m.set_shader_parameter("tex", t)
	m.set_shader_parameter("size_px", Vector2(w, h))
	m.set_shader_parameter("pivot_px", piv)
	m.set_shader_parameter("ppm", ppm)
	m.set_shader_parameter("bias", 0.45 + 1.7 * (h - piv.y) / ppm + extra_bias)
	m.set_shader_parameter("light_tint", (stage.get("look") as Dictionary)["tint_v"])
	mi.material_override = m
	mi.position = pos
	parent.add_child(mi)
	(stage.get("sprite_mats") as Array).append(m)
	if shadow:
		var sh := MeshInstance3D.new()
		var sq := QuadMesh.new()
		sq.size = Vector2(1, 1)
		sh.mesh = sq
		sh.extra_cull_margin = 24.0
		var sm := ShaderMaterial.new()
		sm.shader = shader("vp0_shadow")
		sm.set_shader_parameter("tex", t)
		sm.set_shader_parameter("size_m", Vector2(w, h) / ppm)
		sm.set_shader_parameter("pivot_m", Vector2(piv.x, h - piv.y) / ppm)
		sh.material_override = sm
		sh.position = pos
		parent.add_child(sh)
		(stage.get("shadow_mats") as Array).append(sm)
	return mi


static func add_halo(stage: Node, parent: Node3D, pos: Vector3, radius_m: float, colour: Color, weight := 1.0, seed := 0.0) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(1, 1)
	mi.mesh = q
	mi.extra_cull_margin = 24.0
	var m := ShaderMaterial.new()
	m.shader = shader("vp0_halo")
	m.set_shader_parameter("halo_colour", colour)
	m.set_shader_parameter("radius_m", radius_m)
	m.set_shader_parameter("seed", seed)
	m.set_meta("weight", weight)
	mi.material_override = m
	mi.position = pos
	parent.add_child(mi)
	(stage.get("halo_mats") as Array).append(m)
	return mi


## A flat quad for the ground / water: a PlaneMesh of the given size, centred on `centre`, with `mat`.
static func add_plane(parent: Node3D, centre: Vector3, size: Vector2, mat: Material, priority := 0) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = size
	mi.mesh = pm
	mi.position = centre
	mi.extra_cull_margin = 200.0
	mat.render_priority = priority
	mi.material_override = mat
	parent.add_child(mi)
	return mi


## ArrayMesh builder: add quads (4 points, outward normal by winding), UV in tile units.
class MeshBuilder:
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var uvs := PackedVector2Array()
	var idx := PackedInt32Array()

	func quad(a: Vector3, b: Vector3, c: Vector3, d: Vector3, ua: Vector2, ub: Vector2, uc: Vector2, ud: Vector2) -> void:
		var n := (b - a).cross(d - a).normalized()
		if n.length() < 0.001:
			n = (c - b).cross(a - b).normalized()
		var base := verts.size()
		verts.append_array(PackedVector3Array([a, b, c, d]))
		for i in 4:
			norms.append(n)
		uvs.append_array(PackedVector2Array([ua, ub, uc, ud]))
		idx.append_array(PackedInt32Array([base, base + 1, base + 2, base, base + 2, base + 3]))

	func build() -> ArrayMesh:
		var arr: Array = []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = verts
		arr[Mesh.ARRAY_NORMAL] = norms
		arr[Mesh.ARRAY_TEX_UV] = uvs
		arr[Mesh.ARRAY_INDEX] = idx
		var mesh := ArrayMesh.new()
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr)
		return mesh
