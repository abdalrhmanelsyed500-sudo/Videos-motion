extends RefCounted
## Loads JSON data files. Static helpers only; use via `const DataLoader := preload("res://core/data_loader.gd")`.


static func load_json(path: String) -> Variant:
	## Returns the parsed Variant (Dictionary/Array) or null on any error (the error is printed).
	if not FileAccess.file_exists(path):
		push_error("DataLoader: file not found: %s" % path)
		return null
	var text := FileAccess.get_file_as_string(path)
	var json := JSON.new()
	var err := json.parse(text)
	if err != OK:
		push_error("DataLoader: %s line %d: %s" % [path, json.get_error_line(), json.get_error_message()])
		return null
	return json.data


static func load_dict(path: String) -> Dictionary:
	var v: Variant = load_json(path)
	if v is Dictionary:
		return v
	return {}
