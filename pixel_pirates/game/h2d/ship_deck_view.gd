extends Node3D
## CP-2 Release A: the 3D model of the ship you can walk on: the main deck with the captain's cabin, the helm wheel, the fishing winch,
## the fish barrels, the mast, rigging and the crow's nest; the sleeping deck; the provisioning hold. It lives in the sea view's
## SubViewport, is drawn only while the pirate is on foot aboard (sea_view_3d.gd cross-fades it with the 16-heading sprite), and is
## built from the SAME ship_layout.gd the walker collides with: every solid thing you see is a layout obstacle, so what looks
## solid is solid and what looks like a free aisle is one.
## Cheap by design for the Intel HD 3000: the whole ship is about ten meshes (ship_mesh.gd merges boxes, prisms and cylinders),
## ONE spatial shader (ship_deck.gdshader), no real-time lights, no transparency (dither dissolve), no textures.
## Dynamic parts: the whole ship pose (heading, roll, pitch, heave), the boom and mainsail trim, the wheel, the fish in the barrels
## (from the real hold), the pieces on the provision racks (from the real inventory), the cabin roof dissolve, the hole around the pirate.
## Model space: x starboard, y up, -z toward the bow; ship-local (u, v) becomes (v, -u) (ShipMesh.p). NOT YET RUN ON THE USER'S PC.
const Layout := preload("res://h2d/ship_layout.gd")
const ShipMesh := preload("res://h2d/ship_mesh.gd")
const SHADER := "res://h2d/shaders/ship_deck.gdshader"
const F := Layout.FLOOR_Y
const NEST_Y := Layout.NEST_Y
const MAST_TOP := F + 11.6
const BOOM_Y := F + 3.0
const BOOM_LEN := 6.4
const SAIL_TOP := 8.4
# palette (the wood ramp matches the pier and the sprites)
const WOOD_D := Color(0.29, 0.157, 0.078)
const WOOD_M := Color(0.427, 0.251, 0.1255)
const WOOD_L := Color(0.58, 0.404, 0.18)
const DECK_C := Color(0.70, 0.55, 0.33)
const HULL_C := Color(0.36, 0.22, 0.13)
const TRIM_R := Color(0.55, 0.16, 0.12)
const CABIN_C := Color(0.50, 0.33, 0.20)
const ROOF_C := Color(0.33, 0.20, 0.13)
const CANVAS_C := Color(0.93, 0.87, 0.70)
const ROPE_C := Color(0.71, 0.58, 0.36)
const IRON_C := Color(0.23, 0.24, 0.27)
const LAMP_C := Color(1.0, 0.80, 0.42)
const VOID_C := Color(0.035, 0.03, 0.04)
const SEE := 0.5

var lay: RefCounted = Layout.new()
var root: Node3D = Node3D.new()
var _g_open: Node3D = Node3D.new()
var _g_sleep: Node3D = Node3D.new()
var _g_hold: Node3D = Node3D.new()
var _m_open: ShaderMaterial
var _m_nest: ShaderMaterial
var _m_cabin: ShaderMaterial
var _m_cabin_up: ShaderMaterial
var _m_sleep: ShaderMaterial
var _m_hold: ShaderMaterial
var _cabin_up: MeshInstance3D
var _boom: Node3D = Node3D.new()
var _wheel: Node3D = Node3D.new()
var _fish: Array[MeshInstance3D] = []
var _zones: Dictionary = {}
var _level := 0
var _alpha := 1.0
var _cabin_fade := 1.0
var _stats := {"meshes": 0, "vertices": 0}
var _store_units: Dictionary = {}


static func C(c: Color, see := false) -> Color:
	return Color(c.r, c.g, c.b, SEE if see else 1.0)


func _ready() -> void:
	pass


## Build every mesh. `texel` = metres per art pixel at the deck zoom.
func build(texel: float = 0.0694) -> void:
	add_child(root)
	root.add_child(_g_open)
	root.add_child(_g_sleep)
	root.add_child(_g_hold)
	_m_open = _material(texel, 0.0, 0.0)
	_m_nest = _material(texel, 0.0, 0.0)
	_m_cabin = _material(texel, 0.65, 1.0)
	_m_cabin_up = _material(texel, 0.0, 0.0)
	_m_sleep = _material(texel, 1.0, 1.0)
	_m_hold = _material(texel, 1.0, 1.0)
	# lantern positions in MODEL space (x = v, y, z = -u)
	_set_lamps(_m_open, [Vector4(0.0, F + 2.0, 10.8, 0.8), Vector4(Layout.HELM.y + 0.4, F + 1.2, -Layout.HELM.x, 0.7), Vector4(0.0, F + 1.7, -9.0, 0.8), Vector4(0.0, F + 3.4, -1.0, 0.7)])
	_set_lamps(_m_cabin, [Vector4(0.0, F + 1.7, 7.7, 1.0), Vector4(-0.9, F + 1.2, 9.5, 0.6)])
	_set_lamps(_m_sleep, [Vector4(0.0, F + 1.65, -5.5, 0.9), Vector4(0.0, F + 1.65, 0.6, 0.8), Vector4(0.0, F + 1.65, 5.8, 0.8)])
	_set_lamps(_m_hold, [Vector4(0.0, F + 1.75, 3.0, 0.9), Vector4(0.0, F + 1.75, -3.4, 0.9), Vector4(0.0, F + 1.75, -6.0, 0.8)])
	_build_open()
	_build_cabin()
	_build_sleep()
	_build_hold()
	_build_dynamic()
	set_level(Layout.L_DECK)


func stats() -> Dictionary:
	return _stats


func _material(texel: float, interior: float, lamp_day: float) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = load(SHADER) as Shader
	m.set_shader_parameter("texel", texel)
	m.set_shader_parameter("interior", interior)
	m.set_shader_parameter("lamp_day", lamp_day)
	return m


func _set_lamps(m: ShaderMaterial, lamps: Array) -> void:
	var names := ["lampA", "lampB", "lampC", "lampD"]
	for i in 4:
		m.set_shader_parameter(names[i], lamps[i] if i < lamps.size() else Vector4(0.0, 0.0, 0.0, 0.0))


func _mesh_node(b: Object, m: ShaderMaterial, parent: Node3D) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = b.call("build") as ArrayMesh
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.custom_aabb = AABB(Vector3(-16.0, -4.0, -18.0), Vector3(32.0, 22.0, 36.0))
	parent.add_child(mi)
	_stats["meshes"] = int(_stats["meshes"]) + 1
	_stats["vertices"] = int(_stats["vertices"]) + int(b.call("vertex_count"))
	return mi


# ---- small helpers over the builder (everything in ship-local u, v and absolute height y) ------------------------
func _bx(b: ShipMesh, u: float, v: float, y0: float, hu: float, hv: float, h: float, col: Color, mat: int, yaw := 0.0) -> void:
	b.box(ShipMesh.p(u, v, y0 + h * 0.5), Vector3(hv, h * 0.5, hu), col, mat, yaw)


func _lantern(b: ShipMesh, u: float, v: float, y: float) -> void:
	b.box(ShipMesh.p(u, v, y), Vector3(0.1, 0.14, 0.1), LAMP_C, ShipMesh.M_LAMP)
	b.box(ShipMesh.p(u, v, y + 0.2), Vector3(0.13, 0.04, 0.13), IRON_C, ShipMesh.M_IRON)
	b.box(ShipMesh.p(u, v, y - 0.17), Vector3(0.12, 0.03, 0.12), IRON_C, ShipMesh.M_IRON)


func _coil(b: ShipMesh, u: float, v: float, y: float, r: float, turns: int, col: Color = ROPE_C) -> void:
	for k in turns:
		var rr := r - float(k) * 0.045
		if rr > 0.08:
			b.ring(ShipMesh.p(u, v, y + 0.04 + float(k) * 0.035), Vector3.RIGHT, Vector3.BACK, rr, 10, 0.07, col, ShipMesh.M_ROPE)


