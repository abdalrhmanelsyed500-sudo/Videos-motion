# B1 - Game Pillars: Crown of the Seas (working title)

Status: DESIGN, binding for every later module. Numbers marked `[tuning]` live in `game/data/tuning/tuning_design.json`, are provisional, and have a named owner module. Pillar promises are machine-checked by `tools/data_tools/design_checks.py` (run by `check_project.py` and `check_all.py`).

## 0. One sentence
**You are the captain of a ship full of people, crossing an ocean too big to cheat, and every crossing is a sum you must get right before the sea shows you what you got wrong.**

Thirty-second pitch: you hold the only map to the Crown of the Seas. Between you and the edge of the world lie weeks of open water, islands that each answer one question, and a crew that eats, tires, hopes and talks. The game is the planning table, the horizon, and the men on deck.

## 1. The six pillars
Each pillar has a test question, what it demands, what it forbids, and the commitments that can be checked.

### P1. THE SEA IS THE GAME
Crossing the ocean is the core experience, not the gap between content.
- **Demands:** long, dense, varied voyages; the sea is never empty (weather, wildlife, ships, wrecks, fishing, events); islands are never visible from each other unless a deliberate landmark.
- **Forbids:** loading-screen travel, fast-travel between islands, empty stretches longer than one event window (E2 sets the window), a voyage you can finish with the screen off.
- **Test:** *"Is the player doing something interesting on the water here, or just waiting?"*
- **Commitments `[tuning]`:** voyage length bands at the fixed time scale (1 game day = 15 real minutes, patch T1), no events, in real minutes: **Hop 3-8** (0.2-0.5 days), **Passage 8-25** (to 1.7 days), **Crossing 25-60** (to 4 days), **Dead Ocean 60-120** (to 8 days) (`voyage.*`, owners E2/E9; the bands were re-scoped by T1). Target play-time split: **sea 40 %**, **islands 35 %**, **ship and crew 17 %**, **combat at most 8 %** (`share.*`, owner B7).

### P2. EVERY VOYAGE IS A SUM
Logistics is the puzzle. Before you leave you can work out what you need; the sea decides how right you were.
- **Demands:** the Reckoning (section 2): all stocks shown as *time left at the current consumption* (days above 2, hours below); a planner that gives an honest range, not a promise; preparation choices that matter (what to load, which ration, which route, which watch plan).
- **Forbids:** hidden arithmetic, surprise consumption that the planner could not have shown, a stock bar with no number behind it.
- **Test:** *"Could a careful player have known this was coming, from numbers the game itself showed?"*
- **Commitments `[tuning]`:** forecast band is **plus/minus 25 %** on ordinary sea and **plus/minus 40 %** on dead ocean (`plan.forecast_spread_*`, owners N13/E9). The band is wider, never hidden.

### P3. HARD BUT FAIR
The journey is brutal and scarce, and the game never kills you from a direction it did not warn you about.
- **Demands:** the **Warning Ladder** (section 3); at least two recovery options at every critical state; every loss traceable to a decision or a visible risk.
- **Forbids:** instant death without warning, unrecoverable soft-locks, random events that delete a run, a stat that changes with no visible cause, a punishment the player cannot learn from.
- **Test:** *"If the player loses here, can they point to the moment they could have acted?"*
- **Commitments `[tuning]`:** ladder rungs at **48 / 16 / 6 game hours** left at current consumption = **30 / 10 / 3.75 real minutes** (`warn.*_hours`, owner N13; T1 replaced the old 7 / 3 / 1 days); **3 warning steps minimum** before any survival loss (`warn.min_steps_before_loss`, owner B6); **2 recovery options minimum** (`recovery.min_options`, owner B6). Difficulty may narrow the ladder in Hardcore; it may not remove it (decision B1-3).

### P4. A SHIP IS PEOPLE
The systems are the crew. Food is the cook's pot, a leak is the carpenter's sleepless night, scurvy is a man in a bunk with a name. (B1 uses role names only; the real crew come from the D modules and are all male.)
- **Demands:** every survival system has a person who feels it and says so in his own voice; labour, fatigue and watches are real; pay, grog and discipline move morale; deaths are noticed and recorded.
- **Forbids:** anonymous crew counters as the only crew UI, a morale bar that is not caused by something the player did, a death that no one mentions.
- **Test:** *"Who on deck feels this, and what do they say?"*

### P5. EVERY ISLAND ANSWERS A QUESTION
Islands are normal-sized and quick to explore; each one gives the voyage a reason and a memory.
- **Demands:** at least one survival-relevant offer (enforced in data: `survival_offers` has at least 1 item), exactly one memorable hook (enforced by the island kit slots), no two islands that feel alike (Silhouette Quota, hook-kind and template quotas from A6).
- **Forbids:** an island that is only a stop, a hook repeated more than 4 times, a survival offer that is always the same item in the same place.
- **Test:** *"What question does this island ask, and what is its answer?"* (Example: *"Can I afford a day to lift a wreck?"*)

