# VP-1A.2 — Cinematic HD-2D: lighting first, pixel-art detail first (ship + ocean)

Status: **delivered in the playable game** (exact commit in the delivery report and `git log`: the VP-1A.2 commits). Everything in this document was rendered by the REAL game
(`game/h2d/sea_view_3d.gd` → SubViewport → post), never by a prototype. The software renderer of the test harness stands in
for the user's GPU, so colours here are close but not identical to a real Windows run; **no frame rate is claimed anywhere:
nothing in this release has been measured on the Intel HD 3000.**

## 1. Why the old picture fell short (ranked by impact on perceived quality)

Compared frame-for-frame against the HD-2D references and the user's own screenshot of the game:

1. **No cast shadows anywhere.** The deck was lit by one quantised sun term per normal; nothing ever threw a shadow, so
   barrels, cannons, the mast and the pirate read as stickers pasted on a bright board, and no time of day could be felt.
2. **The sea was a flat cyan field at gameplay scale.** Depth ramp and wake existed, but there was no sun sheen, no lit
   crests, no sky in the water at grazing angles and no dark contact line where the hull meets it.
3. **Props were primitive solids.** Barrels, crates, lanterns and the gun-port muzzles were boxes/cylinders with one flat
   tint each: silhouettes read as placeholders, not objects.
4. **No contact between objects and surfaces.** Without ambient occlusion or contact darkening everything floated.
5. **Night and sunset were global tints.** Lanterns were self-lit yellow boxes that lit nothing.
6. **The see-through dissolve hole ate the sails.** The hole cut around the pirate had no height limit, so the mainsail
   luff and rigging dithered away in a speckle patch beside him.
7. **Cohesion breakers outside this milestone's scope:** the 16-heading sea sprite and the mannequin crew (still open, see
   "known limits"); internal 640x360 on Dev-Lite hides fine detail (Standard/Ultra show it).

Fixing 1-6 is what this release does, in the real pipeline, with no new render pass, no shadow map, no transparency and no
new texture.

## 2. The lighting system (ship_deck.gdshader, ship_deck_view.gd)

* **One sun, real shadows, analytic.** Every fragment on the open deck shoots ONE ray towards the sun (model space, dithered
  penumbra) against: up to 40 axis-aligned boxes (mast, cabin, crow's nest, winch, cannons, fish barrels, barrels, crates,
  windlass, hatch coaming, helm, davit, bowsprit), the pirate (one box at his feet), the bulwark (a 9-step march over the
  real hull outline) and the two sails as translucent triangles (they dim the sun to a warm 60 % instead of blocking it).
  Cost: pure ALU in the fragment shader; no pass, no texture, no memory.
* **Contact darkening (AO)** from the same box list (distance-to-box falloff) plus baked corner gradients on every floor and
  inner wall (per-corner vertex colours, `ShipMesh.quad_c`), so barrels and crates sit ON the deck. A cool sky/bounce fill
  keeps shadow sides readable; nothing goes black.
* **Lanterns are light sources.** Four per material with inverse-square-ish falloff, a normal-facing term, warm colour, a
  slow flicker, and `lamp_on` rising with `h2d_night`: at night the deck carries warm pools under the stern lantern, the
  helm lantern, the foremast lantern and the mast lantern, against cool ambient. Below decks the lamps are always on.
* **Metal glints:** iron catches one crisp dithered sun sparkle (step, not blur) when the sun aligns with the view.
* **Time of day is structural, not a filter:** sun direction/colour, ambient, lantern pools, sail translucency, water
  sheen and horizon glow all move together (see the H0/H1/H2 comparison).
* **Pixel clarity protected:** shadows and sheen are dithered with a 4x4 Bayer matrix at art-pixel scale; the sun term stays
  quantised; no bloom increase, no blur on the play area (the existing tilt-shift only softens the top and bottom bands).
* **The dissolve hole now has a height limit** (`hero_y`): rails and the cabin roof still open around the pirate, the sails
  and rigging above his head never do (fixes deficiency 6).

## 3. The ship as a detailed environment (ship_props.gd, ship_mesh.gd)

New reusable prop builders, all merged into the existing handful of meshes (draw calls unchanged):

* **Cannon:** lathe-turned tube (breech knob, base ring, reinforce, chase, muzzle swell and lip), brass band, trunnions,
  a stepped carriage with cheeks, bed, quoin wedge, axles, four trucks, a breeching rope to two ring bolts, and a small
  pyramid of shot beside it. Four of them stand at real gun ports (two a side) as new SMALL layout obstacles
  (`ship_layout.gd CANNON_U`); every deck interaction was re-checked by the suite.
* **Barrel:** lathe with bulging staves, three raised iron hoops with rivets, lid and bung; the shader adds per-stave
  colour from the angle round the lathe (new angular UV) plus wood grain from the VP-1A atlas.
