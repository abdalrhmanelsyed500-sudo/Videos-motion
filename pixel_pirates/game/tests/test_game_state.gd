extends RefCounted
## GameState (A7): serialisation matches the save_state schema; clock and inventory helpers.
const GameState := preload("res://core/game_state.gd")
const SaveIO := preload("res://core/save_io.gd")


func run(t: Object) -> void:
	var reg: Node = load("res://core/registry.gd").new()
	reg.load_all()
	var s: RefCounted = GameState.new()
	t.check(SaveIO.validate_state(s.to_dict(), reg).is_empty(), "a fresh state validates against save_state")
	t.check(s.clock_text() == "Day 1, 00:00", "clock starts at Day 1, 00:00")
	s.set_clock(2, 13.25)
	t.check(s.clock_text() == "Day 2, 13:15", "set_clock 2 13.25 -> Day 2, 13:15")
	s.add_hours(11.0)
	t.check(s.clock_text() == "Day 3, 00:15", "add_hours rolls over midnight")
	s.add_hours(-1000.0)
	t.check(s.t_seconds == 0, "the clock never goes below 0")
	t.check(s.add_item("item_rope", 4) == 4 and s.add_item("item_rope", -9) == 0, "add_item floors at 0")
	t.check(not s.inventory.has("item_rope"), "zero entries are removed")
	s.add_item("item_hardtack", 12)
	s.overrides = {"hunger_rate": 0.5}
	s.world_seed = "18446744073709551615"
	s.x_m = 1234567.5
	var d: Dictionary = s.to_dict()
	var s2: RefCounted = GameState.from_dict(JSON.parse_string(JSON.stringify(d)))
	t.check(s2.to_dict() == d, "to_dict / JSON / from_dict round trip is lossless")
	t.check(SaveIO.validate_state(d, reg).is_empty(), "the filled state validates")
	_world_clock(t, reg)
	reg.free()


## Patch T1: the state owns the one world clock; the save format is unchanged.
func _world_clock(t: Object, reg: Node) -> void:
	var s: RefCounted = GameState.new()
	t.check(s.to_dict()["clock"].keys() == ["t_seconds"], "the save still has exactly one clock field (format unchanged)")
	t.check(SaveIO.SAVE_VERSION == 1, "SAVE_VERSION is still 1 (old saves load without migration)")
	var dt: float = s.tick(37.5)
	t.check(is_equal_approx(dt, 3600.0) and s.clock_text() == "Day 1, 01:00", "tick(37.5 real s) = one game hour")
	s.clock.pause("report")
	t.check(s.tick(60.0) == 0.0 and s.t_seconds == 3600, "a paused state does not advance")
	t.check(s.playtime_s == 97, "playtime counts real seconds, paused or not (97 s)")
	s.clock.resume("report")
	s.t_seconds = 7200
	t.check(s.clock.t == 7200.0 and s.hour_of_day() == 2.0, "writing t_seconds writes the clock")
	s.tick(0.5)
	t.check(s.t_seconds == 7248, "the saved integer is the floor of the clock")
	var d: Dictionary = s.to_dict()
	var s2: RefCounted = GameState.from_dict(JSON.parse_string(JSON.stringify(d)))
	t.check(s2.t_seconds == 7248 and s2.to_dict() == d, "save round trip keeps the clock")
	t.check(SaveIO.validate_state(d, reg).is_empty(), "the ticked state validates")
	var old := {"clock": {"t_seconds": 123456}}
	var s3: RefCounted = GameState.from_dict(old)
	t.check(s3.t_seconds == 123456 and s3.day() == 2, "an older save (integer game seconds) loads as is")
