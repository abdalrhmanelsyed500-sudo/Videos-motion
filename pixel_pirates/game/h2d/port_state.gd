# gdlint: disable=max-public-methods
extends RefCounted
## CP-1 starting economy: the purse, the fish hold with freshness, the Fish Row market and the hiring of the four recruits.
## Pure logic (no scene): tests/test_port.gd replays tests/fixtures/economy_cases.json made by tools/h2d/economy_logic.py,
## the Python twin of this file. The market arithmetic is core/market.gd (B4). Every number is in
## data/tuning/tuning_port.json (port.*, fish.spoil_*, market.fish_depth_reales) and data/port/*.json; DEFAULTS only
## covers a missing key and is checked against the JSON by economy_logic.py --check and tests/test_port.gd.
## Money is a whole number of reales. Time is in game days (1 day = 15 real minutes, T1). NOT YET RUN IN GODOT.
const Market := preload("res://core/market.gd")
const DEFAULTS := {
	"port.start_reales": 5.0, "port.hold_kg": 40.0, "port.hold_warn_frac": 0.85, "fish.spoil_per_day": 0.35,
	"fish.spoil_floor": 0.25, "fish.spoil_warn": 0.7, "market.fish_depth_reales": 150.0,
}
const SPREAD_PCT_DEFAULT := 20.0
const HALF_LIFE_DEFAULT := 6.0

var p: Dictionary = DEFAULTS.duplicate()
var spread := 0.2
var half_life := HALF_LIFE_DEFAULT
var fish: Dictionary = {}          # species id -> {name, base_reales_per_kg, factor}
var recruits: Dictionary = {}      # crew id -> record of recruits_port.json
var recruit_order: Array = []
var reales := 5
var lots: Array = []               # [[species, kg, caught_day], ...]
var crew: Array[String] = []
var x: Dictionary = {}             # species id -> market memory x
var t_mkt := 0.0
var sold_total := 0
var kg_total := 0.0
var best_sale := 0
var sales_count := 0


## `tuning` = {key: value}; `fish_doc` = data/port/fish_market.json; `recruit_doc` = data/port/recruits_port.json.
func configure(tuning: Dictionary, fish_doc: Dictionary, recruit_doc: Dictionary) -> void:
	p = DEFAULTS.duplicate()
	for k in DEFAULTS.keys():
		if tuning.has(k):
			p[k] = float(tuning[k])
	spread = float(tuning.get("market.spread_pct", SPREAD_PCT_DEFAULT)) / 100.0
	half_life = float(tuning.get("market.recovery_half_life_days", HALF_LIFE_DEFAULT))
	fish = fish_doc["species"]
	recruits = recruit_doc["recruits"]
	recruit_order = recruit_doc["order"]
	reset()


func reset() -> void:
	reales = int(p["port.start_reales"])
	lots.clear()
	crew.clear()
	x.clear()
	t_mkt = 0.0
	sold_total = 0
	kg_total = 0.0
	best_sale = 0
	sales_count = 0


static func round_half_up(v: float) -> int:
	return int(floorf(v + 0.5))


# ---- crew effects ---------------------------------------------------------------------------------------------
## typ: "catch_bonus" (sum), "hold_kg" (sum) or "spoil_mult" (product).
func effect(typ: String) -> float:
	var out := 1.0 if typ == "spoil_mult" else 0.0
	for c in crew:
		var e: Dictionary = (recruits[c] as Dictionary)["effect"]
		if str(e["type"]) != typ:
			continue
		if typ == "spoil_mult":
			out *= float(e["value"])
		else:
			out += float(e["value"])
	return out


func crew_count() -> int:
	return crew.size()


# ---- the hold ---------------------------------------------------------------------------------------------------
func capacity_kg() -> float:
	return float(p["port.hold_kg"]) + effect("hold_kg")


func hold_kg() -> float:
	var kg := 0.0
	for lot in lots:
		kg += float((lot as Array)[1])
	return kg


func hold_frac() -> float:
	return hold_kg() / maxf(capacity_kg(), 0.001)


func is_full() -> bool:
	return capacity_kg() - hold_kg() < 0.005


## Store `kg` of `species` caught on game day `day`. Returns the kg that fitted (the rest is thrown back).
func add_catch(species: String, kg: float, day: float) -> float:
	var room := maxf(capacity_kg() - hold_kg(), 0.0)
	var put := minf(kg, room)
	put = floorf(put * 100.0 + 0.5) / 100.0
	if put > 0.0:
		lots.append([species, put, day])
		kg_total += put
	return put


func freshness_of(caught: float, now: float) -> float:
	var f := 1.0 - float(p["fish.spoil_per_day"]) * effect("spoil_mult") * maxf(now - caught, 0.0)
	return maxf(float(p["fish.spoil_floor"]), f)


func avg_freshness(now: float) -> float:
	var kg := hold_kg()
	if kg <= 0.0:
		return 1.0
	var s := 0.0
	for lot in lots:
		var l := lot as Array
		s += float(l[1]) * freshness_of(float(l[2]), now)
	return s / kg


func species_in_hold() -> Array:
	var seen: Dictionary = {}
	for lot in lots:
		seen[str((lot as Array)[0])] = true
	var out: Array = seen.keys()
	out.sort()
	return out


func kg_of(species: String) -> float:
	var kg := 0.0
	for lot in lots:
		if str((lot as Array)[0]) == species:
			kg += float((lot as Array)[1])
	return kg


