extends Camera3D
## Arcade chase camera (ART_BIBLE §2.1): spring arm behind/above, FOV ramps with speed,
## damped yaw, ray-shortened arm so walls never swallow the view.

@export var dist: float = 5.2
@export var height: float = 2.4
@export var fov_min: float = 68.0
@export var fov_max: float = 84.0

var target: Node3D = null
var _yaw: float = 0.0
var _arm: RayCast3D


func _ready() -> void:
	_arm = RayCast3D.new()
	_arm.collision_mask = 1
	add_child(_arm)


func _physics_process(delta: float) -> void:
	if target == null or not is_instance_valid(target):
		return
	var tpos := target.global_position + Vector3(0, 1.1, 0)
	var desired_yaw: float = target.get("yaw") if target.get("yaw") != null else _yaw
	# damped yaw follow (never snap), shortest angular path
	var diff := wrapf(desired_yaw - _yaw, -PI, PI)
	_yaw += diff * minf(6.0 * delta, 1.0)
	var back := Vector3(-sin(_yaw), 0, -cos(_yaw))
	var want := tpos - back * dist + Vector3(0, height, 0)
	# collision-aware arm: shorten if a wall is between target and camera
	_arm.global_position = tpos
	_arm.global_rotation = Vector3.ZERO
	_arm.target_position = (want - tpos)
	_arm.force_raycast_update()
	var arm_len := (want - tpos).length()
	if _arm.is_colliding():
		arm_len = minf(arm_len, (tpos - _arm.get_collision_point()).length() - 0.3)
	arm_len = maxf(arm_len, 1.6)
	want = tpos + (want - tpos).normalized() * arm_len
	global_position = global_position.lerp(want, minf(10.0 * delta, 1.0))
	look_at(tpos + Vector3(0, 0.35, 0), Vector3.UP)
	var spd: float = float(target.get("speed")) if target.get("speed") != null else 0.0
	var vmax: float = float(Reg.vehicle().get("vmax", 20.0))
	fov = lerpf(fov_min, fov_max, clampf(abs(spd) / vmax, 0.0, 1.0))
