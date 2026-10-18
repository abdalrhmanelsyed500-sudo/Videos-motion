# MODULE B4: Economy - "Heavy Money"

**Status:** designed, machine-checked in Python, GDScript written but NOT run (no Godot in the build sandbox). All numbers are PROVISIONAL (owners: B4, B5, B6, F1, N-modules).
**Goal:** one money system that makes every voyage a sum (P2), keeps the player poor enough that supplies matter and rich enough to grow, and cannot be ground.
**Deliverables:** this document; `core/market.gd` (+ Python twin `tools/data_tools/market.py`); `tools/data_tools/economy_model.py` (the numbers, as a checked model); 61 tuning records (`tuning_economy.json`); 9 new trade items and 9 icons; 40 hand-calculated market cases; tests in Python and GDScript.

## 1. The original idea: HEAVY MONEY

In most games money is a number. Here **money is cargo**. A silver piece of eight weighs 27 g, as the real coin did. A gold doubloon also weighs 27 g but is worth 16 pieces: **gold is 16 times denser wealth**, and the changer takes 6 percent each way to swap.

An honest finding from the model, and the reason the idea is shaped the way it is: with a 15-minute day, a ship costs only about ten days of running cost, so *pocket* coin is light (the mid-game ship, 1,200 reales, is 32 kg of silver). Weight does not bite on a purse. It bites on **windfalls**: wrecks, caches and ruins pay in **silver bars** (10 kg, 370 reales each). A start-stage windfall is 6 bars = **60 kg = 2,220 reales = one full day of the crew's stores** (55 kg/day for 12 men). Now every rich find is a real choice:

1. take the silver and sail with a day less of water, or
2. pay the changer 133 reales (6 percent) to turn it into 130 doubloons (3.5 kg) and keep the day, or
3. leave some behind and come back.

Nothing else in the game weighs on the same scale as "the loot or the water barrel". That is the pirate fantasy and the logistics pillar in one object. (Not a cliche: no "treasure chest = number goes up".)

**The second idea: the market remembers you.** There is no random price noise. A price is `base value x region factor x exp(x) x (1 +/- spread/2)`. `x` is the market's memory of what *you* did there: selling pushes it down, buying pushes it up, and it halves every 6 game days (1.5 real hours). The player can read it ("the harbour master's ledger"), so P2 holds: every number behind a trade is visible before committing, and the same trade gives the same result.

## 2. Options weighed (decisions B4-x)

| # | Question | Options | Recommended and chosen |
|---|---|---|---|
| B4-1 | What is money? | A) a counter; B) every coin has weight; C) a counter plus weight only for bullion | **B**, but with the coin kept as a single item (`item_coin`, 27 g). The counter is only a view of the coins aboard. |
| B4-2 | How do prices move? | A) random events; B) deterministic memory of your trades (chosen); C) fixed prices | **B.** A and C either cannot be planned (breaks P2/P3) or are trivially solved. |
| B4-3 | Who gets paid? | A) fixed wages; B) loot shares; C) both | **B.** Shares from **prize income only** (combat prizes, salvage, treasure) are 30 percent of it, split captain 2.0 / officer 1.5 / hand 1.0, paid every 10 game days (2.5 real hours). **Trade profit is never shared** (it is the captain's business, so trade cannot starve morale and the crew cannot demand a cut of it). Food is not a wage. |
| B4-4 | How big is a safe sale? | 10, 20 or 40 percent of a market's depth | **20 percent** (`market.safe_sale_fraction`). Beyond it the average price falls visibly: a sale of one full depth returns 57 percent (`1 - 1/e`, then the spread). |
| B4-5 | How is trade capped? | A) by hold size; B) by market depth (chosen) | **B.** (At the very start the small hold is about as tight as the market; later only depth binds.) Depth: Tier 1 4,500, Tier 2 2,200, Tier 3 1,100 reales of base value (x1 / x1.9 / x3.2 by ship stage). A fuller hold does not make a better run. |
| B4-6 | How is grinding stopped? | A) cooldowns; B) the memory itself (chosen) | **B.** Hopping between two ports leaves both prices depressed for 6 days. The checked best endless shuttle earns 14 reales/day at the start against a running cost of 73. No cooldown timers exist (anti-pillar: no hidden timers). |
| B4-7 | Does risk pay? | no; yes | **Yes.** A Dead Ocean landfall has never been picked over: salvage and treasure x1.5 (`dead.untouched_mult`). It is the reason to prepare for the crossing (E9). |
| B4-8 | Difficulty? | multiplier on prices; none | **None.** Money has no difficulty multiplier. Story and Hardcore change the food bill only through hunger (N1), and a test checks it. |
| B4-9 | What about upgrades? | fixed prices now | **Anchors only.** B5 sets real prices; an invariant keeps the mid ship at 2-12 and the late ship at 3-16 hours of play. |
| B4-10 | Starting purse | 300 / 600 / 1,200 | **600 reales** (8 days of running cost, 16 kg of silver): enough to provision a first voyage, not enough to skip the early game. |

