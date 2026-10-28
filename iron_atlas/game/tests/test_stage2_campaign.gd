extends SceneTree
## Scripted compact campaign: actual recruitment, equipment, connected movement,
## defense, administration and ceasefire to a negotiated transition.
var checks := 0
var failures: Array = []
var frames := 0
var GS = null
var CLK = null


func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures.append(label)


func _initialize() -> void:
	GS = root.get_node("GameState")
	CLK = root.get_node("CampaignClock")
	check(GS.new_campaign(123, 24) == "", "new regional campaign")


func _process(_delta: float) -> void:
	frames += 1
	if frames != 2:
		return
	var st = GS.cs
	var force: Dictionary = st.formations_of(st.player_id())[0]
	var fid: String = force["id"]
	var start_people := 0
	for f in st.formations_of(st.player_id()):
		start_people += st.formation_personnel(f)
	check(start_people == 60, "campaign starts with 60 fighters")
	var war: Dictionary = GS.diplomacy.declare_war(st, st.player_id(), "cty_vardena", "constitutional crisis")
	check(war["ok"], "conflict declared")
	var rec: Dictionary = GS.economy.recruit(st, "reg_09", 120, 25.0)
	check(rec["ok"], "field force recruited with funds and manpower")
	var squad_count: int = int(force.get("personnel_reserve", 0)) / 12
	var issue: Dictionary = GS.market.equip_from_inventory(st, fid, "rif_surplus", squad_count)
	check(issue["ok"] and int(issue["created_squads"]) > 0, "recruits become equipped squads")
	check(GS.command.issue_move(st, fid, "reg_10")["ok"], "advance to neighboring Vardena district")
	var arrived := advance_until(fid, "reg_10", 45)
	check(arrived and st.regions["reg_10"]["controller"] == st.player_id(), "regional advance captures district")
	# Leave an actually recruited and equipped home guard; no test-created units.
	if st.regions["reg_09"]["controller"] == st.player_id():
		var guard: Dictionary = GS.economy.recruit(st, "reg_09", 48, 25.0)
		if guard.get("ok", false):
			var guard_force: Dictionary = st.formations[guard["formation"]]
			var n: int = int(guard_force.get("personnel_reserve", 0)) / 12
			if n > 0:
				GS.market.equip_from_inventory(st, guard_force["id"], "rif_surplus", n)
	check(st.formations_of(st.player_id()).size() >= 3, "home guard recruited and funded")
	var move: Dictionary = GS.command.issue_move(st, fid, "reg_04")
	check(move["ok"], "advance to second Vardena district")
	arrived = advance_until(fid, "reg_04", 60)
	check(arrived and st.regions["reg_04"]["controller"] == st.player_id(), "second district captured")
	# Fund real economic support until the settlement threshold is reached.
	var funded := true
	for rid in ["reg_09", "reg_10", "reg_04"]:
		if st.regions[rid]["controller"] != st.player_id():
			funded = false
			continue
		var attempts := 0
		while float(st.regions[rid]["political_support"]) < 0.48 and attempts < 15:
			var investment: Dictionary = GS.administration.invest(st, st.player_id(), rid, "economy")
			if not investment["ok"]:
				funded = false
				break
			attempts += 1
	check(funded, "local support funded in all three districts")
	var pos: Dictionary = GS.administration.political_position(st)
	check(float(pos["share"]) >= 0.3 and float(pos["support"]) >= 0.42 and float(pos["stability"]) >= 0.4, "political transition prerequisites achieved")
	var ceasefire := false
	for i in 6:
		if st.wars[war["war"]]["status"] == "ceasefire":
			ceasefire = true
			break
		var offer: Dictionary = GS.diplomacy.propose_ceasefire(st, war["war"])
		if offer.get("accepted", false):
			ceasefire = true
			break
		for j in 7:
			advance_one_day()
	check(ceasefire, "ceasefire negotiated under actual rules")
	var transition: Dictionary = GS.diplomacy.negotiate_transition(st)
	check(transition["ok"] and st.outcome == "negotiated_transition", "end-to-end negotiated transition")
	if not failures.is_empty():
		print("CAMPAIGN DIAGNOSTIC day=", st.day, " cash=", st.treasury, " position=", GS.administration.political_position(st), " outcome=", st.outcome)
		for rid in ["reg_09", "reg_10", "reg_04"]:
			print(rid, " ", st.regions[rid]["controller"], " support ", st.regions[rid]["political_support"], " stability ", st.regions[rid]["stability"])
	print("TESTS: %s: %d checks" % ["PASS" if failures.is_empty() else "FAIL " + "; ".join(failures), checks])
	quit(0 if failures.is_empty() else 1)


func advance_until(fid: String, destination: String, limit: int) -> bool:
	for i in limit:
		if not GS.cs.formations.has(fid):
			return false
		if GS.cs.formations[fid]["region"] == destination and GS.cs.regions[destination]["controller"] == GS.cs.player_id():
			return true
		advance_one_day()
	return false


func advance_one_day() -> void:
	CLK.advance_days(1, GS.cs)
	var regions := {}
	for f in GS.cs.formations.values():
		if f["country"] == GS.cs.player_id():
			regions[f["region"]] = true
	for rid in regions:
		# Several rounds simulate a player deliberately choosing auto-resolve.
		for i in 4:
			if not GS.resolve_player_contact(rid)["ok"]:
				break
