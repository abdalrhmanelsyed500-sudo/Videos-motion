# H2D-1: First Island and Harbor Prototype - Anvil Cay (WRITTEN, NOT RUN IN GODOT)

**Read this first.**
- Nothing here has run in Godot; the sandbox cannot run it. What did run: the art bake (numpy/PIL), a geometry check on the baked files, the Python twin of the docking logic, the GLSL syntax pass over 8 shaders (lenient, not Godot), gdparse, gdlint and `tools/check_all.py`. **You are the test.** Press F5 and follow section 7.
- Scope: ONE island, Anvil Cay, with a small harbor and a docking interaction. The 100 islands are not started. H2D-2 and E2 are not started. The HD-2D look, the oblique north-up camera, the layered pixel-art ship, the ocean and the weather are kept; every H2D-0.3 key still works.
- Anvil Cay is a prototype island. It is not in the island registry (`docs/ISLAND_REGISTRY.md` stays at 0 islands).

## 1. What is on the island
Anvil Cay is a 240 m square patch (864 x 864 px at 3.6 px per metre); land is about 9,100 m2 and the highest point 32 m. Local coordinates below are metres from the island centre: x east, z south. The island sits at the scene origin.

| Part | Where and what |
|---|---|
| Coastline | An irregular, noise-warped outline (five overlapping ellipses plus noise), so it reads as a coast and not a blob. A deep cove opens to the south (the harbor). Shelf water deepens from the shore, shoals and a few reef rocks lie off the coast. |
| Beach | A sand band 7 to 13 m wide (wider at the cove), in four sand tones with wet sand at the waterline, a weed line, wind ripples, driftwood and a few pebbles. |
| Rocks | Two rock stacks guard the cove mouth (breakwaters at about (-3, 46) and (37, 44)); more reef stacks around the island; boulders and cliffs on the hill. The hill (the Anvil, 26 to 32 m) is in the west; a low knoll in the east. |
| Vegetation | 136 sprites: 3 palm shapes (one tall and leaning), 2 jungle trees, bush, flower bush, fern, grass tuft, rocks, boulder, reef rock, driftwood. Jungle on the slopes, palms behind the beach, none on the street, plaza, pier or berth lane. |
| Pier | Wooden deck, 3 m wide, z 2 to 36, 1 m above the water, planks with beams; a T-head on the west side at the end (z 32 to 36). 8 piles, 3 bollards. |
| Harbor | Flat ground at 1.95 m north of the cove: a cobbled plaza, a dirt street at x = 16 and, around them, the **harbourmaster's hut** (flag, chimney), a **warehouse** (hoist beam), the **tavern** (anchor sign, red awning), the **fisher hut** with a net rack, crates, barrels, a cannon, a signal mast with flags, a rowboat on the beach. |
| Lights | 6 lamp posts (pier head, pier, plaza west and east, tavern, street) and lit windows. |
| Buoys | 2 red, 2 cream: they bob with the swell and mark the harbor mouth. The dock zone is the water between them. |

Berth: the ship's centre goes to (21.4, 21), bow to the north, **port side to the pier** (hull edge 0.8 m from the pier edge). Approach point (21.4, 56). Dock zone x 2 to 44, z 42 to 100 (99 percent water). Landing (16, 4), where the pier meets the beach.

## 2. Docking (keys)
| Key | Does |
|---|---|
| **SPACE**, inside the dock zone | Docks. The crew takes the ship along a smooth curve: your position, bending through the approach point, then straight north along the pier into the berth. 6 to 16 s (about 16 s from the far corner of the zone, about 8 s from the mouth). The sails go slack on the last third and the wake fades. |
| **SPACE**, moored | Casts off: backs out stern-first to the approach point (10 s), swings the bow to the south (3 s), then hands you the helm at heading 180 (facing the sea). |
| SPACE, outside the zone | Says you are too far from the berth. |
| **N** | Test only: cycles the time of day: dawn 06:30, noon 12:00, sunset 18:00, night 22:30. The real clock keeps running (1 game day = 15 real minutes). |

While the ship docks, is moored or casts off, A/D do nothing (the crew has her). Everything else works: weather lab, camera, exposure, pause.

**Harbor speed.** The scene runs about five times faster than the real knots (5 kn = 24.7 m/s on screen), so a harbor could not be entered at that pace. Near the berth the whole scene speed is multiplied by 0.30 at 40 m or less, rising smoothly to 1.0 at 110 m (x0.44 at 60 m, x0.72 at 80 m). The HUD shows the factor.

