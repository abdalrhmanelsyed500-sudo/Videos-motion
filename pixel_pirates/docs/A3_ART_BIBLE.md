# MODULE A3 - Art Bible (from the two references)
Status: delivered. Machine-readable parts: `game/data/look/palette.json`, `game/data/look/look_profiles.json`. Evidence: `art_bible/ref_measure.json`, `art_bible/LOOK_LAB_REPORT.md`, `art_bible/looklab_stills/`.

## 0. What the references actually are
Both images are **HD-2D**: low-resolution pixel sprites standing upright in a real 3D scene with perspective, shadows, glow, depth blur and colour grading. I measured them (not eyeballed):
| measurement | ref A (town square) | ref B (forest camp) | meaning for us |
|---|---|---|---|
| sharpest band of screen height | 50-60% | 50-60% | tilt-shift focus band centred at **y = 0.55** |
| sharpness at top/bottom vs peak | 0.30 | 0.016 | blur strength is a per-mood dial: city mild, forest/sea strong |
| edge luminance / centre luminance | 0.13 | 0.33 | strong **vignette** |
| mean saturation | 0.44 | 0.64 | rich but not neon: target 0.45-0.65 |
| median luminance | 0.235 | 0.26 | **dark, moody**: never a flat bright scene |
| darkest 1% luminance | 0.021 | 0.051 | shadows are deep but never pure black |
| overall colour bias | neutral-warm stone | strongly orange (RGB 0.40/0.27/0.15) | warm key light, warm shadows |
| character height / screen height | ~10% | ~13% | characters are SMALL: **11.7%** in our spec (42 px of 360) |
Palette anchors from k-means: earth browns `#673f1e #94672e #ae8438 #deb867`, moss `#41533d`, teal roof `#53605b #6a7873 #8da3a2`, warm stone `#766a4f #b0a37e #e6dabf`, deep warm shadow `#1d0804 #280e0f`, lime foliage highlights `#ebde6f`.

## 1. The look in one paragraph
Tiny hand-pixelled people and props standing in a miniature-like diorama: warm low sun, deep warm shadows, glowing lanterns and fires, floating dust, tilt-shift blur above and below a sharp horizontal band, dark vignette. Sea and land share one grade. **Never flat, never bright-and-clean.**

