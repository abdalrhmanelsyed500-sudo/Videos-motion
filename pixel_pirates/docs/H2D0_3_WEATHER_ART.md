# H2D-0.3: Weather art direction and motion refinement (WRITTEN, NOT RUN IN GODOT)

**Read this first.**
- Nothing here has run in Godot; the sandbox cannot run it. What did run: Python twins of the sail and the environment, two numpy diagnostics (`tools/h2d/sail_preview.py`, `tools/h2d/rain_preview.py`, both labelled diagnostic: they prove numbers, not looks), the GLSL syntax pass over 8 shaders (lenient, not Godot), gdparse, gdlint and `tools/check_all.py`. **You are the test.** Press F5 and follow section 6.
- Scope: sail motion, rain, and the identity of the six weathers. H2D-1, H2D-2 and E2 are not started. Controls, map, clock and the HD-2D camera are unchanged.
- This is a response to your test of H2D-0.2: the sail billowed and fluttered too fast and too much, looped, and looked the same in every weather; the rain was not natural; the weathers were one effect at different strengths.

## 1. What was actually wrong (measured on a Python copy of the old shader, not in Godot)
| Weather | H2D-0.2 sail, whole-pixel changes per second | Cause |
|---|---|---|
| calm | **4.1** | a constant ~2 Hz sine flutter that never depended on the wind: `1.6*sin(p.y*0.55 + time*13)` times `flutter = luff + 0.5*slack + 0.35*gust` |
| breezy, rough | 0 | the belly was a nearly constant ~2 px in every wind, so the sail looked the same in a breeze, rough sea and gale |
| gale | 1.3 | the same flutter plus gusts |

Also: the vertical profile of the sail was a fixed band (rows 11..62) although the real sail in the art spans 12..57 in one frame and 19..77 in another; the displaced sampling was not snapped to whole pixels (shimmer); the sail-trim drawing switched at 50 and 110 degrees with no hysteresis (pop). Rain: streaks only ~1.6 m long, which is **about 3 px** on screen at the art grid (they read as dots); every drop had the same 1.5 s period (a visible pulse), the same size and brightness, the same slant everywhere; rings lasted 0.24 s and were about 1 px. The camera is **257 scene m** from the ship (not 190 as the old fog constant assumed), the screen spans 219..312 m.

## 2. Sail: a model with state (`h2d/sail_model.gd`, twin `tools/h2d/sail_logic.py`, fixture `tests/fixtures/sail_cases.json`)
- **fill** is a damped spring (period 2.8 s, damping 0.55) towards a target from the wind speed in the sail, the angle to the wind (luffing, close-hauled, reaching, running), a gale (taut and flat: -35 %) and a gust (+35 %: it fills, overshoots a little, settles). So a gust is something you see arrive and leave, not a state.
- **flap** (flutter) is only present while luffing with wind in the sail, or briefly when a gust *arrives* (wind rising fast). It builds in 0.6 s and fades over 1.4 s; its rate is 0.4 Hz + 0.025 Hz per knot, modulated by three incommensurate sines, so it never repeats.
- **breath**: sub-pixel, two unrelated periods, only in light air.
- The shader (`ship.gdshader`) turns these into **whole-pixel shifts per 3-pixel band**, anchored at the mast edge, the head and the foot (per-frame sail box from `art/ship_sloop_sailbox.json`, made by `tools/h2d/make_sail_boxes.py`); at most about 2 px. A slack or luffing sail also shows dark fold lines; a taut one is smooth.
- The trim drawing now has hysteresis (6 degrees), `ShipSprite.trim_row_sticky`.
- Result by the Python twin (60 s, beam reach, changes per second at a mid-sail pixel): calm 0.10, breezy 0.27, rough 0.33, gale 0.43; in irons: calm 0.33, breezy 3.1, rough 4.1, gale 5.5 (luffing is intentionally the lively case, and it is the visual cue for IN IRONS). Mean belly: calm 0.2 px, breezy 2.4, rough 2.4, gale 1.7 (flat and taut).
- **Honest limit:** at 112-px art, one pixel is the smallest possible step, so breezy and rough sails differ little in shape; they differ in what the SHIP does (roll, spray) and in the water. The sail itself separates calm (slack, folds, nearly still), a drawing breeze (full, steady), a gale (flat, taut, gust shivers) and luffing (flutter).

