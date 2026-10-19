extends Control
## CP-1 interface of the starting loop, drawn directly on one Control (no scene tree of widgets): the top-right status card
## (purse, hold, crew, objective, nets), the toasts, the interaction prompt, and one modal panel at a time: dialogue, the fish
## market and the map (District / Waters). It only DRAWS what port_game.gd hands it (dictionaries); it holds no rules.
## NOT YET RUN IN GODOT.
const INK := Color(0.10, 0.07, 0.05, 0.94)
const INK2 := Color(0.17, 0.12, 0.08, 0.96)
const GOLD := Color(0.96, 0.78, 0.30)
const CREAM := Color(1.0, 0.95, 0.82)
const DIM := Color(0.74, 0.68, 0.56)
const GREEN := Color(0.50, 0.88, 0.42)
const RED := Color(1.0, 0.45, 0.35)
const WATER := Color(0.13, 0.30, 0.42)
const COASTS := {1: Color(0.84, 0.74, 0.52), 2: Color(0.62, 0.62, 0.36), 3: Color(0.48, 0.62, 0.32), 4: Color(0.27, 0.43, 0.24),
		5: Color(0.52, 0.50, 0.48), 6: Color(0.40, 0.38, 0.37), 7: Color(0.66, 0.52, 0.34), 8: Color(0.64, 0.60, 0.56),
		9: Color(0.36, 0.45, 0.35), 10: Color(0.55, 0.56, 0.36), 11: Color(0.45, 0.50, 0.30)}

var hud: Dictionary = {}
var panel: Dictionary = {}          # {kind: "", "dialogue", "market", "map"} + the data of that kind
var toasts: Array = []              # [{text, color, t}]
var big_note: Dictionary = {}       # the sale banner {text, sub, t}
var _font: Font
var _images: Dictionary = {}        # "district" / "waters" -> ImageTexture
var _t := 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_font = ThemeDB.fallback_font


func toast(text: String, color: Color = CREAM, seconds: float = 5.0) -> void:
	toasts.append({"text": text, "color": color, "t": seconds})
	while toasts.size() > 5:
		toasts.pop_front()


func note_big(text: String, sub: String, seconds: float = 5.5) -> void:
	big_note = {"text": text, "sub": sub, "t": seconds}


func _process(delta: float) -> void:
	_t += delta
	for tt in toasts:
		(tt as Dictionary)["t"] = float((tt as Dictionary)["t"]) - delta
	toasts = toasts.filter(func(q: Dictionary) -> bool: return float(q["t"]) > 0.0)
	if not big_note.is_empty():
		big_note["t"] = float(big_note["t"]) - delta
		if float(big_note["t"]) <= 0.0:
			big_note = {}
	queue_redraw()


# ---- helpers -----------------------------------------------------------------------------------------------------
func _txt(pos: Vector2, s: String, size: int, col: Color, width: float = -1.0, align: int = HORIZONTAL_ALIGNMENT_LEFT) -> void:
	draw_string_outline(_font, pos + Vector2(0, 0), s, align, width, size, 4, Color(0.04, 0.03, 0.02, 0.9))
	draw_string(_font, pos, s, align, width, size, col)


func _para(pos: Vector2, s: String, size: int, col: Color, width: float) -> float:
	## Draws wrapped text starting at pos (the baseline of the first line); returns the height used.
	var sz := _font.get_multiline_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, width, size)
	draw_multiline_string(_font, pos, s, HORIZONTAL_ALIGNMENT_LEFT, width, size, -1, col)
	return sz.y


func _box(r: Rect2, fill: Color = INK, edge: Color = GOLD) -> void:
	draw_rect(Rect2(r.position + Vector2(3, 3), r.size), Color(0, 0, 0, 0.35))
	draw_rect(r, fill)
	draw_rect(r, edge, false, 2.0)
	draw_rect(r.grow(-5.0), edge.darkened(0.55), false, 1.0)


