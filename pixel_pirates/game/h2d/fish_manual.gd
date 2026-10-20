# gdlint: disable=class-definitions-order
extends RefCounted
## CP-2 Release B: the manual fishing state machine. Pure logic (no scene, no input, no drawing): the host gives it presses and
## time, it gives back events and the numbers the first-person view draws. tests/test_fish_manual.gd drives it with simulated players.
##
##   HEAVE   the ship slows below the fishing speed (the nets' drag, as with the passive nets)
##   AIM     stage 1: a needle sweeps a bar, one press casts: the green zone gives a wide, deep net (cast quality)
##   SINK    the net goes down on the rope        SOAK  the shoal gathers over it
##   HAUL    stage 2: pull the two levers ALTERNATELY at the right pace (A, D by default: actions fish_haul_left / _right)
##   RAISE   stage 3: the winch lifts the net out of the water      SUMMARY  the catch card      UNLOAD  the fish go to the barrels
##   FAIL    the haul went wrong (explained)      CANCEL  the net comes back up empty      DONE  the session is over
##
## Hauling in one paragraph: every correct (alternating) pull gives progress; the pace decides how much (the ideal gap is
## mfish.ideal_interval_s, much faster or much slower is worth less), a streak of good pulls gives up to +36 %, the same lever twice
## is worth a quarter and breaks the streak. The ROPE TENSION rises with each pull (more when the pulls come too fast) and relaxes
## towards what the fish do (a slow wobble, and every few seconds a SURGE: the fish runs = tension up, or turns = tension down,
## announced 0.8 s before). Tension above the band strains the rope (it snaps at 1.0: the haul fails), below the band the rope is slack
## and fish slip out. Catch integrity is what is left of the shoal; with the cast quality, the efficiency (haul time against par) and
## the best streak it makes the catch quality, which scales the kg. Every number is data/tuning/tuning_mfish.json (keys mfish.*);
## data/port/manual_fishing.json has the species weights and the ground profiles. NOT YET RUN ON THE USER'S PC.
const Fishing := preload("res://h2d/fishing.gd")
const Catch := preload("res://h2d/fish_catch.gd")

enum Stage { IDLE, HEAVE, AIM, SINK, SOAK, HAUL, RAISE, SUMMARY, UNLOAD, DONE, FAIL, CANCEL }

const DEFAULTS := {
	"heave_timeout_s": 30.0, "aim_period_s": 1.7, "aim_good_half": 0.11, "aim_timeout_s": 14.0, "sink_s": 2.2, "soak_s": 2.4,
	"ideal_interval_s": 0.42, "pace_lo": 0.7, "pace_hi": 1.6, "press_gain": 0.040, "repeat_factor": 0.25, "streak_step": 0.015,
	"streak_cap": 24.0, "tension_base": 0.42, "tension_wobble": 0.13, "tension_decay": 2.4, "tension_press": 0.09, "band_lo": 0.38,
	"band_hi": 0.72, "strain_rate": 4.0, "strain_cool": 0.2, "slack_loss": 0.06, "strain_loss": 0.05, "idle_loss": 0.04,
	"repeat_loss": 0.012, "slip_rate": 0.03, "surge_gap_min_s": 3.0, "surge_gap_max_s": 5.5, "surge_warn_s": 0.8, "surge_s": 1.1,
	"surge_mag": 0.55, "haul_timeout_s": 40.0, "par_s": 9.5, "raise_s": 3.4, "unload_s": 2.4, "cancel_s": 1.4, "haul_kg": 5.0,
	"kg_spread": 0.25, "second_species": 0.45,
}
const PREFIX := "mfish."
const AIM_CENTER := 0.5

var p: Dictionary = DEFAULTS.duplicate()
var species: Dictionary = {}          ## species id -> {avg_kg, icon, note}
var profiles: Dictionary = {}         ## ground id -> {pull, surge, shy, label}

