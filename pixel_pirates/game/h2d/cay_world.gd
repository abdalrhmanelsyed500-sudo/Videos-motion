extends RefCounted
## H2D-1.2 Anvil Cay as a world object: the baked maps (height, biome, palette), the ground patch that follows the
## camera,
## the pier, the houses and props, the streamed vegetation chunks and the pirate. It also answers every question
## the game asks
## of the land: height, class, slope, and "may I stand here".
## Scale: 1 scene unit = 1 m = 1 geographic metre (docs/H2D1_2_SCALE_AND_LAND.md). Data: tools/h2d/bake_cay.py.
## NOT YET RUN IN GODOT.
const Scatter := preload("res://h2d/cay_scatter.gd")
const DataLoader := preload("res://core/data_loader.gd")
const ART_DIR := "res://h2d/art/"
const PX_PER_M := 3.6
const PATCH_M := 400.0
const HERO_M_PER_PX_FALLBACK := 0.0694
const CLIFF_CLASS := 6
const SAND_CLASS := 1

var meta: Dictionary = {}
var n := 0
var cell := 2.0
var ox := 0.0
var oz := 0.0
var size_m := 0.0
var top_m := 100.0
var blockers: Array = []   # [x0, z0, x1, z1] in metres
var walk_min_h := 0.45
var walk_max_slope := 0.55
var chunk_budget := 1      # chunks built per frame while streaming
var _hd := PackedByteArray()
var _bd := PackedByteArray()
var _lut := PackedFloat32Array()
var _params: Dictionary = {}
var _pier: Dictionary = {}
var _root: Node3D
var _terrain: MeshInstance3D
var _terrain_mat: ShaderMaterial
var _pier_nodes: Array = []
var _structs: MultiMeshInstance3D
var _props: MultiMeshInstance3D
var _glow_mats: Array = []
var _veg_mat: ShaderMaterial
var _hero: MultiMeshInstance3D
var _hero_mat: ShaderMaterial
var _blob: MeshInstance3D
var _chunks: Dictionary = {}
var _chunk_m := 200.0
var _active := false


## `tex_fn(file) -> Texture2D` and `mat_fn(shader_file) -> ShaderMaterial` are the view's loaders (the normal
## ResourceLoader path). `parent` is the root of the 3D world: the view's SubViewport (a Node, not a Node3D); the
## island's own Node3D "AnvilCay" is added under it.
func build(parent: Node, ocean_mat: ShaderMaterial, tex_fn: Callable, mat_fn: Callable) -> void:
	meta = DataLoader.load_dict(ART_DIR + "anvil_cay.json")
	var g: Dictionary = meta["grid"]
	n = int(g["cells"])
	cell = float(g["cell_m"])
	ox = float(g["origin_x"])
	oz = float(g["origin_z"])
	size_m = float(g["size_m"])
	top_m = float((meta["height_enc"] as Dictionary)["top"])
	_root = Node3D.new()
	_root.name = "AnvilCay"
	parent.add_child(_root)
	var files: Dictionary = meta["files"]
	var h_tex := tex_fn.call(str(files["height"])) as Texture2D
	var b_tex := tex_fn.call(str(files["biome"])) as Texture2D
	var p_tex := tex_fn.call(str(files["palette"])) as Texture2D
	if h_tex != null and b_tex != null:
		_hd = _bytes_of(h_tex)
		_bd = _bytes_of(b_tex)
	_lut = Scatter.build_lut(top_m)
	_pier = (meta["harbor_layout"] as Dictionary)["pier"]
	blockers = meta["blockers"]
	var sc: Dictionary = meta["scatter"]
	_chunk_m = float(sc["chunk_m"])
	var rules: Array = []
	rules.resize(16)
	for i in 16:
		rules[i] = []
	for k in (sc["classes"] as Dictionary).keys():
		rules[int(k)] = (sc["classes"] as Dictionary)[k]
	var trunk: Dictionary = {}
	for k in (sc["trunk_r"] as Dictionary).keys():
		trunk[int(k)] = float((sc["trunk_r"] as Dictionary)[k])
	_params = {"bio": _bd, "hgt": _hd, "lut": _lut, "n": n, "cell": cell, "ox": ox, "oz": oz,
			"spacing": float(sc["spacing_m"]), "chunk_m": _chunk_m, "rules": rules, "fmin": float(sc["forest_density_min"]),
			"fgain": float(sc["forest_density_gain"]), "min_h": float(sc["min_height_m"]), "trunk": trunk}
	# the ocean reads the same height map (depth, shore foam, shadows on the water)
	ocean_mat.set_shader_parameter("island_data", h_tex)
	ocean_mat.set_shader_parameter("island_origin", Vector2(ox, oz))
	ocean_mat.set_shader_parameter("island_size", size_m)
	_build_terrain(h_tex, b_tex, p_tex, mat_fn)
	_build_pier(mat_fn)
	var va: Dictionary = meta["veg_atlas"]
	_veg_mat = _sprite_material(va, false, tex_fn, mat_fn)
	_structs = _build_sprites(meta["structures"] as Array, meta["struct_atlas"] as Dictionary, true, tex_fn, mat_fn)
	_props = _build_sprites(meta["props"] as Array, va, false, tex_fn, mat_fn)
	_build_hero(tex_fn, mat_fn)


