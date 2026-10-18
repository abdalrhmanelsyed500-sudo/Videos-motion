extends RefCounted
## Turns the sea-state "view" dictionary into lighting numbers for the HD-2D scene: one sun (or moon), ambient
## colour, fog, water colours and the colour grade. Pure functions (no nodes), so they can be tested without a window.
## All colours are display (sRGB) values; the shaders convert on output. Values are PROVISIONAL: they are tuned by
## eye on the user's PC, then frozen into data/look. Directions: x = east, y = up, z = south.
const WORLD_M_PER_SCENE_M := 10.0
const HIGH_SUN := Color("#fff1d6")
const LOW_SUN := Color("#ff9a58")
const STORM_GREY := Color("#8fa0b0")
const MOON := Color("#9fb4e6")
const NIGHT_AMB := Color(0.07, 0.10, 0.22)
const MIN_ELEVATION_DEG := 5.0
## Always a little aerial perspective, so the top of the screen looks farther away than the bottom.
const HAZE_BASE := 0.0016
const WeatherLook := preload("res://h2d/weather_look.gd")


static func rgb(a: Array) -> Color:
	return Color(float(a[0]), float(a[1]), float(a[2]))


static func vec(c: Color) -> Vector3:
	return Vector3(c.r, c.g, c.b)


static func hash01(n: float) -> float:
	return fposmod(sin(n * 12.9898) * 43758.5453, 1.0)


## Sun by day (05-19 h), moon by night. Rises in the east, crosses the south north of the equator (else the north).
static func sun(hour: float, lat: float) -> Dictionary:
	var noon_el := clampf(78.0 - 0.55 * absf(lat), 18.0, 78.0)
	var is_moon := not (hour > 5.0 and hour < 19.0)
	var f := 0.0
	var el := 0.0
	if is_moon:
		f = fposmod(hour - 19.0, 24.0) / 10.0
		el = sin(clampf(f, 0.0, 1.0) * PI) * 42.0
	else:
		f = (hour - 5.0) / 14.0
		el = sin(f * PI) * noon_el
	el = maxf(el, MIN_ELEVATION_DEG)
	var az := 90.0 + clampf(f, 0.0, 1.0) * 180.0 if lat >= 0.0 else 90.0 - clampf(f, 0.0, 1.0) * 180.0
	var h := deg_to_rad(az)
	var e := deg_to_rad(el)
	var dir := Vector3(sin(h) * cos(e), sin(e), -cos(h) * cos(e))
	return {"dir": dir.normalized(), "elevation_deg": el, "azimuth_deg": fposmod(az, 360.0), "is_moon": is_moon}


## Same curve as the 2D painter: half light looks like 0.68, not 0.5.
static func lit_k(v: Dictionary) -> float:
	var fl: float = v["floor"]
	var k := clampf((float(v["light"]) - fl) / maxf(1.0 - fl, 0.001), 0.0, 1.0)
	return pow(k, 0.55)


static func night_tint(c: Color, k: float) -> Color:
	var night := Color(c.r * 0.22, c.g * 0.30, c.b * 0.55)
	return night.lerp(c, k)


