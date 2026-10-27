extends CharacterBody3D
class_name AGMotorcycleController
## Arcade motorcycle dynamics, rider/bike visuals, collisions and falling.

signal state_changed(state: Dictionary)
signal crashed(reason: String, severity: int)
signal fall_finished()
signal near_miss()
signal boost_changed(value: float)

var rider_data: Dictionary = {}
var bike_data: Dictionary = {}
var is_player := false
var difficulty := 1
var bike_view: AGBikeView
var rider_view: AGRiderView
var hitbox: Area3D

var speed := 0.0
var max_speed := 60.0
var acceleration := 15.0
var braking := 26.0
var handling := 0.85
var mass := 120.0
var gear := 1
var rpm := 0.18
var boost_energy := 1.0
var steer := 0.0
var lean := 0.0
var wobble := 0.0
var crash_cooldown := 0.0
var camera_shake := 0.0
var can_drive := false
var crash_active := false
var test_input: Variant = null
var brain: AGRivalBrain
var crash_count := 0
var near_miss_count := 0
var top_speed := 0.0
var start_z := 0.0
var last_input: Dictionary = {}
var rng := RandomNumberGenerator.new()
var _state_timer := 0.0

func _ready() -> void:
    rng.seed = int(Time.get_unix_time_from_system()) + get_instance_id()
    motion_mode = CharacterBody3D.MOTION_MODE_FLOATING
    floor_snap_length = 0.0
    _build_collision()
    if not bike_data.is_empty():
        _build_visuals()

func setup(rider: Dictionary, bike: Dictionary, player_flag: bool, difficulty_level: int) -> void:
    rider_data = rider.duplicate(true)
    bike_data = bike.duplicate(true)
    is_player = player_flag
    difficulty = clampi(difficulty_level, 0, 2)
    var diff_mult: float = [0.96, 1.0, 1.035][difficulty]
    max_speed = float(bike.get("top_speed", 60.0)) * diff_mult
    acceleration = float(bike.get("acceleration", 15.0)) * diff_mult
    braking = float(bike.get("braking", 26.0))
    handling = float(bike.get("handling", 0.85))
    mass = float(bike.get("mass", 120.0))
    start_z = AGRoadPath.START_Z
    if is_inside_tree():
        _build_visuals()

func _build_collision() -> void:
    for child in get_children():
        if child is CollisionShape3D or child is Area3D:
            child.queue_free()
    var body_shape := CollisionShape3D.new()
    var capsule := CapsuleShape3D.new()
    capsule.radius = 0.42
    capsule.height = 1.45
    body_shape.shape = capsule
    body_shape.position = Vector3(0.0, 0.82, 0.0)
    add_child(body_shape)

    hitbox = Area3D.new()
    hitbox.name = "Hitbox"
    hitbox.collision_layer = 1 if is_player else 2
    hitbox.collision_mask = 2 if is_player else 0
    hitbox.monitoring = is_player
    hitbox.monitorable = true
    var hit_shape := CollisionShape3D.new()
    var box := BoxShape3D.new()
    box.size = Vector3(0.95, 1.55, 1.85)
    hit_shape.shape = box
    hit_shape.position = Vector3(0.0, 0.85, 0.0)
    hitbox.add_child(hit_shape)
    add_child(hitbox)
    hitbox.area_entered.connect(_on_hit_area_entered)

func _build_visuals() -> void:
    for child in get_children():
        if child is AGBikeView:
            child.queue_free()
    bike_view = AGBikeFactory.build(bike_data)
    add_child(bike_view)
    rider_view = AGRiderFactory.build(rider_data)
    bike_view.rider_anchor.add_child(rider_view)

func set_visual_visible(value: bool) -> void:
    if bike_view != null:
        bike_view.visible = value

func set_test_input(value: Variant) -> void:
    test_input = value

