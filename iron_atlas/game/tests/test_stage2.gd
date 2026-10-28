extends SceneTree
## Stage 2 regression tests: authoritative outcomes, resource constraints,
## 200-region validation, migration and idempotent transactions.
const CampaignState = preload("res://core/campaign_state.gd")
const World = preload("res://world/world_generator.gd")
const Economy = preload("res://economy/economy_system.gd")
const Market = preload("res://economy/market_system.gd")
const Command = preload("res://military/command_system.gd")
const Combat = preload("res://military/combat_system.gd")
const Supply = preload("res://logistics/supply_system.gd")
const Diplomacy = preload("res://diplomacy/diplomacy_system.gd")
const Admin = preload("res://administration/administration_system.gd")
const AI = preload("res://ai/faction_ai.gd")
const Save = preload("res://persistence/save_system.gd")

var checks := 0
var failures: Array = []


func _initialize() -> void:
	test_world()
	test_recruit_market()
	test_capture_administration()
	test_logistics()
	test_combat()
	test_ai()
	test_politics()
	test_persistence()
	print("TESTS: %s: %d checks" % ["PASS" if failures.is_empty() else "FAIL " + "; ".join(failures), checks])
	quit(0 if failures.is_empty() else 1)


func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures.append(label)


func scenario(size: int = 24) -> Dictionary:
	var f := FileAccess.open("res://data/scenario_vardena.json", FileAccess.READ)
	var data: Dictionary = JSON.parse_string(f.get_as_text())
	f.close()
	data["region_count"] = size
	return data


func fresh(seed_int: int = 75, size: int = 24) -> CampaignState:
	return World.generate(seed_int, scenario(size))


func market() -> Market:
	var m := Market.new()
	m.init(null)
	return m


func test_world() -> void:
	for seed_int in [1, 7, 42, 999, 20261028]:
		var st := fresh(seed_int, 200)
		var again := fresh(seed_int, 200)
		check(st.regions.size() == 200, "200 regions seed %d" % seed_int)
		check(World.validate_world(st).is_empty(), "large world validation seed %d" % seed_int)
		check(JSON.stringify(st.serialize()) == JSON.stringify(again.serialize()), "seed determinism %d" % seed_int)
		check(not World.path_bfs(st, "reg_01", "reg_200", func(_r): return true).is_empty(), "200 land routes %d" % seed_int)
		check(CampaignState.validate(st.serialize()).is_empty(), "large state IDs %d" % seed_int)
	for size in [25, 50, 400]:
		var boundary := fresh(42, size)
		check(boundary.regions.size() == size, "configured world size %d" % size)
		check(World.validate_world(boundary).is_empty(), "configured world validates %d" % size)
	var st := fresh(42, 200)
	check("reg_20" in st.regions["reg_01"]["sea_neighbors"], "sea link is represented separately")
	check(World.path_bfs(st, "reg_01", "reg_20", func(rid): return rid == "reg_20").is_empty(), "sea link is not a land route")
	check(World.path_bfs(st, "unknown", "reg_01", func(_r): return true).is_empty(), "unknown path endpoint rejected")
	var terrains := {}
	var resources := {}
	var cities := 0
	for r in st.regions.values():
		terrains[r["terrain"]] = true
		for resource in r["resources"]:
			resources[resource] = true
		if r["is_city"]:
			cities += 1
	check(terrains.size() >= 6, "terrain diversity")
	check(resources.size() >= 5, "resource diversity")
	check(cities >= 10 and cities < 100, "cities distributed")
	var broken := fresh(8, 200)
	broken.regions["reg_01"]["neighbors"].append("reg_missing")
	check(not World.validate_world(broken).is_empty(), "dangling region reference rejected")
	var disconnected := fresh(9, 200)
	var old: Array = disconnected.regions["reg_01"]["neighbors"].duplicate()
	for nb in old:
		disconnected.regions[nb]["neighbors"].erase("reg_01")
	disconnected.regions["reg_01"]["neighbors"] = []
	check(not World.validate_world(disconnected).is_empty(), "disconnected land graph rejected")