# ---- frame --------------------------------------------------------------------------------------------------------
func _draw() -> void:
	if _font == null:
		return
	var vs := get_viewport_rect().size
	var kind := str(panel.get("kind", ""))
	if bool(hud.get("show", true)) and kind != "map":
		_draw_card(vs)
		_draw_nets(vs)
	_draw_toasts(vs)
	_draw_big_note(vs)
	var prompt := str(hud.get("prompt", ""))
	if prompt != "" and kind == "":
		var w := _font.get_string_size(prompt, HORIZONTAL_ALIGNMENT_LEFT, -1, 20).x + 36.0
		_box(Rect2(vs.x * 0.5 - w * 0.5, vs.y - 150.0, w, 38.0), INK2)
		_txt(Vector2(vs.x * 0.5 - w * 0.5 + 18.0, vs.y - 124.0), prompt, 20, CREAM)
	match kind:
		"dialogue":
			_draw_dialogue(vs)
		"market":
			_draw_market(vs)
		"map":
			_draw_map(vs)


func _draw_card(vs: Vector2) -> void:
	var w := 318.0
	var x := vs.x - w - 10.0
	var crew: Array = hud.get("crew", [])
	var obj := str(hud.get("objective", ""))
	var obj_h := _font.get_multiline_string_size(obj, HORIZONTAL_ALIGNMENT_LEFT, w - 28.0, 15).y
	var h := 118.0 + 18.0 * maxf(float(crew.size()), 1.0) + obj_h + 20.0
	_box(Rect2(x, 10.0, w, h), Color(0.10, 0.07, 0.05, 0.86))
	_txt(Vector2(x + 14.0, 36.0), "PURSE", 13, DIM)
	_txt(Vector2(x + w - 14.0, 40.0), "%d reales" % int(hud.get("purse", 0)), 24, GOLD, 200.0, HORIZONTAL_ALIGNMENT_RIGHT)
	# the hold
	var cap := maxf(float(hud.get("cap_kg", 40.0)), 1.0)
	var kg := float(hud.get("hold_kg", 0.0))
	var frac := clampf(kg / cap, 0.0, 1.0)
	var fresh := float(hud.get("fresh", 1.0))
	_txt(Vector2(x + 14.0, 66.0), "HOLD", 13, DIM)
	var bar := Rect2(x + 64.0, 54.0, w - 78.0, 14.0)
	draw_rect(bar, Color(0.05, 0.04, 0.03, 0.95))
	var col := GREEN
	if frac >= float(hud.get("warn_frac", 0.85)):
		col = Color(1.0, 0.72, 0.25)
	if frac >= 0.999:
		col = RED
	draw_rect(Rect2(bar.position, Vector2(bar.size.x * frac, bar.size.y)), col)
	draw_rect(bar, GOLD.darkened(0.4), false, 1.0)
	_txt(Vector2(x + 14.0, 88.0), "%.1f / %.0f kg" % [kg, cap], 15, CREAM)
	if kg > 0.0:
		var fc := GREEN if fresh >= float(hud.get("spoil_warn", 0.7)) else Color(1.0, 0.72, 0.25)
		_txt(Vector2(x + w - 14.0, 88.0), "freshness %d%%" % int(roundf(fresh * 100.0)), 15, fc, 160.0, HORIZONTAL_ALIGNMENT_RIGHT)
	_txt(Vector2(x + 14.0, 114.0), "CREW", 13, DIM)
	var yy := 114.0
	if crew.is_empty():
		_txt(Vector2(x + 64.0, yy), "you sail alone", 15, DIM)
		yy += 18.0
	for c in crew:
		_txt(Vector2(x + 64.0, yy), str(c), 15, CREAM)
		yy += 18.0
	yy += 8.0
	draw_line(Vector2(x + 12.0, yy - 12.0), Vector2(x + w - 12.0, yy - 12.0), GOLD.darkened(0.5), 1.0)
	_txt(Vector2(x + 14.0, yy + 6.0), "OBJECTIVE", 13, GOLD)
	_para(Vector2(x + 14.0, yy + 26.0), obj, 15, CREAM, w - 28.0)


