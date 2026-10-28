extends RefCounted
## Compile-safe signal dispatcher: systems must not reference the EventBus
## autoload identifier at parse time (headless -s entry scripts compile before
## autoloads are registered). Scenes may use EventBus directly.
const RefCountedBus = null

static func _node():
	var tree := Engine.get_main_loop()
	if tree == null:
		return null
	return (tree as SceneTree).root.get_node_or_null("/root/EventBus")

static func fire(sig: String, a1 = null, a2 = null, nargs: int = 0) -> void:
	var b = _node()
	if b == null:
		return
	if nargs == 0:
		b.emit_signal(sig)
	elif nargs == 1:
		b.emit_signal(sig, a1)
	else:
		b.emit_signal(sig, a1, a2)
