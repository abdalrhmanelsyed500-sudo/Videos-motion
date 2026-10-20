# T1 - The Unified World Clock (patch to B1 and B2)

Status: DESIGN + CODE, binding. Everything marked **PROVISIONAL** is a tuning number with an owner (N13 clock and slow processes, I19 lighting, N-modules for activities) and may change after play-testing; the *rules* are decided. Nothing in the GDScript has run (no Godot in the build sandbox). Python checks, the GDScript linter and the GDScript parser all pass.

Checkpoint before this patch: git tag `pp-checkpoint-b2-before-time-revision` (= commit `af94b6b`, local) and the Drive file `pixel_pirates_B2_project_v1.zip`.

## 1. What was decided (from the owner's brief)
| id | decision | replaces |
|---|---|---|
| T1-1 | **One world clock. 1 game day = 15 real minutes, at sea and ashore.** Continuous, fixed rate. No second scale anywhere. | B2-1 (sea 2.4 min/day, ashore 60 min/day) |
| T1-2 | **No player acceleration** (no x2, no x4, no `Engine.time_scale`). | the x1/x4 part of B1-2 |
| T1-3 | Consumption continues ashore on the same clock; a visit costs real game time. Cap: `loop.visit_cost_days_max` 3.5 days. | B2-3 (one-day cap) |
| T1-4 | The Warning Ladder is measured in **game hours**: 48 / 16 / 6. | 7 / 3 / 1 days |
| T1-5 | Pause only for planning screens, the Morning Report and menus. Paused time advances nothing. Nights cannot be skipped, so night must be playable. | "report breaks the quiet", "fast-forward stops at the report" |
| T1-6 | Slow biological and wear processes are compressed; fast processes are not (section 5). | old per-day values |
| T1-7 | Only the watch-end bell is audible by default. | half-hour bells everywhere |
| T1-8 | Every time-dependent system consumes the game dt returned by `WorldClock.tick()` and nothing else. | |

## 2. The rate table (exact)
| quantity | game time | real time |
|---|---|---|
| 1 real second | 96 game seconds | 1 s |
| 1 game minute | 60 s | 0.625 s |
| 1 game hour | 3600 s | **37.5 s** |
| half-hour bell interval | 30 min | 18.75 s |
| one watch (4 h, "eight bells") | 4 h | **150 s** |
| 1 game day | 24 h | **900 s = 15 min** |
| Morning Report | every day at 08:00 | every 15 min (+ 20 s paused read) |
| 10 days / 14 days / 20 days / 30 days | | 2.5 h / 3.5 h / 5 h / 7.5 h |
The same table holds on every difficulty mode and every quality profile: no difficulty mode changes the day length, and no quality profile changes the clock or the lighting curve (only how expensive it is to draw).

## 3. Day and night (24 h, smooth)
Bands are **provisional and subject to visual testing** (owner I19). The *hard label* is for HUD text and band-triggered events only; **lighting must use the continuous values**.

| band | game hours | length (game) | length (real) | daylight level at start -> end | note |
|---|---|---|---|---|---|
| Dawn | 05-07 | 2 h | 75 s | 0.04 -> 0.55 | first light, cool to warm |
| Morning | 07-10 | 3 h | 112.5 s | 0.55 -> 1.00 | Morning Report at 08:00 |
| Day | 10-17 | 7 h | 262.5 s | 1.00 | full light, shortest shadows at noon |
| Sunset | 17-19 | 2 h | 75 s | 1.00 -> 0.30 | golden hour |
| Evening | 19-20 | 1 h | 37.5 s | 0.30 -> 0.04 | blue hour, lanterns lit |
| Night | 20-05 | 9 h | **337.5 s (5.6 min)** | 0.04 | dark; lanterns, moon, stars |
Rules, all in code and all tested:
- `daylight(hour)`: smoothstep between keyframes at the band boundaries (night floor 0.04, dawn end 0.55, sunset end 0.30). Never jumps: the largest step per 0.01 game hour is below 0.01, and it wraps cleanly at midnight.
- `band_weights(hour)`: a continuous mix of the six bands (always sums to 1), smoothstepped between band midpoints, for colour grading and ambience cross-fades. Also never jumps.
- `band_of_hour(hour)`: the hard label (night wraps midnight).
- Visibility follows daylight: sight range, the tilt-shift, bloom and the grade come from these two curves, so the look changes gradually. How the six moods map onto the existing look presets is an I19 task; the clock side is ready.
- **Independence from the dev PC:** the curves are data and arithmetic, identical on Dev-Lite and Ultra. Dev-Lite may turn off shadows or bloom, but it shows the same time of day on the same schedule. The final look is not reduced because of the dev machine.