func get_state() -> Dictionary:
    return {
        "speed": speed,
        "speed_kmh": speed * 3.6,
        "max_speed": max_speed,
        "gear": gear,
        "rpm": rpm,
        "boost": boost_energy,
        "progress": AGRoadPath.progress(position.z),
        "position": Vector3(position),
        "crashes": crash_count,
        "near_misses": near_miss_count,
        "top_speed": top_speed,
        "can_drive": can_drive,
        "crash_active": crash_active,
        "wheel_angle": bike_view.wheel_angle if bike_view != null else 0.0,
    }

func _physics_process(delta: float) -> void:
    if crash_active:
        speed = lerpf(speed, 0.0, 1.0 - exp(-2.4 * delta))
        velocity = Vector3.ZERO
        move_and_slide()
        return
    var input: Dictionary = _read_input(delta)
    last_input = input
    _update_speed(delta, input)
    _update_steering(delta, input)
    _update_drivetrain()
    _move(delta, input)
    _animate(delta, input)
    crash_cooldown = maxf(0.0, crash_cooldown - delta)
    camera_shake = maxf(0.0, camera_shake - delta * 1.8)
    wobble = lerpf(wobble, 0.0, 1.0 - exp(-3.5 * delta))
    top_speed = maxf(top_speed, speed)
    if is_player:
        AGAudio.set_engine_state(speed, rpm, float(input.get("throttle", 0.0)))
    _state_timer -= delta
    if _state_timer <= 0.0:
        _state_timer = 0.08
        state_changed.emit(get_state())

func _read_input(delta: float) -> Dictionary:
    if brain != null:
        return AGInputProvider._normalized(brain.decide(self, delta))
    return AGInputProvider.read(self)

func _update_speed(delta: float, input: Dictionary) -> void:
    var throttle := float(input.get("throttle", 0.0))
    var brake := float(input.get("brake", 0.0))
    var handbrake := float(input.get("handbrake", 0.0))
    var boost := float(input.get("boost", 0.0))
    var boost_active := boost > 0.15 and boost_energy > 0.02 and can_drive
    var current_max := max_speed + (8.0 if boost_active else 0.0)
    if not can_drive:
        throttle = 0.0
        boost_active = false
    if throttle > 0.0:
        var falloff: float = clampf(1.0 - speed / maxf(current_max, 1.0), 0.05, 1.0)
        speed += acceleration * throttle * (0.35 + falloff * 0.9) * delta
    else:
        speed -= 3.5 * delta
    if boost_active:
        speed += 11.0 * delta
        boost_energy = maxf(0.0, boost_energy - 0.30 * delta)
        boost_changed.emit(boost_energy)
    else:
        boost_energy = minf(1.0, boost_energy + 0.075 * delta)
    if brake > 0.0:
        speed -= braking * brake * delta
    if handbrake > 0.0:
        speed -= braking * 1.15 * handbrake * delta
    speed = clampf(speed, 0.0, current_max)

func _update_steering(delta: float, input: Dictionary) -> void:
    var input_steer := float(input.get("steer", 0.0))
    var speed_factor: float = 1.0 - clampf(speed / maxf(max_speed, 1.0), 0.0, 1.0) * 0.42
    var handbrake_bonus: float = 1.0 + float(input.get("handbrake", 0.0)) * 0.25
    var target: float = input_steer * speed_factor * handling * handbrake_bonus
    steer = lerpf(steer, target, 1.0 - exp(-9.0 * delta))
    lean = lerpf(lean, -steer * clampf(speed / 30.0, 0.0, 1.0) * 0.35, 1.0 - exp(-8.0 * delta))

func _update_drivetrain() -> void:
    var span: float = maxf(max_speed / 6.0, 1.0)
    gear = clampi(int(speed / span) + 1, 1, 6)
    var within: float = fmod(speed, span) / span
    var throttle: float = float(last_input.get("throttle", 0.0))
    rpm = clampf(0.16 + within * 0.78 + throttle * 0.06, 0.14, 1.0)

