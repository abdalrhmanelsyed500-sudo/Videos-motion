extends RefCounted
## On-foot connectivity of Anvil Harbor, checked with the game's own walkability rule on the real baked ground (PNGs read
## straight from res://, so no editor import is needed). Regression for the r4 blocker "the player cannot walk from the pier onto
## the island": a band 0.5 m wide at the landing was steeper than the walker's slope limit, and every earlier check was too
## coarse to see it. See h2d/walk_audit.gd for how the flood fill is made strict.
const CayWorld := preload("res://h2d/cay_world.gd")
const WalkAudit := preload("res://h2d/walk_audit.gd")
const LandWalker := preload("res://h2d/land_walker.gd")
const Ocean := preload("res://core/ocean.gd")
const DataLoader := preload("res://core/data_loader.gd")
const CITY_BOX := Rect2(-215.0, -285.0, 430.0, 335.0)
const WALL_Z := [-106.0, -151.0, -197.0]
const STAIR_X := [[16.0, 16.0], [-28.0, 6.0], [62.0, 6.0], [-150.0, 6.0], [140.0, 6.0]]


## The real CayWorld, built from the baked files; `holder` keeps its nodes (free it when done).
static func build_world(tuning: Dictionary) -> Array:
	var holder := Node.new()
	((Engine.get_main_loop() as SceneTree).root).add_child(holder)
	var w := CayWorld.new()
	w.build(holder, ShaderMaterial.new(), Callable(WalkTestLoader, "load_tex"), Callable(WalkTestLoader, "make_shader_mat"))
	w.walk_min_h = float(tuning.get("land.min_h", 0.45))
	w.walk_max_slope = float(tuning.get("land.max_slope", 0.55))
	return [w, holder]


class WalkTestLoader:
	extends RefCounted

	static func load_tex(file: String) -> Texture2D:
		var img := Image.load_from_file("res://h2d/art/" + file)
		if img == null:
			return null
		return ImageTexture.create_from_image(img)

	static func make_shader_mat(file: String) -> ShaderMaterial:
		var m := ShaderMaterial.new()
		m.shader = load("res://h2d/shaders/" + file)
		return m


func run(t: Object) -> void:
	var tuning := Ocean.load_tuning()
	var built := build_world(tuning)
	var w := built[0] as CayWorld
	var holder := built[1] as Node
	t.check(not (w.get("_hd") as PackedByteArray).is_empty(), "the ground height map was read (needed for every walk check below)")
	if (w.get("_hd") as PackedByteArray).is_empty():
		holder.queue_free()
		return
	var port: Dictionary = w.meta["port"]
	var land: Dictionary = w.meta["land"]
	var r := float(tuning.get("land.body_r_m", 0.45))
	_landing_profile(t, w, r)
	# the flood keeps 0.15 m more clearance than the walker needs, so its routes never graze a blocker's exact edge
	var audit := WalkAudit.new(w, CITY_BOX, 1.0, r + 0.15, 0.25)
	var ok_cells := audit.scan()
	var start := Vector2(float((land["disembark"] as Dictionary)["x"]), float((land["disembark"] as Dictionary)["z"]))
	var reached := audit.flood(start)
	t.check(ok_cells > 50000, "the capital has plenty of ground to walk on (%d cells)" % ok_cells)
	t.check(float(reached) >= 0.985 * float(ok_cells), "the pier reaches %d of %d walkable cells (>= 98.5 %%) with strict edges (%d edges refused)" % [reached, ok_cells, audit.blocked_edges])
	_targets(t, audit, port)
	_walls(t, audit)
	_solids(t, w, port)
	_drive(t, w, audit, tuning, land)
	_island(t, w, land, r)
	_sea_routes(t, w, tuning)
	_npc_spots(t, w, port)
	holder.queue_free()


