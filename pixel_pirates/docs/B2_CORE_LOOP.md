# B2 - Core Loop: Crown of the Seas (working title)

Status: DESIGN, binding. Built on the B1 pillars. Numbers marked `[tuning]` live in `game/data/tuning/tuning_loop.json` (provisional, each with an owner module) and are checked against the B1 pillars by `tools/data_tools/loop_model.py`. The ship's clock exists as code: `core/voyage_clock.gd` (GDScript, unrun) and `tools/data_tools/voyage_clock.py`, both tested against one hand-written fixture.

## 0. The loop in one line
**PLAN the sum -> SAIL the days -> ANSWER the island -> PROVISION -> collect the CLUE -> PLAN again.** One average turn of this wheel takes **40 real minutes**, passes **9.1 game days at sea**, and always ends with something new in the Log.

## 1. Five nested loops
| loop | length (real time, default) | what happens | what it must deliver |
|---|---|---|---|
| L1 Moment | 5-60 s | one thing on the sea or shore: an ambient sight, a choice, or a crisis | never more than **4 min** (`loop.max_quiet_minutes`) of nothing |
| L2 Watch | **24 s** at sea (4 game hours) | the bell strikes, the watch changes, fatigue ticks, the crew roster rotates | rhythm and crew life (P4) |
| L3 Day | **2.4 min** at sea (`time.real_minutes_per_game_day`) | **the Morning Report** at eight bells of the Morning watch (08:00) | the Reckoning updated; one decision card |
| L4 Voyage | 3-90 min (B1 bands) | PLAN, DEPART, SAIL, LANDFALL | a sum answered (P2), a payoff (P6) |
| L5 Visit | 6-45 min exploring + 2 min provisioning | LAND, ASK, ACT, ANSWER, PROVISION, CLUE | the island's question answered (P5) |
Above these sit the campaign (acts, regions, the Crown): owners B5/B7/B8.

## 2. The original idea: EIGHT BELLS (the Morning Report)
Real ships were run by bells: a bell every half hour, **eight bells** at the end of a four-hour watch. Here the bell is the game's heartbeat, and **eight bells of the Morning watch (08:00) is the only fixed pause in the voyage**: the **Morning Report**.
- It is **a pause screen** (B1-2: planning screens stop the clock), so it never steals sailing time. Target reading time **20 s** (`loop.report_max_seconds`).
- It is the **only place where fast-forward always stops**, together with every ladder rung and every crisis. So the x4 button is safe: you can never sleep through a warning.
- It is **written by the ship, in the captain's log voice**, so the Log of the whole voyage writes itself, and the ending can read the Log back to the player: the memory of the game is the journey itself.
- The player's rhythm is therefore a **chain of short days**, each ending in a report and a small decision, with long uninterrupted stretches in between to look at the sea.

### Layout of a Morning Report (6 blocks, all fit one screen)
1. **Header:** `Day 9. Eight bells, Morning watch.` Distance run, bearing, **next landfall as a band** (`4-6 days`, narrowed by the navigator and charts).
2. **Stocks:** each stock as *days left at current consumption*, with its ladder colour (green, advisory, warning, critical) and the change since yesterday.
3. **Ship:** hull percent, leak rate in litres per hour, sail and rigging note.
4. **Crew:** the single most urgent line from the role that feels it most (P4).
5. **Sea:** the 24 h outlook as a band (wind, swell, rain chance) and what it does to the voyage band.
6. **One decision card, if any:** 2-3 options, each with its cost shown (P2, P3).
Then the Log line, written automatically. Buttons: **Continue (x1)**, **Continue x4** (disabled while any rung is lit), **Open the Reckoning**.

### Sample report (day 9 of a 14-day Crossing, 12 men; every number comes from the simulation, the crew line is picked by rules from the role who feels it most)
> **Day 9. Eight bells, Morning watch.** 118 km run, bearing 205. Landfall in **4-6 days**.
> **Hardtack** 6.8 days (advisory). **Water** 10.2 days. **Powder** dry. **Hull** 97 percent, leak 6 L/h.
> *Surgeon:* "One man in the forepeak with fever. The water in the aft barrel is turning, Captain. I would boil it before anyone drinks."
> **Decision:** boil the aft barrel (uses 2 days of wood, saves the barrel) / drink it and risk fever / throw it over and run short.
> *Log:* "Day 9. Hardtack seven days. Water ten. One fever in the forepeak. Wind steady south-west."

