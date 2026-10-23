# FISHMONGER — Phase 0: Technical & Creative Audit of the Actual Project

Branch `arena/7464ca7a-videos-motion` · inspected commit `300012f` (VP-1A.4) · date 2026-10-23.
This audit inspects the **real files** (not old notes): 118 GDScript files, 9 scenes, 49 data JSONs, 20 schemas,
the test suite (42 wasm logic tests) and the browser render harness. Nothing was changed to produce it except the
additive FM-0 items in §9. Baseline preserved: local git tag `baseline-pixel-pirates` = `300012f`; every prior
milestone remains in branch history and on Drive. Source of truth = this repository; Drive holds deliverable mirrors only.

## 1. What the project actually is today

A Godot 4.7.2 **Compatibility-renderer** open-world sailing/fishing/life-sim skeleton with an authored HD-2D look
(3D geometry + authored pixel-art atlases + billboard pixel characters + elevated oblique fixed-north camera), a
schema-validated JSON data layer, a versioned save system with upgraders, a deterministic wildlife/ocean/market model
with Python twins and golden-file tests, a working manual-fishing loop (tension/reel state machine) wired to a real
fish hold and a real market, a walkable three-deck ship, a port town loop with NPCs/dialogue, a map screen with 10
regions, quality profiles down to a 360p Dev-Lite mode, and a CI-style suite + headless render harness.

That is much closer to Fishmonger's foundation than the pirate theme suggests. The brief's "data-driven species
system" (§11), "ecological distribution" (§12), "economy with legible prices" (§17), "wildlife encounters" (§14),
"pixel-art material pipeline" (§6) and "camera" (§5) all **already exist in reusable form**.

## 2. Reusable systems (keep, verified quality)

| System | Files | State / evidence | Fishmonger role |
|---|---|---|---|
| Data registry + mini-schema validator | `core/registry.gd`, `core/schema.gd`, `core/data_loader.gd`, `tools/data_tools/minischema.py` | suite `test_registry/test_schema`; Python twin parity | loads every Fishmonger table unchanged |
| Save/load with versioned envelope + upgraders + backup | `core/save_io.gd`, `data/schemas/save_state.schema.json` | `test_save` | identity migration via a new upgrader step |
| Market arithmetic (region factor, memory, spread; closed form) | `core/market.gd` + twin + golden cases | `test_market` | modern prices; currency symbol is data, not code |
| Species catalogue: **87 species**, 7 files, ecology fields (habitat, regions+abundance, temp, depth, group size, activity, season, diet, rarity, methods, lod, value) | `data/wildlife/species_*.json`, `data/schemas/species.schema.json` | registry-validated; `wildlife.py` twin | the brief §11 catalogue; extend with bait/gear/legal/quality (FM-0) |
| Wildlife sighting model (deterministic, LOD, weather-aware) | `core/wildlife.gd` + twin + golden cases | `test_*` via suite | §14 encounters as-is |
| Ocean field (depth/temp/salinity bands), sea state, climate bands, 10 regions | `core/ocean.gd`, `core/sea_state.gd`, `data/world/regions.json`, `climate_bands.json` | suite | §9 regional ecology as-is |
| Clocks: 1 game day = 15 real min, bands, seasons | `core/world_clock.gd`, `voyage_clock.gd`, tuning | suite | life-sim pacing as-is |
| Fishing: grounds disc rules + **manual tension/reel state machine** + first-person view + catch commit into the real hold | `h2d/fishing.gd`, `fish_manual.gd`, `fish_session.gd`, `fish_view.gd`, `fish_catch.gd`, `fish_storage.gd`, `fish_panel.gd` | suite `fish_flow`, `test_catch_paths`; VP renders | the rod/reel fight of §13 builds ON this state machine |
| Port loop: harbour state, sales, NPCs, barks, dialogue, HUD | `h2d/port_*.gd`, `harbor.gd`, `dialogue*.gd`, `data/port/*.json` | suite `test_port`, `deck_flow` | the harbour of §10/§18; restyle + modernise content |
| Ship control & motion: helm state machine, autopilot, wave-coupled heave/pitch/roll, spray | `h2d/helm.gd`, `ship_mode.gd`, `ship_motion.gd`, `wave_model.gd`, `ship_autopilot.gd` | suite `test_helm/test_sail`; H2D renders | boat handling; sail wind-response retires with the rig, motion model stays |
| Deck walking, interaction, ladders, hold ledger, stores | `h2d/ship_walker.gd`, `ship_deck_view.gd`, `ship_stores.gd`, `ship_layout.gd` | suite `deck_flow`, `walk_audit` | boat deck navigation as-is |
| Rendering: ocean shader w/ day cycle + lantern/sun shadows + AO (VP-1A.2), authored atlases (VP-1A.3/4), quality ladder, post | `h2d/sea_view_3d.gd`, `shaders/*`, `core/quality.gd`, `data/look/look_profiles.json` | 30+ rendered evidence shots; suite | the brief §6/§8 pipeline IS this; extend atlases |
| Pixel character billboards (≤16 headings), sprite manifest | `h2d/ship_sprite.gd`, `art/manifest/sprites.json` | renders | §7 characters; redraw costumes, keep rig |
| Map screen (10 regions, routes), island map model | `ui/map/*`, `core/island_map.gd` | suite `map_*` | §9 navigation UI as-is |
| Land walker + cay terrain scatter (Anvil Cay prototype) | `h2d/land_walker.gd`, `cay_world.gd`, `cay_scatter.gd`, `tools/island_kit` | suite `test_land/test_scatter` | §10 settlements grow from this |
| Test & render harness: 42 wasm logic tests, headless Chromium renders, checkers (gdlint, warnings, types, docs, port, project) | `game/tests/*`, `tools/godot_node`, `tools/godot_browser`, `tools/h2d/*`, `tools/check_all.py` | run every milestone | honest-validation backbone (§29) |
| Atlas generators (pixel-art authoring pipeline) | `tools/vp1/make_px_atlas.py`, `make_px_atlas2.py` | VP-1A.3/4 | §6 material families: add concrete/painted-metal/signage sheets |