var stage: int = Stage.IDLE
var stage_t := 0.0                    ## seconds in this stage
var ground_id := ""
var ground: Dictionary = {}
var profile: Dictionary = {"pull": 1.0, "surge": 1.0, "shy": 1.0, "label": ""}
var potential_kg := 0.0               ## the fish in the net before the quality of the work scales it
var shoal_shares: Array = []          ## [[species, share]] decided at the cast
var cast_q := 1.0                     ## 0.55 .. 1.15
var cast_grade := ""
var aim := 0.0                        ## the needle 0..1
var depth := 0.0                      ## the net: 0 at the pulley, 1 deep
var progress := 0.0
var tension := 0.42
var strain := 0.0
var integrity := 1.0
var streak := 0
var best_streak := 0
var pulls := 0
var repeats := 0
var haul_t := 0.0
var last_side := ""
var since_press := 0.0
var surge_kind := 0                   ## +1 the fish runs (tension up), -1 it turns (tension down), 0 none
var surge_phase := 0                  ## 0 none, 1 warning, 2 active
var surge_left := 0.0
var next_surge := 4.0
var message := ""                     ## the warning the view shows, "" when all is well
var message_kind := ""                ## "ok", "warn", "bad"
var pace_state := ""                  ## "good", "fast", "slow" or "" for the last pull
var winch_angle := 0.0                ## radians: the view spins the drum
var lever := 0.0                      ## -1 left lever down .. +1 right lever down (animation)
var result: Dictionary = {}
var fail_reason := ""
var fail_text := ""
var committed := false
var stored: Dictionary = {}           ## what the hold took: {species: kg}, "released": kg
var heave_note := ""
var _rng := 1
var _hour := 12.0
var _bonus := 0.0
var _room_kg := 40.0
var _last_pull_t := -9.0
var _raise_from := 1.0


func configure(tuning: Dictionary, manual_doc: Dictionary) -> void:
	p = DEFAULTS.duplicate()
	for k in DEFAULTS.keys():
		var full: String = PREFIX + str(k)
		if tuning.has(full):
			p[k] = float(tuning[full])
	species = manual_doc.get("species", {})
	profiles = manual_doc.get("profiles", {})
	stage = Stage.IDLE


func is_active() -> bool:
	return stage != Stage.IDLE and stage != Stage.DONE


func stage_name() -> String:
	return str(Stage.keys()[stage])


func _rand() -> float:
	var r := Fishing.next_rand(_rng)
	_rng = int(r[0])
	return float(r[1])


func _set_stage(s: int) -> Array:
	stage = s
	stage_t = 0.0
	if s == Stage.RAISE or s == Stage.CANCEL:
		_raise_from = depth
	return [{"type": "stage", "stage": s, "name": stage_name()}]


## Start a session on `ground_id`. ctx: {hour, bonus (crew catch bonus), room_kg (free space in the hold), seed}.
func begin(gid: String, ground_rec: Dictionary, ctx: Dictionary) -> Array:
	ground_id = gid
	ground = ground_rec
	profile = (profiles.get(gid, {"pull": 1.0, "surge": 1.0, "shy": 1.0, "label": ""}) as Dictionary)
	_hour = float(ctx.get("hour", 12.0))
	_bonus = float(ctx.get("bonus", 0.0))
	_room_kg = float(ctx.get("room_kg", 40.0))
	_rng = int(ctx.get("seed", 20261020)) % Fishing.LCG_M
	if _rng <= 0:
		_rng = 1
	potential_kg = 0.0
	shoal_shares = []
	cast_q = 1.0
	cast_grade = ""
	aim = 0.0
	depth = 0.0
	progress = 0.0
	tension = float(p["tension_base"])
	strain = 0.0
	integrity = 1.0
	streak = 0
	best_streak = 0
	pulls = 0
	repeats = 0
	haul_t = 0.0
	last_side = ""
	since_press = 0.0
	surge_kind = 0
	surge_phase = 0
	surge_left = 0.0
	next_surge = lerpf(float(p["surge_gap_min_s"]), float(p["surge_gap_max_s"]), _rand())
	message = ""
	message_kind = ""
	pace_state = ""
	winch_angle = 0.0
	lever = 0.0
	result = {}
	fail_reason = ""
	fail_text = ""
	committed = false
	stored = {}
	heave_note = ""
	_last_pull_t = -9.0
	return _set_stage(Stage.HEAVE)


