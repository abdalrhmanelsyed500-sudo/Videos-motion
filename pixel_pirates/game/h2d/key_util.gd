extends RefCounted
## One place that turns a key event into the key the player MEANT. Godot's `keycode` follows the active keyboard layout: on a
## Latin layout it is the letter printed on the key, but on an Arabic (or any non-Latin) layout it is a non-Latin character, so
## `k.keycode == KEY_M` would never match and the map, E, F and the number keys would all seem dead. For those layouts we fall
## back to the PHYSICAL key (the QWERTY position). Latin layouts such as AZERTY keep working by label.


static func code(k: InputEventKey) -> int:
	var kc := int(k.keycode)
	var pc := int(k.physical_keycode)
	if kc == 0:
		return pc
	if kc >= int(KEY_SPECIAL) or kc <= 0x7E:
		return kc          # function keys, arrows, Enter, Esc, or a Latin character
	return pc              # a non-Latin character: use the physical key


static func is_confirm(key: int) -> bool:
	return key == KEY_E or key == KEY_ENTER or key == KEY_KP_ENTER or key == KEY_SPACE


## 0-based index for the keys 1..9 (and the keypad), or -1.
static func digit(key: int) -> int:
	if key >= KEY_1 and key <= KEY_9:
		return key - int(KEY_1)
	if key >= KEY_KP_1 and key <= KEY_KP_9:
		return key - int(KEY_KP_1)
	return -1
