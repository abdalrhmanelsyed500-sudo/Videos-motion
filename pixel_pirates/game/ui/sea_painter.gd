extends RefCounted
## Procedural sea view for the E1 slice: sky, sun and moon, clouds, waves, rain, fog, ice, icebergs, wildlife
## silhouettes, a polygon placeholder ship and the fog-of-war chart. Plain 2D draw calls only (no shaders, no 3D), so it
## runs on the dev PC (Intel HD 3000, Compatibility renderer); final art replaces the polygons, never the data.
## Everything is drawn in a 640 x 360 logical space. All inputs arrive in one Dictionary `v`, produced by
## ui/ocean_slice.gd: light, floor, hour, cloud, storm, herald, rain, fog, ice, wave_m, wind_kn, wind_from_deg,
## heading_deg, look (Ocean.look_at), time (real seconds). Nothing here reads game state, so it is not game logic.
## NOT YET RUN IN GODOT: the first run on the dev PC is the first test (docs/E1_WORLD_SPEC.md).
const Ocean := preload("res://core/ocean.gd")
const W := 640.0
const H := 360.0
const HORIZON := 140.0
const FOV_DEG := 55.0
const FONT_SIZE := 12
const SKY_STRIPS := 24
const SEA_STRIPS := 22
const WAVE_ROWS := 17
const WAVE_STEP_PX := 16.0
const SHIP_POS := Vector2(320.0, 268.0)
const CHART_RECT := Rect2(50.0, 0.0, 540.0, 360.0)


static func rgb(a: Array) -> Color:
	return Color(float(a[0]), float(a[1]), float(a[2]))


## Colour under the current light: full colour by day, a dark blue-shifted version at night.
static func lit(c: Color, light: float, floor_v: float) -> Color:
	var k := clampf((light - floor_v) / maxf(1.0 - floor_v, 0.001), 0.0, 1.0)
	k = pow(k, 0.55)  # dawn and dusk stay readable: half light looks like 0.68, not 0.5
	var night := Color(c.r * 0.22, c.g * 0.30, c.b * 0.55, c.a)
	return night.lerp(c, k)


## Filled polygon from a flat coordinate list [x0, y0, x1, y1, ...], scaled by sc and moved to origin.
static func fpoly(cv: CanvasItem, xy: Array, col: Color, origin: Vector2 = Vector2.ZERO, sc: float = 1.0) -> void:
	var pts := PackedVector2Array()
	for i in range(0, xy.size(), 2):
		pts.append(origin + Vector2(float(xy[i]), float(xy[i + 1])) * sc)
	cv.draw_colored_polygon(pts, col)


static func text(
		cv: CanvasItem, pos: Vector2, s: String, col: Color = Color(0.95, 0.93, 0.85), size: int = FONT_SIZE) -> void:
	var font: Font = ThemeDB.fallback_font
	cv.draw_string(font, pos + Vector2(1, 1), s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(0, 0, 0, 0.75))
	cv.draw_string(font, pos, s, HORIZONTAL_ALIGNMENT_LEFT, -1, size, col)


# ---- sky -----------------------------------------------------------------------------------------
static func sky_colors(v: Dictionary) -> Array:
	var look: Dictionary = v["look"]
	var light: float = v["light"]
	var day := rgb(look["sky_day"])
	var dusk := rgb(look["sky_dusk"])
	var night := rgb(look["sky_night"])
	var twilight := clampf(4.0 * light * (1.0 - light), 0.0, 1.0)
	var blend := clampf((light - float(v["floor"])) / 0.35, 0.0, 1.0)
	var top := night.lerp(day.lerp(dusk, twilight), blend)
	var grey := Color(top.get_luminance(), top.get_luminance(), top.get_luminance())
	top = top.lerp(grey, 0.5 * float(v["cloud"])).darkened(0.45 * float(v["storm"]))
	var fogc := lit(rgb(look["fog_color"]), light, float(v["floor"]))
	var hor := top.lerp(fogc, 0.3 + 0.55 * float(v["fog"])).lightened(0.12 * (1.0 - twilight))
	return [top, hor]


