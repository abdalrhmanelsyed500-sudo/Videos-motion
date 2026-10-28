extends RefCounted
const Bus = preload("res://core/bus.gd")
const CampaignState = preload("res://core/campaign_state.gd")
## Relationship graph (trust/warmth/threat per pair) + a first set of real
## actions with persistent, inspectable consequences. Treaties = PLANNED (Stage 3).

func init(_state) -> void:
	pass


func improve_relations(st: CampaignState, other: String, cost: float) -> Dictionary:
	var pid := st.player_id()
	if not st.countries.has(other) or other == pid:
		return {"ok": false, "error": "unknown country"}
	if st.treasury < cost:
		return {"ok": false, "error": "insufficient funds"}
	st.treasury -= cost
	var r := st.rel(pid, other)
	r["warmth"] = clampf(float(r["warmth"]) + 0.08, 0, 1)
	r["trust"] = clampf(float(r["trust"]) + 0.04, 0, 1)
	Bus.fire("relations_changed", st.pair_key(pid, other), null, 1)
	st.add_report("diplomacy", "Diplomatic outreach to " + st.countries[other]["name"],
		"Warmth +0.08, trust +0.04 for %.0f credits." % cost)
	return {"ok": true}


func condemn(st: CampaignState, other: String) -> Dictionary:
	var pid := st.player_id()
	if not st.countries.has(other):
		return {"ok": false, "error": "unknown country"}
	var r := st.rel(pid, other)
	r["warmth"] = maxf(0.0, float(r["warmth"]) - 0.1)
	r["threat"] = clampf(float(r["threat"]) + 0.08, 0, 1)
	Bus.fire("relations_changed", st.pair_key(pid, other), null, 1)
	st.add_report("diplomacy", "Public statement against " + st.countries[other]["name"],
		"Relations cooled; they now perceive more threat from you.")
	return {"ok": true}


func declare_war(st: CampaignState, a: String, b: String, cause: String) -> Dictionary:
	var wid := st.next_id("war")
	st.wars[wid] = {"id": wid, "sides_a": [a], "sides_b": [b], "start_day": st.day,
		"cause": cause, "status": "active", "losses": {}, "objectives": []}
	var r := st.rel(a, b)
	r["threat"] = 1.0
	r["warmth"] = 0.0
	Bus.fire("war_started", wid, null, 1)
	st.add_report("war", "War: %s vs %s" % [st.countries[a]["name"], st.countries[b]["name"]],
		"Cause: " + cause)
	st.add_history("War began between %s and %s" % [a, b])
	return {"ok": true, "war": wid}


func propose_ceasefire(st: CampaignState, war_id: String) -> Dictionary:
	var w: Dictionary = st.wars.get(war_id, {})
	if w.is_empty() or w["status"] != "active":
		return {"ok": false, "error": "no active war"}
	var a: String = w["sides_a"][0]
	var b: String = w["sides_b"][0]
	var pa := _war_strength(st, a)
	var pb := _war_strength(st, b)
	var me := a if a == st.player_id() else b
	var them := b if me == a else a
	var my_pow := pa if me == a else pb
	var their_pow := pb if me == a else pa
	var willingness := clampf(0.75 - (my_pow - their_pow) * 0.004, 0.1, 0.9)
	if st.randf() < willingness:
		w["status"] = "ceasefire"
		var r := st.rel(a, b)
		r["threat"] = maxf(0.2, float(r["threat"]) - 0.3)
		Bus.fire("war_ended", war_id, null, 1)
		st.add_report("war", "Ceasefire accepted",
			"%s and %s stop hostilities. Front lines freeze." % [
			st.countries[a]["name"], st.countries[b]["name"]])
		return {"ok": true, "accepted": true}
	st.add_report("war", "Ceasefire rejected", st.countries[them]["name"] +
		" believes it can still gain on the battlefield.")
	return {"ok": true, "accepted": false}


func _war_strength(st: CampaignState, country_id: String) -> float:
	var p := 0.0
	for f in st.formations_of(country_id):
		p += st.formation_power(f, {})
	return p


func tick_week(st: CampaignState) -> void:
	# slow drift: neighbours' threat perceptions relax or tighten by behaviour
	for k in st.relations:
		var r: Dictionary = st.relations[k]
		r["threat"] = clampf(float(r["threat"]) - 0.005, 0, 1)
		r["warmth"] = clampf(float(r["warmth"]) - 0.002, 0, 1)
