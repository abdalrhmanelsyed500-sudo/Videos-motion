extends Control
class_name AGHybrid25DBenchmark
## Experimental Hybrid 2.5D benchmark.
##
## This is intentionally separate from the production 3D project. It uses a
## scanline road/projection renderer and original low-resolution sprites, but
## all gameplay positions are road-relative (distance ahead z + lane offset),
## never screen-space-only. Collisions, police and race progression use the same
## coordinates that drive sprite projection.

enum State { RACING, CRASHED, HOSPITAL, FINISHED }

const W := 1280.0
const H := 720.0
const HORIZON := 276.0
const NEAR_PLANE := 18.0
const ROAD_HALF_WIDTH_WORLD := 7.8
const LANE_WIDTH := 3.6
const LANE_COUNT := 4
const FINISH_DISTANCE := 3200.0
const DASH_LENGTH := 12.0
const DASH_PERIOD := 24.0
const ASSET_DIR := "res://experiments/hybrid_2p5d/assets/"

var manifest: Dictionary = {}
var font: Font
var rng := RandomNumberGenerator.new()

var sky_tex: Texture2D
var hills_tex: Texture2D
var ground_tex: Texture2D
var far_buildings_tex: Texture2D
var roadside_left_tex: Texture2D
var roadside_right_tex: Texture2D
var cockpit_tex: Texture2D
var rider_sheet_tex: Texture2D
var traffic_sheet_tex: Texture2D

var rider_info: Dictionary = {}
var traffic_info: Dictionary = {}
var cockpit_info: Dictionary = {}
var rider_frame_names: Array = []
var traffic_kinds: Array = []
var traffic_angles: Array = []

var state: int = State.RACING
var benchmark_mode := false
var debug_mode := false
var test_input: Variant = null
var key_state: Dictionary = {}

var speed := 0.0
var max_speed := 72.0
var acceleration := 16.0
var braking := 26.0
var boost := 1.0
var gear := 1
var rpm := 0.18
var lateral := -1.8  # metres from road center
var steer := 0.0
var distance_traveled := 0.0
var race_time := 0.0
var position_value := 4
var police_level := 0
var police_timer := 0.0
var crash_cooldown := 0.0
var crash_timer := 0.0
var crash_reason := ""
var crash_severity := 0
var finish_position := 1
var collision_count := 0
var near_miss_count := 0
var wobble := 0.0
var warning_message := ""
var warning_timer := 0.0
var objects: Array = []

func _ready() -> void:
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
    mouse_filter = Control.MOUSE_FILTER_IGNORE
    font = ThemeDB.fallback_font
    rng.seed = 20261027
    _load_assets()
    restart_race()

func _load_assets() -> void:
    var manifest_path := ASSET_DIR + "hybrid_assets_manifest.json"
    if FileAccess.file_exists(manifest_path):
        var file := FileAccess.open(manifest_path, FileAccess.READ)
        if file != null:
            var parsed: Variant = JSON.parse_string(file.get_as_text())
            file.close()
            if parsed is Dictionary:
                manifest = parsed
    rider_info = manifest.get("rider_bike_sheet", {})
    traffic_info = manifest.get("traffic_sheet", {})
    cockpit_info = manifest.get("cockpit", {})
    rider_frame_names = rider_info.get("frame_names", [])
    traffic_kinds = traffic_info.get("kinds", ["taxi", "car", "microbus", "truck", "trailer", "police"])
    traffic_angles = traffic_info.get("angles", ["straight", "left", "right"])
    sky_tex = load(ASSET_DIR + "sky.png")
    hills_tex = load(ASSET_DIR + "hills.png")
    ground_tex = load(ASSET_DIR + "ground.png")
    far_buildings_tex = load(ASSET_DIR + "buildings_far.png")
    roadside_left_tex = load(ASSET_DIR + "roadside_left.png")
    roadside_right_tex = load(ASSET_DIR + "roadside_right.png")
    cockpit_tex = load(ASSET_DIR + "cockpit_base.png")
    rider_sheet_tex = load(ASSET_DIR + "rider_bike_sheet.png")
    traffic_sheet_tex = load(ASSET_DIR + "traffic_sheet.png")

func _process(delta: float) -> void:
    _poll_one_shot_keys()
    warning_timer = maxf(0.0, warning_timer - delta)
    crash_cooldown = maxf(0.0, crash_cooldown - delta)
    if state == State.CRASHED and not benchmark_mode:
        crash_timer -= delta
        if crash_timer <= 0.0:
            state = State.HOSPITAL
            warning_message = "HOSPITAL — " + crash_reason
            warning_timer = 5.0
    elif state == State.RACING and not benchmark_mode:
        _update_simulation(delta)
    queue_redraw()

func _poll_one_shot_keys() -> void:
    if _key_just_pressed(KEY_R):
        restart_race()
    if _key_just_pressed(KEY_V):
        debug_mode = not debug_mode
    if _key_just_pressed(KEY_P):
        force_police_alert()
    if _key_just_pressed(KEY_F):
        force_severe_crash("Manual benchmark fall")
    if _key_just_pressed(KEY_G):
        force_finish()
    if _key_just_pressed(KEY_ESCAPE):
        get_tree().quit()

func _key_just_pressed(keycode: int) -> bool:
    var now := Input.is_key_pressed(keycode)
    var was := bool(key_state.get(keycode, false))
    key_state[keycode] = now
    return now and not was

func _read_input() -> Dictionary:
    if test_input != null:
        return _normalize_input(test_input)
    var throttle := 1.0 if (Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP)) else 0.0
    var brake := 1.0 if (Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN)) else 0.0
    var left := 1.0 if (Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT)) else 0.0
    var right := 1.0 if (Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT)) else 0.0
    var handbrake := 1.0 if Input.is_key_pressed(KEY_SPACE) else 0.0
    var boost_value := 1.0 if Input.is_key_pressed(KEY_SHIFT) else 0.0
    return _normalize_input({
        "throttle": throttle, "brake": brake, "steer": right - left,
        "handbrake": handbrake, "boost": boost_value,
    })

