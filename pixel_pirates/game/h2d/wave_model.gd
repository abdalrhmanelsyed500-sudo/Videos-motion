extends RefCounted
## Four-wave sine sum shared by the ocean shader (as uniforms) and the CPU (ship bobbing). Python twin:
## tools/h2d/ship_sprite_logic.py. Units: scene metres. Direction vectors use x = east, z = south (north is -z).
const G := 9.81
const SHAPE_SAMPLES := 64
const DIR_OFFSETS_DEG: Array[float] = [0.0, 22.0, -38.0, 65.0]
const LENGTHS_M: Array[float] = [46.0, 27.0, 15.0, 8.5]
const SHARES: Array[float] = [0.55, 0.28, 0.12, 0.05]  ## the rough sea (the legacy shares)
const SHARES_CALM: Array[float] = [0.80, 0.17, 0.025, 0.005]  ## a calm sea is a long swell with hardly any short waves
const SHARES_GALE: Array[float] = [0.42, 0.30, 0.18, 0.10]  ## a gale carries much more short, steep wind-sea


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


# ---- H2D-0.2: the sea built from the shared environment state (env_model.gd) -----------------------------------------
## The legacy params()/height() above stay as they were (their tests and Python twin are unchanged). The functions
## below add the sea-state shaping: crests sharpen as the sea builds (flat troughs, peaked crests), directions narrow a
## little, and the direction/height come from the environment model, so a change of weather develops gradually.
## Python twin: tools/h2d/env_logic.py (wave_build, wave_height, crest_bias).

## Mean of 2 * q^p - 1 over one wave period (q = 0.5 + 0.5 cos), so the shaped wave still averages zero.
static func crest_bias(p: float) -> float:
	var s := 0.0
	for i in SHAPE_SAMPLES:
		s += pow(0.5 + 0.5 * cos(TAU * float(i) / float(SHAPE_SAMPLES)), p)
	return 2.0 * (s / float(SHAPE_SAMPLES)) - 1.0


## Wave-energy shares of the four waves and the wavelength multiplier for a sea-state index (H2D-0.3):
## {"shares": [x4], "len_mult": float}. Calm = long swell, rough = the legacy mix, gale = more short steep waves.
static func mix_for_sea(sea: float) -> Dictionary:
	var sh: Array = []
	var u := 0.0
	var len_mult := 1.0
	if sea < 0.5:
		u = sea / 0.5
		for i in 4:
			sh.append(SHARES_CALM[i] + (SHARES[i] - SHARES_CALM[i]) * u)
		len_mult = 1.25 - 0.25 * u
	else:
		u = (sea - 0.5) / 0.5
		for i in 4:
			sh.append(SHARES[i] + (SHARES_GALE[i] - SHARES[i]) * u)
		len_mult = 1.0 - 0.10 * u
	return {"shares": sh, "len_mult": len_mult}


## {"waves": [[dir_x, dir_z, k, amp] x 4], "p": crest exponent, "bias": mean correction}.
static func build(wave_vis_m: float, wave_to_deg: float, sea: float, ice: float, crest_calm: float,
		crest_gale: float) -> Dictionary:
	var p := crest_calm + (crest_gale - crest_calm) * sea
	var spread := 1.0 - 0.3 * sea
	var mx := mix_for_sea(sea)
	var shares: Array = mx["shares"]
	var len_mult: float = mx["len_mult"]
	var amp_total := 0.5 * wave_vis_m * (1.0 - 0.85 * clampf(ice, 0.0, 1.0))
	var waves: Array = []
	for i in 4:
		var a := deg_to_rad(wave_to_deg + DIR_OFFSETS_DEG[i] * spread)
		var wl: float = LENGTHS_M[i] * (0.8 + 0.06 * wave_vis_m) * len_mult
		waves.append([sin(a), -cos(a), TAU / wl, amp_total * float(shares[i])])
	return {"waves": waves, "p": p, "bias": crest_bias(p)}


static func height_b(b: Dictionary, x: float, z: float, t: float) -> float:
	var h := 0.0
	var p: float = b["p"]
	var bias: float = b["bias"]
	for w in (b["waves"] as Array):
		var k: float = w[2]
		var ph := k * (float(w[0]) * x + float(w[1]) * z) - sqrt(G * k) * t
		var q := 0.5 + 0.5 * cos(ph)
		h += float(w[3]) * (2.0 * pow(maxf(q, 0.0001), p) - 1.0 - bias)
	return h
