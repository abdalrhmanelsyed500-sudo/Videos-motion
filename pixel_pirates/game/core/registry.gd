extends Node
## Data registry (A5). Autoload "Data". Loads every enveloped JSON under res://data (except schemas/), validates each
## record
## against res://data/schemas/<kind>.schema.json, checks unique keys, id prefixes and cross references, and serves
## records.
## File envelope: {"schema": 1, "kind": "<kind>", "records": [ ... ]}. Files without "records" (palette, look
## profiles) are ignored.
## EXPORT NOTE: add `*.json` to the export preset's "non-resource files" filter, or the exported game will have no
## data.
const DataLoader := preload("res://core/data_loader.gd")
const Schema := preload("res://core/schema.gd")
const DATA_ROOT := "res://data"
const MANIFEST_PATH := "res://art/manifest/sprites.json"

var tables: Dictionary = {}  # kind -> { key -> record }
var schemas: Dictionary = {}  # kind -> schema file content
var errors: PackedStringArray = PackedStringArray()
var _origin: Dictionary = {}  # "kind/key" -> file
var _asset_ids: Dictionary = {}
var _multipliers: Dictionary = {}


func _ready() -> void:
	load_all()
	for e in errors:
		push_error("Data: " + e)


func load_all(root: String = DATA_ROOT) -> PackedStringArray:
	tables.clear()
	schemas.clear()
	_origin.clear()
	_asset_ids.clear()
	_multipliers.clear()
	errors = PackedStringArray()
	var man := DataLoader.load_dict(MANIFEST_PATH).get("assets", {}) as Dictionary
	for k in man.keys():
		_asset_ids[k] = true
	_load_schemas(root + "/schemas")
	var files: Array[String] = []
	_collect_json(root, files)
	files.sort()
	for f in files:
		_load_file(f)
	_check_refs()
	return errors


func has(kind: String, key: String) -> bool:
	return (tables.get(kind, {}) as Dictionary).has(key)


func record(kind: String, key: String) -> Dictionary:
	return (tables.get(kind, {}) as Dictionary).get(key, {})


func all(kind: String) -> Array:
	return (tables.get(kind, {}) as Dictionary).values()


func count(kind: String) -> int:
	return (tables.get(kind, {}) as Dictionary).size()


## Reference lookup used by schema `ref` / `key_ref`.
func lookup(kind: String, key: String) -> bool:
	if kind == "asset":
		return _asset_ids.has(key)
	if kind == "multiplier":
		return _multipliers.has(key)
	return has(kind, key)


func _load_schemas(dir_path: String) -> void:
	var d := DirAccess.open(dir_path)
	if d == null:
		errors.append("cannot open " + dir_path)
		return
	for f in d.get_files():
		if f.ends_with(".schema.json"):
			schemas[f.trim_suffix(".schema.json")] = DataLoader.load_dict(dir_path + "/" + f)
	var dm: Dictionary = schemas.get("difficulty_mode", {})
	var rec_schema: Dictionary = dm.get("record", {})
	var mult_schema: Dictionary = (rec_schema.get("props", {}) as Dictionary).get("multipliers", {})
	var req: Array = mult_schema.get("required", [])
	for k in req:
		_multipliers[k] = true


func _collect_json(dir_path: String, out: Array[String]) -> void:
	var d := DirAccess.open(dir_path)
	if d == null:
		return
	for sub in d.get_directories():
		if sub != "schemas":
			_collect_json(dir_path + "/" + sub, out)
	for f in d.get_files():
		if f.ends_with(".json"):
			out.append(dir_path + "/" + f)


func _load_file(path: String) -> void:
	var doc: Variant = DataLoader.load_json(path)
	if not (doc is Dictionary) or not (doc as Dictionary).has("records"):
		return
	var kind: Variant = doc.get("kind")
	if int(doc.get("schema", 0)) != 1 or not (kind is String) or not (doc["records"] is Array):
		errors.append("%s: bad envelope (need schema=1, kind, records[])" % path)
		return
	if not schemas.has(kind):
		errors.append("%s: no schema for kind '%s'" % [path, kind])
		return
	var sch: Dictionary = schemas[kind]
	var key_field: String = sch["key_field"]
	var prefix: String = sch["id_prefix"]
	var recs: Array = doc["records"]
	for i in range(recs.size()):
		var rec: Variant = recs[i]
		for e in Schema.validate(rec, sch["record"]):
			errors.append("%s record[%d] %s: %s" % [path, i, e[0], e[1]])
		if not (rec is Dictionary) or not (rec as Dictionary).has(key_field):
			continue
		if not ((rec as Dictionary)[key_field] is String):
			continue
		var key: String = rec[key_field]
		if prefix != "" and not key.begins_with(prefix + "_"):
			errors.append("%s: id '%s' must start with '%s_'" % [path, key, prefix])
		if not tables.has(kind):
			tables[kind] = {}
		if (tables[kind] as Dictionary).has(key):
			errors.append("%s: duplicate %s '%s' (also in %s)" % [path, kind, key, _origin.get("%s/%s" % [kind, key], "?")])
		tables[kind][key] = rec
		_origin["%s/%s" % [kind, key]] = path


func _check_refs() -> void:
	for kind in tables.keys():
		for key in (tables[kind] as Dictionary).keys():
			var rec: Dictionary = tables[kind][key]
			for e in Schema.validate(rec, (schemas[kind] as Dictionary)["record"], Callable(self, "lookup")):
				if (e[1] as String).begins_with("unknown ") and "'" in (e[1] as String):
					errors.append("%s %s '%s' %s: %s" % [_origin["%s/%s" % [kind, key]], kind, key, e[0], e[1]])
	for key in (tables.get("tuning", {}) as Dictionary).keys():
		var r: Dictionary = tables["tuning"][key]
		if float(r["value"]) < float(r["min"]) or float(r["value"]) > float(r["max"]):
			errors.append("tuning '%s': value %s outside [%s, %s]" % [key, r["value"], r["min"], r["max"]])
