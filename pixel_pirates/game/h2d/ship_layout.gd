extends RefCounted
## CP-2 Release A: THE SHIP'S PLAN. One source of truth for where things are aboard: the walking space of every level, the solid
## furniture (which the 3D model is built from too, see ship_deck_view.gd), the interaction points and the ladders.
## Pure logic (no nodes): tests/test_ship_layout.gd runs it headless.
## Coordinates are SHIP-LOCAL metres: u along the ship (bow = +u), v across (starboard = +v). A level is a deck of the ship:
##   0 main deck (open air, captain's cabin at the stern), 1 sleeping and equipment deck, 2 provisioning hold,
##   3 crow's nest (a small platform at the top of the mast, reached by the rope ladder).
## The hull is 22 m long and 6.2 m wide on deck (the same footprint as the sloop sprite and ship_motion.gd SHIP_LEN / SHIP_BEAM).
## Scale: the pirate is 1.9 m tall (land walker); a door is 1.4 m wide; every aisle is at least 1.0 m clear, so a 0.38 m body fits.
## NOT YET RUN ON THE USER'S PC (see docs/CP2_RELEASE_A.md).
const L_DECK := 0
const L_SLEEP := 1
const L_HOLD := 2
const L_NEST := 3
const NAMES: Array[String] = ["Main deck", "Sleeping deck", "Provisioning hold", "Crow's nest"]
const FLOOR_Y := 1.2          ## model height of the decks above the water (all three decks share it, so the camera does not jump)
const NEST_Y := 9.6           ## model height of the crow's nest floor
const WALL_MARGIN := 0.3      ## the rail / hull wall thickness walkers never enter
## Half-width of the walkable hull outline at u: [u, half width], linear in between.
const HULL := {
	0: [[-11.0, 1.9], [-10.0, 2.6], [-8.0, 3.0], [-3.0, 3.1], [2.0, 3.05], [5.0, 2.7], [7.5, 1.9], [9.5, 0.9], [11.0, 0.15]],
	1: [[-9.4, 1.2], [-8.2, 2.0], [-3.0, 2.5], [3.0, 2.45], [6.0, 2.1], [8.0, 1.3], [9.2, 0.3]],
	2: [[-6.8, 0.9], [-5.2, 1.7], [-2.0, 2.0], [3.0, 2.0], [5.5, 1.6], [7.2, 0.8]],
}
## Key places (u, v).
const HELM := Vector2(-3.6, 0.6)            ## the wheel's pedestal
const HELM_STATION := Vector2(-4.5, 0.6)    ## where the helmsman stands (just aft of the wheel)
const HELM_LEAVE := Vector2(-3.7, 1.55)     ## where the pirate stands after leaving the wheel (beside it, free to walk on)
const CABIN_U0 := -10.0                     ## the captain's cabin: u from -10.0 (stern wall) to -5.4 (front wall), v +-2.2
const CABIN_U1 := -5.4
const CABIN_V := 2.2
const DOOR_V0 := -2.0                       ## the door in the front wall: v from -2.0 to -0.6 (1.4 m)
const DOOR_V1 := -0.6
const HATCH := Vector2(-1.6, 0.0)           ## main hatch: deck <-> sleeping deck (same u, v on both levels)
const HATCH_HALF := Vector2(0.7, 0.6)       ## the coaming (solid) around the opening
const HOLD_HATCH := Vector2(4.6, 0.0)       ## sleeping deck <-> hold
const MAST := Vector2(1.0, 0.0)
const MAST_R := 0.45
const LADDER_BASE := Vector2(1.0, 2.4)      ## foot of the rope ladder on the starboard side (a ratline ladder to the nest)
const NEST_HALF := 1.4                      ## the crow's nest platform is 2.8 m square around the mast
const LADDER_LAND := Vector2(1.0, 2.0)       ## where you step off the ladder onto the deck
const NEST_ARRIVE := Vector2(1.0, 1.0)
const LADDER_TOP_V := 1.45                  ## the ladder meets the platform edge here
const LADDER_RISE := 8.4                    ## NEST_Y - FLOOR_Y
const WINCH := Vector2(3.2, -2.2)
const WINCH_HALF := Vector2(0.95, 0.55)
const FISH_BARRELS: Array[Vector2] = [Vector2(5.2, -1.75), Vector2(6.1, -1.45), Vector2(5.2, -0.85), Vector2(6.1, -0.6)]
const FISH_BARREL_R := 0.45
## VP-1A.2: where the four deck cannons stand (u), per side: index 0 = port (v < 0), 1 = starboard. Each is a small solid box against the bulwark,
## placed where the deck has nothing else (checked by tests/test_ship_layout.gd: every interaction stays reachable).
const CANNON_U: Array = [[-4.6, -0.6], [-4.6, 6.2]]
const DESK := Vector2(-9.2, -0.7)
const DESK_HALF := Vector2(0.55, 1.0)
const CHEST := Vector2(-6.1, 1.5)
const LEDGER := Vector2(-6.1, 0.0)
## Where you land when you come through a hatch or down the ladder.
const ARRIVE_BELOW := Vector2(-2.9, 0.0)    ## sleeping deck, aft of the ladder
const ARRIVE_ABOVE := Vector2(-2.9, 0.0)    ## main deck, aft of the hatch
const ARRIVE_HOLD := Vector2(3.4, 0.0)
const ARRIVE_BACK_UP := Vector2(3.4, 0.0)   ## sleeping deck, aft of the hold hatch
## The six provision racks of the hold. Items of the real inventory (core/game_state.gd inventory, data/items/items.json) fill them:
## the number of visible pieces is ceil(units / units_per_slot), at most `slots`. side: -1 port, +1 starboard.
const ZONES: Array[Dictionary] = [
	{"id": "food", "label": "Food", "side": -1, "u": -4.2, "hu": 1.4, "cats": ["food"], "units_per_slot": 8, "slots": 6, "piece": "sack"},
	{"id": "drink", "label": "Water and drinks", "side": 1, "u": -4.2, "hu": 1.4, "cats": ["drink"], "units_per_slot": 4, "slots": 6, "piece": "barrel"},
	{"id": "ammo", "label": "Legacy stores", "side": -1, "u": -1.6, "hu": 0.9, "cats": ["ammo"], "units_per_slot": 5, "slots": 6, "piece": "keg"},
	{"id": "parts", "label": "Rope, planks, tar, canvas", "side": 1, "u": -1.6, "hu": 0.9, "cats": ["ship_part"], "units_per_slot": 4, "slots": 6, "piece": "plank"},
	{"id": "stores", "label": "Medicine and tools", "side": -1, "u": 3.2, "hu": 1.0, "cats": ["medicine", "tool"], "units_per_slot": 3, "slots": 6, "piece": "crate"},
	{"id": "trade", "label": "Trade goods", "side": 1, "u": 3.2, "hu": 1.0, "cats": ["trade", "treasure"], "units_per_slot": 6, "slots": 6, "piece": "bale"},
]
const RACK_V := 1.4                        ## rack centre |v| in the hold
const RACK_HV := 0.4

