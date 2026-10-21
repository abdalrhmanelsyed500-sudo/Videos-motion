# gdlint: disable=max-line-length
extends RefCounted
## CP-2B.1 audit: manual fishing is the ONLY way a fish can enter the hold. This test reads the game's own source files and the live
## classes and proves that no other path exists:
##   * `add_catch` (the one function that puts fish into the hold) is called by exactly one runtime file, the winch (fish_manual.gd);
##     the market, the loading of a save and the sale only remove fish or restore them;
##   * no runtime file writes the hold (`lots`, `kg_total`) except port_state.gd;
##   * the old timed net is gone from fishing.gd (no roll, no start, no timer, no hauls, no haul interval, no time multiplier) and its
##     step() takes no hold and returns only stop events however long the ship sits on a ground;
##   * no F6/F7-style cheat key adds fish, no "Lower the nets" prompt and no legacy HUD panel remains;
##   * selling still works (paid once, hold emptied) and the winch session is the only caller of the hold's add function.
## NOT YET RUN ON THE USER'S PC.
const Fishing := preload("res://h2d/fishing.gd")
const PortState := preload("res://h2d/port_state.gd")
const Ocean := preload("res://core/ocean.gd")
const DataLoader := preload("res://core/data_loader.gd")

const ADD_CALLERS_OK := ["res://h2d/port_state.gd", "res://h2d/fish_manual.gd"]
const HOLD_WRITERS_OK := ["res://h2d/port_state.gd"]


func _scripts(dir: String, out: Array) -> void:
	var d := DirAccess.open(dir)
	if d == null:
		return
	for f in d.get_files():
		if f.ends_with(".gd"):
			out.append(dir.path_join(f))
	for sub in d.get_directories():
		if sub != "tests" and sub != ".godot" and sub != "addons":
			_scripts(dir.path_join(sub), out)


func _src(path: String) -> String:
	return FileAccess.get_file_as_string(path)


## True when `pat` occurs in `code` as the start of an identifier (so `slots.append` is not `lots.append`).
func _has_word(code: String, pat: String) -> bool:
	var from := 0
	while true:
		var i := code.find(pat, from)
		if i < 0:
			return false
		if i == 0:
			return true
		var c := code.substr(i - 1, 1)
		if not (c == "_" or (c >= "a" and c <= "z") or (c >= "A" and c <= "Z") or (c >= "0" and c <= "9")):
			return true
		from = i + 1
	return false