## The exact r4 failure: the walker's path from the pier head (z 21) to the quay (z -3) in 5 cm steps along the landing line.
func _landing_profile(t: Object, w: CayWorld, r: float) -> void:
	# along the middle of the pier and 1 m either side, from the pier head (z 21) to the quay (z -3), in 5 cm steps. Beyond the
	# landing the notice board (13, 0.2) is meant to be solid, so only the centre line must be free everywhere.
	var bad: Array = []
	for x in [15.5, 16.0, 16.5]:
		var z := 21.0
		while z >= -3.0:
			if not w.walkable(x, z, r):
				bad.append("(%.1f, %.2f)" % [x, z])
			z -= 0.05
	t.check(bad.is_empty(), "the pier's landing lines (x 15.5, 16, 16.5) are walkable at every 5 cm from the pier head to the quay (blocked at: %s)" % str(bad.slice(0, 6)))
	var gap := 0
	var zz := 4.0
	while zz >= -3.0:
		var any_open := false
		for xi in range(0, 7):
			if w.walkable(14.5 + 0.5 * float(xi), zz, r):
				any_open = true
		if not any_open:
			gap += 1
		zz -= 0.05
	t.check(gap == 0, "at no depth between the pier and the quay is the whole pier width blocked (%d blocked rows)" % gap)
	# and the ground there is not steeper than the limit (the cause)
	var worst := 0.0
	var z2 := 2.0
	while z2 >= -2.0:
		worst = maxf(worst, w.slope_at(16.0, z2))
		z2 -= 0.1
	t.check(worst <= w.walk_max_slope, "the shore ramp at the landing is gentler than the walker's limit (worst slope %.2f, limit %.2f)" % [worst, w.walk_max_slope])


func _targets(t: Object, audit: RefCounted, port: Dictionary) -> void:
	var miss: Array = []
	for pl in port["places"]:
		var p := Vector2(float(pl["x"]), float(pl["z"]))
		if not is_nan(audit.nearest_reached(p, 3.5).x):
			continue
		miss.append(str(pl["id"]))
	t.check(miss.is_empty(), "every place on the map can be reached on foot to within 3.5 m (not reached: %s)" % str(miss))
	var spots: Dictionary = port["recruit_spots"]
	for k in spots.keys():
		var p := Vector2(float((spots[k] as Dictionary)["x"]), float((spots[k] as Dictionary)["z"]))
		t.check(not is_nan(audit.nearest_reached(p, 1.6).x), "the player can stand within talking range of %s" % str(k))
	for it in port["interactions"]:
		var p2 := Vector2(float(it["x"]), float(it["z"]))
		t.check(not is_nan(audit.nearest_reached(p2, 2.0).x), "the player can reach the interaction point '%s'" % str(it["id"]))
	var lost := 0
	for n in port["npcs"]:
		if is_nan(audit.nearest_reached(Vector2(float(n["x"]), float(n["z"])), 1.2).x):
			lost += 1
	t.check(lost == 0, "every one of the %d people stands within 1.2 m of ground the player can reach (%d cut off)" % [(port["npcs"] as Array).size(), lost])
	# Governor's Hill, the gates and the far terraces
	for q in [["palace forecourt", Vector2(16.0, -200.5)], ["town hall steps", Vector2(-62.0, -207.0)], ["barracks yard", Vector2(94.0, -207.0)], ["west gate", Vector2(-110.0, -262.0)],
			["east gate", Vector2(120.0, -262.0)], ["terrace walk", Vector2(-100.0, -158.0)], ["hill road", Vector2(100.0, -113.0)], ["market square", Vector2(16.0, -58.0)]]:
		var qp: Vector2 = q[1]
		t.check(not is_nan(audit.nearest_reached(qp, 4.0).x), "the player can walk to %s" % str(q[0]))


## Retaining walls stay walls: on each wall line the reached cells lie only in the stair columns, and every stair column is passable.
func _walls(t: Object, audit: RefCounted) -> void:
	for zw in WALL_Z:
		var in_stairs := 0
		var outside := 0
		for ix in int(audit.get("nx")):
			var c: Vector2 = audit.call("centre", ix, int((float(zw) - float(audit.get("z0"))) / float(audit.get("cell"))))
			if not audit.call("is_reached", c) or absf(c.x) > 198.0:
				continue          # beyond x +-198 is the open island, not the city wall
			var inside := false
			for s in STAIR_X:
				if absf(c.x - float(s[0])) <= float(s[1]) * 0.5 + 3.0:    # the stair's shoulders: the ground eases out over about 2 cells
					inside = true
			if inside:
				in_stairs += 1
			else:
				outside += 1

		t.check(outside == 0, "the retaining wall at z %.0f can only be crossed at the stairs (%d walkable cells outside them)" % [zw, outside])
		t.check(in_stairs >= 20, "the stairs through the wall at z %.0f are passable (%d cells)" % [zw, in_stairs])


