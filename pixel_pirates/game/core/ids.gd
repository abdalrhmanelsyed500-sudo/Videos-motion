extends RefCounted
## ID grammar for ALL data records and art assets (Module A2). Use via `const Ids := preload("res://core/ids.gd")`.
##   data id   = <kind>_<slug>      kinds below; slug is lower snake_case; islands are isl_NNN (numeric, rename-proof)
##   asset id  = <prefix>_<words>   prefixes below
const DATA_KINDS: PackedStringArray = [
	"isl", "reg", "crew", "npc", "item", "rcp", "ship", "evt", "loc", "fac", "qst", "dlg", "clue",
]
const ASSET_PREFIXES: PackedStringArray = ["spr", "til", "prp", "shp", "ico", "fx", "ui", "bg"]

static var _re_data: RegEx = null
static var _re_island: RegEx = null


static func _init_regex() -> void:
	if _re_data == null:
		_re_data = RegEx.create_from_string("^[a-z]+(_[a-z0-9]+)+$")
		_re_island = RegEx.create_from_string("^isl_[0-9]{3}$")


static func prefix_of(id: String) -> String:
	var i := id.find("_")
	return id.substr(0, i) if i > 0 else ""


static func is_valid_data_id(id: String) -> bool:
	_init_regex()
	if _re_data.search(id) == null:
		return false
	var kind := prefix_of(id)
	if not DATA_KINDS.has(kind):
		return false
	if kind == "isl":
		return _re_island.search(id) != null
	return true


static func is_valid_asset_id(id: String) -> bool:
	_init_regex()
	return _re_data.search(id) != null and ASSET_PREFIXES.has(prefix_of(id))
