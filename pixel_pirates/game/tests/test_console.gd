extends RefCounted
## Debug console commands (A7), run headless against the real data and the fixture islands.
const Console := preload("res://core/console_commands.gd")
const IslandMap := preload("res://core/island_map.gd")
const SaveIO := preload("res://core/save_io.gd")
const SAVE_BASE := "user://saves/a7_console_test.json"


func _cleanup() -> void:
	for suffix in ["", ".bak", ".tmp"]:
		if FileAccess.file_exists(SAVE_BASE + suffix):
			DirAccess.remove_absolute(SAVE_BASE + suffix)


func _ok(t: Object, c: RefCounted, line: String, must_contain: String = "") -> Dictionary:
	var r: Dictionary = c.execute(line)
	var msg := "'%s' ok and contains '%s' (got: %s)" % [line, must_contain, r["text"]]
	t.check(r["ok"] and (must_contain == "" or must_contain in str(r["text"])), msg)   # String.contains("") is false in Godot 4
	return r


func _bad(t: Object, c: RefCounted, line: String, must_contain: String = "") -> void:
	var r: Dictionary = c.execute(line)
	var msg := "'%s' fails with '%s' (got: %s)" % [line, must_contain, r["text"]]
	t.check(not r["ok"] and (must_contain == "" or must_contain in str(r["text"])), msg)


func run(t: Object) -> void:
	_cleanup()
	var reg: Node = load("res://core/registry.gd").new()
	reg.load_all()
	var c: RefCounted = Console.new(reg)
	_tokenizer(t)
	_dispatch(t, c)
	_data_and_tuning(t, c)
	_inventory_time_seed(t, c, reg)
	_teleport(t, c)
	_save_load(t, c)
	_islands(t, c)
	_ocean_and_route(t, c)
	t.check(SaveIO.validate_state(c.state.to_dict(), reg).is_empty(), "state is still valid after all commands")
	_cleanup()
	reg.free()


func _tokenizer(t: Object) -> void:
	t.check(Console.tokenize("give item_rope 3") == PackedStringArray(["give", "item_rope", "3"]), "tokenize plain words")
	var quoted := Console.tokenize("echo \"hello big world\" x")
	t.check(quoted == PackedStringArray(["echo", "hello big world", "x"]), "double quotes")
	t.check(Console.tokenize("echo 'a b'  c") == PackedStringArray(["echo", "a b", "c"]), "single quotes, extra spaces")
	t.check(Console.tokenize("a \"\" b") == PackedStringArray(["a", "", "b"]), "empty quoted token is kept")
	t.check(Console.tokenize("   ").is_empty(), "blank line has no tokens")


func _dispatch(t: Object, c: RefCounted) -> void:
	_bad(t, c, "frobnicate", "unknown command")
	_ok(t, c, "")
	_ok(t, c, "help", "tuning")
	_ok(t, c, "help tp", "tp island")
	_bad(t, c, "help nothing", "no such command")
	_ok(t, c, "ECHO Hello", "Hello")
	var cl: Dictionary = c.execute("clear")
	t.check(cl.get("clear", false), "clear sets the clear flag")
	var comp: PackedStringArray = c.complete("t")
	t.check(comp.has("tp") and comp.has("time") and comp.has("tuning"), "Tab completion for 't'")
	t.check(c.complete("zzz").is_empty(), "no completion for unknown prefix")