func test_recruit_market() -> void:
	var st := fresh()
	var m := market()
	var econ := Economy.new()
	var f: Dictionary = st.formations_of(st.player_id())[0]
	var balance := st.treasury
	var pool: int = st.countries[st.player_id()]["manpower_pool"]
	var wages := econ.personnel_upkeep(st)
	var rec := econ.recruit(st, "reg_09", 24, 25.0)
	check(rec["ok"] and int(rec["recruited"]) >= 12, "real recruitment")
	check(st.treasury == balance - float(rec["cost"]), "recruitment paid once")
	check(int(st.countries[st.player_id()]["manpower_pool"]) == pool - int(rec["recruited"]), "manpower pool debited")
	check(int(f["personnel_reserve"]) == int(rec["recruited"]), "personnel placed in reserve")
	check(econ.personnel_upkeep(st) > wages, "reserve incurs recurring wages")
	var units_before: int = int(f["units"][0]["count"])
	var store_before: int = int(st.inventory["rif_surplus"])
	var issued := m.equip_from_inventory(st, f["id"], "rif_surplus", 1)
	check(issued["ok"] and int(issued["created_squads"]) == 1, "reserve converted to equipped squad")
	check(int(f["units"][0]["count"]) == units_before + 1 and int(st.inventory["rif_surplus"]) == store_before - 1, "equipment changes inventory and composition")
	check(int(f["personnel_reserve"]) == int(rec["recruited"]) - 12, "squad consumes 12 people")
	check(not econ.recruit(st, "reg_09", 12, 0.0)["ok"], "configured recruitment price cannot be bypassed")
	var protective_before: int = int(st.inventory["kit_protect"])
	check(m.equip_from_inventory(st, f["id"], "kit_protect", 1)["ok"] and int(f["attachments"]["kit_protect"]) == 1 and int(st.inventory["kit_protect"]) == protective_before - 1, "protective gear assigned from stock")
	st.inventory["com_secure"] = 1
	var combat := Combat.new()
	var power_before := combat.power_of(st, f, m.catalog)
	check(m.equip_from_inventory(st, f["id"], "com_secure", 1)["ok"] and combat.power_of(st, f, m.catalog) > power_before, "communications gear affects combat")
	var old_damaged: int = int(st.countries[st.player_id()]["damaged_inventory"].get("rif_surplus", 0))
	check(m.equip_from_inventory(st, f["id"], "rif_basic", 1)["ok"] and int(st.countries[st.player_id()]["damaged_inventory"]["rif_surplus"]) > old_damaged, "replaced worn equipment remains damaged")
	check(not m.equip_from_inventory(st, f["id"], "rif_surplus", -1)["ok"], "negative equipment rejected")
	check(not m.purchase(st, "rif_basic", 0)["ok"] and not m.purchase(st, "not_an_item", 1)["ok"], "invalid purchases rejected")
	var rng_before: int = st.rng_state
	var q := m.quote(st, "rif_improved", 1)
	check(q["ok"] and int(st.rng_state) == rng_before and m.quote(st, "rif_improved", 1)["price"] == q["price"], "quote is stable and side effect free")
	var supplier_before: float = float(st.rel(st.player_id(), "cty_meridia")["warmth"])
	var upkeep_before := econ.equipment_upkeep(st, m.catalog)
	balance = st.treasury
	var purchase := m.purchase(st, "rif_improved", 1)
	check(purchase["ok"] and st.treasury == balance - float(q["price"]), "purchase paid exact quoted price")
	var oid: String = purchase["order"]["id"]
	check(st.market_orders[oid]["status"] == "in_transit" and int(st.inventory.get("rif_improved", 0)) == 0, "purchase not delivered early")
	st.day = int(purchase["order"]["eta_day"])
	m.tick_day(st)
	check(st.market_orders[oid]["status"] == "delivered" and int(st.inventory["rif_improved"]) == 1, "delivery reaches inventory")
	check(float(st.rel(st.player_id(), "cty_meridia")["warmth"]) > supplier_before, "supplier relationship changes on delivery")
	check(econ.equipment_upkeep(st, m.catalog) > upkeep_before, "delivered stored equipment incurs maintenance")
	var after_delivery := st.treasury
	m.tick_day(st); m.tick_day(st)
	check(int(st.inventory["rif_improved"]) == 1 and st.treasury == after_delivery, "no repeated delivery or payment")
	var second := m.purchase(st, "rif_basic", 1)
	var cap: String = st.countries[st.player_id()]["capital"]
	var item_before: int = int(st.inventory["rif_basic"])
	st.regions[cap]["controller"] = "cty_vardena"
	st.day = int(second["order"]["eta_day"])
	m.tick_day(st)
	check(second["order"]["status"] == "delayed" and int(st.inventory["rif_basic"]) == item_before, "lost depot delays delivery")
	st.regions[cap]["controller"] = st.player_id()
	m.tick_day(st)
	check(second["order"]["status"] == "delivered" and int(st.inventory["rif_basic"]) == item_before + 1, "restored depot releases delivery")
	var contested := fresh(81)
	var delayed := m.purchase(contested, "rif_basic", 1)
	var hostile: Dictionary = contested.formations_of("cty_vardena")[0]
	var home: String = hostile["region"]
	hostile["region"] = contested.countries[contested.player_id()]["capital"]
	contested.day = int(delayed["order"]["eta_day"])
	m.tick_day(contested)
	check(delayed["order"]["status"] == "delayed", "contested capital interrupts delivery")
	hostile["region"] = home
	m.tick_day(contested)
	check(delayed["order"]["status"] == "delivered", "delivery resumes after capital secured")
	var norders := st.market_orders.size()
	st.countries["cty_vardena"]["treasury"] = 0.0
	check(not m.purchase_for(st, "cty_vardena", "rif_basic", 1)["ok"] and st.market_orders.size() == norders, "AI insufficient funds rejected")


