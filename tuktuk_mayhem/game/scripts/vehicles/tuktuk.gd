extends CharacterBody3D
## Arcade tuk-tuk controller, Phase 2 revision (docs/PHASE2_REPORT.md §5-§8):
## same architecture as Phase 1 (CharacterBody3D + scalar speed + lateral slip, data-driven),
## with: tapered acceleration, smoothed steer with return-to-center, smoothed grip transition
## for controlled drifting (clamped lateral velocity, drift-time tracking), designated ramp-jump
## trigger + airborne/landing states, severity-scaled collision response with a penalty cooldown
## (no scrape spam), and a VISUAL-ONLY body layer (pitch/roll/squash) that never touches physics.

signal impacted(strength: float)
signal landed(strength: float)
signal request_reset

const MeshBuilder := preload("res://scripts/core/mesh_builder.gd")
const MaterialsLib := preload("res://scripts/core/materials.gd")

var params: Dictionary = {}
var yaw: float = 0.0
var speed: float = 0.0            # signed forward speed (m/s)
var lat_vel: Vector3 = Vector3.ZERO
var steer: float = 0.0            # smoothed steer actually applied
var collisions_total: int = 0
var airborne := false
var drift_time := 0.0             # current continuous drift duration (s)
var _steer_in := 0.0
var _grip: float = 8.0
var _impact_cd := 0.0
var _upside_time := 0.0
var _was_air := false
var _ground: RayCast3D
var _body: MeshInstance3D
var _vis_pitch := 0.0
var _vis_roll := 0.0
var _vis_squash := 1.0
var _wheel_spin := 0.0


func _ready() -> void:
	params = Reg.vehicle()
	_grip = float(params.get("grip_lat", 8.0))
	_ground = RayCast3D.new()
	# short ground feeler: hits while resting (y ~ 0.4) and on touchdown, misses in flight,
	# so "grounded" never flickers at rest (that flicker silently aborted launch())
	_ground.target_position = Vector3(0, -0.55, 0)
	add_child(_ground)
	_build_mesh()


func _build_mesh() -> void:
	_body = MeshInstance3D.new()
	_body.name = "BodyMesh"
	_body.mesh = MeshBuilder.build("tuktuk")
	add_child(_body)
	MaterialsLib.apply_to(_body, MaterialsLib.lib())


## Designated ramp launch (district ramp trigger calls this): bounded, speed-scaled, testable.
func launch() -> void:
	if airborne:
		return
	var vmax: float = float(params.get("vmax", 20.0))
	if abs(speed) < float(params.get("jump_speed_min", 8.0)):
		return
	velocity.y = float(params.get("jump_impulse", 9.0)) * clampf(abs(speed) / vmax, 0.5, 0.85)
	airborne = true
	_was_air = true


func is_drifting() -> bool:
	return drift_time > 0.0


func forward() -> Vector3:
	return Vector3(-sin(yaw), 0, -cos(yaw))


func speed_kmh() -> float:
	return abs(speed) * 3.6