## 4. Pause rules
- `WorldClock` keeps a **set of pause reasons**. Time runs only when the set is empty. Pausing twice for the same reason is harmless; releasing one reason does not release another (a Morning Report opened over a planning screen stays paused when the report closes).
- Allowed reasons: `report` (the Morning Report), `planning` (Reckoning, galley, crew, cargo screens), `menu` (pause menu, options, console). Gameplay may not invent a pause (no hidden "cutscene freeze" that stops hunger but not the sea).
- `tick(real_dt)` returns 0 while paused and for non-positive deltas. Systems feed on that return value, so a paused game cannot consume food, water, fatigue, spoilage, weather, events or repairs. Tested with a stand-in consumer: ten paused real minutes consume nothing and move no clock; one running quarter-hour consumes exactly one day of rations (5.4 kg for 12 men).
- `meta.playtime_s` counts real play time, paused or not.
- Pause reasons are **runtime-only and are not saved**. A loaded game must start paused (reason `menu`) until the player confirms (rule for J1).
- Frame stalls: systems must step in sub-steps of the returned game dt (J-module rule) so a long frame never skips an event. The debug live mode clamps one frame to 0.25 s.

## 5. Recalculation of every time-dependent system
Old values came from the 2.4 min/day sea clock. They were **not** converted mechanically. The principle:

> **Slow-process compression.** Anything that takes weeks or months in reality is compressed so that it lands inside **2 to 6 real hours of play**; anything that takes minutes or hours (hunger, thirst, fatigue, watches, repairs, fishing, cooking) stays **realistic in game hours**. A 15-minute day cannot carry real-world 70-day scurvy; it can carry a 14-day one.

| system / key | old (2.4 min/day) | new (15 min/day) | real time of the new value | why |
|---|---|---|---|---|
| Voyage Hop | 3-8 min = 1.25-3.3 d | 3-8 min = **0.2-0.53 d** | same minutes | minutes kept (P1), days shrink |
| Voyage Passage | 8-20 min | 8-25 min = **0.53-1.67 d** | | |
| Voyage Crossing | 20-45 min | 25-60 min = **1.67-4 d** | | stretched so a Crossing is still a multi-day, plannable sum |
| Voyage Dead Ocean | 45-90 min = 18.8-37.5 d | 60-120 min = **4-8 d** (worst case +40 % = 11.2 d) | | must exceed the starting stores hold (8 d) |
| Warning Ladder | 7 / 3 / 1 days | **48 / 16 / 6 hours** (Hardcore about 30 / 10 / 4) | 30 / 10 / **3.75 min** | the last rung leaves at least 2 real minutes to act (checked) |
| Water foul (warm) `water.foul_after_days_warm` | 30 d | **10 d** | 150 min | longer than a worst-case Crossing (5 d), within a worst-case Dead Ocean (11.2 d): rain, boiling or a spring is required there |
| Scurvy onset `health.scurvy_onset_days_no_vitc` | 70 d | **14 d** (Hardcore 10, Story 28) | 210 min | longer than any single voyage (120 min), at most 6 average cycles |
| Hull wear at sea | 0.08 %/d | **0.5 %/d** | | a worst-case Dead Ocean wears 5.6 % (cap 10 %) |
| Barnacle slowdown | 3 %/month | **12 %/month** | month = 7.5 h | careening about every 10-12 hours of play |
| Morale decay | 1/d | **2/d** | | an unpaid crew reaches mutiny pressure in about 12 real hours |
| Ship stores hold (new) | n/a | start **8 d**, mid **14 d**, late **24 d** of full-crew rations | | Crossing worst case 5 d fits the starter; Dead Ocean needs preparation or a better ship |
| Season length (new) | n/a | **20 d** | 5 h | about 8 seasons in a campaign; at least 4 average cycles |
| Gale | n/a | **12 h** | 7.5 min | |
| Fish cast | n/a | **1.5 h** | 56 s | stays realistic |
| Cook a meal / meals per day | n/a | **1 h** / **3** | 37.5 s | |
| Patch a leak / replace a plank | n/a | **2 h** / **6 h** | 75 s / 3.75 min | |
| Careen (one camp slot) | n/a | **24 h** | 15 min | |
| Sleep need | n/a | **8 h** | 5 min | nights are played, no skip |
| Morning Report | every 2.4 min | **every 15 min** | 20 s paused read = 2.2 % of a day | |
| Island visit (full / typical) | 18 h / 6.5 h | T1 **3.0 / 2.1 d**, T2 **1.07 / 0.75 d**, T3 **0.4 / 0.28 d** | 45 / 16 / 6 min | one clock, so exploring costs supplies |
| Campaign | 33 h, 455 days for 50 islands | **40 h, 161 days** for 50 islands | | |
| Average cycle | 40 min, 9.1 days at sea | **48 min, 3.2 days (1.8 at sea)** | | |
| **B1 play-time split (sea / island / ship+crew / combat)** | 39.3 / 35.4 / 20.9 / 4.4 | **41.3 / 34.4 / 19.8 / 4.6** | | targets 40 / 35 / 17 / at most 8 |

