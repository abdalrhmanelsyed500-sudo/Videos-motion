extends RefCounted
const CampaignState = preload("res://core/campaign_state.gd")
## Per-faction land supply reachability, local stockpiles and real consumption.
## Roads are interrupted by lost/contested regions or severely damaged infra.

const CONSUME := {"food": 0.35, "ammo": 0.25, "fuel": 0.3, "parts": 0.15}


func init(_state) -> void:
	pass


func formation_size(f: Dictionary) -> float:
	var s := 0.0
	for u in f["units"]:
		s += float(u["count"]) * float(CampaignState.UNIT_CLASSES[u["class"]]["supply"])
	return s + float(f.get("personnel_reserve", 0)) / 24.0


func _has_hostile(st: CampaignState, rid: String, cid: String) -> bool:
	for f in st.formations_in(rid):
		if st.is_hostile(cid, f["country"]) and st.formation_power(f, {}) > 0.0:
			return true
	return false


func reachable_regions(st: CampaignState, cid: String) -> Dictionary:
	var found := {}
	if not st.countries.has(cid):
		return found
	var cap: String = st.countries[cid]["capital"]
	if not st.regions.has(cap) or st.regions[cap]["controller"] != cid or _has_hostile(st, cap, cid):
		return found
	found[cap] = true
	var queue: Array = [cap]
	var head := 0
	while head < queue.size():
		var cur: String = queue[head]
		head += 1
		for nb in st.regions[cur]["neighbors"]:
			if found.has(nb):
				continue
			var r: Dictionary = st.regions[nb]
			if r["controller"] != cid or float(r["infra_condition"]) < 0.15 or _has_hostile(st, nb, cid):
				continue
			found[nb] = true
			queue.append(nb)
	return found


func connected_to_capital(st: CampaignState, region_id: String, country_id: String) -> bool:
	return reachable_regions(st, country_id).has(region_id)


func refresh_networks(st: CampaignState) -> Dictionary:
	var networks := {}
	for cid in st.countries:
		networks[cid] = reachable_regions(st, cid)
	for rid in st.regions:
		var r: Dictionary = st.regions[rid]
		r["supply_accessibility"] = 1.0 if networks[r["controller"]].has(rid) else 0.0
	return networks


func tick_day(st: CampaignState) -> Array:
	var warnings: Array = []
	var networks := refresh_networks(st)
	for fid in st.formations.keys():
		var f: Dictionary = st.formations[fid]
		var r: Dictionary = st.regions[f["region"]]
		var cid: String = f["country"]
		var linked: bool = networks[cid].has(f["region"])
		var own: bool = r["controller"] == cid
		var need := maxf(0.05, formation_size(f) * 0.06)
		if linked and f["region"] != st.countries[cid]["capital"] and float(r["stocks"]["food"]) < need:
			var source: Dictionary = st.regions[st.countries[cid]["capital"]]
			var moved := minf(need - float(r["stocks"]["food"]), float(source["stocks"]["food"]))
			source["stocks"]["food"] = float(source["stocks"]["food"]) - moved
			r["stocks"]["food"] = float(r["stocks"]["food"]) + moved
		var take := minf(need, float(r["stocks"]["food"])) if own else 0.0
		r["stocks"]["food"] = maxf(0.0, float(r["stocks"]["food"]) - take)
		var ratio := take / need
		if linked and ratio > 0.5:
			f["supplies"] = minf(1.0, float(f["supplies"]) + 0.08 * ratio)
		else:
			f["supplies"] = clampf(float(f["supplies"]) - 0.05 - 0.05 * (1.0 - ratio), 0.0, 1.0)
		# Ammunition is finite; stock is drawn into a normalized formation reserve.
		f["ammo_reserve"] = float(f.get("ammo_reserve", 0.8))
		if own and float(r["stocks"]["ammo"]) > 0.0 and float(f["ammo_reserve"]) < 1.0:
			var ammo_take := minf(float(r["stocks"]["ammo"]), maxf(0.02, formation_size(f) * 0.04))
			r["stocks"]["ammo"] = float(r["stocks"]["ammo"]) - ammo_take
			f["ammo_reserve"] = minf(1.0, float(f["ammo_reserve"]) + 0.05)
		if float(f["supplies"]) < 0.25:
			f["readiness"] = maxf(0.1, float(f["readiness"]) - 0.02)
			f["morale"] = maxf(0.05, float(f["morale"]) - 0.01)
		if (float(f["supplies"]) < 0.4 or float(f["ammo_reserve"]) < 0.25) \
				and int(f.get("last_supply_warning", -100)) + 7 <= st.day:
			f["last_supply_warning"] = st.day
			var message := "%s: supplies %.0f%%, ammunition %.0f%% in %s%s" % [f["name"],
				float(f["supplies"]) * 100, float(f["ammo_reserve"]) * 100, r["name"],
				" (route cut)" if not linked else ""]
			if cid == st.player_id():
				warnings.append(message)
			st.add_report("logistics", "Shortage warning", message, cid)
	return warnings


func tick_week(st: CampaignState) -> void:
	for r in st.regions.values():
		var prod := 6.0 * float(r["economy"]) * float(r["productivity"]) \
			* (0.3 + 0.7 * float(r["stability"])) * float(r["infra_condition"])
		var bonus := 4.0 if int(r["depot_level"]) > 0 else 0.0
		for k in r["stocks"]:
			r["stocks"][k] = minf(200.0, float(r["stocks"][k]) + prod * 0.5 + bonus * 0.25)
		if "fuel" in r["resources"]:
			r["stocks"]["fuel"] = minf(200.0, float(r["stocks"]["fuel"]) + 8.0 * float(r["productivity"]))
		if "grain" in r["resources"]:
			r["stocks"]["food"] = minf(200.0, float(r["stocks"]["food"]) + 8.0 * float(r["productivity"]))


func build_depot(st: CampaignState, region_id: String, cost: float, cid: String = "") -> Dictionary:
	if cid == "":
		cid = st.player_id()
	var r: Dictionary = st.regions.get(region_id, {})
	if r.is_empty() or not st.countries.has(cid):
		return {"ok": false, "error": "unknown region or faction"}
	if r["controller"] != cid:
		return {"ok": false, "error": "region not controlled"}
	if cost < 0.0 or int(r["depot_level"]) >= 2:
		return {"ok": false, "error": "invalid cost or maximum depot level"}
	if st.balance(cid) < cost:
		return {"ok": false, "error": "insufficient funds"}
	st.adjust_balance(cid, -cost)
	r["depot_level"] = int(r["depot_level"]) + 1
	st.add_report("logistics", "Depot upgraded in " + r["name"], "Depot level %d; production improved." % r["depot_level"], cid)
	return {"ok": true}
