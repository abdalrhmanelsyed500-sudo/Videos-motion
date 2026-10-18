extends RefCounted
## Market and money arithmetic (Module B4). Pure static functions with no state and no randomness.
## Python twin: tools/data_tools/market.py. Both run tests/fixtures/market_cases.json (hand-calculated).
## price = base_value x region_factor x exp(x) x (1 +/- spread/2)
##   region_factor : what the island produces (cheap) or lacks (dear); data on the island
##   x             : the market's memory of what YOU did there; selling pushes it down, buying pushes it up,
##                   and it halves every half-life (tuning market.recovery_half_life_days)
##   spread        : the merchant's margin; you buy at +spread/2 and sell at -spread/2
## Trading goods worth V (at base prices) moves x by V / depth, so a whole transaction has a closed form
## and splitting an order into pieces earns exactly the same money.
## HEAVY MONEY: a piece of eight weighs 27 g, a gold doubloon also 27 g but worth 16 pieces.
const REAL_WEIGHT_G := 27.0


## The market forgets: x halves every half_life_days.
static func decay(x: float, dt_days: float, half_life_days: float) -> float:
	return x * pow(0.5, dt_days / half_life_days)


static func price_multiplier(x: float) -> float:
	return exp(x)


## Money received for selling goods worth v_base at base prices. The new memory is x - v_base / depth.
static func sell_revenue(v_base: float, x: float, factor: float, spread: float, depth: float) -> float:
	return factor * (1.0 - spread / 2.0) * depth * exp(x) * (1.0 - exp(-v_base / depth))


static func sell_x(v_base: float, x: float, depth: float) -> float:
	return x - v_base / depth


## Money paid for buying goods worth v_base at base prices. The new memory is x + v_base / depth.
static func buy_cost(v_base: float, x: float, factor: float, spread: float, depth: float) -> float:
	return factor * (1.0 + spread / 2.0) * depth * exp(x) * (exp(v_base / depth) - 1.0)


static func buy_x(v_base: float, x: float, depth: float) -> float:
	return x + v_base / depth


## Weight of a purse of silver pieces, in kg.
static func coin_weight_kg(reales: float, real_g: float = REAL_WEIGHT_G) -> float:
	return reales * real_g / 1000.0


## A doubloon weighs the same as a piece of eight.
static func doubloon_weight_kg(doubloons: float, real_g: float = REAL_WEIGHT_G) -> float:
	return doubloons * real_g / 1000.0


## Changer, silver to gold. The fee comes off the value; whole doubloons only.
## Returns {"doubloons": int, "silver_left": int}. Never takes more silver than offered.
static func to_gold(reales: int, fee_pct: float, doubloon_value: float) -> Dictionary:
	var keep := 1.0 - fee_pct / 100.0
	var d := int(floor(float(reales) * keep / doubloon_value + 0.000000001))
	var spent := int(ceil(float(d) * doubloon_value / keep - 0.000000001))
	return {"doubloons": d, "silver_left": reales - spent}


## Changer, gold to silver. The fee comes off the value, rounded down.
static func to_silver(doubloons: int, fee_pct: float, doubloon_value: float) -> int:
	return int(floor(float(doubloons) * doubloon_value * (1.0 - fee_pct / 100.0) + 0.000000001))


## Divide a pool by shares (captain 2.0, officers 1.5, hands 1.0). The parts add up to the pool.
static func share_values(pool: float, shares: Array) -> Array[float]:
	var total := 0.0
	for s in shares:
		total += float(s)
	var out: Array[float] = []
	for s in shares:
		out.append(pool * float(s) / total if total > 0.0 else 0.0)
	return out


## What the shop window shows for one unit: {"buy": ..., "sell": ...} at the current memory.
static func quote(base_value: float, x: float, factor: float, spread: float) -> Dictionary:
	var mid := base_value * factor * exp(x)
	return {"buy": mid * (1.0 + spread / 2.0), "sell": mid * (1.0 - spread / 2.0)}


## Used by the fixture test: call a function by name with an argument array (JSON numbers arrive as floats).
static func call_case(fn: String, a: Array) -> Variant:
	var out: Variant = null
	match fn:
		"decay":
			out = decay(float(a[0]), float(a[1]), float(a[2]))
		"price_multiplier":
			out = price_multiplier(float(a[0]))
		"sell_revenue":
			out = sell_revenue(float(a[0]), float(a[1]), float(a[2]), float(a[3]), float(a[4]))
		"sell_x":
			out = sell_x(float(a[0]), float(a[1]), float(a[4]))
		"buy_cost":
			out = buy_cost(float(a[0]), float(a[1]), float(a[2]), float(a[3]), float(a[4]))
		"buy_x":
			out = buy_x(float(a[0]), float(a[1]), float(a[4]))
		"coin_weight_kg":
			out = coin_weight_kg(float(a[0]))
		"doubloon_weight_kg":
			out = doubloon_weight_kg(float(a[0]))
		_:
			out = _call_money_case(fn, a)
	return out


static func _call_money_case(fn: String, a: Array) -> Variant:
	var out: Variant = null
	match fn:
		"to_gold_doubloons":
			out = to_gold(int(a[0]), float(a[1]), float(a[2]))["doubloons"]
		"to_gold_left":
			out = to_gold(int(a[0]), float(a[1]), float(a[2]))["silver_left"]
		"to_silver":
			out = to_silver(int(a[0]), float(a[1]), float(a[2]))
		"share_value":
			out = share_values(float(a[0]), a[1])[int(a[2])]
	return out
