# E1 - The Ocean: shape, regions, weather, wildlife, and a playable slice

Status: **designed, data-tested, GDScript written and parity-checked, NEVER RUN IN GODOT.** Everything marked PROVISIONAL has owner E1 unless stated.
This module delivers the world specification AND a small playable vertical slice ("The Three Weathers"). The slice is the first test of the ocean: it is not done until you have sailed it on your PC (checklist in section 11).

## 1. What exists

| Layer | Files | Verified how |
|---|---|---|
| World data | `game/data/world/regions.json` (10 regions), `climate_bands.json` (6), `slice_route.json` (7 checkpoints), `game/data/wildlife/*.json` (87 species), `tuning_ocean.json` (50 keys), schemas `region`, `climate_band`, `species` | `validate_data.py`, `check_project.py`, `ocean_checks.py` (0 problems) |
| Ocean model | `tools/data_tools/ocean.py` and its twin `game/core/ocean.gd` | `test_ocean.py` (properties + 40 golden cases), `gd_logic_check.py` |
| Wildlife | `wildlife.py` / `core/wildlife.gd` | same |
| Ship | `sea_state.py` / `core/sea_state.gd` | 8 golden voyages |
| Console | `route`, `ocean` commands in `core/console_commands.gd` | `tests/test_console.gd` (written, not run) |
| Slice | `ui/ocean_slice.gd/.tscn`, `ui/sea_painter.gd`, `tools/run_slice.bat` | **nothing** (gdparse + gdlint only); concept stills in `art_bible/sea_views_e1/` |

What "verified" means here: the Python model is tested by properties and golden files. The GDScript is a hand translation of it. `python tools/data_tools/gd_logic_check.py` transpiles the GDScript formulas to Python by regex and replays all fixtures (**186 cases, 0 differences**); it caught 6 of 7 deliberately injected bugs (wind constant, sun offset, iceberg hash index, hash prime, wildlife seed, integrator step). The 7th, removing the north/south clamp in `sea_state.gd`, was NOT caught: no golden voyage reaches the north or south edge, because the polar pack stops the ship first. The east and west clamps are covered. That proves the GDScript FORMULAS equal the Python ones. It does not prove the GDScript parses in Godot, runs, or draws anything.

## 2. The world (decisions E1-1, E1-2)

- **9,000 x 6,000 km**, y = 0 is north. Latitude = 75 - y / 40 degrees, so the map spans +75 to -75. No wrapping, no leaving: the edge rim is a storm wall (`ocean.edge_storm_km`) and the ship is clamped.
- Climate belts by |latitude|: tropical < 20, subtropical 20-35, temperate 35-55, cold 55-65, polar 65-75 (data: `climate_bands.json`: doldrums, trades, horse latitudes, westerlies, subpolar, polar).
- Season: a year is 80 game days (20 real hours); start phase 0.25; solar declination 23.44 x sin(2 pi (s - 0.25)).
- Islands: **58** (Tier 1 14, Tier 2 22, Tier 3 22), keys `world.islands_t1..t3`, spread by region quota (section 4). Islands are placed in E2/E3; E1 only reserves the quota and the Treasure Island site in the White Hollow.

## 3. Scale and sailing times (decision E1-3) - the numbers the Canon needs

One game day = 15 real minutes (T1). A sloop at the reference condition (beam reach, 14 kn through the water) with `ship.hull_speed_factor` 1.3 covers **9.3 km per game hour = 14.9 km per real minute**.

| Distance | Real time | Band (km) |
|---|---|---|
| 10 km (the horizon, about) | 40 s | |
| 45 - 119 km | 3 - 8 min | Hop |
| 119 - 372 km | 8 - 25 min | Passage |
| 372 - 893 km | 25 - 60 min | Crossing |
| 893 - 1,786 km | 60 - 120 min | Dead Ocean crossing |
| 3,340 km (the slice, straight line) | 3.7 h at reference speed | |
| 9,000 km (edge to edge) | about 10 h | |

Reference speed is the best case. Real wind changes it: the same sloop made **15.8 km per real minute** west along the Kettle trade, **0.2 kn** (12 km in two game days) becalmed in the Glass Sea, **317 km per game day** running east in the Storm Belt (and cannot come back the same way), and 0 in the polar pack. The autopilot estimate for the whole slice route is **about 8.4 hours** because the legs 1-2 and 3-4 are 1.3-1.6 times longer than the straight line (tacking). That is the intended feeling of the ocean, and also why the slice has debug jumps (section 8).

