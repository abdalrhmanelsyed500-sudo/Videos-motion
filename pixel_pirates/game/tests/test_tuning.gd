extends RefCounted
const Tuning := preload("res://core/tuning.gd")
## Difficulty scaling of tuning values.


func run(t: Object) -> void:
	var reg: Node = load("res://core/registry.gd").new()
	reg.load_all()
	var normal: RefCounted = Tuning.from_registry(reg, "mode_normal")
	var story: RefCounted = Tuning.from_registry(reg, "mode_story")
	var hard: RefCounted = Tuning.from_registry(reg, "mode_hardcore")
	var k := "food.need_kcal_per_man_day"
	t.check(is_equal_approx(normal.f(k), 3200.0), "normal: base value")
	t.check(is_equal_approx(story.f(k), 1600.0), "story: x0.5")
	t.check(is_equal_approx(hard.f(k), 4000.0), "hardcore: x1.25")
	var d := "health.scurvy_onset_days_no_vitc"
	t.check(is_equal_approx(normal.f(d), 70.0), "scurvy base 70 days")
	t.check(is_equal_approx(hard.f(d), 50.0), "hardcore scurvy comes sooner (div by 1.4)")
	t.check(is_equal_approx(story.f(d), 140.0), "story scurvy comes later (div by 0.5)")
	t.check(is_equal_approx(hard.f("crew.watch_length_hours"), 4.0), "unscaled key ignores difficulty")
	# per-system toning: hardcore realism, but food needs eased back to normal
	var toned: RefCounted = Tuning.from_registry(reg, "mode_hardcore", {"hunger_rate": 1.0})
	t.check(is_equal_approx(toned.f(k), 3200.0), "per-system override beats the mode")
	t.check(is_equal_approx(toned.f("water.need_l_per_man_day_min"), 2.5 * 1.25), "other systems keep the mode value")
	t.check(hard.as_int("crew.awake_limit_hours") == 13, "integer helper rounds (16 / 1.25 = 12.8 -> 13)")
	reg.free()
