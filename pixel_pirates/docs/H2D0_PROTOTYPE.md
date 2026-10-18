# H2D-0: the representative HD-2D ocean scene (PROTOTYPE, NOT YET RUN IN GODOT)

> **Updated by H2D-0.1** (`H2D0_1_SAILING_AND_COMPAT.md`): new helm and keys (Z/X added), runtime fixes, F5 launches this scene.

**Status, stated plainly.** Everything below was written and statically checked in a sandbox that cannot run Godot. No shader has been compiled by Godot, no script has run, no frame has been rendered, and **no performance number exists**. What did run: the Python art bakers, the art checker, a GLSL syntax pass over the shaders, gdparse/gdlint on the scripts, and a Python replay of the pure logic. The look, the colour transfer and the speed on the dev PC are all unknown until the user runs it.
Also unconfirmed: the E1b self-test. The user reported "it works", but `build\slice_selftest.txt` never arrived, so the GPU, driver and OpenGL version of the HD 3000 are still unknown, and E2 stays blocked.

## 1. What the scene is
One playable ocean scene (`game/h2d/h2d0.tscn`): a pixel-art sloop (16 headings x 5 sail trims, wind-aware) on an animated ocean, with one island, Anvil Cay (160 m, 93 trees, a hill), in the real E1 weather (checkpoints 1-7). The simulation is the validated E1 one (Ocean, SeaState, world clock, weather smoothing). Only the picture is new, behind the single `SeaView` interface (D1):

| Path | File | What it is |
|---|---|---|
| 3D | `sea_view_3d.gd` | Real 3D scene in the Compatibility renderer, drawn into a SubViewport at the art grid and shown with nearest-neighbour upscaling. Camera FOV 22 deg, pitch 48 deg, north-up (D3). Sprites are billboards with depth bias; ocean, island and shadows are shaders; our own tilt-shift/grade/posterise post pass (Compatibility has no DOF blur). |
| 2D | `sea_view_2d.gd` | The E1 painter (`sea_painter.gd`) wrapped as the lightweight fallback. Still the side-view prototype look; kept only as a fallback. |

Quality profiles (3D): **dev_lite** 640x360, ocean mesh div 64, 6 shadow steps, posterise 12; **standard** 1280x720, div 128, 10 steps, posterise 16; **ultra** 1920x1080, div 192, 12 steps, posterise 24. Dev-Lite is a setting, not the product: the final game keeps full quality on capable hardware.

## 2. How to run (Windows)
Same Godot lookup as the slice: `tools\godot_path.txt` or `GODOT_EXE`. From the project folder:
- `tools\run_h2d0.bat` interactive. If the window is black or Godot reports an OpenGL error, try `tools\run_h2d0.bat angle` (forces the ANGLE/Direct3D 11 driver; whether it works on an HD 3000 is unverified).
- `tools\run_h2d0_bench.bat` (or `... angle`): about 80 s, hands off. Writes `build\h2d0_bench.txt`, `build\h2d0_bench_01.png` ... one screenshot per phase, and `build\h2d0_console.txt` (all Godot output, including shader errors).
- Keys: A/D steer, 1-7 weather, P pause, R reset ship, F1 quality, F2 3D/2D, F3 HUD, F4 flip colour transfer, F12 screenshot, `[` `]` pitch, `-` `=` exposure, `,` `.` visual speed, B benchmark.

**What to send back:** `build\h2d0_bench.txt`, the screenshots (at least `h2d0_bench_01.png`, `_04`, `_06`), and `build\h2d0_console.txt`. Also, if the first run looks wrong (too dark, washed out, black), press F4 and say what changed. If there is a black window or an error, send only `h2d0_console.txt`.

## 3. The benchmark
11 phases, each 1.5 s warm-up + 5 s measured, vsync off, the ship steered by a fixed sine so it turns and sails:
3D Dev-Lite x5 (checkpoints 2, 1, 4, 6, 7), 3D Standard x3 (2, 1, 6), 3D Ultra x1 (2), 2D x2 (2, 6).
Per phase: average fps, 1% low fps, worst frame ms, draw calls, objects, triangles, VRAM, and a picture sanity check (not flat, not black/white, not magenta). Header: adapter, vendor, API, driver, renderer, CPU, RAM, window size, colour-transfer result.
**Target (provisional, mine):** Dev-Lite average >= 30 fps and 1% low >= 20 fps in every phase. Standard and Ultra rows are information only. The report states MEETS TARGET or BELOW TARGET from the measured numbers; it never says passed otherwise.

