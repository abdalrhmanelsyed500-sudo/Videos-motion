# E1b - Visual direction lock (HD-2D) and technical proposal

Status: **direction LOCKED by the user; proposal below awaits approval; nothing in it is built yet.** No Godot code has been run by me (no engine in my sandbox); everything in section 2 that touches Godot is unverified until you run the self-test.

## 1. Confirmation: what is locked

The final game is **HD-2D in the manner of Octopath Traveler / Octopath Traveler II**, as in the two reference images:
- pixel-art ships, islands, ports, vegetation, buildings and props;
- an **angled top-down camera** with real depth (not a side view, not realistic 3D);
- layered scenery, dynamic lighting and shadows, atmospheric fog, depth of field where it helps, controlled colour grading;
- an ocean that changes across tropical, temperate, stormy, frozen and mysterious regions, with distinct rain, fog, storm, wave, ice and light looks;
- one cohesive art direction for assets, effects, camera and environments;
- the ship visibly answers steering and movement; the world feels vast.

| | E1 prototype (today) | Final game |
|---|---|---|
| Camera | stern view, flat side-on, 640 x 360 `_draw()` | angled top-down, perspective camera (A3: FOV 22, pitch 48 at sea, 39 on land) |
| Ship | polygons | pixel-art sprite ship, many headings |
| Ocean | wave lines | pixel-look ocean plane, region-driven |
| Lighting | colour multiply | real light + shadows, sun azimuth from the clock |
| Status | **temporary technical prototype**: tests weather, ocean data, clock, steering | the target |

The E1 view is **not** the approved look and nothing about it (camera, layout, HUD placement) is carried forward except where section 4 says so. What E1 validates is the **simulation**: `Ocean`, `Wildlife`, `SeaState`, the one world clock, the console. Those are view-independent and stay.

**One conflict with earlier Canon, needing your decision (D2 below):** A3-3 says ships are 3D models with pixel textures. You now say pixel-art ships. I propose superseding A3-3.

## 2. E1b: outstanding issues investigated

| # | Finding | Action | Status |
|---|---|---|---|
| 1 | **Turning moved nothing on screen** (sun, clouds, stars and swell followed time, not the compass). The ship did not visibly answer steering. | Sky is now fixed to the compass: sun and moon by azimuth (east rise, south or north noon by hemisphere, west set), clouds and stars by azimuth, swell pattern slides with heading, ship leans into the turn. | changed, **unverified in Godot** |
| 2 | Pointing within 40 deg of the wind drops speed to 0.6 kn and the HUD said nothing. | `IN IRONS` warning with the angle. | changed, unverified |
| 3 | Steering has a mild effect on speed in the trades (3.9 to 5.0 kn across headings at 14 kn of wind); that is the model, not a bug. In irons it matters (0.6 kn). | none; recorded so nobody tunes by accident | by design |
| 4 | The E1 spec and Canon said "14 kn through the water". Wrong: 14 kn is the reference **wind**; the sloop makes 5 kn (9.3 km per game hour). The numbers (14.9 km per real minute) were always right. | wording corrected | fixed |
| 5 | The prototype has never run in Godot, so "validated" is currently false. | `tools\run_slice_selftest.bat`: scripted steering, pause, chart, three weather checkpoints, frame times, **GPU adapter and driver**; writes a report | written, **not run** |
| 6 | The Python concept stills do not include the new sky behaviour. | note only; they stay a data illustration | open |
| 7 | Unknown: which OpenGL path your HD 3000 uses (Godot Compatibility wants OpenGL 3.3; the HD 3000 driver reports 3.1; the engine may fall back to ANGLE). | the self-test prints the adapter, API version and driver | open |

What the self-test checks (it drives the real scene): 87 species, 10 regions and 7 checkpoints load; 3 s of steering turns the ship about 42 deg and back; the ship moves; 3 real seconds equal about 288 game seconds; pause and the chart freeze both clock and ship; the full-world chart reveal never stalls a frame beyond 250 ms; checkpoint 6 is a gale above 3 m waves; checkpoint 5 shows the Herald Swell with no gale yet; average FPS and worst frame at checkpoints 1, 2 and 6. It cannot judge how the picture looks, and it replaces the keyboard with a scripted value (press A and D yourself once).