func _move(delta: float, input: Dictionary) -> void:
    var wobble_offset: float = wobble * sin(float(Engine.get_physics_frames()) * 0.41)
    velocity = Vector3(steer * speed * 0.30 + wobble_offset, 0.0, -speed)
    move_and_slide()
    position.y = AGRoadPath.height_at(position.z)
    var original_x := position.x
    position.x = AGRoadPath.clamp_x(position.z, position.x, 0.72)
    if absf(original_x - position.x) > 0.005 and crash_cooldown <= 0.0 and can_drive:
        _apply_crash(2, speed * 0.55, "Hit the concrete barrier")
    rotation.y = -AGRoadPath.yaw_at(position.z) - steer * 0.10

func _animate(delta: float, input: Dictionary) -> void:
    if bike_view != null:
        bike_view.set_motion(speed, steer, float(input.get("throttle", 0.0)),
            float(input.get("brake", 0.0)), delta)
    if rider_view != null:
        rider_view.set_pose(steer, speed, float(input.get("throttle", 0.0)),
            float(input.get("brake", 0.0)), delta)
    if hitbox != null:
        hitbox.set_meta("speed", speed)

func _on_hit_area_entered(area: Area3D) -> void:
    if not is_player or crash_active or crash_cooldown > 0.0 or not can_drive:
        return
    var other_mass := float(area.get_meta("mass", 1.0))
    var other_speed := float(area.get_meta("speed", 0.0))
    var other_type := String(area.get_meta("type", "vehicle"))
    var relative := absf(speed - other_speed)
    var impact := relative * 0.55 + speed * 0.20 + other_mass * 7.0
    var severity := 1
    if impact > 58.0:
        severity = 3
    elif impact > 34.0:
        severity = 2
    _apply_crash(severity, impact, "Collided with " + other_type.replace("_", " "))

func _apply_crash(severity: int, impact: float, reason: String) -> void:
    if crash_active or crash_cooldown > 0.0:
        return
    crash_count += 1
    crash_cooldown = 0.85
    camera_shake = [0.0, 0.16, 0.42, 0.85][clampi(severity, 0, 3)]
    var rng_direction := -1.0 if rng.randf() < 0.5 else 1.0
    if severity == 1:
        speed *= 0.82
        wobble = 2.2 * rng_direction
        AGAudio.play("collision_minor", -8.0)
        crashed.emit(reason, severity)
    elif severity == 2:
        speed *= 0.55
        wobble = 5.0 * rng_direction
        camera_shake = 0.48
        AGAudio.play("collision_minor", -4.0, 0.82)
        crashed.emit(reason, severity)
        if speed > 43.0 and rng.randf() < 0.34:
            trigger_fall(reason + " at high speed")
    else:
        speed *= 0.18
        AGAudio.play("collision_major", -2.0)
        crashed.emit(reason, severity)
        trigger_fall(reason)

func trigger_fall(reason: String) -> void:
    if crash_active:
        return
    crash_active = true
    can_drive = false
    var direction := -1.0 if rng.randf() < 0.5 else 1.0
    if bike_view != null:
        bike_view.play_slide(direction)
    if rider_view != null and get_parent() != null:
        var old_transform := rider_view.global_transform
        rider_view.reparent(get_parent(), true)
        rider_view.global_transform = old_transform
        rider_view.play_fall(direction)
    crashed.emit(reason, 3)
    await get_tree().create_timer(2.2).timeout
    fall_finished.emit()

func force_severe_crash(reason: String) -> void:
    if crash_active:
        return
    crash_cooldown = 0.0
    _apply_crash(3, 999.0, reason)

func register_near_miss() -> void:
    near_miss_count += 1
    near_miss.emit()

func add_camera_shake(amount: float) -> void:
    camera_shake = maxf(camera_shake, amount)
