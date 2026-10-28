extends Control
## Data-driven strategic map. One canvas draws the region graph (not a node per
## region); zoom, pan, hit testing and view culling share the same transform.

const PixelArt = preload("res://core/pixel_art.gd")
const UiStyle = preload("res://core/ui_style.gd")
const MAP_SCALE := Vector2(10.4, 11.6)
const MAP_OFF := Vector2(40, 60)
const MAP_VIEW := Rect2(0, 42, 940, 636)

var selected_region: String = ""
var selected_formation: String = ""
var selected_market_id: String = ""
var order_targeting: bool = false
var map_zoom: float = 1.0
var map_pan := Vector2.ZERO
var panning := false
var panels: Dictionary = {}
var insp: Dictionary = {}
var top: Dictionary = {}
var market_rows: Array = []
var confirm_dialog: AcceptDialog
var pending_quote: Dictionary = {}
var last_drawn_day := -1
var world_tiles: Dictionary = {}


func _ready() -> void:
	theme = UiStyle.make_theme()
	_load_world_art()
	if GameState.cs == null:
		GameState.new_campaign(1234)
	selected_region = GameState.cs.countries[GameState.cs.player_id()]["capital"]
	_build_topbar()
	_build_dock()
	EventBus.notification.connect(_on_notification)
	_refresh_all()


func _load_world_art() -> void:
	var terrain_names := {"plains": "t_grass", "coast": "t_grass", "forest": "t_forest",
		"hills": "t_hills", "urban": "t_urban", "desert": "t_desert", "badlands": "t_desert",
		"mountain": "t_mountain", "marsh": "t_marsh", "snow": "t_snow"}
	var loaded := {}
	for terrain in terrain_names:
		var name: String = terrain_names[terrain]
		if not loaded.has(name):
			loaded[name] = PixelArt.texture("res://assets/sprites/terrain/" + name + ".png")
		if loaded[name] != null:
			world_tiles[terrain] = loaded[name]


func _build_topbar() -> void:
	var bar := HBoxContainer.new()
	bar.position = Vector2(8, 6)
	bar.size = Vector2(920, 30)
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
	var status := Label.new()
	status.position = Vector2(12, 687)
	status.size = Vector2(920, 28)
	status.text = "Wheel: zoom  ·  Middle drag: pan  ·  Select a region"
	status.add_theme_color_override("font_color", Color(0.93, 0.84, 0.56))
	add_child(status)
	top["message"] = status


func _build_dock() -> void:
	var dock := VBoxContainer.new()
	dock.position = Vector2(946, 40)
	dock.size = Vector2(326, 672)
	add_child(dock)
	var tabs := HBoxContainer.new()
	dock.add_child(tabs)
	var keys := ["Inspector", "Military", "Market", "Politics", "Reports"]
	var labels := ["Region", "Forces", "Arms", "Politics", "Reports"]
	for i in keys.size():
		var b := Button.new()
		b.text = labels[i]
		b.add_theme_font_size_override("font_size", 12)
		b.pressed.connect(_show_panel.bind(keys[i]))
		tabs.add_child(b)
	for key in keys:
		var sc := ScrollContainer.new()
		sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
		sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
		var box := VBoxContainer.new()
		box.custom_minimum_size.x = 296
		box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		sc.add_child(box)
		dock.add_child(sc)
		panels[key] = box
	_build_inspector()
	_build_military()
	_build_market()
	_build_politics()
	_build_reports()
	_show_panel("Inspector")
	confirm_dialog = AcceptDialog.new()
	confirm_dialog.title = "CONFIRM PROCUREMENT"
	add_child(confirm_dialog)
	confirm_dialog.confirmed.connect(_on_confirm_purchase)


func _add_action(box: VBoxContainer, text: String, callback: Callable) -> void:
	var b := Button.new()
	b.text = text
	b.pressed.connect(callback)
	box.add_child(b)


