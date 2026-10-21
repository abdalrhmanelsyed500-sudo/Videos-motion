extends RefCounted
## CP-2 Release A: a tiny procedural mesh builder for the ship's interior and deck (ship_deck_view.gd). Everything is flat-shaded
## boxes, prisms, cylinders and quads merged into ONE ArrayMesh per part, so the whole ship is a handful of draw calls (the dev PC
## is an Intel HD 3000: no per-object nodes, no real-time lights, no transparency).
## Vertex data: position (model space: x starboard, y up, -z toward the bow), normal (flat), COLOR = tint (rgb) + see-through flag
## (a = 1 normal, a = 0.5 dissolves in a hole around the pirate: sails, rigging, the nest seen from below), UV.x = material id for
## ship_deck.gdshader, UV.y = height up the object 0..1 (hoops on barrels). No textures: the shader paints the planks, canvas, rope.
## Pure geometry, no nodes: tests/test_ship_view.gd checks the counts and bounds. NOT YET RUN ON THE USER'S PC.
const M_DECK := 0
const M_HULL := 1
const M_TIMBER := 2
const M_BARREL := 3
const M_CANVAS := 4
const M_ROPE := 5
const M_FISH := 6
const M_IRON := 7
const M_PAINT := 8
const M_CRATE := 9
const M_SACK := 10
const M_CLOTH := 11
const M_LAMP := 12
const M_VOID := 13
const M_NET := 14       ## VP-1A: fishing net: a cut-out diamond lattice (holes are really see-through)

var _v := PackedVector3Array()
var _n := PackedVector3Array()
var _c := PackedColorArray()
var _uv := PackedVector2Array()
var _i := PackedInt32Array()


static func p(u: float, v: float, y: float) -> Vector3:
	return Vector3(v, y, -u)


func vertex_count() -> int:
	return _v.size()


func is_empty() -> bool:
	return _v.is_empty()


## One quad a-b-c-d (any winding); `outward` says which side the flat normal should face (zero = as computed).
func quad(a: Vector3, b: Vector3, c: Vector3, d: Vector3, col: Color, mat: int, outward := Vector3.ZERO, rel0 := 0.0, rel1 := 1.0) -> void:
	var n := (b - a).cross(d - a)
	if n.length() < 0.000001:
		n = (c - a).cross(d - a)
	n = n.normalized()
	if outward != Vector3.ZERO and n.dot(outward) < 0.0:
		n = -n
	var base := _v.size()
	for pt in [a, b, c, d]:
		_v.append(pt)
		_n.append(n)
		_c.append(col)
	_uv.append(Vector2(float(mat), rel0))
	_uv.append(Vector2(float(mat), rel0))
	_uv.append(Vector2(float(mat), rel1))
	_uv.append(Vector2(float(mat), rel1))
	_i.append_array(PackedInt32Array([base, base + 1, base + 2, base, base + 2, base + 3]))


func tri(a: Vector3, b: Vector3, c: Vector3, col: Color, mat: int, outward := Vector3.ZERO) -> void:
	var n := (b - a).cross(c - a).normalized()
	if outward != Vector3.ZERO and n.dot(outward) < 0.0:
		n = -n
	var base := _v.size()
	for pt in [a, b, c]:
		_v.append(pt)
		_n.append(n)
		_c.append(col)
		_uv.append(Vector2(float(mat), 0.5))
	_i.append_array(PackedInt32Array([base, base + 1, base + 2]))


## A box. center in model space, half = (half x, half y, half z), yaw about the vertical axis. The bottom face is skipped.
func box(center: Vector3, half: Vector3, col: Color, mat: int, yaw_deg := 0.0, with_bottom := false) -> void:
	var bs := Basis(Vector3.UP, deg_to_rad(yaw_deg))
	var cs: Array[Vector3] = []
	for sx in [-1.0, 1.0]:
		for sy in [-1.0, 1.0]:
			for sz in [-1.0, 1.0]:
				cs.append(center + bs * Vector3(half.x * float(sx), half.y * float(sy), half.z * float(sz)))
	# index = (sx<0?0:4) + (sy<0?0:2) + (sz<0?0:1)
	var top_rel := 1.0
	var faces := [
		[[4, 5, 7, 6], Vector3.RIGHT, 0.0, top_rel], [[0, 1, 3, 2], Vector3.LEFT, 0.0, top_rel],
		[[2, 3, 7, 6], Vector3.UP, 1.0, 1.0], [[1, 5, 7, 3], Vector3.BACK, 0.0, top_rel],
		[[0, 4, 6, 2], Vector3.FORWARD, 0.0, top_rel],
	]
	for f in faces:
		var idx: Array = f[0]
		var out: Vector3 = bs * (f[1] as Vector3)
		var q0 := float(f[2])
		var q1 := float(f[3])
		# side faces: bottom vertices rel 0, top rel 1
		var a: Vector3 = cs[idx[0]]
		var b: Vector3 = cs[idx[1]]
		var c: Vector3 = cs[idx[2]]
		var d: Vector3 = cs[idx[3]]
		quad(a, b, c, d, col, mat, out, q0, q1)
	if with_bottom:
		quad(cs[0], cs[1], cs[5], cs[4], col, mat, bs * Vector3.DOWN)


