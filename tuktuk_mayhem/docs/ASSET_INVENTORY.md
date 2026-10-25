# EGYPTIAN TUKTUK MAYHEM — Asset Inventory (living)

Source generators: `tools/make_models.py` (geometry: .obj/.mtl DCC source + runtime
`game/data/meshes/*.mesh.json`), `tools/make_textures.py` (PIL, seeded). All assets authored in-repo;
no third-party or scraped assets; AI image tools not used in Phase 1. Status labels per ART_BIBLE §6.

## Geometry (tri counts from specs)

| Asset | Tris | Status | Notes |
|---|---|---|---|
| tuktuk | ~150 | FINAL-P1 | 9-part silhouette: cowl, cabin, canopy, windshield, bench, fenders, roof sign, 3 wheels. Phase 3 adds interior/trim detail |
| wheel | 44 | FINAL-P1 | spare/prop hub |
| building_a | ~120 | FINAL-P1 | sandstone apartment + balcony slabs + cornice + roof hut + tank |
| building_b | ~90 | FINAL-P1 | shopfront row + awning + sign band + pergola |
| building_c | ~50 | FINAL-P1 | rural brick house + parapet + porch |
| person / person_hijab | ~90 / ~110 | TEMP-P1 | stylised blocky; hijab = geometry-level rule (ART_BIBLE §5). Phase 3: proportioned bodies + AnimationPlayer clips |
| crate_stack / market_stall / lamp_post / speed_bump / arrow_chevron / parked_car | 12–70 | FINAL-P1 | props |

## Textures (all 256² except facades 512²)

| Texture | Use | Status |
|---|---|---|
| t_asphalt | roads (edge lines + centre dash, tiles 8 m) | FINAL-P1 |
| t_sidewalk | sidewalks + ground base | FINAL-P1 |
| t_facade_a/b/c | apartment / shopfront / rural brick (windows, AC units, shutters painted) | FINAL-P1 |
| t_tuktuk_paint | teal paint + cream/red stripes + wear chips | FINAL-P1 |
| t_awning / t_sign_band / t_wood / t_whitewash / t_bump / t_plate | awnings, shop band, crates, trim, bumps, plate | FINAL-P1 |

## Audio / fonts / UI art

None yet — Phase 8. UI is code-drawn CanvasLayer (documented TEMP-P1 in PRODUCTION_PLAN).

## Known TEMP items carried openly

- Passenger pose animation = scripted tween (TEMP), replaced Phase 3.
- Wheel steering/roll visual hubs hidden (body mesh carries wheels) — Phase 2.
- Chase-cam framing tune (pitch/arm) — Phase 2 driving-quality pass.
- t02-style transient black frame right after scene change (camera lerp from origin) — Phase 2.
