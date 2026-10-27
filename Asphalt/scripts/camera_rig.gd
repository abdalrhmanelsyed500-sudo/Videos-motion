extends Camera3D
class_name AGCameraRig
## Cockpit, chase and short crash-replay cameras.

enum Mode { COCKPIT, CHASE, REPLAY }

var mode := Mode.COCKPIT
var player: AGMotorcycleController
var hud: CanvasLayer
var race_manager: AGRaceManager
var shake := 0.0
var replay_position := Vector3.ZERO
var replay_time := 0.0
var rng := RandomNumberGenerator.new()

func setup(player_ref: AGMotorcycleController, hud_ref: CanvasLayer,
        manager: AGRaceManager, default_mode := "cockpit") -> void:
    player = player_ref
    hud = hud_ref
    race_manager = manager
    rng.seed = 31337
    near = 0.08
    far = 1500.0
    fov = 76.0
    current = true
    mode = Mode.CHASE if default_mode == "chase" else Mode.COCKPIT
    apply_mode()

func _physics_process(delta: float) -> void:
    if player == null or not is_instance_valid(player):
        return
    shake = maxf(0.0, lerpf(shake, player.camera_shake, 1.0 - exp(-8.0 * delta)))
    match mode:
        Mode.COCKPIT:
            _update_cockpit(delta)
        Mode.CHASE:
            _update_chase(delta)
        Mode.REPLAY:
            _update_replay(delta)

func _update_cockpit(delta: float) -> void:
    var target := player.to_global(Vector3(0.0, 1.30, -0.18))
    target += _shake_offset()
    global_position = target
    global_rotation = player.global_rotation + Vector3(-0.035 + player.lean * 0.03, 0.0, 0.0)
    fov = lerpf(fov, 76.0 + clampf(player.speed / maxf(player.max_speed, 1.0), 0.0, 1.0) * 7.0,
        1.0 - exp(-3.0 * delta))

func _update_chase(delta: float) -> void:
    var desired := player.to_global(Vector3(0.0, 2.55, 6.4))
    global_position = global_position.lerp(desired, 1.0 - exp(-7.0 * delta))
    global_position += _shake_offset()
    var look_target := player.to_global(Vector3(0.0, 1.15, -9.0))
    look_at(look_target, Vector3.UP)
    fov = lerpf(fov, 72.0 + clampf(player.speed / maxf(player.max_speed, 1.0), 0.0, 1.0) * 8.0,
        1.0 - exp(-3.0 * delta))

func _update_replay(delta: float) -> void:
    replay_time += delta
    var orbit := Vector3(sin(replay_time * 1.25) * 7.0, 3.1, cos(replay_time * 1.25) * 7.0)
    global_position = replay_position + orbit
    look_at(replay_position + Vector3(0.0, 0.9, 0.0), Vector3.UP)
    fov = lerpf(fov, 62.0, 1.0 - exp(-2.0 * delta))

func _shake_offset() -> Vector3:
    if shake <= 0.001:
        return Vector3.ZERO
    return Vector3(rng.randf_range(-shake, shake) * 0.14,
        rng.randf_range(-shake, shake) * 0.09, 0.0)

func toggle_mode() -> void:
    if mode == Mode.REPLAY:
        return
    mode = Mode.CHASE if mode == Mode.COCKPIT else Mode.COCKPIT
    apply_mode()

func set_mode(new_mode: int) -> void:
    mode = clampi(new_mode, 0, 2)
    apply_mode()

func apply_mode() -> void:
    if player != null:
        player.set_visual_visible(mode != Mode.COCKPIT)
    if hud != null and hud.has_method("set_cockpit_mode"):
        hud.call("set_cockpit_mode", mode == Mode.COCKPIT)

func start_replay(crash_position: Vector3) -> void:
    replay_position = crash_position
    replay_time = 0.0
    mode = Mode.REPLAY
    if player != null:
        player.set_visual_visible(true)
    if hud != null and hud.has_method("set_cockpit_mode"):
        hud.call("set_cockpit_mode", false)
