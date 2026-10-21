# VP-0 Art Bible — "Pixel Pirates: Cinematic HD-2D"
Status: **Phase 1 (proposal + in-engine prototypes). Nothing here replaces the game's current art yet.** Review it, then approve / change the points in section 2 before any mass production.
Companion documents: `VP0_TECH_ART_SPEC.md` (numbers and conventions), `VP0_ASSET_INVENTORY.md` (what exists, what is needed, in what order), `VP0_PERFORMANCE_AND_RELEASES.md` (low-end strategy, feasible/risky techniques, release sequence). Screenshots: `docs/vp0_shots/`.

## 0. Honest status — read first
* **Your four reference images are not available to me** (they are not in the Drive folder, the repo or the sandbox). I could only measure the two references from module A3 (town square and forest camp; numbers in `docs/A3_ART_BIBLE.md` and `art_bible/ref_measure.json`). Everything below that mentions "the references" means those two plus your written description of all four (cinematic ocean and islands; detailed ship with deck equipment; richly built HD-2D town; lush nature scene with expressive characters). **Please re-upload the four images** and I will re-check the palette, density and proportions against them before the first production release. Nothing is copied from them; they are targets only.
* **Everything was rendered in Godot 4.7.2 (web build, Compatibility/OpenGL ES 3.0) through a software GPU (SwiftShader) in a headless browser.** That proves the shaders compile and look as shown. It does **not** prove frame rate, and it was **not** run on Windows or on the HD 3000. No performance number in these documents is measured on your hardware; the ones I give are labelled *estimate*.
* The prototypes are **prototype code** in `game/prototypes/vp0/`. They do not touch the game scenes, collision, economy, sailing, fishing, dialogue or the r7 map. The regression suite is run at the end of this release (result in the final report).

## 1. The look in one paragraph
A small, warm, slightly melancholy diorama. **Tiny, hand-readable pixel sprites standing upright in a real 3D-lit stage**: low sun with long soft violet shadows, deep warm shadows (never black), glowing windows and lanterns, turquoise lagoons that fade to deep teal, hard pixel edges in the focus band and a gentle tilt-shift blur above and below it. Cinematic through *light, colour and depth*, not through detail overload. One pixel grid, one palette family, one light direction, one camera — so every asset looks like it came from the same team.

## 2. Pillars (the rules the art team follows)
1. **One pixel.** Every visible texel in the focus plane is exactly one art pixel (1/24 m on deck and land). Nothing is ever drawn at a different pixel size, rotated by non-90° angles, or scaled at runtime (sprites are pre-rotated: 8 or 16 facings).
2. **Upright sprites on an oblique ground.** Ground, water and walls are lit surfaces; things that stand (props, plants, people, buildings, masts) are baked sprites with an integrated cel shading, outline and contact shadow.
3. **Readable silhouettes first.** Each asset must be recognisable as a filled black shape at 1× on a 640×360 screen. 1-px outline in the darkest neighbouring ramp step; no outline between inner parts unless the part must read.
4. **Disciplined palettes.** 32 ramps × 5 steps (22 from A3 + 10 added by VP-0: `rope_hemp, brass, plaster, terracotta, thatch, rock_basalt, foam, wood_pale, tar, sea_mid`). Shadows drift cool/purple, highlights drift warm/yellow. No `#000000`, no `#ffffff`.
5. **One light.** A warm key light from the upper left, baked into sprites as 4 cel bands (the same direction as the runtime sun at the default time of day). Runtime light only *tints* sprites (multiply) — it never re-shades them. Time of day = tint + shadow direction + halo strength + grade.
6. **Fire is self-lit.** Pixels of the `fire` ramp (steps 2–4) ignore the tint: lanterns, windows and embers glow at night with no extra texture. By day the same pixels are drawn as dull sky-glass (lamps are off), so a building does not "glow" at noon.
7. **Depth by layers, not by effects.** Foreground (blurred), focus band (sharp, y ≈ 0.55 of the screen), background (blurred, hazier, cooler). Atmosphere is a colour mix toward the look's fog colour, not volumetric fog.
8. **Water is a graphic pattern, not a simulation.** 7 banded depth colours with ordered dithering, contour waves, rare 1-px glints, sand showing through the shallows, a foam rim, a retreating swash line, and a ship wake/hull foam. All computed from one distance-field texture; no reflection render target.
9. **Scale is law.** Human 1.75 m = 42 px; a 22 m sloop = 528 px long; a door 1.9 m = 46 px; a palm ≈ 8 m = 190 px. Open sea uses a *derived* tier (8 px/m) baked from the same models, so the ship is the same ship at every distance.
10. **Gameplay geometry wins.** Visual assets are fitted to `ship_layout.gd` (hull table, hatch, winch, helm, barrels, cabin) and to the r7 map, never the other way round. Where a prop would need new collision (the two deck cannons) it is shown in the prototype and flagged, not silently added to the game.

