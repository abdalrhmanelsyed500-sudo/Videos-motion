extends Node3D
## Assembles and owns one complete race: world, bikes, rivals, traffic, police,
## HUD, camera, countdown and results.

signal race_finished(result: Dictionary)
signal hospital_requested(result: Dictionary)

var auto_build := true
var test_mode := false
var benchmark_mode := false
var road: Node3D
var environment: Node3D
var player: AGMotorcycleController
var rivals: Array = []
var traffic_system: AGTrafficSystem
var police_system: AGPoliceSystem
var race_manager: AGRaceManager
var hud: AGHUD
var camera: AGCameraRig
var selected_rider_index := 0
var selected_bike_index := 0

func configure(test := false, benchmark := false) -> void:
    test_mode = test
    benchmark_mode = benchmark

func _ready() -> void:
    if auto_build:
        _build_world()

func _load_json_array(path: String, key: String) -> Array:
    if not FileAccess.file_exists(path):
        return []
    var file := FileAccess.open(path, FileAccess.READ)
    if file == null:
        return []
    var parsed: Variant = JSON.parse_string(file.get_as_text())
    file.close()
    if parsed is Dictionary and parsed.has(key) and parsed[key] is Array:
        return parsed[key]
    return []

func _riders() -> Array:
    var loaded := AGState.riders()
    if loaded.is_empty():
        loaded = _load_json_array("res://assets/data/riders.json", "riders")
    return loaded

func _bikes() -> Array:
    var loaded := AGState.bikes()
    if loaded.is_empty():
        loaded = _load_json_array("res://assets/data/bikes.json", "bikes")
    return loaded

func _traffic_types() -> Array:
    var loaded := AGState.traffic_types()
    if loaded.is_empty():
        loaded = _load_json_array("res://assets/data/traffic.json", "types")
    return loaded

func _data_at(data: Array, index: int) -> Dictionary:
    if data.is_empty():
        return {}
    return data[clampi(index, 0, data.size() - 1)]

func _build_world() -> void:
    var riders := _riders()
    var bikes := _bikes()
    var traffic_types := _traffic_types()
    selected_rider_index = clampi(AGState.selected_rider_index(), 0, maxi(0, riders.size() - 1))
    selected_bike_index = clampi(AGState.selected_bike_index(), 0, maxi(0, bikes.size() - 1))
    var difficulty := clampi(int(AGState.get_setting("difficulty", 1)), 0, 2)
    var quality := String(AGState.get_setting("quality", "medium"))
    var density := clampf(float(AGState.get_setting("traffic_density", 1.0)), 0.35, 1.8)
    if test_mode and not benchmark_mode:
        density = 0.45
    if benchmark_mode:
        density = 1.15
    var default_camera := String(AGState.get_setting("default_camera", "cockpit"))

    road = AGRoadBuilder.build()
    add_child(road)
    environment = AGEnvironmentBuilder.build(quality)
    add_child(environment)

    player = AGMotorcycleController.new()
    player.name = "PlayerMotorcycle"
    player.setup(_data_at(riders, selected_rider_index), _data_at(bikes, selected_bike_index), true, difficulty)
    var start_z := 0.0
    player.position = Vector3(AGRoadPath.lane_x(start_z, 1), AGRoadPath.height_at(start_z), start_z)
    player.rotation.y = -AGRoadPath.yaw_at(start_z)
    add_child(player)

    var rival_rider_indices := [1, 2, 3, 5, 7]
    var rival_bike_indices := [1, 2, 3, 4, 5]
    var rival_lanes := [0, 2, 3, 1, 2]
    for i in range(mini(rival_rider_indices.size(), maxi(1, riders.size() - 1))):
        var rival := AGMotorcycleController.new()
        rival.name = "RivalMotorcycle_%d" % i
        var rider_index: int = rival_rider_indices[i] % maxi(1, riders.size())
        var bike_index: int = rival_bike_indices[i] % maxi(1, bikes.size())
        rival.setup(_data_at(riders, rider_index), _data_at(bikes, bike_index), false, difficulty)
        rival.brain = AGRivalBrain.new()
        rival.brain.setup(_data_at(riders, rider_index), difficulty, i)
        var rz := -10.0 - float(i) * 8.0
        var lane: int = rival_lanes[i] % AGRoadPath.LANE_COUNT
        rival.position = Vector3(AGRoadPath.lane_x(rz, lane), AGRoadPath.height_at(rz), rz)
        rival.rotation.y = -AGRoadPath.yaw_at(rz)
        add_child(rival)
        rivals.append(rival)

    traffic_system = AGTrafficSystem.new()
    traffic_system.name = "TrafficSystem"
    add_child(traffic_system)
    traffic_system.setup(traffic_types, player, density, difficulty)
    for rival in rivals:
        rival.set_meta("traffic_system", traffic_system)
        rival.set_meta("rivals", rivals)

    race_manager = AGRaceManager.new()
    race_manager.name = "RaceManager"
    add_child(race_manager)
    police_system = AGPoliceSystem.new()
    police_system.name = "PoliceSystem"
    add_child(police_system)
    race_manager.setup(player, rivals, traffic_system, police_system, difficulty, test_mode or benchmark_mode)
    police_system.setup(player, traffic_system, race_manager)

    var hud_scene: PackedScene = load("res://scenes/ui/hud.tscn")
    hud = hud_scene.instantiate() as AGHUD
    hud.name = "RaceHUD"
    add_child(hud)

    camera = AGCameraRig.new()
    camera.name = "GameplayCamera"
    add_child(camera)
    camera.setup(player, hud, race_manager, default_camera)
    hud.setup(player, race_manager, police_system, camera)

    race_manager.countdown_changed.connect(Callable(hud, "set_countdown"))
    police_system.pursuit_started.connect(Callable(hud, "set_police_alert"))
    race_manager.race_finished.connect(Callable(self, "_on_race_finished"))
    player.crashed.connect(Callable(self, "_on_player_crashed"))
    player.fall_finished.connect(Callable(self, "_on_fall_finished"))
    AGAudio.start_race_audio()
    AGSettings.apply()
    if benchmark_mode:
        call_deferred("prepare_benchmark")

