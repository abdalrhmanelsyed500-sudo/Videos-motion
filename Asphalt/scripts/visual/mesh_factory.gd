extends RefCounted
class_name AGMeshFactory
## Reusable primitive construction helpers. Models are assembled from many
## shaped parts; no single primitive is presented as a finished vehicle.

static func mesh_node(mesh: Mesh, material: Material, pos := Vector3.ZERO,
        rotation_degrees_value := Vector3.ZERO, scale_value := Vector3.ONE) -> MeshInstance3D:
    var node := MeshInstance3D.new()
    node.mesh = mesh
    node.material_override = material
    node.position = pos
    node.rotation_degrees = rotation_degrees_value
    node.scale = scale_value
    return node

static func box(size: Vector3) -> BoxMesh:
    var mesh := BoxMesh.new()
    mesh.size = size
    return mesh

static func cylinder(radius: float, height: float, segments := 8,
        top_radius := -1.0) -> CylinderMesh:
    var mesh := CylinderMesh.new()
    mesh.top_radius = radius if top_radius < 0.0 else top_radius
    mesh.bottom_radius = radius
    mesh.height = height
    mesh.radial_segments = segments
    mesh.rings = 1
    return mesh

static func sphere(radius: float, segments := 8, rings := 5) -> SphereMesh:
    var mesh := SphereMesh.new()
    mesh.radius = radius
    mesh.height = radius * 2.0
    mesh.radial_segments = segments
    mesh.rings = rings
    return mesh

static func torus(inner_radius: float, outer_radius: float,
        ring_segments := 12, rings := 6) -> TorusMesh:
    var mesh := TorusMesh.new()
    mesh.inner_radius = inner_radius
    mesh.outer_radius = outer_radius
    mesh.ring_segments = ring_segments
    mesh.rings = rings
    return mesh

static func quad(size: Vector2) -> QuadMesh:
    var mesh := QuadMesh.new()
    mesh.size = size
    return mesh

static func tube_between(a: Vector3, b: Vector3, radius: float,
        material: Material, segments := 6) -> MeshInstance3D:
    var direction := b - a
    var node := mesh_node(cylinder(radius, direction.length(), segments), material,
        (a + b) * 0.5)
    if direction.length_squared() > 0.000001:
        node.quaternion = Quaternion(Vector3.UP, direction.normalized())
    return node

static func begin_mesh() -> SurfaceTool:
    var st := SurfaceTool.new()
    st.begin(Mesh.PRIMITIVE_TRIANGLES)
    return st

static func add_quad(st: SurfaceTool, v0: Vector3, v1: Vector3, v2: Vector3, v3: Vector3,
        uv0 := Vector2.ZERO, uv1 := Vector2.RIGHT, uv2 := Vector2.ONE,
        uv3 := Vector2.DOWN) -> void:
    st.set_uv(uv0)
    st.add_vertex(v0)
    st.set_uv(uv1)
    st.add_vertex(v1)
    st.set_uv(uv2)
    st.add_vertex(v2)
    st.set_uv(uv0)
    st.add_vertex(v0)
    st.set_uv(uv2)
    st.add_vertex(v2)
    st.set_uv(uv3)
    st.add_vertex(v3)

static func finish_mesh(st: SurfaceTool) -> ArrayMesh:
    st.generate_normals()
    var mesh := st.commit()
    return mesh as ArrayMesh
