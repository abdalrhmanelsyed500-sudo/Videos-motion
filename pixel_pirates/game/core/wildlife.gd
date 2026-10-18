extends RefCounted
## Wildlife sighting model (Module E1). Python twin: tools/data_tools/wildlife.py
## (golden file tests/fixtures/wildlife_cases.json).
## Pure and stateless like core/ocean.gd: the same place and time always shows the same animal, so nothing is saved.
## A "slot" is perf.sighting_min_gap_s of real time (90 s = 0.1 game days). In each slot,
## at each 40 km cell, the world rolls once: nothing, or one sighting chosen from every species that could be
## here NOW, weighted by how well the place, season, hour and water suit it.
## Fog and rain shorten how far an animal can be seen, as they do for ships.
const Ocean := preload("res://core/ocean.gd")
const DataLoader := preload("res://core/data_loader.gd")
const WILDLIFE_DIR := "res://data/wildlife"
const RARITY_W := {"common": 1.0, "uncommon": 0.4, "rare": 0.12, "legendary": 0.02}
const HASH_SEED := 311
const MIN_ABUNDANCE := 0.02
const GAME_S_PER_REAL_S := 96.0


static func load_species() -> Array:
	var out: Array = []
	var d := DirAccess.open(WILDLIFE_DIR)
	if d == null:
		return out
	var files: Array[String] = []
	for f in d.get_files():
		if f.begins_with("species_") and f.ends_with(".json"):
			files.append(f)
	files.sort()
	for f in files:
		var doc: Dictionary = DataLoader.load_dict(WILDLIFE_DIR + "/" + f)
		out.append_array(doc.get("records", []))
	return out


static func slot_days(tuning: Dictionary) -> float:
	return float(tuning["perf.sighting_min_gap_s"]) * GAME_S_PER_REAL_S / 86400.0


static func activity_factor(kind: String, hour: float) -> float:
	if kind == "always":
		return 1.0
	var day := hour >= 6.0 and hour < 18.0
	if kind == "diurnal":
		return 1.0 if day else 0.25
	if kind == "nocturnal":
		return 0.25 if day else 1.0
	var near := minf(absf(hour - 6.0), absf(hour - 18.0))   # crepuscular: dawn and dusk
	return 1.0 if near <= 2.0 else 0.4


static func season_factor(window: Variant, s: float) -> float:
	if not (window is Array) or (window as Array).size() < 2:
		return 1.0
	var a := float(window[0])
	var b := float(window[1])
	var inside := (s >= a and s <= b) if a <= b else (s >= a or s <= b)
	return 1.0 if inside else 0.15


## Relative weight of one species at one sampled place and time. 0 means it cannot be here.
static func suitability(tuning: Dictionary, region_ids: Array, sp: Dictionary, smp: Dictionary) -> float:
	var w: PackedFloat64Array = smp["weights"]
	var ab := 0.0
	for i in region_ids.size():
		for rr in sp["regions"]:
			if str(rr["region"]) == str(region_ids[i]):
				ab += w[i] * float(rr["abundance"])
	if ab < MIN_ABUNDANCE:   # a trace from a far region's blend tail is not a population
		return 0.0
	var tol := float(tuning["wildlife.temp_tolerance_c"])
	var tf := 1.0
	var habitat := str(sp["habitat"])
	if habitat != "deep" and habitat != "vent":
		var sst := float(smp["sst_c"])
		var temp: Array = sp["temp_c"]
		var out_of_range := maxf(0.0, maxf(float(temp[0]) - sst, sst - float(temp[1])))
		tf = clampf(1.0 - out_of_range / tol, 0.0, 1.0)
	var pf := 1.0
	var need := float(sp.get("needs_productivity", 0.0))
	if need > 0.0:
		pf = clampf(float(smp["productivity"]) / need, 0.0, 1.0)
	var icef := 1.0
	var ice := float(smp["ice"])
	if habitat == "ice_edge":
		icef = 0.4 + 0.6 * clampf(ice * 3.0, 0.0, 1.0)
	elif ice > 0.5:
		icef = 0.3
	var season_f := season_factor(sp.get("season", null), float(smp["season"]))
	var act_f := activity_factor(str(sp["activity"]), float(smp["hour"]))
	return ab * tf * pf * icef * season_f * act_f * float(RARITY_W[str(sp["rarity"])])


## [[species_id, weight], ...] for every species that could be here now.
static func table(ocean: RefCounted, species: Array, x: float, y: float, t_days: float) -> Array:
	var smp: Dictionary = ocean.sample(x, y, t_days)
	var ids: Array = []
	for r in ocean.regions:
		ids.append(str(r["id"]))
	var tuning: Dictionary = ocean.tuning()
	var out: Array = []
	for sp in species:
		var wt := suitability(tuning, ids, sp, smp)
		if wt > 0.0:
			out.append([str(sp["id"]), wt])
	return out


## The sighting for the slot containing t_days at the 40 km cell containing (x, y), or {} for none. Deterministic.
static func sighting(ocean: RefCounted, species: Array, x: float, y: float, t_days: float) -> Dictionary:
	var tuning: Dictionary = ocean.tuning()
	var sd := slot_days(tuning)
	var slot := int(floorf(t_days / sd))
	var cell := float(tuning["perf.weather_grid_km"])
	var cx := int(floorf(x / cell))
	var cy := int(floorf(y / cell))
	if Ocean.hash01(slot, cx, cy, HASH_SEED) >= float(tuning["wildlife.sighting_chance"]):
		return {}
	var tb := table(ocean, species, x, y, (slot + 0.5) * sd)
	var total := 0.0
	for row in tb:
		total += float(row[1])
	if total <= 0.0:
		return {}
	var pick := Ocean.hash01(slot, cx, cy, HASH_SEED + 1) * total
	var acc := 0.0
	var chosen := str(tb[tb.size() - 1][0])
	for row in tb:
		acc += float(row[1])
		if pick <= acc:
			chosen = str(row[0])
			break
	var sp: Dictionary = {}
	for q in species:
		if str(q["id"]) == chosen:
			sp = q
			break
	var smp: Dictionary = ocean.sample(x, y, t_days)
	var dmin := float(tuning["wildlife.sight_distance_min"])
	var dmax := float(tuning["wildlife.sight_distance_max"])
	var dist := float(smp["visibility_km"]) * (dmin + (dmax - dmin) * Ocean.hash01(slot, cx, cy, HASH_SEED + 2))
	var size: Array = sp["group_size"]
	var lo := int(size[0])
	var hi := int(size[1])
	var n := lo
	if hi > lo:
		n = int(floorf(float(lo) * pow(float(hi) / float(lo), Ocean.hash01(slot, cx, cy, HASH_SEED + 3)) + 0.5))
	return {"species": chosen, "bearing_deg": 360.0 * Ocean.hash01(slot, cx, cy, HASH_SEED + 4),
			"distance_km": dist, "count": n, "slot": slot}
