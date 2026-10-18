extends RefCounted
## Minimal mutable game state (A7). The debug console edits it; the save format (A5 save_state schema) is its
## serialised form. Later modules (J) grow it; keep every field representable in `to_dict()`.
const WorldClock := preload("res://core/world_clock.gd")
const SECONDS_PER_DAY := 86400

## The one world clock (patch T1). `t_seconds` stays the saved integer field (save format unchanged, SAVE_VERSION 1).
var clock: RefCounted = WorldClock.new()
var profile := "Debug"
var difficulty := "mode_normal"
var overrides: Dictionary = {}
var playtime_s := 0
var t_seconds: int:
	get:
		return int(floor(clock.t))
	set(value):
		clock.t = float(value)
var world_seed := "1"
var weather_seed := "2"
var x_m := 0.0
var y_m := 0.0
var at_island := ""
var inventory: Dictionary = {}
var _playtime_frac := 0.0


func to_dict() -> Dictionary:
	return {
		"meta": {"profile": profile, "difficulty": difficulty, "overrides": overrides.duplicate(), "playtime_s": playtime_s},
		"clock": {"t_seconds": t_seconds},
		"rng": {"world_seed": world_seed, "weather_seed": weather_seed},
		"player": {"x_m": x_m, "y_m": y_m, "at_island": at_island},
		"inventory": inventory.duplicate(),
	}


static func from_dict(d: Dictionary) -> RefCounted:
	var s := new()
	s.apply_dict(d)
	return s


## Overwrites this state with a saved dictionary (the console's `load` keeps the same object alive).
func apply_dict(d: Dictionary) -> void:
	var meta: Dictionary = d.get("meta", {})
	profile = str(meta.get("profile", "Debug"))
	difficulty = str(meta.get("difficulty", "mode_normal"))
	overrides = (meta.get("overrides", {}) as Dictionary).duplicate()
	playtime_s = int(meta.get("playtime_s", 0))
	t_seconds = int((d.get("clock", {}) as Dictionary).get("t_seconds", 0))
	var rng: Dictionary = d.get("rng", {})
	world_seed = str(rng.get("world_seed", "1"))
	weather_seed = str(rng.get("weather_seed", "2"))
	var pl: Dictionary = d.get("player", {})
	x_m = float(pl.get("x_m", 0.0))
	y_m = float(pl.get("y_m", 0.0))
	at_island = str(pl.get("at_island", ""))
	inventory.clear()
	var inv: Dictionary = d.get("inventory", {})
	for k in inv.keys():
		inventory[k] = int(inv[k])


## Advances the world by a real-time delta. Returns the game seconds to feed every time-dependent system
## (0 while paused).
## playtime_s counts real play time, paused or not.
func tick(real_dt: float) -> float:
	if real_dt > 0.0:
		_playtime_frac += real_dt
		var whole := int(floor(_playtime_frac))
		playtime_s += whole
		_playtime_frac -= whole
	return clock.tick(real_dt)


func day() -> int:
	return floori(float(t_seconds) / SECONDS_PER_DAY) + 1


func hour_of_day() -> float:
	return float(t_seconds % SECONDS_PER_DAY) / 3600.0


func clock_text() -> String:
	var h := int(hour_of_day())
	var m := int((hour_of_day() - h) * 60.0)
	return "Day %d, %02d:%02d" % [day(), h, m]


## Debug only: jumping the clock skips Morning Reports and every event in between. Gameplay must use tick().
func add_hours(hours: float) -> void:
	t_seconds = maxi(0, t_seconds + roundi(hours * 3600.0))


func set_clock(p_day: int, p_hour: float) -> void:
	t_seconds = maxi(0, (p_day - 1) * SECONDS_PER_DAY + roundi(p_hour * 3600.0))


## n may be negative (take away). The count never goes below 0; a zero entry is removed.
func add_item(item_id: String, n: int) -> int:
	var now := maxi(0, int(inventory.get(item_id, 0)) + n)
	if now == 0:
		inventory.erase(item_id)
	else:
		inventory[item_id] = now
	return now
