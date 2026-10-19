extends RefCounted
## CP-1 fishing: the nets go down inside a fishing ground (F), the ship drifts to a stop, and every fish.haul_interval_s
## real seconds the nets come up with one haul: a species drawn by the ground's weights and kg = fish.haul_kg x ground
## richness x time-of-day factor x (1 + crew bonus) x (1 +/- fish.haul_spread). Fishing stops by itself when the hold is
## full, the sea gets rough (fish.max_sea) or the ship leaves the ground. The draw uses a tiny deterministic generator
## (a = 1103515245, c = 12345, m = 2^31) shared with the Python twin tools/h2d/economy_logic.py, so a given seed gives the same
## fish in both (tests/fixtures/economy_cases.json). Pure logic; NOT YET RUN IN GODOT.
const DEFAULTS := {
	"fish.haul_interval_s": 12.0, "fish.haul_kg": 1.2, "fish.haul_spread": 0.4, "fish.max_speed_kn": 1.5, "fish.max_sea": 0.6,
	"fish.mult_dawn": 1.3, "fish.mult_day": 1.0, "fish.mult_night": 0.7,
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
var timer := 0.0
var hauls := 0
var session_kg := 0.0
var status := "idle"                 # idle | working | drifting | stopped
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
	timer = 0.0
	hauls = 0
	session_kg = 0.0
	status = "idle"
	stop_reason = ""


# ---- the random stream ---------------------------------------------------------------------------------------------
## One step of the generator: [new state, value in 0..1).
static func next_rand(state: int) -> Array:
	var s := (LCG_A * state + LCG_C) % LCG_M
	return [s, float(s) / float(LCG_M)]


static func time_mult(hour: float, tuning: Dictionary) -> float:
	if (hour >= 5.0 and hour < 7.0) or (hour >= 17.0 and hour < 19.0):
		return float(tuning["fish.mult_dawn"])
	if hour >= 20.0 or hour < 5.0:
		return float(tuning["fish.mult_night"])
	return float(tuning["fish.mult_day"])


## One haul from `ground` (record) with the stored generator state. Returns {species, kg}.
func roll(ground: Dictionary, mult: float, bonus: float) -> Dictionary:
	var a := next_rand(seed_state)
	var b := next_rand(int(a[0]))
	seed_state = int(b[0])
	var r1 := float(a[1])
	var r2 := float(b[1])
	var total := 0.0
	for sw in ground["species"]:
		total += float((sw as Array)[1])
	var acc := 0.0
	var list: Array = ground["species"]
	var species := str((list[list.size() - 1] as Array)[0])
	for sw in list:
		acc += float((sw as Array)[1]) / total
		if r1 < acc:
			species = str((sw as Array)[0])
			break
	var kg := float(p["fish.haul_kg"]) * float(ground["richness"]) * mult * (1.0 + bonus) * (1.0 + float(p["fish.haul_spread"]) * (2.0 * r2 - 1.0))
	kg = floorf(kg * 100.0 + 0.5) / 100.0
	return {"species": species, "kg": kg}


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


## F pressed at sea: may the nets go down here? {ok, reason (a sentence for the player)}.
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


func start(px: float, pz: float, crew_count: int, sea_index: float) -> Dictionary:
	var r := can_start(px, pz, crew_count, sea_index)
	if bool(r["ok"]):
		active = true
		ground_id = str(r["ground"])
		timer = 0.0
		hauls = 0
		session_kg = 0.0
		status = "drifting"
		stop_reason = ""
	return r


func stop(reason: String = "") -> void:
	if not active:
		return
	active = false
	status = "stopped"
	stop_reason = reason


## Seconds until the next haul (0 when idle).
func seconds_to_haul() -> float:
	return maxf(float(p["fish.haul_interval_s"]) - timer, 0.0) if active else 0.0


## Advance the nets. `ship` = {x, z, speed_kn}; `hour` 0..24; `sea_index` 0..1; `port` = the PortState; `now` = game days.
## Returns a list of events: {type: "haul", species, kg, stored, full} or {type: "stop", reason, text}.
func step(dt: float, ship: Dictionary, hour: float, sea_index: float, port: RefCounted, now: float) -> Array:
	var events: Array = []
	if not active:
		return events
	if ground_at(float(ship["x"]), float(ship["z"])) != ground_id:
		stop("left")
		events.append({"type": "stop", "reason": "left", "text": "The ship drifted out of the fishing ground: nets up."})
		return events
	if sea_index > float(p["fish.max_sea"]):
		stop("rough")
		events.append({"type": "stop", "reason": "rough", "text": "The sea is too rough: nets hauled in."})
		return events
	if float(ship["speed_kn"]) > float(p["fish.max_speed_kn"]):
		status = "drifting"      # the nets drag: the ship is still slowing down, nothing is caught yet
		return events
	status = "working"
	timer += dt
	var interval := float(p["fish.haul_interval_s"])
	while timer >= interval:
		timer -= interval
		var g: Dictionary = grounds[ground_id]
		var bonus := float(port.call("effect", "catch_bonus"))
		var h := roll(g, time_mult(hour, p), bonus)
		var stored := float(port.call("add_catch", str(h["species"]), float(h["kg"]), now))
		hauls += 1
		session_kg += stored
		var full := bool(port.call("is_full"))
		events.append({"type": "haul", "species": str(h["species"]), "kg": float(h["kg"]), "stored": stored, "full": full})
		if full:
			stop("full")
			events.append({"type": "stop", "reason": "full", "text": "The hold is full: nets up. Sail home and sell the catch."})
			break
	return events
