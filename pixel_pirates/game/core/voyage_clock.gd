extends RefCounted
## Voyage clock (B2): watches, bells, the daily Morning Report, time scale and voyage bands.
## Pure static functions. Python twin: tools/data_tools/voyage_clock.py. Both run tests/fixtures/clock_cases.json.
## Ship's time: 24 h = 6 watches of crew.watch_length_hours (4). Bells strike every half hour; eight bells end a watch.
## The Morning Report is due at eight bells of the Morning watch (08:00 ship time).
const WATCH_NAMES: Array[String] = ["Middle", "Morning", "Forenoon", "Afternoon", "Dog", "First"]
const REPORT_HOUR := 8.0


static func watch_index(hour: float, watch_len: float = 4.0) -> int:
	return int(floor(fposmod(hour, 24.0) / watch_len))


static func watch_name(index: int) -> String:
	return WATCH_NAMES[posmod(index, WATCH_NAMES.size())]


## Bells struck at the most recent half-hour mark: 1..7 inside a watch, 8 at the watch change.
static func last_bell(hour: float, watch_len: float = 4.0) -> int:
	var k := int(floor(fposmod(hour, watch_len) / 0.5))
	return k if k > 0 else 8


static func hours_to_real_seconds(hours: float, minutes_per_day: float) -> float:
	return hours * minutes_per_day * 60.0 / 24.0


static func real_seconds_to_hours(seconds: float, minutes_per_day: float) -> float:
	return seconds * 24.0 / (minutes_per_day * 60.0)


## Game hours that pass while the player spends this many real minutes ashore.
static func ashore_game_hours(real_minutes: float, game_min_per_real_min: float) -> float:
	return real_minutes * game_min_per_real_min / 60.0


static func days_to_real_minutes(days: float, minutes_per_day: float) -> float:
	return days * minutes_per_day


## Morning Reports due while the clock runs from one absolute hour to another (boundary: from < 08:00 <= to).
static func reports_between(abs_hour_from: float, abs_hour_to: float) -> int:
	return int(floor((abs_hour_to - REPORT_HOUR) / 24.0) - floor((abs_hour_from - REPORT_HOUR) / 24.0))


static func band_of(
		minutes: float, hop_min: float, hop_max: float, passage_max: float, crossing_max: float, dead_max: float
) -> String:
	if minutes < hop_min:
		return "below"
	if minutes <= hop_max:
		return "hop"
	if minutes <= passage_max:
		return "passage"
	if minutes <= crossing_max:
		return "crossing"
	if minutes <= dead_max:
		return "dead"
	return "beyond"


## Used by the fixture test: call a function by name with an argument array.
static func call_case(fn: String, a: Array) -> Variant:
	match fn:
		"watch_index":
			return watch_index(float(a[0]), float(a[1]))
		"watch_name":
			return watch_name(int(a[0]))
		"last_bell":
			return last_bell(float(a[0]), float(a[1]))
		"hours_to_real_seconds":
			return hours_to_real_seconds(float(a[0]), float(a[1]))
		"real_seconds_to_hours":
			return real_seconds_to_hours(float(a[0]), float(a[1]))
		"ashore_game_hours":
			return ashore_game_hours(float(a[0]), float(a[1]))
		"days_to_real_minutes":
			return days_to_real_minutes(float(a[0]), float(a[1]))
		"reports_between":
			return reports_between(float(a[0]), float(a[1]))
		"band_of":
			return band_of(float(a[0]), float(a[1]), float(a[2]), float(a[3]), float(a[4]), float(a[5]))
	return null
