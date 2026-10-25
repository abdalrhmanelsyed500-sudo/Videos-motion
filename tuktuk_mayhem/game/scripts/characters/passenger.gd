extends Node3D
## Passenger/pedestrian actor. Mesh chosen by cast data: hijab:true => person_hijab geometry
## (ART_BIBLE §5 enforced at geometry level, not by prompt). Pose animation in Phase 1 is a
## scripted tween (TEMP label in ASSET_INVENTORY); AnimationPlayer clips arrive in Phase 3.

enum PState { WAIT, BOARD, RIDE, EXIT, DONE }

const MeshBuilder := preload("res://scripts/core/mesh_builder.gd")
const MaterialsLib := preload("res://scripts/core/materials.gd")

var state: int = PState.WAIT
var cast_entry: Dictionary = {}
var _mesh: MeshInstance3D
var _tween: Tween
var _bob_t: float = 0.0


func setup(entry: Dictionary) -> void:
	cast_entry = entry
	var spec_name := "person_hijab" if bool(entry.get("hijab", false)) else "person"
	_mesh = MeshInstance3D.new()
	_mesh.mesh = MeshBuilder.build(spec_name)
	add_child(_mesh)
	MaterialsLib.apply_to(_mesh, MaterialsLib.person_mats(entry, MaterialsLib.lib()))


func _process(delta: float) -> void:
	if state == PState.WAIT:  # TEMP idle: weight-shift bob + raised-arm wave via root tilt
		_bob_t += delta
		_mesh.position.y = abs(sin(_bob_t * 2.2)) * 0.03
		_mesh.rotation.z = sin(_bob_t * 2.2) * 0.03


## Walk (tween) to the tuktuk seat, then ride hidden inside the vehicle.
func board_to(seat_global: Vector3, done_cb: Callable) -> void:
	state = PState.BOARD
	_tween = create_tween()
	_tween.tween_property(self, "global_position", seat_global, 0.9).set_trans(Tween.TRANS_SINE)
	_tween.tween_callback(func() -> void:
		state = PState.RIDE
		visible = false
		done_cb.call())


func exit_to(stand_global: Vector3, done_cb: Callable) -> void:
	state = PState.EXIT
	visible = true
	global_position = stand_global + Vector3(0.9, 0, 0.4)
	_tween = create_tween()
	_tween.tween_property(self, "global_position", stand_global, 0.7).set_trans(Tween.TRANS_SINE)
	_tween.tween_callback(func() -> void:
		state = PState.DONE
		done_cb.call())
