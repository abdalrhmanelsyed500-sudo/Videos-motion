extends RefCounted
## The sail (H2D-0.3): replays tests/fixtures/sail_cases.json made by tools/h2d/sail_logic.py (the Python twin), checks
## that SailModel.DEFAULTS and WeatherLook.DEFAULTS match data/tuning/tuning_env.json, and checks the properties that
## the picture depends on: a steady sail does not flutter, a luffing one does, a gale sail is taut and flat, and the
## boom does not flick between two drawings at a switch angle. NOT YET RUN IN GODOT.
const SailModel := preload("res://h2d/sail_model.gd")
const WeatherLook := preload("res://h2d/weather_look.gd")
const ShipSprite := preload("res://h2d/ship_sprite.gd")
const EnvModel := preload("res://h2d/env_model.gd")
const Ocean := preload("res://core/ocean.gd")
const DataLoader := preload("res://core/data_loader.gd")
const DT := 1.0 / 60.0
const TOL := 0.01


func run(t: Object) -> void:
	var tuning := Ocean.load_tuning()
	_defaults(t, tuning, SailModel.PREFIX, SailModel.DEFAULTS)
	_defaults(t, tuning, WeatherLook.PREFIX, WeatherLook.DEFAULTS)
	var fx := DataLoader.load_dict("res://tests/fixtures/sail_cases.json")
	for c in fx["cases"]:
		_replay(t, c, tuning)
	_properties(t, tuning)
	_trim(t)
	_look(t, tuning)


func _defaults(t: Object, tuning: Dictionary, prefix: String, defaults: Dictionary) -> void:
	for k in defaults.keys():
		var full: String = prefix + str(k)
		t.check(tuning.has(full), "tuning has %s" % full)
		if tuning.has(full):
			t.check(absf(float(tuning[full]) - float(defaults[k])) < 0.000001, "default of %s matches the JSON" % full)


func _replay(t: Object, c: Dictionary, tuning: Dictionary) -> void:
	var s := SailModel.new()
	s.configure(tuning)
	var gk := float(c["gustiness"])
	var wk := float(c["wind_kn"])
	var t0 := float(c["t0"])
	var idx := 0
	for i in 1800:
		var tt := t0 + float(i + 1) * DT
		var g := smoothstep(0.60, 0.92, EnvModel.gust_noise(tt)) * gk
		s.step(DT, wk * (1.0 + 0.45 * g), g, float(c["off_deg"]), 40.0, tt)
		if (i + 1) % 150 == 0:
			var want: Dictionary = c["samples"][idx]
			idx += 1
			var o := s.out()
			for key in ["belly", "flap", "luff", "fill", "slack"]:
				var got: float = float(o[{"belly": "belly_px", "flap": "flap_px"}.get(key, key)])
				t.check(absf(got - float(want[key])) < TOL, "%s at t=%.1f: %s %.3f (expected %.3f)" % [
						str(c["name"]), tt, key, got, float(want[key])])
			var dphase := absf(float(o["flap_phase"]) - float(want["phase"]))
			t.check(dphase < 0.05, "%s flutter phase at t=%.1f" % [str(c["name"]), tt])


func _run_sail(tuning: Dictionary, seconds: float, wind: float, off: float) -> Dictionary:
	var s := SailModel.new()
	s.configure(tuning)
	var max_flap := 0.0
	var steps := 0
	var prev := 0
	for i in int(seconds / DT):
		var tt := 30.0 + float(i) * DT
		s.step(DT, wind, 0.0, off, 40.0, tt)
		var o := s.out()
		max_flap = maxf(max_flap, float(o["flap_px"]))
		var disp := int(floorf(float(o["belly_px"]) + float(o["flap_px"]) * sin(float(o["flap_phase"])) + 0.5))
		if i > 600 and disp != prev:
			steps += 1
		prev = disp
	return {"max_flap": max_flap, "steps_per_s": float(steps) / (seconds - 10.0), "belly": float(s.out()["belly_px"])}


func _properties(t: Object, tuning: Dictionary) -> void:
	var calm := _run_sail(tuning, 60.0, 4.0, 90.0)
	var breezy := _run_sail(tuning, 60.0, 14.0, 90.0)
	var gale := _run_sail(tuning, 60.0, 36.0, 90.0)
	var irons := _run_sail(tuning, 60.0, 14.0, 20.0)
	var calm_steps := float(calm["steps_per_s"])
	t.check(calm_steps < 0.5, "a calm sail changes pixel less than once per 2 s (%.2f/s)" % calm_steps)
	t.check(float(breezy["steps_per_s"]) < 1.0, "a filled breezy sail is steady (%.2f/s)" % float(breezy["steps_per_s"]))
	t.check(float(irons["max_flap"]) > 0.8, "a luffing sail with wind in it flutters")
	t.check(float(irons["steps_per_s"]) > float(breezy["steps_per_s"]), "luffing is livelier than a drawing sail")
	t.check(float(breezy["belly"]) > float(calm["belly"]) + 1.0, "a breeze fills the sail much more than a calm")
	t.check(float(gale["belly"]) < float(breezy["belly"]), "a gale sail is flatter than a breezy one")
	t.check(float(breezy["belly"]) < 2.6, "the belly never exceeds about 2 pixels")


func _trim(t: Object) -> void:
	var row := 2
	var changes := 0
	for i in 400:
		# the wind angle wobbles by +-4 degrees around the 50 degree switch point
		var rel := 50.0 + 4.0 * sin(float(i) * 0.4)
		var r := ShipSprite.trim_row_sticky(0.0, rel, row)
		if r != row:
			changes += 1
		row = r
	t.check(changes <= 1, "the boom does not flick at the 50 degree switch (%d changes)" % changes)
	t.check(ShipSprite.trim_row_sticky(0.0, 90.0, 2) == 1, "wind on the starboard beam: boom eased to port")
	t.check(ShipSprite.trim_row_sticky(0.0, -90.0, 2) == 3, "wind on the port beam: boom eased to starboard")
	t.check(ShipSprite.trim_row_sticky(0.0, 20.0, 1) == 2, "close-hauled: boom amidships")
	t.check(ShipSprite.trim_row_sticky(0.0, 170.0, 1) == 0, "running: boom well out")


func _look(t: Object, tuning: Dictionary) -> void:
	var wl := WeatherLook.new()
	wl.configure(tuning)
	t.check(WeatherLook.overcast(0.1, 0.0, 0.0, 0.0) < 0.01, "clear sky is not overcast")
	t.check(WeatherLook.overcast(0.2, 0.8, 0.0, 0.0) > 0.7, "heavy rain is overcast")
	t.check(WeatherLook.overcast(0.2, 0.0, 0.0, 0.7) > 0.5, "fog is overcast")
	t.check(WeatherLook.overcast(0.0, 0.0, 1.0, 0.0) > 0.99, "a storm is fully overcast")
	t.check(wl.fog_start_m(0.05) > wl.fog_start_m(0.7), "thick fog starts closer than light haze")
	t.check(absf(wl.fog_start_m(0.05) - WeatherLook.FOG_START_BASE_M) < 0.5, "light haze keeps the normal fog start")
	var drizzle := wl.rain_character(0.15)
	var downpour := wl.rain_character(0.9)
	t.check(float(drizzle["streak_m"]) < float(downpour["streak_m"]), "drizzle streaks are shorter than a downpour's")
	t.check(float(drizzle["fall_ms"]) < float(downpour["fall_ms"]), "drizzle falls slower")
