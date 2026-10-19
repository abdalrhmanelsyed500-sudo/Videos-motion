extends RefCounted
## On-foot connectivity audit that runs the game's OWN walkability rule (`CayWorld.walkable`) on the real baked ground.
##
## Why it exists: the r4 build had a band 0.5 m wide at the pier's landing where the ground was steeper than the walker's limit.
## A flood fill on a 1 m grid hid it (two cells 1 m apart were both walkable), but the walker moves in steps of at most 0.125 m and
## stopped at the band: "an invisible wall between the pier and the city". So every edge of the flood fill is only accepted when
## EVERY point along it (every `sub_m` metres) is walkable, the way the walker would have to step across it.
##
## Used by tests/test_walk.gd (headless, ground read straight from the PNGs) and by F8 (in the running game, on the live world).
var world: Object
var x0 := 0.0
var z0 := 0.0
var cell := 1.0
var nx := 0
var nz := 0
var radius := 0.45
var sub_m := 0.25
var ok := PackedByteArray()
var seen := PackedByteArray()
var parent := PackedInt32Array()
var reached_count := 0
var blocked_edges := 0
var _calls := 0


func _init(w: Object, box: Rect2, cell_m: float, body_r: float, sub: float) -> void:
	world = w
	x0 = box.position.x
	z0 = box.position.y
	cell = cell_m
	nx = int(box.size.x / cell_m)
	nz = int(box.size.y / cell_m)
	radius = body_r
	sub_m = sub
	ok.resize(nx * nz)
	seen.resize(nx * nz)
	parent.resize(nx * nz)
	for i in nx * nz:
		parent[i] = -1


func centre(ix: int, iz: int) -> Vector2:
	return Vector2(x0 + (float(ix) + 0.5) * cell, z0 + (float(iz) + 0.5) * cell)


func index_of(p: Vector2) -> int:
	var ix := int(floorf((p.x - x0) / cell))
	var iz := int(floorf((p.y - z0) / cell))
	if ix < 0 or iz < 0 or ix >= nx or iz >= nz:
		return -1
	return iz * nx + ix


func _walk(p: Vector2) -> bool:
	_calls += 1
	return world.call("walkable", p.x, p.y, radius) as bool


## Marks the walkable cells (centre point test).
func scan() -> int:
	var n := 0
	for iz in nz:
		for ix in nx:
			if _walk(centre(ix, iz)):
				ok[iz * nx + ix] = 1
				n += 1
	return n


## True when every point from a to b (every sub_m metres, both ends included) is walkable.
func edge_ok(a: Vector2, b: Vector2) -> bool:
	var len_m := a.distance_to(b)
	var k := maxi(int(ceilf(len_m / sub_m)), 1)
	for i in range(1, k):
		if not _walk(a.lerp(b, float(i) / float(k))):
			return false
	return true


## Breadth-first flood from `start` (a world point that must itself be walkable). Returns the number of cells reached.
func flood(start: Vector2) -> int:
	var s := index_of(start)
	if s < 0 or ok[s] == 0:
		return 0
	var q: Array[int] = [s]
	seen[s] = 1
	var head := 0
	while head < q.size():
		var c: int = q[head]
		head += 1
		var cx := c % nx
		var cz := c / nx
		var cp := centre(cx, cz)
		for dz in range(-1, 2):
			for dx in range(-1, 2):
				if dx == 0 and dz == 0:
					continue
				var ax := cx + dx
				var az := cz + dz
				if ax < 0 or az < 0 or ax >= nx or az >= nz:
					continue
				var a := az * nx + ax
				if ok[a] == 0 or seen[a] == 1:
					continue
				if not edge_ok(cp, centre(ax, az)):
					blocked_edges += 1
					continue
				seen[a] = 1
				parent[a] = c
				q.append(a)
	reached_count = q.size()
	return reached_count


func is_reached(p: Vector2) -> bool:
	var i := index_of(p)
	return i >= 0 and seen[i] == 1


## The reached cell centre nearest to p within `within_m` metres, or Vector2(NAN, NAN).
func nearest_reached(p: Vector2, within_m: float) -> Vector2:
	var best := Vector2(NAN, NAN)
	var bd := within_m
	var r := int(ceilf(within_m / cell))
	var c := index_of(p)
	if c < 0:
		return best
	var cx := c % nx
	var cz := c / nx
	for dz in range(-r, r + 1):
		for dx in range(-r, r + 1):
			var ax := cx + dx
			var az := cz + dz
			if ax < 0 or az < 0 or ax >= nx or az >= nz or seen[az * nx + ax] == 0:
				continue
			var cp := centre(ax, az)
			var d := cp.distance_to(p)
			if d <= bd:
				bd = d
				best = cp
	return best


## The cell centres from the flood's start to the cell containing p (empty when p was not reached).
func path_to(p: Vector2) -> Array[Vector2]:
	var out: Array[Vector2] = []
	var i := index_of(p)
	if i < 0 or seen[i] == 0:
		return out
	while i >= 0:
		out.append(centre(i % nx, i / nx))
		i = parent[i]
	out.reverse()
	return out


## Drives the real LandWalker along `path` (world points) with the keys' worth of input, the way a player would, and returns the
## distance still to go to the last point (0 = arrived) or -1 when it got stuck. `walker` must already be ashore at the path start.
static func drive(walker: RefCounted, w: Object, path: Array[Vector2], dt: float = 1.0 / 60.0) -> float:
	var step_n := 0
	for k in range(1, path.size()):
		var wp: Vector2 = path[k]
		var guard := 0
		var last := Vector2(walker.get("x"), walker.get("z"))
		var stuck := 0
		while true:
			var here := Vector2(float(walker.get("x")), float(walker.get("z")))
			var to := wp - here
			if to.length() < 0.2:
				break
			walker.call("step", dt, to.normalized(), false, w)
			step_n += 1
			guard += 1
			var now := Vector2(float(walker.get("x")), float(walker.get("z")))
			if now.distance_to(last) < 0.001:
				stuck += 1
				if stuck > 12:
					return -1.0
			else:
				stuck = 0
				last = now
			if guard > 1500:
				return -1.0
	var fin := Vector2(float(walker.get("x")), float(walker.get("z")))
	return fin.distance_to(path[path.size() - 1])
