extends SceneTree
const CampaignState = preload("res://core/campaign_state.gd")
const WorldGenerator = preload("res://world/world_generator.gd")
const MarketSystem = preload("res://economy/market_system.gd")
const EconomySystem = preload("res://economy/economy_system.gd")
const CommandSystem = preload("res://military/command_system.gd")
const CombatSystem = preload("res://military/combat_system.gd")
const SupplySystem = preload("res://logistics/supply_system.gd")
const DiplomacySystem = preload("res://diplomacy/diplomacy_system.gd")
const FactionAI = preload("res://ai/faction_ai.gd")
const SaveSystem = preload("res://persistence/save_system.gd")
## Headless logic suite: world gen, economy/market, command/combat/logistics,
## diplomacy/AI, save/load. Prints "TESTS: PASS: n checks" or "TESTS: FAIL: msg".

var checks := 0
var failures: Array = []


func _initialize() -> void:
	run()
	var line := "TESTS: %s: %d checks" % ["PASS" if failures.is_empty() else "FAIL " + "; ".join(failures), checks]
	print(line)
	quit(0 if failures.is_empty() else 1)


func ok(cond: bool, label: String) -> void:
	checks += 1
	if not cond:
		failures.append(label)


func run() -> void:
	test_worldgen()
	test_economy_market()
	test_command_combat_logistics()
	test_diplomacy_ai()
	test_save_load()


func fresh(seed_int: int) -> CampaignState:
	var sc := {"treasury": 12000, "stability": 0.45, "start_day": 0,
		"inventory": {"rif_surplus": 40, "rif_basic": 12, "veh_pickup": 3, "veh_truck": 2},
		"start_formations": [
			{"country": "cty_player", "name": "Safehouse Guard", "region": "reg_09",
				"units": [{"class": "infantry", "equip": "rif_surplus", "count": 4, "condition": 0.85}]},
			{"country": "cty_player", "name": "Convoy Column", "region": "reg_13",
				"units": [{"class": "logistics", "equip": "veh_truck", "count": 2, "condition": 0.8}]}],
		"title": "test"}
	return WorldGenerator.generate(seed_int, sc)


func test_worldgen() -> void:
	for seed_int in [1, 7, 42, 999, 20261028]:
		var st := fresh(seed_int)
		ok(st.regions.size() == 24, "region count seed %d" % seed_int)
		ok(st.countries.size() == 5, "country count")
		var sym := true
		for rid in st.regions:
			for nb in st.regions[rid]["neighbors"]:
				if not rid in st.regions[nb]["neighbors"]:
					sym = false
		ok(sym, "neighbor symmetry seed %d" % seed_int)
		var passable := func(_r: String) -> bool: return true
		ok(not WorldGenerator.path_bfs(st, "reg_01", "reg_24", passable).is_empty(),
			"cross-continent path seed %d" % seed_int)
		ok(CampaignState.validate(st.serialize()).is_empty(), "self-validate seed %d" % seed_int)
	# determinism: same seed -> same layout
	var a := fresh(123)
	var b := fresh(123)
	ok(a.regions["reg_03"]["pos"] == b.regions["reg_03"]["pos"] and
		a.regions["reg_03"]["terrain"] == b.regions["reg_03"]["terrain"], "determinism")


func test_economy_market() -> void:
	var st := fresh(5)
	var market := MarketSystem.new(); market.init(null)
	ok(market.catalog.size() >= 12, "catalog loaded")
	var t0 := st.treasury
	var q := market.quote(st, "rif_basic", 10)
	ok(q["ok"] and q["price"] > 0, "quote ok")
	var res := market.purchase(st, "rif_basic", 10)
	ok(res["ok"], "purchase ok")
	ok(st.treasury < t0, "treasury debited")
	var oid: String = res["order"]["id"]
	ok(st.market_orders[oid]["status"] == "in_transit", "order in transit")
	var before: int = int(st.inventory.get("rif_basic", 0))
	for d in range(30):
		st.day += 1
		market.tick_day(st)
	ok(st.market_orders[oid]["status"] == "delivered", "order delivered by eta")
	ok(int(st.inventory.get("rif_basic", 0)) == before + 10, "inventory increased once")
	# unaffordable purchase must not create anything
	st.treasury = 5
	var bad := market.purchase(st, "tnk_main_old", 1)
	ok(not bad["ok"], "unaffordable rejected")
	ok(st.market_orders.size() == 1, "no phantom order")
	# Equipment needs trained personnel or compatible squads; recruit a reserve first.
	st.treasury = 5000.0
	var econ := EconomySystem.new(); econ.init(null)
	var recruited := econ.recruit(st, "reg_09", 24, 25.0)
	ok(recruited["ok"] and recruited["recruited"] >= 12, "reserve recruited before equipment issue")
	var fid: String = st.formations_of(st.player_id())[0]["id"]
	var eq := market.equip_from_inventory(st, fid, "rif_basic", 5)
	ok(eq["ok"] and int(st.inventory["rif_basic"]) == before + 5, "equip issued")
	# upkeep drains treasury daily
	var t1 := st.treasury
	econ.tick_day(st, market.catalog)
	ok(st.treasury <= t1, "daily upkeep applied")
	var income := econ.tick_week(st)
	ok(income > 0, "weekly revenue from controlled regions")


