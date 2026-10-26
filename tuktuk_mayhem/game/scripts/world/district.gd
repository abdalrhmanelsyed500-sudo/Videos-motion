extends Node3D
## Mit Okba P1 district: builds every surface/building/prop from res://data/districts/*.json,
## owns mission ring polling, passenger lifecycle, destination arrow and reset logic.
## Typed-access note: actor nodes carry attached scripts, so cross-script calls go through
## call()/get()/connect() (GDScript cannot see attached-script members through a base type).
const MeshBuilder := preload("res://scripts/core/mesh_builder.gd")
const MaterialsLib := preload("res://scripts/core/materials.gd")

const RING_PICKUP_R := 6.0
const RING_DEST_R := 5.0

## Static collision for every visual surface (quad surfaces are render-only by design).
const COLLISION_BOXES := {
	"building_a": Vector3(9.0, 12.5, 11.0),
	"building_b": Vector3(10.0, 5.6, 8.0),
	"building_c": Vector3(6.0, 4.1, 5.5),
	"crate_stack": Vector3(0.9, 1.4, 0.9),
	"market_stall": Vector3(2.1, 1.9, 1.3),
	"lamp_post": Vector3(0.3, 5.0, 0.3),
	"speed_bump": Vector3(3.4, 0.14, 0.5),
	"parked_car": Vector3(1.8, 1.5, 4.2),
}

var tuktuk: Node3D
var cam: Node3D
var hud: Node3D
var passenger = null
var _cast_idx := -1
var _arrow: MeshInstance3D
var _arrow_t := 0.0
var _dest_marker := Vector3.ZERO
var _pickup_marker := Vector3.ZERO
var _offer_cooldown := 0.0
var _result_open := false
var _ramps: Array = []
var _ramp_cd: Array = []


func _ready() -> void:
	var d: Dictionary = Reg.district()
	_build_ground()
	_build_strips(d.get("roads", []), 0.03, "res://assets/textures/t_asphalt.png", 8.0)
	_build_strips(d.get("sidewalks", []), 0.16, "res://assets/textures/t_sidewalk.png", 3.0)
	for b in d.get("bumps", []):
		_add_mesh("speed_bump", b, 0.05)
	for b in d.get("buildings", []):
		_add_mesh(str(b.get("m", "building_a")), b, 0.16)
	for p in d.get("props", []):
		_add_mesh(str(p.get("m", "crate_stack")), p, 0.16)
	_dest_marker = Vector3(float(d["dest"]["x"]), 0, float(d["dest"]["z"]))
	_pickup_marker = Vector3(float(d["pickup"]["x"]), 0, float(d["pickup"]["z"]))
	_add_collision(d)
	_add_ramps(d.get("ramps", []))
	_add_shortcut_zone(d.get("shortcut", {}))
	_arrow = _make_arrow()
	tuktuk = get_node("Tuktuk")
	cam = get_node("ChaseCam")
	hud = get_node("HUD")
	cam.set("target", tuktuk)
	var st: Dictionary = d.get("start", {})
	if not st.is_empty():
		tuktuk.global_position = Vector3(float(st.get("x", 0)), 0.4, float(st.get("z", 60)))
		tuktuk.set("yaw", float(st.get("ry", 0)))
	if hud.has_method("bind_world"):
		hud.call("bind_world", self)
	tuktuk.connect("request_reset", _on_reset)
	tuktuk.connect("impacted", _on_impact)
	tuktuk.connect("landed", _on_impact)
	MissionMgr.mission_result.connect(_on_result)
	_spawn_passenger()


# ------------------------------------------------------------------ build helpers
func _quad(w: float, d: float, y: float, tex: String, tile_m: float) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(w, d)
	mi.mesh = q
	var m := StandardMaterial3D.new()
	m.albedo_color = Color.WHITE
	var tx: Texture2D = MaterialsLib.tex(tex)
	if tx != null:
		m.albedo_texture = tx
	m.uv1_scale = Vector3(maxf(w / tile_m, 0.25), maxf(d / tile_m, 0.25), 1)
	mi.material_override = m
	# QuadMesh is born in the XY plane (normal +Z): lay it flat, face up, or every road,
	# sidewalk and the ground itself renders as a vertical wall (P1 defect, found by the
	# Phase 2 render inspection).
	mi.rotation.x = -PI / 2.0
	mi.position.y = y
	return mi


