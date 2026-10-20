extends RefCounted
## Pure helpers for the map screen (map_screen.gd): no nodes, no input, no game state, so every rule here is unit-tested without a
## window (tests/test_map_model.gd). World coordinates are metres on the island plane (x east, z south); a view is one baked map
## picture: {id, tab, title, hint, file, bounds [x0, z0, x1, z1], ppm (picture pixels per metre), zoom (first zoom)}.

const VIEWS_FILE := "res://h2d/art/map_views.json"
const VIEW_KEYS: Array = ["id", "tab", "title", "hint", "file", "bounds", "ppm", "zoom"]
const ENTRY_KEYS: Array = ["id", "kind", "name", "x", "z"]

## Built-in copy of the three views. It is used ONLY when map_views.json is missing or unreadable, so the map can still open with
## its three tabs. tests/test_map_model.gd compares it with the file, so the copy cannot drift. Bake: tools/h2d/city_map.py.
const DEFAULT_VIEWS: Array = [
	{"id": "city", "tab": "City", "title": "Anvil Harbor", "hint": "The walled city: streets, terraces, shops and people",
		"file": "map_city.png", "bounds": [-212.0, -282.0, 212.0, 42.0], "ppm": 2.5, "zoom": 0.9},
	{"id": "island", "tab": "Island", "title": "Anvil Cay", "hint": "The whole island: hills, tracks and the harbour",
		"file": "map_island.png", "bounds": [-1300.0, -3500.0, 1500.0, 140.0], "ppm": 0.25, "zoom": 1.0},
	{"id": "sea", "tab": "Sea", "title": "Fishing waters", "hint": "Open water south of the harbour: the four fishing grounds",
		"file": "map_sea.png", "bounds": [-900.0, -420.0, 800.0, 1950.0], "ppm": 0.2, "zoom": 1.0},
]


## Reads map_views.json. Returns {views: Array, error: String}; on any problem the built-in views are returned with the reason.
static func load_views(path: String = VIEWS_FILE) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {"views": DEFAULT_VIEWS.duplicate(true), "error": "%s is missing (built-in views used)" % path}
	var txt := FileAccess.get_file_as_string(path)
	var parsed: Variant = JSON.parse_string(txt)
	if not (parsed is Dictionary) or not (parsed as Dictionary).has("views") or not ((parsed as Dictionary)["views"] is Array):
		return {"views": DEFAULT_VIEWS.duplicate(true), "error": "%s is not a {\"views\": [...]} document (built-in views used)" % path}
	var list: Array = (parsed as Dictionary)["views"]
	var bad := view_problems(list)
	if not bad.is_empty():
		return {"views": DEFAULT_VIEWS.duplicate(true), "error": "%s: %s (built-in views used)" % [path, str(bad[0])]}
	return {"views": list, "error": ""}


## Readable problems of a view list (empty = usable). Release engine builds return null for a missing key, so this is explicit.
static func view_problems(list: Array) -> Array:
	var out: Array = []
	if list.is_empty():
		out.append("no map views")
	var seen: Dictionary = {}
	for i in list.size():
		if not (list[i] is Dictionary):
			out.append("view #%d is not a dictionary" % i)
			continue
		var v: Dictionary = list[i]
		for k in VIEW_KEYS:
			if not v.has(k):
				out.append("view #%d (%s) lacks key '%s'" % [i, str(v.get("id", "?")), k])
		if v.has("id"):
			if seen.has(str(v["id"])):
				out.append("view id '%s' is used twice" % str(v["id"]))
			seen[str(v["id"])] = true
		if v.has("bounds"):
			var b: Variant = v["bounds"]
			if not (b is Array) or (b as Array).size() != 4:
				out.append("view '%s': bounds must be 4 numbers" % str(v.get("id", "?")))
			elif float((b as Array)[2]) <= float((b as Array)[0]) or float((b as Array)[3]) <= float((b as Array)[1]):
				out.append("view '%s': bounds have no area" % str(v.get("id", "?")))
		if v.has("ppm") and float(v["ppm"]) <= 0.0:
			out.append("view '%s': ppm must be > 0" % str(v.get("id", "?")))
	return out