func test_command_combat_logistics() -> void:
	var st := fresh(11)
	var cmd := CommandSystem.new(); cmd.init(null)
	var combat := CombatSystem.new(); combat.init(null)
	var supply := SupplySystem.new(); supply.init(null)
	var market := MarketSystem.new(); market.init(null)
	var fid: String = st.formations_of(st.player_id())[0]["id"]
	var from_r: String = st.formations[fid]["region"]
	var target: String = st.regions[from_r]["neighbors"][0]
	st.rel(st.player_id(), st.regions[target]["controller"])["threat"] = 0.9
	var mv := cmd.issue_move(st, fid, target)
	ok(mv["ok"], "move order accepted")
	ok(cmd.issue_move(st, fid, "reg_99").has("error") or not cmd.issue_move(st, fid, "reg_99")["ok"],
		"bad target rejected")
	var guard := 0
	while st.formations[fid]["region"] != target and guard < 40:
		st.day += 1
		cmd.tick_day(st, market.catalog)
		guard += 1
	ok(st.formations[fid]["region"] == target, "formation arrived")
	# Control must change through the actual order path, not by test assignment.
	ok(st.regions[target]["controller"] == "cty_player", "uncontested hostile region captured")
	# combat: plant a hostile formation in same region and resolve
	var enemy_fid := st.next_id("frm")
	st.formations[enemy_fid] = {"id": enemy_fid, "country": "cty_vardena", "name": "Garrison X",
		"region": target, "units": [{"class": "infantry", "equip": "rif_surplus", "count": 4, "condition": 0.8}],
		"morale": 0.7, "cohesion": 0.7, "readiness": 0.8, "supplies": 0.9,
		"experience": 0, "commander": "X", "orders": [], "loyalty": 0.6}
	st.rel("cty_player", "cty_vardena")["threat"] = 0.9
	var pairs := combat.hostile_pairs(st, target)
	ok(pairs.size() == 1, "hostile pair detected")
	var before_rep := st.reports.size()
	var out := combat.resolve_engagement(st, pairs[0][0], pairs[0][1], market.catalog, 1.0)
	combat.post_battle(st, out["report"], market.catalog)
	ok(st.reports.size() > before_rep, "battle report recorded")
	var losses: Dictionary = out["report"]["losses"]
	ok(losses.has(fid) or losses.has(enemy_fid), "losses recorded per side")
	# logistics: isolated formation loses supplies over time
	var iso_fid: String = st.formations_of(st.player_id())[1]["id"]
	st.formations[iso_fid]["region"] = "reg_24"  # far from player capital, no link
	var s0: float = st.formations[iso_fid]["supplies"]
	for d in range(10):
		supply.tick_day(st)
	ok(st.formations[iso_fid]["supplies"] <= s0, "supplies never increase when isolated")
	var w := supply.build_depot(st, "reg_09", 100.0)
	ok(w["ok"], "depot build ok")


func test_diplomacy_ai() -> void:
	var st := fresh(21)
	var dip := DiplomacySystem.new(); dip.init(null)
	var ai := FactionAI.new(); ai.init(null)
	var market := MarketSystem.new(); market.init(null)
	var w := dip.declare_war(st, "cty_vardena", "cty_player", "constitutional crisis")
	ok(w["ok"], "war declared")
	ok(not CombatSystem.new().hostile_pairs(st, "reg_09").is_empty() or
		st.rel("cty_player", "cty_vardena")["threat"] > 0.55, "hostility active")
	var imp := dip.improve_relations(st, "cty_meridia", 500.0)
	ok(imp["ok"], "improve relations ok")
	var n_before := st.formations.size()
	for week in range(6):
		ai.tick_week(st, market.catalog)
	ok(st.formations.size() >= n_before, "ai never loses formations illegally")
	var moved := false
	for f in st.formations:
		if not st.formations[f]["country"] == st.player_id() and st.formations[f]["orders"].size():
			moved = true
	ok(moved, "ai issues a real movement order")
	var cf := dip.propose_ceasefire(st, w["war"])
	ok(cf["ok"], "ceasefire proposal processed")


func test_save_load() -> void:
	var st := fresh(33)
	var sys := SaveSystem.new()
	st.treasury = 7777.5
	st.day = 12
	var err := sys.save_campaign(st, 3, "suite")
	ok(err == "", "save wrote")
	st.treasury = 1.0
	st.day = 99
	var res := sys.load_campaign(3)
	ok(res["error"] == "", "load ok")
	var st2: CampaignState = res["state"]
	ok(abs(st2.treasury - 7777.5) < 0.01 and st2.day == 12, "state restored")
	ok(st2.regions.size() == 24 and st2.formations.size() == st.formations.size(),
		"entities restored")
	# corruption handling
	var bad := st.serialize()
	bad.erase("regions")
	ok(not CampaignState.validate(bad).is_empty(), "corrupt save rejected")
	var bad2 := st.serialize()
	bad2["regions"]["reg_01"]["neighbors"].append("reg_99")
	ok(not CampaignState.validate(bad2).is_empty(), "dangling neighbor rejected")
