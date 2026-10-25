extends Node
## Reg - data registry autoload. Loads every JSON table once, validates the minimum contract and
## serves it.
## No gameplay numbers live in scripts (master brief code rule 6): tuning/tables come from
## res://data.

const PATHS := {
	"vehicle": "res://data/vehicles/tuktuk_base.json",
	"tuning": "res://data/missions/reward_tuning.json",
	"district": "res://data/districts/mit_okba_p1.json",
	"cast": "res://data/characters/p1_cast.json",
}

var _cache: Dictionary = {}


func _ready() -> void:
	for key in PATHS.keys():
		_cache[key] = _load_json(PATHS[key])


func _load_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("Reg: missing data file %s" % path)
		return {}
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("Reg: cannot open %s" % path)
		return {}
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("Reg: bad JSON in %s" % path)
		return {}
	return parsed


func vehicle() -> Dictionary:
	return _cache.get("vehicle", {})


func tuning() -> Dictionary:
	return _cache.get("tuning", {})


func district() -> Dictionary:
	return _cache.get("district", {})


func cast() -> Array:
	var c: Dictionary = _cache.get("cast", {})
	return c.get("cast", [])


func mesh_spec(name: String) -> Dictionary:
	var path := "res://data/meshes/%s.mesh.json" % name
	if _cache.has("mesh:" + name):
		return _cache["mesh:" + name]
	var d: Dictionary = _load_json(path)
	_cache["mesh:" + name] = d
	return d


## Contract validation used by tests/test_district.gd and test_reward.gd (returns list of problems).
func validate() -> Array:
	var probs: Array = []
	var v: Dictionary = vehicle()
	for k in ["vmax", "accel", "brake", "steer_rate", "grip_lat"]:
		if not v.has(k):
			probs.append("vehicle missing %s" % k)
	var t: Dictionary = tuning()
	for k in ["base_fare", "per_m", "time_base_s", "time_per_m", "reward_cap"]:
		if not t.has(k):
			probs.append("tuning missing %s" % k)
	var d: Dictionary = district()
	for k in ["roads", "pickup", "dest", "start"]:
		if not d.has(k):
			probs.append("district missing %s" % k)
	if cast().is_empty():
		probs.append("cast empty")
	for p in cast():
		var pd: Dictionary = p
		if bool(pd.get("hijab", false)) and not pd.has("hijab_col"):
			probs.append("hijab cast member without hijab colour: %s" % str(pd.get("id", "?")))
	return probs
