# gdlint: disable=max-line-length
extends Control
## CP-2 Release B: the fish-storage panel (E at the barrels). Draws the model from fish_storage.gd: one row per species in the hold with
## its own picture, name, quantity and weight, then the total quantity, the capacity and the space that is left, and the close hint.
## Zero counts are never listed. The host calls refresh() with a new model whenever the hold changes (catch, unload, sale) so an open
## panel is always current. Pure drawing, no input: the host closes it (E, Esc, Space, Enter).
## NOT YET RUN ON THE USER'S PC.
const FishArt := preload("res://h2d/fish_art.gd")

const GOLD := Color(1.0, 0.82, 0.30)
const CREAM := Color(0.96, 0.92, 0.80)
const PANEL := Color(0.09, 0.07, 0.05, 0.95)
const EDGE := Color(0.62, 0.45, 0.22)

var model: Dictionary = {"rows": [], "total_n": 0, "total_kg": 0.0, "capacity": 40.0, "remaining": 40.0, "empty": true}
var is_shown := false
var title := "FISH BARRELS"
var close_hint := "E / Esc: close"
var font: Font = null


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	font = ThemeDB.fallback_font
	visible = false


func open(m: Dictionary) -> void:
	model = m
	is_shown = true
	visible = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	queue_redraw()


func refresh(m: Dictionary) -> void:
	model = m
	queue_redraw()


func close() -> void:
	is_shown = false
	visible = false
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _txt(text: String, pos: Vector2, fsize: int, col: Color, align: int = HORIZONTAL_ALIGNMENT_LEFT, width: float = -1.0) -> void:
	if font == null:
		return
	draw_string(font, pos + Vector2(2, 2), text, align, width, fsize, Color(0, 0, 0, 0.7))
	draw_string(font, pos, text, align, width, fsize, col)


func _draw() -> void:
	if not is_shown:
		return
	var k := size.y / 876.0
	var rows: Array = model["rows"]
	var shown := mini(rows.size(), 8)
	var rh := (60.0 if rows.size() <= 6 else 46.0) * k
	var body := maxf(float(shown), 1.0) * rh
	var w := 660.0 * k
	var h := 250.0 * k + body
	var r := Rect2((size.x - w) * 0.5, maxf((size.y - h) * 0.5, 12.0 * k), w, h)
	draw_rect(Rect2(0, 0, size.x, size.y), Color(0, 0, 0, 0.45))
	draw_rect(Rect2(r.position + Vector2(5, 6), r.size), Color(0, 0, 0, 0.4))
	draw_rect(r, PANEL)
	draw_rect(r, EDGE, false, 3.0)
	_txt(title, Vector2(r.position.x + 28.0 * k, r.position.y + 48.0 * k), int(roundf(34.0 * k)), GOLD)
	var y := r.position.y + 72.0 * k
	draw_rect(Rect2(r.position.x + 24.0 * k, y, w - 48.0 * k, 2.0), EDGE)
	y += 6.0 * k
	if bool(model["empty"]):
		_txt("The barrels are empty.", Vector2(r.position.x + 28.0 * k, y + 38.0 * k), int(roundf(26.0 * k)), CREAM)
		_txt("Cast the net at the winch (F), or fish from the helm.", Vector2(r.position.x + 28.0 * k, y + 72.0 * k), int(roundf(19.0 * k)), Color(0.80, 0.76, 0.66))
	for i in shown:
		var d: Dictionary = rows[i]
		var tex := FishArt.texture(str(d["icon"]))
		var iw := (rh - 8.0 * k) * 2.0
		var icon := Rect2(r.position.x + 28.0 * k, y + 4.0 * k, iw, iw * 0.5)
		if tex != null:
			draw_texture_rect(tex, icon, false)
		else:
			draw_rect(Rect2(icon.position + Vector2(0, icon.size.y * 0.25), Vector2(icon.size.x * 0.7, icon.size.y * 0.5)), Color(0.7, 0.8, 0.9))
		var fs := int(roundf((26.0 if rows.size() <= 6 else 21.0) * k))
		var base := y + rh * 0.62
		_txt(str(d["name"]), Vector2(icon.end.x + 16.0 * k, base), fs, CREAM)
		_txt("x %d" % int(d["count"]), Vector2(r.end.x - 250.0 * k, base), fs, GOLD, HORIZONTAL_ALIGNMENT_RIGHT, 90.0 * k)
		_txt("%.1f kg" % float(d["kg"]), Vector2(r.end.x - 150.0 * k, base), fs, CREAM, HORIZONTAL_ALIGNMENT_RIGHT, 100.0 * k)
		_txt("fresh %d%%" % int(d["fresh"]), Vector2(r.end.x - 28.0 * k, base), int(roundf(17.0 * k)), Color(0.72, 0.84, 0.72), HORIZONTAL_ALIGNMENT_RIGHT)
		y += rh
	if rows.size() > shown:
		_txt("... and %d more kinds" % (rows.size() - shown), Vector2(r.position.x + 28.0 * k, y + 24.0 * k), int(roundf(19.0 * k)), Color(0.80, 0.76, 0.66))
	if bool(model["empty"]):
		y += rh
	y += 6.0 * k
	draw_rect(Rect2(r.position.x + 24.0 * k, y, w - 48.0 * k, 2.0), EDGE)
	_txt("Total  %d fish" % int(model["total_n"]), Vector2(r.position.x + 28.0 * k, y + 40.0 * k), int(roundf(28.0 * k)), CREAM)
	_txt("%.1f kg" % float(model["total_kg"]), Vector2(r.end.x - 28.0 * k, y + 40.0 * k), int(roundf(28.0 * k)), CREAM, HORIZONTAL_ALIGNMENT_RIGHT)
	var cap := maxf(float(model["capacity"]), 1.0)
	var frac := clampf(float(model["total_kg"]) / cap, 0.0, 1.0)
	var bar := Rect2(r.position.x + 28.0 * k, y + 56.0 * k, w - 56.0 * k, 24.0 * k)
	draw_rect(bar, Color(0.06, 0.05, 0.04))
	var bc := Color(0.35, 0.80, 0.45) if frac < 0.7 else (Color(1.0, 0.70, 0.25) if frac < 0.95 else Color(1.0, 0.36, 0.30))
	draw_rect(Rect2(bar.position + Vector2(2, 2), Vector2((bar.size.x - 4.0) * frac, bar.size.y - 4.0)), bc)
	draw_rect(bar, EDGE, false, 2.0)
	_txt("Capacity %.0f kg   |   free %.1f kg" % [cap, float(model["remaining"])], Vector2(r.position.x + 28.0 * k, y + 108.0 * k), int(roundf(21.0 * k)), Color(0.88, 0.84, 0.72))
	_txt(close_hint, Vector2(r.end.x - 28.0 * k, y + 108.0 * k), int(roundf(21.0 * k)), GOLD, HORIZONTAL_ALIGNMENT_RIGHT)
