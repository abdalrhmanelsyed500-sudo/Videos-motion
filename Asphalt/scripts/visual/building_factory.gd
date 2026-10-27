extends RefCounted
class_name AGBuildingFactory
## Modular sandy-brick Egyptian roadside buildings with shops and roof props.

const SIGN_FILES := [
    "res://assets/textures/signs/shop_cafe.png",
    "res://assets/textures/signs/shop_spares.png",
    "res://assets/textures/signs/sign_maadi.png",
    "res://assets/textures/signs/sign_giza.png",
]

static func build(index: int, side: int, z: float, rng: RandomNumberGenerator) -> Node3D:
    var root := Node3D.new()
    root.name = "Building_%d_%d" % [side, index]
    var width := 8.0 + rng.randf() * 8.0
    var depth := 8.0 + rng.randf() * 9.0
    var floors := rng.randi_range(3, 6)
    var height := float(floors) * 3.15
    var texture_path := "res://assets/textures/brick_%d.png" % ((index % 3) + 1)
    var facade := AGPalette.textured("#FFFFFF", texture_path,
        Vector3(2.0, float(floors) * 0.65, 1.0))
    var concrete := AGPalette.textured("concrete", "res://assets/textures/concrete.png")
    var dark := AGPalette.mat("window")
    var metal := AGPalette.mat("#7C776C")
    var awning := AGPalette.textured("#FFFFFF", "res://assets/textures/awning_stripe.png",
        Vector3(1.0, 1.0, 1.0), true)
    var road_dir := -float(side)

    var base := AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width, height, depth)), facade,
        Vector3(0.0, height * 0.5, 0.0))
    base.name = "Facade"
    root.add_child(base)
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width + 0.4, 0.28, depth + 0.4)),
        concrete, Vector3(0.0, height + 0.14, 0.0)))

    # Ground-floor shop, dark doorway, awning and readable Arabic sign.
    var front_x := road_dir * (width * 0.5 + 0.04)
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.06, 2.2, 1.45)), dark,
        Vector3(front_x, 1.1, 0.0)))
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(1.35, 0.16, depth * 0.68)), awning,
        Vector3(front_x + road_dir * 0.68, 2.55, 0.0)))
    var sign_mat := sign_material(SIGN_FILES[index % SIGN_FILES.size()])
    var sign := AGMeshFactory.mesh_node(AGMeshFactory.quad(Vector2(2.8, 1.05)), sign_mat,
        Vector3(front_x + road_dir * 0.09, 3.25, 0.0), Vector3(0, 90.0 * road_dir, 0))
    sign.name = "ShopSign"
    root.add_child(sign)

    # Balconies with coarse railings on alternating floors.
    for floor_index in range(1, floors):
        if (floor_index + index) % 2 != 0:
            continue
        var y := float(floor_index) * 3.15 + 0.5
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(1.0, 0.14, depth * 0.46)),
            concrete, Vector3(front_x + road_dir * 0.5, y, 0.0)))
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.08, 0.65, depth * 0.46)),
            metal, Vector3(front_x + road_dir * 1.0, y + 0.38, 0.0), Vector3.ZERO,
            Vector3(1.0, 1.0, 1.0)))

    # Water tank, satellite dish, AC unit and unfinished rebar.
    if rng.randf() < 0.55:
        var tank_x := rng.randf_range(-width * 0.28, width * 0.28)
        var tank_z := rng.randf_range(-depth * 0.25, depth * 0.25)
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.65, 1.2, 8), metal,
            Vector3(tank_x, height + 0.9, tank_z)))
    if rng.randf() < 0.45:
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.sphere(0.55, 7, 4), concrete,
            Vector3(width * 0.24, height + 0.5, -depth * 0.20), Vector3.ZERO,
            Vector3(1.0, 0.18, 1.0)))
    if rng.randf() < 0.40:
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.9, 0.6, 0.5)), metal,
            Vector3(front_x + road_dir * 0.35, 2.0, depth * 0.30)))
    if rng.randf() < 0.30:
        for i in range(4):
            var px := -width * 0.35 + float(i % 2) * width * 0.7
            var pz := -depth * 0.30 + float(i / 2) * depth * 0.6
            root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.035, 1.5, 5), metal,
                Vector3(px, height + 0.9, pz)))
    root.set_meta("floors", floors)
    return root

static func sign_material(path: String) -> StandardMaterial3D:
    var material := AGPalette.mat("#FFFFFF", true, path)
    material.cull_mode = BaseMaterial3D.CULL_DISABLED
    return material