func _bytes_of(tex: Texture2D) -> PackedByteArray:
	var img := tex.get_image()
	if img.get_format() != Image.FORMAT_RGBA8:
		img.convert(Image.FORMAT_RGBA8)
	return img.get_data()


func _build_terrain(h_tex: Texture2D, b_tex: Texture2D, p_tex: Texture2D, mat_fn: Callable) -> void:
	_terrain_mat = mat_fn.call("terrain.gdshader") as ShaderMaterial
	_terrain_mat.set_shader_parameter("height_tex", h_tex)
	_terrain_mat.set_shader_parameter("biome_tex", b_tex)
	_terrain_mat.set_shader_parameter("palette_tex", p_tex)
	_terrain_mat.set_shader_parameter("grid_origin", Vector2(ox, oz))
	_terrain_mat.set_shader_parameter("grid_size", size_m)
	_terrain_mat.set_shader_parameter("cell_m", cell)
	var plane := PlaneMesh.new()
	plane.size = Vector2(PATCH_M, PATCH_M)
	var cells := int(PATCH_M / cell)
	plane.subdivide_width = cells - 1
	plane.subdivide_depth = cells - 1
	_terrain = MeshInstance3D.new()
	_terrain.mesh = plane
	_terrain.material_override = _terrain_mat
	_terrain.extra_cull_margin = 60.0
	_terrain.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_root.add_child(_terrain)


## The deck and the T-head: boxes 1 m above the water, with planks painted by pier.gdshader.
func _build_pier(mat_fn: Callable) -> void:
	var mat := mat_fn.call("pier.gdshader") as ShaderMaterial
	var x0 := float(_pier["x0"])
	var x1 := float(_pier["x1"])
	var z0 := float(_pier["z0"])
	var z1 := float(_pier["z1"])
	var head: Dictionary = _pier["head"]
	var hx0 := float(head["x0"])
	var hz0 := float(head["z0"])
	var top := float(_pier["height_m"])
	var boxes := [[x0, z0, x1, z1], [hx0, hz0, x0, z1]]
	for b in boxes:
		var bm := BoxMesh.new()
		bm.size = Vector3(float(b[2]) - float(b[0]), top + 0.6, float(b[3]) - float(b[1]))
		var mi := MeshInstance3D.new()
		mi.mesh = bm
		mi.material_override = mat
		mi.position = Vector3((float(b[0]) + float(b[2])) * 0.5, top - (top + 0.6) * 0.5, (float(b[1]) + float(b[3])) * 0.5)
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_root.add_child(mi)
		_pier_nodes.append(mi)
	_glow_mats.append(mat)