**Landing and grounding.** The ship runs aground where land is higher than 0.3 m under ANY of 7 hull probes (bow, stern, centre, four on the sides at +-2.4 m), not just under the centre as before. The pier counts as land. The grounded banner and the R key (reset) work as before. The pier is in the data as land at 1.0 m, so you cannot sail through it; docking itself is assisted and never touches it.

**HUD.** Within 260 m of the berth: distance, bearing and "outside / IN THE DOCK ZONE" on the HUD; a large prompt at the bottom of the screen ("press SPACE to dock", "Moored at Anvil Harbor. Press SPACE to cast off."). The start position is now (-100, 140), heading 58, about 120 m from the dock zone and pointing at it.

## 3. How the ship, water and island share one picture
- **One light.** The island ground is lit per pixel from the baked height data by the same sun, ambient, fog, cloud shadows and overcast as the water and the ship. Hills, trees and houses shadow the ground (ray march over the height + canopy + building channel).
- **Shadows on the water.** The island, the pier, the houses and the trees shade the water beside them: three taps along the sun direction in the ocean shader, only within 14 m of the shore. A sunset sun gives long shadows over the cove.
- **Depth.** Water is tinted by the real depth under it (shallow lagoon colour near shore and on the shoals, deep colour beyond), with foam where the sea laps the shore, the pier and the reef stacks.
- **Atmosphere.** The island sprites use the same distance fog; the same rain darkening and cloud shadows; in an overcast sky the light goes flat everywhere at once. No screen overlay (the H2D-0.3 rule stands).
- **Night.** New global `h2d_night` (0 by day, rising 17:00 to 19:30, falling 04:30 to 06:30, a little in a storm). 6 lamp positions are passed to the ocean, the ground and the sprite shaders; each lays a warm pool with its own flicker on the planks, the plaza and the water. Pixels painted in the two flame colours (fire 3 and fire 4 of the palette: lit windows, lantern glass) are emissive: dim by day (x0.32) and bright at night (x1.25), and the existing bloom picks them up.
- **Moored ship.** Sails hang slack (the sail model is fed no wind), no wake, but the hull keeps rolling and heaving on the swell next to the pier.
- **Berth marking.** A faint dashed outline of the berth is painted on the water, fading in within 110 to 170 m and out once you are moored.

## 4. Performance (low-end), and what is NOT measured
- Compatibility renderer, no shadow maps, no new passes. Draw calls added: the island mesh was already there; the vegetation MultiMesh already existed; **one** more MultiMesh for the structures. The two atlases are 192x224 and 320x288 px.
- **Risk 1: the island mesh is now 240 x 240 quads (about 115,000 triangles, one height fetch per vertex)** so a 3 m pier deck is 3 quads wide. H2D-0 used 96 x 96. That is the first thing to look at if the dev PC is slow (see 7: how to tell).
- Risk 2: the ocean fragment shader gained up to 3 texture taps near the shore and a lamp sum at night (6 lamps, skipped by day). Risk 3: the ground shader's lamp sum at night.
- No fps figure exists for any of this. The target is unchanged: Dev-Lite at least 30 fps.

## 5. Files
**New:** `tools/h2d/bake_harbor.py` (bakes everything below), `tools/h2d/check_harbor.py`, `tools/h2d/harbor_logic.py` (twin, tuning table, fixture), `tools/h2d/import_template.txt`, `game/h2d/harbor.gd`, `game/tests/test_harbor.gd`, `game/tests/fixtures/harbor_cases.json`, `game/data/tuning/tuning_harbor.json` (14 keys, `harbor.*`, all provisional), `game/h2d/art/anvil_cay_albedo.png`, `anvil_cay_data.png`, `anvil_cay_normal.png`, `anvil_veg_atlas.png`, `anvil_struct_atlas.png`, `anvil_cay.json` (+ `.import` files), `art_bible/h2d1/` (numpy previews: NOT Godot renders).
**Changed:** `game/h2d/h2d0.gd`, `sea_view_3d.gd`, `shaders/island.gdshader`, `ocean.gdshader`, `trees.gdshader`, `h2d_common.gdshaderinc`, `game/project.godot` (global `h2d_night`), `tools/check_all.py`, `tools/h2d/check_h2d_art.py` (now checks the new files), `docs/CANON_BIBLE.md` (v1.8), `docs/PROVISIONAL_LEDGER.md`.
**Unused, kept:** the H2D-0 island files (`island_anvil_*`, `trees_atlas.png`, `bake_island.py`; the new bake imports its sprite helpers).

