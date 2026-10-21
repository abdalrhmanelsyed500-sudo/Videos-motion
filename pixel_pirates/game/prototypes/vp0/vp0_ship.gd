extends RefCounted
## VP-0 ship builder: the 24 px/m deck-tier ship, assembled from REAL assets only:
##   hull / deck / cabin / sails = a few textured, cel-lit meshes (pixel-art tiles, nearest) shaped from ship_layout.gd's HULL table;
##   mast with crow's nest, helm, winch, hatch, barrels, crates, cannons, lantern, pirate = baked voxel sprites (art/vp0/ship).
## Props sit at the game's real layout positions (ship_layout.gd constants) so the walkable geometry and interaction points do not change.
## Local axes: x = u (bow +), z = v (starboard +), y up.

const U := preload("res://prototypes/vp0/vp0_util.gd")
const L := preload("res://h2d/ship_layout.gd")

const F := 1.2           # deck height above the water (L.FLOOR_Y)
const RAIL := 0.95       # bulwark height above the deck


static func build(stage, parent: Node3D, yaw_deg: float, sails := true, props := true) -> Node3D:
	var ship := Node3D.new()
	ship.name = "Ship"
	ship.rotation_degrees.y = yaw_deg
	parent.add_child(ship)
	_hull(stage, ship)
	if sails:
		_rig(stage, ship)
	if props:
		_props(stage, ship, yaw_deg)
	return ship


static func _tex(n: String) -> Texture2D:
	return U.tex(U.ART + "ground/" + n + ".png")


static func _hull(stage, ship: Node3D) -> void:
	var hull := U.MeshBuilder.new()      # strakes
	var deck := U.MeshBuilder.new()      # deck planks
	var cap := U.MeshBuilder.new()       # rail cap (pale)
	var us: Array = []
	var u := -11.0
	while u <= 11.001:
		us.append(u)
		u += 0.5
	for i in us.size() - 1:
		var u0: float = us[i]
		var u1: float = us[i + 1]
		var h0 := L.hull_half(0, u0)
		var h1 := L.hull_half(0, u1)
		for side in [1.0, -1.0]:
			var s: float = side
			var k0 := h0 * 0.62
			var k1 := h1 * 0.62
			# keel -> deck line (flared hull), deck line -> rail top
			if s > 0.0:
				hull.quad(Vector3(u0, 0.0, s * k0), Vector3(u1, 0.0, s * k1), Vector3(u1, F, s * h1), Vector3(u0, F, s * h0), Vector2(u0 * 0.5, 0.0), Vector2(u1 * 0.5, 0.0), Vector2(u1 * 0.5, 0.6), Vector2(u0 * 0.5, 0.6))
				hull.quad(Vector3(u0, F, s * h0), Vector3(u1, F, s * h1), Vector3(u1, F + RAIL, s * h1), Vector3(u0, F + RAIL, s * h0), Vector2(u0 * 0.5, 0.6), Vector2(u1 * 0.5, 0.6), Vector2(u1 * 0.5, 1.0), Vector2(u0 * 0.5, 1.0))
				cap.quad(Vector3(u0, F + RAIL, s * h0), Vector3(u1, F + RAIL, s * h1), Vector3(u1, F + RAIL, s * (h1 - 0.3)), Vector3(u0, F + RAIL, s * (h0 - 0.3)), Vector2(u0 * 0.5, 0.0), Vector2(u1 * 0.5, 0.0), Vector2(u1 * 0.5, 0.15), Vector2(u0 * 0.5, 0.15))
			else:
				hull.quad(Vector3(u1, 0.0, s * k1), Vector3(u0, 0.0, s * k0), Vector3(u0, F, s * h0), Vector3(u1, F, s * h1), Vector2(u1 * 0.5, 0.0), Vector2(u0 * 0.5, 0.0), Vector2(u0 * 0.5, 0.6), Vector2(u1 * 0.5, 0.6))
				hull.quad(Vector3(u1, F, s * h1), Vector3(u0, F, s * h0), Vector3(u0, F + RAIL, s * h0), Vector3(u1, F + RAIL, s * h1), Vector2(u1 * 0.5, 0.6), Vector2(u0 * 0.5, 0.6), Vector2(u0 * 0.5, 1.0), Vector2(u1 * 0.5, 1.0))
				cap.quad(Vector3(u1, F + RAIL, s * h1), Vector3(u0, F + RAIL, s * h0), Vector3(u0, F + RAIL, s * (h0 - 0.3)), Vector3(u1, F + RAIL, s * (h1 - 0.3)), Vector2(u1 * 0.5, 0.0), Vector2(u0 * 0.5, 0.0), Vector2(u0 * 0.5, 0.15), Vector2(u1 * 0.5, 0.15))
		deck.quad(Vector3(u0, F, h0 - 0.3), Vector3(u1, F, h1 - 0.3), Vector3(u1, F, -(h1 - 0.3)), Vector3(u0, F, -(h0 - 0.3)), Vector2(u0 / 2.0, (h0 - 0.3) / 2.0), Vector2(u1 / 2.0, (h1 - 0.3) / 2.0), Vector2(u1 / 2.0, -(h1 - 0.3) / 2.0), Vector2(u0 / 2.0, -(h0 - 0.3) / 2.0))
	# transom
	hull.quad(Vector3(-11, 0, 1.2), Vector3(-11, 0, -1.2), Vector3(-11, F + RAIL, -1.9), Vector3(-11, F + RAIL, 1.9), Vector2(0.0, 0.0), Vector2(1.2, 0.0), Vector2(1.5, 1.0), Vector2(-0.3, 1.0))
	var hm: ShaderMaterial = stage.make_cel(_tex("hull_strakes"))
	var dm: ShaderMaterial = stage.make_cel(_tex("deck_planks"))
	var cm: ShaderMaterial = stage.make_cel(_tex("deck_planks"), Color(1.1, 1.05, 0.95))
	for pair in [[hull, hm], [deck, dm], [cap, cm]]:
		var mi := MeshInstance3D.new()
		mi.mesh = (pair[0] as U.MeshBuilder).build()
		mi.material_override = pair[1] as Material
		mi.extra_cull_margin = 30.0
		ship.add_child(mi)


