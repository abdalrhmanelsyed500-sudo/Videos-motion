# CP-1 "Fish Row": the first slice of the capital port and the starting economy

Status 2026-10-19. **Nothing in this document has run in Godot.** Everything is checked statically only (Python twin of the economy, layout and reachability checks on the baked data, GDScript syntax and a heuristic type scan). Section 9 says exactly which is which. Section 8 is the manual test checklist.

## 0. What was asked and what this slice is

The milestone asked for a *substantial* walkable capital (harbour, fish market, general market, commercial streets, bridges, residential streets, tavern, warehouses, squares, six NPC groups), a starting loop (own ship, incomplete crew, recruits, fishing grounds, selling, hiring), and a map. The agreed order was: (1) fix the invisible player, (2) build ONE small slice, (3) expand only after manual testing.

This is step 2. **It is one district of Anvil Harbor, not the whole capital.**

| Asked | In CP-1 | Not yet |
|---|---|---|
| Large working harbour | the existing H2D-1 pier + berth, a 88 m wharf with 3 moored boats and a cargo pile, a net frame, a canal ("The Cut") | docks for many ships, cranes, a long quay |
| Fish market | counter + canopy + 6 stalls/racks/crates, a fishmonger (Barnaby Gull), a real sell interaction | a general market and commercial streets |
| Bridges, waterfront passages | 2 bridges over The Cut, a wharf apron | more canals |
| Residential streets, tavern, warehouses, squares | 5 cottages on the north side of the market yard, the H2D-1 tavern, warehouse and harbourmaster, the plaza, a market yard | the tavern is not enterable; no interiors |
| NPC groups | 28 people: fishers, merchants, dock workers, sailors, shopkeepers, townsmen + 4 recruits | many more people, schedules |
| Recruits | 4, each at a distinct place with role, upfront cost and dialogue | dismissal, wages, crew stats in play |
| Fishing grounds | 4 grounds, the nets, 5 species | fishing minigame, bait, gear |
| Map with markers | district map + waters map, recruits, fish market, ship/harbour | a full city map, quest log |

## 1. P1: the invisible player (root cause)

Symptom: after leaving the harbour the player could still move but could not be seen.

Root cause (found by reading the engine source, not by running it): the hero is drawn by a `MultiMeshInstance3D` whose `custom_aabb` was set once, around the world origin, while the code moved only the *instance* transform inside the MultiMesh. In Godot a MultiMesh with a non-empty `custom_aabb` is culled by `node transform x custom_aabb`; instance transforms are never added to it. So the sprite was drawn only while the camera looked near the origin (the harbour) and was frustum-culled everywhere else.

Fix (`cay_world.gd`, commit `bc9d623`): `set_hero()` now moves the NODE to the hero's position, so the culling box follows the sprite. The same rule is applied to the new CP-1 MultiMeshes (people, markers): they keep the node at the origin and give a district-wide `custom_aabb` (`_make_dynamic_mm`). Guard: `tools/h2d/check_hero_cull.py` reproduces the cull model and also scans the source for the mistake. Movement, collision, docking, boarding and casting off were not touched.

**Unverified in Godot.** Please walk to Lookout Hill, Pearl Cove and Wreck Beach (T key) and look for the pirate.

## 2. The district ("Fish Row", west of the plaza)

Coordinates are metres, x east, z south, as everywhere. The plaza is at (16, -2); the pier and berth (H2D-1) are unchanged.

