# H2D-0.2: Physically integrated weather, ocean and ship response (WRITTEN, NOT RUN IN GODOT)

**Read this first.**
- Nothing here has run in Godot; the sandbox cannot run it. What did run: a Python twin of the environment and the ship motion (the numbers below come from it), the GLSL syntax pass over all 8 shaders (lenient, not Godot), gdparse, gdlint and `tools/check_all.py`. None of that proves the picture looks right. **You are the test.** Press F5 and follow section 6.
- Scope: weather, ocean, rain, spray, sail shape and ship motion only. H2D-1, H2D-2 and E2 are not started. Sailing controls, wind and the no-go zone are unchanged.

## 1. What was wrong
The rain was drawn in `post.gdshader` as vertical streaks on the finished picture. Nothing in the world produced it, the ocean's rings were a separate pattern, the wave shape never changed with weather, the ship bobbed on one number, and a weather jump switched everything in 2 s. So the weather read as a filter. This step removes the filter and makes everything come from one source.

## 2. The one source: `h2d/env_model.gd`
The weather the world makes (`Ocean.sample`) is now only the **target**. The environment model is what the scene experiences:
- **Wind**: mean speed eases to the target (5 s), direction swings slowly (8 s). **Gusts** are deterministic in time (three incommensurate sines, so no repeat, no random numbers) and scale with how windy it is. In a gust the wind gains up to 45 %, veers up to 12 degrees, the boat gains up to 12 % speed (the sails draw harder), the sail flutters and a dark rough patch drifts over the water. Key **G** fires a gust by hand.
- **Sea state**: the waves build over about 40 s (time constant 14 s) and die away slowly (24 s). Wave direction lags the wind (20 s), so after a wind shift the old sea keeps running. A **sea-state index** 0..1 = 0.5 wave height / 6.5 m + 0.35 wind / 38 kn + 0.2 storm, named **Calm < 0.12, Breezy < 0.35, Rough < 0.65, Gale < 0.96, Storm**.
- **Rain** sets in over 5 s and eases off over 9 s; **visibility** follows rain and fog with the same formula as the ocean model.
- **Air drift**: how far the wind has carried the air. Rain bands, gust patches and ripples move with it, so the weather has a direction and a speed.
Python twin and spec: `tools/h2d/env_logic.py`; fixture `tests/fixtures/env_cases.json`; numbers in `data/tuning/tuning_env.json` (39 keys, owner E1, all provisional).

## 3. What you now see, and where each piece comes from
| Effect | How it is made | Driven by |
|---|---|---|
| Waves | 4 waves; crest shape goes from sine (calm) to flat troughs and peaked crests (gale), directions narrow a little as the sea builds; the mesh and the shading use the same function | wave height, wave direction, sea state |
| Rain | **Real drops in the 3D scene** (MultiMesh quads, `rain.gdshader`): each falls from about 28 m, slanted by the wind, to a landing point **on the wave surface**, then shows a small splash. No screen-space rain remains | rain, wind speed and direction, air drift (patchy light rain, even heavy rain) |
| Rings on the water | The ocean shader draws a ring at the landing point of the **same drop** (same grid cell, same hash, same phase) | rain |
| Spindrift | Streaks torn from crests, blown downwind, only where a wave crest is high and only as the sea state rises (`spray.gdshader`) | sea state, wave height, wind |
| Bow and rail spray | Droplets on a ballistic arc plus a foam ring, **triggered when the hull meets the water fast** (bow or a rail), never by a timer | ship motion events |
| Whitecaps, foam lanes | Whitecap threshold falls with the sea state; short foam dashes aligned with the wind appear from Breezy upward and drift downwind | sea state, wind direction |
| Gust patches, ripples | Darker rougher patches drift downwind; one is always over the ship during a gust | gust, air drift |
| Ship motion | Five points of the hull sample the wave field: bow and stern give **pitch**, the rails give **roll**, the mean gives **heave**; damped springs (roll 3.4 s, pitch 2.6 s, heave 2.2 s period); a steady **heel** from the wind in the sails | waves, heading, wind side |
| Drawn ship | Roll and pitch lean the mast (a shear worked out for the 48 degree camera), the sails belly toward the lee and flutter when luffing, in light air or in a gust, raindrops speckle the canvas | motion, wind, rain, luff |
| Hull wash | Foam along the hull (more on the rail that is rolled down) and an expanding ring at the bow after a slam | sea state, slam events |
Only the DRAWN ship moves with the sea. The helm, the course and the speed model are untouched.

## 4. What I expect, from the Python twin (ship at 5 kn; **not** observed in Godot)
| Sea | Roll | Pitch | Heave | Slams in 40 s |
|---|---|---|---|---|
| Calm | +-1.3 deg | small | small | 0 |
| Breezy | -3.5..+6.4 | +-3 | small | 0 |
| Rough | -5..+9 | +-5 | | 4-8 heading upwind |
| Gale | -10..+10 | +-6 | +-1.6 m | about 46 heading upwind, 0-2 downwind |
- Calm to gale (key W): the wind is near 24 kn after 5 s, the waves 2 m after 5 s and 5.3 m after 30 s, rain 0.5 after 5 s.
- Gusts: over 0.3 about 16-19 % of the time at 14-26 kn.
- Rain budget (default "medium"): 56 x 44 cells at 3.4 m, 2 drops per cell = 4,928 quads, about 3,000 streaks on screen in heavy rain. **No frame-rate figure exists.** The effects budget (key E) is how you trade look for speed.

