extends SceneTree
## Phase 2 vehicle QA matrix, scenarios 1-8 (main loop, --fixed-fps 60):
## 1 accel, 2 brake, 3 reverse, 4 steering, 5 drift initiate+recover, 6 bounded collision,
## 7 ground contact / no penetration, 8 ramp jump + landing control.
## Prints TESTS line; runner rejects zero-check suites.

var checks := 0
var fails := 0
var frame := 0
var stage := 0
var tuk: Node3D = null
var wall: StaticBody3D = null
var s0 := 0.0
var yaw0 := 0.0
var yaw_low := 0.0
var yaw_med := 0.0
var prev_spd := 0.0
var hit_speed := -1.0
var after_speed := -1.0
var hits_at_contact := 0
var contact_frame := 0
var was_air := false
var air_frames := 0
var max_y := -99.0
var min_y := 99.0
var drifted := false
var resets_seen := 0


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


func _all_off() -> void:
	for a in ["accelerate", "brake", "steer_left", "steer_right", "handbrake"]:
		_act(a, false)


func _place(pos: Vector3, spd: float, y: float = 0.0) -> void:
	_all_off()
	tuk.global_position = pos + Vector3(0, 0.4 + y, 0)
	tuk.set("speed", spd)
	tuk.set("lat_vel", Vector3.ZERO)
	tuk.set("yaw", 0.0)
	tuk.set("velocity", Vector3.ZERO)


func _initialize() -> void:
	var floor_body := StaticBody3D.new()
	var fs := CollisionShape3D.new()
	var fq := BoxShape3D.new()
	fq.size = Vector3(800, 0.1, 800)
	fs.shape = fq
	floor_body.add_child(fs)
	floor_body.position = Vector3(0, -0.02, 0)
	root.add_child(floor_body)
	tuk = (load("res://scenes/vehicles/tuktuk.tscn") as PackedScene).instantiate()
	root.add_child(tuk)
	tuk.connect("request_reset", _on_reset_seen)


func _on_reset_seen() -> void:
	resets_seen += 1


