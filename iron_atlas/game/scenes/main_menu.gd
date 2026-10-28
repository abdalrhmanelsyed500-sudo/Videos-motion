extends Control

var title_label: Label
var btn_new: Button
var btn_load: Button
var slots_label: Label


func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.09, 0.10, 0.12)
	bg.set_anchors_preset(PRESET_FULL_RECT)
	add_child(bg)
	var vbox := VBoxContainer.new()
	vbox.position = Vector2(440, 180)
	vbox.size = Vector2(400, 360)
	add_child(vbox)
	title_label = Label.new()
	title_label.text = "IRON ATLAS\nSHATTERED WORLD"
	title_label.add_theme_font_size_override("font_size", 34)
	vbox.add_child(title_label)
	btn_new = Button.new()
	btn_new.text = "New Campaign"
	btn_new.pressed.connect(_on_new)
	vbox.add_child(btn_new)
	btn_load = Button.new()
	btn_load.text = "Load Campaign"
	btn_load.pressed.connect(_on_load)
	vbox.add_child(btn_load)
	slots_label = Label.new()
	vbox.add_child(slots_label)
	var note := Label.new()
	note.text = "Stage 1 vertical slice — see docs/STATUS.md"
	note.add_theme_color_override("font_color", Color(0.6, 0.6, 0.6))
	vbox.add_child(note)
	_refresh()


func _refresh() -> void:
	var slots: Array = SaveManager.slots()
	slots_label.text = "Saved slots: " + (", ".join(slots.map(func(s): return str(s))) if slots.size() else "none")
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
