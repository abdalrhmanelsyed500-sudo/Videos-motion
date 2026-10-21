# VP-0 Godot Technical Art Specification
Status: proposal, **implemented in the prototypes** (`game/prototypes/vp0/`). Numbers marked *est.* are estimates, not measurements on the target PC. Godot 4.7.2, **Compatibility renderer** (OpenGL 3.3 / ANGLE ES 3.0), no Steam, Windows 10 64-bit.

## 1. Internal render resolution and scaling
* The 3D world renders into a **SubViewport of 640×360** (`ART_W × ART_H`), `msaa_3d` off, own world, `UPDATE_ALWAYS`. A `TextureRect` (nearest filter) shows it through the *grade* canvas shader at window size.
* Window sizes: 1280×720 = ×2, 1920×1080 = ×3, 2560×1440 = ×4, 3840×2160 = ×6. At 1366×876 (the dev PC) the project must use `display/window/stretch/scale_mode = "integer"` (the prototypes set `Window.content_scale_stretch = INTEGER` with the arg `int=1`; production sets the project setting) → 1280×720 centred with a border. Non-integer scaling blurs and shimmers pixel art: it is **not allowed** in the default profile.
* The project's UI (CanvasLayer) stays at 1280×720 `canvas_items/keep`. UI never goes through the grade pass.
* Dev-Lite is the same pipeline with the grade pass reduced (`taps = 0`, see §10): the picture stays 640×360 pixel-exact.

## 2. Pixel density and filtering
| Tier | Where | px per metre | Visible area (640×360) | Source |
|---|---|---|---|---|
| **T24** | deck, island/city interiors, harbour | **24** (1 px = 4.17 cm) | 26.7 × 15 m | baked from voxel models at 24 px/m |
| T12 | close sea (fishing, docking, near coast) — optional | 12 | 53 × 30 m | `downscale(2)` bake |
| **T8** | open sea (sailing) | **8** (1 px = 12.5 cm) | 80 × 45 m | `downscale(3)` bake (`lod8`) and a dedicated hull bake |
* **All textures: `filter_nearest`, mipmaps off, repeat off** (repeat on only for tiling ground/wood tiles and the noise texture, which is `filter_linear`). Never `filter_linear` on a sprite. Never rotate or scale a sprite node.
* The sprite shader snaps every sprite's pivot to the art-pixel grid **in view space** (`round(view.xy · ppm)/ppm`), so a smoothly moving camera never causes shimmer or sub-pixel scaling, and sprites are exactly 1:1 texels.
* The camera itself is snapped in its own plane to the pixel grid (`vp0_stage.gd::_update_camera`).
* Colour: **the project must not use `source_color` hints on prototype/sprite shaders** (tested: in Compatibility the colours are written as authored; a `source_color` decode without a matching encode darkens everything). Colours in uniforms are the authored sRGB values. Verify once on the Windows build with the colour-bar test (gallery planned in VP-1).

## 3. Character-to-environment scale
| Object | Real size | Pixels (T24) |
|---|---|---|
| Humanoid (crew, NPC) | 1.75 m | 42 px in a 48×64 cell, pivot (24,60) |
| Door | 1.9 m | 46 px |
| Barrel / crate | 0.85 m / 1.0 m | 20×37 / 26×41 baked (incl. top face) |
| Deck cannon | 1.3 m | 58×40 |
| Helm wheel | 1.0 m | ~36 px diameter |
| Palm | 8 m | ~190 px tall (T24), 69 px (T8) |
| Sloop | 22 m × 6.2 m beam | 528 × 150 px deck footprint; at sea 8 px/m: ~176 px long |
| Mast + nest | 11.25 m | 287 px incl. crow's nest (2.8 m = 72 px) |
Ground depth is compressed by `sin(pitch)`; upright height by `cos(pitch)`. Pitch 37° land: 1 m of ground depth = 14.4 px, 1 m of height = 19.2 px. Pitch 48° sea.

## 4. Sprite orientation and animation conventions
* **Facing frames are counter-clockwise** seen from above with north up: frame *k* shows the model rotated `k·360/n` degrees CCW (east → north). `vp0_util.frame_for(n, φ)` takes the world angle φ of the model's +x axis. Props: 8 facings (`_f0…_f7`). Ships at sea: **16 headings, clockwise from north** (`sloop_sea_h00…15`, heading 0 = bow up the screen), matching the existing sailing code.
* Pivot = **centre of the footprint on the ground** (not the image centre); stored in the manifest as pixel coordinates from the top-left, rounded to integers at load.
* Humanoids: A3 sheet layout stays (rows = directions s,n,e,w; 38 frames × 4 directions; idle/walk/run/work/attack/hit/death at the A3 timings). Animation is frame-by-frame: **no sub-pixel movement**, limbs move in whole pixels.
* Animated props (winch crank, flag, sails) are extra frame strips in the same cell size; `frame` goes in `INSTANCE_CUSTOM.x` when batched (see §10).
* Sail/hull deformations are done by mesh (ship deck tier) or by extra baked frames (sea tier: 5 trims × 16 headings exists in the current game; VP-1 re-bakes them).

