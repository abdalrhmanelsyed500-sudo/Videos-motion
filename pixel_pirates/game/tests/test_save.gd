extends RefCounted
## Save format: roundtrip, 64-bit seeds as strings, backup recovery, tamper detection, version handling, migration,
## schema validation.
const SaveIO := preload("res://core/save_io.gd")
const PATH := "user://a5_test_save.json"


func _rm(p: String) -> void:
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(p)


func _clean() -> void:
	for suffix in ["", ".bak", ".tmp"]:
		_rm(PATH + suffix)


func _state() -> Dictionary:
	return {
		"meta": {"profile": "Test", "difficulty": "mode_normal", "playtime_s": 3600},
		"clock": {"t_seconds": 123456},
		"rng": {"world_seed": "18446744073709551615", "weather_seed": "42"},
		"player": {"x_m": 1234567.891, "y_m": -987654.321, "at_island": ""},
		"inventory": {"item_hardtack": 40, "item_rope": 3},
	}


func run(t: Object) -> void:
	_clean()
	var st := _state()
	t.check(SaveIO.write(PATH, st) == OK, "write succeeds")
	var r := SaveIO.read(PATH)
	t.check(r["ok"], "read succeeds: %s" % r["error"])
	var s2: Dictionary = r["state"]
	t.check(s2["rng"]["world_seed"] == "18446744073709551615", "64-bit seed survives exactly (stored as string)")
	t.check(int(s2["clock"]["t_seconds"]) == 123456, "clock survives")
	t.check(is_equal_approx(float(s2["player"]["x_m"]), 1234567.891), "double position survives")
	t.check(int(s2["inventory"]["item_hardtack"]) == 40, "inventory survives")
	# second write must keep the first as backup
	st["clock"]["t_seconds"] = 200000
	t.check(SaveIO.write(PATH, st) == OK, "second write succeeds")
	t.check(FileAccess.file_exists(PATH + ".bak"), "backup file exists after second write")
	# damage the main file: reading must recover from the backup
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	f.store_string("{ this is not json")
	f.close()
	var rec := SaveIO.read(PATH)
	t.check(rec["ok"] and rec["recovered_from_backup"], "corrupt main file recovers from backup")
	t.check(int(rec["state"]["clock"]["t_seconds"]) == 123456, "backup holds the previous save")
	# tampered payload: checksum must fail on both
	var good := SaveIO.make_envelope_text(_state())
	var tampered := good.replace("123456", "999999")
	_rm(PATH + ".bak")
	f = FileAccess.open(PATH, FileAccess.WRITE)
	f.store_string(tampered)
	f.close()
	var bad := SaveIO.read(PATH)
	t.check(not bad["ok"] and "checksum" in str(bad["error"]), "tampered file is detected")
	# newer version refused
	f = FileAccess.open(PATH, FileAccess.WRITE)
	f.store_string(SaveIO.make_envelope_text(_state(), SaveIO.SAVE_VERSION + 5))
	f.close()
	var newer := SaveIO.read(PATH)
	t.check(not newer["ok"] and "newer" in str(newer["error"]), "newer save version is refused")
	# migration v0 -> v1
	SaveIO.migrations[0] = func(s: Dictionary) -> Dictionary:
		s["meta"]["profile"] = str(s["meta"]["profile"]) + "-migrated"
		return s
	f = FileAccess.open(PATH, FileAccess.WRITE)
	f.store_string(SaveIO.make_envelope_text(_state(), 0))
	f.close()
	var mig := SaveIO.read(PATH)
	t.check(mig["ok"] and int(mig["migrated_from"]) == 0, "v0 save is migrated")
	t.check(mig["state"]["meta"]["profile"] == "Test-migrated", "migration function ran")
	SaveIO.migrations.erase(0)
	var nomig := SaveIO.read(PATH)
	t.check(not nomig["ok"] and "migration" in str(nomig["error"]), "missing migration is reported")
	_clean()
	# schema validation of a state
	var reg: Node = load("res://core/registry.gd").new()
	reg.load_all()
	t.check(SaveIO.validate_state(_state(), reg).is_empty(), "sample state validates against save_state schema")
	var broken := _state()
	broken["inventory"]["item_unknown_thing"] = 1
	broken["rng"]["world_seed"] = "not a number"
	t.check(SaveIO.validate_state(broken, reg).size() == 2, "unknown item and bad seed are both flagged")
	reg.free()
