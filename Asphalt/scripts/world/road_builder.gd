extends RefCounted
class_name AGRoadBuilder
## Continuous road surface, markings, shoulders, barriers and collision.

static func build() -> Node3D:
    var root := Node3D.new()
    root.name = "RingRoad"

    var surface_tool := AGMeshFactory.begin_mesh()
    var z := AGRoadPath.START_Z
    while z > AGRoadPath.FINISH_Z:
        var z1 := maxf(z - AGRoadPath.SEGMENT_LENGTH, AGRoadPath.FINISH_Z)
        var c0 := AGRoadPath.center_x(z)
        var c1 := AGRoadPath.center_x(z1)
        var y0 := AGRoadPath.height_at(z)
        var y1 := AGRoadPath.height_at(z1)
        var v0 := Vector3(c0 - AGRoadPath.ROAD_HALF_WIDTH, y0, z)
        var v1 := Vector3(c0 + AGRoadPath.ROAD_HALF_WIDTH, y0, z)
        var v2 := Vector3(c1 + AGRoadPath.ROAD_HALF_WIDTH, y1, z1)
        var v3 := Vector3(c1 - AGRoadPath.ROAD_HALF_WIDTH, y1, z1)
        AGMeshFactory.add_quad(surface_tool, v0, v1, v2, v3,
            Vector2(0.0, -z / 8.0), Vector2(1.0, -z / 8.0),
            Vector2(1.0, -z1 / 8.0), Vector2(0.0, -z1 / 8.0))
        z = z1
    var road_mesh := AGMeshFactory.finish_mesh(surface_tool)
    var normal := first_triangle_normal(road_mesh)
    root.set_meta("road_surface_normal", normal)
    root.set_meta("road_mesh", road_mesh)
    if normal.y < 0.95:
        push_warning("Road surface normal is not upward: " + str(normal))

    var road_material := AGPalette.textured("#FFFFFF", "res://assets/textures/asphalt.png",
        Vector3(3.0, 1.0, 1.0), true)
    road_material.cull_mode = BaseMaterial3D.CULL_DISABLED
    var road_instance := AGMeshFactory.mesh_node(road_mesh, road_material)
    road_instance.name = "RoadSurface"
    root.add_child(road_instance)
    root.add_child(_shoulder_mesh())

    # Road collision is generated from the exact visible triangles.
    var road_body := StaticBody3D.new()
    road_body.name = "RoadCollision"
    var collision_shape := CollisionShape3D.new()
    var trimesh_shape := road_mesh.create_trimesh_shape()
    collision_shape.shape = trimesh_shape
    road_body.add_child(collision_shape)
    root.add_child(road_body)

    root.add_child(_marking_mesh())
    root.add_child(_barrier_meshes())
    root.add_child(_barrier_collision())
    root.add_child(_finish_line())
    return root

static func first_triangle_normal(mesh: ArrayMesh) -> Vector3:
    if mesh.get_surface_count() == 0:
        return Vector3.ZERO
    var arrays := mesh.surface_get_arrays(0)
    var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
    if vertices.size() < 3:
        return Vector3.ZERO
    return (vertices[1] - vertices[0]).cross(vertices[2] - vertices[0]).normalized()

static func _add_strip(st: SurfaceTool, z0: float, z1: float, offset: float,
        width: float, y_offset: float) -> void:
    var c0 := AGRoadPath.center_x(z0)
    var c1 := AGRoadPath.center_x(z1)
    var y0 := AGRoadPath.height_at(z0) + y_offset
    var y1 := AGRoadPath.height_at(z1) + y_offset
    var v0 := Vector3(c0 + offset, y0, z0)
    var v1 := Vector3(c0 + offset + width, y0, z0)
    var v2 := Vector3(c1 + offset + width, y1, z1)
    var v3 := Vector3(c1 + offset, y1, z1)
    AGMeshFactory.add_quad(st, v0, v1, v2, v3)

