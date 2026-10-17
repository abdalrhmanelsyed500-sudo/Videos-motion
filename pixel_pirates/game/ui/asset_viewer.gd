extends Node2D
## Placeholder asset viewer (A4): every manifest asset, animated, 2x, nearest filter.
## Keys: SPACE = next animation, TAB = next direction, Esc = quit. Pure 2D, so it runs on weak GPUs.
const SCALE := 2.0
var _chars: Array[AnimatedSprite2D] = []
var _anim_names: Array[String] = []
var _dirs: Array[String] = ["s", "n", "e", "w"]
var _ai := 0
var _di := 0
var _label: Label


func _ready() -> void:
	RenderingServer.set_default_clear_color(Color("#3a424a"))
	_label = Label.new()
	_label.position = Vector2(8, 4)
	add_child(_label)
	var x := 24.0
	var y := 60.0
	for id in Assets.ids_of_kind("character_sheet"):
		var spr := AnimatedSprite2D.new()
		spr.sprite_frames = Assets.sprite_frames(id)
		spr.scale = Vector2(SCALE, SCALE)
		spr.centered = false
		spr.offset = -Vector2(24, 60)  # pivot = feet
		spr.position = Vector2(x, y + 120)
		add_child(spr)
		_chars.append(spr)
		x += 110.0
	if _chars.size() > 0:
		for n in _chars[0].sprite_frames.get_animation_names():
			var base := String(n).rsplit("_", true, 1)[0]
			if not _anim_names.has(base):
				_anim_names.append(base)
	var cx := 24.0
	var cy := 200.0
	for id in Assets.ids():
		var e := Assets.entry(id)
		if e["kind"] == "character_sheet" or e["kind"] == "ship_billboard":
			continue
		var s := AnimatedSprite2D.new()
		s.sprite_frames = Assets.sprite_frames(id)
		s.scale = Vector2(SCALE, SCALE)
		s.centered = false
		var sz: Array = e["size"]
		var w := float(sz[0]) * SCALE
		var h := float(sz[1]) * SCALE
		if cx + w > 1260.0:
			cx = 24.0
			cy += 130.0
		s.position = Vector2(cx, cy)
		add_child(s)
		s.play("default")
		cx += w + 12.0
	_apply()


func _apply() -> void:
	for c in _chars:
		c.play("%s_%s" % [_anim_names[_ai], _dirs[_di]])
	var state := "all PLACEHOLDER" if Assets.is_placeholder(Assets.ids()[0]) else "mixed"
	_label.text = "anim: %s  dir: %s  |  SPACE anim, TAB dir, Esc quit  |  %d assets, %s" % [
		_anim_names[_ai], _dirs[_di], Assets.ids().size(), state
	]


func _unhandled_input(ev: InputEvent) -> void:
	var k := ev as InputEventKey
	if k == null or not k.pressed or k.echo:
		return
	if k.keycode == KEY_SPACE and _anim_names.size() > 0:
		_ai = (_ai + 1) % _anim_names.size()
		_apply()
	elif k.keycode == KEY_TAB:
		_di = (_di + 1) % _dirs.size()
		_apply()
	elif k.keycode == KEY_ESCAPE:
		get_tree().quit()
