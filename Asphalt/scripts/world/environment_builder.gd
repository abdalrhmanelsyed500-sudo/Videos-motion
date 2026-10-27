extends RefCounted
class_name AGEnvironmentBuilder
## Builds the full low-poly Cairo / Giza Ring Road environment.

static func build(quality := "medium") -> Node3D:
    var root := Node3D.new()
    root.name = "Environment"
    root.set_meta("quality", quality)
    var density: float = float({"low": 0.52, "medium": 0.76, "high": 1.0}.get(quality, 0.76))
    var shadows := quality != "low"

    root.add_child(_sky_and_light(shadows))
    root.add_child(_ground())
    root.add_child(_hills())
    root.add_child(_clouds(density))
    root.add_child(_buildings(density))
    root.add_child(_vegetation(density))
    root.add_child(_streetlights())
    root.add_child(_overpasses())
    root.add_child(_road_signs())
    root.add_child(_intersections())
    root.add_child(_pedestrians(density))
    root.add_child(_parked_vehicles(density))
    return root

static func _sky_and_light(shadows: bool) -> Node3D:
    var holder := Node3D.new()
    holder.name = "SkyAndLight"
    var world_environment := WorldEnvironment.new()
    var environment := Environment.new()
    var sky := Sky.new()
    var sky_material := ProceduralSkyMaterial.new()
    sky_material.sky_top_color = AGPalette.c("sky_top")
    sky_material.sky_horizon_color = AGPalette.c("sky_horizon")
    sky_material.ground_bottom_color = AGPalette.c("sand_dark")
    sky_material.ground_horizon_color = AGPalette.c("sand_light")
    sky_material.sun_angle_max = 18.0
    sky_material.sun_curve = 0.18
    sky.sky_material = sky_material
    environment.background_mode = Environment.BG_SKY
    environment.sky = sky
    environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    environment.ambient_light_color = AGPalette.c("sky_horizon")
    environment.ambient_light_energy = 0.68
    environment.fog_enabled = true
    environment.fog_light_color = AGPalette.c("sand_light")
    environment.fog_density = 0.00065
    world_environment.environment = environment
    holder.add_child(world_environment)

    var sun := DirectionalLight3D.new()
    sun.name = "DesertSun"
    sun.rotation_degrees = Vector3(-38.0, -36.0, 0.0)
    sun.light_color = Color(1.0, 0.93, 0.77)
    sun.light_energy = 1.25
    sun.shadow_enabled = shadows
    sun.directional_shadow_max_distance = 320.0
    holder.add_child(sun)
    return holder

static func _ground() -> MeshInstance3D:
    var mesh := PlaneMesh.new()
    mesh.size = Vector2(12000.0, 12000.0)
    mesh.subdivide_width = 1
    mesh.subdivide_depth = 1
    var material := AGPalette.textured("#FFFFFF", "res://assets/textures/sand.png",
        Vector3(260.0, 260.0, 1.0), true)
    var ground := AGMeshFactory.mesh_node(mesh, material, Vector3(0.0, -3.0, -2200.0))
    ground.name = "DesertGround"
    return ground

static func _hills() -> Node3D:
    var holder := Node3D.new()
    holder.name = "DistantHills"
    var rng := RandomNumberGenerator.new()
    rng.seed = 1402
    for i in range(30):
        var side := -1.0 if i % 2 == 0 else 1.0
        var z := -450.0 - float(i) * 160.0 - rng.randf() * 120.0
        var x := side * (140.0 + rng.randf() * 420.0)
        var material := AGPalette.mat(["sand", "sand_light", "sand_dark"][i % 3])
        var hill := AGMeshFactory.mesh_node(AGMeshFactory.sphere(1.0, 7, 4), material,
            Vector3(x, -11.0, z), Vector3.ZERO,
            Vector3(90.0 + rng.randf() * 90.0, 18.0 + rng.randf() * 28.0, 55.0 + rng.randf() * 60.0))
        holder.add_child(hill)
    return holder

static func _clouds(density: float) -> Node3D:
    var holder := Node3D.new()
    holder.name = "CoarseClouds"
    var rng := RandomNumberGenerator.new()
    rng.seed = 8891
    var material := AGPalette.billboard("res://assets/textures/cloud.png")
    var count := int(26.0 * density)
    for i in range(count):
        var cloud := AGMeshFactory.mesh_node(
            AGMeshFactory.quad(Vector2(52.0 + rng.randf() * 40.0, 20.0 + rng.randf() * 10.0)),
            material,
            Vector3(rng.randf_range(-520.0, 520.0), 72.0 + rng.randf() * 52.0,
                -180.0 - float(i) * 170.0 - rng.randf() * 100.0))
        holder.add_child(cloud)
    return holder

