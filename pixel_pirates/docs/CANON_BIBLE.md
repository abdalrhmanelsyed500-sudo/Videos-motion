# CANON BIBLE - Crown of the Seas (working title) - v0.1 (after A1)
Drive folder: "Pixel Pirates". Repo path: pixel_pirates/.

## Hard content rules
No female characters in the crew. No sexual content. No gods/religion/atheism promotion/insults to religion; mysticism stays neutral (legends, curses, ancient beasts, pirate lore).

## World scale rules (non-negotiable)
Enormous ocean; crossing it is the core experience. 50+ islands (normal-sized, quick to explore). Only a minority in clusters of 2-4; most isolated; some extreme dead-ocean gaps. No island visible from another unless a deliberate landmark. Open sea never empty. Exact sailing times go in the Canon (E2/N13). Three island tiers: Tier 1 about 12-15, Tier 2 about 20-25, Tier 3 about 15-25.

## Core pillar
Realistic pirate-life simulation (food, fishing/hunting, cooking, water, health/disease, ship wear, crew labor, morale/pay, ammo, cargo, weather). Fair tension; difficulty modes Story / Normal / Hardcore Realism. Every island offers at least one survival-relevant thing.

## Decisions
A1-1 Godot 4.7.2-stable standard (non-.NET). A1-2 Forward+. A1-3 typed GDScript; GDExtension only if profiling demands (gates at J7, J22). A1-4 high-res 3D diorama with nearest-filtered pixel textures, integer texel density, FOV about 22 deg. A1-5 pitched camera (about 39 deg) + distance DOF gives tilt-shift. A1-6 ship-fixed origin, world in 64-bit data. A1-7 Windows x86_64 primary; Steam via GodotSteam behind PlatformService; runs without Steam. A1-8 targets: min 30 fps 1080p Low / rec 60 fps 1080p High; RAM peak < 6 GB; texture < 2 GB; < 1500 draw calls at sea. A1-9 engine version locked.

## Verified external facts (2026-10-17)
Godot 4.7.2-stable (2026-08-18), MIT. GodotSteam v4.23 (2026-10-05), Steamworks SDK 1.65.

## File structure
Provisional: pixel_pirates/docs/, pixel_pirates/a1_smoke_test/. Final structure decided in A2.

## Island registry (50+ planned)
Empty. Format: ID | name | tier | biome | position | distances to neighbours | status (planned/designed/built/tested). Filled from E3.

## Open questions
Q1 engine confirmation. Q2 developer PC specs for testing. Q3 Steam: yes/no/later.