func _physics_process(delta: float) -> void:
	var p: Dictionary = params
	var vmax: float = float(p.get("vmax", 20.0))
	var thr := Input.get_axis("brake", "accelerate")   # -1 brake/reverse, +1 throttle
	_steer_in = Input.get_axis("steer_left", "steer_right")
	var hand: bool = Input.is_action_pressed("handbrake")

	# --- smoothed steer with return-to-center (visual + mechanical)
	var k_steer := 1.0 - exp(-float(p.get("steer_smooth", 10.0)) * delta)
	steer += (_steer_in - steer) * k_steer
	if _steer_in == 0.0:
		steer = move_toward(steer, 0.0, float(p.get("steer_return", 8.0)) * delta)

	# --- acceleration with top-end taper; brake; intentional brake-to-reverse
	var accel_eff := float(p.get("accel", 10.0))
	if thr > 0.0:
		var ratio := clampf(speed / vmax, 0.0, 1.0)
		accel_eff *= 1.0 - float(p.get("accel_taper", 0.55)) * ratio * ratio
		speed += accel_eff * thr * delta
	elif thr < 0.0:
		if speed > 0.5:
			speed += float(p.get("brake", 20.0)) * thr * delta
		else:
			var rev: float = -float(p.get("vreverse_max", 5.0))
			speed = maxf(speed - float(p.get("accel", 10.0)) * 0.5 * delta, rev)
	speed -= speed * float(p.get("drag", 0.5)) * delta
	speed = move_toward(speed, 0.0, float(p.get("roll_resist", 1.0)) * delta)
	speed = clampf(speed, -float(p.get("vreverse_max", 5.0)), vmax)

	# --- steering authority: lively at low speed, stable at high speed
	var fade := 1.0 - float(p.get("steer_speed_fade", 0.4)) * clampf(abs(speed) / vmax, 0.0, 1.0)
	var turn := steer * float(p.get("steer_rate", 2.2)) * fade * delta
	if abs(speed) > 0.3:
		yaw -= turn * signf(speed)

	# --- controlled drift: smoothed grip transition, clamped slip, drift-time tracking
	var fwd := forward()
	var right_v := Vector3(-fwd.z, 0, fwd.x)
	var fast_steer: bool = abs(steer) > 0.8 and abs(speed) > float(p.get("drift_speed_min", 10.0))
	var drifting: bool = (hand or fast_steer) and abs(speed) > 3.0
	var grip_want: float = float(p.get("drift_grip_lat", 2.5)) if drifting \
		else float(p.get("grip_lat", 8.0))
	_grip += (grip_want - _grip) * (1.0 - exp(-float(p.get("drift_grip_smooth", 6.0)) * delta))
	lat_vel -= right_v * speed * turn * 0.9
	lat_vel -= lat_vel * minf(_grip * delta, 1.0)
	var lat_max: float = float(p.get("lat_max", 8.0))
	if lat_vel.length() > lat_max:
		lat_vel = lat_vel.normalized() * lat_max
	var sliding := lat_vel.length() > 1.5 and absf(speed) > 5.0
	if sliding:
		drift_time += delta
	else:
		if drift_time >= float(p.get("drift_min_s", 0.7)):
			MissionMgr.report_drift(drift_time)
		drift_time = 0.0

	# --- slope slide from ground ray
	var slope_push := Vector3.ZERO
	if _ground.is_colliding():
		var n: Vector3 = _ground.get_collision_normal()
		slope_push = Vector3(n.x, 0, n.z) * float(p.get("slope_slide", 5.0)) * delta

	# --- integrate; airborne gravity; landing detection (no bounce: y clamped on contact)
	var was_falling := velocity.y
	var planar := fwd * speed + lat_vel + slope_push
	# Vertical integration: a POSITIVE y velocity (ramp launch impulse) must survive the
	# ground frame; clamping it to <=0 while on the floor silently cancels launch() (found by
	# the render dumps: y never left the road). Resting stays pinned, landings never bounce.
	var yv := velocity.y
	if is_on_floor():
		yv = maxf(yv, 0.0)
	else:
		yv -= 18.0 * delta
	velocity = planar + Vector3(0, yv, 0)
	move_and_slide()
	# grounded = floor contact OR standing in feeler reach without real upward velocity
	var grounded := is_on_floor() or (_ground.is_colliding() and velocity.y < 0.5)
	airborne = not grounded
	if _was_air and not airborne:
		var fall := -was_falling
		if fall > float(p.get("landing_min", 3.0)):
			landed.emit(fall)
			speed *= 0.95
			_vis_squash = 0.92
		lat_vel *= 0.7
	_was_air = airborne

	# --- collisions: severity-scaled, cooldown-gated (no per-frame scrape penalties).
	# A floor contact (normal pointing up) is NOT a crash: without this filter, simply
	# driving would count as a collision every cooldown tick and spam penalties/shake.
	_impact_cd = maxf(_impact_cd - delta, 0.0)
	var wall_hit := false
	for i in get_slide_collision_count():
		if get_slide_collision(i).get_normal().y < 0.6:
			wall_hit = true
			break
	var planar_speed := planar.length()
	var hard_hit: bool = wall_hit and _impact_cd <= 0.0 \
		and planar_speed > float(p.get("impact_min", 3.0))
	if hard_hit:
		var sev := clampf(planar_speed / vmax, 0.25, 1.0)
		speed *= 1.0 - clampf(float(p.get("impact_loss", 0.3)), 0.0, 0.8) * sev
		lat_vel *= 0.4
		collisions_total += 1
		_impact_cd = float(p.get("impact_cooldown_s", 0.5))
		MissionMgr.report_collision()
		impacted.emit(planar_speed)

	# --- flip protection (arcade convention): upright after resting on side/roof
	if transform.basis.y.dot(Vector3.UP) < float(p.get("upright_min_dot", 0.35)):
		_upside_time += delta
		if _upside_time > float(p.get("reset_after_s", 1.4)):
			request_reset.emit()
			_upside_time = 0.0
	else:
		_upside_time = 0.0
	# fall recovery: driven off the world edge -> ask the district for a reset (no void death)
	if global_position.y < float(p.get("fall_reset_y", -5.0)):
		request_reset.emit()
	transform.basis = Basis(Vector3.UP, yaw)
	_wheel_spin += speed * delta * 3.0
	_visual_body(delta, thr)


## Visual-only body response (pitch/roll/squash) on a child node: physics root stays clean.
func _visual_body(delta: float, thr: float) -> void:
	if _body == null:
		return
	var vmax: float = float(params.get("vmax", 20.0))
	var pitch_want := clampf(-thr * 0.035 * clampf(abs(speed) / vmax + 0.3, 0.0, 1.0), -0.05, 0.06)
	var roll_want := clampf(-steer * clampf(speed / vmax, -1.0, 1.0) * 0.07
			- lat_vel.dot(Vector3(-forward().z, 0, forward().x)) * 0.008, -0.12, 0.12)
	if airborne:
		pitch_want = 0.08
	var k := 1.0 - exp(-8.0 * delta)
	_vis_pitch += (pitch_want - _vis_pitch) * k
	_vis_roll += (roll_want - _vis_roll) * k
	_vis_squash += (1.0 - _vis_squash) * (1.0 - exp(-6.0 * delta))
	_body.transform = Transform3D(Basis().rotated(Vector3.RIGHT, _vis_pitch)
			.rotated(Vector3.FORWARD, _vis_roll), Vector3.ZERO) * Transform3D(
			Basis().scaled(Vector3(1.0, _vis_squash, 1.0)), Vector3(0, 0.85 * (1.0 - _vis_squash), 0))
