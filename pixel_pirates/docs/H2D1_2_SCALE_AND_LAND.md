# H2D-1.2: Anvil Cay Scale and Land Exploration Prototype (WRITTEN, NOT RUN IN GODOT)

## H2D-1.2.1 launch fix (2026-10-19): `Invalid argument for "build()" function: argument 1 should be "Node3D" but is "SubViewport"`
- **Cause (my error):** `CayWorld.build(vp: Node3D, ...)` in `cay_world.gd`, called from `sea_view_3d.gd` `_build_island()` as `_cay.build(_vp, ...)`. `_vp` is the view's `SubViewport`, created in `setup()` (`own_world_3d = true`); the ocean, camera, ship and weather nodes are added directly under it, so it is the root of the 3D world. A `SubViewport` is a `Node`, never a `Node3D`, so the declared type was wrong from the start. gdparse and gdlint cannot see argument types, so my static checks passed.
- **Fix:** the parameter is now `parent: Node`, because the only thing `build()` does with it is `parent.add_child(_root)` (the island's own `Node3D` named `AnvilCay`). No cast, no change at the call site, no change to the scene hierarchy (`SubViewport` > `AnvilCay` > terrain, pier, sprites, chunks) or to rendering.
- **Similar mismatches:** new scanner `tools/h2d/check_gd_types.py` (in `check_all.py`). It builds a table of every project class (`preload` aliases, typed members, typed parameters and return types) and checks argument types, argument counts, unknown methods and members on project classes (this covers the ~15 `LandWalker` / `CayWorld` calls in `h2d0.gd`), `:=` from a Variant (Dictionary subscript or `.get()`), and typed `var` / `return` mismatches. I proved it can see the bug by putting the old signature back (it reported `build(): argument 1 (parent) should be Node3D but is SubViewport`) and with 8 deliberate mistakes (all found), then removed them. On the real code: 0 findings across all 67 scripts. I also read every `:=` that could infer from a Variant in the H2D-1.2 files (none), and checked that every global shader uniform and every `set_shader_parameter` name exists in a shader or in `project.godot`.
- **Limits:** the scanner only knows simple expressions and a table of Godot node classes; it is not Godot's analyzer. Another error may still appear when you run. **Nothing has run in Godot**, and this fix is untested there.


**Read this first.**
- **Nothing in this module has run in Godot** (the sandbox cannot run the engine). What did run: the art bake (numpy/PIL), the static checks listed in section 8, gdparse, gdlint and `tools/check_all.py` (ALL PASSED, Godot step skipped). **You are the test.** Press F5 and follow section 7.
- Scope: Anvil Cay becomes a **3.9 km island** you can walk on, and the pirate can leave the ship. Kept from H2D-1 and confirmed by you: launch, sailing, docking at the pier, casting off, smooth performance. Not started: E2, the 100 islands, H2D-2, any new system (no combat, no survival, no NPCs).
- Honest limit: only a **560 m circle around the village (about 14 percent of the island)** is open on foot; the rest is baked and visible from the sea, but the pirate cannot enter it yet. The visual quality is still "prototype": you said it needs improving, and this module spent its effort on scale, streaming and walking, not on polish.

## H2D-1.2.2 invisible pirate (2026-10-19): root cause and fix

After H2D-1.2.1 the pirate was controllable but invisible away from the harbour. Cause: `custom_aabb` of the hero MultiMesh was fixed at the world origin while `set_hero()` moved only the instance, and Godot culls a MultiMesh by node transform x `custom_aabb` (it never adds the instance transforms). Fix: `set_hero()` moves the node (`cay_world.gd`). Guard: `tools/h2d/check_hero_cull.py` (cull model + source scan, in `check_all.py`). Not verified in Godot: see `docs/CP1_CAPITAL_PORT.md` section 1 for what to look at.

## 1. What changed
| Before (H2D-1) | Now (H2D-1.2) |
|---|---|
| 240 m patch, 864 px albedo texture | 4.4 km grid, 2 m cells, 2200 x 2200: a **height map** and a **biome map** and a 16 x 8 colour palette. No albedo texture: the ground is drawn per pixel from the biome class (palette step + dithered world noise + patterns) |
| 136 vegetation sprites placed by the bake | A **hashed scatter** per 200 m chunk (8 m cells, one candidate each, kept by biome class, forest density and height). Chunks stream in and out around the camera; the same chunk always grows the same trees |
| No walking | **F** goes ashore from the moored ship; a pirate sprite walks (4 directions, 4-frame cycle) on a camera that zooms to 4x (14.4 px per metre) |
| Island 9,100 m2, peak 32 m | **4.72 km2, 16.1 km of coast, peak 76 m**, 12 ground classes, two bays, hills, a lighthouse, a village, 3 footpaths, 56 structures, 75 stack and reef props, 29 collision blockers |

## 2. Scale, with the numbers
Scene units are metres; the sea view draws 3.6 pixels per metre on the 640 x 360 pixel grid.
| Thing | Value |
|---|---|
| Island | 3.90 km across, 4.72 km2, coast 16.1 km, peak 76 m (a "medium" island, 3-5 km) |
| Sloop | 22 m = 79 px |
| Pirate | 30 px tall with the hat = **2.08 m** at 14.4 px per metre (about 1.85 m without the hat). Sloop : body = 11.7 : 1 |
| Screen width | 178 m at sea; **44 m ashore** |
| Across the island | sailing 5 kn (scene speed 24.7 m/s): 2.6 min; **running 8.7 min; walking 16.2 min** |
| Walk from the pier (path length, from `check_land.py`) | plaza 23 m; Wreck Beach 592 m (2.5 min walking, 1.3 running); Pearl Cove 634 m (2.6 / 1.4); Lookout Hill 641 m (2.7 / 1.4) |
| Speeds (provisional) | walk 4.0 m/s, run (Shift) 7.5 m/s, 0.12 s to full speed |

Note: A6's island-walk placeholder `move.walk_speed_mps` is 1.4 m/s (a real walking pace). The prototype uses 4.0 m/s because an island this size at 1.4 m/s would take 46 minutes to cross. The two numbers disagree and **must be reconciled in E2/N7** (open question below). `land.walk_ms` is a separate key so nothing else changes.

## 3. The land view
- **Camera:** ashore the zoom eases (1.1 s) from 1 to 4. The sea view is unchanged. One pixel of the pirate is one pixel on screen.
- **Mismatch (documented limitation):** vegetation and structures are still drawn at the sea scale (3.6 px per metre), so at zoom 4 a palm has big chunky pixels next to the fine pirate. The ground is re-drawn at the zoom (14.4 px per metre) and is fine. Redrawing the vegetation and houses at 4x density is an art job for a later module.
- **Hero:** a one-instance MultiMesh quad from `anvil_hero_atlas.png` (24 x 32 cells, rows south, north, west, east; frames 1,2,3,2 are the walk cycle) plus a soft shadow blob. Light, night and lamps use the same global uniforms as the rest of the scene.
- **Ship:** stays moored and keeps its idle bob; the clock keeps running (15 real minutes per game day, T1).
- **Rain** looks sparse at zoom 4 (drops are the sea-scale size). Documented.

## 4. Keys ashore
| Key | Does |
|---|---|
| W A S D / arrows | Walk (screen-up is north; diagonal speed is not faster) |
| Shift | Run |
| **F** | Moored at the pier: go ashore. Ashore within 5 m of the ship: board |
| **T** | Test only: jump to the next of the four stops. The stop only counts as visited when you walk into it |
| Tab | Cycle the weather lab (W still does it at sea) |
| N, P, F1-F4 ... | As before |
Ashore, R, SPACE and 1-7 only say "board first". Pressing F2 (the 2D fallback) while ashore boards the ship first: the 2D path has no land.

## 5. The route (4 stops, a test aid, not content)
Plaza (16, -2) -> Pearl Cove (483, -357) -> Lookout Hill (119, -577) -> Wreck Beach (-443, -275). Stops open inside 12 m. The HUD names the next stop with distance and compass direction. When all four are visited it says to walk back to the pier. The walkable circle is centred (60, -270), radius 560 m; at the border the HUD says that the rest of the island is not open yet.

## 6. How it works (for the next person)
- `tools/h2d/cay_terrain.py` + `bake_cay.py` + `cay_sprites.py` write `anvil_cay_{height,biome,palette}.png`, three atlases and `anvil_cay.json` (v2). Height byte: below 0 m 26 levels down to -8 m; above 0 a square-root curve to 100 m. Same decode in `cay_terrain.dec_h`, `cay_scatter.gd` and `h2d_common.gdshaderinc`.
- `h2d/cay_world.gd` (RefCounted): builds the terrain patch (one camera-following 400 m heightfield, 200 x 200 quads, 80k triangles), the pier boxes, the MultiMeshes for structures and props, the chunk streaming and the queries `walkable`, `height_at`, `height_smooth`, `slope_at`, `in_blocker`, `class_at`.
- `h2d/cay_scatter.gd` + twin `tools/h2d/scatter_logic.py` (fixture `tests/fixtures/scatter_cases.json`).
- `h2d/land_walker.gd`: state, speed, facing, walk cycle, collision (tries the full step, then x only, then z only: the pirate slides along walls), the explore circle and the stops. Stub-testable: `tests/test_land.gd`.
- `walkable(x, z, r)`: on the pier = yes; otherwise smoothed ground height at least `land.min_h` (0.45 m), class is not CLIFF, slope at most `land.max_slope` (0.55), and no blocker or tree trunk within the body radius (0.45 m). The Python mirror is `check_land.py`.
- All numbers in `data/tuning/tuning_land.json` (12 `land.*` keys, provisional, owner E2). The T1 guard rejects keys containing "accel", so the ramp time is `land.speedup_s`.
- The bake changed two things after the first draft, found by the new geometry check: stack props are stamped at least 3.2 m wide (a 2 m cell grid blurred 2 m rocks away, leaving 18 sprites in the water) and the Pearl Cove / Wreck Beach props are walked inland to dry ground.

## 7. HOW TO TEST (about 10 minutes; Godot 4.7.2, open `pixel_pirates/game`, press F5)
1. The game starts at sea as in H2D-1. Sail to the harbor mouth (the buoys) and press **SPACE**: it docks as before. Report if this changed.
2. Press **F**. Expected: the camera zooms in over about a second, the pirate stands on the pier, the ship stays moored beside it, the HUD shows the route and the distance to the ship.
3. Walk with WASD, run with Shift. Expected: no sliding after you let go, 4 facing directions, a 4-frame walk, you stop at house walls and tree trunks and slide along them.
4. Walk off the pier to the plaza, along the dirt street north. Press **T** to jump to the next stop (Pearl Cove), and so on. Look at the beach, forest, hill, the lighthouse, the wreck.
5. Walk back to the pier within 5 m of the ship and press **F**: you board, the camera zooms out, SPACE casts off.
6. Try **N** (time of day) and **Tab** (weather) ashore, especially night near the lamps.
7. Report: red/yellow Output lines; fps at Dev-Lite (a) at sea, (b) ashore in the village, (c) ashore in the forest, (d) while walking fast into new ground (stutter when a chunk builds?); whether the pirate feels too fast or slow; whether the island feels big; what looks wrong. The HUD's chunk line says how many chunks and vegetation instances are alive.
Performance expectations (UNMEASURED): at most 9 vegetation chunks (about 300 instances each, one draw call per chunk), 1 terrain patch, 2 sprite MultiMeshes, the pier, 1 hero, 1 blob. Memory: the two 2200 x 2200 data maps are held on the GPU and once on the CPU for queries (about 40 MB CPU, 40 MB GPU). The first frame ashore builds 9 chunks at once (`prime`); a short hitch is possible.

## 8. What was checked, and how
| Step | Result |
|---|---|
| `bake_cay.py` | Deterministic bake, 46 s. 3.9 km, 4.72 km2, peak 76.1 m, 56 structures, 75 props, 29 blockers |
| `check_h2d_art.py` | Palette lock, atlas borders: ground palette 26 colours; vegetation 28; structures 29; hero 16 |
| `check_harbor.py` (rewritten for the new maps) | Berth, approach lane, pier, dock zone, props on land or water as intended, start position reaches the approach by water. It caught the drowned stacks and the surf props above |
| `scatter_logic.py --check` | Python twin of the scatter and its fixture (8 chunks, hashes) |
| `check_land.py` | On a 1 m grid mirroring `walkable` with 1,590 trunks and the blockers: 63.9 ha walkable of 98.5 ha; the pier reaches all four stops; paths 1.00-1.08 x the straight line; 6 separate walkable regions, 100 percent of the walkable ground connected to the pier |
| `check_scale.py` | Island 3-5 km, pirate 1.7-2.3 m, sloop : body 9-14, 14.4 px/m, crossing time over 5 min running |
| `check_shaders.py` | 10 of 10 shaders pass a **glslang syntax check** (lenient, not Godot's compiler) |
| `gdlint`, `gdparse`, `check_gd_warnings.py` | Clean (heuristic scan) |
| New Godot tests `test_land.gd`, `test_scatter.gd`, updated defaults checks | **Written, not run** |
| Python guards | `check_project.py` 0 problems (T1 time rules hold), ledger regenerated |

**Not run in Godot: everything.** The riskiest untested parts: loading the 2200 px data textures through `get_image()`, the terrain shader on ANGLE/HD 3000, the hero/vegetation sprite shader with the depth bias, the streaming hitch, and the camera zoom ease. The hand-written `.png.import` files are the H2D-1 approach (which you confirmed works).

## 9. Original idea: "the ground is a recipe, not a picture"
The island has no albedo picture. A 4.4 km painted texture at 14.4 px per metre would be 63,000 px wide. Instead the biome map stores only a class and a variation number, and the shader paints the ground per pixel in the palette ramp of that class at whatever zoom the camera has. The same 2 data maps give the sea view a 3.6 px per metre island and the land view a 14.4 px per metre island, and Tier-1 islands will cost two small maps each.

## 10. E2 proposal: scene metres versus world metres (decision needed before E2, NOT started)
The sea scene runs ten times faster than the sea it represents: 5 kn is 2.57 m/s, but the scene moves at 24.7 m/s, and the world clock runs 96 game seconds per real second, so the ratio is about 10 (a ship covers 14.9 km of world per real minute). Anvil Cay is 3.9 km across in the scene, which the clock reads as **39 km** of world. Three ways to deal with it:
| Option | What it means | Verdict |
|---|---|---|
| A. Scene x 10 = world | A scene island of 3-5 km is a 30-50 km world island. Anvil Cay itself (4.72 km2 in the scene) would be about 470 km2 in the world, about the size of Guam (544 km2). Walking stays at human scale ashore. Voyage times keep the clock rule. | **Recommended.** One rule, already true in the code, and "walking a 4 km island" sits next to "sailing 40 km past it" like a real medium island |
| B. Scene = world | Scale the sea scene back to real speed (2.57 m/s). | Rejected: the sloop would move at 9 px per second (a screen in 70 s) and a 14.9 km per minute ocean crossing would become 1.5 km per minute: unplayable without acceleration, which T1 forbids |
| C. Shrink islands | Make a medium island 400 m so scene x 10 = 4 km. | Rejected: nothing to explore on foot; this module shows 4 km is explorable and 400 m is a village |
With A, the E2 numbers apply to the world chart (9,000 x 6,000 km) while the scene sizes are one tenth. It also fixes the open **58 versus 100 islands** question only partly: that needs your decision at E2.

## 11. DONE / CANON UPDATE / NEXT
- **DONE:** the island at 3.9 km with 12 ground classes, chunked scatter, a walkable pirate with F/T/Tab, the explore circle with four stops, 12 tuning keys, 2 new GDScript tests, 4 new Python checks, the rewritten geometry check, this document and Canon v1.9.
- **CANON UPDATE:** v1.9 adds this module, the scale table, the `land.*` keys, the walk-speed disagreement (4.0 vs 1.4 m/s) and the scene x 10 proposal.
- **NEXT (three options, I recommend 1):** (1) **H2D-1.3**: fix whatever your test finds, then raise the visual quality of the island (vegetation and structures redrawn for zoom 4, light on the ground), still one island. (2) **E2 world proposal**: decide scene x 10, the 58 versus 100 islands, region placement; no island built yet. (3) **H2D-2**: the first living thing ashore (one NPC or one animal) to test the camera, scale and interactions. Nothing is started until you choose.
