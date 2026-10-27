extends Node
class_name AGPoliceSystem
## Extensible Egyptian police pursuit, escalation and scripted interception.

signal pursuit_started(level: int, message: String)
signal pursuit_changed(level: int)
signal pursuit_ended()

var level := 0
var player: AGMotorcycleController
var traffic_system: AGTrafficSystem
var race_manager: AGRaceManager
var fast_riding_time := 0.0
var calm_time := 0.0
var interception_flags := [false, false]
var last_near_miss_count := 0
var last_crash_count := 0
var rng := RandomNumberGenerator.new()

func setup(player_ref: AGMotorcycleController, traffic: AGTrafficSystem, manager: AGRaceManager) -> void:
    player = player_ref
    traffic_system = traffic
    race_manager = manager
    rng.seed = 77123
    fast_riding_time = 0.0
    calm_time = 0.0
    level = 0
    interception_flags = [false, false]
    last_near_miss_count = player.near_miss_count
    last_crash_count = player.crash_count

func _process(delta: float) -> void:
    if player == null or race_manager == null or race_manager.state != AGRaceManager.State.RACING:
        return
    var illegal_speed := 58.0 + float(race_manager.difficulty) * 3.0
    if player.speed > illegal_speed:
        fast_riding_time += delta
        calm_time = 0.0
    else:
        fast_riding_time = maxf(0.0, fast_riding_time - delta * 0.6)
        calm_time += delta
    if fast_riding_time > 7.0 and level < 1:
        escalate("MOTORCYCLE RADAR: ILLEGAL STREET RACE DETECTED")
    if player.near_miss_count > last_near_miss_count + 2 and level < 2:
        last_near_miss_count = player.near_miss_count
        escalate("RECKLESS OVERTAKING REPORTED — PATROL ESCALATED")
    if player.crash_count > last_crash_count and level < 2:
        last_crash_count = player.crash_count
        escalate("COLLISION REPORTED — POLICE INTERCEPTION INBOUND")
    var progress := AGRoadPath.progress(player.position.z)
    if progress > 0.35 and not interception_flags[0]:
        interception_flags[0] = true
        traffic_system.spawn_interception()
        if level < 2:
            escalate("ROADBLOCK AHEAD: RING ROAD PATROL")
        else:
            pursuit_changed.emit(level)
    if progress > 0.70 and not interception_flags[1]:
        interception_flags[1] = true
        traffic_system.spawn_police(2, 390.0)
        escalate("FINAL PATROL INTERCEPTION")
    if level > 0 and calm_time > 18.0 and player.speed < illegal_speed * 0.75:
        deescalate()

func escalate(message: String) -> void:
    level = clampi(level + 1, 0, 3)
    calm_time = 0.0
    if level <= 1:
        traffic_system.spawn_police(1, 430.0)
    else:
        traffic_system.spawn_police(1, 360.0)
    AGAudio.play("police_alert", -5.0)
    AGAudio.set_siren(true, float(level) / 3.0)
    pursuit_started.emit(level, message)
    pursuit_changed.emit(level)

func deescalate() -> void:
    level = maxi(0, level - 1)
    calm_time = 0.0
    if level == 0:
        AGAudio.set_siren(false)
        traffic_system.clear_police()
        pursuit_ended.emit()
    else:
        AGAudio.set_siren(true, float(level) / 3.0)
        pursuit_changed.emit(level)

func force_alert(message := "TEST PURSUIT") -> void:
    if level == 0:
        escalate(message)
    else:
        pursuit_changed.emit(level)

func get_state() -> Dictionary:
    return {"level": level, "fast_time": fast_riding_time,
        "interceptions": interception_flags, "police_spawned": traffic_system.police_spawned if traffic_system != null else 0}
