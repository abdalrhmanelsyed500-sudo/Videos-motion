extends RefCounted
## The shared environment (H2D-0.2): replays tests/fixtures/env_cases.json made by tools/h2d/env_logic.py (the Python
## twin), checks that the GDScript DEFAULTS match data/tuning/tuning_env.json, and checks the properties that matter for
## the picture: waves keep a zero mean, a calm sea does not slam, the sea builds gradually, rain and wind never jump.
## NOT YET RUN IN GODOT.
const EnvModel := preload("res://h2d/env_model.gd")
const ShipMotion := preload("res://h2d/ship_motion.gd")
const WaveModel := preload("res://h2d/wave_model.gd")
const Ocean := preload("res://core/ocean.gd")
const DataLoader := preload("res://core/data_loader.gd")
const DT := 1.0 / 60.0
const TOL := 0.002


func run(t: Object) -> void:
	var tuning := Ocean.load_tuning()
	_defaults(t, tuning, EnvModel.PREFIX, EnvModel.DEFAULTS)
	_defaults(t, tuning, ShipMotion.PREFIX, ShipMotion.DEFAULTS)
	var fx := DataLoader.load_dict("res://tests/fixtures/env_cases.json")
	var env := EnvModel.new()
	env.configure(tuning)
	for c in fx["classes"]:
		var got := EnvModel.sea_class(float(c["sea"]), env._p)
		t.check(got == str(c["name"]), "sea state %.2f is %s (expected %s)" % [float(c["sea"]), got, str(c["name"])])
	for c in fx["gust"]:
		var n := EnvModel.gust_noise(float(c["t"]))
		t.check(absf(n - float(c["noise"])) < 0.000001, "gust noise at t=%.1f" % float(c["t"]))
	for c in fx["wave"]:
		t.check(absf(WaveModel.crest_bias(float(c["p"])) - float(c["bias"])) < 0.000001, "crest bias p=%.1f" % float(c["p"]))
	_waves(t, fx["wave_build"], tuning)
	for wb in fx["wave_builds"]:
		_waves(t, wb, tuning)
	for tr in fx["env"]:
		_transition(t, tr, tuning)
	for m in fx["motion"]:
		_motion(t, m, tuning)
	_properties(t, tuning)


func _defaults(t: Object, tuning: Dictionary, prefix: String, defaults: Dictionary) -> void:
	for k in defaults.keys():
		var full: String = prefix + str(k)
		t.check(tuning.has(full), "tuning has %s" % full)
		if tuning.has(full):
			t.check(absf(float(tuning[full]) - float(defaults[k])) < 0.000001, "default of %s matches the JSON" % full)


func _waves(t: Object, wb: Dictionary, tuning: Dictionary) -> void:
	var b := WaveModel.build(float(wb["wave_m"]), float(wb["to_deg"]), float(wb["sea"]), float(wb["ice"]),
			float(tuning["env.crest_p_calm"]), float(tuning["env.crest_p_gale"]))
	t.check(absf(float(b["p"]) - float(wb["p"])) < 0.000001, "crest exponent")
	t.check(absf(float(b["bias"]) - float(wb["bias"])) < 0.000001, "crest bias of the build")
	for i in 4:
		for j in 4:
			var want: float = (wb["waves"][i] as Array)[j]
			var got: float = ((b["waves"] as Array)[i] as Array)[j]
			t.check(absf(got - want) < 0.000001, "wave %d component %d" % [i, j])
	for c in wb["heights"]:
		var h := WaveModel.height_b(b, float(c["x"]), float(c["z"]), float(c["t"]))
		t.check(absf(h - float(c["h"])) < 0.0001, "wave height at (%.0f, %.0f, t=%.1f) = %.4f (expected %.4f)" % [
				float(c["x"]), float(c["z"]), float(c["t"]), h, float(c["h"])])


