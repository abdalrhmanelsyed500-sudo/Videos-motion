extends Node
class_name AGRaceManager
## Countdown, timing, position, finish and crash resolution.

enum State { COUNTDOWN, RACING, CRASHED, FINISHED }

signal countdown_changed(text: String)
signal race_started()
signal race_finished(result: Dictionary)
signal crash_occurred(reason: String)
signal position_changed(position_value: int, total: int)
signal time_changed(seconds: float)

var state := State.COUNTDOWN
var countdown_time := 3.6
var race_time := 0.0
var race_length := AGRoadPath.RACE_LENGTH
var player: AGMotorcycleController
var rivals: Array = []
var traffic_system: AGTrafficSystem
var police_system: AGPoliceSystem
var difficulty := 1
var position_value := 1
var total_racers := 6
var top_speed := 0.0
var crash_reason := ""
var test_mode := false
var _position_timer := 0.0
var _last_countdown_text := ""

func setup(player_ref: AGMotorcycleController, rival_refs: Array, traffic: AGTrafficSystem,
        police: AGPoliceSystem, difficulty_value: int, test := false) -> void:
    player = player_ref
    rivals = rival_refs.duplicate()
    traffic_system = traffic
    police_system = police
    difficulty = clampi(difficulty_value, 0, 2)
    test_mode = test
    total_racers = 1 + rivals.size()
    countdown_time = 0.05 if test_mode else 3.6
    state = State.COUNTDOWN
    race_time = 0.0
    top_speed = 0.0
    player.can_drive = false
    for rival in rivals:
        if is_instance_valid(rival):
            rival.can_drive = false

func _process(delta: float) -> void:
    if state == State.COUNTDOWN:
        countdown_time -= delta
        var text := "GO!"
        if countdown_time > 0.0:
            text = str(maxi(1, int(ceil(countdown_time))))
        if text != _last_countdown_text:
            _last_countdown_text = text
            countdown_changed.emit(text)
            if text != "GO!":
                AGAudio.play("countdown_beep", -8.0)
            else:
                AGAudio.play("race_go", -5.0)
        if countdown_time <= -0.35:
            state = State.RACING
            player.can_drive = not player.crash_active
            for rival in rivals:
                if is_instance_valid(rival):
                    rival.can_drive = true
            race_started.emit()
            countdown_changed.emit("")
    elif state == State.RACING:
        race_time += delta
        top_speed = maxf(top_speed, player.speed)
        time_changed.emit(race_time)
        _position_timer -= delta
        if _position_timer <= 0.0:
            _position_timer = 0.20
            var new_position := _calculate_position()
            if new_position != position_value:
                position_value = new_position
                position_changed.emit(position_value, total_racers)
        if AGRoadPath.progress(player.position.z) >= 1.0:
            finish_race(false, "")

func _calculate_position() -> int:
    if player == null:
        return 1
    var value := 1
    var player_z := player.position.z
    for rival in rivals:
        if is_instance_valid(rival) and rival.position.z < player_z:
            value += 1
    return clampi(value, 1, total_racers)

func finish_race(crashed: bool, reason: String) -> void:
    if state == State.FINISHED:
        return
    state = State.FINISHED
    player.can_drive = false
    for rival in rivals:
        if is_instance_valid(rival):
            rival.can_drive = false
    var result := build_result(crashed, reason)
    race_finished.emit(result)

func build_result(crashed: bool, reason: String) -> Dictionary:
    var progress := AGRoadPath.progress(player.position.z)
    var final_position := total_racers if crashed else _calculate_position()
    var police_level := 0
    if police_system != null:
        police_level = police_system.level
    return {
        "title": "RACE COMPLETE" if not crashed else "WIPEOUT",
        "finished": not crashed,
        "crashed": crashed,
        "reason": reason,
        "position": final_position,
        "total_racers": total_racers,
        "time": race_time,
        "progress": progress,
        "distance": progress * race_length,
        "top_speed_kmh": maxf(top_speed, player.top_speed) * 3.6,
        "crashes": player.crash_count,
        "near_misses": player.near_miss_count,
        "police_level": police_level,
        "rider": String(player.rider_data.get("name", "Rider")),
        "bike": String(player.bike_data.get("name", "Bike")),
        "difficulty": difficulty,
        "victory": final_position == 1 and not crashed,
    }

func end_by_crash(reason: String) -> void:
    if state == State.FINISHED or state == State.CRASHED:
        return
    state = State.CRASHED
    crash_reason = reason
    player.can_drive = false
    for rival in rivals:
        if is_instance_valid(rival):
            rival.can_drive = false
    crash_occurred.emit(reason)

func finalize_crash_result() -> void:
    finish_race(true, crash_reason if crash_reason != "" else "Severe crash")

func get_state() -> Dictionary:
    return {
        "state": state,
        "countdown": countdown_time,
        "time": race_time,
        "position": position_value,
        "total": total_racers,
        "progress": AGRoadPath.progress(player.position.z) if player != null else 0.0,
        "difficulty": difficulty,
    }
