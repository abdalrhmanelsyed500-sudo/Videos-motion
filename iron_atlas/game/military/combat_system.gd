extends RefCounted
const Bus = preload("res://core/bus.gd")
const CampaignState = preload("res://core/campaign_state.gd")
const CommandSystem = preload("res://military/command_system.gd")
const WorldGenerator = preload("res://world/world_generator.gd")
## Combat mutates authoritative formations exactly once; reports persist IDs,
## casualties, wounded and equipment salvage. Both strategic and tactical
## outcomes use the same consequence and post-battle path.


func init(_state) -> void:
	pass


func hostile_pairs(st: CampaignState, region_id: String) -> Array:
	var present := st.formations_in(region_id)
	var pairs: Array = []
	for i in present.size():
		for j in range(i + 1, present.size()):
			var a: Dictionary = present[i]
			var b: Dictionary = present[j]
			if _strength(a) > 0 and _strength(b) > 0 and st.is_hostile(a["country"], b["country"]):
				pairs.append([a, b])
	return pairs


func _hostile(st: CampaignState, a: String, b: String) -> bool:
	return st.is_hostile(a, b)


func power_of(st: CampaignState, f: Dictionary, equip_table: Dictionary) -> float:
	var base := st.formation_power(f, equip_table)
	var terrain: String = st.regions[f["region"]]["terrain"]
	base *= float(WorldGenerator.TERRAIN_MOD[terrain]["def"])
	base *= 0.75 + 0.25 * float(f["cohesion"])
	base *= 1.0 + 0.1 * float(f["experience"])
	base *= 0.25 + 0.75 * float(f.get("ammo_reserve", 0.8))
	base *= 1.0 + minf(0.15, 0.05 * int(f.get("attachments", {}).get("com_secure", 0)))
	return base


func resolve_engagement(st: CampaignState, a: Dictionary, b: Dictionary, equip_table: Dictionary,
		intensity: float = 1.0) -> Dictionary:
	if a.is_empty() or b.is_empty() or not st.formations.has(a.get("id", "")) \
			or not st.formations.has(b.get("id", "")) or a["region"] != b["region"] \
			or not st.is_hostile(a["country"], b["country"]):
		return {"report": {}, "error": "invalid engagement"}
	var pa := power_of(st, a, equip_table) * (0.85 + st.randf() * 0.3)
	var pb := power_of(st, b, equip_table) * (0.85 + st.randf() * 0.3)
	var total := pa + pb
	if total <= 0.001:
		return {"report": {}}
	var share_a := pa / total
	var loss_scale := clampf(0.22 * intensity, 0.0, 1.0)
	var losses_b := _apply_losses(st, b, loss_scale * share_a)
	var losses_a := _apply_losses(st, a, loss_scale * (1.0 - share_a))
	for f in [a, b]:
		f["ammo_reserve"] = maxf(0.0, float(f.get("ammo_reserve", 0.8)) - 0.12 * intensity)
		f["cohesion"] = maxf(0.1, float(f["cohesion"]) - 0.05 * intensity)
		f["experience"] = mini(5, int(f["experience"]) + 1)
	a["morale"] = maxf(0.05, float(a["morale"]) - 0.12 * intensity * (1.0 - share_a))
	b["morale"] = maxf(0.05, float(b["morale"]) - 0.12 * intensity * share_a)
	var routed_ids: Array = []
	for f in [a, b]:
		if float(f["morale"]) < 0.22 or _strength(f) <= 0:
			routed_ids.append(f["id"])
	var rep := {"id": st.next_id("bat"), "day": st.day, "region": a["region"],
		"attackers": [a["name"], b["name"]], "combatants": [a["id"], b["id"]],
		"losses": {a["id"]: losses_a, b["id"]: losses_b}, "routed": routed_ids,
		"power_ratio": roundf(pa / maxf(0.001, pb) * 100) / 100.0}
	return {"report": rep, "routed": routed_ids}


func _strength(f: Dictionary) -> int:
	var n := 0
	for u in f["units"]:
		n += int(u["count"])
	return n


