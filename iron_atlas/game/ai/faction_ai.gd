extends RefCounted
const CampaignState = preload("res://core/campaign_state.gd")
const CommandSystem = preload("res://military/command_system.gd")
const DiplomacySystem = preload("res://diplomacy/diplomacy_system.gd")
const EconomySystem = preload("res://economy/economy_system.gd")
const MarketSystem = preload("res://economy/market_system.gd")
const Administration = preload("res://administration/administration_system.gd")
const WorldGenerator = preload("res://world/world_generator.gd")
## Weekly deterministic, local-information policy. All recruiting, purchases,
## equipment, orders and administration use the same validated systems as the player.

const ATTACK_RATIO := 1.25


func init(_state) -> void:
	pass


func observed_strength(st: CampaignState, country_id: String, region_id: String) -> float:
	if not st.can_observe(country_id, region_id):
		return 0.0
	var p := 0.0
	for f in st.formations_in(region_id):
		if st.is_hostile(country_id, f["country"]):
			p += st.formation_power(f, {})
	for nb in st.regions[region_id]["neighbors"]:
		if not st.can_observe(country_id, nb):
			continue
		for f in st.formations_in(nb):
			if st.is_hostile(country_id, f["country"]):
				p += st.formation_power(f, {}) * 0.5
	return p


func tick_week(st: CampaignState, equip_table: Dictionary) -> void:
	for cid in st.countries:
		if not st.countries[cid]["is_player"]:
			_decide(st, cid, equip_table)