## Fills in everything a state dictionary may lack, drops entries that cannot be drawn and lists why.
## Returns {state: Dictionary, problems: Array}. state: entries, tracked, player, ship, ship_heading, ashore, docked, rings.
static func normalize_state(d: Dictionary) -> Dictionary:
	var problems: Array = []
	var s: Dictionary = {"entries": [], "tracked": str(d.get("tracked", "")), "player": Vector2.ZERO, "ship": Vector2.ZERO,
			"ship_heading": 0.0, "ashore": bool(d.get("ashore", false)), "docked": bool(d.get("docked", false)), "rings": []}
	if d.get("player") is Vector2:
		s["player"] = d["player"]
	elif d.has("player"):
		problems.append("'player' is not a position")
	if d.get("ship") is Vector2:
		s["ship"] = d["ship"]
	elif d.has("ship"):
		problems.append("'ship' is not a position")
	s["ship_heading"] = float(d.get("ship_heading", 0.0))
	var skipped := 0
	var ids: Dictionary = {}
	for e in d.get("entries", []):
		if not (e is Dictionary):
			skipped += 1
			continue
		var ed: Dictionary = e
		var ok := true
		for k in ENTRY_KEYS:
			if not ed.has(k):
				ok = false
		if not ok or ids.has(str(ed["id"])):
			skipped += 1
			continue
		ids[str(ed["id"])] = true
		var c: Dictionary = ed.duplicate()
		c["x"] = float(ed["x"])
		c["z"] = float(ed["z"])
		if not c.has("detail"):
			c["detail"] = ""
		if not c.has("rank"):
			c["rank"] = 1
		if not c.has("views"):
			c["views"] = []
		(s["entries"] as Array).append(c)
	if skipped > 0:
		problems.append("%d map entries were skipped (missing id/kind/name/x/z or duplicated)" % skipped)
	for r in d.get("rings", []):
		if r is Dictionary and (r as Dictionary).has("x") and (r as Dictionary).has("z") and (r as Dictionary).has("r"):
			(s["rings"] as Array).append(r)
	return {"state": s, "problems": problems}


static func map_px(view: Dictionary) -> Vector2:
	var b: Array = view["bounds"]
	var ppm := float(view["ppm"])
	return Vector2((float(b[2]) - float(b[0])) * ppm, (float(b[3]) - float(b[1])) * ppm)


static func in_bounds(p: Vector2, view: Dictionary) -> bool:
	var b: Array = view["bounds"]
	return p.x >= float(b[0]) and p.x <= float(b[2]) and p.y >= float(b[1]) and p.y <= float(b[3])


## World metres -> position inside the map frame (pixels), for a given pan origin (where the picture's top-left sits) and zoom.
static func world_to_frame(p: Vector2, view: Dictionary, origin: Vector2, zoom: float) -> Vector2:
	var b: Array = view["bounds"]
	var ppm := float(view["ppm"])
	return origin + Vector2((p.x - float(b[0])) * ppm, (p.y - float(b[1])) * ppm) * zoom


static func frame_to_world(s: Vector2, view: Dictionary, origin: Vector2, zoom: float) -> Vector2:
	var b: Array = view["bounds"]
	var ppm := float(view["ppm"])
	var c := (s - origin) / maxf(zoom, 0.0001) / ppm
	return Vector2(c.x + float(b[0]), c.y + float(b[1]))


## The zoom at which the whole picture just fits the frame.
static func fit_zoom(frame: Vector2, picture: Vector2) -> float:
	if picture.x < 1.0 or picture.y < 1.0 or frame.x < 1.0 or frame.y < 1.0:
		return 1.0
	return minf(frame.x / picture.x, frame.y / picture.y)


