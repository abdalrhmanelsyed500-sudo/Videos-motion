extends RefCounted
## CP-2 Release B: the fish pictures. One 48x24 pixel-art PNG per species (tools/h2d/bake_fish.py), found through the icon id in
## data/port/manual_fishing.json. Loaded the way core/assets.gd loads sprites: the imported resource when it exists, otherwise the PNG
## read straight from disk (a fresh clone that has not been imported yet, a headless run). Cached. Returns null for an unknown species
## (the callers draw a plain fish shape instead of nothing).
const DIR := "res://art/fish/"

static var _cache: Dictionary = {}


static func texture(icon_id: String) -> Texture2D:
	if icon_id == "":
		return null
	if _cache.has(icon_id):
		return _cache[icon_id]
	var path := DIR + icon_id + ".png"
	var tex: Texture2D = null
	if ResourceLoader.exists(path):
		tex = load(path) as Texture2D
	if tex == null and FileAccess.file_exists(path):
		var img := Image.load_from_file(path)
		if img != null and not img.is_empty():
			tex = ImageTexture.create_from_image(img)
	_cache[icon_id] = tex
	return tex


static func clear_cache() -> void:
	_cache.clear()
