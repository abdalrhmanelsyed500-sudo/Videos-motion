extends RefCounted
const Bus = preload("res://core/bus.gd")
const CampaignState = preload("res://core/campaign_state.gd")
## One market for every faction: quote, charge once, delayed delivery, then
## inventory, supplier relations, equipment issue and repairs.

const CATALOG_PATH := "res://data/equipment.json"
var catalog: Dictionary = {}


func init(_state) -> void:
	reload_catalog()


func reload_catalog() -> void:
	var f := FileAccess.open(CATALOG_PATH, FileAccess.READ)
	if f == null:
		push_warning("equipment catalogue missing")
		return
	var parsed = JSON.parse_string(f.get_as_text())
	f.close()
	if typeof(parsed) == TYPE_DICTIONARY:
		catalog = parsed.get("items", {})


func item(id: String) -> Dictionary:
	return catalog.get(id, {})


func availability(st: CampaignState, id: String, cid: String = "") -> Dictionary:
	if cid == "":
		cid = st.player_id()
	var it := item(id)
	if it.is_empty() or not st.countries.has(cid):
		return {"ok": false, "reason": "unknown item or buyer"}
	var supplier: String = it.get("supplier", "local")
	if st.countries.has(supplier) and supplier != cid:
		if st.is_hostile(cid, supplier):
			return {"ok": false, "reason": "supplier is hostile to the buyer"}
		if bool(it.get("export_restricted", false)):
			var warmth: float = float(st.rel(cid, supplier)["warmth"])
			var minimum := 0.45 if int(it.get("tier", 1)) >= 3 else 0.25
			if warmth < minimum:
				return {"ok": false, "reason": "supplier restricts exports (relations too cold)"}
	if bool(it.get("black_market", false)):
		var national_stability := st.stability if cid == st.player_id() else 0.0
		if cid != st.player_id():
			var count := 0
			for region in st.regions.values():
				if region["controller"] == cid:
					national_stability += float(region["stability"])
					count += 1
			national_stability /= maxf(1.0, float(count))
		if national_stability > 0.75:
			return {"ok": false, "reason": "enforcement pressure too high"}
	return {"ok": true, "reason": ""}


func quote(st: CampaignState, id: String, qty: int, cid: String = "") -> Dictionary:
	if cid == "":
		cid = st.player_id()
	var it := item(id)
	if it.is_empty() or qty <= 0 or qty > 1000:
		return {"ok": false, "error": "invalid item or quantity"}
	var avail := availability(st, id, cid)
	if not avail["ok"]:
		return {"ok": false, "error": avail["reason"]}
	var modifier := 1.0
	var supplier: String = it.get("supplier", "local")
	if st.countries.has(supplier) and supplier != cid:
		modifier = clampf(1.15 - float(st.rel(cid, supplier)["warmth"]) * 0.3, 0.85, 1.15)
	var price := roundf(float(it["price"]) * qty * modifier * (1.0 + st.inflation))
	return {"ok": true, "price": price, "upkeep_per_week": float(it.get("upkeep", 0.0)) * qty,
		"eta_days": maxi(1, int(it.get("delivery_days", 5))),
		"diplomatic": _diplomatic_preview(st, it, cid)}


func _diplomatic_preview(st: CampaignState, it: Dictionary, cid: String) -> Array:
	var out: Array = []
	var supplier: String = it.get("supplier", "local")
	if st.countries.has(supplier) and supplier != cid:
		out.append("Supplier warmth and trust increase on delivery: " + st.countries[supplier]["name"])
		if int(it.get("sensitivity", 0)) >= 2:
			out.append("Sensitive order may increase rivals' threat perception")
	return out


func purchase(st: CampaignState, id: String, qty: int) -> Dictionary:
	return purchase_for(st, st.player_id(), id, qty)


func purchase_for(st: CampaignState, cid: String, id: String, qty: int) -> Dictionary:
	var q := quote(st, id, qty, cid)
	if not q["ok"]:
		return q
	if st.balance(cid) < float(q["price"]):
		return {"ok": false, "error": "insufficient funds"}
	st.adjust_balance(cid, -float(q["price"]))
	var oid := st.next_id("ord")
	st.market_orders[oid] = {"id": oid, "owner": cid, "item": id, "qty": qty,
		"status": "in_transit", "eta_day": st.day + int(q["eta_days"]),
		"price": q["price"], "placed_day": st.day, "supplier": item(id).get("supplier", "local")}
	Bus.fire("order_status_changed", oid, "in_transit", 2)
	st.add_report("market", "Order placed: %s x%d" % [item(id)["name"], qty],
		"%s paid %.0f credits; ETA %d days. %s" % [st.countries[cid]["name"],
		q["price"], q["eta_days"], " ".join(q["diplomatic"])], cid)
	return {"ok": true, "order": st.market_orders[oid], "quote": q}