func _normalize_input(value: Dictionary) -> Dictionary:
    return {
        "throttle": clampf(float(value.get("throttle", 0.0)), 0.0, 1.0),
        "brake": clampf(float(value.get("brake", 0.0)), 0.0, 1.0),
        "steer": clampf(float(value.get("steer", 0.0)), -1.0, 1.0),
        "handbrake": clampf(float(value.get("handbrake", 0.0)), 0.0, 1.0),
        "boost": clampf(float(value.get("boost", 0.0)), 0.0, 1.0),
    }

func _update_simulation(delta: float) -> void:
    var input := _read_input()
    var throttle := float(input["throttle"])
    var brake := float(input["brake"])
    var handbrake := float(input["handbrake"])
    var boost_input := float(input["boost"])
    var steer_input := float(input["steer"])

    var boost_active := boost_input > 0.1 and boost > 0.02
    var current_max := max_speed + (8.0 if boost_active else 0.0)
    if throttle > 0.0:
        var falloff := clampf(1.0 - speed / maxf(current_max, 1.0), 0.05, 1.0)
        speed += acceleration * throttle * (0.35 + falloff * 0.9) * delta
    else:
        speed -= 3.0 * delta
    if boost_active:
        speed += 10.0 * delta
        boost = maxf(0.0, boost - 0.28 * delta)
    else:
        boost = minf(1.0, boost + 0.07 * delta)
    if brake > 0.0:
        speed -= braking * brake * delta
    if handbrake > 0.0:
        speed -= braking * 1.15 * handbrake * delta
    speed = clampf(speed, 0.0, current_max)

    var speed_factor := 1.0 - clampf(speed / maxf(max_speed, 1.0), 0.0, 1.0) * 0.38
    steer = lerpf(steer, steer_input * speed_factor, 1.0 - exp(-9.0 * delta))
    lateral += steer * delta * (3.2 + speed * 0.018) + wobble * delta
    lateral = clampf(lateral, -6.9, 6.9)
    wobble = lerpf(wobble, 0.0, 1.0 - exp(-3.5 * delta))

    var gear_span := maxf(max_speed / 6.0, 1.0)
    gear = clampi(int(speed / gear_span) + 1, 1, 6)
    rpm = clampf(0.16 + fmod(speed, gear_span) / gear_span * 0.78 + throttle * 0.06, 0.14, 1.0)

    distance_traveled += speed * delta
    race_time += delta
    _update_police(delta)
    _update_objects(delta)
    _check_collisions()
    position_value = _calculate_position()
    if distance_traveled >= FINISH_DISTANCE:
        _finish_race()

func _update_police(delta: float) -> void:
    if police_level == 0:
        if distance_traveled > 600.0 and speed > 48.0:
            police_timer += delta
            if police_timer > 3.0:
                force_police_alert()
    else:
        if speed < 28.0:
            police_timer -= delta * 0.5
            if police_timer < -8.0:
                police_level = 0
                police_timer = 0.0
        else:
            police_timer = 0.0

func force_police_alert() -> void:
    police_level = clampi(police_level + 1, 0, 3)
    police_timer = 0.0
    warning_message = "POLICE PURSUIT LEVEL " + str(police_level)
    warning_timer = 4.0
    _spawn_police_object()

func _spawn_police_object() -> void:
    for obj in objects:
        var item: Dictionary = obj
        if bool(item.get("is_police", false)):
            return
    _add_traffic("police", 150.0, 2.0, maxf(speed + 3.0, 38.0), true)

func _update_objects(delta: float) -> void:
    for obj in objects:
        var item: Dictionary = obj
        if not bool(item.get("active", true)):
            continue
        var obj_speed := float(item.get("speed", 20.0))
        if bool(item.get("is_crash", false)):
            obj_speed = 0.0
        var z := float(item.get("z", 100.0))
        z += (obj_speed - speed) * delta
        item["z"] = z

        var lane_timer := float(item.get("lane_change_timer", 3.0)) - delta
        if lane_timer <= 0.0:
            lane_timer = rng.randf_range(2.5, 7.0)
            var chance := 0.78 if bool(item.get("is_rival", false)) else 0.45
            if rng.randf() < chance and not bool(item.get("is_crash", false)):
                var direction := -1.0 if rng.randi_range(0, 1) == 0 else 1.0
                item["target_lane"] = clampf(float(item.get("lane", 1.0)) + direction, 0.0, float(LANE_COUNT - 1))
                item["angle"] = "left" if direction < 0.0 else "right"
            else:
                item["target_lane"] = float(item.get("lane", 1.0))
                item["angle"] = "straight"
        else:
            var target_lane := float(item.get("target_lane", item.get("lane", 1.0)))
            var lane_value := lerpf(float(item.get("lane", 1.0)), target_lane, 1.0 - exp(-1.8 * delta))
            item["lane"] = lane_value
            if absf(lane_value - target_lane) < 0.06:
                item["angle"] = "straight"
        item["lane_change_timer"] = lane_timer

        if bool(item.get("is_rival", false)):
            var angle_name := String(item.get("angle", "straight"))
            if angle_name == "left":
                item["frame"] = "riding/lean_left"
            elif angle_name == "right":
                item["frame"] = "riding/lean_right"
            elif speed > 58.0:
                item["frame"] = "riding/accelerate"
            else:
                item["frame"] = "riding/ride"
        if bool(item.get("is_police", false)):
            item["speed"] = maxf(float(item.get("speed", 38.0)), speed + 1.5)

        if z < -35.0 or z > 760.0:
            _respawn_object(item)