## Buildings and other solid things remain solid: every blocker rectangle is unwalkable inside, and each baked grand building
## and house cannot be entered at its anchor.
func _solids(t: Object, w: CayWorld, port: Dictionary) -> void:
	var open_blockers := 0
	var n_checked := 0
	for b in w.blockers:
		var bb := b as Array
		if float(bb[2]) - float(bb[0]) < 1.2 or float(bb[3]) - float(bb[1]) < 1.2:
			continue
		n_checked += 1
		if w.walkable((float(bb[0]) + float(bb[2])) * 0.5, (float(bb[1]) + float(bb[3])) * 0.5, 0.45):
			open_blockers += 1
	t.check(n_checked > 300 and open_blockers == 0, "all %d building-sized blocker rectangles are solid (%d can be walked into)" % [n_checked, open_blockers])
	var enterable: Array = []
	for list_name in ["grand", "bld"]:
		for s in (port["city"] as Dictionary)["lists"][list_name]:
			var nm := str(s["name"])
			if nm.begins_with("wall_post") or nm.begins_with("wall_"):
				continue
			if w.walkable(float(s["x_m"]), float(s["z_m"]) - 2.0, 0.45):
				enterable.append("%s (%.0f, %.0f)" % [nm, float(s["x_m"]), float(s["z_m"])])
	t.check(enterable.size() == 0, "no house, shop or palace can be walked into at its anchor (%d can: %s)" % [enterable.size(), str(enterable.slice(0, 5))])


## The real LandWalker (the code the keys drive) walks the strict flood's route from the pier to the places that matter.
func _drive(t: Object, w: CayWorld, audit: RefCounted, tuning: Dictionary, land: Dictionary) -> void:
	var port: Dictionary = w.meta["port"]
	# every place on the map, every recruit, every interaction and every 12th person, from the data (not a hand-picked list)
	var targets: Array = [["the east gate", Vector2(120.0, -262.0)], ["the palace forecourt", Vector2(16.0, -200.5)]]
	for pl in port["places"]:
		targets.append(["place " + str(pl["id"]), Vector2(float(pl["x"]), float(pl["z"]))])
	for k in (port["recruit_spots"] as Dictionary).keys():
		targets.append(["recruit " + str(k), Vector2(float(port["recruit_spots"][k]["x"]), float(port["recruit_spots"][k]["z"]))])
	for it in port["interactions"]:
		targets.append(["interaction " + str(it["id"]), Vector2(float(it["x"]), float(it["z"]))])
	var npcs: Array = port["npcs"]
	for i in range(0, npcs.size(), 12):
		targets.append(["person " + str(npcs[i]["id"]), Vector2(float(npcs[i]["x"]), float(npcs[i]["z"]))])
	for q in targets:
		var tp: Vector2 = q[1]
		var near: Vector2 = audit.call("nearest_reached", tp, 3.5)
		if is_nan(near.x):
			t.check(false, "walk to %s: no route found" % str(q[0]))
			continue
		var walker := LandWalker.new()
		walker.configure(land, tuning)
		walker.disembark(land)
		var path: Array[Vector2] = audit.call("path_to", near)
		var left: float = WalkAudit.drive(walker, w, path)
		if left < 0.0:
			var here := Vector2(float(walker.get("x")), float(walker.get("z")))
			var close_pts: Array = path.filter(func(q: Vector2) -> bool: return q.distance_to(here) < 5.0)
			print("  (stuck at %.2f, %.2f; the route's waypoints near there: %s)" % [here.x, here.y, str(close_pts)])
			for b in w.blockers:
				var bb := b as Array
				if float(bb[0]) < 3.0 and float(bb[2]) > -10.0 and float(bb[1]) < -128.0 and float(bb[3]) > -142.0:
					print("   blocker ", bb)
			for dz in range(-3, 4):
				var row := ""
				for dx in range(-6, 7):
					row += "#" if w.walkable(-3.5 + dx * 0.5, -135.2 + dz * 0.5, 0.45) else "."
				print("   ", row)
		t.check(left >= 0.0 and left < 1.0, "the real walker walks from the pier to %s (%d waypoints, %.1f m short%s)" % [str(q[0]), path.size(), left, "; STUCK" if left < 0.0 else ""])


