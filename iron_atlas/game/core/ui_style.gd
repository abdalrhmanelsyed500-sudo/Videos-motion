extends RefCounted
## Shared, deliberately square-edged military UI palette.

static func box(bg: Color, border: Color, thickness: int = 1) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = bg
	style.border_color = border
	style.set_border_width_all(thickness)
	style.content_margin_left = 9
	style.content_margin_right = 9
	style.content_margin_top = 5
	style.content_margin_bottom = 5
	return style


static func make_theme() -> Theme:
	var t := Theme.new()
	var ink := Color(0.89, 0.90, 0.82)
	var muted := Color(0.63, 0.68, 0.59)
	var border := Color(0.28, 0.34, 0.29)
	var gold := Color(0.73, 0.67, 0.42)
	for kind in ["Button", "OptionButton"]:
		t.set_stylebox("normal", kind, box(Color(0.14, 0.18, 0.17), border))
		t.set_stylebox("hover", kind, box(Color(0.22, 0.28, 0.23), gold))
		t.set_stylebox("pressed", kind, box(Color(0.29, 0.34, 0.24), gold))
		t.set_stylebox("focus", kind, box(Color(0, 0, 0, 0), gold))
		t.set_stylebox("disabled", kind, box(Color(0.10, 0.12, 0.11), Color(0.18, 0.20, 0.18)))
		t.set_color("font_color", kind, ink)
		t.set_color("font_hover_color", kind, Color(1.0, 0.96, 0.78))
		t.set_color("font_pressed_color", kind, Color.WHITE)
		t.set_color("font_disabled_color", kind, muted.darkened(0.3))
		t.set_font_size("font_size", kind, 14)
	t.set_color("font_color", "Label", ink)
	t.set_stylebox("panel", "Window", box(Color(0.10, 0.14, 0.12), border))
	t.set_stylebox("embedded_border", "Window", box(Color(0.10, 0.14, 0.12), gold))
	t.set_color("title_color", "Window", ink)
	t.set_stylebox("normal", "LineEdit", box(Color(0.09, 0.12, 0.11), border))
	t.set_stylebox("focus", "LineEdit", box(Color(0.11, 0.14, 0.12), gold))
	t.set_color("font_color", "LineEdit", ink)
	t.set_stylebox("panel", "ItemList", box(Color(0.08, 0.11, 0.10), border))
	t.set_stylebox("selected", "ItemList", box(Color(0.28, 0.34, 0.24), gold))
	t.set_stylebox("selected_focus", "ItemList", box(Color(0.28, 0.34, 0.24), gold))
	t.set_color("font_color", "ItemList", ink)
	t.set_color("font_selected_color", "ItemList", Color.WHITE)
	return t
