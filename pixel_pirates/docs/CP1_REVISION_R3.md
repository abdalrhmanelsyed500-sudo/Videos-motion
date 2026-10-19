# CP-1 revision r3: functional systems and the capital redesign

Build label (shown bottom-left on screen): **CP-1 test build r3 (2026-10-19)**. If you do not see that line, you are running an older project folder.

## 1. What your test found, and what was done

| Report | What was done | Evidence level |
|---|---|---|
| Map did not work | Rebuilt from standard Godot Control nodes (`map_ui.gd`). Three views (city / island / sea), zoom, pan, click or arrow-select a marker, track it. **Every key now works on any keyboard layout** (`key_util.gd`: if the layout key is not a Latin letter, the physical key position is used; held keys A/D/W/S also check the physical key). | Logic and layout run in the Godot engine (headless). Drawing NOT seen. |
| Dialogue showed no portrait, name or text | Rebuilt as a Stardew-style box: portrait frame with a 48x48 portrait for each of 16 speakers, name plate, typewriter text, option rows, trade panel (`dialogue_ui.gd`, `dialogue.gd`, `data/port/dialogue.json`). | same |
| Fishing gave no visible feedback | Fishing panel (progress, hold, haul toasts) plus world cues: a beacon and 10 red/white buoys ring each ground, circling gulls, sparkles on the water, a trail of net corks and foam behind the stern while fishing. Details in section 3. | Cue code builds and updates headless. Looks NOT seen. |
| Anvil Cay did not look like a rich capital | Full redesign: see `docs/CP1R_CITY_DISTRICT_PLAN.md` (written first). 4 terraces, palace, town hall, barracks, exchange, 224 buildings, 184 people, walls and gates, avenue, lamps, fountains. | Bake and reachability checks (static). Looks NOT seen. |

### The honest root-cause statement
I could not reproduce "nothing is drawn" headless, because the engine I can run here (the Godot WASM build under Node) has no renderer and a 0x0 window. So the cause is **not proven**. Two causes were found and removed:
1. **Hidden-layer layout (probable).** A hidden Control layer is not laid out when its parent resizes; its size stayed 0x0 and the dialogue box sat at y = -232, off screen. Layer sizes are now set explicitly (`PortUi._fit()`); the F8 UI diagnostic that failed before now passes.
2. **Keyboard layout (plausible).** With an Arabic layout the keys M, E, F, A, D, W, S have no Latin keycode, so the map, interact, nets and steering could be dead. Fixed with the physical-key fallback everywhere.
To stop guessing, **F8 now measures the interface on your machine** (section 5). Because the UI is no longer a custom `_draw` layer, a blank result will name the exact control.

