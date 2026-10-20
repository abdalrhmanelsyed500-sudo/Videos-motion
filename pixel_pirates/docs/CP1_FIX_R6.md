# CP-1 r6: stability release (deep audit, root-cause fixes, pre-test verification)

Build tag in game: `CP-1 test build r6 (2026-10-20)`. No new city, no new gameplay. This release only fixes what the audit found and adds
tests and diagnostics so that a failure names its own stage.

## Honest status first

| | |
|---|---|
| **P1 "M does not open the map"** | **Still NOT reproduced as a plain M bug**: in every harness M opens the map (sea, ashore, all three views, Latin and Arabic layout, at 800x600, 1280x720, 1366x876). **One mechanism that matches your symptom WAS reproduced and removed**: in r3-r5 the debug console opened on **F1** and its text field then ate M, A and D (below). I cannot know whether that is what happened on your PC. If M still fails in r6, the new key line (below) tells us at which stage. |
| Walking, connectivity | Re-audited with stricter limits. One real defect found by the in-game F8 check (a sailor standing inside a blocker), fixed. |
| Pause bug (nets, people kept working under the map) | Found and fixed. |
| Windows / HD 3000 / ANGLE / fps / look on your screen | **Not verified.** I have no Windows, no GPU and no desktop Godot. See "Not verifiable here". |

## What the tests ran on (read this before trusting any number)
- **Godot 4.7.2 WASM release template in Node** (`tools/godot_node/`): runs the real GDScript, parses every script, steps the real scenes.
  No renderer, no audio, no imported textures, window size 0x0, no RegEx module, terse errors, and **script errors in a release template
  are silent** (a missing Dictionary key returns null instead of raising), so every test asserts on RESULTS.
- **Same template inside headless Chromium** (`tools/godot_browser/`): real OpenGL ES 3 drawing on SwiftShader (software, ~8 fps), real
  key events. Screenshots were looked at. It is NOT your HD 3000, not Windows, not ANGLE.
- Python checks (`tools/check_all.py`) are static or mirror code; they say "NOT Godot" in their name.

## P1: the M map, stage by stage

| Stage | Result |
|---|---|
| Physical vs logical keycode (Arabic layout) | `KeyUtil.code` uses the physical key for non-Latin layouts; tested: Arabic ة with physical M opens and closes the map, ashore and at sea (`map_key.gd`, browser `map_ar`). |
| Embedded window focus, clicks | Cannot be tested here. New HUD line says `keys: engine got 0 (none yet: click once inside the game window ...)` or `WINDOW NOT FOCUSED`. |
| Event consumption by a focused control | **Reproduced, see F1 below.** New HUD text names the focused control. A test (`audit_r6.gd`) shows a key typed into a focused text field is counted by the engine but never reaches the game, and the HUD says so. |
| Shortcut conflicts | Only two input handlers exist outside the game scene: `DebugConsole` and `MapUi`. The console is the conflict (below). Godot's own editor shortcuts (F5, F6, F7, F8...) can only be judged on your machine: see checklist. |
| Map instantiation, layering, size | `PortGame.setup()` now records `setup_stage` / `setup_error`. If it stops, the HUD shows **PORT CONTROLLER OFF (setup stopped at: ...)** and pressing M prints **MAP UNAVAILABLE ...** instead of silently toggling the ship-motion mode (the old fall-through). Also written to `user://h2d0_diagnostics.txt`. Layering/size: panel 1232x688 at all tested window sizes; tab row and sidebar inside the panel (`map_key.gd`). |
| Runtime exceptions | In a debug (editor) run any script error **breaks into the debugger and freezes the game**; release templates hide it. I scanned the M path for debug-only behaviour: no `assert`, no `is_debug_build()` branch except the console. Map schema, malformed views, a missing map picture, an entry without coordinates, no views at all: tested, reported by name, never left modal. |
| Pause and restore | A failed `open()` leaves no modal state and no pause (tested, r5 and r6). Esc closes a broken map. |
| The three views' data | City / Island / Sea: markers present, schema complete (tested for each view). |

