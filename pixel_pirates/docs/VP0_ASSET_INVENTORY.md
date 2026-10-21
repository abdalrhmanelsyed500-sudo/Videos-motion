# VP-0 Prioritised Asset Inventory
Legend — **P0** needed for the vertical slice (ship + ocean + Anvil Cay section); **P1** needed for the whole capital/first region; **P2** later regions; **P3** polish. State: ✅ prototype exists (baked, in `game/art/vp0`), 🟡 prototype exists but weak (needs redo or hand pass), ⬜ not started. "Hand" = needs a hand-painted pass on top of the bake. All VP-0 assets are real files (PNG sprites, tiles, maps), not screenshots. Counts of production sprites are estimates.

## 1. What VP-0 actually produced
| Group | Files (`game/art/vp0/…`) | Made how | Notes |
|---|---|---|---|
| ship (props) | `ship/` 15 models, 78 frames; pirate, barrel, barrel_fish, crate, cannon, rope_coil, winch, helm, lantern, hatch, fishing_net, chest, bollard, mast (72×287), cabin (118×155, 8 facings) | Python voxel baker (`tools/vp0/voxel.py`, `models_ship.py`): voxel shapes, tone textures, cel bands + outline, 8 facing renders, shear projection K = 0.75 | max 24 colours per frame |
| island | `island/` 15: palm_a/b/c, rock_a/b/c, bush_a/b, house_a (156×185), house_b (130×235), warehouse (206×154), pier_4, pier_y_6, lamp_post, signpost | same baker, `models_island.py` | house_a is 36 colours |
| sea hull | `hull/sloop_sea_h00…15` (52×240 each, 8 px/m) | baker on the same sloop model, downscale 3 | 35 colours; sails show streaks |
| LOD | `lod8/` 5 sprites: palm_a, palm_c, rock_a, rock_c, bush_a | `downscale(3)` of island models | ≤ 12 colours |
| ground | `ground/` ground_atlas (384×192), deck_planks, hull_strakes, sail_canvas, noise_128 | `ground.py`, numpy | 8 terrain rows × 4 variants |
| world maps | `world/cay_*`, `world/sea_*` (+ json) | `bake_world.py` from the r7 map + a hand-authored test sea | cay cells 60×34, sea cells 160×90 |
| shaders | `game/prototypes/vp0/shaders/` cel, grade, halo, ocean, shadow, sprite, terrain (393 lines) | hand-written | |
| scenes/scripts | `game/prototypes/vp0/` deck, cay, sea (+ stage, ship builder, util) | GDScript | ≈ 3 270 lines of prototype code including the shaders and Python |
Total art on disk: **124 PNGs, 912 KB**.
**Temporary geometry that remains:** the deck planking, hull shell, sails, rails and the terrace in the prototypes are generated *meshes* (planks/strakes are real textures on them). They are intentionally the production approach for large surfaces; the *hand-made hero detail* (sail patching, rail carving, hull ornament) is not done. The old procedural box deck of the game (`ship_deck_view.gd`) is **unchanged** and still the one the game uses.

## 2. Ship — priority P0
| Asset | State | Count (prod.) | Needs |
|---|---|---|---|
| Sloop hull T24 (mesh + strakes texture) | ✅ | 1 (+ 2 more hulls P2: brigantine, galleon) | hand pass: wale, ornament, damage decals |
| Deck planks, hatch coamings, rails | ✅ | 1 set | decals (stains, repairs) |
| Mast, boom, crow's nest | ✅ | 1 per hull | animated flag/ensign (P1) |
| Sails (main, jib), rigging | 🟡 | 5 trims × 3 hulls | sail-specific bake; fix streaks; furling frames |
| Cabin | ✅ | 1 per hull; plus roof-off frames | roof-off set (P0 for exploration), interior props (bunk, table, chart: P1) |
| Helm, winch, hatch | ✅ | 3 × 8 facings | animated wheel/crank (P1) |
| Barrels, crates, rope coil, lantern | ✅ | ~12 | variants (P1) |
| Cannons | ✅ prototype | 2 (+ 6 later) | collision + firing frames (P3) |
| Fishing net, pulley, fish barrels | 🟡 net redo | 4 | redo net; pulleys (P1) |
| Sleeping deck (hammocks, chests, lamps) | ⬜ | ~15 | P0 for the slice's deck 1 |
| Hold (stacked cargo, rats, water casks) | ⬜ | ~20 | P1 |
| Crow's-nest view | ⬜ | ~5 | P1 |
| Sea ship, 16 headings × 5 sail trims at 8 px/m | ✅ headings, ⬜ trims | 80 per hull | re-bake from the hero model |

## 3. Ocean — priority P0
| Asset | State | Needs |
|---|---|---|
| Ocean shader (bands, waves, glints, foam, swash, wake) | ✅ | tune close-up wake; weather states (storm, calm) P1 |
| Depth/shore maps | ✅ for the cay and the test sea | generator for all islands from the global map (P1) |
| Night/dusk variants | ✅ (look params) | moon glints (P1) |
| Open-sea set dressing (birds, drifting weed, flotsam, whales, fish shoals, wakes) | ⬜ | 30–40 sprites, P1; open sea is never empty |
| Weather (rain, fog banks, storm swell, clouds & shadows) | ⬜ here; exist in H2D-0.3 on the old camera | re-base on the new camera, P1 |

## 4. Island & Anvil Cay — priority P0 (slice), P1 (whole city)
| Asset | State | Count (prod.) | Needs |
|---|---|---|---|
| Ground atlas | ✅ | 8 rows now, ~24 rows for biomes (P2) | per-biome atlases |
| Palms, bushes, rocks | ✅ | ~40 across biomes | variety, hand pass |
| Houses (2 types) | ✅ | 12 types for the city (P1) | roofs hand-painted |
| Warehouse | 🟡 | 3 | roof detail |
| Pier, bollard, lamp, signpost | ✅ | 20 harbour props | |
| Terraced cliff, stairs, walls | 🟡 flat slab | ~15 | |
| Fort, lighthouse, market stalls, ship-yard | ⬜ | ~25 (P1) | |
| Dock cranes, boats on cradles | ⬜ | ~10 (P1) | |

## 5. Capital Port City — P1
Full city from the r7 map: rough estimate 40+ distinct buildings (3 sizes, 4 materials), ~60 street props, 8 ground rows, a harbour set — about 350–450 sprites. Not yet planned in detail; artist time per building is unknown until the first hand pass is done.

## 6. Characters — P0 pass (mannequin exists), P1 production
| Asset | State | Count | Needs |
|---|---|---|---|
| Mannequin (scale check) | ✅ | 1 × 8 facings | not final art |
| Player captain | ⬜ | 48×64, 38 frames × 4 dirs | art-direction sheet first (expressive face/hands, reference 4) |
| Crew (6–8, all male) | ⬜ | same | recoloured bodies + unique heads/props |
| NPCs (merchant, dockhand, guard, etc.) | ⬜ | ~12 | |
| Portraits | exist (older style) | | re-check against the new style |
Note: characters stay hand-painted; the baker is not the right tool for faces and cloth.

## 7. Hero-detail pass flags (the "Known weaknesses" list)
sail canvas streaks · warehouse roof · terrace slab · fishing net · wake cross-pattern · mannequin · missing cabin roof-off frames · no animated props.
