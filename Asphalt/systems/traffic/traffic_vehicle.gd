extends Area3D
class_name AGTrafficVehicle
## One moving traffic Area3D; visual model is built from shaped parts.

var type_def: Dictionary = {}
var type_id := "car"
var lane := 1
var speed := 22.0
var target_speed := 22.0
var mass := 1.0
var view: AGVehicleView
var is_police := false
var lane_change_timer := 0.0
var stationary := false

func setup(definition: Dictionary, lane_index: int, z: float, travel_speed: float, police := false) -> void:
    type_def = definition.duplicate(true)
    type_id = String(definition.get("id", "car"))
    lane = clampi(lane_index, 0, AGRoadPath.LANE_COUNT - 1)
    speed = travel_speed
    target_speed = travel_speed
    mass = float(definition.get("mass", 1.0))
    is_police = police
    name = "Traffic_" + type_id
    collision_layer = 2
    collision_mask = 0
    monitoring = false
    monitorable = true
    set_meta("type", type_id)
    set_meta("mass", mass)
    set_meta("speed", speed)
    set_meta("police", police)
    var shape_node := CollisionShape3D.new()
    var box := BoxShape3D.new()
    box.size = Vector3(float(definition.get("width", 1.9)) * 1.15,
        float(definition.get("height", 1.5)) * 1.15,
        float(definition.get("length", 4.5)) * 1.10)
    shape_node.shape = box
    shape_node.position = Vector3(0.0, float(definition.get("height", 1.5)) * 0.55, 0.0)
    add_child(shape_node)
    view = AGVehicleFactory.build(type_def)
    add_child(view)
    position = Vector3(AGRoadPath.lane_x(z, lane), AGRoadPath.height_at(z), z)

func set_traffic_speed(value: float) -> void:
    speed = maxf(0.0, value)
    set_meta("speed", speed)

func animate(delta: float) -> void:
    if view != null:
        view.set_motion(speed, delta)
