extends SceneTree
## Headless gameplay test for the isolated Hybrid 2.5D benchmark.

var benchmark: Control
var checks: Array = []

func _initialize() -> void:
    call_deferred("run_tests")

func check(check_name: String, condition: bool, detail: String = "") -> void:
    checks.append({"name": check_name, "passed": bool(condition), "detail": detail})

func run_tests() -> void:
    var packed: PackedScene = load("res://scenes/experiments/hybrid_2p5d_benchmark.tscn")
    if packed == null:
        check("hybrid_scene_load", false, "missing scene")
        _write_report()
        quit(1)
        return
    benchmark = packed.instantiate()
    root.add_child(benchmark)
    for i in range(8):
        await process_frame
    check("hybrid_scene_load", benchmark != null and benchmark.has_method("get_debug_state"), "scene and API present")
    check("hybrid_assets_loaded", benchmark.manifest != {} and benchmark.rider_sheet_tex != null and benchmark.traffic_sheet_tex != null,
        "manifest and atlases loaded")
    var audit_path := "res://experiments/hybrid_2p5d/assets/sprite_audit.json"
    var audit_ok := false
    if FileAccess.file_exists(audit_path):
        var audit_file := FileAccess.open(audit_path, FileAccess.READ)
        var audit_data: Variant = JSON.parse_string(audit_file.get_as_text())
        audit_file.close()
        audit_ok = audit_data is Dictionary and bool(audit_data.get("passed", false))
    check("sprite_frame_audit", audit_ok, "all sprite frames have alpha and consistent dimensions")
    check("initial_world_objects", benchmark.objects.size() >= 10, "objects=" + str(benchmark.objects.size()))
    var projection: Dictionary = benchmark.call("project", 35.0, 0.0)
    check("road_projection", float(projection.get("p", 0.0)) > 0.0 and float(projection.get("p", 0.0)) < 1.0,
        "p=" + str(snappedf(float(projection.get("p", 0.0)), 0.001)))

    var start_state: Dictionary = benchmark.call("get_debug_state")
    var start_distance := float(start_state.get("distance", 0.0))
    benchmark.call("set_test_input", {"throttle": 1.0, "brake": 0.0, "steer": 0.0, "handbrake": 0.0, "boost": 0.0})
    benchmark.crash_cooldown = 999.0
    benchmark.call("advance_simulation", 3.0)
    benchmark.benchmark_mode = true
    await process_frame
    var moving_state: Dictionary = benchmark.call("get_debug_state")
    check("acceleration", float(moving_state.get("speed", 0.0)) > 10.0,
        "speed=" + str(snappedf(float(moving_state.get("speed", 0.0)), 0.1)))
    check("race_progression", float(moving_state.get("distance", 0.0)) > start_distance + 20.0,
        "distance=" + str(snappedf(float(moving_state.get("distance", 0.0)), 0.1)))
    check("gearbox", int(moving_state.get("gear", 1)) >= 2, "gear=" + str(moving_state.get("gear", 1)))
    check("rpm_from_speed", float(moving_state.get("rpm", 0.0)) > 0.2, "rpm=" + str(snappedf(float(moving_state.get("rpm", 0.0)), 0.01)))

    var lateral_before := float(moving_state.get("lateral", 0.0))
    benchmark.call("set_test_input", {"throttle": 1.0, "brake": 0.0, "steer": 1.0, "handbrake": 0.0, "boost": 0.0})
    benchmark.crash_cooldown = 999.0
    benchmark.call("advance_simulation", 1.5)
    benchmark.benchmark_mode = true
    await process_frame
    var steered_state: Dictionary = benchmark.call("get_debug_state")
    check("steering_changes_lane", absf(float(steered_state.get("lateral", 0.0)) - lateral_before) > 0.4,
        "dx=" + str(snappedf(absf(float(steered_state.get("lateral", 0.0)) - lateral_before), 0.1)))

    benchmark.benchmark_mode = false
    benchmark.crash_cooldown = 0.0
    benchmark.call("force_police_alert")
    var police_state: Dictionary = benchmark.call("get_debug_state")
    var min_police_z := 1e9
    for obj in benchmark.objects:
        var item: Dictionary = obj
        if bool(item.get("is_police", false)):
            min_police_z = minf(min_police_z, float(item.get("z", 999.0)))
    check("police_pursuit", int(police_state.get("police_level", 0)) > 0 and min_police_z > 100.0,
        "level=" + str(police_state.get("police_level", 0)) + " min_z=" + str(snappedf(min_police_z, 0.1)))

    benchmark.call("force_severe_crash", "Automated road-relative impact")
    var crashed_state: Dictionary = benchmark.call("get_debug_state")
    check("severe_crash_state", int(crashed_state.get("state", 0)) == 1, "state=" + str(crashed_state.get("state_name", "")))
    await create_timer(2.5).timeout
    var hospital_state: Dictionary = benchmark.call("get_debug_state")
    check("hospital_defeat_sequence", int(hospital_state.get("state", 0)) == 2, "state=" + str(hospital_state.get("state_name", "")))

    benchmark.call("restart_race")
    var retry_state: Dictionary = benchmark.call("get_debug_state")
    check("retry_resets_race", int(retry_state.get("state", 0)) == 0 and float(retry_state.get("distance", 1.0)) < 1.0,
        "state=" + str(retry_state.get("state_name", "")) + " distance=" + str(retry_state.get("distance", 0.0)))

    benchmark.call("force_finish")
    var finish_state: Dictionary = benchmark.call("get_debug_state")
    check("race_termination", int(finish_state.get("state", 0)) == 3, "state=" + str(finish_state.get("state_name", "")))

    for mode in ["static", "moving", "crash", "hospital", "finish", "debug"]:
        benchmark.call("set_benchmark_state", mode)
        await process_frame
        var bench_state: Dictionary = benchmark.call("get_debug_state")
        check("benchmark_mode_" + mode, bool(bench_state.get("benchmark_mode", false)), "mode=" + mode)

    _write_report()
    var failures := 0
    for item in checks:
        if not bool(item.get("passed", false)):
            failures += 1
    print("HYBRID_SMOKE ", JSON.stringify({"passed": failures == 0, "total": checks.size(), "failed": failures}))
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
        "notes": "Road-relative z/lane coordinates drive both projection and collision; no screen-space-only collision logic.",
    }
    var dir := ProjectSettings.globalize_path("res://tests/reports")
    DirAccess.make_dir_recursive_absolute(dir)
    var file := FileAccess.open("res://tests/reports/hybrid_smoke.json", FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify(report, "\t"))
        file.close()
