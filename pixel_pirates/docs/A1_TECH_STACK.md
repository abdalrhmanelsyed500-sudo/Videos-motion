# MODULE A1: Tech Stack Decision (PC / Steam)

**Goal:** choose the engine, renderer, language, platform and Steam path for a premium Windows 2.5D pixel-art game ("HD-2D" look from the two reference images) with a huge ocean and 50+ islands.
**Delivers:** reference-driven requirements, 3 options with scoring, one recommendation, risks, hardware targets, Steam plan, decision log, smoke-test project.

## 1. What the references demand
Both references are pixel art standing inside a real 3D diorama, not a flat 2D scene.
Image 1 (town square) and image 2 (forest clearing) show:
1. Pixel sprites for characters/props/tiles with crisp, un-smoothed edges (characters roughly 25-35 px tall at native density; exact numbers come in A3).
2. A perspective camera pitched steeply down (about 35-45 degrees), narrow field of view.
3. Tilt-shift: the middle band is sharp, the top and bottom are heavily blurred.
4. Bloom on bright areas, warm key light, dark vignette, teal-shadow / orange-light colour grade.
5. Real cast shadows on the ground (dappled under trees), light shafts / haze (image 2), floating dust particles.
6. Water with reflection and soft depth colour.
Game needs on top: Windows 64-bit native, Steam, an ocean of many kilometres, 50+ islands loaded from data, deep simulation (survival), controller support.

## 2. Options (rule 9)
| | A. Godot 4.7 (recommended) | B. Unity 6 (URP) | C. Unreal Engine 5 |
|---|---|---|---|
| HD-2D look (sprites in 3D, DOF, bloom, shadows, fog) | 4/5 built in (Forward+) | 4/5 (URP + post volumes) | 5/5 (Octopath-style HD-2D was originally made in UE4) |
| Content as plain text (scenes, data, code) so I can write and you can diff it | 5/5 (.tscn .tres .gd .json) | 3/5 (YAML scenes, .meta GUIDs) | 1/5 (binary .uasset) |
| Small-team iteration speed | 5/5 | 4/5 | 2/5 (long compiles, heavy editor) |
| Huge-world control | 4/5 (no built-in streaming; we build it, J7) | 4/5 | 5/5 (World Partition, but heavy) |
| Cost / licence | 5/5 MIT, no royalties | 3/5 (licence terms change; verify) | 3/5 (royalty terms; verify) |
| Steam | 4/5 (GodotSteam) | 5/5 | 5/5 |
| Risk for a 2D-pixel-art-in-3D project | low-medium | medium | medium-high (overkill) |
Scores are my judgement. I did not verify Unity/Unreal current versions or licence terms: check them yourself if you want B or C.
**Recommendation: A. Godot 4.7.2 (standard, non-.NET), Forward+ renderer.** The deciding reason is text-native authoring: everything I produce (scenes, resources, data, code) is plain text you can open, diff and fix, which fits this one-module-at-a-time process.

## 3. Verified facts (checked against the GitHub API on 2026-10-17)
- Latest stable Godot: 4.7.2-stable, released 2026-08-18 (4.7 on 2026-06-18). MIT licence.
- GodotSteam latest: v4.23, released 2026-10-05, built on Steamworks SDK 1.65 and labelled "Godot 4.x". Whether it supports 4.7.x must be confirmed on its release page at install time (not verified).
- Windows 64-bit export of Godot is native (.exe + .pck). The official export-templates package is about 1.3 GB (one-time download).
- NOT verified: I could not run Godot in my sandbox (release downloads are blocked), so no code I give is executed by me. See HOW TO TEST.