Scale perception: the chart is true scale; the sea view uses presentation speed (waves, wake and clouds move at screen speed, not at 9.3 km/h); region blends are 160 km wide, weather systems about 400 km.

## 4. Regions (decision E1-4)

Ten regions, each with its own `nav_rule` (a rule that changes how you plan a voyage), palette, sky, atmosphere, sea, ice, hazards, discoveries and gear needs. Weighted-Voronoi lookup over seed points (domain warp 250 km, north-south aspect 1.8, latitude penalty 2.0), softmax blend 160 km, so there are no hard borders and the renderer never needs to know which region it is in (`Ocean.look_at`).

| Region | Seed (km) | Climate | Nav rule | Isl. T1/T2/T3 | Medians (SST, wind kn, wave m, vis km) |
|---|---|---|---|---|---|
| The Kettle Seas | 7000, 2500 | tropical | squall_wall | 2/4/4 | 29.1, 11, 1.0, 8.5 |
| The Shattered Reaches | 1800, 2650 | tropical | tide_gated_channels | 2/3/3 | 29.5, 6, 0.4, 7.3 |
| The Sunward Banks | 7400, 2050 | subtropical | monsoon_reversal | 1/3/2 | 23.1, 3.8, 1.1, 8.9 |
| The Glass Sea | 4500, 3000 | dead calm | windless_mirror | 1/2/2 | 30.2, 1.6, 0.1, 7.3 |
| The Dead Ocean | 4400, 4150 | subtropical | star_only_drift | 1/1/2 | 24.6, 8.1, 1.5, 9.3 |
| The Green Verge | 1900, 1250 | temperate | pilot_coast_tides | 3/3/2 | 19.0, 19.6, 2.9, 4.7 |
| The Fogbound Expanse | 5200, 1250 | temperate | fog_bell_pilotage | 1/2/2 | 16.3, 7.7, 0.9, **1.1** |
| The Grey Marches | 5600, 500 | subpolar | iceberg_watch | 1/2/2 | 2.8, 18.5, 3.1, 4.1 |
| The Storm Belt | 5000, 4950 | stormy | westerly_run | 1/1/2 | 13.3, **24.4**, **5.4**, 4.7 |
| The White Hollow | 4200, 5700 | polar | ice_leads | 1/1/1 | -0.9, 12.8, 2.0, 4.2 |

Machine-checked contract (`ocean_checks.py`): region areas 4-20 percent of the world; each region keeps its promise (fog region foggy, storm region stormy, calm region calm, polar region iced...); every pair differs on at least 3 of 10 measured axes; seeds are at least 2 blend widths apart; species temperatures fit the local sea; at least 10 species per region.

## 5. Weather, light and the Herald Swell (decisions E1-5, E1-6)

- Weather is a **pure function of (x, y, time)**: integer-hash value noise (Python and GDScript share the hash, so they agree to 1e-4). Nothing is stored, so a save needs no weather state and a replay is exact.
- Wind comes from the belt (trades, westerlies...), scaled by region, monsoon and a gust noise; storms are a smoothstep over a weather index (0.66 to 1.20) that builds over at least 3 real minutes. Wind, waves, rain, cloud, fog, visibility, air and sea temperature, ice, productivity, light limits and currents are all in one `sample(x, y, t)` call.
- **Herald Swell:** `herald(t) == storm(t + 1 game day)` (tested). A long, heavy swell arrives with no wind one game day (15 real minutes) before a gale. The player is told through the sea (longer, taller waves in the view), the HUD line and the journal. It is the fair warning that matches pillar P3.
- Light: `light = max(light_floor, daylight x light_peak)`, where `daylight` is the T1 continuous curve and floor/peak come from latitude and season (polar day and night exist). The same curve on every quality profile.
- Visibility: horizon from eye height, reduced by fog and rain; the Fogbound Expanse median is 1.1 km.

## 6. Ship movement (decision E1-7)

`SeaState` has no clock of its own. It takes `(t_start_days, game_seconds)` from the one world clock and integrates in sub-steps of 600 game seconds (6.25 real s), resampling the ocean every 900 game seconds (9.4 real s) so the hot path stays cheap on the dev PC. Position is clamped to the world, distance accumulated. A paused clock returns 0 game seconds, so a paused ship cannot move (tested). The model has a no-go zone into the wind, a wave-height speed penalty, a hull-speed cap and ice drag (pack ice stops the ship).
Not modelled yet (N and J modules): sail trim, crew skill, hull condition, leeway, anchoring.

