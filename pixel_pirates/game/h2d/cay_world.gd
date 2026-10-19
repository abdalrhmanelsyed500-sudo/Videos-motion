# gdlint: disable=max-public-methods
extends RefCounted
# gdlint: disable=class-definitions-order
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
var port: Dictionary = {}   # the "port" section of anvil_cay.json (CP-1 Fish Row)
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
# CP-1 Fish Row: decks, bridges, props, boats, NPC sprites and markers
var _decks: Array = []
var _deck_mat: ShaderMaterial
var _zoom_mats: Array = []          # sprite materials drawn at the on-foot scale (14.4 px per metre)
var _sprite_zoom := -1.0
var _port_nodes: Array = []
var _npc_node: MultiMeshInstance3D
var _npc_blobs: MultiMeshInstance3D
var _marker_node: MultiMeshInstance3D


## `tex_fn(file) -> Texture2D` and `mat_fn(shader_file) -> ShaderMaterial` are the view's loaders (the normal
## ResourceLoader path). `parent` is the root of the 3D world: the view's SubViewport (a Node, not a Node3D); the
## island's own Node3D "AnvilCay" is added under it.
func build(parent: Node, ocean_mat: ShaderMaterial, tex_fn: Callable, mat_fn: Callable) -> void:
	_tex_fn = tex_fn
	_mat_fn = mat_fn
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
	if meta.has("port"):
		_build_port(tex_fn, mat_fn)


# ---- CP-1 revision, P3: what the player sees on the fishing grounds -----------------------------------------------------------
# A beacon pole and a ring of buoys mark every ground (visible from afar); gulls circle above it; the shoal glitters; and while the nets
# are out a line of corks and foam trails behind the ship. All are camera-facing sprites of the cue atlas, in a few MultiMeshes.
const CUE_AABB := AABB(Vector3(-1300.0, -10.0, -600.0), Vector3(2600.0, 90.0, 2900.0))
const CUE_BEACON := 0
const CUE_BUOY_RED := 1
const CUE_BUOY_WHITE := 2
const CUE_GULL_UP := 3
const CUE_GULL_DOWN := 4
const CUE_SPARK := 5
const CUE_CORK := 6
const CUE_FOAM := 7
const GULLS_PER_GROUND := 6
const SPARKS_PER_GROUND := 26
const TRAIL_N := 16
const CUE_NEAR_M := 950.0
var _tex_fn: Callable
var _mat_fn: Callable
var _cue_grounds: Array = []
var _cue_birds: MultiMeshInstance3D
var _cue_sparks: MultiMeshInstance3D
var _cue_trail: MultiMeshInstance3D
var _cue_static: MultiMeshInstance3D
var _cue_rng := RandomNumberGenerator.new()
var _spark_off: PackedFloat32Array = PackedFloat32Array()
var _trail: Array = []
var _trail_t := 0.0


## `grounds` = [{id, x, z, r}]. Builds the static markers and the animated sets.
func build_cues(grounds: Array) -> void:
	if _root == null or not port.has("atlases") or not (port["atlases"] as Dictionary).has("cue"):
		return
	var atlas: Dictionary = (port["atlases"] as Dictionary)["cue"]
	_cue_grounds = grounds
	_cue_rng.seed = 424242
	var fixed: Array = []
	for g in grounds:
		var gd := g as Dictionary
		var gx := float(gd["x"])
		var gz := float(gd["z"])
		var r := float(gd["r"])
		fixed.append({"type": CUE_BEACON, "x_m": gx, "z_m": gz, "y_m": -0.1, "scale": 1.7, "bob": 0.1})
		for k in 10:
			var a := TAU * float(k) / 10.0
			fixed.append({"type": CUE_BUOY_RED if k % 2 == 0 else CUE_BUOY_WHITE, "x_m": gx + cos(a) * r * 0.88, "z_m": gz + sin(a) * r * 0.88,
					"y_m": -0.1, "scale": 1.25, "bob": 0.14})
	_cue_static = _build_sprites(fixed, atlas, true, _tex_fn, _mat_fn)
	_cue_static.multimesh.custom_aabb = CUE_AABB
	_cue_birds = _make_cue_mm(grounds.size() * GULLS_PER_GROUND, atlas, 1.0)
	_cue_sparks = _make_cue_mm(grounds.size() * SPARKS_PER_GROUND, atlas, 1.6)
	_cue_trail = _make_cue_mm(TRAIL_N * 2, atlas, 1.0)
	_spark_off.resize(grounds.size() * SPARKS_PER_GROUND * 3)
	for i in grounds.size() * SPARKS_PER_GROUND:
		var rr := sqrt(_cue_rng.randf()) * float((grounds[i / SPARKS_PER_GROUND] as Dictionary)["r"]) * 0.8
		var aa := _cue_rng.randf() * TAU
		_spark_off[i * 3] = cos(aa) * rr
		_spark_off[i * 3 + 1] = sin(aa) * rr
		_spark_off[i * 3 + 2] = _cue_rng.randf() * TAU


