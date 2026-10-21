extends "res://prototypes/vp0/vp0_stage.gd"
## VP-0 prototype C: a corner of Anvil Cay (24 px/m): beach, rocks, palms, a cobbled quay, period buildings, a pier and a moored sloop.
## args: shot=street|harbour|beach  look=day|golden|dusk|night.   Keys: Z / X / C = street / harbour / beach.
const SHIP := preload("res://prototypes/vp0/vp0_ship.gd")

const SHOTS := {
	"street": Vector3(2.0, 0.0, -12.0),
	"harbour": Vector3(3.0, 0.0, 5.0),
	"beach": Vector3(-14.0, 0.0, 2.0),
}
var ocean: ShaderMaterial
var meta: Dictionary = {}
var windows: Array = []


func _build() -> void:
	ppm = 24.0
	pitch_deg = float(args.get("pitch", 37.0))
	meta = _json("res://art/vp0/world/cay_world.json")
	var rect: Array = meta["depth_rect"]
	var bed := U.tex(U.ART + "ground/ground_atlas.png")
	ocean = make_ocean(U.ART + "world/cay_depth.png", rect, meta["depth_range"], 2.0, bed)
	U.add_plane(world, Vector3(0, 0, 0), Vector2(180, 180), ocean, -2)
	var cells: Array = meta["cells"]
	var org: Array = meta["origin"]
	var tm := make_terrain(U.ART + "world/cay_cells.png", Vector2(org[0], org[1]), Vector2i(cells[0], cells[1]), 2.0)
	U.add_plane(world, Vector3(float(org[0]) + cells[0] * 0.5, 0.0, float(org[1]) + cells[1] * 0.5 - 40.0), Vector2(220, 160), tm, -1)
	_terrace()
	_props()
	var ship := SHIP.build(self, world, 180.0)
	ship.position = Vector3(3.5, 0.0, 13.0)
	for m in clip_mats:
		(m as ShaderMaterial).set_shader_parameter("clip", Vector4(3.5, 13.0, -1.0, 0.0))
	ocean.set_shader_parameter("ship_pos", Vector2(3.5, 13.0))
	ocean.set_shader_parameter("ship_fwd", Vector2(-1.0, 0.0))
	ocean.set_shader_parameter("ship_speed", 0.0)
	var shot := String(args.get("shot", "street"))
	ship.visible = shot == "harbour"
	set_cam(args["cam"] if false else SHOTS.get(shot, SHOTS["street"]))
	if args.has("cam"):
		var p := String(args["cam"]).split(",")
		set_cam(Vector3(float(p[0]), 0.0, float(p[1])))


func _terrace() -> void:
	var t: Dictionary = meta["terrace"]
	var x0 := float(t["x0"])
	var x1 := float(t["x1"])
	var z0 := float(t["z0"])
	var z1 := float(t["z1"])
	var h := float(t["h"])
	var top := U.MeshBuilder.new()
	var wall := U.MeshBuilder.new()
	top.quad(Vector3(x0, h, z1), Vector3(x1, h, z1), Vector3(x1, h, z0), Vector3(x0, h, z0), Vector2(x0 / 2, z1 / 2), Vector2(x1 / 2, z1 / 2), Vector2(x1 / 2, z0 / 2), Vector2(x0 / 2, z0 / 2))
	wall.quad(Vector3(x0, 0, z1), Vector3(x1, 0, z1), Vector3(x1, h, z1), Vector3(x0, h, z1), Vector2(x0 / 2, 0), Vector2(x1 / 2, 0), Vector2(x1 / 2, h / 2), Vector2(x0 / 2, h / 2))
	wall.quad(Vector3(x0, 0, z0), Vector3(x0, 0, z1), Vector3(x0, h, z1), Vector3(x0, h, z0), Vector2(0, 0), Vector2(3, 0), Vector2(3, h / 2), Vector2(0, h / 2))
	var tm := MeshInstance3D.new()
	tm.mesh = top.build()
	tm.material_override = make_cel(atlas_tile(2, 1), Color(1.3, 1.3, 1.2))
	tm.extra_cull_margin = 30.0
	world.add_child(tm)
	var wm := MeshInstance3D.new()
	wm.mesh = wall.build()
	wm.material_override = make_cel(atlas_tile(7, 0), Color(0.95, 0.9, 0.88))
	wm.extra_cull_margin = 30.0
	world.add_child(wm)


