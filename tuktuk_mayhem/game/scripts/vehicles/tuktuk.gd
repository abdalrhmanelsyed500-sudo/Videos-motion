extends CharacterBody3D
## Arcade tuk-tuk controller (TDD §2): scalar speed along heading + lateral slip, tuned from
## res://data/vehicles/tuktuk_base.json. CharacterBody3D chosen for determinism and stable
## collisions.

signal impacted(strength: float)
signal request_reset

const MeshBuilder := preload("res://scripts/core/mesh_builder.gd")
const MaterialsLib := preload("res://scripts/core/materials.gd")

var params: Dictionary = {}
var yaw: float = 0.0
var speed: float = 0.0            # signed forward speed (m/s)
var lat_vel: Vector3 = Vector3.ZERO
var steer: float = 0.0
var collisions_total: int = 0
var _upside_time: float = 0.0
var _ground: RayCast3D
var _wheels: Array = []
var _wheel_spin: float = 0.0


func _ready() -> void:
	params = Reg.vehicle()
	_ground = RayCast3D.new()
	_ground.target_position = Vector3(0, -1.2, 0)
	add_child(_ground)
	for child in get_children():
		if child.name.begins_with("Wheel"):
			_wheels.append(child)
	_build_mesh()


func _build_mesh() -> void:
	var mi := MeshInstance3D.new()
	mi.name = "BodyMesh"
	mi.mesh = MeshBuilder.build("tuktuk")
	add_child(mi)
	MaterialsLib.apply_to(mi, MaterialsLib.lib())
	for i in range(3):  # three wheels are baked into the body mesh for P1; spin nodes are visual hubs
		var w := MeshInstance3D.new()
		w.name = "Wheel%d" % i
		w.mesh = MeshBuilder.build("wheel")
		var pos: Vector3 = [Vector3(0, 0, -1.35), Vector3(-0.68, 0, 0.95), Vector3(0.61, 0, 0.95)][i]
		w.position = pos
		w.visible = false  # body mesh already carries wheels; hubs reserved for Phase 2 steering visual
		add_child(w)


func forward() -> Vector3:
	return Vector3(-sin(yaw), 0, -cos(yaw))


func speed_kmh() -> float:
	return abs(speed) * 3.6


func _physics_process(delta: float) -> void:
	var p: Dictionary = params
	var vmax: float = float(p.get("vmax", 20.0))
	var thr := Input.get_axis("brake", "accelerate")   # -1 brake/reverse, +1 throttle
	steer = Input.get_axis("steer_left", "steer_right")
	var hand: bool = Input.is_action_pressed("handbrake")

	if thr > 0.0:
		speed += float(p.get("accel", 10.0)) * thr * delta
	elif thr < 0.0:
		if speed > 0.5:
			speed += float(p.get("brake", 20.0)) * thr * delta
		else:
			var rev: float = -float(p.get("vreverse_max", 5.0))
			speed = maxf(speed - float(p.get("accel", 10.0)) * 0.5 * delta, rev)
	# drag + rolling resistance
	speed -= speed * float(p.get("drag", 0.5)) * delta
	var rr: float = float(p.get("roll_resist", 1.0)) * delta
	speed = move_toward(speed, 0.0, rr)
	speed = clampf(speed, -float(p.get("vreverse_max", 5.0)), vmax)

	# steering: rate fades with speed, reverses in reverse gear
	var fade := 1.0 - float(p.get("steer_speed_fade", 0.4)) * clampf(abs(speed) / vmax, 0.0, 1.0)
	var turn := steer * float(p.get("steer_rate", 2.2)) * fade * delta
	if abs(speed) > 0.3:
		yaw -= turn * signf(speed)
	# lateral slip: grip kills sideways velocity; handbrake/fast steer breaks grip (controlled drift)
	var fwd := forward()
	var right_v := Vector3(-fwd.z, 0, fwd.x)
	var fast_steer: bool = abs(steer) > 0.8 and abs(speed) > float(p.get("drift_speed_min", 10.0))
	var drifting: bool = hand or fast_steer
	var grip: float = float(p.get("grip_lat", 8.0))
	if drifting:
		grip = float(p.get("drift_grip_lat", 2.5))
	lat_vel -= right_v * (speed * turn / maxf(delta, 0.0001)) * delta * 0.9
	lat_vel -= lat_vel * minf(grip * delta, 1.0)

	# slope slide from ground ray
	var slope_push := Vector3.ZERO
	if _ground.is_colliding():
		var n: Vector3 = _ground.get_collision_normal()
		slope_push = Vector3(n.x, 0, n.z) * float(p.get("slope_slide", 5.0)) * delta

	var planar := fwd * speed + lat_vel + slope_push
	velocity = planar + Vector3(0, velocity.y - 9.8 * delta if not is_on_floor() else 0.0, 0)
	if is_on_floor():
		velocity.y = minf(velocity.y, 0.0)
	move_and_slide()

	# impacts: lose speed, count for reward penalty, tell HUD
	if get_slide_collision_count() > 0:
		var impact := velocity.length()
		if impact > 1.5:
			speed *= 1.0 - clampf(float(p.get("impact_loss", 0.3)), 0.0, 0.8)
			lat_vel *= 0.4
			collisions_total += 1
			MissionMgr.report_collision()
			impacted.emit(impact)

	# flip protection (arcade convention, TDD §2): upright after resting on side/roof
	if transform.basis.y.dot(Vector3.UP) < float(p.get("upright_min_dot", 0.35)):
		_upside_time += delta
		if _upside_time > float(p.get("reset_after_s", 1.4)):
			request_reset.emit()
			_upside_time = 0.0
	else:
		_upside_time = 0.0
	transform.basis = Basis(Vector3.UP, yaw)
	_wheel_spin += speed * delta * 3.0

