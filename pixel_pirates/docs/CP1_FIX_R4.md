# CP-1 r4: fix for "set_views: Invalid access to property or key 'name' on a base object of type 'Dictionary'"

Build label (bottom-left on screen): **CP-1 test build r4 (2026-10-20)**.

## 1. The exact cause
- Function: `MapUi.set_views()` in `game/h2d/map_ui.gd` (called once from `PortGame.setup()`, `port_game.gd`).
- It builds one tab button per map view with `(views[i] as Dictionary)["name"]`.
- The Dictionaries are the three map views, baked into `game/h2d/art/anvil_cay.json` (`port.map.views`). They were created in `tools/h2d/city_map.py` (`CITY_VIEW`, `ISLAND_VIEW`, `SEA_VIEW`) and copied by `bake_cay.py`. Their keys were `id, title, file, bounds, ppm, zoom`. **No `name`.**
- Root cause = schema mismatch between producer and consumer: the window was written against a view with `name` and `hint`; the baker never produced either. I did not add a default `name`.

## 2. A second, hidden instance of the same bug
`MapUi._sync()` reads `v["hint"]` for the info line under the map. It does not exist either; it would have raised the same error as soon as a tab was selected. I found it while auditing every `["key"]` read in the map code.

## 3. Fix at the source
- The view schema is now defined where views are created: `tools/h2d/city_map.py` adds `tab` (short tab label: City / Island / Sea) and `hint` (one-line description) to each view. `anvil_cay.json` was re-baked (only that file changed; the map PNGs came out byte-identical).
- `map_ui.gd` reads `tab` for the tab buttons and `hint` for the info line. `title` still names the map ("MAP: Anvil Harbor").
- The window now declares the keys it reads (`VIEW_KEYS`, `ENTRY_KEYS`, `STATE_KEYS`, `RING_KEYS`) with `missing_keys()` / `schema_problems()`. On `set_views()` and `open()` it checks them, fills `schema_errors` and calls `push_error` with the key name and the view/entry id. A future mismatch is therefore reported by name, not as an abort half way through a function.

## 4. The other views and the marker/selection path
All three views (city, island, sea) share the same dictionary shape, so all three had the problem; all three are covered now. I audited every dictionary read in `map_ui.gd` against its producer: entries (`id, kind, name, detail, x, z`) come from baked places plus `port_game._entries()` (player, ship, places, recruits, grounds), the state (`entries, player, ship`) from `_map_state()`, the rings (`x, z, r, open`) from `_map_state()`. They all match. I did the same for the HUD, the dialogue window and the trade panel (the other `["key"]` reads against `set_data()`, `Dialogue.view()` and the trade/receipt builders): no mismatch found.

## 5. Why my earlier test run did not catch it
This is my miss. The Godot build I can run here (the WASM release template under Node) **returns null for a missing Dictionary key without any error** (confirmed with a three-line script; the editor's debug build raises the error you saw). The old selfplay never looked at the tab buttons, so it passed. "Tests passed" before meant logic only, not this.

## 6. Regression checks (all run in the Godot engine, headless)
- `test_port.gd` `_map_schema`: each baked view has every key the window reads, a tab label and hint, sane bounds, an existing picture; the views are city, island, sea in order; baked places carry the keys; the old shape (title, no tab/hint) must be reported as 2 named problems.
- `selfplay.gd` `_map_walk` (new): opens the map, then for every view: presses 1/2/3, checks the tab button texts, the title, the hint line, the marker count; arrows through all entries; asserts no control on the map shows "null".
- F8 UI diagnostic: two more lines (map schema empty; tab buttons read their labels).
- **Proof the checks detect the bug:** with the OLD `anvil_cay.json` the same tests fail (7 failures in `test_port`, 9 in selfplay, e.g. "map view 'city' has every key the window reads (missing: [tab, hint])" and "tab button 1 reads '1  <null>'"). With the fix: `test_port` 537 checks, 0 failed; `selfplay` 56 checks, 0 failed.
- Tooling: `tools/godot_node/run.mjs` gets `GODOT_RAW=1` to show the engine output unfiltered.

## 7. Warnings you mentioned
I have not seen your actual log lines, so this is partial; please paste them if anything below does not match.
- **OpenGL 3.3 / ANGLE message**: expected on the HD 3000. The project has `fallback_to_angle = true`; when the native OpenGL driver is below 3.3 Godot switches to ANGLE (OpenGL ES over Direct3D 11) and prints a notice. It is not an error and does not break logic; it only tells you which driver draws (possible speed cost, nothing functional). Not verified by a log from your machine.
- **GDScript warnings** (integer division, shadowing, unused variables): in Godot these do not stop a script from running. The static scan (gdlint and my heuristic) shows nothing that changes behaviour in the CP-1 files. I cannot see the editor's warning list, so I cannot say which ones you see. Only red errors (like this one) abort a function.
- Cleanup of those warnings is left as the separate item you named.

## 8. Test instructions
1. Replace your project folder with the new ZIP (open `game/project.godot`), press F5. Bottom-left must read "CP-1 test build r4".
2. Check the Output panel at start: the red `set_views` error must be gone. Any other red line: copy it.
3. Press **F8** (not inside a panel): toast "SELF-CHECK CP-1: N checks, 0 failed -> PASS". If a line fails, copy the toast and the Output text.
4. Press **M**: the map opens with three tab buttons "1 City", "2 Island", "3 Sea", a title "MAP: Anvil Harbor" and a hint line under the map. Press 1, 2, 3 and Tab to switch; click a marker or use Up/Down, Enter to track; Esc closes.
5. Then the rest of `CP1_REVISION_R3.md` section 6 (dialogue with Pip, fish market, fishing cues, hiring).

## 9. Honest status
- Verified by running in the Godot engine, headless (no renderer, no window): the logic, the data schema, the controls' text and counts. Static: Python checks, `check_all.py`.
- **Not verified:** that the map or any UI is drawn correctly on screen, layout in a real window, fonts and portraits as seen, colours, framerate. None of this has been run with a renderer by me.
