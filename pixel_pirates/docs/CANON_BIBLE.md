# CANON BIBLE - Crown of the Seas (working title) - v1.2 (after A2-A7, B1, B2, T1 time revision, B4 economy, E1 ocean and slice, V1 visual lock)
Drive folder: "Pixel Pirates". Repo path: pixel_pirates/.

## Hard content rules
No female characters in the crew. No sexual content. No gods/religion/atheism promotion/insults to religion; mysticism stays neutral (legends, curses, ancient beasts, pirate lore).

## World scale rules (non-negotiable)
Enormous ocean; crossing it is the core experience. 50+ islands (normal-sized, quick to explore). Only a minority in clusters of 2-4; most isolated; some extreme dead-ocean gaps. No island visible from another unless a deliberate landmark. Open sea never empty. Exact sailing times go in the Canon (E2/N13). Island tiers: Tier 1 about 12-15, Tier 2 about 20-25, Tier 3 about 15-25.

## Core pillar
Realistic pirate-life simulation (food, fishing/hunting, cooking, water, health/disease, ship wear, crew labor, morale/pay, ammo, cargo, weather). Fair tension; difficulty modes Story / Normal / Hardcore Realism. Every island offers at least one survival-relevant thing.

## Developer hardware (fixed fact)
Intel Core i5-2410M 2.3 GHz (2 cores/4 threads), 3 GB DDR3-1333, Intel HD Graphics 3000, 1366x876, Windows 64-bit.

## Decisions
A1-1 Godot 4.7.2-stable standard (non-.NET), locked.
A1-2 Compatibility renderer first; Forward+ "Ultra" optional later (decision gate after vertical slice).
A1-3 typed GDScript; GDExtension only if profiling demands (gates J7, J22).
A1-4 pixel textures, nearest filter, integer texel density, FOV ~22 deg, camera pitch ~39 deg; internal render size is a quality setting.
A1-5 tilt-shift via own full-screen shader (ColorRect + screen texture), not built-in DOF.
A1-6 ship-fixed origin, world in 64-bit data.
A1-7 distribution undecided; no Steam SDK/GodotSteam/steam_appid; plain Windows exe+pck; achievements are internal events; Platform seam only when needed.
A1-8 targets: shipping min = Win10 64-bit, 4 GB RAM, OpenGL 3.3 GPU; recommended = 8 GB, GTX 650/HD 7750 class+; Dev-Lite for dev PC (683x438 internal, shadows/bloom off, 2 px blur, tex < 256 MB, process < 1.2 GB).
A1-9 engine version locked.
A1-10 quality ladder: Dev-Lite / Standard / (Ultra). Quality = data profile.
A1-11 game logic must be headless-testable (no GPU).
A1-12 Look Lab (Python still renders of the look) proposed for A3/A4.

## Verified external facts (2026-10-17)
Godot 4.7.2-stable (2026-08-18), MIT. Compatibility renderer needs OpenGL 3.3; Forward+/Mobile need Vulkan 1.0+. ANGLE (OpenGL ES 3.0 over Direct3D 11) fallback exists on Windows. Compatibility lacks DOF blur, volumetric fog, SSR, SDFGI, VoxelGI, CompositorEffects, HDR; it has glow, fog, SSAO, shadows, decals, screen-texture shaders, full-screen post.

## Not verified
All GDScript is parser-checked only (never executed by me). The user reports Godot already runs on the PC, but nothing visual/performance was measured. Look Lab stills approximate the planned shader; no Godot shader exists yet. Unity/Unreal facts. Hardware targets are design targets.

