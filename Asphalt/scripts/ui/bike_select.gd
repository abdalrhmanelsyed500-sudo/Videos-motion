extends Control

signal back_to_riders()
signal start_race()
signal bike_chosen(index: int)

var selected_index := 0
var cards: Array = []
var bikes: Array = []

func _ready() -> void:
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    AGUIKit.background(self, "res://assets/ui/menu_background.png")
    AGUIKit.dim(self, 0.68)
    AGUIKit.label(self, "CHOOSE YOUR MOTORCYCLE", Rect2(40, 22, 1200, 48), 34,
        AGPalette.c("amber"), HORIZONTAL_ALIGNMENT_CENTER)
    AGUIKit.label(self, "Real frame, wheels, tank, seat, lights, engine and exhaust geometry — not recoloured boxes.",
        Rect2(80, 70, 1120, 30), 17, AGPalette.c("gauge"), HORIZONTAL_ALIGNMENT_CENTER)
    bikes = AGState.bikes()
    selected_index = clampi(AGState.selected_bike_index(), 0, maxi(0, bikes.size() - 1))
    for i in range(mini(6, bikes.size())):
        _build_card(i)
    var back := AGUIKit.button(self, "BACK TO RIDERS", Rect2(42, 650, 250, 46), 18)
    back.pressed.connect(func() -> void: back_to_riders.emit())
    var start := AGUIKit.button(self, "START RACE", Rect2(982, 650, 254, 46), 20)
    start.pressed.connect(func() -> void: start_race.emit())
    _update_highlight()

func _build_card(index: int) -> void:
    var bike: Dictionary = bikes[index]
    var col := index % 3
    var row := int(index / 3)
    var x := 48.0 + float(col) * 404.0
    var y := 120.0 + float(row) * 252.0
    var card := AGUIKit.card(self, Rect2(x, y, 380, 228))
    cards.append(card)
    var bike_id := String(bike.get("id", "bike"))
    var portrait_path := "res://assets/ui/portraits/bike_%02d_%s.png" % [index, bike_id]
    AGUIKit.portrait(self, portrait_path, Rect2(x + 8, y + 8, 240, 120))
    AGUIKit.label(self, String(bike.get("name", "Bike")).to_upper(),
        Rect2(x + 252, y + 12, 120, 42), 15, AGPalette.c("white"))
    AGUIKit.label(self, String(bike.get("type", "bike")).to_upper(),
        Rect2(x + 252, y + 52, 120, 24), 13, AGPalette.c("amber"))
    AGUIKit.label(self, String(bike.get("description", "")),
        Rect2(x + 10, y + 132, 360, 44), 13, AGPalette.c("gauge"))
    var top := clampf(float(bike.get("top_speed", 60.0)) / 85.0, 0.0, 1.0)
    var accel := clampf(float(bike.get("acceleration", 15.0)) / 22.0, 0.0, 1.0)
    var handling := clampf(float(bike.get("handling", 0.85)), 0.0, 1.0)
    AGUIKit.label(self, "SPEED", Rect2(x + 10, y + 176, 55, 18), 12, AGPalette.c("white"))
    AGUIKit.stat_bar(self, Rect2(x + 66, y + 178, 90, 12), top, AGPalette.c("needle"))
    AGUIKit.label(self, "PICKUP", Rect2(x + 166, y + 176, 62, 18), 12, AGPalette.c("white"))
    AGUIKit.stat_bar(self, Rect2(x + 230, y + 178, 70, 12), accel, AGPalette.c("amber"))
    AGUIKit.label(self, "TURN", Rect2(x + 310, y + 176, 40, 18), 12, AGPalette.c("white"))
    AGUIKit.stat_bar(self, Rect2(x + 348, y + 178, 22, 12), handling, AGPalette.c("green"))
    var unlocked := AGState.is_bike_unlocked(bike)
    var select := AGUIKit.button(self, "SELECT" if unlocked else "LOCKED", Rect2(x + 10, y + 198, 150, 26), 14)
    if not unlocked:
        select.disabled = true
    else:
        select.pressed.connect(Callable(self, "_on_select_pressed").bind(index))
    if not unlocked:
        AGUIKit.label(self, "WIN A RACE TO UNLOCK", Rect2(x + 168, y + 198, 200, 26), 12,
            AGPalette.c("needle"), HORIZONTAL_ALIGNMENT_CENTER)

func _on_select_pressed(index: int) -> void:
    selected_index = index
    AGState.set_selected_bike(index)
    bike_chosen.emit(index)
    _update_highlight()

func _update_highlight() -> void:
    for i in range(cards.size()):
        var card: Panel = cards[i]
        var color: Color = AGPalette.c("amber") if i == selected_index else AGPalette.c("concrete_dark")
        card.add_theme_stylebox_override("panel", AGUIKit.base_style(Color(0.08, 0.09, 0.13, 0.94), color))
