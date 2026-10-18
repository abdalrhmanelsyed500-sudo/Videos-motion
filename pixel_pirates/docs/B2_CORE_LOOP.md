# B2 - Core Loop: Crown of the Seas (working title)

Status: DESIGN, binding. **Revised by patch T1 (one world clock, see `T1_TIME_SYSTEM.md`).** Built on the B1 pillars. Numbers marked `[tuning]` live in `game/data/tuning/` (provisional, each with an owner module) and are checked against the B1 pillars by `tools/data_tools/loop_model.py`. The clock exists as code: `core/voyage_clock.gd` + `core/world_clock.gd` (GDScript, unrun) and `tools/data_tools/voyage_clock.py`, tested against two hand-written fixtures.

What T1 changed in this file: the two-clock model (sea 2.4 min/day, ashore 60 min/day), the one-day visit cap, the x4 fast-forward and "the report breaks the quiet" are **removed**. One clock now runs everywhere: **1 game day = 15 real minutes**.

## 0. The loop in one line
**PLAN the sum -> SAIL the days -> ANSWER the island -> PROVISION -> collect the CLUE -> PLAN again.** One average turn of this wheel takes **48 real minutes**, which is **3.2 game days** (1.8 of them at sea), and always ends with something new in the Log.

## 1. Five nested loops
| loop | length (real time, default) | what happens | what it must deliver |
|---|---|---|---|
| L1 Moment | 5-60 s | one thing on the sea or shore: an ambient sight, a choice, or a crisis | never more than **4 min** (`loop.max_quiet_minutes`) of nothing |
| L2 Watch | **150 s** (4 game hours) | the watch bell strikes, the watch changes, fatigue ticks, the crew roster rotates | rhythm and crew life (P4) |
| L3 Day | **15 min** (`time.real_minutes_per_game_day`), at sea and ashore | dawn to night, one full day/night cycle; **the Morning Report** at eight bells of the Morning watch (08:00) | the Reckoning updated; one decision card |
| L4 Voyage | 3-120 min = 0.2-8 game days (T1 bands) | PLAN, DEPART, SAIL, LANDFALL | a sum answered (P2), a payoff (P6) |
| L5 Visit | 6-45 min exploring + 2 min provisioning (0.4-3 game days) | LAND, ASK, ACT, ANSWER, PROVISION, CLUE | the island's question answered (P5) |
Above these sit the campaign (acts, regions, the Crown): owners B5/B7/B8.

## 2. The original idea: EIGHT BELLS (the Morning Report)
Real ships were run by bells: a bell every half hour, **eight bells** at the end of a four-hour watch. Here the bell is the game's heartbeat, and **eight bells of the Morning watch (08:00) is the only fixed pause in the day**: the **Morning Report**.
- **Audio (T1):** a half-hour is 18.75 real seconds, so a bell on every half hour would be constant noise. By default **only the watch-end bell (eight bells) is audible, every 150 s**; the half-hour bells show as a small HUD tick and can be turned on in the options. The 08:00 report opens on a full eight bells.
- It is **a pause screen** (planning screens stop the clock; paused time advances nothing), so it never steals sailing time. Target reading time **20 s** (`loop.report_max_seconds`), at most 3 percent of a game day.
- It is **no longer a safety net for fast-forward**, because there is no fast-forward: time runs at one fixed rate. Safety comes from the Warning Ladder alone, which is measured in game hours (48 / 16 / 6) and always gives at least 2 real minutes to act at the last rung.
- It is **written by the ship, in the captain's log voice**, so the Log of the whole voyage writes itself, and the ending can read the Log back to the player: the memory of the game is the journey itself.
- The player's rhythm is therefore a **chain of 15-minute days**, each with its sunrise, its report and a small decision, with long uninterrupted stretches in between to look at the sea. A short Hop may not contain a report at all; reports come when the clock reaches 08:00, wherever the ship is.

