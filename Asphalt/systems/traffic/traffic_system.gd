extends Node3D
class_name AGTrafficSystem
## Deterministic traffic spawning, following, lane changes and despawning.

signal near_miss_detected()

var vehicles: Array = []
var traffic_types: Array = []
var player: AGMotorcycleController
var density := 1.0
var difficulty := 1
var rng := RandomNumberGenerator.new()
var spawn_distance := 760.0
var despawn_distance := 190.0
var near_miss_cooldown := 0.0
var police_spawned := 0

func setup(types: Array, player_ref: AGMotorcycleController, density_value: float,
        difficulty_value: int) -> void:
    traffic_types = types.duplicate(true)
    player = player_ref
    density = clampf(density_value, 0.35, 1.8)
    difficulty = clampi(difficulty_value, 0, 2)
    rng.seed = 90210 + difficulty * 17
    spawn_initial()

func get_definition(type_id: String) -> Dictionary:
    for definition in traffic_types:
        if String(definition.get("id", "")) == type_id:
            return definition.duplicate(true)
    if traffic_types.is_empty():
        return {"id": "car", "mass": 1.0, "speed_min": 18.0, "speed_max": 28.0,
            "length": 4.4, "width": 1.9, "height": 1.4, "color": "#9AA0A1",
            "accent": "#D4D2C7", "lane_change": 0.5}
    return traffic_types[0].duplicate(true)

func _random_type_id() -> String:
    var roll := rng.randf()
    if roll < 0.32:
        return "car"
    elif roll < 0.50:
        return "taxi"
    elif roll < 0.66:
        return "microbus"
    elif roll < 0.77:
        return "minibus"
    elif roll < 0.91:
        return "truck"
    return "trailer"

func spawn_initial() -> void:
    var count := int(34.0 * density)
    # The player starts near z=0 looking toward -Z. Keep a clear 90 m bubble
    # so no traffic is ever spawned inside or immediately in front of them.
    var player_z := player.position.z if player != null else 0.0
    var first_z := player_z - 90.0
    for i in range(count):
        var z: float = first_z - float(i) * (spawn_distance / float(maxi(count, 1))) - rng.randf() * 24.0
        _spawn_one(_random_type_id(), rng.randi_range(0, AGRoadPath.LANE_COUNT - 1), z, false)

func _spawn_one(type_id: String, lane: int, z: float, police: bool) -> AGTrafficVehicle:
    var definition := get_definition(type_id)
    var speed_min := float(definition.get("speed_min", 18.0))
    var speed_max := float(definition.get("speed_max", 28.0))
    var speed := rng.randf_range(speed_min, speed_max)
    if police:
        speed = rng.randf_range(float(definition.get("speed_min", 30.0)),
            float(definition.get("speed_max", 45.0)))
    var vehicle := AGTrafficVehicle.new()
    vehicle.setup(definition, lane, z, speed, police)
    vehicle.lane_change_timer = rng.randf_range(1.5, 6.0)
    add_child(vehicle)
    vehicles.append(vehicle)
    return vehicle

func spawn_police(count: int, distance_ahead: float = 430.0) -> Array:
    var spawned: Array = []
    for i in range(count):
        var lane := rng.randi_range(0, AGRoadPath.LANE_COUNT - 1)
        var z: float = player.position.z - distance_ahead - float(i) * 24.0
        var vehicle := _spawn_one("police", lane, z, true)
        police_spawned += 1
        spawned.append(vehicle)
    return spawned

func spawn_interception() -> Array:
    # A deliberate roadblock, but spawned far enough ahead to be visible and
    # approached normally; police never teleport on top of the player.
    var lanes := [rng.randi_range(0, 1), rng.randi_range(2, 3)]
    var spawned: Array = []
    for i in range(lanes.size()):
        var z: float = player.position.z - 310.0 - float(i) * 12.0
        var vehicle := _spawn_one("police", int(lanes[i]), z, true)
        vehicle.set_traffic_speed(11.0 + float(i) * 2.0)
        spawned.append(vehicle)
    return spawned

func clear_police() -> void:
    var remaining: Array = []
    for vehicle in vehicles:
        if is_instance_valid(vehicle) and vehicle.is_police:
            vehicle.queue_free()
        else:
            remaining.append(vehicle)
    vehicles = remaining

func get_vehicles() -> Array:
    return vehicles

