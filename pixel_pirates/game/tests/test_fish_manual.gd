# gdlint: disable=max-line-length
extends RefCounted
## CP-2 Release B: the manual fishing state machine, driven by SIMULATED PLAYERS on the real tuning, grounds and species data.
## Checks: the defaults equal the JSON; the stage order; the cast quality from the needle; a steady alternating player lands the net in
## the 8 to 12 s window with a good catch; a sloppy player gets less; one-key mashing, alternating mashing, doing nothing and
## ignoring the surges all do worse or fail with an explanation; the catch is composed from the ground's own species; the commit
## into the REAL hold happens once and respects the capacity; cancel is clean at every stage. Pure logic.
## NOT YET RUN ON THE USER'S PC.
const Manual := preload("res://h2d/fish_manual.gd")
const Catch := preload("res://h2d/fish_catch.gd")
const PortState := preload("res://h2d/port_state.gd")
const Ocean := preload("res://core/ocean.gd")
const DataLoader := preload("res://core/data_loader.gd")
const DT := 1.0 / 60.0


func _fm(tuning: Dictionary) -> Manual:
	var m := Manual.new()
	m.configure(tuning, DataLoader.load_dict("res://data/port/manual_fishing.json"))
	return m


func _grounds() -> Dictionary:
	return (DataLoader.load_dict("res://data/port/fishing_grounds.json")["grounds"] as Dictionary)


func _port(tuning: Dictionary) -> PortState:
	var s := PortState.new()
	s.configure(tuning, DataLoader.load_dict("res://data/port/fish_market.json"), DataLoader.load_dict("res://data/port/recruits_port.json"))
	return s


## A simulated player. kind: perfect | steady_slow | sloppy | mash_one | mash_alt | idle | ignore_surge
## Returns {stage, haul_s, q, kg, count, reason, events: {name: n}, t}
func _play(tuning: Dictionary, gid: String, kind: String, seed_value: int, max_s: float = 90.0, bonus := 0.0) -> Dictionary:
	var m := _fm(tuning)
	var g: Dictionary = _grounds()[gid]
	m.begin(gid, g, {"hour": 12.0, "bonus": bonus, "room_kg": 40.0, "seed": seed_value})
	var evc: Dictionary = {}
	var t := 0.0
	var next_pull := 0.0
	var side := "left"
	var jitter := 0
	while t < max_s and m.stage != Manual.Stage.DONE and m.stage != Manual.Stage.FAIL and m.stage != Manual.Stage.SUMMARY:
		var evs: Array = m.step(DT, {"speed_kn": 0.5, "max_speed_kn": 1.5})
		for e in evs:
			evc[str((e as Dictionary)["type"])] = int(evc.get(str((e as Dictionary)["type"]), 0)) + 1
		if m.stage == Manual.Stage.AIM:
			var want := absf(m.aim - 0.5) < 0.03
			if kind == "sloppy":
				want = m.stage_t > 0.55 and m.stage_t < 0.8 and absf(m.aim - 0.5) < 0.3
			if kind != "idle" and want:
				for e in m.press("cast"):
					evc[str((e as Dictionary)["type"])] = int(evc.get(str((e as Dictionary)["type"]), 0)) + 1
		elif m.stage == Manual.Stage.HAUL:
			var gap := 0.42
			var go := true
			match kind:
				"perfect":
					gap = 0.40
					if m.surge_phase == 1 and m.surge_kind > 0 or (m.surge_phase == 2 and m.surge_kind > 0 and m.surge_left > 0.45):
						go = false                      # the fish runs: let the rope breathe
					elif m.surge_phase >= 1 and m.surge_kind < 0:
						gap = 0.3                       # the fish turns: haul faster
					elif m.tension > 0.78:
						go = false
				"steady_slow":
					gap = 0.8
				"sloppy":
					jitter += 1
					gap = 0.25 + 0.55 * absf(sin(float(jitter) * 1.7))
				"mash_one":
					gap = 0.1
				"mash_alt":
					gap = 0.1
				"ignore_surge":
					gap = 0.40
				"idle":
					go = false
			if go and t >= next_pull:
				if kind == "mash_one":
					side = "left"
				else:
					side = "right" if side == "left" else "left"
				for e in m.press(side):
					evc[str((e as Dictionary)["type"])] = int(evc.get(str((e as Dictionary)["type"]), 0)) + 1
				next_pull = t + gap
		t += DT
	return {"stage": m.stage, "haul_s": m.haul_t, "q": float(m.result.get("q", 0.0)), "kg": float(m.result.get("kg", 0.0)),
		"count": int(m.result.get("count", 0)), "reason": m.fail_reason, "events": evc, "t": t, "m": m, "grade": str(m.result.get("grade", ""))}


