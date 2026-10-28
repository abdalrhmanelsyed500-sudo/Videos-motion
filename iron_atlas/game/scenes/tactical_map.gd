extends Control
## Tactical battle: tile grid derived from the region's terrain seed, tactical
## units spawned from the strategic formations present, click select + right
## click move/attack orders, pause & speed, skirmish resolution through the
## shared CombatSystem factors, battle report back to the strategic layer.

const CELL := 32
const GRID_W := 30
const GRID_H := 20
const SPRITE_DIR := "res://assets/sprites/units/"

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
	var st := GameState.cs
	region_id = _pick_region()
	rng.seed = hash(region_id + str(st.seed)) & 0x7FFFFFFF
	_gen_tiles(st.regions[region_id]["terrain"])
	_spawn_units()
	_build_hud()


func _pick_region() -> String:
	# first contested region, else the player's current region
	var st := GameState.cs
	for rid in st.regions:
		if not GameState.combat.hostile_pairs(st, rid).is_empty():
			return rid
	for f in st.formations_of(st.player_id()):
		return f["region"]
	return st.regions.keys()[0]


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
	var sides := {}
	for f in st.formations_in(region_id):
		sides[f["country"]] = true
	var side_keys: Array = sides.keys()
	var player_side: String = st.player_id()
	for f in st.formations_in(region_id):
		var side := 0 if f["country"] == player_side else 1
		var slot := 0
		for u in f["units"]:
			for k in range(mini(int(u["count"]), 4)):
				var ux := 3 + slot * 2 + (0 if side == 0 else GRID_W - 8)
				var uy := 3 + (slot * 3 + k * 2) % (GRID_H - 6)
				units.append({"id": "%s_%d" % [f["id"], units.size()], "side": side,
					"class": u["class"], "count": int(u["count"]),
					"hp": float(u["count"]) * float(u["condition"]),
					"x": ux, "y": uy, "tx": ux, "ty": uy, "target": -1,
					"equip": u["equip"], "formation": f["id"],
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
	hud["info"].position = Vector2(320, 8)
	add_child(hud["info"])
	hud["result"] = Label.new()
	hud["result"].position = Vector2(420, 340)
	hud["result"].add_theme_font_size_override("font_size", 26)
	add_child(hud["result"])


func _on_hud(key: String) -> void:
	match key:
		"pause": paused = not paused
		"s1": speed = 1
		"s2": speed = 3
		"end": _finish(true)


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
	var atk: float = float(eq.get("combat", 25)) * 0.02 * (0.6 + 0.4 * float(u["morale"]))
	var def_terrain: int = tiles[t["y"] * GRID_W + t["x"]]
	var def_mod := 1.0 + 0.15 * (1.0 if def_terrain in [1, 4, 6] else 0.0)
	var dmg: float = atk * (0.7 + st.randf() * 0.6) / def_mod
	t["hp"] -= dmg
	t["morale"] = maxf(0.05, t["morale"] - 0.01)
	if t["hp"] <= 0 and t["morale"] < 0.3:
		pass  # routed units removed by end-check via hp


func _finish(player_won: bool) -> void:
	if finished:
		return
	finished = true
	var st := GameState.cs
	# apply tactical outcome proportionally to strategic formations present
	var lost_ratio := 0.0
	var alive_friend := 0
	var total_friend := 0
	for u in units:
		if u["side"] == 0:
			total_friend += 1
			if u["hp"] > 0:
				alive_friend += 1
	lost_ratio = 1.0 - (float(alive_friend) / maxf(1.0, float(total_friend)))
	for f in st.formations_in(region_id):
		if f["country"] == st.player_id():
			for u in f["units"]:
				u["count"] = maxi(0, int(roundf(float(u["count"]) * (1.0 - lost_ratio * 0.7))))
			f["morale"] = clampf(float(f["morale"]) + (0.1 if player_won else -0.2), 0.05, 1.0)
	result_text = "VICTORY — hostiles routed" if player_won else "DEFEAT — force withdrawn"
	hud["result"].text = result_text
	var rep := st.add_report("battle", "Tactical engagement: " + st.regions[region_id]["name"],
		"%s. Friendly losses ~%.0f%% of engaged strength." % [result_text, lost_ratio * 100])
	EventBus.battle_finished.emit(rep)
	# clear hostile formations that were wiped tactically
	if player_won:
		for f in st.formations_in(region_id):
			if f["country"] != st.player_id():
				for u in f["units"]:
					u["count"] = maxi(0, int(u["count"]) - 2)
	get_tree().create_timer(1.2).timeout.connect(
		func(): get_tree().change_scene_to_file("res://scenes/world_map.tscn"))


func _draw() -> void:
	for y in GRID_H:
		for x in GRID_W:
			draw_rect(Rect2(x * CELL, y * CELL, CELL, CELL),
				TERRAIN_COLORS[tiles[y * GRID_W + x]])
	for i in units.size():
		var u: Dictionary = units[i]
		if u["hp"] <= 0:
			continue
		var col := Color(0.30, 0.55, 0.30) if u["side"] == 0 else Color(0.62, 0.30, 0.28)
		var rect := Rect2(u["x"] * CELL + 4, u["y"] * CELL + 4, CELL - 8, CELL - 8)
		draw_rect(rect, col)
		draw_rect(Rect2(rect.position + Vector2(4, 4), Vector2(rect.size.x - 8, 4)),
			col.lightened(0.35))
		draw_rect(Rect2(u["x"] * CELL + 4, u["y"] * CELL + CELL - 7,
			(CELL - 8) * clampf(u["hp"] / maxf(1.0, float(u["count"])), 0, 1), 2),
			Color(0.9, 0.85, 0.2))
		if i in selected:
			draw_rect(rect.grow(2), Color(1, 1, 1), false, 1.5)
