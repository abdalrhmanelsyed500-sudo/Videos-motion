extends RefCounted
## Ocean model and wildlife (Module E1). Replays the golden files produced by the Python twin
## (tests/fixtures/ocean_cases.json and wildlife_cases.json), then checks the properties that make the sea honest:
## pure and repeatable, the Herald Swell is tomorrow's gale, regions blend smoothly, ships obey the wind, and the
## slice route's checkpoints keep their promises. THIS FILE HAS NOT BEEN RUN IN GODOT YET (see docs/E1_WORLD_SPEC.md).
const Ocean := preload("res://core/ocean.gd")
const Wildlife := preload("res://core/wildlife.gd")
const DataLoader := preload("res://core/data_loader.gd")
const TOL := 0.0001


func run(t: Object) -> void:
	var oc: RefCounted = Ocean.load_default()
	t.check(oc.regions.size() == 10, "ocean loads 10 regions (has %d)" % oc.regions.size())
	t.check(oc.bands.size() == 6, "ocean loads 6 climate bands (has %d)" % oc.bands.size())
	var fx := DataLoader.load_dict("res://tests/fixtures/ocean_cases.json")
	_noise(t, fx.get("noise", {}))
	_light_and_wind(t, oc, fx)
	_samples(t, oc, fx.get("samples", []))
	_speeds(t, oc, fx.get("speeds", []))
	_bergs_and_looks(t, oc, fx)
	_properties(t, oc)
	_route(t, oc)
	_wildlife(t, oc)


func _near(a: float, b: float) -> bool:
	return absf(a - b) <= TOL * maxf(1.0, absf(b))


func _noise(t: Object, nz: Dictionary) -> void:
	var hs: Array = nz.get("hash", [])
	t.check(hs.size() >= 12, "noise fixture has hash cases")
	for c in hs:
		var a: Array = c["a"]
		var got: float = Ocean.hash01(int(a[0]), int(a[1]), int(a[2]), int(a[3]))
		t.check(_near(got, float(c["v"])), "hash01%s expected %s got %s" % [a, c["v"], got])
	for c in nz.get("vnoise", []):
		var a: Array = c["a"]
		var got: float = Ocean.vnoise(float(a[0]), float(a[1]), float(a[2]), int(a[3]))
		t.check(_near(got, float(c["v"])), "vnoise%s expected %s got %s" % [a, c["v"], got])
	for c in nz.get("fbm", []):
		var a: Array = c["a"]
		var got: float = Ocean.fbm(float(a[0]), float(a[1]), float(a[2]), int(a[3]))
		t.check(_near(got, float(c["v"])), "fbm%s expected %s got %s" % [a, c["v"], got])


func _light_and_wind(t: Object, oc: RefCounted, fx: Dictionary) -> void:
	for c in fx.get("light", []):
		var a: Array = c["a"]
		var got: Array = oc.light_limits(float(a[0]), float(a[1]))
		var ok: bool = _near(float(got[0]), float(c["v"][0])) and _near(float(got[1]), float(c["v"][1]))
		t.check(ok, "light_limits%s expected %s got %s" % [a, c["v"], got])
	for c in fx.get("winds", []):
		var got: Array = oc.base_wind(float(c["a"][0]))
		var ok := true
		for i in 3:
			ok = ok and _near(float(got[i]), float(c["v"][i]))
		t.check(ok, "base_wind(%s) expected %s got %s" % [c["a"][0], c["v"], got])


func _samples(t: Object, oc: RefCounted, samples: Array) -> void:
	t.check(samples.size() >= 40, "sample fixture has >= 40 points (has %d)" % samples.size())
	for c in samples:
		var s: Dictionary = oc.sample(float(c["x"]), float(c["y"]), float(c["t"]))
		var where := "(%s, %s, t=%s)" % [c["x"], c["y"], c["t"]]
		t.check(str(s["region"]) == str(c["region"]), "region at %s expected %s got %s" % [where, c["region"], s["region"]])
		var bad: Array = []
		var want: Dictionary = c["v"]
		for k in want.keys():
			if not _near(float(s[k]), float(want[k])):
				bad.append("%s want %s got %s" % [k, want[k], s[k]])
		t.check(bad.is_empty(), "sample at %s differs: %s" % [where, ", ".join(bad)])
		var w: PackedFloat64Array = s["weights"]
		var wbad := false
		for i in w.size():
			if not _near(w[i], float(c["w"][i])):
				wbad = true
		t.check(not wbad, "region weights at %s differ" % where)


