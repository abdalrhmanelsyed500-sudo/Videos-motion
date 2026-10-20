# gdlint: disable=max-line-length,max-file-lines,max-public-methods,class-definitions-order
extends Control
## CP-2 Release B: the first-person view of the winch. Pure drawing + a few particles: it reads the FishManual state machine and the
## environment the host gives it and draws (no input, no logic, no inventory). Everything is drawn with 2D rectangles, lines and the
## fish PNGs in ONE _draw call (no 3D, no shaders, no extra viewport), so it costs a few hundred draw calls on any GPU; while it is
## up the host stops the 3D world from rendering at all.
##
## The picture: the sea to the horizon (colour from the time of day, waves from the sea state, a gentle sway from the ship's roll),
## the ship's planked side with the rail in the lower left, the winch on the rail (drum, rope, two cranks with the pirate's hands),
## the davit with its pulley, the rope running over it and down into the water, and the net on the end of it: sinking, with shoal
## shadows around it, rising out of the water dripping with the REAL fish in it, swung over the rail. On the pixel grid: the scene
## is drawn at an integer scale of a virtual canvas about 455 x 292, so it is crisp at 1366 x 876 (scale 3) and at other sizes.
## The readable parts (stage, progress, tension, messages, cards) are drawn at real pixel sizes on top.
## NOT YET RUN ON THE USER'S PC.
const Manual := preload("res://h2d/fish_manual.gd")
const FishArt := preload("res://h2d/fish_art.gd")
const Catch := preload("res://h2d/fish_catch.gd")

const GOLD := Color(1.0, 0.82, 0.30)
const CREAM := Color(0.96, 0.92, 0.80)
const GREEN := Color(0.40, 0.90, 0.50)
const RED := Color(1.0, 0.36, 0.30)
const AMBER := Color(1.0, 0.70, 0.25)
const PANEL := Color(0.09, 0.07, 0.05, 0.92)
const PANEL_EDGE := Color(0.62, 0.45, 0.22)
const MAX_PARTICLES := 90

var m: Manual = null
var env: Dictionary = {"hour": 12.0, "sea": 0.2, "roll": 0.0, "light": 1.0, "ground": "", "hold_kg": 0.0, "capacity": 40.0, "names": {}, "keys": {}}
var _t := 0.0
var _s := 3                       # pixels per virtual pixel
var _vw := 455.0
var _vh := 292.0
var _parts: Array = []            # {x, y, vx, vy, life, max, kind}
var _banner := ""
var _banner_t := 0.0
var _banner_col := CREAM
var _shake := 0.0
var _unload_sprites: Array = []   # fish flying to the barrel: {tex, n, t0}
var _last_stage := -1
var font: Font = null


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP      # nothing underneath may be clicked while the view is up
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	set_anchors_preset(Control.PRESET_FULL_RECT)
	font = ThemeDB.fallback_font
	visible = false


func setup(manual: Manual) -> void:
	m = manual


## A Control under a CanvasLayer is not laid out by anything (its anchors have no parent to refer to): the size is set by hand, every frame.
func _fit() -> void:
	var vs := get_viewport_rect().size if is_inside_tree() else Vector2(1366.0, 876.0)
	if size != vs:
		position = Vector2.ZERO
		size = vs


func set_env(e: Dictionary) -> void:
	for k in e.keys():
		env[k] = e[k]


## Called every frame while the view is up.
func tick(dt: float) -> void:
	_fit()
	_t += dt
	_banner_t = maxf(_banner_t - dt, 0.0)
	_shake = maxf(_shake - dt * 3.0, 0.0)
	var i := _parts.size() - 1
	while i >= 0:
		var p: Dictionary = _parts[i]
		p["life"] = float(p["life"]) - dt
		p["x"] = float(p["x"]) + float(p["vx"]) * dt
		p["y"] = float(p["y"]) + float(p["vy"]) * dt
		p["vy"] = float(p["vy"]) + (60.0 if str(p["kind"]) == "drip" else 0.0) * dt
		if float(p["life"]) <= 0.0:
			_parts.remove_at(i)
		i -= 1
	if m != null and m.stage != _last_stage:
		_on_stage(m.stage)
		_last_stage = m.stage
	if m != null and m.stage == Manual.Stage.RAISE and _t - floorf(_t) < dt * 1.5:
		_drips(2)
	queue_redraw()


func on_events(evs: Array) -> void:
	for e in evs:
		var d: Dictionary = e
		match str(d["type"]):
			"cast":
				_banner = str(d["grade"]).to_upper()
				_banner_col = GREEN if float(d["quality"]) >= 1.0 else (AMBER if float(d["quality"]) >= 0.7 else RED)
				_banner_t = 1.6
				_splash(_net_pos(), 14)
			"surge_warn":
				_banner = "THE FISH IS ABOUT TO RUN!" if int(d["kind"]) > 0 else "THE FISH IS TURNING!"
				_banner_col = AMBER
				_banner_t = 1.2
			"streak":
				_banner = "STREAK x%d!" % int(d["streak"])
				_banner_col = GOLD
				_banner_t = 1.0
			"pull_ok":
				_splash(_net_pos() + Vector2(0, 4), 1)
			"pull_bad":
				_shake = 0.35
			"fail":
				_banner = "LOST THE HAUL"
				_banner_col = RED
				_banner_t = 2.0
				_splash(_net_pos(), 22)
			"hauled":
				_banner = "THE NET COMES UP!"
				_banner_col = GREEN
				_banner_t = 1.6


func _on_stage(st: int) -> void:
	if st == Manual.Stage.UNLOAD and m != null:
		_unload_sprites = []
		var t0 := 0.0
		for f in m.result.get("fish", []):
			var d: Dictionary = f
			var n := mini(int(d["count"]), 5)
			for i in n:
				_unload_sprites.append({"icon": _icon_of(str(d["species"])), "t0": t0})
				t0 += 0.11
	elif st == Manual.Stage.SINK:
		_splash(_net_pos(), 10)


func _icon_of(species_id: String) -> String:
	return str((m.species.get(species_id, {}) as Dictionary).get("icon", ""))


# ---- layout -------------------------------------------------------------------------------------------------------------
func _layout() -> void:
	_s = maxi(1, int(roundf(size.y / 292.0)))
	_vw = size.x / float(_s)
	_vh = size.y / float(_s)


func _k() -> float:
	return size.y / 780.0


func _v(x: float, y: float) -> Vector2:
	return Vector2(x * float(_s), y * float(_s))


func _rect(x: float, y: float, w: float, h: float, c: Color) -> void:
	draw_rect(Rect2(x * float(_s), y * float(_s), w * float(_s), h * float(_s)), c)


