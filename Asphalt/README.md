# THE ASPHALT GROOMS — عرسان الأسفلت

**The Ring Road Waits for No One.**

A self-contained, fully 3D retro Egyptian motorcycle street-racing game for **Godot 4.2.2**. The visual target is a late-1990s / early-2000s cockpit racer: low-poly geometry, coarse textures, dusty blue sky, dark asphalt, sandy brick Cairo/Giza roadsides, and a large physical dashboard.

> Project folder in Google Drive: `Asphalt` — <https://drive.google.com/drive/folders/1ruZcKvS1isgF-z4h_mviCuasZI7-a4Oz>

## Launch

1. Install or open **Godot Engine 4.2.2-stable**.
2. Open `project.godot` from the `Asphalt/` folder.
3. Press **Play** (F5), or run from a terminal:
   ```bash
   godot --path /path/to/Asphalt
   ```
4. Recommended display: 1280 × 720, OpenGL 3.3-compatible graphics. The project uses the `gl_compatibility` renderer.

The game does not need an import step for external 3D models: all meshes, textures, UI art and placeholder audio are generated from source scripts and included data.

## Controls

| Action | Keyboard | Optional gamepad |
|---|---|---|
| Accelerate | `W` / `↑` | right trigger |
| Brake / reverse creep | `S` / `↓` | left trigger |
| Steer left / right | `A` / `D` or `←` / `→` | left stick X |
| Handbrake / special | `Space` | A / button 0 |
| Limited boost | `Shift` | B / button 1 |
| Toggle camera | `C` | — |
| Pause | `Esc` | Start |
| Menu navigation | mouse / keyboard | — |

## Game loop

Main Menu → Rider Selection → Motorcycle Selection → Settings → Countdown → Race → Victory / Defeat → Results or Hospital → Retry / Main Menu.

- Eight original street riders with distinct hair, skin tones, clothing, accessories and riding personalities.
- Six motorcycles with different frames, wheels, fairings, handlebars, exhausts, colors and performance.
- Five rivals with lane choice, overtaking, braking and distinct aggression/skill.
- Dynamic traffic: cars, Cairo taxis, microbuses, minibuses, trucks and trailers with type-specific speeds and following behavior.
- Egyptian police pursuit with escalation, sirens and scripted interception roadblocks.
- Minor/moderate/severe crashes with non-graphic falling/sliding, replay camera and a humorous hospital sequence.
- Cockpit, chase and crash-replay cameras; live speed/RPM/gear/boost/position/time/progress dashboard.

## Settings

Quality (Low/Medium/High), 3D resolution scale, shadows, traffic density, rival difficulty, master volume, default camera and FPS display. Resolution and shadows apply immediately; scenery density applies to the next race. Settings, selection, wins and the Golden Falcon unlock are saved to `user://asphalt_grooms_save.json`.

## Project structure

```
Asphalt/
  project.godot, icon.svg, README.md
  autoload/          GameState, AudioDirector
  scenes/            main, race world and UI scene roots
  scripts/           main/race/camera, UI, visual and world modules
  systems/           physics, racing, traffic, police
  assets/data/       rider/bike/traffic/settings JSON
  assets/textures/   coarse procedural PNGs and Arabic signs
  assets/ui/         title, menu art, portraits, hospital/results art
  assets/audio/      procedural WAV placeholders
  docs/              plan, visual analysis, benchmark, architecture, test report
  tests/             static audit and headless gameplay smoke test
  tools/             asset generator, capture, comparison and test runners
```

See `docs/03-architecture.md` for the full data flow.

## Regenerating assets

```bash
python3 -m pip install -r tools/requirements.txt
python3 tools/generate_assets.py
```

`tools/generate_assets.py` deterministically writes all PNG textures, portraits, UI art, JSON data and WAV audio. It does not download third-party game assets. Arabic title/sign text is rasterized with DejaVu Sans; see `assets/LICENSE-ASSETS.txt`.

## Final package

A distributable source archive is created at `dist/THE_ASPALT_GROOMS_Godot_4.2.2.zip` and uploaded to the Google Drive `Asphalt` folder linked above. The archive excludes sandbox-only Godot/Xvfb/Mesa runtime bundles and temporary debug captures; it includes all game source, generated assets, docs, screenshots, metrics and test reports.

## Rendering strategy review

A separate A/B review was added after the full-3D project was completed. It
compares the existing full-3D benchmark with an isolated Hybrid 2.5D prototype
that uses scanline road projection, original low-resolution rider/traffic/background
sprites, a fixed live cockpit overlay, and road-relative collision/gameplay logic.

See `docs/05-rendering-strategy-review.md` for the decision and
`docs/06-hybrid-2p5d-benchmark.md` for the experiment, screenshots and test
results. **Recommendation: use Approach C — Hybrid 2.5D as the future visual
architecture, while preserving the current 3D project and its systems.** The
experiment lives in `experiments/hybrid_2p5d/` and does not rewrite the existing
gameplay systems.

## Tests and screenshots

```bash
GODOT=/path/to/godot-4.2.2 ./tools/run_tests.sh
```

This runs the static resource audit, Godot import/parse checks and a headless gameplay smoke test. Reports are written to `tests/reports/`.

To capture actual in-engine cameras on a normal desktop with a GPU, open the project in Godot and use the game normally. For this sandbox's software-rendering workflow:

```bash
./tools/capture_benchmark.sh
/home/user/Videos-motion/.venv/bin/python tools/compare_reference.py \
  --reference docs/reference/reference_01.png \
  --capture screenshots/benchmark_cockpit.png \
  --label cockpit --report docs/metrics_cockpit.json \
  --review screenshots/review_cockpit.png
```

`capture_benchmark.sh` expects Xvfb + Mesa llvmpipe. The CI-staged portable runtime parts used in this sandbox are build/test tooling, not game assets, and are excluded from the final game ZIP.

## Known limitations

- This is an original low-poly interpretation of the supplied screenshots, not an exact asset-for-asset remake.
- Generated WAVs are clearly documented placeholders; no recorded engine/music library is included.
- Arabic UI text is rasterized in images; functional labels use Latin text for font-shaping reliability.
- No exported desktop/web binary is included; launch the Godot project directly.
- Controller support covers common axes/buttons through the input provider; exotic pads may need remapping.
- Real-GPU 30 FPS is a target, not a guaranteed measurement on every machine. See `docs/04-test-report.md` for honest, measured results in this environment.
- No network multiplayer, cloud saves, voice acting, licensed radio or external high-detail model pack.
