extends Control
const PixelArt = preload("res://core/pixel_art.gd")
const UiStyle = preload("res://core/ui_style.gd")

var title_label: Label
var btn_new: Button
var btn_load: Button
var slots_label: Label
var art: Dictionary = {}


func _ready() -> void:
	theme = UiStyle.make_theme()
	for name in ["t_grass", "t_forest", "t_hills", "t_urban", "t_desert", "t_mountain", "t_water"]:
		art[name] = PixelArt.texture("res://assets/sprites/terrain/" + name + ".png")
	for name in ["tank_main", "truck", "infantry"]:
		art[name] = PixelArt.texture("res://assets/sprites/units/" + name + ".png")
	var vbox := VBoxContainer.new()
	vbox.position = Vector2(90, 148)
	vbox.size = Vector2(440, 490)
	vbox.add_theme_constant_override("separation", 12)
	add_child(vbox)
	var eyebrow := Label.new()
	eyebrow.text = "STRATEGIC COMMAND   /   VARDENA THEATRE"
	eyebrow.add_theme_font_size_override("font_size", 13)
	eyebrow.add_theme_color_override("font_color", Color(0.76, 0.72, 0.50))
	vbox.add_child(eyebrow)
	title_label = Label.new()
	title_label.text = "IRON ATLAS\nSHATTERED WORLD"
	title_label.add_theme_font_size_override("font_size", 38)
	vbox.add_child(title_label)
	var desc := Label.new()
	desc.text = "A regional conflict of territory, supply and political support."
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	desc.add_theme_color_override("font_color", Color(0.65, 0.71, 0.65))
	vbox.add_child(desc)
	btn_new = Button.new()
	btn_new.text = "NEW CAMPAIGN"
	btn_new.custom_minimum_size.y = 42
	btn_new.pressed.connect(_on_new)
	vbox.add_child(btn_new)
	btn_load = Button.new()
	btn_load.text = "LOAD CAMPAIGN"
	btn_load.custom_minimum_size.y = 42
	btn_load.pressed.connect(_on_load)
	vbox.add_child(btn_load)
	slots_label = Label.new()
	slots_label.add_theme_color_override("font_color", Color(0.65, 0.71, 0.65))
	vbox.add_child(slots_label)
	var note := Label.new()
	note.text = "OFFLINE  •  SEEDED WORLDS  •  PAUSABLE TIME"
	note.add_theme_font_size_override("font_size", 12)
	note.add_theme_color_override("font_color", Color(0.52, 0.59, 0.53))
	vbox.add_child(note)
	var caption := Label.new()
	caption.position = Vector2(690, 555)
	caption.text = "THE VARDENA CRISIS  /  REGIONAL OPERATIONS"
	caption.add_theme_font_size_override("font_size", 13)
	caption.add_theme_color_override("font_color", Color(0.78, 0.76, 0.60))
	add_child(caption)
	_refresh()


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.07, 0.10, 0.09))
	for x in range(0, 1280, 48):
		draw_line(Vector2(x, 0), Vector2(x, 720), Color(0.13, 0.17, 0.15, 0.35))
	for y in range(0, 720, 48):
		draw_line(Vector2(0, y), Vector2(1280, y), Color(0.13, 0.17, 0.15, 0.35))
	draw_rect(Rect2(55, 118, 510, 496), Color(0.09, 0.13, 0.11, 0.95))
	draw_rect(Rect2(55, 118, 510, 496), Color(0.31, 0.37, 0.29), false, 1.0)
	draw_rect(Rect2(55, 118, 5, 496), Color(0.68, 0.63, 0.39))
	var origin := Vector2(678, 160)
	for y in 10:
		for x in 16:
			var name := "t_grass"
			if x < 10:
				name = "t_forest" if (x * 3 + y * 5) % 11 < 3 else ("t_hills" if (x + y * 2) % 9 == 0 else "t_grass")
			else:
				name = "t_mountain" if (x * 2 + y) % 7 == 0 else "t_desert"
			if (x == 6 and y == 5) or (x == 11 and y == 3):
				name = "t_urban"
			if art.has(name) and art[name] != null:
				draw_texture_rect(art[name], Rect2(origin + Vector2(x * 32, y * 32), Vector2(32, 32)), false, Color(0.68, 0.73, 0.65))
	for marker in [["tank_main", Vector2(865, 285)], ["truck", Vector2(945, 354)], ["infantry", Vector2(803, 378)]]:
		if art.has(marker[0]) and art[marker[0]] != null:
			draw_texture_rect(art[marker[0]], Rect2(marker[1], Vector2(48, 48)), false)
	draw_rect(Rect2(origin, Vector2(512, 320)), Color(0.72, 0.67, 0.43), false, 2.0)
	draw_line(Vector2(678, 505), Vector2(1190, 505), Color(0.40, 0.45, 0.35), 1.0)


func _refresh() -> void:
	var slots: Array = SaveManager.slots()
	slots_label.text = "SAVE SLOTS  /  " + (", ".join(slots.map(func(s): return str(s))) if slots.size() else "none")
	btn_load.disabled = slots.is_empty()


func _on_new() -> void:
	get_tree().change_scene_to_file("res://scenes/campaign_setup.tscn")


func _on_load() -> void:
	var slots: Array = SaveManager.slots()
	if slots.is_empty():
		return
	var err := SaveManager.load_slot(int(slots[0]))
	if err != "":
		EventBus.notification.emit("Load failed: " + err, 2)
		return
	get_tree().change_scene_to_file("res://scenes/world_map.tscn")
