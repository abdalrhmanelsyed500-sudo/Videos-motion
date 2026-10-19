extends Control
## CP-1 interface root. The first CP-1 interface drew everything by hand on this one Control and the player saw none of it, so
## this revision is a plain node tree: the HUD (port_hud.gd), the conversation window and fish counter (dialogue_ui.gd) and the
## map (map_ui.gd), each made of PanelContainer / Label / TextureRect / Button nodes. This class only owns the three and
## forwards; the rules stay in port_game.gd.
const K := preload("res://h2d/ui_kit.gd")
const Hud := preload("res://h2d/port_hud.gd")
const DialogueUi := preload("res://h2d/dialogue_ui.gd")
const MapUi := preload("res://h2d/map_ui.gd")
const INK := K.INK
const GOLD := K.GOLD
const CREAM := K.CREAM
const DIM := K.DIM
const GREEN := K.GREEN
const RED := K.RED
const AMBER := K.AMBER

var hud: Hud
var dialogue: DialogueUi
var map: MapUi


func _ready() -> void:
	name = "PortUi"
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud = Hud.new()
	hud.name = "Hud"
	add_child(hud)
	dialogue = DialogueUi.new()
	dialogue.name = "Dialogue"
	add_child(dialogue)
	map = MapUi.new()
	map.name = "Map"
	add_child(map)


func toast(text: String, color: Color = CREAM, seconds: float = 5.0) -> void:
	hud.toast(text, color, seconds)


func note_big(text: String, sub: String, seconds: float = 5.5) -> void:
	hud.note_big(text, sub, seconds)


func any_panel_open() -> bool:
	return dialogue.is_open() or map.visible
