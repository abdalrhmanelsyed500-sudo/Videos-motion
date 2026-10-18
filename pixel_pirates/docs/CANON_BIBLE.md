# CANON BIBLE - Crown of the Seas (working title) - v0.8 (after A2, A3, A4, A5, A6, A7, B1, B2)
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
SEED NUMBERS ARE PROVISIONAL PLACEHOLDERS (33 records, docs/PROVISIONAL_LEDGER.md), NOT Canon survival numbers. N-owner tags are proposed. B3 final only when no N* rows remain.
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
Debug console (autoload DebugConsole, debug builds, F1 or backtick): help echo clear data check tuning mode island tp time give inv seed save load quality log perf. Core in core/console_commands.gd (headless-tested), UI in ui/debug_console.gd. GameState (core/game_state.gd) mirrors the save_state schema until J1.
Island workbench: tools/island_kit/new_island.py (spec -> seed search with Silhouette Quota -> bake -> check -> preview -> record). ISLAND_REGISTRY.md generated by tools/data_tools/registry_doc.py.
Decisions: A7-1 console core separate from UI. A7-2 GameState mirrors save schema. A7-3 world rules twice + shared fixture. A7-4 never trust Godot exit code alone. A7-5 static Godot-mistake checks in check_project. A7-6 workbench enforces the quota at creation. A7-7 generated, freshness-checked registry doc. No in-engine map editor until F0 (data volume decides).
GDScript of A6 + A7 is unrun (no Godot in sandbox).

## Pillars (B1) - full text in docs/B1_PILLARS.md
One sentence: you are the captain of a ship full of people, crossing an ocean too big to cheat, and every crossing is a sum you must get right before the sea shows you what you got wrong.
P1 THE SEA IS THE GAME (bands in real minutes at default time scale: Hop 3-8, Passage 8-20, Crossing 20-45, Dead Ocean 45-90; play time sea 40 / islands 35 / ship+crew 17 / combat at most 8 percent). P2 EVERY VOYAGE IS A SUM (the Reckoning). P3 HARD BUT FAIR (Warning Ladder 7 / 3 / 1 days at current consumption; 3 warning steps before any loss; 2 recovery options at every critical state). P4 A SHIP IS PEOPLE. P5 EVERY ISLAND ANSWERS A QUESTION. P6 THE MAP PULLS YOU (no crossing of Passage length or more without a payoff).
Original idea: the Reckoning. The game never hides arithmetic, only the sea hides information. Forecast band +/-25 percent on ordinary sea, +/-40 percent on dead ocean, narrowest ever +/-10 percent; information (navigator, charts, lore) is cargo that narrows the band; stocks are shown as days left at current consumption and as margin against the HIGH end of the band.
Pillar Gate: six yes/no questions per feature (docs/templates/PILLAR_GATE.md). Anti-pillars: not a combat game, not a grind or base-builder, no reflex QTEs, no hidden timers, no pirate cliches (arr dialect, shoulder parrot, plank walking, literal X marks).
Tuning (game/data/tuning/tuning_design.json, 17 provisional keys): warn.* (7/3/1, min steps 3), recovery.min_options 2, plan.forecast_spread_sea/dead/min, voyage.* bands, share.*. Owners N13, B6, E8, E9, E2, B7. Machine-checked by tools/data_tools/design_checks.py (invariants + content-word lint over all data files).
Survival coverage table (11 systems with question, warning, recovery, island offer tag, proposed owner N1-N11) lives in the doc; N12-N14 not yet assigned.
Decisions: B1-1 fair-loss model (setbacks climb the ladder; ship/captain loss only after rungs 1-3; last-chance rescue by mode: Story always, Normal once per act, Hardcore none; B6 finalises). B1-2 real time at sea with pause-to-plan, x1/x4 acceleration that drops to x1 on every rung and event (B2 finalises controls). B1-3 Hardcore narrows widths and removes recommendations but keeps the ladder, honest numbers and recovery minimum.
Not decided here: game days per real minute (N13), exact lose conditions (B6), crew names and voices (D).

