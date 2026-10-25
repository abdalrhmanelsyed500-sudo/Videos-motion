# EGYPTIAN TUKTUK MAYHEM — Art Bible (Phase 0)

## 1. Identity in one paragraph

Sun-baked contemporary Egypt rendered as a saturated, readable arcade world: ochre and sandstone facades under a hot
pale-blue sky, deep shadows, turquoise shop signage, dusty warm light at mission start and golden hour at streaks;
the tuk-tuk is a jewel-bright beetle in the middle of the frame. Geometry is simple and bold; **detail lives in
authored textures** (balconies, AC units, laundry lines, shutters, hand-painted shop signs) so low-poly stays rich.
Nothing grey-cube: every gameplay-relevant object has a silhouette and a material story.

## 2. Reference analysis (the two supplied Crazy Taxi screenshots — principles only, zero assets copied)

1. *Camera placement*: chase cam ~5–7 m behind, ~2.5 m up, slight down-tilt; car sits in the lower-centre third, road
   runs to a vanishing point ahead. → Ours: spring-arm 5.2 m / 2.4 m, tilt 12°, FOV 68→84 with speed.
2. *Road visibility*: the drivable path is always the brightest, least-cluttered ribbon in frame; bridges/water shots
   prove path-first framing. → Ours: asphalt value kept mid-dark, lane paint bright, sidewalk props never overhang the
   carriageway silhouette.
3. *Vehicle readability*: one saturated body colour vs neutral road; dark cabin void reads as "open seat"; roof sign
   gives job identity. → Ours: tuktuk paint = saturated teal/red/yellow variants, black canopy frame, roof "أجرة/TAXI"
   plate; body never shares hue with district walls.
4. *HUD layout*: shot 1 = almost nothing but a huge stylised timer; shot 2 = framed LED money panel top-right, minimap
   inset left with destination name+distance caption, everything else absent. → Ours: timer top-left oversized italic,
   LED fare panel top-right, minimap left (Phase 4), zero permanent clutter.
5. *Destination cue*: giant green world-space arrow floating above the road + minimap + metres caption: three
   redundant cues, one dominant. → Ours: same triad; arrow is a fat green chevron bobbing 6 m above target ring.
6. *Sense of speed*: wide FOV, low cam, converging lane lines, roadside rhythm (poles, trees) — not blur. → Ours: FOV
   ramp + pole/tree rhythm every ~12 m + exhaust puffs above 30 km/h.
7. *Palette*: shot 1 surreal teal/orange; shot 2 clean blue-sky suburbia — both high-chroma, low grey. → Ours: hot
   sand/ochre walls, turquoise & red signage, grey-blue asphalt, green market awnings; sky gradient per region.
8. *Geometry vs recognisability*: blocky low-poly buildings carrying painted detail; cars are 4-box silhouettes. →
   Ours: 1–2 box shells + facade textures with real window recesses where silhouette matters (cornices, balconies as
   thin slabs), tuktuk = authored 9-part mesh.
9. *Vehicle/road/traffic/destination relationship*: traffic sparse but present, arrow overrides all reading order. →
   Ours: parked props Phase 1, pooled traffic Phase 5; arrow z-topmost with outline.
10. *Presentation confidence*: chunky outlined type, LED digits, gold-framed panels. → Ours: bold italic display face
    with black outline (EN) + matching Arabic face (Phase 8), LED-style fare digits, framed panels with 2 px gold-brown
    border — Egyptian coffee-house brass, not sci-fi.

## 3. Modelling & material rules

- Metres, +Y up, origin at ground contact. Tuk-tuk ≈ 2.75 m L × 1.45 m W × 1.9 m H (realistic class proportions).
- Phase-1 meshes: tuktuk 9 parts ≤ 1 200 tris; buildings shell ≤ 200 tris each + facade texture 512²; characters ≤ 350
  tris. Budgets halved on low_end via mesh LOD swap (Phase 4).
- Textures authored by `tools/make_textures.py` (seeded, reviewable); atlas page per district family; no photo sources.
- Wear pass: subtle edge dust + rust flecks on tuktuk trim and market metal — painted in texture, not geometry.
- Lighting: one directional sun (warm 4500 K feel via colour), hemisphere sky colour per region profile, no realtime
  shadows on low_end, soft shadows 1 map on standard+.

## 4. UI style

Display type: heavy italic with black offset outline (timer, bonuses). Panels: dark umber glass with 2 px brass border,
LED-amber digits for money, white sans for labels; Arabic mirrors layout RTL (Phase 8). Destination arrow green
#3ddc55 with black outline; pickup ring amber; fail flash red once (no strobing).

## 5. Character rules (binding)

- Female characters: hijab fully covering hair + neck, loose respectful clothing (long sleeves, below-knee garments);
  enforced at **geometry** level (hijab mesh replaces hair mesh in the generator), at **texture** level (no hair
  textures on female heads) and at **review** level (checklist item in ASSET_INVENTORY). Applies to pedestrians,
  passengers, posters, AI-generated material.
- Variety without caricature: real occupational dress (galabiya, work jackets, uniforms, student backpacks), varied
  builds/ages/skin tones; informal-district residents portrayed with the same care as downtown office workers.

## 6. Asset QC cycle (per master brief §19)

require → generate → inspect shape → inspect colour → tri count → import test (wasm render) → scale/origin check →
collision check → gameplay scene test → refine. Inventory row per asset: name, source (authored/gen-AI/licensed),
status TEMP / FINAL-Pn, tri count, texture size, reviewer notes. AI-generated images (if ever used) are reference or
texture seeds only, inspected against §5, never accepted blind.

## 7. Placeholder policy

Grey shapes allowed ONLY inside `scenes/dev/` (invisible to gameplay) and must be listed as TEMP in the inventory.
Anything the player sees in a milestone screenshot must be an authored asset of that phase's quality bar.