func _poly(pts: Array, c: Color) -> void:
	var out := PackedVector2Array()
	for p in pts:
		out.append(_v(float((p as Vector2).x), float((p as Vector2).y)))
	draw_colored_polygon(out, c)


func _ln(a: Vector2, b: Vector2, c: Color, w: float = 1.0) -> void:
	draw_line(_v(a.x, a.y), _v(b.x, b.y), c, w * float(_s))


func _hy() -> float:
	return _vh * 0.27


func _pulley() -> Vector2:
	return Vector2(_vw * 0.60, _vh * 0.20)


## The net's top ring (virtual coordinates): depth 0 hangs just under the pulley, 1 is deep in the water.
func _net_pos() -> Vector2:
	var depth := m.depth if m != null else 1.0
	var sway := sin(_t * 1.3) * (1.0 + float(env["sea"]) * 3.0) * (0.5 + 0.5 * (1.0 - depth))
	var p := _pulley()
	return Vector2(p.x + 6.0 + sway * (1.4 if depth < 0.3 else 0.5), lerpf(p.y + 20.0, _vh * 0.80, depth))


func _water_y() -> float:
	return _vh * 0.58


# ---- palette ------------------------------------------------------------------------------------------------------------
func _light() -> float:
	return clampf(float(env["light"]), 0.0, 1.0)


func _warm() -> float:
	var h := float(env["hour"])
	var w := 0.0
	if h >= 5.0 and h < 7.5:
		w = 1.0 - absf(h - 6.0) / 1.5
	elif h >= 16.5 and h < 19.5:
		w = 1.0 - absf(h - 18.0) / 1.5
	return clampf(w, 0.0, 1.0)


func _mix_day(day: Color, night: Color) -> Color:
	return night.lerp(day, _light())


func _wood(c: Color) -> Color:
	var l := 0.38 + 0.62 * _light()
	return Color(c.r * l, c.g * l, c.b * l * (0.9 + 0.1 * _light()), c.a)


# ---- drawing ------------------------------------------------------------------------------------------------------------
func _draw() -> void:
	if m == null:
		return
	_layout()
	var sea := float(env["sea"])
	var roll := float(env["roll"])
	var sway := sin(_t * 1.1) * (0.8 + sea * 2.5) + roll * 0.6 + sin(_t * 47.0) * _shake * 1.5
	draw_set_transform(Vector2(0, sway * float(_s)), 0.0, Vector2.ONE)
	_draw_sky()
	_draw_sea()
	_draw_shoal()
	_draw_net_and_rope()
	draw_set_transform(Vector2(0, -sway * 0.6 * float(_s)), 0.0, Vector2.ONE)
	_draw_hull_and_winch()
	_draw_particles()
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	_draw_barrel_and_fly()
	_draw_hud()


func _draw_sky() -> void:
	var hy := _hy() + 6.0
	var warm := _warm()
	var top := _mix_day(Color(0.30, 0.56, 0.86), Color(0.02, 0.04, 0.12))
	var bot := _mix_day(Color(0.72, 0.86, 0.94), Color(0.09, 0.13, 0.27))
	bot = bot.lerp(Color(0.95, 0.55, 0.32), warm * 0.65)
	top = top.lerp(Color(0.45, 0.35, 0.60), warm * 0.4)
	var bands := 9
	for i in bands:
		var y0 := -8.0 + (hy + 8.0) * float(i) / float(bands)
		_rect(0, y0, _vw, (hy + 8.0) / float(bands) + 1.0, top.lerp(bot, float(i) / float(bands - 1)))
	# the sun by day, the moon at night, and a few clouds that drift
	var h := float(env["hour"])
	var sx := _vw * (0.12 + 0.76 * clampf((h - 5.0) / 14.0, 0.0, 1.0))
	if _light() > 0.25:
		var sy := hy - 14.0 - 40.0 * sin(PI * clampf((h - 5.0) / 14.0, 0.0, 1.0))
		_rect(sx - 6, sy - 6, 12, 12, Color(1.0, 0.95, 0.70, 0.95))
		_rect(sx - 8, sy - 4, 16, 8, Color(1.0, 0.95, 0.70, 0.35))
	else:
		_rect(_vw * 0.22 - 5, hy - 46.0, 10, 10, Color(0.92, 0.94, 0.85))
		_rect(_vw * 0.22 - 2, hy - 46.0, 8, 8, Color(0.07, 0.10, 0.20))
	var cc := _mix_day(Color(1, 1, 1, 0.85), Color(0.25, 0.30, 0.45, 0.7))
	for i in 5:
		var cx := fposmod(float(i) * 97.0 + _t * (2.0 + float(i) * 0.7), _vw + 90.0) - 45.0
		var cy := 10.0 + float((i * 37) % 38)
		_rect(cx, cy, 34, 5, cc)
		_rect(cx + 7, cy - 4, 20, 5, cc)
		_rect(cx + 14, cy + 4, 24, 3, Color(cc.r * 0.92, cc.g * 0.92, cc.b * 0.96, cc.a))
	# the distant sea line
	_rect(0, hy - 1.0, _vw, 1.0, _mix_day(Color(0.55, 0.78, 0.90), Color(0.10, 0.18, 0.32)))


func _draw_sea() -> void:
	var hy := _hy() + 6.0
	var far := _mix_day(Color(0.20, 0.58, 0.78), Color(0.05, 0.12, 0.24)).lerp(Color(0.80, 0.50, 0.40), _warm() * 0.3)
	var near := _mix_day(Color(0.06, 0.30, 0.50), Color(0.02, 0.05, 0.13))
	var bands := 16
	for i in bands:
		var f := float(i) / float(bands - 1)
		var y0 := hy + (_vh - hy) * float(i) / float(bands)
		_rect(0, y0, _vw, (_vh - hy) / float(bands) + 1.0, far.lerp(near, pow(f, 0.8)))
	var sea := float(env["sea"])
	var hl := _mix_day(Color(0.78, 0.95, 1.0, 0.55), Color(0.35, 0.45, 0.70, 0.35))
	var rows := 20
	for r in rows:
		var f := float(r) / float(rows - 1)
		var y := hy + 3.0 + pow(f, 1.7) * (_vh - hy - 6.0)
		var span := 8.0 + f * 22.0
		var n := 6 + int(sea * 6.0)
		for j in n:
			var seed_v := float(r * 31 + j * 17)
			var x := fposmod(seed_v * 13.7 + _t * (3.0 + f * 9.0) * (1.0 if r % 2 == 0 else -0.7), _vw + span) - span * 0.5
			var wob := sin(_t * 1.7 + seed_v) * (0.4 + f * 0.8)
			_rect(x, y + wob, span * (0.5 + 0.5 * fposmod(seed_v * 0.37, 1.0)), 1.0 + f * 0.6, hl)
	# the rope enters the water: rings
	if m.depth > 0.35 or m.stage == Manual.Stage.RAISE:
		var np := _net_pos()
		var wy := _water_y()
		var pr := fposmod(_t * 0.9, 1.0)
		_rect(np.x - 6 - pr * 14, wy, 12 + pr * 28, 1, Color(1, 1, 1, 0.5 * (1.0 - pr)))
		_rect(np.x - 4 - pr * 8, wy + 2, 8 + pr * 16, 1, Color(1, 1, 1, 0.3 * (1.0 - pr)))


