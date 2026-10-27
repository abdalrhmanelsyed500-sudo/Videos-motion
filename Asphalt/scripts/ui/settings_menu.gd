extends Control

signal back_to_menu()

var return_target := "menu"

func _ready() -> void:
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    AGUIKit.background(self, "res://assets/ui/menu_background.png")
    AGUIKit.dim(self, 0.74)
    AGUIKit.label(self, "PERFORMANCE / GAME SETTINGS", Rect2(40, 26, 1200, 48), 34,
        AGPalette.c("amber"), HORIZONTAL_ALIGNMENT_CENTER)
    AGUIKit.panel(self, Rect2(300, 100, 680, 520), Color(0.06, 0.06, 0.08, 0.92), AGPalette.c("amber"))

    var quality := _option_button("VISUAL QUALITY", ["LOW", "MEDIUM", "HIGH"], Rect2(560, 140, 340, 40),
        ["low", "medium", "high"].find(String(AGState.get_setting("quality", "medium"))))
    quality.item_selected.connect(func(index: int) -> void: AGState.set_setting("quality", ["low", "medium", "high"][index]))

    var scale_index := [0.6, 0.75, 1.0].find(float(AGState.get_setting("resolution_scale", 1.0)))
    if scale_index < 0:
        scale_index = 2
    var scale := _option_button("3D RESOLUTION SCALE", ["0.60x", "0.75x", "1.00x"], Rect2(560, 196, 340, 40), scale_index)
    scale.item_selected.connect(func(index: int) -> void: AGState.set_setting("resolution_scale", [0.6, 0.75, 1.0][index]))

    var difficulty := _option_button("RIVAL DIFFICULTY", ["SUNDAY RIDER", "STREET RACE", "RING ROAD INSANE"],
        Rect2(560, 252, 340, 40), int(AGState.get_setting("difficulty", 1)))
    difficulty.item_selected.connect(func(index: int) -> void: AGState.set_setting("difficulty", index))

    var camera_index := 0 if String(AGState.get_setting("default_camera", "cockpit")) == "cockpit" else 1
    var camera := _option_button("DEFAULT CAMERA", ["COCKPIT", "THIRD PERSON"], Rect2(560, 308, 340, 40), camera_index)
    camera.item_selected.connect(func(index: int) -> void: AGState.set_setting("default_camera", "cockpit" if index == 0 else "chase"))

    _slider("MASTER VOLUME", Rect2(560, 376, 340, 22), 0.0, 1.0, 0.05,
        float(AGState.get_setting("master_volume", 0.75)), "master_volume")
    _slider("TRAFFIC DENSITY", Rect2(560, 426, 340, 22), 0.35, 1.8, 0.05,
        float(AGState.get_setting("traffic_density", 1.0)), "traffic_density")

    var shadows := CheckBox.new()
    shadows.text = "DYNAMIC SHADOWS"
    shadows.position = Vector2(560, 468)
    shadows.size = Vector2(240, 32)
    shadows.button_pressed = bool(AGState.get_setting("shadows", true))
    _style_checkbox(shadows)
    add_child(shadows)
    shadows.toggled.connect(func(value: bool) -> void: AGState.set_setting("shadows", value))

    var fps := CheckBox.new()
    fps.text = "SHOW FPS"
    fps.position = Vector2(800, 468)
    fps.size = Vector2(180, 32)
    fps.button_pressed = bool(AGState.get_setting("show_fps", false))
    _style_checkbox(fps)
    add_child(fps)
    fps.toggled.connect(func(value: bool) -> void: AGState.set_setting("show_fps", value))

    AGUIKit.label(self, "Resolution and shadows apply immediately. Scene density applies to the next race.",
        Rect2(330, 520, 620, 30), 15, AGPalette.c("gauge"), HORIZONTAL_ALIGNMENT_CENTER)
    var back := AGUIKit.button(self, "BACK", Rect2(530, 566, 220, 42))
    back.pressed.connect(func() -> void: back_to_menu.emit())

func _option_button(label_text: String, items: Array, rect: Rect2, selected: int) -> OptionButton:
    AGUIKit.label(self, label_text, Rect2(330, rect.position.y, 220, rect.size.y), 17, AGPalette.c("white"))
    var option := OptionButton.new()
    option.position = rect.position
    option.size = rect.size
    for i in range(items.size()):
        option.add_item(String(items[i]), i)
    option.selected = clampi(selected, 0, maxi(0, items.size() - 1))
    _style_button(option)
    add_child(option)
    return option

func _slider(label_text: String, rect: Rect2, min_value: float, max_value: float, step: float,
        value: float, setting_key: String) -> HSlider:
    AGUIKit.label(self, label_text, Rect2(330, rect.position.y - 10, 220, rect.size.y + 20), 17, AGPalette.c("white"))
    var slider := HSlider.new()
    slider.min_value = min_value
    slider.max_value = max_value
    slider.step = step
    slider.value = value
    slider.position = rect.position
    slider.size = rect.size
    slider.add_theme_color_override("font_color", AGPalette.c("white"))
    add_child(slider)
    slider.value_changed.connect(func(new_value: float) -> void: AGState.set_setting(setting_key, new_value))
    return slider

func _style_button(button: Button) -> void:
    button.add_theme_stylebox_override("normal", AGUIKit.base_style(Color(0.12, 0.12, 0.14, 0.94), AGPalette.c("concrete")))
    button.add_theme_stylebox_override("hover", AGUIKit.base_style(Color(0.20, 0.19, 0.21, 0.96), AGPalette.c("amber")))
    button.add_theme_color_override("font_color", AGPalette.c("white"))
    button.add_theme_font_size_override("font_size", 16)

func _style_checkbox(check: CheckBox) -> void:
    check.add_theme_color_override("font_color", AGPalette.c("white"))
    check.add_theme_font_size_override("font_size", 16)
