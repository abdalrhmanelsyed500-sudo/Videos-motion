extends Node
## CP-2 Release B: the glue between the winch (the host's F key), the fishing state machine (fish_manual.gd), the first-person view
## (fish_view.gd) and the REAL fish hold (PortState, owned by the port controller). It owns nothing the other pieces own:
##   - the ship controller and the walker are not touched (the host blocks walking and steering while `active`);
##   - the state machine knows nothing about nodes, input or the hold except through `commit`;
##   - the hold is PortState.add_catch, the same call the passive nets and the market use. There is no temporary inventory.
## Input: the host forwards key events with key_event(); only the five fishing actions (and E in the two card stages) are consumed, so
## nothing here is a global input hook. Interruptions: abort() leaves safely from any stage (the net comes up empty before the
## cast is finished; a catch that already exists is kept); the session also ends itself when the passive-net rules (ground, sea
## state, sailing) stop the nets. When it ends the view is hidden and `active` is false, and the host restores the world.
## There is no audio system in the project yet: `sfx` is emitted with a name for each moment so a sound can be attached later.
## NOT YET RUN ON THE USER'S PC.
## name: "cast" | "splash" | "pull" | "bad_pull" | "warn" | "snap" | "raise" | "catch" | "unload" | "end"
signal sfx(name: String)
## info: {stored_kg, count, released_kg, text, cancelled, failed}
signal ended(info: Dictionary)

const Manual := preload("res://h2d/fish_manual.gd")
const View := preload("res://h2d/fish_view.gd")
const DataLoader := preload("res://core/data_loader.gd")
const Fishing := preload("res://h2d/fishing.gd")
const ShipKeys := preload("res://h2d/ship_keys.gd")

const LAYER := 40
const STOP_TEXT := {
	"left": "The ship drifted out of the fishing ground: the net was hauled in.",
	"rough": "The sea turned too rough: the net was hauled in.",
	"moored": "The ship is no longer sailing: the net was hauled in.",
	"full": "The hold is full.",
}

var manual: Manual = Manual.new()
var view: Control = null
var active := false
var configured := false
var last_report := ""
var last_info: Dictionary = {}
var problem := ""
var begun := 0                        # how many sessions were started (diagnostics, tests)
var _layer: CanvasLayer = null
var _pg: Node = null                  # the PortGame: .fishing (Fishing), .state (PortState)
var _names: Dictionary = {}
var _ctx: Dictionary = {}


## `tuning`: the merged tuning dictionary (Ocean.tuning()); `port_game`: the PortGame node. Returns false (and the session stays
## unavailable, with the reason in `problem`) when the data is missing.
func setup(parent: Node, tuning: Dictionary, port_game: Node) -> bool:
	_pg = port_game
	var doc := DataLoader.load_dict("res://data/port/manual_fishing.json")
	if doc.is_empty() or not doc.has("species") or not doc.has("profiles"):
		problem = "data/port/manual_fishing.json is missing or malformed"
		return false
	manual.configure(tuning, doc)
	_layer = CanvasLayer.new()
	_layer.layer = LAYER
	_layer.visible = false
	parent.add_child(_layer)
	view = View.new()
	_layer.add_child(view)
	(view as Object).call("setup", manual)
	configured = true
	return true


func is_ready() -> bool:
	return configured and _pg != null and _pg.get("fishing") != null and _pg.get("state") != null


func _fishing() -> Fishing:
	return _pg.get("fishing") as Fishing


func _state() -> RefCounted:
	return _pg.get("state") as RefCounted


