extends RefCounted
## Authoritative campaign data container. Plain dictionaries/arrays with stable
## string ids so serialization is trivial and save/load is version-tolerant.
## SCHEMA v1 — see docs/ARCHITECTURE.md.

const SCHEMA_VERSION := 1
const UNIT_CLASSES := {
	"infantry": {"wage": 1.1, "supply": 0.5, "power": 1.0, "speed": 1.0},
	"mechanized": {"wage": 1.6, "supply": 1.4, "power": 1.8, "speed": 1.6},
	"armor": {"wage": 2.4, "supply": 2.2, "power": 3.2, "speed": 1.3},
	"artillery": {"wage": 2.0, "supply": 1.8, "power": 2.4, "speed": 0.8},
	"recon": {"wage": 1.4, "supply": 1.0, "power": 0.8, "speed": 2.0},
	"logistics": {"wage": 1.2, "supply": 0.8, "power": 0.2, "speed": 1.4},
}

var schema_version: int = SCHEMA_VERSION
var seed: int = 0
var rng_state: int = 0
var day: int = 0                      # absolute campaign day
var speed_index: int = 1
var paused: bool = false
var treasury: float = 0.0
var stability: float = 0.5            # national/org political stability 0..1
var inflation: float = 0.01
var regions: Dictionary = {}          # id -> region record
var countries: Dictionary = {}        # id -> country record
var formations: Dictionary = {}       # id -> formation record
var inventory: Dictionary = {}        # equip_id -> count (player org stores)
var market_orders: Dictionary = {}    # order_id -> order record
var relations: Dictionary = {}        # "a|b" -> {trust, warmth, threat}
var wars: Dictionary = {}             # war_id -> war record
var reports: Array = []               # newest last: {day, kind, title, body}
var history: Array = []               # {day, text} campaign timeline
var policies: Dictionary = {"tax": 0.5, "security_spend": 0.5}
var counters: Dictionary = {"frm": 0, "ord": 0, "war": 0, "rep": 0}
var outcome: String = ""              # "" = ongoing

var rng := RandomNumberGenerator.new()


func next_id(prefix: String) -> String:
	counters[prefix] = int(counters.get(prefix, 0)) + 1
	return "%s_%04d" % [prefix, counters[prefix]]


func reseed() -> void:
	rng.seed = rng_state if rng_state != 0 else seed
	

func randf() -> float:
	var v := rng.randf()
	rng_state = rng.seed  # persist stream position
	return v


func region(id: String) -> Dictionary:
	return regions.get(id, {})


func country(id: String) -> Dictionary:
	return countries.get(id, {})


func formations_of(country_id: String) -> Array:
	var out: Array = []
	for fid in formations:
		if formations[fid]["country"] == country_id:
			out.append(formations[fid])
	return out


func formations_in(region_id: String) -> Array:
	var out: Array = []
	for fid in formations:
		if formations[fid]["region"] == region_id:
			out.append(formations[fid])
	return out


func player_id() -> String:
	for cid in countries:
		if countries[cid]["is_player"]:
			return cid
	return ""


func pair_key(a: String, b: String) -> String:
	return a + "|" + b if a < b else b + "|" + a


func rel(a: String, b: String) -> Dictionary:
	var k := pair_key(a, b)
	if not relations.has(k):
		relations[k] = {"trust": 0.3, "warmth": 0.3, "threat": 0.2}
	return relations[k]


func add_report(kind: String, title: String, body: String) -> Dictionary:
	var rep := {"day": day, "kind": kind, "title": title, "body": body}
	reports.append(rep)
	if reports.size() > 120:
		reports.pop_front()
	return rep


func add_history(text: String) -> void:
	history.append({"day": day, "text": text})
	if history.size() > 400:
		history.pop_front()


func formation_personnel(f: Dictionary) -> int:
	var n := 0
	for u in f["units"]:
		n += int(u["count"]) * 12
	return n


func formation_power(f: Dictionary, equip_table: Dictionary) -> float:
	var p := 0.0
	for u in f["units"]:
		var cls: Dictionary = UNIT_CLASSES.get(u["class"], UNIT_CLASSES["infantry"])
		var eq: Dictionary = equip_table.get(u["equip"], {})
		var q: float = float(eq.get("combat", 30)) / 50.0
		p += float(u["count"]) * float(cls["power"]) * q
	p *= 0.5 + 0.5 * float(f["morale"])
	p *= 0.6 + 0.4 * float(f["readiness"])
	p *= 0.7 + 0.3 * float(f["supplies"])
	return p


func serialize() -> Dictionary:
	return {
		"schema_version": schema_version, "seed": seed, "rng_state": rng_state,
		"day": day, "speed_index": speed_index, "paused": paused,
		"treasury": treasury, "stability": stability, "inflation": inflation,
		"regions": regions, "countries": countries, "formations": formations,
		"inventory": inventory, "market_orders": market_orders,
		"relations": relations, "wars": wars, "reports": reports,
		"history": history, "policies": policies, "counters": counters,
		"outcome": outcome,
	}


static func validate(data: Dictionary) -> Array:
	var errs: Array = []
	if typeof(data) != TYPE_DICTIONARY:
		return ["save root is not a dictionary"]
	for key in ["schema_version", "seed", "day", "treasury", "regions", "countries",
			"formations", "inventory", "market_orders", "relations", "counters"]:
		if not data.has(key):
			errs.append("missing key: " + key)
	if errs.is_empty() and int(data["schema_version"]) != SCHEMA_VERSION:
		errs.append("unsupported schema %s" % data["schema_version"])
	if errs.is_empty():
		for rid in data["regions"]:
			var r: Dictionary = data["regions"][rid]
			for nb in r.get("neighbors", []):
				if not data["regions"].has(nb):
					errs.append("region %s references unknown neighbor %s" % [rid, nb])
			for nb in r.get("neighbors", []):
				if not rid in data["regions"][nb].get("neighbors", []):
					errs.append("asymmetric neighbor %s->%s" % [rid, nb])
		for fid in data["formations"]:
			var f: Dictionary = data["formations"][fid]
			if not data["regions"].has(f["region"]):
				errs.append("formation %s in unknown region" % fid)
			if not data["countries"].has(f["country"]):
				errs.append("formation %s of unknown country" % fid)
	return errs


func deserialize(data: Dictionary) -> String:
	var errs := validate(data)
	if not errs.is_empty():
		return "; ".join(errs)
	schema_version = data["schema_version"]; seed = data["seed"]
	rng_state = data["rng_state"]; day = data["day"]
	speed_index = data["speed_index"]; paused = data["paused"]
	treasury = data["treasury"]; stability = data["stability"]
	inflation = data["inflation"]; regions = data["regions"]
	countries = data["countries"]; formations = data["formations"]
	inventory = data["inventory"]; market_orders = data["market_orders"]
	relations = data["relations"]; wars = data["wars"]; reports = data["reports"]
	history = data["history"]; policies = data["policies"]
	counters = data["counters"]; outcome = data["outcome"]
	reseed()
	return ""
