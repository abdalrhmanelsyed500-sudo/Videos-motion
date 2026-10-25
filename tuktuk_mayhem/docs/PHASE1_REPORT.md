# PHASE 1 — Playable Core: completion report (2026-10-26)

Branch `arena/7464ca7a-videos-motion` · commit see git log (`FM: tuktuk P1` commit) ·
Drive folder "Egyptian Tuktuk Mayhem" `19W8bqoo5DoPp0JZ23sX4mQtjNKCwSrud` mirrors these docs.

## 1. Godot project found
`pixel_pirates/game` (Godot 4.7.2, Compatibility) — the Fishmonger project, untouched; it also hosts the shared
validation harness (`tools/godot_node`, `tools/godot_browser`). New project: `tuktuk_mayhem/game` (own project.godot).

## 2. Target Godot version
4.7.2 stable (wasm web template 4.7.2-664 for headless validation; desktop export configured for Compatibility).

## 3. Documents created
`docs/GDD.md`, `docs/TDD.md`, `docs/ART_BIBLE.md` (incl. 10-point Crazy Taxi reference analysis, principles only),
`docs/PRODUCTION_PLAN.md`, `docs/ASSET_INVENTORY.md`, this report. Mirrored to Drive.

## 4. Files/scenes created (all new; nothing existing modified except harness PATCHES entry, documented)
- Project: `game/project.godot` (autoloads Reg/Tk/MissionMgr, input map, Compatibility).
- Core: `reg.gd` (JSON registry + validation), `tk.gd` (economy + versioned save), `mission_mgr.gd` (FSM + reward
  maths), `mesh_builder.gd` (runtime ArrayMesh from authored specs), `materials.gd` (runtime PNG materials).
- Gameplay: `vehicles/tuktuk.gd` (arcade CharacterBody3D integrator), `vehicles/chase_cam.gd`,
  `characters/passenger.gd`, `world/district.gd` (data-driven district builder + mission polling + F9 dev probe),
  `ui/hud.gd`, `ui/main_menu.gd`.
- Scenes: `boot/main_menu.tscn`, `world/district_p1.tscn`, `vehicles/tuktuk.tscn`, `characters/passenger.tscn`,
  `ui/hud.tscn`.
- Data: `data/vehicles/tuktuk_base.json`, `data/missions/reward_tuning.json`,
  `data/districts/mit_okba_p1.json`, `data/characters/p1_cast.json`, `data/meshes/*.mesh.json` (13 specs).
- Assets: 13 .obj/.mtl + 12 authored PNG textures (`tools/make_*.py`).
- Tests: `run_one.gd`, `test_reward.gd`, `test_mission.gd`, `test_save.gd`, `test_vehicle.gd`, `test_district.gd`,
  `selfplay.gd`; suite `tools/run_suite.sh`; scenarios `tools/scenarios/{drive_p1,mission_p1}.mjs`.

## 5. Systems that work (wasm-logic + wasm-render verified)
Menu → district load → drive (accel/brake/steer/reverse/drift-grip/impact loss/flip-reset hook) → chase cam with FOV
ramp → pickup ring offer card → accept → passenger boards → timer + destination arrow + HUD needle/distance →
deliver in ring → reward breakdown paid once → result card → next passenger. Versioned save/load. Shortcut flag.
Data-driven: every tuning number lives in JSON.

## 6. Tests performed and results
- Logic suite (real Godot 4.7.2 wasm, headless): **SUITE 6/6 PASS** — test_reward 8, test_mission 14 (pay-once proved),
  test_save 7 (refuses newer version), test_vehicle 10 (accel/brake/steer/reverse/impact/no-penetration/recovery),
  test_district 22 (registry contract, rings on roads, buildings clear of carriageway, hijab-cast rule, live build),
  selfplay 5 (full mission choreography on the real loop).
- Real renderer (Chromium + software WebGL2, Compatibility): mission scenario, **0 console errors**; shots in
  `docs/phase1_shots/` (menu, street view, offer card, driving HUD 00:54 + "To: Felfela Koshary (138 m)",
  DELIVERED card with fare breakdown, next-passenger cycle with balance E£ 78→120).
- Static: gdlint clean, gdparse clean on all scripts.
- NOT verified: desktop editor run, Windows export, user's PC. **HD 3000 UNMEASURED** (software-GL fps means nothing).

## 7. Unresolved problems (honest)
- Chase-cam framing after teleports/scene start is unpolished (one transient black frame right after scene change;
  top-down-ish framing in offer/result shots) — Phase 2 camera pass.
- Software-GL render runs time-dilated (~1/6 game-time); harness placement hooks F10/F11 (render.mjs PATCHES,
  documented, placement-only) used for mission evidence; all transitions real keys/logic.
- Wheel steer/roll visuals, passenger animation, audio, Arabic on-screen text: deferred (plan §Phases).
- District is ONE benchmark block; world expansion gated per plan.

## 8. Drive/GitHub sync
Drive: folder created + this doc set uploaded (report-only mirrors; repo = source of truth; no archive dumps).
GitHub: single focused commit on `arena/7464ca7a-videos-motion`, pushed; no merges to main; baseline tag untouched.

## 9. Exact next task
Phase 2 — Driving quality: chase-carm framing/damping tune (fix transient frame), drift/jump feel, impact feedback
(sparks/skid TEMP FX), speed-line FOV polish, 10-case vehicle matrix extension, then re-run suite + render evidence.

## 10. Verified to run?
Yes within the stated harnesses: wasm-logic 6/6 and wasm-render 0-error mission evidence. Desktop/HD 3000: NOT yet —
the first Windows export (Phase 10) is the earliest honest measurement point on the user's machine.
