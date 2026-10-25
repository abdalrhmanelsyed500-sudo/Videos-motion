extends Control
## Start screen: title, one-line pitch, start button / Enter. Loads the P1 district scene.

const DISTRICT_SCENE := "res://scenes/world/district_p1.tscn"


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Color("1d3a4a")
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var title := Label.new()
	title.text = "EGYPTIAN TUKTUK MAYHEM"
	title.position = Vector2(240, 180)
	title.add_theme_font_size_override("font_size", 54)
	title.add_theme_color_override("font_color", Color("ffe14d"))
	title.add_theme_color_override("font_outline_color", Color.BLACK)
	title.add_theme_constant_override("outline_size", 8)
	add_child(title)
	var sub := Label.new()
	sub.text = ("Phase 1 playable core - Mit Okba trial block\n"
		+ "Pick up, deliver, earn. Watch the clock, mind the alley.")
	sub.position = Vector2(250, 260)
	sub.add_theme_font_size_override("font_size", 22)
	sub.add_theme_color_override("font_color", Color.WHITE)
	add_child(sub)
	var btn := Button.new()
	btn.text = "Start driving  [Enter]"
	btn.position = Vector2(520, 380)
	btn.pressed.connect(_start)
	add_child(btn)
	var cred := Label.new()
	cred.text = "Original game - no third-party assets. Godot 4.7.2 Compatibility."
	cred.position = Vector2(250, 640)
	cred.add_theme_font_size_override("font_size", 14)
	cred.add_theme_color_override("font_color", Color("9fb6c4"))
	add_child(cred)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("start_game") or event.is_action_pressed("ui_accept"):
		_start()


func _start() -> void:
	get_tree().change_scene_to_packed(load(DISTRICT_SCENE))
