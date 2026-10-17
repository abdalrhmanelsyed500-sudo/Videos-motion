extends RefCounted
## Loads the baked fixture islands (A6) and re-verifies in GDScript what the Python baker claims.
const IslandMap := preload("res://core/island_map.gd")
const DIR := "res://tests/fixtures/islands/maps/"


func run(t: Object) -> void:
	var files: Array[String] = []
	var d := DirAccess.open(DIR)
	t.check(d != null, "fixture map folder opens")
	if d == null:
		return
	for f in d.get_files():
		if f.ends_with(".map.json"):
			files.append(f)
	files.sort()
	t.check(files.size() == 10, "10 fixture maps (has %d)" % files.size())
	for f in files:
		var m: RefCounted = IslandMap.from_file(DIR + f)
		t.check(m.error == "", "%s loads: %s" % [f, m.error])
		if m.error != "":
			continue
		t.check(m.width == m.height and m.width >= 80, "%s grid is square and >= 80" % f)
		var mask: PackedByteArray = m.reachable_from_landing()
		var all_ok := true
		for q in m.pois:
			if not m.is_dry(int(q["x"]), int(q["y"])) or mask[int(q["y"]) * m.width + int(q["x"])] != 1:
				all_ok = false
		t.check(all_ok, "%s: every POI is dry land and reachable from the landing" % f)
		t.check(m.pois_of_kind("hook").size() >= 1, "%s has a hook POI" % f)
		var landing_ok := true
		for l in m.landings:
			var on_beach: bool = m.code_at(int(l["x"]), int(l["y"])) == "."
			var sea_ok: bool = m.code_at(int(l["sea_x"]), int(l["sea_y"])) == "-"
			landing_ok = landing_ok and on_beach and sea_ok
		t.check(landing_ok, "%s: landings are beaches next to shallows" % f)
	var m1: RefCounted = IslandMap.from_file(DIR + "isl_901.map.json")
	t.check(m1.width == 128, "tier-2 island is 128 tiles wide")
	var o := m1.offers()
	var offers_ok: bool = o.size() == 3 and o.has("fresh_water") and o.has("fruit") and o.has("timber")
	t.check(offers_ok, "isl_901 offers fresh_water, fruit, timber")
	t.check(m1.explore_minutes() > 0.0 and m1.explore_minutes() < 16.0, "explore time is inside the tier-2 budget")
	var c := m1.local_to_cell(m1.cell_to_local(10, 20))
	t.check(c == Vector2i(10, 20), "cell <-> local metres round trip")
	t.check(m1.cell_to_local(64, 64).is_equal_approx(Vector2(1.0, 1.0)), "centre cell is near local (0,0) in metres")
	# tamper: a changed terrain row must be refused
	var raw: Variant = JSON.parse_string(FileAccess.get_file_as_string(DIR + "isl_901.map.json"))
	var rows: Array = (raw as Dictionary)["terrain"]
	rows[3] = "g" + (rows[3] as String).substr(1)
	var bad: RefCounted = IslandMap.new()
	t.check("hash" in str(bad.parse(raw as Dictionary)), "edited terrain is refused by the hash")
