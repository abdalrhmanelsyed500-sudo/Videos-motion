extends RefCounted
const Bus = preload("res://core/bus.gd")
const CampaignState = preload("res://core/campaign_state.gd")
const Administration = preload("res://administration/administration_system.gd")
## War, ceasefire treaties and a limited negotiated Vardena transition.


func init(_state) -> void:
	pass


func improve_relations(st: CampaignState, other: String, cost: float) -> Dictionary:
	var pid := st.player_id()
	if not st.countries.has(other) or other == pid or cost < 0.0:
		return {"ok": false, "error": "invalid diplomatic outreach"}
	if st.treasury < cost:
		return {"ok": false, "error": "insufficient funds"}
	st.treasury -= cost
	var r := st.rel(pid, other)
	r["warmth"] = minf(1.0, float(r["warmth"]) + 0.08)
	r["trust"] = minf(1.0, float(r["trust"]) + 0.04)
	Bus.fire("relations_changed", st.pair_key(pid, other), null, 1)
	st.add_report("diplomacy", "Diplomatic outreach", "%s: warmth +0.08, trust +0.04 for %.0f credits." % [st.countries[other]["name"], cost])
	return {"ok": true}


func condemn(st: CampaignState, other: String) -> Dictionary:
	var pid := st.player_id()
	if not st.countries.has(other) or other == pid:
		return {"ok": false, "error": "invalid country"}
	var r := st.rel(pid, other)
	r["warmth"] = maxf(0.0, float(r["warmth"]) - 0.1)
	r["threat"] = minf(1.0, float(r["threat"]) + 0.08)
	Bus.fire("relations_changed", st.pair_key(pid, other), null, 1)
	st.add_report("diplomacy", "Public condemnation", st.countries[other]["name"] + " perceives a greater threat.")
	return {"ok": true}


func declare_war(st: CampaignState, a: String, b: String, cause: String) -> Dictionary:
	if not st.countries.has(a) or not st.countries.has(b) or a == b:
		return {"ok": false, "error": "invalid parties"}
	for w in st.wars.values():
		if ((a in w["sides_a"] and b in w["sides_b"]) or (b in w["sides_a"] and a in w["sides_b"])) \
				and w["status"] in ["active", "ceasefire"]:
			return {"ok": false, "error": "war or ceasefire already exists"}
	var wid := st.next_id("war")
	st.wars[wid] = {"id": wid, "sides_a": [a], "sides_b": [b], "start_day": st.day,
		"cause": cause, "status": "active", "losses": {}, "objectives": []}
	var r := st.rel(a, b)
	r["threat"] = 1.0
	r["warmth"] = 0.0
	Bus.fire("war_started", wid, null, 1)
	st.add_report("war", "War: %s vs %s" % [st.countries[a]["name"], st.countries[b]["name"]], "Cause: " + cause)
	st.add_history("War began between %s and %s" % [a, b])
	return {"ok": true, "war": wid}


func propose_ceasefire(st: CampaignState, war_id: String, actor: String = "") -> Dictionary:
	var w: Dictionary = st.wars.get(war_id, {})
	if w.is_empty() or w["status"] != "active":
		return {"ok": false, "error": "no active war"}
	var a: String = w["sides_a"][0]
	var b: String = w["sides_b"][0]
	if actor == "":
		actor = st.player_id()
	if actor != a and actor != b:
		return {"ok": false, "error": "only a party may propose a ceasefire"}
	var next_offer: Dictionary = w.get("next_offer_day", {})
	if st.day < int(next_offer.get(actor, 0)):
		return {"ok": false, "error": "wait until day %d before proposing again" % int(next_offer[actor])}
	next_offer[actor] = st.day + 7
	w["next_offer_day"] = next_offer
	var other := b if actor == a else a
	# The recipient knows its own strength, but estimates the proposer only
	# from formations in or adjacent to territory it controls.
	var observed_proposer := _observed_border_strength(st, other, actor)
	var recipient_strength := _war_strength(st, other)
	var willingness := clampf(0.55 + (observed_proposer - recipient_strength) * 0.02, 0.2, 0.85)
	if st.randf() < willingness:
		w["status"] = "ceasefire"
		var tid := st.next_id("treaty")
		st.treaties[tid] = {"id": tid, "type": "ceasefire", "parties": [a, b],
			"start_day": st.day, "expires_day": st.day + 30, "status": "active", "war": war_id}
		w["treaty"] = tid
		var r := st.rel(a, b)
		r["threat"] = 0.3
		Bus.fire("war_ended", war_id, null, 1)
		st.add_report("war", "Ceasefire accepted", "%s and %s stop hostilities for 30 days; treaty %s." % [
			st.countries[a]["name"], st.countries[b]["name"], tid])
		return {"ok": true, "accepted": true, "treaty": tid}
	st.add_report("war", "Ceasefire rejected", "%s declined the proposal after assessing its relative strength." % st.countries[other]["name"])
	return {"ok": true, "accepted": false}