## 3. The numbers (all provisional)

**Coins and items** (value per kg shows who is "dense"):

| item | value | weight | per kg |
|---|---|---|---|
| Piece of Eight (silver) | 1 | 0.027 kg | 37 |
| Silver bar | 370 | 10 kg | 37 |
| Gold Doubloon | 16 | 0.027 kg | 593 |
| Pearls | 60 | 0.1 kg | 600 |
| Salt / Sugar / Cloth / Tobacco / Furs / Spice | 1 / 6 / 14 / 22 / 40 / 90 | 1 kg each | 1 / 6 / 14 / 22 / 40 / 90 |

Order rule: salt < sugar < cloth < tobacco < silver < furs < spice < gold < pearls. The cheap goods are the cheap way to carry value; spice and furs beat silver per kilo; gold beats all but pearls.

**Prices re-baselined** (reales): hardtack 2, salt meat 5, fresh fish 2, water barrel 6, grog 3, gunpowder 30, cannonball 5, lime 4, bandage 3, rope 8, plank 7, tar 10, canvas 14, hammer 15, fishing line 4. The **ration basket** (hardtack, meat, lime, grog, water for one man for one day) costs **3.58 reales**.

**Running cost per game day** (food + wages-in-kind 1/man + upkeep + expected repairs):

| ship stage | crew (officers) | food | misc | upkeep | repairs | **total** |
|---|---|---|---|---|---|---|
| Start | 12 (3) | 43.0 | 12 | 8 | 9.6 | **72.6** |
| Mid | 20 (5) | 71.6 | 20 | 45 | 24 | **160.6** |
| Late | 30 (7) | 107.4 | 30 | 85 | 48 | **270.4** |

**Income per game day, campaign average** (B2 cycle mix 25/40/25/10):

| stage | income | trade share | share pool | per hand-day | net | surplus | net per real minute |
|---|---|---|---|---|---|---|---|
| Start | 127 | 30% | 23.9 | 1.65 | 30.8 | 42% | 2.05 |
| Mid | 243 | 31% | 45.4 | 1.93 | 37.1 | 23% | 2.48 |
| Late | 409 | 31% | 76.5 | 2.22 | 62.6 | 23% | 4.17 |

**One cycle at the start stage** (every term from the model):

| cycle | gross | trade | salvage | treasure | prize | catch | cost | shares | net | net per real min |
|---|---|---|---|---|---|---|---|---|---|---|
| Hop | 109 | 21 | 30 | 39 | 13 | 6 | 66 | 25 | +18 | 1.35 |
| Passage | 262 | 65 | 45 | 94 | 40 | 18 | 153 | 54 | +55 | 1.74 |
| Crossing | 670 | 231 | 80 | 211 | 102 | 46 | 377 | 118 | +175 | 2.24 |
| Dead Ocean | 1,088 | 338 | 120 | 316 | 216 | 97 | 607 | 196 | +285 | 2.27 |

Reading: **no voyage type is a trap and none is a best answer** (per real minute they sit within 1.35-2.27), and the long, prepared voyage pays a little more per minute *and* a lot more per voyage, because that is the risk.

**Savings time:** mid ship 1,200 reales = about **9.8 hours** of start-stage play; late ship 2,200 = about **14.8 hours** of mid-stage play. A small upgrade (400) is about 4 cycles at start-stage surplus.

**Windfall chest** (silver bars; scales with region wealth): start 6 bars 60 kg 2,220 reales (1.1 days of stores); mid 11.4 bars 114 kg 4,218 reales (1.2 days); late 19.2 bars 192 kg 7,104 reales (1.4 days). Chance per visit: Tier 1 5 percent, Tier 2 2 percent, Tier 3 0.5 percent. A chest never exceeds half the trade hold (400 / 1,100 / 2,600 kg).

## 4. Worked example (every figure reproducible with `economy_model.py`)

*A start-stage Crossing, 2.83 game days (42.5 real minutes), Tier 1 to Tier 1.*
- Distance gives a price gap of `0.6 + 0.12 x 2.83 = 0.94`, so the producer's factor is 0.718 and the consumer's 1.393 (their ratio is 1.94).
- The safe lot is 20 percent of 4,500 = 900 reales of base value, but the starter hold is tighter: 400 kg x 0.6 full x 3.5 reales/kg (salt and sugar) = **840 reales**. So at the start the *hold* binds a little; from the mid-game ship on, the market depth binds (B4-5).
- Buy 840: `0.718 x 1.10 x 4500 x (e^(840/4500) - 1) = 729 reales`. Sell: `1.393 x 0.90 x 4500 x (1 - e^(-840/4500)) = 961 reales`. **Profit 231** (the 231 in the table). The producer's memory moves to +0.187 and the consumer's to -0.187.
- Do it again straight away: you pay about 21 percent more and sell about 17 percent lower, so profit collapses. Wait 6 days and half of that memory is gone. Wait 12 and three quarters.
- The whole cycle (the 2.83-day voyage plus the island visit, 5.2 game days, 78 real minutes) costs 377 reales to run. The trade is 231 of 670 income. **You cannot live on trade alone, and you cannot live without it.**

