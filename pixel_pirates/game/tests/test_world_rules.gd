extends RefCounted
## Same fixture file as test_parity.py: the GDScript world rules must find exactly the same problems.
const WorldRules := preload("res://core/world_rules.gd")
const DataLoader := preload("res://core/data_loader.gd")


func run(t: Object) -> void:
	var fx := DataLoader.load_dict("res://tests/fixtures/world_cases.json")
	var cases: Array = fx.get("cases", [])
	t.check(cases.size() >= 14, "world fixture has >= 14 cases (has %d)" % cases.size())
	for c in cases:
		var islands := {}
		for i in c["islands"]:
			islands[i["id"]] = i
		var want := PackedStringArray()
		for code in c["codes"]:
			want.append(str(code))
		var got := WorldRules.codes(islands)
		t.check(got == want, "world case '%s': expected %s, got %s" % [c["name"], want, got])
