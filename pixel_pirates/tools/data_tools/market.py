"""Market and money arithmetic (Module B4): deterministic prices, saturation and recovery, coin weight, changer, crew shares.
GDScript twin: game/core/market.gd. Both are run against game/tests/fixtures/market_cases.json (hand-calculated).

The market model has NO randomness. A price is a product of visible factors:
    price = base_value x region_factor x exp(x) x (1 +/- spread/2)
  region_factor : what this island produces (cheap) or lacks (dear), data on the island
  x             : the market's memory of what YOU did there (selling pushes x down, buying pushes it up), decays with a half-life
  spread        : the merchant's margin; you buy at +spread/2 and sell at -spread/2
Trading V (in base value) moves x by V/depth, so the exact money for a whole transaction has a closed form."""
from __future__ import annotations

import math

SILVER_REAL_G = 27.0  # one silver piece of eight


def decay(x: float, dt_days: float, half_life_days: float) -> float:
    """The market forgets: x halves every half_life_days."""
    return x * 0.5 ** (dt_days / half_life_days)


def price_multiplier(x: float) -> float:
    return math.exp(x)


def sell(v_base: float, x: float, factor: float, spread: float, depth: float) -> tuple[float, float]:
    """Sell goods worth v_base at base prices. Returns (money received, new x). Selling pushes the price down."""
    revenue = factor * (1.0 - spread / 2.0) * depth * math.exp(x) * (1.0 - math.exp(-v_base / depth))
    return revenue, x - v_base / depth


def buy(v_base: float, x: float, factor: float, spread: float, depth: float) -> tuple[float, float]:
    """Buy goods worth v_base at base prices. Returns (money paid, new x). Buying pushes the price up."""
    cost = factor * (1.0 + spread / 2.0) * depth * math.exp(x) * (math.exp(v_base / depth) - 1.0)
    return cost, x + v_base / depth


def coin_weight_kg(reales: float, real_g: float = SILVER_REAL_G) -> float:
    """Weight of a purse of silver pieces."""
    return reales * real_g / 1000.0


def doubloon_weight_kg(doubloons: float, real_g: float = SILVER_REAL_G) -> float:
    """A doubloon weighs the same as a piece of eight (27 g) and is worth many."""
    return doubloons * real_g / 1000.0


def to_gold(reales: float, fee_pct: float, doubloon_value: float) -> tuple[int, int]:
    """Changer: silver to doubloons. The fee is taken from the value; returns (doubloons, silver left over)."""
    net = reales * (1.0 - fee_pct / 100.0)
    d = int(math.floor(net / doubloon_value + 1e-9))
    return d, int(round(reales - math.ceil(d * doubloon_value / (1.0 - fee_pct / 100.0) - 1e-9)))


def to_silver(doubloons: int, fee_pct: float, doubloon_value: float) -> int:
    """Changer: doubloons to silver, fee taken from the value, rounded down."""
    return int(math.floor(doubloons * doubloon_value * (1.0 - fee_pct / 100.0) + 1e-9))


def share_values(pool: float, shares: list[float]) -> list[float]:
    """Divide a pool by shares (captain 2.0, officers 1.5, hands 1.0); the parts add up to the pool exactly (to the cent)."""
    total = sum(shares)
    return [pool * s / total for s in shares]


def shuttle_best(v_cap: float, depth: float, factor_pair: tuple[float, float], spread: float, half_life: float, leg_days: float,
                 legs: int = 120) -> float:
    """Best repeatable profit per game day for a two-port shuttle that trades one good each leg: buy at the producer (factor_pair[0]),
    sell at the consumer (factor_pair[1]), and runs the legs back and forth forever with market memory. Searches the trade size."""
    best = 0.0
    v_cap = min(v_cap, 3.0 * depth)  # beyond three market depths the price collapses; also keeps exp() finite
    for k in range(1, 61):
        v = v_cap * k / 60.0
        xp, xd, profit = 0.0, 0.0, 0.0
        for _ in range(legs):
            cost, xp = buy(v, xp, factor_pair[0], spread, depth)
            rev, xd = sell(v, xd, factor_pair[1], spread, depth)
            profit = rev - cost
            xp, xd = decay(xp, leg_days, half_life), decay(xd, leg_days, half_life)
        best = max(best, profit / leg_days)  # profit of the last (steady-state) leg per day of that leg
    return best


FUNCS = {"decay": decay, "price_multiplier": price_multiplier, "coin_weight_kg": coin_weight_kg, "doubloon_weight_kg": doubloon_weight_kg,
         "to_silver": to_silver, "sell_revenue": lambda *a: sell(*a)[0], "sell_x": lambda *a: sell(*a)[1],
         "buy_cost": lambda *a: buy(*a)[0], "buy_x": lambda *a: buy(*a)[1], "to_gold_doubloons": lambda *a: to_gold(*a)[0],
         "to_gold_left": lambda *a: to_gold(*a)[1], "share_value": lambda pool, shares, i: share_values(pool, shares)[int(i)]}
