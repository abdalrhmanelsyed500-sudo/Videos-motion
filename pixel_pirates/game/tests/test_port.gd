extends RefCounted
## CP-1 Fish Row: replays tests/fixtures/economy_cases.json made by tools/h2d/economy_logic.py (the Python twin) against
## port_state.gd and fishing.gd, checks the baked district data, the NPC walkers and that the objective text follows real
## state (purse, hold, nets). NOT YET RUN IN GODOT.
const PortState := preload("res://h2d/port_state.gd")
const Fishing := preload("res://h2d/fishing.gd")
const PortNpcs := preload("res://h2d/port_npcs.gd")
const PortGame := preload("res://h2d/port_game.gd")
const Ocean := preload("res://core/ocean.gd")
const DataLoader := preload("res://core/data_loader.gd")
const TOL := 0.0005


class StubWorld:
	extends RefCounted

	func walkable(_x: float, _z: float, _r: float = 0.0) -> bool:
		return true


func _state(tuning: Dictionary) -> PortState:
	var s := PortState.new()
	s.configure(tuning, DataLoader.load_dict("res://data/port/fish_market.json"), DataLoader.load_dict("res://data/port/recruits_port.json"))
	return s


func _fishing(tuning: Dictionary, seed_value: int = 1) -> Fishing:
	var f := Fishing.new()
	f.configure(tuning, DataLoader.load_dict("res://data/port/fishing_grounds.json"), seed_value)
	return f


func run(t: Object) -> void:
	var tuning := Ocean.load_tuning()
	var fx := DataLoader.load_dict("res://tests/fixtures/economy_cases.json")
	# the code defaults equal the JSON the designer edits
	for k in PortState.DEFAULTS.keys():
		t.check(tuning.has(k), "tuning has %s" % k)
		if tuning.has(k):
			t.check(absf(float(tuning[k]) - float(PortState.DEFAULTS[k])) < 0.000001, "port_state default of %s matches the JSON" % k)
	for k in Fishing.DEFAULTS.keys():
		t.check(tuning.has(k), "tuning has %s" % k)
		if tuning.has(k):
			t.check(absf(float(tuning[k]) - float(Fishing.DEFAULTS[k])) < 0.000001, "fishing default of %s matches the JSON" % k)
	# the random stream
	for c in fx["lcg"]:
		var s := int(c["seed"])
		for v in c["values"]:
			var r := Fishing.next_rand(s)
			s = int(r[0])
			t.check(absf(float(r[1]) - float(v)) < 0.000001, "LCG seed %s value %s" % [c["seed"], v])
	# hauls
	for c in fx["haul"]:
		var f := _fishing(tuning, int(c["seed"]))
		var g: Dictionary = f.grounds[str(c["ground"])]
		for h in c["hauls"]:
			var got := f.roll(g, Fishing.time_mult(float(c["hour"]), f.p), float(c["bonus"]))
			t.check(str(got["species"]) == str(h["species"]) and absf(float(got["kg"]) - float(h["kg"])) < 0.0001,
					"haul at %s hour %s: %s %.2f kg" % [c["ground"], c["hour"], h["species"], float(h["kg"])])
		t.check(f.seed_state == int(c["state_after"]), "generator state after the hauls at %s" % c["ground"])
	for c in fx["time_mult"]:
		var f2 := _fishing(tuning)
		t.check(absf(Fishing.time_mult(float(c["hour"]), f2.p) - float(c["mult"])) < 0.0001, "time multiplier at %s h" % c["hour"])
	# freshness
	for c in fx["freshness"]:
		var s2 := _state(tuning)
		if absf(float(c["spoil_mult"]) - 1.0) > 0.001:
			s2.crew.append("crew_silas_reed")
		t.check(absf(s2.freshness_of(0.0, float(c["age_days"])) - float(c["value"])) < TOL, "freshness after %s days x%s" % [c["age_days"], c["spoil_mult"]])
	# scripted sessions
	var n := 0
	for sess in fx["session"]:
		n += 1
		var st := _state(tuning)
		t.check(st.reales == int(sess["start_purse"]), "session %d starts with %d reales" % [n, int(sess["start_purse"])])
		var i := 0
		for step in sess["steps"]:
			i += 1
			var e: Dictionary = step["expect"]
			var tag := "session %d step %d (%s)" % [n, i, step["op"]]
			match str(step["op"]):
				"catch":
					var stored := st.add_catch(str(step["sp"]), float(step["kg"]), float(step["day"]))
					t.check(absf(stored - float(e["stored"])) < TOL, tag + ": kg stored")
				"sell_all":
					var r := st.sell_all(float(step["day"]))
					t.check(int(r["reales"]) == int(e["reales"]), tag + ": reales %d (expected %d)" % [int(r["reales"]), int(e["reales"])])
				"sell":
					var r2 := st.sell_species(str(step["sp"]), float(step["day"]))
					t.check(int(r2["reales"]) == int(e["reales"]), tag + ": reales %d (expected %d)" % [int(r2["reales"]), int(e["reales"])])
				"hire":
					t.check(st.hire(str(step["id"])) == str(e["result"]), tag + ": result " + str(e["result"]))
			t.check(st.reales == int(e["purse"]), tag + ": purse %d (expected %d)" % [st.reales, int(e["purse"])])
			t.check(absf(st.hold_kg() - float(e["hold_kg"])) < TOL, tag + ": hold kg")
			t.check(absf(st.capacity_kg() - float(e["capacity"])) < TOL, tag + ": capacity")
			for sp in (e["x"] as Dictionary).keys():
				t.check(absf(float(st.x.get(sp, 0.0)) - float(e["x"][sp])) < 0.0001, tag + ": market memory of %s" % sp)
	_selling_feedback(t, tuning)
	_recruits(t, tuning)
	_district(t)
	_walkers(t)
	_objectives(t, tuning)


