extends Node3D
class_name AGBikeView
## Visual state for a procedurally assembled motorcycle.

var front_wheel: Node3D
var rear_wheel: Node3D
var steering: Node3D
var rider_anchor: Node3D
var body: Node3D
var wheel_radius := 0.34
var wheel_angle := 0.0
var current_lean := 0.0
var current_pitch := 0.0
var crashing := false

func set_motion(speed: float, steer: float, throttle: float, brake: float, delta: float) -> void:
    if crashing:
        return
    wheel_angle += (speed / maxf(wheel_radius, 0.1)) * delta
    if front_wheel != null:
        front_wheel.rotation.x = wheel_angle
    if rear_wheel != null:
        rear_wheel.rotation.x = wheel_angle
    var speed_factor := clampf(speed / 55.0, 0.0, 1.0)
    var target_lean := -steer * speed_factor * 0.42
    var target_pitch := -throttle * 0.035 + brake * 0.075
    current_lean = lerpf(current_lean, target_lean, 1.0 - exp(-8.0 * delta))
    current_pitch = lerpf(current_pitch, target_pitch, 1.0 - exp(-6.0 * delta))
    if body != null:
        body.rotation.z = current_lean
        body.rotation.x = current_pitch
        body.position.y = sin(wheel_angle * 0.5) * 0.012 * speed_factor
    if steering != null:
        steering.rotation.y = lerpf(steering.rotation.y, steer * 0.34, 1.0 - exp(-10.0 * delta))

func play_slide(direction: float = 1.0) -> void:
    if crashing:
        return
    crashing = true
    var tween := create_tween()
    tween.tween_property(body, "rotation:z", direction * 1.25, 0.55)
    tween.tween_property(body, "position:z", -2.2, 0.9)
    tween.tween_property(body, "position:x", direction * 1.6, 0.9)

func reset_pose() -> void:
    crashing = false
    if body != null:
        body.rotation = Vector3.ZERO
        body.position = Vector3.ZERO
    if steering != null:
        steering.rotation = Vector3.ZERO
