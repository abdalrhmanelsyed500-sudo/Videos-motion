extends RefCounted
## Market and money arithmetic (Module B4). Same fixture file as tools/data_tools/test_economy.py:
## the GDScript functions must give the same answers as the Python twin. Also checks the properties
## that make the market fair (no order trick, round trips lose, no randomness), and that the item and
## tuning data agree with the code (Heavy Money, no economic difficulty multiplier).
const Market := preload("res://core/market.gd")
const DataLoader := preload("res://core/data_loader.gd")
const Tuning := preload("res://core/tuning.gd")
const TOL := 0.0001


func run(t: Object) -> void:
	_fixture(t)
	_properties(t)
	_money(t)
	_data_matches_code(t)


func _fixture(t: Object) -> void:
	var fx := DataLoader.load_dict("res://tests/fixtures/market_cases.json")
	var cases: Array = fx.get("cases", [])
	t.check(cases.size() >= 40, "market fixture has >= 40 cases (has %d)" % cases.size())
	for c in cases:
		var got: Variant = Market.call_case(str(c["fn"]), c["args"])
		var want: float = float(c["expect"])
		var ok: bool = got != null and absf(float(got) - want) <= TOL * maxf(1.0, absf(want))
		t.check(ok, "market %s%s: expected %s, got %s" % [c["fn"], c["args"], want, got])


func _properties(t: Object) -> void:
	var r1: float = Market.sell_revenue(100.0, 0.0, 1.0, 0.2, 1000.0)
	var x1: float = Market.sell_x(100.0, 0.0, 1000.0)
	var r2: float = Market.sell_revenue(100.0, x1, 1.0, 0.2, 1000.0)
	var x2: float = Market.sell_x(100.0, x1, 1000.0)
	var whole: float = Market.sell_revenue(200.0, 0.0, 1.0, 0.2, 1000.0)
	t.check(absf(r1 + r2 - whole) < 0.000000001, "selling in two halves earns exactly what selling at once earns")
	t.check(absf(x2 - Market.sell_x(200.0, 0.0, 1000.0)) < 0.000000001, "two halves leave the same price memory")
	var paid: float = Market.buy_cost(300.0, 0.0, 1.0, 0.2, 1000.0)
	var xb: float = Market.buy_x(300.0, 0.0, 1000.0)
	var back: float = Market.sell_revenue(300.0, xb, 1.0, 0.2, 1000.0)
	t.check(back < paid, "buying a lot and selling it straight back always loses money")
	t.check(absf(Market.sell_x(300.0, xb, 1000.0)) < 0.000000001, "buy then sell leaves the memory where it began")
	var avg_small: float = Market.sell_revenue(100.0, 0.0, 1.0, 0.2, 1000.0) / 100.0
	var avg_big: float = Market.sell_revenue(500.0, 0.0, 1.0, 0.2, 1000.0) / 500.0
	t.check(avg_big < avg_small, "selling more never raises the average price")
	var a: float = Market.sell_revenue(77.0, -0.3, 1.2, 0.2, 900.0)
	var b: float = Market.sell_revenue(77.0, -0.3, 1.2, 0.2, 900.0)
	t.check(a == b, "no randomness: the same sale gives the same money")
	t.check(is_equal_approx(Market.decay(-1.0, 6.0, 6.0), -0.5), "the memory halves in one half-life")
	var q: Dictionary = Market.quote(10.0, 0.0, 1.0, 0.2)
	var window_ok: bool = is_equal_approx(float(q["buy"]), 11.0) and is_equal_approx(float(q["sell"]), 9.0)
	t.check(window_ok, "shop window: goods worth 10 buy at 11 and sell at 9 at spread 20 percent")


func _money(t: Object) -> void:
	var g: Dictionary = Market.to_gold(1000, 6.0, 16.0)
	t.check(int(g["doubloons"]) == 58 and int(g["silver_left"]) >= 0, "1000 silver changes to 58 doubloons")
	var silver_back: int = Market.to_silver(int(g["doubloons"]), 6.0, 16.0)
	t.check(silver_back < 1000 - int(g["silver_left"]), "a round trip through gold costs two fees")
	var none: Dictionary = Market.to_gold(10, 6.0, 16.0)
	var kept: bool = int(none["doubloons"]) == 0 and int(none["silver_left"]) == 10
	t.check(kept, "too little silver buys no gold and keeps all of it")
	for amount in [0, 1, 15, 16, 17, 100, 999, 1600, 123456]:
		var c: Dictionary = Market.to_gold(amount, 6.0, 16.0)
		var left: int = int(c["silver_left"])
		t.check(left >= 0 and left <= amount, "changer never takes more than offered (%d)" % amount)
	var shares: Array[float] = Market.share_values(1000.0, [2.0, 1.5, 1.5, 1.0, 1.0, 1.0])
	var total := 0.0
	for s in shares:
		total += s
	t.check(absf(total - 1000.0) < 0.000000001, "shares add up to the pool")
	var ranked: bool = shares[0] > shares[1] and shares[1] > shares[3]
	t.check(ranked, "captain gets more than an officer, an officer more than a hand")
	var empty: Array[float] = Market.share_values(500.0, [0.0, 0.0])
	t.check(empty[0] == 0.0, "no shares, no division by zero")
	t.check(is_equal_approx(Market.coin_weight_kg(6000.0), 162.0), "6000 pieces of eight weigh 162 kg")
	var gold_kg: float = Market.doubloon_weight_kg(375.0)
	t.check(gold_kg < Market.coin_weight_kg(6000.0) / 15.0, "the same wealth in gold is 16 times lighter")


## The code constant and the data must agree; difficulty modes must not touch money.
func _data_matches_code(t: Object) -> void:
	var reg: Node = load("res://core/registry.gd").new()
	reg.load_all()
	var normal: RefCounted = Tuning.from_registry(reg, "mode_normal")
	var hard: RefCounted = Tuning.from_registry(reg, "mode_hardcore")
	var story: RefCounted = Tuning.from_registry(reg, "mode_story")
	t.check(is_equal_approx(Market.REAL_WEIGHT_G, normal.f("coin.real_weight_g")), "coin weight in code = tuning")
	var coin: Dictionary = reg.record("item", "item_coin")
	var gold: Dictionary = reg.record("item", "item_doubloon")
	t.check(is_equal_approx(float(coin["weight_kg"]), Market.REAL_WEIGHT_G / 1000.0), "Piece of Eight item weighs 27 g")
	t.check(is_equal_approx(float(gold["weight_kg"]), Market.REAL_WEIGHT_G / 1000.0), "Gold Doubloon item weighs 27 g")
	var worth: float = normal.f("coin.doubloon_value_reales")
	t.check(is_equal_approx(float(gold["base_value"]), worth), "Doubloon value = tuning")
	var keys: Array[String] = ["market.spread_pct", "market.depth_reales_t1", "coin.changer_fee_pct", "pay.shares_captain",
		"market.recovery_half_life_days"]
	for key in keys:
		var same: bool = is_equal_approx(hard.f(key), normal.f(key)) and is_equal_approx(story.f(key), normal.f(key))
		t.check(same, "no difficulty mode scales %s (decision B4-9: no economic multiplier)" % key)
	reg.free()