### Layout of a Morning Report (6 blocks, all fit one screen)
1. **Header:** `Day 3. Eight bells, Morning watch.` Distance run, bearing, **next landfall as a band in hours or days** (`6-42 hours`, narrowed by the navigator and charts).
2. **Stocks:** each stock as *time left at current consumption* (days above 2, hours below), with its ladder colour (green, advisory, warning, critical) and the change since yesterday.
3. **Ship:** hull percent, leak rate in litres per hour, sail and rigging note.
4. **Crew:** the single most urgent line from the role that feels it most (P4).
5. **Sea:** the 24 h outlook as a band (wind, swell, rain chance) and what it does to the voyage band.
6. **One decision card, if any:** 2-3 options, each with its cost shown (P2, P3).
Then the Log line, written automatically. Buttons: **Continue**, **Open the Reckoning**. (There is no "x4".)

### Sample report (day 3 of a 3-day Crossing, 12 men, a ship that sailed a little short on water; every number comes from the simulation, the crew line is picked by rules from the role who feels it most)
> **Day 3. Eight bells, Morning watch.** 118 km run, bearing 205. Landfall in **6-42 hours**.
> **Hardtack** 1.9 days (advisory). **Water** 32 hours (advisory; worst-case landfall is 42 hours). **Powder** dry. **Hull** 99 percent, leak 2 L/h.
> *Surgeon:* "The men are quiet, Captain, and quiet men are thirsty men. Another forty-two hours on this ration and I will not answer for the forepeak."
> **Decision:** cut the water ration to two thirds (the crew tires faster) / catch rain (showers likely in about 12 hours; every barrel counts) / press on and trust the short end of the band.
> *Log:* "Day 3. Hardtack two days. Water a day and a third. Showers to the west by noon, if we are lucky."

## 3. The moments rule (what happens in L1)
Every stretch of sea is built from three kinds of moment:
| kind | what | per 10 real min at sea `[tuning]` |
|---|---|---|
| ambient | a sight or sound with no demand: gulls over a shoal, a whale blow, a distant sail, a wreck | as many as the region needs (free) |
| choice | a real decision with a visible cost: turn for a shoal of fish, fly the colours or hide, spend a day mending | at least **2** (`loop.choice_moments_per_10min`) |
| crisis | a ladder rung, a storm, a fight | at most **1** (`loop.crisis_moments_per_10min_max`) |
No gap longer than **4 min** without a moment (`loop.max_quiet_minutes`). The Morning Report counts as a moment, but with a 15-minute day it comes only once per 15 minutes, so **moments, not reports, carry the rule**: E2 must fill every region with enough moments for any 4-minute window. Night sailing counts: a moment at night is a lantern on the water, a dark shape, a change of wind, not a loss of visibility alone. Dead Ocean keeps the same rule with a different flavour (calm, drift, strange water, signs of other ships): "dead" means no islands, not no events.

## 4. The voyage loop (L4)
1. **PLAN** (pause, about 2 min): open the Reckoning (B1). Choose route, ration, watch plan, cargo. See the band and the margin.
2. **DEPART:** weigh anchor; the crew's roster is set. The time of day at departure is part of the plan (leaving at dusk means a night passage).
3. **SAIL:** watches, bells, reports, moments, nights. The player steers, trims, fishes, fights, mends, talks.
4. **LANDFALL:** the first sight of land comes with a **question card** hinting at the island's question without spoiling the answer (P5).
5. **ANCHOR:** choose a landing (islands have several landings, A6).

## 5. The visit loop (L5), built on the A6 island slots
1. **LAND** at one of the landings.
2. **ASK:** read the question (for example *"Can I afford a day to lift a wreck?"*).
3. **ACT:** the five A6 slot kinds in play: *survival* (the offer the island must have), *hook* (the memorable thing), *secret*, *story*, *camp* (the shore day for the crew).
4. **ANSWER:** the hook resolves with consequences.
5. **PROVISION:** load, trade, repair, pay shares; the ship's needs are re-sums.
6. **CLUE:** the payoff is written into the Log and the chart (P6); the next route becomes visible.
Rule (T1, replaces the one-day cap): **time ashore is the same time as at sea, so a visit costs real supplies.** A full Tier 1 visit (45 min) costs **3.0 game days**, Tier 2 (16 min) 1.07, Tier 3 (6 min) 0.4; the typical visit (70 percent of the budget) costs 2.1 / 0.75 / 0.28. The cap is `loop.visit_cost_days_max` = 3.5 days. Because a typical Tier 1 visit eats about a quarter of the starting ship's hold (8 days), **the island's survival offer must pay for the visit** (E3/F rule, stated in the T1 report). Nights pass during exploring; camping on shore is a choice, not a skip.

