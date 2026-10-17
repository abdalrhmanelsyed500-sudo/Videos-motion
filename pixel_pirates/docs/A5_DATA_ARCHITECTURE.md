# A5 - Data-driven architecture

Goal: every number, item, island, crew member and rule lives in a JSON file that is validated by a schema, so 50+ islands and the whole survival simulation can be built from data without touching code, and a typo is caught before the game starts.

Honest status: the Python half (validator, ledger, tests) was **run and passes**. The GDScript half (registry, tuning, save I/O and their 4 test files) is **syntax-checked and lint-clean only**; Godot cannot run in my sandbox. The first `run_all.gd` run on your PC is the real test (see "How to test").

## 1. The envelope

Every data file is one envelope:

```json
{ "schema": 1, "kind": "item", "records": [ { "id": "item_hardtack", ... } ] }
```

`kind` selects a schema in `game/data/schemas/<kind>.schema.json`. Several files may hold the same kind (for example `islands_region_03.json`, `islands_region_04.json`); the registry merges them and rejects duplicate ids across files. Files that are not envelopes (the `look/` palette and profiles) are ignored by the registry.

## 2. Schemas (8 now)

| kind | key | id prefix | purpose |
|---|---|---|---|
| item | id | `item_` | everything that can be carried: weight, volume, stack, spoilage, nutrition, icon (checked against the art manifest) |
| difficulty_mode | id | `mode_` | 9 multipliers + warning lead time + save rules |
| tuning | key | (dotted) | one balance number, with min/max, unit, optional difficulty scaling |
| region | id | `reg_` | sea region (filled by E1) |
| island | id | `isl_NNN` | tier, biome, position, neighbours with sail hours, `survival_offers` (min 1), landmark rules |
| crew_member | id | `crew_` | `gender` enum is `["male"]` only (hard content rule 1) |
| recipe | id | `rcp_` | galley recipes and preservation (filled by N-modules) |
| save_state | - | - | shape of a save game |

A schema file is `{kind, key_field, id_prefix, record: <mini-schema>}`. The mini-schema vocabulary: `type` (string/number/integer/boolean/array/object), `enum`, `pattern`, `min`, `max`, `props`, `required`, `extra` (allow unknown keys; default is **reject**), `values` (schema for every value of a map), `key_ref` (map keys must exist in another kind), `items`, `min_items`, `max_items`, `unique_items`, `ref` (value must be an existing id of a kind). Two special lookup kinds: `asset` (the sprite manifest) and `multiplier` (the difficulty multiplier names).

Rules worth knowing:
- Unknown keys are errors, so `"wieght_kg"` fails instead of silently doing nothing.
- `integer` means a number without a fractional part, because Godot parses every JSON number as a float.
- Errors are reported as JSON paths (`$.stats.craft`), which is what both validators are compared on.

## 3. Two validators, one test file

- **Python** `tools/data_tools/minischema.py` + `validate_data.py` runs on any machine and in the pre-commit hook. It also enforces **world rules** across records: neighbour symmetry, sail distance never below the straight-line distance, `visible_from` only for islands flagged `landmark`, and (as INFO) the tier counts 12-15 / 20-25 / 15-25.
- **GDScript** `core/schema.gd` is the same logic inside the game, used by the registry at startup and for save validation.
- **Parity:** `game/tests/fixtures/validator_cases.json` holds 35 cases (value, schema, expected error paths). `test_parity.py` (Python, 0 mismatches) and `tests/test_schema.gd` (GDScript, **not yet run**) execute the same file. If the two ever disagree, a test fails.

World rules are Python-only until A7 (the in-game debug console / editor will call them).

## 4. Registry (autoload `Data`)

`core/registry.gd`: `load_all()` (returns the error list, also pushed to the log), `has(kind, id)`, `record(kind, id)`, `all(kind)`, `count(kind)`, `lookup(kind, id)` (used for refs). Systems never read JSON themselves.

Add content: create or extend a file in the right folder, run `python tools/check_project.py`, fix what it says, commit. Nothing else.