## 3. Proposal: HD-2D in Godot, on low-end hardware

### Three ways to build it (D1)

| | A. Real 3D scene, pixel sprites (Octopath's method) | B. Pure 2D oblique projection | C. Both behind one interface |
|---|---|---|---|
| Idea | Camera3D (narrow FOV, pitched) over a sea plane; sprites stand on it as `Sprite3D`; real lights, shadows, fog; post shader for tilt-shift and grade | Node2D world scrolled under a fixed ship, rows scaled by y; faked depth | A first; B only as a Dev-Lite fallback |
| Look | the target: true perspective, parallax, shadows, depth of field | convincing but flatter; shadows and lights are faked | A on capable PCs, B on the dev PC |
| Low-end | needs OpenGL 3.3 class; Compatibility lacks DOF, volumetric fog, SSR (we do not need them) | runs on anything | two render paths to maintain |
| Risk | HD 3000 may be too slow or lack the path (unverified) | final quality ceiling | double art-integration work |

**Recommendation: A, built so that C stays possible.** Reason: you said the final game must not be compromised for the dev PC, and A is the only one that is the reference look. The renderer sits behind one small interface (section 4), so a 2D fallback can be added later if the benchmark says the HD 3000 cannot run A. We decide with a measurement (section 5), not an opinion.

### Camera and presentation
- **Camera3D, perspective, FOV 22, pitch 48 at sea (39 ashore), north-up and fixed in yaw** (D3). The camera follows the ship's position with a small look-ahead; it never rotates. Sprites therefore never need rotating, which is what keeps pixel art clean.
- The ship **changes sprite by heading** (16 headings, 9 unique plus mirrors), with a smooth lean (roll) and bob applied to the sprite's transform, plus sail-billow frames driven by wind angle. Turning is visible as the hull swinging through headings, the wake curving, and the world's lighting direction staying fixed.
- Pixel consistency: all 3D is rendered at the **art grid** (640 x 360 per A3, integer scale) into a SubViewport and upscaled with nearest filtering (Dev-Lite: 640 x 360 or 683 x 438; Standard: 1280 x 720, 2 px per texel, Ultra: 1920 x 1080). Ocean, shadows and effects therefore have the same pixel size as the sprites. Sprites use nearest filtering and texel-snapped positions to avoid shimmering.

### Ocean rendering
- A **ring mesh around the ship** (a few thousand vertices at most), snapped to a grid so it never "swims", with a vertex shader summing 2 to 3 sines (amplitude from `wave_m`, direction from the wind, wavelength grows with the Herald Swell) and a fragment shader doing colour (`look_at` deep/shallow), crest foam above a threshold (wind and storm), posterised to the palette so it reads as pixel art.
- Far water fades into the horizon fog; no per-frame region lookups in the shader: the region look is a handful of uniforms updated 2 to 4 times a second and eased (the E1 prototype already does this).
- Ice: floes as instanced quads on a noise mask over the plane (density from `ice`); icebergs as billboarded sprites at their hash-grid positions; the pack is a shader mask.

### Lighting, shadows, grading, depth of field
- One `DirectionalLight3D` for the sun/moon: **azimuth and elevation from the world clock and latitude** (the same formulas the prototype now uses), colour and energy from the T1 daylight curve and the region sky. Ambient from the region sky colour. Torches and ship lanterns: a few `OmniLight3D` (the Compatibility renderer defaults to 8 lights per mesh).
- Shadows: **blob/projected sprite shadows on Dev-Lite**, real shadow maps on Standard and Ultra.
- Colour grade through `Environment` adjustments (supported in Compatibility) with per-region and per-state grades from the A3 `state_grades`; glow lowered threshold (0.65) for the LDR pipeline.
- **Depth of field: our own tilt-shift shader** (A1-5), because the built-in DOF is not in Compatibility; off on Dev-Lite, 2 px blur on Standard.
- Fog: `Environment` depth fog (supported in Compatibility), colour from `look.fog_color`, density from `visibility_km` mapped to presentation distance.

### Weather
- Rain: CPU or GPU particle streaks near the camera, count from `rain`, slant from wind; wet-sea shader term (darker, more foam).
- Storm: wave and foam uniforms, darker sun energy, **lightning as a brief capped light-energy spike** (never a full-white strobe), cloud shadows drifting across the sea as a scrolling mask.
- Fog and ice as above; night and dawn from the same light curve.

### Wildlife and world objects
Sprites on the plane at true bearing and distance (whales blow, fish leap, birds fly), capped by `perf.max_instanced_creatures`; islands are the A6 kit tiles rendered as pixel-art billboards/terrain; the same `Ocean.sample` and `Wildlife.sighting` outputs feed them.

### Performance strategy (dev PC and final)
- Budgets (targets, not measurements): Dev-Lite under 150 draw calls, under 30k triangles, no shadow maps, no blur, 640 x 360 internal, textures under 256 MB, process under 1.2 GB (A1-8).
- Simulation cost already budgeted in E1: ocean resample every 9.4 real seconds, look every 2 s, icebergs every 1.5 s, chart 30 cells per frame, no weather or wildlife state saved.
- Quality scales **up** without touching data: Standard adds shadow maps, tilt-shift, glow; Ultra raises internal resolution and effect counts. The dev profile only lowers counts. Final art never changes for the dev PC.
- Gate: if the benchmark (section 5) is below 30 fps on Dev-Lite, the response is, in order: lower internal size, fewer ocean vertices, drop real-time light to baked-in tint, then the 2D fallback (option C).

## 4. Integrating the validated systems

The E1 scene splits along a line that already exists in the code:

| Keep (view-independent, validated by tests) | Replace (view only) |
|---|---|
| `Ocean`, `Wildlife`, `SeaState`, world clock, console `route`/`ocean`, chart data, journal, HUD *logic* | `ui/sea_painter.gd` (2D side view), HUD *layout*, camera |

`ocean_slice.gd` already builds one `view` dictionary (light, floor, hour, cloud, storm, herald, rain, fog, ice, wave_m, wind, heading, turn, lat, look) plus critter and iceberg lists. The HD-2D `SeaView3D` will take exactly that dictionary plus ship state (x, y, heading, speed, turn rate). Nothing in the model changes. The 2D painter stays as the Dev-Lite fallback and debugging view.

## 5. The representative HD-2D prototype (H2D-0): scope and acceptance

One scene, run from a launcher, with the same self-test harness:
1. Camera3D at the A3 values over the snapped ocean ring with region colours and wave uniforms from the real sample.
2. One placeholder pixel-art sloop sprite, 16 headings (generated from a simple model by a script; placeholder, replaceable), leaning and bobbing, with a pixel wake.
3. Sun azimuth lighting from the clock; sprite shadow; fog; tilt-shift (off on Dev-Lite); region grade.
4. Rain and the three weathers (clear noon, fog, gale) driven from checkpoints 2, 4 and 6; one island billboard from the A6 kit.
5. Steering with A/D with the world's light staying fixed while the hull swings.
6. Benchmark mode: average and worst frame time per scene and quality tier, GPU adapter and driver, written to a report.

Accepted when: you can steer and see the ship swing through headings; the three weathers are distinct; the benchmark report exists for your PC. **Performance on the HD 3000 is judged by that report only.**

## 6. Decisions needed (with recommendation)

- **D1 Render path:** A true 3D scene with pixel sprites (recommended), B pure 2D, C both. 
- **D2 Ship asset:** (1) hand-made pixel sprite sheets only; (2) low-poly 3D model with pixel texture (A3-3, today); (3) **recommended: pixel-art sprite sheets at runtime, layered (hull, sails, rigging, flag, damage) and baked from a simple 3D reference model for consistent angles, then hand-cleaned.** Supersedes A3-3. Runtime cost is sprites only; damage and sail states stay possible as layers.
- **D3 Camera:** north-up fixed (recommended; keeps sprites crisp) or heading-up (world rotates; pixel art suffers).
- **D4 Order:** run the self-test first (priority 1), then approve H2D-0 (priority 3).

## 7. Not verified

All of E1's GDScript and the new self-test have never run in Godot; the HD 3000's graphics path is unknown; every budget in section 3 is a target; the look of the HD-2D scene is untested; the sprite ship pipeline is a proposal.
