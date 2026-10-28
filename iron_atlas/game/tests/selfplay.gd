extends SceneTree
## Long-run stability: 240 simulated days with AI, combat, economy, market and
## logistics active; asserts invariants then save/load round-trip.

var checks := 0
var failures: Array = []
var frames := 0
var GS = null
var CLK = null
var done := false


func ok(cond: bool, label: String) -> void:
	checks += 1
	if not cond:
		failures.append(label)


func _initialize() -> void:
	GS = root.get_node("GameState")
	CLK = root.get_node("CampaignClock")
	GS.new_campaign(90210)
	var dip = GS.diplomacy
	dip.declare_war(GS.cs, "cty_vardena", "cty_player", "selfplay pressure")


func _process(_delta: float) -> void:
	if done:
		return
	frames += 1
	if frames % 2 == 0 and GS.cs.day < 240:
		CLK.advance_days(2, GS.cs)
		return
	if GS.cs.day >= 240:
		done = true
		finish()


func finish() -> void:
	var st = GS.cs
	ok(st.day >= 240, "simulated 240 days")
	ok(is_finite(st.treasury), "treasury finite")
	ok(st.regions.size() == 24, "region count stable")
	for rid in st.regions:
		ok(st.regions[rid]["controller"] != "", "region owned: " + rid)
	for fid in st.formations:
		var f: Dictionary = st.formations[fid]
		ok(st.regions.has(f["region"]), "formation in valid region: " + fid)
		ok(float(f["morale"]) >= 0.0 and float(f["morale"]) <= 1.0, "morale bounded: " + fid)
	var sys = GS.get("market")  # keep reference sanity
	var SaveSys = load("res://persistence/save_system.gd")
	var saver = SaveSys.new()
	ok(saver.save_campaign(st, 4, "selfplay") == "", "selfplay save")
	var res = saver.load_campaign(4)
	ok(res["error"] == "" and res["state"].day == st.day, "selfplay load round-trip")
	if failures.is_empty():
		print("SELFPLAY PASS: %d checks" % checks)
	else:
		print("SELFPLAY FAIL: " + "; ".join(failures))
	quit(0 if failures.is_empty() else 1)
