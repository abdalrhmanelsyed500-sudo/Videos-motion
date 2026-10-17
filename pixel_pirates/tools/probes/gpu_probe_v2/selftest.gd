extends SceneTree
## Headless self-test: needs NO graphics card. Run:
##   Godot_v4.7.2-stable_win64_console.exe --headless --path . --script res://selftest.gd
## Proves the engine starts on this PC without a GPU and that data parsing works (JSON is our data format candidate).
func _init() -> void:
	var ok := true
	var json := JSON.new()
	var err := json.parse('{"island":{"id":"I001","name":"Test","tier":1},"gap_days":[1.5,3,9]}')
	ok = ok and err == OK and json.data["island"]["id"] == "I001"
	var days: Array = json.data["gap_days"]
	ok = ok and days.size() == 3 and is_equal_approx(float(days[0]), 1.5)
	# single-precision build: 100000.001 is stored as 100000.0; double-precision build keeps it
	ok = ok and ((Vector3(100000.001, 0, 0).x == 100000.0) == (not OS.has_feature("double")))
	print("engine: ", Engine.get_version_info()["string"], "  os: ", OS.get_name(), "  64-bit: ", OS.has_feature("64"))
	print("SELFTEST ", "PASS" if ok else "FAIL")
	quit(0 if ok else 1)
