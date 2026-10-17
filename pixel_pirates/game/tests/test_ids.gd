extends RefCounted
const Ids := preload("res://core/ids.gd")


func run(t: Object) -> void:
	t.check(Ids.is_valid_data_id("isl_001"), "isl_001 valid")
	t.check(not Ids.is_valid_data_id("isl_1"), "isl_1 invalid (3 digits)")
	t.check(not Ids.is_valid_data_id("isl_sunken_bay"), "islands are numeric only")
	t.check(Ids.is_valid_data_id("item_hardtack"), "item_hardtack valid")
	t.check(Ids.is_valid_data_id("crew_old_tomas"), "multi-word slug valid")
	t.check(not Ids.is_valid_data_id("Item_Hardtack"), "uppercase invalid")
	t.check(not Ids.is_valid_data_id("item-hardtack"), "dash invalid")
	t.check(not Ids.is_valid_data_id("banana_split"), "unknown kind invalid")
	t.check(not Ids.is_valid_data_id("item"), "no slug invalid")
	t.check(Ids.is_valid_asset_id("spr_crew_mannequin_captain"), "asset id valid")
	t.check(Ids.is_valid_asset_id("til_water_deep_a"), "tile id valid")
	t.check(not Ids.is_valid_asset_id("crew_x"), "data kind is not an asset prefix")
	t.check(Ids.prefix_of("prp_barrel") == "prp", "prefix_of")
