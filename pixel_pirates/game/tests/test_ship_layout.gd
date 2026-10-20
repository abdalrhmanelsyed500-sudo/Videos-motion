extends RefCounted
## CP-2 Release A: the ship's plan. Every level is one connected walking space, every place you must reach can be reached with
## a real body (r = 0.38 m), every aisle is wide enough, nothing solid sits on a spawn point, and the hatches and ladders line
## up between levels. Pure logic. NOT YET RUN ON THE USER'S PC.
const Layout := preload("res://h2d/ship_layout.gd")
const R := 0.38
const STEP := 0.1


func run(t: Object) -> void:
	var lay := Layout.new()
	# --- every arrival and station is standable
	var spots := {
		"helm station": [0, Layout.HELM_STATION], "helm leave": [0, Layout.HELM_LEAVE], "arrive above": [0, Layout.ARRIVE_ABOVE], "ladder land": [0, Layout.LADDER_LAND],
		"arrive below": [1, Layout.ARRIVE_BELOW], "arrive back up": [1, Layout.ARRIVE_BACK_UP], "arrive hold": [2, Layout.ARRIVE_HOLD],
		"nest arrive": [3, Layout.NEST_ARRIVE],
	}
	for k in spots.keys():
		var s: Array = spots[k]
		t.call("check", lay.walkable(int(s[0]), (s[1] as Vector2).x, (s[1] as Vector2).y, R), "standable: " + str(k))
	# --- connectivity per level: flood from the arrival, then every interaction must have standable ground reached within reach
	var starts := {0: Layout.HELM_LEAVE, 1: Layout.ARRIVE_BELOW, 2: Layout.ARRIVE_HOLD, 3: Layout.NEST_ARRIVE}
	var floods := {}
	for lv in 4:
		var res := lay.flood(lv, starts[lv] as Vector2, R, STEP)
		floods[lv] = res
		t.call("check", bool(res["start_ok"]), "level %d start standable" % lv)
		t.call("check", int(res["cells"]) > 200, "level %d has a real floor (%d cells)" % [lv, int(res["cells"])])
		for it in lay.interactions(lv):
			var d: Dictionary = it
			var c: Vector2 = d["c"]
			t.call("check", Layout.near_reached(res, c, float(d["r"]), STEP), "level %d: %s reachable (%s)" % [lv, d["id"], c])
	# --- places that must be reached: other arrivals are in the same connected floor as the start
	var f0: Dictionary = floods[0]
	for nm in ["arrive above", "ladder land"]:
		var p: Vector2 = (spots[nm] as Array)[1]
		t.call("check", (f0["reached"] as Dictionary).has(Vector2i(int(roundf(p.x / STEP)), int(roundf(p.y / STEP)))), "main deck: %s connected to the helm" % nm)
	var f1: Dictionary = floods[1]
	for nm in ["arrive below", "arrive back up"]:
		var p1: Vector2 = (spots[nm] as Array)[1]
		t.call("check", (f1["reached"] as Dictionary).has(Vector2i(int(roundf(p1.x / STEP)), int(roundf(p1.y / STEP)))), "sleeping deck: %s connected" % nm)
	# --- the cabin: inside reachable through the 1.4 m door, desk and chest within reach, door not wider or narrower than designed
	t.call("check", Layout.near_reached(f0, Vector2(-8.2, -0.7), 0.3, STEP), "cabin interior in front of the desk is reachable")
	t.call("check", lay.walkable(0, Layout.CABIN_U1, -1.3, R), "the cabin door admits a body")
	t.call("check", not lay.walkable(0, Layout.CABIN_U1, 0.8, R), "the front wall beside the door is solid")
	t.call("check", not lay.walkable(0, Layout.CABIN_U1, -2.15, 0.1), "the wall strip left of the door is solid")
	t.call("check", absf((Layout.DOOR_V1 - Layout.DOOR_V0) - 1.4) < 0.001, "the door is 1.4 m wide")
	# --- the mast, hatch coaming, winch, barrels are solid
	t.call("check", not lay.walkable(0, Layout.MAST.x, Layout.MAST.y, R), "mast is solid")
	t.call("check", not lay.walkable(0, Layout.HATCH.x, Layout.HATCH.y, R), "open hatch is solid (no walking into the hole)")
	t.call("check", not lay.walkable(0, Layout.WINCH.x, Layout.WINCH.y, R), "winch is solid")
	for b in Layout.FISH_BARRELS:
		t.call("check", not lay.walkable(0, b.x, b.y, R), "fish barrel solid at " + str(b))
	# --- aisles: with a body of 0.5 m radius (a fat margin) the key places on every level are still connected
	for lv in 3:
		var res2 := lay.flood(lv, starts[lv] as Vector2, 0.5, STEP)
		t.call("check", bool(res2["start_ok"]), "level %d start standable with r=0.5" % lv)
		for it in lay.interactions(lv):
			var d2: Dictionary = it
			if lv == 0 and (str(d2["id"]) == "desk" or str(d2["id"]) == "chest"):
				continue    # the cabin door (1.4 m) is designed for r <= 0.6 only at its centre; checked above with r = 0.38
			t.call("check", Layout.near_reached(res2, d2["c"] as Vector2, float(d2["r"]), STEP), "level %d: %s reachable with r=0.5" % [lv, d2["id"]])
	# --- level links line up: the hatch is at the same u, v on both levels, ladders land on standable ground
	t.call("check", Layout.HATCH.is_equal_approx(lay.interaction(0, "hatch_down")["c"] as Vector2), "deck hatch interaction at the hatch")
	t.call("check", Layout.HATCH.is_equal_approx(lay.interaction(1, "ladder_up")["c"] as Vector2), "sleeping deck ladder under the hatch")
	t.call("check", Layout.HOLD_HATCH.is_equal_approx(lay.interaction(1, "hatch_down")["c"] as Vector2), "hold hatch on the sleeping deck")
	t.call("check", Layout.HOLD_HATCH.is_equal_approx(lay.interaction(2, "ladder_up")["c"] as Vector2), "hold ladder under the hold hatch")
	t.call("check", lay.walkable(0, Layout.LADDER_LAND.x, Layout.LADDER_LAND.y, R), "ladder foot landing is standable")
	var base := Layout.ladder_point(0.0)
	var top := Layout.ladder_point(1.0)
	t.call("check", absf(base.z) < 0.001 and absf(top.z - (Layout.NEST_Y - Layout.FLOOR_Y)) < 0.001, "ladder rises exactly from the deck to the nest floor")
	t.call("check", absf(Layout.LADDER_RISE - (Layout.NEST_Y - Layout.FLOOR_Y)) < 0.001, "LADDER_RISE constant matches")
	t.call("check", Vector2(top.x, top.y).distance_to(Layout.NEST_ARRIVE) < 1.2, "the ladder top is next to the nest landing")
	# --- the nest ring around the mast is passable (width of the free ring >= a body)
	t.call("check", lay.walkable(3, 1.0, 1.0, R) and lay.walkable(3, 1.0, -1.0, R) and lay.walkable(3, 2.0, 0.0, R) and lay.walkable(3, 0.0, 0.0, R),
			"the nest can be walked all the way round the mast")
	t.call("check", not lay.walkable(3, 3.0, 0.0, R), "the nest has rails (no walking off)")
	# --- hull limits: not walkable outside the hull
	t.call("check", not lay.walkable(0, 0.0, 3.2, 0.1), "no walking over the rail")
	t.call("check", not lay.walkable(0, -11.5, 0.0, 0.1), "no walking past the stern")
	t.call("check", not lay.walkable(0, 12.0, 0.0, 0.1), "no walking past the bow")
	# --- obstacles never sit on another level's spawn
	for lv in 3:
		for o in lay.obstacles(lv):
			var od: Dictionary = o
			for sp in spots.values():
				if int((sp as Array)[0]) != lv:
					continue
				var pp: Vector2 = (sp as Array)[1]
				t.call("check", not Layout._hits(od, pp.x, pp.y, 0.1), "obstacle %s not on spawn" % od["id"])
	# --- stores
	t.call("check", Layout.pieces_for("food", 0) == 0, "no food, no sacks")
	t.call("check", Layout.pieces_for("food", 1) == 1 and Layout.pieces_for("food", 9) == 2, "pieces grow with units")
	t.call("check", Layout.pieces_for("food", 10000) == 6, "pieces are capped by the rack")
	t.call("check", Layout.zone_for_category("medicine") == "stores" and Layout.zone_for_category("treasure") == "trade", "category to rack")
	t.call("check", Layout.zone_for_category("nonsense") == "", "unknown category has no rack")
	# --- the cabin roof opens at the door and inside
	t.call("check", Layout.cabin_open(-7.0, 0.0) and Layout.cabin_open(-5.4, -1.3) and Layout.cabin_open(-4.9, -1.3), "cabin opens inside and in the doorway")
	t.call("check", not Layout.cabin_open(-3.0, 0.0) and not Layout.cabin_open(-7.0, 3.0), "cabin closed outside")