## 7. Wildlife (decisions E1-8, E1-9)

- **87 species in the seed** (target 200+; `wildlife.species_target` = 200): fish 26, sharks/rays 8, cetaceans 11, pinnipeds 5, reptiles 4, invertebrates 14, seabirds 12, strange 7. 80 are real animals, 7 are fictional (8 percent; rule 5-25): Looking-glass Ray, Ghost Lantern, Stormglass Medusa, Bellsinger, Hollow Whale, Trench Angler, Grandfather Squid. `value` is reales per kg for a catch, or the report payout for observe-only animals.
- **Sighting model** (deterministic, no saved state): one roll per 0.1-game-day slot (1.5 real minutes) per 40 km cell, p = 0.55. The species is chosen by weight = region abundance x temperature fit x productivity x ice x season x time-of-day activity x rarity (common 1, uncommon 0.4, rare 0.12, legendary 0.02). Abundance below 0.02 counts as absent. Distance = visibility x 0.15 - 0.85, so fog hides animals honestly. Measured by the model: about 0.15 - 0.7 sightings per real minute per region and 8+ distinct species per region over 10 game days.
- Open sea is never empty: wildlife (here), weather (section 5), icebergs in the cold regions (hash grid, no state). Ships, wrecks, fishing and events are H/J work and are not in E1.

### Quota plan toward 200+ (`python tools/world/species_quota.py`)

| Group | Seed | Target | To add |
|---|---|---|---|
| pelagic fish | 12 | 24 | 12 |
| reef fish | 7 | 20 | 13 |
| cold fish | 7 | 18 | 11 |
| sharks and rays | 8 | 16 | 8 |
| cetaceans | 11 | 20 | 9 |
| pinnipeds | 5 | 9 | 4 |
| reptiles | 4 | 9 | 5 |
| cephalopods | 4 | 12 | 8 |
| crustaceans | 3 | 10 | 7 |
| cnidarians | 2 | 8 | 6 |
| plankton | 3 | 5 | 2 |
| invertebrates | 2 | 7 | 5 |
| seabirds | 12 | 24 | 12 |
| strange | 7 | 18 | 11 |
| **Total** | **87** | **200** | **113** |

113 species is 5 batches of about 25 (in module H). **Priority order by need:** White Hollow (11 species at abundance 0.3+, needs 14 more to reach 25), Glass Sea and Dead Ocean (12 each, need 13), Storm Belt (20, needs 5). The other six regions already have 27-39. Each batch must keep the contract: at most 4 legendary, fictional 5-25 percent, a seabird in every region except the Dead Ocean, a catchable and a rare species in every region.

## 8. The slice: "The Three Weathers"

Seven checkpoints (data: `slice_route.json`), each chosen to show one thing the world promises:

| # | Place | Position (km) | Day | What you should see |
|---|---|---|---|---|
| 1 | Kettle dawn squall | 7000, 2650 | 1, 06:00 | warm rain squall at first light (rain 0.57, 14 kn, 1.4 m), the reference tropical look |
| 2 | Kettle edge, noon | 7227, 2194 | 2, 12:00 | clear noon, 8.8 km sight, no rain |
| 3 | Sunward, monsoon coast | 6518, 1538 | 4, 06:00 | cooler water (19 C), 5 kn of wind: the monsoon turning |
| 4 | Fogbound dawn | 5889, 1047 | 9, 06:00 | sight 0.7 km (fog 0.67), rain, fog-bell country |
| 5 | Grey Landing, Herald Swell | 5640, 560 | 13, 12:00 | 4.0 m long swell, 17 kn, no gale yet (herald 0.74) |
| 6 | Grey Landing, the gale | 5640, 560 | 14, 12:00 | the gale the swell promised, 15 real minutes later (storm 0.74, 25 kn, 4.6 m, rain 0.70) |
| 7 | Ice Edge | 5600, 40 | 15, 06:00 | sea ice (67 percent), -3 C, the ship stops in the pack at the rim |