## Time-of-day factor with the passive nets' own tuning keys (dawn and dusk good, night poor).
func _time_mult() -> float:
	var h := _hour
	if (h >= 5.0 and h < 7.0) or (h >= 17.0 and h < 19.0):
		return 1.3
	if h >= 20.0 or h < 5.0:
		return 0.7
	return 1.0


## One frame. ctx: {speed_kn, max_speed_kn}. Returns events (dictionaries with "type").
func step(dt: float, ctx: Dictionary) -> Array:
	var ev: Array = []
	if stage == Stage.IDLE or stage == Stage.DONE:
		return ev
	stage_t += dt
	match stage:
		Stage.HEAVE:
			var lim := float(ctx.get("max_speed_kn", 1.5))
			var sp := float(ctx.get("speed_kn", 0.0))
			heave_note = "The ship is slowing: %.1f kn, the net goes out under %.1f kn." % [sp, lim]
			if sp <= lim:
				aim = 0.0
				ev.append_array(_set_stage(Stage.AIM))
			elif stage_t > float(p["heave_timeout_s"]):
				ev.append_array(_fail("heave", "The ship would not slow down in time (%.1f kn). Nothing was lost: try again." % sp))
		Stage.AIM:
			var per := maxf(float(p["aim_period_s"]), 0.2)
			aim = 0.5 - 0.5 * cos(TAU * stage_t / per)       # 0 -> 1 -> 0, a smooth sweep starting at the left end
			if stage_t > float(p["aim_timeout_s"]):
				ev.append_array(_cast(-1.0))
		Stage.SINK:
			depth = clampf(stage_t / maxf(float(p["sink_s"]), 0.1), 0.0, 1.0)
			winch_angle -= dt * 6.0 * (1.0 - depth)
			if stage_t >= float(p["sink_s"]):
				ev.append_array(_set_stage(Stage.SOAK))
		Stage.SOAK:
			depth = 1.0
			if stage_t >= float(p["soak_s"]):
				ev.append_array(_set_stage(Stage.HAUL))
				message = "Pull the levers one after the other!"
				message_kind = "ok"
		Stage.HAUL:
			ev.append_array(_haul_step(dt))
		Stage.RAISE:
			var k := clampf(stage_t / maxf(float(p["raise_s"]), 0.1), 0.0, 1.0)
			depth = _raise_from * (1.0 - k * k * (3.0 - 2.0 * k))     # from where the haul left the net up to the pulley
			winch_angle += dt * 7.0 * (1.0 - 0.6 * k)
			if k >= 1.0:
				ev.append_array(_set_stage(Stage.SUMMARY))
		Stage.UNLOAD:
			if stage_t >= float(p["unload_s"]):
				ev.append_array(_set_stage(Stage.DONE))
		Stage.CANCEL:
			depth = _raise_from * (1.0 - clampf(stage_t / maxf(float(p["cancel_s"]), 0.1), 0.0, 1.0))
			winch_angle += dt * 6.0
			if stage_t >= float(p["cancel_s"]):
				depth = 0.0
				ev.append_array(_set_stage(Stage.DONE))
	lever = move_toward(lever, 0.0, dt * 6.0)
	return ev


func _cast(accuracy_off: float) -> Array:
	# accuracy_off: distance of the needle from the middle of the bar (0 perfect); a negative value means "no press" (weak)
	var half := float(p["aim_good_half"])
	var q := 0.55
	var grade := "Weak cast"
	if accuracy_off >= 0.0:
		if accuracy_off <= half * 0.4:
			q = 1.15
			grade = "Perfect cast"
		elif accuracy_off <= half:
			q = 1.0
			grade = "Good cast"
		elif accuracy_off <= half * 2.2:
			q = 0.8
			grade = "Fair cast"
	cast_q = q
	cast_grade = grade
	# the shoal under the net: species, size
	var pick := Catch.pick_species(ground, _rng, float(p["second_species"]))
	_rng = int(pick["state"])
	shoal_shares = pick["species"]
	var spread := float(p["kg_spread"])
	var size := 1.0 + spread * (2.0 * _rand() - 1.0)
	potential_kg = float(p["haul_kg"]) * float(ground.get("richness", 1.0)) * _time_mult() * (1.0 + _bonus) * size
	var ev := _set_stage(Stage.SINK)
	ev.append({"type": "cast", "grade": grade, "quality": q})
	return ev


