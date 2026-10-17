# A6 - Island template and kit system

Goal: build 50+ islands from data (template + kit + seed + a few record fields), with a hard guarantee that every island is quick to explore, walkable, offers something survival-relevant, and does not look like another island.

Honest status: the Python side (baker, checks, sameness, report, 36 tests) was **run and passes**. The GDScript side (`core/island_map.gd`, `tests/test_island_map.gd`, `ui/island_viewer`) is **syntax-checked and lint-clean only**; Godot cannot run in my sandbox.

## 1. The pipeline: bake, don't generate

```
island record (id, tier, template, kits, seed, survival_offers, hook_kind)
      + island_template (shape, relief, coast, slots)  + kit (tiles, props)  + tuning (grid sizes, budgets)
      --> tools/island_kit/bake.py -->  game/data/islands/maps/<isl_id>.map.json   (committed)
```

The game loads the baked map; it never generates at run time. Reasons: (1) no cross-language determinism problem (Python bakes, GDScript only reads); (2) the dev PC needs no Python; (3) a map is reviewable in Git and viewable in `ui/island_viewer`; (4) load time is trivial.
Every map carries `source_hash` (seed + template + kit + tuning + generator version): if any source changes, `check_project.py` reports the map as **STALE**. It also carries `grid_sha256` and `content_sha256`: a hand-edited map is refused by both the Python checks and `IslandMap` in GDScript. Edit the template or seed and re-bake instead.

## 2. Scale (all provisional, tuning owner E7; numbers in `game/data/tuning/tuning_world.json`)

| tier | grid | island area box | explore budget (walk all POIs from the landing) |
|---|---|---|---|
| 1 | 192 x 192 tiles | 384 x 384 m | 45 min |
| 2 | 128 x 128 | 256 x 256 m | 16 min |
| 3 | 80 x 80 | 160 x 160 m | 6 min |

1 tile = 2 m (matches the 48 px tile at 24 px/m). Walking 1.4 m/s. "Quick to explore" is now a measured number, enforced per map. Explore time is a nearest-neighbour tour of all points of interest, cost-weighted (wading x1.6, uphill penalty), without time spent at each point.

## 3. Terrain model

7 classes: `~` deep, `-` shallow (wadeable), `.` beach, `g` ground, `u` upland, `r` rock, `#` cliff (impassable). Plus elevation 0-15. Ship navigability of shallows is **not decided** here (E8 navigation).
Walkable = everything except deep and cliff. All POIs and landings must be in one walkable component (tested in Python and re-tested in GDScript by flood fill).

## 4. Templates (10) and the shape operators

blob, ring (atoll with passes), crescent (bay), ridge, twin_lobes, cone (crater), mesa (cliff rim, one ramp), stack_field (many rock stacks in wading shallows), flats (tidal), fjord. Each `island_template` record has: allowed tiers, shape op + parameters, land-fraction range, relief (levels, cliff step, rock amount), coast (shallow width, beach width), landing count, and **slots**.
Slots are where content goes: `survival` (one POI per declared survival offer, at least), `hook` (the one memorable thing), `secret`, `story` (reserved for F), `camp`. A slot says where it may be (terrain, distance from coast, near another slot), how many per tier and the minimum spacing. If a slot cannot be placed, the bake fails with a clear message instead of producing a bad island; `bake.py --find-seed isl_NNN` searches for a seed that works.
Rotation, size variation (`var`), domain warp and coast roughness make one template yield different islands per seed.

## 5. Kits (5)

`kit_tropical`, `kit_arid`, `kit_temperate`, `kit_frozen`, `kit_volcanic`: map the 7 terrain classes to tile art and list props with zone, density per 100 tiles, spacing and clusters. They use the A4 placeholder assets (3 new placeholder tiles were added: `til_water_shallow_a`, `til_rock_a`, `til_ice_a`; 41 assets now). An island may list several kits; the first gives the tiles, all give props. Final biome art replaces placeholders by file name (I17).

## 6. Original idea: the Silhouette Quota

The player meets every island first as a shape on the horizon, so uniqueness is measured on what they see: the dry-land silhouette, cropped, resampled to 32x32, compared with the other island at all 8 rotations/flips. Rules on top: max 4 islands per `hook_kind` (20 kinds exist), max 3 per template+kit pair, and neighbouring islands may not share a hook kind.

Calibration, measured, not guessed (100 baked islands): first version, round templates overlapped 0.83 on average (blob vs blob), so I made them irregular (aspect, lobes, warp). After that, same-template islands average 0.70 and random cross-template pairs average 0.54 (90th percentile 0.72). The limit is **0.85**, which flags about 0.2 % of random pairs (near-duplicates). Re-calibrate whenever templates change.

## 7. Limits you should know

- **10 templates are not enough for 50+ islands to feel different.** The quota catches near-duplicates; real variety must come from hooks, set pieces and story in the F modules. Recommendation: reach about 16 templates by E3.
- Seed failure rate is real: 3 of 10 random seeds failed for the atoll, 2 of 10 for stack_field. Use `--find-seed`.
- T1 fixture islands use only 9.7-11.7 min of a 45 min budget for walking alone; the budget is a ceiling. T1 islands will carry much more content (puzzles, fights, story) or we raise the island size. Decide at the vertical slice.
- Island 3D rendering is not part of A6 (J module). `island_viewer` is plain 2D.
- The fixture islands (isl_901 to isl_910, with test names) live in `game/tests/fixtures/islands/` and are not Canon islands. The real registry in `game/data/islands/` is still empty until E3.
- All sizes, budgets, speed and limits are provisional (see `docs/PROVISIONAL_LEDGER.md`).

## 8. How to test and use

```
python tools/check_project.py                       # everything, including maps/stale/sameness
python tools/island_kit/test_island_kit.py          # 36 tests
python tools/island_kit/report.py                   # contact sheet + docs/A6_ISLAND_KIT_REPORT.md
python tools/island_kit/bake.py --islands game/tests/fixtures/islands/islands.json --out /tmp/maps [--only isl_901]
python tools/island_kit/bake.py --islands FILE --out DIR --find-seed isl_NNN
```
Needs `pip install numpy scipy pillow`. Add a real island: add its record (template, kits, seed as a decimal string, offers, hook_kind) to `game/data/islands/*.json`, bake into `game/data/islands/maps/`, run `check_project.py`.
In Godot (first real run of the new GDScript): the A5 commands, plus open `res://ui/island_viewer.tscn` and press F6 (SPACE next island, TAB overlays, +/- zoom). Expect `test_island_map` to pass. Unverified in Godot: `Image.create_empty` + `set_pixel` speed on 192x192 (fine in theory), `static func` using `new()`, and `PackedStringArray(Array)` conversion.
