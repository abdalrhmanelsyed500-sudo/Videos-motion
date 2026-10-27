# Stage 1 — Reference analysis and visual target

## Source material

The three supplied images are preserved in `docs/reference/`:

1. `reference_01.png` — 1672 × 941: first-person urban Ring Road race with two rival motorcycles.
2. `reference_02.png` — 1599 × 984: first-person non-graphic crash and fallen rider.
3. `reference_03.jpeg` — 650 × 400: older low-resolution bridge/desert race with a rider ahead.

They are the primary visual specification. The target is a playable, fully 3D game whose composition, color, geometry density and HUD recall late-1990s / early-2000s motorcycle racing games — not photorealism, modern mobile-game graphics, anime proportions or flat 2D pixel art.

## Measured composition

| Region | Reference 1 / 2 approximate frame coverage | Practical in-game target |
|---|---|---|
| Sky | top 0–25%; bright dusty blue with coarse white clouds | top 0–28% at level camera pitch |
| Horizon / buildings / hills | about 22–45% | 24–44% |
| Road | about 38–78%, converging near center | 39–80% |
| Dashboard | lower 22–28%, irregular dark cowl | lower 24%, hazards visible above it |
| Rival rider/bike at mid-distance | roughly 10–14% frame height | 9–15% at 20–35 m |
| Side buildings | approach within 10–20% of either screen edge at the bottom | modular 3–5 storey blocks on both sides |

Reference 1 uses a wide road with a pair of yellow center lines, dashed white lane lines, low concrete side barriers, sandy brick apartment blocks, small shops with striped awnings, palms, broadleaf trees, streetlights, dusty hills and distant traffic. Reference 3 adds white bridge guardrails, a curve and green/sandy desert hills.

## Quantitative image observations

Measured with Pillow/NumPy on the supplied files:

- Reference 1 mean RGB: `(101.8, 96.6, 106.5)`, median `(89, 83, 95)`.
- Reference 1 sky-region median: `(125, 158, 252)` ≈ `#7D9EFC` — a dusty periwinkle blue, not pure cyan.
- Reference 1 road-region median: `(88, 82, 96)` ≈ `#585260` — muted blue-gray-purple asphalt.
- Reference 1 dashboard-region median: `(75, 72, 60)` ≈ `#4B483C`; the darkest cowl pixels are near `#181818`.
- Dominant quantized colors in references 1/2: `(72,72,96)` road/shadow purple-gray, `(72,72,72)` near-black dashboard, `(96/120,144,240)` blue sky, `(168,144,120)` sand/brick, `(24,24,24)` black tires/interiors.
- Reference 3 sky-region median: `(154, 175, 255)`; its lower resolution and compression reinforce coarse texels and hard edges.

Implemented palette in `scripts/visual/palette.gd`:

- sky top `#5F8BEB`, horizon `#7D9EFC`, cloud `#F2F5F5`;
- asphalt `#4B4858` with darker `#3A3847`;
- yellow markings `#D9B51F`, aged white `#D8D9D1`;
- concrete `#B4A992`, sand `#B9996D` / `#D6B98B`;
- brick facades `#A47F72` / `#8B665C`, recessed windows `#30272E`;
- dashboard `#272326` / `#403A38`, gauge face `#DDD8C5`, needle `#CE3C31`;
- rival clothing magenta `#A72C86`, red `#C32228`, denim `#37568A`.

## Shape language and rendering

- Low-poly meshes with hard edges and clear silhouettes. Buildings/barriers use boxes, but motorcycles, riders, wheels, handlebars, streetlights and signs have recognizable modeled profiles.
- `StandardMaterial3D` albedo colors, high roughness, no metallic gloss, coarse 64–256 px procedural textures and nearest filtering where appropriate.
- Bright ambient light plus one warm directional sun; short, dark, readable shadows.
- Strong linear perspective and a stable horizon. No depth of field, bloom, SSAO or modern post-processing.
- Repeated scenery uses shared meshes/materials and `MultiMeshInstance3D` for barriers and streetlights.
- 1280 × 720 internal target with configurable 0.75× and 0.6× scale.

## Dashboard target

The dashboard is a physical instrument cluster with an irregular dark cowl occupying the bottom quarter of frame: two analog dials with ticks/numerals/moving needles (speed and RPM), a central gear number, engine/heat strip, green/red indicators, position/time/progress and a police/crash warning strip. Needles and numbers come from `MotorcycleController` state; no decorative values are disconnected from gameplay.

## Explicit visual exclusions

No photorealistic PBR, glass towers, contemporary car bodies, generic Western environment, modern flat HUD, bloom, motion blur, lens flare, glossy wet roads, anime/Fortnite proportions or 2D pixel-art substitution. Crash presentation remains non-graphic.

## Verification method

`tools/compare_reference.py` compares an actual in-engine camera capture with `reference_01.png` and `reference_03.jpeg` at 1280 × 720 using region-level mean colors, luminance, edge density, quantized palettes and a simple grayscale structure score. It writes JSON metrics and side-by-side review images. Numeric similarity does **not** prove artistic fidelity; the structured human-readable review is recorded in `docs/02-visual-benchmark.md` after inspecting the rendered screenshots.
