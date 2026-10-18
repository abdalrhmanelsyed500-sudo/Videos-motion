extends RefCounted
## Sprite selection and sea scale for the H2D-0 ship. Python twin: tools/h2d/ship_sprite_logic.py
## (shared cases in tests/fixtures/ship_sprite_cases.json). Heading is compass degrees clockwise from north; wind is the
## direction it blows FROM (the SeaState convention).
const HEADINGS := 16
const TRIMS_DEG: Array[int] = [-80, -45, 0, 45, 80]
## H2D-0 sea scale (provisional H2D0-3): 1 scene metre stands for 10 world metres.
const WORLD_M_PER_SCENE_M := 10.0
const KN_TO_MS := 0.514444
const GAME_S_PER_REAL_S := 96.0


static func wrap180(a: float) -> float:
	return fposmod(a + 180.0, 360.0) - 180.0


static func heading_frame(heading_deg: float, n: int = HEADINGS) -> int:
	return int(floorf(fposmod(heading_deg, 360.0) / (360.0 / float(n)) + 0.5)) % n


## Row of the sail sheet: the boom is eased to the lee side, further out the more the wind is behind the ship.
static func trim_row(heading_deg: float, wind_from_deg: float) -> int:
	var rel := wrap180(wind_from_deg - heading_deg)  # +90 = wind on the starboard beam
	var a := absf(rel)
	var mag := 0
	if a >= 110.0:
		mag = 2
	elif a >= 50.0:
		mag = 1
	if mag == 0:
		return 2
	if rel > 0.0:  # wind from starboard: boom to port (negative trim)
		return 1 if mag == 1 else 0
	return 3 if mag == 1 else 4


## Same as trim_row, but a boom that is already out stays out until the wind angle is `margin` degrees past the switch
## point, so a heading that hovers on 50 or 110 degrees does not flick the sail between two drawings (H2D-0.3).
static func trim_row_sticky(heading_deg: float, wind_from_deg: float, prev_row: int, margin: float = 6.0) -> int:
	var rel := wrap180(wind_from_deg - heading_deg)
	var a := absf(rel)
	var mag := 0
	if prev_row == 0 or prev_row == 4:
		mag = 2
	elif prev_row == 1 or prev_row == 3:
		mag = 1
	if mag == 0 and a >= 50.0 + margin:
		mag = 1
	if mag == 1 and a >= 110.0 + margin:
		mag = 2
	if mag == 2 and a < 110.0 - margin:
		mag = 1
	if mag == 1 and a < 50.0 - margin:
		mag = 0
	if mag == 0:
		return 2
	if rel > 0.0:
		return 1 if mag == 1 else 0
	return 3 if mag == 1 else 4


## Scene metres per real second for a ship speed in knots (world metres per real second divided by the sea scale).
static func scene_speed_ms(speed_kn: float) -> float:
	return speed_kn * KN_TO_MS * GAME_S_PER_REAL_S / WORLD_M_PER_SCENE_M
