# Hybrid 2.5D benchmark — implementation and results

**Status: built, captured, and tested. Recommended as the future art direction.**

All experiment files are isolated under `experiments/hybrid_2p5d/` plus the scene `scenes/experiments/hybrid_2p5d_benchmark.tscn`. The production 3D gameplay systems were not rewritten.

## What was built

A self-contained Godot 4.2.2 `Control` scene (`AGHybrid25DBenchmark`) that renders:

- a scanline pseudo-3D road with curve and elevation;
- low-resolution dark purple-gray asphalt with coarse road-relative texture patches;
- double-yellow centerline, dashed white lane lines and white edge lines that scroll with `distance_traveled`;
- sky, coarse clouds, sandy hills, far Egyptian buildings, near roadside buildings, awnings, Arabic signs, palms and barriers;
- perspective-scaled rider/bike and traffic sprites;
- a dedicated fallen-rider / sliding-bike crash composition;
- a fixed cockpit base with dynamic needles, gear, speed, RPM, boost and status lights.

The renderer is 2D, but the **simulation is road-relative**. Every visible object has a `z` distance ahead of the player and a lane/lateral value. `project(z, lateral)` converts those to screen position/scale. Collision checks use the same `z` and lane values, not screen pixels.

## Original asset production

`tools/generate_hybrid_assets.py` deterministically generates all original art with Pillow:

- `rider_bike_sheet.png`: 128×128 frames, transparent, 4×3 atlas.
  - 7 riding frames: ride, steer left/right, lean left/right, accelerate, brake.
  - 5 crash frames: fall 1, fall 2, slide, recovery, defeat.
  - Fixed rear-wheel baseline and shared pivot `[64,126]` prevent wheel/rider jumping.
  - Egyptian streetwear: red jacket, tight blue jeans, spiky black hair, tan skin, sneakers, crossbody bag, gold earring/scarf accent.
- `traffic_sheet.png`: 6 Egyptian-relevant vehicle types (taxi, car, microbus, truck, trailer, police) × 3 angles, 128×96 frames, transparent.
- Background layers: `sky.png`, `hills.png`, `ground.png`, `buildings_far.png`, `roadside_left.png`, `roadside_right.png`.
- `cockpit_base.png`: dark fairing, two analog gauges, gear box, engine strip and status labels. Needles/numbers are drawn live in Godot.
- `hybrid_assets_manifest.json` and `sprite_audit.json`: frame names, pivots, collision sizes, checksums and alignment checks.

`sprite_audit.json` passes: all frames are the same size, have transparent backgrounds, non-empty alpha bounds, and consistent pivots.

## Real gameplay systems in the experiment

The prototype is not a static animation. It implements:

- acceleration, engine braking, braking, boost, max speed, gear and RPM;
- speed-dependent steering and continuous lane positioning;
- 3 rival riders with lane-change AI and race position;
- 6 traffic types with type-specific speeds, following/lane changes and respawning;
- a stationary fallen-rider/bike hazard with its own collision box;
- police pursuit levels, police car spawn and HUD warning;
- road-relative collision detection with severity (minor, moderate, severe);
- severe crash → falling/sliding frames → WIPEOUT state → hospital defeat sequence;
- retry (`R`), race termination by finish distance, and finish position;
- benchmark modes for static, moving, crash, hospital, finish and debug captures;
- debug overlay showing road-relative `z`, lane, speed, curve and collision boxes.

Controls: `W/↑` throttle, `S/↓` brake, `A/D` or `←/→` steer, `Shift` boost, `Space` handbrake, `P` police alert, `F` force crash, `G` force finish, `V` debug, `R` retry, `Esc` quit.

## Captured evidence

- `screenshots/hybrid_benchmark_static.png` — cockpit/race composition.
- `screenshots/hybrid_benchmark_moving.png` — different distance/speed, scrolled markings, readability during movement.
- `screenshots/hybrid_benchmark_crash.png` — fallen rider, sliding bike, WIPEOUT and crash reason.
- `screenshots/hybrid_benchmark_hospital.png` — non-graphic hospital defeat sequence.
- `screenshots/hybrid_benchmark_finish.png` — race termination/results state.
- `screenshots/hybrid_benchmark_debug.png` — road-relative collision/debug overlay.
- `screenshots/benchmark_3d_crash.png` — preserved full-3D crash composition for A/B.
- `screenshots/ab_cockpit_reference_3d_hybrid.png`, `ab_movement_reference_3d_hybrid.png`, `ab_crash_reference_3d_hybrid.png` — three-panel reference/3D/hybrid reviews.

`tools/capture_hybrid_benchmark.gd` and `tools/capture_3d_crash_benchmark.gd` produced genuine 1280×720 in-engine captures under Xvfb/Mesa llvmpipe.

## Test results

- `tools/run_hybrid_tests.sh`: **21 checks, 0 failures** (`tests/reports/hybrid_smoke.json`).
  - Verified scene load, asset load, sprite audit, road projection, acceleration, deterministic race progression, gear/RPM, steering, police spawn distance, severe crash, hospital transition, retry, finish and all benchmark modes.
- `tools/run_tests.sh` on the full project after adding the experiment: static audit passed, all GDScript parsed, production smoke **27/27** passed.
- Static audit after experiment: 42 GDScript files, 11 scenes, 0 missing resources.

## Measured comparison

| Capture | Reference | Global RGB distance | Mean region RGB distance | Structure score |
|---|---|---:|---:|---:|
| Hybrid cockpit | ref 1 | 23.62 | 35.04 | 0.2232 |
| Hybrid moving | ref 3 | 15.65 | 41.81 | 0.3046 |
| Hybrid crash | ref 2 | 26.27 | 39.66 | 0.1742 |
| Full 3D cockpit | ref 1 | 22.13 | 52.17 | 0.2801 |
| Full 3D bridge | ref 3 | 16.78 | 62.98 | 0.3654 |
| Full 3D crash | ref 2 | 9.40 | 31.16 | 0.2085 |

Full 3D wins some global/structure numbers; hybrid wins cockpit/movement region distances and matches the reference art grammar more closely on inspection. Neither approach is an exact recreation.

## Strengths

- Much closer retro-cockpit presentation: fixed dashboard, coarse sprites, layered backgrounds, strong road perspective.
- Cheap to render and easy to art-direct at consistent low resolution.
- Road-relative physics and projection agree; collisions are not screen-space hacks.
- Sprite sheets and background layers can be regenerated/extended systematically.
- Crash/fall/recovery frames are explicit and readable.

## Weaknesses / remaining work

- Current rider/traffic sprites are a small proof set; final production needs 8 riders, more angles, and more traffic variants.
- Foreground crash sprites are currently too large; scale them down and add intermediate fall frames.
- Background layers still use modest parallax; more unique building/hill/bridge layers are needed to avoid repetition.
- The cockpit base is close but not identical to the reference fairing/gauge silhouette.
- No real-GPU performance measurement or manual controller test yet.
- The experiment has its own simplified simulation; production integration must map existing `RaceManager`/`TrafficSystem`/`PoliceSystem` data to the same road-relative coordinate model.
- Exact visual fidelity remains unclaimed.

## Next steps

1. Promote the hybrid renderer into modular production scripts while keeping the 3D project intact.
2. Expand sprite sheets and backgrounds with the same generator/metadata/audit pipeline.
3. Port menu → rider → bike → countdown → race → results/hospital → retry screens onto the hybrid world.
4. Integrate persistent settings, unlocks and difficulty from `GameState`.
5. Add real-GPU 1280×720 performance tests and tune quality.
6. Repeat A/B review with new sprite batches before declaring the final art direction shipped.