func _build_inspector() -> void:
	var box: VBoxContainer = panels["Inspector"]
	for key in ["name", "controller", "pop", "terrain", "stability", "support", "economy",
			"infra", "security", "stocks", "depot", "neighbors", "events"]:
		insp[key] = Label.new()
		insp[key].autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		box.add_child(insp[key])
	_add_action(box, "Recruit up to 40 (25/person)", _on_recruit)
	_add_action(box, "Build / upgrade depot (2500)", _on_depot)
	_add_action(box, "Invest in security (200)", _on_invest.bind("security"))
	_add_action(box, "Restore infrastructure (300)", _on_invest.bind("infrastructure"))
	_add_action(box, "Support local economy (240)", _on_invest.bind("economy"))
	_add_action(box, "Recover battlefield salvage", _on_recover)
	_add_action(box, "Repair selected salvage x1", _on_repair_salvage)


func _build_military() -> void:
	var box: VBoxContainer = panels["Military"]
	var list := ItemList.new()
	list.name = "FormationList"
	list.custom_minimum_size = Vector2(280, 150)
	list.item_selected.connect(_on_formation_selected)
	box.add_child(list)
	var info := Label.new()
	info.name = "FormationInfo"
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(info)
	_add_action(box, "Move: choose a land region", _on_move_mode)
	_add_action(box, "Hold / cancel orders", _on_hold)
	_add_action(box, "Retreat to friendly region", _on_retreat)
	_add_action(box, "Issue selected Arms item x1", _on_issue_selected)
	_add_action(box, "Repair formation", _on_repair_formation)
	_add_action(box, "Open tactical battle", _on_engage)
	_add_action(box, "Resolve one contact automatically", _on_auto_resolve)


func _build_market() -> void:
	var box: VBoxContainer = panels["Market"]
	var list := ItemList.new()
	list.name = "MarketList"
	list.custom_minimum_size = Vector2(280, 180)
	list.item_selected.connect(_on_market_selected)
	box.add_child(list)
	var info := Label.new()
	info.name = "MarketInfo"
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(info)
	_add_action(box, "Buy selected x1 (confirm)", _on_buy)
	var orders := Label.new()
	orders.name = "OrdersLabel"
	orders.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(orders)


func _build_politics() -> void:
	var box: VBoxContainer = panels["Politics"]
	var info := Label.new()
	info.name = "PoliticsInfo"
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(info)
	_add_action(box, "Declare conflict with Vardena", _on_declare)
	_add_action(box, "Offer government ceasefire", _on_ceasefire)
	_add_action(box, "Offer negotiated transition", _on_transition)
	_add_action(box, "Government outreach (500)", _on_outreach)


func _build_reports() -> void:
	var box: VBoxContainer = panels["Reports"]
	var list := ItemList.new()
	list.name = "ReportList"
	list.custom_minimum_size = Vector2(280, 250)
	list.item_selected.connect(_on_report_selected)
	box.add_child(list)
	var detail := TextEdit.new()
	detail.name = "ReportDetail"
	detail.editable = false
	detail.custom_minimum_size = Vector2(280, 180)
	box.add_child(detail)


func _show_panel(key: String) -> void:
	for k in panels:
		(panels[k].get_parent() as Control).visible = (k == key)
	_refresh_all()


func _on_notification(text: String, priority: int) -> void:
	if top.has("message"):
		top["message"].text = text
		top["message"].add_theme_color_override("font_color", Color(1.0, 0.5, 0.35) if priority >= 2 else Color(0.93, 0.84, 0.56))


# ---------------------------------------------------------------- input/draw
func _gui_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton:
		if ev.button_index == MOUSE_BUTTON_MIDDLE:
			panning = ev.pressed
			return
		if not ev.pressed or not MAP_VIEW.has_point(ev.position):
			return
		if ev.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			var old_zoom := map_zoom
			map_zoom = clampf(map_zoom * (1.2 if ev.button_index == MOUSE_BUTTON_WHEEL_UP else 1.0 / 1.2), 0.65, 3.0)
			map_pan = ev.position - MAP_OFF - (ev.position - MAP_OFF - map_pan) * map_zoom / old_zoom
			queue_redraw()
			return
		if ev.button_index == MOUSE_BUTTON_LEFT:
			var rid := _region_at(ev.position)
			if rid == "":
				return
			if order_targeting and selected_formation != "":
				var res := GameState.command.issue_move(GameState.cs, selected_formation, rid)
				order_targeting = false
				_show_result(res, "Movement order issued")
			else:
				selected_region = rid
			_refresh_all()
	elif ev is InputEventMouseMotion and panning:
		map_pan += ev.relative
		queue_redraw()


