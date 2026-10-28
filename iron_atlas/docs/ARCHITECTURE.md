# IRON ATLAS architecture — Stage 2

## Layout and state

`game/core/campaign_state.gd` is the authoritative campaign model. Region,
faction, formation, order, market order, treaty and battle IDs are stable strings;
regions and systems hold data, not one scene node per district. The project uses
four autoloads: `EventBus`, `GameState`, `CampaignClock`, and `SaveManager`.
`GameState` wires independent `RefCounted` strategic systems to the clock:

- `world/world_generator.gd`: deterministic 24-district legacy map or a
  configurable 25–400-district regional land graph (200 is the setup default).
  `neighbors` are land edges; `sea_neighbors` are separate, currently
  non-navigable edges. Validation checks IDs, ownership, symmetry and land
  connectivity.
- `military/command_system.gd`, `combat_system.gd`: validated orders, land
  BFS, control and authoritative battle consequences; tactical and abstract
  battle outcomes share loss/finalization code.
- `administration/administration_system.gd`: capture, occupation costs,
  support, legitimacy, recovery, investments and campaign outcomes.
- `economy/`, `logistics/`, `diplomacy/`, `ai/`: persistent faction budgets and
  inventory, finite stockpiles and supply connectivity, market deliveries,
  ceasefires, and local-information AI using the same systems as the player.
- `scenes/`: interface, one canvas for map regions with zoom/pan and viewport
  culling, and a tactical scene; `core/pixel_art.gd` loads the same nearest-
  filtered 24px unit / 32px terrain assets in native and web environments.

One equipped unit is an abstract **12-person squad** and one equipment item
is an abstract package, not an individual rifle or vehicle. The starting
scenario has 60 personnel. Reserves, wounded, deaths, condition, gear and
stockpiles persist. Occupation and administration values directly influence
revenue, supply access, stability and political outcomes.

## Clock and interactions

`CampaignClock` is paused or runs 1/2/4/8 campaign days per real second.
Daily: land movement, food and ammunition supply, wages and equipment upkeep,
delivery, ceasefire expiry and encounters. Only occupied regions are scanned
for combat. Player contact pauses the clock and offers tactical or automatic
resolution; AI-versus-AI contacts resolve abstractly. Weekly: local stock
production, tax, occupation/admin, recovery and faction decisions. Monthly:
inflation and debt interest for all factions; player political stability drifts.
Map input and UI call these same system methods; selecting a region does not
itself change ownership.

The tactical scene still owns its grid movement, targeting and firing logic,
and spends formation ammunition directly. At battle end it calls the shared
`CombatSystem` to update both sides, salvage, retreats and reports. Thus the
strategic model is decoupled from rendering, but the tactical simulation is
**not yet fully extracted** from its scene.

## Saves and determinism

`persistence/save_system.gd` writes a temporary file and rotates a backup. Its
JSON envelope contains a readable `state` plus authoritative `state_exact`
(base64 encoded Godot Variant bytes without object decoding). The latter is
necessary because a decimal JSON float round trip was observed to change a
value by one ULP. The PCG RNG stream state is serialized as a decimal string to
avoid 64-bit JSON precision loss. Exact save/resume continuation is tested over
120 days in a 200-region world.

Schema v1 saves load through `CampaignState.migrate()` with new regional,
formation and faction defaults. Stage 1 stored the RNG seed rather than the
stream position, so that position cannot be recovered: migration restarts the
stream and records this in history. Saves are currently exposed through one
manual UI slot; no tactical mid-battle save or autosave is implemented.

## Current boundaries

Supply reachability is a daily BFS per faction, and region income/admin runs
weekly. The renderer avoids 200 scene nodes and culls off-screen region draws,
but has no spatial chunk cache or measured GPU frame budget. The regional
world is a jittered grid graph, not an authored global atlas. Maritime transport,
industry/research, comprehensive intelligence and international endgame are
future work.
