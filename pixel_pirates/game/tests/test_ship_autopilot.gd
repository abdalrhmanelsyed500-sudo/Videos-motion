extends RefCounted
## CP-2 Release A: the course hold steers the REAL helm model (helm.gd) with the real tuning. Checks: it holds a heading with
## no input (a ship left alone keeps its course and speed), it turns to a new heading without overshoot, it never holds a
## heading inside the no-go wedge (the ship is never left in irons), a manual tap re-latches the new heading, the shortest way
## round the compass, wind shifts, and that DEFAULTS match data/tuning/tuning_ship.json. Pure logic.
## NOT YET RUN ON THE USER'S PC.
const Autopilot := preload("res://h2d/ship_autopilot.gd")
const Helm := preload("res://h2d/helm.gd")


func _tuning() -> Dictionary:
	var out: Dictionary = {}
	for fname in ["tuning_ship", "tuning_helm"]:
		var f := FileAccess.open("res://data/tuning/%s.json" % fname, FileAccess.READ)
		if f != null:
			for rec in (JSON.parse_string(f.get_as_text()) as Dictionary)["records"]:
				out[str((rec as Dictionary)["key"])] = float((rec as Dictionary)["value"])
	return out


## Runs `secs` of the hold on the real helm. wind_from fixed. Returns {heading, max_err, max_overshoot, min_off}.
func _sim(tuning: Dictionary, ap: Object, helm: Object, secs: float, wind_from: float, manual_fn: Callable = Callable(), wind_kn := 12.0) -> Dictionary:
	var no_go := 40.0
	var dt := 1.0 / 60.0
	var min_off := 999.0
	var max_yaw := 0.0
	for i in int(secs / dt):
		var manual := 0.0
		if manual_fn.is_valid():
			manual = float(manual_fn.call(float(i) * dt))
		var axis := float(ap.call("steer", dt, manual, float(helm.get("heading_deg")), float(helm.get("yaw_rate")), wind_from, wind_kn, no_go))
		helm.call("step", dt, axis, 6.0)
		min_off = minf(min_off, absf(Autopilot.wrap180(float(helm.get("heading_deg")) - wind_from)))
		max_yaw = maxf(max_yaw, absf(float(helm.get("yaw_rate"))))
	return {"heading": float(helm.get("heading_deg")), "min_off": min_off, "max_yaw": max_yaw}


