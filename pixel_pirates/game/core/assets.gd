extends Node
## Asset resolver + sprite library (A4). Autoload "Assets".
## Game code asks for an ASSET ID, never a path. art/final/<category>/<id>.png wins over art/placeholder/...
## so replacing a placeholder = dropping a same-named file into art/final/ (no code or data change).
const DataLoader := preload("res://core/data_loader.gd")
const MANIFEST_PATH := "res://art/manifest/sprites.json"
const FINAL_DIR := "res://art/final"
const PLACEHOLDER_DIR := "res://art/placeholder"

var _manifest: Dictionary = {}
var _tex_cache: Dictionary = {}


func _ready() -> void:
	reload()


func reload() -> void:
	_tex_cache.clear()
	_manifest = (DataLoader.load_dict(MANIFEST_PATH).get("assets", {}) as Dictionary)


func ids() -> PackedStringArray:
	var out := PackedStringArray()
	for k in _manifest.keys():
		out.append(str(k))
	out.sort()
	return out


func ids_of_kind(kind: String) -> PackedStringArray:
	var out := PackedStringArray()
	for k in ids():
		if (_manifest[k] as Dictionary).get("kind", "") == kind:
			out.append(k)
	return out


func has_asset(id: String) -> bool:
	return _manifest.has(id)


func entry(id: String) -> Dictionary:
	return _manifest.get(id, {})


func _exists(path: String) -> bool:
	return ResourceLoader.exists(path) or FileAccess.file_exists(path)


func path_for(id: String) -> String:
	var e := entry(id)
	if e.is_empty():
		return ""
	var cat := str(e["category"])
	var final_path := "%s/%s/%s.png" % [FINAL_DIR, cat, id]
	if _exists(final_path):
		return final_path
	return "%s/%s/%s.png" % [PLACEHOLDER_DIR, cat, id]


func is_placeholder(id: String) -> bool:
	return path_for(id).begins_with(PLACEHOLDER_DIR)


func texture(id: String) -> Texture2D:
	var path := path_for(id)
	if path == "":
		push_warning("Assets: unknown asset id '%s'" % id)
		var bus := get_node_or_null("/root/Bus")
		if bus != null:
			bus.asset_missing.emit(id)
		return null
	if _tex_cache.has(path):
		return _tex_cache[path]
	var tex: Texture2D = null
	if ResourceLoader.exists(path):
		tex = load(path) as Texture2D
	if tex == null and FileAccess.file_exists(path):
		# not imported yet (fresh clone, headless run): read the PNG directly
		var img := Image.load_from_file(path)
		if img != null and not img.is_empty():
			tex = ImageTexture.create_from_image(img)
	if tex == null:
		push_warning("Assets: cannot load %s (run `godot --headless --path game --import` once)" % path)
		return null
	_tex_cache[path] = tex
	return tex


## Builds SpriteFrames. Characters: animations named "<anim>_<dir>" (e.g. "walk_e"). Others: single "default".
func sprite_frames(id: String) -> SpriteFrames:
	var e := entry(id)
	var tex := texture(id)
	if e.is_empty() or tex == null:
		return null
	var sf := SpriteFrames.new()
	if sf.has_animation("default"):
		sf.remove_animation("default")
	if e["kind"] == "character_sheet":
		var cell: Array = e["cell"]
		var cw := int(cell[0])
		var ch := int(cell[1])
		var dirs: Array = e["dirs"]
		var anims: Dictionary = e["anims"]
		for anim_name in anims.keys():
			var a: Dictionary = anims[anim_name]
			for row in range(dirs.size()):
				var nm := "%s_%s" % [anim_name, dirs[row]]
				sf.add_animation(nm)
				sf.set_animation_speed(nm, 1000.0 / float(a["ms"]))
				sf.set_animation_loop(nm, bool(a["loop"]))
				for i in range(int(a["frames"])):
					var at := AtlasTexture.new()
					at.atlas = tex
					at.region = Rect2((int(a["start"]) + i) * cw, row * ch, cw, ch)
					sf.add_frame(nm, at)
	else:
		var size: Array = e["size"]
		var n := int(e.get("frames", 1))
		sf.add_animation("default")
		sf.set_animation_speed("default", 1000.0 / float(e.get("ms", 100)))
		sf.set_animation_loop("default", true)
		for i in range(n):
			var at2 := AtlasTexture.new()
			at2.atlas = tex
			at2.region = Rect2(i * int(size[0]), 0, int(size[0]), int(size[1]))
			sf.add_frame("default", at2)
	return sf