static func _marking_mesh() -> Node3D:
    var holder := Node3D.new()
    holder.name = "RoadMarkings"
    var yellow_st := AGMeshFactory.begin_mesh()
    var white_st := AGMeshFactory.begin_mesh()
    var z := AGRoadPath.START_Z
    while z > AGRoadPath.FINISH_Z:
        var z1 := maxf(z - AGRoadPath.SEGMENT_LENGTH, AGRoadPath.FINISH_Z)
        # Double yellow centerline and solid white edge lines.
        _add_strip(yellow_st, z, z1, -0.28, 0.11, 0.026)
        _add_strip(yellow_st, z, z1, 0.17, 0.11, 0.026)
        _add_strip(white_st, z, z1, -7.98, 0.12, 0.024)
        _add_strip(white_st, z, z1, 7.86, 0.12, 0.024)
        z = z1
    # Dashed lane lines at the two lane boundaries.
    var dash_z := AGRoadPath.START_Z
    while dash_z > AGRoadPath.FINISH_Z:
        var dash_end := maxf(dash_z - 8.0, AGRoadPath.FINISH_Z)
        _add_strip(white_st, dash_z, dash_end, -3.66, 0.12, 0.025)
        _add_strip(white_st, dash_z, dash_end, 3.54, 0.12, 0.025)
        dash_z -= 22.0
    # Pedestrian crossing bars at two junctions.
    for crossing_z in [-900.0, -2100.0, -3900.0]:
        for i in range(9):
            var x := -7.2 + float(i) * 1.8
            var c := AGRoadPath.center_x(crossing_z)
            var y := AGRoadPath.height_at(crossing_z) + 0.028
            var v0 := Vector3(c + x, y, crossing_z - 2.0)
            var v1 := Vector3(c + x + 0.75, y, crossing_z - 2.0)
            var v2 := Vector3(c + x + 0.75, y, crossing_z + 2.0)
            var v3 := Vector3(c + x, y, crossing_z + 2.0)
            AGMeshFactory.add_quad(white_st, v0, v1, v2, v3)
    var yellow_mesh := AGMeshFactory.finish_mesh(yellow_st)
    var white_mesh := AGMeshFactory.finish_mesh(white_st)
    var yellow_material := AGPalette.mat("yellow", true)
    yellow_material.cull_mode = BaseMaterial3D.CULL_DISABLED
    yellow_material.render_priority = 2
    var white_material := AGPalette.mat("white", true)
    white_material.cull_mode = BaseMaterial3D.CULL_DISABLED
    white_material.render_priority = 2
    var yellow_instance := AGMeshFactory.mesh_node(yellow_mesh, yellow_material)
    yellow_instance.name = "YellowLines"
    var white_instance := AGMeshFactory.mesh_node(white_mesh, white_material)
    white_instance.name = "WhiteLines"
    holder.add_child(yellow_instance)
    holder.add_child(white_instance)
    return holder

static func _barrier_meshes() -> Node3D:
    var holder := Node3D.new()
    holder.name = "Barriers"
    var concrete_transforms: Array = []
    var rail_transforms: Array = []
    var post_transforms: Array = []
    var z := AGRoadPath.START_Z
    while z > AGRoadPath.FINISH_Z:
        var bridge := AGRoadPath.is_bridge(z)
        var yaw := AGRoadPath.yaw_at(z)
        var basis := Basis.IDENTITY.rotated(Vector3.UP, yaw)
        for side in [-1, 1]:
            var x := AGRoadPath.center_x(z) + float(side) * AGRoadPath.BARRIER_OFFSET
            var y := AGRoadPath.height_at(z)
            if bridge:
                for rail_y in [0.55, 1.05]:
                    rail_transforms.append(Transform3D(basis,
                        Vector3(x, y + float(rail_y), z)))
                post_transforms.append(Transform3D(basis, Vector3(x, y + 0.62, z)))
            else:
                concrete_transforms.append(Transform3D(basis, Vector3(x, y + 0.42, z)))
        z -= 4.4
    holder.add_child(_multimesh("ConcreteBarriers", Vector3(0.55, 0.84, 4.35),
        AGPalette.textured("concrete", "res://assets/textures/concrete.png"), concrete_transforms))
    holder.add_child(_multimesh("BridgeRails", Vector3(0.18, 0.13, 4.35),
        AGPalette.mat("white", true), rail_transforms))
    holder.add_child(_multimesh("BridgePosts", Vector3(0.22, 1.30, 0.22),
        AGPalette.mat("white", true), post_transforms))
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
    if transforms.is_empty():
        instance.visible = false
    return instance