## 3. The moments rule (what happens in L1)
Every stretch of sea is built from three kinds of moment:
| kind | what | per 10 real min at sea `[tuning]` |
|---|---|---|
| ambient | a sight or sound with no demand: gulls over a shoal, a whale blow, a distant sail, a wreck | as many as the region needs (free) |
| choice | a real decision with a visible cost: turn for a shoal of fish, fly the colours or hide, spend a day mending | at least **2** (`loop.choice_moments_per_10min`) |
| crisis | a ladder rung, a storm, a fight | at most **1** (`loop.crisis_moments_per_10min_max`) |
No gap longer than **4 min** without a moment at x1 (`loop.max_quiet_minutes`). The Morning Report counts as a moment, and since a day lasts 2.4 min, the report alone already satisfies the rule; moments fill the time between. Dead Ocean keeps the same rule with a different flavour (calm, drift, strange water, signs of other ships): "dead" means no islands, not no events.

## 4. The voyage loop (L4)
1. **PLAN** (pause, about 2 min): open the Reckoning (B1). Choose route, ration, watch plan, cargo. See the band and the margin.
2. **DEPART:** weigh anchor; the crew's roster is set. The first Morning Report arrives within the first game day (even a 3-min Hop crosses 08:00).
3. **SAIL:** watches, reports, moments. The player steers, trims, fishes, fights, mends, talks.
4. **LANDFALL:** the first sight of land comes with a **question card** hinting at the island's question without spoiling the answer (P5).
5. **ANCHOR:** choose a landing (islands have several landings, A6).

## 5. The visit loop (L5), built on the A6 island slots
1. **LAND** at one of the landings.
2. **ASK:** read the question (for example *"Can I afford a day to lift a wreck?"*).
3. **ACT:** the five A6 slot kinds in play: *survival* (the offer the island must have), *hook* (the memorable thing), *secret*, *story*, *camp* (the shore day for the crew).
4. **ANSWER:** the hook resolves with consequences.
5. **PROVISION:** load, trade, repair, pay shares; the ship's needs are re-sums.
6. **CLUE:** the payoff is written into the Log and the chart (P6); the next route becomes visible.
Rule: **an island may not cost more than one game day of supplies** (see section 6), so a visit is a fair, plannable expense.

## 6. Time: two clocks
| | at sea | ashore | `[tuning]` |
|---|---|---|---|
| clock | 1 game day = **2.4 real min** (watch 24 s) | 1 game day = **60 real min** (**24 game min per real min**) | `time.real_minutes_per_game_day`, `time.ashore_game_minutes_per_real_minute`, owner N13 |
| why | a 14-day crossing = 33.6 min, a Crossing; a 70-day scurvy clock = 168 min | a full Tier 1 visit (45 min) = **18 game hours**; Tier 2 (16 min) = 6.4 h; Tier 3 (6 min) = 2.4 h | |
The first draft had one clock: at 2.4 min per day a 45-minute island would have eaten **19 game days** of food. Ashore therefore runs 25 times slower than at sea, a choice recorded as B2-1.
Conversions (proved by the fixture): 1 game hour at sea = 6 s; one watch = 24 s; 14 days = 33.6 min; 37.5 days = 90 min (the longest Dead Ocean); 30 days = 72 min (water goes foul); 70 days = 168 min (scurvy).
Fast-forward at sea is **x4** (`time.accel_fast_factor`) and drops to x1 at every rung, crisis and Morning Report.

## 7. Does the loop deliver the pillars? (computed, not promised)
Archetypes, each ending at a tier of island, averaged over the campaign mix (`loop_model.py`):

| cycle | mix | to island tier | voyage min | game days | island min | ship+crew min | combat min | cycle min |
|---|---|---|---|---|---|---|---|---|
| hop | 25% | T3 | 5.5 | 2.3 | 3.6 | 5.1 | 0.4 | 13.1 |
| passage | 40% | T2 | 14.0 | 5.8 | 9.6 | 6.8 | 1.1 | 27.6 |
| crossing | 25% | T1 | 32.5 | 13.5 | 27.0 | 10.5 | 2.6 | 63.5 |
| dead | 10% | T1 | 67.5 | 28.1 | 27.0 | 17.5 | 5.4 | 98.5 |
| **campaign average** | 100% | | 21.9 | 9.1 | | | | **40.0** |

Result: **sea 39.3 %, islands 35.4 %, ship and crew 20.9 %, combat 4.4 %** against the B1 targets of 40 / 35 / 17 / at most 8. The ship-and-crew share lands above its 17 % centre but inside its allowed range of 10-25 %; combat is well under its cap. B7 tunes this after the vertical slice. Every number comes from `tuning_loop.json`, and `check_project.py` fails if the loop stops delivering the pillars.