## 6. Time: one clock (patch T1)
| | everywhere (sea and shore) | `[tuning]` |
|---|---|---|
| clock | 1 game day = **15 real min**; 1 real s = 96 game s; 1 game hour = 37.5 s; a 4 h watch = 150 s | `time.real_minutes_per_game_day` (locked at 15 by a check), owner N13 |
| acceleration | **none** (no x2, no x4, no `Engine.time_scale`) | removed |
| pause | only planning screens, the Morning Report and menus; paused time advances nothing | `WorldClock` pause reasons are a set |
| day/night | dawn 05-07, morning 07-10, day 10-17, sunset 17-19, evening 19-20, night 20-05 (real seconds: 75 / 112.5 / 262.5 / 75 / 37.5 / 337.5) | `time.*_start_hour`, provisional, subject to visual testing |
Conversions (proved by the fixtures): 1 game day = 15 min; 3 days = 45 min (a Crossing); 8 days = 120 min (the longest Dead Ocean); 10 days = 150 min (water goes foul); 14 days = 210 min (scurvy).
The full rationale, the options considered and the compression of slow processes are in `T1_TIME_SYSTEM.md`.

## 7. Does the loop deliver the pillars? (computed, not promised)
Archetypes, each ending at a tier of island, averaged over the campaign mix (`loop_model.py`):

| cycle | mix | to island tier | voyage min | voyage days | island min | island days | ship+crew min | combat min | cycle min | cycle days |
|---|---|---|---|---|---|---|---|---|---|---|
| hop | 25% | T3 | 5.5 | 0.37 | 4.2 | 0.28 | 5.1 | 0.4 | 13.7 | 0.91 |
| passage | 40% | T2 | 16.5 | 1.10 | 11.2 | 0.75 | 7.3 | 1.3 | 31.7 | 2.11 |
| crossing | 25% | T1 | 42.5 | 2.83 | 31.5 | 2.10 | 12.5 | 3.4 | 78.0 | 5.20 |
| dead | 10% | T1 | 90.0 | 6.00 | 31.5 | 2.10 | 22.0 | 7.2 | 125.5 | 8.37 |
| **campaign average** | 100% | | 27.6 | | | | | | **48.2** | **3.21** |

Result: **sea 41.3 %, islands 34.4 %, ship and crew 19.8 %, combat 4.6 %** against the B1 targets of 40 / 35 / 17 / at most 8 (before T1: 39.3 / 35.4 / 20.9 / 4.4). The ship-and-crew share lands above its 17 % centre but inside its allowed range of 10-25 %; combat is well under its cap. B7 tunes this after the vertical slice. Every number comes from the tuning files, and `check_project.py` fails if the loop stops delivering the pillars.

Consequences the arithmetic exposed (information flags, intended, handed to the owners):
- **Visiting all 50 islands takes about 40 hours of play** (50 cycles x 48 min) and about 161 game days. B8 decides the real route length (a story route of about 30 islands is about 24 hours).
- **Dead Ocean is a preparation puzzle by arithmetic:** the longest crossing is **8 game days, 11.2 at the worst end of the band**. The starting ship holds **8 days** of rations, a mid-game ship 14, a late-game ship 24. So a Dead Ocean needs a bigger ship or careful provisioning; a Crossing (worst case 5 days) never does. 12 men need **336 L** of water at the minimum ration for 11.2 days, and water goes foul after **10 warm days (150 min)**, inside the Dead Ocean worst case. Rain catching, boiling or a spring is therefore *required*. Owners: N4 (water), N10 (cargo weight).
- **Scurvy clock:** 14 days without fruit is **210 minutes** of play, longer than any single voyage (120 min) and about 4.4 average cycles. Islands with `fruit` or `herbs` must appear at least once every few cycles (N5, E3).
- **An average island costs about 1.1 game days of exploring**, up to 3.0 for a full Tier 1 visit. Islands are no longer free, which is the intended consequence of one clock.