static func _buildings(density: float) -> Node3D:
    var holder := Node3D.new()
    holder.name = "RoadsideBuildings"
    var rng := RandomNumberGenerator.new()
    rng.seed = 23018
    var index := 0
    var z := 120.0
    while z > AGRoadPath.FINISH_Z:
        if rng.randf() <= density:
            for side in [-1, 1]:
                if rng.randf() > density * 0.92:
                    continue
                var building := AGBuildingFactory.build(index, side, z, rng)
                var x := AGRoadPath.center_x(z) + float(side) * (AGRoadPath.BARRIER_OFFSET + 11.0 + rng.randf() * 18.0)
                building.position = Vector3(x, AGRoadPath.height_at(z) - 0.35, z)
                building.rotation.y = AGRoadPath.yaw_at(z) + rng.randf_range(-0.08, 0.08)
                holder.add_child(building)
                index += 1
        z -= 88.0 + rng.randf() * 36.0
    return holder

static func _vegetation(density: float) -> Node3D:
    var holder := Node3D.new()
    holder.name = "Vegetation"
    var rng := RandomNumberGenerator.new()
    rng.seed = 731
    var count := int(64.0 * density)
    for i in range(count):
        var z := 80.0 - float(i) * (AGRoadPath.RACE_LENGTH / float(maxi(count, 1))) - rng.randf() * 35.0
        var side := -1.0 if i % 2 == 0 else 1.0
        var x := AGRoadPath.center_x(z) + side * (AGRoadPath.BARRIER_OFFSET + 1.5 + rng.randf() * 7.0)
        var plant: Node3D = _palm(rng) if i % 3 != 0 else _tree(rng)
        plant.position = Vector3(x, AGRoadPath.height_at(z) - 0.25, z)
        plant.rotation.y = rng.randf() * TAU
        holder.add_child(plant)
    return holder

static func _palm(rng: RandomNumberGenerator) -> Node3D:
    var root := Node3D.new()
    var trunk_mat := AGPalette.mat("#7B6040")
    var leaf_mat := AGPalette.mat("palm")
    var height := 4.5 + rng.randf() * 2.0
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.14, height, 6, 0.09),
        trunk_mat, Vector3(0.0, height * 0.5, 0.0)))
    for i in range(7):
        var angle := float(i) * TAU / 7.0
        var leaf := AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.16, 0.09, 2.8)), leaf_mat,
            Vector3(0.0, height, 0.0), Vector3(-18.0, rad_to_deg(angle), 0.0))
        root.add_child(leaf)
    return root

static func _tree(rng: RandomNumberGenerator) -> Node3D:
    var root := Node3D.new()
    var trunk_mat := AGPalette.mat("#6E5335")
    var leaf_mat := AGPalette.mat("leaf")
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.20, 2.6, 6), trunk_mat,
        Vector3(0.0, 1.3, 0.0)))
    for i in range(3):
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.sphere(1.0, 7, 4), leaf_mat,
            Vector3(rng.randf_range(-0.7, 0.7), 3.0 + rng.randf_range(-0.2, 0.8), rng.randf_range(-0.7, 0.7)),
            Vector3.ZERO, Vector3(1.3, 1.0, 1.3)))
    return root

static func _streetlights() -> Node3D:
    var holder := Node3D.new()
    holder.name = "StreetLights"
    var pole_transforms: Array = []
    var arm_transforms: Array = []
    var lamp_transforms: Array = []
    var z := 120.0
    while z > AGRoadPath.FINISH_Z:
        for side in [-1, 1]:
            var c := AGRoadPath.center_x(z)
            var y := AGRoadPath.height_at(z)
            var road_dir := -float(side)
            var x := c + float(side) * (AGRoadPath.BARRIER_OFFSET + 1.2)
            var basis := Basis.IDENTITY.rotated(Vector3.UP, AGRoadPath.yaw_at(z))
            pole_transforms.append(Transform3D(basis, Vector3(x, y + 3.6, z)))
            arm_transforms.append(Transform3D(basis, Vector3(x + road_dir * 0.9, y + 7.0, z)))
            lamp_transforms.append(Transform3D(basis, Vector3(x + road_dir * 1.85, y + 6.92, z)))
        z -= 82.0
    holder.add_child(_multimesh("LightPoles", Vector3(0.16, 7.2, 0.16), AGPalette.mat("metal"), pole_transforms))
    holder.add_child(_multimesh("LightArms", Vector3(1.9, 0.12, 0.12), AGPalette.mat("metal"), arm_transforms))
    holder.add_child(_multimesh("Lamps", Vector3(0.60, 0.14, 0.30), AGPalette.mat("#F0D486", true), lamp_transforms))
    return holder