func _build_ground() -> void:
	var g := _quad(460, 460, 0.0, "res://assets/textures/t_sidewalk.png", 24.0)
	g.name = "Ground"
	add_child(g)


func _build_strips(strips: Array, y: float, tex: String, tile_m: float) -> void:
	for s in strips:
		var mi := _quad(float(s.get("w", 8)), float(s.get("d", 8)), y, tex, tile_m)
		mi.position.x = float(s.get("cx", 0))
		mi.position.z = float(s.get("cz", 0))
		mi.rotation.y = float(s.get("ry", 0))
		add_child(mi)


func _add_mesh(spec: String, place: Dictionary, y: float) -> void:
	var mi := MeshInstance3D.new()
	mi.mesh = MeshBuilder.build(spec)
	var px: float = float(place.get("x", place.get("cx", 0)))
	var pz: float = float(place.get("z", place.get("cz", 0)))
	mi.position = Vector3(px, y, pz)
	mi.rotation.y = float(place.get("ry", 0))
	add_child(mi)
	MaterialsLib.apply_to(mi, MaterialsLib.lib(), _overrides_for(spec))


func _overrides_for(spec: String) -> Dictionary:
	if spec == "building_b":
		var band := StandardMaterial3D.new()
		band.albedo_texture = MaterialsLib.tex("res://assets/textures/t_sign_band.png")
		return {"sign": band}
	if spec == "ramp":
		var rm := StandardMaterial3D.new()
		rm.albedo_texture = MaterialsLib.tex("res://assets/textures/t_bump.png")
		return {"ramp": rm}
	if spec == "parked_car":
		var paint := StandardMaterial3D.new()
		paint.albedo_color = Color("3f5d78")
		paint.roughness = 0.55
		return {"carpaint": paint}
	return {}


func _static_box(size: Vector3, pos: Vector3, ry: float) -> void:
	var b := StaticBody3D.new()
	var cs := CollisionShape3D.new()
	var bs := BoxShape3D.new()
	bs.size = size
	cs.shape = bs
	b.add_child(cs)
	b.position = pos
	b.rotation.y = ry
	add_child(b)


func _add_collision(d: Dictionary) -> void:
	_static_box(Vector3(460, 1.0, 460), Vector3(0, -0.5, 0), 0.0)
	for st in d.get("roads", []):
		var w: float = float(st.get("w", 8))
		var dd: float = float(st.get("d", 8))
		var ry: float = float(st.get("ry", 0))
		_static_box(Vector3(w, 0.1, dd),
				Vector3(float(st.get("cx", 0)), -0.02, float(st.get("cz", 0))), ry)
	for st in d.get("sidewalks", []):
		var w: float = float(st.get("w", 8))
		var dd: float = float(st.get("d", 8))
		var ry: float = float(st.get("ry", 0))
		_static_box(Vector3(w, 0.4, dd),
				Vector3(float(st.get("cx", 0)), 0.0, float(st.get("cz", 0))), ry)
	for b in d.get("buildings", []):
		var key: String = str(b.get("m", "building_a"))
		if COLLISION_BOXES.has(key):
			var sz: Vector3 = COLLISION_BOXES[key]
			_static_box(sz, Vector3(float(b.get("x", 0)), sz.y / 2.0 + 0.16, float(b.get("z", 0))),
					float(b.get("ry", 0)))
	for p in d.get("props", []):
		var key2: String = str(p.get("m", "crate_stack"))
		if COLLISION_BOXES.has(key2):
			var sz2: Vector3 = COLLISION_BOXES[key2]
			_static_box(sz2, Vector3(float(p.get("x", 0)), sz2.y / 2.0 + 0.16, float(p.get("z", 0))),
					float(p.get("ry", 0)))
	for bp in d.get("bumps", []):
		_static_box(COLLISION_BOXES["speed_bump"],
				Vector3(float(bp.get("x", 0)), 0.06, float(bp.get("z", 0))), float(bp.get("ry", 0)))