static func _cabin(stage, ship: Node3D) -> void:
	var b := U.MeshBuilder.new()
	var u0 := L.CABIN_U0
	var u1 := L.CABIN_U1
	var v := L.CABIN_V
	var h := 2.4
	var y0 := F
	var y1 := F + h
	# four walls + roof (outward normals not needed: the cel shader faces the normal toward the camera)
	b.quad(Vector3(u1, y0, -v), Vector3(u1, y0, v), Vector3(u1, y1, v), Vector3(u1, y1, -v), Vector2(0, 0), Vector2(v, 0), Vector2(v, 1.2), Vector2(0, 1.2))
	b.quad(Vector3(u0, y0, -v), Vector3(u0, y0, v), Vector3(u0, y1, v), Vector3(u0, y1, -v), Vector2(0, 0), Vector2(v, 0), Vector2(v, 1.2), Vector2(0, 1.2))
	b.quad(Vector3(u0, y0, v), Vector3(u1, y0, v), Vector3(u1, y1, v), Vector3(u0, y1, v), Vector2(0, 0), Vector2(2.3, 0), Vector2(2.3, 1.2), Vector2(0, 1.2))
	b.quad(Vector3(u0, y0, -v), Vector3(u1, y0, -v), Vector3(u1, y1, -v), Vector3(u0, y1, -v), Vector2(0, 0), Vector2(2.3, 0), Vector2(2.3, 1.2), Vector2(0, 1.2))
	b.quad(Vector3(u0 - 0.15, y1, -v - 0.15), Vector3(u1 + 0.15, y1, -v - 0.15), Vector3(u1 + 0.15, y1, v + 0.15), Vector3(u0 - 0.15, y1, v + 0.15), Vector2(0, 0), Vector2(2.4, 0), Vector2(2.4, 2.4), Vector2(0, 2.4))
	var mi := MeshInstance3D.new()
	mi.mesh = b.build()
	mi.material_override = stage.make_cel(_tex("deck_planks_dark"), Color(1.0, 0.95, 0.9))
	mi.extra_cull_margin = 30.0
	ship.add_child(mi)
	# the door (front wall, v -2.0 .. -0.6) and the stern windows: flat dark / glowing quads
	var d := U.MeshBuilder.new()
	d.quad(Vector3(u1 + 0.02, y0, L.DOOR_V0), Vector3(u1 + 0.02, y0, L.DOOR_V1), Vector3(u1 + 0.02, y0 + 1.9, L.DOOR_V1), Vector3(u1 + 0.02, y0 + 1.9, L.DOOR_V0), Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1))
	var dm := U.MeshBuilder.new()
	for wv in []:
		dm.quad(Vector3(u1 + 0.02, y0 + 0.9, wv - 0.35), Vector3(u1 + 0.02, y0 + 0.9, wv + 0.35), Vector3(u1 + 0.02, y0 + 1.7, wv + 0.35), Vector3(u1 + 0.02, y0 + 1.7, wv - 0.35), Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1))
	# stern-cabin windows on the visible (starboard) wall: dark frame + glass that follows the look (day: sky glass, night: lamp light)
	var fr := U.MeshBuilder.new()
	var gl := U.MeshBuilder.new()
	for wu in [-9.1, -7.7, -6.3]:
		var wx: float = wu
		fr.quad(Vector3(wx - 0.42, y0 + 0.95, v + 0.07), Vector3(wx + 0.42, y0 + 0.95, v + 0.07), Vector3(wx + 0.42, y0 + 1.85, v + 0.07), Vector3(wx - 0.42, y0 + 1.85, v + 0.07), Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1))
		gl.quad(Vector3(wx - 0.30, y0 + 1.05, v + 0.1), Vector3(wx + 0.30, y0 + 1.05, v + 0.1), Vector3(wx + 0.30, y0 + 1.75, v + 0.1), Vector3(wx - 0.30, y0 + 1.75, v + 0.1), Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1))
	var fi := MeshInstance3D.new()
	fi.mesh = fr.build()
	fi.material_override = stage.make_cel(_tex("deck_planks_dark"), Color(0.28, 0.2, 0.15))
	ship.add_child(fi)
	var gi := MeshInstance3D.new()
	gi.mesh = gl.build()
	var gmat := StandardMaterial3D.new()
	gmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	gmat.albedo_color = Color(0.45, 0.6, 0.62)
	gmat.cull_mode = BaseMaterial3D.CULL_DISABLED
	gi.material_override = gmat
	ship.add_child(gi)
	stage.glass_mats.append(gmat)
	var di := MeshInstance3D.new()
	di.mesh = d.build()
	di.material_override = stage.make_cel(_tex("deck_planks_dark"), Color(0.32, 0.22, 0.16))
	ship.add_child(di)


