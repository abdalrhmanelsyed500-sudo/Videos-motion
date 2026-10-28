extends Node
## CampaignClock: pausable simulation clock. Speeds = days per real second.
## Emits day/week/month signals; systems subscribe (GameState wires them).

const SPEEDS := [0.0, 1.0, 2.0, 4.0, 8.0]
const SPEED_NAMES := ["Paused", "x1", "x2", "x4", "x8"]

var speed_index: int = 1
var _acc: float = 0.0


func set_speed(idx: int) -> void:
	speed_index = clampi(idx, 0, SPEEDS.size() - 1)


func is_paused() -> bool:
	return speed_index == 0


func advance_days(n: int, state) -> void:
	## Deterministic manual advance (used by tests/debug & very-fast sim).
	for i in n:
		_step_day(state)


func _process(delta: float) -> void:
	var gs := get_node_or_null("/root/GameState")
	if gs == null or gs.cs == null or is_paused():
		return
	_acc += delta * SPEEDS[speed_index]
	while _acc >= 1.0:
		_acc -= 1.0
		_step_day(gs.cs)


func _step_day(state) -> void:
	state.day += 1
	EventBus.day_passed.emit(state.day)
	if state.day % 7 == 0:
		EventBus.week_passed.emit(state.day / 7)
	if state.day % 30 == 0:
		EventBus.month_passed.emit(state.day / 30)
