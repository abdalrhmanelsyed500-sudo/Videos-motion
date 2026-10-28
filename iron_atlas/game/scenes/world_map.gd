extends Control
## Strategic map: draws region graph from CampaignState (owner fills, borders,
## selection, contested hatch), right dock with inspector + tab panels
## (Military / Market / Reports / Logistics), top bar with clock & treasury.
## All interaction goes through validated system calls.

const MAP_SCALE := Vector2(10.4, 11.6)
const MAP_OFF := Vector2(40, 60)

var selected_region: String = ""
var selected_formation: String = ""
var order_targeting: bool = false
var panels: Dictionary = {}
var insp: Dictionary = {}
var top: Dictionary = {}
var market_rows: Array = []
var confirm_dialog: AcceptDialog
var pending_quote: Dictionary = {}


func _ready() -> void:
	if GameState.cs == null:
		GameState.new_campaign(1234)
	_build_topbar()
	_build_dock()
	_refresh_all()


func _build_topbar() -> void:
	var bar := HBoxContainer.new()
	bar.position = Vector2(8, 6)
	bar.size = Vector2(900, 30)
	add_child(bar)
	top["date"] = Label.new(); bar.add_child(top["date"])
	top["treasury"] = Label.new(); bar.add_child(top["treasury"])
	top["stability"] = Label.new(); bar.add_child(top["stability"])
	top["speed"] = Label.new(); bar.add_child(top["speed"])
	for i in range(5):
		var b := Button.new()
		b.text = CampaignClock.SPEED_NAMES[i]
		b.pressed.connect(_on_speed.bind(i))
		bar.add_child(b)
	var save_b := Button.new()
	save_b.text = "Save"
	save_b.pressed.connect(_on_save)
	bar.add_child(save_b)
	var menu_b := Button.new()
	menu_b.text = "Menu"
	menu_b.pressed.connect(func(): get_tree().change_scene_to_file("res://scenes/main_menu.tscn"))
	bar.add_child(menu_b)


func _build_dock() -> void:
	var dock := VBoxContainer.new()
	dock.position = Vector2(950, 40)
	dock.size = Vector2(320, 660)
	add_child(dock)
	var tabs := HBoxContainer.new()
	dock.add_child(tabs)
	for key in ["Inspector", "Military", "Market", "Reports"]:
		var b := Button.new()
		b.text = key
		b.pressed.connect(_show_panel.bind(key))
		tabs.add_child(b)
	for key in ["Inspector", "Military", "Market", "Reports"]:
		var sc := ScrollContainer.new()
		sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
		var box := VBoxContainer.new()
		box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		sc.add_child(box)
		dock.add_child(sc)
		panels[key] = box
	_build_inspector()
	_build_military()
	_build_market()
	_build_reports()
	_show_panel("Inspector")
	confirm_dialog = AcceptDialog.new()
	add_child(confirm_dialog)
	confirm_dialog.confirmed.connect(_on_confirm_purchase)


func _build_inspector() -> void:
	var box: VBoxContainer = panels["Inspector"]
	for key in ["name", "controller", "pop", "terrain", "stability", "support",
			"economy", "infra", "stocks", "depot", "neighbors", "events"]:
		insp[key] = Label.new()
		insp[key].autowrap_mode = TextServer.AUTOWRAP_WORD
		box.add_child(insp[key])
	var recruit := Button.new()
	recruit.text = "Recruit here (500cr)"
	recruit.pressed.connect(_on_recruit)
	box.add_child(recruit)
	var depot := Button.new()
	depot.text = "Build/upgrade depot (2500cr)"
	depot.pressed.connect(_on_depot)
	box.add_child(depot)


func _build_military() -> void:
	var box: VBoxContainer = panels["Military"]
	var list := ItemList.new()
	list.name = "FormationList"
	list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	list.item_selected.connect(_on_formation_selected)
	box.add_child(list)
	var info := Label.new()
	info.name = "FormationInfo"
	info.autowrap_mode = TextServer.AUTOWRAP_WORD
	box.add_child(info)
	var row := HBoxContainer.new()
	box.add_child(row)
	var mv := Button.new()
	mv.text = "Move (pick target)"
	mv.pressed.connect(_on_move_mode)
	row.add_child(mv)
	var hold := Button.new()
	hold.text = "Hold"
	hold.pressed.connect(_on_hold)
	row.add_child(hold)
	var retreat := Button.new()
	retreat.text = "Retreat"
	retreat.pressed.connect(_on_retreat)
	row.add_child(retreat)
	var equip := Button.new()
	equip.text = "Issue rifles x10"
	equip.pressed.connect(_on_issue_rifles)
	box.add_child(equip)
	var engage := Button.new()
	engage.text = "Open tactical battle"
	engage.pressed.connect(_on_engage)
	box.add_child(engage)


