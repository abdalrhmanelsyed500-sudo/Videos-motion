extends RefCounted
## Authoritative, serializable campaign state. IDs are stable across saves.
## A unit count represents equipped 12-person squads; reserves are individuals.

const SCHEMA_VERSION := 2
const PERSONNEL_PER_UNIT := 12
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
var day: int = 0
var speed_index: int = 1
var paused: bool = false
var treasury: float = 0.0             # player balance; AI balances in countries
var stability: float = 0.5
var inflation: float = 0.01
var regions: Dictionary = {}
var countries: Dictionary = {}
var formations: Dictionary = {}
var inventory: Dictionary = {}       # player equipment packages
var market_orders: Dictionary = {}
var relations: Dictionary = {}
var wars: Dictionary = {}
var treaties: Dictionary = {}
var finalized_battles: Dictionary = {}
var contact_notices: Dictionary = {}
var reports: Array = []
var history: Array = []
var policies: Dictionary = {"tax": 0.5, "security_spend": 0.5}
var counters: Dictionary = {"frm": 0, "ord": 0, "war": 0, "rep": 0, "bat": 0, "treaty": 0}
var outcome: String = ""
var rng := RandomNumberGenerator.new()


func next_id(prefix: String) -> String:
	counters[prefix] = int(counters.get(prefix, 0)) + 1
	return "%s_%04d" % [prefix, counters[prefix]]


func reseed() -> void:
	rng.seed = seed if seed != 0 else 7
	if rng_state != 0:
		rng.state = rng_state
	rng_state = rng.state


func randf() -> float:
	var value := rng.randf()
	rng_state = rng.state  # PCG stream position, not rng.seed
	return value


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
		if countries[cid].get("is_player", false):
			return cid
	return ""


func balance(cid: String) -> float:
	if cid == player_id():
		return treasury
	return float(countries.get(cid, {}).get("treasury", 0.0))


func adjust_balance(cid: String, delta: float) -> void:
	if cid == player_id():
		treasury += delta
	elif countries.has(cid):
		countries[cid]["treasury"] = balance(cid) + delta


func inventory_for(cid: String) -> Dictionary:
	if cid == player_id():
		return inventory
	if not countries.has(cid):
		return {}
	if not countries[cid].has("inventory"):
		countries[cid]["inventory"] = {}
	return countries[cid]["inventory"]


func can_observe(cid: String, rid: String) -> bool:
	if not regions.has(rid) or not countries.has(cid):
		return false
	var r: Dictionary = regions[rid]
	if r["controller"] == cid:
		return true
	for nb in r["neighbors"]:
		if regions.has(nb) and regions[nb]["controller"] == cid:
			return true
	for f in formations.values():
		if f["country"] == cid and f["region"] == rid:
			return true
	return false


func pair_key(a: String, b: String) -> String:
	return a + "|" + b if a < b else b + "|" + a


func rel(a: String, b: String) -> Dictionary:
	var k := pair_key(a, b)
	if not relations.has(k):
		relations[k] = {"trust": 0.3, "warmth": 0.3, "threat": 0.2}
	return relations[k]


func is_hostile(a: String, b: String) -> bool:
	if a == b:
		return false
	for w in wars.values():
		if (a in w["sides_a"] and b in w["sides_b"]) or (b in w["sides_a"] and a in w["sides_b"]):
			if w["status"] == "active":
				return true
			if w["status"] == "ceasefire":
				return false
	return float(rel(a, b).get("threat", 0.0)) > 0.55


func add_report(kind: String, title: String, body: String, audience: String = "public") -> Dictionary:
	var rep := {"day": day, "kind": kind, "title": title, "body": body, "audience": audience}
	reports.append(rep)
	if reports.size() > 200:
		reports.pop_front()
	return rep


func add_history(text: String) -> void:
	history.append({"day": day, "text": text})
	if history.size() > 400:
		history.pop_front()


func formation_personnel(f: Dictionary) -> int:
	var n := int(f.get("personnel_reserve", 0))
	for u in f.get("units", []):
		n += int(u["count"]) * PERSONNEL_PER_UNIT
	return n


func formation_power(f: Dictionary, equip_table: Dictionary) -> float:
	var p := 0.0
	for u in f.get("units", []):
		var cls: Dictionary = UNIT_CLASSES.get(u["class"], UNIT_CLASSES["infantry"])
		var eq: Dictionary = equip_table.get(u["equip"], {})
		var q: float = float(eq.get("combat", 30)) / 50.0
		p += float(u["count"]) * float(cls["power"]) * q * clampf(float(u.get("condition", 1.0)), 0.0, 1.0)
	p *= 0.5 + 0.5 * float(f["morale"])
	p *= 0.4 + 0.6 * float(f["readiness"])
	p *= 0.4 + 0.6 * float(f["supplies"])
	return p


func serialize() -> Dictionary:
	# JSON numbers lose precision above 2^53. Store the 64-bit PCG state as text.
	return {
		"schema_version": schema_version, "seed": seed, "rng_state": str(rng_state),
		"day": day, "speed_index": speed_index, "paused": paused,
		"treasury": treasury, "stability": stability, "inflation": inflation,
		"regions": regions, "countries": countries, "formations": formations,
		"inventory": inventory, "market_orders": market_orders,
		"relations": relations, "wars": wars, "treaties": treaties,
		"finalized_battles": finalized_battles, "contact_notices": contact_notices, "reports": reports,
		"history": history, "policies": policies, "counters": counters,
		"outcome": outcome,
	}


