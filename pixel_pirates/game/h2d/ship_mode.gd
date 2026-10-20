# gdlint: disable=max-returns,class-definitions-order
extends RefCounted
## CP-2 Release A: the ship controller. Two modes, one ship:
##   NAV  = at the helm. A / D steer (or the course hold does), nothing else changes. The classic sailing view.
##   DECK = on foot aboard the moving ship (ship_walker.gd), with the camera on the pirate. The ship keeps sailing on its COURSE
##          HOLD (ship_autopilot.gd), so walking away from the wheel never stops or turns the ship.
## This file owns the rules that join them (leave and take the helm, the C key, what E does at each place) and nothing about
## drawing, key reading or the port: the host (h2d0.gd) passes a plain context dictionary every frame and executes the events.
## Context keys: heading, wind_from, wind_kn, no_go (floats), sailing (bool: free sailing, not docking / moored), docked (bool).
## Events returned by interact(): {"kind": ..., "id": ...}; kinds: none, toast, map, fish_barrels, stores, chest, winch, berths, move, helm.
## NOT YET RUN ON THE USER'S PC.
const Layout := preload("res://h2d/ship_layout.gd")
const Walker := preload("res://h2d/ship_walker.gd")
const Autopilot := preload("res://h2d/ship_autopilot.gd")
enum { NAV, DECK }
const COMPASS: Array[String] = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

var mode := NAV
var layout: RefCounted = Layout.new()
var walker: RefCounted = Walker.new()
var ap: RefCounted = Autopilot.new()
var _tuning: Dictionary = {}


func configure(tuning: Dictionary) -> void:
	_tuning = tuning
	walker.call("configure", tuning, layout)
	ap.call("configure", tuning)
	reset()


func param(key: String, fallback: float) -> float:
	return float(_tuning.get(key, fallback))


## Back to the wheel, hold off, walker at the helm (a reset, boarding from the pier, a scene change).
func reset() -> void:
	mode = NAV
	ap.call("release")
	walker.call("place_at_helm")


func is_deck() -> bool:
	return mode == DECK


func level() -> int:
	return int(walker.get("level"))


static func compass(deg: float) -> String:
	return COMPASS[int(floorf(fposmod(deg, 360.0) / 45.0 + 0.5)) % 8]


# ---- the course hold ------------------------------------------------------------------------------------------------
## The steer axis for the helm this frame. `manual` = A / D (ignored on deck: nobody is at the wheel).
func steer(dt: float, manual: float, c: Dictionary) -> float:
	var m := manual if mode == NAV else 0.0
	return float(ap.call("steer", dt, m, float(c["heading"]), float(c.get("yaw_rate", 0.0)), float(c["wind_from"]),
			float(c["wind_kn"]), float(c["no_go"])))


## C. At the wheel it switches the hold on and off; on deck the hold stays on (the ship must keep sailing). Returns the message.
func toggle_autopilot(c: Dictionary) -> String:
	if mode == DECK:
		return "The course hold stays on while you are away from the wheel. Take the helm (E at the wheel) to steer."
	if not bool(c["sailing"]):
		return "The course hold works at sea. SPACE casts off."
	if bool(ap.get("engaged")):
		ap.call("release")
		return "Course hold OFF: you are steering (A / D)."
	var held := float(ap.call("engage", float(c["heading"]), float(c["wind_from"]), float(c["wind_kn"]), float(c["no_go"])))
	return "COURSE HOLD ON: holding %03d (%s). The ship keeps this heading by itself. A / D corrects it." % [
			int(roundf(held)) % 360, compass(held)]


## Called every frame: on deck, free sailing always means the hold is on.
func ensure_hold(c: Dictionary) -> String:
	if mode == DECK and bool(c["sailing"]) and not bool(ap.get("engaged")):
		var held := float(ap.call("engage", float(c["heading"]), float(c["wind_from"]), float(c["wind_kn"]), float(c["no_go"])))
		return "Course hold ON: holding %03d (%s)." % [int(roundf(held)) % 360, compass(held)]
	return ""


# ---- helm <-> deck ---------------------------------------------------------------------------------------------------
func leave_helm(c: Dictionary) -> String:
	if mode == DECK:
		return ""
	mode = DECK
	walker.call("place_at_helm")
	if bool(c["sailing"]) and not bool(ap.get("engaged")):
		var held := float(ap.call("engage", float(c["heading"]), float(c["wind_from"]), float(c["wind_kn"]), float(c["no_go"])))
		return "You leave the helm. Course hold ON: %03d (%s). The ship sails on by herself." % [int(roundf(held)) % 360, compass(held)]
	if bool(c["sailing"]):
		return "You leave the helm. The ship keeps her course hold."
	return "You leave the helm."


func take_helm() -> String:
	if mode == NAV:
		return ""
	walker.call("settle")
	mode = NAV
	walker.call("place_at_helm")
	if bool(ap.get("engaged")):
		return "You have the helm. Course hold is ON (C releases it; A / D corrects the course)."
	return "You have the helm. A / D steer."


# ---- per frame --------------------------------------------------------------------------------------------------------
## dir: the walking keys as a screen direction (x east, y south). climb_in: +1 W / -1 S. Does nothing in NAV.
func step(dt: float, dir: Vector2, run: bool, heading_deg: float, climb_in: float) -> void:
	if mode != DECK:
		return
	walker.call("step", dt, dir, run, heading_deg, climb_in)


