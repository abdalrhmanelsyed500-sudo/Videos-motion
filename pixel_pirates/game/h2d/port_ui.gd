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


## The interface root lives under a CanvasLayer, which is not a Control: nothing lays it out. So it does not trust anchors against a
## parent; it owns its size and copies the viewport's rectangle (stretch mode canvas_items gives the 1280 x 720 design canvas) on
## start, on every resize and, as a safety net, whenever a frame finds it different. Every child anchors to THIS rectangle.
func _fit() -> void:
	var r := get_viewport().get_visible_rect()
	if r.size.x < 1.0 or r.size.y < 1.0:
		return
	if position != r.position or size != r.size:
		set_anchors_preset(Control.PRESET_TOP_LEFT)
		position = r.position
		size = r.size
	# a hidden Control is not laid out when its parent resizes (found by the F8 diagnostic: a hidden dialogue layer stayed 0 x 0 and its
	# window was drawn off the top of the screen), so the three layers are sized by hand too
	for c in get_children():
		var cc := c as Control
		if cc != null and (cc.size != size or cc.position != Vector2.ZERO):
			cc.set_anchors_preset(Control.PRESET_TOP_LEFT)
			cc.position = Vector2.ZERO
			cc.size = size


func _process(_dt: float) -> void:
	_fit()


func _ready() -> void:
	name = "PortUi"
	set_anchors_preset(Control.PRESET_TOP_LEFT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	get_viewport().size_changed.connect(_fit)
	_fit()
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
