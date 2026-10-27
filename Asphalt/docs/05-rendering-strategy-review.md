# Rendering strategy review — full 3D vs 2.5D vs hybrid

**Decision: adopt Approach C — Hybrid 2.5D for the final visual architecture.**

This review was requested after the existing full-3D prototype was found to be a poor stylistic match for the supplied references. The existing Godot project was **preserved**: the new work lives in `experiments/hybrid_2p5d/` and `scenes/experiments/`. Branch creation is not available in this session, so isolation is by folder/scene rather than by Git branch.

Exact visual fidelity is not claimed. The decision is based on actual 1280×720 screenshots, region metrics, and direct inspection of composition, silhouettes, dashboard, perspective and movement readability — not global color similarity alone.

## Reference diagnosis

The supplied images strongly resemble a late-1990s / early-2000s cockpit racer that uses:

- a fixed, physical dashboard overlay;
- sprite-scaled riders/bikes and traffic, or equivalent pre-rendered 2D assets;
- a mathematically projected road with strong one-point perspective;
- layered sky/hills/buildings/roadside art;
- coarse, low-resolution textures and hard edges;
- restrained or absent real-time lighting on sprites;
- stylized character silhouettes rather than visible low-poly 3D primitives.

The current full-3D prototype has real systems, but its visual language is different: modern low-poly boxes, sparse roadsides, 3D-lit geometry, and a HUD drawn on top of a 3D camera. Adding more 3D content would not by itself fix that mismatch.

## Approach comparison

| Criterion | A — Full 3D | B — 2.5D sprite-based | C — Hybrid 2.5D |
|---|---|---|---|
| Visual fidelity to references | Low–medium. Flexible camera, but characters/vehicles read as primitive 3D models; environment too open; cockpit is an overlay on a 3D world. | High **if** professionally drawn sprites/backgrounds are produced. Best potential for exact art style. | High. The benchmark reproduces dashboard mass, sprite-scaled riders, layered buildings/hills, coarse road texture and classic perspective. |
| Asset-production effort | High with available tools: detailed 3D models, rigs, animations, textures and lighting are needed to escape the primitive look. No Blender/model pack in sandbox. | Very high if all frames/backgrounds are hand-drawn; risk of inconsistent angles and pivots. | Moderate. One deterministic generator produced riding frames, crash frames, 6 traffic types × 3 angles, background layers and cockpit base. More frames can be added systematically. |
| Gameplay requirements | Strong: real 3D collisions, cameras, replay. | Risky if implemented as pure screen animation; road/collision must still be mathematical. | Strong: road-relative `z`/lane coordinates drive both projection and collision; rivals, traffic, police, crashes, hospital, finish and retry were implemented and tested. |
| Performance | Moderate; many meshes, lights, shadows and materials. | Very high if art is pre-rendered. | High; one `Control` draws a scanline road plus textured quads, with cheap state updates. |
| Maintainability | Good systems structure, but art iteration is slow. | Art-heavy; many bespoke drawings and alignment risks. | Good: sprite sheet metadata, shared pivots, deterministic generator, and a single projection function. |
| Curve/elevation support | Native. | Must be custom. | Implemented with `curve_offset()`, `hill_offset()` and `project()`. |
| Collision reliability | Native physics, but can be expensive. | Must be road-relative, not screen-space. | Verified: collision boxes derive from `z` and lane width; debug view shows the same coordinates used by sprites. |

## A/B benchmark evidence

Three 1280×720 compositions were rendered:

- `screenshots/ab_cockpit_reference_3d_hybrid.png`
- `screenshots/ab_movement_reference_3d_hybrid.png`
- `screenshots/ab_crash_reference_3d_hybrid.png`

Metrics from `tools/compare_reference.py`:

| Pair | Global RGB distance | Mean region RGB distance | Structure score |
|---|---:|---:|---:|
| 3D cockpit vs ref 1 | 22.13 | 52.17 | 0.2801 |
| Hybrid cockpit vs ref 1 | 23.62 | **35.04** | 0.2232 |
| 3D bridge vs ref 3 | 16.78 | 62.98 | 0.3654 |
| Hybrid moving vs ref 3 | **15.65** | **41.81** | 0.3046 |
| 3D crash vs ref 2 | **9.40** | **31.16** | 0.2085 |
| Hybrid crash vs ref 2 | 26.27 | 39.66 | 0.1742 |

Interpretation:

- Full 3D wins some global/structure numbers because its sky/road color blocks are closer in a few regions. That does **not** make its artwork closer: the rider/bike silhouettes, dashboard shape, traffic placement and building composition are still wrong for the target.
- Hybrid substantially improves cockpit and movement **region-level** color/layout distances and, more importantly, uses the same visual grammar as the references: fixed cockpit, layered backgrounds, sprite-scaled characters and a projected road.
- The hybrid crash frame is intentionally more graphic with large foreground fall/slide sprites; it matches the reference's crash *presentation* better but needs smaller foreground sprites for final production.
- The SSIM-like structure score is a coarse luminance metric and should not outrank direct art review.

## Recommendation

**Do not continue expanding the existing full-3D art pipeline as the final direction.**

Use **Approach C — Hybrid 2.5D** as the production rendering architecture:

1. Keep the existing 3D project as a systems/reference implementation and a fallback for logic.
2. Port the validated gameplay systems (race state, traffic, rivals, police, crash severity, hospital, menu flow) to a road-relative 2.5D world.
3. Replace 3D visual nodes with the hybrid renderer, sprite sheets, background layers and cockpit overlay.
4. Preserve road-relative `z`/lane coordinates as the single source of truth for projection, collision and AI.
5. Use the 3D scene only for optional debug views, screenshots, or a future “3D mode” — not as the main art direction.

This choice prioritizes the closest practical match to the supplied images while preserving real racing mechanics.

## Next implementation steps

1. Productionize `AGHybrid25DBenchmark` into modular scripts: `RoadRenderer`, `SpriteActor`, `HybridRaceWorld`, `HybridCockpit`, `HybridMenuFlow`.
2. Expand the rider sheet to 8 characters with distinct hair, jackets, jeans, shoes and accessories; add 5–7 riding angles and more crash frames.
3. Expand traffic sheets with more vehicle angles, brake lights, police sirens and damage states.
4. Increase background layer variants (urban Cairo/Giza blocks, unfinished buildings, palms, bridges, hills) and tie parallax to road curve/distance.
5. Integrate existing menu/rider/bike/settings/results/hospital screens with the hybrid race scene.
6. Move `RaceManager`, `TrafficSystem`, `PoliceSystem` and rival AI data to the road-relative coordinate system; keep collision boxes in JSON metadata.
7. Add real-GPU performance testing at 1280×720, then tune quality/resolution settings.
8. Re-run A/B visual review after each major art batch; never rely on a single global color metric.