### The F1 finding (reproduced)
`DebugConsole` toggled on F1 or the backtick and swallowed the key. My r3-r5 notes listed "F1 quality" among the keys. In a debug run (F5 from
the editor) pressing F1 opened the console, its text field took the keyboard focus, and every later key (M, A, D, ...) was typed into it.
- Reproduction with the **unchanged r5 console code** (headless, a real key event for F1 then M with its character): the console panel is
  visible, the focus owner is a `LineEdit`, the engine saw the M key, the game saw 0 keys, the map did not open.
- Fix: the console opens on the **backtick only** (physical key too, so Arabic layouts work), Esc closes it, F1 goes to the game (quality).
  The HUD shows `DEBUG CONSOLE IS OPEN` while it is open. `is_open()` added.
- The release template removes the console, so the browser run of `f1_then_m.mjs` cannot show it; the unit-level test does
  (`audit_r6.gd` builds a console with `force_enabled`).

### New diagnostic: the key line (top-left debug text, F3 hides)
`keys: engine got N, game got N | routed N, map opened N, failed N | last key: keycode K physical P -> C (NAME) mode ...`
- `engine got` counts key presses seen by the game scene's `_input`; `game got` counts those that reached `_unhandled_input`.
  **engine > game**: a UI control swallowed the key (the line also says `FOCUSED CONTROL: <name>`).
- `routed`: reached the port controller. `map opened / failed`: results of `MapUi.open`.
- `PORT CONTROLLER OFF (setup stopped at ...)`, `DEBUG CONSOLE IS OPEN`, `WINDOW NOT FOCUSED`: the other failure stages.

## Audit results (what I looked at, what I found)

