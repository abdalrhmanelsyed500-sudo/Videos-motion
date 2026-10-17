# MODULE A1 (revision R1): Tech Stack Decision - hardware-aware

Revision reason: the developer PC is an Intel Core i5-2410M, 3 GB RAM, Intel HD Graphics 3000, 1366x876, Windows 64-bit. The first A1 (Forward+ renderer) could not run there. This revision keeps the intended look and changes HOW it is produced. Steam is NOT a commitment.

## 1. Facts (verified 2026-10-17 from godotengine/godot and godot-docs on GitHub)
- Godot latest stable 4.7.2 (2026-08-18), MIT licence. Godot 3.6.3 also exists (2026-08-22).
- Godot docs, system requirements: Forward+ and Mobile renderers need Vulkan 1.0 (example given: Intel HD 510, Skylake). Compatibility renderer needs full OpenGL 3.3 (example: Intel HD 2500, Ivy Bridge). Native editor minimum RAM 4 GB, recommended 8 GB.
- Godot can fall back to OpenGL ES 3.0 through ANGLE over Direct3D 11 on Windows when OpenGL 3.3 is not available (project settings `rendering/gl_compatibility/fallback_to_angle`, default true; command line `--rendering-driver opengl3_angle`). Whether this works on HD Graphics 3000 is NOT verified: the probe will tell.
- Compatibility renderer feature table (docs): SUPPORTED glow, depth/height fog, tonemapping, colour adjustments, SSAO, shadows (directional/omni/spot), MSAA 3D, decals, baked lightmap rendering, screen-texture and depth-texture shaders, custom full-screen post-processing. NOT supported: depth-of-field blur, volumetric fog, SSR, SDFGI, VoxelGI, CompositorEffects, FXAA/TAA, HDR colour (it is RGBA8). 8 lights per mesh by default.
- What I could not do: run Godot (download blocked). I can only syntax-check GDScript with the gdtoolkit parser (done, all scripts parse).

## 2. What this means for your PC (honest)
- HD Graphics 3000 is below Godot's documented OpenGL 3.3 requirement and has no Vulkan. The game may only run through the ANGLE fallback, or not at all. 3 GB RAM is below the editor's 4 GB minimum.
- No setting I choose can make this PC render the final look in real time. The final look is decided by the player's hardware, not yours. What I can do: (a) keep the final look independent of expensive engine features, (b) give your PC a "Dev-Lite" mode, (c) keep game logic testable with no GPU, (d) verify the real look through other channels (section 5).

## 3. Decision: "Authored HD-2D", Compatibility-first
The look is built from cheap, authored techniques that exist in the Compatibility renderer, so one project runs from old hardware up to modern GPUs:
| Reference feature | Expensive way (not used as base) | Our method (works in Compatibility) |
|---|---|---|
| Tilt-shift blur | built-in DOF (Forward+/Mobile only) | own full-screen shader (ColorRect reading the screen texture), band-shaped blur + vignette |
| Bloom | HDR glow | Environment glow in LDR with lowered threshold, plus emissive pixel sprites |
| Light shafts / haze | volumetric fog | authored additive gradient quads + depth/height fog + dust particles |
| Soft global light | VoxelGI / SDFGI | hand-placed light pools (decals / omni lights), baked LightmapGI per island (baking needs a RenderingDevice PC, done once, see 5) |
| Cast shadows | n/a | directional light shadows on, blob shadows for far crowds |
| Colour grade | n/a | Environment adjustments / LUT per region |
Optional later ("Ultra" tier, Forward+): real DOF, HDR bloom, volumetric fog. Decision gate: only after the vertical slice, never required.