static func sky(cv: CanvasItem, v: Dictionary) -> void:
	var cols := sky_colors(v)
	var top: Color = cols[0]
	var hor: Color = cols[1]
	var sh := HORIZON / float(SKY_STRIPS)
	for i in SKY_STRIPS:
		var f := pow(float(i) / float(SKY_STRIPS - 1), 1.6)
		cv.draw_rect(Rect2(0.0, float(i) * sh, W, sh + 1.0), top.lerp(hor, f))
	var light: float = v["light"]
	var cloud: float = v["cloud"]
	if light < 0.35:
		var a := (0.35 - light) / 0.35 * (1.0 - 0.9 * cloud)
		for i in 70:
			var sx := Ocean.hash01(i, 1, 0, 77) * W
			var sy := Ocean.hash01(i, 2, 0, 77) * (HORIZON - 12.0)
			var tw := 0.6 + 0.4 * sin(float(v["time"]) * (1.0 + Ocean.hash01(i, 3, 0, 77)) + float(i))
			cv.draw_rect(Rect2(sx, sy, 1.0, 1.0), Color(1, 1, 0.92, a * tw))
	_sun_moon(cv, v)
	_clouds(cv, v)


static func _sun_moon(cv: CanvasItem, v: Dictionary) -> void:
	var hour: float = v["hour"]
	var veil := 1.0 - 0.85 * float(v["cloud"]) - 0.4 * float(v["fog"])
	if veil <= 0.05:
		return
	if hour > 5.0 and hour < 19.0:
		var f := (hour - 5.0) / 14.0
		var pos := Vector2(60.0 + f * 520.0, HORIZON - sin(f * PI) * 118.0 + 4.0)
		var warm := clampf(4.0 * f * (1.0 - f), 0.0, 1.0)
		var col := Color(1.0, 0.82, 0.55).lerp(Color(1.0, 0.97, 0.85), warm)
		cv.draw_circle(pos, 26.0, Color(col.r, col.g, col.b, 0.10 * veil))
		cv.draw_circle(pos, 17.0, Color(col.r, col.g, col.b, 0.18 * veil))
		cv.draw_circle(pos, 9.0, Color(col.r, col.g, col.b, veil))
	else:
		var f2 := fposmod(hour - 19.0, 24.0) / 10.0
		if f2 < 1.0:
			var mp := Vector2(60.0 + f2 * 520.0, HORIZON - sin(f2 * PI) * 100.0 + 4.0)
			cv.draw_circle(mp, 14.0, Color(0.8, 0.85, 1.0, 0.10 * veil))
			cv.draw_circle(mp, 7.0, Color(0.92, 0.94, 1.0, veil))


static func _clouds(cv: CanvasItem, v: Dictionary) -> void:
	var cloud: float = v["cloud"]
	var n := int(3.0 + cloud * 11.0)
	var base := lit(Color(0.95, 0.95, 0.97), float(v["light"]), float(v["floor"])).darkened(0.5 * float(v["storm"]))
	for i in n:
		var speed := 2.0 + 4.0 * Ocean.hash01(i, 4, 0, 78) + float(v["wind_kn"]) * 0.15
		var cx := fposmod(Ocean.hash01(i, 5, 0, 78) * (W + 160.0) + float(v["time"]) * speed, W + 160.0) - 80.0
		var cy := 18.0 + Ocean.hash01(i, 6, 0, 78) * (HORIZON - 56.0)
		var r := 12.0 + 16.0 * Ocean.hash01(i, 7, 0, 78) * (0.5 + cloud)
		var a := 0.30 + 0.5 * cloud
		for k in 4:
			var off := Vector2((float(k) - 1.5) * r * 0.9, -absf(float(k) - 1.5) * r * 0.25)
			cv.draw_circle(Vector2(cx, cy) + off, r * (1.0 - 0.15 * absf(float(k) - 1.5)), Color(base.r, base.g, base.b, a))