## Designated jump ramps: wedge visual + polled launch trigger (clear, testable, isolated).
func _add_ramps(ramps: Array) -> void:
	for r in ramps:
		var mi := MeshInstance3D.new()
		mi.mesh = MeshBuilder.build("ramp")
		mi.position = Vector3(float(r.get("x", 0)), 0.03, float(r.get("z", 0)))
		mi.rotation.y = float(r.get("ry", 0))
		add_child(mi)
		MaterialsLib.apply_to(mi, MaterialsLib.lib())
		_ramps.append(Vector3(float(r.get("x", 0)), 0, float(r.get("z", 0))))
		_ramp_cd.append(0.0)


func _poll_ramps(delta: float) -> void:
	for i in _ramps.size():
		_ramp_cd[i] = maxf(float(_ramp_cd[i]) - delta, 0.0)
		var rp: Vector3 = _ramps[i]
		var tp := Vector3(tuktuk.global_position.x, 0, tuktuk.global_position.z)
		if float(_ramp_cd[i]) <= 0.0 and tp.distance_to(rp) < 3.0:
			tuktuk.call("launch")
			_ramp_cd[i] = 1.5


func _on_impact(strength: float) -> void:
	if cam != null and cam.has_method("add_shake"):
		cam.call("add_shake", strength)


func _add_shortcut_zone(sz: Dictionary) -> void:
	if sz.is_empty():
		return
	var short := Area3D.new()
	short.name = "ShortcutZone"
	short.monitoring = false  # polled by distance; Area3D kept as the Phase-5 navigation hook
	var ss := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(float(sz.get("w", 6)), 4, float(sz.get("d", 80)))
	ss.shape = box
	short.add_child(ss)
	short.position = Vector3(float(sz.get("cx", 0)), 2, float(sz.get("cz", 0)))
	short.rotation.y = float(sz.get("ry", 0))
	add_child(short)


func _make_arrow() -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = MeshBuilder.build("arrow_chevron")
	var m := StandardMaterial3D.new()
	m.albedo_color = Color("3ddc55")
	m.emission_enabled = true
	m.emission = Color("2fae44")
	mi.material_override = m
	mi.position = _dest_marker + Vector3(0, 6.0, 0)
	mi.visible = false
	add_child(mi)
	return mi


# ------------------------------------------------------------------ mission loop
func _spawn_passenger() -> void:
	var cast: Array = Reg.cast()
	if cast.is_empty():
		return
	_cast_idx = (_cast_idx + 1) % cast.size()
	var entry: Dictionary = cast[_cast_idx]
	var p: Node3D = Node3D.new()
	p.set_script(load("res://scripts/characters/passenger.gd"))
	add_child(p)
	p.call("setup", entry)
	var d: Dictionary = Reg.district()
	p.global_position = Vector3(float(d["pickup_stand"]["x"]), 0.16, float(d["pickup_stand"]["z"]))
	passenger = p


