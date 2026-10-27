extends RefCounted
class_name AGBikeFactory
## Builds six distinct low-poly motorcycles from shaped parts.

static func build(def: Dictionary) -> AGBikeView:
    var root := AGBikeView.new()
    root.name = "BikeView"
    root.set_meta("bike_id", String(def.get("id", "bike")))
    var body_color := String(def.get("body_color", "#B5252C"))
    var accent_color := String(def.get("accent_color", "#E1C84B"))
    var dark_color := String(def.get("dark_color", "#2B2930"))
    var body_mat := AGPalette.mat(body_color)
    var accent_mat := AGPalette.mat(accent_color)
    var dark_mat := AGPalette.mat(dark_color)
    var metal_mat := AGPalette.mat("#8C8D8A")
    var engine_mat := AGPalette.mat("#5C5D61")
    var tire_mat := AGPalette.mat("#1B1B20")
    var rim_mat := AGPalette.mat("#B7B4A8")
    var lamp_mat := AGPalette.mat("#F5DFA0", true)
    var tail_mat := AGPalette.mat("#D23A34", true)
    var wheel_radius := float(def.get("wheel_radius", 0.34))
    var custom := bool(def.get("custom", false))
    var fairing := bool(def.get("fairing", false))
    var high_bars := bool(def.get("high_bars", false))
    var exhaust_count := int(def.get("exhausts", 1))
    root.wheel_radius = wheel_radius

    var body := Node3D.new()
    body.name = "Body"
    root.add_child(body)
    root.body = body

    # Steel frame: four visible tubes, not a single primitive body.
    body.add_child(AGMeshFactory.tube_between(Vector3(0.0, 0.56, -0.72), Vector3(0.0, 0.55, 0.67), 0.035, dark_mat))
    body.add_child(AGMeshFactory.tube_between(Vector3(-0.20, 0.57, -0.68), Vector3(-0.22, 0.82, 0.40), 0.028, dark_mat))
    body.add_child(AGMeshFactory.tube_between(Vector3(0.20, 0.57, -0.68), Vector3(0.22, 0.82, 0.40), 0.028, dark_mat))
    body.add_child(AGMeshFactory.tube_between(Vector3(-0.22, 0.82, 0.40), Vector3(0.22, 0.82, 0.40), 0.032, dark_mat))

    # Engine block with coarse cooling fins.
    body.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.42, 0.34, 0.48)), engine_mat, Vector3(0.0, 0.63, 0.02)))
    for i in range(3):
        body.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.48, 0.035, 0.40)), metal_mat,
            Vector3(0.0, 0.52 + float(i) * 0.08, 0.02)))
    body.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.10, 0.30, 8), dark_mat,
        Vector3(0.0, 0.42, 0.10), Vector3(0, 0, 90)))

    # Fuel tank, stripe and seat.
    var tank := AGMeshFactory.mesh_node(AGMeshFactory.sphere(1.0, 8, 4), body_mat,
        Vector3(0.0, 1.02, -0.18), Vector3.ZERO, Vector3(0.34, 0.18, 0.50))
    tank.name = "Tank"
    body.add_child(tank)
    body.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.10, 0.025, 0.58)), accent_mat,
        Vector3(0.0, 1.19, -0.18)))
    body.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.42, 0.12, 0.58)), dark_mat,
        Vector3(0.0, 1.02, 0.39), Vector3(-3, 0, 0)))
    body.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.36, 0.14, 0.52)), body_mat,
        Vector3(0.0, 0.98, 0.76), Vector3(8, 0, 0)))

    # Side panels and footrests.
    for side in [-1, 1]:
        body.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.06, 0.28, 0.42)), body_mat,
            Vector3(float(side) * 0.25, 0.79, 0.18)))
        body.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.025, 0.24, 6), metal_mat,
            Vector3(float(side) * 0.30, 0.49, 0.28), Vector3(0, 0, 90)))

    # Steering head, forks, handlebars and front wheel.
    var steering := Node3D.new()
    steering.name = "Steering"
    steering.position = Vector3(0.0, 0.62, -0.82)
    body.add_child(steering)
    root.steering = steering
    var bar_height := 0.58 if high_bars else 0.44
    steering.add_child(AGMeshFactory.tube_between(Vector3(-0.18, 0.30, 0.0), Vector3(-0.18, wheel_radius - 0.62, 0.0), 0.035, metal_mat))
    steering.add_child(AGMeshFactory.tube_between(Vector3(0.18, 0.30, 0.0), Vector3(0.18, wheel_radius - 0.62, 0.0), 0.035, metal_mat))
    steering.add_child(AGMeshFactory.tube_between(Vector3(-0.18, 0.30, 0.0), Vector3(0.18, 0.30, 0.0), 0.035, dark_mat))
    if high_bars:
        steering.add_child(AGMeshFactory.tube_between(Vector3(-0.32, 0.42, 0.08), Vector3(-0.38, bar_height, 0.02), 0.028, dark_mat))
        steering.add_child(AGMeshFactory.tube_between(Vector3(0.32, 0.42, 0.08), Vector3(0.38, bar_height, 0.02), 0.028, dark_mat))
    steering.add_child(AGMeshFactory.tube_between(Vector3(-0.46, bar_height, 0.02), Vector3(0.46, bar_height, 0.02), 0.032, dark_mat))
    for side in [-1, 1]:
        steering.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.045, 0.16, 6), tire_mat,
            Vector3(float(side) * 0.39, bar_height, 0.02), Vector3(0, 0, 90)))
    var front_wheel := _make_wheel(wheel_radius, tire_mat, rim_mat, accent_mat)
    front_wheel.position = Vector3(0.0, wheel_radius - 0.62, 0.0)
    steering.add_child(front_wheel)
    root.front_wheel = front_wheel

    var rear_wheel := _make_wheel(wheel_radius, tire_mat, rim_mat, accent_mat)
    rear_wheel.position = Vector3(0.0, wheel_radius, 0.80)
    body.add_child(rear_wheel)
    root.rear_wheel = rear_wheel

    # Lights, exhausts and optional fairing.
    steering.add_child(AGMeshFactory.mesh_node(AGMeshFactory.sphere(1.0, 8, 4), lamp_mat,
        Vector3(0.0, 0.25, -0.20), Vector3.ZERO, Vector3(0.14, 0.14, 0.07)))
    body.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.22, 0.10, 0.06)), tail_mat,
        Vector3(0.0, 0.92, 1.02)))
    for i in range(exhaust_count):
        var side := -1.0 if i == 0 else 1.0
        var y := 0.50 + float(i) * 0.06
        body.add_child(AGMeshFactory.tube_between(Vector3(side * 0.18, y, 0.25),
            Vector3(side * 0.30, y - 0.06, 0.92), 0.055, metal_mat, 8))
        body.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.065, 0.12, 8), dark_mat,
            Vector3(side * 0.30, y - 0.06, 0.95), Vector3(90, 0, 0)))
    if fairing:
        var nose := AGMeshFactory.mesh_node(AGMeshFactory.sphere(1.0, 8, 4), body_mat,
            Vector3(0.0, 0.90, -0.85), Vector3.ZERO, Vector3(0.36, 0.30, 0.34))
        body.add_child(nose)
        for side in [-1, 1]:
            body.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.12, 0.10, 0.05)), lamp_mat,
                Vector3(float(side) * 0.16, 0.95, -1.15)))
        body.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.30, 0.05, 0.28)), accent_mat,
            Vector3(0.0, 1.13, -0.75), Vector3(-8, 0, 0)))
    if custom:
        body.add_child(AGMeshFactory.tube_between(Vector3(-0.28, 0.39, 0.72), Vector3(-0.28, 0.38, 1.05), 0.045, accent_mat))
        body.add_child(AGMeshFactory.tube_between(Vector3(0.28, 0.39, 0.72), Vector3(0.28, 0.38, 1.05), 0.045, accent_mat))
        body.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.44, 0.05, 0.55)), accent_mat,
            Vector3(0.0, 0.75, 0.92), Vector3(10, 0, 0)))

    var anchor := Node3D.new()
    anchor.name = "RiderAnchor"
    anchor.position = Vector3(0.0, 1.13, 0.30)
    body.add_child(anchor)
    root.rider_anchor = anchor
    return root

static func _make_wheel(radius: float, tire_mat: Material, rim_mat: Material, accent_mat: Material) -> Node3D:
    var pivot := Node3D.new()
    pivot.name = "WheelPivot"
    var tire := AGMeshFactory.mesh_node(AGMeshFactory.torus(radius * 0.70, radius, 12, 6), tire_mat,
        Vector3.ZERO, Vector3(0, 0, 90))
    pivot.add_child(tire)
    var rim := AGMeshFactory.mesh_node(AGMeshFactory.cylinder(radius * 0.47, 0.10, 10), rim_mat,
        Vector3.ZERO, Vector3(0, 0, 90))
    pivot.add_child(rim)
    var hub := AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.07, 0.16, 8), accent_mat,
        Vector3.ZERO, Vector3(0, 0, 90))
    pivot.add_child(hub)
    for i in range(6):
        var spoke := AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.025, radius * 1.32, 0.025)), rim_mat,
            Vector3.ZERO, Vector3(float(i) * 30.0, 0, 0))
        pivot.add_child(spoke)
    return pivot
