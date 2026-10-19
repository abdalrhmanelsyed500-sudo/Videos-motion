extends RefCounted
## Small helpers that build the CP-1 interface from STANDARD Control nodes (PanelContainer, Label, TextureRect, Button,
## StyleBoxFlat). The first CP-1 interface drew everything by hand on one custom Control; the player saw none of it, so this
## kit uses only the node types that already show up in the HUD labels the player does see.
const INK := Color(0.10, 0.07, 0.05, 0.95)
const INK2 := Color(0.18, 0.12, 0.08, 0.97)
const PARCH := Color(0.89, 0.80, 0.60)
const PARCH_D := Color(0.72, 0.60, 0.40)
const GOLD := Color(0.97, 0.79, 0.30)
const CREAM := Color(1.0, 0.95, 0.82)
const DIM := Color(0.74, 0.68, 0.56)
const GREEN := Color(0.52, 0.90, 0.44)
const RED := Color(1.0, 0.45, 0.35)
const AMBER := Color(1.0, 0.72, 0.25)
const BORDER := Color(0.62, 0.43, 0.20)
const TITLE_FONT := "res://ui/fonts/pirata_one_regular.ttf"

static var _title_font: Font = null
static var _title_tried := false
static var _tex_cache: Dictionary = {}


## The pirate title font when it can be loaded (imported resource first, then the raw file), else the engine default.
static func title_font() -> Font:
	if _title_tried:
		return _title_font
	_title_tried = true
	if ResourceLoader.exists(TITLE_FONT):
		_title_font = load(TITLE_FONT) as Font
	if _title_font == null and FileAccess.file_exists(TITLE_FONT):
		var ff := FontFile.new()
		if ff.load_dynamic_font(TITLE_FONT) == OK:
			_title_font = ff
	return _title_font


static func style(bg: Color, border: Color = BORDER, bw: int = 3, radius: int = 4, shadow: int = 0) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = border
	s.set_border_width_all(bw)
	s.set_corner_radius_all(radius)
	s.content_margin_left = 12.0
	s.content_margin_right = 12.0
	s.content_margin_top = 8.0
	s.content_margin_bottom = 8.0
	if shadow > 0:
		s.shadow_size = shadow
		s.shadow_color = Color(0.0, 0.0, 0.0, 0.5)
		s.shadow_offset = Vector2(0.0, 3.0)
	return s


static func label(text: String, size: int = 16, color: Color = CREAM, outline: int = 4, title: bool = false) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_outline_color", Color(0.04, 0.03, 0.02, 0.92))
	l.add_theme_constant_override("outline_size", outline)
	if title:
		var f := title_font()
		if f != null:
			l.add_theme_font_override("font", f)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


static func panel(bg: Color = INK, border: Color = BORDER, bw: int = 3, shadow: int = 8) -> PanelContainer:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", style(bg, border, bw, 4, shadow))
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return p


static func box(vertical: bool, gap: int = 6) -> BoxContainer:
	var b: BoxContainer = VBoxContainer.new() if vertical else HBoxContainer.new()
	b.add_theme_constant_override("separation", gap)
	b.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return b


static func rect(color: Color, size: Vector2) -> ColorRect:
	var r := ColorRect.new()
	r.color = color
	r.custom_minimum_size = size
	r.size = size
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


## A flat button in the same style: `selected` draws the gold frame.
static func button(text: String, size: int = 17) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.add_theme_font_size_override("font_size", size)
	b.add_theme_color_override("font_color", CREAM)
	b.add_theme_color_override("font_hover_color", Color.WHITE)
	b.add_theme_color_override("font_disabled_color", Color(0.55, 0.50, 0.42))
	b.add_theme_stylebox_override("normal", style(Color(0.20, 0.14, 0.09, 0.96), Color(0.40, 0.28, 0.15), 2, 3))
	b.add_theme_stylebox_override("hover", style(Color(0.30, 0.21, 0.11, 0.98), GOLD, 2, 3))
	b.add_theme_stylebox_override("pressed", style(Color(0.36, 0.25, 0.12, 1.0), GOLD, 2, 3))
	b.add_theme_stylebox_override("disabled", style(Color(0.14, 0.11, 0.09, 0.9), Color(0.28, 0.22, 0.16), 2, 3))
	return b


static func set_button_selected(b: Button, on: bool) -> void:
	if on:
		b.add_theme_stylebox_override("normal", style(Color(0.34, 0.23, 0.10, 1.0), GOLD, 3, 3))
		b.add_theme_color_override("font_color", Color.WHITE)
	else:
		b.add_theme_stylebox_override("normal", style(Color(0.20, 0.14, 0.09, 0.96), Color(0.40, 0.28, 0.15), 2, 3))
		b.add_theme_color_override("font_color", CREAM)


## A texture from an imported resource, or (in the editor / a project run before the import finished) straight from the PNG.
static func texture(path: String) -> Texture2D:
	if _tex_cache.has(path):
		return _tex_cache[path] as Texture2D
	var t: Texture2D = null
	if ResourceLoader.exists(path):
		t = load(path) as Texture2D
	if t == null and FileAccess.file_exists(path):
		var img := Image.load_from_file(path)
		if img != null and not img.is_empty():
			t = ImageTexture.create_from_image(img)
	_tex_cache[path] = t
	return t


static func nearest(c: CanvasItem) -> void:
	c.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
