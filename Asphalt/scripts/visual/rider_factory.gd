extends RefCounted
class_name AGRiderFactory
## Builds eight distinct street riders from a shared articulated low-poly rig.

static func build(def: Dictionary) -> AGRiderView:
    var root := AGRiderView.new()
    root.name = "RiderView"
    root.set_meta("rider_id", String(def.get("id", "rider")))
    root.scale = Vector3(float(def.get("build", 1.0)), float(def.get("height", 1.78)) / 1.78, float(def.get("build", 1.0)))

    var skin_mat := AGPalette.mat(String(def.get("skin", "#A9764B")))
    var shirt_mat := AGPalette.mat(String(def.get("shirt", "#C32228")))
    var jacket_mat := AGPalette.mat(String(def.get("jacket", "#8B1F25")))
    var pants_mat := AGPalette.mat(String(def.get("pants", "#344C78")))
    var shoes_mat := AGPalette.mat(String(def.get("shoes", "#E5E2D2")))
    var hair_mat := AGPalette.mat(String(def.get("hair", "#171318")))
    var accent_mat := AGPalette.mat(String(def.get("accent", "#D9B51F")))
    var dark_mat := AGPalette.mat("#202026")
    var metal_mat := AGPalette.mat("#B7B4A8")

    var hips := Node3D.new()
    hips.name = "Hips"
    root.add_child(hips)
    var torso := Node3D.new()
    torso.name = "Torso"
    torso.position = Vector3(0.0, 0.30, 0.0)
    hips.add_child(torso)

    # Tapered torso with a visible shirt front and two jacket side panels.
    torso.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.24, 0.62, 6, 0.31), shirt_mat, Vector3.ZERO))
    for side in [-1, 1]:
        torso.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.10, 0.60, 0.22)), jacket_mat,
            Vector3(float(side) * 0.22, 0.0, 0.0), Vector3(0, 0, float(side) * -4.0)))
    torso.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.34, 0.06, 0.20)), accent_mat,
        Vector3(0.0, 0.25, -0.10)))
    torso.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.48, 0.07, 0.20)), dark_mat,
        Vector3(0.0, -0.28, 0.0)))

    # Head with readable eyebrows, eyes, nose and mouth.
    var head := Node3D.new()
    head.name = "Head"
    head.position = Vector3(0.0, 0.52, -0.02)
    torso.add_child(head)
    head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.sphere(0.20, 8, 5), skin_mat, Vector3.ZERO))
    head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.04, 0.035, 0.03)), dark_mat,
        Vector3(-0.07, 0.03, -0.19)))
    head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.04, 0.035, 0.03)), dark_mat,
        Vector3(0.07, 0.03, -0.19)))
    head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.10, 0.018, 0.02)), hair_mat,
        Vector3(-0.07, 0.09, -0.188)))
    head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.10, 0.018, 0.02)), hair_mat,
        Vector3(0.07, 0.09, -0.188)))
    head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.035, 0.06, 0.07)), skin_mat,
        Vector3(0.0, -0.01, -0.21)))
    head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.09, 0.015, 0.02)), dark_mat,
        Vector3(0.0, -0.09, -0.19)))
    _build_hair(head, String(def.get("hair_style", "spikes")), hair_mat, accent_mat, dark_mat)

    # Arms: pivots at the shoulders, bent forward toward the handlebars.
    var left_arm := Node3D.new()
    left_arm.name = "LeftArm"
    left_arm.position = Vector3(-0.30, 0.24, 0.0)
    torso.add_child(left_arm)
    var right_arm := Node3D.new()
    right_arm.name = "RightArm"
    right_arm.position = Vector3(0.30, 0.24, 0.0)
    torso.add_child(right_arm)
    _build_arm(left_arm, -1.0, jacket_mat, shirt_mat, skin_mat)
    _build_arm(right_arm, 1.0, jacket_mat, shirt_mat, skin_mat)

    # Legs: bent knees and high-top shoes on the footrests.
    var left_leg := Node3D.new()
    left_leg.name = "LeftLeg"
    left_leg.position = Vector3(-0.16, -0.03, 0.02)
    hips.add_child(left_leg)
    var right_leg := Node3D.new()
    right_leg.name = "RightLeg"
    right_leg.position = Vector3(0.16, -0.03, 0.02)
    hips.add_child(right_leg)
    _build_leg(left_leg, -1.0, pants_mat, shoes_mat, accent_mat, String(def.get("accessory", "")) == "knee_pads")
    _build_leg(right_leg, 1.0, pants_mat, shoes_mat, accent_mat, String(def.get("accessory", "")) == "knee_pads")

    _build_accessory(torso, head, String(def.get("accessory", "")), accent_mat, dark_mat, metal_mat)
    root.configure({
        "hips": hips, "torso": torso, "head": head,
        "left_arm": left_arm, "right_arm": right_arm,
        "left_leg": left_leg, "right_leg": right_leg,
    })
    return root