func _region_radius() -> float:
	return (15.0 if GameState.cs.regions.size() >= 100 else 14.0) * clampf(map_zoom, 0.65, 2.0)


func _region_at(p: Vector2) -> String:
	var best := ""
	var best_dist := maxf(8.0, _region_radius() + 4.0)
	for rid in GameState.cs.regions:
		var distance := p.distance_to(_pos(GameState.cs.regions[rid]))
		if distance < best_dist:
			best_dist = distance
			best = rid
	return best


func _pos(r: Dictionary) -> Vector2:
	return Vector2(float(r["pos"][0]), float(r["pos"][1])) * MAP_SCALE * map_zoom + MAP_OFF + map_pan


func _draw() -> void:
	var st := GameState.cs
	if st == null:
		return
	draw_rect(Rect2(0, 0, size.x, size.y), Color(0.10, 0.12, 0.14))
	var visible := {}
	for rid in st.regions:
		if MAP_VIEW.grow(24).has_point(_pos(st.regions[rid])):
			visible[rid] = true
	for rid in visible:
		var r: Dictionary = st.regions[rid]
		for nb in r["neighbors"]:
			if rid < nb and visible.has(nb):
				draw_line(_pos(r), _pos(st.regions[nb]), Color(0.31, 0.34, 0.32), 1.0)
	var radius := _region_radius()
	for rid in visible:
		var r: Dictionary = st.regions[rid]
		var rgb: Array = st.countries[r["controller"]]["color"]
		var col := Color(rgb[0], rgb[1], rgb[2])
		var contested := st.can_observe(st.player_id(), rid) and _is_contested(rid)
		var center := _pos(r)
		var tile_rect := Rect2(center - Vector2(radius, radius), Vector2(radius * 2, radius * 2))
		if world_tiles.has(r["terrain"]):
			draw_texture_rect(world_tiles[r["terrain"]], tile_rect, false, Color(0.76, 0.80, 0.72, 1.0))
		else:
			draw_rect(tile_rect, col.darkened(0.35))
		# A persistent faction stripe and border make control readable over terrain.
		draw_rect(Rect2(tile_rect.position, Vector2(tile_rect.size.x, 4)), col.lightened(0.15))
		draw_rect(tile_rect, col.darkened(0.25), false, 1.5)
		if r["terrain"] == "coast":
			draw_rect(Rect2(tile_rect.position + Vector2(1, tile_rect.size.y - 4), Vector2(tile_rect.size.x - 2, 3)), Color(0.30, 0.46, 0.53))
		if bool(r["is_city"]):
			draw_rect(Rect2(center - Vector2(2, 2), Vector2(4, 4)), Color(0.96, 0.85, 0.55))
		if contested:
			draw_rect(Rect2(center - Vector2(4, 4), Vector2(8, 8)), Color(0.88, 0.28, 0.20))
		if rid == selected_region:
			draw_rect(tile_rect.grow(3), Color(1.0, 0.88, 0.55), false, 2.0)
		if DisplayServer.get_name() != "headless" and (st.regions.size() < 100 or rid == selected_region or map_zoom > 1.8):
			draw_string(ThemeDB.fallback_font, center + Vector2(-25, radius + 12), r["name"], HORIZONTAL_ALIGNMENT_LEFT, 80, 10, Color(0.92, 0.92, 0.84))

	for fid in st.formations:
		var f: Dictionary = st.formations[fid]
		if not visible.has(f["region"]):
			continue
		if f["country"] != st.player_id() and not st.can_observe(st.player_id(), f["region"]):
			continue
		var fp := _pos(st.regions[f["region"]]) + Vector2(0, -radius - 6)
		var rgb: Array = st.countries[f["country"]]["color"]
		var col := Color(rgb[0], rgb[1], rgb[2])
		draw_rect(Rect2(fp - Vector2(5, 3), Vector2(10, 6)), col.lightened(0.3))
		if fid == selected_formation:
			draw_rect(Rect2(fp - Vector2(7, 5), Vector2(14, 10)), Color.WHITE, false, 1.5)
	# Opaque inspector separates text from map tiles even at high zoom.
	draw_rect(Rect2(940, 36, 340, 684), Color(0.08, 0.11, 0.10))
	draw_line(Vector2(940, 36), Vector2(940, 720), Color(0.28, 0.34, 0.28), 1.0)