## 5. Tile and terrain sizes
* **Cell = 1 m** in the terrain map (`cay_cells.png`: R = ground type, 255 = water; origin and size in `cay_world.json`). The cell map is looked up in the shader with `texelFetch` after a noise displacement (±0.43 m), which makes borders organic.
* **Ground tile = 48×48 px = 2 m at T24**, 4 variants per row; at T8 the same atlas is sampled with `tile_m = 6` (so a tile pixel is still one screen pixel). Atlas 384×192, rows: 0 sand_dry, 1 sand_wet, 2 grass, 3 dirt, 4 cobble, 5 slab, 6 shallow bed, 7 rock floor (`ground_atlas.png`, QA cap 20 colours per tile).
* **Depth/shore map** for water: signed distance to shore in metres mapped −4…+20 → 0…255 (R8), 4 px/m at the cay (416×312), 3 px/m at sea (720×510). Generated from the cell map by `tools/vp0/bake_world.py` (EDT). It also drives sand-through-water and foam.
* Elevated terrain (terraces, quays) = a few textured meshes with the same tiles (cel shader). Never more than ~10 quads per terrace.

## 6. Palette and material standards
* Master palette `data/look/palette.json` (22 ramps) + `palette_vp0.json` (10 ramps): 5 steps each, dark → light; shadow drift cool, light drift warm. Baked sprites pick colours **only** from ramps (the baker's `define(id, ramp, base_step)` enforces it).
* Materials in the baker: id → (ramp, base step, optional flag `emissive` = fire-key, `flat` = no shading). Each material gets 4 cel bands = base step −1 … +2 (+ AO, rim and the depth-edge line).
* Max colours per sheet frame (QA): characters 48, props 32, **structures 40 (proposed)**, ships 40, tiles 20, icons 14. Measured on the VP-0 set (max per frame): props ≤ 24; island sprites ≤ 36 (house_a 36, house_b 28); hull 35; LOD ≤ 12.
* **Emission:** a sprite pixel with `r ≥ 0.995, 0.55 ≤ g, b ≤ 0.62` (the fire ramp's steps 3–4) is emissive in `vp0_sprite.gdshader`. Rule for artists: *do not use these colours for anything that should not glow*. Gold highlights are `#fbe28a` (r = 0.984) on purpose, below the threshold.
* No `#000000`, no `#ffffff`; the grade clamps to `(0.035, 0.03, 0.05) … (0.985, 0.97, 0.95)`.

## 7. Lighting and shadows
* **One sun** per look: direction vector + tint + shadow colour (`LOOKS` in `vp0_stage.gd`: day, golden, dusk, night). The sun is *not* a Godot light.
* Sprites: `light_tint` multiply; emissive pixels follow `glow` (0 by day, 1 at night, from the look).
* **Sprite shadows** (`vp0_shadow.gdshader`): the sprite's own alpha silhouette is stood up on its pivot and projected onto the ground plane along the sun direction (max length 7 m). 1 quad per sprite, no shadow map, direction follows time of day. On a deck the shadow is clipped to the hull outline (a closed form of the hull half-width) so it never falls over the sea.
* Meshes (hull, deck, sails, terrace): `vp0_cel.gdshader`, 4-band N·L with warm-light / cool-shadow tint; the sail has a back-light factor (cloth glows when the sun is behind it).
* Halos: additive camera-facing quads with **4 hard bands** (pixel-art glow), per-light flicker; weight comes from the look (day 0, night 1). Real bloom is optional on top.
* Ambient: none; "ambient" is the tint. No real-time shadows, no `OmniLight3D` in the standard path (Compatibility lights cost a pass per light on the HD 3000).

## 8. Camera framing and perspective
* `Camera3D` **orthogonal**, `size = 360 / ppm` (15 m at 24 px/m, 45 m at 8 px/m), `keep_aspect = KEEP_HEIGHT`, pitch **37°** (land/deck) and **48°** (sea), distance 80 m, `near = 30, far = 150` (tight range for depth precision in a WebGL/ANGLE 24-bit depth buffer).
* Composition: the focus band is y ≈ 0.55 of the screen; the ship pivot sits at y ≈ 0.7 (deck), mast tops may crop at the top edge; horizon-less (the ground fills the frame, as in the references).
* Camera moves in whole art pixels. Follow with a critically damped spring on the *unsnapped* target; snap only the rendered position.
* Render order: ocean `render_priority −2`, terrain −1 (both `depth_draw_never`, no depth write → sprites and meshes always win), opaque sprites/meshes with depth write, shadow quads `depth_draw_never`, halos last with depth test off.

## 9. Naming, folders and import settings
```
game/art/<set>/<group>/<name>[_f<k>|_h<kk>].png      set = vp0 now; later per module (ship, island, city, ...)
game/art/vp0/ship        15 models, 78 frames   (barrel, crate, cannon, winch, helm, hatch, chest, mast, cabin, pirate, ...)
game/art/vp0/island      15 models              (palm_a/b/c, rock_a/b/c, bush_a/b, house_a/b, warehouse, pier_4, pier_y_6, lamp_post, signpost)
game/art/vp0/hull        sloop_sea_h00..15      (sea tier)
game/art/vp0/lod8        5 models               (T8 vegetation and rocks)
game/art/vp0/ground      atlas, planks, strakes, sail canvas, noise
game/art/vp0/world       cell maps, depth maps, *_world.json
game/prototypes/vp0/     scenes, scripts; shaders/
tools/vp0/               baker: voxel.py, models_*.py, ground.py, bake_world.py, bake_all.py
```
* IDs: `<kind>_<slug>` (existing convention). Manifests: `<group>/<group>_manifest.json` with `facings`, `ppm`, `frames[{file,w,h,pivot,colours}]`.
* **Import settings** (production): `Compress/Mode = Lossless`, `Mipmaps = off`, `Filter = Nearest` for every sprite/tile texture; `Process/Fix Alpha Border = on`; `Detect 3D = off`; atlas build by `tools/vp0/atlas.py` (VP-1) into 2048² pages. Prototypes load PNGs with `ResourceLoader.exists + load()` and fall back to `Image.load_from_file` (so they work before the editor has imported them; Windows editor import will create `.import` files, which are not committed by the prototypes).
* Bake commands (from `tools/vp0`, Python venv with numpy/Pillow/scipy): `bake_all.py ship island hull lod8`, `ground.py`, `bake_world.py`.

## 10. LOD, culling, atlas and performance rules
* **Sprite batching:** production draws sprites with one `MultiMeshInstance3D` per (atlas page, tier): `INSTANCE_CUSTOM = (frame, glow, fade, bias)`. The prototype uses one `MeshInstance3D` + `ShaderMaterial` per sprite (≈110 draw calls in the harbour shot) which is fine for a prototype and **not** for production (budget: ≤ 150 draw calls per frame on the HD 3000).
* **Culling:** per-sprite `extra_cull_margin` ≥ sprite half-height; MultiMesh with a custom AABB covering the whole chunk (known Godot trap: instance transforms are not part of the AABB, see the earlier invisible-hero bug). Chunk the world in 32 m cells; instance only chunks within 1.5 screens.
* **LOD:** T24 → T12 → T8 chosen by the camera tier, never per object; distant islands use T8 sprites; farther than 120 m a single "island silhouette" sprite.
* **Water/terrain:** one plane each, per-pixel shaders; plane size ≥ screen, `extra_cull_margin` large. The ocean and the terrain each do roughly 5–8 texture fetches per pixel (distance/cell map, noise, tile atlas; read from the shader source, not profiled).
* **Texture memory (measured, VP-0 set):** 124 PNG files = 912 KB on disk; in VRAM (RGBA8) ≈ 5 MB. A full production set is expected below 64 MB.
* **Shaders:** 7 shaders (cel, grade, halo, ocean, shadow, sprite, terrain = 7 files, 393 lines total; `game/prototypes/vp0/shaders/`); no loops except the grade pass (≤ 12 + 8 taps); no discard in the ocean; `render_mode unshaded` everywhere (no Compatibility lighting passes).
* **Grade pass cost (est.):** Standard = 8 blur taps + 16 bloom taps + 1 nearest fetch at window size: at 1366×768 that is ≈ 25 M texture fetches/frame, too heavy for the HD 3000 (est. ~2 GTexel/s peak, bandwidth-bound). Therefore three profiles:
  1. **Standard** (capable GPU): full-resolution grade as in the prototype.
  2. **Balanced:** the blur/bloom/grade pass runs *at 640×360* into a second SubViewport, the window shows it nearest-scaled: ≈ 5.8 M fetches (est.), softer blur, identical pixels in the focus band.
  3. **Dev-Lite:** `taps = 0` (1 fetch): vignette + grade only. The look in the `*_lite.png` shots.
