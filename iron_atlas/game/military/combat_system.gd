extends RefCounted
const Bus = preload("res://core/bus.gd")
const CampaignState = preload("res://core/campaign_state.gd")
const CommandSystem = preload("res://military/command_system.gd")
const WorldGenerator = preload("res://world/world_generator.gd")
## Abstract combat resolution shared by strategic engagements and tactical
## skirmishes. Factors: class power, equipment quality, training/experience,
## morale, cohesion, terrain defence, supplies, readiness, fortification.
## A weaker force can win with terrain/preparation/cohesion (no auto-loss).

const CAPTURE_CHANCE := 0.25


func init(_state) -> void:
	pass


func hostile_pairs(st: CampaignState, region_id: String) -> Array:
	var present := st.formations_in(region_id)
	var pairs: Array = []
	for i in present.size():
		for j in range(i + 1, present.size()):
			var a: Dictionary = present[i]
			var b: Dictionary = present[j]
			if a["country"] == b["country"]:
				continue
			if _hostile(st, a["country"], b["country"]):
				pairs.append([a, b])
	return pairs


func _hostile(st: CampaignState, a: String, b: String) -> bool:
	for wid in st.wars:
		var w: Dictionary = st.wars[wid]
		if (a in w["sides_a"] and b in w["sides_b"]) or (b in w["sides_a"] and a in w["sides_b"]):
			return true
	return st.rel(a, b)["threat"] > 0.55


func power_of(st: CampaignState, f: Dictionary, equip_table: Dictionary) -> float:
	var base := st.formation_power(f, equip_table)
	var terrain: String = st.regions[f["region"]]["terrain"]
	base *= WorldGenerator.TERRAIN_MOD[terrain]["def"]
	base *= 0.75 + 0.25 * float(f["cohesion"])
	base *= 1.0 + 0.1 * float(f["experience"])
	return base


func resolve_engagement(st: CampaignState, a: Dictionary, b: Dictionary, equip_table: Dictionary,
		intensity: float = 1.0) -> Dictionary:
	var pa := power_of(st, a, equip_table) * (0.85 + st.randf() * 0.3)
	var pb := power_of(st, b, equip_table) * (0.85 + st.randf() * 0.3)
	var total := pa + pb
	if total <= 0.001:
		return {"report": null}
	var share_a := pa / total          # fraction of damage inflicted ON b
	var loss_scale := 0.22 * intensity
	var losses_b := _apply_losses(st, b, loss_scale * share_a)
	var losses_a := _apply_losses(st, a, loss_scale * (1.0 - share_a))
	a["morale"] = maxf(0.05, float(a["morale"]) - 0.06 * intensity * (1.0 - share_a) * 2)
	b["morale"] = maxf(0.05, float(b["morale"]) - 0.06 * intensity * share_a * 2)
	a["cohesion"] = maxf(0.1, float(a["cohesion"]) - 0.05 * intensity)
	b["cohesion"] = maxf(0.1, float(b["cohesion"]) - 0.05 * intensity)
	a["experience"] = mini(5, int(a["experience"]) + 1)
	b["experience"] = mini(5, int(b["experience"]) + 1)
	var routed: Array = []
	for f in [a, b]:
		if float(f["morale"]) < 0.22 or _strength(f) <= 0:
			routed.append(f)
	var routed_ids: Array = []
	for rf in routed:
		routed_ids.append(rf["id"])
	var rep := {
		"day": st.day, "region": a["region"],
		"attackers": [a["name"], b["name"]],
		"losses": {a["id"]: losses_a, b["id"]: losses_b},
		"routed": routed_ids,
		"power_ratio": roundf(pa / maxf(0.001, pb) * 100) / 100.0,
	}
	return {"report": rep, "routed": routed}


func _strength(f: Dictionary) -> int:
	var n := 0
	for u in f["units"]:
		n += int(u["count"])
	return n


func _apply_losses(st: CampaignState, f: Dictionary, frac: float) -> Dictionary:
	var lost_units := 0
	var wounded := 0
	var damaged_equip := 0
	for u in f["units"]:
		var c := int(u["count"])
		var lost := int(roundf(c * clampf(frac, 0.0, 0.6)))
		if lost > 0:
			u["count"] = c - lost
			lost_units += lost
			wounded += int(lost * 12 * 0.4)
			u["condition"] = maxf(0.2, float(u["condition"]) - 0.08)
			damaged_equip += 1 if u["class"] in ["armor", "mechanized", "artillery"] else 0
	f["supplies"] = maxf(0.0, float(f["supplies"]) - 0.15)
	return {"units_lost": lost_units, "wounded": wounded, "equipment_damaged": damaged_equip}


func post_battle(st: CampaignState, rep: Dictionary, equip_table: Dictionary) -> void:
	if rep == null or rep.is_empty():
		return
	for fid in rep["routed"]:
		var f: Dictionary = st.formations.get(fid, {})
		if f.is_empty():
			continue
		var alive := _strength(f)
		if alive <= 0:
			st.formations.erase(fid)
			st.add_report("battle", f["name"] + " destroyed",
				"The formation ceased to exist after the engagement.")
			Bus.fire("formation_defeated", fid, null, 1)
		else:
			# retreat to a friendly neighbor; capturable equipment left behind
			var cs := CommandSystem.new()
			cs.issue_retreat(st, fid)
			if st.randf() < CAPTURE_CHANCE:
				var winner_country := ""
				for other in rep["attackers"]:
					pass
				st.inventory["cap_small_arms"] = int(st.inventory.get("cap_small_arms", 0)) + 5
				st.add_history("Captured equipment secured after battle")
	var r: Dictionary = st.regions.get(rep["region"], {})
	if not r.is_empty():
		r["stability"] = maxf(0.05, float(r["stability"]) - 0.08)
		r["infra"] = maxi(0, int(r["infra"]) - (1 if st.randf() < 0.35 else 0))
		var ctrl := _strongest_in(st, rep["region"])
		if ctrl != "" and ctrl != r["controller"]:
			r["prev_controller"] = r["controller"]
			r["controller"] = ctrl
			Bus.fire("region_controller_changed", rep["region"], ctrl, 2)
	var body := "Engagement at %s — power ratio %s. Routed: %s." % [
		r.get("name", rep["region"]), str(rep["power_ratio"]),
		", ".join(rep["routed"]) if rep["routed"].size() else "none"]
	st.add_report("battle", "Battle of " + r.get("name", rep["region"]), body)
	st.add_history(body)
	Bus.fire("battle_finished", rep, null, 1)


func _strongest_in(st: CampaignState, region_id: String) -> String:
	var present := st.formations_in(region_id)
	if present.is_empty():
		return ""
	var best: Dictionary = present[0]
	for f in present:
		if st.formation_power(f, {}) > st.formation_power(best, {}):
			best = f
	return best["country"]