func _draw_shoal() -> void:
	if m.stage != Manual.Stage.SOAK and m.stage != Manual.Stage.HAUL and m.stage != Manual.Stage.SINK:
		return
	var np := _net_pos()
	var n := 9 if m.stage != Manual.Stage.SINK else 4
	var col := _mix_day(Color(0.03, 0.18, 0.30, 0.55), Color(0.0, 0.03, 0.08, 0.5))
	var scat := 1.0 + (1.0 - m.integrity) * 1.2
	for i in n:
		var a := _t * (0.8 + 0.12 * float(i)) + float(i) * 1.9
		var rx := (28.0 + float(i % 4) * 9.0) * scat
		var x := np.x + cos(a) * rx
		var y := np.y + 14.0 + sin(a * 1.3) * (10.0 + float(i % 3) * 5.0)
		var dirx := -sin(a)
		_poly([Vector2(x - 5.0 * signf(dirx), y), Vector2(x + 2.0 * signf(dirx), y - 2.0), Vector2(x + 2.0 * signf(dirx), y + 2.0)], col)
		_poly([Vector2(x - 5.0 * signf(dirx), y), Vector2(x - 8.0 * signf(dirx), y - 2.0), Vector2(x - 8.0 * signf(dirx), y + 2.0)], col)


func _draw_net_and_rope() -> void:
	var pl := _pulley()
	var np := _net_pos()
	var rope := _wood(Color(0.80, 0.66, 0.40))
	var dark := _wood(Color(0.46, 0.34, 0.20))
	# the rope from the drum over the pulley to the net
	var drum := Vector2(_vw * 0.26, _vh * 0.52)
	var top := Vector2(pl.x, pl.y - 7.0)
	var mid := drum.lerp(top, 0.5) + Vector2(0, 6.0 + sin(_t * 1.5) * 1.2)
	_ln(drum, mid, rope, 1.0)
	_ln(mid, top, rope, 1.0)
	_ln(Vector2(pl.x + 6.0, pl.y), np + Vector2(0, -3.0), rope, 1.0)
	_ln(Vector2(pl.x + 7.0, pl.y), np + Vector2(1, -3.0), dark, 1.0)
	# the net
	var under := np.y > _water_y()
	var q := m.cast_q if m.stage >= Manual.Stage.SINK else 0.8
	var rx := 26.0 * clampf(q, 0.55, 1.2) * (1.0 + (1.0 - clampf(m.depth, 0.0, 1.0)) * 0.1)
	var bag := 34.0 * (0.8 + 0.4 * (1.0 - clampf(m.progress, 0.0, 1.0) * 0.0))
	var col := rope
	if under:
		col = Color(rope.r * 0.55, rope.g * 0.72, rope.b * 0.85, 0.85)
	var ring_y := np.y
	var sw: float = sin(_t * 2.1) * (3.0 if m.stage == Manual.Stage.RAISE else 0.8)
	var pts := 9
	var bottom := Vector2(np.x + sw, ring_y + bag)
	# meridians
	for i in pts:
		var a := PI * float(i) / float(pts - 1)
		var rim := Vector2(np.x + cos(a) * rx, ring_y + sin(a) * 4.0)
		_ln(rim, bottom, col, 1.0)
	# parallels (the mesh)
	for j in [0.3, 0.55, 0.8]:
		var yy := ring_y + bag * float(j)
		var wdt := rx * (1.0 - float(j)) + 1.0
		var prev := Vector2.ZERO
		for i in 7:
			var a2 := PI * float(i) / 6.0
			var p2 := Vector2(np.x + sw * float(j) + cos(a2) * wdt, yy + sin(a2) * 3.0 * (1.0 - float(j)))
			if i > 0:
				_ln(prev, p2, col, 1.0)
			prev = p2
	# the ring
	for i in 17:
		var a3 := TAU * float(i) / 16.0
		var a4 := TAU * float(i + 1) / 16.0
		_ln(Vector2(np.x + cos(a3) * rx, ring_y + sin(a3) * 4.0), Vector2(np.x + cos(a4) * rx, ring_y + sin(a4) * 4.0), dark if i % 2 == 0 else rope, 1.0)
	# the REAL fish in the net once it is coming up (and while it is unloaded they leave one by one)
	if (m.stage == Manual.Stage.RAISE or m.stage == Manual.Stage.SUMMARY or m.stage == Manual.Stage.UNLOAD) and not bool(m.result.get("failed", false)):
		_draw_net_fish(np, sw, bag, rx)


func _fish_list() -> Array:
	# one entry per sprite: {icon, i}; at most 14, in proportion to the real catch
	var out: Array = []
	if m == null or m.result.is_empty():
		return out
	var total := 0
	for f in m.result.get("fish", []):
		total += int((f as Dictionary)["count"])
	if total <= 0:
		return out
	var cap := mini(total, 14)
	for f in m.result.get("fish", []):
		var d: Dictionary = f
		var n := maxi(1, int(roundf(float(d["count"]) / float(total) * float(cap))))
		for i in n:
			if out.size() < cap:
				out.append({"icon": _icon_of(str(d["species"])), "i": out.size()})
	return out


func _draw_net_fish(np: Vector2, sw: float, bag: float, rx: float) -> void:
	var list := _fish_list()
	var vis := 1.0
	if m.stage == Manual.Stage.UNLOAD:
		vis = clampf(1.0 - m.stage_t / maxf(float(m.p["unload_s"]) * 0.8, 0.1), 0.0, 1.0)
	var n := int(ceilf(float(list.size()) * vis))
	for i in n:
		var d: Dictionary = list[i]
		var tex := FishArt.texture(str(d["icon"]))
		var a := float(i) * 2.399
		var rr := (0.25 + 0.55 * fposmod(float(i) * 0.37, 1.0)) * rx * 0.85
		var x := np.x + sw * 0.5 + cos(a) * rr - 10.0
		var y := np.y + bag * 0.30 + sin(a) * bag * 0.22 + 2.0 + float(i % 3) * 2.0
		var wig := sin(_t * 5.0 + float(i)) * (2.0 if m.stage == Manual.Stage.RAISE else 0.5)
		if tex != null:
			draw_set_transform(_v(x + 10.0, y + 5.0 + wig), 0.35 * sin(_t * 3.0 + float(i)) + (0.0 if i % 2 == 0 else PI * 0.08), Vector2.ONE)
			draw_texture_rect(tex, Rect2(-10.0 * float(_s), -5.0 * float(_s), 20.0 * float(_s), 10.0 * float(_s)), false)
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		else:
			_rect(x, y + wig, 16, 7, Color(0.7, 0.8, 0.9))