## 2. Changelog
- P1 map: `map_ui.gd` rewritten; three baked pictures `map_city.png`, `map_island.png`, `map_sea.png` (new city map, Pirata One font); markers: you, ship/pier, fish market, 4 recruits (colour by affordability), tavern, customs, exchange, palace, gates, fishing grounds, quest target (pulsing ring + arrow strip at the top). Tabs 1/2/3 or Tab.
- P2 dialogue: new files above; branching trees tied to real state (purse, hold, crew, unhired, ground visited); recruits show role, cost, "you can / cannot afford" and hire from the dialogue; shopkeepers and the fishmonger open the trade panel (sell one / sell all with money feedback).
- P3 fishing cues: `cue_sprites.py`, `port_cue_atlas.png`, `cay_world.build_cues/update_cues`, fishing panel in the HUD.
- P4 city: `city_layout.py`, `city_art.py`, `city_props.py`, `city_people.py`, `city_export.py`, `city_map.py`; terrain classes 12 slabs, 13 paver, 14 steps, 15 wall; city MultiMeshes; 1049 collision blockers.
- Tests: `selfplay.gd` (32 checks incl. cues), `test_port.gd` (431 checks), F8 UI diagnostic, `check_all.py` ALL PASSED.
- Keys: all keys routed through `KeyUtil`.
- Build label added (this document's first line).

## 3. Fishing: what you should see
1. Sail south of the harbour. Each ground is marked on the map and, at sea, by a **tall beacon and a ring of red and white buoys** (visible from afar), **circling gulls** and **sparkles**.
2. Inside a ring the top strip says you are on the ground and which species run there.
3. Slow below 1.5 knots (nets only work when slow and the sea is calm, sea state <= 0.6) and press **F**: the panel appears (progress bar, fish in hold), **net corks and foam trail behind the stern**, a toast on every haul (e.g. "+2.1 kg mackerel").
4. F again stops. At the fish counter (-77, -10.6) press **E**: sell panel.

## 4. Controls
Sea: A/D steer, F nets (inside a ground, slow), SPACE dock / cast off, M map, F ashore at the pier (and again to board), Z/X sensitivity, 1-7 weather, N time of day, P pause, R reset, G gust, F1-F4 / F12 dev toggles.
Ashore: WASD move, Shift run, E talk / use / sell, M map, F board at the pier, T teleport (test), Esc closes any panel.
Dialogue: Enter / Space / click advance (first press finishes the typing), W/S or Up/Down choose, 1-4 pick, Esc leave.
Map: 1/2/3 or Tab views, + / - or wheel zoom, WASD or drag pan, Up/Down or click select, Enter/E/T track, C clear, Home recentre, M/Esc close.
Test helpers: F6 +25 reales, F7 +10 kg mackerel, **F8 self-check**.

## 5. F8 self-check
Press F8 (not in a panel). It prints and toasts `SELF-CHECK CP-1: N checks, M failed`. Part 1: the unit tests of the economy, recruits, dialogue and layout. Part 2 (live): people and interaction points stand on walkable ground, grounds are in open water, then the **UI diagnostic** opens the dialogue and the map and checks: window size, title font, portrait atlas, the dialogue box lies inside the screen with its size, portrait width, speaker name = "Pip Larkin", text length, the map panel size, map picture loaded, number of markers. **If any line says FAIL, copy the toast and the Output panel text to me**; it names the control.

## 6. Manual test checklist (please tell me pass / fail per line)
1. Launch (F5). Bottom-left shows "CP-1 test build r3". [ ]
2. Press F8: toast says PASS (or send the failing lines). [ ]
3. Press M at sea. A map opens with markers; keys 1/2/3 switch views; Esc closes. [ ]
4. SPACE to dock, F ashore. You see the pirate (not invisible). [ ]
5. Walk Anchor Avenue north to the palace (about 200 m, 1 min). Four terraces, walls, stairs, lamps, guards. [ ]
6. Press E next to Pip Larkin (near the notice board, east): box with portrait, name, text, options, cost (18 reales) and affordability. [ ]
7. Walk to the fish counter (west), E: trade panel. F7 gives fish; sell: money counts up with a toast. [ ]
8. M, select a recruit, Enter: the target is tracked (pulsing ring, arrow strip). [ ]
9. Board (F at the pier), sail to Pilchard Shallows (-300, 560): beacon, buoys, gulls visible. [ ]
10. Slow down, press F: panel, corks and foam behind the stern, haul toasts. [ ]
11. Return, sell, hire Pip (18). Purse drops, crew count rises. [ ]
12. Optional: an Arabic keyboard layout: repeat 3, 6, 10. [ ]
13. Framerate on the HD 3000 (F3 overlay): note the number in the city and at sea. [ ]

## 7. Prices and costs (unchanged, all tunable in `data/tuning/tuning_port.json`)
Per kg: sardine 1.0, mackerel 1.6, parrotfish 2.6, red snapper 3.2, yellowfin 4.5. Recruits: Pip Larkin (lookout) 18, Tuck Marrow (sailor) 30, Silas Reed (cook) 40, Garrick Stave (carpenter) 55 = 143 reales. Start purse 5, hold 40 kg. Full derivation in `docs/CP1_CAPITAL_PORT.md` section 4 and the balance table there.

## 8. Static checks versus Godot runtime
Static (Python): economy twin, layout and reachability on baked data, hero-cull model, art checks, gdlint, `check_all.py` ALL PASSED.
Godot engine, headless (Node WASM 4.7.2): `load_all` 83 scripts (4 fail only because this build has no RegEx module), `test_port` 431 checks 0 failed, `selfplay` 32 checks 0 failed (the scripted loop: dock, walk, talk, hire, fish, sell, map, UI diagnostic), plus the other test scripts.
**Not verified anywhere:** how anything looks, text and portraits on screen, the cue sprites, the new city on the HD 3000, framerate, a real keyboard. That is what your test is for.
