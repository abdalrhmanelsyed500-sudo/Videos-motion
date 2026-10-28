extends RefCounted
const CampaignState = preload("res://core/campaign_state.gd")
## Deterministic staged world generation (seed -> continents -> regions graph ->
## terrain/climate/resources -> cities/infra -> countries/borders -> relations).
## Stage 1 slice: 24 regions, 2 continents, 5 actors (4 countries + player org).

const CONTINENTS := {
	"veldara": {"climate_bias": ["plains", "forest", "hills", "urban"], "name": "Veldara"},
	"korash": {"climate_bias": ["desert", "badlands", "plains", "mountain"], "name": "Korash"},
}
const TERRAIN_MOD := {
	"plains": {"move": 1.0, "def": 1.0}, "forest": {"move": 0.7, "def": 1.25},
	"hills": {"move": 0.8, "def": 1.15}, "urban": {"move": 0.9, "def": 1.35},
	"desert": {"move": 1.1, "def": 0.9}, "badlands": {"move": 0.75, "def": 1.1},
	"mountain": {"move": 0.5, "def": 1.5}, "marsh": {"move": 0.45, "def": 1.1},
	"snow": {"move": 0.6, "def": 1.1}, "coast": {"move": 1.0, "def": 1.0},
}

const REGION_NAMES_A := ["Vardena Capital", "Mirsk", "Olengrad", "Talvo", "Brenna",
	"Kasparov", "Dunmar", "Selitz", "Arvenholm", "Petrava", "Luskan", "Vossberg",
	"Ravenport", "Ilmenau"]
const REGION_NAMES_B := ["Kara-Tash", "Zafir", "Ostran-Min", "Duneheim", "Sabil",
	"Meridia Port", "Halvorn", "Qessab", "Tarkis", "Anvariyeh"]


static func generate(seed_int: int, scenario: Dictionary) -> CampaignState:
	var st := CampaignState.new()
	st.seed = seed_int
	st.rng_state = seed_int if seed_int != 0 else 7
	st.reseed()
	var names_a: Array = REGION_NAMES_A.duplicate()
	var names_b: Array = REGION_NAMES_B.duplicate()
	# --- stage 1-3: continents + region nodes with positions on a 100x56 grid
	var layout_a := _ring_layout(14, Vector2(30, 16), Vector2(24, 11), st)
	var layout_b := _ring_layout(10, Vector2(74, 38), Vector2(20, 10), st)
	for i in layout_a.size():
		_add_region(st, "reg_%02d" % (i + 1), names_a[i], "veldara", layout_a[i], st)
	for i in layout_b.size():
		_add_region(st, "reg_%02d" % (15 + i), names_b[i], "korash", layout_b[i], st)
	# --- stage 4: neighbor graph: ring links + chords + one intercontinent bridge
	var ids: Array = st.regions.keys()
	for i in range(1, 14):
		_link(st, "reg_%02d" % i, "reg_%02d" % (i + 1))
	_link(st, "reg_01", "reg_14")
	for chord in [[2, 6], [4, 10], [7, 12], [1, 8]]:
		_link(st, "reg_%02d" % chord[0], "reg_%02d" % chord[1])
	for i in range(15, 24):
		_link(st, "reg_%02d" % i, "reg_%02d" % (i + 1))
	_link(st, "reg_15", "reg_24")
	for chord in [[16, 20], [18, 23]]:
		_link(st, "reg_%02d" % chord[0], "reg_%02d" % chord[1])
	_link(st, "reg_13", "reg_21")  # strategic bridge between continents
	# --- stage 5-7: countries + ownership
	var ctry_defs := [
		["cty_vardena", "Republic of Vardena", [0.35, 0.55, 0.35], "reg_01", false],
		["cty_karsak", "Karsak Federation", [0.55, 0.35, 0.35], "reg_06", false],
		["cty_meridia", "Meridian League", [0.35, 0.4, 0.6], "reg_18", false],
		["cty_ostran", "Ostran Compact", [0.55, 0.5, 0.3], "reg_22", false],
		["cty_player", "Free Vardena Movement", [0.75, 0.65, 0.25], "reg_09", true],
	]
	for c in ctry_defs:
		st.countries[c[0]] = {"id": c[0], "name": c[1], "color": c[2], "capital": c[3],
			"is_player": c[4], "manpower_pool": 400 + int(st.randf() * 500),
			"doctrine": "balanced", "traits": []}
	var ownership := {"cty_vardena": [1, 2, 3, 4, 5, 9, 10], "cty_karsak": [6, 7, 8, 11, 12],
		"cty_meridia": [15, 16, 17, 18, 19], "cty_ostran": [20, 21, 22, 23, 24],
		"cty_player": [13, 14]}
	for cid in ownership:
		for n in ownership[cid]:
			var rid := "reg_%02d" % n
			st.regions[rid]["country"] = cid
			st.regions[rid]["controller"] = cid
	# contested flavour: region 9 (player safehouse zone) is inside Vardena's claim
	st.regions["reg_09"]["country"] = "cty_vardena"
	st.regions["reg_09"]["controller"] = "cty_player"
	# --- stage 8: relations seed
	for a in st.countries:
		for b in st.countries:
			if a < b:
				var r := st.rel(a, b)
				r["trust"] = 0.2 + st.randf() * 0.4
				r["warmth"] = 0.2 + st.randf() * 0.4
				r["threat"] = 0.1 + st.randf() * 0.4
	st.rel("cty_player", "cty_vardena")["threat"] = 0.8
	st.rel("cty_player", "cty_vardena")["warmth"] = 0.05
	# --- stage 9-10: starting formations + scenario economics
	_apply_scenario(st, scenario)
	# --- stage 11: validation
	var errs := _validate_world(st)
	if errs.size():
		push_warning("world gen warnings: " + "; ".join(errs))
	return st


