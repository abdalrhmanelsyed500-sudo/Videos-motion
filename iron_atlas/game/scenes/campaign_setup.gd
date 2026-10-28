extends Control

var seed_edit: LineEdit
var err_label: Label


func _ready() -> void:
	var vbox := VBoxContainer.new()
	vbox.position = Vector2(420, 200)
	vbox.size = Vector2(440, 300)
	add_child(vbox)
	var head := Label.new()
	head.text = "New Campaign — Republic of Vardena crisis"
	head.add_theme_font_size_override("font_size", 22)
	vbox.add_child(head)
	var row := HBoxContainer.new()
	vbox.add_child(row)
	row.add_child(Label.new())
	row.get_child(0).set_meta("t", "seed")
	(row.get_child(0) as Label).text = "World seed:"
	seed_edit = LineEdit.new()
	seed_edit.text = str(Time.get_unix_time_from_system() % 100000)
	seed_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(seed_edit)
	var btn := Button.new()
	btn.text = "Start Campaign"
	btn.pressed.connect(_on_start)
	vbox.add_child(btn)
	err_label = Label.new()
	err_label.add_theme_color_override("font_color", Color(0.9, 0.4, 0.3))
	vbox.add_child(err_label)
	var back := Button.new()
	back.text = "Back"
	back.pressed.connect(func(): get_tree().change_scene_to_file("res://scenes/main_menu.tscn"))
	vbox.add_child(back)


func _on_start() -> void:
	var s := seed_edit.text.strip_edges()
	var seed_int := 0
	if s.is_valid_int():
		seed_int = s.to_int()
	else:
		# string seeds hash deterministically
		seed_int = s.hash()
	var err := GameState.new_campaign(seed_int)
	if err != "":
		err_label.text = err
		return
	get_tree().change_scene_to_file("res://scenes/world_map.tscn")
