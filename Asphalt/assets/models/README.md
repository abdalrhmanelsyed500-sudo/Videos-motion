# Procedural model library

The game does not depend on an external commercial model pack. `scripts/visual/mesh_factory.gd`,
`bike_factory.gd`, `rider_factory.gd`, `vehicle_factory.gd` and `building_factory.gd` construct
low-poly Godot meshes at runtime from reusable shaped parts. This keeps every model's scale,
pivot, material and collision role deterministic.

- Six motorcycles have separate wheel pivots, steering head, frame tubes, tank, seat, engine,
  exhausts, lights, handlebars and rider anchor.
- Eight riders share a rig but have distinct hair meshes, clothing colors, accessories, skin tones
  and silhouette proportions.
- Seven traffic vehicle styles have type-specific bodies, cabins, windows, lights and wheels.
- Buildings are modular textured blocks with balconies, water tanks, signs and unfinished roofs.

Generated textures and UI art live in `assets/textures/` and `assets/ui/`.