func _draw_hull_and_winch() -> void:
	var l := _light()
	var wood := _wood(Color(0.50, 0.33, 0.17))
	var wood_d := _wood(Color(0.32, 0.20, 0.10))
	var wood_l := _wood(Color(0.66, 0.46, 0.25))
	var iron := _wood(Color(0.20, 0.20, 0.24))
	var wall_top0 := _vh * 0.50
	var wall_top1 := _vh * 0.74
	var wx := _vw * 0.52
	# the ship's side: a planked wall running away to the left, its rail on top
	_poly([Vector2(0, wall_top0 - 10.0), Vector2(wx, wall_top1 - 10.0), Vector2(wx, _vh + 2.0), Vector2(0, _vh + 2.0)], wood)
	var planks := 9
	for i in planks:
		var f := float(i + 1) / float(planks + 1)
		var y0 := lerpf(wall_top0, _vh, f)
		var y1 := lerpf(wall_top1, _vh, f)
		_ln(Vector2(0, y0), Vector2(wx, y1), wood_d, 1.0)
		for j in 4:
			var xx := fposmod(float(i * 53 + j * 71), wx)
			var yy := lerpf(y0, y1, xx / wx)
			_rect(xx, yy - 3.0, 1.0, 2.0, wood_d)
	_poly([Vector2(0, wall_top0 - 10.0), Vector2(wx, wall_top1 - 10.0), Vector2(wx, wall_top1 - 1.0), Vector2(0, wall_top0 + 1.0)], wood_l)
	_ln(Vector2(0, wall_top0 + 1.0), Vector2(wx, wall_top1 - 1.0), wood_d, 1.0)
	_ln(Vector2(0, wall_top0 - 10.0), Vector2(wx, wall_top1 - 10.0), _wood(Color(0.78, 0.58, 0.32)), 1.0)
	# foam at the waterline under the hull edge
	_rect(wx, _vh * 0.80, 3, _vh * 0.2, Color(1, 1, 1, 0.35 * l + 0.1))
	# the davit: post on the rail, arm out over the sea, the pulley at the end
	var pl := _pulley()
	var post_x := _vw * 0.47
	var post_base := lerpf(wall_top0, wall_top1, post_x / wx) - 10.0
	_rect(post_x - 3, pl.y - 2, 6, post_base - pl.y + 2, wood_d)
	_rect(post_x - 2, pl.y - 2, 2, post_base - pl.y + 2, wood)
	_poly([Vector2(post_x - 3, pl.y - 4), Vector2(pl.x + 8, pl.y - 6), Vector2(pl.x + 8, pl.y - 1), Vector2(post_x + 3, pl.y + 4)], wood_d)
	_ln(Vector2(post_x + 2, post_base - 20.0), Vector2(pl.x - 2, pl.y + 2), wood_d, 1.0)     # the brace
	# the pulley wheel
	for i in 12:
		var a := TAU * float(i) / 12.0 + (m.winch_angle * 0.4)
		_ln(Vector2(pl.x + 6.0, pl.y + 1.0), Vector2(pl.x + 6.0 + cos(a) * 6.0, pl.y + 1.0 + sin(a) * 6.0), iron, 1.0)
	_rect(pl.x + 4, pl.y - 1, 4, 4, _wood(Color(0.55, 0.55, 0.60)))
	# the winch: frame, drum with rope turns, ratchet, two cranks
	var dc := Vector2(_vw * 0.20, _vh * 0.505)
	var dw := 48.0
	var dh := 28.0
	_rect(dc.x - dw * 0.5 - 4, dc.y - dh * 0.5 + 8, 6, dh + 3, wood_d)          # upright left
	_rect(dc.x + dw * 0.5 - 2, dc.y - dh * 0.5 + 8, 6, dh + 3, wood_d)          # upright right
	_rect(dc.x - dw * 0.5 - 6, dc.y + dh * 0.5 + 9, dw + 12, 4, wood)           # sill
	_rect(dc.x - dw * 0.5, dc.y - dh * 0.5, dw, dh, _wood(Color(0.42, 0.28, 0.14)))
	var turns := int(dw / 4.0)
	for i in turns:
		var xx := dc.x - dw * 0.5 + 2.0 + float(i) * 4.0
		var ph := fposmod(float(i) * 0.7 + m.winch_angle * 0.6, 1.0)
		_rect(xx, dc.y - dh * 0.5 + 1.0, 3.0, dh - 2.0, rope_col(ph))
		_rect(xx + 2.0, dc.y - dh * 0.5 + 1.0, 1.0, dh - 2.0, _wood(Color(0.40, 0.30, 0.18)))
	_rect(dc.x - dw * 0.5 - 3, dc.y - dh * 0.5 - 2, 3, dh + 4, iron)             # flanges
	_rect(dc.x + dw * 0.5, dc.y - dh * 0.5 - 2, 3, dh + 4, iron)
	# the ratchet wheel with its pawl
	for i in 10:
		var a := TAU * float(i) / 10.0 + m.winch_angle
		_rect(dc.x + dw * 0.5 + 5.0 + cos(a) * 5.0, dc.y + sin(a) * 5.0, 2, 2, iron)
	_rect(dc.x + dw * 0.5 + 3, dc.y - 8.0, 8, 2, iron)
	# the cranks: two levers, each pivoting at the drum ends, the hands on the handles
	_draw_lever(Vector2(dc.x - dw * 0.5 - 4.0, dc.y + 2.0), -1.0, wood_l, iron)
	_draw_lever(Vector2(dc.x + dw * 0.5 + 6.0, dc.y + 2.0), 1.0, wood_l, iron)


func rope_col(ph: float) -> Color:
	var a := _wood(Color(0.82, 0.68, 0.42))
	var b := _wood(Color(0.66, 0.52, 0.30))
	return a.lerp(b, ph)


