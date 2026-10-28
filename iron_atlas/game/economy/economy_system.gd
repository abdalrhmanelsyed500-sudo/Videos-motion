extends RefCounted
const Bus = preload("res://core/bus.gd")
const CampaignState = preload("res://core/campaign_state.gd")
## Daily upkeep, weekly regional tax income, monthly macro drift.
## Every money change is an explicit transaction recorded in reports/history.

const WAGE_PER_PERSON := 0.9
const EQUIP_UPKEEP := {"tier1": 0.6, "tier2": 1.4, "tier3": 2.6}


func init(_state) -> void:
	pass


func personnel_upkeep(st: CampaignState) -> float:
	var cost := 0.0
	for fid in st.formations:
		var f: Dictionary = st.formations[fid]
		if f["country"] != st.player_id():
			continue
		cost += st.formation_personnel(f) * WAGE_PER_PERSON * 0.02
	return cost


func equipment_upkeep(st: CampaignState, equip_table: Dictionary) -> float:
	var cost := 0.0
	for fid in st.formations:
		var f: Dictionary = st.formations[fid]
		if f["country"] != st.player_id():
			continue
		for u in f["units"]:
			var eq: Dictionary = equip_table.get(u["equip"], {})
			cost += float(u["count"]) * float(eq.get("upkeep", 0.5)) * 0.05
	return cost


func tick_day(st: CampaignState, equip_table: Dictionary) -> float:
	var spent := personnel_upkeep(st) + equipment_upkeep(st, equip_table)
	st.treasury -= spent
	return spent


func tick_week(st: CampaignState) -> float:
	var income := 0.0
	var pid := st.player_id()
	for rid in st.regions:
		var r: Dictionary = st.regions[rid]
		if r["controller"] != pid:
			continue
		var base := float(r["economy"]) * 90.0 * (float(r["population"]) / 250000.0 + 0.4)
		income += base * float(st.policies["tax"]) * (0.5 + 0.5 * float(r["stability"])) \
			* (0.6 + 0.4 * float(r["legitimacy"]))
	st.treasury += income
	if income > 0:
		st.add_report("economy", "Weekly revenue collected",
			"%.0f credits from %d controlled region(s)." % [income, _controlled_count(st, pid)])
	return income


func tick_month(st: CampaignState) -> void:
	st.inflation = clampf(float(st.inflation) + (st.randf() - 0.5) * 0.004, -0.02, 0.12)
	var pid := st.player_id()
	var deficit := st.treasury < 0.0
	if deficit:
		st.stability = maxf(0.05, float(st.stability) - 0.03)
		st.add_report("economy", "Treasury in deficit",
			"Unpaid wages and suppliers are eroding stability. Cut spending or raise revenue.")
		Bus.fire("notification", "Treasury deficit: stability falling", 2, 2)
	# stability drifts toward legitimacy/support average
	var sup := 0.0
	var n := 0
	for rid in st.regions:
		var r: Dictionary = st.regions[rid]
		if r["controller"] == pid:
			sup += (float(r["support_player"]) + float(r["legitimacy"])) * 0.5
			n += 1
	if n > 0:
		var target := sup / n
		st.stability = clampf(float(st.stability) + (target - float(st.stability)) * 0.1, 0.0, 1.0)


func _controlled_count(st: CampaignState, pid: String) -> int:
	var n := 0
	for rid in st.regions:
		if st.regions[rid]["controller"] == pid:
			n += 1
	return n


func recruit(st: CampaignState, region_id: String, persons: int, cost_per: float) -> Dictionary:
	var r: Dictionary = st.regions.get(region_id, {})
	if r.is_empty():
		return {"ok": false, "error": "unknown region"}
	if r["controller"] != st.player_id():
		return {"ok": false, "error": "region not under your control"}
	var pool: int = st.countries[st.player_id()]["manpower_pool"]
	var willing := int(persons * (0.5 + float(r["support_player"])))
	willing = mini(willing, pool)
	if willing <= 0:
		return {"ok": false, "error": "no willing recruits here"}
	var cost := willing * cost_per
	if st.treasury < cost:
		return {"ok": false, "error": "insufficient funds (%.0f needed)" % cost}
	st.treasury -= cost
	st.countries[st.player_id()]["manpower_pool"] = pool - willing
	# add to nearest player formation in region, else create a new one
	var target: Dictionary = {}
	for f in st.formations_in(region_id):
		if f["country"] == st.player_id():
			target = f
			break
	if target.is_empty():
		var fid := st.next_id("frm")
		target = {"id": fid, "country": st.player_id(), "name": "Militia " + fid,
			"region": region_id, "units": [], "morale": 0.6, "cohesion": 0.6,
			"readiness": 0.6, "supplies": 0.7, "experience": 0, "commander": "New Cdr",
			"orders": [], "loyalty": 0.6}
		st.formations[fid] = target
		Bus.fire("formation_created", fid, null, 1)
	target["personnel_reserve"] = int(target.get("personnel_reserve", 0)) + willing
	st.add_report("military", "Recruits enlisted in " + r["name"],
		"%d recruits for %.0f credits." % [willing, cost])
	return {"ok": true, "recruited": willing, "cost": cost}