### P6. THE MAP PULLS YOU
A story reason to keep crossing: the clue trail to the Crown, the legend of the lost pirates, the finale on Treasure Island. The game ends there.
- **Demands:** **no crossing of Passage length or more without a payoff** (a new clue, a new island, a loss or a gain with consequences); each region leaves one unforgettable image; the finale (guardians, the mountain climb, the cave sealed by a riddle only a true pirate knows) uses the same systems the player has lived by.
- **Forbids:** padding, a story that pauses the simulation, endless side content after the finale, lore that needs a religion to work (mysticism stays neutral: legends, curses, ancient beasts, pirate lore).
- **Test:** *"What does the player carry away from this crossing?"*

## 2. The original idea: THE RECKONING
Most survival games hide the numbers and let the player discover them by dying. This one does the opposite and still stays tense. **The game never hides arithmetic; only the sea hides information.**

At the chart table the captain opens the **Reckoning**:
1. Choose route, ration level, watch plan, cargo.
2. The table shows the **forecast band** in days or hours: low / expected / high. The band comes from the season's weather, the sea's currents, the navigator's skill and the chart you hold.
3. It shows every stock as *days of stock* and the **margin in days against the HIGH end** of the band.
4. Two stocks in the same voyage can be fine and thin at once; the table shows both.

**Information is cargo.** Navigator skill, bought charts, bird and cloud lore, and tips from islanders **narrow the band** (never below plus/minus 10 %, `plan.forecast_spread_min`, owner E8). A better chart is as valuable as a barrel of water. This ties P2 to exploration and to the navigation module (E8).

### Worked example (12 men, one 3-day crossing = 45 real minutes; produced by `design_checks.py`; rescaled by T1)
| | value |
|---|---|
| band (plus/minus 25 %) | **2.25 / 3 / 3.75 days** (34 / 45 / 56 real minutes) |
| hardtack need | 12 x 0.45 kg = **5.4 kg/day** -> 16.2 kg expected, 20.2 kg worst |
| water need (minimum 2.5 L) | 12 x 2.5 = **30 L/day** -> 90 L expected, 112.5 L worst |
| loaded: 21 kg hardtack, 100 L water | 3.9 and 3.3 days of stock |
| margin against the worst case | hardtack **+0.1 days**, water **-0.4 days** |

The Reckoning shows **ENOUGH for the expected 3 days, hardtack fine in the worst case, water SHORT in the worst case**. The captain decides: load the exact gap (13 L of water), take the two-thirds water plan, plan to catch rain, or trust the sea. Both outcomes are fair: the number was on the table.

## 3. The Warning Ladder
Every stock and condition (food, water, hull, powder, morale, health, fatigue) climbs the same ladder, measured in **game hours left at the current consumption** (T1; one game hour = 37.5 real seconds, so the rungs give 30 / 10 / 3.75 real minutes to act):

| rung | when | what the player gets | the quartermaster says |
|---|---|---|---|
| 1 Advisory | 48 hours or less (2 days) | HUD tint, note in the log | "Biscuit is good for two days at full ration, Captain. The chart says up to three to the next landfall. A short margin." |
| 2 Warning | 16 hours or less | pulsing icon, the quartermaster comes to the table, options listed | "Sixteen hours of biscuit, Captain. Half rations stretch it to a day and a third. Your call, or we put the nets out." |
| 3 Critical | 6 hours or less | the log marks the page, every recovery listed with its cost | "Six hours, Captain. The nets are out, the men know. Quarter ration, the spring on the charted shore, or the officers' own locker. I'd take the locker." |
| 4 Loss | only after rungs 1-3 | a consequence with a cause, never a game-over screen by itself | (the crew speaks about it afterwards) |

Rules: a rung may be skipped only by an **event the player chose to enter** (sailing into a storm on purpose); the ladder never resets silently; Hardcore Realism removes recommendations and map hints but keeps the numbers honest.

## 4. System coverage: every survival system must pass the pillars
"Owner" is the proposed Part N module (finalised when N starts; Canon: N-owner tags are proposed).

