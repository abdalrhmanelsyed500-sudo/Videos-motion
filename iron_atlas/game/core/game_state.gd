extends Node
const CampaignState = preload("res://core/campaign_state.gd")
const EconomySystem = preload("res://economy/economy_system.gd")
const MarketSystem = preload("res://economy/market_system.gd")
const CommandSystem = preload("res://military/command_system.gd")
const CombatSystem = preload("res://military/combat_system.gd")
const SupplySystem = preload("res://logistics/supply_system.gd")
const DiplomacySystem = preload("res://diplomacy/diplomacy_system.gd")
const FactionAI = preload("res://ai/faction_ai.gd")
const WorldGenerator = preload("res://world/world_generator.gd")
## GameState autoload: owns the live CampaignState and the system instances,
## wires CampaignClock ticks to systems. UI and tests call methods here.

var cs: CampaignState = null
var economy := EconomySystem.new()
var market := MarketSystem.new()
var command := CommandSystem.new()
var combat := CombatSystem.new()
var supply := SupplySystem.new()
var diplomacy := DiplomacySystem.new()
var ai := FactionAI.new()

const SCENARIO_PATH := "res://data/scenario_vardena.json"


func _ready() -> void:
	economy.init(null); market.init(null); command.init(null); combat.init(null)
	supply.init(null); diplomacy.init(null); ai.init(null)
	EventBus.day_passed.connect(_on_day)
	EventBus.week_passed.connect(_on_week)
	EventBus.month_passed.connect(_on_month)


func load_scenario() -> Dictionary:
	var f := FileAccess.open(SCENARIO_PATH, FileAccess.READ)
	if f == null:
		return {"treasury": 12000, "title": "Vardena crisis (fallback)"}
	var parsed = JSON.parse_string(f.get_as_text())
	f.close()
	return parsed if typeof(parsed) == TYPE_DICTIONARY else {}


func new_campaign(seed_int: int) -> String:
	var sc := load_scenario()
	cs = WorldGenerator.generate(seed_int, sc)
	CampaignClock.set_speed(0)
	EventBus.notification.emit("Campaign started (seed %d)" % seed_int, 0)
	return ""


func adopt_state(st: CampaignState) -> void:
	cs = st
	CampaignClock.set_speed(0)
	EventBus.notification.emit("Campaign loaded (day %d)" % st.day, 0)


func _on_day(_d: int) -> void:
	if cs == null:
		return
	var equip := market.catalog
	command.tick_day(cs, equip)
	var warns := supply.tick_day(cs)
	for w in warns:
		EventBus.notification.emit(w, 1)
	economy.tick_day(cs, equip)
	market.tick_day(cs)
	# engagements
	for rid in cs.regions:
		var pairs := combat.hostile_pairs(cs, rid)
		for p in pairs:
			var res := combat.resolve_engagement(cs, p[0], p[1], equip, 1.0)
			combat.post_battle(cs, res["report"], equip)


func _on_week(_w: int) -> void:
	if cs == null:
		return
	supply.tick_week(cs)
	economy.tick_week(cs)
	market.catalog = market.catalog  # keep reference stable
	ai.tick_week(cs, market.catalog)
	diplomacy.tick_week(cs)


func _on_month(_m: int) -> void:
	if cs == null:
		return
	economy.tick_month(cs)
