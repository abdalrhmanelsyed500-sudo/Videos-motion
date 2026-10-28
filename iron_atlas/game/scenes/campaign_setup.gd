extends Control
const UiStyle = preload("res://core/ui_style.gd")

var seed_edit: LineEdit
var err_label: Label
var world_size: OptionButton


func _ready() -> void:
	theme = UiStyle.make_theme()
	var vbox := VBoxContainer.new()
	vbox.position = Vector2(420, 185)
	vbox.size = Vector2(440, 420)
	vbox.add_theme_constant_override("separation", 12)
	add_child(vbox)
	var eyebrow := Label.new()
	eyebrow.text = "CAMPAIGN SETUP   /   VARDENA"
	eyebrow.add_theme_font_size_override("font_size", 13)
	eyebrow.add_theme_color_override("font_color", Color(0.76, 0.72, 0.50))
	vbox.add_child(eyebrow)
	var head := Label.new()
	head.text = "The Constitutional Crisis"
	head.add_theme_font_size_override("font_size", 25)
	vbox.add_child(head)
	var summary := Label.new()
	summary.text = "Begin with 60 fighters. Recruit, secure supplies and build local support."
	summary.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	summary.add_theme_color_override("font_color", Color(0.65, 0.71, 0.65))
	vbox.add_child(summary)
	var row := HBoxContainer.new()
	vbox.add_child(row)
	var seed_label := Label.new()
	seed_label.text = "World seed:  "
	row.add_child(seed_label)
	seed_edit = LineEdit.new()
	seed_edit.text = str(int(Time.get_unix_time_from_system()) % 100000)
	seed_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(seed_edit)
	var world_row := HBoxContainer.new()
	vbox.add_child(world_row)
	var world_label := Label.new()
	world_label.text = "Regional map:  "
	world_row.add_child(world_label)
	world_size = OptionButton.new()
	world_size.add_item("200 districts (Stage 2)", 200)
	world_size.add_item("24 districts (classic)", 24)
	world_size.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	world_row.add_child(world_size)
	var btn := Button.new()
	btn.text = "START CAMPAIGN"
	btn.custom_minimum_size.y = 42
	btn.pressed.connect(_on_start)
	vbox.add_child(btn)
	err_label = Label.new()
	err_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	err_label.add_theme_color_override("font_color", Color(0.9, 0.4, 0.3))
	vbox.add_child(err_label)
	var back := Button.new()
	back.text = "BACK"
	back.pressed.connect(func(): get_tree().change_scene_to_file("res://scenes/main_menu.tscn"))
	vbox.add_child(back)


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.07, 0.10, 0.09))
	for x in range(0, 1280, 48):
		draw_line(Vector2(x, 0), Vector2(x, 720), Color(0.13, 0.17, 0.15, 0.35))
	for y in range(0, 720, 48):
		draw_line(Vector2(0, y), Vector2(1280, y), Color(0.13, 0.17, 0.15, 0.35))
	draw_rect(Rect2(374, 145, 532, 490), Color(0.09, 0.13, 0.11, 0.97))
	draw_rect(Rect2(374, 145, 532, 490), Color(0.31, 0.37, 0.29), false, 1.0)
	draw_rect(Rect2(374, 145, 5, 490), Color(0.68, 0.63, 0.39))


func _on_start() -> void:
	var s := seed_edit.text.strip_edges()
	var seed_int := 0
	if s.is_valid_int():
		seed_int = s.to_int()
	else:
		seed_int = s.hash()
	var err := GameState.new_campaign(seed_int, world_size.get_selected_id())
	if err != "":
		err_label.text = err
		return
	get_tree().change_scene_to_file("res://scenes/world_map.tscn")