func _sprite_material(atlas: Dictionary, glow: bool, tex_fn: Callable, mat_fn: Callable) -> ShaderMaterial:
	var m := mat_fn.call("trees.gdshader") as ShaderMaterial
	m.set_shader_parameter("atlas", tex_fn.call(str(atlas["file"])))
	var cp: Array = atlas["cell_px"]
	var piv: Array = atlas["pivot_px"]
	m.set_shader_parameter("cell_px", Vector2(float(cp[0]), float(cp[1])))
	m.set_shader_parameter("pivot_px", Vector2(float(piv[0]), float(piv[1])))
	m.set_shader_parameter("atlas_grid", Vector2(float(atlas["cols"]), float(atlas["rows"])))
	m.set_shader_parameter("m_per_px", 1.0 / PX_PER_M)
	m.set_shader_parameter("glow_on", 1.0 if glow else 0.0)
	_glow_mats.append(m)
	return m


## One MultiMesh of camera-facing sprites for a fixed list (houses, props): ONE draw call.
func _build_sprites(list: Array, atlas: Dictionary, glow: bool, tex_fn: Callable,
		mat_fn: Callable) -> MultiMeshInstance3D:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = QuadMesh.new()
	mm.instance_count = list.size()
	for i in list.size():
		var t: Dictionary = list[i]
		mm.set_instance_transform(i, Transform3D(Basis.IDENTITY, Vector3(float(t["x_m"]), float(t["y_m"]), float(t["z_m"]))))
		var bob := 0.12 if str(t.get("name", "")).begins_with("buoy") else 0.0
		mm.set_instance_custom_data(i, Color(float(t["type"]), float(t["scale"]), bob, 0.0))
	mm.custom_aabb = AABB(Vector3(ox, -20.0, oz), Vector3(size_m, 200.0, size_m))
	var inst := MultiMeshInstance3D.new()
	inst.multimesh = mm
	inst.material_override = _sprite_material(atlas, glow, tex_fn, mat_fn)
	inst.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_root.add_child(inst)
	return inst


func _build_hero(tex_fn: Callable, mat_fn: Callable) -> void:
	var ha: Dictionary = meta["hero_atlas"]
	_hero_mat = _sprite_material(ha, false, tex_fn, mat_fn)
	_hero_mat.set_shader_parameter("depth_bias", 0.8)
	_hero_mat.set_shader_parameter("sprite_light", 0.7)
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = QuadMesh.new()
	mm.instance_count = 1
	mm.custom_aabb = AABB(Vector3(-4.0, -4.0, -4.0), Vector3(8.0, 12.0, 8.0))
	mm.set_instance_custom_data(0, Color(0.0, 1.0, 0.0, 0.0))
	_hero = MultiMeshInstance3D.new()
	_hero.multimesh = mm
	_hero.material_override = _hero_mat
	_hero.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_hero.visible = false
	_root.add_child(_hero)
	var pm := PlaneMesh.new()
	pm.size = Vector2(1.7, 0.9)
	_blob = MeshInstance3D.new()
	_blob.mesh = pm
	_blob.material_override = mat_fn.call("blob.gdshader") as ShaderMaterial
	_blob.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_blob.visible = false
	_root.add_child(_blob)


## Materials that light things at night (the harbour lamps), for sea_view_3d.gd's _set_lamps.
func lamp_materials() -> Array:
	var out: Array = [_terrain_mat]
	out.append_array(_glow_mats)
	return out


func lamps() -> Array:
	return meta["lamps"]


func harbor_layout() -> Dictionary:
	return meta["harbor_layout"]


func set_quality(shadow_steps: float, detail: float) -> void:
	_terrain_mat.set_shader_parameter("shadow_steps", shadow_steps)
	_terrain_mat.set_shader_parameter("detail", detail)


# ---- per frame -------------------------------------------------------------------------------------------------
## `focus` = ground point under the camera target; `zoom` = 1 at sea, ~4 ashore (sets the size of a ground pixel).
func update(focus: Vector2, zoom: float) -> void:
	var near := focus.x > ox - 260.0 and focus.x < ox + size_m + 260.0
	near = near and focus.y > oz - 260.0 and focus.y < oz + size_m + 260.0
	_active = near
	_terrain.visible = near
	if not near:
		_free_chunks(true)
		return
	_terrain.position = Vector3(floorf(focus.x / cell) * cell + cell * 0.5, 0.0,
			floorf(focus.y / cell) * cell + cell * 0.5)
	_terrain_mat.set_shader_parameter("texel_m", 1.0 / (PX_PER_M * zoom))
	_stream(focus, chunk_budget)