## 8. Failure and recovery inside the loop (P3)
The wheel never dead-ends. From any state there is at least one route to the next payoff:
- **Short on stock at sea:** the Warning Ladder (B1: 48 / 16 / 6 game hours) opens options before the loss; Hop and Passage voyages are always reachable from known charted springs.
- **Becalmed or off course:** the Reckoning's band widens on dead ocean, never hides; drifting, fishing and rain catching keep a ship alive.
- **Ship lost:** B1-1 fair-loss model. The castaway recovery (survivors on a shore with a salvage loop back to a hull) is designed in B6; B2 only requires that it re-enters the wheel at PLAN.
- **A bad island:** leaving is always possible; the only price is the supplies already spent (never more than 3.5 game days for a full Tier 1 visit).

## 9. The first loop teaches the whole wheel (B7 will script it)
The first cycle is a **Hop** (3-8 min) with a large margin: one Reckoning with only two stocks, one Morning Report if the clock passes 08:00 (B7 scripts the departure for about 06:00 so the first report always happens; it is auto-explained), one Tier 3 island, one clue. The second cycle is a **Passage** where a stock goes advisory so the player meets rung 1 safely. The first full Crossing comes only after the player has met all three rungs once, each with its recovery options.

## 10. Decisions (options and recommendation)
**B2-1. Time scale. SUPERSEDED by T1-1** (one clock, 15 min per game day everywhere). The old choice was two clocks (sea 2.4 min/day, ashore 60 min/day); it is removed.
**B2-2. Daily Morning Report.** (A) HUD only, no report. (B) **A pause screen at eight bells, 20 s to read (recommended, adopted; unchanged by T1).** (C) A full captain's-log text each day: too slow, too repetitive.
**B2-3. Island cost. SUPERSEDED by T1-3** (consumption continues ashore on the same clock; the typical visit costs up to 2.1 days, the cap is 3.5).

## 11. Pillar Gate for B2 (docs/templates/PILLAR_GATE.md), re-run after T1
| pillar | result | evidence |
|---|---|---|
| P1 sea is the game | yes | sea is the largest share (41.3 %); no quiet stretch above 4 min, carried by the moments rule |
| P2 sum | yes | the Reckoning at PLAN and in the report; islands cost visible supplies, so visits are plannable |
| P3 fair | yes | the ladder is in game hours with at least 2 real minutes to act at the last rung; recovery paths in section 8; no hidden timers, no acceleration to sleep through a warning |
| P4 people | yes | the report always carries one crew line; nights have real watches |
| P5 island question | yes | LANDFALL question card, ASK, ANSWER |
| P6 map pulls | yes | every cycle ends with CLUE; the Log writes itself |
Original idea: Eight Bells. No pirate cliche: the heartbeat is naval bookkeeping, not a parrot.

## 12. Open for later modules
N13 final slow-process rates and the sailing times; E2 the moment tables per region (day and night) and the exact quiet window; B5 how clues and upgrades carry between cycles; B6 castaway recovery and mode-specific rescue; B7 the scripted first hour and whether the 19.8 % ship-and-crew share holds; B8 the route length; I-modules the exact band colours after visual testing.

## 13. How B2 is enforced
`python tools/check_all.py` fails if: the cycle mix does not total 100; the modelled sea, island or ship-and-crew share leaves its pillar range; combat exceeds its cap; the sea has less than the islands; the day is not exactly 15 minutes; a removed two-clock or acceleration key or identifier reappears; the band start hours stop increasing, a band lasts under 30 real seconds, the report hour leaves the Morning band, or the light levels are mis-ordered; the watch length does not divide 24; crises outnumber choices; the report cannot be read in 30 s or takes over 3 percent of a day; the 3-day example stops being a Crossing; a full Tier 1 visit costs more than the cap or less than one day; the starting hold cannot cover a worst-case Crossing, or covers a worst-case Dead Ocean, or the mid-game hold cannot; water goes foul outside the window between a worst-case Crossing and Dead Ocean; scurvy would not outlast one voyage or would never matter; a worst-case Dead Ocean wears over 10 percent of the hull; an activity lasts under 20 s or over 15 min; a season lasts under 4 average cycles; the GDScript defaults differ from the tuning records; any script uses `Engine.time_scale`. The tests in `test_design_checks.py` prove each rule fires, plus a 100-case clock fixture and four hand-calculated clock scenarios (pause, resume, sea to island) that the Python and the GDScript clock must both match (GDScript unrun).
