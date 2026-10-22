# VP-1A.4 — The interior is drawn too (and the house rule: everything is a 3D model wearing authored pixel art)

Branch `arena/7464ca7a-videos-motion`. Baseline: VP-1A.3 (`fdf930e`). The exterior water and ship silhouette you approved are
**untouched** by this step. VP-1A.4 takes the same authored-pixel-art pipeline below decks: the captain's cabin, the
sleeping deck and the provisioning hold now wear a second drawn sheet, and the rule is now canon for the whole game:
*every object in the game is a real 3D model in the Compatibility renderer, surfaced with authored pixel art* — no flat
tints, no shader-only substitutes, in Normal (Standard) profile the art is crisp; Low-End keeps it readable through mips.

## 1. The interior sheet — `game/art/vp1/interior_px.png` (`tools/vp1/make_px_atlas2.py`)

Same craft as `ship_px.png`: 16 seamless 256 px tiles, quantised ramps, periodic noise, Bayer dither, wrapped seams,
single-pixel grit. Material ids 16..31 (see `PX_DENS` / constants in `ship_mesh.gd`):

| id | tile | drawn features | px/m |
|----|------|----------------|------|
| 16 | IFLOOR | worn floor planks, dithered foot-traffic path, one replaced pale plank, spill, nails | 44 |
| 17 | IHULL | inner hull planking with **drawn frames** (futtocks), lit edges, through-bolts, bilge stain | 36 |
| 18 | CEIL | deck-head planks, nail rows, lantern soot | 40 |
| 19 | CWALL | cabin panelling: moulded raised panels, lit/dark moulding, field grain, brass screws | 48 |
| 20 | RUG (own) | woven bands, diamond motifs, fringe, worn patches | 64 |
| 21 | CHART (own) | parchment, coastline + shoal ring, compass rose, rhumb lines, script dashes, coffee stain | 96 |
| 22 | HAM (own) | hammock canvas: weave, stitched seams, gathered ends, sewn patch | 64 |
| 23 | BLANK (own) | wool blanket stripes, weave, fuzz | 64 |
| 24 | BOOKS (own) | spines of varied height/colour, gilt bands, title dashes | 96 |
| 25 | FOOD (own) | biscuit rounds with docker holes, salt-fish rows, cheese wheel with cut wedge | 64 |
| 26 | BOTTLE (own) | glass bottles: three glass tints, neck + cork, label, highlight stripe | 64 |
| 27 | BRASS (own) | polished brass ramp, specular streaks, tarnish blooms | 64 |
| 28 | TAR | tarred wood, glossy speckle, drips | 32 |
| 29 | RACK | rack boards with drawn iron uprights, brackets, bolt heads | 40 |
| 30 | ROPEMAT (own) | coiled rope mat: concentric twisted rings | 48 |
| 31 | BALLAST (own) | ballast stones: rounded lit crowns, dark crevices, moss | 40 |

## 2. Integration (systems untouched)

- `ship_mesh.gd`: `PX_DENS` extended to 32 entries; `px_origin()` now takes the tile inside its own 4×4 sheet (`mat % 16`),
  so ids 16..31 wrap into the second sheet; new `M_IFLOOR..M_BALLAST` constants.
- `ship_deck.gdshader`: second sampler `pxatlas2 : filter_nearest_mipmap, repeat_disable`; the pattern chain picks the
  sheet by id (`m < 16` → `pxatlas`, else `pxatlas2`). Own-colour set extended to the coloured interior props
  (20..27, 30, 31); floors/walls/ceiling/racks stay grey-value-tinted so lantern light and per-object value still work.
