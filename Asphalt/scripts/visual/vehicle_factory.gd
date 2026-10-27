extends RefCounted
class_name AGVehicleFactory
## Builds recognizable low-poly Egyptian traffic vehicles from shaped parts.

static func build(type_def: Dictionary) -> AGVehicleView:
    var root := AGVehicleView.new()
    root.name = "VehicleView"
    var type_id := String(type_def.get("id", "car"))
    root.set_meta("vehicle_id", type_id)
    var body_mat := AGPalette.mat(String(type_def.get("color", "#9AA0A1")))
    var accent_mat := AGPalette.mat(String(type_def.get("accent", "#D4D2C7")))
    var dark_mat := AGPalette.mat("#25262B")
    var glass_mat := AGPalette.mat("#4E6074")
    var tire_mat := AGPalette.mat("#191A1E")
    var rim_mat := AGPalette.mat("#999C9A")
    var lamp_mat := AGPalette.mat("#F1D886", true)
    var tail_mat := AGPalette.mat("#C93630", true)
    var length := float(type_def.get("length", 4.5))
    var width := float(type_def.get("width", 1.9))
    var height := float(type_def.get("height", 1.5))

    match type_id:
        "microbus", "minibus":
            _build_bus(root, type_id, length, width, height, body_mat, accent_mat, dark_mat,
                glass_mat, tire_mat, rim_mat, lamp_mat, tail_mat)
        "truck", "trailer":
            _build_truck(root, type_id, length, width, height, body_mat, accent_mat, dark_mat,
                glass_mat, tire_mat, rim_mat, lamp_mat, tail_mat)
        _:
            _build_car(root, type_id, length, width, height, body_mat, accent_mat, dark_mat,
                glass_mat, tire_mat, rim_mat, lamp_mat, tail_mat)
    return root

static func _wheel(radius: float, tire_mat: Material, rim_mat: Material) -> Node3D:
    var pivot := Node3D.new()
    pivot.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(radius, 0.20, 10), tire_mat,
        Vector3.ZERO, Vector3(0, 0, 90)))
    pivot.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(radius * 0.52, 0.22, 8), rim_mat,
        Vector3.ZERO, Vector3(0, 0, 90)))
    return pivot

static func _add_wheels(root: AGVehicleView, positions: Array, radius: float,
        tire_mat: Material, rim_mat: Material) -> void:
    root.wheel_radius = radius
    for pos in positions:
        var wheel := _wheel(radius, tire_mat, rim_mat)
        wheel.position = pos
        root.add_child(wheel)
        root.wheels.append(wheel)

static func _build_car(root: AGVehicleView, type_id: String, length: float, width: float, height: float,
        body_mat: Material, accent_mat: Material, dark_mat: Material, glass_mat: Material,
        tire_mat: Material, rim_mat: Material, lamp_mat: Material, tail_mat: Material) -> void:
    var body_y := 0.72
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width, 0.72, length)), body_mat,
        Vector3(0.0, body_y, 0.0)))
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width * 0.82, 0.55, length * 0.52)), body_mat,
        Vector3(0.0, body_y + 0.60, 0.08)))
    # Hood slopes by a small rotation; windows are separate readable panels.
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width * 0.90, 0.10, length * 0.28)), body_mat,
        Vector3(0.0, body_y + 0.39, -length * 0.30), Vector3(-7, 0, 0)))
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width * 0.74, 0.34, 0.05)), glass_mat,
        Vector3(0.0, body_y + 0.67, -length * 0.18)))
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width * 0.74, 0.34, 0.05)), glass_mat,
        Vector3(0.0, body_y + 0.67, length * 0.28)))
    for side in [-1, 1]:
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.035, 0.30, length * 0.38)), glass_mat,
            Vector3(float(side) * width * 0.415, body_y + 0.67, 0.06)))
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.12, 0.10, 0.08)), lamp_mat,
            Vector3(float(side) * width * 0.32, body_y, -length * 0.50)))
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.12, 0.10, 0.08)), tail_mat,
            Vector3(float(side) * width * 0.32, body_y, length * 0.50)))
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width * 1.03, 0.12, 0.10)), dark_mat,
        Vector3(0.0, 0.50, -length * 0.52)))
    _add_wheels(root, [
        Vector3(-width * 0.52, 0.36, -length * 0.32), Vector3(width * 0.52, 0.36, -length * 0.32),
        Vector3(-width * 0.52, 0.36, length * 0.32), Vector3(width * 0.52, 0.36, length * 0.32),
    ], 0.36, tire_mat, rim_mat)
    if type_id == "taxi":
        for i in range(7):
            root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.02, 0.10, 0.26)), dark_mat,
                Vector3(-width * 0.51, 0.82, -length * 0.30 + float(i) * length * 0.10)))
            root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.02, 0.10, 0.26)), dark_mat,
                Vector3(width * 0.51, 0.82, -length * 0.30 + float(i) * length * 0.10)))
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.42, 0.16, 0.24)), accent_mat,
            Vector3(0.0, body_y + 0.96, 0.0)))
    if type_id == "police":
        for side in [-1, 1]:
            root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.025, 0.22, length * 0.70)), accent_mat,
                Vector3(float(side) * width * 0.51, 0.70, 0.0)))
        var red := AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.24, 0.12, 0.18)),
            AGPalette.mat("#D53A34", true), Vector3(-0.14, body_y + 1.02, 0.0))
        var blue := AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.24, 0.12, 0.18)),
            AGPalette.mat("#3D6DD8", true), Vector3(0.14, body_y + 1.02, 0.0))
        root.add_child(red)
        root.add_child(blue)
        root.beacon_red = red
        root.beacon_blue = blue
        blue.visible = false