| system | the question the player asks | what warns them | recovery options (min 2) | island offers (`survival_offers`) | owner |
|---|---|---|---|---|---|
| food | do we eat until land? | days of stock, rations, rat sign | ration down, fish, hunt on the next shore | game, fish, fruit, trade_food | N1 |
| fishing and hunting | is the catch worth the hour? | gull flocks, shoals on the chart | net, line, spear; leave it | fish, game | N2 |
| cooking and preservation | will this keep? | spoilage days on each barrel | salt, smoke, cook now | salt | N3 |
| water | is the water still good? | litres and a foul-water date | rain catch, spring, boil, ration | fresh_water | N4 |
| health and disease | who is falling ill? | symptom days, surgeon's report | fruit and herbs, surgeon, rest | fruit, herbs, surgeon | N5 |
| ship condition | will she hold? | leak rate in litres per hour, hull percent | pump, patch, careen on a beach | timber, repair_dock | N6 |
| crew labour | who is too tired to stand a watch? | hours awake, watch roster | rest shift, double watch, anchor | shelter | N7 |
| morale and pay | will they follow me? | morale trend with named causes | shares, grog, a hard talk, a shore day | trade_food | N8 |
| ammunition | will the powder fire? | dampness percent per keg | dry the keg, trade, avoid the fight | ammo_trade, salvage | N9 |
| cargo weight | can she still sail? | speed penalty percent from the load | drop cargo, trade it, lighter ration | salvage | N10 |
| weather and seasons | what is the sea about to do? | barometer, swell, the navigator's lore | shelter, run, heave to | shelter | N11 |

The 11 rows are exactly the systems of the brief; a system that cannot fill a row fails the pillar gate.

## 5. The Pillar Gate
Every feature, system, island and module must answer six questions (template: `docs/templates/PILLAR_GATE.md`). **One "no" sends it back for redesign.**
1. **P1** Does it make the sea more interesting, or at least not shorter or emptier?
2. **P2** Can the player see the numbers behind it before committing?
3. **P3** Is there a warning ladder and at least 2 recovery options?
4. **P4** Is there a person on deck who feels it?
5. **P5** (islands and content) What question does it ask? Is it unlike what exists?
6. **P6** What does the player carry away from it?

Plus the three HARD CONTENT RULES, enforced automatically: no female crew, no sexual content, no gods or religion. `check_project.py` now scans every data file for banned words as a backstop (rule 1 words are scanned in names and dialogue text; `id`, `gender`, and `note`/`source`/`description` fields are skipped; a false hit is fixed by rewording).

## 6. Anti-pillars (what this game is not)
- **Not a combat game.** Combat is at most 8 % of play time and always a consequence of the sea (ships met, creatures disturbed, a mutiny avoided or lost).
- **Not a base-builder or a grind.** No fetch loop longer than one island visit; gathering has a point (a number in the Reckoning).
- **Not a reflex test.** No quick-time events; planning screens pause the clock (and only those: patch T1).
- **No hidden timers.** A timer exists only if it is in the log.
- **No pirate clichés** as design: no "arr" dialect, no shoulder parrot, no peg-leg-as-joke, no literal X-marks-the-spot puzzles, no plank-walking, no rum as the only drink. Pirate life is *accounting under stress*; that is the fresh angle.

## 7. Decisions (options and recommendation)
**B1-1. Loss model.**
- A. Ironman: any loss is the end of the run. Brutal, but breaks P3 (fair) and the length of the game.
- B. No game over at all, only setbacks. Safe, but the voyage loses its stakes.
- C. **Fair loss (recommended, adopted):** setbacks climb the ladder; the ship can be lost and the captain can fall only after rungs 1-3, with a last-chance rescue whose terms depend on the mode (Story: always; Normal: once per act; Hardcore: none). Save slots are not the rescue.
**B1-2. Time model (acceleration part SUPERSEDED by T1).**
- A. Strict real time, no pause. Tense, but unfair for reading numbers.
- B. Turn-based voyage. Fair, but kills the sense of an enormous live ocean.
- C. Real time at sea with a pause-to-plan rule; the player may also accelerate time (x1 / x4). **The acceleration part is SUPERSEDED by T1-2.** The rest stands: planning screens (Reckoning, galley, crew) and the Morning Report pause the clock; there is no acceleration at all, and the clock is the same at sea and ashore (T1-1).
**B1-3. Hardcore Realism** changes widths and recommendations, not the contract: the ladder stays (it may narrow to about 30 / 10 / 4 game hours, T1), the Reckoning stays honest, the recovery minimum stays. (B3 finalises the numbers.)

## 8. Open questions for later modules
- N13 owns the world clock rates and the slow-process compression (T1 fixed the day at 15 real minutes); B1 only fixes the bands and the ladder.
- B6 owns the exact last-chance rescue per mode and the lose conditions.
- B7 owns whether the 40 / 35 / 17 / 8 split holds after the vertical slice.
- D owns the crew voices; B1 uses role names only.

## 9. How B1 is enforced
`python tools/check_all.py` fails if: the warning ladder is out of order or has fewer than 3 steps or 2 recovery options; the forecast band is not wider on dead ocean; voyage bands do not increase; the day is not 15 minutes, or the clock model has two scales or an acceleration key; play-time shares do not total 100 or the sea has less than the islands; combat exceeds 12 %; any data file contains a banned content word. 25 tests prove each rule fires.
