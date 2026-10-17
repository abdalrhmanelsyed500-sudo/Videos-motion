extends RefCounted
## Versioned, checksummed, crash-safe save files (A5). Use via `const SaveIO := preload("res://core/save_io.gd")`.
## File = JSON envelope {magic, save_version, game_version, saved_unix, checksum, payload}. `payload` is the state
## serialised to a STRING and
## the checksum (sha256) covers exactly that string, so reading never depends on how floats/ints re-serialise.
## Write = temp file -> previous save becomes <path>.bak -> temp becomes <path>. A crash at any moment leaves a
## readable file or backup.
## Read = main file; if missing/corrupt, automatically the backup ("recovery is always available"). Older versions
## are migrated step by step.
## 64-bit values (seeds) are stored as DECIMAL STRINGS: JSON numbers are doubles and silently lose integers above
## 2^53.
const MAGIC := "COTS-SAVE"
const SAVE_VERSION := 1

## from_version (int) -> Callable(state: Dictionary) -> Dictionary (the state upgraded to from_version + 1)
static var migrations: Dictionary = {}


static func make_envelope_text(state: Dictionary, version: int = SAVE_VERSION) -> String:
	var payload := JSON.stringify(state, "", true, true)
	var env := {
		"magic": MAGIC,
		"save_version": version,
		"game_version": str(ProjectSettings.get_setting("application/config/version", "0")),
		"saved_unix": int(Time.get_unix_time_from_system()),
		"checksum": payload.sha256_text(),
		"payload": payload,
	}
	return JSON.stringify(env, "  ", true, true)


static func write(path: String, state: Dictionary) -> int:
	var tmp := path + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return FileAccess.get_open_error()
	f.store_string(make_envelope_text(state))
	f.close()
	var bak := path + ".bak"
	if FileAccess.file_exists(bak):
		DirAccess.remove_absolute(bak)
	if FileAccess.file_exists(path):
		var e1 := DirAccess.rename_absolute(path, bak)
		if e1 != OK:
			return e1
	return DirAccess.rename_absolute(tmp, path)


static func read(path: String) -> Dictionary:
	var res := _read_one(path)
	if res["ok"]:
		return res
	var bak := _read_one(path + ".bak")
	if bak["ok"]:
		bak["recovered_from_backup"] = true
		bak["first_error"] = res["error"]
		return bak
	return res


static func _fail(msg: String) -> Dictionary:
	return {"ok": false, "error": msg, "state": {}}


static func _read_one(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return _fail("missing: " + path)
	var json := JSON.new()
	if json.parse(FileAccess.get_file_as_string(path)) != OK or not (json.data is Dictionary):
		return _fail("corrupt: not valid JSON")
	var env: Dictionary = json.data
	if env.get("magic", "") != MAGIC:
		return _fail("not a save file of this game")
	var ver := int(env.get("save_version", -1))
	if ver > SAVE_VERSION:
		return _fail("saved by a newer game version (%d > %d)" % [ver, SAVE_VERSION])
	if ver < 0:
		return _fail("missing save_version")
	var payload := str(env.get("payload", ""))
	if str(env.get("checksum", "")) != payload.sha256_text():
		return _fail("checksum mismatch: file is damaged")
	var pj := JSON.new()
	if pj.parse(payload) != OK or not (pj.data is Dictionary):
		return _fail("corrupt payload")
	var state: Dictionary = pj.data
	var from_v := ver
	while from_v < SAVE_VERSION:
		if not migrations.has(from_v):
			return _fail("no migration from save version %d" % from_v)
		state = (migrations[from_v] as Callable).call(state)
		from_v += 1
	var migrated := ver if ver != SAVE_VERSION else -1
	return {"ok": true, "error": "", "state": state, "migrated_from": migrated, "recovered_from_backup": false}


## Validates a state against data/schemas/save_state.schema.json using the registry's references.
static func validate_state(state: Dictionary, reg: Node) -> Array:
	var schema_script: GDScript = load("res://core/schema.gd")
	return schema_script.validate(state, (reg.schemas["save_state"] as Dictionary)["record"], Callable(reg, "lookup"))