static func _multimesh(node_name: String, size: Vector3, material: Material, transforms: Array) -> MultiMeshInstance3D:
    var mesh := AGMeshFactory.box(size)
    mesh.material = material
    var multimesh := MultiMesh.new()
    multimesh.transform_format = MultiMesh.TRANSFORM_3D
    multimesh.mesh = mesh
    multimesh.instance_count = maxi(1, transforms.size())
    for i in range(transforms.size()):
        multimesh.set_instance_transform(i, transforms[i])
    var instance := MultiMeshInstance3D.new()
    instance.name = node_name
    instance.multimesh = multimesh
    instance.material_override = material
    return instance

static func _overpasses() -> Node3D:
    var holder := Node3D.new()
    holder.name = "Overpasses"
    var concrete := AGPalette.textured("concrete", "res://assets/textures/concrete.png")
    var asphalt := AGPalette.textured("#FFFFFF", "res://assets/textures/asphalt.png", Vector3(4, 1, 1))
    var white := AGPalette.mat("white")
    for overpass_z in [-1200.0, -3200.0, -4250.0]:
        var c := AGRoadPath.center_x(overpass_z)
        var y := AGRoadPath.height_at(overpass_z)
        var group := Node3D.new()
        group.position = Vector3(c, y, overpass_z)
        group.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(115.0, 1.3, 18.0)), concrete,
            Vector3(0.0, 8.6, 0.0)))
        group.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(115.0, 0.06, 15.0)), asphalt,
            Vector3(0.0, 9.28, 0.0)))
        group.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(115.0, 0.04, 0.16)), AGPalette.mat("yellow", true),
            Vector3(0.0, 9.32, 0.0)))
        for rail_side in [-1, 1]:
            group.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(115.0, 0.8, 0.28)), white,
                Vector3(0.0, 9.75, float(rail_side) * 8.5)))
        for px in [-48.0, -28.0, 28.0, 48.0]:
            group.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(1.5, 8.2, 1.5)), concrete,
                Vector3(px, 4.1, 0.0)))
        holder.add_child(group)
    return holder

static func _road_signs() -> Node3D:
    var holder := Node3D.new()
    holder.name = "OverheadSigns"
    var sign_paths := [
        "res://assets/textures/signs/sign_ring_road.png",
        "res://assets/textures/signs/sign_giza.png",
        "res://assets/textures/signs/sign_maadi.png",
        "res://assets/textures/signs/sign_nasr_city.png",
    ]
    var post_mat := AGPalette.mat("metal")
    var board_mat := AGPalette.mat("#1D5C86")
    var sign_z_values := [-420.0, -1580.0, -2860.0, -4180.0]
    for i in range(sign_z_values.size()):
        var z: float = sign_z_values[i]
        var c := AGRoadPath.center_x(z)
        var y := AGRoadPath.height_at(z)
        var group := Node3D.new()
        group.position = Vector3(c, y, z)
        group.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(13.0, 3.3, 0.25)), board_mat,
            Vector3(0.0, 7.3, 0.0)))
        var sign_mat := AGBuildingFactory.sign_material(sign_paths[i])
        group.add_child(AGMeshFactory.mesh_node(AGMeshFactory.quad(Vector2(12.7, 3.0)), sign_mat,
            Vector3(0.0, 7.3, 0.16)))
        for side in [-1, 1]:
            group.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.11, 7.0, 6), post_mat,
                Vector3(float(side) * 6.1, 3.5, 0.0)))
        holder.add_child(group)
    return holder