func _speeds(t: Object, oc: RefCounted, speeds: Array) -> void:
	t.check(speeds.size() >= 20, "speed fixture has >= 20 cases")
	for c in speeds:
		var a: Array = c["a"]
		var got: float = oc.speed_through_water_kmh(float(a[0]), float(a[1]), float(a[2]), float(a[3]))
		t.check(_near(got, float(c["v"])), "speed%s expected %s got %s" % [a, c["v"], got])


func _bergs_and_looks(t: Object, oc: RefCounted, fx: Dictionary) -> void:
	for c in fx.get("bergs", []):
		var a: Array = c["a"]
		var got: Array = oc.bergs_near(float(a[0]), float(a[1]), float(a[2]))
		var want: Array = c["v"]
		var ok: bool = got.size() == want.size()
		if ok:
			for i in got.size():
				ok = ok and _near(float(got[i][0]), float(want[i][0])) and _near(float(got[i][1]), float(want[i][1]))
				ok = ok and int(got[i][2]) == int(want[i][2])
		t.check(ok, "bergs_near%s expected %d bergs, got %d" % [a, want.size(), got.size()])
	for c in fx.get("looks", []):
		var a: Array = c["a"]
		var got: Dictionary = oc.look_at(float(a[0]), float(a[1]))
		var ok := true
		for k in (c["v"] as Dictionary).keys():
			var want: Variant = c["v"][k]
			if want is Array:
				for i in 3:
					ok = ok and _near(float(got[k][i]), float(want[i]))
			else:
				ok = ok and _near(float(got[k]), float(want))
		t.check(ok, "look_at%s differs from the golden values" % [a])


func _properties(t: Object, oc: RefCounted) -> void:
	var a: Dictionary = oc.sample(5600.0, 520.0, 12.5)
	var b: Dictionary = oc.sample(5600.0, 520.0, 12.5)
	t.check(a["wind_kn"] == b["wind_kn"] and a["storm"] == b["storm"], "sample is a pure function (no hidden state)")
	var lead: float = oc.tuning_value("ocean.herald_lead_days")
	var honest := true
	for k in 40:
		var x: float = Ocean.hash01(k, 1, 0, 12) * oc.world_w
		var y: float = Ocean.hash01(k, 2, 0, 12) * oc.world_h
		var d: float = Ocean.hash01(k, 3, 0, 12) * 70.0
		var h: float = oc.sample(x, y, d)["herald"]
		var st: float = oc.sample(x, y, d + lead)["storm"]
		if absf(h - st) > 0.000000001:
			honest = false
	t.check(honest, "Herald Swell: herald(t) equals storm(t + 1 game day) everywhere")
	var rim_ok: bool = oc.edge_rim(0.0, 3000.0) == 1.0 and oc.edge_rim(4500.0, 3000.0) == 0.0
	t.check(rim_ok, "the Rim is weather at the edge, zero inside")
	var lat_ok: bool = absf(oc.lat(3000.0)) < 0.000001 and absf(oc.lat(0.0) - 75.0) < 0.000001
	t.check(lat_ok, "latitude: equator at y = 3000, pole at the edge")
	var eq_ok := true
	for k in 20:
		var lim: Array = oc.light_limits(0.0, float(k) / 20.0)
		eq_ok = eq_ok and absf(float(lim[0]) - 1.0) < 0.000000001 and absf(float(lim[1])) < 0.000000001
	t.check(eq_ok, "light at the equator is exactly the T1 daylight curve, all year")
	var seeds_ok := true
	for r in oc.regions:
		var sx := float(r["seed"]["x_km"])
		var sy := float(r["seed"]["y_km"])
		seeds_ok = seeds_ok and oc.region_at(sx, sy) == str(r["id"])
	t.check(seeds_ok, "every region's seed lies inside its own region")
	var wsum_ok := true
	for k in 30:
		var px: float = Ocean.hash01(k, 1, 0, 3) * oc.world_w
		var py: float = Ocean.hash01(k, 2, 0, 3) * oc.world_h
		var w: PackedFloat64Array = oc.region_weights(px, py)
		var total := 0.0
		for v in w:
			total += v
		wsum_ok = wsum_ok and absf(total - 1.0) < 0.000000001
	t.check(wsum_ok, "region weights sum to 1")
	var kmh: float = oc.tuning_value("ship.sail_speed_kmh")
	var into: float = oc.speed_through_water_kmh(90.0, 14.0, 90.0, 0.0)
	var beam: float = oc.speed_through_water_kmh(190.0, 14.0, 90.0, 0.0)
	t.check(into < 0.3 * beam and beam <= 1.05 * kmh, "into the wind is slow; a beam reach is near reference speed")
	t.check(oc.speed_through_water_kmh(190.0, 14.0, 90.0, 0.97) == 0.0, "a ship frozen into closed ice is stopped")
	t.check(oc.speed_through_water_kmh(0.0, 0.0, 90.0, 0.0) > 0.0, "a becalmed ship still drifts")
	var smp: Dictionary = oc.sample(7000.0, 2650.0, 0.25)
	var gv: Array = oc.ground_velocity_kmh(90.0, smp)
	var thru: float = oc.speed_through_water_kmh(
			90.0, float(smp["wind_kn"]), float(smp["wind_from_deg"]), float(smp["ice"]))
	var want_gv: float = thru + float(smp["current_u_kn"]) * Ocean.KN_KMH
	t.check(_near(float(gv[0]), want_gv), "ground velocity = sailing + current")
	t.check(str(smp["region"]) == "reg_kettle_seas", "the start anchorage is in the Kettle Seas")