func _hull_strip(b: ShipMesh, level: int, y0: float, y1: float, inner_only: bool, col: Color, mat: int, step := 0.5) -> void:
	var rg := Layout.hull_range(level)
	var u := rg.x
	while u < rg.y - 0.001:
		var u2 := minf(u + step, rg.y)
		var h0 := Layout.hull_half(level, u)
		var h1 := Layout.hull_half(level, u2)
		for s in [-1.0, 1.0]:
			var sd := float(s)
			if not inner_only:
				b.quad(ShipMesh.p(u, sd * h0, y0), ShipMesh.p(u2, sd * h1, y0), ShipMesh.p(u2, sd * h1, y1), ShipMesh.p(u, sd * h0, y1), col, mat, Vector3(sd, 0.0, 0.0))
			var i0 := h0 - Layout.WALL_MARGIN
			var i1 := h1 - Layout.WALL_MARGIN
			b.quad(ShipMesh.p(u, sd * i0, F), ShipMesh.p(u2, sd * i1, F), ShipMesh.p(u2, sd * i1, y1), ShipMesh.p(u, sd * i0, y1), col.lightened(0.12), mat, Vector3(-sd, 0.0, 0.0))
			b.quad(ShipMesh.p(u, sd * h0, y1), ShipMesh.p(u2, sd * h1, y1), ShipMesh.p(u2, sd * i1, y1), ShipMesh.p(u, sd * i0, y1), WOOD_L, ShipMesh.M_TIMBER, Vector3.UP)
		u = u2


func _floor(b: ShipMesh, level: int, y: float, col: Color) -> void:
	var rg := Layout.hull_range(level)
	var u := rg.x
	while u < rg.y - 0.001:
		var u2 := minf(u + 0.5, rg.y)
		var h0 := Layout.hull_half(level, u)
		var h1 := Layout.hull_half(level, u2)
		b.quad(ShipMesh.p(u, -h0, y), ShipMesh.p(u2, -h1, y), ShipMesh.p(u2, h1, y), ShipMesh.p(u, h0, y), col, ShipMesh.M_DECK, Vector3.UP)
		u = u2


## A rope ladder from the foot (u, v, y0) to the top (u, v, y1), rails 0.8 m apart along u.
func _ladder(b: ShipMesh, u: float, v0: float, y0: float, v1: float, y1: float, rungs: int, see: bool) -> void:
	var rope := C(ROPE_C, see)
	for du in [-0.4, 0.4]:
		b.beam(ShipMesh.p(u + float(du), v0, y0), ShipMesh.p(u + float(du), v1, y1), 0.07, rope, ShipMesh.M_ROPE)
	for k in range(1, rungs + 1):
		var t := float(k) / float(rungs + 1)
		var vv := lerpf(v0, v1, t)
		var yy := lerpf(y0, y1, t)
		b.beam(ShipMesh.p(u - 0.4, vv, yy), ShipMesh.p(u + 0.4, vv, yy), 0.06, C(WOOD_L, see), ShipMesh.M_TIMBER)


## A wooden ladder in a hatch: two rails and rungs, leaning from (u0, y0) at the foot to (u1, y1) at the top, v = +-0.3.
func _wood_ladder(b: ShipMesh, u0: float, y0: float, u1: float, y1: float, v: float, rungs: int) -> void:
	for s in [-1.0, 1.0]:
		b.beam(ShipMesh.p(u0, v + float(s) * 0.3, y0), ShipMesh.p(u1, v + float(s) * 0.3, y1), 0.08, WOOD_L, ShipMesh.M_TIMBER)
	for k in range(1, rungs + 1):
		var t := float(k) / float(rungs + 1)
		b.beam(ShipMesh.p(lerpf(u0, u1, t), v - 0.3, lerpf(y0, y1, t)), ShipMesh.p(lerpf(u0, u1, t), v + 0.3, lerpf(y0, y1, t)), 0.06, WOOD_M, ShipMesh.M_TIMBER)


func _coaming(b: ShipMesh, c: Vector2, half: Vector2, y: float, h: float) -> void:
	var t := 0.1
	_bx(b, c.x - half.x + t * 0.5, c.y, y, t * 0.5, half.y, h, WOOD_M, ShipMesh.M_TIMBER)
	_bx(b, c.x + half.x - t * 0.5, c.y, y, t * 0.5, half.y, h, WOOD_M, ShipMesh.M_TIMBER)
	_bx(b, c.x, c.y - half.y + t * 0.5, y, half.x, t * 0.5, h, WOOD_M, ShipMesh.M_TIMBER)
	_bx(b, c.x, c.y + half.y - t * 0.5, y, half.x, t * 0.5, h, WOOD_M, ShipMesh.M_TIMBER)
	b.quad(ShipMesh.p(c.x - half.x + t, c.y - half.y + t, y + 0.02), ShipMesh.p(c.x + half.x - t, c.y - half.y + t, y + 0.02),
			ShipMesh.p(c.x + half.x - t, c.y + half.y - t, y + 0.02), ShipMesh.p(c.x - half.x + t, c.y + half.y - t, y + 0.02), VOID_C, ShipMesh.M_VOID, Vector3.UP)


## An upright barrel. `open` leaves the top off (the fish barrels: the fish disk sits inside).
func _barrel(b: ShipMesh, c: Vector2, r: float, y: float, h: float, open: bool, col: Color = WOOD_M) -> void:
	b.cyl(ShipMesh.p(c.x, c.y, y), r, h, 10, col, ShipMesh.M_BARREL, r * 0.9, open, false)
	if open:
		b.quad(ShipMesh.p(c.x - r * 0.8, c.y - r * 0.8, y + 0.08), ShipMesh.p(c.x + r * 0.8, c.y - r * 0.8, y + 0.08),
				ShipMesh.p(c.x + r * 0.8, c.y + r * 0.8, y + 0.08), ShipMesh.p(c.x - r * 0.8, c.y + r * 0.8, y + 0.08), VOID_C, ShipMesh.M_VOID, Vector3.UP)
	else:
		b.cyl(ShipMesh.p(c.x, c.y, y + h - 0.02), r * 0.9, 0.04, 10, col.lightened(0.2), ShipMesh.M_TIMBER, r * 0.88, false, false)


func _crate(b: ShipMesh, c: Vector2, half: Vector2, y: float, h: float, col: Color = Color(0.56, 0.40, 0.22), yaw := 0.0) -> void:
	b.box(ShipMesh.p(c.x, c.y, y + h * 0.5), Vector3(half.y, h * 0.5, half.x), col, ShipMesh.M_CRATE, yaw)