## 2. Scale and grid (hard numbers)
* **Art grid 640 x 360** (16:9). Integer scales: 720p x2, 1080p x3, 1440p x4, 4K x6. Dev-Lite renders at exactly 640x360 and shows it at x2 = 1280x720 inside the developer's 1366x876 screen (this replaces the 683x438 of A1-10: that was not an integer multiple of the art grid).
* **Texel density at the focus plane: 24 px per metre (land / deck), 12 px per metre (open sea).** 1 art pixel = 4.17 cm (land), 8.3 cm (sea). Sea scale is exactly half so the screen pixel grid stays aligned.
* **Camera:** vertical FOV 22 deg; pitch 39 deg on land and 48 deg at sea (sees more water, less foreshortening). Focal length `f = (H/2)/tan(11 deg)` = 926 art px for H = 360, so the focus plane sits `f / px_per_m` = **38.6 m** from the camera (24.3 m high, 30.0 m back). A ground square is foreshortened to `sin(39 deg)` = 0.63 of its width on screen.
* Sprites are **upright billboards** (never tilted), nearest-neighbour filtered, lit by the 3D lights, casting real shadows (Standard) or blob shadows (Dev-Lite/crowds).
* **Ships are 3D models** with pixel textures, not sprites (a 22 m sloop at 24 px/m = 528 px: wider than the screen's focus width; sprites cannot rotate, show damage, or sail). Ship textures need two sets: deck/boarding view 24 px/m and sea view 12 px/m (decision gate in I-module). `shp_sloop_e` in the placeholder set is only a stand-in billboard for the Look Lab.

## 3. Size spec table (all pivots bottom-centre unless noted)
| asset class | cell / size (px) | real size | pivot | notes |
|---|---|---|---|---|
| Humanoid (crew, NPC) | **48 x 64** | body 42 px = 1.75 m | (24, 60) | 4 dirs (s, n, e, w) stored explicitly, w is NOT auto-mirrored in the file (asymmetric gear allowed) |
| Large creature (giant, bear) | 96 x 128 multiples of 48 x 64 | as designed | feet | |
| Ground tile | 48 x 48, seamless | 2 x 2 m | - | water tile: 4 frames, shifts 12 px/frame, loops in space and time |
| Props small | 16 x 24 .. 32 x 32 | 0.7-1.3 m | (w/2, h-2) | barrel 16x24, crate 28x28, chest 28x24, lantern 14x22 |
| Props large | up to 192 x 192 | trees, huts | (w/2, h-2) | palm (7.8 m) 129 x 187; a house needs >= 168 x 150 (door 1.9 m = 46 px) |
| Icons | **24 x 24** | - | - | 1 px outline, 5-step ramp background |
| UI | designed at 640 x 360 grid, x3 at 1080p | - | - | |
Max colours per sheet (QA enforced): characters 48, props 32, tiles 20, ships 40, icons 14.

## 4. Animation spec (humanoids)
Sheet layout: rows = directions (s, n, e, w), columns = every frame of every animation in this order.
| anim | frames | ms/frame | loop | use |
|---|---|---|---|---|
| idle | 4 | 180 | yes | breathing |
| walk | 6 | 100 | yes | 0.6 s cycle; ground speed set in the J-modules, foot-slide tuned there |
| run | 6 | 70 | yes | 0.42 s cycle |
| work | 6 | 120 | yes | haul, swab, row, cook (props change per job) |
| attack | 5 | 70 | no | wind-up, lift, strike, follow-through, recover |
| hit | 3 | 80 | no | |
| death | 8 | 110 | no | ends lying down, stays on last frame |
Total 38 frames x 4 dirs = 152 cells = a 1824 x 256 sheet. Jobs, shooting, climbing, sitting, eating are added per D/N module as extra anims in the same layout. No sub-pixel animation; limbs move in whole pixels.

## 5. Colour system
* **Master palette: 22 ramps x 5 steps = 110 colours** (`palette.json`). Step 0 darkest ... 4 highlight; shadows drift cool-purple, highlights drift warm-yellow (hue shift). **No `#000000`, no `#ffffff`.**
* Ramps: sand, dirt, stone_warm, stone_cool, wood, hull_oak, grass, foliage, palm_frond, sea_deep, lagoon, roof_teal, ice, cloth_red, cloth_blue, cloth_cream, iron, gold, fire, skin_light, skin_tan, skin_dark.
* A sprite uses <= 6 ramps (character), a tile 1 ramp. Palette swap between ramps is the sanctioned way to make variants (lagoon from sea_deep is done in the Look Lab).
* **Fire-ramp pixels (steps 2-4) are self-lit**: they ignore scene lighting and feed the bloom. That one rule makes fires, lanterns, windows and embers glow automatically.
* Skin: three male ramps for variety; the art never depends on skin colour for role.
* **Shading in the sprite:** 4 cel bands, key light from the top-left (-0.5, -0.6), 1 px selective outline in the darkest step of the neighbouring ramp, no outline between interior parts unless needed for readability. No gradients by dithering (dither is allowed only on fog/shaft quads). Sprites carry baked form shading only; the scene light adds colour and cast shadows.

## 6. Lighting and post-process (numbers in `look_profiles.json`)
| effect | Standard | Dev-Lite | note |
|---|---|---|---|
| tilt-shift | focus_y 0.55, half-width 0.12, ramp 0.33, max blur 10 px @1080 (12 taps) | 6 px @1080 equiv = 2 px at 360 (6 taps) | blur scales with screen height |
| vignette | inner 0.45 -> outer 1.05, strength 0.70 | same | |
| bloom (LDR glow) | threshold 0.65, intensity 0.35, radius 8 px | off | |
| grade | saturation 1.15, contrast 1.08, shadow lift 0.03 plum `#2a1620` | same | |
| shadows | real directional | blob only | |
| light shafts | additive quads | off | |
| dust motes | on | on (cheap) | |
Moods (key / ambient / ambient level / exposure): golden_hour `#ffd9a0 / #8a5a48 / 0.30 / 0.62`, overcast, storm, night_fire (key = dim moonlight `#5a6a9a`, fire only as local lights), frozen_dawn. **Correction to my own earlier rule:** I first planned a cool blue fill light; the measurements show warm shadows in both references (R/B 3.5-6), so cool fill is used only in storm, night and frozen moods.

## 7. Original idea: the look is the survival HUD
`state_grades` in `look_profiles.json` (well / hungry / starving / fevered / mutinous) scale saturation, contrast, vignette and tint. When the crew starves, the world itself drains and closes in; when morale breaks, contrast hardens and a red cast creeps in. Keeps the HUD minimal and makes survival felt. Rendered proof: `looklab_stills/still_beach_golden_starving.png` (saturation 0.63 -> 0.44, vignette 0.34 -> 0.18). Story difficulty can scale the effect to zero; Hardcore Realism leaves it at full strength. The N-modules will drive it from real simulation numbers.

## 8. Content rules for ART
1. Crew art: male characters only (broad-shouldered silhouettes; variety by build, age, beard, gear). 2. No nudity or suggestive art anywhere. 3. No religious symbols, places of worship, deities, halos, or mockery of belief. Mystic content is limited to neutral legends: curses, ancient beasts, pirate lore. (Enforced in data text by the checker; art is reviewed by me against this list per I-module.)

## 9. Typography and UI (provisional)
Title/lore font candidate: **Pirata One** (SIL OFL, available in google/fonts); body font to be chosen in I23 for readability at 640x360 x3. UI palette: `cloth_cream`, `wood`, `iron`, `gold` ramps only. Pixel-perfect UI scale x3 at 1080p.

## 10. Look Lab (how to approve the look without a GPU)
`python tools/looklab/looklab.py` renders: `still_beach_golden_standard`, `still_beach_golden_devlite`, `still_beach_golden_starving`, `still_camp_night_standard`, `still_frozen_dawn_standard`, `still_sea_storm_standard` (1080p / 720p). Ground is ray-cast through the real camera model, sprites are depth-scaled billboards, the post chain is the table in section 6. It APPROXIMATES the Godot shader (Gaussian blur levels instead of the 12-tap golden-angle disc), so the stills are a target, not a guarantee.

## 11. Honest limits
* All content in the stills is **placeholder**: mannequins, plain ground tiles, one low hut (door only 1.2 m), no dense foliage. The refs get much of their richness from dense hand-drawn detail; **that detail is future art work (I-modules), not something post-processing creates.**
* Measured against the refs (see report): matches saturation, vignette, tilt-shift, median brightness; near-miss on focus band (band 4 vs 5) and on shadow depth/warmth. Not tuned further on placeholders on purpose.
* The Godot shader that implements this does not exist yet (J-modules) and nothing here was ever run on a GPU or in Godot.