func _transition(t: Object, tr: Dictionary, tuning: Dictionary) -> void:
	var e := EnvModel.new()
	e.configure(tuning)
	e.snap(tr["from_target"])
	var tg: Dictionary = tr["to_target"]
	var tm := 0.0
	var idx := 0
	var samples: Array = tr["samples"]
	var label := "%s -> %s" % [str(tr["from"]), str(tr["to"])]
	for i in samples.size() * 300:
		tm += DT
		e.step(DT, tg, tm)
		if (i + 1) % 300 == 0:
			var s: Dictionary = samples[idx]
			idx += 1
			t.check(absf(e.wind_kn - float(s["wind_kn"])) < TOL, "%s t=%.0f wind" % [label, tm])
			t.check(absf(e.wave_m - float(s["wave_m"])) < TOL, "%s t=%.0f waves" % [label, tm])
			t.check(absf(EnvModel.wrap180(e.wave_to - float(s["wave_to"]))) < 0.01, "%s t=%.0f wave direction" % [label, tm])
			t.check(absf(e.rain - float(s["rain"])) < TOL, "%s t=%.0f rain" % [label, tm])
			t.check(absf(e.sea - float(s["sea"])) < TOL, "%s t=%.0f sea state" % [label, tm])
			t.check(absf(e.gust - float(s["gust"])) < TOL, "%s t=%.0f gust" % [label, tm])
			t.check(absf(e.visibility_km - float(s["visibility_km"])) < 0.01, "%s t=%.0f visibility" % [label, tm])
			t.check(absf(e.adv.x - float(s["adv_x"])) < 0.05 and absf(e.adv.y - float(s["adv_z"])) < 0.05,
					"%s t=%.0f air drift" % [label, tm])


func _motion(t: Object, m: Dictionary, tuning: Dictionary) -> void:
	var e := EnvModel.new()
	e.configure(tuning)
	var tg: Dictionary = m["target"]
	e.snap(tg)
	var mot := ShipMotion.new()
	mot.configure(tuning)
	var tm := float(m["t0"])
	var hd := float(m["heading"])
	var hr := deg_to_rad(hd)
	var f := Vector2(sin(hr), -cos(hr))
	var x := 0.0
	var z := 0.0
	var events := 0
	var idx := 0
	var samples: Array = m["samples"]
	for i in 1200:
		tm += DT
		e.step(DT, tg, tm)
		var b := WaveModel.build(e.wave_vis_m(), e.wave_to, e.sea, 0.0, e.param("crest_p_calm"), e.param("crest_p_gale"))
		x += f.x * float(m["speed_ms"]) * DT
		z += f.y * float(m["speed_ms"]) * DT
		mot.step(DT, b, {"x": x, "z": z, "heading_deg": hd, "t": tm, "wind_to": e.wind_to(), "wind_ms": e.wind_ms(),
				"off_deg": float(m["off_deg"]), "no_go_deg": 40.0, "sea": e.sea})
		events += mot.events.size()
		if (i + 1) % 120 == 0:
			var s: Dictionary = samples[idx]
			idx += 1
			var o := mot.out()
			t.check(absf(float(o["roll_deg"]) - float(s["roll"])) < 0.02, "motion t=%.0f roll %.3f vs %.3f" % [
					tm, float(o["roll_deg"]), float(s["roll"])])
			t.check(absf(float(o["pitch_deg"]) - float(s["pitch"])) < 0.02, "motion t=%.0f pitch" % tm)
			t.check(absf(float(o["heave_m"]) - float(s["heave"])) < 0.01, "motion t=%.0f heave" % tm)
			t.check(events == int(s["events"]), "motion t=%.0f spray events %d vs %d" % [tm, events, int(s["events"])])