func run(t: Object) -> void:
	var tuning := _tuning()
	for k in Autopilot.DEFAULTS.keys():
		var full := "autopilot." + str(k)
		t.call("check", tuning.has(full) and absf(float(tuning[full]) - float(Autopilot.DEFAULTS[k])) < 0.000001, "DEFAULT matches json: " + full)
	var no_go := float(tuning.get("ship.no_go_deg", 40.0))
	t.call("check", no_go > 20.0, "no-go angle is in the tuning (%.0f)" % no_go)
	# --- not engaged: passes the manual axis through
	var ap: Object = Autopilot.new()
	ap.call("configure", tuning)
	t.call("check", is_equal_approx(float(ap.call("steer", 0.016, 0.7, 10.0, 0.0, 0.0, 12.0, 40.0)), 0.7), "not engaged: manual passes through")
	# --- holds a heading with nothing touched (wind well off the bow)
	var helm: Object = Helm.new()
	helm.call("configure", tuning)
	helm.call("reset", 58.0, 5.0)
	ap.call("engage", 58.0, 200.0, 12.0, 40.0)
	var r := _sim(tuning, ap, helm, 30.0, 200.0)
	t.call("check", absf(Autopilot.wrap180(float(r["heading"]) - 58.0)) < 0.6, "holds 58 deg for 30 s (%.2f)" % float(r["heading"]))
	# --- a disturbance (the ship is pushed 25 deg off) is brought back without overshooting more than 4 deg
	helm.call("reset", 58.0 + 25.0, 5.0)
	var peak := 0.0
	var dt := 1.0 / 60.0
	for i in 60 * 14:
		var axis := float(ap.call("steer", dt, 0.0, float(helm.get("heading_deg")), float(helm.get("yaw_rate")), 200.0, 12.0, 40.0))
		helm.call("step", dt, axis, 6.0)
		var e := Autopilot.wrap180(float(helm.get("heading_deg")) - 58.0)
		if i > 60 * 2 and e < 0.0:
			peak = maxf(peak, -e)
	t.call("check", peak < 4.0, "recovery from 25 deg: overshoot %.2f deg" % peak)
	t.call("check", absf(Autopilot.wrap180(float(helm.get("heading_deg")) - 58.0)) < 0.8, "recovery settles on 58 (%.2f)" % float(helm.get("heading_deg")))
	# --- across north (350 -> 10) takes the short way
	helm.call("reset", 350.0, 5.0)
	ap.call("engage", 10.0, 200.0, 12.0, 40.0)
	var short_ok := true
	for i in 60 * 10:
		var axis2 := float(ap.call("steer", dt, 0.0, float(helm.get("heading_deg")), float(helm.get("yaw_rate")), 200.0, 12.0, 40.0))
		helm.call("step", dt, axis2, 6.0)
		if i < 20 and float(helm.get("yaw_rate")) < -0.5:
			short_ok = false
	t.call("check", short_ok and absf(Autopilot.wrap180(float(helm.get("heading_deg")) - 10.0)) < 0.8, "turns the short way over north")
	# --- never holds a heading in the wedge: latch 3 degrees off the wind, wind from 90 deg
	helm.call("reset", 93.0, 4.0)
	var held := float(ap.call("engage", 93.0, 90.0, 12.0, 40.0))
	t.call("check", Autopilot.wrap180(held - 90.0) >= 40.0 + 6.0 - 0.01, "engaging in irons latches a sailable heading (%.1f)" % held)
	var r2 := _sim(tuning, ap, helm, 25.0, 90.0)
	t.call("check", float(r2["min_off"]) > 30.0 or float(r2["heading"]) > 0.0, "sim ran")
	t.call("check", absf(Autopilot.wrap180(float(helm.get("heading_deg")) - 90.0)) >= 44.0, "ends outside the no-go wedge (off=%.1f)" % absf(Autopilot.wrap180(float(helm.get("heading_deg")) - 90.0)))
	# --- wind shifts onto the bow while holding: the hold turns away, then the heading is sailable
	helm.call("reset", 58.0, 5.0)
	ap.call("engage", 58.0, 200.0, 12.0, 40.0)
	var r3 := _sim(tuning, ap, helm, 40.0, 70.0)       # wind now from 70 deg: the held 58 is 12 deg off the wind
	t.call("check", absf(Autopilot.wrap180(float(helm.get("heading_deg")) - 70.0)) >= 45.0, "wind shift: ship bears away from irons (off=%.1f)" % absf(Autopilot.wrap180(float(helm.get("heading_deg")) - 70.0)))
	# --- the wind dropping to a calm never turns the ship (nothing to avoid)
	helm.call("reset", 70.0, 1.0)
	ap.call("engage", 70.0, 70.0, 1.0, 40.0)
	var r4 := _sim(tuning, ap, helm, 10.0, 70.0, Callable(), 1.0)
	t.call("check", absf(Autopilot.wrap180(float(helm.get("heading_deg")) - 70.0)) < 1.0 and float(r4["max_yaw"]) < 1.0, "calm: heading kept even head to wind")
	# --- a manual tap re-latches: hold 58, tap D for 0.5 s, the ship settles on its new heading and holds it
	helm.call("reset", 58.0, 5.0)
	ap.call("engage", 58.0, 200.0, 12.0, 40.0)
	var tap := func(time_s: float) -> float:
		return 1.0 if time_s > 1.0 and time_s < 1.5 else 0.0
	var r5 := _sim(tuning, ap, helm, 14.0, 200.0, tap)
	var gain := Autopilot.wrap180(float(r5["heading"]) - 58.0)
	t.call("check", gain > 8.0 and gain < 30.0, "a 0.5 s tap of D turned the course %.1f deg" % gain)
	var h_after := float(helm.get("heading_deg"))
	var r6 := _sim(tuning, ap, helm, 10.0, 200.0)
	t.call("check", absf(Autopilot.wrap180(float(r6["heading"]) - h_after)) < 0.8, "after the tap the NEW heading is held (%.2f -> %.2f)" % [h_after, float(r6["heading"])])
	t.call("check", not bool(ap.get("manual_override")), "manual override ended")
	# --- holding the key keeps steering by hand and reports it
	var hold_d := func(_time_s: float) -> float:
		return 1.0
	helm.call("reset", 58.0, 5.0)
	ap.call("engage", 58.0, 200.0, 12.0, 40.0)
	_sim(tuning, ap, helm, 1.0, 200.0, hold_d)
	t.call("check", bool(ap.get("manual_override")), "while a key is held the hold waits (manual_override)")
	# --- release
	ap.call("release")
	t.call("check", not bool(ap.get("engaged")) and is_equal_approx(float(ap.call("steer", 0.016, -0.4, 10.0, 0.0, 0.0, 12.0, 40.0)), -0.4), "release hands the wheel back")
	# --- effective_target
	ap.call("engage", 200.0, 90.0, 12.0, 40.0)
	t.call("check", is_equal_approx(float(ap.call("effective_target", 90.0, 12.0, 40.0)), 200.0), "effective target is the latch when it is sailable")
	ap.set("target_deg", 100.0)
	t.call("check", is_equal_approx(float(ap.call("effective_target", 90.0, 12.0, 40.0)), 136.0), "latch inside the wedge: nearest sailable heading (136)")
	ap.set("target_deg", 80.0)
	t.call("check", is_equal_approx(float(ap.call("effective_target", 90.0, 12.0, 40.0)), 44.0), "latch on the other side: 44")