func _respawn_object(item: Dictionary) -> void:
    var new_z := rng.randf_range(420.0, 700.0)
    item["z"] = new_z
    item["lane"] = rng.randf_range(0.0, float(LANE_COUNT - 1))
    item["target_lane"] = item["lane"]
    item["angle"] = "straight"
    item["lane_change_timer"] = rng.randf_range(2.0, 6.0)
    if bool(item.get("is_crash", false)):
        item["speed"] = 0.0
        return
    if bool(item.get("is_rival", false)):
        item["speed"] = rng.randf_range(46.0, 59.0)
        item["frame"] = "riding/ride"
    elif bool(item.get("is_police", false)):
        item["speed"] = rng.randf_range(36.0, 50.0)
    else:
        var kind := String(traffic_kinds[rng.randi_range(0, maxi(0, traffic_kinds.size() - 2))])
        item["type"] = kind
        item["speed"] = _traffic_speed(kind)
        var collision_pair: Array = _collision_for(kind)
        item["collision_width"] = float(collision_pair[0])
        item["collision_length"] = float(collision_pair[1])

func _check_collisions() -> void:
    if crash_cooldown > 0.0 or state != State.RACING:
        return
    for obj in objects:
        var item: Dictionary = obj
        if not bool(item.get("active", true)):
            continue
        var z := absf(float(item.get("z", 100.0)))
        var obj_x := lane_x(float(item.get("lane", 1.0)))
        var dx := absf(lateral - obj_x)
        var length_threshold := (2.1 + float(item.get("collision_length", 4.5))) * 0.5
        var width_threshold := (0.9 + float(item.get("collision_width", 2.0))) * 0.5
        if z < length_threshold and dx < width_threshold:
            _apply_collision(item)
            return
        if z < 18.0 and dx > width_threshold and dx < width_threshold + 1.3 and absf(speed - float(item.get("speed", 0.0))) > 18.0:
            near_miss_count += 1

func _apply_collision(item: Dictionary) -> void:
    var relative := absf(speed - float(item.get("speed", 0.0)))
    var mass := float(item.get("mass", 1.0))
    var impact := relative * 0.55 + speed * 0.22 + mass * 7.0
    var severity := 1
    if impact > 58.0:
        severity = 3
    elif impact > 34.0:
        severity = 2
    collision_count += 1
    crash_cooldown = 0.9
    crash_severity = severity
    var type_name := String(item.get("type", "vehicle"))
    if severity == 1:
        speed *= 0.82
        wobble = rng.randf_range(-2.0, 2.0)
        warning_message = "MINOR IMPACT: " + type_name
        warning_timer = 2.5
    elif severity == 2:
        speed *= 0.55
        wobble = rng.randf_range(-4.0, 4.0)
        warning_message = "MODERATE IMPACT: " + type_name
        warning_timer = 3.0
    else:
        force_severe_crash("Collided with " + type_name.replace("_", " "))

func force_severe_crash(reason: String) -> void:
    if state != State.RACING:
        return
    state = State.CRASHED
    crash_reason = reason
    crash_severity = 3
    crash_timer = 2.2
    speed *= 0.18
    warning_message = "WIPEOUT: " + reason
    warning_timer = 4.0

func _finish_race() -> void:
    if state != State.RACING:
        return
    state = State.FINISHED
    finish_position = _calculate_position()
    warning_message = "RACE COMPLETE — POSITION " + str(finish_position)
    warning_timer = 6.0

func force_finish() -> void:
    if state != State.RACING:
        return
    distance_traveled = FINISH_DISTANCE
    _finish_race()

func _calculate_position() -> int:
    var value := 1
    for obj in objects:
        var item: Dictionary = obj
        if bool(item.get("is_rival", false)) and float(item.get("z", 0.0)) > 0.0:
            value += 1
    return clampi(value, 1, 4)

func restart_race() -> void:
    benchmark_mode = false
    debug_mode = false
    test_input = null
    state = State.RACING
    speed = 0.0
    boost = 1.0
    gear = 1
    rpm = 0.18
    lateral = -1.8
    steer = 0.0
    distance_traveled = 0.0
    race_time = 0.0
    position_value = 4
    police_level = 0
    police_timer = 0.0
    crash_cooldown = 0.0
    crash_timer = 0.0
    crash_reason = ""
    crash_severity = 0
    finish_position = 1
    collision_count = 0
    near_miss_count = 0
    wobble = 0.0
    warning_message = ""
    warning_timer = 0.0
    _spawn_initial_objects()
    queue_redraw()

func _spawn_initial_objects() -> void:
    objects.clear()
    _add_rival(34.0, 1.0, 48.0, "riding/ride", "Kareem")
    _add_rival(92.0, 2.6, 52.0, "riding/steer_left", "Sayed")
    _add_rival(148.0, 0.2, 50.0, "riding/lean_right", "Mona")
    _add_traffic("taxi", 72.0, 0.2, 25.0, false)
    _add_traffic("car", 122.0, 2.8, 29.0, false)
    _add_traffic("microbus", 164.0, 1.4, 19.0, false)
    _add_traffic("truck", 236.0, 3.0, 16.0, false)
    _add_traffic("trailer", 305.0, 0.4, 14.0, false)
    _add_traffic("police", 196.0, 2.0, 38.0, true)
    _add_crash(54.0, 2.0)

func _add_rival(z: float, lane_value: float, rival_speed: float, frame_name: String, rival_name: String) -> void:
    objects.append({
        "kind": "rival", "type": "rider", "name": rival_name,
        "z": z, "lane": lane_value, "target_lane": lane_value,
        "speed": rival_speed, "mass": 1.1, "collision_width": 0.9, "collision_length": 2.1,
        "frame": frame_name, "angle": "straight", "lane_change_timer": rng.randf_range(2.0, 6.0),
        "is_rival": true, "is_police": false, "is_crash": false, "active": true,
    })

func _add_traffic(type_name: String, z: float, lane_value: float, traffic_speed: float, police: bool) -> void:
    var pair := _collision_for(type_name)
    objects.append({
        "kind": "police" if police else "traffic", "type": type_name,
        "z": z, "lane": lane_value, "target_lane": lane_value,
        "speed": traffic_speed, "mass": 3.0 if type_name == "truck" or type_name == "trailer" else 1.4,
        "collision_width": float(pair[0]), "collision_length": float(pair[1]),
        "angle": "straight", "lane_change_timer": rng.randf_range(2.0, 7.0),
        "is_rival": false, "is_police": police, "is_crash": false, "active": true,
    })