## 3. Decisions I need from you
| # | Decision | My proposal | Why |
|---|---|---|---|
| D-1 | **Camera: orthogonal instead of A3's perspective (FOV 22°)** | Orthogonal, 15 m visible height at 24 px/m (8 px/m at sea → 45 m), pitch 37° land / 48° sea | Exact 1:1 sprite pixels, no shimmer, free depth-bias for sprites, simpler shaders. Perspective with FOV 22° is nearly orthogonal anyway; the references read as orthogonal. Reversible: the sprite shader is the only place that depends on it. |
| D-2 | Internal render size | **640×360 SubViewport, integer-scaled** to the window (×2 at 720p, ×3 at 1080p; at 1366×876 the project must use `window/stretch/scale_mode = "integer"` or accept ×1.067 blur). | One art pixel = a whole number of screen pixels; 4× fewer shaded pixels than rendering at 1280×720; this is what makes the HD 3000 plausible. |
| D-3 | Production method for ships, buildings and props | **Voxel-model → baked multi-facing sprites** (tooling in `tools/vp0`), hand-painted touch-up on top for hero assets and all characters | One 3D source gives every heading, every LOD tier (24 / 12 / 8 px/m) and consistent light. Pure hand-pixelling of 16 headings × 3 tiers × damage states is not sustainable. Characters stay hand-painted frames: bakes lack expression. |
| D-4 | Colour caps | Props 32 (A3), **structures/buildings up to 40**, ships 40, characters 48 | The baked house reaches 36 colours with a 3-step roof and shutters; the A3 cap of 32 forces ugly banding. |
| D-5 | Ship exploration at 24 px/m, ship at sea at 8 px/m | Two baked tiers, one hull model | See tech spec §3. The old 3.6 px/m ground and the 112×112 ship sprite are the main reason the current game looks lower quality than its sprites. |
| D-6 | Window/UI scaling | Integer scaling; offer "smooth" as an option | See D-2. |

