extends RefCounted
## CP-2 Release B: what the fish-storage panel shows, as DATA (no nodes): one row per species that is really in the hold, from the real
## hold lots (PortState.lots), the species records (names) and data/port/manual_fishing.json (icon id, average weight of one fish).
## Species with no fish are not listed. The hold stores kilograms; the number of fish is kg / average weight (Catch.count_for), the same
## figure the catch card shows. Pure and testable; the panel only draws it.
const Catch := preload("res://h2d/fish_catch.gd")


## lots: [[species, kg, caught_day]]; fish: PortState.fish (id -> record with "name"); species: manual_fishing.json "species";
## freshness: Callable(caught_day, now) -> 0..1; capacity: kg.
static func model(lots: Array, fish: Dictionary, species: Dictionary, now: float, freshness: Callable, capacity: float) -> Dictionary:
	var kg: Dictionary = {}
	var fr: Dictionary = {}
	for lot in lots:
		var l: Array = lot
		var sp := str(l[0])
		var w := float(l[1])
		kg[sp] = float(kg.get(sp, 0.0)) + w
		var f := 1.0
		if freshness.is_valid():
			f = float(freshness.call(float(l[2]), now))
		fr[sp] = float(fr.get(sp, 0.0)) + w * f
	var ids: Array = kg.keys()
	ids.sort()
	var rows: Array = []
	var total_kg := 0.0
	var total_n := 0
	for sp in ids:
		var k := float(kg[sp])
		if k <= 0.004:
			continue
		var rec: Dictionary = species.get(sp, {})
		var n := Catch.count_for(k, float(rec.get("avg_kg", 0.5)))
		rows.append({"id": str(sp), "name": str((fish.get(sp, {}) as Dictionary).get("name", sp)), "icon": str(rec.get("icon", "")), "count": n, "kg": k,
				"fresh": int(roundf(100.0 * float(fr[sp]) / k))})
		total_kg += k
		total_n += n
	rows.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["kg"]) > float(b["kg"]))
	return {"rows": rows, "total_n": total_n, "total_kg": total_kg, "capacity": capacity, "remaining": maxf(capacity - total_kg, 0.0), "empty": rows.is_empty()}