func _add_crash(z: float, lane_value: float) -> void:
    objects.append({
        "kind": "crash", "type": "fallen_rider",
        "z": z, "lane": lane_value, "target_lane": lane_value,
        "speed": 0.0, "mass": 2.4, "collision_width": 1.8, "collision_length": 3.2,
        "frame": "crash/slide", "angle": "straight", "lane_change_timer": 999.0,
        "is_rival": false, "is_police": false, "is_crash": true, "active": true,
    })

func _collision_for(type_name: String) -> Array:
    var collision_data: Dictionary = traffic_info.get("collision", {})
    var pair: Array = collision_data.get(type_name, [2.0, 4.5])
    if pair.size() < 2:
        return [2.0, 4.5]
    return [float(pair[0]), float(pair[1])]

func _traffic_speed(type_name: String) -> float:
    match type_name:
        "taxi": return rng.randf_range(18.0, 28.0)
        "car": return rng.randf_range(20.0, 32.0)
        "microbus": return rng.randf_range(16.0, 24.0)
        "truck": return rng.randf_range(12.0, 18.0)
        "trailer": return rng.randf_range(11.0, 16.0)
        "police": return rng.randf_range(34.0, 48.0)
        _: return rng.randf_range(18.0, 28.0)

func lane_x(lane_value: float) -> float:
    return -5.4 + clampf(lane_value, 0.0, float(LANE_COUNT - 1)) * LANE_WIDTH

func player_lane_value() -> float:
    return (lateral + 5.4) / LANE_WIDTH

func curve_offset(world_z: float) -> float:
    return sin(world_z * 0.0016) * 42.0 + sin(world_z * 0.00057) * 20.0

func hill_offset(world_z: float) -> float:
    return sin(world_z * 0.0010) * 16.0 + sin(world_z * 0.0021) * 6.0

func horizon_y() -> float:
    return HORIZON + hill_offset(distance_traveled) * 0.45

func road_center_x(world_z: float, p: float) -> float:
    return W * 0.5 + curve_offset(distance_traveled + world_z * 0.80) * p * 3.0

func project(z: float, lateral_metres: float) -> Dictionary:
    var p := clampf(NEAR_PLANE / maxf(z + NEAR_PLANE, NEAR_PLANE), 0.0, 1.0)
    var hy := horizon_y()
    var y := hy + p * (H - hy)
    var half := 8.0 + 740.0 * pow(p, 1.55)
    var center := road_center_x(z, p)
    var x := center + lateral_metres * (half / ROAD_HALF_WIDTH_WORLD)
    var sprite_scale := 0.16 + 2.35 * p
    return {"p": p, "y": y, "half": half, "center": center, "x": x, "scale": sprite_scale}

func _sort_far_to_near(a: Dictionary, b: Dictionary) -> bool:
    return float(a.get("z", 0.0)) > float(b.get("z", 0.0))

func _draw() -> void:
    if sky_tex == null or rider_sheet_tex == null or traffic_sheet_tex == null:
        return
    _draw_background_layers()
    _draw_ground()
    _draw_near_roadside_layers()
    _draw_road()
    _draw_barriers()
    _draw_objects()
    _draw_cockpit()
    _draw_hud()
    _draw_state_overlays()
    if debug_mode:
        _draw_debug()

func _draw_background_layers() -> void:
    var curve := curve_offset(distance_traveled)
    var elevation := hill_offset(distance_traveled)
    var sky_shift := -fmod(distance_traveled * 0.012, W)
    draw_texture_rect(sky_tex, Rect2(sky_shift, 0.0, W, HORIZON + 90.0), true)
    var hill_shift := -fmod(distance_traveled * 0.004 + curve * 0.08, W)
    draw_texture_rect(hills_tex, Rect2(hill_shift, HORIZON - 190.0 + elevation * 0.25, W, 240.0), true)
    var far_shift := -fmod(distance_traveled * 0.008 + curve * 0.16, W)
    draw_texture_rect(far_buildings_tex, Rect2(far_shift, HORIZON - 152.0 + elevation * 0.18, W, 280.0), true)
func _draw_near_roadside_layers() -> void:
    var curve := curve_offset(distance_traveled)
    var elevation := hill_offset(distance_traveled)
    var near_shift := -curve * 0.14
    var near_y := HORIZON - 118.0 + elevation * 0.16
    draw_texture_rect(roadside_left_tex, Rect2(near_shift, near_y, 640.0, 420.0), false)
    draw_texture_rect(roadside_right_tex, Rect2(W - 640.0 + near_shift, near_y, 640.0, 420.0), false)

func _draw_ground() -> void:
    var y := horizon_y() - 18.0
    var shift := -fmod(distance_traveled * 0.018, W)
    draw_texture_rect(ground_tex, Rect2(shift, y, W, H - y + 20.0), true, Color(1.0, 1.0, 1.0, 0.96))