## Build every chunk around `focus` at once (entering the land view, so the first frame has its forest).
func prime(focus: Vector2) -> void:
	_stream(focus, 9)


func _stream(focus: Vector2, budget: int) -> void:
	var cc := Vector2i(int(floorf(focus.x / _chunk_m)), int(floorf(focus.y / _chunk_m)))
	var want: Array = []
	for dz in range(-1, 2):
		for dx in range(-1, 2):
			want.append(Vector2i(cc.x + dx, cc.y + dz))
	want.sort_custom(func(a: Vector2i, b: Vector2i) -> bool: return (a - cc).length_squared() < (b - cc).length_squared())
	var built := 0
	for key in want:
		if _chunks.has(key):
			continue
		if built >= budget:
			break
		_build_chunk(key as Vector2i)
		built += 1
	var drop: Array = []
	for k in _chunks.keys():
		var kk := k as Vector2i
		if absi(kk.x - cc.x) > 2 or absi(kk.y - cc.y) > 2:
			drop.append(kk)
	for k in drop:
		_drop_chunk(k as Vector2i)


func _build_chunk(key: Vector2i) -> void:
	var x0 := float(key.x) * _chunk_m
	var z0 := float(key.y) * _chunk_m
	if x0 + _chunk_m < ox or x0 > ox + size_m or z0 + _chunk_m < oz or z0 > oz + size_m or _hd.is_empty():
		_chunks[key] = {"node": null, "trunks": PackedFloat32Array(), "count": 0}
		return
	var res: Dictionary = Scatter.chunk(key.x, key.y, _params)
	var node: MultiMeshInstance3D = null
	var count: int = res["count"]
	if count > 0:
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_custom_data = true
		mm.mesh = QuadMesh.new()
		mm.instance_count = count
		mm.buffer = res["buf"]
		mm.custom_aabb = AABB(Vector3(x0 - 12.0, -10.0, z0 - 12.0), Vector3(_chunk_m + 24.0, 70.0, _chunk_m + 24.0))
		node = MultiMeshInstance3D.new()
		node.multimesh = mm
		node.material_override = _veg_mat
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_root.add_child(node)
	_chunks[key] = {"node": node, "trunks": res["trunks"], "count": count}


func _drop_chunk(key: Vector2i) -> void:
	var c: Dictionary = _chunks[key]
	if c["node"] != null:
		(c["node"] as Node).queue_free()
	_chunks.erase(key)


func _free_chunks(all: bool) -> void:
	if not all:
		return
	for k in _chunks.keys():
		_drop_chunk(k as Vector2i)


func chunk_stats() -> String:
	var inst := 0
	for k in _chunks.keys():
		inst += int((_chunks[k] as Dictionary)["count"])
	return "%d chunks, %d vegetation instances" % [_chunks.size(), inst]


# ---- the pirate ------------------------------------------------------------------------------------------------
## row: 0 south, 1 north, 2 west, 3 east; frame 0..3. `zoom` keeps one sprite pixel on one screen pixel.
func set_hero(on: bool, x: float, z: float, row: int, frame: int, zoom: float) -> void:
	_hero.visible = on
	_blob.visible = on
	if not on:
		return
	var y := height_smooth(x, z)
	if on_pier(x, z):
		y = float(_pier["height_m"])
	var mm := _hero.multimesh
	mm.set_instance_transform(0, Transform3D(Basis.IDENTITY, Vector3(x, y, z)))
	mm.set_instance_custom_data(0, Color(float(row * 4 + frame), 1.0, 0.0, 0.0))
	_hero_mat.set_shader_parameter("m_per_px", 1.0 / (PX_PER_M * zoom))
	_blob.position = Vector3(x, y + 0.06, z)


