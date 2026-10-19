extends RefCounted
## HARNESS-ONLY polyfill of the RegEx class for the npm WebAssembly Godot template, which is built WITHOUT the regex module.
## It is injected into /proj/core/ by run.mjs when GODOT_REGEX_SHIM=1 (which also rewrites `RegEx` to a preload of this file in the
## copies of the four game scripts that use it; class_name cannot register without the editor's class cache). Never part of the game.
## Supported: ^ $ . [a-z0-9_-] [^..] ( ) | * + ? {n} {n,m} and the escapes \d \w \s \. etc: everything the project's patterns use.
## search() returns a RegExMatch-like object (RefCounted) or null.
var _alts: Array = []
var _valid := false
var _src := ""
var _pos := 0


static func create_from_string(pattern: String, _show_error: bool = true) -> RefCounted:
	var r: RefCounted = (load("res://core/regex_shim.gd") as GDScript).new()
	r.call("compile", pattern)
	return r


func compile(pattern: String, _show_error: bool = true) -> int:
	_src = pattern
	_pos = 0
	_valid = true
	_alts = _parse_alts()
	if _pos != _src.length():
		_valid = false
	return OK if _valid else ERR_PARSE_ERROR


func is_valid() -> bool:
	return _valid


func search(subject: String, offset: int = 0, _end: int = -1) -> RefCounted:
	if not _valid:
		return null
	for start in range(offset, subject.length() + 1):
		var end := _match_alts(_alts, subject, start, func(p: int) -> int: return p)
		if end >= 0:
			var m := RefCounted.new()
			m.set_meta("start", start)
			m.set_meta("end", end)
			return m
	return null


# ---- parser ---------------------------------------------------------------------------------------------------------------
func _parse_alts() -> Array:
	var alts: Array = []
	var seq: Array = []
	while _pos < _src.length():
		var ch := _src[_pos]
		if ch == ")":
			break
		if ch == "|":
			alts.append(seq)
			seq = []
			_pos += 1
			continue
		var node := _parse_atom()
		if node.is_empty():
			_valid = false
			return alts
		var mn := 1
		var mx := 1
		if _pos < _src.length():
			var q := _src[_pos]
			if q == "*":
				mn = 0
				mx = 1 << 30
				_pos += 1
			elif q == "+":
				mn = 1
				mx = 1 << 30
				_pos += 1
			elif q == "?":
				mn = 0
				mx = 1
				_pos += 1
			elif q == "{":
				var close := _src.find("}", _pos)
				if close < 0:
					_valid = false
					return alts
				var body := _src.substr(_pos + 1, close - _pos - 1)
				var parts := body.split(",")
				mn = int(parts[0])
				mx = mn if parts.size() == 1 else (int(parts[1]) if parts[1] != "" else 1 << 30)
				_pos = close + 1
		seq.append([node, mn, mx])
	alts.append(seq)
	return alts


func _parse_atom() -> Dictionary:
	var ch := _src[_pos]
	_pos += 1
	if ch == "^":
		return {"t": "bol"}
	if ch == "$":
		return {"t": "eol"}
	if ch == ".":
		return {"t": "any"}
	if ch == "(":
		if _src.substr(_pos, 2) == "?:":
			_pos += 2
		var inner := _parse_alts()
		if _pos >= _src.length() or _src[_pos] != ")":
			return {}
		_pos += 1
		return {"t": "group", "alts": inner}
	if ch == "[":
		return _parse_set()
	if ch == "\\":
		if _pos >= _src.length():
			return {}
		var e := _src[_pos]
		_pos += 1
		return _escape(e)
	return {"t": "char", "c": ch.unicode_at(0)}


func _escape(e: String) -> Dictionary:
	match e:
		"d":
			return {"t": "set", "neg": false, "r": [[48, 57]]}
		"w":
			return {"t": "set", "neg": false, "r": [[48, 57], [65, 90], [97, 122], [95, 95]]}
		"s":
			return {"t": "set", "neg": false, "r": [[32, 32], [9, 13]]}
		"D":
			return {"t": "set", "neg": true, "r": [[48, 57]]}
		_:
			return {"t": "char", "c": e.unicode_at(0)}


func _parse_set() -> Dictionary:
	var neg := false
	if _pos < _src.length() and _src[_pos] == "^":
		neg = true
		_pos += 1
	var ranges: Array = []
	var first := true
	while _pos < _src.length() and (_src[_pos] != "]" or first):
		first = false
		var lo := _src[_pos]
		_pos += 1
		if lo == "\\" and _pos < _src.length():
			var esc := _escape(_src[_pos])
			_pos += 1
			if esc["t"] == "set":
				ranges.append_array(esc["r"])
				continue
			lo = char(int(esc["c"]))
		if _pos + 1 < _src.length() and _src[_pos] == "-" and _src[_pos + 1] != "]":
			var hi := _src[_pos + 1]
			_pos += 2
			ranges.append([lo.unicode_at(0), hi.unicode_at(0)])
		else:
			ranges.append([lo.unicode_at(0), lo.unicode_at(0)])
	if _pos >= _src.length():
		return {}
	_pos += 1
	return {"t": "set", "neg": neg, "r": ranges}


# ---- matcher (backtracking, continuation style): returns the end position or -1 -----------------------------------------------
func _match_alts(alts: Array, s: String, pos: int, k: Callable) -> int:
	for seq in alts:
		var e := _match_seq(seq as Array, 0, s, pos, k)
		if e >= 0:
			return e
	return -1


func _match_seq(seq: Array, i: int, s: String, pos: int, k: Callable) -> int:
	if i == seq.size():
		return int(k.call(pos))
	var item: Array = seq[i]
	return _match_rep(item[0] as Dictionary, int(item[1]), int(item[2]), 0, s, pos, func(p: int) -> int: return _match_seq(seq, i + 1, s, p, k))


func _match_rep(node: Dictionary, mn: int, mx: int, count: int, s: String, pos: int, k: Callable) -> int:
	if count < mx:
		var e := _match_node(node, s, pos, func(p: int) -> int:
			if p == pos and count >= mn:
				return -1
			return _match_rep(node, mn, mx, count + 1, s, p, k))
		if e >= 0:
			return e
	if count >= mn:
		return int(k.call(pos))
	return -1


func _match_node(node: Dictionary, s: String, pos: int, k: Callable) -> int:
	var t: String = node["t"]
	if t == "bol":
		return int(k.call(pos)) if pos == 0 else -1
	if t == "eol":
		return int(k.call(pos)) if pos == s.length() else -1
	if t == "group":
		return _match_alts(node["alts"] as Array, s, pos, k)
	if pos >= s.length():
		return -1
	var c := s.unicode_at(pos)
	var ok := false
	if t == "any":
		ok = c != 10
	elif t == "char":
		ok = c == int(node["c"])
	elif t == "set":
		var inside := false
		for r in (node["r"] as Array):
			if c >= int(r[0]) and c <= int(r[1]):
				inside = true
				break
		ok = inside != bool(node["neg"])
	return int(k.call(pos + 1)) if ok else -1
