extends RefCounted
class_name AGAudio
## Runtime-safe access to the AudioDirector autoload; works in script-only tests.

static func node() -> Node:
    var loop: MainLoop = Engine.get_main_loop()
    if loop is SceneTree:
        var tree: SceneTree = loop
        return tree.root.get_node_or_null("AudioDirector")
    return null

static func _invoke(method_name: String, args: Array) -> void:
    var director := node()
    if director != null and director.has_method(method_name):
        director.callv(method_name, args)

static func play(sound_name: String, volume_db := 0.0, pitch := 1.0) -> void:
    _invoke("play", [sound_name, volume_db, pitch])

static func play_ui_click() -> void:
    _invoke("play_ui_click", [])

static func start_race_audio() -> void:
    _invoke("start_race_audio", [])

static func stop_race_audio() -> void:
    _invoke("stop_race_audio", [])

static func set_engine_state(speed: float, rpm: float, throttle: float) -> void:
    _invoke("set_engine_state", [speed, rpm, throttle])

static func set_siren(active: bool, intensity := 1.0) -> void:
    _invoke("set_siren", [active, intensity])