func _secure_region(st: CampaignState, cid: String, rid: String) -> bool:
	if not st.regions.has(rid) or st.regions[rid]["controller"] != cid:
		return false
	for f in st.formations_in(rid):
		if st.is_hostile(cid, f["country"]) and st.formation_power(f, {}) > 0.0:
			return false
	return true


func tick_day(st: CampaignState) -> void:
	for oid in st.market_orders.keys():
		var o: Dictionary = st.market_orders[oid]
		if o["status"] not in ["in_transit", "delayed"] or st.day < int(o["eta_day"]):
			continue
		var cid: String = o.get("owner", st.player_id())
		if not st.countries.has(cid):
			continue
		var cap: String = st.countries[cid]["capital"]
		if not _secure_region(st, cid, cap):
			if o["status"] != "delayed":
				o["status"] = "delayed"
				st.add_report("market", "Shipment delayed", "Order %s awaits a secure, controlled capital/depot." % oid, cid)
				Bus.fire("order_status_changed", oid, "delayed", 2)
			continue
		# Status is set before side effects; replaying the next tick cannot redeliver.
		o["status"] = "delivered"
		var store := st.inventory_for(cid)
		store[o["item"]] = int(store.get(o["item"], 0)) + int(o["qty"])
		Bus.fire("order_status_changed", oid, "delivered", 2)
		st.add_report("market", "Delivery: %s x%d" % [item(o["item"]).get("name", o["item"]), o["qty"]],
			"Delivered to %s inventory; maintenance now applies." % st.countries[cid]["name"], cid)
		_diplomatic_effect(st, o, cid)


func _diplomatic_effect(st: CampaignState, o: Dictionary, cid: String) -> void:
	var it := item(o["item"])
	var supplier: String = it.get("supplier", "local")
	if not st.countries.has(supplier) or supplier == cid:
		return
	var r := st.rel(cid, supplier)
	r["warmth"] = clampf(float(r["warmth"]) + (0.03 if int(it["tier"]) < 3 else 0.06), 0.0, 1.0)
	r["trust"] = clampf(float(r["trust"]) + 0.02, 0.0, 1.0)
	Bus.fire("relations_changed", st.pair_key(cid, supplier), null, 1)
	if int(it.get("sensitivity", 0)) >= 2:
		for other in st.countries:
			if other != cid and other != supplier and float(st.rel(other, supplier)["threat"]) > 0.5:
				var r2 := st.rel(cid, other)
				r2["threat"] = minf(1.0, float(r2["threat"]) + 0.05)


func equip_from_inventory(st: CampaignState, formation_id: String, equip_id: String,
		count: int, cid: String = "") -> Dictionary:
	if cid == "":
		cid = st.player_id()
	var f: Dictionary = st.formations.get(formation_id, {})
	var it := item(equip_id)
	if f.is_empty() or f["country"] != cid:
		return {"ok": false, "error": "formation not controlled by buyer"}
	if it.is_empty() or count <= 0:
		return {"ok": false, "error": "invalid equipment or quantity"}
	if it.get("category", "") == "medical":
		return {"ok": false, "error": "medical kits are consumed automatically during recovery"}
	if not _secure_region(st, cid, f["region"]):
		return {"ok": false, "error": "formation must be in secure controlled territory"}
	var store := st.inventory_for(cid)
	var have := int(store.get(equip_id, 0))
	if have < count:
		return {"ok": false, "error": "only %d equipment packages in inventory" % have}
	if it.get("category", "") == "gear":
		var squads := 0
		for u in f["units"]:
			squads += int(u["count"])
		var assigned := 0
		for amount in f.get("attachments", {}).values():
			assigned += int(amount)
		if assigned + count > squads:
			return {"ok": false, "error": "gear requires an unassigned equipped squad"}
		var attachments: Dictionary = f.get("attachments", {})
		attachments[equip_id] = int(attachments.get(equip_id, 0)) + count
		f["attachments"] = attachments
		store[equip_id] = have - count
		st.add_report("military", "Support gear issued", "%s x%d assigned to %s." % [it["name"], count, f["name"]], cid)
		return {"ok": true, "attachments": count}
	var cls: String = it.get("unit_class", "infantry")
	var replacements := 0
	for u in f["units"]:
		if u["class"] == cls and u["equip"] != equip_id:
			replacements += int(u["count"])
	var reserve := int(f.get("personnel_reserve", 0))
	var capacity := replacements + int(reserve / CampaignState.PERSONNEL_PER_UNIT)
	if capacity < count:
		return {"ok": false, "error": "need %d more trained people or compatible squads" % ((count - capacity) * CampaignState.PERSONNEL_PER_UNIT)}
	# Replace compatible squads first, preserving worn packages as damaged stock.
	var remaining := count
	for u in f["units"]:
		if remaining <= 0:
			break
		if u["class"] != cls or u["equip"] == equip_id:
			continue
		var take := mini(remaining, int(u["count"]))
		u["count"] = int(u["count"]) - take
		if float(u.get("condition", 1.0)) < 0.98:
			var damaged: Dictionary = st.countries[cid].get("damaged_inventory", {})
			damaged[u["equip"]] = int(damaged.get(u["equip"], 0)) + take
			st.countries[cid]["damaged_inventory"] = damaged
		else:
			store[u["equip"]] = int(store.get(u["equip"], 0)) + take
		remaining -= take
	var new_squads := remaining
	f["personnel_reserve"] = reserve - new_squads * CampaignState.PERSONNEL_PER_UNIT
	store[equip_id] = have - count
	var found := false
	for u in f["units"]:
		if u["equip"] == equip_id and u["class"] == cls:
			var existing := int(u["count"])
			u["condition"] = (float(u["condition"]) * existing + float(count)) / float(existing + count)
			u["count"] = existing + count
			found = true
			break
	if not found:
		f["units"].append({"class": cls, "equip": equip_id, "count": count, "condition": 1.0})
	st.add_report("military", "Equipment issued", "%s x%d to %s: %d new squads, %d replacements." % [
		it["name"], count, f["name"], new_squads, count - new_squads], cid)
	return {"ok": true, "created_squads": new_squads, "replaced_squads": count - new_squads}