The full set of 23 time keys is in `game/data/tuning/tuning_time.json`; the rest sit in `tuning_core.json`, `tuning_design.json` and `tuning_loop.json`. All are PROVISIONAL and listed in `docs/PROVISIONAL_LEDGER.md`.

## 6. Trade-offs and the options that were weighed
**a) Voyage bands.** (A) Keep the old real-minute bands (3-8 / 8-20 / 20-45 / 45-90): voyages shrink to 0.2-6 game days; Dead Ocean would be 6 days and the 8-day starting hold would cover it, so no preparation puzzle. (B) Keep the old game-day lengths (1.25-37 days): voyages become 19 minutes to 9 hours and the "enormous ocean" pillar breaks, and so would the 3-8 minute Hop. (C) **Adopted: keep the Hop and Passage minutes, stretch the two upper bands** (Crossing 25-60, Dead Ocean 60-120). Cost: the longest voyage is 2 hours without a break; E2 must fill it with day and night moments.
**b) Ladder in hours, not days.** At a 15-minute day, "3 days" is 45 real minutes of warning, far too gentle; "1 day" is 15 minutes. Hours give 30 / 10 / 3.75 real minutes. Cost: a stock that was fine at breakfast can be critical by supper; the Reckoning and the Morning Report must show hours below 2 days.
**c) Visits cost real supplies.** (A) Freeze the supply clock ashore: breaks "one clock". (B) Cap visits at one day: would force Tier 1 islands to 15 minutes of play. (C) **Adopted: same clock, cap 3.5 days.** A typical Tier 1 visit consumes about a quarter of the starter ship's 8-day hold. Consequence handed to E3/F: **every island's survival offer must pay for its own visit**, otherwise islands become a tax. Not yet machine-checked (islands do not exist yet); it will be when E3 lands.
**d) Slow-process compression** (section 5). Cost: realism of disease and wear timescales. Benefit: they are actually felt inside one campaign. The compression is documented per key and can be reversed by changing one number if a longer game is wanted.
**e) Nights are 5.6 real minutes and cannot be skipped.** Risk: dull nights. Mitigation: night moments (lanterns, shapes on the water), real night watches, night-only fishing and creatures, harder navigation that rewards a good navigator. If playtests say nights drag, the options are a shorter night band (the numbers are data) or a camp-sleep mechanic that **spends** the hours rather than skipping them (it would still run through the clock). Acceleration stays forbidden.
**f) A 15-minute day.** Faster than a realistic voyage feel, slower than an arcade. The band limits are 12 to 20 in the data schema, but a check locks the value at 15 because every other number was derived from it: change it only through a new decision, then re-run `loop_model.py`.
**g) Eight Bells audio.** A bell every 18.75 s would be constant noise. Only the watch-end bell (every 150 s) is audible by default; half-hour bells are a HUD tick and an option. The 08:00 bell is a full eight bells and opens the Morning Report.