func test_capture_administration() -> void:
	var st := fresh(11)
	var cmd := Command.new()
	var m := market()
	var admin := Admin.new(); admin.init(null)
	var econ := Economy.new()
	var fid: String = st.formations_of(st.player_id())[0]["id"]
	var old_stability: float = float(st.regions["reg_10"]["stability"])
	var mv := cmd.issue_move(st, fid, "reg_10")
	check(mv["ok"], "land move accepted")
	for d in 20:
		st.day += 1
		cmd.tick_day(st, m.catalog)
	check(st.formations[fid]["region"] == "reg_10", "movement reaches target")
	var r: Dictionary = st.regions["reg_10"]
	check(r["controller"] == st.player_id(), "uncontested hostile territory actually captured")
	check(float(r["stability"]) < old_stability and float(r["opposition"]) >= 0.5 and float(r["recovery_progress"]) == 0.0, "capture creates unstable occupation")
	var balance := st.treasury
	var pressure: float = r["security_pressure"]
	var investment := admin.invest(st, st.player_id(), "reg_10", "security")
	check(investment["ok"] and st.treasury == balance - 200.0 and float(r["security_pressure"]) < pressure, "security investment paid and reduces pressure")
	check(not admin.invest(st, st.player_id(), "reg_01", "economy")["ok"], "cannot administer enemy territory")
	r["infra_condition"] = 0.25
	check(admin.invest(st, st.player_id(), "reg_10", "infrastructure")["ok"] and float(r["infra_condition"]) > 0.25, "infrastructure investment repairs damage")
	r["productivity"] = 0.2
	var low_income := econ.tick_week(st)
	r["productivity"] = 0.95
	var high_income := econ.tick_week(st)
	check(high_income > low_income, "regional productivity affects real tax income")
	balance = st.treasury
	admin.tick_week(st)
	check(st.treasury < balance, "occupation and focus have recurring costs")
	var f: Dictionary = st.formations[fid]
	f["wounded"] = 20
	f["supplies"] = 1.0
	var med_before: int = int(st.inventory["med_kit"])
	var reserve_before: int = int(f["personnel_reserve"])
	admin.tick_week(st)
	check(int(st.inventory["med_kit"]) == med_before - 1 and int(f["wounded"]) == 15 and int(f["personnel_reserve"]) == reserve_before + 5, "medical stock accelerates wounded recovery")


