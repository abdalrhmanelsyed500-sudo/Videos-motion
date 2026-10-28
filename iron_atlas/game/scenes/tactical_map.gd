extends Control
## Tactical battle: tile grid derived from the region's terrain seed, tactical
## units spawned from the strategic formations present, click select + right
## click move/attack orders, pause & speed, skirmish resolution through the
## shared CombatSystem factors, battle report back to the strategic layer.

const CELL := 32
const GRID_W := 30
const GRID_H := 20
const SPRITE_DIR := "res://assets/sprites/units/"
const PixelArt = preload("res://core/pixel_art.gd")
const UiStyle = preload("res://core/ui_style.gd")

var region_id: String = ""
var tiles: PackedByteArray = PackedByteArray()
var units: Array = []          # {id, side, class, count, hp, x, y, tx, ty, target, equip}
var selected: Array = []
var paused: bool = false
var speed: int = 1
var tick_acc: float = 0.0
var finished: bool = false
var result_text: String = ""
var hud: Dictionary = {}
var rng := RandomNumberGenerator.new()
var tile_textures: Dictionary = {}
var unit_textures: Dictionary = {}

const TERRAIN_COLORS := {
	0: Color(0.42, 0.52, 0.33),   # plains
	1: Color(0.24, 0.38, 0.22),   # forest
	2: Color(0.86, 0.88, 0.92),   # snow
	3: Color(0.80, 0.68, 0.42),   # desert
	4: Color(0.45, 0.42, 0.40),   # road/urban
	5: Color(0.25, 0.38, 0.55),   # water
	6: Color(0.52, 0.50, 0.46),   # mountain
	7: Color(0.35, 0.42, 0.30),   # marsh/hills
}
const TERRAIN_INDEX := {"plains": 0, "forest": 1, "snow": 2, "desert": 3, "urban": 4,
	"badlands": 3, "mountain": 6, "marsh": 7, "hills": 7, "coast": 0}
const MOVE_COST := {0: 1.0, 1: 1.5, 2: 1.6, 3: 1.1, 4: 0.8, 5: 99.0, 6: 2.2, 7: 2.0}


func _ready() -> void:
	theme = UiStyle.make_theme()
	var st := GameState.cs
	region_id = _pick_region()
	rng.seed = hash(region_id + str(st.seed)) & 0x7FFFFFFF
	_gen_tiles(st.regions[region_id]["terrain"])
	_load_art()
	_spawn_units()
	_build_hud()


func _pick_region() -> String:
	var st := GameState.cs
	if st.regions.has(GameState.tactical_region):
		for pair in GameState.combat.hostile_pairs(st, GameState.tactical_region):
			if st.player_id() in [pair[0]["country"], pair[1]["country"]]:
				return GameState.tactical_region
	for rid in st.regions:
		for pair in GameState.combat.hostile_pairs(st, rid):
			if st.player_id() in [pair[0]["country"], pair[1]["country"]]:
				return rid
	for f in st.formations_of(st.player_id()):
		return f["region"]
	return st.regions.keys()[0]


func _load_art() -> void:
	# Use raw PNGs when available, with imported-resource fallback in exports.
	# This keeps nearest-neighbor art usable in both desktop and web builds.
	var terrain_names := ["t_grass", "t_forest", "t_snow", "t_desert", "t_urban", "t_water", "t_mountain", "t_hills"]
	for i in terrain_names.size():
		var path: String = "res://assets/sprites/terrain/" + terrain_names[i] + ".png"
		var texture := PixelArt.texture(path)
		if texture != null:
			tile_textures[i] = texture
	for name in ["infantry", "pickup", "truck", "apc", "tank_light", "tank_main", "artillery"]:
		var path: String = SPRITE_DIR + name + ".png"
		var texture := PixelArt.texture(path)
		if texture != null:
			unit_textures[name] = texture


func _gen_tiles(base_terrain: String) -> void:
	tiles.resize(GRID_W * GRID_H)
	var base: int = TERRAIN_INDEX.get(base_terrain, 0)
	for y in GRID_H:
		for x in GRID_W:
			var t := base
			var n := rng.randf()
			if n < 0.12:
				t = (base + 1) % 5 if base != 5 else 0
			elif n < 0.16:
				t = 1 if base != 1 else 0
			if y == GRID_H / 2 and x % 7 == 3:
				t = 4
			tiles[y * GRID_W + x] = t


func _spawn_units() -> void:
	var st := GameState.cs
	var opponent := ""
	for pair in GameState.combat.hostile_pairs(st, region_id):
		if pair[0]["country"] == st.player_id():
			opponent = pair[1]["country"]
			break
		if pair[1]["country"] == st.player_id():
			opponent = pair[0]["country"]
			break
	for f in st.formations_in(region_id):
		if f["country"] != st.player_id() and f["country"] != opponent:
			continue
		var side := 0 if f["country"] == st.player_id() else 1
		var slot := 0
		for strategic in f["units"]:
			var count := int(strategic["count"])
			var represented_groups := mini(count, 4)
			for k in represented_groups:
				var represented := int(count / represented_groups) + (1 if k < count % represented_groups else 0)
				var ux := 3 + (slot % 4) * 2 if side == 0 else GRID_W - 4 - (slot % 4) * 2
				var uy := 3 + (int(slot / 4) * 2) % (GRID_H - 6)
				var hp := float(represented) * float(strategic["condition"])
				units.append({"id": "%s_%d" % [f["id"], units.size()], "side": side,
					"class": strategic["class"], "count": represented, "hp": hp, "max_hp": hp,
					"x": ux, "y": uy, "tx": ux, "ty": uy, "target": -1,
					"equip": strategic["equip"], "formation": f["id"],
					"morale": float(f["morale"])})
				slot += 1