var _obs: Dictionary = {}
var _inter: Dictionary = {}


func _init() -> void:
	_build()


# ---- the hull -----------------------------------------------------------------------------------------------------
static func hull_half(level: int, u: float) -> float:
	if not HULL.has(level):
		return -1.0
	var t: Array = HULL[level]
	if u < float((t[0] as Array)[0]) or u > float((t[t.size() - 1] as Array)[0]):
		return -1.0
	for i in t.size() - 1:
		var a: Array = t[i]
		var b: Array = t[i + 1]
		if u <= float(b[0]):
			var k := (u - float(a[0])) / maxf(float(b[0]) - float(a[0]), 0.0001)
			return lerpf(float(a[1]), float(b[1]), k)
	return -1.0


static func hull_range(level: int) -> Vector2:
	var t: Array = HULL[level]
	return Vector2(float((t[0] as Array)[0]), float((t[t.size() - 1] as Array)[0]))


## Floor height in the model for a level.
static func floor_y(level: int) -> float:
	return NEST_Y if level == L_NEST else FLOOR_Y


# ---- solid things ---------------------------------------------------------------------------------------------------
func _box(id: String, c: Vector2, half: Vector2, ht: float, style: String) -> Dictionary:
	return {"id": id, "shape": "box", "c": c, "half": half, "r": 0.0, "ht": ht, "style": style}


