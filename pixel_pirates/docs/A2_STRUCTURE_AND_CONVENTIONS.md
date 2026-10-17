# MODULE A2 - Project structure, conventions, version control
Status: delivered. Binds every later module. Canon v0.3.

## 1. Decisions (with the options considered)
| # | question | options | decision |
|---|---|---|---|
| A2-1 | Where does the Godot project live? | (a) repo root, (b) `game/` subfolder | **(b) `game/`**. Tools, docs, art references stay outside `res://`, so the exported game never contains them and Godot never imports them. |
| A2-2 | Repo: separate or inside `Videos-motion`? | (a) separate repo now, (b) subfolder now, split later | **(b)**. `pixel_pirates/` is self-contained (own `.gitignore`, `.gitattributes`, README). Split later with `git subtree split --prefix=pixel_pirates` (history kept). Do it before any public release. |
| A2-3 | Data format | JSON / Godot `.tres` / CSV | **JSON for all game data** (diff-able, tool-checkable without Godot, editable in any text editor). `.tres`/`.tscn` only for scenes/resources. Schemas finalised in A5. |
| A2-4 | Dev machine needs Python? | yes / no | **No.** All generated art is committed; Python tools are optional helpers for me/CI. |
| A2-5 | Class access style | `class_name` everywhere / `preload` constants | **`preload` constants for core utilities** (`const Ids := preload("res://core/ids.gd")`). Works in `--script` headless runs even before Godot built its class cache. `class_name` only for scene nodes/resources used in the inspector. |
| A2-6 | Test style | GUT/gdUnit addon / own runner | **Own tiny runner** (`tests/run_all.gd`), zero dependencies, runs headless (no GPU). Revisit if tests exceed ~500 checks. |
| A2-7 | Large binaries | plain git / Git LFS / external storage | **Plain git now.** Decision gate: first single binary > 5 MB or repo > 500 MB -> enable Git LFS (patterns already prepared, commented, in `.gitattributes`). |
| A2-8 | ID grammar | free text / strict | **Strict, machine-checked** (section 4). |

## 2. Folder structure (final)
```
pixel_pirates/
  README.md  .gitignore  .gitattributes  .editorconfig
  docs/            A1..A4 docs, CANON_BIBLE.md, ART_STATUS.md (generated)
  art_bible/       reference measurements, Look Lab stills + report, contact sheet   (not shipped)
  tools/           check_project.py, install_hooks.sh, hooks/, placeholder/, looklab/, probes/   (not shipped)
  game/            <- Godot project root (res://)
    project.godot  .gdlintrc
    core/          engine-independent plumbing: ids, data_loader, log, bus, quality, assets   (autoloads: Log, Bus, Quality, Assets)
    data/          ALL game data as JSON, one folder per domain: look/, crew/, items/, islands/, ships/, ...
    systems/       survival/ economy/ crew/ ship/ combat/ weather/   - pure simulation logic, NO scene or node access (headless-testable)
    world/         ocean/ islands/ cities/   - scenes + scripts that present the world
    ui/            HUD, menus, asset_viewer (current main scene)
    shaders/       post-process (tilt-shift etc., J-modules), water, sprites
    audio/         (K)
    art/           placeholder/<category>/  final/<category>/  manifest/sprites.json   (category = characters|tiles|props|ships|icons|fx|ui|bg)
    tests/         run_all.gd + test_*.gd
```
**Dependency rule (the one that keeps 50 islands maintainable):** `systems/` never imports `world/` or `ui/`; `world/` and `ui/` may read `systems/`; `core/` imports nothing from the others. Systems communicate through `Bus` signals or by being handed data, never by reaching into each other.

## 3. Naming
| thing | rule | example |
|---|---|---|
| files and folders under `game/` | `lower_snake_case`, ASCII | `salt_meat_decay.gd` |
| GDScript classes (`class_name`) | `PascalCase` | `SpoilageModel` |
| functions, variables | `snake_case`; private `_leading_underscore` | `days_until_rot()` |
| constants, enums values | `UPPER_SNAKE_CASE` | `MAX_CREW` |
| signals | past tense, `snake_case` | `ration_cut` |
| scenes | same as root script | `harbor_town.tscn` + `harbor_town.gd` |
| JSON keys | `snake_case` | `"water_litres_per_day"` |
| docs | `UPPER_SNAKE.md` for canon/spec, `A#_NAME.md` for modules | `CANON_BIBLE.md` |
| art assets | `<prefix>_<words>` see 4 | `spr_crew_mannequin_captain` |