func _draw_nets(vs: Vector2) -> void:
	var f: Dictionary = hud.get("fishing", {})
	if f.is_empty() or not bool(f.get("active", false)):
		return
	var w := 430.0
	var r := Rect2(vs.x * 0.5 - w * 0.5, 14.0, w, 74.0)
	_box(r, Color(0.07, 0.15, 0.2, 0.9), Color(0.5, 0.82, 0.95))
	var status := str(f.get("status", ""))
	var head := "NETS DOWN  -  %s" % str(f.get("ground", ""))
	_txt(Vector2(r.position.x + 16.0, r.position.y + 26.0), head, 18, Color(0.7, 0.92, 1.0))
	var msg := "slowing the ship, the nets drag..." if status == "drifting" else "next haul in %d s" % int(ceilf(float(f.get("next_s", 0.0))))
	_txt(Vector2(r.position.x + 16.0, r.position.y + 50.0), msg, 15, CREAM)
	_txt(Vector2(r.position.x + w - 16.0, r.position.y + 50.0), "%d hauls  %.1f kg" % [int(f.get("hauls", 0)), float(f.get("session_kg", 0.0))], 15, CREAM, 200.0, HORIZONTAL_ALIGNMENT_RIGHT)
	var prog := 1.0 - clampf(float(f.get("next_s", 12.0)) / maxf(float(f.get("interval", 12.0)), 0.1), 0.0, 1.0)
	if status == "drifting":
		prog = 0.0
	var b := Rect2(r.position.x + 16.0, r.position.y + 60.0, w - 32.0, 7.0)
	draw_rect(b, Color(0.03, 0.06, 0.08))
	draw_rect(Rect2(b.position, Vector2(b.size.x * prog, b.size.y)), Color(0.5, 0.82, 0.95))
	_txt(Vector2(r.position.x + w - 16.0, r.position.y + 26.0), "F: nets up", 14, DIM, 200.0, HORIZONTAL_ALIGNMENT_RIGHT)