func _circle(id: String, c: Vector2, r: float, ht: float, style: String) -> Dictionary:
	return {"id": id, "shape": "circle", "c": c, "half": Vector2.ZERO, "r": r, "ht": ht, "style": style}


func _build() -> void:
	var d0: Array[Dictionary] = []
	# the captain's cabin (walls; the door gap lies in the front wall)
	d0.append(_box("cabin_back", Vector2(CABIN_U0, 0.0), Vector2(0.1, CABIN_V + 0.1), 2.4, "cabin_wall"))
	d0.append(_box("cabin_port", Vector2((CABIN_U0 + CABIN_U1) * 0.5, -CABIN_V), Vector2((CABIN_U1 - CABIN_U0) * 0.5, 0.1), 2.4, "cabin_wall"))
	d0.append(_box("cabin_stbd", Vector2((CABIN_U0 + CABIN_U1) * 0.5, CABIN_V), Vector2((CABIN_U1 - CABIN_U0) * 0.5, 0.1), 2.4, "cabin_wall"))
	d0.append(_box("cabin_front_a", Vector2(CABIN_U1, (-CABIN_V - 0.1 + DOOR_V0) * 0.5), Vector2(0.1, (DOOR_V0 + CABIN_V + 0.1) * 0.5), 2.4, "cabin_wall"))
	d0.append(_box("cabin_front_b", Vector2(CABIN_U1, (DOOR_V1 + CABIN_V + 0.1) * 0.5), Vector2(0.1, (CABIN_V + 0.1 - DOOR_V1) * 0.5), 2.4, "cabin_wall"))
	d0.append(_box("desk", DESK, DESK_HALF, 0.9, "desk"))
	d0.append(_box("bed", Vector2(-9.0, 1.45), Vector2(0.85, 0.6), 0.6, "bed"))
	d0.append(_box("chest", Vector2(-6.1, 1.5), Vector2(0.4, 0.6), 0.7, "chest"))
	d0.append(_box("shelf", Vector2(-7.3, 1.95), Vector2(0.8, 0.12), 1.6, "shelf"))
	# the helm
	d0.append(_circle("helm", HELM, 0.35, 1.0, "helm"))
	d0.append(_box("hatch", HATCH, HATCH_HALF, 0.35, "hatch"))
	d0.append(_circle("mast", MAST, MAST_R, 10.0, "mast"))
	d0.append(_box("winch", WINCH, WINCH_HALF, 1.4, "winch"))
	for i in FISH_BARRELS.size():
		d0.append(_circle("fish_barrel_%d" % i, FISH_BARRELS[i], FISH_BARREL_R, 1.0, "fish_barrel"))
	d0.append(_circle("barrel_a", Vector2(-2.9, -2.45), 0.45, 1.0, "barrel"))
	d0.append(_circle("barrel_b", Vector2(-2.9, 2.45), 0.45, 1.0, "barrel"))
	d0.append(_box("crate_a", Vector2(3.0, 2.2), Vector2(0.5, 0.5), 1.0, "crate"))
	d0.append(_box("crate_b", Vector2(4.1, 2.15), Vector2(0.45, 0.45), 0.9, "crate"))
	d0.append(_box("windlass", Vector2(8.0, 0.0), Vector2(0.35, 0.7), 0.9, "windlass"))
	for si in 2:
		var sg := -1.0 if si == 0 else 1.0
		for cu in CANNON_U[si]:
			var cuf := float(cu)
			d0.append(_box("cannon_%d_%d" % [si, int(cuf * 10.0)], Vector2(cuf, sg * (hull_half(L_DECK, cuf) - 0.75)), Vector2(0.36, 0.5), 0.5, "cannon"))
	_obs[L_DECK] = d0
	var d1: Array[Dictionary] = []
	d1.append(_circle("mast", MAST, MAST_R, 10.0, "mast"))
	for u_c in [-6.0, -3.9, 3.2]:
		for s in [-1.0, 1.0]:
			d1.append(_box("hammock_%d_%d" % [int(u_c * 10.0), int(s)], Vector2(u_c, s * 1.75), Vector2(0.9, 0.38), 0.9, "hammock"))
	for s in [-1.0, 1.0]:
		d1.append(_box("bunk_%d" % int(s), Vector2(-7.8, s * 1.2), Vector2(0.8, 0.5), 1.1, "bunk"))
	d1.append(_box("hatch_up", HATCH, Vector2(0.2, 0.5), 1.0, "ladder_foot"))
	d1.append(_box("hatch_down", HOLD_HATCH, HATCH_HALF, 0.35, "hatch"))
	d1.append(_box("crate_stack", Vector2(6.4, 1.35), Vector2(0.6, 0.6), 1.2, "crate"))
	d1.append(_circle("barrel_c", Vector2(6.3, -1.35), 0.5, 1.0, "barrel"))
	d1.append(_circle("barrel_d", Vector2(7.4, -0.5), 0.5, 1.0, "barrel"))
	_obs[L_SLEEP] = d1
	var d2: Array[Dictionary] = []
	d2.append(_circle("mast", MAST, MAST_R, 10.0, "mast"))
	d2.append(_box("hold_ladder", HOLD_HATCH, Vector2(0.2, 0.45), 1.0, "ladder_foot"))
	d2.append(_box("ledger_table", LEDGER, Vector2(0.35, 0.7), 0.9, "ledger"))
	for z in ZONES:
		var zd: Dictionary = z
		d2.append(_box("rack_" + str(zd["id"]), Vector2(float(zd["u"]), float(zd["side"]) * RACK_V), Vector2(float(zd["hu"]), RACK_HV), 1.4, "rack"))
	_obs[L_HOLD] = d2
	var d3: Array[Dictionary] = []
	d3.append(_circle("mast", MAST, 0.4, 10.0, "mast"))
	_obs[L_NEST] = d3
	_build_interactions()


