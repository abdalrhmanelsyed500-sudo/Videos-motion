extends RefCounted
## CP-2 Release A: the ship mode's two Input Map actions (project.godot declares them; ensure_actions() repairs a project file that
## lost them), and the one place that asks "is this event that action". Same pattern as the map's open_map: the physical key AND the
## key labelled with the letter, so any keyboard layout works. Matching is EXACT: Shift+E stays the effects-budget key.
const ACTIONS := {"ship_interact": KEY_E, "autopilot_toggle": KEY_C}


static func ensure_actions() -> void:
	for a in ACTIONS.keys():
		var name := str(a)
		var key: int = ACTIONS[a]
		if not InputMap.has_action(name):
			InputMap.add_action(name)
		var has_phys := false
		var has_label := false
		for e in InputMap.action_get_events(name):
			var ke := e as InputEventKey
			if ke == null or ke.shift_pressed or ke.ctrl_pressed or ke.alt_pressed or ke.meta_pressed:
				continue
			if int(ke.physical_keycode) == key and int(ke.keycode) == 0:
				has_phys = true
			if int(ke.keycode) == key:
				has_label = true
		if not has_phys:
			var p := InputEventKey.new()
			p.physical_keycode = key as Key
			InputMap.action_add_event(name, p)
		if not has_label:
			var l := InputEventKey.new()
			l.keycode = key as Key
			InputMap.action_add_event(name, l)


## Does this key event trigger the action (no modifiers)?
static func hit(k: InputEventKey, action: String) -> bool:
	if k == null or not k.pressed or k.echo:
		return false
	if k.shift_pressed or k.ctrl_pressed or k.alt_pressed or k.meta_pressed:
		return false
	if InputMap.has_action(action):
		return k.is_action_pressed(action, false, true)
	return false


## "E" for the HUD: the label of the first key bound to the action.
static func label(action: String) -> String:
	if not InputMap.has_action(action):
		return "?"
	for e in InputMap.action_get_events(action):
		var ke := e as InputEventKey
		if ke != null:
			return OS.get_keycode_string(ke.keycode if int(ke.keycode) != 0 else ke.physical_keycode)
	return "?"
