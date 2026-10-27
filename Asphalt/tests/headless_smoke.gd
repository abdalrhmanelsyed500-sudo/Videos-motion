extends SceneTree
## Headless gameplay smoke test. Drives a real RaceWorld through physics frames.

var checks: Array = []
var finish_result: Dictionary = {}

func _initialize() -> void:
    call_deferred("run_tests")

func check(check_name: String, condition: bool, detail: String = "") -> void:
    checks.append({"name": check_name, "passed": bool(condition), "detail": detail})

func _capture_result(result: Dictionary) -> void:
    finish_result = result.duplicate(true)

func run_tests() -> void:
    var packed: PackedScene = load("res://scenes/race_world.tscn")
    if packed == null:
        check("race_scene_load", false, "Could not load race_world.tscn")
        _write_report()
        quit(1)
        return
    var race_world = packed.instantiate()
    race_world.configure(true, false)
    root.add_child(race_world)
    for i in range(12):
        await process_frame
    check("race_world_build", race_world.player != null and race_world.road != null and race_world.hud != null,
        "player, road and HUD are present")
    var debug: Dictionary = race_world.get_debug_state()
    var normal: Vector3 = debug.get("road_normal", Vector3.ZERO)
    check("road_surface_normals", normal.y > 0.95, "first triangle normal=" + str(normal))
    check("roster_sizes", int(debug.get("rider_count", 0)) == 8 and int(debug.get("bike_count", 0)) == 6,
        "riders=" + str(debug.get("rider_count", 0)) + " bikes=" + str(debug.get("bike_count", 0)))
    check("rival_count", int(debug.get("rival_count", 0)) == 5, "rivals=" + str(debug.get("rival_count", 0)))
    check("traffic_spawned", int(debug.get("traffic_count", 0)) > 0, "traffic=" + str(debug.get("traffic_count", 0)))
    var min_start_distance := 1e9
    for vehicle in race_world.traffic_system.vehicles:
        if is_instance_valid(vehicle):
            min_start_distance = minf(min_start_distance, absf(vehicle.position.z - race_world.player.position.z))
    check("traffic_safe_spawn", min_start_distance > 75.0,
        "closest initial traffic=" + str(snappedf(min_start_distance, 0.1)) + "m")

    # Wait for the shortened test countdown, then accelerate with injected input.
    for i in range(36):
        await physics_frame
    check("countdown_releases_player", race_world.race_manager.state == AGRaceManager.State.RACING,
        "race state=" + str(race_world.race_manager.state))
    race_world.player.set_test_input({"throttle": 1.0, "brake": 0.0, "steer": 0.08, "handbrake": 0.0, "boost": 0.0})
    var start_z: float = float(race_world.player.position.z)
    for i in range(120):
        await physics_frame
    var state: Dictionary = race_world.player.get_state()
    check("player_accelerates", float(state.get("speed", 0.0)) > 8.0, "speed=" + str(snappedf(float(state.get("speed", 0.0)), 0.1)))
    check("player_moves_forward", race_world.player.position.z < start_z - 5.0,
        "start_z=" + str(snappedf(start_z, 0.1)) + " z=" + str(snappedf(race_world.player.position.z, 0.1)))
    check("wheel_pivot_rotates", float(state.get("wheel_angle", 0.0)) > 0.1,
        "wheel_angle=" + str(snappedf(float(state.get("wheel_angle", 0.0)), 0.1)))
    check("gearbox_advances", int(state.get("gear", 1)) >= 2, "gear=" + str(state.get("gear", 1)))
    check("road_progress_advances", float(state.get("progress", 0.0)) > 0.0,
        "progress=" + str(snappedf(float(state.get("progress", 0.0)), 0.001)))
    check("bike_and_rider_parts", race_world.player.bike_view != null and race_world.player.rider_view != null
        and race_world.player.bike_view.front_wheel != null and race_world.player.bike_view.rear_wheel != null
        and race_world.player.rider_view.head != null and race_world.player.rider_view.left_arm != null,
        "functional bike/rider pivots exist")

    # Procedural factories: all six bikes, eight riders and seven traffic bodies.
    var riders: Array = race_world.call("_riders")
    var bikes: Array = race_world.call("_bikes")
    var traffic_types: Array = race_world.call("_traffic_types")
    var bike_ok := true
    var rider_ok := true
    var vehicle_ok := true
    for bike in bikes:
        var bike_view := AGBikeFactory.build(bike)
        if bike_view.front_wheel == null or bike_view.rear_wheel == null or bike_view.steering == null \
                or bike_view.rider_anchor == null or bike_view.body.get_child_count() < 12:
            bike_ok = false
        bike_view.free()
    for rider in riders:
        var rider_view := AGRiderFactory.build(rider)
        if rider_view.torso == null or rider_view.head == null or rider_view.left_arm == null \
                or rider_view.right_leg == null or rider_view.head.get_child_count() < 8:
            rider_ok = false
        rider_view.free()
    for type_def in traffic_types:
        var vehicle_view := AGVehicleFactory.build(type_def)
        if vehicle_view.wheels.size() < 4 or vehicle_view.get_child_count() < 6:
            vehicle_ok = false
        vehicle_view.free()
    check("all_bike_models", bike_ok, "six distinct bike assemblies")
    check("all_rider_models", rider_ok, "eight articulated riders")
    check("all_traffic_models", vehicle_ok, "seven vehicle body styles")

    # Police pursuit spawns far ahead and does not teleport into the player.
    race_world.police_system.force_alert("Automated pursuit test")
    var police_state: Dictionary = race_world.police_system.get_state()
    var min_police_distance := 1e9
    for vehicle in race_world.traffic_system.vehicles:
        if is_instance_valid(vehicle) and vehicle.is_police:
            min_police_distance = minf(min_police_distance, absf(vehicle.position.z - race_world.player.position.z))
    check("police_escalation", int(police_state.get("level", 0)) > 0 and int(police_state.get("police_spawned", 0)) > 0,
        "level=" + str(police_state.get("level", 0)) + " spawned=" + str(police_state.get("police_spawned", 0)))
    check("police_no_teleport", min_police_distance > 200.0,
        "closest police=" + str(snappedf(min_police_distance, 0.1)) + "m")

    # Severe crash: one-shot fall, race stop, defeat result.
    race_world.race_manager.race_finished.connect(Callable(self, "_capture_result"))
    race_world.player.force_severe_crash("Automated severe impact")
    await process_frame
    check("severe_crash_one_shot", race_world.player.crash_active and race_world.player.crash_count >= 1,
        "crash_active=" + str(race_world.player.crash_active))
    check("race_stops_on_crash", race_world.race_manager.state == AGRaceManager.State.CRASHED,
        "state=" + str(race_world.race_manager.state))
    await create_timer(3.5).timeout
    check("fall_finishes_and_result", race_world.race_manager.state == AGRaceManager.State.FINISHED
        and bool(finish_result.get("crashed", false)),
        "state=" + str(race_world.race_manager.state) + " result_crashed=" + str(finish_result.get("crashed", false)))

    # UI scenes instantiate without script errors.
    var ui_paths := [
        "res://scenes/ui/main_menu.tscn", "res://scenes/ui/rider_select.tscn",
        "res://scenes/ui/bike_select.tscn", "res://scenes/ui/settings_menu.tscn",
        "res://scenes/ui/pause_menu.tscn", "res://scenes/ui/hud.tscn",
        "res://scenes/ui/results_screen.tscn", "res://scenes/ui/hospital_screen.tscn",
    ]
    var ui_ok := true
    for path in ui_paths:
        var ui_packed: PackedScene = load(path)
        if ui_packed == null:
            ui_ok = false
            continue
        var instance := ui_packed.instantiate()
        root.add_child(instance)
        await process_frame
        instance.queue_free()
    check("all_ui_scenes", ui_ok, "menu, selections, settings, pause, HUD, results, hospital")

    race_world.queue_free()
    await process_frame

    # Full loop through Main: start race, finish, hospital, retry and menu.
    var main_packed: PackedScene = load("res://scenes/main.tscn")
    var main_node := main_packed.instantiate()
    root.add_child(main_node)
    await process_frame
    main_node.call("_on_start_race")
    for i in range(8):
        await process_frame
    check("main_starts_race", main_node.get("race_world") != null, "race world instantiated by Main")
    var sample_result := {
        "position": 1, "total_racers": 6, "time": 61.5, "progress": 1.0,
        "distance": AGRoadPath.RACE_LENGTH, "top_speed_kmh": 231.0,
        "crashes": 0, "near_misses": 3, "police_level": 1,
        "rider": "Test Rider", "bike": "Test Bike", "victory": true,
        "finished": true, "crashed": false, "reason": "", "difficulty": 1,
    }
    main_node.call("_on_race_finished", sample_result)
    await process_frame
    var screen_layer: Variant = main_node.get("screen_layer")
    check("results_screen_from_loop", screen_layer is CanvasLayer and screen_layer.get_child_count() > 0,
        "results screen displayed")
    var crash_result := sample_result.duplicate(true)
    crash_result["crashed"] = true
    crash_result["victory"] = false
    crash_result["reason"] = "Automated severe impact"
    main_node.call("_on_hospital_requested", crash_result)
    await process_frame
    check("hospital_screen_from_loop", screen_layer is CanvasLayer and screen_layer.get_child_count() > 0,
        "hospital screen displayed")
    main_node.call("_on_start_race")
    for i in range(6):
        await process_frame
    check("retry_after_defeat", main_node.get("race_world") != null, "retry recreates race world")
    main_node.call("_show_main_menu")
    await process_frame
    check("return_to_menu", main_node.get("race_world") == null, "world removed on menu return")
    main_node.queue_free()
    _write_report()
    var failures := 0
    for item in checks:
        if not bool(item.get("passed", false)):
            failures += 1
    quit(0 if failures == 0 else 1)

func _write_report() -> void:
    var failures := 0
    for item in checks:
        if not bool(item.get("passed", false)):
            failures += 1
    var report := {
        "engine": str(Engine.get_version_info().get("string", "unknown")),
        "timestamp": Time.get_datetime_string_from_system(),
        "passed": failures == 0,
        "total_checks": checks.size(),
        "failed_checks": failures,
        "checks": checks,
        "notes": "Headless logic tests use the dummy rendering driver; mesh RID warnings from that driver are environmental, not GDScript errors.",
    }
    var dir := ProjectSettings.globalize_path("res://tests/reports")
    DirAccess.make_dir_recursive_absolute(dir)
    var file := FileAccess.open("res://tests/reports/smoke.json", FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify(report, "\t"))
        file.close()
    print("SMOKE_TESTS ", JSON.stringify({"passed": report["passed"], "total": report["total_checks"], "failed": failures}))
