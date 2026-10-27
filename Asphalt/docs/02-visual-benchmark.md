# Stage 2 — Visual benchmark, comparison and refinement

**Status: complete with verified in-engine captures.** Exact visual fidelity to the three supplied screenshots is **not** claimed; the result is an original, playable low-poly interpretation. This report documents two real capture iterations, the defects found, the fixes applied, and the measurable before/after differences.

## Benchmark scene

`RaceWorld.prepare_benchmark()` renders a real game world, not a mock-up:

- continuous Ring Road mesh with yellow center lines, dashed white lane lines, concrete/white bridge rails, sand shoulders and distant scenery;
- the same `AGBikeFactory` motorcycles used in gameplay, with functional wheel/steering/lean pivots;
- the eight-rider roster from `AGRiderFactory`;
- seven traffic body styles from `AGVehicleFactory`;
- dusty-blue procedural sky, coarse cloud quads, sandy hills, Egyptian brick buildings, Arabic signage, palms, streetlights and overpasses;
- cockpit first-person camera with the live retro dashboard, plus third-person chase and crash-replay cameras.

The benchmark freezes physics but keeps the HUD, world and real camera. It composes an urban cockpit frame around z = −520 m and a bridge/coastal chase frame around z = −2800 m. Dashboard values are real benchmark player state (187 km/h, gear 3, RPM 5.6k, boost 72%, position 2/6), not static decoration.

## Capture evidence

`tools/capture_benchmark.sh` starts Xvfb and runs the official Godot 4.2.2 editor with:

- `gl_compatibility` rendering method,
- OpenGL 3.3 Core Profile, Mesa 23.2.1 llvmpipe software renderer,
- 1280 × 720 viewport,
- dummy audio driver.

`tools/capture_benchmark.gd` waits for frames and calls `ViewportTexture.get_image()`. `screenshots/capture_report.json` records:

```json
{
  "engine": "4.2.2-stable (official)",
  "rendering_method": "gl_compatibility",
  "viewport": [1280, 720],
  "captures": {"cockpit": true, "chase": true, "replay": true}
}
```

Final images:

- `screenshots/benchmark_cockpit.png` — cockpit first-person.
- `screenshots/benchmark_chase.png` — third-person chase on the white-rail bridge section.
- `screenshots/benchmark_replay.png` — crash-replay orbit showing the motorcycle and rider.
- `screenshots/debug_topdown.png` — top-down road-surface/collision diagnostic.

The first iteration is preserved as `screenshots/benchmark_v1_*.png`, with JSON metrics in `docs/metrics_v1_*.json` and review images in `screenshots/review_v1_*.png`.

## Comparison method

`tools/compare_reference.py` compares a capture with a supplied reference at 1280 × 720 using:

- mean/median RGB and luminance in sky, horizon, road and dashboard regions;
- edge density as a coarse proxy for geometry/texture complexity;
- quantized dominant palettes;
- a float, sliding-window SSIM-like local structure score on 320 × 180 luminance.

The first version of the structure metric had an 8-bit clipping bug and produced a meaningless −1; it was corrected before any conclusions were drawn. Numeric similarity remains a review aid, not proof of artistic fidelity.

## Iteration 1 findings and fixes

The first cockpit capture (`benchmark_v1_cockpit.png`) had three severe defects:

1. **Missing dashboard** — the HUD painter used anchors without offsets, leaving `size.y = 0`; the dashboard collapsed into a few labels at the top-left.
   - Fix: use `set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)` for all full-screen UI controls.
2. **Road buried / no asphalt in chase** — the flat desert ground plane was above parts of the elevated road, and the road material was being culled/overwritten.
   - Fix: lower the ground plane to y = −3, add road-level sandy shoulder ribbons, make road/ground materials unshaded with measured colors, disable culling on the road mesh, and raise marking render priority.
3. **Oversized dark-blue panels** — diagnosed with hide-tests and a top-down render. They were traffic-vehicle window panels left at the benchmark camera's own z because `prepare_benchmark()` only repositioned the first nine vehicles.
   - Fix: reposition **all** traffic vehicles at least 90 m ahead of the benchmark camera; make 3D signs opaque and smaller; fix all initial traffic spawning to keep a 90 m clear bubble around the player.

Additional refinement: measured road color `#585260`, opaque Arabic sign textures, smaller shop signs, unshaded white bridge rails, calmer sun/ambient, and a corrected full-rect HUD.

## Measured before/after results

| Metric | v1 cockpit | final cockpit | v1 bridge | final bridge |
|---|---:|---:|---:|---:|
| Global mean RGB distance | 41.23 | **22.13** | 125.05 | **16.78** |
| Mean region RGB distance | 57.87 | **52.17** | 162.55 | **62.98** |
| Structure score (higher = closer) | 0.3199 | 0.2801 | 0.3575 | **0.3654** |

Final region RGB distances:

| Region | final cockpit vs ref 1 | final bridge vs ref 3 |
|---|---:|---:|
| Sky | 35.10 | 90.78 |
| Horizon | 112.07 | 125.98 |
| Road | **18.53** | **24.81** |
| Dashboard | 42.98 | **10.35** |

The replay frame compared against reference 2 produced global RGB distance 36.59, mean region distance 44.47 and structure score 0.2165 (`docs/metrics_final_replay.json`).

Interpretation: the very large global color-distance improvements confirm that fixing the missing dashboard, buried road and dark-blue traffic panels moved the scene much closer to the references. The SSIM-like structure score is coarse and can decrease when correct large shapes are added at different positions; it is reported honestly rather than optimized artificially. Horizon-region distances remain high because the references contain denser, taller, more varied roadside buildings and clouds than our deliberately low-poly procedural scene.

## Structured visual review checklist

1. **Sky** — bright dusty blue with a few coarse white cloud shapes; yes, though cloud distribution is sparser than reference 1.
2. **Road** — dark muted purple-gray asphalt with prominent double-yellow and dashed-white markings and one-point perspective; yes after refinement.
3. **Sand / buildings / hills** — sandy shoulders, brick apartment blocks, Arabic signs, palms, streetlights and distant hills are visible on both sides; yes, but less dense than the references.
4. **Motorcycles / riders** — chase and replay frames show a readable low-poly rider, wheels, frame, tank, seat, handlebars and exhaust; cockpit view hides the player bike by design but shows rivals/traffic ahead.
5. **Dashboard** — physical dark cowl occupies roughly the bottom quarter, with two analog gauges, gear, engine strip and live indicators; yes.
6. **Textures / lighting** — coarse texels, flat colors, simple warm directional light and short shadows; yes.
7. **Avoids wrong styles** — no photorealism, modern glossy cars, anime proportions, generic Western landmarks, or flat 2D pixel-art substitute; yes.
8. **Remaining differences** — horizon/building density, cloud count/placement, exact dashboard silhouette, exact reference traffic/rider placement, and the slightly different road/sand hue. These are documented rather than hidden.

## Decision

The benchmark is **approved as a playable low-poly visual foundation** for the rest of the production pipeline. It is not an exact recreation of the supplied screenshots. The later stages reuse the same road, model factories, materials, HUD and cameras rather than replacing them with unrelated assets.
