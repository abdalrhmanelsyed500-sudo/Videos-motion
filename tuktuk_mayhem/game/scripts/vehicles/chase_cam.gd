extends Camera3D
## Arcade chase camera, Phase 2 revision (see docs/PHASE2_REPORT.md §4 for the diagnosis):
## - first physics frame SNAPS to the arm pose (kills the scene-change black-frame transient),
## - frame-rate-independent exponential smoothing for position, yaw and FOV (no snap on impacts),
## - look-ahead aim blended from the travel direction (road readability + drift visibility),
## - reverse pull-in so backing up stays readable,
## - ray-shortened spring arm against walls/buildings,
## - bounded decaying impact shake proportional to collision severity.

@export var dist: float = 5.2
@export var height: float = 2.4
@export var fov_min: float = 68.0
@export var fov_max: float = 84.0

var target: Node3D = null
var _yaw: float = 0.0
var _fov: float = 68.0
var _shake: float = 0.0
var _armed := false
var _arm: RayCast3D


func _ready() -> void:
	_arm = RayCast3D.new()
	_arm.collision_mask = 1
	add_child(_arm)


## Collision feedback hook (tuktuk "impacted"/"landed" signals): bounded, decaying.
func add_shake(strength: float) -> void:
	_shake = minf(_shake + clampf(strength, 0.0, 20.0) * 0.02, 0.35)


func _physics_process(delta: float) -> void:
	if target == null or not is_instance_valid(target):
		return
	var spd: float = float(target.get("speed")) if target.get("speed") != null else 0.0
	var vmax: float = float(Reg.vehicle().get("vmax", 20.0))
	var pivot := target.global_position + Vector3(0, 1.1, 0)

	# --- yaw: damped follow of the vehicle heading (never snaps, shortest arc)
	var desired_yaw: float = float(target.get("yaw")) if target.get("yaw") != null else _yaw
	var k_yaw := 1.0 - exp(-6.0 * delta)
	_yaw += wrapf(desired_yaw - _yaw, -PI, PI) * k_yaw

	# --- spring arm (shorter when reversing for a tighter, readable backing view)
	var arm_dist := dist * (0.85 if spd < -0.5 else 1.0)
	var back := Vector3(-sin(_yaw), 0, -cos(_yaw))
	var want := pivot - back * arm_dist + Vector3(0, height, 0)
	_arm.global_position = pivot
	_arm.global_rotation = Vector3.ZERO
	_arm.target_position = want - pivot
	_arm.force_raycast_update()
	var arm_len := (want - pivot).length()
	if _arm.is_colliding():
		arm_len = minf(arm_len, (pivot - _arm.get_collision_point()).length() - 0.3)
	arm_len = maxf(arm_len, 1.6)
	want = pivot + (want - pivot).normalized() * arm_len

	# --- position: exponential smoothing; first frame snaps (no origin lerp transient)
	if not _armed:
		global_position = want
		_fov = lerpf(fov_min, fov_max, clampf(abs(spd) / vmax, 0.0, 1.0))
		_armed = true
	else:
		var k_pos := 1.0 - exp(-10.0 * delta)
		global_position = global_position.lerp(want, k_pos)

	# --- aim: pivot + look-ahead along the travel direction (heading when nearly still)
	var fwd := Vector3(-sin(_yaw), 0, -cos(_yaw))
	var lat: Vector3 = target.get("lat_vel") if target.get("lat_vel") != null else Vector3.ZERO
	var travel := fwd * spd + lat
	var aim_dir := fwd
	if travel.length() > 1.0:
		aim_dir = travel.normalized()
	var look_ahead := clampf(2.0 + abs(spd) * 0.15, 2.0, 6.0)
	if spd < -0.5:
		look_ahead = -2.5  # reversing: show where we are going
	var aim := pivot + aim_dir * look_ahead + Vector3(0, 0.35, 0)
	look_at(aim, Vector3.UP)

	# --- FOV: smoothed ramp (no jump when an impact kills the speed)
	var fov_want := lerpf(fov_min, fov_max, clampf(abs(spd) / vmax, 0.0, 1.0))
	_fov += (fov_want - _fov) * (1.0 - exp(-4.0 * delta))
	fov = _fov

	# --- impact shake: bounded, decaying, cheap
	if _shake > 0.001:
		_shake = maxf(_shake - 1.2 * delta, 0.0)
		global_position += Vector3(randf_range(-1.0, 1.0), randf_range(-0.6, 0.6), 0.0) * _shake * 0.12