func _on_player_crashed(reason: String, severity: int) -> void:
    if hud == null:
        return
    if severity < 3:
        hud.show_warning("IMPACT: " + reason)
        return
    race_manager.end_by_crash(reason)
    hud.show_crash_overlay(reason)
    if camera != null:
        camera.start_replay(player.global_position)

func _on_fall_finished() -> void:
    if hud != null:
        hud.show_defeat_transition()
    await get_tree().create_timer(0.75).timeout
    if is_inside_tree() and race_manager != null:
        race_manager.finalize_crash_result()

func _on_race_finished(result: Dictionary) -> void:
    AGAudio.stop_race_audio()
    if bool(result.get("crashed", false)):
        hospital_requested.emit(result)
    else:
        race_finished.emit(result)

func prepare_benchmark(benchmark_z := -520.0) -> void:
    # Freeze gameplay systems and compose a representative cockpit frame.
    player.set_physics_process(false)
    for rival in rivals:
        rival.set_physics_process(false)
    traffic_system.set_process(false)
    police_system.set_process(false)
    race_manager.set_process(false)
    race_manager.state = AGRaceManager.State.RACING
    race_manager.race_time = 42.7
    race_manager.position_value = 2
    race_manager.top_speed = 62.0
    player.can_drive = true
    player.crash_active = false
    player.speed = 52.0
    player.gear = 3
    player.rpm = 0.62
    player.boost_energy = 0.72
    player.top_speed = 62.0
    player.last_input = {"throttle": 1.0, "brake": 0.0, "steer": 0.08, "handbrake": 0.0, "boost": 0.0}
    var z := benchmark_z
    player.position = Vector3(AGRoadPath.lane_x(z, 1), AGRoadPath.height_at(z), z)
    player.rotation.y = -AGRoadPath.yaw_at(z)
    var rival_lanes := [0, 2, 3, 1, 2]
    for i in range(rivals.size()):
        var rival: AGMotorcycleController = rivals[i]
        var rz := z - 28.0 - float(i) * 18.0
        var lane: int = rival_lanes[i % rival_lanes.size()]
        rival.position = Vector3(AGRoadPath.lane_x(rz, lane), AGRoadPath.height_at(rz), rz)
        rival.rotation.y = -AGRoadPath.yaw_at(rz)
        rival.speed = 48.0 + float(i) * 2.0
        rival.gear = 3
        rival.rpm = 0.58
        if rival.bike_view != null:
            rival.bike_view.set_motion(rival.speed, 0.04, 1.0, 0.0, 0.016)
        if rival.rider_view != null:
            rival.rider_view.set_pose(0.04, rival.speed, 1.0, 0.0, 0.016)
    var traffic_index := 0
    for vehicle in traffic_system.vehicles:
        if not is_instance_valid(vehicle):
            continue
        # Place every traffic vehicle in front of the benchmark camera. Leaving
        # any at their old spawn z made large vehicle windows overlap the view.
        var tz := z - 90.0 - float(traffic_index) * 42.0
        var lane2 := traffic_index % AGRoadPath.LANE_COUNT
        vehicle.lane = lane2
        vehicle.position = Vector3(AGRoadPath.lane_x(tz, lane2), AGRoadPath.height_at(tz), tz)
        vehicle.rotation.y = -AGRoadPath.yaw_at(tz)
        vehicle.set_meta("speed", vehicle.speed)
        vehicle.view.set_motion(vehicle.speed, 0.016)
        traffic_index += 1
    var benchmark_progress := AGRoadPath.progress(z)
    hud.set_benchmark_state(187.0, 0.62, 3, 2, 42.7, benchmark_progress, 0.72,
        2 if benchmark_progress > 0.5 else 1)
    camera.set_mode(AGCameraRig.Mode.COCKPIT)
    camera.global_position = player.to_global(Vector3(0.0, 1.30, -0.18))
    camera.global_rotation = player.global_rotation + Vector3(-0.035, 0.0, 0.0)

func get_debug_state() -> Dictionary:
    var road_normal := Vector3.ZERO
    if road != null and road.has_meta("road_surface_normal"):
        road_normal = road.get_meta("road_surface_normal")
    return {
        "road_normal": road_normal,
        "rider_count": _riders().size(),
        "bike_count": _bikes().size(),
        "rival_count": rivals.size(),
        "traffic_count": traffic_system.vehicles.size() if traffic_system != null else 0,
        "player_speed": player.speed if player != null else 0.0,
        "race_state": race_manager.state if race_manager != null else -1,
        "camera_mode": camera.mode if camera != null else -1,
    }
