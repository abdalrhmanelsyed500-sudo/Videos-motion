extends SceneTree
## Vehicle controller matrix on the real loop (--fixed-fps 60): accelerate, brake, steer,
## reverse, impact speed loss + no penetration, control recovery. Prints TESTS line like run_one.
## (Scene-based tests must run on the main loop: SceneTree.iterate() never flushes READY.)

var checks := 0
var fails := 0
var frame := 0
var stage := 0
var tuk: Node3D = null
var wall: StaticBody3D = null
var before := 0.0
var after := 0.0
var prev_spd := 0.0
var prev_hits := 0
var yaw0 := 0.0
var yaw1 := 0.0


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
	var floor_body := StaticBody3D.new()
	var fs := CollisionShape3D.new()
	var fq := BoxShape3D.new()
	fq.size = Vector3(600, 2, 600)
	fs.shape = fq
	floor_body.add_child(fs)
	floor_body.position = Vector3(0, -1, 0)
	root.add_child(floor_body)
	tuk = (load("res://scenes/vehicles/tuktuk.tscn") as PackedScene).instantiate()
	root.add_child(tuk)


func _process(_d: float) -> void:
	frame += 1
	match stage:
		0:
			if frame == 4:
				_act("accelerate", true)
			if frame == 90:
				check(float(tuk.get("speed")) > 5.0, "accelerates (%.1f m/s)" % float(tuk.get("speed")))
				check(tuk.global_position.z < -5.0, "moves forward (-z), z=%.1f" % tuk.global_position.z)
				before = float(tuk.get("speed"))
				_act("accelerate", false)
				_act("brake", true)
				stage = 1
				frame = 0
		1:  # brake decelerates hard; holding brake past zero is reverse by design (checked in stage 3)
			if frame == 20:
				_act("brake", false)
				var s1 := float(tuk.get("speed"))
				check(s1 < before * 0.5, "braking decelerates (%.1f -> %.1f)" % [before, s1])
				check(s1 > -0.5, "short brake does not jump to reverse (%.2f)" % s1)
				tuk.set("speed", 10.0)
				yaw0 = float(tuk.get("yaw"))
				_act("steer_left", true)
				stage = 2
				frame = 0
		2:
			if frame == 30:
				_act("steer_left", false)
				yaw1 = float(tuk.get("yaw"))
				var dyaw := absf(wrapf(yaw1 - yaw0, -PI, PI))
				check(dyaw > 0.1, "steering turns the tuk-tuk (%.2f rad)" % dyaw)
				tuk.set("speed", 0.0)
				tuk.set("yaw", 0.0)
				_act("brake", true)
				stage = 3
				frame = 0
		3:
			if frame == 40:
				_act("brake", false)
				check(float(tuk.get("speed")) < -0.5, "reverse engages (%.2f)" % float(tuk.get("speed")))
				tuk.set("speed", 0.0)
				tuk.set("yaw", 0.0)
				tuk.global_position = Vector3(0, 0.4, 0)
				wall = StaticBody3D.new()
				var ws := CollisionShape3D.new()
				var wb := BoxShape3D.new()
				wb.size = Vector3(8, 6, 1)
				ws.shape = wb
				wall.add_child(ws)
				wall.position = Vector3(0, 2, -18)
				root.add_child(wall)
				_act("accelerate", true)
				stage = 4
				frame = 0
		4:
			if int(tuk.get("collisions_total")) > prev_hits:
				if before == 0.0:
					before = prev_spd   # speed on the frame the first impact landed
					after = float(tuk.get("speed"))
				prev_hits = int(tuk.get("collisions_total"))
			prev_spd = float(tuk.get("speed"))
			if frame == 240:
				_act("accelerate", false)
				check(prev_hits >= 1, "collision detected (%d)" % prev_hits)
				check(absf(after) < absf(before) * 0.8,
						"speed lost on impact (%.1f < %.1f)" % [absf(after), absf(before)])
				check(tuk.global_position.z > -18.0, "no wall penetration (z=%.1f)" % tuk.global_position.z)
				_act("steer_right", true)
				_act("accelerate", true)
				stage = 5
				frame = 0
		5:
			if frame == 60:
				_act("steer_right", false)
				_act("accelerate", false)
				check(absf(float(tuk.get("yaw"))) > 0.05, "regains control after impact")
				_finish()
		9:
			_finish()


func _finish() -> void:
	print("TESTS: %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)