## 3. Pirate-specific identity to replace (player-facing), with rollback kept

- **Theme strings/currency**: "Crown of the Seas" title (`game/project.godot`), "reales", pieces of eight/doubloons
  (`core/market.gd` constants, `port_hud.gd`, `port_state.gd`, `dialogue_ui.gd`, `h2d0.gd`), items `item_coin`,
  `item_doubloon`, `item_silver_bar`, `item_grog`, `item_hardtack`, `item_gunpowder`, `item_cannonball`
  (`data/items/items.json`), pirate dialogue/barks (`data/port/dialogue.json`, `barks.json`), recruits = pirate crew
  with shares (`data/port/recruits_port.json`).
- **The player vessel**: sailing sloop mesh/rig (masts, sails, rigging, crow's nest, cannon props) in
  `h2d/ship_mesh.gd`, `ship_props.gd`, `ship_deck_view.gd`; wind/sail response `h2d/sail_model.gd`; sail-specific helm
  feel (IN IRONS etc.) in `helm.gd`/`tuning_helm.json`. Replaced by a motorised fishing boat (FM-3); motion/wave
  coupling, walker, decks pattern reused; old ship code moves to `game/prototypes/legacy_sloop/` (not deleted).
- **Hero/NPC costumes**: pirate hat/coat sprites (`ship_sprite.gd` palettes, `art/manifest/sprites.json`).
- **Story artefacts**: lost-map/Crown finale content in dialogue/map text — retired from player-facing flow; files kept.
- **Tests referencing old strings** (`deck_flow.gd`, `fish_flow.gd`, `audit_r6.gd`, …) must be updated in the same
  increment as any string rename, or the suite goes red — planned per FM step.

## 4. Rendering pipeline & hardware constraints (unchanged facts)

Compatibility/GL3.3, RGBA8 LDR, no DOF/SSR/SDFGI/TAA/FXAA; shadows are authored single-ray marches, not shadow maps;
post = one cheap pass; profiles `ultra/standard/low_end/dev_lite` (dev_lite = 360p internal + mips). Atlases are
nearest+mip, periodic, 2 sheets of 16 tiles. **Intel HD 3000 remains UNMEASURED** — every milestone repeats this.
The brief's §28 strategy matches house canon: spend the budget on authored texels + one sun + cheap atmosphere.

## 5. Missing systems for the Fishmonger loop (build order in §7)

Fuel/engine consumption & tank UI; boat classes + upgrade tree (hull/engine/hold/refrigeration); rod-&-reel gear
stats (rod/reel/line/hook/bait objects) on top of the existing fight state machine; catch **quality/freshness decay
with ice** (spoilage rules exist only as design notes); orders/contracts board; NPC routines & reputation; modern
harbour architecture set (concrete, painted metal, signage, market stalls, fuel dock); modern boat mesh + helm
(throttle/steer instead of wind); audio (none exists yet — `sfx` bus hooks already emitted by fish_session);
species schema fields for bait/gear/legal/quality (added now, FM-0); contemporary UI skin.

## 6. High-risk compatibility issues

1. **Save games**: identity rename touches saved fields (currency count name, item ids). Mitigation: `save_io`
   upgrader chain (SAVE_VERSION 1→2) mapping old ids→new; backup file already guarantees recovery.
2. **Registry strictness**: every data file validates at boot; schema edits must stay additive (optional props) or
   all 87 species records fail. FM-0 adds only optional props; verified by suite `test_registry`.
3. **Suite string coupling**: HUD assertions contain "reales"/pirate terms; renames must land with test updates in
   one commit (FM-1 rule).
4. **Render harness hooks** (Q/U/I/O/J/K/L/H/V, Backslash, F9–F11) are used by scenarios; boat replacement must keep
   or remap hooks deliberately (FM-3).
5. **HD 3000**: unknown until the user runs it; keep dev_lite + benchmark scene (`h2d/bench.gd`) as the measuring stick.

## 7. Migration sequence (increments, each ends suite-green + rendered evidence + report)

- **FM-0 (this turn)**: audit; baseline tag; additive species-schema fields (baits, gear, fight, legal_min_cm,
  protected, market_tags, freshness_h); `data/fm/fm_identity.json` (title, currency, era, units, home port, term map).
- **FM-1 identity pass (data+strings)**: currency/items/kits/market/port dialogue/title modernised; test strings
  updated same commit; before/after port shots.
- **FM-2 characters & UI skin**: modern fisher costumes for hero + port NPCs; UI kit colours/icons; keep rig/manifest.
- **FM-3 the boat**: modern motorised hull mesh + atlas tiles (painted hull, metal, rubber), throttle/steer helm +
  fuel; legacy sloop to `prototypes/legacy_sloop/`; motion model retuned; sea trials rendered.
- **FM-4 the harbour**: concrete/painted-metal/signage atlas sheet; market stalls, fuel dock, workshop, crates &
  buoys; port loop restyled; NPC routines v1.
- **FM-5 fishing depth**: rod/reel gear objects + bait table wired into `fish_manual`; species gear/bait fields used;
  quality/freshness + ice; orders board v1.
- **FM-6 economy & progression**: boat upgrade tree, expenses, regional demand legibility UI, reputation v1.
- **FM-7 ocean life presentation**: encounter visuals (schools, birds, dolphins, whales) from `wildlife.gd` LODs;
  rival fishers v1.

## 8. Decisions needed from you (before FM-1/FM-3)

1. Currency name/symbol (proposal: **"$" dollars**, fictional coastal state) or keep a local name?
2. Home harbour name (proposal: **Port Marlin**, temperate home region `reg_kettle_seas`) and boat name (proposal:
   **"Gullwing"**, 7 m coastal gillnetter)?
3. Crew: solo-only at start with optional hired deckhands later (recommended), or keep a crew roster from day one?
4. Legacy pirate build: keep playable as a hidden "archive" scene after FM-3 (recommended, zero cost) or fully retire?

## 9. FM-0 changes (additive, this turn)

- `data/schemas/species.schema.json`: + optional props `baits`, `gear`, `fight`, `legal_min_cm`, `protected`,
  `market_tags`, `freshness_h` (brief §11/§13/§17 conventions; existing 87 records stay valid).
- `data/fm/fm_identity.json` + `data/schemas/fm_identity.schema.json`: one record `fm_core` (title, tagline,
  currency, era, units, home port, boat class start, term map pirate→modern).
- `docs/FISHMONGER_PHASE0_AUDIT.md` (this file). Local tag `baseline-pixel-pirates`.
- Validated: registry load + 42/42 suite (see report), gdlint clean, checkers pass.

## 10. Validation performed for Phase 0

Inspection commands on the real tree (find/grep/sed/python over data); schema/record counts read from files
(87 species, 10 regions, 25 items); suite executed after FM-0 (42/42); no runtime claim beyond that; HD 3000
unmeasured; user-PC steps ship with FM-1.
