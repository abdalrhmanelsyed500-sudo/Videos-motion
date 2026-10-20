extends Node
## F6 on map_sandbox.tscn: the map screen ALONE, with made-up data and no game. If this window opens (press M or the MAP button)
## the map scene itself works on your PC; if the game's map then fails, the problem is in the game wiring, not in the map.
const MAP_SCENE := preload("res://ui/map/map_screen.tscn")
var _map: CanvasLayer
var _t := 0.0


func _ready() -> void:
	_map = MAP_SCENE.instantiate()
	add_child(_map)
	_map.set("provider", Callable(self, "_state"))
	_map.set("notify", func(text: String) -> void: print("MAP SANDBOX: ", text))
	var info := Label.new()
	info.text = "MAP SANDBOX - press M or the MAP button. Esc closes. Diagnostics: %s" % str(_map.call("diagnostics"))
	info.position = Vector2(12, 8)
	add_child(info)


func _state() -> Dictionary:
	_t += 0.25
	return {
		"entries": [
			{"id": "pier", "kind": "pier", "name": "Test pier", "detail": "your berth", "x": 16.0, "z": 20.0, "rank": 1, "views": []},
			{"id": "fish", "kind": "market", "name": "Test fish market", "detail": "sell your catch", "x": -77.0, "z": -10.0, "rank": 1, "views": []},
			{"id": "pip", "kind": "recruit", "name": "Test recruit", "detail": "recruit, 18 reales", "x": -40.0, "z": 5.0, "rank": 2, "views": ["city", "island"]},
		],
		"tracked": "", "player": Vector2(-100.0, 140.0), "ship": Vector2(-120.0, 150.0), "ship_heading": 0.0, "ashore": false, "docked": false, "rings": [],
	}
