extends RefCounted
## CP-2 Release B: what a hauled net holds. Pure logic (tests/test_fish_manual.gd). The species and the ground come from the
## EXISTING data (data/port/fishing_grounds.json weights, richness; data/port/fish_market.json names and prices); the only new
## data is the average weight of one fish per species (data/port/manual_fishing.json), which turns kg into a number of fish.
## The hold stays in kg (PortState.lots); the number of fish shown anywhere is count_for(kg, avg_kg), so the barrels, the panel
## and the market always agree.
const Fishing := preload("res://h2d/fishing.gd")


## How many fish `kg` of a species is (at least one when there is any weight at all).
static func count_for(kg: float, avg_kg: float) -> int:
	if kg <= 0.004:
		return 0
	return maxi(1, int(roundf(kg / maxf(avg_kg, 0.01))))


static func grade_for(q: float) -> String:
	if q >= 0.95:
		return "Excellent"
	if q >= 0.72:
		return "Good"
	if q >= 0.45:
		return "Fair"
	return "Poor"


## The species in the net: one drawn by the ground's weights, and with probability `second_p` a second one of the same ground.
## Returns [[species id, share 0..1], ...] and the new generator state: {species: Array, state: int}.
static func pick_species(ground: Dictionary, state: int, second_p: float) -> Dictionary:
	var list: Array = ground["species"]
	var total := 0.0
	for sw in list:
		total += float((sw as Array)[1])
	var a := Fishing.next_rand(state)
	var b := Fishing.next_rand(int(a[0]))
	var c := Fishing.next_rand(int(b[0]))
	var first := str(((list[list.size() - 1]) as Array)[0])
	var acc := 0.0
	for sw in list:
		acc += float((sw as Array)[1]) / total
		if float(a[1]) < acc:
			first = str((sw as Array)[0])
			break
	var out: Array = [[first, 1.0]]
	if list.size() > 1 and float(b[1]) < second_p:
		# the second species: the next one in the list after the first (deterministic and always a species of this ground)
		var idx := 0
		for i in list.size():
			if str((list[i] as Array)[0]) == first:
				idx = i
		var second := str((list[(idx + 1 + int(float(c[1]) * float(list.size() - 1))) % list.size()] as Array)[0])
		if second == first:
			second = str((list[(idx + 1) % list.size()] as Array)[0])
		var share := 0.65 + 0.2 * float(c[1])
		out = [[first, share], [second, 1.0 - share]]
	return {"species": out, "state": int(c[0])}


## Builds the catch: `kg` in total split by `species_shares`, rounded to whole fish. Returns
## {fish: [{species, count, kg}], count, kg}. kg is count x average weight (so the number of fish and the weight agree).
static func compose(species_shares: Array, kg: float, species_data: Dictionary, state: int, spread: float) -> Dictionary:
	var fish: Array = []
	var total_kg := 0.0
	var total_n := 0
	var st := state
	for i in species_shares.size():
		var s: Array = species_shares[i]
		var sp := str(s[0])
		var share := float(s[1])
		var avg := float((species_data.get(sp, {}) as Dictionary).get("avg_kg", 0.5))
		var r := Fishing.next_rand(st)
		st = int(r[0])
		var want := kg * share
		var n := count_for(want, avg)
		if want < (0.25 if i == 0 else 0.5) * avg:
			n = 0            # a net with less than a quarter of the main fish (half of the second) holds none of it
		if n <= 0:
			continue
		var w := floorf(float(n) * avg * (1.0 + spread * (2.0 * float(r[1]) - 1.0)) * 100.0 + 0.5) / 100.0
		fish.append({"species": sp, "count": n, "kg": w})
		total_kg += w
		total_n += n
	return {"fish": fish, "count": total_n, "kg": floorf(total_kg * 100.0 + 0.5) / 100.0, "state": st}