Consequences the arithmetic exposed (information flags, intended, handed to the owners):
- **Visiting all 50 islands takes about 33 hours of play** (50 cycles x 40 min) and about 455 game days. B8 decides the real route length (a story route of about 30 islands is about 20 hours).
- **Dead Ocean is a preparation puzzle by arithmetic:** the longest crossing is **37.5 game days**; 12 men need **1,125 L** of water at the minimum ration, and water goes foul after **30 warm days (72 min)**, before the crossing ends. Rain catching, boiling or a spring is therefore *required*. Owners: N4 (water), N10 (cargo weight).
- **Scurvy clock:** 70 days without fruit is **168 minutes** of sailing, about two long Dead Ocean crossings back to back. Islands with `fruit` or `herbs` must appear at least once every few cycles (N5, E3).
- **An average island visit costs 6.5 game hours** including provisioning; a full Tier 1 visit costs 18 h, never more than one day.

## 8. Failure and recovery inside the loop (P3)
The wheel never dead-ends. From any state there is at least one route to the next payoff:
- **Short on stock at sea:** the Warning Ladder (B1) opens options before the loss; Hop and Passage voyages are always reachable from known charted springs.
- **Becalmed or off course:** the Reckoning's band widens on dead ocean, never hides; drifting, fishing and rain catching keep a ship alive.
- **Ship lost:** B1-1 fair-loss model. The castaway recovery (survivors on a shore with a salvage loop back to a hull) is designed in B6; B2 only requires that it re-enters the wheel at PLAN.
- **A bad island:** leaving is always possible; the only price is the supplies already spent (never more than one game day).

## 9. The first loop teaches the whole wheel (B7 will script it)
The first cycle is a **Hop** (3-8 min) with a large margin: one Reckoning with only two stocks, one Morning Report (the first is auto-explained), one Tier 3 island, one clue. The second cycle is a **Passage** where a stock goes advisory so the player meets rung 1 safely. The first full Crossing comes only after the player has met all three rungs once, each with its recovery options.

## 10. Decisions (options and recommendation)
**B2-1. Time scale.** At sea: (A) 1.2 min per game day: a 14-day crossing is 16.8 min (a Passage), reports every 72 s, a watch lasts 12 s, scurvy is 84 min. (B) **2.4 min per game day (recommended, adopted):** a 14-day crossing is 33.6 min (a Crossing), a report every 2.4 min, a watch 24 s, scurvy 168 min. (C) 4.8 min: a 14-day crossing is 67 min (Dead Ocean), a watch 48 s, scurvy 336 min. Ashore: (A) 12 game min per real min (1 day = 120 min), (B) **24 (recommended, adopted: 1 day = 60 min, a full Tier 1 visit = 18 h)**, (C) 48 (1 day = 30 min). N13 finalises both numbers.
**B2-2. Daily Morning Report.** (A) HUD only, no report. (B) **A pause screen at eight bells, 20 s to read (recommended, adopted).** (C) A full captain's-log text each day: too slow, too repetitive.
**B2-3. Island cost.** (A) free exploring, (B) a hard daily limit, (C) **consumption continues ashore at the same rates on the ashore clock, and a full visit never costs more than one day (recommended, adopted).**

## 11. Pillar Gate for B2 (docs/templates/PILLAR_GATE.md)
| pillar | result | evidence |
|---|---|---|
| P1 sea is the game | yes | sea is the largest share (39.3 %); no quiet stretch above 4 min; the Morning Report breaks every 2.4 min |
| P2 sum | yes | the Reckoning at PLAN and in the report; the island cost rule keeps visits plannable |
| P3 fair | yes | fast-forward always stops at rungs, crises and the report; recovery paths in section 8 |
| P4 people | yes | the report always carries one crew line |
| P5 island question | yes | LANDFALL question card, ASK, ANSWER |
| P6 map pulls | yes | every cycle ends with CLUE; the Log writes itself |
Original idea: Eight Bells. No pirate cliche: the heartbeat is naval bookkeeping, not a parrot.

## 12. Open for later modules
N13 final time scales and the sailing times; E2 the moment tables per region and the exact quiet window; B5 how clues and upgrades carry between cycles; B6 castaway recovery and mode-specific rescue; B7 the scripted first hour and whether the 21 % ship-and-crew share holds; B8 the route length.

## 13. How B2 is enforced
`python tools/check_all.py` fails if: the cycle mix does not total 100; the modelled sea, island or ship-and-crew share leaves its pillar range; combat exceeds its cap; the sea has less than the islands; a game day is longer than the quiet limit; the shortest voyage has no Morning Report; the watch length does not divide 24; crises outnumber choices; the report cannot be read in 30 s; the 14-day example stops being a Crossing; a Tier 1 visit costs more than one day or less than a quarter day. The 46 tests in `test_design_checks.py` (B1 and B2 together) prove each rule fires, plus a 50-case clock fixture that the Python and the GDScript clock must both match (GDScript unrun).
