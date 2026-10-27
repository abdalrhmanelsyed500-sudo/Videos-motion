extends RefCounted
class_name AGState
## Runtime-safe access to the GameState autoload; works in script-only tests.

static func node() -> Node:
    var loop: MainLoop = Engine.get_main_loop()
    if loop is SceneTree:
        var tree: SceneTree = loop
        return tree.root.get_node_or_null("GameState")
    return null

static func _has_property(target: Node, property_name: String) -> bool:
    for property in target.get_property_list():
        if String(property.get("name", "")) == property_name:
            return true
    return false

static func _read(property_name: String, fallback: Variant) -> Variant:
    var state := node()
    if state != null and _has_property(state, property_name):
        return state.get(property_name)
    return fallback

static func _invoke(method_name: String, args: Array, fallback: Variant = null) -> Variant:
    var state := node()
    if state != null and state.has_method(method_name):
        return state.callv(method_name, args)
    return fallback

static func riders() -> Array:
    var value: Variant = _read("riders", [])
    return value if value is Array else []

static func bikes() -> Array:
    var value: Variant = _read("bikes", [])
    return value if value is Array else []

static func traffic_types() -> Array:
    var value: Variant = _read("traffic_types", [])
    return value if value is Array else []

static func settings() -> Dictionary:
    var value: Variant = _read("settings", {})
    return value if value is Dictionary else {}

static func last_result() -> Dictionary:
    var value: Variant = _read("last_result", {})
    return value if value is Dictionary else {}

static func career_wins() -> int:
    return int(_read("career_wins", 0))

static func career_races() -> int:
    return int(_read("career_races", 0))

static func get_setting(key: String, fallback: Variant = null) -> Variant:
    return settings().get(key, fallback)

static func set_setting(key: String, value: Variant) -> void:
    _invoke("set_setting", [key, value])

static func selected_rider_index() -> int:
    return int(_read("selected_rider", 0))

static func selected_bike_index() -> int:
    return int(_read("selected_bike", 0))

static func selected_rider() -> Dictionary:
    var value: Variant = _invoke("get_rider", [], {})
    return value if value is Dictionary else {}

static func selected_bike() -> Dictionary:
    var value: Variant = _invoke("get_bike", [], {})
    return value if value is Dictionary else {}

static func rider(index: int) -> Dictionary:
    var value: Variant = _invoke("get_rider", [index], {})
    return value if value is Dictionary else {}

static func bike(index: int) -> Dictionary:
    var value: Variant = _invoke("get_bike", [index], {})
    return value if value is Dictionary else {}

static func set_selected_rider(index: int) -> void:
    _invoke("set_selected_rider", [index])

static func set_selected_bike(index: int) -> void:
    _invoke("set_selected_bike", [index])

static func is_bike_unlocked(bike: Dictionary) -> bool:
    return bool(_invoke("is_bike_unlocked", [bike], true))

static func difficulty_speed_multiplier() -> float:
    return float(_invoke("difficulty_speed_multiplier", [], 1.0))

static func traffic_density() -> float:
    return float(_invoke("traffic_density", [], 1.0))

static func difficulty_name() -> String:
    return String(_invoke("difficulty_name", [], "STREET RACE"))

static func record_result(result: Dictionary) -> void:
    _invoke("record_result", [result])

static func save_game() -> void:
    _invoke("save_game", [])
