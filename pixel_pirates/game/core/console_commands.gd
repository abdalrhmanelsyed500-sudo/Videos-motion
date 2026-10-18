extends RefCounted
## Debug console command core (A7): tokenizer, dispatcher and commands. No UI here, so it is headless-testable.
## A command handler takes `args: PackedStringArray` and returns {ok: bool, text: String}.
## Add a command: write `_c_name(args)`, register it in `_register_all`, and add a line to tests/test_console.gd.
const SaveIO := preload("res://core/save_io.gd")
const IslandMap := preload("res://core/island_map.gd")
const Tuning := preload("res://core/tuning.gd")
const GameState := preload("res://core/game_state.gd")
const MAP_DIRS: Array[String] = ["res://data/islands/maps/", "res://tests/fixtures/islands/maps/"]
const SAVE_DIR := "user://saves/"
const LOG_LEVELS: Array[String] = ["debug", "info", "warn", "error"]
const MAX_STACK := 1000000

var state: RefCounted
var data: Node
var quality: Node = null
var logger: Node = null
var _cmds: Dictionary = {}


func _init(p_data: Node, p_state: RefCounted = null, p_quality: Node = null, p_log: Node = null) -> void:
	data = p_data
	state = p_state if p_state != null else GameState.new()
	quality = p_quality
	logger = p_log
	_register_all()


func _register_all() -> void:
	_reg("help", "help [command]", "List commands, or show one command's usage.", "_c_help")
	_reg("echo", "echo <text>", "Print text (useful for testing).", "_c_echo")
	_reg("clear", "clear", "Clear the console.", "_c_clear")
	_reg("data", "data counts | list <kind> | show <kind> <id> | reload", "Inspect or hot-reload data files.", "_c_data")
	_reg("check", "check", "Reload all data and run every validation (schemas, refs, world rules).", "_c_check")
	_reg("tuning", "tuning <key> | tuning list [prefix]", "Show a balance number: base and effective value.", "_c_tuning")
	_reg("mode", "mode [id] | mode override <rate> <0-3> | mode clear", "Difficulty and per-system toning.", "_c_mode")
	_reg("island", "island list | island info <isl_id>", "Island registry and baked-map facts.", "_c_island")
	_reg("tp", "tp island <isl_id> [landing|<poi_slot>] | tp xy <x_m> <y_m>", "Teleport the player.", "_c_tp")
	_reg("time", "time | time add <hours> | time set <day> <hour>", "Show or change the game clock.", "_c_time")
	_reg("give", "give <item_id> [n]", "Add (or with a negative n remove) items.", "_c_give")
	_reg("inv", "inv", "List the inventory and total cargo weight.", "_c_inv")
	_reg("seed", "seed | seed world|weather <digits>", "Show or set the 64-bit seeds.", "_c_seed")
	_reg("save", "save [name]", "Write the state to user://saves/<name>.json.", "_c_save")
	_reg("load", "load [name]", "Read a save (with backup recovery) and replace the state.", "_c_load")
	_reg("quality", "quality [profile]", "Show or switch the quality profile.", "_c_quality")
	_reg("log", "log [debug|info|warn|error]", "Show or set the log level.", "_c_log")
	_reg("perf", "perf", "FPS, frame time, memory, objects, draw calls.", "_c_perf")


func _reg(cmd_name: String, usage: String, help: String, method: String) -> void:
	_cmds[cmd_name] = {"usage": usage, "help": help, "fn": Callable(self, method)}


static func tokenize(line: String) -> PackedStringArray:
	var out := PackedStringArray()
	var cur := ""
	var quote := ""
	var has_tok := false
	for i in range(line.length()):
		var ch := line[i]
		if quote != "":
			if ch == quote:
				quote = ""
			else:
				cur += ch
		elif ch == "\"" or ch == "'":
			quote = ch
			has_tok = true
		elif ch == " " or ch == "\t":
			if has_tok:
				out.append(cur)
				cur = ""
				has_tok = false
		else:
			cur += ch
			has_tok = true
	if has_tok:
		out.append(cur)
	return out


