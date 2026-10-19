extends RefCounted
## Data-driven dialogue (CP-1 revision). Pure logic, no nodes: it loads game/data/port/dialogue.json and turns
## (tree, node, flags, variables) into a VIEW the interface shows: the text pages, and the options with their enabled state.
## What an option DOES (trade, hire, track, pay, leave) is decided by port_game.gd, which owns the economy.
const DataLoader := preload("res://core/data_loader.gd")

var doc: Dictionary = {}
var trees: Dictionary = {}


func load_file(path: String) -> bool:
	doc = DataLoader.load_dict(path)
	trees = doc.get("trees", {}) as Dictionary
	return not trees.is_empty()


func has_tree(tree: String) -> bool:
	return trees.has(tree)


## The node a conversation starts at: the first entry whose conditions hold.
func entry_node(tree: String, flags: Dictionary) -> String:
	var t: Dictionary = trees.get(tree, {})
	for e in t.get("entry", []):
		var d := e as Dictionary
		if _holds(d.get("if", []) as Array, flags):
			return str(d["node"])
	return "hub"


func node_exists(tree: String, nid: String) -> bool:
	return ((trees.get(tree, {}) as Dictionary).get("nodes", {}) as Dictionary).has(nid)


func raw_node(tree: String, nid: String) -> Dictionary:
	return ((trees.get(tree, {}) as Dictionary).get("nodes", {}) as Dictionary).get(nid, {}) as Dictionary


## {pages: [String], options: [{label, enabled, hint, action, arg, next, fail}], set: [flags], goto: String}
func view(tree: String, nid: String, flags: Dictionary, vars: Dictionary) -> Dictionary:
	var n := raw_node(tree, nid)
	var out := {"pages": [], "options": [], "set": n.get("set", []), "goto": str(n.get("goto", "")), "node": nid, "tree": tree}
	if n.is_empty():
		out["pages"] = ["..."]
		out["options"] = [{"label": "Leave", "enabled": true, "hint": "", "action": "leave", "arg": "", "next": "", "fail": ""}]
		return out
	var pages: Array = []
	if n.has("pages"):
		for p in n["pages"]:
			pages.append(fmt(str(p), vars))
	elif n.has("texts"):
		for tv in n["texts"]:
			var d := tv as Dictionary
			if _holds(d.get("if", []) as Array, flags):
				pages.append(fmt(str(d["text"]), vars))
				break
	else:
		pages.append(fmt(str(n.get("text", "...")), vars))
	if pages.is_empty():
		pages.append("...")
	out["pages"] = pages
	var opts: Array = []
	for o in n.get("options", []):
		var od := o as Dictionary
		if not _holds(od.get("if", []) as Array, flags):
			continue
		var ok := _holds(od.get("enable_if", []) as Array, flags)
		opts.append({"label": fmt(str(od.get("label", "...")), vars), "enabled": ok, "hint": fmt(str(od.get("hint", "")), vars),
				"action": str(od.get("action", "")), "arg": od.get("arg", ""), "next": str(od.get("next", "")), "fail": str(od.get("fail", ""))})
	out["options"] = opts
	return out


## "{name}" placeholders; unknown names stay visible as they are, so a typo in the data is obvious in the game.
static func fmt(s: String, vars: Dictionary) -> String:
	if s.find("{") < 0:
		return s
	var out := s
	for k in vars.keys():
		out = out.replace("{%s}" % str(k), str(vars[k]))
	return out


static func _holds(conds: Array, flags: Dictionary) -> bool:
	for c in conds:
		var flag_name := str(c)
		var neg := flag_name.begins_with("!")
		if neg:
			flag_name = flag_name.substr(1)
		var v := bool(flags.get(flag_name, false))
		if v == neg:
			return false
	return true


## Every node reachable? Used by the tests: a list of problems (empty = fine).
func validate() -> Array[String]:
	var bad: Array[String] = []
	for tname in trees.keys():
		var t: Dictionary = trees[tname]
		var nodes: Dictionary = t.get("nodes", {})
		for e in t.get("entry", []):
			if not nodes.has(str((e as Dictionary)["node"])):
				bad.append("%s: entry points at missing node %s" % [tname, str((e as Dictionary)["node"])])
		for nid in nodes.keys():
			var n: Dictionary = nodes[nid]
			if n.has("goto") and not nodes.has(str(n["goto"])):
				bad.append("%s.%s: goto %s missing" % [tname, nid, str(n["goto"])])
			var has_exit := n.has("goto")
			for o in n.get("options", []):
				var od := o as Dictionary
				var act := str(od.get("action", ""))
				if od.has("next") and not nodes.has(str(od["next"])):
					bad.append("%s.%s: next %s missing" % [tname, nid, str(od["next"])])
				if od.has("fail") and not nodes.has(str(od["fail"])):
					bad.append("%s.%s: fail %s missing" % [tname, nid, str(od["fail"])])
				if act == "leave" or od.has("next"):
					has_exit = true
				if act not in ["", "leave", "trade", "hire", "track", "pay", "map"]:
					bad.append("%s.%s: unknown action %s" % [tname, nid, act])
			if not has_exit:
				bad.append("%s.%s: no way out" % [tname, nid])
	return bad