func _fail(reason: String, text: String) -> Array:
	fail_reason = reason
	fail_text = text
	message = ""
	result = {"fish": [], "count": 0, "kg": 0.0, "q": 0.0, "grade": "None", "failed": true, "reason": reason, "text": text}
	var ev := _set_stage(Stage.FAIL)
	ev.append({"type": "fail", "reason": reason, "text": text})
	return ev


func _set_message(text: String, kind: String) -> void:
	message = text
	message_kind = kind


func _haul_step(dt: float) -> Array:
	var ev: Array = []
	haul_t += dt
	since_press += dt
	# the fish: slow wobble plus a surge now and then
	var wob := float(p["tension_wobble"]) * float(profile["pull"]) * (0.6 * sin(1.3 * haul_t + 0.7) + 0.4 * sin(2.9 * haul_t + 2.1))
	var surge_off := 0.0
	if surge_phase == 0:
		next_surge -= dt
		if next_surge <= 0.0:
			surge_kind = 1 if _rand() < 0.6 else -1
			surge_phase = 1
			surge_left = float(p["surge_warn_s"])
			ev.append({"type": "surge_warn", "kind": surge_kind})
	elif surge_phase == 1:
		surge_left -= dt
		_set_message("THE FISH IS ABOUT TO RUN: ease off!" if surge_kind > 0 else "THE FISH IS TURNING: haul faster!", "warn")
		if surge_left <= 0.0:
			surge_phase = 2
			surge_left = float(p["surge_s"])
	elif surge_phase == 2:
		surge_left -= dt
		var mag := float(p["surge_mag"]) * float(profile["surge"])
		surge_off = float(surge_kind) * mag * sin(PI * clampf(1.0 - surge_left / maxf(float(p["surge_s"]), 0.1), 0.0, 1.0))
		_set_message("THE FISH RUNS: let the rope breathe!" if surge_kind > 0 else "SLACK: pull, pull!", "warn")
		if surge_left <= 0.0:
			surge_phase = 0
			surge_kind = 0
			next_surge = lerpf(float(p["surge_gap_min_s"]), float(p["surge_gap_max_s"]), _rand())
	var target := float(p["tension_base"]) + wob + surge_off
	tension += (target - tension) * minf(float(p["tension_decay"]) * dt, 1.0)
	tension = clampf(tension, 0.0, 1.1)
	var band_lo := float(p["band_lo"])
	var band_hi := float(p["band_hi"])
	# the rope
	if tension > band_hi:
		strain += (tension - band_hi) * float(p["strain_rate"]) * dt
	else:
		strain = maxf(0.0, strain - float(p["strain_cool"]) * dt)
	var shy := float(profile["shy"])
	if tension < band_lo:
		integrity -= float(p["slack_loss"]) * shy * dt * (1.0 + (band_lo - tension) * 3.0)
	if strain > 0.25:
		integrity -= float(p["strain_loss"]) * clampf((strain - 0.2) * 2.5, 0.0, 2.0) * dt
	if since_press > 1.4 and progress > 0.0:
		integrity -= float(p["idle_loss"]) * shy * dt
	if since_press > 0.9:
		progress = maxf(0.0, progress - float(p["slip_rate"]) * dt)
	integrity = clampf(integrity, 0.0, 1.0)
	# the messages (a surge's own text wins while it lasts)
	if surge_phase == 0:
		if strain > 0.5:
			_set_message("The rope is groaning: ease off!", "bad")
		elif tension > band_hi:
			_set_message("Too tight: slow down!", "warn")
		elif tension < band_lo:
			_set_message("Slack rope: fish are slipping out!", "warn")
		elif since_press > 1.4:
			_set_message("Keep pulling!", "warn")
		elif pace_state == "fast":
			_set_message("Too fast: find the rhythm.", "warn")
		elif pace_state == "slow":
			_set_message("Pull a little quicker.", "warn")
		elif streak >= 6:
			_set_message("Good rhythm! Streak x%d" % streak, "ok")
		else:
			_set_message("", "ok")
	# the ways it ends
	if strain >= 1.0:
		ev.append_array(_fail("snap", "The rope snapped under the strain and the catch fell back into the sea. Ease off when the rope groans or the fish runs, and pull at a steady beat."))
	elif integrity <= 0.12:
		ev.append_array(_fail("escaped", "The shoal slipped out of the net. A slack rope or long pauses let the fish go: keep the rope taut and keep pulling."))
	elif haul_t > float(p["haul_timeout_s"]):
		ev.append_array(_fail("tired", "You tired before the net came up and the shoal moved on. Pull at a steady beat: alternate the two levers."))
	elif progress >= 1.0:
		progress = 1.0
		ev.append_array(_finish_haul())
	return ev


