extends Node
## Tk - player economy / progression / save autoload. Versioned save from day one (TDD §2).

signal balance_changed(new_value: float)

const SAVE_VERSION := 1
const SAVE_PATH := "user://tkm_save.json"

var balance: float = 0.0
var reputation: int = 50
var stats: Dictionary = {"fares": 0, "on_time": 0, "failed": 0, "earned": 0.0, "collisions": 0}


func _ready() -> void:
	var start: float = float(Reg.tuning().get("start_balance", 50))
	balance = start
	reputation = int(Reg.tuning().get("start_reputation", 50))
	load_game()


func add_money(amount: float) -> void:
	balance = maxf(0.0, balance + amount)
	stats["earned"] = float(stats.get("earned", 0.0)) + maxf(0.0, amount)
	balance_changed.emit(balance)


func add_rep(delta: int) -> void:
	reputation = clampi(reputation + delta, 0, 100)


func bump_stat(key: String, delta: int = 1) -> void:
	stats[key] = int(stats.get(key, 0)) + delta


func save_game() -> bool:
	var payload := {"version": SAVE_VERSION, "balance": balance,
		"reputation": reputation, "stats": stats}
	var f := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(payload))
	return true


## Loads with explicit upgraders; unknown/newer version = refuse (never corrupt).
func load_game() -> bool:
	if not FileAccess.file_exists(SAVE_PATH):
		return false
	var f := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if f == null:
		return false
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		return false
	var d: Dictionary = parsed
	var ver: int = int(d.get("version", 0))
	if ver > SAVE_VERSION:
		push_warning("Tk: save from newer version ignored")
		return false
	while ver < SAVE_VERSION:  # upgrader chain (empty today, mandatory pattern for later)
		ver += 1
	balance = float(d.get("balance", balance))
	reputation = int(d.get("reputation", reputation))
	var st: Variant = d.get("stats", {})
	if typeof(st) == TYPE_DICTIONARY:
		stats = st
	return true


func wipe_save() -> void:
	if FileAccess.file_exists(SAVE_PATH):
		DirAccess.remove_absolute(SAVE_PATH)