func _draw_lever(pivot: Vector2, side: float, wood_l: Color, iron: Color) -> void:
	# m.lever < 0: the left lever is pulled down, > 0: the right one (the state machine eases it back to 0)
	var pulled := clampf(side * m.lever, 0.0, 1.0)
	var ang := deg_to_rad(-48.0 + 78.0 * pulled)
	var tip := pivot + Vector2(side * 26.0 * cos(ang), 26.0 * sin(ang))
	_ln(pivot, tip, iron, 2.0)
	_rect(tip.x - 3.0, tip.y - 2.0, 6.0, 5.0, wood_l)
	var skin := _wood(Color(0.86, 0.64, 0.46))
	var sleeve := _wood(Color(0.62, 0.20, 0.16))
	_rect(tip.x - 4.0, tip.y - 3.0, 8.0, 6.0, skin)
	_rect(tip.x - 3.0 + side * 4.0, tip.y + 3.0, 8.0, 20.0, sleeve)


func _draw_particles() -> void:
	for p in _parts:
		var d: Dictionary = p
		var a := clampf(float(d["life"]) / float(d["max"]), 0.0, 1.0)
		if str(d["kind"]) == "drip":
			_rect(float(d["x"]), float(d["y"]), 1.0, 2.0, Color(0.70, 0.88, 1.0, a))
		else:
			_rect(float(d["x"]), float(d["y"]), 2.0, 1.0, Color(1.0, 1.0, 1.0, a))


func _splash(at: Vector2, n: int) -> void:
	for i in n:
		if _parts.size() >= MAX_PARTICLES:
			return
		var a := -PI * (0.15 + 0.7 * float(i % 7) / 6.0)
		var sp := 30.0 + float((i * 13) % 31)
		_parts.append({"x": at.x + float((i * 7) % 11) - 5.0, "y": _water_y() if at.y > _water_y() else at.y, "vx": cos(a) * sp * 0.6, "vy": sin(a) * sp, "life": 0.7, "max": 0.7, "kind": "drip"})


func _drips(n: int) -> void:
	var np := _net_pos()
	for i in n:
		if _parts.size() >= MAX_PARTICLES:
			return
		_parts.append({"x": np.x + float((_parts.size() * 5) % 31) - 15.0, "y": np.y + 14.0 + float((_parts.size() * 3) % 9), "vx": 0.0, "vy": 10.0, "life": 0.9, "max": 0.9, "kind": "drip"})


# ---- the barrel and the fish flying into it ----------------------------------------------------------------------------
func _barrel_rect() -> Rect2:
	var k := _k()
	return Rect2(size.x - 210.0 * k, size.y - 250.0 * k, 130.0 * k, 160.0 * k)


func _draw_barrel_and_fly() -> void:
	if m.stage != Manual.Stage.SUMMARY and m.stage != Manual.Stage.UNLOAD:
		return
	var br := _barrel_rect()
	var wood := _wood(Color(0.50, 0.32, 0.15))
	var hoop := Color(0.22, 0.22, 0.26)
	draw_rect(br, wood)
	for i in 6:
		draw_rect(Rect2(br.position.x + br.size.x * float(i) / 6.0, br.position.y, 2, br.size.y), Color(0.30, 0.19, 0.09))
	draw_rect(Rect2(br.position.x - 6, br.position.y + br.size.y * 0.18, br.size.x + 12, 8), hoop)
	draw_rect(Rect2(br.position.x - 6, br.position.y + br.size.y * 0.72, br.size.x + 12, 8), hoop)
	draw_rect(Rect2(br.position.x - 4, br.position.y - 8, br.size.x + 8, 12), Color(0.66, 0.46, 0.25))
	# what is already in the hold, as a heap of silver in the barrel mouth
	var frac := clampf(float(env["hold_kg"]) / maxf(float(env["capacity"]), 1.0), 0.0, 1.0)
	var heap := Color(0.78, 0.86, 0.92)
	draw_rect(Rect2(br.position.x + 4, br.position.y - 8 - 18.0 * frac * _k(), br.size.x - 8, 6 + 18.0 * frac * _k()), heap)
	if m.stage != Manual.Stage.UNLOAD:
		return
	var np := _net_pos()
	var from := _v(np.x, np.y + 20.0)
	var to := br.position + Vector2(br.size.x * 0.5, -6.0)
	for sp in _unload_sprites:
		var d: Dictionary = sp
		var u := clampf((m.stage_t - float(d["t0"])) / 0.9, 0.0, 1.0)
		if u <= 0.0 or u >= 1.0:
			continue
		var pos := from.lerp(to, u) + Vector2(0, -sin(PI * u) * 150.0 * _k())
		var tex := FishArt.texture(str(d["icon"]))
		var w := 72.0 * _k()
		if tex != null:
			draw_texture_rect(tex, Rect2(pos - Vector2(w * 0.5, w * 0.25), Vector2(w, w * 0.5)), false)
		else:
			draw_rect(Rect2(pos, Vector2(w * 0.5, w * 0.2)), Color(0.7, 0.8, 0.9))


# ---- the readable parts -------------------------------------------------------------------------------------------------
func _txt(text: String, pos: Vector2, fsize: int, col: Color, align: int = HORIZONTAL_ALIGNMENT_LEFT, width: float = -1.0) -> void:
	# `pos` is the anchor: the left edge, the centre or the right edge of the text, by `align`. `width` is the room there is: a text
	# that is wider than that is drawn smaller instead of running off the screen.
	if font == null or fsize < 1:
		return
	var fs := fsize
	var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, fs).x
	if width > 0.0 and w > width:
		fs = maxi(int(floorf(float(fs) * width / w)), 8)
		w = font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, fs).x
	var x := pos.x
	if align == HORIZONTAL_ALIGNMENT_CENTER:
		x -= w * 0.5
	elif align == HORIZONTAL_ALIGNMENT_RIGHT:
		x -= w
	draw_string(font, Vector2(x + 2.0, pos.y + 2.0), text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, fs, Color(0, 0, 0, 0.75))
	draw_string(font, Vector2(x, pos.y), text, HORIZONTAL_ALIGNMENT_LEFT, -1.0, fs, col)


func _box(r: Rect2, col: Color = PANEL, edge: Color = PANEL_EDGE) -> void:
	draw_rect(Rect2(r.position + Vector2(4, 5), r.size), Color(0, 0, 0, 0.35))
	draw_rect(r, col)
	draw_rect(r, edge, false, 3.0)


func _key_label(action: String) -> String:
	return str((env["keys"] as Dictionary).get(action, "?"))