func test_logistics() -> void:
	var st := fresh(22)
	var supply := Supply.new()
	var m := market()
	var cmd := Command.new()
	var cap: String = st.countries[st.player_id()]["capital"]
	check(supply.connected_to_capital(st, cap, st.player_id()), "controlled capital connected")
	st.regions[cap]["controller"] = "cty_vardena"
	check(not supply.connected_to_capital(st, cap, st.player_id()), "captured capital cuts route")
	st.regions[cap]["controller"] = st.player_id()
	var f: Dictionary = st.formations_of(st.player_id())[0]
	f["ammo_reserve"] = 0.2
	var food: float = float(st.regions[cap]["stocks"]["food"])
	var ammo: float = float(st.regions[cap]["stocks"]["ammo"])
	supply.tick_day(st)
	check(float(st.regions[cap]["stocks"]["food"]) < food, "food consumed from stockpile")
	check(float(st.regions[cap]["stocks"]["ammo"]) < ammo and float(f["ammo_reserve"]) > 0.2, "ammo transferred from regional stock")
	f["region"] = "reg_24"
	f["supplies"] = 0.39
	f["last_supply_warning"] = -100
	var warnings := supply.tick_day(st)
	check(float(f["supplies"]) < 0.39, "isolated formation consumes reserves")
	check(not warnings.is_empty(), "warning before severe supply failure")
	var column: Dictionary = st.formations_of(st.player_id())[1]
	var source: String = column["region"]
	var destination: String = st.regions[source]["neighbors"][0]
	var fuel: float = float(st.regions[source]["stocks"]["fuel"])
	check(cmd.issue_move(st, column["id"], destination)["ok"], "vehicle movement ordered")
	cmd.tick_day(st, m.catalog)
	check(float(st.regions[source]["stocks"]["fuel"]) < fuel, "vehicle movement consumes regional fuel")
	check(not supply.build_depot(st, "reg_01", 100.0)["ok"], "cannot build depot in enemy region")
	var road := fresh(23, 200)
	road.regions["reg_10"]["controller"] = road.player_id()
	road.regions["reg_11"]["controller"] = road.player_id()
	check(supply.connected_to_capital(road, "reg_11", road.player_id()), "owned land route connects stockpiles")
	road.regions["reg_10"]["controller"] = "cty_vardena"
	check(not supply.connected_to_capital(road, "reg_11", road.player_id()), "intermediate hostile control interrupts route")
	var dry := fresh(24)
	var fueled := fresh(24)
	var dry_column: Dictionary = dry.formations_of(dry.player_id())[1]
	var fueled_column: Dictionary = fueled.formations_of(fueled.player_id())[1]
	dry.regions[dry_column["region"]]["stocks"]["fuel"] = 0.0
	var next: String = dry.regions[dry_column["region"]]["neighbors"][0]
	var dry_move := cmd.issue_move(dry, dry_column["id"], next)
	var fueled_move := cmd.issue_move(fueled, fueled_column["id"], next)
	cmd.tick_day(dry, m.catalog); cmd.tick_day(fueled, m.catalog)
	check(float(dry_move["order"]["progress"]) < float(fueled_move["order"]["progress"]), "fuel shortage slows motorized movement")
	var combat := Combat.new()
	var well := fresh(25)
	var weak: Dictionary = well.formations_of(well.player_id())[0]
	weak["ammo_reserve"] = 1.0; weak["supplies"] = 1.0
	var full_power := combat.power_of(well, weak, m.catalog)
	weak["ammo_reserve"] = 0.0; weak["supplies"] = 0.0
	check(combat.power_of(well, weak, m.catalog) < full_power * 0.3, "ammunition and supply shortages reduce combat power")