func _build_market() -> void:
	var box: VBoxContainer = panels["Market"]
	var list := ItemList.new()
	list.name = "MarketList"
	list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	list.item_selected.connect(_on_market_selected)
	box.add_child(list)
	var info := Label.new()
	info.name = "MarketInfo"
	info.autowrap_mode = TextServer.AUTOWRAP_WORD
	box.add_child(info)
	var buy := Button.new()
	buy.text = "Buy x1 (confirm)"
	buy.pressed.connect(_on_buy)
	box.add_child(buy)
	var orders := Label.new()
	orders.name = "OrdersLabel"
	orders.autowrap_mode = TextServer.AUTOWRAP_WORD
	box.add_child(orders)


func _build_reports() -> void:
	var box: VBoxContainer = panels["Reports"]
	var list := ItemList.new()
	list.name = "ReportList"
	list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	list.item_selected.connect(_on_report_selected)
	box.add_child(list)
	var detail := TextEdit.new()
	detail.name = "ReportDetail"
	detail.editable = false
	detail.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_child(detail)


func _show_panel(key: String) -> void:
	for k in panels:
		(panels[k].get_parent() as Control).visible = (k == key)
	_refresh_all()


# ---------------------------------------------------------------- input/draw
func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
		var rid := _region_at(ev.position)
		if rid != "":
			if order_targeting and selected_formation != "":
				var res := GameState.command.issue_move(GameState.cs, selected_formation, rid)
				order_targeting = false
				if not res["ok"]:
					EventBus.notification.emit(res["error"], 2)
				_refresh_all()
			else:
				selected_region = rid
				_refresh_all()


func _region_at(p: Vector2) -> String:
	for rid in GameState.cs.regions:
		var rp: Array = GameState.cs.regions[rid]["pos"]
		var c := Vector2(rp[0], rp[1]) * MAP_SCALE + MAP_OFF
		if (p - c).length() < 16:
			return rid
	return ""


func _draw() -> void:
	var st := GameState.cs
	if st == null:
		return
	draw_rect(Rect2(0, 0, size.x, size.y), Color(0.10, 0.12, 0.14))
	for rid in st.regions:
		var r: Dictionary = st.regions[rid]
		for nb in r["neighbors"]:
			if rid < nb:
				draw_line(_pos(r), _pos(st.regions[nb]), Color(0.35, 0.35, 0.38), 1.0)
	for rid in st.regions:
		var r: Dictionary = st.regions[rid]
		var col: Color = Color(st.countries[r["controller"]]["color"][0],
			st.countries[r["controller"]]["color"][1], st.countries[r["controller"]]["color"][2])
		var contested := _is_contested(rid)
		draw_circle(_pos(r), 13.0, col.darkened(0.25 if contested else 0.0))
		if contested:
			draw_circle(_pos(r), 7.0, Color(0.9, 0.3, 0.2))
		draw_arc(_pos(r), 14.0, 0, TAU, 20, Color(0.1, 0.1, 0.1), 1.0)
		if rid == selected_region:
			draw_arc(_pos(r), 18.0, 0, TAU, 24, Color(1, 1, 1), 2.0)
		if not OS.has_feature("web"):
			draw_string(ThemeDB.fallback_font, _pos(r) + Vector2(-30, 30), r["name"],
				HORIZONTAL_ALIGNMENT_LEFT, 80, 10, Color(0.85, 0.85, 0.85))
	for fid in st.formations:
		var f: Dictionary = st.formations[fid]
		var fp := _pos(st.regions[f["region"]]) + Vector2(0, -20)
		var col: Color = Color(st.countries[f["country"]]["color"][0],
			st.countries[f["country"]]["color"][1], st.countries[f["country"]]["color"][2])
		draw_rect(Rect2(fp - Vector2(5, 3), Vector2(10, 6)), col.lightened(0.3))
		if fid == selected_formation:
			draw_rect(Rect2(fp - Vector2(7, 5), Vector2(14, 10)), Color(1, 1, 1), false, 1.5)


func _pos(r: Dictionary) -> Vector2:
	return Vector2(r["pos"][0], r["pos"][1]) * MAP_SCALE + MAP_OFF


func _is_contested(rid: String) -> bool:
	var owners := {}
	for f in GameState.cs.formations_in(rid):
		owners[f["country"]] = true
	return owners.size() > 1


