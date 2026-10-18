"""Tests for market.py and economy_model.py (Module B4). Run: python tools/data_tools/test_economy.py"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import design_checks as D  # noqa: E402
import economy_model as E  # noqa: E402
import market as M  # noqa: E402

fails = 0


def expect(name: str, cond: bool, detail: str = "") -> None:
    global fails
    print(("ok   " if cond else "FAIL ") + name + ("" if cond else f"  {detail}"))
    fails += 0 if cond else 1


T = D.load_tuning()
IT = E.load_items()

# ---- hand-calculated fixtures (shared with game/tests/test_market.gd) --------------------------------------------------------
cases = json.loads((D.ROOT / "game" / "tests" / "fixtures" / "market_cases.json").read_text())["cases"]
bad = []
for c in cases:
    got = M.FUNCS[c["fn"]](*c["args"])
    if abs(got - c["expect"]) > 1e-4 * max(1.0, abs(c["expect"])):
        bad.append((c["fn"], c["args"], got, c["expect"]))
expect(f"all {len(cases)} hand-calculated market cases match", not bad, str(bad[:3]))

# ---- properties of the market maths -------------------------------------------------------------------------------------------
rev1, x1 = M.sell(100, 0, 1, 0.2, 1000)
rev2, x2 = M.sell(100, x1, 1, 0.2, 1000)
rev_all, x_all = M.sell(200, 0, 1, 0.2, 1000)
expect("selling in two halves earns exactly what selling at once earns (no order trick)", abs(rev1 + rev2 - rev_all) < 1e-9 and abs(x2 - x_all) < 1e-12)
cost, xb = M.buy(300, 0, 1, 0.2, 1000)
back, xs = M.sell(300, xb, 1, 0.2, 1000)
expect("buying and selling the same lot straight back always loses money (spread plus slippage)", back < cost)
expect("buy-then-sell round trip leaves x where it started", abs(xs) < 1e-12)
expect("price memory halves every half-life", abs(M.decay(-1, 6, 6) + 0.5) < 1e-12)
expect("selling more never raises the average price", M.sell(500, 0, 1, 0.2, 1000)[0] / 500 < M.sell(100, 0, 1, 0.2, 1000)[0] / 100)
expect("no randomness: the same call returns the same number", M.sell(77, -0.3, 1.2, 0.2, 900) == M.sell(77, -0.3, 1.2, 0.2, 900))
expect("an enormous order stays finite", math.isfinite(M.shuttle_best(1e9, 100.0, (0.8, 1.2), 0.2, 6.0, 1.0)))
gold, left = M.to_gold(1000, 6, 16)
expect("changer to gold: 1000 silver -> 58 doubloons, change is non-negative", gold == 58 and left >= 0, f"{gold} {left}")
expect("gold then back to silver always costs value (two fees)", M.to_silver(gold, 6, 16) < 1000 - left)
sh = M.share_values(1000.0, [2.0, 1.5, 1.5, 1.0, 1.0, 1.0])
expect("shares add up to the pool exactly", abs(sum(sh) - 1000.0) < 1e-9 and sh[0] == max(sh))

# ---- the real numbers satisfy every invariant ---------------------------------------------------------------------------------
expect("real tuning satisfies every economy invariant", E.invariants(T, IT) == [], str(E.invariants(T, IT)))
expect("items: a Piece of Eight weighs 27 g and a Doubloon is worth 16", IT["item_coin"]["weight_kg"] == 0.027 and IT["item_doubloon"]["base_value"] == 16)
expect("items: a silver bar is worth exactly its weight in coin", abs(IT["item_silver_bar"]["base_value"] / IT["item_silver_bar"]["weight_kg"] - 1 / 0.027) < 1.0)


def broken(items=None, **kw):
    t = dict(T)
    t.update(kw)
    return E.invariants(t, items or IT)


def has(word: str, **kw) -> bool:
    return any(word in x for x in broken(**kw))


# ---- mutation tests: every guard really trips ---------------------------------------------------------------------------------
expect("missing keys are reported", any("missing" in x for x in E.invariants({}, IT)))
expect("too-thin margins are caught (spread 5%)", has("spread", **{"market.spread_pct": 5}))
expect("hugely thick spread is caught", has("spread", **{"market.spread_pct": 60}))
expect("a trade run that loses money is caught", has("make a profit", **{"market.differential_base": 0.05, "market.differential_per_day": 0.0}))
expect("a huge differential makes a grind and is caught", has("grind", **{"market.differential_base": 2.0, "market.differential_cap": 3.0, "market.depth_reales_t1": 40000}))
expect("income far below cost is caught", has("surplus", **{"catch.reales_per_sea_minute": 0.0, "salvage.value_t1": 10, "salvage.value_t2": 5, "salvage.value_t3": 2}))
expect("income far above cost is caught", has("surplus", **{"prize.reales_per_combat_minute": 400}))
expect("a market that forgets in a day is caught", has("forget", **{"market.recovery_half_life_days": 0.1}))
expect("a changer that is free is caught", has("changer", **{"coin.changer_fee_pct": 0.5}))
expect("a changer that robs is caught", has("changer", **{"coin.changer_fee_pct": 20}))
expect("ship prices out of reach are caught", has("mid-game ship", **{"upgrade.price_mid_ship": 60000}))
expect("a giveaway ship is caught", has("mid-game ship", **{"upgrade.price_mid_ship": 10}))
expect("captain on 4 shares is caught", has("captain", **{"pay.shares_captain": 4.0}))
expect("a share pool that robs the ship is caught", has("share per hand", **{"pay.share_pool_pct_of_prize": 95}))
expect("a share pool of nothing is caught", has("share per hand", **{"pay.share_pool_pct_of_prize": 2}))
expect("pay every game day is caught", has("share day", **{"pay.interval_game_days": 1}))
expect("a risk-free dead ocean (no premium) is caught", has("risk pays", **{"dead.untouched_mult": 1.0}))
expect("a windfall chest of lead (200 bars) is caught", has("windfall", **{"treasure.windfall_bars": 200}))
expect("a windfall chest of feathers (0.1 bar) is caught", has("windfall", **{"treasure.windfall_bars": 0.1}))
light = {k: dict(v) for k, v in IT.items()}
light["item_coin"]["weight_kg"] = 0.001
expect("weightless coin is caught (heavy money)", any("must weigh" in x for x in broken(light)))
cheap_gold = {k: dict(v) for k, v in IT.items()}
cheap_gold["item_doubloon"]["base_value"] = 1
expect("gold worth the same as silver is caught", any("doubloon" in x.lower() for x in broken(cheap_gold)))
rich_salt = {k: dict(v) for k, v in IT.items()}
rich_salt["item_salt"]["base_value"] = 90
expect("a bulk good denser than silver is caught", any("ordered" in x or "bulk goods" in x for x in broken(rich_salt)))
dense_spice = {k: dict(v) for k, v in IT.items()}
dense_spice["item_spice"]["base_value"] = 900
expect("a trade good denser than gold is caught", any("denser" in x for x in broken(dense_spice)))
expect("crew size must grow", has("crew size", **{"crew.size_mid": 10}))

# ---- the model itself ---------------------------------------------------------------------------------------------------------
sp = [E.stage_economy(T, IT, s) for s in E.STAGES]
expect("running cost grows with stage", sp[0]["run"]["total"] < sp[1]["run"]["total"] < sp[2]["run"]["total"])
expect("ration basket is about 3.6 reales per man-day", 3.4 <= E.basket_per_man_day(T, IT) <= 3.8)
expect("food is the largest running cost at the start", sp[0]["run"]["food"] > max(sp[0]["run"]["misc"], sp[0]["run"]["upkeep"], sp[0]["run"]["repairs"]))
expect("a pricier ration raises the running cost (no hidden constant)", E.running_cost_per_day({**T, "ration.salt_meat_kg_per_man_day": 0.8}, IT, "start")["total"] > sp[0]["run"]["total"])
expect("windfall chest at the start weighs about a day of stores", 0.8 <= E.windfall_weight_kg(T, IT, "start") / E.stores_kg_per_day(T, IT, "start") <= 1.6)
expect("shares come only from prizes, salvage and treasure, not from trade", all(abs(sp[i]["pool_day"] - T["pay.share_pool_pct_of_prize"] / 100 * sum(
    T[f"loop.mix_{n}_pct"] / 100 * sp[i]["per"][n]["income"]["shared_income"] for n in ("hop", "passage", "crossing", "dead")) / sp[i]["cycle_days"]) < 1e-6 for i in range(3)))

print("economy tests:", "PASS" if not fails else f"{fails} FAILED")
sys.exit(1 if fails else 0)