func _draw_road() -> void:
    var hy := horizon_y()
    var road_a := Color.html("#4B4858")
    var road_b := Color.html("#535060")
    var yellow := Color.html("#D9B51F")
    var white := Color.html("#D8D9D1")
    for y in range(int(hy), int(H)):
        var p := clampf(float(y - hy) / maxf(H - hy, 1.0), 0.001, 1.0)
        var z := NEAR_PLANE * (1.0 - p) / p
        var center := road_center_x(z, p)
        var half := 8.0 + 740.0 * pow(p, 1.55)
        var stripe := fmod(z + distance_traveled, 28.0) < 14.0
        var noise := sin((z + distance_traveled) * 0.71 + float(y) * 0.09) * 0.018
        var base := road_a if stripe else road_b
        var road_color := Color(clampf(base.r + noise, 0.0, 1.0),
            clampf(base.g + noise, 0.0, 1.0), clampf(base.b + noise, 0.0, 1.0), 1.0)
        draw_rect(Rect2(center - half, float(y), half * 2.0, 1.0), road_color)
        # Coarse dark asphalt patches, locked to road-relative distance.
        if fmod(z + distance_traveled, 17.0) < 1.4 and p > 0.12:
            var patch_width := half * 0.22
            draw_rect(Rect2(center - half * 0.65, float(y), patch_width, 1.0), Color(0.20, 0.19, 0.24, 1.0))
        var metres_per_pixel := half / ROAD_HALF_WIDTH_WORLD
        var line_w := maxf(1.0, 4.5 * p)
        # Double yellow centerline.
        for offset in [-0.24, 0.24]:
            var mx := center + float(offset) * metres_per_pixel
            draw_rect(Rect2(mx - line_w * 0.5, float(y), line_w, 1.0), yellow)
        # Dashed white lane lines move with road distance.
        if fmod(z + distance_traveled, DASH_PERIOD) < DASH_LENGTH:
            for offset in [-3.6, 3.6]:
                var lx := center + float(offset) * metres_per_pixel
                draw_rect(Rect2(lx - maxf(1.0, 2.8 * p) * 0.5, float(y), maxf(1.0, 2.8 * p), 1.0), white)
        # White edge lines.
        for offset in [-7.45, 7.45]:
            var ex := center + float(offset) * metres_per_pixel
            draw_rect(Rect2(ex - maxf(1.0, 2.2 * p) * 0.5, float(y), maxf(1.0, 2.2 * p), 1.0), white)

func _draw_barriers() -> void:
    var bridge_zone := fmod(distance_traveled, 2000.0) > 1200.0 and fmod(distance_traveled, 2000.0) < 1750.0
    var concrete := Color.html("#B4A992")
    var white := Color.html("#E4E2D6")
    for i in range(30, -1, -1):
        var z := 10.0 + float(i) * 24.0 - fmod(distance_traveled, 24.0)
        if z <= 2.0:
            continue
        var projection := project(z, 0.0)
        var p := float(projection["p"])
        var center := float(projection["center"])
        var half := float(projection["half"])
        var y := float(projection["y"])
        var left_x := center - half * 1.08
        var right_x := center + half * 1.08
        var post_w := maxf(2.0, 5.0 * p)
        var post_h := maxf(3.0, 20.0 * p)
        var color := white if bridge_zone else concrete
        draw_rect(Rect2(left_x - post_w, y - post_h, post_w, post_h), color)
        draw_rect(Rect2(right_x, y - post_h, post_w, post_h), color)
        if bridge_zone:
            draw_rect(Rect2(left_x - post_w * 1.6, y - post_h * 0.72, post_w * 2.6, maxf(1.0, 3.0 * p)), white)
            draw_rect(Rect2(right_x - post_w, y - post_h * 0.72, post_w * 2.6, maxf(1.0, 3.0 * p)), white)
        else:
            draw_rect(Rect2(left_x - post_w * 1.5, y - post_h * 0.55, post_w * 2.5, post_h * 0.55), concrete)
            draw_rect(Rect2(right_x - post_w, y - post_h * 0.55, post_w * 2.5, post_h * 0.55), concrete)

func _draw_objects() -> void:
    var sorted := objects.duplicate()
    sorted.sort_custom(Callable(self, "_sort_far_to_near"))
    for obj in sorted:
        var item: Dictionary = obj
        if not bool(item.get("active", true)):
            continue
        var z := float(item.get("z", 100.0))
        if z < -12.0 or z > 760.0:
            continue
        var lane_value := float(item.get("lane", 1.0))
        var projection := project(z, lane_x(lane_value))
        var p := float(projection["p"])
        var ground := Vector2(float(projection["x"]), float(projection["y"]) + 8.0 * p)
        var sprite_scale := float(projection["scale"])
        if bool(item.get("is_crash", false)):
            _draw_crash_composition(ground, sprite_scale, p)
        elif bool(item.get("is_rival", false)):
            var frame_name := String(item.get("frame", "riding/ride"))
            _draw_rider_sprite(frame_name, ground, sprite_scale * 0.92, clampf(p * 4.0, 0.35, 1.0))
            if debug_mode:
                _draw_object_debug(item, projection)
        else:
            var type_name := String(item.get("type", "car"))
            var angle_name := String(item.get("angle", "straight"))
            _draw_traffic_sprite(type_name, angle_name, ground, sprite_scale * 0.95, clampf(p * 4.0, 0.35, 1.0))
            if bool(item.get("is_police", false)):
                var flash := int(Time.get_ticks_msec() / 180) % 2 == 0
                var light_color := Color.html("#D53A34") if flash else Color.html("#3D6DD8")
                draw_rect(Rect2(ground.x - 9.0 * sprite_scale, ground.y - 76.0 * sprite_scale,
                    18.0 * sprite_scale, 6.0 * sprite_scale), light_color)
            if debug_mode:
                _draw_object_debug(item, projection)

func _draw_crash_composition(ground: Vector2, sprite_scale: float, p: float) -> void:
    _draw_rider_sprite("crash/slide", ground - Vector2(30.0 * sprite_scale, -4.0 * sprite_scale), sprite_scale * 0.88, 1.0)
    _draw_rider_sprite("crash/fall_2", ground + Vector2(38.0 * sprite_scale, -10.0 * sprite_scale), sprite_scale * 0.76, 1.0)
    var dust := Color(0.84, 0.76, 0.58, 0.75)
    draw_circle(ground + Vector2(4.0 * sprite_scale, -5.0 * sprite_scale), maxf(2.0, 8.0 * p), dust)
    draw_circle(ground + Vector2(18.0 * sprite_scale, -2.0 * sprite_scale), maxf(2.0, 6.0 * p), dust)
    draw_circle(ground + Vector2(-18.0 * sprite_scale, -3.0 * sprite_scale), maxf(2.0, 5.0 * p), dust)

func _atlas_frame_rect(info: Dictionary, frame_name: String) -> Rect2:
    var names: Array = info.get("frame_names", [])
    var idx := names.find(frame_name)
    if idx < 0:
        idx = 0
    var cols := maxi(1, int(info.get("columns", 1)))
    var fw := float(info.get("frame_width", 128))
    var fh := float(info.get("frame_height", 128))
    var col := idx % cols
    var row := int(floor(float(idx) / float(cols)))
    return Rect2(float(col) * fw, float(row) * fh, fw, fh)