## Core loop (B2) - full text in docs/B2_CORE_LOOP.md
Wheel: PLAN the sum -> SAIL the days -> ANSWER the island -> PROVISION -> collect the CLUE -> PLAN. Average cycle 40 real min, 9.1 game days at sea. Modelled play-time split sea 39.3 / islands 35.4 / ship+crew 20.9 / combat 4.4 percent (targets 40 / 35 / 17 / max 8; ranges 30-50, 25-45, 10-25, 0-12).
Five loops: L1 Moment (max 4 min quiet), L2 Watch (24 s at sea), L3 Day (2.4 min, Morning Report), L4 Voyage (B1 bands), L5 Visit (6/16/45 min explore + 2 min provision).
Original idea: EIGHT BELLS. Ship's bells every half hour, eight bells ends a 4 h watch; six watches: Middle 00-04, Morning 04-08, Forenoon 08-12, Afternoon 12-16, Dog 16-20, First 20-24. The Morning Report at eight bells of the Morning watch (08:00) is a pause screen (20 s read) and the one place fast-forward always stops (with every ladder rung and crisis); it carries stocks as days left, ship, one crew line, a 24 h outlook band, one decision card, and writes the captain's Log line automatically.
Time (PROVISIONAL, owner N13): at sea 1 game day = 2.4 real min (1 game hour = 6 s, watch = 24 s); ashore 24 game min per real min (1 game day = 60 real min; full Tier 1 visit 45 min = 18 game h, Tier 2 16 min = 6.4 h, Tier 3 6 min = 2.4 h). A visit never costs more than one game day. Fast-forward x4, drops to x1 at every rung, crisis and report. 14 days = 33.6 min (a Crossing); 37.5 days = 90 min (longest Dead Ocean); 30 days = 72 min (water goes foul); 70 days = 168 min (scurvy).
Moments: ambient (free), choice (at least 2 per 10 min), crisis (at most 1 per 10 min).
Cycle mix (campaign, owner B8): Hop 25 / Passage 40 / Crossing 25 / Dead 10 percent, ending at Tier 3 / 2 / 1 / 1 islands. Visiting all 50 islands is about 33 h of play.
Flags handed to owners: Dead Ocean (37.5 days, 1125 L for 12 men, water foul after 30 days) forces rain catching, boiling or a spring (N4, N10); scurvy clock 168 min means fruit/herb islands every few cycles (N5, E3).
Code: core/voyage_clock.gd + tools/data_tools/voyage_clock.py (50-case hand-written fixture), tools/data_tools/loop_model.py, console command `time watch`. Tuning: tuning_loop.json (16 provisional keys). All machine-checked.
Decisions: B2-1 time scales (2.4 min/day at sea, 24 game min per real min ashore). B2-2 daily Morning Report pause screen. B2-3 consumption continues ashore, a full visit never costs more than one day.

## Island registry (50+ planned)
Generated: docs/ISLAND_REGISTRY.md. Currently empty. Format: ID (isl_NNN) | name | tier | biome | position | distances to neighbours | status (planned/designed/built/tested). Filled from E3.

## Open questions
B2: confirm B2-1 to B2-3 (two clocks, Morning Report, island cost rule). First run of core/voyage_clock.gd and tests/test_voyage_clock.gd on the user's PC.
B1: confirm the three decisions (fair-loss model, pause-to-plan real time, Hardcore keeps the ladder) or change them before B2 builds on them.
First run of the A6 + A7 GDScript on the user's PC (tools\run_godot_tests.bat, then the console commands in docs/A7_TOOLING.md section 6). Console command naming (short names like tp, give): keep or rename before J-modules build on them.
First run of the A6 GDScript test (test_island_map) and island_viewer on the user's PC. Whether T1 islands should be bigger or carry more content (budget 45 min vs about 11 min of pure walking). Template count (10 now, about 16 proposed).
First run of the A5 GDScript tests (test_schema/registry/tuning/save) on the user's PC.
First headless test-run output from the user's PC (`tests/run_all.gd`). Probe results postponed by the user. Access to a capable test machine for visual sign-off (borrow / used PC / cloud / RAM upgrade) - decide before the vertical slice.