# ---- sea -----------------------------------------------------------------------------------------
static func sea(cv: CanvasItem, v: Dictionary) -> void:
	var look: Dictionary = v["look"]
	var light: float = v["light"]
	var fl: float = v["floor"]
	var deep := lit(rgb(look["deep"]), light, fl)
	var shallow := lit(rgb(look["shallow"]), light, fl)
	var hor: Color = sky_colors(v)[1]
	var sh := (H - HORIZON) / float(SEA_STRIPS)
	for i in SEA_STRIPS:
		var f := float(i) / float(SEA_STRIPS - 1)
		var col := hor.lerp(shallow.lerp(deep, minf(1.0, f * 1.6)), clampf(f * 3.0, 0.0, 1.0))
		cv.draw_rect(Rect2(0.0, HORIZON + float(i) * sh, W, sh + 1.0), col)
	_waves(cv, v, deep, shallow)


static func _waves(cv: CanvasItem, v: Dictionary, deep: Color, shallow: Color) -> void:
	var look: Dictionary = v["look"]
	var wave_m: float = v["wave_m"]
	var herald: float = v["herald"]
	var t: float = v["time"]
	var wscale := float(look["wave_scale"])
	var amp_max := clampf(wave_m * 3.0 * wscale, 0.6, 20.0)
	var foam_col := lit(Color(0.95, 0.98, 1.0), float(v["light"]), float(v["floor"]))
	var crest_limit := 0.97 - 0.12 * clampf((float(v["wind_kn"]) - 10.0) / 25.0, 0.0, 1.0) - 0.08 * float(v["storm"])
	for r in WAVE_ROWS:
		var f := float(r) / float(WAVE_ROWS - 1)
		var y := HORIZON + 4.0 + (H - HORIZON - 4.0) * pow(f, 1.8)
		var amp := amp_max * (0.12 + 0.88 * f)
		var wl := (14.0 + 150.0 * f) * (1.0 + 1.3 * herald)
		var ph := t * (0.5 + 0.7 * f) + float(r) * 1.7
		var col := deep.lerp(shallow, 0.35 * (1.0 - f)).lightened(0.10 + 0.06 * f)
		var pts := PackedVector2Array()
		var x := -WAVE_STEP_PX
		while x <= W + WAVE_STEP_PX:
			var s1 := sin(x / wl * TAU + ph)
			var s2 := sin(x / (wl * 0.43) * TAU - ph * 1.3 + float(r))
			var yy := y + amp * (0.7 * s1 + 0.3 * s2)
			pts.append(Vector2(x, yy))
			if s1 * 0.7 + s2 * 0.3 > crest_limit * 0.7 and wave_m > 1.2:
				cv.draw_line(Vector2(x - 2.0 - 3.0 * f, yy), Vector2(x + 2.0 + 3.0 * f, yy), foam_col, 1.0 + f)
			x += WAVE_STEP_PX
		cv.draw_polyline(pts, col, 1.0 + f)


# ---- ice -----------------------------------------------------------------------------------------
static func ice(cv: CanvasItem, v: Dictionary) -> void:
	var ic: float = v["ice"]
	if ic < 0.04:
		return
	var col := lit(Color(0.88, 0.95, 1.0), float(v["light"]), float(v["floor"]))
	var n := int(ic * 46.0)
	var drift := float(v["time"]) * 3.0
	for i in n:
		var f := pow(Ocean.hash01(i, 1, 0, 91), 0.8)
		var y := HORIZON + 6.0 + (H - HORIZON - 6.0) * f
		var x := fposmod(Ocean.hash01(i, 2, 0, 91) * (W + 120.0) - drift * (0.3 + f), W + 120.0) - 60.0
		var rw := (5.0 + 26.0 * Ocean.hash01(i, 3, 0, 91)) * (0.25 + f)
		var rh := rw * 0.28
		fpoly(cv, [x - rw, y, x - rw * 0.5, y - rh, x + rw * 0.6, y - rh * 0.8, x + rw, y, x + rw * 0.4, y + rh * 0.6,
				x - rw * 0.6, y + rh * 0.5], col)
	if ic > 0.85:
		cv.draw_rect(Rect2(0.0, HORIZON + 2.0, W, H - HORIZON), Color(col.r, col.g, col.b, (ic - 0.85) / 0.15 * 0.8))


