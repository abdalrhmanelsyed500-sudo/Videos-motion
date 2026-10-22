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
# VP-1A.4: the interior sheet (art/vp1/interior_px.png), ids 16..31: everything below decks is drawn too.
const M_IFLOOR := 16    ## worn interior floor planks with a foot-traffic path
const M_IHULL := 17     ## inner hull planking with drawn frames and through-bolts
const M_CEIL := 18      ## deck-head (underside) planks with nail rows and soot
const M_CWALL := 19     ## cabin panelling with moulded raised panels
const M_RUG := 20       ## woven rug (own colour)
const M_CHART := 21     ## the chart: coastline, rhumb lines, script (own colour)
const M_HAM := 22       ## hammock canvas (own colour)
const M_BLANK := 23     ## wool blanket stripes (own colour)
const M_BOOKS := 24     ## book spines with gilt bands (own colour)
const M_FOOD := 25      ## provisions: biscuit, salt fish, cheese (own colour)
const M_BOTTLE := 26    ## glass bottles (own colour)
const M_BRASS := 27     ## polished brass (own colour)
const M_TAR := 28       ## tarred wood, glossy speckle
const M_RACK := 29      ## rack boards with iron uprights
const M_ROPEMAT := 30   ## coiled rope mat (own colour)
const M_BALLAST := 31   ## ballast stones (own colour)
# VP-1A.3 authored atlas (art/vp1/ship_px.png): texel density px per ship metre per material tile, tile size and edge inset.
const PX_DENS := [48.0, 40.0, 40.0, 32.0, 64.0, 48.0, 48.0, 40.0, 40.0, 48.0, 64.0, 40.0, 48.0, 48.0, 40.0, 40.0, 44.0, 36.0, 40.0, 48.0, 64.0, 96.0, 64.0, 64.0, 96.0, 64.0, 64.0, 64.0, 32.0, 40.0, 48.0, 40.0]
const PX_TILE := 256.0
const PX_INSET := 0.0011

var _v := PackedVector3Array()
var _n := PackedVector3Array()
var _c := PackedColorArray()
var _uv := PackedVector2Array()
var _uv2 := PackedVector2Array()   ## VP-1A.3: (material id, height 0..1); UV carries the authored atlas coords
var _i := PackedInt32Array()


static func p(u: float, v: float, y: float) -> Vector3:
	return Vector3(v, y, -u)


# VP-1A.3: the authored pixel-art atlas (art/vp1/ship_px.png, tools/vp1/make_px_atlas.py): 16 seamless 256 px tiles in a 4x4
# grid, one per material, each drawn at its own texel density. Mesh UVs are PLANAR projections into a tile and wrap inside
# it (the tiles are periodic), so every surface of the ship carries drawn pixel art: planks with grain and nails, strakes,
# canvas weave, rope twist, iron plate, staves, boards.
static func px_origin(mat: int) -> Vector2:
	var loc := mat % 16   # VP-1A.4: two 4x4 sheets (ship_px / interior_px); the shader picks by id
	return Vector2(float(loc % 4) * 0.25, float(loc / 4) * 0.25)


## Atlas uv from a 2D pattern coordinate in ship metres (the caller picks the face plane).
static func px_uv2(mat: int, c: Vector2) -> Vector2:
	var d: float = PX_DENS[mat] if mat < PX_DENS.size() else 32.0
	var t := c * d
	var w := Vector2(posmod(t.x, PX_TILE), posmod(t.y, PX_TILE)) / PX_TILE
	return px_origin(mat) + Vector2(PX_INSET, PX_INSET) + w * (0.25 - 2.0 * PX_INSET)


