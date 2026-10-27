extends Control

signal start_race()
signal rider_select()
signal bike_select()
signal settings()
signal quit_game()

func _ready() -> void:
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    AGUIKit.background(self, "res://assets/ui/menu_background.png")
    AGUIKit.dim(self, 0.34)
    AGUIKit.title(self, 24.0, 820.0)
    AGUIKit.panel(self, Rect2(420, 272, 440, 386),
        Color(0.055, 0.055, 0.075, 0.86), AGPalette.c("amber"))
    var y := 292.0
    var start_button := AGUIKit.button(self, "START RACE", Rect2(470, y, 340, 52), 24)
    start_button.pressed.connect(func() -> void: start_race.emit())
    start_button.grab_focus()
    y += 64
    var rider_button := AGUIKit.button(self, "RIDER SELECT", Rect2(470, y, 340, 48))
    rider_button.pressed.connect(func() -> void: rider_select.emit())
    y += 60
    var bike_button := AGUIKit.button(self, "MOTORCYCLE SELECT", Rect2(470, y, 340, 48))
    bike_button.pressed.connect(func() -> void: bike_select.emit())
    y += 60
    var settings_button := AGUIKit.button(self, "SETTINGS", Rect2(470, y, 340, 48))
    settings_button.pressed.connect(func() -> void: settings.emit())
    y += 60
    var quit_button := AGUIKit.button(self, "QUIT", Rect2(470, y, 340, 48))
    quit_button.pressed.connect(func() -> void: quit_game.emit())
    AGUIKit.label(self, "W / UP ACCELERATE   S / DOWN BRAKE   A / D STEER   SPACE HANDBRAKE   SHIFT BOOST   C CAMERA   ESC PAUSE",
        Rect2(70, 674, 1140, 28), 15, AGPalette.c("gauge"), HORIZONTAL_ALIGNMENT_CENTER)
    AGUIKit.label(self, "CAREER  %d WINS / %d RACES" % [AGState.career_wins(), AGState.career_races()],
        Rect2(470, 612, 340, 24), 16, AGPalette.c("amber"), HORIZONTAL_ALIGNMENT_CENTER)