## 4. Decisions made here (all PROVISIONAL, owner H2D-1)
- **Scale:** 1 scene metre = 10 world metres; scene speed = world speed / 10. A 5 kn sloop moves 24.7 scene m/s (`scene_speed_ms`); the sloop is about 22 scene m long. This is a presentation scale, chosen so a ship crosses the screen in seconds; it needs a decision in H2D-1.
- **Ship art:** 112 x 112 px frames, pivot (56, 66), 3.6 px per metre, 22 colours from 6 palette ramps. Sheet = 16 headings (22.5 deg) x 5 trim rows (-80, -45, 0, 45, 80 deg boom angle). The sail row comes from the wind angle: |rel| < 50 deg row 2; 50-110 rows 1/3; >= 110 rows 0/4; side by wind side.
- **Waves:** four summed sines (46/27/15/8.5 m wavelengths), computed in the ocean shader and mirrored in `wave_model.gd` so the ship bobs with the water (bob snapped to whole art pixels).
- **Light:** `light_model.gd`: sun 05-19 h, noon elevation = clamp(78 - 0.55|lat|, 18, 78), moon at night, cloud/storm grey the key light, fog density from visibility, lightning pulse about every 7 s in a storm.
- **Loading (superseded in H2D-0.1):** the first version read PNGs with `Image.load_from_file` and registered the shader globals at run time; both were wrong. See `H2D0_1_SAILING_AND_COMPAT.md`: textures are imported (lossless) and the globals are declared in `project.godot`.
- **Colour transfer:** the Compatibility 3D pass may or may not apply an sRGB encode; the scene draws a known 0.5 grey quad, reads it back and picks gamma 2.2 or 1.0 (`calibration_note`, F4 flips it by hand).
- **Grounding:** the ship cannot enter cells where the island height is above 0.3 m; it stops and says AGROUND.

## 5. What the checks cover, and what they do not
| Check | Covers | Does NOT cover |
|---|---|---|
| `tools/h2d/check_h2d_art.py` | sheet sizes, no sprite touches its frame border, pivot inside the silhouette, every colour in `palette.json`, colour and ramp limits, adjacent-heading silhouette IoU | whether the art looks good |
| `tools/h2d/check_shaders.py` | each shader transpiled to GLSL and run through glslang (undeclared names, type mismatches; mutation-tested) | anything Godot-specific: render modes, built-in availability per stage, global uniform registration, `pow(x, 3)` int strictness (it is MORE lenient than Godot) |
| `tests/test_h2d.gd` + fixture | ship-frame, trim-row and wave maths vs the Python twin (186+ style) | never executed in Godot |
| gdparse / gdlint | syntax and style | types, runtime errors |

**Real defects the art check found and fixed:** the bow-toward-camera headings (157.5, 180, 202.5 deg) were clipped at the bottom of the 96 px frame (frame is now 112 px tall), and a palm frond was clipped at the right edge of its atlas cell (lean and frond length reduced).
**Silhouette IoU between neighbouring headings** (trim 0): min 0.475, mean 0.55, max 0.635. So every 22.5 deg step changes the silhouette clearly (no heading is indistinct, no warning raised). That is a shape metric only: the contact sheet (`art_bible/h2d0/ship_headings_sheet.png`) still shows ugly sails at some headings, the due-N/S frames look the most awkward, and the sail reads as a flat sheet beside the hull rather than rigging. Acceptable for a prototype; the art is not final.

## 6. Known risks, in the order I would expect them to bite
1. A shader fails to compile in Godot (the checker is lenient). Symptom: black/odd scene, error in `h2d0_console.txt`.
2. Colour transfer wrong (picture too dark/pale): F4.
3. Billboard sprites cut by the ocean (the ocean is drawn first with depth writes off, sprites are pulled toward the camera).
4. The HD 3000 driver cannot do the 3D path at all (OpenGL 3.1). Then the `angle` argument, or the 2D path, is the answer; this is exactly what the benchmark decides.
5. No texel snapping of the sprites: some sub-pixel crawl while moving.
6. The ocean ignores the island (no shore wash in the water), the island is flat-lit in the preview and the hill looks muddy there.

## 7. What H2D-0 does not prove
It does not prove the HD-2D look is right, that Dev-Lite reaches 30 fps, that the 2D fallback is acceptable, or that the sprite pipeline scales to many ships. It is the smallest scene that can answer those once it has run.

## 8. Files
`game/h2d/` (scripts, `shaders/`, `art/`), `game/tests/test_h2d.gd`, `game/tests/fixtures/ship_sprite_cases.json`, `tools/h2d/` (`bake_ship.py`, `bake_island.py`, `ship_model.py`, `ship_sprite_logic.py`, `make_fixture.py`, `check_h2d_art.py`, `check_shaders.py`), `tools/run_h2d0*.bat|.sh`, `art_bible/h2d0/` (previews). Rebake: `python tools/h2d/bake_ship.py --preview`, `python tools/h2d/bake_island.py --preview`.
