extends RefCounted
## Mini-schema validator (A5). GDScript twin of tools/data_tools/minischema.py: SAME semantics, and both must flag
## exactly the
## same error paths for tests/fixtures/validator_cases.json. Use via `const Schema :=
## preload("res://core/schema.gd")`.
## Keys: type, enum, pattern, min, max, props, required, extra, values, key_ref, items, min_items, max_items,
## unique_items, ref.
## Result: Array of [path, message] pairs; empty = valid.


static func validate(value: Variant, schema: Dictionary, ref_lookup: Callable = Callable()) -> Array:
	var errs: Array = []
	_check(value, schema, "$", errs, ref_lookup)
	return errs


static func error_paths(errs: Array) -> PackedStringArray:
	var seen := {}
	for e in errs:
		seen[e[0]] = true
	var out := PackedStringArray()
	for k in seen.keys():
		out.append(str(k))
	out.sort()
	return out


static func _is_num(v: Variant) -> bool:
	return typeof(v) == TYPE_INT or typeof(v) == TYPE_FLOAT


static func _is_int(v: Variant) -> bool:
	return _is_num(v) and floorf(float(v)) == float(v)


static func _enum_has(options: Array, v: Variant) -> bool:
	for e in options:
		if _is_num(v) and _is_num(e):
			if float(v) == float(e):
				return true
		elif typeof(v) == typeof(e) and v == e:
			return true
	return false


static func _check(v: Variant, s: Dictionary, path: String, errs: Array, refs: Callable) -> void:
	var t: String = s.get("type", "")
	var ok := false
	match t:
		"object":
			ok = v is Dictionary
		"array":
			ok = v is Array
		"string":
			ok = v is String
		"boolean":
			ok = v is bool
		"number":
			ok = _is_num(v)
		"integer":
			ok = _is_int(v)
		_:
			errs.append([path, "schema error: unknown type '%s'" % t])
			return
	if not ok:
		errs.append([path, "expected " + t])
		return
	if s.has("enum") and not _enum_has(s["enum"], v):
		errs.append([path, "not in enum"])
	match t:
		"string":
			_check_string(v, s, path, errs, refs)
		"number", "integer":
			if s.has("min") and v < s["min"]:
				errs.append([path, "below min"])
			if s.has("max") and v > s["max"]:
				errs.append([path, "above max"])
		"array":
			_check_array(v, s, path, errs, refs)
		"object":
			_check_object(v, s, path, errs, refs)


static func _check_string(v: String, s: Dictionary, path: String, errs: Array, refs: Callable) -> void:
	if s.has("pattern"):
		var re := RegEx.create_from_string(str(s["pattern"]))
		if not re.is_valid() or re.search(v) == null:
			errs.append([path, "does not match pattern"])
	if s.has("ref") and refs.is_valid() and not refs.call(s["ref"], v):
		errs.append([path, "unknown %s '%s'" % [s["ref"], v]])


static func _check_array(v: Array, s: Dictionary, path: String, errs: Array, refs: Callable) -> void:
	if s.has("min_items") and v.size() < int(s["min_items"]):
		errs.append([path, "too few items"])
	if s.has("max_items") and v.size() > int(s["max_items"]):
		errs.append([path, "too many items"])
	if s.get("unique_items", false):
		for i in range(v.size()):
			for j in range(i):
				if v[j] == v[i]:
					errs.append(["%s[%d]" % [path, i], "duplicate item"])
					break
	if s.has("items"):
		for i in range(v.size()):
			_check(v[i], s["items"], "%s[%d]" % [path, i], errs, refs)


static func _check_object(v: Dictionary, s: Dictionary, path: String, errs: Array, refs: Callable) -> void:
	var props: Dictionary = s.get("props", {})
	for k in s.get("required", []):
		if not v.has(k):
			errs.append(["%s.%s" % [path, k], "required"])
	for k in v.keys():
		var kp := "%s.%s" % [path, k]
		if s.has("key_ref") and refs.is_valid() and not refs.call(s["key_ref"], str(k)):
			errs.append([kp, "unknown %s '%s'" % [s["key_ref"], k]])
		if props.has(k):
			_check(v[k], props[k], kp, errs, refs)
		elif s.has("values"):
			_check(v[k], s["values"], kp, errs, refs)
		elif not s.get("extra", false):
			errs.append([kp, "unknown key"])
