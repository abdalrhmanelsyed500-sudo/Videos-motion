# IRON ATLAS: SHATTERED WORLD — Stage 2 status

Verified 2026-10-28 on branch `arena/7464ca7a-videos-motion`. The starting
working tree was clean at `7ff6e08`; the original Stage 1 suite reproduced
**4/4 passes, 119 checks** before edits. The discrepancies found in the earlier
report and code are recorded in [`STAGE2_AUDIT.md`](STAGE2_AUDIT.md).

## Implemented and tested

- **Regional world:** seeded 24-district classic or 200-district default; the
  generator accepts 25–400. Stable IDs, coherent bidirectional land links,
  separate sea links, terrain-linked resources, population, cities,
  infrastructure, stockpiles and strategic values. Full ID/symmetry/land
  connectivity validation: `game/world/world_generator.gd`. The 200-district
  graph is tested for five specified seeds and another ten benchmark seeds;
  configurations of 25, 50 and 400 districts are also validated.
- **Insurgency and command:** the scenario starts with 60 personnel in abstract
  12-person squads. Recruitment consumes faction funds and manpower, creates
  paid reserves, and equipment assignment either equips reserves or replaces
  existing gear. Land orders, friendly retreats, readiness, morale and
  contested/uncontested control use authoritative state. Files:
  `game/economy/economy_system.gd`, `game/military/command_system.gd`.
- **Combat and recovery:** tactical and abstract outcomes persist casualties,
  wounded, deaths, equipment condition, ammo use, battlefield salvage, retreats
  and reports; medical stock speeds recovery and damaged packages require parts
  and money to repair. Battle finalization is idempotent across saves. The
  tactical retreat button now produces a withdrawal, not victory. Files:
  `game/military/combat_system.gd`, `game/scenes/tactical_map.gd`.
- **Territorial administration:** capture resets stability/recovery and raises
  opposition and pressure; security, infrastructure and economy investments
  cost money and change persistent state. Occupation/focus costs recur. Local
  support, legitimacy, stability, productivity and infrastructure affect real
  revenue and political thresholds. `game/administration/administration_system.gd`,
  `game/data/regional_rules.json`.
- **Campaign outcomes:** losing all controlled territory and equipped squads
  is defeat. Holding the Vardena capital plus 60% of its claimed districts,
  with sufficient support, stability and legitimacy, yields a military
  transition. A 30%-share, supported/stable/legitimate territory and a live
  government ceasefire allow a negotiated transition. The complete negotiated
  path was exercised on the 24-district scenario using real system actions in
  `game/tests/test_stage2_campaign.gd`.
- **Market and logistics:** catalog-driven prices, inflation/supplier effects,
  restrictions, stable quotes, affordability checks, one-time payment,
  deliveries delayed by a lost or contested capital, one-time inventory/relationship
  changes, maintenance and real assignment/repair. Regional food, ammo, fuel
  and spare parts are consumed; hostile/interrupted routes and low supplies
  affect readiness, movement and combat. Player warnings precede severe
  shortages. Files: `game/economy/market_system.gd`, `game/logistics/supply_system.gd`,
  `game/data/equipment.json`.
- **Competing factions:** persistent faction budgets, manpower and inventories;
  AI uses the same recruit, purchase, assignment, supply, wage, admin and
  command paths as the player. It scores local threats and high-value regions,
  attacks or reinforces, reacts to lost claims and may declare war or seek a
  ceasefire. AI decisions and negotiating strength estimates use local/border
  observations, not distant hidden unit counts. `game/ai/faction_ai.gd`,
  `game/diplomacy/diplomacy_system.gd`.
- **Interface and pixel art:** data-driven, zoomable/pannable map with
  viewport draw culling; controller, regional values, supply, military,
  procurement, diplomacy, reports and visible feedback. Enemy markers and
  remote detailed district data are hidden outside basic observation; private
  faction reports are filtered. The tactical scene draws the committed 24px
  unit and 32px terrain sprites. `game/scenes/`, `game/core/pixel_art.gd`,
  `game/core/ui_style.gd`; generated assets use deterministic seeds in
  `tools/make_sprites.py`.
