extends Node
const CampaignState = preload("res://core/campaign_state.gd")
const EconomySystem = preload("res://economy/economy_system.gd")
const MarketSystem = preload("res://economy/market_system.gd")
const CommandSystem = preload("res://military/command_system.gd")
const CombatSystem = preload("res://military/combat_system.gd")
const SupplySystem = preload("res://logistics/supply_system.gd")
const DiplomacySystem = preload("res://diplomacy/diplomacy_system.gd")
const FactionAI = preload("res://ai/faction_ai.gd")
const AdministrationSystem = preload("res://administration/administration_system.gd")
const WorldGenerator = preload("res://world/world_generator.gd")
## Autoload owns the campaign and orchestrates ticks; systems remain independent.

var cs: CampaignState = null
var economy := EconomySystem.new()
var market := MarketSystem.new()
var command := CommandSystem.new()
var combat := CombatSystem.new()
var supply := SupplySystem.new()
var diplomacy := DiplomacySystem.new()
var ai := FactionAI.new()
var administration := AdministrationSystem.new()
var tactical_region: String = ""

const SCENARIO_PATH := "res://data/scenario_vardena.json"


func _ready() -> void:
	economy.init(null); market.init(null); command.init(null); combat.init(null)
	supply.init(null); diplomacy.init(null); ai.init(null); administration.init(null)
	EventBus.day_passed.connect(_on_day)
	EventBus.week_passed.connect(_on_week)
	EventBus.month_passed.connect(_on_month)


func load_scenario() -> Dictionary:
	var f := FileAccess.open(SCENARIO_PATH, FileAccess.READ)
	if f == null:
		return {}
	var parsed = JSON.parse_string(f.get_as_text())
	f.close()
	return parsed if typeof(parsed) == TYPE_DICTIONARY else {}


func new_campaign(seed_int: int, region_count: int = 24) -> String:
	var sc := load_scenario()
	if sc.is_empty() or not sc.has("start_formations"):
		return "Scenario data missing or invalid"
	sc["region_count"] = region_count
	var generated := WorldGenerator.generate(seed_int, sc)
	var errors := WorldGenerator.validate_world(generated)
	if not errors.is_empty():
		return "World validation failed: " + "; ".join(errors)
	cs = generated
	supply.refresh_networks(cs)
	tactical_region = ""
	CampaignClock.reset()
	EventBus.notification.emit("Campaign started (seed %d, %d regions)" % [seed_int, cs.regions.size()], 0)
	return ""


func adopt_state(st: CampaignState) -> void:
	cs = st
	tactical_region = ""
	CampaignClock.reset()
	EventBus.notification.emit("Campaign loaded (day %d)" % st.day, 0)


func _on_day(_d: int) -> void:
	if cs == null or cs.outcome != "":
		return
	var equip := market.catalog
	command.tick_day(cs, equip)
	var warns := supply.tick_day(cs)
	for w in warns:
		EventBus.notification.emit(w, 1)
	economy.tick_day(cs, equip)
	market.tick_day(cs)
	diplomacy.tick_day(cs)
	# Only occupied regions need combat checks; avoid scanning every empty region.
	var occupied := {}
	for f in cs.formations.values():
		occupied[f["region"]] = true
	var current_notices := {}
	for rid in occupied:
		var pairs := combat.hostile_pairs(cs, rid)
		for p in pairs:
			if not cs.formations.has(p[0]["id"]) or not cs.formations.has(p[1]["id"]):
				continue
			if cs.player_id() in [p[0]["country"], p[1]["country"]]:
				var key: String = rid + ":" + cs.pair_key(p[0]["country"], p[1]["country"])
				current_notices[key] = true
				if not cs.contact_notices.has(key):
					cs.contact_notices[key] = true
					cs.add_report("battle", "Hostile contact: " + cs.regions[rid]["name"],
						"Clock paused. Select the formation and open tactical battle or resolve the contact.")
					EventBus.notification.emit("Contact in %s: choose tactical battle or resolve." % cs.regions[rid]["name"], 2)
					CampaignClock.set_speed(0)
			else:
				var result := combat.resolve_engagement(cs, p[0], p[1], equip)
				combat.post_battle(cs, result.get("report", {}), equip)
	for key in cs.contact_notices.keys():
		if not current_notices.has(key):
			cs.contact_notices.erase(key)
	if administration.evaluate_outcome(cs) != "":
		CampaignClock.set_speed(0)


func resolve_player_contact(rid: String) -> Dictionary:
	if cs == null or not cs.regions.has(rid):
		return {"ok": false, "error": "select a contact region"}
	for p in combat.hostile_pairs(cs, rid):
		if cs.player_id() in [p[0]["country"], p[1]["country"]]:
			var result := combat.resolve_engagement(cs, p[0], p[1], market.catalog)
			if result.get("report", {}).is_empty():
				return {"ok": false, "error": "unable to resolve contact"}
			combat.post_battle(cs, result["report"], market.catalog)
			return {"ok": true, "report": result["report"]}
	return {"ok": false, "error": "no hostile contact here"}


func _on_week(_w: int) -> void:
	if cs == null or cs.outcome != "":
		return
	supply.tick_week(cs)
	economy.tick_week(cs)
	administration.tick_week(cs)
	diplomacy.tick_week(cs)
	ai.tick_week(cs, market.catalog)
	if administration.evaluate_outcome(cs) != "":
		CampaignClock.set_speed(0)


func _on_month(_m: int) -> void:
	if cs == null or cs.outcome != "":
		return
	economy.tick_month(cs)