func _finish_haul() -> Array:
	var eff := clampf(float(p["par_s"]) / maxf(haul_t, 0.1), 0.0, 1.0)
	var streak_score := clampf(float(best_streak) / maxf(float(p["streak_cap"]), 1.0), 0.0, 1.0)
	var q := pow(integrity, 0.8) * (0.55 + 0.45 * eff) * (0.75 + 0.25 * streak_score) * cast_q
	q = clampf(q, 0.05, 1.3)
	var kg := potential_kg * q
	var spread := float(p["kg_spread"]) * 0.4
	var cp := Catch.compose(shoal_shares, kg, species, _rng, spread)
	_rng = int(cp["state"])
	result = {"fish": cp["fish"], "count": cp["count"], "kg": cp["kg"], "q": q, "grade": Catch.grade_for(q), "efficiency": eff,
		"integrity": integrity, "best_streak": best_streak, "cast": cast_grade, "haul_s": haul_t, "pulls": pulls, "failed": false,
		"potential_kg": potential_kg, "ground": ground_id}
	message = ""
	var ev := _set_stage(Stage.RAISE)
	ev.append({"type": "hauled", "quality": q})
	return ev


## An input. which: "left" | "right" | "cast" | "confirm". Returns events.
func press(which: String) -> Array:
	var ev: Array = []
	match stage:
		Stage.AIM:
			if which == "cast":
				ev.append_array(_cast(absf(aim - AIM_CENTER)))
		Stage.HAUL:
			if which == "left" or which == "right":
				ev.append_array(_pull(which))
		Stage.SUMMARY:
			if which == "confirm" or which == "cast":
				ev.append_array(unload())
		Stage.FAIL:
			if which == "confirm" or which == "cast":
				ev.append_array(_set_stage(Stage.DONE))
	return ev