## 4. ID grammar (checked by `tools/check_project.py` and `tests/test_ids.gd`)
* **Data IDs** `<kind>_<slug>`, lowercase, digits and `_` only. Kinds: `isl reg crew npc item rcp ship evt loc fac qst dlg clue`.
  **Islands are numeric: `isl_001` .. `isl_999`** (rename-proof; the display name lives in data). Examples: `item_hardtack`, `crew_old_tomas`, `reg_dead_ocean`.
* **Asset IDs** prefixes: `spr` animated/directional sprite, `til` tile, `prp` prop, `shp` ship billboard, `ico` icon, `fx` effect, `ui`, `bg`.
* The registry ID `I001` used in earlier canon text is now the data ID `isl_001`.

## 5. Code conventions
* Typed GDScript everywhere (`var x: int`, `-> void`); `gdlint` clean at max line length 120 (`game/.gdlintrc`); tabs.
* No magic numbers in systems: every balance number comes from `data/` JSON (A5).
* A system exposes `func step(state, dt_game_hours)` style pure functions over plain data (Dictionary/Resource) so it can be unit-tested headless.
* Every system module ships with `tests/test_<system>.gd`. A module is not "done" without a green runner.
* Randomness only through one seeded RNG object passed in (reproducible bug reports, deterministic voyages).
* Logging via `Log` (levels DEBUG/INFO/WARN/ERROR), never bare `print` in game code.
* Save files carry `save_version` (int); every data file carries `"schema": N`. Breaking change = bump + migration function.

## 6. Version control
* **Git**, remote on GitHub (already configured). One long-lived line of work; short topic work per session.
* **Commit message:** `<MODULE-ID>: <what and why>` e.g. `N3: spoilage model + tests`. One logical change per commit. Generated files (placeholder PNGs, `ART_STATUS.md`, stills) are committed WITH the generator change that produced them.
* **Versioning:** SemVer `0.MINOR.PATCH` in `application/config/version`; MINOR bumps at milestones (0.1 vertical slice, 0.2 first region, ...). Tag releases `v0.1.0`.
* **Never commit:** `game/.godot/`, builds, `.exe/.pck`, secrets, store SDKs (A1-7). `export_presets.cfg` may be committed only if it contains no keys/paths to secrets.
* **Committed on purpose:** `*.import` and `*.uid` files (Godot needs them so every clone imports identically).
* **Optional pre-commit hook:** `sh tools/install_hooks.sh` (needs Python): runs `check_project.py` when `pixel_pirates/` files are staged.

## 7. Automatic checks (A7 grows this)
`python tools/check_project.py` (no packages needed; `gdparse` used if installed) verifies:
1. file/folder names (section 3), 2. every JSON under `game/data/` parses and every `"id"` obeys the grammar,
3. **HARD CONTENT RULES in data:** crew records must be `"gender": "male"`; text containing religion/sexual terms FAILS the commit (narrow review list produces warnings; exceptions need a line in `tools/content_allow.txt`),
4. manifest <-> files in `art/placeholder/` (nothing listed-but-missing, nothing present-but-unlisted), 5. GDScript syntax.
It also mirrors `test_ids.gd` so the ID regexes are verified even without Godot. I tested the failure path: a planted female crew record, a religion word, a bad island ID and a badly named file were all caught.

## 8. Original idea of this module: the repository enforces the creative rules
Content rules, naming and IDs are not honour-system documents; they are tests. A future writing session (crew bios, dialogue, item text) cannot accidentally break "no female crew / no religion / no sexual content" without the check failing first.

## 9. Not verified
Godot was never run by me (sandbox cannot download it). The GDScript is parser-checked (gdtoolkit 4.5.0, no syntax errors, no lint problems) but NOT executed. Specific unverified points: `--script` runs seeing the `Assets` autoload (tests avoid depending on it), `Color.html()` use in `test_assets.gd`, `ResourceLoader.exists()` behaviour for un-imported PNGs (code falls back to reading the file). First run result from the user's PC will settle these.