static func _build_bus(root: AGVehicleView, type_id: String, length: float, width: float, height: float,
        body_mat: Material, accent_mat: Material, dark_mat: Material, glass_mat: Material,
        tire_mat: Material, rim_mat: Material, lamp_mat: Material, tail_mat: Material) -> void:
    var body_y := height * 0.48
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width, height * 0.88, length)), body_mat,
        Vector3(0.0, body_y, 0.0)))
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width * 0.92, 0.16, length * 0.96)), accent_mat,
        Vector3(0.0, 0.76, 0.0)))
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width * 0.80, height * 0.38, 0.06)), glass_mat,
        Vector3(0.0, body_y + 0.38, -length * 0.50)))
    for side in [-1, 1]:
        for i in range(4 if type_id == "microbus" else 6):
            var z := -length * 0.36 + float(i) * length * 0.15
            root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.035, height * 0.30, length * 0.11)), glass_mat,
                Vector3(float(side) * width * 0.505, body_y + 0.32, z)))
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.13, 0.12, 0.07)), lamp_mat,
            Vector3(float(side) * width * 0.32, body_y - 0.25, -length * 0.51)))
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.13, 0.12, 0.07)), tail_mat,
            Vector3(float(side) * width * 0.32, body_y - 0.25, length * 0.51)))
    _add_wheels(root, [
        Vector3(-width * 0.54, 0.40, -length * 0.34), Vector3(width * 0.54, 0.40, -length * 0.34),
        Vector3(-width * 0.54, 0.40, length * 0.34), Vector3(width * 0.54, 0.40, length * 0.34),
    ], 0.40, tire_mat, rim_mat)

static func _build_truck(root: AGVehicleView, type_id: String, length: float, width: float, height: float,
        body_mat: Material, accent_mat: Material, dark_mat: Material, glass_mat: Material,
        tire_mat: Material, rim_mat: Material, lamp_mat: Material, tail_mat: Material) -> void:
    var cab_length := 2.5
    var cargo_length := length - cab_length - 0.3
    var cargo_z := cab_length * 0.5 + cargo_length * 0.5
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width, 0.55, length)), dark_mat,
        Vector3(0.0, 0.60, 0.0)))
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width * 0.94, height * 0.72, cab_length)), accent_mat,
        Vector3(0.0, 1.45, -length * 0.5 + cab_length * 0.5)))
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width * 0.86, height * 0.76, cargo_length)), body_mat,
        Vector3(0.0, 1.72, cargo_z)))
    root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width * 0.78, 0.32, 0.05)), glass_mat,
        Vector3(0.0, 1.75, -length * 0.5 + 0.04)))
    for side in [-1, 1]:
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.025, height * 0.50, cargo_length * 0.82)), accent_mat,
            Vector3(float(side) * width * 0.485, 1.78, cargo_z)))
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.16, 0.12, 0.08)), lamp_mat,
            Vector3(float(side) * width * 0.33, 0.85, -length * 0.50)))
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.16, 0.12, 0.08)), tail_mat,
            Vector3(float(side) * width * 0.33, 0.85, length * 0.50)))
    var axle_z := [-length * 0.38, -length * 0.10, length * 0.28, length * 0.42]
    var wheel_positions := []
    for z in axle_z:
        wheel_positions.append(Vector3(-width * 0.56, 0.44, float(z)))
        wheel_positions.append(Vector3(width * 0.56, 0.44, float(z)))
    _add_wheels(root, wheel_positions, 0.44, tire_mat, rim_mat)
    if type_id == "trailer":
        root.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(width * 0.80, 0.10, cargo_length * 0.90)),
            AGPalette.mat("#7E3B32"), Vector3(0.0, 2.10, cargo_z)))
