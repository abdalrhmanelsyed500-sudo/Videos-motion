extends SceneTree
## Scenario 10 of the Phase 2 QA matrix: complete mission UNDER DRIVING STRESS on the real loop
## (--fixed-fps 60): offer at the stand, accept, board, a real controlled-drift manoeuvre with
## reward credit, a ramp launch + landing, delivery in the ring, fare paid EXACTLY ONCE,
## dismiss to a valid next-passenger state. Prints SELFPLAY line; zero-check = failure.
## Teleports replace long transits only; every mission transition is the real state machine.

var checks := 0
var fails := 0
var frame := 0
var stage := 0
var dist: Node3D = null
var tuk: Node3D = null
var bal_start := 0.0
var drifted_seen := false
var air_seen := false
var air_streak := 0
var air_max_y := -99.0
var landed_seen := false


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
	var tk: Node = root.get_node_or_null("Tk")
	if tk == null:
		print("SELFPLAY: 1 checks, 1 failed -> FAIL")
		quit(1)
	bal_start = float(tk.get("balance"))


func _process(_delta: float) -> void:
	frame += 1
	var mgr: Node = root.get_node_or_null("/root/MissionMgr")
	var tk: Node = root.get_node_or_null("/root/Tk")
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
				var d: Dictionary = (root.get_node("Reg") as Node).call("district")
				tuk.global_position = Vector3(float(d["pickup"]["x"]), 0.4, float(d["pickup"]["z"]))
				tuk.set("speed", 0.0)
				stage = 1
		1:  # offer appears at the stand -> accept
			if st == 1:
				check(true, "offer appeared at the stand")
				_act("accept_mission", true)
				_act("accept_mission", false)
				stage = 2
				frame = 0
			elif frame > 240:
				check(false, "offer never appeared")
				stage = 9
		2:  # boarding completes -> DRIVING
			if st == 3:
				check(true, "passenger boarded, driving started")
				stage = 3
				frame = 0
			elif frame > 240:
				check(false, "boarding never finished (state %d)" % st)
				stage = 9
		3:  # driving stress: controlled drift manoeuvre (real inputs)
			if frame == 10:
				tuk.set("speed", 18.0)
				_act("accelerate", true)
				_act("steer_left", true)
				_act("handbrake", true)
			if frame > 10 and frame < 90:
				if float(tuk.get("drift_time")) > 0.3:
					drifted_seen = true
			if frame == 55:
				_act("accelerate", false)
				_act("steer_left", false)
				_act("handbrake", false)
			if frame == 110:
				check(drifted_seen, "drift manoeuvre registered during driving")
				check(float(mgr.get("drift_earned")) > 0.0,
						"drift bonus credited (%.1f)" % float(mgr.get("drift_earned")))
				stage = 4
				frame = 0
		4:  # ramp launch + landing under mission
			if frame == 1:
				tuk.set("yaw", 1.5708)
				tuk.global_position = Vector3(-30, 0.4, 60)
				tuk.set("speed", 14.0)
			if frame <= 100:
				if bool(tuk.get("airborne")):
					air_streak += 1
					if air_streak >= 3:
						air_seen = true  # sustained flight, not a one-frame flag
					air_max_y = maxf(air_max_y, tuk.global_position.y)
				elif air_seen:
					landed_seen = true
			if frame == 100:
				check(air_seen, "ramp launched the tuk-tuk mid-mission (sustained flight)")
				check(air_max_y > 0.5, "mission jump gained height (max y=%.2f m)" % air_max_y)
				check(landed_seen, "tuk-tuk landed back on the road")
				stage = 5
				frame = 0
		5:  # deliver in the destination ring
			if frame == 5:
				var d2: Dictionary = (root.get_node("Reg") as Node).call("district")
				tuk.global_position = Vector3(float(d2["dest"]["x"]) - 2.0, 0.4, float(d2["dest"]["z"]))
				tuk.set("speed", 0.0)
				stage = 6
				frame = 0
		6:
			if st == 4:
				var bal: float = float(tk.get("balance"))
				check(bal > bal_start, "fare paid on delivery (%f -> %f)" % [bal_start, bal])
				_act("accept_mission", true)
				_act("accept_mission", false)
				stage = 7
				frame = 0
			elif frame > 240:
				check(false, "delivery never completed (state %d)" % st)
				stage = 9
		7:  # paid exactly once + valid next state
			if st == 0:
				var bal2: float = float(tk.get("balance"))
				check(dist.get("passenger") != null, "next passenger waiting after result")
				check(bal2 > bal_start, "balance kept after dismiss")
				_act("accept_mission", true)
				_act("accept_mission", false)
				check(is_equal_approx(float(tk.get("balance")), bal2), "no double pay on stray accept")
				stage = 9
				_finish()
		9:
			if frame > 400:
				_finish()


func _finish() -> void:
	print("SELFPLAY: %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)