# ---- the open air: hull, main deck, mast, rigging, winch, barrels, helm, nest ---------------------------------------
func _build_open() -> void:
	var b := ShipMesh.new()
	var rail_top := F + 0.95
	# the hull outside and the bulwark, the deck planks
	_hull_strip(b, 0, -0.5, rail_top, false, HULL_C, ShipMesh.M_HULL)
	# a red wale along the hull side
	for s in [-1.0, 1.0]:
		var u := -11.0
		while u < 10.5:
			var u2 := minf(u + 0.5, 11.0)
			var h0 := Layout.hull_half(0, u) + 0.02
			var h1 := Layout.hull_half(0, u2) + 0.02
			b.quad(ShipMesh.p(u, float(s) * h0, F - 0.25), ShipMesh.p(u2, float(s) * h1, F - 0.25), ShipMesh.p(u2, float(s) * h1, F - 0.05),
					ShipMesh.p(u, float(s) * h0, F - 0.05), TRIM_R, ShipMesh.M_PAINT, Vector3(float(s), 0.0, 0.0))
			u = u2
	_floor(b, 0, F, DECK_C)
	# transom (stern wall), the stem post and the bowsprit
	b.quad(ShipMesh.p(-11.0, -1.9, -0.5), ShipMesh.p(-11.0, 1.9, -0.5), ShipMesh.p(-11.0, 1.9, rail_top + 0.1), ShipMesh.p(-11.0, -1.9, rail_top + 0.1), HULL_C, ShipMesh.M_HULL, Vector3(0.0, 0.0, 1.0))
	b.quad(ShipMesh.p(-10.95, -1.9, F + 0.4), ShipMesh.p(-10.95, 1.9, F + 0.4), ShipMesh.p(-10.95, 1.9, F + 0.9), ShipMesh.p(-10.95, -1.9, F + 0.9), Color(0.12, 0.17, 0.25), ShipMesh.M_PAINT, Vector3(0.0, 0.0, 1.0))
	_bx(b, 10.8, 0.0, -0.5, 0.18, 0.12, rail_top + 0.9, WOOD_M, ShipMesh.M_TIMBER)
	b.beam(ShipMesh.p(10.7, 0.0, F + 0.7), ShipMesh.p(14.8, 0.0, F + 2.1), 0.22, WOOD_L, ShipMesh.M_TIMBER)
	# rail stanchions every 2 m
	for s in [-1.0, 1.0]:
		var uu := -9.0
		while uu < 9.0:
			var hh := Layout.hull_half(0, uu) - 0.15
			_bx(b, uu, float(s) * hh, rail_top, 0.07, 0.07, 0.3, WOOD_M, ShipMesh.M_TIMBER)
			uu += 2.0
	# the stern: taffrail and the stern lantern post
	_bx(b, -10.8, 0.0, rail_top, 0.08, 1.7, 0.12, WOOD_L, ShipMesh.M_TIMBER)
	_bx(b, -10.8, 0.0, rail_top, 0.06, 0.06, 0.9, WOOD_M, ShipMesh.M_TIMBER)
	_lantern(b, -10.8, 0.0, rail_top + 1.1)
	# the mast and its collar
	b.cyl(ShipMesh.p(Layout.MAST.x, Layout.MAST.y, -0.5), 0.27, MAST_TOP + 0.5, 8, WOOD_M, ShipMesh.M_TIMBER, 0.16, false, false)
	b.cyl(ShipMesh.p(Layout.MAST.x, Layout.MAST.y, F), 0.4, 0.28, 8, WOOD_D, ShipMesh.M_TIMBER, 0.34, false, false)
	for yy in [F + 2.4, F + 6.0, F + 9.6]:
		b.cyl(ShipMesh.p(Layout.MAST.x, Layout.MAST.y, float(yy)), 0.3, 0.1, 8, IRON_C, ShipMesh.M_IRON, -1.0, false, false)
	b.box(ShipMesh.p(Layout.MAST.x, Layout.MAST.y, MAST_TOP + 0.1), Vector3(0.09, 0.14, 0.09), LAMP_C, ShipMesh.M_LAMP)
	# a black pennant at the masthead (flat, pointing aft)
	b.quad(ShipMesh.p(Layout.MAST.x - 0.1, 0.0, MAST_TOP - 0.1), ShipMesh.p(Layout.MAST.x - 1.6, 0.0, MAST_TOP - 0.25), ShipMesh.p(Layout.MAST.x - 0.1, 0.0, MAST_TOP - 0.6), ShipMesh.p(Layout.MAST.x - 0.1, 0.0, MAST_TOP - 0.1), C(Color(0.07, 0.07, 0.09), true), ShipMesh.M_CLOTH)
	# the helm pedestal; the wheel is a separate node (it turns)
	_bx(b, Layout.HELM.x, Layout.HELM.y, F, 0.22, 0.22, 0.78, WOOD_M, ShipMesh.M_TIMBER)
	_bx(b, Layout.HELM.x, Layout.HELM.y, F + 0.78, 0.26, 0.26, 0.06, WOOD_L, ShipMesh.M_TIMBER)
	b.tube(ShipMesh.p(Layout.HELM.x + 0.2, Layout.HELM.y, F + 1.2), ShipMesh.p(Layout.HELM.x - 0.25, Layout.HELM.y, F + 1.2), 0.05, 6, IRON_C, ShipMesh.M_IRON)
	b.box(ShipMesh.p(Layout.HELM.x + 0.1, Layout.HELM.y + 0.4, F + 0.38), Vector3(0.1, 0.38, 0.1), WOOD_D, ShipMesh.M_TIMBER)
	_lantern(b, Layout.HELM.x + 0.1, Layout.HELM.y + 0.4, F + 0.95)
	# the main hatch: coaming, void, ladder
	_coaming(b, Layout.HATCH, Layout.HATCH_HALF, F, 0.35)
	_wood_ladder(b, Layout.HATCH.x + 0.45, F + 0.9, Layout.HATCH.x - 0.1, F - 1.3, Layout.HATCH.y, 5)
	# the fishing winch: sills, uprights, drum, ratchet, cranks, the rope and the davit over the port side
	var w := Layout.WINCH
	for s in [-1.0, 1.0]:
		_bx(b, w.x, w.y + float(s) * 0.42, F, 0.95, 0.07, 0.14, WOOD_D, ShipMesh.M_TIMBER)
		for e in [-1.0, 1.0]:
			_bx(b, w.x + float(e) * 0.75, w.y + float(s) * 0.42, F, 0.08, 0.08, 1.15, WOOD_M, ShipMesh.M_TIMBER)
			b.beam(ShipMesh.p(w.x + float(e) * 0.95, w.y + float(s) * 0.42, F + 0.12), ShipMesh.p(w.x + float(e) * 0.75, w.y + float(s) * 0.42, F + 0.85), 0.07, WOOD_L, ShipMesh.M_TIMBER)
	b.tube(ShipMesh.p(w.x - 0.95, w.y, F + 0.95), ShipMesh.p(w.x + 0.95, w.y, F + 0.95), 0.07, 6, IRON_C, ShipMesh.M_IRON)
	b.tube(ShipMesh.p(w.x - 0.6, w.y, F + 0.95), ShipMesh.p(w.x + 0.6, w.y, F + 0.95), 0.3, 10, WOOD_L, ShipMesh.M_BARREL, false)
	b.tube(ShipMesh.p(w.x - 0.45, w.y, F + 0.95), ShipMesh.p(w.x + 0.3, w.y, F + 0.95), 0.34, 10, ROPE_C.darkened(0.12), ShipMesh.M_ROPE, true)
	b.tube(ShipMesh.p(w.x + 0.62, w.y, F + 0.95), ShipMesh.p(w.x + 0.7, w.y, F + 0.95), 0.4, 10, IRON_C, ShipMesh.M_IRON)
	for e in [-1.0, 1.0]:
		var ex := w.x + float(e) * 0.97
		b.beam(ShipMesh.p(ex, w.y, F + 0.95), ShipMesh.p(ex, w.y + 0.46, F + 1.3), 0.06, IRON_C, ShipMesh.M_IRON)
		b.beam(ShipMesh.p(ex - 0.12, w.y + 0.46, F + 1.3), ShipMesh.p(ex + 0.12, w.y + 0.46, F + 1.3), 0.08, WOOD_L, ShipMesh.M_TIMBER)
	# davit: a post at the port rail, an arm out over the water, a pulley block, the rope down to the net
	var pu := w.x
	_bx(b, pu, -2.7, F, 0.09, 0.09, 2.5, WOOD_M, ShipMesh.M_TIMBER)
	b.beam(ShipMesh.p(pu, -2.7, F + 2.45), ShipMesh.p(pu, -4.4, F + 2.1), 0.14, WOOD_M, ShipMesh.M_TIMBER)
	b.beam(ShipMesh.p(pu, -2.7, F + 1.5), ShipMesh.p(pu, -3.8, F + 2.05), 0.07, WOOD_L, ShipMesh.M_TIMBER)
	b.box(ShipMesh.p(pu, -4.35, F + 1.95), Vector3(0.1, 0.16, 0.14), IRON_C, ShipMesh.M_IRON)
	b.beam(ShipMesh.p(w.x + 0.2, w.y - 0.3, F + 1.2), ShipMesh.p(pu, -2.7, F + 2.4), 0.04, ROPE_C, ShipMesh.M_ROPE)
	b.beam(ShipMesh.p(pu, -2.7, F + 2.4), ShipMesh.p(pu, -4.35, F + 2.05), 0.04, ROPE_C, ShipMesh.M_ROPE)
	b.beam(ShipMesh.p(pu, -4.35, F + 1.9), ShipMesh.p(pu, -4.35, F + 0.95), 0.04, ROPE_C, ShipMesh.M_ROPE)
	# the net bundle hanging at the end of the rope: cork floats and a rolled net
	b.cyl(ShipMesh.p(pu, -4.35, F + 0.45), 0.34, 0.55, 8, Color(0.22, 0.30, 0.30), ShipMesh.M_ROPE, 0.22, false, false)
	for k in 5:
		var a := TAU * float(k) / 5.0
		b.box(ShipMesh.p(pu + cos(a) * 0.34, -4.35 + sin(a) * 0.34, F + 1.0), Vector3(0.06, 0.05, 0.06), Color(0.85, 0.62, 0.3), ShipMesh.M_SACK)
	# net heap and hauled rope on the deck (flat: nothing to trip on)
	b.cyl(ShipMesh.p(1.9, -2.15, F), 0.46, 0.14, 8, Color(0.22, 0.30, 0.30), ShipMesh.M_ROPE, 0.3, false, false)
	b.cyl(ShipMesh.p(2.3, -1.45, F), 0.34, 0.1, 8, Color(0.24, 0.32, 0.31), ShipMesh.M_ROPE, 0.22, false, false)
	# fish barrels (open; the fish are separate nodes)
	for k in Layout.FISH_BARRELS.size():
		_barrel(b, Layout.FISH_BARRELS[k], Layout.FISH_BARREL_R, F, 1.0, true, Color(0.50, 0.33, 0.17))
	# ordinary props from the layout
	for o in lay.call("obstacles", Layout.L_DECK):
		var od: Dictionary = o
		var c: Vector2 = od["c"]
		match str(od["style"]):
			"barrel":
				_barrel(b, c, float(od["r"]), F, float(od["ht"]), false)
			"crate":
				var hf: Vector2 = od["half"]
				_crate(b, c, hf, F, float(od["ht"]))
				if str(od["id"]) == "crate_a":
					_crate(b, c + Vector2(0.05, -0.05), hf * 0.85, F + float(od["ht"]), 0.8, Color(0.50, 0.36, 0.2), 14.0)
			"windlass":
				b.tube(ShipMesh.p(c.x, c.y - 0.62, F + 0.5), ShipMesh.p(c.x, c.y + 0.62, F + 0.5), 0.2, 8, WOOD_L, ShipMesh.M_BARREL)
				for s in [-1.0, 1.0]:
					_bx(b, c.x, c.y + float(s) * 0.55, F, 0.28, 0.07, 0.62, WOOD_M, ShipMesh.M_TIMBER)
				b.ring(ShipMesh.p(c.x + 0.4, c.y, F + 0.5), Vector3.RIGHT, Vector3.UP, 0.26, 6, 0.05, IRON_C, ShipMesh.M_IRON)
				b.beam(ShipMesh.p(c.x, c.y + 0.7, F + 0.5), ShipMesh.p(c.x - 0.3, c.y + 0.7, F + 0.9), 0.06, IRON_C, ShipMesh.M_IRON)
	# rope coils, planks, a boat hook: low things on the deck (nothing blocks)
	_coil(b, -0.2, -2.35, F, 0.34, 4)
	_coil(b, 2.55, 2.4, F, 0.3, 4)
	_coil(b, 7.3, 1.0, F, 0.28, 3)
	_coil(b, -6.6, 2.6, F, 0.3, 4)
	for k in 4:
		_bx(b, -0.7, 2.62 + float(k % 2) * 0.01, F + 0.02 + float(k) * 0.05, 1.5, 0.12, 0.05, WOOD_L if k % 2 == 0 else WOOD_M, ShipMesh.M_TIMBER)
	b.beam(ShipMesh.p(-2.0, -2.7, F + 0.08), ShipMesh.p(0.8, -2.65, F + 0.08), 0.07, WOOD_L, ShipMesh.M_TIMBER)
	# the anchor, hung on the outside of the port bow
	b.beam(ShipMesh.p(8.2, -1.55, F + 1.1), ShipMesh.p(8.2, -1.55, F - 0.1), 0.08, IRON_C, ShipMesh.M_IRON)
	b.beam(ShipMesh.p(8.2, -1.9, F + 0.95), ShipMesh.p(8.2, -1.2, F + 0.95), 0.07, IRON_C, ShipMesh.M_IRON)
	b.beam(ShipMesh.p(8.2, -1.9, F - 0.1), ShipMesh.p(8.2, -1.2, F - 0.1), 0.07, IRON_C, ShipMesh.M_IRON)
	_lantern(b, 9.0, 0.0, F + 1.6)
	_bx(b, 9.0, 0.0, F, 0.05, 0.05, 1.4, WOOD_M, ShipMesh.M_TIMBER)
	_mesh_node(b, _m_open, _g_open)
	_build_rigging()
	_build_nest()


