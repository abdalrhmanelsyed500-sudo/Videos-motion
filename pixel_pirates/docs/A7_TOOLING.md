# A7 - Tooling: debug console, teleport, island workbench, automatic checks

Status: Python parts RUN and tested in the sandbox. GDScript parts (console, state, world rules, UI) are syntax- and lint-checked only: **Godot cannot run in the sandbox, so none of it has executed yet.** The first run on the dev PC is the real test (steps below).

## 1. Automatic checks

| command | what it does | needs |
|---|---|---|
| `python tools/check_all.py` | every check below in one go, writes `build/check_report.md`, exit 1 on any failure | Python + `pip install gdtoolkit` |
| `python tools/check_all.py --quick` | same, skips the island-kit tests | |
| `python tools/check_all.py --godot PATH` | also runs the in-engine tests (import, then `res://tests/run_all.gd`) | Godot exe |
| `tools\run_godot_tests.bat` / `tools/run_godot_tests.sh` | only the in-engine tests, output in `build/godot_tests.txt` | Godot exe, **no Python** |
| `python tools/check_project.py` | data schemas, refs, world rules, parity fixtures, island kit, content rule 1, **registry doc freshness, duplicate GDScript member names, dead `res://` paths** | Python |

`check_project.py` is the pre-commit hook (`tools/install_hooks.sh`).

The in-engine step fails when: the `TESTS: N checks, M failed` line is missing (runner crashed), M > 0, or the output contains `SCRIPT ERROR` / `Parse Error` / `Compile Error` (Godot can exit 0 after a script error, so the exit code alone is not trusted). This logic was tested with four fake Godot executables (pass, fail, silent, script error).

Godot location for the .bat/.sh: environment variable `GODOT_EXE`, or the path alone on one line in `tools/godot_path.txt` (gitignored).

### Why the new static checks exist
Godot is not available to CI here, so `gdparse` (syntax) is not enough. While writing A7 the debug console had a `var _input: LineEdit` next to the engine callback `func _input(event)` - valid syntax, compile error in the engine. Two checks now catch that class of bug and were proven on exactly that case.

## 2. World rules in GDScript (`core/world_rules.gd`)
The five world rules (`dist_short`, `not_mutual`, `asym`, `visible_no_landmark`, `visible_self`) now exist in Python and GDScript. `Registry` runs them after the reference check and reports `WORLD: ...` errors. Both implementations are run against `game/tests/fixtures/world_cases.json` (14 hand-written cases; Python 14/14, GDScript unrun).

## 3. Debug console (`ui/debug_console.gd`, autoload `DebugConsole`, debug builds only)
Open with **F1** or **`** (backtick). Up/Down = history, Tab = complete, Esc = close. The command logic lives in `core/console_commands.gd` (no UI), so `tests/test_console.gd` runs it headless.

| command | use |
|---|---|
| `help [cmd]` | list commands or one usage |
| `data counts` / `data list <kind>` / `data show <kind> <id>` / `data reload` | inspect and hot-reload data |
| `check` | reload and run all validation (schemas, refs, world rules) |
| `tuning <key>` / `tuning list [prefix]` | base and effective (difficulty-scaled) balance number |
| `mode [id]` / `mode override <rate> <0-3>` / `mode clear` | difficulty and per-system toning |
| `island list` / `island info <isl_id>` | registry and baked-map facts (explore minutes, POIs, landings) |
| `tp island <isl_id> [landing\|<slot>]` / `tp xy <x_m> <y_m>` | teleport (world position in metres) |
| `time` / `time add <h>` / `time set <day> <hour>` | game clock |
| `give <item_id> [n]` / `inv` | items and cargo weight |
| `seed` / `seed world\|weather <digits>` | 64-bit seeds |
| `save [name]` / `load [name]` | `user://saves/<name>.json` with the A5 hashed, atomic format |
| `quality [profile]` / `log [level]` / `perf` | profile, log level, FPS/memory/draw calls |
| `echo`, `clear` | utilities |

To add a command: write `_c_name(args)` in `console_commands.gd`, register it in `_register_all`, add a line to `tests/test_console.gd`.

`GameState` (`core/game_state.gd`) is a minimal state that serialises exactly to the `save_state` schema. The real game state (J1) replaces it through `DebugConsole.attach_state()`; the console does not change.

Island viewer: click anywhere on the island to see the terrain, elevation, nearest POI and walking distance from the landing.

## 4. Island workbench (`tools/island_kit/new_island.py`)
One command creates a registry record, finds a seed, bakes, checks, and renders a preview:

```
python tools/island_kit/new_island.py --id isl_012 --name "Saltglass" --tier 2 --template tpl_mesa_cliffs --kit kit_arid ^
    --offers fresh_water,game --hook-kind beacon_tower --region reg_xxx --x-km 410 --y-km -220 [--hook "text"] [--dry-run]
```
- Refuses: duplicate or malformed id, template not allowed for the tier, unknown kit/offer/hook kind, hook-kind quota (max 4) and template+kit quota (max 3) already used.
- Seed search starts from a hash of the id (deterministic) and skips seeds that fail a bake rule, a map check, or **look like an island already in the file** (silhouette overlap >= 0.85).
- New records are `status: planned`, `provisional: true`, `owner: E3`.
- `--region` must exist before `check_project.py` accepts the record: regions come from E1. Until then, use `--islands-file` pointing at a scratch file.
- `--dry-run` prints what would happen and writes nothing.

## 5. Island registry document
`python tools/data_tools/registry_doc.py` writes `docs/ISLAND_REGISTRY.md` from the data files (tier counts against targets, cluster share, neighbours with km and sloop hours, template, kit, hook kind, explore minutes, status). `check_project.py` fails when the document is stale, so the registry cannot drift from the data.

## 6. First run on the dev PC (the real test of the GDScript)
1. `tools\run_godot_tests.bat` (set `GODOT_EXE` first). Expect `ALL TESTS PASSED`. Paste `build\godot_tests.txt` back if not.
2. Open `game/` in Godot, press F5, press F1: type `help`, `check`, `data counts`, `island list`, `tp island isl_903`, `give item_hardtack 5`, `inv`, `save a`, `load a`, `perf`.
3. Switch the main scene to `res://ui/island_viewer.tscn` (Project Settings) to try click-to-inspect.

## 7. Decisions
- A7-1 the console core is separate from its UI, so it is testable without a display.
- A7-2 `GameState` mirrors the save schema now; J1 swaps the real state in.
- A7-3 world rules exist twice, proven equal by one shared fixture.
- A7-4 never trust the Godot exit code alone; parse the result line and engine errors.
- A7-5 static checks for Godot-only mistakes live in `check_project.py` (collisions, dead paths).
- A7-6 the workbench enforces the Silhouette Quota at creation time, not only at audit time.
- A7-7 the registry document is generated and freshness-checked.

## 8. Limits (honest)
- No GDScript has been run. Likely first-run failures: `RegEx.create_from_string`, `%-8s` string formats, `Performance` monitor constants, autoload input order, `Color.html()`.
- `tp` sets the state position only; there is no player node yet (J-modules).
- The editor itself (a map/data editor inside Godot) is not built: the data are JSON edited in any editor, validated by `check_all`, and islands are authored through the workbench. A custom in-engine editor is not worth its cost before the data volume exists; revisit at F0.
