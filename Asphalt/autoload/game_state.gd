extends Node
## Persistent game state, roster data, settings and race results.

signal settings_changed()
signal selection_changed()
signal result_saved(result: Dictionary)

const SAVE_PATH := "user://asphalt_grooms_save.json"
const DIFFICULTY_NAMES := ["SUNDAY RIDER", "STREET RACE", "RING ROAD INSANE"]
const QUALITY_NAMES := ["LOW", "MEDIUM", "HIGH"]

var riders: Array = []
var bikes: Array = []
var traffic_types: Array = []
var settings: Dictionary = {}
var selected_rider: int = 0
var selected_bike: int = 0
var last_result: Dictionary = {}
var career_wins: int = 0
var career_races: int = 0
var unlocked_bikes: Array = ["cairo_125", "delta_150", "sprint_200", "khan_custom", "shadow_250"]

func _ready() -> void:
    riders = _load_array("res://assets/data/riders.json", "riders")
    bikes = _load_array("res://assets/data/bikes.json", "bikes")
    traffic_types = _load_array("res://assets/data/traffic.json", "types")
    settings = _load_dictionary("res://assets/data/settings_defaults.json")
    _load_save()
    _register_actions()
    apply_audio_volume()

func _load_json(path: String) -> Variant:
    if not FileAccess.file_exists(path):
        push_error("Missing data file: " + path)
        return null
    var file := FileAccess.open(path, FileAccess.READ)
    if file == null:
        push_error("Could not open data file: " + path)
        return null
    var text := file.get_as_text()
    file.close()
    return JSON.parse_string(text)

func _load_array(path: String, key: String) -> Array:
    var parsed: Variant = _load_json(path)
    if parsed is Dictionary and parsed.has(key) and parsed[key] is Array:
        return parsed[key]
    push_error("Invalid array data in " + path)
    return []

func _load_dictionary(path: String) -> Dictionary:
    var parsed: Variant = _load_json(path)
    if parsed is Dictionary:
        return parsed.duplicate(true)
    push_error("Invalid settings defaults")
    return {}

func _register_actions() -> void:
    _action("throttle", [KEY_W, KEY_UP])
    _action("brake", [KEY_S, KEY_DOWN])
    _action("steer_left", [KEY_A, KEY_LEFT])
    _action("steer_right", [KEY_D, KEY_RIGHT])
    _action("handbrake", [KEY_SPACE])
    _action("boost", [KEY_SHIFT])
    _action("pause", [KEY_ESCAPE])
    _action("camera_toggle", [KEY_C])
    _action("retry", [KEY_R])

func _action(action_name: String, keycodes: Array) -> void:
    if not InputMap.has_action(action_name):
        InputMap.add_action(action_name)
    for keycode in keycodes:
        var event := InputEventKey.new()
        event.keycode = int(keycode)
        InputMap.action_add_event(action_name, event)

func _load_save() -> void:
    if not FileAccess.file_exists(SAVE_PATH):
        return
    var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
    if file == null:
        return
    var parsed: Variant = JSON.parse_string(file.get_as_text())
    file.close()
    if not (parsed is Dictionary):
        return
    var data: Dictionary = parsed
    selected_rider = clampi(int(data.get("selected_rider", 0)), 0, maxi(0, riders.size() - 1))
    selected_bike = clampi(int(data.get("selected_bike", 0)), 0, maxi(0, bikes.size() - 1))
    career_wins = int(data.get("career_wins", 0))
    career_races = int(data.get("career_races", 0))
    if data.get("unlocked_bikes", []) is Array:
        unlocked_bikes = data["unlocked_bikes"]
    if data.get("settings", {}) is Dictionary:
        for key in data["settings"].keys():
            settings[key] = data["settings"][key]
    if data.get("last_result", {}) is Dictionary:
        last_result = data["last_result"]

func save_game() -> void:
    var data := {
        "selected_rider": selected_rider,
        "selected_bike": selected_bike,
        "career_wins": career_wins,
        "career_races": career_races,
        "unlocked_bikes": unlocked_bikes,
        "settings": settings,
        "last_result": last_result,
    }
    var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
    if file == null:
        push_warning("Could not write save file")
        return
    file.store_string(JSON.stringify(data, "\t"))
    file.close()

func get_rider(index: int = -1) -> Dictionary:
    var i := selected_rider if index < 0 else index
    if riders.is_empty():
        return {}
    return riders[clampi(i, 0, riders.size() - 1)]

func get_bike(index: int = -1) -> Dictionary:
    var i := selected_bike if index < 0 else index
    if bikes.is_empty():
        return {}
    return bikes[clampi(i, 0, bikes.size() - 1)]

func get_bike_by_id(bike_id: String) -> Dictionary:
    for bike in bikes:
        if String(bike.get("id", "")) == bike_id:
            return bike
    return get_bike(0)

func get_rider_by_id(rider_id: String) -> Dictionary:
    for rider in riders:
        if String(rider.get("id", "")) == rider_id:
            return rider
    return get_rider(0)

func is_bike_unlocked(bike: Dictionary) -> bool:
    return bool(bike.get("unlocked", true)) or unlocked_bikes.has(String(bike.get("id", "")))

func set_selected_rider(index: int) -> void:
    selected_rider = clampi(index, 0, maxi(0, riders.size() - 1))
    selection_changed.emit()
    save_game()

func set_selected_bike(index: int) -> void:
    selected_bike = clampi(index, 0, maxi(0, bikes.size() - 1))
    selection_changed.emit()
    save_game()

func set_setting(key: String, value: Variant) -> void:
    settings[key] = value
    settings_changed.emit()
    if key == "master_volume":
        apply_audio_volume()
    save_game()

func apply_audio_volume() -> void:
    var volume := clampf(float(settings.get("master_volume", 0.75)), 0.0, 1.0)
    AudioServer.set_bus_volume_db(0, linear_to_db(maxf(volume, 0.001)))

func difficulty_name() -> String:
    var i := clampi(int(settings.get("difficulty", 1)), 0, DIFFICULTY_NAMES.size() - 1)
    return DIFFICULTY_NAMES[i]

func difficulty_speed_multiplier() -> float:
    return [0.90, 1.0, 1.10][clampi(int(settings.get("difficulty", 1)), 0, 2)]

func traffic_density() -> float:
    return clampf(float(settings.get("traffic_density", 1.0)), 0.35, 1.8)

func record_result(result: Dictionary) -> void:
    last_result = result.duplicate(true)
    career_races += 1
    if int(result.get("position", 99)) == 1 and not bool(result.get("crashed", false)):
        career_wins += 1
        if not unlocked_bikes.has("golden_falcon"):
            unlocked_bikes.append("golden_falcon")
            last_result["unlock"] = "GOLDEN FALCON"
    result_saved.emit(last_result)
    save_game()
