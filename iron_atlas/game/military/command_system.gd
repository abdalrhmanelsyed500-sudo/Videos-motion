extends RefCounted
const Bus = preload("res://core/bus.gd")
const CampaignState = preload("res://core/campaign_state.gd")
const WorldGenerator = preload("res://world/world_generator.gd")
## Orders with validation, queueing, cancellation and status feedback.
## Order: {id, formation, type, target_region, path, progress, status, issued_day}

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
	var passable := func(rid: String) -> bool: return true
	var path := WorldGenerator.path_bfs(st, f["region"], target_region, passable)
	if path.is_empty():
		return {"ok": false, "error": "no land route"}
	var oid := st.next_id("ord")
	var order := {"id": oid, "formation": formation_id, "type": "move",
		"target_region": target_region, "path": path.slice(1), "progress": 0.0,
		"status": "active", "issued_day": st.day}
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
		var score: float = (1.0 if r["controller"] == f["country"] else 0.0) + r["stability"]
		if score > best_score:
			best_score = score
			best = nb
	if best == "":
		return {"ok": false, "error": "nowhere to retreat"}
	f["morale"] = maxf(0.15, float(f["morale"]) - 0.15)
	return issue_move(st, formation_id, best)


func cancel_order(st: CampaignState, order_id: String) -> Dictionary:
	for fid in st.formations:
		var orders: Array = st.formations[fid]["orders"]
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
		var f: Dictionary = st.formations[fid]
		var o := active_order(f)
		if o.is_empty() or o["type"] != "move":
			continue
		var terrain: String = st.regions[f["region"]]["terrain"]
		var speed_mod: float = WorldGenerator.TERRAIN_MOD[terrain]["move"]
		var cls_speed := 1.0
		for u in f["units"]:
			cls_speed = minf(cls_speed, float(CampaignState.UNIT_CLASSES[u["class"]]["speed"]))
		if float(f["supplies"]) < 0.25:
			speed_mod *= 0.5
		o["progress"] += 0.55 * cls_speed * speed_mod
		f["supplies"] = maxf(0.0, float(f["supplies"]) - SUPPLY_PER_MOVE)
		if o["progress"] >= 1.0:
			o["progress"] = 0.0
			var from_id: String = f["region"]
			f["region"] = o["path"].pop_front()
			st.regions[from_id]["history"].append({"day": st.day, "text": f["name"] + " departed"})
			if o["path"].is_empty():
				o["status"] = "completed"
				f["orders"].erase(o)
				st.regions[f["region"]]["history"].append(
					{"day": st.day, "text": f["name"] + " arrived"})
			_check_control(st, f["region"])


func _check_control(st: CampaignState, region_id: String) -> void:
	var r: Dictionary = st.regions[region_id]
	var present := st.formations_in(region_id)
	if present.is_empty():
		return
	var strongest: Dictionary = present[0]
	for f in present:
		if st.formation_power(f, {}) > st.formation_power(strongest, {}):
			strongest = f
	var enemy_present := false
	for f in present:
		if f["country"] != strongest["country"] and _at_war_or_hostile(st, f["country"], strongest["country"]):
			enemy_present = true
	if enemy_present:
		return  # contested: control changes only via combat resolution
	if r["controller"] != strongest["country"]:
		r["prev_controller"] = r["controller"]
		r["controller"] = strongest["country"]
		r["history"].append({"day": st.day, "text": "control passed to " + strongest["country"]})
		Bus.fire("region_controller_changed", region_id, r["controller"], 2)


func _at_war_or_hostile(st: CampaignState, a: String, b: String) -> bool:
	for wid in st.wars:
		var w: Dictionary = st.wars[wid]
		if a in w["sides_a"] and b in w["sides_b"]:
			return true
		if b in w["sides_a"] and a in w["sides_b"]:
			return true
	return st.rel(a, b)["threat"] > 0.55