## A sale must pay the documented amount and say so: the estimate before equals the payout, and a big sale lowers the price.
func _selling_feedback(t: Object, tuning: Dictionary) -> void:
	var s := _state(tuning)
	s.add_catch("spc_sardine", 20.0, 0.0)
	var est := s.estimate_all(0.0)
	var before := s.reales
	var lvl := s.price_level("spc_sardine", 0.0)
	var r := s.sell_all(0.0)
	t.check(int(r["reales"]) == est, "the estimate shown before selling equals the payout (%d)" % est)
	t.check(s.reales == before + est, "the purse grows by exactly the payout")
	t.check(lvl == 1.0 and s.price_level("spc_sardine", 0.0) < 1.0, "selling lowers the price level of that species")
	t.check(s.price_level("spc_sardine", 12.0) > s.price_level("spc_sardine", 0.0), "the price recovers with game days")
	t.check(s.hold_kg() == 0.0 and s.species_in_hold().is_empty(), "the hold is empty after selling")


func _recruits(t: Object, tuning: Dictionary) -> void:
	var s := _state(tuning)
	t.check(s.recruit_order.size() == 4, "four recruits in the capital")
	var total := 0
	for cid in s.recruit_order:
		var r: Dictionary = s.recruits[cid]
		total += int(r["cost"])
		t.check(str(r["gender"]) == "male", "%s is male (content rule 1)" % cid)
		t.check(int(r["cost"]) > 0 and (r["pages"] as Array).size() >= 3, "%s has a cost and dialogue" % cid)
		t.check(not s.is_hired(cid) and not s.can_afford(cid) or int(r["cost"]) <= s.reales, "%s affordability follows the purse" % cid)
	t.check(total == 143, "all four recruits cost 143 reales together (docs/CP1_CAPITAL_PORT.md)")
	s.reales = 18
	t.check(s.can_afford("crew_pip_larkin") and not s.can_afford("crew_tuck_marrow"), "18 reales buy Pip but not Tuck")
	t.check(s.hire("crew_pip_larkin") == "ok" and s.reales == 0, "hiring Pip takes his 18 reales")
	t.check(s.hire("crew_pip_larkin") == "already", "a hired hand cannot be hired twice")
	t.check(absf(s.effect("catch_bonus") - 0.1) < 0.0001, "Pip adds 10% to every haul")
	var s2 := _state(tuning)
	s2.crew.append("crew_garrick_stave")
	t.check(absf(s2.capacity_kg() - 60.0) < 0.0001, "Garrick adds 20 kg of hold")


func _district(t: Object) -> void:
	var meta := DataLoader.load_dict("res://h2d/art/anvil_cay.json")
	t.check(int(meta.get("version", 0)) >= 3, "anvil_cay.json is format v3")
	var port: Dictionary = meta.get("port", {})
	t.check(not port.is_empty(), "the baked island has the Fish Row district")
	if port.is_empty():
		return
	t.check((port["npcs"] as Array).size() >= 24, "at least 24 people in the district (%d)" % (port["npcs"] as Array).size())
	var groups: Dictionary = {}
	for n in port["npcs"]:
		groups[str((n as Dictionary)["group"])] = true
	for g in ["fisher", "merchant", "docker", "sailor", "shopkeeper", "townsman", "recruit"]:
		t.check(groups.has(g), "NPC group %s exists" % g)
	var ids: Dictionary = {}
	for it in port["interactions"]:
		ids[str((it as Dictionary)["kind"])] = true
	t.check(ids.has("market") and ids.has("notice"), "a market counter and a notice board can be used")
	t.check((port["ships"] as Array).size() >= 1 and (port["hulls"] as Array).size() >= 3, "moored ships exist and are solid")
	var recs: Dictionary = DataLoader.load_dict("res://data/port/recruits_port.json")["recruits"]
	for cid in recs.keys():
		t.check((port["recruit_spots"] as Dictionary).has(cid), "%s has a place in the district" % cid)
	var grounds: Dictionary = DataLoader.load_dict("res://data/port/fishing_grounds.json")["grounds"]
	for gid in grounds.keys():
		var g: Dictionary = grounds[gid]
		t.check(float(g["z"]) > 300.0, "%s lies out at sea, away from the harbour" % gid)


