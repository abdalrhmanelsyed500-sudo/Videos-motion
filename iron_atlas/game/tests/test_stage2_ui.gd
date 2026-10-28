extends SceneTree
## 200-region interface actions are wired to actual simulation operations.
var checks := 0
var failures: Array = []
var frame := 0
var GS = null
var wm = null
var setup = null


func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures.append(label)


func _initialize() -> void:
	GS = root.get_node("GameState")
	check(GS.new_campaign(42424, 200) == "", "200-region campaign starts")
	setup = load("res://scenes/campaign_setup.tscn").instantiate()
	root.add_child(setup)


func _process(_delta: float) -> void:
	frame += 1
	if frame == 2:
		check(setup.is_node_ready() and setup.world_size.get_selected_id() == 200, "new game defaults to 200 regions")
		setup.queue_free()
		wm = load("res://scenes/world_map.tscn").instantiate()
		root.add_child(wm)
	if frame == 5:
		check(wm.is_node_ready() and wm.panels.has("Politics"), "stage 2 panels built")
		wm.selected_region = "reg_09"
		wm._refresh_all()
		check(str(wm.insp["controller"].text).contains("Free Vardena"), "inspector shows actual controller")
		check(str(wm.insp["security"].text).contains("Supply route"), "inspector exposes supply and security")
		wm.selected_region = "reg_200"
		wm._refresh_all()
		check(str(wm.insp["stocks"].text).contains("unknown"), "remote stockpiles are not exposed without intelligence")
		wm.selected_region = "reg_09"
		wm._refresh_all()
		check(wm._region_at(wm._pos(GS.cs.regions["reg_09"])) == "reg_09", "200-region hit testing")
		var event := InputEventMouseButton.new()
		event.button_index = MOUSE_BUTTON_WHEEL_UP
		event.pressed = true
		event.position = wm._pos(GS.cs.regions["reg_09"])
		wm._gui_input(event)
		check(wm.map_zoom > 1.0 and wm._region_at(event.position) == "reg_09", "zoom preserves map target")
		var f: Dictionary = GS.cs.formations_of(GS.cs.player_id())[0]
		wm.selected_formation = f["id"]
		var before_cash: float = GS.cs.treasury
		wm._on_recruit()
		check(int(f["personnel_reserve"]) >= 12 and GS.cs.treasury < before_cash, "UI recruitment changes state")
		wm._show_panel("Market")
		var list: ItemList = wm.panels["Market"].get_node("MarketList")
		var index := -1
		for i in list.item_count:
			if list.get_item_metadata(i) == "rif_surplus":
				index = i
				break
		check(index >= 0, "equipment catalogue rendered")
		if index < 0:
			print("TESTS: FAIL missing equipment metadata: %d checks" % checks)
			quit(1)
			return
		wm._on_market_selected(index)
		var stock_before: int = int(GS.cs.inventory["rif_surplus"])
		wm._on_issue_selected()
		check(int(GS.cs.inventory["rif_surplus"]) == stock_before - 1, "UI equips selected purchased inventory")
		before_cash = GS.cs.treasury
		wm._on_buy()
		wm._on_confirm_purchase()
		check(GS.cs.treasury < before_cash and GS.cs.market_orders.size() == 1, "UI purchase creates paid order")
		before_cash = GS.cs.treasury
		var pressure: float = float(GS.cs.regions["reg_09"]["security_pressure"])
		wm._on_invest("security")
		check(GS.cs.treasury < before_cash and float(GS.cs.regions["reg_09"]["security_pressure"]) < pressure, "administration button has real effects")
		wm._on_declare()
		check(not GS.cs.wars.is_empty(), "politics action declares real war")
		var reports_before: int = GS.cs.reports.size()
		wm._on_ceasefire()
		check(GS.cs.reports.size() > reports_before, "ceasefire reports its reason/result")
		check(str(wm.top["message"].text) != "", "feedback visible in status bar")
		GS.cs.add_report("military", "Hidden rival logistics", "private", "cty_vardena")
		GS.cs.add_report("military", "Own logistics", "visible detail", GS.cs.player_id())
		wm._refresh_reports()
		var reports: ItemList = wm.panels["Reports"].get_node("ReportList")
		var hidden_found := false
		var own_index := -1
		for i in reports.item_count:
			if reports.get_item_text(i).contains("Hidden rival logistics"):
				hidden_found = true
			if reports.get_item_text(i).contains("Own logistics"):
				own_index = i
		check(not hidden_found and own_index >= 0, "private rival reports are filtered")
		if own_index >= 0:
			wm._on_report_selected(own_index)
			check(wm.panels["Reports"].get_node("ReportDetail").text == "visible detail", "filtered report selection shows correct detail")
		print("TESTS: %s: %d checks" % ["PASS" if failures.is_empty() else "FAIL " + "; ".join(failures), checks])
		quit(0 if failures.is_empty() else 1)