func _build_interactions() -> void:
	_inter[L_DECK] = [
		_i("helm", HELM, 1.9, "E  Take the helm"),
		_i("desk", Vector2(-8.2, -0.7), 1.4, "E  Study the chart on the captain's desk"),
		_i("chest", CHEST, 1.5, "E  Open the sea chest"),
		_i("hatch_down", HATCH, 1.7, "E  Climb down to the sleeping deck"),
		_i("rope_ladder", LADDER_BASE, 1.5, "E  Climb the rope ladder to the crow's nest"),
		_i("winch", Vector2(WINCH.x, WINCH.y + 0.9), 1.6, "F  Work the fishing winch"),
		_i("fish_barrels", Vector2(5.65, -1.15), 1.9, "E  Look into the fish barrels"),
	]
	_inter[L_SLEEP] = [
		_i("ladder_up", HATCH, 1.6, "E  Climb up to the main deck"),
		_i("hatch_down", HOLD_HATCH, 1.6, "E  Climb down to the provisioning hold"),
		_i("berths", Vector2(-4.9, 0.0), 2.4, "E  Look at the crew's berths"),
	]
	_inter[L_HOLD] = [
		_i("ladder_up", HOLD_HATCH, 1.6, "E  Climb up to the sleeping deck"),
		_i("ledger", LEDGER, 1.8, "E  Check the stores ledger"),
		_i("racks", Vector2(-1.0, 0.0), 2.6, "E  Look over the provisions"),
	]
	_inter[L_NEST] = [
		_i("ladder_down", NEST_ARRIVE, 1.4, "E  Climb down the rope ladder"),
	]


func _i(id: String, c: Vector2, r: float, prompt: String) -> Dictionary:
	return {"id": id, "c": c, "r": r, "prompt": prompt}


func obstacles(level: int) -> Array:
	return _obs.get(level, [])


func interactions(level: int) -> Array:
	return _inter.get(level, [])


## The nearest interaction whose reach covers (u, v) on this level, or {}.
func nearest_interaction(level: int, u: float, v: float) -> Dictionary:
	var best: Dictionary = {}
	var best_d := 1.0e9
	for it in interactions(level):
		var d: Dictionary = it
		var dist := Vector2(u, v).distance_to(d["c"] as Vector2)
		if dist <= float(d["r"]) and dist < best_d:
			best_d = dist
			best = d
	return best


func interaction(level: int, id: String) -> Dictionary:
	for it in interactions(level):
		if str((it as Dictionary)["id"]) == id:
			return it as Dictionary
	return {}


