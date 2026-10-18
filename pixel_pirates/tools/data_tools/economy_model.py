"""Economy arithmetic (Module B4): what the ship costs per game day, what each voyage cycle earns, whether the numbers hold together.
Builds on the B2/T1 loop model (cycle lengths) and the T1 clock. Prints the tables used in docs/B4_ECONOMY.md.

  python tools/data_tools/economy_model.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import design_checks as D  # noqa: E402
import loop_model as LM  # noqa: E402
import market as M  # noqa: E402

STAGES = ("start", "mid", "late")
STAGE_GOODS = {"start": ("item_salt", "item_sugar"), "mid": ("item_cloth", "item_tobacco"), "late": ("item_furs", "item_spice")}
TIER_DEPTH = {1: "market.depth_reales_t1", 2: "market.depth_reales_t2", 3: "market.depth_reales_t3"}
# surplus the economy must leave the player after costs and shares, as a fraction of running cost (Normal difficulty)
SURPLUS_MIN, SURPLUS_MAX = 0.15, 0.45
NEED = ["coin.real_weight_g", "coin.doubloon_value_reales", "coin.changer_fee_pct", "market.spread_pct", "market.depth_reales_t1",
        "market.depth_reales_t2", "market.depth_reales_t3", "market.recovery_half_life_days", "market.safe_sale_fraction",
        "market.differential_base", "market.differential_per_day", "market.differential_cap", "ration.salt_meat_kg_per_man_day",
        "ration.lime_kg_per_man_day", "ration.grog_kg_per_man_day", "ration.water_l_per_man_day", "food.hardtack_kg_per_man_day",
        "running.misc_per_man_day", "repair.cost_per_hull_pct", "repair.expected_damage_pct_per_day", "repair.cost_mult_mid",
        "repair.cost_mult_late", "trade.cargo_fill_fraction", "salvage.fraction_of_islands", "prize.reales_per_combat_minute",
        "catch.reales_per_sea_minute", "stage.wealth_mult_mid", "stage.wealth_mult_late", "pay.share_pool_pct_of_prize", "pay.shares_captain",
        "pay.shares_officer", "pay.shares_hand", "pay.interval_game_days", "pay.expected_share_per_hand_day", "info.chart_price_t1_region",
        "upgrade.price_small", "upgrade.price_mid_ship", "upgrade.price_late_ship", "time.real_minutes_per_game_day"]
NEED += [f"{p}_{s}" for p in ("crew.size", "crew.officers", "running.upkeep_per_day", "ship.trade_capacity_kg") for s in STAGES]
NEED += [f"{p}_t{n}" for p in ("salvage.value", "treasure.value", "treasure.windfall_chance") for n in (1, 2, 3)]
NEED += ["treasure.windfall_bars", "dead.untouched_mult", "start.purse_reales"]


def load_items(data_dir: Path = D.DATA) -> dict[str, dict]:
    d = json.loads((data_dir / "items" / "items.json").read_text())
    return {r["id"]: r for r in d["records"]}


def wealth(t: dict, stage: str) -> float:
    return {"start": 1.0, "mid": t["stage.wealth_mult_mid"], "late": t["stage.wealth_mult_late"]}[stage]


def repair_mult(t: dict, stage: str) -> float:
    return {"start": 1.0, "mid": t["repair.cost_mult_mid"], "late": t["repair.cost_mult_late"]}[stage]


def basket_per_man_day(t: dict, items: dict) -> float:
    """Reales per man per game day for the shipboard ration basket at base prices."""
    bv = {k: v["base_value"] for k, v in items.items()}
    water_per_l = bv["item_water_barrel"] / items["item_water_barrel"]["capacity_l"]
    return (t["food.hardtack_kg_per_man_day"] * bv["item_hardtack"] + t["ration.salt_meat_kg_per_man_day"] * bv["item_salt_meat"]
            + t["ration.lime_kg_per_man_day"] * bv["item_lime"] + t["ration.grog_kg_per_man_day"] * bv["item_grog"]
            + t["ration.water_l_per_man_day"] * water_per_l)


def running_cost_per_day(t: dict, items: dict, stage: str) -> dict:
    n = t[f"crew.size_{stage}"]
    food = n * basket_per_man_day(t, items)
    misc = n * t["running.misc_per_man_day"]
    upkeep = t[f"running.upkeep_per_day_{stage}"]
    repairs = t["repair.expected_damage_pct_per_day"] * t["repair.cost_per_hull_pct"] * repair_mult(t, stage)
    return {"food": food, "misc": misc, "upkeep": upkeep, "repairs": repairs, "total": food + misc + upkeep + repairs}


def factor_pair(t: dict, days: float) -> tuple[float, float]:
    """(producer factor, consumer factor) for two regions this many game days apart: cheap origin, dear destination."""
    r = 1.0 + min(t["market.differential_cap"], t["market.differential_base"] + t["market.differential_per_day"] * days)
    return 1.0 / math.sqrt(r), math.sqrt(r)


def trade_profit(t: dict, items: dict, stage: str, tier: int, days: float) -> float:
    """Profit of one fresh-market trade run: buy at the producer, sell at the consumer (both of this tier), real market maths."""
    w = wealth(t, stage)
    depth = t[TIER_DEPTH[tier]] * w
    goods = [items[g]["base_value"] for g in STAGE_GOODS[stage]]
    density = sum(goods) / len(goods) * w if stage != "start" else sum(goods) / len(goods)
    cargo_value = t[f"ship.trade_capacity_kg_{stage}"] * t["trade.cargo_fill_fraction"] * density
    v = min(cargo_value, t["market.safe_sale_fraction"] * depth)
    spread = t["market.spread_pct"] / 100.0
    fp, fc = factor_pair(t, days)
    cost, _ = M.buy(v, 0.0, fp, spread, depth)
    rev, _ = M.sell(v, 0.0, fc, spread, depth)
    return rev - cost


def cycle_income(t: dict, items: dict, stage: str, name: str) -> dict:
    c = LM.cycle(t, name)
    w, tier = wealth(t, stage), c["tier"]
    trade = trade_profit(t, items, stage, tier, c["days"])
    um = t["dead.untouched_mult"] if name == "dead" else 1.0   # a Dead Ocean landfall has never been picked over
    salvage = um * t["salvage.fraction_of_islands"] * t[f"salvage.value_t{tier}"] * w
    windfall = t[f"treasure.windfall_chance_t{tier}"] * windfall_value(t, items, stage)
    treasure = um * (t[f"treasure.value_t{tier}"] * w + windfall)
    prize = t["prize.reales_per_combat_minute"] * c["combat"] * w
    catch = t["catch.reales_per_sea_minute"] * c["sea"] * w
    shared = salvage + treasure + prize
    return {"cycle": c, "trade": trade, "salvage": salvage, "treasure": treasure, "prize": prize, "catch": catch,
            "gross": trade + shared + catch, "shared_income": shared}


def windfall_bars(t: dict, stage: str) -> float:
    """A windfall is a chest of silver bars; later regions are richer, so the chest is bigger (value and weight grow together)."""
    return t["treasure.windfall_bars"] * wealth(t, stage)


def windfall_value(t: dict, items: dict, stage: str) -> float:
    return windfall_bars(t, stage) * items["item_silver_bar"]["base_value"]


def windfall_weight_kg(t: dict, items: dict, stage: str) -> float:
    return windfall_bars(t, stage) * items["item_silver_bar"]["weight_kg"]


def stores_kg_per_day(t: dict, items: dict, stage: str) -> float:
    """Mass of one day of full-crew stores: dry ration, grog, lime, and the water barrels (barrel weight per litre)."""
    n = t[f"crew.size_{stage}"]
    dry = t["food.hardtack_kg_per_man_day"] + t["ration.salt_meat_kg_per_man_day"] + t["ration.lime_kg_per_man_day"] + t["ration.grog_kg_per_man_day"]
    barrel = items["item_water_barrel"]
    return n * (dry + t["ration.water_l_per_man_day"] * barrel["weight_kg"] / barrel["capacity_l"])


def share_count(t: dict, stage: str) -> float:
    n, o = t[f"crew.size_{stage}"], t[f"crew.officers_{stage}"]
    return t["pay.shares_captain"] + o * t["pay.shares_officer"] + (n - 1 - o) * t["pay.shares_hand"]


def stage_economy(t: dict, items: dict, stage: str) -> dict:
    """Campaign-average economy per game day for a ship stage, using the B2 cycle mix."""
    run = running_cost_per_day(t, items, stage)
    tot = {"gross": 0.0, "shared": 0.0, "days": 0.0, "minutes": 0.0, "trade": 0.0, "catch": 0.0}
    per = {}
    for name, (_, _, _, mk) in LM.ARCH.items():
        wt = t[mk] / 100.0
        ci = cycle_income(t, items, stage, name)
        cyc = ci["cycle"]
        days = cyc["total_days"]
        pool = t["pay.share_pool_pct_of_prize"] / 100.0 * ci["shared_income"]
        net = ci["gross"] - run["total"] * days - pool
        per[name] = {"gross": ci["gross"], "cost": run["total"] * days, "pool": pool, "net": net, "days": days, "minutes": cyc["total"],
                     "net_per_day": net / days, "net_per_min": net / cyc["total"], "income": ci}
        tot["gross"] += wt * ci["gross"]
        tot["shared"] += wt * ci["shared_income"]
        tot["days"] += wt * days
        tot["minutes"] += wt * cyc["total"]
        tot["trade"] += wt * ci["trade"]
        tot["catch"] += wt * ci["catch"]
    pool_day = t["pay.share_pool_pct_of_prize"] / 100.0 * tot["shared"] / tot["days"]
    income_day = tot["gross"] / tot["days"]
    net_day = income_day - run["total"] - pool_day
    shares = share_count(t, stage)
    return {"stage": stage, "run": run, "income_day": income_day, "pool_day": pool_day, "net_day": net_day, "surplus_ratio": net_day / run["total"],
            "share_per_hand_day": pool_day / shares, "shares": shares, "trade_day": tot["trade"] / tot["days"],
            "trade_share": tot["trade"] / tot["gross"], "per": per, "cycle_days": tot["days"], "cycle_minutes": tot["minutes"],
            "net_per_min": net_day * tot["days"] / tot["minutes"]}


def best_shuttle_per_day(t: dict, items: dict, stage: str, tier: int, days: float) -> float:
    w = wealth(t, stage)
    depth = t[TIER_DEPTH[tier]] * w
    goods = [items[g]["base_value"] for g in STAGE_GOODS[stage]]
    density = sum(goods) / len(goods) * (w if stage != "start" else 1.0)
    v_cap = t[f"ship.trade_capacity_kg_{stage}"] * t["trade.cargo_fill_fraction"] * density
    return M.shuttle_best(v_cap, depth, factor_pair(t, days), t["market.spread_pct"] / 100.0, t["market.recovery_half_life_days"], days)


def e_run_start(t: dict, items: dict) -> float:
    return running_cost_per_day(t, items, "start")["total"]


def invariants(t: dict, items: dict) -> list[str]:
    miss = [k for k in NEED if k not in t]
    if miss:
        return [f"economy: missing tuning keys {miss}"]
    p: list[str] = []
    # --- heavy money -----------------------------------------------------------------------------------------------------
    real_kg = t["coin.real_weight_g"] / 1000.0
    if abs(items["item_coin"]["weight_kg"] - real_kg) > 1e-9 or abs(items["item_doubloon"]["weight_kg"] - real_kg) > 1e-9:
        p.append("economy: the Piece of Eight and the Gold Doubloon items must weigh coin.real_weight_g")
    if items["item_coin"]["base_value"] != 1 or items["item_doubloon"]["base_value"] != t["coin.doubloon_value_reales"]:
        p.append("economy: the coin is worth 1 and the doubloon coin.doubloon_value_reales in the item data")
    if t["coin.doubloon_value_reales"] <= 1:
        p.append("economy: gold must be worth more than silver")
    for a in ("item_silver_bar", "item_pearls"):
        if items[a]["category"] != "treasure":
            p.append(f"economy: {a} must be a treasure item")
    if abs(items["item_silver_bar"]["base_value"] - items["item_silver_bar"]["weight_kg"] / real_kg) > 1.0:
        p.append("economy: a silver bar must be worth the same per kg as silver coin")
    d_silver = 1.0 / real_kg
    d_gold = t["coin.doubloon_value_reales"] / real_kg
    densities = {g: items[g]["base_value"] / items[g]["weight_kg"] for g in ("item_salt", "item_sugar", "item_cloth", "item_tobacco", "item_furs", "item_spice")}
    ordered = list(densities.values())
    if ordered != sorted(ordered) or len(set(ordered)) != len(ordered):
        p.append("economy: trade goods must be ordered salt < sugar < cloth < tobacco < furs < spice by value per kg")
    if max(ordered[:4]) >= d_silver:
        p.append("economy: salt, sugar, cloth and tobacco must be less dense wealth than silver coin (bulk goods are the cheap way to carry value)")
    if max(ordered) >= d_gold:
        p.append("economy: no trade good may be denser in value than gold; gold is the densest legal cargo short of pearls")
    if items["item_pearls"]["base_value"] / items["item_pearls"]["weight_kg"] <= d_silver:
        p.append("economy: pearls must be denser wealth than silver")
    for st in STAGES:
        days = windfall_weight_kg(t, items, st) / stores_kg_per_day(t, items, st)
        if not 0.5 <= days <= 3.0:
            p.append(f"economy: a {st}-stage windfall chest weighs {days:.2f} days of stores; it must be 0.5-3 (heavy enough to force a choice, light enough to carry)")
        if windfall_weight_kg(t, items, st) > 0.5 * t[f"ship.trade_capacity_kg_{st}"]:
            p.append(f"economy: a {st}-stage windfall chest may not fill half the trade hold")
        gold_kg = M.doubloon_weight_kg(windfall_value(t, items, st) / t["coin.doubloon_value_reales"], t["coin.real_weight_g"])
        if gold_kg > 0.1 * windfall_weight_kg(t, items, st):
            p.append("economy: the same windfall in gold must weigh under a tenth of the bullion (gold is the dense option)")
    start_days = t["ship.stores_hold_days_start"]
    chest_days = windfall_weight_kg(t, items, "start") / stores_kg_per_day(t, items, "start")
    if chest_days >= start_days / 4:
        p.append("economy: a start-stage windfall may not eat a quarter of the stores hold")
    fee_cost = windfall_value(t, items, "start") * t["coin.changer_fee_pct"] / 100.0
    if fee_cost > 0.6 * e_run_start(t, items) * start_days:
        p.append("economy: converting a windfall to gold may not cost more than 60 percent of the starter hold's days of running cost")
    purse_days = t["start.purse_reales"] / e_run_start(t, items)
    if not 6.0 <= purse_days <= 12.0:
        p.append(f"economy: the starting purse covers {purse_days:.1f} days of running cost; it must be 6-12 (a first voyage, no skipping the early game)")
    if 2 * t["coin.changer_fee_pct"] < 6 or 2 * t["coin.changer_fee_pct"] > 25:
        p.append("economy: the changer round trip must cost between 6 and 25 percent")
    # --- prices and the market ---------------------------------------------------------------------------------------------
    sp = t["market.spread_pct"]
    if not 10 <= sp <= 35:
        p.append("economy: the merchant spread must be 10-35 percent")
    if not t["market.depth_reales_t1"] > t["market.depth_reales_t2"] > t["market.depth_reales_t3"] > 0:
        p.append("economy: market depth must fall with the island tier (T1 > T2 > T3)")
    cap = t["market.safe_sale_fraction"]
    for tier in (1, 2, 3):
        pr = trade_profit(t, items, "start", tier, LM.cycle(t, {1: "crossing", 2: "passage", 3: "hop"}[tier])["days"])
        if pr <= 0:
            p.append(f"economy: a safe trade run to a Tier {tier} island must make a profit at the start (got {pr:.1f})")
    # --- running cost, income, shares -------------------------------------------------------------------------------------
    basket = basket_per_man_day(t, items)
    if not 3.0 <= basket <= 4.5:
        p.append(f"economy: the ration basket costs {basket:.2f} reales per man-day; it must stay between 3.0 and 4.5")
    prev_run = 0.0
    for s in STAGES:
        e = stage_economy(t, items, s)
        if e["run"]["total"] <= prev_run:
            p.append("economy: running cost per day must grow with the ship stage")
        prev_run = e["run"]["total"]
        if not SURPLUS_MIN <= e["surplus_ratio"] <= SURPLUS_MAX:
            p.append(f"economy: {s}-stage surplus is {100 * e['surplus_ratio']:.0f} percent of running cost; it must be {int(SURPLUS_MIN * 100)}-{int(SURPLUS_MAX * 100)}")
        if not 0.25 <= e["trade_share"] <= 0.55:
            p.append(f"economy: {s}-stage trade is {100 * e['trade_share']:.0f} percent of income; it must be 25-55 (trade is a livelihood, not the only one)")
        exp = t["pay.expected_share_per_hand_day"]
        if not 0.6 * exp <= e["share_per_hand_day"] <= 1.6 * exp:
            p.append(f"economy: {s}-stage share per hand-day is {e['share_per_hand_day']:.2f}; the crew expects {exp} (within 60-160 percent)")
        for name, c in e["per"].items():
            if c["net"] < -0.1 * c["cost"]:
                p.append(f"economy: a {name} cycle at {s} stage loses {-c['net']:.0f} reales ({100 * -c['net'] / c['cost']:.0f} percent of its cost); too ruinous")
        hop, dead = e["per"]["hop"], e["per"]["dead"]
        if dead["net"] <= e["per"]["crossing"]["net"]:
            p.append(f"economy: at {s} stage a Dead Ocean cycle must pay more than a Crossing (risk pays)")
        if not 0.5 <= dead["net_per_min"] / max(1e-9, hop["net_per_min"]) <= 3.0 if hop["net_per_min"] > 0 else False:
            p.append(f"economy: at {s} stage income per real minute of Dead Ocean must be within 0.5-3x of a Hop (no best voyage type)")
    # --- anti-grind: the best endless shuttle may not out-earn the livelihood ----------------------------------------------------
    for s in STAGES:
        run = running_cost_per_day(t, items, s)["total"]
        for tier, name in ((1, "crossing"), (2, "passage"), (3, "hop")):
            days = LM.cycle(t, name)["days"]
            sh = best_shuttle_per_day(t, items, s, tier, days)
            if sh > 1.0 * run:
                p.append(f"economy: an endless Tier {tier} shuttle at {s} stage earns {sh:.0f} reales/day, more than the running cost {run:.0f}: a grind exists")
    if t["market.recovery_half_life_days"] < LM.cycle(t, "hop")["total_days"]:
        p.append("economy: the market must not forget faster than one Hop cycle, or hopping back and forth resets prices")
    # --- shares ---------------------------------------------------------------------------------------------------------------
    if not t["pay.shares_captain"] >= t["pay.shares_officer"] >= t["pay.shares_hand"] >= 1.0:
        p.append("economy: shares must be captain >= officer >= hand >= 1")
    if t["pay.shares_captain"] > 3.0:
        p.append("economy: the captain's shares may not exceed 3 hand shares")
    for s in STAGES:
        if t[f"crew.officers_{s}"] >= t[f"crew.size_{s}"] - 1:
            p.append(f"economy: {s}-stage officers must be fewer than the hands")
    if not t["crew.size_start"] < t["crew.size_mid"] < t["crew.size_late"]:
        p.append("economy: crew size must grow start < mid < late")
    if t["pay.interval_game_days"] * t["time.real_minutes_per_game_day"] < 60:
        p.append("economy: share day may come at most once per real hour")
    if t["pay.interval_game_days"] < LM.cycle(t, "crossing")["days"]:
        p.append("economy: share day must be at least a Crossing apart, or pay interrupts every voyage")
    # --- upgrades are reachable --------------------------------------------------------------------------------------------------
    e0, e1 = stage_economy(t, items, "start"), stage_economy(t, items, "mid")
    mid_hours = t["upgrade.price_mid_ship"] / max(1e-9, e0["net_per_min"] * 60.0)
    if not 2.0 <= mid_hours <= 12.0:
        p.append(f"economy: saving for the mid-game ship takes {mid_hours:.1f} hours of start-stage play; it must be 2-12")
    late_hours = t["upgrade.price_late_ship"] / max(1e-9, e1["net_per_min"] * 60.0)
    if not 3.0 <= late_hours <= 16.0:
        p.append(f"economy: saving for the late-game ship takes {late_hours:.1f} hours of mid-stage play; it must be 3-16")
    if t["upgrade.price_small"] / max(1e-9, e0["net_day"] * e0["cycle_days"]) > 8:
        p.append("economy: a small upgrade may not take more than 8 start-stage cycles to afford")
    chart_days = t["info.chart_price_t1_region"] / max(1e-9, e0["net_day"])
    if chart_days > 6.0:
        p.append("economy: a chart must cost no more than 6 days of start-stage surplus (information is cargo, it must be affordable)")
    return p


def report(t: dict, items: dict) -> str:
    L = []
    b = basket_per_man_day(t, items)
    L.append(f"ration basket: {b:.2f} reales per man per game day at base prices")
    L.append("| stage | crew | food | misc | upkeep | repairs | running/day |")
    L.append("|---|---|---|---|---|---|---|")
    for s in STAGES:
        r = running_cost_per_day(t, items, s)
        L.append(f"| {s} | {t[f'crew.size_{s}']:.0f} | {r['food']:.1f} | {r['misc']:.1f} | {r['upkeep']:.1f} | {r['repairs']:.1f} | **{r['total']:.1f}** |")
    L.append("")
    L.append("| stage | income/day | trade | shared (prizes+salvage+treasure) pool/day | share per hand-day | net/day | surplus | net per real min | cycle min |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for s in STAGES:
        e = stage_economy(t, items, s)
        L.append(f"| {s} | {e['income_day']:.0f} | {100 * e['trade_share']:.0f}% | {e['pool_day']:.1f} | {e['share_per_hand_day']:.2f} | {e['net_day']:.1f} | "
                 f"{100 * e['surplus_ratio']:.0f}% | {e['net_per_min']:.2f} | {e['cycle_minutes']:.0f} |")
    L.append("")
    L.append("| cycle (start stage) | gross | trade | salvage | treasure | prize | catch | cost | shares | net | net/real min |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    e = stage_economy(t, items, "start")
    for name, c in e["per"].items():
        i = c["income"]
        L.append(f"| {name} | {c['gross']:.0f} | {i['trade']:.0f} | {i['salvage']:.0f} | {i['treasure']:.0f} | {i['prize']:.0f} | {i['catch']:.0f} | "
                 f"{c['cost']:.0f} | {c['pool']:.0f} | {c['net']:.0f} | {c['net_per_min']:.2f} |")
    L.append("")
    for s in STAGES:
        run = running_cost_per_day(t, items, s)["total"]
        L.append(f"best endless shuttle at {s} stage: " + ", ".join(
            f"T{tier} {best_shuttle_per_day(t, items, s, tier, LM.cycle(t, n)['days']):.0f}/day" for tier, n in ((1, 'crossing'), (2, 'passage'), (3, 'hop')))
            + f" (running cost {run:.0f}/day)")
    return "\n".join(L)


def main() -> int:
    t, items = D.load_tuning(), load_items()
    print(report(t, items))
    prob = invariants(t, items)
    print("\nproblems:", prob or "none")
    return 1 if prob else 0


if __name__ == "__main__":
    sys.exit(main())
