extends RefCounted
## Loads the REAL data through the registry (no autoload needed) and checks it, plus content rule 1 at schema level.
const Schema := preload("res://core/schema.gd")


func run(t: Object) -> void:
	var reg: Node = load("res://core/registry.gd").new()
	var errs: PackedStringArray = reg.load_all()
	t.check(errs.is_empty(), "all data validates clean: %s" % "; ".join(errs))
	t.check(reg.count("item") >= 16, "at least 16 items (has %d)" % reg.count("item"))
	t.check(reg.count("difficulty_mode") == 3, "3 difficulty modes")
	t.check(reg.count("tuning") >= 14, "at least 14 tuning keys")
	t.check(reg.has("item", "item_hardtack"), "item_hardtack exists")
	t.check(reg.lookup("asset", "ico_item_hardtack"), "asset lookup works")
	t.check(not reg.lookup("item", "item_does_not_exist"), "unknown item is unknown")
	var modes: Array = ["mode_story", "mode_normal", "mode_hardcore"]
	for k in (reg.record("difficulty_mode", "mode_normal")["multipliers"] as Dictionary).keys():
		var a := float(reg.record("difficulty_mode", modes[0])["multipliers"][k])
		var b := float(reg.record("difficulty_mode", modes[1])["multipliers"][k])
		var c := float(reg.record("difficulty_mode", modes[2])["multipliers"][k])
		t.check(a <= b and b <= c, "difficulty ordering story <= normal <= hardcore for %s" % k)
		t.check(is_equal_approx(b, 1.0), "normal multiplier %s is 1.0" % k)
	# negative: a broken item must be rejected
	var bad: Dictionary = (reg.record("item", "item_rope") as Dictionary).duplicate(true)
	bad["weight_kg"] = -1
	var item_schema: Dictionary = reg.schemas["item"]["record"]
	t.check(Schema.validate(bad, item_schema, Callable(reg, "lookup")).size() > 0, "negative weight is rejected")
	# HARD CONTENT RULE 1: crew must be male - enforced by the schema itself
	var crew := {
		"id": "crew_test", "name": "Test Man", "age": 30, "gender": "female", "role": "sailor",
		"sprite": "spr_crew_mannequin_sailor", "loyalty_start": 50,
		"stats": {"strength": 5, "endurance": 5, "seamanship": 5, "fighting": 5, "craft": 5},
	}
	var crew_schema: Dictionary = reg.schemas["crew_member"]["record"]
	var paths := Schema.error_paths(Schema.validate(crew, crew_schema, Callable(reg, "lookup")))
	t.check(paths.has("$.gender"), "female crew record is rejected by the schema")
	crew["gender"] = "male"
	t.check(Schema.validate(crew, crew_schema, Callable(reg, "lookup")).is_empty(), "male crew record passes")
	reg.free()