# ---------------------------------------------------------------- refresh
func _refresh_all() -> void:
	var st := GameState.cs
	if st == null:
		return
	top["date"].text = "Day %d  " % st.day
	top["treasury"].text = "Treasury %.0f  " % st.treasury
	top["stability"].text = "Stability %.2f  " % st.stability
	top["speed"].text = CampaignClock.SPEED_NAMES[CampaignClock.speed_index]
	_refresh_inspector()
	_refresh_military()
	_refresh_market()
	_refresh_reports()
	queue_redraw()


func _refresh_inspector() -> void:
	var st := GameState.cs
	if selected_region == "" or not st.regions.has(selected_region):
		insp["name"].text = "Select a region on the map."
		return
	var r: Dictionary = st.regions[selected_region]
	insp["name"].text = r["name"] + "  [" + selected_region + "]"
	insp["controller"].text = "Controller: %s (claim: %s)" % [
		st.countries[r["controller"]]["name"], st.countries[r["country"]]["name"]]
	insp["pop"].text = "Population %dk · urbanization %.0f%%" % [
		r["population"] / 1000, r["urbanization"] * 100]
	insp["terrain"].text = "Terrain: %s · climate %s" % [r["terrain"], r["climate"]]
	insp["stability"].text = "Stability %.2f · legitimacy %.2f" % [r["stability"], r["legitimacy"]]
	insp["support"].text = "Support for you %.2f" % r["support_player"]
	insp["economy"].text = "Economy %.2f · resources: %s" % [
		r["economy"], ", ".join(r["resources"]) if r["resources"].size() else "none"]
	insp["infra"].text = "Infrastructure %d/4 · depot level %d" % [r["infra"], r["depot_level"]]
	insp["stocks"].text = "Stocks F%.0f A%.0f Fu%.0f P%.0f" % [
		r["stocks"]["food"], r["stocks"]["ammo"], r["stocks"]["fuel"], r["stocks"]["parts"]]
	insp["neighbors"].text = "Links: " + ", ".join(r["neighbors"])
	var hist: Array = r["history"].slice(-4)
	insp["events"].text = "Recent: " + ("; ".join(hist.map(
		func(h): return h["text"])) if hist.size() else "quiet")


func _refresh_military() -> void:
	var st := GameState.cs
	var list: ItemList = panels["Military"].get_node("FormationList")
	list.clear()
	for fid in st.formations:
		var f: Dictionary = st.formations[fid]
		if f["country"] != st.player_id():
			continue
		list.add_item("%s @%s (%d units, mor %.2f)" % [f["name"], f["region"],
			f["units"].size(), f["morale"]])
		list.set_metadata(list.item_count - 1, fid)
	var info: Label = panels["Military"].get_node("FormationInfo")
	if selected_formation != "" and st.formations.has(selected_formation):
		var f: Dictionary = st.formations[selected_formation]
		var comps: Array = []
		for u in f["units"]:
			comps.append("%dx %s/%s" % [u["count"], u["class"], u["equip"]])
		info.text = "%s\nCommander %s\nComposition: %s\nMorale %.2f Cohesion %.2f Readiness %.2f Supplies %.2f\nRegion %s" % [
			f["name"], f["commander"], ", ".join(comps), f["morale"], f["cohesion"],
			f["readiness"], f["supplies"], f["region"]]
	else:
		info.text = "Select a formation."


func _refresh_market() -> void:
	var st := GameState.cs
	var list: ItemList = panels["Market"].get_node("MarketList")
	list.clear()
	market_rows = []
	for id in GameState.market.catalog:
		var it: Dictionary = GameState.market.catalog[id]
		var avail := GameState.market.availability(st, id)
		list.add_item("%s  T%d  %.0fcr%s" % [it["name"], it["tier"], it["price"],
			"" if avail["ok"] else "  [UNAVAILABLE]"])
		list.set_metadata(list.item_count - 1, id)
		market_rows.append(id)
	var orders: Label = panels["Market"].get_node("OrdersLabel")
	var lines: Array = []
	for oid in st.market_orders:
		var o: Dictionary = st.market_orders[oid]
		lines.append("%s: %s x%d %s eta%d" % [oid, o["item"], o["qty"], o["status"], o["eta_day"]])
	var inv_lines: Array = []
	for k in st.inventory:
		if int(st.inventory[k]) > 0:
			inv_lines.append("%s x%d" % [k, st.inventory[k]])
	orders.text = "Inventory: " + ", ".join(inv_lines) + \
		"\nOrders: " + ("; ".join(lines) if lines.size() else "none")


func _refresh_reports() -> void:
	var list: ItemList = panels["Reports"].get_node("ReportList")
	list.clear()
	for rep in GameState.cs.reports:
		list.add_item("D%d [%s] %s" % [rep["day"], rep["kind"], rep["title"]])


