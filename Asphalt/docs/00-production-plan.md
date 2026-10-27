# THE ASPHALT GROOMS — عرسان الأسفلت

**Production plan / environment audit**

Tagline: *The Ring Road Waits for No One.*

## Environment audit (2026-10-27)

- Repository: `abdalrhmanelsyed500-sudo/Videos-motion`, branch `arena/2879e691-videos-motion`.
- Existing content: a Python/ImageMagick motion-test renderer, three realistic background plates, one narration MP3, and a sample MP4. None of it is a Godot project; existing work is preserved in the repository root and untouched.
- Godot was not preinstalled. Godot 4.2.2-stable is being made available as a portable Linux runtime for headless tests; the game project uses the Godot 4.2 API and `config_version=5`.
- Available creation tools: GDScript, procedural `ArrayMesh`/`SurfaceTool` geometry, procedurally generated PNG textures, Python + Pillow/NumPy for texture and image analysis, ImageMagick for inspection, and generated WAV audio.
- No external 3D model/skeleton/audio asset library is supplied. All geometry is authored procedurally as reusable Godot-ready `.tres` mesh resources and/or generated at runtime from deterministic mesh factories. This keeps the project self-contained and legally clean.
- Rendering tests use Xvfb + Mesa llvmpipe where a display is required. Target internal resolution is 1280 × 720.

## Technical decisions

1. **Godot 4.2 + GDScript**: a stable installed runtime with straightforward `CharacterBody3D`, `Area3D`, `StandardMaterial3D`, `ArrayMesh`, signals, and UI APIs.
2. **Procedural low-poly assets instead of external models**: every mesh has a known scale, pivot and material. Motorcycles are composed of cylinders, torus-like procedural wheels, tapered tanks, frames, forks, exhausts and lights — not a single box. Riders are modular low-poly articulated figures with distinct silhouettes.
3. **Spline-like road centerline with straight segment sampling**: the road is built as a continuous `ArrayMesh` strip, with separate marking meshes, shoulder strips, barriers, props and collision. This avoids visible seams while keeping collision simple and grounded.
4. **Gameplay-first physics**: arcade motorcycle dynamics are integrated in a `CharacterBody3D` with speed, lean, steering, gear/RPM model, lateral damping, and collision impulses. Traffic and rivals use deterministic lane-based movement with local hazard checks; no dependency on Godot navigation baking.
5. **Single autoload game state**: `GameState` owns roster/bike selections, settings, difficulty, race results and screen transitions. A `RaceManager` owns countdown, progress, position, time, police escalation and finish/crash resolution.
6. **Retro rendering by construction**: flat albedo materials, coarse textures, one directional light, a procedural sky, low geometry density, and deliberately restrained post-processing.
7. **Generated audio**: short original synthesized WAV tones stand in for engine, collision, countdown, siren and hospital stingers. The README documents them as procedural placeholders.

## Stage plan and acceptance criteria

| Stage | Work | Verification |
|---|---|---|
| 1 | Audit, reference analysis, runtime, docs | This plan; reference images analyzed; engine version verified by running `--version`. |
| 2 | Visual prototype: road, bike, rider, traffic, sky, cockpit dashboard, camera | Actual camera capture at 1280×720 and `compare_reference.py` report; inspect composition/palette; refine. |
| 3 | Handling: acceleration, brake, steering, gears, wheel spin, lean, collisions, camera modes | Scripted input tests on straight and curved road; verify speed, position, wheel angle, gauges, no falling through road. |
| 4 | Racing and traffic: rivals, lane decisions, spawning/despawning, race position/time/finish | Headless race simulation with deterministic RNG; verify multiple participants finish and positions update. |
| 5 | Crashes and police: severity, falling, hospital, pursuit and interception | Test harness triggers minor/moderate/severe impacts; verify one-shot crash state, hospital screen and retry; police escalates. |
| 6 | Asset production: 8 riders, 6 bikes, traffic types, buildings, signs, props | Resource audit checks meshes/materials, distinct silhouettes, wheel pivots, rider attachment points. |
| 7 | Complete loop: menu → rider → bike → settings → countdown → race → results → retry | Automated screen-flow test and manual headless run; verify each scene loads and transitions. |
| 8 | QA/performance: parser/runtime errors, visual defects, frame time, quality settings | Godot headless run logs, test report, measured frame time where rendering is available. |
| 9 | Handover: README, controls, structure, test report, known limitations, Drive upload | Final file audit and Drive folder contents; upload project archive and key docs to `Asphalt`. |

## Main risks and mitigations

- **No high-fidelity models**: procedural mesh factories prioritize silhouette, proportion, material readability and functional pivots. Distinct hair, clothing, accessories and bike geometry prevent recolor-only characters.
- **No real GPU/display**: logic tests run headless; visual captures use software Mesa. If software rendering fails, the project still ships with a reproducible capture script for the user's machine, and screenshots are not claimed as verified.
- **Scope vs. quality**: the complete loop is implemented first, then roster and environment density are expanded. Every script has a narrow responsibility; no giant monolith.
- **Arabic typography**: Godot's built-in font may not include Arabic shaping in all environments; UI uses a generated Arabic title texture for display and English/Latin labels for functional controls, with Arabic names in data docs. A bundled font can be added later if available.
- **Audio assets**: generated tones are clearly labeled as placeholders; no external copyrighted sounds are assumed.

## Delivery

All source work lives inside the local `Asphalt/` project folder, mirrored into the Google Drive folder named `Asphalt`. The final ZIP and key documentation are uploaded there. The original repository's unrelated motion-test files remain untouched.
