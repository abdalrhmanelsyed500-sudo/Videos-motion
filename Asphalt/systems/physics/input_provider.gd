extends RefCounted
class_name AGInputProvider
## Keyboard input with optional gamepad axes. Tests can inject a dictionary.

static func read(controller) -> Dictionary:
    if controller.test_input != null:
        return _normalized(controller.test_input)
    var result := {
        "throttle": Input.get_action_strength("throttle"),
        "brake": Input.get_action_strength("brake"),
        "steer": Input.get_action_strength("steer_right") - Input.get_action_strength("steer_left"),
        "handbrake": Input.get_action_strength("handbrake"),
        "boost": Input.get_action_strength("boost"),
    }
    if Input.get_connected_joypads().size() > 0:
        result["throttle"] = maxf(float(result["throttle"]), maxf(0.0, Input.get_joy_axis(0, 5)))
        result["brake"] = maxf(float(result["brake"]), maxf(0.0, Input.get_joy_axis(0, 4)))
        var axis := Input.get_joy_axis(0, 0)
        if absf(axis) > 0.14:
            result["steer"] = clampf(axis, -1.0, 1.0)
        if Input.is_joy_button_pressed(0, 1):
            result["boost"] = 1.0
        if Input.is_joy_button_pressed(0, 0):
            result["handbrake"] = 1.0
    return _normalized(result)

static func _normalized(input: Dictionary) -> Dictionary:
    return {
        "throttle": clampf(float(input.get("throttle", 0.0)), 0.0, 1.0),
        "brake": clampf(float(input.get("brake", 0.0)), 0.0, 1.0),
        "steer": clampf(float(input.get("steer", 0.0)), -1.0, 1.0),
        "handbrake": clampf(float(input.get("handbrake", 0.0)), 0.0, 1.0),
        "boost": clampf(float(input.get("boost", 0.0)), 0.0, 1.0),
    }
