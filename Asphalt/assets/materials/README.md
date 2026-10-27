# Material palette

`scripts/visual/palette.gd` is the canonical palette. It was chosen from measurements of the
three supplied reference images and emphasizes a dusty blue sky, purple-gray asphalt, sandy
brick architecture and a charcoal dashboard. Materials use `StandardMaterial3D` with high
roughness, no metallic response, and nearest texture filtering where coarse texels are desired.
