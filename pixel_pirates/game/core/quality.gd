extends Node
## Quality ladder (A1-10). Autoload "Quality".
## Profiles live in data/look/look_profiles.json, the SAME file the Look Lab reads.
## Command line: `... -- --quality=dev_lite`. Default: standard. This module only HOLDS the numbers; the post-process
## shader that consumes them is built in the J-modules.
const DataLoader := preload("res://core/data_loader.gd")
const PROFILES_PATH := "res://data/look/look_profiles.json"

var profile_name: String = "standard"
var _data: Dictionary = {}


func _ready() -> void:
	reload()
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--quality="):
			set_profile(arg.trim_prefix("--quality="))


func reload() -> void:
	_data = DataLoader.load_dict(PROFILES_PATH)


func profile_names() -> PackedStringArray:
	var out := PackedStringArray()
	for k in (_data.get("profiles", {}) as Dictionary).keys():
		out.append(str(k))
	return out


func set_profile(profile_id: String) -> bool:
	if not (_data.get("profiles", {}) as Dictionary).has(profile_id):
		push_warning("Quality: unknown profile '%s'" % profile_id)
		return false
	profile_name = profile_id
	var bus := get_node_or_null("/root/Bus")
	if bus != null:
		bus.quality_changed.emit(profile_id)
	return true


func profile() -> Dictionary:
	return (_data.get("profiles", {}) as Dictionary).get(profile_name, {})


func mood(mood_name: String) -> Dictionary:
	return (_data.get("moods", {}) as Dictionary).get(mood_name, {})


func art_grid() -> Vector2i:
	var g: Array = _data.get("art_grid", [640, 360])
	return Vector2i(int(g[0]), int(g[1]))


## Blur radius in real pixels for a given screen height (profile numbers are defined at 1080 px).
func blur_px_for_height(screen_h: float) -> float:
	var ts: Dictionary = profile().get("tilt_shift", {})
	return float(ts.get("max_blur_px", 0.0)) * screen_h / 1080.0
