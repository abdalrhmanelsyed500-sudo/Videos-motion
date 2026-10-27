# Architecture

## Root ideas

- **One project folder**: all game source is under `Asphalt/`. The unrelated repository root is left intact.
- **Runtime assembly**: complex 3D models are deterministic assemblies of Godot meshes created at runtime. This avoids binary model imports and keeps pivots functional.
- **State separation**: `GameState` owns persistent choices/results; `RaceWorld` owns one race; `Main` owns screen flow; each gameplay system owns a narrow behavior.
- **Proxy autoloads**: `AGState` and `AGAudio` resolve `/root/GameState` and `/root/AudioDirector` at runtime, allowing script-only tests to parse and run without instantiated autoloads.

## Directory map

- `project.godot`, `icon.svg` — Godot 4.2 project settings and icon.
- `autoload/` — `game_state.gd`, `audio_director.gd`.
- `scenes/` — `main.tscn`, `race_world.tscn`, and `ui/*.tscn` screen roots.
- `scripts/main.gd` — menu/race/results/hospital/pause/settings transitions.
- `scripts/race_world.gd` — assembles one complete race and exposes benchmark/test state.
- `scripts/camera_rig.gd` — cockpit/chase/replay cameras.
- `scripts/visual/` — palette, mesh factory, bike/rider/vehicle/building factories, view/animation scripts.
- `scripts/world/` — road path, continuous road builder, environment builder.
- `scripts/ui/` — UI kit, HUD dashboard, menus, selection, settings, pause, results, hospital.
- `systems/physics/` — input provider and motorcycle controller.
- `systems/racing/` — rival brain and race manager.
- `systems/traffic/` — traffic vehicle and traffic system.
- `systems/police/` — pursuit/interception system.
- `assets/data/` — JSON roster, bike stats, traffic stats and settings defaults.
- `assets/textures/`, `assets/ui/`, `assets/audio/` — generated PNG/WAV assets.
- `tests/` — static audit and headless smoke test.
- `tools/` — deterministic asset generator, capture/compare/run-tests scripts.
- `docs/` — plan, visual analysis, benchmark, architecture, test report and user references.

## Data flow

```
Main
 ├── GameState (autoload): riders, bikes, settings, unlocks, results
 ├── AudioDirector (autoload): generated engine/ambience/siren/SFX
 └── RaceWorld
      ├── RoadBuilder / EnvironmentBuilder
      ├── Player MotorcycleController
      │    ├── BikeView (wheel/steer/lean/slide)
      │    ├── RiderView (body/head/limbs/fall)
      │    └── Hitbox Area3D
      ├── 5 Rival MotorcycleControllers + RivalBrains
      ├── TrafficSystem -> TrafficVehicles
      ├── PoliceSystem
      ├── RaceManager (countdown, position, time, finish/crash)
      ├── HUD (live gauges and warnings)
      └── CameraRig (cockpit/chase/replay)
```

## Collision and crash model

- Road collision is a trimesh shape generated from the visible road mesh; barrier boxes approximate curved guardrails.
- Player hitbox is an `Area3D` on layer 1/mask 2; traffic and rival hitboxes are monitorable areas on layer 2.
- Relative speed and vehicle mass determine minor, moderate or severe impact.
- Minor/moderate impacts slow the bike, add wobble and camera shake; a high-speed moderate impact may fall.
- Severe impacts detach the rider, slide the bike, start a replay camera, stop the race, and transition to the hospital/defeat result exactly once.

## AI and traffic

- `RivalBrain` scans traffic/rivals ahead, scores lane clearance, chooses a target lane and steers toward it. Personality comes from roster `aggression`/`skill` and difficulty.
- `TrafficSystem` maintains a bounded pool of vehicles, type-specific speeds and lane-change probabilities, following distance, safe spawn distance ahead, and despawning behind the player.
- `PoliceSystem` escalates from sustained illegal speed, near misses, crashes or race-progress thresholds. Police spawn far ahead and drive normally; scripted interceptions create obstruction without teleporting onto the player.

## Rendering and performance

- `gl_compatibility` OpenGL 3 renderer, no MSAA, one directional light, coarse textures and shared materials.
- `MultiMeshInstance3D` is used for barriers and streetlights.
- Quality setting scales building/vegetation/cloud density; resolution scale uses the viewport's 3D scaling property when available; shadows toggle global directional lights.
- HUD is a single `CanvasLayer` with one custom `Control` painter, avoiding hundreds of gauge nodes.
- Traffic is pooled with a configurable spawn limit and conservative despawn radius.

## Procedural animation

See `assets/animations/PROCEDURAL.md`. Wheels, lean, steering, suspension, rider posture, falling, sliding, police beacons and cameras are per-frame transforms driven by live state rather than imported animation clips.