func _draw_hud() -> void:
	var k := _k()
	var vw := size.x
	var vh := size.y
	var fs := int(roundf(22.0 * k))
	var st := m.stage
	# the stage ribbon (top left) and the hold (top right)
	var labels := ["1  CAST", "2  HAUL", "3  RAISE"]
	var cur := 0 if st <= Manual.Stage.SOAK else (1 if st == Manual.Stage.HAUL else 2)
	var x := 24.0 * k
	_box(Rect2(x - 8.0 * k, 16.0 * k, 560.0 * k, 78.0 * k))
	_txt("FISHING AT THE WINCH  -  %s" % str(env["ground"]), Vector2(x, 44.0 * k), int(roundf(24.0 * k)), GOLD)
	for i in 3:
		var on := i == cur and st != Manual.Stage.FAIL and st != Manual.Stage.CANCEL
		var col := GOLD if on else Color(0.62, 0.58, 0.50)
		var bx := x + float(i) * 176.0 * k
		draw_rect(Rect2(bx, 56.0 * k, 164.0 * k, 28.0 * k), Color(0.28, 0.20, 0.08, 0.95) if on else Color(0.14, 0.11, 0.08, 0.9))
		_txt(labels[i], Vector2(bx + 10.0 * k, 77.0 * k), fs, col)
	var hold := "Hold  %.1f / %.0f kg" % [float(env["hold_kg"]), float(env["capacity"])]
	_box(Rect2(vw - 330.0 * k, 16.0 * k, 306.0 * k, 46.0 * k))
	_txt(hold, Vector2(vw - 316.0 * k, 48.0 * k), fs, CREAM)
	# the hint line (bottom)
	var hint := _hint_text()
	if hint != "":
		_txt(hint, Vector2(vw * 0.5, vh - 22.0 * k), int(roundf(20.0 * k)), Color(0.90, 0.86, 0.74), HORIZONTAL_ALIGNMENT_CENTER, vw * 0.68)
	# the banner
	if _banner_t > 0.0 and _banner != "":
		var a := clampf(_banner_t / 0.4, 0.0, 1.0)
		var c := Color(_banner_col.r, _banner_col.g, _banner_col.b, a)
		_txt(_banner, Vector2(vw * 0.5, vh * 0.20), int(roundf(46.0 * k)), c, HORIZONTAL_ALIGNMENT_CENTER, vw)
	match st:
		Manual.Stage.HEAVE:
			_panel_text("HEAVING TO", m.heave_note + "  (Esc: leave the winch)", k)
		Manual.Stage.AIM:
			_draw_aim(k)
		Manual.Stage.SINK:
			_panel_text("THE NET GOES DOWN", "Cast: %s" % m.cast_grade, k)
		Manual.Stage.SOAK:
			var dots := ".".repeat(1 + int(_t * 3.0) % 3)
			_panel_text("THE SHOAL GATHERS" + dots, "Get ready: pull the levers one after the other.", k)
		Manual.Stage.HAUL:
			_draw_haul(k)
		Manual.Stage.RAISE:
			_draw_bar(Rect2(vw * 0.5 - 240.0 * k, vh - 150.0 * k, 480.0 * k, 34.0 * k), clampf(1.0 - m.depth / maxf(m._raise_from, 0.01), 0.0, 1.0), GOLD, "RAISING THE NET", k)
		Manual.Stage.SUMMARY:
			_draw_summary(k)
		Manual.Stage.UNLOAD:
			_panel_text("UNLOADING INTO THE BARRELS", "%d fish, %.1f kg" % [int(m.result.get("count", 0)), float(m.result.get("kg", 0.0))], k)
		Manual.Stage.FAIL:
			_draw_fail(k)
		Manual.Stage.CANCEL:
			_panel_text("HAULING THE NET BACK", "Nothing is lost: try again.", k)


func _hint_text() -> String:
	match m.stage:
		Manual.Stage.AIM:
			return "%s: cast the net      %s: let go of the winch" % [_key_label("fish_cast"), _key_label("fish_cancel")]
		Manual.Stage.HAUL:
			return "%s and %s: pull the levers one after the other      %s: let go (the net comes back empty)" % [_key_label("fish_haul_left"), _key_label("fish_haul_right"), _key_label("fish_cancel")]
		Manual.Stage.SUMMARY:
			return "%s or %s: unload into the barrels" % [_key_label("ship_interact"), _key_label("fish_cast")]
		Manual.Stage.FAIL:
			return "%s: back to the deck" % _key_label("ship_interact")
		Manual.Stage.HEAVE, Manual.Stage.SINK, Manual.Stage.SOAK:
			return "%s: let go of the winch" % _key_label("fish_cancel")
	return ""


