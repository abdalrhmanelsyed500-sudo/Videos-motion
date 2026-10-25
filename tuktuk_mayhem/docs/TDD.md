# EGYPTIAN TUKTUK MAYHEM — Technical Design Document (Phase 0)

## 1. Environment actually inspected (2026-10-25)

- Repo `abdalrhmanelsyed500-sudo/Videos-motion`, branch `arena/7464ca7a-videos-motion` (session-pinned), HEAD `0030cff`.
- Existing Godot project: `pixel_pirates/game` (Godot 4.7.2, Compatibility) — untouched by this project; it also hosts
  the shared validation harness (see §6). New project lives in `tuktuk_mayhem/game` (its own `project.godot`).
- Engine available in this sandbox: Godot **4.7.2 web template (wasm32, nothreads)** via npm
  `@ringozz/godot-web-wasm32@4.7.2-664`, run headless under Node (logic) or in headless Chromium with software WebGL2
  (real rendering + screenshots). No desktop Godot binary here; the user's PC (i5-2410M / HD 3000 / 3 GB) remains
  **UNMEASURED** — every perf statement must say which runner produced it.
- Python 3 venv + Pillow/numpy for texture/model generators; gdtoolkit for lint/parse.

## 2. Architecture

```
tuktuk_mayhem/game/
  project.godot            autoloads: Tk (game state/economy), MissionMgr, Reg (data registry)
  scenes/ boot/ world/ vehicles/ characters/ ui/
  scripts/ core/ vehicles/ missions/ characters/ ui/ world/
  data/ vehicles/ missions/ districts/ characters/
  assets/ models/*.obj materials/ textures/*.png audio/(later) fonts/(later)
  tests/ test_*.gd + run_one.gd (same protocol as pixel_pirates harness)
```
- **Data-driven**: vehicles, reward tuning, district graphs, character tables = JSON loaded by `Reg`; scripts never
  hard-code tuning numbers (code-quality rule 6 of the master brief).
- **Vehicle**: `CharacterBody3D` + custom arcade integrator (ground ray for slope, slip vector for drift).
  Rationale vs VehicleBody3D: deterministic, stable on wasm headless, tunable feel, no wheel-ray tuning pain;
  documented trade-off (no suspension travel sim — arcade brief accepts).
- **Missions**: finite state machine in `MissionMgr` (IDLE→OFFER→BOARDING→DRIVING→RESULT), signals to HUD;
  reward granted through a single `pay_out()` guarded by a paid flag (double-pay unit test).
- **World**: district scene owns road graph (JSON spline list), spawn points, rings; later regions = same contract.
- **UI**: CanvasLayer HUD reading signals only; no gameplay logic in UI scripts.
- **Saves**: `user://save.json`, `{version, balance, rep, unlocks, stats}`; loader runs upgraders list; Phase 1 writes
  balance/stats only but the versioned path exists from day one.

## 3. Godot 4.7 API discipline

Only APIs verified in 4.7 docs/source: CharacterBody3D.move_and_slide, RayCast3D, Area3D monitors, AnimationPlayer,
NavigationRegion3D deferred to Phase 5 (traffic), Web export caveats (no RegEx in wasm template → harness injects
regex_shim like pixel_pirates; our scripts avoid RegEx entirely). GDScript static typing on all new scripts; gdlint
clean; `gdparse` in CI-like check script.

## 4. Performance budget (design targets, not measurements)

Desktop low-end profile (HD 3000 class): 1366×768 window, Compatibility renderer, no GI, baked lightmaps OFF (vertex
light + directional sun + minimal shadows on profile "low_end"), draw calls < 250 in district view via merged static
meshes per block + texture atlases; traffic pool ≤ 24 active; pedestrians ≤ 60 near-tier. Profiles: ultra / standard /
low_end / dev_lite exactly like pixel_pirates (shared concept, separate code).

## 5. Asset pipeline

Geometry: authored `.obj` from `tools/make_models.py` (deterministic, seeded) — real geometry, sane origins (y=0
ground), +Y up, metres. Textures: authored PNG from `tools/make_textures.py` (PIL, seeded) — asphalt with lane marks,
sidewalk tiles, 3 facade families (sandstone apartment w/ balconies+AC units, shopfront row, rural brick), tuktuk
paint+trim, character palettes. Materials: StandardMaterial3D, albedo+roughness only (Compatibility-friendly),
nearest-off linear filtering, no normal maps on low_end. Every generated asset logged in
`docs/ASSET_INVENTORY.md` with status FINAL-P1 / TEMP.

## 6. Validation harness (shared, honest)

- Logic: `node pixel_pirates/tools/godot_node/run.mjs tuktuk_mayhem/game --script res://tests/run_one.gd -- <name>`
  per test (wasm engine: real GDScript, scenes, input events; NO rendering/audio).
- Render: `node pixel_pirates/tools/godot_browser/render.mjs tuktuk_mayhem/game <scenario.mjs>` → real Compatibility
  draw in Chromium + screenshots + page-console error capture (0 errors required).
- Suite wrapper: `tuktuk_mayhem/tools/run_suite.sh` (mirrors pixel_pirates runner protocol, prints SUITE: n/m).
- Claims language: "wasm-logic verified", "wasm-render verified", "desktop UNVERIFIED", "HD 3000 UNMEASURED".

## 7. Risks & mitigations

- wasm template lacks RegEx/editor import → raw-texture fallback already proven in pixel_pirates; keep textures PNG,
  no .import reliance.
- Software WebGL2 is slow → screenshots at 640×360..1280×720, short scenarios, ≤2 parallel renders.
- Scope creep → phase gates: no region N+1 before region N passes its checklist.
- Sandbox resets (happened twice) → push every commit + tag to origin immediately; /tmp toolchain rebuilt by
  /tmp/setup2.sh recipe kept in `tuktuk_mayhem/tools/bootstrap_sandbox.sh`.
