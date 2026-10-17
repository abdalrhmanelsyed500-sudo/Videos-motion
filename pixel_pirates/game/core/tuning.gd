extends RefCounted
## Tuning access with difficulty scaling (A5). EVERY balance number in game code comes through here:
## `tuning.f("food.need_kcal_per_man_day")`.
## Effective value = base * multiplier (scale_mode "mul") or base / multiplier ("div"; for "time until X" values,
## where a higher
## rate means a SHORTER time). Multiplier = per-system override if set, else the difficulty mode's value, else 1.0.
## Pure data in, number out: headless-testable. Use via `load("res://core/tuning.gd").new(...)` or `from_registry`.
var _rows: Dictionary
var _mults: Dictionary
var _overrides: Dictionary


func _init(rows: Dictionary, mode_record: Dictionary, overrides: Dictionary = {}) -> void:
	_rows = rows
	_mults = mode_record.get("multipliers", {})
	_overrides = overrides


static func from_registry(reg: Node, mode_id: String, overrides: Dictionary = {}) -> RefCounted:
	var script: GDScript = load("res://core/tuning.gd")
	return script.new(reg.tables.get("tuning", {}), reg.record("difficulty_mode", mode_id), overrides)


func multiplier(mult_key: String) -> float:
	return float(_overrides.get(mult_key, _mults.get(mult_key, 1.0)))


func base(key: String) -> float:
	if not _rows.has(key):
		push_error("Tuning: unknown key '%s'" % key)
		return 0.0
	return float((_rows[key] as Dictionary)["value"])


func f(key: String) -> float:
	var b := base(key)
	var row: Dictionary = _rows.get(key, {})
	if not row.has("scale"):
		return b
	var m := multiplier(str(row["scale"]))
	if str(row.get("scale_mode", "mul")) == "div":
		return b / maxf(m, 0.0001)
	return b * m


func as_int(key: String) -> int:
	return roundi(f(key))