*Share day (every 10 game days = 2.5 real hours).* 12 crew, 14.5 shares. Prize income of 800 over the period gives a pool of 240: captain 33.1, each officer 24.8, each hand 16.6 reales. A pool of zero pays zero and the crew's mood says so (B6/N8 decide the consequence; the money rule is only that the pool is exact to the cent).

*A windfall.* 6 silver bars (60 kg). The starter hold carries 8 days of stores (442 kg) and a 400 kg trade hold; if the chest takes stores space, it leaves **6.9 days** of stores. Changing it to gold costs 133 reales and weighs 3.5 kg. The decision is the game.

## 5. Pillar gate (docs/templates/PILLAR_GATE.md)

| # | Pillar | Answer | Evidence |
|---|---|---|---|
| 1 | P1 The sea is the game | **yes** | Trade profit scales with the voyage length (the price gap grows 0.12 per day); the Dead Ocean premium rewards the longest crossings. Short hops are never the best answer (invariant). |
| 2 | P2 Every voyage is a sum | **yes** | Prices are deterministic and visible (`quote()`); the memory `x` is readable; the model prints a cost and income for every voyage type. |
| 3 | P3 Hard but fair | **yes** | No random price shocks; windfalls are rare but never required (chance 5/2/0.5 percent); the running cost is covered with a 23-42 percent surplus; the Warning Ladder (48/16/6 h) is untouched. Recovery: sell stock, change coin, leave loot, fish. |
| 4 | P4 A ship is people | **yes** | The crew is paid in shares from prize income only; the Quartermaster (D-module) will read the pool. Share day is a visible event. |
| 5 | P5 Every island answers a question | n/a | (content) Each island's market role (producer/consumer) is a data field for E3/F. |
| 6 | P6 The map pulls you | **yes** | Dense goods and the Dead Ocean premium give a reason to go farther; a chart is cargo (150 reales). |

Hard content rules: no female crew OK, no sexual content OK, no gods or religion OK (no character, item or text added; the content-word lint passes).

## 6. What is machine-checked

`economy_model.invariants()` runs inside `tools/check_project.py` and `check_all.py`. It checks, among others: coin weights equal 27 g; doubloon worth 16; goods ordered by density; gold the densest legal cargo; windfall chest 0.5-3 days of stores and under half the hold, and gold under a tenth of its weight; changer round trip 6-25 percent; spread 10-35 percent; depth falls by tier; every safe trade run profits; surplus 15-45 percent per stage; trade 25-55 percent of income; share per hand-day within 60-160 percent of 1.5; no cycle loses more than 10 percent of its cost; Dead Ocean pays more than a Crossing and within 3x of a Hop per minute; **no endless shuttle earns more than the running cost** (it simulates 120 legs with market memory); the market never forgets faster than one Hop; share rules; upgrade savings times; chart price; starting purse 6-12 days.
`tools/data_tools/test_economy.py` has 46 test lines: the 40 hand-calculated cases (as one), properties (splitting an order changes nothing, a round trip always loses), and about 30 mutation tests proving each invariant fires. `game/tests/test_market.gd` runs the same fixture file in Godot.

## 7. Risks and what is NOT verified

- **GDScript has not run.** `market.gd` and `test_market.gd` pass gdlint and gdparse only.
- **The model is an average, not a playthrough.** Real income is spiky (windfalls, combat). The mean can be right and the first ten hours still feel wrong.
- **A start-stage windfall (2,220) is worth about two mid ships (1,200).** One lucky chest skips a stage. Either B5 prices the ship higher, or the chance at Tier 1 drops. I kept the numbers coherent with the model and flagged it for B5.
- **The starting purse (600) cannot fund a full 900-reales lot.** The first trades are smaller and the player ramps up; that is intended but unplayed.
- The ship prices are anchors; real values belong to B5. The share consequences belong to B6/N8. Chart pricing belongs to E8.
- Prices of re-baselined items are provisional until N1-N10 finalize the survival numbers.
- No UI exists for the ledger or the changer yet (J-modules).

## 8. Godot tests to run on your PC

1. `tools\run_godot_tests.bat` (or `.sh`). Expect `== test_market.gd` followed by no `FAIL` lines.
2. If a market case fails, the line names the function, the arguments, the expected and the got value; send me that line.
3. Re-import once (`--import`) so the 9 new icons are known; `test_assets.gd` should then pass with 50 assets in the manifest (it only requires 30 or more).
