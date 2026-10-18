extends RefCounted
## Debug console command core (A7): tokenizer, dispatcher and commands. No UI here, so it is headless-testable.
## A command handler takes `args: PackedStringArray` and returns {ok: bool, text: String}.
## Add a command: write `_c_name(args)`, register it in `_register_all`, and add a line to tests/test_console.gd.
const DataLoader := preload("res://core/data_loader.gd")
const SaveIO := preload("res://core/save_io.gd")
const IslandMap := preload("res://core/island_map.gd")
const Tuning := preload("res://core/tuning.gd")
const GameState := preload("res://core/game_state.gd")
const VoyageClock := preload("res://core/voyage_clock.gd")
const Ocean := preload("res://core/ocean.gd")
const SeaState := preload("res://core/sea_state.gd")
const MAP_DIRS: Array[String] = ["res://data/islands/maps/", "res://tests/fixtures/islands/maps/"]
const SAVE_DIR := "user://saves/"
const LOG_LEVELS: Array[String] = ["debug", "info", "warn", "error"]
const MAX_STACK := 1000000

## Debug live mode (`time live on`): the console UI feeds real frame time to the world clock.
var live := false
var state: RefCounted
var sea: RefCounted = null  ## SeaState of the voyage; created on first use (E1 slice)
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
	_reg("time", "time | watch | tick <real_s> | live on|off | pause|resume <reason> | add <h> | set <day> <hour>",
		"World clock: show, tick by real seconds, pause. add/set are debug-only jumps.", "_c_time")
	_reg("give", "give <item_id> [n]", "Add (or with a negative n remove) items.", "_c_give")
	_reg("inv", "inv", "List the inventory and total cargo weight.", "_c_inv")
	_reg("seed", "seed | seed world|weather <digits>", "Show or set the 64-bit seeds.", "_c_seed")
	_reg("save", "save [name]", "Write the state to user://saves/<name>.json.", "_c_save")
	_reg("load", "load [name]", "Read a save (with backup recovery) and replace the state.", "_c_load")
	_reg("quality", "quality [profile]", "Show or switch the quality profile.", "_c_quality")
	_reg("log", "log [debug|info|warn|error]", "Show or set the log level.", "_c_log")
	_reg("perf", "perf", "FPS, frame time, memory, objects, draw calls.", "_c_perf")
	_reg("route", "route | route <n> | route heading <deg> | route status",
			"E1 slice route: list checkpoints, jump the ship to one (debug: places ship and clock only).", "_c_route")
	_reg("ocean", "ocean <x_km> <y_km> [t_days]", "What the sea and sky are doing at a point (default: now).", "_c_ocean")


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
		state.clock.set_location("sea")
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
	state.clock.set_location("island")
	var where := "%s %s (cell %d,%d)" % [island_id, target, cell.x, cell.y]
	return _ok("teleported to %s x=%.1f m, y=%.1f m" % [where, state.x_m, state.y_m])


func _c_time(args: PackedStringArray) -> Dictionary:
	if args.is_empty():
		return _ok(state.clock_text())
	var result := _usage("time")
	match args[0]:
		"watch":
			result = _ok(_time_watch_text())
		"tick":
			result = _time_tick(args)
		"live":
			result = _time_live(args)
		"pause", "resume":
			result = _time_pause(args)
		"add", "set":
			result = _time_debug_jump(args)
	return result


func _band_starts(tun: RefCounted) -> Array:
	var out: Array = []
	for k in ["dawn", "morning", "day", "sunset", "evening", "night"]:
		out.append(tun.f("time.%s_start_hour" % k))
	return out


