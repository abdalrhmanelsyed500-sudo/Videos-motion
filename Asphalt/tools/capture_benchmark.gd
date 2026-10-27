extends SceneTree
## Renders and saves actual in-engine gameplay-camera frames.
## Run with Xvfb + Mesa llvmpipe:
## godot --path . --display-driver x11 --rendering-driver opengl3 \
##   --audio-driver Dummy --script res://tools/capture_benchmark.gd

var race_world: Node
var screenshot_dir := ""

func _initialize() -> void:
    call_deferred("run")

func run() -> void:
    screenshot_dir = ProjectSettings.globalize_path("res://screenshots")
    DirAccess.make_dir_recursive_absolute(screenshot_dir)
    var packed: PackedScene = load("res://scenes/race_world.tscn")
    if packed == null:
        printerr("Could not load race_world.tscn")
        quit(1)
        return
    race_world = packed.instantiate()
    race_world.configure(false, true)
    root.add_child(race_world)
    for i in range(14):
        await process_frame

    # Urban cockpit frame, matching the composition of reference_01.
    race_world.call("prepare_benchmark", -520.0)
    for i in range(8):
        await process_frame
    var cockpit_ok := await capture_frame(screenshot_dir + "/benchmark_cockpit.png")
    print("Captured cockpit: ", cockpit_ok)

    # Bridge/coastal third-person frame, echoing reference_03's white rails.
    race_world.call("prepare_benchmark", -2800.0)
    var camera: Variant = race_world.get("camera")
    var player: Variant = race_world.get("player")
    var hud: Variant = race_world.get("hud")
    if camera != null and player != null:
        camera.call("set_mode", 1)  # AGCameraRig.Mode.CHASE
        camera.global_position = player.to_global(Vector3(0.0, 2.6, 6.6))
    if hud != null:
        hud.call("set_cockpit_mode", false)
    for i in range(22):
        await process_frame
    var chase_ok := await capture_frame(screenshot_dir + "/benchmark_chase.png")
    print("Captured chase: ", chase_ok)

    # Short crash-replay orbit around the bike/rider.
    if camera != null and player != null:
        camera.call("start_replay", player.global_position + Vector3(0.0, 0.0, -2.0))
    for i in range(14):
        await process_frame
    var replay_ok := await capture_frame(screenshot_dir + "/benchmark_replay.png")
    print("Captured replay: ", replay_ok)

    var metadata := {
        "engine": str(Engine.get_version_info().get("string", "unknown")),
        "rendering_method": ProjectSettings.get_setting("rendering/renderer/rendering_method", "unknown"),
        "viewport": [root.size.x, root.size.y],
        "captures": {
            "cockpit": cockpit_ok, "chase": chase_ok, "replay": replay_ok,
        },
    }
    var report := FileAccess.open("res://screenshots/capture_report.json", FileAccess.WRITE)
    if report != null:
        report.store_string(JSON.stringify(metadata, "\t"))
        report.close()
    quit(0 if cockpit_ok and chase_ok and replay_ok else 1)

func capture_frame(path: String) -> bool:
    for i in range(5):
        await process_frame
    if RenderingServer.has_method("force_frame_draw"):
        RenderingServer.call("force_frame_draw")
    await process_frame
    var viewport_texture := root.get_texture()
    if viewport_texture == null:
        printerr("Root viewport texture is null")
        return false
    var image := viewport_texture.get_image()
    if image == null or image.is_empty():
        printerr("Captured image is empty: " + path)
        return false
    var error := image.save_png(path)
    if error != OK:
        printerr("Could not save " + path + " (error " + str(error) + ")")
        return false
    print("Saved ", path, " ", image.get_width(), "x", image.get_height())
    return true