func lane_clearance(lane: int, z: float, max_distance: float = 180.0) -> float:
    var best := max_distance
    for vehicle in vehicles:
        if not is_instance_valid(vehicle) or vehicle.lane != lane:
            continue
        var dz: float = vehicle.position.z - z
        if dz < 0.0 and dz > -max_distance:
            best = minf(best, -dz)
    return best

func _process(delta: float) -> void:
    if player == null or not is_instance_valid(player):
        return
    near_miss_cooldown = maxf(0.0, near_miss_cooldown - delta)
    for vehicle in vehicles:
        if not is_instance_valid(vehicle):
            continue
        _update_vehicle(vehicle, delta)
        _maybe_near_miss(vehicle)
    _cleanup_and_respawn()

func _update_vehicle(vehicle: AGTrafficVehicle, delta: float) -> void:
    vehicle.target_speed = _desired_speed(vehicle)
    vehicle.speed = lerpf(vehicle.speed, vehicle.target_speed, 1.0 - exp(-1.4 * delta))
    vehicle.set_meta("speed", vehicle.speed)
    vehicle.position.z -= vehicle.speed * delta
    var desired_x := AGRoadPath.lane_x(vehicle.position.z, vehicle.lane)
    vehicle.position.x = lerpf(vehicle.position.x, desired_x, 1.0 - exp(-2.3 * delta))
    vehicle.position.y = AGRoadPath.height_at(vehicle.position.z)
    vehicle.rotation.y = -AGRoadPath.yaw_at(vehicle.position.z)
    vehicle.animate(delta)
    vehicle.lane_change_timer -= delta
    if vehicle.lane_change_timer <= 0.0:
        vehicle.lane_change_timer = rng.randf_range(3.0, 8.0)
        _try_lane_change(vehicle)

func _desired_speed(vehicle: AGTrafficVehicle) -> float:
    var definition := vehicle.type_def
    var base := rng.randf_range(float(definition.get("speed_min", 18.0)),
        float(definition.get("speed_max", 28.0)))
    # Following distance: check the nearest vehicle ahead in the same lane.
    var gap := 999.0
    var ahead_speed := base
    for other in vehicles:
        if not is_instance_valid(other) or other == vehicle or other.lane != vehicle.lane:
            continue
        var dz: float = other.position.z - vehicle.position.z
        if dz < 0.0 and -dz < gap:
            gap = -dz
            ahead_speed = other.speed
    if gap < 28.0:
        return minf(base, ahead_speed * clampf(gap / 28.0, 0.15, 1.0))
    return base

func _try_lane_change(vehicle: AGTrafficVehicle) -> void:
    var lane_change_chance := float(vehicle.type_def.get("lane_change", 0.5))
    if vehicle.is_police or rng.randf() > lane_change_chance:
        return
    var options: Array = []
    if vehicle.lane > 0:
        options.append(vehicle.lane - 1)
    if vehicle.lane < AGRoadPath.LANE_COUNT - 1:
        options.append(vehicle.lane + 1)
    if options.is_empty():
        return
    var new_lane: int = options[rng.randi_range(0, options.size() - 1)]
    if lane_clearance(new_lane, vehicle.position.z, 55.0) > 42.0:
        vehicle.lane = new_lane

func _maybe_near_miss(vehicle: AGTrafficVehicle) -> void:
    if near_miss_cooldown > 0.0 or player.crash_active:
        return
    var dz: float = vehicle.position.z - player.position.z
    var dx: float = vehicle.position.x - player.position.x
    if absf(dz) < 3.0 and absf(dx) > 0.85 and absf(dx) < 2.1 and absf(player.speed - vehicle.speed) > 18.0:
        near_miss_cooldown = 1.2
        player.register_near_miss()
        near_miss_detected.emit()

func _cleanup_and_respawn() -> void:
    var remaining: Array = []
    for vehicle in vehicles:
        if not is_instance_valid(vehicle):
            continue
        if vehicle.position.z > player.position.z + despawn_distance or vehicle.position.z < AGRoadPath.FINISH_Z - 120.0:
            vehicle.queue_free()
        else:
            remaining.append(vehicle)
    vehicles = remaining
    var desired_count := int(34.0 * density)
    while vehicles.size() < desired_count:
        var z: float = player.position.z - spawn_distance - rng.randf() * 220.0
        # Never spawn within the player's immediate hazard zone.
        if absf(z - player.position.z) < 260.0:
            z = player.position.z - 320.0
        _spawn_one(_random_type_id(), rng.randi_range(0, AGRoadPath.LANE_COUNT - 1), z, false)
