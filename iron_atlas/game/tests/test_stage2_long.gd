extends SceneTree
## 365-day 200-region campaign and deterministic save/resume equivalence.
var checks := 0
var failures: Array = []
var frame := 0
var GS = null
var CLK = null
var saver = null
var baseline := ""
var expected_day := 0
var snapshot: Dictionary = {}
var checkpoint: Dictionary = {}


func check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures.append(label)


func _initialize() -> void:
	GS = root.get_node("GameState")
	CLK = root.get_node("CampaignClock")
	saver = load("res://persistence/save_system.gd").new()
	check(GS.new_campaign(97531, 200) == "", "large campaign created")


func _process(_delta: float) -> void:
	frame += 1
	if frame == 2:
		CLK.advance_days(90, GS.cs)
		check(GS.cs.day == 90 and GS.cs.outcome == "", "first 90 active days")
		checkpoint = GS.cs.serialize().duplicate(true)
		check(saver.save_campaign(GS.cs, 4, "long checkpoint") == "", "long campaign checkpoint")
		CLK.advance_days(120, GS.cs)
		expected_day = GS.cs.day
		snapshot = GS.cs.serialize().duplicate(true)
		baseline = JSON.stringify(snapshot, "", true, true)
		check(GS.cs.regions.size() == 200, "target scale remains intact")
	if frame == 3:
		var restored: Dictionary = saver.load_campaign(4)
		check(restored["error"] == "", "long checkpoint loaded")
		if restored["error"] != "":
			finish()
			return
		GS.adopt_state(restored["state"])
		check(first_diff(checkpoint, GS.cs.serialize(), "checkpoint") == "", "checkpoint restores exact state")
		CLK.advance_days(120, GS.cs)
		var resumed := JSON.stringify(GS.cs.serialize(), "", true, true)
		if resumed != baseline:
			print("DIFF ", first_diff(snapshot, GS.cs.serialize(), "state"))
		check(GS.cs.day == expected_day and resumed == baseline, "save/resume exactly matches uninterrupted simulation")
		CLK.advance_days(155, GS.cs)
		check(GS.cs.day == 365, "365 days simulated")
		check(is_finite(GS.cs.treasury), "player treasury remains finite")
		var owners_valid := true
		var quantities_valid := true
		var budgets_finite := true
		var stocks_valid := true
		for r in GS.cs.regions.values():
			if not GS.cs.countries.has(r["controller"]):
				owners_valid = false
			for value in r["stocks"].values():
				if not is_finite(float(value)) or float(value) < -0.0001:
					stocks_valid = false
		for cid in GS.cs.countries:
			if not is_finite(GS.cs.balance(cid)):
				budgets_finite = false
			for count in GS.cs.inventory_for(cid).values():
				if int(count) < 0:
					quantities_valid = false
		for f in GS.cs.formations.values():
			for u in f["units"]:
				if int(u["count"]) < 0:
					quantities_valid = false
		check(owners_valid, "all 200 controllers remain valid")
		check(quantities_valid, "no negative equipment or squads")
		check(budgets_finite, "all faction budgets remain finite")
		check(stocks_valid, "stockpiles remain nonnegative and finite")
		check(not GS.cs.reports.is_empty(), "long campaign produced real reports")
		finish()


func finish() -> void:
	print("TESTS: %s: %d checks" % ["PASS" if failures.is_empty() else "FAIL " + "; ".join(failures), checks])
	quit(0 if failures.is_empty() else 1)


func first_diff(a, b, path: String) -> String:
	if typeof(a) == TYPE_DICTIONARY and typeof(b) == TYPE_DICTIONARY:
		for key in a:
			if not b.has(key):
				return path + "." + str(key) + " missing"
			var nested := first_diff(a[key], b[key], path + "." + str(key))
			if nested != "":
				return nested
		for key in b:
			if not a.has(key):
				return path + "." + str(key) + " extra"
		return ""
	if typeof(a) == TYPE_ARRAY and typeof(b) == TYPE_ARRAY:
		if a.size() != b.size():
			return "%s array size %d != %d" % [path, a.size(), b.size()]
		for i in a.size():
			var nested := first_diff(a[i], b[i], path + "[" + str(i) + "]")
			if nested != "":
				return nested
		return ""
	if a != b:
		if typeof(a) in [TYPE_FLOAT, TYPE_INT] and typeof(b) in [TYPE_FLOAT, TYPE_INT]:
			return "%s %.20f != %.20f delta %.20f" % [path, float(a), float(b), float(a) - float(b)]
		return path + " " + str(a) + " != " + str(b)
	return ""
