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
	reg.free()
