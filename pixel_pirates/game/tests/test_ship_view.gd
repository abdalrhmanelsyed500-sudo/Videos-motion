extends RefCounted
## CP-2 Release A: the 3D ship model builds, stays small (a few meshes, bounded vertices), follows the layout, and maps ship-local
## positions to the world correctly at any heading (the pirate is drawn there). Headless: no pixels are checked here (the
## renderer scenario tools/godot_browser/scenarios/deck_*.mjs does that). NOT YET RUN ON THE USER'S PC.
const View := preload("res://h2d/ship_deck_view.gd")
const Layout := preload("res://h2d/ship_layout.gd")
const ShipMesh := preload("res://h2d/ship_mesh.gd")
const Walker := preload("res://h2d/ship_walker.gd")


func run(t: Object) -> void:
	# --- the mesh builder
	var b := ShipMesh.new()
	b.box(Vector3(0.0, 1.0, 0.0), Vector3(1.0, 1.0, 1.0), Color.WHITE, ShipMesh.M_DECK)
	t.call("check", b.vertex_count() == 20, "a box without a bottom has 5 faces x 4 vertices (%d)" % b.vertex_count())
	var bb: AABB = b.bounds()
	t.call("check", bb.size.is_equal_approx(Vector3(2.0, 2.0, 2.0)), "box bounds are 2 m")
	b.cyl(Vector3.ZERO, 0.5, 1.0, 8, Color.WHITE, ShipMesh.M_BARREL)
	b.beam(Vector3.ZERO, Vector3(0, 0, 3), 0.1, Color.WHITE, ShipMesh.M_ROPE)
	b.tube(Vector3.ZERO, Vector3(0, 0, 3), 0.1, 6, Color.WHITE, ShipMesh.M_ROPE)
	var mesh: ArrayMesh = b.build()
	t.call("check", mesh.get_surface_count() == 1, "one surface")
	t.call("check", ShipMesh.p(2.0, 3.0, 4.0).is_equal_approx(Vector3(3.0, 4.0, -2.0)), "ship-local (u, v, y) -> model (v, y, -u)")
	# --- the whole ship
	var v := View.new()
	v.build()
	var st: Dictionary = v.stats()
	t.call("check", int(st["meshes"]) >= 8 and int(st["meshes"]) <= 20, "a handful of meshes (%d)" % int(st["meshes"]))
	t.call("check", int(st["vertices"]) > 3000 and int(st["vertices"]) < 60000, "vertex budget (%d)" % int(st["vertices"]))
	# --- levels
	for lv in 4:
		v.set_level(lv)
		t.call("check", v.level() == lv, "level %d set" % lv)
		var g_open: bool = (lv == 0 or lv == 3)
		t.call("check", (v.get_child(0).get_child(0) as Node3D).visible == g_open, "open group visible only on the deck and nest (level %d)" % lv)
	# --- pose: ship-local to world at several headings
	v.set_level(0)
	for hd in [0.0, 58.0, 90.0, 180.0, 291.0]:
		v.set_pose(Vector2(100.0, -50.0), float(hd), 0.0, 0.0, 0.0, 0.5)
		var lp := Vector2(3.0, 1.5)
		var w3: Vector3 = v.to_world(ShipMesh.p(lp.x, lp.y, 1.2))
		var want: Vector2 = Vector2(100.0, -50.0) + Walker.to_world(lp, float(hd))
		t.call("check", absf(w3.x - want.x) < 0.001 and absf(w3.z - want.y) < 0.001 and absf(w3.y - 1.2) < 0.001, "to_world matches the walker at heading %d (%s vs %s)" % [int(hd), str(Vector2(w3.x, w3.z)), str(want)])
	# bow points where the heading points
	v.set_pose(Vector2.ZERO, 90.0, 0.0, 0.0, 0.0, 0.5)
	var bow: Vector3 = v.to_world(ShipMesh.p(10.0, 0.0, 0.0))
	t.call("check", bow.x > 9.9 and absf(bow.z) < 0.01, "heading 90: the bow is to the east")
	# --- roll and pitch lean the mast like the sprite does
	v.set_pose(Vector2.ZERO, 0.0, 10.0, 0.0, 0.0, 1.0)
	var top: Vector3 = v.to_world(ShipMesh.p(0.0, 0.0, 10.0))
	t.call("check", top.x > 1.0, "positive roll leans the masthead to starboard (%.2f)" % top.x)
	v.set_pose(Vector2.ZERO, 0.0, 0.0, 6.0, 0.0, 1.0)
	top = v.to_world(ShipMesh.p(0.0, 0.0, 10.0))
	t.call("check", top.z > 0.5, "positive pitch (bow up) leans the masthead aft (%.2f)" % top.z)
	# --- fish and stores follow data
	v.set_fish_fill(0.0)
	t.call("check", v.fish_visible_count() == 0, "empty hold: no fish in the barrels")
	v.set_fish_fill(0.3)
	t.call("check", v.fish_visible_count() == 2, "30%% full: the first two barrels hold fish (%d)" % v.fish_visible_count())
	v.set_fish_fill(1.0)
	t.call("check", v.fish_visible_count() == 4, "full hold: all four barrels")
	v.set_fish_fill(0.5)
	t.call("check", v.fish_visible_count() == 2, "half full: two barrels")
	v.set_stores({"food": 30, "drink": 0})
	var zn: Dictionary = v.get("_zones")
	t.call("check", (zn["food"] as MeshInstance3D).mesh != null and (zn["drink"] as MeshInstance3D).mesh == null, "stores: food racks filled, drink racks empty")
	v.set_stores({})
	t.call("check", (zn["food"] as MeshInstance3D).mesh == null, "stores: empty inventory leaves bare racks")
	# --- cabin roof dissolve
	v.set_alpha(1.0)
	v.set_cabin_open(true, 1.0)
	t.call("check", v.cabin_fade() < 0.01, "cabin roof fully dissolved when inside")
	v.set_cabin_open(false, 1.0)
	t.call("check", v.cabin_fade() > 0.99, "and back")
	v.free()