static func _sail_mesh(pts: Array, nu: int, nv: int, billow: float, side: float) -> ArrayMesh:
	## pts = 4 corners [tack-low, clew-low, clew-high?]: bilinear patch (p00, p10, p11, p01) with a belly toward `side`.
	var b := U.MeshBuilder.new()
	var p00: Vector3 = pts[0]
	var p10: Vector3 = pts[1]
	var p11: Vector3 = pts[2]
	var p01: Vector3 = pts[3]
	for i in nu:
		for j in nv:
			var a := float(i) / nu
			var a2 := float(i + 1) / nu
			var c := float(j) / nv
			var c2 := float(j + 1) / nv
			var q := []
			for ab in [[a, c], [a2, c], [a2, c2], [a, c2]]:
				var x: float = ab[0]
				var y: float = ab[1]
				var p := p00.lerp(p10, x).lerp(p01.lerp(p11, x), y)
				p.z += side * billow * sin(PI * x) * sin(PI * y)
				q.append(p)
			b.quad(q[0], q[1], q[2], q[3], Vector2(a, 1.0 - c), Vector2(a2, 1.0 - c), Vector2(a2, 1.0 - c2), Vector2(a, 1.0 - c2))
	return b.build()


static func _rig(stage, ship: Node3D) -> void:
	var sailtex := _tex("sail_canvas")
	var sm: ShaderMaterial = stage.make_cel(sailtex, Color(1.18, 1.12, 1.02), 0.42)
	# main sail: from the mast (u 1.0) aft along a boom swung 18 degrees to starboard
	var boom_y := F + 2.7
	var ang := deg_to_rad(18.0)
	var clew := Vector3(1.0 - 6.4 * cos(ang), boom_y, 6.4 * sin(ang))
	var tack := Vector3(1.0 - 0.15, boom_y, 0.0)
	var head := Vector3(1.0 - 0.15, F + 10.6, 0.0)
	var peak := Vector3(1.0 - 1.6, F + 9.0, 0.5)
	var main := MeshInstance3D.new()
	main.mesh = _sail_mesh([tack, clew, peak, head], 10, 14, 0.75, 1.0)
	main.material_override = sm
	main.extra_cull_margin = 30.0
	ship.add_child(main)
	# jib: tack on the bowsprit, head at the mast top
	var jtack := Vector3(12.2, F + 1.7, 0.0)
	var jclew := Vector3(7.4, F + 2.2, -0.4)
	var jhead := Vector3(1.6, F + 10.2, -0.1)
	var jib := MeshInstance3D.new()
	jib.mesh = _sail_mesh([jtack, jclew, jhead, jhead.lerp(jtack, 0.02)], 8, 12, 0.5, -1.0)
	jib.material_override = sm
	jib.extra_cull_margin = 30.0
	ship.add_child(jib)
	# boom and bowsprit: thin wooden boxes
	var wood: ShaderMaterial = stage.make_cel(_tex("deck_planks_dark"), Color(0.9, 0.8, 0.7))
	var boom := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(6.6, 0.16, 0.16)
	boom.mesh = bm
	boom.material_override = wood
	boom.position = Vector3(1.0 - 3.3 * cos(ang), boom_y - 0.05, 3.3 * sin(ang))
	boom.rotation.y = -ang
	ship.add_child(boom)
	var spr := MeshInstance3D.new()
	var sb := BoxMesh.new()
	sb.size = Vector3(4.4, 0.2, 0.2)
	spr.mesh = sb
	spr.material_override = wood
	spr.position = Vector3(11.2, F + 1.2, 0.0)
	spr.rotation.z = deg_to_rad(8.0)
	ship.add_child(spr)
	# standing rigging: shrouds with ratlines, forestay, backstay, 1 px lines
	var pts := PackedVector3Array()
	var top := Vector3(1.0, F + 9.4, 0.0)
	for side in [1.0, -1.0]:
		var s: float = side
		for du in [-0.8, 0.0, 0.8]:
			var base := Vector3(1.0 + float(du), F + RAIL, s * (L.hull_half(0, 1.0 + float(du)) - 0.15))
			pts.append(base)
			pts.append(Vector3(1.0 + float(du) * 0.12, F + 8.4, s * 0.5))
		for k in range(1, 11):
			var t := float(k) / 11.0
			var a := Vector3(1.0 - 0.8, F + RAIL, s * (L.hull_half(0, 0.2) - 0.15)).lerp(Vector3(1.0 - 0.1, F + 8.4, s * 0.5), t)
			var b2 := Vector3(1.0 + 0.8, F + RAIL, s * (L.hull_half(0, 1.8) - 0.15)).lerp(Vector3(1.0 + 0.1, F + 8.4, s * 0.5), t)
			pts.append(a)
			pts.append(b2)
	pts.append(top)
	pts.append(Vector3(11.0, F + 1.15, 0.0))
	pts.append(top)
	pts.append(Vector3(-10.4, F + RAIL + 0.2, 0.0))
	pts.append(top)
	pts.append(Vector3(1.0 - 0.15, F + 10.6, 0.0))
	ship.add_child(stage.make_lines(pts, Color(0.30, 0.22, 0.13)))


