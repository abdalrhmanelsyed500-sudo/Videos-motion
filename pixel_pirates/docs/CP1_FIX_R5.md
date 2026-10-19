# CP-1 r5: the two blockers (M map, walking onto the island)

Build tag in game: `CP-1 test build r5 (2026-10-20)`.

## Honest status first
| | |
|---|---|
| **P2 walk onto the island** | Root cause found and proven, fixed, regression tests added. |
| **P1 M does not open the map** | **NOT reproduced.** In a real renderer (below) and in the headless tests, M opens the map and M/Esc close it, at sea and ashore, in all three views, with a US and an Arabic key event. I did not find a code path that eats the key, so I cannot honestly say "the cause of what you saw is fixed". What I did find and fix are three real defects in the same feature, and I added a diagnostic so that if M still fails on your PC, the screen tells us why. Details below. |

## A renderer was found (for the first time in this project)
`@sparticuz/chromium` + `puppeteer-core` give headless Chromium with **WebGL 2 on SwiftShader (software)**, which runs the Godot 4.7.2 web
template with the **Compatibility (OpenGL ES 3) renderer**: `tools/godot_browser/` (README there). Screenshots in `docs/r5_shots/` were
SEEN by me and come from that run. It is software rendering at ~8 fps, NOT your HD 3000, NOT Windows/ANGLE: it says nothing about
speed or about driver-specific problems. It does show what the game's own UI and 3D scene draw.

## P1: what was checked
Chain: key event -> `h2d0._unhandled_input` -> `PortGame.handle_key` -> `KeyUtil.code` -> `_open_map` -> `MapUi.open`. Tested with real DOM
key events at 1280x720 and 1366x876 (your size): at sea M opens the Sea tab, M closes; ashore M opens the City tab; Esc closes; a key
event with the Arabic character and physical M opens/closes it. Digits 1/2/3 switch City/Island/Sea. No open-then-close, no other handler
eating the key, no 0x0 panel. Shift+M still toggles ship motion; key-repeat does not toggle.

### Defects found and fixed in the map (visible in the r4 screenshots `docs/r5_shots/r4_*`)
1. The **tab buttons were cut off** by the map picture (tab row ended at y 79, picture started at y 64): "1 City / 2 Island / 3 Sea" were half hidden.
2. The **sidebar was wider than its panel** (a long line widened every row to 324 px): cards ran over the panel border.
3. **A failed open left the game stuck**: `MapUi.open()` set `visible = true` first; if anything later failed, the game stayed in map mode with the clock paused and every key swallowed. Now `open()` returns whether the map is really shown; if not, the open is undone, the clock resumes and a red message with the reason appears (and `push_error`).

### New diagnostic (read this if M still does nothing for you)
The debug text (top-left, F3 hides it) has a new line **`last key: keycode K physical P -> C (NAME) mode none|map|...`**. Press M and read it:
- the line changes to `... (M) mode map` and no map shows: tell me, it is a drawing problem (send the red message if any);
- the line changes with `mode none` and nothing happens: the key arrives but is not handled; send the line;
- the line never changes: the game window does not receive the key. **If you start with F5 from the editor, Godot 4.7 may embed the game in the editor's "Game" tab: click inside the game once, or set Run -> "Run Game Floating"/disable "Embed Game on Next Play".** That is a hypothesis; I cannot test the editor.

### Tests
- `game/tests/map_key.gd` (37 checks): real `InputEventKey` through the viewport: toggle changes visibility, City/Island/Sea, sea and ashore, Latin + Arabic layout, Shift+M, echo, tab-row and sidebar layout, failed open leaves no modal/pause.
  Run: `node ../tools/godot_node/run.mjs . --fixed-fps 60 --script res://tests/map_key.gd` (from `game/`).
- **On r4 code the same file fails 4 checks**: tab row (40 + 39 high > picture at 64), sidebar row 324 px > 280, failed open leaves modal state, leaves the clock paused. The key-toggle checks PASS on r4, which is consistent with "not reproduced".
- Real renderer scenarios: `tools/godot_browser/scenarios/map_open.mjs`, `map_ar.mjs`, `map_ashore.mjs`.

## P2: cannot walk onto the island (root cause, proven)
The CP-1 `shape()` left a 0.15 m -> 1.58 m jump between the first two shore rings 2 m apart: bilinear slope ~0.70 against `walk_max_slope` 0.55, so the pier landing was a dead band ~0.5 m wide (z 1.4..1.9). Every earlier check sampled 1-2 m and missed it.
Fix: `shore_ramp()` in `tools/h2d/city_layout.py` (rings 0.95/1.75/1.95, slope 0.40), applied by `bake_cay.py`; re-baked (1048 blockers). Cliffs, buildings, walls and the notice board stay solid.
Tests: `game/tests/test_walk.gd` (44 checks, ~35 s) with `h2d/walk_audit.gd`: fine landing profile, strict flood fill (every walkable cell reached from the pier), the real `LandWalker` driven pier -> every place and recruit, wall crossings only at stairs, island-wide walk. **On the r4 data it fails 16+ checks (the pier reaches 148 of 98,925 walkable cells, every place unreachable, 183 people cut off).**
`tools/h2d/check_harbor.py` was updated: the first 2 m cell of the pier is now the shore ramp (0.96 m, deck 1.0 m).

## Verification run (all headless WASM Godot unless stated)
test_port 537/0, selfplay 56/0, test_walk 44/0, map_key 37/0, load_all 86 scripts (4 RegEx-only failures, as before), `check_all.py` ALL PASSED, check_port PASS, check_land PASS (pier region holds 100 % of walkable cells; longest walk 955 m = 4.0 min).
Not verified: the Windows build, the HD 3000, audio, the editor import of the changed height/biome PNGs (Godot will re-import them on first open).

## Manual checklist (your PC)
1. Open the project (let the editor re-import), run. Bottom-left tag must say **r5**.
2. At sea press **M**: the map opens on the Sea tab with three tab buttons fully visible. **M** or **Esc** closes. Try 1/2/3.
   If nothing happens: read the `last key:` line (above) and send it to me.
3. Press M with the Arabic layout too.
4. SPACE to dock at the pier (or follow the on-screen prompt), **F** to go ashore. Press **M**: City tab opens.
5. Walk (WASD) up the pier: you must step onto the quay with no invisible wall. Walk to Silas Reed, the fish market (W), the tavern (NE). Walls (the three terrace walls) should block you except at the stairs; buildings stay solid.
6. Press **E** next to a recruit (dialogue), **F6** (+25 reales) and sell at the fish counter as before.
Known leftovers (not changed on purpose): the map picture does not fill the whole map window in the City view; two markers (market square, battery) sit near unwalkable ground (the place tolerance is 8 m); the debug text overlaps the "IN IRONS" banner.