func execute(line: String) -> Dictionary:
	var toks := tokenize(line.strip_edges())
	if toks.is_empty():
		return _ok("")
	var cmd_name := toks[0].to_lower()
	if not _cmds.has(cmd_name):
		var near := complete(cmd_name.substr(0, 1))
		var hint := " Try: " + ", ".join(near) if not near.is_empty() else " Type 'help'."
		return _fail("unknown command '%s'.%s" % [cmd_name, hint])
	var args := PackedStringArray()
	for i in range(1, toks.size()):
		args.append(toks[i])
	return (_cmds[cmd_name]["fn"] as Callable).call(args)


## command names that start with `prefix`, sorted (used for Tab completion)
func complete(prefix: String) -> PackedStringArray:
	var out := PackedStringArray()
	for k in _cmds.keys():
		if (k as String).begins_with(prefix.to_lower()):
			out.append(k)
	out.sort()
	return out


static func _ok(text: String) -> Dictionary:
	return {"ok": true, "text": text}


static func _fail(text: String) -> Dictionary:
	return {"ok": false, "text": "error: " + text}


func _usage(cmd_name: String) -> Dictionary:
	return _fail("usage: " + str((_cmds[cmd_name] as Dictionary)["usage"]))


func _tuning() -> RefCounted:
	return Tuning.from_registry(data, state.difficulty, state.overrides)


func _find_map(island_id: String) -> RefCounted:
	for dir in MAP_DIRS:
		var path: String = dir + island_id + ".map.json"
		if FileAccess.file_exists(path):
			return IslandMap.from_file(path)
	return null


func _c_help(args: PackedStringArray) -> Dictionary:
	if args.size() >= 1:
		var k := args[0].to_lower()
		if not _cmds.has(k):
			return _fail("no such command '%s'" % k)
		return _ok("%s\n  %s" % [_cmds[k]["usage"], _cmds[k]["help"]])
	var names := PackedStringArray(_cmds.keys())
	names.sort()
	var lines := PackedStringArray()
	for k in names:
		lines.append("%-8s %s" % [k, _cmds[k]["help"]])
	return _ok("\n".join(lines) + "\n(help <command> shows usage)")


func _c_echo(args: PackedStringArray) -> Dictionary:
	return _ok(" ".join(args))


func _c_clear(_args: PackedStringArray) -> Dictionary:
	return {"ok": true, "text": "", "clear": true}


func _c_data(args: PackedStringArray) -> Dictionary:
	var sub := args[0] if args.size() > 0 else ""
	match sub:
		"counts":
			var lines := PackedStringArray()
			var kinds := PackedStringArray(data.tables.keys())
			kinds.sort()
			for k in kinds:
				lines.append("%s: %d" % [k, data.count(k)])
			return _ok("\n".join(lines))
		"list", "show":
			return _data_lookup(sub, args)
		"reload":
			return _c_check(args)
	return _usage("data")


func _data_lookup(sub: String, args: PackedStringArray) -> Dictionary:
	if args.size() < 2 or not data.tables.has(args[1]):
		return _fail("kinds: " + ", ".join(PackedStringArray(data.tables.keys())))
	if sub == "list":
		var ids := PackedStringArray((data.tables[args[1]] as Dictionary).keys())
		ids.sort()
		return _ok(", ".join(ids))
	if args.size() < 3 or not data.has(args[1], args[2]):
		return _fail("no such record. usage: data show <kind> <id>")
	return _ok(JSON.stringify(data.record(args[1], args[2]), "  "))


func _c_check(_args: PackedStringArray) -> Dictionary:
	var errs: PackedStringArray = data.load_all()
	if errs.is_empty():
		return _ok("data reloaded: 0 problems")
	var shown := errs.slice(0, 12)
	var more := "" if errs.size() <= 12 else "\n... and %d more" % (errs.size() - 12)
	return {"ok": false, "text": "data reloaded: %d problems\n%s%s" % [errs.size(), "\n".join(shown), more]}


