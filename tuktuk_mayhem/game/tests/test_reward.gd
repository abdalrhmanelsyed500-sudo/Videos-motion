extends RefCounted
## Pure reward maths from data tuning: monotonicity, cap, floor, penalties, breakdown sum.


func run(t) -> void:
	var mm := load("res://scripts/core/mission_mgr.gd") as GDScript
	var tune := {"base_fare": 8.0, "per_m": 0.055, "time_left_rate": 0.35, "clean_drive_bonus": 6.0,
		"shortcut_bonus": 5.0, "collision_penalty": 2.5, "reward_cap": 120.0}
	var a: float = mm.compute_reward(100.0, 10.0, 0, false, tune)
	var b: float = mm.compute_reward(200.0, 10.0, 0, false, tune)
	t.check(b > a, "longer trip pays more (%f vs %f)" % [b, a])
	var c: float = mm.compute_reward(100.0, 30.0, 0, false, tune)
	t.check(c > a, "more time left pays more (%f vs %f)" % [c, a])
	var d: float = mm.compute_reward(100.0, 10.0, 3, false, tune)
	t.check(d < a, "collisions reduce pay (%f vs %f)" % [d, a])
	var e: float = mm.compute_reward(100.0, 10.0, 0, true, tune)
	t.check(e > a, "shortcut bonus pays (%f vs %f)" % [e, a])
	var cap: float = mm.compute_reward(100000.0, 100000.0, 0, true, tune)
	t.check(is_equal_approx(cap, 120.0), "cap enforced (%f)" % cap)
	var floor_v: float = mm.compute_reward(1.0, 0.0, 99, false, tune)
	t.check(floor_v >= 0.0, "never negative (%f)" % floor_v)
	var br: Dictionary = mm.compute_breakdown(120.0, 15.0, 1, true, tune)
	var total: float = float(br["base"]) + float(br["distance"]) + float(br["time_left"])
	total += float(br["clean"]) + float(br["shortcut"]) - float(br["penalty"])
	t.check(abs(total - float(br["total"])) < 1e-6, "breakdown sums to total")
	t.check(float(br["clean"]) == 0.0, "no clean bonus with a collision")
