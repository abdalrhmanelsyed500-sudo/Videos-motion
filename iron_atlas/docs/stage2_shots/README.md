# Stage 2 visual evidence

Captured 2026-10-28 at 1280×720 using the repository's unchanged
`pixel_pirates/tools/godot_browser/render.mjs`: Godot 4.7.2 web template,
Chromium WebGL 2 / SwiftShader software rendering. `world_render.log` and
`tactical_render.log` contain the capture output; neither run emitted a script,
engine, or page error. Software rendering here is **not a performance test**.

- `01_main_menu.png`, `02_setup.png`: actual menu and campaign setup.
- `03_world.png`: the generated 200-district world, seed 123.
- `04_forces.png`, `05_market.png`, `06_politics.png`: actual UI tabs selected
  using mouse input, including a real formation and catalogue selection.
- `05b_quote.png` and `05c_order.png`: a real mouse-confirmed procurement;
  the balance changes from 12,000 to 11,747 and the order enters transit.
- `07_tactical_fixture.png`: the real tactical scene, but the test fixture
  `game/tests/render_tactical_fixture.gd` moves an existing enemy formation
  into contact before rendering. It is **not** evidence of a played battle or
  combat outcome; automated tactical tests cover the outcome separately.

The generated 24px unit/32px terrain art and nearest-neighbor rendering are
consistent, but remain noticeably simpler than the supplied professional
reference art. Further hand-authored art and visual polish remain open work.