func _spr(group: String, sname: String, x: float, z: float, phi := 0.0, y := 0.0, shadow := true) -> void:
	U.add_sprite(self, world, group, sname, Vector3(x, y, z), phi, shadow)


func _props() -> void:
	# buildings along the north side of the road (fronts face the camera: south)
	_spr("island", "house_a", -18.0, -8.5)
	_spr("island", "warehouse", -5.0, -8.5)
	_spr("island", "house_b", 3.5, -8.8)
	_spr("island", "house_b", 15.0, -13.2, 0.0, 1.6)
	_spr("island", "house_a", 24.0, -13.6, 0.0, 1.6)
	# window glow positions (house_a: x -1.62 / +1.54 m, h 1.83 m, 2.17 m toward the viewer)
	_window(-18.0, -8.5, -1.62, 1.83, 2.17, 0.0)
	_window(-18.0, -8.5, 1.54, 1.83, 2.17, 0.0)
	_window(24.0, -13.6, -1.62, 1.83, 2.17, 1.6)
	_window(24.0, -13.6, 1.54, 1.83, 2.17, 1.6)
	# street furniture
	for x in [-3.2, 4.4, 11.0]:
		_spr("island", "lamp_post", x, -2.2)
		U.add_halo(self, world, Vector3(x + 0.33, 4.08, -2.2), 2.0, Color(1.0, 0.62, 0.22), 1.0, x)
	_spr("island", "signpost", -9.5, -3.0)
	for x in [-3.5, 0.5, 6.5, 10.5]:
		_spr("ship", "bollard", x, 0.55)
	_spr("ship", "barrel", 3.3, -1.0)
	_spr("ship", "barrel_fish", 4.1, -1.4)
	_spr("ship", "crate", 5.0, -0.9, 10.0)
	_spr("ship", "crate", 5.1, -0.9, 10.0, 1.0 * 22.0 / 24.0)
	_spr("ship", "barrel", -1.8, -1.5)
	_spr("ship", "pirate", 0.2, -2.6, -80.0)
	_spr("ship", "pirate", -7.6, -3.8, 200.0)
	# pier from the quay (z 1) south: 6 m long, planked
	_spr("island", "pier_y_6", 8.5, 4.0)
	# beach: palms, bushes, rocks
	for p in [Vector2(-15.0, 1.2), Vector2(-12.4, -0.9), Vector2(-17.6, 3.4), Vector2(-9.4, -0.6)]:
		_spr("island", "palm_a" if int(absf(p.x)) % 2 == 0 else "palm_c", p.x, p.y)
	_spr("island", "palm_b", -21.0, -2.6)
	_spr("island", "bush_a", -22.0, -4.2)
	_spr("island", "bush_b", -10.8, -4.4)
	_spr("island", "bush_a", -14.0, -4.0)
	_spr("island", "rock_a", -26.3, 0.6)
	_spr("island", "rock_c", -27.6, 3.6)
	_spr("island", "rock_b", -23.8, 5.4)
	_spr("island", "rock_c", -15.3, 8.7)
	_spr("island", "rock_a", -13.9, 10.6)
	_spr("island", "rock_b", 16.6, 8.2)
	_spr("island", "palm_c", 17.6, 1.8)
	_spr("island", "palm_a", 21.5, 2.4)
	_spr("island", "rock_a", 22.0, 10.0)
	_spr("island", "bush_b", 27.0, -4.5)
	_spr("island", "palm_b", 12.2, -10.6, 0.0, 1.6)
	_spr("island", "bush_a", 20.5, -10.8, 0.0, 1.6)


func _window(x: float, z: float, dx: float, h: float, dz: float, y0: float) -> void:
	U.add_halo(self, world, Vector3(x + dx, y0 + h, z + dz), 1.3, Color(1.0, 0.7, 0.3), 0.7, x + dx)


func _json(p: String) -> Dictionary:
	if not FileAccess.file_exists(p):
		return {}
	var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(p))
	return d as Dictionary if d is Dictionary else {}


func _unhandled_input(ev: InputEvent) -> void:
	super(ev)
	var k := ev as InputEventKey
	if k == null or not k.pressed or k.echo:
		return
	match k.keycode:
		KEY_Z: set_cam(SHOTS["street"])
		KEY_X: set_cam(SHOTS["harbour"])
		KEY_C: set_cam(SHOTS["beach"])