func _is_contested(rid: String) -> bool:
	return not GameState.combat.hostile_pairs(GameState.cs, rid).is_empty()


# ---------------------------------------------------------------- refresh
func _refresh_all() -> void:
	var st := GameState.cs
	if st == null or top.is_empty() or panels.is_empty():
		return
	top["date"].text = "Day %d  " % st.day
	top["treasury"].text = "Credits %.0f  " % st.treasury
	top["stability"].text = "Stability %.2f  " % st.stability
	top["speed"].text = CampaignClock.SPEED_NAMES[CampaignClock.speed_index]
	_refresh_inspector()
	_refresh_military()
	_refresh_market()
	_refresh_politics()
	_refresh_reports()
	queue_redraw()


func _refresh_inspector() -> void:
	var st := GameState.cs
	if selected_region == "" or not st.regions.has(selected_region):
		insp["name"].text = "Select a region on the map."
		return
	var r: Dictionary = st.regions[selected_region]
	insp["name"].text = "%s  [%s]  %s" % [r["name"], selected_region, "CITY" if r["is_city"] else "district"]
	insp["controller"].text = "Controller: %s\nClaim: %s" % [st.countries[r["controller"]]["name"], st.countries[r["country"]]["name"]]
	insp["pop"].text = "Population %dk · strategic value %.1f" % [r["population"] / 1000, r["strategic_value"]]
	insp["terrain"].text = "Terrain: %s · climate %s" % [r["terrain"], r["climate"]]
	insp["stability"].text = "Stability %.2f · legitimacy %.2f" % [r["stability"], r["legitimacy"]]
	insp["support"].text = "Local support %.2f · opposition %.2f" % [r["political_support"], r["opposition"]]
	insp["economy"].text = "Productivity %.0f%% · output %.2f\nResources: %s" % [float(r["productivity"]) * 100,
		r["economy"], ", ".join(r["resources"]) if r["resources"].size() else "none"]
	insp["infra"].text = "Infrastructure %.0f%% (level %d) · recovery %.0f%%" % [
		float(r["infra_condition"]) * 100, r["infra"], float(r["recovery_progress"]) * 100]
	insp["security"].text = "Security pressure %.2f · focus %s\nSupply route: %s" % [r["security_pressure"], r["admin_focus"],
		"connected" if float(r["supply_accessibility"]) > 0.5 else "unavailable / cut"]
	insp["stocks"].text = "Stocks: food %.0f · ammo %.0f · fuel %.0f · parts %.0f" % [
		r["stocks"]["food"], r["stocks"]["ammo"], r["stocks"]["fuel"], r["stocks"]["parts"]]
	insp["depot"].text = "Depot %d · salvage: %s" % [r["depot_level"], str(r["salvage"]) if not r["salvage"].is_empty() else "none"]
	insp["neighbors"].text = "Land links: " + ", ".join(r["neighbors"]) + ("\nSea links (not navigable): " + ", ".join(r["sea_neighbors"]) if r["sea_neighbors"].size() else "")
	var hist: Array = r["history"].slice(-3)
	insp["events"].text = "Recent: " + ("; ".join(hist.map(func(h): return h["text"])) if hist.size() else "quiet")
	if not st.can_observe(st.player_id(), selected_region):
		insp["stability"].text = "Stability / legitimacy: unknown (no local observation)"
		insp["support"].text = "Local support / opposition: unknown"
		insp["economy"].text = "Known resources: " + (", ".join(r["resources"]) if r["resources"].size() else "none")
		insp["infra"].text = "Infrastructure and recovery: unknown"
		insp["security"].text = "Security and supply route: unknown"
		insp["stocks"].text = "Stockpiles: unknown"
		insp["depot"].text = "Depot and salvage: unknown"
		insp["events"].text = "Recent events: no local intelligence"