## Icebergs: each entry {rel: degrees off the bow, dist: km, size: 1..4}.
static func bergs(cv: CanvasItem, v: Dictionary, list: Array) -> void:
	var light: float = v["light"]
	var fl: float = v["floor"]
	var vis: float = v["visibility_km"]
	for b in list:
		var rel: float = b["rel"]
		var dist: float = b["dist"]
		if absf(rel) > FOV_DEG + 6.0 or dist > vis:
			continue
		var t := clampf(1.0 - dist / 14.0, 0.0, 1.0)
		var x := W * 0.5 + rel / FOV_DEG * W * 0.5
		var y := HORIZON + 3.0 + 50.0 * t * t
		var hgt := (6.0 + 11.0 * float(b["size"])) * (0.35 + 1.6 * t * t)
		var wid := hgt * 1.4
		var a := clampf(1.2 - dist / maxf(vis, 0.1), 0.15, 1.0)
		var body := lit(Color(0.86, 0.93, 1.0), light, fl)
		var shade := lit(Color(0.55, 0.7, 0.86), light, fl)
		var o := Vector2(x, y)
		fpoly(cv, [-wid * 0.5, 0.0, -wid * 0.3, -hgt * 0.6, -wid * 0.05, -hgt, wid * 0.25, -hgt * 0.7, wid * 0.5, 0.0],
				Color(body.r, body.g, body.b, a), o)
		fpoly(cv, [-wid * 0.05, -hgt, wid * 0.25, -hgt * 0.7, wid * 0.5, 0.0, wid * 0.1, 0.0],
				Color(shade.r, shade.g, shade.b, a), o)


# ---- weather -------------------------------------------------------------------------------------
static func rain(cv: CanvasItem, v: Dictionary) -> void:
	var r: float = v["rain"]
	if r < 0.05:
		return
	var n := int(r * 150.0)
	var t: float = v["time"]
	var slant := clampf(float(v["wind_kn"]) / 40.0, 0.0, 1.0) * 10.0
	var col := Color(0.75, 0.82, 0.9, 0.35 + 0.25 * r)
	for i in n:
		var x := fposmod(Ocean.hash01(i, 1, 0, 61) * W + t * 40.0 * slant * 0.2, W)
		var y := fposmod(Ocean.hash01(i, 2, 0, 61) * H + t * (260.0 + 120.0 * Ocean.hash01(i, 3, 0, 61)), H)
		cv.draw_line(Vector2(x, y), Vector2(x - slant * 0.6, y + 7.0), col, 1.0)


static func fog(cv: CanvasItem, v: Dictionary) -> void:
	var f: float = v["fog"]
	if f < 0.04:
		return
	var fc := lit(rgb(v["look"]["fog_color"]), float(v["light"]), float(v["floor"]))
	cv.draw_rect(Rect2(0.0, 0.0, W, H), Color(fc.r, fc.g, fc.b, clampf(f * 0.55, 0.0, 0.6)))
	for i in 8:
		var yy := HORIZON - 30.0 + float(i) * 12.0
		var band_a := clampf(f * 0.4, 0.0, 0.45) * (1.0 - absf(float(i) - 3.5) / 5.0)
		cv.draw_rect(Rect2(0.0, yy, W, 13.0), Color(fc.r, fc.g, fc.b, band_a))


## A rare, dim flash: at most a short pulse every few seconds, never a full-white strobe.
static func lightning(cv: CanvasItem, v: Dictionary) -> void:
	var s: float = v["storm"]
	if s < 0.5:
		return
	var slot := int(floorf(float(v["time"]) * 1.5))
	if Ocean.hash01(slot, 1, 0, 51) > 0.07 * s:
		return
	var ph := fposmod(float(v["time"]) * 1.5, 1.0)
	cv.draw_rect(Rect2(0.0, 0.0, W, H), Color(0.85, 0.9, 1.0, 0.22 * (1.0 - ph)))


