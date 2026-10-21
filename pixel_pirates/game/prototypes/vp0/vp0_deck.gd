extends "res://prototypes/vp0/vp0_stage.gd"
## VP-0 prototype A: the sloop at deck scale (24 px/m) on open water. args: yaw=0  look=day|golden|dusk|night
const SHIP := preload("res://prototypes/vp0/vp0_ship.gd")

var ship: Node3D
var ocean: ShaderMaterial
var yaw := 0.0


func _build() -> void:
	ppm = 24.0
	pitch_deg = float(args.get("pitch", 37.0))
	yaw = float(args.get("yaw", 0.0))
	var meta := _json("res://art/vp0/world/sea_world.json")
	var rect: Array = meta.get("depth_rect", [-120, -85, 240, 170])
	var rng: Array = meta.get("depth_range", [-4, 20])
	var bed := U.tex(U.ART + "ground/ground_atlas.png")
	ocean = make_ocean(U.ART + "world/sea_depth.png", rect, rng, 2.0, bed)
	# the deck scene sits in deep water: shift the sampling window so the whole screen is open sea
	ocean.set_shader_parameter("depth_rect", Vector4(rect[0], rect[1] + 60.0, rect[2], rect[3]))
	U.add_plane(world, Vector3(0, 0, 0), Vector2(160, 160), ocean, -2)
	ship = SHIP.build(self, world, yaw)
	var cy := cos(deg_to_rad(yaw))
	var sy := sin(deg_to_rad(yaw))
	for m in clip_mats:
		(m as ShaderMaterial).set_shader_parameter("clip", Vector4(0.0, 0.0, cy, sy))
	ocean.set_shader_parameter("ship_pos", Vector2(0, 0))
	ocean.set_shader_parameter("ship_fwd", Vector2(cy, -sy))
	ocean.set_shader_parameter("ship_half", Vector2(11.0, 3.1))
	ocean.set_shader_parameter("ship_speed", float(args.get("speed", 0.55)))
	set_cam(Vector3(1.5, 0.0, -7.3))
	if String(args.get("dbg", "0")) == "2":
		for p in [Vector3(1.5, 0, -7.3), Vector3(6.5, 0, -7.3), Vector3(1.5, 0, -2.3), Vector3(-3.5, 0, -7.3)]:
			var mi := MeshInstance3D.new()
			var bm := BoxMesh.new()
			bm.size = Vector3(1, 1, 1)
			mi.mesh = bm
			mi.position = p + Vector3(0, 0.5, 0)
			var sm := StandardMaterial3D.new()
			sm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			sm.albedo_color = Color(1, 0.2, 0.2) if p.x > 1.6 else (Color(0.2, 1, 0.2) if p.z > -7 else Color(1, 1, 0.2))
			mi.material_override = sm
			world.add_child(mi)
		ship.visible = false
		U.add_sprite(self, world, "ship", "barrel", Vector3(1.5, 0, -7.3), 0.0, false)


func _json(p: String) -> Dictionary:
	if not FileAccess.file_exists(p):
		return {}
	var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(p))
	return d as Dictionary if d is Dictionary else {}