func _data_and_tuning(t: Object, c: RefCounted) -> void:
	var n_items: int = (c.get("data") as Object).call("count", "item")   # the item table grew in B4 (9 trade items): compare with the real count
	_ok(t, c, "data counts", "item: %d" % n_items)
	_ok(t, c, "data list difficulty_mode", "mode_hardcore")
	_ok(t, c, "data show item item_hardtack", "weight_kg")
	_bad(t, c, "data show item item_nope")
	_bad(t, c, "data list nokind", "kinds:")
	_ok(t, c, "check", "0 problems")
	_ok(t, c, "tuning food.need_kcal_per_man_day", "3200")
	_ok(t, c, "tuning food.need_kcal_per_man_day", "PROVISIONAL")
	_ok(t, c, "mode mode_hardcore")
	_ok(t, c, "tuning food.need_kcal_per_man_day", "4000")
	_ok(t, c, "mode override hunger_rate 1")
	_ok(t, c, "tuning food.need_kcal_per_man_day", "3200")
	_bad(t, c, "mode override hunger_rate 9", "between 0 and 3")
	_bad(t, c, "mode override bogus_rate 1")
	_ok(t, c, "mode clear")
	_ok(t, c, "tuning food.need_kcal_per_man_day", "4000")
	_bad(t, c, "mode mode_nope", "unknown mode")
	_bad(t, c, "tuning no.such.key", "unknown tuning key")
	_ok(t, c, "tuning list water.", "water.need_l_per_man_day_min")
	_ok(t, c, "mode mode_normal")


## Patch T1: the world clock through the console (watch line, real-time tick, pause reasons, debug jumps).
func _time_commands(t: Object, c: RefCounted) -> void:
	_ok(t, c, "time set 1 0")
	_ok(t, c, "time watch", "band night, daylight 0.04")
	_ok(t, c, "time watch", "1 day = 15 real min (1 game hour = 37.5 s)")
	_ok(t, c, "time watch", "paused: no")
	_ok(t, c, "time tick 37.5", "3600.0 game s")
	t.check(c.state.clock_text() == "Day 1, 01:00", "37.5 real seconds = one game hour")
	_ok(t, c, "time pause report", "paused by report")
	_ok(t, c, "time tick 100", "0.0 game s")
	t.check(c.state.clock_text() == "Day 1, 01:00", "a paused clock does not move")
	_ok(t, c, "time watch", "paused: report")
	_ok(t, c, "time pause planning", "paused by planning, report")
	_ok(t, c, "time resume report", "paused by planning")
	_ok(t, c, "time resume planning", "time runs")
	_ok(t, c, "time tick 450", "43200.0 game s")
	t.check(c.state.clock_text() == "Day 1, 13:00", "450 real seconds = 12 game hours")
	_ok(t, c, "time watch", "band day, daylight 1.00")
	_bad(t, c, "time tick abc", "usage")
	_bad(t, c, "time tick -5", "between")
	_bad(t, c, "time pause BAD!", "usage")
	_bad(t, c, "time live maybe", "usage")
	_ok(t, c, "time live on", "live clock ON")
	var hud: String = c.hud_text()
	t.check(c.live and "| day |" in hud and "daylight 1.00" in hud, "live mode is on; the HUD line shows band and light")
	_ok(t, c, "time pause menu")
	t.check("PAUSED: menu" in c.hud_text(), "the HUD line shows a pause")
	_ok(t, c, "time resume menu")
	_ok(t, c, "time live off", "live clock OFF")
	t.check(not c.live, "live mode is off again")
	_ok(t, c, "time set 1 0")


func _inventory_time_seed(t: Object, c: RefCounted, reg: Node) -> void:
	_ok(t, c, "give item_rope 3", "item_rope: 3")
	t.check(c.state.inventory["item_rope"] == 3, "inventory holds 3 rope")
	_ok(t, c, "give item_rope -5", "item_rope: 0")
	t.check(not c.state.inventory.has("item_rope"), "removing more than owned removes the entry, never negative")
	_bad(t, c, "give item_nothing 2", "unknown item")
	_bad(t, c, "give item_rope abc", "whole number")
	_ok(t, c, "give item_hardtack 10")
	var kg := float(reg.record("item", "item_hardtack")["weight_kg"]) * 10.0
	_ok(t, c, "inv", "total cargo weight: %.1f kg" % kg)
	_ok(t, c, "time set 3 14.5", "Day 3, 14:30")
	_ok(t, c, "time watch", "Afternoon watch, last bell 5")
	_ok(t, c, "time add 10", "Day 4, 00:30")
	_ok(t, c, "time add -100000", "Day 1, 00:00")
	_bad(t, c, "time add abc", "usage")
	_time_commands(t, c)
	_ok(t, c, "seed world 18446744073709551615", "18446744073709551615")
	_bad(t, c, "seed world abc", "usage")
	_ok(t, c, "seed weather 99")
	t.check(c.state.world_seed == "18446744073709551615" and c.state.weather_seed == "99", "seeds stored as strings")


