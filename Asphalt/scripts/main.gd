extends Node
## Top-level scene flow, pause handling and persistent settings/results.

var world_root: Node3D
var screen_layer: CanvasLayer
var race_world: Node3D
var is_paused := false
var settings_from_pause := false

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	world_root = Node3D.new()
	world_root.name = "WorldRoot"
	add_child(world_root)
	screen_layer = CanvasLayer.new()
	screen_layer.name = "ScreenLayer"
	screen_layer.layer = 10
	screen_layer.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(screen_layer)
	var state_node := AGState.node()
	if state_node != null and state_node.has_signal("settings_changed"):
		state_node.connect("settings_changed", Callable(self, "_on_settings_changed"))
	AGSettings.apply()
	show_screen("main_menu")

func clear_screens(keep_paused := false) -> void:
	for child in screen_layer.get_children():
		child.queue_free()
	if not keep_paused and get_tree().paused:
		get_tree().paused = false
		is_paused = false

func show_screen(screen_name: String, result_data: Dictionary = {}, keep_paused := false) -> Control:
	clear_screens(keep_paused)
	var path := "res://scenes/ui/" + screen_name + ".tscn"
	var packed: PackedScene = load(path)
	if packed == null:
		push_error("Missing UI scene: " + path)
		return null
	var screen := packed.instantiate()
	if not result_data.is_empty() and screen.has_method("set_result"):
		screen.call("set_result", result_data)
	screen_layer.add_child(screen)
	if screen is Control:
		(screen as Control).set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_connect_screen(screen)
	return screen

func _connect_screen(screen: Node) -> void:
	_connect(screen, "start_race", "_on_start_race")
	_connect(screen, "rider_select", "_show_rider_select")
	_connect(screen, "bike_select", "_show_bike_select")
	_connect(screen, "settings", "_on_settings_requested")
	_connect(screen, "quit_game", "_on_quit_game")
	_connect(screen, "back_to_menu", "_on_back_to_menu")
	_connect(screen, "back_to_riders", "_show_rider_select")
	_connect(screen, "continue_to_bikes", "_show_bike_select")
	_connect(screen, "rider_chosen", "_on_rider_chosen")
	_connect(screen, "bike_chosen", "_on_bike_chosen")
	_connect(screen, "resume", "_resume_game")
	_connect(screen, "restart", "_on_start_race")
	_connect(screen, "quit_to_menu", "_show_main_menu")
	_connect(screen, "toggle_camera", "_toggle_camera")
	_connect(screen, "retry", "_on_start_race")
	_connect(screen, "menu", "_show_main_menu")

func _connect(screen: Node, signal_name: String, method_name: String) -> void:
	if screen.has_signal(signal_name):
		screen.connect(signal_name, Callable(self, method_name))

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause") and race_world != null:
		if is_paused:
			_resume_game()
		else:
			_pause_game()
	elif event.is_action_pressed("camera_toggle") and race_world != null and not is_paused:
		_toggle_camera()

func _pause_game() -> void:
	if race_world == null or is_paused:
		return
	is_paused = true
	get_tree().paused = true
	show_screen("pause_menu", {}, true)

func _resume_game() -> void:
	is_paused = false
	settings_from_pause = false
	get_tree().paused = false
	clear_screens(false)

func _toggle_camera() -> void:
	if race_world == null:
		return
	var target_camera: Variant = race_world.get("camera")
	if target_camera != null and target_camera is Node and target_camera.has_method("toggle_mode"):
		target_camera.call("toggle_mode")

func remove_world() -> void:
	AGAudio.stop_race_audio()
	if race_world != null and is_instance_valid(race_world):
		race_world.queue_free()
	race_world = null

func _on_start_race() -> void:
	is_paused = false
	settings_from_pause = false
	get_tree().paused = false
	remove_world()
	var packed: PackedScene = load("res://scenes/race_world.tscn")
	if packed == null:
		push_error("Missing race world scene")
		return
	race_world = packed.instantiate()
	world_root.add_child(race_world)
	_connect(race_world, "race_finished", "_on_race_finished")
	_connect(race_world, "hospital_requested", "_on_hospital_requested")
	clear_screens(false)
	AGSettings.apply()

func _on_race_finished(result: Dictionary) -> void:
	AGState.record_result(result)
	var display_result := AGState.last_result()
	if display_result.is_empty():
		display_result = result
	remove_world()
	show_screen("results_screen", display_result)

func _on_hospital_requested(result: Dictionary) -> void:
	AGState.record_result(result)
	var display_result := AGState.last_result()
	if display_result.is_empty():
		display_result = result
	remove_world()
	show_screen("hospital_screen", display_result)

func _show_main_menu() -> void:
	is_paused = false
	settings_from_pause = false
	get_tree().paused = false
	remove_world()
	show_screen("main_menu")

func _show_rider_select() -> void:
	show_screen("rider_select")

func _show_bike_select() -> void:
	show_screen("bike_select")

func _on_settings_requested() -> void:
	settings_from_pause = is_paused
	show_screen("settings_menu", {}, is_paused)

func _on_back_to_menu() -> void:
	if settings_from_pause and is_paused:
		settings_from_pause = false
		show_screen("pause_menu", {}, true)
	else:
		_show_main_menu()

func _on_rider_chosen(_index: int) -> void:
	pass

func _on_bike_chosen(_index: int) -> void:
	pass

func _on_settings_changed() -> void:
	AGSettings.apply()

func _on_quit_game() -> void:
	get_tree().quit()