func _make_cue_mm(count: int, atlas: Dictionary, light: float) -> MultiMeshInstance3D:
	var mat := _sprite_material(atlas, true, _tex_fn, _mat_fn)
	mat.set_shader_parameter("sprite_light", light)
	var node := _make_dynamic_mm(count, mat, QuadMesh.new())
	node.multimesh.custom_aabb = CUE_AABB
	return node


## Called every frame by the port controller. `ship` = Vector2 (x, z), `heading_deg`, `nets` = the nets are down, `moving` = metres per
## second (the wake only trails while the ship moves).
func update_cues(dt: float, t: float, ship: Vector2, heading_deg: float, nets: bool, _speed_ms: float) -> void:
	if _cue_birds == null:
		return
	var bm := _cue_birds.multimesh
	var sm := _cue_sparks.multimesh
	for gi in _cue_grounds.size():
		var g := _cue_grounds[gi] as Dictionary
		var gx := float(g["x"])
		var gz := float(g["z"])
		var near := ship.distance_to(Vector2(gx, gz)) < CUE_NEAR_M
		for k in GULLS_PER_GROUND:
			var i := gi * GULLS_PER_GROUND + k
			if not near:
				bm.set_instance_custom_data(i, Color(0.0, 0.0, 0.0, 0.0))
				continue
			var ph := float(k) * 1.047 + float(gi) * 0.7
			var rad := 26.0 + 9.0 * float(k % 3)
			var a := ph + t * (0.30 + 0.05 * float(k % 3)) * (1.0 if k % 2 == 0 else -1.0)
			var y := 13.0 + 4.0 * sin(t * 0.8 + ph) + float(k % 3) * 2.0
			bm.set_instance_transform(i, Transform3D(Basis.IDENTITY, Vector3(gx + cos(a) * rad, y, gz + sin(a) * rad)))
			bm.set_instance_custom_data(i, Color(float(CUE_GULL_UP if fposmod(t * 2.6 + ph, 1.0) < 0.5 else CUE_GULL_DOWN), 1.0, 0.0, 0.0))
		for k in SPARKS_PER_GROUND:
			var i2 := gi * SPARKS_PER_GROUND + k
			if not near:
				sm.set_instance_custom_data(i2, Color(0.0, 0.0, 0.0, 0.0))
				continue
			var ox2 := _spark_off[i2 * 3]
			var oz2 := _spark_off[i2 * 3 + 1]
			var phs := _spark_off[i2 * 3 + 2]
			var f := maxf(sin(t * 2.4 + phs), 0.0)
			f = f * f * f
			sm.set_instance_transform(i2, Transform3D(Basis.IDENTITY, Vector3(gx + ox2, 0.15, gz + oz2)))
			sm.set_instance_custom_data(i2, Color(float(CUE_SPARK), 0.15 + 1.05 * f, 0.0, 0.0) if f > 0.02 else Color(0.0, 0.0, 0.0, 0.0))
	# the net line: corks and foam behind the ship while the nets are down
	var tm := _cue_trail.multimesh
	if nets:
		_trail_t -= dt
		if _trail_t <= 0.0:
			_trail_t = 0.45
			var h := deg_to_rad(heading_deg)
			var stern := ship - Vector2(sin(h), -cos(h)) * 9.0
			_trail.push_front(Vector3(stern.x, stern.y, t))
			if _trail.size() > TRAIL_N:
				_trail.pop_back()
	else:
		_trail.clear()
	for i in TRAIL_N:
		var ci := i * 2
		if i >= _trail.size():
			tm.set_instance_custom_data(ci, Color(0.0, 0.0, 0.0, 0.0))
			tm.set_instance_custom_data(ci + 1, Color(0.0, 0.0, 0.0, 0.0))
			continue
		var p := _trail[i] as Vector3
		var age := clampf((t - p.z) / (TRAIL_N * 0.45), 0.0, 1.0)
		tm.set_instance_transform(ci, Transform3D(Basis.IDENTITY, Vector3(p.x, 0.0 + 0.08 * sin(t * 3.0 + float(i)), p.y)))
		tm.set_instance_custom_data(ci, Color(float(CUE_CORK), 1.0, 0.1, 0.0))
		tm.set_instance_transform(ci + 1, Transform3D(Basis.IDENTITY, Vector3(p.x + 1.2, 0.02, p.y + 0.8)))
		tm.set_instance_custom_data(ci + 1, Color(float(CUE_FOAM), 1.1 - 0.7 * age, 0.0, 0.0))


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
	var ppm := float(atlas.get("px_per_m", PX_PER_M))
	m.set_shader_parameter("m_per_px", 1.0 / ppm)
	m.set_shader_parameter("glow_on", 1.0 if glow else 0.0)
	if ppm > 10.0:
		_zoom_mats.append(m)
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
		var bob := float(t.get("bob", 0.12 if str(t.get("name", "")).begins_with("buoy") else 0.0))
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
	# H2D-1.2.2: the culling box is in the NODE's local space and Godot never adds the instance transforms to a custom
	# AABB. The hero therefore moves the NODE (set_hero) and keeps its one instance at the identity; a box left at the
	# world origin made the pirate vanish about 25 m from it (see tools/h2d/check_hero_cull.py).
	mm.custom_aabb = AABB(Vector3(-4.0, -2.0, -4.0), Vector3(8.0, 10.0, 8.0))
	mm.set_instance_transform(0, Transform3D.IDENTITY)
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
	if _deck_mat != null:
		_deck_mat.set_shader_parameter("texel_m", 1.0 / (PX_PER_M * zoom))
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
	var y := ground_y(x, z)
	_hero.position = Vector3(x, y, z)  # the node carries the position, so the culling box follows the sprite
	_hero.multimesh.set_instance_custom_data(0, Color(float(row * 4 + frame), 1.0, 0.0, 0.0))
	_hero_mat.set_shader_parameter("m_per_px", 1.0 / (PX_PER_M * zoom))
	set_sprite_zoom(zoom)
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
	var dh := deck_height(x, z)
	if not is_nan(dh):
		return dh
	if _in_moored_hull(x, z):
		return 1.0          # a moored boat is as solid as land to the ship's hull probes
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


