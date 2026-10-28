extends RefCounted
const Bus = preload("res://core/bus.gd")
const CampaignState = preload("res://core/campaign_state.gd")
## Shared faction economy. Player balance is st.treasury; rivals have persistent
## balances in countries. Recruits are people; each equipped unit is 12 people.

const WAGE_PER_PERSON_DAY := 0.018
var recruit_price: float = 25.0


func init(_state) -> void:
	var file := FileAccess.open("res://data/regional_rules.json", FileAccess.READ)
	if file != null:
		var parsed = JSON.parse_string(file.get_as_text())
		if typeof(parsed) == TYPE_DICTIONARY:
			recruit_price = float(parsed.get("recruit_cost_per_person", 25.0))
		file.close()


func personnel_upkeep(st: CampaignState, cid: String = "") -> float:
	if cid == "":
		cid = st.player_id()
	var cost := 0.0
	for f in st.formations_of(cid):
		cost += (st.formation_personnel(f) + int(f.get("wounded", 0)) * 0.5) * WAGE_PER_PERSON_DAY
	return cost


func equipment_upkeep(st: CampaignState, equip_table: Dictionary, cid: String = "") -> float:
	if cid == "":
		cid = st.player_id()
	var cost := 0.0
	for f in st.formations_of(cid):
		for u in f["units"]:
			var eq: Dictionary = equip_table.get(u["equip"], {})
			cost += float(u["count"]) * float(eq.get("upkeep", 0.0)) / 7.0
		for id in f.get("attachments", {}):
			var attachment: Dictionary = equip_table.get(id, {})
			cost += float(f["attachments"][id]) * float(attachment.get("upkeep", 0.0)) / 7.0
	for id in st.inventory_for(cid):
		var eq: Dictionary = equip_table.get(id, {})
		cost += float(st.inventory_for(cid)[id]) * float(eq.get("upkeep", 0.0)) / 7.0
	return cost


func tick_day(st: CampaignState, equip_table: Dictionary) -> float:
	var player_spent := 0.0
	for cid in st.countries:
		var spent := personnel_upkeep(st, cid) + equipment_upkeep(st, equip_table, cid)
		st.adjust_balance(cid, -spent)
		if cid == st.player_id():
			player_spent = spent
		if st.balance(cid) < 0.0:
			for f in st.formations_of(cid):
				f["readiness"] = maxf(0.1, float(f["readiness"]) - 0.005)
				f["morale"] = maxf(0.05, float(f["morale"]) - 0.003)
	return player_spent


func tick_week(st: CampaignState) -> float:
	var revenues := {}
	for rid in st.regions:
		var r: Dictionary = st.regions[rid]
		var cid: String = r["controller"]
		var base := float(r["economy"]) * 90.0 * (float(r["population"]) / 250000.0 + 0.4)
		var rate := float(st.policies.get("tax", 0.5)) if cid == st.player_id() else 0.5
		var output := base * rate * (0.5 + 0.5 * float(r["stability"])) \
			* (0.4 + 0.6 * float(r["legitimacy"])) * float(r["productivity"]) \
			* (0.4 + 0.6 * float(r["infra_condition"]))
		revenues[cid] = float(revenues.get(cid, 0.0)) + output
	for cid in revenues:
		st.adjust_balance(cid, float(revenues[cid]))
	var player_income := float(revenues.get(st.player_id(), 0.0))
	if player_income > 0:
		st.add_report("economy", "Weekly revenue collected",
			"%.0f credits from %d controlled region(s); productivity and stability affect receipts." % [
			player_income, _controlled_count(st, st.player_id())])
	return player_income


func tick_month(st: CampaignState) -> void:
	st.inflation = clampf(st.inflation + (st.randf() - 0.5) * 0.004, -0.02, 0.12)
	# All factions pay the same monthly interest on a negative balance.
	for cid in st.countries:
		var balance := st.balance(cid)
		if balance < 0.0:
			st.adjust_balance(cid, balance * 0.01)
	if st.treasury < 0.0:
		st.stability = maxf(0.05, st.stability - 0.03)
		st.add_report("economy", "Treasury in deficit", "Debt interest and unpaid personnel are eroding readiness.")
		Bus.fire("notification", "Treasury deficit: readiness falling", 2, 2)
	var sup := 0.0
	var n := 0
	for r in st.regions.values():
		if r["controller"] == st.player_id():
			sup += (float(r["political_support"]) + float(r["legitimacy"])) * 0.5
			n += 1
	if n > 0:
		st.stability = clampf(st.stability + (sup / n - st.stability) * 0.1, 0.0, 1.0)


func _controlled_count(st: CampaignState, cid: String) -> int:
	var n := 0
	for r in st.regions.values():
		if r["controller"] == cid:
			n += 1
	return n


func recruit(st: CampaignState, region_id: String, persons: int, cost_per: float) -> Dictionary:
	return recruit_for(st, st.player_id(), region_id, persons, cost_per)


func recruit_for(st: CampaignState, cid: String, region_id: String, persons: int, cost_per: float) -> Dictionary:
	var r: Dictionary = st.regions.get(region_id, {})
	if r.is_empty() or not st.countries.has(cid):
		return {"ok": false, "error": "unknown faction or region"}
	if persons <= 0 or not is_equal_approx(cost_per, recruit_price):
		return {"ok": false, "error": "invalid quantity or configured recruitment price"}
	if r["controller"] != cid:
		return {"ok": false, "error": "region not under your control"}
	var pool := int(st.countries[cid]["manpower_pool"])
	var willingness := clampf(0.5 + float(r["political_support"]), 0.2, 1.0)
	var willing := mini(persons, mini(int(floor(persons * willingness)), pool))
	if willing <= 0:
		return {"ok": false, "error": "no willing recruits here"}
	var cost := willing * cost_per
	if st.balance(cid) < cost:
		return {"ok": false, "error": "insufficient funds (%.0f needed)" % cost}
	st.adjust_balance(cid, -cost)
	st.countries[cid]["manpower_pool"] = pool - willing
	var target: Dictionary = {}
	for f in st.formations_in(region_id):
		if f["country"] == cid:
			target = f
			break
	if target.is_empty():
		var fid := st.next_id("frm")
		target = {"id": fid, "country": cid, "name": "Militia " + fid,
			"region": region_id, "units": [], "morale": 0.6, "cohesion": 0.6,
			"readiness": 0.6, "supplies": 0.7, "experience": 0, "commander": "Local staff",
			"orders": [], "loyalty": 0.6}
		CampaignState.apply_formation_defaults(target)
		st.formations[fid] = target
		Bus.fire("formation_created", fid, null, 1)
	target["personnel_reserve"] = int(target.get("personnel_reserve", 0)) + willing
	st.add_report("military", "Recruits enlisted in " + r["name"],
		"%s enlisted %d people for %.0f credits. Assign equipment to form squads." % [
		st.countries[cid]["name"], willing, cost], cid)
	return {"ok": true, "recruited": willing, "cost": cost, "formation": target["id"]}