func _process(delta: float) -> void:
	if tuktuk == null:
		return
	var tpos := Vector3(tuktuk.global_position.x, 0, tuktuk.global_position.z)
	var spd: float = absf(float(tuktuk.get("speed")))
	var max_stop: float = float(Reg.tuning().get("deliver_max_speed", 3.0))
	_offer_cooldown = maxf(_offer_cooldown - delta, 0.0)
	_poll_ramps(delta)
	var st: int = MissionMgr.state
	if st == MissionMgr.State.IDLE:
		var at_pick: bool = tpos.distance_to(_pickup_marker) < RING_PICKUP_R
		if _offer_cooldown <= 0.0 and passenger != null and at_pick and spd < max_stop:
			var dest_lbl: String = str(Reg.district().get("dest_name_en", "Town"))
			MissionMgr.make_offer(passenger.get("cast_entry"), dest_lbl, _route_distance())
	elif st == MissionMgr.State.OFFER:
		if Input.is_action_just_pressed("accept_mission"):
			if MissionMgr.accept_offer():
				var seat: Vector3 = tuktuk.global_position + Vector3(0, 1.05, 0.62)
				passenger.call("board_to", seat, MissionMgr.begin_driving)
	elif st == MissionMgr.State.DRIVING:
		_arrow.visible = true
		_arrow_t += delta
		_arrow.position = _dest_marker + Vector3(0, 5.6 + sin(_arrow_t * 3.0) * 0.35, 0)
		_arrow.rotation.y += delta * 0.8
		if tpos.distance_to(_dest_marker) < RING_DEST_R and spd < max_stop:
			MissionMgr.complete_delivery()
		var szn: Node3D = get_node_or_null("ShortcutZone")
		if szn != null:
			var szp := Vector3(szn.global_position.x, 0, szn.global_position.z)
			if szp.distance_to(tpos) < 5.0:
				MissionMgr.report_shortcut()
	elif st == MissionMgr.State.RESULT:
		_arrow.visible = false
		_result_open = true
		if Input.is_action_just_pressed("accept_mission"):
			next_mission_cycle()


func _on_result(result: Dictionary) -> void:
	_result_open = true
	var stand: Vector3
	if bool(result.get("success", false)):
		stand = _dest_marker + Vector3(2.5, 0.16, 3.5)
	else:
		stand = tuktuk.global_position + Vector3(1.6, 0.16, 0.0)
	if passenger != null:
		var p: Node = passenger
		passenger = null  # detached immediately: the exit tween owns only its own instance
		p.call("exit_to", stand, func() -> void: p.queue_free())


## Street-route estimate (ring + market street via the junctions), not beeline: keeps fares honest.
func _route_distance() -> float:
	var d: Dictionary = Reg.district()
	var px: float = float(d["pickup"]["x"])
	var pz: float = float(d["pickup"]["z"])
	var dx: float = float(d["dest"]["x"])
	var dz: float = float(d["dest"]["z"])
	return absf(px - dx) + absf(pz - 0.0) + absf(0.0 - dz) + 10.0


func _on_reset() -> void:
	var d: Dictionary = Reg.district()
	var r: Dictionary = d.get("reset", {"x": 0, "z": 60, "ry": -1.5708})
	tuktuk.global_position = Vector3(float(r.get("x", 0)), 0.4, float(r.get("z", 60)))
	tuktuk.set("yaw", float(r.get("ry", 0)))
	tuktuk.set("speed", 0.0)
	tuktuk.set("lat_vel", Vector3.ZERO)
	if hud.has_method("show_toast"):
		hud.call("show_toast", "Back on the road - careful now!")


## Dev-only harness probe (F9): dumps camera/vehicle/surface state to the console log.
func _dbg_dump(tag: String) -> void:
	var meshes := 0
	var vis := 0
	for ch in get_children():
		if ch is MeshInstance3D:
			meshes += 1
			if ch.visible:
				vis += 1
	var g: Node3D = get_node_or_null("Ground")
	print("TKDBG %s cam=%s rot=%s tuk=%s yaw=%s meshes=%d/%d ground=%s arrow=%s state=%d" % [
		tag, str(cam.global_position), str(cam.global_rotation_degrees),
		str(tuktuk.global_position), str(tuktuk.get("yaw")), vis, meshes,
		str(g.global_position) if g != null else "null", str(_arrow.global_position),
		MissionMgr.state])


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.physical_keycode == KEY_F9:
		_dbg_dump("key")


func next_mission_cycle() -> void:
	MissionMgr.reset_to_idle()
	_result_open = false
	_offer_cooldown = 1.0
	_spawn_passenger()
