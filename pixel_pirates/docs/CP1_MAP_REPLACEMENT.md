# CP-1: the map system, replaced completely

**Status: written and tested headless and in a software-rendered browser build of the engine. NOT tested on Windows, NOT tested on
the HD 3000, NOT tested in the desktop Godot editor.** I cannot say the problem on your PC is fixed. I can say the new map is a
different, much smaller design that removes every weakness I could find in the old one, and that it shows an error instead of
failing silently. Please run the manual checklist below.

## 1. Old root cause (honest version)
The real cause on your PC was **never proven**; I could not reproduce your machine. What I found:
* One reproduced mechanism (fixed in r6): F1 opened the debug console, whose text field swallowed the letter M.
* The old path had **five hops** (raw key tap, `_unhandled_input`, `PortGame.handle_key`, `_open_map`, `ui.map.open`), all depending on
  the port controller having started. Any failure in any hop was **silent**: no message, no log line the player could see.
* A fixed-pixel layout, no Input Map action, no on-screen button, and the map was part of the port UI, so a port UI problem
  disabled the map as well.

## 2. New architecture
| File | Role |
|---|---|
| `game/ui/map/map_screen.tscn` + `map_screen.gd` | One self-contained `CanvasLayer` (layer 90): tabs, picture frame, markers, list, Close, zoom, pan, "MAP [M]" button. |
| `game/ui/map/map_model.gd` | Pure data: loads/validates the views, maps world metres to picture pixels, normalises the live state. No nodes. |
| `game/h2d/art/map_views.json` | The three views: City, Island, Sea (picture file, world bounds, pixels per metre). Written by `tools/h2d/bake_cay.py`. |
| `game/ui/map/map_sandbox.tscn` | F6 sandbox: the map alone with made-up data, no game. |
| `project.godot` `[input] open_map` | The single Input Map action for M (physical M plus the key labelled M). |

Rules the design follows:
* **One way in.** Only `map_screen.gd::_input` reads `open_map`; nothing else in the game opens or closes the map (no duplicate
  handlers). The corner button calls the same function. A focused button, other keyboard layouts (physical key) and the dialogue
  window cannot swallow it. A focused text field still wins (typing "m" in a text box must not open the map), and a dialogue
  gets a toast ("Finish talking first").
* **Works ashore, at the pier and at sea**, with no dependence on the port controller. If the port is off the map still opens.
* **Layout is containers.** The picture is inside a clipped frame in its own area, so it cannot cover the tabs or the Close
  button; layout is verified at 800x600 up to 2560x1440 and in the real renderer at 1366x876.
* **Safe state.** Opening changes nothing in the game. The host (`h2d0.gd`) pauses the clock under the reason `"map"` on `opened`
  and resumes it on `closed` (reasons are separate, so a pause the player set with P survives exactly). Every way out (Esc, M, Close
  button, node leaving the tree) emits `closed` once. A watchdog releases a stuck `"map"` pause if no map is open. While open,
  the ship and walker ignore held keys.
* **Errors are visible.** Missing/damaged picture, missing views (built-in three are used), a damaged scene (an emergency
  window with Close), or a failed open all show a red notice and a toast, count in `fail_count`, and write
  `user://map_diagnostics.txt`. The F8 self-check and the top-left debug text include the map's state
  (`map: closed, tab 0 of 3, opened 3 times, failed 0`).
* Old code removed after grep confirmed nothing used it: `h2d/map_ui.gd`, its node in `port_ui.gd`, the map term in `any_panel_open`,
  the open/close code in `port_game.gd`, and `tests/map_key.gd`. `port_game.gd` now only supplies live entries (`bind_map`).

## 3. Controls
M toggles; Esc / Close button / M closes. 1/2/3 or Tab: City / Island / Sea. Mouse wheel, `+`/`-`, buttons: zoom. Drag, middle drag, WASD
or arrows: pan. Up/Down select a row, Enter or T tracks, C clears tracking, Home or "Find me" recentres on you. Click a marker or a list row
to see its details. Shift+M is still the ship-motion toggle.

## 4. Tests that were actually run (WASM headless Godot 4.7 template in Node + Chromium software GL)
| Test | Result |
|---|---|
| `tests/test_map_model.gd` (model, views, state normalising) | 67 / 0 failed |
| `tests/map_screen_test.gd` (standalone; SubViewports 800x600 to 2560x1440; real key and mouse events; all 3 tabs; zoom, pan; missing picture / views; init failure; Close) | 203 / 0 |
| `tests/map_sandbox_test.gd` (sandbox scene alone) | 1 / PASS |
| `tests/map_flow.gd` (inside the real game scene: M at sea, ashore, at the notice board, with a focused Button, Arabic layout, Close button, 30 open/close cycles, pause reasons identical before and after, ship and walker held keys, dialogue blocks the map and works afterwards, nets timer frozen while open and running after, recruiting then the map, P pause preserved, watchdog) | 54 / 0 |
| `tests/audit_r6.gd`, `selfplay.gd`, `test_port.gd` updated to the new map | pass |
| Full suite (`tools/godot_node/run_suite.sh`) | before the last small edits: 30 of 31 with one audit failure; I fixed the audit test (it assumed the old modal map) and re-ran those scripts: all pass. A complete suite re-run after the very last lint edits was run per file (map tests above) not as one batch. |
| `tools/check_all.py` (check_project, docs, gdlint, gdparse) | ALL PASSED (Godot step SKIP) |
| Real-renderer run at **1366x876** (`tools/godot_browser/scenarios/map_screen.mjs`): corner button click opens it, 3 tabs, zoom, drag pan, Esc, ashore M, Arabic M, walking after close | screenshots in `docs/map_shots/`: tabs and Close fully visible, picture inside its frame |

What these do NOT prove: Windows, ANGLE/D3D11, the HD 3000, real fps, your keyboard, and whether the old failure had the same cause as anything
I tested.

## 5. Known limits
* On the Island tab the 18 places of the city sit close together at the harbour (zoom in to separate them).
* The headless engine has no window, so layout was proved with SubViewports and the browser renderer, not the desktop window manager.

## 6. Manual test checklist (please run, Windows, Godot 4.7.2)
1. Open `game/` in Godot, press **F6 on `ui/map/map_sandbox.tscn`**. Press **M**: a map window with Close, 3 tabs and a picture should
   open. Esc closes. If this fails, tell me what the top-left text and the Output panel say.
2. F5 the game. Press **M** at sea: Sea tab; ship stops moving; press M or Esc, the ship moves again.
3. Click the **MAP [M]** button (bottom right): same.
4. Tabs 1, 2, 3 each show their own picture, labels readable, you are marked.
5. Wheel zoom, drag to pan, **Home** returns to you. The picture never covers the tabs or Close at any zoom.
6. Press F9-style walking: SPACE at the pier, F ashore; M ashore opens City. WASD moves the chart, not you; after Close you walk.
7. Talk to Pip (E): M says "Finish talking first"; after Esc M works. Hire Pip (F6 for money), the map marks him "aboard your ship".
8. Fish in the Pilchard Shallows (F): open the map during fishing: nets pause; close: they continue.
9. Try a non-Latin keyboard layout (e.g. Arabic): M should still open it.
10. Open and close 20 times quickly; then check the game is not paused. Press **F8** and send me the result, plus
    `%APPDATA%/Godot/app_userdata/<project>/map_diagnostics.txt` if it exists.
