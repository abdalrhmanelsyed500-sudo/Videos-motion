# CP-2B.1: Mandatory Manual Fishing

Order (2026-10-21): the winch is the only way to catch fish. The old automatic net (F while sailing on a ground) had survived Release B and
must go completely. Baselines kept: Release A (ship, sailing, map) and Release B (winch session, storage panel, barrels, species, prices).

**Status: built and tested in the Godot 4.7.2 WASM headless runtime only. NOT run on Windows or on the HD 3000.**

## 1. What was found (audit of every way fish could reach the hold)

| Path | Where | Verdict |
|---|---|---|
| Timed net: F while sailing on a ground -> `PortGame._toggle_nets` -> `Fishing.start` -> `Fishing.step` rolled a haul every 12 s and called `PortState.add_catch` | `port_game.gd`, `fishing.gd` | **removed** |
| Test key **F7**: +10 kg mackerel | `port_game.gd` `_test_key` | **removed** (F6, +25 reales, stays) |
| Winch session unload | `fish_manual.gd` `commit` -> `add_catch` | **the only remaining caller** |
| Selling | `PortState.sell_all` | removes fish, pays reales: kept |
| Save restore | `PortState.apply_dict` | restores the hold, catches nothing: kept |
| Debug console, market, dialogue, cheats, background timers, ship stores | grep of every script | no other writer of the hold |
| Test seeding (`add_catch` in `tests/`, harness hooks in `tools/godot_browser`) | tests only | not part of the game |

## 2. What changed

* `h2d/fishing.gd` is now only the **fishing grounds and the winch rules** (ground, crew, sea state, ship speed, deterministic generator for
  species). Removed: `start`, `roll`, `time_mult`, `seconds_to_haul`, the timer, the haul loop and the state `timer`, `hauls`, `session_kg`,
  `session_by`, `manual`. `step(ship, sea)` takes no hold and returns only `stop` events (ground lost, sea too rough). Defaults reduced to
  `fish.max_speed_kn` and `fish.max_sea`.
* `h2d/port_game.gd`: F while sailing (helm or anywhere not at the winch) **only shows a message**: where the winch is, or why fishing is not
  possible here. No net, no timer. The "Lower the nets" prompt is gone. The legacy "NETS DOWN" HUD panel (`port_hud.gd`) is gone. Objective
  texts now describe the winch. The F7 test-fish key is gone.
* `h2d/h2d0.gd`, `h2d/fish_session.gd`: the deck hint no longer mentions drift nets; the session no longer asks the legacy net to give way.
* **Kept:** the ship's net cues (buoys, corks, foam trail) are visual only and follow the winch session (`fishing.active`); the helm slows the ship
  while a winch session holds the ground; the species, prices, hold size, freshness, storage panel and barrels are untouched.
* Data and tools: `data/port/dialogue.json` (two lines no longer say "lower the nets"); `tuning_port.json` notes mark `fish.haul_interval_s`,
  `fish.haul_kg`, `fish.haul_spread`, `fish.mult_*` as **INCOME MODEL ONLY** (the Python twin `tools/h2d/economy_logic.py` still uses them to
  size the early game; the game does not read them). Docs `CP1_CAPITAL_PORT.md`, `CP2A...`, `CP2B...` carry a pointer to this change.
* **Behaviour change you will notice:** there is no F7 shortcut to fill the barrels. The Release A checklist step "press F7 twice" no longer works;
  fish the real way (or, for development only, call `PortState.add_catch` from a test).

## 3. Regression tests added

| Test | What it proves | Result |
|---|---|---|
| `tests/test_catch_paths.gd` (new, 27 checks) | reads every runtime script: `add_catch` is called only by the winch (`fish_manual.gd`) and defined in `port_state.gd`; only `port_state.gd` writes `lots` / `kg_total`; no trace of `_toggle_nets`, haul interval, "Lower the nets", "NETS DOWN", `KEY_F7`; `Fishing` has no `roll`/`start`/`seconds_to_haul`/`time_mult` and no timer state; an hour of 0.1 s steps inside a ground gives zero events; leaving the ground only lets go; selling pays once and empties the hold; a save restores the same hold. A mutation check (a temporary file calling `add_catch`) made it fail as intended | 27 / 0 failed |
| `tests/fish_flow.gd`, new section `_no_auto_fish` (real scene, real key events) | ship on Pilchard Shallows at the helm: 20 s waiting, then F pressed three times with 6 s between: hold stays 0 and empty, the legacy net never becomes active (`status` stays `idle`), no winch view opens, a message is shown, no "Lower the nets" prompt | part of 98 / 0 |
| `fish_flow`, after a real manual session | the hold equals the catch card once (no duplicate from any legacy system), lots add up to the hold, 15 s more on the ground and opening/closing the winch change nothing | part of 98 / 0 |
| `fish_flow`, selling | a real `sell_all` pays and updates the purse, the barrels and the open storage panel follow, selling twice pays once | part of 98 / 0 |
| `selfplay`, `map_flow`, `audit_r6` (updated) | F on a ground at the helm does not fish; the map and a paused clock never bring fish; the people and map rules still hold | 114/0, 52/0, 65/0 |

Whole suite (`tools/godot_node/run_suite.sh`) on code commit `57d9f8b`: **42 passed, 0 failed** (fish_flow 98, selfplay 114, map_flow 52, audit_r6 65, deck_flow 68, test_port 489, test_fish_manual 150, test_fish_ui 56).
Lint: `gdlint`, `check_gd_warnings`, `check_gd_types`, `check_docs`, `economy_logic.py --check` all clean.

## 4. Windows checklist (5 minutes)

1. Start the game, sail to the **Pilchard Shallows** (chart M). Stay at the helm. Wait one minute: the hold bar stays at 0.0 kg.
2. Press **F** at the helm in the ground, several times: you get only a message about the winch; no "NETS DOWN" panel, no kilograms, no slowing down.
3. Press **E** to leave the helm, walk to the drum on the main deck, press **F**: the first-person fishing view opens (cast with Space, haul with A and D, raise, card, unload with E). The hold grows only after the unload.
4. Sail home, moor, walk to the fish market, sell: the purse grows, the hold, barrels and **E** panel empty.
5. Press F7: nothing happens (no test fish). F6 still gives 25 reales.
6. Check that the sailing, the ship walk, the map (M) and the storage panel still behave as in Release A and B.

## 5. Limits

Not tested on Windows or the Intel HD 3000. No real-renderer screenshots were made for this change (the HUD panel and prompt that were
removed are not part of the first-person view; the scene tests drive the real game scene and real key events).