## Atlas uv for a point on a face with normal n: floors use (x, z), walls the two in-plane axes.
static func px_uv(mat: int, pt: Vector3, n: Vector3) -> Vector2:
	var an := Vector3(absf(n.x), absf(n.y), absf(n.z))
	var c: Vector2
	if an.y > 0.7:
		c = Vector2(pt.x, pt.z)
	elif an.x > an.z:
		c = Vector2(pt.z, pt.y)
	else:
		c = Vector2(pt.x, pt.y)
	return px_uv2(mat, c)




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
	var k := 0
	for pt in [a, b, c, d]:
		_v.append(pt)
		_n.append(n)
		_c.append(col)
		_uv.append(px_uv(mat, pt, n))
		_uv2.append(Vector2(float(mat), rel0 if k < 2 else rel1))
		k += 1
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
		_uv.append(px_uv(mat, pt, n))
		_uv2.append(Vector2(float(mat), 0.5))
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
	arrays[Mesh.ARRAY_TEX_UV2] = _uv2
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
func surface(pt: Callable, rows: int, cols: int, col: Color, mat: int, uvscale_x := 8.0, uvscale_y := 8.0) -> void:
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
			_uv.append(px_uv2(mat, Vector2(float(c) / float(cols) * uvscale_x, float(r) / float(rows) * uvscale_y)))
			_uv2.append(Vector2(float(mat), float(r) / float(rows)))
	for r in rows:
		for c in cols:
			var i0 := base + r * (cols + 1) + c
			var i1 := i0 + 1
			var i2 := i0 + cols + 2
			var i3 := i0 + cols + 1
			_i.append_array(PackedInt32Array([i0, i1, i2, i0, i2, i3]))


## VP-1A.2: a quad with a colour per corner (a, b, c, d in order): soft ambient-occlusion gradients on floors and wall bases.
func quad_c(a: Vector3, b: Vector3, c: Vector3, d: Vector3, ca: Color, cb: Color, cc: Color, cd: Color, mat: int, outward := Vector3.ZERO) -> void:
	var n := (b - a).cross(d - a)
	if n.length() < 0.000001:
		n = (c - a).cross(d - a)
	n = n.normalized()
	if outward != Vector3.ZERO and n.dot(outward) < 0.0:
		n = -n
	var base := _v.size()
	var k := 0
	for pt in [a, b, c, d]:
		_v.append(pt)
		_n.append(n)
		_c.append([ca, cb, cc, cd][k])
		_uv.append(px_uv(mat, pt, n))
		_uv2.append(Vector2(float(mat), 0.5))
		k += 1
	_i.append_array(PackedInt32Array([base, base + 1, base + 2, base, base + 2, base + 3]))


## VP-1A.2: a smooth surface of revolution round `axis` starting at `base`. prof = Array of Vector2(radius, distance along the axis), base to
## tip. Smooth normals, so barrels, cannon tubes, lantern bodies and blocks shade as round things. UV.x = material + 0.4 * (angle / TAU), which
## the shader reads back as the angle round the axis (barrel staves); UV.y = distance along the axis / total (hoops).
func lathe(base: Vector3, prof: Array, segs: int, col: Color, mat: int, axis := Vector3.UP) -> void:
	var rows := prof.size()
	if rows < 2:
		return
	var f := axis.normalized()
	var up := Vector3.UP if absf(f.y) < 0.95 else Vector3.RIGHT
	var s := f.cross(up).normalized()
	var t := f.cross(s).normalized()
	var hmax := maxf(absf((prof[rows - 1] as Vector2).y - (prof[0] as Vector2).y), 0.0001)
	var h0 := (prof[0] as Vector2).y
	var base_i := _v.size()
	for r in rows:
		var pr: Vector2 = prof[r]
		var prv: Vector2 = prof[maxi(r - 1, 0)]
		var nxt: Vector2 = prof[mini(r + 1, rows - 1)]
		var nr := Vector2(nxt.y - prv.y, -(nxt.x - prv.x))
		if nr.length() < 0.00001:
			nr = Vector2(1.0, 0.0)
		nr = nr.normalized()
		for k in segs + 1:
			var a := TAU * float(k) / float(segs)
			var d := s * cos(a) + t * sin(a)
			_v.append(base + d * pr.x + f * pr.y)
			_n.append((d * nr.x + f * nr.y).normalized())
			_c.append(col)
			_uv.append(px_uv2(mat, Vector2(a * pr.x, pr.y)))
			_uv2.append(Vector2(float(mat), (pr.y - h0) / hmax))
	for r in rows - 1:
		for k in segs:
			var i0 := base_i + r * (segs + 1) + k
			_i.append_array(PackedInt32Array([i0, i0 + 1, i0 + segs + 2, i0, i0 + segs + 2, i0 + segs + 1]))