func _draw_rider_sprite(frame_name: String, ground: Vector2, sprite_scale: float, alpha: float) -> void:
    if rider_sheet_tex == null:
        return
    var src := _atlas_frame_rect(rider_info, frame_name)
    var pivot: Array = rider_info.get("pivot", [64.0, 126.0])
    var px := float(pivot[0])
    var py := float(pivot[1])
    var fw := float(rider_info.get("frame_width", 128.0))
    var fh := float(rider_info.get("frame_height", 128.0))
    var w := fw * sprite_scale
    var h := fh * sprite_scale
    var dest := Rect2(ground.x - w * (px / fw), ground.y - h * (py / fh), w, h)
    draw_texture_rect_region(rider_sheet_tex, dest, src, Color(1.0, 1.0, 1.0, alpha))

func _draw_traffic_sprite(type_name: String, angle_name: String, ground: Vector2, sprite_scale: float, alpha: float) -> void:
    if traffic_sheet_tex == null:
        return
    var row := traffic_kinds.find(type_name)
    if row < 0:
        row = 0
    var col := traffic_angles.find(angle_name)
    if col < 0:
        col = 0
    var fw := float(traffic_info.get("frame_width", 128.0))
    var fh := float(traffic_info.get("frame_height", 96.0))
    var src := Rect2(float(col) * fw, float(row) * fh, fw, fh)
    var pivot: Array = traffic_info.get("pivot", [64.0, 94.0])
    var px := float(pivot[0])
    var py := float(pivot[1])
    var w := fw * sprite_scale
    var h := fh * sprite_scale
    var dest := Rect2(ground.x - w * (px / fw), ground.y - h * (py / fh), w, h)
    draw_texture_rect_region(traffic_sheet_tex, dest, src, Color(1.0, 1.0, 1.0, alpha))

func _draw_object_debug(item: Dictionary, projection: Dictionary) -> void:
    var p := float(projection["p"])
    var x := float(projection["x"])
    var y := float(projection["y"])
    var half := float(projection["half"])
    var width_world := float(item.get("collision_width", 2.0))
    var length_world := float(item.get("collision_length", 4.5))
    var w := width_world * (half / ROAD_HALF_WIDTH_WORLD)
    var h := maxf(4.0, length_world * p * 3.0)
    draw_rect(Rect2(x - w * 0.5, y - h * 0.5, w, h), Color(1.0, 0.2, 0.2, 0.65), false, 2.0)
    _draw_text(Vector2(x + w * 0.5 + 4.0, y - h * 0.5), "z=" + str(int(float(item.get("z", 0.0)))) + "  lane=" + str(snappedf(float(item.get("lane", 1.0)), 0.1)),
        12, Color(1.0, 0.95, 0.7, 0.9))

func _draw_cockpit() -> void:
    if cockpit_tex == null:
        return
    var top_y := float(cockpit_info.get("top_y", 500.0))
    draw_texture_rect(cockpit_tex, Rect2(0.0, top_y, W, 220.0), false)
    var left_center := _vec2_from_manifest(cockpit_info.get("gauge_left", [460, 140]))
    var right_center := _vec2_from_manifest(cockpit_info.get("gauge_right", [820, 140]))
    var gear_center := _vec2_from_manifest(cockpit_info.get("gear_center", [640, 140]))
    left_center.y += top_y
    right_center.y += top_y
    gear_center.y += top_y
    var radius := float(cockpit_info.get("gauge_radius", 68.0))
    # Mask static base values, then draw live values. This keeps gauge artwork
    # fixed while speed, RPM, gear and indicators remain real gameplay state.
    draw_rect(Rect2(gear_center.x - 24.0, gear_center.y - 28.0, 48.0, 56.0), Color(0.055, 0.05, 0.055, 1.0))
    draw_rect(Rect2(left_center.x - 62.0, left_center.y + 26.0, 124.0, 24.0), Color(0.16, 0.15, 0.15, 0.92))
    draw_rect(Rect2(right_center.x - 62.0, right_center.y + 26.0, 124.0, 24.0), Color(0.16, 0.15, 0.15, 0.92))
    _draw_needle(left_center, radius, clampf(speed * 3.6 / 320.0, 0.0, 1.0))
    _draw_needle(right_center, radius, clampf(rpm, 0.0, 1.0), Color.html("#8D2A22"))
    _draw_centered_text(gear_center + Vector2(0.0, 12.0), str(gear), 42, Color.html("#EDE8D8"), 120.0)
    _draw_centered_text(left_center + Vector2(0.0, 43.0), str(int(speed * 3.6)) + " KM/H", 17, Color.html("#EDE8D8"), 130.0)
    _draw_centered_text(right_center + Vector2(0.0, 43.0), "%.1f RPM" % (rpm * 9.0), 17, Color.html("#EDE8D8"), 130.0)
    var boost_width := 220.0 * clampf(boost, 0.0, 1.0)
    draw_rect(Rect2(W * 0.5 - 110.0, H - 12.0, 220.0, 7.0), Color(0.08, 0.08, 0.09, 1.0))
    draw_rect(Rect2(W * 0.5 - 110.0, H - 12.0, boost_width, 7.0), Color.html("#42B0E8"))
    # Indicator lights use live simulation state.
    var throttle_active := speed > 1.0 and (test_input == null or float(_read_input()["throttle"]) > 0.05)
    var brake_active := float(_read_input()["brake"]) > 0.05
    _draw_indicator_light(Vector2(184.0, top_y + 132.0), throttle_active, Color.html("#3DBE5A"))
    _draw_indicator_light(Vector2(184.0, top_y + 168.0), brake_active, Color.html("#D0443B"))
    _draw_indicator_light(Vector2(1012.0, top_y + 132.0), boost > 0.05, Color.html("#3F79D6"))
    _draw_indicator_light(Vector2(1012.0, top_y + 168.0), police_level > 0, Color.html("#DDB33B"))