## 5. Tuning, difficulty, per-system toning

Every balance number is a `tuning` record and is read as `Tuning.f("food.need_kcal_per_man_day")`, never hard-coded. A record may name a `scale` (one of the 9 multiplier names) and a `scale_mode`:
- `mul` (default): value x multiplier, e.g. hunger.
- `div`: value / multiplier, e.g. "days until scurvy" (harsher mode = sooner).

The multiplier comes from the chosen mode (`mode_story`, `mode_normal`, `mode_hardcore`), **unless the player set a per-system override** (0 to 3). That is how "Hardcore Realism but with easier food" works: `Tuning.from_registry(Data, "mode_hardcore", {"hunger_rate": 1.0})`. Keys without a `scale` (watch length 4 h) never change with difficulty.

Worked numbers (the test expectations): food need normal 3200, hardcore 4000, story 1600; scurvy onset 70 days normal, 50 hardcore, 140 story; with `hunger_rate` overridden to 1.0 on hardcore the food need is 3200 again while thirst stays x1.25.

Difficulty ordering (story <= normal <= hardcore for every multiplier, normal = 1.0) is a test.

## 6. Provisional numbers (original idea: the Provisional Ledger)

Every balance record carries `provisional`, `owner` and `source`. **All 33 seed numbers are placeholders**, not Canon survival numbers: they exist so the code and tests have real data. `python tools/data_tools/validate_data.py --ledger` writes `docs/PROVISIONAL_LEDGER.md`: what is unfinished, who finalises it, and where it came from (some say "historical, not source-checked"). The rule for later: **B3 is finalised only when no `N*` rows remain.** The N-module numbers in `owner` are my proposal; the N-list is not fixed yet.

## 7. Save format

`core/save_io.gd`:
- The file is an envelope `{save_version, game_version, saved_unix, payload, sha256}` where `payload` is the state as a JSON **string**; the checksum covers that string, so a damaged or hand-edited file is detected (`checksum mismatch`).
- Writing is atomic: write `file.tmp`, then rotate the current file to `file.bak`, then rename `.tmp` to the main file. A crash at any step leaves at least one valid file.
- Reading tries the main file, then the backup (`recovered_from_backup = true`).
- `SAVE_VERSION = 1`. An older save is upgraded by a chain of `migrations[n]` functions (n to n+1); a newer save is refused with a clear message; a missing migration is an error, never a guess.
- **64-bit values are stored as decimal strings.** A JSON double loses integers above 2^53, so `"world_seed": "18446744073709551615"` is a string (schema pattern `^[0-9]{1,20}$`).
- `validate_state(state, registry)` runs the `save_state` schema: unknown item ids in the inventory are errors.

## 8. Things you must know

- **Export:** add `*.json` to the export preset's "Filters to export non-resource files", or the exported game has no data. (Not needed to run from the editor.)
- Provisional values will change; nothing may copy them into code or docs as final.
- Content rule 1 is enforced twice: by the crew schema (`gender` enum) and by `check_project.py`. A test proves a female crew record is rejected by each.

## 9. How to test

On any machine with Python 3.11+ (needs `pip install` nothing for validation):
```
python tools/check_project.py                  # everything: ids, content rules, data model, parity, gdscript syntax
python tools/data_tools/test_data_tools.py     # 14 + 4 data tests
python tools/data_tools/validate_data.py --ledger
```
On your PC with Godot (first real run of the GDScript half):
```
Godot_v4.7.2-stable_win64_console.exe --headless --path game --import
Godot_v4.7.2-stable_win64_console.exe --headless --path game --script res://tests/run_all.gd
```
Expected: `test_schema`, `test_registry`, `test_tuning`, `test_save` all pass. Please paste the output if anything says FAIL; those are bugs I could not see.

Unverified Godot behaviours this module relies on: `--script` runs with autoloads absent (the tests construct `registry.gd` themselves for that reason); `DirAccess.rename_absolute` / `remove_absolute` on `user://` paths; `JSON.stringify` argument order; JSON number parsing as float.
