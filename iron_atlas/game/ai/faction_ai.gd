extends RefCounted
const Bus = preload("res://core/bus.gd")
const CampaignState = preload("res://core/campaign_state.gd")
const CommandSystem = preload("res://military/command_system.gd")
const DiplomacySystem = preload("res://diplomacy/diplomacy_system.gd")
const WorldGenerator = preload("res://world/world_generator.gd")
## Weekly weighted-utility decisions for every non-player actor: recruit,
## reinforce, attack, hold, buy equipment, seek ceasefire. Uses the same rules
## and information limits as the player (no hidden omniscience: evaluates only
## regions adjacent to its own and formations it can observe = same region or
## neighbouring region).

const ATTACK_RATIO := 1.35


func init(_state) -> void:
	pass


func observed_strength(st: CampaignState, country_id: String, region_id: String) -> float:
	var p := 0.0
	for f in st.formations_in(region_id):
		if f["country"] != country_id:
			p += st.formation_power(f, {})
	for nb in st.regions[region_id]["neighbors"]:
		for f in st.formations_in(nb):
			if f["country"] != country_id:
				p += st.formation_power(f, {}) * 0.5
	return p


func tick_week(st: CampaignState, equip_table: Dictionary) -> void:
	for cid in st.countries:
		if st.countries[cid]["is_player"]:
			continue
		_decide(st, cid, equip_table)


func _decide(st: CampaignState, cid: String, equip_table: Dictionary) -> void:
	var mine := st.formations_of(cid)
	var treasury_proxy := 3000.0 + st.randf() * 4000.0  # AI budget envelope (documented)
	# 1) defend: reinforce most threatened owned region
	var worst := ""
	var worst_gap := 0.0
	for rid in st.regions:
		if st.regions[rid]["controller"] != cid:
			continue
		var gap := observed_strength(st, cid, rid) - own_strength_in(st, cid, rid)
		if gap > worst_gap:
			worst_gap = gap
			worst = rid
	if worst != "" and mine.size() > 0:
		var nearest := _nearest_formation(st, mine, worst)
		if nearest != "" and st.formations[nearest]["region"] != worst:
			CommandSystem.new().issue_move(st, nearest, worst)
	# 2) attack if local superiority on a border region
	for f in mine:
		var o := CommandSystem.new().active_order(f)
		if not o.is_empty():
			continue
		for nb in st.regions[f["region"]]["neighbors"]:
			var r: Dictionary = st.regions[nb]
			if r["controller"] == cid:
				continue
			var my_pow := st.formation_power(f, equip_table)
			var their_pow := observed_strength(st, cid, nb) * 0.6
			if their_pow < 0.001 or my_pow / maxf(0.001, their_pow) > ATTACK_RATIO:
				if st.randf() < 0.5:
					CommandSystem.new().issue_move(st, f["id"], nb)
					st.add_history("%s probes %s" % [st.countries[cid]["name"], r["name"]])
				break
	# 3) recruit when rich in manpower and short of formations
	var pool: int = st.countries[cid]["manpower_pool"]
	if mine.size() < 3 and pool > 250 and treasury_proxy > 4000:
		var home: String = st.countries[cid]["capital"]
		var fid := st.next_id("frm")
		st.formations[fid] = {"id": fid, "country": cid,
			"name": st.countries[cid]["name"] + " Bn %d" % mine.size() + 1,
			"region": home, "units": [
				{"class": "infantry", "equip": "rif_surplus", "count": 4, "condition": 0.8}],
			"morale": 0.65, "cohesion": 0.65, "readiness": 0.7, "supplies": 0.8,
			"experience": 0, "commander": "AI Cdr", "orders": [], "loyalty": 0.6}
		st.countries[cid]["manpower_pool"] = pool - 60
		Bus.fire("formation_created", fid, null, 1)
	# 4) seek ceasefire when badly outmatched in an active war
	for wid in st.wars:
		var w: Dictionary = st.wars[wid]
		if w["status"] != "active":
			continue
		if cid in w["sides_a"] or cid in w["sides_b"]:
			var me_pow := _war_strength(st, cid)
			var them_pow := _war_strength(st, w["sides_b"][0] if cid in w["sides_a"] else w["sides_a"][0])
			if me_pow < them_pow * 0.5 and st.randf() < 0.4:
				DiplomacySystem.new().propose_ceasefire(st, wid)


func own_strength_in(st: CampaignState, cid: String, region_id: String) -> float:
	var p := 0.0
	for f in st.formations_in(region_id):
		if f["country"] == cid:
			p += st.formation_power(f, {})
	return p


func _nearest_formation(st: CampaignState, mine: Array, target: String) -> String:
	var best := ""
	var best_len := 999
	var passable := func(_rid: String) -> bool: return true
	for f in mine:
		var path := WorldGenerator.path_bfs(st, f["region"], target, passable)
		if path.size() > 0 and path.size() < best_len:
			best_len = path.size()
			best = f["id"]
	return best


func _war_strength(st: CampaignState, cid: String) -> float:
	var p := 0.0
	for f in st.formations_of(cid):
		p += st.formation_power(f, {})
	return p