## `fog_cap` is the densest the fog may get per scene metre (look.fog_density_cap): thick enough that the fog
## reaches the ship and the far sea disappears, thin enough that the ship never vanishes.
static func compute(v: Dictionary, fog_cap: float = 0.02) -> Dictionary:
	var look: Dictionary = v["look"]
	var env: Dictionary = v.get("env", {})
	var rain := float(env.get("rain_inst", 0.0))
	var fogk := WeatherLook.fog_thickness(float(v["fog"]))
	var overcast := WeatherLook.overcast(float(v["cloud"]), rain, float(v["storm"]), float(v["fog"]))
	var s := sun(float(v["hour"]), float(v["lat"]))
	var k := lit_k(v)
	var cloud: float = v["cloud"]
	var storm: float = v["storm"]
	var veil := clampf(0.8 * cloud + 0.9 * storm + 0.8 * float(v["fog"]) + 0.5 * rain, 0.0, 1.0)
	var el: float = s["elevation_deg"]
	var sun_col: Color
	var strength: float
	if s["is_moon"]:
		sun_col = MOON
		strength = 0.30 * (1.0 - 0.7 * cloud)
	else:
		sun_col = LOW_SUN.lerp(HIGH_SUN, clampf((el - 8.0) / 30.0, 0.0, 1.0)).lerp(STORM_GREY, veil * 0.8)
		strength = smoothstep(0.0, 18.0, el) * (1.0 - 0.7 * veil)
	var sky_day: Color = rgb(look["sky_day"])
	var sky_dusk: Color = rgb(look["sky_dusk"])
	var dusk := clampf(1.0 - el / 25.0, 0.0, 1.0) if not s["is_moon"] else 0.0
	var day_amb := sky_day.lerp(sky_dusk, dusk * 0.6) * 0.55 + Color(0.16, 0.15, 0.14)
	var amb := NIGHT_AMB.lerp(day_amb, k).lerp(STORM_GREY * 0.55, storm * 0.5 * k)
	# overcast light is flat but not dark: a little diffuse light comes back from the whole sky
	amb = amb.lerp(amb + Color(0.06, 0.065, 0.07), overcast * k)
	# fog is milky and bright, rain and storm clouds are grey
	var fog_c := rgb(look["fog_color"]).lerp(STORM_GREY, veil * 0.5).lerp(Color(0.82, 0.85, 0.86), 0.55 * fogk)
	fog_c = night_tint(fog_c, k)
	# lightning is LIGHT, not a screen overlay: it brightens the ambient, the fog and the sun for a moment
	var fl := flash(float(v.get("time", 0.0)), storm)
	fog_c = fog_c.lerp(Color(0.86, 0.90, 1.0), 0.55 * fl)
	var vis_scene_m := maxf(float(v["visibility_km"]), 0.15) * 1000.0 / WORLD_M_PER_SCENE_M
	var density := clampf(maxf(HAZE_BASE, 3.0 / vis_scene_m) + 0.012 * float(v["fog"]), HAZE_BASE, fog_cap)
	var deep := rgb(look["deep"]).lerp(STORM_GREY * 0.35, storm * 0.45)
	var shallow := rgb(look["shallow"]).lerp(STORM_GREY * 0.6, storm * 0.4)
	var wind_to := deg_to_rad(float(v["wind_from_deg"]) + 180.0)
	return {
		"sun_dir": s["dir"], "elevation_deg": el, "is_moon": s["is_moon"],
		"sun_col": vec(sun_col * (0.65 * strength) + Color(0.35, 0.38, 0.5) * fl),
		"amb_col": vec(amb * 0.62 + Color(0.40, 0.44, 0.58) * fl), "overcast": overcast, "flash": fl,
		"fog_col": vec(fog_c), "fog_density": density,
		"deep": vec(deep), "shallow": vec(shallow), "foam": vec(Color(0.93, 0.97, 0.97).lerp(rgb(look["fog_color"]), 0.15)),
		"night": 1.0 - k, "wind_to": Vector2(sin(wind_to), -cos(wind_to)),
		"sat": 1.12 * (1.0 - 0.28 * storm) * (1.0 - 0.2 * float(v["fog"])) * (1.0 - 0.1 * rain),
		"con": 1.06 + 0.06 * storm,
		"tint": vec(Color(1.0, 1.0, 1.0).lerp(Color(0.86, 0.95, 1.06), clampf(float(v["ice"]), 0.0, 1.0) * 0.7)),
	}


## Lightning pulse 0..1: a storm throws a flash about every 7 s (two quick pulses), deterministic in real time.
static func flash(real_t: float, storm: float) -> float:
	if storm < 0.5:
		return 0.0
	var slot := floorf(real_t / 7.0)
	var r := hash01(slot)
	if r < 0.45:
		return 0.0
	var dt := real_t - slot * 7.0 - r * 5.0
	if dt < 0.0:
		return 0.0
	var f := exp(-dt * 9.0)
	if dt > 0.18:
		f += 0.6 * exp(-(dt - 0.18) * 9.0)
	return clampf(f, 0.0, 1.0) * clampf((storm - 0.5) * 3.0, 0.0, 1.0)
