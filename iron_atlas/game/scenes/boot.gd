extends Node


func _ready() -> void:
	# Scene replacement during _ready can collide with the initial root setup.
	get_tree().call_deferred("change_scene_to_file", "res://scenes/main_menu.tscn")
