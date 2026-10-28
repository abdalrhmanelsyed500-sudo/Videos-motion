extends RefCounted
const CampaignState = preload("res://core/campaign_state.gd")
## Versioned JSON save/load with validation. Paths under user://saves/.
## Never overwrites the only valid save without a fallback: writes go to a
## .tmp file first, then rotate old save to .bak before rename.

const DIR := "user://saves/"
const META_KEYS := ["slot", "saved_at_day", "campaign_seed", "schema_version", "note"]


func _ensure_dir() -> void:
	if not DirAccess.dir_exists_absolute(DIR):
		DirAccess.make_dir_recursive_absolute(DIR)


func slot_path(slot: int) -> String:
	return DIR + "slot_%d.json" % slot


func save_campaign(state, slot: int, note: String = "") -> String:
	_ensure_dir()
	var snapshot: Dictionary = state.serialize()
	# Keep a readable JSON copy plus an exact Variant-byte copy. Godot's JSON
	# parser can round decimal floats by one ULP; the exact copy preserves the
	# RNG-driven simulation across save/reload without enabling object decoding.
	var exact := Marshalls.raw_to_base64(var_to_bytes(snapshot))
	var payload := {"meta": {"slot": slot, "saved_at_day": state.day,
		"campaign_seed": state.seed, "schema_version": state.schema_version,
		"note": note}, "state": snapshot, "state_exact": exact}
	var tmp := slot_path(slot) + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return "cannot open %s for write" % tmp
	f.store_string(JSON.stringify(payload, "\t", false, true))
	f.close()
	var bak := slot_path(slot) + ".bak"
	if FileAccess.file_exists(slot_path(slot)):
		if FileAccess.file_exists(bak):
			var remove_error := DirAccess.remove_absolute(bak)
			if remove_error != OK:
				return "cannot rotate backup (%d); original retained" % remove_error
		var backup_error := DirAccess.rename_absolute(slot_path(slot), bak)
		if backup_error != OK:
			return "cannot rotate save (%d); original retained" % backup_error
	var rename_error := DirAccess.rename_absolute(tmp, slot_path(slot))
	if rename_error != OK:
		return "cannot finalize save (%d); backup retained" % rename_error
	return ""


func load_campaign(slot: int) -> Dictionary:
	## returns {"error": String, "state": CampaignState-or-null, "meta": Dictionary}
	var path := slot_path(slot)
	if not FileAccess.file_exists(path):
		if FileAccess.file_exists(path + ".bak"):
			path = path + ".bak"
		else:
			return {"error": "no save in slot %d" % slot, "state": null, "meta": {}}
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {"error": "cannot read " + path, "state": null, "meta": {}}
	var parsed = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(parsed) != TYPE_DICTIONARY or not parsed.has("state"):
		return {"error": "corrupt save (bad json root)", "state": null, "meta": {}}
	var state_data = parsed["state"]
	if parsed.has("state_exact"):
		if typeof(parsed["state_exact"]) != TYPE_STRING:
			return {"error": "invalid exact state", "state": null, "meta": {}}
		state_data = bytes_to_var(Marshalls.base64_to_raw(parsed["state_exact"]))
	if typeof(state_data) != TYPE_DICTIONARY:
		return {"error": "invalid save state", "state": null, "meta": {}}
	var st = CampaignState.new()
	var err: String = st.deserialize(state_data)
	if err != "":
		return {"error": err, "state": null, "meta": {}}
	return {"error": "", "state": st, "meta": parsed.get("meta", {})}


func list_slots() -> Array:
	var out: Array = []
	var d := DirAccess.open(DIR)
	if d == null:
		return out
	for i in range(1, 6):
		if FileAccess.file_exists(slot_path(i)) or FileAccess.file_exists(slot_path(i) + ".bak"):
			out.append(i)
	return out
