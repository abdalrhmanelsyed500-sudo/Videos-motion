# IRON ATLAS: SHATTERED WORLD

A fictional regional-conflict strategy game built in Godot 4.7 / GDScript.
The 200-district scenario is the default; the original 24-district map remains
selectable. See [`docs/STATUS.md`](docs/STATUS.md) for verified scope and limits.

## Launch in Godot

1. Install **Godot 4.7.x** (the project declares the 4.7 feature set).
2. In the Godot Project Manager choose **Import** and select
   `iron_atlas/game/project.godot`, then open the project. Let the editor import
   assets and press **F5** to run the project.
3. Alternatively, from the repository root, run `godot --editor --path iron_atlas/game`
   and press F5; after the first import, `godot --path iron_atlas/game` runs it.

The native desktop build could not be executed in this sandbox. The actual UI
was inspected through Godot's web template and a software WebGL renderer; see
[`docs/stage2_shots/`](docs/stage2_shots/).

## Play the regional loop

- Start a campaign and choose a seed/map size. Time begins **paused**.
- Select a district on the map; the Region panel shows controller, political
  support, infrastructure, stocks and the supply route. The mouse wheel zooms;
  middle-drag pans. The right panel scrolls for additional actions.
- Recruit in a controlled district. In **Arms**, select an item already in
  inventory; in **Forces**, select a formation and issue it. New squads need
  12 reserve personnel per equipment package. Protective and communication
  gear is assigned to existing squads; medical kits are used during recovery.
- With a formation selected, choose **Move** and click a destination connected
  by land. Increase clock speed. On hostile contact time pauses: choose tactical
  battle or resolve one engagement automatically. In tactical view left-click
  a friendly unit and right-click terrain or a hostile to issue orders.
- Invest in security, infrastructure and local recovery. Review reports for
  casualties, shortages, delivery and diplomacy. **Politics** shows transition
  conditions and lets you declare a conflict, offer a ceasefire and negotiate.
- **Save** writes slot 1; the main menu loads the first available slot. Saves
  are desktop `user://saves/slot_N.json`; the WASM test filesystem is transient.

## Automated tests and measurements

From the repository root, with Node.js and npm installed:

```sh
(cd pixel_pirates/tools/godot_node && npm ci)
bash iron_atlas/tools/run_suite.sh /tmp/iron_atlas_suite.log
python3 iron_atlas/tools/benchmark_stage2.py
```

The suite invokes the actual Godot 4.7.2 WASM engine through the existing
read-only shared harness. It includes the four Stage 1 suites and five Stage 2
suites, rejects script errors, and requires a nonzero PASS check count. The
benchmark script uses Python's Unix `resource` module and measures headless
simulation, **not FPS**. Sample results and method are in
[`docs/STAGE2_PERFORMANCE.md`](docs/STAGE2_PERFORMANCE.md).
