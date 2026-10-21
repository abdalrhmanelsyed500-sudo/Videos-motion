# CP-2 Release B: Manual First-Person Fishing and Fish Inventory

> **CP-2B.1 (2026-10-21): the automatic net and the F7 test-fish key described in this document were removed. Fish now come only from the winch (CP2B_MANUAL_FISHING.md, CP2B1_MANUAL_ONLY.md).**

Working title "Crown of the Seas". Baseline: Release A (`0709dc0`, tested by the user on Windows). Release A's ship exploration,
sailing and the r7 map are not rewritten; Release B adds to them.

**Status: built and tested in the Godot 4.7.2 WASM headless runtime and in a real-renderer browser harness only.
It has NOT been run on Windows, on the Intel HD 3000, or with real keyboards. Section 7 is the checklist for that.**

## 1. What the player does

| Step | Key | What happens |
|---|---|---|
| Walk to the winch on the main deck (the drum by the davit, port side) | WASD | Prompt: **F  Work the fishing winch** |
| Enter | **F** | Full-screen first-person view: sea, the ship's side, the winch with the pirate's hands on two cranks, the davit and pulley, the rope, the net. If the ship is not on a fishing ground, the sea is rough, the hold is full, or a ground needs a hand you have not hired, you get a plain sentence saying why and nothing else changes |
| 0. Heave to | (wait) | The ship slows to 1.5 kn or less (same rule as the old nets). Esc lets go |
| 1. Cast | **Space** | A needle sweeps a bar. Perfect (narrow centre), good, fair, weak (no press for 14 s is a weak cast). The cast sets the net's reach and the catch potential. Rope and net animate down; shoal shadows gather |
| 2. Haul | **A** and **D**, alternating | Each correct alternate pull advances the net. Ideal gap is 0.42 s. Streak and rhythm gauge on the left, rope tension meter on the right (green band is safe), strain and "catch left" bars under it, next lever highlighted at the bottom. Fish make runs and turns, announced 0.8 s before: ease off during a run |
| 3. Raise | (automatic) | Drum spins, net rises out of the water dripping, the REAL fish are in the net |
| Catch card | **E** or **Space** | Picture, species, number and kg for each kind, grade, cast, pace, streak, room left in the hold |
| Unload | (automatic) | The fish fly into a barrel; the catch goes into the real hold at that moment |
| Leave | **Esc** | During cast/haul the net comes back empty and nothing is lost or stored. On the catch card Esc unloads |
| Storage panel | **E** at the fish barrels | Picture, name, quantity, kg and freshness per species in the hold; total quantity; capacity and free space; close hint |

Keys are Input Map actions (Project Settings > Input Map): `fish_winch` F, `fish_haul_left` A, `fish_haul_right` D, `fish_cast` Space,
`fish_cancel` Esc. Each has a physical-key event and a key-label event (layout-proof, like `open_map`); `ShipKeys.ensure_actions()` repairs
a project file that lost them. The on-screen labels are read from the Input Map, so a remap shows on screen.

~~At the helm F still lowers the old passive drift nets~~ **(changed in CP-2B.1: F at the helm never fishes; it shows where the winch is. There is no passive net and no F7 test fish.)**

## 2. Failure and quality (nothing is a silent loss)

* Haul quality `q = integrity^0.8 x (0.55 + 0.45 x pace) x (0.75 + 0.25 x streak) x cast`. Catch weight = potential x q.
  A sloppy player catches roughly a quarter of what a perfect one does.
* Rope strain over the band damages the shoal and, at 100%, **snaps the rope**: the haul is lost, with the reason on a red card.
  A slack rope or long pauses let the shoal **escape**; a very slow haul ends with you **tired**.
* Single-key mashing: a repeated side pull is worth 25% and adds loss; both mash kinds snapped the rope in 6 of 6 simulated runs.
* Cancel at any point before the net is up is free and clean.

## 3. Data (everything is tunable without code)

* `data/tuning/tuning_mfish.json`: 39 `mfish.*` values (aim width and period, sink/soak/raise/unload seconds, ideal gap, band, strain,
  surge timing and size, par time, kg per haul, spreads). `fish_manual.gd` `DEFAULTS` equal the JSON (a test enforces it).
