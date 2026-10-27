# Stage 1 — Reference analysis and visual target

## Source material

The three supplied images are preserved in `docs/reference/`:

1. `reference_01.png` — 1672 × 941, first-person urban Ring Road race with two rival motorcycles.
2. `reference_02.png` — 1599 × 984, first-person non-graphic crash and fallen rider.
3. `reference_03.jpeg` — 650 × 400, older low-resolution bridge/desert race with a rider directly ahead.

They are the primary visual specification. The target is a playable, fully 3D game whose composition, color, geometry density, and HUD recall late-1990s / early-2000s motorcycle racing games — not a photorealistic modern racer and not a 2D pixel-art imitation.

## Measured composition

| Region | Reference 1 / 2 approximate frame coverage | Practical in-game target |
|---|---|---|
| Sky | top 0–25%; bright blue with a few coarse white clouds | top 0–28% at level camera pitch |
| Horizon / buildings / hills | about 22–45% | 24–44% |
| Road | about 38–78%, converging to a single vanishing point near the center | 39–80% |
| Dashboard | lower 22–28%, with an irregular dark cowl silhouette | lower 24%, with hazard sightline kept clear above it |
| Rival rider/bike at mid-distance | roughly 10–14% frame height, placed just above dashboard | 9–15% at 20–35 m |
| Side buildings | approach within 10–20% of either screen edge at the bottom | modular 3–5 storey blocks on both sides |

Reference 1 uses a wide road with a pair of yellow center lines, dashed white lane lines, low concrete side barriers, sandy brick apartment blocks, small shops with striped awnings, palms, broadleaf trees, streetlights, a dusty hill skyline, and distant moving traffic. Reference 3 adds white bridge guardrails, a curve, and green/sandy desert hills.

## Palette

The palette is sampled from the references and implemented in `assets/materials/palette.tres`:

- sky: saturated but slightly dusty blue, approximately `#48A6E8`–`#66B8F2`.
- cloud: near-white `#F2F5F5`, with hard, low-resolution edges.
- asphalt: muted blue-gray-purple `#49474F`–`#56545B`; never glossy black.
- yellow markings: `#D5B11A`–`#E7CA2E`.
- white markings: `#D8D9D1` (slightly aged).
- concrete barriers: `#AAA394`–`#C6B9A5`.
- sand / hills / unfinished buildings: `#A98961`, `#BEA078`, `#D6B98B`.
- brick facade: `#A47F72`, `#BD9E86`, `#8B665C`, with dark recessed windows `#33272B`.
- dashboard: charcoal `#252224`–`#3A3433`; gauge faces aged white `#DDD8C5`; needle red-orange `#CF3B30`.
- rival clothing: strong magenta `#A72C86`, red `#C32228`, blue jeans `#344C78`; natural tan skin tones.

## Shape language and rendering

- Low-poly meshes with hard edges and clear silhouettes. Boxes are allowed for buildings and barriers, but motorcycles, riders, wheels, handlebars, streetlights, and signs must have recognizable modeled profiles.
- Simple `SpatialMaterial` / `StandardMaterial3D` albedo colors, low specular, no PBR glossiness, no screen-space reflections.
- Coarse procedural textures (64–256 px), nearest or low-quality filtering where appropriate; visible texel edges are desirable.
- Bright ambient light plus one warm directional sun. Short, dark, clearly readable blob/shadow shapes.
- Strong linear perspective and a stable horizon. No depth-of-field or modern post-processing bloom.
- 1280 × 720 internal rendering target with configurable 0.75× and 0.6× scale for slower hardware.
- Repeated scenery uses shared meshes/materials and `MultiMeshInstance3D` where practical.

## Dashboard target

The dashboard is a physical 3D/2D instrument cluster with:

- an irregular dark cowl occupying the bottom quarter of the frame;
- two large analog dials with ticks, numerals and moving needles (speed left, RPM right);
- a central gear number from the actual gear state;
- an engine/heat strip with green–yellow–red sections;
- green and red corner indicator blocks;
- race position, time and distance as small retro overlays;
- a crash/police warning strip.

All numbers and needles come from `MotorcycleController` state; no decorative values are disconnected from gameplay.

## Explicit visual exclusions

No photorealistic PBR, glass towers, contemporary car bodies, anime proportions, generic US/European signage, modern flat HUD, bloom, motion blur, lens flare, glossy wet roads, or excessively detailed foliage. Crash presentation must remain non-graphic.

## Verification method

The visual benchmark is evaluated with `tools/compare_reference.py`, which compares an actual in-engine camera capture with `reference_01.png` at the same resolution using region-level mean colors, luminance, edge density, color quantization, and structural similarity of downscaled luminance. It also writes a side-by-side review image. Numeric similarity does **not** prove artistic fidelity; a structured human-readable review is recorded in `docs/02-visual-benchmark.md` after inspecting the rendered screenshot.