## Keeps the picture inside the frame: centred when smaller than the frame, otherwise never panned past an edge by more than `slack`.
static func clamp_origin(origin: Vector2, frame: Vector2, picture_scaled: Vector2, slack: float = 40.0) -> Vector2:
	var out := origin
	for axis in 2:
		var f := frame[axis]
		var p := picture_scaled[axis]
		if p <= f:
			out[axis] = (f - p) * 0.5
		else:
			out[axis] = clampf(origin[axis], f - p - slack, slack)
	return out


## The origin after zooming from `old_zoom` to `new_zoom` so that the map point under `pivot` (frame pixels) stays under it.
static func zoom_about(origin: Vector2, old_zoom: float, new_zoom: float, pivot: Vector2) -> Vector2:
	return pivot - (pivot - origin) * (new_zoom / maxf(old_zoom, 0.0001))


## The origin that puts world point `p` in the middle of the frame.
static func origin_centered_on(p: Vector2, view: Dictionary, zoom: float, frame: Vector2) -> Vector2:
	return frame * 0.5 - (world_to_frame(p, view, Vector2.ZERO, zoom))


## Entries that belong on a view (an entry with no `views` list shows on every view).
static func entries_for_view(entries: Array, view_id: String) -> Array:
	var out: Array = []
	for e in entries:
		var vs: Array = (e as Dictionary).get("views", []) as Array
		if vs.is_empty() or vs.has(view_id):
			out.append(e)
	return out


## Which tab opens first: the city when ashore or docked at the pier, the sea when under way.
static func default_tab(st: Dictionary, list: Array) -> int:
	var want := "city" if (bool(st.get("ashore", false)) or bool(st.get("docked", false))) else "sea"
	for i in list.size():
		if str((list[i] as Dictionary)["id"]) == want:
			return i
	return 0


## Where the player is: the walker ashore, otherwise the ship.
static func you_at(st: Dictionary) -> Vector2:
	return st["player"] if bool(st.get("ashore", false)) else st["ship"]


## Decides which marker names are drawn so that no two overlap. Each item: {id, dot: Rect2, label: Vector2 (size), priority: int,
## force: bool}. A name sits right of its dot; the highest priority (and forced) names are placed first, a later name that would
## overlap a placed name or an equally or more important dot is hidden. Returns {id: Rect2} for the names that are shown.
static func place_labels(items: Array) -> Dictionary:
	var order: Array = []
	for i in items.size():
		order.append(i)
	order.sort_custom(func(a: int, b: int) -> bool:
		var ia: Dictionary = items[a]
		var ib: Dictionary = items[b]
		if bool(ia.get("force", false)) != bool(ib.get("force", false)):
			return bool(ia.get("force", false))
		if int(ia.get("priority", 0)) != int(ib.get("priority", 0)):
			return int(ia.get("priority", 0)) > int(ib.get("priority", 0))
		return a < b)
	var placed: Array = []
	var shown: Dictionary = {}
	for idx in order:
		var it: Dictionary = items[idx]
		var dot: Rect2 = it["dot"]
		var sz: Vector2 = it["label"]
		var r := Rect2(dot.position + Vector2(dot.size.x + 3.0, (dot.size.y - sz.y) * 0.5), sz)
		var clash := false
		for p in placed:
			if (p as Rect2).intersects(r):
				clash = true
				break
		if not clash:
			# a name may cover the dot of a LESS important marker, never the dot of an equal or more important one
			for j in items.size():
				var other: Dictionary = items[j]
				if j != idx and int(other.get("priority", 0)) >= int(it.get("priority", 0)) and (other["dot"] as Rect2).intersects(r):
					clash = true
					break
		if not clash or bool(it.get("force", false)):
			shown[str(it["id"])] = r
			placed.append(r)
	return shown