static func _ring_layout(n: int, center: Vector2, radius: Vector2, st: CampaignState) -> Array:
	var out: Array = []
	for i in n:
		var a := TAU * i / n + st.randf() * 0.18
		out.append([roundf(center.x + cos(a) * radius.x * (0.8 + st.randf() * 0.4)),
			roundf(center.y + sin(a) * radius.y * (0.8 + st.randf() * 0.4))])
	return out


static func _add_region(st: CampaignState, id: String, name: String, continent: String, pos: Array, s) -> void:
	var bias: Array = CONTINENTS[continent]["climate_bias"]
	var terrain: String = bias[int(s.randf() * bias.size()) % bias.size()]
	var pop := int(40 + s.randf() * 460) * 1000
	var r := {
		"id": id, "name": name, "continent": continent, "pos": pos,
		"terrain": terrain, "climate": "temperate" if continent == "veldara" else "arid",
		"country": "", "controller": "", "prev_controller": "",
		"population": pop, "urbanization": 0.2 + s.randf() * 0.6,
		"economy": roundf((0.4 + s.randf() * 0.8) * (pop / 200000.0) * 100) / 100.0,
		"resources": _roll_resources(s), "infra": 1 + int(s.randf() * 4),
		"stability": roundf((0.4 + s.randf() * 0.4) * 100) / 100.0,
		"support_player": roundf(s.randf() * 0.5 * 100) / 100.0,
		"legitimacy": roundf((0.3 + s.randf() * 0.5) * 100) / 100.0,
		"neighbors": [], "stocks": {"food": 60.0, "ammo": 40.0, "fuel": 40.0, "parts": 25.0},
		"depot_level": 1 if s.randf() < 0.4 else 0, "history": [],
	}
	st.regions[id] = r


static func _roll_resources(s) -> Array:
	var pool := ["grain", "steel", "fuel", "minerals", "electronics", "timber"]
	var out: Array = []
	for i in range(int(s.randf() * 3)):
		var pick: String = pool[int(s.randf() * pool.size()) % pool.size()]
		if pick not in out:
			out.append(pick)
	return out


static func _link(st: CampaignState, a: String, b: String) -> void:
	if a == b or not st.regions.has(a) or not st.regions.has(b):
		return
	if b not in st.regions[a]["neighbors"]:
		st.regions[a]["neighbors"].append(b)
	if a not in st.regions[b]["neighbors"]:
		st.regions[b]["neighbors"].append(a)


static func _apply_scenario(st: CampaignState, sc: Dictionary) -> void:
	st.treasury = float(sc.get("treasury", 12000))
	st.day = int(sc.get("start_day", 0))
	st.stability = float(sc.get("stability", 0.45))
	st.inventory = sc.get("inventory", {}).duplicate(true)
	var start := sc.get("start_formations", [])
	for fdef in start:
		var fid := st.next_id("frm")
		st.formations[fid] = {
			"id": fid, "country": fdef["country"], "name": fdef["name"],
			"region": fdef["region"], "units": fdef["units"].duplicate(true),
			"morale": 0.7, "cohesion": 0.7, "readiness": 0.8, "supplies": 0.9,
			"experience": 0, "commander": fdef.get("commander", "Staff"),
			"orders": [], "loyalty": 0.7,
		}
	# rival starting garrisons so the world is not empty
	var garrisons := [["cty_vardena", "reg_02", "1st Garrison"], ["cty_vardena", "reg_05", "2nd Garrison"],
		["cty_karsak", "reg_07", "Karsak Border Guard"], ["cty_meridia", "reg_17", "League Militia"],
		["cty_ostran", "reg_23", "Ostran Rifle Bn"]]
	for g in garrisons:
		var fid := st.next_id("frm")
		st.formations[fid] = {"id": fid, "country": g[0], "name": g[2], "region": g[1],
			"units": [{"class": "infantry", "equip": "rif_surplus", "count": 4, "condition": 0.8}],
			"morale": 0.65, "cohesion": 0.65, "readiness": 0.75, "supplies": 0.8,
			"experience": 0, "commander": "Local Cdr", "orders": [], "loyalty": 0.6}
	st.add_history("Campaign begins: " + sc.get("title", "Vardena crisis"))


static func _validate_world(st: CampaignState) -> Array:
	var errs: Array = []
	for rid in st.regions:
		var r: Dictionary = st.regions[rid]
		if r["neighbors"].is_empty():
			errs.append("isolated region " + rid)
		if r["controller"] == "":
			errs.append("unowned region " + rid)
	for cid in st.countries:
		var cap: String = st.countries[cid]["capital"]
		if not st.regions.has(cap):
			errs.append("bad capital for " + cid)
	return errs


static func path_bfs(st: CampaignState, from_id: String, to_id: String, passable: Callable) -> Array:
	if from_id == to_id:
		return [from_id]
	var prev := {from_id: ""}
	var q: Array = [from_id]
	while q.size():
		var cur: String = q.pop_front()
		for nb in st.regions[cur]["neighbors"]:
			if prev.has(nb):
				continue
			if not passable.call(nb):
				continue
			prev[nb] = cur
			if nb == to_id:
				var path: Array = [to_id]
				var walk := to_id
				while prev[walk] != "":
					walk = prev[walk]
					path.push_front(walk)
				return path
			q.append(nb)
	return []