- **Quay Street** runs west from the plaza along z -4..3.4. **The market yard** lies north of it (x -102..-53, z -29..-4). **The warehouse yard** (Garrick's boatyard) is at x -36..-19, z -30..-4.
- **The Cut** is a canal at x -48..-40 running from z -14 south to the sea. **Quay Street Bridge** (x -50..-38, z -3.2..3.2) and **Net Walk Footbridge** (z 9.6..12.8) cross it; each is 16 m long on foot.
- **The wharf deck** (1.75 m, a 0.2 m step down from the 1.95 m quay) follows the shore from x -116 to x -28. Moored: a red-sailed sloop (22 x 6.4 m hull), two smacks, two skiffs in The Cut. The hulls are solid for the player's ship (a boat is as solid as land to the hull probes).
- **Fish market**: the counter at (-77, -12.6) under a canopy, stalls and racks around it. Stand within 3.4 m of (-77, -10.6) and press E.
- **Notice board** at (13, -2.4), five metres from where you land from the ship. Press E: it opens the map.

Everything is baked by `tools/h2d/bake_cay.py` from one layout file, `tools/h2d/port_layout.py`; the result is the `port` section of `anvil_cay.json` (format v3). Art: five atlases in `game/h2d/art/port_*_atlas.png`, previews in `art_bible/cp1/`. Props and people are drawn at 14.4 px/m (the pirate's scale); the moored boats at 3.6 px/m (the ship scale).

Cost on the dev PC (estimates, not measured): one draw call each for props, big props, boats, people, people's shadows, markers and the merged deck mesh. People are moved on the CPU only within 110 m of the player.

## 3. People

28 people, each a sprite from `port_npc_atlas.png` (24 x 32 px, 4 directions x 4 frames per look, 10 looks).

| Group | Count | What they do |
|---|---|---|
| fishers | 5 | mend nets, walk the apron |
| merchants | 4 | stand at stalls, stroll the yard |
| dock workers | 4 | patrol the wharf, carry |
| sailors | 3 | the plaza and the pier |
| shopkeepers | 3 | stand at counters (Barnaby the fishmonger is one) |
| townsmen | 5 | wander Quay Street |
| recruits | 4 | stand at their post |

Press E near anyone for a short line (`game/data/port/barks.json`). Lines depend on what you did: whether the hold has fish, whether you have fished at all, whether you are poor, whether you have a crew. Content rules: all speakers are men, no religion, nothing sexual.

## 4. The recruits (all four cost reales upfront, once)

| Recruit | Role | Cost | Where | Effect (what you get) |
|---|---|---|---|---|
| Pip Larkin, 19 | lookout | 18 | by the signal mast, east of the plaza, in front of the tavern (27.5, -2.4); 31 m from the pier | +10% fish in every haul |
| Tomas "Tuck" Marrow | sailor | 30 | the net frame at the west wharf (-100.5, 8.6); 141 m on foot | +25% fish in every haul |
| Silas Reed, 41 | cook | 40 | the well in the market yard (-57.5, -13.8) | fish spoils 30% slower |
| Garrick Stave, 52 | carpenter | 55 | the boatyard behind the warehouses (-26.5, -22) | +20 kg of hold (40 -> 60 kg) |

Total 143 reales. Each has 3 dialogue pages the first time you talk, then goes straight to the offer. The offer panel shows role, cost, your purse and the effect, and says clearly whether you can afford him ("Y hire / N not now" or "you are N short"). Their data follows the `crew_member` schema (male, stats, loyalty) so module D can promote them to real crew records.

## 5. The starting loop and every number

You start at sea (-100, 140), heading to the harbour, with a **purse of 5 reales**, an empty 40 kg hold and no crew. The objective card (top right) always tells you the next step from the real state.

1. Sail to the **Pilchard Shallows** (-300, 560), 0.6 km away (about 25 s of sailing). Press **F** inside a ground: the nets go down, the ship slows below 1.5 kn.
2. Every **12 s** a haul comes up: about **1.2 kg x richness x time-of-day x (1 + crew bonus) x (1 +/- 40%)**. A toast shows the species, kg and the hold.
3. Press F again (or fill the hold) to haul in. Sail home, press SPACE in the dock zone to moor, F to go ashore.
4. Walk west to the fish market (about 120 m, 30 s), press E at the counter. The panel shows each species in the hold, freshness, the price per kg, the estimate and the whole-hold total. **Enter / E sells everything**, 1-5 sells one species. A big gold "+N reales" banner shows the payout and "Purse A -> B".
5. Talk to a recruit you can afford, press **Y**.

### 5.1 Prices (reales per kg of FRESH fish, before the 20% market spread)

| Species | Base | Why this number |
|---|---|---|
| Sardine | 1.0 | B4 prices fresh fish at 2/kg on average; the sardine is the bottom of the range, the fish of the first trip |
| Atlantic Mackerel | 1.6 | the harbour's daily fish |
| Parrotfish | 2.6 | reef fish, only from the Kelp Reef |
| Red Snapper | 3.2 | prized at table, reef and deep water |
| Yellowfin Tuna | 4.5 | the best fish of the prologue, only from Blue Drop |

You are paid `base x freshness x (1 - spread/2) x e^x` per kg for a small sale (spread 20%, B4). Selling a lot at once pays slightly less per kg because of market depth: **depth 150 reales per species** (a fish stall is a small market; T1 ports are 4500 across all goods). The market remembers: after a sale that species' price level drops (the panel shows "market at 84% of normal") and recovers with a **half-life of 6 game days (90 real minutes)**. So selling 40 kg of one fish is worse than 10 kg of four fish; this is the reason to vary grounds.

### 5.2 Spoilage

Fresh fish loses **0.35 of its value per game day** (a game day is 15 real minutes), floor **0.25** (fish meal: never worthless, but it hurts). A 4-minute trip costs about 6%. The cook (Silas) multiplies the loss by 0.7. The HUD warns below 0.7 average freshness.

### 5.3 Grounds (distance is from the berth)

| Ground | Where | Richness | Species (weights) | Reales per haul | Reales per minute of nets | Notes |
|---|---|---|---|---|---|---|
| Pilchard Shallows | (-300, 560), r 90, 628 m | 1.0 | sardine 65%, mackerel 35% | 1.45 | 7.3 | the place to learn the nets |
| Gannet Bank | (480, 650), r 95, 778 m | 1.1 | mackerel 50, sardine 20, red snapper 30 | 2.59 | 12.9 | |
| Kelp Reef | (-700, 1000), r 100, 1216 m | 1.2 | parrotfish 45, red snapper 35, mackerel 20 | 3.76 | 18.8 | |
| Blue Drop | (300, 1750), r 110, 1751 m | 1.3 | mackerel 50, tuna 25, red snapper 25 | 4.25 | 21.3 | **needs at least 1 hand aboard** (deep water) |

Time of day (T1 bands): dawn 05-07 and dusk 17-19 **x1.3**, daylight and evening **x1.0**, night 20-05 **x0.7**. The nets stop if the sea index goes above **0.6** or the ship leaves the ground. The hold holds **40 kg** (about 33 hauls = 6.7 minutes of nets); the HUD turns amber at 85%.

### 5.4 Balance (simulated, not played)

`tools/h2d/economy_logic.py` replays the loop with three policies (the numbers assume 4 kn average path speed, 100 s of overhead per trip):

| Policy | Pip | Tuck | Silas | Garrick (all four) |
|---|---|---|---|---|
| best (moves to the better ground as soon as it can) | 6.0 min | 13.3 | 19.8 | 27.1 |
| near (stays at the nearest ground) | 5.0 | 20.6 | 31.0 | 56.6 |
| cautious (many short trips) | 8.5 | 21.6 | 38.9 | 64.8 |

The design target (written in the script) is the first hire in 5-10 minutes and all four in under an hour for a player who explores. **Whether it feels like that is exactly what the manual test must tell us.** Every number lives in `game/data/tuning/tuning_port.json` (15 keys, each with a unit and a one-line reason) and `game/data/port/*.json`; edit the JSON, the Python twin (`--check`) and the GDScript defaults must agree.

### 5.5 Conflicts recorded, not hidden

- The prologue purse is **5 reales**; B4's starting purse is **600**. B4's 600 is read here as the campaign purse after the first prize. Owner: B4; revisit at the first real economy module. It is in the Provisional Ledger.
- Prices are per-species fish prices; B4's single "fresh fish 2/kg" is their average.
- No save to disk in this slice: purse, hold, crew and market memory live until the game is closed (the state has `to_dict`/`apply_dict` ready for the save module).

## 6. Controls (new and changed)

| Key | Where | Action |
|---|---|---|
| **F** | at sea, inside a fishing ground | nets down / up (outside a ground: tells you the nearest ground and how far) |
| **E** | ashore | talk / sell / read the board (at sea E still toggles the effects budget) |
| **M** | anywhere | the map. **Shift+M** is now the ship-motion toggle |
| **Tab** | map open | switch Fish Row / the waters south |
| **Enter / Space / E** | a panel | continue / sell everything |
| **1-5** | the market | sell one species |
| **Y / N** | a recruit's offer | hire / not now |
| **Esc** | any panel | close |
| F6 / F7 | any time | TEST: +25 reales / +10 kg mackerel in the hold |

While a panel is open the game clock is paused (T1: planning screens pause) and WASD/A-D do nothing. Everything else is as in H2D-1.2 (A/D steer, SPACE dock/cast off, F ashore when moored, F board at the pier, T next stop).

## 7. How it works (for the next person)

- `h2d/port_state.gd` purse, hold lots with freshness, market (via `core/market.gd`), hiring. `h2d/fishing.gd` the nets and the deterministic haul generator. `h2d/port_npcs.gd` walkers. Pure logic, no scene.
- `h2d/port_game.gd` the controller: owns the above plus `port_ui.gd` (everything is drawn on one Control, from dictionaries). `h2d0.gd` calls `step(dt, ctx)` each frame and `handle_key` first in `_unhandled_input`; the controller tells it only whether the nets are down (`target_kn = 0`) and whether a panel is open.
- Every rule has a Python twin (`tools/h2d/economy_logic.py`) and a fixture (`tests/fixtures/economy_cases.json`) replayed by `tests/test_port.gd`; that test also checks the baked district, the walkers and that the objective text follows the state.

## 8. HOW TO TEST (about 15 minutes; Godot 4.7.2, open `pixel_pirates/game`, F5)

If you can, run the project once headless first: `Godot_..._console.exe --headless --path game --import`, then `--script res://tests/run_all.gd` (this is the first time `test_port.gd` ever runs; tell me any red line).

1. **P1**: leave the harbour by ship, moor, F ashore, press T four times. Is the pirate visible at every stop? (Yes/No per stop.)
2. At the start press **M**: the waters map shows your ship, the harbour and the four grounds. Press Tab: the district map shows Fish Row, the market, the notice board and the four recruits (gold diamonds).
3. Sail to the Pilchard Shallows (follow the objective card), press F. Does the ship slow to a stop? Do hauls come every 12 s with toasts? Does the hold bar grow?
4. Press F7 once (test fish) if you do not want to wait. Moor (SPACE in the dock zone), F ashore. Are the stalls, boats, people and the fish market visible and in the right size? Do people walk?
5. Walk to the notice board (5 m from the landing) and press E: map opens. Close with Esc.
6. Walk west on Quay Street to the fish market (about 120 m). Press E at the counter. Check the table, sell with Enter. Is the "+N reales" feedback clear? Does the purse change by exactly that amount?
7. Press F6 until you have 18 reales, find Pip near the tavern (the map marks him; he has a floating marker). Read his dialogue, press Y. Does the purse drop by 18, does the marker disappear, does the HUD list him in the crew?
8. Go fishing with Pip: haul sizes should be about 10% larger. Try the other grounds, then try Blue Drop with and without a hand aboard.
9. Time: how long until you hired the first and all four? (The simulation said 5-8.5 minutes and 27-65 minutes.)
10. Report: red/yellow Output lines, fps at sea / in Fish Row (Dev-Lite), anything that looks like a placeholder, anything that feels wrong in price, speed or distance.

## 9. What was checked, and how

| Check | Kind | Result |
|---|---|---|
| `tools/check_all.py` (all steps incl. the CP-1 ones below) | static, Python | ALL PASSED |
| `economy_logic.py --check` (twin, fixture, tuning JSON, GDScript defaults, balance targets) | static | PASS |
| `check_port.py` (28 people on walkable ground and reachable from the pier, 4 recruits >= 20 m apart, market and board reachable, decks vs hulls, grounds >= 100 m from land) | static, on the baked data | PASS (13 genuine layout errors were found and fixed this session: notice board unreachable, recruits 3 m apart, 4 people standing in blockers, hulls overlapping the wharf) |
| `check_land.py` (pier to all stops with the new blockers) | static | PASS |
| `check_h2d_art.py` (colour caps: stalls 32, misc 12, big 32, ships 19, people 35; no clipped cell) | static | PASS (stall atlas was 36 colours: merged to 32) |
| content-rule lint of the new data | static | PASS (it caught the word "her" for a ship, "she", and "religion"/"sexual" inside notes; reworded) |
| gdparse, gdlint, GDScript type scan, warning scan | static, NOT Godot | PASS. gdlint line limit raised from 120 to 200 because UI/data lines are long; three `max-returns` / `max-public-methods` exceptions are marked in the code |
| **Godot run (F5, headless tests)** | **runtime** | **NOT DONE: the Godot binary cannot be downloaded in my sandbox** |

Riskiest untested parts: the hand-built MultiMeshes for people/markers (culling box, per-instance data), the merged deck mesh with `pier.gdshader`, drawing the UI with `_draw` (outlined text), the map images built from `height_at` the first time M is pressed (about 30k samples, expect a short hitch), reading `meta["port"]` in `h2d0`, and the first run of every new GDScript file. Any of them can fail on first launch.

## 10. Original idea: "the notice board knows your purse"

Instead of a quest log, the world answers the same question, "what do I do next?", in three places that all read the real state: the objective card, the markers floating over the people (gold = a recruit, green = a recruit you can afford, cyan fish = the market), and the street talk (barks change with whether you fish, are poor or have a crew).

## 11. DONE / CANON UPDATE / NEXT

- **DONE** (static only): P1 fix; Fish Row district; 28 people; 4 recruits with dialogue and costs; 4 grounds, 5 species, nets, selling with feedback, hiring; map with markers; documented, tunable economy; tests written.
- **CANON UPDATE**: H2D-1.2.2 (hero cull) and CP-1 (this slice) bullets; the prologue purse conflict is in the Provisional Ledger.
- **NEXT** (only after your manual test): (a) fix whatever the test finds; (b) then expand one step at a time: the general market street, a tavern interior with a second recruit source, more ships in the harbour, a save slot. I will not expand before you have tested this slice.