* `data/port/manual_fishing.json`: per species `avg_kg`, `icon`, note; per ground `pull`, `surge`, `shy`, label.
* Existing data is reused: `fishing_grounds.json` (grounds, richness, species weights, min crew), `fish_market.json` (names, prices),
  the passive nets' time-of-day multipliers (dawn x1.3, night x0.7) and the crew catch bonus.
* **No new species and no price change.** Same five species. Counts of fish are derived: kg / `avg_kg`
  (sardine 0.12, mackerel 0.45, parrotfish 1.4, red snapper 1.8, yellowfin 6.0). The hold still stores kilograms.
* **Economy:** manual fishing yields about 7 to 8 kg per minute of play (passive nets: about 6). A test asserts 6 to 20 kg/min.
  Grounds differ: Pilchard Shallows is gentle (pull 0.75, surge 0.6) and Blue Drop is the hardest (pull 1.35, surge 1.4) but richer.
  Blue Drop still needs one hand aboard (existing rule). In the simulated Blue Drop test reading the surges landed 12 of 12 nets
  (60.6 kg); ignoring them landed 10 (51.4 kg, 2 snapped).
* Perfect haul 7.5 to 13 s (about 8.5 s with no pauses); a steady slow player lands in about 23 s with quality 0.47.

## 4. Fish art

Five 48x24 pixel-art PNGs, facing right, drawn by `tools/h2d/bake_fish.py` into `game/art/fish/ico_fish_<species>.png`
(preview: `docs/cp2b_shots/fish_icons_6x.png`). They are a first, honest art pass in the existing palette feel, not final art. They are not
in `art/manifest/sprites.json` (that file ties every entry to the placeholder palette lock); `h2d/fish_art.gd` loads them directly
(imported resource if it exists, otherwise the PNG from disk, like the sea view's texture loader).

## 5. Engineering

| Piece | File | Knows about |
|---|---|---|
| State machine | `h2d/fish_manual.gd`, `fish_catch.gd` | Nothing but data and a `commit(port)` callable. No nodes, no input |
| Session glue | `h2d/fish_session.gd` | Starts/ends the session, forwards the five actions, commits to the REAL `PortState.add_catch`, emits `sfx` and `ended` |
| First-person view | `h2d/fish_view.gd` | Draws the state machine; one `_draw` (a few hundred primitives), no 3D, no shaders, no extra viewport |
| Storage model | `h2d/fish_storage.gd`, `fish_panel.gd` | The model is plain data from `PortState.lots`; the panel draws it and is refreshed every frame while open |
| Host | `h2d/h2d0.gd` (about 90 lines added) | F at the winch, blocking, restoring the world |
| Grounds and rules | `h2d/fishing.gd` | the ground, sea and drag rules; since CP-2B.1 it has no timed catch at all |

* **No temporary inventory.** The catch is added to `PortState` (the same call the passive nets and the market use) when the unload
  starts, so barrels, the storage panel, the HUD hold bar and the fish market all see it at once.
* **No global input hook.** Fishing keys are read in `_input` only while a session is active, and only the five actions (plus E on
  the cards) are consumed. While it is up the other keys do nothing (M, digits, Tab, W...), so nothing steers or jumps behind it. The
  map's `can_open` rule is chained (the port controller's own "no chart over a conversation" rule stays in force) so the chart cannot
  open hidden behind the view.
* **Never stuck.** The session ends by itself when the ground is lost, the sea turns rough, the ship stops sailing, a ship reset happens
  or the nets are stopped from outside. Every end path hides the view, hides nothing else, re-enables the 3D world and the walk keys
  (`fish_flow` tests each path). While the view is up the 3D world is not rendered at all (saves the GPU on the HD 3000).
* Barrels on deck were already driven by `hold_frac` (four barrels fill in turn); this release adds a check that they follow a catch and a sale.
* **Audio:** the project has no audio system yet. `FishSession` emits `sfx(name)` for cast, splash, pull, bad_pull, warn, snap, raise,
  catch, unload and end so sounds can be attached later. **There is no sound in this release.**

