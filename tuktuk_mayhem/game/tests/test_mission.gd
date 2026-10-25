extends RefCounted
## Mission FSM + pay-once guarantee, with real autoload stand-ins registered by name.


func _boot(t) -> Array:
	var reg: Node = _auto(t, "Reg", "res://scripts/core/reg.gd")
	var tk: Node = _auto(t, "Tk", "res://scripts/core/tk.gd")
	var mgr: Node = _auto(t, "MissionMgr", "res://scripts/core/mission_mgr.gd")
	return [reg, tk, mgr]

func _auto(t, nm: String, path: String):
	var n = t.get_root().get_node_or_null(nm)
	if n == null:
		n = (load(path) as GDScript).new()
		n.name = nm
		t.get_root().add_child(n)
	t.iterate(0.001)  # flush deferred READY (autoloads and stand-ins alike in --script mode)
	return n



func run(t) -> void:
	var boot: Array = _boot(t)
	var tk: Node = boot[1]
	var mgr: Node = boot[2]
	var start_bal: float = float(tk.get("balance"))
	t.check(mgr.get("state") == 0, "starts IDLE")
	mgr.call("make_offer", {"name_en": "Mona", "hijab": true}, "Felfela Koshary", 120.0)
	t.check(mgr.get("state") == 1, "offer opens")
	t.check(not mgr.call("accept_offer") == false, "accept works in OFFER")
	t.check(mgr.get("state") == 2, "BOARDING after accept")
	mgr.call("begin_driving")
	t.check(mgr.get("state") == 3, "DRIVING after boarding")
	var tl: float = float(mgr.get("time_left_s"))
	t.check(tl > 30.0 and tl < 200.0, "timer initialised from tuning (%f)" % tl)
	mgr.call("_process", 1.0)
	t.check(abs(float(mgr.get("time_left_s")) - (tl - 1.0)) < 1e-6, "timer ticks")
	mgr.call("report_collision")
	mgr.call("report_collision")
	mgr.call("complete_delivery")
	t.check(mgr.get("state") == 4, "RESULT after delivery")
	var bal1: float = float(tk.get("balance"))
	t.check(bal1 > start_bal, "reward paid (%f -> %f)" % [start_bal, bal1])
	mgr.call("complete_delivery")
	mgr.call("_finish", true, "again")
	t.check(is_equal_approx(float(tk.get("balance")), bal1), "reward paid exactly once")
	var stats: Dictionary = tk.get("stats")
	t.check(int(stats.get("fares", 0)) == 1, "one fare counted")
	mgr.call("reset_to_idle")
	t.check(mgr.get("state") == 0, "back to IDLE for the next passenger")
	# timeout path
	mgr.call("make_offer", {"name_en": "Tarek"}, "Town", 80.0)
	mgr.call("accept_offer")
	mgr.call("begin_driving")
	mgr.set("time_left_s", 0.01)
	mgr.call("_process", 0.05)
	t.check(mgr.get("state") == 4, "timeout ends the mission")
	var bal2: float = float(tk.get("balance"))
	t.check(bal2 <= bal1, "no pay on timeout")
	for n in boot:
		n.queue_free()
