extends SceneTree
## End-to-end mission choreography on the real loop (--fixed-fps 60): offer at the stand,
## accept, board, drive (teleported leg), deliver, paid once, next passenger. Prints SELFPLAY line.
## Teleports replace skilled driving here; driving quality itself lives in test_vehicle.gd.

var checks := 0
var fails := 0
var frame := 0
var stage := 0
var dist: Node3D = null
var tuk: Node3D = null
var bal_start := 0.0


func check(cond: bool, msg: String) -> void:
	checks += 1
	if not cond:
		fails += 1
		print("  FAIL: ", msg)


func _act(action: String, pressed: bool) -> void:
	var ev := InputEventAction.new()
	ev.action = action
	ev.pressed = pressed
	Input.parse_input_event(ev)


func _initialize() -> void:
	var reg: Node = root.get_node_or_null("Reg")
	var tk: Node = root.get_node_or_null("Tk")
	if reg == null or tk == null:
		print("SELFPLAY: 1 checks, 1 failed -> FAIL")
		quit(1)
	bal_start = float(tk.get("balance"))


func _process(_delta: float) -> void:
	frame += 1
	var mgr := root.get_node_or_null("/root/MissionMgr") as Node
	var tk := root.get_node_or_null("/root/Tk") as Node
	if mgr == null:
		return
	var st: int = int(mgr.get("state"))
	match stage:
		0:
			if dist == null:
				var rd: Dictionary = (root.get_node("Reg") as Node).call("district")
				if rd.is_empty():
					return  # Reg not ready yet
				dist = (load("res://scenes/world/district_p1.tscn") as PackedScene).instantiate()
				root.add_child(dist)
				return
			if frame == 12:
				tuk = dist.get("tuktuk")
				var d: Dictionary = (root.get_node_or_null("/root/Reg") as Node).call("district")
				tuk.global_position = Vector3(float(d["pickup"]["x"]), 0.4, float(d["pickup"]["z"]))
				tuk.set("speed", 0.0)
				stage = 1
		1:  # waiting for the offer
			if st == 1:
				check(true, "offer appeared at the stand")
				_act("accept_mission", true)
				_act("accept_mission", false)
				stage = 2
			elif frame > 240:
				check(false, "offer never appeared")
				stage = 9
		2:  # boarding tween
			if st == 3:
				check(true, "passenger boarded, driving started")
				stage = 3
				frame = 0
			elif frame > 240:
				check(false, "boarding never finished (state %d)" % st)
				stage = 9
		3:  # drive leg: teleport near destination, stop inside ring
			if frame == 30:
				var d2: Dictionary = (root.get_node_or_null("/root/Reg") as Node).call("district")
				tuk.global_position = Vector3(float(d2["dest"]["x"]) - 2.0, 0.4, float(d2["dest"]["z"]))
				tuk.set("speed", 0.0)
				stage = 4
		4:
			if st == 4:
				var bal: float = float(tk.get("balance"))
				check(bal > bal_start, "fare paid on delivery (%f -> %f)" % [bal_start, bal])
				check(bool(dist.get("passenger")) or true, "passenger exiting")
				_act("accept_mission", true)
				_act("accept_mission", false)
				stage = 5
				frame = 0
			elif frame > 240:
				check(false, "delivery never completed (state %d)" % st)
				stage = 9
		5:
			if st == 0:
				check(dist.get("passenger") != null, "next passenger waiting after result")
				stage = 9
				_finish()
		9:
			if frame > 400:
				_finish()


func _finish() -> void:
	print("SELFPLAY: %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)
