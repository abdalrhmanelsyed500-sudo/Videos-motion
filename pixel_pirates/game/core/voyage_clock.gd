extends RefCounted
## Time arithmetic (B2, revised by patch T1): watches, bells, Morning Report cadence, voyage bands, day/night
## bands and the daylight curve. Pure static functions with no state. Python twin: tools/data_tools/voyage_clock.py.
## Both run tests/fixtures/clock_cases.json. The stateful clock is world_clock.gd.
## Decision T1: one clock, 1 game day = 15 real minutes (tuning time.real_minutes_per_game_day), at sea and ashore.
## Ship's time: 24 h = 6 watches of crew.watch_length_hours (4). Bells strike every half hour; eight bells end a watch.
const WATCH_NAMES: Array[String] = ["Middle", "Morning", "Forenoon", "Afternoon", "Dog", "First"]
const BAND_NAMES: Array[String] = ["dawn", "morning", "day", "sunset", "evening", "night"]
## Band start hours (tuning time.*_start_hour). PROVISIONAL, subject to visual testing.
const DEFAULT_STARTS: Array[float] = [5.0, 7.0, 10.0, 17.0, 19.0, 20.0]
const DEFAULT_REPORT_HOUR := 8.0


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


static func days_to_real_minutes(days: float, minutes_per_day: float) -> float:
	return days * minutes_per_day


## Morning Reports due while the clock runs from one absolute hour to another (boundary: from < report hour <= to).
static func reports_between(abs_hour_from: float, abs_hour_to: float, report_hour: float = DEFAULT_REPORT_HOUR) -> int:
	return int(floor((abs_hour_to - report_hour) / 24.0) - floor((abs_hour_from - report_hour) / 24.0))


## Voyage length band, in real minutes.
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


## Hard label for HUD text and band-triggered events (night wraps midnight).
## Lighting must use daylight()/band_weights(), never this label.
static func band_of_hour(hour: float, starts: Array = DEFAULT_STARTS) -> String:
	var h := fposmod(hour, 24.0)
	if h < float(starts[0]) or h >= float(starts[5]):
		return "night"
	for i in range(5):
		if h < float(starts[i + 1]):
			return BAND_NAMES[i]
	return "night"


static func _smooth(x: float) -> float:
	var c := clampf(x, 0.0, 1.0)
	return c * c * (3.0 - 2.0 * c)


## Continuous daylight level 0..1 (the lighting driver): smoothstep between keyframes at the band
## boundaries, wraps at midnight.
static func daylight(hour: float, starts: Array, night_floor: float, dawn_end: float, sunset_end: float) -> float:
	var h := fposmod(hour, 24.0)
	var hs: Array[float] = [0.0]
	for s in starts:
		hs.append(float(s))
	hs.append(24.0)
	var vs: Array[float] = [night_floor, night_floor, dawn_end, 1.0, 1.0, sunset_end, night_floor, night_floor]
	for i in range(hs.size() - 1):
		if h >= hs[i] and h < hs[i + 1]:
			return vs[i] + (vs[i + 1] - vs[i]) * _smooth((h - hs[i]) / (hs[i + 1] - hs[i]))
	return night_floor


## Continuous mix of the six bands (sums to 1) for grading and ambience: smoothstep between band
## MIDPOINTS, so the look never switches abruptly at a boundary. Hard labels stay in band_of_hour().
static func band_weights(hour: float, starts: Array = DEFAULT_STARTS) -> Dictionary:
	var s: Array[float] = []
	for v in starts:
		s.append(float(v))
	var mids: Array[float] = [
		(s[0] + s[1]) / 2.0, (s[1] + s[2]) / 2.0, (s[2] + s[3]) / 2.0,
		(s[3] + s[4]) / 2.0, (s[4] + s[5]) / 2.0, (s[5] + s[0] + 24.0) / 2.0,
	]
	var pts: Array[float] = [mids[5] - 24.0]
	pts.append_array(mids)
	pts.append(mids[0] + 24.0)
	var names: Array[String] = ["night", "dawn", "morning", "day", "sunset", "evening", "night", "dawn"]
	var h := fposmod(hour, 24.0)
	if h < pts[0]:
		h += 24.0
	var out := {}
	for n in BAND_NAMES:
		out[n] = 0.0
	for i in range(pts.size() - 1):
		if h >= pts[i] and h < pts[i + 1]:
			var w := _smooth((h - pts[i]) / (pts[i + 1] - pts[i]))
			out[names[i]] += 1.0 - w
			out[names[i + 1]] += w
			return out
	out["night"] = 1.0
	return out


## Used by the fixture test: call a function by name with an argument array (JSON numbers arrive as floats).
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
		"days_to_real_minutes":
			return days_to_real_minutes(float(a[0]), float(a[1]))
		"reports_between":
			return reports_between(float(a[0]), float(a[1]), float(a[2]))
		"band_of":
			return band_of(float(a[0]), float(a[1]), float(a[2]), float(a[3]), float(a[4]), float(a[5]))
		"band_of_hour":
			return band_of_hour(float(a[0]), a[1])
		"daylight":
			return daylight(float(a[0]), a[1], float(a[2]), float(a[3]), float(a[4]))
		"band_weights":
			return band_weights(float(a[0]), a[1])
	return null
