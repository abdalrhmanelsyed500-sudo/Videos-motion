extends Node2D
## Island viewer (A6): draws baked island maps with plain 2D, no 3D or GPU effects, so it runs on the dev PC.
## Run this scene with F6 in the editor. SPACE = next island, TAB = toggle overlays, +/- = zoom.
const IslandMap := preload("res://core/island_map.gd")
const DIRS: Array[String] = ["res://tests/fixtures/islands/maps/", "res://data/islands/maps/"]
const COLORS := {
	"~": Color("#2c6a82"), "-": Color("#5cb8a5"), ".": Color("#b3a37e"), "g": Color("#7f9a45"),
	"u": Color("#5f7a37"), "r": Color("#5f6b76"), "#": Color("#5b4e3d"),
}
const POI_COLORS := {
	"survival": Color("#50dc78"), "hook": Color("#ff5a5a"), "secret": Color("#c878ff"),
	"story": Color("#ffdc3c"), "camp": Color("#ff963c"),
}
var _files: Array[String] = []
var _index := 0
var _map: RefCounted = null
var _tex: ImageTexture = null
var _zoom := 3
var _overlays := true
var _label := Label.new()


func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	for dir in DIRS:
		var d := DirAccess.open(dir)
		if d == null:
			continue
		for f in d.get_files():
			if f.ends_with(".map.json"):
				_files.append(dir + f)
	_files.sort()
	add_child(_label)
	_label.position = Vector2(8, 8)
	if _files.is_empty():
		_label.text = "No baked islands found."
		return
	_load(0)


func _load(i: int) -> void:
	_index = posmod(i, _files.size())
	_map = IslandMap.from_file(_files[_index])
	if _map.error != "":
		_label.text = "%s: %s" % [_files[_index], _map.error]
		_tex = null
		queue_redraw()
		return
	var img := Image.create_empty(_map.width, _map.height, false, Image.FORMAT_RGB8)
	for y in range(_map.height):
		for x in range(_map.width):
			var c: Color = COLORS[_map.code_at(x, y)]
			if _map.is_dry(x, y) or _map.code_at(x, y) == "#":
				c = c.lightened(0.02 * _map.elev_at(x, y))
			img.set_pixel(x, y, c)
	_tex = ImageTexture.create_from_image(img)
	_label.text = "%s  %s  explore %.1f min  land %.0f%%   [SPACE next, TAB overlays, +/- zoom]" % [
		_map.island_id, _map.template_id, _map.explore_minutes(), float(_map.stats.get("land_fraction", 0.0)) * 100.0]
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and (event as InputEventKey).pressed:
		match (event as InputEventKey).keycode:
			KEY_SPACE:
				_load(_index + 1)
			KEY_TAB:
				_overlays = not _overlays
				queue_redraw()
			KEY_EQUAL, KEY_KP_ADD:
				_zoom = mini(_zoom + 1, 6)
				queue_redraw()
			KEY_MINUS, KEY_KP_SUBTRACT:
				_zoom = maxi(_zoom - 1, 1)
				queue_redraw()


func _draw() -> void:
	if _tex == null:
		return
	var origin := Vector2(8, 32)
	draw_texture_rect(_tex, Rect2(origin, Vector2(_map.width, _map.height) * _zoom), false)
	if not _overlays:
		return
	var half := Vector2(0.5, 0.5)
	for poly in _map.trails:
		var pts := PackedVector2Array()
		for p in poly:
			pts.append(origin + (Vector2(p[0], p[1]) + half) * _zoom)
		if pts.size() > 1:
			draw_polyline(pts, Color("#96693c"), 1.0)
	for l in _map.landings:
		draw_circle(origin + (Vector2(l["x"], l["y"]) + half) * _zoom, 3.0, Color.WHITE)
	for q in _map.pois:
		draw_circle(origin + (Vector2(q["x"], q["y"]) + half) * _zoom, 3.0, POI_COLORS.get(q["kind"], Color.WHITE))
