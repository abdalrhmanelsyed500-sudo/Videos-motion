extends Node
## The ONE rendering interface of the sailing view (decision D1): the controller (h2d0.gd) talks only to this, so the
## real 3D HD-2D path (sea_view_3d.gd) and the lightweight 2D fallback (sea_view_2d.gd) are interchangeable, and the
## game logic (SeaState, clock, weather) never knows which one is drawing.
##
## `v` is the sea view dictionary: light, floor, hour, lat, cloud, storm, herald, rain, fog, ice, wave_m, wind_kn,
## wind_from_deg, visibility_km, look (Ocean.look_at), time (real seconds), heading_deg, speed_kn, turn.
## `ship` is {x, z (scene metres), heading_deg, speed_kn, scene_speed}.


func setup(_host: Node) -> void:
	pass


func update_view(_v: Dictionary, _ship: Dictionary, _dt: float) -> void:
	pass


## "dev_lite" | "standard" | "ultra"
func set_quality(_quality: String) -> void:
	pass


func set_active(_on: bool) -> void:
	pass


func path_name() -> String:
	return "base"


func describe() -> String:
	return path_name()


## Height of land under a scene position in metres (below 0 = open water). Used for the grounding check.
func land_height_at(_x: float, _z: float) -> float:
	return -99.0