## 3. Rain (`rain.gdshader`, `h2d_common.gdshaderinc`, `ocean.gdshader`)
- **No two drops alike.** Every slot has its own period (1.25..1.9 s), so nothing pulses in step; every drop has its own size, speed and brightness; about one in three is a brighter "near" drop.
- **Pixel-art streak.** Two tones, a bright head (first 30 %) and a dim tail, hard edges. Streak length is 1.7 m in light rain to 3.4 m in a downpour (about 4 to 8 px on screen; H2D-0.2 was about 3). Far drops are dimmer (depth); fog hides them like everything else.
- **Rain bends where the gust is.** The slant follows the MEAN wind everywhere; inside the dark gust patch on the water (`h2d_gust_field`, the same field the ocean darkens) it leans up to 80 % more, and slow eddies make neighbouring drops lean alike. So you see the gust cross the water, darken it, and bend the rain over it.
- **Light and heavy rain differ in kind.** Drizzle is sparse, short and nearly upright; a downpour is dense, long, slanted and comes in **sheets** (broad bands twice as thick as the gaps, drifting with the air).
- **Splashes.** Crown and ring last 0.5 s (were 0.24 s), grow to about 0.7 m, and are 60 % size in light rain. The ring on the water is still the landing of the same drop (same cell, hash, period and phase).
- **Density is capped and the same on every effects level.** `h2d_rain_dens` = 0.9 / 0.5 / 0.32 for low / medium / high (the level changes how many slots exist, this changes how many are active). Numpy diagnostic of the drop placement at medium: drizzle about 110 drops on screen (0.3 % of pixels), steady rain about 520 (2.1 %), downpour about 1,000 (5 %). If a downpour feels too busy, lower `look.rain_density`.

## 4. The six weathers
All derive continuously from the shared environment (`h2d/weather_look.gd`, `light_model.gd`), so a change of weather fades from one look to the next. New shader globals: `h2d_overcast`, `h2d_fog_start`, `h2d_focus`, `h2d_rain_dens` (declared in `project.godot`). `overcast = max(1.4(cloud-0.25), 0.9 rain, storm, 0.8 fog)`.
| | Light | Water | Rain / spray | Sail | Ship | Visibility |
|---|---|---|---|---|---|---|
| **Calm** | warm, full sun, cloud shadows | glassy: ripples 35 %, **long low swell** (wavelength x1.25, 80 % in the longest wave), sky mirrored more towards the horizon, **broad glitter path** that changes slowly | none | slack, folds, nearly still | roll about 1 degree, no slams | clear |
| **Breezy** | bright, drifting cloud shadows | bright cat's-paw ripples, **small sharp glints**, a few white tips | none | full and steady | roll 3 to 5 | clear |
| **Drizzle / rain** | **overcast: no glints, no cloud shadows, flat light** (a little diffuse light comes back), colours slightly desaturated | dull, pitted, greyer | short or long streaks, rings, sheets in heavy rain | full | as the sea | closer horizon (fog cap 0.006) |
| **Fog** | milky bright fog colour, flat light, no glints or shadows | calm swell | none | slack | still | fog starts **50 m closer**, reaches the ship (about 60 % of its colour), far sea about 80 % hidden |
| **Rough** | darker | dark blue-grey, whitecaps, foam dashes along the wind, **gusts that visibly cross the water** | spindrift begins | full, gusts shiver | roll up to 9, pitch 5, slams only head to sea | as rain |
| **Gale** | overcast, storm grey | peaked steep crests (wave mix 42/30/18/10 %), streaked foam | spindrift, heavy rain bent by gusts | taut and flat, gust shivers | roll 10, pitch 6, heave 1.6 m, about 55 slams per 40 s upwind | close |
Removed: the **screen-space haze and lightning overlays** in `post.gdshader`. Lightning is now a boost of the scene's own light (ambient, fog and sun, `LightModel.flash`), so it lights the water, ship and rain. The old fog cap of 0.09 per metre erased the ship; the caps are now 0.006 (rain, haze) and 0.009 (thick fog).
Wave composition now depends on the sea state (`WaveModel.mix_for_sea`): long swell when calm, the old mix when rough, more short steep waves in a gale. Twin: `wave_mix` in `env_logic.py`; four builds in the fixture.

