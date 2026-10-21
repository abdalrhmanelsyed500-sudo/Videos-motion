extends RefCounted
## VP-1A.2: the detailed, reusable props of the playable ship, built with ship_mesh.gd (the same merged meshes, the same one shader): a full
## cannon on its carriage, round barrels with bulging staves and hoops, crates with corner posts, rails and a brace, lanterns with a frame,
## pulley blocks, deadeyes with chain plates, belaying-pin rails, an anchor, rope knots and cannon balls. Variation comes from the arguments
## (colour, size, yaw, wear), never from copying one model N times. Pure geometry: no nodes, no textures. Model space: x starboard, y up,
## -z toward the bow; (u, v) are ship-local like ShipMesh.p().
const ShipMesh := preload("res://h2d/ship_mesh.gd")
const Layout := preload("res://h2d/ship_layout.gd")

const F := Layout.FLOOR_Y
const WOOD_D := Color(0.29, 0.157, 0.078)
const WOOD_M := Color(0.427, 0.251, 0.1255)
const WOOD_L := Color(0.58, 0.404, 0.18)
const IRON_C := Color(0.23, 0.24, 0.27)
const BRASS := Color(0.72, 0.55, 0.2)
const ROPE_C := Color(0.71, 0.58, 0.36)
const LAMP_C := Color(1.0, 0.80, 0.42)


static func p(u: float, v: float, y: float) -> Vector3:
	return ShipMesh.p(u, v, y)


static func bx(b: ShipMesh, u: float, v: float, y0: float, hu: float, hv: float, h: float, col: Color, mat: int, yaw := 0.0) -> void:
	b.box(p(u, v, y0 + h * 0.5), Vector3(hv, h * 0.5, hu), col, mat, yaw)


## A small ball (cannon shot, a knot, a rope end) at c.
static func ball(b: ShipMesh, c: Vector3, r: float, col: Color, mat: int) -> void:
	var prof: Array = []
	for k in 7:
		var a := PI * float(k) / 6.0
		prof.append(Vector2(sin(a) * r, -cos(a) * r))
	b.lathe(c - Vector3(0.0, r, 0.0) + Vector3(0.0, r, 0.0), prof, 6, col, mat)


## An upright barrel: bulging staves, three raised iron hoops, a lid (closed) or an open top. h = height, r = radius at the belly.
static func barrel(b: ShipMesh, c: Vector2, r: float, y: float, h: float, open: bool, col: Color, wear := 0.0) -> void:
	var prof: Array = []
	var n := 16
	for k in n + 1:
		var t := float(k) / float(n)
		var rad := r * (0.84 + 0.16 * (1.0 - pow(2.0 * t - 1.0, 2.0)))
		if k == 2 or k == 8 or k == 14:
			rad += 0.014
		prof.append(Vector2(rad, t * h))
	b.lathe(p(c.x, c.y, y), prof, 12, col.darkened(wear * 0.25), ShipMesh.M_BARREL)
	if not open:
		b.cyl(p(c.x, c.y, y + h - 0.02), r * 0.84, 0.04, 12, col.lightened(0.18), ShipMesh.M_TIMBER, r * 0.82, false, false)
		# a bung and a rope handle on the lid
		b.cyl(p(c.x + r * 0.35, c.y, y + h + 0.02), 0.035, 0.03, 6, WOOD_D, ShipMesh.M_TIMBER, 0.03, false, false)


