# MODULE A4 - Placeholder asset pipeline
Status: delivered. 38 assets generated, 0 QA problems. Overview image: `art_bible/placeholder_contact_sheet.png`. Live list: `docs/ART_STATUS.md` (generated).

## 1. Goal
Every system (J, N, F modules) can be built and tested **now** with correctly sized, correctly named, palette-locked art, and the final art replaces it later **by dropping a same-named file**, with zero code or data changes.

## 2. How it works
```
tools/placeholder/placeholder_specs.json  (icon list; data-driven)
tools/placeholder/{pxdraw,characters,props}.py   -> palette-locked drawing kit
tools/placeholder/gen_placeholders.py            -> writes:
    game/art/placeholder/<category>/<asset_id>.png
    game/art/manifest/sprites.json      (sizes, pivots, frames, timings, px/m, colours, status)
    docs/ART_STATUS.md                  (placeholder vs FINAL per asset)
    art_bible/placeholder_contact_sheet.png
game/core/assets.gd  (autoload "Assets")  -> asset id -> texture / SpriteFrames; art/final/ wins over art/placeholder/
game/ui/asset_viewer.tscn (main scene)    -> shows everything animated; SPACE next anim, TAB next direction
```
The PNGs are committed, so the developer's PC never needs Python.

## 3. The 38 placeholders
* **Characters (4 sheets, 1824 x 256 each, 48 x 64 cells, 38 frames x 4 directions):** `spr_crew_mannequin_captain` (red coat, tricorn), `spr_crew_mannequin_sailor` (cream shirt, red bandana), `spr_crew_mannequin_gunner` (blue cap), `spr_npc_mannequin_villager`. All male silhouettes (rule 1). Animations idle/walk/run/work/attack/hit/death exactly as in A3 section 4 (in the death pose the hat falls off so the lying body fits the 48 px cell). They are intentionally plain "mannequins": they use the real palette and light, so they look consistent in the scene but nobody mistakes them for final art.
* **Tiles (48 x 48, seamless):** `til_sand_a`, `til_grass_a`, `til_dirt_a`, `til_cobble_a`, `til_deck_planks_a`, `til_snow_a`, `til_water_deep_a` (4 frames, 220 ms, loops).
* **Props:** `prp_barrel` 16x24, `prp_crate` 28x28, `prp_chest_closed` 28x24, `prp_rock_a` 36x24, `prp_palm_a` 72x104, `prp_palm_b` 129x187, `prp_hut_a` 104x104 (undersized, door 1.2 m: a stand-in), `prp_lantern` 14x22 (emissive), `prp_cannon` 40x28, `prp_campfire` 28x28 x 4 frames @110 ms (emissive).
* **Ship stand-in:** `shp_sloop_e` 272x200, 12 px/m (real ships are 3D models, A3).
* **Icons (16, 24 x 24):** hardtack, salt meat, fresh fish, water barrel, grog, gunpowder, cannonball, lime, bandage, rope, plank, tar, canvas, hammer, fishing line, coin (2-letter code on a category-coloured plate).

## 4. QA built into the generator (`gen_placeholders.py` exits 1 on any failure)
1. every non-transparent pixel is in `palette.json` (off-palette = fail); 2. colour budget per sheet (characters 48, props 32, tiles 20, ships 40, icons 14); 3. asset ID grammar; 3b. **no character frame may touch its cell border or be empty** (this check found a real bug on the first run: 114 of 608 frames clipped - the cutlass tip and the fallen body overflowed the 48 px cell; fixed by a shorter blade, and the hat comes off in the death pose; now 0 of 608); 4. `check_project.py` verifies manifest <-> files; 5. `tests/test_assets.gd` repeats palette lock + sheet dimensions inside Godot (no GPU needed).
Result of this run: 38 assets, 0 problems.

## 5. Add a new placeholder
* Icon: add `["ico_item_<name>", "XX", "<category>"]` to `placeholder_specs.json`, run the generator. Done.
* New prop/character kind: add a function in `props.py`/`characters.py` using `Canvas.ellipsoid/capsule/cylinder_v/poly/rect`, register it in `gen_placeholders.py`. Shapes are shaded automatically with the A3 key light.
* Run: `python tools/placeholder/gen_placeholders.py` (needs numpy + pillow), then `python tools/check_project.py`, commit PNGs + manifest together.

## 6. Replace a placeholder with final art
1. Draw to the A3 spec (same size, pivot, frame order). 2. Save as `game/art/final/<category>/<asset_id>.png` (same file name). 3. Run `--import` once or open the editor. 4. `Assets.path_for(id)` now returns the final file; `ART_STATUS.md` shows `FINAL` after the next generator run. The manifest entry (timings, pivot) still applies; edit it if the final art changes frame counts or timings.

## 7. Using it in game code
```gdscript
var spr := AnimatedSprite2D.new()           # 2D test scenes; the 3D game wraps this in Sprite3D billboards (J-modules)
spr.sprite_frames = Assets.sprite_frames("spr_crew_mannequin_captain")
spr.play("walk_e")                           # "<anim>_<dir>", dirs: s n e w
var tex: Texture2D = Assets.texture("ico_item_hardtack")
```
The default texture filter is **Nearest** (`project.godot`). 3D `Sprite3D` nodes must set `texture_filter = NEAREST` and `pixel_size = 1.0/24.0` (land) in the J-modules.

## 8. Original idea: the placeholder set is a ruler, not decoration
Because every placeholder obeys the true px/m scale, character-to-door, barrel-to-crew and tile-to-body ratios, level layout and sailing/walking times built now stay valid when final art arrives. The Look Lab renders the same placeholders through the full post chain, so "does the scene read?" can be asked before any final art exists.

## 9. Known limits / not verified
* Mannequins are crude; the tricorn reads like a conical hat; sheet frames were checked visually in contact sheets, not in motion in Godot.
* Hut is undersized, sails are flat, no foliage clutter. Fine for placeholders; the spec to build final art is A3.
* `assets.gd` and `asset_viewer.gd` are syntax-checked only, never run. Expect to fix small runtime errors on first launch; send me the output.
* Emissive flags in the manifest are data only until the J-modules read them.