## A cylinder (or cone frustum) standing on `base` (centre of the bottom), `segs` sides. `open_top` leaves the top uncapped (barrel).
func cyl(base: Vector3, r: float, h: float, segs: int, col: Color, mat: int, r_top := -1.0, open_top := false, cap_bottom := true) -> void:
	var rt := r if r_top < 0.0 else r_top
	var top := base + Vector3(0.0, h, 0.0)
	for k in segs:
		var a0 := TAU * float(k) / float(segs)
		var a1 := TAU * float(k + 1) / float(segs)
		var d0 := Vector3(cos(a0), 0.0, sin(a0))
		var d1 := Vector3(cos(a1), 0.0, sin(a1))
		var mid := ((d0 + d1) * 0.5).normalized()
		quad(base + d0 * r, base + d1 * r, top + d1 * rt, top + d0 * rt, col, mat, mid, 0.0, 1.0)
		if not open_top:
			tri(top, top + d0 * rt, top + d1 * rt, col, mat, Vector3.UP)
		if cap_bottom:
			tri(base, base + d1 * r, base + d0 * r, col, mat, Vector3.DOWN)


## A square prism from a to b (thick = side length): ropes, spars, rails, ratlines.
func beam(a: Vector3, b: Vector3, thick: float, col: Color, mat: int) -> void:
	var dir := b - a
	if dir.length() < 0.001:
		return
	var f := dir.normalized()
	var up := Vector3.UP if absf(f.y) < 0.95 else Vector3.RIGHT
	var s := f.cross(up).normalized() * (thick * 0.5)
	var t := f.cross(s).normalized() * (thick * 0.5)
	var o: Array[Vector3] = [s + t, s - t, -s - t, -s + t]
	for k in 4:
		var k2 := (k + 1) % 4
		var mid := (o[k] + o[k2]).normalized()
		quad(a + o[k], a + o[k2], b + o[k2], b + o[k], col, mat, mid, 0.0, 1.0)
	quad(a + o[0], a + o[1], a + o[2], a + o[3], col, mat, -f)
	quad(b + o[0], b + o[1], b + o[2], b + o[3], col, mat, f)


## A cylinder lying along the axis a -> b (a winch drum, a spar, a rope): radius r, `segs` sides, optional end caps.
func tube(a: Vector3, b: Vector3, r: float, segs: int, col: Color, mat: int, caps := true) -> void:
	var dir := b - a
	if dir.length() < 0.001:
		return
	var f := dir.normalized()
	var up := Vector3.UP if absf(f.y) < 0.95 else Vector3.RIGHT
	var s := f.cross(up).normalized()
	var t := f.cross(s).normalized()
	for k in segs:
		var a0 := TAU * float(k) / float(segs)
		var a1 := TAU * float(k + 1) / float(segs)
		var o0 := (s * cos(a0) + t * sin(a0)) * r
		var o1 := (s * cos(a1) + t * sin(a1)) * r
		var mid := (o0 + o1).normalized()
		quad(a + o0, a + o1, b + o1, b + o0, col, mat, mid, 0.0, 1.0)
		if caps:
			tri(a, a + o1, a + o0, col, mat, -f)
			tri(b, b + o0, b + o1, col, mat, f)


## A ring of beams (the wheel's rim, a coil of rope): centre c, radius r, in the plane spanned by ax1 and ax2.
func ring(c: Vector3, ax1: Vector3, ax2: Vector3, r: float, segs: int, thick: float, col: Color, mat: int) -> void:
	for k in segs:
		var a0 := TAU * float(k) / float(segs)
		var a1 := TAU * float(k + 1) / float(segs)
		beam(c + (ax1 * cos(a0) + ax2 * sin(a0)) * r, c + (ax1 * cos(a1) + ax2 * sin(a1)) * r, thick, col, mat)


func build() -> ArrayMesh:
	var mesh := ArrayMesh.new()
	if _v.is_empty():
		return mesh
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = _v
	arrays[Mesh.ARRAY_NORMAL] = _n
	arrays[Mesh.ARRAY_COLOR] = _c
	arrays[Mesh.ARRAY_TEX_UV] = _uv
	arrays[Mesh.ARRAY_INDEX] = _i
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh


## Bounds of everything added so far.
func bounds() -> AABB:
	if _v.is_empty():
		return AABB()
	var lo := _v[0]
	var hi := _v[0]
	for pt in _v:
		lo = Vector3(minf(lo.x, pt.x), minf(lo.y, pt.y), minf(lo.z, pt.z))
		hi = Vector3(maxf(hi.x, pt.x), maxf(hi.y, pt.y), maxf(hi.z, pt.z))
	return AABB(lo, hi - lo)

## VP-1A: a smooth parametric surface (sails): `pt` is a Callable(t, s) -> Vector3 over [0,1]x[0,1]; the normals are averaged over the grid,
## so cloth shades as one curved piece instead of 36 flat facets.
func surface(pt: Callable, rows: int, cols: int, col: Color, mat: int) -> void:
	var pts: Array = []
	for r in rows + 1:
		var row: Array = []
		for c in cols + 1:
			row.append(pt.call(float(r) / float(rows), float(c) / float(cols)))
		pts.append(row)
	var base := _v.size()
	for r in rows + 1:
		for c in cols + 1:
			var p0: Vector3 = (pts[r] as Array)[c]
			var pr: Vector3 = (pts[mini(r + 1, rows)] as Array)[c] - (pts[maxi(r - 1, 0)] as Array)[c]
			var pc: Vector3 = (pts[r] as Array)[mini(c + 1, cols)] - (pts[r] as Array)[maxi(c - 1, 0)]
			var n := pc.cross(pr)
			if n.length() < 0.000001:
				n = Vector3.RIGHT
			_v.append(p0)
			_n.append(n.normalized())
			_c.append(col)
			_uv.append(Vector2(float(mat), float(r) / float(rows)))
	for r in rows:
		for c in cols:
			var i0 := base + r * (cols + 1) + c
			var i1 := i0 + 1
			var i2 := i0 + cols + 2
			var i3 := i0 + cols + 1
			_i.append_array(PackedInt32Array([i0, i1, i2, i0, i2, i3]))