func test_combat() -> void:
	var st := fresh(33)
	var combat := Combat.new()
	var m := market()
	var a: Dictionary = st.formations_of(st.player_id())[0]
	var b: Dictionary = st.formations_of("cty_vardena")[0]
	a["units"][0]["count"] = 12
	b["units"][0]["count"] = 2
	b["region"] = a["region"]
	a["ammo_reserve"] = 0.8; b["ammo_reserve"] = 0.8
	var initial_ammo: float = a["ammo_reserve"]
	var result := combat.resolve_engagement(st, a, b, m.catalog, 4.0)
	var rep: Dictionary = result["report"]
	var lost := 0
	var total_people := 0
	for loss in rep["losses"].values():
		lost += int(loss["units_lost"])
		total_people += int(loss["killed"]) + int(loss["wounded"])
	check(lost > 0 and total_people == lost * 12, "casualties and wounded conserved")
	check(int(a.get("wounded", 0)) + int(b.get("wounded", 0)) > 0, "wounded persist in formations")
	check(int(st.regions[a["region"]]["salvage"].get("rif_surplus", 0)) == lost, "equipment salvage reflects actual losses")
	check(float(a["ammo_reserve"]) < initial_ammo and float(a["units"][0]["condition"]) < 0.85, "combat uses ammo and damages equipment")
	combat.post_battle(st, rep, m.catalog)
	var reports := st.reports.size()
	var stability: float = float(st.regions[a["region"]]["stability"])
	combat.post_battle(st, rep, m.catalog)
	check(st.reports.size() == reports and float(st.regions[a["region"]]["stability"]) == stability, "battle finalization is idempotent")
	var saver := Save.new()
	check(saver.save_campaign(st, 3, "battle-idempotence") == "", "battle consequences saved")
	var loaded: CampaignState = saver.load_campaign(3)["state"]
	var loaded_reports := loaded.reports.size()
	combat.post_battle(loaded, rep, m.catalog)
	check(loaded.reports.size() == loaded_reports and loaded.finalized_battles.has(rep["id"]), "battle consequences cannot repeat after load")
	var battle_region: String = a["region"]
	if not combat.hostile_pairs(st, battle_region).is_empty():
		check(not m.recover_salvage(st, st.player_id(), battle_region)["ok"], "salvage cannot be collected during active contact")
		for day in 30:
			var pairs := combat.hostile_pairs(st, battle_region)
			if pairs.is_empty():
				break
			if Command.new().active_order(b).is_empty():
				var next_battle := combat.resolve_engagement(st, a, b, m.catalog, 4.0)
				combat.post_battle(st, next_battle.get("report", {}), m.catalog)
			st.day += 1
			Command.new().tick_day(st, m.catalog)
	var salvage: int = int(st.regions[battle_region]["salvage"].get("rif_surplus", 0))
	var recover := m.recover_salvage(st, st.player_id(), battle_region)
	check(recover["ok"] and int(recover["recovered"]) == salvage, "battlefield salvage recovered as damaged")
	var damaged: Dictionary = st.countries[st.player_id()]["damaged_inventory"]
	var before: int = int(st.inventory["rif_surplus"])
	var money := st.treasury
	var repair := m.repair_recovered(st, st.player_id(), battle_region, "rif_surplus", 1)
	check(repair["ok"] and int(damaged["rif_surplus"]) == salvage - 1 and int(st.inventory["rif_surplus"]) == before + 1 and st.treasury < money, "salvage repair consumes funds and restores inventory")
	check(not m.recover_salvage(st, st.player_id(), a["region"])["ok"], "salvage cannot be recovered twice")
	var protected := fresh(34)
	var unprotected := fresh(34)
	var pf: Dictionary = protected.formations_of(protected.player_id())[0]
	var uf: Dictionary = unprotected.formations_of(unprotected.player_id())[0]
	pf["units"][0]["count"] = 100; uf["units"][0]["count"] = 100
	pf["attachments"] = {"kit_protect": 3}
	var p_loss := combat._apply_losses(protected, pf, 0.2)
	var u_loss := combat._apply_losses(unprotected, uf, 0.2)
	check(int(p_loss["units_lost"]) < int(u_loss["units_lost"]), "protective gear reduces casualties")


