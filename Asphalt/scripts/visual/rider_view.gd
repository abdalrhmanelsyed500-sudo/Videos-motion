extends Node3D
class_name AGRiderView
## Procedural articulated rider; all pivots remain available for crash/fall animation.

var hips: Node3D
var torso: Node3D
var head: Node3D
var left_arm: Node3D
var right_arm: Node3D
var left_leg: Node3D
var right_leg: Node3D
var crashing := false
var phase := 0.0

func configure(parts: Dictionary) -> void:
    hips = parts.get("hips")
    torso = parts.get("torso")
    head = parts.get("head")
    left_arm = parts.get("left_arm")
    right_arm = parts.get("right_arm")
    left_leg = parts.get("left_leg")
    right_leg = parts.get("right_leg")
    apply_riding_pose()

func apply_riding_pose() -> void:
    if torso != null:
        torso.rotation = Vector3(-0.27, 0.0, 0.0)
    if head != null:
        head.rotation = Vector3(0.18, 0.0, 0.0)
    if left_arm != null:
        left_arm.rotation = Vector3(-0.12, -0.12, -0.10)
    if right_arm != null:
        right_arm.rotation = Vector3(-0.12, 0.12, 0.10)
    if left_leg != null:
        left_leg.rotation = Vector3(0.05, 0.0, -0.08)
    if right_leg != null:
        right_leg.rotation = Vector3(0.05, 0.0, 0.08)

func set_pose(steer: float, speed: float, throttle: float, brake: float, delta: float) -> void:
    if crashing:
        return
    phase += delta * (2.0 + speed * 0.06)
    var bob := sin(phase) * 0.012 * clampf(speed / 50.0, 0.0, 1.0)
    if torso != null:
        torso.rotation.x = lerpf(torso.rotation.x, -0.27 - throttle * 0.08 + brake * 0.14, 1.0 - exp(-8.0 * delta))
        torso.rotation.z = lerpf(torso.rotation.z, -steer * 0.10, 1.0 - exp(-7.0 * delta))
        torso.position.y = 0.30 + bob
    if head != null:
        head.rotation.y = lerpf(head.rotation.y, -steer * 0.28, 1.0 - exp(-9.0 * delta))
        head.rotation.x = lerpf(head.rotation.x, 0.18 - brake * 0.12, 1.0 - exp(-7.0 * delta))
    if left_arm != null:
        left_arm.rotation.y = lerpf(left_arm.rotation.y, -0.12 + steer * 0.22, 1.0 - exp(-10.0 * delta))
    if right_arm != null:
        right_arm.rotation.y = lerpf(right_arm.rotation.y, 0.12 + steer * 0.22, 1.0 - exp(-10.0 * delta))
    if left_leg != null:
        left_leg.rotation.x = 0.05 + bob * 0.7
    if right_leg != null:
        right_leg.rotation.x = 0.05 - bob * 0.7

func play_fall(direction: float = 1.0) -> void:
    if crashing:
        return
    crashing = true
    var tween := create_tween()
    tween.set_parallel(true)
    tween.tween_property(self, "rotation:x", -1.05, 0.75)
    tween.tween_property(self, "rotation:z", direction * 1.35, 0.75)
    tween.tween_property(self, "position:y", position.y - 0.72, 0.75)
    tween.tween_property(self, "position:x", position.x + direction * 1.15, 0.75)
    tween.tween_property(self, "position:z", position.z - 0.85, 0.75)