static func _intersections() -> Node3D:
    var holder := Node3D.new()
    holder.name = "Intersections"
    var asphalt := AGPalette.textured("#FFFFFF", "res://assets/textures/asphalt.png", Vector3(8, 1, 1))
    var concrete := AGPalette.mat("concrete")
    var metal := AGPalette.mat("metal")
    for junction_z in [-900.0, -2100.0, -3900.0]:
        var c := AGRoadPath.center_x(junction_z)
        var y := AGRoadPath.height_at(junction_z)
        var group := Node3D.new()
        group.position = Vector3(c, y, junction_z)
        group.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(95.0, 0.035, 13.0)), asphalt,
            Vector3(0.0, -0.02, 0.0)))
        for side in [-1, 1]:
            group.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.09, 4.5, 6), metal,
                Vector3(float(side) * 11.0, 2.25, 0.0)))
            group.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.45, 1.1, 0.45)),
                AGPalette.mat("black"), Vector3(float(side) * 11.0, 4.3, 0.0)))
            group.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.22, 0.22, 0.22)),
                AGPalette.mat("#D64B32", true), Vector3(float(side) * 11.0, 4.65, 0.0)))
        group.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(95.0, 0.16, 0.7)), concrete,
            Vector3(0.0, 0.08, 7.0)))
        holder.add_child(group)
    return holder

static func _pedestrians(density: float) -> Node3D:
    var holder := Node3D.new()
    holder.name = "Pedestrians"
    var rng := RandomNumberGenerator.new()
    rng.seed = 555
    var count := int(24.0 * density)
    for i in range(count):
        var z := 150.0 - float(i) * (AGRoadPath.RACE_LENGTH / float(maxi(count, 1)))
        var side := -1.0 if i % 2 == 0 else 1.0
        var x := AGRoadPath.center_x(z) + side * (AGRoadPath.BARRIER_OFFSET + 1.1 + rng.randf() * 3.0)
        var person := Node3D.new()
        person.position = Vector3(x, AGRoadPath.height_at(z), z)
        var skin := AGPalette.mat(["skin_light", "skin_mid", "skin_dark"][i % 3])
        var cloth := AGPalette.mat(["#C32228", "#37568A", "#D6B98B", "#4F8E3A"][i % 4])
        person.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.18, 0.75, 6, 0.22), cloth,
            Vector3(0.0, 0.95, 0.0)))
        person.add_child(AGMeshFactory.mesh_node(AGMeshFactory.sphere(0.16, 6, 4), skin,
            Vector3(0.0, 1.50, 0.0)))
        for leg_side in [-1, 1]:
            person.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.06, 0.55, 5), AGPalette.mat("black"),
                Vector3(float(leg_side) * 0.09, 0.30, 0.0)))
        person.rotation.y = rng.randf() * TAU
        holder.add_child(person)
    return holder

static func _parked_vehicles(density: float) -> Node3D:
    var holder := Node3D.new()
    holder.name = "ParkedVehicles"
    var rng := RandomNumberGenerator.new()
    rng.seed = 919
    var count := int(12.0 * density)
    for i in range(count):
        var z := 60.0 - float(i) * (AGRoadPath.RACE_LENGTH / float(maxi(count, 1))) - rng.randf() * 60.0
        var side := -1.0 if i % 2 == 0 else 1.0
        var type_id: String = ["car", "taxi", "microbus", "truck"][i % 4]
        var type_def := _traffic_definition(type_id)
        var vehicle := AGVehicleFactory.build(type_def)
        vehicle.position = Vector3(AGRoadPath.center_x(z) + side * (AGRoadPath.BARRIER_OFFSET + 3.0),
            AGRoadPath.height_at(z), z)
        vehicle.rotation.y = AGRoadPath.yaw_at(z) + rng.randf_range(-0.06, 0.06)
        holder.add_child(vehicle)
    return holder

static func _traffic_definition(type_id: String) -> Dictionary:
    var defaults := {
        "car": {"id": "car", "color": "#9AA0A1", "accent": "#D4D2C7", "length": 4.4, "width": 1.9, "height": 1.4},
        "taxi": {"id": "taxi", "color": "#E5BC28", "accent": "#24242A", "length": 4.5, "width": 1.9, "height": 1.5},
        "microbus": {"id": "microbus", "color": "#E7E2D4", "accent": "#2862A4", "length": 5.6, "width": 2.1, "height": 2.2},
        "truck": {"id": "truck", "color": "#8B6B4D", "accent": "#3F454A", "length": 8.5, "width": 2.6, "height": 3.0},
    }
    return defaults.get(type_id, defaults["car"])
