extends RefCounted
## The fishing grounds and the rules of the winch (CP-2B.1: manual fishing is the ONLY way to catch fish).
## This class knows WHERE fish are (the grounds of data/port/fishing_grounds.json), whether the net may go out here (ground, crew,
## sea state, ship speed) and keeps hold of the ground while a winch session runs (the ship must stay slow and inside the disc).
## It does NOT catch anything: the old timed "nets down, a haul every 12 s" path (CP-1) was removed in CP-2B.1. Fish enter the hold only
## through the winch session (h2d/fish_session.gd + h2d/fish_manual.gd). It also holds the tiny deterministic generator
## (a = 1103515245, c = 12345, m = 2^31) that the winch session uses to choose species. Pure logic.
const DEFAULTS := {
	"fish.max_speed_kn": 1.5, "fish.max_sea": 0.6,
}
const LCG_A := 1103515245
const LCG_C := 12345
const LCG_M := 2147483648

var p: Dictionary = DEFAULTS.duplicate()
var grounds: Dictionary = {}         # id -> record of fishing_grounds.json
var ground_order: Array = []
var seed_state := 1
var active := false
var ground_id := ""
var status := "idle"                 # idle | working | drifting | stopped (active = a winch session holds the ground)
var stop_reason := ""


func configure(tuning: Dictionary, grounds_doc: Dictionary, seed_value: int = 1) -> void:
	p = DEFAULTS.duplicate()
	for k in DEFAULTS.keys():
		if tuning.has(k):
			p[k] = float(tuning[k])
	grounds = grounds_doc["grounds"]
	ground_order = grounds.keys()
	seed_state = seed_value
	reset()


func reset() -> void:
	active = false
	ground_id = ""
	status = "idle"
	stop_reason = ""


# ---- the random stream ---------------------------------------------------------------------------------------------
## One step of the generator: [new state, value in 0..1).
static func next_rand(state: int) -> Array:
	var s := (LCG_A * state + LCG_C) % LCG_M
	return [s, float(s) / float(LCG_M)]


# ---- grounds ---------------------------------------------------------------------------------------------------------
## The id of the ground whose disc holds (x, z), or "".
func ground_at(px: float, pz: float) -> String:
	for id in ground_order:
		var g: Dictionary = grounds[id]
		var dx := px - float(g["x"])
		var dz := pz - float(g["z"])
		if dx * dx + dz * dz <= float(g["r"]) * float(g["r"]):
			return str(id)
	return ""


## The nearest ground: {id, dist_m (to its edge, 0 inside), bearing_deg}.
func nearest_ground(px: float, pz: float, crew_count: int = 99) -> Dictionary:
	var best := {"id": "", "dist_m": 1.0e9, "bearing_deg": 0.0}
	for id in ground_order:
		var g: Dictionary = grounds[id]
		if int(g["min_crew"]) > crew_count:
			continue
		var dx := float(g["x"]) - px
		var dz := float(g["z"]) - pz
		var d := maxf(sqrt(dx * dx + dz * dz) - float(g["r"]), 0.0)
		if d < float(best["dist_m"]):
			best = {"id": str(id), "dist_m": d, "bearing_deg": fposmod(rad_to_deg(atan2(dx, -dz)), 360.0)}
	return best


## May the net go out here (the winch asks)? {ok, reason (a sentence for the player)}.
func can_start(px: float, pz: float, crew_count: int, sea_index: float) -> Dictionary:
	var id := ground_at(px, pz)
	if id == "":
		var n := nearest_ground(px, pz)
		var g: Dictionary = grounds[str(n["id"])]
		return {"ok": false, "reason": "No fish here. The nearest ground is %s, %d m away (see the chart, M)." % [str(g["name"]), int(roundf(float(n["dist_m"])))]}
	var gr: Dictionary = grounds[id]
	if int(gr["min_crew"]) > crew_count:
		return {"ok": false, "reason": "%s needs at least %d hand aboard: the water is too deep to work alone. Hire a recruit first." % [str(gr["name"]), int(gr["min_crew"])]}
	if sea_index > float(p["fish.max_sea"]):
		return {"ok": false, "reason": "The sea is too rough to work the nets (sea state %.2f, the limit is %.2f)." % [sea_index, float(p["fish.max_sea"])]}
	return {"ok": true, "reason": "", "ground": id}


## The winch session asks for the ground. Same checks as can_start; on success the ship is held (slow, inside the ground).
func start_manual(px: float, pz: float, crew_count: int, sea_index: float) -> Dictionary:
	var r := can_start(px, pz, crew_count, sea_index)
	if bool(r["ok"]):
		active = true
		ground_id = str(r["ground"])
		status = "drifting"
		stop_reason = ""
	return r


func stop(reason: String = "") -> void:
	if not active:
		return
	active = false
	status = "stopped"
	stop_reason = reason


## Keeps the winch session honest. `ship` = {x, z, speed_kn}; `sea_index` 0..1. Returns [{type: "stop", reason, text}] when the ground
## is lost or the sea is too rough (the session then lets go). It never catches or stores anything.
func step(ship: Dictionary, sea_index: float) -> Array:
	var events: Array = []
	if not active:
		return events
	if ground_at(float(ship["x"]), float(ship["z"])) != ground_id:
		stop("left")
		events.append({"type": "stop", "reason": "left", "text": "The ship drifted out of the fishing ground: the net was hauled in."})
	elif sea_index > float(p["fish.max_sea"]):
		stop("rough")
		events.append({"type": "stop", "reason": "rough", "text": "The sea is too rough: the net was hauled in."})
	else:
		status = "drifting" if float(ship["speed_kn"]) > float(p["fish.max_speed_kn"]) else "working"
	return events
