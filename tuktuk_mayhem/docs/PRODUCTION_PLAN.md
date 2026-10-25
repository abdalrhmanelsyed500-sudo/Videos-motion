# EGYPTIAN TUKTUK MAYHEM — Production Plan & Phase Status

Branch `arena/7464ca7a-videos-motion` · repo dir `tuktuk_mayhem/` · Drive folder "Egyptian Tuktuk Mayhem"
(`19W8bqoo5DoPp0JZ23sX4mQtjNKCwSrud`) holds mirrors of these docs; **repo is source of truth**.

Status labels: Planned / In Progress / Implemented / Tested / Verified (Verified = ran in wasm logic AND wasm render
with 0 console errors, or on user's PC when they run it).

| Phase | Scope | Status |
|---|---|---|
| 0 Discovery & planning | env inspection, GDD/TDD/ArtBible/plan, Drive folder, risk list | **Verified** |
| 1 Playable core | menu, district block, tuktuk+camera, 1 passenger, 1 mission, timer, arrow, reward, result, replay; logic tests + render shots | **Verified** (suite 6/6 wasm-logic; 0-error wasm-render mission evidence; desktop/HD3000 UNMEASURED) |
| 2 Driving quality | drift/jumps polish, impact feel, speed FX, camera tuning, 10-case vehicle test matrix | Planned |
| 3 Core assets | production tuktuk, building families, character set w/ real animations, props, UI skin | Planned |
| 4 First full district | Mit Okba complete: traffic-free crowds, passengers, shortcuts, missions, audio bed, benchmark | Planned |
| 5 World systems | region manager, streaming, traffic AI, pedestrians, economy/save/unlocks | Planned |
| 6 World expansion | Cairo districts → Alexandria → tourist coast → countryside → industrial → intercity (gate per region) | Planned |
| 7 Content expansion | mission types, vehicles, upgrades, challenges | Planned |
| 8 Audio & polish | full SFX/original music, AR localization RTL, material/lighting pass | Planned |
| 9 QA & optimization | profiles, perf reports per runner, save/region-transition tests | Planned |
| 10 Release candidate | Windows export config, launch docs, completed/unfinished list | Planned |

## Phase 1 task list (dependency order)

1. Project skeleton + autoloads + data registry. 2. Texture/model generators → assets. 3. District scene (roads,
sidewalks, 6 buildings, props, rings). 4. Tuktuk controller + camera. 5. Passenger + mission FSM + reward. 6. HUD +
result card + menu. 7. Tests (mission, reward-once, vehicle controls, ring detection). 8. Suite run + render scenario
shots. 9. Docs update + commit + push + Drive mirror.

## Known limitations carried openly

- wasm harness ≠ desktop: no audio, software GL, slow; HD 3000 UNMEASURED until user runs a build.
- Phase-1 characters use scripted pose tweens (TEMP) — AnimationPlayer clips in Phase 3.
- No traffic/pedestrian simulation in Phase 1 (parked props + static pedestrians only), by design gate.
- Arabic strings structurally ready (string table) but EN-only on screen until Phase 8.