func test_ai() -> void:
	var st := fresh(55)
	var ai := AI.new()
	var m := market()
	for cid in st.countries:
		if cid != st.player_id():
			st.countries[cid]["treasury"] = 0.0
			st.countries[cid]["inventory"] = {}
	var count := st.formations.size()
	var pool: int = int(st.countries["cty_vardena"]["manpower_pool"])
	ai.tick_week(st, m.catalog)
	check(st.formations.size() == count and int(st.countries["cty_vardena"]["manpower_pool"]) == pool, "AI cannot recruit for free")
	check(st.market_orders.is_empty() and float(st.countries["cty_vardena"]["treasury"]) == 0.0, "AI cannot buy with zero budget")
	var funded := fresh(56)
	funded.countries["cty_vardena"]["treasury"] = 5000.0
	funded.countries["cty_vardena"]["inventory"] = {"rif_surplus": 4}
	var pool_before: int = int(funded.countries["cty_vardena"]["manpower_pool"])
	ai._decide(funded, "cty_vardena", m.catalog)
	check(float(funded.countries["cty_vardena"]["treasury"]) < 5000.0, "funded AI pays for recruitment")
	check(int(funded.countries["cty_vardena"]["manpower_pool"]) < pool_before, "funded AI spends manpower")
	check(int(funded.countries["cty_vardena"]["inventory"]["rif_surplus"]) < 4, "AI issues real inventory")
	var gov_cap: String = funded.countries["cty_vardena"]["capital"]
	var trained := false
	for f in funded.formations_in(gov_cap):
		if f["country"] == "cty_vardena" and funded.formation_power(f, m.catalog) > 0.0:
			trained = true
	check(trained, "AI forms staffed equipped squads")
	var economy := Economy.new()
	var wage_due := economy.personnel_upkeep(funded, "cty_vardena")
	var ai_balance := funded.balance("cty_vardena")
	economy.tick_day(funded, m.catalog)
	check(wage_due > 0 and funded.balance("cty_vardena") <= ai_balance - wage_due, "AI pays recurring personnel costs under same rules")
	funded.treasury = -1000.0
	funded.countries["cty_vardena"]["treasury"] = -1000.0
	economy.tick_month(funded)
	check(is_equal_approx(funded.treasury, -1010.0) and is_equal_approx(funded.balance("cty_vardena"), -1010.0), "debt interest applies equally to player and AI")
	var local := fresh(57)
	for f in local.formations_of(local.player_id()):
		f["region"] = "reg_24"
	var seen := ai.observed_strength(local, "cty_vardena", "reg_02")
	local.formations_of(local.player_id())[0]["units"][0]["count"] = 100
	check(ai.observed_strength(local, "cty_vardena", "reg_02") == seen, "AI observation ignores distant hidden strength")
	var limited := fresh(60, 200)
	for r in limited.regions.values():
		r["controller"] = "cty_vardena"
	limited.regions["reg_01"]["controller"] = limited.player_id()
	for formation in limited.formations_of(limited.player_id()):
		formation["region"] = "reg_01"
	var distant: Dictionary = limited.formations_of("cty_vardena")[0]
	distant["region"] = "reg_03"
	var initial_seen := ai.observed_strength(limited, limited.player_id(), "reg_02")
	distant["units"][0]["count"] = 100
	check(not limited.can_observe(limited.player_id(), "reg_03") and ai.observed_strength(limited, limited.player_id(), "reg_02") == initial_seen, "AI cannot peek two districts beyond its border")
	var attacking := fresh(58)
	var gov: Dictionary = attacking.formations_of("cty_vardena")[0]
	gov["region"] = "reg_10"
	gov["units"][0]["count"] = 20
	ai._decide(attacking, "cty_vardena", m.catalog)
	var attack_order := Command.new().active_order(gov)
	check(not attack_order.is_empty() and attack_order["target_region"] == "reg_09", "AI contests neighboring hostile territory when stronger")
	var defending := fresh(59)
	var guard: Dictionary = defending.formations_of("cty_vardena")[0]
	defending.formations_of(defending.player_id())[0]["region"] = "reg_14"
	defending.regions["reg_01"]["strategic_value"] = 100.0
	ai._decide(defending, "cty_vardena", m.catalog)
	var defend_order := Command.new().active_order(guard)
	check(not defend_order.is_empty() and defend_order["target_region"] == "reg_01", "AI reinforces threatened high-value region")


