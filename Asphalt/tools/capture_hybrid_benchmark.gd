extends SceneTree
## Capture the Hybrid 2.5D benchmark states at 1280x720.

var benchmark: Control

func _initialize() -> void:
    call_deferred("run")

func run() -> void:
    var packed: PackedScene = load("res://scenes/experiments/hybrid_2p5d_benchmark.tscn")
    if packed == null:
        printerr("Could not load hybrid benchmark scene")
        quit(1)
        return
    benchmark = packed.instantiate()
    root.add_child(benchmark)
    for i in range(12):
        await process_frame
    var modes := ["static", "moving", "crash", "hospital", "finish", "debug"]
    var ok := true
    for mode in modes:
        benchmark.call("set_benchmark_state", mode)
        for i in range(7):
            await process_frame
        var file_name: String = "hybrid_benchmark_" + String(mode) + ".png"
        ok = await capture_frame(file_name) and ok
    var report := {
        "engine": str(Engine.get_version_info().get("string", "unknown")),
        "rendering": "2D CanvasItem / scanline pseudo-3D",
        "viewport": [root.size.x, root.size.y],
        "modes": modes,
        "all_captures_ok": ok,
    }
    var file := FileAccess.open("res://screenshots/hybrid_capture_report.json", FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify(report, "\t"))
        file.close()
    quit(0 if ok else 1)

func capture_frame(file_name: String) -> bool:
    if RenderingServer.has_method("force_frame_draw"):
        RenderingServer.call("force_frame_draw")
    await process_frame
    var image := root.get_texture().get_image()
    var path := ProjectSettings.globalize_path("res://screenshots/" + file_name)
    var error := image.save_png(path)
    print("HYBRID_CAPTURE=", error == OK, " FILE=", file_name)
    return error == OK
