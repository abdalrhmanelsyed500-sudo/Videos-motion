# Test report

**Final status: automated checks passed on 2026-10-27.** All results below come from the cleaned final project file set. Manual real-GPU play and exact visual fidelity are explicitly **not** claimed as tested.

## Environment

- Engine: official **Godot 4.2.2-stable**, version string `4.2.2-stable (official)` / `4.2.2.stable.official.15073afe3`.
- Logic tests: Godot headless/dummy rendering driver with `--disable-render-loop`.
- Visual capture: Xvfb + Mesa llvmpipe, `gl_compatibility`, OpenGL 3.3 Core Profile, 1280 × 720, dummy audio.
- Project settings: `config_version=5`, GDScript, no external binary model pack.

## Command summary

```bash
GODOT=/path/to/Godot_v4.2.2-stable_linux.x86_64 ./tools/run_tests.sh
./tools/capture_benchmark.sh
python3 tools/compare_reference.py --reference docs/reference/reference_01.png \
  --capture screenshots/benchmark_cockpit.png --label final-cockpit \
  --report docs/metrics_final_cockpit.json --review screenshots/review_final_cockpit.png
```

`tools/run_tests.sh` runs the static audit, Godot import/global-class refresh, a `--check-only` parse pass over every GDScript file, and the headless gameplay smoke test.

## Verified features

| Area | Result | Evidence |
|---|---|---|
| Engine version | Pass | `godot --headless --version` → `4.2.2.stable.official.15073afe3`. |
| Static resource audit | Pass | `tests/reports/static_audit.json`: 0 errors. |
| Roster/data integrity | Pass | 8 riders, 6 motorcycles, 7 traffic types; unique IDs; distinct hair/accessories; portraits exist. |
| Asset manifest | Pass | 57 deterministic asset files, SHA-256 verified; 743,515 bytes. |
| Project structure | Pass | 38 GDScript files, 10 scene files, 107 generated/imported asset files. |
| GDScript parse | Pass | All 38 `.gd` files pass `godot --check-only --script`. |
| Import | Pass | `logs/import.log` has no script/parse/compile errors. |
| Main scene launch | Pass | Headless `main.tscn` run exits 0. |
| Race scene launch | Pass | Headless `race_world.tscn` run exits 0; no GDScript errors. |
| Road mesh | Pass | First triangle normal `(0, 0.999999, -0.001564)`; top-down diagnostic shows continuous asphalt. |
| Handling / drivetrain | Pass | Injected throttle produces forward motion, speed > 8 m/s, wheel rotation > 0.1 rad, gear ≥ 2, progress > 0. |
| Bike/rider pivots | Pass | Front/rear wheels, steering, rider head/arms/legs present; all 6 bike and 8 rider factories instantiate. |
| Traffic models/spawn | Pass | 7 vehicle styles instantiate with wheels; closest initial traffic is > 75 m after fix. |
| Police | Pass | `force_alert()` escalates level and spawns police > 200 m ahead; no teleport onto player. |
| Severe crash | Pass | One-shot `crash_active`, race state `CRASHED`, fall completes, final result `crashed=true`. |
| UI scenes | Pass | Main menu, rider select, bike select, settings, pause, HUD, results and hospital all instantiate. |
| Full loop | Pass | Main starts race, shows results, shows hospital, retries, and returns to menu. |
| In-engine screenshots | Pass | 3 × 1280 × 720 PNGs saved from real Godot cameras; `screenshots/capture_report.json`. |
| Reference comparison | Pass (review aid) | Final cockpit global RGB distance 22.13; final bridge 16.78; review images generated. |

## Headless gameplay smoke test

`tests/reports/smoke.json`: **27 checks, 0 failures**.

The test instantiates the real `RaceWorld`, waits for the shortened test countdown, injects throttle, observes speed/position/wheel/gear/progress changes, exercises all model factories, forces police escalation, triggers a severe crash, waits for the fall/result, instantiates every UI scene, and drives the complete `Main` retry/menu loop.

A first run failed one check: `traffic_safe_spawn` reported a vehicle 6.9 m from the player. Root cause: initial traffic was distributed around the road start rather than relative to the player, and `prepare_benchmark()` left some vehicles at the camera. Fixes: initial traffic now starts at least 90 m ahead, every benchmark vehicle is repositioned ahead, and the smoke threshold is > 75 m. The final run passes all 27 checks.

## Visual benchmark results

- `docs/metrics_final_cockpit.json`: global RGB distance 22.13, mean region RGB distance 52.17, structure score 0.2801.
- `docs/metrics_final_bridge.json`: global RGB distance 16.78, mean region RGB distance 62.98, structure score 0.3654.
- `docs/metrics_final_replay.json`: global RGB distance 36.59, mean region RGB distance 44.47, structure score 0.2165.
- Before/after details and the structured checklist are in `docs/02-visual-benchmark.md`.

## Warnings and environmental noise

- Godot's **dummy renderer** emits many `Parameter "m" is null` messages from `mesh_get_surface_count` when generated `ArrayMesh` resources are inspected in headless mode. These are rendering-server-null warnings, not GDScript errors; the same project renders correctly under Xvfb/Mesa llvmpipe.
- Software capture logs one benign `Could not set V-Sync mode. V-Sync is not supported.` warning.
- Early captures had two `Control` anchor-size warnings; these were removed by deleting explicit `size` writes after `set_anchors_and_offsets_preset()`.
- `ObjectDB instances leaked at exit` / `Resources still in use at exit` can appear when the test `SceneTree` script quits immediately after freeing nodes; no failed checks or broken resources result.

## Untested functionality

- Manual keyboard/mouse play on a physical real-GPU desktop.
- Measured 30 FPS on real hardware; software llvmpipe capture is not a performance benchmark.
- Physical gamepad hardware, force feedback, or exotic controller remapping.
- Audio playback quality through speakers/headphones; generated WAV files are placeholder tones.
- Exported desktop/web binaries and long-duration (30+ minute) stability.
- Network multiplayer or cloud save synchronization.
- Exact visual fidelity to the three supplied screenshots.

## Known limitations

- Audio is procedural placeholder WAV, not recorded motorcycle samples or licensed music.
- Arabic display text is rasterized into title/sign textures; functional labels use Latin text for font-shaping reliability.
- No external high-detail 3D model pack, skeletal animation files, or cinematic voice acting.
- The road and environment are a low-poly interpretation, not an asset-for-asset recreation.
- The default `gl_compatibility` renderer prioritizes broad compatibility over modern post-processing.

## Reproducibility

Reports are stored in `tests/reports/`, comparison JSON in `docs/metrics_*.json`, logs in `logs/`, and captures/review images in `screenshots/`. The asset generator and its manifest allow deterministic regeneration of all original PNG/WAV/JSON assets.
