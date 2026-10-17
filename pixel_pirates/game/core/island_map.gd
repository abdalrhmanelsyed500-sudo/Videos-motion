extends RefCounted
## A baked island map (Module A6): terrain classes, elevation, landings, points of interest, trails and props.
## The game never generates islands at run time; tools/island_kit/bake.py writes these files. Loading verifies the
## grid hash, so a hand-edited map is refused (edit the template/seed and re-bake instead).
const ELEV_DIGITS := "0123456789abcdef"
const WALKABLE := ".gur-"  ## beach, ground, upland, rock, shallows (wading). Deep water and cliffs are not walkable.
const DRY := ".gur"

var island_id := ""
var template_id := ""
var width := 0
var height := 0
var tile_m := 2.0
var terrain := PackedByteArray()
var elev := PackedByteArray()
var legend: Dictionary = {}
var landings: Array = []
var pois: Array = []
var trails: Array = []
var prop_assets: Array = []
var props: Array = []
var stats: Dictionary = {}
var error := ""


static func from_file(path: String) -> RefCounted:
	var m := new()
	var text := FileAccess.get_file_as_string(path)
	if text.is_empty():
		m.error = "cannot read " + path
		return m
	var parsed: Variant = JSON.parse_string(text)
	if not (parsed is Dictionary):
		m.error = "not a JSON object: " + path
		return m
	m.error = m.parse(parsed as Dictionary)
	return m


func parse(d: Dictionary) -> String:
	var err := _check_header(d)
	if err != "":
		return err
	err = _read_grids(d)
	if err != "":
		return err
	var hash_text := "\n".join(PackedStringArray(d["terrain"])) + "|" + "\n".join(PackedStringArray(d["elev"]))
	if hash_text.sha256_text() != str(d["grid_sha256"]):
		return "grid hash mismatch (map was edited by hand; re-bake it)"
	island_id = str(d["island"])
	template_id = str(d["template"])
	tile_m = float(d.get("tile_m", 2.0))
	legend = d["legend"]
	landings = d["landings"]
	pois = d["pois"]
	trails = d.get("trails", [])
	prop_assets = d.get("prop_assets", [])
	props = d.get("props", [])
	stats = d.get("stats", {})
	return ""


func _check_header(d: Dictionary) -> String:
	if int(d.get("map_schema", 0)) != 1:
		return "unsupported map_schema"
	for k in ["island", "template", "size", "terrain", "elev", "legend", "grid_sha256", "landings", "pois"]:
		if not d.has(k):
			return "missing key " + k
	var size: Array = d["size"]
	width = int(size[0])
	height = int(size[1])
	if (d["terrain"] as Array).size() != height or (d["elev"] as Array).size() != height:
		return "row count does not match size"
	return ""


func _read_grids(d: Dictionary) -> String:
	for r in d["terrain"]:
		if (r as String).length() != width:
			return "terrain row has the wrong length"
		terrain.append_array((r as String).to_ascii_buffer())
	for r in d["elev"]:
		if (r as String).length() != width:
			return "elev row has the wrong length"
		for i in range(width):
			var v := ELEV_DIGITS.find((r as String)[i])
			if v < 0:
				return "bad elevation digit"
			elev.append(v)
	return ""


func in_bounds(x: int, y: int) -> bool:
	return x >= 0 and y >= 0 and x < width and y < height


func code_at(x: int, y: int) -> String:
	return char(terrain[y * width + x])


func terrain_name(x: int, y: int) -> String:
	return str(legend.get(code_at(x, y), "?"))


func elev_at(x: int, y: int) -> int:
	return elev[y * width + x]


func is_walkable(x: int, y: int) -> bool:
	return in_bounds(x, y) and WALKABLE.contains(code_at(x, y))


func is_dry(x: int, y: int) -> bool:
	return in_bounds(x, y) and DRY.contains(code_at(x, y))


## metres from the island's centre; +x east, +y south (the 3D world maps y to z)
func cell_to_local(x: int, y: int) -> Vector2:
	return Vector2((x + 0.5 - width * 0.5) * tile_m, (y + 0.5 - height * 0.5) * tile_m)


func local_to_cell(p: Vector2) -> Vector2i:
	return Vector2i(floori(p.x / tile_m + width * 0.5), floori(p.y / tile_m + height * 0.5))


func pois_of_kind(kind: String) -> Array:
	return pois.filter(func(q: Dictionary) -> bool: return q["kind"] == kind)


func offers() -> PackedStringArray:
	var out := PackedStringArray()
	for q in pois:
		if q.has("offer") and not out.has(q["offer"]):
			out.append(q["offer"])
	return out


func explore_minutes() -> float:
	return float(stats.get("explore_minutes", 0.0))


## flood fill (4-neighbour, walkable cells) from the first landing; returns a PackedByteArray mask (1 = reachable)
func reachable_from_landing() -> PackedByteArray:
	var seen := PackedByteArray()
	seen.resize(width * height)
	if landings.is_empty():
		return seen
	var stack: Array[Vector2i] = [Vector2i(int(landings[0]["x"]), int(landings[0]["y"]))]
	while not stack.is_empty():
		var c: Vector2i = stack.pop_back()
		if not is_walkable(c.x, c.y) or seen[c.y * width + c.x] == 1:
			continue
		seen[c.y * width + c.x] = 1
		stack.append(Vector2i(c.x + 1, c.y))
		stack.append(Vector2i(c.x - 1, c.y))
		stack.append(Vector2i(c.x, c.y + 1))
		stack.append(Vector2i(c.x, c.y - 1))
	return seen