## The blockers are bucketed in 16 m cells (a rectangle goes into every cell it touches, grown by 1 m), so a walk test reads a handful of
## rectangles instead of all ~1000 (the capital has that many; ~150 people ask every frame).
const BGRID_M := 16.0
var _bgrid: Dictionary = {}


func _build_bgrid() -> void:
	_bgrid.clear()
	for b in blockers:
		var bb := b as Array
		var cx0 := int(floorf((float(bb[0]) - 1.0) / BGRID_M))
		var cx1 := int(floorf((float(bb[2]) + 1.0) / BGRID_M))
		var cz0 := int(floorf((float(bb[1]) - 1.0) / BGRID_M))
		var cz1 := int(floorf((float(bb[3]) + 1.0) / BGRID_M))
		for cz in range(cz0, cz1 + 1):
			for cx in range(cx0, cx1 + 1):
				var k := Vector2i(cx, cz)
				if not _bgrid.has(k):
					_bgrid[k] = []
				(_bgrid[k] as Array).append(bb)


func in_blocker(x: float, z: float, r: float) -> bool:
	if _bgrid.is_empty() and not blockers.is_empty():
		_build_bgrid()
	var cell_list: Variant = _bgrid.get(Vector2i(int(floorf(x / BGRID_M)), int(floorf(z / BGRID_M))))
	if cell_list != null:
		for b in cell_list as Array:
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
# gdlint: disable=max-returns
func walkable(x: float, z: float, r: float = 0.45) -> bool:
	if on_pier(x, z):
		return true
	if not is_nan(deck_height(x, z)):
		return not in_blocker(x, z, r)          # CP-1: wharf and bridges are floors; props on them still block
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
# gdlint: enable=max-returns