func _build_rigging() -> void:
	var b := ShipMesh.new()
	var m := Layout.MAST
	var rope := C(ROPE_C.darkened(0.08), true)
	# shrouds and ratline ladders on both sides; the starboard ladder at LADDER_BASE is the one you climb
	for s in [-1.0, 1.0]:
		var sd := float(s)
		_ladder(b, m.x, sd * Layout.LADDER_BASE.y, F, sd * Layout.LADDER_TOP_V, NEST_Y, 14, true)
		for du in [-1.3, 1.5]:
			b.beam(ShipMesh.p(m.x + float(du), sd * 2.75, F + 0.9), ShipMesh.p(m.x + float(du) * 0.2, sd * 1.35, NEST_Y - 0.1), 0.06, rope, ShipMesh.M_ROPE)
		for du in [-0.8, 2.2]:
			b.beam(ShipMesh.p(m.x + float(du), sd * 2.8, F + 0.9), ShipMesh.p(m.x, sd * 0.2, MAST_TOP - 0.7), 0.045, rope, ShipMesh.M_ROPE)
	# forestay and backstay
	b.beam(ShipMesh.p(m.x, 0.0, MAST_TOP - 0.2), ShipMesh.p(14.6, 0.0, F + 2.15), 0.05, rope, ShipMesh.M_ROPE)
	b.beam(ShipMesh.p(m.x, 0.0, MAST_TOP - 0.2), ShipMesh.p(-10.8, 0.0, F + 1.9), 0.045, rope, ShipMesh.M_ROPE)
	# the jib: a triangle from the masthead to the bowsprit
	var cream := C(CANVAS_C, true)
	b.tri(ShipMesh.p(m.x + 0.3, 0.0, MAST_TOP - 0.9), ShipMesh.p(13.6, 0.0, F + 2.3), ShipMesh.p(9.2, 0.0, F + 2.9), cream, ShipMesh.M_CANVAS, Vector3(1.0, 0.0, 0.0))
	b.tri(ShipMesh.p(m.x + 0.3, 0.0, MAST_TOP - 0.9), ShipMesh.p(13.6, 0.0, F + 2.3), ShipMesh.p(9.2, 0.0, F + 2.9), cream, ShipMesh.M_CANVAS, Vector3(-1.0, 0.0, 0.0))
	_mesh_node(b, _m_open, _g_open)


func _build_nest() -> void:
	var m := Layout.MAST
	var h := Layout.NEST_HALF
	var b := ShipMesh.new()
	var nf := ShipMesh.new()
	# the floor (own material: it dissolves only while you are NOT in the nest)
	nf.box(ShipMesh.p(m.x, m.y, NEST_Y - 0.09), Vector3(h, 0.09, h), C(DECK_C, true), ShipMesh.M_DECK)
	for s in [-1.0, 1.0]:
		b.beam(ShipMesh.p(m.x - h, float(s) * 0.5, NEST_Y - 0.25), ShipMesh.p(m.x + h, float(s) * 0.5, NEST_Y - 0.25), 0.14, C(WOOD_D, true), ShipMesh.M_TIMBER)
	var col := C(WOOD_M, true)
	var panel := C(Color(0.46, 0.30, 0.17), true)
	# rails: three sides closed with half panels, the starboard side open where the ladder arrives
	for e in [-1.0, 1.0]:
		var ed := float(e)
		b.box(ShipMesh.p(m.x + ed * h, m.y, NEST_Y + 0.28), Vector3(h, 0.28, 0.04), panel, ShipMesh.M_HULL)
	b.box(ShipMesh.p(m.x, m.y - h, NEST_Y + 0.28), Vector3(0.04, 0.28, h), panel, ShipMesh.M_HULL)
	for sgn in [-1.0, 1.0]:
		b.box(ShipMesh.p(m.x + float(sgn) * (h + 0.55) * 0.5, m.y + h, NEST_Y + 0.28), Vector3(0.04, 0.28, (h - 0.55) * 0.5), panel, ShipMesh.M_HULL)
	for cu in [-1.0, 1.0]:
		for cv in [-1.0, 1.0]:
			b.box(ShipMesh.p(m.x + float(cu) * h, m.y + float(cv) * h, NEST_Y + 0.5), Vector3(0.07, 0.5, 0.07), col, ShipMesh.M_TIMBER)
	b.beam(ShipMesh.p(m.x - h, -h, NEST_Y + 1.0), ShipMesh.p(m.x + h, -h, NEST_Y + 1.0), 0.07, col, ShipMesh.M_TIMBER)
	b.beam(ShipMesh.p(m.x - h, -h, NEST_Y + 1.0), ShipMesh.p(m.x - h, h, NEST_Y + 1.0), 0.07, col, ShipMesh.M_TIMBER)
	b.beam(ShipMesh.p(m.x + h, -h, NEST_Y + 1.0), ShipMesh.p(m.x + h, h, NEST_Y + 1.0), 0.07, col, ShipMesh.M_TIMBER)
	b.beam(ShipMesh.p(m.x - h, h, NEST_Y + 1.0), ShipMesh.p(m.x - 0.55, h, NEST_Y + 1.0), 0.07, col, ShipMesh.M_TIMBER)
	b.beam(ShipMesh.p(m.x + h, h, NEST_Y + 1.0), ShipMesh.p(m.x + 0.55, h, NEST_Y + 1.0), 0.07, col, ShipMesh.M_TIMBER)
	b.beam(ShipMesh.p(m.x - 0.5, h, NEST_Y + 0.9), ShipMesh.p(m.x + 0.5, h + 0.1, NEST_Y + 0.9), 0.05, C(ROPE_C, true), ShipMesh.M_ROPE)
	# a brass telescope on the floor and a small lantern
	b.tube(ShipMesh.p(m.x - 0.6, -0.9, NEST_Y + 0.07), ShipMesh.p(m.x + 0.1, -0.7, NEST_Y + 0.07), 0.05, 6, C(Color(0.72, 0.55, 0.2), true), ShipMesh.M_IRON)
	b.box(ShipMesh.p(m.x + 0.9, -0.9, NEST_Y + 0.15), Vector3(0.1, 0.14, 0.1), LAMP_C, ShipMesh.M_LAMP)
	_mesh_node(b, _m_open, _g_open)
	_mesh_node(nf, _m_nest, _g_open)