static func _build_arm(pivot: Node3D, side: float, jacket_mat: Material, shirt_mat: Material, skin_mat: Material) -> void:
    var shoulder := Vector3(0.0, 0.0, 0.0)
    var elbow := Vector3(side * 0.11, -0.24, -0.25)
    var hand := Vector3(side * 0.10, -0.34, -0.58)
    pivot.add_child(AGMeshFactory.tube_between(shoulder, elbow, 0.075, jacket_mat, 6))
    pivot.add_child(AGMeshFactory.tube_between(elbow, hand, 0.060, shirt_mat, 6))
    pivot.add_child(AGMeshFactory.mesh_node(AGMeshFactory.sphere(0.075, 6, 4), skin_mat, hand))

static func _build_leg(pivot: Node3D, side: float, pants_mat: Material, shoes_mat: Material,
        accent_mat: Material, knee_pads: bool) -> void:
    var hip := Vector3.ZERO
    var knee := Vector3(side * 0.08, -0.28, -0.18)
    var foot := Vector3(side * 0.11, -0.53, -0.28)
    pivot.add_child(AGMeshFactory.tube_between(hip, knee, 0.095, pants_mat, 6))
    pivot.add_child(AGMeshFactory.tube_between(knee, foot, 0.075, pants_mat, 6))
    pivot.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.14, 0.09, 0.24)), shoes_mat,
        foot + Vector3(0.0, -0.02, -0.05)))
    if knee_pads:
        pivot.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.16, 0.11, 0.10)), accent_mat, knee))

static func _build_hair(head: Node3D, style: String, hair_mat: Material,
        accent_mat: Material, dark_mat: Material) -> void:
    if style == "flattop":
        head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.40, 0.16, 0.38)), hair_mat,
            Vector3(0.0, 0.19, 0.0)))
    elif style == "mohawk":
        for i in range(5):
            var z := -0.15 + float(i) * 0.075
            var cone := AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.06, 0.22, 5, 0.0), hair_mat,
                Vector3(0.0, 0.23, z))
            head.add_child(cone)
    elif style == "ponytail":
        head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.sphere(0.21, 8, 4), hair_mat,
            Vector3(0.0, 0.10, 0.02), Vector3.ZERO, Vector3(1.0, 0.70, 1.0)))
        head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.075, 0.36, 6, 0.02), hair_mat,
            Vector3(0.0, 0.04, 0.27), Vector3(62, 0, 0)))
        head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.34, 0.04, 0.04)), accent_mat,
            Vector3(0.0, 0.14, -0.16)))
    elif style == "undercut":
        head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.42, 0.13, 0.36)), hair_mat,
            Vector3(0.0, 0.17, 0.01)))
        head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.43, 0.035, 0.38)), accent_mat,
            Vector3(0.0, 0.10, 0.01)))
    elif style == "curly":
        for i in range(9):
            var angle := float(i) * TAU / 9.0
            head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.sphere(0.09, 6, 4), hair_mat,
                Vector3(cos(angle) * 0.18, 0.15 + sin(float(i) * 1.7) * 0.04, sin(angle) * 0.16)))
    elif style == "cap":
        head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.sphere(0.21, 8, 4), dark_mat,
            Vector3(0.0, 0.13, 0.0), Vector3.ZERO, Vector3(1.0, 0.55, 1.0)))
        head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.34, 0.035, 0.22)), dark_mat,
            Vector3(0.0, 0.15, -0.24)))
    elif style == "wild_spikes":
        for i in range(7):
            var x := -0.18 + float(i) * 0.06
            var h := 0.18 + (0.12 if i % 2 == 0 else 0.04)
            head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.055, h, 5, 0.0), hair_mat,
                Vector3(x, 0.17, sin(float(i) * 2.1) * 0.10), Vector3(sin(float(i)) * 16.0, 0, cos(float(i)) * 12.0)))
    else:  # spikes
        for i in range(6):
            var x := -0.16 + float(i) * 0.064
            head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.055, 0.18, 5, 0.0), hair_mat,
                Vector3(x, 0.19, sin(float(i) * 1.5) * 0.08), Vector3(0, 0, (float(i) - 2.5) * 7.0)))