func _c_tuning(args: PackedStringArray) -> Dictionary:
	if args.is_empty():
		return _usage("tuning")
	var tun := _tuning()
	if args[0] == "list":
		var prefix := args[1] if args.size() > 1 else ""
		var keys := PackedStringArray((data.tables.get("tuning", {}) as Dictionary).keys())
		keys.sort()
		var lines := PackedStringArray()
		for k in keys:
			if k.begins_with(prefix):
				lines.append("%s = %s" % [k, snappedf(tun.f(k), 0.0001)])
		return _ok("\n".join(lines))
	if not data.has("tuning", args[0]):
		return _fail("unknown tuning key '%s'" % args[0])
	var row: Dictionary = data.record("tuning", args[0])
	var eff := snappedf(tun.f(args[0]), 0.0001)
	var text := "%s = %s %s (base %s, mode %s)" % [args[0], eff, row["unit"], row["value"], state.difficulty]
	if row.get("provisional", false):
		text += "  [PROVISIONAL, owner %s]" % row.get("owner", "?")
	return _ok(text)


func _c_mode(args: PackedStringArray) -> Dictionary:
	if args.is_empty():
		return _ok("mode %s, overrides %s" % [state.difficulty, state.overrides])
	if args[0] == "clear":
		state.overrides = {}
		return _ok("overrides cleared")
	if args[0] == "override":
		return _mode_override(args)
	if not data.has("difficulty_mode", args[0]):
		return _fail("unknown mode '%s'" % args[0])
	state.difficulty = args[0]
	return _ok("difficulty mode is now %s" % args[0])


func _mode_override(args: PackedStringArray) -> Dictionary:
	if args.size() < 3 or not data.lookup("multiplier", args[1]) or not args[2].is_valid_float():
		return _fail("usage: mode override <rate> <0-3>; rates: " + ", ".join(data.multiplier_names()))
	var v := float(args[2])
	if v < 0.0 or v > 3.0:
		return _fail("override must be between 0 and 3")
	state.overrides[args[1]] = v
	return _ok("override %s = %s" % [args[1], v])


func _island_ids() -> PackedStringArray:
	var out := PackedStringArray()
	for dir in MAP_DIRS:
		var d := DirAccess.open(dir)
		if d == null:
			continue
		for f in d.get_files():
			if f.ends_with(".map.json"):
				out.append(f.trim_suffix(".map.json"))
	out.sort()
	return out


func _c_island(args: PackedStringArray) -> Dictionary:
	var sub := args[0] if args.size() > 0 else ""
	if sub == "list":
		var lines := PackedStringArray()
		for r in data.all("island"):
			lines.append("%s  %s  tier %s  %s" % [r["id"], r["name"], r["tier"], r["biome"]])
		var text := "\n".join(lines) if not lines.is_empty() else "(registry has no islands yet)"
		return _ok(text + "\nbaked maps: " + ", ".join(_island_ids()))
	if sub == "info" and args.size() >= 2:
		return _island_info(args[1])
	return _usage("island")


func _island_info(island_id: String) -> Dictionary:
	var lines := PackedStringArray()
	if data.has("island", island_id):
		var r: Dictionary = data.record("island", island_id)
		var pos: Dictionary = r["position"]
		var head := "%s '%s' tier %s biome %s" % [island_id, r["name"], r["tier"], r["biome"]]
		lines.append("%s at %s, %s km" % [head, pos["x_km"], pos["y_km"]])
		for n in r.get("neighbors", []):
			lines.append("  -> %s  %s km  %s h by sloop" % [n["id"], n["distance_km"], n["sail_hours_sloop"]])
	var m: RefCounted = _find_map(island_id)
	if m == null and lines.is_empty():
		return _fail("unknown island '%s'" % island_id)
	if m != null:
		if m.error != "":
			return _fail("map error: " + m.error)
		var kinds := {}
		for q in m.pois:
			kinds[q["kind"]] = int(kinds.get(q["kind"], 0)) + 1
		lines.append("map %dx%d tiles (%d m), land %.0f%%, %d landings, POIs %s" % [
			m.width, m.height, m.width * m.tile_m, float(m.stats.get("land_fraction", 0.0)) * 100.0, m.landings.size(), kinds])
		var offers_text := ", ".join(m.offers())
		lines.append("offers: %s; explore time %.1f min; template %s" % [offers_text, m.explore_minutes(), m.template_id])
	else:
		lines.append("(no baked map yet)")
	return _ok("\n".join(lines))


