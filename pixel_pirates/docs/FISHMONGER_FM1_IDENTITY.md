# FISHMONGER — FM-1: Identity Pass (completion report)

Branch `arena/7464ca7a-videos-motion` · baseline `baseline-pixel-pirates` = `300012f` (tag **pushed to origin**) ·
FM-0 = `776dad2` · approved decisions of 2026-10-23 applied verbatim: currency **USD "$"**, home harbour **Port Marlin**
in `reg_kettle_seas`, starting vessel **Gullwing** (7 m coastal boat), **solo start** with deckhands as later optional
progression, legacy pirate content **removed from the active experience but never deleted**.

## 1. Verified starting state and backup

- Sandbox reset had rolled the local checkout back to an old snapshot; recovered with
  `git fetch` + `git reset --hard origin/arena/7464ca7a-videos-motion` → `776dad2` (FM-0). **No work was lost**: every
  commit existed on origin. The local-only tag had vanished with the reset; it was re-created at the same commit
  (`git cat-file -t 300012f` = commit) and **pushed** (`baseline-pixel-pirates`) so the pirate baseline is now
  recoverable from origin independent of this sandbox.
- Working tree clean before edits; no files deleted, moved or renamed anywhere; no history rewritten.
- Branch note: Arena binds this session to `arena/7464ca7a-videos-motion`; a separate FM-1 branch is not permitted by the
  session rules. Isolation/reversibility is provided instead by the pushed baseline tag + focused commits; nothing is
  merged to `main`.

## 2. Identity architecture (no scattered hard-codes)

- New autoload **`core/identity.gd`** (registered in `project.godot` after `Data`): reads `data/fm/fm_identity.json`
  (`fm_core`) at boot and exposes `title`, `sym`, `currency_code/name`, `home_port`, `home_region`, `start_boat`,
  `boat_len_m`, `crew_policy`, plus formatters `money()`, `money_f()`, `per_kg()`. Fallback constants equal the approved
  values, so identity survives a data-load failure. All UI money/port strings now call Identity.
- `fm_identity` record extended (schema + record, additive): `home_port`, `boat_len_m`, `crew_policy`; source note cites
  the approved decisions.

## 3. Exact changes

| Area | Change |
|---|---|
| Title/metadata | `project.godot`: name **Fishmonger**, modern description; `debug_console.gd` banner; `h2d0.gd` debug overlay line |
| Currency display | `port_hud.gd` purse label; `dialogue_ui.gd` purse/total/price-board/receipt lines; `h2d0.gd` lockbox toast; `port_game.gd` all objective/recruit/bark money strings → `Identity.money/per_kg` ("$5", "$ per kg", "Account $x -> $y") |
| Harbour identity | `harbor.gd` default + `configure()` default → Port Marlin; `anvil_cay.json` port name/district/views/plaza/pier; `map_views.json` city title; `map_model.gd` built-in DEFAULT_VIEWS city title (parity trio kept equal, test-enforced) |
| Modern place names | tavern "The Anchor and Crown" → **The Dockside Diner**; "Counting House (coin and assay)" → **Harbour Bank**; "Barracks (town guard)" → **Coast Guard Station**; "Anvil Battery (harbour guns)" → **Old Battery Point (historic museum)**; the placed cannon prop on the plaza re-typed to crates (asset kept in the atlas for rollback) |
| Items (display names only, ids stable) | Hardtack→Ship Biscuit, Salt Meat→Salted Meat, Grog→Bottled Grog (legacy stock), Gunpowder→Black Powder (legacy, hazardous), Cannonball→Cannonball (legacy relic), Coin→Old Silver Coin (legacy), Doubloon→Collector Doubloon (legacy), Silver Bar→Silver Bar (legacy bullion), Water Barrel→Water Drum, Fresh Fish→Fresh Fish (hold) |
| Rack labels | `ship_layout.gd` ZONES: "Water and grog"→"Water and drinks", "Powder and shot"→"Legacy stores", "Trade goods and treasure"→"Trade goods" |
| Port text data | `dialogue.json`, `barks.json`, `recruits_port.json`, `fish_market.json`: "Anvil Harbor"→Port Marlin (6), prose "reales"→dollars (26); `fish_market.json` currency field → USD. Internal key `base_reales_per_kg` and tuning key `port.start_reales` **unchanged** (stable internals) |
| Tests updated same commit | `deck_flow` (lockbox toast), `map_flow` (price shown with $), `fish_flow`/`test_catch_paths` (message wording), `test_ship_stores` (Ship Biscuit/Water Drum + heading order) |
| Docs | this file; `port_state.gd` comment clarifies dollars vs internal field names |

## 4. Remaining pirate identity in active gameplay (honest list)

- The **sailing sloop itself** still appears as the player boat (mesh/rig/helm) — boat replacement is FM-3 by plan; its
  identity references (name/boat class) are already modern in data (`Gullwing` reserved for the FM-3 hull).
- Internal comment codename "the pirate" for the player character in several scripts (comments only, zero player-facing).
- Legacy-category items still exist as records (rollback + old saves) but are labelled "(legacy …)" and grouped under
  "Legacy stores".
- Dialogue character voices still carry old-coast flavour text beyond currency/terms — full voice pass deferred to FM-2.
- Crew recruitment UI still exists (data currently empty); per decision it becomes the optional deckhand progression
  later; starting state is already solo.

## 5. Validation actually executed

- `tools/check_all.py`: **ALL PASSED** (registry/data model incl. fm_identity, schema+id grammar parity, market twin,
  port layout, docs-vs-data, hero-cull guard, warning scan, island kit, gdlint, gdparse, static type scan).
- Logic suite: first run after the string pass = 40/42 with exactly the two string-coupled assertions failing
  (`test_map_model` view parity, `test_ship_stores` names); both fixed in the same commit; final run result recorded in
  the chat report (42/42).
- Headless renders (real renderer, dev_lite): `map_ashore` after (`/tmp/FM1new2`) and before (`/tmp/FM1old`, worktree at
  `776dad2`), **0 shader/runtime errors** each; crops prove "$5", "Port Marlin plaza/berth", "FISHMONGER" overlay and the
  deckhand objective on screen. Evidence copies in `docs/fm1_shots/`.
- Not tested: Godot editor run and anything on the user's PC; **HD 3000 remains UNMEASURED**.

## 6. Save compatibility

- No saved field, item id, species id, tuning key or market dict key was renamed; money stays a unit-less integer in
  saves, so old saves load and now simply display as dollars. **No save migration needed in FM-1.** If FM-2/3 rename any
  stored key, `save_io` upgraders (SAVE_VERSION 1→2) are the designated path.

## 7. Deferred (documented, not forgotten)

FM-2: character costumes + UI skin + dialogue voice pass. FM-3: motorboat hull/helm/fuel + legacy sloop to
`prototypes/legacy_sloop/` (assets retained). FM-4 harbour architecture sheet. FM-5 rod/reel gear + freshness/ice +
orders. Crew-hiring progression system. Audio (none exists yet).
