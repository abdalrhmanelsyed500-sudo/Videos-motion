extends RefCounted
## Checks placeholder pipeline output: manifest <-> files <-> palette lock.
## Reads PNGs straight from disk: no GPU, no import needed.
const DataLoader := preload("res://core/data_loader.gd")
const Ids := preload("res://core/ids.gd")


func _palette() -> Dictionary:
	var out := {}
	var p := DataLoader.load_dict("res://data/look/palette.json")
	for ramp in (p.get("ramps", {}) as Dictionary).values():
		for h in ramp:
			out[Color.html(h).to_html(false)] = true
	return out


func run(t: Object) -> void:
	var man := DataLoader.load_dict("res://art/manifest/sprites.json")
	var assets: Dictionary = man.get("assets", {})
	t.check(assets.size() >= 30, "manifest has >= 30 assets (has %d)" % assets.size())
	var pal := _palette()
	t.check(pal.size() >= 100, "palette has >= 100 colours")
	for id in assets.keys():
		var e: Dictionary = assets[id]
		t.check(Ids.is_valid_asset_id(id), "valid asset id: %s" % id)
		var path := "res://art/placeholder/%s/%s.png" % [e["category"], id]
		t.check(FileAccess.file_exists(path), "file exists: %s" % path)
		var img := Image.load_from_file(path)
		if img == null or img.is_empty():
			t.check(false, "loads: %s" % path)
			continue
		if e["kind"] == "character_sheet":
			var cell: Array = e["cell"]
			var total := 0
			for a in (e["anims"] as Dictionary).values():
				total += int(a["frames"])
			t.check(img.get_width() == int(cell[0]) * total, "%s width = cell x frames" % id)
			t.check(img.get_height() == int(cell[1]) * (e["dirs"] as Array).size(), "%s height = cell x dirs" % id)
			continue  # pixel scan skipped for big sheets (slow on old CPUs); Python QA covers it
		var bad := 0
		for y in range(img.get_height()):
			for x in range(img.get_width()):
				var c := img.get_pixel(x, y)
				if c.a > 0.0 and not pal.has(c.to_html(false)):
					bad += 1
		t.check(bad == 0, "%s: %d off-palette pixels" % [id, bad])