func _time_watch_text() -> String:
	var tun := _tuning()
	var h: float = state.hour_of_day()
	var wl: float = tun.f("crew.watch_length_hours")
	var starts := _band_starts(tun)
	var level := VoyageClock.daylight(h, starts, tun.f("light.night_floor"), tun.f("light.dawn_end_level"),
			tun.f("light.sunset_end_level"))
	var rate: float = state.clock.minutes_per_day
	var to_report := VoyageClock.hours_to_real_seconds(fposmod(tun.f("time.report_hour") - h, 24.0), rate)
	var paused := "no"
	if state.clock.is_paused():
		paused = ", ".join(state.clock.pause_reasons())
	var line1 := "%s - %s watch, last bell %d | band %s, daylight %.2f" % [state.clock_text(),
			VoyageClock.watch_name(VoyageClock.watch_index(h, wl)), VoyageClock.last_bell(h, wl),
			VoyageClock.band_of_hour(h, starts), level]
	var line2 := "1 day = %.0f real min (1 game hour = %.1f s) | next Morning Report in %.0f real s | paused: %s" % [
			rate, VoyageClock.hours_to_real_seconds(1.0, rate), to_report, paused]
	return line1 + "\n" + line2


## One line for the debug HUD: clock, band, daylight level, where the ship is, pause state.
func hud_text() -> String:
	var tun := _tuning()
	var h: float = state.hour_of_day()
	var starts := _band_starts(tun)
	var level := VoyageClock.daylight(h, starts, tun.f("light.night_floor"), tun.f("light.dawn_end_level"),
			tun.f("light.sunset_end_level"))
	var where: String = state.at_island if state.at_island != "" else "sea"
	var line := "%s | %s | daylight %.2f | %s" % [state.clock_text(), VoyageClock.band_of_hour(h, starts), level, where]
	if state.clock.is_paused():
		line += " | PAUSED: " + ", ".join(state.clock.pause_reasons())
	return line


func _time_live(args: PackedStringArray) -> Dictionary:
	if args.size() < 2 or not (args[1] in ["on", "off"]):
		return _usage("time")
	live = args[1] == "on"
	if live:
		return _ok("live clock ON: the clock follows real time, 1 game day = %.0f real min. HUD line at the top right." %
				state.clock.minutes_per_day)
	return _ok("live clock OFF: the clock holds still until you tick it.")


func _time_tick(args: PackedStringArray) -> Dictionary:
	if args.size() < 2 or not args[1].is_valid_float():
		return _usage("time")
	var real_s := float(args[1])
	if real_s < 0.0 or real_s > 86400.0:
		return _fail("real seconds must be between 0 and 86400")
	var game_s: float = state.tick(real_s)
	return _ok("%.1f real s -> %.1f game s (%.2f h) | %s" % [real_s, game_s, game_s / 3600.0, state.clock_text()])


func _time_pause(args: PackedStringArray) -> Dictionary:
	var re := RegEx.create_from_string("^[a-z_]{1,24}$")
	if args.size() < 2 or re.search(args[1]) == null:
		return _fail("usage: time %s <reason> (reason: lowercase letters and _, e.g. report, planning, menu)" % args[0])
	if args[0] == "pause":
		state.clock.pause(args[1])
	else:
		state.clock.resume(args[1])
	var reasons: PackedStringArray = state.clock.pause_reasons()
	var now := "time runs" if reasons.is_empty() else "paused by " + ", ".join(reasons)
	return _ok("%s %s: %s" % [args[0], args[1], now])


func _time_debug_jump(args: PackedStringArray) -> Dictionary:
	if args[0] == "add" and args.size() > 1 and args[1].is_valid_float():
		state.add_hours(float(args[1]))
		return _ok("[debug jump] " + state.clock_text())
	if args[0] == "set" and args.size() > 2 and args[1].is_valid_int() and args[2].is_valid_float():
		state.set_clock(int(args[1]), float(args[2]))
		return _ok("[debug jump] " + state.clock_text())
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


# ---- E1: ocean and the slice route -------------------------------------------------------------
func ensure_sea() -> RefCounted:
	if sea == null:
		sea = SeaState.new(Ocean.load_default())
	return sea


func _now_days() -> float:
	return float(state.clock.t) / 86400.0


