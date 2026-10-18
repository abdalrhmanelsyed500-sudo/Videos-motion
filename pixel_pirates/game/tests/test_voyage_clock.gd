extends RefCounted
## Same fixture file as tools/data_tools/test_design_checks.py: the GDScript clock must give the same answers.
const VoyageClock := preload("res://core/voyage_clock.gd")
const DataLoader := preload("res://core/data_loader.gd")


func run(t: Object) -> void:
	var fx := DataLoader.load_dict("res://tests/fixtures/clock_cases.json")
	var cases: Array = fx.get("cases", [])
	t.check(cases.size() >= 40, "clock fixture has >= 40 cases (has %d)" % cases.size())
	for c in cases:
		var got: Variant = VoyageClock.call_case(str(c["fn"]), c["args"])
		var want: Variant = c["expect"]
		var ok := false
		if typeof(want) == TYPE_STRING:
			ok = str(got) == str(want)
		else:
			ok = got != null and absf(float(got) - float(want)) < 0.000001
		t.check(ok, "clock %s%s: expected %s, got %s" % [c["fn"], c["args"], want, got])
	t.check(VoyageClock.WATCH_NAMES.size() * 4 == 24, "six watches of four hours make a day")