func _c_tp(args: PackedStringArray) -> Dictionary:
	if args.is_empty():
		return _usage("tp")
	if args[0] == "xy":
		if args.size() < 3 or not args[1].is_valid_float() or not args[2].is_valid_float():
			return _usage("tp")
		state.x_m = float(args[1])
		state.y_m = float(args[2])
		state.at_island = ""
		return _ok("teleported to open sea at x=%s m, y=%s m" % [state.x_m, state.y_m])
	var island_id := args[1] if args[0] == "island" and args.size() > 1 else args[0]
	var target_idx := 2 if args[0] == "island" else 1
	var target := args[target_idx] if args.size() > target_idx else "landing"
	if not island_id.begins_with("isl_"):
		return _usage("tp")
	return _tp_island(island_id, target)


func _tp_island(island_id: String, target: String) -> Dictionary:
	var m: RefCounted = _find_map(island_id)
	if m == null or m.error != "":
		return _fail("no usable baked map for '%s'" % island_id)
	var cell := Vector2i(-1, -1)
	if target == "landing":
		cell = Vector2i(int(m.landings[0]["x"]), int(m.landings[0]["y"]))
	else:
		for q in m.pois:
			if q["slot"] == target:
				cell = Vector2i(int(q["x"]), int(q["y"]))
	if cell.x < 0:
		var slots := PackedStringArray()
		for q in m.pois:
			slots.append(q["slot"])
		return _fail("no target '%s'. try landing, %s" % [target, ", ".join(slots)])
	var local: Vector2 = m.cell_to_local(cell.x, cell.y)
	var origin := Vector2.ZERO
	if data.has("island", island_id):
		var pos: Dictionary = data.record("island", island_id)["position"]
		origin = Vector2(float(pos["x_km"]), float(pos["y_km"])) * 1000.0
	state.x_m = origin.x + local.x
	state.y_m = origin.y + local.y
	state.at_island = island_id
	var where := "%s %s (cell %d,%d)" % [island_id, target, cell.x, cell.y]
	return _ok("teleported to %s x=%.1f m, y=%.1f m" % [where, state.x_m, state.y_m])


func _c_time(args: PackedStringArray) -> Dictionary:
	if args.is_empty():
		return _ok(state.clock_text())
	if args[0] == "add" and args.size() > 1 and args[1].is_valid_float():
		state.add_hours(float(args[1]))
		return _ok(state.clock_text())
	if args[0] == "set" and args.size() > 2 and args[1].is_valid_int() and args[2].is_valid_float():
		state.set_clock(int(args[1]), float(args[2]))
		return _ok(state.clock_text())
	return _usage("time")


func _c_give(args: PackedStringArray) -> Dictionary:
	if args.is_empty():
		return _usage("give")
	if not data.has("item", args[0]):
		return _fail("unknown item '%s'" % args[0])
	var n := 1
	if args.size() > 1:
		if not args[1].is_valid_int():
			return _fail("n must be a whole number")
		n = int(args[1])
	var now: int = state.add_item(args[0], n)
	if now > MAX_STACK:
		now = MAX_STACK
		state.inventory[args[0]] = now
	return _ok("%s: %d" % [args[0], now])