- **Persistence:** schema v2, stable RNG stream state, exact Variant copy in a
  JSON envelope, v1 migration with documented RNG limitation, active orders
  and deliveries preserved. `game/persistence/save_system.gd`,
  `game/core/campaign_state.gd`.

## Automated results

`bash iron_atlas/tools/run_suite.sh /tmp/iron_atlas_suite.log`:

| Suite | Result |
|---|---:|
| Stage 1 logic | PASS, 60 checks |
| Stage 1 UI flow | PASS, 12 checks |
| Stage 1 tactical | PASS, 5 checks |
| Stage 1 selfplay | PASS, 99 checks |
| Stage 2 logic/world/systems | PASS, 136 checks |
| Stage 2 UI | PASS, 18 checks |
| Stage 2 tactical consequences | PASS, 15 checks |
| Stage 2 playable campaign path | PASS, 14 checks |
| Stage 2 long campaign/save replay | PASS, 14 checks |
| **Total** | **9 suites, 373 checks; 0 failed** |

The long test advances a 200-district campaign for 365 simulated days and
compares 120 days after a save with the uninterrupted state, exactly. It uses
the manual test clock; player contacts may remain paused for a decision, so
it is not a claim of 365 days of human playtesting. The original tests remain
present; tautological assertions were strengthened rather than removed.

## Performance and visual verification

In the available Node/Godot 4.7.2 WASM **headless** environment, 10 validated
200-region generations averaged **13.19 ms**. A 200-day simulation averaged
**7.98 ms/day** (p95 **27.29 ms/day**); 29 formations existed at the end. Peak
RSS for the *entire* Node + WASM process was **245,048 KiB ≈ 239.3 MiB**.
See [`STAGE2_PERFORMANCE.md`](STAGE2_PERFORMANCE.md) and
[`stage2_benchmark.json`](stage2_benchmark.json) for methodology and all
numbers. GPU frame time, native desktop performance, incremental world memory
and FPS were **not measured**.

Actual software-WebGL UI screenshots are in [`stage2_shots/`](stage2_shots/).
The menu, setup, 200-region map, formation selection and a paid market order
were exercised with real mouse input. The tactical screenshot uses an explicit
contact-placement fixture; it is visual evidence, not proof of a played battle.
The reference images and committed sprites were inspected. The resulting art
is consistent and pixel-based, but still materially simpler than the supplied
professional references and needs further hand-authored polish.

## Simplified / incomplete

- The 200-district world is a jittered rectangular land graph, not an authored
  geographic map. Its strategic pacing and complete 200-district victory path
  have not been human-playtested or balanced to completion; the verified
  end-to-end transition uses the 24-district option.
- Sea links are labelled separately but naval movement, sea trade and maritime
  supply are **not implemented**. No six-continent/international endgame,
  full research/industry tree, event director or advanced diplomacy is claimed.
- Tactical battles are simplified 30×20 skirmishes against one opponent;
  enemy tactics, pathfinding, equipment representation and visuals are basic.
  Tactical simulation logic remains partly in the scene script. Simultaneous
  multi-faction battles and mid-battle saving are not implemented.
- AI is a local heuristic, not a comprehensive strategic planner. Observation
  hides distant formations and some region details, but this is not a full
  espionage, misinformation or intelligence-network system. Public borders,
  war and territorial events remain visible.
- There is no autosave; the UI exposes one manual save slot. Loading a Stage 1
  save restarts its RNG stream because the old save did not contain the stream
  position. If the current primary JSON is corrupt, recovery from its `.bak`
  currently requires selecting/restoring that backup manually.
- Native desktop startup, real-GPU frame time, modest-hardware performance and
  long-term player-facing balance are unverified in this environment.
