extends RefCounted
## The look of each kind of weather (H2D-0.3): the numbers that make calm, a breeze, rain, fog, a rough sea and a
## gale DIFFERENT KINDS of scene, not one scene at different strengths. Everything is a continuous function of the
## shared environment (env_model.gd), so a change of weather fades from one look to the next. Pure arithmetic.
##
## What changes with the weather (where it is applied):
##   calm    glassy water (almost no ripples, long low swell, long sun glitter, sky reflection), slack sail, still ship
##   breezy  bright cat's-paw ripples, sharp small glints, drifting cloud shadows, full steady sail, sparse white tips
##   rain    overcast: no sun glints, no cloud shadows, flat light, dull pitted water, closer horizon, rain with
##           its own character per intensity (drizzle is short and near-vertical, a downpour is long and gust-bent)
##   fog     the fog starts closer and reaches the ship, milky light, desaturated, no glints, no cloud shadows, calm sea
##   rough   dark blue-grey water, whitecaps, foam lanes, steep irregular waves, gusts that visibly cross the water
##   gale    peaked crests, streaked foam, spindrift, heavy rain bent by the gusts, taut sail, violent ship
## All numbers: data/tuning/tuning_env.json (look.*). NOT YET RUN IN GODOT.
const PREFIX := "look."
const DEFAULTS := {
	"rain_fall_ms": 19.0, "rain_streak_m": 1.5, "rain_drift_factor": 0.55, "rain_gust_bend": 0.8, "rain_density": 1.0,
	"fog_start_shift_m": 45.0,
}
const FOG_START_BASE_M := 190.0  ## about the camera distance to the ship

var _p: Dictionary = DEFAULTS.duplicate()


func configure(values: Dictionary) -> void:
	_p = DEFAULTS.duplicate()
	for k in DEFAULTS.keys():
		var full: String = PREFIX + str(k)
		if values.has(full):
			_p[k] = float(values[full])


func param(key: String) -> float:
	return float(_p[key])


## 0 = open sky, 1 = full overcast (rain, storm and fog all put a lid on the sky).
static func overcast(cloud: float, rain_inst: float, storm: float, fog: float) -> float:
	return clampf(maxf(1.4 * (cloud - 0.25), maxf(0.9 * rain_inst, maxf(storm, 0.8 * fog))), 0.0, 1.0)


## 0 = clear air, 1 = thick fog. Light haze (fog level under 0.2) does not count: it is only the distance fade.
static func fog_thickness(fog: float) -> float:
	return smoothstep(0.2, 0.7, fog)


func fog_start_m(fog: float) -> float:
	return FOG_START_BASE_M - param("fog_start_shift_m") * fog_thickness(fog)


## Character of the falling rain from its intensity (0..1): light rain is short, slow and thin, a downpour is long.
func rain_character(rain_inst: float) -> Dictionary:
	var k := clampf(rain_inst, 0.0, 1.0)
	return {
		"fall_ms": param("rain_fall_ms") * lerpf(0.85, 1.15, k),
		"streak_m": param("rain_streak_m") * lerpf(0.45, 1.0, k),
		"alpha": lerpf(0.55, 0.9, k),
		"splash": lerpf(0.5, 1.0, k),
	}
