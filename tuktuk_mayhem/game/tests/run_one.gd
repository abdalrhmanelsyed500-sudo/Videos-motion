extends SceneTree
## Runs ONE test file: node run.mjs <game> --script res://tests/run_one.gd -- test_reward
## (protocol mirrors pixel_pirates/game/tests/run_one.gd: test scripts expose run(t), t.check())
var checks := 0
var fails := 0


func check(cond: bool, msg: String) -> void:
	checks += 1
	if not cond:
		fails += 1
		print("  FAIL: ", msg)


func _initialize() -> void:
	var names := OS.get_cmdline_user_args()
	for nm in names:
		print("== ", nm)
		var s := load("res://tests/%s.gd" % nm) as GDScript
		if s == null:
			fails += 1
			print("  FAIL: cannot load ", nm)
			continue
		var inst: Object = s.new()
		inst.call("run", self)
	if checks == 0:
		fails += 1
		print("  FAIL: no checks ran at all")
	print("TESTS: %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)
