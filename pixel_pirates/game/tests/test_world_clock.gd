extends RefCounted
## The ONE world clock (patch T1): time conversion, pause behaviour, sea/island continuity.
## Scenarios are hand-calculated in tests/fixtures/clock_scenarios.json and shared with
## tools/data_tools/test_design_checks.py.
const VoyageClock := preload("res://core/voyage_clock.gd")
const WorldClock := preload("res://core/world_clock.gd")
const DataLoader := preload("res://core/data_loader.gd")
const RATION_KG_PER_DAY := 5.4  # 12 men x 0.45 kg hardtack (tuning food.hardtack_kg_per_man_day)


func run(t: Object) -> void:
	_scenarios(t)
	_conversion(t)
	_pause(t)
	_continuity(t)


func _scenarios(t: Object) -> void:
	var fx := DataLoader.load_dict("res://tests/fixtures/clock_scenarios.json")
	var scs: Array = fx.get("scenarios", [])
	t.check(scs.size() >= 4, "clock scenario fixture has >= 4 scenarios (has %d)" % scs.size())
	for sc in scs:
		var clk := WorldClock.new(float(sc.get("minutes_per_day", 15.0)), float(sc.get("start_t", 0.0)))
		var n := 0
		for st in sc["steps"]:
			var dt := -1.0
			match str(st["op"]):
				"tick":
					dt = clk.tick(float(st["dt"]))
				"pause":
					clk.pause(str(st["reason"]))
				"resume":
					clk.resume(str(st["reason"]))
				"where":
					clk.set_location(str(st["place"]))
			_expect_step(t, clk, st, dt, "%s step %d" % [sc["name"], n])
			n += 1


func _expect_step(t: Object, clk: RefCounted, st: Dictionary, dt: float, label: String) -> void:
	if st.has("expect_dt"):
		t.check(absf(dt - float(st["expect_dt"])) < 0.000001, "%s: dt expected %s, got %s" % [label, st["expect_dt"], dt])
	if st.has("expect_t"):
		t.check(absf(clk.t - float(st["expect_t"])) < 0.000001, "%s: t expected %s, got %s" % [label, st["expect_t"], clk.t])
	if st.has("expect_paused"):
		t.check(clk.is_paused() == bool(st["expect_paused"]), "%s: paused expected %s" % [label, st["expect_paused"]])
	if st.has("expect_hour"):
		var msg := "%s: hour expected %s, got %s" % [label, st["expect_hour"], clk.hour()]
		t.check(absf(clk.hour() - float(st["expect_hour"])) < 0.000001, msg)
	if st.has("expect_day"):
		t.check(clk.day() == int(st["expect_day"]), "%s: day expected %s, got %s" % [label, st["expect_day"], clk.day()])


func _conversion(t: Object) -> void:
	var clk := WorldClock.new()
	t.check(is_equal_approx(clk.game_seconds_per_real_second(), 96.0), "1 real second = 96 game seconds at 15 min/day")
	t.check(is_equal_approx(VoyageClock.hours_to_real_seconds(1.0, 15.0), 37.5), "1 game hour = 37.5 real seconds")
	t.check(is_equal_approx(VoyageClock.hours_to_real_seconds(4.0, 15.0), 150.0), "a 4 h watch = 150 real seconds")
	t.check(is_equal_approx(VoyageClock.hours_to_real_seconds(0.5, 15.0), 18.75), "a half-hour bell = 18.75 real s")
	t.check(is_equal_approx(VoyageClock.hours_to_real_seconds(24.0, 15.0), 900.0), "1 game day = 900 real seconds")
	t.check(is_equal_approx(VoyageClock.real_seconds_to_hours(900.0, 15.0), 24.0), "900 real seconds = 24 game hours")
	var steps := 0
	while steps < 900:
		clk.tick(1.0)
		steps += 1
	var one_day: bool = is_equal_approx(clk.t, 86400.0) and clk.day() == 2 and is_equal_approx(clk.hour(), 0.0)
	t.check(one_day, "900 one-second ticks make exactly one day")
	var odd := WorldClock.new()
	for i in range(1000):
		odd.tick(0.9)
	t.check(absf(odd.t - 900.0 * 96.0) < 0.001, "the frame rate does not matter: 1000 ticks of 0.9 s = 900 s of game")


func _pause(t: Object) -> void:
	var clk := WorldClock.new()
	var used := 0.0
	for i in range(900):
		used += RATION_KG_PER_DAY * clk.tick(1.0) / 86400.0
	t.check(absf(used - RATION_KG_PER_DAY) < 0.000001, "one real quarter-hour consumes exactly one day of rations")
	var before := used
	var t_before := clk.t
	clk.pause("report")
	for i in range(600):
		used += RATION_KG_PER_DAY * clk.tick(1.0) / 86400.0
	t.check(used == before and clk.t == t_before, "ten paused real minutes consume nothing and move no clock")
	clk.pause("planning")
	clk.resume("report")
	t.check(clk.tick(30.0) == 0.0 and clk.is_paused(), "a second pause reason keeps time stopped")
	clk.pause("planning")
	t.check(clk.pause_reasons().size() == 1, "pausing for the same reason twice is idempotent")
	clk.resume("planning")
	t.check(not clk.is_paused() and absf(clk.tick(30.0) - 2880.0) < 0.000001, "resuming restarts at the same rate")
	t.check(clk.tick(-3.0) == 0.0 and clk.tick(0.0) == 0.0, "a zero or negative delta does nothing")
	clk.resume("never_paused")
	t.check(not clk.is_paused(), "resuming an unheld reason is harmless")


func _continuity(t: Object) -> void:
	var clk := WorldClock.new()
	var worst := 0.0
	for i in range(300):
		clk.set_location("sea" if i % 100 < 50 else "island")
		var before := clk.t
		var dt := clk.tick(1.0)
		worst = maxf(worst, absf(dt - 96.0))
		worst = maxf(worst, absf((clk.t - before) - 96.0))
	t.check(worst < 0.000001, "every tick is 96 game seconds on both sides of a landfall")
	var sea := WorldClock.new()
	var shore := WorldClock.new()
	shore.set_location("island")
	for i in range(100):
		sea.tick(0.37)
		shore.tick(0.37)
	t.check(absf(sea.t - shore.t) < 0.000001, "the same real time gives the same game time at sea and ashore")
	var jump := WorldClock.new(15.0, 5000.0)
	jump.set_location("island")
	jump.set_location("sea")
	t.check(jump.t == 5000.0, "changing location never moves the clock")
	var mid := WorldClock.new(15.0, 86000.0)
	mid.tick(5.0)
	t.check(mid.day() == 2 and absf(mid.t - 86480.0) < 0.000001, "the clock runs on across midnight")
