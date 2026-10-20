extends RefCounted
## CP-2 Release A: the provisions list and the fish rows come from the real inventory and fish lots.
const Stores := preload("res://h2d/ship_stores.gd")
const Layout := preload("res://h2d/ship_layout.gd")
const DataLoader := preload("res://core/data_loader.gd")


func run(t: Object) -> void:
	var items := Stores.index_items(DataLoader.load_dict("res://data/items/items.json").get("records", []))
	t.call("check", items.size() >= 20, "item records loaded (%d)" % items.size())
	t.call("check", Stores.zone_units({}, items).is_empty(), "empty inventory: bare racks")
	t.call("check", Stores.provision_rows({}, items).is_empty(), "empty inventory: no rows")
	var inv := {"item_hardtack": 40, "item_water_barrel": 2, "item_rope": 0, "item_unknown": 5, "item_gunpowder": 10}
	var z := Stores.zone_units(inv, items)
	t.call("check", int(z.get("food", 0)) == 40 and int(z.get("drink", 0)) == 2 and int(z.get("ammo", 0)) == 10, "units per rack zone: %s" % str(z))
	t.call("check", not z.has("parts"), "zero and unknown items do not fill a rack")
	var rows := Stores.provision_rows(inv, items)
	var names: Array = []
	for r in rows:
		names.append(str((r as Array)[0]))
	t.call("check", names.has("Hardtack") and names.has("Water Barrel") or names.has("Water barrel"), "hardtack and water listed: %s" % str(names))
	t.call("check", not names.has("Rope"), "a zero-count item is hidden")
	t.call("check", names.find("FOOD") < names.find("Hardtack"), "group heading precedes its items")
	var kg := Stores.total_kg(inv, items)
	t.call("check", kg > 40.0, "total weight counts the items (%.1f kg)" % kg)
	for id in Stores.TEST_PACK.keys():
		t.call("check", items.has(id), "test pack item exists: %s" % id)
	# fish: two lots of one species merge, an empty species is hidden
	var lots := [["spc_mackerel", 4.0, 0.0], ["spc_mackerel", 6.0, 1.0], ["spc_sardine", 0.0, 0.0]]
	var fish := {"spc_mackerel": {"name": "Atlantic Mackerel"}, "spc_sardine": {"name": "Sardine"}}
	var fr := func(caught: float, now: float) -> float: return 1.0 - 0.1 * (now - caught)
	var fr_rows := Stores.fish_rows(lots, fish, 1.0, fr)
	t.call("check", fr_rows.size() == 1, "one species with fish (%d rows)" % fr_rows.size())
	t.call("check", str((fr_rows[0] as Array)[0]) == "Atlantic Mackerel" and str((fr_rows[0] as Array)[1]) == "10.0 kg", "merged lots: %s" % str(fr_rows))
	t.call("check", str((fr_rows[0] as Array)[2]) == "fresh 96%", "freshness is weight-averaged: %s" % str((fr_rows[0] as Array)[2]))
	t.call("check", Stores.fish_rows([], fish, 0.0, fr).is_empty(), "no lots, no rows")
	t.call("check", Layout.pieces_for("food", 40) == 5, "40 food units show 5 sacks on the rack")
