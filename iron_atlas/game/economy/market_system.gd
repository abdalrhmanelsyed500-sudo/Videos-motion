extends RefCounted
const Bus = preload("res://core/bus.gd")
const CampaignState = preload("res://core/campaign_state.gd")
## Arms market: catalogue from data/equipment.json, availability rules,
## orders with persistent status + delivery ETA, diplomatic consequences.

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


func availability(st: CampaignState, id: String) -> Dictionary:
	var it := item(id)
	if it.is_empty():
		return {"ok": false, "reason": "unknown item"}
	var tier := int(it.get("tier", 1))
	var pid := st.player_id()
	var supplier: String = it.get("supplier", "local")
	if tier >= 3:
		var rel_warmth: float = st.rel(pid, supplier)["warmth"] if st.countries.has(supplier) else 0.5
		if rel_warmth < 0.45 and it.get("export_restricted", false):
			return {"ok": false, "reason": "supplier restricts exports (relations too cold)"}
	if it.get("black_market", false):
		if st.stability > 0.75:
			return {"ok": false, "reason": "enforcement pressure too high right now"}
	return {"ok": true, "reason": ""}


func quote(st: CampaignState, id: String, qty: int) -> Dictionary:
	var it := item(id)
	if it.is_empty() or qty <= 0:
		return {"ok": false, "error": "bad quote request"}
	var avail := availability(st, id)
	if not avail["ok"]:
		return {"ok": false, "error": avail["reason"]}
	var price := float(it["price"]) * qty
	var fluct := 0.9 + st.randf() * 0.2
	price = roundf(price * fluct)
	var upkeep := float(it.get("upkeep", 0.5)) * qty
	var eta := int(it.get("delivery_days", 5))
	var diplo := _diplomatic_preview(st, it)
	return {"ok": true, "price": price, "upkeep_per_week": upkeep, "eta_days": eta,
		"diplomatic": diplo}


func _diplomatic_preview(st: CampaignState, it: Dictionary) -> Array:
	var out: Array = []
	var supplier: String = it.get("supplier", "local")
	if not st.countries.has(supplier):
		return out
	out.append("+%s warmth with %s" % ["small" if int(it["tier"]) < 3 else "notable",
		st.countries[supplier]["name"]])
	if int(it.get("sensitivity", 0)) >= 2:
		for cid in st.countries:
			if cid != st.player_id() and cid != supplier:
				if st.rel(cid, supplier)["threat"] > 0.5:
					out.append("suspicion from " + st.countries[cid]["name"])
	return out


func purchase(st: CampaignState, id: String, qty: int) -> Dictionary:
	var q := quote(st, id, qty)
	if not q["ok"]:
		return q
	if st.treasury < float(q["price"]):
		return {"ok": false, "error": "insufficient funds"}
	st.treasury -= float(q["price"])
	var oid := st.next_id("ord")
	st.market_orders[oid] = {"id": oid, "item": id, "qty": qty, "status": "in_transit",
		"eta_day": st.day + int(q["eta_days"]), "price": q["price"],
		"placed_day": st.day, "supplier": item(id).get("supplier", "local")}
	Bus.fire("order_status_changed", oid, "in_transit", 2)
	st.add_report("market", "Order placed: %s x%d" % [item(id)["name"], qty],
		"%.0f credits, ETA %d days. %s" % [q["price"], q["eta_days"],
		" ".join(q["diplomatic"])])
	return {"ok": true, "order": st.market_orders[oid]}


func tick_day(st: CampaignState) -> void:
	for oid in st.market_orders.keys():
		var o: Dictionary = st.market_orders[oid]
		if o["status"] != "in_transit":
			continue
		if st.randf() < 0.004:  # rare interdiction/loss event
			o["status"] = "lost_in_transit"
			Bus.fire("order_status_changed", oid, o["status"], 2)
			st.add_report("market", "Shipment lost", "Order %s never arrived." % oid)
			continue
		if st.day >= int(o["eta_day"]):
			o["status"] = "delivered"
			st.inventory[o["item"]] = int(st.inventory.get(o["item"], 0)) + int(o["qty"])
			Bus.fire("order_status_changed", oid, "delivered", 2)
			st.add_report("market", "Delivery: %s x%d" % [item(o["item"]).get("name", o["item"]),
				o["qty"]], "Added to inventory. Assign it to formations from the Military panel.")
			_diplomatic_effect(st, o)


func _diplomatic_effect(st: CampaignState, o: Dictionary) -> void:
	var it := item(o["item"])
	var supplier: String = it.get("supplier", "local")
	if not st.countries.has(supplier):
		return
	var r := st.rel(st.player_id(), supplier)
	r["warmth"] = clampf(float(r["warmth"]) + (0.03 if int(it["tier"]) < 3 else 0.06), 0, 1)
	r["trust"] = clampf(float(r["trust"]) + 0.02, 0, 1)
	Bus.fire("relations_changed", st.pair_key(st.player_id(), supplier), null, 1)
	if int(it.get("sensitivity", 0)) >= 2:
		for cid in st.countries:
			if cid != st.player_id() and cid != supplier and st.rel(cid, supplier)["threat"] > 0.5:
				var r2 := st.rel(st.player_id(), cid)
				r2["threat"] = clampf(float(r2["threat"]) + 0.05, 0, 1)
				Bus.fire("relations_changed", st.pair_key(st.player_id(), cid), null, 1)


func equip_from_inventory(st: CampaignState, formation_id: String, equip_id: String, count: int) -> Dictionary:
	var f: Dictionary = st.formations.get(formation_id, {})
	if f.is_empty():
		return {"ok": false, "error": "unknown formation"}
	var have: int = int(st.inventory.get(equip_id, 0))
	if have < count:
		return {"ok": false, "error": "only %d in inventory" % have}
	var it := item(equip_id)
	st.inventory[equip_id] = have - count
	var cls: String = it.get("unit_class", "infantry")
	var found := false
	for u in f["units"]:
		if u["equip"] == equip_id:
			u["count"] += count
			found = true
			break
	if not found:
		f["units"].append({"class": cls, "equip": equip_id, "count": count, "condition": 1.0})
	st.add_report("military", "Equipment issued", "%s x%d to %s." % [it.get("name", equip_id),
		count, f["name"]])
	return {"ok": true}