func _sample_text(smp: Dictionary) -> String:
	var line1 := "%s | lat %.1f | %s" % [smp["region"], smp["lat"], state.clock_text()]
	var line2 := "wind %.0f kn from %.0f deg | waves %.1f m | storm %.2f herald %.2f" % [
			smp["wind_kn"], smp["wind_from_deg"], smp["wave_m"], smp["storm"], smp["herald"]]
	line2 += " | rain %.2f fog %.2f | visibility %.1f km" % [smp["rain"], smp["fog"], smp["visibility_km"]]
	var line3 := "sea %.1f C air %.1f C | ice %.2f | light peak %.2f floor %.2f" % [
			smp["sst_c"], smp["air_c"], smp["ice"], smp["light_peak"], smp["light_floor"]]
	line3 += " | productivity %.2f | current %.1f kn" % [smp["productivity"], smp["current_u_kn"]]
	return line1 + "\n" + line2 + "\n" + line3


func _c_ocean(args: PackedStringArray) -> Dictionary:
	if args.size() < 2 or not args[0].is_valid_float() or not args[1].is_valid_float():
		return _usage("ocean")
	var t_days := float(args[2]) if args.size() > 2 and args[2].is_valid_float() else _now_days()
	var oc: RefCounted = ensure_sea().ocean
	var x := float(args[0])
	var y := float(args[1])
	if x < 0.0 or y < 0.0 or x > oc.world_w or y > oc.world_h:
		return _fail("outside the world (0..%.0f, 0..%.0f km)" % [oc.world_w, oc.world_h])
	return _ok(_sample_text(oc.sample(x, y, t_days)))


func _checkpoints() -> Array:
	var doc := DataLoader.load_dict("res://data/world/slice_route.json")
	return doc.get("checkpoints", [])


func _c_route(args: PackedStringArray) -> Dictionary:
	var cps := _checkpoints()
	if cps.is_empty():
		return _fail("res://data/world/slice_route.json has no checkpoints")
	var result := _usage("route")
	if args.is_empty():
		result = _route_list(cps)
	elif args[0] == "status":
		result = _route_status()
	elif args[0] == "heading":
		result = _route_heading(args)
	else:
		var token := args[1] if args[0] == "jump" and args.size() > 1 else args[0]
		if token.is_valid_int():
			result = _route_jump(cps, int(token))
	return result


func _route_list(cps: Array) -> Dictionary:
	var lines: Array[String] = []
	for c in cps:
		var head := "%d  %s" % [int(c["id"]), c["name"]]
		lines.append("%s  (%.0f, %.0f km, day %.2f)" % [head, c["x_km"], c["y_km"], c["t_days"]])
		lines.append("     " + str(c["why"]))
	return _ok("\n".join(lines))


func _route_status() -> Dictionary:
	var sv := ensure_sea()
	var smp: Dictionary = sv.ocean.sample(sv.x_km, sv.y_km, _now_days())
	return _ok("ship (%.0f, %.0f) km heading %.0f | sailed %.0f km\n%s" % [
			sv.x_km, sv.y_km, sv.heading_deg, sv.distance_km, _sample_text(smp)])


func _route_heading(args: PackedStringArray) -> Dictionary:
	if args.size() < 2 or not args[1].is_valid_float():
		return _usage("route")
	var sv := ensure_sea()
	sv.heading_deg = fposmod(float(args[1]), 360.0)
	return _ok("heading %.0f deg" % sv.heading_deg)


func _route_jump(cps: Array, number: int) -> Dictionary:
	var sv := ensure_sea()
	for c in cps:
		if int(c["id"]) == number:
			sv.place(float(c["x_km"]), float(c["y_km"]), float(c["heading_deg"]))
			state.t_seconds = roundi(float(c["t_days"]) * 86400.0)
			state.clock.set_location("sea")
			var smp: Dictionary = sv.ocean.sample(sv.x_km, sv.y_km, float(c["t_days"]))
			return _ok("DEBUG JUMP to %d %s: ship and clock placed (time still runs at the fixed rate).\n%s" % [
					number, c["name"], _sample_text(smp)])
	return _fail("no checkpoint %d (1..%d)" % [number, cps.size()])