Art limits (checked by `tools/h2d/check_h2d_art.py`): ground 20 colours (limit 52), vegetation atlas 28 and structure atlas 26 (limit 32 each), every colour from `palette.json`, no sprite touches its cell border. Rebuild: `python tools/h2d/bake_harbor.py --preview` (deterministic), then `python tools/h2d/check_harbor.py`.

## 6. The geometry check (`tools/h2d/check_harbor.py`, runs in `check_all.py`)
Berth footprint and approach lane are open water; water under the berth about 7 m deep; the pier deck is solid at 1 m and joins the beach; the hull-to-pier gap is 0.8 m; the dock zone is 99 percent water and holds the approach point; every vegetation sprite stands on land, nothing stands on the pier or in the lane, structures and lamps stand on solid ground, buoys in water; and a breadth-first search shows the start position reaches the approach point through open water with a 6 m safety disc. It reads the baked files only: it proves the map, not the game.

## 7. How to test (about 10 minutes)
1. Open `pixel_pirates/game` in Godot 4.7.2 and press F5 (the first import takes a moment). Look at the Output panel: report red or yellow lines.
2. You start in open water with the island ahead. You should see a coast with a beach, rocks, palms and, in the cove, a pier with lamps and houses behind it. Steer with A/D. Press F3 to hide the HUD.
3. Sail towards the cove (the HUD shows the berth distance and bearing). The ship should slow down on the screen as you near the pier (that is the harbor speed). Pass the buoys. When the HUD says IN THE DOCK ZONE, press SPACE.
4. Watch the ship swing round and slide in beside the pier, sails going slack. Press SPACE again to cast off; it backs out and turns to the sea, then you steer again.
5. Press N three times: sunset, night, dawn. At night the lamps and windows should glow and pool on the planks and the water. Check the island is not black at night.
6. Run the ship into the rocks or the beach: it must stop with the AGROUND banner. Try the pier side: you should stop, not pass through.
7. Press W for rain and fog, 1-7 for the weather checkpoints, F1 for quality, F2 for the 2D fallback (it has no island, and SPACE docks an invisible harbor there: expected).
8. Tell me: fps at Dev-Lite near the harbor (compare with open sea), what looks wrong, whether docking feels easy and reliable, and whether the ship looks like it belongs in the water and beside the pier.
**If the dev PC is slow only near the island,** tell me: it points at the 115,000-triangle island mesh (risk 1).

## 8. NOT verified in Godot (all of it)
- That any new shader compiles in Godot (the GLSL pass is a lenient transpile) or looks as intended: night lamps, water shadows, the berth outline, emissive windows, bobbing buoys.
- That the imported textures load (the `.import` files are hand-written like the H2D-0.1 ones; if Godot rejects them, open the editor once and it re-imports).
- That the ship billboard sorts correctly against the pier, piles and houses (depth bias is 2 m; the ship is 22 m long). It may clip at the pier edge: tell me.
- That docking runs as the twin says (the Python twin and the GDScript share equations and a fixture, replayed by `tests/test_harbor.gd`, which has never run).
- Any frame rate; any colour on the dev PC's real output (the earlier colour-calibration caveats stand).
- The sprites are numpy art made without an art tool; they are a prototype of the look, not final art.

## 9. Decisions and next steps
- H2D1-1 Anvil Cay is a prototype harbor island, not a registry island. H2D1-2 Docking is assisted (SPACE), not free-handling a 22 m hull at 5x speed. H2D1-3 Near a berth the scene speed is eased, a presentation cheat declared in the tuning file. H2D1-4 Grounding is a hull footprint. H2D1-5 Night is one global and six lamp positions, not a light system. H2D1-6 The 100-island plan is recorded in Canon v1.8 as the user's stated plan and is **not** built.
- Next (proposals; nothing started): (a) fix what your test finds in H2D-1; (b) a landing and a first walkable shore (ship to land) at the landing point; (c) E2: place the islands against the plan, once the 58 vs 100 conflict is settled.