func _teleport(t: Object, c: RefCounted) -> void:
	var m: RefCounted = IslandMap.from_file("res://tests/fixtures/islands/maps/isl_901.map.json")
	var l: Dictionary = m.landings[0]
	var want: Vector2 = m.cell_to_local(int(l["x"]), int(l["y"]))
	_ok(t, c, "time set 2 9.5", "Day 2, 09:30")
	_ok(t, c, "tp island isl_901", "teleported")
	t.check(c.state.at_island == "isl_901", "at_island set")
	var kept: bool = c.state.clock_text() == "Day 2, 09:30" and c.state.clock.where == "island"
	t.check(kept, "landfall does not touch the clock")
	var at_landing: bool = is_equal_approx(c.state.x_m, want.x) and is_equal_approx(c.state.y_m, want.y)
	t.check(at_landing, "position equals the landing cell in metres")
	var hook: String = str(m.pois_of_kind("hook")[0]["slot"])
	_ok(t, c, "tp isl_901 " + hook, hook)
	_bad(t, c, "tp isl_901 nothing_here", "try landing")
	_bad(t, c, "tp island isl_999", "no usable baked map")
	_bad(t, c, "tp island", "usage")
	_ok(t, c, "tp xy 100 -200.5", "open sea")
	var at_xy: bool = is_equal_approx(c.state.x_m, 100.0) and is_equal_approx(c.state.y_m, -200.5)
	t.check(c.state.at_island == "" and at_xy, "tp xy sets open-sea position")
	kept = c.state.clock_text() == "Day 2, 09:30" and c.state.clock.where == "sea"
	t.check(kept, "leaving the island does not touch the clock")
	_bad(t, c, "tp xy 1", "usage")


func _save_load(t: Object, c: RefCounted) -> void:
	_ok(t, c, "give item_rope 7")
	_ok(t, c, "time set 5 6")
	_ok(t, c, "save a7_console_test", "saved")
	_ok(t, c, "give item_rope 100")
	_ok(t, c, "time set 9 9")
	_ok(t, c, "load a7_console_test", "Day 5, 06:00")
	t.check(c.state.inventory["item_rope"] == 7, "load restored the inventory")
	_bad(t, c, "save ../evil", "letters, digits")
	_bad(t, c, "load no_such_save")
	c.state.inventory["item_not_real"] = 1
	_bad(t, c, "save a7_console_test", "not saved")
	c.state.inventory.erase("item_not_real")


func _islands(t: Object, c: RefCounted) -> void:
	_ok(t, c, "island list", "isl_901")
	_ok(t, c, "island info isl_901", "explore time")
	_bad(t, c, "island info isl_nope", "unknown island")
	_bad(t, c, "quality", "not available")
	_bad(t, c, "log", "not available")


func _ocean_and_route(t: Object, c: RefCounted) -> void:
	_ok(t, c, "route", "Kettle dawn squall")
	_ok(t, c, "route 5", "Herald Swell")
	t.check(c.state.t_seconds == roundi(12.5 * 86400.0), "route 5 placed the clock at day 12.5 (debug jump)")
	_ok(t, c, "route status", "reg_grey_marches")
	_ok(t, c, "route heading 45", "45")
	_ok(t, c, "route jump 7", "Ice Edge")
	_ok(t, c, "route 1", "reg_kettle_seas")
	var before: float = c.state.clock.t
	c.state.clock.pause("report")
	var gs: float = c.state.tick(10.0)
	t.check(gs == 0.0 and c.state.clock.t == before, "a paused clock does not move the ship's world either")
	c.state.clock.resume("report")
	_bad(t, c, "route 99", "no checkpoint")
	_bad(t, c, "route heading", "usage")
	_ok(t, c, "ocean 7000 2650 0.25", "reg_kettle_seas")
	_ok(t, c, "ocean 5600 520", "reg_grey_marches")
	_bad(t, c, "ocean 99999 1", "outside the world")
	_bad(t, c, "ocean 5", "usage")