## May the net go out here? {ok, reason}. The same rules as the passive nets plus a hold that has room.
func can_begin(ctx: Dictionary) -> Dictionary:
	if not is_ready():
		return {"ok": false, "reason": "The winch is not ready (%s)." % problem}
	if active:
		return {"ok": false, "reason": ""}
	var ps := _state()
	if bool(ps.call("is_full")):
		return {"ok": false, "reason": "The hold is full (%.0f kg). Sail home and sell the catch first." % float(ps.call("capacity_kg"))}
	var f := _fishing()
	var was_active := f.active
	var r := f.can_start(float(ctx["sx"]), float(ctx["sz"]), int(ps.call("crew_count")), float(ctx["sea"]))
	if not bool(r["ok"]):
		return r
	return {"ok": true, "reason": "", "passive_was_on": was_active}


## Start a session (the host has checked that the pirate stands at the winch). Returns {ok, reason}.
func begin(ctx: Dictionary) -> Dictionary:
	var c := can_begin(ctx)
	if not bool(c["ok"]):
		return c
	var f := _fishing()
	var ps := _state()
	if f.active:
		f.stop("manual")             # the passive nets give way to the winch
	var r := f.start_manual(float(ctx["sx"]), float(ctx["sz"]), int(ps.call("crew_count")), float(ctx["sea"]))
	if not bool(r["ok"]):
		return r
	var gid := f.ground_id
	var seed_v := f.seed_state
	f.seed_state = int((Fishing.next_rand(seed_v) as Array)[0])
	_names = {}
	for sid in (ps.get("fish") as Dictionary).keys():
		_names[str(sid)] = str(((ps.get("fish") as Dictionary)[sid] as Dictionary).get("name", sid))
	_ctx = ctx
	manual.begin(gid, f.grounds[gid] as Dictionary, {"hour": float(ctx["hour"]), "bonus": float(ps.call("effect", "catch_bonus")),
			"room_kg": float(ps.call("capacity_kg")) - float(ps.call("hold_kg")), "seed": seed_v})
	active = true
	begun += 1
	last_report = ""
	last_info = {}
	_refresh_env(ctx)
	(view as Object).set("visible", true)
	_layer.visible = true
	sfx.emit("cast")
	return {"ok": true, "reason": "", "ground": gid}


func _refresh_env(ctx: Dictionary) -> void:
	var ps := _state()
	var keys := {}
	for a in ["fish_haul_left", "fish_haul_right", "fish_cast", "fish_cancel", "ship_interact", "fish_winch"]:
		keys[a] = ShipKeys.label(a)
	var gname := ""
	var f := _fishing()
	if f.grounds.has(manual.ground_id):
		gname = str((f.grounds[manual.ground_id] as Dictionary).get("name", ""))
	(view as Object).call("set_env", {"hour": float(ctx.get("hour", 12.0)), "sea": float(ctx.get("sea", 0.2)), "light": float(ctx.get("light", 1.0)),
			"roll": float(ctx.get("roll", 0.0)), "ground": gname, "hold_kg": float(ps.call("hold_kg")), "capacity": float(ps.call("capacity_kg")),
			"names": _names, "keys": keys})


## Every frame while `active`. ctx: {speed_kn, hour, sea, light, now, sx, sz}.
func tick(dt: float, ctx: Dictionary) -> void:
	if not active:
		return
	_ctx = ctx
	var f := _fishing()
	if not f.active and manual.stage != Manual.Stage.DONE:
		abort(str(STOP_TEXT.get(f.stop_reason, "The net was hauled in.")))
		return
	var evs := manual.step(dt, {"speed_kn": float(ctx.get("speed_kn", 0.0)), "max_speed_kn": float(f.p["fish.max_speed_kn"])})
	_after(evs)
	_refresh_env(ctx)
	(view as Object).call("tick", dt)
	if manual.stage == Manual.Stage.DONE:
		_finish(false)