Run: `tools\run_slice.bat` (Windows; same Godot lookup as `run_godot_tests.bat`) or `godot --path game res://ui/ocean_slice.tscn`.
Keys: **A/D** steer, **P** pause, **M** chart (opens the chart and pauses the clock like a planning screen), **1-7** debug jump to a checkpoint, **N** (on the chart) reveal everything (debug), **F1 or `** console. Close the console before steering (it does not capture A/D while open).
Console: `route` (list), `route 5` / `route jump 5` (debug jump: places ship and clock, **never accelerates time**), `route heading 90`, `route status`, `ocean <x_km> <y_km> [t_days]` (what the sea and sky are doing anywhere), `time ...` as before. The slice always runs the live clock itself (it turns the console's own live clock off so time cannot double).

HUD: region, day/time/band, latitude and chart position, wind and its compass direction, waves, visibility, air temperature, heading, speed, distance sailed, warnings (gale, Herald Swell, fog, ice, becalmed), the journal (n / 87), the next checkpoint with distance, bearing and an ETA at current speed, a wind rose (bow up), a region banner when you cross into a new region. The chart is a fog-of-war map: cells within 120 km of the ship are revealed a few per frame (30 cells per frame, so a 15,000-cell region lookup never stalls a frame on the dev PC).

Sea view (all plain 2D draw calls at 640 x 360, scaled 2x): sky by light and region palette, stars, sun and moon on their hours, clouds, 17 wave rows (height from the real wave model, wavelength grows with the Herald), whitecaps by wind and storm, ice floes and icebergs at true bearing, rain, fog, rare dim lightning (never a full-white strobe), a polygon placeholder ship that heels with the wind, wildlife silhouettes at their true bearing (whales blow, fish leap, birds fly, strange things glow). Displayed values ease toward the model values over 2 s, so weather never snaps.

Concept stills: `art_bible/sea_views_e1/sea_views_sheet.png` (+ nine 1280 x 720 stills). **They come from `tools/world/render_sea_views.py`, a Python mirror of the painter's colour logic driven by the real ocean model; they are not screenshots of Godot.** They show the data is capable of nine clearly different looks (tropical dawn, tropical noon, monsoon dawn, fog, Herald swell, gale, ice edge, tropical night, glass calm). Known weakness visible in them: the gale checkpoint (rain, dark sky, 4.6 m waves, foam) still reads as "rough" more than "violent", because the ship does not pitch hard and there is no spray. Fix candidates: spray particles and heavier pitch (J-module). The mirror had a bug that hid the rain (PIL's ImageDraw replaces pixels instead of blending, so the fog rectangle erased the streaks); it is fixed in the script, and the Godot painter blends normally.

## 9. Performance strategy (dev PC and final game)

- **The model is cheap and caches itself:** `sample()` is 3-4 hash-noise evaluations per field; the ship resamples every 9.4 real seconds, the slice smooths in between. Region lookups (the most expensive call, ~10 distance evaluations) happen at most 1 per second for the look, 1 per 1.5 s for icebergs, and 30 per frame for chart reveal.
- **No save state for weather or wildlife**: both are recomputed from (x, y, t), so there is nothing to serialise, nothing to leak, and no per-entity update cost far from the player.
- **Draw budget:** about 400-700 draw commands per frame in the slice, all batched 2D (no shaders, no 3D, no screen texture), which is what Compatibility on an HD 3000 handles best. If it is too slow, the first levers are `WAVE_ROWS` (17), the rain count (150), the cloud count (3-14) and the star count (70), all constants at the top of `sea_painter.gd`.
- **Quality scales up without touching the data:** the final game replaces polygons with the final art, adds the HD-2D lighting stack on capable hardware (A1), and uses the same `look_at` and `sample` outputs. The dev profile only lowers counts.
- `perf.*` tuning keys reserve the limits for the real game: `perf.weather_grid_km` 40, `perf.active_radius_km`, `perf.max_instanced_creatures`, `perf.max_school_instances`, `perf.sighting_min_gap_s`.
- Not measured: frame time on any machine. The first FPS reading (shown bottom left in the slice) is the first measurement.

## 10. Tests and what they prove

| Check | Proves | Does not prove |
|---|---|---|
| `test_ocean.py` | noise range and determinism; geography (cold north, warm equator, regions keep promises); Herald = storm + 1 day; the slice weathers exist where claimed; ship speeds and no-go; 40 + 40 + 8 golden cases match; sighting rate and variety | that the numbers feel right |
| `ocean_checks.py` | region contract (areas, identity, pairwise difference, species temperature) | that regions feel distinct to a player |
| `gd_logic_check.py` | the GDScript formulas equal the Python ones on 186 cases | that the GDScript runs |
| `tests/test_ocean.gd`, `test_sea_state.gd`, `test_console.gd` | (written) the same fixtures and rules inside Godot | **not run** |
| gdparse + gdlint | syntax and style | semantics |

## 11. Acceptance checklist - ALL UNVERIFIED (to be ticked on the user's PC)

1. `tools\run_godot_tests.bat` shows `test_ocean`, `test_sea_state` and `test_console` passing (they replay the golden files inside Godot).
2. `tools\run_slice.bat` opens without script errors in the Output panel.
3. Press 1: a warm tropical dawn, rain, a ship that moves when you hold nothing (the wind pushes it) and turns with A/D.
4. Press 2, 4, 5, 6, 7: five clearly different looks (clear noon, thick fog with a 0.7 km sight line, grey long swell, gale, ice). Say which ones look wrong.
5. At checkpoint 5 note the Herald Swell line; wait 15 real minutes (do not jump): the gale must arrive on its own.
6. Press P: the clock text stops and the ship stops. Press M: the chart opens and time stops; N reveals the whole world in a few seconds without a visible stall.
7. `route status` and `ocean 5600 520 13.5` print region, wind, waves, visibility and light.
8. FPS reading at the bottom left on the dev PC: report the number at checkpoints 2 (clear) and 6 (gale). Target 30+ on Dev-Lite.
9. Wildlife: sail 5 real minutes in the Kettle Seas; expect 1-3 sightings and journal entries; a whale blows; birds fly.
10. The look: is it the right direction, or do you want the sea view to change? (This is the biggest open design question: the 2D side view vs the final HD-2D 3/4 view with the camera on the ship.)

## 12. Decisions

E1-1 World 9,000 x 6,000 km, latitude by y. E1-2 No wrapping; the rim is a storm wall. E1-3 One reference speed (14.9 km per real minute), exact times derived from it; real wind decides the rest. E1-4 Ten regions, each with a unique nav_rule, blended not bordered. E1-5 Weather is a pure function of (x, y, t); nothing saved. E1-6 Herald Swell = the next day's storm, always. E1-7 SeaState owns no clock; paused clock moves nothing. E1-8 Sightings are deterministic, not saved, honest about visibility. E1-9 Seed 87 species, plan 200+ in five batches; 5-25 percent fictional. E1-10 Debug jumps place ship and clock; time acceleration does not exist (T1-2 stands). E1-11 The slice uses plain 2D so it runs on the dev PC; quality is added on top, never baked into data. E1-12 Python is the reference model; GDScript twins are held to it by golden files and `gd_logic_check.py`.

## 13. Not verified / risks

- Every GDScript file of E1 (nothing has run in Godot). The likeliest first-run failures: a type-inference error that gdparse/gdlint cannot see (Godot's analyzer is stricter on `:=` with untyped calls); a draw call that behaves differently from what the Python mirror shows; the `DebugConsole` autoload not being present (then the slice builds its own state).
- Whether 14.9 km per real minute and the 8.4-hour slice feel like an enormous ocean or like a chore. The numbers are data (`ship.sail_speed_kmh`, `ship.hull_speed_factor`, T1 day length).
- The 2D side view is a presentation stand-in. The A3 art direction is 2.5D HD-2D with a ship-fixed camera; the model does not depend on the view.
- The fog-of-war chart colours cells by region palette only (no ice, no depth).
- Nothing yet places islands, ships, wrecks or events: "never empty" is only met by weather, wildlife and icebergs.
- Species values and abundances are provisional estimates from general natural history.

## 14. Files added or changed by E1

Data: `game/data/world/{regions,climate_bands,slice_route}.json`, `game/data/schemas/{region,climate_band,species}.schema.json`, `game/data/wildlife/*.json`, `game/data/tuning/tuning_ocean.json`.
Python: `tools/data_tools/{ocean,wildlife,sea_state,ocean_checks,test_ocean,gd_logic_check}.py`, `tools/world/{render_world_map,render_sea_views,species_quota,slice_autopilot,build_species}.py`, `tools/check_all.py`, `tools/check_project.py`.
GDScript: `game/core/{ocean,wildlife,sea_state}.gd`, `game/core/console_commands.gd` (route, ocean), `game/ui/{ocean_slice,sea_painter}.gd`, `game/ui/ocean_slice.tscn`, `game/tests/{test_ocean,test_sea_state,test_console}.gd`, `game/tests/fixtures/{ocean,wildlife,sea}_cases.json`.
Docs/art: this file, `art_bible/world_map_e1_v2.png` (the first render `world_map_e1.png` was replaced), `art_bible/sea_views_e1/`.
Launchers: `tools/run_slice.bat`, `tools/run_slice.sh`.
