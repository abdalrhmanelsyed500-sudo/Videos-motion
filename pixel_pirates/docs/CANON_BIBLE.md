# CANON BIBLE - Crown of the Seas (working title) - v0.2 (after A1 revision R1)
Drive folder: "Pixel Pirates". Repo path: pixel_pirates/.

## Hard content rules
No female characters in the crew. No sexual content. No gods/religion/atheism promotion/insults to religion; mysticism stays neutral (legends, curses, ancient beasts, pirate lore).

## World scale rules (non-negotiable)
Enormous ocean; crossing it is the core experience. 50+ islands (normal-sized, quick to explore). Only a minority in clusters of 2-4; most isolated; some extreme dead-ocean gaps. No island visible from another unless a deliberate landmark. Open sea never empty. Exact sailing times go in the Canon (E2/N13). Island tiers: Tier 1 about 12-15, Tier 2 about 20-25, Tier 3 about 15-25.

## Core pillar
Realistic pirate-life simulation (food, fishing/hunting, cooking, water, health/disease, ship wear, crew labor, morale/pay, ammo, cargo, weather). Fair tension; difficulty modes Story / Normal / Hardcore Realism. Every island offers at least one survival-relevant thing.

## Developer hardware (fixed fact)
Intel Core i5-2410M 2.3 GHz (2 cores/4 threads), 3 GB DDR3-1333, Intel HD Graphics 3000, 1366x876, Windows 64-bit.

## Decisions
A1-1 Godot 4.7.2-stable standard (non-.NET), locked.
A1-2 Compatibility renderer first; Forward+ "Ultra" optional later (decision gate after vertical slice).
A1-3 typed GDScript; GDExtension only if profiling demands (gates J7, J22).
A1-4 pixel textures, nearest filter, integer texel density, FOV ~22 deg, camera pitch ~39 deg; internal render size is a quality setting.
A1-5 tilt-shift via own full-screen shader (ColorRect + screen texture), not built-in DOF.
A1-6 ship-fixed origin, world in 64-bit data.
A1-7 distribution undecided; no Steam SDK/GodotSteam/steam_appid; plain Windows exe+pck; achievements are internal events; Platform seam only when needed.
A1-8 targets: shipping min = Win10 64-bit, 4 GB RAM, OpenGL 3.3 GPU; recommended = 8 GB, GTX 650/HD 7750 class+; Dev-Lite for dev PC (683x438 internal, shadows/bloom off, 2 px blur, tex < 256 MB, process < 1.2 GB).
A1-9 engine version locked.
A1-10 quality ladder: Dev-Lite / Standard / (Ultra). Quality = data profile.
A1-11 game logic must be headless-testable (no GPU).
A1-12 Look Lab (Python still renders of the look) proposed for A3/A4.

## Verified external facts (2026-10-17)
Godot 4.7.2-stable (2026-08-18), MIT. Compatibility renderer needs OpenGL 3.3; Forward+/Mobile need Vulkan 1.0+. ANGLE (OpenGL ES 3.0 over Direct3D 11) fallback exists on Windows. Compatibility lacks DOF blur, volumetric fog, SSR, SDFGI, VoxelGI, CompositorEffects, HDR; it has glow, fog, SSAO, shadows, decals, screen-texture shaders, full-screen post.

## Not verified
Whether Godot 4.7.2 runs on HD Graphics 3000 (probe pending). Unity/Unreal facts. Hardware targets are design targets.

## File structure
Provisional: pixel_pirates/docs/, pixel_pirates/a1_smoke_test/. Final structure in A2.

## Island registry (50+ planned)
Empty. Format: ID | name | tier | biome | position | distances to neighbours | status (planned/designed/built/tested). Filled from E3.

## Open questions
Probe results (selftest + visual probe). Access to a capable test machine (borrow / used PC / cloud / RAM upgrade).