## 4. Technical decisions
1. **Look = high-resolution 3D diorama with pixel textures** (not a low-res image upscaled). Sprites are `Sprite3D` billboards with nearest-filtering, no mipmaps, integer texel density; ground/props are pixel textures; effects (DOF, bloom, fog) run at full screen resolution. Narrow FOV (~22 degrees) keeps texel size almost constant.
2. **Free tilt-shift (original idea #1):** because the camera is pitched, distance grows from the bottom of the screen to the top, so ordinary distance-based depth of field (near + far) produces a horizontal sharp band, exactly like the references, with no custom shader. The smoke test proves this on your PC.
3. **Ship-fixed origin (original idea #2):** the world is stored in 64-bit data (GDScript `float` is 64-bit) and the ship always stays near render origin; the ocean and islands slide past. Reason: single-precision vectors (Godot default) have about 8 mm spacing at 100 km from origin, which makes sprites and wave shaders jitter on long voyages. Bonus: the "dead ocean" can be an endless shader plane and speed is felt as the world sliding. Detailed in J7.
4. **Language:** typed GDScript for everything. C# rejected (extra .NET dependency, larger exports, weaker GodotSteam path). Heavy loops (ocean sim, ecosystems, streaming) start as data-oriented GDScript (PackedArrays); a GDExtension (C++/Rust) is a decision gate at J7 and J22 only if profiling proves it.
5. **Renderer:** Forward+ only. Compatibility/Mobile renderers cannot give the volumetric fog / DOF quality of the references, so they are out.
6. **Engine lock:** 4.7.2-stable for the entire production. No engine upgrade without your approval.
7. **Platform:** Windows 10/11 x86_64 primary. Steam Deck is a stretch target through Proton (not verified).
8. **Steam:** GodotSteam behind a `PlatformService` interface, so the game also runs without Steam (dev builds, DRM-free). Features: achievements, cloud saves (saves live in `user://`), Steam Input/controller, rich presence. Details J28/M6. Steam needs a Steamworks partner account and a per-game fee (I believe $100; verify). For testing without an app id use the public Spacewar id 480 in `steam_appid.txt`.

## 5. Risks and mitigations
| Risk | Mitigation |
|---|---|
| HD-2D polish needs tuning (DOF, bloom, grading) | I21/J10 prototype early; vertical slice before mass content |
| Thousands of sprites (foliage, crowds, fish) | MultiMeshInstance3D with a sprite shader; per-scene counts in budgets |
| Float precision on long voyages | Ship-fixed origin + 64-bit data (decision 3) |
| Sprite shimmer when scaled by perspective | Narrow FOV, integer texel density rules in A3/J1 |
| GodotSteam vs Godot 4.7.x compatibility | Check at install; fall back to prior GodotSteam or a pinned build |
| I cannot execute Godot in my sandbox | Every code module ships with a self-test and expected output; you run it and paste errors back |

## 6. Hardware targets (design targets, to be measured in M3, not measured yet)
- **Minimum:** Windows 10 64-bit, quad-core CPU (Intel i5-6600 / Ryzen 3 1200 class), 8 GB RAM, Vulkan-capable GPU with 2-4 GB VRAM (GTX 960 / RX 470 class), 12 GB disk. Target 30 fps at 1080p, Low effects.
- **Recommended:** Windows 10/11, 6-core CPU (i5-10400 / Ryzen 5 3600 class), 16 GB RAM, GTX 1660 / RTX 2060 / RX 5600 XT class, SSD, 20 GB disk. Target 60 fps at 1080p, High effects.
- **Budgets:** frame 16.6 ms; below 1500 draw calls at sea; texture memory below 2 GB; peak RAM below 6 GB; island load without a visible stall (below 100 ms per frame, loaded in background threads).
- **Resolutions:** 16:9 base, 1280x720 to 4K, ultrawide supported, UI scales.
The exact GPU driver floor for Forward+ will be confirmed on real machines in M3.

## 7. Decision log
A1-1 Godot 4.7.2 standard | A1-2 Forward+ | A1-3 typed GDScript, GDExtension only by profiling | A1-4 high-res 3D diorama, nearest-filter integer texel density | A1-5 pitched camera + distance DOF = tilt-shift | A1-6 ship-fixed origin with 64-bit world data | A1-7 Windows x86_64 primary, Steam via GodotSteam behind PlatformService | A1-8 hardware targets above | A1-9 engine locked for the project.

## 8. Smoke test
Folder `a1_smoke_test/` (Godot project). Open it in Godot 4.7.2, press F5. Expected: a diorama of 9 pixel pirates receding in depth, sharp in the middle band and blurred toward top and bottom, warm shadows, bloom, fog; HUD shows engine, GPU, API, renderer. Keys D/G/F/S toggle depth of field/glow/fog/shadows. Console prints a system report. In a single-precision build `Vector3.x for 100000.001` prints `100000`.