func _build_dynamic() -> void:
	# the boom and mainsail: pivot at the mast, rotated by the trim; the sail bulges to the side the boom swings to
	var bm := ShipMesh.new()
	_boom.position = ShipMesh.p(Layout.MAST.x, Layout.MAST.y, BOOM_Y)
	_g_open.add_child(_boom)
	bm.beam(Vector3(0.0, 0.0, 0.1), Vector3(0.0, 0.0, BOOM_LEN), 0.18, WOOD_L, ShipMesh.M_TIMBER)
	bm.beam(Vector3(0.0, 0.0, BOOM_LEN), Vector3(0.0, 0.08, BOOM_LEN + 0.2), 0.12, IRON_C, ShipMesh.M_IRON)
	var rows := 6
	var cols := 6
	var cream := C(CANVAS_C, true)
	for r in rows:
		var t0 := float(r) / float(rows)
		var t1 := float(r + 1) / float(rows)
		for c in cols:
			var s0 := float(c) / float(cols)
			var s1 := float(c + 1) / float(cols)
			var a := _sail_pt(t0, s0)
			var bb := _sail_pt(t0, s1)
			var cc := _sail_pt(t1, s1)
			var d := _sail_pt(t1, s0)
			if t1 >= 0.999 and s1 > 0.999:
				bm.tri(a, bb, d, cream, ShipMesh.M_CANVAS, Vector3(1.0, 0.0, 0.0))
			else:
				bm.quad(a, bb, cc, d, cream, ShipMesh.M_CANVAS, Vector3(1.0, 0.0, 0.0))
	_mesh_node(bm, _m_open, _boom)
	# the wheel
	var wb := ShipMesh.new()
	wb.ring(Vector3.ZERO, Vector3.RIGHT, Vector3.UP, 0.46, 12, 0.07, WOOD_L, ShipMesh.M_TIMBER)
	for k in 8:
		var a2 := TAU * float(k) / 8.0
		var dir := Vector3(cos(a2), sin(a2), 0.0)
		wb.beam(dir * 0.06, dir * 0.46, 0.05, WOOD_M, ShipMesh.M_TIMBER)
		wb.beam(dir * 0.46, dir * 0.66, 0.06, WOOD_L, ShipMesh.M_TIMBER)
	wb.tube(Vector3(0.0, 0.0, -0.1), Vector3(0.0, 0.0, 0.1), 0.1, 8, Color(0.72, 0.55, 0.2), ShipMesh.M_IRON)
	_wheel.position = ShipMesh.p(Layout.HELM.x, Layout.HELM.y, F + 1.2)
	_g_open.add_child(_wheel)
	_mesh_node(wb, _m_open, _wheel)
	# the fish in the four barrels
	for k in Layout.FISH_BARRELS.size():
		var fb := ShipMesh.new()
		fb.cyl(Vector3.ZERO, 0.38, 0.14, 9, Color(0.8, 0.85, 0.9), ShipMesh.M_FISH, 0.3, false, false)
		var node := _mesh_node(fb, _m_open, _g_open)
		var c: Vector2 = Layout.FISH_BARRELS[k]
		node.position = ShipMesh.p(c.x, c.y, F + 0.1)
		node.visible = false
		_fish.append(node)


## A point of the mainsail in the boom's frame: t up the luff (0 boom .. 1 head), s along the foot (0 mast .. 1 clew), z aft.
func _sail_pt(t: float, s: float) -> Vector3:
	var length := BOOM_LEN * (1.0 - t * 0.92)
	var belly := 0.6 * sin(PI * s) * (1.0 - t * 0.55)
	return Vector3(belly, 0.12 + t * SAIL_TOP, 0.15 + length * s)