static func _props(stage, ship: Node3D, yaw: float) -> void:
	var sp := func(sname: String, uv: Vector2, psi := 0.0, y := F, shadow := true) -> MeshInstance3D:
		var mi: MeshInstance3D = U.add_sprite(stage, ship, "ship", sname, Vector3(uv.x, y, uv.y), yaw + psi, shadow)
		if mi != null and shadow:
			var sh := ship.get_child(ship.get_child_count() - 1) as MeshInstance3D
			var smat := sh.material_override as ShaderMaterial
			smat.set_shader_parameter("clip_on", 1.0)
			smat.set_meta("clip_ship", true)
			stage.get("clip_mats").append(smat)
		return mi
	sp.call("cabin", Vector2(-7.7, 0.0))
	sp.call("mast", L.MAST)
	sp.call("helm", L.HELM, 0.0)
	sp.call("winch", L.WINCH, 0.0)
	sp.call("hatch", L.HATCH, 0.0)
	sp.call("hatch", L.HOLD_HATCH, 0.0, F, false)
	for p in L.FISH_BARRELS:
		sp.call("barrel_fish", p)
	sp.call("barrel", Vector2(-2.9, -2.45))
	sp.call("barrel", Vector2(-2.9, 2.45))
	sp.call("crate", Vector2(2.9, 2.1), 12.0)
	sp.call("crate", Vector2(4.0, 2.05), -8.0)
	sp.call("cannon", Vector2(-0.2, -2.5), 90.0)
	sp.call("cannon", Vector2(-0.4, 2.5), -90.0)
	sp.call("rope_coil", Vector2(8.2, 0.9))
	sp.call("bollard", Vector2(9.3, 0.0))
	sp.call("bollard", Vector2(-10.0, 1.4))
	sp.call("lantern", Vector2(-4.9, 2.0))
	sp.call("pirate", L.HELM_STATION, 0.0)
	sp.call("pirate", Vector2(4.8, -2.55), -150.0)
	sp.call("chest", Vector2(-3.0, -1.0), 20.0)
	# lantern halo, followed by the look's halo weight
	U.add_halo(stage, ship, Vector3(-4.9, F + 0.65, 2.0), 1.7, Color(1.0, 0.62, 0.22), 1.0, 1.0)
	U.add_halo(stage, ship, Vector3(L.CABIN_U1 + 0.3, F + 1.3, 0.0), 2.6, Color(1.0, 0.6, 0.25), 0.6, 2.0)
