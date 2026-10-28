extends RefCounted
const Bus = preload("res://core/bus.gd")
const CampaignState = preload("res://core/campaign_state.gd")
const WorldGenerator = preload("res://world/world_generator.gd")
const Administration = preload("res://administration/administration_system.gd")
## Orders traverse land neighbors only; sea_neighbors require future naval rules.

const SUPPLY_PER_MOVE := 0.06


func init(_state) -> void:
	pass


func issue_move(st: CampaignState, formation_id: String, target_region: String) -> Dictionary:
	var f: Dictionary = st.formations.get(formation_id, {})
	if f.is_empty():
		return {"ok": false, "error": "unknown formation"}
	if not st.regions.has(target_region):
		return {"ok": false, "error": "unknown target region"}
	if f["region"] == target_region:
		return {"ok": false, "error": "already there"}
	var path := WorldGenerator.path_bfs(st, f["region"], target_region, func(_rid): return true)
	if path.is_empty():
		return {"ok": false, "error": "no land route"}
	var oid := st.next_id("ord")
	var order := {"id": oid, "formation": formation_id, "type": "move",
		"target_region": target_region, "path": path.slice(1), "progress": 0.0,
		"status": "active", "issued_day": st.day, "retreat": false}
	f["orders"].append(order)
	return {"ok": true, "order": order}


func issue_hold(st: CampaignState, formation_id: String) -> Dictionary:
	var f: Dictionary = st.formations.get(formation_id, {})
	if f.is_empty():
		return {"ok": false, "error": "unknown formation"}
	f["orders"] = []
	return {"ok": true}


func issue_retreat(st: CampaignState, formation_id: String) -> Dictionary:
	var f: Dictionary = st.formations.get(formation_id, {})
	if f.is_empty():
		return {"ok": false, "error": "unknown formation"}
	var best := ""
	var best_score := -1.0
	for nb in st.regions[f["region"]]["neighbors"]:
		var r: Dictionary = st.regions[nb]
		if r["controller"] != f["country"] or _hostiles_present(st, nb, f["country"]):
			continue
		var score: float = float(r["stability"]) + float(r["supply_accessibility"])
		if score > best_score:
			best_score = score
			best = nb
	if best == "":
		return {"ok": false, "error": "no friendly adjacent region to retreat to"}
	f["orders"] = []
	f["morale"] = maxf(0.15, float(f["morale"]) - 0.15)
	var result := issue_move(st, formation_id, best)
	if result["ok"]:
		result["order"]["retreat"] = true
	return result


func cancel_order(st: CampaignState, order_id: String) -> Dictionary:
	for f in st.formations.values():
		var orders: Array = f["orders"]
		for i in orders.size():
			if orders[i]["id"] == order_id:
				orders[i]["status"] = "cancelled"
				orders.remove_at(i)
				return {"ok": true}
	return {"ok": false, "error": "order not found"}


func active_order(f: Dictionary) -> Dictionary:
	for o in f["orders"]:
		if o["status"] == "active":
			return o
	return {}


func tick_day(st: CampaignState, equip_table: Dictionary) -> void:
	for fid in st.formations.keys():
		if not st.formations.has(fid):
			continue
		var f: Dictionary = st.formations[fid]
		var o := active_order(f)
		if o.is_empty() or o["type"] != "move":
			continue
		if o["path"].is_empty():
			f["orders"].erase(o)
			continue
		if _hostiles_present(st, f["region"], f["country"]) and not bool(o.get("retreat", false)):
			continue
		var r: Dictionary = st.regions[f["region"]]
		var speed_mod: float = WorldGenerator.TERRAIN_MOD[r["terrain"]]["move"]
		var cls_speed := 1.0
		var fuel_need := 0.0
		for u in f["units"]:
			cls_speed = minf(cls_speed, float(CampaignState.UNIT_CLASSES[u["class"]]["speed"]))
			fuel_need += float(equip_table.get(u["equip"], {}).get("fuel", 0.0)) * float(u["count"]) * 0.05
		if fuel_need > 0.0:
			var available := float(r["stocks"]["fuel"]) if r["controller"] == f["country"] else 0.0
			var used := minf(available, fuel_need)
			r["stocks"]["fuel"] = maxf(0.0, float(r["stocks"]["fuel"]) - used)
			if used < fuel_need * 0.5:
				speed_mod *= 0.35
				if int(f.get("last_fuel_warning", -100)) + 7 <= st.day:
					f["last_fuel_warning"] = st.day
					st.add_report("logistics", "Fuel shortage", f["name"] + " is moving slowly without fuel.", f["country"])
		if float(f["supplies"]) < 0.25:
			speed_mod *= 0.5
		o["progress"] = float(o["progress"]) + 0.55 * cls_speed * speed_mod
		f["supplies"] = maxf(0.0, float(f["supplies"]) - SUPPLY_PER_MOVE)
		if float(o["progress"]) >= 1.0:
			o["progress"] = 0.0
			var from_id: String = f["region"]
			f["region"] = o["path"].pop_front()
			if o["path"].is_empty():
				o["status"] = "completed"
				f["orders"].erase(o)
				st.regions[f["region"]]["history"].append({"day": st.day, "text": f["name"] + " arrived"})
			_check_control(st, from_id)
			_check_control(st, f["region"])


func _check_control(st: CampaignState, region_id: String) -> void:
	var r: Dictionary = st.regions[region_id]
	var present := st.formations_in(region_id)
	var strongest: Dictionary = {}
	for f in present:
		if st.formation_power(f, {}) <= 0.0:
			continue
		if strongest.is_empty() or st.formation_power(f, {}) > st.formation_power(strongest, {}):
			strongest = f
	if strongest.is_empty() or strongest["country"] == r["controller"]:
		return
	if not st.is_hostile(strongest["country"], r["controller"]):
		return # neutral forces do not capture neutral territory
	for f in present:
		if st.is_hostile(f["country"], strongest["country"]) and st.formation_power(f, {}) > 0.0:
			return
	Administration.capture(st, region_id, strongest["country"])


func _hostiles_present(st: CampaignState, region_id: String, cid: String) -> bool:
	for f in st.formations_in(region_id):
		if st.is_hostile(cid, f["country"]) and st.formation_power(f, {}) > 0.0:
			return true
	return false


func _at_war_or_hostile(st: CampaignState, a: String, b: String) -> bool:
	return st.is_hostile(a, b)
