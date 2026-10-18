extends RefCounted
## World rules (Canon, cross-record): GDScript twin of tools/data_tools/validate_data.py `world_findings`.
## Proven equal on game/tests/fixtures/world_cases.json (tests/test_world_rules.gd and test_parity.py).
## Codes: dist_short, not_mutual, asym, visible_no_landmark, visible_self.


## islands: id -> island record. Returns Array of [code, island_a, island_b, message].
static func findings(islands: Dictionary) -> Array:
	var out: Array = []
	for iid in islands.keys():
		var isl: Dictionary = islands[iid]
		var pos := Vector2(float(isl["position"]["x_km"]), float(isl["position"]["y_km"]))
		for n in isl.get("neighbors", []):
			var nid: String = n["id"]
			if not islands.has(nid):
				continue  # unknown ref is reported by the registry's reference check
			var other: Dictionary = islands[nid]
			var opos := Vector2(float(other["position"]["x_km"]), float(other["position"]["y_km"]))
			var straight := pos.distance_to(opos)
			if float(n["distance_km"]) + 0.01 < straight:
				var m := "%s->%s sail distance %s km is shorter than the straight line %.2f km"
				out.append(["dist_short", iid, nid, m % [iid, nid, n["distance_km"], straight]])
			var back: Variant = null
			for o in other.get("neighbors", []):
				if o["id"] == iid:
					back = o
					break
			if back == null:
				out.append(["not_mutual", iid, nid, "%s lists %s as neighbour but %s does not list %s" % [iid, nid, nid, iid]])
			elif _differs(back as Dictionary, n as Dictionary):
				out.append(["asym", iid, nid, "%s<->%s distance/time differs between the two directions" % [iid, nid]])
		var vis: Array = isl.get("visible_from", [])
		if not vis.is_empty() and not bool(isl["landmark"]):
			out.append(["visible_no_landmark", iid, "", "%s is visible from %s but is not a deliberate landmark" % [iid, vis]])
		for v in vis:
			if v == iid:
				out.append(["visible_self", iid, "", "%s lists itself in visible_from" % iid])
	return out


static func _differs(a: Dictionary, b: Dictionary) -> bool:
	var dd := absf(float(a["distance_km"]) - float(b["distance_km"]))
	var dh := absf(float(a["sail_hours_sloop"]) - float(b["sail_hours_sloop"]))
	return dd > 0.01 or dh > 0.01


## sorted "code|a|b" strings, the form stored in the shared fixture file
static func codes(islands: Dictionary) -> PackedStringArray:
	var out := PackedStringArray()
	for f in findings(islands):
		out.append("%s|%s|%s" % [f[0], f[1], f[2]])
	out.sort()
	return out