## 6. Tests (what was and was not run)

Automated, Godot 4.7.2 WASM headless (logic, parsing, scene flow, real key events through `root.push_input`):

| Test | Result |
|---|---|
| `test_fish_manual` (state machine, simulated players, economy window, commit) | 150 checks, 0 failed |
| `test_fish_ui` (storage model, pictures, input actions and repair, views build) | 56 checks, 0 failed |
| `fish_flow` (the whole sequence in the real `h2d0` scene: refusals, enter, stray keys, cast, haul with A/D, raise, card, unload, real hold, barrels, panel, sale, Esc at each stage, idle failure, ground lost, reset, nets stopped) | 71 checks, 0 failed |
| `deck_flow`, `map_flow` (Release A regressions; one assertion updated to the new panel) | 68/0 and 54/0 |
| Full suite `tools/godot_node/run_suite.sh` (code commit `6b3d1b0`) | 41 passed, 0 failed |
| `gdlint`, `check_gd_warnings`, `check_gd_types`, `check_docs` | clean |

Real renderer (Godot web template in headless Chromium with SwiftShader at 1366x876, **software, not the HD 3000**):
`tools/godot_browser/scenarios/fish_winch.mjs`, shots in `docs/cp2b_shots/`. Because the software renderer runs at about 8 fps, a harness-only
hook (key Z, in memory, never in the game) nudges the stage machine for the screenshots; the drawing, layout, keys, hold and panel are real.
The shots caught two real bugs (a Control under a CanvasLayer is never laid out, so the view had size 0; centred text anchors), both fixed.

**Not tested:** Windows, ANGLE/D3D11, the Intel HD 3000, real framerate, a real keyboard (including non-Latin layouts), audio (none exists),
long play sessions. The harness cannot judge how the haul *feels*; the balance numbers come from simulated players.

## 7. Windows manual checklist (about 10 minutes)

1. Run the game (F5 or your usual way). Press **E** at the helm, walk to the drum on the main deck, near the davit. Prompt reads "F  Work the fishing winch".
2. Press F at the harbour mouth (no fish): a sentence says where the nearest ground is; nothing else happens.
3. Sail to **Pilchard Shallows** (chart M, 0.6 km south-west of the cove), let the course hold run, walk to the winch, press **F**.
   The view fills the screen: sea, ship side, winch, rope, net. All text readable, nothing cut off at 1366x876.
4. Wait for "heaving to"; when the needle starts, press **Space** near the centre. The net goes down with a splash.
5. When the **HAUL** step shows, alternate **A D A D** at a steady beat. The net bar climbs, streak counts up, the tension needle stays in the green. Time it: about 8 to 12 s.
6. When "THE FISH IS ABOUT TO RUN" appears, stop pulling for a second, then resume.
7. Watch the net come up with fish in it; the card names the species, number and kg. Press **E**: fish fly into the barrel and you are back on deck with a message "Stored ...".
8. Press **E** at the barrels: picture, name, quantity, kg, total, capacity, free space. Walk to the fish market, sell; reopen the panel: the row is gone. The barrels on deck are empty.
9. Try failures: mash only **A** (the rope should snap and a red card explains why), press nothing during the haul (the shoal escapes), press **Esc** at the needle and again with the net down (clean exit, nothing stored).
10. During the view press **M**, digits, Tab, W: nothing should happen behind the view. After leaving, A/D/W walk the ship again and **M** opens the chart.
11. Open Project Settings > Input Map: change `fish_haul_left` to another key; the label on screen should change.
12. Report: did the view ever stay on screen, did any key stop working afterwards, whether the view feels smooth (the debug HUD is hidden while it is up; compare with the sailing view), and whether the haul feels too easy or too hard (tuning is in `data/tuning/tuning_mfish.json`).

## 8. Known limits

* Fish art is a first pass; the net and winch are drawn shapes, not final art. No audio. No fish in the 3D ship model's net.
* One species mix per cast (one or two species); no rare catches yet; no weather effect on the haul beyond the sea-state limit.
* The MAP button of the port HUD stays drawn over the view (its click is refused with a message while fishing).
* Windows and HD 3000 behaviour is unverified.
