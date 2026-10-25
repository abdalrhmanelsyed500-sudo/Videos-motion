extends RefCounted
## Used via preload constant (raw wasm runtime has no editor class cache): MaterialsLib
const MeshBuilder := preload("res://scripts/core/mesh_builder.gd")
## Shared StandardMaterial3D library, keyed by mesh GROUP name (see tools/make_models.py).
## Textured where the Art Bible puts detail-on-texture; flat PBR-ish colours elsewhere.
## Per-asset overrides exist because two assets can share a group name with different looks
## (e.g. group "sign" = licence plate on the tuktuk, shop band on building_b).

## Runtime PNG load (no editor import in wasm/raw runs): buffer -> Image -> ImageTexture.
static func tex(path: String) -> Texture2D:
	if not FileAccess.file_exists(path):
		push_warning("MaterialsLib: texture missing %s (flat colour fallback)" % path)
		return null
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return null
	var img := Image.new()
	if img.load_png_from_buffer(f.get_buffer(f.get_length())) != OK:
		push_warning("MaterialsLib: bad PNG %s" % path)
		return null
	return ImageTexture.create_from_image(img)


static func _mat(col: Color, rough: float = 0.85, tex: Texture2D = null, alpha: float = 1.0,
		emit: Color = Color(0, 0, 0)) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.roughness = rough
	if tex != null:
		m.albedo_texture = tex
	if alpha < 1.0:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.albedo_color.a = alpha
	if emit != Color(0, 0, 0):
		m.emission_enabled = true
		m.emission = emit
	return m


static func lib() -> Dictionary:
	var t := {}
	t["paint"] = _mat(Color.WHITE, 0.5, tex("res://assets/textures/t_tuktuk_paint.png"))
	t["trim"] = _mat(Color("2b2e33"), 0.6)
	t["canopy"] = _mat(Color("d9d2bd"), 0.9)
	t["glass"] = _mat(Color("9fc4d8"), 0.25, null, 0.35)
	t["cabin"] = _mat(Color("1d1c1a"), 0.95)
	t["seat"] = _mat(Color("7a3b2e"), 0.9)
	t["wheel"] = _mat(Color("17181a"), 0.8)
	t["lamp"] = _mat(Color("ffe9a8"), 0.4, null, 1.0, Color("ffe9a8"))
	t["sign"] = _mat(Color.WHITE, 0.6, tex("res://assets/textures/t_plate.png"))
	t["facade_a"] = _mat(Color.WHITE, 0.9, tex("res://assets/textures/t_facade_a.png"))
	t["facade_b"] = _mat(Color.WHITE, 0.9, tex("res://assets/textures/t_facade_b.png"))
	t["facade_c"] = _mat(Color.WHITE, 0.9, tex("res://assets/textures/t_facade_c.png"))
	t["trim_w"] = _mat(Color.WHITE, 0.9, tex("res://assets/textures/t_whitewash.png"))
	t["rail"] = _mat(Color("6b6f74"), 0.7)
	t["tank"] = _mat(Color("9aa0a6"), 0.6)
	t["awning"] = _mat(Color.WHITE, 0.9, tex("res://assets/textures/t_awning.png"))
	t["crate"] = _mat(Color.WHITE, 0.9, tex("res://assets/textures/t_wood.png"))
	t["bump"] = _mat(Color.WHITE, 0.8, tex("res://assets/textures/t_bump.png"))
	t["arrow"] = _mat(Color("3ddc55"), 0.5, null, 1.0, Color("2fae44"))
	t["carpaint"] = _mat(Color("b8452f"), 0.55)
	return t


## mats = lib() plus per-asset overrides {group: material}
static func apply_to(mi: MeshInstance3D, base: Dictionary, overrides: Dictionary = {}) -> void:
	var use: Dictionary = base.duplicate()
	for k in overrides.keys():
		use[k] = overrides[k]
	MeshBuilder.apply_materials(mi, use)


## Character tints from the cast table (ART_BIBLE §5: hijab members get hijab material, never hair).
static func person_mats(cast_entry: Dictionary, base: Dictionary) -> Dictionary:
	var skin := _mat(Color(str(cast_entry.get("skin", "#8a5a3b"))), 0.8)
	var cloth := _mat(Color(str(cast_entry.get("cloth", "#3b4d6b"))), 0.9)
	var legs := _mat(Color(str(cast_entry.get("legs", "#4a4238"))), 0.9)
	var out := {"skin": skin, "cloth": cloth, "legs": legs}
	if bool(cast_entry.get("hijab", false)):
		out["hijab"] = _mat(Color(str(cast_entry.get("hijab_col", "#2f4f63"))), 0.9)
	else:
		out["hair"] = _mat(Color(str(cast_entry.get("hair", "#201812"))), 0.9)
	var merged := base.duplicate()
	for k in out.keys():
		merged[k] = out[k]
	return merged
