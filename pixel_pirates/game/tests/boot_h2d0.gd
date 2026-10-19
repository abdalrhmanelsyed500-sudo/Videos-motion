extends SceneTree
## Boots the real scene headless and runs N frames: godot --headless --fixed-fps 60 --path game --script res://tests/boot_h2d0.gd
var frames := 0
var scene: Node


func _initialize() -> void:
	var ps := load("res://h2d/h2d0.tscn") as PackedScene
	print("BOOT scene loaded: ", ps != null)
	scene = ps.instantiate()
	root.add_child(scene)
	print("BOOT scene added")


func _process(_delta: float) -> bool:
	frames += 1
	if frames == 30:
		var pg: Node = scene.get("_port")
		print("BOOT port controller: ", pg != null, " enabled=", pg.get("enabled") if pg != null else "-")
		quit(0)
	return false
