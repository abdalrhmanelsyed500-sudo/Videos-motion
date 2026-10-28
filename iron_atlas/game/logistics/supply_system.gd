extends RefCounted
const CampaignState = preload("res://core/campaign_state.gd")
const WorldGenerator = preload("res://world/world_generator.gd")
## Depots, stocks, consumption, supply graph (BFS through controlled/connected
## regions to the owner's capital), shortage effects with warnings.

const CONSUME := {"food": 0.35, "ammo": 0.25, "fuel": 0.3, "parts": 0.15}


func init(_state) -> void:
	pass


func formation_size(f: Dictionary) -> float:
	var s := 0.0
	for u in f["units"]:
		s += float(u["count"]) * float(CampaignState.UNIT_CLASSES[u["class"]]["supply"])
	return s


func connected_to_capital(st: CampaignState, region_id: String, country_id: String) -> bool:
	var cap: String = st.countries[country_id]["capital"]
	var passable := func(rid: String) -> bool:
		return st.regions[rid]["controller"] == country_id or rid == region_id
	return not WorldGenerator.path_bfs(st, region_id, cap, passable).is_empty()


func tick_day(st: CampaignState) -> Array:
	var warnings: Array = []
	for fid in st.formations.keys():
		var f: Dictionary = st.formations[fid]
		var r: Dictionary = st.regions[f["region"]]
		var size := formation_size(f)
		var need := {}
		for k in CONSUME:
			need[k] = CONSUME[k] * size * 0.1
		var covered := 0.0
		var total := 0.0
		var linked := connected_to_capital(st, f["region"], f["country"])
		for k in need:
			total += 1.0
			var take := minf(need[k], float(r["stocks"][k]))
			r["stocks"][k] = float(r["stocks"][k]) - take
			covered += take / maxf(0.001, need[k])
		var ratio := covered / maxf(0.001, total)
		if linked:
			# depots replenish formation supplies slowly from national pipeline
			f["supplies"] = minf(1.0, float(f["supplies"]) + 0.10 * ratio + 0.05)
		else:
			# cut off from the national pipeline: local stocks only delay attrition
			f["supplies"] = clampf(float(f["supplies"]) - 0.05 - 0.05 * (1.0 - ratio), 0.0, 1.0)
		if float(f["supplies"]) < 0.25:
			f["readiness"] = maxf(0.1, float(f["readiness"]) - 0.02)
			f["morale"] = maxf(0.05, float(f["morale"]) - 0.01)
			warnings.append("%s low on supply in %s" % [f["name"], r["name"]])
	return warnings


func tick_week(st: CampaignState) -> void:
	# regional stock production + depot throughput
	for rid in st.regions:
		var r: Dictionary = st.regions[rid]
		var prod := 6.0 * float(r["economy"]) * (0.5 + 0.5 * float(r["stability"]))
		var bonus := 4.0 if int(r["depot_level"]) > 0 else 0.0
		for k in r["stocks"]:
			r["stocks"][k] = minf(200.0, float(r["stocks"][k]) + prod * 0.5 + bonus * 0.25)
		if "fuel" in r["resources"]:
			r["stocks"]["fuel"] = minf(200.0, float(r["stocks"]["fuel"]) + 8.0)
		if "grain" in r["resources"]:
			r["stocks"]["food"] = minf(200.0, float(r["stocks"]["food"]) + 8.0)


func build_depot(st: CampaignState, region_id: String, cost: float) -> Dictionary:
	var r: Dictionary = st.regions.get(region_id, {})
	if r.is_empty():
		return {"ok": false, "error": "unknown region"}
	if int(r["depot_level"]) >= 2:
		return {"ok": false, "error": "depot already at max level"}
	if st.treasury < cost:
		return {"ok": false, "error": "insufficient funds"}
	st.treasury -= cost
	r["depot_level"] = int(r["depot_level"]) + 1
	st.add_report("logistics", "Depot upgraded in " + r["name"],
		"Depot level %d. Regional throughput improved." % r["depot_level"])
	return {"ok": true}