## 7. Save compatibility
- **No change to the save format.** `SAVE_VERSION` stays 1; the schema still has exactly one clock field, `clock.t_seconds` (integer game seconds, >= 0). Game seconds mean the same thing as before; only the real-time rate they accumulate at changed, so an older save loads as is. (No gameplay saves exist yet, only test fixtures.)
- `GameState.t_seconds` is now a property over `GameState.clock.t` (a float): the getter floors it, the setter writes it. A save therefore loses less than one game second (10 ms of real time) on a round trip, and `to_dict() -> JSON -> from_dict()` stays lossless (tested).
- `meta.playtime_s` remains real seconds. Pause reasons and the ship's location flag are not saved.
- A future rate change needs no migration, because saved time is game time. A migration would be needed only if the *meaning* of `t_seconds` changed.

## 8. Code map
| file | what |
|---|---|
| `game/core/voyage_clock.gd` | pure functions: watches, bells, conversions, `band_of`, `band_of_hour`, `daylight`, `band_weights`, `reports_between` |
| `game/core/world_clock.gd` | the one clock: `tick(real_dt) -> game_dt`, pause-reason set, `set_location` (bookkeeping only), `hour()`, `day()` |
| `game/core/game_state.gd` | owns `clock`; `t_seconds` property; `tick(real_dt)` (also counts playtime) |
| `game/core/console_commands.gd`, `game/ui/debug_console.gd` | `time`, `time watch`, `time tick <real_s>`, `time live on|off`, `time pause|resume <reason>`, `time add|set` (debug-only jumps); live HUD line |
| `tools/data_tools/voyage_clock.py` | Python twin (functions + `WorldClock` + scenario runner) |
| `tools/data_tools/loop_model.py`, `design_checks.py`, `tools/check_project.py` | the invariants (section 9) |
| `game/data/tuning/tuning_time.json` (+ edits to core, design, loop) | 78 tuning records in total |
| `game/tests/fixtures/clock_cases.json` (100 hand-written cases), `clock_scenarios.json` (4 hand-calculated scenarios) | shared by Python and GDScript |

## 9. What is machine-checked (and proven to fire)
`python tools/check_all.py` fails if any of these breaks (each has a negative test in `test_design_checks.py`):
the day is not exactly 15 min; a removed two-clock/acceleration key (`time.accel_*`, `time.ashore_*`) or identifier comes back; band starts stop increasing or any band lasts under 30 real seconds; the report hour leaves the Morning band; light levels are mis-ordered; the watch does not divide 24; the report takes over 3 % of a day; the 3-day example stops being a Crossing; a full Tier 1 visit exceeds the cap or costs under a day; the starter hold cannot cover a worst-case Crossing / covers a worst-case Dead Ocean / the mid hold cannot cover it; water foul falls outside the Crossing-to-Dead-Ocean window; scurvy would not outlast one voyage or would never matter; Dead Ocean wear exceeds 10 %; an activity is under 20 s or over 15 min; a season is under 4 cycles; the critical rung leaves under 2 real minutes; the GDScript defaults (rate, band starts, report hour) differ from the tuning records; any script uses `Engine.time_scale`; the docs state an old time rule without marking it superseded. Two deliberate breakages (rate 12; GDScript default 14) were run to confirm the checks fail, then reverted.

## 10. Results (this build sandbox)
| check | result |
|---|---|
| `python tools/check_all.py` | **ALL PASSED**: project check (data, parity, island kit, refs, content rules, time rules), data tools tests, design checks tests, island kit tests, gdlint, gdparse. **Godot in-engine tests: SKIPPED (no Godot here).** |
| `test_design_checks.py` | 85 checks pass (pillars, loop, time invariants, day/night boundaries and smoothness, pause behaviour, sea/island continuity, 100 + 4 fixture items) |
| `test_data_tools.py`, `test_parity.py` | pass (scurvy scaling now 14 / 10 / 28; validator 35 cases and world rules 14 cases match) |
| `validate_data.py` | 78 tuning records, 0 problems |
| gdlint / gdparse | clean on all GDScript, including the new `world_clock.gd`, `test_world_clock.gd`, the rewritten `voyage_clock.gd` and `test_voyage_clock.gd` |
| GDScript in Godot | **NOT RUN.** The GDScript tests were written and syntax-checked, never executed. |

