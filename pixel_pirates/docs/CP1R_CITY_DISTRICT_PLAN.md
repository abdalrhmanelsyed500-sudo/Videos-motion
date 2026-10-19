# Anvil Harbor: district plan (CP-1 revision r3)

Written BEFORE the layout code, then implemented in `tools/h2d/city_layout.py`. If the plan and the code disagree, the code (and `anvil_cay.json`) wins; the numbers below are what the baker produced on 2026-10-19.

## Why the old Fish Row did not read as a capital
Fish Row was one flat lane of 30 m x 50 m with five cottages and a market canopy. A capital needs: a skyline that climbs, an unmistakable seat of power, wealth that gets visibly richer away from the water, a working harbour, a defended edge, and streets that lead somewhere.

## The idea: "a city that climbs out of the sea"
Anvil Harbor rises in four terraces from the quay to the Governor's Hill. Poor and working at the water, rich and ordered at the top. One grand avenue (Anchor Avenue) runs from the pier straight up to the palace; retaining walls and stairs separate the terraces; a wall with two gates closes the north.

| Terrace | Height | Districts | Look |
|---|---|---|---|
| Harbour / Lower Town | 1.95 to 5.0 m (gentle slope) | The Quay (east docks, warehouses, tavern, inn, customs), Fish Row (west, kept from CP-1), the Shipyard, Anvil Battery, Anvil Light | timber, tar, thatch, brick warehouses, cranes, crates, cargo |
| A | 5.0 m | Market Quarter: Grand Market Square, Exchange, Counting House, shops, homes | plaster, half-timber, brick, striped shop awnings |
| B: Hill Road | 7.4 m | Hill Road Terrace: tall townhouses, merchants' homes | tall 3-storey houses in brick, white, sand, rose, blue |
| C: The Mansions | 9.9 m | Terrace Walk: mansions with columns and gardens, lawns, hedges, trees | white, rose, ochre and stone mansions, teal / slate roofs |
| D: Governor's Hill | 12.5 m | Palace, Town Hall, Barracks, Treasury, palace gardens, fountain | the grandest buildings, statues, long forecourt |

Walls (retaining walls) at z = -106, -151, -197; stair columns at x = 16 (the avenue), -28, 62, -150, 140. The north wall stands at z = -270 with the **West Gate** (x -110) and **East Gate** (x 120); the east and west sides are closed by rows of wall posts down to the sea.

## Streets
Quay Street (z 0), Chandlers' Street (-44), Merchants' Row (-86), Hill Road (-113), Terrace Walk (-158); lanes West (x -28), East (62), Far West (-150), Far East (140), Net Lane (x -112), Shore Lane (x 112); **Anchor Avenue** x 8..24 from z -4 to -199 (slab centre, brick pavements, palms and iron lamps every 9 m). Plazas: Customs Square (the Anvil monument), Grand Market Square (fountain, 8 stalls, benches, tubs), the Palace forecourt.

## Landmarks the player can find (all on the map)
Pier (your berth) / Fish Market (Fish Row) / Harbour notice board / Customs House / The Anchor and Crown tavern / The Gilded Gull inn / Grand Market Square / Merchants' Exchange / Counting House / Governor's Palace / Town Hall (clock tower) / Barracks / Treasury / West and East Gate / Garrick's boatyard / Shipyard / Anvil Battery / Anvil Light.

## Numbers (from the bake)
515 buildings (256 wall posts and 27 wall sections + towers and gates, 224 houses, shops, warehouses, mansions, tavern and inn), 8 grand buildings (palace, town hall, customs house, guild hall (the Exchange), barracks, 2 counting houses, fort bastion), 8 civic monuments (2 fountains, 3 statues, the Anvil, 2 dock cranes), 321 street props (92 iron lamps, planters, tubs, crates, barrels, carts), 133 planted trees, 184 people. All art is original pixel art from the project palette (`tools/h2d/city_kit.py`, `city_art.py`, `city_props.py`), 14.4 px per metre like the rest of the port.

## People (184, every one a man: project rule 1)
52 townsmen, 26 shopkeepers and stallholders (each shop has a named keeper with their own greeting, line and wares), 19 merchants, 18 guards (palace, barracks, gates, battery, patrols), 18 nobles, 17 fishers, 10 dockers, 10 sailors, 7 clerks (customs, exchange, counting house, palace steward, registrar, treasury), 2 innkeepers, and the 4 recruits. 43 have personal names.

## Checks that guard the plan
`tools/h2d/check_land.py`: every place and every person stands on ground the walker can stand on and can be reached on foot from the pier; the pier reaches all four island stops on foot. `tools/h2d/check_port.py`: wander discs, patrol legs, no two people within 1.2 m (the layout keeps 1.7 m). These are static checks of the baked data, not a Godot run.
