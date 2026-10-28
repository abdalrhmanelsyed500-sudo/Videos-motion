# IRON ATLAS: SHATTERED WORLD — Stage 0 Audit

Date: 2026-10-28 · Branch: `arena/7464ca7a-videos-motion` · Repo head at audit: `531a7ff`

## Repository state (inspected, not assumed)
- The sandbox had rolled the local branch back to base `e376391`; the pushed branch head
  `531a7ff` (EGYPTIAN TUKTUK MAYHEM Phase 0-2) was recovered with
  `git fetch origin arena/7464ca7a-videos-motion && git reset --hard origin/...`.
  No work was lost; nothing was deleted or renamed.
- Existing top-level projects (all preserved untouched): `pixel_pirates/` (Godot project +
  the shared headless test harness), `tuktuk_mayhem/` (Godot 4.7.2 project, Phase 2 suite
  7/7, 103 checks), plus art/doc folders from earlier tasks (`pixelart*`, `cartoon`,
  `chile33`, `docs`, `renders`, `assets`).
- IRON ATLAS is added as a NEW sibling project `iron_atlas/` with its own Godot project in
  `iron_atlas/game/`. It does not modify or depend on the other projects except for
  re-using the proven headless test harness
  `pixel_pirates/tools/godot_node/run.mjs` (read-only usage).

## Engine / tooling available in this environment (measured)
- No native Godot binary on PATH (`godot: command not found`).
- Working engine: **Godot 4.7.2 template_release wasm32**, headless under Node v22 via the
  npm package `@ringozz/godot-web-wasm32` (restored with `npm ci` in
  `pixel_pirates/tools/godot_node/`, registry.npmjs.org reachable).
  Harness characteristics (known, documented by the harness): no rendering (dummy
  renderer), no audio, no RegEx module (projects must avoid `RegEx` or use the shim),
  imported textures (`.ctex`) unavailable — raw PNG loads fail headless, so logic tests
  must not depend on texture resources.
- Python 3.11 + venv with Pillow 13 / numpy 2.4 for deterministic sprite generation.
- GitHub/PyPI/npm reachable; Godot release binaries (native) NOT downloadable here, so
  **visual verification in-editor must happen on the user's machine**; headless logic and
  scene-flow tests run here. This limitation is stated explicitly per the brief.

## Art reference (inspected)
- `my-pixel-tank-collection-v0-*.jpg` / `images.jpeg`: CHAR D1 / CHAR R35 isometric tank
  sprites — compact palettes, 2-3 tone camo blocks, 1px dark rim (not thick black
  outlines), deliberate top-left light, clean readable texture. Canonical benchmark for
  military sprite shading language.
- `Rogue North on Steam.jpeg`: top-down tactical pixel art — snow/rock/forest terrain with
  soft palette, small vehicles with subtle rims, no outlines on terrain, sparse decoration,
  high readability at 1x. Canonical benchmark for tactical map + terrain tiles.
- Translation into our library: 32px terrain tiles with 4-6 colour palettes and no outline;
  24px top-down unit sprites with 1px darker rim, 3-tone body shading, light from top-left;
  strategic map uses flat owner-colour fills + thin borders (readability first).

## Risks / current errors
- Headless wasm cannot show pixels: UI/scene tests assert state transitions, not visuals.
- wasm FS is in-memory: `user://` saves persist only within one process run (tests save
  then load in the same run; on desktop saves persist normally).
- Large ambition vs one slice: everything beyond Stage 1 is marked PLANNED in STATUS.md.
