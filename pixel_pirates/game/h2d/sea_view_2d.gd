extends "res://h2d/sea_view.gd"
## Lightweight 2D fallback: the E1 procedural painter behind the shared interface. Side view, no island, no depth:
## it exists so the game stays playable and testable on hardware that cannot run the 3D path, and as the benchmark
## baseline.
const Painter := preload("res://ui/sea_painter.gd")

var _layer: CanvasLayer
var _canvas: Node2D


class PainterCanvas:
	extends Node2D
	var view: Dictionary = {}

	func _draw() -> void:
		if view.is_empty():
			return
		Painter.sky(self, view)
		Painter.sea(self, view)
		Painter.ice(self, view)
		Painter.ship(self, view)
		Painter.rain(self, view)
		Painter.fog(self, view)
		Painter.lightning(self, view)


func setup(host: Node) -> void:
	_layer = CanvasLayer.new()
	_layer.layer = 0
	host.add_child(_layer)
	_canvas = PainterCanvas.new()
	_canvas.scale = Vector2(2.0, 2.0)
	_canvas.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_layer.add_child(_canvas)
	_layer.visible = false


func update_view(v: Dictionary, _ship: Dictionary, _dt: float) -> void:
	if not _layer.visible:
		return
	(_canvas as PainterCanvas).view = v
	_canvas.queue_redraw()


func set_active(on: bool) -> void:
	_layer.visible = on


func path_name() -> String:
	return "2D"


func describe() -> String:
	return "2D fallback (E1 painter) 640x360 logical"
