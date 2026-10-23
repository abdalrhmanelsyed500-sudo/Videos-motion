extends Node
## Fishmonger identity singleton (FM-1). ONE place for the approved canonical identity (decision record 2026-10-23,
## docs/FISHMONGER_PHASE0_AUDIT.md, data/fm/fm_identity.json): title, currency, home port, starting boat, crew policy.
## Values are read from the fm_identity table when the Data registry has loaded it; the FALLBACK constants are the same
## approved values so the identity survives even if data loading fails. Display code calls Identity.money()/Identity.sym
## and Identity.home_port — identity strings are never hard-coded in UI scripts again.
## Internal stable keys (save fields, tuning keys like port.start_reales, market dict keys) are NOT identity display
## values and deliberately keep their old names (see FM-1 report, save-compatibility note).

const FALLBACK := {
	"title": "Fishmonger",
	"symbol": "$",
	"code": "USD",
	"currency_name": "dollar",
	"home_port": "Port Marlin",
	"home_region": "reg_kettle_seas",
	"start_boat": "Gullwing",
	"boat_len_m": 7.0,
	"crew_policy": "solo start; hired deckhands unlock later as optional progression",
}

var title: String = FALLBACK["title"]
var sym: String = FALLBACK["symbol"]
var currency_code: String = FALLBACK["code"]
var currency_name: String = FALLBACK["currency_name"]
var home_port: String = FALLBACK["home_port"]
var home_region: String = FALLBACK["home_region"]
var start_boat: String = FALLBACK["start_boat"]
var boat_len_m: float = FALLBACK["boat_len_m"]
var crew_policy: String = FALLBACK["crew_policy"]


func _ready() -> void:
	var d: Node = get_node_or_null("/root/Data")
	if d == null:
		return
	var tables: Dictionary = d.get("tables") if d.get("tables") != null else {}
	var rec: Dictionary = tables.get("fm_identity", {}).get("fm_core", {})
	if rec.is_empty():
		return
	title = str(rec.get("title", title))
	var cur: Dictionary = rec.get("currency", {})
	sym = str(cur.get("symbol", sym))
	currency_code = str(cur.get("code", currency_code))
	currency_name = str(cur.get("name", currency_name))
	home_port = str(rec.get("home_port", home_port))
	home_region = str(rec.get("home_region", home_region))
	start_boat = str(rec.get("start_boat", start_boat))
	boat_len_m = float(rec.get("boat_len_m", boat_len_m))
	crew_policy = str(rec.get("crew_policy", crew_policy))


## Whole-money display: 600 -> "$600". The unit is the approved currency; no other symbol exists in the game.
func money(n: float) -> String:
	return "%s%d" % [sym, int(roundf(n))]


## Two-decimal display for per-kg prices and receipts: 3.5 -> "$3.50".
func money_f(n: float) -> String:
	return "%s%.2f" % [sym, n]


## The header unit of price boards: "$ per kg".
func per_kg() -> String:
	return "%s per kg" % sym