## Properties the player sees, independent of the fixture.
func _properties(t: Object, tuning: Dictionary) -> void:
	var env := EnvModel.new()
	env.configure(tuning)
	# the shaped wave still averages zero (flat troughs, peaked crests, no net rise of the sea)
	var b := WaveModel.build(4.0, 90.0, 0.8, 0.0, env.param("crest_p_calm"), env.param("crest_p_gale"))
	var sum := 0.0
	var n := 4000
	for i in n:
		sum += WaveModel.height_b(b, float(i) * 0.37, float(i % 17) * 1.3, 3.0)
	t.check(absf(sum / float(n)) < 0.12, "shaped waves average %.3f m (zero expected)" % (sum / float(n)))
	# a calm sea never slams, a gale heading upwind does, and the same inputs always give the same events
	var calm := _slams(tuning, {"wind_kn": 4.0, "wave_m": 0.35, "rain": 0.0, "storm": 0.0, "fog": 0.05,
			"wind_from_deg": 225.0}, 225.0)
	var gale := _slams(tuning, {"wind_kn": 36.0, "wave_m": 6.0, "rain": 0.8, "storm": 0.7, "fog": 0.15,
			"wind_from_deg": 225.0}, 225.0)
	t.check(calm == 0, "a calm sea makes no spray events (got %d)" % calm)
	t.check(gale >= 8, "a gale head-on makes spray events (got %d in 40 s)" % gale)
	t.check(gale == _slams(tuning, {"wind_kn": 36.0, "wave_m": 6.0, "rain": 0.8, "storm": 0.7, "fog": 0.15,
			"wind_from_deg": 225.0}, 225.0), "spray events are deterministic")
	# build-up is gradual: 5 s after a calm-to-gale change the sea state is still well below its end value
	var e := EnvModel.new()
	e.configure(tuning)
	e.snap({"wind_kn": 4.0, "wave_m": 0.35, "rain": 0.0, "storm": 0.0, "fog": 0.05, "wind_from_deg": 225.0})
	var gale_t := {"wind_kn": 36.0, "wave_m": 6.0, "rain": 0.8, "storm": 0.7, "fog": 0.15, "wind_from_deg": 225.0}
	for i in 300:
		e.step(DT, gale_t, float(i) * DT)
	t.check(e.wave_m < 3.0, "5 s into a calm-to-gale change the waves are %.2f m (still building)" % e.wave_m)
	for i in 3300:
		e.step(DT, gale_t, 5.0 + float(i) * DT)
	t.check(e.wave_m > 5.0, "after a minute the waves have built to %.2f m" % e.wave_m)
	t.check(e.sea_name() == "Gale" or e.sea_name() == "Storm", "the sea state reads %s after a minute" % e.sea_name())
	# rain is a function of the environment only: no rain target, no rain
	var dry := EnvModel.new()
	dry.configure(tuning)
	dry.snap({"wind_kn": 12.0, "wave_m": 1.0, "rain": 0.0, "storm": 0.0, "fog": 0.0, "wind_from_deg": 0.0})
	t.check(dry.rain_inst == 0.0, "no rain without rain")


func _slams(tuning: Dictionary, tgt: Dictionary, heading: float) -> int:
	var e := EnvModel.new()
	e.configure(tuning)
	e.snap(tgt)
	var m := ShipMotion.new()
	m.configure(tuning)
	var hr := deg_to_rad(heading)
	var f := Vector2(sin(hr), -cos(hr))
	var x := 0.0
	var z := 0.0
	var tm := 100.0
	var count := 0
	for i in 2400:
		tm += DT
		e.step(DT, tgt, tm)
		var b := WaveModel.build(e.wave_vis_m(), e.wave_to, e.sea, 0.0, e.param("crest_p_calm"), e.param("crest_p_gale"))
		x += f.x * 24.7 * DT
		z += f.y * 24.7 * DT
		m.step(DT, b, {"x": x, "z": z, "heading_deg": heading, "t": tm, "wind_to": e.wind_to(), "wind_ms": e.wind_ms(),
				"off_deg": 0.0, "no_go_deg": 40.0, "sea": e.sea})
		count += m.events.size()
	return count