# ---- the market ---------------------------------------------------------------------------------------------------
func _decay_to(now: float) -> void:
	var dt := maxf(now - t_mkt, 0.0)
	if dt > 0.0:
		for k in x.keys():
			x[k] = Market.decay(float(x[k]), dt, half_life)
	t_mkt = maxf(now, t_mkt)


func _memory(species: String, now: float) -> float:
	## The memory as it will be at `now`, without changing the state (for quotes and estimates).
	var dt := maxf(now - t_mkt, 0.0)
	return Market.decay(float(x.get(species, 0.0)), dt, half_life)


## Reales per kg of FRESH fish for a small sale right now: base x factor x (1 - spread/2) x e^x.
func quote(species: String, now: float) -> float:
	var f: Dictionary = fish[species]
	return float(f["base_reales_per_kg"]) * float(f["factor"]) * (1.0 - spread * 0.5) * exp(_memory(species, now))


## 1.0 = the market has forgotten you; below 1 you have pushed the price down.
func price_level(species: String, now: float) -> float:
	return exp(_memory(species, now))


func _base_value(species: String, now: float) -> float:
	var v := 0.0
	for lot in lots:
		var l := lot as Array
		if str(l[0]) == species:
			v += float(l[1]) * float((fish[species] as Dictionary)["base_reales_per_kg"]) * freshness_of(float(l[2]), now)
	return v


## What selling all of `species` would pay now (whole reales), without selling.
func estimate_species(species: String, now: float) -> int:
	var v := _base_value(species, now)
	if v <= 0.0:
		return 0
	var rev := Market.sell_revenue(v, _memory(species, now), float((fish[species] as Dictionary)["factor"]), spread,
			float(p["market.fish_depth_reales"]))
	return round_half_up(rev)


func estimate_all(now: float) -> int:
	var t := 0
	for sp in species_in_hold():
		t += estimate_species(str(sp), now)
	return t


func sell_species(species: String, now: float) -> Dictionary:
	_decay_to(now)
	var kg := kg_of(species)
	if kg <= 0.0:
		return {"kg": 0.0, "reales": 0, "value_base": 0.0, "fresh": 1.0}
	var v := _base_value(species, now)
	var fr := v / maxf(kg * float((fish[species] as Dictionary)["base_reales_per_kg"]), 0.0001)
	var xs := float(x.get(species, 0.0))
	var rev := Market.sell_revenue(v, xs, float((fish[species] as Dictionary)["factor"]), spread, float(p["market.fish_depth_reales"]))
	var pay := round_half_up(rev)
	x[species] = Market.sell_x(v, xs, float(p["market.fish_depth_reales"]))
	var keep: Array = []
	for lot in lots:
		if str((lot as Array)[0]) != species:
			keep.append(lot)
	lots = keep
	reales += pay
	sold_total += pay
	sales_count += 1
	best_sale = maxi(best_sale, pay)
	return {"kg": kg, "reales": pay, "value_base": v, "fresh": fr}


## Sells every species (in id order). Returns {kg, reales, per: {species: reales}, rows: [{species, kg, reales, fresh, level}]}.
func sell_all(now: float) -> Dictionary:
	var total := 0
	var kg := 0.0
	var per: Dictionary = {}
	var rows: Array = []
	for sp in species_in_hold():
		var level := price_level(str(sp), now)
		var r := sell_species(str(sp), now)
		total += int(r["reales"])
		kg += float(r["kg"])
		per[str(sp)] = int(r["reales"])
		rows.append({"species": str(sp), "kg": float(r["kg"]), "reales": int(r["reales"]), "fresh": float(r["fresh"]), "level": level})
	return {"kg": kg, "reales": total, "per": per, "rows": rows}


# ---- hiring ---------------------------------------------------------------------------------------------------------
func cost_of(crew_id: String) -> int:
	return int((recruits[crew_id] as Dictionary)["cost"])


func is_hired(crew_id: String) -> bool:
	return crew.has(crew_id)


func can_afford(crew_id: String) -> bool:
	return reales >= cost_of(crew_id)


## "ok", "poor" or "already".
func hire(crew_id: String) -> String:
	if crew.has(crew_id):
		return "already"
	if reales < cost_of(crew_id):
		return "poor"
	reales -= cost_of(crew_id)
	crew.append(crew_id)
	return "ok"


func unhired() -> Array:
	var out: Array = []
	for c in recruit_order:
		if not crew.has(str(c)):
			out.append(str(c))
	return out


## The cheapest recruit not hired yet ("" when everybody is aboard).
func cheapest_unhired() -> String:
	var best := ""
	for c in unhired():
		if best == "" or cost_of(str(c)) < cost_of(best):
			best = str(c)
	return best


# ---- save format (kept compatible with GameState.to_dict by living in its own key) -------------------------------------
func to_dict() -> Dictionary:
	return {"reales": reales, "lots": lots.duplicate(true), "crew": crew.duplicate(), "x": x.duplicate(), "t_mkt": t_mkt,
			"sold_total": sold_total, "kg_total": kg_total, "best_sale": best_sale, "sales_count": sales_count}


func apply_dict(d: Dictionary) -> void:
	reales = int(d.get("reales", reales))
	lots = (d.get("lots", []) as Array).duplicate(true)
	crew.clear()
	for c in d.get("crew", []):
		crew.append(str(c))
	x = (d.get("x", {}) as Dictionary).duplicate()
	t_mkt = float(d.get("t_mkt", 0.0))
	sold_total = int(d.get("sold_total", 0))
	kg_total = float(d.get("kg_total", 0.0))
	best_sale = int(d.get("best_sale", 0))
	sales_count = int(d.get("sales_count", 0))
