extends SceneTree
## Scenario 9 of the Phase 2 QA matrix: chase-camera behaviour (main loop, --fixed-fps 60).
## Measurable checks: first-frame snap (no origin transient), bounded arm distance through
## driving/turns/collisions/reverse, pitch sanity, no oscillation at rest, finite transforms.

var checks := 0
var fails := 0
var frame := 0
var stage := 0
var tuk: Node3D = null
var cam: Node3D = null
var rest_pos := Vector3.ZERO


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


func _dist() -> float:
	return (cam.global_position - tuk.global_position).length()


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
	cam = (load("res://scripts/vehicles/chase_cam.gd") as GDScript).new()
	root.add_child(cam)
	cam.set("target", tuk)


func _process(_d: float) -> void:
	frame += 1
	match stage:
		0:  # first-frame snap: camera must already be near the vehicle on frame 2
			if frame == 2:
				check(_dist() < 8.0, "C1 camera snaps to arm on first frames (d=%.1f)" % _dist())
				_act("accelerate", true)
			if frame == 120:
				check(_dist() > 1.4 and _dist() < 7.5, "C2 arm distance in driving bounds (%.1f)" % _dist())
				var pitch: float = cam.global_rotation_degrees.x
				check(pitch < -5.0 and pitch > -80.0, "C2 pitch sane (%.1f deg)" % pitch)
				stage = 1
				frame = 0
		1:  # sharp turn: vehicle stays framed, no wild swing
			if frame == 1:
				_act("steer_left", true)
			if frame == 60:
				check(_dist() < 8.5, "C3 framed through a sharp turn (%.1f)" % _dist())
				var cam_yaw := cam.global_rotation_degrees.y
				var tuk_yaw := rad_to_deg(float(tuk.get("yaw")))
				var ydiff := absf(wrapf(deg_to_rad(cam_yaw - tuk_yaw), -PI, PI))
				check(ydiff < 1.2, "C3 camera yaw tracks heading (%.0f deg)" % rad_to_deg(ydiff))
				_act("steer_left", false)
				stage = 2
				frame = 0
		2:  # collision: camera keeps following, shake bounded
			if frame == 1:
				tuk.set("yaw", 0.0)
				tuk.global_position = Vector3(0, 0.4, 0)
				tuk.set("speed", 0.0)
				var wall := StaticBody3D.new()
				var ws := CollisionShape3D.new()
				var wb := BoxShape3D.new()
				wb.size = Vector3(8, 6, 1)
				ws.shape = wb
				wall.add_child(ws)
				wall.position = Vector3(0, 2, -14)
				wall.name = "CamWall"
				root.add_child(wall)
				_act("accelerate", true)
			if frame == 150:
				_act("accelerate", false)
				check(_dist() < 8.5, "C4 camera follows through impact (%.1f)" % _dist())
				check(is_finite(cam.global_position.x) and is_finite(cam.global_position.y),
						"C4 camera transform finite")
				root.get_node("CamWall").queue_free()
				stage = 3
				frame = 0
		3:  # rest: no oscillation
			if frame == 1:
				tuk.set("speed", 0.0)
				tuk.set("lat_vel", Vector3.ZERO)
			if frame == 40:
				rest_pos = cam.global_position
			if frame == 100:
				check((cam.global_position - rest_pos).length() < 0.05,
						"C5 no oscillation at rest (drift %.3f)" % (cam.global_position - rest_pos).length())
				stage = 4
				frame = 0
		4:  # reverse stays readable
			if frame == 1:
				_act("brake", true)
			if frame == 70:
				check(float(tuk.get("speed")) < -1.0, "C6 reversing")
				check(_dist() < 7.0, "C6 reverse pull-in keeps tight frame (%.1f)" % _dist())
				_act("brake", false)
				_finish()
		9:
			_finish()


func _finish() -> void:
	print("TESTS: %d checks, %d failed -> %s" % [checks, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)
