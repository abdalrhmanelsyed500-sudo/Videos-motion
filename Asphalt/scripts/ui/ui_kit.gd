extends RefCounted
class_name AGUIKit
## Shared retro menu widgets. Fixed 1280x720 coordinates scale with canvas_items.

const WIDTH := 1280.0
const HEIGHT := 720.0

static func base_style(fill: Color, border: Color) -> StyleBoxFlat:
    var style := StyleBoxFlat.new()
    style.bg_color = fill
    style.border_color = border
    style.border_width_left = 2
    style.border_width_top = 2
    style.border_width_right = 2
    style.border_width_bottom = 2
    style.corner_radius_top_left = 0
    style.corner_radius_top_right = 0
    style.corner_radius_bottom_left = 0
    style.corner_radius_bottom_right = 0
    style.content_margin_left = 8
    style.content_margin_top = 5
    style.content_margin_right = 8
    style.content_margin_bottom = 5
    return style

static func background(parent: Control, texture_path: String) -> TextureRect:
    var texture: Texture2D = load(texture_path)
    var rect := TextureRect.new()
    rect.texture = texture
    rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    rect.stretch_mode = TextureRect.STRETCH_SCALE
    rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
    parent.add_child(rect)
    return rect

static func dim(parent: Control, alpha := 0.42) -> ColorRect:
    var rect := ColorRect.new()
    rect.color = Color(0.025, 0.025, 0.035, alpha)
    rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
    parent.add_child(rect)
    return rect

static func title(parent: Control, y := 26.0, width := 820.0) -> TextureRect:
    var texture: Texture2D = load("res://assets/ui/title.png")
    var rect := TextureRect.new()
    rect.texture = texture
    rect.position = Vector2((WIDTH - width) * 0.5, y)
    rect.size = Vector2(width, width * 220.0 / 960.0)
    rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
    rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
    parent.add_child(rect)
    return rect

static func panel(parent: Control, rect: Rect2, fill := Color(0.08, 0.08, 0.10, 0.88),
        border := Color(0.90, 0.72, 0.23)) -> Panel:
    var node := Panel.new()
    node.position = rect.position
    node.size = rect.size
    node.add_theme_stylebox_override("panel", base_style(fill, border))
    parent.add_child(node)
    return node

static func label(parent: Control, text_value: String, rect: Rect2, font_size := 18,
        color := Color(0.85, 0.85, 0.82), align := HORIZONTAL_ALIGNMENT_LEFT) -> Label:
    var node := Label.new()
    node.text = text_value
    node.position = rect.position
    node.size = rect.size
    node.add_theme_font_size_override("font_size", font_size)
    node.add_theme_color_override("font_color", color)
    node.horizontal_alignment = align
    node.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
    node.mouse_filter = Control.MOUSE_FILTER_IGNORE
    parent.add_child(node)
    return node

static func button(parent: Control, text_value: String, rect: Rect2, font_size := 20) -> Button:
    var node := Button.new()
    node.text = text_value
    node.position = rect.position
    node.size = rect.size
    node.focus_mode = Control.FOCUS_ALL
    node.add_theme_stylebox_override("normal", base_style(Color(0.14, 0.13, 0.15, 0.92), AGPalette.c("amber")))
    node.add_theme_stylebox_override("hover", base_style(Color(0.30, 0.21, 0.11, 0.96), AGPalette.c("white")))
    node.add_theme_stylebox_override("pressed", base_style(Color(0.50, 0.24, 0.10, 0.98), AGPalette.c("needle")))
    node.add_theme_stylebox_override("focus", base_style(Color(0.18, 0.18, 0.20, 0.98), AGPalette.c("white")))
    node.add_theme_stylebox_override("disabled", base_style(Color(0.10, 0.10, 0.11, 0.65), Color(0.35, 0.34, 0.34)))
    node.add_theme_color_override("font_color", AGPalette.c("white"))
    node.add_theme_color_override("font_hover_color", AGPalette.c("amber"))
    node.add_theme_color_override("font_pressed_color", Color(1.0, 1.0, 1.0))
    node.add_theme_color_override("font_disabled_color", Color(0.55, 0.54, 0.54))
    node.add_theme_font_size_override("font_size", font_size)
    node.pressed.connect(func() -> void: AGAudio.play_ui_click())
    parent.add_child(node)
    return node

static func card(parent: Control, rect: Rect2) -> Panel:
    var node := panel(parent, rect, Color(0.08, 0.09, 0.13, 0.94), AGPalette.c("concrete"))
    return node

static func portrait(parent: Control, texture_path: String, rect: Rect2) -> TextureRect:
    var texture: Texture2D = load(texture_path)
    var node := TextureRect.new()
    node.texture = texture
    node.position = rect.position
    node.size = rect.size
    node.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
    node.mouse_filter = Control.MOUSE_FILTER_IGNORE
    parent.add_child(node)
    return node

static func stat_bar(parent: Control, rect: Rect2, value: float, color: Color) -> void:
    var back := ColorRect.new()
    back.color = Color(0.05, 0.05, 0.07, 0.9)
    back.position = rect.position
    back.size = rect.size
    back.mouse_filter = Control.MOUSE_FILTER_IGNORE
    parent.add_child(back)
    var fill := ColorRect.new()
    fill.color = color
    fill.position = rect.position + Vector2(2, 2)
    fill.size = Vector2((rect.size.x - 4) * clampf(value, 0.0, 1.0), rect.size.y - 4)
    fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
    parent.add_child(fill)