# ---- walking ------------------------------------------------------------------------------------------------------
func _inside_hull(level: int, u: float, v: float, r: float) -> bool:
	if level == L_NEST:
		var lim := NEST_HALF - 0.1 - r * 0.5
		return absf(u - MAST.x) <= lim and absf(v - MAST.y) <= lim
	for du in [-r * 0.8, 0.0, r * 0.8]:
		var h := hull_half(level, u + float(du)) - WALL_MARGIN
		if h <= 0.0 or absf(v) + r * 0.75 > h:
			return false
	return true


static func _hits(o: Dictionary, u: float, v: float, r: float) -> bool:
	var c: Vector2 = o["c"]
	if str(o["shape"]) == "circle":
		return Vector2(u, v).distance_to(c) < r + float(o["r"])
	var half: Vector2 = o["half"]
	var qx := clampf(u, c.x - half.x, c.x + half.x)
	var qy := clampf(v, c.y - half.y, c.y + half.y)
	return Vector2(u - qx, v - qy).length() < r


## True if a body of radius r can stand at (u, v) on this level.
func walkable(level: int, u: float, v: float, r: float) -> bool:
	if not _inside_hull(level, u, v, r):
		return false
	for o in obstacles(level):
		if _hits(o as Dictionary, u, v, r):
			return false
	return true


## True when (u, v) is inside the captain's cabin or in its doorway: the roof dissolves and the walls drop so you can see in.
static func cabin_open(u: float, v: float) -> bool:
	if u >= CABIN_U0 and u <= CABIN_U1 + 0.9 and absf(v) <= CABIN_V:
		if u <= CABIN_U1 + 0.15:
			return true
		return v >= DOOR_V0 - 0.3 and v <= DOOR_V1 + 0.3
	return false


## Where the rope ladder is: the hero's local position and the height above the nest-ladder foot at climb fraction t (0 foot, 1 top).
static func ladder_point(t: float) -> Vector3:
	var k := clampf(t, 0.0, 1.0)
	return Vector3(LADDER_BASE.x, lerpf(LADDER_BASE.y, LADDER_TOP_V, k), LADDER_RISE * k)


# ---- stores ---------------------------------------------------------------------------------------------------------
static func zone_for_category(cat: String) -> String:
	for z in ZONES:
		if ((z as Dictionary)["cats"] as Array).has(cat):
			return str((z as Dictionary)["id"])
	return ""


## How many pieces of a rack are visible for `units` items in it.
static func pieces_for(zone_id: String, units: int) -> int:
	for z in ZONES:
		var zd: Dictionary = z
		if str(zd["id"]) == zone_id:
			if units <= 0:
				return 0
			return mini(int(zd["slots"]), int(ceilf(float(units) / float(zd["units_per_slot"]))))
	return 0


# ---- test help ------------------------------------------------------------------------------------------------------
## Flood fill of the standable ground from `start` on a grid of `step` metres. Returns {cells, reached: Dictionary key -> true}.
func flood(level: int, start: Vector2, r: float, step_m: float) -> Dictionary:
	var reached: Dictionary = {}
	var key0 := _key(start, step_m)
	if not walkable(level, start.x, start.y, r):
		return {"cells": 0, "reached": reached, "start_ok": false}
	var queue: Array = [key0]
	reached[key0] = true
	var head := 0
	while head < queue.size():
		var k: Vector2i = queue[head]
		head += 1
		for dv in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var n: Vector2i = k + (dv as Vector2i)
			if reached.has(n):
				continue
			var p := Vector2(float(n.x) * step_m, float(n.y) * step_m)
			if walkable(level, p.x, p.y, r):
				reached[n] = true
				queue.append(n)
	return {"cells": reached.size(), "reached": reached, "start_ok": true}


static func _key(p: Vector2, step_m: float) -> Vector2i:
	return Vector2i(int(roundf(p.x / step_m)), int(roundf(p.y / step_m)))


## True if some standable cell within `reach` of `target` was reached by a flood.
static func near_reached(res: Dictionary, target: Vector2, reach: float, step_m: float) -> bool:
	var reached: Dictionary = res["reached"]
	var n := int(ceilf(reach / step_m))
	var c := _key(target, step_m)
	for i in range(-n, n + 1):
		for j in range(-n, n + 1):
			if reached.has(Vector2i(c.x + i, c.y + j)) and Vector2(float(i), float(j)).length() * step_m <= reach:
				return true
	return false