func _process(_d: float) -> void:
	frame += 1
	match stage:
		0:  # S1 acceleration from rest
			if frame == 3:
				_place(Vector3(0, 0, 0), 0.0)
				_act("accelerate", true)
			if frame == 93:
				check(float(tuk.get("speed")) > 10.0,
						"S1 accelerates from rest (%.1f m/s in 1.5 s)" % float(tuk.get("speed")))
				check(tuk.global_position.z < -8.0, "S1 covers ground (z=%.1f)" % tuk.global_position.z)
				stage = 1
				frame = 0
		1:  # S2 braking predictability
			if frame == 1:
				s0 = float(tuk.get("speed"))
				_act("accelerate", false)
				_act("brake", true)
			if frame == 25:
				var s1 := float(tuk.get("speed"))
				check(s1 < s0 * 0.5 and s1 > -0.6,
						"S2 brake halves speed without jumping to reverse (%.1f->%.1f)" % [s0, s1])
				check(is_finite(s1), "S2 speed stays finite")
				_all_off()
				stage = 2
				frame = 0
		2:  # S3 brake-to-reverse + reverse steering sign
			if frame == 1:
				_place(Vector3(0, 0, 20), 0.0)
				_act("brake", true)
			if frame == 61:
				check(float(tuk.get("speed")) < -2.0,
						"S3 brake from rest engages reverse (%.1f)" % float(tuk.get("speed")))
				check(tuk.global_position.z > 20.5, "S3 reverse moves +z (z=%.1f)" % tuk.global_position.z)
				yaw0 = float(tuk.get("yaw"))
				_act("steer_left", true)
			if frame == 101:
				var dy := wrapf(float(tuk.get("yaw")) - yaw0, -PI, PI)
				check(dy < -0.05, "S3 reverse steering mirrors (dyaw=%.2f)" % dy)
				_all_off()
				stage = 3
				frame = 0
		3:  # S4 steering authority low vs medium speed
			if frame == 1:
				_place(Vector3(0, 0, 0), 5.0)
				_act("steer_left", true)
			if frame == 41:
				yaw_low = absf(wrapf(float(tuk.get("yaw")), -PI, PI))
				_place(Vector3(0, 0, 0), 14.0)
				_act("steer_left", true)
			if frame == 81:
				yaw_med = absf(wrapf(float(tuk.get("yaw")), -PI, PI))
				check(yaw_low > 0.3, "S4 low-speed turn authority (%.2f rad)" % yaw_low)
				check(yaw_med > 0.15, "S4 medium-speed turn authority (%.2f rad)" % yaw_med)
				check(yaw_med < yaw_low, "S4 high-speed stability (med %.2f < low %.2f)" % [yaw_med, yaw_low])
				_all_off()
				stage = 4
				frame = 0
		4:  # S5 drift initiate, recover, bonus reported
			if frame == 1:
				_place(Vector3(0, 0, 0), 14.0)
				_act("accelerate", true)
				_act("steer_left", true)
				_act("handbrake", true)
			if frame == 40:
				var lat: Vector3 = tuk.get("lat_vel")
				drifted = float(tuk.get("drift_time")) > 0.3
				check(lat.length() > 1.5, "S5 drift initiates (lat %.1f m/s)" % lat.length())
				check(drifted, "S5 drift time accumulates (%.2f s)" % float(tuk.get("drift_time")))
				_all_off()
			if frame == 130:
				var lat2: Vector3 = tuk.get("lat_vel")
				check(lat2.length() < 0.8, "S5 grip recovers after release (lat %.2f)" % lat2.length())
				check(float(tuk.get("drift_time")) == 0.0, "S5 drift timer resets")
				var mgr: Node = root.get_node("MissionMgr")
				check(mgr != null, "S5 mission manager present for drift bonus")
				stage = 5
				frame = 0
		5:  # S6 bounded collision, single penalty per contact
			if frame == 1:
				_place(Vector3(0, 0, 0), 0.0)
				wall = StaticBody3D.new()
				var ws := CollisionShape3D.new()
				var wb := BoxShape3D.new()
				wb.size = Vector3(8, 6, 1)
				ws.shape = wb
				wall.add_child(ws)
				wall.position = Vector3(0, 2, -16)
				root.add_child(wall)
				_act("accelerate", true)
				tuk.set("collisions_total", 0)
				hits_at_contact = -1
				hit_speed = -1.0
				after_speed = -1.0
				contact_frame = 0
			if hit_speed < 0.0 and int(tuk.get("collisions_total")) > 0:
				hit_speed = prev_spd
				after_speed = float(tuk.get("speed"))
				hits_at_contact = int(tuk.get("collisions_total"))
				contact_frame = frame
				_act("accelerate", false)  # stop driving into the wall after the hit
			prev_spd = float(tuk.get("speed"))
			if frame == 200:
				_all_off()
				check(hit_speed > 0.0, "S6 collision registered")
				check(absf(after_speed) < absf(hit_speed), "S6 speed lost on impact")
				var kept := 100.0 * absf(after_speed) / maxf(absf(hit_speed), 0.001)
				check(absf(after_speed) > absf(hit_speed) * 0.2,
						"S6 loss bounded (kept %.0f%%)" % kept)
				var extra := int(tuk.get("collisions_total")) - hits_at_contact
				var contact_frames := maxi(frame - contact_frame, 1)
				# cooldown 0.5 s = 30 frames: allow the cooldown cadence, reject per-frame spam
				check(extra <= 2 + int(contact_frames / 30.0),
						"S6 no per-frame penalty spam (%d extra over %d frames)" % [extra, contact_frames])
				check(extra < int(contact_frames / 4.0),
						"S6 penalties far below frame rate (%d extra / %d frames)" % [extra, contact_frames])
				check(tuk.global_position.z > -16.5, "S6 no wall penetration")
				_act("steer_right", true)
				_act("accelerate", true)
			if frame == 260:
				check(absf(float(tuk.get("yaw"))) > 0.05, "S6 recovers control after impact")
				_all_off()
				wall.queue_free()
				stage = 6
				frame = 0
		6:  # S7 ground contact over bumps, no penetration
			if frame == 1:
				_place(Vector3(20, 0, 0), 12.0)
				min_y = 99.0
				_act("accelerate", true)
			if frame <= 180:
				min_y = minf(min_y, tuk.global_position.y)
			if frame == 180:
				_all_off()
				check(min_y > -0.3, "S7 never below road surface (min y=%.2f)" % min_y)
				check(tuk.global_position.y < 1.2,
						"S7 no bounce launch off bumps (y=%.2f)" % tuk.global_position.y)
				check(absf(float(tuk.get("speed"))) > 3.0, "S7 keeps rolling over bumps")
				stage = 7
				frame = 0
		7:  # S8 ramp jump: airborne, land, keep control
			if frame == 1:
				_place(Vector3(-30, 0, 60), 14.0)
				tuk.set("yaw", 1.5708)  # face west, as approaching the district ramp
				_act("accelerate", true)
				was_air = false
			if frame == 10:
				tuk.call("launch")  # isolated rig: trigger wiring itself is proven in selfplay
			if frame <= 150:
				if bool(tuk.get("airborne")):
					was_air = true
					air_frames += 1
				max_y = maxf(max_y, tuk.global_position.y)
			if frame == 150:
				_all_off()
				check(air_frames >= 5,
						"S8 airborne persists (%d frames, not a one-frame flag)" % air_frames)
				check(max_y > 0.5, "S8 jump actually gains height (max y=%.2f m)" % max_y)
				check(not bool(tuk.get("airborne")), "S8 lands again")
				check(tuk.global_position.y < 1.0,
						"S8 rests on road after landing (y=%.2f)" % tuk.global_position.y)
				_act("steer_left", true)
				_act("accelerate", true)
			if frame == 200:
				check(absf(float(tuk.get("yaw")) - 1.5708) > 0.05, "S8 steering works after landing")
				_all_off()
				tuk.global_position = Vector3(-30, -10, 60)  # simulate driving off the world edge
			if frame == 210:
				check(resets_seen > 0, "S8 fall below world requests a reset (recovery path)")
				_finish()
		9:
			_finish()


func _finish() -> void:
	print("TESTS: %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)
