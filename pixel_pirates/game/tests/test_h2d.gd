extends RefCounted
## H2D-0 pure logic: sprite frame and sail trim selection, sea scale, wave model (replays the Python twin's fixture),
## lighting model ranges. NOT YET RUN IN GODOT.
const ShipSprite := preload("res://h2d/ship_sprite.gd")
const WaveModel := preload("res://h2d/wave_model.gd")
const LightModel := preload("res://h2d/light_model.gd")
const DataLoader := preload("res://core/data_loader.gd")
const Ocean := preload("res://core/ocean.gd")
const TOL := 0.0001


func run(t: Object) -> void:
	var fx := DataLoader.load_dict("res://tests/fixtures/ship_sprite_cases.json")
	for c in fx["frames"]:
		var got := ShipSprite.heading_frame(float(c["heading"]))
		t.check(got == int(c["frame"]), "heading %s -> frame %d (expected %d)" % [c["heading"], got, int(c["frame"])])
	for c in fx["trims"]:
		var got := ShipSprite.trim_row(float(c["heading"]), float(c["wind_from"]))
		t.check(got == int(c["row"]), "trim heading %s wind %s -> %d (expected %d)" % [
				c["heading"], c["wind_from"], got, int(c["row"])])
	for c in fx["speeds"]:
		var got := ShipSprite.scene_speed_ms(float(c["kn"]))
		t.check(absf(got - float(c["scene_ms"])) < TOL, "scene speed %s kn = %.4f" % [c["kn"], got])
	for c in fx["waves"]:
		var p := WaveModel.params(float(c["wave_m"]), float(c["wind_from"]), float(c["ice"]))
		for q in c["points"]:
			var h := WaveModel.height(p, float(q["x"]), float(q["z"]), float(q["t"]))
			t.check(absf(h - float(q["h"])) < TOL, "wave %.1f m at (%s, %s, t=%s): %.5f vs %.5f" % [
					float(c["wave_m"]), q["x"], q["z"], q["t"], h, float(q["h"])])
	_check_rules(t)
	_check_light(t)


func _check_rules(t: Object) -> void:
	t.check(ShipSprite.trim_row(90.0, 270.0) == 0 or ShipSprite.trim_row(90.0, 270.0) == 4, "running: boom well out")
	t.check(ShipSprite.trim_row(0.0, 0.0) == 2, "head to wind: boom centred")
	t.check(ShipSprite.trim_row(0.0, 90.0) == 1, "wind on the starboard beam: boom to port")
	t.check(ShipSprite.trim_row(0.0, 270.0) == 3, "wind on the port beam: boom to starboard")
	t.check(absf(ShipSprite.scene_speed_ms(5.0) - 24.69) < 0.05, "5 kn is about 24.7 scene m/s")


func _view(hour: float, storm: float) -> Dictionary:
	var oc: RefCounted = Ocean.load_default()
	return {"light": 1.0 if hour > 6.0 and hour < 18.0 else 0.1, "floor": 0.1, "hour": hour, "lat": 10.0, "cloud": 0.2,
			"storm": storm, "fog": 0.0, "ice": 0.0, "visibility_km": 20.0, "wind_from_deg": 270.0, "wave_m": 2.0,
			"look": oc.look_at(7000.0, 2650.0)}


func _check_light(t: Object) -> void:
	var day := LightModel.compute(_view(12.0, 0.0))
	var night := LightModel.compute(_view(0.0, 0.0))
	var storm := LightModel.compute(_view(12.0, 0.9))
	var sd: Vector3 = day["sun_dir"]
	t.check(absf(sd.length() - 1.0) < 0.001 and sd.y > 0.5, "noon sun is high and normalised")
	var key_day: float = (day["sun_col"] as Vector3).length()
	t.check((night["sun_col"] as Vector3).length() < key_day, "night key is dimmer")
	t.check((storm["sun_col"] as Vector3).length() < key_day, "storm key is dimmer")
	t.check(float(day["fog_density"]) >= LightModel.HAZE_BASE, "fog never below the base haze")
	var east := LightModel.sun(6.5, 10.0)["dir"] as Vector3
	var west := LightModel.sun(17.5, 10.0)["dir"] as Vector3
	t.check(east.x > 0.3 and west.x < -0.3, "sun rises in the east and sets in the west")
	t.check(LightModel.flash(3.0, 0.2) == 0.0, "no lightning in fair weather")