func _build_hud() -> void:
	var bar := HBoxContainer.new()
	bar.position = Vector2(8, 6)
	add_child(bar)
	for label in ["pause", "s1", "s2", "end"]:
		var b := Button.new()
		b.text = {"pause": "Pause/Run", "s1": "x1", "s2": "x3", "end": "Retreat/End"}[label]
		b.pressed.connect(_on_hud.bind(label))
		bar.add_child(b)
	hud["info"] = Label.new()
	hud["info"].position = Vector2(390, 12)
	add_child(hud["info"])
	var briefing := Label.new()
	briefing.position = Vector2(976, 70)
	briefing.size = Vector2(290, 240)
	briefing.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	briefing.text = "TACTICAL CONTACT\n\nLeft click a friendly unit to select it. Right click terrain to move, or an enemy to attack.\n\nUnits consume ammunition; low reserves reduce firepower. Losses, wounded and salvage persist after battle.\n\nRetreat orders a withdrawal; it is not a victory."
	add_child(briefing)
	hud["briefing"] = briefing
	hud["result"] = Label.new()
	hud["result"].position = Vector2(420, 340)
	hud["result"].add_theme_font_size_override("font_size", 20)
	hud["result"].size = Vector2(500, 100)
	hud["result"].autowrap_mode = TextServer.AUTOWRAP_WORD
	add_child(hud["result"])
	var back := Button.new()
	back.text = "Return to world"
	back.position = Vector2(420, 450)
	back.visible = false
	back.pressed.connect(func(): get_tree().change_scene_to_file("res://scenes/world_map.tscn"))
	add_child(back)
	hud["back"] = back


func _on_hud(key: String) -> void:
	match key:
		"pause": paused = not paused
		"s1": speed = 1
		"s2": speed = 3
		"end": _finish(false)


func _gui_input(ev: InputEvent) -> void:
	if finished:
		return
	if ev is InputEventMouseButton and ev.pressed:
		var cell := Vector2i(int(ev.position.x / CELL), int(ev.position.y / CELL))
		if ev.button_index == MOUSE_BUTTON_LEFT:
			selected = []
			for i in units.size():
				if units[i]["side"] == 0 and units[i]["x"] == cell.x and units[i]["y"] == cell.y:
					selected = [i]
		elif ev.button_index == MOUSE_BUTTON_RIGHT and selected.size():
			var enemy := -1
			for i in units.size():
				if units[i]["side"] == 1 and units[i]["x"] == cell.x and units[i]["y"] == cell.y:
					enemy = i
			for si in selected:
				if enemy >= 0:
					units[si]["target"] = enemy
				else:
					units[si]["tx"] = clampi(cell.x, 0, GRID_W - 1)
					units[si]["ty"] = clampi(cell.y, 0, GRID_H - 1)
					units[si]["target"] = -1


func _process(delta: float) -> void:
	if paused or finished:
		queue_redraw()
		return
	tick_acc += delta * speed * 2.0
	while tick_acc >= 1.0:
		tick_acc -= 1.0
		_tick()
	queue_redraw()


func _tick() -> void:
	for i in units.size():
		var u: Dictionary = units[i]
		if u["hp"] <= 0:
			continue
		if u["target"] >= 0 and (u["target"] >= units.size() or units[u["target"]]["hp"] <= 0):
			u["target"] = -1
		if u["side"] == 1 and u["target"] < 0:
			var closest := -1
			var distance := 9999
			for j in units.size():
				var candidate: Dictionary = units[j]
				if candidate["side"] != 0 or float(candidate["hp"]) <= 0:
					continue
				var d: int = absi(int(candidate["x"]) - int(u["x"])) + absi(int(candidate["y"]) - int(u["y"]))
				if d < distance:
					distance = d
					closest = j
			u["target"] = closest
		if u["target"] >= 0:
			var t: Dictionary = units[u["target"]]
			var d := absi(t["x"] - u["x"]) + absi(t["y"] - u["y"])
			var reach := 3 if u["class"] in ["artillery", "recon"] else 1
			if d <= reach:
				_fire(u, t)
			else:
				_step_toward(u, t["x"], t["y"])
		else:
			if u["x"] != u["tx"] or u["y"] != u["ty"]:
				_step_toward(u, u["tx"], u["ty"])
	# cleanup + end check
	var alive := [0, 0]
	for u in units:
		if u["hp"] > 0:
			alive[u["side"]] += 1
	hud["info"].text = "Friendly %d · Hostile %d · %s" % [alive[0], alive[1],
		"PAUSED" if paused else "RUN x%d" % speed]
	if alive[1] == 0 or alive[0] == 0:
		_finish(alive[1] == 0)