- `ship_deck_view.gd`: `MATS2_PATH` + `_mats_tex2()` (imported or loaded from file with mipmaps) set on every ship
  material; interior surfaces reassigned: cabin walls → panelling, new drawn deck-head quad under the cabin roof,
  cabin/sleep/hold floors → IFLOOR, inner hull strips → IHULL (drawn frames), desk → timber with CHART sheet + BRASS
  compass, bed/hammocks/bunks → HAM/BLANK, shelf → BOOKS, rug quads → RUG, racks → RACK, ledger paper → CHART (+a BOTTLE
  beside the ink), keelson/mast step → TAR; new props: two ballast piles at the hold ends, a rope mat under the big coil,
  an open biscuit crate by the ledger (FOOD top). Collision, layouts, stores logic, dissolve lists: unchanged.

## 3. How to test (Windows, from the ZIP)

F5 at the Capital Port, `E` aboard, then walk: cabin (rug, panelled walls, chart with rose and rhumb lines, books,
brass compass, deck-head overhead) → ladder to the sleeping deck (hammock canvas, blankets, worn floor, frames on the
walls) → ladder to the hold (drawn frames + through-bolts on the hull, rack boards with iron uprights, provisions,
ballast piles, rope mat). F2/F3/F4: lanterns and sun light the drawn interior; F1 Low-End stays readable. Nothing blocks
walking, fishing or the stores panel (suite proves the behaviours).

## 4. Evidence (`docs/vp1a4_shots/`, 1366×876 native renderer)

- `A0_cabin_after.png` / `B0_cabin_before.png`, `A4_cabin_close.png` / `B4_cabin_close_before.png` — cabin, same camera,
  VP-1A.4 vs VP-1A.3 (2× nearest crops).
- `A1_sleep_after.png` / `B1_sleep_before.png` — sleeping deck.
- `A2_hold_after.png` / `B2_hold_before.png`, `A5_hold_close.png` — hold with racks and ballast.
- `A3_provisions_after.png` — stores view. `C0_interior_sheet.png` — the interior sheet itself.
- Runs `/tmp/DW7` (after) and `/tmp/DWold` (worktree at `fdf930e`): **0 shader/runtime errors** each. Suite **42/42 PASS**.
  `gdlint` clean, `check_gd_warnings` 0, `check_gd_types` PASS.

## 5. Known limits

1. At the default deck-camera distance the finest interior tiles (chart, books) read as colour masses; they resolve when
   the camera is close (cabin dissolve brings you near) — intended HD-2D behaviour, same as the references.
2. Ballast piles and the rope mat are visual only (no collision added) — you can walk through them; deliberate to keep
   the hold walkable everywhere.
3. Dev-Lite 360p softens interior art through mipmaps (same trade as VP-1A.3). HD 3000 fps remains **UNMEASURED**.
4. The cabin's drawn deck-head is a single quad: no beam shadows on it (beams are geometry below it and cast in the
   shader's march only for the listed casters).

## 6. CANON update

- **House rule (canon):** every game object = real 3D model (Compatibility) + authored pixel-art sheet(s); new content
  (Anvil Cay, cities, islands) extends the sheets or adds new ones, never flat tints or shader-only substitutes.
- Ship art = two sheets: `ship_px.png` (ids 0..15) + `interior_px.png` (ids 16..31); UV = atlas art, UV2 = (material,
  relative height); own-colour ids: 4, 12, 14, 20..27, 30, 31; everything else grey value tint ×2.
- Interior densities in `PX_DENS` (chart/books 96 px/m = finest art in the game).
- All VP-1A/1A.2/1A.3 canon stands (lighting, ocean, profiles, suite, exterior untouched).

## 7. Next modules (proposed)

1. **VP-1B Anvil Cay coast** (recommended): beach/rocks/palms/path/pier/harbour from sheet-1 tiles 12..15 + a new cay
   sheet (thatch, palm bark, fronds, jetty wood), same sun tying land to sea.
2. **VP-1C camera & resolution pass**: 1366×768…4K and odd aspects without distortion/cropping; deck-density decision
   (14.4 vs 24 px/m) with measured evidence; break the deck-tile tone repetition.
3. **VP-1A.5 rigging & sail close-ups**: drawn rope coils, belaying pins, sail reef-points and cringles at close range,
   completing the ship's art before the cay phase.