func _refresh_military() -> void:
	var st := GameState.cs
	var list: ItemList = panels["Military"].get_node("FormationList")
	list.clear()
	for fid in st.formations:
		var f: Dictionary = st.formations[fid]
		if f["country"] != st.player_id():
			continue
		list.add_item("%s @%s · supply %.0f%%" % [f["name"], f["region"], float(f["supplies"]) * 100])
		list.set_item_metadata(list.item_count - 1, fid)
		if fid == selected_formation:
			list.select(list.item_count - 1)
	var info: Label = panels["Military"].get_node("FormationInfo")
	if selected_formation != "" and st.formations.has(selected_formation):
		var f: Dictionary = st.formations[selected_formation]
		var comps: Array = []
		for u in f["units"]:
			if int(u["count"]) > 0:
				comps.append("%dx %s (%.0f%%)" % [u["count"], u["equip"], float(u["condition"]) * 100])
		var order := GameState.command.active_order(f)
		info.text = "%s\nComposition: %s\nReserve %d · wounded %d · killed %d\nMorale %.2f · readiness %.2f\nSupply %.0f%% · ammo %.0f%%\nOrder: %s\nGear: %s\nSelected item: %s" % [
			f["name"], ", ".join(comps) if comps.size() else "none", f.get("personnel_reserve", 0),
			f.get("wounded", 0), f.get("dead", 0), f["morale"], f["readiness"],
			float(f["supplies"]) * 100, float(f.get("ammo_reserve", 0.8)) * 100,
			("move to " + str(order["target_region"])) if not order.is_empty() else "hold", str(f.get("attachments", {})),
			selected_market_id if selected_market_id != "" else "none"]
	else:
		info.text = "Select a formation. Select equipment in Arms before issuing it."


func _refresh_market() -> void:
	var st := GameState.cs
	var list: ItemList = panels["Market"].get_node("MarketList")
	list.clear()
	market_rows = []
	for id in GameState.market.catalog:
		var it: Dictionary = GameState.market.catalog[id]
		var avail := GameState.market.availability(st, id)
		list.add_item("%s  T%d  %.0fcr%s" % [it["name"], it["tier"], it["price"], "" if avail["ok"] else " [restricted]"])
		list.set_item_metadata(list.item_count - 1, id)
		if id == selected_market_id:
			list.select(list.item_count - 1)
		market_rows.append(id)
	var orders: Label = panels["Market"].get_node("OrdersLabel")
	var lines: Array = []
	for oid in st.market_orders:
		var o: Dictionary = st.market_orders[oid]
		if o.get("owner", st.player_id()) == st.player_id():
			lines.append("%s: %s x%d %s (day %d)" % [oid, o["item"], o["qty"], o["status"], o["eta_day"]])
	var inv_lines: Array = []
	for k in st.inventory:
		if int(st.inventory[k]) > 0:
			inv_lines.append("%s x%d" % [k, st.inventory[k]])
	var damaged: Dictionary = st.countries[st.player_id()].get("damaged_inventory", {})
	orders.text = "Inventory: " + (", ".join(inv_lines) if inv_lines.size() else "none") + \
		"\nDamaged: " + str(damaged) + "\nOrders: " + ("; ".join(lines) if lines.size() else "none")


func _refresh_politics() -> void:
	var st := GameState.cs
	var pos := GameState.administration.political_position(st)
	var rel := st.rel(st.player_id(), "cty_vardena")
	var war := _government_war()
	var status: String = st.wars[war]["status"] if war != "" else ("hostile, undeclared" if st.is_hostile(st.player_id(), "cty_vardena") else "peace")
	var info: Label = panels["Politics"].get_node("PoliticsInfo")
	info.text = "VARDENA POLITICAL POSITION\nControlled: %d/%d (%.0f%%)\nLocal support %.2f · stability %.2f · legitimacy %.2f\nGovernment trust %.2f · threat %.2f\nConflict: %s\n\nSettlement: ceasefire + 30%% of Vardena + support 0.42 + stability 0.40 + legitimacy 0.38.\nMilitary transition: capital + 60%% + same support/stability/legitimacy.\nOutcome: %s" % [
		pos["controlled"], pos["claimed"], float(pos["share"]) * 100, pos["support"], pos["stability"], pos["legitimacy"],
		rel["trust"], rel["threat"], status, st.outcome if st.outcome != "" else "ongoing"]


