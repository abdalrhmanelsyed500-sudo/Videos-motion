extends RefCounted
## Runs the SAME fixture file as tools/data_tools/test_parity.py: both validators must flag exactly the same error
## paths.
const Schema := preload("res://core/schema.gd")
const DataLoader := preload("res://core/data_loader.gd")
var _known: Dictionary = {}


func _lookup(kind: String, key: String) -> bool:
	return (_known.get(kind, []) as Array).has(key)


func run(t: Object) -> void:
	var fx := DataLoader.load_dict("res://tests/fixtures/validator_cases.json")
	_known = fx.get("ref_known", {})
	var cases: Array = fx.get("cases", [])
	t.check(cases.size() >= 30, "fixture has >= 30 cases (has %d)" % cases.size())
	for c in cases:
		var got := Schema.error_paths(Schema.validate(c["value"], c["schema"], Callable(self, "_lookup")))
		var want := PackedStringArray()
		for p in c["error_paths"]:
			want.append(str(p))
		t.check(got == want, "case '%s': expected %s, got %s" % [c["name"], want, got])
