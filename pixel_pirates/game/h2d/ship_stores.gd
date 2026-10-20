extends RefCounted
## CP-2 Release A: what the provisioning hold shows and the fish barrels hold, derived from the REAL data: GameState.inventory
## (item id -> count) with the item records of data/items/items.json, and PortState.lots (the fish hold). No second inventory,
## no second economy: this file only reads and arranges. Pure logic, tested in tests/test_ship_stores.gd.
const Layout := preload("res://h2d/ship_layout.gd")
## Shift+F6 test pack (the real inventory starts empty until the port sells provisions): item id -> count.
const TEST_PACK := {"item_hardtack": 40, "item_salt_meat": 20, "item_water_barrel": 4, "item_grog": 6, "item_gunpowder": 10,
		"item_cannonball": 15, "item_lime": 6, "item_hammer": 1, "item_rope": 6, "item_plank": 8, "item_cloth": 6, "item_salt": 10}


static func index_items(records: Array) -> Dictionary:
	var out: Dictionary = {}
	for r in records:
		var d: Dictionary = r
		out[str(d["id"])] = d
	return out


## Units per rack zone id from the inventory.
static func zone_units(inventory: Dictionary, items: Dictionary) -> Dictionary:
	var out: Dictionary = {}
	for id in inventory.keys():
		var n := int(inventory[id])
		if n <= 0 or not items.has(str(id)):
			continue
		var zone := Layout.zone_for_category(str((items[str(id)] as Dictionary).get("category", "")))
		if zone == "":
			continue
		out[zone] = int(out.get(zone, 0)) + n
	return out


## Rows for the info panel: [name, quantity text, detail text]; zero counts are hidden; groups follow the rack order.
static func provision_rows(inventory: Dictionary, items: Dictionary) -> Array:
	var rows: Array = []
	for z in Layout.ZONES:
		var zd: Dictionary = z
		var lines: Array = []
		for id in inventory.keys():
			var n := int(inventory[id])
			if n <= 0 or not items.has(str(id)):
				continue
			var rec: Dictionary = items[str(id)]
			if (zd["cats"] as Array).has(str(rec.get("category", ""))):
				lines.append([str(rec.get("name", id)), "x%d" % n, "%.1f kg" % (float(rec.get("weight_kg", 0.0)) * float(n))])
		if lines.is_empty():
			continue
		lines.sort_custom(func(a: Array, b: Array) -> bool: return str(a[0]) < str(b[0]))
		if not rows.is_empty():
			rows.append(["", "", ""])
		rows.append([str(zd["label"]).to_upper(), "", ""])
		rows.append_array(lines)
	return rows


static func total_kg(inventory: Dictionary, items: Dictionary) -> float:
	var kg := 0.0
	for id in inventory.keys():
		if items.has(str(id)):
			kg += float((items[str(id)] as Dictionary).get("weight_kg", 0.0)) * float(maxi(int(inventory[id]), 0))
	return kg


## Fish rows from the hold's lots: [species name, "12.5 kg", "fresh 98%"]. Species with no fish are hidden.
static func fish_rows(lots: Array, fish: Dictionary, now: float, freshness: Callable) -> Array:
	var kg: Dictionary = {}
	var fr: Dictionary = {}
	for lot in lots:
		var l: Array = lot
		var sp := str(l[0])
		var w := float(l[1])
		kg[sp] = float(kg.get(sp, 0.0)) + w
		fr[sp] = float(fr.get(sp, 0.0)) + w * float(freshness.call(float(l[2]), now))
	var out: Array = []
	var keys: Array = kg.keys()
	keys.sort()
	for sp in keys:
		var k := float(kg[sp])
		if k <= 0.004:
			continue
		var nm := str((fish.get(sp, {}) as Dictionary).get("name", sp))
		out.append([nm, "%.1f kg" % k, "fresh %d%%" % int(roundf(100.0 * float(fr[sp]) / k))])
	return out