static func migrate(data: Dictionary) -> Dictionary:
	var d := data.duplicate(true)
	var v := int(d.get("schema_version", 0))
	if v == 1:
		# v1 saved the seed rather than the PCG stream position; this cannot be recovered.
		d["rng_state"] = "0"
		d["treaties"] = {}
		d["finalized_battles"] = {}
		d["contact_notices"] = {}
		for cid in d.get("countries", {}):
			var c: Dictionary = d["countries"][cid]
			c["treasury"] = float(c.get("treasury", 8000.0))
			c["inventory"] = c.get("inventory", {"rif_surplus": 8})
			c["damaged_inventory"] = c.get("damaged_inventory", {})
		for rid in d.get("regions", {}):
			var r: Dictionary = d["regions"][rid]
			apply_region_defaults(r)
		for fid in d.get("formations", {}):
			apply_formation_defaults(d["formations"][fid])
		d["schema_version"] = 2
		var history: Array = d.get("history", [])
		history.append({"day": int(d.get("day", 0)), "text": "Migrated v1 save; random stream restarted."})
		d["history"] = history
	elif v != SCHEMA_VERSION:
		return {"error": "unsupported schema %d" % v, "data": {}}
	return {"error": "", "data": d}


static func apply_region_defaults(r: Dictionary) -> void:
	r["sea_neighbors"] = r.get("sea_neighbors", [])
	r["political_support"] = float(r.get("political_support", r.get("support_player", 0.4)))
	r["productivity"] = float(r.get("productivity", 0.75))
	r["infra_condition"] = float(r.get("infra_condition", 0.75))
	r["security_pressure"] = float(r.get("security_pressure", 0.2))
	r["opposition"] = float(r.get("opposition", 0.3))
	r["supply_accessibility"] = float(r.get("supply_accessibility", 0.0))
	r["recovery_progress"] = float(r.get("recovery_progress", 0.5))
	r["admin_focus"] = r.get("admin_focus", "none")
	r["salvage"] = r.get("salvage", {})
	r["is_city"] = bool(r.get("is_city", int(r.get("infra", 0)) >= 3))
	r["strategic_value"] = float(r.get("strategic_value", 1.0 + float(r.get("infra", 1)) * 0.25))


static func apply_formation_defaults(f: Dictionary) -> void:
	f["attachments"] = f.get("attachments", {})
	f["personnel_reserve"] = int(f.get("personnel_reserve", 0))
	f["wounded"] = int(f.get("wounded", 0))
	f["dead"] = int(f.get("dead", 0))
	f["last_supply_warning"] = int(f.get("last_supply_warning", -100))


static func validate(data: Dictionary) -> Array:
	var errs: Array = []
	for key in ["schema_version", "seed", "rng_state", "day", "treasury", "regions", "countries",
			"formations", "inventory", "market_orders", "relations", "counters"]:
		if not data.has(key):
			errs.append("missing key: " + key)
	if not errs.is_empty():
		return errs
	if int(data["schema_version"]) != SCHEMA_VERSION:
		return ["unsupported schema %s" % data["schema_version"]]
	if typeof(data["regions"]) != TYPE_DICTIONARY or typeof(data["countries"]) != TYPE_DICTIONARY:
		return ["invalid regions/countries"]
	for rid in data["regions"]:
		var r: Dictionary = data["regions"][rid]
		if r.get("id", "") != rid:
			errs.append("invalid region id " + str(rid))
		if not data["countries"].has(r.get("country", "")) or not data["countries"].has(r.get("controller", "")):
			errs.append("invalid owner/controller " + str(rid))
		for kind in ["neighbors", "sea_neighbors"]:
			for nb in r.get(kind, []):
				if not data["regions"].has(nb):
					errs.append("region %s references unknown %s" % [rid, nb])
				elif not rid in data["regions"][nb].get(kind, []):
					errs.append("asymmetric %s %s->%s" % [kind, rid, nb])
	for fid in data["formations"]:
		var f: Dictionary = data["formations"][fid]
		if not data["regions"].has(f.get("region", "")):
			errs.append("formation %s in unknown region" % fid)
		if not data["countries"].has(f.get("country", "")):
			errs.append("formation %s of unknown country" % fid)
		for u in f.get("units", []):
			if int(u.get("count", -1)) < 0:
				errs.append("negative unit count: " + str(fid))
	return errs


func deserialize(data: Dictionary) -> String:
	var migrated := migrate(data)
	if migrated["error"] != "":
		return migrated["error"]
	var d: Dictionary = migrated["data"]
	var errs := validate(d)
	if not errs.is_empty():
		return "; ".join(errs)
	schema_version = SCHEMA_VERSION; seed = int(d["seed"])
	rng_state = str(d["rng_state"]).to_int(); day = int(d["day"])
	speed_index = int(d.get("speed_index", 0)); paused = bool(d.get("paused", false))
	treasury = float(d["treasury"]); stability = float(d.get("stability", 0.5))
	inflation = float(d.get("inflation", 0.01)); regions = d["regions"]
	countries = d["countries"]; formations = d["formations"]
	inventory = d["inventory"]; market_orders = d["market_orders"]
	relations = d["relations"]; wars = d.get("wars", {}); treaties = d.get("treaties", {})
	finalized_battles = d.get("finalized_battles", {}); contact_notices = d.get("contact_notices", {})
	reports = d.get("reports", [])
	history = d.get("history", []); policies = d.get("policies", policies)
	counters = d["counters"]; outcome = str(d.get("outcome", ""))
	reseed()
	return ""