## A crate with a frame: four corner posts, top and bottom rails and a diagonal brace on one face. half = (u, v) half sizes.
static func crate(b: ShipMesh, c: Vector2, half: Vector2, y: float, h: float, col: Color, yaw := 0.0, brace_side := 1.0) -> void:
	var bs := Basis(Vector3.UP, deg_to_rad(yaw))
	var cen := p(c.x, c.y, y)
	var hx := half.y
	var hz := half.x
	b.box(cen + Vector3(0.0, h * 0.5, 0.0), Vector3(hx, h * 0.5, hz), col, ShipMesh.M_CRATE, yaw)
	var post := col.darkened(0.32)
	for sx in [-1.0, 1.0]:
		for sz in [-1.0, 1.0]:
			b.box(cen + bs * Vector3(float(sx) * (hx - 0.005), h * 0.5, float(sz) * (hz - 0.005)), Vector3(0.05, h * 0.5 + 0.01, 0.05), post, ShipMesh.M_TIMBER, yaw)
	for yy in [0.07, h - 0.07]:
		for sz in [-1.0, 1.0]:
			b.box(cen + bs * Vector3(0.0, float(yy), float(sz) * (hz + 0.012)), Vector3(hx - 0.02, 0.035, 0.018), post, ShipMesh.M_TIMBER, yaw)
		for sx in [-1.0, 1.0]:
			b.box(cen + bs * Vector3(float(sx) * (hx + 0.012), float(yy), 0.0), Vector3(0.018, 0.035, hz - 0.02), post, ShipMesh.M_TIMBER, yaw)
	var sxb := brace_side
	b.beam(cen + bs * Vector3(sxb * (hx + 0.016), 0.08, -hz + 0.06), cen + bs * Vector3(sxb * (hx + 0.016), h - 0.08, hz - 0.06), 0.04, post, ShipMesh.M_TIMBER)
	# an iron corner plate and nail heads
	b.box(cen + bs * Vector3(hx + 0.02, h - 0.1, hz - 0.1), Vector3(0.01, 0.07, 0.07), IRON_C, ShipMesh.M_IRON, yaw)


## A lantern hung at (u, v, y) = its centre: a glass body that glows, an iron cap, base, four bars, a ring handle.
static func lantern(b: ShipMesh, u: float, v: float, y: float) -> void:
	var glass: Array = [Vector2(0.06, -0.12), Vector2(0.085, -0.07), Vector2(0.095, 0.0), Vector2(0.085, 0.08), Vector2(0.07, 0.13)]
	b.lathe(p(u, v, y), glass, 8, LAMP_C, ShipMesh.M_LAMP)
	var cap: Array = [Vector2(0.12, 0.12), Vector2(0.13, 0.14), Vector2(0.08, 0.2), Vector2(0.03, 0.25), Vector2(0.0, 0.26)]
	b.lathe(p(u, v, y), cap, 8, IRON_C, ShipMesh.M_IRON)
	var base: Array = [Vector2(0.0, -0.17), Vector2(0.1, -0.17), Vector2(0.12, -0.13), Vector2(0.1, -0.11)]
	b.lathe(p(u, v, y), base, 8, IRON_C, ShipMesh.M_IRON)
	for k in 4:
		var a := TAU * (float(k) + 0.5) / 4.0
		var dx := cos(a) * 0.1
		var dz := sin(a) * 0.1
		b.beam(p(u, v, y) + Vector3(dx, -0.12, dz), p(u, v, y) + Vector3(dx, 0.13, dz), 0.016, IRON_C, ShipMesh.M_IRON)
	b.ring(p(u, v, y + 0.31), Vector3.RIGHT, Vector3.UP, 0.055, 6, 0.014, IRON_C, ShipMesh.M_IRON)


## A pulley block: a wooden shell, an iron strap, a sheave and a hook, hanging at c (centre), strap axis along ax.
static func block(b: ShipMesh, c: Vector3, ax := Vector3.RIGHT, size := 1.0) -> void:
	b.box(c, Vector3(0.05, 0.09, 0.06) * size, WOOD_D, ShipMesh.M_TIMBER)
	b.tube(c - ax * 0.07 * size, c + ax * 0.07 * size, 0.045 * size, 8, IRON_C, ShipMesh.M_IRON)
	b.ring(c, Vector3.BACK, Vector3.UP, 0.1 * size, 8, 0.016 * size, IRON_C, ShipMesh.M_IRON)
	b.tube(c + Vector3(0.0, -0.1, 0.0) * size, c + Vector3(0.0, -0.16, 0.0) * size, 0.02 * size, 5, IRON_C, ShipMesh.M_IRON)


## A deadeye (wooden disc with a rope groove) on a chain plate that runs down the hull side. side = +-1 for the rail at (u, v).
static func deadeye(b: ShipMesh, u: float, v: float, y: float) -> void:
	var disc: Array = [Vector2(0.0, 0.0), Vector2(0.1, 0.0), Vector2(0.105, 0.02), Vector2(0.1, 0.04), Vector2(0.0, 0.04)]
	b.lathe(p(u, v, y), disc, 8, WOOD_D, ShipMesh.M_TIMBER)
	b.ring(p(u, v, y + 0.02), Vector3.RIGHT, Vector3.BACK, 0.1, 8, 0.02, ROPE_C.darkened(0.1), ShipMesh.M_ROPE)
	b.beam(p(u, v, y - 0.02), p(u, v, y - 0.3), 0.03, IRON_C, ShipMesh.M_IRON)