func _c_inv(_args: PackedStringArray) -> Dictionary:
	if state.inventory.is_empty():
		return _ok("(empty)")
	var ids := PackedStringArray((state.inventory as Dictionary).keys())
	ids.sort()
	var lines := PackedStringArray()
	var total := 0.0
	for k in ids:
		var kg := float(data.record("item", k).get("weight_kg", 0.0)) * int(state.inventory[k])
		total += kg
		lines.append("%-22s x%-7d %8.1f kg" % [k, state.inventory[k], kg])
	lines.append("total cargo weight: %.1f kg" % total)
	return _ok("\n".join(lines))


func _c_seed(args: PackedStringArray) -> Dictionary:
	if args.is_empty():
		return _ok("world %s, weather %s" % [state.world_seed, state.weather_seed])
	var re := RegEx.create_from_string("^[0-9]{1,20}$")
	if args.size() < 2 or not (args[0] in ["world", "weather"]) or re.search(args[1]) == null:
		return _usage("seed")
	if args[0] == "world":
		state.world_seed = args[1]
	else:
		state.weather_seed = args[1]
	return _ok("%s seed = %s" % [args[0], args[1]])


func _state_problems(d: Dictionary) -> PackedStringArray:
	var out := PackedStringArray()
	for e in SaveIO.validate_state(d, data):
		out.append("%s %s" % [e[0], e[1]])
	return out


func _save_path(args: PackedStringArray) -> String:
	var slot := args[0] if args.size() > 0 else "debug"
	var re := RegEx.create_from_string("^[A-Za-z0-9_-]{1,32}$")
	if re.search(slot) == null:
		return ""
	return SAVE_DIR + slot + ".json"


func _c_save(args: PackedStringArray) -> Dictionary:
	var path := _save_path(args)
	if path == "":
		return _fail("save name: letters, digits, _ and - only (max 32)")
	var problems := _state_problems(state.to_dict())
	if not problems.is_empty():
		return _fail("state is invalid, not saved: " + "; ".join(problems))
	DirAccess.make_dir_recursive_absolute(SAVE_DIR)
	var err: int = SaveIO.write(path, state.to_dict())
	if err != OK:
		return _fail("write failed (error %d)" % err)
	return _ok("saved " + path)


func _c_load(args: PackedStringArray) -> Dictionary:
	var path := _save_path(args)
	if path == "":
		return _fail("save name: letters, digits, _ and - only (max 32)")
	var r: Dictionary = SaveIO.read(path)
	if not r["ok"]:
		return _fail(str(r["error"]))
	var problems := _state_problems(r["state"])
	if not problems.is_empty():
		return _fail("save is invalid: " + "; ".join(problems))
	state.apply_dict(r["state"])
	var note := " (recovered from backup)" if r.get("recovered_from_backup", false) else ""
	return _ok("loaded %s%s: %s" % [path, note, state.clock_text()])


func _c_quality(args: PackedStringArray) -> Dictionary:
	if quality == null:
		return _fail("Quality autoload is not available here")
	if args.is_empty():
		return _ok("profile %s; available: %s" % [quality.profile_name, ", ".join(quality.profile_names())])
	if not quality.set_profile(args[0]):
		return _fail("unknown profile '%s'" % args[0])
	return _ok("quality profile is now " + args[0])


func _c_log(args: PackedStringArray) -> Dictionary:
	if logger == null:
		return _fail("Log autoload is not available here")
	if args.is_empty():
		return _ok("log level: " + LOG_LEVELS[logger.level])
	var idx := LOG_LEVELS.find(args[0].to_lower())
	if idx < 0:
		return _usage("log")
	logger.level = idx
	return _ok("log level is now " + LOG_LEVELS[idx])


func _c_perf(_args: PackedStringArray) -> Dictionary:
	var mb := 1048576.0
	return _ok("fps %d | frame %.2f ms | static mem %.0f MB | video mem %.0f MB | objects %d | draw calls %d" % [
		Performance.get_monitor(Performance.TIME_FPS), Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0,
		Performance.get_monitor(Performance.MEMORY_STATIC) / mb,
		Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / mb,
		Performance.get_monitor(Performance.OBJECT_COUNT),
		Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)])