func negotiate_transition(st: CampaignState) -> Dictionary:
	if st.outcome != "":
		return {"ok": false, "error": "campaign already ended"}
	var ceasefire := false
	for w in st.wars.values():
		if w["status"] == "ceasefire" and ((st.player_id() in w["sides_a"] and "cty_vardena" in w["sides_b"]) \
				or (st.player_id() in w["sides_b"] and "cty_vardena" in w["sides_a"])):
			ceasefire = true
	if not ceasefire:
		return {"ok": false, "error": "a government ceasefire is required first"}
	var admin := Administration.new()
	admin.init(null)
	var pos := admin.political_position(st)
	if float(pos["share"]) < float(admin.rules.get("settlement_share", 0.3)):
		return {"ok": false, "error": "control at least 30% of Vardena's regions"}
	if float(pos["support"]) < float(admin.rules.get("transition_support", 0.42)) \
			or float(pos["stability"]) < float(admin.rules.get("transition_stability", 0.4)) \
			or float(pos["legitimacy"]) < float(admin.rules.get("transition_legitimacy", 0.38)):
		return {"ok": false, "error": "controlled regions require support 0.42, stability 0.40 and legitimacy 0.38"}
	st.outcome = "negotiated_transition"
	st.add_report("campaign", "Negotiated transition", "The government agreed to a political transition after a ceasefire and sustained regional support.")
	Bus.fire("campaign_ended", st.outcome, null, 1)
	return {"ok": true, "outcome": st.outcome}


func _war_strength(st: CampaignState, country_id: String) -> float:
	var p := 0.0
	for f in st.formations_of(country_id):
		p += st.formation_power(f, {})
	return p


func _observed_border_strength(st: CampaignState, observer: String, target: String) -> float:
	var total := 0.0
	for f in st.formations_of(target):
		var r: Dictionary = st.regions[f["region"]]
		var visible: bool = r["controller"] == observer
		if not visible:
			for nb in r["neighbors"]:
				if st.regions[nb]["controller"] == observer:
					visible = true
					break
		if visible:
			total += st.formation_power(f, {})
	return total


func tick_day(st: CampaignState) -> void:
	for tid in st.treaties:
		var t: Dictionary = st.treaties[tid]
		if t["status"] == "active" and int(t["expires_day"]) <= st.day:
			t["status"] = "expired"
			var w: Dictionary = st.wars.get(t["war"], {})
			if not w.is_empty() and w["status"] == "ceasefire":
				w["status"] = "active"
				st.rel(t["parties"][0], t["parties"][1])["threat"] = 1.0
				st.add_report("war", "Ceasefire expired", "Treaty %s expired; hostilities resumed." % tid)
				Bus.fire("war_started", t["war"], null, 1)


func tick_week(st: CampaignState) -> void:
	for k in st.relations:
		var r: Dictionary = st.relations[k]
		r["threat"] = clampf(float(r["threat"]) - 0.005, 0.0, 1.0)
		r["warmth"] = clampf(float(r["warmth"]) - 0.002, 0.0, 1.0)
