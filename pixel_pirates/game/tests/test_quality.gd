extends RefCounted
const DataLoader := preload("res://core/data_loader.gd")


func run(t: Object) -> void:
	var d := DataLoader.load_dict("res://data/look/look_profiles.json")
	t.check(not d.is_empty(), "look_profiles.json loads")
	var profiles: Dictionary = d.get("profiles", {})
	t.check(profiles.has("standard") and profiles.has("dev_lite"), "both quality profiles exist")
	var std: Dictionary = profiles.get("standard", {})
	var lite: Dictionary = profiles.get("dev_lite", {})
	var lite_blur := float(lite["tilt_shift"]["max_blur_px"])
	t.check(lite_blur <= float(std["tilt_shift"]["max_blur_px"]), "Dev-Lite blur <= Standard")
	t.check(float(lite["bloom"]["intensity"]) == 0.0, "Dev-Lite has bloom off")
	t.check(lite["internal"] == [640, 360], "Dev-Lite internal is the 640x360 art grid")
	for pname in profiles.keys():
		var p: Dictionary = profiles[pname]
		for k in ["tilt_shift", "vignette", "bloom", "grade", "fog"]:
			t.check(p.has(k), "%s has %s" % [pname, k])
	var moods: Dictionary = d.get("moods", {})
	t.check(moods.size() >= 5, "at least 5 moods")
	for m in moods.keys():
		t.check(float(moods[m]["exposure"]) > 0.3, "mood %s exposure sane" % m)
	var grid: Array = d.get("art_grid", [])
	t.check(grid == [640, 360], "art grid 640x360")