Also fixed on the way: `ShipMotion` was **never configured from the tuning file** in H2D-0.2 (it ran on its built-in defaults, which equal the JSON, so no visible bug, but edits to `motion.*` were ignored). `View3D.configure_env` now passes the table to the motion, the sail and the look.

## 5. Tuning (all provisional, `data/tuning/tuning_env.json`, 62 keys)
`sail.*` (15 keys): fill period and damping, maximum belly (2.2 px), flutter size, rise, fall, rate, gust gain, breathing. `look.*` (8 keys): `rain_fall_ms` 19, `rain_streak_m` 3.4, `rain_drift_factor` 0.55, `rain_gust_bend` 0.8, `rain_density` 1.0, `fog_start_shift_m` 50, `fog_density_cap` 0.009, `haze_density_cap` 0.006. Edit the JSON, press F5; no code changes.

## 6. How to test (about 5 minutes)
Open the project, press **F5**. Keys: **W** weather lab (real, calm, breezy, drizzle, rain, fog, rough, gale, storm; the sea takes about 30 s to build or die away), **G** gust, **M** ship motion off/half/full, **E** effects low/medium/high, A/D steer, Z/X turn sensitivity, F3 HUD.
1. Press **W** once (calm). Wait 20 s. **Sail:** nearly still, faint dark fold lines, occasionally one pixel of drift. It must NOT shiver. Water: glassy, a long soft glitter path.
2. **W** (breezy). Sail fills to a steady belly and stays. Small sharp glints, cloud shadows drifting.
3. Steer into the wind (until IN IRONS shows). The sail flutters; steer away and it fills again within a few seconds.
4. **W** until **drizzle**: sparse, short, nearly upright streaks, small rings, no glints, flat light. **W** to **rain**: more, longer, slanted, in bands.
5. **W** to **fog**: milky, the horizon comes close, the ship stays visible but veiled.
6. **W** to **rough**, press **G** a few times: a dark rough patch should drift over the ship and **the rain/spray should lean harder inside it**. (In rough there is little rain; watch it in gale.)
7. **W** to **gale**: sail flat and taut, shivers once when a gust arrives, heavy bent rain, spindrift, the ship rolling and slamming. Turn downwind: slams almost stop.
8. Press **E** to switch effects levels: the amount of rain should look about the same at each level.
9. Press **F1** (Standard) only if the frame rate allows.
Please report: red or yellow Output text; fps in calm and in gale (Dev-Lite, medium); and ONE LINE per wrong thing, e.g. "sail still moves too fast in calm", "rain too dense in gale", "fog hides the ship".

## 7. Risks (nothing here is verified)
- Shader compile in ANGLE/D3D11 on the HD 3000; the new rain vertex shader calls a noise function twice and the gust field once per vertex (about 20,000 vertices at medium). `INSTANCE_ID` was already used in H2D-0.2.
- 4 to 8 px streaks, 1.4 px wide, may look thin or aliased at 640x360.
- Fill rate: the rain is alpha-blended quads over about 5 % of the screen in a downpour.
- Every value is hand-tuned and provisional. No frame-rate figure exists.
- The fog caps are computed for a 257 m camera: if the camera pitch (`[` `]`) changes, the veil changes with it.

## 8. Files
New: `h2d/sail_model.gd`, `h2d/weather_look.gd`, `art/ship_sloop_sailbox.json`, `tests/test_sail.gd`, `tests/fixtures/sail_cases.json`, `tools/h2d/sail_logic.py`, `make_sail_boxes.py`, `sail_preview.py`, `rain_preview.py`. Changed: `ship.gdshader`, `rain.gdshader`, `ocean.gdshader`, `post.gdshader`, `h2d_common.gdshaderinc`, `spray.gdshader`, `light_model.gd`, `wave_model.gd`, `ship_sprite.gd`, `sea_view_3d.gd`, `h2d0.gd`, `project.godot` (4 globals), `tuning_env.json`, `test_env.gd`, `env_logic.py`, `check_all.py`.
