extends Node
## MissionMgr - delivery mission finite state machine + reward calculation (data-driven).
## States: IDLE -> OFFER -> BOARDING -> DRIVING -> RESULT -> IDLE. One reward payout per mission
## (guarded).

signal state_changed(new_state: int)
signal offer_shown(info: Dictionary)
signal driving_started(info: Dictionary)
signal mission_result(result: Dictionary)
signal toast(text: String)

enum State { IDLE, OFFER, BOARDING, DRIVING, RESULT }

var state: int = State.IDLE
var passenger: Dictionary = {}          # cast entry of current passenger
var dest_name: String = ""
var distance_m: float = 0.0
var time_limit_s: float = 0.0
var time_left_s: float = 0.0
var collisions: int = 0
var used_shortcut: bool = false
var drift_earned: float = 0.0
var _paid_this_mission := false
var _offer_age_s: float = 0.0


func _process(delta: float) -> void:
	if state == State.DRIVING:
		time_left_s -= delta
		if time_left_s <= 0.0:
			time_left_s = 0.0
			_finish(false, "Time is up - the passenger walked off.")
	elif state == State.OFFER:
		_offer_age_s += delta
		if _offer_age_s > float(Reg.tuning().get("offer_timeout_s", 12.0)):
			close_offer(false)


## District calls this when the tuktuk idles inside the pickup ring.
func make_offer(pax: Dictionary, dest_label: String, dist_m: float) -> void:
	if state != State.IDLE:
		return
	passenger = pax
	dest_name = dest_label
	distance_m = dist_m
	var t: Dictionary = Reg.tuning()
	time_limit_s = float(t.get("time_base_s", 30.0)) + float(t.get("time_per_m", 0.35)) * dist_m
	state = State.OFFER
	_offer_age_s = 0.0
	state_changed.emit(state)
	offer_shown.emit({
		"name": str(pax.get("name_en", "Passenger")),
		"line": str(pax.get("line_en", "")),
		"dest": dest_label, "dist_m": dist_m, "time_s": time_limit_s})


func accept_offer() -> bool:
	if state != State.OFFER:
		return false
	state = State.BOARDING
	state_changed.emit(state)
	return true


func close_offer(accepted: bool) -> void:
	if state != State.OFFER:
		return
	if not accepted:
		toast.emit("Maybe next time.")
	state = State.IDLE
	passenger = {}
	state_changed.emit(state)


## Passenger script calls this when the board tween finishes.
func begin_driving() -> void:
	if state != State.BOARDING:
		return
	state = State.DRIVING
	time_left_s = time_limit_s
	collisions = 0
	used_shortcut = false
	drift_earned = 0.0
	_paid_this_mission = false
	state_changed.emit(state)
	driving_started.emit({"dest": dest_name, "dist_m": distance_m, "time_s": time_limit_s})


func report_collision() -> void:
	if state == State.DRIVING:
		collisions += 1
		Tk.bump_stat("collisions", 1)


## Controlled-drift bonus: rate * seconds, capped per mission (tuning-driven), toast once per drift.
func report_drift(seconds: float) -> void:
	if state != State.DRIVING:
		return
	var t: Dictionary = Reg.tuning()
	var cap: float = float(t.get("drift_bonus_cap", 4.0))
	if drift_earned >= cap:
		return
	var add := minf(float(t.get("drift_bonus_per_s", 1.5)) * seconds, cap - drift_earned)
	drift_earned += add
	toast.emit("Controlled drift! +E£%d" % int(add))


func report_shortcut() -> void:
	if state == State.DRIVING and not used_shortcut:
		used_shortcut = true
		toast.emit("Shortcut! The old alley pays off.")


## District calls when the tuktuk stops inside the destination ring.
func complete_delivery() -> void:
	if state == State.DRIVING:
		_finish(true, "Delivered!")


func _finish(success: bool, msg: String) -> void:
	state = State.RESULT
	var t: Dictionary = Reg.tuning()
	var reward := 0.0
	var breakdown := {}
	if success:
		reward = compute_reward(distance_m, time_left_s, collisions, used_shortcut, t)
		breakdown = compute_breakdown(distance_m, time_left_s, collisions, used_shortcut, t)
		breakdown["drift"] = drift_earned
		reward = minf(reward + drift_earned, float(t.get("reward_cap", 120.0)))
		if not _paid_this_mission:
			_paid_this_mission = true
			Tk.add_money(reward)
			Tk.add_rep(int(t.get("rep_win", 1)))
			Tk.bump_stat("fares", 1)
			if time_left_s > 0.0:
				Tk.bump_stat("on_time", 1)
	else:
		Tk.add_rep(int(t.get("rep_fail", -2)))
		Tk.bump_stat("failed", 1)
	Tk.save_game()
	var result := {"success": success, "msg": msg, "reward": reward, "breakdown": breakdown,
		"time_left": time_left_s, "collisions": collisions, "shortcut": used_shortcut,
		"balance": Tk.balance}
	state_changed.emit(state)
	mission_result.emit(result)


## Called by district/HUD after the result card is dismissed.
func reset_to_idle() -> void:
	state = State.IDLE
	passenger = {}
	_paid_this_mission = false
	state_changed.emit(state)


## Pure reward maths (unit-tested in tests/test_reward.gd).
static func compute_breakdown(dist_m: float, sec_left: float, hits: int,
		shortcut: bool, t: Dictionary) -> Dictionary:
	var base: float = float(t.get("base_fare", 5.0))
	var dist_pay: float = float(t.get("per_m", 0.05)) * dist_m
	var time_pay: float = float(t.get("time_left_rate", 0.3)) * maxf(0.0, sec_left)
	var clean: float = float(t.get("clean_drive_bonus", 0.0)) if hits == 0 else 0.0
	var short_b: float = float(t.get("shortcut_bonus", 0.0)) if shortcut else 0.0
	var pen: float = float(t.get("collision_penalty", 0.0)) * hits
	var total := base + dist_pay + time_pay + clean + short_b - pen
	total = clampf(total, 0.0, float(t.get("reward_cap", 999.0)))
	return {"base": base, "distance": dist_pay, "time_left": time_pay, "clean": clean,
		"shortcut": short_b, "penalty": pen, "total": total}


static func compute_reward(dist_m: float, sec_left: float, hits: int,
		shortcut: bool, t: Dictionary) -> float:
	return float(compute_breakdown(dist_m, sec_left, hits, shortcut, t).get("total", 0.0))
