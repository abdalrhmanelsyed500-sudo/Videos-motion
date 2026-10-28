extends SceneTree
## Scene flow test (frame-phased, fixed-fps): menu -> campaign -> world map UI
## -> recruit/market/move -> clock advance -> save/load. Autoloads fetched at
## runtime; UI touched only after the scene's _ready has run.

var checks := 0
var failures: Array = []
var frames := 0
var phase := 0
var GS = null
var CLK = null
var SM = null
var wm = null


func ok(cond: bool, label: String) -> void:
	checks += 1
	if not cond:
		failures.append(label)


func _initialize() -> void:
	GS = root.get_node("GameState")
	CLK = root.get_node("CampaignClock")
	SM = root.get_node("SaveManager")
	var menu = load("res://scenes/main_menu.tscn").instantiate()
	root.add_child(menu)
	menu.queue_free()
	GS.new_campaign(777)
	ok(GS.cs != null and GS.cs.regions.size() == 24, "campaign created")


func _process(_delta: float) -> void:
	frames += 1
	if frames == 2 and phase == 0:
		phase = 1
		wm = load("res://scenes/world_map.tscn").instantiate()
		root.add_child(wm)
	elif frames == 5 and phase == 1:
		phase = 2
		ok(wm.get_child_count() >= 3, "world map ui built")
		ok(wm.is_node_ready(), "world map ready")
		wm.selected_region = "reg_09"
		wm._refresh_all()
		var before_recruits: int = GS.cs.formations_of(GS.cs.player_id())[0].get("personnel_reserve", 0)
		var before_treasury: float = GS.cs.treasury
		wm._on_recruit()
		ok(int(GS.cs.formations_of(GS.cs.player_id())[0].get("personnel_reserve", 0)) > before_recruits and GS.cs.treasury < before_treasury, "recruit changes personnel and treasury")
		wm._show_panel("Market")
		var list: ItemList = wm.panels["Market"].get_node("MarketList")
		ok(list.item_count >= 10, "market list populated")
		var t1: float = GS.cs.treasury
		var res = GS.market.purchase(GS.cs, "rif_basic", 2)
		ok(res["ok"] and GS.cs.treasury < t1, "purchase debits treasury")
		var fid: String = GS.cs.formations_of(GS.cs.player_id())[0]["id"]
		var from_r: String = GS.cs.formations[fid]["region"]
		var mv = GS.command.issue_move(GS.cs, fid, GS.cs.regions[from_r]["neighbors"][0])
		ok(mv["ok"], "move order issued from UI layer")
		CLK.advance_days(25, GS.cs)
		ok(GS.cs.day >= 25, "clock advanced")
		ok(GS.cs.formations[fid]["region"] != from_r or not GS.cs.formations.has(fid),
			"formation moved or resolved")
		var err: String = SM.save_slot(2, "ui-flow")
		ok(err == "", "save slot 2")
		var ld: String = SM.load_slot(2)
		ok(ld == "", "load slot 2")
		ok(GS.cs.day >= 25, "loaded day preserved")
		wm.queue_free()
		print("TESTS: %s: %d checks" % [
			"PASS" if failures.is_empty() else "FAIL " + "; ".join(failures), checks])
		quit(0 if failures.is_empty() else 1)
