# VP-1A: Ship and Ocean in the Playable Game

Order (2026-10-21): the approved direction "Pixel Pirates - Cinematic HD-2D" must show up in the ACTUAL game. VP-1A = playable ship (exterior, main deck,
equipment) and the ocean, built into the CP-2B.1 game before any island work.

**Status: built and checked in (a) the Godot 4.7.2 WASM headless runtime (logic tests) and (b) a real WebGL render of the actual game in a software
renderer (screenshots only). NOT run on Windows. NOT run on the HD 3000. No frame rate has been measured anywhere; every performance statement below is
an estimate from what the code does.**

## 1. Audit (what was there)

* The deck is ~10 merged meshes built in code (`ship_deck_view.gd` + `ship_mesh.gd`) with ONE shader (`ship_deck.gdshader`). Good: few draw calls, every
  collider/interaction point comes from `ship_layout.gd`. Weak: all wood was procedural noise (no board orientation or grain), sails were streaky, the
  fishing net was a few thin lines, no cannons or gun ports, hull had no waterline detail.
* The VP-0 sprite props cannot replace this: the cabin, hatches and ladder are walkable geometry. So VP-1A upgrades the meshes and shader in place.
* The ocean already had waves, shore foam, a curved wake, a bow wave, glints and a `detail` switch. Weak: smooth continuous colour, depth contours as coarse
  blobs, foam as soft noise, nothing tied to the pixel-art look.

## 2. What changed

| Area | Change |
|---|---|
| Material atlas | `tools/vp1/make_ship_mats.py` -> `art/vp1/ship_mats.png`, **one 256x256 texture** (2x2 tiles: deck boards, hull strakes, timber grain, canvas weave). R = value, G = warm/cool, B = crevice. One texture for every ship material = no extra material changes. |
| Deck/hull/timber | Boards run bow-to-stern on the deck and along the hull, with per-plank colour variation, caulked seams, nail dots, weathering in the crevice channel. `tex_on` falls back to the old procedural look if the texture is missing. |
| Hull | Waterline band and wale (rub-rail), dark lower strakes, gun ports with cannon muzzles along both sides (**visual only: no colliders**). |
| Sails | Mainsail and jib are now smooth grid surfaces with soft gathered folds, two-sided cloth with back-light (sun through the canvas), seams from the canvas tile, and the near-hero see-through dither. |
| Fishing net | New material `M_NET` (14): a diamond lattice with real holes (`discard`). Used for the net hanging at the davit and the net heaps on deck. |
| Outlines | A depth-jump outline in the ship shader gives a readable silhouette against the sea. |
| Ocean | Bayer-dithered six-tone depth ramp (deep -> coastal -> shallow turquoise), dithered posterize, caustic/contour lines in shallows (only when `detail` > 0.5), dithered foam with faint foam dropped, existing wake/bow wave/hull wash kept. Depth scale uses the 0-8 m range stored in the island depth data. |
| Day/dusk/night | Unchanged lighting; the new ramp follows it (checked with N at noon, later stops and night, see shots `o0..o4`). |

## 3. Quality profiles (existing switch, F1)

* `dev_lite` (640x360, `detail` 0, posterize 12): the new ocean ramp and dithered foam stay; caustics and contours are skipped. This is the Low-End look.
* `standard` (1280x720) and `ultra` (1920x1080): add caustics/contours.
* No reflections, no extra render passes, no real-time shadows, no new transparent layers were added. New cost: one extra 256x256 texture sample set per ship
  fragment, a few ALU ops in the ocean shader. **Estimated** small; **UNMEASURED** on the HD 3000. Please report the bench output on your PC (key B).

## 4. Placeholders and honest limits

* The **sea-view ship** (16-heading billboard, `art/../ship_sloop_hull.png` / `_sails.png`) is UNCHANGED. It is tied to `ship_sloop_sailbox.json`; re-baking
  needs the sea pixel density decision (VP-1C). You will notice the deck view is richer than the distant ship.
* Crew still look like mannequins (VP-0 finding); not part of VP-1A.
* Cannons are muzzles at gun ports, not full cannon models on the deck.
* The wake still follows the existing simulation (curved, real ship motion); its look is only changed by the new foam dither.
* Resolution/aspect questions (14.4 px/m vs 24 px/m on deck; 640x360 vs 800x450 vs 960x540; 1366x768 ... 3840x2160; ultrawide) are **proposals for VP-1C**,
  not changed here. Stretch/aspect settings are untouched.

## 5. Verification

| Check | Result |
|---|---|
| Test suite (WASM headless) | 42 passed, 0 failed |
| `test_ship_view` (mesh count 8-20, vertices 3000-60000) | 30 checks, 0 failed |
| `gdlint`, `check_gd_warnings`, `check_gd_types`, `check_docs` | clean (heuristic checkers; NOT Godot) |
| Real-renderer run of the actual game (`vp1_cmp.mjs`, `vp1_sea.mjs`, `deck_walk.mjs`) | no `SHADER ERROR` / `SCRIPT ERROR` in the page log (see section 6) |
| Screenshots before/after | `docs/vp1a_shots/` (`before_*` = CP-2B.1, `after_*` = this build) |

## 6. Windows test steps (about 5 minutes)

1. Unzip, open the project in Godot 4.7.x, press F5 (or run `res://h2d/h2d0.tscn`).
2. Sea: sail with A/D; check the water: dithered turquoise, deeper blue away from land. Press N several times: dawn/day/sunset/night. Press F1 for the other quality profiles.
3. Leave the helm (E). Walk the deck: planks should run along the ship, the hull side shows gun ports, the sails look like cloth with soft folds. The net at the davit should look like a net.
4. Check all three decks and the cabin (ladders, hatches). Use the winch (F) and fish; fish enter the hold once. Land at the harbour, sell, open the map (M).
5. If anything looks wrong or runs slowly, press B and F3 and send a screenshot with the console output.
