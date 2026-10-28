extends RefCounted
const CampaignState = preload("res://core/campaign_state.gd")
const Bus = preload("res://core/bus.gd")
## Regional administration operates on the same authoritative state as taxes,
## supply and control. Investment prices and victory thresholds are data-driven.

var rules: Dictionary = {}


func init(_state) -> void:
	var file := FileAccess.open("res://data/regional_rules.json", FileAccess.READ)
	if file != null:
		var parsed = JSON.parse_string(file.get_as_text())
		if typeof(parsed) == TYPE_DICTIONARY:
			rules = parsed
		file.close()


static func capture(st: CampaignState, rid: String, new_controller: String) -> bool:
	if not st.regions.has(rid) or not st.countries.has(new_controller):
		return false
	var r: Dictionary = st.regions[rid]
	if r["controller"] == new_controller:
		return false
	var previous: String = r["controller"]
	r["prev_controller"] = previous
	r["controller"] = new_controller
	r["stability"] = clampf(float(r["stability"]) * 0.65, 0.05, 0.55)
	r["political_support"] = clampf(float(r["support_player"]) if new_controller == st.player_id() else 0.35, 0.05, 0.75)
	r["legitimacy"] = minf(float(r["legitimacy"]), 0.38)
	r["productivity"] = maxf(0.1, float(r["productivity"]) - 0.15)
	r["security_pressure"] = maxf(0.5, float(r["security_pressure"]))
	r["opposition"] = maxf(0.5, float(r["opposition"]))
	r["supply_accessibility"] = 0.0
	r["recovery_progress"] = 0.0
	r["admin_focus"] = "none"
	var message := "%s took control from %s; administration and supply must recover." % [
		st.countries[new_controller]["name"], st.countries[previous]["name"]]
	r["history"].append({"day": st.day, "text": message})
	if r["history"].size() > 30:
		r["history"].pop_front()
	st.add_report("territory", "Control changed: " + r["name"], message)
	Bus.fire("region_controller_changed", rid, new_controller, 2)
	return true


func invest(st: CampaignState, cid: String, rid: String, kind: String) -> Dictionary:
	if not st.countries.has(cid) or not st.regions.has(rid):
		return {"ok": false, "error": "unknown faction or region"}
	var r: Dictionary = st.regions[rid]
	if r["controller"] != cid:
		return {"ok": false, "error": "region is not controlled by this faction"}
	var options: Dictionary = rules.get("investments", {})
	if not options.has(kind):
		return {"ok": false, "error": "unknown administration action"}
	var config: Dictionary = options[kind]
	var cost := float(config["cost"])
	if st.balance(cid) < cost:
		return {"ok": false, "error": "insufficient funds"}
	st.adjust_balance(cid, -cost)
	r["admin_focus"] = kind
	match kind:
		"security":
			r["security_pressure"] = maxf(0.0, float(r["security_pressure"]) - float(config["pressure_reduction"]))
			r["opposition"] = maxf(0.0, float(r["opposition"]) - float(config["opposition_reduction"]))
		"infrastructure":
			r["infra_condition"] = minf(1.0, float(r["infra_condition"]) + float(config["repair"]))
			r["recovery_progress"] = minf(1.0, float(r["recovery_progress"]) + 0.12)
		"economy":
			r["productivity"] = minf(1.0, float(r["productivity"]) + float(config["productivity"]))
			r["political_support"] = minf(1.0, float(r["political_support"]) + float(config["support"]))
			r["legitimacy"] = minf(1.0, float(r["legitimacy"]) + float(config.get("legitimacy", 0.02)))
			if cid == st.player_id():
				r["support_player"] = r["political_support"]
	var msg := "%s allocated to %s for %.0f credits; ongoing focus costs %.0f/week." % [
		kind.capitalize(), r["name"], cost, float(rules.get("focus_upkeep_per_week", 4.0))]
	st.add_report("administration", "Investment in " + r["name"], msg, cid)
	return {"ok": true, "cost": cost}