func _refresh_reports() -> void:
	var list: ItemList = panels["Reports"].get_node("ReportList")
	list.clear()
	for i in GameState.cs.reports.size():
		var rep: Dictionary = GameState.cs.reports[i]
		if rep.get("audience", "public") not in ["public", GameState.cs.player_id()]:
			continue
		list.add_item("D%d [%s] %s" % [rep["day"], rep["kind"], rep["title"]])
		list.set_item_metadata(list.item_count - 1, i)


# ---------------------------------------------------------------- actions
func _show_result(res: Dictionary, success: String) -> void:
	EventBus.notification.emit(success if res.get("ok", false) else str(res.get("error", "Action failed")), 0 if res.get("ok", false) else 2)


func _on_speed(i: int) -> void:
	if GameState.cs.outcome != "" and i > 0:
		EventBus.notification.emit("Campaign ended; return to menu or load a save.", 1)
		return
	CampaignClock.set_speed(i)
	_refresh_all()


func _on_save() -> void:
	var err := SaveManager.save_slot(1, "manual")
	EventBus.notification.emit("Saved to slot 1." if err == "" else "Save failed: " + err, 0 if err == "" else 2)


func _on_recruit() -> void:
	var cost := float(GameState.administration.rules.get("recruit_cost_per_person", 25.0))
	var res := GameState.economy.recruit(GameState.cs, selected_region, 40, cost)
	_show_result(res, "Enlisted %d people; issue equipment to form squads." % int(res.get("recruited", 0)))
	_refresh_all()


func _on_depot() -> void:
	_show_result(GameState.supply.build_depot(GameState.cs, selected_region, 2500.0), "Depot upgraded")
	_refresh_all()


func _on_invest(kind: String) -> void:
	_show_result(GameState.administration.invest(GameState.cs, GameState.cs.player_id(), selected_region, kind), "Investment funded: " + kind)
	_refresh_all()


func _on_recover() -> void:
	_show_result(GameState.market.recover_salvage(GameState.cs, GameState.cs.player_id(), selected_region), "Damaged salvage recovered; repair before issuing")
	_refresh_all()


func _on_repair_salvage() -> void:
	_show_result(GameState.market.repair_recovered(GameState.cs, GameState.cs.player_id(), selected_region, selected_market_id, 1), "Recovered equipment repaired")
	_refresh_all()


func _on_formation_selected(idx: int) -> void:
	var list: ItemList = panels["Military"].get_node("FormationList")
	selected_formation = list.get_item_metadata(idx)
	_refresh_all()


func _on_move_mode() -> void:
	if selected_formation == "":
		EventBus.notification.emit("Select a formation first.", 1)
		return
	order_targeting = true
	EventBus.notification.emit("Click a target region on the map.", 0)


func _on_hold() -> void:
	_show_result(GameState.command.issue_hold(GameState.cs, selected_formation), "Formation ordered to hold")
	_refresh_all()


func _on_retreat() -> void:
	_show_result(GameState.command.issue_retreat(GameState.cs, selected_formation), "Retreat ordered")
	_refresh_all()


func _on_issue_selected() -> void:
	_show_result(GameState.market.equip_from_inventory(GameState.cs, selected_formation, selected_market_id, 1), "Equipment issued")
	_refresh_all()


func _on_issue_rifles() -> void:
	# Compatibility entry point retained for existing integrations.
	_show_result(GameState.market.equip_from_inventory(GameState.cs, selected_formation, "rif_basic", 1), "Rifle package issued")
	_refresh_all()


func _on_repair_formation() -> void:
	_show_result(GameState.market.repair_formation(GameState.cs, selected_formation), "Formation repaired")
	_refresh_all()


func _on_engage() -> void:
	if not GameState.cs.formations.has(selected_formation):
		EventBus.notification.emit("Select a formation first.", 1)
		return
	var f: Dictionary = GameState.cs.formations[selected_formation]
	if GameState.combat.hostile_pairs(GameState.cs, f["region"]).is_empty():
		EventBus.notification.emit("No hostile contact in this region.", 1)
		return
	GameState.tactical_region = f["region"]
	CampaignClock.set_speed(0)
	get_tree().change_scene_to_file("res://scenes/tactical_map.tscn")


