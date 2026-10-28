extends SceneTree
## Visual QA only: places an existing enemy formation at player contact so the
## unmodified tactical scene can be rendered. This is not a gameplay test.
var frames := 0


func _process(_delta: float) -> void:
	frames += 1
	if frames != 2:
		return
	var gs = root.get_node("GameState")
	gs.new_campaign(123, 24)
	var friendly: Dictionary = gs.cs.formations_of(gs.cs.player_id())[0]
	var enemy: Dictionary = gs.cs.formations_of("cty_vardena")[0]
	enemy["region"] = friendly["region"]
	gs.tactical_region = friendly["region"]
	root.add_child(load("res://scenes/tactical_map.tscn").instantiate())
