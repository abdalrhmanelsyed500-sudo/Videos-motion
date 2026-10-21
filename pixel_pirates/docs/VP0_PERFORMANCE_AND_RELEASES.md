# VP-0 Performance Strategy, Techniques and Release Sequence
Target: i5-2410M (2c/4t), Intel HD 3000, 3 GB RAM, ~1366×876, Windows 10 64-bit, Compatibility renderer. Final-game quality is **not** reduced for this PC: it gets a lighter profile; capable PCs get the standard one.
**Nothing below was measured on the target hardware.** The prototype ran only in a software-GPU browser build of Godot 4.7.2 (~8 fps, meaningless as a benchmark). Estimates are from shader source and fetch counts. The first real numbers must come from you running the VP-1 benchmark scene on the Windows machine (it prints frame time, draw calls and the profile in use).

## 1. Strategy in five rules
1. **Render small, scale by integers.** The whole 3D picture is 640×360. All per-pixel work (ocean, terrain, grade) runs on 230 k pixels, not 1.2 M. (est.: 4–5× cheaper than 1366×768 and 4× cheaper than 1280×720.)
2. **Few big draws, no real-time lights, no shadow maps.** Sprites batched per atlas page; one plane for ocean, one for terrain; halos and sprite shadows are quads. Budget ≤ 150 draw calls and ≤ 300 k vertices.
3. **Fake what the Compatibility renderer lacks:** bloom = additive pixel-band halos (+ optional low-res blur), DOF = tilt-shift blur on the grade pass, fog = colour mix by distance, reflections = a pattern of glints and a sky-colour tint on the water, shadows = projected silhouettes.
4. **Split the grade pass** (below) so the only full-resolution work is a nearest-neighbour blit.
5. **Quality ladder by profile**, selected automatically from a 3-second benchmark on first launch and always overridable.

## 2. Profiles
| Effect | Standard | Balanced | Dev-Lite (HD 3000 default until measured) |
|---|---|---|---|
| Internal size | 640×360 | 640×360 | 640×360 (or 480×270 if needed, ×2.67 → needs integer scale off) |
| Grade/blur/bloom | window res, 8+16 taps | **640×360**, 8+16 taps | none, 1 fetch (vignette, grade) |
| Ocean | 3 noise octaves + glints + foam | same | 1 octave, no glints, no dither wave lines |
| Sprite shadows | on, projected | on | off (blob decal) |
| Halos | 4-band + blur bloom | 4-band | 2 bands |
| Atmosphere/fog | colour mix + cloud shadows | colour mix | colour mix |
| Weather particles | 600 | 300 | 100 |
| Terrain | 5 fetches, dithered borders | same | cell map without displacement |
Est. cost (fetches per frame): Standard ≈ 25 M at 1366×768 (not viable on the HD 3000); Balanced ≈ 6 M; Dev-Lite ≈ 1–2 M. All *estimates*.

## 3. Techniques — feasible / risky / unsuitable
| Technique | Verdict | Reason / alternative |
|---|---|---|
| 640×360 SubViewport + integer scale | **Feasible**, core | Done in the prototypes. |
| Ortho camera, sprite snapping | **Feasible** | Done and verified in renders. |
| Billboard sprites with a depth bias in the vertex shader | **Feasible** | Done. |
| Baked voxel→sprite pipeline | **Feasible** | Done (124 PNGs). |
| Water band shader + distance-field map | **Feasible** | Done; ~8 fetches/pixel est. |
| Sprite projected shadows, 4-band halos | **Feasible** | Done. |
| Tilt-shift / vignette / grade in a canvas shader | **Feasible** (Balanced/Lite), heavy at full res | See §2. |
| MultiMesh sprite batching with INSTANCE_CUSTOM | **Feasible, not yet built** | VP-1. Mind the AABB trap. |
| Bloom via `Environment.glow` | **Risky** | Compatibility glow is LDR and costs two full-res passes; use halos by default. |
| Sun light shadows on meshes | **Risky** | One shadow map pass + 4 samples per pixel; skip on Lite. |
| Real-time point lights (lanterns) | **Risky** | One pass per light in Compatibility; limit to 2; halos instead. |
| ANGLE/D3D11 fallback on the HD 3000 | **Risky, unconfirmed** | Test on the machine; the engine prints which driver runs. |
| Sub-pixel camera smoothing | **Unsuitable** | Shimmer; replaced with snapped camera + smoothed target. |
| Rotating sprites at runtime | **Unsuitable** | Breaks pixel consistency; use pre-baked facings. |
| Volumetric fog, SSR, SDFGI, TAA/FXAA, true DOF | **Unsuitable** | Not supported in Compatibility. |
| Reflection render target for water | **Unsuitable** | Doubles the frame cost for little gain at 8 px/m. |
| Real 3D props with full lighting | **Unsuitable** | Mixes styles and costs lights; baked sprites only. |

## 4. Memory
Prototype art: 912 KB on disk, ~5 MB VRAM (est.). Production forecast < 64 MB VRAM; 2048² atlas pages, loaded per region. With 3 GB RAM total and an OS using ~1.2 GB, the game must stay below ~900 MB resident: stream region atlases; keep one island's sprites + sea tier loaded.

## 5. Measurement protocol (to run on your PC in VP-1)
Run the `benchmark` scene on Dev-Lite, Balanced, Standard for 30 s each at the real window size; it logs average/1% frame time, draw calls, vertices, texture memory, chosen driver. Compare with the 16.7 ms budget (60 fps) and the 33 ms floor (30 fps). Only then settle the default profile.

## 6. Proposed release sequence (small, testable)
| Release | Content | You test | Risk |
|---|---|---|---|
| **VP-1** Foundation | Production render pipeline module (stage, profiles, integer scaling, camera) + sprite MultiMesh + atlas importer + benchmark scene. No gameplay change. | Run the benchmark; confirm colours and sharpness. | Low |
| **VP-2** Ocean | Replace the sea scene's water with the new ocean (sailing unchanged), depth maps for the existing islands, wake. Old sprite ship stays. | Sail 5 minutes; check performance/readability. | Low–medium |
| **VP-3** Ship deck | New deck visuals under the existing walkable layout: hull, planks, cabin roof-off, rails, equipment, sleeping deck, hold; cannons only visual. Collision untouched, tests rerun. | Walk three decks, fish, interact with everything. | Medium (alignment) |
| **VP-4** Ship at sea | New hull sprites (16 × 5 trims), sail bake, wake integration, weather re-based on the new camera. | Sail, tack, storm. | Medium |
| **VP-5** Anvil Cay | New terrain, buildings, props, harbour for the existing r7 map; collision/interaction positions untouched. | Walk the city, M map, dialogue, shops. | Medium |
| **VP-6** Lighting & grade | Full time-of-day cycle, night lights/halos, atmosphere, profiles auto-selection. | A full 15-min day cycle. | Low |
| **VP-7** Characters | Captain, crew, NPCs, animations, portraits check. | Everything with people. | Medium (art) |
| **VP-8** Polish | Weakness list, optimisation pass with measured numbers. | Release candidate. | Low |
Each release: before/after screenshots from identical cameras, regression suite, a list of settings to disable on weak hardware, and an honest statement of what was and was not run on Windows. No release starts until the previous one is accepted, and **mass production starts only after you approve this Art Bible.**