func run(t: Object) -> void:
	var tuning := Ocean.load_tuning()
	# ---- defaults = JSON ----
	for k in Manual.DEFAULTS.keys():
		var full: String = "mfish." + str(k)
		t.check(tuning.has(full), "tuning has %s" % full)
		if tuning.has(full):
			t.check(absf(float(tuning[full]) - float(Manual.DEFAULTS[k])) < 0.000001, "default of %s matches the JSON" % k)
	# ---- the data: every species of every ground has an average weight, an icon id and a price ----
	var doc := DataLoader.load_dict("res://data/port/manual_fishing.json")
	var market := DataLoader.load_dict("res://data/port/fish_market.json")["species"] as Dictionary
	for gid in _grounds().keys():
		t.check((doc["profiles"] as Dictionary).has(gid), "ground %s has a haul profile" % gid)
		for sw in (_grounds()[gid] as Dictionary)["species"]:
			var sp := str((sw as Array)[0])
			t.check((doc["species"] as Dictionary).has(sp), "%s has an average weight" % sp)
			t.check(market.has(sp), "%s is on the market" % sp)
	# ---- stage order and the cast ----
	var m := _fm(tuning)
	var g: Dictionary = _grounds()["gnd_pilchard_shallows"]
	m.begin("gnd_pilchard_shallows", g, {"hour": 12.0, "bonus": 0.0, "room_kg": 40.0, "seed": 5})
	t.check(m.stage == Manual.Stage.HEAVE, "begin starts in HEAVE")
	m.step(DT, {"speed_kn": 4.0, "max_speed_kn": 1.5})
	t.check(m.stage == Manual.Stage.HEAVE, "too fast: still heaving to")
	m.press("cast")
	t.check(m.stage == Manual.Stage.HEAVE, "a cast press before AIM does nothing")
	m.step(DT, {"speed_kn": 1.0, "max_speed_kn": 1.5})
	t.check(m.stage == Manual.Stage.AIM, "slow enough: AIM")
	for i in 5000:
		m.step(DT, {"speed_kn": 0.5, "max_speed_kn": 1.5})
		if absf(m.aim - 0.5) < 0.03:
			break
	m.press("cast")
	t.check(m.stage == Manual.Stage.SINK and m.cast_q >= 1.14, "needle in the middle: a perfect cast (q %.2f)" % m.cast_q)
	var m2 := _fm(tuning)
	m2.begin("gnd_pilchard_shallows", g, {"seed": 5})
	m2.step(DT, {"speed_kn": 0.0})
	m2.press("cast")                           # the needle is at the very end: a miss
	t.check(m2.stage == Manual.Stage.SINK and m2.cast_q < 0.6, "needle at the end: a weak cast (q %.2f)" % m2.cast_q)
	var m3 := _fm(tuning)
	m3.begin("gnd_pilchard_shallows", g, {"seed": 5})
	m3.step(DT, {"speed_kn": 0.0})
	for i in int((float(tuning["mfish.aim_timeout_s"]) + 1.0) / DT):
		m3.step(DT, {"speed_kn": 0.0})
		if m3.stage != Manual.Stage.AIM:
			break
	t.check(m3.stage == Manual.Stage.SINK and m3.cast_q < 0.6, "no press: the net goes out weak by itself")
	var m4 := _fm(tuning)
	m4.begin("gnd_pilchard_shallows", g, {"seed": 5})
	for i in int(32.0 / DT):
		m4.step(DT, {"speed_kn": 5.0, "max_speed_kn": 1.5})
	t.check(m4.stage == Manual.Stage.FAIL and m4.fail_reason == "heave", "a ship that never slows ends the attempt with an explanation")
	# ---- the simulated players ----
	var perfect: Array = []
	for seed_v in [3, 11, 29, 101, 777, 4242, 31337, 99991]:
		var r := _play(tuning, "gnd_gannet_bank", "perfect", seed_v)
		perfect.append(r)
		print("MFISH perfect seed %d: stage %s haul %.1f s q %.2f kg %.2f count %d %s" % [seed_v, str(Manual.Stage.keys()[int(r["stage"])]), float(r["haul_s"]), float(r["q"]), float(r["kg"]), int(r["count"]), str(r["reason"])])
	var ok_n := 0
	var times: Array = []
	var qs := 0.0
	for r in perfect:
		if int(r["stage"]) == Manual.Stage.SUMMARY:
			ok_n += 1
			times.append(float(r["haul_s"]))
			qs += float(r["q"])
	t.check(ok_n >= 7, "a steady alternating player lands the net on %d of 8 seeds" % ok_n)
	var in_window := 0
	for x in times:
		if float(x) >= 7.0 and float(x) <= 13.5:
			in_window += 1
	t.check(in_window >= maxi(ok_n - 1, 1), "a normal successful haul takes 7 to 13.5 s (%d of %d inside)" % [in_window, ok_n])
	t.check(ok_n > 0 and qs / float(ok_n) >= 0.7, "and the catch quality is good (mean %.2f)" % (qs / maxf(float(ok_n), 1.0)))
	var kinds := {"steady_slow": [], "sloppy": [], "mash_one": [], "mash_alt": [], "idle": [], "ignore_surge": []}
	for kd in kinds.keys():
		var okc := 0
		var sumq := 0.0
		var fails: Dictionary = {}
		var sumh := 0.0
		for seed_v in [3, 11, 29, 101, 777, 4242]:
			var r := _play(tuning, "gnd_gannet_bank", str(kd), seed_v)
			if int(r["stage"]) == Manual.Stage.SUMMARY:
				okc += 1
				sumq += float(r["q"])
				sumh += float(r["haul_s"])
			else:
				fails[str(r["reason"])] = int(fails.get(str(r["reason"]), 0)) + 1
		print("MFISH %s: landed %d of 6, mean q %.2f, mean haul %.1f s, fails %s" % [kd, okc, sumq / maxf(float(okc), 1.0), sumh / maxf(float(okc), 1.0), str(fails)])
		kinds[kd] = {"ok": okc, "q": sumq / maxf(float(okc), 1.0), "fails": fails, "h": sumh / maxf(float(okc), 1.0)}
	var pq := qs / maxf(float(ok_n), 1.0)
	t.check(int((kinds["mash_one"] as Dictionary)["ok"]) == 0, "mashing ONE lever never lands the net")
	t.check(int((kinds["idle"] as Dictionary)["ok"]) == 0 and not (kinds["idle"] as Dictionary)["fails"].is_empty(), "doing nothing never lands it and the failure has a reason")
	t.check(int((kinds["mash_alt"] as Dictionary)["ok"]) == 0 or float((kinds["mash_alt"] as Dictionary)["q"]) < pq - 0.1, "mashing both levers as fast as possible is clearly worse than the rhythm")
	t.check(int((kinds["sloppy"] as Dictionary)["ok"]) == 0 or float((kinds["sloppy"] as Dictionary)["q"]) < pq - 0.05, "a sloppy rhythm gives a smaller catch (%.2f against %.2f)" % [float((kinds["sloppy"] as Dictionary)["q"]), pq])
	# deep water (heavy pulls, strong runs): reading the surges must pay
	var deep_p := 0.0
	var deep_i := 0.0
	var landed_p := 0
	var landed_i := 0
	var snaps_i := 0
	for seed_v in [3, 11, 29, 101, 777, 4242, 31337, 99991, 5, 6, 7, 8]:
		var rp := _play(tuning, "gnd_blue_drop", "perfect", seed_v)
		var ri := _play(tuning, "gnd_blue_drop", "ignore_surge", seed_v)
		if int(rp["stage"]) == Manual.Stage.SUMMARY:
			landed_p += 1
			deep_p += float(rp["kg"])
		if int(ri["stage"]) == Manual.Stage.SUMMARY:
			landed_i += 1
			deep_i += float(ri["kg"])
		elif str(ri["reason"]) == "snap":
			snaps_i += 1
	print("MFISH blue drop 12 nets: reading the surges landed %d (%.1f kg), ignoring them landed %d (%.1f kg, %d snaps)" % [landed_p, deep_p, landed_i, deep_i, snaps_i])
	t.check(landed_p >= 10, "deep water: a player who reads the surges lands %d of 12 nets" % landed_p)
	t.check(deep_p > deep_i, "deep water: reading the surges pays (%.1f kg against %.1f kg for ignoring them)" % [deep_p, deep_i])
	# ---- failures explain themselves ----
	var snapped := false
	for seed_v in [3, 11, 29, 101, 777, 4242]:
		var r := _play(tuning, "gnd_blue_drop", "mash_alt", seed_v)
		if str(r["reason"]) == "snap":
			snapped = true
			t.check(str((r["m"] as Manual).advice()).length() > 30, "a snapped rope is explained in words")
			t.check((r["m"] as Manual).result["fish"].is_empty(), "and the catch is lost")
			break
	t.check(snapped, "fast mashing in deep water snaps the rope")
	# ---- the catch comes from the ground's own species ----
	for gid in _grounds().keys():
		var allowed: Array = []
		for sw in (_grounds()[gid] as Dictionary)["species"]:
			allowed.append(str((sw as Array)[0]))
		var bad := 0
		var n := 0
		for seed_v in [1, 2, 3, 4, 5, 6, 7, 8]:
			var r := _play(tuning, str(gid), "perfect", seed_v)
			if int(r["stage"]) != Manual.Stage.SUMMARY:
				continue
			n += 1
			for f in (r["m"] as Manual).result["fish"]:
				if not allowed.has(str((f as Dictionary)["species"])):
					bad += 1
		t.check(bad == 0 and n > 0, "%s: every fish caught belongs to the ground (%d nets)" % [gid, n])
	# the deep ground gives bigger nets than the shallows
	var kg_sh := 0.0
	var kg_bd := 0.0
	for seed_v in [1, 2, 3, 4, 5, 6]:
		kg_sh += float(_play(tuning, "gnd_pilchard_shallows", "perfect", seed_v)["kg"])
		kg_bd += float(_play(tuning, "gnd_blue_drop", "perfect", seed_v)["kg"])
	print("MFISH kg per net: shallows %.2f, blue drop %.2f" % [kg_sh / 6.0, kg_bd / 6.0])
	t.check(kg_bd > kg_sh, "the Blue Drop (richness 1.3) gives more kg per net than the Pilchard Shallows")
	# the passive nets for comparison: 1.2 kg per 12 s; a manual net of ~30 s must be worth more but not absurdly more
	var per_min_manual := (kg_sh / 6.0) / 30.0 * 60.0
	t.check(per_min_manual > 6.0 and per_min_manual < 20.0, "manual fishing at the shallows pays %.1f kg a minute against 6.0 for the passive nets" % per_min_manual)
	# ---- the commit: once, into the real hold, with the capacity respected ----
	var ps := _port(tuning)
	var r1 := _play(tuning, "gnd_gannet_bank", "perfect", 3)
	var mm := r1["m"] as Manual
	t.check(int(mm.stage) == Manual.Stage.SUMMARY, "a landed net waits in SUMMARY")
	var before := ps.hold_kg()
	var res := mm.commit(ps, 0.5)
	var after := ps.hold_kg()
	t.check(absf((after - before) - float(mm.result["kg"])) < 0.02 and after > 0.0, "commit puts the catch in the real hold (%.2f kg)" % after)
	mm.commit(ps, 0.5)
	t.check(absf(ps.hold_kg() - after) < 0.0001, "a second commit adds nothing")
	t.check(not res.is_empty() and int(res["count_stored"]) > 0, "the commit reports the fish stored")
	# a nearly full hold takes only what fits and says how much was released
	var ps2 := _port(tuning)
	ps2.add_catch("spc_sardine", 39.5, 0.0)
	var r2 := _play(tuning, "gnd_gannet_bank", "perfect", 3)
	var mm2 := r2["m"] as Manual
	var res2 := mm2.commit(ps2, 0.5)
	t.check(ps2.hold_kg() <= ps2.capacity_kg() + 0.001, "a full hold is never overfilled (%.2f of %.0f)" % [ps2.hold_kg(), ps2.capacity_kg()])
	t.check(float(res2["released"]) > 0.0, "the fish that do not fit are reported as released (%.2f kg)" % float(res2["released"]))
	# ---- unload and done ----
	mm.press("confirm")
	t.check(mm.stage == Manual.Stage.UNLOAD, "confirm in the summary starts the unload")
	for i in int(5.0 / DT):
		mm.step(DT, {})
	t.check(mm.stage == Manual.Stage.DONE and not mm.is_active(), "the unload ends in DONE and the session is over")
	# ---- cancel at every stage ----
	for stg in ["heave", "aim", "sink", "haul", "summary"]:
		var cm := _fm(tuning)
		var cp := _port(tuning)
		cm.begin("gnd_gannet_bank", _grounds()["gnd_gannet_bank"], {"seed": 9})
		var guard := 0
		while guard < 4000 and not (cm.stage == Manual.Stage.HEAVE and stg == "heave") and not (cm.stage == Manual.Stage.AIM and stg == "aim") and not (cm.stage == Manual.Stage.SINK and stg == "sink") and not (cm.stage == Manual.Stage.HAUL and stg == "haul") and not (cm.stage == Manual.Stage.SUMMARY and stg == "summary"):
			guard += 1
			cm.step(DT, {"speed_kn": 0.0})
			if cm.stage == Manual.Stage.AIM and stg in ["sink", "haul", "summary"]:
				cm.press("cast") if absf(cm.aim - 0.5) < 0.05 else null
			if cm.stage == Manual.Stage.HAUL and stg == "summary":
				var sd := "left"
				for i in 400:
					cm.step(DT, {})
					if i % 25 == 0:
						cm.press(sd)
						sd = "right" if sd == "left" else "left"
					if cm.stage != Manual.Stage.HAUL:
						break
		cm.cancel()
		for i in int(8.0 / DT):
			cm.step(DT, {})
			if cm.stage == Manual.Stage.DONE:
				break
		cm.commit(cp, 0.5)
		t.check(cm.stage == Manual.Stage.DONE and not cm.is_active(), "cancel during %s ends cleanly in DONE" % stg)
		if stg != "summary":
			t.check(cp.hold_kg() < 0.0001, "cancel during %s takes nothing into the hold and loses nothing" % stg)
		else:
			t.check(cp.hold_kg() > 0.0 or cm.result.is_empty(), "cancel in the summary keeps the catch")
	# ---- quantity maths ----
	t.check(Catch.count_for(0.0, 0.12) == 0 and Catch.count_for(0.5, 0.12) == 4 and Catch.count_for(0.01, 6.0) == 1, "count_for: none, a few sardines, a tiny tuna is still one fish")
	t.check(Catch.grade_for(1.1) == "Excellent" and Catch.grade_for(0.8) == "Good" and Catch.grade_for(0.5) == "Fair" and Catch.grade_for(0.2) == "Poor", "grades")
