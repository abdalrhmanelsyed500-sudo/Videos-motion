extends RefCounted
## The ONE world clock (patch T1). Sea and shore share it; there is no second scale and no player acceleration.
## Every time-dependent system (rations, thirst, fatigue, spoilage, weather, events, repairs, bells) must
## consume the game seconds that tick() returns. While any pause reason is held tick() returns 0, so nothing
## can advance while time is stopped.
## Pause reasons are a SET: "report" (Morning Report), "planning" (plan/provision screens), "menu".
## Duplicates are idempotent and time runs again only when the set is empty.
## set_location() is bookkeeping only: it never changes the rate and never jumps.
## Python twin: tools/data_tools/voyage_clock.py (WorldClock); both run tests/fixtures/clock_scenarios.json.
const DEFAULT_MINUTES_PER_DAY := 15.0  # PROVISIONAL (decision T1); must equal tuning time.real_minutes_per_game_day
const SECONDS_PER_DAY := 86400.0

var minutes_per_day: float = DEFAULT_MINUTES_PER_DAY
var t: float = 0.0  ## game seconds since the start of day 1, 00:00
var where: String = "sea"
var _pauses: Dictionary = {}


func _init(p_minutes_per_day: float = DEFAULT_MINUTES_PER_DAY, p_t: float = 0.0) -> void:
	minutes_per_day = p_minutes_per_day
	t = p_t


func pause(reason: String) -> void:
	_pauses[reason] = true


func resume(reason: String) -> void:
	_pauses.erase(reason)


func is_paused() -> bool:
	return not _pauses.is_empty()


func pause_reasons() -> PackedStringArray:
	var out := PackedStringArray(_pauses.keys())
	out.sort()
	return out


func set_location(p_where: String) -> void:
	where = p_where


## Game seconds that pass per real second (96 at 15 min/day).
func game_seconds_per_real_second() -> float:
	return SECONDS_PER_DAY / (minutes_per_day * 60.0)


## Advances the clock by a real-time delta and returns the GAME seconds that passed (0 while paused or for dt <= 0).
func tick(real_dt: float) -> float:
	if is_paused() or real_dt <= 0.0:
		return 0.0
	var dt := real_dt * game_seconds_per_real_second()
	t += dt
	return dt


func hour() -> float:
	return fposmod(t / 3600.0, 24.0)


func day() -> int:
	return int(floor(t / SECONDS_PER_DAY)) + 1