## 11. Remaining risks
1. **No GDScript has run.** The new code may contain a runtime error the parser cannot see (typing, a property accessor, a lambda). Section 12 is how to find out.
2. The six bands are numbers on paper. Whether Dawn 05-07 and a 37.5-second Evening look right needs the Look Lab / in-engine visual test (I19). The Evening band is the shortest at 37.5 s and the most likely to need widening.
3. Whether a 5.6-minute night is fun is unknown (section 6e).
4. A 15-minute day with a 2-hour Dead Ocean voyage: E2 must supply enough moments (at least 2 choices per 10 minutes) for 8 game days at night and day.
5. The "island pays for its visit" rule is a design promise until E3 builds islands.
6. The slow-process compression was chosen by arithmetic (the invariants), not by play. Hull wear 0.5 %/d, morale 2/d and barnacles 12 %/month are the least certain.
7. The check that docs mark old time rules as superseded is textual and can miss a differently-worded stale rule; a human read of B1/B2/Canon is still needed.
8. Frame-stall handling in the real game (sub-stepping) is a rule for J1, not code yet.

## 12. Exact Godot tests to run on your PC
Prerequisite: Godot 4.7.2 and `tools\godot_path.txt` (or the `GODOT_EXE` variable).

**Test 1: the automatic suite.** Run `tools\run_godot_tests.bat`. Pass = the last line reads `TESTS: N checks, 0 failed -> PASS` and there is no `SCRIPT ERROR` or `Parse Error` anywhere. In the output look for these sections with no `FAIL:` line under them: `== test_voyage_clock.gd`, `== test_world_clock.gd`, `== test_game_state.gd`, `== test_console.gd`, `== test_tuning.gd`. Send me the last 30 lines either way.

**Test 2: the console, by hand** (run the game with F5, press the backtick key, left of 1). Type each line and compare:
1. `time set 1 0` -> `[debug jump] Day 1, 00:00`
2. `time watch` -> `Day 1, 00:00 - Middle watch, last bell 8 | band night, daylight 0.04` and a second line `1 day = 15 real min (1 game hour = 37.5 s) | next Morning Report in 300 real s | paused: no`
3. `time tick 60` -> `60.0 real s -> 5760.0 game s (1.60 h) | Day 1, 01:36`
4. `time pause report` -> `pause report: paused by report`, then `time tick 60` -> `... 0.0 game s (0.00 h) | Day 1, 01:36` (nothing moved), then `time resume report` -> `resume report: time runs`
5. `time set 1 4.9`, then `time tick 7.5` -> `Day 1, 05:06`; `time watch` shows `band dawn` and a daylight between 0.04 and 0.55.

**Test 3: the real-time stopwatch** (the only test of the actual feel). Type `time set 1 0`, then `time live on` and close the console (backtick or Esc). A line appears at the top right (clock, band, daylight, place). Start a stopwatch when it reads `Day 1, 00:00`:
- it must read about `01:00` after **37.5 s**, `04:00` after **150 s**, `Day 2, 00:00` after **15 min** (there is no Morning Report screen yet, so only what you type pauses it);
- open the console and type `time pause menu`: the line shows `PAUSED: menu` and stops; `time resume menu` restarts it;
- type `tp island isl_901` and then `tp xy 100 100` while it runs: the place word changes between the island id and `sea` and **the clock does not jump or change speed**.
Then `time live off`. Note: the debug clock clamps a single frame to 0.25 s, so a stalled window can make the stopwatch read slightly behind; ignore stalls, not drift.
Tell me the stopwatch readings and anything that differs; on the HD 3000 a low frame rate does not matter for this test, only the time.

Not testable yet: the look of the six bands (no lighting hooked to the clock; that is I19), the Morning Report screen (J-module), and any consumption of food or water (no survival systems yet).