| Area | Finding | Action |
|---|---|---|
| Walking / connectivity | Reachability checks were looser than the movement rule. The real in-game F8 self-check failed: `npc_sailor_1 stands on walkable ground` (a sailor baked at (29.0, 0.2) inside a 2.5x3 m blocker; the Python mirror cannot see it). | New check in `test_walk` (fails on r5 data, 1 person); sailor moved to (31.8, 0.2); F8 now reports 737 checks, 0 failed in the browser run. |
| Walking, tolerances | Places only needed to be within 7 m, people within 1.6 m of reachable ground. | Places now 3.5 m (actual worst 3 m: the market-square fountain), people 1.2 m (actual worst 1.0 m). The real `LandWalker` now walks from the pier to **every** place, recruit, interaction and every 12th person (was 8 hand-picked targets); all arrive. Obstacle tests (walls only at stairs, 300+ building blockers solid, no house enterable) unchanged and green. |
| Fishing grounds | Reachable by sea? Identifiable? | New `test_walk` check: a hull-footprint flood fill (8 m, 5 probes, the game's own aground rule) from the start reaches the middle and 8 points inside the rim of all four grounds. They are identifiable: name + blurb in data, a beacon and 10 buoys per ground (`build_cues`), a ring on the Sea map, the nearest-ground message when you press F outside one. |
| Pause | `h2d0._process` called `PortGame.step` even when the clock was paused or a panel was open: hauls continued under the map and the clock-frozen catch never spoiled (a catch farm), people kept walking. | `paused` added to the port context; nets and people wait while paused or modal (`audit_r6.gd`: 40 s paused -> 0 hauls; the same 14 s running -> a haul). Fails on r5. |
| Money | A dialogue `pay` action with a negative argument would add money. Hire with too little money returned silently. | Clamped (`maxi(cost, 0)`); a toast says how many reales are missing. Tested: negative pay never adds, poor hire refused and changes nothing, hire twice charges once, selling the same hold twice pays once. |
| Starter money | Docs say 5 reales (CP-1) while B4 says 600 (documented conflict, open). | New `tools/h2d/check_docs.py` (in `check_all`): purse, hold, haul interval, spoilage, sea limit, depth, 5 prices, 4 recruit costs, 4 grounds (position, radius, richness, distance, "needs a hand") must equal the data. All consistent. The 5 vs 600 reading is still an open ledger item for B4. |
| NPCs and dialogue | `_open_dialogue` returned silently when the fishmonger record was missing; the notice-board label was used for any non-market interaction; an unknown track target was stored. | Toast + warning for a missing person; the label is chosen by interaction kind; unknown targets are refused. **Dialogue audit**: for all 183 people, every node of the tree they speak, 4 purse/hold/crew situations: no unresolved `{placeholder}`, no empty option, no dead end, every `next` exists. The recruit option and fishmonger sell option behave as designed (`selfplay`, `test_port`). |
| Economy code | `PortState` (sell, hire, effects, spoilage), `Fishing` (can_start, step, stop): read in full, no stacking or double-pay path found beyond the ones above. R during active nets: the ship leaves the ground and the nets stop with a message. |
| City data vs docs | The docs said **28 people** (CP-1 text, Canon) and **184 people** (r3 text, city plan); the bake has **183** (183 distinct ids; one of the 184 planned spots was rejected as blocked). | Docs corrected to 183 (28 kept as the first-slice figure); `check_docs.py` now compares the people count in four docs with the baked count. Places 18, recruits 4, prices, costs, grounds already matched. |
| UI / window sizes | Looked at 800x600, 1280x720 (r5) and 1366x876: dialogue, hire menu, sell dialogue, map, F8 result. Everything fits and is letterboxed correctly. | Leftovers (not fixed, cosmetic): the city map picture does not fill the map window; marker labels overlap in the dense Fish Row; the debug text overlaps the "IN IRONS" banner at sea (F3 hides it); a toast can be partly hidden behind the dialogue options. |
| F8 accuracy | F8 runs the 537-check unit test plus 200 live checks on the real world. It was right (it found the sailor). In headless it skips the live part (no ground texture): the message says so. | None. |

## Test results (all with the WASM template + RegEx polyfill; see above)
`tools/godot_node/run_suite.sh` runs every `test_*.gd` one at a time (a single `run_all.gd` dies in the WASM runtime at `test_island_map`),
then `selfplay`, `map_key`, `load_all`, `audit_r6`: **29 passed, 0 failed** (first complete run after all fixes; re-run at the end, see the final report).

Test classification of the earlier failures:
- **`load_all` RegEx failures: ENVIRONMENTAL.** Without the polyfill exactly 3 scripts fail (`core/ids.gd`, `core/schema.gd`,
  `core/console_commands.gd`), and they are exactly the 3 files that contain `RegEx` (`grep -l RegEx`); the errors are `Identifier "RegEx" not declared`.
  The npm WASM template has no RegEx module. With the polyfill: 90 scripts, 0 failed, and registry/schema/save/ids/console tests pass.
  (Desktop Godot builds include the RegEx module; I did not run a desktop build here.)
- **Four TEST defects fixed** (the tests had never run in Godot before): `String.contains("")` is false in Godot 4 (empty expectations in
  `test_console`); JSON numbers are floats and `[640.0, 360.0] == [640, 360]` is false (`test_quality`); the item count in
  `test_console` was 16 but B4 added 9 trade items; `test_island_map` had two `:=` on untyped calls (a real parse error in desktop Godot too);
  `test_ocean` compared ties in an unstable sort (3 species-table cases with equal scores in a different order than Python's stable sort).
  None of these was a game defect.
- A leftover environment limit: headless has no terrain textures, so live walking cannot be tested there; `test_walk` reads the PNGs itself.

### New regression tests, and whether they fail on the old code
| Test | Guards | On r5 code |
|---|---|---|
| `audit_r6.gd` F1 / backtick / Arabic backtick / Esc / focused field / key counters | dead keys | Old console: F1 opens it, focus is a LineEdit, M never reaches the game (reproduced separately, see above). The test also needs the new API, so on r5 it stops at the first new call. |
| `audit_r6.gd` pause rules | catch farm under the map | **FAIL** on r5: "40 s under a paused clock bring no haul (timer 4.0)" |
| `audit_r6.gd` negative pay | free money | **FAIL** on r5: "5 -> 55" |
| `audit_r6.gd` setup failure, malformed docs, bad map data, invalid targets, dialogue audit | silent failure | new behaviour (stage/error API), no r5 equivalent |
| `test_walk.gd` baked people on walkable ground | the F8 sailor | **FAIL** on r5 data: 1 person, `npc_sailor_1 (29.0, 0.2)` |
| `test_walk.gd` stricter reach, walker to all places/recruits/people, sea routes | P2-style gaps | PASS on r5 data (no defect found there) |
| `check_docs.py` | doc drift | PASS (no drift) |

## Controls (unchanged except the console)
Sea: A/D steer, Z/X sensitivity, F nets (inside a ground, slow), SPACE dock / cast off, M map, F ashore (moored), 1-7 weather, N time, P pause,
Shift+M ship motion, R reset, **F1 quality**, F2 path, F3 hide debug text, F4 colour transfer, F8 self-check, F12 screenshot.
Ashore: WASD, Shift run, E talk / sell / read, M map, F board (at the pier), T next stop. Map: 1/2/3 or Tab views, +/- zoom, WASD pan,
Up/Down select, Enter/E/T track, C clear, Home centre, Esc/M close. Test helpers: F6 +25 reales, F7 +10 kg mackerel.
**Debug console: the backtick key (left of 1), not F1.**

## Manual checklist for you (10 minutes)
1. Open `game/` in Godot 4.7, let it re-import, press F5. Bottom-left tag says **r6**. **If the game runs embedded in the editor's Game tab, click inside it once.**
2. Read the key line in the top-left debug text. Press M: `engine got` and `game got` go up by 1, `map opened` goes to 1, the map shows. Esc closes.
3. Press **F1**: the quality name changes, no console appears. Press the backtick: the console opens (debug builds), the key line says DEBUG CONSOLE IS OPEN; Esc closes it.
4. **If M still does nothing**, copy the key line exactly and the contents of `user://h2d0_diagnostics.txt` (Godot: Project > Open User Data Folder). Also tell me whether the editor Debugger tab shows a red error or a "break".
5. Press **F8** once (if the editor stops the game on F8, run the game in its own window: Editor Settings > Run > Game Embed Mode off): expect `SELF-CHECK CP-1: 737 checks ... 0 failed -> PASS`.
6. Sail to the Pilchard Shallows, press F, open the map (M) and wait 20 s: **no haul while the map is open**. Close it: hauls resume.
7. Dock, press F, walk (WASD) to Pip Larkin (east of the plaza), E, try to hire with 5 reales (a red "short" line and a message), F6 twice, hire.
8. Walk west to the fish counter, E, sell. One money update, one toast.

## Known limitations / not verifiable here
- **Not verified at all**: Windows, ANGLE/D3D11, the Intel HD 3000, real fps, how it looks on your screen, audio, the editor import step, Godot's Debugger behaviour on your machine.
- **Not reproduced**: your "M does nothing". The F1 console is a reproduced mechanism, not a confirmed cause.
- **Editor keys** (F5-F8, F12) can be taken by the editor when the game is embedded: cannot be tested here.
- Cosmetic leftovers listed in the UI row above. Open design item: purse 5 vs B4 600.
- The RegEx polyfill makes the harness compile the three RegEx scripts; it is a harness aid only and is not shipped in `game/`.

## Changelog r6
- Console: backtick only, `is_open()`, F1 free for the game.
- Diagnostics: key-stage line, focus owner, setup stage/error, MAP UNAVAILABLE message, user-data diagnostics lines.
- Fixes: world waits while paused/modal; `pay` clamp; hire-poor message; missing-person message; track-target validation; notice label by kind; sailor spot.
- Tests: `audit_r6.gd` (58 checks), `test_walk.gd` (86), 4 test defects fixed, `check_docs.py`, `run_suite.sh`, browser scenarios `f1_then_m`, `flow_r6`.
- Tooling: RegEx polyfill for the WASM harness, browser harness hooks F10/F11.