func _vec2_from_manifest(value: Variant) -> Vector2:
    if not (value is Array):
        return Vector2.ZERO
    var arr: Array = value
    if arr.size() < 2:
        return Vector2.ZERO
    return Vector2(float(arr[0]), float(arr[1]))

func _draw_needle(center: Vector2, radius: float, value: float, color: Color = Color(0.807, 0.235, 0.192, 1.0)) -> void:
    var start_deg := float(cockpit_info.get("needle_start_deg", 135.0))
    var end_deg := float(cockpit_info.get("needle_end_deg", 405.0))
    var angle := deg_to_rad(lerpf(start_deg, end_deg, clampf(value, 0.0, 1.0)))
    var tip := center + Vector2(cos(angle), sin(angle)) * radius * 0.72
    draw_line(center, tip, color, 4.0)
    draw_circle(center, 6.0, Color(0.10, 0.09, 0.09))

func _draw_indicator_light(center: Vector2, active: bool, color: Color) -> void:
    var rect := Rect2(center.x - 30.0, center.y - 5.0, 10.0, 10.0)
    draw_rect(rect, Color(0.12, 0.11, 0.12, 1.0))
    if active:
        draw_rect(rect.grow(-2.0), color)

func _draw_hud() -> void:
    var panel_color := Color(0.045, 0.045, 0.055, 0.76)
    draw_rect(Rect2(16.0, 14.0, 250.0, 82.0), panel_color)
    draw_rect(Rect2(16.0, 14.0, 250.0, 82.0), Color.html("#D9B51F"), false, 2.0)
    _draw_text(Vector2(28.0, 38.0), "POS  %d/4" % position_value, 20, Color.html("#EDE8D8"))
    _draw_text(Vector2(28.0, 65.0), "TIME %s" % _format_time(race_time), 18, Color.html("#DDD8C5"))
    var progress := clampf(distance_traveled / FINISH_DISTANCE, 0.0, 1.0)
    draw_rect(Rect2(28.0, 84.0, 220.0, 5.0), Color(0.15, 0.14, 0.16, 1.0))
    draw_rect(Rect2(28.0, 84.0, 220.0 * progress, 5.0), Color.html("#D9B51F"))
    var message := warning_message
    if warning_timer <= 0.0 and police_level > 0:
        message = "POLICE PURSUIT LEVEL " + str(police_level)
    if message != "":
        draw_rect(Rect2(W - 410.0, 14.0, 394.0, 58.0), Color(0.12, 0.04, 0.04, 0.80))
        draw_rect(Rect2(W - 410.0, 14.0, 394.0, 58.0), Color.html("#CE3C31"), false, 2.0)
        _draw_text(Vector2(W - 397.0, 44.0), message, 17, Color.html("#EDE8D8"))
    _draw_centered_text(Vector2(W * 0.5, 24.0), "HYBRID 2.5D BENCHMARK", 14, Color(0.92, 0.90, 0.84, 0.55), 300.0)

func _draw_state_overlays() -> void:
    if state == State.CRASHED:
        draw_rect(Rect2(0.0, 0.0, W, H), Color(0.65, 0.08, 0.05, 0.16))
        _draw_rider_sprite("crash/slide", Vector2(W * 0.47, H * 0.86), 2.9, 1.0)
        _draw_rider_sprite("crash/fall_2", Vector2(W * 0.60, H * 0.84), 2.25, 1.0)
        _draw_centered_text(Vector2(W * 0.5, 220.0), "WIPEOUT!", 64, Color.html("#FFFFFF"), 500.0)
        _draw_centered_text(Vector2(W * 0.5, 280.0), crash_reason, 22, Color.html("#FFD9A0"), 600.0)
    elif state == State.HOSPITAL:
        draw_rect(Rect2(0.0, 0.0, W, H), Color(0.91, 0.89, 0.82, 0.55))
        draw_rect(Rect2(170.0, 90.0, 940.0, 500.0), Color(0.07, 0.09, 0.08, 0.92))
        draw_rect(Rect2(170.0, 90.0, 940.0, 500.0), Color.html("#EDE8D8"), false, 3.0)
        _draw_centered_text(Vector2(W * 0.5, 145.0), "THE ASPHALT SAID NO!", 42, Color.html("#F0C73A"), 800.0)
        _draw_centered_text(Vector2(W * 0.5, 200.0), "HOSPITAL — CAIRO RING ROAD WARD 7", 20, Color.html("#DDD8C5"), 700.0)
        _draw_centered_text(Vector2(W * 0.5, 260.0), "CRASH REPORT: " + crash_reason, 24, Color.html("#FF8B75"), 800.0)
        _draw_centered_text(Vector2(W * 0.5, 318.0), "No graphic injuries — just a bruised ego, a bent exhaust and a very loud nurse.", 18, Color.html("#EDE8D8"), 880.0)
        _draw_centered_text(Vector2(W * 0.5, 355.0), "The doctor says: next time, brake before the microbus, ya batal!", 18, Color.html("#EDE8D8"), 880.0)
        _draw_centered_text(Vector2(W * 0.5, 412.0), "POS %d/4   TIME %s   TOP SPEED %.0f km/h" % [position_value, _format_time(race_time), speed * 3.6], 20, Color.html("#D9B51F"), 800.0)
        _draw_centered_text(Vector2(W * 0.5, 470.0), "PRESS R TO RETRY", 28, Color.html("#FFFFFF"), 500.0)
        _draw_rider_sprite("crash/defeat", Vector2(W * 0.5, 555.0), 1.35, 1.0)
    elif state == State.FINISHED:
        draw_rect(Rect2(0.0, 0.0, W, H), Color(0.03, 0.04, 0.06, 0.55))
        draw_rect(Rect2(280.0, 170.0, 720.0, 340.0), Color(0.06, 0.06, 0.08, 0.92))
        draw_rect(Rect2(280.0, 170.0, 720.0, 340.0), Color.html("#D9B51F"), false, 3.0)
        _draw_centered_text(Vector2(W * 0.5, 225.0), "RACE COMPLETE", 46, Color.html("#F0C73A"), 650.0)
        _draw_centered_text(Vector2(W * 0.5, 292.0), "FINAL POSITION  %d / 4" % finish_position, 26, Color.html("#EDE8D8"), 600.0)
        _draw_centered_text(Vector2(W * 0.5, 340.0), "TIME %s   DISTANCE %.0f m" % [_format_time(race_time), distance_traveled], 22, Color.html("#DDD8C5"), 650.0)
        _draw_centered_text(Vector2(W * 0.5, 410.0), "PRESS R TO RACE AGAIN", 26, Color.html("#FFFFFF"), 550.0)