# ---- the ship (placeholder polygons; final art replaces them) --------------------------------------
static func ship(cv: CanvasItem, v: Dictionary) -> void:
	var t: float = v["time"]
	var light: float = v["light"]
	var fl: float = v["floor"]
	var rel_wind := wrapf(float(v["wind_from_deg"]) - float(v["heading_deg"]), -180.0, 180.0)
	var wind_f := clampf(float(v["wind_kn"]) / 30.0, 0.0, 1.0)
	var heel := signf(rel_wind) * wind_f * 0.16 * sin(deg_to_rad(absf(rel_wind)))
	var roll := sin(t * 0.9) * 0.025 * (0.4 + float(v["wave_m"]) * 0.6) + heel
	var bob := sin(t * 1.3) * (0.4 + float(v["wave_m"]) * 0.7)
	cv.draw_set_transform(SHIP_POS + Vector2(0.0, bob), roll, Vector2.ONE)
	var hull := lit(Color("#5a3c28"), light, fl)
	var hull_dark := lit(Color("#3a281c"), light, fl)
	var deck := lit(Color("#8a6a45"), light, fl)
	var sail := lit(Color("#e8dcc0"), light, fl)
	var sail_shade := lit(Color("#bfae8c"), light, fl)
	fpoly(cv, [-34, -6, 34, -6, 26, 16, -26, 16], hull)
	fpoly(cv, [-34, -6, 34, -6, 31, -2, -31, -2], deck)
	cv.draw_rect(Rect2(-26.0, 9.0, 52.0, 3.0), hull_dark)
	cv.draw_rect(Rect2(-1.5, -64.0, 3.0, 58.0), hull_dark)
	var billow := clampf(sin(deg_to_rad(absf(rel_wind))), 0.0, 1.0) * wind_f * 9.0 + 2.0
	var skew := clampf(rel_wind / 90.0, -1.0, 1.0) * 6.0
	var belly := -34.0 - billow * 0.2
	fpoly(cv, [-22, -60, 22, -60, 26 + skew, belly, -26 + skew, belly], sail)
	fpoly(cv, [-26 + skew, belly, 26 + skew, belly, 30 + skew, -8, -30 + skew, -8], sail_shade)
	var flag_w := 7.0 + 6.0 * wind_f
	fpoly(cv, [1, -64, 1 + flag_w, -61 + sin(t * 6.0), 1, -58], lit(Color("#a82020"), light, fl))
	cv.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	if light < 0.45:
		var g := (0.45 - light) / 0.45
		cv.draw_circle(SHIP_POS + Vector2(30.0, -4.0 + bob), 9.0, Color(1.0, 0.75, 0.3, 0.12 * g))
		cv.draw_circle(SHIP_POS + Vector2(30.0, -4.0 + bob), 2.0, Color(1.0, 0.85, 0.45, g))
	var wake_a := clampf(float(v["speed_kn"]) / 10.0, 0.0, 1.0) * 0.5
	for i in 3:
		var wy := SHIP_POS.y + 17.0 + float(i) * 4.0
		var half := 24.0 + 8.0 * float(i)
		var wcol := Color(1, 1, 1, wake_a * (1.0 - 0.3 * float(i)))
		cv.draw_line(Vector2(SHIP_POS.x - half, wy), Vector2(SHIP_POS.x + half, wy), wcol, 1.0)