func repair_formation(st: CampaignState, formation_id: String, cid: String = "") -> Dictionary:
	if cid == "":
		cid = st.player_id()
	var f: Dictionary = st.formations.get(formation_id, {})
	if f.is_empty() or f["country"] != cid:
		return {"ok": false, "error": "unknown formation"}
	var r: Dictionary = st.regions[f["region"]]
	if not _secure_region(st, cid, f["region"]):
		return {"ok": false, "error": "repair requires secure controlled territory"}
	var damaged := 0
	for u in f["units"]:
		if int(u["count"]) > 0 and float(u["condition"]) < 0.99:
			damaged += int(u["count"])
	if damaged == 0:
		return {"ok": false, "error": "no damaged equipment"}
	var cost := float(damaged) * 35.0
	var parts := float(damaged) * 1.0
	if st.balance(cid) < cost or float(r["stocks"]["parts"]) < parts:
		return {"ok": false, "error": "insufficient funds or regional spare parts"}
	st.adjust_balance(cid, -cost)
	r["stocks"]["parts"] = float(r["stocks"]["parts"]) - parts
	for u in f["units"]:
		u["condition"] = minf(1.0, float(u["condition"]) + 0.25)
	st.add_report("logistics", "Formation repaired", "%s: %.0f credits, %.0f parts." % [f["name"], cost, parts], cid)
	return {"ok": true, "cost": cost, "parts": parts}


func recover_salvage(st: CampaignState, cid: String, rid: String) -> Dictionary:
	var r: Dictionary = st.regions.get(rid, {})
	if r.is_empty() or not st.countries.has(cid) or not _secure_region(st, cid, rid):
		return {"ok": false, "error": "secure the region to recover equipment"}
	var damaged: Dictionary = st.countries[cid].get("damaged_inventory", {})
	var recovered := 0
	for id in r["salvage"]:
		if not item(id).is_empty():
			var amount := int(r["salvage"][id])
			damaged[id] = int(damaged.get(id, 0)) + amount
			recovered += amount
	if recovered == 0:
		return {"ok": false, "error": "no recoverable equipment"}
	r["salvage"] = {}
	st.countries[cid]["damaged_inventory"] = damaged
	st.add_report("logistics", "Battlefield equipment recovered", "%d damaged packages require repair." % recovered, cid)
	return {"ok": true, "recovered": recovered}


func repair_recovered(st: CampaignState, cid: String, rid: String, id: String, count: int) -> Dictionary:
	var r: Dictionary = st.regions.get(rid, {})
	if r.is_empty() or not st.countries.has(cid) or count <= 0 or not _secure_region(st, cid, rid):
		return {"ok": false, "error": "repair requires a secure controlled region"}
	var it := item(id)
	var damaged: Dictionary = st.countries[cid].get("damaged_inventory", {})
	if it.is_empty() or int(damaged.get(id, 0)) < count:
		return {"ok": false, "error": "insufficient damaged equipment"}
	var cost := maxf(25.0, float(it["price"]) * 0.12) * count
	var parts := float(count) * 2.0
	if st.balance(cid) < cost or float(r["stocks"]["parts"]) < parts:
		return {"ok": false, "error": "insufficient funds or spare parts"}
	st.adjust_balance(cid, -cost)
	r["stocks"]["parts"] = float(r["stocks"]["parts"]) - parts
	damaged[id] = int(damaged[id]) - count
	var store := st.inventory_for(cid)
	store[id] = int(store.get(id, 0)) + count
	st.add_report("logistics", "Recovered equipment repaired", "%s x%d repaired for %.0f credits." % [it["name"], count, cost], cid)
	return {"ok": true, "cost": cost, "parts": parts}
