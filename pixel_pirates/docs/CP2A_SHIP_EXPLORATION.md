# CP-2 Release A: Ship Exploration & Sailing Autopilot

Build tag: see the title line in the game. Release B (manual first-person fishing) is **not** in this release: the winch is built and
approachable, and says so when you use it.

## What is new

* **Course hold (autopilot), key C.** Holds the heading you had when you pressed it and sails at the speed the wind allows on that
  heading (the sails decide speed as before). If the held heading points into the wind (inside the red no-go wedge plus 6 degrees)
  the hold steers the nearest heading the sails can use, so an unattended ship never stalls in irons; the status chip says so.
  A or D at the helm steer by hand; half a second after you let go the hold takes the new heading. The hold does **not** avoid
  land or other ships: it is a heading hold, not navigation. Docking (SPACE) or casting off releases it.
* **Status chip (bottom centre):** `STEERING: DIRECT` or `COURSE HOLD 027 NE`, with the place you are in (MAIN DECK, SLEEPING DECK,
  PROVISIONING HOLD, CROW'S NEST).
* **E = ship interaction** (new Input Map action `ship_interact`; C is `autopilot_toggle`). At the helm E leaves the wheel (the
  hold engages by itself so the ship keeps her course) and puts the pirate on the deck. On deck E uses what the prompt shows
  (take the helm, chart table, chest, winch, barrels, berths, hatches, rope ladder, provisions racks). At the pier E remains the
  port/dialogue key.
* **A real 3D ship you can walk on** (HD-2D look, same camera): three decks, a crow's nest, and a pirate who moves with the ship.
  * Main deck: wheel, captain's cabin (door, desk with the chart = opens the map, sea chest, bunk, lantern; the roof turns
    see-through when you step inside), mast and rigging, ordinary barrels, crates, coils, planks, **fishing winch** (oak drum, rope,
    davit and pulley, net), **fish barrels** (0 / 2 / 4 barrels full according to the real hold: empty at 0 kg, full near 40 kg;
    selling at the port empties them at once), hatch down, rope ladder up.
  * Sleeping deck: hammocks and bunks, sea bags, crates, beams, lanterns (enclosed lighting), hatch up and down.
  * Provisioning hold: racks of sacks, crates and food barrels. E at the racks lists the real provisions in the hold (same items
    as the port economy; no second inventory). Shift+F6 adds a test provisions pack.
  * Crow's nest: climb the rope ladder (about 3 s), wider lookout view.
* The helm HUD is hidden while you walk. The bottom key line shows the walking keys.

## Keys

| Key | Action |
|---|---|
| A / D | Steer (at the helm) |
| C | Course hold on / off |
| E | Leave the helm / use / climb / take the helm |
| W A S D, Shift | Walk, run (on deck) |
| M | Map (also at the chart table) |
| SPACE | Dock / cast off |
| F | Nets while sailing; ashore when moored **and on the main deck** |
| Esc / E | Close a panel |
| Shift+E | Effects budget (this used to be plain E) |
| Shift+F6 | Test provisions pack |
| F7 | Test fish (+10 kg mackerel) |
| R | Reset the ship |

Tuning (walking speed, climb time, zoom, autopilot gains): `game/data/tuning/tuning_ship.json`.

## Manual checklist (Windows)

Start the game (F5, or the exported exe). Click once in the window so it has keyboard focus.

1. **Helm and hold.** The chip says STEERING: DIRECT. Press C: COURSE HOLD with the heading. Let go of the keys: the ship keeps
   the heading for 30 s. Tap D: she turns, then holds the new heading. Press C again: direct steering.
2. **Leave the helm.** Press E at the wheel: a toast says the ship keeps her course; the camera pulls out to show the deck; the
   pirate stands behind the wheel. Watch the sea move past: the ship must not stop or turn.
3. **Walk.** WASD to walk, Shift to run. The pirate must stay on the ship while she moves and turns. Walk into barrels,
   the mast, cabin walls: you stop; you never get stuck; every aisle is passable.
4. **Take the helm.** Walk to the wheel; the prompt says "Take the helm"; E. The chip returns to direct steering (or hold, if
   it was on) and you can steer.
5. **Captain's cabin.** Walk in through the door: the roof turns see-through. E at the desk opens the map; close it with M or Esc.
   E at the chest and the winch shows a short text.
6. **Fish barrels.** Press F7 twice (20 kg): two barrels fill. Press E at the barrels: panel with the fish; Esc closes. Sail
   home, sell at the port: the barrels are empty at once.
7. **Hatch down (main deck to sleeping deck)**: walk onto the hatch, E: short fade, you stand on the ladder landing below. The
   hammocks, bunks and lanterns are visible. Walk around. **Hatch down again** to the hold, and **back up twice**. Check every one of
   the four directions: position sensible, camera follows, no stuck pirate.
8. **Hold.** Press Shift+F6 to get provisions; E at the racks lists them. Walk between the racks.
9. **Rope ladder.** On the main deck go to the rope ladder, E: the pirate climbs (about 3 s) to the nest; the camera rises
   and widens. E at the top: climbs down. Try pressing S or W half-way: the climb reverses and ends on the deck, not in mid-air.
10. **Walking while the ship moves:** do steps 7 to 9 with the hold on and the ship sailing at speed.
11. **Docking.** Take the helm, steer into the harbour, SPACE: the hold is released and the ship docks as before. Leave the
    helm at the pier: F goes ashore only from the main deck. Cast off with SPACE: the pirate is at the helm.
12. **R** while on a lower deck: the ship resets and the pirate is back at the helm.

Also check: the 1366 x 876 window: status chip, prompt and toast must not overlap each other or the panels.

## What was verified, and what was not

* **Automated, headless (WASM Godot template, logic and scenes, no pixels):** `test_ship_layout` 205, `test_ship_walker` 80,
  `test_ship_autopilot` 25, `test_ship_view` 30, `test_ship_stores` 26, scene test `deck_flow` 68 checks in the real
  `h2d0.tscn` (E leaves the helm, hold keeps the heading, walking does not steer, camera follows ship plus pirate, desk opens the map,
  hatches both ways, ladder up and down with reversal, barrels follow the hold, panels block walking, F ashore rules, R reset).
  Full suite 38 passed, 0 failed (includes the earlier tests and the map tests).
* **Real renderer (software OpenGL ES 3 in headless Chromium, 1366 x 876, ~8 fps)**: `tools/godot_browser/scenarios/deck_walk.mjs`
  with screenshots in `docs/cp2a_shots/`: helm, course hold, main deck, barrels, cabin, ladder, nest, sleeping deck, hold. This
  proves the shader compiles and the scenes draw. In those runs the pirate was placed by harness-only key hooks (Q U I O J K L H V,
  in memory only, not in the game); the transitions themselves are covered by `deck_flow`.
* **NOT verified:** Windows, the Intel HD 3000, real frame rate, audio, the editor import step.

## Known limits

* Course hold does not steer around land: in the renderer run the ship ran aground on Anvil Cay while on hold (the existing aground
  state applies, press R or turn away).
* The ship shows half of the sea motion on deck (tuning key `deck.motion_scale`); no extra real-time lights (two to four lantern
  terms in the shader only).