# ---- wildlife silhouettes ----------------------------------------------------------------------------------
## Each critter: {group, rel (degrees off the bow), near (0 far .. 1 close), count, phase, born, name}.
static func critters(cv: CanvasItem, v: Dictionary, list: Array) -> void:
	var t: float = v["time"]
	var fl: float = v["floor"]
	for c in list:
		var rel: float = c["rel"]
		if absf(rel) > FOV_DEG + 10.0:
			continue
		var near: float = c["near"]
		var age: float = t - float(c["born"])
		var a := clampf(minf(age / 1.5, (float(c["life"]) - age) / 3.0), 0.0, 1.0)
		if a <= 0.0:
			continue
		var x := W * 0.5 + rel / FOV_DEG * W * 0.5
		var sc := 0.5 + 1.5 * near
		var fogc: Color = sky_colors(v)[1]
		var body := lit(Color(0.09, 0.11, 0.15), float(v["light"]), fl).lerp(fogc, 0.6 * (1.0 - near))
		body.a = a
		var ph: float = c["phase"]
		var n := mini(int(c["count"]), 8)
		var group := str(c["group"])
		if group == "seabird":
			for i in n:
				var o := Vector2(Ocean.hash01(i, 1, 0, 63) * 60.0 - 30.0, Ocean.hash01(i, 2, 0, 63) * 26.0) * sc
				var p := Vector2(x + o.x + sin(t * 0.4 + ph + i) * 8.0, HORIZON - 14.0 - 34.0 * near + o.y)
				var f := sin(t * 7.0 + ph + float(i)) * 2.0 * sc
				var wing := PackedVector2Array([p + Vector2(-5, -1 + f) * sc, p + Vector2(0, 1), p + Vector2(5, -1 + f) * sc])
				cv.draw_polyline(wing, body, 1.0)
		else:
			var y := HORIZON + 8.0 + 62.0 * near * near
			_sea_creature(cv, group, Vector2(x, y), sc, n, ph, t, body)


static func _sea_creature(
		cv: CanvasItem, group: String, p: Vector2, sc: float, n: int, ph: float, t: float, body: Color) -> void:
	var foam := Color(1, 1, 1, body.a * 0.8)
	match group:
		"cetacean":
			var arch := PackedVector2Array()
			for i in 9:
				var u := float(i) / 8.0
				arch.append(p + Vector2((u - 0.5) * 34.0 * sc, -sin(u * PI) * 6.0 * sc))
			cv.draw_colored_polygon(arch, body)
			fpoly(cv, [4, -5, 8, -12, 9, -4], body, p, sc)
			if fposmod(t + ph, 7.0) < 1.3:
				for k in 3:
					cv.draw_line(p + Vector2(-8, -5) * sc, p + Vector2(-8 + (k - 1) * 3, -14 - 4 * k) * sc, foam, 1.0)
		"shark_ray":
			fpoly(cv, [0, 0, -2, -9, 7, 0], body, p, sc)
			cv.draw_line(p + Vector2(-14, 1) * sc, p + Vector2(8, 1) * sc, foam, 1.0)
		"pelagic_fish", "reef_fish", "cold_fish":
			for i in n:
				var u := fposmod(t * 0.8 + ph + float(i) * 0.23, 3.0)
				if u < 1.0:
					var fp := p + Vector2((float(i) - float(n) * 0.5) * 7.0 * sc + u * 14.0 * sc, -sin(u * PI) * 9.0 * sc)
					cv.draw_circle(fp, 1.8 * sc, body)
					cv.draw_line(fp, fp + Vector2(-4, 1) * sc, body, 1.0)
				elif u < 1.4:
					var ring := p + Vector2((float(i) - float(n) * 0.5) * 7.0 * sc + 14.0 * sc, 0.0)
					cv.draw_arc(ring, (u - 1.0) * 12.0 * sc, 0.0, TAU, 12, foam, 1.0)
		"pinniped", "reptile":
			cv.draw_circle(p + Vector2(0, -2) * sc, 3.0 * sc, body)
			cv.draw_line(p + Vector2(-9, 1) * sc, p + Vector2(9, 1) * sc, foam, 1.0)
		"strange":
			var pulse := 0.5 + 0.5 * sin(t * 2.0 + ph)
			cv.draw_circle(p, 14.0 * sc * (0.7 + 0.3 * pulse), Color(0.4, 0.95, 0.9, 0.08 * body.a))
			cv.draw_circle(p, 5.0 * sc, Color(0.5, 1.0, 0.95, 0.5 * body.a * (0.5 + 0.5 * pulse)))
		_:
			for i in n:
				var o := Vector2((Ocean.hash01(i, 1, 0, 64) - 0.5) * 36.0, Ocean.hash01(i, 2, 0, 64) * 8.0) * sc
				cv.draw_circle(p + o, 1.5 * sc, body)


