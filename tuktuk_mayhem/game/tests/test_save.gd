extends SceneTree
## Versioned save round-trip on the real loop (--fixed-fps 60): write, reload, refuse-newer, wipe.

var checks := 0
var fails := 0
var frame := 0


func check(cond: bool, msg: String) -> void:
	checks += 1
	if not cond:
		fails += 1
		print("  FAIL: ", msg)


func _process(_d: float) -> void:
	frame += 1
	if frame != 4:
		return
	var tk: Node = root.get_node("Tk")
	var reg: Node = root.get_node("Reg")
	tk.call("wipe_save")
	tk.call("add_money", 42.0)
	tk.set("reputation", 61)
	check(bool(tk.call("save_game")), "save writes")
	tk.set("balance", 1.0)
	check(bool(tk.call("load_game")), "load reads")
	var want: float = float(reg.call("tuning").get("start_balance", 60)) + 42.0
	check(is_equal_approx(float(tk.get("balance")), want),
			"balance restored (%f vs %f)" % [float(tk.get("balance")), want])
	check(int(tk.get("reputation")) == 61, "reputation restored")
	var f := FileAccess.open("user://tkm_save.json", FileAccess.WRITE)
	f.store_string('{"version": 99, "balance": 5}')
	f = null
	tk.set("balance", 7.0)
	check(not bool(tk.call("load_game")), "newer save version refused")
	check(is_equal_approx(float(tk.get("balance")), 7.0), "refused load keeps state")
	tk.call("wipe_save")
	check(not bool(tk.call("load_game")), "wipe removes save")
	print("TESTS: %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)