static func _barrier_collision() -> StaticBody3D:
    var body := StaticBody3D.new()
    body.name = "BarrierCollision"
    var z := AGRoadPath.START_Z
    while z > AGRoadPath.FINISH_Z:
        var yaw := AGRoadPath.yaw_at(z)
        for side in [-1, 1]:
            var shape := BoxShape3D.new()
            shape.size = Vector3(1.0, 1.6, 52.0)
            var collision := CollisionShape3D.new()
            collision.shape = shape
            collision.position = Vector3(AGRoadPath.center_x(z) + float(side) * AGRoadPath.BARRIER_OFFSET,
                AGRoadPath.height_at(z) + 0.7, z)
            collision.rotation.y = yaw
            body.add_child(collision)
        z -= 48.0
    return body

static func _shoulder_mesh() -> Node3D:
    var holder := Node3D.new()
    holder.name = "SandShoulders"
    var st := AGMeshFactory.begin_mesh()
    var z := AGRoadPath.START_Z
    var inner := AGRoadPath.ROAD_HALF_WIDTH
    var outer := AGRoadPath.BARRIER_OFFSET + 45.0
    while z > AGRoadPath.FINISH_Z:
        var z1 := maxf(z - AGRoadPath.SEGMENT_LENGTH, AGRoadPath.FINISH_Z)
        var c0 := AGRoadPath.center_x(z)
        var c1 := AGRoadPath.center_x(z1)
        var y0 := AGRoadPath.height_at(z) + 0.012
        var y1 := AGRoadPath.height_at(z1) + 0.012
        var lv0 := Vector3(c0 - outer, y0, z)
        var lv1 := Vector3(c0 - inner, y0, z)
        var lv2 := Vector3(c1 - inner, y1, z1)
        var lv3 := Vector3(c1 - outer, y1, z1)
        AGMeshFactory.add_quad(st, lv0, lv1, lv2, lv3,
            Vector2(0.0, -z / 12.0), Vector2(1.0, -z / 12.0),
            Vector2(1.0, -z1 / 12.0), Vector2(0.0, -z1 / 12.0))
        var rv0 := Vector3(c0 + inner, y0, z)
        var rv1 := Vector3(c0 + outer, y0, z)
        var rv2 := Vector3(c1 + outer, y1, z1)
        var rv3 := Vector3(c1 + inner, y1, z1)
        AGMeshFactory.add_quad(st, rv0, rv1, rv2, rv3,
            Vector2(0.0, -z / 12.0), Vector2(1.0, -z / 12.0),
            Vector2(1.0, -z1 / 12.0), Vector2(0.0, -z1 / 12.0))
        z = z1
    var mesh := AGMeshFactory.finish_mesh(st)
    var material := AGPalette.textured("#FFFFFF", "res://assets/textures/sand.png",
        Vector3(10.0, 1.0, 1.0), true)
    var instance := AGMeshFactory.mesh_node(mesh, material)
    instance.name = "ShoulderSurface"
    holder.add_child(instance)
    return holder

static func _finish_line() -> MeshInstance3D:
    var z := AGRoadPath.FINISH_Z + 3.0
    var material := AGPalette.textured("white", "res://assets/textures/checker.png",
        Vector3(10.0, 1.0, 1.0), true)
    material.cull_mode = BaseMaterial3D.CULL_DISABLED
    material.render_priority = 2
    var line := AGMeshFactory.mesh_node(AGMeshFactory.quad(Vector2(AGRoadPath.ROAD_WIDTH, 3.0)),
        material, Vector3(AGRoadPath.center_x(z), AGRoadPath.height_at(z) + 0.045, z),
        Vector3(-90, 0, 0))
    line.name = "FinishLine"
    return line
