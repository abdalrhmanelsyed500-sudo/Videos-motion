extends "res://prototypes/vp0/vp0_stage.gd"
## VP-0 prototype B: the open sea at 8 px/m (the sailing tier). One sloop under way, a second far off, an island with LOD sprites.
## args: heading=70 (degrees clockwise from north)  look=...   Keys: A/D turn the demo ship, [ ] ; ' pan.
const HULL_FRAMES := 16

var ocean: ShaderMaterial
var heading := 70.0
var ship_pos := Vector2(0, 2)
var ship_mi: MeshInstance3D
var _frame := -1


func _build() -> void:
	ppm = 8.0
	pitch_deg = float(args.get("pitch", 48.0))
	heading = float(args.get("heading", 70.0))
	var meta := _json("res://art/vp0/world/sea_world.json")
	var bed := U.tex(U.ART + "ground/ground_atlas.png")
	ocean = make_ocean(U.ART + "world/sea_depth.png", meta["depth_rect"], meta["depth_range"], 6.0, bed)
	U.add_plane(world, Vector3(0, 0, 0), Vector2(400, 400), ocean, -2)
	var cells: Array = meta["cells"]
	var org: Array = meta["origin"]
	var tm := make_terrain(U.ART + "world/sea_cells.png", Vector2(org[0], org[1]), Vector2i(cells[0], cells[1]), 6.0)
	U.add_plane(world, Vector3(float(org[0]) + cells[0] * 0.5, 0.0, float(org[1]) + cells[1] * 0.5), Vector2(cells[0], cells[1]), tm, -1)
	_island_sprites(U.tex(U.ART + "world/sea_cells.png").get_image(), org)
	_place_ship()
	# a second, distant sloop on another heading (the sea is never empty)
	var far := U.add_sprite(self, world, "hull", "sloop_sea", Vector3(-26.0, 0.0, -22.0), 0.0, false, 0.0, 0.0, 3)
	far.set_meta("far", true)
	set_cam(Vector3(12.0, 0.0, -4.0))


func _place_ship() -> void:
	var f := int(roundf(fposmod(heading, 360.0) / 22.5)) % HULL_FRAMES
	if f == _frame:
		return
	_frame = f
	if ship_mi != null:
		ship_mi.queue_free()
	ship_mi = U.add_sprite(self, world, "hull", "sloop_sea", Vector3(ship_pos.x, 0.0, ship_pos.y), 0.0, false, 0.0, 0.0, f)
	var h := deg_to_rad(heading)
	ocean.set_shader_parameter("ship_pos", ship_pos)
	ocean.set_shader_parameter("ship_fwd", Vector2(sin(h), -cos(h)))
	ocean.set_shader_parameter("ship_speed", 0.7)
	set_look(look_name)


func _island_sprites(img: Image, org: Array) -> void:
	var n := 0
	for y in range(2, img.get_height() - 2, 2):
		for x in range(2, img.get_width() - 2, 2):
			var t := int(roundf(img.get_pixel(x, y).r * 255.0))
			if t == 255:
				continue
			var hsh := (x * 73856093) ^ (y * 19349663)
			var r := float(absi(hsh) % 1000) / 1000.0
			var wx := float(org[0]) + float(x) + 0.5
			var wz := float(org[1]) + float(y) + 0.5
			if t == 7 and r < 0.20:
				U.add_sprite(self, world, "lod8", "rock_c" if r < 0.08 else "rock_a", Vector3(wx, 0, wz))
			elif (t == 2 or t == 0) and r < 0.05 and int(roundf(img.get_pixel(x + 2, y).r * 255.0)) != 255 and int(roundf(img.get_pixel(x - 2, y).r * 255.0)) != 255:
				U.add_sprite(self, world, "lod8", "palm_a" if r < 0.025 else "palm_c", Vector3(wx, 0, wz))
				n += 1
			elif t == 2 and r > 0.93:
				U.add_sprite(self, world, "lod8", "bush_a", Vector3(wx, 0, wz))


func _json(p: String) -> Dictionary:
	if not FileAccess.file_exists(p):
		return {}
	var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(p))
	return d as Dictionary if d is Dictionary else {}


func _unhandled_input(ev: InputEvent) -> void:
	super(ev)
	var k := ev as InputEventKey
	if k == null or not k.pressed:
		return
	match k.keycode:
		KEY_A:
			heading -= 22.5
			_place_ship()
		KEY_D:
			heading += 22.5
			_place_ship()