## A belaying-pin rail along the bulwark: a timber with turned pins and a rope hung over two of them.
static func pin_rail(b: ShipMesh, u0: float, u1: float, v: float, y: float, inward: float) -> void:
	b.beam(p(u0, v, y), p(u1, v, y), 0.09, WOOD_M, ShipMesh.M_TIMBER)
	var n := int(floorf((u1 - u0) / 0.28))
	for k in n + 1:
		var uu := u0 + 0.14 + float(k) * 0.28
		if uu > u1 - 0.1:
			break
		var pin: Array = [Vector2(0.025, 0.0), Vector2(0.018, 0.08), Vector2(0.03, 0.14), Vector2(0.022, 0.2)]
		b.lathe(p(uu, v + inward * 0.03, y), pin, 5, WOOD_L, ShipMesh.M_TIMBER)
	var um := (u0 + u1) * 0.5
	b.ring(p(um, v + inward * 0.09, y - 0.1), Vector3.BACK, Vector3.UP, 0.12, 8, 0.03, ROPE_C, ShipMesh.M_ROPE)


## A small knot / rope seizing: a short fat bead of rope at c.
static func knot(b: ShipMesh, c: Vector3, r := 0.04) -> void:
	b.box(c, Vector3(r, r, r), ROPE_C.darkened(0.1), ShipMesh.M_ROPE)


## The anchor hung on the outside of the port bow at (u, v): shank, stock, arms with flukes, ring and a cable.
static func anchor(b: ShipMesh, u: float, v: float, y_top: float) -> void:
	var y_bot := y_top - 1.35
	b.beam(p(u, v, y_top), p(u, v, y_bot), 0.09, IRON_C, ShipMesh.M_IRON)
	b.beam(p(u - 0.5, v, y_top - 0.18), p(u + 0.5, v, y_top - 0.18), 0.075, WOOD_D, ShipMesh.M_TIMBER)
	b.ring(p(u, v, y_top + 0.12), Vector3.BACK, Vector3.UP, 0.12, 8, 0.045, IRON_C, ShipMesh.M_IRON)
	for s in [-1.0, 1.0]:
		var sd := float(s)
		b.beam(p(u + sd * 0.0, v, y_bot + 0.04), p(u + sd * 0.55, v, y_bot + 0.42), 0.08, IRON_C, ShipMesh.M_IRON)
		b.tri(p(u + sd * 0.55, v - 0.05, y_bot + 0.55), p(u + sd * 0.55, v + 0.05, y_bot + 0.55), p(u + sd * 0.7, v, y_bot + 0.32), IRON_C, ShipMesh.M_IRON)
		b.tri(p(u + sd * 0.4, v - 0.05, y_bot + 0.3), p(u + sd * 0.4, v + 0.05, y_bot + 0.3), p(u + sd * 0.7, v, y_bot + 0.32), IRON_C.lightened(0.1), ShipMesh.M_IRON)
	b.cyl(p(u, v, y_bot - 0.03), 0.06, 0.08, 6, IRON_C, ShipMesh.M_IRON, 0.03, false, true)