## File structure (FINAL, A2)
pixel_pirates/ { README.md, .gitignore, .gitattributes, .editorconfig, docs/, art_bible/, tools/, game/ }
game/ (= res://) { project.godot, .gdlintrc, core/, data/, systems/{survival,economy,crew,ship,combat,weather}/, world/{ocean,islands,cities}/, ui/, shaders/, audio/, art/{placeholder,final,manifest}/, tests/ }
Dependency rule: systems/ never imports world/ or ui/; core/ imports nothing; systems talk via Bus signals or passed-in data.
Autoloads: Log, Bus, Quality, Assets, Data (registry). Core utilities via preload constants (Ids, DataLoader).
tools/: island_kit/ (bake, island_checks, sameness, shapes, prng, preview, report, tests), data_tools/, check_project.py, install_hooks.sh, hooks/pre-commit, placeholder/ (generator), looklab/ (stills + report), probes/gpu_probe_v2/.
docs/: A6_ISLAND_KIT.md, A6_ISLAND_KIT_REPORT.md (generated), A5_DATA_ARCHITECTURE.md, PROVISIONAL_LEDGER.md (generated), A1_TECH_STACK.md, A2_STRUCTURE_AND_CONVENTIONS.md, A3_ART_BIBLE.md, A4_PLACEHOLDER_PIPELINE.md, CANON_BIBLE.md, ART_STATUS.md (generated).

## ID grammar (A2)
Data: <kind>_<slug> lowercase; kinds isl reg crew npc item rcp ship evt loc fac qst dlg clue mode kit tpl. Islands numeric isl_001..isl_999 (the old "I001" = isl_001).
Assets: prefixes spr til prp shp ico fx ui bg (e.g. spr_crew_mannequin_captain, til_water_deep_a, ico_item_hardtack).

## Art canon (A3/A4)
Look: HD-2D (pixel sprites upright in a 3D scene), measured from the references. Art grid 640x360; integer scales 720p x2, 1080p x3, 4K x6. 24 px/m land and deck, 12 px/m open sea.
Camera: FOV 22 deg, pitch 39 deg land / 48 deg sea, focus plane 38.6 m. Humanoid cell 48x64, body 42 px = 1.75 m, pivot (24,60), 4 dirs x 7 anims (idle4@180, walk6@100, run6@70, work6@120, attack5@70, hit3@80, death8@110).
Tile 48x48 (2 m). Icon 24x24. Ships are 3D models (stand-in billboard only). Palette: 22 ramps x 5 = 110 colours in game/data/look/palette.json, no pure black/white; fire-ramp pixels are self-lit.
Post: tilt-shift focus_y 0.55 (10 px @1080), vignette 0.70, LDR bloom 0.65/0.35, grade sat 1.15 contrast 1.08; moods golden_hour, overcast, storm, night_fire, frozen_dawn. state_grades = the look as a survival HUD.
Dev-Lite = 640x360 internal (supersedes 683x438), no shadows/bloom/shafts.
38 placeholder assets (4 mannequin sheets, 7 tiles, 10 props, 1 ship stand-in, 16 icons); replace by dropping same-named files into game/art/final/<category>/.

## Decisions added
A2-1 Godot project in game/. A2-2 stays inside Videos-motion for now, split later with git subtree. A2-3 JSON for all data. A2-4 dev PC needs no Python (generated art is committed). A2-5 preload constants for core utilities. A2-6 own headless test runner. A2-7 plain git, Git LFS gate at first binary > 5 MB or repo > 500 MB. A2-8 strict machine-checked IDs. A2-9 content rules enforced by tools/check_project.py.
A3-1 art grid 640x360, 24/12 px per metre. A3-2 camera 22 deg FOV, 39/48 deg pitch. A3-3 ships are 3D models. A3-4 master palette 110 colours. A3-5 warm shadows (measured), cool fill only in storm/night/frozen. A3-6 look = survival HUD (state_grades). A3-7 Dev-Lite 640x360. A3-8 Look Lab is the GPU-free look approval tool.
A4-1 committed generated placeholders, drop-in replacement through the Assets resolver. A4-2 QA built into the generator (palette lock, colour budgets, no clipping).
A1-10 amended: Dev-Lite internal 640x360.

## Data architecture (A5)
Envelope {schema:1, kind, records}; schemas in game/data/schemas (item, difficulty_mode, tuning, region, island, crew_member, recipe, save_state). Unknown keys rejected. Two validators (Python tools/data_tools, GDScript core/schema.gd) proven equal by one 35-case fixture file. World rules (neighbour symmetry, sail distance >= straight line, landmark-only visibility, every island >= 1 survival_offer) are enforced in Python and (since A7) in GDScript, proven equal by game/tests/fixtures/world_cases.json.
Content rule 1 enforced in the crew schema (gender enum ["male"]) and in check_project.py.
Tuning: every balance number via Tuning.f(key); scale mul/div by one of 9 difficulty multipliers (hunger_rate thirst_rate spoilage_rate disease_rate ship_wear_rate morale_decay_rate ammo_dampness_rate weather_severity fatigue_rate) or a per-system override 0-3. Modes: mode_story / mode_normal / mode_hardcore.
Save: sha256 envelope, .tmp->.bak->main atomic write, backup recovery, SAVE_VERSION 1 with migrations, 64-bit seeds as decimal strings.
SEED NUMBERS ARE PROVISIONAL PLACEHOLDERS (78 tuning records after T1, docs/PROVISIONAL_LEDGER.md), NOT Canon survival numbers. N-owner tags are proposed. B3 final only when no N* rows remain.
Decisions: A5-1 JSON envelopes + schema files. A5-2 two validators + shared fixtures. A5-3 tuning through one accessor with difficulty scaling and overrides. A5-4 provisional ledger. A5-5 hardened save format. A5-6 export filter must include *.json.
GDScript half of A5 is unrun (no Godot in sandbox).

## Island construction (A6) - sizes are PROVISIONAL (owner E7)
Pipeline: island record + island_template + kit + seed -> tools/island_kit/bake.py -> committed baked map game/data/islands/maps/<id>.map.json. The game loads baked maps, never generates. source_hash flags stale maps; grid/content hashes flag hand edits.
Grid: tier 1 = 192x192 tiles (384 m), tier 2 = 128 (256 m), tier 3 = 80 (160 m); 1 tile = 2 m; walk 1.4 m/s. Explore budget (walk all POIs from the landing): T1 45 min, T2 16, T3 6.
Terrain classes: deep ~, shallow -, beach ., ground g, upland u, rock r, cliff #; elevation 0-15. Walkable = all but deep and cliff.
Templates (10): tpl_blob_isle, tpl_atoll_ring, tpl_crescent_bay, tpl_ridge_spine, tpl_twin_lobes, tpl_cone_volcano, tpl_mesa_cliffs, tpl_stack_field, tpl_tidal_flats, tpl_fjord_cleft. Slot kinds: survival, hook, secret, story, camp.
Kits (5): kit_tropical, kit_arid, kit_temperate, kit_frozen, kit_volcanic (placeholder art mapping).
Hook kinds (20): wreck_field ruin creature_den natural_wonder puzzle_site hermit trade_post hazard_field hidden_cache shortcut beacon_tower ship_graveyard tidal_secret echo_cave sunken_road carcass_whale weather_vane_rock salt_works mapmaker duel_ground.
Silhouette Quota: 32x32 dry-land silhouette, any rotation/flip, overlap >= 0.85 = alike (calibrated on 100 islands); max 4 islands per hook kind, max 3 per template+kit, neighbours may not share a hook kind.
Decisions: A6-1 bake, don't generate. A6-2 explore time is a measured per-tier budget. A6-3 slots guarantee a survival POI per declared offer and a hook per island. A6-4 Silhouette Quota. A6-5 fixtures isl_901..910 are test data, not registry. A6-6 need about 16 templates by E3 (proposal). Open: ship navigability of shallows (E8).
Fixture islands: 10 in game/tests/fixtures/islands, one per template.

## Tooling (A7)
`python tools/check_all.py [--quick] [--godot PATH]` = every automatic check, report in build/check_report.md. `tools/run_godot_tests.bat|.sh` = in-engine tests without Python (Godot path from env GODOT_EXE or tools/godot_path.txt). Engine result is trusted only from the "TESTS: N checks, M failed" line plus absence of SCRIPT/Parse errors.
check_project.py also checks: registry doc freshness, duplicate GDScript member names (var vs func), dead res:// paths.
Debug console (autoload DebugConsole, debug builds, F1 or backtick): help echo clear data check tuning mode island tp time give inv seed save load quality log perf. `time` = show / watch / tick <real_s> / live on|off (debug HUD follows real time) / pause|resume <reason> / add / set (add and set are debug-only jumps). Core in core/console_commands.gd (headless-tested), UI in ui/debug_console.gd. GameState (core/game_state.gd) mirrors the save_state schema until J1.
Island workbench: tools/island_kit/new_island.py (spec -> seed search with Silhouette Quota -> bake -> check -> preview -> record). ISLAND_REGISTRY.md generated by tools/data_tools/registry_doc.py.
Decisions: A7-1 console core separate from UI. A7-2 GameState mirrors save schema. A7-3 world rules twice + shared fixture. A7-4 never trust Godot exit code alone. A7-5 static Godot-mistake checks in check_project. A7-6 workbench enforces the quota at creation. A7-7 generated, freshness-checked registry doc. No in-engine map editor until F0 (data volume decides).
GDScript of A6 + A7 is unrun (no Godot in sandbox).

## Pillars (B1) - full text in docs/B1_PILLARS.md
One sentence: you are the captain of a ship full of people, crossing an ocean too big to cheat, and every crossing is a sum you must get right before the sea shows you what you got wrong.
P1 THE SEA IS THE GAME (bands in real minutes at the fixed T1 time scale: Hop 3-8, Passage 8-25, Crossing 25-60, Dead Ocean 60-120, i.e. 0.2-0.5 / to 1.7 / to 4 / to 8 game days; play time sea 40 / islands 35 / ship+crew 17 / combat at most 8 percent). P2 EVERY VOYAGE IS A SUM (the Reckoning). P3 HARD BUT FAIR (Warning Ladder 48 / 16 / 6 game hours at current consumption = 30 / 10 / 3.75 real minutes, T1; 3 warning steps before any loss; 2 recovery options at every critical state). P4 A SHIP IS PEOPLE. P5 EVERY ISLAND ANSWERS A QUESTION. P6 THE MAP PULLS YOU (no crossing of Passage length or more without a payoff).
Original idea: the Reckoning. The game never hides arithmetic, only the sea hides information. Forecast band +/-25 percent on ordinary sea, +/-40 percent on dead ocean, narrowest ever +/-10 percent; information (navigator, charts, lore) is cargo that narrows the band; stocks are shown as time left at current consumption (days above 2, hours below) and as margin against the HIGH end of the band.
Pillar Gate: six yes/no questions per feature (docs/templates/PILLAR_GATE.md). Anti-pillars: not a combat game, not a grind or base-builder, no reflex QTEs, no hidden timers, no pirate cliches (arr dialect, shoulder parrot, plank walking, literal X marks).
Tuning (game/data/tuning/tuning_design.json, 17 provisional keys): warn.*_hours (48/16/6, min steps 3), recovery.min_options 2, plan.forecast_spread_sea/dead/min, voyage.* bands, share.*. Owners N13, B6, E8, E9, E2, B7. Machine-checked by tools/data_tools/design_checks.py (invariants + content-word lint over all data files).
Survival coverage table (11 systems with question, warning, recovery, island offer tag, proposed owner N1-N11) lives in the doc; N12-N14 not yet assigned.
Decisions: B1-1 fair-loss model (setbacks climb the ladder; ship/captain loss only after rungs 1-3; last-chance rescue by mode: Story always, Normal once per act, Hardcore none; B6 finalises). B1-2 real time with pause-to-plan (kept); its x1/x4 acceleration is SUPERSEDED by T1-2 (no acceleration at all). B1-3 Hardcore narrows widths and removes recommendations but keeps the ladder, honest numbers and recovery minimum.
Not decided here: slow-process rates (N13; the day length is fixed by T1), exact lose conditions (B6), crew names and voices (D).

## Core loop (B2) - full text in docs/B2_CORE_LOOP.md
Wheel: PLAN the sum -> SAIL the days -> ANSWER the island -> PROVISION -> collect the CLUE -> PLAN. Average cycle 48 real min = 3.2 game days (1.8 at sea). Modelled play-time split sea 41.3 / islands 34.4 / ship+crew 19.8 / combat 4.6 percent (targets 40 / 35 / 17 / max 8; ranges 30-50, 25-45, 10-25, 0-12). Rescaled by T1 (before T1: 39.3 / 35.4 / 20.9 / 4.4).
Five loops: L1 Moment (max 4 min quiet), L2 Watch (150 s), L3 Day (15 min, Morning Report), L4 Voyage (T1 bands), L5 Visit (6/16/45 min explore + 2 min provision = 0.4 / 1.07 / 3.0 game days).
Original idea: EIGHT BELLS. Ship's bells every half hour, eight bells ends a 4 h watch; six watches: Middle 00-04, Morning 04-08, Forenoon 08-12, Afternoon 12-16, Dog 16-20, First 20-24. Audio (T1): a half hour is 18.75 real s, so only the watch-end bell (eight bells, every 150 s) is audible by default; half-hour bells are a HUD tick (option). The Morning Report at 08:00 is a pause screen (20 s read, at most 3 percent of a day); it carries stocks as time left, ship, one crew line, a 24 h outlook band, one decision card, and writes the captain's Log line. It is NOT a fast-forward stop any more (there is no fast-forward) and does not count as the quiet-breaker (moments carry the 4-minute rule).
Moments: ambient (free), choice (at least 2 per 10 min), crisis (at most 1 per 10 min).
Cycle mix (campaign, owner B8): Hop 25 / Passage 40 / Crossing 25 / Dead 10 percent, ending at Tier 3 / 2 / 1 / 1 islands. Visiting all 50 islands is about 40 h of play and 161 game days.
Code: core/voyage_clock.gd (pure functions) + core/world_clock.gd + tools/data_tools/voyage_clock.py (100-case and 4-scenario hand-written fixtures), tools/data_tools/loop_model.py, console command `time`. Tuning: tuning_loop.json (14 keys) + tuning_time.json (23 keys), all provisional. All machine-checked.
Decisions: B2-1 SUPERSEDED by T1-1 (two clocks removed). B2-2 daily Morning Report pause screen (kept). B2-3 SUPERSEDED by T1-3 (a visit costs supplies on the one clock; the old one-day cap is removed).

## Time (T1) - the one world clock - full text in docs/T1_TIME_SYSTEM.md (PROVISIONAL, owner N13)
1 game day = 15 real minutes (tuning time.real_minutes_per_game_day, locked by a check), at sea AND ashore. 1 real s = 96 game s; 1 game hour = 37.5 s; a 4 h watch = 150 s; a half-hour bell = 18.75 s. Continuous, fixed rate. No player acceleration (no x2/x4, no Engine.time_scale). Pause only for planning screens, the Morning Report and menus; pause reasons are a set; paused time advances nothing (supplies, events, crew needs, weather). Time never jumps or changes speed between sea and island (WorldClock.set_location is bookkeeping only).
Day/night (24 h, smooth; provisional, subject to visual testing): Dawn 05-07 (75 s), Morning 07-10 (112.5 s), Day 10-17 (262.5 s), Sunset 17-19 (75 s), Evening 19-20 (37.5 s), Night 20-05 (337.5 s). Lighting is driven by a continuous daylight level (night floor 0.04, dawn end 0.55, sunset end 0.30, smoothstep between keyframes) and continuous band weights, never by the hard band label; the same curves on every quality profile.
Voyage bands in game days: Hop 0.2-0.5, Passage to 1.7, Crossing to 4, Dead Ocean to 8 (worst case +40 percent = 11.2). Ladder 48 / 16 / 6 game hours (Hardcore about 30 / 10 / 4). Visit cost: full T1 3.0 days, T2 1.07, T3 0.4 (typical 0.7 of that); cap loop.visit_cost_days_max 3.5; the island's survival offer must pay for the visit.
Slow-process compression (so they land in 2-6 real hours): water foul after 10 warm days (150 min), scurvy onset 14 days (210 min; hardcore 10, story 28), hull wear 0.5 percent per day at sea, barnacle penalty 12 percent per month, morale decay 2 per day, season 20 days (5 h), gale 12 h. Fast processes stay realistic in game hours: fish cast 1.5 h, cook 1 h, patch leak 2 h, plank 6 h, careen 24 h, sleep need 8 h, 3 meals per day.
Ship stores hold (days of full-crew rations): start 8, mid 14, late 24. Crossing worst case 5 d <= 8 < Dead Ocean worst case 11.2 <= 14. Dead Ocean therefore needs preparation or a better ship; a Crossing does not.
Worked Reckoning (replaces the 14-day one): 12 men, 3-day Crossing, band 2.25 / 3 / 3.75 days; 21 kg hardtack and 100 L water give +0.1 d (hardtack) and -0.4 d (water short).
Save format unchanged (SAVE_VERSION 1, clock.t_seconds = integer game seconds, meta.playtime_s = real seconds). Pause reasons are runtime-only and not saved; a loaded game must start paused until the player confirms.
Decisions: T1-1 one clock, 15 min per game day everywhere (supersedes B2-1). T1-2 no player acceleration (supersedes B1-2's x1/x4). T1-3 consumption continues ashore on the same clock; visit cost cap 3.5 days (supersedes B2-3). T1-4 ladder measured in game hours. T1-5 nights cannot be skipped, so night must be playable (E2 moment tables per day and night). T1-6 slow biological and wear processes are compressed, fast processes are not. T1-7 only the watch-end bell is audible by default. T1-8 every time-dependent system consumes the game dt from WorldClock.tick and nothing else.
Not verified: any GDScript of T1 (no Godot in the sandbox); the visual look of the six bands; whether a 5.6-minute night is too long or too short in play; whether 15 minutes per day feels right.

## Economy (B4) - "Heavy Money" - full text in docs/B4_ECONOMY.md (PROVISIONAL; owners B4, B5, B6, F1, N-modules)
Unit: the real (piece of eight). **Money is cargo:** a Piece of Eight (`item_coin`, value 1) weighs 27 g; a Gold Doubloon (`item_doubloon`) weighs 27 g and is worth 16; a Silver Bar (`item_silver_bar`) is 10 kg, worth 370 (same value per kg as coin, 37). Changer fee 6 percent each way (round trip 12). Pearls (60 for 0.1 kg) are the densest wealth. Pocket coin is light at this time scale (the mid ship, 1,200 reales, is 32 kg); **weight bites on windfalls**: a start-stage chest is 6 silver bars = 60 kg = 2,220 reales = 1.1 days of the crew's stores (55 kg/day for 12 men). Chests scale with region wealth (114 kg mid, 192 kg late). Chance per visit: Tier 1 5 percent, Tier 2 2, Tier 3 0.5; the choice is silver, gold (fee) or leaving some.
**Prices are deterministic:** price = base x region factor x exp(x) x (1 +/- spread/2), spread 20 percent. x is the market's memory of the player's trades (sell pushes down, buy pushes up by V/depth) and halves every 6 game days. Depths (base value): Tier 1 4,500, Tier 2 2,200, Tier 3 1,100, times stage wealth 1 / 1.9 / 3.2. Safe sale 20 percent of depth. Price gap between regions 0.6 + 0.12 per game day, cap 1.2. No random price noise, no cooldowns. Splitting an order earns exactly the same money (checked).
**Trade items:** salt 1, sugar 6, cloth 14, tobacco 22, furs 40, spice 90 reales per kg. **Re-baselined:** hardtack 2, salt meat 5, fresh fish 2, water barrel 6, grog 3, gunpowder 30, cannonball 5, lime 4, bandage 3, rope 8, plank 7, tar 10, canvas 14, hammer 15, fishing line 4. Ration basket 3.58 reales per man-day.
**Running cost per game day:** start 72.6 (12 crew), mid 160.6 (20), late 270.4 (30). Crew 12 / 20 / 30, officers 3 / 5 / 7. **Income per game day (campaign average):** 127 / 243 / 409; surplus 42 / 23 / 23 percent of running cost; trade is 30 percent of income. Cycle net at start: Hop +18, Passage +55, Crossing +175, Dead Ocean +285 reales (1.35-2.27 per real minute: no trap, no best voyage). Dead Ocean landfall x1.5 salvage and treasure.
**Crew pay:** loot shares from prize income only (combat prizes, salvage, treasure), never from trade. Pool 30 percent of that income, split captain 2.0 / officer 1.5 / hand 1.0, paid every 10 game days (2.5 real hours); about 1.65 reales per hand per day at start. **Starting purse 600 reales** (8 days of running cost). Upgrade anchors (B5 sets real prices): small 400, mid ship 1,200 (about 9.8 h of play), late ship 2,200 (about 14.8 h), chart 150.
**Anti-grind (machine-checked):** the best endless two-port shuttle earns 14 reales/day at start (running cost 73), 25 at mid, 39 at late. No economic difficulty multiplier; Story and Hardcore touch the food bill only through hunger (N1).
Code: tools/data_tools/market.py + core/market.gd (twins, 40 hand-calculated cases in tests/fixtures/market_cases.json), tools/data_tools/economy_model.py (model and invariants, in check_project/check_all), tools/data_tools/test_economy.py, tests/test_market.gd. Tuning: tuning_economy.json (61 records). Items: 25 (9 new). Assets: 50 (9 new icons).
Decisions: B4-1 money is cargo (one coin item, weighed). B4-2 deterministic price memory. B4-3 shares from prize income only. B4-4 safe sale 20 percent of depth. B4-5 trade capped by market depth. B4-6 grinding stopped by the memory itself, no cooldowns. B4-7 risk pays (Dead Ocean x1.5). B4-8 no economic difficulty multiplier. B4-9 B5 sets real upgrade prices within invariant windows. B4-10 starting purse 600.
Not verified: any GDScript of B4 (no Godot in the sandbox); whether the first ten hours feel right (the model is an average); a start-stage windfall (2,220) is worth about two mid ships (flag for B5); the starter purse cannot fund a full lot; UI for ledger and changer does not exist yet.

## The Ocean (E1) - full text in docs/E1_WORLD_SPEC.md (PROVISIONAL, owner E1; GDScript never run in Godot)
**World:** 9,000 x 6,000 km, y = 0 north, latitude = 75 - y/40 (+75 to -75). No wrapping; the rim is a storm wall and the ship is clamped. Year 80 game days (20 real hours), start phase 0.25. Islands 58 planned: Tier 1 14, Tier 2 22, Tier 3 22 (keys world.islands_t1..t3); placement is E2/E3.
**Exact sailing times (sloop, reference condition: beam reach in 14 kn of wind = 5 kn through the water; ship.sail_speed_kmh):** 9.3 km per game hour = **14.9 km per real minute**. Horizon about 10 km = 40 s. Hop 45-119 km (3-8 real min), Passage 119-372 km (8-25), Crossing 372-893 km (25-60), Dead Ocean 893-1,786 km (60-120). Edge to edge about 10 real hours. Real wind decides the rest: measured 15.8 km per real minute along the Kettle trade, 12 km in two game days becalmed in the Glass Sea, 317 km per game day running east in the Storm Belt (the way back is a different voyage), 0 in the polar pack. Supply budgets must use the T1 bands above (game days) AND check the wind of the route.
**Ten regions (seed km; nav_rule):** Kettle Seas (7000,2500; squall_wall; tropical start); Shattered Reaches (1800,2650; tide_gated_channels); Sunward Banks (7400,2050; monsoon_reversal); Glass Sea (4500,3000; windless_mirror); Dead Ocean (4400,4150; star_only_drift); Green Verge (1900,1250; pilot_coast_tides); Fogbound Expanse (5200,1250; fog_bell_pilotage; median sight 1.1 km); Grey Marches (5600,500; iceberg_watch); Storm Belt (5000,4950; westerly_run; median wind 24.4 kn, waves 5.4 m); White Hollow (4200,5700; ice_leads; Treasure Island reserved). Regions blend over 160 km; no hard borders. Machine-checked identity contract (areas 4-20 percent, promises kept, pairwise difference on 3 of 10 axes, spacing, species fit, 10+ species each).
**Weather and light:** a pure function of (x, y, time) via integer-hash noise (no saved state, Python and GDScript agree to 1e-4). Systems about 400 km across, building over 3+ real minutes; gale = smoothstep 0.66-1.20 of the weather index. **Herald Swell: herald(t) = storm(t + 1 game day), always** (15 real minutes of fair warning: long heavy swell, no wind). Light = max(floor, daylight x peak) from the T1 curve with latitude and season.
**Wildlife:** 87 species seeded (target 200+; plan: 113 more in 5 batches, White Hollow, Glass Sea and Dead Ocean first), 80 real, 7 fictional (Looking-glass Ray, Ghost Lantern, Stormglass Medusa, Bellsinger, Hollow Whale, Trench Angler, Grandfather Squid). Deterministic sightings: one roll per 1.5 real minutes per 40 km cell, p 0.55, distance = visibility x 0.15-0.85, abundance under 0.02 = absent.
**Ship at sea:** SeaState owns no clock; integrates the game seconds the one clock returns (sub-step 600 game s, resample 900 game s). A paused clock moves nothing.
**Slice "The Three Weathers":** 7 checkpoints from the Kettle dawn squall to the Ice Edge, about 3,340 km straight, about 8.4 real hours sailed (autopilot estimate). Debug jumps (keys 1-7 or `route <n>`) place ship and clock and never accelerate time. Console additions: `route`, `ocean`.
**Code:** core/ocean.gd, wildlife.gd, sea_state.gd; ui/ocean_slice.gd, sea_painter.gd; Python twins in tools/data_tools; golden files ocean_cases.json, wildlife_cases.json, sea_cases.json; `gd_logic_check.py` replays them against the GDScript formulas (186 cases, 0 differences; not a Godot run). Tuning: tuning_ocean.json (50 keys). Data: 10 regions, 6 climate bands, 87 species.
**Decisions:** E1-1 world 9,000 x 6,000 km, latitude by y. E1-2 no wrapping, storm-wall rim. E1-3 one reference speed 14.9 km per real minute; times derived. E1-4 ten regions, unique nav_rule each, blended. E1-5 weather is a pure function of (x, y, t). E1-6 Herald Swell = next day's storm. E1-7 SeaState owns no clock. E1-8 deterministic, visibility-honest sightings. E1-9 87 seed, 200+ plan, 5-25 percent fictional. E1-10 debug jumps only, no acceleration. E1-11 slice in plain 2D, quality added on top. E1-12 Python is the reference; GDScript held to it by golden files.
**Not verified:** every GDScript of E1 (no Godot run); frame time on any PC; whether 14.9 km per real minute feels enormous or tedious; the 2D side view versus the final HD-2D camera; sea-view stills are a Python mirror, not Godot captures.

## Visual direction lock (V1, user-locked 2026-10-18) - proposal in docs/E1B_HD2D_PROPOSAL.md
The final game is **HD-2D in the manner of Octopath Traveler / Octopath Traveler II** (the two reference images): pixel-art ships, islands, ports, vegetation, buildings; an **angled top-down camera** with real depth (not side-view, not realistic 3D); layered scenery, dynamic lighting and shadows, atmospheric fog, depth of field where appropriate, controlled colour grading; an ocean that changes across tropical, temperate, stormy, frozen and mysterious regions; distinct rain, fog, storm, wave, ice and light looks; one cohesive art direction. The ship must visibly respond to steering; the ocean, islands and effects must convey a vast world. The E1 side-view scene is a **temporary technical prototype** (weather, ocean data, clock, steering) and is NOT the approved look. Priorities: 1 validate the prototype in Godot, 2 working sailing controls, 3 representative HD-2D prototype, 4 low-end performance validation, 5 expand the world. E2 does not start until the prototype's outstanding issues are investigated and the next step is defined. The world ambition is unchanged (Pacific-scale ocean, 10 regions, polar and mysterious regions, 200+ species).
**Pending decisions (proposal section 6):** D1 render path (recommended: real 3D scene with pixel sprites, 2D fallback possible), D2 ship asset (recommended: layered pixel-art sprite sheets, baked from a 3D reference; would supersede A3-3 "ships are 3D models"), D3 camera north-up fixed (recommended), D4 order.
**E1b changes:** compass-fixed sky and swell (turning visibly turns the world), ship leans into turns, IN IRONS warning, scripted self-test (`tools\run_slice_selftest.bat`, not yet run), spec wording fix (14 kn is the reference wind; the sloop makes 5 kn).

## Island registry (50+ planned)
Generated: docs/ISLAND_REGISTRY.md. Currently empty. Format: ID (isl_NNN) | name | tier | biome | position | distances to neighbours | status (planned/designed/built/tested). Filled from E3.

## Open questions
V1/E1b: run `tools\\run_slice_selftest.bat` on the dev PC and send build\\slice_selftest.txt (includes GPU adapter and driver); answer D1-D4 in docs/E1B_HD2D_PROPOSAL.md; E2 is blocked until then.
E1: run tools\\run_godot_tests.bat (new: test_ocean, test_sea_state, test_console), then tools\\run_slice.bat and answer the 10-point checklist in docs/E1_WORLD_SPEC.md section 11; confirm the E1 decisions, especially the reference speed and the sea-view direction. E2 must place islands against the region quotas and the exact times above.
B4: first run of core/market.gd and tests/test_market.gd on the user's PC; confirm the B4 decisions (Heavy Money, shares from prizes only, deterministic prices); B5 must price the ships against the windfall size.
T1: first run of core/voyage_clock.gd, core/world_clock.gd, tests/test_voyage_clock.gd, tests/test_world_clock.gd on the user's PC; confirm the T1 decisions; visual test of the six day/night bands (I19).
B1: confirm the decisions (fair-loss model, pause-to-plan real time without acceleration, Hardcore keeps the ladder).
First run of the A6 + A7 GDScript on the user's PC (tools\run_godot_tests.bat, then the console commands in docs/A7_TOOLING.md section 6). Console command naming (short names like tp, give): keep or rename before J-modules build on them.
First run of the A6 GDScript test (test_island_map) and island_viewer on the user's PC. Whether T1 islands should be bigger or carry more content (budget 45 min vs about 11 min of pure walking). Template count (10 now, about 16 proposed).
First run of the A5 GDScript tests (test_schema/registry/tuning/save) on the user's PC.
First headless test-run output from the user's PC (`tests/run_all.gd`). Probe results postponed by the user. Access to a capable test machine for visual sign-off (borrow / used PC / cloud / RAM upgrade) - decide before the vertical slice.
