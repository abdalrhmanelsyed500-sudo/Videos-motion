extends Control

signal back_to_menu()
signal continue_to_bikes()
signal rider_chosen(index: int)

var selected_index := 0
var cards: Array = []
var riders: Array = []

func _ready() -> void:
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    AGUIKit.background(self, "res://assets/ui/menu_background.png")
    AGUIKit.dim(self, 0.66)
    AGUIKit.label(self, "CHOOSE YOUR STREET RIDER", Rect2(40, 22, 1200, 48), 34,
        AGPalette.c("amber"), HORIZONTAL_ALIGNMENT_CENTER)
    AGUIKit.label(self, "Eight original Sarasegya silhouettes — hair, skin tone, clothing, bags and riding attitude all differ.",
        Rect2(80, 70, 1120, 30), 17, AGPalette.c("gauge"), HORIZONTAL_ALIGNMENT_CENTER)
    riders = AGState.riders()
    selected_index = clampi(AGState.selected_rider_index(), 0, maxi(0, riders.size() - 1))
    for i in range(mini(8, riders.size())):
        _build_card(i)
    var back := AGUIKit.button(self, "BACK", Rect2(42, 650, 220, 46))
    back.pressed.connect(func() -> void: back_to_menu.emit())
    var next := AGUIKit.button(self, "CONTINUE TO BIKES", Rect2(980, 650, 256, 46), 19)
    next.pressed.connect(func() -> void: continue_to_bikes.emit())
    _update_highlight()

func _build_card(index: int) -> void:
    var rider: Dictionary = riders[index]
    var col := index % 4
    var row := int(index / 4)
    var x := 42.0 + float(col) * 302.0
    var y := 118.0 + float(row) * 250.0
    var card := AGUIKit.card(self, Rect2(x, y, 282, 230))
    cards.append(card)
    var rider_id := String(rider.get("id", "rider"))
    var portrait_path := "res://assets/ui/portraits/rider_%02d_%s.png" % [index, rider_id]
    AGUIKit.portrait(self, portrait_path, Rect2(x + 8, y + 8, 120, 156))
    AGUIKit.label(self, String(rider.get("name", "Rider")).to_upper(),
        Rect2(x + 134, y + 10, 140, 44), 16, AGPalette.c("white"))
    AGUIKit.label(self, String(rider.get("epithet", "Street Rider")).to_upper(),
        Rect2(x + 134, y + 54, 140, 40), 13, AGPalette.c("amber"))
    AGUIKit.label(self, String(rider.get("arabic_name", "")),
        Rect2(x + 134, y + 94, 140, 26), 15, AGPalette.c("gauge"))
    AGUIKit.label(self, "AGGR", Rect2(x + 134, y + 124, 42, 18), 12, AGPalette.c("white"))
    AGUIKit.stat_bar(self, Rect2(x + 178, y + 126, 92, 12), float(rider.get("aggression", 0.5)), AGPalette.c("needle"))
    AGUIKit.label(self, "SKILL", Rect2(x + 134, y + 144, 42, 18), 12, AGPalette.c("white"))
    AGUIKit.stat_bar(self, Rect2(x + 178, y + 146, 92, 12), float(rider.get("skill", 0.5)), AGPalette.c("green"))
    var select := AGUIKit.button(self, "SELECT", Rect2(x + 8, y + 178, 126, 38), 17)
    select.pressed.connect(Callable(self, "_on_select_pressed").bind(index))
    AGUIKit.label(self, String(rider.get("hair_style", "")).replace("_", " ").to_upper(),
        Rect2(x + 142, y + 184, 130, 24), 12, AGPalette.c("concrete"), HORIZONTAL_ALIGNMENT_CENTER)

func _on_select_pressed(index: int) -> void:
    selected_index = index
    AGState.set_selected_rider(index)
    rider_chosen.emit(index)
    _update_highlight()

func _update_highlight() -> void:
    for i in range(cards.size()):
        var card: Panel = cards[i]
        var color: Color = AGPalette.c("amber") if i == selected_index else AGPalette.c("concrete_dark")
        card.add_theme_stylebox_override("panel", AGUIKit.base_style(Color(0.08, 0.09, 0.13, 0.94), color))