func test_politics() -> void:
	var st := fresh(66)
	var dip := Diplomacy.new()
	var admin := Admin.new(); admin.init(null)
	var w := dip.declare_war(st, st.player_id(), "cty_vardena", "test")
	check(w["ok"] and st.is_hostile(st.player_id(), "cty_vardena"), "war creates hostility")
	check(not dip.declare_war(st, st.player_id(), "cty_vardena", "duplicate")["ok"], "duplicate war rejected")
	var accepted := false
	for i in 30:
		var proposal := dip.propose_ceasefire(st, w["war"])
		if proposal.get("accepted", false):
			accepted = true
			break
		st.day += 7
	check(accepted and not st.is_hostile(st.player_id(), "cty_vardena"), "ceasefire suspends hostilities")
	check(not st.treaties.is_empty(), "ceasefire is a persisted treaty")
	check(not dip.negotiate_transition(st)["ok"], "insufficient political support or territory blocks settlement")
	for rid in ["reg_01", "reg_02"]:
		Admin.capture(st, rid, st.player_id())
	for r in st.regions.values():
		if r["country"] == "cty_vardena" and r["controller"] == st.player_id():
			r["political_support"] = 0.7
			r["stability"] = 0.7
			r["legitimacy"] = 0.7
	for r in st.regions.values():
		if r["country"] == "cty_vardena" and r["controller"] == st.player_id():
			r["legitimacy"] = 0.1
	check(not dip.negotiate_transition(st)["ok"], "low legitimacy blocks transition")
	for r in st.regions.values():
		if r["country"] == "cty_vardena" and r["controller"] == st.player_id():
			r["legitimacy"] = 0.7
	check(dip.negotiate_transition(st)["ok"] and st.outcome == "negotiated_transition", "eligible ceasefire leads to negotiated transition")
	var expiration := fresh(67)
	var war := dip.declare_war(expiration, expiration.player_id(), "cty_vardena", "test")
	for i in 30:
		if dip.propose_ceasefire(expiration, war["war"]).get("accepted", false):
			break
		expiration.day += 7
	expiration.day += 30
	dip.tick_day(expiration)
	check(expiration.wars[war["war"]]["status"] == "active" and expiration.is_hostile(expiration.player_id(), "cty_vardena"), "expired ceasefire resumes conflict")
	var defeated := fresh(68)
	for fid in defeated.formations.keys():
		if defeated.formations[fid]["country"] == defeated.player_id():
			defeated.formations.erase(fid)
	for r in defeated.regions.values():
		if r["controller"] == defeated.player_id():
			r["controller"] = "cty_vardena"
	check(admin.evaluate_outcome(defeated) == "defeat", "loss of all people and territory defeats campaign")
	var stranded := fresh(69)
	for f in stranded.formations_of(stranded.player_id()):
		for unit in f["units"]:
			unit["count"] = 0
		f["wounded"] = 5
		f["personnel_reserve"] = 12
	for r in stranded.regions.values():
		if r["controller"] == stranded.player_id():
			r["controller"] = "cty_vardena"
	check(admin.evaluate_outcome(stranded) == "defeat", "stranded unarmed reserves without territory cannot softlock campaign")