# ---- the land, as numbers --------------------------------------------------------------------------------------
func _idx(x: float, z: float) -> int:
	var ix := int(floorf((x - ox) / cell))
	var iz := int(floorf((z - oz) / cell))
	if ix < 0 or iz < 0 or ix >= n or iz >= n:
		return -1
	return (iz * n + ix) * 4


func on_pier(x: float, z: float) -> bool:
	var head: Dictionary = _pier["head"]
	if x >= float(_pier["x0"]) and x <= float(_pier["x1"]) and z >= float(_pier["z0"]) and z <= float(_pier["z1"]):
		return true
	return x >= float(head["x0"]) and x <= float(_pier["x1"]) and z >= float(head["z0"]) and z <= float(_pier["z1"])


## Nearest-cell ground height in metres (the grounding probes). The pier counts as 1 m of "land" like in H2D-1.
func height_at(x: float, z: float) -> float:
	if on_pier(x, z):
		return float(_pier["height_m"])
	var i := _idx(x, z)
	if i < 0 or _hd.is_empty():
		return -99.0
	return _lut[_hd[i]]


## Bilinear ground height: the walker's feet follow the slope smoothly.
func height_smooth(x: float, z: float) -> float:
	if _hd.is_empty():
		return -99.0
	var fx := (x - ox) / cell - 0.5
	var fz := (z - oz) / cell - 0.5
	var ix := int(floorf(fx))
	var iz := int(floorf(fz))
	var tx := fx - float(ix)
	var tz := fz - float(iz)
	var h00 := _cell_h(ix, iz)
	var h10 := _cell_h(ix + 1, iz)
	var h01 := _cell_h(ix, iz + 1)
	var h11 := _cell_h(ix + 1, iz + 1)
	return lerpf(lerpf(h00, h10, tx), lerpf(h01, h11, tx), tz)


func _cell_h(ix: int, iz: int) -> float:
	if ix < 0 or iz < 0 or ix >= n or iz >= n:
		return -8.0
	return _lut[_hd[(iz * n + ix) * 4]]


func class_at(x: float, z: float) -> int:
	var i := _idx(x, z)
	if i < 0 or _bd.is_empty():
		return 0
	return _bd[i] >> 4


## Rise over run, 2 m baseline.
func slope_at(x: float, z: float) -> float:
	var gx := (height_smooth(x + 1.0, z) - height_smooth(x - 1.0, z)) * 0.5
	var gz := (height_smooth(x, z + 1.0) - height_smooth(x, z - 1.0)) * 0.5
	return sqrt(gx * gx + gz * gz)


func in_blocker(x: float, z: float, r: float) -> bool:
	for b in blockers:
		var bb := b as Array
		if x > float(bb[0]) - r and x < float(bb[2]) + r and z > float(bb[1]) - r and z < float(bb[3]) + r:
			return true
	var key := Vector2i(int(floorf(x / _chunk_m)), int(floorf(z / _chunk_m)))
	for dz in range(-1, 2):
		for dx in range(-1, 2):
			var k := Vector2i(key.x + dx, key.y + dz)
			if not _chunks.has(k):
				continue
			var tr: PackedFloat32Array = (_chunks[k] as Dictionary)["trunks"]
			var m := 0
			while m + 2 < tr.size():
				var ddx := x - tr[m]
				var ddz := z - tr[m + 1]
				var rr := r + tr[m + 2]
				if ddx * ddx + ddz * ddz < rr * rr:
					return true
				m += 3
	return false


## May a person with a 0.45 m body radius stand at (x, z)? The rules are in docs/H2D1_2_SCALE_AND_LAND.md and are
## mirrored
## by tools/h2d/check_land.py (which checks the on-foot route statically).
func walkable(x: float, z: float, r: float = 0.45) -> bool:
	if on_pier(x, z):
		return true
	var i := _idx(x, z)
	if i < 0 or _hd.is_empty():
		return false
	if height_smooth(x, z) < walk_min_h:
		return false
	if (_bd[i] >> 4) == CLIFF_CLASS:
		return false
	if slope_at(x, z) > walk_max_slope:
		return false
	return not in_blocker(x, z, r)
