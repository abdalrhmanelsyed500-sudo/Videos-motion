extends Control
## The helm display, drawn the same way over the 3D and the 2D view: a compass ring (north up, like the world) with the
## ship's bow, the wind, the red no-go wedge (where the sails cannot draw), the green fast zone, a rudder bar and
## a speed bar that shows both the speed now and the speed the sails could give at this heading.
## Fed once per frame by h2d0.gd through set_state(); it only draws. NOT YET RUN IN GODOT.
const RADIUS := 66.0
const RING_COL := Color(0.96, 0.92, 0.80, 0.95)
const INK := Color(0.05, 0.08, 0.10, 0.85)
const WEDGE_COL := Color(0.90, 0.20, 0.16, 0.45)
const FAST_COL := Color(0.30, 0.80, 0.40, 0.40)
const BOW_COL := Color(1.0, 0.85, 0.25)
const WIND_COL := Color(0.55, 0.85, 1.0)
const WIDTH := 200.0
const HEIGHT := 232.0

var _s: Dictionary = {}


func _init() -> void:
	custom_minimum_size = Vector2(WIDTH, HEIGHT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func set_state(state: Dictionary) -> void:
	_s = state
	queue_redraw()


static func dir(deg: float) -> Vector2:
	var a := deg_to_rad(deg)
	return Vector2(sin(a), -cos(a))


func _wedge(c: Vector2, from_deg: float, to_deg: float, r: float, col: Color) -> void:
	var pts := PackedVector2Array([c])
	var n := 18
	for i in n + 1:
		pts.append(c + dir(lerpf(from_deg, to_deg, float(i) / float(n))) * r)
	draw_colored_polygon(pts, col)


## Text centred on `pos` (x) with its baseline at pos.y.
func _text(pos: Vector2, text: String, size: int, col: Color) -> void:
	var font := ThemeDB.fallback_font
	var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size).x
	var at := Vector2(pos.x - w * 0.5, pos.y)
	draw_string(font, at + Vector2(1.0, 1.0), text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size, INK)
	draw_string(font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, size, col)


func _draw() -> void:
	if _s.is_empty():
		return
	var c := Vector2(WIDTH * 0.5, 84.0)
	var heading: float = _s["heading"]
	var wind_from: float = _s["wind_from"]
	var no_go: float = _s["no_go"]
	var irons: bool = _s["in_irons"]
	draw_circle(c, RADIUS + 4.0, Color(0.05, 0.08, 0.10, 0.45))
	_wedge(c, wind_from - no_go, wind_from + no_go, RADIUS, WEDGE_COL)
	_wedge(c, wind_from + 80.0, wind_from + 140.0, RADIUS, FAST_COL)
	_wedge(c, wind_from - 140.0, wind_from - 80.0, RADIUS, FAST_COL)
	draw_arc(c, RADIUS, 0.0, TAU, 64, RING_COL, 2.0, true)
	for i in 4:
		var d := dir(float(i) * 90.0)
		draw_line(c + d * (RADIUS - 6.0), c + d * RADIUS, RING_COL, 2.0)
	_text(c + Vector2(0.0, -RADIUS - 6.0), "N", 13, RING_COL)
	# wind: an arrow on the rim pointing the way the wind blows (towards the centre)
	var wp := c + dir(wind_from) * (RADIUS + 1.0)
	var wd := dir(wind_from + 180.0)
	var side := Vector2(-wd.y, wd.x)
	var tail := wp - wd * 2.0
	draw_colored_polygon(PackedVector2Array([wp + wd * 20.0, tail + side * 8.0, tail - side * 8.0]), WIND_COL)
	draw_line(wp - wd * 2.0, wp - wd * 14.0, WIND_COL, 3.0)
	# the ship: a bow line and a small hull
	var col := Color(1.0, 0.30, 0.25) if irons else BOW_COL
	var bow := dir(heading)
	var bside := Vector2(-bow.y, bow.x)
	draw_line(c, c + bow * (RADIUS - 4.0), col, 3.0)
	var stern := c - bow * 12.0
	var hull := PackedVector2Array([c + bow * 20.0, stern + bside * 8.0, c - bow * 8.0, stern - bside * 8.0])
	draw_colored_polygon(hull, col)
	# rudder bar: the helm, left = port (A), right = starboard (D)
	var by := c.y + RADIUS + 18.0
	var half := 60.0
	draw_rect(Rect2(c.x - half, by - 4.0, half * 2.0, 8.0), Color(0.05, 0.08, 0.10, 0.6))
	draw_line(Vector2(c.x, by - 7.0), Vector2(c.x, by + 7.0), RING_COL, 2.0)
	var rud: float = _s["rudder"]
	draw_rect(Rect2(c.x + minf(0.0, rud * half), by - 3.0, absf(rud * half), 6.0), col)
	_text(Vector2(c.x - half - 8.0, by + 5.0), "A", 12, RING_COL)
	_text(Vector2(c.x + half + 8.0, by + 5.0), "D", 12, RING_COL)
	# speed bar: solid = speed now, tick = what the sails could give at this heading
	var sy := by + 18.0
	var vmax := maxf(float(_s["best_kn"]) * 1.1, 1.0)
	draw_rect(Rect2(c.x - half, sy - 4.0, half * 2.0, 8.0), Color(0.05, 0.08, 0.10, 0.6))
	var now_w: float = clampf(float(_s["speed_kn"]) / vmax, 0.0, 1.0) * half * 2.0
	draw_rect(Rect2(c.x - half, sy - 3.0, now_w, 6.0), col)
	var tx: float = c.x - half + clampf(float(_s["target_kn"]) / vmax, 0.0, 1.0) * half * 2.0
	draw_line(Vector2(tx, sy - 7.0), Vector2(tx, sy + 7.0), Color(1.0, 1.0, 1.0), 2.0)
	var line := "%03d deg   %.1f kn   %s" % [int(fposmod(heading, 360.0)), float(_s["speed_kn"]), _s["sail_name"]]
	_text(Vector2(c.x, sy + 24.0), line, 13, col)