func _on_auto_resolve() -> void:
	if not GameState.cs.formations.has(selected_formation):
		EventBus.notification.emit("Select a formation first.", 1)
		return
	var rid: String = GameState.cs.formations[selected_formation]["region"]
	_show_result(GameState.resolve_player_contact(rid), "Engagement resolved; see Reports")
	_refresh_all()


func _on_market_selected(idx: int) -> void:
	var list: ItemList = panels["Market"].get_node("MarketList")
	selected_market_id = list.get_item_metadata(idx)
	var info: Label = panels["Market"].get_node("MarketInfo")
	var it: Dictionary = GameState.market.item(selected_market_id)
	var q := GameState.market.quote(GameState.cs, selected_market_id, 1)
	info.text = "%s\nCombat %d · reliability %d\nUpkeep %.1f/week · delivery %d days\nSupplier %s\n%s" % [it["name"], it["combat"], it["reliability"], it["upkeep"], it["delivery_days"], it["supplier"],
		" ".join(q["diplomatic"]) if q["ok"] else q.get("error", "")]


func _on_buy() -> void:
	var id := selected_market_id
	var q := GameState.market.quote(GameState.cs, id, 1)
	if not q["ok"]:
		_show_result(q, "")
		return
	pending_quote = {"id": id, "quote": q}
	confirm_dialog.dialog_text = "Buy %s x1 for %.0f credits?\nMaintenance +%.1f/week · ETA %d days\n%s" % [
		GameState.market.item(id)["name"], q["price"], q["upkeep_per_week"], q["eta_days"], "\n".join(q["diplomatic"])]
	confirm_dialog.popup_centered()


func _on_confirm_purchase() -> void:
	if pending_quote.is_empty():
		return
	var current := GameState.market.quote(GameState.cs, pending_quote["id"], 1)
	if not current["ok"]:
		_show_result(current, "")
		pending_quote = {}
		return
	if float(current["price"]) != float(pending_quote["quote"]["price"]):
		pending_quote = {}
		EventBus.notification.emit("Supplier price changed; confirm the new quote.", 1)
		_on_buy()
		return
	_show_result(GameState.market.purchase(GameState.cs, pending_quote["id"], 1), "Order paid; delivery pending")
	pending_quote = {}
	_refresh_all()


func _government_war() -> String:
	var pid: String = GameState.cs.player_id()
	for wid in GameState.cs.wars:
		var w: Dictionary = GameState.cs.wars[wid]
		if ((pid in w["sides_a"] and "cty_vardena" in w["sides_b"]) or (pid in w["sides_b"] and "cty_vardena" in w["sides_a"])) \
				and w["status"] in ["active", "ceasefire"]:
			return wid
	return ""


func _on_declare() -> void:
	_show_result(GameState.diplomacy.declare_war(GameState.cs, GameState.cs.player_id(), "cty_vardena", "constitutional crisis"), "Conflict declared")
	_refresh_all()


func _on_ceasefire() -> void:
	var war := _government_war()
	if war == "":
		EventBus.notification.emit("Declare a formal conflict first.", 1)
		return
	var result := GameState.diplomacy.propose_ceasefire(GameState.cs, war)
	_show_result(result, "Ceasefire accepted" if result.get("accepted", false) else "Ceasefire rejected; see Reports")
	_refresh_all()


func _on_transition() -> void:
	var result := GameState.diplomacy.negotiate_transition(GameState.cs)
	_show_result(result, "Negotiated transition achieved")
	if result.get("ok", false):
		CampaignClock.set_speed(0)
	_refresh_all()


func _on_outreach() -> void:
	_show_result(GameState.diplomacy.improve_relations(GameState.cs, "cty_vardena", 500.0), "Diplomatic outreach funded")
	_refresh_all()


func _on_report_selected(idx: int) -> void:
	var list: ItemList = panels["Reports"].get_node("ReportList")
	var rep_index: int = int(list.get_item_metadata(idx))
	var rep: Dictionary = GameState.cs.reports[rep_index]
	var detail: TextEdit = panels["Reports"].get_node("ReportDetail")
	detail.text = rep["body"]


func _process(_delta: float) -> void:
	if GameState.cs != null and GameState.cs.day != last_drawn_day:
		last_drawn_day = GameState.cs.day
		_refresh_all()
