# Crown of the Seas (working title)

Open-world pirate-life simulation. Godot 4.7.2, Compatibility renderer, typed GDScript. Windows-first, no store dependency.

| folder | what |
|---|---|
| `game/` | the Godot project (open THIS folder in Godot). `res://` = `game/` |
| `docs/` | design + engineering docs (A1 stack, A2 structure, A3 art bible, A4 placeholder pipeline, A5 data architecture, A6 island kit, A7 tooling, B1 pillars), `CANON_BIBLE.md`, `ART_STATUS.md` |
| `art_bible/` | reference measurements, Look Lab stills + report, placeholder contact sheet |
| `tools/` | Python helpers (`check_all.py`, placeholder generator, Look Lab, island kit + workbench, data tools) and `probes/` (GPU probe) - none needed to RUN the game. `run_godot_tests.bat` needs no Python |

## First run on a fresh clone (Windows)
1. `Godot_v4.7.2-stable_win64_console.exe --headless --path game --import`  (builds the import cache once)
2. `Godot_v4.7.2-stable_win64_console.exe --headless --path game --script res://tests/run_all.gd`  -> last line `TESTS: N checks, 0 failed -> PASS`
3. Open `game/` in the editor and press F5: the Placeholder Asset Viewer starts (pure 2D). Add `-- --quality=dev_lite` to the command line for the light profile.

4. `tools\run_godot_tests.bat` does steps 1-2 in one go (set `GODOT_EXE` or fill `tools\godot_path.txt`). In the running game press **F1** for the debug console (`help`). Everything about tooling: `docs/A7_TOOLING.md`.

Rules that bind every change: see `docs/A2_STRUCTURE_AND_CONVENTIONS.md` and the HARD CONTENT RULES in `docs/CANON_BIBLE.md`.