func _apply_losses(st: CampaignState, f: Dictionary, frac: float) -> Dictionary:
	var lost_units := 0
	var wounded := 0
	var killed := 0
	var damaged := 0
	var r: Dictionary = st.regions[f["region"]]
	var protected: int = int(f.get("attachments", {}).get("kit_protect", 0))
	var protection := minf(0.30, 0.05 * protected)
	for u in f["units"]:
		var c := int(u["count"])
		var expected := c * clampf(frac * (1.0 - protection), 0.0, 1.0)
		var lost := int(floor(expected))
		if lost < c and st.randf() < expected - lost:
			lost += 1
		lost = mini(c, lost)
		if lost > 0:
			u["count"] = c - lost
			lost_units += lost
			var casualties := lost * CampaignState.PERSONNEL_PER_UNIT
			var w := int(roundf(casualties * 0.4))
			wounded += w
			killed += casualties - w
			var equip: String = u["equip"]
			r["salvage"][equip] = int(r["salvage"].get(equip, 0)) + lost
		if c > 0 and frac > 0.0:
			u["condition"] = maxf(0.1, float(u["condition"]) - minf(0.25, frac * 0.4 + 0.03))
			damaged += int(u["count"])
	if lost_units > 0:
		var attachments: Dictionary = f.get("attachments", {})
		for equip in attachments:
			var destroyed := mini(int(attachments[equip]), lost_units)
			attachments[equip] = int(attachments[equip]) - destroyed
			r["salvage"][equip] = int(r["salvage"].get(equip, 0)) + destroyed
	f["wounded"] = int(f.get("wounded", 0)) + wounded
	f["dead"] = int(f.get("dead", 0)) + killed
	f["supplies"] = maxf(0.0, float(f["supplies"]) - frac * 0.5)
	f["readiness"] = maxf(0.1, float(f["readiness"]) - frac * 0.2)
	return {"units_lost": lost_units, "wounded": wounded, "killed": killed, "equipment_damaged": damaged}


func apply_tactical_outcome(st: CampaignState, rid: String, tactical_units: Array,
		player_won: bool, equip_table: Dictionary) -> Dictionary:
	var groups := {}
	for u in tactical_units:
		var fid: String = u["formation"]
		if not st.formations.has(fid):
			continue
		if not groups.has(fid):
			groups[fid] = {"initial": 0.0, "remaining": 0.0, "side": int(u["side"])}
		groups[fid]["initial"] = float(groups[fid]["initial"]) + float(u.get("max_hp", u["count"]))
		groups[fid]["remaining"] = float(groups[fid]["remaining"]) + maxf(0.0, float(u["hp"]))
	var losses := {}
	var routed: Array = []
	var names: Array = []
	for fid in groups:
		var f: Dictionary = st.formations[fid]
		var initial: float = float(groups[fid]["initial"])
		var ratio := clampf(1.0 - float(groups[fid]["remaining"]) / maxf(0.001, initial), 0.0, 1.0)
		losses[fid] = _apply_losses(st, f, ratio)
		names.append(f["name"])
		var lost_side := (int(groups[fid]["side"]) == 1 and player_won) or (int(groups[fid]["side"]) == 0 and not player_won)
		if lost_side:
			routed.append(fid)
			f["morale"] = maxf(0.05, float(f["morale"]) - 0.2)
		else:
			f["morale"] = minf(1.0, float(f["morale"]) + 0.05)
	var rep := {"id": st.next_id("bat"), "day": st.day, "region": rid, "attackers": names,
		"combatants": groups.keys(), "losses": losses, "routed": routed, "power_ratio": 1.0,
		"tactical": true, "player_won": player_won}
	post_battle(st, rep, equip_table)
	return rep


func post_battle(st: CampaignState, rep: Dictionary, _equip_table: Dictionary) -> void:
	if rep == null or rep.is_empty():
		return
	var bid: String = rep.get("id", "")
	if bid == "" or st.finalized_battles.has(bid):
		return
	var player_involved := false
	for fid in rep.get("combatants", []):
		if st.formations.has(fid) and st.formations[fid]["country"] == st.player_id():
			player_involved = true
	st.finalized_battles[bid] = true
	for fid in rep["routed"]:
		var f: Dictionary = st.formations.get(fid, {})
		if f.is_empty():
			continue
		if st.formation_personnel(f) <= 0 and int(f.get("wounded", 0)) <= 0:
			st.formations.erase(fid)
			Bus.fire("formation_defeated", fid, null, 1)
		else:
			var retreat := CommandSystem.new().issue_retreat(st, fid)
			if not retreat["ok"]:
				f["orders"] = []
				st.add_report("battle", f["name"] + " encircled", "No safe adjacent region was available for retreat.", f["country"])
	var r: Dictionary = st.regions.get(rep["region"], {})
	if not r.is_empty():
		r["stability"] = maxf(0.05, float(r["stability"]) - 0.04)
		r["infra_condition"] = maxf(0.1, float(r["infra_condition"]) - 0.025)
		r["security_pressure"] = minf(1.0, float(r["security_pressure"]) + 0.04)
		CommandSystem.new()._check_control(st, rep["region"])
	var details: Array = []
	for fid in rep["losses"]:
		var loss: Dictionary = rep["losses"][fid]
		details.append("%s: %d squads lost, %d killed, %d wounded, %d damaged" % [
			fid, loss["units_lost"], loss["killed"], loss["wounded"], loss["equipment_damaged"]])
	var body := "Engagement at %s. %s. Routed: %s. Battlefield salvage requires recovery and repair." % [
		r.get("name", rep["region"]), "; ".join(details), ", ".join(rep["routed"]) if rep["routed"].size() else "none"]
	var audience := "public" if player_involved or st.can_observe(st.player_id(), rep["region"]) else "hidden"
	st.add_report("battle", "Battle of " + r.get("name", rep["region"]), body, audience)
	st.add_history(body)
	Bus.fire("battle_finished", rep, null, 1)