# ---- the captain's cabin -----------------------------------------------------------------------------------------------
func _build_cabin() -> void:
	var low := ShipMesh.new()
	var up := ShipMesh.new()
	var in_f := Layout.CABIN_U0
	var u1 := Layout.CABIN_U1
	# walls: lower half always, upper half (and the roof) dissolves when you walk in
	for o in lay.call("obstacles", Layout.L_DECK):
		var od: Dictionary = o
		if str(od["style"]) != "cabin_wall":
			continue
		var c: Vector2 = od["c"]
		var hf: Vector2 = od["half"]
		_bx(low, c.x, c.y, F, hf.x, hf.y, 1.0, CABIN_C, ShipMesh.M_HULL)
		_bx(up, c.x, c.y, F + 1.0, hf.x, hf.y, 1.4, CABIN_C, ShipMesh.M_HULL)
		# a dark base board and a red band
		_bx(low, c.x, c.y, F + 0.95, hf.x + 0.015, hf.y + 0.015, 0.1, TRIM_R, ShipMesh.M_PAINT)
	# door frame and the open door leaf lying against the inside of the port wall
	_bx(low, u1, Layout.DOOR_V0 + 0.04, F, 0.14, 0.06, 1.0, WOOD_D, ShipMesh.M_TIMBER)
	_bx(low, u1, Layout.DOOR_V1 - 0.04, F, 0.14, 0.06, 1.0, WOOD_D, ShipMesh.M_TIMBER)
	_bx(up, u1, (Layout.DOOR_V0 + Layout.DOOR_V1) * 0.5, F + 1.0, 0.14, 0.7, 0.14, WOOD_D, ShipMesh.M_TIMBER)
	_bx(low, u1 - 0.8, Layout.DOOR_V0 + 0.1, F, 0.65, 0.04, 1.0, WOOD_M, ShipMesh.M_CRATE)
	# windows (dark glass) in the upper walls
	for s in [-1.0, 1.0]:
		for wu in [-9.0, -7.7, -6.4]:
			up.box(ShipMesh.p(float(wu), float(s) * (Layout.CABIN_V - 0.09), F + 1.65), Vector3(0.03, 0.22, 0.28), Color(0.10, 0.15, 0.22), ShipMesh.M_PAINT)
	for wv in [-1.0, 0.0, 1.0]:
		up.box(ShipMesh.p(in_f + 0.11, float(wv) * 1.0, F + 1.65), Vector3(0.28, 0.22, 0.03), Color(0.10, 0.15, 0.22), ShipMesh.M_PAINT)
	# the roof, an overhang, a skylight and the galley pipe
	_bx(up, (in_f + u1) * 0.5 - 0.1, 0.0, F + 2.4, (u1 - in_f) * 0.5 + 0.3, Layout.CABIN_V + 0.28, 0.14, ROOF_C, ShipMesh.M_DECK)
	_bx(up, -8.4, 0.0, F + 2.54, 0.7, 0.45, 0.22, WOOD_M, ShipMesh.M_TIMBER)
	up.box(ShipMesh.p(-8.4, 0.0, F + 2.8), Vector3(0.36, 0.03, 0.62), Color(0.2, 0.3, 0.4), ShipMesh.M_PAINT)
	up.cyl(ShipMesh.p(-6.5, 1.2, F + 2.5), 0.1, 0.9, 6, IRON_C, ShipMesh.M_IRON, 0.09, false, false)
	_lantern(up, -5.7, 0.0, F + 2.9)
	_bx(up, -5.7, 0.0, F + 2.54, 0.04, 0.04, 0.2, IRON_C, ShipMesh.M_IRON)
	_mesh_node(up, _m_cabin_up, root)
	_cabin_up = root.get_child(root.get_child_count() - 1) as MeshInstance3D
	# the furniture (from the layout so it stays where the collision is)
	for o in lay.call("obstacles", Layout.L_DECK):
		var od2: Dictionary = o
		var c2: Vector2 = od2["c"]
		var hf2: Vector2 = od2["half"]
		match str(od2["style"]):
			"desk":
				_bx(low, c2.x, c2.y, F + 0.78, hf2.x + 0.05, hf2.y + 0.05, 0.1, WOOD_L, ShipMesh.M_DECK)
				for sx in [-1.0, 1.0]:
					for sy in [-1.0, 1.0]:
						_bx(low, c2.x + float(sx) * (hf2.x - 0.06), c2.y + float(sy) * (hf2.y - 0.06), F, 0.06, 0.06, 0.78, WOOD_D, ShipMesh.M_TIMBER)
				_bx(low, c2.x - 0.2, c2.y, F + 0.18, 0.18, hf2.y - 0.1, 0.6, WOOD_M, ShipMesh.M_CRATE)
				# the chart on the desk, a compass, a quill and a lantern
				low.quad(ShipMesh.p(c2.x - 0.4, c2.y - 0.8, F + 0.9), ShipMesh.p(c2.x + 0.4, c2.y - 0.8, F + 0.9), ShipMesh.p(c2.x + 0.4, c2.y + 0.5, F + 0.9), ShipMesh.p(c2.x - 0.4, c2.y + 0.5, F + 0.9), Color(0.86, 0.76, 0.52), ShipMesh.M_CANVAS, Vector3.UP)
				low.quad(ShipMesh.p(c2.x - 0.3, c2.y - 0.6, F + 0.91), ShipMesh.p(c2.x + 0.1, c2.y - 0.5, F + 0.91), ShipMesh.p(c2.x + 0.2, c2.y + 0.2, F + 0.91), ShipMesh.p(c2.x - 0.2, c2.y + 0.1, F + 0.91), Color(0.40, 0.55, 0.62), ShipMesh.M_PAINT, Vector3.UP)
				low.ring(ShipMesh.p(c2.x + 0.3, c2.y + 0.72, F + 0.92), Vector3.RIGHT, Vector3.BACK, 0.07, 8, 0.025, Color(0.72, 0.55, 0.2), ShipMesh.M_IRON)
				_lantern(low, c2.x - 0.3, c2.y + 0.78, F + 1.12)
				low.beam(ShipMesh.p(c2.x + 0.1, c2.y - 0.9, F + 0.92), ShipMesh.p(c2.x + 0.4, c2.y - 0.95, F + 1.25), 0.02, CANVAS_C, ShipMesh.M_CLOTH)
			"bed":
				_bx(low, c2.x, c2.y, F, hf2.x, hf2.y, 0.3, WOOD_M, ShipMesh.M_TIMBER)
				_bx(low, c2.x, c2.y, F + 0.3, hf2.x - 0.04, hf2.y - 0.04, 0.14, Color(0.78, 0.72, 0.6), ShipMesh.M_CLOTH)
				_bx(low, c2.x + 0.3, c2.y, F + 0.44, hf2.x - 0.5, hf2.y - 0.06, 0.05, TRIM_R, ShipMesh.M_CLOTH)
				_bx(low, c2.x - hf2.x + 0.22, c2.y, F + 0.44, 0.17, hf2.y - 0.12, 0.1, CANVAS_C, ShipMesh.M_CLOTH)
			"chest":
				_bx(low, c2.x, c2.y, F, hf2.x, hf2.y, 0.5, WOOD_M, ShipMesh.M_CRATE)
				_bx(low, c2.x, c2.y, F + 0.5, hf2.x + 0.02, hf2.y + 0.02, 0.16, WOOD_L, ShipMesh.M_CRATE)
				for k in [-0.4, 0.4]:
					_bx(low, c2.x, c2.y + float(k), F, hf2.x + 0.03, 0.04, 0.68, IRON_C, ShipMesh.M_IRON)
				_bx(low, c2.x + hf2.x + 0.02, c2.y, F + 0.42, 0.03, 0.06, 0.12, Color(0.72, 0.55, 0.2), ShipMesh.M_IRON)
			"shelf":
				_bx(low, c2.x, c2.y, F + 0.55, hf2.x, hf2.y + 0.05, 0.05, WOOD_L, ShipMesh.M_TIMBER)
				_bx(low, c2.x, c2.y, F + 0.95, hf2.x, hf2.y + 0.05, 0.05, WOOD_L, ShipMesh.M_TIMBER)
				var bu := c2.x - hf2.x + 0.1
				var k2 := 0
				while bu < c2.x + hf2.x - 0.1:
					var bh := 0.22 + float(k2 % 3) * 0.05
					var bc: Color = [Color(0.5, 0.18, 0.15), Color(0.2, 0.3, 0.4), Color(0.45, 0.35, 0.18), Color(0.25, 0.4, 0.28)][k2 % 4]
					_bx(low, bu, c2.y, F + 0.6, 0.06, 0.09, bh, bc, ShipMesh.M_PAINT)
					_bx(low, bu, c2.y, F + 1.0, 0.06, 0.09, bh, bc.lightened(0.1), ShipMesh.M_PAINT)
					bu += 0.14
					k2 += 1
	# the floor: a dark rug in the middle, a lantern on the chest
	low.quad(ShipMesh.p(-9.6, -1.6, F + 0.025), ShipMesh.p(-5.9, -1.6, F + 0.025), ShipMesh.p(-5.9, 0.8, F + 0.025), ShipMesh.p(-9.6, 0.8, F + 0.025), Color(0.40, 0.14, 0.12), ShipMesh.M_CLOTH, Vector3.UP)
	low.quad(ShipMesh.p(-9.3, -1.4, F + 0.03), ShipMesh.p(-6.2, -1.4, F + 0.03), ShipMesh.p(-6.2, 0.6, F + 0.03), ShipMesh.p(-9.3, 0.6, F + 0.03), Color(0.56, 0.38, 0.16), ShipMesh.M_CLOTH, Vector3.UP)
	_mesh_node(low, _m_cabin, _g_open)


# ---- the sleeping and equipment deck -------------------------------------------------------------------------------------
func _build_sleep() -> void:
	var b := ShipMesh.new()
	var top := F + 1.5
	_floor(b, 1, F, Color(0.50, 0.38, 0.24))
	_hull_strip(b, 1, F - 0.2, top, false, Color(0.34, 0.21, 0.13), ShipMesh.M_HULL)
	# ribs along both walls and the cross beams overhead (they dissolve near the pirate)
	var u := -8.4
	while u < 8.4:
		var h := Layout.hull_half(1, u) - Layout.WALL_MARGIN
		if h > 0.4:
			for s in [-1.0, 1.0]:
				_bx(b, u, float(s) * (h - 0.06), F, 0.08, 0.07, 2.1, WOOD_M, ShipMesh.M_TIMBER)
			b.beam(ShipMesh.p(u, -h, F + 2.12), ShipMesh.p(u, h, F + 2.12), 0.16, C(WOOD_D, true), ShipMesh.M_TIMBER)
		u += 1.5
	for s in [-1.0, 1.0]:
		b.beam(ShipMesh.p(-8.0, float(s) * 1.45, F + 2.0), ShipMesh.p(7.5, float(s) * 1.45, F + 2.0), 0.13, C(WOOD_M, true), ShipMesh.M_TIMBER)
	# the mast comes down through the deck
	b.cyl(ShipMesh.p(Layout.MAST.x, Layout.MAST.y, F), 0.3, 2.2, 8, WOOD_M, ShipMesh.M_TIMBER, 0.3, false, false)
	for o in lay.call("obstacles", Layout.L_SLEEP):
		var od: Dictionary = o
		var c: Vector2 = od["c"]
		var hf: Vector2 = od["half"]
		match str(od["style"]):
			"hammock":
				_hammock(b, c, hf, 0)
			"bunk":
				_bunk(b, c, hf)
			"crate":
				_crate(b, c, hf, F, 0.7)
				_crate(b, c + Vector2(0.0, 0.03), hf * 0.9, F + 0.7, 0.5, Color(0.5, 0.36, 0.2), 9.0)
			"barrel":
				_barrel(b, c, float(od["r"]), F, 0.95, false)
			"hatch":
				_coaming(b, c, hf, F, 0.35)
				_wood_ladder(b, c.x - 0.1, F, c.x + 0.45, F - 1.3, c.y, 4)
			"ladder_foot":
				_wood_ladder(b, c.x + 0.35, F, c.x - 0.3, F + 2.3, c.y, 6)
	# sea bags, coils, a lantern chain from a beam
	for k in 6:
		var su: float = [-6.9, -4.9, -3.0, 2.1, 4.4, 3.2][k]
		var sv: float = [-0.9, 0.95, -0.95, 0.95, -0.9, 0.9][k]
		b.cyl(ShipMesh.p(su, sv, F), 0.2, 0.34, 7, Color(0.55, 0.45, 0.3), ShipMesh.M_SACK, 0.15, false, false)
	_coil(b, 7.2, 0.75, F, 0.3, 4)
	_coil(b, -3.3, 0.9, F, 0.28, 3)
	for lp in [Vector2(-5.8, 0.0), Vector2(-0.6, 0.0), Vector2(5.5, 0.0)]:
		b.beam(ShipMesh.p(lp.x, lp.y, F + 2.1), ShipMesh.p(lp.x, lp.y, F + 1.85), 0.03, IRON_C, ShipMesh.M_IRON)
		_lantern(b, lp.x, lp.y, F + 1.65)
	_mesh_node(b, _m_sleep, _g_sleep)


