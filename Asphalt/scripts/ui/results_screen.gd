extends Control

signal retry()
signal menu()

var result_data: Dictionary = {}
var audio_played := false

func _ready() -> void:
    _rebuild()

func set_result(result: Dictionary) -> void:
    result_data = result.duplicate(true)
    if is_inside_tree():
        _rebuild()

func _rebuild() -> void:
    for child in get_children():
        child.queue_free()
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    AGUIKit.background(self, "res://assets/ui/results_bg.png")
    AGUIKit.dim(self, 0.58)
    var victory := bool(result_data.get("victory", false))
    var title := "VICTORY — THE RING ROAD IS YOURS" if victory else "RACE COMPLETE"
    AGUIKit.label(self, title, Rect2(60, 42, 1160, 64), 38,
        AGPalette.c("amber") if victory else AGPalette.c("white"), HORIZONTAL_ALIGNMENT_CENTER)
    AGUIKit.panel(self, Rect2(330, 128, 620, 440), Color(0.055, 0.055, 0.07, 0.92), AGPalette.c("amber"))
    var lines := [
        "FINAL POSITION       %d / %d" % [int(result_data.get("position", 99)), int(result_data.get("total_racers", 6))],
        "RACE TIME            %s" % _format_time(float(result_data.get("time", 0.0))),
        "DISTANCE             %.0f m" % float(result_data.get("distance", 0.0)),
        "TOP SPEED            %.0f km/h" % float(result_data.get("top_speed_kmh", 0.0)),
        "CRASHES / NEAR MISS  %d / %d" % [int(result_data.get("crashes", 0)), int(result_data.get("near_misses", 0))],
        "POLICE PURSUIT       LEVEL %d" % int(result_data.get("police_level", 0)),
        "RIDER / BIKE         %s / %s" % [String(result_data.get("rider", "-")), String(result_data.get("bike", "-"))],
    ]
    var y := 168.0
    for line in lines:
        AGUIKit.label(self, line, Rect2(370, y, 540, 40), 21, AGPalette.c("gauge"))
        y += 48
    if result_data.has("unlock"):
        AGUIKit.label(self, "UNLOCKED: %s" % String(result_data.get("unlock", "")),
            Rect2(370, y + 6, 540, 40), 22, AGPalette.c("amber"))
    var retry_button := AGUIKit.button(self, "RETRY RACE", Rect2(370, 500, 240, 46))
    retry_button.pressed.connect(func() -> void: retry.emit())
    var menu_button := AGUIKit.button(self, "MAIN MENU", Rect2(670, 500, 240, 46))
    menu_button.pressed.connect(func() -> void: menu.emit())
    if not audio_played:
        audio_played = true
        AGAudio.play("victory_sting" if victory else "hospital_sting", -8.0)

func _format_time(seconds: float) -> String:
    var minutes := int(seconds / 60.0)
    var remainder := fmod(seconds, 60.0)
    return "%02d:%04.1f" % [minutes, remainder]