# ---- chart ---------------------------------------------------------------------------------------
static func chart_pos(x_km: float, y_km: float, world_w: float, world_h: float) -> Vector2:
	return CHART_RECT.position + Vector2(x_km / world_w * CHART_RECT.size.x, y_km / world_h * CHART_RECT.size.y)


## `c` = {tex, world_w, world_h, ship: Vector2(km), heading, route: Array of checkpoints, reached: Dictionary,
## labels: Array of [name, x_km, y_km, revealed bool], known_pct}
static func chart(cv: CanvasItem, c: Dictionary) -> void:
	var ww: float = c["world_w"]
	var wh: float = c["world_h"]
	cv.draw_rect(Rect2(0.0, 0.0, W, H), Color(0.05, 0.05, 0.07, 0.96))
	cv.draw_rect(CHART_RECT.grow(2.0), Color(0.55, 0.45, 0.3))
	cv.draw_texture_rect(c["tex"], CHART_RECT, false)
	for k in range(1, 9):
		var gx := CHART_RECT.position.x + CHART_RECT.size.x * float(k) * 1000.0 / ww
		cv.draw_line(Vector2(gx, 0), Vector2(gx, H), Color(1, 1, 1, 0.07), 1.0)
	for k in range(1, 6):
		var gy := CHART_RECT.size.y * float(k) * 1000.0 / wh
		cv.draw_line(Vector2(CHART_RECT.position.x, gy), Vector2(CHART_RECT.end.x, gy), Color(1, 1, 1, 0.07), 1.0)
	var route: Array = c["route"]
	var reached: Dictionary = c["reached"]
	var prev := Vector2.ZERO
	for i in route.size():
		var cp: Dictionary = route[i]
		var p := chart_pos(float(cp["x_km"]), float(cp["y_km"]), ww, wh)
		if i > 0:
			cv.draw_line(prev, p, Color(1.0, 0.85, 0.3, 0.45), 1.0)
		var done := reached.has(int(cp["id"]))
		cv.draw_circle(p, 3.5, Color(0.3, 1.0, 0.5) if done else Color(1.0, 0.85, 0.3))
		text(cv, p + Vector2(5, -3), str(int(cp["id"])), Color(1, 0.95, 0.6), 11)
		prev = p
	for lb in c["labels"]:
		if bool(lb[3]):
			text(cv, chart_pos(float(lb[1]), float(lb[2]), ww, wh) - Vector2(30, 0), str(lb[0]), Color(1, 1, 1, 0.75), 10)
	var sp: Vector2 = c["ship"]
	var sp_c := chart_pos(sp.x, sp.y, ww, wh)
	var hd: float = deg_to_rad(float(c["heading"]))
	var dir := Vector2(sin(hd), -cos(hd))
	var side := Vector2(-dir.y, dir.x) * 4.0
	var arrow := PackedVector2Array([sp_c + dir * 7.0, sp_c - dir * 4.0 + side, sp_c - dir * 4.0 - side])
	cv.draw_colored_polygon(arrow, Color(1, 1, 1))
	text(cv, Vector2(6, 16), "CHART", Color(1.0, 0.9, 0.6), 14)
	text(cv, Vector2(6, 34), "%.0f%% charted" % float(c["known_pct"]), Color(0.9, 0.9, 0.9), 11)
	text(cv, Vector2(6, 52), "9,000 x 6,000 km", Color(0.7, 0.7, 0.7), 10)
	text(cv, Vector2(6, 340), "M close  N reveal all (debug)", Color(0.8, 0.8, 0.8), 10)
