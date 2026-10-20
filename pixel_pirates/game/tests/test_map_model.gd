extends RefCounted
## Pure rules of the map (ui/map/map_model.gd): view data, coordinate maths, pan/zoom limits, label placement, state clean-up.
## Also keeps the three copies of the view table in step (map_views.json, the built-in copy, the island json) and checks the
## picture sizes against bounds * ppm.
const Model := preload("res://ui/map/map_model.gd")


func run(t: Object) -> void:
	_views(t)
	_maths(t)
	_state(t)
	_labels(t)


func _views(t: Object) -> void:
	var r := Model.load_views()
	t.check(str(r["error"]) == "", "map_views.json loads without a problem (%s)" % str(r["error"]))
	var views: Array = r["views"]
	t.check(views.size() == 3, "three views")
	var ids: Array = []
	for v in views:
		ids.append(str((v as Dictionary)["id"]))
	t.check(ids == ["city", "island", "sea"], "views are city, island, sea (%s)" % str(ids))
	t.check(Model.view_problems(views).is_empty(), "the views have every key: %s" % str(Model.view_problems(views)))
	t.check(JSON.stringify(Model.DEFAULT_VIEWS) == JSON.stringify(views), "the built-in views equal map_views.json")
	var cay: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://h2d/art/anvil_cay.json"))
	var from_cay: Array = (((cay as Dictionary)["port"] as Dictionary)["map"] as Dictionary)["views"]
	t.check(JSON.stringify(from_cay) == JSON.stringify(views), "anvil_cay.json port.map.views equals map_views.json (one bake wrote both)")
	for v in views:
		var vd := v as Dictionary
		var path := "res://h2d/art/" + str(vd["file"])
		t.check(FileAccess.file_exists(path), "picture exists: " + path)
		var img := Image.load_from_file(path)
		var px := Model.map_px(vd)
		t.check(img != null and not img.is_empty() and absf(img.get_width() - px.x) <= 1.0 and absf(img.get_height() - px.y) <= 1.0,
				"picture %s is %s px, bounds x ppm say %s" % [str(vd["file"]), str(img.get_size() if img != null else Vector2i.ZERO), str(px)])
	# missing / broken data falls back to the built-in views and says why
	var miss := Model.load_views("res://h2d/art/" + "no_such_views" + ".json")
	t.check((miss["views"] as Array).size() == 3 and str(miss["error"]).contains("missing"), "a missing views file falls back with a reason")
	var bad := Model.view_problems([{"id": "x"}])
	t.check(bad.size() >= 7, "a view with only an id reports its missing keys (%d)" % bad.size())
	t.check(not Model.view_problems([]).is_empty(), "an empty view list is a problem")
	var dup := Model.view_problems([Model.DEFAULT_VIEWS[0], Model.DEFAULT_VIEWS[0]])
	t.check(str(dup).contains("twice"), "a duplicated view id is reported")
	var flat: Dictionary = (Model.DEFAULT_VIEWS[0] as Dictionary).duplicate(true)
	flat["bounds"] = [1.0, 1.0, 1.0, 5.0]
	t.check(str(Model.view_problems([flat])).contains("no area"), "bounds with no area are reported")
	# every named place lies on at least one view, so a marker is never lost
	var cp: Dictionary = (cay as Dictionary)["port"]
	for pl in cp["places"]:
		var p := Vector2(float((pl as Dictionary)["x"]), float((pl as Dictionary)["z"]))
		var ok := false
		for v in views:
			var vd2 := v as Dictionary
			if (((pl as Dictionary).get("views", []) as Array).is_empty() or ((pl as Dictionary)["views"] as Array).has(vd2["id"])) and Model.in_bounds(p, vd2):
				ok = true
		t.check(ok, "place '%s' lies inside a view it is listed on" % str((pl as Dictionary)["id"]))


