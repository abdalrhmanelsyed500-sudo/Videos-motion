extends RefCounted
## Four-wave sine sum shared by the ocean shader (as uniforms) and the CPU (ship bobbing). Python twin:
## tools/h2d/ship_sprite_logic.py. Units: scene metres. Direction vectors use x = east, z = south (north is -z).
const G := 9.81
const DIR_OFFSETS_DEG: Array[float] = [0.0, 22.0, -38.0, 65.0]
const LENGTHS_M: Array[float] = [46.0, 27.0, 15.0, 8.5]
const SHARES: Array[float] = [0.55, 0.28, 0.12, 0.05]


## Four entries [dir_x, dir_z, k, amp]. wave_m is the crest-to-trough height from the sea state; ice damps the swell.
static func params(wave_m: float, wind_from_deg: float, ice: float) -> Array:
	var to_deg := wind_from_deg + 180.0
	var amp_total := 0.5 * wave_m * (1.0 - 0.85 * clampf(ice, 0.0, 1.0))
	var out: Array = []
	for i in 4:
		var a := deg_to_rad(to_deg + DIR_OFFSETS_DEG[i])
		var wl: float = LENGTHS_M[i] * (0.8 + 0.06 * wave_m)
		out.append([sin(a), -cos(a), TAU / wl, amp_total * SHARES[i]])
	return out


static func height(p: Array, x: float, z: float, t: float) -> float:
	var h := 0.0
	for w in p:
		var k: float = w[2]
		h += float(w[3]) * sin(k * (float(w[0]) * x + float(w[1]) * z) - sqrt(G * k) * t)
	return h