func run(t: Object) -> void:
	var files: Array = []
	_scripts("res://", files)
	t.check(files.size() > 60, "the audit sees the game's scripts (%d)" % files.size())
	# ---- who may add fish ----------------------------------------------------------------------------------------------
	var add_callers: Array = []
	var hold_writers: Array = []
	var legacy: Array = []
	for f in files:
		var path := str(f)
		var src := _src(path)
		var code_lines := PackedStringArray()
		for line in src.split("\n"):
			var ln := (line as String).strip_edges()
			if ln.begins_with("#") or ln.begins_with("##"):
				continue
			code_lines.append(line)
		var code := "\n".join(code_lines)
		if _has_word(code, "add_catch(") or code.contains("\"add_catch\""):
			add_callers.append(path)
		for pat in ["lots.append", "lots.push_back", "lots.insert", "lots +=", "lots = ", "\"lots\", ", "kg_total +=", "kg_total = "]:
			if _has_word(code, pat):
				hold_writers.append(path)
				break
		for pat in ["_toggle_nets", "seconds_to_haul", "haul_interval", "session_by", "Lower the nets", "NETS DOWN", "KEY_F7"]:
			if code.contains(pat):
				legacy.append("%s: %s" % [path, pat])
	for p in add_callers:
		t.check(ADD_CALLERS_OK.has(p), "add_catch is called only from the winch and its definition (found in %s)" % p)
	t.check(add_callers.has("res://h2d/fish_manual.gd"), "the winch session does put its catch into the hold through add_catch")
	for p in hold_writers:
		t.check(HOLD_WRITERS_OK.has(p), "only port_state.gd writes the hold (found in %s)" % p)
	t.check(legacy.is_empty(), "no trace of the old net timer, its prompt, its HUD panel or an F7 fish cheat remains: %s" % str(legacy))
	# ---- the legacy net is gone from the class ---------------------------------------------------------------------------
	var f := Fishing.new()
	for m in ["roll", "start", "seconds_to_haul", "time_mult"]:
		t.check(not f.has_method(m), "Fishing has no `%s` any more" % m)
	var props: Array = []
	for pr in f.get_property_list():
		props.append(str((pr as Dictionary)["name"]))
	for pr in ["timer", "hauls", "session_kg", "session_by", "manual"]:
		t.check(not props.has(pr), "Fishing has no `%s` state any more" % pr)
	t.check(not Fishing.DEFAULTS.has("fish.haul_interval_s") and not Fishing.DEFAULTS.has("fish.haul_kg"), "the timed-haul tuning keys are not read by the game")
	var step_args := 0
	for m in f.get_method_list():
		if str((m as Dictionary)["name"]) == "step":
			step_args = ((m as Dictionary)["args"] as Array).size()
	t.check(step_args == 2, "step() takes only the ship and the sea: it cannot reach the hold (%d args)" % step_args)
	# ---- an hour on a ground with a held net gives only stop events, never a fish ---------------------------------------------
	var tuning := Ocean.load_tuning()
	f.configure(tuning, DataLoader.load_dict("res://data/port/fishing_grounds.json"), 7)
	var gid := str(f.ground_order[0])
	var g: Dictionary = f.grounds[gid]
	var r: Dictionary = f.start_manual(float(g["x"]), float(g["z"]), 4, 0.0)
	t.check(bool(r["ok"]) and f.active, "a winch session can hold the ground")
	var events := 0
	for i in 36000:                              # an hour of 0.1 s steps
		var ev: Array = f.step({"x": float(g["x"]), "z": float(g["z"]), "speed_kn": 0.2}, 0.0)
		events += ev.size()
	t.check(events == 0 and f.active, "an hour inside the ground with a slow ship: no event of any kind, nothing caught")
	var out: Array = f.step({"x": float(g["x"]) + 5000.0, "z": float(g["z"]), "speed_kn": 0.2}, 0.0)
	t.check(out.size() == 1 and str((out[0] as Dictionary)["type"]) == "stop" and not f.active, "leaving the ground only lets go of the net")
	# ---- selling still works ---------------------------------------------------------------------------------------------
	var st := PortState.new()
	st.configure(tuning, DataLoader.load_dict("res://data/port/fish_market.json"), DataLoader.load_dict("res://data/port/recruits_port.json"))
	var sp := str(st.fish.keys()[0])
	t.check(st.hold_kg() == 0.0, "a new hold is empty: nothing is given for free")
	var put := st.add_catch(sp, 10.0, 0.0)
	t.check(is_equal_approx(put, 10.0) and is_equal_approx(st.hold_kg(), 10.0), "add_catch stores exactly what it is given (once)")
	var purse := st.reales
	var sale: Dictionary = st.sell_all(0.0)
	t.check(int(sale["reales"]) > 0 and st.reales == purse + int(sale["reales"]), "selling pays the market price (%d reales)" % int(sale["reales"]))
	t.check(st.hold_kg() == 0.0 and st.lots.is_empty(), "the sale empties the hold")
	var again: Dictionary = st.sell_all(0.0)
	t.check(int(again["reales"]) == 0 and st.reales == purse + int(sale["reales"]), "selling the same fish twice pays once")
	# loading a save restores the hold without catching anything new
	var snap: Dictionary = st.to_dict()
	st.add_catch(sp, 4.0, 0.0)
	var kg_before := st.hold_kg()
	var saved: Dictionary = st.to_dict()
	var st2 := PortState.new()
	st2.configure(tuning, DataLoader.load_dict("res://data/port/fish_market.json"), DataLoader.load_dict("res://data/port/recruits_port.json"))
	st2.apply_dict(saved)
	t.check(is_equal_approx(st2.hold_kg(), kg_before), "loading a save restores the same hold, no more and no less (%.2f kg)" % st2.hold_kg())
	t.check(snap.has("lots"), "the save format still has the hold")