func _step_toward(u: Dictionary, gx: int, gy: int) -> void:
	var dx := signi(gx - u["x"])
	var dy := signi(gy - u["y"])
	var tries := [[dx, 0], [0, dy], [dx, dy]]
	for tr in tries:
		if tr[0] == 0 and tr[1] == 0:
			continue
		var nx: int = int(u["x"]) + tr[0]
		var ny: int = int(u["y"]) + tr[1]
		if nx < 0 or ny < 0 or nx >= GRID_W or ny >= GRID_H:
			continue
		if MOVE_COST[tiles[ny * GRID_W + nx]] > 3.0:
			continue
		var blocked := false
		for o in units:
			if o["hp"] > 0 and o["x"] == nx and o["y"] == ny:
				blocked = true
				break
		if not blocked:
			u["x"] = nx
			u["y"] = ny
			return


func _fire(u: Dictionary, t: Dictionary) -> void:
	var st := GameState.cs
	var eq: Dictionary = GameState.market.item(u["equip"])
	var f: Dictionary = st.formations.get(u["formation"], {})
	var ammo := float(f.get("ammo_reserve", 0.0))
	if not f.is_empty():
		f["ammo_reserve"] = maxf(0.0, ammo - 0.006)
	var ammo_mod := 1.0 if ammo > 0.02 else 0.15
	var atk: float = float(eq.get("combat", 25)) * 0.02 * (0.6 + 0.4 * float(u["morale"])) * ammo_mod
	var def_terrain: int = tiles[t["y"] * GRID_W + t["x"]]
	var def_mod := 1.0 + 0.15 * (1.0 if def_terrain in [1, 4, 6] else 0.0)
	var dmg: float = atk * (0.7 + st.randf() * 0.6) / def_mod
	t["hp"] = maxf(0.0, float(t["hp"]) - dmg)
	t["morale"] = maxf(0.05, float(t["morale"]) - 0.01)


func _finish(player_won: bool) -> void:
	if finished:
		return
	finished = true
	var st := GameState.cs
	var rep := GameState.combat.apply_tactical_outcome(st, region_id, units, player_won, GameState.market.catalog)
	result_text = "VICTORY — hostiles routed" if player_won else "RETREAT / DEFEAT — withdrawal ordered"
	var killed := 0
	var wounded := 0
	for fid in rep["losses"]:
		if st.formations.has(fid) and st.formations[fid]["country"] == st.player_id():
			killed += int(rep["losses"][fid]["killed"])
			wounded += int(rep["losses"][fid]["wounded"])
	hud["result"].text = "%s\nFriendly killed %d · wounded %d\nFull report is available on the world map." % [result_text, killed, wounded]
	hud["back"].visible = true


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.08, 0.11, 0.10))
	draw_line(Vector2(960, 0), Vector2(960, 720), Color(0.30, 0.36, 0.29), 1.0)
	for y in GRID_H:
		for x in GRID_W:
			var tile: int = tiles[y * GRID_W + x]
			if tile_textures.has(tile):
				# Seeded quarter turns break repeated tile seams without filtering pixels.
				var quarter := (x * 13 + y * 7 + int(rng.seed % 4)) % 4
				draw_set_transform(Vector2(x * CELL + CELL / 2, y * CELL + CELL / 2), float(quarter) * PI / 2.0)
				draw_texture(tile_textures[tile], Vector2(-CELL / 2, -CELL / 2))
				draw_set_transform(Vector2.ZERO)
			else:
				draw_rect(Rect2(x * CELL, y * CELL, CELL, CELL), TERRAIN_COLORS[tile])
	for i in units.size():
		var u: Dictionary = units[i]
		if float(u["hp"]) <= 0:
			continue
		var col := Color(0.30, 0.55, 0.30) if u["side"] == 0 else Color(0.62, 0.30, 0.28)
		var rect := Rect2(u["x"] * CELL + 4, u["y"] * CELL + 4, CELL - 8, CELL - 8)
		var sprite := {"infantry": "infantry", "recon": "pickup", "logistics": "truck",
			"mechanized": "apc", "armor": "tank_main", "artillery": "artillery"}.get(u["class"], "infantry")
		if unit_textures.has(sprite):
			draw_rect(rect, Color(col.r, col.g, col.b, 0.45))
			draw_texture(unit_textures[sprite], rect.position, Color.WHITE if u["side"] == 0 else Color(1.0, 0.68, 0.62))
		else:
			draw_rect(rect, col)
			draw_rect(Rect2(rect.position + Vector2(4, 4), Vector2(rect.size.x - 8, 4)), col.lightened(0.35))
		draw_rect(Rect2(u["x"] * CELL + 4, u["y"] * CELL + CELL - 7,
			(CELL - 8) * clampf(float(u["hp"]) / maxf(0.001, float(u["max_hp"])), 0, 1), 2), Color(0.9, 0.85, 0.2))
		if i in selected:
			draw_rect(rect.grow(2), Color(1, 1, 1), false, 1.5)