func _panel_text(title: String, sub: String, k: float) -> void:
	var vw := size.x
	var vh := size.y
	var r := Rect2(vw * 0.5 - 360.0 * k, vh - 190.0 * k, 720.0 * k, 110.0 * k)
	_box(r)
	_txt(title, Vector2(vw * 0.5, r.position.y + 48.0 * k), int(roundf(32.0 * k)), GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	_txt(sub, Vector2(vw * 0.5, r.position.y + 86.0 * k), int(roundf(22.0 * k)), CREAM, HORIZONTAL_ALIGNMENT_CENTER, r.size.x - 20.0 * k)


func _draw_bar(r: Rect2, frac: float, col: Color, label: String, k: float) -> void:
	draw_rect(Rect2(r.position + Vector2(3, 4), r.size), Color(0, 0, 0, 0.4))
	draw_rect(r, Color(0.06, 0.05, 0.04, 0.95))
	draw_rect(Rect2(r.position + Vector2(3, 3), Vector2((r.size.x - 6.0) * clampf(frac, 0.0, 1.0), r.size.y - 6.0)), col)
	draw_rect(r, PANEL_EDGE, false, 3.0)
	_txt(label, Vector2(r.position.x + r.size.x * 0.5, r.position.y - 8.0 * k), int(roundf(22.0 * k)), CREAM, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)


# ---- stage 1: the casting needle ------------------------------------------------------------------------------------------
func _draw_aim(k: float) -> void:
	var vw := size.x
	var vh := size.y
	var r := Rect2(vw * 0.5 - 330.0 * k, vh - 220.0 * k, 660.0 * k, 130.0 * k)
	_box(r)
	_txt("CAST THE NET", Vector2(vw * 0.5, r.position.y + 38.0 * k), int(roundf(30.0 * k)), GOLD, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	var bar := Rect2(r.position.x + 30.0 * k, r.position.y + 58.0 * k, r.size.x - 60.0 * k, 32.0 * k)
	draw_rect(bar, Color(0.10, 0.08, 0.06))
	var half := float(m.p["aim_good_half"])
	# fair zone, good zone, perfect zone
	for z in [[2.2, Color(0.55, 0.50, 0.15)], [1.0, Color(0.20, 0.55, 0.25)], [0.4, Color(0.35, 0.90, 0.45)]]:
		var hw := half * float(z[0]) * bar.size.x
		draw_rect(Rect2(bar.position.x + bar.size.x * 0.5 - hw, bar.position.y, hw * 2.0, bar.size.y), z[1])
	draw_rect(bar, PANEL_EDGE, false, 3.0)
	var nx := bar.position.x + bar.size.x * m.aim
	draw_rect(Rect2(nx - 4.0 * k, bar.position.y - 10.0 * k, 8.0 * k, bar.size.y + 20.0 * k), Color(1.0, 0.95, 0.80))
	_txt("%s" % _key_label("fish_cast"), Vector2(vw * 0.5, r.position.y + 118.0 * k), int(roundf(22.0 * k)), CREAM, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)


# ---- stage 2: the haul ----------------------------------------------------------------------------------------------------
func _draw_haul(k: float) -> void:
	var vw := size.x
	var vh := size.y
	var fs := int(roundf(22.0 * k))
	# progress
	_draw_bar(Rect2(vw * 0.5 - 240.0 * k, vh - 150.0 * k, 480.0 * k, 36.0 * k), m.progress, GREEN if m.integrity > 0.5 else AMBER, "THE NET   %d%%" % int(roundf(m.progress * 100.0)), k)
	# the message
	if m.message != "":
		var mc := GREEN if m.message_kind == "ok" else (AMBER if m.message_kind == "warn" else RED)
		_txt(m.message, Vector2(vw * 0.5, vh - 184.0 * k), int(roundf(28.0 * k)), mc, HORIZONTAL_ALIGNMENT_CENTER, vw * 0.68)
	# the two levers: which one is next
	var nextv := m.next_lever()
	for i in 2:
		var side := "left" if i == 0 else "right"
		var cx := vw * 0.5 + (-1.0 if i == 0 else 1.0) * 330.0 * k
		var r := Rect2(cx - 48.0 * k, vh - 170.0 * k, 96.0 * k, 96.0 * k)
		var on := nextv == side
		draw_rect(Rect2(r.position + Vector2(3, 4), r.size), Color(0, 0, 0, 0.4))
		draw_rect(r, Color(0.40, 0.28, 0.10, 0.96) if on else Color(0.14, 0.11, 0.08, 0.92))
		draw_rect(r, GOLD if on else PANEL_EDGE, false, 4.0 if on else 3.0)
		_txt(_key_label("fish_haul_left" if i == 0 else "fish_haul_right"), Vector2(r.position.x + r.size.x * 0.5, r.position.y + r.size.y * 0.64), int(roundf(52.0 * k)), GOLD if on else CREAM, HORIZONTAL_ALIGNMENT_CENTER, r.size.x)
	# the rope tension meter (right edge): slack | band | strained, the needle, and the strain under it
	var mx := vw - 118.0 * k
	var my := 120.0 * k
	var mh := 360.0 * k
	var mw := 54.0 * k
	_box(Rect2(mx - 18.0 * k, my - 44.0 * k, mw + 36.0 * k, mh + 150.0 * k))
	_txt("ROPE", Vector2(mx + mw * 0.5, my - 14.0 * k), fs, CREAM, HORIZONTAL_ALIGNMENT_CENTER, mw + 30.0 * k)
	var lo := float(m.p["band_lo"])
	var hi := float(m.p["band_hi"])
	var yv := func(t: float) -> float: return my + mh * (1.0 - clampf(t, 0.0, 1.1) / 1.1)
	draw_rect(Rect2(mx, my, mw, mh), Color(0.08, 0.07, 0.06))
	draw_rect(Rect2(mx, yv.call(1.1), mw, yv.call(hi) - yv.call(1.1)), Color(0.55, 0.14, 0.12))
	draw_rect(Rect2(mx, yv.call(hi), mw, yv.call(lo) - yv.call(hi)), Color(0.18, 0.50, 0.24))
	draw_rect(Rect2(mx, yv.call(lo), mw, yv.call(0.0) - yv.call(lo)), Color(0.18, 0.30, 0.52))
	draw_rect(Rect2(mx, my, mw, mh), PANEL_EDGE, false, 3.0)
	var ny := float(yv.call(m.tension))
	var nc := GREEN if (m.tension >= lo and m.tension <= hi) else (RED if m.tension > hi else Color(0.5, 0.7, 1.0))
	draw_rect(Rect2(mx - 12.0 * k, ny - 4.0 * k, mw + 24.0 * k, 8.0 * k), nc)
	_txt("tight", Vector2(mx + mw * 0.5, my + 22.0 * k), int(roundf(17.0 * k)), Color(1, 0.8, 0.7), HORIZONTAL_ALIGNMENT_CENTER, mw + 30.0 * k)
	_txt("slack", Vector2(mx + mw * 0.5, my + mh - 8.0 * k), int(roundf(17.0 * k)), Color(0.75, 0.88, 1.0), HORIZONTAL_ALIGNMENT_CENTER, mw + 30.0 * k)
	# strain (will it snap?) and what is left of the shoal
	var by := my + mh + 26.0 * k
	_mini_bar(Rect2(mx - 6.0 * k, by, mw + 12.0 * k, 16.0 * k), m.strain, Color(1.0, 0.45, 0.25), "STRAIN", k)
	_mini_bar(Rect2(mx - 6.0 * k, by + 52.0 * k, mw + 12.0 * k, 16.0 * k), m.integrity, Color(0.45, 0.85, 0.95), "CATCH", k)
	# the rhythm and the streak (left edge)
	var lx := 24.0 * k
	var ly := 120.0 * k
	_box(Rect2(lx - 8.0 * k, ly - 8.0 * k, 252.0 * k, 232.0 * k))
	_txt("RHYTHM", Vector2(lx, ly + 24.0 * k), fs, CREAM)
	var pr := m.pace_ratio()
	var gx := Rect2(lx, ly + 40.0 * k, 232.0 * k, 24.0 * k)
	draw_rect(gx, Color(0.08, 0.07, 0.06))
	draw_rect(Rect2(gx.position.x + gx.size.x * 0.35, gx.position.y, gx.size.x * 0.3, gx.size.y), Color(0.20, 0.52, 0.26))
	draw_rect(gx, PANEL_EDGE, false, 2.0)
	if pr >= 0.0:
		var px := gx.position.x + gx.size.x * clampf(pr / 2.0, 0.0, 1.0)
		draw_rect(Rect2(px - 3.0 * k, gx.position.y - 5.0 * k, 6.0 * k, gx.size.y + 10.0 * k), Color(1, 0.95, 0.8))
	_txt("slow", Vector2(lx, ly + 84.0 * k), int(roundf(17.0 * k)), Color(0.75, 0.88, 1.0))
	_txt("fast", Vector2(lx + 232.0 * k, ly + 84.0 * k), int(roundf(17.0 * k)), Color(1, 0.8, 0.7), HORIZONTAL_ALIGNMENT_RIGHT)
	_txt("STREAK  x%d" % m.streak, Vector2(lx, ly + 126.0 * k), int(roundf(28.0 * k)), GOLD if m.streak >= 8 else CREAM)
	_txt("best %d   pulls %d" % [m.best_streak, m.pulls], Vector2(lx, ly + 158.0 * k), int(roundf(19.0 * k)), Color(0.82, 0.78, 0.68))
	var eff := clampf(float(m.p["par_s"]) / maxf(m.haul_t, 0.1), 0.0, 1.0) if m.progress > 0.05 else 1.0
	_txt("pace %d%%   time %.1f s" % [int(roundf(eff * 100.0)), m.haul_t], Vector2(lx, ly + 190.0 * k), int(roundf(19.0 * k)), Color(0.82, 0.78, 0.68))


func _mini_bar(r: Rect2, frac: float, col: Color, label: String, k: float) -> void:
	draw_rect(r, Color(0.06, 0.05, 0.04))
	draw_rect(Rect2(r.position + Vector2(2, 2), Vector2((r.size.x - 4.0) * clampf(frac, 0.0, 1.0), r.size.y - 4.0)), col)
	draw_rect(r, PANEL_EDGE, false, 2.0)
	_txt(label, Vector2(r.position.x + r.size.x * 0.5, r.position.y + r.size.y + 20.0 * k), int(roundf(17.0 * k)), CREAM, HORIZONTAL_ALIGNMENT_CENTER, r.size.x + 40.0 * k)


# ---- stage 3: the catch card ---------------------------------------------------------------------------------------------
func _draw_summary(k: float) -> void:
	var res := m.result
	var fish: Array = res.get("fish", [])
	var rows := maxi(fish.size(), 1)
	var rh := 56.0 * k
	# the card sits on the left so the net, with the real fish in it, stays in view on the right
	var card := Rect2(24.0 * k, 150.0 * k, 560.0 * k, 230.0 * k + rh * float(rows))
	_box(card)
	var gcol := GREEN if str(res.get("grade", "")) in ["Excellent", "Good"] else (AMBER if str(res.get("grade", "")) == "Fair" else RED)
	_txt("THE CATCH", Vector2(card.position.x + 28.0 * k, card.position.y + 46.0 * k), int(roundf(34.0 * k)), GOLD)
	_txt(str(res.get("grade", "")).to_upper(), Vector2(card.end.x - 28.0 * k, card.position.y + 46.0 * k), int(roundf(34.0 * k)), gcol, HORIZONTAL_ALIGNMENT_RIGHT)
	var y := card.position.y + 70.0 * k
	var names: Dictionary = env["names"]
	if fish.is_empty():
		_txt("The net came up empty: the shoal was too thin.", Vector2(card.position.x + 28.0 * k, y + 40.0 * k), int(roundf(24.0 * k)), CREAM)
		y += rh
	for f in fish:
		var d: Dictionary = f
		var tex := FishArt.texture(_icon_of(str(d["species"])))
		var icon := Rect2(card.position.x + 28.0 * k, y + 4.0 * k, 96.0 * k, 48.0 * k)
		if tex != null:
			draw_texture_rect(tex, icon, false)
		_txt(str(names.get(str(d["species"]), str(d["species"]))), Vector2(icon.end.x + 18.0 * k, y + 36.0 * k), int(roundf(28.0 * k)), CREAM)
		_txt("x %d" % int(d["count"]), Vector2(card.end.x - 190.0 * k, y + 36.0 * k), int(roundf(30.0 * k)), GOLD, HORIZONTAL_ALIGNMENT_RIGHT, 100.0 * k)
		_txt("%.1f kg" % float(d["kg"]), Vector2(card.end.x - 28.0 * k, y + 36.0 * k), int(roundf(26.0 * k)), Color(0.85, 0.80, 0.70), HORIZONTAL_ALIGNMENT_RIGHT)
		y += rh
	draw_rect(Rect2(card.position.x + 24.0 * k, y + 2.0 * k, card.size.x - 48.0 * k, 2.0), PANEL_EDGE)
	_txt("Total  %d fish, %.1f kg" % [int(res.get("count", 0)), float(res.get("kg", 0.0))], Vector2(card.position.x + 28.0 * k, y + 38.0 * k), int(roundf(28.0 * k)), CREAM)
	_txt("%s  |  pace %d%%  |  best streak %d  |  catch left %d%%" % [str(res.get("cast", "")), int(roundf(float(res.get("efficiency", 0.0)) * 100.0)), int(res.get("best_streak", 0)), int(roundf(float(res.get("integrity", 0.0)) * 100.0))], Vector2(card.position.x + 28.0 * k, y + 72.0 * k), int(roundf(19.0 * k)), Color(0.82, 0.78, 0.68))
	var room := maxf(float(env["capacity"]) - float(env["hold_kg"]), 0.0)
	var fits := "Room in the hold: %.1f kg" % room
	if float(res.get("kg", 0.0)) > room + 0.01:
		fits = "The hold has room for only %.1f kg: the rest goes back into the sea." % room
	_txt(fits, Vector2(card.position.x + 28.0 * k, y + 104.0 * k), int(roundf(20.0 * k)), AMBER if float(res.get("kg", 0.0)) > room + 0.01 else Color(0.82, 0.78, 0.68))


func _draw_fail(k: float) -> void:
	var vw := size.x
	var vh := size.y
	var card := Rect2(vw * 0.5 - 340.0 * k, vh * 0.5 - 140.0 * k, 680.0 * k, 280.0 * k)
	_box(card, Color(0.16, 0.06, 0.05, 0.94), Color(0.75, 0.25, 0.20))
	_txt("THE HAUL WAS LOST", Vector2(vw * 0.5, card.position.y + 52.0 * k), int(roundf(36.0 * k)), RED, HORIZONTAL_ALIGNMENT_CENTER, card.size.x)
	if font != null:
		draw_multiline_string(font, Vector2(card.position.x + 30.0 * k, card.position.y + 100.0 * k), m.fail_text, HORIZONTAL_ALIGNMENT_LEFT, card.size.x - 60.0 * k, int(roundf(23.0 * k)), 5, CREAM)
	_txt("%s: back to the deck" % _key_label("ship_interact"), Vector2(vw * 0.5, card.end.y - 22.0 * k), int(roundf(22.0 * k)), GOLD, HORIZONTAL_ALIGNMENT_CENTER, card.size.x)
