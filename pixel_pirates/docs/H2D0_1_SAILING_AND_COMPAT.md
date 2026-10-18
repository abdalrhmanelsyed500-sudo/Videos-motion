# H2D-0.1: Compatibility, runtime cleanup and sailing controls (WRITTEN, NOT RUN IN GODOT)

**Read this first.**
- Nothing here has run in Godot. The sandbox cannot run it. What did run: Python (a twin of the helm, the fixture and the shader/GDScript checks), gdparse, gdlint, a GLSL syntax pass and `tools/check_all.py --quick` (ALL PASSED, which includes none of the GDScript logic in-engine).
- **I never received your console output.** I only know from your message that it showed an OpenGL 3.3 / ANGLE notice, an error at `sea_view_3d.gd:193`, image-loading warnings and integer-division / shadowing / unused warnings. Everything below was found by reading the source (mine and Godot's) and is **unverified until you run it**.
- You test by hand, so there are no batch files in this step. Open the project in Godot and press F5.

## 1. Which renderer runs on the HD 3000, and does it matter
Windows Godot tries native OpenGL 3.3 first. If the driver reports less (the HD 3000 reports OpenGL 3.1), the engine prints "Your video card drivers seem not to support the required OpenGL 3.3 version, switching to ANGLE" and runs **OpenGL ES 3.0 on top of Direct3D 11 (ANGLE)**. That fallback is a project setting we keep on (`rendering/gl_compatibility/fallback_to_angle=true`), so the message is expected and not a fault of the project. It is almost certainly what your PC does. **Not confirmed by a log.**
What I could not know: whether the scene *looks* right through ANGLE and how fast it is. So the HUD now has an always-on renderer line (for example `renderer: OpenGL ES 3.0 via ANGLE (Direct3D 11) [opengl3_angle]  GPU: ...`), and the scene writes `user://h2d0_diagnostics.txt` (Godot, OS, method, driver, adapter, API version, driver info, window size, colour-transfer result). On Windows that file is in `%APPDATA%\Godot\app_userdata\Crown of the Seas\`. If you can, send me that one small file; it answers the question.
Optional, dev PC only: Project Settings > Rendering > GL Compatibility > Driver > Windows = `opengl3_angle`, which skips the failed OpenGL attempt and the message. Do not force it for a release: other PCs should use native OpenGL.
Note: the engine's Compatibility renderer has no DOF blur; the HD-2D tilt-shift is our own post pass (unchanged).

## 2. Runtime cleanup (what each warning was, and the fix)
| Symptom | Real cause | Fix |
|---|---|---|
| Error at `sea_view_3d.gd:193` (`_register_globals`) | I called `RenderingServer.global_shader_parameter_get_list()` to see whether a global uniform existed. In the engine that function is editor-only: outside the editor it always returns an error. Not a warning to suppress: the design was wrong. | The globals are declared statically in `project.godot` `[shader_globals]` (twelve `h2d_*` entries, which is also how Godot wants them: shaders need them at compile time). The script only calls `global_shader_parameter_set`, which is cheap and legal at runtime. |
| Image warnings ("loaded resource as image file, this will not work on export") | I read the PNGs with `Image.load_from_file("res://...")`, which bypasses the import system. | The art is loaded with `load()` as `Texture2D`; `.png.import` files for the six art PNGs are shipped, with lossless, no-mipmap settings so pixel art stays exact (`compress/mode=0`). The data map is read back with `get_image()`. **The six `.import` files are hand-written, copied from the format of a real Godot demo project; Godot may rewrite them on first open. Unverified.** `core/assets.gd` keeps `Image.load_from_file` only as a fallback for the placeholder art outside the import pipeline. |
| Integer division | Two real `int / int` sites | Fixed (float division where a fraction was meant). |
| Shadowing | `core/ocean.gd`: a local `tuning` hid the `tuning()` method | Renamed `tuning_map`. |
| Unused variable | `asset_viewer.gd` unused `h`; `sea_view_2d.gd` unused private `_v` | Removed. |
| (hardening, not a known error) | Texture lookups inside loops/branches in three shaders | `textureLod(..., 0.0)` in `island.gdshader` and `post.gdshader`. |
`tools/h2d/check_gd_warnings.py` is a rough scanner for these classes (integer division, member shadowing, unused locals); it is a heuristic and **not** Godot's analyser. It reports 0 findings now. Godot may still print warnings I cannot predict; send me the first lines and I will fix those too.

## 3. The old sailing, and why it felt bad (found by reading the code)
- A constant 14 deg/s turn that stopped dead when the key was released, so it felt on/off.
- The picture lagged the real heading by 0.35 s (a smoothing filter), so what you saw did not match what you pressed.
- The wake was always straight, so the ship seemed to slide sideways through its own wake.
- Speed was smoothed over 2 s and fell off a cliff at the no-go angle, with no explanation on screen.
- Only 16 sprite headings and no heading, wind or no-go display at all.

## 4. The new helm (`game/h2d/helm.gd`)
**Keys:** `A` / `Left` = turn to port (left). `D` / `Right` = turn to starboard (right). `Z` / `X` = less / more turn sensitivity (x0.4 to x2.0, default x1.0).
**What happens, in the default tuning (computed by the Python twin; the feel itself is for you to judge):**
- Press D: the rudder goes over in about 0.12 s, the bow starts to swing at once and reaches full turn rate (36 deg/s at full speed) in about 0.6 s. 90 degrees takes about **2.8 s** with the key held.
- Release: the turn dies away in about 0.1 s; the ship carries on about **6.6 degrees** more, then holds the heading. It does not keep spinning.
- A short tap of 0.2 s turns about **5 degrees**, so fine course corrections are possible.
- Reversing (D then A) swings back straight away.
- Steering works at any speed; the rudder just bites less when the ship has lost way (45% of the turn rate at a standstill). That is why you can always bear away from the wind.
- The heading you see is the real heading (no display lag). The 16 sprite headings are drawn from it; the wake now curves the way the ship turned.
- Speed has momentum: +1 kn takes about 2.5 s of sailing, losing speed 3.5 s. Pointing straight into the wind for 8 s bleeds a 5 kn ship to about **1 kn**, not to a dead stop. This replaces the cliff.

**The no-go zone and "IN IRONS"** (the sail model itself is unchanged: sails cannot draw within 40 degrees of the wind, `ship.no_go_deg`):
- Red wedge on the compass = the 40-degree zone on each side of the wind. Green arcs = the best sailing (80 to 140 degrees off the wind).
- When the bow is inside the red wedge you get a pulsing **IN IRONS** banner and a line that says which key leaves fastest (the side you are already leaning to) and why speed is falling.
- With the bow in the green you read "Beam reach: good speed (96% of the best the wind allows)".
- Outside both, the line says the sails give N% of the best speed and to turn towards the green zone.

**The helm display (bottom left, `helm_hud.gd`):** a compass ring (north up, like the world) with the ship's bow (yellow, red when in irons), the wind arrow with its direction, the red and green zones, a rudder bar (A left / D right), and a speed bar whose solid part is your speed and whose white tick is what the sails could give at this heading. Under it: heading in degrees, speed, and the point of sail.
The text HUD (F3 hides everything) shows the renderer, time, wind, turn rate, sensitivity and the advice sentence.

## 5. Tuning without touching code
`game/data/tuning/tuning_helm.json`, nine keys (owner N13, all provisional): `helm.max_turn_deg_s` 36, `helm.min_steerage` 0.45, `helm.steerage_full_kn` 3.0, `helm.rudder_rise_s` 0.12, `helm.rudder_return_s` 0.10, `helm.yaw_build_s` 0.18, `helm.yaw_brake_s` 0.10, `helm.speed_gain_s` 2.5, `helm.speed_loss_s` 3.5.
- Too twitchy: lower `max_turn_deg_s` (try 28) or press Z.
- Too sluggish: raise `max_turn_deg_s` (try 45) or press X.
- Coasts too far after release: lower `yaw_brake_s`. Wants a little weight: raise `yaw_build_s` to 0.3.
- Speed changes too slowly or fast: `speed_gain_s` / `speed_loss_s`.
Values are read at start-up; re-run (F5) after editing.
Tests (`tests/test_helm.gd`, never run in Godot yet) replay `tests/fixtures/helm_cases.json`, made by `tools/h2d/helm_logic.py --fixture`, and check the feel limits (90 deg between 1.5 and 4 s, coast under 9 deg, 0.2 s tap between 2 and 10 deg, head-to-wind speed bleed), `point_of_sail`, `escape_direction`, and that `Helm.DEFAULTS` equal the JSON.

## 6. How to start it
1. Unzip the project anywhere (the zip's top folder is `pixel_pirates`).
2. Godot 4.7.x: Project Manager > Import > select `pixel_pirates/game/project.godot`. On the first open Godot imports the art (a short progress bar). Errors in the Output panel at that point are what I want to see.
3. Press **F5**. The main scene is `res://h2d/h2d0.tscn`. If F5 asks for a main scene, choose it.
4. Wait about a second for the colour calibration, then sail.

## 7. What to look at, in order (a two-minute test)
1. Bottom of the Output panel: copy any red or yellow lines.
2. HUD line 2 shows which renderer is really running.
3. Hold D for 3 s: about 100 degrees, wake bends to port, then holds the heading when you release.
4. Tap A briefly several times: small, predictable steps.
5. Point the bow at the wind arrow: red wedge, IN IRONS banner, speed falls slowly; press the key it names and speed returns.
6. Z and X: the turn rate changes, the HUD shows the new sensitivity.
7. Tell me what is too fast, too slow or unclear. The helm numbers are guesses made by simulation.

## 8. Not done, on purpose
No H2D-1, no H2D-2, no E2, no new content, no change to the wind, the sail polar, the weather or the world. The ocean look and its speed on the HD 3000 are still unmeasured. The bench (`B`) still exists but you do not need it.
