extends RefCounted
class_name AGRivalBrain
## Navigation, decision-making and movement are separated from the controller.

var rider_data: Dictionary = {}
var difficulty := 1
var index := 0
var rng := RandomNumberGenerator.new()
var target_lane := 1
var decision_timer := 0.0
var reaction_time := 0.45
var speed_factor := 0.9
var aggression := 0.6
var skill := 0.8
var boost_timer := 0.0
var personality_name := "STREET"

func setup(rider: Dictionary, difficulty_level: int, rival_index: int) -> void:
    rider_data = rider.duplicate(true)
    difficulty = clampi(difficulty_level, 0, 2)
    index = rival_index
    rng.seed = 4100 + rival_index * 173 + int(String(rider.get("id", "")).hash())
    aggression = float(rider.get("aggression", 0.65))
    skill = float(rider.get("skill", 0.8))
    speed_factor = 0.76 + skill * 0.17 + float(difficulty) * 0.035
    reaction_time = lerpf(0.72, 0.26, skill)
    decision_timer = rng.randf_range(0.2, reaction_time)
    boost_timer = rng.randf_range(3.0, 9.0)
    personality_name = String(rider.get("epithet", "STREET RIDER")).to_upper()
    target_lane = rival_index % AGRoadPath.LANE_COUNT

func decide(controller: AGMotorcycleController, delta: float) -> Dictionary:
    decision_timer -= delta
    boost_timer -= delta
    if decision_timer <= 0.0:
        decision_timer = reaction_time + rng.randf_range(0.0, 0.35)
        target_lane = _choose_lane(controller)
    var desired_x := AGRoadPath.lane_x(controller.position.z, target_lane)
    var dx := desired_x - controller.position.x
    var steer := clampf(dx * (0.18 + skill * 0.10), -1.0, 1.0)
    var desired_speed := controller.max_speed * speed_factor
    var throttle := 1.0 if controller.speed < desired_speed else 0.0
    var brake := 0.0
    var gap := _gap_ahead(controller, target_lane)
    if gap < 42.0 and controller.speed > 25.0:
        brake = clampf((42.0 - gap) / 42.0, 0.0, 0.85) * lerpf(1.0, 0.55, skill)
    if controller.crash_active:
        throttle = 0.0
        brake = 1.0
    var boost := 0.0
    if boost_timer <= 0.0 and controller.boost_energy > 0.45 and aggression > 0.7 and gap > 80.0:
        boost = 1.0
        boost_timer = rng.randf_range(7.0, 14.0)
    return {
        "throttle": throttle, "brake": brake, "steer": steer,
        "handbrake": 0.0, "boost": boost,
    }

func _choose_lane(controller: AGMotorcycleController) -> int:
    var current := AGRoadPath.lane_from_x(controller.position.z, controller.position.x)
    var best_lane := current
    var best_score := -1e9
    for lane in range(AGRoadPath.LANE_COUNT):
        var clearance := _gap_ahead(controller, lane)
        var score := clearance
        score -= absf(float(lane - current)) * 28.0
        score += rng.randf_range(-8.0, 8.0)
        if lane == current:
            score += 12.0
        if aggression > 0.85 and lane != current:
            score += 8.0
        if score > best_score:
            best_score = score
            best_lane = lane
    return best_lane

func _gap_ahead(controller: AGMotorcycleController, lane: int) -> float:
    var traffic_system: AGTrafficSystem = controller.get_meta("traffic_system", null)
    var z := controller.position.z
    var best := 180.0
    if traffic_system != null:
        for vehicle in traffic_system.vehicles:
            if not is_instance_valid(vehicle) or vehicle.lane != lane:
                continue
            var dz: float = vehicle.position.z - z
            if dz < 0.0 and dz > -180.0:
                best = minf(best, -dz)
    for rival in controller.get_meta("rivals", []):
        if is_instance_valid(rival) and rival != controller:
            var rival_lane := AGRoadPath.lane_from_x(rival.position.z, rival.position.x)
            if rival_lane == lane:
                var dz2: float = rival.position.z - z
                if dz2 < 0.0 and dz2 > -180.0:
                    best = minf(best, -dz2 + 2.0)
    return best