## 4. What the prototypes show (screenshots in `docs/vp0_shots/`)
Open them in this order. "Before" are the CP-2A shots from the current game.
| Shot | Shows | File |
|---|---|---|
| Before (current deck, 3.6 px/m ground vs 24 px/m sprites) | the mismatch we are fixing | `before_d00_helm_direct.png`, `before_d03_barrels.png`, `before_d05_winch.png` |
| **A. Ship deck** day / golden / night | hull, deck planking, cabin with windows, mast + crow's nest, main sail and jib, rigging lines, helm, winch, hatch, barrels, crates, two deck cannons (new, see §4.1), lantern, mannequins for scale | `deck_day.png`, `deck_golden.png`, `deck_night.png` |
| **B. Ocean** (at sea tier 8 px/m) day / golden / night | banded water, contour waves, sand through shallows, shore foam, ship wake, island with LOD sprites | `sea_day.png`, `sea_golden.png`, `sea_night.png` |
| **C. Anvil Cay** harbour, street, beach | cobbled quay and plaza, three period buildings, lamp posts, bollards, a pier, the moored sloop, palms, rocks, wet sand, shallows | `harbour_day/golden/night.png`, `street_day/dusk.png`, `beach_day/golden.png` |
| Dev-Lite | same scenes with the grade pass off (no blur, no bloom, no vignette) | `deck_lite.png`, `sea_lite.png` |
### 4.1 Things the prototype adds that need a decision in the game
* **Two deck cannons** at (−0.2, −2.5) and (−0.4, +2.5): not in `ship_layout.gd` (a visual-only addition; their positions were not checked against walkable geometry). Making them real means two new obstacles plus a walkability re-test (VP-3).
* **Cabin:** the cabin sprite is centred in the layout's cabin footprint (`CABIN_U0/U1` = −10.0…−5.4, `CABIN_V` = 2.2); its door was not matched to the layout's door, which must happen in VP-3. It is a sprite, not walls you can fade; the game's "fade the roof when you enter" needs a second baked frame set (roof off). Listed in VP-3.

## 5. Visual language per subject
### Ships
Hull = textured meshes shaped from the existing hull table (strakes, flared belly, wale, rail cap); sails = billowing meshes with a canvas texture and a back-light factor; mast with crow's nest, boom, bowsprit and shrouds with ratlines (1-px lines). Equipment = baked sprites. A ship at 24 px/m is the hero asset of the game; budget most of the hand-painting here.
### Ocean
Band colours (deep → shallow): `#123a4f #1d5f73 #238a8c #3d8c92 #5cb8a5 #9be0c0 #dffbe0`; foam `#7fc4bc #bfe8d8 #e6faec #fffff0`. Depth is a *signed distance to shore* texture (−4…+20 m, 4 px/m at the cay, 3 px/m at sea). The wave pattern is two moving noise fields turned into 1-px contour lines — the same trick as the references' water.
### Terrain and vegetation
Ground = 48-px (2 m) tiles in an atlas (4 variants per row: dry sand, wet sand, grass, dirt, cobble, slab, shallow bed, rock floor). The cell map is displaced by noise so borders are organic. Everything that stands is a sprite. Palms/rocks/bushes have a 8 px/m LOD for the sea tier.
### Architecture
Timber-frame plaster houses with terracotta/slate roofs, thatched warehouses, cobbled quays. Windows are fire-ramp glass (see pillar 6). Large roofs need a hand-painted detail pass (the warehouse roof in the prototype is flat noise).
### Characters (not part of VP-0)
The mannequin is a **scale reference only**. Production characters: 48×64 cells, 42-px body, 4 directions, hand-painted, expressive faces/hands (the fourth reference). Needs its own art-direction review before production.

## 6. Techniques — feasible / risky / unsuitable
See `VP0_PERFORMANCE_AND_RELEASES.md` §3 for the full table with cost estimates.

## 7. Known weaknesses of the prototypes (so you do not have to hunt for them)
* Hull sprite at sea: the sail has vertical streaks (seam sampling of the voxel canvas). Needs a sail-specific bake.
* The warehouse roof, the terrace top and the sails are texture-noise flats compared with the references' painted detail. They need the hand pass (see inventory "hero" flags).
* Fishing net sprite reads as a leopard-print blob; to be redrawn.
* Characters are mannequins. People walking, animation and faces are not in this phase.
* The wake: ladder-like cross pattern at close range; at sea tier it renders as two long straight streaks (`sea_golden.png`) rather than a V that widens and fades. Tuning pending.
* In `harbour_*` shots the moored ship is large and in front of the quay (camera choice); the framing needs a proper composition pass.
* The distant sloop in the sea shots is blurred by the tilt-shift band (intended) but reads as a smear; a distance-dependent sharper LOD hull is needed.
* No weather, no rain, no fog banks, no clouds, no god-rays in the prototypes (they exist in H2D-0.3 and must be re-based on the new camera in VP-4).