## 5. Keys (new in bold; everything else as in H2D-0.1)
**W** weather lab: real, calm, breezy, rough, gale, storm, real... (wind direction stays real; the sea takes about 30 s to build) | **G** gust | **M** ship motion off / half / full | **E** effects budget low / medium / high | 1-7 jump to a checkpoint (its weather now fades in) | A/D steer, Z/X sensitivity, F1 quality, F2 3D/2D, F3 HUD, F4 colour, F12 screenshot, B benchmark.
The HUD has two new lines: sea state (name, index, gust, weather mode, effects) and ship motion (roll, pitch, heave, slam count).

## 6. How to test (about 10 minutes)
1. Open the project, F5. Expect no red errors. The first line of the HUD says H2D-0.2. **Copy the Output panel text if anything is red or yellow.**
2. **Calm** (W once): almost no rings, the sail hangs and flutters a little, the ship barely moves, no spray. M to "off" and back: the ship should visibly stop and start rocking.
3. **Rough** (W twice more): over about 30 s the waves grow and the crests sharpen; whitecaps and foam dashes appear; light rain in patches; steer upwind (A/D) and watch the bow lift, the mast lean and an occasional burst of spray at the bow. Turn beam-on: it should roll more, not pitch.
4. **Gale / storm**: dense rain falling at the wind's slant with splash and rings at the same places; spindrift streaks off the crests; the ship leans and is thrown about but never flips; you can still steer.
5. **The rain is in the world, not on the screen**: in rain, change heading and press 1-7: the slant follows the wind direction of that place, never your heading; drops land on the water (watch a ring start where a streak ended).
6. **G**: a dark patch crosses the water, the sail flutters, the ship surges a little, HUD "gusting" rises.
7. **E** low/medium/high: same look, different density. **F1** Dev-Lite/Standard/Ultra. Note the fps shown on the HUD in calm and in a storm, at each effects level.
8. P pauses the game clock only; the rain and waves keep moving (they run on real time).
What to send back: red/yellow Output text; fps in calm / gale at Dev-Lite medium; for each thing that looks wrong, one line (for example "rain looks like thin white lines, too regular", "ship leans the wrong way", "spray every second in a gale").

## 7. Tuning without code
`data/tuning/tuning_env.json` (read at start-up; re-run after editing):
- `env.sea_build_s` / `env.sea_decay_s` how fast the sea grows and dies; `env.gust_gain`, `env.gust_surge`, `env.gust_veer_deg` gust strength; `env.crest_p_gale` how peaked gale crests are (1 = plain sine).
- `motion.gain` overall ship motion (also key M); `motion.roll_max_deg`, `motion.pitch_max_deg`, `motion.heave_max_m` limits; `motion.roll_period_s` etc. weight (larger = slower and heavier); `motion.heel_deg_per_ms2` steady wind heel; `motion.slam_bow_ms` / `motion.slam_side_ms` how fast water must rise to throw spray (raise for less spray); `motion.slam_cooldown_*` minimum time between bursts.
Constants in the shaders (rain density, streak length, ring size) are in `rain.gdshader`, `ocean.gdshader` and `sea_view_3d.gd` (`EFFECTS`).

## 8. Known limits (honest)
- Unverified in Godot: all of it. Risks I cannot rule out: an unexpected shader compile error in the Compatibility renderer (the first message will say which shader), MultiMesh `INSTANCE_ID` behaviour on the HD 3000 through ANGLE, rain streaks that are too thin or too bright at 640 x 360, fill-rate cost of about 5,000 transparent quads on integrated graphics.
- Sail bulge direction is "toward the lee in screen space", not computed per tack. Roll direction on screen uses the camera angle (48 degrees) and was derived by hand, not seen.
- Rain drops land on the same spots only once per 1.5 s cycle and then re-roll; rain is a field of independent drops, not a physical simulation of clouds.
- The wake, the ship's shadow and the island shader are unchanged. Trees do not sway yet. The 2D fallback shows the new weather numbers but not the new rain or spray.
- All new numbers are provisional (owner E1) until you have judged them by eye.

## 9. Files
New: `h2d/env_model.gd`, `h2d/ship_motion.gd`, `h2d/shaders/rain.gdshader`, `h2d/shaders/spray.gdshader`, `data/tuning/tuning_env.json`, `tests/test_env.gd`, `tests/fixtures/env_cases.json`, `tools/h2d/env_logic.py`, `tools/h2d/make_env_tuning.py`, this document.
Changed: `h2d/h2d0.gd` (environment, keys, HUD), `h2d/sea_view_3d.gd` (effects, motion, uniforms), `h2d/wave_model.gd` (shaped waves; old functions untouched), `shaders/h2d_common.gdshaderinc`, `ocean.gdshader`, `ship.gdshader`, `post.gdshader` (screen rain removed), `project.godot` (4 more shader globals), `tools/check_all.py`, `tools/h2d/check_shaders.py`.
Tests: `tests/test_env.gd` replays the Python twin (waves, environment transitions, ship motion, spray events) and checks that the GDScript defaults equal the JSON; run it with the other tests when Godot is available (`tools/check_all.py --godot PATH`).