func _hammock(b: ShipMesh, c: Vector2, half: Vector2, _side: int) -> void:
	var col := Color(0.78, 0.70, 0.52)
	var steps := 6
	var wv := half.y * 0.95
	var cols := 4
	for i in steps:
		var u0 := c.x - half.x + 2.0 * half.x * float(i) / float(steps)
		var u1 := c.x - half.x + 2.0 * half.x * float(i + 1) / float(steps)
		var rise0 := pow(absf(float(i) / float(steps) * 2.0 - 1.0), 2.0)
		var rise1 := pow(absf(float(i + 1) / float(steps) * 2.0 - 1.0), 2.0)
		for j in cols:
			var f0 := float(j) / float(cols) * 2.0 - 1.0
			var f1 := float(j + 1) / float(cols) * 2.0 - 1.0
			var y00 := F + 0.5 + 0.55 * rise0 - 0.2 * (1.0 - f0 * f0) * (1.0 - rise0)
			var y01 := F + 0.5 + 0.55 * rise1 - 0.2 * (1.0 - f0 * f0) * (1.0 - rise1)
			var y11 := F + 0.5 + 0.55 * rise1 - 0.2 * (1.0 - f1 * f1) * (1.0 - rise1)
			var y10 := F + 0.5 + 0.55 * rise0 - 0.2 * (1.0 - f1 * f1) * (1.0 - rise0)
			b.quad(ShipMesh.p(u0, c.y + f0 * wv, y00 + 0.0), ShipMesh.p(u1, c.y + f0 * wv, y01), ShipMesh.p(u1, c.y + f1 * wv, y11), ShipMesh.p(u0, c.y + f1 * wv, y10), col, ShipMesh.M_CLOTH, Vector3.UP)
	# the hooks at the ends and a rolled blanket
	for e in [-1.0, 1.0]:
		var eu := c.x + float(e) * (half.x + 0.05)
		b.beam(ShipMesh.p(eu, c.y, F + 1.05), ShipMesh.p(eu + float(e) * 0.1, c.y, F + 1.9), 0.04, ROPE_C, ShipMesh.M_ROPE)
		_bx(b, eu + float(e) * 0.1, c.y, F, 0.05, 0.05, 1.9, WOOD_M, ShipMesh.M_TIMBER)
	b.box(ShipMesh.p(c.x + half.x * 0.4, c.y, F + 0.62), Vector3(wv * 0.7, 0.07, 0.3), TRIM_R, ShipMesh.M_CLOTH)


func _bunk(b: ShipMesh, c: Vector2, half: Vector2) -> void:
	for sx in [-1.0, 1.0]:
		for sy in [-1.0, 1.0]:
			_bx(b, c.x + float(sx) * (half.x - 0.05), c.y + float(sy) * (half.y - 0.05), F, 0.05, 0.05, 1.7, WOOD_M, ShipMesh.M_TIMBER)
	for k in 2:
		var y := F + 0.35 + float(k) * 0.75
		_bx(b, c.x, c.y, y, half.x, half.y, 0.07, WOOD_L, ShipMesh.M_DECK)
		_bx(b, c.x, c.y, y + 0.07, half.x - 0.05, half.y - 0.05, 0.1, Color(0.72, 0.66, 0.52) if k == 0 else Color(0.5, 0.58, 0.62), ShipMesh.M_CLOTH)
		_bx(b, c.x - half.x + 0.2, c.y, y + 0.17, 0.15, half.y - 0.1, 0.07, CANVAS_C, ShipMesh.M_CLOTH)
	_bx(b, c.x + 0.25, c.y, F + 0.42, half.x - 0.5, half.y - 0.08, 0.04, TRIM_R if c.y > 0.0 else Color(0.2, 0.32, 0.4), ShipMesh.M_CLOTH)


# ---- the provisioning hold --------------------------------------------------------------------------------------------------
func _build_hold() -> void:
	var b := ShipMesh.new()
	var top := F + 1.6
	_floor(b, 2, F, Color(0.40, 0.30, 0.20))
	_hull_strip(b, 2, F - 0.2, top, false, Color(0.30, 0.19, 0.12), ShipMesh.M_HULL)
	var u := -6.4
	while u < 6.8:
		var h := Layout.hull_half(2, u) - Layout.WALL_MARGIN
		if h > 0.4:
			for s in [-1.0, 1.0]:
				_bx(b, u, float(s) * (h - 0.06), F, 0.09, 0.08, 2.2, WOOD_M, ShipMesh.M_TIMBER)
			b.beam(ShipMesh.p(u, -h, F + 2.2), ShipMesh.p(u, h, F + 2.2), 0.18, C(WOOD_D, true), ShipMesh.M_TIMBER)
		u += 1.6
	# a keelson down the middle, dunnage boards, the mast step
	_bx(b, 0.2, 0.0, F, 6.6, 0.1, 0.05, WOOD_D, ShipMesh.M_TIMBER)
	_bx(b, Layout.MAST.x, Layout.MAST.y, F, 0.65, 0.65, 0.3, WOOD_D, ShipMesh.M_TIMBER)
	b.cyl(ShipMesh.p(Layout.MAST.x, Layout.MAST.y, F + 0.3), 0.3, 2.0, 8, WOOD_M, ShipMesh.M_TIMBER, 0.3, false, false)
	for o in lay.call("obstacles", Layout.L_HOLD):
		var od: Dictionary = o
		var c: Vector2 = od["c"]
		var hf: Vector2 = od["half"]
		match str(od["style"]):
			"rack":
				_rack(b, c, hf)
			"ledger":
				_bx(b, c.x, c.y, F + 0.62, hf.x, hf.y, 0.07, WOOD_L, ShipMesh.M_DECK)
				for sx in [-1.0, 1.0]:
					for sy in [-1.0, 1.0]:
						_bx(b, c.x + float(sx) * (hf.x - 0.05), c.y + float(sy) * (hf.y - 0.05), F, 0.04, 0.04, 0.62, WOOD_M, ShipMesh.M_TIMBER)
				b.quad(ShipMesh.p(c.x - 0.2, c.y - 0.35, F + 0.7), ShipMesh.p(c.x + 0.2, c.y - 0.35, F + 0.7), ShipMesh.p(c.x + 0.2, c.y + 0.1, F + 0.7), ShipMesh.p(c.x - 0.2, c.y + 0.1, F + 0.7), Color(0.9, 0.84, 0.66), ShipMesh.M_CANVAS, Vector3.UP)
				_bx(b, c.x - 0.2, c.y - 0.35, F + 0.69, 0.02, 0.45, 0.03, Color(0.4, 0.15, 0.1), ShipMesh.M_PAINT)
				_lantern(b, c.x + 0.1, c.y + 0.5, F + 0.84)
				b.cyl(ShipMesh.p(c.x - 0.25, c.y + 0.45, F + 0.69), 0.04, 0.1, 6, Color(0.1, 0.1, 0.14), ShipMesh.M_PAINT, -1.0, false, false)
			"ladder_foot":
				_wood_ladder(b, c.x + 0.4, F, c.x - 0.2, F + 2.3, c.y, 6)
	# the hatch above: a square of light is not drawn, the beam of the hatch frame is
	_coaming(b, Layout.HOLD_HATCH, Vector2(0.7, 0.6), F + 2.2, 0.05)
	# loose sacks and a coil near the ledger, a lantern chain
	for k in 5:
		b.cyl(ShipMesh.p(-5.5 + float(k % 2) * 0.35, -0.55 + float(k) * 0.28, F), 0.22, 0.34, 7, Color(0.64, 0.52, 0.32), ShipMesh.M_SACK, 0.16, false, false)
	for lp in [Vector2(-3.0, 0.0), Vector2(3.4, 0.0), Vector2(6.0, 0.0)]:
		b.beam(ShipMesh.p(lp.x, lp.y, F + 2.2), ShipMesh.p(lp.x, lp.y, F + 1.95), 0.03, IRON_C, ShipMesh.M_IRON)
		_lantern(b, lp.x, lp.y, F + 1.75)
	_mesh_node(b, _m_hold, _g_hold)
	for z in Layout.ZONES:
		var zd: Dictionary = z
		var node := MeshInstance3D.new()
		node.material_override = _m_hold
		node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		node.custom_aabb = AABB(Vector3(-16.0, -4.0, -18.0), Vector3(32.0, 22.0, 36.0))
		_g_hold.add_child(node)
		_zones[str(zd["id"])] = node
	set_stores({})