func _draw_debug() -> void:
    var panel := Rect2(16.0, 104.0, 390.0, 132.0)
    draw_rect(panel, Color(0.02, 0.02, 0.03, 0.82))
    draw_rect(panel, Color.html("#42B0E8"), false, 2.0)
    _draw_text(Vector2(28.0, 128.0), "ROAD-RELATIVE DEBUG", 16, Color.html("#7DD4FF"))
    _draw_text(Vector2(28.0, 154.0), "speed=%.1f m/s  gear=%d  rpm=%.2f" % [speed, gear, rpm], 15, Color.html("#EDE8D8"))
    _draw_text(Vector2(28.0, 178.0), "distance=%.1f m  lane=%.2f  lateral=%.2f" % [distance_traveled, player_lane_value(), lateral], 15, Color.html("#EDE8D8"))
    _draw_text(Vector2(28.0, 202.0), "police=%d  collisions=%d  near_misses=%d" % [police_level, collision_count, near_miss_count], 15, Color.html("#EDE8D8"))
    _draw_text(Vector2(28.0, 226.0), "objects=%d  state=%d  curve=%.1f" % [objects.size(), state, curve_offset(distance_traveled)], 15, Color.html("#EDE8D8"))
    var player_projection := project(2.0, lateral)
    var px := float(player_projection["x"])
    var py := float(player_projection["y"])
    draw_rect(Rect2(px - 14.0, py - 10.0, 28.0, 20.0), Color(0.2, 1.0, 0.4, 0.8), false, 2.0)

func _draw_text(position_value: Vector2, text_value: String, font_size: int, color: Color) -> void:
    if font != null:
        draw_string(font, position_value, text_value, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)

func _draw_centered_text(center: Vector2, text_value: String, font_size: int, color: Color, width_value: float) -> void:
    if font == null:
        return
    draw_string(font, Vector2(center.x - width_value * 0.5, center.y), text_value,
        HORIZONTAL_ALIGNMENT_CENTER, width_value, font_size, color)

func _format_time(seconds: float) -> String:
    var minutes := int(seconds / 60.0)
    var remainder := fmod(seconds, 60.0)
    return "%02d:%04.1f" % [minutes, remainder]

func set_test_input(value: Variant) -> void:
    test_input = value
    benchmark_mode = false

func advance_simulation(seconds: float) -> void:
    # Deterministic fixed-step hook for headless tests; still uses the exact
    # same _update_simulation() path as interactive play.
    benchmark_mode = false
    if state != State.RACING:
        state = State.RACING
    var steps := maxi(1, int(seconds * 60.0))
    for i in range(steps):
        _update_simulation(1.0 / 60.0)
    queue_redraw()

func set_benchmark_state(mode: String) -> void:
    benchmark_mode = true
    debug_mode = false
    state = State.RACING
    speed = 52.0
    max_speed = 72.0
    boost = 0.72
    gear = 3
    rpm = 0.62
    lateral = -1.8
    steer = 0.08
    distance_traveled = 420.0
    race_time = 42.7
    position_value = 2
    police_level = 1
    crash_reason = ""
    crash_severity = 0
    crash_timer = 1.2
    warning_message = "POLICE PURSUIT LEVEL 1"
    warning_timer = 4.0
    _spawn_initial_objects()
    if mode == "moving":
        distance_traveled = 540.0
        race_time = 48.2
        speed = 61.0
        gear = 4
        rpm = 0.78
        lateral = -0.8
        for obj in objects:
            var item: Dictionary = obj
            item["z"] = float(item.get("z", 100.0)) - 26.0 + rng.randf_range(-4.0, 4.0)
            if bool(item.get("is_rival", false)):
                item["frame"] = "riding/lean_right" if float(item.get("lane", 1.0)) > 1.5 else "riding/accelerate"
    elif mode == "crash":
        state = State.CRASHED
        crash_reason = "Collided with microbus"
        crash_severity = 3
        speed = 18.0
        gear = 2
        rpm = 0.35
        warning_message = "WIPEOUT: " + crash_reason
    elif mode == "hospital":
        state = State.HOSPITAL
        crash_reason = "Collided with microbus"
        crash_severity = 3
        speed = 0.0
        warning_message = "HOSPITAL — " + crash_reason
    elif mode == "finish":
        state = State.FINISHED
        distance_traveled = FINISH_DISTANCE
        race_time = 61.5
        position_value = 2
        finish_position = 2
        warning_message = "RACE COMPLETE — POSITION 2"
    elif mode == "debug":
        debug_mode = true
        police_level = 2
        warning_message = "POLICE PURSUIT LEVEL 2"
    queue_redraw()

func get_debug_state() -> Dictionary:
    return {
        "state": int(state),
        "state_name": ["RACING", "CRASHED", "HOSPITAL", "FINISHED"][int(state)],
        "speed": speed,
        "gear": gear,
        "rpm": rpm,
        "lateral": lateral,
        "lane": player_lane_value(),
        "distance": distance_traveled,
        "race_time": race_time,
        "position": position_value,
        "police_level": police_level,
        "collision_count": collision_count,
        "near_miss_count": near_miss_count,
        "crash_severity": crash_severity,
        "crash_reason": crash_reason,
        "finish_position": finish_position,
        "objects": objects.size(),
        "benchmark_mode": benchmark_mode,
    }
