extends SceneTree
## Capture a crash/fallen-rider composition from the existing 3D project.

var race_world: Node

func _initialize() -> void:
    call_deferred("run")

func run() -> void:
    var packed: PackedScene = load("res://scenes/race_world.tscn")
    race_world = packed.instantiate()
    race_world.configure(false, true)
    root.add_child(race_world)
    for i in range(14):
        await process_frame
    race_world.call("prepare_benchmark", -520.0)
    var player: Variant = race_world.get("player")
    var hud: Variant = race_world.get("hud")
    var camera: Variant = race_world.get("camera")
    var manager: Variant = race_world.get("race_manager")
    if player != null:
        player.crash_active = true
        player.can_drive = false
        if player.bike_view != null:
            player.bike_view.play_slide(1.0)
        if player.rider_view != null:
            var rider: Node3D = player.rider_view
            var old_transform := rider.global_transform
            rider.reparent(race_world, true)
            rider.global_transform = old_transform
            rider.play_fall(1.0)
    if manager != null and manager.has_method("end_by_crash"):
        manager.call("end_by_crash", "Benchmark fall")
    if camera != null:
        camera.call("start_replay", player.global_position + Vector3(0.0, 0.0, -1.0))
        camera.set_physics_process(false)
        camera.current = true
        camera.fov = 64.0
        camera.global_position = player.global_position + Vector3(5.6, 3.4, 4.2)
        camera.look_at(player.global_position + Vector3(0.0, 0.85, 0.0), Vector3.UP)
    if hud != null:
        hud.call("set_cockpit_mode", true)
        hud.call("show_warning", "BENCHMARK FALL")
    for i in range(30):
        await process_frame
    if RenderingServer.has_method("force_frame_draw"):
        RenderingServer.call("force_frame_draw")
    await process_frame
    var image := root.get_texture().get_image()
    var path := ProjectSettings.globalize_path("res://screenshots/benchmark_3d_crash.png")
    var error := image.save_png(path)
    print("THREED_CRASH_CAPTURE=", error == OK, " PATH=", path)
    quit(0 if error == OK else 1)
