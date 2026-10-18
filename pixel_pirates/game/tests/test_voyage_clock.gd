extends RefCounted
## Time arithmetic (patch T1). Same fixture file as tools/data_tools/test_design_checks.py: the GDScript
## functions must give the same answers. Also checks day/night boundaries and smoothness, and that the
## code defaults equal the tuning records.
const VoyageClock := preload("res://core/voyage_clock.gd")
const WorldClock := preload("res://core/world_clock.gd")
const DataLoader := preload("res://core/data_loader.gd")
const Tuning := preload("res://core/tuning.gd")
const STARTS: Array = [5.0, 7.0, 10.0, 17.0, 19.0, 20.0]


func run(t: Object) -> void:
	_fixture(t)
	_bands(t)
	_smoothness(t)
	_defaults_match_tuning(t)


func _fixture(t: Object) -> void:
	var fx := DataLoader.load_dict("res://tests/fixtures/clock_cases.json")
	var cases: Array = fx.get("cases", [])
	t.check(cases.size() >= 90, "clock fixture has >= 90 cases (has %d)" % cases.size())
	for c in cases:
		var got: Variant = VoyageClock.call_case(str(c["fn"]), c["args"])
		var want: Variant = c["expect"]
		var ok := false
		if typeof(want) == TYPE_STRING:
			ok = str(got) == str(want)
		elif typeof(want) == TYPE_DICTIONARY:
			ok = _weights_match(got, want)
		else:
			ok = got != null and absf(float(got) - float(want)) < 0.000001
		t.check(ok, "clock %s%s: expected %s, got %s" % [c["fn"], c["args"], want, got])
	t.check(VoyageClock.WATCH_NAMES.size() * 4 == 24, "six watches of four hours make a day")


func _weights_match(got: Variant, want: Dictionary) -> bool:
	if typeof(got) != TYPE_DICTIONARY:
		return false
	var total := 0.0
	for k in VoyageClock.BAND_NAMES:
		total += float(got[k])
		if absf(float(got[k]) - float(want.get(k, 0.0))) > 0.000001:
			return false
	return absf(total - 1.0) < 0.000000001


func _bands(t: Object) -> void:
	var seen := {}
	var lengths := {}
	for i in range(2400):
		var b := VoyageClock.band_of_hour(float(i) / 100.0, STARTS)
		seen[b] = true
		lengths[b] = float(lengths.get(b, 0.0)) + 0.01
	t.check(seen.size() == 6, "every one of the six bands occurs in a day")
	var want := {"dawn": 2.0, "morning": 3.0, "day": 7.0, "sunset": 2.0, "evening": 1.0, "night": 9.0}
	for k in want.keys():
		t.check(absf(float(lengths[k]) - float(want[k])) < 0.0001, "band %s lasts %s game hours" % [k, want[k]])
	var band := func(h: float) -> String: return VoyageClock.band_of_hour(h, STARTS)
	t.check(band.call(4.999) == "night" and band.call(5.0) == "dawn", "night ends and dawn begins at 05:00")
	t.check(band.call(19.999) == "evening" and band.call(20.0) == "night", "night begins at 20:00")
	t.check(band.call(30.0) == "dawn" and band.call(-1.0) == "night", "hours wrap")


func _smoothness(t: Object) -> void:
	var max_step := 0.0
	var max_wstep := 0.0
	var lo := 9.0
	var hi := -9.0
	var prev := VoyageClock.daylight(0.0, STARTS, 0.04, 0.55, 0.3)
	var prev_w := VoyageClock.band_weights(0.0, STARTS)
	for i in range(1, 2401):
		var h := float(i) / 100.0
		var d := VoyageClock.daylight(h, STARTS, 0.04, 0.55, 0.3)
		max_step = maxf(max_step, absf(d - prev))
		lo = minf(lo, d)
		hi = maxf(hi, d)
		prev = d
		var w := VoyageClock.band_weights(h, STARTS)
		for k in VoyageClock.BAND_NAMES:
			max_wstep = maxf(max_wstep, absf(float(w[k]) - float(prev_w[k])))
		prev_w = w
	t.check(max_step < 0.01, "daylight never jumps (max step per 0.01 h = %s)" % max_step)
	t.check(max_wstep < 0.01, "band weights never jump (max step per 0.01 h = %s)" % max_wstep)
	t.check(lo >= 0.04 - 0.000001 and hi <= 1.000001, "daylight stays between the night floor and 1")
	var at_zero := VoyageClock.daylight(0.0, STARTS, 0.04, 0.55, 0.3)
	var wrap_gap := absf(at_zero - VoyageClock.daylight(23.9999, STARTS, 0.04, 0.55, 0.3))
	t.check(wrap_gap < 0.001, "daylight wraps cleanly at midnight")
	t.check(VoyageClock.daylight(12.0, STARTS, 0.04, 0.55, 0.3) == 1.0, "full daylight at noon")


## The code defaults must equal the tuning records, so a changed tuning number cannot silently disagree with the code.
func _defaults_match_tuning(t: Object) -> void:
	var reg: Node = load("res://core/registry.gd").new()
	reg.load_all()
	var tun: RefCounted = Tuning.from_registry(reg, "mode_normal")
	var rate_key := "time.real_minutes_per_game_day"
	t.check(is_equal_approx(WorldClock.DEFAULT_MINUTES_PER_DAY, tun.f(rate_key)), "WorldClock default rate = tuning")
	t.check(is_equal_approx(WorldClock.DEFAULT_MINUTES_PER_DAY, 15.0), "the decided rate is 15 real minutes per game day")
	var keys: Array[String] = ["dawn", "morning", "day", "sunset", "evening", "night"]
	for i in range(6):
		var tuned: float = tun.f("time.%s_start_hour" % keys[i])
		t.check(is_equal_approx(VoyageClock.DEFAULT_STARTS[i], tuned), "band start %s = tuning" % keys[i])
	t.check(is_equal_approx(VoyageClock.DEFAULT_REPORT_HOUR, tun.f("time.report_hour")), "report hour = tuning")
	var hard: RefCounted = Tuning.from_registry(reg, "mode_hardcore")
	var story: RefCounted = Tuning.from_registry(reg, "mode_story")
	var same_day: bool = is_equal_approx(hard.f(rate_key), 15.0) and is_equal_approx(story.f(rate_key), 15.0)
	t.check(same_day, "no difficulty mode changes the day length")
	t.check(is_equal_approx(hard.f("time.night_start_hour"), 20.0), "no difficulty mode moves the bands")
	reg.free()