## The hero's state for the view: {level, u, v, feet: Vector2 local, height, row, frame, busy, climbing}.
func hero() -> Dictionary:
	var feet := walker.call("feet_local") as Vector2
	return {"level": int(walker.get("level")), "u": feet.x, "v": feet.y, "height": float(walker.call("height_above_floor")),
			"row": int(walker.get("row")), "frame": int(walker.get("frame")), "busy": bool(walker.call("is_busy")),
			"climbing": int(walker.get("mode")) == Walker.Mode.CLIMB, "fade": float(walker.call("fade_amount"))}


func hero_at() -> Vector2:
	return walker.call("feet_local") as Vector2


# ---- what the HUD says --------------------------------------------------------------------------------------------
func status(c: Dictionary) -> Dictionary:
	var engaged := bool(ap.get("engaged"))
	var sailing := bool(c["sailing"])
	if not sailing:
		if mode == DECK:
			return {"kind": "moored", "title": "MOORED", "sub": "Walk the ship. SPACE casts off. F goes ashore from the main deck."}
		return {"kind": "none", "title": "", "sub": ""}
	if engaged:
		var tgt := float(ap.get("target_deg"))
		var eff := float(ap.call("effective_target", float(c["wind_from"]), float(c["wind_kn"]), float(c["no_go"])))
		var title := "COURSE HOLD  %03d %s" % [int(roundf(eff)) % 360, compass(eff)]
		if mode == DECK:
			return {"kind": "hold", "title": title, "sub": "The ship sails herself. E at the wheel takes the helm."}
		if bool(ap.get("manual_override")):
			return {"kind": "hand", "title": "STEERING BY HAND", "sub": "The hold takes your new heading when you let go."}
		if absf(Autopilot.wrap180(eff - tgt)) > 0.5 or bool(ap.get("adjusted")):
			return {"kind": "hold", "title": title + "  (turned away from the wind)", "sub": "C  release   A / D  correct   E  leave the helm"}
		return {"kind": "hold", "title": title, "sub": "C  release   A / D  correct   E  leave the helm"}
	return {"kind": "direct", "title": "STEERING: DIRECT", "sub": "A / D steer   C  hold course   E  leave the helm"}


## The prompt for the place the pirate stands at ("" if none) and its id.
func prompt() -> Dictionary:
	if mode != DECK:
		return {"id": "", "text": ""}
	var wm := int(walker.get("mode"))
	if wm == Walker.Mode.CLIMB:
		return {"id": "climb", "text": "W  climb up      S  climb down"}
	if wm == Walker.Mode.TRANSIT:
		return {"id": "", "text": ""}
	var it := layout.call("nearest_interaction", int(walker.get("level")), float(walker.get("u")), float(walker.get("v"))) as Dictionary
	if it.is_empty():
		return {"id": "", "text": ""}
	return {"id": str(it["id"]), "text": str(it["prompt"])}


## F: is the pirate at the fishing winch right now (main deck, not climbing, not in a transition)?
func winch_ready() -> bool:
	if mode != DECK or bool(walker.call("is_busy")):
		return false
	var it := layout.call("nearest_interaction", int(walker.get("level")), float(walker.get("u")), float(walker.get("v"))) as Dictionary
	return not it.is_empty() and str(it["id"]) == "winch"


## E. Does the thing at the pirate's feet. The host handles the returned event (the map, the panels, the toasts).
func interact(_c: Dictionary) -> Dictionary:
	if mode != DECK:
		return {"kind": "helm_leave", "id": "helm"}
	if bool(walker.call("is_busy")):
		return {"kind": "none", "id": ""}
	var lv := int(walker.get("level"))
	var it := layout.call("nearest_interaction", lv, float(walker.get("u")), float(walker.get("v"))) as Dictionary
	if it.is_empty():
		return {"kind": "none", "id": ""}
	var id := str(it["id"])
	match id:
		"helm":
			return {"kind": "helm", "id": id, "text": take_helm()}
		"hatch_down":
			if lv == Layout.L_DECK:
				walker.call("start_transit", Layout.L_SLEEP, Layout.HATCH, Layout.ARRIVE_BELOW)
			else:
				walker.call("start_transit", Layout.L_HOLD, Layout.HOLD_HATCH, Layout.ARRIVE_HOLD)
			return {"kind": "move", "id": id}
		"ladder_up":
			if lv == Layout.L_SLEEP:
				walker.call("start_transit", Layout.L_DECK, Layout.HATCH, Layout.ARRIVE_ABOVE)
			else:
				walker.call("start_transit", Layout.L_SLEEP, Layout.HOLD_HATCH, Layout.ARRIVE_BACK_UP)
			return {"kind": "move", "id": id}
		"rope_ladder":
			walker.call("start_climb", 1)
			return {"kind": "move", "id": id}
		"ladder_down":
			walker.call("start_climb", -1)
			return {"kind": "move", "id": id}
		"desk":
			return {"kind": "map", "id": id}
		"chest", "winch", "fish_barrels", "berths":
			return {"kind": id, "id": id}
		"ledger", "racks":
			return {"kind": "stores", "id": id}
	return {"kind": "none", "id": id}


## True when the pirate may go ashore from here (main deck only, and not in the middle of a transition).
func can_go_ashore() -> bool:
	return mode == NAV or (int(walker.get("level")) == Layout.L_DECK and not bool(walker.call("is_busy")))