* **Crate:** body plus four corner posts, top/bottom rails, a diagonal brace, an iron corner plate.
* **Lantern:** glass body (the emitter), iron cap/base, four bars, ring handle — it now reads as a lamp, and it lights.
* **Rigging furniture:** deadeyes with chain plates where the shrouds meet the rail, two belaying-pin rails with turned
  pins and a hung rope, pulley blocks at the davit, masthead and forestay, knots; the anchor became a real anchor (shank,
  stock, arms, flukes, ring) hung from a cat-head.
* **Hull:** two rubbing strakes standing proud of the planking per side (a lit top lip over a dark face) on top of the
  VP-1A waterline band, wale and gun-port frames: layered planking that catches the sun.
* **Sails** keep the VP-1A cloth (folds, stitching, back-light) and now cast their translucent shadow on the deck.

## 4. The ocean as a lit environment (ocean.gdshader)

* **Sun sheen:** a broad warm path towards the sun computed on the SMOOTH swell normal (ripples excluded), quantised to
  three dithered steps, killed by overcast and gusts: light on water, not sparkle.
* **Lit crests:** the sun-facing side of a wave glows shallow-turquoise (cheap sub-surface term on crest height).
* **Sky in the water:** at grazing angles the sea takes the horizon/fog colour (warm at sunset, cold at dusk and night),
  plus an atmospheric **horizon glow** towards the sun's bearing at dawn/dusk, three dithered steps.
* **Hull contact:** the water darkens in a tight ring around the hull, a thin wobbling foam line rides the waterline, and
  the existing wake/bow foam keeps its dithered pixel-art core.
* Everything above respects `detail`: Dev-Lite keeps sheen (cheap) and drops caustics/foam lanes as before.

## 5. Profiles and cost

| | Standard / Ultra | Dev-Lite (Low-End) |
|---|---|---|
| internal resolution | 1280x720 / 1920x1080 | 640x360 |
| shadow casters | all (20+) | 12 largest |
| penumbra dither | soft | tight |
| ocean caustics / lanes / crest noise | on | off |
| sun sheen, horizon glow, hull ring, lanterns, AO | on | on |

No new render pass, no shadow map, no transparency, no new texture, no bigger textures. The shadow work is a bounded ALU
loop in one fragment shader. **Frame rate on the Intel HD 3000: UNMEASURED — press B in game for the bench and report it.**

## 6. Evidence (docs/vp1a2_shots/, real game, software renderer, 1366x876 window)

The H pairs keep the HUD on (same in before and after) so the frame is unmistakably the live game; the L series and the
sea series are captured with the HUD hidden.

* `before_H0_day.png` / `after_H0_day.png` — same camera, mid-deck, Standard profile, day (baseline = CP-2B.1 commit 0465780).
* `before_H1_sunset.png` / `after_H1_sunset.png`, `before_H2_night.png` / `after_H2_night.png` — the same two moments.
* `after_H3_night_lite.png` — the SAME night on Dev-Lite: the art direction survives the low-end profile.
* `after_L0..L4` — one continuous day cycle on Dev-Lite at mid-deck (day, afternoon, sunset, night, dawn).
* `dw_d00..d12` — the full deck walk after integration (all three decks, cabin, nest, winch, fishing barrels).
* `sea_o0..o4` — open sea at five times of day.

## 7. Windows test steps

1. Unzip, open the project in Godot 4.7.x, press F5. The game starts at the helm in Dev-Lite.
2. Press F1 once (Standard), F3 to hide the HUD, E to leave the helm and walk to mid-deck: at day the mast, the sails and
   every barrel throw a shadow; walk around a barrel and watch its contact darkening.
3. Press N repeatedly: sunset lengthens the shadows and warms the sails; night switches the deck to lantern pools against
   cool ambient; dawn returns. The sea changes with them (sheen path, horizon glow, dark hull ring).
4. Stand beside a cannon (two a side against the bulwark): carriage, trucks, breeching rope and shot pyramid.
5. Check the game still plays: three decks and the cabin via ladders/hatches, the winch (F) and first-person fishing,
   fish entering the hold once, selling ashore, M map, C course hold.
6. Press F1 twice more to return to Dev-Lite and compare: same art direction, fewer shadow casters, no caustics.
7. Press B and send the bench output on your PC; nothing here has been measured on the HD 3000 yet.

## 8. Known remaining visual limits

* The 16-heading sea sprite (ship seen from afar) and the mannequin crew are unchanged: VP-1C candidates.
* No true volumetrics or light shafts: deliberately skipped as unjustifiable on the target GPU; the horizon glow and the
  lantern pools carry the atmosphere instead.
* Cannons are fixed dress; no reload animation (combat is a later module).
* Tilt-shift still softens the top and bottom of the frame by design (HD-2D miniature look); the play band stays sharp.
* Software-renderer screenshots show the water more cyan than a real GPU will.
