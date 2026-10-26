# EGYPTIAN TUKTUK MAYHEM — Phase 2 Vehicle QA Matrix

Ten scenarios, run headless through the **real Godot 4.7.2 engine** (wasm, fixed 60 fps physics,
`--fixed-fps 60`) via `tools/run_suite.sh`. Scenarios 1–8 live in `game/tests/test_vehicle.gd`
(isolated rig: flat 800×800 m floor + spawned tuk-tuk, real `Input` actions injected as
`InputEventAction`), scenario 9 in `game/tests/test_camera.gd` (vehicle + chase camera rig),
scenario 10 in `game/tests/selfplay.gd` (full district + mission + HUD, real logic).

**Latest run:** `/tmp/tkm_p2_s7.log` (mirrored to `docs/logs/suite_p2_final.log`) — SUITE
**7/7 PASS** (test_reward 8, test_mission 14, test_save 7, test_vehicle **31**, test_camera
**10**, test_district 22, selfplay **11** = **103 checks, 0 failed**). Phase 2 QA scenarios
contribute **52 assertions**.
The runner rejects a zero-check suite: a `PASS` line with `0 checks` counts as a failure
(`tools/run_suite.sh`), so no scenario can silently no-op its way to green.

| # | Scenario | Rig | Inputs / stimulus | Assertions (tolerances) | Result |
|---|----------|-----|-------------------|--------------------------|--------|
| 1 | Acceleration from rest | isolated | `accelerate` 90 frames (1.5 s) from (0,0,0) | speed > 10 m/s (vmax 24, accel 13 with taper); covers ground z < −8 m | 2/2 PASS |
| 2 | Braking predictability | isolated | from ~14 m/s, `brake` 25 frames | speed < 50 % of entry **and** > −0.6 (no jump straight to reverse); speed finite | 2/2 PASS |
| 3 | Reverse | isolated | `brake` from rest 60 frames, then `steer_left` 40 frames | speed < −2 m/s (brake-to-reverse engages); moves +z; yaw mirrors (Δyaw < −0.05 rad — left input while reversing turns the nose left, i.e. sign-flipped vs forward) | 3/3 PASS |
| 4 | Steering authority | isolated | `steer_left` 40 frames at 5 m/s, then at 14 m/s | \|Δyaw\| > 0.30 rad at low speed; > 0.15 rad at medium; medium < low (speed-sensitive fade, high-speed stability) | 3/3 PASS |
| 5 | Drift initiate + recover | isolated | 14 m/s, `accelerate`+`steer_left`+`handbrake` 40 frames, release 90 frames | lateral slip \|lat_vel\| > 1.5 m/s during input; drift_time > 0.3 s accumulated; after release \|lat_vel\| < 0.8 (traction returns, no stuck slide); drift timer resets; MissionMgr reachable for the bonus | 5/5 PASS |
| 6 | Collision: severity, cooldown, recovery | isolated | accelerate into a wall (8×6×1 m at z = −16) from rest; **sampled at the contact frame**; then steer away | collision registered (counter increments); speed after < speed at contact (energy lost); speed after > 20 % of contact speed (loss bounded, not a full stop); penalty rate: extra hits ≤ 2 + contact_frames/30 **and** < contact_frames/4 (0.5 s cooldown ⇒ ≪ frame-rate spam); no penetration (z > −16.5); yaw responds within 60 frames of steering away (recovery path) | 7/7 PASS |
| 7 | Ground contact over bumps | isolated | 180 frames at 12 m/s, throttle | min y > −0.3 m (never below the road surface); y < 1.2 m at end (no bounce-launch spam); keeps rolling > 3 m/s | 3/3 PASS |
| 8 | Ramp jump + landing + fall recovery | isolated | placed at 14 m/s facing west, `launch()` invoked (the district trigger wiring itself is proven end-to-end in scenario 10); then placed at y = −10 m (off-world fall) | airborne persists ≥ 5 consecutive frames (not a one-frame flag); jump gains > 0.5 m height; lands again (airborne false); rests on road (y < 1.0, no penetration/bounce loop); steering responds after landing (control kept); below `fall_reset_y` the vehicle emits `request_reset` (recovery path, no void death) | 6/6 PASS |
| 9 | Camera behaviour (C1–C6) | vehicle + chase cam | spawn, drive, sharp turn, wall impact, rest 90 frames, reverse | **C1** distance < 8 m on frame 2 — first-frame snap regression guard (kills the scene-change black-frame fly-in); **C2** arm distance inside [1.4, 7.5] m and pitch inside (−80°, −5°) while driving; **C3** framed through a sharp turn (d < 8.5 m) with camera-yaw vs heading difference < 1.2 rad (≈69°) — follows heading without copying jitter; **C4** still framing after an impact (d < 8.5 m) and finite camera position (no NaN shake); **C5** at rest 90 frames: total camera drift < 0.05 m (no idle oscillation); **C6** reversing: speed < −1 m/s and distance < 7 m (pull-in keeps the backing view tight and readable) | 10/10 PASS |
| 10 | Full mission under stress | district + mission + HUD | real offer→accept→board flow; drift manoeuvre mid-mission; ramp at (−40, 60) mid-mission at 18 m/s; teleport-free delivery to the dest ring; result; dismiss; stray extra accept | offer appears at the stand; passenger boards (state DRIVING); drift manoeuvre registered while driving **and** `drift_earned` > 0 (bonus paid through the real MissionMgr path); ramp launch sustains ≥ 3 airborne frames **and** gains > 0.5 m mid-mission; lands back on the road; fare paid on delivery (balance increases); next passenger waiting after result; balance kept after dismiss; stray accept at IDLE does **not** pay twice | 11/11 PASS |

## Meaningful-tolerance notes

* Every threshold is derived from the data tables (`data/vehicles/tuktuk_base.json`,
  `data/missions/reward_tuning.json`), not from observed output — e.g. S1's 10 m/s follows from
  accel 13 m/s² with the 0.55 top-end taper; S6's 20 %-kept floor from `impact_loss` 0.35 with
  severity clamped to [0.25, 1].
* S6's spam bound is **rate-based**: with a 0.5 s cooldown (30 frames) pressing into a wall may
  legitimately re-penalise on the cooldown cadence, so the assertion allows that cadence and
  rejects anything approaching per-frame (extra hits must also stay below contact_frames/4).
* Timings assume the engine's fixed 60 fps physics step (`--fixed-fps 60`); the same suite under
  software rendering dilates real time but never physics deltas.

## Known limitation (declared, not hidden)

* Scenario 7 runs on the isolated flat rig: it proves no floor penetration, no bounce-spam and
  maintained contact. The only elevated surface in the district is the **designated ramp**
  (visual wedge + polled radius trigger, see PHASE2_REPORT §6); there are no sloped colliders,
  so "bumps" beyond the speed-bump strips (visual + `speed_bump` collider box, 0.14 m tall) are
  not part of the P1 district. The speed bumps are crossed in scenario 10's mission route and in
  the render evidence.