# ---- CP-1 Fish Row: decks, bridges, people, markers -----------------------------------------------------------------
## The deck height at (x, z) when a wharf or bridge deck is there, else NAN.
func deck_height(x: float, z: float) -> float:
	for d in _decks:
		var dd := d as Dictionary
		if x >= float(dd["x0"]) and x <= float(dd["x1"]) and z >= float(dd["z0"]) and z <= float(dd["z1"]):
			return float(dd["h"])
	return NAN


func _in_moored_hull(x: float, z: float) -> bool:
	for h in port.get("hulls", []):
		var hh := h as Array
		if x >= float(hh[0]) and x <= float(hh[2]) and z >= float(hh[1]) and z <= float(hh[3]):
			return true
	return false


## Where a person's feet are: the pier, a deck, or the smoothed ground.
func ground_y(x: float, z: float) -> float:
	if on_pier(x, z):
		return float(_pier["height_m"])
	var dh := deck_height(x, z)
	if not is_nan(dh):
		return dh
	return height_smooth(x, z)


## Sprites drawn at the on-foot scale (people, stalls, boats, markers) share the pirate's world scale, so a stall is the same
## size whether the camera is still easing in or not: 1 / (3.6 x land.zoom) metres per sprite pixel.
func set_sprite_zoom(zoom: float) -> void:
	if absf(zoom - _sprite_zoom) < 0.0005:
		return
	_sprite_zoom = zoom
	for m in _zoom_mats:
		(m as ShaderMaterial).set_shader_parameter("m_per_px", 1.0 / (PX_PER_M * zoom))


func _build_port(tex_fn: Callable, mat_fn: Callable) -> void:
	port = meta["port"]
	_decks = port["decks"]
	_build_decks(mat_fn)
	var at: Dictionary = port["atlases"]
	_port_nodes.append(_build_sprites(port["props"] as Array, at["stall"] as Dictionary, true, tex_fn, mat_fn))
	_port_nodes.append(_build_sprites(port["big"] as Array, at["big"] as Dictionary, true, tex_fn, mat_fn))
	_port_nodes.append(_build_sprites(port["ships"] as Array, at["ships"] as Dictionary, false, tex_fn, mat_fn))
	# the capital: one MultiMesh per atlas (small houses, grand buildings, civic monuments, street props) and the planted trees
	if port.has("city"):
		var cl: Dictionary = (port["city"] as Dictionary)["lists"]
		for key in ["bld", "grand", "civic", "street"]:
			if cl.has(key) and not (cl[key] as Array).is_empty():
				_port_nodes.append(_build_sprites(cl[key] as Array, at[key] as Dictionary, true, tex_fn, mat_fn))
		var trees: Array = (port["city"] as Dictionary)["trees"]
		if not trees.is_empty():
			_port_nodes.append(_build_sprites(trees, meta["veg_atlas"] as Dictionary, false, tex_fn, mat_fn))
	var npcs: Array = port["npcs"]
	# one MultiMesh for every person (ONE draw call), one for their contact shadows, one for the floating markers
	var nat: Dictionary = at["npc"]
	var nmat := _sprite_material(nat, false, tex_fn, mat_fn)
	nmat.set_shader_parameter("depth_bias", 0.8)
	nmat.set_shader_parameter("sprite_light", 0.7)
	_npc_node = _make_dynamic_mm(npcs.size(), nmat, QuadMesh.new())
	var bm := PlaneMesh.new()
	bm.size = Vector2(1.5, 0.8)
	_npc_blobs = _make_dynamic_mm(npcs.size(), mat_fn.call("blob.gdshader") as ShaderMaterial, bm)
	var kmat := _sprite_material(at["misc"] as Dictionary, true, tex_fn, mat_fn)
	kmat.set_shader_parameter("depth_bias", 5.0)
	kmat.set_shader_parameter("sprite_light", 1.6)
	_marker_node = _make_dynamic_mm(16, kmat, QuadMesh.new())
	set_npcs([])
	set_markers([])


