extends Node
const SaveSystem = preload("res://persistence/save_system.gd")
## SaveManager autoload: thin wrapper so UI uses one entry point while tests
## can instantiate SaveSystem directly without autoloads.

var sys := SaveSystem.new()


func save_slot(slot: int, note: String = "") -> String:
	var gs := get_node_or_null("/root/GameState")
	if gs == null or gs.cs == null:
		return "no active campaign"
	return sys.save_campaign(gs.cs, slot, note)


func load_slot(slot: int) -> String:
	var gs := get_node_or_null("/root/GameState")
	if gs == null:
		return "GameState missing"
	var res := sys.load_campaign(slot)
	if res["error"] != "":
		return res["error"]
	gs.adopt_state(res["state"])
	return ""


func slots() -> Array:
	return sys.list_slots()