func _maths(t: Object) -> void:
	var v: Dictionary = Model.DEFAULT_VIEWS[0]
	var org := Vector2(10, 20)
	for p in [Vector2(-212, -282), Vector2(0, 0), Vector2(16, -66), Vector2(212, 42)]:
		var back := Model.frame_to_world(Model.world_to_frame(p, v, org, 1.7), v, org, 1.7)
		t.check(back.distance_to(p) < 0.001, "world -> frame -> world round trip %s" % str(p))
	t.check(Model.world_to_frame(Vector2(-212, -282), v, org, 2.0).is_equal_approx(org), "the north-west corner sits at the origin")
	t.check(Model.world_to_frame(Vector2(212, 42), v, Vector2.ZERO, 1.0).is_equal_approx(Model.map_px(v)), "the south-east corner sits at the picture size")
	t.check(is_equal_approx(Model.fit_zoom(Vector2(800, 500), Vector2(1060, 810)), 500.0 / 810.0), "fit zoom is the smaller ratio")
	t.check(Model.fit_zoom(Vector2(0, 0), Vector2(10, 10)) == 1.0, "fit zoom of a zero frame is a safe 1.0")
	# clamp: a picture smaller than the frame is centred, a bigger one cannot be dragged away
	t.check(Model.clamp_origin(Vector2(300, 300), Vector2(800, 500), Vector2(400, 300)).is_equal_approx(Vector2(200, 100)), "a small picture is centred")
	var big := Model.clamp_origin(Vector2(5000, 5000), Vector2(800, 500), Vector2(2000, 1500))
	t.check(big == Vector2(40, 40), "dragging a big picture far right/down stops at the slack (%s)" % str(big))
	var lo := Model.clamp_origin(Vector2(-9000, -9000), Vector2(800, 500), Vector2(2000, 1500))
	t.check(lo == Vector2(800 - 2000 - 40, 500 - 1500 - 40), "dragging far left/up stops at the far edge (%s)" % str(lo))
	# zoom keeps the point under the pivot
	var pv := Vector2(300, 200)
	var w1 := Model.frame_to_world(pv, v, org, 1.0)
	var org2 := Model.zoom_about(org, 1.0, 2.5, pv)
	var w2 := Model.frame_to_world(pv, v, org2, 2.5)
	t.check(w1.distance_to(w2) < 0.001, "zooming about the cursor keeps the world point under it")
	var c := Model.origin_centered_on(Vector2(16, -66), v, 1.2, Vector2(800, 500))
	t.check(Model.world_to_frame(Vector2(16, -66), v, c, 1.2).is_equal_approx(Vector2(400, 250)), "centring puts the point in the middle of the frame")
	# first tab
	var views: Array = Model.DEFAULT_VIEWS
	t.check(Model.default_tab({"ashore": true}, views) == 0, "ashore -> City tab")
	t.check(Model.default_tab({"docked": true}, views) == 0, "docked at the pier -> City tab")
	t.check(Model.default_tab({"ashore": false, "docked": false}, views) == 2, "under way -> Sea tab")
	t.check(Model.default_tab({}, [{"id": "x"}]) == 0, "no matching tab -> the first")
	t.check(Model.you_at({"ashore": true, "player": Vector2(1, 2), "ship": Vector2(3, 4)}) == Vector2(1, 2), "you are the walker ashore")
	t.check(Model.you_at({"ashore": false, "player": Vector2(1, 2), "ship": Vector2(3, 4)}) == Vector2(3, 4), "you are the ship at sea")
	var es: Array = [{"id": "a", "views": []}, {"id": "b", "views": ["city"]}, {"id": "c", "views": ["sea"]}]
	t.check(Model.entries_for_view(es, "city").size() == 2 and Model.entries_for_view(es, "sea").size() == 2, "an entry without views shows on every view")


func _state(t: Object) -> void:
	var n := Model.normalize_state({})
	t.check((n["problems"] as Array).is_empty() and ((n["state"] as Dictionary)["entries"] as Array).is_empty(), "an empty state is fine (defaults)")
	var s: Dictionary = n["state"]
	t.check(s["player"] == Vector2.ZERO and s["ship"] == Vector2.ZERO and not bool(s["ashore"]), "defaults: positions zero, not ashore")
	var d := {"entries": [{"id": "a", "kind": "place", "name": "A", "x": 1, "z": 2}, {"id": "a", "kind": "place", "name": "dup", "x": 1, "z": 2},
			{"id": "b", "kind": "place", "x": 1, "z": 2}, "junk", {"id": "c", "kind": "ground", "name": "C", "x": 5.5, "z": 6.5, "rank": 2}],
			"player": "not a vector", "ship": Vector2(3, 4), "tracked": "c", "ship_heading": 1.5, "rings": [{"x": 1, "z": 2, "r": 3, "open": true}, {"x": 1}]}
	var r := Model.normalize_state(d)
	var st: Dictionary = r["state"]
	t.check((st["entries"] as Array).size() == 2, "bad entries (duplicate id, no name, not a dictionary) are dropped: %d kept" % (st["entries"] as Array).size())
	t.check(str(r["problems"]).contains("3 map entries were skipped"), "the drop is reported: %s" % str(r["problems"]))
	t.check(str(r["problems"]).contains("player"), "a wrong 'player' type is reported")
	t.check(st["ship"] == Vector2(3, 4) and str(st["tracked"]) == "c" and is_equal_approx(float(st["ship_heading"]), 1.5), "good fields pass through")
	t.check((st["rings"] as Array).size() == 1, "a ring without radius is dropped")
	t.check(typeof(((st["entries"] as Array)[0] as Dictionary)["x"]) == TYPE_FLOAT, "integer coordinates become floats")


func _labels(t: Object) -> void:
	var dot := Vector2(26, 26)
	var items: Array = [
		{"id": "a", "dot": Rect2(Vector2(100, 100), dot), "label": Vector2(100, 20), "priority": 20, "force": false},
		{"id": "b", "dot": Rect2(Vector2(130, 100), dot), "label": Vector2(100, 20), "priority": 10, "force": false},   # b's dot sits on a's name
		{"id": "c", "dot": Rect2(Vector2(400, 300), dot), "label": Vector2(100, 20), "priority": 10, "force": false},
	]
	var shown := Model.place_labels(items)
	t.check(shown.has("a") and shown.has("c") and not shown.has("b"), "overlapping names: the higher priority stays, the other is hidden (%s)" % str(shown.keys()))
	items[1]["force"] = true
	shown = Model.place_labels(items)
	t.check(shown.has("b"), "a forced (selected / tracked) name is always shown")
	var rects: Array = []
	for id in shown.keys():
		rects.append(shown[id])
	var clash := false
	items[1]["force"] = false
	var s2 := Model.place_labels(items)
	var rr: Array = []
	for id in s2.keys():
		rr.append(s2[id])
	for i in rr.size():
		for j in range(i + 1, rr.size()):
			if (rr[i] as Rect2).intersects(rr[j] as Rect2):
				clash = true
	t.check(not clash, "no two shown names overlap")
	t.check(Model.place_labels([]).is_empty(), "no items, no names")