## A MultiMeshInstance3D whose instances move every frame: the culling box (in node space, and the node stays at the
## origin) covers the whole district and the harbour around it (see the hero bug of H2D-1.2.1).
func _make_dynamic_mm(count: int, mat: Material, mesh: Mesh) -> MultiMeshInstance3D:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	mm.mesh = mesh
	mm.instance_count = maxi(count, 1)
	mm.custom_aabb = AABB(Vector3(-260.0, -10.0, -340.0), Vector3(520.0, 60.0, 400.0))
	var node := MultiMeshInstance3D.new()
	node.multimesh = mm
	node.material_override = mat
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_root.add_child(node)
	for i in mm.instance_count:
		mm.set_instance_transform(i, Transform3D(Basis.IDENTITY, Vector3(0.0, -50.0, 0.0)))
		mm.set_instance_custom_data(i, Color(0.0, 0.0, 0.0, 0.0))
	return node


## The wharf and the two bridges: boxes merged into ONE mesh (one draw call), planks painted by pier.gdshader.
func _build_decks(mat_fn: Callable) -> void:
	_deck_mat = mat_fn.call("pier.gdshader") as ShaderMaterial
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for d in _decks:
		var dd := d as Dictionary
		var top := float(dd["h"])
		var bm := BoxMesh.new()
		bm.size = Vector3(float(dd["x1"]) - float(dd["x0"]), top + 0.8, float(dd["z1"]) - float(dd["z0"]))
		var c := Vector3((float(dd["x0"]) + float(dd["x1"])) * 0.5, top - (top + 0.8) * 0.5, (float(dd["z0"]) + float(dd["z1"])) * 0.5)
		st.append_from(bm, 0, Transform3D(Basis.IDENTITY, c))
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = _deck_mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_root.add_child(mi)
	_glow_mats.append(_deck_mat)


## `people` = PortNpcs.people (dictionaries with x, z, look, row, frame, hidden). Hidden people are scaled to nothing.
func set_npcs(people: Array) -> void:
	if _npc_node == null:
		return
	var mm := _npc_node.multimesh
	var bb := _npc_blobs.multimesh
	for i in mm.instance_count:
		if i >= people.size() or bool((people[i] as Dictionary)["hidden"]):
			mm.set_instance_custom_data(i, Color(0.0, 0.0, 0.0, 0.0))
			bb.set_instance_transform(i, Transform3D(Basis.IDENTITY, Vector3(0.0, -50.0, 0.0)))
			continue
		var pe := people[i] as Dictionary
		var x := float(pe["x"])
		var z := float(pe["z"])
		var y := ground_y(x, z)
		mm.set_instance_transform(i, Transform3D(Basis.IDENTITY, Vector3(x, y, z)))
		mm.set_instance_custom_data(i, Color(float(int(pe["look"]) * 16 + int(pe["row"]) * 4 + int(pe["frame"])), 1.0, 0.0, 0.0))
		bb.set_instance_transform(i, Transform3D(Basis.IDENTITY, Vector3(x, y + 0.06, z)))
		bb.set_instance_custom_data(i, Color(0.0, 0.0, 0.0, 0.0))


## `list` = [{x, y, z, type}] (type = index in the misc atlas: 0 recruit, 1 recruit you can afford, 2 fish market, 3 notice board).
func set_markers(list: Array) -> void:
	if _marker_node == null:
		return
	var mm := _marker_node.multimesh
	for i in mm.instance_count:
		if i >= list.size():
			mm.set_instance_custom_data(i, Color(0.0, 0.0, 0.0, 0.0))
			continue
		var m := list[i] as Dictionary
		mm.set_instance_transform(i, Transform3D(Basis.IDENTITY, Vector3(float(m["x"]), float(m["y"]), float(m["z"]))))
		mm.set_instance_custom_data(i, Color(float(int(m["type"])), 1.0, float(m.get("bob", 0.16)), 0.0))


func npc_count() -> int:
	return (port.get("npcs", []) as Array).size()