func _walkers(t: Object) -> void:
	var port: Dictionary = DataLoader.load_dict("res://h2d/art/anvil_cay.json")["port"]
	var a := PortNpcs.new()
	var b := PortNpcs.new()
	a.setup(port["npcs"] as Array)
	b.setup(port["npcs"] as Array)
	var w := StubWorld.new()
	for _i in 600:
		a.step(0.1, w, Vector2(-60.0, 0.0))
		b.step(0.1, w, Vector2(-60.0, 0.0))
	var same := true
	var moved := 0
	for i in a.people.size():
		var p := a.people[i] as Dictionary
		var q := b.people[i] as Dictionary
		if absf(float(p["x"]) - float(q["x"])) > 0.0001 or absf(float(p["z"]) - float(q["z"])) > 0.0001:
			same = false
		if Vector2(float(p["x"]) - float(p["hx"]), float(p["z"]) - float(p["hz"])).length() > 0.5:
			moved += 1
		if str(p["mode"]) == "stand":
			t.check(float(p["x"]) == float(p["hx"]) and float(p["z"]) == float(p["hz"]), "%s keeps his place" % p["id"])
		else:
			var d := Vector2(float(p["x"]) - float(p["hx"]), float(p["z"]) - float(p["hz"])).length()
			t.check(d <= float(p["r"]) + 0.01, "%s stays within %.1f m of his post" % [p["id"], float(p["r"])])
	t.check(same, "the walkers are deterministic")
	t.check(moved >= 3, "some people really walk (%d moved)" % moved)
	var i0 := a.index_of_recruit("crew_pip_larkin")
	t.check(i0 >= 0, "Pip stands in the district")
	a.hide_recruit("crew_pip_larkin")
	t.check(bool((a.people[i0] as Dictionary)["hidden"]), "a hired recruit leaves the street")
	t.check(a.nearest(float((a.people[i0] as Dictionary)["x"]), float((a.people[i0] as Dictionary)["z"]), 2.0, true) != i0, "a hired recruit cannot be talked to")


func _objectives(t: Object, tuning: Dictionary) -> void:
	var g := PortGame.new()
	g.state = _state(tuning)
	g.fishing = _fishing(tuning)
	var at_sea := {"ashore": false, "docked": false, "sailing": true, "now": 0.0}
	var ashore := {"ashore": true, "docked": true, "sailing": false, "now": 0.0}
	t.check(g.objective(at_sea).contains("Pilchard Shallows"), "start objective points to the nearest ground")
	g.state.add_catch("spc_sardine", 20.0, 0.0)
	t.check(g.objective(at_sea).contains("Sail home"), "with fish aboard at sea: sail home")
	t.check(g.objective(ashore).contains("Fish Market"), "with fish ashore: go to the Fish Market")
	g.state.sell_all(0.0)
	t.check(g.state.reales > 5, "the sale paid something")
	g.state.reales = 18
	t.check(g.objective(ashore).contains("Pip Larkin"), "with 18 reales: find Pip Larkin")
	g.state.hire("crew_pip_larkin")
	t.check(g.objective(ashore).contains("Marrow") and g.objective(ashore).contains("30"), "after Pip the cheapest recruit is Tuck, 30 reales")
	g.state.reales = 500
	for cid in g.state.recruit_order:
		g.state.hire(cid)
	t.check(g.objective(ashore).contains("Crew complete"), "all hired: the loop is complete")
	# nets
	g.fishing.start(-300.0, 560.0, 0, 0.1)
	t.check(g.fishing.active, "nets go down inside the Pilchard Shallows")
	var no := g.fishing.can_start(0.0, 0.0, 0, 0.1)
	t.check(not bool(no["ok"]) and str(no["reason"]).contains("Pilchard"), "no nets near the harbour; the answer names the nearest ground")
	var rough := _fishing(tuning).can_start(-300.0, 560.0, 0, 0.9)
	t.check(not bool(rough["ok"]), "no nets in a rough sea")
	var deep := _fishing(tuning).can_start(300.0, 1750.0, 0, 0.1)
	t.check(not bool(deep["ok"]) and str(deep["reason"]).contains("hand"), "Blue Drop needs a hand aboard")
	g.free()