func _pull(side: String) -> Array:
	var ev: Array = []
	var now := haul_t
	var gap := now - _last_pull_t
	var ideal := float(p["ideal_interval_s"])
	var repeat := side == last_side and last_side != ""
	var r := 1.0 if (_last_pull_t < -1.0 or gap > 3.0) else gap / ideal
	var pf := 1.0
	var lo := float(p["pace_lo"])
	var hi := float(p["pace_hi"])
	if r < lo:
		pf = maxf(0.05, pow(clampf((r - 0.3) / maxf(lo - 0.3, 0.01), 0.0, 1.0), 1.5))
		pace_state = "fast"
	elif r > hi:
		pf = maxf(0.45, 1.0 - (r - hi) * 0.35)
		pace_state = "slow"
	else:
		pace_state = "good"
	var tf := 1.0
	if tension < float(p["band_lo"]):
		tf = lerpf(0.55, 1.0, clampf(tension / maxf(float(p["band_lo"]), 0.01), 0.0, 1.0))
	elif tension > float(p["band_hi"]):
		tf = 0.75
	if repeat:
		repeats += 1
		streak = 0
		integrity = maxf(0.0, integrity - float(p["repeat_loss"]))
		ev.append({"type": "pull_bad", "side": side})
	else:
		if pace_state == "good":
			streak += 1
			best_streak = maxi(best_streak, streak)
			ev.append({"type": "pull_ok", "side": side, "streak": streak})
			if streak > 0 and streak % 8 == 0:
				progress += 0.02
				ev.append({"type": "streak", "streak": streak})
		else:
			streak = streak >> 1
			ev.append({"type": "pull_bad", "side": side})
	var mult := 1.0 + float(p["streak_step"]) * float(mini(streak, int(p["streak_cap"])))
	var gain := float(p["press_gain"]) * pf * tf * mult * (float(p["repeat_factor"]) if repeat else 1.0)
	progress = clampf(progress + gain, 0.0, 1.0)
	# the tension: each pull adds, more when the pulls come too fast
	var mash := clampf(ideal / maxf(gap, 0.05) - 1.0, 0.0, 2.0) if _last_pull_t > -1.0 else 0.0
	tension = clampf(tension + float(p["tension_press"]) * (1.0 + mash), 0.0, 1.1)
	pulls += 1
	_last_pull_t = now
	since_press = 0.0
	last_side = side
	lever = -1.0 if side == "left" else 1.0
	winch_angle += 0.55
	depth = clampf(1.0 - progress * 0.5, 0.5, 1.0)         # the net comes up a little with every pull (the rest happens in RAISE)
	return ev


## Leave from the summary: the catch goes into the hold NOW (see commit) and the fish fly to the barrels.
func unload() -> Array:
	if stage != Stage.SUMMARY:
		return []
	return _set_stage(Stage.UNLOAD)


## Esc (fish_cancel): during the cast and the haul the net comes back empty; in the summary the catch is kept and unloaded.
func cancel() -> Array:
	match stage:
		Stage.HEAVE, Stage.AIM:
			return _set_stage(Stage.DONE)
		Stage.SINK, Stage.SOAK, Stage.HAUL:
			return _set_stage(Stage.CANCEL)
		Stage.RAISE:
			return []                # the net is already coming up: let it
		Stage.SUMMARY:
			return unload()
		Stage.FAIL:
			return _set_stage(Stage.DONE)
	return []


## Put the catch into the REAL hold (PortState.add_catch), once. Returns {stored: {species: kg}, released: kg, count_stored: n}.
## Safe to call at any time and any number of times.
func commit(port: RefCounted, now: float) -> Dictionary:
	if committed or result.is_empty() or bool(result.get("failed", false)):
		return stored
	committed = true
	var got: Dictionary = {}
	var released := 0.0
	var count_stored := 0
	for f in result["fish"]:
		var d: Dictionary = f
		var kg := float(d["kg"])
		var put := float(port.call("add_catch", str(d["species"]), kg, now))
		if put > 0.0:
			got[str(d["species"])] = float(got.get(str(d["species"]), 0.0)) + put
			count_stored += Catch.count_for(put, float((species.get(str(d["species"]), {}) as Dictionary).get("avg_kg", 0.5)))
		released += kg - put
	stored = {"stored": got, "released": floorf(released * 100.0 + 0.5) / 100.0, "count_stored": count_stored}
	return stored


## Everything a view needs to explain the failure or the catch in plain words.
func advice() -> String:
	if stage == Stage.FAIL:
		return fail_text
	return ""


## The current alternate lever the host should highlight ("left" first, then the other).
func next_lever() -> String:
	return "right" if last_side == "left" else "left"


## The pace the player is at, 0 (too slow) .. 1 (ideal) .. 2 (too fast), for the rhythm gauge; -1 when no pull yet.
func pace_ratio() -> float:
	if _last_pull_t < -1.0:
		return -1.0
	return clampf(float(p["ideal_interval_s"]) / maxf(haul_t - _last_pull_t, 0.05), 0.0, 2.0)