func _rack(b: ShipMesh, c: Vector2, half: Vector2) -> void:
	var side := signf(c.y)
	var wall_v := c.y + side * (half.y - 0.04)
	_bx(b, c.x, wall_v, F, half.x, 0.04, 1.4, WOOD_D, ShipMesh.M_HULL)
	_bx(b, c.x, c.y, F + 0.78, half.x, half.y, 0.06, WOOD_L, ShipMesh.M_DECK)
	_bx(b, c.x, c.y, F + 1.38, half.x, half.y, 0.05, WOOD_L, ShipMesh.M_DECK)
	var n := int(roundf(half.x * 2.0 / 0.9)) + 1
	for k in n:
		var uu := c.x - half.x + 0.05 + (2.0 * half.x - 0.1) * float(k) / float(maxi(n - 1, 1))
		_bx(b, uu, c.y + side * (half.y - 0.06), F, 0.05, 0.05, 1.4, WOOD_M, ShipMesh.M_TIMBER)
		_bx(b, uu, c.y - side * (half.y - 0.06), F, 0.05, 0.05, 0.06, WOOD_D, ShipMesh.M_TIMBER)


## The pieces on every rack. units: {zone id: int}.
func set_stores(units: Dictionary) -> void:
	_store_units = units.duplicate()
	for z in Layout.ZONES:
		var zd: Dictionary = z
		var id := str(zd["id"])
		var n := Layout.pieces_for(id, int(units.get(id, 0)))
		var b := ShipMesh.new()
		var c := Vector2(float(zd["u"]), float(zd["side"]) * Layout.RACK_V)
		var hu := float(zd["hu"])
		for k in n:
			var col := k % 3
			var tier := floori(float(k) / 3.0)
			var pu := c.x - hu + (hu * 2.0) * (float(col) + 0.5) / 3.0
			var py := F if tier == 0 else F + 0.84
			var pc := Vector2(pu, c.y)
			var jit := float((k * 37) % 7 - 3) * 2.5
			match str(zd["piece"]):
				"sack":
					b.cyl(ShipMesh.p(pc.x, pc.y, py), 0.3, 0.5, 8, Color(0.72, 0.60, 0.40), ShipMesh.M_SACK, 0.2, false, false)
					b.cyl(ShipMesh.p(pc.x + 0.05, pc.y - 0.1, py + 0.42), 0.14, 0.14, 6, Color(0.66, 0.55, 0.36), ShipMesh.M_SACK, 0.1, false, false)
				"barrel":
					_barrel(b, pc, 0.3, py, 0.62, false, Color(0.42, 0.28, 0.15))
				"keg":
					_barrel(b, pc, 0.24, py, 0.42, false, Color(0.22, 0.2, 0.2))
					_barrel(b, pc + Vector2(0.0, 0.0), 0.2, py + 0.42, 0.3, false, Color(0.25, 0.22, 0.2))
				"plank":
					for q in 3:
						_bx(b, pc.x, pc.y, py + 0.04 + float(q) * 0.1, 0.34, 0.2, 0.08, WOOD_L if q % 2 == 0 else WOOD_M, ShipMesh.M_TIMBER, jit)
					_coil(b, pc.x, pc.y, py + 0.3, 0.2, 2)
				"crate":
					_crate(b, pc, Vector2(0.28, 0.28), py, 0.5, Color(0.56, 0.4, 0.22), jit)
				"bale":
					_crate(b, pc, Vector2(0.3, 0.3), py, 0.46, Color(0.55, 0.28, 0.20) if k % 2 == 0 else Color(0.28, 0.35, 0.5), jit)
					b.box(ShipMesh.p(pc.x, pc.y, py + 0.23), Vector3(0.31, 0.03, 0.31), ROPE_C, ShipMesh.M_ROPE)
		var node: MeshInstance3D = _zones[id]
		node.mesh = b.build() if n > 0 else null
	_stats["stores"] = int(_stats.get("stores", 0)) + 1


# ---- per frame control -----------------------------------------------------------------------------------------------------------
func set_level(level: int) -> void:
	_level = level
	_g_open.visible = level == Layout.L_DECK or level == Layout.L_NEST
	_cabin_up.visible = _g_open.visible and _cabin_fade > 0.02
	_g_sleep.visible = level == Layout.L_SLEEP
	_g_hold.visible = level == Layout.L_HOLD
	_apply_fades()


func level() -> int:
	return _level


## Ship pose: position (x east, z south, scene metres), heading, roll, pitch (degrees), heave (metres), `motion` 0..1.
func set_pose(pos: Vector2, heading_deg: float, roll_deg: float, pitch_deg: float, heave_m: float, motion: float) -> void:
	var yaw := Basis(Vector3.UP, -deg_to_rad(heading_deg))
	var tilt := Basis(Vector3.RIGHT, deg_to_rad(pitch_deg * motion)) * Basis(Vector3.BACK, -deg_to_rad(roll_deg * motion))
	root.transform = Transform3D(yaw * tilt, Vector3(pos.x, heave_m * motion, pos.y))


## Model-space point (x, y, z) to the world.
func to_world(p: Vector3) -> Vector3:
	return root.transform * p


func set_trim(deg: float) -> void:
	_boom.rotation = Vector3(0.0, deg_to_rad(deg), 0.0)
	_boom.scale = Vector3(1.0 if deg >= 0.0 else -1.0, 1.0, 1.0)


func set_rudder(r: float) -> void:
	_wheel.rotation = Vector3(0.0, 0.0, -r * 1.7)


## The fish in the barrels from the real hold: frac 0..1 of the capacity. Barrels fill one after the other.
func set_fish_fill(frac: float) -> void:
	var n := _fish.size()
	for k in n:
		var f := clampf(clampf(frac, 0.0, 1.0) * float(n) - float(k), 0.0, 1.0)
		var node := _fish[k]
		node.visible = f > 0.01
		var c: Vector2 = Layout.FISH_BARRELS[k]
		node.position = ShipMesh.p(c.x, c.y, F + 0.1 + f * 0.8)


func fish_visible_count() -> int:
	var n := 0
	for node in _fish:
		if node.visible:
			n += 1
	return n


## The pirate's place on the screen (0..1) and his distance from the camera: geometry nearer than this dissolves around him.
func set_hero_screen(uv: Vector2, dist: float, in_nest: bool) -> void:
	for m in [_m_open, _m_cabin_up, _m_sleep, _m_hold]:
		var sm: ShaderMaterial = m
		sm.set_shader_parameter("hero_uv", uv)
		sm.set_shader_parameter("hero_dist", dist)
	_m_nest.set_shader_parameter("hero_uv", Vector2(-1.0, -1.0) if in_nest else uv)
	_m_nest.set_shader_parameter("hero_dist", dist)


func set_aspect(a: float) -> void:
	for m in [_m_open, _m_nest, _m_cabin, _m_cabin_up, _m_sleep, _m_hold]:
		(m as ShaderMaterial).set_shader_parameter("aspect", a)


## 0..1: how much of the model shows (the cross-fade with the sailing sprite).
func set_alpha(a: float) -> void:
	_alpha = clampf(a, 0.0, 1.0)
	_apply_fades()


func set_cabin_open(open: bool, dt: float) -> void:
	var target := 0.0 if open else 1.0
	_cabin_fade = move_toward(_cabin_fade, target, dt * 4.0)
	_apply_fades()


func cabin_fade() -> float:
	return _cabin_fade


func _apply_fades() -> void:
	for m in [_m_open, _m_nest, _m_cabin, _m_sleep, _m_hold]:
		(m as ShaderMaterial).set_shader_parameter("fade", _alpha)
	_m_cabin_up.set_shader_parameter("fade", _alpha * _cabin_fade)
	if _cabin_up != null:
		_cabin_up.visible = _g_open.visible and _alpha * _cabin_fade > 0.02
	root.visible = _alpha > 0.01


func set_wet(w: float) -> void:
	_m_open.set_shader_parameter("wet", w)
	_m_nest.set_shader_parameter("wet", w)
