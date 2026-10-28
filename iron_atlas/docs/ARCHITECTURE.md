# IRON ATLAS — Architecture (adapted to this repository)

## Layout
```
iron_atlas/
  docs/                    this folder (audit, architecture, roadmap, status)
  tools/
    run_suite.sh           headless suite (reuses pixel_pirates wasm harness)
    make_sprites.py        deterministic pixel-art generator (Pillow)
  game/                    Godot 4.7 project root (res://)
    project.godot
    core/                  autoloads + campaign state container
    world/ world_generator.gd
    military/              command_system.gd combat_system.gd
    economy/               economy_system.gd market_system.gd
    logistics/             supply_system.gd
    diplomacy/             diplomacy_system.gd
    ai/                    faction_ai.gd
    persistence/           save_system.gd
    scenes/                boot, menus, world_map, tactical_map (UI built in code)
    data/                  equipment.json scenario_vardena.json
    tests/                 headless SceneTree tests
    assets/sprites/        generated png (units, terrain)
```

## Shared state rules
- **CampaignState** (`core/campaign_state.gd`, RefCounted) owns ALL authoritative campaign
  data as plain typed Dictionaries/Arrays with stable string ids (`reg_07`, `cty_vardena`,
  `frm_0003`, `ord_0012`). It serializes to one JSON blob (schema version 1).
- Autoloads (exactly four): `EventBus` (signals only), `GameState` (holds the live
  CampaignState + system instances), `CampaignClock` (speeds/ticks), `SaveManager`
  (thin wrapper over `SaveSystem` class so tests can use the class without autoloads).
- Systems are RefCounted classes constructed by GameState with an explicit `state`
  reference: Economy, Market, Command, Combat, Supply, Diplomacy, FactionAI.
  They never touch nodes/rendering → testable headless and reusable in multiplayer later.
- Rendering reads state, never owns it: world_map/tactical_map draw from CampaignState and
  push player intent through CommandSystem/MarketSystem methods (validated commands).

## Simulation cadence (configurable)
- CampaignClock speeds: paused/1/2/4/8 days per second; emits `day_passed`,
  `week_passed`, `month_passed`.
- daily: movement, supply consumption, market ETAs, engagements, wages/upkeep.
- weekly: regional tax income, AI decisions, diplomacy drift.
- monthly: stability/legitimacy drift, reports rollup, attrition recovery.

## Determinism
- One `seed:int` per campaign; all generation and procedural choices use a seeded
  RandomNumberGenerator stored in CampaignState (`rng_state` persisted) so save/load
  continues the same stream. AI uses the same stream discipline.

## Interfaces kept expandable (simplified now, real hooks)
- Diplomacy: 3 dimensions (trust/warmth/threat) now; schema allows more keys later.
- Combat: single abstract resolution function with documented factor list; tactical map
  feeds the same function per skirmish tick.
- Market: catalogue JSON with full field set from the brief (tier, upkeep, crew, training,
  fuel, ammo, parts, reliability, availability, export restriction, supplier, sensitivity).
- Occupation/politics/research/intelligence: PLANNED (STATUS.md), interfaces reserved in
  region records (support, legitimacy, stability, stocks).
