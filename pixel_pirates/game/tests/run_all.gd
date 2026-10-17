extends SceneTree
## Headless test runner (A2/A7). Needs NO graphics card:
##   Godot_v4.7.2-stable_win64_console.exe --headless --path game --script res://tests/run_all.gd
## Run `... --headless --path game --import` once after a fresh clone or after new art arrives.
## Every tests/test_*.gd is a script with `func run(t) -> void`; use t.check(cond, message).
var checks := 0
var fails := 0


func check(cond: bool, msg: String) -> void:
	checks += 1
	if not cond:
		fails += 1
		print("  FAIL: ", msg)


func _initialize() -> void:
	var files: Array[String] = []
	var d := DirAccess.open("res://tests")
	if d == null:
		print("TESTS: cannot open res://tests")
		quit(2)
		return
	for f in d.get_files():
		if f.begins_with("test_") and f.ends_with(".gd"):
			files.append(f)
	files.sort()
	for f in files:
		print("== ", f)
		var s := load("res://tests/" + f) as GDScript
		if s == null:
			fails += 1
			print("  FAIL: cannot load ", f)
			continue
		var inst: Object = s.new()
		inst.call("run", self)
	print("TESTS: %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)