func _route(t: Object, oc: RefCounted) -> void:
	var route := DataLoader.load_dict("res://data/world/slice_route.json")
	var cps: Array = route.get("checkpoints", [])
	t.check(cps.size() >= 6, "slice route has >= 6 checkpoints")
	var seen: Dictionary = {}
	for c in cps:
		var s: Dictionary = oc.sample(float(c["x_km"]), float(c["y_km"]), float(c["t_days"]))
		seen[str(s["region"])] = true
		var bad: Array = []
		for k in (c["expect"] as Dictionary).keys():
			var v: Variant = c["expect"][k]
			if k == "region":
				if str(s["region"]) != str(v):
					bad.append("region")
			elif str(k).ends_with("_min"):
				if float(s[str(k).trim_suffix("_min")]) < float(v):
					bad.append(str(k))
			elif str(k).ends_with("_max"):
				if float(s[str(k).trim_suffix("_max")]) > float(v):
					bad.append(str(k))
		t.check(bad.is_empty(), "slice checkpoint %s (%s) breaks: %s" % [c["id"], c["name"], bad])
	t.check(seen.size() >= 4, "the slice route crosses >= 4 regions (crosses %d)" % seen.size())


func _wildlife(t: Object, oc: RefCounted) -> void:
	var sp: Array = Wildlife.load_species()
	t.check(sp.size() >= 60, "species seed has >= 60 records (has %d)" % sp.size())
	var fx := DataLoader.load_dict("res://tests/fixtures/wildlife_cases.json")
	var cases: Array = fx.get("cases", [])
	t.check(cases.size() >= 40, "wildlife fixture has >= 40 cases")
	for c in cases:
		var x := float(c["x"])
		var y := float(c["y"])
		var tt := float(c["t"])
		var got: Dictionary = Wildlife.sighting(oc, sp, x, y, tt)
		var want: Variant = c["sighting"]
		var where := "(%s, %s, t=%s)" % [x, y, tt]
		if want == null:
			t.check(got.is_empty(), "sighting at %s should be none, got %s" % [where, got])
		else:
			var ok: bool = not got.is_empty() and str(got["species"]) == str(want["species"])
			ok = ok and int(got.get("count", -1)) == int(want["count"])
			ok = ok and int(got.get("slot", -1)) == int(want["slot"])
			ok = ok and _near(float(got.get("bearing_deg", -1.0)), float(want["bearing_deg"]))
			ok = ok and _near(float(got.get("distance_km", -1.0)), float(want["distance_km"]))
			t.check(ok, "sighting at %s expected %s got %s" % [where, want, got])
		var tb: Array = Wildlife.table(oc, sp, x, y, tt)
		tb.sort_custom(func(p: Array, q: Array) -> bool: return float(p[1]) > float(q[1]))
		var top: Array = c["top"]
		# Python's sort is stable, GDScript's sort_custom is not: species with the same score (to 1e-4) may come in either order, so
		# compare the top entries as "score|species" keys (score rounded to 4 decimals, then species id)
		var top_ok := tb.size() >= top.size()
		if top_ok:
			var want_keys: Array = []
			var got_keys: Array = []
			for i in top.size():
				want_keys.append("%.4f|%s" % [float(top[i][1]), str(top[i][0])])
				got_keys.append("%.4f|%s" % [float(tb[i][1]), str(tb[i][0])])
			want_keys.sort()
			got_keys.sort()
			top_ok = want_keys == got_keys
		t.check(top_ok, "species table at %s: top entries differ from the golden file" % where)
	var night: float = Wildlife.activity_factor("nocturnal", 0.0)
	t.check(night > Wildlife.activity_factor("nocturnal", 12.0), "nocturnal animals prefer the night")
	var in_window: bool = Wildlife.season_factor([0.2, 0.6], 0.4) == 1.0
	t.check(in_window and Wildlife.season_factor([0.2, 0.6], 0.9) < 1.0, "season window")
	t.check(Wildlife.season_factor([0.8, 0.1], 0.95) == 1.0, "a season window may wrap around the year")