func _decide(st: CampaignState, cid: String, equip_table: Dictionary) -> void:
	var mine := st.formations_of(cid)
	var cmd := CommandSystem.new()
	var market := MarketSystem.new()
	market.catalog = equip_table
	var economy := EconomySystem.new()
	economy.init(null)
	var home: String = st.countries[cid]["capital"]
	# Foreign control of this faction's claimed districts is a public, local
	# grievance. It escalates relations once per counterpart per week, not per
	# district; an active ceasefire still overrides hostility until it expires.
	var grievances := {}
	for r in st.regions.values():
		if r["country"] == cid and r["controller"] != cid:
			grievances[r["controller"]] = true
	for other in grievances:
		var relationship := st.rel(cid, other)
		var old_threat := float(relationship["threat"])
		relationship["threat"] = minf(1.0, old_threat + 0.025)
		if old_threat <= 0.55 and float(relationship["threat"]) > 0.55:
			st.add_report("diplomacy", "Territorial tensions rise", "%s contests foreign control by %s." % [st.countries[cid]["name"], st.countries[other]["name"]])
	# Recruit through the player rule and pay from the actor's actual treasury.
	if st.regions[home]["controller"] == cid and st.balance(cid) >= 900.0 \
			and int(st.countries[cid]["manpower_pool"]) >= 24:
		var home_force: Dictionary = {}
		for f in mine:
			if f["region"] == home:
				home_force = f
				break
		if home_force.is_empty() or (int(home_force.get("personnel_reserve", 0)) < 12 and st.formation_personnel(home_force) < 96):
			economy.recruit_for(st, cid, home, 24, economy.recruit_price)
			mine = st.formations_of(cid)
	# Assign real inventory to real reserves; order replacements only if affordable.
	for f in mine:
		if st.regions[f["region"]]["controller"] != cid or int(f.get("personnel_reserve", 0)) < 12:
			continue
		var store := st.inventory_for(cid)
		var count := mini(int(f["personnel_reserve"]) / 12, int(store.get("rif_surplus", 0)))
		if count > 0:
			market.equip_from_inventory(st, f["id"], "rif_surplus", count, cid)
		elif not _has_pending_order(st, cid, "rif_surplus") and st.balance(cid) > 800.0:
			market.purchase_for(st, cid, "rif_surplus", 2)
	# Stabilize one occupied region when resources permit; no free occupation.
	if st.balance(cid) > 1200.0:
		for r in st.regions.values():
			if r["controller"] == cid and r["country"] != cid and float(r["security_pressure"]) > 0.6 \
					and r["admin_focus"] == "none":
				var admin := Administration.new()
				admin.init(null)
				admin.invest(st, cid, r["id"], "security")
				break
	# Evaluate only owned regions and their immediately adjacent, visible front.
	var front := ""
	var front_score := -1.0
	for rid in st.regions:
		var r: Dictionary = st.regions[rid]
		if r["controller"] != cid:
			continue
		var border := false
		for nb in r["neighbors"]:
			if st.is_hostile(cid, st.regions[nb]["controller"]):
				border = true
				break
		var threat := observed_strength(st, cid, rid)
		var own := own_strength_in(st, cid, rid)
		var score := (threat - own) * 3.0 + float(r["strategic_value"]) + (2.0 if border else 0.0)
		if (border or threat > 0.0) and score > front_score:
			front = rid
			front_score = score
	for f in mine:
		if not cmd.active_order(f).is_empty() or st.formation_power(f, equip_table) <= 0.0:
			continue
		if float(f["supplies"]) < 0.3 or float(f["readiness"]) < 0.3:
			continue
		var current: String = f["region"]
		var best_target := ""
		var best_value := -1.0
		for nb in st.regions[current]["neighbors"]:
			var target: Dictionary = st.regions[nb]
			if not st.is_hostile(cid, target["controller"]):
				continue
			var own_power := st.formation_power(f, equip_table)
			var enemy_power := observed_strength(st, cid, nb)
			if enemy_power > 0.0 and own_power < enemy_power * ATTACK_RATIO:
				continue
			var score: float = float(target["strategic_value"]) + (3.0 if target["country"] == cid else 0.0)
			if score > best_value:
				best_value = score
				best_target = nb
		if best_target != "":
			cmd.issue_move(st, f["id"], best_target)
			st.add_history("%s contests %s" % [st.countries[cid]["name"], st.regions[best_target]["name"]])
		elif front != "" and current != front and st.regions[current]["controller"] == cid:
			var friendly_path := WorldGenerator.path_bfs(st, current, front,
				func(rid): return st.regions[rid]["controller"] == cid)
			if not friendly_path.is_empty():
				cmd.issue_move(st, f["id"], front)
	# At a hostile border, formalize a conflict only when no war already exists.
	if front != "":
		for nb in st.regions[front]["neighbors"]:
			var other: String = st.regions[nb]["controller"]
			if other != cid and float(st.rel(cid, other)["threat"]) >= 0.75 and not _has_war(st, cid, other):
				DiplomacySystem.new().declare_war(st, cid, other, "contested border")
				break
	for wid in st.wars:
		var w: Dictionary = st.wars[wid]
		if w["status"] != "active" or (cid not in w["sides_a"] and cid not in w["sides_b"]):
			continue
		var observed := observed_strength(st, cid, front) if front != "" else 0.0
		var own := 0.0
		for f in mine:
			own += st.formation_power(f, equip_table)
		if (st.balance(cid) < 200.0 or (observed > 0.0 and own < observed * 0.5)) \
				and int(st.countries[cid].get("last_peace_offer", -100)) + 21 <= st.day:
			st.countries[cid]["last_peace_offer"] = st.day
			DiplomacySystem.new().propose_ceasefire(st, wid, cid)


func _has_pending_order(st: CampaignState, cid: String, item: String) -> bool:
	for o in st.market_orders.values():
		if o.get("owner", st.player_id()) == cid and o["item"] == item and o["status"] in ["in_transit", "delayed"]:
			return true
	return false


func _has_war(st: CampaignState, a: String, b: String) -> bool:
	for w in st.wars.values():
		if ((a in w["sides_a"] and b in w["sides_b"]) or (b in w["sides_a"] and a in w["sides_b"])) \
				and w["status"] in ["active", "ceasefire"]:
			return true
	return false


func own_strength_in(st: CampaignState, cid: String, region_id: String) -> float:
	var p := 0.0
	for f in st.formations_in(region_id):
		if f["country"] == cid:
			p += st.formation_power(f, {})
	return p