func _draw_toasts(vs: Vector2) -> void:
	var y := 112.0 if not hud.get("fishing", {}).is_empty() and bool((hud["fishing"] as Dictionary).get("active", false)) else 24.0
	for q in toasts:
		var d := q as Dictionary
		var a := clampf(float(d["t"]) / 0.8, 0.0, 1.0)
		var c := (d["color"] as Color)
		c.a = a
		var w := _font.get_string_size(str(d["text"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 17).x + 28.0
		draw_rect(Rect2(vs.x * 0.5 - w * 0.5, y - 20.0, w, 30.0), Color(0.08, 0.06, 0.04, 0.78 * a))
		_txt(Vector2(vs.x * 0.5 - w * 0.5 + 14.0, y), str(d["text"]), 17, c)
		y += 34.0


func _draw_big_note(vs: Vector2) -> void:
	if big_note.is_empty():
		return
	var t := float(big_note["t"])
	var a := clampf(t / 0.8, 0.0, 1.0)
	var pop := 1.0 + 0.18 * maxf(0.0, 1.0 - (5.5 - t) * 4.0)
	var s := str(big_note["text"])
	var size := int(46.0 * pop)
	var w := _font.get_string_size(s, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	var y := vs.y * 0.30
	draw_rect(Rect2(vs.x * 0.5 - w * 0.5 - 30.0, y - size, w + 60.0, size + 46.0), Color(0.08, 0.06, 0.03, 0.72 * a))
	_txt(Vector2(vs.x * 0.5 - w * 0.5, y), s, size, Color(GOLD.r, GOLD.g, GOLD.b, a))
	_txt(Vector2(0.0, y + 30.0), str(big_note["sub"]), 18, Color(CREAM.r, CREAM.g, CREAM.b, a), vs.x, HORIZONTAL_ALIGNMENT_CENTER)


# ---- dialogue ------------------------------------------------------------------------------------------------------
func _draw_dialogue(vs: Vector2) -> void:
	var d := panel
	var w := minf(vs.x - 80.0, 900.0)
	var text := str(d.get("text", ""))
	var th := _font.get_multiline_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, w - 60.0, 20).y
	var status := str(d.get("status", ""))
	var h := 120.0 + th + (30.0 if status != "" else 0.0) + 34.0
	var r := Rect2(vs.x * 0.5 - w * 0.5, vs.y - h - 40.0, w, h)
	_box(r)
	_txt(Vector2(r.position.x + 28.0, r.position.y + 38.0), str(d.get("speaker", "")), 26, GOLD)
	_txt(Vector2(r.position.x + w - 28.0, r.position.y + 36.0), str(d.get("sub", "")), 16, DIM, 400.0, HORIZONTAL_ALIGNMENT_RIGHT)
	draw_line(Vector2(r.position.x + 24.0, r.position.y + 50.0), Vector2(r.position.x + w - 24.0, r.position.y + 50.0), GOLD.darkened(0.5), 1.0)
	var y := r.position.y + 84.0
	_para(Vector2(r.position.x + 30.0, y), text, 20, CREAM, w - 60.0)
	y += th + 14.0
	if status != "":
		_txt(Vector2(r.position.x + 30.0, y + 8.0), status, 18, (d.get("status_color", GOLD) as Color))
		y += 30.0
	_txt(Vector2(r.position.x + 30.0, r.position.y + h - 16.0), str(d.get("keys", "")), 16, DIM)
	if str(d.get("page", "")) != "":
		_txt(Vector2(r.position.x + w - 30.0, r.position.y + h - 16.0), str(d.get("page", "")), 15, DIM, 200.0, HORIZONTAL_ALIGNMENT_RIGHT)


# ---- the fish market -------------------------------------------------------------------------------------------------
func _draw_market(vs: Vector2) -> void:
	var d := panel
	var w := 780.0
	var rows: Array = d.get("rows", [])
	var prices: Array = d.get("prices", [])
	var res: Dictionary = d.get("result", {})
	var h := 150.0 + 26.0 * maxf(float(rows.size()), 1.0) + 40.0 + 26.0 * float(prices.size()) + 70.0
	if not res.is_empty():
		h = 150.0 + 26.0 * float((res["rows"] as Array).size()) + 190.0
	var r := Rect2(vs.x * 0.5 - w * 0.5, vs.y * 0.5 - h * 0.5, w, h)
	_box(r)
	_txt(Vector2(r.position.x + 28.0, r.position.y + 40.0), "FISH ROW MARKET", 26, GOLD)
	_txt(Vector2(r.position.x + w - 28.0, r.position.y + 38.0), "fishmonger %s" % str(d.get("monger", "")), 16, DIM, 400.0, HORIZONTAL_ALIGNMENT_RIGHT)
	draw_line(Vector2(r.position.x + 24.0, r.position.y + 52.0), Vector2(r.position.x + w - 24.0, r.position.y + 52.0), GOLD.darkened(0.5), 1.0)
	var y := r.position.y + 84.0
	var cx := r.position.x + 28.0
	if not res.is_empty():
		_txt(Vector2(cx, y), "SOLD", 16, DIM)
		y += 12.0
		for q in res["rows"]:
			var rr := q as Dictionary
			y += 26.0
			_txt(Vector2(cx, y), "%s" % str(rr["name"]), 18, CREAM)
			_txt(Vector2(cx + 250.0, y), "%.1f kg" % float(rr["kg"]), 18, CREAM)
			_txt(Vector2(cx + 380.0, y), "fresh %d%%" % int(roundf(float(rr["fresh"]) * 100.0)), 16, DIM)
			_txt(Vector2(cx + 520.0, y), "price level %d%%" % int(roundf(float(rr["level"]) * 100.0)), 16, DIM)
			_txt(Vector2(cx + w - 56.0, y), "+%d" % int(rr["reales"]), 20, GOLD, 100.0, HORIZONTAL_ALIGNMENT_RIGHT)
		y += 44.0
		_txt(Vector2(cx, y), "YOU EARNED  %d reales" % int(res["reales"]), 30, GOLD)
		y += 34.0
		_txt(Vector2(cx, y), "Purse: %d  ->  %d reales" % [int(res["purse_before"]), int(res["purse_after"])], 20, CREAM)
		y += 28.0
		_txt(Vector2(cx, y), str(res.get("line", "")), 16, DIM)
	else:
		_txt(Vector2(cx, y), "YOUR HOLD", 16, DIM)
		if rows.is_empty():
			y += 30.0
			_txt(Vector2(cx, y), "Empty. Sail out, cast the nets (F at a fishing ground) and come back.", 18, CREAM)
		for q in rows:
			var rr := q as Dictionary
			y += 26.0
			_txt(Vector2(cx, y), "[%s] %s" % [str(rr["key"]), str(rr["name"])], 18, CREAM)
			_txt(Vector2(cx + 250.0, y), "%.1f kg" % float(rr["kg"]), 18, CREAM)
			var fc := GREEN if float(rr["fresh"]) >= 0.7 else Color(1.0, 0.72, 0.25)
			_txt(Vector2(cx + 380.0, y), "fresh %d%%" % int(roundf(float(rr["fresh"]) * 100.0)), 16, fc)
			_txt(Vector2(cx + 520.0, y), "%.2f /kg" % float(rr["price"]), 16, DIM)
			_txt(Vector2(cx + w - 56.0, y), "%d" % int(rr["est"]), 20, GOLD, 100.0, HORIZONTAL_ALIGNMENT_RIGHT)
		y += 40.0
		_txt(Vector2(cx, y), "TODAY'S PRICES  (reales per kg, fresh; the market remembers what you sell)", 16, DIM)
		for q in prices:
			var pp := q as Dictionary
			y += 26.0
			_txt(Vector2(cx, y), str(pp["name"]), 17, CREAM)
			_txt(Vector2(cx + 250.0, y), "%.2f" % float(pp["price"]), 17, GOLD)
			var lv := float(pp["level"])
			var lc := GREEN if lv > 0.93 else (Color(1.0, 0.72, 0.25) if lv > 0.7 else RED)
			_txt(Vector2(cx + 380.0, y), "market at %d%% of normal" % int(roundf(lv * 100.0)), 16, lc)
		y += 36.0
		if int(d.get("total", 0)) > 0:
			_txt(Vector2(cx, y), "The whole hold would pay about %d reales." % int(d["total"]), 20, GOLD)
	_txt(Vector2(cx, r.position.y + h - 18.0), str(d.get("keys", "")), 16, DIM)
	_txt(Vector2(r.position.x + w - 28.0, r.position.y + h - 18.0), "purse %d reales" % int(d.get("purse", 0)), 17, GOLD, 300.0, HORIZONTAL_ALIGNMENT_RIGHT)


# ---- the map ---------------------------------------------------------------------------------------------------------
func set_map_image(key: String, img: Image) -> void:
	_images[key] = ImageTexture.create_from_image(img)


func has_map_image(key: String) -> bool:
	return _images.has(key)


func _draw_map(vs: Vector2) -> void:
	var d := panel
	var tab := int(d.get("tab", 0))
	var r := Rect2(30.0, 24.0, vs.x - 60.0, vs.y - 48.0)
	_box(r, Color(0.09, 0.07, 0.05, 0.97))
	_txt(Vector2(r.position.x + 24.0, r.position.y + 38.0), "ANVIL HARBOR  -  %s" % ("FISH ROW" if tab == 0 else "THE WATERS SOUTH"), 26, GOLD)
	_txt(Vector2(r.position.x + r.size.x - 24.0, r.position.y + 36.0), "Tab: switch map    M / Esc: close", 16, DIM, 500.0, HORIZONTAL_ALIGNMENT_RIGHT)
	var side := 330.0
	var area := Rect2(r.position.x + 20.0, r.position.y + 56.0, r.size.x - side - 50.0, r.size.y - 76.0)
	var b: Array = d["bounds"]
	var bw := float(b[2]) - float(b[0])
	var bh := float(b[3]) - float(b[1])
	var sc := minf(area.size.x / bw, area.size.y / bh)
	var org := area.position + (area.size - Vector2(bw, bh) * sc) * 0.5
	draw_rect(Rect2(org, Vector2(bw, bh) * sc), WATER)
	var key := "district" if tab == 0 else "waters"
	if _images.has(key):
		draw_texture_rect(_images[key] as Texture2D, Rect2(org, Vector2(bw, bh) * sc), false)
	draw_rect(Rect2(org, Vector2(bw, bh) * sc), GOLD.darkened(0.3), false, 2.0)
	var m := func(x: float, z: float) -> Vector2: return org + Vector2((x - float(b[0])) * sc, (z - float(b[1])) * sc)
	if tab == 0:
		for q in d.get("wharf", []):
			var a := q as Array
			draw_rect(Rect2(m.call(float(a[0]), float(a[1])), Vector2(float(a[2]) - float(a[0]), float(a[3]) - float(a[1])) * sc), Color(0.55, 0.38, 0.22))
		for q in d.get("bridges", []):
			var a := q as Array
			draw_rect(Rect2(m.call(float(a[0]), float(a[1])), Vector2(float(a[2]) - float(a[0]), float(a[3]) - float(a[1])) * sc), Color(0.76, 0.60, 0.36))
			draw_rect(Rect2(m.call(float(a[0]), float(a[1])), Vector2(float(a[2]) - float(a[0]), float(a[3]) - float(a[1])) * sc), Color(0.2, 0.12, 0.06), false, 1.5)
		for q in d.get("buildings", []):
			var a := q as Array
			draw_rect(Rect2(m.call(float(a[0]), float(a[1])), Vector2(float(a[2]) - float(a[0]), float(a[3]) - float(a[1])) * sc), Color(0.50, 0.30, 0.24))
			draw_rect(Rect2(m.call(float(a[0]), float(a[1])), Vector2(float(a[2]) - float(a[0]), float(a[3]) - float(a[1])) * sc), Color(0.15, 0.08, 0.06), false, 1.5)
		for q in d.get("labels", []):
			var lb := q as Dictionary
			_txt(m.call(float(lb["x"]), float(lb["z"])) - Vector2(40, 0), str(lb["text"]), 13, Color(0.95, 0.9, 0.78, 0.8))
		# the harbour: the player's ship
		_glyph_ship(m.call(float(d["berth"][0]), float(d["berth"][1])) as Vector2, 0.0, sc * 0.55, GOLD, "Your sloop (berth)")
		for q in d.get("recruits", []):
			var rc := q as Dictionary
			var st := str(rc["state"])
			if st == "hired":
				continue
			var p := m.call(float(rc["x"]), float(rc["z"])) as Vector2
			_glyph_recruit(p, GREEN if st == "afford" else GOLD, 11.0)
			_txt(p + Vector2(14.0, 5.0), str(rc["name"]), 15, CREAM)
		for q in d.get("points", []):
			var pt := q as Dictionary
			var p2 := m.call(float(pt["x"]), float(pt["z"])) as Vector2
			if str(pt["kind"]) == "market":
				_glyph_fish(p2, Color(0.55, 0.9, 1.0), 13.0)
			else:
				draw_rect(Rect2(p2 - Vector2(7, 8), Vector2(14, 16)), Color(0.95, 0.9, 0.7))
				draw_rect(Rect2(p2 - Vector2(7, 8), Vector2(14, 16)), Color(0.2, 0.12, 0.06), false, 2.0)
			_txt(p2 + Vector2(16.0, 5.0), str(pt["name"]), 15, CREAM)
	else:
		for q in d.get("grounds", []):
			var g := q as Dictionary
			var c := m.call(float(g["x"]), float(g["z"])) as Vector2
			var rad := float(g["r"]) * sc
			var gc := Color(0.55, 0.9, 1.0) if bool(g["open"]) else Color(0.7, 0.6, 0.6)
			draw_arc(c, rad, 0.0, TAU, 40, gc, 2.0)
			draw_circle(c, rad, Color(gc.r, gc.g, gc.b, 0.12))
			_glyph_fish(c, gc, 12.0)
			_txt(c + Vector2(-rad, -rad - 8.0), str(g["name"]), 15, CREAM)
			_txt(c + Vector2(-rad, rad + 16.0), str(g["line"]), 13, DIM)
		var hb := m.call(float(d["berth"][0]), float(d["berth"][1])) as Vector2
		_glyph_ship(hb, 0.0, 0.9, GOLD, "Anvil Harbor")
	var ship := d.get("ship", Vector2.ZERO) as Vector2
	var pl := d.get("player", Vector2.ZERO) as Vector2
	if bool(d.get("ashore", false)):
		var pp2 := m.call(pl.x, pl.y) as Vector2
		_glyph_player(pp2)
		_txt(pp2 + Vector2(12.0, -10.0), "you", 15, Color(1, 1, 1))
	elif tab == 1:
		_glyph_ship(m.call(ship.x, ship.y) as Vector2, float(d.get("ship_heading", 0.0)), 1.0, Color(1, 1, 1), "your ship")
	# the side list
	var sx := r.position.x + r.size.x - side - 10.0
	var y := r.position.y + 70.0
	_txt(Vector2(sx, y), "WANTED HANDS", 15, GOLD)
	y += 10.0
	for q in d.get("recruits", []):
		var rc := q as Dictionary
		var st := str(rc["state"])
		y += 22.0
		var col := DIM if st == "hired" else (GREEN if st == "afford" else GOLD)
		_glyph_recruit(Vector2(sx + 8.0, y - 5.0), col, 7.0)
		_txt(Vector2(sx + 24.0, y), "%s, %s" % [str(rc["name"]), str(rc["role"])], 16, CREAM if st != "hired" else DIM)
		y += 20.0
		var line := "%d reales" % int(rc["cost"])
		if st == "hired":
			line = "aboard your ship"
		elif st == "afford":
			line += "  -  you can afford him"
		else:
			line += "  -  %d short" % int(rc["short"])
		_txt(Vector2(sx + 24.0, y), line, 14, col)
		y += 18.0
		y += _para(Vector2(sx + 24.0, y), "Find him at %s." % str(rc["place"]), 14, DIM, side - 40.0) + 4.0
	y += 18.0
	_txt(Vector2(sx, y), "FISH MARKET", 15, Color(0.55, 0.9, 1.0))
	y += 22.0
	y += _para(Vector2(sx, y), "Barnaby Gull buys by the kilo, under the red canopy on Quay Street (west of the canal).", 14, DIM, side - 10.0)
	y += 24.0
	_txt(Vector2(sx, y), "LEGEND", 15, GOLD)
	y += 22.0
	_glyph_recruit(Vector2(sx + 8.0, y - 5.0), GOLD, 7.0)
	_txt(Vector2(sx + 24.0, y), "recruit    ", 14, CREAM)
	_glyph_recruit(Vector2(sx + 108.0, y - 5.0), GREEN, 7.0)
	_txt(Vector2(sx + 124.0, y), "affordable", 14, CREAM)
	y += 22.0
	_glyph_fish(Vector2(sx + 8.0, y - 5.0), Color(0.55, 0.9, 1.0), 9.0)
	_txt(Vector2(sx + 24.0, y), "fish market / fishing ground", 14, CREAM)
	y += 22.0
	_glyph_ship(Vector2(sx + 8.0, y - 5.0), 0.0, 0.5, GOLD, "")
	_txt(Vector2(sx + 24.0, y), "your ship", 14, CREAM)


func _glyph_recruit(p: Vector2, col: Color, s: float) -> void:
	var pts := PackedVector2Array([p + Vector2(0, -s), p + Vector2(s, 0), p + Vector2(0, s), p + Vector2(-s, 0)])
	draw_colored_polygon(pts, col)
	draw_polyline(PackedVector2Array([pts[0], pts[1], pts[2], pts[3], pts[0]]), Color(0.1, 0.06, 0.03), 2.0)
	draw_rect(Rect2(p + Vector2(-1.0, -s * 0.5), Vector2(2.0, s * 0.5)), Color(0.1, 0.06, 0.03))
	draw_rect(Rect2(p + Vector2(-1.0, s * 0.15), Vector2(2.0, 2.0)), Color(0.1, 0.06, 0.03))


func _glyph_fish(p: Vector2, col: Color, s: float) -> void:
	var body := PackedVector2Array()
	for i in 16:
		var a := TAU * float(i) / 16.0
		body.append(p + Vector2(cos(a) * s, sin(a) * s * 0.55))
	draw_colored_polygon(body, col)
	draw_colored_polygon(PackedVector2Array([p + Vector2(s * 0.8, 0), p + Vector2(s * 1.5, -s * 0.6), p + Vector2(s * 1.5, s * 0.6)]), col)
	draw_polyline(body + PackedVector2Array([body[0]]), Color(0.05, 0.1, 0.14), 2.0)
	draw_circle(p + Vector2(-s * 0.45, -s * 0.1), 1.6, Color(0.05, 0.1, 0.14))


func _glyph_ship(p: Vector2, heading_deg: float, scale: float, col: Color, label: String) -> void:
	var a := deg_to_rad(heading_deg)
	var fwd := Vector2(sin(a), -cos(a))
	var side := Vector2(-fwd.y, fwd.x)
	var s := 18.0 * scale
	var pts := PackedVector2Array([p + fwd * s * 1.4, p + side * s * 0.6 + fwd * s * 0.2, p + side * s * 0.5 - fwd * s * 1.1,
			p - side * s * 0.5 - fwd * s * 1.1, p - side * s * 0.6 + fwd * s * 0.2])
	draw_colored_polygon(pts, col)
	draw_polyline(PackedVector2Array([pts[0], pts[1], pts[2], pts[3], pts[4], pts[0]]), Color(0.1, 0.06, 0.03), 2.0)
	if label != "":
		_txt(p + Vector2(s * 0.9 + 6.0, 5.0), label, 15, CREAM)


func _glyph_player(p: Vector2) -> void:
	var pulse := 1.0 + 0.12 * sin(_t * 5.0)
	draw_circle(p, 9.0 * pulse, Color(1, 1, 1, 0.35))
	draw_circle(p, 5.5, Color(1.0, 1.0, 1.0))
	draw_circle(p, 5.5, Color(0.1, 0.06, 0.03), false, 2.0)


# ---- map images --------------------------------------------------------------------------------------------------------
## Samples the world into a small Image: `cell` metres per pixel over bounds [x0, z0, x1, z1]. `world` = cay_world.gd.
static func build_map_image(world: Object, bounds: Array, cell: float) -> Image:
	var x0 := float(bounds[0])
	var z0 := float(bounds[1])
	var w := int(ceilf((float(bounds[2]) - x0) / cell))
	var h := int(ceilf((float(bounds[3]) - z0) / cell))
	var img := Image.create_empty(w, h, false, Image.FORMAT_RGBA8)
	for j in h:
		for i in w:
			var x := x0 + (float(i) + 0.5) * cell
			var z := z0 + (float(j) + 0.5) * cell
			var ht := float(world.call("height_at", x, z))
			if ht < 0.3:
				img.set_pixel(i, j, Color(0, 0, 0, 0))
				continue
			var cls := int(world.call("class_at", x, z))
			var c: Color = COASTS.get(cls, Color(0.5, 0.55, 0.4))
			c = c.darkened(clampf((ht - 2.0) / 120.0, 0.0, 0.3))
			img.set_pixel(i, j, c)
	return img