func tick_week(st: CampaignState) -> void:
	var bills := {}
	for rid in st.regions:
		var r: Dictionary = st.regions[rid]
		var cid: String = r["controller"]
		var occupied: bool = r["country"] != cid
		var cost := float(rules.get("occupation_cost_per_week", 5.0)) if occupied else 0.0
		if r["admin_focus"] != "none":
			cost += float(rules.get("focus_upkeep_per_week", 4.0))
		bills[cid] = float(bills.get(cid, 0.0)) + cost
		var pressure: float = float(r["security_pressure"])
		var opposition: float = float(r["opposition"])
		var support: float = float(r["political_support"])
		var focus: String = r["admin_focus"]
		if focus == "security":
			pressure -= 0.015
			opposition -= 0.008
		else:
			pressure += opposition * 0.006 - 0.003
		if focus == "economy":
			r["productivity"] = minf(1.0, float(r["productivity"]) + 0.012)
		if focus == "infrastructure":
			r["infra_condition"] = minf(1.0, float(r["infra_condition"]) + 0.008)
		var accessible: float = float(r["supply_accessibility"])
		var drift := (support - opposition - pressure * 0.25) * 0.025 + (0.006 if accessible > 0.5 else -0.004)
		r["security_pressure"] = clampf(pressure, 0.0, 1.0)
		r["opposition"] = clampf(opposition - (support - 0.4) * 0.006, 0.0, 1.0)
		r["stability"] = clampf(float(r["stability"]) + drift, 0.05, 1.0)
		r["political_support"] = clampf(support + (float(r["stability"]) - 0.45) * 0.009, 0.0, 1.0)
		r["legitimacy"] = clampf(float(r["legitimacy"]) + (support - opposition) * 0.008, 0.0, 1.0)
		r["recovery_progress"] = clampf(float(r["recovery_progress"]) + maxf(0.0, drift) * 0.25, 0.0, 1.0)
		if cid == st.player_id():
			r["support_player"] = r["political_support"]
	for cid in bills:
		var due: float = bills[cid]
		st.adjust_balance(cid, -due)
		if due > 0.0 and st.balance(cid) < 0.0:
			for r in st.regions.values():
				if r["controller"] == cid and r["country"] != cid:
					r["stability"] = maxf(0.05, float(r["stability"]) - 0.015)
	for f in st.formations.values():
		var r: Dictionary = st.regions[f["region"]]
		if r["controller"] == f["country"] and float(f["supplies"]) >= 0.35:
			var wounded := int(f.get("wounded", 0))
			if wounded > 0:
				var store := st.inventory_for(f["country"])
				var has_medical := int(store.get("med_kit", 0)) > 0
				if has_medical:
					store["med_kit"] = int(store["med_kit"]) - 1
				var rate := 0.25 if has_medical else 0.10
				var recovered := mini(wounded, maxi(1, int(ceil(wounded * rate))))
				f["wounded"] = wounded - recovered
				f["personnel_reserve"] = int(f.get("personnel_reserve", 0)) + recovered
			f["readiness"] = minf(1.0, float(f["readiness"]) + 0.015)
			f["morale"] = minf(1.0, float(f["morale"]) + 0.01)


func political_position(st: CampaignState) -> Dictionary:
	var claimed := 0
	var controlled := 0
	var support := 0.0
	var stability := 0.0
	var legitimacy := 0.0
	for r in st.regions.values():
		if r["country"] != "cty_vardena":
			continue
		claimed += 1
		if r["controller"] == st.player_id():
			controlled += 1
			support += float(r["political_support"])
			stability += float(r["stability"])
			legitimacy += float(r["legitimacy"])
	return {"claimed": claimed, "controlled": controlled,
		"share": float(controlled) / maxf(1.0, float(claimed)),
		"support": support / maxf(1.0, float(controlled)),
		"stability": stability / maxf(1.0, float(controlled)),
		"legitimacy": legitimacy / maxf(1.0, float(controlled))}


func evaluate_outcome(st: CampaignState) -> String:
	if st.outcome != "":
		return st.outcome
	var armed_squads := 0
	for f in st.formations_of(st.player_id()):
		for unit in f["units"]:
			armed_squads += int(unit["count"])
	var controlled := 0
	for r in st.regions.values():
		if r["controller"] == st.player_id():
			controlled += 1
	if armed_squads == 0 and controlled == 0:
		st.outcome = "defeat"
		st.add_report("campaign", "Movement defeated", "No territory or equipped squads remain to continue the struggle.")
		Bus.fire("campaign_ended", st.outcome, null, 1)
		return st.outcome
	var pos := political_position(st)
	var capital: String = st.countries["cty_vardena"]["capital"]
	if st.regions[capital]["controller"] == st.player_id() \
			and float(pos["share"]) >= float(rules.get("military_transition_share", 0.6)) \
			and float(pos["support"]) >= float(rules.get("transition_support", 0.42)) \
			and float(pos["stability"]) >= float(rules.get("transition_stability", 0.4)) \
			and float(pos["legitimacy"]) >= float(rules.get("transition_legitimacy", 0.38)):
		st.outcome = "military_transition"
		st.add_report("campaign", "Government replaced", "The capital and a supported majority of Vardena are under your administration.")
		Bus.fire("campaign_ended", st.outcome, null, 1)
	return st.outcome