## One key event from the host. Returns true when it was consumed.
func key_event(k: InputEventKey) -> bool:
	if not active or k == null or not k.pressed or k.echo:
		return false
	var evs: Array = []
	if ShipKeys.hit(k, "fish_cancel"):
		evs = manual.cancel()
	elif ShipKeys.hit(k, "fish_haul_left"):
		evs = manual.press("left")
	elif ShipKeys.hit(k, "fish_haul_right"):
		evs = manual.press("right")
	elif ShipKeys.hit(k, "fish_cast"):
		evs = manual.press("cast")
	elif ShipKeys.hit(k, "ship_interact"):
		evs = manual.press("confirm")
	else:
		return false          # every other key is left alone (the host ignores it while the view is up)
	_after(evs)
	if manual.stage == Manual.Stage.DONE:
		_finish(false)
	return true


func _after(evs: Array) -> void:
	if evs.is_empty():
		return
	(view as Object).call("on_events", evs)
	for e in evs:
		var d: Dictionary = e
		match str(d["type"]):
			"cast":
				sfx.emit("splash")
			"pull_ok":
				sfx.emit("pull")
			"pull_bad":
				sfx.emit("bad_pull")
			"surge_warn":
				sfx.emit("warn")
			"fail":
				sfx.emit("snap" if str(d["reason"]) == "snap" else "end")
			"hauled":
				sfx.emit("raise")
			"stage":
				if int(d["stage"]) == Manual.Stage.SUMMARY:
					sfx.emit("catch")
				elif int(d["stage"]) == Manual.Stage.UNLOAD:
					sfx.emit("unload")
					_commit()      # the fish go into the REAL hold now: the barrels, the storage panel and the market see them at once


func _commit() -> void:
	if manual.committed or manual.result.is_empty() or bool(manual.result.get("failed", false)):
		return
	var ps := _state()
	manual.commit(ps, float(_ctx.get("now", 0.0)))
	var st: Dictionary = manual.stored
	var parts: Array = []
	for sid in (st.get("stored", {}) as Dictionary).keys():
		parts.append("%s %.1f kg" % [str(_names.get(str(sid), sid)), float((st["stored"] as Dictionary)[sid])])
	last_report = "Stored %d fish (%s). Hold %.1f / %.0f kg." % [int(st.get("count_stored", 0)), ", ".join(PackedStringArray(parts)), float(ps.call("hold_kg")), float(ps.call("capacity_kg"))]
	if float(st.get("released", 0.0)) > 0.05:
		last_report += " %.1f kg went back into the sea: the hold was full." % float(st["released"])


## Leave NOW, from any stage (interruption, reset, the ground lost). A catch that already exists is kept and stored.
func abort(reason: String = "") -> void:
	if not active:
		return
	if manual.stage == Manual.Stage.SUMMARY or manual.stage == Manual.Stage.UNLOAD or manual.stage == Manual.Stage.RAISE:
		if manual.stage == Manual.Stage.RAISE and not manual.result.is_empty():
			manual.stage = Manual.Stage.SUMMARY
		_commit()
	_finish(true, reason)


func _finish(was_abort: bool, reason: String = "") -> void:
	if not active:
		return
	_commit()
	var f := _fishing()
	if f.active and f.manual:
		f.stop("manual_done")
	active = false
	var failed := bool(manual.result.get("failed", false))
	var st: Dictionary = manual.stored
	var kg := 0.0
	for sid in (st.get("stored", {}) as Dictionary).keys():
		kg += float((st["stored"] as Dictionary)[sid])
	var text := last_report
	if text == "":
		if reason != "":
			text = reason
		elif failed:
			text = "The haul was lost. Nothing was stored."
		else:
			text = "You let go of the winch. The net came back empty."
	elif reason != "":
		text += " " + reason
	last_info = {"stored_kg": kg, "count": int(st.get("count_stored", 0)), "released_kg": float(st.get("released", 0.0)), "text": text,
			"cancelled": was_abort or manual.result.is_empty(), "failed": failed}
	(view as Object).set("visible", false)
	_layer.visible = false
	manual.stage = Manual.Stage.DONE
	sfx.emit("end")
	ended.emit(last_info)


func _exit_tree() -> void:
	active = false