## One cannon on a carriage against the bulwark at u, firing out of a gun port on `side` (-1 port, +1 starboard).
static func cannon(b: ShipMesh, u: float, side: float) -> void:
	var hh := Layout.hull_half(0, u)
	var y := F + 0.4
	# the tube: breech knob, base ring, reinforce, chase with mouldings, muzzle swell and lip (iron, with a brass ring)
	var prof: Array = [Vector2(0.0, -0.14), Vector2(0.05, -0.13), Vector2(0.07, -0.07), Vector2(0.05, -0.02), Vector2(0.11, 0.0), Vector2(0.18, 0.06),
			Vector2(0.2, 0.14), Vector2(0.2, 0.34), Vector2(0.17, 0.38), Vector2(0.17, 0.44), Vector2(0.155, 0.5), Vector2(0.14, 0.9),
			Vector2(0.13, 1.2), Vector2(0.15, 1.24), Vector2(0.17, 1.3), Vector2(0.17, 1.38), Vector2(0.14, 1.42), Vector2(0.1, 1.44)]
	var v_start := side * (hh - 1.2)
	b.lathe(p(u, v_start, y), prof, 10, IRON_C, ShipMesh.M_IRON, Vector3(side, 0.0, 0.0))
	# a brass band on the reinforce and a touch-hole
	b.lathe(p(u, v_start + side * 0.3, y), [Vector2(0.205, 0.0), Vector2(0.21, 0.02), Vector2(0.205, 0.05)], 10, BRASS, ShipMesh.M_IRON, Vector3(side, 0.0, 0.0))
	# trunnions through the cheeks
	b.tube(p(u - 0.36, v_start + side * 0.52, y), p(u + 0.36, v_start + side * 0.52, y), 0.05, 6, IRON_C, ShipMesh.M_IRON)
	# the carriage: two cheeks that step down towards the breech, a bed, a quoin wedge, an axle and four trucks
	for e in [-1.0, 1.0]:
		var uu := u + float(e) * 0.27
		bx(b, uu, side * (hh - 0.55), F + 0.14, 0.06, 0.2, 0.34, WOOD_D, ShipMesh.M_TIMBER)
		bx(b, uu, side * (hh - 0.95), F + 0.14, 0.06, 0.2, 0.24, WOOD_D, ShipMesh.M_TIMBER)
		bx(b, uu, side * (hh - 1.1), F + 0.14, 0.06, 0.12, 0.14, WOOD_D, ShipMesh.M_TIMBER)
		# front trucks (bigger) and rear trucks
		b.tube(p(uu + float(e) * 0.09, side * (hh - 0.4), F + 0.14), p(uu + float(e) * 0.01, side * (hh - 0.4), F + 0.14), 0.14, 8, WOOD_M, ShipMesh.M_TIMBER)
		b.tube(p(uu + float(e) * 0.09, side * (hh - 1.02), F + 0.1), p(uu + float(e) * 0.01, side * (hh - 1.02), F + 0.1), 0.1, 8, WOOD_M, ShipMesh.M_TIMBER)
		b.tube(p(uu + float(e) * 0.11, side * (hh - 0.4), F + 0.14), p(uu + float(e) * 0.09, side * (hh - 0.4), F + 0.14), 0.045, 6, IRON_C, ShipMesh.M_IRON)
	b.tube(p(u - 0.3, side * (hh - 0.4), F + 0.14), p(u + 0.3, side * (hh - 0.4), F + 0.14), 0.03, 5, IRON_C, ShipMesh.M_IRON)
	b.tube(p(u - 0.3, side * (hh - 1.02), F + 0.1), p(u + 0.3, side * (hh - 1.02), F + 0.1), 0.03, 5, IRON_C, ShipMesh.M_IRON)
	bx(b, u, side * (hh - 0.95), F + 0.04, 0.2, 0.1, 0.1, WOOD_M, ShipMesh.M_TIMBER)
	b.tri(p(u - 0.18, side * (hh - 1.18), F + 0.2), p(u + 0.18, side * (hh - 1.18), F + 0.2), p(u, side * (hh - 1.0), F + 0.2), WOOD_L, ShipMesh.M_TIMBER, Vector3.UP)
	# breeching rope looped from the cascabel to two ring bolts in the bulwark
	var cas := p(u, v_start - side * 0.1, y)
	for e in [-1.0, 1.0]:
		var rb := p(u + float(e) * 0.42, side * (hh - 0.32), y - 0.02)
		b.beam(cas, rb, 0.035, ROPE_C, ShipMesh.M_ROPE)
		b.box(rb, Vector3(0.03, 0.04, 0.03), IRON_C, ShipMesh.M_IRON)
	# a small pyramid of shot beside it
	var bc := p(u + 0.55, side * (hh - 0.75), F)
	for q in [Vector3(0.0, 0.07, 0.0), Vector3(0.14, 0.07, 0.0), Vector3(0.07, 0.07, 0.12), Vector3(0.07, 0.19, 0.04)]:
		ball(b, bc + (q as Vector3), 0.07, Color(0.14, 0.14, 0.16), ShipMesh.M_IRON)