# ---------------------------------------------------------------- actions
func _on_speed(i: int) -> void:
	CampaignClock.set_speed(i)
	_refresh_all()


func _on_save() -> void:
	var err := SaveManager.save_slot(1, "manual")
	EventBus.notification.emit("Saved." if err == "" else "Save failed: " + err,
		0 if err == "" else 2)


func _on_recruit() -> void:
	if selected_region == "":
		return
	var res := GameState.economy.recruit(GameState.cs, selected_region, 40, 25.0)
	if not res["ok"]:
		EventBus.notification.emit(res["error"], 2)
	_refresh_all()


func _on_depot() -> void:
	if selected_region == "":
		return
	var res := GameState.supply.build_depot(GameState.cs, selected_region, 2500.0)
	if not res["ok"]:
		EventBus.notification.emit(res["error"], 2)
	_refresh_all()


func _on_formation_selected(idx: int) -> void:
	var list: ItemList = panels["Military"].get_node("FormationList")
	selected_formation = list.get_item_metadata(idx)
	_refresh_all()


func _on_move_mode() -> void:
	order_targeting = true
	EventBus.notification.emit("Click a target region on the map.", 0)


func _on_hold() -> void:
	if selected_formation != "":
		GameState.command.issue_hold(GameState.cs, selected_formation)
		_refresh_all()


func _on_retreat() -> void:
	if selected_formation != "":
		GameState.command.issue_retreat(GameState.cs, selected_formation)
		_refresh_all()


func _on_issue_rifles() -> void:
	if selected_formation != "":
		var res := GameState.market.equip_from_inventory(GameState.cs,
			selected_formation, "rif_basic", 10)
		if not res["ok"]:
			EventBus.notification.emit(res["error"], 2)
		_refresh_all()


func _on_engage() -> void:
	if selected_formation == "":
		return
	var f: Dictionary = GameState.cs.formations[selected_formation]
	if GameState.combat.hostile_pairs(GameState.cs, f["region"]).is_empty():
		EventBus.notification.emit("No hostile contact in this region.", 1)
		return
	CampaignClock.set_speed(0)
	get_tree().change_scene_to_file("res://scenes/tactical_map.tscn")


func _on_market_selected(idx: int) -> void:
	var list: ItemList = panels["Market"].get_node("MarketList")
	var id: String = list.get_item_metadata(idx)
	var info: Label = panels["Market"].get_node("MarketInfo")
	var it: Dictionary = GameState.market.item(id)
	var q := GameState.market.quote(GameState.cs, id, 1)
	info.text = "%s\nTier %d · combat %d · reliability %d\nUpkeep %.1f/wk · crew %d · training %d\nDelivery %d days · supplier %s\n%s" % [
		it["name"], it["tier"], it["combat"], it["reliability"], it["upkeep"],
		it["crew"], it["training"], it["delivery_days"], it["supplier"],
		("Diplomatic: " + ", ".join(q["diplomatic"])) if q["ok"] else q.get("error", "")]


func _on_buy() -> void:
	var list: ItemList = panels["Market"].get_node("MarketList")
	if list.get_selected_items().is_empty():
		return
	var id: String = list.get_item_metadata(list.get_selected_items()[0])
	var q := GameState.market.quote(GameState.cs, id, 1)
	if not q["ok"]:
		EventBus.notification.emit(q["error"], 2)
		return
	pending_quote = {"id": id, "quote": q}
	confirm_dialog.dialog_text = "Buy %s x1 for %.0f credits?\nWeekly upkeep +%.1f · ETA %d days\n%s" % [
		GameState.market.item(id)["name"], q["price"], q["upkeep_per_week"],
		q["eta_days"], "\n".join(q["diplomatic"])]
	confirm_dialog.popup_centered()


func _on_confirm_purchase() -> void:
	if pending_quote.is_empty():
		return
	var res := GameState.market.purchase(GameState.cs, pending_quote["id"], 1)
	if not res["ok"]:
		EventBus.notification.emit(res["error"], 2)
	pending_quote = {}
	_refresh_all()


func _on_report_selected(idx: int) -> void:
	var rep: Dictionary = GameState.cs.reports[idx]
	var detail: TextEdit = panels["Reports"].get_node("ReportDetail")
	detail.text = rep["body"]


func _process(_d: float) -> void:
	if GameState.cs != null:
		top["date"].text = "Day %d  " % GameState.cs.day
		top["treasury"].text = "Treasury %.0f  " % GameState.cs.treasury
		queue_redraw()