func test_persistence() -> void:
	var st := fresh(77)
	var m := market()
	var cmd := Command.new()
	var saver := Save.new()
	var f: Dictionary = st.formations_of(st.player_id())[0]
	var move := cmd.issue_move(st, f["id"], "reg_10")
	cmd.tick_day(st, m.catalog)
	f["wounded"] = 3
	var purchase := m.purchase(st, "rif_basic", 1)
	check(move["ok"] and purchase["ok"], "active campaign prepared")
	var bal := st.treasury
	var progress: float = float(move["order"]["progress"])
	check(saver.save_campaign(st, 5, "stage2") == "", "active campaign saved")
	var loaded := saver.load_campaign(5)
	check(loaded["error"] == "", "active campaign loaded")
	var copy: CampaignState = loaded["state"]
	check(copy.treasury == bal and int(copy.formations[f["id"]]["wounded"]) == 3, "funds and wounded restored")
	check(absf(float(copy.formations[f["id"]]["orders"][0]["progress"]) - progress) < 0.0001, "active movement progress restored")
	check(copy.market_orders[purchase["order"]["id"]]["status"] == "in_transit", "in-transit purchase restored")
	var stream_matches := true
	for i in 20:
		if st.randf() != copy.randf():
			stream_matches = false
	check(stream_matches, "64-bit RNG stream exactly resumes")
	copy.day = int(purchase["order"]["eta_day"])
	var before: int = int(copy.inventory["rif_basic"])
	m.tick_day(copy); m.tick_day(copy)
	check(int(copy.inventory["rif_basic"]) == before + 1 and copy.treasury == bal, "loaded delivery and payment occur once")
	check(saver.save_campaign(copy, 5, "delivered") == "", "delivered state saved")
	var second: CampaignState = saver.load_campaign(5)["state"]
	var after: int = int(second.inventory["rif_basic"])
	m.tick_day(second)
	check(int(second.inventory["rif_basic"]) == after and second.treasury == bal, "delivered order remains idempotent after reload")
	var diplomatic := fresh(79)
	var foreign := m.purchase(diplomatic, "rif_improved", 1)
	diplomatic.day = int(foreign["order"]["eta_day"])
	m.tick_day(diplomatic)
	var warmth: float = float(diplomatic.rel(diplomatic.player_id(), "cty_meridia")["warmth"])
	var report_count := diplomatic.reports.size()
	saver.save_campaign(diplomatic, 5, "delivered diplomatic")
	var diplomatic_reload: CampaignState = saver.load_campaign(5)["state"]
	m.tick_day(diplomatic_reload)
	check(float(diplomatic_reload.rel(diplomatic_reload.player_id(), "cty_meridia")["warmth"]) == warmth and diplomatic_reload.reports.size() == report_count, "delivery diplomacy and event do not repeat after load")
	var old := st.serialize().duplicate(true)
	old["schema_version"] = 1
	old["rng_state"] = old["seed"]
	old.erase("treaties"); old.erase("finalized_battles"); old.erase("contact_notices")
	for r in old["regions"].values():
		for key in ["sea_neighbors", "political_support", "productivity", "infra_condition", "security_pressure", "opposition", "supply_accessibility", "recovery_progress", "admin_focus", "salvage", "is_city", "strategic_value"]:
			r.erase(key)
	for c in old["countries"].values():
		c.erase("treasury"); c.erase("inventory"); c.erase("damaged_inventory")
	for formation in old["formations"].values():
		formation.erase("attachments"); formation.erase("wounded"); formation.erase("dead")
	var migrated := CampaignState.new()
	check(migrated.deserialize(old) == "" and migrated.schema_version == 2 and migrated.regions["reg_09"].has("opposition"), "version 1 save migrates with regional defaults")
	check(str(migrated.history[-1]["text"]).contains("random stream restarted"), "v1 RNG migration limitation recorded")
	var legacy_file := FileAccess.open(saver.slot_path(5), FileAccess.WRITE)
	legacy_file.store_string(JSON.stringify({"meta": {"schema_version": 1}, "state": old}))
	legacy_file.close()
	var legacy := saver.load_campaign(5)
	check(legacy["error"] == "" and legacy["state"].schema_version == 2 and legacy["state"].countries["cty_vardena"].has("treasury"), "actual legacy JSON file loads through migration")
