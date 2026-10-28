extends SceneTree
## One-shot, non-rendering WASM benchmark. Output is data, not an FPS claim.
const World = preload("res://world/world_generator.gd")
const Save = preload("res://persistence/save_system.gd")
var frame := 0
var GS = null
var CLK = null


func _initialize() -> void:
	GS = root.get_node("GameState")
	CLK = root.get_node("CampaignClock")


func _process(_delta: float) -> void:
	frame += 1
	if frame != 2:
		return
	var config: Dictionary = GS.load_scenario()
	config["region_count"] = 200
	var generations: Array = []
	var invalid := 0
	var static_before: float = Performance.get_monitor(Performance.MEMORY_STATIC)
	var generated = null
	for i in 10:
		var t0 := Time.get_ticks_usec()
		generated = World.generate(1000 + i, config)
		generations.append((Time.get_ticks_usec() - t0) / 1000.0)
		invalid += 0 if World.validate_world(generated).is_empty() else 1
	var static_after: float = Performance.get_monitor(Performance.MEMORY_STATIC)
	var raw_bytes: int = JSON.stringify(generated.serialize()).to_utf8_buffer().size()
	GS.new_campaign(90210, 200)
	var updates: Array = []
	for i in 200:
		if GS.cs.outcome != "":
			break
		var t0 := Time.get_ticks_usec()
		CLK.advance_days(1, GS.cs)
		updates.append((Time.get_ticks_usec() - t0) / 1000.0)
	var saver := Save.new()
	var save_error := saver.save_campaign(GS.cs, 5, "benchmark")
	var save_bytes := 0
	if save_error == "":
		save_bytes = FileAccess.get_file_as_bytes(saver.slot_path(5)).size()
	var result := {
		"environment": "Godot 4.7.2 web template, Node headless, no renderer",
		"regions": 200,
		"generation_samples": generations.size(),
		"generation_mean_ms": mean(generations),
		"generation_median_ms": percentile(generations, 0.5),
		"generation_min_ms": percentile(generations, 0.0),
		"generation_max_ms": percentile(generations, 1.0),
		"invalid_worlds": invalid,
		"simulation_days": updates.size(),
		"simulation_mean_ms_per_day": mean(updates),
		"simulation_median_ms_per_day": percentile(updates, 0.5),
		"simulation_p95_ms_per_day": percentile(updates, 0.95),
		"simulation_max_ms_per_day": percentile(updates, 1.0),
		"active_formations_end": GS.cs.formations.size(),
		"engine_static_memory_before_bytes": static_before,
		"engine_static_memory_after_bytes": static_after,
		"serialized_world_json_bytes": raw_bytes,
		"campaign_save_bytes": save_bytes,
		"save_error": save_error,
	}
	print("PERF_JSON " + JSON.stringify(result))
	quit(0 if invalid == 0 and updates.size() == 200 and save_error == "" else 1)


func mean(values: Array) -> float:
	var sum := 0.0
	for value in values:
		sum += float(value)
	return sum / maxf(1.0, float(values.size()))


func percentile(values: Array, fraction: float) -> float:
	if values.is_empty():
		return 0.0
	var sorted := values.duplicate()
	sorted.sort()
	var index := clampi(int(roundf(fraction * (sorted.size() - 1))), 0, sorted.size() - 1)
	return float(sorted[index])
