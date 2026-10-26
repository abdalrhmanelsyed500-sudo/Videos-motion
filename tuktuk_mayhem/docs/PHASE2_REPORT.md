# EGYPTIAN TUKTUK MAYHEM — Phase 2 Report
## Professional driving quality, vehicle feel, camera polish & QA

Branch `arena/7464ca7a-videos-motion`, base commit `0d84b1f` (Phase 0+1). Engine: Godot
4.7.2-stable web template (Compatibility / OpenGL ES 3), unchanged version. Everything below was
**executed and verified in this sandbox** (headless wasm engine for logic, headless Chromium +
SwiftShader software WebGL2 for render evidence); nothing is claimed for native Windows
performance, which remains unmeasured until the Phase 10 export.

---

### 1. Method: recovery, baseline, inspect-before-edit

* The sandbox had been reset (workspace rolled back to pre-Phase-1 `e376391`, toolchain gone).
  Recovered safely: `git fetch origin --tags` + `git reset --hard
  origin/arena/7464ca7a-videos-motion` **after** confirming the working tree was clean (nothing of
  the user's was lost), landing back on `0d84b1f`; toolchain rebuilt with the project's own
  `tuktuk_mayhem/tools/bootstrap_sandbox.sh` (venv, npm deps, Chromium libs).
* **Baseline suite re-run before any edit:** 6/6 PASS, 66 checks (`/tmp/tkm_base_p2.log`).
* Every touched file was read in full first (current implementation, dependencies, existing
  behaviour) and changed by the smallest safe edit that met the objective; after each edit:
  `gdlint` + `gdparse`, targeted test, then the full suite.
* Post-change suite: **7/7 PASS, 103 checks** (`/tmp/tkm_p2_s7.log`, mirrored to
  `docs/logs/suite_p2_final.log`) — the six Phase 0/1 suites (reward 8, mission 14, save 7,
  district 22 + vehicle/selfplay rewritten below) plus the new camera suite. Boarding/delivery economics, input bindings and the Pixel Pirates project were
  not touched (drift bonus excepted — directive-mandated).

### 2. Camera diagnosis (causes, not symptoms)

Inspection of the Phase 1 `chase_cam.gd` found seven concrete causes of the rough feel:

1. **Origin-lerp transient:** the camera started at the scene origin and lerped to the arm pose,
   producing a fly-in (and a black first frame) on every scene change.
2. **Raw heading copy:** camera yaw was set directly from the vehicle yaw each frame, copying
   every steering tick into the view (jitter, no damping).
3. **No look-ahead:** the camera aimed at the vehicle only; in turns and drifts the road the
   player was about to take left the frame.
4. **FOV snap:** speed-linked FOV was assigned instantly, so impacts that killed speed jerked the
   projection.
5. **No wall awareness:** the arm was a fixed offset; against buildings the camera clipped
   through geometry.
6. **Unreadable reverse:** backing up used the forward framing (full distance, no pull-in).
7. **No collision feedback:** impacts produced nothing in the camera at all.

### 2b. Visual foundation fixes (found by inspecting the render evidence)

Two Phase 1 defects made the district itself render wrong; both were diagnosed from the shots,
not assumed:

* **Vertical ground:** `_quad()` created `QuadMesh` strips without laying them flat — a QuadMesh
  is born in the XY plane, so the 460 m ground, every road and every sidewalk stood up as a
  vertical wall (this is why the Phase 1 "street view" frames are frame-filling asphalt).
  Fix: `rotation.x = -PI/2` in `_quad()` (normals up, UVs/tiling and strip transforms unchanged).
* **Upside-down sun:** the `Sun` DirectionalLight3D basis pointed the light upward from below the
  horizon — vertical faces lit, every horizontal face black — and ambient was disabled
  (`ambient_light_source = 1`). Fix: proper ~50° elevation from the south plus a warm ambient
  fill (energy 0.45) in `district_p1.tscn`. Shadows remain off (P1 perf decision, unchanged).

Both fixes are scene/builder-level; no gameplay logic touched. Verified by probe renders
(horizontal asphalt ring, lit sidewalks, horizon and sky correct) before the evidence run, and
by the final shot set itself. An errata paragraph was appended to `docs/PHASE1_REPORT.md`.

### 3. Camera implementation (`scripts/vehicles/chase_cam.gd`, rewritten in place)

* **First-frame snap** (`_armed`): frame 1 places the camera exactly at the arm pose — the
  scene-change transient is gone (regression-guarded by QA C1: distance < 8 m on frame 2).
* **Frame-rate-independent exponential smoothing** everywhere: `k = 1 − exp(−rate·Δ)` — yaw 6/s,
  position 10/s, FOV 4/s. Never snaps on impacts, never oscillates at rest (QA C5: < 0.05 m idle
  drift over 90 frames), identical behaviour at any frame rate.
* **Dynamic framing / look-ahead:** aim point = pivot + travel direction ×
  `clamp(2.0 + 0.15·|v|, 2, 6)`; travel direction blends heading with lateral slip, so drifts
  stay visible and the road stays in frame (QA C3). Reversing aims −2.5 m along the backing
  direction (show where you're going).
* **Heading follow without physics jitter:** yaw is a damped shortest-arc follow of the smoothed
  heading; steering ticks are filtered by the exponential, not copied (QA C3: |yaw diff| < 69°
  through a sharp turn while still framing).
* **Reverse readability:** arm distance ×0.85 when speed < −0.5 (pull-in), camera stays behind
  the vehicle's rear (QA C6).
* **Wall-aware arm:** `RayCast3D` spring arm (mask 1) shortens to the hit point −0.3 m, floor
  1.6 m — no clipping through buildings.
* **Bounded decaying shake:** `add_shake(strength)` adds `strength×0.02`, clamped to 0.35 m,
  decaying 1.2/s — proportional to collision severity, finite (QA C4), never per-frame spam.

### 4. Vehicle feel (`scripts/vehicles/tuktuk.gd`, same architecture, data-driven)

Architecture preserved: `CharacterBody3D`, scalar forward speed + lateral slip vector, all
numbers from `data/vehicles/tuktuk_base.json` (no gameplay constants in code). Changes:

* **Acceleration taper:** `accel × (1 − 0.55·(v/vmax)²)` — lively off the line, honest top end.
* **Smoothed steering with return-to-center:** input → `steer_smooth` 10/s exponential; release
  recenters at `steer_return` 8/s. Speed-sensitive authority fade (`steer_speed_fade` 0.45)
  keeps it mischievous at low speed and predictable at high speed (QA S4).
* **Brake-to-reverse** preserved from P1 (deliberate, readable: brake first halves speed, only
  from < 0.5 m/s does it engage reverse — QA S2/S3).
* **Visual-only body layer:** pitch under throttle/brake, roll from steer + slip, landing squash
  — applied to the `BodyMesh` child; the physics root transform is never touched, so feel comes
  from motion, not from faked physics.

### 5. Controlled drift (deliberate mechanic, not accidental slide)

* **Entry:** handbrake, or fast steering (|steer| > 0.8) above `drift_speed_min` 12 m/s, with
  |speed| > 3. Grip target drops from `grip_lat` 9 to `drift_grip_lat` 2.6 — through a
  `drift_grip_smooth` 6/s exponential, so entry and exit are smooth, never binary.
* **Clamped lateral velocity:** slip is capped at `lat_max` 8 m/s (direction preserved) —
  dramatic but never uncontrollable; no straight-road slide (grip stays 9 without drift input,
  QA S5 checks recovery to |lat| < 0.8 after release — traction returns, no stuck slide).
* **Frame-rate independence:** all grip/slip terms scale with Δ through exponentials.
* **Drift-time tracking:** sliding state (|lat| > 1.5 and |v| > 5) accumulates `drift_time`;
  on slip end, ≥ `drift_min_s` 0.7 s reports to `MissionMgr.report_drift(seconds)`.
* **Economy (data-only):** `reward_tuning.json` → `drift_bonus_per_s` 1.5 E£/s,
  `drift_bonus_cap` 4.0 E£ per mission, toast once per drift, shown as its own term in the
  result-card breakdown, inside the existing 120 E£ reward cap. Pay-once verified under stress
  (QA scenario 10).

### 6. Jumps / ramps (designated launch surface — honest limitation)

* The P1 district has **no sloped colliders** (strips are flat boxes), and the ground-ray jump
  trigger (`normal.y < 0.9`) could therefore never fire. Rather than fake physics slopes, the
  brief's fallback is implemented and declared: a **designated ramp** at (−40, 60) on the south
  ring — an authored visual wedge (`ramp.mesh.json`, 6 triangles, generated by the project's own
  `tools/make_models.py`, FINAL label — same authored pipeline as all P1 models) plus a
  **radius trigger** polled by the district (`_poll_ramps`: distance < 3 m and cooldown 1.5 s
  expired → `tuktuk.launch()`).
* `launch()` requires |speed| ≥ `jump_speed_min` 8 m/s and applies `jump_impulse` 9.0 ×
  clamp(v/vmax, 0.5, 0.85) upward — bounded and speed-scaled (apex ≈ 0.56 m at the minimum
  launch speed, ≈ 1.6 m at top speed; airtime 0.5–0.85 s).
* **Two integration bugs found and fixed while proving the jump honest:** (1) the on-floor
  vertical clamp (`minf(velocity.y, 0)`) silently cancelled the launch impulse — the render
  dumps showed y never leaving the road; positive y velocity now survives the ground frame
  (resting stays pinned, landings still never bounce). (2) at exact rest height the body has no
  floor contact, so `airborne` flickered true while standing still — which made `launch()`
  early-return AND let a one-frame flag pass the old tests. Grounded is now
  `is_on_floor() OR (short ground feeler ray AND vy < 0.5)`; the feeler was shortened to 0.55 m
  so it misses in flight. The QA assertions were hardened accordingly: airborne must persist
  ≥ 5 consecutive frames AND the jump must gain > 0.5 m of height (both in the isolated rig and
  mid-mission), so a flag-only "jump" can never pass again.
* **Airborne + landing:** gravity 18 m/s²; ground contact re-detected via `is_on_floor()`;
  landings with fall speed > `landing_min` 3 m/s emit `landed(strength)` → camera shake +
  speed ×0.95 + body squash + slip damping — feedback without bounce spam or floor penetration
  (QA S7/S8/S10).
* **Limitation:** the ramp wedge is visual; the launch is the polled trigger volume, not a slope
  collider. This is a deliberate, documented Phase 2 scope decision (real sloped physics would
  require rebuilding district collision — outside "don't rewrite the district builder").
* **Spawn fix (found by render evidence):** the scene spawned the tuk-tuk with yaw 0 despite
  `start.ry = −π/2` in the district data — `_ready` now applies the data-driven start placement
  (position + heading), so the player begins facing east along the south ring as designed.

### 7. Collision feedback & recovery

* **Severity-scaled:** `sev = clamp(planar_speed/vmax, 0.25, 1)`; speed loss = `impact_loss`
  0.35 × sev; lateral slip ×0.4; `impacted(planar_speed)` → camera shake ∝ severity.
* **Cooldown:** `impact_cooldown_s` 0.5 s gates both the penalty and the balance hit
  (`report_collision`) — no per-frame scrape spam (QA S6 rate assertions).
* **Bug found by the QA matrix and fixed:** `get_slide_collision_count()` includes **floor**
  contact — simply driving counted as a collision every cooldown tick, spamming −2.5 E£ balance
  penalties and camera shake. Impact now filters collisions by normal (`normal.y < 0.6` = wall)
  and severity uses planar speed (fall velocity no longer masquerades as a crash). This is
  exactly the kind of defect the contact-frame sampling in S6 exists to catch.
* **Recovery paths:** steering authority is untouched by impacts (S6: yaw responds within 60
  frames of steering away); flip protection (`upright_min_dot` 0.35, `reset_after_s` 1.4 s →
  `request_reset` → district respawns at the `reset` spot) carries over from P1.
* **Fall recovery (found by render evidence):** the ground collider is a finite 460×460 m slab —
  driving off the world edge meant falling forever with no way back. `fall_reset_y` (−5 m, data
  key) now emits `request_reset` and the district respawns the vehicle on the road; asserted in
  QA (S8 tail check) and observed working in the second render run.

### 8. QA matrix & test suite

* Full matrix with every assertion and tolerance: **`docs/VEHICLE_QA_MATRIX.md`** (10 scenarios,
  49 Phase 2 assertions; suite total 100 checks, 0 failed, 7/7 scripts).
* New/rewritten: `tests/test_vehicle.gd` (31 checks, scenarios 1–8 + fall-reset recovery),
  `tests/test_camera.gd` (10 checks, scenario 9), `tests/selfplay.gd` (11 checks, scenario 10 —
  full mission under drift/ramp stress with pay-once verification). Phase 2 QA scenarios
  contribute 52 assertions. `tools/run_suite.sh` gained the camera entry
  and a **zero-check rejection guard**.
* Collision assertions are sampled **at the contact frame** (speed just before vs just after),
  not "somewhere after the fact".

### 9. Render evidence (real renderer, `docs/phase2_shots/`)

Captured with the shared harness (`pixel_pirates/tools/godot_browser/render.mjs`, real Godot web
template in headless Chromium, software WebGL2/SwiftShader, 640×360) via the new scenario
`tools/scenarios/phase2_evidence.mjs`. Placement-only hooks were added to the harness's existing
tuktuk PATCHES entry (documented in render.mjs): **F8** collision course at the parked car,
**F12** ramp approach (west along the south ring at 16 m/s), **F13** diagonal alley — they only
set position/yaw/speed with zeroed slip; every behaviour afterwards (acceleration, drift,
impact, launch, landing, reversing, the full mission flow with offer/accept/board/deliver/result)
is real keys and real game logic. No hook hides a defect: physics, camera and mission code run
untouched. F9 dumps (`TKDBG` in `page.log`) give the ground-truth state per shot.

**Time-dilation statement:** SwiftShader software rendering runs ~4 fps, and the engine clamps
Δ, so game time advances ≈15× slower than real time. Scenario waits are real seconds sized for
that dilation; this affects evidence capture timing only — it is **not** a performance
measurement, and no frame rate in this report may be read as native performance.

Both evidence runs log two benign `WebGL: INVALID_OPERATION` lines (bindBuffer/bufferSubData)
from the SwiftShader driver at the mission-card redraw; they are driver validation warnings, not
Godot errors: no `ERR` (stderr) lines appear in `page.log`, rendering and all later shots are
unaffected. They are reported here rather than filtered.

Evidence index (shot → what it proves → TKDBG anchor in `page.log`): see
`docs/phase2_shots/` table in §10 below.

### 10. Evidence index

| Shot | Content | Verified state |
|------|---------|----------------|
| t00_menu.png | main menu | — |
| t01_start.png | district spawn on the south ring | TKDBG state=0, tuk (0, 0, 60) |
| t02_speed_straight.png | high-speed straight: smoothed follow, FOV widening | TKDBG dump mid-hold |
| t03_drift.png | controlled drift (throttle+steer+handbrake): lateral slip, body roll | TKDBG dump mid-drift |
| t04_drift_exit.png | grip recovery after release | — |
| t05_impact.png | collision with the parked car at ~12 m/s (vehicle stopped at the car, no penetration; penalty applied through the cooldown gate) | TKDBG stopped at car |
| t05b_impact_settled.png | +5 s later: byte-identical frame to t05 — the state is fully settled (the bounded ~4 cm shake is sub-pixel at 640×360 and already decayed at capture; shake is asserted numerically in QA C4/S6, not visually) | TKDBG dump |
| t06_air_1.png | ramp launch captured MID-AIR by an OBSERVATIONAL poller (F9 dumps at ~0.4 s cadence; shoot when a dump reports y > 0.5 — nothing is nudged); tuk-tuk visibly off the deck over the ring road | poll dump tuk=(-39.65, 0.650, 60) |
| t07_landed.png | landing + squash + control retained | TKDBG y back on road |
| t08_alley.png | narrow diagonal alley framing at speed | TKDBG in alley |
| t09_reverse.png | reversing: camera pulled in, stays behind | TKDBG negative speed |
| t10_mission_drift.png | drifting mid-mission (timer running, slip + body attitude) | — |
| t11_drift_bonus_toast.png | mission HUD after the drift window (timer 00:46, destination line + arrow); the toast itself expired before capture in the ~1:1-dilation segment — the drift BONUS is evidenced by the result-card term in t12 and by QA (S5/S10 drift_earned) | TKDBG state=1 |
| t12_result.png | result card with the drift bonus term | TKDBG state=4 |

### 11. Tuning notes (all data, zero code constants)

`data/vehicles/tuktuk_base.json` (Phase 2 keys): `accel_taper` 0.55, `steer_smooth` 10,
`steer_return` 8, `lat_max` 8, `drift_grip_smooth` 6, `drift_min_s` 0.7, `impact_min` 3.0,
`impact_cooldown_s` 0.5, `jump_impulse` 9.0, `jump_speed_min` 8.0, `landing_min` 3.0, `fall_reset_y` −5.0 — next to
the P1 keys (`vmax` 24, `accel` 13, `brake` 24, `steer_rate` 2.5, `grip_lat` 9,
`drift_grip_lat` 2.6, `impact_loss` 0.35, …). `data/missions/reward_tuning.json`:
`drift_bonus_per_s` 1.5, `drift_bonus_cap` 4.0. `data/districts/mit_okba_p1.json`:
`ramps: [{x: −40, z: 60, ry: −π/2}]`. Camera constants (smoothing rates, shake bounds) live in
`chase_cam.gd` as exported/documented feel parameters — they are presentation response curves,
not gameplay numbers; gameplay-facing camera limits asserted by QA C2 come from the exports
(`dist` 5.2, `height` 2.4, `fov` 68–84).

### 12. Compatibility & shared-harness discipline

* `render.mjs` change is additive and confined to the tuktuk entry of the PATCHES map (F8/F12/F13
  + a `_place_tuk` helper appended in-memory to `district.gd`); Pixel Pirates hooks
  (deck/fish/F9/F10/F11) are byte-identical. Pixel Pirates gameplay/assets untouched.
* The patched in-memory `district.gd` was verified with `gdparse` before the render run.
* `gdlint` + `gdparse` clean across all scripts and tests.

### 13. Files changed (Phase 2)

`game/scripts/vehicles/{tuktuk,chase_cam}.gd` (rewritten in place),
`game/scripts/core/mission_mgr.gd` (drift bonus), `game/scripts/world/district.gd` (ramps,
impact→shake), `game/scripts/ui/hud.gd` (drift term in the breakdown line),
`game/data/{vehicles/tuktuk_base,missions/reward_tuning,districts/mit_okba_p1}.json`,
`game/data/meshes/ramp.mesh.json` + `game/assets/models/ramp.{obj,mtl}` (new authored wedge;
all other meshes byte-identical — seeded regeneration), `tools/make_models.py` (+ramp),
`tools/run_suite.sh` (+camera, +zero-check guard), `game/tests/{test_vehicle,test_camera,
selfplay}.gd`, `tools/scenarios/phase2_evidence.mjs`,
`pixel_pirates/tools/godot_browser/render.mjs` (additive hooks),
`docs/{PHASE2_REPORT,VEHICLE_QA_MATRIX}.md`, `docs/phase2_shots/` (new).

### 14. Limitations (honest labels)

* **Windows/Intel HD 3000 performance: unmeasured.** No FPS figure in this project has ever been
  measured on native hardware; the first honest measurement point remains the Phase 10 native
  export.
* Ramp = designated trigger surface + visual wedge (see §6), not a sloped collider.
* Render evidence runs under software GL with ~15× time dilation (§9); it proves behaviour and
  framing, not timing/performance.
* Isolated rigs (scenarios 1–9) intentionally exclude the district; scenario 10 and the render
  evidence cover the integrated path.

### 15. Git

Single descriptive commit on `arena/7464ca7a-videos-motion`, pushed to the same branch only; no
merge to `main`; tag `baseline-pixel-pirates` untouched and re-fetched after the reset.

### 16. Next phase recommendation

Phase 3 (regions A–G per PRODUCTION_PLAN) can build on the now-verified driving feel; the ramp
trigger pattern (`district.ramps` data + polled radius) is reusable for region set-pieces, and
if real sloped physics is ever wanted, it should be a scoped district-collision task of its own.