## The island beyond the walls: from the pier to every stop of the exploration route (Pearl Cove, Lookout Hill, Wreck Beach...), on
## a coarser 3 m grid but with the same strict edges.
func _island(t: Object, w: CayWorld, land: Dictionary, r: float) -> void:
	var audit := WalkAudit.new(w, Rect2(-520.0, -620.0, 1060.0, 666.0), 3.0, r + 0.15, 0.25)
	audit.scan()
	var d := land["disembark"] as Dictionary
	var n := audit.flood(Vector2(float(d["x"]), float(d["z"])))
	t.check(n > 20000, "the island walk grid is connected to the pier (%d cells)" % n)
	for q in land["pois"]:
		var p := Vector2(float(q["x"]), float(q["z"]))
		t.check(not is_nan(audit.nearest_reached(p, 8.0).x), "the pier reaches the stop '%s' on foot" % str(q["name"]))


## By sea: from where the game starts the ship, a hull-sized water route leads to the middle and to the rim of every fishing ground
## (the nets work only inside a ground, so an unreachable ground would silently end the economy loop). 8 m grid, five hull probes per cell
## with the game's own aground rule (height under any probe > harbor.ground_limit_m).
func _sea_routes(t: Object, w: CayWorld, tuning: Dictionary) -> void:
	var limit := float(tuning.get("harbor.ground_limit_m", 0.5))
	var bounds := Rect2(-900.0, -420.0, 1700.0, 2370.0)
	var step := 8.0
	var nx := int(bounds.size.x / step)
	var nz := int(bounds.size.y / step)
	var free := PackedByteArray()
	free.resize(nx * nz)
	for j in nz:
		for i in nx:
			var x := bounds.position.x + (float(i) + 0.5) * step
			var z := bounds.position.y + (float(j) + 0.5) * step
			var ok := true
			for off in [Vector2.ZERO, Vector2(10, 0), Vector2(-10, 0), Vector2(0, 10), Vector2(0, -10)]:
				if w.height_at(x + off.x, z + off.y) > limit:
					ok = false
					break
			free[j * nx + i] = 1 if ok else 0
	var start := Vector2(-100.0, 140.0)    # H2D0.START_POS
	var si := int((start.x - bounds.position.x) / step)
	var sj := int((start.y - bounds.position.y) / step)
	t.check(free[sj * nx + si] == 1, "the ship's start position is open water")
	var seen := PackedByteArray()
	seen.resize(nx * nz)
	var queue: Array[int] = [sj * nx + si]
	seen[sj * nx + si] = 1
	var head := 0
	while head < queue.size():
		var c: int = queue[head]
		head += 1
		var ci := c % nx
		var cj := c / nx
		for d in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
			var ni: int = ci + int(d[0])
			var nj: int = cj + int(d[1])
			if ni < 0 or nj < 0 or ni >= nx or nj >= nz:
				continue
			var n: int = nj * nx + ni
			if seen[n] == 0 and free[n] == 1:
				seen[n] = 1
				queue.append(n)
	t.check(queue.size() > 20000, "the sea around the start is one large body of open water (%d cells)" % queue.size())
	var doc := DataLoader.load_dict("res://data/port/fishing_grounds.json")
	var grounds: Dictionary = doc["grounds"]
	t.check(grounds.size() == 4, "there are four fishing grounds (%d)" % grounds.size())
	for id in grounds.keys():
		var g: Dictionary = grounds[id]
		var pts: Array = [Vector2(float(g["x"]), float(g["z"]))]
		for k in 8:
			var a := TAU * float(k) / 8.0
			pts.append(Vector2(float(g["x"]) + cos(a) * float(g["r"]) * 0.6, float(g["z"]) + sin(a) * float(g["r"]) * 0.6))
		var reached := 0
		for p in pts:
			var i2 := int((p.x - bounds.position.x) / step)
			var j2 := int((p.y - bounds.position.y) / step)
			if i2 >= 0 and j2 >= 0 and i2 < nx and j2 < nz and seen[j2 * nx + i2] == 1:
				reached += 1
		t.check(reached == pts.size(), "%s: the middle and 8 points inside its rim can be sailed to from the start (%d of %d)" % [str(g["name"]), reached, pts.size()])


## The in-game F8 check found "npc_sailor_1 stands on walkable ground" failing while every offline check passed: the baked NPC spot
## itself must pass the exact rule the people use to move (PortNpcs.BODY_R) on the real ground.
func _npc_spots(t: Object, w: CayWorld, port: Dictionary) -> void:
	var bad: Array = []
	for n in port["npcs"]:
		if not w.walkable(float(n["x"]), float(n["z"]), 0.4):
			bad.append("%s (%.1f, %.1f)" % [str(n["id"]), float(n["x"]), float(n["z"])])
	t.check(bad.is_empty(), "every baked person stands on walkable ground (%d do not: %s)" % [bad.size(), str(bad)])
