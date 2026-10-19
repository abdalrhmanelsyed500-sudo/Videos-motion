extends RefCounted
## H2D-1.2 vegetation scatter: replays tests/fixtures/scatter_cases.json written by tools/h2d/scatter_logic.py
## (the Python twin of cay_scatter.gd). Checks the hash, the instance and trunk counts per chunk, and that a
## second run gives the same result. NOT YET RUN IN GODOT.
const Scatter := preload("res://h2d/cay_scatter.gd")
const DataLoader := preload("res://core/data_loader.gd")
const ART := "res://h2d/art/"


func _bytes(file: String) -> PackedByteArray:
	var img := Image.load_from_file(ART + file)
	if img == null or img.is_empty():
		return PackedByteArray()
	img.convert(Image.FORMAT_RGBA8)
	return img.get_data()


func _params(meta: Dictionary) -> Dictionary:
	var g: Dictionary = meta["grid"]
	var sc: Dictionary = meta["scatter"]
	var top := float((meta["height_enc"] as Dictionary)["top"])
	var rules: Array = []
	rules.resize(16)
	for i in 16:
		rules[i] = []
	for k in (sc["classes"] as Dictionary).keys():
		rules[int(k)] = (sc["classes"] as Dictionary)[k]
	var trunk := {}
	for k in (sc["trunk_r"] as Dictionary).keys():
		trunk[int(k)] = float((sc["trunk_r"] as Dictionary)[k])
	return {"bio": _bytes("anvil_cay_biome.png"), "hgt": _bytes("anvil_cay_height.png"),
			"lut": Scatter.build_lut(top), "n": int(g["cells"]), "cell": float(g["cell_m"]),
			"ox": float(g["origin_x"]), "oz": float(g["origin_z"]),
			"spacing": float(sc["spacing_m"]), "chunk_m": float(sc["chunk_m"]), "rules": rules,
			"fmin": float(sc["forest_density_min"]), "fgain": float(sc["forest_density_gain"]),
			"min_h": float(sc["min_height_m"]), "trunk": trunk}


func run(t: Object) -> void:
	var fx := DataLoader.load_dict("res://tests/fixtures/scatter_cases.json")
	for c in fx["hashes"]:
		var got := Scatter.hash01(int(c["ix"]), int(c["iz"]), int(c["salt"]))
		var msg := "hash01(%s, %s, %s) = %.6f (expected %s)" % [c["ix"], c["iz"], c["salt"], got, c["v"]]
		t.check(absf(got - float(c["v"])) < 0.00001, msg)
	t.check(Scatter.hash01(5, 5, 1) != Scatter.hash01(5, 5, 2), "different salts give different numbers")
	var lut := Scatter.build_lut(100.0)
	t.check(absf(lut[0] + 8.0) < 0.001 and absf(lut[255] - 100.0) < 0.001, "height LUT spans -8 m .. 100 m")
	t.check(absf(lut[26]) < 0.4, "the beach knee is near 0 m (byte 26 = %.2f m)" % lut[26])
	var meta := DataLoader.load_dict(ART + "anvil_cay.json")
	var p := _params(meta)
	t.check(not (p["bio"] as PackedByteArray).is_empty(), "biome map loads")
	t.check((p["bio"] as PackedByteArray).size() == int(p["n"]) * int(p["n"]) * 4, "biome map is n x n RGBA")
	if (p["bio"] as PackedByteArray).is_empty() or (p["hgt"] as PackedByteArray).is_empty():
		return
	for c in fx["chunks"]:
		var r: Dictionary = Scatter.chunk(int(c["cx"]), int(c["cz"]), p)
		var tag := "chunk (%s, %s)" % [c["cx"], c["cz"]]
		var msg := "%s grows %d instances (expected %d)" % [tag, int(r["count"]), int(c["count"])]
		t.check(int(r["count"]) == int(c["count"]), msg)
		var tr: PackedFloat32Array = r["trunks"]
		t.check(tr.size() == int(c["trunks"]) * 3, "%s has %d trunks" % [tag, int(c["trunks"])])
		var buf: PackedFloat32Array = r["buf"]
		var sx := 0.0
		var sz := 0.0
		var st := 0
		for i in int(r["count"]):
			sx += buf[i * 16 + 3]
			sz += buf[i * 16 + 11]
			st += int(buf[i * 16 + 12])
		var near := absf(sx - float(c["sum_x"])) < 0.5 and absf(sz - float(c["sum_z"])) < 0.5
		t.check(near, "%s positions match the twin" % tag)
		t.check(st == int(c["sum_type"]), "%s types match the twin" % tag)
		var again: Dictionary = Scatter.chunk(int(c["cx"]), int(c["cz"]), p)
		var same := int(again["count"]) == int(r["count"]) and (again["buf"] as PackedFloat32Array) == buf
		t.check(same, "%s is deterministic" % tag)
