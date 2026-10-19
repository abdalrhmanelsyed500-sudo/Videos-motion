extends RefCounted
## H2D-1.2 vegetation scatter of Anvil Cay. Pure function of (chunk, baked maps): a hashed jittered grid, one
## candidate per
## 8 m cell, kept or dropped by the biome class, the forest density and the ground height. No random numbers: the
## same chunk
## always grows the same trees, so a tree never moves and the walker's trunk blockers are stable.
## Python twin: tools/h2d/scatter_logic.py (shared hash and count cases in tests/fixtures/scatter_cases.json).
##
## `p` is the parameter dictionary built by cay_world.gd: bio (PackedByteArray RGBA of the biome map), hgt (RGBA of
## the height
## map), lut (PackedFloat32Array, 256 decoded heights), n, cell, ox, oz, spacing, chunk_m, rules (Array indexed by
## class: Array of
## [type, probability, scale_min, scale_max]), fmin, fgain, min_h, trunk (Dictionary type -> radius m).
## It returns {"buf": PackedFloat32Array (16 floats per instance: 3x4 transform, custom data type/scale/0/0),
## "count": int,
## "trunks": PackedFloat32Array (x, z, r per trunk)}.

const FOREST_CLASS := 4


static func hash01(ix: int, iz: int, salt: int) -> float:
	var v: int = (ix * 374761393 + iz * 668265263 + salt * 1442695041) & 0xFFFFFFFF
	v = ((v ^ (v >> 13)) * 1274126177) & 0xFFFFFFFF
	v = v ^ (v >> 16)
	return float(v & 0xFFFF) / 65535.0


## Decoded height of a height-map byte (cay_terrain.py dec_h), for building the LUT.
static func decode_height(b: int, top: float) -> float:
	var v := float(b) / 255.0
	if v < 0.1:
		return v / 0.1 * 8.0 - 8.0
	var u := (v - 0.1) / 0.9
	return u * u * top


static func build_lut(top: float) -> PackedFloat32Array:
	var lut := PackedFloat32Array()
	lut.resize(256)
	for i in 256:
		lut[i] = decode_height(i, top)
	return lut


static func chunk(cx: int, cz: int, p: Dictionary) -> Dictionary:
	var bio: PackedByteArray = p["bio"]
	var hgt: PackedByteArray = p["hgt"]
	var lut: PackedFloat32Array = p["lut"]
	var n: int = p["n"]
	var cell: float = p["cell"]
	var ox: float = p["ox"]
	var oz: float = p["oz"]
	var sp: float = p["spacing"]
	var rules: Array = p["rules"]
	var fmin: float = p["fmin"]
	var fgain: float = p["fgain"]
	var min_h: float = p["min_h"]
	var trunk_r: Dictionary = p["trunk"]
	var per := int(roundf(float(p["chunk_m"]) / sp))
	var buf := PackedFloat32Array()
	var trunks := PackedFloat32Array()
	var count := 0
	for gj in range(cz * per, cz * per + per):
		for gi in range(cx * per, cx * per + per):
			var x := (float(gi) + 0.15 + 0.7 * hash01(gi, gj, 1)) * sp
			var z := (float(gj) + 0.15 + 0.7 * hash01(gi, gj, 2)) * sp
			var ix := int(floorf((x - ox) / cell))
			var iz := int(floorf((z - oz) / cell))
			if ix < 0 or iz < 0 or ix >= n or iz >= n:
				continue
			var idx := (iz * n + ix) * 4
			var cls: int = bio[idx] >> 4
			if cls == 0 or cls >= rules.size():
				continue
			var entries: Array = rules[cls]
			if entries.is_empty():
				continue
			var b: int = bio[idx + 2]
			if b == 255:
				continue
			var dens := 1.0
			if cls == FOREST_CLASS:
				dens = fmin + fgain * float(b) / 250.0
			var h: float = lut[hgt[idx]]
			if h < min_h:
				continue
			var r := hash01(gi, gj, 3)
			var cum := 0.0
			var pick: Array = []
			for e in entries:
				cum += float((e as Array)[1]) * dens
				if r < cum:
					pick = e
					break
			if pick.is_empty():
				continue
			var typ := int(pick[0])
			var sc := float(pick[2]) + (float(pick[3]) - float(pick[2])) * hash01(gi, gj, 4)
			buf.append_array(PackedFloat32Array([1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, h, 0.0, 0.0, 1.0, z,
					float(typ), sc, 0.0, 0.0]))
			count += 1
			if trunk_r.has(typ):
				trunks.append_array(PackedFloat32Array([x, z, float(trunk_r[typ]) * sc]))
	return {"buf": buf, "count": count, "trunks": trunks}
