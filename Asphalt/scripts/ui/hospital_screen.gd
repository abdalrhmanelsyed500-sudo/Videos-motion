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
    AGUIKit.background(self, "res://assets/ui/hospital_bg.png")
    AGUIKit.dim(self, 0.38)
    var title_tex := TextureRect.new()
    title_tex.texture = load("res://assets/ui/title.png")
    title_tex.position = Vector2(390, 18)
    title_tex.size = Vector2(500, 115)
    title_tex.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
    title_tex.mouse_filter = Control.MOUSE_FILTER_IGNORE
    add_child(title_tex)
    AGUIKit.panel(self, Rect2(260, 142, 760, 430), Color(0.07, 0.08, 0.08, 0.88), AGPalette.c("white"))
    AGUIKit.label(self, "THE ASPHALT SAID NO!", Rect2(300, 166, 680, 52), 38,
        AGPalette.c("amber"), HORIZONTAL_ALIGNMENT_CENTER)
    AGUIKit.label(self, "HUMOROUS RETRO HOSPITAL — CAIRO RING ROAD WARD 7",
        Rect2(300, 220, 680, 30), 17, AGPalette.c("gauge"), HORIZONTAL_ALIGNMENT_CENTER)
    var reason := String(result_data.get("reason", "Severe crash"))
    AGUIKit.label(self, "CRASH REPORT:  " + reason, Rect2(310, 270, 660, 42), 22,
        AGPalette.c("needle"), HORIZONTAL_ALIGNMENT_CENTER)
    var lines := [
        "No graphic injuries — just a bruised ego, a bent exhaust and a very loud nurse.",
        "The doctor says: next time, brake before the microbus, ya batal!",
        "POSITION %d/%d     TIME %s     TOP SPEED %.0f km/h" % [
            int(result_data.get("position", 99)), int(result_data.get("total_racers", 6)),
            _format_time(float(result_data.get("time", 0.0))), float(result_data.get("top_speed_kmh", 0.0))],
        "DISTANCE %.0f m     CRASHES %d     POLICE LEVEL %d" % [
            float(result_data.get("distance", 0.0)), int(result_data.get("crashes", 1)),
            int(result_data.get("police_level", 0))],
    ]
    var y := 330.0
    for line in lines:
        AGUIKit.label(self, line, Rect2(310, y, 660, 38), 17,
            AGPalette.c("white"), HORIZONTAL_ALIGNMENT_CENTER)
        y += 46
    var retry_button := AGUIKit.button(self, "RETRY RACE", Rect2(330, 514, 260, 44))
    retry_button.pressed.connect(func() -> void: retry.emit())
    var menu_button := AGUIKit.button(self, "MAIN MENU", Rect2(690, 514, 260, 44))
    menu_button.pressed.connect(func() -> void: menu.emit())
    if not audio_played:
        audio_played = true
        AGAudio.play("hospital_sting", -6.0)

func _format_time(seconds: float) -> String:
    var minutes := int(seconds / 60.0)
    var remainder := fmod(seconds, 60.0)
    return "%02d:%04.1f" % [minutes, remainder]