## 4. Quality ladder (same content, different cost)
- **Dev-Lite (your PC):** internal render size 683x438 (exactly half of 1366x876: 1 art pixel = 2 screen pixels, nearest upscale, 4x less GPU work), shadows off, bloom off, cheaper blur (2 px), small island streaming radius, texture budget under 256 MB, game process under about 1.2 GB RAM.
- **Standard:** full resolution, shadows, bloom, fog, shafts, tilt-shift (5 px). Target GPU class: GTX 650 / Radeon HD 7750 and up (those are the docs' Compatibility "recommended" examples) - to be measured in M3.
- **Ultra (optional):** Forward+ extras.
Quality is a data profile (`quality_profiles.json`, A5), not code branches.

## 5. Development and testing plan for a weak PC
1. **Everything is text.** I write scenes/data/code/assets; you do not need the editor for most work.
2. **Headless logic tests.** `--headless` needs no GPU. Survival simulation (Part N), economy, data validation and island generation are written as scripts with self-tests you can run on your PC (`selftest.gd` proves headless works).
3. **Syntax check on my side.** I run gdtoolkit on every GDScript before delivering. That finds syntax errors, not runtime errors.
4. **Look Lab (proposal for A3/A4):** a Python tool in my sandbox that renders still images of the HD-2D look (pixel scene + same tilt-shift, bloom, grade, vignette parameters as the Godot shader). You approve the look from PNGs without any GPU; the Godot shader then copies those numbers.
5. **Visual verification needs one capable machine at some point.** Options (your choice, some cost money): borrow a friend's PC for test sessions; a cheap used PC with a GTX 650-class or newer GPU; a rented cloud Windows GPU desktop (paid, I will not choose one for you); or upgrade this laptop's RAM to 8 GB if the model allows (check its maximum). Run the probe first; the numbers decide.
6. **Probe first.** Run `tools/probes/gpu_probe_v2` (README.txt inside): step 1 headless self-test, step 2 visual probe. Send me `probe_result.txt` or the error text.

## 6. Other decisions
- **Engine:** Godot 4.7.2 standard, locked. Godot 3.6.3 (OpenGL ES 2/3, runs on very old GPUs) is rejected as the base: end-of-line architecture and a lower ceiling; kept only as a documented emergency fallback if the probe proves 4.7.2 cannot start at all and no other machine is available.
- **Language:** typed GDScript. **Look:** pixel textures, nearest filter, integer texel density, FOV about 22 degrees, camera pitch about 39 degrees.
- **World:** ship-fixed origin with 64-bit world data (unchanged; reason: 32-bit vectors have about 8 mm spacing at 100 km from origin).
- **Distribution:** undecided. No Steam SDK, no GodotSteam, no steam_appid. Export is a plain Windows x86_64 .exe + .pck (itch.io, direct download or any store). Achievements are internal events on our own event bus; a store adapter can listen later. A thin `Platform` seam (no third-party code) is created only when needed (A2/J4).

## 7. Hardware targets (design targets, not measured)
- **Minimum (shipping):** Windows 10 64-bit, 4 GB RAM, GPU with OpenGL 3.3, 2-core CPU, Standard at 720p-1080p; Dev-Lite as the in-game "Low".
- **Recommended:** 8 GB RAM, GTX 650 / HD 7750 class or better, quad-core, 1080p Standard at 60 fps.
- **Dev PC (yours):** Dev-Lite at 683x438 internal, goal 30 fps if the probe runs at all.
- Budgets: 16.6 ms frame (Standard), under 1000 draw calls at sea, textures under 1 GB (Standard) / 256 MB (Dev-Lite), RAM peak under 3 GB (Standard) / 1.2 GB (Dev-Lite).

## 8. Risks
| Risk | Mitigation |
|---|---|
| Godot does not start on HD 3000 | Probe; borrowed/cheap/cloud GPU machine; emergency fallback in section 6 |
| Visual sign-off impossible on dev PC | Look Lab stills, then periodic sessions on a capable machine |
| LDR (RGBA8) bloom looks weaker than HDR | emissive sprites, tuned threshold, authored glow halos; Ultra tier optional |
| LightmapGI baking needs RenderingDevice hardware | bake on a capable machine once per island, commit the result; or hand-placed light pools |
| I cannot run Godot | gdtoolkit syntax check + self-tests + you report errors |

## 9. Decision log (supersedes the first A1 where noted)
A1-1 Godot 4.7.2 standard (kept) | A1-2 **Compatibility renderer first, Forward+ optional "Ultra" later (changed)** | A1-3 typed GDScript (kept) | A1-4 pixel textures, nearest, integer density (kept; internal render size is a quality-ladder setting) | A1-5 **tilt-shift = own screen shader, not built-in DOF (changed)** | A1-6 ship-fixed origin (kept) | A1-7 **distribution undecided, no Steam dependency (changed)** | A1-8 **targets above (changed)** | A1-9 engine locked (kept) | A1-10 quality ladder Dev-Lite / Standard / (Ultra) | A1-11 headless-testable logic | A1-12 Look Lab proposal.

---
## Revision note R2 (with A2-A4)
* The user chose to skip the GPU probe for now ("Godot is already running on my PC"); the probe stays available in `tools/probes/gpu_probe_v2/`. Visual/performance testing is postponed; headless tests come first.
* **Dev-Lite internal resolution changed from 683x438 to 640x360** (= the art grid of A3; shown at x2 = 1280x720 on the 1366x876 screen, integer scale, ~22% fewer pixels). Supersedes A1-10 numbers only; the ladder idea is unchanged.
* The quality profiles are now real data: `game/data/look/look_profiles.json`, read by `core/quality.gd` and by the Look Lab.
