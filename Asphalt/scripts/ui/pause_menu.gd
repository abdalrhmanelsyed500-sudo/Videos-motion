extends Control

signal resume()
signal restart()
signal settings()
signal quit_to_menu()
signal toggle_camera()

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_WHEN_PAUSED
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    AGUIKit.dim(self, 0.72)
    AGUIKit.panel(self, Rect2(440, 150, 400, 430), Color(0.055, 0.055, 0.07, 0.95), AGPalette.c("amber"))
    AGUIKit.label(self, "PAUSED", Rect2(460, 174, 360, 54), 42, AGPalette.c("amber"), HORIZONTAL_ALIGNMENT_CENTER)
    var y := 242.0
    var resume_button := AGUIKit.button(self, "RESUME RACE", Rect2(490, y, 300, 48))
    resume_button.pressed.connect(func() -> void: resume.emit())
    y += 60
    var camera_button := AGUIKit.button(self, "TOGGLE CAMERA (C)", Rect2(490, y, 300, 48), 18)
    camera_button.pressed.connect(func() -> void: toggle_camera.emit())
    y += 60
    var restart_button := AGUIKit.button(self, "RESTART RACE", Rect2(490, y, 300, 48))
    restart_button.pressed.connect(func() -> void: restart.emit())
    y += 60
    var settings_button := AGUIKit.button(self, "SETTINGS", Rect2(490, y, 300, 48))
    settings_button.pressed.connect(func() -> void: settings.emit())
    y += 60
    var menu_button := AGUIKit.button(self, "QUIT TO MENU", Rect2(490, y, 300, 48))
    menu_button.pressed.connect(func() -> void: quit_to_menu.emit())