static func _build_accessory(torso: Node3D, head: Node3D, accessory: String,
        accent_mat: Material, dark_mat: Material, metal_mat: Material) -> void:
    if accessory == "crossbody_bag":
        torso.add_child(AGMeshFactory.tube_between(Vector3(-0.26, 0.25, -0.05),
            Vector3(0.23, -0.28, -0.16), 0.035, dark_mat, 5))
        torso.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.20, 0.24, 0.12)), dark_mat,
            Vector3(0.20, -0.30, -0.10)))
    elif accessory == "sunglasses":
        head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.13, 0.055, 0.025)), dark_mat,
            Vector3(-0.08, 0.035, -0.205)))
        head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.13, 0.055, 0.025)), dark_mat,
            Vector3(0.08, 0.035, -0.205)))
        head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.045, 0.015, 0.02)), dark_mat,
            Vector3(0.0, 0.035, -0.21)))
    elif accessory == "helmet_half":
        head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.sphere(0.22, 8, 4), accent_mat,
            Vector3(0.0, 0.10, 0.0), Vector3.ZERO, Vector3(1.0, 0.65, 1.0)))
        head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.32, 0.045, 0.05)), dark_mat,
            Vector3(0.0, 0.035, -0.22)))
    elif accessory == "bandana":
        head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.42, 0.065, 0.39)), accent_mat,
            Vector3(0.0, 0.13, 0.0)))
        head.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.16, 0.06, 0.05)), accent_mat,
            Vector3(0.22, 0.10, 0.13), Vector3(0, -20, 0)))
    elif accessory == "chain":
        for i in range(5):
            torso.add_child(AGMeshFactory.mesh_node(AGMeshFactory.cylinder(0.022, 0.018, 6), metal_mat,
                Vector3(-0.10 + float(i) * 0.05, 0.19 - absf(float(i) - 2.0) * 0.025, -0.18), Vector3(0, 0, 90)))
    elif accessory == "backpack":
        torso.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.36, 0.42, 0.20)), dark_mat,
            Vector3(0.0, -0.02, 0.20)))
        torso.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.24, 0.05, 0.03)), accent_mat,
            Vector3(0.0, 0.07, 0.31)))
    elif accessory == "scarf":
        torso.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.38, 0.10, 0.28)), accent_mat,
            Vector3(0.0, 0.27, -0.02)))
        torso.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.10, 0.28, 0.06)), accent_mat,
            Vector3(0.20, 0.12, 0.12), Vector3(0, 0, -18)))
    elif accessory == "knee_pads":
        torso.add_child(AGMeshFactory.mesh_node(AGMeshFactory.box(Vector3(0.12, 0.05, 0.03)), accent_mat,
            Vector3(-0.12, -0.10, -0.18)))
