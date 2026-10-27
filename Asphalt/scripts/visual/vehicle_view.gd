extends Node3D
class_name AGVehicleView
## Visual wheel rotation and police beacon animation for traffic models.

var wheels: Array = []
var wheel_radius := 0.36
var beacon_red: MeshInstance3D
var beacon_blue: MeshInstance3D
var wheel_angle := 0.0

func set_motion(speed: float, delta: float) -> void:
    wheel_angle += speed * delta / maxf(wheel_radius, 0.1)
    for wheel in wheels:
        wheel.rotation.x = wheel_angle
    if beacon_red != null and beacon_blue != null:
        var flip := (Time.get_ticks_msec() / 180) % 2 == 0
        beacon_red.visible = flip
        beacon_blue.visible = not flip
